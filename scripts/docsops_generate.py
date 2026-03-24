#!/usr/bin/env python3
"""DocsOps generation orchestrator.

Implements:
- docsops generate
- --auto (non-interactive execution)
- --trigger policy (run only when quality/drift gates indicate action)

Security model:
- operator mode: local CLI only (Codex/Claude CLI), no API calls
- veridoc mode: API-driven command allowed via explicit --api-generate-command
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

API_KEY_ENV_NAMES = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GROQ_API_KEY",
    "DEEPSEEK_API_KEY",
    "AZURE_OPENAI_API_KEY",
)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _resolve_runtime_config(raw: str) -> Path:
    candidate = Path(raw).expanduser()
    if candidate.exists():
        return candidate.resolve()
    fallbacks = [
        REPO_ROOT / "docsops" / "config" / "client_runtime.yml",
        REPO_ROOT / "config" / "client_runtime.yml",
        REPO_ROOT / "reports" / "acme-demo" / "client_runtime.yml",
    ]
    for path in fallbacks:
        if path.exists():
            return path.resolve()
    return candidate.resolve()


def _load_runtime_map(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _nested_get(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _looks_passing(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"pass", "passed", "ok", "healthy", "green", "success", "succeeded"}:
            return True
        if normalized in {"fail", "failed", "error", "critical", "red", "breach", "blocked"}:
            return False
    return None


def _policy_triggered(reports_dir: Path) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    kpi = _load_json(reports_dir / "kpi-sla-report.json")
    if kpi:
        for key in ("status", "overall_status", "result"):
            verdict = _looks_passing(kpi.get(key))
            if verdict is False:
                reasons.append(f"kpi-sla {key}={kpi.get(key)}")
                break

    drift = _load_json(reports_dir / "api_sdk_drift_report.json")
    if drift:
        for key in ("drift_detected", "has_drift", "breaking_change_detected"):
            if bool(drift.get(key)):
                reasons.append(f"api drift {key}=true")
                break

    docs_contract = _load_json(reports_dir / "pr_docs_contract.json")
    if docs_contract:
        for key in ("status", "result"):
            verdict = _looks_passing(docs_contract.get(key))
            if verdict is False:
                reasons.append(f"docs contract {key}={docs_contract.get(key)}")
                break

    return (len(reasons) > 0, reasons)


def _build_prompt(reports_dir: Path, runtime_config: Path, auto_apply: bool) -> str:
    consolidated = reports_dir / "consolidated_report.json"
    stage_summary = reports_dir / "pipeline_stage_summary.json"
    review_manifest = reports_dir / "review_manifest.json"

    apply_line = (
        "Apply changes directly and keep edits minimal and deterministic."
        if auto_apply
        else "Propose patch + diff first; do not apply without confirmation."
    )

    return "\n".join(
        [
            "You are processing a DocsOps consolidated report.",
            "Goal: produce production-quality documentation updates with verification.",
            apply_line,
            "",
            f"Runtime config: {runtime_config}",
            f"Consolidated report: {consolidated}",
            f"Stage summary: {stage_summary}",
            f"Review manifest: {review_manifest}",
            "",
            "Required output order:",
            "1) Critical findings first",
            "2) Exact file-level fixes",
            "3) Validation commands run + results",
            "4) Final go/no-go",
        ]
    )


def _assert_local_only_security(allow_api_env: bool) -> None:
    if allow_api_env:
        return
    present = [name for name in API_KEY_ENV_NAMES if os.getenv(name)]
    if present:
        joined = ", ".join(present)
        raise RuntimeError(
            "operator mode is local-only. Remote API key env vars are set: "
            f"{joined}. Unset them or pass --allow-api-env to override."
        )


def _wrap_with_egress_guard(cmd: list[str], egress_guard: str) -> list[str]:
    if egress_guard == "off":
        return cmd
    if os.name != "posix":
        raise RuntimeError("egress guard requires POSIX runtime; use --egress-guard off only if policy allows.")
    unshare = shutil.which("unshare")
    if not unshare:
        raise RuntimeError("egress guard requested but `unshare` is not available.")
    # Linux network namespace without interfaces blocks outbound traffic for child process.
    return [unshare, "-n", "--", *cmd]


def _run_local_cli(engine: str, prompt: str, auto_apply: bool, dry_run: bool, egress_guard: str) -> int:
    engines: list[str]
    if engine == "auto":
        engines = ["codex", "claude"]
    else:
        engines = [engine]

    selected = next((name for name in engines if shutil.which(name)), "")
    if not selected:
        print("[docsops] no local LLM CLI found in PATH (expected: codex or claude)")
        return 2

    if selected == "codex":
        cmd = ["codex", "exec", "-a", "never", "-s", "workspace-write", prompt]
    else:
        cmd = [
            "claude",
            "--permission-mode",
            "bypassPermissions",
            "--dangerously-skip-permissions",
            "-p",
            prompt,
        ]

    mode_label = "auto" if auto_apply else "review"
    guarded_cmd = _wrap_with_egress_guard(cmd, egress_guard=egress_guard)
    print(f"[docsops] local engine={selected} mode={mode_label} egress_guard={egress_guard}")
    print(f"[docsops] $ {' '.join(shlex.quote(part) for part in guarded_cmd[:-1])} '<prompt>'")

    if dry_run:
        return 0

    completed = subprocess.run(guarded_cmd, cwd=str(REPO_ROOT), check=False)
    return int(completed.returncode)


def _run_api_command(command: str, dry_run: bool) -> int:
    cmd = shlex.split(command)
    print(f"[docsops] veridoc API command: {' '.join(shlex.quote(part) for part in cmd)}")
    if dry_run:
        return 0
    completed = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False)
    return int(completed.returncode)


def _resolve_veridoc_api_command(explicit: str, runtime: dict[str, Any]) -> str:
    if explicit.strip():
        return explicit.strip()

    env_value = os.getenv("VERIDOC_API_GENERATE_COMMAND", "").strip()
    if env_value:
        return env_value

    candidates = (
        _nested_get(runtime, "veridoc", "api_generate_command"),
        _nested_get(runtime, "llm", "api_generate_command"),
        _nested_get(runtime, "integrations", "ask_ai", "api_generate_command"),
        _nested_get(runtime, "integrations", "ask_ai", "generate_command"),
        _nested_get(runtime, "ask_ai", "api_generate_command"),
        _nested_get(runtime, "ask_ai", "generate_command"),
    )
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return ""


def cmd_generate(args: argparse.Namespace) -> int:
    reports_dir = Path(args.reports_dir).resolve()
    runtime_config = _resolve_runtime_config(args.runtime_config)

    if not runtime_config.exists():
        print(f"[docsops] runtime config not found: {runtime_config}")
        return 2

    consolidated = reports_dir / "consolidated_report.json"
    if not consolidated.exists():
        print(f"[docsops] missing consolidated report: {consolidated}")
        return 2
    runtime_map = _load_runtime_map(runtime_config)

    if args.trigger == "policy":
        should_run, reasons = _policy_triggered(reports_dir)
        if not should_run:
            print("[docsops] policy trigger not fired; generation skipped")
            return 0
        print("[docsops] policy trigger fired:")
        for reason in reasons:
            print(f"  - {reason}")

    if args.mode == "operator":
        _assert_local_only_security(allow_api_env=bool(args.allow_api_env))
        prompt = _build_prompt(reports_dir, runtime_config, auto_apply=bool(args.auto))
        return _run_local_cli(
            args.local_engine,
            prompt,
            auto_apply=bool(args.auto),
            dry_run=bool(args.dry_run),
            egress_guard=args.egress_guard,
        )

    if args.mode == "veridoc":
        api_cmd = _resolve_veridoc_api_command(args.api_generate_command, runtime_map)
        if not api_cmd:
            print("[docsops] veridoc API command is missing.")
            print("[docsops] Set one of:")
            print("  - --api-generate-command \"<cmd>\"")
            print("  - VERIDOC_API_GENERATE_COMMAND env var")
            print("  - runtime config key: veridoc.api_generate_command")
            return 2
        return _run_api_command(api_cmd, dry_run=bool(args.dry_run))

    print(f"[docsops] unsupported mode: {args.mode}")
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="DocsOps generation orchestrator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_generate = subparsers.add_parser("generate", help="Generate docs from consolidated report")
    p_generate.add_argument("--reports-dir", default="reports")
    p_generate.add_argument("--runtime-config", default="docsops/config/client_runtime.yml")
    p_generate.add_argument("--mode", choices=["operator", "veridoc"], default="operator")
    p_generate.add_argument("--trigger", choices=["always", "policy"], default="always")
    p_generate.add_argument("--auto", action="store_true", help="Run non-interactively")
    p_generate.add_argument("--local-engine", choices=["auto", "codex", "claude"], default="auto")
    p_generate.add_argument("--egress-guard", choices=["required", "off"], default="required")
    p_generate.add_argument("--allow-api-env", action="store_true", help="Allow API key env vars in operator mode")
    p_generate.add_argument("--api-generate-command", default="", help="Explicit API generation command for veridoc mode")
    p_generate.add_argument("--dry-run", action="store_true")
    p_generate.set_defaults(func=cmd_generate)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

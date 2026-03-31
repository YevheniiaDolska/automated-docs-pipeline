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
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.flow_feedback import FlowNarrator
from scripts.llm_egress import ensure_external_allowed, load_policy

API_KEY_ENV_NAMES = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GROQ_API_KEY",
    "DEEPSEEK_API_KEY",
    "AZURE_OPENAI_API_KEY",
)


def _advanced_prompts_allowed() -> tuple[bool, str]:
    """Resolve whether advanced prompt profile is allowed by current license."""
    try:
        from scripts.license_gate import allow_advanced_prompts, get_license

        info = get_license()
        enabled = bool(allow_advanced_prompts(info))
        if enabled:
            return True, f"plan={info.plan}"
        if info.plan == "pilot" and info.days_remaining <= 0:
            return False, "pilot_expired"
        return False, f"feature_blocked:{info.plan}"
    except (RuntimeError, ValueError, TypeError, OSError):
        # Keep backward compatibility in environments where license_gate
        # is not bundled.
        return True, "license_gate_unavailable"


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


def _build_prompt(reports_dir: Path, runtime_config: Path, auto_apply: bool, advanced_prompts: bool) -> str:
    consolidated = reports_dir / "consolidated_report.json"
    stage_summary = reports_dir / "pipeline_stage_summary.json"
    review_manifest = reports_dir / "review_manifest.json"

    apply_line = (
        "Apply changes directly and keep edits minimal and deterministic."
        if auto_apply
        else "Propose patch + diff first; do not apply without confirmation."
    )

    if not advanced_prompts:
        return "\n".join(
            [
                "You are processing a DocsOps consolidated report in degraded prompt mode.",
                "Use only deterministic edits based on templates, lint output, and explicit report findings.",
                apply_line,
                "",
                f"Runtime config: {runtime_config}",
                f"Consolidated report: {consolidated}",
                "",
                "Required output order:",
                "1) List blocking lint/drift findings",
                "2) Minimal file-level fixes",
                "3) Commands executed and exact outputs",
                "4) Residual risks",
                "",
                "Do not use advanced narrative prompt strategies.",
            ]
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


def _run_local_model_command(command_template: str, model: str, prompt: str, dry_run: bool) -> int:
    # Fast path for Ollama: avoid giant shell argument interpolation issues.
    if "ollama" in command_template and "{model}" in command_template:
        ollama = shutil.which("ollama") or "ollama"
        cmd = [ollama, "run", model, prompt]
        print(f"[docsops] local model command: {shlex.quote(ollama)} run {shlex.quote(model)} '<prompt>'")
    else:
        if "{prompt}" not in command_template:
            command_template = f"{command_template} \"{{prompt}}\""
        rendered = command_template.replace("{model}", model).replace("{prompt}", prompt)
        cmd = shlex.split(rendered)
        print(f"[docsops] local model command: {' '.join(shlex.quote(part) for part in cmd[:-1])} '<prompt>'")
    if dry_run:
        return 0
    completed = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False)
    return int(completed.returncode)


def _model_exists_in_ollama(model: str) -> bool:
    ollama = shutil.which("ollama")
    if not ollama:
        return False
    try:
        out = subprocess.run([ollama, "list"], cwd=str(REPO_ROOT), check=False, capture_output=True, text=True)
    except (RuntimeError, ValueError, TypeError, OSError):  # noqa: BLE001
        return False
    if out.returncode != 0:
        return False
    needle = model.strip().lower()
    for line in (out.stdout or "").splitlines():
        if not line.strip():
            continue
        if line.lower().startswith(needle + " "):
            return True
    return False


def _preflight_local_model(model: str) -> tuple[bool, str]:
    ollama = shutil.which("ollama")
    if not ollama:
        return (
            False,
            "Ollama not found. Install from https://ollama.com/download and run setup wizard again.",
        )
    if _model_exists_in_ollama(model):
        return True, f"Model '{model}' is available."

    modelfile_candidates = [
        REPO_ROOT / "docsops" / "ollama" / "Modelfile",
        REPO_ROOT / "ollama" / "Modelfile",
    ]
    modelfile = next((p for p in modelfile_candidates if p.exists()), None)
    if modelfile is None:
        return (
            False,
            f"Model '{model}' is missing and Modelfile not found. "
            "Run: python3 docsops/scripts/setup_client_env_wizard.py",
        )
    try:
        create = subprocess.run(
            [ollama, "create", model, "-f", str(modelfile)],
            cwd=str(REPO_ROOT),
            check=False,
            capture_output=True,
            text=True,
        )
    except (RuntimeError, ValueError, TypeError, OSError) as exc:  # noqa: BLE001
        return False, f"Failed to create '{model}' from Modelfile: {exc}"
    if create.returncode != 0:
        err = (create.stderr or create.stdout or "").strip()
        return False, f"Failed to create '{model}' from Modelfile. Details: {err[:260]}"
    if _model_exists_in_ollama(model):
        return True, f"Model '{model}' was auto-created from Modelfile."
    return False, f"Attempted to create '{model}', but it is still not listed by ollama."


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
    narrator = FlowNarrator("DocsOps Generate", total_steps=3)
    narrator.start("Local-first generation orchestration")
    reports_dir = Path(args.reports_dir).resolve()
    runtime_config = _resolve_runtime_config(args.runtime_config)
    narrator.stage(1, "Load runtime and policy", str(runtime_config))

    if not runtime_config.exists():
        print(f"[docsops] runtime config not found: {runtime_config}")
        narrator.finish(False, "runtime config not found")
        return 2

    consolidated = reports_dir / "consolidated_report.json"
    if not consolidated.exists():
        print(f"[docsops] missing consolidated report: {consolidated}")
        narrator.finish(False, "consolidated report missing")
        return 2
    runtime_map = _load_runtime_map(runtime_config)
    narrator.done("Runtime and consolidated report found")

    if args.trigger == "policy":
        should_run, reasons = _policy_triggered(reports_dir)
        if not should_run:
            print("[docsops] policy trigger not fired; generation skipped")
            return 0
        print("[docsops] policy trigger fired:")
        for reason in reasons:
            print(f"  - {reason}")

    advanced_prompts, prompt_reason = _advanced_prompts_allowed()
    if not advanced_prompts:
        print(f"[docsops] advanced prompts disabled by license gate ({prompt_reason}); using degraded prompt mode")

    if args.mode == "operator":
        policy = load_policy(runtime_config)
        llm_cfg = runtime_map.get("llm_control", {}) if isinstance(runtime_map.get("llm_control"), dict) else {}
        narrator.stage(2, "Prepare generation mode", "Resolve local/external execution path")
        prompt = _build_prompt(
            reports_dir,
            runtime_config,
            auto_apply=bool(args.auto),
            advanced_prompts=advanced_prompts,
        )
        llm_mode = str(llm_cfg.get("llm_mode", policy.llm_mode)).strip().lower() or policy.llm_mode
        local_model = str(llm_cfg.get("local_model", policy.local_model)).strip() or policy.local_model
        local_cmd = str(llm_cfg.get("local_model_command", policy.local_model_command)).strip() or policy.local_model_command
        if llm_mode == "local_default":
            _assert_local_only_security(allow_api_env=bool(args.allow_api_env))
            print("[docsops] llm_mode=local_default (fully local first)")
            print(f"[docsops] note: {policy.quality_delta_note}")
            if bool(args.dry_run):
                print("[docsops] preflight: skipped in dry-run mode")
            else:
                ok, msg = _preflight_local_model(local_model)
                print(f"[docsops] preflight: {msg}")
                if not ok:
                    narrator.finish(False, "local model preflight failed")
                    return 3
            local_rc = _run_local_model_command(local_cmd, local_model, prompt, dry_run=bool(args.dry_run))
            if local_rc == 0:
                narrator.done("Local model run completed")
                narrator.finish(True, "Generation completed in fully-local mode")
                return 0
            print(f"[docsops] local model run failed (rc={local_rc}).")
            if not ensure_external_allowed(
                policy=policy,
                step="docsops_generate_operator_fallback",
                reports_dir=reports_dir,
                approve_once=bool(args.external_approve_once),
                approve_for_run=bool(args.external_approve_for_run),
                non_interactive=bool(args.auto),
            ):
                print("[docsops] external fallback blocked by policy.")
                narrator.finish(False, "local run failed and external fallback blocked")
                return 3
            print("[docsops] external fallback approved for this step.")
        elif llm_mode == "external_preferred":
            print("[docsops] llm_mode=external_preferred (Codex/Claude CLI without extra approvals)")
        narrator.done(f"Mode resolved: {llm_mode}")
        narrator.stage(3, "Execute generation", "Run selected local engine")
        rc = _run_local_cli(
            args.local_engine,
            prompt,
            auto_apply=bool(args.auto),
            dry_run=bool(args.dry_run),
            egress_guard=args.egress_guard,
        )
        narrator.finish(rc == 0, f"operator mode rc={rc}")
        return rc

    if args.mode == "veridoc":
        narrator.stage(2, "Prepare generation mode", "veridoc API command mode")
        api_cmd = _resolve_veridoc_api_command(args.api_generate_command, runtime_map)
        if not api_cmd:
            print("[docsops] veridoc API command is missing.")
            print("[docsops] Set one of:")
            print("  - --api-generate-command \"<cmd>\"")
            print("  - VERIDOC_API_GENERATE_COMMAND env var")
            print("  - runtime config key: veridoc.api_generate_command")
            narrator.finish(False, "veridoc API command missing")
            return 2
        narrator.done("API command resolved")
        narrator.stage(3, "Execute generation", "Run veridoc API command")
        rc = _run_api_command(api_cmd, dry_run=bool(args.dry_run))
        narrator.finish(rc == 0, f"veridoc mode rc={rc}")
        return rc

    print(f"[docsops] unsupported mode: {args.mode}")
    narrator.finish(False, f"unsupported mode: {args.mode}")
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
    p_generate.add_argument("--external-approve-once", action="store_true", help="Approve one external LLM fallback step")
    p_generate.add_argument("--external-approve-for-run", action="store_true", help="Approve external LLM fallback for this run")
    p_generate.add_argument("--api-generate-command", default="", help="Explicit API generation command for veridoc mode")
    p_generate.add_argument("--dry-run", action="store_true")
    p_generate.set_defaults(func=cmd_generate)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

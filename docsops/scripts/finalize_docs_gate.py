#!/usr/bin/env python3
"""Unified finalize gate for docs flows.

Flow:
1. Lint all docs.
2. If lint fails, run auto-fixes (and optional LLM fix command), then retry.
3. Optionally ask user confirmation before commit.
4. Optionally run pre-commit and commit/push.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.license_gate import check as _license_check, get_license


@dataclass
class CommandResult:
    command: str
    return_code: int
    output: str


def _ask_confirmation(prompt: str, ui_confirmation: str) -> bool:
    mode = (ui_confirmation or "auto").strip().lower()

    def _cli() -> bool:
        print("[finalize] ------------------------------------------------------------")
        print("[finalize] ACTION REQUIRED")
        print(f"[finalize] {prompt}")
        print("[finalize] Type Yes to continue with commit flow, or No to stop.")
        print("[finalize] ------------------------------------------------------------")
        while True:
            raw = input("[finalize] Enter Yes or No: ").strip().lower()
            if raw in {"yes", "y"}:
                return True
            if raw in {"no", "n", ""}:
                return False
            print("[finalize] Invalid input. Please enter Yes or No.")

    def _try_zenity() -> bool | None:
        if mode == "off":
            return None
        if os.name == "nt":
            return None
        if not os.environ.get("DISPLAY"):
            return None
        if subprocess.run(["which", "zenity"], check=False, capture_output=True).returncode != 0:
            return None
        result = subprocess.run(["zenity", "--question", "--title=VeriOps", f"--text={prompt}"], check=False)
        return result.returncode == 0

    def _try_windows_msgbox() -> bool | None:
        if mode == "off":
            return None
        if os.name != "nt":
            return None
        cmd = (
            "Add-Type -AssemblyName PresentationFramework; "
            f"$r=[System.Windows.MessageBox]::Show('{prompt}','VeriOps confirmation','YesNo','Question'); "
            "if($r -eq 'Yes'){exit 0}else{exit 1}"
        )
        result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], check=False)
        return result.returncode == 0

    if mode in {"on", "auto"}:
        for probe in (_try_zenity, _try_windows_msgbox):
            try:
                out = probe()
                if out is not None:
                    return out
            except (Exception,):
                if mode == "on":
                    return False
                continue
    return _cli()


def _read_yaml(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return raw


def _run(command: str, cwd: Path) -> CommandResult:
    completed = subprocess.run(
        shlex.split(command),
        cwd=str(cwd),
        check=False,
        text=True,
        capture_output=True,
    )
    output = "\n".join([completed.stdout or "", completed.stderr or ""]).strip()
    return CommandResult(command=command, return_code=completed.returncode, output=output)


def _format_command(command: str, docs_root: str, reports_dir: str, iteration: int) -> str:
    return command.format(docs_root=docs_root, reports_dir=reports_dir, iteration=iteration)


def _default_auto_fix_commands(docs_root: str) -> list[str]:
    return [
        f"python3 scripts/normalize_docs.py {shlex.quote(docs_root)}",
        f"python3 scripts/seo_geo_optimizer.py {shlex.quote(docs_root)} --fix",
    ]


def _safe_git_add(repo_root: Path, docs_root: str) -> None:
    candidates = [
        docs_root,
        "mkdocs.yml",
        "docusaurus.config.js",
        "docs",
    ]
    existing: list[str] = []
    for rel in candidates:
        path = (repo_root / rel).resolve() if not Path(rel).is_absolute() else Path(rel)
        if path.exists():
            existing.append(rel)
    if not existing:
        return
    subprocess.run(["git", "add", *existing], cwd=str(repo_root), check=False)


def _load_finalize_config(runtime_config: Path | None) -> dict[str, Any]:
    if runtime_config is None or not runtime_config.exists():
        return {}
    runtime = _read_yaml(runtime_config)
    block = runtime.get("finalize_gate", {})
    return block if isinstance(block, dict) else {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Finalize docs gate: lint -> fix -> lint (+optional commit prompt)")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--runtime-config", default="", help="Optional runtime config to read finalize_gate settings")
    parser.add_argument("--lint-command", default="npm run lint")
    parser.add_argument("--max-iterations", type=int, default=5)
    parser.add_argument("--llm-fix-command", default="", help="Optional command called after lint failure")
    parser.add_argument("--auto-fix-command", action="append", default=[], help="Repeatable auto-fix command")
    parser.add_argument("--continue-on-error", action="store_true")

    parser.add_argument("--ask-commit-confirmation", action="store_true")
    parser.add_argument(
        "--non-interactive-approval",
        choices=["fail", "approve", "deny"],
        default="fail",
        help=(
            "Behavior when confirmation is required but stdin is not interactive: "
            "fail (default), approve, or deny"
        ),
    )
    parser.add_argument(
        "--ui-confirmation",
        choices=["auto", "on", "off"],
        default="auto",
        help="Use GUI yes/no dialog when possible (auto fallback to CLI)",
    )
    parser.add_argument("--precommit-command", default="sh .husky/pre-commit")
    parser.add_argument("--run-precommit-before-commit", action="store_true")
    parser.add_argument("--precommit-max-iterations", type=int, default=3)
    parser.add_argument("--commit-on-approve", action="store_true")
    parser.add_argument("--commit-message", default="docs: finalize generated docs")
    parser.add_argument("--push-on-commit", action="store_true")

    parser.add_argument("--json-report", default="reports/finalize_gate_report.json")
    return parser.parse_args()


def _merge_config(args: argparse.Namespace, cfg: dict[str, Any]) -> dict[str, Any]:
    merged = {
        "docs_root": args.docs_root,
        "reports_dir": args.reports_dir,
        "lint_command": args.lint_command,
        "max_iterations": args.max_iterations,
        "llm_fix_command": args.llm_fix_command,
        "auto_fix_commands": args.auto_fix_command,
        "continue_on_error": bool(args.continue_on_error),
        "ask_commit_confirmation": bool(args.ask_commit_confirmation),
        "non_interactive_approval": str(args.non_interactive_approval),
        "ui_confirmation": str(args.ui_confirmation),
        "precommit_command": args.precommit_command,
        "run_precommit_before_commit": bool(args.run_precommit_before_commit),
        "precommit_max_iterations": int(args.precommit_max_iterations),
        "commit_on_approve": bool(args.commit_on_approve),
        "commit_message": args.commit_message,
        "push_on_commit": bool(args.push_on_commit),
        "json_report": args.json_report,
    }

    if cfg:
        for key, value in cfg.items():
            if key in merged and value not in (None, ""):
                merged[key] = value

    if not merged["auto_fix_commands"]:
        merged["auto_fix_commands"] = _default_auto_fix_commands(str(merged["docs_root"]))

    return merged


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    runtime_path = Path(args.runtime_config).resolve() if args.runtime_config else None
    cfg = _load_finalize_config(runtime_path)
    merged = _merge_config(args, cfg)

    docs_root = str(merged["docs_root"])
    reports_dir = str(merged["reports_dir"])
    lint_command = str(merged["lint_command"])
    max_iterations = int(merged["max_iterations"])
    llm_fix_command = str(merged["llm_fix_command"])
    auto_fix_commands = [str(c) for c in merged.get("auto_fix_commands", []) if str(c).strip()]

    report_path = (repo_root / str(merged["json_report"]))
    report_path.parent.mkdir(parents=True, exist_ok=True)

    history: list[dict[str, Any]] = []
    success = False

    # -- License gate: scoring/auto-fix requires seo_geo_scoring feature --
    lic = get_license()
    if not _license_check("seo_geo_scoring", lic):
        print("[finalize] License: SEO/GEO scoring disabled. Running lint-only (no auto-fix scoring).")

    print("[finalize] Step 7A: Finalize Gate started.")
    print("[finalize] Step 7A.1: Run lint and quality checks.")
    print("[finalize] Step 7A.2: If needed, run safe auto-fixes and repeat checks.")

    for iteration in range(1, max_iterations + 1):
        print(f"[finalize] Lint iteration {iteration}/{max_iterations}: running {lint_command}")
        lint_cmd = _format_command(lint_command, docs_root, reports_dir, iteration)
        lint_result = _run(lint_cmd, repo_root)
        history.append(
            {
                "iteration": iteration,
                "phase": "lint",
                "command": lint_result.command,
                "return_code": lint_result.return_code,
                "output": lint_result.output,
            }
        )

        if lint_result.return_code == 0:
            success = True
            print(f"[finalize] Lint iteration {iteration}: passed.")
            break

        print(f"[finalize] Lint iteration {iteration}: failed. Running auto-fix commands.")

        for raw_cmd in auto_fix_commands:
            cmd = _format_command(raw_cmd, docs_root, reports_dir, iteration)
            print(f"[finalize] Auto-fix: {cmd}")
            result = _run(cmd, repo_root)
            history.append(
                {
                    "iteration": iteration,
                    "phase": "auto_fix",
                    "command": result.command,
                    "return_code": result.return_code,
                    "output": result.output,
                }
            )

        if llm_fix_command.strip():
            llm_cmd = _format_command(llm_fix_command, docs_root, reports_dir, iteration)
            print(f"[finalize] LLM fix command: {llm_cmd}")
            llm_result = _run(llm_cmd, repo_root)
            history.append(
                {
                    "iteration": iteration,
                    "phase": "llm_fix",
                    "command": llm_result.command,
                    "return_code": llm_result.return_code,
                    "output": llm_result.output,
                }
            )

    approve = False
    precommit_ok = None
    commit_done = False
    push_done = False

    if success and bool(merged["ask_commit_confirmation"]):
        print("[finalize] Step 7A.3: Checks passed. Waiting for explicit approval before commit.")
        if not sys.stdin.isatty():
            mode = str(merged.get("non_interactive_approval", "fail")).strip().lower()
            if mode == "approve":
                print("[finalize] Non-interactive session detected. Auto-approval is enabled.")
                approve = True
            elif mode == "deny":
                print("[finalize] Non-interactive session detected. Auto-deny is enabled.")
                approve = False
            else:
                print("[finalize] ERROR: Confirmation required, but session is non-interactive.")
                print("[finalize] Re-run interactively OR set --non-interactive-approval approve|deny.")
                success = False
                approve = False
        else:
            approve = _ask_confirmation(
                "Finalize gate passed. Did you review the docs and approve commit?",
                str(merged.get("ui_confirmation", "auto")),
            )
        print(f"[finalize] Approval result: {'Yes' if approve else 'No'}")

        if approve and bool(merged["run_precommit_before_commit"]):
            print("[finalize] Step 7A.4: Run pre-commit loop after approval.")
            precommit_ok = False
            precommit_max_iterations = max(1, int(merged.get("precommit_max_iterations", 3)))
            for pre_iter in range(1, precommit_max_iterations + 1):
                print(f"[finalize] Pre-commit iteration {pre_iter}/{precommit_max_iterations}: running {merged['precommit_command']}")
                _safe_git_add(repo_root, docs_root)
                pre = _run(str(merged["precommit_command"]), repo_root)
                history.append(
                    {
                        "iteration": pre_iter,
                        "phase": "precommit",
                        "command": pre.command,
                        "return_code": pre.return_code,
                        "output": pre.output,
                    }
                )
                if pre.return_code == 0:
                    precommit_ok = True
                    print(f"[finalize] Pre-commit iteration {pre_iter}: passed.")
                    break

                print(f"[finalize] Pre-commit iteration {pre_iter}: failed. Running auto-fix commands.")
                for raw_cmd in auto_fix_commands:
                    cmd = _format_command(raw_cmd, docs_root, reports_dir, pre_iter)
                    print(f"[finalize] Pre-commit auto-fix: {cmd}")
                    result = _run(cmd, repo_root)
                    history.append(
                        {
                            "iteration": pre_iter,
                            "phase": "precommit_auto_fix",
                            "command": result.command,
                            "return_code": result.return_code,
                            "output": result.output,
                        }
                    )

                if llm_fix_command.strip():
                    llm_cmd = _format_command(llm_fix_command, docs_root, reports_dir, pre_iter)
                    print(f"[finalize] Pre-commit LLM fix command: {llm_cmd}")
                    llm_result = _run(llm_cmd, repo_root)
                    history.append(
                        {
                            "iteration": pre_iter,
                            "phase": "precommit_llm_fix",
                            "command": llm_result.command,
                            "return_code": llm_result.return_code,
                            "output": llm_result.output,
                        }
                    )

            if not precommit_ok:
                success = False

        if approve and success and bool(merged["commit_on_approve"]):
            print("[finalize] Step 7A.5: Approval confirmed. Creating commit.")
            _safe_git_add(repo_root, docs_root)
            commit = _run(f"git commit -m {shlex.quote(str(merged['commit_message']))}", repo_root)
            history.append(
                {
                    "iteration": max_iterations,
                    "phase": "commit",
                    "command": commit.command,
                    "return_code": commit.return_code,
                    "output": commit.output,
                }
            )
            commit_done = commit.return_code == 0
            if commit_done and bool(merged["push_on_commit"]):
                print("[finalize] Step 7A.6: Pushing commit.")
                push = _run("git push", repo_root)
                history.append(
                    {
                        "iteration": max_iterations,
                        "phase": "push",
                        "command": push.command,
                        "return_code": push.return_code,
                        "output": push.output,
                    }
                )
                push_done = push.return_code == 0

    payload = {
        "ok": bool(success),
        "approved": approve,
        "precommit_ok": precommit_ok,
        "commit_done": commit_done,
        "push_done": push_done,
        "history": history,
    }
    report_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    if payload["ok"]:
        print(f"[finalize] Step 7A complete: success. report: {report_path}")
        return 0

    print(f"[finalize] Step 7A complete: failed. report: {report_path}")
    if bool(merged["continue_on_error"]):
        print("[finalize] continue_on_error=true -> returning success exit code")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

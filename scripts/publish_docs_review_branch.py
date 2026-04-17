#!/usr/bin/env python3
"""Create and push docs changes to a dedicated review branch.

Behavior:
- never merges into main/default branch
- runs lint + pre-commit before push
- creates timestamped review branch and pushes it
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


def _run(cmd: list[str], cwd: Path) -> int:
    print(f"[review-branch] $ {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=str(cwd), check=False)
    return int(completed.returncode)


def _run_shell(command: str, cwd: Path) -> int:
    print(f"[review-branch] $ {command}")
    completed = subprocess.run(shlex.split(command), cwd=str(cwd), check=False)
    return int(completed.returncode)


def _current_branch(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return ""
    branch = completed.stdout.strip()
    if branch == "HEAD":
        return ""
    return branch


def _has_changes(repo_root: Path) -> bool:
    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return False
    return bool(completed.stdout.strip())


def _read_runtime(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (RuntimeError, ValueError, TypeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _has_npm_lint_script(repo_root: Path) -> bool:
    package_json = repo_root / "package.json"
    if not package_json.exists():
        return False
    try:
        payload = json.loads(package_json.read_text(encoding="utf-8"))
    except (RuntimeError, ValueError, TypeError, OSError):
        return False
    scripts = payload.get("scripts", {}) if isinstance(payload, dict) else {}
    return isinstance(scripts, dict) and "lint" in scripts


def _resolve_base_branch(repo_root: Path, preferred: str) -> str:
    candidate = preferred.strip()
    if candidate:
        return candidate
    for name in ("main", "master"):
        rc = _run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{name}"], repo_root)
        if rc == 0:
            return name
    return "main"


def _remote_exists(repo_root: Path, remote: str) -> bool:
    completed = subprocess.run(
        ["git", "remote", "get-url", remote],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def _build_review_branch_name(prefix: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    clean_prefix = prefix.strip().strip("/") or "docs/review"
    return f"{clean_prefix}/{stamp}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish docs changes to review branch")
    parser.add_argument("--runtime-config", default="docsops/config/client_runtime.yml")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--remote", default="")
    parser.add_argument("--base-branch", default="")
    parser.add_argument("--review-prefix", default="")
    parser.add_argument("--lint-command", default="")
    parser.add_argument("--precommit-command", default="")
    parser.add_argument("--commit-message", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    runtime_path = Path(args.runtime_config).resolve()
    runtime = _read_runtime(runtime_path)
    review_cfg = runtime.get("review_branch", {})
    if not isinstance(review_cfg, dict):
        review_cfg = {}
    finalize = runtime.get("finalize_gate", {})
    if not isinstance(finalize, dict):
        finalize = {}

    if not bool(review_cfg.get("enabled", True)):
        print("[review-branch] review branch flow disabled in runtime config")
        return 0

    if not _has_changes(repo_root):
        print("[review-branch] no local changes, nothing to publish")
        return 0

    current = _current_branch(repo_root)
    if not current:
        print("[review-branch] unable to detect current branch (detached HEAD)")
        return 2

    remote = str(args.remote or review_cfg.get("remote", "origin")).strip() or "origin"
    base_branch = _resolve_base_branch(repo_root, str(args.base_branch or review_cfg.get("base_branch", "")))
    review_prefix = str(args.review_prefix or review_cfg.get("prefix", "docs/review")).strip() or "docs/review"
    lint_command = str(args.lint_command or review_cfg.get("lint_command", finalize.get("lint_command", "npm run lint"))).strip()
    precommit_command = str(args.precommit_command or review_cfg.get("precommit_command", finalize.get("precommit_command", "sh .husky/pre-commit"))).strip()
    commit_message = str(
        args.commit_message
        or review_cfg.get("commit_message", "docs: autopipeline update for manual review")
    ).strip()

    if lint_command == "npm run lint" and not _has_npm_lint_script(repo_root):
        lint_command = (
            f"python3 docsops/scripts/finalize_docs_gate.py --docs-root {shlex.quote(args.docs_root)} "
            f"--reports-dir reports --runtime-config {shlex.quote(str(args.runtime_config))} --continue-on-error"
        )

    if lint_command:
        lint_rc = _run_shell(lint_command, repo_root)
        if lint_rc != 0:
            print(f"[review-branch] lint failed (rc={lint_rc}); push aborted")
            return lint_rc
    if precommit_command:
        pre_rc = _run_shell(precommit_command, repo_root)
        if pre_rc != 0:
            print(f"[review-branch] pre-commit failed (rc={pre_rc}); push aborted")
            return pre_rc

    if current == base_branch:
        review_branch = _build_review_branch_name(review_prefix)
        switch_rc = _run(["git", "switch", "-c", review_branch], repo_root)
        if switch_rc != 0:
            return switch_rc
    else:
        review_branch = current

    add_rc = _run(["git", "add", "-A"], repo_root)
    if add_rc != 0:
        return add_rc

    commit_rc = _run(["git", "commit", "-m", commit_message], repo_root)
    if commit_rc != 0:
        print("[review-branch] commit skipped or failed; checking if there is anything to push")

    if not _remote_exists(repo_root, remote):
        print(
            f"[review-branch] remote '{remote}' is not configured; "
            "skipping push in local/clean-room mode",
        )
        print(f"[review-branch] local review branch ready: {review_branch}")
        return 0

    push_rc = _run(["git", "push", "-u", remote, review_branch], repo_root)
    if push_rc != 0:
        return push_rc

    print(f"[review-branch] pushed review branch: {review_branch}")
    print("[review-branch] merge to base branch must be done manually after review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

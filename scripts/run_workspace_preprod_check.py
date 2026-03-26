#!/usr/bin/env python3
"""Run a simple pre-prod readiness check across workspace repositories."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPOS = [
    "/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline",
    "/mnt/c/Users/Kroha/Documents/development/git_wrapper",
    "/mnt/c/Users/Kroha/Documents/development/forge-studio",
    "/mnt/c/Users/Kroha/Documents/development/code-forge",
    "/mnt/c/Users/Kroha/Documents/development/app-forge",
    "/mnt/c/Users/Kroha/Documents/development/quantum-forge",
]


def _git_dirty(repo: Path) -> str:
    completed = subprocess.run(
        ["git", "status", "--short"],
        cwd=str(repo),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return "git_error"
    return "dirty" if (completed.stdout or "").strip() else "clean"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pre-prod checks for workspace repos.")
    parser.add_argument("--repos", nargs="*", default=DEFAULT_REPOS)
    parser.add_argument("--report", default="reports/workspace_preprod_check.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows: list[dict] = []
    for raw in args.repos:
        repo = Path(raw).resolve()
        docsops = repo / "docsops"
        nested_docsops = docsops / "docsops"
        if nested_docsops.exists():
            license_jwt_path = nested_docsops / "license.jwt"
            capability_pack_path = nested_docsops / ".capability_pack.enc"
        else:
            license_jwt_path = docsops / "license.jwt"
            capability_pack_path = docsops / ".capability_pack.enc"
        row = {
            "repo": str(repo),
            "exists": repo.exists(),
            "git_state": "",
            "docsops_installed": docsops.exists(),
            "nested_docsops": nested_docsops.exists(),
            "runtime_config": (docsops / "config" / "client_runtime.yml").exists(),
            "policy_pack": (docsops / "policy_packs" / "selected.yml").exists(),
            "license_jwt": license_jwt_path.exists(),
            "license_jwt_path": str(license_jwt_path),
            "capability_pack": capability_pack_path.exists(),
            "capability_pack_path": str(capability_pack_path),
            "ops_installers": {
                "linux": (docsops / "ops" / "install_cron_weekly.sh").exists(),
                "windows": (docsops / "ops" / "install_windows_task.ps1").exists(),
            },
            "branding_report_exists": (repo / "reports" / "veridoc_branding_policy_report.json").exists(),
            "ready": False,
        }
        if repo.exists():
            row["git_state"] = _git_dirty(repo)
        row["ready"] = all(
            [
                row["exists"],
                row["docsops_installed"],
                row["runtime_config"],
                row["policy_pack"],
                row["license_jwt"],
            ]
        )
        rows.append(row)

    ok_count = sum(1 for r in rows if r["ready"])
    payload = {
        "ok": ok_count == len(rows),
        "ok_count": ok_count,
        "total": len(rows),
        "repositories": rows,
    }
    out = (REPO_ROOT / args.report).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"[workspace-preprod] report: {out}")
    print(f"[workspace-preprod] ready: {ok_count}/{len(rows)}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

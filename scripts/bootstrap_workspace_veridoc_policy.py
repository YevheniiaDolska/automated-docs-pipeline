#!/usr/bin/env python3
"""Bootstrap VeriDoc docsops bundle + branding policy across workspace repositories."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPOS = [
    "/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline",
    "/mnt/c/Users/Kroha/Documents/development/git_wrapper",
    "/mnt/c/Users/Kroha/Documents/development/forge-studio",
    "/mnt/c/Users/Kroha/Documents/development/code-forge",
    "/mnt/c/Users/Kroha/Documents/development/app-forge",
    "/mnt/c/Users/Kroha/Documents/development/quantum-forge",
]


def _slug(value: str) -> str:
    text = re.sub(r"[^a-z0-9-]+", "-", value.strip().lower())
    return re.sub(r"-{2,}", "-", text).strip("-")


def _detect_api_root(repo: Path) -> str:
    for candidate in ("api", "openapi"):
        if (repo / candidate).exists():
            return candidate
    return "api"


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=False), encoding="utf-8")


def _load_yaml(path: Path) -> dict:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return raw


def _build_profile(repo: Path, landing_url: str, cheapest_paid_plan: str, default_plan: str) -> Path:
    template = _load_yaml(REPO_ROOT / "profiles" / "clients" / "_template.client.yml")
    name = repo.name
    client_id = _slug(name)
    template["client"]["id"] = client_id
    template["client"]["company_name"] = name
    template["client"]["contact_email"] = f"docs-owner@{client_id}.local"
    template["runtime"]["docs_root"] = "docs"
    template["runtime"]["api_root"] = _detect_api_root(repo)
    template["runtime"]["sdk_root"] = "sdk"
    template["runtime"]["docs_flow"]["mode"] = "hybrid"
    template["runtime"]["output_targets"] = ["mkdocs"]
    template["runtime"]["integrations"]["algolia"]["enabled"] = False
    template["runtime"]["integrations"]["ask_ai"]["enabled"] = False
    template["runtime"]["veridoc_branding"] = {
        "enabled": True,
        "landing_url": landing_url,
        "plan": default_plan,
        "cheapest_paid_plan": cheapest_paid_plan,
        "badge_opt_out": False,
        "referral_code_env": "VERIDOC_REFERRAL_CODE",
        "docs_root": "docs",
        "report_path": "reports/veridoc_branding_policy_report.json",
        "apply_on_weekly": True,
    }
    template["licensing"]["plan"] = "professional"
    template["licensing"]["days"] = 365
    template["licensing"]["auto_generate_capability_pack"] = True
    template["licensing"]["license_key_env"] = "VERIOPS_LICENSE_KEY"

    profile_path = REPO_ROOT / "profiles" / "clients" / "generated" / f"{client_id}.client.yml"
    _write_yaml(profile_path, template)
    return profile_path


def _run(cmd: list[str]) -> tuple[int, str]:
    completed = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False, capture_output=True, text=True)
    output = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")
    return completed.returncode, output.strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap docsops + VeriDoc branding across repositories.")
    parser.add_argument("--landing-url", required=True, help="Landing URL for Powered by VeriDoc badge.")
    parser.add_argument("--cheapest-paid-plan", default="starter", help="Cheapest paid plan slug.")
    parser.add_argument("--default-plan", default="starter", help="Plan used for generated workspace profiles.")
    parser.add_argument("--docsops-dir", default="docsops", help="Docsops folder name in target repos.")
    parser.add_argument("--report", default="reports/workspace_bootstrap_report.json", help="Report path.")
    parser.add_argument("--repos", nargs="*", default=DEFAULT_REPOS, help="Repositories to bootstrap.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_rows: list[dict] = []
    for raw in args.repos:
        repo = Path(raw).resolve()
        row = {
            "repo": str(repo),
            "exists": repo.exists(),
            "profile_path": "",
            "provision_rc": None,
            "ok": False,
            "error": "",
        }
        if not repo.exists():
            row["error"] = "repository not found"
            report_rows.append(row)
            continue
        try:
            profile_path = _build_profile(
                repo,
                landing_url=args.landing_url,
                cheapest_paid_plan=args.cheapest_paid_plan,
                default_plan=args.default_plan,
            )
            row["profile_path"] = str(profile_path)
            cmd = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "provision_client_repo.py"),
                "--client",
                str(profile_path),
                "--client-repo",
                str(repo),
                "--docsops-dir",
                args.docsops_dir,
                "--install-scheduler",
                "none",
            ]
            rc, output = _run(cmd)
            row["provision_rc"] = rc
            row["ok"] = rc == 0
            if rc != 0:
                row["error"] = output[-3000:]
        except (Exception,) as exc:
            row["error"] = str(exc)
        report_rows.append(row)

    ok_count = sum(1 for r in report_rows if r.get("ok"))
    payload = {
        "ok": ok_count == len(report_rows),
        "repositories": report_rows,
        "ok_count": ok_count,
        "total": len(report_rows),
    }
    out = (REPO_ROOT / args.report).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"[workspace-bootstrap] report: {out}")
    print(f"[workspace-bootstrap] success: {ok_count}/{len(report_rows)}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


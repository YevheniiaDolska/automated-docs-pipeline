#!/usr/bin/env python3
"""Build a client bundle from one centralized client profile.

Usage:
  python3 scripts/build_client_bundle.py --client profiles/clients/acme.client.yml
"""

from __future__ import annotations

import argparse
import datetime as dt
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
MANAGED_START = "<!-- DOCSOPS_MANAGED_BLOCK:START -->"
MANAGED_END = "<!-- DOCSOPS_MANAGED_BLOCK:END -->"


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Expected YAML mapping in {path}")
    return raw


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=False)


def copy_into_bundle(rel_path: str, bundle_root: Path) -> None:
    src = REPO_ROOT / rel_path
    if not src.exists():
        raise FileNotFoundError(f"Missing file in repo: {rel_path}")
    dst = bundle_root / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_path_into_bundle(rel_path: str, bundle_root: Path) -> None:
    src = REPO_ROOT / rel_path
    if not src.exists():
        raise FileNotFoundError(f"Missing path in repo: {rel_path}")
    dst = bundle_root / rel_path
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def render_template(path: Path, replacements: dict[str, str]) -> str:
    text = path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    return text


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], Mapping)
            and isinstance(value, Mapping)
        ):
            merged[key] = deep_merge(dict(merged[key]), dict(value))
        else:
            merged[key] = value
    return merged


def build_runtime_config(profile: dict[str, Any]) -> dict[str, Any]:
    runtime = profile.get("runtime", {})
    private = profile.get("private_tuning", {})

    return {
        "project": {
            "client_id": profile["client"]["id"],
            "company_name": profile["client"]["company_name"],
            "preferred_llm": runtime.get("preferred_llm", "claude"),
            "output_targets": runtime.get("output_targets", ["mkdocs"]),
        },
        "docs_flow": runtime.get("docs_flow", {"mode": "code-first"}),
        "paths": {
            "docs_root": runtime.get("docs_root", "docs"),
            "api_root": runtime.get("api_root", "api"),
            "sdk_root": runtime.get("sdk_root", "sdk"),
        },
        "api_first": runtime.get(
            "api_first",
            {
                "enabled": False,
                "project_slug": "project",
                "notes_path": "notes/api-planning.md",
                "spec_path": "api/openapi.yaml",
                "spec_tree_path": "api/project",
                "docs_provider": "mkdocs",
                "docs_spec_target": "docs/assets/api",
                "stubs_output": "generated/api-stubs/fastapi/app/main.py",
                "openapi_version": "3.0.3",
                "manual_overrides_path": "",
                "regression_snapshot_path": "",
                "update_regression_snapshot": False,
                "generate_from_notes": True,
                "verify_user_path": False,
                "mock_base_url": "http://localhost:4010/v1",
                "sync_playground_endpoint": True,
                "run_docs_lint": False,
                "auto_remediate": True,
                "max_attempts": 3,
            },
        ),
        "modules": runtime.get(
            "modules",
            {
                "gap_detection": True,
                "drift_detection": True,
                "docs_contract": True,
                "kpi_sla": True,
                "rag_optimization": True,
                "ontology_graph": True,
                "retrieval_evals": True,
                "terminology_management": True,
                "multilang_examples": True,
                "normalization": True,
                "snippet_lint": True,
                "diagram_validation": True,
                "self_checks": True,
                "fact_checks": True,
                "knowledge_validation": True,
                "i18n_sync": True,
                "release_pack": True,
            },
        ),
        "terminology": runtime.get(
            "terminology",
            {
                "enabled": True,
                "glossary_path": "glossary.yml",
                "auto_add_from_markers": True,
            },
        ),
        "retrieval_eval": runtime.get(
            "retrieval_eval",
            {
                "enabled": True,
                "index_path": "docs/assets/knowledge-retrieval-index.json",
                "dataset_path": "",
                "top_k": 3,
                "min_precision": 0.5,
                "min_recall": 0.5,
                "max_hallucination_rate": 0.5,
                "auto_samples": 25,
            },
        ),
        "knowledge_graph": runtime.get(
            "knowledge_graph",
            {
                "enabled": True,
                "modules_dir": "knowledge_modules",
                "output_path": "docs/assets/knowledge-graph.jsonld",
            },
        ),
        "git_sync": runtime.get(
            "git_sync",
            {
                "enabled": False,
                "repo_path": ".",
                "remote": "origin",
                "branch": "",
                "fetch_first": True,
                "rebase": True,
                "autostash": True,
                "continue_on_error": True,
            },
        ),
        "multilang_examples": runtime.get(
            "multilang_examples",
            {
                "enabled": True,
                "scope": "all",
                "required_languages": ["curl", "javascript", "python"],
            },
        ),
        "custom_tasks": runtime.get("custom_tasks", {"weekly": [], "on_demand": []}),
        "integrations": runtime.get(
            "integrations",
            {
                "algolia": {
                    "enabled": False,
                    "docs_dir": runtime.get("docs_root", "docs"),
                    "report_output": "reports/seo-report.json",
                    "upload_on_weekly": False,
                    "app_id_env": "ALGOLIA_APP_ID",
                    "api_key_env": "ALGOLIA_API_KEY",
                    "index_name_env": "ALGOLIA_INDEX_NAME",
                    "index_name_default": "docs",
                },
                "ask_ai": {
                    "enabled": False,
                    "auto_configure_on_provision": True,
                    "install_runtime_pack": False,
                    "provider": "openai",
                    "billing_mode": "disabled",
                    "model": "gpt-4.1-mini",
                    "base_url": "https://api.openai.com/v1",
                },
            },
        ),
        "pipeline": {
            "stale_days": private.get("stale_days", 21),
            "weekly_stale_days": private.get("weekly_stale_days", 180),
            "rag_chunk_target_tokens": private.get("rag_chunk_target_tokens", 420),
            "verify_max_attempts": private.get("verify_max_attempts", 3),
            "gap_priority_weights": private.get(
                "gap_priority_weights",
                {
                    "business_impact": 0.40,
                    "user_frequency": 0.40,
                    "implementation_cost": 0.20,
                },
            ),
        },
    }


def build_licensed_files(profile: dict[str, Any], bundle_root: Path) -> None:
    company = profile["client"]["company_name"]
    client_id = profile["client"]["id"]
    today = dt.date.today().isoformat()

    replacements = {
        "COMPANY_NAME": company,
        "CLIENT_ID": client_id,
        "DATE_ISSUED": today,
    }

    lic_template = REPO_ROOT / "templates" / "legal" / "LICENSE-COMMERCIAL.template.md"
    notice_template = REPO_ROOT / "templates" / "legal" / "NOTICE.template.md"

    (bundle_root / "LICENSE-COMMERCIAL.md").write_text(
        render_template(lic_template, replacements), encoding="utf-8"
    )
    (bundle_root / "NOTICE").write_text(
        render_template(notice_template, replacements), encoding="utf-8"
    )


def build_vale_config(profile: dict[str, Any], bundle_root: Path) -> None:
    bundle_cfg = profile.get("bundle", {})
    style_guide = str(bundle_cfg.get("style_guide", "google")).strip().lower()
    if style_guide not in {"google", "microsoft", "hybrid"}:
        raise ValueError("bundle.style_guide must be one of: google, microsoft, hybrid")

    if style_guide == "google":
        packages = "Google, proselint, write-good"
        base_styles = "Google, GEO, proselint, write-good, AmericanEnglish"
    elif style_guide == "microsoft":
        packages = "Microsoft, proselint, write-good"
        base_styles = "Microsoft, GEO, proselint, write-good, AmericanEnglish"
    else:
        packages = "Google, Microsoft, proselint, write-good"
        base_styles = "Google, Microsoft, GEO, proselint, write-good, AmericanEnglish"

    vale_ini = (
        "StylesPath = .vale/styles\n"
        "MinAlertLevel = error\n"
        f"Packages = {packages}\n\n"
        "[*.md]\n"
        f"BasedOnStyles = {base_styles}\n\n"
        "[docs/ru/**/*.md]\n"
        "BasedOnStyles = GEO\n\n"
        "[docs/de/**/*.md]\n"
        "BasedOnStyles = GEO\n\n"
        "[docs/fr/**/*.md]\n"
        "BasedOnStyles = GEO\n\n"
        "[docs/es/**/*.md]\n"
        "BasedOnStyles = GEO\n\n"
        "[docs/zh/**/*.md]\n"
        "BasedOnStyles = GEO\n\n"
        "[docs/ja/**/*.md]\n"
        "BasedOnStyles = GEO\n\n"
        "[docs/ko/**/*.md]\n"
        "BasedOnStyles = GEO\n\n"
        "[docs/pt/**/*.md]\n"
        "BasedOnStyles = GEO\n"
    )
    (bundle_root / ".vale.ini").write_text(vale_ini, encoding="utf-8")


def build_managed_instruction_block(docsops_root: str) -> str:
    root = docsops_root.strip("/")
    lines = [
        MANAGED_START,
        "## DocsOps Managed Local Workflow",
        "",
        "When user asks to run documentation automation, ALWAYS:",
        f"1. Read `{root}/config/client_runtime.yml`.",
        f"2. Read `{root}/policy_packs/selected.yml`.",
        "3. Read `glossary.yml` before generating docs and use preferred terminology.",
        "   If a term already exists in glossary, use the preferred form and do not substitute synonyms.",
        "4. If you introduce a new project term, add a marker in docs:",
        "   `<!-- glossary:add: Term | Description | alias1, alias2 -->`.",
        f"5. Run `{root}/scripts/sync_project_glossary.py` when glossary markers are present.",
        f"6. Run only scripts from `{root}/scripts/` that are required by enabled modules.",
        "7. Block publish if verification fails.",
        "8. Return a short report: changed files, checks passed/failed, publish targets.",
        "",
        "Do not invent ad-hoc pipeline logic outside these files.",
        MANAGED_END,
        "",
    ]
    return "\n".join(lines)


def upsert_managed_block(file_path: Path, block_text: str) -> None:
    text = file_path.read_text(encoding="utf-8")
    if MANAGED_START in text and MANAGED_END in text:
        start = text.index(MANAGED_START)
        end = text.index(MANAGED_END) + len(MANAGED_END)
        new_text = text[:start] + block_text.rstrip() + text[end:]
    else:
        if not text.endswith("\n"):
            text += "\n"
        new_text = text + "\n" + block_text
    file_path.write_text(new_text, encoding="utf-8")


def build_llm_instruction_files(profile: dict[str, Any], bundle_root: Path) -> None:
    bundle_cfg = profile.get("bundle", {})
    llm_cfg = bundle_cfg.get("llm", {})

    codex_src_rel = str(llm_cfg.get("codex_instructions_source", "AGENTS.md"))
    claude_src_rel = str(llm_cfg.get("claude_instructions_source", "CLAUDE.md"))

    codex_src = REPO_ROOT / codex_src_rel
    claude_src = REPO_ROOT / claude_src_rel
    if not codex_src.exists():
        raise FileNotFoundError(f"Missing Codex instructions file: {codex_src_rel}")
    if not claude_src.exists():
        raise FileNotFoundError(f"Missing Claude instructions file: {claude_src_rel}")

    codex_dst = bundle_root / "AGENTS.md"
    claude_dst = bundle_root / "CLAUDE.md"
    shutil.copy2(codex_src, codex_dst)
    shutil.copy2(claude_src, claude_dst)

    if bool(llm_cfg.get("inject_managed_block", True)):
        docsops_root = str(llm_cfg.get("docsops_root_in_client_repo", "docsops"))
        block = build_managed_instruction_block(docsops_root)
        upsert_managed_block(codex_dst, block)
        upsert_managed_block(claude_dst, block)


def _cron_day_to_number(day: str) -> str:
    mapping = {
        "sunday": "0",
        "monday": "1",
        "tuesday": "2",
        "wednesday": "3",
        "thursday": "4",
        "friday": "5",
        "saturday": "6",
    }
    key = day.strip().lower()
    if key not in mapping:
        raise ValueError(f"Unsupported day_of_week: {day}")
    return mapping[key]


def build_automation_files(profile: dict[str, Any], bundle_root: Path) -> None:
    bundle_cfg = profile.get("bundle", {})
    llm_cfg = bundle_cfg.get("llm", {})
    auto_cfg = bundle_cfg.get("automation", {})
    weekly_cfg = auto_cfg.get("weekly_gap_report", {})
    if not bool(weekly_cfg.get("enabled", True)):
        return

    docsops_root = str(llm_cfg.get("docsops_root_in_client_repo", "docsops")).strip("/")
    day = str(weekly_cfg.get("day_of_week", "monday")).strip().lower()
    time_24h = str(weekly_cfg.get("time_24h", "10:00")).strip()
    since_days = int(weekly_cfg.get("since_days", 7))
    retry_delay_seconds = int(weekly_cfg.get("retry_delay_seconds", 60))
    hh, mm = time_24h.split(":")
    cron_day = _cron_day_to_number(day)
    client_id = str(profile.get("client", {}).get("id", "client")).strip()
    task_name = f"DocsOpsWeekly-{client_id}"

    ops_dir = bundle_root / "ops"
    ops_dir.mkdir(parents=True, exist_ok=True)

    run_sh = f"""#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT=\"$(cd \"$(dirname \"${{BASH_SOURCE[0]}}\")/../..\" && pwd)\"
cd \"$REPO_ROOT\"
mkdir -p reports
while true; do
  if python3 {docsops_root}/scripts/run_weekly_gap_batch.py --docsops-root {docsops_root} --reports-dir reports --since {since_days}; then
    break
  fi
  echo \"[docsops] weekly run failed, retrying in {retry_delay_seconds}s...\"
  sleep {retry_delay_seconds}
done
"""
    run_ps1 = f"""$ErrorActionPreference = \"Stop\"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot \"..\\..\" )).Path
Set-Location $RepoRoot
New-Item -ItemType Directory -Path \"reports\" -Force | Out-Null
while ($true) {{
  if (Get-Command py -ErrorAction SilentlyContinue) {{
    py -3 \"{docsops_root}/scripts/run_weekly_gap_batch.py\" --docsops-root \"{docsops_root}\" --reports-dir \"reports\" --since {since_days}
  }} else {{
    python \"{docsops_root}/scripts/run_weekly_gap_batch.py\" --docsops-root \"{docsops_root}\" --reports-dir \"reports\" --since {since_days}
  }}
  if ($LASTEXITCODE -eq 0) {{
    break
  }}
  Write-Host \"[docsops] weekly run failed, retrying in {retry_delay_seconds}s...\"
  Start-Sleep -Seconds {retry_delay_seconds}
}}
"""
    install_cron = f"""#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT=\"$(cd \"$(dirname \"${{BASH_SOURCE[0]}}\")/../..\" && pwd)\"
MARKER=\"# docsops-weekly-{client_id}\"
LINE=\"{int(mm)} {int(hh)} * * {cron_day} cd '$REPO_ROOT' && bash {docsops_root}/ops/run_weekly_docsops.sh >> '$REPO_ROOT/reports/docsops-weekly.log' 2>&1 $MARKER\"
(crontab -l 2>/dev/null | grep -v \"$MARKER\"; echo \"$LINE\") | crontab -
echo \"Installed weekly cron for {task_name} at {day} {time_24h}\"
"""
    install_windows = f"""$ErrorActionPreference = \"Stop\"
$TaskName = \"{task_name}\"
$ScriptPath = (Resolve-Path (Join-Path $PSScriptRoot \"run_weekly_docsops.ps1\")).Path
$Action = New-ScheduledTaskAction -Execute \"powershell.exe\" -Argument \"-NoProfile -ExecutionPolicy Bypass -File `\"$ScriptPath`\"\"\n"""
    install_windows += (
        f"$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek {day.capitalize()} -At \"{time_24h}\"\n"
        "$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel LeastPrivilege\n"
        "Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Force | Out-Null\n"
        f"Write-Host \"Installed Task Scheduler job: {task_name} ({day} {time_24h})\"\n"
    )

    (ops_dir / "run_weekly_docsops.sh").write_text(run_sh, encoding="utf-8")
    (ops_dir / "run_weekly_docsops.ps1").write_text(run_ps1, encoding="utf-8")
    (ops_dir / "install_cron_weekly.sh").write_text(install_cron, encoding="utf-8")
    (ops_dir / "install_windows_task.ps1").write_text(install_windows, encoding="utf-8")

    (ops_dir / "runbook.md").write_text(
        (
            "# Weekly automation runbook\n\n"
            "Linux/macOS:\n"
            "1. Run `bash docsops/ops/install_cron_weekly.sh` once.\n\n"
            "Windows:\n"
            "1. Run `powershell -ExecutionPolicy Bypass -File docsops/ops/install_windows_task.ps1` once.\n"
        ),
        encoding="utf-8",
    )

    for f in (ops_dir / "run_weekly_docsops.sh", ops_dir / "install_cron_weekly.sh"):
        f.chmod(0o755)


def create_bundle(profile_path: Path) -> Path:
    profile = read_yaml(profile_path)
    client = profile.get("client", {})
    bundle_cfg = profile.get("bundle", {})

    client_id = str(client.get("id", "")).strip()
    company = str(client.get("company_name", "")).strip()
    if not client_id or not company:
        raise ValueError("client.id and client.company_name are required")

    out_dir = str(bundle_cfg.get("output_dir", "generated/client_bundles"))
    bundle_root = REPO_ROOT / out_dir / client_id

    if bundle_root.exists():
        shutil.rmtree(bundle_root)
    bundle_root.mkdir(parents=True, exist_ok=True)

    pack_name = str(bundle_cfg.get("base_policy_pack", "minimal")).strip()
    policy_src = REPO_ROOT / "policy_packs" / f"{pack_name}.yml"
    if not policy_src.exists():
        raise FileNotFoundError(f"Unknown policy pack: {pack_name}")

    policy = read_yaml(policy_src)
    policy_overrides = bundle_cfg.get("policy_overrides", {})
    if isinstance(policy_overrides, Mapping):
        policy = deep_merge(policy, dict(policy_overrides))

    policy_dst = bundle_root / "policy_packs" / "selected.yml"
    write_yaml(policy_dst, policy)

    for rel in bundle_cfg.get("include_scripts", []):
        copy_into_bundle(str(rel), bundle_root)
    for rel in bundle_cfg.get("include_docs", []):
        copy_into_bundle(str(rel), bundle_root)
    for rel in bundle_cfg.get("include_paths", []):
        copy_path_into_bundle(str(rel), bundle_root)

    runtime_cfg = build_runtime_config(profile)
    write_yaml(bundle_root / "config" / "client_runtime.yml", runtime_cfg)

    build_llm_instruction_files(profile, bundle_root)
    build_automation_files(profile, bundle_root)
    build_vale_config(profile, bundle_root)

    operator_note = {
        "client": {
            "id": client_id,
            "company_name": company,
            "contact_email": client.get("contact_email", ""),
        },
        "local_use": {
            "llm_instructions": ["AGENTS.md", "CLAUDE.md"],
            "runtime_config": "config/client_runtime.yml",
            "policy_pack": "policy_packs/selected.yml",
            "automation_runbook": "ops/runbook.md",
            "vale_config": ".vale.ini",
        },
    }
    write_yaml(bundle_root / "BUNDLE_INFO.yml", operator_note)

    build_licensed_files(profile, bundle_root)

    return bundle_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build one client bundle")
    parser.add_argument(
        "--client",
        required=True,
        help="Path to *.client.yml profile (relative to repo or absolute)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profile_path = Path(args.client)
    if not profile_path.is_absolute():
        profile_path = (REPO_ROOT / profile_path).resolve()

    if not profile_path.exists():
        raise FileNotFoundError(f"Profile not found: {profile_path}")

    bundle = create_bundle(profile_path)
    print(f"[ok] bundle created: {bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

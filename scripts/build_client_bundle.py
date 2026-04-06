#!/usr/bin/env python3
"""Build a client bundle from one centralized client profile.

Usage:
  python3 scripts/build_client_bundle.py --client profiles/clients/acme.client.yml
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.api_protocols import merge_protocol_settings, normalize_protocols

MANAGED_START = "<!-- VERIOPS_MANAGED_BLOCK:START -->"
MANAGED_END = "<!-- VERIOPS_MANAGED_BLOCK:END -->"


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
    api_protocols = normalize_protocols(runtime.get("api_protocols", ["rest"]))
    api_protocol_settings = merge_protocol_settings(runtime.get("api_protocol_settings", {}), api_protocols)

    return {
        "project": {
            "client_id": profile["client"]["id"],
            "company_name": profile["client"]["company_name"],
            "preferred_llm": runtime.get("preferred_llm", "claude"),
            "output_targets": runtime.get("output_targets", ["mkdocs"]),
        },
        "llm_control": runtime.get(
            "llm_control",
            {
                "llm_mode": "external_preferred",
                "external_llm_allowed": True,
                "require_explicit_approval": False,
                "approval_cache_scope": "run",
                "redact_before_external": True,
                "local_model": "veridoc-writer",
                "local_base_model": "qwen3:30b",
                "local_model_command": "ollama run {model} \"{prompt}\"",
                "auto_install_local_model_on_setup": True,
                "strict_local_first": False,
                "quality_delta_note": "Fully local mode may reduce output quality by ~10-15% on hardest synthesis tasks.",
            },
        ),
        "docs_flow": runtime.get("docs_flow", {"mode": "code-first"}),
        "docs_site": runtime.get(
            "docs_site",
            {
                "generator": "mkdocs",
                "build_enabled": True,
                "build_command": "",
            },
        ),
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
                "sandbox_backend": "external",
                "mock_service": "custom",
                "mock_base_url": "https://sandbox-api.example.com/v1",
                "sync_playground_endpoint": True,
                "external_mock": {
                    "enabled": True,
                    "provider": "postman",
                    "base_path": "/v1",
                    "postman": {
                        "api_key_env": "POSTMAN_API_KEY",
                        "workspace_id_env": "POSTMAN_WORKSPACE_ID",
                        "collection_uid_env": "POSTMAN_COLLECTION_UID",
                        "mock_server_id_env": "POSTMAN_MOCK_SERVER_ID",
                        "mock_server_name": "",
                        "private": False,
                    },
                },
                "run_docs_lint": False,
                "generate_test_assets": True,
                "test_assets_output_dir": "reports/api-test-assets",
                "testrail_csv": "reports/api-test-assets/testrail_test_cases.csv",
                "zephyr_json": "reports/api-test-assets/zephyr_test_cases.json",
                "upload_test_assets": False,
                "upload_test_assets_strict": False,
                "test_assets_upload_report": "reports/api-test-assets/upload_report.json",
                "test_management": {
                    "testrail": {
                        "enabled_env": "TESTRAIL_UPLOAD_ENABLED",
                        "base_url_env": "TESTRAIL_BASE_URL",
                        "email_env": "TESTRAIL_EMAIL",
                        "api_key_env": "TESTRAIL_API_KEY",
                        "section_id_env": "TESTRAIL_SECTION_ID",
                        "suite_id_env": "TESTRAIL_SUITE_ID",
                    },
                    "zephyr_scale": {
                        "enabled_env": "ZEPHYR_UPLOAD_ENABLED",
                        "base_url_env": "ZEPHYR_SCALE_BASE_URL",
                        "api_token_env": "ZEPHYR_SCALE_API_TOKEN",
                        "project_key_env": "ZEPHYR_SCALE_PROJECT_KEY",
                        "folder_id_env": "ZEPHYR_SCALE_FOLDER_ID",
                    },
                },
                "auto_remediate": True,
                "max_attempts": 3,
            },
        ),
        "api_protocols": api_protocols,
        "api_protocol_settings": api_protocol_settings,
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
        "finalize_gate": runtime.get(
            "finalize_gate",
            {
                "enabled": True,
                "docs_root": str(runtime.get("docs_root", "docs")),
                "reports_dir": "reports",
                "lint_command": "npm run lint",
                "max_iterations": 5,
                "continue_on_error": True,
                "auto_fix_commands": [
                    "python3 scripts/normalize_docs.py {docs_root}",
                    "python3 scripts/seo_geo_optimizer.py {docs_root} --fix",
                ],
                "llm_fix_command": "",
                "ask_commit_confirmation": False,
                "run_precommit_before_commit": True,
                "precommit_max_iterations": 3,
                "commit_on_approve": False,
                "push_on_commit": False,
            },
        ),
        "review_branch": runtime.get(
            "review_branch",
            {
                "enabled": True,
                "auto_push": True,
                "remote": "origin",
                "base_branch": "main",
                "prefix": "docs/review",
                "lint_command": "npm run lint",
                "precommit_command": "sh .husky/pre-commit",
                "commit_message": "docs: autopipeline update for manual review",
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
        "veridoc_branding": runtime.get(
            "veridoc_branding",
            {
                "enabled": False,
                "landing_url": "https://veri-doc.app/",
                "plan": "free",
                "cheapest_paid_plan": "starter",
                "badge_opt_out": False,
                "docs_root": runtime.get("docs_root", "docs"),
                "report_path": "reports/veridoc_branding_policy_report.json",
                "apply_on_weekly": True,
            },
        ),
        "pr_autofix": runtime.get(
            "pr_autofix",
            {
                "enabled": False,
                "require_label": False,
                "label_name": "auto-doc-fix",
                "enable_auto_merge": False,
                "commit_message": "docs: auto-sync PR docs",
                "workflow_filename": "docsops-pr-autofix.yml",
            },
        ),
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
                    "site_generator": "mkdocs",
                    "generate_search_widget": True,
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


def build_licensing_infrastructure(profile: dict[str, Any], bundle_root: Path) -> None:
    """Set up the licensing directory structure in the bundle.

    If an Ed25519 private key is available locally, generates a signed JWT
    automatically based on the licensing section in the client profile.
    Otherwise copies a placeholder.
    """
    keys_dir = bundle_root / "docsops" / "keys"
    keys_dir.mkdir(parents=True, exist_ok=True)
    docsops_dir = bundle_root / "docsops"

    # Copy the Ed25519 public key for offline JWT verification
    pub_key_src = REPO_ROOT / "docsops" / "keys" / "veriops-licensing.pub"
    if pub_key_src.exists():
        shutil.copy2(pub_key_src, keys_dir / "veriops-licensing.pub")

    # Try to auto-generate JWT if private key is available.
    # For client deliveries we require a signed JWT by default.
    priv_key_path = REPO_ROOT / "docsops" / "keys" / "veriops-licensing.key"
    licensing = profile.get("licensing", {})
    plan = str(licensing.get("plan", "professional")).strip().lower()
    days = int(licensing.get("days", 365))
    max_docs = int(licensing.get("max_docs", 0))
    require_signed_jwt = bool(licensing.get("require_signed_jwt", True))
    manual_jwt_path_raw = str(licensing.get("manual_jwt_path", "")).strip()
    client_id = str(profile.get("client", {}).get("id", "")).strip()
    tenant_id = str(profile.get("client", {}).get("tenant_id", client_id)).strip()
    company_domain = str(profile.get("client", {}).get("company_domain", "")).strip().lower()

    jwt_path = docsops_dir / "license.jwt"
    generated_or_copied = False

    if manual_jwt_path_raw:
        manual_jwt_path = Path(manual_jwt_path_raw)
        if not manual_jwt_path.is_absolute():
            manual_jwt_path = (REPO_ROOT / manual_jwt_path).resolve()
        if manual_jwt_path.exists():
            shutil.copy2(manual_jwt_path, jwt_path)
            print(f"[license] JWT copied from manual path: {manual_jwt_path}")
            generated_or_copied = True
        elif require_signed_jwt:
            raise RuntimeError(
                f"Signed JWT is required but manual_jwt_path does not exist: {manual_jwt_path}"
            )

    if not generated_or_copied and priv_key_path.exists() and client_id:
        try:
            sys_path_orig = list(sys.path)
            build_dir = str(REPO_ROOT / "build")
            if build_dir not in sys.path:
                sys.path.insert(0, build_dir)
            try:
                from generate_license import generate_jwt
            finally:
                sys.path[:] = sys_path_orig

            priv_key = base64.b64decode(priv_key_path.read_bytes().strip())
            token = generate_jwt(
                client_id=client_id,
                plan=plan,
                days=days,
                private_key=priv_key,
                max_docs=max_docs,
                tenant_id=tenant_id,
                company_domain=company_domain,
            )
            jwt_path.write_text(token + "\n", encoding="utf-8")
            print(f"[license] JWT auto-generated: plan={plan}, days={days}, client={client_id}")
            generated_or_copied = True
        except (RuntimeError, ValueError, TypeError, OSError) as exc:
            if require_signed_jwt:
                raise RuntimeError(
                    "JWT auto-generation failed. Run:\n"
                    f"python3 build/generate_license.py --client-id {client_id or 'CLIENT'} "
                    f"--plan {plan} --days {days} "
                    f"--tenant-id {tenant_id or client_id or 'TENANT'} "
                    f"--company-domain {company_domain or '<company-domain>'} "
                    "--output generated/tmp/license.jwt\n"
                    "Then set licensing.manual_jwt_path to that file and rebuild."
                ) from exc
            print(f"[license] JWT auto-generation failed ({exc}), writing placeholder")

    if not generated_or_copied:
        reason = "no private key" if not priv_key_path.exists() else "no client_id"
        if require_signed_jwt:
            raise RuntimeError(
                "Signed JWT is required for this bundle but was not produced "
                f"({reason}). Run:\n"
                f"python3 build/generate_license.py --client-id {client_id or 'CLIENT'} "
                f"--plan {plan} --days {days} "
                f"--tenant-id {tenant_id or client_id or 'TENANT'} "
                f"--company-domain {company_domain or '<company-domain>'} "
                "--output generated/tmp/license.jwt\n"
                "Then set licensing.manual_jwt_path to that file and rebuild."
            )
        print(f"[license] Skipping JWT auto-generation ({reason}), writing placeholder")
        jwt_path.write_text(
            "# Placeholder: generate a license JWT with:\n"
            f"#   python3 build/generate_license.py --client-id {client_id or 'CLIENT'} "
            f"--plan {plan} --days {days} "
            f"--tenant-id {tenant_id or client_id or 'TENANT'} "
            f"--company-domain {company_domain or '<company-domain>'} "
            "--output generated/tmp/license.jwt\n"
            "# Then copy the .jwt file here.\n",
            encoding="utf-8",
        )

    # Optional encrypted capability pack generation at bundle build time.
    # This keeps repository sources unencrypted while delivering encrypted packs to clients.
    pack_path = docsops_dir / ".capability_pack.enc"
    auto_pack = bool(licensing.get("auto_generate_capability_pack", True))
    license_key_env = str(licensing.get("license_key_env", "VERIOPS_LICENSE_KEY")).strip() or "VERIOPS_LICENSE_KEY"
    license_key = str(licensing.get("license_key", "")).strip() or str(os.environ.get(license_key_env, "")).strip()
    if auto_pack and client_id and license_key:
        generate_pack_script = REPO_ROOT / "build" / "generate_pack.py"
        if generate_pack_script.exists():
            try:
                import subprocess

                cmd = [
                    sys.executable,
                    str(generate_pack_script),
                    "--client-id",
                    client_id,
                    "--plan",
                    plan,
                    "--license-key",
                    license_key,
                    "--days",
                    str(days),
                    "--output",
                    str(pack_path),
                ]
                completed = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False, capture_output=True, text=True)
                if completed.returncode == 0 and pack_path.exists():
                    print(f"[license] capability pack generated: {pack_path}")
                else:
                    print("[license] capability pack generation failed; writing placeholder")
                    (docsops_dir / ".capability_pack.README.txt").write_text(
                        "Capability pack was not generated automatically.\n"
                        "To generate manually on operator machine:\n"
                        f"  python3 build/generate_pack.py --client-id {client_id} --plan {plan} "
                        f"--license-key <KEY> --days {days} --output docsops/.capability_pack.enc\n",
                        encoding="utf-8",
                    )
            except (RuntimeError, ValueError, TypeError, OSError) as exc:
                print(f"[license] capability pack generation error ({exc}); writing placeholder")
        else:
            print("[license] build/generate_pack.py not found; skipping capability pack generation")
    else:
        reason = []
        if not auto_pack:
            reason.append("disabled")
        if not client_id:
            reason.append("no client_id")
        if not license_key:
            reason.append(f"missing {license_key_env}")
        print(f"[license] capability pack skipped ({', '.join(reason)})")


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
        "## VeriOps Managed Local Workflow",
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
    local_src_rel = str(llm_cfg.get("local_instructions_source", "LOCAL_MODEL.md"))

    codex_src = REPO_ROOT / codex_src_rel
    claude_src = REPO_ROOT / claude_src_rel
    local_src = REPO_ROOT / local_src_rel
    if not codex_src.exists():
        raise FileNotFoundError(f"Missing Codex instructions file: {codex_src_rel}")
    if not claude_src.exists():
        raise FileNotFoundError(f"Missing Claude instructions file: {claude_src_rel}")
    if not local_src.exists():
        # Backward-compatible fallback: reuse AGENTS when LOCAL_MODEL is absent.
        local_src = codex_src

    codex_dst = bundle_root / "AGENTS.md"
    claude_dst = bundle_root / "CLAUDE.md"
    local_dst = bundle_root / "LOCAL_MODEL.md"
    shutil.copy2(codex_src, codex_dst)
    shutil.copy2(claude_src, claude_dst)
    shutil.copy2(local_src, local_dst)

    if bool(llm_cfg.get("inject_managed_block", True)):
        docsops_root = str(llm_cfg.get("docsops_root_in_client_repo", "docsops"))
        block = build_managed_instruction_block(docsops_root)
        upsert_managed_block(codex_dst, block)
        upsert_managed_block(claude_dst, block)
        upsert_managed_block(local_dst, block)


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
    task_name = f"VeriOpsWeekly-{client_id}"
    llm_control = profile.get("runtime", {}).get("llm_control", {})
    if not isinstance(llm_control, Mapping):
        llm_control = {}
    llm_mode = str(llm_control.get("llm_mode", "local_default")).strip().lower() or "local_default"
    local_engine = "auto"
    if llm_mode == "external_preferred":
        local_engine = str(profile.get("runtime", {}).get("preferred_llm", "claude")).strip().lower()
        if local_engine not in {"codex", "claude"}:
            local_engine = "auto"

    ops_dir = bundle_root / "ops"
    ops_dir.mkdir(parents=True, exist_ok=True)

    run_sh = f"""#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT=\"$(cd \"$(dirname \"${{BASH_SOURCE[0]}}\")/../..\" && pwd)\"
cd \"$REPO_ROOT\"
mkdir -p reports
if [[ -f ".env.docsops.local" ]]; then
  set -a
  . ".env.docsops.local"
  set +a
fi
while true; do
  if python3 {docsops_root}/scripts/run_autopipeline.py --docsops-root {docsops_root} --reports-dir reports --since {since_days} --runtime-config {docsops_root}/config/client_runtime.yml --mode operator --auto-generate --local-engine {local_engine}; then
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
if (Test-Path \".env.docsops.local\") {{
  Get-Content \".env.docsops.local\" | ForEach-Object {{
    if ($_ -match '^\\s*$' -or $_ -match '^\\s*#') {{ return }}
    $kv = $_.Split('=', 2)
    if ($kv.Length -eq 2) {{
      [Environment]::SetEnvironmentVariable($kv[0].Trim(), $kv[1].Trim(), \"Process\")
    }}
  }}
}}
while ($true) {{
  if (Get-Command py -ErrorAction SilentlyContinue) {{
    py -3 \"{docsops_root}/scripts/run_autopipeline.py\" --docsops-root \"{docsops_root}\" --reports-dir \"reports\" --since {since_days} --runtime-config \"{docsops_root}/config/client_runtime.yml\" --mode \"operator\" --auto-generate --local-engine \"{local_engine}\"
  }} else {{
    python \"{docsops_root}/scripts/run_autopipeline.py\" --docsops-root \"{docsops_root}\" --reports-dir \"reports\" --since {since_days} --runtime-config \"{docsops_root}/config/client_runtime.yml\" --mode \"operator\" --auto-generate --local-engine \"{local_engine}\"
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
            "Client first step (set secrets interactively):\n"
            "1. Run `python3 docsops/scripts/setup_client_env_wizard.py` once.\n\n"
            "If fully-local mode is selected, setup wizard can also install Ollama,\n"
            "pull the base model, and create `veridoc-writer` from `docsops/LOCAL_MODEL.md`.\n\n"
            "Linux/macOS:\n"
            "1. Run `bash docsops/ops/install_cron_weekly.sh` once.\n\n"
            "Windows:\n"
            "1. Run `powershell -ExecutionPolicy Bypass -File docsops/ops/install_windows_task.ps1` once.\n\n"
            "Scheduled run executes full chain:\n"
            "`run_autopipeline -> consolidated report -> docsops_generate`.\n"
        ),
        encoding="utf-8",
    )

    for f in (ops_dir / "run_weekly_docsops.sh", ops_dir / "install_cron_weekly.sh"):
        f.chmod(0o755)


def _append_env(lines: list[str], key: str, value: str, comment: str) -> None:
    lines.append(f"# {comment}")
    lines.append(f"{key}={value}")
    lines.append("")


def build_local_env_template(profile: dict[str, Any], runtime_cfg: dict[str, Any], bundle_root: Path) -> None:
    lines: list[str] = [
        "# VeriOps local secrets template",
        "# Rename/copy to .env.docsops.local in client repo root and fill real values.",
        "# This file is generated from enabled features in client profile.",
        "",
    ]

    integrations = runtime_cfg.get("integrations", {})
    if isinstance(integrations, Mapping):
        algolia = integrations.get("algolia", {})
        if isinstance(algolia, Mapping) and bool(algolia.get("enabled", False)):
            _append_env(lines, str(algolia.get("app_id_env", "ALGOLIA_APP_ID")), "YOUR_ALGOLIA_APP_ID", "Algolia app id")
            _append_env(
                lines,
                str(algolia.get("api_key_env", "ALGOLIA_API_KEY")),
                "YOUR_ALGOLIA_ADMIN_API_KEY",
                "Algolia admin API key",
            )
            _append_env(
                lines,
                str(algolia.get("index_name_env", "ALGOLIA_INDEX_NAME")),
                str(algolia.get("index_name_default", "docs")),
                "Algolia index name",
            )

        ask_ai = integrations.get("ask_ai", {})
        if isinstance(ask_ai, Mapping) and bool(ask_ai.get("enabled", False)):
            provider = str(ask_ai.get("provider", "openai")).strip().lower()
            billing_mode = str(ask_ai.get("billing_mode", "disabled")).strip().lower()
            if provider == "openai":
                _append_env(lines, "OPENAI_API_KEY", "YOUR_OPENAI_API_KEY", "Ask AI: OpenAI API key")
                if billing_mode == "user-subscription":
                    _append_env(
                        lines,
                        "DOCSOPS_SHARED_OPENAI_API_KEY",
                        "",
                        "Ask AI: optional shared OpenAI key for centrally managed entitlement mode",
                    )
            elif provider == "anthropic":
                _append_env(lines, "ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY", "Ask AI: Anthropic API key")
            elif provider == "azure-openai":
                _append_env(lines, "AZURE_OPENAI_API_KEY", "YOUR_AZURE_OPENAI_API_KEY", "Ask AI: Azure OpenAI key")
                _append_env(lines, "AZURE_OPENAI_ENDPOINT", "https://YOUR_RESOURCE.openai.azure.com/", "Ask AI: Azure endpoint")
            else:
                _append_env(lines, "ASK_AI_API_KEY", "YOUR_ASK_AI_API_KEY", "Ask AI: custom provider key")
                _append_env(lines, "ASK_AI_BASE_URL", "https://api.example.com/v1", "Ask AI: custom provider base URL")

    api_first = runtime_cfg.get("api_first", {})
    if isinstance(api_first, Mapping):
        sandbox_backend = str(api_first.get("sandbox_backend", "")).strip().lower()
        external_mock = api_first.get("external_mock", {})
        if (
            bool(api_first.get("enabled", False))
            and sandbox_backend == "external"
            and isinstance(external_mock, Mapping)
            and bool(external_mock.get("enabled", False))
        ):
            provider = str(external_mock.get("provider", "postman")).strip().lower()
            if provider == "postman":
                postman = external_mock.get("postman", {})
                if isinstance(postman, Mapping):
                    _append_env(
                        lines,
                        str(postman.get("api_key_env", "POSTMAN_API_KEY")),
                        "YOUR_POSTMAN_API_KEY",
                        "Postman API key",
                    )
                    _append_env(
                        lines,
                        str(postman.get("workspace_id_env", "POSTMAN_WORKSPACE_ID")),
                        "YOUR_POSTMAN_WORKSPACE_ID",
                        "Postman workspace id",
                    )
                    _append_env(
                        lines,
                        str(postman.get("collection_uid_env", "POSTMAN_COLLECTION_UID")),
                        "",
                        "Postman collection uid (optional; leave empty to import from generated OpenAPI)",
                    )
                    _append_env(
                        lines,
                        str(postman.get("mock_server_id_env", "POSTMAN_MOCK_SERVER_ID")),
                        "",
                        "Postman mock server id (optional; leave empty to auto-create)",
                    )

        if bool(api_first.get("upload_test_assets", False)):
            test_mgmt = api_first.get("test_management", {})
            if isinstance(test_mgmt, Mapping):
                testrail = test_mgmt.get("testrail", {})
                if isinstance(testrail, Mapping):
                    _append_env(
                        lines,
                        str(testrail.get("enabled_env", "TESTRAIL_UPLOAD_ENABLED")),
                        "false",
                        "Set true to enable TestRail upload",
                    )
                    _append_env(lines, str(testrail.get("base_url_env", "TESTRAIL_BASE_URL")), "", "TestRail base URL")
                    _append_env(lines, str(testrail.get("email_env", "TESTRAIL_EMAIL")), "", "TestRail account email")
                    _append_env(lines, str(testrail.get("api_key_env", "TESTRAIL_API_KEY")), "", "TestRail API key")
                    _append_env(lines, str(testrail.get("section_id_env", "TESTRAIL_SECTION_ID")), "", "TestRail section id")
                    _append_env(
                        lines,
                        str(testrail.get("suite_id_env", "TESTRAIL_SUITE_ID")),
                        "",
                        "TestRail suite id (optional)",
                    )

                zephyr = test_mgmt.get("zephyr_scale", {})
                if isinstance(zephyr, Mapping):
                    _append_env(
                        lines,
                        str(zephyr.get("enabled_env", "ZEPHYR_UPLOAD_ENABLED")),
                        "false",
                        "Set true to enable Zephyr upload",
                    )
                    _append_env(
                        lines,
                        str(zephyr.get("base_url_env", "ZEPHYR_SCALE_BASE_URL")),
                        "https://api.zephyrscale.smartbear.com/v2",
                        "Zephyr base URL (optional)",
                    )
                    _append_env(
                        lines,
                        str(zephyr.get("api_token_env", "ZEPHYR_SCALE_API_TOKEN")),
                        "",
                        "Zephyr API token",
                    )
                    _append_env(
                        lines,
                        str(zephyr.get("project_key_env", "ZEPHYR_SCALE_PROJECT_KEY")),
                        "",
                        "Zephyr project key",
                    )
                    _append_env(
                        lines,
                        str(zephyr.get("folder_id_env", "ZEPHYR_SCALE_FOLDER_ID")),
                        "",
                        "Zephyr folder id (optional)",
                    )

    pr_autofix = runtime_cfg.get("pr_autofix", {})
    if isinstance(pr_autofix, Mapping) and bool(pr_autofix.get("enabled", False)):
        _append_env(lines, "DOCSOPS_BOT_TOKEN", "", "Optional GitHub token if default GITHUB_TOKEN cannot push")

    licensing = profile.get("licensing", {})
    if not isinstance(licensing, Mapping):
        licensing = {}
    expose_license_key_env = bool(licensing.get("expose_license_key_env", False))
    expose_dev_plan_override_env = bool(licensing.get("expose_dev_plan_override_env", False))
    license_key_env = str(licensing.get("license_key_env", "VERIOPS_LICENSE_KEY")).strip() or "VERIOPS_LICENSE_KEY"

    # Licensing (client-friendly defaults: signed JWT is shipped in docsops/license.jwt)
    lines.append("# --- Licensing ---")
    lines.append("")
    if expose_license_key_env:
        _append_env(
            lines,
            license_key_env,
            "",
            "Operator-only license key (needed only for encrypted capability-pack refresh workflows).",
        )
    if expose_dev_plan_override_env:
        _append_env(
            lines,
            "VERIOPS_LICENSE_PLAN",
            "",
            "Dev/test override only: set pilot|professional|enterprise to bypass JWT validation.",
        )
    _append_env(
        lines,
        "VERIOPS_TENANT_ID",
        "",
        "Optional: expected tenant/company id for license binding verification.",
    )
    _append_env(
        lines,
        "VERIOPS_COMPANY_DOMAIN",
        "",
        "Optional: expected primary domain for license binding verification.",
    )
    _append_env(
        lines,
        "VERIOPS_UPDATE_SERVER",
        "https://updates.veriops.dev",
        "Server endpoint for signed bundle updates (metadata-only requests).",
    )
    _append_env(
        lines,
        "VERIOPS_PHONE_HOME_URL",
        "https://api.veri-doc.app",
        "Server endpoint for license refresh (metadata-only requests).",
    )
    _append_env(
        lines,
        "VERIOPS_REVOCATION_CHECK_ENABLED",
        "false",
        "Enable server-side revoke checks (metadata-only).",
    )
    _append_env(
        lines,
        "VERIOPS_REVOCATION_URL",
        "https://api.veri-doc.app/billing/license/revocation-check",
        "Revocation endpoint used when VERIOPS_REVOCATION_CHECK_ENABLED=true.",
    )
    _append_env(
        lines,
        "VERIOPS_PACK_REGISTRY_URL",
        "https://api.veri-doc.app/ops/pack-registry/fetch",
        "Encrypted prompt/policy/template pack fetch endpoint.",
    )

    out = bundle_root / ".env.docsops.local.template"
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


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

    runtime_cfg = build_runtime_config(profile)
    branding_cfg = runtime_cfg.get("veridoc_branding", {})
    if isinstance(branding_cfg, Mapping) and bool(branding_cfg.get("enabled", False)) and bool(
        branding_cfg.get("apply_on_weekly", True)
    ):
        custom_tasks = runtime_cfg.get("custom_tasks", {})
        if not isinstance(custom_tasks, Mapping):
            custom_tasks = {"weekly": [], "on_demand": []}
            runtime_cfg["custom_tasks"] = custom_tasks
        weekly = custom_tasks.get("weekly", [])
        if not isinstance(weekly, list):
            weekly = []
            custom_tasks["weekly"] = weekly
        has_branding_task = any(
            isinstance(item, Mapping) and str(item.get("id", "")).strip() == "veridoc-branding-policy"
            for item in weekly
        )
        if not has_branding_task:
            docs_root = str(branding_cfg.get("docs_root", runtime_cfg.get("paths", {}).get("docs_root", "docs")))
            landing_url = str(branding_cfg.get("landing_url", "https://veri-doc.app/")).strip()
            plan = str(branding_cfg.get("plan", "free")).strip().lower()
            cheapest = str(branding_cfg.get("cheapest_paid_plan", "starter")).strip().lower()
            report_path = str(branding_cfg.get("report_path", "reports/veridoc_branding_policy_report.json")).strip()
            referral_env = str(branding_cfg.get("referral_code_env", "")).strip()
            badge_opt_out = bool(branding_cfg.get("badge_opt_out", False))
            opt_out_flag = " --badge-opt-out" if badge_opt_out else ""
            referral_arg = ""
            if referral_env:
                referral_arg = f" --referral-code \"${{{referral_env}:-}}\""
            cmd = (
                f"python3 docsops/scripts/apply_veridoc_branding_policy.py "
                f"--repo-root . --docs-root {docs_root} --landing-url {landing_url} "
                f"--plan {plan} --cheapest-paid-plan {cheapest} "
                f"--report {report_path}{opt_out_flag}{referral_arg}"
            )
            weekly.append(
                {
                    "id": "veridoc-branding-policy",
                    "enabled": True,
                    "command": cmd,
                    "continue_on_error": False,
                }
            )

    include_scripts = [str(rel) for rel in bundle_cfg.get("include_scripts", [])]
    required_scripts: list[str] = []
    # License gate and pack runtime are always required (all gated scripts depend on them)
    required_scripts.append("scripts/license_gate.py")
    required_scripts.append("scripts/pack_runtime.py")
    required_scripts.append("scripts/check_updates.py")
    required_scripts.append("scripts/rollback.py")
    required_scripts.append("scripts/finalize_docs_gate.py")
    required_scripts.append("scripts/setup_client_env_wizard.py")
    required_scripts.append("scripts/run_autopipeline.py")
    required_scripts.append("scripts/publish_docs_review_branch.py")
    required_scripts.append("scripts/docs_ci_bootstrap.py")
    required_scripts.append("scripts/run_docs_ci_checks.py")
    required_scripts.append("scripts/docsops_generate.py")
    required_scripts.append("scripts/llm_egress.py")
    required_scripts.append("scripts/flow_feedback.py")
    if isinstance(branding_cfg, Mapping) and bool(branding_cfg.get("enabled", False)):
        required_scripts.append("scripts/apply_veridoc_branding_policy.py")
    pr_autofix = runtime_cfg.get("pr_autofix", {})
    if isinstance(pr_autofix, Mapping) and bool(pr_autofix.get("enabled", False)):
        required_scripts.append("scripts/auto_fix_pr_docs.py")
    api_first = runtime_cfg.get("api_first", {})
    api_protocols = runtime_cfg.get("api_protocols", [])
    api_protocol_settings = runtime_cfg.get("api_protocol_settings", {})
    non_rest_enabled = False
    if isinstance(api_protocols, list):
        for protocol in api_protocols:
            key = str(protocol).strip().lower()
            if key not in {"graphql", "grpc", "asyncapi", "websocket"}:
                continue
            cfg = api_protocol_settings.get(key, {}) if isinstance(api_protocol_settings, Mapping) else {}
            if not isinstance(cfg, Mapping) or bool(cfg.get("enabled", True)):
                non_rest_enabled = True
                break
    if isinstance(api_first, Mapping):
        external_mock = api_first.get("external_mock", {})
        if bool(api_first.get("enabled", False)) and isinstance(external_mock, Mapping):
            required_scripts.extend(
                [
                    "scripts/run_api_first_flow.py",
                    "scripts/generate_openapi_from_planning_notes.py",
                    "scripts/validate_openapi_contract.py",
                    "scripts/generate_fastapi_stubs_from_openapi.py",
                    "scripts/self_verify_api_user_path.py",
                    "scripts/normalize_docs.py",
                    "scripts/apply_openapi_overrides.py",
                    "scripts/check_openapi_regression.py",
                    "scripts/generate_api_test_assets.py",
                ]
            )
            if bool(api_first.get("upload_test_assets", False)):
                required_scripts.append("scripts/upload_api_test_assets.py")
            if str(api_first.get("sandbox_backend", "")).strip().lower() == "external" and bool(
                external_mock.get("enabled", False)
            ):
                required_scripts.append("scripts/ensure_external_mock_server.py")
    if non_rest_enabled:
        required_scripts.extend(
            [
                "scripts/run_multi_protocol_contract_flow.py",
                "scripts/generate_protocol_contract_from_planning_notes.py",
                "scripts/generate_protocol_server_stubs.py",
                "scripts/generate_protocol_docs.py",
                "scripts/generate_protocol_test_assets.py",
                "scripts/check_protocol_regression.py",
                "scripts/validate_graphql_contract.py",
                "scripts/validate_proto_contract.py",
                "scripts/validate_asyncapi_contract.py",
                "scripts/validate_websocket_contract.py",
                "scripts/run_protocol_lint_stack.py",
                "scripts/run_protocol_self_verify.py",
                "scripts/run_protocol_docs_quality_suite.py",
                "scripts/validate_protocol_test_coverage.py",
                "scripts/publish_protocol_assets.py",
                "scripts/multi_protocol_engine.py",
                "scripts/api_protocols.py",
            ]
        )

    # Algolia widget generator when Algolia is enabled
    integrations = runtime_cfg.get("integrations", {})
    if isinstance(integrations, Mapping):
        algolia_cfg = integrations.get("algolia", {})
        if isinstance(algolia_cfg, Mapping) and bool(algolia_cfg.get("enabled", False)):
            required_scripts.append("scripts/generate_algolia_widget.py")
        ask_ai_cfg = integrations.get("ask_ai", {})
        if isinstance(ask_ai_cfg, Mapping):
            if bool(ask_ai_cfg.get("auto_configure_on_provision", True)):
                required_scripts.append("scripts/configure_ask_ai.py")
            if bool(ask_ai_cfg.get("install_runtime_pack", False)):
                required_scripts.append("scripts/install_ask_ai_runtime.py")
                include_paths = [str(rel) for rel in bundle_cfg.get("include_paths", [])]
                if "runtime/ask-ai-pack" not in include_paths:
                    include_paths.append("runtime/ask-ai-pack")
                bundle_cfg["include_paths"] = include_paths

    for req in required_scripts:
        if req not in include_scripts:
            include_scripts.append(req)
    include_paths = [str(rel) for rel in bundle_cfg.get("include_paths", [])]
    ip_protection_path = REPO_ROOT / "config" / "ip_protection"
    if ip_protection_path.exists() and "config/ip_protection" not in include_paths:
        include_paths.append("config/ip_protection")
    bundle_cfg["include_paths"] = include_paths

    for rel in include_scripts:
        copy_into_bundle(str(rel), bundle_root)
    for rel in bundle_cfg.get("include_docs", []):
        copy_into_bundle(str(rel), bundle_root)
    for rel in bundle_cfg.get("include_paths", []):
        copy_path_into_bundle(str(rel), bundle_root)

    write_yaml(bundle_root / "config" / "client_runtime.yml", runtime_cfg)

    build_llm_instruction_files(profile, bundle_root)
    build_automation_files(profile, bundle_root)
    build_local_env_template(profile, runtime_cfg, bundle_root)
    build_vale_config(profile, bundle_root)
    build_licensing_infrastructure(profile, bundle_root)

    operator_note = {
        "client": {
            "id": client_id,
            "company_name": company,
            "contact_email": client.get("contact_email", ""),
        },
        "local_use": {
            "llm_instructions": ["AGENTS.md", "CLAUDE.md", "LOCAL_MODEL.md"],
            "runtime_config": "config/client_runtime.yml",
            "policy_pack": "policy_packs/selected.yml",
            "automation_runbook": "ops/runbook.md",
            "local_env_template": ".env.docsops.local.template",
            "vale_config": ".vale.ini",
            "traceability_manifest": "TRACEABILITY.yml",
        },
        "licensing": {
            "public_key": "docsops/keys/veriops-licensing.pub",
            "license_jwt": "docsops/license.jwt",
            "capability_pack": "docsops/.capability_pack.enc",
            "activation": "License key activates features. "
                          "All plans use the same bundle.",
            "binding": "Optional license claims: tenant_id and company_domain.",
        },
    }
    write_yaml(bundle_root / "BUNDLE_INFO.yml", operator_note)

    build_licensed_files(profile, bundle_root)

    # Traceability watermark for provenance and leak attribution.
    now_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    rev = ""
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(REPO_ROOT),
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode == 0:
            rev = completed.stdout.strip()
    except (RuntimeError, ValueError, TypeError, OSError):  # noqa: BLE001
        rev = ""
    build_fingerprint = hashlib.sha256(f"{client_id}|{company}|{now_utc}|{rev}".encode("utf-8")).hexdigest()[:24]
    traceability = {
        "build_id": f"{client_id}-{build_fingerprint}",
        "generated_at_utc": now_utc,
        "source_git_commit": rev,
        "client_id": client_id,
        "company_name": company,
        "tenant_id": str(client.get("tenant_id", client_id)),
        "company_domain": str(client.get("company_domain", "")),
        "watermark_note": "Bundle contains client-specific provenance metadata for traceability.",
    }
    write_yaml(bundle_root / "TRACEABILITY.yml", traceability)
    (bundle_root / "docsops" / ".bundle_trace.json").write_text(
        json.dumps(traceability, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )

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

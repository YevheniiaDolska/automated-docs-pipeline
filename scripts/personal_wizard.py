#!/usr/bin/env python3
"""Personal documentation pipeline wizard.

Same functionality as the full client onboarding wizard but WITHOUT:
- Licensing / license gate / JWT validation
- Encryption / capability pack generation
- Licensed files (LICENSE-COMMERCIAL.md, NOTICE)

Instead of directly copying configs, this wizard:
1. Runs an interactive profile wizard (or loads an existing profile).
2. Builds a self-contained bundle (same structure as client bundles, minus licensing).
3. Prints the bundle path so the user can install it via provision_client_repo.py
   or manually copy it -- exactly like a real client would on a separate machine.

Usage:
  python3 scripts/personal_wizard.py
  python3 scripts/personal_wizard.py --profile profiles/clients/my.client.yml --yes
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.api_protocols import merge_protocol_settings, normalize_protocols
from scripts.build_client_bundle import (
    build_automation_files,
    build_llm_instruction_files,
    build_runtime_config,
    build_vale_config,
    copy_into_bundle,
    copy_path_into_bundle,
    deep_merge,
    read_yaml,
    write_yaml,
)

PRESETS_DIR = REPO_ROOT / "profiles" / "clients" / "presets"
TEMPLATE_PROFILE = REPO_ROOT / "profiles" / "clients" / "_template.client.yml"

LICENSING_SCRIPTS = {
    "scripts/license_gate.py",
    "scripts/pack_runtime.py",
    "scripts/check_updates.py",
    "scripts/rollback.py",
}


# -- Prompt helpers -----------------------------------------------------------

def _prompt(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    raw = input(f"{prompt}{suffix}: ").strip()
    if raw:
        return raw
    if default is not None:
        return default
    raise ValueError(f"Value is required: {prompt}")


def _prompt_choice(prompt: str, options: list[str], default: str) -> str:
    opts = "/".join(options)
    while True:
        value = _prompt(f"{prompt} ({opts})", default).strip().lower()
        if value in options:
            return value
        print(f"Choose one of: {opts}")


def _prompt_yes_no(prompt: str, default_yes: bool = True) -> bool:
    suffix = "[Y/n]" if default_yes else "[y/N]"
    raw = input(f"{prompt} {suffix}: ").strip().lower()
    if not raw:
        return default_yes
    return raw in {"y", "yes"}


def _prompt_csv(prompt: str, default_values: list[str]) -> list[str]:
    default = ",".join(default_values)
    raw = _prompt(prompt, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9\-]+", "-", value.lower().strip())
    return re.sub(r"-{2,}", "-", slug).strip("-")


# -- Profile helpers ----------------------------------------------------------

def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return payload


def _build_profile_from_preset(preset_name: str) -> dict[str, Any]:
    template = _load_yaml_mapping(TEMPLATE_PROFILE)
    preset_path = PRESETS_DIR / f"{preset_name}.yml"
    if preset_path.exists():
        override = _load_yaml_mapping(preset_path)
        template = deep_merge(template, override)
    return template


def _save_generated_profile(profile: dict[str, Any], client_id: str) -> Path:
    out_dir = REPO_ROOT / "profiles" / "clients" / "generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{client_id}.client.yml"
    write_yaml(out_path, profile)
    return out_path


# -- Interactive profile wizard (no licensing) --------------------------------

def _create_personal_profile() -> tuple[Path, str]:
    """Run interactive profile wizard without licensing questions.

    Returns (profile_path, client_id).
    """
    print("Preset-based profile creation")
    preset = _prompt_choice(
        "Choose preset",
        ["small", "startup", "enterprise", "pilot-evidence"],
        "startup",
    )
    profile = _build_profile_from_preset(preset)

    company_name = _prompt(
        "Company / project name",
        str(profile["client"].get("company_name", "My Project")),
    )
    suggested_id = _slugify(company_name) or "personal"
    client_id = _slugify(_prompt("Client ID (slug)", suggested_id))
    if not client_id:
        raise ValueError("Client ID cannot be empty.")
    contact_email = _prompt(
        "Contact email",
        str(profile["client"].get("contact_email", "me@example.com")),
    )
    print(
        "LLM execution profiles:\n"
        "- fully-local: strict local-first mode for regulated environments;\n"
        "  external LLM fallback is blocked by default.\n"
        "- hybrid: cloud-capable mode for normal teams using hosted Git/cloud workflows;\n"
        "  external LLM usage is allowed.\n"
        "- cloud: same trust model as hybrid, cloud-first behavior."
    )
    llm_tier = _prompt_choice(
        "LLM mode",
        ["fully-local", "hybrid", "cloud"],
        "hybrid",
    )
    strict_local = llm_tier == "fully-local"
    if strict_local:
        print(
            "[info] Fully local mode selected: no external LLM egress by default. "
            "Quality on hardest synthesis tasks can be ~10-15% lower."
        )
        print(
            "[info] Strict local-first guardrails will auto-disable external egress paths: "
            "Ask AI cloud provider, Algolia upload, external mock backend, and test-management uploads."
        )
    else:
        print(
            "[info] Cloud-capable mode selected: external LLM providers are allowed. "
            "Use this when data already leaves your perimeter by policy."
        )

    # No licensing questions -- personal wizard skips them entirely

    docs_root = _prompt(
        "Docs path in client repo",
        str(profile["runtime"].get("docs_root", "docs")),
    )
    api_root = _prompt(
        "API path in client repo",
        str(profile["runtime"].get("api_root", "api")),
    )
    sdk_root = _prompt(
        "SDK path in client repo",
        str(profile["runtime"].get("sdk_root", "sdk")),
    )
    flow_mode = _prompt_choice(
        "Docs flow mode",
        ["code-first", "api-first", "hybrid"],
        str(profile["runtime"]["docs_flow"].get("mode", "code-first")),
    )
    style_guide = _prompt_choice(
        "Vale style guide",
        ["google", "microsoft", "hybrid"],
        str(profile.get("bundle", {}).get("style_guide", "google")).strip().lower(),
    )
    output_targets = _prompt_csv(
        "Publish targets (comma-separated, e.g. mkdocs,readme,github)",
        [str(x) for x in profile["runtime"].get("output_targets", ["mkdocs"])],
    )
    if not output_targets:
        output_targets = ["mkdocs"]

    enable_pr_autofix = _prompt_yes_no(
        "Enable optional PR auto-fix workflow?",
        default_yes=False,
    )

    sandbox_backend_default = str(
        profile["runtime"]["api_first"].get("sandbox_backend", "external")
    )
    if flow_mode in {"api-first", "hybrid"}:
        sandbox_options = ["docker", "prism"] if strict_local else [
            "docker",
            "prism",
            "external",
        ]
        sandbox_default = (
            sandbox_backend_default
            if sandbox_backend_default in sandbox_options
            else "prism"
        )
        sandbox_backend = _prompt_choice(
            "API sandbox backend",
            sandbox_options,
            sandbox_default,
        )
        profile["runtime"]["api_first"]["sandbox_backend"] = sandbox_backend
        if sandbox_backend == "external":
            mock_default = str(
                profile["runtime"]["api_first"].get(
                    "mock_base_url",
                    "https://<your-real-public-mock-url>/v1",
                )
            )
            profile["runtime"]["api_first"]["mock_base_url"] = _prompt(
                "External mock base URL",
                mock_default,
            )
        upload_assets_default = bool(
            profile["runtime"]["api_first"].get("upload_test_assets", False)
        )
        if strict_local:
            profile["runtime"]["api_first"]["upload_test_assets"] = False
            profile["runtime"]["api_first"]["external_mock"]["enabled"] = False
        else:
            profile["runtime"]["api_first"]["upload_test_assets"] = _prompt_yes_no(
                "Enable API test asset upload (TestRail/Zephyr)?",
                default_yes=upload_assets_default,
            )

    enable_algolia = False
    if not strict_local:
        enable_algolia = _prompt_yes_no(
            "Enable Algolia integration?",
            default_yes=bool(
                profile["runtime"]["integrations"]["algolia"].get("enabled", False)
            ),
        )
    algolia_site_generator = "mkdocs"
    if enable_algolia and not strict_local:
        algolia_site_generator = _prompt_choice(
            "Algolia: site generator for search widget",
            ["mkdocs", "docusaurus", "hugo", "vitepress", "custom"],
            str(
                profile["runtime"]["integrations"]["algolia"].get(
                    "site_generator", "mkdocs"
                )
            ),
        )
    enable_ask_ai = strict_local
    if not strict_local:
        enable_ask_ai = _prompt_yes_no(
            "Enable Ask AI integration?",
            default_yes=bool(
                profile["runtime"]["integrations"]["ask_ai"].get("enabled", False)
            ),
        )
    enable_veridoc_branding = _prompt_yes_no(
        "Enable Powered by VeriDoc badge policy automation?",
        default_yes=bool(
            profile["runtime"].get("veridoc_branding", {}).get("enabled", False)
        ),
    )
    branding_landing_url = "https://veri-doc.app/"
    branding_plan = "free"
    branding_cheapest = "pro"
    branding_badge_opt_out = False
    if enable_veridoc_branding:
        branding_defaults = profile["runtime"].get("veridoc_branding", {})
        if not isinstance(branding_defaults, dict):
            branding_defaults = {}
        branding_landing_url = _prompt(
            "Branding landing URL",
            str(branding_defaults.get("landing_url", "https://veri-doc.app/")),
        )
        branding_plan = _prompt_choice(
            "Branding plan",
            ["pilot", "free", "starter", "pro", "business", "enterprise"],
            str(branding_defaults.get("plan", "free")).strip().lower(),
        )
        # Do not ask operator at bundle-build time.
        # Client controls opt-out later in product UI (Settings -> Referrals).
        branding_badge_opt_out = bool(branding_defaults.get("badge_opt_out", False))

    enable_intent_weekly = _prompt_yes_no(
        "Enable weekly intent experience build?",
        default_yes=True,
    )
    finalize_gate_cfg = profile["runtime"].get("finalize_gate", {})
    enable_finalize_commit_confirmation = False
    if isinstance(finalize_gate_cfg, dict):
        enable_finalize_commit_confirmation = _prompt_yes_no(
            "Finalize gate: ask interactive confirmation before commit?",
            default_yes=bool(
                finalize_gate_cfg.get("ask_commit_confirmation", False)
            ),
        )

    advanced_default = preset != "pilot-evidence"
    if _prompt_yes_no(
        "Configure full advanced options now?",
        default_yes=advanced_default,
    ):
        modules = profile["runtime"].get("modules", {})
        if isinstance(modules, dict):
            print("Module toggles:")
            for key in sorted(modules.keys()):
                modules[key] = _prompt_yes_no(
                    f"  Enable module '{key}'?",
                    default_yes=bool(modules[key]),
                )

        bundle_cfg = profile.get("bundle", {})
        include_paths = bundle_cfg.get("include_paths", [])
        if isinstance(include_paths, list):
            bundle_cfg["include_paths"] = _prompt_csv(
                "Bundle include_paths (comma-separated)",
                [str(x) for x in include_paths],
            )

        include_scripts = bundle_cfg.get("include_scripts", [])
        if isinstance(include_scripts, list):
            extra_scripts = _prompt_csv(
                "Extra include_scripts to append (comma-separated, optional)",
                [],
            )
            for script in extra_scripts:
                if script not in include_scripts:
                    include_scripts.append(script)
            bundle_cfg["include_scripts"] = include_scripts

        weekly_tasks = (
            profile["runtime"].get("custom_tasks", {}).get("weekly", [])
        )
        if isinstance(weekly_tasks, list):
            extra_tasks = _prompt_csv(
                "Extra weekly task commands to append (comma-separated, optional)",
                [],
            )
            for command in extra_tasks:
                weekly_tasks.append(
                    {
                        "id": f"custom-{len(weekly_tasks) + 1}",
                        "enabled": True,
                        "command": command,
                        "continue_on_error": True,
                    }
                )

        if flow_mode in {"api-first", "hybrid"}:
            api_first = profile["runtime"].get("api_first", {})
            if isinstance(api_first, dict):
                api_first["verify_user_path"] = _prompt_yes_no(
                    "Enable API user-path verification?",
                    default_yes=bool(api_first.get("verify_user_path", False)),
                )
                api_first["sync_playground_endpoint"] = _prompt_yes_no(
                    "Sync sandbox URL into docs playground config?",
                    default_yes=bool(
                        api_first.get("sync_playground_endpoint", True)
                    ),
                )
                api_first["generate_test_assets"] = _prompt_yes_no(
                    "Generate API test assets from API contracts (REST/GraphQL/gRPC/AsyncAPI/WebSocket)?",
                    default_yes=bool(
                        api_first.get("generate_test_assets", True)
                    ),
                )

            git_sync = profile["runtime"].get("git_sync", {})
            if isinstance(git_sync, dict):
                git_sync["enabled"] = _prompt_yes_no(
                    "Enable git sync (auto pull before weekly run)?",
                    default_yes=bool(git_sync.get("enabled", True)),
                )
                if git_sync["enabled"]:
                    git_sync["repo_path"] = _prompt(
                        "Git sync repo path",
                        str(git_sync.get("repo_path", ".")),
                    )
                    git_sync["remote"] = _prompt(
                        "Git sync remote",
                        str(git_sync.get("remote", "origin")),
                    )
                    git_sync["branch"] = _prompt(
                        "Git sync branch (empty=detected)",
                        str(git_sync.get("branch", "")),
                    )

        integrations = profile["runtime"].get("integrations", {})
        if isinstance(integrations, dict):
            algolia = integrations.get("algolia", {})
            if isinstance(algolia, dict) and bool(enable_algolia):
                algolia["upload_on_weekly"] = _prompt_yes_no(
                    "Algolia: upload index on weekly run?",
                    default_yes=bool(algolia.get("upload_on_weekly", False)),
                )

            ask_ai = integrations.get("ask_ai", {})
            if isinstance(ask_ai, dict) and bool(enable_ask_ai):
                ask_ai["provider"] = _prompt_choice(
                    "Ask AI provider",
                    ["openai", "anthropic", "azure-openai", "custom", "local", "ollama"],
                    str(ask_ai.get("provider", "openai" if not strict_local else "local")).strip().lower(),
                )
                ask_ai["billing_mode"] = _prompt_choice(
                    "Ask AI billing mode",
                    ["disabled", "user-subscription", "platform-paid"],
                    str(ask_ai.get("billing_mode", "disabled")).strip().lower(),
                )
                ask_ai["install_runtime_pack"] = _prompt_yes_no(
                    "Ask AI: install runtime pack during provisioning?",
                    default_yes=bool(
                        ask_ai.get("install_runtime_pack", False)
                    ),
                )

    # -- Assign values to profile (no licensing section) ----------------------
    profile["client"]["id"] = client_id
    profile["client"]["company_name"] = company_name
    profile["client"]["contact_email"] = contact_email
    # No profile["licensing"] = {...} -- personal wizard skips licensing
    profile["runtime"]["docs_root"] = docs_root
    profile["runtime"]["api_root"] = api_root
    profile["runtime"]["sdk_root"] = sdk_root
    profile["runtime"]["docs_flow"]["mode"] = flow_mode
    profile["bundle"]["style_guide"] = style_guide
    profile["runtime"]["output_targets"] = output_targets
    profile["runtime"]["pr_autofix"]["enabled"] = enable_pr_autofix
    profile["runtime"]["integrations"]["algolia"]["enabled"] = enable_algolia
    if enable_algolia:
        profile["runtime"]["integrations"]["algolia"][
            "site_generator"
        ] = algolia_site_generator
        profile["runtime"]["integrations"]["algolia"][
            "generate_search_widget"
        ] = True
    profile["runtime"]["integrations"]["ask_ai"]["enabled"] = enable_ask_ai
    llm_control = profile["runtime"].get("llm_control", {})
    if not isinstance(llm_control, dict):
        llm_control = {}
    llm_control["llm_mode"] = "local_default" if strict_local else "external_preferred"
    llm_control["local_model"] = "veridoc-writer"
    llm_control["local_base_model"] = "qwen2.5:7b"
    llm_control["local_model_command"] = "ollama run {model} \"{prompt}\""
    llm_control["auto_install_local_model_on_setup"] = True
    llm_control["strict_local_first"] = strict_local
    llm_control["quality_delta_note"] = (
        "Fully local mode may reduce output quality by ~10-15% on hardest synthesis tasks."
    )
    if strict_local:
        llm_control["external_llm_allowed"] = False
        llm_control["require_explicit_approval"] = True
    else:
        llm_control["external_llm_allowed"] = True
        llm_control["require_explicit_approval"] = False
    llm_control["approval_cache_scope"] = "run"
    llm_control["redact_before_external"] = True
    profile["runtime"]["llm_control"] = llm_control
    if strict_local:
        integrations = profile["runtime"].get("integrations", {})
        if isinstance(integrations, dict):
            algolia_cfg = integrations.get("algolia", {})
            if isinstance(algolia_cfg, dict):
                algolia_cfg["enabled"] = False
                algolia_cfg["upload_on_weekly"] = False
            ask_ai_cfg = integrations.get("ask_ai", {})
            if isinstance(ask_ai_cfg, dict):
                ask_ai_cfg["enabled"] = True
                ask_ai_cfg["provider"] = "local"
                ask_ai_cfg["model"] = "qwen2.5:7b"
                ask_ai_cfg["base_url"] = "http://localhost:11434/v1"
                ask_ai_cfg["install_runtime_pack"] = True
                ask_ai_cfg["billing_mode"] = "disabled"

        api_first_cfg = profile["runtime"].get("api_first", {})
        if isinstance(api_first_cfg, dict):
            api_first_cfg["sandbox_backend"] = "prism"
            api_first_cfg["upload_test_assets"] = False
            external_mock_cfg = api_first_cfg.get("external_mock", {})
            if isinstance(external_mock_cfg, dict):
                external_mock_cfg["enabled"] = False
    profile["runtime"]["veridoc_branding"] = {
        "enabled": enable_veridoc_branding,
        "landing_url": branding_landing_url,
        "plan": branding_plan,
        "cheapest_paid_plan": branding_cheapest,
        "badge_opt_out": bool(branding_badge_opt_out),
        "referral_code_env": "VERIDOC_REFERRAL_CODE",
        "docs_root": docs_root,
        "report_path": "reports/veridoc_branding_policy_report.json",
        "apply_on_weekly": True,
    }
    if isinstance(finalize_gate_cfg, dict):
        finalize_gate_cfg[
            "ask_commit_confirmation"
        ] = enable_finalize_commit_confirmation
        if (
            enable_finalize_commit_confirmation
            and "commit_on_approve" in finalize_gate_cfg
        ):
            finalize_gate_cfg["commit_on_approve"] = True
    weekly_tasks = (
        profile["runtime"].get("custom_tasks", {}).get("weekly", [])
    )
    if isinstance(weekly_tasks, list):
        found = False
        for task in weekly_tasks:
            if (
                isinstance(task, dict)
                and str(task.get("id", "")).strip() == "intent-experiences"
            ):
                task["enabled"] = enable_intent_weekly
                found = True
        if enable_intent_weekly and not found:
            weekly_tasks.append(
                {
                    "id": "intent-experiences",
                    "enabled": True,
                    "command": "python3 docsops/scripts/build_all_intent_experiences.py",
                    "continue_on_error": True,
                }
            )
    if flow_mode == "api-first":
        profile["runtime"]["api_first"]["enabled"] = True
    elif flow_mode == "code-first":
        profile["runtime"]["api_first"]["enabled"] = False

    out_path = _save_generated_profile(profile, client_id)
    print(f"[ok] generated profile: {out_path}")
    return out_path, client_id


# -- .env template (no licensing env vars) ------------------------------------

def _append_env(lines: list[str], key: str, value: str, comment: str) -> None:
    lines.append(f"# {comment}")
    lines.append(f"{key}={value}")
    lines.append("")


def build_personal_env_template(
    runtime_cfg: dict[str, Any],
    bundle_root: Path,
) -> None:
    """Build .env template identical to build_local_env_template but without licensing vars."""
    lines: list[str] = [
        "# VeriOps local secrets template (personal bundle -- no licensing)",
        "# Rename/copy to .env.docsops.local in client repo root and fill real values.",
        "# This file is generated from enabled features in client profile.",
        "",
    ]

    integrations = runtime_cfg.get("integrations", {})
    if isinstance(integrations, Mapping):
        algolia = integrations.get("algolia", {})
        if isinstance(algolia, Mapping) and bool(algolia.get("enabled", False)):
            _append_env(
                lines,
                str(algolia.get("app_id_env", "ALGOLIA_APP_ID")),
                "YOUR_ALGOLIA_APP_ID",
                "Algolia app id",
            )
            _append_env(
                lines,
                str(algolia.get("api_key_env", "ALGOLIA_API_KEY")),
                "YOUR_ALGOLIA_ADMIN_API_KEY",
                "Algolia admin API key",
            )
            _append_env(
                lines,
                str(algolia.get("search_api_key_env", "ALGOLIA_SEARCH_API_KEY")),
                "YOUR_ALGOLIA_SEARCH_API_KEY",
                "Algolia search API key for docs UI widget",
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
            billing_mode = str(
                ask_ai.get("billing_mode", "disabled")
            ).strip().lower()
            if billing_mode == "user-subscription":
                shared_key_env = "DOCSOPS_SHARED_OPENAI_API_KEY" if provider == "openai" else "DOCSOPS_SHARED_ASK_AI_API_KEY"
                _append_env(
                    lines,
                    shared_key_env,
                    "",
                    "Ask AI: optional shared fallback key for centrally managed entitlement mode",
                )
            if provider == "openai":
                _append_env(
                    lines,
                    "OPENAI_API_KEY",
                    "YOUR_OPENAI_API_KEY",
                    "Ask AI: OpenAI API key",
                )
            elif provider == "anthropic":
                _append_env(
                    lines,
                    "ANTHROPIC_API_KEY",
                    "YOUR_ANTHROPIC_API_KEY",
                    "Ask AI: Anthropic API key",
                )
            elif provider == "azure-openai":
                _append_env(
                    lines,
                    "AZURE_OPENAI_API_KEY",
                    "YOUR_AZURE_OPENAI_API_KEY",
                    "Ask AI: Azure OpenAI key",
                )
                _append_env(
                    lines,
                    "AZURE_OPENAI_ENDPOINT",
                    "https://YOUR_RESOURCE.openai.azure.com/",
                    "Ask AI: Azure endpoint",
                )
            elif provider in {"local", "ollama"}:
                _append_env(
                    lines,
                    "ASK_AI_BASE_URL",
                    "http://localhost:11434/v1",
                    "Ask AI: local Ollama endpoint",
                )
            else:
                _append_env(
                    lines,
                    "ASK_AI_API_KEY",
                    "YOUR_ASK_AI_API_KEY",
                    "Ask AI: custom provider key",
                )
                _append_env(
                    lines,
                    "ASK_AI_BASE_URL",
                    "https://api.example.com/v1",
                    "Ask AI: custom provider base URL",
                )

    api_first = runtime_cfg.get("api_first", {})
    if isinstance(api_first, Mapping):
        sandbox_backend = str(
            api_first.get("sandbox_backend", "")
        ).strip().lower()
        external_mock = api_first.get("external_mock", {})
        if (
            bool(api_first.get("enabled", False))
            and sandbox_backend == "external"
            and isinstance(external_mock, Mapping)
            and bool(external_mock.get("enabled", False))
        ):
            provider = str(
                external_mock.get("provider", "postman")
            ).strip().lower()
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
                        str(
                            postman.get(
                                "workspace_id_env", "POSTMAN_WORKSPACE_ID"
                            )
                        ),
                        "YOUR_POSTMAN_WORKSPACE_ID",
                        "Postman workspace id",
                    )
                    _append_env(
                        lines,
                        str(
                            postman.get(
                                "collection_uid_env", "POSTMAN_COLLECTION_UID"
                            )
                        ),
                        "",
                        "Postman collection uid (optional; leave empty to import from generated OpenAPI)",
                    )
                    _append_env(
                        lines,
                        str(
                            postman.get(
                                "mock_server_id_env",
                                "POSTMAN_MOCK_SERVER_ID",
                            )
                        ),
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
                        str(
                            testrail.get(
                                "enabled_env", "TESTRAIL_UPLOAD_ENABLED"
                            )
                        ),
                        "false",
                        "Set true to enable TestRail upload",
                    )
                    _append_env(
                        lines,
                        str(testrail.get("base_url_env", "TESTRAIL_BASE_URL")),
                        "",
                        "TestRail base URL",
                    )
                    _append_env(
                        lines,
                        str(testrail.get("email_env", "TESTRAIL_EMAIL")),
                        "",
                        "TestRail account email",
                    )
                    _append_env(
                        lines,
                        str(testrail.get("api_key_env", "TESTRAIL_API_KEY")),
                        "",
                        "TestRail API key",
                    )
                    _append_env(
                        lines,
                        str(
                            testrail.get(
                                "section_id_env", "TESTRAIL_SECTION_ID"
                            )
                        ),
                        "",
                        "TestRail section id",
                    )
                    _append_env(
                        lines,
                        str(
                            testrail.get("suite_id_env", "TESTRAIL_SUITE_ID")
                        ),
                        "",
                        "TestRail suite id (optional)",
                    )

                zephyr = test_mgmt.get("zephyr_scale", {})
                if isinstance(zephyr, Mapping):
                    _append_env(
                        lines,
                        str(
                            zephyr.get(
                                "enabled_env", "ZEPHYR_UPLOAD_ENABLED"
                            )
                        ),
                        "false",
                        "Set true to enable Zephyr upload",
                    )
                    _append_env(
                        lines,
                        str(
                            zephyr.get(
                                "base_url_env",
                                "ZEPHYR_SCALE_BASE_URL",
                            )
                        ),
                        "https://api.zephyrscale.smartbear.com/v2",
                        "Zephyr base URL (optional)",
                    )
                    _append_env(
                        lines,
                        str(
                            zephyr.get(
                                "api_token_env",
                                "ZEPHYR_SCALE_API_TOKEN",
                            )
                        ),
                        "",
                        "Zephyr API token",
                    )
                    _append_env(
                        lines,
                        str(
                            zephyr.get(
                                "project_key_env",
                                "ZEPHYR_SCALE_PROJECT_KEY",
                            )
                        ),
                        "",
                        "Zephyr project key",
                    )
                    _append_env(
                        lines,
                        str(
                            zephyr.get(
                                "folder_id_env",
                                "ZEPHYR_SCALE_FOLDER_ID",
                            )
                        ),
                        "",
                        "Zephyr folder id (optional)",
                    )

    branding = runtime_cfg.get("veridoc_branding", {})
    if isinstance(branding, Mapping) and bool(branding.get("enabled", False)):
        referral_env = str(
            branding.get("referral_code_env", "VERIDOC_REFERRAL_CODE")
        ).strip()
        _append_env(
            lines,
            referral_env,
            "",
            "Optional referral code used in Powered by VeriDoc badge links for higher plans.",
        )

    pr_autofix = runtime_cfg.get("pr_autofix", {})
    if isinstance(pr_autofix, Mapping) and bool(
        pr_autofix.get("enabled", False)
    ):
        _append_env(
            lines,
            "DOCSOPS_BOT_TOKEN",
            "",
            "Optional GitHub token if default GITHUB_TOKEN cannot push",
        )

    # No licensing env vars -- personal bundle does not use license_gate.py

    out = bundle_root / ".env.docsops.local.template"
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


# -- Personal bundle builder (no licensing) -----------------------------------

def create_personal_bundle(profile_path: Path) -> Path:
    """Build a self-contained bundle like create_bundle() but without licensing.

    Skips: build_licensing_infrastructure, build_licensed_files,
    licensing scripts (license_gate, pack_runtime, check_updates, rollback),
    licensing env vars, licensing section in BUNDLE_INFO.
    """
    profile = read_yaml(profile_path)
    client = profile.get("client", {})
    bundle_cfg = profile.get("bundle", {})

    client_id = str(client.get("id", "")).strip()
    company = str(client.get("company_name", "")).strip()
    if not client_id or not company:
        raise ValueError("client.id and client.company_name are required")

    out_dir = str(bundle_cfg.get("output_dir", "generated/personal_bundles"))
    bundle_root = REPO_ROOT / out_dir / client_id

    if bundle_root.exists():
        shutil.rmtree(bundle_root)
    bundle_root.mkdir(parents=True, exist_ok=True)

    # Policy pack
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

    # Runtime config
    runtime_cfg = build_runtime_config(profile)

    # Branding task injection (same logic as create_bundle)
    branding_cfg = runtime_cfg.get("veridoc_branding", {})
    if (
        isinstance(branding_cfg, Mapping)
        and bool(branding_cfg.get("enabled", False))
        and bool(branding_cfg.get("apply_on_weekly", True))
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
            isinstance(item, Mapping)
            and str(item.get("id", "")).strip() == "veridoc-branding-policy"
            for item in weekly
        )
        if not has_branding_task:
            docs_root = str(
                branding_cfg.get(
                    "docs_root",
                    runtime_cfg.get("paths", {}).get("docs_root", "docs"),
                )
            )
            landing_url = str(
                branding_cfg.get("landing_url", "https://veri-doc.app/")
            ).strip()
            plan = str(
                branding_cfg.get("plan", "free")
            ).strip().lower()
            cheapest = str(
                branding_cfg.get("cheapest_paid_plan", "starter")
            ).strip().lower()
            report_path = str(
                branding_cfg.get(
                    "report_path",
                    "reports/veridoc_branding_policy_report.json",
                )
            ).strip()
            referral_env = str(
                branding_cfg.get("referral_code_env", "VERIDOC_REFERRAL_CODE")
            ).strip()
            badge_opt_out = bool(branding_cfg.get("badge_opt_out", False))
            opt_out_flag = " --badge-opt-out" if badge_opt_out else ""
            cmd = (
                f"python3 docsops/scripts/apply_veridoc_branding_policy.py "
                f"--repo-root . --docs-root {docs_root} "
                f"--landing-url {landing_url} "
                f"--plan {plan} --cheapest-paid-plan {cheapest} "
                f"--report {report_path}{opt_out_flag} "
                f'--referral-code "${{{referral_env}:-}}"'
            )
            weekly.append(
                {
                    "id": "veridoc-branding-policy",
                    "enabled": True,
                    "command": cmd,
                    "continue_on_error": False,
                }
            )

    # Scripts -- same as create_bundle but WITHOUT licensing scripts
    include_scripts = [str(rel) for rel in bundle_cfg.get("include_scripts", [])]
    required_scripts: list[str] = []
    # finalize_docs_gate is still required (not a licensing script)
    required_scripts.append("scripts/finalize_docs_gate.py")
    required_scripts.append("scripts/setup_client_env_wizard.py")
    if isinstance(branding_cfg, Mapping) and bool(
        branding_cfg.get("enabled", False)
    ):
        required_scripts.append("scripts/apply_veridoc_branding_policy.py")
    pr_autofix = runtime_cfg.get("pr_autofix", {})
    if isinstance(pr_autofix, Mapping) and bool(
        pr_autofix.get("enabled", False)
    ):
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
            cfg = (
                api_protocol_settings.get(key, {})
                if isinstance(api_protocol_settings, Mapping)
                else {}
            )
            if not isinstance(cfg, Mapping) or bool(cfg.get("enabled", True)):
                non_rest_enabled = True
                break
    if isinstance(api_first, Mapping):
        external_mock = api_first.get("external_mock", {})
        if bool(api_first.get("enabled", False)) and isinstance(
            external_mock, Mapping
        ):
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
            if str(
                api_first.get("sandbox_backend", "")
            ).strip().lower() == "external" and bool(
                external_mock.get("enabled", False)
            ):
                required_scripts.append(
                    "scripts/ensure_external_mock_server.py"
                )
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

    # Algolia widget generator
    integrations = runtime_cfg.get("integrations", {})
    if isinstance(integrations, Mapping):
        algolia_cfg = integrations.get("algolia", {})
        if isinstance(algolia_cfg, Mapping) and bool(
            algolia_cfg.get("enabled", False)
        ):
            required_scripts.append("scripts/generate_algolia_widget.py")

    # Filter out licensing scripts
    for req in required_scripts:
        if req not in include_scripts and req not in LICENSING_SCRIPTS:
            include_scripts.append(req)
    include_scripts = [
        s for s in include_scripts if s not in LICENSING_SCRIPTS
    ]

    for rel in include_scripts:
        copy_into_bundle(str(rel), bundle_root)
    for rel in bundle_cfg.get("include_docs", []):
        copy_into_bundle(str(rel), bundle_root)
    for rel in bundle_cfg.get("include_paths", []):
        copy_path_into_bundle(str(rel), bundle_root)

    write_yaml(bundle_root / "config" / "client_runtime.yml", runtime_cfg)

    build_llm_instruction_files(profile, bundle_root)
    build_automation_files(profile, bundle_root)
    build_personal_env_template(runtime_cfg, bundle_root)
    build_vale_config(profile, bundle_root)
    # No build_licensing_infrastructure -- personal bundle
    # No build_licensed_files -- personal bundle

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
            "local_env_template": ".env.docsops.local.template",
            "vale_config": ".vale.ini",
        },
        "personal_bundle": True,
    }
    write_yaml(bundle_root / "BUNDLE_INFO.yml", operator_note)

    return bundle_root


# -- Profile preview ----------------------------------------------------------

def _print_profile_preview(profile_path: Path) -> None:
    payload = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        print(f"[warn] profile is not a mapping: {profile_path}")
        return

    client = (
        payload.get("client", {})
        if isinstance(payload.get("client"), dict)
        else {}
    )
    runtime = (
        payload.get("runtime", {})
        if isinstance(payload.get("runtime"), dict)
        else {}
    )
    flow = (
        runtime.get("docs_flow", {})
        if isinstance(runtime.get("docs_flow"), dict)
        else {}
    )
    integrations = (
        runtime.get("integrations", {})
        if isinstance(runtime.get("integrations"), dict)
        else {}
    )
    algolia = (
        integrations.get("algolia", {})
        if isinstance(integrations.get("algolia"), dict)
        else {}
    )
    ask_ai = (
        integrations.get("ask_ai", {})
        if isinstance(integrations.get("ask_ai"), dict)
        else {}
    )

    print("\nProfile preview")
    print(f"  Profile file:   {profile_path}")
    print(f"  Client ID:      {client.get('id', '')}")
    print(f"  Company:        {client.get('company_name', '')}")
    print(f"  Docs flow:      {flow.get('mode', 'code-first')}")
    print(f"  Output targets: {runtime.get('output_targets', [])}")
    print(f"  Algolia:        {bool(algolia.get('enabled', False))}")
    print(f"  Ask AI:         {bool(ask_ai.get('enabled', False))}")
    print(f"  Licensing:      none (personal bundle)")


# -- CLI ----------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Personal documentation pipeline wizard (builds bundle without licensing)",
    )
    parser.add_argument(
        "--profile",
        help="Path to an existing *.client.yml profile (skip wizard)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompts",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("=" * 60)
    print("  VeriOps Personal Bundle Wizard")
    print("=" * 60)
    print()
    print("This wizard builds a self-contained VeriOps bundle for")
    print("personal use -- same as a client bundle but without")
    print("licensing, encryption, or capability packs.")
    print()

    # Step 1: Get or create profile
    if args.profile:
        profile_path = Path(args.profile)
        if not profile_path.is_absolute():
            profile_path = (REPO_ROOT / profile_path).resolve()
        if not profile_path.exists():
            print(f"[error] Profile not found: {profile_path}")
            return 1
        client_id = (
            yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
        ).get("client", {}).get("id", "personal")
    else:
        if not sys.stdin.isatty():
            print(
                "[error] Interactive mode requires a terminal. "
                "Use --profile for non-interactive."
            )
            return 1
        profile_path, client_id = _create_personal_profile()

    # Step 2: Preview
    _print_profile_preview(profile_path)

    # Step 3: Confirm
    if not args.yes:
        print()
        if not _prompt_yes_no("Build personal bundle?", default_yes=True):
            print("[stop] Bundle build cancelled")
            return 0

    # Step 4: Build bundle
    print("\n[build] Building personal bundle...")
    bundle_root = create_personal_bundle(profile_path)
    print(f"[ok] Bundle created: {bundle_root}")

    # Step 5: Print install instructions
    print()
    print("=" * 60)
    print("  Bundle Ready!")
    print("=" * 60)
    print()
    print(f"  Bundle path: {bundle_root}")
    print()
    print("Install into your repo using provision_client_repo.py:")
    print()
    print(f"  python3 scripts/provision_client_repo.py \\")
    print(f"    --client {profile_path.relative_to(REPO_ROOT)} \\")
    print(f"    --client-repo /path/to/your/repo \\")
    print(f"    --docsops-dir docsops")
    print()
    print("Or manually copy the bundle contents:")
    print()
    print(f"  cp -r {bundle_root}/* /path/to/your/repo/docsops/")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())

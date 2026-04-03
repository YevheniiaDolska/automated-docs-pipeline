#!/usr/bin/env python3
"""Build bundle and install it into a client repository in one command.

Example:
  python3 scripts/provision_client_repo.py \
    --client profiles/clients/blockstream-demo.client.yml \
    --client-repo /path/to/client-repo \
    --docsops-dir docsops \
    --install-scheduler linux
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml
logger = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_client_bundle import create_bundle  # noqa: E402
from scripts.docs_ci_bootstrap import install_docs_ci_files  # noqa: E402

PRESETS_DIR = REPO_ROOT / "profiles" / "clients" / "presets"
TEMPLATE_PROFILE = REPO_ROOT / "profiles" / "clients" / "_template.client.yml"
DOCSOPS_LOCAL_ENV = ".env.docsops.local"


def _prompt_with_default(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    raw = input(f"{prompt}{suffix}: ").strip()
    if raw:
        return raw
    if default is not None:
        return default
    raise ValueError(f"Value is required: {prompt}")


def _prompt_choice(prompt: str, options: list[str], default: str) -> str:
    options_str = "/".join(options)
    while True:
        value = _prompt_with_default(f"{prompt} ({options_str})", default).strip().lower()
        if value in options:
            return value
        print(f"Please choose one of: {options_str}")


def _prompt_yes_no(prompt: str, default_yes: bool = True) -> bool:
    suffix = "[Y/n]" if default_yes else "[y/N]"
    raw = input(f"{prompt} {suffix}: ").strip().lower()
    if not raw:
        return default_yes
    return raw in {"y", "yes"}


def _prompt_csv(prompt: str, default_values: list[str]) -> list[str]:
    default = ",".join(default_values)
    raw = _prompt_with_default(prompt, default)
    values = [x.strip() for x in raw.split(",") if x.strip()]
    return values


def _slugify_client_id(value: str) -> str:
    slug = re.sub(r"[^a-z0-9\-]+", "-", value.lower().strip())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(dict(merged[key]), value)
        else:
            merged[key] = value
    return merged


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return payload


def _build_profile_from_preset(preset_name: str) -> dict[str, Any]:
    template = _load_yaml_mapping(TEMPLATE_PROFILE)
    preset_path = PRESETS_DIR / f"{preset_name}.yml"
    if not preset_path.exists():
        raise FileNotFoundError(f"Preset not found: {preset_path}")
    preset = _load_yaml_mapping(preset_path)
    overrides = preset.get("overrides", {})
    if not isinstance(overrides, dict):
        raise ValueError(f"Preset overrides must be a mapping: {preset_path}")
    return _deep_merge(template, overrides)


def _save_generated_profile(profile: dict[str, Any], client_id: str) -> Path:
    out_dir = REPO_ROOT / "profiles" / "clients" / "generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{client_id}.client.yml"
    out_path.write_text(yaml.safe_dump(profile, sort_keys=False, allow_unicode=False), encoding="utf-8")
    return out_path


def _create_profile_via_wizard(default_scheduler: str, *, require_repo: bool = True) -> tuple[Path, str, str]:
    print("Preset-based profile creation")
    preset = _prompt_choice("Choose preset", ["small", "startup", "enterprise", "pilot-evidence"], "startup")
    profile = _build_profile_from_preset(preset)

    company_name = _prompt_with_default("Company name", str(profile["client"].get("company_name", "ACME Inc.")))
    suggested_id = _slugify_client_id(company_name) or "client"
    client_id = _slugify_client_id(_prompt_with_default("Client ID (slug)", suggested_id))
    if not client_id:
        raise ValueError("Client ID cannot be empty.")
    contact_email = _prompt_with_default(
        "Contact email",
        str(profile["client"].get("contact_email", "docs-owner@example.com")),
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
    tenant_id = _prompt_with_default(
        "Tenant ID (license binding)",
        str(profile["client"].get("tenant_id", client_id)),
    )
    company_domain = _prompt_with_default(
        "Company primary domain (license binding, optional)",
        str(profile["client"].get("company_domain", "")),
    )

    # Licensing
    license_plan = _prompt_choice(
        "License plan",
        ["pilot", "professional", "enterprise"],
        str(profile.get("licensing", {}).get("plan", "professional")),
    )
    license_days = int(_prompt_with_default(
        "License validity (days)",
        str(profile.get("licensing", {}).get("days", 365)),
    ))

    client_repo = ""
    if require_repo:
        client_repo = _prompt_with_default("Path to local client repository")

    docs_root = _prompt_with_default("Docs path in client repo", str(profile["runtime"].get("docs_root", "docs")))
    api_root = _prompt_with_default("API path in client repo", str(profile["runtime"].get("api_root", "api")))
    sdk_root = _prompt_with_default("SDK path in client repo", str(profile["runtime"].get("sdk_root", "sdk")))
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

    enable_pr_autofix = _prompt_yes_no("Enable optional PR auto-fix workflow?", default_yes=False)

    sandbox_backend_default = str(profile["runtime"]["api_first"].get("sandbox_backend", "external"))
    if flow_mode in {"api-first", "hybrid"}:
        sandbox_options = ["docker", "prism"] if strict_local else ["docker", "prism", "external"]
        sandbox_default = sandbox_backend_default if sandbox_backend_default in sandbox_options else "prism"
        sandbox_backend = _prompt_choice("API sandbox backend", sandbox_options, sandbox_default)
        profile["runtime"]["api_first"]["sandbox_backend"] = sandbox_backend
        if sandbox_backend == "external":
            mock_default = str(profile["runtime"]["api_first"].get("mock_base_url", "https://<your-real-public-mock-url>/v1"))
            profile["runtime"]["api_first"]["mock_base_url"] = _prompt_with_default("External mock base URL", mock_default)
        upload_assets_default = bool(profile["runtime"]["api_first"].get("upload_test_assets", False))
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
            default_yes=bool(profile["runtime"]["integrations"]["algolia"].get("enabled", False)),
        )
    algolia_site_generator = "mkdocs"
    if enable_algolia and not strict_local:
        algolia_site_generator = _prompt_choice(
            "Algolia: site generator for search widget",
            ["mkdocs", "docusaurus", "hugo", "vitepress", "custom"],
            str(profile["runtime"]["integrations"]["algolia"].get("site_generator", "mkdocs")),
        )
    enable_ask_ai = False
    if not strict_local:
        enable_ask_ai = _prompt_yes_no(
            "Enable Ask AI integration?",
            default_yes=bool(profile["runtime"]["integrations"]["ask_ai"].get("enabled", False)),
        )
    enable_veridoc_branding = _prompt_yes_no(
        "Enable Powered by VeriDoc badge policy automation?",
        default_yes=bool(profile["runtime"].get("veridoc_branding", {}).get("enabled", False)),
    )
    branding_landing_url = "https://veri-doc.app/"
    branding_plan = "free"
    branding_cheapest = "pro"
    branding_badge_opt_out = False
    if enable_veridoc_branding:
        branding_defaults = profile["runtime"].get("veridoc_branding", {})
        if not isinstance(branding_defaults, dict):
            branding_defaults = {}
        branding_landing_url = _prompt_with_default(
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

    enable_intent_weekly = _prompt_yes_no("Enable weekly intent experience build?", default_yes=True)
    finalize_gate_cfg = profile["runtime"].get("finalize_gate", {})
    enable_finalize_commit_confirmation = False
    if isinstance(finalize_gate_cfg, dict):
        enable_finalize_commit_confirmation = _prompt_yes_no(
            "Finalize gate: ask interactive confirmation before commit?",
            default_yes=bool(finalize_gate_cfg.get("ask_commit_confirmation", False)),
        )

    advanced_default = preset != "pilot-evidence"
    if _prompt_yes_no("Configure full advanced options now?", default_yes=advanced_default):
        modules = profile["runtime"].get("modules", {})
        if isinstance(modules, dict):
            print("Module toggles:")
            for key in sorted(modules.keys()):
                modules[key] = _prompt_yes_no(f"  Enable module '{key}'?", default_yes=bool(modules[key]))

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

        weekly_tasks = profile["runtime"].get("custom_tasks", {}).get("weekly", [])
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
                    default_yes=bool(api_first.get("sync_playground_endpoint", True)),
                )
                api_first["generate_test_assets"] = _prompt_yes_no(
                    "Generate API test assets from API contracts (REST/GraphQL/gRPC/AsyncAPI/WebSocket)?",
                    default_yes=bool(api_first.get("generate_test_assets", True)),
                )

            git_sync = profile["runtime"].get("git_sync", {})
            if isinstance(git_sync, dict):
                git_sync["enabled"] = _prompt_yes_no(
                    "Enable git sync (auto pull before weekly run)?",
                    default_yes=bool(git_sync.get("enabled", True)),
                )
            if git_sync["enabled"]:
                git_sync["repo_path"] = _prompt_with_default("Git sync repo path", str(git_sync.get("repo_path", ".")))
                git_sync["remote"] = _prompt_with_default("Git sync remote", str(git_sync.get("remote", "origin")))
                git_sync["branch"] = _prompt_with_default("Git sync branch (empty=detected)", str(git_sync.get("branch", "")))

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
                    ["openai", "anthropic", "azure-openai", "custom"],
                    str(ask_ai.get("provider", "openai")).strip().lower(),
                )
                ask_ai["billing_mode"] = _prompt_choice(
                    "Ask AI billing mode",
                    ["disabled", "user-subscription", "platform-paid"],
                    str(ask_ai.get("billing_mode", "disabled")).strip().lower(),
                )
                ask_ai["install_runtime_pack"] = _prompt_yes_no(
                    "Ask AI: install runtime pack during provisioning?",
                    default_yes=bool(ask_ai.get("install_runtime_pack", False)),
                )

    scheduler = "none"
    if require_repo:
        scheduler = _prompt_choice("Install scheduler mode", ["none", "linux", "windows"], default_scheduler)

    profile["client"]["id"] = client_id
    profile["client"]["company_name"] = company_name
    profile["client"]["contact_email"] = contact_email
    profile["client"]["tenant_id"] = tenant_id
    profile["client"]["company_domain"] = company_domain.strip().lower()
    profile["licensing"] = {
        "plan": license_plan,
        "days": license_days,
        "max_docs": 0,
    }
    profile["runtime"]["docs_root"] = docs_root
    profile["runtime"]["api_root"] = api_root
    profile["runtime"]["sdk_root"] = sdk_root
    profile["runtime"]["docs_flow"]["mode"] = flow_mode
    profile["bundle"]["style_guide"] = style_guide
    profile["runtime"]["output_targets"] = output_targets
    profile["runtime"]["pr_autofix"]["enabled"] = enable_pr_autofix
    profile["runtime"]["integrations"]["algolia"]["enabled"] = enable_algolia
    if enable_algolia:
        profile["runtime"]["integrations"]["algolia"]["site_generator"] = algolia_site_generator
        profile["runtime"]["integrations"]["algolia"]["generate_search_widget"] = True
    profile["runtime"]["integrations"]["ask_ai"]["enabled"] = enable_ask_ai
    llm_control = profile["runtime"].get("llm_control", {})
    if not isinstance(llm_control, dict):
        llm_control = {}
    llm_control["llm_mode"] = "local_default" if strict_local else "external_preferred"
    llm_control["local_model"] = "veridoc-writer"
    llm_control["local_base_model"] = "qwen3:30b"
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
                ask_ai_cfg["enabled"] = False
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
        finalize_gate_cfg["ask_commit_confirmation"] = enable_finalize_commit_confirmation
        if enable_finalize_commit_confirmation and "commit_on_approve" in finalize_gate_cfg:
            finalize_gate_cfg["commit_on_approve"] = True
    weekly_tasks = profile["runtime"].get("custom_tasks", {}).get("weekly", [])
    if isinstance(weekly_tasks, list):
        found = False
        for task in weekly_tasks:
            if isinstance(task, dict) and str(task.get("id", "")).strip() == "intent-experiences":
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
    return out_path, client_repo, scheduler


def _run_interactive_wizard(args: argparse.Namespace) -> argparse.Namespace:
    print("Interactive provisioning wizard")
    print("This will ask for required settings and can either build bundle only or install into local client repo.\n")
    print("What you need:")
    print("1) existing profile OR preset-driven profile creation")
    print("2) local path to client repository (only for install-local mode)")
    print("3) scheduler mode (none/linux/windows, only for install-local mode)\n")

    mode_default = "bundle-only"
    source_mode_hint: str | None = None
    while True:
        mode_raw = _prompt_with_default(
            "Delivery mode (bundle-only/install-local)",
            mode_default,
        ).strip().lower()
        if mode_raw in {"bundle-only", "install-local"}:
            mode = mode_raw
            break
        if mode_raw in {"existing", "preset"}:
            # Backward-compatible path for older interactive flows/tests that
            # answered profile source first.
            mode = "install-local"
            source_mode_hint = mode_raw
            break
        print("Please choose one of: bundle-only/install-local")

    args.bundle_only = mode == "bundle-only"

    default_scheduler = "windows" if os.name == "nt" else "linux"
    source_default = "preset" if getattr(args, "generate_profile", False) else "existing"
    source_mode = source_mode_hint or _prompt_choice(
        "Profile source",
        ["existing", "preset"],
        source_default,
    )
    if source_mode == "preset":
        generated_profile, client_repo, scheduler = _create_profile_via_wizard(
            default_scheduler,
            require_repo=not bool(args.bundle_only),
        )
        args.client = str(generated_profile)
        if not bool(args.bundle_only):
            args.client_repo = client_repo
            args.install_scheduler = scheduler
        else:
            args.client_repo = ""
            args.install_scheduler = "none"
    else:
        default_profile = "profiles/clients/blockstream-demo.client.yml"
        print("Examples of profile files:")
        print("- profiles/clients/blockstream-demo.client.yml")
        print("- profiles/clients/examples/basic.client.yml")
        print("- profiles/clients/examples/pro.client.yml")
        print("- profiles/clients/examples/enterprise.client.yml\n")
        args.client = _prompt_with_default("Path to client profile (*.client.yml)", args.client or default_profile)
        if not bool(args.bundle_only):
            args.client_repo = _prompt_with_default("Path to local client repository", args.client_repo)
            args.install_scheduler = _prompt_choice(
                "Install scheduler mode",
                ["none", "linux", "windows"],
                args.install_scheduler if args.install_scheduler in {"none", "linux", "windows"} else default_scheduler,
            )
        else:
            args.client_repo = ""
            args.install_scheduler = "none"

    args.docsops_dir = _prompt_with_default("Target folder name inside client repo", args.docsops_dir or "docsops")

    return args


def _resolve_args(args: argparse.Namespace) -> argparse.Namespace:
    bundle_only = bool(getattr(args, "bundle_only", False))
    missing_required = (not args.client) or ((not bundle_only) and (not args.client_repo))
    needs_prompt = args.interactive or missing_required
    if not needs_prompt:
        return args
    if not sys.stdin.isatty():
        raise ValueError(
            "Missing required arguments. Provide --client and (for install-local mode) --client-repo, "
            "or run in a terminal with --interactive."
        )
    return _run_interactive_wizard(args)


def copy_bundle_to_repo(bundle_root: Path, client_repo: Path, docsops_dir: str) -> Path:
    target = (client_repo / docsops_dir).resolve()
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(bundle_root, target)
    return target


def _read_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return payload


def _read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key:
            values[key] = value
    return values


def _write_dotenv(path: Path, values: dict[str, str]) -> None:
    lines = [
        "# VeriOps local secrets",
        "# Generated by scripts/provision_client_repo.py",
        "",
    ]
    for key in sorted(values.keys()):
        lines.append(f"{key}={values[key]}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _ensure_gitignore_has_env(client_repo: Path, env_name: str) -> None:
    gitignore = client_repo / ".gitignore"
    existing_lines: list[str] = []
    if gitignore.exists():
        existing_lines = gitignore.read_text(encoding="utf-8").splitlines()
    if any(line.strip() == env_name for line in existing_lines):
        return
    if existing_lines and existing_lines[-1].strip():
        existing_lines.append("")
    existing_lines.append("# VeriOps local secrets")
    existing_lines.append(env_name)
    existing_lines.append("")
    gitignore.write_text("\n".join(existing_lines), encoding="utf-8")


def _collect_secret_inputs(client_repo: Path, docsops_dir: str) -> Path | None:
    if not sys.stdin.isatty():
        return None

    runtime_path = client_repo / docsops_dir / "config" / "client_runtime.yml"
    if not runtime_path.exists():
        return None
    runtime = _read_yaml(runtime_path)
    api_first = runtime.get("api_first", {})
    if not isinstance(api_first, dict):
        api_first = {}
    pr_auto = runtime.get("pr_autofix", {})
    if not isinstance(pr_auto, dict):
        pr_auto = {}

    needed_vars: list[tuple[str, str, bool]] = []
    sandbox_backend = str(api_first.get("sandbox_backend", "")).strip().lower()
    external_mock = api_first.get("external_mock", {})
    if not isinstance(external_mock, dict):
        external_mock = {}
    if sandbox_backend == "external" and bool(external_mock.get("enabled", False)):
        provider = str(external_mock.get("provider", "postman")).strip().lower()
        if provider == "postman":
            postman = external_mock.get("postman", {})
            if not isinstance(postman, dict):
                postman = {}
            needed_vars.extend(
                [
                    (str(postman.get("api_key_env", "POSTMAN_API_KEY")), "Postman API Key (required)", True),
                    (
                        str(postman.get("workspace_id_env", "POSTMAN_WORKSPACE_ID")),
                        "Postman Workspace ID (required for auto-create)",
                        True,
                    ),
                    (
                        str(postman.get("collection_uid_env", "POSTMAN_COLLECTION_UID")),
                        "Postman Collection UID (optional, auto-import from OpenAPI if empty)",
                        False,
                    ),
                    (
                        str(postman.get("mock_server_id_env", "POSTMAN_MOCK_SERVER_ID")),
                        "Existing Postman Mock Server ID (optional, reuse mode)",
                        False,
                    ),
                ]
            )

    if bool(pr_auto.get("enabled", False)):
        needed_vars.append(
            ("DOCSOPS_BOT_TOKEN", "GitHub token with contents:write,pull_requests:write (optional)", False)
        )

    test_mgmt = api_first.get("test_management", {})
    if not isinstance(test_mgmt, dict):
        test_mgmt = {}
    if bool(api_first.get("upload_test_assets", False)):
        testrail = test_mgmt.get("testrail", {})
        if not isinstance(testrail, dict):
            testrail = {}
        zephyr = test_mgmt.get("zephyr_scale", {})
        if not isinstance(zephyr, dict):
            zephyr = {}

        needed_vars.extend(
            [
                (str(testrail.get("enabled_env", "TESTRAIL_UPLOAD_ENABLED")), "Set true to enable TestRail upload", False),
                (str(testrail.get("base_url_env", "TESTRAIL_BASE_URL")), "TestRail base URL (required if enabled)", False),
                (str(testrail.get("email_env", "TESTRAIL_EMAIL")), "TestRail account email (required if enabled)", False),
                (str(testrail.get("api_key_env", "TESTRAIL_API_KEY")), "TestRail API key (required if enabled)", False),
                (str(testrail.get("section_id_env", "TESTRAIL_SECTION_ID")), "TestRail section id (required if enabled)", False),
                (str(testrail.get("suite_id_env", "TESTRAIL_SUITE_ID")), "TestRail suite id (optional)", False),
                (str(zephyr.get("enabled_env", "ZEPHYR_UPLOAD_ENABLED")), "Set true to enable Zephyr upload", False),
                (str(zephyr.get("base_url_env", "ZEPHYR_SCALE_BASE_URL")), "Zephyr Scale base URL (optional; default cloud URL)", False),
                (str(zephyr.get("api_token_env", "ZEPHYR_SCALE_API_TOKEN")), "Zephyr Scale API token (required if enabled)", False),
                (str(zephyr.get("project_key_env", "ZEPHYR_SCALE_PROJECT_KEY")), "Zephyr project key (required if enabled)", False),
                (str(zephyr.get("folder_id_env", "ZEPHYR_SCALE_FOLDER_ID")), "Zephyr folder id (optional)", False),
            ]
        )

    if not needed_vars:
        return None

    print(f"\nSecrets setup (stored locally in client repo {DOCSOPS_LOCAL_ENV}, not committed)")
    print(f"- We will save values to {DOCSOPS_LOCAL_ENV} in client repo root.")
    print(f"- {DOCSOPS_LOCAL_ENV} will be added to .gitignore automatically.")
    print("- Press Enter to skip optional values.\n")
    print("How to get values:")
    print("- Postman API Key: Postman -> Settings -> API Keys.")
    print("- Postman Workspace ID: workspace URL or Postman API workspace endpoint.")
    print("- Collection UID: optional; can be skipped because pipeline imports from generated OpenAPI.")
    print("- TestRail: base URL + email + API key + section id from your TestRail project.")
    print("- Zephyr Scale: API token + project key from Zephyr Scale Cloud.")
    print("- DOCSOPS_BOT_TOKEN: optional GitHub PAT for restricted orgs.\n")

    if not _prompt_yes_no("Configure .env secrets now?", default_yes=True):
        return None

    dotenv_path = client_repo / DOCSOPS_LOCAL_ENV
    current = _read_dotenv(dotenv_path)
    updated = dict(current)

    for key, hint, required in needed_vars:
        if not key:
            continue
        masked_default = ""
        if key in current and current[key]:
            masked_default = "(already set)"
        prompt = f"{key} - {hint} {masked_default}".strip()
        value = input(f"{prompt}: ").strip()
        if not value:
            if required and key not in updated:
                print(f"[warn] {key} is required for full automation; leaving empty for now.")
            continue
        updated[key] = value

    _write_dotenv(dotenv_path, updated)
    _ensure_gitignore_has_env(client_repo, DOCSOPS_LOCAL_ENV)
    print(f"[ok] wrote local secrets: {dotenv_path}")
    print(f"[ok] ensured {DOCSOPS_LOCAL_ENV} ignored in git: {client_repo / '.gitignore'}")
    return dotenv_path


def install_pr_autofix_workflow(client_repo: Path, docsops_dir: str) -> Path | None:
    runtime_path = client_repo / docsops_dir / "config" / "client_runtime.yml"
    if not runtime_path.exists():
        return None
    runtime = _read_yaml(runtime_path)
    pr_cfg = runtime.get("pr_autofix", {})
    if not isinstance(pr_cfg, dict) or not bool(pr_cfg.get("enabled", False)):
        return None

    workflow_filename = str(pr_cfg.get("workflow_filename", "docsops-pr-autofix.yml")).strip() or "docsops-pr-autofix.yml"
    paths = runtime.get("paths", {})
    if not isinstance(paths, dict):
        paths = {}
    docs_root = str(paths.get("docs_root", "docs")).strip() or "docs"
    label_name = str(pr_cfg.get("label_name", "auto-doc-fix")).strip() or "auto-doc-fix"
    require_label = "true" if bool(pr_cfg.get("require_label", False)) else "false"
    enable_auto_merge = "true" if bool(pr_cfg.get("enable_auto_merge", False)) else "false"
    commit_message = str(pr_cfg.get("commit_message", "docs: auto-sync PR docs")).replace('"', '\\"')

    workflow_text = (
        "name: VeriOps PR Auto Fix\n\n"
        "on:\n"
        "  pull_request:\n"
        "    types: [opened, synchronize, reopened, labeled]\n\n"
        "permissions:\n"
        "  contents: write\n"
        "  pull-requests: write\n\n"
        "concurrency:\n"
        "  group: docsops-pr-${{ github.event.pull_request.number }}\n"
        "  cancel-in-progress: true\n\n"
        "jobs:\n"
        "  pr-doc-fix:\n"
        "    if: ${{ github.event.pull_request.head.repo.fork == false }}\n"
        "    runs-on: ubuntu-latest\n"
        "    env:\n"
        f"      DOCSOPS_DOCS_ROOT: \"{docs_root}\"\n"
        "      DOCSOPS_PUSH_TOKEN: ${{ secrets.DOCSOPS_BOT_TOKEN != '' && secrets.DOCSOPS_BOT_TOKEN || github.token }}\n"
        "    steps:\n"
        "      - name: Checkout PR branch\n"
        "        uses: actions/checkout@v4\n"
        "        with:\n"
        "          ref: ${{ github.event.pull_request.head.ref }}\n"
        "          token: ${{ env.DOCSOPS_PUSH_TOKEN }}\n"
        "          fetch-depth: 0\n\n"
        "      - name: Setup Python\n"
        "        uses: actions/setup-python@v5\n"
        "        with:\n"
        "          python-version: '3.11'\n\n"
        "      - name: Apply docs auto-fix\n"
        f"        env:\n          DOCSOPS_REQUIRE_LABEL: \"{require_label}\"\n          DOCSOPS_LABEL_NAME: \"{label_name}\"\n"
        "        run: |\n"
        "          set -e\n"
        "          if [[ \"$DOCSOPS_REQUIRE_LABEL\" == \"true\" ]]; then\n"
        "            LABELS=\"${{ join(github.event.pull_request.labels.*.name, ' ') }}\"\n"
        "            if [[ \" $LABELS \" != *\" $DOCSOPS_LABEL_NAME \"* ]]; then\n"
        "              echo \"[docsops] label '$DOCSOPS_LABEL_NAME' is required, skipping auto-fix\"\n"
        "              exit 0\n"
        "            fi\n"
        "          fi\n"
        f"          python3 {docsops_dir}/scripts/auto_fix_pr_docs.py \\\n"
        "            --base \"${{ github.event.pull_request.base.sha }}\" \\\n"
        "            --head \"${{ github.event.pull_request.head.sha }}\" \\\n"
        "            --pr-number \"${{ github.event.pull_request.number }}\" \\\n"
        "            --docs-root \"$DOCSOPS_DOCS_ROOT\"\n\n"
        "      - name: Commit docs fix into PR branch\n"
        "        run: |\n"
        "          set -e\n"
        "          if git diff --quiet; then\n"
        "            echo \"[docsops] no generated changes\"\n"
        "            exit 0\n"
        "          fi\n"
        "          git config user.name \"docsops-bot\"\n"
        "          git config user.email \"docsops-bot@users.noreply.github.com\"\n"
        "          git add \"$DOCSOPS_DOCS_ROOT/\"\n"
        f"          git commit -m \"{commit_message}\"\n"
        "          git push origin \"${{ github.event.pull_request.head.ref }}\"\n\n"
        "      - name: Enable auto-merge\n"
        f"        if: ${{ {enable_auto_merge} }}\n"
        "        env:\n"
        "          GH_TOKEN: ${{ env.DOCSOPS_PUSH_TOKEN }}\n"
        "        run: |\n"
        "          set -e\n"
        "          gh pr merge \"${{ github.event.pull_request.number }}\" --auto --squash\n"
    )

    workflow_dir = client_repo / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    output = workflow_dir / workflow_filename
    output.write_text(workflow_text, encoding="utf-8")
    return output


def install_docs_ci_workflow(client_repo: Path, docsops_dir: str) -> list[Path]:
    runtime_path = client_repo / docsops_dir / "config" / "client_runtime.yml"
    if not runtime_path.exists():
        return []
    runtime = _read_yaml(runtime_path)
    return install_docs_ci_files(client_repo, runtime, install_jenkins=True)


def _apply_algolia_widget(client_repo: Path, docsops_dir: str, runtime: dict[str, Any]) -> None:
    integrations = runtime.get("integrations", {})
    if not isinstance(integrations, dict):
        return
    algolia = integrations.get("algolia", {})
    if not isinstance(algolia, dict):
        return
    if not bool(algolia.get("enabled", False)):
        return
    if not bool(algolia.get("generate_search_widget", True)):
        return

    generator = str(algolia.get("site_generator", "mkdocs")).strip().lower()
    app_id_env = str(algolia.get("app_id_env", "ALGOLIA_APP_ID"))
    api_key_env = str(algolia.get("api_key_env", "ALGOLIA_API_KEY"))
    index_name_env = str(algolia.get("index_name_env", "ALGOLIA_INDEX_NAME"))
    index_name_default = str(algolia.get("index_name_default", "docs"))

    widget_script = client_repo / docsops_dir / "scripts" / "generate_algolia_widget.py"
    if not widget_script.exists():
        print("[algolia] generate_algolia_widget.py not found in bundle, skipping widget generation")
        return

    # Use placeholder values -- the actual keys come from env at runtime.
    # At provisioning time we write a helper script that reads env and generates widget files.
    helper_script = client_repo / docsops_dir / "scripts" / "setup_algolia_widget.sh"
    docs_root = str(runtime.get("paths", {}).get("docs_root", "docs"))

    helper_text = f"""#!/usr/bin/env bash
# Auto-generated by VeriOps provisioning.
# Generates Algolia search widget files for the client site.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${{BASH_SOURCE[0]}})/../../.." && pwd)"
cd "$REPO_ROOT"

APP_ID="${{${app_id_env}:-YOUR_ALGOLIA_APP_ID}}"
SEARCH_KEY="${{${api_key_env}:-YOUR_ALGOLIA_SEARCH_KEY}}"
INDEX_NAME="${{${index_name_env}:-{index_name_default}}}"

python3 "{docsops_dir}/scripts/generate_algolia_widget.py" \\
  --generator "{generator}" \\
  --app-id "$APP_ID" \\
  --search-key "$SEARCH_KEY" \\
  --index-name "$INDEX_NAME" \\
  --output-dir "."

echo "[algolia] Search widget generated for {generator}"
"""
    helper_script.write_text(helper_text, encoding="utf-8")
    try:
        helper_script.chmod(0o755)
    except OSError:
        logger.warning("Could not set executable bit on %s", helper_script)
    print(f"[algolia] widget setup script: {helper_script}")
    print(f"[algolia] site generator: {generator}")


def apply_integrations(client_repo: Path, docsops_dir: str) -> None:
    runtime_path = client_repo / docsops_dir / "config" / "client_runtime.yml"
    if not runtime_path.exists():
        return
    runtime = _read_yaml(runtime_path)
    integrations = runtime.get("integrations", {})
    if not isinstance(integrations, dict):
        return

    _apply_algolia_widget(client_repo, docsops_dir, runtime)

    ask_ai = integrations.get("ask_ai", {})
    if not isinstance(ask_ai, dict):
        return
    if not bool(ask_ai.get("auto_configure_on_provision", True)):
        return

    configure_script = client_repo / docsops_dir / "scripts" / "configure_ask_ai.py"
    if configure_script.exists():
        cmd = [
            sys.executable,
            str(configure_script),
            "--config",
            "config/ask-ai.yml",
            "--provider",
            str(ask_ai.get("provider", "openai")),
            "--billing-mode",
            str(ask_ai.get("billing_mode", "disabled")),
            "--model",
            str(ask_ai.get("model", "gpt-4.1-mini")),
            "--base-url",
            str(ask_ai.get("base_url", "https://api.openai.com/v1")),
        ]
        if bool(ask_ai.get("enabled", False)):
            cmd.append("--enable")
        else:
            cmd.append("--disable")
        subprocess.run(cmd, cwd=str(client_repo), check=True)

    if bool(ask_ai.get("install_runtime_pack", False)):
        runtime_pack_script = client_repo / docsops_dir / "scripts" / "install_ask_ai_runtime.py"
        if runtime_pack_script.exists():
            subprocess.run(
                [
                    sys.executable,
                    str(runtime_pack_script),
                    "--target-dir",
                    ".",
                    "--skip-if-missing",
                ],
                cwd=str(client_repo),
                check=True,
            )


def generate_env_checklist(client_repo: Path, docsops_dir: str) -> Path | None:
    runtime_path = client_repo / docsops_dir / "config" / "client_runtime.yml"
    if not runtime_path.exists():
        return None

    runtime = _read_yaml(runtime_path)
    integrations = runtime.get("integrations", {})
    if not isinstance(integrations, dict):
        integrations = {}

    algolia = integrations.get("algolia", {})
    if not isinstance(algolia, dict):
        algolia = {}
    ask_ai = integrations.get("ask_ai", {})
    if not isinstance(ask_ai, dict):
        ask_ai = {}
    api_first = runtime.get("api_first", {})
    if not isinstance(api_first, dict):
        api_first = {}

    lines: list[str] = [
        "# ENV_CHECKLIST",
        "",
        "Set these environment variables in local shell and CI secrets.",
        "Runner/agent prerequisites are installed on client infrastructure (not inside docsops bundle).",
        "",
        "## Core",
        "",
        "- [ ] `GITHUB_TOKEN` (normally auto-provided in GitHub Actions)",
        "",
    ]

    if bool(algolia.get("enabled", False)):
        site_gen = str(algolia.get("site_generator", "mkdocs"))
        lines.extend(
            [
                "## Algolia",
                "",
                f"- [ ] `{algolia.get('app_id_env', 'ALGOLIA_APP_ID')}`",
                f"- [ ] `{algolia.get('api_key_env', 'ALGOLIA_API_KEY')}`",
                f"- [ ] `{algolia.get('index_name_env', 'ALGOLIA_INDEX_NAME')}`",
                "",
                f"Site generator: `{site_gen}`",
                "",
                "After setting env vars, generate search widget files:",
                "```bash",
                "bash docsops/scripts/setup_algolia_widget.sh",
                "```",
                "",
            ]
        )

    if bool(ask_ai.get("enabled", False)):
        provider = str(ask_ai.get("provider", "openai")).strip().lower()
        billing_mode = str(ask_ai.get("billing_mode", "disabled")).strip().lower()
        provider_vars = {
            "openai": ["OPENAI_API_KEY"],
            "anthropic": ["ANTHROPIC_API_KEY"],
            "azure-openai": ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"],
            "custom": ["ASK_AI_API_KEY", "ASK_AI_BASE_URL"],
        }.get(provider, ["ASK_AI_API_KEY"])
        lines.extend(["## Ask AI", "", f"- Provider: `{provider}`", f"- Billing mode: `{billing_mode}`"])
        lines.extend([f"- [ ] `{name}`" for name in provider_vars])
        if provider == "openai" and billing_mode == "user-subscription":
            lines.extend(
                [
                    "- [ ] `DOCSOPS_SHARED_OPENAI_API_KEY` (optional centralized key for plan-entitled users)",
                    "- Set one of: `OPENAI_API_KEY` or `DOCSOPS_SHARED_OPENAI_API_KEY`.",
                ]
            )
        lines.append("")

    sandbox_backend = str(api_first.get("sandbox_backend", "")).strip().lower()
    external_mock = api_first.get("external_mock", {})
    if not isinstance(external_mock, dict):
        external_mock = {}
    if sandbox_backend == "external" and bool(external_mock.get("enabled", False)):
        provider = str(external_mock.get("provider", "postman")).strip().lower()
        lines.extend(
                [
                    "## API external sandbox",
                "",
                "- This is a one-time setup. After that, weekly/API-first flow updates mock automatically.",
                f"- Provider: `{provider}`",
                "",
            ]
        )
        if provider == "postman":
            postman = external_mock.get("postman", {})
            if not isinstance(postman, dict):
                postman = {}
            api_key_env = str(postman.get("api_key_env", "POSTMAN_API_KEY"))
            workspace_env = str(postman.get("workspace_id_env", "POSTMAN_WORKSPACE_ID"))
            collection_env = str(postman.get("collection_uid_env", "POSTMAN_COLLECTION_UID"))
            mock_id_env = str(postman.get("mock_server_id_env", "POSTMAN_MOCK_SERVER_ID"))
            lines.extend(
                [
                    "Give these inputs to the pipeline:",
                    f"- [ ] `{api_key_env}`: Postman API key (required)",
                    f"- [ ] `{workspace_env}`: Postman workspace id (required for auto-create mode)",
                    f"- [ ] `{collection_env}`: Postman collection uid (optional; if missing, pipeline imports collection from generated OpenAPI)",
                    f"- [ ] `{mock_id_env}`: existing Postman mock id (optional, to reuse existing mock)",
                    "",
                    "How it works:",
                    "- If mock id is provided, pipeline reuses that mock and resolves URL automatically.",
                    "- If mock id is empty, pipeline creates/updates collection from generated OpenAPI, then creates mock.",
                    "- Resolved URL is written into docs playground endpoint via `sync_playground_endpoint`.",
                    "",
                ]
            )

    test_mgmt = api_first.get("test_management", {})
    if not isinstance(test_mgmt, dict):
        test_mgmt = {}
    if bool(api_first.get("upload_test_assets", False)):
        testrail_cfg = test_mgmt.get("testrail", {})
        if not isinstance(testrail_cfg, dict):
            testrail_cfg = {}
        zephyr_cfg = test_mgmt.get("zephyr_scale", {})
        if not isinstance(zephyr_cfg, dict):
            zephyr_cfg = {}
        lines.extend(
            [
                "## API test management upload (TestRail/Zephyr)",
                "",
                "- Pipeline auto-generates test assets from OpenAPI and can auto-upload them.",
                "- Upload runs during API-first flow when `upload_test_assets=true`.",
                "",
                "TestRail env vars:",
                f"- [ ] `{testrail_cfg.get('enabled_env', 'TESTRAIL_UPLOAD_ENABLED')}` (`true` to enable upload)",
                f"- [ ] `{testrail_cfg.get('base_url_env', 'TESTRAIL_BASE_URL')}`",
                f"- [ ] `{testrail_cfg.get('email_env', 'TESTRAIL_EMAIL')}`",
                f"- [ ] `{testrail_cfg.get('api_key_env', 'TESTRAIL_API_KEY')}`",
                f"- [ ] `{testrail_cfg.get('section_id_env', 'TESTRAIL_SECTION_ID')}`",
                f"- [ ] `{testrail_cfg.get('suite_id_env', 'TESTRAIL_SUITE_ID')}` (optional)",
                "",
                "Zephyr Scale env vars:",
                f"- [ ] `{zephyr_cfg.get('enabled_env', 'ZEPHYR_UPLOAD_ENABLED')}` (`true` to enable upload)",
                f"- [ ] `{zephyr_cfg.get('base_url_env', 'ZEPHYR_SCALE_BASE_URL')}` (optional; default cloud URL)",
                f"- [ ] `{zephyr_cfg.get('api_token_env', 'ZEPHYR_SCALE_API_TOKEN')}`",
                f"- [ ] `{zephyr_cfg.get('project_key_env', 'ZEPHYR_SCALE_PROJECT_KEY')}`",
                f"- [ ] `{zephyr_cfg.get('folder_id_env', 'ZEPHYR_SCALE_FOLDER_ID')}` (optional)",
                "",
            ]
        )

    pr_auto = runtime.get("pr_autofix", {})
    if not isinstance(pr_auto, dict):
        pr_auto = {}
    if bool(pr_auto.get("enabled", False)):
        lines.extend(
            [
                "## PR auto-doc workflow (GitHub)",
                "",
                "- This is a one-time repository setup.",
                "- During provisioning, docsops installs `.github/workflows/docsops-pr-autofix.yml`.",
                "- Workflow always commits to the same PR branch that triggered it (never to main).",
                "",
                "Required repository settings:",
                "- [ ] Actions workflow permissions: `Read and write permissions`",
                "- [ ] Pull requests: allow auto-merge (optional, if `enable_auto_merge=true`)",
                "",
                "Optional secret (only if default GITHUB_TOKEN cannot push in your org):",
                "- [ ] `DOCSOPS_BOT_TOKEN` with scopes: `contents:write`, `pull_requests:write`",
                "",
            ]
        )

    lines.extend(
        [
            "## Self-hosted runner/agent prerequisites",
            "",
            "Install these on the machine that executes CI jobs (GitHub self-hosted, GitLab runner, Forgejo/Gitea runner, or Jenkins agent):",
            "",
            "- [ ] `git`",
            "- [ ] `python3` and `pip`",
            "- [ ] `node` and `npm`",
            "- [ ] network access to the repository host and dependency registries (npm/pypi)",
            "",
            "Optional generator-specific build tools:",
            "",
            "- `mkdocs`: `mkdocs` Python package",
            "- `sphinx`: `sphinx-build` Python package",
            "- `hugo`: `hugo` binary",
            "- `jekyll`: `ruby` + `bundle`",
            "",
            "Quick Ubuntu bootstrap example:",
            "",
            "```bash",
            "sudo apt-get update",
            "sudo apt-get install -y git python3 python3-pip nodejs npm",
            "python3 -m pip install --upgrade pip",
            "python3 -m pip install mkdocs sphinx",
            "```",
            "",
            "Jenkins:",
            "",
            "- [ ] Use `Jenkinsfile.docsops` generated by provisioning/wizard.",
            "- [ ] Ensure Jenkins agent has the same prerequisites as above.",
            "",
            "## Verification",
            "",
            "- [ ] Docs CI is present in your git platform (GitHub/GitLab/Forgejo) and runs `npm run lint` on PR/MR.",
            "- [ ] Autopipeline pushes docs updates to a dedicated `docs/review/*` branch (no auto-merge).",
            "- [ ] Run one weekly cycle and check `reports/consolidated_report.json` timestamp.",
            "- [ ] Ensure there are no missing-secret errors in `reports/docsops-weekly.log`.",
            "",
        ]
    )

    output = client_repo / docsops_dir / "ENV_CHECKLIST.md"
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def execute_provision(args: argparse.Namespace) -> int:
    profile_path = Path(args.client)
    if not profile_path.is_absolute():
        profile_path = (REPO_ROOT / profile_path).resolve()
    if not profile_path.exists():
        raise FileNotFoundError(f"Client profile not found: {profile_path}")
    bundle_root = create_bundle(profile_path)
    if bool(getattr(args, "bundle_only", False)):
        print(f"[ok] bundle built: {bundle_root}")
        print("[next] deliver this folder to client and place as <client-repo>/docsops")
        print("[next] client runs: python3 docsops/scripts/setup_client_env_wizard.py")
        return 0

    client_repo = Path(args.client_repo).resolve()
    if not client_repo.exists():
        raise FileNotFoundError(f"Client repo not found: {client_repo}")
    installed_path = copy_bundle_to_repo(bundle_root, client_repo, args.docsops_dir)
    workflow_path = install_pr_autofix_workflow(client_repo, args.docsops_dir)
    ci_workflows = install_docs_ci_workflow(client_repo, args.docsops_dir)
    apply_integrations(client_repo, args.docsops_dir)
    checklist = generate_env_checklist(client_repo, args.docsops_dir)
    dotenv_path = _collect_secret_inputs(client_repo, args.docsops_dir)
    run_scheduler_install(client_repo, args.docsops_dir, args.install_scheduler)

    print(f"[ok] bundle built: {bundle_root}")
    print(f"[ok] bundle installed: {installed_path}")
    if workflow_path:
        print(f"[ok] pr auto-doc workflow installed: {workflow_path}")
    for path in ci_workflows:
        print(f"[ok] docs CI workflow installed: {path}")
    if checklist:
        print(f"[ok] env checklist: {checklist}")
    if dotenv_path:
        print(f"[ok] local .env updated: {dotenv_path}")
    if args.install_scheduler != "none":
        print(f"[ok] scheduler installed: {args.install_scheduler}")
    else:
        print("[next] install scheduler manually from docsops/ops/runbook.md")
    return 0


def run_scheduler_install(client_repo: Path, docsops_dir: str, mode: str) -> None:
    if mode == "none":
        return
    if mode == "linux":
        script = client_repo / docsops_dir / "ops" / "install_cron_weekly.sh"
        subprocess.run(["bash", str(script)], cwd=str(client_repo), check=True)
        return
    if mode == "windows":
        script = client_repo / docsops_dir / "ops" / "install_windows_task.ps1"
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
            ],
            cwd=str(client_repo),
            check=True,
        )
        return
    raise ValueError(f"Unsupported install-scheduler mode: {mode}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Provision docsops into a client repo")
    parser.add_argument("--client", help="Path to client profile (*.client.yml)")
    parser.add_argument("--client-repo", help="Path to client repository root")
    parser.add_argument("--docsops-dir", default="docsops", help="Target dir inside client repo")
    parser.add_argument(
        "--install-scheduler",
        default="none",
        choices=["none", "linux", "windows"],
        help="Optionally install weekly scheduler during provisioning",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run interactive wizard (prompts for missing values)",
    )
    parser.add_argument(
        "--generate-profile",
        action="store_true",
        help="Interactive mode: create profile from preset (small/startup/enterprise)",
    )
    parser.add_argument(
        "--bundle-only",
        action="store_true",
        help="Build client bundle only (no install into local client repository).",
    )
    return parser.parse_args()


def main() -> int:
    args = _resolve_args(parse_args())
    return execute_provision(args)


if __name__ == "__main__":
    raise SystemExit(main())

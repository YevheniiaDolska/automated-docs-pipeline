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
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_client_bundle import create_bundle  # noqa: E402

PRESETS_DIR = REPO_ROOT / "profiles" / "clients" / "presets"
TEMPLATE_PROFILE = REPO_ROOT / "profiles" / "clients" / "_template.client.yml"


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


def _create_profile_via_wizard(default_scheduler: str) -> tuple[Path, str, str]:
    print("Preset-based profile creation")
    preset = _prompt_choice("Choose preset", ["small", "startup", "enterprise"], "startup")
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
    client_repo = _prompt_with_default("Path to local client repository")

    docs_root = _prompt_with_default("Docs path in client repo", str(profile["runtime"].get("docs_root", "docs")))
    api_root = _prompt_with_default("API path in client repo", str(profile["runtime"].get("api_root", "api")))
    sdk_root = _prompt_with_default("SDK path in client repo", str(profile["runtime"].get("sdk_root", "sdk")))
    flow_mode = _prompt_choice(
        "Docs flow mode",
        ["code-first", "api-first", "hybrid"],
        str(profile["runtime"]["docs_flow"].get("mode", "code-first")),
    )
    scheduler = _prompt_choice("Install scheduler mode", ["none", "linux", "windows"], default_scheduler)

    profile["client"]["id"] = client_id
    profile["client"]["company_name"] = company_name
    profile["client"]["contact_email"] = contact_email
    profile["runtime"]["docs_root"] = docs_root
    profile["runtime"]["api_root"] = api_root
    profile["runtime"]["sdk_root"] = sdk_root
    profile["runtime"]["docs_flow"]["mode"] = flow_mode
    if flow_mode == "api-first":
        profile["runtime"]["api_first"]["enabled"] = True
    elif flow_mode == "code-first":
        profile["runtime"]["api_first"]["enabled"] = False

    out_path = _save_generated_profile(profile, client_id)
    print(f"[ok] generated profile: {out_path}")
    return out_path, client_repo, scheduler


def _run_interactive_wizard(args: argparse.Namespace) -> argparse.Namespace:
    print("Interactive provisioning wizard")
    print("This will ask for required settings and then install docsops into the client repo.\n")
    print("What you need:")
    print("1) existing profile OR preset-driven profile creation")
    print("2) local path to client repository")
    print("3) scheduler mode (none/linux/windows)\n")

    default_scheduler = "windows" if os.name == "nt" else "linux"
    mode_default = "preset" if getattr(args, "generate_profile", False) else "existing"
    source_mode = _prompt_choice("Profile source", ["existing", "preset"], mode_default)
    if source_mode == "preset":
        generated_profile, client_repo, scheduler = _create_profile_via_wizard(default_scheduler)
        args.client = str(generated_profile)
        args.client_repo = client_repo
        args.install_scheduler = scheduler
    else:
        default_profile = "profiles/clients/blockstream-demo.client.yml"
        print("Examples of profile files:")
        print("- profiles/clients/blockstream-demo.client.yml")
        print("- profiles/clients/examples/basic.client.yml")
        print("- profiles/clients/examples/pro.client.yml")
        print("- profiles/clients/examples/enterprise.client.yml\n")
        args.client = _prompt_with_default("Path to client profile (*.client.yml)", args.client or default_profile)
        args.client_repo = _prompt_with_default("Path to local client repository", args.client_repo)
        args.install_scheduler = _prompt_choice(
            "Install scheduler mode",
            ["none", "linux", "windows"],
            args.install_scheduler if args.install_scheduler in {"none", "linux", "windows"} else default_scheduler,
        )

    args.docsops_dir = _prompt_with_default("Target folder name inside client repo", args.docsops_dir or "docsops")

    return args


def _resolve_args(args: argparse.Namespace) -> argparse.Namespace:
    needs_prompt = args.interactive or not args.client or not args.client_repo
    if not needs_prompt:
        return args
    if not sys.stdin.isatty():
        raise ValueError(
            "Missing required arguments (--client, --client-repo) and interactive input is unavailable. "
            "Provide both arguments explicitly or run in a terminal with --interactive."
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


def apply_integrations(client_repo: Path, docsops_dir: str) -> None:
    runtime_path = client_repo / docsops_dir / "config" / "client_runtime.yml"
    if not runtime_path.exists():
        return
    runtime = _read_yaml(runtime_path)
    integrations = runtime.get("integrations", {})
    if not isinstance(integrations, dict):
        return

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

    lines: list[str] = [
        "# ENV_CHECKLIST",
        "",
        "Set these environment variables in local shell and CI secrets.",
        "",
        "## Core",
        "",
        "- [ ] `GITHUB_TOKEN` (normally auto-provided in GitHub Actions)",
        "",
    ]

    if bool(algolia.get("enabled", False)):
        lines.extend(
            [
                "## Algolia",
                "",
                f"- [ ] `{algolia.get('app_id_env', 'ALGOLIA_APP_ID')}`",
                f"- [ ] `{algolia.get('api_key_env', 'ALGOLIA_API_KEY')}`",
                f"- [ ] `{algolia.get('index_name_env', 'ALGOLIA_INDEX_NAME')}`",
                "",
            ]
        )

    if bool(ask_ai.get("enabled", False)):
        provider = str(ask_ai.get("provider", "openai")).strip().lower()
        provider_vars = {
            "openai": ["OPENAI_API_KEY"],
            "anthropic": ["ANTHROPIC_API_KEY"],
            "azure-openai": ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"],
            "custom": ["ASK_AI_API_KEY", "ASK_AI_BASE_URL"],
        }.get(provider, ["ASK_AI_API_KEY"])
        lines.extend(["## Ask AI", "", f"- Provider: `{provider}`"])
        lines.extend([f"- [ ] `{name}`" for name in provider_vars])
        lines.append("")

    lines.extend(
        [
            "## Verification",
            "",
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
    client_repo = Path(args.client_repo).resolve()
    if not client_repo.exists():
        raise FileNotFoundError(f"Client repo not found: {client_repo}")

    bundle_root = create_bundle(profile_path)
    installed_path = copy_bundle_to_repo(bundle_root, client_repo, args.docsops_dir)
    apply_integrations(client_repo, args.docsops_dir)
    checklist = generate_env_checklist(client_repo, args.docsops_dir)
    run_scheduler_install(client_repo, args.docsops_dir, args.install_scheduler)

    print(f"[ok] bundle built: {bundle_root}")
    print(f"[ok] bundle installed: {installed_path}")
    if checklist:
        print(f"[ok] env checklist: {checklist}")
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
    return parser.parse_args()


def main() -> int:
    args = _resolve_args(parse_args())
    return execute_provision(args)


if __name__ == "__main__":
    raise SystemExit(main())

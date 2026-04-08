#!/usr/bin/env python3
"""One-command interactive onboarding for a new client repository.

Flow:
1. Generate/select client profile via preset wizard.
2. Show profile summary and path.
3. Confirm.
4. Build bundle + install to client repo + apply integrations + install scheduler.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import provision_client_repo as provision


def _prompt_yes_no(prompt: str, default_yes: bool = True) -> bool:
    suffix = "[Y/n]" if default_yes else "[y/N]"
    raw = input(f"{prompt} {suffix}: ").strip().lower()
    if not raw:
        return default_yes
    return raw in {"y", "yes"}


def _print_profile_preview(profile_path: Path) -> None:
    payload = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        print(f"[warn] profile is not a mapping: {profile_path}")
        return

    client = payload.get("client", {}) if isinstance(payload.get("client"), dict) else {}
    runtime = payload.get("runtime", {}) if isinstance(payload.get("runtime"), dict) else {}
    licensing = payload.get("licensing", {}) if isinstance(payload.get("licensing"), dict) else {}
    flow = runtime.get("docs_flow", {}) if isinstance(runtime.get("docs_flow"), dict) else {}
    integrations = runtime.get("integrations", {}) if isinstance(runtime.get("integrations"), dict) else {}
    algolia = integrations.get("algolia", {}) if isinstance(integrations.get("algolia"), dict) else {}
    ask_ai = integrations.get("ask_ai", {}) if isinstance(integrations.get("ask_ai"), dict) else {}
    llm_control = runtime.get("llm_control", {}) if isinstance(runtime.get("llm_control"), dict) else {}
    branding = runtime.get("veridoc_branding", {}) if isinstance(runtime.get("veridoc_branding"), dict) else {}

    print("\nProfile preview")
    print(f"- Profile file: {profile_path}")
    print(f"- Client ID: {client.get('id', '')}")
    print(f"- Company: {client.get('company_name', '')}")
    print(f"- Docs flow: {flow.get('mode', 'code-first')}")
    print(f"- Output targets: {runtime.get('output_targets', [])}")
    commercial_package = str(licensing.get("commercial_package", "")).strip().lower()
    if not commercial_package:
        plan_to_package = {
            "pilot": "pilot",
            "professional": "full",
            "enterprise": "full+rag",
        }
        commercial_package = plan_to_package.get(str(licensing.get("plan", "professional")).strip().lower(), "full")
    print(f"- Commercial package: {commercial_package}")
    print(f"- RAG add-on: {commercial_package == 'full+rag'}")
    print(f"- License plan (JWT): {licensing.get('plan', 'professional')}")
    print(f"- Signed JWT required: {bool(licensing.get('require_signed_jwt', True))}")
    print(f"- Algolia enabled: {bool(algolia.get('enabled', False))}")
    print(f"- Ask AI enabled: {bool(ask_ai.get('enabled', False))}")
    print(f"- Badge policy enabled: {bool(branding.get('enabled', False))}")
    if bool(branding.get("enabled", False)):
        print(f"- Badge policy locked: {bool(branding.get('lock_badge_policy', True))}")
    llm_mode = str(llm_control.get("llm_mode", "external_preferred")).strip().lower()
    strict_local = bool(llm_control.get("strict_local_first", llm_mode == "local_default"))
    print(f"- LLM mode: {llm_mode}")
    print(f"- Strict local-first: {strict_local}")
    print(f"- Local model: {llm_control.get('local_model', 'veridoc-writer')}")
    if llm_control.get("local_base_model"):
        print(f"- Local base model: {llm_control.get('local_base_model')}")
    print("- IP protection: metadata-only egress + server-side revoke/pack controls.")
    if strict_local or llm_mode == "local_default":
        print("- Local bootstrap: setup_client_env_wizard installs Ollama, pulls base model, and creates veridoc-writer.")
        print("- Strict local guardrails: external Ask AI, Algolia upload, external mock backend, and test uploads are disabled.")
    else:
        print("- Cloud/hybrid profile: external providers are allowed (same trust model as hosted Git/cloud workflows).")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interactive one-command client onboarding")
    parser.add_argument("--client", help="Optional existing client profile path")
    parser.add_argument("--client-repo", help="Optional client repository path")
    parser.add_argument("--docsops-dir", default="docsops", help="Target docsops directory in client repo")
    parser.add_argument(
        "--install-scheduler",
        default="none",
        choices=["none", "linux", "windows"],
        help="Scheduler mode (none/linux/windows)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt before install",
    )
    parser.add_argument(
        "--mode",
        choices=["bundle-only", "install-local"],
        default="bundle-only",
        help="bundle-only: build client bundle for handoff; install-local: build and install into local client repo",
    )
    return parser.parse_args()


def main() -> int:
    provision.load_local_env(
        provision.REPO_ROOT,
        filenames=(".env", ".env.local", ".env.operator", ".env.docsops.local"),
        override=False,
    )
    base_args = parse_args()
    mode = getattr(base_args, "mode", "install-local")
    bundle_only = mode == "bundle-only"
    interactive_args = argparse.Namespace(
        client=base_args.client,
        client_repo=base_args.client_repo,
        docsops_dir=base_args.docsops_dir,
        install_scheduler=base_args.install_scheduler,
        interactive=True,
        generate_profile=True,
        bundle_only=bundle_only,
    )

    resolved = provision._resolve_args(interactive_args)
    profile_path = Path(resolved.client)
    if not profile_path.is_absolute():
        profile_path = (provision.REPO_ROOT / profile_path).resolve()

    _print_profile_preview(profile_path)
    if not base_args.yes:
        action_msg = (
            "Continue with bundle build only?"
            if bundle_only
            else "Continue with bundle build + install + scheduler?"
        )
        if not _prompt_yes_no(action_msg, default_yes=True):
            print("[stop] onboarding cancelled by user")
            return 0

    return provision.execute_provision(resolved)


if __name__ == "__main__":
    sys.exit(main())

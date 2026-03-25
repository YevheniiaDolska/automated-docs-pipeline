from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))


def _base_profile() -> dict[str, Any]:
    return {
        "client": {"id": "seed", "company_name": "ACME", "contact_email": "docs@example.com"},
        "licensing": {"plan": "professional", "days": 365},
        "bundle": {"style_guide": "google", "include_paths": ["docs"], "include_scripts": ["scripts/a.py"]},
        "runtime": {
            "docs_root": "docs",
            "api_root": "api",
            "sdk_root": "sdk",
            "docs_flow": {"mode": "code-first"},
            "output_targets": ["mkdocs"],
            "modules": {"gap_detection": True, "drift_detection": False},
            "custom_tasks": {"weekly": [{"id": "intent-experiences", "enabled": False, "command": "cmd", "continue_on_error": True}]},
            "finalize_gate": {"ask_commit_confirmation": False, "commit_on_approve": False},
            "git_sync": {"enabled": True, "repo_path": ".", "remote": "origin", "branch": "main"},
            "pr_autofix": {"enabled": False},
            "api_first": {
                "enabled": False,
                "sandbox_backend": "external",
                "mock_base_url": "https://example.test/v1",
                "upload_test_assets": False,
                "verify_user_path": False,
                "sync_playground_endpoint": True,
                "generate_test_assets": True,
            },
            "integrations": {
                "algolia": {"enabled": False, "site_generator": "mkdocs", "upload_on_weekly": False},
                "ask_ai": {
                    "enabled": False,
                    "provider": "openai",
                    "billing_mode": "disabled",
                    "install_runtime_pack": False,
                },
            },
        },
    }


def test_create_profile_via_wizard_full_branching(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import provision_client_repo as mod

    profile = _base_profile()

    monkeypatch.setattr(mod, "_build_profile_from_preset", lambda preset: profile)
    monkeypatch.setattr(mod, "_save_generated_profile", lambda prof, client_id: tmp_path / f"{client_id}.client.yml")

    def _prompt_choice(prompt: str, options: list[str], default: str) -> str:
        if "Choose preset" in prompt:
            return "startup"
        if "License plan" in prompt:
            return "professional"
        if "Docs flow mode" in prompt:
            return "hybrid"
        if "Vale style guide" in prompt:
            return "google"
        if "API sandbox backend" in prompt:
            return "external"
        if "Algolia: site generator" in prompt:
            return "mkdocs"
        if "Ask AI provider" in prompt:
            return "openai"
        if "Ask AI billing mode" in prompt:
            return "user-subscription"
        if "Install scheduler mode" in prompt:
            return "linux"
        return default if default in options else options[0]

    def _prompt_with_default(prompt: str, default: str | None = None) -> str:
        if "Path to local client repository" in prompt:
            return str(tmp_path / "client")
        if "Company name" in prompt:
            return "Acme Cloud"
        if "Contact email" in prompt:
            return "owner@acme.dev"
        if "License validity" in prompt:
            return "365"
        if "External mock base URL" in prompt:
            return "https://mock.acme.dev/v1"
        return default or "value"

    def _prompt_csv(prompt: str, default_values: list[str]) -> list[str]:
        if "Extra include_scripts" in prompt:
            return ["scripts/extra.py"]
        if "Extra weekly task commands" in prompt:
            return ["python3 docsops/scripts/custom_task.py"]
        return default_values

    monkeypatch.setattr(mod, "_prompt_choice", _prompt_choice)
    monkeypatch.setattr(mod, "_prompt_with_default", _prompt_with_default)
    monkeypatch.setattr(mod, "_prompt_csv", _prompt_csv)
    monkeypatch.setattr(mod, "_prompt_yes_no", lambda prompt, default_yes=True: True)

    out_path, client_repo, scheduler = mod._create_profile_via_wizard(default_scheduler="none")
    assert out_path.name == "acme-cloud.client.yml"
    assert client_repo.endswith("client")
    assert scheduler == "linux"
    assert profile["runtime"]["docs_flow"]["mode"] == "hybrid"
    assert profile["runtime"]["api_first"]["sandbox_backend"] == "external"
    assert profile["runtime"]["integrations"]["algolia"]["enabled"] is True
    assert profile["runtime"]["integrations"]["ask_ai"]["enabled"] is True


def test_collect_secret_inputs_writes_dotenv_and_gitignore(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import provision_client_repo as mod

    repo = tmp_path / "client-repo"
    runtime_dir = repo / "docsops" / "config"
    runtime_dir.mkdir(parents=True)

    runtime = {
        "api_first": {
            "sandbox_backend": "external",
            "external_mock": {
                "enabled": True,
                "provider": "postman",
                "postman": {
                    "api_key_env": "POSTMAN_API_KEY",
                    "workspace_id_env": "POSTMAN_WORKSPACE_ID",
                },
            },
            "upload_test_assets": True,
            "test_management": {
                "testrail": {"enabled_env": "TESTRAIL_UPLOAD_ENABLED"},
                "zephyr_scale": {"enabled_env": "ZEPHYR_UPLOAD_ENABLED"},
            },
        },
        "pr_autofix": {"enabled": True},
    }
    (runtime_dir / "client_runtime.yml").write_text(yaml.safe_dump(runtime, sort_keys=False), encoding="utf-8")

    monkeypatch.setattr(mod.sys, "stdin", types.SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr(mod, "_prompt_yes_no", lambda prompt, default_yes=True: True)
    monkeypatch.setattr(mod.getpass, "getpass", lambda prompt: "secret-value")

    dotenv_path = mod._collect_secret_inputs(repo, "docsops")
    assert dotenv_path is not None and dotenv_path.exists()

    dotenv_text = dotenv_path.read_text(encoding="utf-8")
    assert "POSTMAN_API_KEY=secret-value" in dotenv_text
    assert "DOCSOPS_BOT_TOKEN=secret-value" in dotenv_text

    gitignore = (repo / ".gitignore").read_text(encoding="utf-8")
    assert mod.DOCSOPS_LOCAL_ENV in gitignore

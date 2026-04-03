from __future__ import annotations

import copy
import json
from pathlib import Path

import yaml

from scripts import generate_public_docs_audit as public_audit
from scripts import personal_wizard as pw
from scripts import setup_client_env_wizard as env_wizard


def _base_profile() -> dict:
    return {
        "client": {"id": "demo", "company_name": "Demo", "contact_email": "demo@example.com"},
        "runtime": {
            "docs_root": "docs",
            "api_root": "api",
            "sdk_root": "sdk",
            "docs_flow": {"mode": "hybrid"},
            "output_targets": ["mkdocs"],
            "pr_autofix": {"enabled": False},
            "integrations": {
                "algolia": {"enabled": False, "upload_on_weekly": False, "site_generator": "mkdocs"},
                "ask_ai": {"enabled": False, "provider": "openai", "billing_mode": "disabled"},
            },
            "api_first": {
                "enabled": True,
                "sandbox_backend": "external",
                "mock_base_url": "https://mock.example.com/v1",
                "verify_user_path": False,
                "sync_playground_endpoint": True,
                "generate_test_assets": True,
                "upload_test_assets": True,
                "external_mock": {"enabled": True, "provider": "postman", "postman": {}},
                "test_management": {
                    "testrail": {},
                    "zephyr_scale": {},
                },
            },
            "custom_tasks": {"weekly": [], "on_demand": []},
            "modules": {"rag_optimization": True, "api_first_flow": True},
            "veridoc_branding": {"enabled": True, "landing_url": "https://veri-doc.app/"},
            "llm_control": {},
            "finalize_gate": {"ask_commit_confirmation": False, "commit_on_approve": True},
        },
        "bundle": {
            "style_guide": "google",
            "output_dir": "generated/personal_bundles",
            "base_policy_pack": "minimal",
            "include_scripts": [],
            "include_docs": [],
            "include_paths": ["templates/interactive-diagram.html"],
            "policy_overrides": {},
        },
    }


def test_build_personal_env_template_full_branches(tmp_path: Path) -> None:
    runtime_cfg = _base_profile()["runtime"]
    runtime_cfg["integrations"]["algolia"]["enabled"] = True
    runtime_cfg["integrations"]["ask_ai"]["enabled"] = True
    runtime_cfg["integrations"]["ask_ai"]["provider"] = "azure-openai"
    runtime_cfg["integrations"]["ask_ai"]["billing_mode"] = "user-subscription"
    runtime_cfg["pr_autofix"]["enabled"] = True
    runtime_cfg["veridoc_branding"]["enabled"] = True
    runtime_cfg["api_first"]["upload_test_assets"] = True

    pw.build_personal_env_template(runtime_cfg, tmp_path)
    data = (tmp_path / ".env.docsops.local.template").read_text(encoding="utf-8")
    assert "ALGOLIA_APP_ID" in data
    assert "AZURE_OPENAI_API_KEY" in data
    assert "TESTRAIL_UPLOAD_ENABLED" in data
    assert "ZEPHYR_UPLOAD_ENABLED" in data
    assert "VERIDOC_REFERRAL_CODE" in data
    assert "DOCSOPS_BOT_TOKEN" in data


def test_create_personal_profile_interactive_hybrid(tmp_path: Path, monkeypatch) -> None:
    profile = _base_profile()
    generated = tmp_path / "generated.yml"

    monkeypatch.setattr(pw, "_build_profile_from_preset", lambda preset: copy.deepcopy(profile))
    monkeypatch.setattr(pw, "_save_generated_profile", lambda payload, client_id: generated)

    choices = iter(
        [
            "startup",  # preset
            "hybrid",  # llm mode
            "hybrid",  # flow mode
            "google",  # style guide
            "external",  # sandbox backend
            "mkdocs",  # algolia generator
            "free",  # branding plan
            "openai",  # ask ai provider
            "platform-paid",  # ask ai billing mode
        ]
    )
    yes_no = iter(
        [
            True,   # enable PR autofix
            True,   # upload API test assets
            True,   # enable Algolia
            True,   # enable Ask AI
            True,   # enable branding
            True,   # enable weekly intent
            True,   # finalize confirmation
            True,   # configure advanced
            True,   # module api_first_flow
            True,   # module rag_optimization
            True,   # verify user path
            True,   # sync playground endpoint
            True,   # generate test assets
            True,   # git sync enabled
            True,   # algolia upload weekly
            True,   # ask ai install runtime pack
        ]
    )
    csv_values = iter(
        [
            ["mkdocs", "github"],
            ["templates/interactive-diagram.html", "knowledge_modules"],
            ["scripts/custom_task.py"],
            ["python3 scripts/custom_weekly.py"],
        ]
    )
    prompts = iter(
        [
            "ACME Docs",  # company name
            "acme-docs",  # client id
            "docs@acme.example",  # email
            "docs",
            "api",
            "sdk",
            "https://mock.example.com/v1",
            "https://veri-doc.app/",
            ".",  # git sync repo path
            "origin",
            "main",
        ]
    )

    monkeypatch.setattr(pw, "_prompt_choice", lambda *a, **k: next(choices))
    monkeypatch.setattr(pw, "_prompt_yes_no", lambda *a, **k: next(yes_no))
    monkeypatch.setattr(pw, "_prompt_csv", lambda *a, **k: next(csv_values))
    monkeypatch.setattr(pw, "_prompt", lambda *a, **k: next(prompts))

    out_path, client_id = pw._create_personal_profile()
    assert out_path == generated
    assert client_id == "acme-docs"


def test_create_personal_bundle_basic(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "policy_packs").mkdir(parents=True)
    (repo_root / "policy_packs" / "minimal.yml").write_text("policy: minimal\n", encoding="utf-8")
    monkeypatch.setattr(pw, "REPO_ROOT", repo_root)

    profile = _base_profile()
    profile_path = tmp_path / "profile.yml"
    profile_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")

    monkeypatch.setattr(pw, "read_yaml", lambda path: profile if Path(path) == profile_path else {"policy": "minimal"})
    monkeypatch.setattr(pw, "copy_into_bundle", lambda rel, bundle_root: None)
    monkeypatch.setattr(pw, "copy_path_into_bundle", lambda rel, bundle_root: None)
    monkeypatch.setattr(pw, "build_runtime_config", lambda p: p["runtime"])
    monkeypatch.setattr(pw, "build_llm_instruction_files", lambda p, bundle_root: None)
    monkeypatch.setattr(pw, "build_automation_files", lambda p, bundle_root: None)
    monkeypatch.setattr(pw, "build_vale_config", lambda p, bundle_root: None)

    bundle = pw.create_personal_bundle(profile_path)
    assert bundle.exists()
    assert (bundle / "config" / "client_runtime.yml").exists()
    info = yaml.safe_load((bundle / "BUNDLE_INFO.yml").read_text(encoding="utf-8"))
    assert info["personal_bundle"] is True


def test_personal_wizard_main_non_interactive(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    profile_path = repo_root / "profiles" / "clients" / "generated" / "demo.client.yml"
    profile_path.parent.mkdir(parents=True)
    profile_payload = _base_profile()
    profile_path.write_text(yaml.safe_dump(profile_payload, sort_keys=False), encoding="utf-8")

    monkeypatch.setattr(pw, "REPO_ROOT", repo_root)
    monkeypatch.setattr(pw, "_print_profile_preview", lambda path: None)
    monkeypatch.setattr(pw, "create_personal_bundle", lambda path: repo_root / "generated/personal_bundles/demo")

    monkeypatch.setattr("sys.argv", ["personal_wizard.py", "--profile", str(profile_path), "--yes"])
    assert pw.main() == 0


def test_env_wizard_local_mode_with_install(tmp_path: Path, monkeypatch) -> None:
    template = tmp_path / ".env.docsops.local.template"
    template.write_text("A=1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    runtime = {
        "llm_control": {
            "llm_mode": "local_default",
            "strict_local_first": True,
            "local_model": "veridoc-writer",
            "local_base_model": "qwen3:30b",
            "auto_install_local_model_on_setup": True,
        }
    }

    answers = iter(["", "y", "y", "y"])  # key, install model, create model, install CI
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    monkeypatch.setattr(env_wizard, "_load_runtime", lambda repo_root: runtime)
    monkeypatch.setattr(env_wizard, "_install_ollama_and_model", lambda model: None)
    monkeypatch.setattr(env_wizard, "_create_veridoc_modelfile", lambda repo_root, base_model, model_name: tmp_path / "Modelfile")
    monkeypatch.setattr(env_wizard, "_create_ollama_model", lambda model_name, modelfile_path: None)
    monkeypatch.setattr(env_wizard, "install_docs_ci_files", lambda *a, **k: [tmp_path / "Jenkinsfile.docsops"])

    assert env_wizard.main() == 0
    out = (tmp_path / ".env.docsops.local").read_text(encoding="utf-8")
    assert "A=" in out
    assert "VERIOPS_PACK_REGISTRY_URL=https://api.veri-doc.app/ops/pack-registry/fetch" in out


def test_env_wizard_cloud_mode_skips_local_install(tmp_path: Path, monkeypatch) -> None:
    template = tmp_path / ".env.docsops.local.template"
    template.write_text("A=1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    runtime = {"llm_control": {"llm_mode": "external_preferred", "strict_local_first": False}}
    answers = iter(["", "n"])  # key, install CI
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    monkeypatch.setattr(env_wizard, "_load_runtime", lambda repo_root: runtime)
    monkeypatch.setattr(env_wizard, "install_docs_ci_files", lambda *a, **k: [])
    assert env_wizard.main() == 0


def test_env_wizard_template_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert env_wizard.main() == 2


def _audit_aggregate_payload() -> dict:
    return {
        "metrics": {
            "crawl": {
                "pages_crawled": 12,
                "urls_examined": 12,
                "requested_pages": 12,
                "discovered_pages": 12,
                "crawl_scope_pages": 12,
                "crawl_scope_basis": "sitemap",
                "crawl_coverage_pct": 100.0,
            },
            "links": {
                "broken_internal_links_count": 0,
                "docs_broken_links_count": 0,
                "repo_broken_links_count": 0,
                "unverified_links_count": 0,
            },
            "seo_geo": {"seo_geo_issue_rate_pct": 1.0},
            "api_coverage": {
                "reference_coverage_pct": 85.0,
                "api_pages_detected": 6,
                "detection_note": "",
                "no_api_pages_found": False,
            },
            "examples": {"example_reliability_estimate_pct": 80.0, "detection_note": ""},
            "freshness": {"last_updated_coverage_pct": 80.0},
        },
        "confidence": {"score": 0.9},
    }


def test_public_audit_main_non_interactive(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(public_audit, "_site_payload", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(public_audit, "_merge_site_runs", lambda runs: {"site_url": "https://docs.example.com"})
    monkeypatch.setattr(public_audit, "_aggregate_sites", lambda sites: _audit_aggregate_payload())
    monkeypatch.setattr(public_audit, "_build_html", lambda payload: "<html>ok</html>")
    monkeypatch.setattr(public_audit, "_build_broken_links_export", lambda payload: {"items": []})
    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_public_docs_audit.py",
            "--site-url",
            "docs.example.com",
            "--json-output",
            str(tmp_path / "reports" / "audit.json"),
            "--html-output",
            str(tmp_path / "reports" / "audit.html"),
            "--broken-links-output",
            str(tmp_path / "reports" / "broken.json"),
        ],
    )
    assert public_audit.main() == 0
    assert (tmp_path / "reports" / "audit.json").exists()
    assert (tmp_path / "reports" / "audit.html").exists()
    assert (tmp_path / "reports" / "broken.json").exists()


def test_public_audit_main_interactive_with_pdf(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(public_audit, "_site_payload", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(public_audit, "_merge_site_runs", lambda runs: {"site_url": "https://docs.example.com"})
    monkeypatch.setattr(public_audit, "_aggregate_sites", lambda sites: _audit_aggregate_payload())
    monkeypatch.setattr(public_audit, "_build_html", lambda payload: "<html>ok</html>")
    monkeypatch.setattr(public_audit, "_build_broken_links_export", lambda payload: {"items": []})
    monkeypatch.setattr(public_audit, "_resolve_company_assumptions_path", lambda **kwargs: "")

    class _Proc:
        def __init__(self, rc: int = 0):
            self.returncode = rc
            self.stderr = ""

    monkeypatch.setattr(public_audit.subprocess, "run", lambda *a, **k: _Proc(0))

    answers = iter(
        [
            "docs.example.com",  # URL #1
            "",  # end urls
            "single-product",
            "0",  # max pages
            "10",  # timeout
            "Acme",
            "",  # output dir default
            "3",  # llm none
            "y",  # generate pdf
            "",  # pdf default path
        ]
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_public_docs_audit.py",
            "--interactive",
            "--runtime-config",
            "docsops/config/client_runtime.yml",
        ],
    )
    assert public_audit.main() == 0
    out_dir = tmp_path / "reports" / "acme"
    assert (out_dir / "public_docs_audit.json").exists()

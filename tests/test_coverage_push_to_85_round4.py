from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _mk_frontmatter_page(title: str) -> str:
    return (
        "---\n"
        f"title: {title}\n"
        "description: Demo page description long enough for checks.\n"
        "content_type: reference\n"
        "product: both\n"
        "tags:\n"
        "  - API\n"
        "---\n\n"
        "Powered by VeriDoc\n\n"
        "Body text.\n"
    )


def _create_acme_demo_tree(root: Path) -> None:
    from scripts import build_acme_demo_site as mod

    docs = root / "docs"
    for rel in mod.REQUIRED_PAGES:
        target = docs / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_mk_frontmatter_page(rel), encoding="utf-8")

    # Optional badge page can be plain
    (docs / "quality" / "review-manifest.md").write_text("# Review\n", encoding="utf-8")

    nav = []
    for rel in mod.REQUIRED_PAGES:
        nav.append({rel: rel})
    (root / "mkdocs.yml").write_text(yaml.safe_dump({"nav": nav}, sort_keys=False), encoding="utf-8")


def test_build_acme_validate_assets_contract_and_built_site(tmp_path: Path) -> None:
    from scripts import build_acme_demo_site as mod

    _create_acme_demo_tree(tmp_path)
    docs = tmp_path / "docs"

    assets = docs / "assets"
    (assets / "api").mkdir(parents=True, exist_ok=True)
    (assets / "api" / "openapi.yaml").write_text("openapi: 3.0.3\n", encoding="utf-8")
    (assets / "knowledge-retrieval-index.json").write_text('{"records": []}\n', encoding="utf-8")
    (assets / "knowledge-graph.jsonld").write_text('{"nodes": [], "edges": []}\n', encoding="utf-8")
    (assets / "facets-index.json").write_text('{"records": []}\n', encoding="utf-8")
    (assets / "javascripts").mkdir(parents=True, exist_ok=True)
    (assets / "javascripts" / "sandbox-config.js").write_text(
        "asyncapi_ws_fallback_urls websocket_fallback_urls wss://echo.websocket.events\n",
        encoding="utf-8",
    )

    ws = docs / "reference" / "websocket-events.md"
    ws.write_text(
        "__ACME_SANDBOX_CONTROLLER__ live-echo-plus-semantic offline-semantic-fallback simulated_response\n",
        encoding="utf-8",
    )
    asyncp = docs / "reference" / "asyncapi-events.md"
    asyncp.write_text(
        "__ACME_SANDBOX_CONTROLLER__ live-echo-plus-semantic offline-semantic-fallback "
        "simulated_response project.updated task.completed\n",
        encoding="utf-8",
    )

    (docs / "reference" / "swagger-test.html").write_text("<html></html>\n", encoding="utf-8")

    mod._validate_assets_contract(tmp_path)

    site = tmp_path / "site"
    (site / "reference" / "rest-api").mkdir(parents=True, exist_ok=True)
    (site / "reference" / "rest-api" / "index.html").write_text(
        '../swagger-test.html "content.code.copy"',
        encoding="utf-8",
    )
    (site / "reference").mkdir(parents=True, exist_ok=True)
    (site / "reference" / "swagger-test.html").write_text("ok", encoding="utf-8")
    (site / "assets" / "javascripts").mkdir(parents=True, exist_ok=True)
    (site / "assets" / "javascripts" / "app.js").write_text("clipboard.js", encoding="utf-8")

    mod._validate_built_site_contract(tmp_path)


def test_build_acme_build_demo_and_main_branches(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import build_acme_demo_site as mod

    _create_acme_demo_tree(tmp_path)
    reports = tmp_path / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    calls: list[str] = []

    def fake_validate_page_contract(_: Path) -> None:
        calls.append("validate_page")

    def fake_sync_assets(_: Path, __: Path) -> None:
        calls.append("sync_assets")

    def fake_validate_assets(_: Path) -> None:
        calls.append("validate_assets")

    def fake_validate_scope(_: Path) -> None:
        calls.append("validate_scope")

    def fake_run_quality_stack(**_: object) -> None:
        calls.append("quality")

    def fake_run(cmd: list[str], cwd: Path) -> None:
        calls.append("run:" + " ".join(cmd))

    def fake_validate_built(_: Path) -> None:
        calls.append("validate_built")

    monkeypatch.setattr(mod, "_validate_page_contract", fake_validate_page_contract)
    monkeypatch.setattr(mod, "_sync_pipeline_assets", fake_sync_assets)
    monkeypatch.setattr(mod, "_validate_assets_contract", fake_validate_assets)
    monkeypatch.setattr(mod, "_validate_scope", fake_validate_scope)
    monkeypatch.setattr(mod, "_run_quality_stack", fake_run_quality_stack)
    monkeypatch.setattr(mod, "_run", fake_run)
    monkeypatch.setattr(mod, "_validate_built_site_contract", fake_validate_built)

    mod.build_demo(tmp_path, reports, build_site=True, strict_quality=True)
    assert "quality" in calls
    assert any(c.startswith("run:mkdocs build") for c in calls)
    assert "validate_built" in calls

    monkeypatch.setattr(sys, "argv", ["x", "--output-root", str(tmp_path), "--reports-dir", str(reports), "--skip-strict-quality"])
    rc = mod.main()
    assert rc == 0


def test_run_autopipeline_guardrails_and_publish_helpers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import run_autopipeline as mod

    runtime = {
        "llm_control": {
            "llm_mode": "external_preferred",
            "strict_local_first": True,
            "external_llm_allowed": True,
            "require_explicit_approval": False,
        },
        "integrations": {
            "algolia": {"enabled": True, "upload_on_weekly": True},
            "ask_ai": {"enabled": True, "billing_mode": "user-subscription"},
        },
        "api_first": {
            "sandbox_backend": "external",
            "upload_test_assets": True,
            "upload_test_assets_strict": True,
            "external_mock": {"enabled": True},
        },
        "api_protocol_settings": {"rest": {"upload_test_assets": True}},
    }
    adjusted, changed = mod._enforce_strict_local_guardrails(runtime)
    assert changed is True
    assert adjusted["llm_control"]["llm_mode"] == "local_default"
    assert adjusted["integrations"]["algolia"]["enabled"] is False
    assert adjusted["api_first"]["sandbox_backend"] == "prism"

    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{", encoding="utf-8")
    assert mod._safe_load_json(bad_json) == {}

    repo = tmp_path / "repo"
    out_idx = tmp_path / "AUTOPIPELINE_OUTPUT_INDEX.md"
    out_idx.write_text("# x\n", encoding="utf-8")
    repo.mkdir(parents=True, exist_ok=True)
    assert mod._publish_output_index_to_docs(repo, out_idx) is None

    (repo / "docs" / "operations").mkdir(parents=True, exist_ok=True)
    target = mod._publish_output_index_to_docs(repo, out_idx)
    assert target is not None and target.exists()
    assert "Autopipeline Output Index" in target.read_text(encoding="utf-8")

    class _Completed:
        def __init__(self, rc: int, out: str) -> None:
            self.returncode = rc
            self.stdout = out

    monkeypatch.setattr(
        mod.subprocess,
        "run",
        lambda *args, **kwargs: _Completed(0, " M docs/index.md\n?? reports/x.json\n"),
    )
    changed_files = mod._git_changed_files(repo)
    assert "docs/index.md" in changed_files
    assert "reports/x.json" in changed_files


def test_run_autopipeline_main_enterprise_strict_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import run_autopipeline as mod

    docsops = tmp_path / "docsops"
    (docsops / "config").mkdir(parents=True)
    runtime = {
        "api_governance": {"strictness": "enterprise-strict"},
        "docs_flow": {"mode": "code-first"},
        "modules": {},
        "paths": {"docs_root": "docs"},
    }
    runtime_path = docsops / "config" / "client_runtime.yml"
    runtime_path.write_text(yaml.safe_dump(runtime, sort_keys=False), encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(mod, "_run", lambda cmd, cwd: 7 if "run_weekly_gap_batch.py" in " ".join(cmd) else 0)
    monkeypatch.setattr(
        mod,
        "_build_stage_summary",
        lambda **kwargs: {
            "weekly_rc": 7,
            "strictness": "enterprise-strict",
            "skip_consolidated_report": False,
            "missing_required_artifacts": 0,
            "stages": [],
        },
    )
    monkeypatch.setattr(mod, "_write_review_manifest", lambda *a, **k: (tmp_path / "reports" / "REVIEW_MANIFEST.md"))

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "x",
            "--docsops-root",
            "docsops",
            "--reports-dir",
            "reports",
            "--runtime-config",
            str(runtime_path),
            "--mode",
            "operator",
            "--skip-local-llm-packet",
        ],
    )

    rc = mod.main()
    assert rc == 7


def test_build_client_bundle_env_template_provider_branches(tmp_path: Path) -> None:
    from scripts import build_client_bundle as mod

    # custom provider branch
    runtime_custom = {
        "integrations": {"ask_ai": {"enabled": True, "provider": "custom", "billing_mode": "disabled"}},
        "api_first": {"enabled": False},
    }
    mod.build_local_env_template(runtime_custom, tmp_path)
    text = (tmp_path / ".env.docsops.local.template").read_text(encoding="utf-8")
    assert "ASK_AI_API_KEY" in text
    assert "ASK_AI_BASE_URL" in text

    # azure provider + upload assets branch
    runtime_azure = {
        "integrations": {"ask_ai": {"enabled": True, "provider": "azure-openai", "billing_mode": "disabled"}},
        "api_first": {
            "enabled": True,
            "sandbox_backend": "external",
            "external_mock": {
                "enabled": True,
                "provider": "postman",
                "postman": {
                    "api_key_env": "POSTMAN_API_KEY",
                    "workspace_id_env": "POSTMAN_WORKSPACE_ID",
                    "collection_uid_env": "POSTMAN_COLLECTION_UID",
                    "mock_server_id_env": "POSTMAN_MOCK_SERVER_ID",
                },
            },
            "upload_test_assets": True,
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
        },
        "veridoc_branding": {"enabled": True, "referral_code_env": "VERIDOC_REFERRAL_CODE"},
        "pr_autofix": {"enabled": True},
    }
    mod.build_local_env_template(runtime_azure, tmp_path)
    text2 = (tmp_path / ".env.docsops.local.template").read_text(encoding="utf-8")
    assert "AZURE_OPENAI_API_KEY" in text2
    assert "POSTMAN_API_KEY" in text2
    assert "TESTRAIL_UPLOAD_ENABLED" in text2
    assert "ZEPHYR_UPLOAD_ENABLED" in text2
    assert "VERIDOC_REFERRAL_CODE" in text2
    assert "DOCSOPS_BOT_TOKEN" in text2

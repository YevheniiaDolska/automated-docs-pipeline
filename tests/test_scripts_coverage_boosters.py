from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestAutoFixPrDocs:
    def test_render_list_and_doc_content(self) -> None:
        from scripts import auto_fix_pr_docs as mod

        assert mod._render_list([]) == "- none"
        content = mod._build_doc_content(
            42,
            ["api/openapi.yaml"],
            {
                "interface_changed": ["api/openapi.yaml"],
                "openapi_changed": ["api/openapi.yaml"],
                "sdk_changed": [],
            },
        )
        assert "PR 42 API and docs sync note" in content
        assert "## Changed files in PR" in content
        assert "`api/openapi.yaml`" in content

    def test_main_no_fix_needed(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        from scripts import auto_fix_pr_docs as mod

        monkeypatch.setattr(mod, "_changed_files", lambda b, h: ["docs/a.md"])
        monkeypatch.setattr(mod, "evaluate_contract", lambda files: {"blocked": False, "interface_changed": []})
        monkeypatch.setattr(
            mod,
            "evaluate_drift",
            lambda files: type("Drift", (), {"status": "ok", "openapi_changed": [], "sdk_changed": []})(),
        )
        monkeypatch.setattr(sys, "argv", ["x", "--base", "a", "--head", "b", "--pr-number", "1"])
        rc = mod.main()
        assert rc == 0
        assert "no docs auto-fix required" in capsys.readouterr().out

    def test_main_writes_fix_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import auto_fix_pr_docs as mod

        monkeypatch.setattr(mod, "_changed_files", lambda b, h: ["api/openapi.yaml"])
        monkeypatch.setattr(
            mod,
            "evaluate_contract",
            lambda files: {"blocked": True, "interface_changed": ["api/openapi.yaml"]},
        )
        monkeypatch.setattr(
            mod,
            "evaluate_drift",
            lambda files: type("Drift", (), {"status": "drift", "openapi_changed": ["api/openapi.yaml"], "sdk_changed": []})(),
        )
        out_dir = tmp_path / "docs-out"
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "x",
                "--base",
                "a",
                "--head",
                "b",
                "--pr-number",
                "9",
                "--output-dir",
                str(out_dir),
            ],
        )
        rc = mod.main()
        assert rc == 0
        out_file = out_dir / "pr-9-api-doc-sync.md"
        assert out_file.exists()
        assert "PR number: `9`" in out_file.read_text(encoding="utf-8")


class TestEnsureExternalMockServer:
    def test_read_env_and_normalize_helpers(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import ensure_external_mock_server as mod

        monkeypatch.delenv("X_REQ", raising=False)
        with pytest.raises(RuntimeError):
            mod._read_env("X_REQ", required=True)
        monkeypatch.setenv("X_REQ", " value ")
        assert mod._read_env("X_REQ", required=True) == "value"
        assert mod._normalize_base_path("") == ""
        assert mod._normalize_base_path("v1") == "/v1"
        assert mod._normalize_base_path("/v1/") == "/v1"

    def test_find_mock_node_recursive(self) -> None:
        from scripts import ensure_external_mock_server as mod

        payload = {"a": {"b": [{"x": 1}, {"id": "m1", "url": "https://mock"}]}}
        node = mod._find_mock_node(payload)
        assert node is not None
        assert node["id"] == "m1"

    def test_resolve_postman_mock_reuse_existing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import ensure_external_mock_server as mod

        monkeypatch.setenv("POSTMAN_API_KEY", "k")
        monkeypatch.setenv("POSTMAN_MOCK_SERVER_ID", "mid")
        args = type(
            "Args",
            (),
            {
                "postman_api_key_env": "POSTMAN_API_KEY",
                "postman_mock_server_id_env": "POSTMAN_MOCK_SERVER_ID",
                "postman_workspace_id_env": "POSTMAN_WORKSPACE_ID",
                "postman_collection_uid_env": "POSTMAN_COLLECTION_UID",
                "postman_mock_server_name": "",
                "postman_private": False,
                "project_slug": "proj",
                "spec_path": "",
            },
        )()

        monkeypatch.setattr(mod, "_http_json", lambda *a, **k: {"mockServer": {"id": "mid", "url": "https://m"}})
        resolved = mod._resolve_postman_mock(args)
        assert resolved["mock_server_id"] == "mid"
        assert resolved["mock_url"] == "https://m"

    def test_resolve_postman_import_and_create(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import ensure_external_mock_server as mod

        spec = tmp_path / "openapi.yaml"
        spec.write_text("openapi: 3.0.3\ninfo:\n  title: T\n  version: 1.0.0\npaths: {}\n", encoding="utf-8")

        monkeypatch.setenv("POSTMAN_API_KEY", "k")
        monkeypatch.setenv("POSTMAN_WORKSPACE_ID", "w")
        monkeypatch.delenv("POSTMAN_COLLECTION_UID", raising=False)
        monkeypatch.delenv("POSTMAN_MOCK_SERVER_ID", raising=False)

        calls: list[tuple[str, str]] = []

        def fake_http(method: str, url: str, **kwargs):  # type: ignore[no-untyped-def]
            calls.append((method, url))
            if url.endswith("/import/openapi"):
                return {"collections": [{"uid": "c123"}]}
            return {"mock": {"id": "m123", "url": "https://mock.example.com"}}

        monkeypatch.setattr(mod, "_http_json", fake_http)
        args = type(
            "Args",
            (),
            {
                "postman_api_key_env": "POSTMAN_API_KEY",
                "postman_mock_server_id_env": "POSTMAN_MOCK_SERVER_ID",
                "postman_workspace_id_env": "POSTMAN_WORKSPACE_ID",
                "postman_collection_uid_env": "POSTMAN_COLLECTION_UID",
                "postman_mock_server_name": "",
                "postman_private": True,
                "project_slug": "proj",
                "spec_path": str(spec),
            },
        )()

        resolved = mod._resolve_postman_mock(args)
        assert resolved["mock_server_id"] == "m123"
        assert resolved["mock_url"].startswith("https://mock.")
        assert any(url.endswith("/import/openapi") for _, url in calls)
        assert any(url.endswith("/mockservers") for _, url in calls)

    def test_main_writes_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        from scripts import ensure_external_mock_server as mod

        output = tmp_path / "resolved.json"
        monkeypatch.setattr(
            mod,
            "_resolve_postman_mock",
            lambda args: {"mock_server_id": "m", "mock_url": "https://m.example.com"},
        )
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "x",
                "--project-slug",
                "proj",
                "--base-path",
                "/v1",
                "--output-json",
                str(output),
            ],
        )
        rc = mod.main()
        assert rc == 0
        payload = json.loads(output.read_text(encoding="utf-8"))
        assert payload["mock_base_url"] == "https://m.example.com/v1"
        assert "mock_base_url" in capsys.readouterr().out


class TestNormalizeDocs:
    def test_parse_frontmatter_and_lines(self) -> None:
        from scripts import normalize_docs as mod

        fm, body = mod.parse_frontmatter("---\ncontent_type: how-to\n---\n\nText\n")
        assert fm["content_type"] == "how-to"
        assert "Text" in body

        lines = mod.normalize_lines(["2. A", "* b", "## next steps"])
        assert lines[0] == "1. A"
        assert lines[1] == "- b"
        assert lines[2] == "## Next steps"

    def test_normalize_markdown_appends_next_steps(self, tmp_path: Path) -> None:
        from scripts import normalize_docs as mod

        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        (docs_root / "index.md").write_text("# Home\n", encoding="utf-8")
        page = docs_root / "how-to.md"
        text = "---\ncontent_type: how-to\n---\n\nHello\n"
        normalized = mod.normalize_markdown(text, page, docs_root)
        assert "## Next steps" in normalized
        assert "[Documentation index]" in normalized

    def test_collect_files_and_main_modes(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import normalize_docs as mod

        docs = tmp_path / "docs"
        docs.mkdir()
        md = docs / "a.md"
        md.write_text("---\ncontent_type: how-to\n---\n\n2. A\n", encoding="utf-8")

        files = mod.collect_files([str(docs)])
        assert md in files

        monkeypatch.setattr(sys, "argv", ["x", str(docs), "--check"])
        assert mod.main() == 1
        monkeypatch.setattr(sys, "argv", ["x", str(docs)])
        assert mod.main() == 0


class TestInstallAskAiRuntime:
    def test_copy_pack_and_write_report(self, tmp_path: Path) -> None:
        from scripts import install_ask_ai_runtime as mod

        source = tmp_path / "src"
        source.mkdir()
        (source / "a.txt").write_text("x\n", encoding="utf-8")
        dst = tmp_path / "dst"
        mod._copy_pack(source, dst, force=False)
        assert (dst / "a.txt").exists()
        with pytest.raises(FileExistsError):
            mod._copy_pack(source, dst, force=False)
        mod._copy_pack(source, dst, force=True)

        report = mod._write_install_report(tmp_path, "ask-ai-runtime")
        payload = json.loads(report.read_text(encoding="utf-8"))
        assert payload["installed"] is True

    def test_update_ask_ai_config(self, tmp_path: Path) -> None:
        from scripts import install_ask_ai_runtime as mod

        cfg = tmp_path / "config" / "ask-ai.yml"
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(yaml.safe_dump({"enabled": True, "runtime": {"base_url": "http://custom"}}), encoding="utf-8")
        mod._update_ask_ai_config(cfg, "ask-ai-runtime")
        data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        assert data["enabled"] is True
        assert data["runtime"]["runtime_dir"] == "ask-ai-runtime"
        assert data["runtime"]["base_url"] == "http://custom"


class TestKnowledgeRetrievalIndex:
    def test_load_modules_and_transform(self, tmp_path: Path) -> None:
        from scripts import generate_knowledge_retrieval_index as mod

        modules = tmp_path / "knowledge_modules"
        modules.mkdir()
        (modules / "a.yml").write_text(
            yaml.safe_dump(
                {
                    "id": "m1",
                    "title": "Module",
                    "status": "active",
                    "content": {"docs_markdown": "A" * 500, "assistant_context": "B" * 400},
                    "intents": ["configure"],
                }
            ),
            encoding="utf-8",
        )
        (modules / "b.yml").write_text("[]\n", encoding="utf-8")
        loaded = mod._load_modules(modules)
        assert len(loaded) == 1
        rec = mod._module_to_index_record(loaded[0])
        assert rec["docs_excerpt"] == "A" * 400
        assert rec["assistant_excerpt"] == "B" * 300

    def test_main_writes_only_active(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        from scripts import generate_knowledge_retrieval_index as mod

        modules = tmp_path / "knowledge_modules"
        modules.mkdir()
        (modules / "a.yml").write_text(yaml.safe_dump({"id": "a", "status": "active", "content": {}}), encoding="utf-8")
        (modules / "b.yml").write_text(yaml.safe_dump({"id": "b", "status": "draft", "content": {}}), encoding="utf-8")
        output = tmp_path / "docs" / "assets" / "index.json"

        monkeypatch.setattr(sys, "argv", ["x", "--modules-dir", str(modules), "--output", str(output)])
        mod.main()
        payload = json.loads(output.read_text(encoding="utf-8"))
        assert len(payload) == 1
        assert payload[0]["id"] == "a"
        assert "Generated retrieval index with 1 records" in capsys.readouterr().out


from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestExtractKnowledgeModules:
    def test_helpers(self) -> None:
        from scripts import extract_knowledge_modules_from_docs as mod

        assert mod._slug("Hello World!") == "hello-world"
        assert mod._slug("___") == "module"

        fm, body = mod._parse_frontmatter("---\ntitle: T\n---\nBody")
        assert fm["title"] == "T"
        assert body == "Body"
        fm2, body2 = mod._parse_frontmatter("No frontmatter")
        assert fm2 == {}
        assert body2 == "No frontmatter"

        intents = mod._pick_intents("troubleshooting", "Auth Error", "Fix secure flow")
        assert "troubleshoot" in intents
        assert "secure" in intents
        assert mod._pick_audiences("tutorial") == ["beginner", "practitioner"]

    def test_chunking_and_module_generation(self, tmp_path: Path) -> None:
        from scripts import extract_knowledge_modules_from_docs as mod

        body = "## A\n" + ("x" * 500) + "\n\n## B\n" + ("y" * 500)
        chunks = mod._chunk_body(body, chunk_target_chars=600)
        assert len(chunks) >= 2

        module = mod._module_for_chunk(
            tmp_path / "file.md",
            "docs/file.md",
            {"content_type": "how-to", "title": "Configure webhook"},
            "short",
            1,
            "owner-x",
        )
        assert module["id"].startswith("auto-file-1")
        assert module["owner"] == "owner-x"
        assert module["status"] == "active"
        assert len(module["content"]["docs_markdown"]) >= 80

    def test_main_success_and_missing_docs(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import extract_knowledge_modules_from_docs as mod

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "a.md").write_text(
            "---\n"
            "title: Configure Webhooks\n"
            "description: Configure webhook pipeline safely.\n"
            "content_type: how-to\n"
            "---\n\n"
            "## Step\n\nRun command.\n",
            encoding="utf-8",
        )
        modules = tmp_path / "knowledge_modules"
        modules.mkdir()
        (modules / "auto-old.yml").write_text("id: auto-old\n", encoding="utf-8")
        report = tmp_path / "reports" / "auto_extract.json"

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "x",
                "--docs-dir",
                str(docs),
                "--modules-dir",
                str(modules),
                "--report",
                str(report),
                "--chunk-target-chars",
                "200",
                "--owner",
                "docsops",
            ],
        )
        assert mod.main() == 0
        payload = json.loads(report.read_text(encoding="utf-8"))
        assert payload["modules_removed"] == 1
        assert payload["modules_created"] >= 1
        assert any(p.name.startswith("auto-") for p in modules.glob("*.yml"))

        missing_docs = tmp_path / "no-docs"
        monkeypatch.setattr(sys, "argv", ["x", "--docs-dir", str(missing_docs)])
        assert mod.main() == 1


class TestRetrievalEvals:
    def test_helpers_and_evaluate(self, tmp_path: Path) -> None:
        from scripts import run_retrieval_evals as mod

        assert "hello" in mod._tokenize("Hello, World!")
        index = [
            {"id": "m1", "title": "Webhook auth", "summary": "HMAC verification", "docs_excerpt": "", "assistant_excerpt": ""},
            {"id": "m2", "title": "Retry policy", "summary": "Exponential backoff", "docs_excerpt": "", "assistant_excerpt": ""},
        ]
        dataset = [{"query": "webhook auth", "expected_ids": ["m1"]}]
        metrics = mod.evaluate(index, dataset, top_k=1)
        assert metrics["status"] == "ok"
        assert metrics["precision_at_k"] >= 0
        assert metrics["recall_at_k"] >= 0

        err = mod.evaluate(index, [], top_k=1)
        assert err["status"] == "error"

        auto = mod._build_auto_dataset(index, limit=1)
        assert len(auto) == 1
        assert auto[0]["expected_ids"] == ["m1"]

        idx_path = tmp_path / "idx.json"
        idx_path.write_text(json.dumps(index), encoding="utf-8")
        assert len(mod._load_index(idx_path)) == 2
        ds_path = tmp_path / "dataset.yml"
        ds_path.write_text(yaml.safe_dump(dataset), encoding="utf-8")
        assert len(mod._load_dataset(ds_path)) == 1

    def test_main_success_and_breach(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import run_retrieval_evals as mod

        index = [
            {"id": "m1", "title": "Webhook auth", "summary": "HMAC verification", "docs_excerpt": "", "assistant_excerpt": "", "intents": [], "audiences": []},
            {"id": "m2", "title": "Retry policy", "summary": "Exponential backoff", "docs_excerpt": "", "assistant_excerpt": "", "intents": [], "audiences": []},
        ]
        index_path = tmp_path / "index.json"
        index_path.write_text(json.dumps(index), encoding="utf-8")
        report = tmp_path / "report.json"
        dataset_out = tmp_path / "generated.yml"

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "x",
                "--index",
                str(index_path),
                "--report",
                str(report),
                "--dataset-out",
                str(dataset_out),
                "--auto-generate-dataset",
                "--auto-samples",
                "2",
            ],
        )
        assert mod.main() == 0
        assert report.exists()
        assert dataset_out.exists()

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "x",
                "--index",
                str(index_path),
                "--report",
                str(report),
                "--auto-generate-dataset",
                "--min-precision",
                "0.99",
                "--min-recall",
                "0.99",
                "--max-hallucination-rate",
                "0.0",
            ],
        )
        assert mod.main() == 1

    def test_main_missing_index(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import run_retrieval_evals as mod

        missing = tmp_path / "missing.json"
        monkeypatch.setattr(sys, "argv", ["x", "--index", str(missing)])
        with pytest.raises(FileNotFoundError):
            mod.main()


class TestOnboardClient:
    def test_prompt_yes_no_and_preview(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        from scripts import onboard_client as mod

        monkeypatch.setattr("builtins.input", lambda *_a, **_k: "")
        assert mod._prompt_yes_no("Q", default_yes=True) is True
        monkeypatch.setattr("builtins.input", lambda *_a, **_k: "n")
        assert mod._prompt_yes_no("Q", default_yes=True) is False

        profile = tmp_path / "c.yml"
        profile.write_text(
            yaml.safe_dump(
                {
                    "client": {"id": "acme", "company_name": "Acme"},
                    "runtime": {
                        "docs_flow": {"mode": "hybrid"},
                        "output_targets": ["sphinx"],
                        "integrations": {"algolia": {"enabled": True}, "ask_ai": {"enabled": False}},
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        mod._print_profile_preview(profile)
        out = capsys.readouterr().out
        assert "Profile preview" in out
        assert "Client ID: acme" in out

        bad = tmp_path / "bad.yml"
        bad.write_text("- x\n", encoding="utf-8")
        mod._print_profile_preview(bad)
        assert "[warn] profile is not a mapping" in capsys.readouterr().out

    def test_main_paths(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import onboard_client as mod

        profile = tmp_path / "profile.yml"
        profile.write_text(yaml.safe_dump({"client": {"id": "x"}, "runtime": {}}), encoding="utf-8")
        resolved = SimpleNamespace(
            client=str(profile),
            client_repo=str(tmp_path / "repo"),
            docsops_dir="docsops",
            install_scheduler="none",
            interactive=True,
            generate_profile=True,
        )

        monkeypatch.setattr(mod.provision, "_resolve_args", lambda args: resolved)
        monkeypatch.setattr(mod, "_print_profile_preview", lambda p: None)
        monkeypatch.setattr(sys, "argv", ["x", "--yes"])
        monkeypatch.setattr(mod.provision, "execute_provision", lambda args: 0)
        assert mod.main() == 0

        monkeypatch.setattr(sys, "argv", ["x"])
        monkeypatch.setattr(mod, "_prompt_yes_no", lambda *a, **k: False)
        assert mod.main() == 0


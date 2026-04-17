"""Tests for knowledge system scripts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _write_module(path: Path, module_id: str, dependency: str | None = None) -> None:
    payload = {
        "id": module_id,
        "title": "Configure webhook signing validation",
        "summary": "Reusable module for secure webhook validation and duplicate prevention in docs and assistant channels.",
        "intents": ["configure", "secure"],
        "audiences": ["operator", "all"],
        "channels": ["docs", "assistant", "automation"],
        "priority": 90,
        "status": "active",
        "owner": "docs@example.com",
        "last_verified": "2026-03-07",
        "dependencies": [dependency] if dependency else [],
        "content": {
            "docs_markdown": "Use HMAC signature validation before parsing payload data. Reject stale requests older than 300 seconds and return HTTP 401 for invalid signatures.",
            "assistant_context": "Recommend HMAC validation, replay protection <=300 seconds, and key rotation every 90 days.",
            "automation_workflow": "Verify signature -> validate timestamp -> parse payload.",
        },
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_validate_modules_pass(tmp_path: Path) -> None:
    from scripts.validate_knowledge_modules import validate_modules

    modules_dir = tmp_path / "knowledge_modules"
    modules_dir.mkdir()
    _write_module(modules_dir / "a.yml", "module-a")
    _write_module(modules_dir / "b.yml", "module-b", dependency="module-a")

    modules, issues = validate_modules(modules_dir)

    assert len(modules) == 2
    assert issues == []


def test_validate_modules_dependency_error(tmp_path: Path) -> None:
    from scripts.validate_knowledge_modules import validate_modules

    modules_dir = tmp_path / "knowledge_modules"
    modules_dir.mkdir()
    _write_module(modules_dir / "a.yml", "module-a", dependency="module-missing")

    _, issues = validate_modules(modules_dir)

    assert any("unknown dependency" in issue.message for issue in issues)


def test_assemble_channel_bundle(tmp_path: Path) -> None:
    from scripts.assemble_intent_experience import _build_channel_bundle

    module = {
        "id": "module-a",
        "title": "Module A",
        "priority": 80,
        "content": {"assistant_context": "Assistant-ready context."},
    }

    bundle = _build_channel_bundle("configure", "operator", "assistant", [module])

    assert bundle["module_count"] == 1
    assert bundle["modules"][0]["module_id"] == "module-a"


def test_generate_retrieval_index_record() -> None:
    from scripts.generate_knowledge_retrieval_index import _module_to_index_record

    module = {
        "id": "module-a",
        "title": "Module A",
        "summary": "Summary",
        "status": "active",
        "priority": 50,
        "owner": "docs@example.com",
        "last_verified": "2026-03-07",
        "intents": ["configure"],
        "audiences": ["operator"],
        "channels": ["docs", "assistant"],
        "dependencies": [],
        "tags": ["How-To"],
        "content": {
            "docs_markdown": "A" * 450,
            "assistant_context": "B" * 350,
        },
        "source_file": "knowledge_modules/module-a.yml",
    }

    record = _module_to_index_record(module)

    assert record["objectID"] == "module-a"
    assert len(record["docs_excerpt"]) == 400
    assert len(record["assistant_excerpt"]) == 300


def test_generated_bundle_is_json_serializable() -> None:
    from scripts.assemble_intent_experience import _build_channel_bundle

    bundle = _build_channel_bundle(
        "secure",
        "operator",
        "automation",
        [
            {
                "id": "module-a",
                "title": "Module A",
                "priority": 70,
                "content": {"automation_workflow": "Step A -> Step B"},
            }
        ],
    )

    payload = json.dumps(bundle)
    assert "module-a" in payload


def test_sort_modules_uses_dependency_order() -> None:
    from scripts.assemble_intent_experience import _sort_modules

    modules = [
        {
            "id": "module-a",
            "priority": 95,
            "dependencies": ["module-b"],
        },
        {
            "id": "module-b",
            "priority": 20,
            "dependencies": [],
        },
        {
            "id": "module-c",
            "priority": 90,
            "dependencies": [],
        },
    ]

    sorted_modules = _sort_modules(modules)
    sorted_ids = [module["id"] for module in sorted_modules]

    assert sorted_ids.index("module-b") < sorted_ids.index("module-a")


def test_sort_modules_raises_on_cycle() -> None:
    from scripts.assemble_intent_experience import _sort_modules

    modules = [
        {
            "id": "module-a",
            "priority": 95,
            "dependencies": ["module-b"],
        },
        {
            "id": "module-b",
            "priority": 90,
            "dependencies": ["module-a"],
        },
    ]

    try:
        _sort_modules(modules)
        assert False, "Expected dependency cycle error"
    except ValueError as exc:
        assert "Dependency cycle detected" in str(exc)


def test_sort_modules_does_not_use_priority_for_root_order() -> None:
    from scripts.assemble_intent_experience import _sort_modules

    modules = [
        {
            "id": "module-z",
            "priority": 999,
            "dependencies": [],
        },
        {
            "id": "module-a",
            "priority": 1,
            "dependencies": [],
        },
    ]

    sorted_modules = _sort_modules(modules)
    sorted_ids = [module["id"] for module in sorted_modules]
    assert sorted_ids == ["module-a", "module-z"]


def test_detect_rag_contradictions_and_exclude_from_index(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import detect_rag_contradictions as detect_mod
    from scripts import generate_knowledge_retrieval_index as index_mod

    modules_dir = tmp_path / "knowledge_modules"
    modules_dir.mkdir()
    report_path = tmp_path / "reports" / "rag_contradictions_report.json"
    report_path.parent.mkdir(parents=True)
    index_path = tmp_path / "docs" / "assets" / "knowledge-retrieval-index.json"
    index_path.parent.mkdir(parents=True)

    mod_a = {
        "id": "module-a",
        "title": "Webhook setup",
        "summary": "A",
        "status": "active",
        "priority": 90,
        "owner": "docs@example.com",
        "last_verified": "2026-01-01",
        "metadata": {"source_path": "how-to/webhooks-a.md", "updated_at": "2026-01-01T00:00:00Z"},
        "semantic": {"topic": "Webhook setup"},
        "content": {
            "docs_markdown": "The default port is 5678. Set timeout to 30 seconds.",
            "assistant_context": "ctx",
        },
    }
    mod_b = {
        "id": "module-b",
        "title": "Webhook setup",
        "summary": "B",
        "status": "active",
        "priority": 85,
        "owner": "docs@example.com",
        "last_verified": "2026-01-02",
        "metadata": {"source_path": "how-to/webhooks-b.md", "updated_at": "2026-01-02T00:00:00Z"},
        "semantic": {"topic": "Webhook setup"},
        "content": {
            "docs_markdown": "The default port is 8080. Set timeout to 30 seconds.",
            "assistant_context": "ctx",
        },
    }
    (modules_dir / "a.yml").write_text(yaml.safe_dump(mod_a, sort_keys=False), encoding="utf-8")
    (modules_dir / "b.yml").write_text(yaml.safe_dump(mod_b, sort_keys=False), encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "x",
            "--modules-dir",
            str(modules_dir),
            "--report",
            str(report_path),
            "--min-similarity",
            "0.1",
            "--fail-on-critical",
        ],
    )
    assert detect_mod.main() == 2

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["summary"]["critical_contradictions"] >= 1
    assert "module-a" in report["critical_module_ids"]
    assert "module-b" in report["critical_module_ids"]

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "x",
            "--modules-dir",
            str(modules_dir),
            "--output",
            str(index_path),
            "--contradictions-report",
            str(report_path),
            "--exclude-critical-contradictions",
        ],
    )
    index_mod.main()
    records = json.loads(index_path.read_text(encoding="utf-8"))
    assert records == []

"""Tests for the LLM company-template planner (LLM mocked)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts import generate_company_templates as mod
from scripts import validate_frontmatter as vfm

_ALLOWED = {"Reference", "How-To", "Concept", "Tutorial", "Troubleshooting"}
_MODULE_IDS = {"auto-x-1"}
_SNIPPETS = {"sdk/create-charge"}


def _schema() -> dict:
    return vfm.load_schema("docs-schema.yml")


def _good_template() -> dict:
    return {
        "doc_type": "sdk-reference",
        "output_path": "docs/reference/sdk-reference.md",
        "frontmatter": {
            "title": "Payments SDK reference",
            "description": "Reference for the Payments SDK: install, initialize, and create charges safely.",
            "content_type": "reference",
            "product": "both",
            "tags": ["Reference"],
        },
        "intro": "The Payments SDK provides typed methods for charges and refunds.",
        "sections": [
            {
                "heading": "Create a charge",
                "slots": [
                    {"type": "snippet", "ref": "sdk/create-charge"},
                    {"type": "module", "ref": "auto-x-1"},
                ],
            }
        ],
    }


def test_validate_plan_accepts_good_plan() -> None:
    valid, errors = mod.validate_plan(
        {"templates": [_good_template()]},
        module_ids=_MODULE_IDS, snippet_refs=_SNIPPETS, schema=_schema(), allowed_tags=_ALLOWED,
    )
    assert errors == []
    assert len(valid) == 1


def test_validate_plan_flags_bad_refs_and_tags() -> None:
    bad = _good_template()
    bad["frontmatter"]["tags"] = ["Nonexistent"]
    bad["sections"][0]["slots"][1]["ref"] = "auto-missing"
    valid, errors = mod.validate_plan(
        {"templates": [bad]},
        module_ids=_MODULE_IDS, snippet_refs=_SNIPPETS, schema=_schema(), allowed_tags=_ALLOWED,
    )
    assert valid == []
    assert any("not a known module id" in e for e in errors)
    assert any("not in the allowed set" in e for e in errors)


def test_plan_templates_repairs_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    bad = _good_template()
    bad["frontmatter"]["content_type"] = "manual"  # invalid enum
    responses = [{"templates": [bad]}, {"templates": [_good_template()]}]

    def _fake_llm(**kwargs: object) -> dict:
        return responses.pop(0)

    monkeypatch.setattr(mod, "_run_llm_json_prompt", _fake_llm)
    specs, errors = mod.plan_templates(
        {"company": "ACME"},
        provider={"name": "deepseek", "style": "openai", "base_url": "x", "api_key_env": "K"},
        api_key="k", model="deepseek-chat", timeout=10,
        module_ids=_MODULE_IDS, snippet_refs=_SNIPPETS, schema=_schema(), allowed_tags=_ALLOWED,
    )
    assert errors == []
    assert len(specs) == 1
    assert responses == []  # both attempts consumed


def test_write_and_render_creates_spec_and_doc(tmp_path: Path) -> None:
    modules_dir = tmp_path / "modules"
    modules_dir.mkdir()
    (modules_dir / "auto-x-1.yml").write_text(
        "id: auto-x-1\nsummary: Interactive API reference with a sandbox.\n", encoding="utf-8"
    )
    docs_root = tmp_path / "docs"
    specs_dir = tmp_path / "templates" / "specs"

    manifest = mod.write_and_render(
        [_good_template()],
        specs_dir=specs_dir, docs_root=docs_root, modules_dir=modules_dir,
        schema=_schema(), allowed_tags=_ALLOWED,
    )
    assert manifest[0]["status"] == "ok"
    assert (specs_dir / "sdk-reference.spec.yml").exists()
    doc_path = tmp_path / "docs" / "reference" / "sdk-reference.md"
    assert doc_path.exists()
    text = doc_path.read_text(encoding="utf-8")
    assert '--8<-- "sdk/create-charge.md"' in text
    assert "Interactive API reference with a sandbox." in text


def test_load_module_catalog_skips_inactive(tmp_path: Path) -> None:
    (tmp_path / "a.yml").write_text("id: a\ntitle: A\nsummary: s\nstatus: active\nintents: [configure]\n", encoding="utf-8")
    (tmp_path / "b.yml").write_text("id: b\ntitle: B\nsummary: s\nstatus: deprecated\n", encoding="utf-8")
    catalog = mod.load_module_catalog(tmp_path)
    ids = {m["id"] for m in catalog}
    assert ids == {"a"}

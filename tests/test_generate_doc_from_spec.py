"""Tests for the SSOT spec -> document skeleton renderer."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts import generate_doc_from_spec as mod
from scripts import validate_frontmatter as vfm

_ALLOWED = {"Reference", "How-To", "Concept", "Tutorial", "Troubleshooting"}

_SPEC = {
    "doc_type": "sdk-reference",
    "output_path": "docs/reference/sdk-reference.md",
    "frontmatter": {
        "title": "Payments SDK reference",
        "description": "Reference for the Payments SDK: install, initialize, create charges, handle errors.",
        "content_type": "reference",
        "product": "both",
        "tags": ["Reference"],
    },
    "intro": "The Payments SDK provides typed client methods for charges and refunds.",
    "sections": [
        {
            "heading": "Create a charge",
            "slots": [
                {"type": "prose", "text": "Create a charge with an amount in cents."},
                {"type": "snippet", "ref": "sdk/create-charge"},
                {"type": "variable", "ref": "product_name"},
            ],
        }
    ],
}


def _schema() -> dict:
    return vfm.load_schema("docs-schema.yml")


def test_render_valid_spec(tmp_path: Path) -> None:
    rendered, errors = mod.build_document(
        _SPEC, modules_dir=tmp_path, schema=_schema(), allowed_tags=_ALLOWED
    )
    assert errors == []
    assert rendered.startswith("---\n")
    assert "# Payments SDK reference" in rendered
    assert '--8<-- "sdk/create-charge.md"' in rendered   # snippet SSOT include
    assert "{{ product_name }}" in rendered               # variable macro preserved


def test_bad_tag_is_rejected() -> None:
    spec = {**_SPEC, "frontmatter": {**_SPEC["frontmatter"], "tags": ["Reference", "API"]}}
    errors = mod.validate_frontmatter_dict(spec["frontmatter"], _schema(), _ALLOWED)
    assert any("'API' is not in the allowed set" in e for e in errors)


def test_short_description_is_rejected() -> None:
    spec_fm = {**_SPEC["frontmatter"], "description": "too short"}
    errors = mod.validate_frontmatter_dict(spec_fm, _schema(), _ALLOWED)
    assert any("description" in e for e in errors)


def test_invalid_content_type_is_rejected() -> None:
    spec_fm = {**_SPEC["frontmatter"], "content_type": "manual"}
    errors = mod.validate_frontmatter_dict(spec_fm, _schema(), _ALLOWED)
    assert any("content_type" in e for e in errors)


def test_unknown_module_slot_raises(tmp_path: Path) -> None:
    spec = {
        **_SPEC,
        "sections": [{"heading": "X", "slots": [{"type": "module", "ref": "does-not-exist"}]}],
    }
    with pytest.raises(mod.SpecError):
        mod.render_spec(spec, tmp_path)


def test_module_slot_inlines_summary(tmp_path: Path) -> None:
    (tmp_path / "auto-x-1.yml").write_text(
        "id: auto-x-1\nsummary: Configure webhooks with HMAC signatures.\n", encoding="utf-8"
    )
    spec = {**_SPEC, "sections": [{"heading": "Webhooks", "slots": [{"type": "module", "ref": "auto-x-1"}]}]}
    rendered = mod.render_spec(spec, tmp_path)
    assert "<!-- ssot:module auto-x-1 -->" in rendered
    assert "Configure webhooks with HMAC signatures." in rendered


def test_geo_contract_flags_long_first_paragraph() -> None:
    long_intro = " ".join(["word"] * 80)
    spec = {**_SPEC, "intro": long_intro, "geo_contract": {"first_paragraph_max_words": 60}}
    rendered = mod.render_spec(spec, Path("."))
    warnings = mod.check_geo_contract(spec, rendered)
    assert any("first paragraph" in w for w in warnings)


def test_load_allowed_tags_from_mkdocs() -> None:
    tags = mod.load_allowed_tags(Path("mkdocs.yml"))
    assert "Reference" in tags
    assert "API" not in tags  # confirms the whitelist is real

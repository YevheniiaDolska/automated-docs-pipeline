"""Tests for scripts/validate_frontmatter.py."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.validate_frontmatter import (
    _is_type,
    _normalize_string_candidate,
    _type_matches,
    _validate_node,
    extract_frontmatter,
    load_schema,
    validate_file,
)


# ---------------------------------------------------------------------------
# extract_frontmatter
# ---------------------------------------------------------------------------


class TestExtractFrontmatter:
    """Tests for extract_frontmatter."""

    def test_extract_valid_frontmatter(self) -> None:
        """Extracts well-formed YAML frontmatter from markdown text."""
        text = '---\ntitle: "Hello"\ndescription: "World"\n---\n# Body'
        result = extract_frontmatter(text)

        assert result is not None
        assert result["title"] == "Hello"
        assert result["description"] == "World"

    def test_returns_none_when_no_frontmatter(self) -> None:
        """Returns None when text does not start with ---."""
        assert extract_frontmatter("# No frontmatter") is None

    def test_returns_none_when_missing_closing_delimiter(self) -> None:
        """Returns None when closing --- is absent."""
        assert extract_frontmatter("---\ntitle: Hello\n") is None

    def test_returns_none_for_invalid_yaml(self) -> None:
        """Returns None when YAML between delimiters is malformed."""
        assert extract_frontmatter("---\n: :\n  bad:\n---\nbody") is None

    def test_returns_none_for_non_dict_yaml(self) -> None:
        """Returns None when YAML parses to a non-dict (e.g. a list)."""
        assert extract_frontmatter("---\n- item1\n- item2\n---\nbody") is None

    def test_handles_date_values(self) -> None:
        """YAML dates are parsed as date objects; frontmatter still loads."""
        text = '---\ntitle: "Test"\nlast_reviewed: 2026-01-15\n---\nbody'
        result = extract_frontmatter(text)

        assert result is not None
        assert "last_reviewed" in result


# ---------------------------------------------------------------------------
# _normalize_string_candidate
# ---------------------------------------------------------------------------


class TestNormalizeStringCandidate:
    """Tests for _normalize_string_candidate."""

    def test_normalizes_plain_string(self) -> None:
        """Plain strings pass through unchanged."""
        assert _normalize_string_candidate("hello") == "hello"

    def test_normalizes_date_to_iso(self) -> None:
        """Dates are converted to ISO-8601 date strings."""
        from datetime import date

        assert _normalize_string_candidate(date(2026, 3, 1)) == "2026-03-01"

    def test_normalizes_datetime_to_iso_date(self) -> None:
        """Datetimes are truncated to the date portion."""
        from datetime import datetime

        result = _normalize_string_candidate(datetime(2026, 3, 1, 12, 30))
        assert result == "2026-03-01"

    def test_normalizes_integer_to_string(self) -> None:
        """Non-string scalars are str()-ified."""
        assert _normalize_string_candidate(42) == "42"


# ---------------------------------------------------------------------------
# _is_type
# ---------------------------------------------------------------------------


class TestIsType:
    """Tests for _is_type."""

    def test_string_type(self) -> None:
        assert _is_type("hello", "string") is True
        assert _is_type(123, "string") is False

    def test_string_accepts_date(self) -> None:
        """Dates are treated as strings in frontmatter context."""
        from datetime import date

        assert _is_type(date(2026, 1, 1), "string") is True

    def test_integer_type(self) -> None:
        assert _is_type(42, "integer") is True
        assert _is_type(3.14, "integer") is False
        assert _is_type(True, "integer") is False

    def test_number_type(self) -> None:
        assert _is_type(3.14, "number") is True
        assert _is_type(42, "number") is True
        assert _is_type(True, "number") is False

    def test_boolean_type(self) -> None:
        assert _is_type(True, "boolean") is True
        assert _is_type(1, "boolean") is False

    def test_array_type(self) -> None:
        assert _is_type([1, 2], "array") is True
        assert _is_type("list", "array") is False

    def test_object_type(self) -> None:
        assert _is_type({"key": "val"}, "object") is True
        assert _is_type([], "object") is False

    def test_null_type(self) -> None:
        assert _is_type(None, "null") is True
        assert _is_type("", "null") is False

    def test_unknown_type_returns_true(self) -> None:
        """Unknown type names are permissive."""
        assert _is_type("anything", "custom_type") is True


# ---------------------------------------------------------------------------
# _type_matches
# ---------------------------------------------------------------------------


class TestTypeMatches:
    """Tests for _type_matches."""

    def test_single_type(self) -> None:
        assert _type_matches("hello", "string") is True

    def test_union_type_list(self) -> None:
        assert _type_matches("hello", ["string", "null"]) is True
        assert _type_matches(None, ["string", "null"]) is True
        assert _type_matches(42, ["string", "null"]) is False

    def test_non_string_type_returns_true(self) -> None:
        """Non-string/non-list type is permissive."""
        assert _type_matches("any", 42) is True


# ---------------------------------------------------------------------------
# _validate_node
# ---------------------------------------------------------------------------


class TestValidateNode:
    """Tests for _validate_node."""

    def test_type_mismatch(self) -> None:
        errors = _validate_node(42, {"type": "string"}, "root")
        assert len(errors) == 1
        assert "must be of type" in errors[0]

    def test_enum_violation(self) -> None:
        errors = _validate_node("bad", {"type": "string", "enum": ["a", "b"]}, "root")
        assert len(errors) == 1
        assert "invalid value" in errors[0]

    def test_enum_passes(self) -> None:
        errors = _validate_node("a", {"type": "string", "enum": ["a", "b"]}, "root")
        assert errors == []

    def test_min_length(self) -> None:
        errors = _validate_node("ab", {"type": "string", "minLength": 5}, "root")
        assert len(errors) == 1
        assert "too short" in errors[0]

    def test_max_length(self) -> None:
        errors = _validate_node("a" * 100, {"type": "string", "maxLength": 10}, "root")
        assert len(errors) == 1
        assert "too long" in errors[0]

    def test_pattern_violation(self) -> None:
        errors = _validate_node("123", {"type": "string", "pattern": "^[a-z]+$"}, "root")
        assert len(errors) == 1
        assert "does not match pattern" in errors[0]

    def test_pattern_passes(self) -> None:
        errors = _validate_node("abc", {"type": "string", "pattern": "^[a-z]+$"}, "root")
        assert errors == []

    def test_array_min_items(self) -> None:
        errors = _validate_node([], {"type": "array", "minItems": 1}, "root")
        assert len(errors) == 1
        assert "too few items" in errors[0]

    def test_array_max_items(self) -> None:
        errors = _validate_node([1, 2, 3], {"type": "array", "maxItems": 2}, "root")
        assert len(errors) == 1
        assert "too many items" in errors[0]

    def test_array_unique_items(self) -> None:
        errors = _validate_node(
            ["a", "b", "a"],
            {"type": "array", "uniqueItems": True},
            "root",
        )
        assert len(errors) == 1
        assert "unique items" in errors[0]

    def test_array_item_schema(self) -> None:
        errors = _validate_node(
            ["ok", 42],
            {"type": "array", "items": {"type": "string"}},
            "root",
        )
        assert len(errors) == 1
        assert "[1]" in errors[0]

    def test_object_required_fields(self) -> None:
        errors = _validate_node(
            {"a": 1},
            {"type": "object", "required": ["a", "b"]},
            "root",
        )
        assert len(errors) == 1
        assert "missing required field" in errors[0]

    def test_object_properties_validated(self) -> None:
        schema: dict[str, Any] = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "maxLength": 3},
            },
        }
        errors = _validate_node({"name": "toolong"}, schema, "root")
        assert len(errors) == 1
        assert "too long" in errors[0]


# ---------------------------------------------------------------------------
# validate_file
# ---------------------------------------------------------------------------


class TestValidateFile:
    """Tests for validate_file."""

    def test_valid_file_produces_no_errors(self, tmp_path: Path) -> None:
        """A well-formed file passes validation."""
        md = tmp_path / "good.md"
        md.write_text(
            '---\ntitle: "Good Title"\ndescription: "A valid description."\ncontent_type: reference\n---\n# Good\n',
            encoding="utf-8",
        )
        schema: dict[str, Any] = {
            "required": ["title"],
            "properties": {
                "title": {"type": "string", "maxLength": 70},
            },
        }
        errors = validate_file(md, schema)
        assert errors == []

    def test_missing_frontmatter_reports_error(self, tmp_path: Path) -> None:
        """A file without frontmatter triggers a single error."""
        md = tmp_path / "bad.md"
        md.write_text("# No frontmatter\n", encoding="utf-8")
        errors = validate_file(md, {"required": ["title"]})
        assert len(errors) == 1
        assert "missing or invalid frontmatter" in errors[0]

    def test_missing_required_field(self, tmp_path: Path) -> None:
        """Missing required field is reported."""
        md = tmp_path / "missing.md"
        md.write_text("---\ntitle: Hello\n---\n# Body\n", encoding="utf-8")
        errors = validate_file(md, {"required": ["title", "description"]})
        assert any("missing required field 'description'" in e for e in errors)

    def test_property_validation(self, tmp_path: Path) -> None:
        """Property rules are applied to present fields."""
        md = tmp_path / "prop.md"
        md.write_text(
            "---\ntitle: X\n---\n# Body\n",
            encoding="utf-8",
        )
        schema: dict[str, Any] = {
            "required": [],
            "properties": {"title": {"type": "string", "minLength": 10}},
        }
        errors = validate_file(md, schema)
        assert any("too short" in e for e in errors)


# ---------------------------------------------------------------------------
# load_schema
# ---------------------------------------------------------------------------


class TestLoadSchema:
    """Tests for load_schema."""

    def test_loads_valid_schema(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Loads a valid YAML schema file."""
        schema_file = tmp_path / "schema.yml"
        schema_file.write_text(
            yaml.dump({"required": ["title"], "properties": {"title": {"type": "string"}}}),
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        result = load_schema("schema.yml")
        assert "required" in result

    def test_raises_on_non_dict(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Raises ValueError when schema YAML is not a mapping."""
        schema_file = tmp_path / "bad.yml"
        schema_file.write_text("- item1\n- item2\n", encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ValueError, match="must be a mapping"):
            load_schema("bad.yml")

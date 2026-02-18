#!/usr/bin/env python3
"""Validate Markdown frontmatter against docs-schema.yml."""

from __future__ import annotations

import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml


def load_schema(schema_path: str = "docs-schema.yml") -> dict[str, Any]:
    """Load JSON Schema (YAML format) used for frontmatter validation."""
    schema = yaml.safe_load(Path(schema_path).read_text(encoding="utf-8"))
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a mapping.")
    return schema


def extract_frontmatter(text: str) -> dict[str, Any] | None:
    """Extract frontmatter mapping from Markdown content."""
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        loaded = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
    return loaded if isinstance(loaded, dict) else None


def _normalize_string_candidate(value: Any) -> str:
    """Normalize scalar values that should be treated like strings."""
    if isinstance(value, str):
        return value
    if isinstance(value, (date, datetime)):
        return value.isoformat()[:10]
    return str(value)


def _is_type(value: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str) or isinstance(value, (date, datetime))
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "null":
        return value is None
    return True


def _type_matches(value: Any, expected_type: Any) -> bool:
    if isinstance(expected_type, str):
        return _is_type(value, expected_type)
    if isinstance(expected_type, list):
        return any(isinstance(item, str) and _is_type(value, item) for item in expected_type)
    return True


def _validate_node(value: Any, schema: dict[str, Any], location: str) -> list[str]:
    errors: list[str] = []

    expected_type = schema.get("type")
    if expected_type is not None and not _type_matches(value, expected_type):
        errors.append(f"{location}: must be of type '{expected_type}'")
        return errors

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{location}: invalid value '{value}'. Allowed: {schema['enum']}")

    if _type_matches(value, "string"):
        normalized = _normalize_string_candidate(value)
        min_length = schema.get("minLength")
        max_length = schema.get("maxLength")
        pattern = schema.get("pattern")
        if isinstance(min_length, int) and len(normalized) < min_length:
            errors.append(f"{location}: too short ({len(normalized)} < {min_length})")
        if isinstance(max_length, int) and len(normalized) > max_length:
            errors.append(f"{location}: too long ({len(normalized)} > {max_length})")
        if isinstance(pattern, str) and not re.match(pattern, normalized):
            errors.append(f"{location}: does not match pattern '{pattern}'")

    if _type_matches(value, "array"):
        if not isinstance(value, list):
            return errors
        min_items = schema.get("minItems")
        max_items = schema.get("maxItems")
        if isinstance(min_items, int) and len(value) < min_items:
            errors.append(f"{location}: too few items ({len(value)} < {min_items})")
        if isinstance(max_items, int) and len(value) > max_items:
            errors.append(f"{location}: too many items ({len(value)} > {max_items})")
        if schema.get("uniqueItems") is True:
            normalized_items = [str(item) for item in value]
            if len(normalized_items) != len(set(normalized_items)):
                errors.append(f"{location}: must contain unique items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(_validate_node(item, item_schema, f"{location}[{index}]"))

    if _type_matches(value, "object"):
        if not isinstance(value, dict):
            return errors
        required = schema.get("required", [])
        if isinstance(required, list):
            for field in required:
                if field not in value:
                    errors.append(f"{location}.{field}: missing required field")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for field, field_schema in properties.items():
                if field in value and isinstance(field_schema, dict):
                    errors.extend(_validate_node(value[field], field_schema, f"{location}.{field}"))

    return errors


def validate_file(filepath: Path, schema: dict[str, Any]) -> list[str]:
    """Validate one Markdown file against schema."""
    text = filepath.read_text(encoding="utf-8")
    frontmatter = extract_frontmatter(text)
    if frontmatter is None:
        return [f"{filepath}: missing or invalid frontmatter"]

    errors: list[str] = []
    required_fields = schema.get("required", [])
    if isinstance(required_fields, list):
        for field in required_fields:
            if field not in frontmatter:
                errors.append(f"{filepath}: missing required field '{field}'")

    properties = schema.get("properties", {})
    if isinstance(properties, dict):
        for field, rules in properties.items():
            if field in frontmatter and isinstance(rules, dict):
                field_errors = _validate_node(frontmatter[field], rules, f"{filepath}:{field}")
                errors.extend(field_errors)

    return errors


def main() -> None:
    schema = load_schema()
    all_errors: list[str] = []

    docs_path = Path("docs")
    if not docs_path.exists():
        print("Error: docs/ directory not found", file=sys.stderr)
        sys.exit(1)

    for md_file in sorted(docs_path.rglob("*.md")):
        if md_file.name.startswith("_"):
            continue
        all_errors.extend(validate_file(md_file, schema))

    if all_errors:
        print(f"\nFrontmatter validation: {len(all_errors)} error(s)\n", file=sys.stderr)
        for error in all_errors:
            print(f"  {error}", file=sys.stderr)
        sys.exit(1)

    print("Frontmatter validation: all files pass")


if __name__ == "__main__":
    main()

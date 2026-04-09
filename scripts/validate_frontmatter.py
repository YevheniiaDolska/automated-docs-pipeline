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
    schema_file = Path(schema_path)
    if not schema_file.exists():
        # In pilot/empty repos schema may be absent; keep validator non-blocking.
        return {"type": "object", "properties": {}, "required": []}
    schema = yaml.safe_load(schema_file.read_text(encoding="utf-8"))
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

    errors.extend(_validate_lifecycle_fields(frontmatter, filepath))

    return errors


def _normalize_lifecycle_status(frontmatter: dict[str, Any]) -> str:
    """Resolve lifecycle status from current and legacy frontmatter fields."""
    status = frontmatter.get("status")
    if isinstance(status, str) and status.strip():
        return status.strip().lower()

    maturity = frontmatter.get("maturity")
    if isinstance(maturity, str) and maturity.strip():
        mapped = {
            "ga": "active",
            "removed": "removed",
            "deprecated": "deprecated",
            "preview": "draft",
        }
        return mapped.get(maturity.strip().lower(), maturity.strip().lower())

    return "active"


def _validate_lifecycle_fields(frontmatter: dict[str, Any], filepath: Path) -> list[str]:
    """Validate lifecycle requirements for deprecated/removed docs."""
    errors: list[str] = []
    status = _normalize_lifecycle_status(frontmatter)

    if status not in {"deprecated", "removed", "archived"}:
        return errors

    required = ("deprecated_since", "removal_date", "replacement_url")
    for field in required:
        value = frontmatter.get(field)
        normalized = _normalize_string_candidate(value).strip() if value is not None else ""
        if not normalized:
            errors.append(f"{filepath}: {field} is required when status is '{status}'")

    for field in ("deprecated_since", "removal_date"):
        value = frontmatter.get(field)
        normalized = _normalize_string_candidate(value).strip() if value is not None else ""
        if normalized and not re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", normalized):
            errors.append(f"{filepath}: {field} must match YYYY-MM-DD")

    replacement_url = frontmatter.get("replacement_url")
    if replacement_url is not None:
        normalized = _normalize_string_candidate(replacement_url).strip()
        if not (normalized.startswith("/") or normalized.startswith("http://") or normalized.startswith("https://")):
            errors.append(f"{filepath}: replacement_url must start with '/' or 'http(s)://'")

    if status in {"removed", "archived"} and frontmatter.get("noindex") is not True:
        errors.append(f"{filepath}: noindex: true is required when status is '{status}'")

    return errors


def _validate_i18n_fields(
    frontmatter: dict[str, Any],
    filepath: Path,
    docs_path: Path,
) -> list[str]:
    """Validate i18n-specific frontmatter fields.

    Checks:
    - language matches the locale folder (if folder-based layout)
    - translation_of target file exists
    - source_hash is present when translation_of is set
    """
    errors: list[str] = []

    language = frontmatter.get("language")
    translation_of = frontmatter.get("translation_of")
    source_hash = frontmatter.get("source_hash")

    # Check language matches locale folder
    if language:
        try:
            rel = filepath.relative_to(docs_path)
            parts = rel.parts
            if parts and re.match(r"^[a-z]{2,3}$", parts[0]):
                folder_locale = parts[0]
                if language != folder_locale:
                    errors.append(
                        f"{filepath}: language '{language}' does not match "
                        f"folder locale '{folder_locale}'"
                    )
        except ValueError:
            errors.append(f"{filepath}: invalid locale path structure")

    # Check translation_of target exists
    if translation_of:
        target = docs_path / translation_of
        if not target.exists():
            errors.append(
                f"{filepath}: translation_of target does not exist: {translation_of}"
            )
        # source_hash should be present for translations
        if not source_hash:
            errors.append(
                f"{filepath}: source_hash is required when translation_of is set"
            )

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

        # Validate i18n fields
        text = md_file.read_text(encoding="utf-8")
        fm = extract_frontmatter(text)
        if fm is not None:
            all_errors.extend(_validate_i18n_fields(fm, md_file, docs_path))

    if all_errors:
        print(f"\nFrontmatter validation: {len(all_errors)} error(s)\n", file=sys.stderr)
        for error in all_errors:
            print(f"  {error}", file=sys.stderr)
        sys.exit(1)

    print("Frontmatter validation: all files pass")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Validate frontmatter in all Markdown files against docs-schema.yml."""

import yaml
import sys
import re
from pathlib import Path

def load_schema(schema_path="docs-schema.yml"):
    return yaml.safe_load(Path(schema_path).read_text())

def extract_frontmatter(text):
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        return yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None

def validate_file(filepath, schema):
    errors = []
    text = filepath.read_text(encoding="utf-8")
    fm = extract_frontmatter(text)

    if fm is None:
        errors.append(f"{filepath}: missing or invalid frontmatter")
        return errors

    for field, rules in schema.get("required_fields", {}).items():
        if field not in fm:
            errors.append(f"{filepath}: missing required field '{field}'")
            continue

        value = fm[field]
        ftype = rules.get("type")

        if ftype == "string":
            if not isinstance(value, str):
                errors.append(f"{filepath}: '{field}' must be a string")
            else:
                if "min_length" in rules and len(value) < rules["min_length"]:
                    errors.append(f"{filepath}: '{field}' too short ({len(value)} < {rules['min_length']})")
                if "max_length" in rules and len(value) > rules["max_length"]:
                    errors.append(f"{filepath}: '{field}' too long ({len(value)} > {rules['max_length']})")

        elif ftype == "enum":
            if value not in rules.get("values", []):
                errors.append(f"{filepath}: invalid {field}='{value}'. Allowed: {rules['values']}")

    for field, rules in schema.get("optional_fields", {}).items():
        if field not in fm:
            continue
        value = fm[field]
        ftype = rules.get("type")

        if ftype == "enum" and value not in rules.get("values", []):
            errors.append(f"{filepath}: invalid {field}='{value}'. Allowed: {rules['values']}")
        elif ftype == "list":
            if not isinstance(value, list):
                errors.append(f"{filepath}: '{field}' must be a list")
            elif "max_items" in rules and len(value) > rules["max_items"]:
                errors.append(f"{filepath}: '{field}' has too many items ({len(value)} > {rules['max_items']})")
        elif ftype == "string" and "pattern" in rules:
            if not re.match(rules["pattern"], str(value)):
                errors.append(f"{filepath}: '{field}' doesn't match pattern {rules['pattern']}")

    return errors

def main():
    schema = load_schema()
    all_errors = []

    docs_path = Path("docs")
    if not docs_path.exists():
        print("Error: docs/ directory not found", file=sys.stderr)
        sys.exit(1)

    for md_file in sorted(docs_path.rglob("*.md")):
        if md_file.name.startswith("_"):
            continue
        all_errors.extend(validate_file(md_file, schema))

    if all_errors:
        print(f"\n❌ Frontmatter validation: {len(all_errors)} error(s)\n", file=sys.stderr)
        for e in all_errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"✅ Frontmatter validation: all files pass")

if __name__ == "__main__":
    main()

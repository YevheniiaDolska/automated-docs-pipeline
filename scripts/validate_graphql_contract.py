#!/usr/bin/env python3
"""Validate GraphQL schema contract file (SDL) with semantic checks."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def _extract_blocks(schema_text: str, kind: str) -> list[tuple[str, str]]:
    pattern = re.compile(rf"\b{re.escape(kind)}\s+([A-Za-z_][A-Za-z0-9_]*)[^{{]*\{{", re.MULTILINE)
    blocks: list[tuple[str, str]] = []
    for match in pattern.finditer(schema_text):
        name = match.group(1)
        start = match.end() - 1
        depth = 0
        end = start
        while end < len(schema_text):
            ch = schema_text[end]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    break
            end += 1
        body = schema_text[start + 1 : end] if end < len(schema_text) else ""
        blocks.append((name, body))
    return blocks


def _extract_schema_root_types(schema_text: str) -> dict[str, str]:
    match = re.search(r"\bschema\s*\{(.*?)\}", schema_text, re.DOTALL)
    if not match:
        return {}
    body = match.group(1)
    roots: dict[str, str] = {}
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        roots[key.strip()] = value.strip()
    return roots


def validate_schema(schema_text: str) -> list[str]:
    errors: list[str] = []
    if not schema_text.strip():
        return ["GraphQL schema is empty."]

    if "type Query" not in schema_text and "schema" not in schema_text:
        errors.append("GraphQL schema must contain `type Query` or explicit `schema { ... }` block.")

    if schema_text.count("{") != schema_text.count("}"):
        errors.append("GraphQL schema appears malformed: unbalanced braces.")

    if schema_text.count("(") != schema_text.count(")"):
        errors.append("GraphQL schema appears malformed: unbalanced parentheses.")

    seen_types: set[str] = set()
    for kind in ("type", "input", "interface", "enum", "union", "scalar"):
        for name, body in _extract_blocks(schema_text, kind):
            key = name.lower()
            if key in seen_types:
                errors.append(f"Duplicate type declaration: {name}")
            seen_types.add(key)

            if kind in {"type", "input", "interface"}:
                seen_fields: set[str] = set()
                for raw in body.splitlines():
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    field_name = line.split("(", 1)[0].split(":", 1)[0].strip()
                    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", field_name):
                        continue
                    normalized = field_name.lower()
                    if normalized in seen_fields:
                        errors.append(f"{kind} {name}: duplicate field `{field_name}`")
                    seen_fields.add(normalized)

    root_types = _extract_schema_root_types(schema_text)
    for root_key, root_name in root_types.items():
        if root_name and root_name.lower() not in seen_types:
            errors.append(f"schema root `{root_key}: {root_name}` references missing type `{root_name}`")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate GraphQL SDL contract")
    parser.add_argument("schema", help="Path to .graphql/.gql schema")
    args = parser.parse_args()

    schema_path = Path(args.schema)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    errors = validate_schema(schema_path.read_text(encoding="utf-8"))
    if errors:
        for err in errors:
            print(f"[graphql-contract] {err}")
        return 1

    print(f"[graphql-contract] ok: {schema_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

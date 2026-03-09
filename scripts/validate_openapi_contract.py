#!/usr/bin/env python3
"""Validate baseline API-first quality contract for an OpenAPI document."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml


REQUIRED_TOP_LEVEL = ["openapi", "info", "paths", "components"]
REQUIRED_HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _has_external_refs(spec_path: Path) -> bool:
    raw = spec_path.read_text(encoding="utf-8")
    # Split-file structure should reference external files.
    return "$ref: ./" in raw or "$ref: ../" in raw


def _schema_modeling_signals(spec_path: Path) -> tuple[bool, bool]:
    root = spec_path.parent
    has_all_of = False
    has_one_of = False
    for file in root.rglob("*.y*ml"):
        raw = file.read_text(encoding="utf-8")
        has_all_of = has_all_of or ("allOf:" in raw)
        has_one_of = has_one_of or ("oneOf:" in raw)
    return (has_all_of, has_one_of)


def validate(spec: dict[str, Any], spec_path: Path) -> list[str]:
    errors: list[str] = []

    for key in REQUIRED_TOP_LEVEL:
        if key not in spec:
            errors.append(f"Missing top-level key: {key}")

    info = spec.get("info", {})
    if not info.get("title"):
        errors.append("info.title is required")
    if not info.get("description"):
        errors.append("info.description is required")

    components = spec.get("components", {})
    if "securitySchemes" not in components:
        errors.append("components.securitySchemes is required")
    if "responses" not in components:
        errors.append("components.responses is required")
    if "schemas" not in components:
        errors.append("components.schemas is required")

    paths = spec.get("paths", {})
    if not paths:
        errors.append("paths must not be empty")

    for path_name, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in REQUIRED_HTTP_METHODS:
                continue
            if not isinstance(operation, dict):
                errors.append(f"{method.upper()} {path_name}: operation object is invalid")
                continue

            if not operation.get("operationId"):
                errors.append(f"{method.upper()} {path_name}: missing operationId")
            if not operation.get("tags"):
                errors.append(f"{method.upper()} {path_name}: missing tags")
            if not operation.get("summary"):
                errors.append(f"{method.upper()} {path_name}: missing summary")
            if not operation.get("description"):
                errors.append(f"{method.upper()} {path_name}: missing description")

            responses = operation.get("responses", {})
            if not responses:
                errors.append(f"{method.upper()} {path_name}: missing responses")
                continue

            has_success = any(code.startswith(("2", "3")) for code in responses.keys())
            if not has_success:
                errors.append(f"{method.upper()} {path_name}: missing success response")

    if not _has_external_refs(spec_path):
        errors.append("Spec should use split-file references ($ref to external files)")

    has_all_of, has_one_of = _schema_modeling_signals(spec_path)
    if not has_all_of:
        errors.append("Spec should include allOf for inheritance/reuse modeling")
    if not has_one_of:
        errors.append("Spec should include oneOf for polymorphic modeling")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/validate_openapi_contract.py <spec-path>")
        return 2

    spec_path = Path(sys.argv[1])
    if not spec_path.exists():
        print(f"Spec file does not exist: {spec_path}")
        return 2

    spec = load_yaml(spec_path)
    errors = validate(spec, spec_path)

    if errors:
        print("OpenAPI contract validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("OpenAPI contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Apply manual OpenAPI overrides to root spec and split tree files."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping in {path}")
    return data


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=False)


def deep_merge(base: Any, patch: Any) -> Any:
    """Recursively merge mappings while preserving unknown keys (including x-*)."""
    if isinstance(base, dict) and isinstance(patch, dict):
        merged = dict(base)
        for key, value in patch.items():
            if key in merged:
                merged[key] = deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged
    return patch


def apply_overrides(spec_path: Path, spec_tree: Path | None, overrides_path: Path) -> tuple[int, int]:
    overrides = _read_yaml(overrides_path)

    root_patch = overrides.get("spec") or overrides.get("root") or {}
    if root_patch and not isinstance(root_patch, dict):
        raise ValueError("overrides.spec (or overrides.root) must be a mapping")

    files_patch = overrides.get("files", {})
    if files_patch and not isinstance(files_patch, dict):
        raise ValueError("overrides.files must be a mapping of relative path -> patch mapping")

    root_applied = 0
    file_applied = 0

    if root_patch:
        root_spec = _read_yaml(spec_path)
        merged = deep_merge(root_spec, root_patch)
        _write_yaml(spec_path, merged)
        root_applied = 1

    if files_patch:
        if spec_tree is None:
            raise ValueError("overrides.files provided, but --spec-tree is not set")
        for rel_path, patch in files_patch.items():
            if not isinstance(rel_path, str) or not rel_path.strip():
                raise ValueError("overrides.files keys must be non-empty strings")
            if not isinstance(patch, dict):
                raise ValueError(f"overrides.files[{rel_path!r}] must be a mapping")
            target = (spec_tree / rel_path).resolve()
            # Prevent escaping outside of split tree.
            if spec_tree.resolve() not in target.parents and target != spec_tree.resolve():
                raise ValueError(f"Invalid overrides.files path outside spec tree: {rel_path}")
            current = _read_yaml(target) if target.exists() else {}
            merged = deep_merge(current, patch)
            _write_yaml(target, merged)
            file_applied += 1

    return root_applied, file_applied


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply manual overrides to OpenAPI artifacts")
    parser.add_argument("--spec", required=True, help="Root OpenAPI spec path")
    parser.add_argument("--overrides", required=True, help="YAML overrides file")
    parser.add_argument("--spec-tree", default=None, help="Split OpenAPI tree root path")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"Spec file does not exist: {spec_path}")
        return 2

    overrides_path = Path(args.overrides)
    if not overrides_path.exists():
        print(f"Overrides file does not exist: {overrides_path}")
        return 2

    spec_tree = Path(args.spec_tree) if args.spec_tree else None
    if spec_tree is not None and not spec_tree.exists():
        print(f"Spec tree path does not exist: {spec_tree}")
        return 2

    try:
        root_applied, file_applied = apply_overrides(spec_path, spec_tree, overrides_path)
    except Exception as error:  # noqa: BLE001
        print(f"Failed to apply overrides: {error}")
        return 1

    print(f"[ok] OpenAPI overrides applied: root={root_applied}, files={file_applied}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

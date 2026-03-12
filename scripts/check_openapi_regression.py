#!/usr/bin/env python3
"""Check OpenAPI regression against a saved snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _normalized_yaml_bytes(path: Path) -> bytes:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    normalized = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return normalized.encode("utf-8")


def collect_snapshot(spec_path: Path, spec_tree: Path | None) -> dict[str, Any]:
    files: dict[str, str] = {}

    files[str(spec_path.as_posix())] = _sha256_bytes(_normalized_yaml_bytes(spec_path))
    if spec_tree is not None:
        for item in sorted(spec_tree.rglob("*.y*ml")):
            files[str(item.as_posix())] = _sha256_bytes(_normalized_yaml_bytes(item))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "spec_path": str(spec_path.as_posix()),
        "spec_tree": str(spec_tree.as_posix()) if spec_tree is not None else None,
        "files": files,
    }


def compare_snapshots(current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, list[str]]:
    current_files = current.get("files", {})
    baseline_files = baseline.get("files", {})
    if not isinstance(current_files, dict) or not isinstance(baseline_files, dict):
        raise ValueError("Snapshot format is invalid: files must be mapping")

    added = sorted(path for path in current_files.keys() if path not in baseline_files)
    removed = sorted(path for path in baseline_files.keys() if path not in current_files)
    changed = sorted(
        path
        for path in current_files.keys()
        if path in baseline_files and current_files[path] != baseline_files[path]
    )
    return {"added": added, "removed": removed, "changed": changed}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check OpenAPI artifacts against regression snapshot")
    parser.add_argument("--spec", required=True, help="Root OpenAPI spec path")
    parser.add_argument("--snapshot", required=True, help="Snapshot JSON path")
    parser.add_argument("--spec-tree", default=None, help="Split OpenAPI tree path")
    parser.add_argument("--update", action="store_true", help="Write/refresh snapshot and exit")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"Spec file does not exist: {spec_path}")
        return 2

    spec_tree = Path(args.spec_tree) if args.spec_tree else None
    if spec_tree is not None and not spec_tree.exists():
        print(f"Spec tree path does not exist: {spec_tree}")
        return 2

    snapshot_path = Path(args.snapshot)
    current = collect_snapshot(spec_path, spec_tree)

    if args.update:
        _write_json(snapshot_path, current)
        print(f"[ok] OpenAPI regression snapshot updated: {snapshot_path}")
        return 0

    if not snapshot_path.exists():
        print(f"OpenAPI regression snapshot does not exist: {snapshot_path}")
        print("Run with --update to create baseline snapshot.")
        return 2

    baseline = json.loads(snapshot_path.read_text(encoding="utf-8"))
    diff = compare_snapshots(current, baseline)
    if any(diff.values()):
        print("OpenAPI regression check failed:")
        for key in ("added", "removed", "changed"):
            entries = diff[key]
            if entries:
                print(f"- {key}:")
                for path in entries:
                    print(f"  - {path}")
        return 1

    print("OpenAPI regression check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

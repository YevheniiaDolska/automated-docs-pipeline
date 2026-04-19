#!/usr/bin/env python3
"""Generic regression snapshot checker for API protocol contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


TEXT_EXTENSIONS = {".yaml", ".yml", ".json", ".graphql", ".gql", ".proto"}


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _normalized_bytes(path: Path) -> bytes:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
        normalized = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return normalized.encode("utf-8")
    if suffix == ".json":
        data = json.loads(text)
        normalized = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return normalized.encode("utf-8")
    return text.encode("utf-8")


def _iter_files(paths: list[Path], *, exclude_paths: set[Path] | None = None) -> list[Path]:
    excluded = {p.resolve() for p in (exclude_paths or set())}
    files: list[Path] = []
    for item in paths:
        if item.is_file() and item.suffix.lower() in TEXT_EXTENSIONS:
            resolved = item.resolve()
            if resolved not in excluded:
                files.append(item)
        elif item.is_dir():
            files.extend(
                sorted(
                    candidate
                    for candidate in item.rglob("*")
                    if candidate.is_file()
                    and candidate.suffix.lower() in TEXT_EXTENSIONS
                    and candidate.resolve() not in excluded
                )
            )
    return files


def collect_snapshot(protocol: str, inputs: list[Path], *, exclude_paths: set[Path] | None = None) -> dict[str, Any]:
    files = _iter_files(inputs, exclude_paths=exclude_paths)
    hashes = {str(path.as_posix()): _sha256_bytes(_normalized_bytes(path)) for path in files}
    return {
        "protocol": protocol,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": hashes,
    }


def compare_snapshots(current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, list[str]]:
    current_files = current.get("files", {})
    baseline_files = baseline.get("files", {})
    if not isinstance(current_files, dict) or not isinstance(baseline_files, dict):
        raise ValueError("Snapshot format is invalid: files must be mapping")

    added = sorted(path for path in current_files.keys() if path not in baseline_files)
    removed = sorted(path for path in baseline_files.keys() if path not in current_files)
    changed = sorted(path for path in current_files.keys() if path in baseline_files and current_files[path] != baseline_files[path])
    return {"added": added, "removed": removed, "changed": changed}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check protocol contract regression snapshot")
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--input", dest="inputs", action="append", required=True, help="Contract file/dir (repeatable)")
    parser.add_argument("--exclude", dest="excludes", action="append", default=[], help="Path to exclude from snapshot (repeatable)")
    parser.add_argument("--update", action="store_true")
    args = parser.parse_args()

    inputs = [Path(item) for item in args.inputs]
    missing = [str(p) for p in inputs if not p.exists()]
    if missing:
        print(f"Missing regression input paths: {', '.join(missing)}")
        return 2

    snapshot_path = Path(args.snapshot)
    exclude_paths = {Path(item).resolve() for item in args.excludes}
    # Prevent self-referential churn when snapshot file is inside the input directory.
    exclude_paths.add(snapshot_path.resolve())
    current = collect_snapshot(args.protocol, inputs, exclude_paths=exclude_paths)

    if args.update:
        _write_json(snapshot_path, current)
        print(f"[ok] protocol regression snapshot updated: {snapshot_path}")
        return 0

    if not snapshot_path.exists():
        print(f"Protocol regression snapshot missing: {snapshot_path}")
        print("Run with --update to create baseline snapshot.")
        return 2

    baseline = json.loads(snapshot_path.read_text(encoding="utf-8"))
    diff = compare_snapshots(current, baseline)
    if any(diff.values()):
        print("Protocol regression check failed:")
        for key in ("added", "removed", "changed"):
            if diff[key]:
                print(f"- {key}:")
                for item in diff[key]:
                    print(f"  - {item}")
        return 1

    print("Protocol regression check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

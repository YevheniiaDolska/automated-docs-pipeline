#!/usr/bin/env python3
"""Sync docs from multiple source repositories into one hub repository.

Usage example:
  python3 scripts/sync_multi_repo_docs.py \
    --pair "../app-forge/docs:docs/app-forge" \
    --pair "../code-forge/docs:docs/code-forge" \
    --pair "../quantum-forge/docs:docs/quantum-forge"
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def _parse_pair(raw: str) -> tuple[Path, Path]:
    """Internal helper for `_parse_pair`."""
    if ":" not in raw:
        raise ValueError(f"Invalid --pair value '{raw}'. Expected '<source>:<target>'.")
    src_raw, dst_raw = raw.split(":", 1)
    src = Path(src_raw).expanduser().resolve()
    dst = Path(dst_raw).expanduser().resolve()
    return src, dst


def _safe_wipe_dir(path: Path) -> None:
    """Internal helper for `_safe_wipe_dir`."""
    if not path.exists():
        return
    if not path.is_dir():
        raise RuntimeError(f"Refusing to wipe non-directory: {path}")
    shutil.rmtree(path)


def _copy_docs(src: Path, dst: Path) -> None:
    """Internal helper for `_copy_docs`."""
    if not src.exists():
        raise FileNotFoundError(f"Source docs path not found: {src}")
    if not src.is_dir():
        raise NotADirectoryError(f"Source docs path is not a directory: {src}")
    _safe_wipe_dir(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)


def parse_args() -> argparse.Namespace:
    """Execute `parse_args` workflow."""
    parser = argparse.ArgumentParser(description="Sync docs from source repos into hub docs sections.")
    parser.add_argument(
        "--pair",
        action="append",
        required=True,
        help="Mapping '<source_docs_path>:<target_docs_path>'. Can be passed multiple times.",
    )
    return parser.parse_args()


def main() -> int:
    """Execute `main` workflow."""
    args = parse_args()
    total = 0
    for raw in args.pair:
        src, dst = _parse_pair(raw)
        _copy_docs(src, dst)
        total += 1
        print(f"[ok] synced: {src} -> {dst}")
    print(f"[ok] completed sync pairs: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


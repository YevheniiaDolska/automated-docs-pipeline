#!/usr/bin/env python3
"""Sync canonical root docs into docsops mirror files."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAIRS = [
    (ROOT / "README_SETUP.md", ROOT / "docsops" / "README_SETUP.md"),
    (ROOT / "POLICY_PACKS.md", ROOT / "docsops" / "POLICY_PACKS.md"),
]


def main() -> int:
    for src, dst in PAIRS:
        content = src.read_text(encoding="utf-8")
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(content, encoding="utf-8")
        print(f"synced: {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

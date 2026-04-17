#!/usr/bin/env python3
"""Publish protocol contract/doc assets into docs assets tree."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def _copy(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _ensure_protocols_index(target_root: Path) -> None:
    protocols = sorted(p.name for p in target_root.iterdir() if p.is_dir())
    lines = [
        "---",
        'title: "Protocol assets index"',
        'description: "Generated index for published protocol assets."',
        "content_type: reference",
        "product: both",
        "---",
        "",
        "# Protocol assets index",
        "",
    ]
    if protocols:
        lines.append("Generated protocol asset bundles:")
        lines.append("")
        for protocol in protocols:
            lines.append(f"- [{protocol.upper()} assets](./{protocol}/)")
    else:
        lines.append("No protocol assets are currently published.")
    lines.append("")
    (target_root / "index.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish protocol assets")
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--generated-doc", required=True)
    parser.add_argument("--target-root", default="docs/assets/protocols")
    args = parser.parse_args()

    source = Path(args.source)
    generated_doc = Path(args.generated_doc)
    target_root = Path(args.target_root)
    if target_root.is_absolute():
        raise ValueError("--target-root must be a repository-relative path")
    root = target_root / args.protocol
    root.mkdir(parents=True, exist_ok=True)

    if source.is_file():
        _copy(source, root / source.name)
    elif source.is_dir():
        for item in source.rglob("*"):
            if item.is_file():
                rel = item.relative_to(source)
                _copy(item, root / rel)

    _copy(generated_doc, root / generated_doc.name)
    _ensure_protocols_index(target_root)
    print(f"[protocol-publish] published into: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

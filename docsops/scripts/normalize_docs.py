#!/usr/bin/env python3
"""Normalize Markdown docs for consistent structure and list style."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

CONTENT_TYPES_WITH_NEXT_STEPS = {
    "tutorial",
    "how-to",
    "concept",
    "reference",
    "troubleshooting",
}

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
NEXT_STEPS_HEADING_RE = re.compile(r"^##\s+next\s*steps\s*$", re.IGNORECASE)
H2_RE = re.compile(r"^##\s+")
ORDERED_LIST_RE = re.compile(r"^(\s*)\d+\.\s+")
UNORDERED_LIST_RE = re.compile(r"^(\s*)[+*]\s+")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    raw = match.group(1)
    body = text[match.end() :]
    fm: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fm[key.strip()] = value.strip().strip('"')
    return fm, body


def build_home_link(path: Path, docs_root: Path) -> str:
    sibling_index = path.parent / "index.md"
    if sibling_index.exists() and sibling_index != path:
        return "index.md"

    docs_index = docs_root / "index.md"
    if docs_index.exists():
        rel = docs_index.relative_to(path.parent) if docs_index.is_relative_to(path.parent) else None
        if rel is not None:
            return str(rel).replace("\\", "/")
        return str(Path("..") / "index.md").replace("\\", "/")

    return "../index.md"


def normalize_lines(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        if ORDERED_LIST_RE.match(line):
            # Keep original indentation and normalize ordered lists to "1. " style.
            line = ORDERED_LIST_RE.sub(r"\g<1>1. ", line)
        if UNORDERED_LIST_RE.match(line):
            # Keep original indentation and normalize bullets to "- ".
            line = UNORDERED_LIST_RE.sub(r"\g<1>- ", line)
        if NEXT_STEPS_HEADING_RE.match(line.strip()):
            indent = line[: len(line) - len(line.lstrip())]
            line = f"{indent}## Next steps"
        out.append(line.rstrip())
    return out


def has_next_steps(lines: list[str]) -> bool:
    return any(NEXT_STEPS_HEADING_RE.match(line.strip()) for line in lines)


def append_next_steps(lines: list[str], path: Path, docs_root: Path) -> list[str]:
    if has_next_steps(lines):
        return lines

    link = build_home_link(path, docs_root)
    new_lines = lines[:]
    if new_lines and new_lines[-1] != "":
        new_lines.append("")
    new_lines.extend(
        [
            "## Next steps",
            "",
            f"- [Documentation index]({link})",
            "",
        ]
    )
    return new_lines


def normalize_markdown(text: str, path: Path, docs_root: Path) -> str:
    text = text.replace("\r\n", "\n")
    fm, body = parse_frontmatter(text)
    lines = body.split("\n")
    lines = normalize_lines(lines)

    content_type = fm.get("content_type", "").strip().lower()
    if content_type in CONTENT_TYPES_WITH_NEXT_STEPS and path.name != "index.md":
        lines = append_next_steps(lines, path, docs_root)

    normalized_body = "\n".join(lines).rstrip() + "\n"
    if fm:
        frontmatter_text = text[: text.find(body)]
        return frontmatter_text + normalized_body
    return normalized_body


def collect_files(paths: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for item in paths:
        p = Path(item)
        if p.is_file() and p.suffix == ".md":
            files.append(p)
        elif p.is_dir():
            files.extend(sorted(p.rglob("*.md")))
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize documentation markdown files")
    parser.add_argument("paths", nargs="+", help="Markdown files or directories")
    parser.add_argument("--check", action="store_true", help="Check only, do not modify files")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    docs_root = repo / "docs"

    changed: list[Path] = []
    files = collect_files(args.paths)
    for path in files:
        original = path.read_text(encoding="utf-8")
        normalized = normalize_markdown(original, path, docs_root)
        if normalized != original:
            changed.append(path)
            if not args.check:
                path.write_text(normalized, encoding="utf-8")

    if args.check and changed:
        print("Normalization required for files:")
        for file in changed:
            print(f"- {file}")
        return 1

    if changed and not args.check:
        print(f"Normalized {len(changed)} file(s).")
    else:
        print("Normalization check passed." if args.check else "No normalization changes needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

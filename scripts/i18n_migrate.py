#!/usr/bin/env python3
"""
One-time migration: move docs/ files into docs/{default_locale}/ layout.

This script converts a flat docs/ structure into the folder-based i18n layout
required by mkdocs-static-i18n. Files like _variables.yml, stylesheets/,
assets/, and diagrams/ remain at the docs/ root level.

Idempotent: safe to run multiple times. If docs/{locale}/ already contains
Markdown files, the script skips the migration.

Usage:
    python3 scripts/i18n_migrate.py
    python3 scripts/i18n_migrate.py --config i18n.yml --docs-dir docs --dry-run
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

from i18n_utils import load_i18n_config

# Directories and files that stay at the docs/ root level (not moved)
KEEP_AT_ROOT = {
    "_variables.yml",
    "stylesheets",
    "assets",
    "diagrams",
}


def _should_skip(path: Path, docs_dir: Path) -> bool:
    """Check if a path should remain at docs/ root."""
    try:
        rel = path.relative_to(docs_dir)
    except ValueError:
        return True
    top = rel.parts[0] if rel.parts else ""
    return top in KEEP_AT_ROOT or path.name.startswith("_")


def _is_locale_dir(name: str) -> bool:
    """Check if a directory name looks like a locale code."""
    return bool(re.match(r"^[a-z]{2,3}$", name))


def is_already_migrated(docs_dir: Path, locale: str) -> bool:
    """Check if docs are already in folder-based layout."""
    locale_dir = docs_dir / locale
    if not locale_dir.is_dir():
        return False
    md_files = list(locale_dir.rglob("*.md"))
    return len(md_files) > 0


def migrate(
    docs_dir: Path,
    locale: str,
    dry_run: bool = False,
) -> list[tuple[Path, Path]]:
    """Move Markdown files and content directories into docs/{locale}/.

    Args:
        docs_dir: Root docs directory.
        locale: Default locale code.
        dry_run: If True, only report what would happen.

    Returns:
        List of (source, destination) tuples for moved items.
    """
    if is_already_migrated(docs_dir, locale):
        print(f"Migration skipped: docs/{locale}/ already contains Markdown files.")
        return []

    target_dir = docs_dir / locale
    moves: list[tuple[Path, Path]] = []

    # Collect top-level items to move
    items_to_move: list[Path] = []
    for item in sorted(docs_dir.iterdir()):
        if item.name == locale:
            continue
        if _is_locale_dir(item.name) and item.is_dir():
            continue
        if _should_skip(item, docs_dir):
            continue
        items_to_move.append(item)

    if not items_to_move:
        print("Nothing to migrate.")
        return []

    # Perform the migration
    for item in items_to_move:
        dest = target_dir / item.name
        moves.append((item, dest))

        if dry_run:
            print(f"  [DRY RUN] {item} -> {dest}")
            continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
            shutil.rmtree(item)
        else:
            shutil.move(str(item), str(dest))

    if not dry_run:
        print(f"Migrated {len(moves)} items into docs/{locale}/")

    return moves


def update_mkdocs_nav(mkdocs_path: Path, locale: str, dry_run: bool = False) -> bool:
    """Prefix all nav paths in mkdocs.yml with the locale directory.

    Args:
        mkdocs_path: Path to mkdocs.yml.
        locale: Locale prefix to add.
        dry_run: If True, only report changes.

    Returns:
        True if changes were made (or would be made).
    """
    if not mkdocs_path.exists():
        print("mkdocs.yml not found, skipping nav update.")
        return False

    text = mkdocs_path.read_text(encoding="utf-8")

    # Match nav path values:
    #   "- Title: path/to/file.md" (with colon)
    #   "- path/to/file.md"       (bare path on a list line)
    # but not paths that already have the locale prefix

    # Pattern 1: paths after colon (e.g. "Home: index.md")
    colon_pattern = re.compile(
        r"(:\s+)(?!" + re.escape(locale) + r"/)"
        r"([a-zA-Z0-9][a-zA-Z0-9_\-./]*\.md)"
    )
    new_text = colon_pattern.sub(rf"\g<1>{locale}/\2", text)

    # Pattern 2: bare paths on list lines (e.g. "- getting-started/index.md")
    bare_pattern = re.compile(
        r"(-\s+)(?!" + re.escape(locale) + r"/)"
        r"([a-zA-Z0-9][a-zA-Z0-9_\-./]*\.md)\s*$",
        re.MULTILINE,
    )
    new_text = bare_pattern.sub(rf"\g<1>{locale}/\2", new_text)

    if new_text == text:
        print("mkdocs.yml nav paths already prefixed or no changes needed.")
        return False

    if dry_run:
        print("  [DRY RUN] Would update mkdocs.yml nav paths")
        return True

    mkdocs_path.write_text(new_text, encoding="utf-8")
    print(f"Updated mkdocs.yml: prefixed nav paths with '{locale}/'")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate docs/ to folder-based i18n layout (docs/{locale}/)"
    )
    parser.add_argument(
        "--config",
        default="i18n.yml",
        help="Path to i18n.yml (default: i18n.yml)",
    )
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Documentation root directory (default: docs)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be moved without making changes",
    )
    args = parser.parse_args()

    try:
        config = load_i18n_config(args.config)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    docs_dir = Path(args.docs_dir)
    if not docs_dir.is_dir():
        print(f"Error: {docs_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    locale = config.default_language
    print(f"Migrating docs/ -> docs/{locale}/ ...")

    moves = migrate(docs_dir, locale, dry_run=args.dry_run)
    if moves:
        update_mkdocs_nav(Path("mkdocs.yml"), locale, dry_run=args.dry_run)

    if args.dry_run:
        print(f"\nDry run complete. {len(moves)} items would be moved.")
    else:
        print(f"\nMigration complete. {len(moves)} items moved.")


if __name__ == "__main__":
    main()

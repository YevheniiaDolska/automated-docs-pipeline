"""Tests for scripts/i18n_migrate.py."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from i18n_migrate import (
    KEEP_AT_ROOT,
    is_already_migrated,
    migrate,
    update_mkdocs_nav,
)


@pytest.fixture
def docs_tree(tmp_path: Path) -> Path:
    """Create a minimal docs/ tree for migration tests."""
    docs = tmp_path / "docs"
    docs.mkdir()

    # Root-level files that should stay
    (docs / "_variables.yml").write_text("product_name: Test\n", encoding="utf-8")
    styles = docs / "stylesheets"
    styles.mkdir()
    (styles / "custom.css").write_text("body {}\n", encoding="utf-8")

    # Content files that should be moved
    (docs / "index.md").write_text("---\ntitle: Home\n---\nWelcome\n", encoding="utf-8")
    howto = docs / "how-to"
    howto.mkdir()
    (howto / "guide.md").write_text("---\ntitle: Guide\n---\nSteps\n", encoding="utf-8")

    return docs


class TestIsAlreadyMigrated:
    def test_not_migrated(self, docs_tree: Path):
        assert is_already_migrated(docs_tree, "en") is False

    def test_already_migrated(self, docs_tree: Path):
        en = docs_tree / "en"
        en.mkdir()
        (en / "index.md").write_text("# Home\n", encoding="utf-8")
        assert is_already_migrated(docs_tree, "en") is True


class TestMigrate:
    def test_moves_content_files(self, docs_tree: Path):
        moves = migrate(docs_tree, "en")
        assert len(moves) > 0

        # Content moved
        assert (docs_tree / "en" / "index.md").exists()
        assert (docs_tree / "en" / "how-to" / "guide.md").exists()

        # Root stays
        assert (docs_tree / "_variables.yml").exists()
        assert (docs_tree / "stylesheets" / "custom.css").exists()

        # Originals removed
        assert not (docs_tree / "index.md").exists()
        assert not (docs_tree / "how-to").exists()

    def test_idempotent(self, docs_tree: Path):
        migrate(docs_tree, "en")
        # Second run should skip
        moves = migrate(docs_tree, "en")
        assert moves == []

    def test_dry_run(self, docs_tree: Path):
        moves = migrate(docs_tree, "en", dry_run=True)
        assert len(moves) > 0
        # Nothing actually moved
        assert (docs_tree / "index.md").exists()
        assert not (docs_tree / "en" / "index.md").exists()


class TestUpdateMkdocsNav:
    def test_prefixes_paths(self, tmp_path: Path):
        mkdocs = tmp_path / "mkdocs.yml"
        mkdocs.write_text(textwrap.dedent("""\
            nav:
              - Home: index.md
              - Getting Started:
                - getting-started/index.md
                - "Quickstart": getting-started/quickstart.md
        """), encoding="utf-8")

        changed = update_mkdocs_nav(mkdocs, "en")
        assert changed is True

        text = mkdocs.read_text(encoding="utf-8")
        assert "en/index.md" in text
        assert "en/getting-started/index.md" in text
        assert "en/getting-started/quickstart.md" in text

    def test_no_double_prefix(self, tmp_path: Path):
        mkdocs = tmp_path / "mkdocs.yml"
        mkdocs.write_text("nav:\n  - Home: en/index.md\n", encoding="utf-8")

        changed = update_mkdocs_nav(mkdocs, "en")
        assert changed is False

    def test_missing_file(self, tmp_path: Path):
        assert update_mkdocs_nav(tmp_path / "missing.yml", "en") is False

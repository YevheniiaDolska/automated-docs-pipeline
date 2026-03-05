"""Tests for scripts/lifecycle_manager.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.lifecycle_manager import LifecycleManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _write_md(path: Path, frontmatter: str, body: str) -> Path:
    """Write a markdown file with frontmatter and body."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")
    return path


@pytest.fixture()
def docs_dir(tmp_path: Path) -> Path:
    """Create a minimal docs directory with lifecycle states."""
    docs = tmp_path / "docs"
    docs.mkdir()

    _write_md(
        docs / "active-page.md",
        'title: "Active Page"\nstatus: active',
        "# Active Page\n\nContent.",
    )
    _write_md(
        docs / "deprecated-page.md",
        'title: "Old Feature"\nstatus: deprecated\ndeprecated_since: "2025-06-01"\nreplaced_by: "/new-feature"\nsunset_date: "2026-06-01"',
        "# Old Feature\n\nDeprecated content.",
    )
    _write_md(
        docs / "removed-page.md",
        'title: "Removed Feature"\nstatus: removed\nreplaced_by: "/migration-guide"',
        "# Removed Feature\n\nRemoved.",
    )
    _write_md(
        docs / "draft-page.md",
        'title: "Draft Feature"\nstatus: draft',
        "# Draft Feature\n\nIn progress.",
    )
    _write_md(
        docs / "legacy-preview.md",
        'title: "Preview Feature"\nmaturity: preview\nlast_reviewed: "2024-01-01"',
        "# Preview Feature\n\nPreview content.",
    )
    _write_md(
        docs / "legacy-beta.md",
        'title: "Beta Feature"\nmaturity: beta',
        "# Beta Feature\n\nBeta content.",
    )
    _write_md(
        docs / "legacy-ga.md",
        'title: "GA Feature"\nmaturity: ga',
        "# GA Feature\n\nGA content.",
    )
    _write_md(
        docs / "legacy-removed.md",
        'title: "Legacy Removed"\nmaturity: removed',
        "# Legacy Removed\n\nArchived.",
    )
    # File starting with _ should be skipped
    _write_md(docs / "_variables.md", "title: skip", "skipped")

    return docs


# ---------------------------------------------------------------------------
# extract_frontmatter
# ---------------------------------------------------------------------------


class TestExtractFrontmatter:
    """Tests for LifecycleManager.extract_frontmatter."""

    def test_extracts_valid_frontmatter(self) -> None:
        manager = LifecycleManager()
        fm, body = manager.extract_frontmatter('---\ntitle: "Test"\n---\n# Body')
        assert fm["title"] == "Test"
        assert "Body" in body

    def test_returns_empty_without_frontmatter(self) -> None:
        manager = LifecycleManager()
        fm, body = manager.extract_frontmatter("# No frontmatter")
        assert fm == {}

    def test_returns_empty_for_incomplete_delimiters(self) -> None:
        manager = LifecycleManager()
        fm, body = manager.extract_frontmatter("---\ntitle: Test\n")
        assert fm == {}

    def test_returns_empty_for_bad_yaml(self) -> None:
        manager = LifecycleManager()
        fm, body = manager.extract_frontmatter("---\n: :\n---\nbody")
        assert fm == {}


# ---------------------------------------------------------------------------
# scan_all_pages
# ---------------------------------------------------------------------------


class TestScanAllPages:
    """Tests for scan_all_pages."""

    def test_categorizes_pages_by_status(self, docs_dir: Path) -> None:
        """Pages are grouped by their lifecycle state."""
        manager = LifecycleManager(docs_dir=str(docs_dir), site_generator="mkdocs")
        results = manager.scan_all_pages()

        assert len(results["active"]) >= 1
        assert len(results["deprecated"]) == 1
        assert len(results["removed"]) == 1
        assert len(results["draft"]) >= 1

    def test_legacy_maturity_mapped_to_current_states(self, docs_dir: Path) -> None:
        """Legacy 'maturity' field maps to current status values."""
        manager = LifecycleManager(docs_dir=str(docs_dir), site_generator="mkdocs")
        results = manager.scan_all_pages()

        # maturity: ga -> active
        active_titles = [p["title"] for p in results["active"]]
        assert "GA Feature" in active_titles

        # maturity: removed -> archived
        archived_titles = [p["title"] for p in results["archived"]]
        assert "Legacy Removed" in archived_titles

        # maturity: preview -> stays "preview" (not mapped in legacy_map)
        preview_titles = [p["title"] for p in results["preview"]]
        assert "Preview Feature" in preview_titles

    def test_skips_underscore_files(self, docs_dir: Path) -> None:
        """Files starting with _ are not included in results."""
        manager = LifecycleManager(docs_dir=str(docs_dir), site_generator="mkdocs")
        results = manager.scan_all_pages()
        all_files = []
        for pages in results.values():
            all_files.extend(p["file"] for p in pages)
        assert not any("_variables" in f for f in all_files)

    def test_deprecated_page_has_metadata(self, docs_dir: Path) -> None:
        """Deprecated page retains replacement and sunset info."""
        manager = LifecycleManager(docs_dir=str(docs_dir), site_generator="mkdocs")
        results = manager.scan_all_pages()
        deprecated = results["deprecated"][0]
        assert deprecated["replaced_by"] == "/new-feature"
        assert deprecated["sunset_date"] == "2026-06-01"


# ---------------------------------------------------------------------------
# generate_lifecycle_report
# ---------------------------------------------------------------------------


class TestGenerateLifecycleReport:
    """Tests for generate_lifecycle_report."""

    def test_report_contains_statistics(self, docs_dir: Path) -> None:
        manager = LifecycleManager(docs_dir=str(docs_dir), site_generator="mkdocs")
        results = manager.scan_all_pages()
        report = manager.generate_lifecycle_report(results)

        assert "# Documentation Lifecycle Report" in report
        assert "## Statistics" in report
        assert "DEPRECATED" in report
        assert "REMOVED" in report

    def test_report_shows_deprecated_replacement(self, docs_dir: Path) -> None:
        manager = LifecycleManager(docs_dir=str(docs_dir), site_generator="mkdocs")
        results = manager.scan_all_pages()
        report = manager.generate_lifecycle_report(results)

        assert "/new-feature" in report

    def test_report_shows_removed_without_replacement(self, docs_dir: Path) -> None:
        """Removed pages without replacement get a warning."""
        docs = docs_dir
        _write_md(
            docs / "removed-no-replacement.md",
            'title: "Gone"\nstatus: removed',
            "# Gone",
        )
        manager = LifecycleManager(docs_dir=str(docs), site_generator="mkdocs")
        results = manager.scan_all_pages()
        report = manager.generate_lifecycle_report(results)
        assert "No replacement specified" in report


# ---------------------------------------------------------------------------
# generate_redirect_pages
# ---------------------------------------------------------------------------


class TestGenerateRedirectPages:
    """Tests for generate_redirect_pages."""

    def test_creates_redirect_html_for_removed_pages(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Redirect pages are created for removed docs with replaced_by."""
        monkeypatch.chdir(tmp_path)
        docs = tmp_path / "docs"
        docs.mkdir()
        _write_md(
            docs / "removed-page.md",
            'title: "Removed Feature"\nstatus: removed\nreplaced_by: "/migration-guide"',
            "# Removed Feature\n\nRemoved.",
        )
        # Use absolute path to validate the bug fix in generate_redirect_pages
        manager = LifecycleManager(docs_dir=str(docs), site_generator="mkdocs")
        results = manager.scan_all_pages()
        manager.generate_redirect_pages(results)

        redirect_dir = Path("docs/_redirects")
        html_files = list(redirect_dir.rglob("*.html"))
        assert len(html_files) >= 1
        content = html_files[0].read_text()
        assert "/migration-guide" in content


# ---------------------------------------------------------------------------
# generate_mkdocs_overrides
# ---------------------------------------------------------------------------


class TestGenerateMkdocsOverrides:
    """Tests for generate_mkdocs_overrides."""

    def test_creates_overrides_directory(self, docs_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(docs_dir.parent)
        manager = LifecycleManager(docs_dir=str(docs_dir), site_generator="mkdocs")
        results = manager.scan_all_pages()
        manager.generate_mkdocs_overrides(results)

        main_html = Path("overrides/main.html")
        assert main_html.exists()
        content = main_html.read_text()
        assert "Deprecated" in content
        assert "Preview Feature" in content


# ---------------------------------------------------------------------------
# generate_docusaurus_plugin
# ---------------------------------------------------------------------------


class TestGenerateDocusaurusPlugin:
    """Tests for generate_docusaurus_plugin."""

    def test_creates_plugin_file(self, docs_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(docs_dir.parent)
        manager = LifecycleManager(docs_dir=str(docs_dir), site_generator="docusaurus")
        results = manager.scan_all_pages()
        manager.generate_docusaurus_plugin(results)

        plugin_file = Path("docusaurus-plugin-lifecycle.js")
        assert plugin_file.exists()
        content = plugin_file.read_text()
        assert "lifecyclePlugin" in content

        banner_file = Path("LifecycleBanner.jsx")
        assert banner_file.exists()

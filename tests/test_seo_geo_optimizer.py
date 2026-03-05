"""Tests for scripts/seo_geo_optimizer.py."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from scripts.seo_geo_optimizer import (
    AlgoliaOptimizer,
    ComprehensiveSEOOptimizer,
    GEOFinding,
    SEOEnhancer,
    analyze_content,
    extract_frontmatter,
    geo_lint_file,
    get_first_paragraph,
    infer_metadata_from_path,
    seo_validate_file,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _write_md(path: Path, frontmatter: str, body: str) -> Path:
    """Write a markdown file with frontmatter and body."""
    path.write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# extract_frontmatter
# ---------------------------------------------------------------------------


class TestExtractFrontmatter:
    """Tests for extract_frontmatter."""

    def test_extracts_valid_frontmatter(self) -> None:
        fm, body = extract_frontmatter('---\ntitle: "Test"\n---\n# Body')
        assert fm["title"] == "Test"
        assert "Body" in body

    def test_returns_empty_without_frontmatter(self) -> None:
        fm, body = extract_frontmatter("# No frontmatter here")
        assert fm == {}

    def test_returns_empty_for_incomplete_delimiters(self) -> None:
        fm, body = extract_frontmatter("---\ntitle: Test\n")
        assert fm == {}

    def test_returns_empty_for_bad_yaml(self) -> None:
        fm, body = extract_frontmatter("---\n: :\nbad yaml\n---\nbody")
        assert fm == {}


# ---------------------------------------------------------------------------
# get_first_paragraph
# ---------------------------------------------------------------------------


class TestGetFirstParagraph:
    """Tests for get_first_paragraph."""

    def test_extracts_first_paragraph(self) -> None:
        content = "# Title\nThis is the first paragraph. It has words.\n\nSecond paragraph."
        result = get_first_paragraph(content)
        assert "first paragraph" in result
        assert "Second" not in result

    def test_returns_empty_for_empty_content(self) -> None:
        assert get_first_paragraph("") == ""

    def test_skips_headings(self) -> None:
        content = "# Title\nParagraph text."
        result = get_first_paragraph(content)
        assert "Title" not in result
        assert "Paragraph text." in result


# ---------------------------------------------------------------------------
# GEOFinding
# ---------------------------------------------------------------------------


class TestGEOFinding:
    """Tests for GEOFinding data class."""

    def test_str_representation(self) -> None:
        finding = GEOFinding("test.md", 10, "rule-name", "message here", "warning")
        text = str(finding)
        assert "test.md:10" in text
        assert "[warning]" in text
        assert "rule-name" in text


# ---------------------------------------------------------------------------
# geo_lint_file
# ---------------------------------------------------------------------------


class TestGeoLintFile:
    """Tests for geo_lint_file."""

    def test_missing_description_is_error(self, tmp_path: Path) -> None:
        md = _write_md(tmp_path / "test.md", 'title: "Test"', "# Test\n\nContent here.")
        findings = geo_lint_file(md)
        rules = [f.rule for f in findings]
        assert "meta-description-missing" in rules

    def test_short_description_is_warning(self, tmp_path: Path) -> None:
        md = _write_md(tmp_path / "test.md", 'title: "T"\ndescription: "Short"', "# T\n\nContent.")
        findings = geo_lint_file(md)
        rules = [f.rule for f in findings]
        assert "meta-description-short" in rules

    def test_long_description_is_warning(self, tmp_path: Path) -> None:
        long_desc = "A" * 200
        md = _write_md(tmp_path / "test.md", f'title: "T"\ndescription: "{long_desc}"', "# T\n\nContent.")
        findings = geo_lint_file(md)
        rules = [f.rule for f in findings]
        assert "meta-description-long" in rules

    def test_first_paragraph_too_long(self, tmp_path: Path) -> None:
        long_para = " ".join(["word"] * 70)
        md = _write_md(
            tmp_path / "test.md",
            'title: "T"\ndescription: "Valid description that is long enough for the check."',
            f"# Title\n{long_para}\n\nSecond para.",
        )
        findings = geo_lint_file(md)
        rules = [f.rule for f in findings]
        assert "first-paragraph-too-long" in rules

    def test_generic_heading_detected(self, tmp_path: Path) -> None:
        md = _write_md(
            tmp_path / "test.md",
            'title: "T"\ndescription: "Valid description that is long enough for the check."',
            "# Title\n\n## Overview\n\nContent here.",
        )
        findings = geo_lint_file(md)
        rules = [f.rule for f in findings]
        assert "heading-generic" in rules

    def test_heading_hierarchy_skip(self, tmp_path: Path) -> None:
        md = _write_md(
            tmp_path / "test.md",
            'title: "T"\ndescription: "Valid description that is long enough for the check."',
            "# Title\n\n#### Skipped heading\n\nContent.",
        )
        findings = geo_lint_file(md)
        rules = [f.rule for f in findings]
        assert "heading-hierarchy-skip" in rules

    def test_valid_file_has_minimal_findings(self, tmp_path: Path) -> None:
        md = _write_md(
            tmp_path / "test.md",
            'title: "Configure webhook triggers"\ndescription: "This guide explains how to configure webhook triggers for your automation workflow."',
            "# Configure webhook triggers\n\nThe webhook trigger is a node that starts workflows when it receives HTTP requests on port 5678.\n\n"
            "## Set up webhook endpoints\n\nConfigure the endpoint path and authentication method.\n\n"
            "```javascript\nconst webhook = new Webhook({ port: 5678 });\n```\n",
        )
        findings = geo_lint_file(md)
        errors = [f for f in findings if f.severity == "error"]
        assert len(errors) == 0


# ---------------------------------------------------------------------------
# seo_validate_file
# ---------------------------------------------------------------------------


class TestSeoValidateFile:
    """Tests for seo_validate_file."""

    def test_missing_title_is_error(self, tmp_path: Path) -> None:
        md = _write_md(tmp_path / "test.md", 'description: "Desc"', "# Body\n\nContent.")
        findings = seo_validate_file(md)
        rules = [f.rule for f in findings]
        assert "seo-title-missing" in rules

    def test_short_title_is_warning(self, tmp_path: Path) -> None:
        md = _write_md(tmp_path / "test.md", 'title: "Hi"\ndescription: "Desc"', "# Hi\n\nContent.")
        findings = seo_validate_file(md)
        rules = [f.rule for f in findings]
        assert "seo-title-short" in rules

    def test_long_title_is_warning(self, tmp_path: Path) -> None:
        long_title = "A" * 80
        md = _write_md(tmp_path / "test.md", f'title: "{long_title}"\ndescription: "Desc"', "# T\n\nContent.")
        findings = seo_validate_file(md)
        rules = [f.rule for f in findings]
        assert "seo-title-long" in rules

    def test_url_naming_with_underscores(self, tmp_path: Path) -> None:
        md = _write_md(tmp_path / "BAD_NAME.md", 'title: "Title Here"\ndescription: "Desc"', "# T\n\nContent.")
        findings = seo_validate_file(md)
        rules = [f.rule for f in findings]
        assert "seo-url-naming" in rules

    def test_bare_url_detected(self, tmp_path: Path) -> None:
        md = _write_md(
            tmp_path / "test.md",
            'title: "Title Here Enough"\ndescription: "Desc"',
            "# Title\n\nVisit https://example.com for more info.\n",
        )
        findings = seo_validate_file(md)
        rules = [f.rule for f in findings]
        assert "seo-bare-url" in rules

    def test_image_without_alt_text(self, tmp_path: Path) -> None:
        md = _write_md(
            tmp_path / "test.md",
            'title: "Title Here Enough"\ndescription: "Desc"',
            "# Title\n\n![](image.png)\n",
        )
        findings = seo_validate_file(md)
        rules = [f.rule for f in findings]
        assert "seo-img-no-alt" in rules

    def test_thin_content_detected(self, tmp_path: Path) -> None:
        md = _write_md(
            tmp_path / "test.md",
            'title: "Title Here Enough"\ndescription: "Desc"',
            "# Title\n\nShort content.\n",
        )
        findings = seo_validate_file(md)
        rules = [f.rule for f in findings]
        assert "seo-thin-content" in rules

    def test_duplicate_heading_detected(self, tmp_path: Path) -> None:
        md = _write_md(
            tmp_path / "test.md",
            'title: "Title Here Enough"\ndescription: "Desc"',
            "# Title\n\n## Section one\n\nContent.\n\n## Section one\n\nMore content.\n",
        )
        findings = seo_validate_file(md)
        rules = [f.rule for f in findings]
        assert "seo-duplicate-heading" in rules

    def test_no_freshness_signal(self, tmp_path: Path) -> None:
        md = _write_md(
            tmp_path / "test.md",
            'title: "Title Here Enough"\ndescription: "Desc"',
            "# Title\n\nContent.\n",
        )
        findings = seo_validate_file(md)
        rules = [f.rule for f in findings]
        assert "seo-no-freshness" in rules


# ---------------------------------------------------------------------------
# SEOEnhancer
# ---------------------------------------------------------------------------


class TestSEOEnhancer:
    """Tests for SEOEnhancer."""

    def test_generate_structured_data(self) -> None:
        enhancer = SEOEnhancer("https://docs.example.com")
        fm: dict[str, Any] = {"title": "Test", "description": "Desc", "content_type": "how-to"}
        sd = enhancer.generate_structured_data(Path("docs/how-to/test.md"), fm, "# Test\n\n1. Step one\n2. Step two")
        assert sd["@type"] == "HowTo"
        assert "headline" in sd

    def test_generate_meta_tags(self) -> None:
        enhancer = SEOEnhancer("https://docs.example.com")
        fm: dict[str, Any] = {"title": "Test", "description": "Desc", "tags": ["webhook"]}
        tags = enhancer.generate_meta_tags(fm, Path("docs/test.md"))
        assert tags["title"] == "Test"
        assert "webhook" in tags["keywords"]

    def test_generate_sitemap_entry(self) -> None:
        enhancer = SEOEnhancer("https://docs.example.com")
        fm: dict[str, Any] = {"content_type": "reference", "last_reviewed": "2026-02-01"}
        entry = enhancer.generate_sitemap_entry(Path("docs/reference/index.md"), fm)
        assert entry["priority"] == 0.9  # index page
        assert entry["changefreq"] in ("weekly", "monthly", "yearly")

    def test_breadcrumb_generation(self) -> None:
        enhancer = SEOEnhancer("https://docs.example.com")
        breadcrumb = enhancer._generate_breadcrumb(Path("docs/reference/nodes/webhook.md"))
        assert breadcrumb is not None
        assert breadcrumb["@type"] == "BreadcrumbList"
        assert len(breadcrumb["itemListElement"]) >= 1

    def test_breadcrumb_returns_none_for_root(self) -> None:
        enhancer = SEOEnhancer("https://docs.example.com")
        breadcrumb = enhancer._generate_breadcrumb(Path("index.md"))
        assert breadcrumb is None

    def test_extract_steps(self) -> None:
        enhancer = SEOEnhancer()
        content = "1. First step\n2. Second step\n3. Third step\n"
        steps = enhancer._extract_steps(content)
        assert len(steps) >= 1
        assert steps[0]["@type"] == "HowToStep"

    def test_extract_qa_pairs(self) -> None:
        enhancer = SEOEnhancer()
        content = "Problem: Webhook not firing\nSolution: Check the URL and port\n"
        qa = enhancer._extract_qa_pairs(content)
        assert len(qa) == 1
        assert qa[0]["@type"] == "Question"


# ---------------------------------------------------------------------------
# AlgoliaOptimizer
# ---------------------------------------------------------------------------


class TestAlgoliaOptimizer:
    """Tests for AlgoliaOptimizer."""

    def test_extract_content_sections(self) -> None:
        optimizer = AlgoliaOptimizer()
        content = "## Section one\n\nParagraph text.\n\n## Section two\n\nMore text.\n"
        sections = optimizer.extract_content_sections(content)
        assert len(sections) == 2
        assert sections[0]["heading"] == "Section one"
        assert sections[0]["level"] == 2

    def test_create_search_record(self) -> None:
        optimizer = AlgoliaOptimizer()
        fm: dict[str, Any] = {"title": "Test", "content_type": "tutorial", "tags": ["webhook"]}
        section = {"heading": "Setup", "content": "Install the package.", "level": 2}
        record = optimizer.create_search_record(Path("docs/test.md"), fm, section, 0)
        assert "objectID" in record
        assert record["content_type"] == "tutorial"
        assert record["heading"] == "Setup"

    def test_generate_algolia_config(self) -> None:
        optimizer = AlgoliaOptimizer()
        config = optimizer.generate_algolia_config()
        assert "searchableAttributes" in config
        assert "customRanking" in config


# ---------------------------------------------------------------------------
# infer_metadata_from_path
# ---------------------------------------------------------------------------


class TestInferMetadataFromPath:
    """Tests for infer_metadata_from_path."""

    def test_infers_tutorial_from_path(self) -> None:
        metadata = infer_metadata_from_path(Path("docs/getting-started/quickstart.md"))
        assert metadata["content_type"] == "tutorial"

    def test_infers_howto_from_path(self) -> None:
        metadata = infer_metadata_from_path(Path("docs/how-to/configure-webhook.md"))
        assert metadata["content_type"] == "how-to"

    def test_infers_reference_from_path(self) -> None:
        metadata = infer_metadata_from_path(Path("docs/reference/api.md"))
        assert metadata["content_type"] == "reference"

    def test_infers_troubleshooting_from_path(self) -> None:
        metadata = infer_metadata_from_path(Path("docs/troubleshooting/issue.md"))
        assert metadata["content_type"] == "troubleshooting"

    def test_infers_component_from_filename(self) -> None:
        metadata = infer_metadata_from_path(Path("docs/reference/webhook-node.md"))
        assert metadata.get("app_component") == "webhook"


# ---------------------------------------------------------------------------
# analyze_content
# ---------------------------------------------------------------------------


class TestAnalyzeContent:
    """Tests for analyze_content."""

    def test_infers_howto_from_numbered_steps(self) -> None:
        content = "1. First step\n2. Second step\n3. Third step\n"
        metadata = analyze_content(content)
        assert metadata.get("content_type") == "how-to"

    def test_infers_tutorial_from_prerequisites(self) -> None:
        content = "## Before you begin\n\nInstall Node.js.\n"
        metadata = analyze_content(content)
        assert metadata.get("content_type") == "tutorial"

    def test_infers_troubleshooting_from_problem(self) -> None:
        content = "Problem: The webhook does not fire.\nSolution: Check the port.\n"
        metadata = analyze_content(content)
        assert metadata.get("content_type") == "troubleshooting"

    def test_infers_reference_from_parameter_table(self) -> None:
        content = "| Parameter | Type | Description |\n"
        metadata = analyze_content(content)
        assert metadata.get("content_type") == "reference"

    def test_detects_version_in_content(self) -> None:
        content = "This feature is available since version 2.5.\n"
        metadata = analyze_content(content)
        assert metadata.get("app_version") == "2.5"


# ---------------------------------------------------------------------------
# ComprehensiveSEOOptimizer
# ---------------------------------------------------------------------------


class TestComprehensiveSEOOptimizer:
    """Tests for ComprehensiveSEOOptimizer."""

    def test_optimize_file_collects_findings(self, tmp_path: Path) -> None:
        md = _write_md(
            tmp_path / "test.md",
            'title: "Configure webhook endpoints"\ndescription: "This guide explains how to set up webhook endpoints for workflow automation."',
            "# Configure webhook endpoints\n\nThe webhook node is a trigger that starts workflows on port 5678.\n\n"
            "## Set up endpoint paths\n\nConfigure the path and method.\n\n```bash\ncurl http://localhost:5678/webhook\n```\n",
        )
        optimizer = ComprehensiveSEOOptimizer()
        results = optimizer.optimize_file(md)
        assert results["filepath"] == str(md)
        assert isinstance(results["geo_findings"], list)
        assert results["seo_data"] is not None
        assert len(results["search_records"]) >= 1

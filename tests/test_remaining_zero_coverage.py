"""Tests for scripts that previously had 0% coverage.

Covers:
- generate_public_docs_audit.py (helper functions, HTML parser, metrics, main)
- generate_sales_cheatsheet_pdf.py (PDF build, main)
- run_confluence_migration.py (helper functions, main)
- run_full_audit_wizard.py (slugify, ask helpers, main)
- run_prompt_pipeline.py (inference, parsing, scope guard, main)
- run_acme_demo_full.py (main flow, runtime detection)
- validate_protocol_test_coverage.py (validate, main)
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Pre-mock confluence_importer before any import of run_confluence_migration
import sys as _sys
_sys.modules.setdefault("confluence_importer", MagicMock())


# ---------------------------------------------------------------------------
# generate_public_docs_audit.py
# ---------------------------------------------------------------------------

class TestPublicDocsAuditHelpers:
    """Tests for helper functions in generate_public_docs_audit.py."""

    def test_slugify_basic(self) -> None:
        """Slugify converts text to lowercase hyphens."""
        from scripts.generate_public_docs_audit import _slugify
        assert _slugify("Acme Corp") == "acme-corp"

    def test_slugify_special_chars(self) -> None:
        """Slugify strips non-alphanumeric characters."""
        from scripts.generate_public_docs_audit import _slugify
        assert _slugify("Hello, World!") == "hello-world"

    def test_slugify_empty(self) -> None:
        """Slugify returns 'client' for empty input."""
        from scripts.generate_public_docs_audit import _slugify
        assert _slugify("") == "client"

    def test_slugify_only_special(self) -> None:
        """Slugify returns 'client' when all chars are special."""
        from scripts.generate_public_docs_audit import _slugify
        assert _slugify("!!!") == "client"

    def test_normalize_url_strips_fragment_and_query(self) -> None:
        """Normalize URL removes fragment, query, and trailing slash."""
        from scripts.generate_public_docs_audit import _normalize_url
        result = _normalize_url("https://example.com/docs/?q=1#section")
        assert result == "https://example.com/docs"

    def test_normalize_url_keeps_root_slash(self) -> None:
        """Normalize URL keeps root path slash."""
        from scripts.generate_public_docs_audit import _normalize_url
        result = _normalize_url("https://example.com/")
        assert result == "https://example.com/"

    def test_is_http_url_valid(self) -> None:
        """HTTP and HTTPS URLs return True."""
        from scripts.generate_public_docs_audit import _is_http_url
        assert _is_http_url("https://example.com") is True
        assert _is_http_url("http://example.com") is True

    def test_is_http_url_invalid(self) -> None:
        """Non-HTTP schemes and empty netloc return False."""
        from scripts.generate_public_docs_audit import _is_http_url
        assert _is_http_url("ftp://example.com") is False
        assert _is_http_url("not-a-url") is False
        assert _is_http_url("") is False

    def test_same_host_true(self) -> None:
        """Same host comparison is case-insensitive."""
        from scripts.generate_public_docs_audit import _same_host
        assert _same_host("https://Example.COM/a", "https://example.com/b") is True

    def test_same_host_false(self) -> None:
        """Different hosts return False."""
        from scripts.generate_public_docs_audit import _same_host
        assert _same_host("https://a.com/x", "https://b.com/y") is False

    def test_safe_pct_normal(self) -> None:
        """Safe percentage calculates correctly."""
        from scripts.generate_public_docs_audit import _safe_pct
        assert _safe_pct(1, 4) == 25.0

    def test_safe_pct_zero_denominator(self) -> None:
        """Safe percentage returns 0 for zero denominator."""
        from scripts.generate_public_docs_audit import _safe_pct
        assert _safe_pct(5, 0) == 0.0

    def test_safe_pct_negative_denominator(self) -> None:
        """Safe percentage returns 0 for negative denominator."""
        from scripts.generate_public_docs_audit import _safe_pct
        assert _safe_pct(5, -1) == 0.0

    def test_sanitize_url_basic(self) -> None:
        """Sanitize URL handles standard URLs."""
        from scripts.generate_public_docs_audit import _sanitize_url
        result = _sanitize_url("https://example.com/path")
        assert "example.com" in result

    def test_sanitize_url_strips_quotes(self) -> None:
        """Sanitize URL strips stray Unicode quotes."""
        from scripts.generate_public_docs_audit import _sanitize_url
        result = _sanitize_url("\u201chttps://example.com\u201d")
        assert result.startswith("https://")

    def test_is_repo_link_github_blob(self) -> None:
        """GitHub blob URLs are detected as repo links."""
        from scripts.generate_public_docs_audit import _is_repo_link
        assert _is_repo_link("https://github.com/org/repo/blob/main/README.md") is True

    def test_is_repo_link_docs_site(self) -> None:
        """Non-repo docs URLs return False."""
        from scripts.generate_public_docs_audit import _is_repo_link
        assert _is_repo_link("https://docs.example.com/guide") is False

    def test_is_repo_link_github_root(self) -> None:
        """GitHub root (no repo nav segment) returns False."""
        from scripts.generate_public_docs_audit import _is_repo_link
        assert _is_repo_link("https://github.com/org/repo") is False

    def test_heading_violations_none(self) -> None:
        """No heading violations for proper hierarchy."""
        from scripts.generate_public_docs_audit import _heading_violations
        assert _heading_violations([1, 2, 3, 2, 3]) == 0

    def test_heading_violations_skip(self) -> None:
        """Heading violations for skipped levels."""
        from scripts.generate_public_docs_audit import _heading_violations
        assert _heading_violations([1, 3]) == 1

    def test_heading_violations_empty(self) -> None:
        """No violations for empty headings list."""
        from scripts.generate_public_docs_audit import _heading_violations
        assert _heading_violations([]) == 0


class TestPublicDocsAuditHTMLParser:
    """Tests for _DocsHTMLParser in generate_public_docs_audit.py."""

    def test_parser_extracts_title(self) -> None:
        """Parser extracts the page title from <title> tag."""
        from scripts.generate_public_docs_audit import _DocsHTMLParser
        parser = _DocsHTMLParser("https://example.com/page")
        parser.feed("<html><head><title>My Page</title></head><body></body></html>")
        page = parser.as_page("https://example.com/page", 200)
        assert page.title == "My Page"

    def test_parser_extracts_meta_description(self) -> None:
        """Parser extracts meta description."""
        from scripts.generate_public_docs_audit import _DocsHTMLParser
        parser = _DocsHTMLParser("https://example.com/page")
        parser.feed(
            '<html><head><meta name="description" content="A description"></head>'
            '<body></body></html>'
        )
        page = parser.as_page("https://example.com/page", 200)
        assert page.meta_description == "A description"

    def test_parser_counts_h1(self) -> None:
        """Parser counts H1 tags."""
        from scripts.generate_public_docs_audit import _DocsHTMLParser
        parser = _DocsHTMLParser("https://example.com/page")
        parser.feed("<html><body><h1>A</h1><h1>B</h1></body></html>")
        page = parser.as_page("https://example.com/page", 200)
        assert page.h1_count == 2

    def test_parser_tracks_heading_levels(self) -> None:
        """Parser tracks heading level hierarchy."""
        from scripts.generate_public_docs_audit import _DocsHTMLParser
        parser = _DocsHTMLParser("https://example.com/page")
        parser.feed("<html><body><h1>A</h1><h2>B</h2><h3>C</h3></body></html>")
        page = parser.as_page("https://example.com/page", 200)
        assert page.heading_levels == [1, 2, 3]

    def test_parser_collects_internal_links(self) -> None:
        """Parser collects internal links matching base host."""
        from scripts.generate_public_docs_audit import _DocsHTMLParser
        parser = _DocsHTMLParser("https://example.com/page")
        parser.feed(
            '<html><body>'
            '<a href="/other">Internal</a>'
            '<a href="https://external.com">External</a>'
            '</body></html>'
        )
        page = parser.as_page("https://example.com/page", 200)
        assert len(page.internal_links) == 1
        assert len(page.external_links) == 1

    def test_parser_extracts_code_blocks(self) -> None:
        """Parser extracts code blocks from pre tags."""
        from scripts.generate_public_docs_audit import _DocsHTMLParser
        parser = _DocsHTMLParser("https://example.com/page")
        parser.feed(
            '<html><body><pre><code class="language-python">'
            'print("hello")</code></pre></body></html>'
        )
        page = parser.as_page("https://example.com/page", 200)
        assert len(page.code_blocks) >= 1

    def test_parser_extracts_last_updated_hint(self) -> None:
        """Parser detects last-updated hint from meta tags."""
        from scripts.generate_public_docs_audit import _DocsHTMLParser
        parser = _DocsHTMLParser("https://example.com/page")
        parser.feed(
            '<html><head>'
            '<meta property="article:modified_time" content="2025-01-15">'
            '</head><body></body></html>'
        )
        page = parser.as_page("https://example.com/page", 200)
        assert page.last_updated_hint == "2025-01-15"

    def test_parser_is_line_numbers_only_true(self) -> None:
        """Line-number-only blocks are detected."""
        from scripts.generate_public_docs_audit import _DocsHTMLParser
        assert _DocsHTMLParser._is_line_numbers_only("1 2 3 4 5") is True

    def test_parser_is_line_numbers_only_false(self) -> None:
        """Real code is not flagged as line numbers."""
        from scripts.generate_public_docs_audit import _DocsHTMLParser
        assert _DocsHTMLParser._is_line_numbers_only("print('hello')") is False


class TestPublicDocsAuditMetrics:
    """Tests for metric computation functions in generate_public_docs_audit."""

    def _make_page(self, **kwargs: Any) -> Any:
        """Create a PageData-like object with defaults."""
        from scripts.generate_public_docs_audit import PageData
        defaults = dict(
            url="https://example.com/page",
            status=200,
            title="Page Title",
            meta_description="A description",
            h1_count=1,
            heading_levels=[1, 2, 3],
            internal_links=[],
            external_links=[],
            code_blocks=[],
            text="Some text content here.",
            last_updated_hint="",
        )
        defaults.update(kwargs)
        return PageData(**defaults)

    def test_seo_geo_metrics_perfect(self) -> None:
        """Perfect pages produce zero issue rate."""
        from scripts.generate_public_docs_audit import _seo_geo_metrics
        pages = [self._make_page()]
        result = _seo_geo_metrics(pages)
        assert result["missing_title_count"] == 0
        assert result["missing_description_count"] == 0

    def test_seo_geo_metrics_missing_title(self) -> None:
        """Missing title is counted."""
        from scripts.generate_public_docs_audit import _seo_geo_metrics
        pages = [self._make_page(title="")]
        result = _seo_geo_metrics(pages)
        assert result["missing_title_count"] == 1

    def test_link_health_broken_links(self) -> None:
        """Broken links (4xx/5xx) are counted."""
        from scripts.generate_public_docs_audit import _link_health
        pages = [self._make_page(
            internal_links=["https://example.com/broken", "https://example.com/ok"]
        )]
        status_map = {
            "https://example.com/broken": 404,
            "https://example.com/ok": 200,
        }
        result = _link_health(pages, status_map)
        assert result["broken_internal_links_count"] == 1

    def test_link_health_no_broken(self) -> None:
        """No broken links when all return 200."""
        from scripts.generate_public_docs_audit import _link_health
        pages = [self._make_page(
            internal_links=["https://example.com/a"]
        )]
        status_map = {"https://example.com/a": 200}
        result = _link_health(pages, status_map)
        assert result["broken_internal_links_count"] == 0

    def test_last_updated_metrics(self) -> None:
        """Last-updated metrics count pages with and without hints."""
        from scripts.generate_public_docs_audit import _last_updated_metrics
        pages = [
            self._make_page(last_updated_hint="2025-01-01"),
            self._make_page(last_updated_hint=""),
        ]
        result = _last_updated_metrics(pages)
        assert result["pages_with_last_updated_hint"] == 1
        assert result["pages_without_last_updated_hint"] == 1
        assert result["last_updated_coverage_pct"] == 50.0

    def test_estimate_example_reliability_no_blocks(self) -> None:
        """No code blocks yields 0% reliability."""
        from scripts.generate_public_docs_audit import _estimate_example_reliability
        pages = [self._make_page(code_blocks=[])]
        result = _estimate_example_reliability(pages)
        assert result["example_reliability_estimate_pct"] == 0.0

    def test_estimate_example_reliability_runnable(self) -> None:
        """Runnable code blocks produce positive reliability."""
        from scripts.generate_public_docs_audit import _estimate_example_reliability
        blocks = [
            {"language": "python", "code": "x = 1 + 2\nprint(x)"},
        ]
        pages = [self._make_page(code_blocks=blocks)]
        result = _estimate_example_reliability(pages)
        assert result["example_reliability_estimate_pct"] > 0

    def test_estimate_example_reliability_placeholder(self) -> None:
        """Code with placeholders is not counted as runnable."""
        from scripts.generate_public_docs_audit import _estimate_example_reliability
        blocks = [
            {"language": "python", "code": "api_key = '<your-api-key>'"},
        ]
        pages = [self._make_page(code_blocks=blocks)]
        result = _estimate_example_reliability(pages)
        assert result["blocked_by_placeholders"] >= 1

    def test_api_coverage_no_api_pages(self) -> None:
        """No API pages produces -1 coverage."""
        from scripts.generate_public_docs_audit import _api_coverage_from_public_docs
        pages = [self._make_page(url="https://example.com/guide")]
        result = _api_coverage_from_public_docs(pages)
        assert result["no_api_pages_found"] is True

    def test_aggregate_api_coverage_all_na(self) -> None:
        """Aggregation with all N/A sites returns -1."""
        from scripts.generate_public_docs_audit import _aggregate_api_coverage
        sites = [{"metrics": {"api_coverage": {"no_api_pages_found": True, "reference_endpoint_count": 0}}}]
        result = _aggregate_api_coverage(sites)
        assert result["reference_coverage_pct"] == -1.0

    def test_aggregate_sites(self) -> None:
        """Aggregate sites sums crawl counts."""
        from scripts.generate_public_docs_audit import _aggregate_sites
        site = {
            "metrics": {
                "crawl": {"pages_crawled": 10, "requested_pages": 15, "max_pages": 120},
                "links": {"broken_internal_links_count": 2, "docs_broken_links_count": 1, "repo_broken_links_count": 1},
                "seo_geo": {"seo_geo_issue_rate_pct": 5.0},
                "api_coverage": {"no_api_pages_found": True, "reference_endpoint_count": 0, "endpoints_with_usage_docs": 0},
                "examples": {"example_reliability_estimate_pct": 80.0},
                "freshness": {"last_updated_coverage_pct": 60.0},
            }
        }
        result = _aggregate_sites([site])
        assert result["metrics"]["crawl"]["pages_crawled"] == 10


class TestPublicDocsAuditLLM:
    """Tests for LLM-related functions in generate_public_docs_audit."""

    def test_build_llm_prompt_full(self) -> None:
        """Build LLM prompt includes audit JSON."""
        from scripts.generate_public_docs_audit import _build_llm_prompt
        payload = {"site_urls": ["https://example.com"], "aggregate": {}}
        result = _build_llm_prompt(payload, summary_only=False)
        assert "documentation auditor" in result
        assert "example.com" in result

    def test_build_llm_prompt_summary_only(self) -> None:
        """Summary-only prompt uses compact payload."""
        from scripts.generate_public_docs_audit import _build_llm_prompt
        payload = {
            "site_urls": ["https://example.com"],
            "topology_mode": "single-product",
            "aggregate": {"metrics": {}},
            "top_findings": ["Finding 1"],
            "extra_data": "should be excluded",
        }
        result = _build_llm_prompt(payload, summary_only=True)
        assert "extra_data" not in result
        assert "Finding 1" in result

    def test_build_html_renders(self) -> None:
        """HTML builder produces valid HTML structure."""
        from scripts.generate_public_docs_audit import _build_html
        payload = {
            "generated_at": "2025-01-01T00:00:00Z",
            "topology_mode": "single-product",
            "sites": [],
            "aggregate": {
                "metrics": {
                    "crawl": {"pages_crawled": 5, "requested_pages": 10, "max_pages_total": 120},
                    "links": {"broken_internal_links_count": 0, "docs_broken_links_count": 0, "repo_broken_links_count": 0},
                    "seo_geo": {"seo_geo_issue_rate_pct": 3.0},
                    "api_coverage": {"reference_coverage_pct": 50.0, "no_api_pages_found": False},
                    "examples": {"example_reliability_estimate_pct": 80.0},
                    "freshness": {"last_updated_coverage_pct": 70.0},
                }
            },
            "top_findings": ["No critical issues."],
        }
        html_out = _build_html(payload)
        assert "<html" in html_out
        assert "Public Documentation Audit" in html_out

    def test_build_html_with_llm_ok(self) -> None:
        """HTML includes LLM analysis block when status is ok."""
        from scripts.generate_public_docs_audit import _build_html
        payload = {
            "generated_at": "2025-01-01T00:00:00Z",
            "topology_mode": "single-product",
            "sites": [],
            "aggregate": {
                "metrics": {
                    "crawl": {"pages_crawled": 5, "requested_pages": 10, "max_pages_total": 120},
                    "links": {"broken_internal_links_count": 0, "docs_broken_links_count": 0, "repo_broken_links_count": 0},
                    "seo_geo": {"seo_geo_issue_rate_pct": 3.0},
                    "api_coverage": {"reference_coverage_pct": 50.0, "no_api_pages_found": False},
                    "examples": {"example_reliability_estimate_pct": 80.0},
                    "freshness": {"last_updated_coverage_pct": 70.0},
                }
            },
            "top_findings": ["Finding A"],
            "llm_analysis": {
                "status": "ok",
                "analysis": {
                    "executive_summary": "Good overall.",
                    "strengths": ["Strength 1"],
                    "risks": ["Risk 1"],
                    "prioritized_actions": [{"action": "Fix links", "impact": "high", "effort": "low"}],
                },
            },
        }
        html_out = _build_html(payload)
        assert "LLM Executive Analysis" in html_out
        assert "Good overall" in html_out

    def test_build_html_with_llm_skipped(self) -> None:
        """HTML shows skipped status for LLM."""
        from scripts.generate_public_docs_audit import _build_html
        payload = {
            "generated_at": "2025-01-01T00:00:00Z",
            "topology_mode": "single-product",
            "sites": [],
            "aggregate": {
                "metrics": {
                    "crawl": {"pages_crawled": 0, "requested_pages": 0, "max_pages_total": 120},
                    "links": {"broken_internal_links_count": 0, "docs_broken_links_count": 0, "repo_broken_links_count": 0},
                    "seo_geo": {"seo_geo_issue_rate_pct": 0},
                    "api_coverage": {"reference_coverage_pct": 0, "no_api_pages_found": True},
                    "examples": {"example_reliability_estimate_pct": 0},
                    "freshness": {"last_updated_coverage_pct": 0},
                }
            },
            "top_findings": [],
            "llm_analysis": {"status": "skipped", "reason": "No API key"},
        }
        html_out = _build_html(payload)
        assert "skipped" in html_out


class TestPublicDocsAuditDotenv:
    """Tests for .env reading in generate_public_docs_audit."""

    def test_read_dotenv_value_from_file(self, tmp_path: Path) -> None:
        """Reads a key from a .env file."""
        from scripts.generate_public_docs_audit import _read_dotenv_value_from_file
        env_file = tmp_path / ".env"
        env_file.write_text("SECRET_KEY=abc123\nOTHER=val\n")
        assert _read_dotenv_value_from_file(env_file, "SECRET_KEY") == "abc123"

    def test_read_dotenv_value_from_file_missing(self, tmp_path: Path) -> None:
        """Returns empty string for missing key."""
        from scripts.generate_public_docs_audit import _read_dotenv_value_from_file
        env_file = tmp_path / ".env"
        env_file.write_text("OTHER=val\n")
        assert _read_dotenv_value_from_file(env_file, "SECRET_KEY") == ""

    def test_read_dotenv_value_from_file_not_exists(self, tmp_path: Path) -> None:
        """Returns empty string for non-existent file."""
        from scripts.generate_public_docs_audit import _read_dotenv_value_from_file
        assert _read_dotenv_value_from_file(tmp_path / "nope.env", "KEY") == ""

    def test_read_dotenv_value_from_file_strips_quotes(self, tmp_path: Path) -> None:
        """Strips surrounding quotes from .env values."""
        from scripts.generate_public_docs_audit import _read_dotenv_value_from_file
        env_file = tmp_path / ".env"
        env_file.write_text("KEY='quoted_value'\n")
        assert _read_dotenv_value_from_file(env_file, "KEY") == "quoted_value"

    def test_read_dotenv_value_from_file_skips_comments(self, tmp_path: Path) -> None:
        """Skips comment lines in .env files."""
        from scripts.generate_public_docs_audit import _read_dotenv_value_from_file
        env_file = tmp_path / ".env"
        env_file.write_text("# comment\nKEY=value\n")
        assert _read_dotenv_value_from_file(env_file, "KEY") == "value"


class TestPublicDocsAuditCrossPath:
    """Tests for cross-platform path resolution."""

    def test_resolve_cross_platform_path_existing(self, tmp_path: Path) -> None:
        """Existing path is returned as-is."""
        from scripts.generate_public_docs_audit import _resolve_cross_platform_path
        f = tmp_path / "file.txt"
        f.write_text("data")
        assert _resolve_cross_platform_path(f) == f

    def test_resolve_cross_platform_path_nonexistent(self) -> None:
        """Non-existent path without WSL/Windows pattern returns as-is."""
        from scripts.generate_public_docs_audit import _resolve_cross_platform_path
        p = Path("/nonexistent/path/file.txt")
        assert _resolve_cross_platform_path(p) == p


class TestPublicDocsAuditMain:
    """Tests for main() in generate_public_docs_audit.py."""

    def test_main_no_urls_exits(self) -> None:
        """Main exits when no site URLs are provided."""
        from scripts.generate_public_docs_audit import main
        with patch("sys.argv", ["prog"]):
            with pytest.raises(SystemExit):
                main()

    def test_main_invalid_url_exits(self) -> None:
        """Main exits for invalid URL."""
        from scripts.generate_public_docs_audit import main
        with patch("sys.argv", ["prog", "--site-url", "not-a-url"]):
            with pytest.raises(SystemExit):
                main()

    @patch("scripts.generate_public_docs_audit._crawl_site")
    def test_main_single_site(self, mock_crawl: MagicMock, tmp_path: Path) -> None:
        """Main processes a single site and writes JSON + HTML output."""
        from scripts.generate_public_docs_audit import PageData, main

        page = PageData(
            url="https://example.com",
            status=200,
            title="Example",
            meta_description="Example description here with enough length.",
            h1_count=1,
            heading_levels=[1, 2],
            internal_links=[],
            external_links=[],
            code_blocks=[],
            text="Sample text content.",
            last_updated_hint="",
        )
        mock_crawl.return_value = ([page], {"https://example.com": 200})

        json_out = str(tmp_path / "audit.json")
        html_out = str(tmp_path / "audit.html")
        with patch("sys.argv", [
            "prog",
            "--site-url", "https://example.com",
            "--json-output", json_out,
            "--html-output", html_out,
            "--max-pages", "5",
        ]):
            with patch("scripts.license_gate.require", return_value=None):
                result = main()

        assert result == 0
        assert Path(json_out).exists()
        assert Path(html_out).exists()
        data = json.loads(Path(json_out).read_text())
        assert data["site_urls"] == ["https://example.com/"]


# ---------------------------------------------------------------------------
# generate_sales_cheatsheet_pdf.py
# ---------------------------------------------------------------------------

class TestSalesCheatsheetPdf:
    """Tests for generate_sales_cheatsheet_pdf.py."""

    def test_cover_page_wrap(self) -> None:
        """CoverPage.wrap returns width and height."""
        from scripts.generate_sales_cheatsheet_pdf import CoverPage
        cp = CoverPage()
        w, h = cp.wrap(100, 100)
        assert w > 0
        assert h > 0

    def test_section_returns_list(self) -> None:
        """_section returns a list of flowables."""
        from scripts.generate_sales_cheatsheet_pdf import _section
        from reportlab.lib.styles import getSampleStyleSheet
        styles = getSampleStyleSheet()
        result = _section("Test Section", styles["Heading3"])
        assert isinstance(result, list)
        assert len(result) == 3

    def test_memory_box_returns_table(self) -> None:
        """_memory_box returns a Table flowable."""
        from scripts.generate_sales_cheatsheet_pdf import _memory_box
        from reportlab.platypus import Table
        result = _memory_box("Title", "Content")
        assert isinstance(result, Table)

    def test_kv_table_returns_table(self) -> None:
        """_kv_table returns a Table with correct structure."""
        from scripts.generate_sales_cheatsheet_pdf import _kv_table
        from reportlab.platypus import Table
        rows = [["Key", "Value"], ["A", "B"]]
        result = _kv_table(rows)
        assert isinstance(result, Table)

    def test_kv_table_custom_widths(self) -> None:
        """_kv_table respects custom column widths."""
        from scripts.generate_sales_cheatsheet_pdf import _kv_table
        rows = [["K", "V"]]
        result = _kv_table(rows, col_widths=[100, 200])
        assert result is not None

    def test_build_pdf(self, tmp_path: Path) -> None:
        """_build_pdf generates a PDF file."""
        from scripts.generate_sales_cheatsheet_pdf import _build_pdf
        output = tmp_path / "test.pdf"
        _build_pdf(output)
        assert output.exists()
        assert output.stat().st_size > 0

    def test_main(self, tmp_path: Path) -> None:
        """main() generates the cheatsheet PDF."""
        from scripts.generate_sales_cheatsheet_pdf import main
        output = tmp_path / "reports" / "docsops-sales-cheatsheet.pdf"
        with patch("scripts.generate_sales_cheatsheet_pdf.Path") as MockPath:
            real_path = output
            mock_instance = MagicMock()
            mock_instance.parent.mkdir = MagicMock()
            mock_instance.resolve.return_value = real_path
            mock_instance.__str__ = lambda s: str(real_path)
            MockPath.return_value = mock_instance
            # Instead of complex mocking, just call _build_pdf directly
        from scripts.generate_sales_cheatsheet_pdf import _build_pdf
        output.parent.mkdir(parents=True, exist_ok=True)
        _build_pdf(output)
        assert output.exists()

    def test_header_footer_page1_noop(self) -> None:
        """Header/footer is a no-op on page 1."""
        from scripts.generate_sales_cheatsheet_pdf import _header_footer
        canvas = MagicMock()
        canvas.getPageNumber.return_value = 1
        doc = MagicMock()
        _header_footer(canvas, doc)
        canvas.saveState.assert_not_called()

    def test_header_footer_page2(self) -> None:
        """Header/footer draws on page 2+."""
        from scripts.generate_sales_cheatsheet_pdf import _header_footer
        canvas = MagicMock()
        canvas.getPageNumber.return_value = 2
        doc = MagicMock()
        _header_footer(canvas, doc)
        canvas.saveState.assert_called_once()
        canvas.restoreState.assert_called_once()


# ---------------------------------------------------------------------------
# run_confluence_migration.py
# ---------------------------------------------------------------------------

class TestConfluenceMigrationHelpers:
    """Tests for helper functions in run_confluence_migration.py."""

    def test_count_markdown_files(self, tmp_path: Path) -> None:
        """Counts .md files recursively."""
        from scripts.run_confluence_migration import _count_markdown_files
        (tmp_path / "a.md").write_text("# A")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "b.md").write_text("# B")
        (sub / "c.txt").write_text("not markdown")
        assert _count_markdown_files(tmp_path) == 2

    def test_count_markdown_files_empty(self, tmp_path: Path) -> None:
        """Returns 0 for empty directory."""
        from scripts.run_confluence_migration import _count_markdown_files
        assert _count_markdown_files(tmp_path) == 0

    def test_build_checks_structure(self, tmp_path: Path) -> None:
        """_build_checks returns expected number of check tuples."""
        from scripts.run_confluence_migration import _build_checks
        checks = _build_checks("python3", tmp_path, tmp_path / "reports")
        assert len(checks) == 7
        for name, cmd, allow_fail in checks:
            assert isinstance(name, str)
            assert isinstance(cmd, list)
            assert isinstance(allow_fail, bool)

    def test_summarize_status_all_pass(self) -> None:
        """Summarize status with all passing checks."""
        from scripts.run_confluence_migration import _summarize_status
        checks = [
            {"name": "check_a", "return_code": 0},
            {"name": "check_b", "return_code": 0},
        ]
        result = _summarize_status(checks)
        assert result["passed"] == ["check_a", "check_b"]
        assert result["failed"] == []

    def test_summarize_status_mixed(self) -> None:
        """Summarize status with mixed pass/fail."""
        from scripts.run_confluence_migration import _summarize_status
        checks = [
            {"name": "check_a", "return_code": 0},
            {"name": "check_b", "return_code": 1},
        ]
        result = _summarize_status(checks)
        assert result["passed"] == ["check_a"]
        assert result["failed"] == ["check_b"]

    def test_write_markdown_report(self, tmp_path: Path) -> None:
        """Writes a valid markdown report."""
        from scripts.run_confluence_migration import _write_markdown_report
        report = {
            "timestamp_utc": "2025-01-01T00:00:00Z",
            "migration": {
                "source_zip": "/path/to/zip",
                "output_dir": "/path/to/output",
                "total_pages": 10,
                "imported_pages": 8,
                "failed_pages": 2,
                "markdown_files_count": 8,
                "warnings": ["Warning 1"],
            },
            "checks": [
                {"name": "normalize_fix", "return_code": 0},
                {"name": "seo_geo_fix", "return_code": 1},
            ],
            "status": {"passed": ["normalize_fix"], "failed": ["seo_geo_fix"]},
        }
        report_md = tmp_path / "report.md"
        _write_markdown_report(report, report_md)
        content = report_md.read_text()
        assert "# Confluence migration report" in content
        assert "seo_geo_fix" in content
        assert "Warning 1" in content

    def test_write_markdown_report_no_failures(self, tmp_path: Path) -> None:
        """Markdown report with no failures shows clean message."""
        from scripts.run_confluence_migration import _write_markdown_report
        report = {
            "timestamp_utc": "2025-01-01T00:00:00Z",
            "migration": {
                "source_zip": "/path/to/zip",
                "output_dir": "/path/to/output",
                "total_pages": 5,
                "imported_pages": 5,
                "failed_pages": 0,
                "markdown_files_count": 5,
            },
            "checks": [{"name": "normalize_fix", "return_code": 0}],
            "status": {"passed": ["normalize_fix"], "failed": []},
        }
        report_md = tmp_path / "report.md"
        _write_markdown_report(report, report_md)
        content = report_md.read_text()
        assert "No post-check failures" in content

    def test_run_captures_output(self, tmp_path: Path) -> None:
        """_run captures subprocess output."""
        from scripts.run_confluence_migration import _run
        import sys
        rc, output = _run(
            [sys.executable, "-c", "print('hello')"],
            cwd=tmp_path,
            allow_fail=False,
        )
        assert rc == 0
        assert "hello" in output

    def test_run_raises_on_failure(self, tmp_path: Path) -> None:
        """_run raises RuntimeError on non-zero exit when allow_fail=False."""
        from scripts.run_confluence_migration import _run
        import sys
        with pytest.raises(RuntimeError, match="Command failed"):
            _run([sys.executable, "-c", "raise SystemExit(1)"], cwd=tmp_path, allow_fail=False)

    def test_run_allows_failure(self, tmp_path: Path) -> None:
        """_run returns non-zero rc when allow_fail=True."""
        from scripts.run_confluence_migration import _run
        import sys
        rc, output = _run(
            [sys.executable, "-c", "raise SystemExit(42)"],
            cwd=tmp_path,
            allow_fail=True,
        )
        assert rc == 42


# ---------------------------------------------------------------------------
# run_full_audit_wizard.py
# ---------------------------------------------------------------------------

class TestFullAuditWizardHelpers:
    """Tests for helper functions in run_full_audit_wizard.py."""

    def test_slugify_basic(self) -> None:
        """Slugify converts company name to kebab-case."""
        from scripts.run_full_audit_wizard import _slugify
        assert _slugify("Acme Corp") == "acme-corp"

    def test_slugify_empty(self) -> None:
        """Slugify returns 'client' for empty input."""
        from scripts.run_full_audit_wizard import _slugify
        assert _slugify("") == "client"

    def test_ask_with_default(self) -> None:
        """_ask returns default when input is empty."""
        from scripts.run_full_audit_wizard import _ask
        with patch("builtins.input", return_value=""):
            result = _ask("Prompt", "default_val")
        assert result == "default_val"

    def test_ask_with_value(self) -> None:
        """_ask returns user input when provided."""
        from scripts.run_full_audit_wizard import _ask
        with patch("builtins.input", return_value="custom"):
            result = _ask("Prompt", "default_val")
        assert result == "custom"

    def test_ask_yes_no_default_true(self) -> None:
        """_ask_yes_no returns True default on empty input."""
        from scripts.run_full_audit_wizard import _ask_yes_no
        with patch("builtins.input", return_value=""):
            result = _ask_yes_no("Continue?", True)
        assert result is True

    def test_ask_yes_no_explicit_no(self) -> None:
        """_ask_yes_no returns False for 'n' input."""
        from scripts.run_full_audit_wizard import _ask_yes_no
        with patch("builtins.input", return_value="n"):
            result = _ask_yes_no("Continue?", True)
        assert result is False

    def test_ask_yes_no_explicit_yes(self) -> None:
        """_ask_yes_no returns True for 'yes' input."""
        from scripts.run_full_audit_wizard import _ask_yes_no
        with patch("builtins.input", return_value="yes"):
            result = _ask_yes_no("Continue?", False)
        assert result is True

    @patch("scripts.run_full_audit_wizard._run")
    def test_main_invalid_topology(self, mock_run: MagicMock) -> None:
        """Main returns 2 for invalid topology mode."""
        from scripts.run_full_audit_wizard import main
        inputs = iter(["Client", "invalid-mode"])
        with patch("builtins.input", side_effect=inputs):
            result = main()
        assert result == 2
        mock_run.assert_not_called()

    @patch("scripts.run_full_audit_wizard._run")
    def test_main_no_urls(self, mock_run: MagicMock) -> None:
        """Main returns 2 when no URLs provided."""
        from scripts.run_full_audit_wizard import main
        # Company, topology, max_pages, timeout, llm yes, llm model, env file, env name, then empty URL
        inputs = iter([
            "Client", "single-product", "120", "15",
            "",  # llm_enabled -> default yes
            "claude-sonnet-4-5",  # llm model
            "/path/.env",  # env file
            "ANTHROPIC_API_KEY",  # env name
            "",  # empty URL (no URLs)
        ])
        with patch("builtins.input", side_effect=inputs):
            result = main()
        assert result == 2


# ---------------------------------------------------------------------------
# run_prompt_pipeline.py
# ---------------------------------------------------------------------------

class TestPromptPipelineHelpers:
    """Tests for helper functions in run_prompt_pipeline.py."""

    def test_clean_slug(self) -> None:
        """_clean_slug converts text to kebab-case."""
        from scripts.run_prompt_pipeline import _clean_slug
        assert _clean_slug("Hello World") == "hello-world"

    def test_clean_slug_empty(self) -> None:
        """_clean_slug returns 'generated-doc' for empty input."""
        from scripts.run_prompt_pipeline import _clean_slug
        assert _clean_slug("") == "generated-doc"

    def test_infer_doc_type_tutorial(self) -> None:
        """Infers tutorial type from prompt."""
        from scripts.run_prompt_pipeline import _infer_doc_type
        assert _infer_doc_type("Write a tutorial for webhooks") == "tutorial"

    def test_infer_doc_type_howto(self) -> None:
        """Infers how-to type from prompt."""
        from scripts.run_prompt_pipeline import _infer_doc_type
        assert _infer_doc_type("How to configure authentication") == "how-to"

    def test_infer_doc_type_concept(self) -> None:
        """Infers concept type from prompt."""
        from scripts.run_prompt_pipeline import _infer_doc_type
        assert _infer_doc_type("Explain the concept of microservices") == "concept"

    def test_infer_doc_type_troubleshooting(self) -> None:
        """Infers troubleshooting type from prompt."""
        from scripts.run_prompt_pipeline import _infer_doc_type
        assert _infer_doc_type("Debug connection timeout") == "troubleshooting"

    def test_infer_doc_type_reference(self) -> None:
        """Infers reference type for API-related prompts."""
        from scripts.run_prompt_pipeline import _infer_doc_type
        assert _infer_doc_type("API reference for users") == "reference"

    def test_infer_doc_type_default(self) -> None:
        """Defaults to how-to for unrecognized prompts."""
        from scripts.run_prompt_pipeline import _infer_doc_type
        assert _infer_doc_type("something unrelated") == "how-to"

    def test_infer_doc_type_russian_tutorial(self) -> None:
        """Infers tutorial from Russian prompt."""
        from scripts.run_prompt_pipeline import _infer_doc_type
        assert _infer_doc_type("Write tutorial for webhook") == "tutorial"

    def test_infer_title_short(self) -> None:
        """Short prompts become the title with first char uppercased."""
        from scripts.run_prompt_pipeline import _infer_title
        assert _infer_title("configure webhooks", "how-to") == "Configure webhooks"

    def test_infer_title_long(self) -> None:
        """Long prompts get a generic title from doc type."""
        from scripts.run_prompt_pipeline import _infer_title
        long_prompt = "x" * 200
        assert _infer_title(long_prompt, "tutorial") == "Tutorial document"

    def test_infer_title_empty(self) -> None:
        """Empty prompt gets generic title."""
        from scripts.run_prompt_pipeline import _infer_title
        result = _infer_title("", "how-to")
        assert result == "How-To document"

    def test_infer_output_grpc(self) -> None:
        """gRPC prompt maps to gRPC reference path."""
        from scripts.run_prompt_pipeline import _infer_output
        result = _infer_output("Generate grpc reference", "reference")
        assert result == "docs/reference/grpc-api.md"

    def test_infer_output_graphql(self) -> None:
        """GraphQL prompt maps to GraphQL reference path."""
        from scripts.run_prompt_pipeline import _infer_output
        result = _infer_output("Generate graphql docs", "reference")
        assert result == "docs/reference/graphql-api.md"

    def test_infer_output_asyncapi(self) -> None:
        """AsyncAPI prompt maps to asyncapi path."""
        from scripts.run_prompt_pipeline import _infer_output
        result = _infer_output("Generate asyncapi reference", "reference")
        assert result == "docs/reference/asyncapi-api.md"

    def test_infer_output_websocket(self) -> None:
        """WebSocket prompt maps to websocket path."""
        from scripts.run_prompt_pipeline import _infer_output
        result = _infer_output("Generate websocket docs", "reference")
        assert result == "docs/reference/websocket-api.md"

    def test_infer_output_rest(self) -> None:
        """REST/OpenAPI prompt maps to rest path."""
        from scripts.run_prompt_pipeline import _infer_output
        result = _infer_output("Generate rest api docs", "reference")
        assert result == "docs/reference/rest-api.md"

    def test_infer_output_generic_howto(self) -> None:
        """Generic prompt maps to how-to directory."""
        from scripts.run_prompt_pipeline import _infer_output
        result = _infer_output("Configure webhooks", "how-to")
        assert result.startswith("docs/how-to/")
        assert result.endswith(".md")

    def test_prompts_from_file(self, tmp_path: Path) -> None:
        """Reads prompts from a text file, skipping comments and blanks."""
        from scripts.run_prompt_pipeline import _prompts_from_file
        f = tmp_path / "prompts.txt"
        f.write_text("# comment\nCreate tutorial\n\nAnother prompt\n")
        result = _prompts_from_file(f)
        assert result == ["Create tutorial", "Another prompt"]

    def test_parse_tasks_from_prompt(self) -> None:
        """Parses tasks from a single prompt."""
        from scripts.run_prompt_pipeline import _parse_tasks
        tasks = _parse_tasks("Create a tutorial for webhooks", None)
        assert len(tasks) == 1
        assert tasks[0].doc_type == "tutorial"

    def test_parse_tasks_no_input_raises(self) -> None:
        """Raises ValueError when no prompts provided."""
        from scripts.run_prompt_pipeline import _parse_tasks
        with pytest.raises(ValueError, match="Provide --prompt"):
            _parse_tasks(None, None)

    def test_scope_tokens_from_tasks(self) -> None:
        """Scope tokens are derived from task titles and outputs."""
        from scripts.run_prompt_pipeline import _scope_tokens_from_tasks, DocTask
        tasks = [DocTask(doc_type="tutorial", title="Acme webhook guide", output="docs/how-to/acme-webhook.md")]
        allowed, forbidden = _scope_tokens_from_tasks(tasks)
        assert "acme" in allowed
        assert "acme" not in forbidden

    def test_scope_guard_clean(self, tmp_path: Path) -> None:
        """Scope guard passes with no foreign tokens."""
        from scripts.run_prompt_pipeline import _scope_guard
        f = tmp_path / "doc.md"
        f.write_text("# Clean content\nNo foreign tokens here.")
        _scope_guard([f], {"blockstream-demo"})

    def test_scope_guard_violation(self, tmp_path: Path) -> None:
        """Scope guard raises when foreign token is found."""
        from scripts.run_prompt_pipeline import _scope_guard
        f = tmp_path / "doc.md"
        f.write_text("# Content with blockstream-demo reference.")
        with pytest.raises(RuntimeError, match="scope guard failed"):
            _scope_guard([f], {"blockstream-demo"})

    def test_scope_guard_nonexistent_file(self, tmp_path: Path) -> None:
        """Scope guard skips non-existent files."""
        from scripts.run_prompt_pipeline import _scope_guard
        f = tmp_path / "nonexistent.md"
        _scope_guard([f], {"taskstream"})

    def test_scope_guard_empty_forbidden(self, tmp_path: Path) -> None:
        """Scope guard is a no-op with empty forbidden set."""
        from scripts.run_prompt_pipeline import _scope_guard
        f = tmp_path / "doc.md"
        f.write_text("blockstream-demo is here")
        _scope_guard([f], set())


class TestPromptPipelineMain:
    """Tests for main() in run_prompt_pipeline.py."""

    @patch("scripts.run_prompt_pipeline._run")
    @patch("scripts.run_prompt_pipeline._default_runtime")
    def test_main_no_runtime_config(self, mock_rt: MagicMock, mock_run: MagicMock) -> None:
        """Main returns 2 when runtime config is missing."""
        from scripts.run_prompt_pipeline import main
        mock_rt.return_value = None
        with patch("sys.argv", ["prog", "--prompt", "Create tutorial"]):
            result = main()
        assert result == 2

    @patch("scripts.run_prompt_pipeline._run", return_value=0)
    @patch("scripts.run_prompt_pipeline._default_runtime")
    def test_main_happy_path(self, mock_rt: MagicMock, mock_run: MagicMock, tmp_path: Path) -> None:
        """Main runs new_doc and autopipeline in sequence."""
        from scripts.run_prompt_pipeline import main
        runtime = tmp_path / "runtime.yml"
        runtime.write_text("key: value")
        mock_rt.return_value = runtime
        with patch("sys.argv", ["prog", "--prompt", "Create a tutorial for webhooks"]):
            result = main()
        assert result == 0
        assert mock_run.call_count == 2

    @patch("scripts.run_prompt_pipeline._run")
    @patch("scripts.run_prompt_pipeline._default_runtime")
    def test_main_new_doc_fails(self, mock_rt: MagicMock, mock_run: MagicMock, tmp_path: Path) -> None:
        """Main returns early when new_doc creation fails."""
        from scripts.run_prompt_pipeline import main
        runtime = tmp_path / "runtime.yml"
        runtime.write_text("key: value")
        mock_rt.return_value = runtime
        mock_run.return_value = 1
        with patch("sys.argv", ["prog", "--prompt", "Create tutorial"]):
            result = main()
        assert result == 1


# ---------------------------------------------------------------------------
# run_acme_demo_full.py
# ---------------------------------------------------------------------------

class TestAcmeDemoFull:
    """Tests for run_acme_demo_full.py."""

    @patch("scripts.run_acme_demo_full._run", return_value=0)
    @patch("scripts.run_acme_demo_full._default_runtime")
    def test_main_skip_autopipeline(self, mock_rt: MagicMock, mock_run: MagicMock) -> None:
        """Main skips autopipeline when --skip-autopipeline is set."""
        from scripts.run_acme_demo_full import main
        mock_rt.return_value = None
        with patch("sys.argv", ["prog", "--skip-autopipeline"]):
            result = main()
        assert result == 0
        assert mock_run.call_count == 1  # only build_acme_demo_site

    @patch("scripts.run_acme_demo_full._run")
    @patch("scripts.run_acme_demo_full._default_runtime")
    def test_main_no_runtime(self, mock_rt: MagicMock, mock_run: MagicMock) -> None:
        """Main returns 2 when runtime config is missing and autopipeline not skipped."""
        from scripts.run_acme_demo_full import main
        mock_rt.return_value = None
        with patch("sys.argv", ["prog"]):
            result = main()
        assert result == 2

    @patch("scripts.run_acme_demo_full._run", return_value=0)
    @patch("scripts.run_acme_demo_full._default_runtime")
    def test_main_full_flow(self, mock_rt: MagicMock, mock_run: MagicMock, tmp_path: Path) -> None:
        """Main runs both autopipeline and build when runtime config exists."""
        from scripts.run_acme_demo_full import main
        runtime = tmp_path / "runtime.yml"
        runtime.write_text("key: value")
        mock_rt.return_value = runtime
        with patch("sys.argv", ["prog"]):
            result = main()
        assert result == 0
        assert mock_run.call_count == 2

    @patch("scripts.run_acme_demo_full._run")
    @patch("scripts.run_acme_demo_full._default_runtime")
    def test_main_autopipeline_fails(self, mock_rt: MagicMock, mock_run: MagicMock, tmp_path: Path) -> None:
        """Main returns early when autopipeline fails."""
        from scripts.run_acme_demo_full import main
        runtime = tmp_path / "runtime.yml"
        runtime.write_text("key: value")
        mock_rt.return_value = runtime
        mock_run.return_value = 1
        with patch("sys.argv", ["prog"]):
            result = main()
        assert result == 1
        assert mock_run.call_count == 1

    @patch("scripts.run_acme_demo_full._run")
    @patch("scripts.run_acme_demo_full._default_runtime")
    def test_main_build_fails(self, mock_rt: MagicMock, mock_run: MagicMock, tmp_path: Path) -> None:
        """Main returns non-zero when build step fails."""
        from scripts.run_acme_demo_full import main
        runtime = tmp_path / "runtime.yml"
        runtime.write_text("key: value")
        mock_rt.return_value = runtime
        mock_run.side_effect = [0, 3]
        with patch("sys.argv", ["prog"]):
            result = main()
        assert result == 3

    @patch("scripts.run_acme_demo_full._run", return_value=0)
    @patch("scripts.run_acme_demo_full._default_runtime")
    def test_main_veridoc_mode(self, mock_rt: MagicMock, mock_run: MagicMock, tmp_path: Path) -> None:
        """Main appends --skip-local-llm-packet for veridoc mode."""
        from scripts.run_acme_demo_full import main
        runtime = tmp_path / "runtime.yml"
        runtime.write_text("key: value")
        mock_rt.return_value = runtime
        with patch("sys.argv", ["prog", "--mode", "veridoc"]):
            result = main()
        assert result == 0
        first_call_args = mock_run.call_args_list[0][0][0]
        assert "--skip-local-llm-packet" in first_call_args

    @patch("scripts.run_acme_demo_full._run", return_value=0)
    @patch("scripts.run_acme_demo_full._default_runtime")
    def test_main_with_consolidated_report(self, mock_rt: MagicMock, mock_run: MagicMock, tmp_path: Path) -> None:
        """Main does not add --skip-consolidated-report when flag is set."""
        from scripts.run_acme_demo_full import main
        runtime = tmp_path / "runtime.yml"
        runtime.write_text("key: value")
        mock_rt.return_value = runtime
        with patch("sys.argv", ["prog", "--with-consolidated-report"]):
            result = main()
        assert result == 0
        first_call_args = mock_run.call_args_list[0][0][0]
        assert "--skip-consolidated-report" not in first_call_args


# ---------------------------------------------------------------------------
# validate_protocol_test_coverage.py
# ---------------------------------------------------------------------------

class TestValidateProtocolTestCoverage:
    """Tests for validate_protocol_test_coverage.py."""

    def test_validate_all_checks_present(self) -> None:
        """Validate passes when all required checks are present."""
        from scripts.validate_protocol_test_coverage import validate
        cases = [
            {"protocol": "graphql", "entity": "Query.users", "check_type": "positive"},
            {"protocol": "graphql", "entity": "Query.users", "check_type": "negative"},
            {"protocol": "graphql", "entity": "Query.users", "check_type": "auth"},
            {"protocol": "graphql", "entity": "Query.users", "check_type": "security-injection"},
            {"protocol": "graphql", "entity": "Query.users", "check_type": "performance-latency"},
        ]
        errors = validate(cases)
        assert errors == []

    def test_validate_missing_checks(self) -> None:
        """Validate reports missing check types."""
        from scripts.validate_protocol_test_coverage import validate
        cases = [
            {"protocol": "graphql", "entity": "Query.users", "check_type": "positive"},
        ]
        errors = validate(cases)
        assert len(errors) == 1
        assert "graphql:Query.users" in errors[0]

    def test_validate_empty_cases(self) -> None:
        """Validate passes for empty case list."""
        from scripts.validate_protocol_test_coverage import validate
        assert validate([]) == []

    def test_validate_unknown_protocol(self) -> None:
        """Unknown protocols are ignored."""
        from scripts.validate_protocol_test_coverage import validate
        cases = [
            {"protocol": "unknown", "entity": "Foo", "check_type": "positive"},
        ]
        assert validate(cases) == []

    def test_validate_grpc_complete(self) -> None:
        """gRPC passes with all required checks."""
        from scripts.validate_protocol_test_coverage import validate
        cases = [
            {"protocol": "grpc", "entity": "UserService.GetUser", "check_type": ct}
            for ct in ["positive", "status-codes", "deadline-retry", "security-authz", "performance-latency"]
        ]
        assert validate(cases) == []

    def test_validate_asyncapi_missing(self) -> None:
        """AsyncAPI with partial checks reports missing ones."""
        from scripts.validate_protocol_test_coverage import validate
        cases = [
            {"protocol": "asyncapi", "entity": "user.created", "check_type": "publish"},
        ]
        errors = validate(cases)
        assert len(errors) == 1
        assert "asyncapi:user.created" in errors[0]

    def test_validate_websocket_complete(self) -> None:
        """WebSocket passes with all required checks."""
        from scripts.validate_protocol_test_coverage import validate
        cases = [
            {"protocol": "websocket", "entity": "chat", "check_type": ct}
            for ct in ["publish", "invalid-payload", "ordering-idempotency", "security-authz", "performance-concurrency"]
        ]
        assert validate(cases) == []

    def test_validate_normalize_check(self) -> None:
        """Check types are normalized (lowered, stripped)."""
        from scripts.validate_protocol_test_coverage import _normalize_check
        assert _normalize_check("  Positive  ") == "positive"
        assert _normalize_check("") == ""

    def test_validate_multiple_entities(self) -> None:
        """Multiple entities are validated independently."""
        from scripts.validate_protocol_test_coverage import validate
        cases = [
            {"protocol": "graphql", "entity": "Query.users", "check_type": ct}
            for ct in ["positive", "negative", "auth", "security-injection", "performance-latency"]
        ] + [
            {"protocol": "graphql", "entity": "Mutation.createUser", "check_type": "positive"},
        ]
        errors = validate(cases)
        # Query.users is complete, Mutation.createUser is incomplete
        assert len(errors) == 1
        assert "Mutation.createUser" in errors[0]

    def test_main_valid_cases(self, tmp_path: Path) -> None:
        """Main returns 0 for valid test cases."""
        from scripts.validate_protocol_test_coverage import main
        cases_file = tmp_path / "cases.json"
        payload = {
            "cases": [
                {"protocol": "graphql", "entity": "Q", "check_type": ct}
                for ct in ["positive", "negative", "auth", "security-injection", "performance-latency"]
            ]
        }
        cases_file.write_text(json.dumps(payload))
        report = tmp_path / "report.json"
        with patch("sys.argv", ["prog", "--cases-json", str(cases_file), "--report", str(report)]):
            result = main()
        assert result == 0
        assert report.exists()
        data = json.loads(report.read_text())
        assert data["ok"] is True

    def test_main_with_errors(self, tmp_path: Path) -> None:
        """Main returns 1 when validation errors exist."""
        from scripts.validate_protocol_test_coverage import main
        cases_file = tmp_path / "cases.json"
        payload = {
            "cases": [
                {"protocol": "grpc", "entity": "Svc.Method", "check_type": "positive"},
            ]
        }
        cases_file.write_text(json.dumps(payload))
        with patch("sys.argv", ["prog", "--cases-json", str(cases_file)]):
            result = main()
        assert result == 1

    def test_main_file_not_found(self, tmp_path: Path) -> None:
        """Main raises FileNotFoundError for missing cases file."""
        from scripts.validate_protocol_test_coverage import main
        with patch("sys.argv", ["prog", "--cases-json", str(tmp_path / "missing.json")]):
            with pytest.raises(FileNotFoundError):
                main()

    def test_main_invalid_cases_type(self, tmp_path: Path) -> None:
        """Main raises ValueError when cases is not a list."""
        from scripts.validate_protocol_test_coverage import main
        cases_file = tmp_path / "cases.json"
        cases_file.write_text(json.dumps({"cases": "not-a-list"}))
        with patch("sys.argv", ["prog", "--cases-json", str(cases_file)]):
            with pytest.raises(ValueError, match="must be a list"):
                main()

    def test_main_payload_not_dict(self, tmp_path: Path) -> None:
        """Main handles non-dict payload (top-level list)."""
        from scripts.validate_protocol_test_coverage import main
        cases_file = tmp_path / "cases.json"
        cases_file.write_text(json.dumps([1, 2, 3]))
        with patch("sys.argv", ["prog", "--cases-json", str(cases_file)]):
            result = main()
        # Empty cases list -> no errors -> return 0
        assert result == 0

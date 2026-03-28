"""Tests for Confluence migration scripts."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from confluence_converter import ConfluenceToMarkdownConverter
from confluence_importer import ConfluenceImporter


@pytest.fixture
def sample_confluence_zip(tmp_path: Path) -> Path:
    """Create a minimal Confluence export ZIP with entities.xml."""
    xml = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<root>
  <object class=\"Page\">
    <id>101</id>
    <property name=\"title\">Webhook Setup</property>
    <property name=\"spaceKey\">DOCS</property>
    <property name=\"bodyContent\"><![CDATA[<h1>Webhook Setup</h1><p>Configure webhook endpoint.</p><ul><li>Enable HMAC</li></ul>]]></property>
  </object>
  <object class=\"Page\">
    <id>102</id>
    <property name=\"title\">API Reference</property>
    <property name=\"spaceKey\">DOCS</property>
    <property name=\"bodyContent\"><![CDATA[<h2>List projects</h2><p>Use GET /projects.</p>]]></property>
  </object>
</root>
"""
    zip_path = tmp_path / "confluence-export.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("entities.xml", xml)
    return zip_path


class TestConfluenceConverter:
    def test_basic_html_conversion(self) -> None:
        converter = ConfluenceToMarkdownConverter()
        content = "<h2>Title</h2><p>Hello</p><ul><li>Item</li></ul>"
        markdown = converter.convert(content)

        assert "## Title" in markdown
        assert "Hello" in markdown
        assert "- Item" in markdown

    def test_code_macro_conversion(self) -> None:
        converter = ConfluenceToMarkdownConverter()
        content = (
            '<ac:structured-macro ac:name="code">'
            '<ac:parameter ac:name="language">python</ac:parameter>'
            '<ac:plain-text-body><![CDATA[print("ok")]]></ac:plain-text-body>'
            "</ac:structured-macro>"
        )
        markdown = converter.convert(content)
        assert "```python" in markdown
        assert 'print("ok")' in markdown


class TestConfluenceImporter:
    def test_import_export(self, sample_confluence_zip: Path, tmp_path: Path) -> None:
        importer = ConfluenceImporter()
        output_dir = tmp_path / "docs" / "imported"

        result = importer.import_export(sample_confluence_zip, output_dir)

        assert result.total_pages == 2
        assert result.imported_pages == 2
        assert result.failed_pages == 0
        assert len(result.generated_files) == 2

        first = Path(result.generated_files[0]).read_text(encoding="utf-8")
        assert "content_type:" in first
        assert "# " in first
        assert "description:" in first

    def test_missing_entities_xml_raises(self, tmp_path: Path) -> None:
        bad_zip = tmp_path / "bad.zip"
        with zipfile.ZipFile(bad_zip, "w") as archive:
            archive.writestr("readme.txt", "no entities")

        importer = ConfluenceImporter()
        with pytest.raises(ValueError):
            importer.import_export(bad_zip, tmp_path / "out")


class TestExpandedPipeline:
    """Tests for the expanded 14-step migration pipeline."""

    def test_build_checks_returns_14_steps(self, tmp_path: Path) -> None:
        from run_confluence_migration import _build_checks

        checks = _build_checks("python3", tmp_path, tmp_path / "rpt", tmp_path)
        assert len(checks) == 14

    def test_quality_enhance_step_present(self, tmp_path: Path) -> None:
        from run_confluence_migration import _build_checks

        checks = _build_checks("python3", tmp_path, tmp_path / "rpt", tmp_path)
        names = [n for n, _c, _a in checks]
        expected = [
            "normalize_check_before",
            "seo_geo_before",
            "normalize_fix",
            "quality_enhance",
            "seo_geo_fix",
            "validate_frontmatter",
            "normalize_check_after",
            "seo_geo_after",
            "examples_smoke",
            "extract_knowledge",
            "validate_knowledge",
            "rebuild_index",
            "glossary_sync",
            "final_lint_check",
        ]
        assert names == expected

    def test_use_llm_propagates(self, tmp_path: Path) -> None:
        from run_confluence_migration import _build_checks

        checks = _build_checks("python3", tmp_path, tmp_path / "rpt", tmp_path, use_llm=True)
        for name, cmd, _af in checks:
            if name == "quality_enhance":
                assert "--use-llm" in cmd
                return
        pytest.fail("quality_enhance step not found")


class TestApiModeArgs:
    """Tests for REST API mode CLI arguments and validation."""

    def test_api_mode_args_parsed(self) -> None:
        from run_confluence_migration import parse_args

        sys.argv = [
            "run_confluence_migration.py",
            "--confluence-url", "https://mycompany.atlassian.net",
            "--confluence-token", "tok123",
            "--confluence-username", "user@example.com",
            "--space-keys", "DEV,OPS",
            "--include-attachments",
            "--incremental",
            "--skip-post-checks",
        ]
        args = parse_args()
        assert args.confluence_url == "https://mycompany.atlassian.net"
        assert args.confluence_token == "tok123"
        assert args.confluence_username == "user@example.com"
        assert args.space_keys == "DEV,OPS"
        assert args.include_attachments is True
        assert args.incremental is True

    def test_api_mode_requires_token(self) -> None:
        from run_confluence_migration import _run_api_mode
        import argparse

        args = argparse.Namespace(
            confluence_url="https://mycompany.atlassian.net",
            confluence_token="",
            confluence_username="user@example.com",
            space_keys="DEV",
            include_attachments=False,
            incremental=False,
        )
        with pytest.raises(SystemExit):
            _run_api_mode(args, Path("/tmp/out"), Path("/tmp/repo"))

    def test_api_mode_requires_space_keys(self) -> None:
        from run_confluence_migration import _run_api_mode
        import argparse

        args = argparse.Namespace(
            confluence_url="https://mycompany.atlassian.net",
            confluence_token="tok123",
            confluence_username="user@example.com",
            space_keys="",
            include_attachments=False,
            incremental=False,
        )
        with pytest.raises(SystemExit):
            _run_api_mode(args, Path("/tmp/out"), Path("/tmp/repo"))


class TestConfluenceRunner:
    def test_run_script_generates_reports(self, sample_confluence_zip: Path, tmp_path: Path) -> None:
        repo_root = Path(__file__).resolve().parent.parent
        output_dir = tmp_path / "imported"
        reports_dir = tmp_path / "reports"

        cmd = [
            sys.executable,
            str(repo_root / "scripts" / "run_confluence_migration.py"),
            "--export-zip",
            str(sample_confluence_zip),
            "--output-dir",
            str(output_dir),
            "--reports-dir",
            str(reports_dir),
            "--skip-post-checks",
        ]
        completed = subprocess.run(cmd, cwd=str(repo_root), check=False, capture_output=True, text=True)
        assert completed.returncode == 0, completed.stdout + completed.stderr

        report_json = reports_dir / "confluence_migration_report.json"
        report_md = reports_dir / "confluence_migration_report.md"
        assert report_json.exists()
        assert report_md.exists()

        payload = json.loads(report_json.read_text(encoding="utf-8"))
        assert payload["migration"]["imported_pages"] == 2
        assert payload["migration"]["failed_pages"] == 0

"""Tests for scripts/lint_code_snippets.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lint_code_snippets import (
    CodeBlock,
    LintResult,
    _is_template_code,
    extract_code_blocks,
    lint_bash,
    lint_file,
    lint_json,
    lint_paths,
    lint_python,
    lint_yaml,
)


# ---------------------------------------------------------------------------
# extract_code_blocks
# ---------------------------------------------------------------------------


class TestExtractCodeBlocks:
    """Tests for extract_code_blocks."""

    def test_extracts_single_block(self, tmp_path: Path) -> None:
        md = tmp_path / "test.md"
        md.write_text(
            "# Title\n\n```python\nprint('hello')\n```\n",
            encoding="utf-8",
        )
        blocks = extract_code_blocks(md)
        assert len(blocks) == 1
        assert blocks[0].language == "python"
        assert "print" in blocks[0].content

    def test_extracts_multiple_blocks(self, tmp_path: Path) -> None:
        md = tmp_path / "test.md"
        md.write_text(
            "```python\nx = 1\n```\n\n```json\n{}\n```\n",
            encoding="utf-8",
        )
        blocks = extract_code_blocks(md)
        assert len(blocks) == 2
        assert blocks[0].language == "python"
        assert blocks[1].language == "json"

    def test_extracts_tags(self, tmp_path: Path) -> None:
        md = tmp_path / "test.md"
        md.write_text("```python nolint\ncode\n```\n", encoding="utf-8")
        blocks = extract_code_blocks(md)
        assert "nolint" in blocks[0].tags

    def test_records_line_numbers(self, tmp_path: Path) -> None:
        md = tmp_path / "test.md"
        md.write_text("line1\nline2\n```bash\necho hi\n```\n", encoding="utf-8")
        blocks = extract_code_blocks(md)
        assert blocks[0].line_number == 3

    def test_handles_empty_language(self, tmp_path: Path) -> None:
        md = tmp_path / "test.md"
        md.write_text("```\nno language\n```\n", encoding="utf-8")
        blocks = extract_code_blocks(md)
        assert blocks[0].language == ""


# ---------------------------------------------------------------------------
# _is_template_code
# ---------------------------------------------------------------------------


class TestIsTemplateCode:
    """Tests for _is_template_code."""

    def test_detects_bracket_placeholder(self) -> None:
        assert _is_template_code("do_thing([operation])") is True

    def test_detects_jinja_placeholder(self) -> None:
        assert _is_template_code("port {{ default_port }}") is True

    def test_detects_angle_bracket_placeholder(self) -> None:
        assert _is_template_code("kubectl get <resource-name>") is True

    def test_detects_ellipsis(self) -> None:
        assert _is_template_code("function setup() { ... }") is True

    def test_normal_code_is_not_template(self) -> None:
        assert _is_template_code("print('hello world')") is False


# ---------------------------------------------------------------------------
# lint_json
# ---------------------------------------------------------------------------


class TestLintJson:
    """Tests for lint_json."""

    def test_valid_json_passes(self) -> None:
        block = CodeBlock(Path("test.md"), 1, "json", '{"key": "value"}')
        result = lint_json(block)
        assert result.passed is True

    def test_invalid_json_fails(self) -> None:
        block = CodeBlock(Path("test.md"), 1, "json", "{bad json}")
        result = lint_json(block)
        assert result.passed is False
        assert "JSON error" in result.error_message


# ---------------------------------------------------------------------------
# lint_yaml
# ---------------------------------------------------------------------------


class TestLintYaml:
    """Tests for lint_yaml."""

    def test_valid_yaml_passes(self) -> None:
        block = CodeBlock(Path("test.md"), 1, "yaml", "key: value\nlist:\n  - item")
        result = lint_yaml(block)
        assert result.passed is True

    def test_invalid_yaml_fails(self) -> None:
        block = CodeBlock(Path("test.md"), 1, "yaml", ":\n  bad:\n    - :\n  : :")
        result = lint_yaml(block)
        assert result.passed is False
        assert "YAML error" in result.error_message


# ---------------------------------------------------------------------------
# lint_python
# ---------------------------------------------------------------------------


class TestLintPython:
    """Tests for lint_python."""

    def test_valid_python_passes(self) -> None:
        block = CodeBlock(Path("test.md"), 1, "python", "x = 1\nprint(x)\n")
        result = lint_python(block)
        assert result.passed is True

    def test_invalid_python_fails(self) -> None:
        block = CodeBlock(Path("test.md"), 1, "python", "def broken(\n")
        result = lint_python(block)
        assert result.passed is False
        assert "Python syntax error" in result.error_message


# ---------------------------------------------------------------------------
# lint_bash
# ---------------------------------------------------------------------------


class TestLintBash:
    """Tests for lint_bash."""

    def test_valid_bash_passes(self) -> None:
        block = CodeBlock(Path("test.md"), 1, "bash", "echo hello\n")
        result = lint_bash(block)
        assert result.passed is True

    def test_invalid_bash_fails(self) -> None:
        block = CodeBlock(Path("test.md"), 1, "bash", 'if then echo "broken"\n')
        result = lint_bash(block)
        assert result.passed is False


# ---------------------------------------------------------------------------
# lint_file
# ---------------------------------------------------------------------------


class TestLintFile:
    """Tests for lint_file."""

    def test_skips_nolint_tagged_blocks(self, tmp_path: Path) -> None:
        md = tmp_path / "test.md"
        md.write_text("```python nolint\ndef broken(\n```\n", encoding="utf-8")
        results = lint_file(md)
        assert len(results) == 0

    def test_skips_output_languages(self, tmp_path: Path) -> None:
        md = tmp_path / "test.md"
        md.write_text("```text\nsome output\n```\n", encoding="utf-8")
        results = lint_file(md)
        assert len(results) == 0

    def test_skips_template_code(self, tmp_path: Path) -> None:
        md = tmp_path / "test.md"
        md.write_text("```python\ndo_thing({{ variable }})\n```\n", encoding="utf-8")
        results = lint_file(md)
        assert len(results) == 0

    def test_unknown_language_produces_info(self, tmp_path: Path) -> None:
        md = tmp_path / "test.md"
        md.write_text("```fortran\nPROGRAM HELLO\n```\n", encoding="utf-8")
        results = lint_file(md)
        assert len(results) == 1
        assert results[0].severity == "info"

    def test_lints_valid_python_block(self, tmp_path: Path) -> None:
        md = tmp_path / "test.md"
        md.write_text("```python\nx = 1\n```\n", encoding="utf-8")
        results = lint_file(md)
        assert len(results) == 1
        assert results[0].passed is True


# ---------------------------------------------------------------------------
# lint_paths
# ---------------------------------------------------------------------------


class TestLintPaths:
    """Tests for lint_paths."""

    def test_lints_directory(self, tmp_path: Path) -> None:
        (tmp_path / "a.md").write_text("```json\n{}\n```\n", encoding="utf-8")
        (tmp_path / "b.md").write_text("```yaml\nkey: val\n```\n", encoding="utf-8")
        results, files_checked, blocks_checked = lint_paths([str(tmp_path)])
        assert files_checked == 2
        assert blocks_checked == 2
        assert all(r.passed for r in results)

    def test_lints_single_file(self, tmp_path: Path) -> None:
        md = tmp_path / "test.md"
        md.write_text("```json\n{}\n```\n", encoding="utf-8")
        results, files_checked, blocks_checked = lint_paths([str(md)])
        assert files_checked == 1

    def test_skips_non_md_files(self, tmp_path: Path) -> None:
        (tmp_path / "readme.txt").write_text("not markdown", encoding="utf-8")
        results, files_checked, blocks_checked = lint_paths([str(tmp_path / "readme.txt")])
        assert files_checked == 0

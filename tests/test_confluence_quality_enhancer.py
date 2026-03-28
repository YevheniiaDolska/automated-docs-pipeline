"""Tests for confluence_quality_enhancer.py."""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

# Ensure scripts/ is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from confluence_quality_enhancer import (
    CONTENT_TYPE_TAG_MAP,
    GENERIC_HEADINGS,
    EnhancementResult,
    _build_llm_prompt,
    _enhance_with_llm,
    _fix_bare_urls,
    _fix_blank_lines,
    _fix_code_blocks,
    _fix_description,
    _fix_first_paragraph,
    _fix_frontmatter,
    _fix_generic_headings,
    _fix_heading_hierarchy,
    _fix_ordered_lists,
    _fix_tags,
    _fix_title,
    _improve_content_type,
    _load_allowed_tags,
    _load_variables,
    _parse_frontmatter,
    _replace_variables,
    _serialize_frontmatter,
    _ensure_next_steps,
    enhance_directory,
    enhance_file,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALLOWED_TAGS = [
    "Tutorial",
    "How-To",
    "Concept",
    "Reference",
    "Troubleshooting",
    "Cloud",
    "Self-hosted",
    "Webhook",
    "AI",
    "Nodes",
]


def _make_md(fm: dict, body: str) -> str:
    """Build a minimal Markdown document with frontmatter."""
    lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            lines.append(f"{k}:")
            for item in v:
                lines.append(f"  - {item}")
        else:
            lines.append(f'{k}: "{v}"')
    lines.append("---")
    lines.append("")
    lines.append(body)
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# TestLoadVariables
# ---------------------------------------------------------------------------


class TestLoadVariables:
    """Tests for _load_variables."""

    def test_load_from_variables_yml(self, tmp_path):
        """Load flat and nested variables."""
        repo = tmp_path / "repo"
        docs = repo / "docs"
        docs.mkdir(parents=True)
        var_file = docs / "_variables.yml"
        var_file.write_text(
            yaml.dump({
                "product_name": "TestProduct",
                "default_port": 5678,
                "env_vars": {"port": "TEST_PORT"},
                "short": "ab",  # too short, should be skipped
            }),
            encoding="utf-8",
        )

        result = _load_variables(repo)

        assert "TestProduct" in result
        assert result["TestProduct"] == "{{ product_name }}"
        assert "5678" in result
        assert result["5678"] == "{{ default_port }}"
        assert "TEST_PORT" in result
        assert result["TEST_PORT"] == "{{ env_vars.port }}"
        assert "ab" not in result

    def test_missing_file(self, tmp_path):
        """Return empty dict if _variables.yml does not exist."""
        result = _load_variables(tmp_path)
        assert result == {}


# ---------------------------------------------------------------------------
# TestLoadAllowedTags
# ---------------------------------------------------------------------------


class TestLoadAllowedTags:
    """Tests for _load_allowed_tags."""

    def test_parse_mkdocs_tags(self, tmp_path):
        """Parse tags from mkdocs.yml extra.tags section."""
        mkdocs = tmp_path / "mkdocs.yml"
        mkdocs.write_text(
            yaml.dump({"extra": {"tags": {"Tutorial": "", "API": "", "Cloud": ""}}}),
            encoding="utf-8",
        )

        result = _load_allowed_tags(tmp_path)
        assert "Tutorial" in result
        assert "API" in result
        assert "Cloud" in result

    def test_missing_mkdocs(self, tmp_path):
        """Return default content type tags if mkdocs.yml missing."""
        result = _load_allowed_tags(tmp_path)
        assert set(result) == set(CONTENT_TYPE_TAG_MAP.values())


# ---------------------------------------------------------------------------
# TestParseFrontmatter
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    """Tests for frontmatter parsing and serialization."""

    def test_parse_valid_frontmatter(self):
        text = '---\ntitle: "My Doc"\ncontent_type: how-to\n---\n\nBody text.'
        fm, body = _parse_frontmatter(text)
        assert fm["title"] == "My Doc"
        assert fm["content_type"] == "how-to"
        assert "Body text." in body

    def test_parse_no_frontmatter(self):
        text = "Just plain text without frontmatter."
        fm, body = _parse_frontmatter(text)
        assert fm == {}
        assert body == text

    def test_serialize_roundtrip(self):
        fm = {"title": "Test", "tags": ["A", "B"], "product": "both"}
        serialized = _serialize_frontmatter(fm)
        assert serialized.startswith("---\n")
        assert serialized.endswith("---\n")
        assert 'title: "Test"' in serialized
        assert "  - A" in serialized


# ---------------------------------------------------------------------------
# TestImproveContentType
# ---------------------------------------------------------------------------


class TestImproveContentType:
    """Tests for _improve_content_type."""

    def test_troubleshooting_keywords(self):
        assert _improve_content_type("Debug errors", "troubleshoot the issue fix resolve", "") == "troubleshooting"

    def test_reference_keywords(self):
        assert _improve_content_type("API Reference", "endpoint parameter schema method", "") == "reference"

    def test_howto_keywords(self):
        assert _improve_content_type("How to deploy", "configure install deploy setup", "") == "how-to"

    def test_tutorial_keywords(self):
        assert _improve_content_type("Getting Started Tutorial", "step by step tutorial walkthrough beginner", "") == "tutorial"

    def test_concept_keywords(self):
        assert _improve_content_type("Architecture Overview", "architecture concept design explain model theory", "") == "concept"

    def test_keep_current_if_close(self):
        """Keep current type if its score is close to the best."""
        result = _improve_content_type("Setup guide", "configure and install", "how-to")
        assert result == "how-to"

    def test_fallback_to_howto(self):
        """Default to how-to when no keywords match."""
        assert _improve_content_type("Random", "no matching keywords here at all", "") == "how-to"


# ---------------------------------------------------------------------------
# TestFixTitle
# ---------------------------------------------------------------------------


class TestFixTitle:
    """Tests for _fix_title."""

    def test_short_title_unchanged(self):
        assert _fix_title("My Short Title") == "My Short Title"

    def test_truncate_long_title(self):
        long_title = "A " * 50  # way over 70 chars
        result = _fix_title(long_title)
        assert len(result) <= 70

    def test_strip_trailing_period(self):
        assert _fix_title("My Title.") == "My Title"

    def test_truncate_at_word_boundary(self):
        title = "Configure the webhook endpoint for real-time event streaming on production"
        result = _fix_title(title)
        assert len(result) <= 70
        assert not result.endswith(" ")

    def test_empty_title(self):
        assert _fix_title("") == ""


# ---------------------------------------------------------------------------
# TestFixDescription
# ---------------------------------------------------------------------------


class TestFixDescription:
    """Tests for _fix_description."""

    def test_normal_description(self):
        desc = "This is a normal description that is between 50 and 160 characters long enough to pass."
        result = _fix_description(desc, "Title", "body")
        assert 50 <= len(result) <= 160

    def test_too_short_description(self):
        result = _fix_description("Short.", "My Guide", "some body text")
        assert len(result) >= 50
        assert "my guide" in result.lower()

    def test_too_long_description(self):
        desc = "x " * 100  # way over 160 chars
        result = _fix_description(desc, "Title", "body")
        assert len(result) <= 163  # 160 + "..."

    def test_empty_description_generates_from_body(self):
        body = "This document explains how to configure webhooks for production use and other things."
        result = _fix_description("", "Webhooks", body)
        assert len(result) >= 50

    def test_very_short_gets_migration_suffix(self):
        result = _fix_description("Ok.", "X", "b")
        assert len(result) >= 50


# ---------------------------------------------------------------------------
# TestFixTags
# ---------------------------------------------------------------------------


class TestFixTags:
    """Tests for _fix_tags."""

    def test_filter_invalid_tags(self):
        result = _fix_tags(["Tutorial", "InvalidTag", "Cloud"], "tutorial", ALLOWED_TAGS)
        assert "Tutorial" in result
        assert "Cloud" in result
        assert "InvalidTag" not in result

    def test_add_canonical_tag(self):
        result = _fix_tags(["Cloud"], "how-to", ALLOWED_TAGS)
        assert result[0] == "How-To"
        assert "Cloud" in result

    def test_cap_at_8(self):
        tags = ALLOWED_TAGS[:9]
        result = _fix_tags(tags, "tutorial", ALLOWED_TAGS)
        assert len(result) <= 8

    def test_no_duplicate_tags(self):
        result = _fix_tags(["Tutorial", "tutorial", "TUTORIAL"], "tutorial", ALLOWED_TAGS)
        assert result.count("Tutorial") == 1

    def test_none_tags(self):
        result = _fix_tags(None, "reference", ALLOWED_TAGS)
        assert "Reference" in result


# ---------------------------------------------------------------------------
# TestFixFrontmatter
# ---------------------------------------------------------------------------


class TestFixFrontmatter:
    """Tests for _fix_frontmatter orchestration."""

    def test_adds_missing_fields(self):
        fm = {"title": "Test"}
        changes: list[str] = []
        result = _fix_frontmatter(fm, "Test", "body text", ALLOWED_TAGS, changes)
        assert "content_type" in result
        assert "description" in result
        assert "tags" in result
        assert result["product"] == "both"
        assert "last_reviewed" in result
        assert result["language"] == "en"

    def test_preserves_existing_product(self):
        fm = {"title": "T", "product": "cloud"}
        changes: list[str] = []
        result = _fix_frontmatter(fm, "T", "body", ALLOWED_TAGS, changes)
        assert result["product"] == "cloud"

    def test_changes_logged(self):
        fm = {"title": "A" * 80}  # too long title
        changes: list[str] = []
        _fix_frontmatter(fm, "A" * 80, "body", ALLOWED_TAGS, changes)
        assert any("title truncated" in c for c in changes)


# ---------------------------------------------------------------------------
# TestFixHeadingHierarchy
# ---------------------------------------------------------------------------


class TestFixHeadingHierarchy:
    """Tests for _fix_heading_hierarchy."""

    def test_fix_skipped_levels(self):
        lines = ["# Title", "", "#### Skipped to H4"]
        changes: list[str] = []
        result = _fix_heading_hierarchy(lines, changes)
        assert result[2] == "## Skipped to H4"
        assert changes

    def test_correct_hierarchy_unchanged(self):
        lines = ["# Title", "", "## Section", "", "### Subsection"]
        changes: list[str] = []
        result = _fix_heading_hierarchy(lines, changes)
        assert result == lines
        assert not changes

    def test_multiple_skips(self):
        lines = ["# Title", "", "#### A", "", "##### B"]
        changes: list[str] = []
        result = _fix_heading_hierarchy(lines, changes)
        assert result[2] == "## A"
        assert result[4] == "### B"


# ---------------------------------------------------------------------------
# TestFixGenericHeadings
# ---------------------------------------------------------------------------


class TestFixGenericHeadings:
    """Tests for _fix_generic_headings."""

    def test_replace_overview_for_tutorial(self):
        lines = ["## Overview"]
        changes: list[str] = []
        result = _fix_generic_headings(lines, "tutorial", changes)
        assert result[0] == "## What you will learn"
        assert changes

    def test_replace_summary_for_howto(self):
        lines = ["## Summary"]
        changes: list[str] = []
        result = _fix_generic_headings(lines, "how-to", changes)
        assert result[0] == "## Result"

    def test_replace_configuration_default(self):
        lines = ["## Configuration"]
        changes: list[str] = []
        result = _fix_generic_headings(lines, "reference", changes)
        assert result[0] == "## Configure the service"

    def test_h1_not_replaced(self):
        """Only H2+ headings are replaced."""
        lines = ["# Overview"]
        changes: list[str] = []
        result = _fix_generic_headings(lines, "tutorial", changes)
        assert result[0] == "# Overview"

    def test_non_generic_heading_preserved(self):
        lines = ["## Configure HMAC authentication"]
        changes: list[str] = []
        result = _fix_generic_headings(lines, "how-to", changes)
        assert result[0] == "## Configure HMAC authentication"
        assert not changes


# ---------------------------------------------------------------------------
# TestFixFirstParagraph
# ---------------------------------------------------------------------------


class TestFixFirstParagraph:
    """Tests for _fix_first_paragraph."""

    def test_add_definition_pattern(self):
        body = "# My Feature\n\nThis feature does stuff with things.\n\nMore content."
        changes: list[str] = []
        result = _fix_first_paragraph(body, "how-to", changes)
        # The original already contains "is" pattern? No - "does" is not in DEFINITION_PATTERNS
        # Actually "does" is not matched. The function should prepend a definition sentence.
        # Let's check: "does" is not in the patterns list
        assert "explains how to" in result or "is" in result.split("\n\n")[0]

    def test_already_has_definition(self):
        body = "# Title\n\nThis feature is a great tool for automation.\n\nMore."
        changes: list[str] = []
        result = _fix_first_paragraph(body, "concept", changes)
        assert "added definition pattern" not in " ".join(changes)

    def test_truncate_long_paragraph(self):
        long_para = " ".join(["word"] * 80)
        body = f"# Title\n\n{long_para}\n\nMore content."
        changes: list[str] = []
        result = _fix_first_paragraph(body, "how-to", changes)
        # After prepending definition, word count may exceed 60 and get truncated
        assert any("truncated" in c for c in changes) or len(result.split("\n\n")[1].split()) <= 65

    def test_empty_body(self):
        changes: list[str] = []
        result = _fix_first_paragraph("", "how-to", changes)
        assert result == ""


# ---------------------------------------------------------------------------
# TestFixCodeBlocks
# ---------------------------------------------------------------------------


class TestFixCodeBlocks:
    """Tests for _fix_code_blocks."""

    def test_detect_python(self):
        lines = ["```", "import os", "print(os.getcwd())", "```"]
        changes: list[str] = []
        result = _fix_code_blocks(lines, changes)
        assert result[0] == "```python"
        assert changes

    def test_detect_bash(self):
        lines = ["```", "#!/bin/bash", "echo hello", "```"]
        changes: list[str] = []
        result = _fix_code_blocks(lines, changes)
        assert result[0] == "```bash"

    def test_detect_yaml(self):
        lines = ["```", "name: test", "version: 1.0", "```"]
        changes: list[str] = []
        result = _fix_code_blocks(lines, changes)
        assert result[0] == "```yaml"

    def test_detect_json(self):
        lines = ["```", '{"key": "value"}', "```"]
        changes: list[str] = []
        result = _fix_code_blocks(lines, changes)
        assert result[0] == "```json"

    def test_already_labeled(self):
        lines = ["```python", "import os", "```"]
        changes: list[str] = []
        result = _fix_code_blocks(lines, changes)
        assert result[0] == "```python"
        assert not changes

    def test_undetectable_stays_unlabeled(self):
        lines = ["```", "some random text", "nothing recognizable", "```"]
        changes: list[str] = []
        result = _fix_code_blocks(lines, changes)
        assert result[0] == "```"
        assert not changes


# ---------------------------------------------------------------------------
# TestFixBlankLines
# ---------------------------------------------------------------------------


class TestFixBlankLines:
    """Tests for _fix_blank_lines."""

    def test_add_blank_before_heading(self):
        lines = ["Some text.", "## Heading"]
        changes: list[str] = []
        result = _fix_blank_lines(lines, changes)
        assert "" in result
        idx = result.index("## Heading")
        assert result[idx - 1] == ""

    def test_add_blank_before_code_block(self):
        lines = ["Some text.", "```python", "code", "```"]
        changes: list[str] = []
        result = _fix_blank_lines(lines, changes)
        idx = result.index("```python")
        assert result[idx - 1] == ""

    def test_no_change_when_already_correct(self):
        lines = ["Some text.", "", "## Heading", "", "Content."]
        changes: list[str] = []
        result = _fix_blank_lines(lines, changes)
        assert not changes

    def test_skip_inside_code_blocks(self):
        lines = ["```python", "## Not a heading", "```"]
        changes: list[str] = []
        result = _fix_blank_lines(lines, changes)
        assert "## Not a heading" in result


# ---------------------------------------------------------------------------
# TestFixOrderedLists
# ---------------------------------------------------------------------------


class TestFixOrderedLists:
    """Tests for _fix_ordered_lists."""

    def test_normalize_numbered_lists(self):
        lines = ["2. Second item", "3. Third item"]
        changes: list[str] = []
        result = _fix_ordered_lists(lines, changes)
        assert result[0] == "1. Second item"
        assert result[1] == "1. Third item"
        assert changes

    def test_already_normalized(self):
        lines = ["1. First", "1. Second"]
        changes: list[str] = []
        result = _fix_ordered_lists(lines, changes)
        assert not changes

    def test_skip_inside_code_blocks(self):
        lines = ["```", "2. Inside code", "```"]
        changes: list[str] = []
        result = _fix_ordered_lists(lines, changes)
        assert result[1] == "2. Inside code"


# ---------------------------------------------------------------------------
# TestReplaceVariables
# ---------------------------------------------------------------------------


class TestReplaceVariables:
    """Tests for _replace_variables."""

    def test_replace_hardcoded_values(self):
        var_map = {"ProductName": "{{ product_name }}", "5678": "{{ default_port }}"}
        lines = ["Run ProductName on port 5678."]
        changes: list[str] = []
        result = _replace_variables(lines, var_map, changes)
        assert "{{ product_name }}" in result[0]
        assert "{{ default_port }}" in result[0]
        assert changes

    def test_skip_code_blocks(self):
        var_map = {"ProductName": "{{ product_name }}"}
        lines = ["```", "ProductName", "```"]
        changes: list[str] = []
        result = _replace_variables(lines, var_map, changes)
        assert result[1] == "ProductName"

    def test_skip_indented_code(self):
        var_map = {"ProductName": "{{ product_name }}"}
        lines = ["    ProductName is here"]
        changes: list[str] = []
        result = _replace_variables(lines, var_map, changes)
        assert result[0] == "    ProductName is here"

    def test_no_double_replacement(self):
        var_map = {"ProductName": "{{ product_name }}"}
        lines = ["{{ product_name }} is already replaced."]
        changes: list[str] = []
        result = _replace_variables(lines, var_map, changes)
        assert result[0].count("{{ product_name }}") == 1

    def test_empty_var_map(self):
        lines = ["Some text."]
        changes: list[str] = []
        result = _replace_variables(lines, {}, changes)
        assert result == lines
        assert not changes


# ---------------------------------------------------------------------------
# TestFixBareUrls
# ---------------------------------------------------------------------------


class TestFixBareUrls:
    """Tests for _fix_bare_urls."""

    def test_wrap_bare_url(self):
        lines = ["Visit https://example.com/docs for more."]
        changes: list[str] = []
        result = _fix_bare_urls(lines, changes)
        assert "[https://example.com/docs](https://example.com/docs)" in result[0]
        assert changes

    def test_skip_markdown_links(self):
        lines = ["See [docs](https://example.com/docs)."]
        changes: list[str] = []
        result = _fix_bare_urls(lines, changes)
        assert result[0] == lines[0]
        assert not changes

    def test_skip_code_blocks(self):
        lines = ["```", "https://example.com", "```"]
        changes: list[str] = []
        result = _fix_bare_urls(lines, changes)
        assert result[1] == "https://example.com"


# ---------------------------------------------------------------------------
# TestEnsureNextSteps
# ---------------------------------------------------------------------------


class TestEnsureNextSteps:
    """Tests for _ensure_next_steps."""

    def test_add_next_steps(self):
        lines = ["## Section", "", "Content.", ""]
        changes: list[str] = []
        result = _ensure_next_steps(lines, "how-to", changes)
        assert any("Next steps" in line for line in result)
        assert changes

    def test_skip_if_already_present(self):
        lines = ["## Next steps", "", "- Do something."]
        changes: list[str] = []
        result = _ensure_next_steps(lines, "how-to", changes)
        assert not changes

    def test_skip_for_release_notes(self):
        lines = ["## Section", "", "Content."]
        changes: list[str] = []
        result = _ensure_next_steps(lines, "release-note", changes)
        assert not changes


# ---------------------------------------------------------------------------
# TestBuildLlmPrompt
# ---------------------------------------------------------------------------


class TestBuildLlmPrompt:
    """Tests for _build_llm_prompt."""

    def test_prompt_contains_title_and_body(self):
        prompt = _build_llm_prompt("My Title", "My body content", "how-to")
        assert "My Title" in prompt
        assert "My body content" in prompt
        assert "how-to" in prompt
        assert "progressive disclosure" in prompt.lower()


# ---------------------------------------------------------------------------
# TestEnhanceWithLlm
# ---------------------------------------------------------------------------


class TestEnhanceWithLlm:
    """Tests for _enhance_with_llm."""

    def test_skips_when_no_provider(self):
        changes: list[str] = []
        with patch.dict("sys.modules", {"gitspeak_core.docs.llm_executor": MagicMock(side_effect=ImportError)}):
            # Force reimport failure
            result = _enhance_with_llm("Title", "Body text.", "how-to", changes)
        assert result == "Body text."

    def test_rejects_drastically_different_length(self):
        changes: list[str] = []
        mock_module = MagicMock()
        mock_provider = MagicMock()
        mock_provider.get_active_provider.return_value = "groq"
        mock_response = MagicMock()
        mock_response.error = None
        mock_response.content = "x"  # way too short
        mock_provider.generate.return_value = mock_response
        mock_module.LLMProvider.return_value = mock_provider

        with patch.dict("sys.modules", {"gitspeak_core.docs.llm_executor": mock_module}):
            result = _enhance_with_llm("Title", "A" * 1000, "how-to", changes)
        assert result == "A" * 1000
        assert any("rejected" in c for c in changes)


# ---------------------------------------------------------------------------
# TestEnhanceFile
# ---------------------------------------------------------------------------


class TestEnhanceFile:
    """Tests for enhance_file (end-to-end single file)."""

    def test_basic_enhancement(self, tmp_path):
        """Enhance a basic Confluence-migrated document."""
        fm = {
            "title": "My Confluence Page",
            "description": "Short",
            "content_type": "how-to",
            "tags": ["Migration", "Confluence"],
        }
        body = textwrap.dedent("""\
            # My Confluence Page

            ## Overview

            This page covers the setup.

            ```
            import os
            print(os.getcwd())
            ```

            2. First step
            3. Second step
        """)
        md_file = tmp_path / "test-doc.md"
        md_file.write_text(_make_md(fm, body), encoding="utf-8")

        result = enhance_file(md_file, {}, ALLOWED_TAGS, use_llm=False)

        assert result.success
        assert result.changes  # should have multiple changes

        # Read back and verify
        text = md_file.read_text(encoding="utf-8")
        assert "```python" in text  # code block language detected
        assert "## Before you begin" in text or "## Overview" not in text  # generic heading replaced

    def test_idempotency(self, tmp_path):
        """Running enhancer twice produces the same result."""
        fm = {
            "title": "Idempotency Test",
            "description": "Testing that running the enhancer twice gives the same output consistently.",
            "content_type": "concept",
            "tags": ["Concept"],
            "product": "both",
        }
        body = textwrap.dedent("""\
            # Idempotency Test

            This feature is a powerful tool for automation.

            ## Key concepts

            Some content about concepts.

            ## Next steps

            - Do something.
        """)
        md_file = tmp_path / "idempotent.md"
        md_file.write_text(_make_md(fm, body), encoding="utf-8")

        # First pass
        enhance_file(md_file, {}, ALLOWED_TAGS, use_llm=False)
        first_pass = md_file.read_text(encoding="utf-8")

        # Second pass
        result = enhance_file(md_file, {}, ALLOWED_TAGS, use_llm=False)
        second_pass = md_file.read_text(encoding="utf-8")

        assert first_pass == second_pass

    def test_unreadable_file(self, tmp_path):
        """Handle unreadable file gracefully."""
        bad_file = tmp_path / "nonexistent.md"
        result = enhance_file(bad_file, {}, ALLOWED_TAGS)
        assert not result.success
        assert result.warnings


# ---------------------------------------------------------------------------
# TestEnhanceDirectory
# ---------------------------------------------------------------------------


class TestEnhanceDirectory:
    """Tests for enhance_directory."""

    def test_process_multiple_files(self, tmp_path):
        """Process all .md files in a directory."""
        repo = tmp_path / "repo"
        docs = repo / "docs"
        docs.mkdir(parents=True)
        (docs / "_variables.yml").write_text(
            yaml.dump({"product_name": "TestProd"}), encoding="utf-8",
        )

        target = tmp_path / "imported"
        target.mkdir()

        for i in range(3):
            fm = {"title": f"Doc {i}", "description": "x" * 60, "content_type": "how-to"}
            (target / f"doc-{i}.md").write_text(
                _make_md(fm, f"# Doc {i}\n\nThis document is about topic {i}.\n"),
                encoding="utf-8",
            )

        results = enhance_directory(target, repo, use_llm=False)

        assert len(results) == 3
        assert all(r.success for r in results)

    def test_empty_directory(self, tmp_path):
        """Handle directory with no .md files."""
        empty = tmp_path / "empty"
        empty.mkdir()
        results = enhance_directory(empty, tmp_path, use_llm=False)
        assert results == []

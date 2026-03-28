"""Tests for LLM-powered quality enhancement functions in confluence_quality_enhancer."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from confluence_quality_enhancer import (
    ESSENTIAL_SECTIONS,
    PLACEHOLDER_PATTERNS,
    _fix_code_block_verification,
    _fix_code_examples_with_llm,
    _fix_missing_sections_with_llm,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_provider(response_text: str, error: bool = False) -> MagicMock:
    """Create a mock LLM provider that returns ``response_text``."""
    provider = MagicMock()
    result = MagicMock()
    result.content = response_text
    result.error = error
    provider.generate.return_value = result
    return provider


# ---------------------------------------------------------------------------
# _fix_code_examples_with_llm
# ---------------------------------------------------------------------------


class TestFixCodeExamplesLLM:
    def test_skip_when_no_provider(self) -> None:
        lines = ["```python", "x = foo", "```"]
        out = _fix_code_examples_with_llm(lines, "how-to", [], None)
        assert out == lines

    def test_placeholder_detection(self) -> None:
        """Code blocks with placeholder patterns are detected."""
        lines = [
            "```python",
            'url = "https://example.com/api"',
            "data = {'key': 'YOUR_API_KEY'}",
            "```",
        ]
        provider = _make_provider(
            'url = "https://api.stripe.com/v1/charges"\n'
            "data = {'key': 'sk_live_abc123'}"
        )
        changes: list[str] = []
        out = _fix_code_examples_with_llm(lines, "reference", changes, provider)
        assert provider.generate.called
        assert any("replaced placeholder" in c.lower() or "LLM replaced" in c for c in changes)

    def test_no_placeholder_no_llm_call(self) -> None:
        """Clean code blocks should not trigger LLM calls."""
        lines = [
            "```python",
            'url = "https://api.stripe.com/v1/charges"',
            "amount = 2000",
            "```",
        ]
        provider = _make_provider("")
        changes: list[str] = []
        out = _fix_code_examples_with_llm(lines, "how-to", changes, provider)
        assert not provider.generate.called
        assert out == lines

    def test_block_count_mismatch_skips(self) -> None:
        """When LLM returns wrong number of blocks, changes are skipped."""
        lines = [
            "```python",
            "foo = bar",
            "```",
            "",
            "```javascript",
            "const x = 'test123'",
            "```",
        ]
        # Return only 1 block instead of 2
        provider = _make_provider("real_code = True")
        changes: list[str] = []
        out = _fix_code_examples_with_llm(lines, "how-to", changes, provider)
        # Should skip and return original
        assert out == lines
        assert any("skipped" in c.lower() for c in changes)

    def test_llm_error_returns_original(self) -> None:
        provider = _make_provider("", error=True)
        lines = ["```python", "x = foo", "```"]
        changes: list[str] = []
        out = _fix_code_examples_with_llm(lines, "how-to", changes, provider)
        assert out == lines

    def test_llm_exception_returns_original(self) -> None:
        provider = MagicMock()
        provider.generate.side_effect = RuntimeError("API down")
        lines = ["```python", "x = foo", "```"]
        changes: list[str] = []
        out = _fix_code_examples_with_llm(lines, "how-to", changes, provider)
        assert out == lines
        assert any("failed" in c.lower() for c in changes)


# ---------------------------------------------------------------------------
# _fix_missing_sections_with_llm
# ---------------------------------------------------------------------------


class TestFixMissingSectionsLLM:
    def test_skip_when_no_provider(self) -> None:
        lines = ["# My Doc", "", "Some content."]
        out = _fix_missing_sections_with_llm(lines, "how-to", "My Doc", [], None)
        assert out == lines

    def test_skip_unknown_content_type(self) -> None:
        provider = _make_provider("## New Section\n\nContent.")
        lines = ["# Doc", "", "Text."]
        changes: list[str] = []
        out = _fix_missing_sections_with_llm(lines, "release-note", "Doc", changes, provider)
        assert out == lines
        assert not provider.generate.called

    def test_adds_missing_error_handling(self) -> None:
        provider = _make_provider("## Error handling\n\nIf the request fails, retry with backoff.")
        lines = [
            "# Configure webhook",
            "",
            "## Prerequisites",
            "",
            "Install the SDK.",
            "",
            "## Next steps",
            "",
            "Deploy to production.",
        ]
        changes: list[str] = []
        out = _fix_missing_sections_with_llm(lines, "how-to", "Configure webhook", changes, provider)
        # New section should appear before "Next steps"
        joined = "\n".join(out)
        assert "## Error handling" in joined
        next_idx = next(i for i, l in enumerate(out) if "## Next steps" in l)
        error_idx = next(i for i, l in enumerate(out) if "## Error handling" in l)
        assert error_idx < next_idx
        assert any("missing sections" in c.lower() for c in changes)

    def test_skip_if_sections_present(self) -> None:
        provider = _make_provider("should not be called")
        lines = [
            "# My How-To",
            "",
            "## Error handling",
            "",
            "Handle errors here.",
            "",
            "## Next steps",
            "",
            "Continue.",
        ]
        changes: list[str] = []
        out = _fix_missing_sections_with_llm(lines, "how-to", "My How-To", changes, provider)
        assert not provider.generate.called

    def test_reference_type_sections(self) -> None:
        provider = _make_provider(
            "## Error codes\n\n| Code | Meaning |\n|---|---|\n| 400 | Bad request |\n\n"
            "## Rate limits\n\n100 requests per minute.\n\n"
            "## Authentication\n\nUse Bearer token."
        )
        lines = ["# API Reference", "", "Endpoint docs."]
        changes: list[str] = []
        out = _fix_missing_sections_with_llm(lines, "reference", "API Reference", changes, provider)
        joined = "\n".join(out)
        assert "## Error codes" in joined
        assert "## Rate limits" in joined

    def test_llm_error_returns_original(self) -> None:
        provider = _make_provider("", error=True)
        lines = ["# Doc", "", "Text."]
        out = _fix_missing_sections_with_llm(lines, "how-to", "Doc", [], provider)
        assert out == lines


# ---------------------------------------------------------------------------
# _fix_code_block_verification
# ---------------------------------------------------------------------------


class TestFixCodeBlockVerification:
    def test_correct_output_unchanged(self) -> None:
        lines = [
            "```python",
            "print(2 + 2)",
            "# Output: 4",
            "```",
        ]
        changes: list[str] = []
        out = _fix_code_block_verification(lines, changes)
        assert "# Output: 4" in out[2]
        assert not changes  # nothing to fix

    def test_wrong_output_fixed(self) -> None:
        lines = [
            "```python",
            "print(3 * 7)",
            "# Output: 14",
            "```",
        ]
        changes: list[str] = []
        out = _fix_code_block_verification(lines, changes)
        assert "21" in out[2]
        assert any("fixed" in c.lower() or "verified" in c.lower() for c in changes)

    def test_skip_do_not_execute(self) -> None:
        lines = [
            "```python",
            "# do-not-execute",
            "import some_unavailable_module",
            "# Output: something",
            "```",
        ]
        changes: list[str] = []
        out = _fix_code_block_verification(lines, changes)
        assert out == lines

    def test_skip_network_calls(self) -> None:
        lines = [
            "```python",
            "import requests",
            "resp = requests.get('https://api.example.com')",
            "# Output: 200",
            "```",
        ]
        changes: list[str] = []
        out = _fix_code_block_verification(lines, changes)
        assert out == lines

    def test_skip_subprocess_calls(self) -> None:
        lines = [
            "```python",
            "import subprocess",
            "subprocess.run(['ls'])",
            "# Output: files",
            "```",
        ]
        changes: list[str] = []
        out = _fix_code_block_verification(lines, changes)
        assert out == lines

    def test_skip_yaml_blocks(self) -> None:
        lines = [
            "```yaml",
            "key: value",
            "# Output: something",
            "```",
        ]
        changes: list[str] = []
        out = _fix_code_block_verification(lines, changes)
        assert out == lines

    def test_skip_json_blocks(self) -> None:
        lines = [
            "```json",
            '{"key": "value"}',
            "```",
        ]
        changes: list[str] = []
        out = _fix_code_block_verification(lines, changes)
        assert out == lines

    def test_no_output_comment_skipped(self) -> None:
        lines = [
            "```python",
            "x = 42",
            "print(x)",
            "```",
        ]
        changes: list[str] = []
        out = _fix_code_block_verification(lines, changes)
        assert out == lines


# ---------------------------------------------------------------------------
# Placeholder pattern coverage
# ---------------------------------------------------------------------------


class TestPlaceholderPatterns:
    @pytest.mark.parametrize("text,expected", [
        ("x = foo", True),
        ("x = bar", True),
        ("url = 'https://example.com'", True),
        ("key = 'test123'", True),
        ("token = YOUR_API_KEY", True),
        ("api_key = 'sk_live_real'", False),
        ("amount = 2000", False),
    ])
    def test_patterns(self, text: str, expected: bool) -> None:
        found = any(p.search(text) for p in PLACEHOLDER_PATTERNS)
        assert found == expected


class TestEssentialSections:
    def test_howto_has_expected(self) -> None:
        assert "error handling" in ESSENTIAL_SECTIONS["how-to"]
        assert "next steps" in ESSENTIAL_SECTIONS["how-to"]

    def test_reference_has_expected(self) -> None:
        assert "error codes" in ESSENTIAL_SECTIONS["reference"]
        assert "rate limits" in ESSENTIAL_SECTIONS["reference"]
        assert "authentication" in ESSENTIAL_SECTIONS["reference"]

    def test_concept_has_expected(self) -> None:
        assert "security considerations" in ESSENTIAL_SECTIONS["concept"]
        assert "performance implications" in ESSENTIAL_SECTIONS["concept"]

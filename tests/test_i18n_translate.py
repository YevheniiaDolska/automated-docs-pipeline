"""Tests for scripts/i18n_translate.py."""

from __future__ import annotations

import hashlib
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from i18n_utils import (
    I18nConfig,
    LanguageConfig,
    TranslationConfig,
    compute_content_hash,
    extract_frontmatter,
)
from i18n_translate import DocumentTranslator, _get_items_from_sync


def _make_config() -> I18nConfig:
    return I18nConfig(
        default_language="en",
        docs_structure="folder",
        languages=[
            LanguageConfig(locale="en", name="English"),
            LanguageConfig(locale="ru", name="Russian"),
        ],
        translation=TranslationConfig(
            model="claude-sonnet-4-20250514",
            temperature=0.3,
        ),
    )


class TestBuildTranslationPrompt:
    def test_contains_source_content(self):
        config = _make_config()
        translator = DocumentTranslator(config)

        source = "---\ntitle: Test\n---\nHello world.\n"
        prompt = translator.build_translation_prompt(source, "en", "ru", "Russian")

        assert "Hello world." in prompt
        assert "Russian" in prompt
        assert "code blocks" in prompt.lower()
        assert "{{ variable }}" in prompt

    def test_preserves_variable_syntax_instruction(self):
        config = _make_config()
        translator = DocumentTranslator(config)

        prompt = translator.build_translation_prompt(
            "Content", "en", "ru", "Russian"
        )
        # The prompt should mention preserving variables
        assert "variable" in prompt.lower()
        assert "preserve" in prompt.lower() or "DO NOT TRANSLATE" in prompt


class TestPostProcess:
    def test_sets_language_field(self):
        config = _make_config()
        translator = DocumentTranslator(config)

        translated = "---\ntitle: Test RU\n---\nContent\n"
        source = "---\ntitle: Test\n---\nOriginal content\n"

        result = translator._post_process(translated, "en", "ru", source)
        fm, _ = extract_frontmatter(result)

        assert fm["language"] == "ru"
        assert "source_hash" in fm
        assert len(fm["source_hash"]) == 64

    def test_source_hash_matches_body(self):
        config = _make_config()
        translator = DocumentTranslator(config)

        source_body = "Original content"
        source = f"---\ntitle: Test\n---\n{source_body}\n"
        translated = "---\ntitle: Test RU\n---\nTranslated\n"

        result = translator._post_process(translated, "en", "ru", source)
        fm, _ = extract_frontmatter(result)

        expected_hash = hashlib.sha256(source_body.encode("utf-8")).hexdigest()
        assert fm["source_hash"] == expected_hash


class TestTranslateDocument:
    def test_calls_anthropic_api(self):
        config = _make_config()
        translator = DocumentTranslator(config)

        # Mock the Anthropic client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text="---\ntitle: Test RU\n---\nTranslated content\n")
        ]
        mock_client.messages.create.return_value = mock_response
        translator._client = mock_client

        source = "---\ntitle: Test\n---\nOriginal content\n"
        result = translator.translate_document(source, "en", "ru", "Russian")

        # Verify API was called
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-sonnet-4-20250514"
        assert call_kwargs["temperature"] == 0.3

        # Verify result has i18n fields
        fm, _ = extract_frontmatter(result)
        assert fm["language"] == "ru"
        assert "source_hash" in fm


class TestCreateTranslationFromSource:
    def test_dry_run(self, tmp_path: Path):
        config = _make_config()
        docs = tmp_path / "docs"
        en = docs / "en" / "how-to"
        en.mkdir(parents=True)
        (en / "guide.md").write_text(
            "---\ntitle: Guide\n---\nContent\n", encoding="utf-8"
        )

        translator = DocumentTranslator(config, docs_dir=docs)
        result = translator.create_translation_from_source(
            "en/how-to/guide.md", "ru", dry_run=True
        )

        assert result is None
        assert not (docs / "ru" / "how-to" / "guide.md").exists()

    def test_missing_source(self, tmp_path: Path):
        config = _make_config()
        docs = tmp_path / "docs"
        docs.mkdir()

        translator = DocumentTranslator(config, docs_dir=docs)
        result = translator.create_translation_from_source(
            "en/missing.md", "ru"
        )
        assert result is None

    def test_writes_translation(self, tmp_path: Path):
        config = _make_config()
        docs = tmp_path / "docs"
        en = docs / "en"
        en.mkdir(parents=True)
        (en / "index.md").write_text(
            "---\ntitle: Home\n---\nWelcome\n", encoding="utf-8"
        )

        translator = DocumentTranslator(config, docs_dir=docs)

        # Mock API
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text="---\ntitle: Home RU\n---\nDobro pozhalovat\n")
        ]
        mock_client.messages.create.return_value = mock_response
        translator._client = mock_client

        result = translator.create_translation_from_source("en/index.md", "ru")

        assert result is not None
        assert result.exists()
        assert result == docs / "ru" / "index.md"

        fm, body = extract_frontmatter(result.read_text(encoding="utf-8"))
        assert fm["language"] == "ru"
        assert fm["translation_of"] == "en/index.md"
        assert "source_hash" in fm


class TestGetItemsFromSync:
    def test_returns_missing_items(self, tmp_path: Path):
        config = _make_config()
        docs = tmp_path / "docs"
        en = docs / "en"
        en.mkdir(parents=True)
        (en / "index.md").write_text(
            "---\ntitle: Home\n---\nContent\n", encoding="utf-8"
        )

        items = _get_items_from_sync(config, docs, locale="ru")
        assert len(items) == 1
        assert items[0] == ("en/index.md", "ru")

    def test_stale_only_filter(self, tmp_path: Path):
        config = _make_config()
        docs = tmp_path / "docs"
        en = docs / "en"
        en.mkdir(parents=True)
        (en / "a.md").write_text("---\ntitle: A\n---\nContent A\n", encoding="utf-8")
        (en / "b.md").write_text("---\ntitle: B\n---\nContent B\n", encoding="utf-8")

        # Create ru/a.md with correct hash, ru/b.md missing
        ru = docs / "ru"
        ru.mkdir(parents=True)
        h = compute_content_hash(en / "a.md")
        (ru / "a.md").write_text(
            f"---\ntitle: A RU\nsource_hash: {h}\n---\nTranslated A\n",
            encoding="utf-8",
        )

        # All missing returns b.md
        items = _get_items_from_sync(config, docs, locale="ru")
        assert len(items) == 1
        paths = [i[0] for i in items]
        assert "en/b.md" in paths

        # Stale only returns nothing (a is ok, b is missing not stale)
        stale = _get_items_from_sync(config, docs, locale="ru", stale_only=True)
        assert len(stale) == 0

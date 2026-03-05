"""Tests for scripts/i18n_utils.py."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

# Allow importing from scripts/
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from i18n_utils import (
    I18nConfig,
    LanguageConfig,
    TranslationConfig,
    compute_content_hash,
    deep_merge,
    extract_frontmatter,
    get_locale_from_path,
    load_i18n_config,
    load_variables_for_locale,
    set_frontmatter_field,
)


# ---------------------------------------------------------------------------
# load_i18n_config
# ---------------------------------------------------------------------------

class TestLoadI18nConfig:
    def test_loads_valid_config(self, tmp_path: Path):
        cfg_file = tmp_path / "i18n.yml"
        cfg_file.write_text(textwrap.dedent("""\
            default_language: en
            docs_structure: folder
            languages:
              - locale: en
                name: English
                build: true
              - locale: ru
                name: Russian
                build: true
                seo_overrides:
                  first_para_max_words: 80
            translation:
              stale_threshold_days: 14
              auto_translate:
                provider: anthropic
                model: claude-sonnet-4-20250514
                max_concurrency: 5
                temperature: 0.2
        """), encoding="utf-8")

        config = load_i18n_config(cfg_file)

        assert config.default_language == "en"
        assert config.docs_structure == "folder"
        assert len(config.languages) == 2
        assert config.languages[1].locale == "ru"
        assert config.languages[1].seo_overrides == {"first_para_max_words": 80}
        assert config.translation.stale_threshold_days == 14
        assert config.translation.max_concurrency == 5

    def test_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_i18n_config(tmp_path / "missing.yml")

    def test_missing_default_language_raises(self, tmp_path: Path):
        cfg = tmp_path / "i18n.yml"
        cfg.write_text("languages:\n  - locale: en\n", encoding="utf-8")
        with pytest.raises(ValueError, match="default_language"):
            load_i18n_config(cfg)

    def test_default_language_not_in_list_raises(self, tmp_path: Path):
        cfg = tmp_path / "i18n.yml"
        cfg.write_text(textwrap.dedent("""\
            default_language: fr
            languages:
              - locale: en
        """), encoding="utf-8")
        with pytest.raises(ValueError, match="not in languages"):
            load_i18n_config(cfg)

    def test_empty_languages_raises(self, tmp_path: Path):
        cfg = tmp_path / "i18n.yml"
        cfg.write_text("default_language: en\nlanguages: []\n", encoding="utf-8")
        with pytest.raises(ValueError, match="at least one"):
            load_i18n_config(cfg)


class TestI18nConfigProperties:
    def _make_config(self) -> I18nConfig:
        return I18nConfig(
            default_language="en",
            docs_structure="folder",
            languages=[
                LanguageConfig(locale="en", name="English"),
                LanguageConfig(locale="ru", name="Russian"),
                LanguageConfig(locale="de", name="German", build=False),
            ],
            translation=TranslationConfig(),
        )

    def test_locales(self):
        assert self._make_config().locales == ["en", "ru", "de"]

    def test_build_locales(self):
        assert self._make_config().build_locales == ["en", "ru"]

    def test_target_locales(self):
        assert self._make_config().target_locales == ["ru", "de"]

    def test_get_language(self):
        cfg = self._make_config()
        assert cfg.get_language("ru").name == "Russian"
        assert cfg.get_language("xx") is None


# ---------------------------------------------------------------------------
# get_locale_from_path
# ---------------------------------------------------------------------------

class TestGetLocaleFromPath:
    def test_detects_locale(self):
        assert get_locale_from_path("docs/en/how-to/guide.md", "docs") == "en"
        assert get_locale_from_path("docs/ru/index.md", "docs") == "ru"

    def test_returns_none_for_non_locale_dir(self):
        assert get_locale_from_path("docs/how-to/guide.md", "docs") is None
        assert get_locale_from_path("docs/stylesheets/custom.css", "docs") is None

    def test_returns_none_for_unrelated_path(self):
        assert get_locale_from_path("other/en/file.md", "docs") is None

    def test_path_objects(self):
        assert get_locale_from_path(Path("docs/de/ref.md"), Path("docs")) == "de"


# ---------------------------------------------------------------------------
# compute_content_hash
# ---------------------------------------------------------------------------

class TestComputeContentHash:
    def test_hash_excludes_frontmatter(self, tmp_path: Path):
        f = tmp_path / "doc.md"
        f.write_text("---\ntitle: Test\n---\nBody content here.\n", encoding="utf-8")
        h = compute_content_hash(f)
        assert len(h) == 64
        assert h == compute_content_hash(f)  # deterministic

    def test_different_body_different_hash(self, tmp_path: Path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("---\ntitle: A\n---\nBody A\n", encoding="utf-8")
        f2.write_text("---\ntitle: A\n---\nBody B\n", encoding="utf-8")
        assert compute_content_hash(f1) != compute_content_hash(f2)

    def test_same_body_same_hash(self, tmp_path: Path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("---\ntitle: A\n---\nSame body\n", encoding="utf-8")
        f2.write_text("---\ntitle: B\n---\nSame body\n", encoding="utf-8")
        assert compute_content_hash(f1) == compute_content_hash(f2)


# ---------------------------------------------------------------------------
# deep_merge
# ---------------------------------------------------------------------------

class TestDeepMerge:
    def test_flat_merge(self):
        assert deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}

    def test_override(self):
        assert deep_merge({"a": 1}, {"a": 2}) == {"a": 2}

    def test_nested_merge(self):
        base = {"env_vars": {"port": "8080", "host": "localhost"}}
        over = {"env_vars": {"port": "3000"}}
        result = deep_merge(base, over)
        assert result == {"env_vars": {"port": "3000", "host": "localhost"}}

    def test_does_not_mutate_base(self):
        base = {"a": {"b": 1}}
        deep_merge(base, {"a": {"c": 2}})
        assert base == {"a": {"b": 1}}


# ---------------------------------------------------------------------------
# load_variables_for_locale
# ---------------------------------------------------------------------------

class TestLoadVariablesForLocale:
    def test_base_only(self, tmp_path: Path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "_variables.yml").write_text(
            "product_name: TestProduct\ndefault_port: 5678\n",
            encoding="utf-8",
        )

        result = load_variables_for_locale("en", str(docs))
        assert result["product_name"] == "TestProduct"
        assert result["default_port"] == 5678

    def test_locale_override(self, tmp_path: Path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "_variables.yml").write_text(
            "product_name: TestProduct\nproduct_tagline: English tagline\n",
            encoding="utf-8",
        )
        ru_dir = docs / "ru"
        ru_dir.mkdir()
        (ru_dir / "_variables.yml").write_text(
            "product_tagline: Russian tagline\n",
            encoding="utf-8",
        )

        result = load_variables_for_locale("ru", str(docs))
        assert result["product_name"] == "TestProduct"
        assert result["product_tagline"] == "Russian tagline"

    def test_no_variables_file(self, tmp_path: Path):
        docs = tmp_path / "docs"
        docs.mkdir()
        result = load_variables_for_locale("en", str(docs))
        assert result == {}


# ---------------------------------------------------------------------------
# extract_frontmatter
# ---------------------------------------------------------------------------

class TestExtractFrontmatter:
    def test_valid(self):
        fm, body = extract_frontmatter("---\ntitle: Test\n---\nBody\n")
        assert fm == {"title": "Test"}
        assert "Body" in body

    def test_no_frontmatter(self):
        fm, body = extract_frontmatter("No frontmatter here")
        assert fm == {}
        assert body == "No frontmatter here"


# ---------------------------------------------------------------------------
# set_frontmatter_field
# ---------------------------------------------------------------------------

class TestSetFrontmatterField:
    def test_updates_field(self, tmp_path: Path):
        f = tmp_path / "doc.md"
        f.write_text("---\ntitle: Old\n---\nBody\n", encoding="utf-8")
        set_frontmatter_field(f, "language", "ru")
        fm, _ = extract_frontmatter(f.read_text(encoding="utf-8"))
        assert fm["language"] == "ru"
        assert fm["title"] == "Old"

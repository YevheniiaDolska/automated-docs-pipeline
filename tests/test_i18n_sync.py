"""Tests for scripts/i18n_sync.py."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from i18n_utils import I18nConfig, LanguageConfig, TranslationConfig, compute_content_hash
from i18n_sync import I18nSyncChecker, save_report


def _make_config(default: str = "en", targets: list[str] | None = None) -> I18nConfig:
    """Create a minimal I18nConfig for testing."""
    langs = [LanguageConfig(locale=default, name=default.upper())]
    for t in (targets or ["ru"]):
        langs.append(LanguageConfig(locale=t, name=t.upper()))
    return I18nConfig(
        default_language=default,
        docs_structure="folder",
        languages=langs,
        translation=TranslationConfig(),
    )


@pytest.fixture
def i18n_docs(tmp_path: Path) -> Path:
    """Create a docs tree with en source and partial ru translation."""
    docs = tmp_path / "docs"

    # Source docs
    en = docs / "en"
    en.mkdir(parents=True)
    (en / "index.md").write_text(
        "---\ntitle: Home\ndescription: Home page description text\ncontent_type: concept\n---\nWelcome to the docs.\n",
        encoding="utf-8",
    )
    howto = en / "how-to"
    howto.mkdir()
    (howto / "guide.md").write_text(
        "---\ntitle: Guide\ndescription: A guide description text\ncontent_type: how-to\n---\nStep 1: Do something.\n",
        encoding="utf-8",
    )

    # Russian translations (partial)
    ru = docs / "ru"
    ru.mkdir(parents=True)
    source_hash = compute_content_hash(en / "index.md")
    (ru / "index.md").write_text(
        f"---\ntitle: Home RU\nlanguage: ru\ntranslation_of: en/index.md\nsource_hash: {source_hash}\n---\nDobro pozhalovat.\n",
        encoding="utf-8",
    )
    # guide.md is missing in ru -> should be detected as missing

    return docs


class TestI18nSyncChecker:
    def test_detects_missing_translation(self, i18n_docs: Path):
        config = _make_config()
        checker = I18nSyncChecker(config, docs_dir=i18n_docs)
        report = checker.check_all()

        assert report.total_source_docs == 2

        statuses = {item.target_path: item.status for item in report.items}
        assert statuses["ru/index.md"] == "ok"
        assert statuses["ru/how-to/guide.md"] == "missing"

    def test_detects_stale_translation(self, i18n_docs: Path):
        # Modify source to make translation stale
        source = i18n_docs / "en" / "index.md"
        source.write_text(
            "---\ntitle: Home\ndescription: Home page description text\ncontent_type: concept\n---\nUpdated welcome content!\n",
            encoding="utf-8",
        )

        config = _make_config()
        checker = I18nSyncChecker(config, docs_dir=i18n_docs)
        report = checker.check_all()

        statuses = {item.target_path: item.status for item in report.items}
        assert statuses["ru/index.md"] == "stale"

    def test_stale_when_no_source_hash(self, i18n_docs: Path):
        # Remove source_hash from translation
        ru_index = i18n_docs / "ru" / "index.md"
        ru_index.write_text(
            "---\ntitle: Home RU\nlanguage: ru\n---\nContent\n",
            encoding="utf-8",
        )

        config = _make_config()
        checker = I18nSyncChecker(config, docs_dir=i18n_docs)
        report = checker.check_all()

        statuses = {item.target_path: item.status for item in report.items}
        assert statuses["ru/index.md"] == "stale"

    def test_coverage_calculation(self, i18n_docs: Path):
        config = _make_config()
        checker = I18nSyncChecker(config, docs_dir=i18n_docs)
        report = checker.check_all()

        ru_cov = report.coverage["ru"]
        assert ru_cov["total_source_docs"] == 2
        assert ru_cov["translated"] == 1
        assert ru_cov["missing"] == 1
        assert ru_cov["coverage_pct"] == 50.0

    def test_multiple_target_locales(self, i18n_docs: Path):
        config = _make_config(targets=["ru", "de"])
        checker = I18nSyncChecker(config, docs_dir=i18n_docs)
        report = checker.check_all()

        # 2 source docs * 2 targets = 4 items
        assert len(report.items) == 4
        assert "ru" in report.coverage
        assert "de" in report.coverage
        assert report.coverage["de"]["missing"] == 2

    def test_no_source_docs(self, tmp_path: Path):
        docs = tmp_path / "docs"
        (docs / "en").mkdir(parents=True)
        config = _make_config()
        checker = I18nSyncChecker(config, docs_dir=docs)
        report = checker.check_all()
        assert report.total_source_docs == 0
        assert len(report.items) == 0


class TestSaveReport:
    def test_saves_valid_json(self, i18n_docs: Path, tmp_path: Path):
        config = _make_config()
        checker = I18nSyncChecker(config, docs_dir=i18n_docs)
        report = checker.check_all()

        out = tmp_path / "report.json"
        save_report(report, out)

        data = json.loads(out.read_text(encoding="utf-8"))
        assert "generated_at" in data
        assert "coverage" in data
        assert "items" in data
        assert len(data["items"]) == 2

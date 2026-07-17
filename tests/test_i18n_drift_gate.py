"""Tests for scripts/i18n_drift_gate.py."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from i18n_utils import I18nConfig, LanguageConfig, TranslationConfig
from i18n_drift_gate import (
    DRIFT_STATUSES,
    build_findings,
    run_gate,
    save_report,
)
from i18n_sync import TranslationStatus


_FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n?", re.DOTALL)


def _make_config(default: str = "en", targets: list[str] | None = None) -> I18nConfig:
    """Create a minimal I18nConfig for testing.

    An explicit empty `targets` list means "no target locales" and must be
    distinguished from None, which means "use the default".
    """
    if targets is None:
        targets = ["ru"]
    langs = [LanguageConfig(locale=default, name=default.upper())]
    for t in targets:
        langs.append(LanguageConfig(locale=t, name=t.upper()))
    return I18nConfig(
        default_language=default,
        docs_structure="folder",
        languages=langs,
        translation=TranslationConfig(),
    )


def _body_hash(text: str) -> str:
    """Hash a document body the way the pipeline does."""
    body = _FRONTMATTER_RE.sub("", text, count=1).strip()
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _write_source(docs: Path, rel: str, body: str = "Original body.") -> str:
    """Write an English source doc and return its body hash."""
    path = docs / "en" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    text = textwrap.dedent(f"""\
        ---
        title: "Source"
        description: "A source document used by the drift gate tests."
        content_type: how-to
        ---

        # Source

        {body}
        """)
    path.write_text(text, encoding="utf-8")
    return _body_hash(text)


def _write_translation(docs: Path, rel: str, locale: str, source_hash: str) -> Path:
    """Write a translation claiming to match the given source hash."""
    path = docs / locale / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    text = textwrap.dedent(f"""\
        ---
        title: "Перевод"
        description: "Переведенный документ для тестов."
        content_type: how-to
        language: {locale}
        translation_of: en/{rel}
        source_hash: {source_hash}
        ---

        # Перевод

        Переведенное содержимое.
        """)
    path.write_text(text, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Gate behavior
# ---------------------------------------------------------------------------

def test_in_sync_translation_produces_no_drift(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    source_hash = _write_source(docs, "guide.md")
    _write_translation(docs, "guide.md", "ru", source_hash)

    report = run_gate(_make_config(), docs)

    assert not report.has_drift
    assert report.total_findings == 0
    assert report.findings_by_locale["ru"]["total"] == 0


def test_source_change_immediately_flags_translation(tmp_path: Path) -> None:
    """The gate must fire on the change itself, not on a schedule."""
    docs = tmp_path / "docs"
    source_hash = _write_source(docs, "guide.md", body="Original body.")
    _write_translation(docs, "guide.md", "ru", source_hash)

    assert not run_gate(_make_config(), docs).has_drift

    # The English page changes. Nothing else happens: no re-run of any
    # scheduled job, no date rolling over.
    _write_source(docs, "guide.md", body="Body with a new retry limit of 3.")

    report = run_gate(_make_config(), docs)

    assert report.has_drift
    assert report.total_findings == 1
    finding = report.findings[0]
    assert finding.status == "stale"
    assert finding.target_locale == "ru"
    assert finding.severity == "error"


def test_missing_translation_is_reported_per_locale(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    _write_source(docs, "guide.md")

    report = run_gate(_make_config(targets=["ru", "de"]), docs)

    assert report.total_findings == 2
    assert {f.target_locale for f in report.findings} == {"ru", "de"}
    assert all(f.status == "missing" for f in report.findings)


def test_stale_outranks_missing_in_severity(tmp_path: Path) -> None:
    """A stale page reads as authoritative and is silently wrong.

    A missing page falls back to English, so the reader knows what they got.
    """
    docs = tmp_path / "docs"
    source_hash = _write_source(docs, "stale.md")
    _write_translation(docs, "stale.md", "ru", source_hash)
    _write_source(docs, "stale.md", body="Changed.")
    _write_source(docs, "absent.md")

    report = run_gate(_make_config(), docs)

    by_status = {f.status: f for f in report.findings}
    assert by_status["stale"].severity == "error"
    assert by_status["missing"].severity == "warning"


def test_translation_without_source_hash_is_drift(tmp_path: Path) -> None:
    """An unverifiable translation must not pass as fresh."""
    docs = tmp_path / "docs"
    _write_source(docs, "guide.md")
    path = docs / "ru" / "guide.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\ntitle: 'Перевод'\nlanguage: ru\n---\n\n# Перевод\n",
        encoding="utf-8",
    )

    report = run_gate(_make_config(), docs)

    assert report.has_drift
    assert report.findings[0].status == "stale"


def test_missing_translation_does_not_block_by_default(tmp_path: Path) -> None:
    """A repo with pre-existing untranslated pages must be able to adopt this.

    A gate that fails every pull request on day one over coverage gaps gets
    switched off, and then it catches the drift it existed to catch.
    """
    docs = tmp_path / "docs"
    _write_source(docs, "never-translated.md")

    report = run_gate(_make_config(), docs, strict=True)

    assert report.has_drift
    assert not report.has_blocking
    assert report.total_warnings == 1
    assert report.total_errors == 0


def test_stale_translation_blocks_by_default(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    source_hash = _write_source(docs, "guide.md")
    _write_translation(docs, "guide.md", "ru", source_hash)
    _write_source(docs, "guide.md", body="Changed.")

    report = run_gate(_make_config(), docs, strict=True)

    assert report.has_blocking
    assert report.total_errors == 1


def test_fail_on_any_also_blocks_missing_translations(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    _write_source(docs, "never-translated.md")

    report = run_gate(_make_config(), docs, strict=True, fail_on="any")

    assert report.has_blocking


def test_clean_tree_never_blocks(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    source_hash = _write_source(docs, "guide.md")
    _write_translation(docs, "guide.md", "ru", source_hash)

    for fail_on in ("error", "any"):
        report = run_gate(_make_config(), docs, strict=True, fail_on=fail_on)
        assert not report.has_blocking


def test_no_target_locales_yields_no_findings(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    _write_source(docs, "guide.md")

    report = run_gate(_make_config(targets=[]), docs)

    assert not report.has_drift
    assert report.locales == []


# ---------------------------------------------------------------------------
# Scoping
# ---------------------------------------------------------------------------

def test_build_findings_respects_scope() -> None:
    """Changed-only mode must gate exactly the touched source docs."""
    items = [
        TranslationStatus(
            source_path="en/touched.md",
            target_locale="ru",
            target_path="ru/touched.md",
            status="stale",
        ),
        TranslationStatus(
            source_path="en/untouched.md",
            target_locale="ru",
            target_path="ru/untouched.md",
            status="stale",
        ),
    ]

    findings = build_findings(items, scope={"en/touched.md"})

    assert len(findings) == 1
    assert findings[0].source_path == "en/touched.md"


def test_build_findings_without_scope_returns_all() -> None:
    items = [
        TranslationStatus(
            source_path="en/a.md",
            target_locale="ru",
            target_path="ru/a.md",
            status="missing",
        ),
        TranslationStatus(
            source_path="en/b.md",
            target_locale="ru",
            target_path="ru/b.md",
            status="ok",
        ),
    ]

    findings = build_findings(items, scope=None)

    assert len(findings) == 1
    assert findings[0].status == "missing"


def test_ok_is_the_only_clean_status() -> None:
    assert "ok" not in DRIFT_STATUSES
    assert set(DRIFT_STATUSES) == {"missing", "stale"}


# ---------------------------------------------------------------------------
# Report output
# ---------------------------------------------------------------------------

def test_findings_carry_actionable_remediation(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    _write_source(docs, "guide.md")

    report = run_gate(_make_config(), docs)

    remediation = report.findings[0].remediation
    assert "i18n:translate" in remediation
    assert "--locale ru" in remediation


def test_save_report_writes_readable_json(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    _write_source(docs, "guide.md")
    report = run_gate(_make_config(), docs, strict=True)

    out = tmp_path / "reports" / "i18n_drift_report.json"
    save_report(report, out)

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["total_findings"] == 1
    assert data["strict"] is True
    assert data["mode"] == "full-scan"
    assert data["findings"][0]["target_locale"] == "ru"

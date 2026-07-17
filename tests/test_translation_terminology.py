"""Tests for scripts/validate_translation_terminology.py."""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from validate_translation_terminology import (
    extract_prose,
    load_locale_rules,
    print_findings,
    run_validation,
    save_report,
    term_appears_in_source,
)


GLOSSARY = textwrap.dedent("""\
    terms:
      retry:
        description: Automatic re-execution after failure
        aliases:
        - auto-retry
        locales:
          ru:
            preferred: повторная попытка
            match:
            - повторн
            forbidden:
            - stem: перезапуск
              reason: Means "restart" - re-runs the whole workflow, not one node
            risk: high
      item:
        description: A single data object passed between nodes
        aliases:
        - record
        locales:
          ru:
            preferred: элемент
            match:
            - элемент
            forbidden:
            - stem: товар
              reason: Means "merchandise" - a commerce false friend
            risk: high
      workflow:
        description: A sequence of connected nodes
        aliases:
        - flow
    """)


def _write_glossary(tmp_path: Path, content: str = GLOSSARY) -> Path:
    path = tmp_path / "glossary.yml"
    path.write_text(content, encoding="utf-8")
    return path


def _write_source(docs: Path, rel: str, body: str) -> None:
    path = docs / "en" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        textwrap.dedent(f"""\
            ---
            title: "Source"
            description: "Source document for terminology tests."
            content_type: how-to
            ---

            # Source

            {body}
            """),
        encoding="utf-8",
    )


def _write_translation(docs: Path, rel: str, body: str, source_rel: str = "") -> None:
    path = docs / "ru" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    translation_of = source_rel or f"en/{rel}"
    path.write_text(
        textwrap.dedent(f"""\
            ---
            title: "Перевод"
            description: "Переведенный документ."
            content_type: how-to
            language: ru
            translation_of: {translation_of}
            source_hash: abc123
            ---

            # Перевод

            {body}
            """),
        encoding="utf-8",
    )


def _validate(tmp_path: Path):
    rules = load_locale_rules(_write_glossary(tmp_path))
    return run_validation(tmp_path / "docs", rules, ["ru"], [])


# ---------------------------------------------------------------------------
# Glossary loading
# ---------------------------------------------------------------------------

def test_only_terms_with_locale_rules_are_loaded(tmp_path: Path) -> None:
    """Terms without a locales block are not enforced.

    Verifying every term does not scale; verifying the risky ones does.
    """
    rules = load_locale_rules(_write_glossary(tmp_path))

    assert set(rules) == {"ru"}
    assert {r.term for r in rules["ru"]} == {"retry", "item"}


def test_locale_rule_requires_preferred_rendering(tmp_path: Path) -> None:
    path = tmp_path / "glossary.yml"
    path.write_text(
        "terms:\n  retry:\n    locales:\n      ru:\n        match: [повторн]\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="requires a 'preferred' rendering"):
        load_locale_rules(path)


def test_forbidden_entries_must_declare_a_stem(tmp_path: Path) -> None:
    path = tmp_path / "glossary.yml"
    path.write_text(
        textwrap.dedent("""\
            terms:
              retry:
                locales:
                  ru:
                    preferred: повторная попытка
                    forbidden:
                    - перезапуск
            """),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must be mappings with a 'stem' key"):
        load_locale_rules(path)


def test_match_defaults_to_the_preferred_rendering(tmp_path: Path) -> None:
    path = tmp_path / "glossary.yml"
    path.write_text(
        textwrap.dedent("""\
            terms:
              retry:
                locales:
                  ru:
                    preferred: Повторная Попытка
            """),
        encoding="utf-8",
    )

    rules = load_locale_rules(path)

    assert rules["ru"][0].match == ["повторная попытка"]


def test_missing_glossary_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_locale_rules(tmp_path / "nope.yml")


# ---------------------------------------------------------------------------
# The core case: fluent output that means the wrong thing
# ---------------------------------------------------------------------------

def test_fluent_mistranslation_is_an_error(tmp_path: Path) -> None:
    """The sentence parses and reads naturally, and states the wrong thing."""
    docs = tmp_path / "docs"
    _write_source(docs, "guide.md", "When a node fails, retry re-executes it.")
    _write_translation(
        docs, "guide.md", "Когда узел завершается с ошибкой, перезапуск выполняет его снова."
    )

    report = _validate(tmp_path)

    errors = [f for f in report.findings if f.severity == "error"]
    assert len(errors) == 1
    assert errors[0].term == "retry"
    assert errors[0].rule == "forbidden-rendering"
    assert "restart" in errors[0].message
    assert "повторная попытка" in errors[0].remediation


def test_correct_translation_passes_clean(tmp_path: Path) -> None:
    """No false positives, or the gate becomes noise people learn to skip."""
    docs = tmp_path / "docs"
    _write_source(docs, "guide.md", "Retry re-runs the node. Each item is kept.")
    _write_translation(
        docs,
        "guide.md",
        "Повторная попытка выполняет узел заново. Каждый элемент сохраняется.",
    )

    report = _validate(tmp_path)

    assert report.findings == []
    assert report.total_errors == 0


def test_inflected_forms_count_as_correct(tmp_path: Path) -> None:
    """Russian declines; stem matching must not punish grammar."""
    docs = tmp_path / "docs"
    _write_source(docs, "guide.md", "Configure retry for each item.")
    _write_translation(
        docs,
        "guide.md",
        "Настройте повторные попытки для каждого элемента.",
    )

    report = _validate(tmp_path)

    assert report.total_errors == 0
    assert report.total_warnings == 0


def test_missing_approved_rendering_is_a_warning_not_an_error(tmp_path: Path) -> None:
    """A rephrasing may be legitimate, so a human decides rather than the gate."""
    docs = tmp_path / "docs"
    _write_source(docs, "guide.md", "Configure retry behavior.")
    _write_translation(docs, "guide.md", "Настройте поведение узла при сбое.")

    report = _validate(tmp_path)

    assert report.total_errors == 0
    assert report.total_warnings == 1
    assert report.findings[0].rule == "missing-approved-rendering"


def test_terms_absent_from_the_source_are_not_checked(tmp_path: Path) -> None:
    """A term the English page never uses cannot have been mistranslated here."""
    docs = tmp_path / "docs"
    _write_source(docs, "guide.md", "This page describes workflows only.")
    _write_translation(docs, "guide.md", "На этой странице описаны рабочие процессы.")

    report = _validate(tmp_path)

    assert report.findings == []


def test_multiple_terms_are_reported_independently(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    _write_source(docs, "guide.md", "Retry re-runs the node for each item.")
    _write_translation(
        docs, "guide.md", "Перезапуск выполняет узел для каждого товара."
    )

    report = _validate(tmp_path)

    errors = {f.term for f in report.findings if f.severity == "error"}
    assert errors == {"retry", "item"}


# ---------------------------------------------------------------------------
# Prose extraction
# ---------------------------------------------------------------------------

def test_code_blocks_are_not_treated_as_prose() -> None:
    """A term inside a code sample is not a translation of anything."""
    text = "Prose here.\n\n```python\nretry = 'перезапуск'\n```\n"

    prose = extract_prose(text)

    assert "перезапуск" not in prose
    assert "prose here" in prose


def test_inline_code_and_variables_are_stripped() -> None:
    text = "Use `перезапуск` with {{ товар }} now."

    prose = extract_prose(text)

    assert "перезапуск" not in prose
    assert "товар" not in prose
    assert "now" in prose


def test_link_targets_are_stripped_but_link_text_is_kept() -> None:
    text = "See [элемент](/ru/товар/page.md) for details."

    prose = extract_prose(text)

    assert "элемент" in prose
    assert "товар" not in prose


def test_frontmatter_is_excluded_from_prose() -> None:
    text = "---\ntitle: перезапуск\n---\n\nBody text.\n"

    prose = extract_prose(text)

    assert "перезапуск" not in prose
    assert "body text" in prose


def test_term_matching_is_word_boundary_aware() -> None:
    assert term_appears_in_source("retry", "configure retry now")
    assert not term_appears_in_source("retry", "no such word here")
    # "item" must not match inside "omitted"
    assert not term_appears_in_source("item", "this value is omitted")


@pytest.mark.parametrize("prose", [
    "configure retry now",
    "configure retries now",
    "the node retried twice",
    "the node is retrying",
])
def test_consonant_y_terms_match_their_inflections(prose: str) -> None:
    """"retry" is not a prefix of "retries", so \\w* alone misses the term.

    Missing the term in the source silently skips its check, and the page
    then reports clean for the wrong reason.
    """
    assert term_appears_in_source("retry", prose)


@pytest.mark.parametrize("term,prose", [
    ("item", "each item is kept"),
    ("item", "all items are kept"),
    ("trigger", "the trigger fires"),
    ("trigger", "the workflow is triggered"),
    ("credential", "store the credentials"),
    ("binary data", "binary data is attached"),
])
def test_regular_inflections_match(term: str, prose: str) -> None:
    assert term_appears_in_source(term, prose)


def test_source_using_an_inflected_term_is_still_checked(tmp_path: Path) -> None:
    """End-to-end guard for the inflection gap: source says "retries"."""
    docs = tmp_path / "docs"
    _write_source(docs, "guide.md", "The node retries automatically on failure.")
    _write_translation(docs, "guide.md", "Узел выполняет перезапуск автоматически.")

    report = _validate(tmp_path)

    errors = [f for f in report.findings if f.severity == "error"]
    assert len(errors) == 1
    assert errors[0].term == "retry"


# ---------------------------------------------------------------------------
# Traceability
# ---------------------------------------------------------------------------

def test_translation_without_translation_of_is_flagged(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    path = docs / "ru" / "orphan.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\ntitle: 'Перевод'\nlanguage: ru\n---\n\n# Перевод\n",
        encoding="utf-8",
    )

    report = _validate(tmp_path)

    assert report.findings[0].rule == "missing-translation-of"
    assert report.findings[0].severity == "warning"


def test_translation_pointing_at_a_missing_source_is_an_error(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    _write_translation(docs, "guide.md", "Текст.", source_rel="en/gone.md")

    report = _validate(tmp_path)

    assert report.findings[0].rule == "source-not-found"
    assert report.findings[0].severity == "error"


def test_quiet_output_still_names_the_term_and_the_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The pre-commit hook runs with --quiet.

    Failing without naming the term and file leaves the developer nothing to
    act on, and a gate nobody can act on gets removed.
    """
    docs = tmp_path / "docs"
    _write_source(docs, "guide.md", "Retry re-runs the node.")
    _write_translation(docs, "guide.md", "Перезапуск выполняет узел заново.")
    report = _validate(tmp_path)

    print_findings(report)

    out = capsys.readouterr().out
    assert "guide.md" in out
    assert "перезапуск" in out
    assert "повторная попытка" in out
    assert "ERROR" in out


def test_save_report_round_trips_non_ascii(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    _write_source(docs, "guide.md", "Retry re-runs the node.")
    _write_translation(docs, "guide.md", "Перезапуск выполняет узел заново.")
    report = _validate(tmp_path)

    out = tmp_path / "reports" / "terminology.json"
    save_report(report, out)

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["total_errors"] == 1
    assert "повторная попытка" in data["findings"][0]["remediation"]

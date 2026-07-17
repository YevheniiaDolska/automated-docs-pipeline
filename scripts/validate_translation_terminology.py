#!/usr/bin/env python3
"""
Translation Terminology Validator

Context-aware verification of technical terminology in translated documents.

AI translation handles grammar well and context poorly. A term with one
precise English meaning can render into a phrase that means something
subtly different, while the sentence still parses and still reads naturally
to a fluent speaker who is not the engineer who understands the system. No
grammar checker catches this, because nothing is grammatically wrong.

This validator does not attempt to verify whole translations. It verifies
the specific terms where a meaning shift actually matters -- the ones
carrying a `locales` block in glossary.yml -- which is a much smaller and
more tractable problem.

For each glossary term that appears in the English source, the matching
translation must:

  - contain at least one approved rendering (`match` stems), and
  - contain none of the known-wrong renderings (`forbidden` stems).

A forbidden rendering is an error: it is a term that reads fluently and
means the wrong thing. A missing approved rendering is a warning: the
translator may have legitimately rephrased the sentence, so a human decides.

Usage:
    # Validate every translation
    python3 scripts/validate_translation_terminology.py

    # Validate one locale, failing the build on errors
    python3 scripts/validate_translation_terminology.py --locale ru --strict

    # Validate specific files (pre-commit usage)
    python3 scripts/validate_translation_terminology.py docs/ru/how-to/guide.md

Exit codes:
    0  No errors (warnings may be present), or no errors with --strict off.
    1  Terminology errors found with --strict enabled.
    2  Configuration or invocation error.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from i18n_utils import (
    extract_frontmatter,
    get_locale_from_path,
    load_i18n_config,
)


EXIT_OK = 0
EXIT_ERRORS = 1
EXIT_ERROR = 2

# This validator is the one script in the pipeline that must print non-English
# text: a finding is unreadable without the term it is about. Windows consoles
# default to a legacy code page (cp1251) that cannot encode most target
# languages, which turns findings into mojibake or raises UnicodeEncodeError.
# Force UTF-8 on the streams this script owns.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

# Strip these before matching prose, so a term inside a code sample or a
# variable placeholder never counts as a translation.
_FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
_VARIABLE_RE = re.compile(r"\{\{.*?\}\}", re.DOTALL)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_LINK_TARGET_RE = re.compile(r"\]\([^)]*\)")
_FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n?", re.DOTALL)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ForbiddenRule:
    """A known-wrong rendering of a term in a specific locale."""
    stem: str
    reason: str


@dataclass
class LocaleRule:
    """Terminology rules for one term in one locale."""
    term: str
    locale: str
    preferred: str
    match: list[str] = field(default_factory=list)
    forbidden: list[ForbiddenRule] = field(default_factory=list)
    risk: str = "medium"


@dataclass
class TerminologyFinding:
    """A single terminology problem in a translated document."""
    target_path: str
    source_path: str
    locale: str
    term: str
    rule: str
    severity: str
    risk: str
    message: str
    remediation: str


@dataclass
class TerminologyReport:
    """Full terminology validation result."""
    generated_at: str
    docs_checked: int = 0
    terms_with_rules: int = 0
    locales: list[str] = field(default_factory=list)
    total_errors: int = 0
    total_warnings: int = 0
    findings: list[TerminologyFinding] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Glossary loading
# ---------------------------------------------------------------------------

def load_locale_rules(glossary_path: str | Path) -> dict[str, list[LocaleRule]]:
    """Load per-locale terminology rules from the glossary.

    Args:
        glossary_path: Path to glossary.yml.

    Returns:
        Mapping of locale code to the rules defined for that locale.

    Raises:
        FileNotFoundError: If the glossary does not exist.
        ValueError: If the glossary is malformed.
    """
    path = Path(glossary_path)
    if not path.exists():
        raise FileNotFoundError(f"Glossary not found: {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("glossary.yml must be a YAML mapping")

    terms = raw.get("terms", {})
    if not isinstance(terms, dict):
        raise ValueError("glossary.yml: 'terms' must be a mapping")

    rules: dict[str, list[LocaleRule]] = {}

    for term, entry in terms.items():
        if not isinstance(entry, dict):
            continue
        locales = entry.get("locales")
        if not isinstance(locales, dict):
            continue

        for locale, spec in locales.items():
            if not isinstance(spec, dict):
                raise ValueError(
                    f"glossary.yml: terms.{term}.locales.{locale} must be a mapping"
                )

            preferred = str(spec.get("preferred", "")).strip()
            if not preferred:
                raise ValueError(
                    f"glossary.yml: terms.{term}.locales.{locale} "
                    "requires a 'preferred' rendering"
                )

            match_stems = [
                str(stem).strip().lower()
                for stem in spec.get("match", [preferred])
                if str(stem).strip()
            ]

            forbidden: list[ForbiddenRule] = []
            for item in spec.get("forbidden", []) or []:
                if not isinstance(item, dict) or "stem" not in item:
                    raise ValueError(
                        f"glossary.yml: terms.{term}.locales.{locale}.forbidden "
                        "entries must be mappings with a 'stem' key"
                    )
                forbidden.append(ForbiddenRule(
                    stem=str(item["stem"]).strip().lower(),
                    reason=str(item.get("reason", "")).strip()
                    or "Known incorrect rendering",
                ))

            rules.setdefault(locale, []).append(LocaleRule(
                term=term,
                locale=locale,
                preferred=preferred,
                match=match_stems,
                forbidden=forbidden,
                risk=str(spec.get("risk", "medium")).strip().lower(),
            ))

    return rules


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_prose(text: str) -> str:
    """Reduce a Markdown document to lowercase prose.

    Removes frontmatter, fenced and inline code, {{ variables }}, HTML tags,
    and link targets, so terminology matching only ever sees translatable
    prose. Matching inside a code sample would produce findings that no
    translator can act on.

    Args:
        text: Full Markdown document content.

    Returns:
        Lowercased prose with non-translatable regions removed.
    """
    body = _FRONTMATTER_RE.sub("", text, count=1)
    body = _FENCED_CODE_RE.sub(" ", body)
    body = _INLINE_CODE_RE.sub(" ", body)
    body = _VARIABLE_RE.sub(" ", body)
    body = _HTML_TAG_RE.sub(" ", body)
    body = _LINK_TARGET_RE.sub("] ", body)
    return body.lower()


def _source_term_pattern(term: str) -> str:
    """Build a regex matching a glossary term and its English inflections.

    A trailing `\\w*` covers regular inflection ("item" -> "items",
    "trigger" -> "triggered"). It does not cover the consonant + y class,
    where the stem itself changes: "retry" is not a prefix of "retries". That
    class is handled explicitly, because failing to match the term in the
    source silently skips the check for it, which is the worst outcome
    available -- a page reports clean precisely because the term was missed.

    Args:
        term: The glossary term, any case.

    Returns:
        A regex pattern string.
    """
    term = term.lower()
    if len(term) > 1 and term.endswith("y") and term[-2] not in "aeiou":
        # retry -> retry, retries, retried, retrying
        return r"\b" + re.escape(term[:-1]) + r"(?:y|ies|ied|ying)\b"
    return r"\b" + re.escape(term) + r"\w*"


def term_appears_in_source(term: str, source_prose: str) -> bool:
    """Check whether a glossary term is used in the English source.

    Args:
        term: The glossary term.
        source_prose: Lowercased English prose.

    Returns:
        True if the term or an inflected form appears as a whole word.
    """
    return re.search(_source_term_pattern(term), source_prose) is not None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_document(
    target_path: Path,
    docs_dir: Path,
    rules: list[LocaleRule],
    locale: str,
) -> list[TerminologyFinding]:
    """Validate terminology in a single translated document.

    Args:
        target_path: Path to the translated document.
        docs_dir: Documentation root directory.
        rules: Locale rules to apply.
        locale: Target locale code.

    Returns:
        Findings for this document.
    """
    findings: list[TerminologyFinding] = []

    target_text = target_path.read_text(encoding="utf-8")
    fm, _ = extract_frontmatter(target_text)

    source_rel = str(fm.get("translation_of", "")).strip()
    if not source_rel:
        findings.append(TerminologyFinding(
            target_path=target_path.as_posix(),
            source_path="",
            locale=locale,
            term="",
            rule="missing-translation-of",
            severity="warning",
            risk="medium",
            message=(
                "Translation has no 'translation_of' in frontmatter, so its "
                "source cannot be resolved and its terminology cannot be verified"
            ),
            remediation=(
                "Add 'translation_of: <source path relative to docs/>' "
                "to the frontmatter"
            ),
        ))
        return findings

    source_path = docs_dir / source_rel
    if not source_path.exists():
        findings.append(TerminologyFinding(
            target_path=target_path.as_posix(),
            source_path=source_rel,
            locale=locale,
            term="",
            rule="source-not-found",
            severity="error",
            risk="high",
            message=(
                f"Translation claims to translate '{source_rel}', "
                "which does not exist"
            ),
            remediation=(
                "Fix 'translation_of' in the frontmatter, or remove the "
                "orphaned translation"
            ),
        ))
        return findings

    source_prose = extract_prose(source_path.read_text(encoding="utf-8"))
    target_prose = extract_prose(target_text)

    for rule in rules:
        # Only verify terms the English page actually uses. A term the source
        # never mentions cannot have been mistranslated here.
        if not term_appears_in_source(rule.term, source_prose):
            continue

        for forbidden in rule.forbidden:
            if forbidden.stem in target_prose:
                findings.append(TerminologyFinding(
                    target_path=target_path.as_posix(),
                    source_path=source_rel,
                    locale=locale,
                    term=rule.term,
                    rule="forbidden-rendering",
                    severity="error",
                    risk=rule.risk,
                    message=(
                        f"'{rule.term}' appears to be rendered as "
                        f"'{forbidden.stem}'. {forbidden.reason}"
                    ),
                    remediation=(
                        f"Use '{rule.preferred}' for '{rule.term}' "
                        f"in {locale}"
                    ),
                ))

        if rule.match and not any(stem in target_prose for stem in rule.match):
            findings.append(TerminologyFinding(
                target_path=target_path.as_posix(),
                source_path=source_rel,
                locale=locale,
                term=rule.term,
                rule="missing-approved-rendering",
                severity="warning",
                risk=rule.risk,
                message=(
                    f"The source uses '{rule.term}', but no approved {locale} "
                    f"rendering appears in the translation "
                    f"(expected one of: {', '.join(rule.match)})"
                ),
                remediation=(
                    f"Confirm '{rule.term}' is rendered as '{rule.preferred}', "
                    "or accept the rephrasing if the meaning is preserved"
                ),
            ))

    return findings


def collect_targets(
    docs_dir: Path,
    locales: list[str],
    explicit_paths: list[str],
    only_locale: str = "",
) -> list[tuple[Path, str]]:
    """Collect translated documents to validate.

    Args:
        docs_dir: Documentation root directory.
        locales: Configured target locales.
        explicit_paths: Specific file paths passed on the command line.
        only_locale: Restrict to a single locale, or "" for all.

    Returns:
        List of (path, locale) pairs.
    """
    targets: list[tuple[Path, str]] = []

    if explicit_paths:
        for raw in explicit_paths:
            path = Path(raw)
            if not path.is_file() or path.suffix != ".md":
                continue
            locale = get_locale_from_path(path, docs_dir)
            if not locale or locale not in locales:
                continue
            if only_locale and locale != only_locale:
                continue
            targets.append((path, locale))
        return targets

    for locale in locales:
        if only_locale and locale != only_locale:
            continue
        locale_dir = docs_dir / locale
        if not locale_dir.is_dir():
            continue
        for path in sorted(locale_dir.rglob("*.md")):
            if path.name.startswith("_"):
                continue
            targets.append((path, locale))

    return targets


def run_validation(
    docs_dir: Path,
    rules_by_locale: dict[str, list[LocaleRule]],
    target_locales: list[str],
    explicit_paths: list[str],
    only_locale: str = "",
) -> TerminologyReport:
    """Validate terminology across translated documents.

    Args:
        docs_dir: Documentation root directory.
        rules_by_locale: Locale rules loaded from the glossary.
        target_locales: Configured target locales.
        explicit_paths: Specific paths to validate, or empty for a full scan.
        only_locale: Restrict to a single locale, or "" for all.

    Returns:
        TerminologyReport with all findings.
    """
    targets = collect_targets(
        docs_dir, target_locales, explicit_paths, only_locale
    )

    findings: list[TerminologyFinding] = []
    for path, locale in targets:
        rules = rules_by_locale.get(locale, [])
        if not rules:
            continue
        findings.extend(validate_document(path, docs_dir, rules, locale))

    total_rules = sum(len(r) for r in rules_by_locale.values())

    return TerminologyReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        docs_checked=len(targets),
        terms_with_rules=total_rules,
        locales=sorted(rules_by_locale.keys()),
        total_errors=sum(1 for f in findings if f.severity == "error"),
        total_warnings=sum(1 for f in findings if f.severity == "warning"),
        findings=findings,
    )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def save_report(report: TerminologyReport, output_path: str | Path) -> Path:
    """Save the terminology report as JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(report), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def print_findings(report: TerminologyReport) -> None:
    """Print findings without the summary banner.

    Used by the pre-commit hook. A gate that fails without naming the term
    and the file gives the developer nothing to act on, and a gate nobody can
    act on is a gate that gets removed.
    """
    for finding in report.findings:
        marker = "ERROR" if finding.severity == "error" else "WARN "
        print(f"  [{marker}] {finding.target_path}")
        print(f"          {finding.message}")
        print(f"          Fix: {finding.remediation}")


def print_summary(report: TerminologyReport) -> None:
    """Print a human-readable validation summary."""
    print()
    print("=" * 60)
    print("  TRANSLATION TERMINOLOGY VALIDATION")
    print("=" * 60)
    print()
    print(f"  Documents checked: {report.docs_checked}")
    print(f"  Locale rules loaded: {report.terms_with_rules}")
    print(f"  Locales with rules: {', '.join(report.locales) or 'none'}")
    print()

    if not report.findings:
        print("  PASS: no terminology drift found.")
        print()
        print("=" * 60)
        return

    print(f"  Errors:   {report.total_errors}")
    print(f"  Warnings: {report.total_warnings}")
    print()

    for finding in report.findings[:30]:
        marker = "ERROR" if finding.severity == "error" else "WARN "
        print(f"  [{marker}] {finding.target_path}")
        print(f"          {finding.message}")
        print(f"          Fix: {finding.remediation}")
        print()

    if len(report.findings) > 30:
        print(f"  ... and {len(report.findings) - 30} more")
        print()

    print("=" * 60)


def write_annotations(report: TerminologyReport) -> None:
    """Emit GitHub Actions annotations for each finding."""
    if not os.environ.get("GITHUB_ACTIONS"):
        return
    for finding in report.findings:
        level = "error" if finding.severity == "error" else "warning"
        print(
            f"::{level} file={finding.target_path}::"
            f"{finding.message} Fix: {finding.remediation}"
        )


def write_github_summary(report: TerminologyReport) -> None:
    """Append a Markdown summary to the GitHub Actions step summary."""
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    lines: list[str] = ["## Translation terminology", ""]

    if not report.findings:
        lines.append(
            f"No terminology drift across {report.docs_checked} translated "
            "document(s)."
        )
    else:
        lines.append(
            f"**{report.total_errors}** error(s), "
            f"**{report.total_warnings}** warning(s)."
        )
        lines.append("")
        lines.append("| Severity | Page | Term | Problem |")
        lines.append("| --- | --- | --- | --- |")
        for finding in report.findings[:50]:
            lines.append(
                f"| {finding.severity} | `{finding.target_path}` | "
                f"`{finding.term}` | {finding.message} |"
            )
        if len(report.findings) > 50:
            lines.append(f"| ... | {len(report.findings) - 50} more | | |")

    lines.append("")
    with open(summary_path, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify technical terminology in translated documents against "
            "per-locale glossary rules"
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Specific translated files to validate (default: all)",
    )
    parser.add_argument(
        "--config",
        default="i18n.yml",
        help="Path to i18n.yml (default: i18n.yml)",
    )
    parser.add_argument(
        "--glossary",
        default="glossary.yml",
        help="Path to glossary.yml (default: glossary.yml)",
    )
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Documentation root directory (default: docs)",
    )
    parser.add_argument(
        "--locale",
        default="",
        help="Restrict validation to a single locale",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when terminology errors are found",
    )
    parser.add_argument(
        "--output",
        default="reports/i18n_terminology_report.json",
        help=(
            "Output JSON report path "
            "(default: reports/i18n_terminology_report.json)"
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print findings only, skipping the summary banner",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        config = load_i18n_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    try:
        rules_by_locale = load_locale_rules(args.glossary)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if not rules_by_locale:
        print(
            "No per-locale terminology rules defined in the glossary. "
            "Add a 'locales' block to the terms where a mistranslation "
            "would change the technical meaning."
        )
        return EXIT_OK

    docs_dir = Path(args.docs_dir)
    if not docs_dir.is_dir():
        print(f"Error: docs directory not found: {docs_dir}", file=sys.stderr)
        return EXIT_ERROR

    report = run_validation(
        docs_dir,
        rules_by_locale,
        config.target_locales,
        args.paths,
        only_locale=args.locale,
    )

    save_report(report, args.output)
    if args.quiet:
        print_findings(report)
    else:
        print_summary(report)
        print(f"  Report saved to: {args.output}")
    write_annotations(report)
    write_github_summary(report)

    if report.total_errors and args.strict:
        print()
        print(
            "  FAIL: translated pages use terminology that reads fluently "
            "and means the wrong thing."
        )
        return EXIT_ERRORS

    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())

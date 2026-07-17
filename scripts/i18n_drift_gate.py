#!/usr/bin/env python3
"""
Translation Drift Gate

Applies code-drift gate logic to translations, per language, on every change
to a source document. Where i18n_sync.py reports translation state, this
script enforces it: when an English page changes, every language version that
has fallen behind becomes a blocking finding.

The gate answers one question per (source doc, locale) pair: is this
translation currently in sync with the English body it claims to translate?
Staleness is content-based (SHA-256 of the source body, excluding
frontmatter), not date-based, so a page that changed 10 seconds ago is
flagged and a page that has not changed in two years is not.

Usage:
    # Gate only the source docs touched in this PR (CI usage)
    python3 scripts/i18n_drift_gate.py --base-ref origin/main --strict

    # Gate the whole docs tree (nightly / release usage)
    python3 scripts/i18n_drift_gate.py --strict

    # Also block on languages that were never translated at all
    python3 scripts/i18n_drift_gate.py --strict --fail-on any

    # Report without failing the build
    python3 scripts/i18n_drift_gate.py

Exit codes:
    0  Nothing blocking found, or --strict not enabled.
    1  Blocking findings with --strict enabled.
    2  Configuration or invocation error.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from i18n_sync import I18nSyncChecker, TranslationStatus
from i18n_utils import I18nConfig, load_i18n_config


EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_ERROR = 2

# Statuses that count as drift. "ok" is the only clean state.
DRIFT_STATUSES = ("missing", "stale")


@dataclass
class DriftFinding:
    """A single translation that has fallen behind its source."""
    source_path: str
    target_locale: str
    target_path: str
    status: str
    severity: str
    details: str
    remediation: str


@dataclass
class DriftReport:
    """Full drift gate result."""
    generated_at: str
    mode: str
    base_ref: str = ""
    strict: bool = False
    fail_on: str = "error"
    source_docs_checked: int = 0
    locales: list[str] = field(default_factory=list)
    total_findings: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    findings_by_locale: dict[str, dict] = field(default_factory=dict)
    findings: list[DriftFinding] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return self.total_findings > 0

    @property
    def has_blocking(self) -> bool:
        """Whether these findings should fail the build.

        Under the default `fail_on="error"`, only stale translations block. A
        stale page states the old behavior as fact and no reader can tell; a
        page that was never translated falls back to English, which is a
        coverage decision rather than drift introduced by this change.

        This distinction is what makes the gate adoptable on a repository that
        already has untranslated pages. A gate that fails every pull request
        from day one over pre-existing coverage gaps gets switched off, and
        then it catches nothing at all.
        """
        if self.fail_on == "any":
            return self.total_findings > 0
        return self.total_errors > 0


# ---------------------------------------------------------------------------
# Changed-file detection
# ---------------------------------------------------------------------------

def get_changed_source_docs(
    base_ref: str,
    docs_dir: Path,
    source_locale: str,
) -> list[str] | None:
    """List source-locale docs changed against a base ref.

    Args:
        base_ref: Git ref to diff against (for example "origin/main").
        docs_dir: Documentation root directory.
        source_locale: Source locale code.

    Returns:
        Locale-relative doc paths (for example "en/how-to/guide.md"), or
        None if git is unavailable or the ref cannot be resolved. Returning
        None signals the caller to fall back to a full scan rather than
        silently gating nothing.
    """
    source_prefix = (docs_dir / source_locale).as_posix()

    try:
        result = subprocess.run(
            [
                "git", "diff", "--name-only", "--diff-filter=ACMR",
                f"{base_ref}...HEAD", "--", source_prefix,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print("  Warning: git not found; falling back to full scan.", file=sys.stderr)
        return None

    if result.returncode != 0:
        stderr = result.stderr.strip()
        print(
            f"  Warning: could not diff against '{base_ref}' ({stderr}); "
            "falling back to full scan.",
            file=sys.stderr,
        )
        return None

    changed: list[str] = []
    docs_prefix = docs_dir.as_posix()
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line or not line.endswith(".md"):
            continue
        # docs/en/how-to/guide.md -> en/how-to/guide.md
        if line.startswith(f"{docs_prefix}/"):
            changed.append(line[len(docs_prefix) + 1:])

    return changed


# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------

def _severity_for(status: str) -> str:
    """Map a translation status to a gate severity.

    A stale translation is more dangerous than a missing one: a missing
    page falls back to English and the reader knows what they are getting,
    while a stale page reads as authoritative and is silently wrong.
    """
    return "error" if status == "stale" else "warning"


def _remediation_for(status: str, source_path: str, locale: str) -> str:
    if status == "missing":
        return (
            f"npm run i18n:translate -- --source {source_path} --locale {locale}"
        )
    return (
        f"npm run i18n:translate -- --source {source_path} --locale {locale}  "
        "# re-translate, then review terminology"
    )


def build_findings(
    items: list[TranslationStatus],
    scope: set[str] | None,
) -> list[DriftFinding]:
    """Convert sync statuses into gate findings.

    Args:
        items: All translation statuses from the sync checker.
        scope: Locale-relative source paths to restrict to, or None for all.

    Returns:
        Drift findings, sorted by locale then source path.
    """
    findings: list[DriftFinding] = []

    for item in items:
        if item.status not in DRIFT_STATUSES:
            continue
        if scope is not None and item.source_path not in scope:
            continue

        findings.append(DriftFinding(
            source_path=item.source_path,
            target_locale=item.target_locale,
            target_path=item.target_path,
            status=item.status,
            severity=_severity_for(item.status),
            details=item.details,
            remediation=_remediation_for(
                item.status, item.source_path, item.target_locale
            ),
        ))

    findings.sort(key=lambda f: (f.target_locale, f.source_path))
    return findings


def run_gate(
    config: I18nConfig,
    docs_dir: Path,
    base_ref: str = "",
    strict: bool = False,
    fail_on: str = "error",
) -> DriftReport:
    """Run the translation drift gate.

    Args:
        config: Loaded i18n configuration.
        docs_dir: Documentation root directory.
        base_ref: Git ref to scope the gate to changed docs, or "" for a
            full scan.
        strict: Whether blocking findings should fail the build.
        fail_on: "error" to block only on stale translations, "any" to block
            on missing translations too.

    Returns:
        DriftReport with findings and per-locale counts.
    """
    checker = I18nSyncChecker(config, docs_dir=docs_dir)
    sync = checker.check_all()

    scope: set[str] | None = None
    mode = "full-scan"

    if base_ref:
        changed = get_changed_source_docs(
            base_ref, docs_dir, config.default_language
        )
        if changed is not None:
            scope = set(changed)
            mode = "changed-only"

    findings = build_findings(sync.items, scope)

    findings_by_locale: dict[str, dict] = {}
    for locale in config.target_locales:
        locale_findings = [f for f in findings if f.target_locale == locale]
        findings_by_locale[locale] = {
            "total": len(locale_findings),
            "stale": sum(1 for f in locale_findings if f.status == "stale"),
            "missing": sum(1 for f in locale_findings if f.status == "missing"),
            "coverage_pct": sync.coverage.get(locale, {}).get("coverage_pct", 0.0),
        }

    checked = len(scope) if scope is not None else sync.total_source_docs

    return DriftReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        mode=mode,
        base_ref=base_ref,
        strict=strict,
        fail_on=fail_on,
        source_docs_checked=checked,
        locales=config.target_locales,
        total_findings=len(findings),
        total_errors=sum(1 for f in findings if f.severity == "error"),
        total_warnings=sum(1 for f in findings if f.severity == "warning"),
        findings_by_locale=findings_by_locale,
        findings=findings,
    )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def save_report(report: DriftReport, output_path: str | Path) -> Path:
    """Save the drift report as JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = asdict(report)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def print_summary(report: DriftReport) -> None:
    """Print a human-readable gate summary."""
    print()
    print("=" * 60)
    print("  TRANSLATION DRIFT GATE")
    print("=" * 60)
    print()
    print(f"  Mode: {report.mode}", end="")
    if report.base_ref:
        print(f" (base: {report.base_ref})")
    else:
        print()
    print(f"  Source docs checked: {report.source_docs_checked}")
    print(f"  Target locales: {', '.join(report.locales) or 'none'}")
    print()

    if not report.has_drift:
        print("  PASS: every language version is in sync with its source.")
        print()
        print("=" * 60)
        return

    for locale, stats in report.findings_by_locale.items():
        if stats["total"] == 0:
            continue
        print(
            f"  [{locale}] {stats['total']} behind "
            f"({stats['stale']} stale, {stats['missing']} missing)"
        )

    print()
    print(
        f"  Findings: {report.total_findings} "
        f"({report.total_errors} stale, {report.total_warnings} missing)"
    )
    if report.fail_on == "error" and report.total_warnings:
        print(
            "  Missing translations are reported, not blocking. "
            "Use --fail-on any to block on them too."
        )
    print()
    for finding in report.findings[:25]:
        marker = "ERROR" if finding.severity == "error" else "WARN "
        print(f"  [{marker}] {finding.target_path}")
        print(f"          {finding.details}")
        print(f"          Fix: {finding.remediation}")
    if len(report.findings) > 25:
        print(f"  ... and {len(report.findings) - 25} more")

    print()
    print("=" * 60)


def write_github_summary(report: DriftReport) -> None:
    """Append a Markdown summary to the GitHub Actions step summary."""
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    lines: list[str] = ["## Translation drift gate", ""]

    if not report.has_drift:
        lines.append(
            f"All language versions are in sync across "
            f"{report.source_docs_checked} source document(s)."
        )
    else:
        lines.append(
            f"**{report.total_findings}** translation(s) have fallen behind "
            f"their English source."
        )
        lines.append("")
        lines.append("| Locale | Page | Status | Fix |")
        lines.append("| --- | --- | --- | --- |")
        for finding in report.findings[:50]:
            lines.append(
                f"| `{finding.target_locale}` | `{finding.target_path}` | "
                f"{finding.status} | `{finding.remediation.split('  #')[0]}` |"
            )
        if len(report.findings) > 50:
            lines.append(f"| ... | {len(report.findings) - 50} more | | |")

    lines.append("")

    with open(summary_path, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def write_annotations(report: DriftReport) -> None:
    """Emit GitHub Actions annotations for each finding."""
    if not os.environ.get("GITHUB_ACTIONS"):
        return

    for finding in report.findings:
        level = "error" if finding.severity == "error" else "warning"
        message = (
            f"{finding.target_locale}: {finding.details}. "
            f"Fix: {finding.remediation}"
        )
        print(f"::{level} file=docs/{finding.source_path}::{message}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gate translations against source drift, per language"
    )
    parser.add_argument(
        "--config",
        default="i18n.yml",
        help="Path to i18n.yml (default: i18n.yml)",
    )
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Documentation root directory (default: docs)",
    )
    parser.add_argument(
        "--base-ref",
        default="",
        help=(
            "Git ref to diff against, restricting the gate to source docs "
            "changed in this branch (for example: origin/main). "
            "Omit for a full scan."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when blocking findings exist (see --fail-on)",
    )
    parser.add_argument(
        "--fail-on",
        choices=["error", "any"],
        default="error",
        help=(
            "Which findings block with --strict. 'error' (default) blocks on "
            "stale translations only, so a repository with pre-existing "
            "untranslated pages can adopt the gate without failing every "
            "pull request. 'any' also blocks on missing translations."
        ),
    )
    parser.add_argument(
        "--output",
        default="reports/i18n_drift_report.json",
        help="Output JSON report path (default: reports/i18n_drift_report.json)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        config = load_i18n_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if not config.target_locales:
        print("No target locales configured. Translation drift gate skipped.")
        return EXIT_OK

    docs_dir = Path(args.docs_dir)
    if not docs_dir.is_dir():
        print(f"Error: docs directory not found: {docs_dir}", file=sys.stderr)
        return EXIT_ERROR

    report = run_gate(
        config,
        docs_dir,
        base_ref=args.base_ref,
        strict=args.strict,
        fail_on=args.fail_on,
    )

    save_report(report, args.output)
    print_summary(report)
    write_annotations(report)
    write_github_summary(report)
    print(f"  Report saved to: {args.output}")

    if args.strict and report.has_blocking:
        print()
        print(
            "  FAIL: source pages changed without their translations. "
            "Update the translations or accept the drift explicitly."
        )
        return EXIT_DRIFT

    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())

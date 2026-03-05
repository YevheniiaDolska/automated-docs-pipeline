#!/usr/bin/env python3
"""
Translation Sync Checker

Detects missing and stale translations by comparing source documents
against their translations in other locale directories. Outputs a JSON
report used by the consolidated report pipeline and the auto-translator.

Usage:
    python3 scripts/i18n_sync.py
    python3 scripts/i18n_sync.py --config i18n.yml --docs-dir docs
    python3 scripts/i18n_sync.py --output reports/i18n_sync_report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from i18n_utils import (
    I18nConfig,
    compute_content_hash,
    extract_frontmatter,
    load_i18n_config,
)


@dataclass
class TranslationStatus:
    """Status of a single translation pair."""
    source_path: str
    target_locale: str
    target_path: str
    status: str  # "ok", "missing", "stale"
    source_hash: str = ""
    target_hash: str = ""
    details: str = ""


@dataclass
class SyncReport:
    """Full sync report across all locales."""
    generated_at: str
    default_language: str
    total_source_docs: int = 0
    languages: list[str] = field(default_factory=list)
    coverage: dict[str, dict] = field(default_factory=dict)
    items: list[TranslationStatus] = field(default_factory=list)


class I18nSyncChecker:
    """Checks translation freshness across all configured locales."""

    def __init__(
        self,
        config: I18nConfig,
        docs_dir: str | Path = "docs",
    ):
        self.config = config
        self.docs_dir = Path(docs_dir)
        self.source_locale = config.default_language
        self.target_locales = config.target_locales

    def _list_source_docs(self) -> list[Path]:
        """List all Markdown files in the source locale directory."""
        source_dir = self.docs_dir / self.source_locale
        if not source_dir.is_dir():
            return []
        return sorted(
            p for p in source_dir.rglob("*.md")
            if not p.name.startswith("_")
        )

    def _get_relative_path(self, filepath: Path) -> str:
        """Get path relative to the source locale directory."""
        source_dir = self.docs_dir / self.source_locale
        return str(filepath.relative_to(source_dir))

    def check_translation(
        self,
        source_path: Path,
        target_locale: str,
    ) -> TranslationStatus:
        """Check a single source doc against its translation.

        Args:
            source_path: Path to the source Markdown file.
            target_locale: Target locale code.

        Returns:
            TranslationStatus describing the state.
        """
        rel_path = self._get_relative_path(source_path)
        target_path = self.docs_dir / target_locale / rel_path
        source_rel = f"{self.source_locale}/{rel_path}"
        target_rel = f"{target_locale}/{rel_path}"

        source_hash = compute_content_hash(source_path)

        if not target_path.exists():
            return TranslationStatus(
                source_path=source_rel,
                target_locale=target_locale,
                target_path=target_rel,
                status="missing",
                source_hash=source_hash,
                details=f"Translation does not exist for {target_locale}",
            )

        # Read translation frontmatter
        text = target_path.read_text(encoding="utf-8")
        fm, _ = extract_frontmatter(text)
        stored_hash = fm.get("source_hash", "")

        if not stored_hash:
            # No source_hash in translation -- treat as stale (cannot verify)
            return TranslationStatus(
                source_path=source_rel,
                target_locale=target_locale,
                target_path=target_rel,
                status="stale",
                source_hash=source_hash,
                target_hash="",
                details="Translation has no source_hash in frontmatter",
            )

        if stored_hash != source_hash:
            return TranslationStatus(
                source_path=source_rel,
                target_locale=target_locale,
                target_path=target_rel,
                status="stale",
                source_hash=source_hash,
                target_hash=stored_hash,
                details="Source content changed since translation was made",
            )

        return TranslationStatus(
            source_path=source_rel,
            target_locale=target_locale,
            target_path=target_rel,
            status="ok",
            source_hash=source_hash,
            target_hash=stored_hash,
        )

    def check_all(self) -> SyncReport:
        """Check all source documents against all target locales.

        Returns:
            SyncReport with per-locale coverage and item-level status.
        """
        source_docs = self._list_source_docs()
        items: list[TranslationStatus] = []

        for source_path in source_docs:
            for target_locale in self.target_locales:
                status = self.check_translation(source_path, target_locale)
                items.append(status)

        # Compute per-locale coverage
        coverage: dict[str, dict] = {}
        for locale in self.target_locales:
            locale_items = [i for i in items if i.target_locale == locale]
            total = len(locale_items)
            ok = sum(1 for i in locale_items if i.status == "ok")
            missing = sum(1 for i in locale_items if i.status == "missing")
            stale = sum(1 for i in locale_items if i.status == "stale")
            coverage[locale] = {
                "total_source_docs": total,
                "translated": ok,
                "missing": missing,
                "stale": stale,
                "coverage_pct": round(ok / total * 100, 1) if total else 0.0,
            }

        return SyncReport(
            generated_at=datetime.now(timezone.utc).isoformat(),
            default_language=self.source_locale,
            total_source_docs=len(source_docs),
            languages=self.target_locales,
            coverage=coverage,
            items=items,
        )


def save_report(report: SyncReport, output_path: str | Path) -> Path:
    """Save sync report as JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "generated_at": report.generated_at,
        "default_language": report.default_language,
        "total_source_docs": report.total_source_docs,
        "languages": report.languages,
        "coverage": report.coverage,
        "items": [asdict(item) for item in report.items],
    }

    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def print_summary(report: SyncReport) -> None:
    """Print a human-readable summary of the sync report."""
    print()
    print("=" * 60)
    print("  i18n TRANSLATION SYNC REPORT")
    print("=" * 60)
    print()
    print(f"  Source language: {report.default_language}")
    print(f"  Source documents: {report.total_source_docs}")
    print()

    for locale, stats in report.coverage.items():
        print(f"  [{locale}] {stats['coverage_pct']:.1f}% translated")
        print(f"    Translated: {stats['translated']}")
        print(f"    Missing:    {stats['missing']}")
        print(f"    Stale:      {stats['stale']}")
        print()

    # List missing and stale items
    problems = [i for i in report.items if i.status != "ok"]
    if problems:
        print(f"  Action items: {len(problems)}")
        for item in problems[:20]:
            print(f"    [{item.status.upper()}] {item.target_path}")
        if len(problems) > 20:
            print(f"    ... and {len(problems) - 20} more")
    else:
        print("  All translations are up to date.")

    print()
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check translation freshness across all locales"
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
        "--output",
        default="reports/i18n_sync_report.json",
        help="Output JSON report path (default: reports/i18n_sync_report.json)",
    )
    args = parser.parse_args()

    try:
        config = load_i18n_config(args.config)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not config.target_locales:
        print("No target locales configured. Nothing to check.")
        sys.exit(0)

    checker = I18nSyncChecker(config, docs_dir=args.docs_dir)
    report = checker.check_all()

    save_report(report, args.output)
    print_summary(report)
    print(f"  Report saved to: {args.output}")


if __name__ == "__main__":
    main()

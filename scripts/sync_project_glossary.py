#!/usr/bin/env python3
"""Sync project glossary entries from inline glossary markers in markdown docs.

Marker format inside docs:
  <!-- glossary:add: Term | Description -->
  <!-- glossary:add: Term | Description | alias-one, alias-two -->
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

MARKER_PATTERN = re.compile(
    r"<!--\s*glossary:add:\s*(?P<payload>.*?)\s*-->",
    flags=re.IGNORECASE,
)


def _iter_markdown_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_file() and path.suffix.lower() == ".md":
            files.append(path)
            continue
        if path.is_dir():
            files.extend(sorted(path.rglob("*.md")))
    return sorted(set(files))


def _load_glossary(glossary_path: Path) -> dict[str, Any]:
    if not glossary_path.exists():
        return {"terms": {}, "forbidden": []}
    payload = yaml.safe_load(glossary_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Glossary must be a YAML mapping: {glossary_path}")
    if not isinstance(payload.get("terms"), dict):
        payload["terms"] = {}
    if not isinstance(payload.get("forbidden"), list):
        payload["forbidden"] = []
    return payload


def _parse_marker_payload(payload: str) -> tuple[str, str, list[str]] | None:
    parts = [part.strip() for part in payload.split("|")]
    if len(parts) < 2:
        return None
    term = parts[0]
    description = parts[1]
    if not term or not description:
        return None
    aliases: list[str] = []
    if len(parts) >= 3 and parts[2]:
        aliases = [item.strip() for item in parts[2].split(",") if item.strip()]
    return term, description, aliases


def sync_glossary(
    paths: list[str],
    glossary_path: Path,
    write: bool,
    report_path: Path | None,
) -> dict[str, Any]:
    glossary = _load_glossary(glossary_path)
    terms = glossary["terms"]
    known = {str(key).strip().lower(): str(key).strip() for key in terms}

    scanned_files = 0
    markers_found = 0
    added_terms: list[dict[str, Any]] = []
    updated_terms: list[dict[str, Any]] = []

    for md_path in _iter_markdown_files(paths):
        scanned_files += 1
        rel_path = str(md_path)
        content = md_path.read_text(encoding="utf-8", errors="ignore")
        for marker in MARKER_PATTERN.finditer(content):
            parsed = _parse_marker_payload(marker.group("payload"))
            if parsed is None:
                continue
            markers_found += 1
            term, description, aliases = parsed
            norm = term.lower()
            existing_key = known.get(norm)
            if existing_key is None:
                terms[term] = {
                    "description": description,
                    "aliases": aliases,
                    "usage_context": [rel_path],
                }
                known[norm] = term
                added_terms.append(
                    {
                        "term": term,
                        "description": description,
                        "aliases": aliases,
                        "source": rel_path,
                    }
                )
                continue

            entry = terms.get(existing_key, {})
            if not isinstance(entry, dict):
                entry = {"description": "", "aliases": []}
            changed = False

            current_desc = str(entry.get("description", "")).strip()
            if not current_desc and description:
                entry["description"] = description
                changed = True

            current_aliases = entry.get("aliases", [])
            if not isinstance(current_aliases, list):
                current_aliases = []
            alias_set = {str(alias).strip() for alias in current_aliases if str(alias).strip()}
            for alias in aliases:
                if alias not in alias_set:
                    alias_set.add(alias)
                    changed = True
            entry["aliases"] = sorted(alias_set)

            usage_context = entry.get("usage_context", [])
            if not isinstance(usage_context, list):
                usage_context = []
            if rel_path not in usage_context:
                usage_context.append(rel_path)
                changed = True
            entry["usage_context"] = usage_context

            terms[existing_key] = entry
            if changed:
                updated_terms.append(
                    {
                        "term": existing_key,
                        "source": rel_path,
                    }
                )

    if write:
        glossary_path.parent.mkdir(parents=True, exist_ok=True)
        glossary_path.write_text(
            yaml.safe_dump(glossary, sort_keys=False, allow_unicode=False),
            encoding="utf-8",
        )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "glossary_path": str(glossary_path),
        "scanned_files": scanned_files,
        "markers_found": markers_found,
        "added_count": len(added_terms),
        "updated_count": len(updated_terms),
        "added_terms": added_terms,
        "updated_terms": updated_terms,
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync glossary entries from docs markers")
    parser.add_argument(
        "--paths",
        nargs="+",
        default=["docs"],
        help="Markdown files or directories to scan (default: docs)",
    )
    parser.add_argument(
        "--glossary",
        default="glossary.yml",
        help="Glossary YAML path (default: glossary.yml)",
    )
    parser.add_argument(
        "--report",
        default="reports/glossary_sync_report.json",
        help="JSON report path (default: reports/glossary_sync_report.json)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write updates into glossary file",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = sync_glossary(
        paths=[str(p) for p in args.paths],
        glossary_path=Path(args.glossary),
        write=bool(args.write),
        report_path=Path(args.report) if args.report else None,
    )
    print(
        "[ok] glossary sync: "
        f"scanned={report['scanned_files']} markers={report['markers_found']} "
        f"added={report['added_count']} updated={report['updated_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

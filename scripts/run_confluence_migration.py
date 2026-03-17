#!/usr/bin/env python3
"""One-click Confluence migration with docsops post-check report."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any

from confluence_importer import ConfluenceImporter


def _run(cmd: list[str], cwd: Path, allow_fail: bool = False) -> tuple[int, str]:
    print(f"[migrate] $ {' '.join(shlex.quote(part) for part in cmd)}")
    completed = subprocess.run(
        cmd,
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0 and not allow_fail:
        raise RuntimeError(f"Command failed (rc={completed.returncode}): {' '.join(cmd)}\n{output}")
    return completed.returncode, output


def _count_markdown_files(path: Path) -> int:
    return len(list(path.rglob("*.md")))


def _build_checks(py: str, import_dir: Path, reports_dir: Path) -> list[tuple[str, list[str], bool]]:
    return [
        (
            "normalize_check_before",
            [py, "scripts/normalize_docs.py", str(import_dir), "--check"],
            True,
        ),
        (
            "seo_geo_before",
            [py, "scripts/seo_geo_optimizer.py", str(import_dir)],
            True,
        ),
        (
            "normalize_fix",
            [py, "scripts/normalize_docs.py", str(import_dir)],
            True,
        ),
        (
            "seo_geo_fix",
            [py, "scripts/seo_geo_optimizer.py", str(import_dir), "--fix"],
            True,
        ),
        (
            "examples_smoke",
            [
                py,
                "scripts/check_code_examples_smoke.py",
                "--paths",
                str(import_dir),
                "--allow-empty",
                "--report",
                str(reports_dir / "confluence_examples_smoke.json"),
            ],
            True,
        ),
        (
            "normalize_check_after",
            [py, "scripts/normalize_docs.py", str(import_dir), "--check"],
            True,
        ),
        (
            "seo_geo_after",
            [py, "scripts/seo_geo_optimizer.py", str(import_dir)],
            True,
        ),
    ]


def _summarize_status(checks: list[dict[str, Any]]) -> dict[str, list[str]]:
    failed = [c["name"] for c in checks if c["return_code"] != 0]
    passed = [c["name"] for c in checks if c["return_code"] == 0]
    return {"passed": passed, "failed": failed}


def _write_markdown_report(report: dict[str, Any], report_md: Path) -> None:
    migration = report["migration"]
    checks = report["checks"]
    status = report["status"]

    lines = [
        "# Confluence migration report",
        "",
        f"- Timestamp: {report['timestamp_utc']}",
        f"- Source ZIP: `{migration['source_zip']}`",
        f"- Output dir: `{migration['output_dir']}`",
        "",
        "## Summary",
        "",
        f"- Total pages found: {migration['total_pages']}",
        f"- Pages migrated: {migration['imported_pages']}",
        f"- Pages failed: {migration['failed_pages']}",
        f"- Markdown files in output: {migration['markdown_files_count']}",
        "",
        "## What was broken",
        "",
    ]

    broken = status["failed"]
    if broken:
        for name in broken:
            lines.append(f"- {name}")
    else:
        lines.append("- No post-check failures.")

    lines.extend(["", "## What was fixed automatically", ""])
    fixed_items: list[str] = []
    if any(c["name"] == "normalize_fix" and c["return_code"] == 0 for c in checks):
        fixed_items.append("- Markdown structure normalized (lists, spacing, section shape).")
    if any(c["name"] == "seo_geo_fix" and c["return_code"] == 0 for c in checks):
        fixed_items.append("- SEO/GEO metadata and content issues auto-corrected where safe.")
    if fixed_items:
        lines.extend(fixed_items)
    else:
        lines.append("- No automatic fixes were applied.")

    lines.extend(["", "## Check results", ""])
    for check in checks:
        marker = "OK" if check["return_code"] == 0 else "FAIL"
        lines.append(f"- `{check['name']}`: {marker} (rc={check['return_code']})")

    if migration.get("warnings"):
        lines.extend(["", "## Migration warnings", ""])
        for warning in migration["warnings"]:
            lines.append(f"- {warning}")

    report_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one-click Confluence migration into docsops-ready Markdown")
    parser.add_argument("--export-zip", default="", help="Path to Confluence export ZIP (entities.xml inside)")
    parser.add_argument(
        "--output-dir",
        default="",
        help="Output directory for imported markdown (default: docs/imported/confluence/<timestamp>)",
    )
    parser.add_argument(
        "--reports-dir",
        default="reports",
        help="Directory for JSON and Markdown migration report",
    )
    parser.add_argument(
        "--skip-post-checks",
        action="store_true",
        help="Skip docsops post-checks after import",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]

    export_zip_raw = args.export_zip.strip()
    if not export_zip_raw:
        export_zip_raw = input("Confluence export ZIP path: ").strip()
        if not export_zip_raw:
            print("[migrate] error: export ZIP path is required")
            return 2

    export_zip = Path(export_zip_raw).expanduser()
    if not export_zip.is_absolute():
        export_zip = (Path.cwd() / export_zip).resolve()

    if args.output_dir.strip():
        output_dir = Path(args.output_dir).expanduser()
        if not output_dir.is_absolute():
            output_dir = (Path.cwd() / output_dir).resolve()
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        output_dir = (repo_root / "docs" / "imported" / "confluence" / ts).resolve()

    reports_dir = Path(args.reports_dir).expanduser()
    if not reports_dir.is_absolute():
        reports_dir = (Path.cwd() / reports_dir).resolve()
    reports_dir.mkdir(parents=True, exist_ok=True)

    importer = ConfluenceImporter()
    migration_result = importer.import_export(export_zip=export_zip, output_dir=output_dir)

    migration_payload: dict[str, Any] = {
        "source_zip": migration_result.source_zip,
        "output_dir": migration_result.output_dir,
        "total_pages": migration_result.total_pages,
        "imported_pages": migration_result.imported_pages,
        "failed_pages": migration_result.failed_pages,
        "failed_titles": migration_result.failed_titles,
        "warnings": migration_result.warnings,
        "generated_files": migration_result.generated_files,
        "markdown_files_count": _count_markdown_files(output_dir),
    }

    checks_payload: list[dict[str, Any]] = []
    py = sys.executable

    if not args.skip_post_checks:
        for name, cmd, allow_fail in _build_checks(py=py, import_dir=output_dir, reports_dir=reports_dir):
            rc, output = _run(cmd, cwd=repo_root, allow_fail=allow_fail)
            checks_payload.append(
                {
                    "name": name,
                    "return_code": rc,
                    "output_excerpt": output[-2000:],
                }
            )

    status = _summarize_status(checks_payload)
    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "migration": migration_payload,
        "checks": checks_payload,
        "status": status,
    }

    report_json = reports_dir / "confluence_migration_report.json"
    report_md = reports_dir / "confluence_migration_report.md"

    report_json.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    _write_markdown_report(report, report_md)

    print("[migrate] done")
    print(f"[migrate] imported pages: {migration_result.imported_pages}/{migration_result.total_pages}")
    print(f"[migrate] report json: {report_json}")
    print(f"[migrate] report md:   {report_md}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

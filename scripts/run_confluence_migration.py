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


def _build_checks(
    py: str,
    import_dir: Path,
    reports_dir: Path,
    repo_root: Path,
    use_llm: bool = False,
) -> list[tuple[str, list[str], bool]]:
    enhance_cmd = [
        py,
        "scripts/confluence_quality_enhancer.py",
        str(import_dir),
        "--repo-root",
        str(repo_root),
        "--report",
        str(reports_dir / "confluence_quality_enhance.json"),
    ]
    if use_llm:
        enhance_cmd.append("--use-llm")

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
            "quality_enhance",
            enhance_cmd,
            True,
        ),
        (
            "seo_geo_fix",
            [py, "scripts/seo_geo_optimizer.py", str(import_dir), "--fix"],
            True,
        ),
        (
            "validate_frontmatter",
            [py, "scripts/validate_frontmatter.py", "--paths", str(import_dir)],
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
            "extract_knowledge",
            [
                py,
                "scripts/extract_knowledge_modules_from_docs.py",
                "--docs-dir",
                str(import_dir),
                "--modules-dir",
                str(repo_root / "knowledge_modules"),
                "--report",
                str(reports_dir / "confluence_knowledge_extract.json"),
            ],
            True,
        ),
        (
            "validate_knowledge",
            [py, "scripts/validate_knowledge_modules.py"],
            True,
        ),
        (
            "rebuild_index",
            [py, "scripts/generate_knowledge_retrieval_index.py"],
            True,
        ),
        (
            "glossary_sync",
            [
                py,
                "scripts/sync_project_glossary.py",
                "--paths",
                str(import_dir),
                "--glossary",
                str(repo_root / "glossary.yml"),
                "--report",
                str(reports_dir / "confluence_glossary_sync.json"),
                "--write",
            ],
            True,
        ),
        (
            "final_lint_check",
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

    source_line = (
        f"- Source URL: `{migration['source_url']}`"
        if migration.get("source_url")
        else f"- Source ZIP: `{migration.get('source_zip', 'N/A')}`"
    )

    lines = [
        "# Confluence migration report",
        "",
        f"- Timestamp: {report['timestamp_utc']}",
        source_line,
        f"- Output dir: `{migration['output_dir']}`",
    ]
    if migration.get("api_version"):
        lines.append(f"- API version: {migration['api_version']}")

    lines.extend([
        "",
        "## Summary",
        "",
        f"- Total pages found: {migration['total_pages']}",
        f"- Pages migrated: {migration['imported_pages']}",
        f"- Pages failed: {migration['failed_pages']}",
        f"- Markdown files in output: {migration['markdown_files_count']}",
    ])
    if migration.get("skipped_pages"):
        lines.append(f"- Pages skipped (unchanged): {migration['skipped_pages']}")
    if migration.get("attachments_downloaded"):
        lines.append(f"- Attachments downloaded: {migration['attachments_downloaded']}")

    lines.extend([
        "",
        "## What was broken",
        "",
    ])

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
    if any(c["name"] == "quality_enhance" and c["return_code"] == 0 for c in checks):
        fixed_items.append("- Quality enhancement applied (frontmatter, headings, code blocks, variables, structure).")
    if any(c["name"] == "seo_geo_fix" and c["return_code"] == 0 for c in checks):
        fixed_items.append("- SEO/GEO metadata and content issues auto-corrected where safe.")
    if any(c["name"] == "extract_knowledge" and c["return_code"] == 0 for c in checks):
        fixed_items.append("- Knowledge modules extracted for RAG retrieval.")
    if any(c["name"] == "glossary_sync" and c["return_code"] == 0 for c in checks):
        fixed_items.append("- Glossary synchronized with imported terminology.")
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
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use LLM to enhance information architecture (progressive disclosure, logical structure)",
    )
    parser.add_argument(
        "--confluence-url",
        default="",
        help="Confluence base URL for REST API mode (e.g. https://mycompany.atlassian.net)",
    )
    parser.add_argument(
        "--confluence-token",
        default="",
        help="API token (Cloud) or Personal Access Token (Server/Data Center)",
    )
    parser.add_argument(
        "--confluence-username",
        default="",
        help="Email address (Cloud) or username (Server/Data Center)",
    )
    parser.add_argument(
        "--space-keys",
        default="",
        help="Comma-separated Confluence space keys to import",
    )
    parser.add_argument(
        "--include-attachments",
        action="store_true",
        help="Download page attachments when using REST API mode",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Only fetch pages modified since last sync (REST API mode)",
    )
    return parser.parse_args()


def _resolve_output_dir(args: argparse.Namespace, repo_root: Path) -> Path:
    if args.output_dir.strip():
        output_dir = Path(args.output_dir).expanduser()
        if not output_dir.is_absolute():
            output_dir = (Path.cwd() / output_dir).resolve()
        return output_dir
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return (repo_root / "docs" / "imported" / "confluence" / ts).resolve()


def _run_api_mode(
    args: argparse.Namespace, output_dir: Path, repo_root: Path,
) -> dict[str, Any]:
    from confluence_rest_client import ConfluenceConfig, ConfluenceRestClient

    space_keys = [k.strip() for k in args.space_keys.split(",") if k.strip()]
    if not space_keys:
        print("[migrate] error: --space-keys is required for REST API mode")
        raise SystemExit(2)
    if not args.confluence_token.strip():
        print("[migrate] error: --confluence-token is required for REST API mode")
        raise SystemExit(2)

    sync_state_file = repo_root / ".confluence_sync_state.json" if args.incremental else None
    config = ConfluenceConfig(
        base_url=args.confluence_url.strip().rstrip("/"),
        token=args.confluence_token.strip(),
        username=args.confluence_username.strip(),
        space_keys=space_keys,
        include_attachments=args.include_attachments,
        sync_state_file=sync_state_file,
    )
    with ConfluenceRestClient(config) as client:
        result = client.fetch_and_import(output_dir, incremental=args.incremental)

    return {
        "source_url": result.source_url,
        "output_dir": result.output_dir,
        "total_pages": result.total_pages,
        "imported_pages": result.imported_pages,
        "failed_pages": result.failed_pages,
        "skipped_pages": result.skipped_pages,
        "attachments_downloaded": result.attachments_downloaded,
        "failed_titles": result.failed_titles,
        "warnings": result.warnings,
        "generated_files": result.generated_files,
        "markdown_files_count": _count_markdown_files(output_dir),
        "api_version": getattr(result, "api_version", ""),
    }


def _run_zip_mode(
    args: argparse.Namespace, output_dir: Path,
) -> dict[str, Any]:
    export_zip_raw = args.export_zip.strip()
    if not export_zip_raw:
        export_zip_raw = input("Confluence export ZIP path: ").strip()
        if not export_zip_raw:
            print("[migrate] error: export ZIP path is required")
            raise SystemExit(2)

    export_zip = Path(export_zip_raw).expanduser()
    if not export_zip.is_absolute():
        export_zip = (Path.cwd() / export_zip).resolve()

    importer = ConfluenceImporter()
    result = importer.import_export(export_zip=export_zip, output_dir=output_dir)

    return {
        "source_zip": result.source_zip,
        "output_dir": result.output_dir,
        "total_pages": result.total_pages,
        "imported_pages": result.imported_pages,
        "failed_pages": result.failed_pages,
        "failed_titles": result.failed_titles,
        "warnings": result.warnings,
        "generated_files": result.generated_files,
        "markdown_files_count": _count_markdown_files(output_dir),
    }


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = _resolve_output_dir(args, repo_root)

    reports_dir = Path(args.reports_dir).expanduser()
    if not reports_dir.is_absolute():
        reports_dir = (Path.cwd() / reports_dir).resolve()
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Determine mode: REST API vs ZIP export
    use_api = bool(args.confluence_url.strip())
    if use_api:
        migration_payload = _run_api_mode(args, output_dir, repo_root)
    else:
        migration_payload = _run_zip_mode(args, output_dir)

    checks_payload: list[dict[str, Any]] = []
    py = sys.executable

    if not args.skip_post_checks:
        for name, cmd, allow_fail in _build_checks(
            py=py,
            import_dir=output_dir,
            reports_dir=reports_dir,
            repo_root=repo_root,
            use_llm=args.use_llm,
        ):
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
    print(f"[migrate] imported pages: {migration_payload['imported_pages']}/{migration_payload['total_pages']}")
    print(f"[migrate] report json: {report_json}")
    print(f"[migrate] report md:   {report_md}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

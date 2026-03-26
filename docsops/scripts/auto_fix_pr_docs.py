#!/usr/bin/env python3
"""Auto-generate docs patch file for a blocked PR when interface drift is detected."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.check_api_sdk_drift import evaluate as evaluate_drift
from scripts.check_docs_contract import evaluate_contract


def _changed_files(base_ref: str, head_ref: str) -> list[str]:
    cmd = ["git", "diff", "--name-only", f"{base_ref}...{head_ref}"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _render_list(items: list[str]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- `{item}`" for item in items)


def _build_doc_content(pr_number: int, files: list[str], report: dict[str, Any]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    title = f"PR {pr_number} API and docs sync note"
    description = (
        "Auto-generated reference note listing API or interface changes detected in the PR and "
        "the required documentation alignment actions."
    )
    interface_changed = report.get("interface_changed", [])
    openapi_changed = report.get("openapi_changed", [])
    sdk_changed = report.get("sdk_changed", [])

    return (
        "---\n"
        f'title: "{title}"\n'
        f'description: "{description}"\n'
        "content_type: reference\n"
        "product: both\n"
        "tags:\n"
        "  - Reference\n"
        f'last_reviewed: "{now}"\n'
        "---\n\n"
        f"# {title}\n\n"
        "This page is an auto-generated reference note that records interface changes in this pull request.\n\n"
        "## Pull request scope\n\n"
        f"- PR number: `{pr_number}`\n"
        f"- Generated date (UTC): `{now}`\n"
        f"- Total changed files: `{len(files)}`\n\n"
        "## Changed files in PR\n\n"
        f"{_render_list(files)}\n\n"
        "## Interface files changed\n\n"
        f"{_render_list(interface_changed)}\n\n"
        "## OpenAPI files changed\n\n"
        f"{_render_list(openapi_changed)}\n\n"
        "## SDK or client files changed\n\n"
        f"{_render_list(sdk_changed)}\n\n"
        "## Documentation sync action\n\n"
        "Use this note as a checkpoint that API or interface changes were detected and reflected in docs.\n"
        "If business-facing behavior changed, also update the relevant how-to and concept pages in this PR branch.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-fix blocked PR by adding required docs reference note")
    parser.add_argument("--base", required=True, help="Base commit/branch")
    parser.add_argument("--head", required=True, help="Head commit/branch")
    parser.add_argument("--pr-number", required=True, type=int)
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args()

    files = _changed_files(args.base, args.head)
    contract = evaluate_contract(files)
    drift = evaluate_drift(files)

    needs_fix = bool(contract.get("blocked")) or drift.status == "drift"
    if not needs_fix:
        print("[auto-doc-fix] no docs auto-fix required for this PR")
        return 0

    report = {
        "interface_changed": list(contract.get("interface_changed", [])),
        "openapi_changed": list(drift.openapi_changed),
        "sdk_changed": list(drift.sdk_changed),
    }

    output_dir = args.output_dir.strip() or f"{args.docs_root}/reference/pr-auto-fixes"
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"pr-{args.pr_number}-api-doc-sync.md"
    out_file.write_text(_build_doc_content(args.pr_number, files, report), encoding="utf-8")
    print(f"[auto-doc-fix] generated docs sync note: {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

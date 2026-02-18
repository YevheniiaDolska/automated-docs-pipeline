#!/usr/bin/env python3
"""Detect API/SDK drift against reference documentation touchpoints in a PR."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

OPENAPI_PATTERNS = (
    r"openapi.*\.(ya?ml|json)$",
    r"swagger.*\.(ya?ml|json)$",
    r"api-spec.*\.(ya?ml|json)$",
)

SDK_PATTERNS = (
    r"^sdk/",
    r"^clients/",
    r"generated/(sdk|client)",
)

REFERENCE_DOC_PATTERNS = (
    r"^docs/reference/",
    r"^templates/api-reference\.md$",
    r"^templates/sdk-reference\.md$",
    r"^docs/how-to/.*api",
)


@dataclass
class DriftReport:
    status: str
    summary: str
    openapi_changed: list[str]
    sdk_changed: list[str]
    reference_docs_changed: list[str]


def _changed_files(base_ref: str, head_ref: str) -> list[str]:
    cmd = ["git", "diff", "--name-only", f"{base_ref}...{head_ref}"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _select(files: list[str], patterns: tuple[str, ...]) -> list[str]:
    return [path for path in files if any(re.search(pattern, path, re.IGNORECASE) for pattern in patterns)]


def _load_policy_pack(path: str | None) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    if path is None:
        return OPENAPI_PATTERNS, SDK_PATTERNS, REFERENCE_DOC_PATTERNS

    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Policy pack must be a mapping.")

    section = data.get("drift", {})
    if not isinstance(section, dict):
        raise ValueError("Policy pack drift section must be a mapping.")

    openapi_patterns = tuple(section.get("openapi_patterns", list(OPENAPI_PATTERNS)))
    sdk_patterns = tuple(section.get("sdk_patterns", list(SDK_PATTERNS)))
    reference_patterns = tuple(section.get("reference_doc_patterns", list(REFERENCE_DOC_PATTERNS)))

    if not openapi_patterns and not sdk_patterns:
        raise ValueError("Policy pack must define openapi_patterns and/or sdk_patterns.")
    if not reference_patterns:
        raise ValueError("Policy pack reference_doc_patterns cannot be empty.")

    return openapi_patterns, sdk_patterns, reference_patterns


def evaluate(
    files: list[str],
    openapi_patterns: tuple[str, ...] = OPENAPI_PATTERNS,
    sdk_patterns: tuple[str, ...] = SDK_PATTERNS,
    reference_doc_patterns: tuple[str, ...] = REFERENCE_DOC_PATTERNS,
) -> DriftReport:
    openapi_changed = _select(files, openapi_patterns)
    sdk_changed = _select(files, sdk_patterns)
    reference_docs_changed = _select(files, reference_doc_patterns)

    if not openapi_changed and not sdk_changed:
        return DriftReport(
            status="ok",
            summary="No API/SDK signature changes detected.",
            openapi_changed=openapi_changed,
            sdk_changed=sdk_changed,
            reference_docs_changed=reference_docs_changed,
        )

    if reference_docs_changed:
        return DriftReport(
            status="ok",
            summary="API/SDK changes are accompanied by reference docs updates.",
            openapi_changed=openapi_changed,
            sdk_changed=sdk_changed,
            reference_docs_changed=reference_docs_changed,
        )

    return DriftReport(
        status="drift",
        summary="API/SDK changes detected without reference documentation updates.",
        openapi_changed=openapi_changed,
        sdk_changed=sdk_changed,
        reference_docs_changed=reference_docs_changed,
    )


def _render_markdown(report: DriftReport) -> str:
    def _list(items: list[str]) -> str:
        if not items:
            return "- none"
        return "\n".join(f"- `{item}`" for item in items)

    return (
        "# API/SDK Drift Report\n\n"
        f"Status: **{report.status.upper()}**\n\n"
        f"{report.summary}\n\n"
        "## OpenAPI changes\n\n"
        f"{_list(report.openapi_changed)}\n\n"
        "## SDK/client changes\n\n"
        f"{_list(report.sdk_changed)}\n\n"
        "## Reference docs changes\n\n"
        f"{_list(report.reference_docs_changed)}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Check API/SDK drift versus reference docs")
    parser.add_argument("--base", required=True, help="Base commit/branch")
    parser.add_argument("--head", required=True, help="Head commit/branch")
    parser.add_argument("--json-output", default="reports/api_sdk_drift_report.json")
    parser.add_argument("--md-output", default="reports/api_sdk_drift_report.md")
    parser.add_argument("--policy-pack", help="Optional policy pack YAML path")
    args = parser.parse_args()

    files = _changed_files(args.base, args.head)
    openapi_patterns, sdk_patterns, reference_doc_patterns = _load_policy_pack(args.policy_pack)
    report = evaluate(files, openapi_patterns, sdk_patterns, reference_doc_patterns)

    json_path = Path(args.json_output)
    md_path = Path(args.md_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")

    print(f"Drift report JSON: {json_path}")
    print(f"Drift report Markdown: {md_path}")
    print(report.summary)

    return 1 if report.status == "drift" else 0


if __name__ == "__main__":
    raise SystemExit(main())

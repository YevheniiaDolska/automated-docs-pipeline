#!/usr/bin/env python3
"""Block PRs when public interface changes are not paired with docs updates."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

INTERFACE_PATTERNS = (
    r"^api/",
    r"openapi.*\.(ya?ml|json)$",
    r"swagger.*\.(ya?ml|json)$",
    r"api-spec.*\.(ya?ml|json)$",
    r"^src/.*/(routes|controllers|handlers|public|sdk)/",
    r"^sdk/",
    r"^clients/",
)

DOC_PATTERNS = (
    r"^docs/",
    r"^templates/",
    r"^\.vscode/docs\.code-snippets$",
    r"^README_SETUP\.md$",
    r"^SETUP_GUIDE\.md$",
    r"^SETUP_FOR_PROJECTS\.md$",
)


def _changed_files(base_ref: str, head_ref: str) -> list[str]:
    cmd = ["git", "diff", "--name-only", f"{base_ref}...{head_ref}"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return files


def _matches_any(path: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, path, re.IGNORECASE) for pattern in patterns)


def _load_policy_pack(path: str | None) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if path is None:
        return INTERFACE_PATTERNS, DOC_PATTERNS

    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Policy pack must be a mapping.")

    section = data.get("docs_contract", {})
    if not isinstance(section, dict):
        raise ValueError("Policy pack docs_contract section must be a mapping.")

    interface_patterns = tuple(section.get("interface_patterns", list(INTERFACE_PATTERNS)))
    doc_patterns = tuple(section.get("doc_patterns", list(DOC_PATTERNS)))

    if not interface_patterns:
        raise ValueError("Policy pack interface_patterns cannot be empty.")
    if not doc_patterns:
        raise ValueError("Policy pack doc_patterns cannot be empty.")

    return interface_patterns, doc_patterns


def evaluate_contract(
    files: list[str],
    interface_patterns: tuple[str, ...] = INTERFACE_PATTERNS,
    doc_patterns: tuple[str, ...] = DOC_PATTERNS,
) -> dict[str, Any]:
    interface_changed = [path for path in files if _matches_any(path, interface_patterns)]
    docs_changed = [path for path in files if _matches_any(path, doc_patterns)]

    return {
        "interface_changed": interface_changed,
        "docs_changed": docs_changed,
        "blocked": bool(interface_changed) and not bool(docs_changed),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check docs contract for interface changes")
    parser.add_argument("--base", required=True, help="Base commit/branch")
    parser.add_argument("--head", required=True, help="Head commit/branch")
    parser.add_argument("--json-output", help="Optional output path for JSON report")
    parser.add_argument("--policy-pack", help="Optional policy pack YAML path")
    args = parser.parse_args()

    files = _changed_files(args.base, args.head)
    interface_patterns, doc_patterns = _load_policy_pack(args.policy_pack)
    report = evaluate_contract(files, interface_patterns, doc_patterns)

    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Changed files: {len(files)}")
    print(f"Interface files changed: {len(report['interface_changed'])}")
    print(f"Docs files changed: {len(report['docs_changed'])}")

    if report["blocked"]:
        print("Blocking PR: public interface changed but docs were not updated.")
        return 1

    print("Docs contract check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

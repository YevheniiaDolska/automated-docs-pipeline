#!/usr/bin/env python3
"""Lightweight compliance gate for production coding rules.

This checker enforces high-signal bans from main_rules.md:
- no placeholder stubs (`pass`, TODO implement, NotImplementedError)
- no broad swallow handlers (`except Exception: pass`)
- no hardcoded credential-like constants
- no `shell=True` in subprocess calls
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCAN_DIRS = ("scripts", "packages", "docsops/scripts")
DEFAULT_EXCLUDE_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    "tests",
}


RULE_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "broad-except-pass",
        re.compile(r"except\s+Exception(?:\s+as\s+\w+)?\s*:\s*\n\s*pass\b", re.MULTILINE),
        "Do not swallow broad exceptions; handle explicitly and log.",
    ),
    (
        "todo-implement",
        re.compile(r"#\s*TODO\s*:\s*implement", re.IGNORECASE),
        "TODO-implement stubs are not allowed in production code.",
    ),
    (
        "not-implemented",
        re.compile(r"raise\s+NotImplementedError\b"),
        "NotImplementedError is not allowed in production code paths.",
    ),
    (
        "placeholder-return",
        re.compile(r"return\s+(?:0|None|False|\"\"|''|\[\]|\{\})\s*#\s*placeholder", re.IGNORECASE),
        "Placeholder return values are not allowed.",
    ),
    (
        "hardcoded-secrets",
        re.compile(
            r"^\s*(?:API_KEY|SECRET_KEY|PASSWORD|TOKEN)\s*=\s*[\"'][^\"'\n]{8,}[\"']\s*$",
            re.MULTILINE,
        ),
        "Hardcoded secrets are not allowed.",
    ),
    (
        "subprocess-shell-true",
        re.compile(r"subprocess\.(?:run|Popen)\([^)]*shell\s*=\s*True", re.DOTALL),
        "shell=True is forbidden by production rules.",
    ),
]


def _should_skip(path: Path) -> bool:
    if path.suffix != ".py":
        return True
    return any(part in DEFAULT_EXCLUDE_PARTS for part in path.parts)


def _iter_python_files(scan_dirs: list[Path]) -> list[Path]:
    files: list[Path] = []
    for base in scan_dirs:
        if not base.exists():
            continue
        if base.is_file() and base.suffix == ".py":
            if not _should_skip(base):
                files.append(base)
            continue
        for path in base.rglob("*.py"):
            if not _should_skip(path):
                files.append(path)
    return sorted(set(files))


def _scan_file(path: Path) -> list[tuple[str, int, str]]:
    findings: list[tuple[str, int, str]] = []
    text = path.read_text(encoding="utf-8")
    for rule_name, pattern, message in RULE_PATTERNS:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append((rule_name, line, message))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check repository compliance with main_rules bans.")
    parser.add_argument(
        "--scan-dir",
        action="append",
        default=[],
        help="Directory or file to scan (can be repeated). Defaults: scripts, packages, docsops/scripts.",
    )
    args = parser.parse_args()

    targets = args.scan_dir or list(DEFAULT_SCAN_DIRS)
    scan_dirs = [(REPO_ROOT / target).resolve() for target in targets]
    files = _iter_python_files(scan_dirs)
    if not files:
        print("[main_rules] no Python files to scan.")
        return 0

    violations: list[str] = []
    for path in files:
        rel = path.relative_to(REPO_ROOT)
        findings = _scan_file(path)
        for rule_name, line, message in findings:
            violations.append(f"{rel}:{line}: [{rule_name}] {message}")

    if violations:
        print("[main_rules] compliance failed:")
        for item in violations:
            print(f"  - {item}")
        return 1

    print(f"[main_rules] compliance passed ({len(files)} files scanned).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

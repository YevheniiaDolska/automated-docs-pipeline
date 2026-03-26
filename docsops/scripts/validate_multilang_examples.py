#!/usr/bin/env python3
"""Validate multi-language code examples in markdown files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


FENCE_RE = re.compile(r"^```([a-zA-Z0-9\-_+]*)\s*$")
TAB_RE = re.compile(r'^===\s+"([^"]+)"\s*$')


LANG_SYNONYMS: dict[str, set[str]] = {
    "curl": {"curl", "bash", "shell", "sh"},
    "javascript": {"javascript", "js", "node", "nodejs"},
    "python": {"python", "py"},
    "typescript": {"typescript", "ts"},
    "go": {"go", "golang"},
    "ruby": {"ruby", "rb"},
    "java": {"java"},
}


@dataclass
class Issue:
    file: str
    message: str


@dataclass
class CodeFence:
    language: str
    content: str


def _normalize_language(value: str) -> str:
    key = value.strip().lower()
    for canonical, variants in LANG_SYNONYMS.items():
        if key == canonical or key in variants:
            return canonical
    return key


def _is_api_doc(path: Path) -> bool:
    p = path.as_posix().lower()
    name = path.name.lower()
    if "/reference/api" in p or "/assets/api" in p or "openapi" in p:
        return True
    if "api" in name or "playground" in name:
        return True
    if "/how-to/" in p and "api" in name:
        return True
    return False


def _extract_tab_groups(lines: list[str]) -> list[set[str]]:
    groups: list[set[str]] = []
    idx = 0
    while idx < len(lines):
        tab_match = TAB_RE.match(lines[idx].strip())
        if not tab_match:
            idx += 1
            continue

        group_langs: set[str] = set()
        while idx < len(lines):
            tab_match = TAB_RE.match(lines[idx].strip())
            if not tab_match:
                break
            tab_label_lang = _normalize_language(tab_match.group(1))
            idx += 1

            while idx < len(lines):
                stripped = lines[idx].rstrip("\n")
                if TAB_RE.match(stripped.strip()):
                    break
                fence_open = FENCE_RE.match(stripped.strip())
                if fence_open:
                    lang = _normalize_language(fence_open.group(1))
                    if lang:
                        group_langs.add(lang)
                    idx += 1
                    while idx < len(lines):
                        if lines[idx].strip() == "```":
                            idx += 1
                            break
                        idx += 1
                    continue
                idx += 1

            if tab_label_lang:
                group_langs.add(tab_label_lang)
            if idx < len(lines) and TAB_RE.match(lines[idx].strip()):
                continue
            break

        groups.append(group_langs)
    return groups


def _extract_fences(lines: list[str]) -> list[CodeFence]:
    fences: list[CodeFence] = []
    in_block = False
    language = ""
    body: list[str] = []
    for raw in lines:
        stripped = raw.strip()
        if not in_block:
            open_match = FENCE_RE.match(stripped)
            if not open_match:
                continue
            language = _normalize_language(open_match.group(1))
            body = []
            in_block = True
            continue
        if stripped == "```":
            fences.append(CodeFence(language=language, content="\n".join(body)))
            in_block = False
            continue
        body.append(raw)
    return fences


def _requires_multilang(fences: list[CodeFence]) -> bool:
    for fence in fences:
        lang = fence.language
        content = fence.content.lower()
        if lang == "curl":
            return True
        if lang in {"bash", "shell", "sh"} and "curl " in content:
            return True
        if lang in {"javascript", "typescript", "python", "go", "ruby", "java"} and (
            "fetch(" in content
            or "axios." in content
            or "requests." in content
            or "httpx." in content
            or "httpclient" in content
        ):
            return True
    return False


def validate_docs(
    docs_dir: Path,
    scope: str,
    required_languages: list[str],
) -> list[Issue]:
    issues: list[Issue] = []
    required = {_normalize_language(v) for v in required_languages if v.strip()}
    if not required:
        required = {"curl", "javascript", "python"}

    for md in sorted(docs_dir.rglob("*.md")):
        if scope == "api" and not _is_api_doc(md):
            continue
        lines = md.read_text(encoding="utf-8").splitlines()
        fences = _extract_fences(lines)
        if not fences:
            continue
        if not _requires_multilang(fences):
            continue
        groups = _extract_tab_groups(lines)
        if not groups:
            issues.append(
                Issue(
                    file=str(md),
                    message=(
                        "Missing language tabs. Add a tab group with languages: "
                        + ", ".join(sorted(required))
                    ),
                )
            )
            continue
        if not any(required.issubset(group) for group in groups):
            issues.append(
                Issue(
                    file=str(md),
                    message=(
                        "No tab group contains required languages: "
                        + ", ".join(sorted(required))
                    ),
                )
            )
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate multi-language code examples")
    parser.add_argument("--docs-dir", default="docs", help="Docs root directory")
    parser.add_argument("--scope", choices=["api", "all"], default="all")
    parser.add_argument(
        "--required-languages",
        default="curl,javascript,python",
        help="Comma-separated required languages per tab group",
    )
    parser.add_argument(
        "--report",
        default="reports/multilang_examples_report.json",
        help="JSON report output path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    docs_dir = Path(args.docs_dir)
    if not docs_dir.exists():
        print(f"docs directory not found: {docs_dir}", file=sys.stderr)
        return 2

    required = [v.strip() for v in str(args.required_languages).split(",") if v.strip()]
    issues = validate_docs(docs_dir, args.scope, required)

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": {
            "valid": len(issues) == 0,
            "issue_count": len(issues),
            "scope": args.scope,
            "required_languages": required,
        },
        "issues": [{"file": i.file, "message": i.message} for i in issues],
    }
    report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    if issues:
        print(f"Multi-language examples: {len(issues)} issue(s)")
        for issue in issues:
            print(f"  {issue.file}: {issue.message}")
        return 1

    print("Multi-language examples: all checks pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

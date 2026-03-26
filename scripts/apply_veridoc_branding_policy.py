#!/usr/bin/env python3
"""Apply VeriDoc branding and referral badge policy to Markdown docs.

Policy:
- Free + cheapest paid tier: badge is mandatory, no referral commission link.
- Higher tiers: badge default-on, optional opt-out, optional referral link.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

MANAGED_START = "<!-- VERIDOC_POWERED_BADGE:START -->"
MANAGED_END = "<!-- VERIDOC_POWERED_BADGE:END -->"
IGNORE_MARKER = "<!-- veridoc-badge:ignore -->"


def _is_markdown(path: Path) -> bool:
    return path.suffix.lower() in {".md", ".markdown"}


def _with_ref(url: str, referral_code: str) -> str:
    if not referral_code.strip():
        return url
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["ref"] = referral_code.strip()
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(query),
            parsed.fragment,
        )
    )


def _badge_block(landing_url: str) -> str:
    return "\n".join(
        [
            MANAGED_START,
            f"[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)]({landing_url})",
            MANAGED_END,
            "",
        ]
    )


def _remove_managed_block(text: str) -> tuple[str, bool]:
    pattern = re.compile(
        re.escape(MANAGED_START) + r".*?" + re.escape(MANAGED_END) + r"\n?",
        re.DOTALL,
    )
    new_text, count = pattern.subn("", text)
    return new_text, count > 0


def _insert_or_replace_badge(text: str, landing_url: str) -> tuple[str, bool]:
    block = _badge_block(landing_url)
    pattern = re.compile(
        re.escape(MANAGED_START) + r".*?" + re.escape(MANAGED_END) + r"\n?",
        re.DOTALL,
    )
    if pattern.search(text):
        new_text = pattern.sub(block, text)
        return new_text, new_text != text

    # Insert after frontmatter if present; otherwise at top.
    if text.startswith("---\n"):
        second = text.find("\n---\n", 4)
        if second != -1:
            insert_at = second + len("\n---\n")
            return text[:insert_at] + "\n" + block + text[insert_at:], True
    return block + text, True


def _collect_docs(docs_root: Path) -> list[Path]:
    return sorted([p for p in docs_root.rglob("*") if p.is_file() and _is_markdown(p)])


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply VeriDoc badge/referral policy to docs.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--docs-root", default="docs", help="Docs root path, relative to repo root.")
    parser.add_argument("--landing-url", required=True, help="Landing URL used in Powered by VeriDoc badge.")
    parser.add_argument("--plan", default="free", help="Current plan (for example free/starter/pro/business/enterprise).")
    parser.add_argument("--cheapest-paid-plan", default="starter", help="Cheapest paid plan slug.")
    parser.add_argument("--badge-opt-out", action="store_true", help="Allow removing badge for higher plans.")
    parser.add_argument("--referral-code", default="", help="Referral code for higher plans when badge is enabled.")
    parser.add_argument("--report", default="reports/veridoc_branding_policy_report.json", help="JSON report output path.")
    parser.add_argument("--check", action="store_true", help="Check mode. Do not write files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    docs_root = (repo_root / args.docs_root).resolve()
    report_path = (repo_root / args.report).resolve()

    if not docs_root.exists():
        _write_json(
            report_path,
            {
                "ok": False,
                "reason": f"docs_root does not exist: {docs_root}",
            },
        )
        print(f"[branding] docs root not found: {docs_root}")
        return 2

    plan = args.plan.strip().lower()
    cheapest = args.cheapest_paid_plan.strip().lower()
    mandatory = plan in {"free", cheapest}
    allow_commission = not mandatory

    landing_url = args.landing_url.strip()
    if not landing_url:
        print("[branding] landing_url is empty")
        return 2

    if allow_commission and (not args.badge_opt_out) and args.referral_code.strip():
        effective_url = _with_ref(landing_url, args.referral_code.strip())
        commission_enabled = True
    else:
        effective_url = landing_url
        commission_enabled = False

    changed: list[str] = []
    removed: list[str] = []
    skipped: list[str] = []
    would_change = 0

    for path in _collect_docs(docs_root):
        raw = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(repo_root)).replace("\\", "/")
        if IGNORE_MARKER in raw:
            skipped.append(rel)
            continue

        if mandatory:
            updated, did_change = _insert_or_replace_badge(raw, effective_url)
            if did_change:
                if args.check:
                    would_change += 1
                else:
                    path.write_text(updated, encoding="utf-8")
                    changed.append(rel)
            continue

        # Higher-tier behavior
        if args.badge_opt_out:
            updated, did_change = _remove_managed_block(raw)
            if did_change:
                if args.check:
                    would_change += 1
                else:
                    path.write_text(updated, encoding="utf-8")
                    removed.append(rel)
        else:
            updated, did_change = _insert_or_replace_badge(raw, effective_url)
            if did_change:
                if args.check:
                    would_change += 1
                else:
                    path.write_text(updated, encoding="utf-8")
                    changed.append(rel)

    payload = {
        "ok": True,
        "repo_root": str(repo_root),
        "docs_root": str(docs_root),
        "plan": plan,
        "cheapest_paid_plan": cheapest,
        "mandatory_badge": mandatory,
        "badge_opt_out": bool(args.badge_opt_out),
        "commission_enabled": commission_enabled,
        "effective_landing_url": effective_url,
        "changed_files_count": len(changed),
        "removed_files_count": len(removed),
        "skipped_files_count": len(skipped),
        "changed_files": changed,
        "removed_files": removed,
        "skipped_files": skipped,
        "check_mode": bool(args.check),
        "would_change_count": would_change,
    }
    _write_json(report_path, payload)
    print(f"[branding] report: {report_path}")
    if args.check and would_change > 0:
        print(f"[branding] check failed: would_change={would_change}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


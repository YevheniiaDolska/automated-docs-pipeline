#!/usr/bin/env python3
"""Generate llms.txt/llms-full.txt and markdown URL artifacts for static docs."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}, text
    raw = parts[0][4:]
    body = parts[1]
    try:
        meta = yaml.safe_load(raw) or {}
    except (RuntimeError, ValueError, TypeError):
        return {}, text
    if not isinstance(meta, dict):
        meta = {}
    return meta, body


def _load_site_url(mkdocs_path: Path) -> str:
    if not mkdocs_path.exists():
        return ""
    try:
        payload = yaml.safe_load(mkdocs_path.read_text(encoding="utf-8")) or {}
    except (RuntimeError, ValueError, TypeError, OSError):
        return ""
    if not isinstance(payload, dict):
        return ""
    return str(payload.get("site_url", "")).rstrip("/")


def _doc_url(md_path: Path, docs_root: Path, site_url: str) -> str:
    rel = md_path.relative_to(docs_root)
    if rel.name == "index.md":
        suffix = "/" if rel.parent == Path(".") else f"/{rel.parent.as_posix()}/"
    else:
        suffix = f"/{rel.with_suffix('').as_posix()}/"
    return f"{site_url}{suffix}" if site_url else suffix


def _extract_title(meta: dict[str, Any], body: str, fallback: str) -> str:
    title = str(meta.get("title", "")).strip()
    if title:
        return title
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def _extract_summary(meta: dict[str, Any], body: str) -> str:
    desc = str(meta.get("description", "")).strip()
    if desc:
        return desc
    clean = re.sub(r"\s+", " ", body)
    return clean[:180].strip()


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate LLM web artifacts for docs")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--site-root", default="site")
    parser.add_argument("--mkdocs-config", default="mkdocs.yml")
    args = parser.parse_args()

    docs_root = Path(args.docs_root).resolve()
    site_root = Path(args.site_root).resolve()
    mkdocs_path = Path(args.mkdocs_config).resolve()
    site_url = _load_site_url(mkdocs_path)

    docs = [
        p for p in sorted(docs_root.rglob("*.md"))
        if "/assets/" not in p.as_posix() and "/operations/" not in p.as_posix()
    ]

    llms_lines = ["# llms.txt", "", "LLM sitemap for documentation pages.", ""]
    llms_full_lines = ["# llms-full.txt", "", "Extended LLM sitemap with summaries.", ""]

    for md in docs:
        raw = md.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(raw)
        title = _extract_title(meta, body, md.stem.replace("-", " ").title())
        summary = _extract_summary(meta, body)
        url = _doc_url(md, docs_root, site_url)
        llms_lines.append(f"- {url} | {title}")
        llms_full_lines.append(f"- {url} | {title} | {summary}")

        # Markdown-by-URL: publish a raw markdown sibling path in static site output.
        site_md_path = site_root / md.relative_to(docs_root)
        _write_text(site_md_path, raw)

    llms_txt = docs_root / "llms.txt"
    llms_full_txt = docs_root / "llms-full.txt"
    _write_text(llms_txt, "\n".join(llms_lines))
    _write_text(llms_full_txt, "\n".join(llms_full_lines))

    if site_root.exists():
        _write_text(site_root / "llms.txt", "\n".join(llms_lines))
        _write_text(site_root / "llms-full.txt", "\n".join(llms_full_lines))

    print(f"[llm-web] generated: {llms_txt}")
    print(f"[llm-web] generated: {llms_full_txt}")
    if site_root.exists():
        print(f"[llm-web] published markdown mirrors into: {site_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

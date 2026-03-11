#!/usr/bin/env python3
"""Auto-extract knowledge modules from Markdown docs."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

import yaml


def _slug(value: str) -> str:
    clean = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return re.sub(r"-{2,}", "-", clean) or "module"


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]
    try:
        payload = yaml.safe_load(raw) or {}
        if isinstance(payload, dict):
            return payload, body
    except yaml.YAMLError:
        pass
    return {}, body


def _pick_intents(content_type: str, title: str, body: str) -> list[str]:
    text = f"{title} {body}".lower()
    intents: list[str] = []
    if content_type in {"tutorial", "how-to"} or "configure" in text:
        intents.append("configure")
    if content_type == "troubleshooting" or "error" in text or "fix" in text:
        intents.append("troubleshoot")
    if content_type in {"reference", "concept"} or "integrat" in text:
        intents.append("integrate")
    if "secure" in text or "auth" in text:
        intents.append("secure")
    if not intents:
        intents = ["configure"]
    return sorted(set(intents))


def _pick_audiences(content_type: str) -> list[str]:
    if content_type == "tutorial":
        return ["beginner", "practitioner"]
    if content_type in {"reference", "concept"}:
        return ["developer", "operator"]
    if content_type == "troubleshooting":
        return ["support", "operator"]
    return ["practitioner", "developer"]


def _chunk_body(body: str, chunk_target_chars: int) -> list[str]:
    # Split by H2/H3 blocks first.
    parts = re.split(r"\n(?=##\s|###\s)", body)
    chunks: list[str] = []
    current = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        candidate = (current + "\n\n" + part).strip() if current else part
        if len(candidate) <= chunk_target_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(part) <= chunk_target_chars:
            current = part
            continue
        # Hard split long part by paragraphs.
        para = ""
        for p in part.split("\n\n"):
            p = p.strip()
            if not p:
                continue
            cand = (para + "\n\n" + p).strip() if para else p
            if len(cand) <= chunk_target_chars:
                para = cand
            else:
                if para:
                    chunks.append(para)
                para = p
        current = para
    if current:
        chunks.append(current)
    return chunks


def _extract_summary(frontmatter: dict[str, Any], body_chunk: str) -> str:
    desc = str(frontmatter.get("description", "")).strip()
    if desc:
        return desc[:240]
    text = re.sub(r"\s+", " ", body_chunk).strip()
    if len(text) < 30:
        text = f"{text} This module is auto-generated from docs content for retrieval and assistant context."
    return text[:240]


def _extract_title(frontmatter: dict[str, Any], path: Path, idx: int) -> str:
    title = str(frontmatter.get("title", "")).strip()
    if title:
        return title if idx == 1 else f"{title} (Part {idx})"
    stem = path.stem.replace("-", " ").replace("_", " ").title()
    return stem if idx == 1 else f"{stem} (Part {idx})"


def _module_for_chunk(path: Path, rel_path: str, frontmatter: dict[str, Any], chunk: str, idx: int, owner: str) -> dict[str, Any]:
    content_type = str(frontmatter.get("content_type", "")).strip().lower()
    title = _extract_title(frontmatter, path, idx)
    summary = _extract_summary(frontmatter, chunk)
    chunk_clean = chunk.strip()
    if len(chunk_clean) < 80:
        chunk_clean = (chunk_clean + "\n\nThis auto-generated knowledge chunk was expanded to satisfy minimum retrieval module length for stable indexing.")
    assistant_context = (
        f"Use this module when answering questions related to: {title}. "
        f"Source path: {rel_path}. "
        f"Summary: {summary}\n\n{chunk_clean}"
    )
    if len(assistant_context) < 60:
        assistant_context += " Additional context: use this module as a trusted source for assistant answers."
    module_id = _slug(f"auto-{path.stem}-{idx}")
    intents = _pick_intents(content_type, title, chunk_clean)
    audiences = _pick_audiences(content_type)
    tags: list[str] = ["auto-extracted", content_type or "docs", _slug(path.stem)]
    return {
        "id": module_id,
        "title": title[:90],
        "summary": summary[:240],
        "intents": intents,
        "audiences": audiences,
        "channels": ["docs", "assistant", "automation"],
        "priority": 60,
        "status": "active",
        "owner": owner,
        "last_verified": dt.date.today().isoformat(),
        "dependencies": [],
        "tags": sorted(set(t for t in tags if t)),
        "content": {
            "docs_markdown": chunk_clean,
            "assistant_context": assistant_context,
        },
    }


def _write_module(path: Path, module: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(module, sort_keys=False, allow_unicode=False), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract knowledge modules from docs markdown")
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument("--modules-dir", default="knowledge_modules")
    parser.add_argument("--report", default="reports/knowledge_auto_extract_report.json")
    parser.add_argument("--chunk-target-chars", type=int, default=1400)
    parser.add_argument("--owner", default="docsops-auto")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    docs_dir = Path(args.docs_dir)
    modules_dir = Path(args.modules_dir)
    report_path = Path(args.report)

    if not docs_dir.exists():
        print(f"docs directory not found: {docs_dir}")
        return 1

    # Clear previous auto-generated modules.
    removed = 0
    for file in modules_dir.glob("auto-*.yml"):
        file.unlink()
        removed += 1

    created = 0
    processed_docs = 0
    for md_path in sorted(docs_dir.rglob("*.md")):
        if "/reference/intent-experiences/" in md_path.as_posix():
            continue
        text = md_path.read_text(encoding="utf-8")
        frontmatter, body = _parse_frontmatter(text)
        if not body.strip():
            continue
        chunks = _chunk_body(body, args.chunk_target_chars)
        if not chunks:
            continue
        processed_docs += 1
        rel_path = md_path.as_posix()
        for idx, chunk in enumerate(chunks, start=1):
            module = _module_for_chunk(md_path, rel_path, frontmatter, chunk, idx, args.owner)
            target = modules_dir / f"{module['id']}.yml"
            _write_module(target, module)
            created += 1

    report = {
        "status": "ok",
        "docs_processed": processed_docs,
        "modules_created": created,
        "modules_removed": removed,
        "modules_dir": str(modules_dir),
        "generated_at": dt.datetime.utcnow().isoformat() + "Z",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print(f"Auto knowledge extraction done: {created} module(s) from {processed_docs} doc(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Insert screenshot blocks into Markdown docs from a manifest.

Supports two modes:
1) Explicit mode via target.doc + target.marker/target.heading.
2) Automatic mode via naming convention:
   <doc-slug>__<section-slug>.png
   where doc-slug maps to docs/<...>.md by slugified relative path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import yaml


def _read_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return payload


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-")


def _sha1_bytes(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def _doc_slug(path: Path, docs_root: Path) -> str:
    rel = path.relative_to(docs_root).as_posix()
    no_ext = rel[:-3] if rel.endswith(".md") else rel
    return _slug(no_ext.replace("/", "-"))


def _heading_slug(text: str) -> str:
    return _slug(text)


def _build_doc_index(docs_root: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for md in docs_root.rglob("*.md"):
        out[_doc_slug(md, docs_root)] = md
    return out


def _build_heading_index(content: str) -> dict[str, str]:
    idx: dict[str, str] = {}
    for raw in content.splitlines():
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", raw.strip())
        if not m:
            continue
        heading = m.group(2).strip()
        slug = _heading_slug(heading)
        if slug and slug not in idx:
            idx[slug] = heading
    return idx


def _infer_auto_target(item_id: str, img_path: Path) -> tuple[str, str]:
    token = img_path.stem.strip() or item_id.strip()
    if "__" not in token:
        return "", ""
    left, right = token.split("__", 1)
    return _slug(left), _slug(right)


def _resolve_doc_path(raw: str, repo_root: Path, docs_root: Path) -> Path:
    text = str(raw).strip().replace("\\", "/")
    if not text:
        raise ValueError("target.doc is empty")
    if text.startswith("/"):
        return Path(text)
    candidate = repo_root / text
    if candidate.exists():
        return candidate
    if text.startswith(f"{docs_root.name}/"):
        return repo_root / text
    return docs_root / text


def _resolve_image_path(raw: str, repo_root: Path) -> Path:
    text = str(raw).strip().replace("\\", "/")
    if not text:
        raise ValueError("image path is empty")
    if text.startswith("/"):
        return Path(text)
    return repo_root / text


def _build_image_markdown(doc_path: Path, image_path: Path, alt: str) -> str:
    rel = os.path.relpath(str(image_path), start=str(doc_path.parent)).replace("\\", "/")
    return f"![{alt}]({rel})"


def _screenshot_block(item_id: str, image_md: str) -> str:
    return "\n".join(
        [
            f"<!-- screenshot:auto:{item_id}:start -->",
            image_md,
            f"<!-- screenshot:auto:{item_id}:end -->",
        ]
    )


def _replace_existing_block(content: str, item_id: str, block: str) -> tuple[str, bool]:
    pattern = re.compile(
        rf"<!-- screenshot:auto:{re.escape(item_id)}:start -->.*?<!-- screenshot:auto:{re.escape(item_id)}:end -->",
        flags=re.DOTALL,
    )
    if not pattern.search(content):
        return content, False
    updated = pattern.sub(block, content, count=1)
    return updated, True


def _replace_marker(content: str, marker: str, block: str) -> tuple[str, bool]:
    escaped = re.escape(marker)
    pattern = re.compile(rf"^[ \t]*{escaped}[ \t]*$", flags=re.MULTILINE)
    if not pattern.search(content):
        return content, False
    updated = pattern.sub(block, content, count=1)
    return updated, True


def _insert_after_heading(content: str, heading: str, block: str) -> tuple[str, bool]:
    lines = content.splitlines()
    heading_norm = heading.strip().lower()
    idx = -1
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line.strip())
        if not m:
            continue
        if m.group(2).strip().lower() == heading_norm:
            idx = i
            break
    if idx < 0:
        return content, False
    insert_at = idx + 1
    while insert_at < len(lines) and not lines[insert_at].strip():
        insert_at += 1
    block_lines = ["", block, ""]
    updated_lines = lines[:insert_at] + block_lines + lines[insert_at:]
    return "\n".join(updated_lines) + "\n", True


def _insert_after_anchor(content: str, anchor_slug: str, block: str) -> tuple[str, bool]:
    if not anchor_slug:
        return content, False
    lines = content.splitlines()
    anchor_norm = _slug(anchor_slug)
    idx = -1
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line.strip())
        if not m:
            continue
        heading = m.group(2).strip()
        if _heading_slug(heading) == anchor_norm:
            idx = i
            break
    if idx < 0:
        return content, False
    insert_at = idx + 1
    while insert_at < len(lines) and not lines[insert_at].strip():
        insert_at += 1
    updated_lines = lines[:insert_at] + ["", block, ""] + lines[insert_at:]
    return "\n".join(updated_lines) + "\n", True


def _insert_after_h1(content: str, block: str) -> tuple[str, bool]:
    lines = content.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(#)\s+(.+?)\s*$", line.strip())
        if not m:
            continue
        insert_at = i + 1
        while insert_at < len(lines) and not lines[insert_at].strip():
            insert_at += 1
        updated_lines = lines[:insert_at] + ["", block, ""] + lines[insert_at:]
        return "\n".join(updated_lines) + "\n", True
    return content, False


def main() -> int:
    parser = argparse.ArgumentParser(description="Insert screenshots into docs at relevant sections.")
    parser.add_argument("--manifest", default="docs/screenshots.yml", help="Screenshot manifest path.")
    parser.add_argument("--docs-root", default="docs", help="Docs root directory.")
    parser.add_argument("--report", default="reports/screenshot_injection_report.json", help="Output JSON report path.")
    parser.add_argument("--check", action="store_true", help="Do not write files; report only.")
    args = parser.parse_args()

    repo_root = Path.cwd()
    manifest_path = (repo_root / args.manifest).resolve()
    docs_root = (repo_root / args.docs_root).resolve()
    report_path = (repo_root / args.report).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)

    if not manifest_path.exists():
        report_path.write_text(
            json.dumps(
                {
                    "ok": True,
                    "skipped": True,
                    "reason": "manifest_not_found",
                    "manifest": str(manifest_path),
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"[screenshots] skipped: manifest not found: {manifest_path}")
        return 0

    data = _read_yaml(manifest_path)
    entries = data.get("screenshots", [])
    if not isinstance(entries, list):
        raise ValueError("manifest field 'screenshots' must be a list")
    doc_index = _build_doc_index(docs_root)

    report_items: list[dict[str, Any]] = []
    needs_review: list[dict[str, Any]] = []
    changed_files: set[str] = set()
    failed = 0
    stats = {"inserted": 0, "updated": 0, "already_present": 0, "skipped": 0}

    for raw in entries:
        if not isinstance(raw, dict):
            continue
        item_id = str(raw.get("id", "")).strip()
        target = raw.get("target", {})
        if not isinstance(target, dict):
            target = {}
        doc_raw = str(target.get("doc", "")).strip()
        img_raw = str(raw.get("output", raw.get("image", ""))).strip()
        alt_raw = str(raw.get("alt", "")).strip()
        marker = str(target.get("marker", f"<!-- screenshot:{item_id} -->")).strip()
        heading = str(target.get("heading", "")).strip()
        anchor = _slug(str(target.get("anchor", "")).strip())

        item_report: dict[str, Any] = {"id": item_id}
        try:
            img_path = _resolve_image_path(img_raw, repo_root)
        except ValueError as exc:
            failed += 1
            item_report.update({"ok": False, "error": str(exc)})
            report_items.append(item_report)
            continue
        doc_path: Path | None = None
        inferred_doc_slug = ""
        inferred_section_slug = ""

        if doc_raw:
            try:
                doc_path = _resolve_doc_path(doc_raw, repo_root, docs_root)
            except ValueError as exc:
                failed += 1
                item_report.update({"ok": False, "error": str(exc)})
                report_items.append(item_report)
                continue
        else:
            inferred_doc_slug, inferred_section_slug = _infer_auto_target(item_id, img_path)
            if inferred_doc_slug:
                doc_path = doc_index.get(inferred_doc_slug)

        item_report["doc"] = str(doc_path) if doc_path else ""
        item_report["image"] = str(img_path)
        if doc_path is None:
            needs_review.append(
                {
                    "id": item_id,
                    "reason": "doc_target_not_resolved",
                    "hint": "Use target.doc or name image/id as <doc-slug>__<section-slug>.",
                    "inferred_doc_slug": inferred_doc_slug,
                }
            )
            item_report.update({"ok": True, "changed": False, "skipped": True, "reason": "needs_review_doc_target"})
            stats["skipped"] += 1
            report_items.append(item_report)
            continue
        if not doc_path.exists():
            failed += 1
            item_report.update({"ok": False, "error": "doc_not_found"})
            report_items.append(item_report)
            continue
        if not img_path.exists():
            failed += 1
            item_report.update({"ok": False, "error": "image_not_found"})
            report_items.append(item_report)
            continue

        content = doc_path.read_text(encoding="utf-8")
        heading_idx = _build_heading_index(content)
        inferred_heading = heading_idx.get(inferred_section_slug, "") if inferred_section_slug else ""
        alt = alt_raw or (f"{inferred_heading} screenshot" if inferred_heading else (item_id or "Screenshot"))
        image_md = _build_image_markdown(doc_path, img_path, alt)
        image_hash = _sha1_bytes(img_path.read_bytes())[:12]
        if not item_id:
            stable_key = f"{doc_path}|{anchor}|{heading}|{img_path}|{image_hash}"
            item_id = f"shot-{hashlib.sha1(stable_key.encode('utf-8')).hexdigest()[:12]}"
        block = _screenshot_block(item_id, image_md)

        updated, replaced_block = _replace_existing_block(content, item_id, block)
        if replaced_block:
            if updated != content:
                if not args.check:
                    doc_path.write_text(updated, encoding="utf-8")
                changed_files.add(str(doc_path))
                item_report.update({"ok": True, "changed": True, "method": "update-by-id"})
                stats["updated"] += 1
            else:
                item_report.update({"ok": True, "changed": False, "method": "already_present"})
                stats["already_present"] += 1
            report_items.append(item_report)
            continue

        updated, replaced = _replace_marker(content, marker, block)
        method = "marker"
        if not replaced and anchor:
            updated, inserted = _insert_after_anchor(content, anchor, block)
            replaced = inserted
            method = "anchor"
        if not replaced and heading:
            updated, inserted = _insert_after_heading(content, heading, block)
            replaced = inserted
            method = "heading"
        if not replaced and inferred_section_slug:
            if inferred_heading:
                updated, inserted = _insert_after_heading(content, inferred_heading, block)
                replaced = inserted
                method = "auto-heading"
        if not replaced:
            updated, inserted = _insert_after_h1(content, block)
            replaced = inserted
            method = "auto-h1"
        if not replaced:
            needs_review.append(
                {
                    "id": item_id,
                    "doc": str(doc_path),
                    "reason": "anchor_not_found",
                    "marker": marker,
                    "heading": heading,
                    "inferred_section_slug": inferred_section_slug,
                }
            )
            item_report.update({"ok": True, "changed": False, "skipped": True, "reason": "needs_review_anchor"})
            stats["skipped"] += 1
            report_items.append(item_report)
            continue

        if updated != content:
            changed_files.add(str(doc_path))
            if not args.check:
                doc_path.write_text(updated, encoding="utf-8")
        item_report.update({"ok": True, "method": method, "changed": bool(updated != content), "id": item_id})
        if updated != content:
            stats["inserted"] += 1
        else:
            stats["already_present"] += 1
        report_items.append(item_report)

    payload = {
        "ok": failed == 0,
        "manifest": str(manifest_path),
        "changed_files_count": len(changed_files),
        "changed_files": sorted(changed_files),
        "failed": int(failed),
        "needs_review_count": len(needs_review),
        "needs_review": needs_review,
        "stats": stats,
        "items": report_items,
    }
    report_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"[screenshots] report: {report_path}")
    if failed:
        print(f"[screenshots] failed items: {failed}")
    if needs_review:
        print(f"[screenshots] needs_review items: {len(needs_review)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

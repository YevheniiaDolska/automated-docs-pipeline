#!/usr/bin/env python3
"""Generate retrieval index for module-level AI and search consumption."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def _load_modules(modules_dir: Path) -> list[dict[str, Any]]:
    modules: list[dict[str, Any]] = []
    for path in sorted(modules_dir.glob("*.yml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload["source_file"] = str(path)
            modules.append(payload)
    return modules


def _module_to_index_record(module: dict[str, Any]) -> dict[str, Any]:
    content = module.get("content", {})
    metadata = module.get("metadata", {}) if isinstance(module.get("metadata"), dict) else {}
    semantic = module.get("semantic", {}) if isinstance(module.get("semantic"), dict) else {}
    docs_markdown = str(content.get("docs_markdown", "")).strip()
    assistant_context = str(content.get("assistant_context", "")).strip()

    return {
        "objectID": module.get("id"),
        "id": module.get("id"),
        "title": module.get("title"),
        "summary": module.get("summary"),
        "status": module.get("status"),
        "priority": module.get("priority"),
        "owner": module.get("owner"),
        "last_verified": module.get("last_verified"),
        "intents": module.get("intents", []),
        "audiences": module.get("audiences", []),
        "channels": module.get("channels", []),
        "dependencies": module.get("dependencies", []),
        "tags": module.get("tags", []),
        "docs_excerpt": docs_markdown[:400],
        "assistant_excerpt": assistant_context[:300],
        "url": metadata.get("url", ""),
        "heading": metadata.get("heading", ""),
        "version": metadata.get("version", ""),
        "updated_at": metadata.get("updated_at", ""),
        "source_site": metadata.get("source_site", ""),
        "topic": semantic.get("topic", ""),
        "semantic_intent": semantic.get("intent", ""),
        "semantic_audience": semantic.get("audience", ""),
        "keywords": semantic.get("keywords", []),
        "semantic_status": semantic.get("status", ""),
        "source_file": module.get("source_file"),
    }


def _load_critical_module_ids(report_path: Path) -> set[str]:
    if not report_path.exists():
        return set()
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (RuntimeError, ValueError, TypeError, OSError):
        return set()
    if not isinstance(payload, dict):
        return set()
    raw_ids = payload.get("critical_module_ids", [])
    if not isinstance(raw_ids, list):
        return set()
    return {str(item).strip() for item in raw_ids if str(item).strip()}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate knowledge retrieval index")
    parser.add_argument("--modules-dir", default="knowledge_modules")
    parser.add_argument("--output", default="docs/assets/knowledge-retrieval-index.json")
    parser.add_argument("--contradictions-report", default="")
    parser.add_argument("--exclude-critical-contradictions", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    modules = _load_modules(Path(args.modules_dir))
    blocked_ids: set[str] = set()
    if args.exclude_critical_contradictions and str(args.contradictions_report).strip():
        blocked_ids = _load_critical_module_ids(Path(args.contradictions_report))

    active_modules = [module for module in modules if module.get("status") == "active"]
    if blocked_ids:
        active_modules = [module for module in active_modules if str(module.get("id", "")).strip() not in blocked_ids]
    index = [_module_to_index_record(module) for module in active_modules]

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print(f"Generated retrieval index with {len(index)} records: {output_path}")
    if blocked_ids:
        print(f"Excluded {len(blocked_ids)} critical modules from index based on contradictions report.")


if __name__ == "__main__":
    main()

"""Knowledge retrieval helpers for Ask AI runtime."""

from __future__ import annotations

import glob
import json
from pathlib import Path
from typing import Any


def load_knowledge_index(path: str) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    payload = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    return []


def load_assistant_bundles(glob_pattern: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for file_path in sorted(glob.glob(glob_pattern)):
        p = Path(file_path)
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            items.append(payload)
    return items


def rank_modules(question: str, modules: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    q = question.lower()

    def score(module: dict[str, Any]) -> int:
        tokens = [
            str(module.get("title", "")).lower(),
            str(module.get("summary", "")).lower(),
            str(module.get("assistant_excerpt", "")).lower(),
            " ".join(str(v).lower() for v in module.get("intents", [])),
            " ".join(str(v).lower() for v in module.get("channels", [])),
        ]
        text = " ".join(tokens)
        return sum(1 for part in q.split() if part and part in text)

    ranked = sorted(modules, key=lambda m: (score(m), int(m.get("priority", 0))), reverse=True)
    return ranked[: max(limit, 1)]


def build_context(question: str, modules: list[dict[str, Any]], max_context_modules: int) -> dict[str, Any]:
    top = rank_modules(question, modules, max_context_modules)
    return {
        "question": question,
        "modules": [
            {
                "id": m.get("id"),
                "title": m.get("title"),
                "summary": m.get("summary"),
                "assistant_excerpt": m.get("assistant_excerpt"),
                "source_file": m.get("source_file"),
            }
            for m in top
        ],
    }

#!/usr/bin/env python3
"""Generate llms.txt, llms-full.txt, and an llms-ctx.json manifest from modules.

These files help LLMs and AI search consume the documentation:

- ``llms.txt``      -- a lean index: one line per topic (title, link, summary),
                       grouped by intent. Small by design.
- ``llms-full.txt`` -- full documentation content for modules flagged for the
                       ``assistant`` channel, deduplicated (each module once),
                       badge markers stripped, and token-budgeted: content that
                       exceeds the per-part cap spills into ``llms-full.partN.txt``
                       so no single file overloads a model's context window.
- ``llms-ctx.json`` -- a manifest listing every section with its token estimate
                       and part, so an agent can fetch sections selectively
                       instead of loading everything.

Because the docs assemble from SSOT modules, generating from modules (not from
rendered pages) means each unit of content appears exactly once -- no duplication.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# Canonical intent order for grouping the index.
_INTENT_ORDER = [
    "install", "configure", "troubleshoot", "optimize",
    "secure", "migrate", "automate", "compare", "integrate",
]

_BADGE_RE = re.compile(
    r"<!--\s*VERIDOC_POWERED_BADGE:START\s*-->.*?<!--\s*VERIDOC_POWERED_BADGE:END\s*-->",
    re.DOTALL | re.IGNORECASE,
)


def load_modules(modules_dir: Path) -> list[dict[str, Any]]:
    modules: list[dict[str, Any]] = []
    for path in sorted(modules_dir.glob("*.yml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and str(payload.get("status")) == "active":
            modules.append(payload)
    return modules


def load_variables(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def strip_badges(text: str) -> str:
    """Remove VeriDoc badge blocks and collapse the resulting blank lines."""
    cleaned = _BADGE_RE.sub("", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def estimate_tokens(text: str, chars_per_token: int = 4) -> int:
    return math.ceil(len(text) / max(chars_per_token, 1))


def _module_url(module: dict[str, Any]) -> str:
    meta = module.get("metadata", {}) if isinstance(module.get("metadata"), dict) else {}
    url = str(meta.get("url", "")).strip()
    if url:
        return url
    source = str(meta.get("source_path", "")).strip()
    return f"/{source}" if source else ""


_PART_SUFFIX_RE = re.compile(r"\s*\(Part\s+\d+\)\s*$", re.IGNORECASE)


def _clean_title(title: str) -> str:
    """Drop the auto-chunk '(Part N)' suffix for a clean index entry."""
    return _PART_SUFFIX_RE.sub("", title).strip()


def _primary_intent(module: dict[str, Any]) -> str:
    intents = module.get("intents", [])
    if isinstance(intents, list):
        for intent in _INTENT_ORDER:
            if intent in intents:
                return intent
        if intents:
            return str(intents[0])
    return "integrate"


def build_llms_txt(
    modules: list[dict[str, Any]],
    *,
    product_name: str,
    tagline: str,
    min_priority: int,
) -> str:
    """Build the lean index grouped by intent."""
    groups: dict[str, list[dict[str, Any]]] = {}
    seen: set[str] = set()
    for module in modules:
        channels = module.get("channels", [])
        if isinstance(channels, list) and "docs" not in channels:
            continue
        if int(module.get("priority", 0)) < min_priority:
            continue
        # Collapse auto-chunks of one source doc: index the page once, by URL.
        dedup_key = _module_url(module) or str(module.get("id", ""))
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        groups.setdefault(_primary_intent(module), []).append(module)

    lines = [f"# {product_name}", ""]
    if tagline:
        lines += [f"> {tagline}", ""]

    ordered_intents = _INTENT_ORDER + sorted(set(groups) - set(_INTENT_ORDER))
    for intent in ordered_intents:
        items = groups.get(intent)
        if not items:
            continue
        items.sort(key=lambda m: (-int(m.get("priority", 0)), str(m.get("title", ""))))
        lines.append(f"## {intent.capitalize()}")
        for module in items:
            title = _clean_title(str(module.get("title", "")).strip())
            summary = str(module.get("summary", "")).strip()
            url = _module_url(module)
            link = f"[{title}]({url})" if url else title
            lines.append(f"- {link}: {summary}" if summary else f"- {link}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_llms_full(
    modules: list[dict[str, Any]],
    *,
    product_name: str,
    assistant_only: bool,
    max_tokens_per_part: int,
    chars_per_token: int,
) -> tuple[list[str], list[dict[str, Any]]]:
    """Build token-budgeted full-content parts and a manifest of sections."""
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for module in modules:
        module_id = str(module.get("id", ""))
        if module_id in seen:
            continue
        channels = module.get("channels", [])
        if assistant_only and isinstance(channels, list) and "assistant" not in channels:
            continue
        seen.add(module_id)
        selected.append(module)
    selected.sort(key=lambda m: (-int(m.get("priority", 0)), str(m.get("id", ""))))

    parts: list[list[str]] = [[]]
    manifest: list[dict[str, Any]] = []
    part_tokens = 0
    header = (
        f"# {product_name} -- full documentation for LLMs\n\n"
        f"> Machine-readable full text, assembled from knowledge modules. "
        f"Sections are token-budgeted across parts; see llms-ctx.json to fetch selectively.\n"
    )
    parts[0].append(header)
    part_tokens = estimate_tokens(header, chars_per_token)

    for module in selected:
        content = module.get("content", {})
        body = strip_badges(str(content.get("docs_markdown", ""))) if isinstance(content, dict) else ""
        if not body:
            continue
        title = str(module.get("title", "")).strip()
        url = _module_url(module)
        section = f"## {title}\n\n"
        if url:
            section += f"Source: {url}\n\n"
        section += body + "\n"
        section_tokens = estimate_tokens(section, chars_per_token)

        # Start a new part if this section would overflow the current one
        # (but never split a single section across parts).
        if part_tokens + section_tokens > max_tokens_per_part and parts[-1]:
            parts.append([])
            part_tokens = 0
        parts[-1].append(section)
        part_tokens += section_tokens

        manifest.append(
            {
                "id": str(module.get("id", "")),
                "title": title,
                "url": url,
                "tokens": section_tokens,
                "intents": module.get("intents", []),
                "part": len(parts),
            }
        )

    rendered_parts = ["\n".join(chunk).rstrip() + "\n" for chunk in parts]
    return rendered_parts, manifest


def _part_filename(index: int) -> str:
    return "llms-full.txt" if index == 0 else f"llms-full.part{index + 1}.txt"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--modules-dir", default="knowledge_modules")
    parser.add_argument("--variables", default="docs/_variables.yml")
    parser.add_argument("--output-dir", default="docs", help="Where llms.txt files are written (served at site root)")
    parser.add_argument("--min-priority", type=int, default=30, help="Min module priority for the llms.txt index")
    parser.add_argument("--max-tokens-per-part", type=int, default=60000, help="Token cap per llms-full part")
    parser.add_argument("--chars-per-token", type=int, default=4, help="Token estimate heuristic (chars/token)")
    parser.add_argument("--all-channels", action="store_true", help="Include all channels in llms-full (default: assistant only)")
    args = parser.parse_args()

    modules_dir = Path(args.modules_dir)
    modules = load_modules(modules_dir)
    if not modules:
        print(f"[warn] no active modules in {modules_dir}")
        return 0

    variables = load_variables(Path(args.variables))
    product_name = str(variables.get("product_name", "Documentation")).strip() or "Documentation"
    tagline = str(variables.get("product_tagline", "")).strip()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    index = build_llms_txt(modules, product_name=product_name, tagline=tagline, min_priority=int(args.min_priority))
    (out_dir / "llms.txt").write_text(index, encoding="utf-8")

    parts, manifest = build_llms_full(
        modules,
        product_name=product_name,
        assistant_only=not bool(args.all_channels),
        max_tokens_per_part=int(args.max_tokens_per_part),
        chars_per_token=int(args.chars_per_token),
    )
    for i, part in enumerate(parts):
        (out_dir / _part_filename(i)).write_text(part, encoding="utf-8")

    ctx = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "product": product_name,
        "parts": [
            {"file": _part_filename(i), "tokens": estimate_tokens(part, int(args.chars_per_token))}
            for i, part in enumerate(parts)
        ],
        "total_sections": len(manifest),
        "total_tokens": sum(e["tokens"] for e in manifest),
        "sections": manifest,
    }
    (out_dir / "llms-ctx.json").write_text(json.dumps(ctx, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    print(
        f"[ok] llms.txt ({len(index.splitlines())} lines), "
        f"llms-full in {len(parts)} part(s), {len(manifest)} sections, "
        f"~{ctx['total_tokens']} tokens -> {out_dir}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

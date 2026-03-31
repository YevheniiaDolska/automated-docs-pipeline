#!/usr/bin/env python3
"""Assemble intent-specific experiences from reusable knowledge modules."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _load_modules(modules_dir: Path) -> list[dict[str, Any]]:
    modules: list[dict[str, Any]] = []
    for path in sorted(modules_dir.glob("*.yml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload["_path"] = str(path)
            modules.append(payload)
    return modules


def _match_module(module: dict[str, Any], intent: str, audience: str, channel: str) -> bool:
    intents = module.get("intents", [])
    audiences = module.get("audiences", [])
    channels = module.get("channels", [])
    status = module.get("status")

    return (
        status == "active"
        and intent in intents
        and channel in channels
        and (audience in audiences or "all" in audiences)
    )


def _sort_modules(modules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for module in modules:
        module_id = str(module.get("id", "")).strip()
        if module_id:
            by_id[module_id] = module

    def _sort_key(module_id: str) -> str:
        return module_id

    indegree: dict[str, int] = {module_id: 0 for module_id in by_id}
    graph: dict[str, list[str]] = defaultdict(list)

    for module_id, module in by_id.items():
        deps = module.get("dependencies", [])
        if not isinstance(deps, list):
            continue
        for dep in deps:
            dep_id = str(dep).strip()
            if dep_id in by_id:
                graph[dep_id].append(module_id)
                indegree[module_id] += 1

    ready = sorted([module_id for module_id, deg in indegree.items() if deg == 0], key=_sort_key)
    ordered_ids: list[str] = []
    while ready:
        current = ready.pop(0)
        ordered_ids.append(current)
        for neighbor in sorted(graph.get(current, []), key=_sort_key):
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                ready.append(neighbor)
        ready.sort(key=_sort_key)

    if len(ordered_ids) != len(by_id):
        unresolved = sorted([module_id for module_id, deg in indegree.items() if deg > 0])
        raise ValueError(
            "Dependency cycle detected in matched modules: " + ", ".join(unresolved)
        )

    return [by_id[module_id] for module_id in ordered_ids]


def _build_docs_page(intent: str, audience: str, matched: list[dict[str, Any]]) -> str:
    title = f"Intent experience: {intent} for {audience}"
    description = (
        "Assembled guidance for one intent and audience using reusable "
        "knowledge modules with verified metadata and channel-ready sections."
    )

    lines: list[str] = [
        "---",
        f'title: "{title}"',
        f'description: "{description}"',
        "content_type: reference",
        "product: both",
        "tags:",
        "  - Reference",
        "  - AI",
        "---",
        "",
        "<!-- markdownlint-disable MD001 MD007 MD024 MD025 MD031 -->",
        "",
        f"# {title}",
        "",
        (
            f"This page is assembled for the `{intent}` intent and the `{audience}` "
            "audience using reusable modules."
        ),
        "",
        "```bash",
        "python3 scripts/assemble_intent_experience.py \\",
        f"  --intent {intent} --audience {audience} --channel docs",
        "```",
        "",
        "## Included modules",
        "",
    ]

    for module in matched:
        module_title = str(module.get("title", module.get("id", "module"))).strip() or "module"
        lines.append(f"### {module_title}")
        lines.append("")
        summary = str(module.get("summary", "")).strip()
        if summary:
            lines.append(summary)
            lines.append("")
        docs_chunk = str(module.get("content", {}).get("docs_markdown", "")).strip()
        if docs_chunk:
            lines.append(_sanitize_docs_chunk(docs_chunk, module_title))
            lines.append("")

    lines.extend(
        [
            "## Next steps",
            "",
            "- Validate modules: `npm run lint:knowledge`",
            "- Rebuild retrieval index: `npm run build:knowledge-index`",
            "- Generate assistant pack: `npm run build:intent -- --channel assistant`",
            "",
        ]
    )
    return "\n".join(lines)


def _sanitize_docs_chunk(chunk: str, module_title: str) -> str:
    """Normalize inserted markdown chunks for aggregated docs pages.

    Rules:
    - Keep one H1 at page level only by demoting chunk headings.
    - Prefix chunk headings with module title to avoid duplicate-heading lint errors.
    - Normalize common list indentation to 2 spaces.
    - Add blank line around fenced code blocks.
    """
    out: list[str] = []
    in_fence = False
    prev_blank = True

    for raw in chunk.splitlines():
        line = raw.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            if not prev_blank:
                out.append("")
            out.append(stripped)
            in_fence = not in_fence
            prev_blank = False
            continue

        if in_fence:
            out.append(line)
            prev_blank = (line == "")
            continue

        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            level = min(len(heading.group(1)) + 2, 6)
            text = heading.group(2).strip()
            out.append(f"{'#' * level} {module_title}: {text}")
            prev_blank = False
            continue

        if re.match(r"^ {4}[-*]\s+", line):
            line = "  " + line.lstrip()
        elif re.match(r"^ {4}\d+\.\s+", line):
            line = "  " + line.lstrip()

        out.append(line)
        prev_blank = (line == "")

    normalized: list[str] = []
    for i, line in enumerate(out):
        normalized.append(line)
        if line.strip().startswith("```"):
            next_line = out[i + 1] if i + 1 < len(out) else ""
            if next_line and next_line.strip():
                normalized.append("")
    return "\n".join(normalized).strip()


def _build_channel_bundle(intent: str, audience: str, channel: str, matched: list[dict[str, Any]]) -> dict[str, Any]:
    bundle_items: list[dict[str, Any]] = []

    channel_field = {
        "assistant": "assistant_context",
        "automation": "automation_workflow",
        "in-product": "in_product_guidance",
        "field": "field_enablement",
        "sales": "sales_partner_enablement",
        "docs": "docs_markdown",
    }[channel]

    for module in matched:
        content = module.get("content", {})
        text = str(content.get(channel_field, "")).strip()
        if not text:
            continue
        bundle_items.append(
            {
                "module_id": module.get("id"),
                "title": module.get("title"),
                "priority": module.get("priority"),
                "intent": intent,
                "audience": audience,
                "channel": channel,
                "content": text,
            }
        )

    return {
        "intent": intent,
        "audience": audience,
        "channel": channel,
        "module_count": len(bundle_items),
        "modules": bundle_items,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assemble intent experiences from knowledge modules")
    parser.add_argument("--modules-dir", default="knowledge_modules")
    parser.add_argument("--intent", required=True)
    parser.add_argument("--audience", required=True)
    parser.add_argument("--channel", required=True, choices=["docs", "assistant", "automation", "in-product", "field", "sales"])
    parser.add_argument("--docs-output-dir", default="docs/reference/intent-experiences")
    parser.add_argument("--bundle-output-dir", default="reports/intent-bundles")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    modules = _load_modules(Path(args.modules_dir))

    matched = _sort_modules(
        [m for m in modules if _match_module(m, args.intent, args.audience, args.channel)]
    )

    if args.channel == "docs":
        docs_output_dir = Path(args.docs_output_dir)
        docs_output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{_slugify(args.intent)}-{_slugify(args.audience)}.md"
        output_path = docs_output_dir / filename
        output_path.write_text(_build_docs_page(args.intent, args.audience, matched), encoding="utf-8")
        print(f"Generated docs experience: {output_path}")

    bundle_output_dir = Path(args.bundle_output_dir)
    bundle_output_dir.mkdir(parents=True, exist_ok=True)
    bundle_filename = f"{_slugify(args.intent)}-{_slugify(args.audience)}-{_slugify(args.channel)}.json"
    bundle_path = bundle_output_dir / bundle_filename
    bundle = _build_channel_bundle(args.intent, args.audience, args.channel, matched)
    bundle_path.write_text(json.dumps(bundle, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"Generated channel bundle: {bundle_path}")


if __name__ == "__main__":
    main()

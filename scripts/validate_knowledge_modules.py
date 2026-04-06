#!/usr/bin/env python3
"""Validate knowledge modules for intent-driven docs orchestration."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ALLOWED_INTENTS = {
    "install",
    "configure",
    "troubleshoot",
    "optimize",
    "secure",
    "migrate",
    "automate",
    "compare",
    "integrate",
}

ALLOWED_AUDIENCES = {
    "beginner",
    "practitioner",
    "operator",
    "developer",
    "architect",
    "sales",
    "support",
    "all",
}

ALLOWED_CHANNELS = {
    "docs",
    "in-product",
    "assistant",
    "automation",
    "field",
    "sales",
}

ALLOWED_SEMANTIC_STATUS = {"rule_based", "llm_enriched"}
ISO_DATE_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}"
    r"[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})$"
)


@dataclass
class ModuleIssue:
    module_path: str
    message: str


def _load_yaml(path: Path) -> dict[str, Any] | None:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return None
    return payload if isinstance(payload, dict) else None


def _validate_set_field(module: dict[str, Any], field: str, allowed: set[str], issues: list[ModuleIssue], module_path: Path) -> None:
    value = module.get(field)
    if not isinstance(value, list) or not value:
        issues.append(ModuleIssue(str(module_path), f"'{field}' must be a non-empty list"))
        return
    for item in value:
        if not isinstance(item, str):
            issues.append(ModuleIssue(str(module_path), f"'{field}' contains non-string value"))
            continue
        if item not in allowed:
            issues.append(ModuleIssue(str(module_path), f"'{field}' contains unsupported value '{item}'"))


def _dfs_cycle(node: str, graph: dict[str, list[str]], visited: set[str], stack: set[str], cycles: list[list[str]]) -> None:
    visited.add(node)
    stack.add(node)

    for neighbor in graph.get(node, []):
        if neighbor not in visited:
            _dfs_cycle(neighbor, graph, visited, stack, cycles)
        elif neighbor in stack:
            cycles.append([node, neighbor])

    stack.remove(node)


def validate_modules(modules_dir: Path) -> tuple[list[dict[str, Any]], list[ModuleIssue]]:
    issues: list[ModuleIssue] = []
    modules: list[dict[str, Any]] = []
    by_id: dict[str, Path] = {}

    for path in sorted(modules_dir.glob("*.yml")):
        module = _load_yaml(path)
        if module is None:
            issues.append(ModuleIssue(str(path), "invalid YAML structure"))
            continue

        module_id = module.get("id")
        if not isinstance(module_id, str) or not module_id:
            issues.append(ModuleIssue(str(path), "missing 'id'"))
            continue

        if module_id in by_id:
            issues.append(
                ModuleIssue(
                    str(path),
                    f"duplicate module id '{module_id}' already defined in {by_id[module_id]}",
                )
            )
            continue

        by_id[module_id] = path

        if not isinstance(module.get("title"), str) or len(module["title"]) < 10:
            issues.append(ModuleIssue(str(path), "'title' must be at least 10 characters"))

        if not isinstance(module.get("summary"), str) or len(module["summary"]) < 30:
            issues.append(ModuleIssue(str(path), "'summary' must be at least 30 characters"))

        _validate_set_field(module, "intents", ALLOWED_INTENTS, issues, path)
        _validate_set_field(module, "audiences", ALLOWED_AUDIENCES, issues, path)
        _validate_set_field(module, "channels", ALLOWED_CHANNELS, issues, path)

        priority = module.get("priority")
        if not isinstance(priority, int) or priority < 1 or priority > 100:
            issues.append(ModuleIssue(str(path), "'priority' must be an integer between 1 and 100"))

        status = module.get("status")
        if status not in {"active", "deprecated"}:
            issues.append(ModuleIssue(str(path), "'status' must be 'active' or 'deprecated'"))

        content = module.get("content")
        if not isinstance(content, dict):
            issues.append(ModuleIssue(str(path), "'content' must be an object"))
        else:
            docs_markdown = content.get("docs_markdown")
            assistant_context = content.get("assistant_context")
            if not isinstance(docs_markdown, str) or len(docs_markdown.strip()) < 80:
                issues.append(ModuleIssue(str(path), "'content.docs_markdown' must be at least 80 characters"))
            if not isinstance(assistant_context, str) or len(assistant_context.strip()) < 60:
                issues.append(ModuleIssue(str(path), "'content.assistant_context' must be at least 60 characters"))

        metadata = module.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            issues.append(ModuleIssue(str(path), "'metadata' must be an object when present"))
        elif isinstance(metadata, dict):
            for key in ("url", "title", "heading", "version", "updated_at", "source_site"):
                value = str(metadata.get(key, "")).strip()
                if not value:
                    issues.append(ModuleIssue(str(path), f"'metadata.{key}' is required"))
            url = str(metadata.get("url", "")).strip().lower()
            if url and not (url.startswith("http://") or url.startswith("https://")):
                issues.append(ModuleIssue(str(path), "'metadata.url' must be absolute http(s) URL"))
            updated_at = str(metadata.get("updated_at", "")).strip()
            if updated_at and not ISO_DATE_PATTERN.match(updated_at):
                issues.append(ModuleIssue(str(path), "'metadata.updated_at' must be ISO datetime with timezone"))

        semantic = module.get("semantic")
        if semantic is not None:
            if not isinstance(semantic, dict):
                issues.append(ModuleIssue(str(path), "'semantic' must be an object when present"))
            else:
                topic = str(semantic.get("topic", "")).strip()
                if len(topic) < 3:
                    issues.append(ModuleIssue(str(path), "'semantic.topic' must be at least 3 characters"))
                intent = str(semantic.get("intent", "")).strip()
                if intent and intent not in ALLOWED_INTENTS:
                    issues.append(ModuleIssue(str(path), f"'semantic.intent' has unsupported value '{intent}'"))
                audience = str(semantic.get("audience", "")).strip()
                if audience and audience not in ALLOWED_AUDIENCES:
                    issues.append(ModuleIssue(str(path), f"'semantic.audience' has unsupported value '{audience}'"))
                keywords = semantic.get("keywords", [])
                if not isinstance(keywords, list):
                    issues.append(ModuleIssue(str(path), "'semantic.keywords' must be a list"))
                else:
                    for kw in keywords:
                        if not isinstance(kw, str) or not kw.strip():
                            issues.append(ModuleIssue(str(path), "'semantic.keywords' must contain non-empty strings"))
                            break
                status = str(semantic.get("status", "")).strip()
                if status and status not in ALLOWED_SEMANTIC_STATUS:
                    issues.append(
                        ModuleIssue(
                            str(path),
                            f"'semantic.status' must be one of {sorted(ALLOWED_SEMANTIC_STATUS)}",
                        )
                    )

        module["_path"] = str(path)
        modules.append(module)

    module_ids = {m["id"] for m in modules if isinstance(m.get("id"), str)}
    graph: dict[str, list[str]] = defaultdict(list)

    for module in modules:
        deps = module.get("dependencies", [])
        if not isinstance(deps, list):
            issues.append(ModuleIssue(module["_path"], "'dependencies' must be a list if present"))
            continue
        for dep in deps:
            if not isinstance(dep, str):
                issues.append(ModuleIssue(module["_path"], "'dependencies' must contain strings only"))
                continue
            if dep not in module_ids:
                issues.append(ModuleIssue(module["_path"], f"unknown dependency '{dep}'"))
                continue
            graph[module["id"]].append(dep)

    visited: set[str] = set()
    stack: set[str] = set()
    cycles: list[list[str]] = []

    for module_id in module_ids:
        if module_id not in visited:
            _dfs_cycle(module_id, graph, visited, stack, cycles)

    for cycle in cycles:
        issues.append(ModuleIssue("knowledge_modules", f"dependency cycle detected: {cycle[0]} -> {cycle[1]}"))

    return modules, issues


def _build_report(modules: list[dict[str, Any]], issues: list[ModuleIssue]) -> dict[str, Any]:
    by_intent: dict[str, int] = defaultdict(int)
    by_channel: dict[str, int] = defaultdict(int)

    for module in modules:
        for intent in module.get("intents", []):
            by_intent[str(intent)] += 1
        for channel in module.get("channels", []):
            by_channel[str(channel)] += 1

    return {
        "summary": {
            "module_count": len(modules),
            "issue_count": len(issues),
            "valid": len(issues) == 0,
        },
        "coverage": {
            "intents": dict(sorted(by_intent.items())),
            "channels": dict(sorted(by_channel.items())),
        },
        "issues": [{"module_path": i.module_path, "message": i.message} for i in issues],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate knowledge modules")
    parser.add_argument("--modules-dir", default="knowledge_modules", help="Path to module YAML files")
    parser.add_argument("--report", default="reports/knowledge_modules_report.json", help="Path to JSON report")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    modules_dir = Path(args.modules_dir)

    if not modules_dir.exists():
        print(f"knowledge module directory not found: {modules_dir}", file=sys.stderr)
        sys.exit(1)

    modules, issues = validate_modules(modules_dir)
    report = _build_report(modules, issues)

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    if issues:
        print(f"Knowledge modules: {len(issues)} issue(s)", file=sys.stderr)
        for issue in issues:
            print(f"  {issue.module_path}: {issue.message}", file=sys.stderr)
        sys.exit(1)

    print(f"Knowledge modules: {len(modules)} modules pass")


if __name__ == "__main__":
    main()

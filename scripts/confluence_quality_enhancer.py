#!/usr/bin/env python3
"""Enhance migrated Confluence docs to pipeline quality standards.

Applies idempotent structural and stylistic fixes to Markdown documents
imported from Confluence, ensuring they pass all linters, SEO/GEO checks,
and are ready for RAG extraction.  Content meaning is preserved; only
structure, metadata, and formatting are improved.

Optionally uses an LLM to restructure information architecture for
progressive disclosure and optimal heading hierarchy.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GENERIC_HEADINGS = {
    "overview",
    "introduction",
    "configuration",
    "setup",
    "details",
    "information",
    "general",
    "notes",
    "summary",
}

DEFINITION_PATTERNS = [
    re.compile(p)
    for p in [
        r"\bis\b",
        r"\benables?\b",
        r"\bprovides?\b",
        r"\ballows?\b",
        r"\bcreates?\b",
        r"\bprocesses?\b",
        r"\bexecutes?\b",
    ]
]

CONTENT_TYPE_KEYWORDS: dict[str, list[str]] = {
    "troubleshooting": [
        "troubleshoot",
        "error",
        "fail",
        "issue",
        "debug",
        "problem",
        "fix",
        "resolve",
        "workaround",
    ],
    "reference": [
        "api",
        "endpoint",
        "reference",
        "parameter",
        "schema",
        "specification",
        "field",
        "property",
        "method",
    ],
    "how-to": [
        "how to",
        "setup",
        "configure",
        "install",
        "deploy",
        "migrate",
        "upgrade",
        "integrate",
        "connect",
    ],
    "tutorial": [
        "tutorial",
        "getting started",
        "quick start",
        "walkthrough",
        "step by step",
        "learn",
        "beginner",
    ],
    "concept": [
        "concept",
        "architecture",
        "overview",
        "understand",
        "explain",
        "design",
        "theory",
        "model",
    ],
}

LANG_HEURISTICS: list[tuple[str, re.Pattern[str]]] = [
    ("python", re.compile(r"(^import |^from |^def |^class |print\(|if __name__)", re.M)),
    ("bash", re.compile(r"(^#!/bin/|^\$\s|^export |^echo |^curl |^npm |^pip |^apt )", re.M)),
    ("yaml", re.compile(r"(^\w+:\s|^---$|^\s+-\s)", re.M)),
    ("json", re.compile(r'^[\s]*[{\[]', re.M)),
    ("javascript", re.compile(r"(^const |^let |^var |^function |^import |=>|console\.log)", re.M)),
    ("xml", re.compile(r"(^<\?xml|<\w+[^>]*>.*</\w+>)", re.M)),
    ("sql", re.compile(r"(^SELECT |^INSERT |^UPDATE |^DELETE |^CREATE TABLE|^ALTER )", re.M | re.I)),
]

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.M)
FENCED_CODE_RE = re.compile(r"^```(\w*)\s*$", re.M)
ORDERED_LIST_RE = re.compile(r"^(\s*)\d+\.\s+")
BARE_URL_RE = re.compile(r"(?<!\()(?<!\[)(https?://[^\s)\]>]+)")

CONTENT_TYPE_TAG_MAP: dict[str, str] = {
    "tutorial": "Tutorial",
    "how-to": "How-To",
    "concept": "Concept",
    "reference": "Reference",
    "troubleshooting": "Troubleshooting",
}

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class EnhancementResult:
    """Result of enhancing a single file."""

    file_path: str
    changes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    success: bool = True
    llm_enhanced: bool = False


# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------


def _load_variables(repo_root: Path) -> dict[str, str]:
    """Build a map of literal values to {{ variable }} placeholders."""
    variables_path = repo_root / "docs" / "_variables.yml"
    if not variables_path.exists():
        return {}
    with open(variables_path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    var_map: dict[str, str] = {}
    for key, value in data.items():
        if isinstance(value, str) and len(value) >= 4:
            var_map[value] = "{{ " + key + " }}"
        elif isinstance(value, (int, float)):
            var_map[str(value)] = "{{ " + key + " }}"
        elif isinstance(value, dict):
            for sub_key, sub_val in value.items():
                if isinstance(sub_val, str) and len(sub_val) >= 4:
                    var_map[sub_val] = "{{ " + f"{key}.{sub_key}" + " }}"
    return var_map


def _load_allowed_tags(repo_root: Path) -> list[str]:
    """Extract allowed tags from mkdocs.yml."""
    mkdocs_path = repo_root / "mkdocs.yml"
    if not mkdocs_path.exists():
        return list(CONTENT_TYPE_TAG_MAP.values())
    with open(mkdocs_path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    extra = data.get("extra", {})
    tags_section = extra.get("tags", {})
    if isinstance(tags_section, dict):
        return list(tags_section.keys())
    return list(CONTENT_TYPE_TAG_MAP.values())


# ---------------------------------------------------------------------------
# Frontmatter helpers
# ---------------------------------------------------------------------------


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split YAML frontmatter from body text."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    try:
        fm = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}, text
    body = text[match.end():]
    return fm, body


def _serialize_frontmatter(fm: dict[str, Any]) -> str:
    """Serialize frontmatter dict to YAML block."""
    lines = ["---"]
    for key, value in fm.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, str):
            if '"' in value or ":" in value or value.startswith("{"):
                escaped = value.replace('"', "'")
                lines.append(f'{key}: "{escaped}"')
            else:
                lines.append(f'{key}: "{value}"')
        elif value is None:
            continue
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _improve_content_type(title: str, body: str, current: str) -> str:
    """Improve content_type detection with enhanced keyword matching."""
    combined = (title + " " + body[:2000]).lower()
    scores: dict[str, int] = {}
    for ctype, keywords in CONTENT_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            scores[ctype] = score

    if not scores:
        return current if current else "how-to"

    best = max(scores, key=lambda k: scores[k])
    if current and current in scores and scores[current] >= scores[best] - 1:
        return current
    return best


def _fix_title(title: str) -> str:
    """Ensure title is under 70 characters, stripped of trailing punctuation."""
    title = title.strip()
    title = title.rstrip(".")
    if len(title) <= 70:
        return title
    truncated = title[:67]
    last_space = truncated.rfind(" ")
    if last_space > 30:
        truncated = truncated[:last_space]
    return truncated.rstrip(" .,;:-")


def _fix_description(desc: str, title: str, body: str) -> str:
    """Ensure description is 50-160 characters."""
    if not desc:
        clean_body = " ".join(body.replace("\n", " ").split())
        clean_body = re.sub(r"^#+\s+.*?\s+", "", clean_body)
        desc = clean_body[:160].rstrip()

    desc = desc.strip()

    if len(desc) < 50:
        suffix = f" This document covers {title.lower().rstrip('.')}."
        desc = (desc.rstrip(".") + suffix)[:160]

    if len(desc) < 50:
        desc = (desc + " Migrated from Confluence and enhanced for quality.")[:160]

    if len(desc) > 160:
        truncated = desc[:157]
        last_space = truncated.rfind(" ")
        if last_space > 80:
            truncated = truncated[:last_space]
        desc = truncated.rstrip(" .,;:-") + "..."

    return desc


def _fix_tags(
    tags: list[str] | None,
    content_type: str,
    allowed_tags: list[str],
) -> list[str]:
    """Filter tags to allowed set, add canonical content_type tag, cap at 8."""
    if tags is None:
        tags = []

    allowed_lower = {t.lower(): t for t in allowed_tags}
    fixed: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        tag_str = str(tag).strip()
        canonical = allowed_lower.get(tag_str.lower())
        if canonical and canonical.lower() not in seen:
            fixed.append(canonical)
            seen.add(canonical.lower())

    ct_tag = CONTENT_TYPE_TAG_MAP.get(content_type)
    if ct_tag and ct_tag.lower() not in seen:
        fixed.insert(0, ct_tag)
        seen.add(ct_tag.lower())

    return fixed[:8]


def _fix_frontmatter(
    fm: dict[str, Any],
    title: str,
    body: str,
    allowed_tags: list[str],
    changes: list[str],
) -> dict[str, Any]:
    """Orchestrate all frontmatter fixes."""
    old_ct = fm.get("content_type", "")
    new_ct = _improve_content_type(title, body, old_ct)
    if new_ct != old_ct:
        changes.append(f"content_type: '{old_ct}' -> '{new_ct}'")
    fm["content_type"] = new_ct

    old_title = fm.get("title", title)
    new_title = _fix_title(old_title)
    if new_title != old_title:
        changes.append(f"title truncated: {len(old_title)} -> {len(new_title)} chars")
    fm["title"] = new_title

    old_desc = fm.get("description", "")
    new_desc = _fix_description(old_desc, new_title, body)
    if new_desc != old_desc:
        changes.append("description adjusted to 50-160 chars")
    fm["description"] = new_desc

    old_tags = fm.get("tags", [])
    new_tags = _fix_tags(old_tags, new_ct, allowed_tags)
    if new_tags != old_tags:
        changes.append(f"tags fixed: {old_tags} -> {new_tags}")
    fm["tags"] = new_tags

    if not fm.get("product"):
        fm["product"] = "both"
        changes.append("added product: both")

    if not fm.get("last_reviewed"):
        fm["last_reviewed"] = date.today().isoformat()
        changes.append("added last_reviewed date")

    if not fm.get("language"):
        fm["language"] = "en"

    return fm


# ---------------------------------------------------------------------------
# Content fixes
# ---------------------------------------------------------------------------


def _fix_heading_hierarchy(lines: list[str], changes: list[str]) -> list[str]:
    """Fix skipped heading levels (e.g., H2 -> H4 becomes H2 -> H3)."""
    result: list[str] = []
    prev_level = 1
    fixed_count = 0

    for line in lines:
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match:
            hashes = match.group(1)
            text = match.group(2)
            level = len(hashes)
            if level > prev_level + 1:
                new_level = prev_level + 1
                line = "#" * new_level + " " + text
                fixed_count += 1
                level = new_level
            prev_level = level
        result.append(line)

    if fixed_count:
        changes.append(f"fixed {fixed_count} skipped heading levels")
    return result


def _fix_generic_headings(
    lines: list[str],
    content_type: str,
    changes: list[str],
) -> list[str]:
    """Replace generic headings with descriptive alternatives."""
    replacements: dict[str, dict[str, str]] = {
        "overview": {
            "tutorial": "What you will learn",
            "how-to": "Before you begin",
            "concept": "Key concepts",
            "reference": "Quick reference",
            "troubleshooting": "Symptoms and diagnosis",
        },
        "introduction": {
            "tutorial": "What you will build",
            "how-to": "About this task",
            "concept": "Background",
            "reference": "About this reference",
            "troubleshooting": "Problem description",
        },
        "configuration": {
            "default": "Configure the service",
        },
        "setup": {
            "default": "Set up your environment",
        },
        "details": {
            "default": "How it works",
        },
        "information": {
            "default": "Key information",
        },
        "general": {
            "default": "General guidelines",
        },
        "notes": {
            "default": "Important notes",
        },
        "summary": {
            "tutorial": "What you learned",
            "how-to": "Result",
            "concept": "Key takeaways",
            "reference": "Quick summary",
            "troubleshooting": "Resolution summary",
        },
    }

    result: list[str] = []
    fixed_count = 0
    for line in lines:
        match = re.match(r"^(#{2,6})\s+(.+)$", line)
        if match:
            hashes = match.group(1)
            text = match.group(2).strip()
            text_lower = text.lower().rstrip(":")
            if text_lower in GENERIC_HEADINGS and text_lower in replacements:
                options = replacements[text_lower]
                replacement = options.get(content_type, options.get("default", text))
                if replacement != text:
                    line = f"{hashes} {replacement}"
                    fixed_count += 1
        result.append(line)

    if fixed_count:
        changes.append(f"replaced {fixed_count} generic headings")
    return result


def _fix_first_paragraph(body: str, content_type: str, changes: list[str]) -> str:
    """Ensure first paragraph has a definition pattern and is under 60 words."""
    body_stripped = body.lstrip("\n")
    if not body_stripped:
        return body

    # Skip if body starts with heading -- find paragraph after first heading
    heading_match = re.match(r"^(#+\s+.+)\n+", body_stripped)
    if heading_match:
        heading = heading_match.group(0)
        rest = body_stripped[len(heading):]
    else:
        heading = ""
        rest = body_stripped

    if not rest.strip():
        return body

    # Extract first paragraph (text until double newline or next heading)
    para_match = re.match(r"(.+?)(?:\n\n|\n#|\Z)", rest, re.DOTALL)
    if not para_match:
        return body

    first_para = para_match.group(1).strip()
    after_para = rest[para_match.end(1):]

    # Check for definition pattern
    has_definition = any(p.search(first_para) for p in DEFINITION_PATTERNS)

    if not has_definition and first_para:
        ct_verb = {
            "tutorial": "guides you through",
            "how-to": "explains how to",
            "concept": "describes",
            "reference": "provides reference information for",
            "troubleshooting": "helps resolve issues with",
        }
        verb = ct_verb.get(content_type, "provides information about")
        # Extract topic from heading or title
        topic_match = re.match(r"^#+\s+(.+)$", heading.strip()) if heading else None
        topic = topic_match.group(1).strip().lower() if topic_match else "this topic"
        prefix = f"This document {verb} {topic}. "
        first_para = prefix + first_para
        changes.append("added definition pattern to first paragraph")

    # Enforce 60 word limit
    words = first_para.split()
    if len(words) > 60:
        first_para = " ".join(words[:58]) + "."
        changes.append("truncated first paragraph to 60 words")

    return heading + first_para + after_para


def _fix_code_blocks(lines: list[str], changes: list[str]) -> list[str]:
    """Add language tags to unlabeled fenced code blocks."""
    result: list[str] = []
    i = 0
    fixed_count = 0

    while i < len(lines):
        line = lines[i]
        fence_match = re.match(r"^```(\w*)(\s*)$", line)

        if fence_match and not fence_match.group(1):
            # Found unlabeled opening fence -- collect code block content
            code_lines: list[str] = []
            j = i + 1
            while j < len(lines) and not re.match(r"^```\s*$", lines[j]):
                code_lines.append(lines[j])
                j += 1

            # Detect language from content
            code_text = "\n".join(code_lines)
            detected = ""
            for lang, pattern in LANG_HEURISTICS:
                if pattern.search(code_text):
                    detected = lang
                    break

            if detected:
                result.append(f"```{detected}")
                fixed_count += 1
            else:
                result.append(line)

            # Add code lines and closing fence
            result.extend(code_lines)
            if j < len(lines):
                result.append(lines[j])
            i = j + 1
        else:
            result.append(line)
            i += 1

    if fixed_count:
        changes.append(f"detected language for {fixed_count} code blocks")
    return result


def _fix_blank_lines(lines: list[str], changes: list[str]) -> list[str]:
    """Ensure blank lines before/after headings, lists, code blocks, admonitions."""
    result: list[str] = []
    fixed_count = 0

    def needs_blank_before(line: str) -> bool:
        return bool(
            re.match(r"^#{1,6}\s+", line)
            or re.match(r"^```", line)
            or re.match(r"^!!!\s+", line)
            or re.match(r"^[-*]\s+", line)
            or ORDERED_LIST_RE.match(line)
        )

    def needs_blank_after(line: str) -> bool:
        return bool(re.match(r"^#{1,6}\s+", line))

    in_code_block = False
    for i, line in enumerate(lines):
        is_fence = bool(re.match(r"^```", line))

        if is_fence and in_code_block:
            # Closing fence
            in_code_block = False
            result.append(line)
            continue

        if in_code_block:
            result.append(line)
            continue

        # Add blank line before if needed
        if needs_blank_before(line) and result and result[-1].strip():
            result.append("")
            fixed_count += 1

        result.append(line)

        if is_fence:
            # Opening fence
            in_code_block = True

        # Add blank line after heading
        if needs_blank_after(line) and i + 1 < len(lines) and lines[i + 1].strip():
            result.append("")
            fixed_count += 1

    if fixed_count:
        changes.append(f"added {fixed_count} blank lines for formatting")
    return result


def _fix_ordered_lists(lines: list[str], changes: list[str]) -> list[str]:
    """Normalize numbered lists to use 1. prefix."""
    result: list[str] = []
    fixed_count = 0
    in_code_block = False

    for line in lines:
        if re.match(r"^```", line):
            in_code_block = not in_code_block

        if in_code_block:
            result.append(line)
            continue

        match = ORDERED_LIST_RE.match(line)
        if match:
            indent = match.group(1)
            rest = line[match.end():]
            new_line = f"{indent}1. {rest}"
            if new_line != line:
                fixed_count += 1
            result.append(new_line)
        else:
            result.append(line)

    if fixed_count:
        changes.append(f"normalized {fixed_count} ordered list items to 1.")
    return result


def _replace_variables(
    lines: list[str],
    var_map: dict[str, str],
    changes: list[str],
) -> list[str]:
    """Replace hardcoded values with {{ variable }} placeholders.

    Skips content inside code blocks.
    """
    if not var_map:
        return lines

    result: list[str] = []
    in_code_block = False
    replaced_count = 0

    # Sort by length descending to avoid partial matches
    sorted_vars = sorted(var_map.items(), key=lambda x: -len(x[0]))

    for line in lines:
        if re.match(r"^```", line):
            in_code_block = not in_code_block
            result.append(line)
            continue

        if in_code_block or line.startswith("    "):
            result.append(line)
            continue

        original = line
        for literal, placeholder in sorted_vars:
            if literal in line and placeholder not in line:
                line = line.replace(literal, placeholder)

        if line != original:
            replaced_count += 1
        result.append(line)

    if replaced_count:
        changes.append(f"replaced hardcoded values with variables in {replaced_count} lines")
    return result


def _fix_bare_urls(lines: list[str], changes: list[str]) -> list[str]:
    """Wrap bare URLs in [url](url) markdown format."""
    result: list[str] = []
    fixed_count = 0
    in_code_block = False

    for line in lines:
        if re.match(r"^```", line):
            in_code_block = not in_code_block
            result.append(line)
            continue

        if in_code_block or line.startswith("    "):
            result.append(line)
            continue

        original = line
        # Only fix URLs not already in markdown links or images
        # Skip lines that have markdown link syntax around URLs
        if "](http" not in line and "![" not in line:
            line = BARE_URL_RE.sub(r"[\1](\1)", line)

        if line != original:
            fixed_count += 1
        result.append(line)

    if fixed_count:
        changes.append(f"wrapped {fixed_count} bare URLs in markdown links")
    return result


def _ensure_next_steps(lines: list[str], content_type: str, changes: list[str]) -> list[str]:
    """Add a 'Next steps' section if missing."""
    has_next_steps = any(
        re.match(r"^##\s+(?:next\s*steps|what.s?\s*next)\s*$", line, re.IGNORECASE)
        for line in lines
    )

    if has_next_steps or content_type == "release-note":
        return lines

    result = list(lines)
    # Strip trailing blank lines
    while result and not result[-1].strip():
        result.pop()

    result.extend([
        "",
        "## Next steps",
        "",
        "- Review and verify the migrated content for accuracy.",
        "- Update any broken internal links to point to correct pages.",
        "- Add additional context or examples where needed.",
        "",
    ])
    changes.append("added 'Next steps' section")
    return result


# ---------------------------------------------------------------------------
# LLM-powered code examples and missing sections
# ---------------------------------------------------------------------------

PLACEHOLDER_PATTERNS = [
    re.compile(r"\bfoo\b", re.I),
    re.compile(r"\bbar\b", re.I),
    re.compile(r"\bbaz\b", re.I),
    re.compile(r"\bexample\.com\b", re.I),
    re.compile(r"\btest123\b", re.I),
    re.compile(r"\bYOUR_API_KEY\b"),
    re.compile(r"\bmy-api-key\b", re.I),
    re.compile(r"\blorem\s+ipsum\b", re.I),
    re.compile(r"\bplaceholder\b", re.I),
]

ESSENTIAL_SECTIONS: dict[str, list[str]] = {
    "how-to": ["error handling", "next steps"],
    "tutorial": ["error handling", "next steps"],
    "reference": ["error codes", "rate limits", "authentication"],
    "concept": ["security considerations", "performance implications"],
}


def _get_llm_provider() -> Any | None:
    """Try to import and return an LLMProvider instance, or None."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages" / "core"))
        from gitspeak_core.docs.llm_executor import LLMProvider
        provider = LLMProvider()
        if provider.get_active_provider() == "none":
            return None
        return provider
    except (ImportError, ModuleNotFoundError):
        return None


def _fix_code_examples_with_llm(
    lines: list[str],
    content_type: str,
    changes: list[str],
    provider: Any | None,
) -> list[str]:
    """Replace placeholder code examples with realistic ones via LLM.

    Scans fenced code blocks for placeholder patterns (foo, bar, example.com,
    test123, YOUR_API_KEY used as literal value).  When placeholders are found
    and an LLM provider is available, asks the LLM to produce a realistic,
    runnable replacement while preserving the language tag and block count.
    """
    if provider is None:
        return lines

    # Identify code blocks with placeholders
    blocks: list[tuple[int, int, str, list[str]]] = []  # (start, end, lang, code_lines)
    i = 0
    while i < len(lines):
        fence = re.match(r"^```(\w*)\s*$", lines[i])
        if fence:
            lang = fence.group(1)
            start = i
            code: list[str] = []
            j = i + 1
            while j < len(lines) and not re.match(r"^```\s*$", lines[j]):
                code.append(lines[j])
                j += 1
            end = j  # closing fence
            code_text = "\n".join(code)
            has_placeholder = any(p.search(code_text) for p in PLACEHOLDER_PATTERNS)
            if has_placeholder and code:
                blocks.append((start, end, lang, code))
            i = j + 1
        else:
            i += 1

    if not blocks:
        return lines

    # Build prompt for all placeholder blocks at once
    block_texts = []
    for idx, (_, _, lang, code) in enumerate(blocks):
        block_texts.append(f"BLOCK {idx + 1} (language: {lang or 'unknown'}):\n" + "\n".join(code))

    prompt = (
        "Replace placeholder values (foo, bar, example.com, test123, YOUR_API_KEY, "
        "lorem ipsum, placeholder) in these code blocks with realistic, production-quality "
        "examples.  Preserve the language, structure, and number of code blocks.  "
        "Return ONLY the replacement code blocks separated by a line containing exactly "
        "'---BLOCK---'.  Do not wrap them in fences.\n\n"
        f"Content type: {content_type}\n\n" + "\n\n".join(block_texts)
    )

    try:
        response = provider.generate(
            prompt=prompt,
            system="You are a code example improver. Output only code, no commentary.",
            max_tokens=3000,
            temperature=0.3,
        )
        if response.error or not response.content.strip():
            return lines

        parts = response.content.strip().split("---BLOCK---")
        if len(parts) != len(blocks):
            changes.append(
                f"LLM code example fix skipped: expected {len(blocks)} blocks, got {len(parts)}"
            )
            return lines
    except (RuntimeError, ValueError, OSError) as exc:
        changes.append(f"LLM code example fix failed: {exc}")
        return lines

    # Rebuild lines with replacements applied in reverse order
    result = list(lines)
    for idx in reversed(range(len(blocks))):
        start, end, lang, _old = blocks[idx]
        new_code = parts[idx].strip().splitlines()
        replacement = [f"```{lang}"] + new_code + ["```"]
        result[start : end + 1] = replacement

    changes.append(f"LLM replaced placeholder code in {len(blocks)} blocks")
    return result


def _fix_missing_sections_with_llm(
    lines: list[str],
    content_type: str,
    title: str,
    changes: list[str],
    provider: Any | None,
) -> list[str]:
    """Add essential sections missing from the document via LLM.

    Based on *content_type*, checks whether commonly expected sections
    (error handling, security, performance, etc.) are present.  Missing
    sections are generated by the LLM with concrete, factual content and
    inserted before the "Next steps" section (or appended at the end).
    """
    if provider is None:
        return lines

    expected = ESSENTIAL_SECTIONS.get(content_type)
    if not expected:
        return lines

    body_lower = "\n".join(lines).lower()
    missing = [
        sec for sec in expected
        if not re.search(rf"^##\s+.*{re.escape(sec)}", body_lower, re.MULTILINE | re.IGNORECASE)
    ]

    if not missing:
        return lines

    prompt = (
        f"Document title: {title}\nContent type: {content_type}\n\n"
        f"The document is missing these sections: {', '.join(missing)}.\n\n"
        "Generate ONLY the missing sections as Markdown (H2 headings).  Each section "
        "must contain concrete, factual content (not filler).  Include realistic code "
        "examples or parameter tables where relevant.  Do not repeat existing content.  "
        "Output only the new sections, no commentary."
    )

    try:
        response = provider.generate(
            prompt=prompt,
            system="You are a senior technical writer. Output only Markdown sections.",
            max_tokens=2000,
            temperature=0.3,
        )
        if response.error or not response.content.strip():
            return lines

        new_sections = response.content.strip().splitlines()
    except (RuntimeError, ValueError, OSError) as exc:
        changes.append(f"LLM missing sections generation failed: {exc}")
        return lines

    # Insert before "Next steps" if present, else append
    insert_idx = len(lines)
    for idx, line in enumerate(lines):
        if re.match(r"^##\s+(?:next\s*steps|what.s?\s*next)\s*$", line, re.IGNORECASE):
            insert_idx = idx
            break

    # Ensure blank line separation
    result = list(lines)
    insertion = ["", ""] + new_sections + [""]
    result[insert_idx:insert_idx] = insertion

    changes.append(f"LLM added missing sections: {', '.join(missing)}")
    return result


def _fix_code_block_verification(lines: list[str], changes: list[str]) -> list[str]:
    """Execute Python code blocks and verify documented output comments.

    For each fenced python code block that contains an output comment
    (``# Output: <expected>``), execute the code via subprocess and compare.
    If the actual output differs, replace the documented output with the
    real value.  Blocks containing ``# do-not-execute``, network calls,
    or unavailable imports are skipped.
    """
    SKIP_PATTERNS = [
        re.compile(r"#\s*do-not-execute", re.I),
        re.compile(r"requests\.(get|post|put|delete|patch)\b"),
        re.compile(r"httpx\.(get|post|put|delete|patch|AsyncClient)\b"),
        re.compile(r"urllib\.request"),
        re.compile(r"socket\."),
        re.compile(r"subprocess\."),
    ]
    OUTPUT_RE = re.compile(r"^(\s*#\s*Output:\s*)(.+)$")

    result = list(lines)
    fixed_count = 0
    i = 0

    while i < len(result):
        fence = re.match(r"^```python\s*$", result[i])
        if not fence:
            i += 1
            continue

        # Collect code block
        code_lines: list[str] = []
        j = i + 1
        while j < len(result) and not re.match(r"^```\s*$", result[j]):
            code_lines.append(result[j])
            j += 1

        code_text = "\n".join(code_lines)

        # Check if block should be skipped
        skip = any(p.search(code_text) for p in SKIP_PATTERNS)
        if skip or not code_lines:
            i = j + 1
            continue

        # Find output comments in the block
        output_indices: list[int] = []
        for ci, cl in enumerate(code_lines):
            if OUTPUT_RE.match(cl):
                output_indices.append(ci)

        if not output_indices:
            i = j + 1
            continue

        # Execute code
        try:
            proc = subprocess.run(
                [sys.executable, "-c", code_text],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode != 0:
                i = j + 1
                continue

            actual_lines = proc.stdout.strip().splitlines()
        except (subprocess.TimeoutExpired, OSError):
            i = j + 1
            continue

        # Match output comments to actual output lines
        for oi_idx, ci in enumerate(output_indices):
            if oi_idx >= len(actual_lines):
                break
            m = OUTPUT_RE.match(code_lines[ci])
            if not m:
                continue
            prefix = m.group(1)
            documented = m.group(2).strip()
            actual = actual_lines[oi_idx].strip()
            if documented != actual:
                code_lines[ci] = f"{prefix}{actual}"
                fixed_count += 1

        # Write back updated code lines
        result[i + 1 : j] = code_lines

        i = i + 1 + len(code_lines) + 1

    if fixed_count:
        changes.append(f"verified and fixed {fixed_count} code output comments")
    return result


# ---------------------------------------------------------------------------
# LLM-powered information architecture enhancement
# ---------------------------------------------------------------------------


def _build_llm_prompt(title: str, body: str, content_type: str) -> str:
    """Build the LLM prompt for restructuring document architecture."""
    return f"""You are a senior technical writer restructuring a document migrated from Confluence.

TASK: Improve the INFORMATION ARCHITECTURE of this document for optimal readability.
You MUST preserve ALL content meaning, facts, code examples, and technical details.
You MUST NOT add new information or remove existing information.

RULES:
1. Apply progressive disclosure: simple/common cases first, then variations, then advanced
2. Group related content under clear, descriptive H2/H3 headings (not generic like "Overview")
3. Ensure logical flow: prerequisites -> basic usage -> configuration -> advanced -> troubleshooting
4. Keep heading hierarchy correct (no skipped levels)
5. Keep first paragraph under 60 words with a clear definition
6. Maintain all code blocks, tables, admonitions, and links exactly as-is
7. Use sentence case for headings
8. Do NOT change any frontmatter (output body only, no --- block)
9. Do NOT add commentary or explanations about your changes
10. Output ONLY the restructured document body (no frontmatter)

DOCUMENT TYPE: {content_type}
TITLE: {title}

DOCUMENT BODY:
{body}

OUTPUT the restructured document body:"""


def _enhance_with_llm(
    title: str,
    body: str,
    content_type: str,
    changes: list[str],
) -> str:
    """Use LLM to restructure information architecture."""
    try:
        # Import here to avoid hard dependency
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "packages" / "core"))
        from gitspeak_core.docs.llm_executor import LLMProvider
    except (ImportError, ModuleNotFoundError):
        changes.append("LLM enhancement skipped: llm_executor not available")
        return body

    provider = LLMProvider()
    active = provider.get_active_provider()
    if active == "none":
        changes.append("LLM enhancement skipped: no API key configured")
        return body

    prompt = _build_llm_prompt(title, body, content_type)

    try:
        response = provider.generate(
            prompt=prompt,
            system="You are a documentation restructuring assistant. Output only the restructured document body.",
            max_tokens=4000,
            temperature=0.2,
        )
        if response.error or not response.content.strip():
            changes.append(f"LLM enhancement failed: {response.error or 'empty response'}")
            return body

        enhanced = response.content.strip()

        # Safety check: enhanced version should not be drastically different in length
        orig_len = len(body.strip())
        enhanced_len = len(enhanced)
        if enhanced_len < orig_len * 0.5 or enhanced_len > orig_len * 2.0:
            changes.append("LLM enhancement rejected: output length too different from original")
            return body

        changes.append(f"LLM restructured information architecture ({active})")
        return enhanced + "\n"
    except (RuntimeError, ValueError, OSError) as exc:
        changes.append(f"LLM enhancement failed: {exc}")
        return body


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------


def enhance_file(
    filepath: Path,
    var_map: dict[str, str],
    allowed_tags: list[str],
    use_llm: bool = False,
) -> EnhancementResult:
    """Apply all quality enhancements to a single Markdown file."""
    result = EnhancementResult(file_path=str(filepath))

    try:
        text = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        result.success = False
        result.warnings.append(f"Cannot read file: {exc}")
        return result

    fm, body = _parse_frontmatter(text)
    if not fm:
        result.warnings.append("No valid frontmatter found; skipping frontmatter fixes")
        fm = {}

    title = fm.get("title", filepath.stem.replace("-", " ").title())

    # 1. LLM-powered restructuring (optional, runs first for best results)
    if use_llm:
        body = _enhance_with_llm(title, body, fm.get("content_type", "how-to"), result.changes)
        if any("LLM restructured" in c for c in result.changes):
            result.llm_enhanced = True

    # 2. Fix frontmatter
    fm = _fix_frontmatter(fm, title, body, allowed_tags, result.changes)

    # 3-11. Fix content (line-based operations)
    lines = body.split("\n")
    lines = _fix_heading_hierarchy(lines, result.changes)
    lines = _fix_generic_headings(lines, fm["content_type"], result.changes)
    body = "\n".join(lines)

    # First paragraph fix (operates on body string)
    body = _fix_first_paragraph(body, fm["content_type"], result.changes)

    lines = body.split("\n")
    lines = _fix_code_blocks(lines, result.changes)

    # LLM-powered code example and section fixes (only when --use-llm)
    llm_provider = _get_llm_provider() if use_llm else None
    lines = _fix_code_examples_with_llm(lines, fm["content_type"], result.changes, llm_provider)
    lines = _fix_missing_sections_with_llm(
        lines, fm["content_type"], title, result.changes, llm_provider,
    )

    lines = _fix_blank_lines(lines, result.changes)
    lines = _fix_ordered_lists(lines, result.changes)
    lines = _replace_variables(lines, var_map, result.changes)
    lines = _fix_bare_urls(lines, result.changes)
    lines = _ensure_next_steps(lines, fm["content_type"], result.changes)

    # Code block verification (always, no LLM required)
    lines = _fix_code_block_verification(lines, result.changes)

    # Reassemble
    new_body = "\n".join(lines)
    new_text = _serialize_frontmatter(fm) + "\n" + new_body

    # Normalize trailing whitespace
    new_text = re.sub(r"\n{3,}", "\n\n", new_text)
    if not new_text.endswith("\n"):
        new_text += "\n"

    try:
        filepath.write_text(new_text, encoding="utf-8")
    except OSError as exc:
        result.success = False
        result.warnings.append(f"Cannot write file: {exc}")

    return result


def enhance_directory(
    directory: Path,
    repo_root: Path,
    use_llm: bool = False,
) -> list[EnhancementResult]:
    """Process all .md files in a directory."""
    var_map = _load_variables(repo_root)
    allowed_tags = _load_allowed_tags(repo_root)

    results: list[EnhancementResult] = []
    md_files = sorted(directory.rglob("*.md"))

    for md_file in md_files:
        logger.info("Enhancing %s", md_file)
        result = enhance_file(md_file, var_map, allowed_tags, use_llm=use_llm)
        results.append(result)
        if result.changes:
            logger.info("  Changes: %s", "; ".join(result.changes))
        if result.warnings:
            logger.warning("  Warnings: %s", "; ".join(result.warnings))

    return results


def _write_report(results: list[EnhancementResult], report_path: Path) -> None:
    """Write enhancement report as JSON."""
    report: dict[str, Any] = {
        "total_files": len(results),
        "enhanced_files": sum(1 for r in results if r.changes),
        "llm_enhanced_files": sum(1 for r in results if r.llm_enhanced),
        "failed_files": sum(1 for r in results if not r.success),
        "files": [],
    }
    for r in results:
        report["files"].append({
            "file_path": r.file_path,
            "changes": r.changes,
            "warnings": r.warnings,
            "success": r.success,
            "llm_enhanced": r.llm_enhanced,
        })

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Enhance migrated Confluence docs to pipeline quality standards",
    )
    parser.add_argument(
        "directory",
        help="Directory containing Markdown files to enhance",
    )
    parser.add_argument(
        "--repo-root",
        default="",
        help="Repository root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--report",
        default="",
        help="Path to write JSON enhancement report",
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use LLM for information architecture restructuring",
    )
    return parser.parse_args()


def main() -> int:
    """Entry point."""
    logging.basicConfig(level=logging.INFO, format="[enhance] %(message)s")
    args = parse_args()

    directory = Path(args.directory).resolve()
    if not directory.is_dir():
        logger.error("Not a directory: %s", directory)
        return 1

    if args.repo_root:
        repo_root = Path(args.repo_root).resolve()
    else:
        repo_root = Path(__file__).resolve().parents[1]

    results = enhance_directory(directory, repo_root, use_llm=args.use_llm)

    total_changes = sum(len(r.changes) for r in results)
    total_warnings = sum(len(r.warnings) for r in results)
    llm_count = sum(1 for r in results if r.llm_enhanced)

    print(f"[enhance] processed {len(results)} files")
    print(f"[enhance] {total_changes} changes applied")
    if llm_count:
        print(f"[enhance] {llm_count} files restructured by LLM")
    if total_warnings:
        print(f"[enhance] {total_warnings} warnings")

    if args.report:
        report_path = Path(args.report).resolve()
        _write_report(results, report_path)
        print(f"[enhance] report: {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

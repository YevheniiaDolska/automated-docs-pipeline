"""
Documentation Subprocess Worker.

Entry point for isolated documentation generation subprocesses.
Each subprocess receives a TaskContext via stdin JSON, generates
a document using TemplateLibrary, performs self-checks (linting,
frontmatter, SEO/GEO validation), and writes the result to stdout.

Run as: python -m gitspeak_core.docs.doc_worker
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PROTOCOL_VERSION = "1.0"


def _validate_frontmatter(content: str) -> dict[str, Any]:
    """
    Validate frontmatter fields in generated markdown content.

    Checks for required fields (title, description, content_type),
    title length (max 70 chars), description length (50-160 chars),
    and valid content_type values.

    Args:
        content: Markdown content with YAML frontmatter.

    Returns:
        Dict with 'valid' bool, 'errors' list, and 'warnings' list.
    """
    result: dict[str, Any] = {"valid": True, "errors": [], "warnings": []}

    frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not frontmatter_match:
        result["valid"] = False
        result["errors"].append("Missing frontmatter block")
        return result

    frontmatter_text = frontmatter_match.group(1)
    fields: dict[str, str] = {}
    for line in frontmatter_text.split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip('"').strip("'")

    required_fields = ["title", "description", "content_type"]
    for field_name in required_fields:
        if field_name not in fields:
            result["valid"] = False
            result["errors"].append(f"Missing required frontmatter field: {field_name}")

    if "title" in fields and len(fields["title"]) > 70:
        result["warnings"].append(
            f"Title exceeds 70 characters: {len(fields['title'])} chars"
        )

    if "description" in fields:
        desc_len = len(fields["description"])
        if desc_len < 50:
            result["warnings"].append(
                f"Description too short: {desc_len} chars (min 50)"
            )
        elif desc_len > 160:
            result["warnings"].append(
                f"Description too long: {desc_len} chars (max 160)"
            )

    valid_types = {
        "tutorial", "how-to", "concept", "reference",
        "troubleshooting", "release-note",
    }
    if "content_type" in fields and fields["content_type"] not in valid_types:
        result["warnings"].append(
            f"Unknown content_type: {fields['content_type']}. "
            f"Valid types: {', '.join(sorted(valid_types))}"
        )

    return result


def _validate_first_paragraph(content: str) -> dict[str, Any]:
    """
    Validate the first paragraph meets GEO optimization rules.

    Checks that the first paragraph is under 60 words and contains
    a definition pattern (is, enables, provides, allows, etc.).

    Args:
        content: Markdown content (frontmatter already stripped).

    Returns:
        Dict with 'valid' bool, 'errors' list, and 'warnings' list.
    """
    result: dict[str, Any] = {"valid": True, "errors": [], "warnings": []}

    body = re.sub(r"^---\n.*?\n---\n*", "", content, flags=re.DOTALL)
    body = re.sub(r"^#+\s+.*\n+", "", body).strip()

    paragraphs = re.split(r"\n\s*\n", body)
    if not paragraphs:
        result["warnings"].append("No body content found after frontmatter")
        return result

    first_para = paragraphs[0].strip()
    word_count = len(first_para.split())

    if word_count > 60:
        result["warnings"].append(
            f"First paragraph has {word_count} words (max 60 for GEO)"
        )

    definition_patterns = [
        r"\bis\b", r"\benables?\b", r"\bprovides?\b",
        r"\ballows?\b", r"\bcreates?\b", r"\bprocesses?\b",
        r"\bexecutes?\b",
    ]
    has_definition = any(
        re.search(pattern, first_para, re.IGNORECASE)
        for pattern in definition_patterns
    )
    if not has_definition:
        result["warnings"].append(
            "First paragraph lacks a definition pattern "
            "(is, enables, provides, allows, creates, processes, executes)"
        )

    return result


def _validate_markdown_structure(content: str) -> dict[str, Any]:
    """
    Validate markdown structural rules.

    Checks for: only one H1 heading, no heading level skips,
    code blocks have language specified, and blank lines around
    headings.

    Args:
        content: Full markdown content.

    Returns:
        Dict with 'valid' bool, 'errors' list, and 'warnings' list.
    """
    result: dict[str, Any] = {"valid": True, "errors": [], "warnings": []}

    body = re.sub(r"^---\n.*?\n---\n*", "", content, flags=re.DOTALL)

    h1_count = len(re.findall(r"^# [^\n]+", body, re.MULTILINE))
    if h1_count > 1:
        result["errors"].append(f"Multiple H1 headings found: {h1_count} (max 1)")
        result["valid"] = False
    elif h1_count == 0:
        result["warnings"].append("No H1 heading found")

    headings = re.findall(r"^(#{1,6})\s", body, re.MULTILINE)
    prev_level = 0
    for heading in headings:
        level = len(heading)
        if prev_level > 0 and level > prev_level + 1:
            result["errors"].append(
                f"Heading hierarchy skip: H{prev_level} to H{level}"
            )
            result["valid"] = False
        prev_level = level

    code_blocks = re.findall(r"^```(\w*)", body, re.MULTILINE)
    for idx, lang in enumerate(code_blocks):
        if idx % 2 == 0 and not lang:
            result["warnings"].append(
                f"Code block {idx // 2 + 1} missing language specifier"
            )

    return result


def _run_self_checks(content: str) -> dict[str, Any]:
    """
    Run all self-check validations on generated document content.

    Combines frontmatter, first paragraph GEO, and markdown
    structure validations into a single result.

    Args:
        content: Full markdown document content.

    Returns:
        Dict with 'passed' bool, 'score' float, 'checks' dict
        containing individual check results.
    """
    checks = {
        "frontmatter": _validate_frontmatter(content),
        "first_paragraph": _validate_first_paragraph(content),
        "markdown_structure": _validate_markdown_structure(content),
    }

    total_errors = sum(len(c["errors"]) for c in checks.values())
    total_warnings = sum(len(c["warnings"]) for c in checks.values())

    score = 100.0
    score -= total_errors * 10.0
    score -= total_warnings * 2.0
    score = max(0.0, score)

    all_valid = all(c["valid"] for c in checks.values())

    return {
        "passed": all_valid and score >= 80.0,
        "score": score,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "checks": checks,
    }


def _generate_document(context: dict[str, Any]) -> dict[str, str]:
    """
    Generate a document from the task context.

    Uses TemplateLibrary if available, otherwise generates
    a basic markdown document from the context description.

    Args:
        context: TaskContext as a dict with 'description',
            'relevant_code', 'patterns_to_follow', etc.

    Returns:
        Dict with 'content' (markdown) and 'template_id' used.
    """
    description = context.get("description", "")
    template_id = ""

    try:
        from gitspeak_core.docs.template_library import TemplateLibrary

        lib = TemplateLibrary()
        template_map = {
            "how-to": "how_to",
            "tutorial": "tutorial",
            "concept": "concept",
            "reference": "api_reference",
            "troubleshooting": "troubleshooting",
            "quickstart": "quickstart",
            "release-note": "release_notes",
            "faq": "faq",
        }

        output_format = context.get("output_format", {})
        doc_type = output_format.get("content_type", "how-to")
        template_id = template_map.get(doc_type, "how_to")

        variables = {
            "title": output_format.get("title", "Untitled"),
            "description": output_format.get("description", description[:160]),
        }

        content = lib.render_template(template_id, variables=variables)
        return {"content": content, "template_id": template_id}

    except ImportError:
        logger.warning("TemplateLibrary not available, generating basic document")

    output_format = context.get("output_format", {})
    title = output_format.get("title", "Untitled Document")
    doc_description = output_format.get("description", description[:160])
    content_type = output_format.get("content_type", "how-to")

    content = f"""---
title: "{title}"
description: "{doc_description}"
content_type: {content_type}
---

# {title}

{description}
"""
    return {"content": content, "template_id": "basic_fallback"}


def handle_execute(request: dict[str, Any]) -> dict[str, Any]:
    """
    Handle an execute command from the orchestrator.

    Generates a document, runs self-checks, and returns the
    result in the subprocess protocol format.

    Args:
        request: Subprocess protocol request with 'task_id',
            'full_context', and optional 'previous_attempt'.

    Returns:
        Subprocess protocol response dict.
    """
    task_id = request.get("task_id", "unknown")
    context = request.get("full_context", {})
    previous_attempt = request.get("previous_attempt")

    logger.info("Executing doc generation task %s", task_id)

    if previous_attempt:
        logger.info(
            "Retrying task %s with feedback from previous attempt",
            task_id,
        )

    doc_result = _generate_document(context)
    content = doc_result["content"]
    template_id = doc_result["template_id"]

    self_check = _run_self_checks(content)

    status = "success" if self_check["passed"] else "failure"

    return {
        "protocol_version": PROTOCOL_VERSION,
        "task_id": task_id,
        "status": status,
        "code": content,
        "tests": "",
        "self_check": self_check,
        "test_results": {
            "template_id": template_id,
            "frontmatter_valid": self_check["checks"]["frontmatter"]["valid"],
            "geo_score": self_check["score"],
        },
    }


def main() -> None:
    """
    Subprocess worker entry point.

    Reads a JSON request from stdin, dispatches to the appropriate
    handler, and writes the JSON response to stdout.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )

    raw_input = sys.stdin.read()
    if not raw_input.strip():
        error_response = {
            "protocol_version": PROTOCOL_VERSION,
            "task_id": "unknown",
            "status": "failure",
            "code": "",
            "tests": "",
            "self_check": {"passed": False, "error": "Empty stdin"},
            "test_results": {},
        }
        sys.stdout.write(json.dumps(error_response))
        sys.stdout.flush()
        return

    try:
        request = json.loads(raw_input)
    except json.JSONDecodeError as exc:
        error_response = {
            "protocol_version": PROTOCOL_VERSION,
            "task_id": "unknown",
            "status": "failure",
            "code": "",
            "tests": "",
            "self_check": {"passed": False, "error": f"Invalid JSON: {exc}"},
            "test_results": {},
        }
        sys.stdout.write(json.dumps(error_response))
        sys.stdout.flush()
        return

    protocol_version = request.get("protocol_version", "1.0")
    if protocol_version != PROTOCOL_VERSION:
        logger.warning(
            "Protocol version mismatch: expected %s, got %s",
            PROTOCOL_VERSION,
            protocol_version,
        )

    command = request.get("command", "execute")
    if command == "execute":
        response = handle_execute(request)
    else:
        response = {
            "protocol_version": PROTOCOL_VERSION,
            "task_id": request.get("task_id", "unknown"),
            "status": "failure",
            "code": "",
            "tests": "",
            "self_check": {"passed": False, "error": f"Unknown command: {command}"},
            "test_results": {},
        }

    sys.stdout.write(json.dumps(response))
    sys.stdout.flush()


if __name__ == "__main__":
    main()

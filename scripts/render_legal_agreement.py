#!/usr/bin/env python3
"""Render legal agreement templates with {{PLACEHOLDER}} substitution.

Outputs finalized Markdown and optional PDF.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Z0-9_]+)\s*\}\}")


def _load_vars_file(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"vars file not found: {path}")

    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()

    if suffix == ".json":
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError("vars JSON must be an object")
        return {str(k): str(v) for k, v in payload.items()}

    # simple KEY=VALUE format (supports .env/.txt/.vars)
    values: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _parse_cli_vars(items: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"invalid --var value '{item}', expected KEY=VALUE")
        key, value = item.split("=", 1)
        k = key.strip()
        if not k:
            raise ValueError(f"invalid --var key in '{item}'")
        out[k] = value
    return out


def _extract_placeholders(template: str) -> set[str]:
    return set(PLACEHOLDER_RE.findall(template))


def _render(template: str, values: dict[str, str]) -> tuple[str, list[str]]:
    missing: list[str] = []

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in values:
            return values[key]
        missing.append(key)
        return match.group(0)

    rendered = PLACEHOLDER_RE.sub(repl, template)
    return rendered, sorted(set(missing))


def _write_pdf_from_markdown(markdown_text: str, out_pdf: Path, title: str) -> None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except ImportError as exc:
        raise RuntimeError("PDF output requires 'reportlab' (pip install reportlab)") from exc

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], spaceAfter=10, spaceBefore=8)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], spaceAfter=8, spaceBefore=8)
    body = ParagraphStyle("body", parent=styles["BodyText"], leading=14, spaceAfter=6)
    code = ParagraphStyle("code", parent=styles["Code"], leading=12, spaceAfter=6)

    story: list[Any] = []
    if title.strip():
        story.append(Paragraph(title, h1))
        story.append(Spacer(1, 4))

    for raw in markdown_text.splitlines():
        line = raw.rstrip()
        if not line:
            story.append(Spacer(1, 4))
            continue
        if line.startswith("# "):
            story.append(Paragraph(line[2:].strip(), h1))
            continue
        if line.startswith("## "):
            story.append(Paragraph(line[3:].strip(), h2))
            continue
        if line.startswith("---"):
            continue
        if line.startswith("```"):
            continue

        if line.startswith("- "):
            line = f"• {line[2:].strip()}"
        line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        style = code if line.startswith("    ") else body
        story.append(Paragraph(line, style))

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(out_pdf), pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=16 * mm, bottomMargin=16 * mm)
    doc.build(story)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render legal agreement template")
    parser.add_argument("--template", required=True, help="Path to template .md file")
    parser.add_argument("--output", required=True, help="Path for rendered .md output")
    parser.add_argument("--vars-file", default="", help="JSON or KEY=VALUE file")
    parser.add_argument("--var", action="append", default=[], help="Single KEY=VALUE; repeatable")
    parser.add_argument("--strict", action="store_true", help="Fail if any placeholders remain unresolved")
    parser.add_argument("--pdf", default="", help="Optional output PDF path")
    parser.add_argument("--title", default="", help="Optional PDF title")
    args = parser.parse_args()

    template_path = Path(args.template)
    output_path = Path(args.output)

    if not template_path.exists():
        print(f"[error] template not found: {template_path}", file=sys.stderr)
        return 2

    values: dict[str, str] = {}
    if args.vars_file:
        values.update(_load_vars_file(Path(args.vars_file)))
    values.update(_parse_cli_vars(list(args.var)))

    template_text = template_path.read_text(encoding="utf-8")
    placeholders = _extract_placeholders(template_text)
    rendered, missing = _render(template_text, values)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")

    unresolved = sorted([k for k in placeholders if k not in values])
    print(f"[render] template: {template_path}")
    print(f"[render] output: {output_path}")
    print(f"[render] placeholders_total: {len(placeholders)}")
    print(f"[render] placeholders_filled: {len(placeholders) - len(unresolved)}")
    if unresolved:
        print(f"[render] placeholders_missing: {', '.join(unresolved)}")

    if args.strict and unresolved:
        print("[error] unresolved placeholders in strict mode", file=sys.stderr)
        return 3

    if args.pdf:
        out_pdf = Path(args.pdf)
        _write_pdf_from_markdown(rendered, out_pdf, title=args.title)
        print(f"[render] pdf: {out_pdf}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

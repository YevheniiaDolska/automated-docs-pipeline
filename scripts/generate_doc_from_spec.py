#!/usr/bin/env python3
"""Render a company document skeleton from an SSOT template spec.

A spec (``templates/specs/*.spec.yml``) is a composition manifest: it declares the
frontmatter and an ordered list of sections whose content comes from single sources
(knowledge modules, SDK snippets, SSOT variables, or literal company-specific prose).
This renderer resolves those slots into a Markdown skeleton and validates the
frontmatter against ``docs-schema.yml`` plus the allowed-tags list in ``mkdocs.yml``.

Spec schema:
    doc_type: sdk-reference            # informational
    output_path: docs/reference/x.md   # where the skeleton is written
    frontmatter:                       # validated (title/description/content_type/...)
      title: "..."
      description: "..."
      content_type: reference
      product: both
      tags: [Reference]
    intro: "First paragraph prose."    # optional; drives the GEO first-paragraph rule
    geo_contract:                      # optional
      first_paragraph_max_words: 60
    sections:
      - heading: "Install the SDK"
        slots:
          - {type: prose, text: "..."}          # literal company-specific prose
          - {type: snippet, ref: sdk/install}    # --8<-- include (SSOT snippet #1)
          - {type: module, ref: auto-x-1}        # knowledge-module pointer + summary
          - {type: variable, ref: product_name}  # {{ product_name }} macro

Usage:
    python3 scripts/generate_doc_from_spec.py --spec templates/specs/x.spec.yml
    python3 scripts/generate_doc_from_spec.py --spec x.spec.yml --stdout
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import validate_frontmatter as vfm  # reuse schema loader + node validator


class SpecError(Exception):
    """Raised when a spec cannot be rendered into a valid document."""


def _tolerant_yaml_load(path: Path) -> Any:
    """Load YAML that may contain mkdocs python-object tags."""

    class _Loader(yaml.SafeLoader):
        pass

    _Loader.add_multi_constructor(
        "tag:yaml.org,2002:python/name:", lambda loader, suffix, node: None
    )
    _Loader.add_multi_constructor("!!python/name:", lambda loader, suffix, node: None)
    return yaml.load(path.read_text(encoding="utf-8"), Loader=_Loader)


def load_allowed_tags(mkdocs_path: Path) -> set[str]:
    """Return the set of allowed frontmatter tags from the mkdocs ``tags`` mapping."""
    if not mkdocs_path.exists():
        return set()
    data = _tolerant_yaml_load(mkdocs_path)

    def _find_tags(node: Any) -> dict[str, Any] | None:
        if isinstance(node, dict):
            tags = node.get("tags")
            if isinstance(tags, dict) and all(isinstance(v, str) for v in tags.values()):
                return tags
            for value in node.values():
                found = _find_tags(value)
                if found is not None:
                    return found
        elif isinstance(node, list):
            for item in node:
                found = _find_tags(item)
                if found is not None:
                    return found
        return None

    tags = _find_tags(data) or {}
    return set(tags.keys())


def validate_frontmatter_dict(
    frontmatter: dict[str, Any],
    schema: dict[str, Any],
    allowed_tags: set[str],
) -> list[str]:
    """Validate a frontmatter mapping against the schema and allowed tags."""
    errors = vfm._validate_node(frontmatter, schema, "frontmatter")
    for field in ("title", "description", "content_type"):
        if field not in frontmatter:
            errors.append(f"frontmatter.{field}: required field is missing")
    tags = frontmatter.get("tags", [])
    if tags and not isinstance(tags, list):
        errors.append("frontmatter.tags: must be a list")
    elif isinstance(tags, list) and allowed_tags:
        for tag in tags:
            if tag not in allowed_tags:
                errors.append(
                    f"frontmatter.tags: '{tag}' is not in the allowed set "
                    f"({', '.join(sorted(allowed_tags))})"
                )
    return errors


def _load_module_summary(modules_dir: Path, module_id: str) -> str:
    path = modules_dir / f"{module_id}.yml"
    if not path.exists():
        raise SpecError(f"module slot references unknown module: {module_id}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SpecError(f"module {module_id} is not a valid mapping")
    return str(payload.get("summary", "")).strip()


def _render_slot(slot: dict[str, Any], modules_dir: Path) -> str:
    slot_type = str(slot.get("type", "")).strip().lower()
    if slot_type == "prose":
        return str(slot.get("text", "")).strip()
    if slot_type == "variable":
        ref = str(slot.get("ref", "")).strip()
        if not ref:
            raise SpecError("variable slot missing 'ref'")
        return "{{ " + ref + " }}"
    if slot_type == "snippet":
        ref = str(slot.get("ref", "")).strip().removesuffix(".md")
        if not ref:
            raise SpecError("snippet slot missing 'ref'")
        return f'--8<-- "{ref}.md"'
    if slot_type == "module":
        ref = str(slot.get("ref", "")).strip()
        if not ref:
            raise SpecError("module slot missing 'ref'")
        summary = _load_module_summary(modules_dir, ref)
        # Pointer to the single source, plus its summary as a lead sentence.
        marker = f"<!-- ssot:module {ref} -->"
        return f"{marker}\n\n{summary}" if summary else marker
    raise SpecError(f"unknown slot type: {slot_type!r}")


def _dump_frontmatter(frontmatter: dict[str, Any]) -> str:
    body = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=False).rstrip("\n")
    return f"---\n{body}\n---\n"


def render_spec(spec: dict[str, Any], modules_dir: Path) -> str:
    """Render a spec mapping into a Markdown skeleton (frontmatter + sections)."""
    if not isinstance(spec, dict):
        raise SpecError("spec is not a mapping")
    frontmatter = spec.get("frontmatter")
    if not isinstance(frontmatter, dict):
        raise SpecError("spec.frontmatter is required and must be a mapping")

    title = str(frontmatter.get("title", "")).strip()
    parts = [_dump_frontmatter(frontmatter), "", f"# {title}", ""]

    intro = str(spec.get("intro", "")).strip()
    if intro:
        parts += [intro, ""]

    for section in spec.get("sections", []) or []:
        if not isinstance(section, dict):
            continue
        heading = str(section.get("heading", "")).strip()
        if heading:
            parts += [f"## {heading}", ""]
        for slot in section.get("slots", []) or []:
            if not isinstance(slot, dict):
                continue
            rendered = _render_slot(slot, modules_dir).strip()
            if rendered:
                parts += [rendered, ""]

    return "\n".join(parts).rstrip() + "\n"


def _first_paragraph_words(rendered: str) -> int:
    """Count words in the first prose paragraph after the H1."""
    lines = rendered.split("\n")
    body = lines
    for i, line in enumerate(lines):
        if line.startswith("# "):
            body = lines[i + 1:]
            break
    paragraph: list[str] = []
    for line in body:
        stripped = line.strip()
        if not stripped:
            if paragraph:
                break
            continue
        if stripped.startswith(("#", "<!--", "--8<--", "```", "|", "-", "*")):
            if paragraph:
                break
            continue
        paragraph.append(stripped)
    return len((" ".join(paragraph)).split())


def check_geo_contract(spec: dict[str, Any], rendered: str) -> list[str]:
    """Best-effort GEO checks enforced at build time, not after."""
    contract = spec.get("geo_contract", {})
    if not isinstance(contract, dict):
        return []
    warnings: list[str] = []
    max_words = contract.get("first_paragraph_max_words")
    if isinstance(max_words, int) and max_words > 0:
        count = _first_paragraph_words(rendered)
        if count > max_words:
            warnings.append(
                f"geo_contract: first paragraph has {count} words (max {max_words})"
            )
    return warnings


def build_document(
    spec: dict[str, Any],
    *,
    modules_dir: Path,
    schema: dict[str, Any],
    allowed_tags: set[str],
) -> tuple[str, list[str]]:
    """Render a spec and return (markdown, blocking_errors)."""
    frontmatter = spec.get("frontmatter", {})
    errors: list[str] = []
    if isinstance(frontmatter, dict):
        errors += validate_frontmatter_dict(frontmatter, schema, allowed_tags)
    else:
        errors.append("spec.frontmatter is required and must be a mapping")
    rendered = render_spec(spec, modules_dir)
    return rendered, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--spec", required=True, help="Path to a *.spec.yml file")
    parser.add_argument("--modules-dir", default="knowledge_modules", help="Knowledge modules directory")
    parser.add_argument("--schema", default="docs-schema.yml", help="Frontmatter schema")
    parser.add_argument("--mkdocs", default="mkdocs.yml", help="mkdocs.yml for the allowed-tags list")
    parser.add_argument("--output", default="", help="Output path (default: spec's output_path)")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of writing")
    parser.add_argument("--strict-geo", action="store_true", help="Treat GEO-contract warnings as errors")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    schema = vfm.load_schema(args.schema)
    allowed_tags = load_allowed_tags(Path(args.mkdocs))
    modules_dir = Path(args.modules_dir)

    try:
        rendered, errors = build_document(
            spec, modules_dir=modules_dir, schema=schema, allowed_tags=allowed_tags
        )
    except SpecError as exc:
        print(f"[error] {spec_path.name}: {exc}")
        return 2

    warnings = check_geo_contract(spec, rendered)
    if args.strict_geo:
        errors += warnings
        warnings = []

    for warning in warnings:
        print(f"[warn] {spec_path.name}: {warning}")
    if errors:
        print(f"[error] {spec_path.name}: frontmatter/spec validation failed:")
        for err in errors:
            print(f"  - {err}")
        return 1

    if args.stdout:
        sys.stdout.write(rendered)
        return 0

    output = args.output or str(spec.get("output_path", "")).strip()
    if not output:
        print(f"[error] {spec_path.name}: no --output and spec has no output_path")
        return 2
    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered, encoding="utf-8")
    print(f"[ok] {spec_path.name} -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

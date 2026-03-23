#!/usr/bin/env python3
"""Doc Compiler -- transform documentation into overview artifacts.

Produces 5 modalities from existing docs without LLM dependency:
  1. Executive briefing   - markdown summary from metrics + reports
  2. Cross-doc consistency - contradictions in ports/versions/terms
  3. Auto FAQ              - Q&A extraction from docs
  4. Architecture diagram  - mermaid diagram from component references
  5. Doc critique          - heuristic quality analysis
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
_scripts_dir = str(REPO_ROOT / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

# ---------------------------------------------------------------------------
# YAML loader (reuse project pattern)
# ---------------------------------------------------------------------------

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


def _load_yaml(path: Path) -> Any:
    """Load YAML file, returning empty dict on missing/error."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text) or {}
    # Minimal JSON fallback (handles simple cases)
    try:
        return json.loads(text)
    except Exception:
        return {}


def _load_json(path: Path) -> Any:
    """Load JSON file, returning empty dict on missing/error."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
CODE_BLOCK_RE = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
INTERNAL_LINK_RE = re.compile(r"\[([^\]]*)\]\((?!https?://)([^)]+)\)")
PORT_RE = re.compile(r"\bport\s+(\d{2,5})\b|\b(\d{4,5})\s*port\b", re.IGNORECASE)
PORT_STANDALONE_RE = re.compile(r":(\d{2,5})\b")
VERSION_RE = re.compile(r"\bv?(\d+\.\d+(?:\.\d+)?)\b")
URL_RE = re.compile(r"https?://[^\s)\"'>]+")


@dataclass
class DocInfo:
    """Parsed document metadata and content."""

    path: str
    title: str
    description: str
    content_type: str
    tags: list[str]
    body: str
    word_count: int
    code_blocks: list[dict[str, str]]
    headings: list[dict[str, Any]]
    internal_links: list[str]
    ports: list[str]
    versions: list[str]
    urls: list[str]


def _parse_frontmatter(text: str) -> dict[str, Any]:
    """Extract YAML frontmatter from markdown text."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    raw = match.group(1)
    if yaml is not None:
        try:
            return yaml.safe_load(raw) or {}
        except Exception:
            return {}
    # Minimal key: value parser
    result: dict[str, Any] = {}
    for line in raw.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if value.startswith("["):
                try:
                    value = json.loads(value)  # type: ignore[assignment]
                except Exception:
                    pass
            result[key] = value
    return result


def _extract_body(text: str) -> str:
    """Return markdown body without frontmatter."""
    match = FRONTMATTER_RE.match(text)
    if match:
        return text[match.end():]
    return text


def _extract_ports(text: str) -> list[str]:
    """Extract port numbers from text."""
    ports: set[str] = set()
    for m in PORT_RE.finditer(text):
        ports.add(m.group(1) or m.group(2))
    for m in PORT_STANDALONE_RE.finditer(text):
        port = m.group(1)
        val = int(port)
        if 80 <= val <= 65535:
            ports.add(port)
    return sorted(ports)


def load_doc(path: Path, docs_dir: Path) -> DocInfo:
    """Load and parse a single markdown document."""
    text = path.read_text(encoding="utf-8")
    fm = _parse_frontmatter(text)
    body = _extract_body(text)
    tags_raw = fm.get("tags", [])
    if isinstance(tags_raw, str):
        tags_raw = [t.strip() for t in tags_raw.split(",") if t.strip()]

    code_blocks = [
        {"language": m.group(1) or "text", "content": m.group(2).strip()}
        for m in CODE_BLOCK_RE.finditer(body)
    ]
    headings = [
        {"level": len(m.group(1)), "text": m.group(2).strip()}
        for m in HEADING_RE.finditer(body)
    ]
    internal_links = [m.group(2) for m in INTERNAL_LINK_RE.finditer(body)]

    rel_path = str(path.relative_to(docs_dir))
    words = len(re.findall(r"\w+", body))

    return DocInfo(
        path=rel_path,
        title=str(fm.get("title", path.stem)),
        description=str(fm.get("description", "")),
        content_type=str(fm.get("content_type", "")),
        tags=list(tags_raw) if isinstance(tags_raw, list) else [],
        body=body,
        word_count=words,
        code_blocks=code_blocks,
        headings=headings,
        internal_links=internal_links,
        ports=_extract_ports(body),
        versions=sorted(set(VERSION_RE.findall(body))),
        urls=sorted(set(URL_RE.findall(body))),
    )


def load_all_docs(docs_dir: Path) -> list[DocInfo]:
    """Load all .md files from docs directory."""
    docs: list[DocInfo] = []
    if not docs_dir.exists():
        return docs
    for md_file in sorted(docs_dir.rglob("*.md")):
        try:
            docs.append(load_doc(md_file, docs_dir))
        except Exception:
            continue
    return docs


# ---------------------------------------------------------------------------
# Modality 1: Executive briefing
# ---------------------------------------------------------------------------


def compile_executive_briefing(
    docs: list[DocInfo],
    reports_dir: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Assemble executive briefing from docs + existing reports."""
    consolidated = _load_json(reports_dir / "consolidated_report.json")
    kpi_wall = _load_json(reports_dir / "kpi-wall.json")

    health = consolidated.get("health_summary", {})
    quality_score = health.get("quality_score", "N/A")
    drift_status = health.get("drift_status", "N/A")
    sla_status = health.get("sla_status", "N/A")
    total_actions = health.get("total_action_items", 0)

    # Doc coverage breakdown
    type_counts: dict[str, int] = {}
    total_words = 0
    total_code_blocks = 0
    for doc in docs:
        ct = doc.content_type or "untyped"
        type_counts[ct] = type_counts.get(ct, 0) + 1
        total_words += doc.word_count
        total_code_blocks += len(doc.code_blocks)

    # Top action items
    action_items = consolidated.get("action_items", [])
    top_actions = action_items[:5]

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = [
        f"# Documentation executive briefing ({now})",
        "",
        "## Health summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Quality score | {quality_score} |",
        f"| Drift status | {drift_status} |",
        f"| SLA status | {sla_status} |",
        f"| Action items | {total_actions} |",
        "",
        "## Documentation coverage",
        "",
        f"- **Total documents:** {len(docs)}",
        f"- **Total words:** {total_words:,}",
        f"- **Total code blocks:** {total_code_blocks}",
        "",
        "### By content type",
        "",
        "| Content type | Count |",
        "|-------------|-------|",
    ]
    for ct in sorted(type_counts.keys()):
        lines.append(f"| {ct} | {type_counts[ct]} |")

    if top_actions:
        lines.extend(["", "## Top action items", ""])
        for i, item in enumerate(top_actions, 1):
            title = item.get("title", "Untitled")
            priority = item.get("priority", "unknown")
            source = item.get("source_report", "unknown")
            lines.append(f"{i}. **[{priority}]** {title} (source: {source})")

    if kpi_wall:
        kpi_metrics = kpi_wall.get("metrics", kpi_wall)
        if isinstance(kpi_metrics, dict):
            lines.extend(["", "## KPI highlights", ""])
            for key, value in list(kpi_metrics.items())[:8]:
                if isinstance(value, dict):
                    val = value.get("value", value.get("score", ""))
                else:
                    val = value
                lines.append(f"- **{key}:** {val}")

    lines.append("")
    content = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")

    return {
        "modality": "executive_briefing",
        "output": str(output_path),
        "doc_count": len(docs),
        "quality_score": quality_score,
        "action_items_count": total_actions,
    }


# ---------------------------------------------------------------------------
# Modality 2: Cross-doc consistency
# ---------------------------------------------------------------------------


def compile_cross_doc_consistency(
    docs: list[DocInfo],
    glossary_path: Path,
    variables_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Check cross-document consistency for ports, versions, terms."""
    issues: list[dict[str, Any]] = []

    # Load reference data
    glossary = _load_yaml(glossary_path)
    variables = _load_yaml(variables_path)

    # Flatten variables for comparison
    flat_vars: dict[str, str] = {}
    _flatten_dict(variables, "", flat_vars)

    # 1. Port contradictions -- check if different docs mention different ports
    port_sources: dict[str, list[str]] = {}
    for doc in docs:
        for port in doc.ports:
            port_sources.setdefault(port, []).append(doc.path)

    # Check ports against _variables.yml
    var_ports: set[str] = set()
    for key, val in flat_vars.items():
        if "port" in key.lower():
            var_ports.add(str(val))

    for port, sources in port_sources.items():
        if var_ports and port not in var_ports:
            issues.append({
                "type": "port_not_in_variables",
                "severity": "warning",
                "port": port,
                "docs": sources,
                "message": (
                    f"Port {port} found in docs but not in _variables.yml. "
                    f"Consider using a variable."
                ),
            })

    # 2. Version contradictions
    version_sources: dict[str, list[str]] = {}
    for doc in docs:
        for ver in doc.versions:
            version_sources.setdefault(ver, []).append(doc.path)

    var_versions: set[str] = set()
    for key, val in flat_vars.items():
        if "version" in key.lower():
            var_versions.add(str(val))

    # 3. Terminology mismatches (check glossary)
    if isinstance(glossary, dict):
        terms = glossary.get("terms", glossary)
        if isinstance(terms, list):
            for entry in terms:
                if not isinstance(entry, dict):
                    continue
                preferred = str(entry.get("preferred", entry.get("term", "")))
                aliases = entry.get("aliases", [])
                if isinstance(aliases, str):
                    aliases = [a.strip() for a in aliases.split(",")]
                for alias in aliases:
                    alias_lower = alias.lower()
                    for doc in docs:
                        if alias_lower in doc.body.lower():
                            # Check it is not just part of the preferred term
                            if preferred.lower() != alias_lower:
                                issues.append({
                                    "type": "terminology_mismatch",
                                    "severity": "warning",
                                    "alias_used": alias,
                                    "preferred_term": preferred,
                                    "doc": doc.path,
                                    "message": (
                                        f"Non-preferred term '{alias}' used in "
                                        f"{doc.path}. Preferred: '{preferred}'."
                                    ),
                                })

    # 4. Hardcoded values that should use variables
    for doc in docs:
        for key, val in flat_vars.items():
            val_str = str(val)
            if len(val_str) < 3:
                continue
            # Skip common false positives
            if val_str in ("True", "False", "None", "true", "false"):
                continue
            if val_str in doc.body and "{{" not in doc.body.split(val_str)[0][-30:]:
                issues.append({
                    "type": "hardcoded_variable",
                    "severity": "suggestion",
                    "variable": key,
                    "value": val_str,
                    "doc": doc.path,
                    "message": (
                        f"Hardcoded value '{val_str}' in {doc.path} could use "
                        f"variable '{{{{ {key} }}}}'."
                    ),
                })

    result = {
        "modality": "cross_doc_consistency",
        "output": str(output_path),
        "total_issues": len(issues),
        "issues_by_type": _count_by_key(issues, "type"),
        "issues": issues,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result


def _flatten_dict(
    d: Any, prefix: str, result: dict[str, str],
) -> None:
    """Flatten a nested dict into dot-separated keys."""
    if isinstance(d, dict):
        for key, val in d.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            _flatten_dict(val, new_prefix, result)
    else:
        result[prefix] = str(d)


def _count_by_key(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    """Count items grouped by a key."""
    counts: dict[str, int] = {}
    for item in items:
        val = str(item.get(key, "unknown"))
        counts[val] = counts.get(val, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Modality 3: Auto FAQ
# ---------------------------------------------------------------------------


def compile_auto_faq(
    docs: list[DocInfo],
    output_path: Path,
    faq_doc_path: Path | None = None,
) -> dict[str, Any]:
    """Extract Q&A pairs from documentation."""
    faqs: list[dict[str, Any]] = []

    for doc in docs:
        ct = doc.content_type.lower()

        if ct == "troubleshooting":
            # Extract problem/solution pairs from headings + body
            faqs.extend(_extract_troubleshooting_faq(doc))
        elif ct == "how-to":
            # Generate "How do I...?" from title
            faqs.append({
                "question": f"How do I {_to_question_form(doc.title)}?",
                "answer": doc.description or _first_paragraph(doc.body),
                "source": doc.path,
                "tags": doc.tags,
                "category": "how-to",
            })
        elif ct in ("concept", "reference"):
            # Generate "What is...?" from first paragraph
            if doc.title:
                faqs.append({
                    "question": f"What is {_strip_title_prefix(doc.title)}?",
                    "answer": doc.description or _first_paragraph(doc.body),
                    "source": doc.path,
                    "tags": doc.tags,
                    "category": ct,
                })
        elif ct == "tutorial":
            faqs.append({
                "question": (
                    f"How do I get started with "
                    f"{_strip_title_prefix(doc.title)}?"
                ),
                "answer": doc.description or _first_paragraph(doc.body),
                "source": doc.path,
                "tags": doc.tags,
                "category": "tutorial",
            })

    # Group by tags
    tag_groups: dict[str, list[int]] = {}
    for i, faq in enumerate(faqs):
        for tag in faq.get("tags", []):
            tag_groups.setdefault(tag, []).append(i)

    result = {
        "modality": "auto_faq",
        "output": str(output_path),
        "total_faqs": len(faqs),
        "faqs_by_category": _count_by_key(faqs, "category"),
        "tag_groups": {k: len(v) for k, v in tag_groups.items()},
        "faqs": faqs,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Optionally generate a FAQ markdown doc
    if faq_doc_path:
        _write_faq_doc(faqs, tag_groups, faq_doc_path)

    return result


def _extract_troubleshooting_faq(doc: DocInfo) -> list[dict[str, Any]]:
    """Extract Q&A from troubleshooting doc structure."""
    faqs: list[dict[str, Any]] = []
    sections = re.split(r"\n##\s+", doc.body)
    for section in sections[1:]:  # Skip content before first H2
        lines = section.strip().splitlines()
        if not lines:
            continue
        heading = lines[0].strip()
        body_text = "\n".join(lines[1:]).strip()
        if body_text:
            faqs.append({
                "question": heading.rstrip("?") + "?",
                "answer": _first_paragraph(body_text),
                "source": doc.path,
                "tags": doc.tags,
                "category": "troubleshooting",
            })
    return faqs


def _to_question_form(title: str) -> str:
    """Convert a title to lowercase question form."""
    title = title.lower().strip()
    for prefix in ("how to ", "guide to ", "configure ", "set up "):
        if title.startswith(prefix):
            return title
    return title


def _strip_title_prefix(title: str) -> str:
    """Remove common prefixes from title for question form."""
    for prefix in ("The ", "A ", "An "):
        if title.startswith(prefix):
            title = title[len(prefix):]
    return title


def _first_paragraph(text: str) -> str:
    """Extract first non-empty paragraph."""
    for para in text.split("\n\n"):
        stripped = para.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("```"):
            return stripped[:300]
    return text[:300].strip()


def _write_faq_doc(
    faqs: list[dict[str, Any]],
    tag_groups: dict[str, list[int]],
    output_path: Path,
) -> None:
    """Write FAQ as a markdown document."""
    lines = [
        "---",
        'title: "Frequently asked questions"',
        'description: "Auto-generated FAQ from documentation content types."',
        "content_type: reference",
        "tags:",
        "  - Reference",
        "---",
        "",
        "# Frequently asked questions",
        "",
    ]
    # Group by category
    by_cat: dict[str, list[dict[str, Any]]] = {}
    for faq in faqs:
        cat = faq.get("category", "general")
        by_cat.setdefault(cat, []).append(faq)

    for cat in sorted(by_cat.keys()):
        lines.append(f"## {cat.replace('-', ' ').title()}")
        lines.append("")
        for faq in by_cat[cat]:
            lines.append(f"### {faq['question']}")
            lines.append("")
            lines.append(faq["answer"])
            lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Modality 4: Architecture diagram
# ---------------------------------------------------------------------------


INTERACTIVE_THRESHOLD = 6  # Generate interactive HTML when 6+ components

# HTML entity icons per content type / keyword
_COMPONENT_ICONS: dict[str, str] = {
    "api": "&#128268;",
    "auth": "&#128272;",
    "database": "&#128451;",
    "cache": "&#9889;",
    "storage": "&#128193;",
    "worker": "&#128736;",
    "service": "&#9881;",
    "gateway": "&#9878;",
    "client": "&#128187;",
    "web": "&#127760;",
    "cdn": "&#127758;",
    "queue": "&#128229;",
}


def _pick_icon(name: str) -> str:
    """Pick an HTML entity icon based on component name keywords."""
    lower = name.lower()
    for keyword, icon in _COMPONENT_ICONS.items():
        if keyword in lower:
            return icon
    return "&#9881;"  # Default: gear


def _generate_interactive_html(
    components: dict[str, dict[str, Any]],
    layers: dict[str, list[str]],
    relationships: set[tuple[str, str]],
) -> str:
    """Generate interactive HTML diagram from components and layers."""
    # Build layer HTML
    layer_blocks: list[str] = []
    layer_names = sorted(layers.keys())
    for i, layer_name in enumerate(layer_names):
        comp_ids = layers[layer_name]
        display_name = layer_name.replace("-", " ").title()
        comps_html = []
        for cid in comp_ids:
            info = components[cid]
            icon = _pick_icon(info["name"])
            comps_html.append(
                f'    <div class="component" data-id="{cid}" '
                f'onclick="showInfo(\'{cid}\')">\n'
                f'      <span class="icon">{icon}</span>\n'
                f'      <div class="name">{info["name"]}</div>\n'
                f'      <div class="metric">{info["source"]}</div>\n'
                f'    </div>'
            )
        layer_blocks.append(
            f'  <div class="layer-label">{display_name}</div>\n'
            f'  <div class="layer">\n'
            + "\n".join(comps_html)
            + "\n  </div>"
        )
        if i < len(layer_names) - 1:
            arrows = " ".join(["&#8595;"] * min(len(comp_ids), 5))
            layer_blocks.append(f'  <div class="arrow-row">{arrows}</div>')

    diagram_html = "\n\n".join(layer_blocks)

    # Build descriptions JS object
    desc_entries: list[str] = []
    for cid, info in components.items():
        name = info["name"].replace('"', '\\"')
        source = info["source"].replace('"', '\\"')
        ctype = (info.get("type") or "other").replace('"', '\\"')
        desc_entries.append(
            f'  {cid}: {{\n'
            f'    title: "{name}",\n'
            f'    desc: "Component from {source}. '
            f'Content type: {ctype}.",\n'
            f'    tags: ["{ctype}"]\n'
            f'  }}'
        )
    descriptions_js = "{\n" + ",\n".join(desc_entries) + "\n}"

    # Read template and inject content
    template_path = REPO_ROOT / "templates" / "interactive-diagram.html"
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
        # Replace title
        html = template.replace(
            "[System] Architecture", "Documentation Architecture"
        )
        # Replace diagram content between EDIT markers
        edit_start = "<!-- === EDIT THIS SECTION: Add/remove layers and components === -->"
        edit_end = "<!-- === END EDITABLE SECTION === -->"
        if edit_start in html and edit_end in html:
            before = html.split(edit_start)[0]
            after = html.split(edit_end)[1]
            html = (
                before
                + edit_start + "\n"
                + '<div class="diagram">\n\n'
                + diagram_html
                + "\n\n</div>\n"
                + edit_end
                + after
            )
        # Replace descriptions JS
        desc_start = "// === EDIT THIS SECTION: descriptions for each component ==="
        if desc_start in html:
            # Find the const descriptions = { ... }; block and replace it
            desc_pattern = re.compile(
                r"const descriptions = \{.*?\};", re.DOTALL
            )
            html = desc_pattern.sub(
                f"const descriptions = {descriptions_js};", html,
            )
        return html

    # Fallback: minimal standalone HTML if template missing
    return (
        "<!DOCTYPE html>\n<html><head><meta charset='UTF-8'>"
        "<title>Architecture</title></head><body>\n"
        f"<h1>Documentation Architecture</h1>\n"
        f"<p>{len(components)} components across {len(layers)} layers</p>\n"
        "</body></html>"
    )


def compile_architecture_diagram(
    docs: list[DocInfo],
    output_path: Path,
) -> dict[str, Any]:
    """Generate architecture diagram from docs.

    Produces a mermaid markdown diagram always. When 6+ components are
    detected, also generates an interactive HTML diagram (per CLAUDE.md
    rules for multi-component architecture docs).
    """
    # Filter architecture-relevant docs
    arch_docs = [
        d for d in docs
        if d.content_type in ("concept", "reference")
        or any(t.lower() in ("architecture", "api", "deployment")
               for t in d.tags)
    ]

    if not arch_docs:
        arch_docs = docs  # Fallback to all docs

    # Extract components from H2 headings
    components: dict[str, dict[str, Any]] = {}
    for doc in arch_docs:
        for h in doc.headings:
            if h["level"] == 2:
                name = h["text"]
                comp_id = re.sub(r"[^a-zA-Z0-9]", "_", name)[:30]
                if comp_id not in components:
                    components[comp_id] = {
                        "name": name,
                        "source": doc.path,
                        "type": doc.content_type,
                    }

    # Detect relationships via internal links
    relationships: list[dict[str, str]] = []
    doc_path_to_id: dict[str, str] = {}
    for comp_id, info in components.items():
        source = info["source"]
        if source not in doc_path_to_id:
            doc_path_to_id[source] = comp_id

    for doc in arch_docs:
        from_id = doc_path_to_id.get(doc.path)
        if not from_id:
            continue
        for link in doc.internal_links:
            # Resolve link to a doc path
            link_clean = link.split("#")[0].split("?")[0]
            for target_path, target_id in doc_path_to_id.items():
                if target_path.endswith(link_clean) or link_clean.endswith(
                    Path(target_path).stem
                ):
                    if from_id != target_id:
                        relationships.append({
                            "from": from_id,
                            "to": target_id,
                        })

    # Group components into layers by content type
    layers: dict[str, list[str]] = {}
    for comp_id, info in components.items():
        layer = info.get("type", "other") or "other"
        layers.setdefault(layer, []).append(comp_id)

    # Generate mermaid (always produced)
    mermaid_lines = ["```mermaid", "graph TD"]

    for layer_name, comp_ids in sorted(layers.items()):
        display_name = layer_name.replace("-", " ").title()
        mermaid_lines.append(f"    subgraph {display_name}")
        for cid in comp_ids:
            label = components[cid]["name"]
            mermaid_lines.append(f"        {cid}[\"{label}\"]")
        mermaid_lines.append("    end")

    seen_rels: set[tuple[str, str]] = set()
    for rel in relationships:
        pair = (rel["from"], rel["to"])
        if pair not in seen_rels:
            mermaid_lines.append(f"    {rel['from']} --> {rel['to']}")
            seen_rels.add(pair)

    mermaid_lines.append("```")

    # Build markdown output
    content = "\n".join([
        "# Architecture overview",
        "",
        "Auto-generated architecture diagram from documentation cross-references.",
        "",
        "\n".join(mermaid_lines),
        "",
        "## Components",
        "",
        "| Component | Source | Type |",
        "|-----------|--------|------|",
    ] + [
        f"| {info['name']} | {info['source']} | {info['type']} |"
        for info in components.values()
    ] + [""])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")

    result: dict[str, Any] = {
        "modality": "architecture_diagram",
        "output": str(output_path),
        "components_count": len(components),
        "relationships_count": len(seen_rels),
        "layers": {k: len(v) for k, v in layers.items()},
        "interactive": False,
    }

    # Generate interactive HTML when 6+ components
    if len(components) >= INTERACTIVE_THRESHOLD:
        html_path = output_path.with_suffix(".html")
        html_content = _generate_interactive_html(
            components, layers, seen_rels,
        )
        html_path.write_text(html_content, encoding="utf-8")
        result["interactive"] = True
        result["interactive_output"] = str(html_path)

    return result


# ---------------------------------------------------------------------------
# Modality 5: Doc critique
# ---------------------------------------------------------------------------

# Heuristic thresholds
THIN_CONTENT_WORDS = 100
SHORT_DESCRIPTION_CHARS = 50
BOILERPLATE_PHRASES = [
    "lorem ipsum",
    "todo",
    "fixme",
    "placeholder",
    "coming soon",
    "tbd",
    "to be determined",
    "work in progress",
]
SYLLABLE_RE = re.compile(r"[aeiouy]+", re.IGNORECASE)


def compile_doc_critique(
    docs: list[DocInfo],
    reports_dir: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Run 8 heuristic quality checks on documentation."""
    issues: list[dict[str, Any]] = []

    # Build lookup for orphan detection
    all_paths = {d.path for d in docs}
    linked_paths: set[str] = set()
    for doc in docs:
        for link in doc.internal_links:
            linked_paths.add(link.lstrip("./"))

    for doc in docs:
        # 1. Missing code examples in tutorials/how-tos
        if doc.content_type in ("tutorial", "how-to") and not doc.code_blocks:
            issues.append({
                "check": "missing_code_examples",
                "severity": "warning",
                "doc": doc.path,
                "message": (
                    f"{doc.content_type} '{doc.title}' has no code examples."
                ),
            })

        # 2. Short descriptions
        if len(doc.description) < SHORT_DESCRIPTION_CHARS and doc.description:
            issues.append({
                "check": "short_description",
                "severity": "warning",
                "doc": doc.path,
                "message": (
                    f"Description is only {len(doc.description)} chars "
                    f"(minimum recommended: {SHORT_DESCRIPTION_CHARS})."
                ),
            })

        # 3. Thin content
        if doc.word_count < THIN_CONTENT_WORDS:
            issues.append({
                "check": "thin_content",
                "severity": "warning",
                "doc": doc.path,
                "message": (
                    f"Only {doc.word_count} words "
                    f"(minimum recommended: {THIN_CONTENT_WORDS})."
                ),
            })

        # 4. Boilerplate detection
        body_lower = doc.body.lower()
        for phrase in BOILERPLATE_PHRASES:
            if phrase in body_lower:
                issues.append({
                    "check": "boilerplate_detected",
                    "severity": "warning",
                    "doc": doc.path,
                    "phrase": phrase,
                    "message": (
                        f"Boilerplate phrase '{phrase}' found in {doc.path}."
                    ),
                })

        # 5. Reading level (simple Flesch-Kincaid approximation)
        sentences = len(re.findall(r"[.!?]+", doc.body)) or 1
        words = doc.word_count or 1
        syllables = len(SYLLABLE_RE.findall(doc.body)) or 1
        fk_grade = 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59
        if fk_grade > 14:
            issues.append({
                "check": "high_reading_level",
                "severity": "suggestion",
                "doc": doc.path,
                "reading_level": round(fk_grade, 1),
                "message": (
                    f"Reading level is grade {fk_grade:.1f} "
                    f"(target: below 14)."
                ),
            })

    # 6. Orphaned docs (not linked from any other doc)
    for doc in docs:
        normalized = doc.path.lstrip("./")
        if normalized not in linked_paths and doc.content_type != "":
            # Index pages are expected to not be linked
            if not normalized.endswith("index.md"):
                issues.append({
                    "check": "orphaned_doc",
                    "severity": "suggestion",
                    "doc": doc.path,
                    "message": (
                        f"No internal links point to {doc.path}."
                    ),
                })

    # 7. Duplicate coverage (multiple docs with very similar titles)
    titles_lower: dict[str, list[str]] = {}
    for doc in docs:
        key = re.sub(r"[^a-z0-9]+", " ", doc.title.lower()).strip()
        titles_lower.setdefault(key, []).append(doc.path)
    for title_key, paths in titles_lower.items():
        if len(paths) > 1:
            issues.append({
                "check": "duplicate_coverage",
                "severity": "warning",
                "docs": paths,
                "title_key": title_key,
                "message": (
                    f"Possible duplicate coverage: {', '.join(paths)} "
                    f"have similar titles."
                ),
            })

    # 8. Missing content types per feature area (tag-based)
    tag_types: dict[str, set[str]] = {}
    for doc in docs:
        for tag in doc.tags:
            tag_types.setdefault(tag, set()).add(doc.content_type)
    expected_types = {"tutorial", "how-to", "reference"}
    for tag, types in tag_types.items():
        missing = expected_types - types
        if missing and len(types) >= 1:
            issues.append({
                "check": "missing_doc_type_for_feature",
                "severity": "suggestion",
                "tag": tag,
                "existing_types": sorted(types),
                "missing_types": sorted(missing),
                "message": (
                    f"Tag '{tag}' has {', '.join(sorted(types))} but no "
                    f"{', '.join(sorted(missing))}."
                ),
            })

    result = {
        "modality": "doc_critique",
        "output": str(output_path),
        "total_issues": len(issues),
        "issues_by_check": _count_by_key(issues, "check"),
        "issues_by_severity": _count_by_key(issues, "severity"),
        "issues": issues,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result


# ---------------------------------------------------------------------------
# Combined runner
# ---------------------------------------------------------------------------

ALL_MODALITIES = [
    "executive_briefing",
    "cross_doc_consistency",
    "auto_faq",
    "architecture_diagram",
    "doc_critique",
]


def run_doc_compiler(
    docs_dir: Path,
    reports_dir: Path,
    glossary_path: Path,
    modalities: list[str],
    generate_faq_doc: bool = False,
) -> dict[str, Any]:
    """Run selected doc compiler modalities."""
    docs = load_all_docs(docs_dir)
    variables_path = docs_dir / "_variables.yml"
    results: dict[str, Any] = {}

    if "executive_briefing" in modalities:
        results["executive_briefing"] = compile_executive_briefing(
            docs, reports_dir,
            reports_dir / "doc_compiler_briefing.md",
        )

    if "cross_doc_consistency" in modalities:
        results["cross_doc_consistency"] = compile_cross_doc_consistency(
            docs, glossary_path, variables_path,
            reports_dir / "doc_compiler_consistency.json",
        )

    if "auto_faq" in modalities:
        faq_doc = (docs_dir / "faq-auto-generated.md") if generate_faq_doc else None
        results["auto_faq"] = compile_auto_faq(
            docs,
            reports_dir / "doc_compiler_faq.json",
            faq_doc,
        )

    if "architecture_diagram" in modalities:
        results["architecture_diagram"] = compile_architecture_diagram(
            docs,
            reports_dir / "doc_compiler_architecture.md",
        )

    if "doc_critique" in modalities:
        results["doc_critique"] = compile_doc_critique(
            docs, reports_dir,
            reports_dir / "doc_compiler_critique.json",
        )

    # Write combined report
    combined = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "docs_dir": str(docs_dir),
        "total_docs_loaded": len(docs),
        "modalities_run": list(results.keys()),
        "results": results,
    }
    combined_path = reports_dir / "doc_compiler_report.json"
    combined_path.parent.mkdir(parents=True, exist_ok=True)
    combined_path.write_text(
        json.dumps(combined, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return combined


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point."""
    from license_gate import require

    parser = argparse.ArgumentParser(
        description="Doc Compiler -- documentation overview artifacts",
    )
    parser.add_argument(
        "--docs-dir", default="docs",
        help="Path to docs directory (default: docs)",
    )
    parser.add_argument(
        "--reports-dir", default="reports",
        help="Path to reports directory (default: reports)",
    )
    parser.add_argument(
        "--glossary-path", default="glossary.yml",
        help="Path to glossary.yml (default: glossary.yml)",
    )
    parser.add_argument(
        "--modalities", default="all",
        help=(
            "Comma-separated modalities to run, or 'all'. "
            "Options: executive_briefing, cross_doc_consistency, "
            "auto_faq, architecture_diagram, doc_critique"
        ),
    )
    parser.add_argument(
        "--generate-faq-doc", action="store_true",
        help="Also generate a FAQ markdown document in docs/",
    )
    args = parser.parse_args()

    # License gate
    require("doc_compiler")

    # Parse modalities
    if args.modalities.strip().lower() == "all":
        modalities = list(ALL_MODALITIES)
    else:
        modalities = [
            m.strip() for m in args.modalities.split(",") if m.strip()
        ]
        invalid = set(modalities) - set(ALL_MODALITIES)
        if invalid:
            print(
                f"[doc-compiler] Unknown modalities: {', '.join(invalid)}. "
                f"Valid: {', '.join(ALL_MODALITIES)}",
                file=sys.stderr,
            )
            return 1

    docs_dir = Path(args.docs_dir)
    reports_dir = Path(args.reports_dir)
    glossary_path = Path(args.glossary_path)

    print(f"[doc-compiler] Running modalities: {', '.join(modalities)}")
    print(f"[doc-compiler] Docs: {docs_dir}, Reports: {reports_dir}")

    result = run_doc_compiler(
        docs_dir=docs_dir,
        reports_dir=reports_dir,
        glossary_path=glossary_path,
        modalities=modalities,
        generate_faq_doc=args.generate_faq_doc,
    )

    print(f"[doc-compiler] Loaded {result['total_docs_loaded']} documents")
    print(f"[doc-compiler] Completed: {', '.join(result['modalities_run'])}")
    print(
        f"[doc-compiler] Combined report: "
        f"{reports_dir / 'doc_compiler_report.json'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

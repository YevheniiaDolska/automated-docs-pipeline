#!/usr/bin/env python3
"""Validate interactive HTML diagrams and Mermaid diagrams against document content.

Catches diagram hallucinations at three levels:
- Level 1: Structural integrity (diagram HTML alone)
- Level 2: Document-diagram consistency (cross-validation)
- Level 3: Semantic coherence (internal logic)

Also validates Mermaid diagrams in markdown code blocks against the surrounding
document text to ensure consistent component names, metrics, and structure.

Usage:
    python scripts/validate_diagram_content.py docs templates
    python scripts/validate_diagram_content.py --strict docs/
"""

from __future__ import annotations

import argparse
import html.parser
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class DiagramComponent:
    """A single interactive component parsed from diagram HTML."""

    data_id: str
    name: str
    metric: str
    layer: str


@dataclass
class DiagramInfo:
    """Parsed representation of an interactive HTML diagram."""

    path: Path
    components: list[DiagramComponent] = field(default_factory=list)
    layers: list[str] = field(default_factory=list)
    descriptions: dict[str, dict] = field(default_factory=dict)
    has_sync_theme: bool = False
    has_css_variables: bool = False
    title: str = ""


@dataclass
class MermaidDiagram:
    """A Mermaid diagram extracted from a markdown code block."""

    md_path: Path
    line: int
    source: str
    node_labels: list[str] = field(default_factory=list)


@dataclass
class DiagramEmbedding:
    """An iframe embedding linking a markdown file to a diagram HTML file."""

    md_path: Path
    diagram_path: Path
    iframe_line: int
    context_text: str


@dataclass
class ValidationIssue:
    """A single validation finding."""

    path: Path
    line: int
    level: str  # "error" | "warning"
    check: str  # e.g. "L1:data-id-mismatch"
    message: str


# ---------------------------------------------------------------------------
# HTML parser
# ---------------------------------------------------------------------------

class _DiagramHTMLParser(html.parser.HTMLParser):
    """Extract components, layers, and metadata from diagram HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.components: list[dict] = []
        self.layers: list[str] = []
        self.title: str = ""

        self._in_layer_label = False
        self._in_name = False
        self._in_metric = False
        self._in_h1 = False
        self._current_layer = ""
        self._current_component: dict | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = dict(attrs)
        cls = attr_dict.get("class", "") or ""

        if tag == "h1":
            self._in_h1 = True
            return

        if "layer-label" in cls:
            self._in_layer_label = True
            return

        if "component" in cls:
            data_id = attr_dict.get("data-id", "")
            self._current_component = {
                "data_id": data_id,
                "name": "",
                "metric": "",
                "layer": self._current_layer,
            }
            return

        if self._current_component is not None:
            if "name" in cls:
                self._in_name = True
            elif "metric" in cls:
                self._in_metric = True

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return

        if self._in_h1:
            self.title = text
            return

        if self._in_layer_label:
            self._current_layer = text
            if text not in self.layers:
                self.layers.append(text)
            return

        if self._in_name and self._current_component is not None:
            self._current_component["name"] = text
            return

        if self._in_metric and self._current_component is not None:
            self._current_component["metric"] = text
            return

    def handle_endtag(self, tag: str) -> None:
        if tag == "h1":
            self._in_h1 = False

        if self._in_layer_label and tag == "div":
            self._in_layer_label = False

        if self._in_name and tag == "div":
            self._in_name = False

        if self._in_metric and tag == "div":
            self._in_metric = False
            if self._current_component is not None:
                self.components.append(self._current_component)
                self._current_component = None

    def handle_entityref(self, name: str) -> None:
        text = f"&{name};"
        if self._in_metric and self._current_component is not None:
            self._current_component["metric"] += html.parser.unescape(text)
        if self._in_name and self._current_component is not None:
            self._current_component["name"] += html.parser.unescape(text)

    def handle_charref(self, name: str) -> None:
        text = f"&#{name};"
        char = html.parser.unescape(text)
        if self._in_metric and self._current_component is not None:
            self._current_component["metric"] += char
        if self._in_name and self._current_component is not None:
            self._current_component["name"] += char


# ---------------------------------------------------------------------------
# JS object → Python dict
# ---------------------------------------------------------------------------

def _js_object_to_json(js_text: str) -> dict:
    """Convert a JS object literal to a Python dict.

    Handles unquoted keys, single-quoted strings, trailing commas,
    and arrays of strings.
    """
    text = js_text.strip()
    if not text:
        return {}

    # Remove JS single-line comments
    text = re.sub(r'//[^\n]*', '', text)
    # Remove JS multi-line comments
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

    # Quote unquoted keys: word at start of line or after { or ,
    text = re.sub(r'(?<=[{,\n])\s*(\w+)\s*:', r' "\1":', text)
    # Fix first key if it wasn't caught
    if re.match(r'\s*\{?\s*\w+\s*:', text):
        text = re.sub(r'^(\s*\{?\s*)(\w+)(\s*:)', r'\1"\2"\3', text)

    # Replace single-quoted strings with double-quoted
    text = re.sub(r"'([^']*)'", r'"\1"', text)

    # Remove trailing commas before } or ]
    text = re.sub(r',\s*([}\]])', r'\1', text)

    # Ensure outer braces
    text = text.strip()
    if not text.startswith("{"):
        text = "{" + text
    if not text.endswith("}"):
        text = text + "}"

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


# ---------------------------------------------------------------------------
# Parsing functions
# ---------------------------------------------------------------------------

def parse_diagram_html(path: Path) -> DiagramInfo:
    """Parse an interactive diagram HTML file into DiagramInfo."""
    content = path.read_text(encoding="utf-8", errors="ignore")
    info = DiagramInfo(path=path)

    # Parse HTML structure
    parser = _DiagramHTMLParser()
    parser.feed(content)

    info.title = parser.title
    info.layers = parser.layers
    info.components = [
        DiagramComponent(
            data_id=c["data_id"],
            name=c["name"],
            metric=c["metric"],
            layer=c["layer"],
        )
        for c in parser.components
    ]

    # Extract descriptions JS object
    match = re.search(
        r'const\s+descriptions\s*=\s*\{(.+?)\};',
        content,
        re.DOTALL,
    )
    if match:
        info.descriptions = _js_object_to_json("{" + match.group(1) + "}")

    # Check for syncTheme function
    info.has_sync_theme = "function syncTheme" in content or "syncTheme()" in content

    # Check for CSS custom properties
    required_vars = {"--bg", "--surface", "--border", "--text", "--accent"}
    found_vars = set(re.findall(r'(--(?:bg|surface|border|text|accent))\s*:', content))
    info.has_css_variables = required_vars.issubset(found_vars)

    return info


def _extract_mermaid_blocks(md_path: Path, content: str) -> list[MermaidDiagram]:
    """Extract Mermaid code blocks from markdown content."""
    diagrams: list[MermaidDiagram] = []
    lines = content.splitlines()
    in_block = False
    block_start = 0
    block_lines: list[str] = []

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not in_block and stripped.startswith("```") and "mermaid" in stripped.lower():
            in_block = True
            block_start = i
            block_lines = []
            continue
        if in_block and stripped.startswith("```"):
            source = "\n".join(block_lines)
            # Extract node labels from mermaid syntax
            labels = _extract_mermaid_labels(source)
            diagrams.append(MermaidDiagram(
                md_path=md_path,
                line=block_start,
                source=source,
                node_labels=labels,
            ))
            in_block = False
            continue
        if in_block:
            block_lines.append(line)

    return diagrams


def _extract_mermaid_labels(source: str) -> list[str]:
    """Extract human-readable labels from Mermaid diagram syntax.

    Handles common patterns:
    - A[Label Text]
    - A(Label Text)
    - A{Label Text}
    - A([Label Text])
    - A[[Label Text]]
    - A -->|edge label| B
    - A -- edge label --> B
    """
    labels: list[str] = []

    # Node labels in brackets/parens/braces (including doubled variants)
    for m in re.finditer(
        r'(?:^|\s)\w+\s*[\[\(\{]{1,2}([^\]\)\}]+?)[\]\)\}]{1,2}',
        source,
    ):
        label = m.group(1).strip()
        if label and not label.startswith("fa:"):
            labels.append(label)

    return labels


def find_diagram_embeddings(paths: list[str]) -> list[DiagramEmbedding]:
    """Scan markdown files for iframe diagram embeddings."""
    embeddings: list[DiagramEmbedding] = []

    for path_str in paths:
        p = Path(path_str)
        md_files = [p] if p.is_file() and p.suffix.lower() == ".md" else []
        if p.is_dir():
            md_files = sorted(p.rglob("*.md"))

        for md_file in md_files:
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()

            for i, line in enumerate(lines, start=1):
                match = re.search(
                    r'<iframe\s+[^>]*src=["\']([^"\']+\.html)["\']',
                    line,
                    re.IGNORECASE,
                )
                if not match:
                    continue

                src = match.group(1)
                diagram_path = (md_file.parent / src).resolve()
                if not diagram_path.exists():
                    # Try from docs root
                    for parent in md_file.parents:
                        candidate = parent / src.lstrip("./")
                        if candidate.exists():
                            diagram_path = candidate.resolve()
                            break

                embeddings.append(DiagramEmbedding(
                    md_path=md_file,
                    diagram_path=diagram_path,
                    iframe_line=i,
                    context_text=content,
                ))

    return embeddings


# ---------------------------------------------------------------------------
# Metric normalization
# ---------------------------------------------------------------------------

def _normalize_metric(text: str) -> str:
    """Normalize metric text for comparison.

    "12K" -> "12000", "12,000" -> "12000", "8.5K" -> "8500",
    "2.1M" -> "2100000", etc.
    """
    t = text.strip().lower().replace(",", "")
    # Handle K/M/B suffixes
    m = re.match(r'^([\d.]+)\s*k\b', t)
    if m:
        return str(int(float(m.group(1)) * 1_000))
    m = re.match(r'^([\d.]+)\s*m\b', t)
    if m:
        return str(int(float(m.group(1)) * 1_000_000))
    m = re.match(r'^([\d.]+)\s*b\b', t)
    if m:
        return str(int(float(m.group(1)) * 1_000_000_000))
    # Strip non-digit for pure number comparison
    digits_only = re.sub(r'[^\d]', '', t)
    return digits_only if digits_only else t


def _metric_matches(diagram_metric: str, doc_text: str) -> bool:
    """Check if a diagram metric value appears in the document text."""
    norm = _normalize_metric(diagram_metric)
    if not norm:
        return True  # empty metric is OK

    doc_lower = doc_text.lower().replace(",", "")

    # Direct substring match
    if diagram_metric.lower() in doc_lower:
        return True

    # Normalized number match: find all numbers in doc (with optional commas/suffixes)
    doc_numbers = set()
    for m in re.finditer(r'[\d][,\d]*\.?\d*\s*[kKmMbB]?', doc_text):
        doc_numbers.add(_normalize_metric(m.group(0)))

    return norm in doc_numbers


# ---------------------------------------------------------------------------
# Level 1: Structural integrity (diagram HTML alone)
# ---------------------------------------------------------------------------

def validate_structure(info: DiagramInfo) -> list[ValidationIssue]:
    """Level 1: Validate diagram structural integrity."""
    issues: list[ValidationIssue] = []
    path = info.path

    # Collect all data-ids from HTML
    html_ids = [c.data_id for c in info.components]
    html_id_set = set(html_ids)
    desc_keys = set(info.descriptions.keys())

    # Check for duplicate data-id values
    seen: set[str] = set()
    for cid in html_ids:
        if cid in seen:
            issues.append(ValidationIssue(
                path=path, line=0, level="error",
                check="L1:duplicate-data-id",
                message=f"Duplicate data-id '{cid}' in HTML",
            ))
        seen.add(cid)

    # Every data-id must have matching key in descriptions
    for cid in html_id_set:
        if cid not in desc_keys:
            issues.append(ValidationIssue(
                path=path, line=0, level="error",
                check="L1:data-id-no-description",
                message=f"data-id '{cid}' has no matching key in descriptions object",
            ))

    # Every descriptions key must have matching data-id
    for key in desc_keys:
        if key not in html_id_set:
            issues.append(ValidationIssue(
                path=path, line=0, level="error",
                check="L1:description-no-data-id",
                message=f"descriptions key '{key}' has no matching data-id in HTML",
            ))

    # Component .name must match descriptions[id].title
    # Allow HTML name to be a substring of the title (short display name vs full title)
    for comp in info.components:
        desc = info.descriptions.get(comp.data_id)
        if desc and "title" in desc:
            html_name = comp.name.strip()
            desc_title = desc["title"].strip()
            name_low = html_name.lower()
            title_low = desc_title.lower()
            # Check: exact match, substring, or acronym match
            name_is_acronym = (
                name_low.replace(" ", "").isalpha()
                and len(name_low.split()) == 1
                and len(name_low) <= 5
                and name_low == "".join(
                    w[0] for w in desc_title.split() if w[0].isupper()
                ).lower()
            )
            # Also allow: every word in HTML name appears in desc title
            name_words = set(name_low.split())
            title_words_set = set(title_low.split())
            name_words_in_title = name_words.issubset(title_words_set)
            if (name_low != title_low
                    and name_low not in title_low
                    and not name_is_acronym
                    and not name_words_in_title):
                issues.append(ValidationIssue(
                    path=path, line=0, level="error",
                    check="L1:name-title-mismatch",
                    message=(
                        f"Component '{comp.data_id}': HTML name '{html_name}' "
                        f"not found in descriptions title '{desc_title}'"
                    ),
                ))

    # Each description must have 2+ sentences
    for key, desc in info.descriptions.items():
        desc_text = desc.get("desc", "")
        sentences = [s.strip() for s in re.split(r'[.!?]+', desc_text) if s.strip()]
        if len(sentences) < 2:
            issues.append(ValidationIssue(
                path=path, line=0, level="warning",
                check="L1:short-description",
                message=f"descriptions['{key}'].desc has {len(sentences)} sentence(s), need 2+",
            ))

    # Each component must have 3+ tags
    for key, desc in info.descriptions.items():
        tags = desc.get("tags", [])
        if len(tags) < 3:
            issues.append(ValidationIssue(
                path=path, line=0, level="warning",
                check="L1:few-tags",
                message=f"descriptions['{key}'] has {len(tags)} tag(s), need 3+",
            ))

    # syncTheme() must be present
    if not info.has_sync_theme:
        issues.append(ValidationIssue(
            path=path, line=0, level="error",
            check="L1:missing-sync-theme",
            message="syncTheme() function not found in diagram",
        ))

    # CSS theme variables must be present
    if not info.has_css_variables:
        issues.append(ValidationIssue(
            path=path, line=0, level="error",
            check="L1:missing-css-variables",
            message="Required CSS variables (--bg, --surface, --border, --text, --accent) not found",
        ))

    return issues


# ---------------------------------------------------------------------------
# Level 2: Document-diagram consistency
# ---------------------------------------------------------------------------

def validate_consistency(
    info: DiagramInfo,
    embedding: DiagramEmbedding,
) -> list[ValidationIssue]:
    """Level 2: Validate diagram content against embedding document."""
    issues: list[ValidationIssue] = []
    doc_text = embedding.context_text
    doc_lower = doc_text.lower()

    # Check component/layer count claims in document
    # Pattern: "N components across M layers"
    count_match = re.search(
        r'(\d+)\s+components?\s+across\s+(\d+)\s+layers?',
        doc_text,
        re.IGNORECASE,
    )
    if count_match:
        claimed_components = int(count_match.group(1))
        claimed_layers = int(count_match.group(2))
        actual_components = len(info.components)
        actual_layers = len(info.layers)

        if claimed_components != actual_components:
            issues.append(ValidationIssue(
                path=embedding.md_path,
                line=embedding.iframe_line,
                level="error",
                check="L2:component-count-mismatch",
                message=(
                    f"Document claims {claimed_components} components but "
                    f"diagram has {actual_components}"
                ),
            ))
        if claimed_layers != actual_layers:
            issues.append(ValidationIssue(
                path=embedding.md_path,
                line=embedding.iframe_line,
                level="error",
                check="L2:layer-count-mismatch",
                message=(
                    f"Document claims {claimed_layers} layers but "
                    f"diagram has {actual_layers}"
                ),
            ))

    # Component names should appear in the document text
    for comp in info.components:
        name_lower = comp.name.strip().lower()
        if name_lower and name_lower not in doc_lower:
            issues.append(ValidationIssue(
                path=embedding.md_path,
                line=embedding.iframe_line,
                level="warning",
                check="L2:component-name-missing-in-doc",
                message=f"Component '{comp.name}' not mentioned in document text",
            ))

    # Metrics from diagram should appear in document
    for comp in info.components:
        metric = comp.metric.strip()
        if metric and not _metric_matches(metric, doc_text):
            issues.append(ValidationIssue(
                path=embedding.md_path,
                line=embedding.iframe_line,
                level="warning",
                check="L2:metric-missing-in-doc",
                message=(
                    f"Component '{comp.name}' metric '{metric}' "
                    f"not found in document text"
                ),
            ))

    # At least 50% of technology tags should appear in document
    all_tags: list[str] = []
    for desc in info.descriptions.values():
        all_tags.extend(desc.get("tags", []))
    if all_tags:
        found = sum(1 for tag in all_tags if tag.lower() in doc_lower)
        ratio = found / len(all_tags)
        if ratio < 0.5:
            issues.append(ValidationIssue(
                path=embedding.md_path,
                line=embedding.iframe_line,
                level="warning",
                check="L2:low-tag-overlap",
                message=(
                    f"Only {found}/{len(all_tags)} ({ratio:.0%}) technology tags "
                    f"from diagram appear in document (need 50%+)"
                ),
            ))

    # Diagram title words should overlap with document title
    if info.title:
        title_words = set(
            w.lower() for w in re.findall(r'\w+', info.title)
            if len(w) > 3
        )
        if title_words:
            # Extract doc title from frontmatter or first H1
            doc_title = ""
            title_match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', doc_text, re.MULTILINE)
            if title_match:
                doc_title = title_match.group(1)
            if not doc_title:
                h1_match = re.search(r'^#\s+(.+)$', doc_text, re.MULTILINE)
                if h1_match:
                    doc_title = h1_match.group(1)

            if doc_title:
                doc_title_words = set(
                    w.lower() for w in re.findall(r'\w+', doc_title)
                    if len(w) > 3
                )
                overlap = title_words & doc_title_words
                if not overlap:
                    issues.append(ValidationIssue(
                        path=embedding.md_path,
                        line=embedding.iframe_line,
                        level="warning",
                        check="L2:title-mismatch",
                        message=(
                            f"Diagram title '{info.title}' has no word overlap "
                            f"with document title '{doc_title}'"
                        ),
                    ))

    return issues


# ---------------------------------------------------------------------------
# Level 2b: Mermaid diagram vs document consistency
# ---------------------------------------------------------------------------

def validate_mermaid_consistency(
    diagram: MermaidDiagram,
    doc_text: str,
) -> list[ValidationIssue]:
    """Validate Mermaid diagram labels against the surrounding document."""
    issues: list[ValidationIssue] = []
    doc_lower = doc_text.lower()

    # Check that node labels appear in document text
    missing = []
    for label in diagram.node_labels:
        label_lower = label.strip().lower()
        # Skip very short labels (A, B, etc.) or formatting
        if len(label_lower) <= 2:
            continue
        if label_lower not in doc_lower:
            missing.append(label)

    if missing and len(missing) > len(diagram.node_labels) * 0.5:
        issues.append(ValidationIssue(
            path=diagram.md_path,
            line=diagram.line,
            level="warning",
            check="L2:mermaid-labels-missing-in-doc",
            message=(
                f"Mermaid diagram has {len(missing)}/{len(diagram.node_labels)} "
                f"labels not found in document: {', '.join(missing[:5])}"
            ),
        ))

    return issues


# ---------------------------------------------------------------------------
# Level 3: Semantic coherence
# ---------------------------------------------------------------------------

def validate_semantics(info: DiagramInfo) -> list[ValidationIssue]:
    """Level 3: Validate semantic coherence within diagram."""
    issues: list[ValidationIssue] = []
    path = info.path

    # Check for duplicate data-ids (also L1 but critical)
    ids = [c.data_id for c in info.components]
    seen: set[str] = set()
    for cid in ids:
        if cid in seen:
            issues.append(ValidationIssue(
                path=path, line=0, level="error",
                check="L3:duplicate-data-id",
                message=f"Duplicate data-id '{cid}'",
            ))
        seen.add(cid)

    # No orphan components: each component's description should mention
    # at least one component from an adjacent layer
    layers_order = info.layers
    layer_components: dict[str, list[str]] = {}
    for comp in info.components:
        layer_components.setdefault(comp.layer, []).append(comp.data_id)

    for comp in info.components:
        desc_data = info.descriptions.get(comp.data_id)
        if not desc_data:
            continue
        desc_text = (desc_data.get("desc", "") + " " +
                     " ".join(desc_data.get("tags", []))).lower()

        comp_layer_idx = layers_order.index(comp.layer) if comp.layer in layers_order else -1
        if comp_layer_idx < 0:
            continue

        # Gather names of components in adjacent layers
        adjacent_names: list[str] = []
        for offset in (-1, 1):
            adj_idx = comp_layer_idx + offset
            if 0 <= adj_idx < len(layers_order):
                adj_layer = layers_order[adj_idx]
                for adj_id in layer_components.get(adj_layer, []):
                    adj_desc = info.descriptions.get(adj_id, {})
                    adj_title = adj_desc.get("title", "")
                    if adj_title:
                        adjacent_names.append(adj_title.lower())
                    # Also try component name from HTML
                    for c2 in info.components:
                        if c2.data_id == adj_id and c2.name:
                            adjacent_names.append(c2.name.lower())

        if not adjacent_names:
            continue  # edge layer with no adjacent layer (top or bottom)

        # Also gather adjacent layer names themselves
        adjacent_layer_names: list[str] = []
        for offset in (-1, 1):
            adj_idx = comp_layer_idx + offset
            if 0 <= adj_idx < len(layers_order):
                adjacent_layer_names.append(layers_order[adj_idx].lower())

        # Check if description mentions any adjacent component or layer
        mentions_adjacent = any(
            name in desc_text
            for name in adjacent_names
        )
        if not mentions_adjacent:
            # Check if any significant word from adjacent names (>3 chars) appears
            adj_words = set()
            for name in adjacent_names:
                adj_words.update(w for w in name.split() if len(w) > 3)
            mentions_adjacent = any(w in desc_text for w in adj_words)
        if not mentions_adjacent:
            # Check if adjacent layer name appears
            mentions_adjacent = any(
                layer_name in desc_text
                for layer_name in adjacent_layer_names
            )

        if not mentions_adjacent:
            issues.append(ValidationIssue(
                path=path, line=0, level="warning",
                check="L3:orphan-component",
                message=(
                    f"Component '{comp.data_id}' ({comp.name}) description "
                    f"does not mention any adjacent-layer component"
                ),
            ))

    return issues


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def validate_diagrams(paths: list[str], strict: bool = False) -> int:
    """Run all validation checks and return exit code (0=pass, 1=fail)."""
    all_issues: list[ValidationIssue] = []
    diagrams_checked = 0
    mermaid_checked = 0

    # Find all diagram HTML files
    html_files: list[Path] = []
    for path_str in paths:
        p = Path(path_str)
        if p.is_file() and p.suffix.lower() == ".html":
            html_files.append(p)
        elif p.is_dir():
            html_files.extend(sorted(p.rglob("*.html")))

    # Filter to actual diagram files (must have data-id attributes)
    diagram_infos: dict[Path, DiagramInfo] = {}
    for html_path in html_files:
        try:
            content = html_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if 'data-id=' not in content:
            continue
        info = parse_diagram_html(html_path)
        if info.components:
            diagram_infos[html_path.resolve()] = info

    # L1 + L3: structural + semantic for each diagram
    for info in diagram_infos.values():
        diagrams_checked += 1
        all_issues.extend(validate_structure(info))
        all_issues.extend(validate_semantics(info))

    # Find embeddings and run L2
    embeddings = find_diagram_embeddings(paths)
    for emb in embeddings:
        resolved = emb.diagram_path.resolve() if emb.diagram_path.exists() else None
        if resolved and resolved in diagram_infos:
            all_issues.extend(validate_consistency(diagram_infos[resolved], emb))

    # Find and validate Mermaid diagrams in markdown
    for path_str in paths:
        p = Path(path_str)
        md_files = [p] if p.is_file() and p.suffix.lower() == ".md" else []
        if p.is_dir():
            md_files = sorted(p.rglob("*.md"))

        for md_file in md_files:
            try:
                content = md_file.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            mermaid_blocks = _extract_mermaid_blocks(md_file, content)
            for mblock in mermaid_blocks:
                mermaid_checked += 1
                all_issues.extend(validate_mermaid_consistency(mblock, content))

    # Report results
    errors = [i for i in all_issues if i.level == "error"]
    warnings = [i for i in all_issues if i.level == "warning"]

    print(f"\nDiagram content validation: {diagrams_checked} HTML diagram(s), "
          f"{mermaid_checked} Mermaid diagram(s) checked")
    print("=" * 60)

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for issue in errors:
            print(f"  {issue.path}:{issue.line} [{issue.check}]")
            print(f"    {issue.message}")

    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for issue in warnings:
            print(f"  {issue.path}:{issue.line} [{issue.check}]")
            print(f"    {issue.message}")

    total = diagrams_checked + mermaid_checked
    print(f"\nSummary: {len(errors)} error(s), {len(warnings)} warning(s) "
          f"across {total} diagram(s)")

    if errors:
        return 1
    if strict and warnings:
        return 1
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate interactive diagrams and Mermaid diagrams against document content",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Directories or files to scan for diagrams and markdown",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    args = parser.parse_args()

    return validate_diagrams(args.paths, strict=args.strict)


if __name__ == "__main__":
    raise SystemExit(main())

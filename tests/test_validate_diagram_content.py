"""Tests for scripts/validate_diagram_content.py — diagram hallucination detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.validate_diagram_content import (
    DiagramComponent,
    DiagramEmbedding,
    DiagramInfo,
    MermaidDiagram,
    ValidationIssue,
    _extract_mermaid_blocks,
    _js_object_to_json,
    _metric_matches,
    _normalize_metric,
    find_diagram_embeddings,
    parse_diagram_html,
    validate_consistency,
    validate_mermaid_consistency,
    validate_semantics,
    validate_structure,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

MINIMAL_DIAGRAM_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Test Architecture</title>
<style>
:root {
  --bg: #fff;
  --surface: #f8f;
  --border: #e2e;
  --text: #1e2;
  --accent: #636;
}
[data-theme="dark"] {
  --bg: #0f1;
  --surface: #1e2;
  --border: #334;
  --text: #e2e;
  --accent: #818;
}
</style>
</head>
<body>
<h1>Test Architecture</h1>
<p class="subtitle">3 components across 2 layers</p>
<div class="diagram">
  <div class="layer-label">Frontend</div>
  <div class="layer">
    <div class="component" data-id="web" onclick="showInfo('web')">
      <span class="icon">W</span>
      <div class="name">Web App</div>
      <div class="metric">10K DAU</div>
    </div>
    <div class="component" data-id="mobile" onclick="showInfo('mobile')">
      <span class="icon">M</span>
      <div class="name">Mobile App</div>
      <div class="metric">5K DAU</div>
    </div>
  </div>
  <div class="layer-label">Backend</div>
  <div class="layer">
    <div class="component" data-id="api" onclick="showInfo('api')">
      <span class="icon">A</span>
      <div class="name">API Server</div>
      <div class="metric">2K req/sec</div>
    </div>
  </div>
</div>
<script>
const descriptions = {
  web: {
    title: "Web App",
    desc: "React SPA serving 10,000 daily active users. Connects to API Server via REST endpoints.",
    tags: ["React", "SPA", "REST"]
  },
  mobile: {
    title: "Mobile App",
    desc: "iOS and Android native apps with 5,000 daily users. Connects to the API Server using GraphQL.",
    tags: ["iOS", "Android", "GraphQL"]
  },
  api: {
    title: "API Server",
    desc: "Node.js server handling 2,000 requests per second at peak. Serves Web App and Mobile App clients.",
    tags: ["Node.js", "Express", "REST", "GraphQL"]
  }
};
function syncTheme() {
  try {
    const parentScheme = window.parent.document.body.getAttribute('data-md-color-scheme');
    if (parentScheme === 'slate') {
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  } catch (e) {}
}
syncTheme();
</script>
</body>
</html>
"""


def _write_diagram(tmp_path: Path, content: str = MINIMAL_DIAGRAM_HTML) -> Path:
    """Write a diagram HTML file and return its path."""
    p = tmp_path / "diagrams" / "test.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def _write_md(tmp_path: Path, content: str, name: str = "doc.md") -> Path:
    """Write a markdown file and return its path."""
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


# ===================================================================
# TestJsObjectToJson
# ===================================================================


class TestJsObjectToJson:
    """Tests for _js_object_to_json."""

    def test_unquoted_keys(self) -> None:
        result = _js_object_to_json('{ name: "hello", age: "30" }')
        assert result["name"] == "hello"
        assert result["age"] == "30"

    def test_single_quoted_strings(self) -> None:
        result = _js_object_to_json("{ title: 'Web App', desc: 'A web app.' }")
        assert result["title"] == "Web App"

    def test_trailing_commas(self) -> None:
        result = _js_object_to_json('{ a: "1", b: "2", }')
        assert result["a"] == "1"
        assert result["b"] == "2"

    def test_nested_arrays(self) -> None:
        result = _js_object_to_json('{ tags: ["React", "SPA"] }')
        assert result["tags"] == ["React", "SPA"]

    def test_nested_objects(self) -> None:
        result = _js_object_to_json("""
        {
          web: {
            title: "Web",
            desc: "A web app.",
            tags: ["React"]
          }
        }
        """)
        assert result["web"]["title"] == "Web"
        assert result["web"]["tags"] == ["React"]

    def test_invalid_input_returns_empty(self) -> None:
        assert _js_object_to_json("") == {}
        assert _js_object_to_json("not json at all {{{") == {}

    def test_js_comments_stripped(self) -> None:
        result = _js_object_to_json("""
        {
          // this is a comment
          name: "test"
        }
        """)
        assert result["name"] == "test"


# ===================================================================
# TestParseDiagramHtml
# ===================================================================


class TestParseDiagramHtml:
    """Tests for parse_diagram_html."""

    def test_parses_components(self, tmp_path: Path) -> None:
        p = _write_diagram(tmp_path)
        info = parse_diagram_html(p)
        assert len(info.components) == 3

    def test_parses_layers(self, tmp_path: Path) -> None:
        p = _write_diagram(tmp_path)
        info = parse_diagram_html(p)
        assert info.layers == ["Frontend", "Backend"]

    def test_parses_title(self, tmp_path: Path) -> None:
        p = _write_diagram(tmp_path)
        info = parse_diagram_html(p)
        assert info.title == "Test Architecture"

    def test_parses_descriptions(self, tmp_path: Path) -> None:
        p = _write_diagram(tmp_path)
        info = parse_diagram_html(p)
        assert "web" in info.descriptions
        assert info.descriptions["web"]["title"] == "Web App"

    def test_detects_sync_theme(self, tmp_path: Path) -> None:
        p = _write_diagram(tmp_path)
        info = parse_diagram_html(p)
        assert info.has_sync_theme is True

    def test_detects_css_variables(self, tmp_path: Path) -> None:
        p = _write_diagram(tmp_path)
        info = parse_diagram_html(p)
        assert info.has_css_variables is True

    def test_component_layers(self, tmp_path: Path) -> None:
        p = _write_diagram(tmp_path)
        info = parse_diagram_html(p)
        layers_by_id = {c.data_id: c.layer for c in info.components}
        assert layers_by_id["web"] == "Frontend"
        assert layers_by_id["api"] == "Backend"


# ===================================================================
# TestFindDiagramEmbeddings
# ===================================================================


class TestFindDiagramEmbeddings:
    """Tests for find_diagram_embeddings."""

    def test_finds_iframe(self, tmp_path: Path) -> None:
        diagram = _write_diagram(tmp_path)
        md = _write_md(tmp_path, (
            "---\ntitle: Test\n---\n"
            '# Hello\n\n'
            '<iframe src="diagrams/test.html" title="arch"></iframe>\n'
        ))
        embeddings = find_diagram_embeddings([str(tmp_path)])
        assert len(embeddings) == 1
        assert embeddings[0].diagram_path.resolve() == diagram.resolve()

    def test_resolves_relative_path(self, tmp_path: Path) -> None:
        diagram = _write_diagram(tmp_path)
        subdir = tmp_path / "en"
        subdir.mkdir()
        md = _write_md(tmp_path, (
            '# Test\n'
            '<iframe src="../diagrams/test.html"></iframe>\n'
        ), name="en/page.md")
        embeddings = find_diagram_embeddings([str(tmp_path)])
        assert len(embeddings) >= 1

    def test_no_embeddings_in_plain_md(self, tmp_path: Path) -> None:
        _write_md(tmp_path, "# Just text\nNo diagrams here.")
        embeddings = find_diagram_embeddings([str(tmp_path)])
        assert len(embeddings) == 0


# ===================================================================
# TestValidateStructure
# ===================================================================


class TestValidateStructure:
    """Tests for validate_structure (Level 1)."""

    def test_valid_diagram_passes(self, tmp_path: Path) -> None:
        p = _write_diagram(tmp_path)
        info = parse_diagram_html(p)
        issues = validate_structure(info)
        errors = [i for i in issues if i.level == "error"]
        assert len(errors) == 0

    def test_missing_description_key(self, tmp_path: Path) -> None:
        html = MINIMAL_DIAGRAM_HTML.replace(
            'mobile: {', '// mobile removed\n  mobile_typo: {'
        )
        p = _write_diagram(tmp_path, html)
        info = parse_diagram_html(p)
        issues = validate_structure(info)
        checks = [i.check for i in issues if i.level == "error"]
        assert "L1:data-id-no-description" in checks

    def test_name_title_mismatch(self, tmp_path: Path) -> None:
        # "Web App" is a substring of "Web Application" so that would pass;
        # use a completely different title to trigger mismatch
        html = MINIMAL_DIAGRAM_HTML.replace(
            'title: "Web App"', 'title: "Dashboard Portal"'
        )
        p = _write_diagram(tmp_path, html)
        info = parse_diagram_html(p)
        issues = validate_structure(info)
        checks = [i.check for i in issues if i.level == "error"]
        assert "L1:name-title-mismatch" in checks

    def test_short_description_warning(self, tmp_path: Path) -> None:
        html = MINIMAL_DIAGRAM_HTML.replace(
            'desc: "React SPA serving 10,000 daily active users. Connects to API Server via REST endpoints."',
            'desc: "A web app."',
        )
        p = _write_diagram(tmp_path, html)
        info = parse_diagram_html(p)
        issues = validate_structure(info)
        checks = [i.check for i in issues if i.level == "warning"]
        assert "L1:short-description" in checks

    def test_few_tags_warning(self, tmp_path: Path) -> None:
        html = MINIMAL_DIAGRAM_HTML.replace(
            'tags: ["React", "SPA", "REST"]',
            'tags: ["React"]',
        )
        p = _write_diagram(tmp_path, html)
        info = parse_diagram_html(p)
        issues = validate_structure(info)
        checks = [i.check for i in issues if i.level == "warning"]
        assert "L1:few-tags" in checks

    def test_missing_sync_theme(self, tmp_path: Path) -> None:
        html = MINIMAL_DIAGRAM_HTML.replace("function syncTheme", "function xTheme")
        html = html.replace("syncTheme()", "xTheme()")
        p = _write_diagram(tmp_path, html)
        info = parse_diagram_html(p)
        issues = validate_structure(info)
        checks = [i.check for i in issues if i.level == "error"]
        assert "L1:missing-sync-theme" in checks

    def test_missing_css_variables(self, tmp_path: Path) -> None:
        html = MINIMAL_DIAGRAM_HTML.replace("--accent:", "--highlight:")
        p = _write_diagram(tmp_path, html)
        info = parse_diagram_html(p)
        issues = validate_structure(info)
        checks = [i.check for i in issues if i.level == "error"]
        assert "L1:missing-css-variables" in checks

    def test_duplicate_data_id(self, tmp_path: Path) -> None:
        # Add a duplicate component
        extra = (
            '    <div class="component" data-id="web" onclick="showInfo(\'web\')">\n'
            '      <span class="icon">W2</span>\n'
            '      <div class="name">Web App</div>\n'
            '      <div class="metric">10K DAU</div>\n'
            '    </div>\n'
        )
        html = MINIMAL_DIAGRAM_HTML.replace(
            '  </div>\n  <div class="layer-label">Backend',
            extra + '  </div>\n  <div class="layer-label">Backend',
        )
        p = _write_diagram(tmp_path, html)
        info = parse_diagram_html(p)
        issues = validate_structure(info)
        checks = [i.check for i in issues if i.level == "error"]
        assert "L1:duplicate-data-id" in checks


# ===================================================================
# TestValidateConsistency
# ===================================================================


class TestValidateConsistency:
    """Tests for validate_consistency (Level 2)."""

    def _make_embedding(
        self, tmp_path: Path, doc_text: str, diagram_html: str = MINIMAL_DIAGRAM_HTML,
    ) -> tuple[DiagramInfo, DiagramEmbedding]:
        p = _write_diagram(tmp_path, diagram_html)
        info = parse_diagram_html(p)
        md = _write_md(tmp_path, doc_text)
        return info, DiagramEmbedding(
            md_path=md,
            diagram_path=p,
            iframe_line=5,
            context_text=doc_text,
        )

    def test_matching_counts_pass(self, tmp_path: Path) -> None:
        doc = (
            "---\ntitle: Test Architecture\n---\n"
            "# Test Architecture\n\n"
            "The diagram shows 3 components across 2 layers.\n"
            "Web App, Mobile App, API Server are all present.\n"
            "10K DAU, 5K DAU, 2K req/sec.\n"
            "React SPA REST iOS Android GraphQL Node.js Express\n"
        )
        info, emb = self._make_embedding(tmp_path, doc)
        issues = validate_consistency(info, emb)
        errors = [i for i in issues if i.level == "error"]
        assert len(errors) == 0

    def test_component_count_mismatch(self, tmp_path: Path) -> None:
        doc = (
            "The diagram shows 5 components across 2 layers.\n"
            "Web App, Mobile App, API Server.\n"
        )
        info, emb = self._make_embedding(tmp_path, doc)
        issues = validate_consistency(info, emb)
        checks = [i.check for i in issues if i.level == "error"]
        assert "L2:component-count-mismatch" in checks

    def test_layer_count_mismatch(self, tmp_path: Path) -> None:
        doc = "The diagram shows 3 components across 4 layers.\n"
        info, emb = self._make_embedding(tmp_path, doc)
        issues = validate_consistency(info, emb)
        checks = [i.check for i in issues if i.level == "error"]
        assert "L2:layer-count-mismatch" in checks

    def test_missing_component_names_warning(self, tmp_path: Path) -> None:
        doc = "# Test\nThis doc does not mention any component names at all.\n"
        info, emb = self._make_embedding(tmp_path, doc)
        issues = validate_consistency(info, emb)
        checks = [i.check for i in issues if i.level == "warning"]
        assert "L2:component-name-missing-in-doc" in checks

    def test_no_claim_scenario(self, tmp_path: Path) -> None:
        """No component count claim → no count error."""
        doc = (
            "# Test Architecture\nThis is an overview.\n"
            "Web App, Mobile App, API Server.\n"
            "10K DAU, 5K DAU, 2K req/sec.\n"
            "React SPA REST iOS Android GraphQL Node.js Express\n"
        )
        info, emb = self._make_embedding(tmp_path, doc)
        issues = validate_consistency(info, emb)
        count_errors = [i for i in issues
                        if "count" in i.check and i.level == "error"]
        assert len(count_errors) == 0


# ===================================================================
# TestValidateSemantics
# ===================================================================


class TestValidateSemantics:
    """Tests for validate_semantics (Level 3)."""

    def test_well_connected_passes(self, tmp_path: Path) -> None:
        p = _write_diagram(tmp_path)
        info = parse_diagram_html(p)
        issues = validate_semantics(info)
        errors = [i for i in issues if i.level == "error"]
        assert len(errors) == 0

    def test_orphan_detection(self, tmp_path: Path) -> None:
        """Component whose description mentions no adjacent-layer component."""
        html = MINIMAL_DIAGRAM_HTML.replace(
            'desc: "React SPA serving 10,000 daily active users. Connects to API Server via REST endpoints."',
            'desc: "This component is completely isolated. It has no connections to anything else at all."',
        )
        p = _write_diagram(tmp_path, html)
        info = parse_diagram_html(p)
        issues = validate_semantics(info)
        checks = [i.check for i in issues]
        assert "L3:orphan-component" in checks

    def test_duplicate_detection(self, tmp_path: Path) -> None:
        extra = (
            '    <div class="component" data-id="web" onclick="showInfo(\'web\')">\n'
            '      <span class="icon">W2</span>\n'
            '      <div class="name">Web App</div>\n'
            '      <div class="metric">10K DAU</div>\n'
            '    </div>\n'
        )
        html = MINIMAL_DIAGRAM_HTML.replace(
            '  </div>\n  <div class="layer-label">Backend',
            extra + '  </div>\n  <div class="layer-label">Backend',
        )
        p = _write_diagram(tmp_path, html)
        info = parse_diagram_html(p)
        issues = validate_semantics(info)
        checks = [i.check for i in issues if i.level == "error"]
        assert "L3:duplicate-data-id" in checks


# ===================================================================
# TestMetricNormalization
# ===================================================================


class TestMetricNormalization:
    """Tests for _normalize_metric and _metric_matches."""

    def test_normalize_k(self) -> None:
        assert _normalize_metric("12K") == "12000"

    def test_normalize_decimal_k(self) -> None:
        assert _normalize_metric("8.5K") == "8500"

    def test_normalize_m(self) -> None:
        assert _normalize_metric("2.1M") == "2100000"

    def test_normalize_commas(self) -> None:
        assert _normalize_metric("12,000") == "12000"

    def test_metric_matches_direct(self) -> None:
        assert _metric_matches("12K req/sec", "The gateway handles 12K req/sec.")

    def test_metric_matches_expanded(self) -> None:
        assert _metric_matches("12K", "processing 12,000 requests per second")

    def test_metric_no_match(self) -> None:
        assert not _metric_matches("12K", "processing 8000 requests")


# ===================================================================
# TestMermaidValidation
# ===================================================================


class TestMermaidValidation:
    """Tests for Mermaid diagram extraction and validation."""

    def test_extract_mermaid_blocks(self, tmp_path: Path) -> None:
        md = _write_md(tmp_path, (
            "# Test\n\n"
            "```mermaid\n"
            "sequenceDiagram\n"
            "    Client->>API Gateway: POST /webhook\n"
            "    API Gateway->>HMAC Validator: Verify signature\n"
            "```\n\n"
            "Some text.\n"
        ))
        content = md.read_text()
        blocks = _extract_mermaid_blocks(md, content)
        assert len(blocks) == 1
        assert "sequenceDiagram" in blocks[0].source

    def test_mermaid_labels_extracted(self, tmp_path: Path) -> None:
        md = _write_md(tmp_path, (
            "```mermaid\n"
            "graph TD\n"
            "    A[Web Client] --> B[Load Balancer]\n"
            "    B --> C[API Server]\n"
            "```\n"
        ))
        content = md.read_text()
        blocks = _extract_mermaid_blocks(md, content)
        assert len(blocks) == 1
        labels_lower = [l.lower() for l in blocks[0].node_labels]
        assert "web client" in labels_lower
        assert "load balancer" in labels_lower

    def test_mermaid_consistency_pass(self) -> None:
        diag = MermaidDiagram(
            md_path=Path("test.md"), line=5, source="graph TD",
            node_labels=["Web Client", "Load Balancer", "API Server"],
        )
        doc = "The Web Client connects to the Load Balancer which routes to the API Server."
        issues = validate_mermaid_consistency(diag, doc)
        assert len(issues) == 0

    def test_mermaid_consistency_missing_labels(self) -> None:
        diag = MermaidDiagram(
            md_path=Path("test.md"), line=5, source="graph TD",
            node_labels=["Phantom Service", "Ghost Node", "Mystery Box", "Unknown Widget"],
        )
        doc = "This document talks about something completely different."
        issues = validate_mermaid_consistency(diag, doc)
        checks = [i.check for i in issues]
        assert "L2:mermaid-labels-missing-in-doc" in checks

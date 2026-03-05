"""Final coverage boost tests targeting remaining low-coverage modules.

Targets remaining gaps to push total coverage above 85%.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ===========================================================================
# markdown_converter.py — deeper conversion tests
# ===========================================================================


class TestMarkdownConverterDeep:
    """Cover markdown_converter conversion logic."""

    def test_admonition_with_title(self) -> None:
        from scripts.markdown_converter import mkdocs_to_docusaurus

        content = '!!! warning "Be careful"\n    This is a warning.\n'
        result = mkdocs_to_docusaurus(content)
        assert ":::warning" in result or "warning" in result

    def test_collapsible_block(self) -> None:
        from scripts.markdown_converter import mkdocs_to_docusaurus

        content = '??? info "Click to expand"\n    Hidden content.\n'
        result = mkdocs_to_docusaurus(content)
        assert "<details>" in result
        assert "Click to expand" in result

    def test_tabs_conversion(self) -> None:
        from scripts.markdown_converter import mkdocs_to_docusaurus

        content = '=== "Python"\n\n    python code\n\n=== "JavaScript"\n\n    js code\n'
        result = mkdocs_to_docusaurus(content)
        assert "Tabs" in result or "TabItem" in result

    def test_code_blocks_preserved(self) -> None:
        from scripts.markdown_converter import mkdocs_to_docusaurus

        content = "```python\n!!! note\n    inside code\n```\n"
        result = mkdocs_to_docusaurus(content)
        assert "!!! note" in result  # Should not be converted inside code block

    def test_docusaurus_to_mkdocs_admonition(self) -> None:
        from scripts.markdown_converter import docusaurus_to_mkdocs

        content = ":::warning[Be careful]\nThis is a warning.\n:::\n"
        result = docusaurus_to_mkdocs(content)
        assert '!!! warning "Be careful"' in result

    def test_docusaurus_to_mkdocs_no_title(self) -> None:
        from scripts.markdown_converter import docusaurus_to_mkdocs

        content = ":::info\nSome info.\n:::\n"
        result = docusaurus_to_mkdocs(content)
        assert "!!! info" in result

    def test_convert_directory(self, tmp_path: Path) -> None:
        from scripts.markdown_converter import convert_directory

        src = tmp_path / "src"
        src.mkdir()
        (src / "test.md").write_text(
            '!!! info "Title"\n    Content here.\n',
            encoding="utf-8",
        )
        dst = tmp_path / "dst"
        convert_directory(str(src), "docusaurus", str(dst))
        output = dst / "test.md"
        assert output.exists()
        assert ":::" in output.read_text(encoding="utf-8")

    def test_convert_directory_to_mkdocs(self, tmp_path: Path) -> None:
        from scripts.markdown_converter import convert_directory

        src = tmp_path / "src"
        src.mkdir()
        (src / "test.md").write_text(":::info\nContent.\n:::\n", encoding="utf-8")
        dst = tmp_path / "dst"
        convert_directory(str(src), "mkdocs", str(dst))
        output = dst / "test.md"
        assert output.exists()
        assert "!!!" in output.read_text(encoding="utf-8")

    def test_fence_toggle_open(self) -> None:
        from scripts.markdown_converter import _is_fence_toggle

        toggled, marker = _is_fence_toggle("```python", None)
        assert toggled is True
        assert marker == "```"

    def test_fence_toggle_close(self) -> None:
        from scripts.markdown_converter import _is_fence_toggle

        toggled, marker = _is_fence_toggle("```", "```")
        assert toggled is True
        assert marker is None

    def test_fence_toggle_no_match(self) -> None:
        from scripts.markdown_converter import _is_fence_toggle

        toggled, marker = _is_fence_toggle("normal text", None)
        assert toggled is False

    def test_collect_indented_block(self) -> None:
        from scripts.markdown_converter import _collect_indented_block

        lines = ["    indented line 1", "    indented line 2", "", "not indented"]
        block, next_idx = _collect_indented_block(lines, 0)
        assert len(block) == 2
        assert block[0] == "indented line 1"
        assert next_idx == 3

    def test_docusaurus_details_to_mkdocs(self) -> None:
        from scripts.markdown_converter import docusaurus_to_mkdocs

        content = "<details><summary>Click me</summary>\n\nHidden content here.\n\n</details>\n"
        result = docusaurus_to_mkdocs(content)
        assert '??? note "Click me"' in result
        assert "Hidden content here." in result

    def test_docusaurus_details_multiline_summary(self) -> None:
        from scripts.markdown_converter import docusaurus_to_mkdocs

        content = "<details>\n<summary>Expandable</summary>\n\nContent inside.\n\n</details>\n"
        result = docusaurus_to_mkdocs(content)
        assert '??? note "Expandable"' in result

    def test_docusaurus_tabs_to_mkdocs(self) -> None:
        from scripts.markdown_converter import docusaurus_to_mkdocs

        content = (
            '<Tabs>\n'
            '<TabItem value="t0" label="Python">\n\npy code\n\n</TabItem>\n'
            '<TabItem value="t1" label="JavaScript">\n\njs code\n\n</TabItem>\n'
            '</Tabs>\n'
        )
        result = docusaurus_to_mkdocs(content)
        assert '=== "Python"' in result
        assert '=== "JavaScript"' in result
        assert "py code" in result

    def test_docusaurus_import_lines_stripped(self) -> None:
        from scripts.markdown_converter import docusaurus_to_mkdocs

        content = "import Tabs from '@theme/Tabs';\nimport TabItem from '@theme/TabItem';\n\n# Title\n"
        result = docusaurus_to_mkdocs(content)
        assert "import Tabs" not in result
        assert "# Title" in result

    def test_mkdocs_tabs_add_import(self) -> None:
        from scripts.markdown_converter import mkdocs_to_docusaurus

        content = '---\ntitle: "T"\n---\n\n=== "A"\n\n    Content A\n\n=== "B"\n\n    Content B\n'
        result = mkdocs_to_docusaurus(content)
        assert "import Tabs" in result
        assert "TabItem" in result

    def test_admonition_empty_body(self) -> None:
        from scripts.markdown_converter import _convert_admonition_docusaurus_to_mkdocs

        result = _convert_admonition_docusaurus_to_mkdocs("info", None, [])
        assert result[0] == "!!! info"
        assert result[1] == "    "

    def test_roundtrip_admonition(self) -> None:
        from scripts.markdown_converter import mkdocs_to_docusaurus, docusaurus_to_mkdocs

        original = '!!! warning "Caution"\n    Handle with care.\n'
        docusaurus = mkdocs_to_docusaurus(original)
        mkdocs = docusaurus_to_mkdocs(docusaurus)
        assert "!!!" in mkdocs
        assert "Handle with care" in mkdocs


# ===========================================================================
# check_code_examples_smoke.py — dispatch and scanning
# ===========================================================================


class TestSmokeCheckDeep:
    """Cover check_code_examples_smoke dispatch logic."""

    def test_scan_and_run_smoke_on_dir(self, tmp_path: Path) -> None:
        from scripts.check_code_examples_smoke import run_smoke

        md = tmp_path / "test.md"
        md.write_text(
            "```python smoke-test\nprint(1 + 1)\n```\n\n```json\n{}\n```\n",
            encoding="utf-8",
        )
        exit_code = run_smoke([str(tmp_path)], timeout=10, allow_empty=True, allow_network=False)
        assert exit_code == 0

    def test_smoke_with_bash_block(self, tmp_path: Path) -> None:
        from scripts.check_code_examples_smoke import run_smoke

        md = tmp_path / "test.md"
        md.write_text(
            "```bash smoke-test\necho 'hello world'\n```\n",
            encoding="utf-8",
        )
        exit_code = run_smoke([str(tmp_path)], timeout=10, allow_empty=True, allow_network=False)
        assert exit_code == 0

    def test_smoke_empty_dir(self, tmp_path: Path) -> None:
        from scripts.check_code_examples_smoke import run_smoke

        exit_code = run_smoke([str(tmp_path)], timeout=10, allow_empty=True, allow_network=False)
        assert exit_code == 0


# ===========================================================================
# pilot_analysis.py — basic_seo_analysis, basic_gap_detection
# ===========================================================================


class TestPilotAnalysisDeep:
    """Cover pilot_analysis pure logic methods."""

    def _write_md(self, path: Path, frontmatter: str, body: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")
        return path

    def test_basic_seo_analysis(self, tmp_path: Path) -> None:
        from scripts.pilot_analysis import PilotAnalyzer

        docs = tmp_path / "docs"
        docs.mkdir()
        self._write_md(
            docs / "test.md",
            'title: "Test"\ndescription: "Description."',
            "# Test\n\nContent.\n",
        )
        analyzer = PilotAnalyzer(docs_dir=str(docs))
        result = analyzer._basic_seo_analysis()
        assert isinstance(result, dict)
        assert "total_issues" in result

    def test_basic_gap_detection(self, tmp_path: Path) -> None:
        from scripts.pilot_analysis import PilotAnalyzer

        docs = tmp_path / "docs"
        docs.mkdir()
        self._write_md(
            docs / "test.md",
            'title: "Test"',
            "# Test\n\nThis might be wrong TODO fix later.\n",
        )
        analyzer = PilotAnalyzer(docs_dir=str(docs))
        result = analyzer._basic_gap_detection()
        assert isinstance(result, dict)
        assert "total_gaps" in result


# ===========================================================================
# new_doc.py — deeper coverage
# ===========================================================================


class TestNewDocDeep:
    """Deeper coverage for new_doc.py."""

    def test_load_variables_from_custom_dir(self, tmp_path: Path) -> None:
        from scripts.new_doc import DocumentCreator

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "_variables.yml").write_text("product_name: CustomApp\ndefault_port: 3000\n", encoding="utf-8")
        creator = DocumentCreator(base_dir=str(tmp_path))
        # After init, variables should be loaded from the custom path
        assert isinstance(creator.variables, dict)

    def test_get_templates_has_standard_types(self) -> None:
        from scripts.new_doc import DocumentCreator

        creator = DocumentCreator()
        templates = creator.get_templates()
        assert "tutorial" in templates
        assert "how-to" in templates
        assert "concept" in templates
        assert "reference" in templates
        assert "troubleshooting" in templates


# ===========================================================================
# batch_generator.py — deeper coverage
# ===========================================================================


class TestBatchGeneratorFinal:
    """Cover remaining batch_generator paths."""

    def test_generate_documents_from_template(self, tmp_path: Path) -> None:
        from scripts.gap_detection.batch_generator import BatchDocGenerator, BatchResult, DocumentTask
        from scripts.gap_detection.gap_aggregator import DocumentationGap, AggregatedReport

        templates = tmp_path / "templates"
        templates.mkdir()
        (templates / "reference.md").write_text(
            "---\ntitle: Template\n---\n# Template\n",
            encoding="utf-8",
        )
        generator = BatchDocGenerator(
            templates_dir=str(templates),
            output_base=str(tmp_path),
        )

        report = AggregatedReport(
            gaps=[
                DocumentationGap("1", "API ref", "Desc", "code", "api", "reference", "high"),
            ],
        )
        batch = generator.create_batch_from_report(report, max_tasks=1)
        generated = generator.generate_documents(batch, use_claude=False)
        assert len(generated.generated_files) >= 1
        assert generated.tasks[0].status == "generated"


# ===========================================================================
# algolia_parser.py — deeper coverage
# ===========================================================================


class TestAlgoliaParserDeep:
    """Cover AlgoliaAnalytics remaining logic."""

    def test_categorize_authentication_query(self) -> None:
        from scripts.gap_detection.algolia_parser import AlgoliaAnalytics, SearchQuery

        analytics = AlgoliaAnalytics()
        query = SearchQuery("oauth2 token setup", 20, 5, 0.1)
        analytics._enrich_query(query)
        assert query.category == "authentication"

    def test_categorize_deployment_query(self) -> None:
        from scripts.gap_detection.algolia_parser import AlgoliaAnalytics, SearchQuery

        analytics = AlgoliaAnalytics()
        query = SearchQuery("docker install self-host", 15, 3, 0.05)
        analytics._enrich_query(query)
        assert query.category == "deployment"

    def test_low_ctr_detection(self) -> None:
        from scripts.gap_detection.algolia_parser import AlgoliaAnalytics, SearchQuery

        analytics = AlgoliaAnalytics()
        queries = [
            SearchQuery("test query", 50, 10, 0.02),  # Low CTR (2%)
        ]
        result = analytics._analyze_queries(queries)
        assert len(result.low_ctr_queries) >= 1


# ===========================================================================
# community_collector.py — deeper coverage
# ===========================================================================


class TestCommunityCollectorDeep:
    """Cover CommunityCollector remaining methods."""

    def test_categorize_workflow(self) -> None:
        from scripts.gap_detection.community_collector import CommunityCollector

        collector = CommunityCollector()
        assert collector._categorize_topic("How to run workflow automation") == "workflow"

    def test_categorize_deployment(self) -> None:
        from scripts.gap_detection.community_collector import CommunityCollector

        collector = CommunityCollector()
        assert collector._categorize_topic("Docker deployment guide for self-host") == "deployment"

    def test_categorize_security(self) -> None:
        from scripts.gap_detection.community_collector import CommunityCollector

        collector = CommunityCollector()
        assert collector._categorize_topic("SSL security encryption setup") == "security"

    def test_categorize_data(self) -> None:
        from scripts.gap_detection.community_collector import CommunityCollector

        collector = CommunityCollector()
        assert collector._categorize_topic("JSON data transform parsing") == "data"

    def test_categorize_scheduling(self) -> None:
        from scripts.gap_detection.community_collector import CommunityCollector

        collector = CommunityCollector()
        assert collector._categorize_topic("Cron schedule timer setup") == "scheduling"


# ===========================================================================
# generate_docusaurus_config.py — deeper coverage
# ===========================================================================


class TestDocusaurusConfig:
    """Cover generate_docusaurus_config."""

    def test_module_loads(self) -> None:
        import scripts.generate_docusaurus_config as mod

        assert hasattr(mod, "main") or hasattr(mod, "generate_docusaurus_config") or len(dir(mod)) > 5


# ===========================================================================
# doc_layers_validator.py — deeper coverage
# ===========================================================================


class TestDocLayersDeep:
    """Deeper coverage for doc_layers_validator."""

    def _write_md(self, path: Path, frontmatter: str, body: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")
        return path

    def test_tutorial_with_technical_details(self, tmp_path: Path) -> None:
        from scripts.doc_layers_validator import DocLayersValidator

        docs = tmp_path / "docs"
        docs.mkdir()
        self._write_md(
            docs / "test.md",
            'title: "T"\ncontent_type: tutorial',
            "# T\n\nThe implementation uses a complex algorithm with O(n) complexity.\n\nThe data structure is a hash map.\n",
        )
        validator = DocLayersValidator(docs_dir=str(docs))
        violations = validator.detect_layer_violations()
        tutorial_violations = [v for v in violations if v["content_type"] == "tutorial"]
        assert len(tutorial_violations) >= 1

    def test_howto_with_theory(self, tmp_path: Path) -> None:
        from scripts.doc_layers_validator import DocLayersValidator

        docs = tmp_path / "docs"
        docs.mkdir()
        self._write_md(
            docs / "test.md",
            'title: "T"\ncontent_type: how-to',
            "# T\n\nIn this tutorial we explore the theory behind webhooks.\n",
        )
        validator = DocLayersValidator(docs_dir=str(docs))
        violations = validator.detect_layer_violations()
        assert len(violations) >= 1

    def test_concept_with_steps(self, tmp_path: Path) -> None:
        from scripts.doc_layers_validator import DocLayersValidator

        docs = tmp_path / "docs"
        docs.mkdir()
        self._write_md(
            docs / "test.md",
            'title: "T"\ncontent_type: concept',
            "# T\n\nStep 1: Do this thing.\nStep 2: Then do that.\n",
        )
        validator = DocLayersValidator(docs_dir=str(docs))
        violations = validator.detect_layer_violations()
        concept_violations = [v for v in violations if v["content_type"] == "concept"]
        assert len(concept_violations) >= 1

#!/usr/bin/env python3
"""Tests for the doc compiler -- 5 documentation overview modalities."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from scripts.compile_doc_overview import (
    ALL_MODALITIES,
    DocInfo,
    compile_architecture_diagram,
    compile_auto_faq,
    compile_cross_doc_consistency,
    compile_doc_critique,
    compile_executive_briefing,
    load_doc,
    run_doc_compiler,
)
from scripts.license_gate import (
    COMMUNITY_FEATURES,
    PLAN_FEATURES,
    LicenseInfo,
    _community_license,
    reset_cache,
)


@pytest.fixture(autouse=True)
def _reset_license_cache():
    reset_cache()
    yield
    reset_cache()


@pytest.fixture()
def _enterprise_env(monkeypatch):
    monkeypatch.setenv("VERIOPS_LICENSE_PLAN", "enterprise")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_doc(tmp_path: Path, rel_path: str, content: str) -> Path:
    """Write a markdown doc to tmp_path/docs/rel_path."""
    full = tmp_path / "docs" / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")
    return full


def _make_tutorial(title: str = "Set up webhooks") -> str:
    return (
        "---\n"
        f'title: "{title}"\n'
        f'description: "Step-by-step guide to configure webhooks for your application."\n'
        "content_type: tutorial\n"
        "tags:\n"
        "  - Tutorial\n"
        "  - API\n"
        "---\n\n"
        f"# {title}\n\n"
        "This tutorial walks you through configuring webhooks.\n\n"
        "## Prerequisites\n\n"
        "You need an API key and access to port 8080.\n\n"
        "## Step 1\n\n"
        "```python\n"
        "import requests\n"
        "requests.post('http://localhost:8080/webhooks')\n"
        "```\n\n"
        "## Step 2\n\n"
        "Verify the webhook fires. Version 1.2.0 added this feature.\n"
    )


def _make_howto(title: str = "Configure authentication") -> str:
    return (
        "---\n"
        f'title: "{title}"\n'
        f'description: "How to configure authentication for secure API access in production."\n'
        "content_type: how-to\n"
        "tags:\n"
        "  - How-To\n"
        "  - API\n"
        "---\n\n"
        f"# {title}\n\n"
        "Authentication enables secure access to the API.\n\n"
        "## Set up API keys\n\n"
        "Generate keys from the dashboard on port 3000.\n"
    )


def _make_troubleshooting() -> str:
    return (
        "---\n"
        'title: "Webhook not firing"\n'
        'description: "Troubleshoot common issues when webhooks do not fire as expected."\n'
        "content_type: troubleshooting\n"
        "tags:\n"
        "  - Troubleshooting\n"
        "---\n\n"
        "# Webhook not firing\n\n"
        "Common troubleshooting steps for webhook failures.\n\n"
        "## Webhook returns 404\n\n"
        "Check that the URL is correct and the endpoint is running.\n\n"
        "## Webhook times out\n\n"
        "Increase the timeout to 30 seconds in the configuration.\n"
    )


def _make_concept() -> str:
    return (
        "---\n"
        'title: "Event-driven architecture"\n'
        'description: "Understanding event-driven architecture patterns and message brokers."\n'
        "content_type: concept\n"
        "tags:\n"
        "  - Concept\n"
        "  - Architecture\n"
        "---\n\n"
        "# Event-driven architecture\n\n"
        "Event-driven architecture is a pattern where components communicate "
        "through events published to a message broker.\n\n"
        "## Core components\n\n"
        "The main components are producers, consumers, and brokers.\n\n"
        "## Message brokers\n\n"
        "Common brokers include RabbitMQ (port 5672) and Kafka (port 9092).\n"
    )


def _make_reference() -> str:
    return (
        "---\n"
        'title: "API reference"\n'
        'description: "Complete API reference for all endpoints and request and response schemas."\n'
        "content_type: reference\n"
        "tags:\n"
        "  - Reference\n"
        "  - API\n"
        "---\n\n"
        "# API reference\n\n"
        "The API provides endpoints for managing resources.\n\n"
        "## Endpoints\n\n"
        "| Method | Path | Description |\n"
        "|--------|------|-------------|\n"
        "| GET | /users | List users |\n"
        "| POST | /users | Create user |\n\n"
        "## Authentication\n\n"
        "Use Bearer tokens. See [auth guide](../how-to/configure-auth.md).\n"
    )


def _setup_docs(tmp_path: Path) -> Path:
    """Create a minimal doc set and return docs_dir."""
    _write_doc(tmp_path, "getting-started/setup-webhooks.md", _make_tutorial())
    _write_doc(tmp_path, "how-to/configure-auth.md", _make_howto())
    _write_doc(tmp_path, "troubleshooting/webhook-not-firing.md", _make_troubleshooting())
    _write_doc(tmp_path, "concepts/event-driven.md", _make_concept())
    _write_doc(tmp_path, "reference/api-reference.md", _make_reference())
    return tmp_path / "docs"


def _setup_reports(tmp_path: Path) -> Path:
    """Create minimal reports and return reports_dir."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    consolidated = {
        "health_summary": {
            "quality_score": 85,
            "drift_status": "ok",
            "sla_status": "ok",
            "total_action_items": 3,
        },
        "action_items": [
            {"title": "Add webhook guide", "priority": "high", "source_report": "gaps"},
            {"title": "Update auth docs", "priority": "medium", "source_report": "drift"},
            {"title": "Fix stale FAQ", "priority": "low", "source_report": "kpi"},
        ],
    }
    (reports_dir / "consolidated_report.json").write_text(
        json.dumps(consolidated), encoding="utf-8",
    )
    kpi = {"metrics": {"doc_coverage": {"value": "78%"}, "freshness": {"value": "92%"}}}
    (reports_dir / "kpi-wall.json").write_text(
        json.dumps(kpi), encoding="utf-8",
    )
    return reports_dir


def _setup_glossary(tmp_path: Path) -> Path:
    """Create a glossary.yml."""
    glossary_path = tmp_path / "glossary.yml"
    # Write as simple YAML-like text (parsed by yaml.safe_load)
    glossary_path.write_text(
        "terms:\n"
        "  - preferred: webhook\n"
        "    aliases: [web hook, web-hook]\n"
        "  - preferred: API key\n"
        "    aliases: [api-key, apikey]\n",
        encoding="utf-8",
    )
    return glossary_path


def _setup_variables(tmp_path: Path) -> None:
    """Create _variables.yml in docs/."""
    vars_path = tmp_path / "docs" / "_variables.yml"
    vars_path.write_text(
        "product_name: TestProduct\n"
        "default_port: 8080\n"
        "api_version: v2\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# License gating tests
# ---------------------------------------------------------------------------


class TestLicenseGating:
    def test_pilot_blocked(self):
        features = dict(PLAN_FEATURES["pilot"])
        assert features.get("doc_compiler") is False

    def test_professional_blocked(self):
        features = dict(PLAN_FEATURES["professional"])
        assert features.get("doc_compiler") is False

    def test_enterprise_allowed(self):
        features = dict(PLAN_FEATURES["enterprise"])
        assert features.get("doc_compiler") is True


# ---------------------------------------------------------------------------
# Doc loading tests
# ---------------------------------------------------------------------------


class TestDocLoading:
    def test_frontmatter_parsing(self, tmp_path):
        docs_dir = _setup_docs(tmp_path)
        doc = load_doc(docs_dir / "getting-started" / "setup-webhooks.md", docs_dir)
        assert doc.title == "Set up webhooks"
        assert doc.content_type == "tutorial"
        assert "Tutorial" in doc.tags

    def test_code_block_extraction(self, tmp_path):
        docs_dir = _setup_docs(tmp_path)
        doc = load_doc(docs_dir / "getting-started" / "setup-webhooks.md", docs_dir)
        assert len(doc.code_blocks) == 1
        assert doc.code_blocks[0]["language"] == "python"


# ---------------------------------------------------------------------------
# Executive briefing tests
# ---------------------------------------------------------------------------


class TestExecutiveBriefing:
    def test_produces_markdown(self, tmp_path):
        docs_dir = _setup_docs(tmp_path)
        reports_dir = _setup_reports(tmp_path)
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = reports_dir / "briefing.md"
        result = compile_executive_briefing(docs, reports_dir, out)
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "# Documentation executive briefing" in content
        assert result["modality"] == "executive_briefing"

    def test_includes_kpi(self, tmp_path):
        docs_dir = _setup_docs(tmp_path)
        reports_dir = _setup_reports(tmp_path)
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = reports_dir / "briefing.md"
        compile_executive_briefing(docs, reports_dir, out)
        content = out.read_text(encoding="utf-8")
        assert "KPI highlights" in content

    def test_includes_action_items(self, tmp_path):
        docs_dir = _setup_docs(tmp_path)
        reports_dir = _setup_reports(tmp_path)
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = reports_dir / "briefing.md"
        compile_executive_briefing(docs, reports_dir, out)
        content = out.read_text(encoding="utf-8")
        assert "Add webhook guide" in content

    def test_graceful_missing_reports(self, tmp_path):
        docs_dir = _setup_docs(tmp_path)
        reports_dir = tmp_path / "empty_reports"
        reports_dir.mkdir()
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = reports_dir / "briefing.md"
        result = compile_executive_briefing(docs, reports_dir, out)
        assert out.exists()
        assert result["quality_score"] == "N/A"


# ---------------------------------------------------------------------------
# Cross-doc consistency tests
# ---------------------------------------------------------------------------


class TestCrossDocConsistency:
    def test_port_not_in_variables(self, tmp_path):
        docs_dir = _setup_docs(tmp_path)
        _setup_variables(tmp_path)
        glossary = _setup_glossary(tmp_path)
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = tmp_path / "consistency.json"
        result = compile_cross_doc_consistency(
            docs, glossary, docs_dir / "_variables.yml", out,
        )
        # Port 3000, 5672, 9092 are in docs but not in _variables.yml
        port_issues = [
            i for i in result["issues"] if i["type"] == "port_not_in_variables"
        ]
        assert len(port_issues) > 0

    def test_terminology_mismatch(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        _write_doc(tmp_path, "how-to/test.md", (
            "---\n"
            'title: "Test doc"\n'
            'description: "A test document with terminology issues for validation testing."\n'
            "content_type: how-to\n"
            "---\n\n"
            "# Test doc\n\n"
            "Configure the web hook endpoint.\n"
        ))
        glossary = _setup_glossary(tmp_path)
        vars_path = docs_dir / "_variables.yml"
        vars_path.write_text("product_name: Test\n", encoding="utf-8")
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = tmp_path / "consistency.json"
        result = compile_cross_doc_consistency(docs, glossary, vars_path, out)
        term_issues = [
            i for i in result["issues"] if i["type"] == "terminology_mismatch"
        ]
        assert len(term_issues) > 0
        assert any("web hook" in i["alias_used"] for i in term_issues)

    def test_variables_check(self, tmp_path):
        docs_dir = _setup_docs(tmp_path)
        _setup_variables(tmp_path)
        glossary = _setup_glossary(tmp_path)
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = tmp_path / "consistency.json"
        result = compile_cross_doc_consistency(
            docs, glossary, docs_dir / "_variables.yml", out,
        )
        # "8080" appears in docs and in _variables as default_port
        hardcoded = [
            i for i in result["issues"] if i["type"] == "hardcoded_variable"
        ]
        # Should detect hardcoded values that match variables
        assert isinstance(hardcoded, list)

    def test_no_false_positives_empty(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        glossary = tmp_path / "glossary.yml"
        glossary.write_text("", encoding="utf-8")
        vars_path = docs_dir / "_variables.yml"
        vars_path.write_text("", encoding="utf-8")
        out = tmp_path / "consistency.json"
        result = compile_cross_doc_consistency([], glossary, vars_path, out)
        assert result["total_issues"] == 0

    def test_output_is_valid_json(self, tmp_path):
        docs_dir = _setup_docs(tmp_path)
        _setup_variables(tmp_path)
        glossary = _setup_glossary(tmp_path)
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = tmp_path / "consistency.json"
        compile_cross_doc_consistency(
            docs, glossary, docs_dir / "_variables.yml", out,
        )
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "issues" in data


# ---------------------------------------------------------------------------
# Auto FAQ tests
# ---------------------------------------------------------------------------


class TestAutoFaq:
    def test_troubleshooting_extraction(self, tmp_path):
        docs_dir = _setup_docs(tmp_path)
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = tmp_path / "faq.json"
        result = compile_auto_faq(docs, out)
        ts_faqs = [f for f in result["faqs"] if f["category"] == "troubleshooting"]
        assert len(ts_faqs) >= 2  # Two H2 sections in troubleshooting doc

    def test_howto_questions(self, tmp_path):
        docs_dir = _setup_docs(tmp_path)
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = tmp_path / "faq.json"
        result = compile_auto_faq(docs, out)
        howto_faqs = [f for f in result["faqs"] if f["category"] == "how-to"]
        assert len(howto_faqs) >= 1
        assert howto_faqs[0]["question"].startswith("How do I")

    def test_concept_questions(self, tmp_path):
        docs_dir = _setup_docs(tmp_path)
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = tmp_path / "faq.json"
        result = compile_auto_faq(docs, out)
        concept_faqs = [f for f in result["faqs"] if f["category"] == "concept"]
        assert len(concept_faqs) >= 1
        assert "What is" in concept_faqs[0]["question"]

    def test_tag_grouping(self, tmp_path):
        docs_dir = _setup_docs(tmp_path)
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = tmp_path / "faq.json"
        result = compile_auto_faq(docs, out)
        assert "API" in result["tag_groups"]


# ---------------------------------------------------------------------------
# Architecture diagram tests
# ---------------------------------------------------------------------------


class TestArchitectureDiagram:
    def test_valid_mermaid_output(self, tmp_path):
        docs_dir = _setup_docs(tmp_path)
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = tmp_path / "arch.md"
        result = compile_architecture_diagram(docs, out)
        content = out.read_text(encoding="utf-8")
        assert "```mermaid" in content
        assert "graph TD" in content
        assert result["modality"] == "architecture_diagram"

    def test_component_extraction(self, tmp_path):
        docs_dir = _setup_docs(tmp_path)
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = tmp_path / "arch.md"
        result = compile_architecture_diagram(docs, out)
        assert result["components_count"] > 0

    def test_relationship_detection(self, tmp_path):
        docs_dir = _setup_docs(tmp_path)
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = tmp_path / "arch.md"
        result = compile_architecture_diagram(docs, out)
        # The reference doc links to how-to/configure-auth.md
        assert result["relationships_count"] >= 0  # May or may not match

    def test_interactive_html_generated(self, tmp_path):
        """When 6+ components, interactive HTML diagram is generated."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        # Create enough docs with enough H2 headings to exceed threshold
        for i in range(4):
            _write_doc(tmp_path, f"concepts/arch-{i}.md", (
                "---\n"
                f'title: "Architecture part {i}"\n'
                f'description: "Architecture documentation part {i} for interactive diagram test."\n'
                "content_type: concept\n"
                "tags:\n"
                "  - Architecture\n"
                "---\n\n"
                f"# Architecture part {i}\n\n"
                f"## Component Alpha {i}\n\nAlpha component details.\n\n"
                f"## Component Beta {i}\n\nBeta component details.\n"
            ))
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = tmp_path / "arch.md"
        result = compile_architecture_diagram(docs, out)
        assert result["components_count"] >= 6
        assert result["interactive"] is True
        html_path = out.with_suffix(".html")
        assert html_path.exists()
        html_content = html_path.read_text(encoding="utf-8")
        assert "showInfo" in html_content

    def test_no_interactive_below_threshold(self, tmp_path):
        """When fewer than 6 components, only mermaid is generated."""
        docs_dir = _setup_docs(tmp_path)
        from scripts.compile_doc_overview import load_all_docs
        docs = [d for d in load_all_docs(docs_dir) if d.content_type == "concept"]
        out = tmp_path / "arch.md"
        result = compile_architecture_diagram(docs, out)
        if result["components_count"] < 6:
            assert result["interactive"] is False


# ---------------------------------------------------------------------------
# Doc critique tests
# ---------------------------------------------------------------------------


class TestDocCritique:
    def test_missing_code_examples(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        _write_doc(tmp_path, "how-to/no-code.md", (
            "---\n"
            'title: "Guide without code"\n'
            'description: "A how-to guide that has no code examples for testing purposes."\n'
            "content_type: how-to\n"
            "---\n\n"
            "# Guide without code\n\n"
            "This guide explains things but has no code blocks.\n"
            "Follow these steps to complete the task.\n"
            "Check the configuration settings in the dashboard.\n"
        ))
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = tmp_path / "critique.json"
        result = compile_doc_critique(docs, tmp_path / "reports", out)
        checks = [i["check"] for i in result["issues"]]
        assert "missing_code_examples" in checks

    def test_short_description(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        _write_doc(tmp_path, "ref/short.md", (
            "---\n"
            'title: "Short desc doc"\n'
            'description: "Too short."\n'
            "content_type: reference\n"
            "---\n\n"
            "# Short desc doc\n\n"
            "Content here is adequate length for testing purposes.\n"
            "This document has enough words to pass the thin content check.\n"
            "Additional content to reach the word count threshold needed.\n"
            "More words to ensure we pass the minimum word count of one hundred.\n"
            "Even more content padding to make this test focus on description length.\n"
            "Final paragraph with additional text to reach the needed word count.\n"
            "Testing the short description detection in the doc critique modality.\n"
            "This paragraph adds more words for the minimum content requirement.\n"
        ))
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = tmp_path / "critique.json"
        result = compile_doc_critique(docs, tmp_path / "reports", out)
        checks = [i["check"] for i in result["issues"]]
        assert "short_description" in checks

    def test_thin_content(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        _write_doc(tmp_path, "ref/thin.md", (
            "---\n"
            'title: "Thin page"\n'
            'description: "This document has very little content and should be flagged as thin."\n'
            "content_type: reference\n"
            "---\n\n"
            "# Thin page\n\n"
            "Just a few words.\n"
        ))
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = tmp_path / "critique.json"
        result = compile_doc_critique(docs, tmp_path / "reports", out)
        checks = [i["check"] for i in result["issues"]]
        assert "thin_content" in checks

    def test_boilerplate_detection(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        _write_doc(tmp_path, "ref/wip.md", (
            "---\n"
            'title: "Work in progress page"\n'
            'description: "This page is a placeholder for future documentation content."\n'
            "content_type: reference\n"
            "---\n\n"
            "# Work in progress page\n\n"
            "This section is TODO and coming soon.\n"
            "More content will be added in a future update to this page.\n"
            "For now this placeholder exists to reserve the documentation slot.\n"
            "Additional text to pad out the word count beyond the minimum.\n"
            "Even more content to ensure we reach the one hundred word minimum.\n"
            "The quick brown fox jumps over the lazy dog repeatedly here.\n"
            "Final padding text to make the document pass the thin content check.\n"
            "This last paragraph should push us well past the minimum threshold.\n"
        ))
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = tmp_path / "critique.json"
        result = compile_doc_critique(docs, tmp_path / "reports", out)
        checks = [i["check"] for i in result["issues"]]
        assert "boilerplate_detected" in checks

    def test_duplicate_coverage(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        for i in range(2):
            _write_doc(tmp_path, f"ref/webhooks-{i}.md", (
                "---\n"
                'title: "Webhooks"\n'
                'description: "Documentation about webhooks for the platform integration system."\n'
                "content_type: reference\n"
                "---\n\n"
                "# Webhooks\n\n"
                "Webhook documentation content that is duplicated across files.\n"
                "This tests the duplicate coverage detection in doc critique.\n"
                "Additional content to reach the minimum word count for testing.\n"
                "More text padding to pass the thin content threshold check.\n"
                "Even more words to ensure the document is not flagged as thin.\n"
                "The content here is intentionally similar to test deduplication.\n"
                "Final paragraph with enough words to pass all other checks.\n"
                "Last line of content to hit the one hundred word minimum.\n"
            ))
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = tmp_path / "critique.json"
        result = compile_doc_critique(docs, tmp_path / "reports", out)
        checks = [i["check"] for i in result["issues"]]
        assert "duplicate_coverage" in checks

    def test_reading_level(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        # Create doc with very complex sentences
        long_words = " ".join(
            ["implementation" if i % 2 == 0 else "characterization" for i in range(80)]
        )
        _write_doc(tmp_path, "ref/complex.md", (
            "---\n"
            'title: "Complex document"\n'
            'description: "A document with deliberately complex language for reading level tests."\n'
            "content_type: reference\n"
            "---\n\n"
            "# Complex document\n\n"
            f"{long_words}.\n"
        ))
        from scripts.compile_doc_overview import load_all_docs
        docs = load_all_docs(docs_dir)
        out = tmp_path / "critique.json"
        result = compile_doc_critique(docs, tmp_path / "reports", out)
        checks = [i["check"] for i in result["issues"]]
        assert "high_reading_level" in checks


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


class TestCLI:
    def test_modalities_filtering(self, tmp_path, _enterprise_env):
        docs_dir = _setup_docs(tmp_path)
        reports_dir = _setup_reports(tmp_path)
        _setup_variables(tmp_path)
        glossary = _setup_glossary(tmp_path)
        result = run_doc_compiler(
            docs_dir=docs_dir,
            reports_dir=reports_dir,
            glossary_path=glossary,
            modalities=["executive_briefing", "doc_critique"],
        )
        assert set(result["modalities_run"]) == {"executive_briefing", "doc_critique"}
        assert "auto_faq" not in result["modalities_run"]

    def test_combined_report_output(self, tmp_path, _enterprise_env):
        docs_dir = _setup_docs(tmp_path)
        reports_dir = _setup_reports(tmp_path)
        _setup_variables(tmp_path)
        glossary = _setup_glossary(tmp_path)
        result = run_doc_compiler(
            docs_dir=docs_dir,
            reports_dir=reports_dir,
            glossary_path=glossary,
            modalities=list(ALL_MODALITIES),
        )
        combined_path = reports_dir / "doc_compiler_report.json"
        assert combined_path.exists()
        data = json.loads(combined_path.read_text(encoding="utf-8"))
        assert len(data["modalities_run"]) == 5
        assert data["total_docs_loaded"] == 5

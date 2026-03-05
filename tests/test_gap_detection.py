"""Tests for scripts/gap_detection/ module.

Covers the pure data-processing logic of:
- code_analyzer.py (CodeChange, AnalysisResult, pattern matching, commit analysis)
- community_collector.py (categorization, doc type detection, keyword extraction)
- algolia_parser.py (CSV/JSON parsing, query analysis, enrichment)
- gap_aggregator.py (aggregation, deduplication, summary, export)
- batch_generator.py (task creation, slugify, template mapping)
"""

from __future__ import annotations

import csv
import json
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.gap_detection.code_analyzer import CodeChange, CodeChangeAnalyzer, AnalysisResult
from scripts.gap_detection.community_collector import CommunityCollector, CommunityTopic, CollectionResult
from scripts.gap_detection.algolia_parser import AlgoliaAnalytics, SearchQuery, AlgoliaResult
from scripts.gap_detection.gap_aggregator import (
    AggregatedReport,
    DocumentationGap,
    GapAggregator,
)
from scripts.gap_detection.batch_generator import BatchDocGenerator, DocumentTask, BatchResult


# ===========================================================================
# CodeChangeAnalyzer
# ===========================================================================


class TestCodeChangeAnalyzer:
    """Tests for CodeChangeAnalyzer."""

    def test_analyze_commit_message_feature(self) -> None:
        """Feature commits are detected with high priority."""
        analyzer = CodeChangeAnalyzer()
        commit = {"hash": "abc123", "message": "feat(webhook): add retry logic", "date": "2026-01-01"}
        result = analyzer._analyze_commit_message(commit)
        assert result is not None
        assert result["type"] == "feature"
        assert result["priority"] == "high"
        assert result["scope"] == "webhook"
        assert result["doc_required"] is True

    def test_analyze_commit_message_breaking(self) -> None:
        analyzer = CodeChangeAnalyzer()
        commit = {"hash": "abc123", "message": "BREAKING CHANGE: remove v1 API", "date": "2026-01-01"}
        result = analyzer._analyze_commit_message(commit)
        assert result is not None
        assert result["type"] == "breaking"
        assert result["priority"] == "high"

    def test_analyze_commit_message_fix(self) -> None:
        analyzer = CodeChangeAnalyzer()
        commit = {"hash": "abc123", "message": "fix: correct timeout handling", "date": "2026-01-01"}
        result = analyzer._analyze_commit_message(commit)
        assert result is not None
        assert result["type"] == "fix"
        assert result["priority"] == "medium"

    def test_analyze_commit_message_unrecognized(self) -> None:
        analyzer = CodeChangeAnalyzer()
        commit = {"hash": "abc123", "message": "WIP something", "date": "2026-01-01"}
        result = analyzer._analyze_commit_message(commit)
        assert result is None

    def test_should_ignore_node_modules(self) -> None:
        analyzer = CodeChangeAnalyzer()
        assert analyzer._should_ignore("node_modules/package/index.js") is True

    def test_should_not_ignore_src(self) -> None:
        analyzer = CodeChangeAnalyzer()
        assert analyzer._should_ignore("src/index.ts") is False

    def test_map_status(self) -> None:
        analyzer = CodeChangeAnalyzer()
        assert analyzer._map_status("A") == "added"
        assert analyzer._map_status("M") == "modified"
        assert analyzer._map_status("D") == "deleted"
        assert analyzer._map_status("R100") == "renamed"

    def test_generate_summary(self) -> None:
        analyzer = CodeChangeAnalyzer()
        changes = [
            CodeChange("f1.ts", "added", "api_endpoint", "desc", 10, priority="high"),
            CodeChange("f2.ts", "modified", "env_var", "desc", 5, priority="medium"),
            CodeChange("f3.ts", "added", "api_endpoint", "desc", 8, priority="high"),
        ]
        commit_analysis = [
            {"type": "feature", "doc_required": True, "priority": "high"},
            {"type": "fix", "doc_required": False, "priority": "medium"},
        ]
        summary = analyzer._generate_summary(changes, commit_analysis)
        assert summary["total_changes"] == 3
        assert summary["by_category"]["api_endpoint"] == 2
        assert summary["by_priority"]["high"] == 2
        assert summary["commits_requiring_docs"] == 1

    def test_analyze_file_diff_detects_api_endpoint(self) -> None:
        analyzer = CodeChangeAnalyzer()
        diff = """
+@app.post('/api/v1/users')
+async def create_user(data):
+    pass
"""
        changes = analyzer._analyze_file_diff("src/routes.py", diff, "added")
        api_changes = [c for c in changes if c.category == "api_endpoint"]
        assert len(api_changes) >= 1

    def test_analyze_file_diff_detects_env_var(self) -> None:
        analyzer = CodeChangeAnalyzer()
        diff = "+DATABASE_URL = os.environ['DATABASE_URL']\n"
        changes = analyzer._analyze_file_diff("src/config.py", diff, "added")
        env_changes = [c for c in changes if c.category == "env_var"]
        assert len(env_changes) >= 1


# ===========================================================================
# CommunityCollector
# ===========================================================================


class TestCommunityCollector:
    """Tests for CommunityCollector."""

    def test_categorize_topic_webhook(self) -> None:
        collector = CommunityCollector()
        assert collector._categorize_topic("How to configure webhook trigger") == "webhook"

    def test_categorize_topic_authentication(self) -> None:
        collector = CommunityCollector()
        assert collector._categorize_topic("OAuth2 credential setup") == "authentication"

    def test_categorize_topic_error(self) -> None:
        collector = CommunityCollector()
        assert collector._categorize_topic("Error when running workflow") == "error"

    def test_categorize_topic_general(self) -> None:
        collector = CommunityCollector()
        assert collector._categorize_topic("Some random question") == "general"

    def test_determine_doc_type_troubleshooting(self) -> None:
        collector = CommunityCollector()
        assert collector._determine_doc_type("Webhook not working after update") == "troubleshooting"

    def test_determine_doc_type_howto(self) -> None:
        collector = CommunityCollector()
        assert collector._determine_doc_type("How to set up email notifications") == "how-to"

    def test_determine_doc_type_concept(self) -> None:
        collector = CommunityCollector()
        assert collector._determine_doc_type("What is the difference between triggers") == "concept"

    def test_determine_doc_type_reference(self) -> None:
        collector = CommunityCollector()
        assert collector._determine_doc_type("List of available configuration options") == "reference"

    def test_determine_doc_type_default(self) -> None:
        collector = CommunityCollector()
        assert collector._determine_doc_type("Random topic without keywords") == "how-to"

    def test_clean_title(self) -> None:
        collector = CommunityCollector()
        assert collector._clean_title("<b>Bold</b> title   with   spaces") == "Bold title with spaces"

    def test_extract_keywords(self) -> None:
        collector = CommunityCollector()
        keywords = collector._extract_keywords("How to configure webhook authentication with OAuth2")
        assert len(keywords) >= 1
        # Should contain meaningful words, not stop words
        assert "configure" in keywords or "webhook" in keywords or "authentication" in keywords

    def test_analyze_keyword_frequency(self) -> None:
        collector = CommunityCollector()
        topics = [
            CommunityTopic("Webhook setup", "", "rss", keywords=["webhook", "setup"]),
            CommunityTopic("Webhook auth", "", "rss", keywords=["webhook", "auth"]),
            CommunityTopic("Auth config", "", "rss", keywords=["auth", "config"]),
        ]
        freq = collector._analyze_keyword_frequency(topics)
        assert freq.get("webhook", 0) == 2
        assert freq.get("auth", 0) == 2

    def test_generate_doc_suggestions(self) -> None:
        collector = CommunityCollector()
        topics = [
            CommunityTopic("Webhook setup", "", "rss", category="webhook", keywords=["webhook"], potential_doc_type="how-to"),
            CommunityTopic("Webhook config", "", "rss", category="webhook", keywords=["webhook"], potential_doc_type="how-to"),
            CommunityTopic("Auth issue", "", "rss", category="authentication", keywords=["auth"], potential_doc_type="troubleshooting"),
        ]
        freq = {"webhook": 2, "auth": 1}
        suggestions = collector._generate_doc_suggestions(topics, freq)
        assert len(suggestions) >= 1
        # Most frequent category should appear first
        assert suggestions[0]["category"] == "webhook"


# ===========================================================================
# AlgoliaAnalytics
# ===========================================================================


class TestAlgoliaAnalytics:
    """Tests for AlgoliaAnalytics."""

    def test_enrich_query_webhook(self) -> None:
        analytics = AlgoliaAnalytics()
        query = SearchQuery("webhook trigger setup", 50, 0, 0)
        analytics._enrich_query(query)
        assert query.category == "webhook"

    def test_enrich_query_error(self) -> None:
        analytics = AlgoliaAnalytics()
        query = SearchQuery("error 500 not working", 30, 0, 0)
        analytics._enrich_query(query)
        assert query.category == "error"

    def test_enrich_query_sets_priority(self) -> None:
        analytics = AlgoliaAnalytics()
        high = SearchQuery("test", 100, 0, 0)
        analytics._enrich_query(high)
        assert high.priority == "high"

        medium = SearchQuery("test", 5, 0, 0)
        analytics._enrich_query(medium)
        assert medium.priority in ("low", "medium")

    def test_analyze_queries_separates_no_results(self) -> None:
        analytics = AlgoliaAnalytics()
        queries = [
            SearchQuery("webhook", 50, 0, 0),  # no results
            SearchQuery("auth", 30, 10, 0.01),  # low CTR
            SearchQuery("setup", 100, 50, 0.5),  # popular
        ]
        result = analytics._analyze_queries(queries)
        assert len(result.no_results_queries) == 1
        assert result.no_results_queries[0].query == "webhook"
        assert len(result.popular_queries) >= 1

    def test_analyze_from_json(self, tmp_path: Path) -> None:
        data = {
            "queries": [
                {"query": "webhook setup", "count": 50, "nbHits": 0, "clickThroughRate": 0},
                {"query": "auth config", "count": 30, "nbHits": 10, "clickThroughRate": 0.05},
            ],
        }
        json_path = tmp_path / "algolia.json"
        json_path.write_text(json.dumps(data), encoding="utf-8")
        analytics = AlgoliaAnalytics()
        result = analytics.analyze_from_json(str(json_path))
        assert len(result.no_results_queries) == 1
        assert result.no_results_queries[0].query == "webhook setup"

    def test_analyze_from_csv(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "algolia.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Search", "Count", "Results", "CTR"])
            writer.writeheader()
            writer.writerow({"Search": "webhook", "Count": "50", "Results": "0", "CTR": "0"})
            writer.writerow({"Search": "setup guide", "Count": "30", "Results": "10", "CTR": "5%"})
        analytics = AlgoliaAnalytics()
        result = analytics.analyze_from_csv(str(csv_path))
        assert len(result.no_results_queries) >= 1

    def test_analyze_from_json_file_not_found(self) -> None:
        analytics = AlgoliaAnalytics()
        with pytest.raises(FileNotFoundError):
            analytics.analyze_from_json("/nonexistent.json")

    def test_parse_csv_row_empty_query(self) -> None:
        analytics = AlgoliaAnalytics()
        result = analytics._parse_csv_row({"Search": "", "Count": "10"})
        assert result is None

    def test_generate_doc_suggestions(self) -> None:
        analytics = AlgoliaAnalytics()
        result = AlgoliaResult(
            no_results_queries=[SearchQuery("webhook trigger", 50, 0, 0, category="webhook")],
            low_ctr_queries=[SearchQuery("auth setup", 30, 10, 0.01, category="authentication")],
        )
        suggestions = analytics._generate_suggestions(result)
        assert len(suggestions) >= 1


# ===========================================================================
# GapAggregator
# ===========================================================================


class TestGapAggregator:
    """Tests for GapAggregator."""

    def test_aggregate_code_only(self, tmp_path: Path) -> None:
        aggregator = GapAggregator(output_dir=str(tmp_path))
        code_result = AnalysisResult(
            changes=[
                CodeChange("src/api.ts", "added", "api_endpoint", "New endpoint /users", 20, priority="high",
                           doc_suggestion="Create reference for /users endpoint"),
            ],
        )
        report = aggregator.aggregate_all(code_result=code_result)
        assert len(report.gaps) == 1
        assert report.gaps[0].source == "code"
        assert report.summary["total_gaps"] == 1
        assert "code_changes" in report.sources_analyzed

    def test_aggregate_community_only(self, tmp_path: Path) -> None:
        aggregator = GapAggregator(output_dir=str(tmp_path))
        community_result = CollectionResult(
            suggested_docs=[
                {
                    "category": "webhook",
                    "topic": "Webhook configuration",
                    "frequency": 15,
                    "suggested_doc_type": "how-to",
                    "priority": "high",
                    "keywords": ["webhook", "config"],
                    "sample_questions": ["How to configure webhooks?"],
                },
            ],
        )
        report = aggregator.aggregate_all(community_result=community_result)
        assert len(report.gaps) == 1
        assert report.gaps[0].source == "community"

    def test_aggregate_algolia_only(self, tmp_path: Path) -> None:
        aggregator = GapAggregator(output_dir=str(tmp_path))
        algolia_result = AlgoliaResult(
            suggested_docs=[
                {
                    "query": "webhook setup",
                    "reason": "no_results",
                    "search_count": 50,
                    "category": "webhook",
                    "suggested_doc_type": "how-to",
                    "priority": "high",
                    "action": "Create webhook setup guide",
                },
            ],
        )
        report = aggregator.aggregate_all(algolia_result=algolia_result)
        assert len(report.gaps) == 1
        assert report.gaps[0].source == "search"

    def test_deduplication(self, tmp_path: Path) -> None:
        aggregator = GapAggregator(output_dir=str(tmp_path))
        gaps = [
            DocumentationGap("1", "T1", "D1", "code", "webhook", "how-to", "high", frequency=10),
            DocumentationGap("2", "T2", "D2", "community", "webhook", "how-to", "medium", frequency=5),
        ]
        result = aggregator._deduplicate_gaps(gaps)
        assert len(result) == 1
        assert result[0].frequency == 15  # Merged frequencies
        assert result[0].priority == "high"  # Kept highest priority

    def test_generate_summary(self, tmp_path: Path) -> None:
        aggregator = GapAggregator(output_dir=str(tmp_path))
        report = AggregatedReport(
            gaps=[
                DocumentationGap("1", "T1", "D1", "code", "api_endpoint", "reference", "high"),
                DocumentationGap("2", "T2", "D2", "community", "webhook", "how-to", "medium"),
                DocumentationGap("3", "T3", "D3", "search", "error", "troubleshooting", "low"),
            ],
        )
        summary = aggregator._generate_summary(report)
        assert summary["total_gaps"] == 3
        assert summary["high_priority"] == 1
        assert summary["by_source"]["code"] == 1
        assert summary["by_doc_type"]["reference"] == 1

    def test_map_code_to_doc_type(self, tmp_path: Path) -> None:
        aggregator = GapAggregator(output_dir=str(tmp_path))
        assert aggregator._map_code_to_doc_type("api_endpoint") == "reference"
        assert aggregator._map_code_to_doc_type("breaking_change") == "how-to"
        assert aggregator._map_code_to_doc_type("unknown_category") == "how-to"

    def test_truncate(self, tmp_path: Path) -> None:
        aggregator = GapAggregator(output_dir=str(tmp_path))
        assert aggregator._truncate("short", 50) == "short"
        assert aggregator._truncate("a" * 100, 10) == "aaaaaaa..."

    def test_save_to_json(self, tmp_path: Path) -> None:
        aggregator = GapAggregator(output_dir=str(tmp_path))
        report = AggregatedReport(
            gaps=[DocumentationGap("1", "T", "D", "code", "api", "reference", "high")],
            summary={"total_gaps": 1},
            sources_analyzed=["code_changes"],
        )
        path = aggregator.save_to_json(report)
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        assert data["summary"]["total_gaps"] == 1
        assert len(data["gaps"]) == 1

    def test_save_to_csv(self, tmp_path: Path) -> None:
        aggregator = GapAggregator(output_dir=str(tmp_path))
        report = AggregatedReport(
            gaps=[DocumentationGap("1", "T", "D", "code", "api", "reference", "high")],
        )
        path = aggregator.save_to_csv(report)
        assert Path(path).exists()
        content = Path(path).read_text(encoding="utf-8")
        assert "ID" in content
        assert "code" in content

    def test_sorting_by_priority_and_frequency(self, tmp_path: Path) -> None:
        aggregator = GapAggregator(output_dir=str(tmp_path))
        code_result = AnalysisResult(
            changes=[
                CodeChange("f1", "added", "api_endpoint", "d1", 1, priority="low", doc_suggestion="s1"),
                CodeChange("f2", "added", "webhook", "d2", 1, priority="high", doc_suggestion="s2"),
                CodeChange("f3", "added", "config_option", "d3", 1, priority="medium", doc_suggestion="s3"),
            ],
        )
        report = aggregator.aggregate_all(code_result=code_result)
        priorities = [g.priority for g in report.gaps]
        expected_order = ["high", "medium", "low"]
        # High should come before medium, medium before low
        high_idx = priorities.index("high") if "high" in priorities else 999
        low_idx = priorities.index("low") if "low" in priorities else -1
        assert high_idx < low_idx


# ===========================================================================
# BatchDocGenerator
# ===========================================================================


class TestBatchDocGenerator:
    """Tests for BatchDocGenerator."""

    def test_slugify(self) -> None:
        generator = BatchDocGenerator()
        assert generator._slugify("Configure Webhook Auth!") == "configure-webhook-auth"
        assert generator._slugify("API v2 Endpoints") == "api-v2-endpoints"

    def test_clean_title(self) -> None:
        generator = BatchDocGenerator()
        result = generator._clean_title("Api Endpoint: /users/create")
        assert "Api Endpoint" in result or "api" in result.lower()

    def test_create_task_from_gap(self) -> None:
        generator = BatchDocGenerator()
        gap = DocumentationGap(
            id="CODE-0001",
            title="New API endpoint /users",
            description="Create reference docs",
            source="code",
            category="api_endpoint",
            suggested_doc_type="reference",
            priority="high",
            keywords=["api", "users"],
        )
        task = generator._create_task_from_gap(gap, 1)
        assert task.id == "DOC-001"
        assert task.gap_id == "CODE-0001"
        assert task.doc_type == "reference"
        assert "reference" in task.output_path
        assert task.template_name == "reference.md"

    def test_create_batch_from_report(self, tmp_path: Path) -> None:
        generator = BatchDocGenerator(templates_dir=str(tmp_path / "templates"), output_base=str(tmp_path))
        report = AggregatedReport(
            gaps=[
                DocumentationGap("1", "High gap", "D", "code", "api", "reference", "high"),
                DocumentationGap("2", "Medium gap", "D", "code", "webhook", "how-to", "medium"),
                DocumentationGap("3", "Low gap", "D", "code", "config", "reference", "low"),
            ],
        )
        batch = generator.create_batch_from_report(report, max_tasks=5, priority_filter=["high", "medium"])
        assert len(batch.tasks) == 2
        assert batch.tasks[0].priority == "high"

    def test_save_batch_config(self, tmp_path: Path) -> None:
        generator = BatchDocGenerator(output_base=str(tmp_path))
        batch = BatchResult(
            tasks=[
                DocumentTask("DOC-001", "GAP-001", "Test", "reference", "api", "high", "docs/ref/test.md", "reference.md"),
            ],
            claude_prompt="Generate docs for test",
        )
        path = generator.save_batch_config(batch)
        assert Path(path).exists()
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        assert data["total_tasks"] == 1

    def test_generate_claude_prompt(self) -> None:
        generator = BatchDocGenerator()
        tasks = [
            DocumentTask("DOC-001", "GAP-001", "Webhook Guide", "how-to", "webhook", "high", "docs/how-to/webhook.md", "how-to.md"),
        ]
        prompt = generator._generate_claude_prompt(tasks)
        assert "DOC-001" in prompt
        assert "Webhook Guide" in prompt

    def test_template_map_coverage(self) -> None:
        """All standard doc types have a template mapping."""
        generator = BatchDocGenerator()
        for doc_type in ["tutorial", "how-to", "concept", "reference", "troubleshooting"]:
            assert doc_type in generator.TEMPLATE_MAP
            assert doc_type in generator.OUTPUT_DIRS

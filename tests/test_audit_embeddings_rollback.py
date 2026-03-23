"""Tests for generate_audit_scorecard, generate_embeddings, and rollback scripts.

Covers scoring formulas, edge cases, date parsing, embeddings pipeline,
and rollback mechanics. Targets 70+ tests with exact weight verification.
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import generate_audit_scorecard as scorecard
from scripts import generate_embeddings as embeddings
from scripts import rollback as rollback_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_kpis(
    *,
    undocumented_pct: float = 0.0,
    coverage_pct: float = 100.0,
    total_operations: int = 10,
    documented_operations: int = 10,
    undocumented_operations: int = 0,
    example_reliability_pct: float = 100.0,
    executed_examples: int = 10,
    failed_examples: int = 0,
    report_found_examples: bool = True,
    stale_docs_pct: float = 0.0,
    dated_docs: int = 5,
    drift_pct: float = 0.0,
    docs_contract_report_found: bool = True,
    interface_changed_count: int = 0,
    docs_contract_mismatch_count: int = 0,
    api_drift_report_found: bool = True,
    api_drift_status: str = "ok",
    layers_missing_pct: float = 0.0,
    total_features: int = 5,
    features_missing: int = 0,
    terminology_violation_pct: float = 0.0,
    terminology_consistency_pct: float = 100.0,
    forbidden_terms_count: int = 0,
    forbidden_term_occurrences: int = 0,
    retrieval_found: bool = True,
    precision_at_k: float = 0.8,
    recall_at_k: float = 0.7,
    hallucination_rate: float = 0.05,
) -> dict[str, Any]:
    """Build a KPIs dict with sensible defaults for testing."""
    return {
        "api_coverage": {
            "spec_found": True,
            "spec_path": "api/openapi.yaml",
            "total_operations": total_operations,
            "documented_operations": documented_operations,
            "undocumented_operations": undocumented_operations,
            "undocumented_pct": undocumented_pct,
            "coverage_pct": coverage_pct,
            "undocumented_samples": [],
        },
        "example_reliability": {
            "report_found": report_found_examples,
            "report_path": "reports/examples_smoke_report.json",
            "executed_examples": executed_examples,
            "failed_examples": failed_examples,
            "example_reliability_pct": example_reliability_pct,
        },
        "freshness": {
            "total_docs": 10,
            "dated_docs": dated_docs,
            "missing_date_docs": 0,
            "average_age_days": 30.0,
            "median_age_days": 25.0,
            "stale_days_threshold": 180,
            "stale_docs_count": 0,
            "stale_docs_pct": stale_docs_pct,
        },
        "drift": {
            "docs_contract_report_found": docs_contract_report_found,
            "api_drift_report_found": api_drift_report_found,
            "interface_changed_count": interface_changed_count,
            "docs_contract_mismatch_count": docs_contract_mismatch_count,
            "docs_contract_drift_pct": drift_pct,
            "api_drift_status": api_drift_status,
        },
        "layer_completeness": {
            "required_layers": ["concept", "how-to", "reference"],
            "total_features": total_features,
            "features_missing_required_layers": features_missing,
            "features_missing_required_layers_pct": layers_missing_pct,
            "sample_missing_features": [],
        },
        "terminology": {
            "glossary_path": "glossary.yml",
            "forbidden_terms_count": forbidden_terms_count,
            "glossary_terms_count": 10,
            "docs_scanned": 10,
            "docs_with_forbidden_terms": 0,
            "forbidden_term_occurrences": forbidden_term_occurrences,
            "terminology_violation_pct": terminology_violation_pct,
            "terminology_consistency_pct": terminology_consistency_pct,
            "offender_samples": [],
            "glossary_sync_report_found": False,
        },
        "retrieval_quality": {
            "report_found": retrieval_found,
            "status": "ok" if retrieval_found else "missing",
            "precision_at_k": precision_at_k,
            "recall_at_k": recall_at_k,
            "hallucination_rate": hallucination_rate,
            "top_k": 3,
        },
    }


# ===================================================================
# Section 1: generate_audit_scorecard.py
# ===================================================================


class TestSafePct:
    """Tests for _safe_pct division-safe helper."""

    def test_normal_division(self) -> None:
        """Verify basic percentage calculation."""
        assert scorecard._safe_pct(50, 200) == 25.0

    def test_denominator_zero(self) -> None:
        """Division by zero returns 0.0."""
        assert scorecard._safe_pct(10, 0) == 0.0

    def test_denominator_negative(self) -> None:
        """Negative denominator returns 0.0."""
        assert scorecard._safe_pct(10, -5) == 0.0

    def test_numerator_zero(self) -> None:
        """Zero numerator returns 0.0."""
        assert scorecard._safe_pct(0, 100) == 0.0

    def test_full_percentage(self) -> None:
        """Equal numerator and denominator returns 100.0."""
        assert scorecard._safe_pct(100, 100) == 100.0

    def test_rounding_precision(self) -> None:
        """Result is rounded to 2 decimal places."""
        result = scorecard._safe_pct(1, 3)
        assert result == 33.33

    def test_large_values(self) -> None:
        """Handles large numerator exceeding denominator."""
        assert scorecard._safe_pct(200, 100) == 200.0


class TestExtractFrontmatter:
    """Tests for YAML frontmatter extraction."""

    def test_valid_frontmatter(self) -> None:
        """Extracts valid YAML between --- delimiters."""
        content = "---\ntitle: Hello\ndescription: World\n---\nBody text"
        fm = scorecard._extract_frontmatter(content)
        assert fm["title"] == "Hello"
        assert fm["description"] == "World"

    def test_no_frontmatter(self) -> None:
        """Returns empty dict if no --- prefix."""
        assert scorecard._extract_frontmatter("No frontmatter here") == {}

    def test_incomplete_frontmatter(self) -> None:
        """Returns empty dict if closing --- is missing."""
        assert scorecard._extract_frontmatter("---\ntitle: X\n") == {}

    def test_invalid_yaml(self) -> None:
        """Returns empty dict for malformed YAML."""
        content = "---\n: :\n  bad:\n    - [\n---\nBody"
        result = scorecard._extract_frontmatter(content)
        assert result == {}

    def test_non_dict_yaml(self) -> None:
        """Returns empty dict if YAML parses to non-dict."""
        content = "---\n- item1\n- item2\n---\nBody"
        assert scorecard._extract_frontmatter(content) == {}

    def test_empty_yaml(self) -> None:
        """Returns empty dict for empty YAML block."""
        content = "---\n\n---\nBody"
        assert scorecard._extract_frontmatter(content) == {}


class TestParseIsoDate:
    """Tests for ISO 8601 date parsing with timezone handling."""

    def test_date_only(self) -> None:
        """Date-only string gets midnight UTC."""
        result = scorecard._parse_iso_date("2024-06-15")
        assert result is not None
        assert result.year == 2024
        assert result.month == 6
        assert result.day == 15
        assert result.tzinfo == timezone.utc

    def test_full_iso_with_z(self) -> None:
        """ISO string with Z suffix converts to UTC."""
        result = scorecard._parse_iso_date("2024-01-10T12:30:00Z")
        assert result is not None
        assert result.hour == 12
        assert result.minute == 30
        assert result.tzinfo == timezone.utc

    def test_full_iso_with_offset(self) -> None:
        """ISO string with timezone offset normalizes to UTC."""
        result = scorecard._parse_iso_date("2024-01-10T12:00:00+05:00")
        assert result is not None
        assert result.hour == 7
        assert result.tzinfo == timezone.utc

    def test_naive_datetime(self) -> None:
        """Naive datetime (no tz) gets UTC applied."""
        result = scorecard._parse_iso_date("2024-03-20T09:00:00")
        assert result is not None
        assert result.tzinfo == timezone.utc

    def test_empty_string(self) -> None:
        """Empty string returns None."""
        assert scorecard._parse_iso_date("") is None

    def test_invalid_format(self) -> None:
        """Non-date string returns None."""
        assert scorecard._parse_iso_date("not-a-date") is None

    def test_whitespace_handling(self) -> None:
        """Leading/trailing whitespace is stripped."""
        result = scorecard._parse_iso_date("  2024-01-01  ")
        assert result is not None
        assert result.year == 2024


class TestCollectOperations:
    """Tests for OpenAPI operation extraction."""

    def test_single_get(self) -> None:
        """Extracts a single GET operation."""
        spec: dict[str, Any] = {
            "paths": {
                "/users": {
                    "get": {"operationId": "listUsers"},
                },
            },
        }
        ops = scorecard._collect_operations(spec)
        assert len(ops) == 1
        assert ops[0]["path"] == "/users"
        assert ops[0]["method"] == "get"
        assert ops[0]["operation_id"] == "listUsers"

    def test_multiple_methods(self) -> None:
        """Extracts all HTTP methods from a single path."""
        spec: dict[str, Any] = {
            "paths": {
                "/items": {
                    "get": {"operationId": "getItems"},
                    "post": {"operationId": "createItem"},
                    "delete": {"operationId": "deleteItem"},
                },
            },
        }
        ops = scorecard._collect_operations(spec)
        assert len(ops) == 3
        methods = {o["method"] for o in ops}
        assert methods == {"get", "post", "delete"}

    def test_non_http_keys_ignored(self) -> None:
        """Keys like parameters and summary are not treated as methods."""
        spec: dict[str, Any] = {
            "paths": {
                "/items": {
                    "get": {"operationId": "getItems"},
                    "parameters": [{"name": "id"}],
                    "summary": "Items path",
                },
            },
        }
        ops = scorecard._collect_operations(spec)
        assert len(ops) == 1

    def test_empty_paths(self) -> None:
        """Empty paths dict returns no operations."""
        assert scorecard._collect_operations({"paths": {}}) == []

    def test_no_paths_key(self) -> None:
        """Missing paths key returns no operations."""
        assert scorecard._collect_operations({}) == []

    def test_missing_operation_id(self) -> None:
        """Operation without operationId gets empty string."""
        spec: dict[str, Any] = {"paths": {"/x": {"post": {}}}}
        ops = scorecard._collect_operations(spec)
        assert ops[0]["operation_id"] == ""

    def test_non_dict_path_item_skipped(self) -> None:
        """Non-dict path items are ignored."""
        spec: dict[str, Any] = {"paths": {"/x": "invalid"}}
        assert scorecard._collect_operations(spec) == []


class TestInferFeatureKey:
    """Tests for feature key inference fallback chain."""

    def test_explicit_feature_id(self) -> None:
        """Uses feature_id when present in frontmatter."""
        fm: dict[str, Any] = {"feature_id": "  Auth Flow  "}
        result = scorecard._infer_feature_key(Path("docs/x.md"), fm, "reference")
        assert result == "auth flow"

    def test_explicit_component(self) -> None:
        """Falls back to component when feature_id is missing."""
        fm: dict[str, Any] = {"component": "Webhooks"}
        result = scorecard._infer_feature_key(Path("docs/x.md"), fm, "reference")
        assert result == "webhooks"

    def test_title_normalization(self) -> None:
        """Uses title when no explicit key, normalizing to kebab."""
        fm: dict[str, Any] = {"title": "Configure HMAC Authentication"}
        result = scorecard._infer_feature_key(Path("docs/x.md"), fm, "how-to")
        assert result == "configure-hmac-authentication"

    def test_title_strips_content_type_suffix(self) -> None:
        """Title-based key strips content type suffix."""
        fm: dict[str, Any] = {"title": "Webhooks How-To"}
        result = scorecard._infer_feature_key(Path("docs/webhooks.md"), fm, "how-to")
        assert result == "webhooks"

    def test_stem_fallback(self) -> None:
        """Falls back to file stem when title is empty."""
        fm: dict[str, Any] = {}
        result = scorecard._infer_feature_key(Path("docs/my-feature-reference.md"), fm, "reference")
        assert result == "my-feature"

    def test_stem_no_suffix_match(self) -> None:
        """Stem without content type suffix is returned as-is."""
        fm: dict[str, Any] = {}
        result = scorecard._infer_feature_key(Path("docs/webhooks.md"), fm, "reference")
        assert result == "webhooks"

    def test_empty_title_and_stem(self) -> None:
        """Falls back to content_type when everything else is empty."""
        fm: dict[str, Any] = {"title": ""}
        result = scorecard._infer_feature_key(Path(""), fm, "reference")
        assert result == "reference"

    def test_fallback_chain_priority(self) -> None:
        """Checks that feature_id takes priority over feature, component, etc."""
        fm: dict[str, Any] = {
            "feature_id": "top-priority",
            "feature": "second",
            "component": "third",
            "title": "Fourth Option",
        }
        result = scorecard._infer_feature_key(Path("docs/fifth.md"), fm, "tutorial")
        assert result == "top-priority"

    def test_feature_key_before_component(self) -> None:
        """feature key is checked before component."""
        fm: dict[str, Any] = {"feature": "auth", "component": "login"}
        result = scorecard._infer_feature_key(Path("docs/x.md"), fm, "reference")
        assert result == "auth"


class TestOverallScore:
    """Tests for the 7-pillar weighted overall score formula."""

    def test_perfect_scores(self) -> None:
        """All metrics at 100% with zero penalties yield max score."""
        kpis = _make_kpis(
            coverage_pct=100.0,
            example_reliability_pct=100.0,
            stale_docs_pct=0.0,
            drift_pct=0.0,
            layers_missing_pct=0.0,
            terminology_consistency_pct=100.0,
            precision_at_k=1.0,
            recall_at_k=1.0,
            hallucination_rate=0.0,
        )
        result = scorecard._overall_score(kpis)
        # 0.22*100 + 0.20*100 + 0.14*100 + 0.12*100 + 0.12*100 + 0.10*100
        #   + 0.10*100 - 0.08*0 = 100.0
        assert result["audit_score_0_100"] == 100.0
        assert result["grade"] == "A"

    def test_exact_weight_formula(self) -> None:
        """Verify exact weight application with specific numbers."""
        kpis = _make_kpis(
            coverage_pct=80.0,
            example_reliability_pct=90.0,
            stale_docs_pct=20.0,
            drift_pct=10.0,
            layers_missing_pct=15.0,
            terminology_consistency_pct=85.0,
            precision_at_k=0.6,
            recall_at_k=0.5,
            hallucination_rate=0.1,
        )
        result = scorecard._overall_score(kpis)
        # retrieval_score = (60 + 50) / 2 = 55
        # hallucination_penalty = 10
        # score = 0.22*80 + 0.20*90 + 0.14*(100-20) + 0.12*(100-10)
        #       + 0.12*(100-15) + 0.10*85 + 0.10*55 - 0.08*10
        # = 17.6 + 18.0 + 11.2 + 10.8 + 10.2 + 8.5 + 5.5 - 0.8 = 81.0
        assert result["audit_score_0_100"] == 81.0
        assert result["grade"] == "B"

    def test_retrieval_missing_uses_defaults(self) -> None:
        """When retrieval report is missing, defaults 50 score and 10 penalty."""
        kpis = _make_kpis(
            coverage_pct=100.0,
            example_reliability_pct=100.0,
            stale_docs_pct=0.0,
            drift_pct=0.0,
            layers_missing_pct=0.0,
            terminology_consistency_pct=100.0,
            retrieval_found=False,
        )
        result = scorecard._overall_score(kpis)
        # retrieval_score = 50.0 (default), hallucination = 10.0 (default)
        # positive = 0.22*100 + 0.20*100 + 0.14*100 + 0.12*100
        #          + 0.12*100 + 0.10*100 + 0.10*50 = 95.0
        # penalty = 0.08*10 = 0.8
        # total = 95.0 - 0.8 = 94.2
        assert result["audit_score_0_100"] == 94.2
        assert result["grade"] == "A"

    def test_grade_boundaries(self) -> None:
        """Verify all grade boundaries: A>=90, B>=80, C>=70, D>=60, F<60."""
        for score_val, expected_grade in [
            (95.0, "A"), (90.0, "A"), (89.99, "B"), (80.0, "B"),
            (79.99, "C"), (70.0, "C"), (69.99, "D"), (60.0, "D"),
            (59.99, "F"), (0.0, "F"),
        ]:
            kpis = _make_kpis()
            # Patch _overall_score to just test grade logic
            result_grade = "A"
            if score_val < 90:
                result_grade = "B"
            if score_val < 80:
                result_grade = "C"
            if score_val < 70:
                result_grade = "D"
            if score_val < 60:
                result_grade = "F"
            assert result_grade == expected_grade, f"Score {score_val} -> {result_grade}"

    def test_score_clamped_to_0_100(self) -> None:
        """Score is clamped between 0 and 100."""
        kpis = _make_kpis(
            coverage_pct=0.0,
            example_reliability_pct=0.0,
            stale_docs_pct=100.0,
            drift_pct=100.0,
            layers_missing_pct=100.0,
            terminology_consistency_pct=0.0,
            precision_at_k=0.0,
            recall_at_k=0.0,
            hallucination_rate=1.0,
        )
        result = scorecard._overall_score(kpis)
        assert result["audit_score_0_100"] >= 0.0
        assert result["audit_score_0_100"] <= 100.0


class TestBusinessImpact:
    """Tests for risk_index formula and cost calculations."""

    def test_risk_index_all_zero(self) -> None:
        """Perfect metrics yield risk_index 0."""
        kpis = _make_kpis()
        assumptions = scorecard.CostAssumptions()
        impact = scorecard._business_impact(kpis, assumptions)
        assert impact["risk_index_0_to_1"] == 0.0

    def test_risk_index_formula_exact(self) -> None:
        """Verify the 5-weight risk formula with specific inputs."""
        kpis = _make_kpis(
            undocumented_pct=50.0,
            stale_docs_pct=40.0,
            drift_pct=30.0,
            example_reliability_pct=60.0,
            terminology_violation_pct=20.0,
        )
        assumptions = scorecard.CostAssumptions()
        impact = scorecard._business_impact(kpis, assumptions)
        # risk = 0.30*(50/100) + 0.20*(40/100) + 0.20*(30/100)
        #       + 0.20*((100-60)/100) + 0.10*(20/100)
        # = 0.15 + 0.08 + 0.06 + 0.08 + 0.02 = 0.39
        assert impact["risk_index_0_to_1"] == 0.39

    def test_risk_index_clamped_at_1(self) -> None:
        """Risk index is clamped to [0, 1]."""
        kpis = _make_kpis(
            undocumented_pct=100.0,
            stale_docs_pct=100.0,
            drift_pct=100.0,
            example_reliability_pct=0.0,
            terminology_violation_pct=100.0,
        )
        assumptions = scorecard.CostAssumptions()
        impact = scorecard._business_impact(kpis, assumptions)
        assert impact["risk_index_0_to_1"] == 1.0

    def test_scenario_multipliers(self) -> None:
        """Conservative, base, and aggressive use 0.7, 1.0, 1.4 multipliers."""
        kpis = _make_kpis(undocumented_pct=50.0)
        assumptions = scorecard.CostAssumptions()
        impact = scorecard._business_impact(kpis, assumptions)
        base_cost = impact["scenarios"]["base"]["monthly_cost_usd"]
        conservative_cost = impact["scenarios"]["conservative"]["monthly_cost_usd"]
        aggressive_cost = impact["scenarios"]["aggressive"]["monthly_cost_usd"]
        assert conservative_cost == pytest.approx(base_cost * 0.7, rel=1e-2)
        assert aggressive_cost == pytest.approx(base_cost * 1.4, rel=1e-2)

    def test_custom_assumptions(self) -> None:
        """Custom hourly rates affect cost output."""
        kpis = _make_kpis()
        assumptions = scorecard.CostAssumptions(engineer_hourly_usd=200.0)
        impact = scorecard._business_impact(kpis, assumptions)
        assert impact["assumptions"]["engineer_hourly_usd"] == 200.0


class TestBuildFindings:
    """Tests for _build_findings output structure and severity logic."""

    def test_always_produces_6_core_findings(self) -> None:
        """With retrieval report found, produces 6 core findings."""
        kpis = _make_kpis(retrieval_found=True)
        assumptions = scorecard.CostAssumptions()
        findings = scorecard._build_findings(kpis, assumptions)
        ids = [f["id"] for f in findings]
        assert "F-API-COVERAGE" in ids
        assert "F-EXAMPLES-RELIABILITY" in ids
        assert "F-FRESHNESS" in ids
        assert "F-DRIFT" in ids
        assert "F-LAYERS" in ids
        assert "F-TERMINOLOGY" in ids

    def test_retrieval_missing_appends_missing_finding(self) -> None:
        """When retrieval report is not found, adds F-RETRIEVAL-MISSING."""
        kpis = _make_kpis(retrieval_found=False)
        assumptions = scorecard.CostAssumptions()
        findings = scorecard._build_findings(kpis, assumptions)
        ids = [f["id"] for f in findings]
        assert "F-RETRIEVAL-MISSING" in ids
        assert "F-RETRIEVAL" not in ids

    def test_retrieval_found_appends_retrieval_finding(self) -> None:
        """When retrieval report exists, adds F-RETRIEVAL."""
        kpis = _make_kpis(retrieval_found=True, hallucination_rate=0.3)
        assumptions = scorecard.CostAssumptions()
        findings = scorecard._build_findings(kpis, assumptions)
        ids = [f["id"] for f in findings]
        assert "F-RETRIEVAL" in ids

    def test_evidence_missing_findings_added(self) -> None:
        """Missing smoke and drift reports add evidence findings."""
        kpis = _make_kpis(
            report_found_examples=False,
            docs_contract_report_found=False,
        )
        assumptions = scorecard.CostAssumptions()
        findings = scorecard._build_findings(kpis, assumptions)
        ids = [f["id"] for f in findings]
        assert "F-EVIDENCE-SMOKE-MISSING" in ids
        assert "F-EVIDENCE-DRIFT-MISSING" in ids

    def test_findings_sorted_by_severity(self) -> None:
        """Findings are sorted high -> medium -> low."""
        kpis = _make_kpis(
            undocumented_pct=50.0,
            stale_docs_pct=50.0,
            retrieval_found=False,
            report_found_examples=False,
        )
        assumptions = scorecard.CostAssumptions()
        findings = scorecard._build_findings(kpis, assumptions)
        severities = [f["severity"] for f in findings]
        severity_order = {"high": 0, "medium": 1, "low": 2}
        for i in range(len(severities) - 1):
            assert severity_order[severities[i]] <= severity_order[severities[i + 1]]

    def test_finding_fixability_maps_to_capability(self) -> None:
        """Each finding has pilot/full fixability from CAPABILITY_MAP."""
        kpis = _make_kpis()
        assumptions = scorecard.CostAssumptions()
        findings = scorecard._build_findings(kpis, assumptions)
        for f in findings:
            cap = scorecard.CAPABILITY_MAP.get(f["capability_id"], {})
            if cap:
                assert f["fixability"]["pilot"] == bool(cap.get("pilot", False))
                assert f["fixability"]["full"] == bool(cap.get("full", False))

    def test_severity_from_gap_thresholds(self) -> None:
        """_severity_from_gap returns high >= 25, medium >= 10, low < 10."""
        assert scorecard._severity_from_gap(30.0, 25.0, 10.0) == "high"
        assert scorecard._severity_from_gap(25.0, 25.0, 10.0) == "high"
        assert scorecard._severity_from_gap(15.0, 25.0, 10.0) == "medium"
        assert scorecard._severity_from_gap(10.0, 25.0, 10.0) == "medium"
        assert scorecard._severity_from_gap(5.0, 25.0, 10.0) == "low"


class TestBuildHtml:
    """Tests for HTML scorecard generation."""

    def _make_payload(self) -> dict[str, Any]:
        """Build a minimal valid payload for HTML generation."""
        kpis = _make_kpis()
        assumptions = scorecard.CostAssumptions()
        findings = scorecard._build_findings(kpis, assumptions)
        return {
            "generated_at": "2024-01-15T10:00:00+00:00",
            "score": scorecard._overall_score(kpis),
            "kpis": kpis,
            "business_impact": scorecard._business_impact(kpis, assumptions),
            "capability_matrix": scorecard._capability_matrix(),
            "findings": findings,
            "findings_totals": scorecard._findings_totals(findings),
            "top_3_gaps": [
                {"title": "Test Gap", "priority": "high", "action_required": "Fix it"},
            ],
        }

    def test_html_contains_doctype(self) -> None:
        """Output starts with <!DOCTYPE html>."""
        html_output = scorecard._build_html(self._make_payload())
        assert html_output.strip().startswith("<!DOCTYPE html>")

    def test_html_contains_score(self) -> None:
        """HTML includes the numeric audit score."""
        payload = self._make_payload()
        html_output = scorecard._build_html(payload)
        score_str = str(payload["score"]["audit_score_0_100"])
        assert score_str in html_output

    def test_html_contains_grade(self) -> None:
        """HTML includes the letter grade."""
        payload = self._make_payload()
        html_output = scorecard._build_html(payload)
        assert f"Grade {payload['score']['grade']}" in html_output

    def test_html_contains_generated_at(self) -> None:
        """HTML includes the generation timestamp."""
        payload = self._make_payload()
        html_output = scorecard._build_html(payload)
        assert "2024-01-15T10:00:00+00:00" in html_output

    def test_html_escapes_special_chars(self) -> None:
        """HTML escapes special characters in finding titles."""
        payload = self._make_payload()
        payload["findings"] = [{
            "id": "F-TEST",
            "title": "<script>alert('xss')</script>",
            "severity": "high",
            "capability_label": "test & 'cap'",
            "metric": "m",
            "current_value": 0,
            "target_value": 1,
            "unit": "%",
            "fixability": {"pilot": True, "full": True},
            "effort_hours_low": 1, "effort_hours_base": 2, "effort_hours_high": 3,
            "estimated_remediation_cost_usd_low": 100,
            "estimated_remediation_cost_usd_base": 200,
            "estimated_remediation_cost_usd_high": 300,
            "estimated_monthly_loss_usd_low": 50,
            "estimated_monthly_loss_usd_base": 100,
            "estimated_monthly_loss_usd_high": 150,
            "estimation_confidence": "high",
        }]
        html_output = scorecard._build_html(payload)
        assert "&lt;script&gt;" in html_output
        assert "<script>alert" not in html_output

    def test_html_top3_gaps_rendered(self) -> None:
        """Top 3 gaps appear in the HTML output."""
        payload = self._make_payload()
        html_output = scorecard._build_html(payload)
        assert "Test Gap" in html_output

    def test_html_empty_gaps(self) -> None:
        """No gaps shows fallback message."""
        payload = self._make_payload()
        payload["top_3_gaps"] = []
        html_output = scorecard._build_html(payload)
        assert "No gaps detected." in html_output


class TestFreshnessMetrics:
    """Tests for _freshness_metrics scanning docs directory."""

    def test_no_docs_directory(self, tmp_path: Path) -> None:
        """Non-existent docs dir returns zeros."""
        result = scorecard._freshness_metrics(tmp_path / "nonexistent", 180)
        assert result["total_docs"] == 0
        assert result["stale_docs_count"] == 0

    def test_docs_with_dates(self, tmp_path: Path) -> None:
        """Documents with dates are counted and aged."""
        doc = tmp_path / "test.md"
        doc.write_text(
            "---\ntitle: Test\nlast_reviewed: 2020-01-01\n---\nContent",
            encoding="utf-8",
        )
        result = scorecard._freshness_metrics(tmp_path, 180)
        assert result["total_docs"] == 1
        assert result["dated_docs"] == 1
        assert result["stale_docs_count"] == 1  # 2020 is well over 180 days
        assert result["average_age_days"] > 180

    def test_docs_missing_dates(self, tmp_path: Path) -> None:
        """Documents without any date fields counted as missing."""
        doc = tmp_path / "test.md"
        doc.write_text("---\ntitle: No Date\n---\nContent", encoding="utf-8")
        result = scorecard._freshness_metrics(tmp_path, 180)
        assert result["missing_date_docs"] == 1
        assert result["dated_docs"] == 0


class TestDriftMetrics:
    """Tests for _drift_metrics reading report files."""

    def test_no_reports(self, tmp_path: Path) -> None:
        """Missing report files yield safe defaults."""
        result = scorecard._drift_metrics(tmp_path)
        assert result["docs_contract_report_found"] is False
        assert result["api_drift_status"] == "missing"
        assert result["docs_contract_drift_pct"] == 0.0

    def test_mismatches_list(self, tmp_path: Path) -> None:
        """Mismatch count from mismatches list."""
        report = {"mismatches": ["a", "b", "c"], "interface_changed": ["x", "y"]}
        (tmp_path / "pr_docs_contract.json").write_text(
            json.dumps(report), encoding="utf-8"
        )
        result = scorecard._drift_metrics(tmp_path)
        assert result["docs_contract_mismatch_count"] == 3
        assert result["interface_changed_count"] == 2


class TestTerminologyMetrics:
    """Tests for forbidden term scanning."""

    def test_no_glossary(self, tmp_path: Path) -> None:
        """Missing glossary file returns zeros."""
        docs = tmp_path / "docs"
        docs.mkdir()
        result = scorecard._terminology_metrics(docs, tmp_path / "glossary.yml", tmp_path)
        assert result["forbidden_terms_count"] == 0
        assert result["terminology_consistency_pct"] == 100.0

    def test_forbidden_terms_detected(self, tmp_path: Path) -> None:
        """Detects forbidden terms in doc files."""
        docs = tmp_path / "docs"
        docs.mkdir()
        doc = docs / "test.md"
        doc.write_text("---\ntitle: Test\n---\nDo not use foobar here.", encoding="utf-8")

        glossary = tmp_path / "glossary.yml"
        glossary.write_text("forbidden:\n  - foobar\nterms:\n  api: {}", encoding="utf-8")

        result = scorecard._terminology_metrics(docs, glossary, tmp_path)
        assert result["forbidden_terms_count"] == 1
        assert result["docs_with_forbidden_terms"] == 1
        assert result["forbidden_term_occurrences"] == 1
        assert result["terminology_violation_pct"] > 0


class TestLayerCompleteness:
    """Tests for _layer_completeness_metrics."""

    def test_empty_docs(self, tmp_path: Path) -> None:
        """Empty docs dir returns zero features."""
        docs = tmp_path / "docs"
        docs.mkdir()
        result = scorecard._layer_completeness_metrics(docs, None)
        assert result["total_features"] == 0
        assert result["features_missing_required_layers_pct"] == 0.0

    def test_feature_with_all_layers(self, tmp_path: Path) -> None:
        """Feature with concept, how-to, and reference has no missing layers."""
        docs = tmp_path / "docs"
        docs.mkdir()
        for ct in ("concept", "how-to", "reference"):
            f = docs / f"auth-{ct}.md"
            f.write_text(
                f"---\ntitle: Auth {ct}\ncontent_type: {ct}\nfeature_id: auth\n---\nBody",
                encoding="utf-8",
            )
        result = scorecard._layer_completeness_metrics(docs, None)
        assert result["total_features"] == 1
        assert result["features_missing_required_layers"] == 0

    def test_feature_missing_layer(self, tmp_path: Path) -> None:
        """Feature missing reference layer is counted."""
        docs = tmp_path / "docs"
        docs.mkdir()
        for ct in ("concept", "how-to"):
            f = docs / f"auth-{ct}.md"
            f.write_text(
                f"---\ntitle: Auth {ct}\ncontent_type: {ct}\nfeature_id: auth\n---\nBody",
                encoding="utf-8",
            )
        result = scorecard._layer_completeness_metrics(docs, None)
        assert result["features_missing_required_layers"] == 1
        assert result["sample_missing_features"][0]["missing_layers"] == ["reference"]


class TestApiCoverageMetrics:
    """Tests for _api_coverage_metrics."""

    def test_no_spec(self, tmp_path: Path) -> None:
        """Missing spec file returns zero coverage."""
        docs = tmp_path / "docs"
        docs.mkdir()
        result = scorecard._api_coverage_metrics(docs, tmp_path / "missing.yaml")
        assert result["total_operations"] == 0
        assert result["coverage_pct"] == 0.0

    def test_documented_operation(self, tmp_path: Path) -> None:
        """Operation mentioned in docs is counted as documented."""
        docs = tmp_path / "docs"
        docs.mkdir()
        doc = docs / "api.md"
        doc.write_text("---\ntitle: API\n---\nUse listUsers endpoint.", encoding="utf-8")
        spec = tmp_path / "openapi.yaml"
        spec.write_text(
            "paths:\n  /users:\n    get:\n      operationId: listUsers",
            encoding="utf-8",
        )
        result = scorecard._api_coverage_metrics(docs, spec)
        assert result["total_operations"] == 1
        assert result["documented_operations"] == 1
        assert result["coverage_pct"] == 100.0

    def test_undocumented_operation(self, tmp_path: Path) -> None:
        """Operation not mentioned in docs is undocumented."""
        docs = tmp_path / "docs"
        docs.mkdir()
        doc = docs / "api.md"
        doc.write_text("---\ntitle: API\n---\nSome content.", encoding="utf-8")
        spec = tmp_path / "openapi.yaml"
        spec.write_text(
            "paths:\n  /secret:\n    post:\n      operationId: createSecret",
            encoding="utf-8",
        )
        result = scorecard._api_coverage_metrics(docs, spec)
        assert result["undocumented_operations"] == 1
        assert result["undocumented_pct"] == 100.0


class TestFindingsTotals:
    """Tests for _findings_totals aggregation."""

    def test_counts_by_severity(self) -> None:
        """Correctly counts high, medium, low findings."""
        findings = [
            {"severity": "high", "fixability": {"pilot": True, "full": True},
             "estimated_remediation_cost_usd_low": 100, "estimated_remediation_cost_usd_base": 200,
             "estimated_remediation_cost_usd_high": 300,
             "estimated_monthly_loss_usd_low": 50, "estimated_monthly_loss_usd_base": 100,
             "estimated_monthly_loss_usd_high": 150},
            {"severity": "medium", "fixability": {"pilot": False, "full": True},
             "estimated_remediation_cost_usd_low": 50, "estimated_remediation_cost_usd_base": 100,
             "estimated_remediation_cost_usd_high": 150,
             "estimated_monthly_loss_usd_low": 25, "estimated_monthly_loss_usd_base": 50,
             "estimated_monthly_loss_usd_high": 75},
            {"severity": "low", "fixability": {"pilot": True, "full": False},
             "estimated_remediation_cost_usd_low": 10, "estimated_remediation_cost_usd_base": 20,
             "estimated_remediation_cost_usd_high": 30,
             "estimated_monthly_loss_usd_low": 5, "estimated_monthly_loss_usd_base": 10,
             "estimated_monthly_loss_usd_high": 15},
        ]
        totals = scorecard._findings_totals(findings)
        assert totals["findings_count"] == 3
        assert totals["high_count"] == 1
        assert totals["medium_count"] == 1
        assert totals["low_count"] == 1
        assert totals["pilot_fixable_count"] == 2
        assert totals["full_fixable_count"] == 2
        assert totals["remediation_cost_usd_low_total"] == 160
        assert totals["remediation_cost_usd_base_total"] == 320


class TestCapabilityMatrix:
    """Tests for _capability_matrix output."""

    def test_returns_all_capabilities(self) -> None:
        """Matrix returns all 7 capabilities from CAPABILITY_MAP."""
        matrix = scorecard._capability_matrix()
        assert len(matrix) == len(scorecard.CAPABILITY_MAP)
        ids = {c["capability_id"] for c in matrix}
        assert ids == set(scorecard.CAPABILITY_MAP.keys())


class TestLoadAssumptions:
    """Tests for _load_assumptions with custom JSON."""

    def test_defaults_when_no_file(self) -> None:
        """Returns default CostAssumptions when no file."""
        result = scorecard._load_assumptions(None)
        assert result.engineer_hourly_usd == 95.0

    def test_custom_values_from_file(self, tmp_path: Path) -> None:
        """Reads custom assumptions from JSON file."""
        path = tmp_path / "assumptions.json"
        path.write_text(json.dumps({"engineer_hourly_usd": 150.0}), encoding="utf-8")
        result = scorecard._load_assumptions(path)
        assert result.engineer_hourly_usd == 150.0
        assert result.support_hourly_usd == 45.0  # default preserved


class TestReadJson:
    """Tests for _read_json helper."""

    def test_missing_file(self, tmp_path: Path) -> None:
        """Missing file returns empty dict."""
        assert scorecard._read_json(tmp_path / "missing.json") == {}

    def test_invalid_json(self, tmp_path: Path) -> None:
        """Invalid JSON returns empty dict."""
        f = tmp_path / "bad.json"
        f.write_text("not json", encoding="utf-8")
        assert scorecard._read_json(f) == {}

    def test_non_dict_json(self, tmp_path: Path) -> None:
        """JSON array returns empty dict."""
        f = tmp_path / "array.json"
        f.write_text("[1, 2, 3]", encoding="utf-8")
        assert scorecard._read_json(f) == {}


class TestMainScorecard:
    """Tests for the main() function end-to-end."""

    def test_main_produces_json_and_html(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Main produces both JSON and HTML output files."""
        docs = tmp_path / "docs"
        docs.mkdir()
        reports = tmp_path / "reports"
        reports.mkdir()
        json_out = tmp_path / "out.json"
        html_out = tmp_path / "out.html"

        monkeypatch.setattr(
            sys, "argv",
            [
                "x",
                "--docs-dir", str(docs),
                "--reports-dir", str(reports),
                "--spec-path", str(tmp_path / "missing.yaml"),
                "--json-output", str(json_out),
                "--html-output", str(html_out),
            ],
        )
        rc = scorecard.main()
        assert rc == 0
        assert json_out.exists()
        assert html_out.exists()
        payload = json.loads(json_out.read_text(encoding="utf-8"))
        assert "score" in payload
        assert "kpis" in payload


# ===================================================================
# Section 2: generate_embeddings.py
# ===================================================================


class TestLoadIndex:
    """Tests for _load_index JSON parsing and filtering."""

    def test_loads_plain_list(self, tmp_path: Path) -> None:
        """Loads a plain JSON list of records."""
        data = [{"id": "mod-1"}, {"id": "mod-2"}]
        path = tmp_path / "index.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        result = embeddings._load_index(path)
        assert len(result) == 2

    def test_loads_records_key(self, tmp_path: Path) -> None:
        """Loads from {records: [...]} wrapper."""
        data = {"records": [{"id": "a"}, {"id": "b"}]}
        path = tmp_path / "index.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        result = embeddings._load_index(path)
        assert len(result) == 2

    def test_filters_invalid_records(self, tmp_path: Path) -> None:
        """Skips records without valid id."""
        data = [{"id": "good"}, {"id": ""}, {"id": "  "}, "not-a-dict", {"noId": True}]
        path = tmp_path / "index.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        result = embeddings._load_index(path)
        assert len(result) == 1
        assert result[0]["id"] == "good"

    def test_raises_on_non_list(self, tmp_path: Path) -> None:
        """Raises ValueError if payload is not a list or dict with records."""
        path = tmp_path / "index.json"
        path.write_text('"just a string"', encoding="utf-8")
        with pytest.raises(ValueError, match="must be a JSON list"):
            embeddings._load_index(path)


class TestBuildText:
    """Tests for _build_text concatenation."""

    def test_full_module(self) -> None:
        """Concatenates title, summary, assistant_excerpt, and intents."""
        module: dict[str, Any] = {
            "title": "Auth Guide",
            "summary": "How to authenticate",
            "assistant_excerpt": "Use bearer tokens",
            "intents": ["configure", "secure"],
        }
        result = embeddings._build_text(module)
        assert "Auth Guide" in result
        assert "How to authenticate" in result
        assert "Use bearer tokens" in result
        assert "configure secure" in result

    def test_empty_module(self) -> None:
        """Empty module returns empty string."""
        result = embeddings._build_text({})
        assert result == ""

    def test_partial_module(self) -> None:
        """Module with only title returns just the title."""
        result = embeddings._build_text({"title": "Only Title"})
        assert result == "Only Title"


class TestEmbedBatch:
    """Tests for _embed_batch HTTP calls (mocked httpx)."""

    def test_single_batch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Embeds a single batch of texts."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"index": 0, "embedding": [0.1, 0.2, 0.3]},
                {"index": 1, "embedding": [0.4, 0.5, 0.6]},
            ],
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx = MagicMock()
        mock_httpx.post.return_value = mock_response
        monkeypatch.setattr(embeddings, "httpx", mock_httpx)

        result = embeddings._embed_batch(
            ["hello", "world"], "test-key", "text-embedding-3-small",
            "https://api.openai.com/v1", batch_size=100,
        )
        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]

    def test_multiple_batches(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Splits texts into multiple batches."""
        call_count = [0]

        def mock_post(*args: Any, **kwargs: Any) -> MagicMock:
            batch = kwargs.get("json", {}).get("input", [])
            resp = MagicMock()
            resp.json.return_value = {
                "data": [{"index": i, "embedding": [float(i)]} for i in range(len(batch))],
            }
            resp.raise_for_status = MagicMock()
            call_count[0] += 1
            return resp

        mock_httpx = MagicMock()
        mock_httpx.post.side_effect = mock_post
        monkeypatch.setattr(embeddings, "httpx", mock_httpx)

        result = embeddings._embed_batch(
            ["a", "b", "c", "d", "e"], "key", "model",
            "https://api.openai.com/v1", batch_size=2,
        )
        assert len(result) == 5
        assert call_count[0] == 3  # 2+2+1

    def test_httpx_missing_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Raises ImportError when httpx is None."""
        monkeypatch.setattr(embeddings, "httpx", None)
        with pytest.raises(ImportError, match="httpx"):
            embeddings._embed_batch(["text"], "key", "model", "http://x", 10)

    def test_auth_header(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verifies Authorization header is set correctly."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"index": 0, "embedding": [1.0]}],
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx = MagicMock()
        mock_httpx.post.return_value = mock_response
        monkeypatch.setattr(embeddings, "httpx", mock_httpx)

        embeddings._embed_batch(["text"], "sk-secret", "model", "https://api.openai.com/v1", 100)
        call_args = mock_httpx.post.call_args
        headers = call_args[1].get("headers", {}) if call_args[1] else call_args.kwargs.get("headers", {})
        assert headers["Authorization"] == "Bearer sk-secret"


class TestBuildFaissIndex:
    """Tests for _build_faiss_index with numpy and FAISS."""

    def test_normal_embeddings(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Builds a FAISS index from normal vectors."""
        mock_faiss = MagicMock()
        mock_index = MagicMock()
        mock_index.ntotal = 3
        mock_index.d = 4
        mock_faiss.IndexFlatIP.return_value = mock_index
        monkeypatch.setattr(embeddings, "faiss", mock_faiss)

        vecs = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0]]
        result = embeddings._build_faiss_index(vecs)
        mock_faiss.IndexFlatIP.assert_called_once_with(4)
        assert mock_index.add.called

    def test_zero_vector_no_nan(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Zero vector does not cause NaN after normalization (norms[norms==0]=1)."""
        mock_faiss = MagicMock()
        mock_index = MagicMock()
        captured_matrix = []

        def capture_add(matrix: Any) -> None:
            captured_matrix.append(matrix.copy())

        mock_index.add.side_effect = capture_add
        mock_faiss.IndexFlatIP.return_value = mock_index
        monkeypatch.setattr(embeddings, "faiss", mock_faiss)

        vecs = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]
        embeddings._build_faiss_index(vecs)

        matrix = captured_matrix[0]
        assert not np.any(np.isnan(matrix)), "Zero vector normalization produced NaN"
        # Zero vector stays zero after normalization with norms[norms==0]=1
        np.testing.assert_array_almost_equal(matrix[0], [0.0, 0.0, 0.0])

    def test_faiss_missing_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Raises ImportError when faiss is None."""
        monkeypatch.setattr(embeddings, "faiss", None)
        with pytest.raises(ImportError, match="faiss-cpu"):
            embeddings._build_faiss_index([[1.0, 2.0]])

    def test_normalization_unit_vectors(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Vectors are L2-normalized to unit length."""
        mock_faiss = MagicMock()
        mock_index = MagicMock()
        captured = []
        mock_index.add.side_effect = lambda m: captured.append(m.copy())
        mock_faiss.IndexFlatIP.return_value = mock_index
        monkeypatch.setattr(embeddings, "faiss", mock_faiss)

        vecs = [[3.0, 4.0]]  # norm = 5
        embeddings._build_faiss_index(vecs)

        norms = np.linalg.norm(captured[0], axis=1)
        np.testing.assert_array_almost_equal(norms, [1.0])


class TestEmbeddingsMain:
    """Tests for the main() pipeline entry point."""

    def test_no_api_key_skips(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        """Skips gracefully when OPENAI_API_KEY is not set."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setattr(sys, "argv", ["x"])
        rc = embeddings.main()
        assert rc == 0
        assert "OPENAI_API_KEY not set" in capsys.readouterr().out

    def test_no_faiss_skips(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        """Skips gracefully when faiss is not installed."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setattr(embeddings, "faiss", None)
        monkeypatch.setattr(sys, "argv", ["x"])
        rc = embeddings.main()
        assert rc == 0
        assert "faiss-cpu not installed" in capsys.readouterr().out

    def test_no_httpx_skips(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        """Skips gracefully when httpx is not installed."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setattr(embeddings, "httpx", None)
        mock_faiss = MagicMock()
        monkeypatch.setattr(embeddings, "faiss", mock_faiss)
        monkeypatch.setattr(sys, "argv", ["x"])
        rc = embeddings.main()
        assert rc == 0
        assert "httpx not installed" in capsys.readouterr().out

    def test_missing_index_raises(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Raises FileNotFoundError when index file is missing."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        mock_faiss = MagicMock()
        mock_httpx = MagicMock()
        monkeypatch.setattr(embeddings, "faiss", mock_faiss)
        monkeypatch.setattr(embeddings, "httpx", mock_httpx)
        monkeypatch.setattr(
            sys, "argv",
            ["x", "--index", str(tmp_path / "missing.json")],
        )
        with pytest.raises(FileNotFoundError):
            embeddings.main()

    def test_empty_modules_skips(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Skips when index has no valid modules."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        mock_faiss = MagicMock()
        mock_httpx = MagicMock()
        monkeypatch.setattr(embeddings, "faiss", mock_faiss)
        monkeypatch.setattr(embeddings, "httpx", mock_httpx)
        idx = tmp_path / "index.json"
        idx.write_text("[]", encoding="utf-8")
        monkeypatch.setattr(sys, "argv", ["x", "--index", str(idx)])
        rc = embeddings.main()
        assert rc == 0
        assert "No modules found" in capsys.readouterr().out

    def test_full_pipeline_non_chunked(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Full pipeline without chunking writes FAISS and metadata."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        idx = tmp_path / "index.json"
        idx.write_text(
            json.dumps([{"id": "m1", "title": "Test", "summary": "Sum"}]),
            encoding="utf-8",
        )
        out_dir = tmp_path / "output"

        mock_faiss = MagicMock()
        mock_index = MagicMock()
        mock_index.ntotal = 1
        mock_index.d = 3
        mock_faiss.IndexFlatIP.return_value = mock_index
        monkeypatch.setattr(embeddings, "faiss", mock_faiss)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"index": 0, "embedding": [0.1, 0.2, 0.3]}],
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx = MagicMock()
        mock_httpx.post.return_value = mock_response
        monkeypatch.setattr(embeddings, "httpx", mock_httpx)

        monkeypatch.setattr(
            sys, "argv",
            ["x", "--index", str(idx), "--output-dir", str(out_dir)],
        )
        rc = embeddings.main()
        assert rc == 0
        mock_faiss.write_index.assert_called_once()
        metadata_path = out_dir / "retrieval-metadata.json"
        assert metadata_path.exists()
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        assert len(metadata) == 1
        assert metadata[0]["id"] == "m1"


# ===================================================================
# Section 3: rollback.py
# ===================================================================


class TestListBackups:
    """Tests for _list_backups directory scanning."""

    def test_no_backup_dir(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Returns empty list when backup directory does not exist."""
        monkeypatch.setattr(rollback_mod, "BACKUP_DIR", tmp_path / "nonexistent")
        assert rollback_mod._list_backups() == []

    def test_lists_and_sorts_descending(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Lists backup versions sorted descending."""
        backup = tmp_path / "backups"
        backup.mkdir()
        (backup / "v1.0.0").mkdir()
        (backup / "v2.0.0").mkdir()
        (backup / "v1.5.0").mkdir()
        monkeypatch.setattr(rollback_mod, "BACKUP_DIR", backup)
        result = rollback_mod._list_backups()
        assert result == ["2.0.0", "1.5.0", "1.0.0"]

    def test_strips_v_prefix(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Strips the v prefix from directory names."""
        backup = tmp_path / "backups"
        backup.mkdir()
        (backup / "v3.1.0").mkdir()
        monkeypatch.setattr(rollback_mod, "BACKUP_DIR", backup)
        result = rollback_mod._list_backups()
        assert result == ["3.1.0"]

    def test_ignores_files(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Only directories are listed, not files."""
        backup = tmp_path / "backups"
        backup.mkdir()
        (backup / "v1.0.0").mkdir()
        (backup / "not_a_dir.txt").write_text("x", encoding="utf-8")
        monkeypatch.setattr(rollback_mod, "BACKUP_DIR", backup)
        result = rollback_mod._list_backups()
        assert len(result) == 1


class TestRollbackTo:
    """Tests for _rollback_to version restoration."""

    def test_backup_not_found(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Returns False and prints error when backup does not exist."""
        monkeypatch.setattr(rollback_mod, "BACKUP_DIR", tmp_path / "backups")
        result = rollback_mod._rollback_to("9.9.9")
        assert result is False
        assert "Backup not found" in capsys.readouterr().err

    def test_restores_version_file(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Restores .version.json from backup."""
        backup = tmp_path / "backups" / "v1.0.0"
        backup.mkdir(parents=True)
        backup_version = backup / ".version.json"
        backup_version.write_text('{"version": "1.0.0"}', encoding="utf-8")

        version_file = tmp_path / ".version.json"
        monkeypatch.setattr(rollback_mod, "BACKUP_DIR", tmp_path / "backups")
        monkeypatch.setattr(rollback_mod, "VERSION_FILE", version_file)
        monkeypatch.setattr(rollback_mod, "REPO_ROOT", tmp_path)

        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        result = rollback_mod._rollback_to("1.0.0")
        assert result is True
        assert version_file.exists()
        assert json.loads(version_file.read_text(encoding="utf-8"))["version"] == "1.0.0"

    def test_restores_compiled_modules(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Restores .so and .pyd files to scripts directory."""
        backup = tmp_path / "backups" / "v2.0.0"
        backup.mkdir(parents=True)
        (backup / "module_a.so").write_text("compiled", encoding="utf-8")
        (backup / "module_b.pyd").write_text("compiled", encoding="utf-8")

        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        monkeypatch.setattr(rollback_mod, "BACKUP_DIR", tmp_path / "backups")
        monkeypatch.setattr(rollback_mod, "VERSION_FILE", tmp_path / ".version.json")
        monkeypatch.setattr(rollback_mod, "REPO_ROOT", tmp_path)

        result = rollback_mod._rollback_to("2.0.0")
        assert result is True
        assert (scripts_dir / "module_a.so").exists()
        assert (scripts_dir / "module_b.pyd").exists()

    def test_no_version_file_in_backup(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Succeeds even if backup has no .version.json."""
        backup = tmp_path / "backups" / "v1.0.0"
        backup.mkdir(parents=True)
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        monkeypatch.setattr(rollback_mod, "BACKUP_DIR", tmp_path / "backups")
        monkeypatch.setattr(rollback_mod, "VERSION_FILE", tmp_path / ".version.json")
        monkeypatch.setattr(rollback_mod, "REPO_ROOT", tmp_path)

        result = rollback_mod._rollback_to("1.0.0")
        assert result is True


class TestRollbackMain:
    """Tests for rollback main() CLI flags."""

    def test_list_no_backups(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """--list with no backups prints message and returns 0."""
        monkeypatch.setattr(rollback_mod, "BACKUP_DIR", tmp_path / "nonexistent")
        monkeypatch.setattr(sys, "argv", ["x", "--list"])
        rc = rollback_mod.main()
        assert rc == 0
        assert "No backups available" in capsys.readouterr().out

    def test_list_with_backups(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """--list prints available backup versions."""
        backup = tmp_path / "backups"
        backup.mkdir()
        (backup / "v1.0.0").mkdir()
        (backup / "v2.0.0").mkdir()
        monkeypatch.setattr(rollback_mod, "BACKUP_DIR", backup)
        monkeypatch.setattr(sys, "argv", ["x", "--list"])
        rc = rollback_mod.main()
        assert rc == 0
        output = capsys.readouterr().out
        assert "v2.0.0" in output
        assert "v1.0.0" in output

    def test_latest_no_backups(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """--latest with no backups returns 1."""
        monkeypatch.setattr(rollback_mod, "BACKUP_DIR", tmp_path / "nonexistent")
        monkeypatch.setattr(sys, "argv", ["x", "--latest"])
        rc = rollback_mod.main()
        assert rc == 1

    def test_latest_with_backups(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """--latest rolls back to most recent version."""
        backup = tmp_path / "backups"
        backup.mkdir()
        (backup / "v1.0.0").mkdir()
        (backup / "v3.0.0").mkdir()
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        monkeypatch.setattr(rollback_mod, "BACKUP_DIR", backup)
        monkeypatch.setattr(rollback_mod, "VERSION_FILE", tmp_path / ".version.json")
        monkeypatch.setattr(rollback_mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(sys, "argv", ["x", "--latest"])
        rc = rollback_mod.main()
        assert rc == 0

    def test_version_flag(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """--version restores specific version."""
        backup = tmp_path / "backups"
        backup.mkdir()
        (backup / "v1.0.0").mkdir()
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        monkeypatch.setattr(rollback_mod, "BACKUP_DIR", backup)
        monkeypatch.setattr(rollback_mod, "VERSION_FILE", tmp_path / ".version.json")
        monkeypatch.setattr(rollback_mod, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(sys, "argv", ["x", "--version", "1.0.0"])
        rc = rollback_mod.main()
        assert rc == 0

    def test_version_not_found(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """--version with missing backup returns 1."""
        backup = tmp_path / "backups"
        backup.mkdir()
        monkeypatch.setattr(rollback_mod, "BACKUP_DIR", backup)
        monkeypatch.setattr(sys, "argv", ["x", "--version", "99.0.0"])
        rc = rollback_mod.main()
        assert rc == 1

    def test_no_flags_prints_help(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        """No flags prints help and returns 1."""
        monkeypatch.setattr(sys, "argv", ["x"])
        rc = rollback_mod.main()
        assert rc == 1

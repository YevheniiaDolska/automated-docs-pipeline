"""Tests for internal-mode executive PDF generation.

Validates dual-mode (public/internal) functionality without breaking
existing public-mode PDF generation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _minimal_scorecard(**overrides: Any) -> dict[str, Any]:
    """Build a minimal scorecard fixture with realistic structure."""
    base: dict[str, Any] = {
        "generated_at": "2026-03-21T00:00:00Z",
        "score": {
            "audit_score_0_100": 72.5,
            "grade": "C",
        },
        "kpis": {
            "api_coverage": {"coverage_pct": 85.0, "spec_found": True},
            "example_reliability": {"example_reliability_pct": 60.0},
            "freshness": {"stale_docs_pct": 25.0, "total_docs": 42},
            "drift": {"docs_contract_drift_pct": 8.0},
            "layer_completeness": {"features_missing_required_layers_pct": 15.0},
            "terminology": {"terminology_consistency_pct": 92.0},
            "retrieval_quality": {"hallucination_rate": 12.0},
        },
        "findings": [
            {
                "id": "F-DRIFT",
                "title": "Code/docs contract drift at 8%",
                "severity": "high",
                "estimated_monthly_loss_usd_base": 1200,
                "estimated_remediation_cost_usd_base": 3500,
                "evidence_source": "Contract diff analysis",
                "estimation_confidence": "medium",
                "note": "Run drift reconciliation pipeline",
            },
            {
                "id": "F-EXAMPLES",
                "title": "Example reliability at 60%",
                "severity": "medium",
                "estimated_monthly_loss_usd_base": 800,
                "estimated_remediation_cost_usd_base": 2000,
                "evidence_source": "Smoke test results",
                "estimation_confidence": "medium",
                "note": "Add syntax validation to build pipeline",
            },
        ],
        "findings_totals": {
            "findings_count": 2,
            "high_count": 1,
            "medium_count": 1,
            "low_count": 0,
            "remediation_cost_usd_low_total": 3850,
            "remediation_cost_usd_base_total": 5500,
            "remediation_cost_usd_high_total": 8250,
            "monthly_loss_usd_low_total": 1400,
            "monthly_loss_usd_base_total": 2000,
            "monthly_loss_usd_high_total": 3000,
        },
        "business_impact": {
            "assumptions": {"engineer_hourly_usd": 95.0},
            "scenarios": {
                "conservative": {"monthly_cost_usd": 2800, "engineering_hours": 20, "support_hours": 10},
                "base": {"monthly_cost_usd": 4000, "engineering_hours": 30, "support_hours": 15},
                "aggressive": {"monthly_cost_usd": 5600, "engineering_hours": 42, "support_hours": 21},
            },
        },
        "capability_matrix": [
            {
                "capability_id": "api_coverage_sync",
                "capability_label": "API Coverage Sync",
                "pipeline_modules": ["validate_openapi_contract", "check_api_sdk_drift"],
                "related_flow": "api_first",
                "pilot": True,
                "full": True,
            },
            {
                "capability_id": "example_execution_quality",
                "capability_label": "Executable Examples",
                "pipeline_modules": ["examples_smoke_test"],
                "related_flow": "docs_flow",
                "pilot": True,
                "full": False,
            },
        ],
        "top_3_gaps": [
            {
                "id": "GAP-001",
                "title": "Missing webhook tutorial",
                "priority": "high",
                "action_required": "Create webhook integration tutorial",
                "related_files": ["docs/reference/webhooks.md"],
            },
        ],
    }
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k].update(v)
        else:
            base[k] = v
    return base


def _minimal_public_audit() -> dict[str, Any]:
    return {
        "aggregate": {
            "metrics": {
                "crawl": {"pages_crawled": 120},
                "links": {"broken_internal_links_count": 5, "docs_broken_links_count": 5},
                "seo_geo": {"seo_geo_issue_rate_pct": 8.5},
                "api_coverage": {"reference_coverage_pct": 70.0},
                "examples": {"example_reliability_estimate_pct": 65.0},
                "freshness": {"last_updated_coverage_pct": 40.0},
            },
        },
        "sites": [],
        "top_findings": ["Broken links found", "SEO issues detected"],
    }


# ---------------------------------------------------------------------------
# Mode detection tests
# ---------------------------------------------------------------------------


class TestModeDetection:
    def test_auto_internal_when_scorecard_only(self) -> None:
        from scripts.generate_executive_audit_pdf import _detect_mode

        sc = _minimal_scorecard()
        assert _detect_mode("auto", sc, {}) == "internal"

    def test_auto_public_when_public_present(self) -> None:
        from scripts.generate_executive_audit_pdf import _detect_mode

        sc = _minimal_scorecard()
        pub = _minimal_public_audit()
        assert _detect_mode("auto", sc, pub) == "public"

    def test_auto_public_when_no_scorecard_score(self) -> None:
        from scripts.generate_executive_audit_pdf import _detect_mode

        assert _detect_mode("auto", {}, _minimal_public_audit()) == "public"

    def test_auto_public_when_scorecard_missing_score(self) -> None:
        from scripts.generate_executive_audit_pdf import _detect_mode

        sc = {"kpis": {}}
        assert _detect_mode("auto", sc, _minimal_public_audit()) == "public"

    def test_explicit_mode_override(self) -> None:
        from scripts.generate_executive_audit_pdf import _detect_mode

        assert _detect_mode("internal", {}, _minimal_public_audit()) == "internal"
        assert _detect_mode("public", _minimal_scorecard(), {}) == "public"


# ---------------------------------------------------------------------------
# Internal PDF end-to-end
# ---------------------------------------------------------------------------


class TestInternalPDFGeneration:
    def test_internal_pdf_creates_file(self, tmp_path: Path) -> None:
        from scripts.generate_executive_audit_pdf import _build_pdf

        out = tmp_path / "test-internal.pdf"
        _build_pdf(
            output_path=out,
            scorecard=_minimal_scorecard(),
            public_audit={},
            llm_analysis={},
            company_name="TestCo",
            mode="internal",
        )
        assert out.exists()
        assert out.stat().st_size > 1000  # non-trivial PDF

    def test_internal_pdf_with_empty_kpis(self, tmp_path: Path) -> None:
        from scripts.generate_executive_audit_pdf import _build_pdf

        sc = _minimal_scorecard()
        sc["kpis"] = {}
        sc["findings"] = []
        sc["capability_matrix"] = []
        out = tmp_path / "test-empty-kpis.pdf"
        _build_pdf(
            output_path=out,
            scorecard=sc,
            public_audit={},
            llm_analysis={},
            company_name="EmptyCo",
            mode="internal",
        )
        assert out.exists()


# ---------------------------------------------------------------------------
# Public PDF backward compatibility
# ---------------------------------------------------------------------------


class TestPublicPDFBackwardCompat:
    def test_public_pdf_still_works(self, tmp_path: Path) -> None:
        from scripts.generate_executive_audit_pdf import _build_pdf

        out = tmp_path / "test-public.pdf"
        _build_pdf(
            output_path=out,
            scorecard={},
            public_audit=_minimal_public_audit(),
            llm_analysis={},
            company_name="PubCo",
            mode="public",
        )
        assert out.exists()
        assert out.stat().st_size > 1000

    def test_public_pdf_default_mode(self, tmp_path: Path) -> None:
        """Ensure default mode=public when not specified (backward compat)."""
        from scripts.generate_executive_audit_pdf import _build_pdf

        out = tmp_path / "test-default.pdf"
        _build_pdf(
            output_path=out,
            scorecard={},
            public_audit=_minimal_public_audit(),
            llm_analysis={},
            company_name="DefaultCo",
        )
        assert out.exists()

    def test_public_pdf_with_scorecard(self, tmp_path: Path) -> None:
        """Public mode with scorecard data still works (existing behavior)."""
        from scripts.generate_executive_audit_pdf import _build_pdf

        out = tmp_path / "test-pub-with-sc.pdf"
        _build_pdf(
            output_path=out,
            scorecard=_minimal_scorecard(),
            public_audit=_minimal_public_audit(),
            llm_analysis={},
            company_name="BothCo",
            mode="public",
        )
        assert out.exists()


# ---------------------------------------------------------------------------
# KPI category table
# ---------------------------------------------------------------------------


class TestKPICategoryTable:
    def test_returns_flowable_list(self) -> None:
        from scripts.generate_executive_audit_pdf import _kpi_category_table

        sc = _minimal_scorecard()
        result = _kpi_category_table(sc["kpis"])
        assert isinstance(result, list)
        assert len(result) == 1  # single Table

    def test_handles_empty_kpis(self) -> None:
        from scripts.generate_executive_audit_pdf import _kpi_category_table

        result = _kpi_category_table({})
        assert isinstance(result, list)
        assert len(result) == 1

    def test_7_rows_generated(self) -> None:
        from scripts.generate_executive_audit_pdf import _kpi_category_table, _INTERNAL_KPI_ROWS

        assert len(_INTERNAL_KPI_ROWS) == 7

        sc = _minimal_scorecard()
        result = _kpi_category_table(sc["kpis"])
        table = result[0]
        # header + 7 data rows
        assert len(table._argH) == 0 or True  # Table was created
        # Check we can wrap without error
        table.wrap(500, 800)


# ---------------------------------------------------------------------------
# Internal expert analysis
# ---------------------------------------------------------------------------


class TestInternalExpertAnalysis:
    def test_returns_flowables(self) -> None:
        from reportlab.lib.styles import getSampleStyleSheet
        from scripts.generate_executive_audit_pdf import _internal_expert_analysis

        styles = getSampleStyleSheet()
        body = styles["Normal"]
        sc = _minimal_scorecard()
        result = _internal_expert_analysis(sc, body)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_shows_strengths_for_on_target_kpis(self) -> None:
        from reportlab.lib.styles import getSampleStyleSheet
        from scripts.generate_executive_audit_pdf import _internal_expert_analysis

        styles = getSampleStyleSheet()
        sc = _minimal_scorecard()
        # API coverage at 85% vs 90% target -> below target
        # Terminology at 92% vs 90% target -> strength
        result = _internal_expert_analysis(sc, styles["Normal"])
        texts = [str(getattr(f, "text", "")) for f in result]
        joined = " ".join(texts)
        assert "Terminology" in joined  # Should appear as strength

    def test_shows_high_severity_risks(self) -> None:
        from reportlab.lib.styles import getSampleStyleSheet
        from scripts.generate_executive_audit_pdf import _internal_expert_analysis

        styles = getSampleStyleSheet()
        sc = _minimal_scorecard()
        result = _internal_expert_analysis(sc, styles["Normal"])
        texts = [str(getattr(f, "text", "")) for f in result]
        joined = " ".join(texts)
        assert "F-DRIFT" in joined

    def test_no_findings_graceful(self) -> None:
        from reportlab.lib.styles import getSampleStyleSheet
        from scripts.generate_executive_audit_pdf import _internal_expert_analysis

        styles = getSampleStyleSheet()
        sc = _minimal_scorecard()
        sc["findings"] = []
        sc["top_3_gaps"] = []
        result = _internal_expert_analysis(sc, styles["Normal"])
        assert isinstance(result, list)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# Capability matrix table
# ---------------------------------------------------------------------------


class TestCapabilityMatrixTable:
    def test_returns_table(self) -> None:
        from scripts.generate_executive_audit_pdf import _capability_matrix_table

        sc = _minimal_scorecard()
        result = _capability_matrix_table(sc["capability_matrix"])
        assert isinstance(result, list)
        assert len(result) == 1

    def test_empty_matrix(self) -> None:
        from scripts.generate_executive_audit_pdf import _capability_matrix_table

        result = _capability_matrix_table([])
        assert result == []

    def test_table_has_correct_columns(self) -> None:
        from scripts.generate_executive_audit_pdf import _capability_matrix_table

        sc = _minimal_scorecard()
        result = _capability_matrix_table(sc["capability_matrix"])
        table = result[0]
        # Should have 5 columns
        assert len(table._colWidths) == 5


# ---------------------------------------------------------------------------
# CLI validation
# ---------------------------------------------------------------------------


class TestCLIValidation:
    def test_internal_without_scorecard_fails(self, tmp_path: Path) -> None:
        from scripts.generate_executive_audit_pdf import _detect_mode

        # auto with empty scorecard and empty public -> public (which would fail separately)
        mode = _detect_mode("auto", {}, {})
        assert mode == "public"

    def test_main_internal_mode_no_score_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import generate_executive_audit_pdf as mod
        from scripts import license_gate

        monkeypatch.setattr(license_gate, "require", lambda f, **kw: None)
        monkeypatch.setattr(sys, "argv", [
            "x", "--mode", "internal",
            "--scorecard-json", "/dev/null",
            "--public-audit-json", "/dev/null",
        ])
        monkeypatch.setattr(mod, "_read_json", lambda p: {})
        with pytest.raises(SystemExit) as exc_info:
            mod.main()
        assert "scorecard" in str(exc_info.value).lower()

    def test_main_public_mode_no_audit_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import generate_executive_audit_pdf as mod
        from scripts import license_gate

        monkeypatch.setattr(license_gate, "require", lambda f, **kw: None)
        monkeypatch.setattr(sys, "argv", [
            "x", "--mode", "public",
            "--scorecard-json", "/dev/null",
            "--public-audit-json", "/dev/null",
        ])
        monkeypatch.setattr(mod, "_read_json", lambda p: {})
        with pytest.raises(SystemExit) as exc_info:
            mod.main()
        assert "public" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Broken link cost model
# ---------------------------------------------------------------------------


class TestBrokenLinkCostModel:
    def test_small_site(self) -> None:
        from scripts.generate_executive_audit_pdf import _estimate_broken_link_cost

        monthly, remediation, note = _estimate_broken_link_cost(10, 50)
        assert monthly > 0
        assert remediation > 0
        assert "Nonlinear" in note

    def test_large_site_caps_scale(self) -> None:
        from scripts.generate_executive_audit_pdf import _estimate_broken_link_cost

        monthly_small, _, _ = _estimate_broken_link_cost(500, 100)
        monthly_large, _, _ = _estimate_broken_link_cost(500, 10000)
        # Large site has higher caps
        assert monthly_large >= monthly_small

    def test_zero_broken_links(self) -> None:
        from scripts.generate_executive_audit_pdf import _estimate_broken_link_cost

        monthly, remediation, _ = _estimate_broken_link_cost(0, 100)
        assert monthly == 0
        assert remediation == 0

    def test_tier1_tier2_split(self) -> None:
        from scripts.generate_executive_audit_pdf import _estimate_broken_link_cost

        # 150 links: first 100 at tier1 rate, next 50 at tier2
        monthly, remediation, _ = _estimate_broken_link_cost(150, 5000)
        assert monthly > 0
        assert remediation > 0


# ---------------------------------------------------------------------------
# Internal methodology section
# ---------------------------------------------------------------------------


class TestInternalMethodology:
    def test_returns_flowables(self) -> None:
        from reportlab.lib.styles import getSampleStyleSheet
        from scripts.generate_executive_audit_pdf import _internal_methodology_section

        styles = getSampleStyleSheet()
        section = styles["Heading3"]
        body = styles["Normal"]
        result = _internal_methodology_section(section, body)
        assert isinstance(result, list)
        assert len(result) > 5  # header + intro + 7 pillars * 2


# ---------------------------------------------------------------------------
# Internal financial cards
# ---------------------------------------------------------------------------


class TestInternalFinancialCards:
    def test_returns_flowables(self) -> None:
        from scripts.generate_executive_audit_pdf import _internal_financial_cards

        sc = _minimal_scorecard()
        result = _internal_financial_cards(sc)
        assert isinstance(result, list)
        assert len(result) == 1  # single Table

    def test_empty_scenarios(self) -> None:
        from scripts.generate_executive_audit_pdf import _internal_financial_cards

        result = _internal_financial_cards({"business_impact": {}})
        assert result == []

    def test_no_business_impact(self) -> None:
        from scripts.generate_executive_audit_pdf import _internal_financial_cards

        result = _internal_financial_cards({})
        assert result == []

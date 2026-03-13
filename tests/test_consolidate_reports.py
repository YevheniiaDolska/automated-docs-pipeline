"""Tests for scripts/consolidate_reports.py."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.consolidate_reports import (
    ActionItem,
    HealthSummary,
    InputReportStatus,
    ReportConsolidator,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_json(path: Path, data: dict[str, Any]) -> None:
    """Write a JSON file to the given path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _make_gaps_report(gaps: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build a minimal gaps report payload."""
    gaps = gaps or [
        {
            "id": "GAP-001",
            "title": "Missing webhook docs",
            "category": "webhook",
            "priority": "high",
            "frequency": 120,
            "suggested_doc_type": "how-to",
            "action_required": "Create webhook guide",
            "related_files": ["src/webhooks.ts"],
            "keywords": ["webhook"],
            "sample_queries": ["how to configure webhooks"],
            "source": "code",
            "status": "new",
        },
    ]
    return {
        "generated_at": "2026-01-01T00:00:00Z",
        "summary": {
            "total_gaps": len(gaps),
            "high_priority": sum(1 for g in gaps if g.get("priority") == "high"),
            "medium_priority": sum(1 for g in gaps if g.get("priority") == "medium"),
            "low_priority": sum(1 for g in gaps if g.get("priority") == "low"),
        },
        "gaps": gaps,
    }


def _make_drift_report(status: str = "ok", openapi: list[str] | None = None, sdk: list[str] | None = None) -> dict[str, Any]:
    """Build a minimal drift report payload."""
    return {
        "status": status,
        "openapi_changed": openapi or [],
        "sdk_changed": sdk or [],
        "reference_docs_changed": [],
        "summary": "test",
    }


def _make_kpi_report(quality_score: int = 85, stale_files: list[str] | None = None) -> dict[str, Any]:
    """Build a minimal KPI wall payload."""
    stale_files = stale_files or []
    return {
        "generated_at": "2026-01-01T00:00:00Z",
        "quality_score": quality_score,
        "stale_pct": 10.0,
        "total_docs": 20,
        "metadata_completeness_pct": 95.0,
        "stale_docs": len(stale_files),
        "stale_files": stale_files,
    }


def _make_sla_report(status: str = "ok", breaches: list[str] | None = None) -> dict[str, Any]:
    """Build a minimal SLA report payload."""
    return {
        "status": status,
        "breaches": breaches or [],
        "metrics": {"quality_score": 85},
    }


def _make_retrieval_report(status: str = "ok") -> dict[str, Any]:
    return {
        "generated_at": "2026-01-01T00:00:00Z",
        "status": status,
        "metrics": {
            "precision_at_k": 0.8,
            "recall_at_k": 0.75,
            "hallucination_rate": 0.1,
            "top_k": 3,
            "sample_count": 10,
        },
        "breaches": [] if status == "ok" else ["precision_at_k=0.4 < 0.5"],
    }


def _make_graph_report() -> dict[str, Any]:
    return {
        "generated_at": "2026-01-01T00:00:00Z",
        "status": "ok",
        "modules_count": 4,
        "graph_nodes": 20,
        "edge_count": 11,
        "output_file": "docs/assets/knowledge-graph.jsonld",
    }


def _make_docs_contract_report(
    status: str = "drift",
    mismatches: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "interface_changed": ["src/api/routes.py"] if status == "drift" else [],
        "docs_changed": [],
        "blocked": status == "drift",
        "mismatch_count": len(mismatches or []),
        "mismatches": mismatches or [],
    }


# ---------------------------------------------------------------------------
# ReportConsolidator._next_id
# ---------------------------------------------------------------------------


class TestNextId:
    """Tests for the internal ID generator."""

    def test_generates_sequential_ids(self, tmp_path: Path) -> None:
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        assert consolidator._next_id() == "CONS-001"
        assert consolidator._next_id() == "CONS-002"
        assert consolidator._next_id() == "CONS-003"


# ---------------------------------------------------------------------------
# ReportConsolidator._read_json
# ---------------------------------------------------------------------------


class TestReadJson:
    """Tests for _read_json helper."""

    def test_reads_valid_json(self, tmp_path: Path) -> None:
        _write_json(tmp_path / "test.json", {"key": "value"})
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        result = consolidator._read_json("test.json")
        assert result == {"key": "value"}

    def test_returns_none_for_missing_file(self, tmp_path: Path) -> None:
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        assert consolidator._read_json("nonexistent.json") is None

    def test_returns_none_for_invalid_json(self, tmp_path: Path) -> None:
        (tmp_path / "bad.json").write_text("not json", encoding="utf-8")
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        assert consolidator._read_json("bad.json") is None


# ---------------------------------------------------------------------------
# _process_gaps
# ---------------------------------------------------------------------------


class TestProcessGaps:
    """Tests for _process_gaps."""

    def test_processes_gaps_report(self, tmp_path: Path) -> None:
        """Gaps are converted to action items."""
        _write_json(tmp_path / "doc_gaps_report.json", _make_gaps_report())
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        consolidator._process_gaps()

        assert consolidator.input_statuses["gaps"].found is True
        assert len(consolidator.action_items) == 1
        assert consolidator.action_items[0].source_report == "gaps"
        assert consolidator.action_items[0].category == "webhook"

    def test_missing_gaps_report(self, tmp_path: Path) -> None:
        """Missing report sets found=False and produces no items."""
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        consolidator._process_gaps()

        assert consolidator.input_statuses["gaps"].found is False
        assert len(consolidator.action_items) == 0


# ---------------------------------------------------------------------------
# _process_drift
# ---------------------------------------------------------------------------


class TestProcessDrift:
    """Tests for _process_drift."""

    def test_drift_ok_creates_no_items(self, tmp_path: Path) -> None:
        _write_json(tmp_path / "api_sdk_drift_report.json", _make_drift_report("ok"))
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        consolidator._process_drift()

        assert consolidator.health.drift_status == "ok"
        assert len(consolidator.action_items) == 0

    def test_drift_detected_creates_action_items(self, tmp_path: Path) -> None:
        """Drift with changed OpenAPI and SDK files produces action items."""
        drift = _make_drift_report(
            status="drift",
            openapi=["api/openapi.yaml"],
            sdk=["sdk/client.ts"],
        )
        _write_json(tmp_path / "api_sdk_drift_report.json", drift)
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        consolidator._process_drift()

        assert consolidator.health.drift_status == "drift"
        assert len(consolidator.action_items) == 2
        categories = {item.category for item in consolidator.action_items}
        assert "api_drift" in categories
        assert "sdk_drift" in categories

    def test_missing_drift_report(self, tmp_path: Path) -> None:
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        consolidator._process_drift()
        assert consolidator.input_statuses["drift"].found is False


# ---------------------------------------------------------------------------
# _process_kpi
# ---------------------------------------------------------------------------


class TestProcessKpi:
    """Tests for _process_kpi."""

    def test_processes_kpi_report(self, tmp_path: Path) -> None:
        kpi = _make_kpi_report(quality_score=82, stale_files=["docs/old.md"])
        _write_json(tmp_path / "kpi-wall.json", kpi)
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        consolidator._process_kpi()

        assert consolidator.health.quality_score == 82
        assert consolidator.health.total_docs == 20
        assert len(consolidator.action_items) == 1
        assert consolidator.action_items[0].category == "stale_doc"

    def test_no_stale_files_produces_no_items(self, tmp_path: Path) -> None:
        _write_json(tmp_path / "kpi-wall.json", _make_kpi_report())
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        consolidator._process_kpi()
        assert len(consolidator.action_items) == 0

    def test_missing_kpi_report(self, tmp_path: Path) -> None:
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        consolidator._process_kpi()
        assert consolidator.input_statuses["kpi"].found is False


# ---------------------------------------------------------------------------
# _process_sla
# ---------------------------------------------------------------------------


class TestProcessSla:
    """Tests for _process_sla."""

    def test_sla_ok_creates_no_items(self, tmp_path: Path) -> None:
        _write_json(tmp_path / "kpi-sla-report.json", _make_sla_report("ok"))
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        consolidator._process_sla()

        assert consolidator.health.sla_status == "ok"
        assert len(consolidator.action_items) == 0

    def test_sla_breach_creates_action_items(self, tmp_path: Path) -> None:
        sla = _make_sla_report("breach", breaches=["Quality score below 80"])
        _write_json(tmp_path / "kpi-sla-report.json", sla)
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        consolidator._process_sla()

        assert consolidator.health.sla_status == "breach"
        assert len(consolidator.action_items) == 1
        assert consolidator.action_items[0].category == "sla_breach"
        assert consolidator.action_items[0].priority == "high"

    def test_missing_sla_report(self, tmp_path: Path) -> None:
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        consolidator._process_sla()
        assert consolidator.input_statuses["sla"].found is False


# ---------------------------------------------------------------------------
# _cross_reference_drift
# ---------------------------------------------------------------------------


class TestCrossReferenceDrift:
    """Tests for _cross_reference_drift."""

    def test_annotates_gap_items_overlapping_drift(self, tmp_path: Path) -> None:
        """Gap items whose related_files overlap drift files get annotated."""
        _write_json(tmp_path / "doc_gaps_report.json", _make_gaps_report([
            {
                "title": "Gap overlapping drift",
                "category": "api_endpoint",
                "priority": "high",
                "frequency": 10,
                "related_files": ["api/openapi.yaml"],
                "source": "code",
            },
        ]))
        _write_json(
            tmp_path / "api_sdk_drift_report.json",
            _make_drift_report("drift", openapi=["api/openapi.yaml"]),
        )
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        consolidator._process_gaps()
        consolidator._cross_reference_drift()

        gap_item = consolidator.action_items[0]
        assert gap_item.context["drift_related"] is True
        assert "api/openapi.yaml" in gap_item.context["drift_overlapping_files"]

    def test_no_annotation_when_no_drift(self, tmp_path: Path) -> None:
        _write_json(tmp_path / "doc_gaps_report.json", _make_gaps_report())
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        consolidator._process_gaps()
        consolidator._cross_reference_drift()

        gap_item = consolidator.action_items[0]
        assert gap_item.context.get("drift_related") is False


# ---------------------------------------------------------------------------
# consolidate (full integration)
# ---------------------------------------------------------------------------


class TestConsolidate:
    """Tests for full consolidation flow."""

    def test_full_consolidation(self, tmp_path: Path) -> None:
        """Full consolidation merges all four reports."""
        _write_json(tmp_path / "doc_gaps_report.json", _make_gaps_report())
        _write_json(tmp_path / "api_sdk_drift_report.json", _make_drift_report("ok"))
        _write_json(tmp_path / "kpi-wall.json", _make_kpi_report())
        _write_json(tmp_path / "kpi-sla-report.json", _make_sla_report("ok"))

        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        result = consolidator.consolidate()

        assert "generated_at" in result
        assert "input_reports" in result
        assert "health_summary" in result
        assert "action_items" in result
        assert result["health_summary"]["quality_score"] == 85
        assert len(result["action_items"]) >= 1

    def test_consolidation_includes_retrieval_and_graph(self, tmp_path: Path) -> None:
        _write_json(tmp_path / "doc_gaps_report.json", _make_gaps_report())
        _write_json(tmp_path / "api_sdk_drift_report.json", _make_drift_report("ok"))
        _write_json(tmp_path / "kpi-wall.json", _make_kpi_report())
        _write_json(tmp_path / "kpi-sla-report.json", _make_sla_report("ok"))
        _write_json(tmp_path / "retrieval_evals_report.json", _make_retrieval_report("ok"))
        _write_json(tmp_path / "knowledge_graph_report.json", _make_graph_report())

        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        result = consolidator.consolidate()

        assert result["input_reports"]["retrieval_evals"]["found"] is True
        assert result["input_reports"]["knowledge_graph"]["found"] is True
        assert result["health_summary"]["retrieval_precision_at_k"] == 0.8
        assert result["health_summary"]["knowledge_graph_nodes"] == 20

    def test_consolidation_with_all_missing_reports(self, tmp_path: Path) -> None:
        """Consolidation completes even when all reports are missing."""
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        result = consolidator.consolidate()

        assert result["health_summary"]["total_action_items"] == 0
        for status in result["input_reports"].values():
            assert status["found"] is False


class TestProcessDocsContract:
    """Tests for docs contract report-only integration."""

    def test_emits_only_new_or_changed_items(self, tmp_path: Path) -> None:
        report = _make_docs_contract_report(
            status="drift",
            mismatches=[
                {
                    "id": "dod::src/api/routes.py",
                    "path": "src/api/routes.py",
                    "signature": "abc123",
                },
            ],
        )
        _write_json(tmp_path / "pr_docs_contract.json", report)
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        consolidator._process_docs_contract()

        assert consolidator.input_statuses["docs_contract"].found is True
        assert consolidator.input_statuses["docs_contract"].details["new_or_changed_count"] == 1
        assert consolidator.input_statuses["docs_contract"].details["emitted_count"] == 1
        assert any(item.source_report == "docs_contract" for item in consolidator.action_items)

        state_path = tmp_path / "dod_contract_state.json"
        assert state_path.exists()
        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert "dod::src/api/routes.py" in state["active"]

        # Second run with same mismatch should emit nothing (not new/changed).
        consolidator_2 = ReportConsolidator(reports_dir=str(tmp_path))
        consolidator_2._process_docs_contract()
        assert consolidator_2.input_statuses["docs_contract"].details["new_or_changed_count"] == 0
        assert consolidator_2.input_statuses["docs_contract"].details["emitted_count"] == 0

    def test_closed_and_deduplicated_mismatches(self, tmp_path: Path) -> None:
        report = _make_docs_contract_report(
            status="drift",
            mismatches=[
                {
                    "id": "dod::api/openapi.yaml",
                    "path": "api/openapi.yaml",
                    "signature": "sig1",
                },
            ],
        )
        _write_json(tmp_path / "pr_docs_contract.json", report)
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        consolidator.action_items.append(
            ActionItem(
                id="CONS-999",
                source_report="drift",
                source_id=None,
                title="Existing drift item",
                category="api_drift",
                suggested_doc_type="reference",
                priority="high",
                frequency=0,
                action_required="update docs",
                related_files=["api/openapi.yaml"],
            )
        )
        consolidator._process_docs_contract()
        assert consolidator.input_statuses["docs_contract"].details["deduplicated_count"] == 1
        assert consolidator.input_statuses["docs_contract"].details["emitted_count"] == 0

        # Now mismatch disappears -> should be counted as closed.
        _write_json(tmp_path / "pr_docs_contract.json", _make_docs_contract_report(status="ok", mismatches=[]))
        consolidator_2 = ReportConsolidator(reports_dir=str(tmp_path))
        consolidator_2._process_docs_contract()
        assert consolidator_2.input_statuses["docs_contract"].details["closed_count"] == 1


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------


class TestSave:
    """Tests for the save method."""

    def test_save_writes_json_file(self, tmp_path: Path) -> None:
        _write_json(tmp_path / "doc_gaps_report.json", _make_gaps_report())
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        output = tmp_path / "output" / "consolidated.json"
        consolidator.save(output_path=str(output))

        assert output.exists()
        data = json.loads(output.read_text(encoding="utf-8"))
        assert "action_items" in data


# ---------------------------------------------------------------------------
# _print_summary
# ---------------------------------------------------------------------------


class TestPrintSummary:
    """Tests for _print_summary."""

    def test_prints_without_error(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _write_json(tmp_path / "doc_gaps_report.json", _make_gaps_report())
        _write_json(tmp_path / "kpi-wall.json", _make_kpi_report())
        consolidator = ReportConsolidator(reports_dir=str(tmp_path))
        result = consolidator.consolidate()
        consolidator._print_summary(result)

        captured = capsys.readouterr()
        assert "CONSOLIDATED REPORT SUMMARY" in captured.out
        assert "Quality score" in captured.out

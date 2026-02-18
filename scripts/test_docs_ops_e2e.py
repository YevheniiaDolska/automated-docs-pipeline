#!/usr/bin/env python3
"""Run fixture-based E2E checks for docs operations gates."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.check_api_sdk_drift import evaluate as evaluate_drift
from scripts.check_docs_contract import evaluate_contract
from scripts.evaluate_kpi_sla import evaluate as evaluate_sla


def _load_fixture(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_docs_contract_tests(fixtures_dir: Path) -> None:
    for fixture_name in ["scenario_docs_contract_block.json", "scenario_docs_contract_pass.json"]:
        fixture = _load_fixture(fixtures_dir / fixture_name)
        report = evaluate_contract(fixture["files"])
        actual = bool(report["blocked"])
        expected = bool(fixture["expected_blocked"])
        if actual != expected:
            raise AssertionError(
                f"docs contract fixture failed: {fixture['name']} (expected {expected}, got {actual})"
            )


def run_drift_tests(fixtures_dir: Path) -> None:
    for fixture_name in ["scenario_drift_block.json", "scenario_drift_pass.json"]:
        fixture = _load_fixture(fixtures_dir / fixture_name)
        report = evaluate_drift(fixture["files"])
        if report.status != fixture["expected_status"]:
            raise AssertionError(
                f"drift fixture failed: {fixture['name']} (expected {fixture['expected_status']}, got {report.status})"
            )


def run_sla_tests() -> None:
    current = {
        "quality_score": 79,
        "stale_pct": 17.0,
        "gap_high": 9,
    }
    previous = {
        "quality_score": 88,
        "stale_pct": 12.0,
        "gap_high": 5,
    }
    thresholds = {
        "min_quality_score": 80,
        "max_stale_pct": 15.0,
        "max_high_priority_gaps": 8,
        "max_quality_score_drop": 5,
    }

    report = evaluate_sla(current, previous, thresholds)
    if report.status != "breach":
        raise AssertionError("SLA fixture failed: expected breach status.")


def main() -> int:
    fixtures_dir = Path("tests/fixtures/docs_ops")

    run_docs_contract_tests(fixtures_dir)
    run_drift_tests(fixtures_dir)
    run_sla_tests()

    print("Docs ops E2E fixtures passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

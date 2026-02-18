#!/usr/bin/env python3
"""Golden tests for report outputs and workflow contracts."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.check_api_sdk_drift import _render_markdown as render_drift_md
from scripts.check_api_sdk_drift import evaluate as evaluate_drift
from scripts.evaluate_kpi_sla import _render_markdown as render_sla_md
from scripts.evaluate_kpi_sla import evaluate as evaluate_sla
from scripts.generate_kpi_wall import build_metrics, render_dashboard_html, render_markdown


GOLDEN_DIR = Path("tests/golden")


def _assert_equal_text(path: Path, actual: str, update: bool) -> None:
    if update:
        path.write_text(actual, encoding="utf-8")
        return

    expected = path.read_text(encoding="utf-8")
    if actual != expected:
        raise AssertionError(f"Golden mismatch for {path}")


def _assert_equal_json(path: Path, actual: dict[str, Any], update: bool) -> None:
    if update:
        path.write_text(json.dumps(actual, indent=2, sort_keys=True), encoding="utf-8")
        return

    expected = json.loads(path.read_text(encoding="utf-8"))
    if actual != expected:
        raise AssertionError(f"Golden JSON mismatch for {path}")


def _prepare_kpi_fixture(tmp_dir: Path) -> tuple[Path, Path]:
    docs_dir = tmp_dir / "docs"
    reports_dir = tmp_dir / "reports"
    docs_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    (docs_dir / "alpha.md").write_text(
        """---
title: Alpha page
description: Alpha description for testing fixture output consistency.
content_type: reference
last_reviewed: '2026-01-01'
---

# Alpha
Fixture content.
""",
        encoding="utf-8",
    )

    (docs_dir / "beta.md").write_text(
        """---
title: Beta page
description: Beta description for testing fixture output consistency.
content_type: how-to
last_reviewed: '2026-03-20'
---

# Beta
Fixture content.
""",
        encoding="utf-8",
    )

    (reports_dir / "doc_gaps_report.json").write_text(
        json.dumps(
            {
                "gaps": [
                    {"priority": "high", "title": "Gap A"},
                    {"priority": "medium", "title": "Gap B"},
                    {"priority": "high", "title": "Gap C"},
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    (reports_dir / "pilot-baseline.json").write_text(
        json.dumps({"debt_score": {"total": 120}}, indent=2),
        encoding="utf-8",
    )

    (reports_dir / "pilot-analysis.json").write_text(
        json.dumps({"debt_score": {"total": 90}}, indent=2),
        encoding="utf-8",
    )

    return docs_dir, reports_dir


def _run_kpi_goldens(update: bool) -> None:
    with tempfile.TemporaryDirectory() as temp:
        tmp_dir = Path(temp)
        docs_dir, reports_dir = _prepare_kpi_fixture(tmp_dir)

        metrics = build_metrics(
            docs_dir=docs_dir,
            reports_dir=reports_dir,
            stale_days=90,
            generated_at="2026-02-17T00:00:00Z",
            reference_date=date(2026, 4, 15),
        )

        metrics_json = metrics.__dict__
        metrics_md = render_markdown(metrics)
        metrics_html = render_dashboard_html(metrics)

        _assert_equal_json(GOLDEN_DIR / "kpi_wall.json", metrics_json, update)
        _assert_equal_text(GOLDEN_DIR / "kpi_wall.md", metrics_md, update)
        _assert_equal_text(GOLDEN_DIR / "wow_dashboard.html", metrics_html, update)


def _run_drift_goldens(update: bool) -> None:
    files = ["api/openapi.yaml", "sdk/client.ts", "docs/reference/orders.md"]
    report = evaluate_drift(files)

    payload = {
        "status": report.status,
        "summary": report.summary,
        "openapi_changed": report.openapi_changed,
        "sdk_changed": report.sdk_changed,
        "reference_docs_changed": report.reference_docs_changed,
    }

    _assert_equal_json(GOLDEN_DIR / "api_sdk_drift.json", payload, update)
    _assert_equal_text(GOLDEN_DIR / "api_sdk_drift.md", render_drift_md(report), update)


def _run_sla_goldens(update: bool) -> None:
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
    payload = {
        "status": report.status,
        "summary": report.summary,
        "breaches": report.breaches,
        "trend_notes": report.trend_notes,
        "metrics": report.metrics,
    }

    _assert_equal_json(GOLDEN_DIR / "kpi_sla.json", payload, update)
    _assert_equal_text(GOLDEN_DIR / "kpi_sla.md", render_sla_md(report, thresholds), update)


def _workflow_fingerprint(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    on_section = data.get("on", {})

    if isinstance(on_section, dict):
        triggers = sorted(on_section.keys())
    elif isinstance(on_section, list):
        triggers = sorted(str(item) for item in on_section)
    else:
        triggers = [str(on_section)]

    jobs = data.get("jobs", {})
    job_fingerprints: dict[str, Any] = {}

    for job_id, job in sorted(jobs.items()):
        steps = job.get("steps", []) if isinstance(job, dict) else []
        step_names = []
        for step in steps:
            if isinstance(step, dict) and "name" in step:
                step_names.append(str(step["name"]))
            elif isinstance(step, dict) and "uses" in step:
                step_names.append(f"uses:{step['uses']}")
            else:
                step_names.append("unnamed")

        job_fingerprints[job_id] = step_names

    return {
        "name": data.get("name"),
        "triggers": triggers,
        "jobs": job_fingerprints,
    }


def _run_workflow_goldens(update: bool) -> None:
    workflow_paths = [
        Path(".github/workflows/pr-dod-contract.yml"),
        Path(".github/workflows/api-sdk-drift-gate.yml"),
        Path(".github/workflows/kpi-wall.yml"),
        Path(".github/workflows/release-docs-pack.yml"),
        Path(".github/workflows/docs-ops-e2e.yml"),
    ]

    payload = {str(path): _workflow_fingerprint(path) for path in workflow_paths}
    _assert_equal_json(GOLDEN_DIR / "workflow_fingerprints.json", payload, update)


def main() -> int:
    parser = argparse.ArgumentParser(description="Golden tests for reports and workflows")
    parser.add_argument("--update-golden", action="store_true", help="Update golden fixtures")
    args = parser.parse_args()

    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)

    _run_kpi_goldens(args.update_golden)
    _run_drift_goldens(args.update_golden)
    _run_sla_goldens(args.update_golden)
    _run_workflow_goldens(args.update_golden)

    print("Golden tests for reports and workflows passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

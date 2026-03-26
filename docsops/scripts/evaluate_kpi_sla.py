#!/usr/bin/env python3
"""Evaluate KPI SLA thresholds and trend regression for docs operations."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml


@dataclass
class SlaReport:
    status: str
    summary: str
    breaches: list[str]
    trend_notes: list[str]
    metrics: dict


DEFAULT_THRESHOLDS = {
    "min_quality_score": 80,
    "max_stale_pct": 15.0,
    "max_high_priority_gaps": 8,
    "max_quality_score_drop": 5,
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_thresholds(policy_pack: str | None) -> dict:
    if policy_pack is None:
        return dict(DEFAULT_THRESHOLDS)

    data = yaml.safe_load(Path(policy_pack).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Policy pack must be a mapping.")

    section = data.get("kpi_sla", {})
    if not isinstance(section, dict):
        raise ValueError("Policy pack kpi_sla section must be a mapping.")

    thresholds = dict(DEFAULT_THRESHOLDS)
    thresholds.update(section)
    return thresholds


def evaluate(current: dict, previous: dict | None, thresholds: dict) -> SlaReport:
    breaches: list[str] = []
    trend_notes: list[str] = []

    quality = int(current.get("quality_score", 0))
    stale_pct = float(current.get("stale_pct", 0.0))
    high_gaps = int(current.get("gap_high", 0))

    if quality < int(thresholds["min_quality_score"]):
        breaches.append(
            f"Quality score breach: {quality} < {int(thresholds['min_quality_score'])}."
        )

    if stale_pct > float(thresholds["max_stale_pct"]):
        breaches.append(
            f"Stale docs breach: {stale_pct:.1f}% > {float(thresholds['max_stale_pct']):.1f}%."
        )

    if high_gaps > int(thresholds["max_high_priority_gaps"]):
        breaches.append(
            f"High-priority gap breach: {high_gaps} > {int(thresholds['max_high_priority_gaps'])}."
        )

    if previous is not None:
        previous_quality = int(previous.get("quality_score", quality))
        drop = previous_quality - quality
        if drop > int(thresholds["max_quality_score_drop"]):
            breaches.append(
                f"Quality trend breach: dropped by {drop} points (max allowed {int(thresholds['max_quality_score_drop'])})."
            )
        trend_notes.append(f"Quality score trend: previous {previous_quality}, current {quality}.")

    status = "breach" if breaches else "ok"
    summary = "SLA thresholds breached." if breaches else "KPI SLA check passed."

    return SlaReport(
        status=status,
        summary=summary,
        breaches=breaches,
        trend_notes=trend_notes,
        metrics={
            "quality_score": quality,
            "stale_pct": stale_pct,
            "high_priority_gaps": high_gaps,
        },
    )


def _render_markdown(report: SlaReport, thresholds: dict) -> str:
    def list_block(items: list[str]) -> str:
        if not items:
            return "- none"
        return "\n".join(f"- {item}" for item in items)

    return (
        "# KPI SLA Evaluation\n\n"
        f"Status: **{report.status.upper()}**\n\n"
        f"{report.summary}\n\n"
        "## Thresholds\n\n"
        f"- Minimum quality score: {int(thresholds['min_quality_score'])}\n"
        f"- Maximum stale percent: {float(thresholds['max_stale_pct']):.1f}%\n"
        f"- Maximum high-priority gaps: {int(thresholds['max_high_priority_gaps'])}\n"
        f"- Maximum quality score drop: {int(thresholds['max_quality_score_drop'])}\n\n"
        "## Breaches\n\n"
        f"{list_block(report.breaches)}\n\n"
        "## Trend notes\n\n"
        f"{list_block(report.trend_notes)}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate KPI SLA thresholds and trend")
    parser.add_argument("--current", required=True, help="Current KPI JSON path")
    parser.add_argument("--previous", help="Previous KPI JSON path")
    parser.add_argument("--policy-pack", help="Optional policy pack YAML path")
    parser.add_argument("--json-output", default="reports/kpi-sla-report.json")
    parser.add_argument("--md-output", default="reports/kpi-sla-report.md")
    args = parser.parse_args()

    current = _load_json(Path(args.current))
    previous = _load_json(Path(args.previous)) if args.previous else None
    thresholds = _load_thresholds(args.policy_pack)

    report = evaluate(current, previous, thresholds)

    json_path = Path(args.json_output)
    md_path = Path(args.md_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report, thresholds), encoding="utf-8")

    print(f"KPI SLA JSON report: {json_path}")
    print(f"KPI SLA Markdown report: {md_path}")
    print(report.summary)

    return 1 if report.status == "breach" else 0


if __name__ == "__main__":
    raise SystemExit(main())

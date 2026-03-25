#!/usr/bin/env python3
"""Annual ROI calculator for VeriDoc/VeriOps adoption."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class RoiInputs:
    """Inputs for annual ROI estimation."""

    hours_doc_per_month: float
    hours_eng_per_month: float
    hours_qa_per_month: float
    blended_rate_usd_per_hour: float
    routine_time_saved_pct: float
    incidents_per_month_before: float
    incident_cost_usd: float
    incident_reduction_pct: float
    releases_per_month: float
    release_value_usd: float
    release_acceleration_pct: float
    subscription_cost_usd_per_month: float


def _pct_to_fraction(value: float) -> float:
    return max(0.0, min(100.0, value)) / 100.0


def estimate_annual_roi(inputs: RoiInputs) -> dict[str, float]:
    """Estimate annual gross and net ROI effects."""
    save_fraction = _pct_to_fraction(inputs.routine_time_saved_pct)
    incident_reduction_fraction = _pct_to_fraction(inputs.incident_reduction_pct)
    release_accel_fraction = _pct_to_fraction(inputs.release_acceleration_pct)

    monthly_hours_total = (
        inputs.hours_doc_per_month
        + inputs.hours_eng_per_month
        + inputs.hours_qa_per_month
    )
    annual_labor_savings = monthly_hours_total * inputs.blended_rate_usd_per_hour * save_fraction * 12.0

    annual_incident_savings = (
        inputs.incidents_per_month_before
        * inputs.incident_cost_usd
        * incident_reduction_fraction
        * 12.0
    )

    annual_release_uplift = (
        inputs.releases_per_month
        * inputs.release_value_usd
        * release_accel_fraction
        * 12.0
    )

    annual_subscription_cost = inputs.subscription_cost_usd_per_month * 12.0
    annual_total_benefit = annual_labor_savings + annual_incident_savings + annual_release_uplift
    annual_net_benefit = annual_total_benefit - annual_subscription_cost

    if annual_subscription_cost <= 0:
        roi_pct = 0.0
    else:
        roi_pct = (annual_net_benefit / annual_subscription_cost) * 100.0

    return {
        "annual_labor_savings_usd": round(annual_labor_savings, 2),
        "annual_incident_savings_usd": round(annual_incident_savings, 2),
        "annual_release_uplift_usd": round(annual_release_uplift, 2),
        "annual_total_benefit_usd": round(annual_total_benefit, 2),
        "annual_subscription_cost_usd": round(annual_subscription_cost, 2),
        "annual_net_benefit_usd": round(annual_net_benefit, 2),
        "roi_pct": round(roi_pct, 2),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Annual ROI calculator")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    parser.add_argument("--hours-doc-per-month", type=float, default=80.0)
    parser.add_argument("--hours-eng-per-month", type=float, default=120.0)
    parser.add_argument("--hours-qa-per-month", type=float, default=100.0)
    parser.add_argument("--blended-rate-usd-per-hour", type=float, default=65.0)
    parser.add_argument("--routine-time-saved-pct", type=float, default=45.0)
    parser.add_argument("--incidents-per-month-before", type=float, default=3.0)
    parser.add_argument("--incident-cost-usd", type=float, default=1800.0)
    parser.add_argument("--incident-reduction-pct", type=float, default=40.0)
    parser.add_argument("--releases-per-month", type=float, default=4.0)
    parser.add_argument("--release-value-usd", type=float, default=2500.0)
    parser.add_argument("--release-acceleration-pct", type=float, default=15.0)
    parser.add_argument("--subscription-cost-usd-per-month", type=float, default=799.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    roi_inputs = RoiInputs(
        hours_doc_per_month=args.hours_doc_per_month,
        hours_eng_per_month=args.hours_eng_per_month,
        hours_qa_per_month=args.hours_qa_per_month,
        blended_rate_usd_per_hour=args.blended_rate_usd_per_hour,
        routine_time_saved_pct=args.routine_time_saved_pct,
        incidents_per_month_before=args.incidents_per_month_before,
        incident_cost_usd=args.incident_cost_usd,
        incident_reduction_pct=args.incident_reduction_pct,
        releases_per_month=args.releases_per_month,
        release_value_usd=args.release_value_usd,
        release_acceleration_pct=args.release_acceleration_pct,
        subscription_cost_usd_per_month=args.subscription_cost_usd_per_month,
    )

    roi_result = estimate_annual_roi(roi_inputs)
    payload = {
        "inputs": {
            "hours_doc_per_month": args.hours_doc_per_month,
            "hours_eng_per_month": args.hours_eng_per_month,
            "hours_qa_per_month": args.hours_qa_per_month,
            "blended_rate_usd_per_hour": args.blended_rate_usd_per_hour,
            "routine_time_saved_pct": args.routine_time_saved_pct,
            "incidents_per_month_before": args.incidents_per_month_before,
            "incident_cost_usd": args.incident_cost_usd,
            "incident_reduction_pct": args.incident_reduction_pct,
            "releases_per_month": args.releases_per_month,
            "release_value_usd": args.release_value_usd,
            "release_acceleration_pct": args.release_acceleration_pct,
            "subscription_cost_usd_per_month": args.subscription_cost_usd_per_month,
        },
        "roi_result": roi_result,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    print("ROI estimate (annual):")
    print(f"  Total benefit: ${roi_result['annual_total_benefit_usd']:.2f}")
    print(f"  Subscription cost: ${roi_result['annual_subscription_cost_usd']:.2f}")
    print(f"  Net benefit: ${roi_result['annual_net_benefit_usd']:.2f}")
    print(f"  ROI: {roi_result['roi_pct']:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

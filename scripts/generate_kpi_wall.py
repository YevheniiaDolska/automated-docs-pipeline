#!/usr/bin/env python3
"""Generate a weekly KPI wall and customer-facing wow dashboard."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml
from yaml import YAMLError


@dataclass
class KpiMetrics:
    generated_at: str
    total_docs: int
    docs_with_frontmatter: int
    metadata_completeness_pct: float
    stale_docs: int
    stale_pct: float
    gap_total: int
    gap_high: int
    quality_score: int
    debt_trend_note: str
    before_after_note: str


def _extract_frontmatter(text: str) -> dict[str, Any] | None:
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        data = yaml.safe_load(parts[1])
        return data if isinstance(data, dict) else None
    except YAMLError:
        return None


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)).date()
    except (TypeError, ValueError):
        try:
            return datetime.strptime(str(value), "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return None


def _load_gap_metrics(report_path: Path) -> tuple[int, int]:
    if not report_path.exists():
        return 0, 0
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0, 0

    gaps = data.get("gaps", [])
    if not isinstance(gaps, list):
        return 0, 0

    total = len(gaps)
    high = sum(1 for g in gaps if str(g.get("priority", "")).lower() == "high")
    return total, high


def _load_before_after_note(reports_dir: Path) -> str:
    baseline = reports_dir / "pilot-baseline.json"
    latest = reports_dir / "pilot-analysis.json"

    if not baseline.exists() or not latest.exists():
        return "Before/after KPI baseline is not available yet."

    try:
        before = json.loads(baseline.read_text(encoding="utf-8"))
        after = json.loads(latest.read_text(encoding="utf-8"))
        b_debt = int(before.get("debt_score", {}).get("total", 0))
        a_debt = int(after.get("debt_score", {}).get("total", 0))
        delta = a_debt - b_debt
        direction = "reduced" if delta < 0 else "increased"
        return f"Documentation debt {direction} by {abs(delta)} points (before {b_debt}, after {a_debt})."
    except (AttributeError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return "Before/after KPI files exist, but parsing failed."


def _compute_quality_score(metadata_pct: float, stale_pct: float, gap_high: int) -> int:
    score = 100
    score -= int(round((100 - metadata_pct) * 0.35))
    score -= int(round(stale_pct * 0.30))
    score -= min(gap_high * 3, 25)
    return max(0, min(100, score))


def build_metrics(
    docs_dir: Path,
    reports_dir: Path,
    stale_days: int,
    generated_at: str | None = None,
    reference_date: date | None = None,
) -> KpiMetrics:
    current_date = reference_date or date.today()
    files = sorted(p for p in docs_dir.rglob("*.md") if "assets/" not in str(p).replace("\\", "/"))
    total_docs = len(files)

    docs_with_frontmatter = 0
    required_fields = ("title", "description", "content_type")
    required_total = 0
    required_present = 0

    stale_cutoff = current_date - timedelta(days=stale_days)
    stale_docs = 0

    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        fm = _extract_frontmatter(text)
        if fm is None:
            continue

        docs_with_frontmatter += 1

        for field in required_fields:
            required_total += 1
            if fm.get(field):
                required_present += 1

        reviewed = _parse_date(fm.get("last_reviewed"))
        if reviewed is not None and reviewed < stale_cutoff:
            stale_docs += 1

    metadata_pct = (required_present / required_total * 100.0) if required_total else 0.0
    stale_pct = (stale_docs / total_docs * 100.0) if total_docs else 0.0

    gap_total, gap_high = _load_gap_metrics(reports_dir / "doc_gaps_report.json")
    quality_score = _compute_quality_score(metadata_pct, stale_pct, gap_high)

    if gap_total == 0:
        debt_trend_note = "No active gaps in the latest report."
    elif gap_high == 0:
        debt_trend_note = f"{gap_total} total gaps, no high-priority gaps."
    else:
        debt_trend_note = f"{gap_total} total gaps, {gap_high} high-priority gaps need SLA attention."

    return KpiMetrics(
        generated_at=generated_at or datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        total_docs=total_docs,
        docs_with_frontmatter=docs_with_frontmatter,
        metadata_completeness_pct=round(metadata_pct, 1),
        stale_docs=stale_docs,
        stale_pct=round(stale_pct, 1),
        gap_total=gap_total,
        gap_high=gap_high,
        quality_score=quality_score,
        debt_trend_note=debt_trend_note,
        before_after_note=_load_before_after_note(reports_dir),
    )


def render_markdown(metrics: KpiMetrics) -> str:
    return f"""# Documentation KPI Wall

Generated at: {metrics.generated_at}

## Scorecard

- Quality score: **{metrics.quality_score}/100**
- Total docs: **{metrics.total_docs}**
- Docs with frontmatter: **{metrics.docs_with_frontmatter}**
- Metadata completeness: **{metrics.metadata_completeness_pct}%**
- Stale docs: **{metrics.stale_docs} ({metrics.stale_pct}%)**
- Open doc gaps: **{metrics.gap_total}**
- High-priority doc gaps: **{metrics.gap_high}**

## Executive Notes

- Debt trend: {metrics.debt_trend_note}
- Before/after: {metrics.before_after_note}

## Suggested Focus This Week

1. Resolve high-priority gaps first.
1. Reduce stale-doc ratio below 10%.
1. Keep metadata completeness above 95%.
"""


def render_dashboard_html(metrics: KpiMetrics) -> str:
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Documentation Operations Dashboard</title>
  <style>
    :root {{
      --bg: #f4f6f8;
      --card: #ffffff;
      --ink: #102030;
      --muted: #5d6b79;
      --accent: #0b7285;
      --accent-2: #f59f00;
      --accent-3: #2f9e44;
      --danger: #c92a2a;
    }}
    body {{ margin: 0; font-family: Georgia, 'Times New Roman', serif; background: linear-gradient(120deg, #f8fafc, #edf2f7); color: var(--ink); }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 28px; }}
    h1 {{ font-size: 2rem; margin: 0 0 8px; }}
    p.meta {{ color: var(--muted); margin-top: 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(220px,1fr)); gap: 14px; margin-top: 18px; }}
    .card {{ background: var(--card); border-radius: 14px; padding: 16px; box-shadow: 0 6px 18px rgba(0,0,0,0.06); }}
    .k {{ color: var(--muted); font-size: 0.9rem; }}
    .v {{ font-size: 1.7rem; font-weight: 700; margin-top: 6px; }}
    .score {{ color: var(--accent); }}
    .warn {{ color: var(--accent-2); }}
    .good {{ color: var(--accent-3); }}
    .bad {{ color: var(--danger); }}
    .notes {{ margin-top: 20px; background: #0b1724; color: #dbe8f3; border-radius: 14px; padding: 18px; }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <h1>Documentation Operations Dashboard</h1>
    <p class=\"meta\">Generated at {metrics.generated_at}</p>
    <div class=\"grid\">
      <div class=\"card\"><div class=\"k\">Quality score</div><div class=\"v score\">{metrics.quality_score}/100</div></div>
      <div class=\"card\"><div class=\"k\">Total docs</div><div class=\"v\">{metrics.total_docs}</div></div>
      <div class=\"card\"><div class=\"k\">Metadata completeness</div><div class=\"v good\">{metrics.metadata_completeness_pct}%</div></div>
      <div class=\"card\"><div class=\"k\">Stale docs</div><div class=\"v warn\">{metrics.stale_docs} ({metrics.stale_pct}%)</div></div>
      <div class=\"card\"><div class=\"k\">Open gaps</div><div class=\"v\">{metrics.gap_total}</div></div>
      <div class=\"card\"><div class=\"k\">High-priority gaps</div><div class=\"v bad\">{metrics.gap_high}</div></div>
    </div>

    <div class=\"notes\">
      <p><strong>Debt trend:</strong> {metrics.debt_trend_note}</p>
      <p><strong>Before/after:</strong> {metrics.before_after_note}</p>
      <p><strong>Positioning:</strong> This is a full documentation operations system, not simple draft generation.</p>
    </div>
  </div>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate weekly docs KPI wall and dashboard")
    parser.add_argument("--docs-dir", default="docs", help="Docs directory")
    parser.add_argument("--reports-dir", default="reports", help="Reports directory")
    parser.add_argument("--stale-days", type=int, default=90, help="Staleness threshold in days")
    parser.add_argument("--generated-at", help="Override timestamp for deterministic output")
    parser.add_argument("--reference-date", help="Override current date (YYYY-MM-DD) for deterministic output")
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    reports_dir = Path(args.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    reference_date = None
    if args.reference_date:
        reference_date = datetime.strptime(args.reference_date, "%Y-%m-%d").date()

    metrics = build_metrics(
        docs_dir,
        reports_dir,
        args.stale_days,
        generated_at=args.generated_at,
        reference_date=reference_date,
    )

    md_path = reports_dir / "kpi-wall.md"
    html_path = reports_dir / "wow-dashboard.html"
    json_path = reports_dir / "kpi-wall.json"

    md_path.write_text(render_markdown(metrics), encoding="utf-8")
    html_path.write_text(render_dashboard_html(metrics), encoding="utf-8")
    json_path.write_text(json.dumps(metrics.__dict__, indent=2), encoding="utf-8")

    print(f"KPI wall written to {md_path}")
    print(f"Wow dashboard written to {html_path}")
    print(f"Machine-readable metrics written to {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

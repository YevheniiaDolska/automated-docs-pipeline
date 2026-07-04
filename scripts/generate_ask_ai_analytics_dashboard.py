#!/usr/bin/env python3
"""Render the Ask AI usage report into a self-contained analytics dashboard.

Reads the JSON report produced by scripts/report_ask_ai_usage.py and writes a
single standalone HTML file (no external assets, no network calls) with:

- KPI stat tiles (question volume, answer rate, helpful rate, coverage gap)
- A daily volume chart split into answered vs. zero-citation questions
- A satisfaction split bar (helpful vs. unhelpful feedback)
- Top questions and doc-gap candidate tables (the actionable analytics)

Usage:
  python3 scripts/generate_ask_ai_analytics_dashboard.py \
    --report reports/ask_ai_usage_report.json \
    --output reports/ask-ai-analytics.html
"""

from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Palette matches reports/wow-dashboard.html for a consistent look across the suite.
COLORS = {
    "bg": "#0f172a",
    "surface": "#1e293b",
    "surface2": "#334155",
    "border": "#475569",
    "text": "#f1f5f9",
    "muted": "#94a3b8",
    "accent": "#6366f1",
    "green": "#10b981",
    "yellow": "#f59e0b",
    "red": "#ef4444",
    "blue": "#3b82f6",
}


def _esc(text: Any) -> str:
    return html.escape(str(text), quote=True)


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{round(value * 100)}%"


def _fmt_ts(raw: str) -> str:
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return str(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.strftime("%Y-%m-%d %H:%M UTC")


def _stat_tile(label: str, value: str, sub: str, tone: str) -> str:
    accent = COLORS.get(tone, COLORS["accent"])
    return (
        '<div class="tile">'
        f'<div class="tile-value" style="color:{accent};">{_esc(value)}</div>'
        f'<div class="tile-label">{_esc(label)}</div>'
        f'<div class="tile-sub">{_esc(sub)}</div>'
        "</div>"
    )


def _volume_chart(daily: list[dict[str, Any]]) -> str:
    """Stacked daily bars: answered (accent) over zero-citation (amber)."""
    if not daily:
        return '<p class="empty">No dated questions in this window yet.</p>'

    daily = daily[-30:]  # keep the chart readable
    max_total = max(row.get("questions", 0) for row in daily) or 1
    plot_h = 180
    bar_w = 26
    gap = 10
    left_pad = 8
    width = left_pad * 2 + len(daily) * (bar_w + gap)
    height = plot_h + 46

    bars = []
    for idx, row in enumerate(daily):
        total = int(row.get("questions", 0))
        zero = int(row.get("zero_citation", 0))
        answered = max(total - zero, 0)
        x = left_pad + idx * (bar_w + gap)
        total_h = round(plot_h * total / max_total)
        zero_h = round(total_h * zero / total) if total else 0
        answered_h = max(total_h - zero_h, 0)
        y_answered = plot_h - total_h
        y_zero = plot_h - zero_h
        title = (
            f'{row.get("date", "")}: {total} questions, '
            f"{answered} answered, {zero} without citations"
        )
        if answered_h > 0:
            bars.append(
                f'<rect x="{x}" y="{y_answered}" width="{bar_w}" height="{answered_h}" '
                f'rx="3" fill="{COLORS["accent"]}"><title>{_esc(title)}</title></rect>'
            )
        if zero_h > 0:
            # 2px surface gap separates the two segments.
            bars.append(
                f'<rect x="{x}" y="{y_zero}" width="{bar_w}" height="{zero_h}" '
                f'rx="3" fill="{COLORS["yellow"]}"><title>{_esc(title)}</title></rect>'
            )
        bars.append(
            f'<text x="{x + bar_w / 2}" y="{plot_h + 16}" text-anchor="middle" '
            f'class="axis" font-size="9">{_esc(str(row.get("date", ""))[5:])}</text>'
        )
        bars.append(
            f'<text x="{x + bar_w / 2}" y="{y_answered - 4}" text-anchor="middle" '
            f'class="axis" font-size="9">{total}</text>'
        )

    legend = (
        '<div class="legend">'
        f'<span><i style="background:{COLORS["accent"]}"></i>Answered</span>'
        f'<span><i style="background:{COLORS["yellow"]}"></i>No citations</span>'
        "</div>"
    )
    svg = (
        f'<svg viewBox="0 0 {width} {height}" width="100%" '
        f'preserveAspectRatio="xMinYMid meet" role="img" '
        f'aria-label="Daily question volume">{"".join(bars)}</svg>'
    )
    return legend + '<div class="chart-scroll">' + svg + "</div>"


def _satisfaction_bar(helpful: int, unhelpful: int) -> str:
    total = helpful + unhelpful
    if total == 0:
        return '<p class="empty">No feedback submitted yet.</p>'
    help_pct = round(100 * helpful / total)
    unhelp_pct = 100 - help_pct
    return (
        '<div class="split-bar">'
        f'<div style="width:{help_pct}%;background:{COLORS["green"]}">'
        f'{help_pct}% helpful</div>'
        f'<div style="width:{unhelp_pct}%;background:{COLORS["red"]}">'
        f'{unhelp_pct}%</div>'
        "</div>"
        f'<div class="split-legend"><span>{helpful} helpful</span>'
        f'<span>{unhelpful} unhelpful</span></div>'
    )


def _question_rows(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<tr><td colspan="3" class="empty">No questions recorded.</td></tr>'
    out = []
    for row in rows:
        cites = int(row.get("max_citations", 0))
        badge = (
            f'<span class="pill pill-red">0</span>'
            if cites == 0
            else f'<span class="pill pill-green">{cites}</span>'
        )
        out.append(
            "<tr>"
            f'<td>{_esc(row.get("question", ""))}</td>'
            f'<td class="num">{int(row.get("count", 0))}</td>'
            f'<td class="num">{badge}</td>'
            "</tr>"
        )
    return "".join(out)


def _gap_rows(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<tr><td colspan="3" class="empty">No doc-gap candidates. Coverage looks healthy.</td></tr>'
    labels = {"no_citations": "No citations", "marked_unhelpful": "Marked unhelpful"}
    out = []
    for row in rows[:25]:
        reason = str(row.get("reason", ""))
        tone = "pill-amber" if reason == "no_citations" else "pill-red"
        out.append(
            "<tr>"
            f'<td>{_esc(row.get("question", ""))}</td>'
            f'<td class="num">{int(row.get("count", 0))}</td>'
            f'<td><span class="pill {tone}">{_esc(labels.get(reason, reason))}</span></td>'
            "</tr>"
        )
    return "".join(out)


def render_dashboard(report: dict[str, Any]) -> str:
    totals = report.get("totals", {})
    window = report.get("window_days", 0)
    window_label = "all history" if not window else f"last {window} days"
    questions = int(totals.get("questions", 0))
    unique = int(totals.get("unique_questions", 0))
    answer_rate = totals.get("answer_rate")
    helpful_rate = totals.get("helpful_rate")
    zero_rate = totals.get("zero_citation_rate")
    feedback_events = int(totals.get("feedback_events", 0))
    helpful = int(totals.get("helpful", 0))
    unhelpful = int(totals.get("unhelpful", 0))
    gaps = report.get("doc_gap_candidates", [])

    tiles = "".join(
        [
            _stat_tile("Questions asked", f"{questions:,}", f"{unique:,} unique", "blue"),
            _stat_tile("Answer rate", _pct(answer_rate), "grounded in docs", "green"),
            _stat_tile(
                "Coverage gap",
                _pct(zero_rate),
                f"{int(totals.get('zero_citation_questions', 0)):,} without citations",
                "yellow" if (zero_rate or 0) < 0.3 else "red",
            ),
            _stat_tile(
                "Helpful rate",
                _pct(helpful_rate),
                f"{feedback_events:,} ratings",
                "green" if (helpful_rate or 0) >= 0.6 else "yellow",
            ),
            _stat_tile("Doc-gap candidates", f"{len(gaps):,}", "ready to route to docs", "accent"),
        ]
    )

    css = f"""
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
      background: {COLORS['bg']}; color: {COLORS['text']}; line-height: 1.5;
      min-height: 100vh; padding: 32px 24px;
    }}
    .wrap {{ max-width: 1200px; margin: 0 auto; }}
    .header {{ display: flex; justify-content: space-between; align-items: flex-end;
      border-bottom: 1px solid {COLORS['surface2']}; padding-bottom: 20px; margin-bottom: 28px; }}
    .header h1 {{ font-size: 1.6rem; font-weight: 700;
      background: linear-gradient(135deg, #818cf8, #6366f1, #4f46e5);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
    .header .sub {{ color: {COLORS['muted']}; font-size: .85rem; margin-top: 4px; }}
    .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: .7rem;
      font-weight: 600; text-transform: uppercase; letter-spacing: .05em;
      background: rgba(16,185,129,0.15); color: {COLORS['green']}; }}
    .tiles {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px; margin-bottom: 28px; }}
    .tile {{ background: {COLORS['surface']}; border: 1px solid {COLORS['surface2']};
      border-radius: 14px; padding: 18px 20px; }}
    .tile-value {{ font-size: 1.9rem; font-weight: 700; line-height: 1.1; }}
    .tile-label {{ font-size: .8rem; font-weight: 600; margin-top: 6px; }}
    .tile-sub {{ font-size: .72rem; color: {COLORS['muted']}; margin-top: 2px; }}
    .grid {{ display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 24px; }}
    .card {{ background: {COLORS['surface']}; border: 1px solid {COLORS['surface2']};
      border-radius: 14px; padding: 20px; }}
    .card h2 {{ font-size: 1rem; font-weight: 600; margin-bottom: 14px; }}
    .card h2 .hint {{ font-size: .72rem; color: {COLORS['muted']}; font-weight: 400; }}
    .chart-scroll {{ overflow-x: auto; }}
    .axis {{ fill: {COLORS['muted']}; }}
    .legend {{ display: flex; gap: 16px; font-size: .75rem; color: {COLORS['muted']};
      margin-bottom: 10px; }}
    .legend i {{ display: inline-block; width: 10px; height: 10px; border-radius: 3px;
      margin-right: 6px; vertical-align: middle; }}
    .split-bar {{ display: flex; height: 34px; border-radius: 8px; overflow: hidden;
      font-size: .75rem; font-weight: 600; color: #06231a; }}
    .split-bar div {{ display: flex; align-items: center; justify-content: center;
      min-width: 32px; color: #fff; }}
    .split-legend {{ display: flex; justify-content: space-between; font-size: .75rem;
      color: {COLORS['muted']}; margin-top: 8px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: .82rem; }}
    th {{ text-align: left; color: {COLORS['muted']}; font-weight: 600; font-size: .72rem;
      text-transform: uppercase; letter-spacing: .04em; padding: 8px 10px;
      border-bottom: 1px solid {COLORS['surface2']}; }}
    td {{ padding: 9px 10px; border-bottom: 1px solid {COLORS['surface2']}; vertical-align: top; }}
    td.num {{ text-align: right; white-space: nowrap; }}
    tr:last-child td {{ border-bottom: none; }}
    .pill {{ display: inline-block; padding: 2px 9px; border-radius: 12px; font-size: .72rem;
      font-weight: 600; }}
    .pill-green {{ background: rgba(16,185,129,0.15); color: {COLORS['green']}; }}
    .pill-amber {{ background: rgba(245,158,11,0.15); color: {COLORS['yellow']}; }}
    .pill-red {{ background: rgba(239,68,68,0.15); color: {COLORS['red']}; }}
    .empty {{ color: {COLORS['muted']}; font-size: .82rem; padding: 12px 0; }}
    .full {{ margin-bottom: 24px; }}
    @media (max-width: 820px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    """

    generated = _fmt_ts(report.get("generated_at", ""))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Ask AI Analytics</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <div>
      <h1>Ask AI Analytics</h1>
      <div class="sub">Assistant usage, answer coverage, and doc-gap signals &middot; {_esc(window_label)}</div>
    </div>
    <div style="text-align:right;">
      <span class="badge">Live</span>
      <div class="sub">Generated {_esc(generated)}</div>
    </div>
  </div>

  <div class="tiles">{tiles}</div>

  <div class="grid">
    <div class="card">
      <h2>Daily question volume <span class="hint">answered vs. no citations</span></h2>
      {_volume_chart(report.get("daily", []))}
    </div>
    <div class="card">
      <h2>Answer satisfaction <span class="hint">from thumbs up / down</span></h2>
      {_satisfaction_bar(helpful, unhelpful)}
    </div>
  </div>

  <div class="card full">
    <h2>Doc-gap candidates <span class="hint">route these to the docs pipeline</span></h2>
    <table>
      <thead><tr><th>Question</th><th class="num">Count</th><th>Reason</th></tr></thead>
      <tbody>{_gap_rows(gaps)}</tbody>
    </table>
  </div>

  <div class="card full">
    <h2>Top questions <span class="hint">most frequently asked</span></h2>
    <table>
      <thead><tr><th>Question</th><th class="num">Count</th><th class="num">Citations</th></tr></thead>
      <tbody>{_question_rows(report.get("top_questions", []))}</tbody>
    </table>
  </div>
</div>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Ask AI usage report into an HTML dashboard")
    parser.add_argument("--report", default="reports/ask_ai_usage_report.json")
    parser.add_argument("--output", default="reports/ask-ai-analytics.html")
    args = parser.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        print(f"[ask-ai-dashboard] report not found: {report_path}")
        print("[ask-ai-dashboard] run scripts/report_ask_ai_usage.py first")
        return 1

    report = json.loads(report_path.read_text(encoding="utf-8"))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_dashboard(report), encoding="utf-8")

    totals = report.get("totals", {})
    print(
        f"[ask-ai-dashboard] questions={totals.get('questions', 0)} "
        f"answer-rate={_pct(totals.get('answer_rate'))} "
        f"gaps={len(report.get('doc_gap_candidates', []))}"
    )
    print(f"[ask-ai-dashboard] dashboard: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

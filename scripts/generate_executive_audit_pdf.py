#!/usr/bin/env python3
"""Generate one-page executive PDF from deterministic + LLM audit outputs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def _pick_llm_block(public_payload: dict[str, Any], llm_payload: dict[str, Any]) -> dict[str, Any]:
    if isinstance(llm_payload.get("analysis"), dict):
        return llm_payload["analysis"]
    llm = public_payload.get("llm_analysis", {})
    if isinstance(llm, dict) and isinstance(llm.get("analysis"), dict):
        return llm["analysis"]
    return {}


def _format_money(value: Any) -> str:
    try:
        amount = float(value)
    except Exception:  # noqa: BLE001
        amount = 0.0
    return "${:,.0f}".format(amount)


def _risk_band(score: float) -> str:
    if score >= 85:
        return "Low"
    if score >= 70:
        return "Moderate"
    if score >= 55:
        return "High"
    return "Critical"


def _status_color(label: str) -> colors.Color:
    key = label.strip().lower()
    if key == "low":
        return colors.HexColor("#047857")
    if key == "moderate":
        return colors.HexColor("#0f766e")
    if key == "high":
        return colors.HexColor("#b45309")
    if key == "critical":
        return colors.HexColor("#b42318")
    return colors.HexColor("#334155")


def _status_color_hex(label: str) -> str:
    key = label.strip().lower()
    if key == "low":
        return "#047857"
    if key == "moderate":
        return "#0f766e"
    if key == "high":
        return "#b45309"
    if key == "critical":
        return "#b42318"
    return "#334155"


def _metric_card_table(data: list[list[str]]) -> Table:
    table = Table(data, colWidths=[57 * mm, 33 * mm, 57 * mm, 33 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbe4f0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e8eef7")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fbff")),
                ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f8fbff")),
            ]
        )
    )
    return table


def _hero_table(title: str, subtitle: str, score: str, grade: str, risk_band: str) -> Table:
    risk_color = _status_color_hex(risk_band)
    data = [
        [
            Paragraph(f"<b>{title}</b><br/><font size='8' color='#64748b'>{subtitle}</font>", ParagraphStyle("hero_title")),
            Paragraph(
                "<b>Audit Score</b><br/><font size='18' color='#155eef'><b>{}</b></font>"
                "<font size='9' color='#64748b'> / 100</font>".format(score),
                ParagraphStyle("hero_score"),
            ),
            Paragraph(
                "<b>Grade</b><br/><font size='16' color='#0f766e'><b>{}</b></font>".format(grade),
                ParagraphStyle("hero_grade"),
            ),
            Paragraph(
                "<b>Risk Band</b><br/><font size='12' color='{}'><b>{}</b></font>".format(
                    risk_color,
                    risk_band,
                ),
                ParagraphStyle("hero_risk"),
            ),
        ]
    ]
    table = Table(data, colWidths=[98 * mm, 28 * mm, 24 * mm, 24 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fbff")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#cfdcf0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e3ebf7")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def _financial_table(base: dict[str, Any], totals: dict[str, Any]) -> Table:
    data = [
        ["Financial Exposure", "Low", "Base", "High", "Basis"],
        [
            "Remediation cost (one-time)",
            _format_money(totals.get("remediation_cost_usd_low_total", 0)),
            _format_money(totals.get("remediation_cost_usd_base_total", 0)),
            _format_money(totals.get("remediation_cost_usd_high_total", 0)),
            "Finding-level effort model",
        ],
        [
            "Monthly loss",
            _format_money(totals.get("monthly_loss_usd_low_total", 0)),
            _format_money(totals.get("monthly_loss_usd_base_total", 0)),
            _format_money(totals.get("monthly_loss_usd_high_total", 0)),
            "Operational friction model",
        ],
        [
            "Opportunity cost (macro)",
            _format_money(base.get("monthly_cost_usd", 0)),
            _format_money(base.get("monthly_cost_usd", 0)),
            _format_money(base.get("monthly_cost_usd", 0)),
            "Engineering/support/release delay",
        ],
    ]
    table = Table(data, colWidths=[58 * mm, 23 * mm, 23 * mm, 23 * mm, 43 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef4ff")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.6),
                ("ALIGN", (1, 1), (3, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8e3f6")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e7edf8")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _risk_matrix(findings: list[dict[str, Any]]) -> Table:
    rows = [["ID", "Issue", "Severity", "Monthly Loss (Base)", "Fix Cost (Base)"]]
    for item in findings[:4]:
        rows.append(
            [
                str(item.get("id", "")),
                str(item.get("title", ""))[:58],
                str(item.get("severity", "n/a")).upper(),
                _format_money(item.get("estimated_monthly_loss_usd_base", 0)),
                _format_money(item.get("estimated_remediation_cost_usd_base", 0)),
            ]
        )
    if len(rows) == 1:
        rows.append(["-", "No findings captured.", "-", "-", "-"])
    table = Table(rows, colWidths=[18 * mm, 76 * mm, 21 * mm, 33 * mm, 33 * mm])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fff7ed")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#9a3412")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.4),
        ("ALIGN", (3, 1), (4, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1d7c8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#f5e3d7")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for idx, row in enumerate(rows[1:], start=1):
        sev = str(row[2]).lower()
        if sev == "high":
            style.append(("TEXTCOLOR", (2, idx), (2, idx), colors.HexColor("#b42318")))
        elif sev == "medium":
            style.append(("TEXTCOLOR", (2, idx), (2, idx), colors.HexColor("#b45309")))
        elif sev == "low":
            style.append(("TEXTCOLOR", (2, idx), (2, idx), colors.HexColor("#047857")))
    table.setStyle(TableStyle(style))
    return table


def _assumptions_table(assumptions: dict[str, Any]) -> Table:
    rows = [["Assumption", "Value"]]
    for key, value in assumptions.items():
        rows.append([str(key), str(value)])
    if len(rows) == 1:
        rows.append(["No assumptions provided", "-"])
    table = Table(rows, colWidths=[85 * mm, 96 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.2),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d7e0f3")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5ebf8")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _evidence_table(findings: list[dict[str, Any]]) -> Table:
    rows = [["Finding", "Evidence Source", "Confidence"]]
    for item in findings[:8]:
        rows.append(
            [
                f"{item.get('id', '')} — {str(item.get('title', ''))[:40]}",
                str(item.get("evidence_source", ""))[:62] or "-",
                str(item.get("estimation_confidence", "n/a")),
            ]
        )
    if len(rows) == 1:
        rows.append(["No findings captured", "-", "-"])
    table = Table(rows, colWidths=[70 * mm, 84 * mm, 27 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#effcf6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#065f46")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.1),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfe7dc")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e0f0e8")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _paragraphs(items: list[str], style: ParagraphStyle, max_items: int) -> list[Paragraph]:
    out: list[Paragraph] = []
    for item in items[:max_items]:
        cleaned = str(item).strip()
        if not cleaned:
            continue
        out.append(Paragraph(f"• {cleaned}", style))
    return out


def _build_pdf(
    output_path: Path,
    scorecard: dict[str, Any],
    public_audit: dict[str, Any],
    llm_analysis: dict[str, Any],
    company_name: str,
    report_style: str,
) -> None:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleExec",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=19,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleExec",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.4,
        leading=10.6,
        textColor=colors.HexColor("#475569"),
        spaceAfter=6,
    )
    section_style = ParagraphStyle(
        "SectionExec",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.3,
        leading=12.4,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=5,
        spaceAfter=3,
    )
    body_style = ParagraphStyle(
        "BodyExec",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=10.8,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=2,
    )

    score = scorecard.get("score", {})
    kpis = scorecard.get("kpis", {})
    totals = scorecard.get("findings_totals", {})
    findings = scorecard.get("findings", [])
    assumptions = scorecard.get("business_impact", {}).get("assumptions", {})
    public_metrics = public_audit.get("aggregate", {}).get("metrics", {})

    api_cov = kpis.get("api_coverage", {}).get("coverage_pct", 0.0)
    ex_rel = kpis.get("example_reliability", {}).get("example_reliability_pct", 0.0)
    drift = kpis.get("drift", {}).get("docs_contract_drift_pct", 0.0)
    retrieval = kpis.get("retrieval_quality", {}).get("hallucination_rate", 0.0)

    seo_geo = public_metrics.get("seo_geo", {}).get("seo_geo_issue_rate_pct", 0.0)
    public_api_cov = public_metrics.get("api_coverage", {}).get("reference_coverage_pct", 0.0)
    broken_links = public_metrics.get("links", {}).get("broken_internal_links_count", 0)
    pages = public_metrics.get("crawl", {}).get("pages_crawled", 0)
    score_value = float(score.get("audit_score_0_100", 0.0) or 0.0)
    risk_band = _risk_band(score_value)

    cards = [
        ["Audit score", str(score.get("audit_score_0_100", "n/a")), "Grade", str(score.get("grade", "n/a"))],
        ["Internal API coverage", f"{api_cov}%", "Public API coverage", f"{public_api_cov}%"],
        ["Example reliability", f"{ex_rel}%", "Docs drift", f"{drift}%"],
        ["RAG hallucination rate", f"{round(float(retrieval) * 100.0, 2)}%", "Public broken links", str(broken_links)],
    ]

    impact_base = scorecard.get("business_impact", {}).get("scenarios", {}).get("base", {})

    risk_items: list[str] = []
    for item in findings[:3]:
        risk_items.append(
            f"{item.get('title', 'Issue')}: gap {item.get('gap_value', 'n/a')}{item.get('unit', '')}, "
            f"fix cost {_format_money(item.get('estimated_remediation_cost_usd_base', 0))}"
        )
    for item in (public_audit.get("top_findings", []) or [])[:2]:
        risk_items.append(str(item))

    action_items = []
    if isinstance(llm_analysis.get("prioritized_actions"), list):
        action_items = [str(v) for v in llm_analysis.get("prioritized_actions", [])]
    if not action_items:
        action_items = [
            "Fix high-severity findings from the matrix and close evidence gaps in reports.",
            "Enable weekly scorecard run and enforce finalize gate in docs generation flow.",
            "Raise API + usage-doc coverage and execute example smoke checks on every cycle.",
        ]

    summary_text = str(llm_analysis.get("executive_summary", "")).strip()
    if not summary_text:
        summary_text = (
            f"{company_name} documentation has measurable quality and drift risk. "
            "The pipeline can close these gaps with a prioritized, module-linked remediation plan."
        )

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title="Executive Docs Audit One-Pager",
        author="VeriOps",
    )

    content = [
        _hero_table(
            f"{company_name} — Executive Documentation Audit",
            f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | Public pages scanned: {pages}",
            f"{score_value:.1f}",
            str(score.get("grade", "n/a")),
            risk_band,
        ),
        Spacer(1, 2.4 * mm),
        Paragraph("Board-Level Snapshot", section_style),
        _metric_card_table(cards),
        Spacer(1, 2.8 * mm),
        Paragraph("Executive Narrative", section_style),
        Paragraph(summary_text, body_style),
        Paragraph(
            f"External posture: SEO/GEO issue rate <b>{seo_geo}%</b>, public API coverage <b>{public_api_cov}%</b>, "
            f"broken links <b>{broken_links}</b>.",
            body_style,
        ),
        Paragraph("Financial Exposure Model", section_style),
        _financial_table(impact_base if isinstance(impact_base, dict) else {}, totals),
        Spacer(1, 2.4 * mm),
        Paragraph("Top Risk Matrix", section_style),
        _risk_matrix(findings),
        Spacer(1, 2.2 * mm),
        Paragraph("Priority Action Plan (Next 14 Days)", section_style),
    ]
    content.extend(_paragraphs(risk_items, body_style, max_items=5))
    content.extend(_paragraphs(action_items, body_style, max_items=4))
    content.append(
        Paragraph(
            "Assumptions and evidence links are included in scorecard artifacts for audit defensibility.",
            subtitle_style,
        )
    )

    if report_style == "board-memo":
        content.extend(
            [
                PageBreak(),
                Paragraph("Appendix A — Assumptions (Economic Model Inputs)", section_style),
                _assumptions_table(assumptions if isinstance(assumptions, dict) else {}),
                Spacer(1, 2.4 * mm),
                Paragraph("Appendix B — Evidence Traceability", section_style),
                _evidence_table(findings),
                Spacer(1, 2.4 * mm),
                Paragraph(
                    "Note: estimates are directional and should be calibrated with client rates, release cadence, and support volume.",
                    subtitle_style,
                ),
            ]
        )

    doc.build(content)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate executive audit PDF from audit outputs")
    parser.add_argument("--scorecard-json", default="reports/audit_scorecard.json")
    parser.add_argument("--public-audit-json", default="reports/public_docs_audit.json")
    parser.add_argument("--llm-summary-json", default="reports/public_docs_audit_llm_summary.json")
    parser.add_argument("--company-name", default="Client")
    parser.add_argument("--output", default="reports/executive_audit_one_pager.pdf")
    parser.add_argument(
        "--report-style",
        choices=["one-pager", "board-memo"],
        default="board-memo",
        help="one-pager for short summary, board-memo for premium report with appendix.",
    )
    args = parser.parse_args()

    scorecard = _read_json(Path(args.scorecard_json))
    public_audit = _read_json(Path(args.public_audit_json))
    llm_summary = _read_json(Path(args.llm_summary_json))

    if not scorecard:
        raise SystemExit(f"Missing or invalid scorecard JSON: {args.scorecard_json}")
    if not public_audit:
        raise SystemExit(f"Missing or invalid public audit JSON: {args.public_audit_json}")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    llm_block = _pick_llm_block(public_audit, llm_summary)
    _build_pdf(
        output_path=output,
        scorecard=scorecard,
        public_audit=public_audit,
        llm_analysis=llm_block,
        company_name=str(args.company_name),
        report_style=str(args.report_style),
    )
    print(f"[ok] executive pdf: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

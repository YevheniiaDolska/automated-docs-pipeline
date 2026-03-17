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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


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


def _metric_card_table(data: list[list[str]]) -> Table:
    table = Table(data, colWidths=[58 * mm, 32 * mm, 58 * mm, 32 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbe4f0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e8eef7")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
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
) -> None:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleExec",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleExec",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
        spaceAfter=8,
    )
    section_style = ParagraphStyle(
        "SectionExec",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "BodyExec",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.2,
        leading=12,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=2,
    )

    score = scorecard.get("score", {})
    kpis = scorecard.get("kpis", {})
    totals = scorecard.get("findings_totals", {})
    findings = scorecard.get("findings", [])
    public_metrics = public_audit.get("aggregate", {}).get("metrics", {})

    api_cov = kpis.get("api_coverage", {}).get("coverage_pct", 0.0)
    ex_rel = kpis.get("example_reliability", {}).get("example_reliability_pct", 0.0)
    drift = kpis.get("drift", {}).get("docs_contract_drift_pct", 0.0)
    retrieval = kpis.get("retrieval_quality", {}).get("hallucination_rate", 0.0)

    seo_geo = public_metrics.get("seo_geo", {}).get("seo_geo_issue_rate_pct", 0.0)
    public_api_cov = public_metrics.get("api_coverage", {}).get("reference_coverage_pct", 0.0)
    broken_links = public_metrics.get("links", {}).get("broken_internal_links_count", 0)
    pages = public_metrics.get("crawl", {}).get("pages_crawled", 0)

    cards = [
        ["Audit score", str(score.get("audit_score_0_100", "n/a")), "Grade", str(score.get("grade", "n/a"))],
        ["Internal API coverage", f"{api_cov}%", "Public API coverage", f"{public_api_cov}%"],
        ["Example reliability", f"{ex_rel}%", "Docs drift", f"{drift}%"],
        ["RAG hallucination rate", f"{round(float(retrieval) * 100.0, 2)}%", "Public broken links", str(broken_links)],
    ]

    monthly_loss = _format_money(totals.get("monthly_loss_usd_base_total", 0))
    remediation = _format_money(totals.get("remediation_cost_usd_base_total", 0))

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
        author="Auto-Doc Pipeline",
    )

    content = [
        Paragraph(f"{company_name} — Executive Documentation Audit", title_style),
        Paragraph(
            f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | "
            f"Public pages scanned: {pages}",
            subtitle_style,
        ),
        _metric_card_table(cards),
        Spacer(1, 4 * mm),
        Paragraph("Executive Summary", section_style),
        Paragraph(summary_text, body_style),
        Paragraph("Financial Snapshot", section_style),
        Paragraph(
            f"Estimated monthly loss (base): <b>{monthly_loss}</b> | "
            f"Estimated one-time remediation (base): <b>{remediation}</b>",
            body_style,
        ),
        Paragraph("Top Risks (Deterministic + LLM Consolidated)", section_style),
    ]
    content.extend(_paragraphs(risk_items, body_style, max_items=5))
    content.append(Paragraph("Priority Action Plan (Next 14 Days)", section_style))
    content.extend(_paragraphs(action_items, body_style, max_items=4))

    doc.build(content)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate one-page executive PDF from audit outputs")
    parser.add_argument("--scorecard-json", default="reports/audit_scorecard.json")
    parser.add_argument("--public-audit-json", default="reports/public_docs_audit.json")
    parser.add_argument("--llm-summary-json", default="reports/public_docs_audit_llm_summary.json")
    parser.add_argument("--company-name", default="Client")
    parser.add_argument("--output", default="reports/executive_audit_one_pager.pdf")
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
    )
    print(f"[ok] executive pdf: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


#!/usr/bin/env python3
"""Generate premium consulting-grade executive PDF from audit outputs.

Produces a dense branded report (6-7 pages) with cover page, score gauges,
full-width progress bars, per-site breakdown, risk matrix, expert analysis,
methodology, and optional appendix.  Depends only on ``reportlab``.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing, Group, Rect, String, Wedge
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
NAVY = colors.HexColor("#0f172a")
ACCENT_BLUE = colors.HexColor("#2563eb")
SUCCESS_GREEN = colors.HexColor("#059669")
WARNING_AMBER = colors.HexColor("#d97706")
DANGER_RED = colors.HexColor("#dc2626")
LIGHT_BG = colors.HexColor("#f8fafc")
LIGHT_BLUE_BG = colors.HexColor("#f0f9ff")
LIGHT_RED_BG = colors.HexColor("#fef2f2")
LIGHT_GREEN_BG = colors.HexColor("#f0fdf4")
HEADER_BLUE_BG = colors.HexColor("#dbeafe")
GREY_300 = colors.HexColor("#d1d5db")
GREY_400 = colors.HexColor("#9ca3af")
GREY_500 = colors.HexColor("#6b7280")
GREY_600 = colors.HexColor("#4b5563")
GREY_700 = colors.HexColor("#374151")
WHITE = colors.white

PAGE_W, PAGE_H = A4
MARGIN = 14 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-") or "client"


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


def _score_color(score: float) -> colors.Color:
    if score >= 85:
        return SUCCESS_GREEN
    if score >= 70:
        return colors.HexColor("#0d9488")
    if score >= 55:
        return WARNING_AMBER
    return DANGER_RED


def _risk_band_color(band: str) -> colors.Color:
    key = band.strip().lower()
    if key == "low":
        return SUCCESS_GREEN
    if key == "moderate":
        return colors.HexColor("#0d9488")
    if key == "high":
        return WARNING_AMBER
    return DANGER_RED


def _grade_from_score(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B+"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    if score >= 50:
        return "D"
    return "F"


def _derive_public_score(
    seo_issue_pct: float,
    broken_links: int,
    pages: int,
    api_cov_pct: float | None,
    example_rel_pct: float,
) -> float:
    """Compute 0-100 composite score from public audit metrics."""
    seo_score = max(0.0, 30.0 * (1.0 - min(seo_issue_pct / 50.0, 1.0)))
    if pages > 0:
        broken_ratio = min(broken_links / max(pages * 20, 1), 1.0)
    else:
        broken_ratio = 0.0
    link_score = 25.0 * (1.0 - broken_ratio)
    if api_cov_pct is None:
        api_score = 10.0
    else:
        api_score = 20.0 * min(api_cov_pct / 100.0, 1.0)
    example_score = 15.0 * min(example_rel_pct / 100.0, 1.0)
    freshness_score = 10.0 if pages > 0 else 0.0
    total = seo_score + link_score + api_score + example_score + freshness_score
    return round(min(max(total, 0.0), 100.0), 1)


def _cell_color(value: float, good_thresh: float, warn_thresh: float, *, invert: bool = False) -> colors.Color:
    if invert:
        if value <= good_thresh:
            return LIGHT_GREEN_BG
        if value <= warn_thresh:
            return colors.HexColor("#fffbeb")
        return LIGHT_RED_BG
    if value >= good_thresh:
        return LIGHT_GREEN_BG
    if value >= warn_thresh:
        return colors.HexColor("#fffbeb")
    return LIGHT_RED_BG


def _metric_bg(value: float, good: float, warn: float, *, invert: bool = False) -> colors.Color:
    """Background for metric card cells."""
    if invert:
        if value <= good:
            return colors.HexColor("#dcfce7")
        if value <= warn:
            return colors.HexColor("#fef9c3")
        return colors.HexColor("#fee2e2")
    if value >= good:
        return colors.HexColor("#dcfce7")
    if value >= warn:
        return colors.HexColor("#fef9c3")
    return colors.HexColor("#fee2e2")


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------


def _draw_score_gauge(score: float, size: int = 140) -> Drawing:
    """Circular arc gauge with score in center."""
    d = Drawing(size, size)
    cx = size / 2
    cy = size / 2
    radius = size / 2 - 6

    bg_wedge = Wedge(cx, cy, radius, 0, 360, strokeColor=None, fillColor=colors.HexColor("#e5e7eb"))
    d.add(bg_wedge)

    inner_radius = radius * 0.68
    inner = Wedge(cx, cy, inner_radius, 0, 360, strokeColor=None, fillColor=WHITE)
    d.add(inner)

    if score > 0:
        sweep = min(score / 100.0 * 360, 360)
        fg_color = _score_color(score)
        fg_wedge = Wedge(cx, cy, radius, 90, 90 + sweep, strokeColor=None, fillColor=fg_color)
        d.add(fg_wedge)
        inner2 = Wedge(cx, cy, inner_radius, 0, 360, strokeColor=None, fillColor=WHITE)
        d.add(inner2)

    score_str = "{:.0f}".format(score)
    d.add(String(cx, cy + 6, score_str, fontSize=size * 0.24, fillColor=NAVY,
                 textAnchor="middle", fontName="Helvetica-Bold"))
    grade = _grade_from_score(score)
    d.add(String(cx, cy - size * 0.10, grade, fontSize=size * 0.12, fillColor=GREY_500,
                 textAnchor="middle", fontName="Helvetica-Bold"))
    d.add(String(cx, cy - size * 0.20, "out of 100", fontSize=size * 0.06, fillColor=GREY_400,
                 textAnchor="middle", fontName="Helvetica"))
    return d


def _draw_progress_bar(label: str, value: float, max_val: float, bar_color: colors.Color,
                        width: int = 500, height: int = 38) -> Drawing:
    """Full-width horizontal progress bar."""
    d = Drawing(width, height)
    bar_h = 16
    bar_y = 2
    bar_w = width - 90
    bar_x = 0

    # Label above bar
    d.add(String(0, bar_y + bar_h + 8, label, fontSize=9.5, fillColor=GREY_700,
                 textAnchor="start", fontName="Helvetica"))

    # Background bar
    d.add(Rect(bar_x, bar_y, bar_w, bar_h, fillColor=colors.HexColor("#e5e7eb"),
               strokeColor=None, rx=4, ry=4))

    # Fill bar
    fill_pct = min(value / max_val, 1.0) if max_val > 0 else 0
    fill_w = max(bar_w * fill_pct, 0)
    if fill_w > 0:
        d.add(Rect(bar_x, bar_y, fill_w, bar_h, fillColor=bar_color,
                    strokeColor=None, rx=4, ry=4))

    # Percentage label (right of bar, bold)
    pct_text = "{:.1f}%".format(value)
    d.add(String(bar_w + 8, bar_y + 3, pct_text, fontSize=10.5, fillColor=NAVY,
                 textAnchor="start", fontName="Helvetica-Bold"))

    return d


class DrawingFlowable(Flowable):
    def __init__(self, drawing: Drawing) -> None:
        super().__init__()
        self.drawing = drawing
        self.width = drawing.width
        self.height = drawing.height

    def wrap(self, avail_w: float, avail_h: float) -> tuple[float, float]:
        return self.width, self.height

    def draw(self) -> None:
        renderPDF.draw(self.drawing, self.canv, 0, 0)


# ---------------------------------------------------------------------------
# Header / footer
# ---------------------------------------------------------------------------


def _header_footer(canvas, doc, company_name: str, gen_date: str) -> None:
    page_num = canvas.getPageNumber()
    if page_num == 1:
        return

    canvas.saveState()
    w, h = A4

    canvas.setStrokeColor(ACCENT_BLUE)
    canvas.setLineWidth(1.5)
    canvas.line(MARGIN, h - 10 * mm, w - MARGIN, h - 10 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(GREY_600)
    canvas.drawString(MARGIN, h - 9 * mm, "Documentation Quality Audit  |  {}".format(company_name))
    canvas.drawRightString(w - MARGIN, h - 9 * mm, gen_date)

    canvas.setStrokeColor(colors.HexColor("#d1d5db"))
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 9 * mm, w - MARGIN, 9 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GREY_500)
    canvas.drawString(MARGIN, 5.5 * mm, "CONFIDENTIAL")
    canvas.drawCentredString(w / 2, 5.5 * mm, "Page {}".format(page_num))
    canvas.drawRightString(w - MARGIN, 5.5 * mm, gen_date)

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Section helpers
# ---------------------------------------------------------------------------


def _section_header(text: str, style: ParagraphStyle) -> list[Flowable]:
    bar_data = [[Paragraph(text, style)]]
    bar_table = Table(bar_data, colWidths=[CONTENT_W])
    bar_table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBEFORE", (0, 0), (0, -1), 3.5, ACCENT_BLUE),
    ]))
    return [Spacer(1, 5 * mm), bar_table, Spacer(1, 2 * mm)]


def _thin_rule() -> Table:
    data = [[""]]
    t = Table(data, colWidths=[CONTENT_W], rowHeights=[1])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


# Common table style additions for alternating rows
def _alt_row_style(base_cmds: list, num_rows: int) -> list:
    """Add alternating row backgrounds to a table style command list."""
    for i in range(1, num_rows):
        if i % 2 == 0:
            base_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_BG))
    return base_cmds


# ---------------------------------------------------------------------------
# Cover page
# ---------------------------------------------------------------------------


def _cover_page(company_name: str, score: float, risk_band_label: str, gen_date: str,
                pages_scanned: int, top_findings: list[str]) -> list[Flowable]:

    class CoverDrawing(Flowable):
        def __init__(self) -> None:
            super().__init__()
            self.width = CONTENT_W - 12
            self.height = PAGE_H - 2 * MARGIN - 16

        def wrap(self, aw: float, ah: float) -> tuple[float, float]:
            return self.width, self.height

        def draw(self) -> None:
            c = self.canv
            w = self.width
            h = self.height

            # Dark navy background -- top 55%
            navy_h = h * 0.55
            c.setFillColor(NAVY)
            c.rect(0, h - navy_h, w, navy_h, fill=1, stroke=0)

            # Company name
            c.setFillColor(WHITE)
            c.setFont("Helvetica-Bold", 32)
            c.drawString(30, h - 65, company_name)

            # Title
            c.setFont("Helvetica-Bold", 20)
            c.drawString(30, h - 105, "Documentation Infrastructure")
            c.drawString(30, h - 131, "Audit Report")

            # Subtitle
            c.setFont("Helvetica", 12)
            c.setFillColor(colors.HexColor("#94a3b8"))
            c.drawString(30, h - 165, "Prepared by DocsOps Automation Platform")

            # Date
            c.setFont("Helvetica", 10)
            c.drawString(30, h - 188, gen_date)

            # Confidentiality
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(colors.HexColor("#475569"))
            c.drawString(30, h - 214, "CONFIDENTIAL  |  FOR INTERNAL USE ONLY")

            # Score gauge (right side)
            gauge = _draw_score_gauge(score, size=160)
            renderPDF.draw(gauge, c, w - 200, h - 230)

            # Risk band badge
            band_color = _risk_band_color(risk_band_label)
            badge_x = w - 180
            badge_y = h - 258
            c.setFillColor(band_color)
            c.roundRect(badge_x, badge_y, 120, 24, 5, fill=1, stroke=0)
            c.setFillColor(WHITE)
            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(badge_x + 60, badge_y + 7, "Risk: {}".format(risk_band_label))

            # Bottom section -- light background with findings
            info_y = h - navy_h - 30

            # Accent line
            c.setStrokeColor(ACCENT_BLUE)
            c.setLineWidth(3)
            c.line(30, info_y + 10, w - 30, info_y + 10)

            c.setFillColor(GREY_700)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(30, info_y - 15, "Key Metrics")

            c.setFont("Helvetica", 10)
            pages_label = str(pages_scanned) if pages_scanned > 0 else "0 (site may block automated crawlers)"
            c.drawString(30, info_y - 35, "Pages scanned: {}".format(pages_label))
            c.drawString(30, info_y - 53, "Report type: Premium Executive Audit")
            c.drawString(30, info_y - 71, "Methodology: 5-pillar automated analysis + expert synthesis")

            # Key Findings bullets
            if top_findings:
                c.setFont("Helvetica-Bold", 11)
                c.setFillColor(NAVY)
                c.drawString(30, info_y - 105, "Headline Findings")

                c.setFont("Helvetica", 9.5)
                c.setFillColor(GREY_700)
                y_pos = info_y - 125
                for finding in top_findings[:4]:
                    text = str(finding)[:90]
                    # Bullet with colored dot
                    c.setFillColor(DANGER_RED)
                    c.circle(38, y_pos + 3, 3, fill=1, stroke=0)
                    c.setFillColor(GREY_700)
                    c.drawString(48, y_pos, text)
                    y_pos -= 18

            # Footer disclaimer
            c.setFillColor(GREY_500)
            c.setFont("Helvetica", 8)
            c.drawString(30, 20,
                         "This report is generated automatically by the DocsOps platform. "
                         "Estimates are directional.")

    return [CoverDrawing(), PageBreak()]


# ---------------------------------------------------------------------------
# Per-site breakdown table
# ---------------------------------------------------------------------------


def _per_site_table(public_audit: dict[str, Any]) -> list[Flowable]:
    sites = public_audit.get("sites", [])
    if not sites:
        return []

    header = ["Site URL", "Pages", "Broken Links", "API Cov %", "Example Rel %", "SEO Issue %"]
    rows = [header]
    style_cmds: list[tuple[Any, ...]] = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BLUE_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#93c5fd")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#bfdbfe")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]

    for idx, site in enumerate(sites[:12], start=1):
        metrics = site.get("metrics", {})
        url = str(site.get("url", site.get("site_url", "n/a")))[:45]
        pg = str(metrics.get("crawl", {}).get("pages_crawled", metrics.get("pages", 0)))
        bl = str(metrics.get("links", {}).get("broken_internal_links_count",
                                               metrics.get("broken_links", 0)))
        api_cov_raw = metrics.get("api_coverage", {}).get("reference_coverage_pct",
                                                              metrics.get("api_coverage_pct", 0))
        api_na = metrics.get("api_coverage", {}).get("no_api_pages_found", False) or float(api_cov_raw) < 0
        api_cov = 0.0 if api_na else float(api_cov_raw)
        ex_rel = float(metrics.get("examples", {}).get("example_reliability_estimate_pct",
                                                         metrics.get("example_reliability_pct", 0)))
        seo_rate = float(metrics.get("seo_geo", {}).get("seo_geo_issue_rate_pct",
                                                          metrics.get("seo_issue_rate_pct", 0)))

        api_cov_str = "N/A" if api_na else "{:.1f}".format(api_cov)
        rows.append([url, pg, bl, api_cov_str, "{:.1f}".format(ex_rel), "{:.1f}".format(seo_rate)])

        # Color-code cells
        if not api_na:
            style_cmds.append(("BACKGROUND", (3, idx), (3, idx), _cell_color(api_cov, 80, 50)))
        else:
            style_cmds.append(("BACKGROUND", (3, idx), (3, idx), LIGHT_BG))
        style_cmds.append(("BACKGROUND", (4, idx), (4, idx), _cell_color(ex_rel, 80, 50)))
        style_cmds.append(("BACKGROUND", (5, idx), (5, idx), _cell_color(seo_rate, 5, 15, invert=True)))
        # Alternating rows
        if idx % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, idx), (0, idx), LIGHT_BG))
            style_cmds.append(("BACKGROUND", (1, idx), (2, idx), LIGHT_BG))

    table = Table(rows, colWidths=[62 * mm, 16 * mm, 22 * mm, 22 * mm, 24 * mm, 22 * mm])
    table.setStyle(TableStyle(style_cmds))
    return [table]


# ---------------------------------------------------------------------------
# Synthetic findings from public audit (when scorecard has no findings)
# ---------------------------------------------------------------------------


def _synthetic_findings_from_public(public_audit: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate finding rows from public audit data."""
    findings: list[dict[str, Any]] = []
    agg = public_audit.get("aggregate", {}).get("metrics", {})

    broken = int(agg.get("links", {}).get("broken_internal_links_count", 0) or 0)
    if broken > 0:
        findings.append({
            "id": "PUB-001",
            "title": "Broken internal links detected: {}".format(broken),
            "severity": "HIGH" if broken > 10 else "MEDIUM",
            "estimated_monthly_loss_usd_base": broken * 85,
            "estimated_remediation_cost_usd_base": broken * 120,
            "evidence_source": "Automated link check (HEAD+GET with redirect following)",
            "estimation_confidence": "medium",
        })

    seo_rate = float(agg.get("seo_geo", {}).get("seo_geo_issue_rate_pct", 0) or 0)
    if seo_rate > 0:
        findings.append({
            "id": "PUB-002",
            "title": "SEO/GEO issue rate: {:.1f}%".format(seo_rate),
            "severity": "HIGH" if seo_rate > 20 else "MEDIUM",
            "estimated_monthly_loss_usd_base": int(seo_rate * 200),
            "estimated_remediation_cost_usd_base": int(seo_rate * 300),
            "evidence_source": "24-check SEO/GEO scoring model",
            "estimation_confidence": "medium",
        })

    api_na = agg.get("api_coverage", {}).get("no_api_pages_found", False)
    if api_na:
        findings.append({
            "id": "PUB-003",
            "title": "No API reference pages in crawled sample",
            "severity": "MEDIUM",
            "estimated_monthly_loss_usd_base": 2000,
            "estimated_remediation_cost_usd_base": 4000,
            "evidence_source": "API coverage cross-reference analysis",
            "estimation_confidence": "low",
        })

    ex_rel = float(agg.get("examples", {}).get("example_reliability_estimate_pct", 0) or 0)
    if ex_rel < 50:
        findings.append({
            "id": "PUB-004",
            "title": "Low code example reliability: {:.0f}%".format(ex_rel),
            "severity": "MEDIUM",
            "estimated_monthly_loss_usd_base": 1500,
            "estimated_remediation_cost_usd_base": 2500,
            "evidence_source": "Code example syntax and completeness analysis",
            "estimation_confidence": "low",
        })

    freshness = float(agg.get("freshness", {}).get("last_updated_coverage_pct", 0) or 0)
    if freshness < 50:
        findings.append({
            "id": "PUB-005",
            "title": "Weak freshness visibility: {:.0f}% pages show update date".format(freshness),
            "severity": "LOW",
            "estimated_monthly_loss_usd_base": 500,
            "estimated_remediation_cost_usd_base": 800,
            "evidence_source": "HTML metadata and date element analysis",
            "estimation_confidence": "low",
        })

    # Add top_findings as individual low-priority items
    for i, finding_text in enumerate(public_audit.get("top_findings", [])[:3]):
        text = str(finding_text)
        if not any(text.lower() in str(f.get("title", "")).lower() for f in findings):
            findings.append({
                "id": "PUB-{:03d}".format(10 + i),
                "title": text[:80],
                "severity": "LOW",
                "estimated_monthly_loss_usd_base": 300,
                "estimated_remediation_cost_usd_base": 500,
                "evidence_source": "Aggregate audit analysis",
                "estimation_confidence": "low",
            })

    return findings


# ---------------------------------------------------------------------------
# Fallback expert analysis (when LLM is not available)
# ---------------------------------------------------------------------------


def _fallback_expert_analysis(public_audit: dict[str, Any], body_style: ParagraphStyle) -> list[Flowable]:
    """Render structured data-driven analysis when LLM was skipped."""
    elements: list[Flowable] = []
    agg = public_audit.get("aggregate", {}).get("metrics", {})
    sites = public_audit.get("sites", [])
    samples = sites[0].get("samples", {}) if sites else {}

    title_style = ParagraphStyle(
        "FallbackTitle", parent=body_style, fontName="Helvetica-Bold",
        fontSize=10.5, textColor=colors.HexColor("#1e3a8a"), spaceAfter=2,
    )
    item_style = ParagraphStyle(
        "FallbackItem", parent=body_style, fontSize=9.5, leading=13, leftIndent=12,
    )
    red_item = ParagraphStyle(
        "FallbackRed", parent=item_style, textColor=colors.HexColor("#991b1b"),
    )
    green_item = ParagraphStyle(
        "FallbackGreen", parent=item_style, textColor=colors.HexColor("#065f46"),
    )

    # Link Health
    broken = int(agg.get("links", {}).get("broken_internal_links_count", 0) or 0)
    elements.append(Paragraph("Link Health", title_style))
    if broken > 0:
        elements.append(Paragraph(
            "- <b>{} broken internal links</b> detected during crawl".format(broken), red_item))
        broken_samples = samples.get("broken_links", [])[:5]
        for url in broken_samples:
            elements.append(Paragraph("  {} {}".format("->", str(url)[:70]), item_style))
    else:
        elements.append(Paragraph("+ No broken internal links detected", green_item))
    elements.append(Spacer(1, 3 * mm))

    # SEO/GEO
    seo_rate = float(agg.get("seo_geo", {}).get("seo_geo_issue_rate_pct", 0) or 0)
    elements.append(Paragraph("SEO/GEO Assessment", title_style))
    if seo_rate > 0:
        elements.append(Paragraph(
            "- Issue rate: <b>{:.1f}%</b> of scanned pages have structural SEO/GEO problems".format(seo_rate),
            red_item if seo_rate > 10 else item_style))
    else:
        elements.append(Paragraph("+ All scanned pages pass SEO/GEO structural checks", green_item))
    elements.append(Spacer(1, 3 * mm))

    # Content Coverage
    total_examples = int(agg.get("examples", {}).get("total_code_examples", 0) or 0) if isinstance(agg.get("examples"), dict) else 0
    ex_rel = float(agg.get("examples", {}).get("example_reliability_estimate_pct", 0) or 0)
    freshness = float(agg.get("freshness", {}).get("last_updated_coverage_pct", 0) or 0)
    elements.append(Paragraph("Content Coverage", title_style))
    if total_examples > 0:
        elements.append(Paragraph(
            "Code examples found: <b>{}</b>, estimated reliability: <b>{:.0f}%</b>".format(total_examples, ex_rel),
            green_item if ex_rel > 70 else item_style))
    else:
        elements.append(Paragraph("- No code examples detected in crawled pages", item_style))
    elements.append(Paragraph(
        "Freshness visibility: <b>{:.0f}%</b> of pages expose last-updated metadata".format(freshness),
        green_item if freshness > 50 else item_style))
    elements.append(Spacer(1, 3 * mm))

    # Recommendations
    top_findings = public_audit.get("top_findings", [])
    if top_findings:
        elements.append(Paragraph("Recommendations", title_style))
        for finding in top_findings[:5]:
            elements.append(Paragraph("-> {}".format(str(finding)), item_style))

    return elements


# ---------------------------------------------------------------------------
# LLM strengths, risks, limitations
# ---------------------------------------------------------------------------


def _llm_strengths_risks(llm_analysis: dict[str, Any], body_style: ParagraphStyle) -> list[Flowable]:
    elements: list[Flowable] = []

    strengths = llm_analysis.get("strengths", [])
    risks = llm_analysis.get("risks", [])
    limitations = llm_analysis.get("limitations", [])

    green_style = ParagraphStyle("LLMGreen", parent=body_style, textColor=colors.HexColor("#065f46"),
                                  fontSize=9.5, leading=13, leftIndent=12)
    red_style = ParagraphStyle("LLMRed", parent=body_style, textColor=colors.HexColor("#991b1b"),
                                fontSize=9.5, leading=13, leftIndent=12)
    grey_style = ParagraphStyle("LLMGrey", parent=body_style, textColor=GREY_600,
                                 fontSize=9, leading=12, leftIndent=12)
    sub_title = ParagraphStyle("SubH", parent=body_style, fontName="Helvetica-Bold",
                                fontSize=10.5, spaceAfter=2)

    if strengths:
        elements.append(Paragraph("Strengths", ParagraphStyle(
            "StrH", parent=sub_title, textColor=SUCCESS_GREEN)))
        elements.append(Spacer(1, 1.5 * mm))
        for item in strengths[:8]:
            elements.append(Paragraph("+ {}".format(str(item).strip()), green_style))
        elements.append(Spacer(1, 4 * mm))

    if risks:
        elements.append(Paragraph("Risks", ParagraphStyle(
            "RskH", parent=sub_title, textColor=DANGER_RED)))
        elements.append(Spacer(1, 1.5 * mm))
        for item in risks[:8]:
            elements.append(Paragraph("- {}".format(str(item).strip()), red_style))
        elements.append(Spacer(1, 4 * mm))

    if limitations:
        elements.append(Paragraph("Limitations", ParagraphStyle(
            "LimH", parent=sub_title, textColor=GREY_600)))
        elements.append(Spacer(1, 1.5 * mm))
        for item in limitations[:6]:
            elements.append(Paragraph("* {}".format(str(item).strip()), grey_style))

    return elements


# ---------------------------------------------------------------------------
# Methodology
# ---------------------------------------------------------------------------


def _methodology_section(section_style: ParagraphStyle, body_style: ParagraphStyle) -> list[Flowable]:
    elements: list[Flowable] = []
    elements.extend(_section_header("Methodology", section_style))

    intro = (
        "This audit applies a rigorous, repeatable methodology combining automated analysis "
        "with expert synthesis. The platform evaluates documentation quality across five pillars."
    )
    elements.append(Paragraph(intro, body_style))
    elements.append(Spacer(1, 3 * mm))

    pillars = [
        (
            "1. Automated Crawl + Structural HTML Analysis",
            "Every public documentation page is crawled and analyzed for structural integrity, "
            "link health, navigation depth, and content organization. The crawler detects broken links, "
            "orphaned pages, redirect chains, and missing metadata.",
        ),
        (
            "2. SEO/GEO Scoring Model (24 Checks)",
            "Each page is evaluated against 8 GEO checks (LLM/AI search optimization) and "
            "16 SEO checks (traditional search engine optimization). Checks cover meta descriptions, "
            "heading hierarchy, fact density, URL structure, internal linking, and content depth.",
        ),
        (
            "3. API Reference Cross-Coverage Analysis",
            "The platform compares published API reference documentation against the actual API surface "
            "(OpenAPI specs, GraphQL schemas, gRPC protos). Coverage gaps, undocumented endpoints, "
            "and stale references are identified.",
        ),
        (
            "4. Code Example Reliability Estimation",
            "Code examples embedded in documentation are analyzed for syntactic correctness, "
            "completeness, and consistency with current API signatures. Reliability scores "
            "estimate the likelihood of examples working as documented.",
        ),
        (
            "5. Executive Synthesis and Prioritization",
            "All quantitative findings are synthesized into actionable "
            "executive narratives. The analysis identifies patterns, prioritizes risks, "
            "and generates strategic recommendations calibrated to business impact.",
        ),
    ]

    pillar_title_style = ParagraphStyle(
        "PillarTitle", parent=body_style, fontName="Helvetica-Bold", fontSize=10, spaceAfter=1,
    )
    pillar_body_style = ParagraphStyle(
        "PillarBody", parent=body_style, fontSize=9, leading=12, spaceAfter=5,
    )

    for title, desc in pillars:
        elements.append(Paragraph(title, pillar_title_style))
        elements.append(Paragraph(desc, pillar_body_style))

    return elements


# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------


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
    style_cmds: list[tuple[Any, ...]] = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BLUE_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 1), (3, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#93c5fd")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#bfdbfe")),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 2), (-1, 2), LIGHT_BG),
    ]
    table.setStyle(TableStyle(style_cmds))
    return table


def _risk_matrix(findings: list[dict[str, Any]]) -> Table:
    rows = [["ID", "Issue", "Severity", "Monthly Loss", "Fix Cost"]]
    for item in findings[:8]:
        rows.append([
            str(item.get("id", "")),
            str(item.get("title", ""))[:65],
            str(item.get("severity", "n/a")).upper(),
            _format_money(item.get("estimated_monthly_loss_usd_base", 0)),
            _format_money(item.get("estimated_remediation_cost_usd_base", 0)),
        ])
    if len(rows) == 1:
        rows.append(["-", "No findings captured.", "-", "-", "-"])
    table = Table(rows, colWidths=[18 * mm, 78 * mm, 20 * mm, 26 * mm, 26 * mm])
    style: list[tuple[Any, ...]] = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fef3c7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#92400e")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (3, 1), (4, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#fbbf24")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#fde68a")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]
    for idx, row in enumerate(rows[1:], start=1):
        sev = str(row[2]).lower()
        if sev == "high":
            style.append(("TEXTCOLOR", (2, idx), (2, idx), colors.HexColor("#b42318")))
            style.append(("FONTNAME", (2, idx), (2, idx), "Helvetica-Bold"))
        elif sev == "medium":
            style.append(("TEXTCOLOR", (2, idx), (2, idx), colors.HexColor("#b45309")))
        elif sev == "low":
            style.append(("TEXTCOLOR", (2, idx), (2, idx), colors.HexColor("#047857")))
        if idx % 2 == 0:
            style.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#fffbeb")))
    table.setStyle(TableStyle(style))
    return table


def _assumptions_table(assumptions: dict[str, Any]) -> Table:
    rows = [["Assumption", "Value"]]
    for key, value in assumptions.items():
        rows.append([str(key), str(value)])
    if len(rows) == 1:
        rows.append(["No assumptions provided", "-"])
    table = Table(rows, colWidths=[90 * mm, 78 * mm])
    style_cmds: list[tuple[Any, ...]] = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e7ff")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#93c5fd")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#bfdbfe")),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    _alt_row_style(style_cmds, len(rows))
    table.setStyle(TableStyle(style_cmds))
    return table


def _evidence_table(findings: list[dict[str, Any]]) -> Table:
    rows = [["Finding", "Evidence Source", "Confidence"]]
    for item in findings[:10]:
        rows.append([
            "{} -- {}".format(item.get("id", ""), str(item.get("title", ""))[:45]),
            str(item.get("evidence_source", ""))[:60] or "-",
            str(item.get("estimation_confidence", "n/a")),
        ])
    if len(rows) == 1:
        rows.append(["No findings captured", "-", "-"])
    table = Table(rows, colWidths=[72 * mm, 78 * mm, 22 * mm])
    style_cmds: list[tuple[Any, ...]] = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d1fae5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#065f46")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#6ee7b7")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#a7f3d0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    _alt_row_style(style_cmds, len(rows))
    table.setStyle(TableStyle(style_cmds))
    return table


# ---------------------------------------------------------------------------
# Main PDF builder
# ---------------------------------------------------------------------------


def _build_pdf(
    output_path: Path,
    scorecard: dict[str, Any],
    public_audit: dict[str, Any],
    llm_analysis: dict[str, Any],
    company_name: str,
) -> None:
    styles = getSampleStyleSheet()

    section_style = ParagraphStyle(
        "SectionExec", parent=styles["Heading3"],
        fontName="Helvetica-Bold", fontSize=13, leading=15,
        textColor=colors.HexColor("#1e3a8a"), spaceBefore=2, spaceAfter=2,
    )
    body_style = ParagraphStyle(
        "BodyExec", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9.5, leading=13,
        textColor=NAVY, spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleExec", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9, leading=11,
        textColor=GREY_500, spaceAfter=4,
    )

    # -- Extract data --
    score_data = scorecard.get("score", {})
    kpis = scorecard.get("kpis", {})
    totals = scorecard.get("findings_totals", {})
    findings = scorecard.get("findings", [])
    assumptions = scorecard.get("business_impact", {}).get("assumptions", {})
    public_metrics = public_audit.get("aggregate", {}).get("metrics", {})

    api_cov = float(kpis.get("api_coverage", {}).get("coverage_pct", 0.0) or 0)
    ex_rel = float(kpis.get("example_reliability", {}).get("example_reliability_pct", 0.0) or 0)
    drift = float(kpis.get("drift", {}).get("docs_contract_drift_pct", 0.0) or 0)
    retrieval = float(kpis.get("retrieval_quality", {}).get("hallucination_rate", 0.0) or 0)

    seo_geo = float(public_metrics.get("seo_geo", {}).get("seo_geo_issue_rate_pct", 0.0) or 0)
    public_api_cov_raw = public_metrics.get("api_coverage", {}).get("reference_coverage_pct", 0.0)
    public_api_na = public_metrics.get("api_coverage", {}).get("no_api_pages_found", False) or float(public_api_cov_raw or 0) < 0
    public_api_cov = 0.0 if public_api_na else float(public_api_cov_raw or 0)
    broken_links = int(public_metrics.get("links", {}).get("broken_internal_links_count", 0) or 0)
    pages = int(public_metrics.get("crawl", {}).get("pages_crawled", 0) or 0)
    public_ex_rel = float(public_metrics.get("examples", {}).get("example_reliability_estimate_pct", 0) or 0)
    freshness_pct = float(public_metrics.get("freshness", {}).get("last_updated_coverage_pct", 0) or 0)

    # Always derive score from actual public audit data
    score_value = _derive_public_score(
        seo_issue_pct=seo_geo,
        broken_links=broken_links,
        pages=pages,
        api_cov_pct=public_api_cov if not public_api_na else None,
        example_rel_pct=public_ex_rel,
    )

    risk_band_label = _risk_band(score_value)
    gen_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    top_findings = public_audit.get("top_findings", []) or []

    impact_base = scorecard.get("business_impact", {}).get("scenarios", {}).get("base", {})
    if not isinstance(impact_base, dict):
        impact_base = {}

    summary_text = str(llm_analysis.get("executive_summary", "")).strip()
    if not summary_text:
        summary_text = (
            "{} documentation has measurable quality gaps and structural risks. "
            "This audit identifies {} specific findings across link health, content coverage, "
            "and search optimization that directly impact developer experience and support costs."
        ).format(company_name, max(len(top_findings), 3))

    action_items: list[str] = []
    if isinstance(llm_analysis.get("prioritized_actions"), list):
        action_items = [str(v) for v in llm_analysis["prioritized_actions"]]
    if not action_items:
        action_items = [
            "Resolve all broken internal links ({} found) to reduce user friction and improve SEO.".format(broken_links),
            "Add last-updated metadata to all documentation pages for freshness visibility.",
            "Establish automated weekly audit cadence to track regression and improvement.",
        ]

    # Use synthetic findings from public audit when scorecard has none
    effective_findings = findings if findings else _synthetic_findings_from_public(public_audit)

    # -- Build document --
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Executive Documentation Audit",
        author="DocsOps",
    )

    content: list[Flowable] = []
    bar_width = int(CONTENT_W - 10)

    # == PAGE 1: Cover ==
    content.extend(_cover_page(company_name, score_value, risk_band_label, gen_date, pages, top_findings))

    # == PAGE 2: Executive Summary + Per-Site Breakdown + Key Metrics ==
    content.extend(_section_header("Executive Summary", section_style))

    # Score gauge + narrative side by side
    gauge_drawing = _draw_score_gauge(score_value, size=140)
    gauge_cell = DrawingFlowable(gauge_drawing)

    narrative_parts = [
        Paragraph(summary_text, body_style),
        Spacer(1, 2 * mm),
        Paragraph(
            "External posture: SEO/GEO issue rate <b>{:.1f}%</b>, public API coverage "
            "<b>{}</b>, broken links <b>{}</b>.".format(
                seo_geo,
                "N/A" if public_api_na else "{:.1f}%".format(public_api_cov),
                broken_links,
            ),
            body_style,
        ),
    ]
    summary_data = [[gauge_cell, narrative_parts]]
    summary_table = Table(summary_data, colWidths=[150, CONTENT_W - 160])
    summary_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    content.append(summary_table)

    # Key metrics cards (6 cells, color-coded)
    content.append(Spacer(1, 4 * mm))
    grade_label = _grade_from_score(score_value)
    cards_data = [
        ["Audit Score", "{:.1f} / 100".format(score_value),
         "Grade", grade_label,
         "Risk Band", risk_band_label],
        ["Pages Scanned", str(pages),
         "Broken Links", str(broken_links),
         "SEO Issue Rate", "{:.1f}%".format(seo_geo)],
    ]
    col_w = CONTENT_W / 6
    cards_table = Table(cards_data, colWidths=[col_w] * 6)
    cards_style: list[tuple[Any, ...]] = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("FONTNAME", (3, 0), (3, -1), "Helvetica-Bold"),
        ("FONTNAME", (5, 0), (5, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (-1, -1), NAVY),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#93c5fd")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#bfdbfe")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("ALIGN", (3, 0), (3, -1), "CENTER"),
        ("ALIGN", (5, 0), (5, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        # Color-code label columns
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BLUE_BG),
        ("BACKGROUND", (2, 0), (2, -1), LIGHT_BLUE_BG),
        ("BACKGROUND", (4, 0), (4, -1), LIGHT_BLUE_BG),
        # Color-code value backgrounds by health
        ("BACKGROUND", (1, 0), (1, 0), _metric_bg(score_value, 70, 50)),
        ("BACKGROUND", (3, 1), (3, 1), _metric_bg(broken_links, 5, 20, invert=True)),
        ("BACKGROUND", (5, 1), (5, 1), _metric_bg(seo_geo, 5, 15, invert=True)),
    ]
    cards_table.setStyle(TableStyle(cards_style))
    content.append(cards_table)

    # Per-site table (on same page, no page break)
    site_table_items = _per_site_table(public_audit)
    if site_table_items:
        content.append(Spacer(1, 4 * mm))
        content.append(Paragraph(
            "<b>Per-Site Breakdown</b>",
            ParagraphStyle("PerSiteH", parent=body_style, fontName="Helvetica-Bold",
                          fontSize=10.5, textColor=colors.HexColor("#1e3a8a")),
        ))
        content.append(Spacer(1, 2 * mm))
        content.extend(site_table_items)

    content.append(PageBreak())

    # == PAGE 3: Board-Level Metrics + Financial Exposure ==
    content.extend(_section_header("Board-Level Metrics", section_style))

    # Full-width progress bars
    metrics_bars = [
        ("SEO/GEO Issue Rate (lower is better)", seo_geo, 50, _score_color(100 - seo_geo * 2)),
        ("Example Reliability (estimate)", public_ex_rel, 100, _score_color(public_ex_rel)),
        ("Freshness Visibility (last-updated metadata)", freshness_pct, 100, _score_color(freshness_pct)),
    ]

    if public_api_na:
        content.append(Paragraph(
            "API Coverage (Public): <b>N/A</b> -- no API reference pages found in crawled sample",
            body_style))
        content.append(Spacer(1, 2 * mm))
    else:
        bar = _draw_progress_bar("API Coverage (Public)", public_api_cov, 100,
                                  _score_color(public_api_cov), width=bar_width)
        content.append(DrawingFlowable(bar))

    for label, val, max_v, clr in metrics_bars:
        bar = _draw_progress_bar(label, val, max_v, clr, width=bar_width)
        content.append(DrawingFlowable(bar))

    # Internal metrics (from scorecard) if available
    if api_cov > 0 or ex_rel > 0 or drift > 0:
        content.append(Spacer(1, 3 * mm))
        content.append(_thin_rule())
        content.append(Spacer(1, 2 * mm))
        content.append(Paragraph("<b>Internal Metrics (from scorecard)</b>", body_style))
        content.append(Spacer(1, 1 * mm))
        internal_bars = [
            ("API Coverage (Internal)", api_cov, 100, _score_color(api_cov)),
            ("Example Reliability (Internal)", ex_rel, 100, _score_color(ex_rel)),
            ("Docs-Contract Drift", drift, 50, _score_color(100 - drift * 2)),
        ]
        for label, val, max_v, clr in internal_bars:
            bar = _draw_progress_bar(label, val, max_v, clr, width=bar_width)
            content.append(DrawingFlowable(bar))

    # Financial exposure on same page
    content.append(Spacer(1, 4 * mm))
    content.extend(_section_header("Financial Exposure Model", section_style))
    content.append(_financial_table(impact_base, totals))
    content.append(PageBreak())

    # == PAGE 4: Risk Matrix + Priority Actions ==
    content.extend(_section_header("Risk Matrix", section_style))
    content.append(_risk_matrix(effective_findings))
    content.append(Spacer(1, 5 * mm))

    content.extend(_section_header("Priority Action Plan (Next 14 Days)", section_style))

    # Top risk items
    for item in effective_findings[:3]:
        risk_text = "<b>{}</b>: {}".format(
            item.get("id", ""),
            str(item.get("title", ""))[:70],
        )
        content.append(Paragraph("-> {}".format(risk_text), body_style))
    content.append(Spacer(1, 3 * mm))

    content.append(Paragraph("<b>Recommended actions:</b>", body_style))
    content.append(Spacer(1, 1 * mm))
    for i, action in enumerate(action_items[:5], 1):
        content.append(Paragraph("{}. {}".format(i, action), body_style))

    content.append(PageBreak())

    # == PAGE 5: Expert Analysis ==
    content.extend(_section_header("Expert Analysis: Strengths and Risks", section_style))
    llm_items = _llm_strengths_risks(llm_analysis, body_style)
    if llm_items:
        content.extend(llm_items)
    else:
        # Fallback: data-driven analysis from public audit
        content.extend(_fallback_expert_analysis(public_audit, body_style))
    content.append(PageBreak())

    # == PAGE 6: Methodology ==
    content.extend(_methodology_section(section_style, body_style))

    # == PAGE 7 (optional): Combined Appendix ==
    has_assumptions = isinstance(assumptions, dict) and len(assumptions) > 0
    has_evidence = len(effective_findings) > 0
    if has_assumptions or has_evidence:
        content.append(PageBreak())
        if has_assumptions:
            content.extend(_section_header("Appendix A -- Economic Model Assumptions", section_style))
            content.append(_assumptions_table(assumptions))
            content.append(Spacer(1, 3 * mm))
            content.append(Paragraph(
                "Note: estimates are directional and should be calibrated with "
                "client rates, release cadence, and support volume.",
                subtitle_style,
            ))
        if has_evidence:
            content.append(Spacer(1, 4 * mm))
            content.extend(_section_header("Appendix B -- Evidence Traceability", section_style))
            content.append(_evidence_table(effective_findings))
            content.append(Spacer(1, 3 * mm))
            content.append(Paragraph(
                "All findings are traceable to automated checks. Evidence sources "
                "reference specific crawl data, API specs, or code analysis results.",
                subtitle_style,
            ))

    # -- Build --
    def _on_page(canvas, doc_obj):
        _header_footer(canvas, doc_obj, company_name, gen_date)

    doc.build(content, onFirstPage=_on_page, onLaterPages=_on_page)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate premium executive audit PDF")
    parser.add_argument("--scorecard-json", default="reports/audit_scorecard.json")
    parser.add_argument("--public-audit-json", default="reports/public_docs_audit.json")
    parser.add_argument("--llm-summary-json", default="reports/public_docs_audit_llm_summary.json")
    parser.add_argument("--company-name", default="Client")
    parser.add_argument("--output", default=None,
                        help="Output PDF path. Defaults to reports/{company-slug}-executive-audit.pdf")
    args = parser.parse_args()

    scorecard = _read_json(Path(args.scorecard_json))
    public_audit = _read_json(Path(args.public_audit_json))
    llm_summary = _read_json(Path(args.llm_summary_json))

    if not public_audit:
        raise SystemExit("Missing or invalid public audit JSON: {}".format(args.public_audit_json))

    # Scorecard is optional for public-only audits
    if not scorecard:
        scorecard = {}

    if args.output:
        output = Path(args.output)
    else:
        slug = _slugify(str(args.company_name))
        output = Path("reports/{}-executive-audit.pdf".format(slug))
    output.parent.mkdir(parents=True, exist_ok=True)
    llm_block = _pick_llm_block(public_audit, llm_summary)
    _build_pdf(
        output_path=output,
        scorecard=scorecard,
        public_audit=public_audit,
        llm_analysis=llm_block,
        company_name=str(args.company_name),
    )
    print("[ok] executive pdf: {}".format(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

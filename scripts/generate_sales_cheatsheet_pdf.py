#!/usr/bin/env python3
"""Generate VeriOps Sales Cheat Sheet PDF.

A memorization-friendly sales reference for pitching the VeriOps
Automation Platform to VP Engineering, VP Product, and Head of DevRel.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing, Rect, String
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
# Colors
# ---------------------------------------------------------------------------
NAVY = colors.HexColor("#0f172a")
ACCENT = colors.HexColor("#2563eb")
GREEN = colors.HexColor("#059669")
AMBER = colors.HexColor("#d97706")
RED = colors.HexColor("#dc2626")
LIGHT_BG = colors.HexColor("#f8fafc")
LIGHT_BLUE = colors.HexColor("#f0f9ff")
LIGHT_GREEN = colors.HexColor("#f0fdf4")
LIGHT_AMBER = colors.HexColor("#fffbeb")
GREY5 = colors.HexColor("#6b7280")
GREY6 = colors.HexColor("#4b5563")
GREY7 = colors.HexColor("#374151")
WHITE = colors.white

PAGE_W, PAGE_H = A4
MARGIN = 14 * mm


# ---------------------------------------------------------------------------
# Flowable helpers
# ---------------------------------------------------------------------------
class CoverPage(Flowable):
    def __init__(self) -> None:
        super().__init__()
        self.width = PAGE_W - 2 * MARGIN - 12
        self.height = PAGE_H - 2 * MARGIN - 12

    def wrap(self, aw: float, ah: float) -> tuple[float, float]:
        return self.width, self.height

    def draw(self) -> None:
        c = self.canv
        w = self.width
        h = self.height

        # Navy top 55%
        navy_h = h * 0.55
        c.setFillColor(NAVY)
        c.rect(0, h - navy_h, w, navy_h, fill=1, stroke=0)

        # Title block
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(30, h - 40, "VeriOps Automation Platform")

        c.setFont("Helvetica-Bold", 26)
        c.drawString(30, h - 80, "Sales Cheat Sheet")

        c.setFont("Helvetica", 12)
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.drawString(30, h - 110, "Everything you need to pitch, in one document")

        c.setFont("Helvetica", 9)
        c.drawString(30, h - 140, "Target: VP Engineering  |  VP Product  |  Head of DevRel")

        # Accent line
        c.setStrokeColor(ACCENT)
        c.setLineWidth(3)
        c.line(30, h - 160, w - 30, h - 160)

        # Three value props in navy area
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 11)
        props = [
            "Detect  ->  Generate  ->  Verify  ->  Publish  ->  Monitor",
        ]
        c.drawString(30, h - 190, props[0])

        c.setFont("Helvetica", 9.5)
        c.setFillColor(colors.HexColor("#cbd5e1"))
        taglines = [
            "Not an AI text generator. A complete documentation operating system.",
            "Runs locally. Your content never leaves your environment.",
            "Measurable ROI from day one. $5K pilot with real KPIs.",
        ]
        y = h - 215
        for line in taglines:
            c.drawString(30, y, line)
            y -= 16

        # Bottom section
        info_y = h - navy_h - 40
        c.setFillColor(GREY7)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(30, info_y, "The One-Sentence Pitch")
        c.setFont("Helvetica", 9.5)
        c.setFillColor(GREY6)

        pitch = (
            '"We automate documentation the way CI/CD automated deployment --'
        )
        pitch2 = (
            'detect gaps, generate drafts, enforce quality, and monitor drift.'
        )
        pitch3 = (
            'Your engineers ship docs in hours, not days, at Stripe-level quality."'
        )
        c.drawString(30, info_y - 22, pitch)
        c.drawString(30, info_y - 36, pitch2)
        c.drawString(30, info_y - 50, pitch3)

        # Memory anchor box
        box_y = info_y - 100
        c.setFillColor(LIGHT_BLUE)
        c.roundRect(30, box_y, w - 60, 38, 4, fill=1, stroke=0)
        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(40, box_y + 22, "MEMORY ANCHOR: Think of it as")
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, box_y + 6, '"GitHub Actions for documentation" -- automated, gated, measurable')

        # Date
        c.setFillColor(GREY5)
        c.setFont("Helvetica", 7)
        gen = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        c.drawString(30, 10, "CONFIDENTIAL  |  Internal use only  |  {}".format(gen))


def _header_footer(canvas, doc) -> None:
    page = canvas.getPageNumber()
    if page == 1:
        return
    canvas.saveState()
    w, h = A4
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(1)
    canvas.line(MARGIN, h - 10 * mm, w - MARGIN, h - 10 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GREY6)
    canvas.drawString(MARGIN, h - 9 * mm, "VeriOps Sales Cheat Sheet")
    canvas.drawRightString(w - MARGIN, h - 9 * mm, "Page {}".format(page))
    canvas.setStrokeColor(colors.HexColor("#e5e7eb"))
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 8 * mm, w - MARGIN, 8 * mm)
    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(GREY5)
    canvas.drawString(MARGIN, 4.5 * mm, "CONFIDENTIAL")
    canvas.restoreState()


def _section(text: str, style: ParagraphStyle) -> list:
    data = [[Paragraph(text, style)]]
    t = Table(data, colWidths=[PAGE_W - 2 * MARGIN])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBEFORE", (0, 0), (0, -1), 3, ACCENT),
    ]))
    return [Spacer(1, 5 * mm), t, Spacer(1, 2 * mm)]


def _memory_box(title: str, content: str, bg: colors.Color = LIGHT_BLUE) -> Table:
    """Colored box for memory anchors."""
    data = [[Paragraph(
        "<font color='#2563eb'><b>{}</b></font><br/>{}".format(title, content),
        ParagraphStyle("MemBox", fontName="Helvetica", fontSize=8.5, leading=11.5,
                       textColor=NAVY)
    )]]
    t = Table(data, colWidths=[PAGE_W - 2 * MARGIN])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("BOX", (0, 0), (-1, -1), 0.3, colors.HexColor("#dbeafe")),
    ]))
    return t


def _kv_table(rows: list[list[str]], col_widths: list[float] | None = None) -> Table:
    if not col_widths:
        col_widths = [55 * mm, PAGE_W - 2 * MARGIN - 55 * mm]
    t = Table(rows, colWidths=col_widths)
    style = [
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR", (0, 0), (-1, -1), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
    ]
    t.setStyle(TableStyle(style))
    return t


def _build_pdf(output: Path) -> None:
    styles = getSampleStyleSheet()

    sec = ParagraphStyle("Sec", parent=styles["Heading3"], fontName="Helvetica-Bold",
                         fontSize=11, leading=13, textColor=colors.HexColor("#1e3a8a"),
                         spaceBefore=2, spaceAfter=2)
    body = ParagraphStyle("Body", parent=styles["Normal"], fontName="Helvetica",
                          fontSize=8.5, leading=11.2, textColor=NAVY, spaceAfter=2)
    sub = ParagraphStyle("Sub", parent=styles["Normal"], fontName="Helvetica",
                         fontSize=8, leading=10, textColor=GREY5, spaceAfter=3)
    bold_body = ParagraphStyle("BBody", parent=body, fontName="Helvetica-Bold")
    small = ParagraphStyle("Small", parent=body, fontSize=7.8, leading=10)

    content: list = []

    # ── PAGE 1: COVER ─────────────────────────────────────────────────
    content.append(CoverPage())
    content.append(PageBreak())

    # ── PAGE 2: THE PROBLEM + SOLUTION ────────────────────────────────
    content.extend(_section("Page 2: The Problem They Have", sec))

    content.append(Paragraph(
        "<b>Say this:</b> \"How fast does your engineering team ship features?\"",
        body))
    content.append(Paragraph("(They will say: weekly, biweekly, continuous.)", sub))
    content.append(Spacer(1, 2 * mm))
    content.append(Paragraph(
        "<b>Then ask:</b> \"And how fast does documentation keep up?\"",
        body))
    content.append(Paragraph("(They will pause. This is the pain.)", sub))
    content.append(Spacer(1, 3 * mm))

    content.append(_memory_box(
        "THE CORE PROBLEM (memorize this)",
        "Engineering ships faster than docs can follow. Every release without updated docs "
        "creates support tickets, developer frustration, and churn risk. "
        "The gap compounds -- by month 6, docs are a liability, not an asset."
    ))
    content.append(Spacer(1, 4 * mm))

    content.append(Paragraph("<b>Three pain points to probe:</b>", body))
    pain_data = [
        ["Pain point", "Question to ask", "What they will say"],
        ["Stale docs", "\"What % of your docs are current?\"",
         "They do not know (which proves the point)"],
        ["Support load", "\"How many tickets are really docs questions?\"",
         "25-40% is typical for dev tools"],
        ["Slow onboarding", "\"How long until a new dev makes their first API call?\"",
         "Hours to days (should be minutes)"],
    ]
    t = Table(pain_data, colWidths=[30 * mm, 65 * mm, 70 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    content.append(t)

    content.append(Spacer(1, 5 * mm))
    content.extend(_section("Our Solution (one paragraph)", sec))
    content.append(Paragraph(
        "VeriOps is a documentation operating system that runs in your CI/CD pipeline. "
        "It automatically detects what docs are missing or stale, generates drafts from "
        "AI-powered templates, enforces quality with 8 automated gates, and monitors "
        "documentation health weekly -- just like you monitor uptime. "
        "It generates a consulting-grade executive audit PDF and powers "
        "AI-ready knowledge search. Your engineers review and approve; the system does the rest.",
        body,
    ))
    content.append(Spacer(1, 3 * mm))
    content.append(_memory_box(
        "THE PIPELINE IN 5 WORDS",
        "Detect -> Generate -> Verify -> Publish -> Monitor"
    ))
    content.append(PageBreak())

    # ── PAGE 3: WHAT THEY GET ─────────────────────────────────────────
    content.extend(_section("Page 3: What They Get (Features as Benefits)", sec))
    content.append(Paragraph(
        "Never list features. Always state what it DOES for them. Here is your translation table:",
        sub,
    ))

    feat_data = [
        ["What we have", "What you say"],
        ["Weekly consolidated reports\n(4 signal sources merged)",
         "\"You get a single prioritized list of what to fix,\nranked by business impact -- every Monday.\""],
        ["38 Stripe-quality templates\n+ protocol-specific templates",
         "\"Every doc your team writes looks like Stripe's docs.\nConsistency is enforced, not hoped for.\""],
        ["8 automated quality gates\n(contracts, Vale, SEO/GEO, RAG...)",
         "\"Bad docs cannot ship. Quality gates block\nmerge until standards are met.\""],
        ["5 API protocols\n(REST, GraphQL, gRPC, AsyncAPI, WS)",
         "\"Whatever APIs you have, we document them.\nOne pipeline covers your entire surface.\""],
        ["Postman mock servers\n+ interactive Try-it panels",
         "\"Developers test API calls live in the docs.\nNo setup needed -- sandbox is built in.\""],
        ["Self-verification layer\n(code execution + fact-checking)",
         "\"Every code example is tested. Every port number\nis verified. No stale, broken examples.\""],
        ["Knowledge modules + RAG\n(FAISS search, retrieval evals)",
         "\"Your docs power AI search out of the box.\nDevelopers ask questions, get instant answers.\""],
        ["Premium executive audit PDF\n(consulting-grade, 9 pages)",
         "\"We deliver a McKinsey-level report that shows\nyour board exactly what is at risk and what to fix.\""],
        ["Smart merge for test assets\n(preserves manual + custom cases)",
         "\"When your API changes, tests update automatically.\nManual test cases are never overwritten.\""],
        ["Runs 100% locally\n(no SaaS, no data leaks)",
         "\"Your content never leaves your environment.\nNo vendor lock-in. You own everything.\""],
    ]
    ft = Table(feat_data, colWidths=[62 * mm, 104 * mm])
    ft_style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, 1), (0, -1), LIGHT_BG),
    ]
    for i in range(1, len(feat_data)):
        if i % 2 == 0:
            ft_style.append(("BACKGROUND", (1, i), (1, i), colors.HexColor("#fafbfc")))
    ft.setStyle(TableStyle(ft_style))
    content.append(ft)
    content.append(PageBreak())

    # ── PAGE 4: RESULTS + PROOF ───────────────────────────────────────
    content.extend(_section("Page 4: The Numbers (Memorize These)", sec))
    content.append(Paragraph(
        "These are real outcomes from the platform. Use them in every conversation.",
        sub,
    ))

    num_data = [
        ["Metric", "Before", "After", "Impact"],
        ["Time to publish", "2-3 days", "2-6 hours", "-90%"],
        ["Style consistency", "~60%", "98%", "Brand-safe"],
        ["Support tickets\n(docs-related)", "25-40% of total", "-25% to -50%", "Fewer tickets"],
        ["Pages per person\nper quarter", "~50", "120-220+", "+140-340%"],
        ["Quality score", "Unknown", "82-85/100", "SLA-tracked"],
        ["Stale content", "Unknown", "<12%", "Monitored weekly"],
    ]
    nt = Table(num_data, colWidths=[40 * mm, 30 * mm, 30 * mm, 66 * mm])
    nt_style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ALIGN", (1, 1), (2, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("BACKGROUND", (3, 1), (3, -1), LIGHT_GREEN),
        ("TEXTCOLOR", (3, 1), (3, -1), GREEN),
        ("FONTNAME", (3, 1), (3, -1), "Helvetica-Bold"),
    ]
    nt.setStyle(TableStyle(nt_style))
    content.append(nt)

    content.append(Spacer(1, 5 * mm))
    content.append(_memory_box(
        "YOUR GO-TO STAT",
        "\"90% reduction in time to publish, with 98% style consistency -- measurable from week one.\""
    ))
    content.append(Spacer(1, 4 * mm))

    content.extend(_section("Competitive Positioning", sec))
    comp_data = [
        ["They say...", "You say..."],
        ["\"We will hire a tech writer\"",
         "\"Great -- VeriOps makes one writer 3-4x more productive. "
         "The $20K implementation costs less than 2 months of a writer's salary, "
         "and the system scales with your team.\""],
        ["\"We will build it in-house\"",
         "\"We see that take 6-12 months. Our pilot proves value in 2 weeks for $5K. "
         "If it works, you skip the build entirely.\""],
        ["\"We use an AI writing tool\"",
         "\"AI generates text. We enforce quality. Eight gates block every merge. "
         "Code examples are executed and verified. No hallucinated docs ship.\""],
        ["\"Our docs are fine\"",
         "\"We offer a free audit with a consulting-grade PDF report. "
         "Quality score, broken links, dollar exposure. "
         "If everything is green, you owe us nothing.\""],
    ]
    ct = Table(comp_data, colWidths=[52 * mm, 114 * mm])
    ct.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fef2f2")),
        ("TEXTCOLOR", (0, 0), (-1, 0), RED),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#fff5f5")),
    ]))
    content.append(ct)
    content.append(PageBreak())

    # ── PAGE 5: PRICING + DEAL STRUCTURE ──────────────────────────────
    content.extend(_section("Page 5: Pricing and Deal Structure", sec))

    price_data = [
        ["Tier", "Price", "Duration", "What they get"],
        ["Pilot",
         "$5,000",
         "10-14 days",
         "5-10 published pages, before/after KPIs, quality score,\n"
         "premium 9-page executive audit PDF, go/no-go recommendation"],
        ["Full implementation",
         "$20-40K",
         "3-6 weeks",
         "Complete rollout: 8 CI gates, 38 templates, scheduler,\n"
         "all 5 protocols, RAG pipeline, mock servers, training"],
        ["Monthly retainer\n(optional)",
         "$3-8K/mo",
         "Ongoing",
         "Continuous support, pipeline updates, priority access,\n"
         "quarterly business reviews"],
        ["Founding customer\n(limited)",
         "$9-15K",
         "3-6 weeks",
         "Full implementation at discount.\n"
         "Requires: case study + testimonial rights"],
    ]
    pt = Table(price_data, colWidths=[32 * mm, 22 * mm, 22 * mm, 90 * mm])
    pt_style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TEXTCOLOR", (1, 1), (1, -1), ACCENT),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
    ]
    pt.setStyle(TableStyle(pt_style))
    content.append(pt)

    content.append(Spacer(1, 4 * mm))
    content.append(_memory_box(
        "THE CLOSE",
        "\"Let us start with a $5K pilot. Two weeks, real pages, real metrics. "
        "If the numbers work, 80% of the pilot fee credits toward full implementation. "
        "If they do not -- you spent $5K to learn something valuable about your docs.\""
    ))

    content.append(Spacer(1, 4 * mm))
    content.append(Paragraph("<b>ROI math to use in conversation:</b>", body))
    roi_data = [
        ["Their cost", "Our cost", "Math"],
        ["Tech writer: $150K/year\n(salary + benefits)",
         "Full implementation: $20-40K\n(one-time)",
         "Break-even in 2 months.\nWriter + VeriOps = 3-4x output."],
        ["In-house build: 2 engineers\nx 6 months = $300K+",
         "Full implementation: $20-40K\n+ $3-8K/mo retainer",
         "10x cheaper. Production-ready\nin 3-6 weeks, not 6-12 months."],
        ["Support tickets: $25-50\nper ticket x 500/month\n= $12-25K/month",
         "25-50% ticket reduction\n= $3-12K/month saved",
         "Platform pays for itself\nfrom support savings alone."],
    ]
    rt = Table(roi_data, colWidths=[52 * mm, 52 * mm, 62 * mm])
    rt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0fdf4")),
        ("TEXTCOLOR", (0, 0), (-1, 0), GREEN),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    content.append(rt)
    content.append(PageBreak())

    # ── PAGE 6: PERSONA PLAYBOOKS ─────────────────────────────────────
    content.extend(_section("Page 6: Persona Playbooks", sec))
    content.append(Paragraph(
        "Different buyers care about different things. Adjust your pitch:",
        sub,
    ))

    persona_data = [
        ["Persona", "They care about", "Lead with", "Proof point"],
        ["VP Engineering",
         "Developer velocity,\nengineering efficiency,\ntechnical debt",
         "\"Your engineers spend 20% of time\non docs. We cut that to 5%.\"",
         "Pages per person: 50 -> 220+\nTime to publish: -90%"],
        ["VP Product",
         "User activation,\ntime-to-value,\nchurn reduction",
         "\"Users who read good docs\nactivate 2x faster and churn\n40% less.\"",
         "Support tickets: -25% to -50%\nOnboarding time: hours -> min"],
        ["Head of DevRel",
         "Content quality,\ncommunity trust,\nAPI adoption",
         "\"Every doc looks like Stripe.\nCode examples are tested.\nAI search built in via knowledge modules.\"",
         "Quality score: 82-85/100\nStyle consistency: 98%\n5 protocols + RAG pipeline"],
    ]
    per_t = Table(persona_data, colWidths=[30 * mm, 38 * mm, 50 * mm, 48 * mm])
    per_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    content.append(per_t)

    content.append(Spacer(1, 6 * mm))
    content.extend(_section("The Sales Conversation Flow", sec))
    content.append(Paragraph(
        "Follow this arc in every meeting. Each step builds on the previous one:",
        sub,
    ))

    flow_data = [
        ["Step", "What to do", "Time"],
        ["1. Pain",
         "Ask about docs velocity vs. engineering velocity. Let them feel the gap.",
         "3 min"],
        ["2. Cost",
         "\"What does a support ticket cost? How many are docs questions?\" "
         "Let them do the math.",
         "2 min"],
        ["3. Demo",
         "Run the audit wizard on THEIR docs site. Show the 9-page executive PDF: "
         "score gauges, risk matrix, dollar exposure. This is the wow moment.",
         "5 min"],
        ["4. Solution",
         "Walk through the 5-step pipeline: detect, generate, verify, publish, monitor. "
         "Show knowledge modules + AI search. Show mock server Try-it panel.",
         "5 min"],
        ["5. Proof",
         "Share the numbers table (page 4). \"90% faster, 98% consistent, measurable week one.\"",
         "2 min"],
        ["6. Close",
         "\"$5K pilot, 2 weeks, real pages, real metrics. 80% credits toward full implementation. "
         "When can we start?\"",
         "3 min"],
    ]
    ft2 = Table(flow_data, colWidths=[14 * mm, 130 * mm, 18 * mm])
    ft2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TEXTCOLOR", (0, 1), (0, -1), ACCENT),
        ("ALIGN", (2, 1), (2, -1), "CENTER"),
    ]))
    content.append(ft2)
    content.append(PageBreak())

    # ── PAGE 7: QUICK REFERENCE CARD ──────────────────────────────────
    content.extend(_section("Page 7: Quick Reference Card (Tear-Out)", sec))
    content.append(Paragraph(
        "Print this page. Keep it next to you during calls.",
        sub,
    ))

    content.append(Spacer(1, 2 * mm))
    content.append(_memory_box(
        "ONE-LINER",
        "\"We automate documentation the way CI/CD automated deployment.\""
    ))
    content.append(Spacer(1, 3 * mm))

    content.append(Paragraph("<b>6 things to ALWAYS say:</b>", body))
    always_items = [
        "1. \"90% reduction in time to publish\" -- the headline stat",
        "2. \"Runs locally -- your content never leaves your environment\"",
        "3. \"$5K pilot, 2 weeks, measurable results or you walk away\"",
        "4. \"We deliver a consulting-grade audit PDF your board can read\"",
        "5. \"Quality gates block bad docs from shipping, like CI blocks bad code\"",
        "6. \"Your docs power AI search -- developers get instant answers\"",
    ]
    for item in always_items:
        content.append(Paragraph(item, body))
    content.append(Spacer(1, 3 * mm))

    content.append(Paragraph("<b>5 things to NEVER say:</b>", body))
    never_items = [
        "1. Technical jargon (FAISS, Spectral, reportlab, IDNA, frontmatter)",
        "2. \"AI writes your docs\" -- we are an operating system, not a generator",
        "3. Feature lists without benefits -- always translate to outcomes",
        "4. \"It is easy\" -- say \"it is fast\" or \"it is measurable\" instead",
        "5. Pricing before establishing value -- always demo the audit first",
    ]
    for item in never_items:
        content.append(Paragraph(item, body))
    content.append(Spacer(1, 3 * mm))

    content.append(Paragraph("<b>Qualifying questions (ask all 3):</b>", body))
    qual = [
        "1. \"How many developers use your docs daily?\" (>50 = good fit)",
        "2. \"How many doc pages do you maintain?\" (>100 = good fit)",
        "3. \"Do you have API docs?\" (Yes = immediate value)",
    ]
    for item in qual:
        content.append(Paragraph(item, body))

    content.append(Spacer(1, 4 * mm))
    content.append(_memory_box(
        "THE DEMO KILLER MOVE",
        "Run the audit wizard on their actual docs site during the call. "
        "Generate the 9-page executive PDF live: score gauges, per-site breakdown, "
        "risk matrix, and dollar exposure. Hand them the PDF before the call ends. "
        "This creates an \"oh wow\" moment every single time.",
        LIGHT_GREEN,
    ))

    content.append(Spacer(1, 4 * mm))
    ref_data = [
        ["Topic", "Quick answer"],
        ["What is it?", "Documentation operating system for CI/CD pipelines"],
        ["Who is it for?", "Series B+ tech companies with 50+ developers using docs"],
        ["How long to start?", "2-week pilot, 3-6 weeks full rollout"],
        ["What does it cost?", "$5K pilot -> $20-40K implementation -> $3-8K/mo retainer"],
        ["What is the ROI?", "2-month payback. 10x cheaper than building in-house"],
        ["What protocols?", "REST, GraphQL, gRPC, AsyncAPI, WebSocket -- all in one pipeline"],
        ["Is it SaaS?", "No. Runs locally in your repo. You own everything"],
        ["What about AI?", "AI generates drafts. 8 gates + code verification enforce quality"],
        ["What is the audit?", "Free 9-page executive PDF: score gauges, risk matrix, dollar exposure"],
        ["AI search ready?", "Yes. Knowledge modules + FAISS search -- developers ask, get answers"],
        ["Can we try it?", "Yes. $5K pilot, 2 weeks, real measurable results"],
    ]
    reft = Table(ref_data, colWidths=[38 * mm, 128 * mm])
    reft.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR", (0, 0), (-1, -1), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
    ]))
    content.append(reft)

    # ── BUILD ─────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=14 * mm, bottomMargin=14 * mm,
        title="VeriOps Sales Cheat Sheet",
        author="VeriOps",
    )
    doc.build(content, onFirstPage=_header_footer, onLaterPages=_header_footer)


def main() -> int:
    output = Path("reports/docsops-sales-cheatsheet.pdf")
    output.parent.mkdir(parents=True, exist_ok=True)
    _build_pdf(output)
    print("[ok] sales cheat sheet: {}".format(output))
    print("[ok] absolute: {}".format(output.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

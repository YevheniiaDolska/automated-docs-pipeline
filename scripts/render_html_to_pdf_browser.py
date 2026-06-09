#!/usr/bin/env python3
"""Render a local HTML file to PDF using Playwright Chromium."""

from __future__ import annotations

import argparse
from pathlib import Path


def _render_html_to_pdf(
    *,
    html_input: Path,
    pdf_output: Path,
    page_format: str,
    margin_mm: int,
    print_background: bool,
) -> None:
    """Render the provided HTML file into a PDF using headless Chromium."""
    from playwright.sync_api import sync_playwright

    html_path = html_input.resolve()
    pdf_path = pdf_output.resolve()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            timeout=10_000,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        page = browser.new_page(viewport={"width": 1440, "height": 2200}, device_scale_factor=1.25)
        page.set_default_timeout(10_000)
        page.goto(html_path.as_uri(), wait_until="load")
        page.wait_for_timeout(900)
        page.pdf(
            path=str(pdf_path),
            format=page_format,
            print_background=print_background,
            margin={
                "top": f"{margin_mm}mm",
                "right": f"{margin_mm}mm",
                "bottom": f"{margin_mm}mm",
                "left": f"{margin_mm}mm",
            },
        )
        browser.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Render local HTML to PDF via Playwright Chromium.")
    parser.add_argument("--html-input", required=True)
    parser.add_argument("--pdf-output", required=True)
    parser.add_argument("--format", default="A4")
    parser.add_argument("--margin-mm", type=int, default=8)
    parser.add_argument("--no-print-background", action="store_true")
    args = parser.parse_args()

    _render_html_to_pdf(
        html_input=Path(args.html_input),
        pdf_output=Path(args.pdf_output),
        page_format=str(args.format),
        margin_mm=int(args.margin_mm),
        print_background=not bool(args.no_print_background),
    )
    print(f"[ok] browser PDF: {Path(args.pdf_output).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

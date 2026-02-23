#!/usr/bin/env python3
"""
Documentation Quality Badge Generator

Generates SVG badges (like coverage badges) for docs quality score.
Reads from reports/kpi-wall.json and outputs SVG badge files.

Usage:
    python3 scripts/generate_badge.py
    python3 scripts/generate_badge.py --json reports/kpi-wall.json --output reports/

Generates:
    - docs-quality-badge.svg    (overall quality score)
    - docs-metadata-badge.svg   (metadata completeness)
    - docs-freshness-badge.svg  (content freshness)
"""

import argparse
import json
from pathlib import Path


def _color_for_score(score: float) -> str:
    """Return badge color based on score."""
    if score >= 90:
        return "#4c1"       # bright green
    if score >= 80:
        return "#97ca00"    # green
    if score >= 70:
        return "#a3c51c"    # yellow-green
    if score >= 60:
        return "#dfb317"    # yellow
    if score >= 40:
        return "#fe7d37"    # orange
    return "#e05d44"        # red


def _make_badge_svg(label: str, value: str, color: str) -> str:
    """Generate a shields.io-style SVG badge."""
    # Calculate widths based on text length
    label_width = len(label) * 6.5 + 12
    value_width = len(value) * 7.5 + 12
    total_width = label_width + value_width

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20" role="img" aria-label="{label}: {value}">
  <title>{label}: {value}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="{total_width}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_width}" height="20" fill="#555"/>
    <rect x="{label_width}" width="{value_width}" height="20" fill="{color}"/>
    <rect width="{total_width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="11">
    <text aria-hidden="true" x="{label_width / 2}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_width / 2}" y="14">{label}</text>
    <text aria-hidden="true" x="{label_width + value_width / 2}" y="15" fill="#010101" fill-opacity=".3">{value}</text>
    <text x="{label_width + value_width / 2}" y="14">{value}</text>
  </g>
</svg>"""


def generate_badges(json_path: Path, output_dir: Path) -> list[str]:
    """Generate all badge SVGs from KPI data."""
    data = json.loads(json_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)

    badges_generated = []

    # Quality Score Badge
    score = data.get("quality_score", 0)
    svg = _make_badge_svg("docs quality", f"{score}/100", _color_for_score(score))
    path = output_dir / "docs-quality-badge.svg"
    path.write_text(svg, encoding="utf-8")
    badges_generated.append(str(path))

    # Metadata Completeness Badge
    meta = data.get("metadata_completeness_pct", 0)
    svg = _make_badge_svg("metadata", f"{meta}%", _color_for_score(meta))
    path = output_dir / "docs-metadata-badge.svg"
    path.write_text(svg, encoding="utf-8")
    badges_generated.append(str(path))

    # Freshness Badge
    stale_pct = data.get("stale_pct", 0)
    fresh_pct = round(100 - stale_pct, 1)
    svg = _make_badge_svg("freshness", f"{fresh_pct}%", _color_for_score(fresh_pct))
    path = output_dir / "docs-freshness-badge.svg"
    path.write_text(svg, encoding="utf-8")
    badges_generated.append(str(path))

    # Gaps Badge
    gaps = data.get("gap_high", 0)
    gap_label = f"{gaps} high" if gaps > 0 else "0"
    gap_color = "#4c1" if gaps == 0 else "#fe7d37" if gaps <= 3 else "#e05d44"
    svg = _make_badge_svg("doc gaps", gap_label, gap_color)
    path = output_dir / "docs-gaps-badge.svg"
    path.write_text(svg, encoding="utf-8")
    badges_generated.append(str(path))

    # Automated Checks Badge
    svg = _make_badge_svg("quality gates", "8 active", "#4c1")
    path = output_dir / "docs-gates-badge.svg"
    path.write_text(svg, encoding="utf-8")
    badges_generated.append(str(path))

    return badges_generated


def print_readme_snippet(output_dir: Path):
    """Print README markdown snippet for badges."""
    print("\nAdd these badges to your README.md:\n")
    print("```markdown")
    print(f"![Docs Quality](/{output_dir}/docs-quality-badge.svg)")
    print(f"![Metadata](/{output_dir}/docs-metadata-badge.svg)")
    print(f"![Freshness](/{output_dir}/docs-freshness-badge.svg)")
    print(f"![Doc Gaps](/{output_dir}/docs-gaps-badge.svg)")
    print(f"![Quality Gates](/{output_dir}/docs-gates-badge.svg)")
    print("```")


def main():
    parser = argparse.ArgumentParser(description="Generate documentation quality badges")
    parser.add_argument(
        "--json",
        default="reports/kpi-wall.json",
        help="Path to KPI wall JSON (default: reports/kpi-wall.json)",
    )
    parser.add_argument(
        "--output",
        default="reports",
        help="Output directory for badge SVGs (default: reports/)",
    )
    args = parser.parse_args()

    json_path = Path(args.json)
    output_dir = Path(args.output)

    if not json_path.exists():
        print(f"Error: {json_path} not found. Run 'npm run kpi-wall' first.")
        return 1

    badges = generate_badges(json_path, output_dir)

    for badge in badges:
        print(f"Badge generated: {badge}")

    print_readme_snippet(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

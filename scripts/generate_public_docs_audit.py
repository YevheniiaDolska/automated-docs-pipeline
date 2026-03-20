#!/usr/bin/env python3
"""Generate an external audit for public docs sites (no repo access required)."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen


CODE_PLACEHOLDER_PATTERN = re.compile(
    r"(<your-|YOUR_|{{|}}|api\.example\.com|your-domain\.example\.com)",
    flags=re.IGNORECASE,
)
ENDPOINT_PATTERN = re.compile(r"(/v\d+)?/[a-z0-9_\-/{}/]+")


def _normalize_url(raw: str) -> str:
    parsed = urlparse(raw.strip())
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    clean = parsed._replace(fragment="", query="", path=path)
    return urlunparse(clean)


def _is_http_url(raw: str) -> bool:
    try:
        parsed = urlparse(raw)
    except Exception:  # noqa: BLE001
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _same_host(a: str, b: str) -> bool:
    return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()


def _safe_pct(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def _fetch(url: str, timeout: int) -> tuple[int, str, str]:
    req = Request(
        url=url,
        headers={
            "User-Agent": "DocsOps-Public-Audit/1.0 (+https://docsops.local)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            status = int(getattr(resp, "status", 200) or 200)
            content_type = str(resp.headers.get("Content-Type", ""))
            body = resp.read().decode("utf-8", errors="ignore")
            return status, content_type, body
    except HTTPError as exc:
        return int(exc.code), "text/html", exc.read().decode("utf-8", errors="ignore")
    except URLError:
        return 0, "", ""


@dataclass
class PageData:
    url: str
    status: int
    title: str
    meta_description: str
    h1_count: int
    heading_levels: list[int]
    internal_links: list[str]
    external_links: list[str]
    code_blocks: list[dict[str, str]]
    text: str
    last_updated_hint: str


class _DocsHTMLParser(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.title = ""
        self.meta_description = ""
        self.h1_count = 0
        self.heading_levels: list[int] = []
        self.internal_links: list[str] = []
        self.external_links: list[str] = []
        self.code_blocks: list[dict[str, str]] = []
        self.text_chunks: list[str] = []
        self.last_updated_hint = ""

        self._in_title = False
        self._in_code = False
        self._in_pre = False
        self._code_lang = ""
        self._code_buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = dict(attrs)
        if tag == "title":
            self._in_title = True
            return
        if tag == "meta":
            name = str(attrs_map.get("name", "")).strip().lower()
            if name == "description":
                self.meta_description = str(attrs_map.get("content", "")).strip()
            return
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(tag[1])
            self.heading_levels.append(level)
            if level == 1:
                self.h1_count += 1
            return
        if tag == "a":
            href = str(attrs_map.get("href", "")).strip()
            if href:
                absolute = _normalize_url(urljoin(self.base_url, href))
                if _is_http_url(absolute):
                    if _same_host(absolute, self.base_url):
                        self.internal_links.append(absolute)
                    else:
                        self.external_links.append(absolute)
            return
        if tag == "pre":
            self._in_pre = True
            self._code_lang = ""
            self._code_buf = []
            return
        if tag == "code":
            self._in_code = True
            cls = str(attrs_map.get("class", "")).lower()
            m = re.search(r"language-([a-z0-9_+-]+)", cls)
            self._code_lang = m.group(1) if m else self._code_lang
            return
        if tag == "time":
            dt = str(attrs_map.get("datetime", "")).strip()
            if dt:
                self.last_updated_hint = dt

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
            return
        if tag == "code":
            self._in_code = False
            return
        if tag == "pre":
            self._in_pre = False
            code = "".join(self._code_buf).strip()
            if code:
                self.code_blocks.append({"language": self._code_lang or "text", "code": code})
            self._code_buf = []
            self._code_lang = ""

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        if self._in_title and not self.title:
            self.title = text
        if self._in_pre or self._in_code:
            self._code_buf.append(data)
        self.text_chunks.append(text)
        if not self.last_updated_hint and re.search(r"last\s+updated", text, flags=re.IGNORECASE):
            self.last_updated_hint = text

    def as_page(self, url: str, status: int) -> PageData:
        return PageData(
            url=url,
            status=status,
            title=self.title,
            meta_description=self.meta_description,
            h1_count=self.h1_count,
            heading_levels=self.heading_levels[:],
            internal_links=sorted(set(self.internal_links)),
            external_links=sorted(set(self.external_links)),
            code_blocks=self.code_blocks[:],
            text=" ".join(self.text_chunks),
            last_updated_hint=self.last_updated_hint,
        )


def _heading_violations(levels: list[int]) -> int:
    if not levels:
        return 0
    violations = 0
    prev = levels[0]
    for level in levels[1:]:
        if level - prev > 1:
            violations += 1
        prev = level
    return violations


def _estimate_example_reliability(pages: list[PageData]) -> dict[str, Any]:
    total = 0
    runnable = 0
    blocked_by_placeholders = 0
    network_bound = 0

    for page in pages:
        for block in page.code_blocks:
            lang = str(block.get("language", "text")).lower()
            code = str(block.get("code", ""))
            if lang in {"text", "yaml", "json", "toml", "ini"}:
                continue
            total += 1
            if CODE_PLACEHOLDER_PATTERN.search(code):
                blocked_by_placeholders += 1
                continue
            if "http://" in code.lower() or "https://" in code.lower() or "curl " in code.lower():
                network_bound += 1
                continue
            runnable += 1

    reliability = _safe_pct(runnable, total) if total else 0.0
    return {
        "total_code_examples": total,
        "runnable_without_env": runnable,
        "blocked_by_placeholders": blocked_by_placeholders,
        "network_bound_examples": network_bound,
        "example_reliability_estimate_pct": reliability,
    }


def _api_coverage_from_public_docs(pages: list[PageData]) -> dict[str, Any]:
    reference_endpoints: set[str] = set()
    non_reference_endpoints: set[str] = set()

    for page in pages:
        bucket = reference_endpoints if re.search(r"(reference|api)", page.url, flags=re.IGNORECASE) else non_reference_endpoints
        sources = [page.text] + [block.get("code", "") for block in page.code_blocks]
        for src in sources:
            for match in ENDPOINT_PATTERN.findall(src.lower()):
                cleaned = match.strip()
                if cleaned and len(cleaned) > 3 and cleaned.count("/") >= 1:
                    bucket.add(cleaned)

    total_ref = len(reference_endpoints)
    matched = len(reference_endpoints & non_reference_endpoints)
    uncovered = max(0, total_ref - matched)

    return {
        "reference_endpoint_count": total_ref,
        "endpoints_with_usage_docs": matched,
        "reference_endpoints_without_usage_docs": uncovered,
        "reference_coverage_pct": _safe_pct(matched, total_ref),
        "uncovered_endpoint_samples": sorted(list(reference_endpoints - non_reference_endpoints))[:20],
    }


def _seo_geo_metrics(pages: list[PageData]) -> dict[str, Any]:
    total = len(pages)
    missing_title = sum(1 for p in pages if not p.title.strip())
    missing_description = sum(1 for p in pages if not p.meta_description.strip())
    multi_h1 = sum(1 for p in pages if p.h1_count > 1)
    heading_jump = sum(1 for p in pages if _heading_violations(p.heading_levels) > 0)

    return {
        "pages_scanned": total,
        "missing_title_count": missing_title,
        "missing_description_count": missing_description,
        "multiple_h1_count": multi_h1,
        "heading_hierarchy_jump_count": heading_jump,
        "seo_geo_issue_rate_pct": _safe_pct(missing_title + missing_description + multi_h1 + heading_jump, max(1, total * 4)),
    }


def _link_health(pages: list[PageData], status_map: dict[str, int]) -> dict[str, Any]:
    internal_links = set()
    for page in pages:
        internal_links.update(page.internal_links)
    broken = [url for url in sorted(internal_links) if status_map.get(url, 0) >= 400 or status_map.get(url, 0) == 0]
    return {
        "internal_links_checked": len(internal_links),
        "broken_internal_links_count": len(broken),
        "broken_internal_link_samples": broken[:30],
    }


def _last_updated_metrics(pages: list[PageData]) -> dict[str, Any]:
    with_hint = [p for p in pages if p.last_updated_hint.strip()]
    return {
        "pages_with_last_updated_hint": len(with_hint),
        "pages_without_last_updated_hint": len(pages) - len(with_hint),
        "last_updated_coverage_pct": _safe_pct(len(with_hint), len(pages)),
        "samples_with_last_updated": [{"url": p.url, "hint": p.last_updated_hint[:120]} for p in with_hint[:10]],
    }


def _crawl_site(start_url: str, max_pages: int, timeout: int) -> tuple[list[PageData], dict[str, int]]:
    queue = deque([start_url])
    seen: set[str] = set()
    pages: list[PageData] = []
    status_map: dict[str, int] = {}

    while queue and len(seen) < int(max_pages):
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)

        status, content_type, body = _fetch(current, int(timeout))
        status_map[current] = status
        if status < 200 or status >= 400:
            continue
        if "html" not in content_type.lower():
            continue

        parser_html = _DocsHTMLParser(current)
        parser_html.feed(body)
        page = parser_html.as_page(current, status)
        pages.append(page)

        for link in page.internal_links:
            if link not in seen and len(seen) + len(queue) < int(max_pages) * 3:
                queue.append(link)

    for page in pages:
        for link in page.internal_links:
            if link in status_map:
                continue
            status, _, _ = _fetch(link, int(timeout))
            status_map[link] = status

    return pages, status_map


def _site_payload(site_url: str, max_pages: int, timeout: int) -> dict[str, Any]:
    pages, status_map = _crawl_site(site_url, max_pages, timeout)
    metrics = {
        "crawl": {
            "pages_crawled": len(pages),
            "requested_pages": len(status_map),
            "max_pages": int(max_pages),
        },
        "links": _link_health(pages, status_map),
        "seo_geo": _seo_geo_metrics(pages),
        "api_coverage": _api_coverage_from_public_docs(pages),
        "examples": _estimate_example_reliability(pages),
        "freshness": _last_updated_metrics(pages),
    }
    return {
        "site_url": site_url,
        "metrics": metrics,
        "samples": {
            "broken_links": metrics["links"]["broken_internal_link_samples"],
            "api_uncovered_samples": metrics["api_coverage"]["uncovered_endpoint_samples"],
        },
    }


def _aggregate_sites(sites: list[dict[str, Any]]) -> dict[str, Any]:
    def wavg(key_path: list[str]) -> float:
        acc = 0.0
        weight = 0
        for site in sites:
            cur: Any = site["metrics"]
            for key in key_path:
                cur = cur[key]
            pages = int(site["metrics"]["crawl"]["pages_crawled"])
            acc += float(cur) * pages
            weight += pages
        return round(acc / max(1, weight), 2)

    metrics = {
        "crawl": {
            "pages_crawled": sum(int(s["metrics"]["crawl"]["pages_crawled"]) for s in sites),
            "requested_pages": sum(int(s["metrics"]["crawl"]["requested_pages"]) for s in sites),
            "max_pages_total": sum(int(s["metrics"]["crawl"]["max_pages"]) for s in sites),
        },
        "links": {
            "broken_internal_links_count": sum(int(s["metrics"]["links"]["broken_internal_links_count"]) for s in sites),
        },
        "seo_geo": {
            "seo_geo_issue_rate_pct": wavg(["seo_geo", "seo_geo_issue_rate_pct"]),
        },
        "api_coverage": {
            "reference_coverage_pct": wavg(["api_coverage", "reference_coverage_pct"]),
        },
        "examples": {
            "example_reliability_estimate_pct": wavg(["examples", "example_reliability_estimate_pct"]),
        },
        "freshness": {
            "last_updated_coverage_pct": wavg(["freshness", "last_updated_coverage_pct"]),
        },
    }
    return {"metrics": metrics}


def _read_dotenv_value(env_file: Path, key: str) -> str:
    if not env_file.exists():
        return ""
    for raw in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() != key:
            continue
        value = v.strip().strip("'").strip('"')
        return value
    return ""


def _build_llm_prompt(payload: dict[str, Any], summary_only: bool = False) -> str:
    if summary_only:
        compact = {
            "site_urls": payload.get("site_urls", []),
            "topology_mode": payload.get("topology_mode", ""),
            "aggregate": payload.get("aggregate", {}),
            "top_findings": payload.get("top_findings", []),
        }
        audit_json = json.dumps(compact, ensure_ascii=True)
    else:
        audit_json = json.dumps(payload, ensure_ascii=True)
    return (
        "You are a strict documentation auditor.\\n"
        "Input is a structured public-docs audit JSON.\\n"
        "Produce compact executive analysis for a sales readout.\\n"
        "Return JSON only with keys: executive_summary, strengths, risks, prioritized_actions, limitations.\\n"
        "Rules:\\n"
        "- executive_summary: 4-6 sentences, concrete numbers only.\\n"
        "- strengths: array of max 5 bullets.\\n"
        "- risks: array of max 7 bullets.\\n"
        "- prioritized_actions: array of exactly 5 actions, each action includes impact and effort.\\n"
        "- limitations: 3-5 bullets explaining what external audit cannot guarantee.\\n"
        "Do not output markdown. Do not output commentary.\\n\\n"
        f"Audit JSON:\\n{audit_json}"
    )


def _run_llm_analysis(
    payload: dict[str, Any],
    model: str,
    api_key: str,
    timeout: int,
    summary_only: bool = False,
) -> dict[str, Any]:
    prompt = _build_llm_prompt(payload, summary_only=summary_only)
    body = {
        "model": model,
        "max_tokens": 1600,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = Request(
        url="https://api.anthropic.com/v1/messages",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")
    data = json.loads(raw or "{}")
    content = data.get("content", [])
    text = ""
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text = str(part.get("text", "")).strip()
                if text:
                    break
    if not text:
        raise RuntimeError("LLM response has no text content.")
    try:
        parsed = json.loads(text)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"LLM returned non-JSON content: {text[:300]}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("LLM response JSON root is not an object.")
    return parsed


def _build_html(payload: dict[str, Any]) -> str:
    m = payload["aggregate"]["metrics"]
    sites = payload.get("sites", [])
    sites_list = "".join(
        "<li><strong>{}</strong>: pages={}, broken_links={}, api_coverage={}%, examples={}%</li>".format(
            html.escape(str(site.get("site_url", ""))),
            site.get("metrics", {}).get("crawl", {}).get("pages_crawled", 0),
            site.get("metrics", {}).get("links", {}).get("broken_internal_links_count", 0),
            site.get("metrics", {}).get("api_coverage", {}).get("reference_coverage_pct", 0.0),
            site.get("metrics", {}).get("examples", {}).get("example_reliability_estimate_pct", 0.0),
        )
        for site in sites
    ) or "<li>No sites scanned.</li>"
    llm_block = ""
    llm = payload.get("llm_analysis", {})
    if isinstance(llm, dict):
        status = str(llm.get("status", "")).strip().lower()
        if status == "ok":
            analysis = llm.get("analysis", {}) if isinstance(llm.get("analysis"), dict) else {}
            summary = html.escape(str(analysis.get("executive_summary", "")))
            strengths = analysis.get("strengths", []) if isinstance(analysis.get("strengths"), list) else []
            risks = analysis.get("risks", []) if isinstance(analysis.get("risks"), list) else []
            actions = analysis.get("prioritized_actions", []) if isinstance(analysis.get("prioritized_actions"), list) else []
            llm_block = (
                "<div class=\"section\">"
                "<h2>LLM Executive Analysis (Claude Sonnet)</h2>"
                f"<p>{summary}</p>"
                "<h3>Strengths</h3><ul>"
                + "".join(f"<li>{html.escape(str(item))}</li>" for item in strengths[:5])
                + "</ul><h3>Risks</h3><ul>"
                + "".join(f"<li>{html.escape(str(item))}</li>" for item in risks[:7])
                + "</ul><h3>Prioritized actions</h3><ul>"
                + "".join(f"<li>{html.escape(str(item))}</li>" for item in actions[:5])
                + "</ul></div>"
            )
        elif status:
            reason = html.escape(str(llm.get("reason") or llm.get("error") or "not available"))
            llm_block = (
                "<div class=\"section\">"
                "<h2>LLM Executive Analysis (Claude Sonnet)</h2>"
                f"<p>Status: {html.escape(status)}. {reason}</p>"
                "</div>"
            )

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>Public Docs Audit</title>
<style>
  :root {{ --bg:#f8fafc; --text:#0f172a; --muted:#64748b; --card:#fff; --border:#e2e8f0; --accent:#0ea5e9; }}
  body {{ margin:0; font-family:\"Segoe UI\", Arial, sans-serif; background:linear-gradient(145deg,#ecfeff,#f8fafc); color:var(--text); }}
  .wrap {{ max-width:1050px; margin:0 auto; padding:24px 16px 40px; }}
  .hero,.section {{ background:var(--card); border:1px solid var(--border); border-radius:14px; padding:16px; margin-bottom:14px; }}
  h1 {{ margin:0 0 8px; font-size:28px; }}
  .sub {{ color:var(--muted); margin:0; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:10px; margin-top:12px; }}
  .card {{ border:1px solid var(--border); border-radius:10px; padding:12px; }}
  .value {{ font-size:30px; font-weight:700; color:var(--accent); margin-top:6px; }}
  .label {{ font-size:13px; color:var(--muted); }}
  ul {{ margin:8px 0 0 18px; }}
</style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"hero\">
      <h1>Public Documentation Audit</h1>
      <p class=\"sub\">Sites: {len(sites)} | topology: {html.escape(str(payload.get('topology_mode', 'single-product')))}</p>
      <p class=\"sub\">Generated: {html.escape(payload['generated_at'])}</p>
      <div class=\"grid\">
        <div class=\"card\"><div class=\"label\">Pages crawled</div><div class=\"value\">{m['crawl']['pages_crawled']}</div></div>
        <div class=\"card\"><div class=\"label\">Broken internal links</div><div class=\"value\">{m['links']['broken_internal_links_count']}</div></div>
        <div class=\"card\"><div class=\"label\">SEO/GEO issue rate</div><div class=\"value\">{m['seo_geo']['seo_geo_issue_rate_pct']}%</div></div>
        <div class=\"card\"><div class=\"label\">API reference coverage</div><div class=\"value\">{m['api_coverage']['reference_coverage_pct']}%</div></div>
        <div class=\"card\"><div class=\"label\">Example reliability (estimate)</div><div class=\"value\">{m['examples']['example_reliability_estimate_pct']}%</div></div>
        <div class=\"card\"><div class=\"label\">Last-updated coverage</div><div class=\"value\">{m['freshness']['last_updated_coverage_pct']}%</div></div>
      </div>
    </div>
    <div class=\"section\">
      <h2>Top Findings</h2>
      <ul>
        {''.join(f'<li>{html.escape(item)}</li>' for item in payload['top_findings'])}
      </ul>
    </div>
    <div class=\"section\">
      <h2>Per-site Summary</h2>
      <ul>
        {sites_list}
      </ul>
    </div>
    {llm_block}
  </div>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit public docs sites")
    parser.add_argument(
        "--site-url",
        action="append",
        default=[],
        help="Root docs URL; pass multiple times for multiple sites",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run as simple wizard and ask for inputs interactively",
    )
    parser.add_argument("--max-pages", type=int, default=120)
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument(
        "--topology-mode",
        choices=["single-product", "multi-project"],
        default="single-product",
        help="single-product: multiple docs sites may indicate fragmentation; multi-project: no fragmentation penalty",
    )
    parser.add_argument("--json-output", default="reports/public_docs_audit.json")
    parser.add_argument("--html-output", default="reports/public_docs_audit.html")
    parser.add_argument(
        "--llm-enabled",
        action="store_true",
        help="Add optional Claude executive analysis on top of deterministic metrics",
    )
    parser.add_argument(
        "--llm-model",
        default="claude-sonnet-4-5",
        help="Anthropic model name for executive analysis",
    )
    parser.add_argument(
        "--llm-env-file",
        default="/mnt/c/Users/Kroha/Documents/development/forge-marketing/.env",
        help="Path to .env file containing ANTHROPIC_API_KEY",
    )
    parser.add_argument(
        "--llm-api-key-env-name",
        default="ANTHROPIC_API_KEY",
        help="Env var key to read from --llm-env-file or environment",
    )
    parser.add_argument(
        "--llm-timeout",
        type=int,
        default=45,
        help="LLM request timeout in seconds",
    )
    parser.add_argument(
        "--llm-summary-only",
        action="store_true",
        help="Send only aggregate metrics to LLM (not per-page data). Much cheaper and faster.",
    )
    parser.add_argument(
        "--llm-summary-output",
        default="reports/public_docs_audit_llm_summary.json",
        help="Optional JSON file with LLM executive analysis",
    )
    parser.add_argument(
        "--report-url-base",
        default="",
        help="Optional public base URL to build report link (example: https://docsops.company.com/reports)",
    )
    parser.add_argument(
        "--generate-pdf",
        action="store_true",
        help="Automatically generate executive PDF after audit completes",
    )
    parser.add_argument(
        "--company-name",
        default="Client",
        help="Company name for executive PDF report",
    )
    parser.add_argument(
        "--pdf-output",
        default="reports/executive_audit_one_pager.pdf",
        help="Output path for executive PDF",
    )
    parser.add_argument(
        "--scorecard-json",
        default="reports/audit_scorecard.json",
        help="Path to audit scorecard JSON (for PDF generation)",
    )
    args = parser.parse_args()

    site_urls = list(args.site_url or [])
    if args.interactive:
        print("Public docs audit wizard")
        print("Enter all public documentation URLs (one per line).")
        print("Press Enter on empty line when finished.")
        collected: list[str] = []
        index = 1
        while True:
            raw = input(f"URL #{index}: ").strip()
            if not raw:
                if collected:
                    break
                print("At least one URL is required.")
                continue
            collected.append(raw)
            index += 1
        site_urls = collected
        mode = input(
            "Topology mode [single-product/multi-project] (default: single-product): "
        ).strip().lower()
        if mode in {"single-product", "multi-project"}:
            args.topology_mode = mode
        max_pages_raw = input(f"Max pages per site (default: {args.max_pages}): ").strip()
        if max_pages_raw.isdigit():
            args.max_pages = int(max_pages_raw)
        timeout_raw = input(f"Request timeout seconds (default: {args.timeout}): ").strip()
        if timeout_raw.isdigit():
            args.timeout = int(timeout_raw)
        out_dir_raw = input("Output directory (default: reports): ").strip()
        if out_dir_raw:
            out_dir = Path(out_dir_raw)
            args.json_output = str(out_dir / "public_docs_audit.json")
            args.html_output = str(out_dir / "public_docs_audit.html")
            args.llm_summary_output = str(out_dir / "public_docs_audit_llm_summary.json")
        print("Claude Sonnet executive analysis options:")
        print("  1) Summary only -- LLM gets aggregate metrics only (fast, ~$0.05)")
        print("  2) Full -- LLM gets all per-site data (slower, ~$3-4/site)")
        print("  3) None -- no LLM analysis")
        llm_raw = input("Choice [1/2/3] (default: 1): ").strip()
        if llm_raw in {"1", ""}:
            args.llm_enabled = True
            args.llm_summary_only = True
            env_file_raw = input(
                f"LLM .env path (default: {args.llm_env_file}): "
            ).strip()
            if env_file_raw:
                args.llm_env_file = env_file_raw
        elif llm_raw == "2":
            args.llm_enabled = True
            args.llm_summary_only = False
            env_file_raw = input(
                f"LLM .env path (default: {args.llm_env_file}): "
            ).strip()
            if env_file_raw:
                args.llm_env_file = env_file_raw
        else:
            args.llm_enabled = False
        company_raw = input("Company name for PDF report (default: Client): ").strip()
        if company_raw:
            args.company_name = company_raw
        pdf_raw = input("Generate executive PDF after audit? [Y/n]: ").strip().lower()
        args.generate_pdf = pdf_raw not in {"n", "no"}
        if args.generate_pdf:
            pdf_out_raw = input(f"PDF output path (default: {args.pdf_output}): ").strip()
            if pdf_out_raw:
                args.pdf_output = pdf_out_raw

    if not site_urls:
        raise SystemExit("No --site-url provided. Use --interactive or pass one or more --site-url values.")

    normalized_urls: list[str] = []
    for raw in site_urls:
        u = _normalize_url(raw)
        if not _is_http_url(u):
            raise SystemExit(f"Invalid --site-url: {raw}")
        if u not in normalized_urls:
            normalized_urls.append(u)

    sites = [_site_payload(url, int(args.max_pages), int(args.timeout)) for url in normalized_urls]
    aggregate = _aggregate_sites(sites)
    m = aggregate["metrics"]

    findings = []
    if m["links"]["broken_internal_links_count"] > 0:
        findings.append(f"Broken internal links: {m['links']['broken_internal_links_count']}")
    if m["seo_geo"]["seo_geo_issue_rate_pct"] > 10:
        findings.append(f"SEO/GEO issue rate is high: {m['seo_geo']['seo_geo_issue_rate_pct']}%")
    if m["api_coverage"]["reference_coverage_pct"] < 70:
        findings.append(f"API usage-doc coverage is low: {m['api_coverage']['reference_coverage_pct']}%")
    if m["examples"]["example_reliability_estimate_pct"] < 60:
        findings.append(f"Example reliability estimate is low: {m['examples']['example_reliability_estimate_pct']}%")
    if m["freshness"]["last_updated_coverage_pct"] < 50:
        findings.append(f"Freshness visibility is weak: only {m['freshness']['last_updated_coverage_pct']}% pages show last updated")
    if len(sites) > 1:
        if args.topology_mode == "single-product":
            findings.append("Documentation is split across multiple sites for one product; this is likely a discoverability/consistency risk.")
        else:
            findings.append("Documentation is split across multiple sites, but marked as multi-project; no fragmentation penalty applied.")
    if not findings:
        findings.append("No critical external issues found in sampled pages.")

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "site_url": normalized_urls[0] if len(normalized_urls) == 1 else "multiple-sites",
        "site_urls": normalized_urls,
        "topology_mode": str(args.topology_mode),
        "sites": sites,
        "aggregate": aggregate,
        "top_findings": findings,
    }

    if bool(args.llm_enabled):
        llm_api_key = os.environ.get(str(args.llm_api_key_env_name), "").strip()
        if not llm_api_key:
            llm_api_key = _read_dotenv_value(Path(args.llm_env_file), str(args.llm_api_key_env_name))
        if not llm_api_key:
            payload["llm_analysis"] = {
                "status": "skipped",
                "reason": (
                    f"Missing {args.llm_api_key_env_name}. "
                    f"Set env var or add it to {args.llm_env_file}."
                ),
            }
        else:
            try:
                llm_result = _run_llm_analysis(
                    payload,
                    model=str(args.llm_model),
                    api_key=llm_api_key,
                    timeout=int(args.llm_timeout),
                    summary_only=bool(getattr(args, "llm_summary_only", False)),
                )
                payload["llm_analysis"] = {
                    "status": "ok",
                    "model": str(args.llm_model),
                    "analysis": llm_result,
                }
                llm_path = Path(args.llm_summary_output)
                llm_path.parent.mkdir(parents=True, exist_ok=True)
                llm_path.write_text(json.dumps(payload["llm_analysis"], ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                payload["llm_analysis"] = {
                    "status": "failed",
                    "model": str(args.llm_model),
                    "error": str(exc),
                }

    json_path = Path(args.json_output)
    html_path = Path(args.html_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(_build_html(payload), encoding="utf-8")

    report_url = ""
    base = str(args.report_url_base).strip().rstrip("/")
    if base:
        report_url = f"{base}/{html_path.name}"

    print(f"[ok] public docs audit JSON: {json_path}")
    print(f"[ok] public docs audit HTML: {html_path}")
    print(f"[ok] public docs audit HTML (absolute): {html_path.resolve()}")
    if report_url:
        print(f"[ok] public docs audit URL: {report_url}")
    if bool(args.llm_enabled):
        llm_state = payload.get("llm_analysis", {}).get("status", "unknown")
        print(f"[ok] llm analysis status: {llm_state}")
        if llm_state == "ok":
            print(f"[ok] llm summary JSON: {args.llm_summary_output}")
    print(
        "[ok] summary: "
        f"sites={len(sites)} "
        f"pages={m['crawl']['pages_crawled']} "
        f"broken_links={m['links']['broken_internal_links_count']} "
        f"api_coverage={m['api_coverage']['reference_coverage_pct']}%"
    )

    if bool(getattr(args, "generate_pdf", False)):
        print("\n[pdf] generating executive PDF...")
        import subprocess
        pdf_cmd = [
            "python3", "scripts/generate_executive_audit_pdf.py",
            "--scorecard-json", str(getattr(args, "scorecard_json", "reports/audit_scorecard.json")),
            "--public-audit-json", str(args.json_output),
            "--llm-summary-json", str(args.llm_summary_output),
            "--company-name", str(getattr(args, "company_name", "Client")),
            "--output", str(getattr(args, "pdf_output", "reports/executive_audit_one_pager.pdf")),
        ]
        result = subprocess.run(pdf_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            pdf_path = Path(getattr(args, "pdf_output", "reports/executive_audit_one_pager.pdf"))
            print(f"[ok] executive PDF: {pdf_path}")
            print(f"[ok] executive PDF (absolute): {pdf_path.resolve()}")
        else:
            print(f"[warn] PDF generation failed: {result.stderr.strip()}")
            print("[hint] install reportlab: pip install reportlab")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

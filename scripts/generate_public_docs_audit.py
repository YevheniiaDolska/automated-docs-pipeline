#!/usr/bin/env python3
"""Generate an external audit for public docs sites (no repo access required)."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def _slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug (lowercase, hyphens)."""
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-") or "client"


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


def _sanitize_url(url: str) -> str:
    """Percent-encode non-ASCII characters so urllib can handle the URL.

    Some pages contain malformed hrefs with Unicode characters such as
    right/left quotes, em-dashes, or accented letters.  ``urllib`` raises
    ``UnicodeEncodeError`` when such a URL is fed to ``http.client``.
    """
    # Strip leading/trailing whitespace and common stray quotes
    url = url.strip().strip("\u201c\u201d\u2018\u2019\"'")
    parsed = urlparse(url)
    # Re-encode path and query: quote non-ASCII but keep already-encoded %XX
    from urllib.parse import quote, quote_plus  # noqa: E402
    clean_path = quote(parsed.path, safe="/:@!$&'()*+,;=-._~")
    clean_query = quote(parsed.query, safe="/:@!$&'()*+,;=-._~?=")
    clean_fragment = quote(parsed.fragment, safe="/:@!$&'()*+,;=-._~")
    try:
        clean_netloc = parsed.netloc.encode("idna").decode("ascii") if parsed.netloc else ""
    except (UnicodeError, UnicodeDecodeError):
        clean_netloc = parsed.netloc.encode("ascii", errors="ignore").decode("ascii")
    sanitized = urlunparse((
        parsed.scheme,
        clean_netloc,
        clean_path,
        parsed.params,
        clean_query,
        clean_fragment,
    ))
    return sanitized


_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
]


def _fetch(url: str, timeout: int, head_only: bool = False, _ua_idx: int = 0) -> tuple[int, str, str]:
    url = _sanitize_url(url)
    ua = _USER_AGENTS[min(_ua_idx, len(_USER_AGENTS) - 1)]
    req = Request(
        url=url,
        method="HEAD" if head_only else "GET",
        headers={
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            status = int(getattr(resp, "status", 200) or 200)
            content_type = str(resp.headers.get("Content-Type", ""))
            if head_only:
                return status, content_type, ""
            body = resp.read().decode("utf-8", errors="ignore")
            return status, content_type, body
    except HTTPError as exc:
        code = int(exc.code)
        # Follow 3xx redirects that urllib does not handle (e.g. 308)
        if 300 <= code < 400:
            location = exc.headers.get("Location", "") if exc.headers else ""
            if location and head_only:
                return 200, "text/html", ""  # redirect = alive
            if location and not head_only:
                try:
                    return _fetch(location, timeout, head_only=False, _ua_idx=_ua_idx)
                except Exception:  # noqa: BLE001
                    pass
            return code, "text/html", ""
        try:
            return code, "text/html", exc.read().decode("utf-8", errors="ignore")
        except Exception:  # noqa: BLE001
            return code, "text/html", ""
    except (URLError, OSError, TimeoutError):
        return 0, "", ""
    except Exception:  # noqa: BLE001 -- SSL, socket, redirect loops, etc.
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


_DATE_PATTERN = re.compile(
    r"\b\d{4}[-/]\d{2}[-/]\d{2}\b"
    r"|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b"
    r"|\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b",
    flags=re.IGNORECASE,
)

_UPDATED_TEXT_PATTERN = re.compile(
    r"(?:last\s+(?:updated|modified|edited|reviewed)|updated\s+on|modified\s+on|edited\s+on)",
    flags=re.IGNORECASE,
)

_HIGHLIGHT_CLASS_PATTERN = re.compile(
    r"highlight|codehilite|prism-code|hljs|shiki|code-block|sourceCode",
    flags=re.IGNORECASE,
)


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
        self._in_highlight_div = 0  # nesting counter for highlight wrappers
        self._code_lang = ""
        self._code_buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = dict(attrs)
        cls = str(attrs_map.get("class", "")).lower()

        if tag == "title":
            self._in_title = True
            return

        if tag == "meta":
            name = str(attrs_map.get("name", "")).strip().lower()
            prop = str(attrs_map.get("property", "")).strip().lower()
            content = str(attrs_map.get("content", "")).strip()
            if name == "description":
                self.meta_description = content
            # Detect last-modified from <meta property="article:modified_time">
            # or <meta name="revised"> or <meta http-equiv="last-modified">
            if not self.last_updated_hint and content:
                if prop in ("article:modified_time", "og:updated_time"):
                    self.last_updated_hint = content
                elif name in ("revised", "last-modified", "dcterms.modified"):
                    self.last_updated_hint = content
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
            # Some renderers put language class on <pre> directly
            m = re.search(r"language-([a-z0-9_+-]+)", cls)
            if m:
                self._code_lang = m.group(1)
            return

        if tag == "code":
            self._in_code = True
            m = re.search(r"language-([a-z0-9_+-]+)", cls)
            self._code_lang = m.group(1) if m else self._code_lang
            # Detect data-lang attribute (used by some SSGs)
            data_lang = str(attrs_map.get("data-lang", "") or attrs_map.get("data-language", "") or "").strip()
            if data_lang and not self._code_lang:
                self._code_lang = data_lang.lower()
            return

        # Detect highlight wrapper divs (MkDocs Material, Sphinx, etc.)
        if tag == "div" and _HIGHLIGHT_CLASS_PATTERN.search(cls):
            self._in_highlight_div += 1
            # Extract language from class like "highlight-python" or "language-js"
            m = re.search(r"(?:highlight|language)-([a-z0-9_+-]+)", cls)
            if m and m.group(1) not in ("highlight", "code"):
                self._code_lang = m.group(1)
            return

        if tag == "time":
            dt = str(attrs_map.get("datetime", "")).strip()
            if dt and not self.last_updated_hint:
                self.last_updated_hint = dt
            return

        # Universal date attribute detection on any element
        if not self.last_updated_hint:
            for attr_name in ("data-updated", "data-modified", "data-last-updated",
                              "data-date", "data-timestamp", "data-last-modified"):
                val = str(attrs_map.get(attr_name, "")).strip()
                if val:
                    self.last_updated_hint = val
                    break

        # Detect date-related CSS classes on any element (span, div, p, footer)
        if not self.last_updated_hint and cls:
            if re.search(r"git-revision-date|last[-_]?(?:updated|modified)|date[-_]?modified"
                         r"|revision[-_]?date|page[-_]?date|article[-_]?date|updated[-_]?at"
                         r"|modified[-_]?date|publish[-_]?date|doc[-_]?date", cls):
                # The date text will arrive in handle_data; flag detection
                pass

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
            return
        if tag == "code":
            # If <code> was standalone (not inside <pre>) but had language class
            # and accumulated content, treat as code block
            if not self._in_pre and self._code_buf:
                code = "".join(self._code_buf).strip()
                if code and self._code_lang:
                    self.code_blocks.append({"language": self._code_lang, "code": code})
                self._code_buf = []
            self._in_code = False
            return
        if tag == "pre":
            self._in_pre = False
            code = "".join(self._code_buf).strip()
            if code and not self._is_line_numbers_only(code):
                self.code_blocks.append({"language": self._code_lang or "text", "code": code})
            self._code_buf = []
            self._code_lang = ""
            return
        if tag == "div" and self._in_highlight_div > 0:
            self._in_highlight_div -= 1
            # Flush accumulated code when outermost highlight div closes
            # (only if not already flushed by a nested <pre> end)
            if self._in_highlight_div == 0 and not self._in_pre and not self._in_code and self._code_buf:
                code = "".join(self._code_buf).strip()
                if code:
                    self.code_blocks.append({"language": self._code_lang or "text", "code": code})
                self._code_buf = []
                self._code_lang = ""

    @staticmethod
    def _is_line_numbers_only(code: str) -> bool:
        """Return True if code is just line numbers (MkDocs Material table layout)."""
        stripped = code.strip()
        if not stripped:
            return False
        # Line numbers: all tokens are digits
        tokens = stripped.split()
        if not tokens:
            return False
        if all(t.isdigit() for t in tokens):
            return True
        # Sometimes digits are concatenated without spaces: "12345678"
        if stripped.isdigit() and len(stripped) <= 50:
            return True
        return False

    def handle_data(self, data: str) -> None:
        # Always collect raw data into code buffers (preserve whitespace)
        if self._in_pre or self._in_code:
            self._code_buf.append(data)
        elif self._in_highlight_div > 0:
            self._code_buf.append(data)

        text = data.strip()
        if not text:
            return
        if self._in_title and not self.title:
            self.title = text
        self.text_chunks.append(text)
        # Detect last-updated from text content
        if not self.last_updated_hint:
            if _UPDATED_TEXT_PATTERN.search(text):
                m = _DATE_PATTERN.search(text)
                if m:
                    self.last_updated_hint = text
                else:
                    # Mark that we saw the label; date might be in a sibling element
                    self.last_updated_hint = text
            elif _DATE_PATTERN.search(text) and len(text) < 60:
                # Short text that is just a date (common in footer/sidebar)
                # Only capture if it looks like a standalone date element
                pass

    def as_page(self, url: str, status: int) -> PageData:
        # Deduplicate code blocks (MkDocs Material tabs often repeat same content)
        seen: set[str] = set()
        unique_blocks: list[dict[str, str]] = []
        for block in self.code_blocks:
            key = block.get("code", "").strip()
            if key and key not in seen:
                seen.add(key)
                unique_blocks.append(block)
        return PageData(
            url=url,
            status=status,
            title=self.title,
            meta_description=self.meta_description,
            h1_count=self.h1_count,
            heading_levels=self.heading_levels[:],
            internal_links=sorted(set(self.internal_links)),
            external_links=sorted(set(self.external_links)),
            code_blocks=unique_blocks,
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


_DATA_ONLY_LANGS = {"text", "yaml", "json", "toml", "ini", "xml", "csv", "diff",
                     "log", "plaintext", "txt", "properties", "env", "conf", "cfg"}


def _estimate_example_reliability(pages: list[PageData]) -> dict[str, Any]:
    total = 0
    runnable = 0
    blocked_by_placeholders = 0
    network_bound = 0
    total_all_blocks = 0  # including data-only blocks, for detection quality metric

    for page in pages:
        for block in page.code_blocks:
            total_all_blocks += 1
            lang = str(block.get("language", "")).lower()
            code = str(block.get("code", ""))
            # Skip data-only formats (not executable code examples)
            if lang in _DATA_ONLY_LANGS:
                continue
            # Heuristic: unlabeled blocks with code-like content count as examples
            if not lang or lang == "nohighlight":
                # Check if it looks like code (has function calls, assignments, imports)
                if not re.search(r"[=();{}]|import |require\(|def |function |class |const |let |var ", code):
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
    # If we found no executable examples but did find code blocks, it is
    # likely a detection issue rather than truly 0% reliability.
    detection_note = ""
    if total == 0 and total_all_blocks > 0:
        detection_note = (
            "No executable code blocks detected ({} data-only blocks found). "
            "Site may use non-standard code rendering that the auditor does not "
            "recognize, or all examples are in data formats (YAML/JSON)."
        ).format(total_all_blocks)
    elif total == 0 and total_all_blocks == 0:
        detection_note = (
            "No code blocks detected in crawled pages. The site may use "
            "JavaScript-rendered code blocks invisible to the HTML parser."
        )
    return {
        "total_code_examples": total,
        "total_code_blocks_all": total_all_blocks,
        "runnable_without_env": runnable,
        "blocked_by_placeholders": blocked_by_placeholders,
        "network_bound_examples": network_bound,
        "example_reliability_estimate_pct": reliability,
        "detection_note": detection_note,
    }


_API_URL_PATTERN = re.compile(
    r"(reference|api|endpoint|method|operation|resource|rest|graphql|sdk|swagger|openapi|redoc)",
    flags=re.IGNORECASE,
)

# Content-based heuristics: HTTP methods, status codes, request/response blocks
_API_CONTENT_INDICATORS = re.compile(
    r"\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+/[a-z]"
    r"|\bHTTP/[12]\.\d\b"
    r"|\b[2345]\d{2}\s"
    r"|\bcurl\s"
    r"|\bRequest\s+body\b"
    r"|\bResponse\s+body\b"
    r"|\bapplication/json\b"
    r"|\bAuthorization:\s"
    r"|\bContent-Type:\s",
    flags=re.IGNORECASE,
)


def _is_api_page(page: PageData) -> bool:
    """Detect API reference pages via URL patterns AND content heuristics."""
    # URL-based detection (expanded patterns)
    if _API_URL_PATTERN.search(page.url):
        return True
    # Content-based detection: if page has 3+ HTTP method / status code indicators
    text_sample = page.text[:5000]
    code_sample = " ".join(b.get("code", "") for b in page.code_blocks[:10])
    combined = text_sample + " " + code_sample
    matches = _API_CONTENT_INDICATORS.findall(combined)
    return len(matches) >= 3


def _api_coverage_from_public_docs(pages: list[PageData]) -> dict[str, Any]:
    reference_endpoints: set[str] = set()
    non_reference_endpoints: set[str] = set()

    api_page_count = 0
    for page in pages:
        is_api = _is_api_page(page)
        if is_api:
            api_page_count += 1
        bucket = reference_endpoints if is_api else non_reference_endpoints
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
        "api_pages_detected": api_page_count,
        "endpoints_with_usage_docs": matched,
        "reference_endpoints_without_usage_docs": uncovered,
        "reference_coverage_pct": _safe_pct(matched, total_ref) if total_ref > 0 else -1.0,
        "no_api_pages_found": total_ref == 0 and api_page_count == 0,
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


_REPO_HOST_PATTERNS = re.compile(
    r"github\.com|gitlab\.com|bitbucket\.org|codeberg\.org",
    flags=re.IGNORECASE,
)


def _is_repo_link(url: str) -> bool:
    """Return True if *url* points to a code repository (not user-facing docs)."""
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if not _REPO_HOST_PATTERNS.search(host):
        return False
    path = parsed.path.lower()
    # Repo navigation: /tree/, /blob/, /commit/, /pull/, /issues/, /raw/, /compare/
    repo_segments = ("/tree/", "/blob/", "/commit/", "/commits/", "/pull/",
                     "/issues/", "/raw/", "/compare/", "/actions/", "/releases/tag/",
                     "/blame/", "/edit/", "/delete/", "/find/", "/archive/")
    return any(seg in path for seg in repo_segments)


def _link_health(pages: list[PageData], status_map: dict[str, int]) -> dict[str, Any]:
    internal_links = set()
    for page in pages:
        internal_links.update(page.internal_links)
    # Only count confirmed 4xx/5xx as broken; exclude timeouts (0) and redirects (3xx)
    broken = [url for url in sorted(internal_links) if status_map.get(url, 0) >= 400]
    unreachable = [url for url in sorted(internal_links) if status_map.get(url, 0) == 0]
    # Separate docs-site broken links from repository navigation broken links
    docs_broken = [u for u in broken if not _is_repo_link(u)]
    repo_broken = [u for u in broken if _is_repo_link(u)]
    return {
        "internal_links_checked": len(internal_links),
        "broken_internal_links_count": len(broken),
        "docs_broken_links_count": len(docs_broken),
        "repo_broken_links_count": len(repo_broken),
        "broken_internal_link_samples": docs_broken[:20] + repo_broken[:10],
        "docs_broken_link_samples": docs_broken[:30],
        "repo_broken_link_samples": repo_broken[:30],
        "unreachable_links_count": len(unreachable),
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
    """Crawl *start_url* up to *max_pages* with parallel BFS + parallel link check.

    If the first attempt yields zero pages (site blocks requests), automatically
    retries with alternative User-Agent strings before giving up.
    """

    max_pages = int(max_pages)
    timeout = int(timeout)
    workers = min(max_pages, 10)  # parallel crawl workers

    # Try up to len(_USER_AGENTS) User-Agent variants for the start page
    for ua_attempt in range(len(_USER_AGENTS)):
        seen: set[str] = set()
        pages: list[PageData] = []
        status_map: dict[str, int] = {}
        queue: list[str] = [start_url]

        if ua_attempt > 0:
            print("[audit] retry with alternative User-Agent ({}/{})...".format(
                ua_attempt + 1, len(_USER_AGENTS)), flush=True)
        else:
            print("[audit] crawling up to {} pages ({} workers)...".format(max_pages, workers), flush=True)

        def _crawl_one(url: str, _ua: int = ua_attempt) -> tuple[str, int, PageData | None, list[str]]:
            """Fetch + parse one page.  Returns (url, status, page_or_None, new_links)."""
            st, ct, body = _fetch(url, timeout, _ua_idx=_ua)
            if st < 200 or st >= 400 or "html" not in ct.lower():
                return url, st, None, []
            parser_html = _DocsHTMLParser(url)
            parser_html.feed(body)
            page = parser_html.as_page(url, st)
            return url, st, page, page.internal_links

        with ThreadPoolExecutor(max_workers=workers) as pool:
            while queue and len(seen) < max_pages:
                # Submit a batch of URLs (up to remaining budget)
                batch: list[str] = []
                while queue and len(seen) + len(batch) < max_pages:
                    candidate = queue.pop(0)
                    if candidate not in seen:
                        seen.add(candidate)
                        batch.append(candidate)
                if not batch:
                    break

                futures = {pool.submit(_crawl_one, u): u for u in batch}
                for future in as_completed(futures):
                    url, st, page, new_links = future.result()
                    status_map[url] = st
                    if page is not None:
                        pages.append(page)
                        print(
                            "[audit] page {}/{}: {}".format(len(pages), max_pages, url[:80]),
                            flush=True,
                        )
                        for link in new_links:
                            if link not in seen and len(seen) + len(queue) < max_pages * 3:
                                queue.append(link)

        # If we got at least 1 page, stop retrying
        if pages:
            break
        # Log what happened with the start URL
        start_status = status_map.get(start_url, 0)
        print("[warn] 0 pages fetched (start URL status={}). ".format(start_status), end="", flush=True)
        if ua_attempt < len(_USER_AGENTS) - 1:
            print("Retrying...", flush=True)
        else:
            print("All User-Agent variants exhausted.", flush=True)

    # -- Parallel link-health check (HEAD-only, short timeout, 50 workers) ------
    link_timeout = min(timeout, 3)
    link_workers = 50
    unchecked: set[str] = set()
    for page in pages:
        for link in page.internal_links:
            if link not in status_map:
                unchecked.add(link)

    if unchecked:
        done = 0
        total = len(unchecked)
        print("[audit] checking {} unique links ({} workers)...".format(total, link_workers), flush=True)

        def _check_one(link: str) -> tuple[str, int]:
            st, _, _ = _fetch(link, link_timeout, head_only=True)
            # Many SPA/SSG sites return 404 for HEAD but 200 for GET; retry
            if st >= 400 or st == 0:
                st2, ct2, _ = _fetch(link, link_timeout)
                if 200 <= st2 < 400:
                    st = st2
            return link, st

        with ThreadPoolExecutor(max_workers=link_workers) as pool:
            futures = {pool.submit(_check_one, lnk): lnk for lnk in unchecked}
            for future in as_completed(futures):
                link, st = future.result()
                status_map[link] = st
                done += 1
                if done % 100 == 0 or done == total:
                    print("[audit] links: {}/{}".format(done, total), flush=True)

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
            "docs_broken_link_samples": metrics["links"].get("docs_broken_link_samples", []),
            "repo_broken_link_samples": metrics["links"].get("repo_broken_link_samples", []),
            "api_uncovered_samples": metrics["api_coverage"]["uncovered_endpoint_samples"],
        },
    }


def _aggregate_api_coverage(sites: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate API coverage across sites, treating -1.0 (N/A) correctly."""
    total_ref = 0
    total_usage = 0
    all_na = True
    for s in sites:
        ac = s["metrics"]["api_coverage"]
        if not ac.get("no_api_pages_found"):
            all_na = False
            total_ref += int(ac.get("reference_endpoint_count", 0))
            total_usage += int(ac.get("endpoints_with_usage_docs", 0))
    if all_na:
        return {"reference_coverage_pct": -1.0, "no_api_pages_found": True}
    pct = round(total_usage / max(1, total_ref) * 100, 2) if total_ref else 0.0
    return {"reference_coverage_pct": pct, "no_api_pages_found": False}


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
            "docs_broken_links_count": sum(int(s["metrics"]["links"].get("docs_broken_links_count", 0)) for s in sites),
            "repo_broken_links_count": sum(int(s["metrics"]["links"].get("repo_broken_links_count", 0)) for s in sites),
        },
        "seo_geo": {
            "seo_geo_issue_rate_pct": wavg(["seo_geo", "seo_geo_issue_rate_pct"]),
        },
        "api_coverage": _aggregate_api_coverage(sites),
        "examples": {
            "example_reliability_estimate_pct": wavg(["examples", "example_reliability_estimate_pct"]),
        },
        "freshness": {
            "last_updated_coverage_pct": wavg(["freshness", "last_updated_coverage_pct"]),
        },
    }
    return {"metrics": metrics}


def _resolve_cross_platform_path(p: Path) -> Path:
    """Convert between WSL and Windows paths if needed."""
    s = str(p)
    if not p.exists():
        # WSL path on Windows: /mnt/c/Users/... -> C:\Users\...
        if s.startswith("/mnt/") and len(s) > 6 and s[5].isalpha() and s[6] == "/":
            win = "{}:{}".format(s[5].upper(), s[6:].replace("/", "\\"))
            candidate = Path(win)
            if candidate.exists():
                return candidate
        # Windows path on WSL: C:\Users\... -> /mnt/c/Users/...
        if len(s) >= 3 and s[1] == ":" and s[2] in ("/", "\\"):
            wsl = "/mnt/{}/{}".format(s[0].lower(), s[3:].replace("\\", "/"))
            candidate = Path(wsl)
            if candidate.exists():
                return candidate
    return p


def _read_dotenv_value_from_file(env_file: Path, key: str) -> str:
    """Read a single key from a .env file, return empty string if not found."""
    env_file = _resolve_cross_platform_path(env_file)
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


def _read_dotenv_value(env_file_hint: str, key: str) -> str:
    """Search for *key* across multiple .env locations.

    Search order:
    1. The explicit path provided via ``--llm-env-file``.
    2. ``.env`` in the script's own repository root (Auto-Doc Pipeline).
    3. ``.env`` in the current working directory.
    4. Common sibling project location (forge-marketing).

    Each candidate is tried with cross-platform path resolution so the
    same invocation works from both WSL and native Windows Python.
    """
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent  # Auto-Doc Pipeline root

    candidates: list[Path] = []
    # Explicit user-provided path always first
    if env_file_hint:
        candidates.append(Path(env_file_hint))
    # Repo-local .env (user copied it here)
    candidates.append(repo_root / ".env")
    # CWD .env
    candidates.append(Path.cwd() / ".env")
    # Legacy fallback: forge-marketing sibling
    candidates.append(repo_root.parent / "forge-marketing" / ".env")

    for candidate in candidates:
        val = _read_dotenv_value_from_file(candidate, key)
        if val:
            return val
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
        "- strengths: array of max 5 bullets (strings).\\n"
        "- risks: array of max 7 bullets (strings).\\n"
        "- prioritized_actions: array of exactly 5 objects, each with keys "
        "{\\\"action\\\": \\\"text\\\", \\\"impact\\\": \\\"critical|high|medium|low\\\", "
        "\\\"effort\\\": \\\"high|medium|low\\\"}.\\n"
        "- limitations: 3-5 bullets explaining what external audit cannot guarantee.\\n"
        "IMPORTANT context notes:\\n"
        "- If broken links include repo_broken_links_count, those are repository "
        "navigation links (GitHub/GitLab), not user-facing docs. Separate them in analysis.\\n"
        "- If detection_note is set on examples or api_coverage shows no_api_pages_found "
        "on large samples (500+ pages), flag as potential detection limitation.\\n"
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
    # Strip markdown code fences (```json ... ```) that Claude sometimes wraps around JSON
    stripped = text.strip()
    if stripped.startswith("```"):
        first_nl = stripped.find("\n")
        if first_nl != -1:
            stripped = stripped[first_nl + 1:]
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()
    try:
        parsed = json.loads(stripped)
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
                + "".join(
                    "<li>{}</li>".format(
                        html.escape(str(item.get("action", "")))
                        + (" <em>[{}, {}]</em>".format(
                            html.escape(str(item.get("impact", ""))),
                            html.escape(str(item.get("effort", "")))
                        ) if isinstance(item, dict) and item.get("impact") else "")
                        if isinstance(item, dict) else html.escape(str(item))
                    )
                    for item in actions[:5]
                )
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
        <div class=\"card\"><div class=\"label\">Broken links (docs)</div><div class=\"value\">{m['links'].get('docs_broken_links_count', m['links']['broken_internal_links_count'])}</div></div>
        <div class=\"card\"><div class=\"label\">Broken links (repo nav)</div><div class=\"value\">{m['links'].get('repo_broken_links_count', 0)}</div></div>
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
        default="",
        help="Path to .env file containing ANTHROPIC_API_KEY (auto-searches repo root and common locations if empty)",
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
        default=None,
        help="Output path for executive PDF. Defaults to reports/{company-slug}-executive-audit.pdf",
    )
    parser.add_argument(
        "--scorecard-json",
        default="reports/audit_scorecard.json",
        help="Path to audit scorecard JSON (for PDF generation)",
    )
    args = parser.parse_args()

    # -- License gate: public docs audit requires enterprise plan --
    try:
        from scripts.license_gate import require
        require("executive_audit_pdf")
    except ImportError:
        pass

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
            default_pdf = "reports/{}-executive-audit.pdf".format(_slugify(args.company_name))
            pdf_out_raw = input(f"PDF output path (default: {default_pdf}): ").strip()
            args.pdf_output = pdf_out_raw if pdf_out_raw else default_pdf

    if not site_urls:
        raise SystemExit("No --site-url provided. Use --interactive or pass one or more --site-url values.")

    normalized_urls: list[str] = []
    for raw in site_urls:
        u = _normalize_url(raw)
        if not _is_http_url(u):
            raise SystemExit(f"Invalid --site-url: {raw}")
        if u not in normalized_urls:
            normalized_urls.append(u)

    # Process sites in parallel when multiple URLs are provided.
    if len(normalized_urls) == 1:
        sites = [_site_payload(normalized_urls[0], int(args.max_pages), int(args.timeout))]
    else:
        print("[audit] processing {} sites in parallel...".format(len(normalized_urls)), flush=True)
        sites = []
        with ThreadPoolExecutor(max_workers=min(len(normalized_urls), 4)) as pool:
            futures = {
                pool.submit(_site_payload, url, int(args.max_pages), int(args.timeout)): url
                for url in normalized_urls
            }
            for future in as_completed(futures):
                sites.append(future.result())
    aggregate = _aggregate_sites(sites)
    m = aggregate["metrics"]

    findings = []
    total_pages = m["crawl"]["pages_crawled"]
    if total_pages == 0:
        findings.append(
            "Crawler could not fetch any pages. The site may block automated "
            "requests, require JavaScript rendering, or be temporarily unavailable. "
            "Metrics below are unavailable."
        )
    docs_broken = int(m["links"].get("docs_broken_links_count", 0))
    repo_broken = int(m["links"].get("repo_broken_links_count", 0))
    total_broken = int(m["links"]["broken_internal_links_count"])
    if total_broken > 0:
        if repo_broken > 0 and docs_broken > 0:
            findings.append(
                "Broken links: {} on docs sites, {} in repository navigation "
                "(repo links are not user-facing documentation)".format(docs_broken, repo_broken)
            )
        elif repo_broken > 0 and docs_broken == 0:
            findings.append(
                "Broken links: {} in repository navigation only "
                "(not user-facing documentation)".format(repo_broken)
            )
        else:
            findings.append("Broken internal links: {}".format(total_broken))
    if m["seo_geo"]["seo_geo_issue_rate_pct"] > 10:
        findings.append(f"SEO/GEO issue rate is high: {m['seo_geo']['seo_geo_issue_rate_pct']}%")
    api_cov = m["api_coverage"]["reference_coverage_pct"]
    api_pages = int(m["api_coverage"].get("api_pages_detected", 0))
    if m["api_coverage"].get("no_api_pages_found"):
        if total_pages >= 500:
            findings.append(
                "API reference pages not detected in {} crawled pages "
                "(possible detection limitation -- site may use non-standard URL patterns)".format(total_pages)
            )
        else:
            findings.append(
                "No API reference pages found in {} crawled pages "
                "(increase max_pages or check site URL structure)".format(total_pages)
            )
    elif api_cov < 70:
        findings.append("API usage-doc coverage is low: {}% ({} API pages detected)".format(api_cov, api_pages))
    ex_pct = m["examples"]["example_reliability_estimate_pct"]
    ex_note = str(m["examples"].get("detection_note", "") or "")
    if ex_pct < 60:
        if ex_pct < 0.1 and total_pages >= 500:
            findings.append(
                "Example reliability: 0% on {} pages (likely detection limitation). {}".format(
                    total_pages, ex_note or "Site may use JS-rendered code blocks.")
            )
        else:
            findings.append("Example reliability estimate is low: {}%".format(ex_pct))
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
            llm_api_key = _read_dotenv_value(str(args.llm_env_file), str(args.llm_api_key_env_name))
        if not llm_api_key:
            payload["llm_analysis"] = {
                "status": "skipped",
                "reason": (
                    f"Missing {args.llm_api_key_env_name}. "
                    "Set env var or place .env in the repo root."
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
        "api_coverage={}".format("N/A (no API pages in sample)" if m["api_coverage"].get("no_api_pages_found") else f"{m['api_coverage']['reference_coverage_pct']}%")
    )

    if bool(getattr(args, "generate_pdf", False)):
        print("\n[pdf] generating executive PDF...")
        import subprocess
        company = str(getattr(args, "company_name", "Client"))
        pdf_output = getattr(args, "pdf_output", None)
        if not pdf_output:
            pdf_output = "reports/{}-executive-audit.pdf".format(_slugify(company))
        pdf_cmd = [
            "python3", "scripts/generate_executive_audit_pdf.py",
            "--scorecard-json", str(getattr(args, "scorecard_json", "reports/audit_scorecard.json")),
            "--public-audit-json", str(args.json_output),
            "--llm-summary-json", str(args.llm_summary_output),
            "--company-name", company,
            "--output", str(pdf_output),
        ]
        result = subprocess.run(pdf_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            pdf_path = Path(pdf_output)
            print(f"[ok] executive PDF: {pdf_path}")
            print(f"[ok] executive PDF (absolute): {pdf_path.resolve()}")
        else:
            print(f"[warn] PDF generation failed: {result.stderr.strip()}")
            print("[hint] install reportlab: pip install reportlab")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

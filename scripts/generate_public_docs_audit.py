#!/usr/bin/env python3
"""Generate an external audit for public docs sites (no repo access required)."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import html
import json
import logging
import os
import re
import subprocess
import sys
import statistics
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
try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore

logger = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.llm_egress import ensure_external_allowed, load_policy, redact_payload


CODE_PLACEHOLDER_PATTERN = re.compile(
    r"(<your-|YOUR_|{{|}}|api\.example\.com|your-domain\.example\.com)",
    flags=re.IGNORECASE,
)
ENDPOINT_PATTERN = re.compile(
    r"(?<![a-z0-9])"
    r"(/(?:[a-z0-9._~!$&'()*+,;=:@%-]+|\{[a-z0-9._~-]+\})"
    r"(?:/(?:[a-z0-9._~!$&'()*+,;=:@%-]+|\{[a-z0-9._~-]+\}))*)",
    flags=re.IGNORECASE,
)
_CLOUD_PROVIDER_PATTERN = re.compile(r"^(aws|azure|gcp)$", flags=re.IGNORECASE)
_LOCALE_PATTERN = re.compile(r"^[a-z]{2}(?:-[a-z]{2})?$", flags=re.IGNORECASE)
_INCONCLUSIVE_HTTP_STATUSES = {0, -2, 401, 403, 405, 406, 408, 425, 429, 500, 502, 503, 504}
_LINK_STATUS_ALIVE = "alive"
_LINK_STATUS_CONFIRMED_BROKEN = "confirmed_broken"
_LINK_STATUS_UNVERIFIED = "unverified"
_LINK_STATUS_EXCLUDED = "excluded"
_EXCLUDED_PATH_EXTENSIONS = (
    ".css", ".js", ".mjs", ".map", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot", ".pdf", ".zip", ".tar", ".gz", ".bz2", ".7z",
)
_EXCLUDED_PATH_SEGMENTS = (
    "/assets/", "/static/", "/_static/", "/images/", "/img/", "/fonts/", "/scripts/",
    "/search", "/sitemap", "/rss", "/feed",
)
_CONTRACT_PATH_CANDIDATES = (
    "/openapi.json", "/openapi.yaml", "/openapi.yml",
    "/swagger.json", "/swagger.yaml", "/swagger.yml",
    "/api-docs", "/v1/api-docs", "/v2/api-docs",
    "/graphql", "/graphql/schema", "/schema.graphql",
    "/asyncapi.json", "/asyncapi.yaml", "/asyncapi.yml",
    "/ws", "/websocket",
)

_SITEMAP_HINT_RE = re.compile(r"(?im)^\s*sitemap\s*:\s*(\S+)\s*$")
_URLSET_LOC_RE = re.compile(r"(?is)<loc>\s*(.*?)\s*</loc>")
_RSS_LINK_RE = re.compile(r"(?is)<link>\s*(https?://[^<\s]+)\s*</link>")
_CRAWL_TRAP_QUERY_KEYS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid", "yclid", "mc_cid", "mc_eid", "ref", "source", "session",
    "sort", "order", "view", "format", "print", "filter", "filters", "page",
    "cursor", "offset", "start", "end", "date", "month", "year", "calendar",
}
_CRAWL_TRAP_PATH_HINTS = (
    "/search", "/calendar", "/tag/", "/tags/", "/archive/", "/archives/",
)
_MAX_TEXT_CHUNKS_PER_PAGE = 5000
_MAX_TEXT_CHARS_PER_PAGE = 200_000
_MAX_LINKS_PER_PAGE = 1_500
_MAX_LINK_HEALTH_CHECKS = 60_000
_MAX_CODE_BUFFER_CHARS = 400_000
_MAX_CODE_BLOCK_CHARS = 100_000
_MAX_CODE_BLOCKS_PER_PAGE = 300


def _slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug (lowercase, hyphens)."""
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-") or "client"


def _normalize_url(raw: str) -> str:
    value = str(raw or "").strip()
    # Accept wizard input without scheme, e.g. "docs.example.com/path".
    if value and "://" not in value and not value.startswith("/"):
        value = "https://" + value
    try:
        parsed = urlparse(value)
    except (ValueError, TypeError):
        # Malformed values like "https://[service.name]" should not crash audit.
        return ""
    path = parsed.path or "/"
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 4:
        p0, p1, p2, p3 = parts[0], parts[1], parts[2], parts[3]
        if (
            _CLOUD_PROVIDER_PATTERN.match(p0)
            and _LOCALE_PATTERN.match(p1)
            and _CLOUD_PROVIDER_PATTERN.match(p2)
            and _LOCALE_PATTERN.match(p3)
            and p0.lower() == p2.lower()
        ):
            fixed_parts = [p0, p3] + parts[4:]
            path = "/" + "/".join(fixed_parts)
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    clean = parsed._replace(fragment="", query="", path=path)
    return urlunparse(clean)


def _safe_join_normalize_url(base_url: str, href: str) -> str:
    """Safely join and normalize a discovered href.

    Broken HTML can contain malformed bracket hosts, invalid ports, or junk
    characters that make urllib parsing raise ValueError. A single bad link
    must never crash the crawl worker.
    """
    try:
        joined = urljoin(base_url, href)
    except (ValueError, TypeError):
        return ""
    try:
        return _normalize_url(joined)
    except (ValueError, TypeError):
        return ""


def _is_probable_crawl_trap(url: str) -> bool:
    parsed = urlparse(url)
    path = (parsed.path or "/").lower()
    if any(hint in path for hint in _CRAWL_TRAP_PATH_HINTS):
        return True
    if not parsed.query:
        return False
    keys = [part.split("=", 1)[0].strip().lower() for part in parsed.query.split("&") if part.strip()]
    if len(keys) >= 4:
        return True
    return any(k in _CRAWL_TRAP_QUERY_KEYS for k in keys)


def _extract_http_urls_from_xml(body: str) -> list[str]:
    urls: list[str] = []
    for match in _URLSET_LOC_RE.findall(body or ""):
        candidate = _normalize_url(str(match).strip())
        if _is_http_url(candidate) and candidate not in urls:
            urls.append(candidate)
    return urls


def _discover_seed_urls_from_sitemaps(
    start_url: str,
    timeout: int,
    auth_headers: dict[str, str] | None = None,
) -> tuple[set[str], int]:
    parsed = urlparse(start_url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    auth_headers = auth_headers or {}
    discovered: set[str] = set()
    robot_sitemap_count = 0

    robots_url = f"{root}/robots.txt"
    st, _, body = _fetch(robots_url, max(4, int(timeout)), extra_headers=auth_headers)
    sitemap_candidates: list[str] = []
    if 200 <= st < 400 and body:
        for raw_url in _SITEMAP_HINT_RE.findall(body):
            candidate = _normalize_url(str(raw_url).strip())
            if _is_http_url(candidate):
                sitemap_candidates.append(candidate)
                robot_sitemap_count += 1

    # Common sitemap endpoints (include when robots.txt does not declare them).
    for suffix in ("/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml"):
        sitemap_candidates.append(_normalize_url(root + suffix))

    # Breadth-limited sitemap traversal to avoid unbounded sitemap index loops.
    checked: set[str] = set()
    queue: deque[str] = deque(dict.fromkeys(sitemap_candidates))
    while queue and len(checked) < 30:
        sitemap_url = _normalize_url(queue.popleft())
        if sitemap_url in checked:
            continue
        checked.add(sitemap_url)
        st, ct, body = _fetch(sitemap_url, max(4, int(timeout)), extra_headers=auth_headers)
        if not (200 <= st < 400):
            continue
        text = body or ""
        if ("xml" not in ct.lower()) and "<urlset" not in text.lower() and "<sitemapindex" not in text.lower():
            continue
        for loc in _extract_http_urls_from_xml(text):
            if not _same_host(loc, start_url):
                continue
            if loc.endswith(".xml") and ("sitemap" in loc.lower()) and loc not in checked:
                queue.append(loc)
                continue
            discovered.add(loc)
            if len(discovered) >= 120000:
                break
        if len(discovered) >= 120000:
            break
    return discovered, robot_sitemap_count


def _discover_seed_urls_from_feeds(
    start_url: str,
    timeout: int,
    auth_headers: dict[str, str] | None = None,
) -> set[str]:
    parsed = urlparse(start_url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    auth_headers = auth_headers or {}
    discovered: set[str] = set()
    for suffix in ("/feed", "/rss", "/atom.xml", "/feed.xml"):
        feed_url = _normalize_url(root + suffix)
        st, ct, body = _fetch(feed_url, max(4, int(timeout)), extra_headers=auth_headers)
        if not (200 <= st < 400):
            continue
        text = body or ""
        if not text:
            continue
        if "xml" not in ct.lower() and "<rss" not in text.lower() and "<feed" not in text.lower():
            continue
        for raw in _RSS_LINK_RE.findall(text):
            link = _normalize_url(raw)
            if _is_http_url(link) and _same_host(link, start_url):
                discovered.add(link)
    return discovered


def _normalize_relative_locale_href(base_url: str, href: str) -> str:
    """Fix locale-switcher relative links like `aws/ja` on `/aws/en/...` pages."""
    href = href.strip()
    if (
        not href
        or href.startswith(("#", "/", "http://", "https://", "mailto:", "tel:", "javascript:"))
    ):
        return href
    base_parts = [p for p in (urlparse(base_url).path or "/").split("/") if p]
    href_parts = [p for p in href.split("/") if p]
    if len(base_parts) >= 2 and len(href_parts) >= 2:
        base_provider = base_parts[0]
        if (
            _CLOUD_PROVIDER_PATTERN.match(base_provider)
            and _LOCALE_PATTERN.match(base_parts[1])
            and href_parts[0].lower() == base_provider.lower()
            and _LOCALE_PATTERN.match(href_parts[1])
        ):
            return "/" + "/".join(href_parts)
    return href


def _canonical_link_variants(url: str) -> list[str]:
    """Return canonical variants to validate suspicious broken links."""
    parsed = urlparse(url)
    path = parsed.path or "/"
    parts = [p for p in path.split("/") if p]
    candidates: list[str] = []

    def _add_path(new_path: str) -> None:
        if not new_path.startswith("/"):
            new_path = "/" + new_path
        if new_path != "/" and new_path.endswith("/"):
            new_path = new_path[:-1]
        candidate = urlunparse(parsed._replace(path=new_path, query="", fragment=""))
        candidate = _normalize_url(candidate)
        if candidate not in candidates:
            candidates.append(candidate)

    _add_path(path)

    # index.html variations
    if path.lower().endswith("/index.html"):
        _add_path(path[:-len("/index.html")] or "/")
    elif path.lower().endswith("index.html"):
        _add_path(path[:-len("index.html")] or "/")

    # Trailing slash toggles (when path looks like a section, not a file)
    has_ext = bool(re.search(r"/[^/]+\.[a-z0-9]{1,6}$", path.lower()))
    if not has_ext and path != "/":
        _add_path(path + "/")
        _add_path(path.rstrip("/"))

    # Provider/locale crossover variants: /aws/en/gcp/en/... -> test both prefixes.
    if len(parts) >= 4 and _LOCALE_PATTERN.match(parts[1]) and _LOCALE_PATTERN.match(parts[3]):
        if _CLOUD_PROVIDER_PATTERN.match(parts[0]) and _CLOUD_PROVIDER_PATTERN.match(parts[2]):
            rest = parts[4:]
            _add_path("/".join([parts[0], parts[1], *rest]))
            _add_path("/".join([parts[2], parts[3], *rest]))

    return candidates


def _is_http_url(raw: str) -> bool:
    try:
        parsed = urlparse(raw)
    except (ValueError, TypeError) as exc:  # noqa: BLE001
        logger.debug("URL parse failed for '%s': %s", raw, exc)
        return False
    if parsed.scheme not in {"http", "https"}:
        return False
    if not parsed.netloc:
        return False
    if any(ch.isspace() for ch in parsed.netloc):
        return False
    try:
        _ = parsed.port
    except (ValueError, TypeError):
        return False
    hostname = parsed.hostname or ""
    if not hostname:
        return False
    if any(ch.isspace() for ch in hostname):
        return False
    return True


def _same_host(a: str, b: str) -> bool:
    return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()


def _safe_pct(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def _deterministic_link_sample(urls: set[str], limit: int) -> set[str]:
    """Return a deterministic uniform sample of URLs up to *limit* size."""
    if limit <= 0 or len(urls) <= limit:
        return set(urls)
    ranked = sorted(
        urls,
        key=lambda u: hashlib.sha1(u.encode("utf-8", errors="ignore")).hexdigest(),
    )
    return set(ranked[:limit])


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


def _fetch(
    url: str,
    timeout: int,
    head_only: bool = False,
    _ua_idx: int = 0,
    extra_headers: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    if not _is_http_url(url):
        return 0, "", ""
    url = _sanitize_url(url)
    ua = _USER_AGENTS[min(_ua_idx, len(_USER_AGENTS) - 1)]
    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if extra_headers:
        for k, v in extra_headers.items():
            if str(k).strip() and str(v).strip():
                headers[str(k)] = str(v)
    req = Request(
        url=url,
        method="HEAD" if head_only else "GET",
        headers=headers,
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            status = int(getattr(resp, "status", 200) or 200)
            content_type = str(resp.headers.get("Content-Type", ""))
            if head_only:
                return status, content_type, ""
            raw = resp.read()
            # Handle gzip payloads in a robust way:
            # - explicit *.gz URLs,
            # - gzip content-encoding headers,
            # - raw gzip magic bytes (some sites omit headers).
            is_gzip_payload = (
                url.lower().endswith(".gz")
                or str(resp.headers.get("Content-Encoding", "")).lower() == "gzip"
                or raw[:2] == b"\x1f\x8b"
            )
            if is_gzip_payload:
                try:
                    raw = gzip.decompress(raw)
                except (OSError, EOFError, ValueError) as exc:
                    logger.debug("Failed to decompress gzip payload for %s: %s", url, exc)
            body = raw.decode("utf-8", errors="ignore")
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
                    return _fetch(location, timeout, head_only=False, _ua_idx=_ua_idx, extra_headers=extra_headers)
                except (RuntimeError, ValueError, TypeError, OSError) as redir_exc:  # noqa: BLE001
                    logger.debug(
                        "Redirect fetch failed for %s: %s", location, redir_exc,
                    )
            return code, "text/html", ""
        try:
            return code, "text/html", exc.read().decode("utf-8", errors="ignore")
        except (RuntimeError, ValueError, TypeError, OSError) as read_exc:  # noqa: BLE001
            logger.debug("Failed to read HTTP error body (code=%d): %s", code, read_exc)
            return code, "text/html", ""
    except (URLError, OSError, TimeoutError):
        return 0, "", ""
    except (RuntimeError, ValueError, TypeError, OSError) as exc:  # noqa: BLE001 -- SSL, socket, redirect loops, etc.
        logger.debug("Unexpected fetch error: %s", exc)
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
        self._text_chars = 0
        self.last_updated_hint = ""

        self._in_title = False
        self._in_code = False
        self._in_pre = False
        self._in_highlight_div = 0  # nesting counter for highlight wrappers
        self._code_lang = ""
        self._code_buf: list[str] = []
        self._code_buf_chars = 0
        self._date_class_detected = False

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
                href = _normalize_relative_locale_href(self.base_url, href)
                absolute = _safe_join_normalize_url(self.base_url, href)
                if _is_http_url(absolute):
                    if _same_host(absolute, self.base_url):
                        if len(self.internal_links) < _MAX_LINKS_PER_PAGE:
                            self.internal_links.append(absolute)
                    else:
                        if len(self.external_links) < _MAX_LINKS_PER_PAGE:
                            self.external_links.append(absolute)
            return

        if tag == "pre":
            self._in_pre = True
            self._code_lang = ""
            self._code_buf = []
            self._code_buf_chars = 0
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
                # Date text may be emitted in a nested node; track context.
                self._date_class_detected = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
            return
        if tag == "code":
            # If <code> was standalone (not inside <pre>) but had language class
            # and accumulated content, treat as code block
            if not self._in_pre and self._code_buf:
                code = "".join(self._code_buf).strip()
                if len(code) > _MAX_CODE_BLOCK_CHARS:
                    code = code[:_MAX_CODE_BLOCK_CHARS]
                if code and self._code_lang and len(self.code_blocks) < _MAX_CODE_BLOCKS_PER_PAGE:
                    self.code_blocks.append({"language": self._code_lang, "code": code})
                self._code_buf = []
                self._code_buf_chars = 0
            self._in_code = False
            return
        if tag == "pre":
            self._in_pre = False
            code = "".join(self._code_buf).strip()
            if len(code) > _MAX_CODE_BLOCK_CHARS:
                code = code[:_MAX_CODE_BLOCK_CHARS]
            if code and not self._is_line_numbers_only(code) and len(self.code_blocks) < _MAX_CODE_BLOCKS_PER_PAGE:
                self.code_blocks.append({"language": self._code_lang or "text", "code": code})
            self._code_buf = []
            self._code_buf_chars = 0
            self._code_lang = ""
            return
        if tag == "div" and self._in_highlight_div > 0:
            self._in_highlight_div -= 1
            # Flush accumulated code when outermost highlight div closes
            # (only if not already flushed by a nested <pre> end)
            if self._in_highlight_div == 0 and not self._in_pre and not self._in_code and self._code_buf:
                code = "".join(self._code_buf).strip()
                if len(code) > _MAX_CODE_BLOCK_CHARS:
                    code = code[:_MAX_CODE_BLOCK_CHARS]
                if code and len(self.code_blocks) < _MAX_CODE_BLOCKS_PER_PAGE:
                    self.code_blocks.append({"language": self._code_lang or "text", "code": code})
                self._code_buf = []
                self._code_buf_chars = 0
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
            if self._code_buf_chars < _MAX_CODE_BUFFER_CHARS:
                remaining = _MAX_CODE_BUFFER_CHARS - self._code_buf_chars
                piece = data[:remaining]
                if piece:
                    self._code_buf.append(piece)
                    self._code_buf_chars += len(piece)
        elif self._in_highlight_div > 0:
            if self._code_buf_chars < _MAX_CODE_BUFFER_CHARS:
                remaining = _MAX_CODE_BUFFER_CHARS - self._code_buf_chars
                piece = data[:remaining]
                if piece:
                    self._code_buf.append(piece)
                    self._code_buf_chars += len(piece)

        text = data.strip()
        if not text:
            return
        if self._in_title and not self.title:
            self.title = text
        if (
            len(self.text_chunks) < _MAX_TEXT_CHUNKS_PER_PAGE
            and self._text_chars < _MAX_TEXT_CHARS_PER_PAGE
        ):
            remaining = _MAX_TEXT_CHARS_PER_PAGE - self._text_chars
            clipped = text[:remaining]
            if clipped:
                self.text_chunks.append(clipped)
                self._text_chars += len(clipped)
        # Detect last-updated from text content
        if not self.last_updated_hint:
            if self._date_class_detected and _DATE_PATTERN.search(text):
                self.last_updated_hint = text
                self._date_class_detected = False
                return
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
                self.last_updated_hint = text

    def as_page(self, url: str, status: int) -> PageData:
        # Deduplicate code blocks (MkDocs Material tabs often repeat same content)
        seen: set[str] = set()
        unique_blocks: list[dict[str, str]] = []
        for block in self.code_blocks:
            key = block.get("code", "").strip()
            if key and key not in seen:
                seen.add(key)
                unique_blocks.append(block)
                if len(unique_blocks) >= _MAX_CODE_BLOCKS_PER_PAGE:
                    break
        try:
            text_value = " ".join(self.text_chunks)
        except MemoryError:
            # Fallback for pathological pages on constrained hosts.
            text_value = " ".join(self.text_chunks[:1000])
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
            text=text_value,
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
    r"(?:^|[\/._-])("
    r"api|apis|reference|references|endpoint|endpoints|method|methods|operation|operations|"
    r"resource|resources|rest|graphql|graphiql|grpc|proto|protobuf|asyncapi|event|events|"
    r"websocket|web-socket|ws|rpc|sdk|swagger|openapi|redoc|postman|schema|spec|specs"
    r")(?:$|[\/._-])",
    flags=re.IGNORECASE,
)

# Content-based heuristics: HTTP methods, status codes, request/response blocks
_API_SIGNAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+/[a-z0-9]", flags=re.IGNORECASE),
    re.compile(r"\bHTTP/[12]\.\d\b", flags=re.IGNORECASE),
    re.compile(r"\b(?:[2345]\d{2})\b", flags=re.IGNORECASE),
    re.compile(r"\bcurl\s", flags=re.IGNORECASE),
    re.compile(r"\bRequest\s+body\b|\bResponse\s+body\b", flags=re.IGNORECASE),
    re.compile(r"\bapplication/json\b|\bContent-Type:\s|\bAuthorization:\s", flags=re.IGNORECASE),
    re.compile(r"\bopenapi\s*:\s*3|\bswagger\s*:\s*['\"]?2", flags=re.IGNORECASE),
    re.compile(r"\boperationId\s*[:=]\s*['\"]?[a-z_][a-z0-9_.-]*", flags=re.IGNORECASE),
    re.compile(r"\bquery\s+[A-Za-z_][A-Za-z0-9_]*|\bmutation\s+[A-Za-z_][A-Za-z0-9_]*|\bsubscription\s+[A-Za-z_][A-Za-z0-9_]*", flags=re.IGNORECASE),
    re.compile(r"\btype\s+Query\b|\btype\s+Mutation\b|\b__schema\b|\bgraphql\b", flags=re.IGNORECASE),
    re.compile(r"\bsyntax\s*=\s*['\"]proto3['\"]|\bservice\s+[A-Za-z_][A-Za-z0-9_]*\s*\{|\brpc\s+[A-Za-z_][A-Za-z0-9_]*\s*\(", flags=re.IGNORECASE),
    re.compile(r"\basyncapi\s*:\s*[0-9]|\bchannels\s*:\s|\bpublish\s*:\s|\bsubscribe\s*:\s", flags=re.IGNORECASE),
    re.compile(r"\bwebsocket\b|\bws://|\bwss://|\bevent\s+payload\b", flags=re.IGNORECASE),
    re.compile(r"\bjsonrpc\b\s*:\s*['\"]2\.0['\"]", flags=re.IGNORECASE),
)

_OPERATION_ID_PATTERN = re.compile(
    r"\boperationId\s*[:=]\s*['\"]?([A-Za-z_][A-Za-z0-9_.-]*)",
    flags=re.IGNORECASE,
)
_RPC_PATTERN = re.compile(r"\brpc\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", flags=re.IGNORECASE)
_GQL_OPERATION_PATTERN = re.compile(
    r"\b(?:query|mutation|subscription)\s+([A-Za-z_][A-Za-z0-9_]*)",
    flags=re.IGNORECASE,
)
_ASYNC_CHANNEL_PATTERN = re.compile(
    r"(?im)^\s*([A-Za-z0-9_./{}-]+)\s*:\s*(?:\n\s+(?:publish|subscribe)\s*:)",
    flags=re.MULTILINE,
)
_WEBSOCKET_EVENT_PATTERN = re.compile(
    r"\b(?:event|topic|channel)\s*[:=]\s*['\"]?([A-Za-z0-9_./:-]+)",
    flags=re.IGNORECASE,
)
_METHOD_PATH_PATTERN = re.compile(
    r"\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+"
    r"(/(?:[a-z0-9._~!$&'()*+,;=:@%-]+|\{[a-z0-9._~-]+\})"
    r"(?:/(?:[a-z0-9._~!$&'()*+,;=:@%-]+|\{[a-z0-9._~-]+\}))*)",
    flags=re.IGNORECASE,
)


def _api_signal_score(text: str) -> int:
    score = 0
    for pattern in _API_SIGNAL_PATTERNS:
        if pattern.search(text):
            score += 1
    return score


def _extract_api_identifiers(text: str) -> set[str]:
    identifiers: set[str] = set()
    for match in ENDPOINT_PATTERN.findall(text.lower()):
        cleaned = str(match).strip().rstrip(".,;:)]}\"'")
        if cleaned and cleaned.count("/") >= 1 and len(cleaned) > 3:
            identifiers.add(f"ep:{cleaned}")
    for match in _METHOD_PATH_PATTERN.findall(text):
        cleaned = str(match).lower().strip().rstrip(".,;:)]}\"'")
        if cleaned:
            identifiers.add(f"ep:{cleaned}")
    for match in _OPERATION_ID_PATTERN.findall(text):
        cleaned = str(match).lower().strip()
        if cleaned:
            identifiers.add(f"op:{cleaned}")
    for match in _RPC_PATTERN.findall(text):
        cleaned = str(match).lower().strip()
        if cleaned:
            identifiers.add(f"rpc:{cleaned}")
    for match in _GQL_OPERATION_PATTERN.findall(text):
        cleaned = str(match).lower().strip()
        if cleaned:
            identifiers.add(f"gql:{cleaned}")
    for match in _ASYNC_CHANNEL_PATTERN.findall(text):
        cleaned = str(match).lower().strip()
        if cleaned:
            identifiers.add(f"ch:{cleaned}")
    for match in _WEBSOCKET_EVENT_PATTERN.findall(text):
        cleaned = str(match).lower().strip()
        if cleaned:
            identifiers.add(f"ev:{cleaned}")
    return identifiers


def _is_api_page(page: PageData) -> bool:
    """Detect API reference pages via URL patterns AND content heuristics."""
    # URL-based detection (expanded patterns)
    if _API_URL_PATTERN.search(page.url):
        return True
    # Content-based detection: independent signal types (protocol-agnostic)
    text_sample = page.text[:5000]
    code_sample = " ".join(b.get("code", "") for b in page.code_blocks[:10])
    combined = text_sample + " " + code_sample
    return _api_signal_score(combined) >= 2


def _discover_contract_urls(pages: list[PageData]) -> list[str]:
    pattern = re.compile(
        r"(openapi|swagger|api-docs|graphql|schema|asyncapi|\.proto|protobuf|descriptor)",
        flags=re.IGNORECASE,
    )
    urls: list[str] = []
    for page in pages:
        for link in page.internal_links:
            if pattern.search(link):
                norm = _normalize_url(link)
                if norm and _is_http_url(norm) and norm not in urls:
                    urls.append(norm)
        for match in re.findall(r"https?://[^\s)\"'>]+", page.text):
            if pattern.search(match):
                norm = _normalize_url(match)
                if norm and _is_http_url(norm) and norm not in urls:
                    urls.append(norm)
        parsed = urlparse(page.url)
        root = f"{parsed.scheme}://{parsed.netloc}"
        for suffix in _CONTRACT_PATH_CANDIDATES:
            candidate = _normalize_url(root + suffix)
            if candidate and _is_http_url(candidate) and candidate not in urls:
                urls.append(candidate)
    return urls[:120]


def _extract_contract_identifiers(contract_text: str) -> set[str]:
    ids: set[str] = set()
    # OpenAPI/Swagger paths
    for m in re.findall(r"\"(/[^\"\\s]+)\"\\s*:\\s*\\{", contract_text):
        ids.add(f"ep:{m.lower()}")
    for m in re.findall(r"(?m)^\\s{0,8}(/[^:\\s]+)\\s*:\\s*$", contract_text):
        if "/" in m:
            ids.add(f"ep:{m.lower()}")
    for m in _OPERATION_ID_PATTERN.findall(contract_text):
        ids.add(f"op:{m.lower()}")
    for m in _RPC_PATTERN.findall(contract_text):
        ids.add(f"rpc:{m.lower()}")
    for m in _GQL_OPERATION_PATTERN.findall(contract_text):
        ids.add(f"gql:{m.lower()}")
    for m in _ASYNC_CHANNEL_PATTERN.findall(contract_text):
        ids.add(f"ch:{str(m).lower()}")
    for m in _WEBSOCKET_EVENT_PATTERN.findall(contract_text):
        ids.add(f"ev:{str(m).lower()}")
    return ids


def _parse_structured_contract_identifiers(contract_text: str) -> set[str]:
    ids: set[str] = set()
    payload: Any = None
    stripped = contract_text.strip()
    if not stripped:
        return ids
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        if yaml is not None:
            try:
                payload = yaml.safe_load(stripped)
            except (AttributeError, TypeError, ValueError):
                payload = None
    if not isinstance(payload, dict):
        return ids

    paths = payload.get("paths")
    if isinstance(paths, dict):
        for pth, pdef in paths.items():
            if isinstance(pth, str):
                ids.add(f"ep:{pth.lower()}")
            if isinstance(pdef, dict):
                for _, op in pdef.items():
                    if isinstance(op, dict):
                        op_id = op.get("operationId")
                        if isinstance(op_id, str) and op_id.strip():
                            ids.add(f"op:{op_id.lower().strip()}")

    channels = payload.get("channels")
    if isinstance(channels, dict):
        for ch in channels.keys():
            if isinstance(ch, str):
                ids.add(f"ch:{ch.lower()}")

    data = payload.get("data")
    if isinstance(data, dict):
        schema = data.get("__schema")
        if isinstance(schema, dict):
            query_type = schema.get("queryType")
            mutation_type = schema.get("mutationType")
            if isinstance(query_type, dict) and isinstance(query_type.get("name"), str):
                ids.add(f"gql:{query_type['name'].lower()}")
            if isinstance(mutation_type, dict) and isinstance(mutation_type.get("name"), str):
                ids.add(f"gql:{mutation_type['name'].lower()}")

    services = payload.get("services")
    if isinstance(services, list):
        for svc in services:
            if isinstance(svc, dict):
                methods = svc.get("methods")
                if isinstance(methods, list):
                    for method in methods:
                        if isinstance(method, dict) and isinstance(method.get("name"), str):
                            ids.add(f"rpc:{method['name'].lower()}")
    return ids


def _source_of_truth_identifiers(
    pages: list[PageData],
    timeout: int,
    auth_headers: dict[str, str] | None = None,
) -> tuple[set[str], str]:
    candidates = _discover_contract_urls(pages)
    if not candidates:
        return set(), "No contract URLs discovered in crawled pages"
    ids: set[str] = set()
    for url in candidates:
        if not url or not _is_http_url(url):
            continue
        st, ct, body = _fetch(url, max(4, int(timeout)), extra_headers=auth_headers or {})
        if st < 200 or st >= 400:
            continue
        text = body or ""
        if not text and "json" not in ct.lower() and "yaml" not in ct.lower() and "text" not in ct.lower():
            continue
        ids.update(_parse_structured_contract_identifiers(text))
        ids.update(_extract_contract_identifiers(text))
    if not ids:
        return set(), "Contract URLs found but no operations parsed"
    return ids, ""


def _api_coverage_from_public_docs(
    pages: list[PageData],
    timeout: int = 15,
    auth_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    reference_ids: set[str] = set()
    non_reference_ids: set[str] = set()

    api_page_count = 0
    for page in pages:
        is_api = _is_api_page(page)
        if is_api:
            api_page_count += 1
        bucket = reference_ids if is_api else non_reference_ids
        sources = [page.text] + [block.get("code", "") for block in page.code_blocks]
        for src in sources:
            bucket.update(_extract_api_identifiers(src))

    source_ids, source_note = _source_of_truth_identifiers(
        pages=pages,
        timeout=int(timeout),
        auth_headers=auth_headers or {},
    )
    coverage_method = "heuristic"
    if source_ids:
        reference_ids = source_ids
        coverage_method = "source_of_truth"

    total_ref = len(reference_ids)
    matched = len(reference_ids & non_reference_ids)
    uncovered = max(0, total_ref - matched)
    no_identifiers = total_ref == 0 and api_page_count > 0
    detection_note = ""
    if no_identifiers:
        detection_note = (
            "API-like pages were detected, but no endpoint or operation "
            "identifiers could be extracted. Coverage is shown as N/A."
        )
    if source_note:
        detection_note = (detection_note + " " + source_note).strip()

    return {
        "reference_endpoint_count": total_ref,
        "api_pages_detected": api_page_count,
        "endpoints_with_usage_docs": matched,
        "reference_endpoints_without_usage_docs": uncovered,
        "reference_coverage_pct": _safe_pct(matched, total_ref) if total_ref > 0 else -1.0,
        "no_api_pages_found": total_ref == 0 and api_page_count == 0,
        "coverage_determined": total_ref > 0,
        "coverage_method": coverage_method,
        "detection_note": detection_note,
        "uncovered_endpoint_samples": sorted(list(reference_ids - non_reference_ids))[:20],
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


def _is_excluded_link(url: str) -> bool:
    """Return True for internal URLs outside documentation page scope."""
    parsed = urlparse(url)
    path = (parsed.path or "/").lower()
    if any(path.endswith(ext) for ext in _EXCLUDED_PATH_EXTENSIONS):
        return True
    if any(seg in path for seg in _EXCLUDED_PATH_SEGMENTS):
        return True
    if path.startswith("/api/") and ("openapi" not in path and "swagger" not in path):
        return True
    return False


def _link_health(pages: list[PageData], status_map: dict[str, int]) -> dict[str, Any]:
    internal_links = set()
    for page in pages:
        internal_links.update(page.internal_links)
    # Count only confirmed broken links; treat transient/auth/rate-limit statuses as unverified.
    broken = []
    unverified = []
    excluded = []
    for url in sorted(internal_links):
        if _is_excluded_link(url):
            excluded.append(url)
            continue
        st = int(status_map.get(url, 0) or 0)
        if st in _INCONCLUSIVE_HTTP_STATUSES:
            unverified.append(url)
            continue
        if st >= 400:
            broken.append(url)
    unreachable = [url for url in sorted(internal_links) if status_map.get(url, 0) == 0]
    # Separate docs-site broken links from repository navigation broken links
    docs_broken = [u for u in broken if not _is_repo_link(u)]
    repo_broken = [u for u in broken if _is_repo_link(u)]
    docs_unverified = [u for u in unverified if not _is_repo_link(u)]
    repo_unverified = [u for u in unverified if _is_repo_link(u)]
    return {
        "internal_links_checked": len(internal_links),
        "broken_internal_links_count": len(broken),
        "docs_broken_links_count": len(docs_broken),
        "repo_broken_links_count": len(repo_broken),
        "broken_internal_link_samples": docs_broken[:20] + repo_broken[:10],
        "docs_broken_link_samples": docs_broken[:30],
        "repo_broken_link_samples": repo_broken[:30],
        "unreachable_links_count": len(unreachable),
        "unverified_links_count": len(unverified),
        "unverified_link_samples": unverified[:30],
        "confirmed_broken_links_count": len(broken),
        "excluded_links_count": len(excluded),
        "excluded_link_samples": excluded[:30],
        "_all_confirmed_broken_links": broken,
        "_all_unverified_links": unverified,
        "_all_excluded_links": excluded,
        "_all_docs_unverified_links": docs_unverified,
        "_all_repo_unverified_links": repo_unverified,
    }


def _last_updated_metrics(pages: list[PageData]) -> dict[str, Any]:
    with_hint = [p for p in pages if p.last_updated_hint.strip()]
    return {
        "pages_with_last_updated_hint": len(with_hint),
        "pages_without_last_updated_hint": len(pages) - len(with_hint),
        "last_updated_coverage_pct": _safe_pct(len(with_hint), len(pages)),
        "samples_with_last_updated": [{"url": p.url, "hint": p.last_updated_hint[:120]} for p in with_hint[:10]],
    }


def _browser_verify_links(
    urls: list[str],
    timeout: int,
    auth_headers: dict[str, str] | None = None,
    storage_state_path: str = "",
) -> dict[str, int]:
    """Best-effort browser verification using Playwright if available."""
    if not urls:
        return {}
    try:
        from playwright.sync_api import Error as PlaywrightError  # type: ignore
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        return {}
    result: dict[str, int] = {}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            kwargs: dict[str, Any] = {}
            if auth_headers:
                kwargs["extra_http_headers"] = auth_headers
            if storage_state_path and Path(storage_state_path).exists():
                kwargs["storage_state"] = storage_state_path
            context = browser.new_context(**kwargs)
            page = context.new_page()
            page.set_default_navigation_timeout(max(1000, int(timeout * 1000)))
            for url in urls:
                try:
                    resp = page.goto(url, wait_until="domcontentloaded")
                    status = int(resp.status) if resp is not None else 0
                except (PlaywrightError, OSError, RuntimeError, ValueError, TypeError):
                    status = 0
                result[url] = status
            context.close()
            browser.close()
    except (PlaywrightError, OSError, RuntimeError, ValueError, TypeError):
        return {}
    return result


def _browser_discover_pages(
    start_url: str,
    max_pages: int,
    timeout: int,
    auth_headers: dict[str, str] | None = None,
    storage_state_path: str = "",
) -> tuple[list[PageData], dict[str, int]]:
    """Discover pages via browser rendering for JS-heavy docs."""
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        return [], {}

    auth_headers = auth_headers or {}
    seen: set[str] = set()
    queue: deque[str] = deque([start_url])
    pages: list[PageData] = []
    status_map: dict[str, int] = {}
    host = urlparse(start_url).netloc.lower()

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            kwargs: dict[str, Any] = {}
            if auth_headers:
                kwargs["extra_http_headers"] = auth_headers
            if storage_state_path and Path(storage_state_path).exists():
                kwargs["storage_state"] = storage_state_path
            context = browser.new_context(**kwargs)
            page = context.new_page()
            page.set_default_navigation_timeout(max(1500, int(timeout * 1000)))

            while queue and len(seen) < max_pages:
                url = _normalize_url(queue.popleft())
                if url in seen:
                    continue
                seen.add(url)
                try:
                    resp = page.goto(url, wait_until="domcontentloaded")
                    st = int(resp.status) if resp is not None else 0
                    status_map[url] = st
                    if st < 200 or st >= 400:
                        continue
                    html_body = page.content()
                    parser_html = _DocsHTMLParser(url)
                    parser_html.feed(html_body)
                    parsed = parser_html.as_page(url, st)
                    pages.append(parsed)
                    for link in parsed.internal_links:
                        if urlparse(link).netloc.lower() == host and link not in seen and len(queue) < max_pages * 3:
                            queue.append(link)
                except (RuntimeError, ValueError, TypeError):
                    status_map[url] = 0
            context.close()
            browser.close()
    except (RuntimeError, ValueError, TypeError):
        return [], {}
    return pages, status_map


def _ensure_playwright_storage_state(
    *,
    storage_state_path: str,
    login_url: str,
    username: str,
    password: str,
    username_selector: str,
    password_selector: str,
    submit_selector: str,
    success_wait_url_pattern: str,
    timeout: int,
    auth_headers: dict[str, str] | None = None,
) -> str:
    """Create Playwright storage state by logging in once, if needed."""
    if not storage_state_path:
        return ""
    state_path = _resolve_cross_platform_path(Path(storage_state_path))
    if state_path.exists():
        return str(state_path)
    if not (login_url and username and password and username_selector and password_selector and submit_selector):
        return ""
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        return ""

    state_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            kwargs: dict[str, Any] = {}
            if auth_headers:
                kwargs["extra_http_headers"] = auth_headers
            context = browser.new_context(**kwargs)
            page = context.new_page()
            page.set_default_navigation_timeout(max(1500, int(timeout * 1000)))
            page.goto(login_url, wait_until="domcontentloaded")
            page.fill(username_selector, username)
            page.fill(password_selector, password)
            page.click(submit_selector)
            if success_wait_url_pattern.strip():
                page.wait_for_url(re.compile(success_wait_url_pattern), timeout=max(3000, int(timeout * 1000)))
            else:
                page.wait_for_load_state("networkidle", timeout=max(3000, int(timeout * 1000)))
            context.storage_state(path=str(state_path))
            context.close()
            browser.close()
        return str(state_path)
    except (RuntimeError, ValueError, TypeError):
        return ""


def _cookie_header_from_storage_state(storage_state_path: str, target_host: str) -> str:
    if not storage_state_path:
        return ""
    p = _resolve_cross_platform_path(Path(storage_state_path))
    if not p.exists():
        return ""
    try:
        payload = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
    except (json.JSONDecodeError, OSError, TypeError):
        return ""
    cookies = payload.get("cookies", []) if isinstance(payload, dict) else []
    if not isinstance(cookies, list):
        return ""
    host = target_host.lower()
    pairs: list[str] = []
    for c in cookies:
        if not isinstance(c, dict):
            continue
        domain = str(c.get("domain", "")).lstrip(".").lower()
        if not domain:
            continue
        if host != domain and not host.endswith("." + domain):
            continue
        name = str(c.get("name", "")).strip()
        value = str(c.get("value", "")).strip()
        if name and value:
            pairs.append(f"{name}={value}")
    return "; ".join(pairs)


def _crawl_site(
    start_url: str,
    max_pages: int,
    timeout: int,
    verification_modes: set[str] | None = None,
    auth_headers: dict[str, str] | None = None,
    browser_verify_sample: int = 100,
    browser_discovery_pages: int = 300,
    storage_state_path: str = "",
    crawl_convergence_rounds: int = 8,
    crawl_batch_size: int = 60,
    auto_max_pages: int = 100000,
    return_stats: bool = False,
) -> tuple[list[PageData], dict[str, int]] | tuple[list[PageData], dict[str, int], dict[str, Any]]:
    """Crawl *start_url* up to *max_pages* with parallel BFS + parallel link check.

    If the first attempt yields zero pages (site blocks requests), automatically
    retries with alternative User-Agent strings before giving up.
    """

    max_pages = int(max_pages)
    timeout = int(timeout)
    auto_mode = max_pages <= 0
    effective_limit = max_pages if max_pages > 0 else max(200, int(auto_max_pages))
    workers = min(max(1, effective_limit), 10)  # parallel crawl workers
    batch_size = max(10, int(crawl_batch_size))
    convergence_rounds = max(2, int(crawl_convergence_rounds))

    verification_modes = verification_modes or {"bot"}
    auth_headers = auth_headers or {}
    trap_urls_skipped = 0
    seeded_sitemap_urls = 0
    robots_sitemaps = 0
    stop_reason = "limit_reached" if not auto_mode else "converged"

    # Try up to len(_USER_AGENTS) User-Agent variants for the start page
    for ua_attempt in range(len(_USER_AGENTS)):
        seen: set[str] = set()
        pages: list[PageData] = []
        status_map: dict[str, int] = {}
        discovered: set[str] = {start_url}
        seed_urls: set[str] = {start_url}
        sitemap_urls, robot_count = _discover_seed_urls_from_sitemaps(
            start_url=start_url,
            timeout=timeout,
            auth_headers=auth_headers,
        )
        feed_urls = _discover_seed_urls_from_feeds(
            start_url=start_url,
            timeout=timeout,
            auth_headers=auth_headers,
        )
        seed_urls.update(sitemap_urls)
        seed_urls.update(feed_urls)
        seeded_sitemap_urls = len(sitemap_urls)
        robots_sitemaps = robot_count
        # If sitemap is available, treat it as authoritative crawl scope.
        # This prevents crawl-trap inflation and keeps coverage meaningful.
        sitemap_scope = len(sitemap_urls) > 0
        queue: deque[str] = deque(sorted(seed_urls))
        discovered.update(seed_urls)
        rounds_without_new = 0
        prior_crawled = 0
        progress_total = min(effective_limit, len(seed_urls)) if sitemap_scope else effective_limit

        if ua_attempt > 0:
            print("[audit] retry with alternative User-Agent ({}/{})...".format(
                ua_attempt + 1, len(_USER_AGENTS)), flush=True)
        else:
            if auto_mode:
                print(
                    "[audit] auto-crawl enabled: until convergence (cap={}, {} workers)...".format(
                        effective_limit, workers,
                    ),
                    flush=True,
                )
            else:
                print("[audit] crawling up to {} pages ({} workers)...".format(max_pages, workers), flush=True)

        def _crawl_one(url: str, _ua: int = ua_attempt) -> tuple[str, int, PageData | None, list[str]]:
            """Fetch + parse one page.  Returns (url, status, page_or_None, new_links)."""
            st, ct, body = _fetch(url, timeout, _ua_idx=_ua, extra_headers=auth_headers)
            if st < 200 or st >= 400 or "html" not in ct.lower():
                return url, st, None, []
            parser_html = _DocsHTMLParser(url)
            try:
                parser_html.feed(body)
            except (RuntimeError, ValueError, TypeError, OSError):  # noqa: BLE001
                # Never fail the whole crawl due to one malformed page.
                return url, st, None, []
            page = parser_html.as_page(url, st)
            return url, st, page, page.internal_links

        with ThreadPoolExecutor(max_workers=workers) as pool:
            while queue and len(seen) < effective_limit:
                # Submit a batch of URLs (up to remaining budget)
                batch: list[str] = []
                round_discovered_before = len(discovered)
                while queue and len(seen) + len(batch) < effective_limit and len(batch) < batch_size:
                    candidate = queue.popleft()
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
                        print("[audit] page {}/{}: {}".format(len(pages), progress_total, url[:80]), flush=True)
                        for link in new_links:
                            if not _is_http_url(link):
                                continue
                            if not _same_host(link, start_url):
                                continue
                            if _is_probable_crawl_trap(link):
                                trap_urls_skipped += 1
                                continue
                            # In sitemap-scoped mode, keep crawl strictly within sitemap/feed seeds.
                            if sitemap_scope and link not in seed_urls:
                                continue
                            if link not in discovered:
                                discovered.add(link)
                                if len(seen) + len(queue) < effective_limit * 2:
                                    queue.append(link)

                if auto_mode:
                    found_new = len(discovered) > round_discovered_before
                    crawled_new = len(pages) > prior_crawled
                    if found_new or crawled_new:
                        rounds_without_new = 0
                    else:
                        rounds_without_new += 1
                    prior_crawled = len(pages)
                    if rounds_without_new >= convergence_rounds:
                        stop_reason = "converged"
                        break
            else:
                # Loop finished without break.
                if not auto_mode and not queue:
                    stop_reason = "queue_exhausted"
                else:
                    stop_reason = "limit_reached"

        # If we got at least 1 page, stop retrying
        if pages:
            if not auto_mode and len(seen) >= effective_limit:
                stop_reason = "limit_reached"
            elif not auto_mode and not queue:
                stop_reason = "queue_exhausted"
            elif auto_mode and not queue:
                stop_reason = "queue_exhausted"
            break
        # Log what happened with the start URL
        start_status = status_map.get(start_url, 0)
        print("[warn] 0 pages fetched (start URL status={}). ".format(start_status), end="", flush=True)
        if ua_attempt < len(_USER_AGENTS) - 1:
            print("Retrying...", flush=True)
        else:
            print("All User-Agent variants exhausted.", flush=True)

    # Browser discovery pass to include JS-rendered docs pages.
    if "browser" in verification_modes and int(browser_discovery_pages) > 0:
        b_pages, b_status = _browser_discover_pages(
            start_url=start_url,
            max_pages=min(effective_limit, int(browser_discovery_pages)),
            timeout=max(6, timeout),
            auth_headers=auth_headers,
            storage_state_path=storage_state_path,
        )
        if b_pages:
            by_url = {p.url: p for p in pages}
            for p in b_pages:
                by_url[p.url] = p
            pages = list(by_url.values())
            for u, st in b_status.items():
                if u not in status_map or status_map.get(u, 0) in {0, -2}:
                    status_map[u] = st

    # -- Parallel link-health check (HEAD-only, short timeout, 50 workers) ------
    link_timeout = min(timeout, 3)
    link_workers = 50
    total_unchecked = 0
    unchecked: set[str] = set()
    for page in pages:
        for link in page.internal_links:
            if link not in status_map:
                unchecked.add(link)

    total_unchecked = len(unchecked)
    if total_unchecked > _MAX_LINK_HEALTH_CHECKS:
        unchecked = _deterministic_link_sample(unchecked, _MAX_LINK_HEALTH_CHECKS)
        print(
            "[audit] link-check sample mode: checking {}/{} unique links".format(
                len(unchecked),
                total_unchecked,
            ),
            flush=True,
        )

    if unchecked:
        done = 0
        total = len(unchecked)
        print("[audit] checking {} unique links ({} workers)...".format(total, link_workers), flush=True)

        def _check_one(link: str) -> tuple[str, int]:
            st, _, _ = _fetch(link, link_timeout, head_only=True, extra_headers=auth_headers)
            # Many SPA/SSG sites return 404 for HEAD but 200 for GET; retry
            if st >= 400 or st == 0:
                st2, _, _ = _fetch(link, link_timeout, extra_headers=auth_headers)
                if 200 <= st2 < 400:
                    st = st2
                else:
                    st = st2
            # Canonical variant validation: if original URL appears broken, try likely normalized paths.
            if st in {404, 410}:
                for candidate in _canonical_link_variants(link):
                    if candidate == _normalize_url(link):
                        continue
                    st3, _, _ = _fetch(candidate, link_timeout, extra_headers=auth_headers)
                    if 200 <= st3 < 400:
                        return link, 200
            # Authenticated fallback pass
            if st >= 400 and "authenticated" in verification_modes and auth_headers:
                st_auth, _, _ = _fetch(link, max(link_timeout, 8), extra_headers=auth_headers)
                if 200 <= st_auth < 400:
                    return link, 200
            # Treat transient/blocked statuses as inconclusive, not broken.
            if st in _INCONCLUSIVE_HTTP_STATUSES:
                return link, -2
            return link, st

        with ThreadPoolExecutor(max_workers=link_workers) as pool:
            futures = {pool.submit(_check_one, lnk): lnk for lnk in unchecked}
            for future in as_completed(futures):
                link, st = future.result()
                status_map[link] = st
                done += 1
                if done % 100 == 0 or done == total:
                    print("[audit] links: {}/{}".format(done, total), flush=True)

        # Browser verification pass for a sample of remaining broken candidates
        if "browser" in verification_modes:
            candidates = [
                link for link in sorted(unchecked)
                if int(status_map.get(link, 0) or 0) >= 400
            ][: max(0, int(browser_verify_sample))]
            if candidates:
                print("[audit] browser-verifying {} broken-link candidates...".format(len(candidates)), flush=True)
                browser_status = _browser_verify_links(
                    candidates,
                    timeout=max(6, timeout),
                    auth_headers=auth_headers,
                    storage_state_path=storage_state_path,
                )
                for link, st in browser_status.items():
                    if 200 <= int(st or 0) < 400:
                        status_map[link] = int(st)
                    elif int(st or 0) == 0:
                        status_map[link] = -2

    crawl_stats = {
        "auto_mode": auto_mode,
        "configured_max_pages": int(max_pages),
        "effective_limit": int(effective_limit),
        # Use crawl frontier discovery, not all in-page links, for coverage denominator.
        "discovered_pages": len(discovered),
        "urls_examined": len(seen),
        "pages_crawled": len(pages),
        "requested_pages": len(status_map),
        "stop_reason": stop_reason,
        "trap_urls_skipped": int(trap_urls_skipped),
        "seeded_sitemap_urls": int(seeded_sitemap_urls),
        "robots_sitemaps_declared": int(robots_sitemaps),
        "link_checks_total_candidates": int(total_unchecked),
        "link_checks_executed": int(len(unchecked)),
        "link_checks_sampled": bool(total_unchecked > len(unchecked)),
    }
    if return_stats:
        return pages, status_map, crawl_stats
    return pages, status_map


def _site_payload(
    site_url: str,
    max_pages: int,
    timeout: int,
    verification_modes: set[str] | None = None,
    auth_headers: dict[str, str] | None = None,
    browser_verify_sample: int = 100,
    browser_discovery_pages: int = 300,
    storage_state_path: str = "",
    crawl_convergence_rounds: int = 8,
    crawl_batch_size: int = 60,
    auto_max_pages: int = 100000,
) -> dict[str, Any]:
    crawl_result = _crawl_site(
        site_url,
        max_pages,
        timeout,
        verification_modes=verification_modes,
        auth_headers=auth_headers,
        browser_verify_sample=browser_verify_sample,
        browser_discovery_pages=browser_discovery_pages,
        storage_state_path=storage_state_path,
        crawl_convergence_rounds=crawl_convergence_rounds,
        crawl_batch_size=crawl_batch_size,
        auto_max_pages=auto_max_pages,
        return_stats=True,
    )
    if isinstance(crawl_result, tuple) and len(crawl_result) == 3:
        pages, status_map, crawl_stats = crawl_result
    else:
        pages, status_map = crawl_result  # type: ignore[misc]
        crawl_stats = {
            "auto_mode": int(max_pages) <= 0,
            "configured_max_pages": int(max_pages),
            "effective_limit": int(max_pages),
            # Legacy fallback path: count discovered pages by crawled page URLs only.
            # Including all in-page links here inflates denominator and breaks coverage.
            "discovered_pages": len({p.url for p in pages}),
            "urls_examined": len({p.url for p in pages}),
            "pages_crawled": len(pages),
            "requested_pages": len(status_map),
            "stop_reason": "unknown",
            "trap_urls_skipped": 0,
            "seeded_sitemap_urls": 0,
            "robots_sitemaps_declared": 0,
        }

    discovered_pages = int(crawl_stats.get("discovered_pages", 0) or 0)
    urls_examined = int(crawl_stats.get("urls_examined", len(status_map)) or 0)
    requested_pages = int(crawl_stats.get("requested_pages", len(status_map)) or 0)
    pages_crawled = int(crawl_stats.get("pages_crawled", len(pages)) or 0)
    seeded_sitemap_urls = int(crawl_stats.get("seeded_sitemap_urls", 0) or 0)
    scope_basis = "sitemap" if seeded_sitemap_urls > 0 else "discovered"
    scope_pages = seeded_sitemap_urls if seeded_sitemap_urls > 0 else discovered_pages
    metrics = {
        "crawl": {
            "pages_crawled": pages_crawled,
            "requested_pages": requested_pages,
            "urls_examined": urls_examined,
            "max_pages": int(max_pages),
            "effective_limit": int(crawl_stats.get("effective_limit", max_pages) or 0),
            "auto_mode": bool(crawl_stats.get("auto_mode", int(max_pages) <= 0)),
            "stop_reason": str(crawl_stats.get("stop_reason", "unknown")),
            "discovered_pages": discovered_pages,
            "crawl_scope_basis": scope_basis,
            "crawl_scope_pages": scope_pages,
            "crawl_coverage_pct": _safe_pct(urls_examined, scope_pages),
            "trap_urls_skipped": int(crawl_stats.get("trap_urls_skipped", 0) or 0),
            "seeded_sitemap_urls": seeded_sitemap_urls,
            "robots_sitemaps_declared": int(crawl_stats.get("robots_sitemaps_declared", 0) or 0),
        },
        "links": _link_health(pages, status_map),
        "seo_geo": _seo_geo_metrics(pages),
        "api_coverage": _api_coverage_from_public_docs(
            pages,
            timeout=int(timeout),
            auth_headers=auth_headers or {},
        ),
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
            "unverified_link_samples": metrics["links"].get("unverified_link_samples", []),
            "api_uncovered_samples": metrics["api_coverage"]["uncovered_endpoint_samples"],
        },
    }


def _aggregate_api_coverage(sites: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate API coverage across sites, treating -1.0 (N/A) correctly."""
    total_ref = 0
    total_usage = 0
    total_api_pages = 0
    all_na = True
    for s in sites:
        ac = s["metrics"]["api_coverage"]
        total_api_pages += int(ac.get("api_pages_detected", 0))
        if not ac.get("no_api_pages_found"):
            all_na = False
            total_ref += int(ac.get("reference_endpoint_count", 0))
            total_usage += int(ac.get("endpoints_with_usage_docs", 0))
    if all_na:
        return {
            "reference_coverage_pct": -1.0,
            "no_api_pages_found": True,
            "api_pages_detected": total_api_pages,
            "coverage_determined": False,
            "detection_note": "",
        }
    if total_ref == 0:
        return {
            "reference_coverage_pct": -1.0,
            "no_api_pages_found": False,
            "api_pages_detected": total_api_pages,
            "coverage_determined": False,
            "detection_note": (
                "API-like pages were detected, but no endpoint or operation "
                "identifiers could be extracted in aggregate."
            ),
        }
    pct = round(total_usage / max(1, total_ref) * 100, 2) if total_ref else 0.0
    return {
        "reference_coverage_pct": pct,
        "no_api_pages_found": False,
        "api_pages_detected": total_api_pages,
        "coverage_determined": True,
        "detection_note": "",
    }


def _merge_site_runs(site_runs: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge repeated runs for one site; links use intersection for confirmed breaks."""
    if not site_runs:
        return {}
    if len(site_runs) == 1:
        return site_runs[0]

    merged = dict(site_runs[0])
    metrics_runs = [r.get("metrics", {}) for r in site_runs if isinstance(r.get("metrics"), dict)]
    if not metrics_runs:
        return merged

    link_runs = [m.get("links", {}) for m in metrics_runs]
    confirmed_sets = [
        set(l.get("_all_confirmed_broken_links", []))
        for l in link_runs
    ]
    intersection_confirmed = set.intersection(*confirmed_sets) if confirmed_sets else set()
    unverified_union: set[str] = set()
    excluded_union: set[str] = set()
    for l in link_runs:
        unverified_union.update(l.get("_all_unverified_links", []))
        excluded_union.update(l.get("_all_excluded_links", []))
    unverified_union -= intersection_confirmed

    docs_confirmed = [u for u in sorted(intersection_confirmed) if not _is_repo_link(u)]
    repo_confirmed = [u for u in sorted(intersection_confirmed) if _is_repo_link(u)]

    link_merged = merged.setdefault("metrics", {}).setdefault("links", {})
    link_merged["broken_internal_links_count"] = len(intersection_confirmed)
    link_merged["confirmed_broken_links_count"] = len(intersection_confirmed)
    link_merged["docs_broken_links_count"] = len(docs_confirmed)
    link_merged["repo_broken_links_count"] = len(repo_confirmed)
    link_merged["broken_internal_link_samples"] = docs_confirmed[:20] + repo_confirmed[:10]
    link_merged["docs_broken_link_samples"] = docs_confirmed[:30]
    link_merged["repo_broken_link_samples"] = repo_confirmed[:30]
    link_merged["unverified_links_count"] = len(unverified_union)
    link_merged["unverified_link_samples"] = sorted(list(unverified_union))[:30]
    link_merged["excluded_links_count"] = len(excluded_union)
    link_merged["excluded_link_samples"] = sorted(list(excluded_union))[:30]
    link_merged["_all_confirmed_broken_links"] = sorted(list(intersection_confirmed))
    link_merged["_all_unverified_links"] = sorted(list(unverified_union))
    link_merged["_all_excluded_links"] = sorted(list(excluded_union))

    # Median for volatile percentages
    def _median_metric(path: list[str], default: float = 0.0) -> float:
        vals: list[float] = []
        for m in metrics_runs:
            cur: Any = m
            ok = True
            for k in path:
                if not isinstance(cur, dict) or k not in cur:
                    ok = False
                    break
                cur = cur[k]
            if ok:
                try:
                    vals.append(float(cur))
                except (TypeError, ValueError):
                    logger.debug("Skipping non-numeric metric value at path=%s: %r", path, cur)
        if not vals:
            return default
        return round(float(statistics.median(vals)), 2)

    merged["metrics"]["examples"]["example_reliability_estimate_pct"] = _median_metric(
        ["examples", "example_reliability_estimate_pct"], 0.0,
    )
    merged["metrics"]["seo_geo"]["seo_geo_issue_rate_pct"] = _median_metric(
        ["seo_geo", "seo_geo_issue_rate_pct"], 0.0,
    )
    merged["metrics"]["freshness"]["last_updated_coverage_pct"] = _median_metric(
        ["freshness", "last_updated_coverage_pct"], 0.0,
    )
    return merged


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
            "urls_examined": sum(int(s["metrics"]["crawl"].get("urls_examined", s["metrics"]["crawl"]["requested_pages"])) for s in sites),
            "max_pages_total": sum(max(0, int(s["metrics"]["crawl"].get("max_pages", 0))) for s in sites),
            "discovered_pages": sum(int(s["metrics"]["crawl"].get("discovered_pages", s["metrics"]["crawl"]["requested_pages"])) for s in sites),
            "crawl_scope_pages": sum(int(s["metrics"]["crawl"].get("crawl_scope_pages", s["metrics"]["crawl"].get("discovered_pages", s["metrics"]["crawl"]["requested_pages"]))) for s in sites),
            "trap_urls_skipped": sum(int(s["metrics"]["crawl"].get("trap_urls_skipped", 0)) for s in sites),
        },
        "links": {
            "broken_internal_links_count": sum(int(s["metrics"]["links"]["broken_internal_links_count"]) for s in sites),
            "docs_broken_links_count": sum(int(s["metrics"]["links"].get("docs_broken_links_count", 0)) for s in sites),
            "repo_broken_links_count": sum(int(s["metrics"]["links"].get("repo_broken_links_count", 0)) for s in sites),
            "unverified_links_count": sum(int(s["metrics"]["links"].get("unverified_links_count", 0)) for s in sites),
            "confirmed_broken_links_count": sum(int(s["metrics"]["links"].get("confirmed_broken_links_count", 0)) for s in sites),
            "excluded_links_count": sum(int(s["metrics"]["links"].get("excluded_links_count", 0)) for s in sites),
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
    pages = int(metrics["crawl"]["pages_crawled"] or 0)
    urls_examined = int(metrics["crawl"].get("urls_examined", metrics["crawl"]["requested_pages"]) or 0)
    scope_pages = int(metrics["crawl"].get("crawl_scope_pages", metrics["crawl"].get("discovered_pages", metrics["crawl"]["requested_pages"])) or 0)
    docs_broken = int(metrics["links"].get("docs_broken_links_count", 0))
    unverified = int(metrics["links"].get("unverified_links_count", 0))
    api_cov = float(metrics["api_coverage"].get("reference_coverage_pct", -1.0) or -1.0)
    api_pages = int(metrics["api_coverage"].get("api_pages_detected", 0) or 0)
    crawl_ratio = 0.0 if scope_pages <= 0 else min(1.0, urls_examined / scope_pages)
    metrics["crawl"]["crawl_coverage_pct"] = _safe_pct(urls_examined, scope_pages)
    link_conf = max(20.0, 95.0 - min(70.0, (unverified / max(1, docs_broken + unverified)) * 100.0))
    api_conf = 85.0 if api_cov >= 0 else (55.0 if api_pages > 0 else 35.0)
    crawl_conf = 35.0 + crawl_ratio * 60.0
    overall_conf = round((link_conf * 0.4) + (api_conf * 0.35) + (crawl_conf * 0.25), 2)
    confidence = {
        "overall_confidence_pct": overall_conf,
        "links_confidence_pct": round(link_conf, 2),
        "api_confidence_pct": round(api_conf, 2),
        "crawl_confidence_pct": round(crawl_conf, 2),
    }
    return {"metrics": metrics, "confidence": confidence}


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


def _run_llm_json_prompt(
    *,
    api_key: str,
    model: str,
    timeout: int,
    prompt: str,
    max_tokens: int = 1200,
) -> dict[str, Any]:
    """Run Anthropic LLM and return parsed JSON object."""
    body = {
        "model": model,
        "max_tokens": int(max_tokens),
        "temperature": 0.1,
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
    text = ""
    for part in data.get("content", []) if isinstance(data.get("content"), list) else []:
        if isinstance(part, dict) and part.get("type") == "text":
            text = str(part.get("text", "")).strip()
            if text:
                break
    if not text:
        raise RuntimeError("LLM returned empty response")
    stripped = text.strip()
    if stripped.startswith("```"):
        first_nl = stripped.find("\n")
        if first_nl != -1:
            stripped = stripped[first_nl + 1:]
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()
    parsed = json.loads(stripped)
    if not isinstance(parsed, dict):
        raise RuntimeError("LLM response is not JSON object")
    return parsed


def _clamp(v: Any, low: float, high: float, default: float) -> float:
    try:
        n = float(v)
    except (TypeError, ValueError):
        n = float(default)
    return max(low, min(high, n))


def _autofill_assumptions_with_llm(
    *,
    company_name: str,
    site_urls: list[str],
    aggregate_metrics: dict[str, Any],
    llm_api_key: str,
    llm_model: str,
    llm_timeout: int,
) -> dict[str, Any]:
    """Generate assumptions profile from available public signals."""
    prompt = (
        "Return JSON only with keys: "
        "engineer_hourly_usd,support_hourly_usd,release_count_per_month,"
        "baseline_manual_sync_hours_per_week,avg_release_delay_hours,"
        "monthly_support_tickets,docs_related_ticket_share,avg_ticket_handling_minutes,"
        "assumptions_confidence_pct,provenance. "
        "Use realistic enterprise software ranges, do not invent precise facts. "
        "Prefer conservative base-case values for B2B SaaS docs operations. "
        "provenance must be an array of short strings describing rationale. "
        f"Company: {company_name}. Sites: {site_urls}. "
        f"Audit metrics: {json.dumps(aggregate_metrics, ensure_ascii=True)}"
    )
    out = _run_llm_json_prompt(
        api_key=llm_api_key,
        model=llm_model,
        timeout=llm_timeout,
        prompt=prompt,
        max_tokens=1000,
    )
    return {
        "engineer_hourly_usd": round(_clamp(out.get("engineer_hourly_usd"), 50, 400, 120), 2),
        "support_hourly_usd": round(_clamp(out.get("support_hourly_usd"), 20, 180, 55), 2),
        "release_count_per_month": round(_clamp(out.get("release_count_per_month"), 1, 30, 8), 2),
        "baseline_manual_sync_hours_per_week": round(_clamp(out.get("baseline_manual_sync_hours_per_week"), 2, 80, 16), 2),
        "avg_release_delay_hours": round(_clamp(out.get("avg_release_delay_hours"), 0.5, 72, 6), 2),
        "monthly_support_tickets": round(_clamp(out.get("monthly_support_tickets"), 20, 50000, 1200), 2),
        "docs_related_ticket_share": round(_clamp(out.get("docs_related_ticket_share"), 0.02, 0.8, 0.22), 4),
        "avg_ticket_handling_minutes": round(_clamp(out.get("avg_ticket_handling_minutes"), 5, 240, 25), 2),
        "assumptions_confidence_pct": round(_clamp(out.get("assumptions_confidence_pct"), 20, 90, 55), 2),
        "provenance": out.get("provenance", []) if isinstance(out.get("provenance"), list) else [],
    }


def _resolve_company_assumptions_path(
    explicit_path: str,
    company_name: str,
    site_urls: list[str],
    profiles_dir: str,
) -> str:
    """Resolve company assumptions profile path for financial model overrides."""
    if str(explicit_path).strip():
        p = _resolve_cross_platform_path(Path(str(explicit_path).strip()))
        return str(p) if p.exists() else ""
    base_dir = _resolve_cross_platform_path(Path(str(profiles_dir).strip()))
    if not base_dir.exists():
        return ""

    candidates: list[Path] = []
    company_slug = _slugify(company_name)
    if company_slug:
        candidates.append(base_dir / f"{company_slug}.json")

    for raw in site_urls:
        parsed = urlparse(raw)
        host = parsed.netloc.lower()
        host = re.sub(r"^docs\.", "", host)
        host_slug = _slugify(host.replace(".", "-"))
        domain_slug = _slugify(host.split(".")[0]) if host else ""
        if host_slug:
            candidates.append(base_dir / f"{host_slug}.json")
        if domain_slug:
            candidates.append(base_dir / f"{domain_slug}.json")

    candidates.append(base_dir / "default.json")
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists():
            return str(candidate)
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
    except (RuntimeError, ValueError, TypeError, OSError) as exc:  # noqa: BLE001
        raise RuntimeError(f"LLM returned non-JSON content: {text[:300]}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("LLM response JSON root is not an object.")
    return parsed


def _build_html(payload: dict[str, Any]) -> str:
    m = payload["aggregate"]["metrics"]
    conf = payload.get("confidence", {}) if isinstance(payload.get("confidence"), dict) else {}
    sites = payload.get("sites", [])
    def _fmt_api_cov(ac: dict[str, Any]) -> str:
        raw = float(ac.get("reference_coverage_pct", -1.0) or -1.0)
        if raw < 0:
            return "N/A"
        return f"{raw}%"
    sites_list = "".join(
        "<li><strong>{}</strong>: pages={}, broken_links={}, api_coverage={}, examples={}%</li>".format(
            html.escape(str(site.get("site_url", ""))),
            site.get("metrics", {}).get("crawl", {}).get("pages_crawled", 0),
            site.get("metrics", {}).get("links", {}).get("broken_internal_links_count", 0),
            _fmt_api_cov(site.get("metrics", {}).get("api_coverage", {})),
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
        <div class=\"card\"><div class=\"label\">Pages discovered</div><div class=\"value\">{m['crawl'].get('discovered_pages', m['crawl'].get('requested_pages', 0))}</div></div>
        <div class=\"card\"><div class=\"label\">Crawl coverage</div><div class=\"value\">{m['crawl'].get('crawl_coverage_pct', 0)}%</div></div>
        <div class=\"card\"><div class=\"label\">Broken links (docs)</div><div class=\"value\">{m['links'].get('docs_broken_links_count', m['links']['broken_internal_links_count'])}</div></div>
        <div class=\"card\"><div class=\"label\">Broken links (repo nav)</div><div class=\"value\">{m['links'].get('repo_broken_links_count', 0)}</div></div>
        <div class=\"card\"><div class=\"label\">Unverified links</div><div class=\"value\">{m['links'].get('unverified_links_count', 0)}</div></div>
        <div class=\"card\"><div class=\"label\">SEO/GEO issue rate</div><div class=\"value\">{m['seo_geo']['seo_geo_issue_rate_pct']}%</div></div>
        <div class=\"card\"><div class=\"label\">API reference coverage</div><div class=\"value\">{_fmt_api_cov(m['api_coverage'])}</div></div>
        <div class=\"card\"><div class=\"label\">Example reliability (estimate)</div><div class=\"value\">{m['examples']['example_reliability_estimate_pct']}%</div></div>
        <div class=\"card\"><div class=\"label\">Last-updated coverage</div><div class=\"value\">{m['freshness']['last_updated_coverage_pct']}%</div></div>
        <div class=\"card\"><div class=\"label\">Audit confidence</div><div class=\"value\">{conf.get('overall_confidence_pct', 0)}%</div></div>
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
    parser.add_argument(
        "--max-pages",
        type=int,
        default=0,
        help="Per-site crawl cap. Use 0 for automatic crawl until convergence (default).",
    )
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument(
        "--auto-max-pages",
        type=int,
        default=100000,
        help="Safety cap used when --max-pages=0 (auto mode).",
    )
    parser.add_argument(
        "--crawl-convergence-rounds",
        type=int,
        default=8,
        help="Stop auto-crawl after this many rounds without newly discovered pages.",
    )
    parser.add_argument(
        "--crawl-batch-size",
        type=int,
        default=60,
        help="Max URLs fetched per crawl round before convergence check.",
    )
    parser.add_argument(
        "--verification-runs",
        type=int,
        default=3,
        help="Number of full crawl+verification runs; broken links use intersection across runs",
    )
    parser.add_argument(
        "--verification-modes",
        default="bot,browser,authenticated",
        help="Comma-separated: bot,browser,authenticated",
    )
    parser.add_argument(
        "--browser-verify-sample",
        type=int,
        default=120,
        help="How many broken-link candidates to verify in browser mode",
    )
    parser.add_argument(
        "--browser-discovery-pages",
        type=int,
        default=400,
        help="How many pages browser mode may discover for JS-heavy docs",
    )
    parser.add_argument(
        "--auth-headers-json",
        default="",
        help="JSON file path or raw JSON object with auth headers for authenticated checks",
    )
    parser.add_argument(
        "--auth-headers-env-name",
        default="DOCS_AUDIT_AUTH_HEADERS_JSON",
        help="Environment variable that may contain JSON object with auth headers",
    )
    parser.add_argument(
        "--auth-storage-state",
        default="reports/playwright_storage_state.json",
        help="Playwright storage state file used for authenticated browser checks",
    )
    parser.add_argument(
        "--auth-login-url",
        default="",
        help="Login URL for automatic storage-state generation",
    )
    parser.add_argument(
        "--auth-username-env-name",
        default="DOCS_AUDIT_LOGIN_USERNAME",
        help="Environment variable for login username",
    )
    parser.add_argument(
        "--auth-password-env-name",
        default="DOCS_AUDIT_LOGIN_PASSWORD",
        help="Environment variable for login password",
    )
    parser.add_argument(
        "--auth-username-selector",
        default="input[name='username'], input[type='email']",
        help="CSS selector for username/email input on login page",
    )
    parser.add_argument(
        "--auth-password-selector",
        default="input[type='password']",
        help="CSS selector for password input on login page",
    )
    parser.add_argument(
        "--auth-submit-selector",
        default="button[type='submit'], input[type='submit']",
        help="CSS selector for submit button on login page",
    )
    parser.add_argument(
        "--auth-success-url-pattern",
        default="",
        help="Optional regex URL pattern indicating successful login",
    )
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
        default=".env",
        help="Path to .env file containing ANTHROPIC_API_KEY (defaults to repo .env; also searches common fallback locations)",
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
    parser.add_argument(
        "--auto-scorecard",
        action="store_true",
        help="Automatically regenerate scorecard before PDF using company assumptions profile",
    )
    parser.add_argument(
        "--assumptions-json",
        default="",
        help="Explicit assumptions JSON for financial model (overrides profile auto-detection)",
    )
    parser.add_argument(
        "--assumptions-profiles-dir",
        default="config/company_assumptions",
        help="Directory with company assumptions profiles (example: databricks.json, default.json)",
    )
    parser.add_argument(
        "--assumptions-autofill",
        action="store_true",
        help="Use LLM to generate assumptions when profile is not found",
    )
    parser.add_argument(
        "--assumptions-autofill-output",
        default="reports/company_assumptions.autofill.json",
        help="Path to save LLM-generated assumptions profile",
    )
    parser.add_argument(
        "--runtime-config",
        default="docsops/config/client_runtime.yml",
        help="Runtime config path used for LLM egress policy",
    )
    parser.add_argument(
        "--external-llm-approve-once",
        action="store_true",
        help="Approve one external LLM step for this execution",
    )
    parser.add_argument(
        "--external-llm-approve-for-run",
        action="store_true",
        help="Approve external LLM usage for this run (cached in reports dir)",
    )
    args = parser.parse_args()

    # -- License gate: public docs audit requires enterprise plan --
    try:
        from scripts.license_gate import require
        require("executive_audit_pdf")
    except ImportError:
        logger.warning("license_gate unavailable; continuing without plan enforcement")

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
        max_pages_raw = input(
            f"Max pages per site (default: {args.max_pages}, 0 = auto): "
        ).strip()
        if max_pages_raw and re.fullmatch(r"-?\d+", max_pages_raw):
            args.max_pages = int(max_pages_raw)
        timeout_raw = input(f"Request timeout seconds (default: {args.timeout}): ").strip()
        if timeout_raw.isdigit():
            args.timeout = int(timeout_raw)
        company_raw = input("Company name for PDF report (default: Client): ").strip()
        if company_raw:
            args.company_name = company_raw
        default_out_dir = Path("reports") / _slugify(args.company_name)
        out_dir_raw = input(f"Output directory (default: {default_out_dir}): ").strip()
        out_dir = Path(out_dir_raw) if out_dir_raw else default_out_dir
        args.json_output = str(out_dir / "public_docs_audit.json")
        args.html_output = str(out_dir / "public_docs_audit.html")
        args.llm_summary_output = str(out_dir / "public_docs_audit_llm_summary.json")
        args.scorecard_json = str(out_dir / "audit_scorecard.json")
        args.assumptions_autofill_output = str(out_dir / "company_assumptions.autofill.json")
        print("Claude Sonnet executive analysis options:")
        print("  1) Summary only -- LLM gets aggregate metrics only (fast, ~$0.05)")
        print("  2) Full -- LLM gets all per-site data (slower, ~$3-4/site)")
        print("  3) None -- no LLM analysis")
        llm_prompt = (
            "Choice [1/2/3] (default: 1)\n"
            "  1 = Summary only (fast, cheap)\n"
            "  2 = Full analysis (slower, more expensive)\n"
            "  3 = None (no LLM)\n"
            "> "
        )
        llm_raw = input(llm_prompt).strip()
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
        pdf_raw = input("Generate executive PDF after audit? [Y/n]: ").strip().lower()
        args.generate_pdf = pdf_raw not in {"n", "no"}
        if args.generate_pdf:
            default_pdf = str(out_dir / "{}-executive-audit.pdf".format(_slugify(args.company_name)))
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

    verification_modes = {
        part.strip().lower()
        for part in str(getattr(args, "verification_modes", "bot,browser,authenticated")).split(",")
        if part.strip()
    }
    if not verification_modes:
        verification_modes = {"bot"}
    allowed_modes = {"bot", "browser", "authenticated"}
    verification_modes = {m for m in verification_modes if m in allowed_modes} or {"bot"}

    auth_headers: dict[str, str] = {}
    auth_raw = ""
    env_name = str(getattr(args, "auth_headers_env_name", "DOCS_AUDIT_AUTH_HEADERS_JSON")).strip()
    if env_name:
        auth_raw = str(os.environ.get(env_name, "")).strip()
    if not auth_raw:
        auth_src = str(getattr(args, "auth_headers_json", "")).strip()
        if auth_src:
            maybe_path = _resolve_cross_platform_path(Path(auth_src))
            if maybe_path.exists():
                auth_raw = maybe_path.read_text(encoding="utf-8", errors="ignore").strip()
            else:
                auth_raw = auth_src
    if auth_raw:
        try:
            parsed_auth = json.loads(auth_raw)
            if isinstance(parsed_auth, dict):
                auth_headers = {
                    str(k): str(v)
                    for k, v in parsed_auth.items()
                    if str(k).strip() and str(v).strip()
                }
        except (RuntimeError, ValueError, TypeError, OSError):  # noqa: BLE001
            auth_headers = {}

    storage_state_path = _ensure_playwright_storage_state(
        storage_state_path=str(getattr(args, "auth_storage_state", "")),
        login_url=str(getattr(args, "auth_login_url", "")).strip(),
        username=str(os.environ.get(str(getattr(args, "auth_username_env_name", "DOCS_AUDIT_LOGIN_USERNAME")), "")).strip(),
        password=str(os.environ.get(str(getattr(args, "auth_password_env_name", "DOCS_AUDIT_LOGIN_PASSWORD")), "")).strip(),
        username_selector=str(getattr(args, "auth_username_selector", "")).strip(),
        password_selector=str(getattr(args, "auth_password_selector", "")).strip(),
        submit_selector=str(getattr(args, "auth_submit_selector", "")).strip(),
        success_wait_url_pattern=str(getattr(args, "auth_success_url_pattern", "")).strip(),
        timeout=max(8, int(args.timeout)),
        auth_headers=auth_headers,
    )
    if storage_state_path:
        parsed_host = urlparse(normalized_urls[0]).netloc if normalized_urls else ""
        cookie_header = _cookie_header_from_storage_state(storage_state_path, parsed_host)
        if cookie_header and "Cookie" not in auth_headers:
            auth_headers["Cookie"] = cookie_header

    verification_runs = max(1, int(getattr(args, "verification_runs", 3)))

    def _run_site(url: str) -> dict[str, Any]:
        runs: list[dict[str, Any]] = []
        for run_idx in range(verification_runs):
            if verification_runs > 1:
                print(f"[audit] run {run_idx + 1}/{verification_runs} for {url}", flush=True)
            runs.append(_site_payload(
                url,
                int(args.max_pages),
                int(args.timeout),
                verification_modes=verification_modes,
                auth_headers=auth_headers,
                browser_verify_sample=int(getattr(args, "browser_verify_sample", 120)),
                browser_discovery_pages=int(getattr(args, "browser_discovery_pages", 400)),
                storage_state_path=storage_state_path,
                crawl_convergence_rounds=int(getattr(args, "crawl_convergence_rounds", 8)),
                crawl_batch_size=int(getattr(args, "crawl_batch_size", 60)),
                auto_max_pages=int(getattr(args, "auto_max_pages", 100000)),
            ))
        merged = _merge_site_runs(runs)
        merged["run_count"] = verification_runs
        return merged

    # Process sites in parallel when multiple URLs are provided.
    if len(normalized_urls) == 1:
        sites = [_run_site(normalized_urls[0])]
    else:
        print("[audit] processing {} sites in parallel...".format(len(normalized_urls)), flush=True)
        sites = []
        with ThreadPoolExecutor(max_workers=min(len(normalized_urls), 4)) as pool:
            futures = {pool.submit(_run_site, url): url for url in normalized_urls}
            for future in as_completed(futures):
                sites.append(future.result())
    aggregate = _aggregate_sites(sites)
    m = aggregate["metrics"]

    findings = []
    total_pages = m["crawl"]["pages_crawled"]
    urls_examined = int(m["crawl"].get("urls_examined", m["crawl"].get("requested_pages", 0)) or 0)
    scope_pages = int(m["crawl"].get("crawl_scope_pages", m["crawl"].get("discovered_pages", m["crawl"].get("requested_pages", 0))) or 0)
    scope_basis = str(m["crawl"].get("crawl_scope_basis", "discovered"))
    crawl_coverage_pct = float(m["crawl"].get("crawl_coverage_pct", _safe_pct(urls_examined, scope_pages)))
    if total_pages == 0:
        findings.append(
            "Crawler could not fetch any pages. The site may block automated "
            "requests, require JavaScript rendering, or be temporarily unavailable. "
            "Metrics below are unavailable."
        )
    elif crawl_coverage_pct < 80:
        findings.append(
            "Crawl coverage is low: {}% ({} URLs examined of {} in {} scope). "
            "Run authenticated mode or increase auto crawl safety cap.".format(
                crawl_coverage_pct, urls_examined, scope_pages, scope_basis,
            ),
        )
    docs_broken = int(m["links"].get("docs_broken_links_count", 0))
    repo_broken = int(m["links"].get("repo_broken_links_count", 0))
    unverified_links = int(m["links"].get("unverified_links_count", 0))
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
    if unverified_links > 0:
        findings.append(
            "Link verification inconclusive for {} URLs (auth/rate-limit/server block); "
            "these are excluded from broken-link counts.".format(unverified_links)
        )
    if m["seo_geo"]["seo_geo_issue_rate_pct"] > 10:
        findings.append(f"SEO/GEO issue rate is high: {m['seo_geo']['seo_geo_issue_rate_pct']}%")
    api_cov = m["api_coverage"]["reference_coverage_pct"]
    api_pages = int(m["api_coverage"].get("api_pages_detected", 0))
    api_detection_note = str(m["api_coverage"].get("detection_note", "") or "")
    if m["api_coverage"].get("no_api_pages_found"):
        if total_pages >= 500:
            findings.append(
                "API reference pages not detected in {} crawled pages "
                "(possible detection limitation -- site may use non-standard URL patterns)".format(total_pages)
            )
        else:
            findings.append(
                "No API reference pages found in {} crawled pages "
                "(check API URL patterns, JS rendering, and authenticated access)".format(total_pages)
            )
    elif float(api_cov) < 0:
        findings.append(
            "API pages detected ({}), but coverage is N/A because endpoint/operation "
            "identifiers were not extracted. {}".format(api_pages, api_detection_note)
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
        "verification_modes": sorted(list(verification_modes)),
        "sites": sites,
        "aggregate": aggregate,
        "confidence": aggregate.get("confidence", {}),
        "top_findings": findings,
    }

    if bool(args.llm_enabled):
        reports_dir = Path(str(args.json_output)).resolve().parent
        policy = load_policy(Path(str(args.runtime_config)))
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
            approved = ensure_external_allowed(
                policy=policy,
                step="public_docs_audit_executive_analysis",
                reports_dir=reports_dir,
                approve_once=bool(getattr(args, "external_llm_approve_once", False)),
                approve_for_run=bool(getattr(args, "external_llm_approve_for_run", False)),
                non_interactive=not bool(getattr(args, "interactive", False)),
            )
            if not approved:
                payload["llm_analysis"] = {
                    "status": "blocked",
                    "reason": "External LLM use blocked by policy/approval gate.",
                }
            else:
                try:
                    llm_input = redact_payload(payload) if policy.redact_before_external else payload
                    llm_result = _run_llm_analysis(
                        llm_input,
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
                except (RuntimeError, ValueError, TypeError, OSError) as exc:  # noqa: BLE001
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
        f"discovered={m['crawl'].get('discovered_pages', m['crawl'].get('requested_pages', 0))} "
        f"coverage={m['crawl'].get('crawl_coverage_pct', 0)}% "
        f"broken_links={m['links']['broken_internal_links_count']} "
        "api_coverage={}".format(
            "N/A (no API pages in sample)"
            if m["api_coverage"].get("no_api_pages_found")
            else ("N/A (identifier extraction incomplete)" if float(m["api_coverage"].get("reference_coverage_pct", -1) or -1) < 0 else f"{m['api_coverage']['reference_coverage_pct']}%")
        )
    )

    if bool(getattr(args, "generate_pdf", False)):
        print("\n[pdf] generating executive PDF...")
        company = str(getattr(args, "company_name", "Client"))
        pdf_output = getattr(args, "pdf_output", None)
        if not pdf_output:
            pdf_output = "reports/{}-executive-audit.pdf".format(_slugify(company))
        scorecard_json = str(getattr(args, "scorecard_json", "reports/audit_scorecard.json"))

        auto_scorecard_enabled = bool(getattr(args, "auto_scorecard", False) or bool(getattr(args, "generate_pdf", False)))
        if auto_scorecard_enabled:
            assumptions_path = _resolve_company_assumptions_path(
                explicit_path=str(getattr(args, "assumptions_json", "")),
                company_name=company,
                site_urls=normalized_urls,
                profiles_dir=str(getattr(args, "assumptions_profiles_dir", "config/company_assumptions")),
            )
            assumptions_autofill_enabled = bool(getattr(args, "assumptions_autofill", False) or bool(getattr(args, "generate_pdf", False)))
            if not assumptions_path and assumptions_autofill_enabled:
                llm_api_key = os.environ.get(str(args.llm_api_key_env_name), "").strip()
                if not llm_api_key:
                    llm_api_key = _read_dotenv_value(str(args.llm_env_file), str(args.llm_api_key_env_name))
                if llm_api_key:
                    try:
                        reports_dir = Path(str(args.json_output)).resolve().parent
                        policy = load_policy(Path(str(args.runtime_config)))
                        approved = ensure_external_allowed(
                            policy=policy,
                            step="public_docs_audit_assumptions_autofill",
                            reports_dir=reports_dir,
                            approve_once=bool(getattr(args, "external_llm_approve_once", False)),
                            approve_for_run=bool(getattr(args, "external_llm_approve_for_run", False)),
                            non_interactive=not bool(getattr(args, "interactive", False)),
                        )
                        if not approved:
                            raise RuntimeError("External LLM assumptions autofill blocked by policy/approval gate.")
                        safe_metrics = redact_payload(m) if policy.redact_before_external else m
                        auto_profile = _autofill_assumptions_with_llm(
                            company_name=company,
                            site_urls=normalized_urls,
                            aggregate_metrics=safe_metrics,
                            llm_api_key=llm_api_key,
                            llm_model=str(args.llm_model),
                            llm_timeout=int(args.llm_timeout),
                        )
                        auto_path = Path(str(getattr(args, "assumptions_autofill_output", "reports/company_assumptions.autofill.json")))
                        auto_path.parent.mkdir(parents=True, exist_ok=True)
                        auto_path.write_text(json.dumps(auto_profile, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
                        assumptions_path = str(auto_path)
                        print(f"[pdf] assumptions autofill generated: {auto_path}")
                    except (RuntimeError, ValueError, TypeError, OSError) as exc:  # noqa: BLE001
                        print(f"[warn] assumptions autofill failed: {exc}")
                else:
                    print("[warn] assumptions autofill requested but LLM API key is missing")
            scorecard_cmd = [
                "python3", "scripts/generate_audit_scorecard.py",
                "--docs-dir", "docs",
                "--reports-dir", "reports",
                "--spec-path", "api/openapi.yaml",
                "--policy-pack", "policy_packs/api-first.yml",
                "--glossary-path", "glossary.yml",
                "--json-output", scorecard_json,
                "--html-output", "reports/audit_scorecard.html",
            ]
            if assumptions_path:
                scorecard_cmd.extend(["--assumptions-json", assumptions_path])
                print(f"[pdf] scorecard assumptions profile: {assumptions_path}")
            else:
                print("[pdf] scorecard assumptions profile not found; using built-in defaults")
            scorecard_res = subprocess.run(scorecard_cmd, capture_output=True, text=True)
            if scorecard_res.returncode == 0:
                print(f"[ok] auto-scorecard json: {scorecard_json}")
            else:
                print(f"[warn] auto-scorecard failed: {scorecard_res.stderr.strip()}")

        pdf_cmd = [
            "python3", "scripts/generate_executive_audit_pdf.py",
            "--scorecard-json", scorecard_json,
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

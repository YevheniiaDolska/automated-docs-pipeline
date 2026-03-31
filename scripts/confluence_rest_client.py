#!/usr/bin/env python3
"""Confluence REST API client for Cloud (v2) and Server/Data Center (v1).

Fetches pages directly from Confluence via API, converts to Markdown, and
writes docsops-ready files -- no manual ZIP export needed.
"""

from __future__ import annotations

import base64
import json
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from confluence_converter import ConfluenceToMarkdownConverter
from confluence_importer import ConfluencePage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ConfluenceConfig:
    """Configuration for Confluence REST API access."""

    base_url: str
    token: str
    username: str = ""
    api_version: str = "auto"  # "auto", "v1", "v2"
    space_keys: list[str] = field(default_factory=list)
    page_limit: int = 25
    include_attachments: bool = False
    sync_state_file: Path | None = None

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        if not self.base_url:
            raise ValueError("base_url is required")
        if not self.token:
            raise ValueError("token is required")


@dataclass
class SyncState:
    """Persisted state for incremental sync."""

    last_sync_utc: str = ""
    page_versions: dict[str, str] = field(default_factory=dict)
    space_keys: list[str] = field(default_factory=list)


@dataclass
class FetchResult:
    """Result of a REST API fetch-and-import operation."""

    source_url: str
    output_dir: str
    api_version: str = ""
    total_pages: int = 0
    imported_pages: int = 0
    failed_pages: int = 0
    skipped_pages: int = 0
    attachments_downloaded: int = 0
    failed_titles: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    generated_files: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers reused from ConfluenceImporter (avoid duplication)
# ---------------------------------------------------------------------------


def _safe_filename(title: str) -> str:
    """Convert title to a safe filename slug."""
    slug = title.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug[:120].strip("-") or "untitled-page"


def _guess_content_type(title: str, markdown: str) -> str:
    """Guess content_type from title and body."""
    title_lower = title.lower()
    if any(token in title_lower for token in ["troubleshoot", "error", "fail", "issue"]):
        return "troubleshooting"
    if any(token in title_lower for token in ["api", "endpoint", "reference", "parameter"]):
        return "reference"
    if any(token in title_lower for token in ["how to", "setup", "configure", "install"]):
        return "how-to"
    if len(markdown.splitlines()) > 40:
        return "concept"
    return "how-to"


def _escape_yaml(value: str) -> str:
    return value.replace('"', "'")


def _make_summary(title: str, markdown: str) -> str:
    clean = " ".join(markdown.replace("\n", " ").split())
    if not clean:
        clean = f"Migrated from Confluence: {title}."
    summary = clean[:180].rstrip()
    if len(summary) < 50:
        summary = (summary + " This page was migrated from Confluence and requires review.")[:180]
    return summary


def _build_frontmatter(page: ConfluencePage, markdown: str) -> str:
    """Build YAML frontmatter for an imported page."""
    content_type = _guess_content_type(page.title, markdown)
    summary = _make_summary(page.title, markdown)
    tags = ["Migration", "Confluence", content_type.capitalize()]

    lines = [
        "---",
        f'title: "{_escape_yaml(page.title)}"',
        f'description: "{_escape_yaml(summary)}"',
        f"content_type: {content_type}",
        "product: both",
        "language: en",
        "tags:",
    ]
    for tag in tags:
        lines.append(f"  - {tag}")

    if page.id:
        lines.append(f'confluence_id: "{_escape_yaml(page.id)}"')
    if page.space:
        lines.append(f'confluence_space: "{_escape_yaml(page.space)}"')
    if page.parent_id:
        lines.append(f'confluence_parent_id: "{_escape_yaml(page.parent_id)}"')
    if page.author:
        lines.append(f'confluence_author: "{_escape_yaml(page.author)}"')
    if page.modified:
        lines.append(f'last_modified: "{_escape_yaml(page.modified[:10])}"')

    lines.append("---")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# REST client
# ---------------------------------------------------------------------------


MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.0


class ConfluenceRestClient:
    """Fetch pages from Confluence Cloud or Server via REST API."""

    def __init__(self, config: ConfluenceConfig) -> None:
        self.config = config
        self.converter = ConfluenceToMarkdownConverter()
        self._client: httpx.Client | None = None

    # -- HTTP layer ----------------------------------------------------------

    def _build_headers(self) -> dict[str, str]:
        """Build auth headers. Cloud uses Basic (email:token), Server uses Bearer PAT."""
        headers: dict[str, str] = {"Accept": "application/json"}
        if self.config.username:
            # Cloud: Basic auth with email:token
            creds = f"{self.config.username}:{self.config.token}"
            encoded = base64.b64encode(creds.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
        else:
            # Server/DC: Bearer token (PAT)
            headers["Authorization"] = f"Bearer {self.config.token}"
        return headers

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.config.base_url,
                headers=self._build_headers(),
                timeout=30.0,
            )
        return self._client

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """HTTP request with retry on 429/5xx."""
        client = self._get_client()
        last_exc: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                response = client.request(method, path, params=params)
                if response.status_code == 429 or response.status_code >= 500:
                    wait = RETRY_BACKOFF_BASE * (2**attempt)
                    logger.warning(
                        "HTTP %d on %s, retry %d/%d in %.1fs",
                        response.status_code,
                        path,
                        attempt + 1,
                        MAX_RETRIES,
                        wait,
                    )
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError:
                raise
            except (httpx.RequestError, ValueError) as exc:
                last_exc = exc
                wait = RETRY_BACKOFF_BASE * (2**attempt)
                logger.warning(
                    "Request/json parse error on %s, retry %d/%d in %.1fs: %s",
                    path,
                    attempt + 1,
                    MAX_RETRIES,
                    wait,
                    exc,
                )
                time.sleep(wait)

        if last_exc:
            raise last_exc
        raise RuntimeError(f"Max retries exceeded for {path}")

    # -- API version detection -----------------------------------------------

    def detect_api_version(self) -> str:
        """Probe endpoints to determine if Cloud v2 or Server v1."""
        if self.config.api_version != "auto":
            return self.config.api_version

        # Try Cloud v2 first
        try:
            self._request("GET", "/wiki/api/v2/spaces", params={"limit": 1})
            return "v2"
        except (httpx.HTTPError, ValueError, RuntimeError) as exc:
            logger.debug("Cloud v2 probe failed: %s", exc)

        # Try Server v1
        try:
            self._request("GET", "/rest/api/space", params={"limit": 1})
            return "v1"
        except (httpx.HTTPError, ValueError, RuntimeError) as exc:
            logger.debug("Server v1 probe failed: %s", exc)

        raise RuntimeError(
            "Cannot detect Confluence API version. "
            "Verify base_url and credentials."
        )

    # -- Space listing -------------------------------------------------------

    def fetch_spaces(self) -> list[dict[str, Any]]:
        """List available spaces."""
        api_version = self.detect_api_version()
        if api_version == "v2":
            data = self._request("GET", "/wiki/api/v2/spaces", params={"limit": 250})
            return data.get("results", [])
        else:
            data = self._request("GET", "/rest/api/space", params={"limit": 250})
            return data.get("results", [])

    # -- Page fetching -------------------------------------------------------

    def fetch_pages(
        self,
        space_key: str,
        since: str | None = None,
    ) -> list[ConfluencePage]:
        """Fetch pages from a space. Optional incremental via ``since`` date."""
        api_version = self.detect_api_version()
        if api_version == "v2":
            return self._fetch_pages_v2(space_key, since)
        return self._fetch_pages_v1(space_key, since)

    def _fetch_pages_v1(
        self,
        space_key: str,
        since: str | None = None,
    ) -> list[ConfluencePage]:
        """Server/DC v1 API page fetch with pagination."""
        pages: list[ConfluencePage] = []
        start = 0
        limit = self.config.page_limit

        while True:
            params: dict[str, Any] = {
                "spaceKey": space_key,
                "type": "page",
                "expand": "body.storage,version,ancestors",
                "start": start,
                "limit": limit,
            }
            if since:
                params["cql"] = f'space="{space_key}" AND type=page AND lastModified >= "{since}"'
                # When using CQL, remove spaceKey/type params
                params.pop("spaceKey", None)
                params.pop("type", None)
                path = "/rest/api/content/search"
            else:
                path = "/rest/api/content"

            data = self._request("GET", path, params=params)
            results = data.get("results", [])

            for item in results:
                body_storage = item.get("body", {}).get("storage", {}).get("value", "")
                version = item.get("version", {})
                ancestors = item.get("ancestors", [])
                parent_id = str(ancestors[-1]["id"]) if ancestors else None

                pages.append(
                    ConfluencePage(
                        id=str(item["id"]),
                        title=item.get("title", "Untitled"),
                        content=body_storage,
                        space=space_key,
                        parent_id=parent_id,
                        modified=version.get("when", ""),
                        author=version.get("by", {}).get("displayName", ""),
                    )
                )

            # Check for next page
            size = data.get("size", len(results))
            if size < limit:
                break
            start += limit

        return pages

    def _fetch_pages_v2(
        self,
        space_key: str,
        since: str | None = None,
    ) -> list[ConfluencePage]:
        """Cloud v2 API page fetch with cursor pagination."""
        # First resolve space key to space id
        spaces_data = self._request(
            "GET",
            "/wiki/api/v2/spaces",
            params={"keys": space_key, "limit": 1},
        )
        space_results = spaces_data.get("results", [])
        if not space_results:
            raise ValueError(f"Space '{space_key}' not found")
        space_id = space_results[0]["id"]

        pages: list[ConfluencePage] = []
        params: dict[str, Any] = {
            "limit": self.config.page_limit,
            "body-format": "storage",
        }
        if since:
            params["modified-date"] = since

        next_path: str | None = f"/wiki/api/v2/spaces/{space_id}/pages"

        while next_path:
            data = self._request("GET", next_path, params=params)
            results = data.get("results", [])

            for item in results:
                body_val = item.get("body", {}).get("storage", {}).get("value", "")
                version = item.get("version", {})

                pages.append(
                    ConfluencePage(
                        id=str(item["id"]),
                        title=item.get("title", "Untitled"),
                        content=body_val,
                        space=space_key,
                        parent_id=str(item["parentId"]) if item.get("parentId") else None,
                        modified=version.get("createdAt", ""),
                        author=version.get("authorId", ""),
                    )
                )

            # Cursor pagination
            links = data.get("_links", {})
            next_link = links.get("next")
            if next_link:
                next_path = next_link
                params = {}  # params are in the URL
            else:
                next_path = None

        return pages

    # -- Attachment downloading ----------------------------------------------

    def fetch_attachments(self, page_id: str, output_dir: Path) -> int:
        """Download attachments for a page. Returns count downloaded."""
        api_version = self.detect_api_version()
        output_dir.mkdir(parents=True, exist_ok=True)
        count = 0

        try:
            if api_version == "v2":
                data = self._request(
                    "GET",
                    f"/wiki/api/v2/pages/{page_id}/attachments",
                    params={"limit": 50},
                )
            else:
                data = self._request(
                    "GET",
                    f"/rest/api/content/{page_id}/child/attachment",
                    params={"limit": 50},
                )

            results = data.get("results", [])
            client = self._get_client()

            for att in results:
                title = att.get("title", "")
                if api_version == "v2":
                    download_link = att.get("downloadLink", "")
                else:
                    dl = att.get("_links", {}).get("download", "")
                    download_link = dl

                if not download_link or not title:
                    continue

                try:
                    resp = client.get(download_link)
                    resp.raise_for_status()
                    dest = output_dir / _safe_filename(title)
                    dest.write_bytes(resp.content)
                    count += 1
                except (httpx.HTTPError, OSError, ValueError) as exc:
                    logger.warning("Failed to download attachment '%s': %s", title, exc)

        except (httpx.HTTPError, ValueError, RuntimeError) as exc:
            logger.warning("Failed to fetch attachments for page %s: %s", page_id, exc)

        return count

    # -- Sync state ----------------------------------------------------------

    def _load_sync_state(self) -> SyncState | None:
        """Load persisted sync state from JSON file."""
        if not self.config.sync_state_file:
            return None
        path = self.config.sync_state_file
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return SyncState(
                last_sync_utc=data.get("last_sync_utc", ""),
                page_versions=data.get("page_versions", {}),
                space_keys=data.get("space_keys", []),
            )
        except (json.JSONDecodeError, OSError, TypeError):
            return None

    def _save_sync_state(self, state: SyncState) -> None:
        """Write sync state to JSON file."""
        if not self.config.sync_state_file:
            return
        path = self.config.sync_state_file
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "last_sync_utc": state.last_sync_utc,
            "page_versions": state.page_versions,
            "space_keys": state.space_keys,
        }
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # -- Full pipeline -------------------------------------------------------

    def fetch_and_import(
        self,
        output_dir: Path,
        incremental: bool = False,
    ) -> FetchResult:
        """Fetch pages from Confluence, convert to Markdown, write files."""
        output_dir.mkdir(parents=True, exist_ok=True)
        api_version = self.detect_api_version()

        result = FetchResult(
            source_url=self.config.base_url,
            output_dir=str(output_dir),
            api_version=api_version,
        )

        since: str | None = None
        sync_state = self._load_sync_state() if incremental else None
        if sync_state and sync_state.last_sync_utc:
            since = sync_state.last_sync_utc[:10]  # YYYY-MM-DD

        space_keys = self.config.space_keys
        if not space_keys:
            result.warnings.append("No space_keys specified; fetching space list")
            spaces = self.fetch_spaces()
            space_keys = [s.get("key", "") for s in spaces if s.get("key")]
            if not space_keys:
                result.warnings.append("No spaces found")
                return result

        all_pages: list[ConfluencePage] = []
        for sk in space_keys:
            try:
                pages = self.fetch_pages(sk, since=since)
                all_pages.extend(pages)
            except (httpx.HTTPError, ValueError, RuntimeError) as exc:
                result.warnings.append(f"Failed to fetch space '{sk}': {exc}")

        result.total_pages = len(all_pages)

        new_versions: dict[str, str] = {}
        for page in all_pages:
            # Skip if version unchanged (incremental)
            if sync_state and page.id in sync_state.page_versions:
                old_ver = sync_state.page_versions[page.id]
                new_ver = page.modified or ""
                if old_ver == new_ver:
                    result.skipped_pages += 1
                    continue

            try:
                file_path = output_dir / f"{_safe_filename(page.title)}.md"
                markdown = self.converter.convert(page.content)
                frontmatter = _build_frontmatter(page, markdown)
                full_doc = f"{frontmatter}\n\n# {page.title}\n\n{markdown}\n"
                file_path.write_text(full_doc, encoding="utf-8")
                result.generated_files.append(str(file_path))
                result.imported_pages += 1
                new_versions[page.id] = page.modified or ""

                # Download attachments if enabled
                if self.config.include_attachments:
                    att_dir = output_dir / "attachments" / _safe_filename(page.title)
                    count = self.fetch_attachments(page.id, att_dir)
                    result.attachments_downloaded += count

            except (OSError, ValueError, RuntimeError) as exc:
                result.failed_pages += 1
                result.failed_titles.append(page.title)
                result.warnings.append(f"Failed page '{page.title}': {exc}")

        # Save sync state
        if self.config.sync_state_file:
            from datetime import datetime, timezone

            state = SyncState(
                last_sync_utc=datetime.now(timezone.utc).isoformat(),
                page_versions={
                    **(sync_state.page_versions if sync_state else {}),
                    **new_versions,
                },
                space_keys=space_keys,
            )
            self._save_sync_state(state)

        return result

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> ConfluenceRestClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

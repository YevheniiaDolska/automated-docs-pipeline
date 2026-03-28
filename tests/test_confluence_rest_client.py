"""Tests for Confluence REST API client."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from confluence_rest_client import (
    ConfluenceConfig,
    ConfluenceRestClient,
    FetchResult,
    SyncState,
    _build_frontmatter,
    _guess_content_type,
    _make_summary,
    _safe_filename,
)
from confluence_importer import ConfluencePage


# ---------------------------------------------------------------------------
# ConfluenceConfig
# ---------------------------------------------------------------------------


class TestConfluenceConfig:
    def test_defaults(self) -> None:
        cfg = ConfluenceConfig(base_url="https://acme.atlassian.net", token="tok123")
        assert cfg.base_url == "https://acme.atlassian.net"
        assert cfg.token == "tok123"
        assert cfg.username == ""
        assert cfg.api_version == "auto"
        assert cfg.page_limit == 25
        assert cfg.include_attachments is False
        assert cfg.sync_state_file is None

    def test_trailing_slash_stripped(self) -> None:
        cfg = ConfluenceConfig(base_url="https://acme.atlassian.net/", token="tok")
        assert cfg.base_url == "https://acme.atlassian.net"

    def test_missing_base_url_raises(self) -> None:
        with pytest.raises(ValueError, match="base_url"):
            ConfluenceConfig(base_url="", token="tok")

    def test_missing_token_raises(self) -> None:
        with pytest.raises(ValueError, match="token"):
            ConfluenceConfig(base_url="https://acme.atlassian.net", token="")


# ---------------------------------------------------------------------------
# SyncState
# ---------------------------------------------------------------------------


class TestSyncState:
    def test_load_save_roundtrip(self, tmp_path: Path) -> None:
        state_file = tmp_path / "sync.json"
        cfg = ConfluenceConfig(
            base_url="https://acme.atlassian.net",
            token="tok",
            sync_state_file=state_file,
        )
        client = ConfluenceRestClient(cfg)

        original = SyncState(
            last_sync_utc="2026-03-28T12:00:00+00:00",
            page_versions={"101": "2026-03-28", "102": "2026-03-27"},
            space_keys=["DOCS", "ENG"],
        )
        client._save_sync_state(original)
        assert state_file.exists()

        loaded = client._load_sync_state()
        assert loaded is not None
        assert loaded.last_sync_utc == original.last_sync_utc
        assert loaded.page_versions == original.page_versions
        assert loaded.space_keys == original.space_keys

    def test_load_missing_file(self, tmp_path: Path) -> None:
        cfg = ConfluenceConfig(
            base_url="https://acme.atlassian.net",
            token="tok",
            sync_state_file=tmp_path / "nonexistent.json",
        )
        client = ConfluenceRestClient(cfg)
        assert client._load_sync_state() is None

    def test_load_no_sync_file_configured(self) -> None:
        cfg = ConfluenceConfig(base_url="https://acme.atlassian.net", token="tok")
        client = ConfluenceRestClient(cfg)
        assert client._load_sync_state() is None

    def test_save_no_sync_file_configured(self) -> None:
        cfg = ConfluenceConfig(base_url="https://acme.atlassian.net", token="tok")
        client = ConfluenceRestClient(cfg)
        # Should not raise
        client._save_sync_state(SyncState(last_sync_utc="2026-03-28"))


# ---------------------------------------------------------------------------
# Build headers
# ---------------------------------------------------------------------------


class TestBuildHeaders:
    def test_cloud_basic_auth(self) -> None:
        cfg = ConfluenceConfig(
            base_url="https://acme.atlassian.net",
            token="api-tok",
            username="user@acme.com",
        )
        client = ConfluenceRestClient(cfg)
        headers = client._build_headers()
        expected = base64.b64encode(b"user@acme.com:api-tok").decode()
        assert headers["Authorization"] == f"Basic {expected}"
        assert headers["Accept"] == "application/json"

    def test_server_bearer_token(self) -> None:
        cfg = ConfluenceConfig(
            base_url="https://confluence.internal.acme.com",
            token="pat-xyz",
        )
        client = ConfluenceRestClient(cfg)
        headers = client._build_headers()
        assert headers["Authorization"] == "Bearer pat-xyz"


# ---------------------------------------------------------------------------
# API version detection
# ---------------------------------------------------------------------------


def _make_mock_response(status: int = 200, json_data: Any = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = json_data or {}
    resp.raise_for_status.return_value = None
    if status >= 400:
        import httpx

        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=resp,
        )
    return resp


class TestApiVersionDetection:
    def test_explicit_version(self) -> None:
        cfg = ConfluenceConfig(
            base_url="https://acme.atlassian.net",
            token="tok",
            api_version="v1",
        )
        client = ConfluenceRestClient(cfg)
        assert client.detect_api_version() == "v1"

    def test_v2_detected(self) -> None:
        cfg = ConfluenceConfig(base_url="https://acme.atlassian.net", token="tok")
        client = ConfluenceRestClient(cfg)
        mock_client = MagicMock()
        mock_client.request.return_value = _make_mock_response(200, {"results": []})
        client._client = mock_client
        assert client.detect_api_version() == "v2"

    def test_v1_fallback(self) -> None:
        cfg = ConfluenceConfig(base_url="https://acme.atlassian.net", token="tok")
        client = ConfluenceRestClient(cfg)
        mock_client = MagicMock()

        call_count = 0

        def side_effect(method: str, path: str, **kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if "/v2/" in path:
                raise RuntimeError("not found")
            return _make_mock_response(200, {"results": []})

        mock_client.request.side_effect = side_effect
        client._client = mock_client
        assert client.detect_api_version() == "v1"

    def test_both_fail(self) -> None:
        cfg = ConfluenceConfig(base_url="https://acme.atlassian.net", token="tok")
        client = ConfluenceRestClient(cfg)
        mock_client = MagicMock()
        mock_client.request.side_effect = RuntimeError("connection failed")
        client._client = mock_client

        with pytest.raises(RuntimeError, match="Cannot detect"):
            client.detect_api_version()


# ---------------------------------------------------------------------------
# Page fetching
# ---------------------------------------------------------------------------


class TestFetchPages:
    def _make_v1_client(self) -> tuple[ConfluenceRestClient, MagicMock]:
        cfg = ConfluenceConfig(
            base_url="https://confluence.acme.com",
            token="tok",
            api_version="v1",
            page_limit=2,
        )
        client = ConfluenceRestClient(cfg)
        mock_http = MagicMock()
        client._client = mock_http
        return client, mock_http

    def test_single_page_v1(self) -> None:
        client, mock_http = self._make_v1_client()
        mock_http.request.return_value = _make_mock_response(200, {
            "results": [
                {
                    "id": "101",
                    "title": "Webhook Setup",
                    "body": {"storage": {"value": "<p>Content</p>"}},
                    "version": {"when": "2026-03-28", "by": {"displayName": "Alice"}},
                    "ancestors": [],
                },
            ],
            "size": 1,
        })

        pages = client.fetch_pages("DOCS")
        assert len(pages) == 1
        assert pages[0].id == "101"
        assert pages[0].title == "Webhook Setup"
        assert pages[0].space == "DOCS"
        assert pages[0].author == "Alice"

    def test_pagination_v1(self) -> None:
        client, mock_http = self._make_v1_client()

        page1_resp = _make_mock_response(200, {
            "results": [
                {"id": "1", "title": "P1", "body": {"storage": {"value": ""}}, "version": {}, "ancestors": []},
                {"id": "2", "title": "P2", "body": {"storage": {"value": ""}}, "version": {}, "ancestors": []},
            ],
            "size": 2,
        })
        page2_resp = _make_mock_response(200, {
            "results": [
                {"id": "3", "title": "P3", "body": {"storage": {"value": ""}}, "version": {}, "ancestors": []},
            ],
            "size": 1,
        })
        mock_http.request.side_effect = [page1_resp, page2_resp]

        pages = client.fetch_pages("DOCS")
        assert len(pages) == 3

    def test_incremental_with_since_v1(self) -> None:
        client, mock_http = self._make_v1_client()
        mock_http.request.return_value = _make_mock_response(200, {"results": [], "size": 0})

        client.fetch_pages("DOCS", since="2026-03-01")
        call_args = mock_http.request.call_args
        params = call_args.kwargs.get("params") or call_args[1].get("params", {})
        assert "cql" in params
        assert "2026-03-01" in params["cql"]

    def test_v2_space_resolution(self) -> None:
        cfg = ConfluenceConfig(
            base_url="https://acme.atlassian.net",
            token="tok",
            api_version="v2",
            page_limit=25,
        )
        client = ConfluenceRestClient(cfg)
        mock_http = MagicMock()

        spaces_resp = _make_mock_response(200, {"results": [{"id": "sp-42", "key": "DOCS"}]})
        pages_resp = _make_mock_response(200, {
            "results": [
                {
                    "id": "201",
                    "title": "API Ref",
                    "body": {"storage": {"value": "<p>Hi</p>"}},
                    "version": {"createdAt": "2026-03-28", "authorId": "u-1"},
                    "parentId": None,
                },
            ],
            "_links": {},
        })
        mock_http.request.side_effect = [spaces_resp, pages_resp]
        client._client = mock_http

        pages = client.fetch_pages("DOCS")
        assert len(pages) == 1
        assert pages[0].id == "201"

    def test_v2_space_not_found(self) -> None:
        cfg = ConfluenceConfig(
            base_url="https://acme.atlassian.net",
            token="tok",
            api_version="v2",
        )
        client = ConfluenceRestClient(cfg)
        mock_http = MagicMock()
        mock_http.request.return_value = _make_mock_response(200, {"results": []})
        client._client = mock_http

        with pytest.raises(ValueError, match="Space.*not found"):
            client.fetch_pages("MISSING")


# ---------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------


class TestFetchAttachments:
    def test_download_to_output_dir(self, tmp_path: Path) -> None:
        cfg = ConfluenceConfig(
            base_url="https://confluence.acme.com",
            token="tok",
            api_version="v1",
        )
        client = ConfluenceRestClient(cfg)
        mock_http = MagicMock()

        att_resp = _make_mock_response(200, {
            "results": [
                {"title": "diagram.png", "_links": {"download": "/download/att/1"}},
            ],
        })
        file_resp = MagicMock()
        file_resp.status_code = 200
        file_resp.content = b"PNG_BYTES"
        file_resp.raise_for_status.return_value = None

        mock_http.request.return_value = att_resp
        mock_http.get.return_value = file_resp
        client._client = mock_http

        out_dir = tmp_path / "attachments"
        count = client.fetch_attachments("101", out_dir)
        assert count == 1
        assert out_dir.exists()

    def test_skip_on_download_error(self, tmp_path: Path) -> None:
        cfg = ConfluenceConfig(
            base_url="https://confluence.acme.com",
            token="tok",
            api_version="v1",
        )
        client = ConfluenceRestClient(cfg)
        mock_http = MagicMock()

        att_resp = _make_mock_response(200, {
            "results": [
                {"title": "file.pdf", "_links": {"download": "/download/att/2"}},
            ],
        })
        mock_http.request.return_value = att_resp
        mock_http.get.side_effect = RuntimeError("download failed")
        client._client = mock_http

        count = client.fetch_attachments("101", tmp_path / "att")
        assert count == 0


# ---------------------------------------------------------------------------
# Retry logic
# ---------------------------------------------------------------------------


class TestRetryLogic:
    @patch("confluence_rest_client.time.sleep")
    def test_retry_on_429(self, mock_sleep: MagicMock) -> None:
        cfg = ConfluenceConfig(base_url="https://acme.atlassian.net", token="tok")
        client = ConfluenceRestClient(cfg)
        mock_http = MagicMock()

        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_ok = _make_mock_response(200, {"ok": True})

        mock_http.request.side_effect = [resp_429, resp_ok]
        client._client = mock_http

        result = client._request("GET", "/test")
        assert result == {"ok": True}
        assert mock_sleep.call_count == 1

    @patch("confluence_rest_client.time.sleep")
    def test_retry_on_500(self, mock_sleep: MagicMock) -> None:
        cfg = ConfluenceConfig(base_url="https://acme.atlassian.net", token="tok")
        client = ConfluenceRestClient(cfg)
        mock_http = MagicMock()

        resp_500 = MagicMock()
        resp_500.status_code = 500
        resp_ok = _make_mock_response(200, {"ok": True})

        mock_http.request.side_effect = [resp_500, resp_ok]
        client._client = mock_http

        result = client._request("GET", "/test")
        assert result == {"ok": True}

    @patch("confluence_rest_client.time.sleep")
    def test_max_retries_exceeded(self, mock_sleep: MagicMock) -> None:
        cfg = ConfluenceConfig(base_url="https://acme.atlassian.net", token="tok")
        client = ConfluenceRestClient(cfg)
        mock_http = MagicMock()

        resp_500 = MagicMock()
        resp_500.status_code = 500
        mock_http.request.return_value = resp_500
        client._client = mock_http

        with pytest.raises(RuntimeError, match="Max retries"):
            client._request("GET", "/test")


# ---------------------------------------------------------------------------
# fetch_and_import (end-to-end with mocks)
# ---------------------------------------------------------------------------


class TestFetchAndImport:
    def test_end_to_end(self, tmp_path: Path) -> None:
        cfg = ConfluenceConfig(
            base_url="https://acme.atlassian.net",
            token="tok",
            api_version="v1",
            space_keys=["DOCS"],
        )
        client = ConfluenceRestClient(cfg)
        mock_http = MagicMock()

        pages_resp = _make_mock_response(200, {
            "results": [
                {
                    "id": "301",
                    "title": "Getting Started",
                    "body": {"storage": {"value": "<p>Welcome to the guide.</p>"}},
                    "version": {"when": "2026-03-28", "by": {"displayName": "Bob"}},
                    "ancestors": [],
                },
            ],
            "size": 1,
        })
        mock_http.request.return_value = pages_resp
        client._client = mock_http

        output_dir = tmp_path / "imported"
        result = client.fetch_and_import(output_dir)

        assert isinstance(result, FetchResult)
        assert result.total_pages == 1
        assert result.imported_pages == 1
        assert result.failed_pages == 0
        assert result.api_version == "v1"
        assert len(result.generated_files) == 1

        md_file = Path(result.generated_files[0])
        assert md_file.exists()
        content = md_file.read_text(encoding="utf-8")
        assert "content_type:" in content
        assert "# Getting Started" in content

    def test_incremental_skips_unchanged(self, tmp_path: Path) -> None:
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({
            "last_sync_utc": "2026-03-27T00:00:00+00:00",
            "page_versions": {"301": "2026-03-27"},
            "space_keys": ["DOCS"],
        }), encoding="utf-8")

        cfg = ConfluenceConfig(
            base_url="https://acme.atlassian.net",
            token="tok",
            api_version="v1",
            space_keys=["DOCS"],
            sync_state_file=state_file,
        )
        client = ConfluenceRestClient(cfg)
        mock_http = MagicMock()

        pages_resp = _make_mock_response(200, {
            "results": [
                {
                    "id": "301",
                    "title": "Getting Started",
                    "body": {"storage": {"value": "<p>Same content</p>"}},
                    "version": {"when": "2026-03-27", "by": {}},
                    "ancestors": [],
                },
            ],
            "size": 1,
        })
        mock_http.request.return_value = pages_resp
        client._client = mock_http

        output_dir = tmp_path / "imported"
        result = client.fetch_and_import(output_dir, incremental=True)

        assert result.total_pages == 1
        assert result.skipped_pages == 1
        assert result.imported_pages == 0


# ---------------------------------------------------------------------------
# Output structure / helpers
# ---------------------------------------------------------------------------


class TestOutputStructure:
    def test_fetch_result_defaults(self) -> None:
        r = FetchResult(source_url="https://acme.atlassian.net", output_dir="/tmp/out")
        assert r.total_pages == 0
        assert r.failed_titles == []
        assert r.warnings == []

    def test_safe_filename(self) -> None:
        assert _safe_filename("Webhook Setup") == "webhook-setup"
        assert _safe_filename("API Reference (v2)") == "api-reference-v2"
        assert _safe_filename("") == "untitled-page"

    def test_guess_content_type(self) -> None:
        assert _guess_content_type("Troubleshooting auth", "") == "troubleshooting"
        assert _guess_content_type("API Reference", "") == "reference"
        assert _guess_content_type("How to configure", "") == "how-to"
        long_body = "\n".join(["line"] * 50)
        assert _guess_content_type("Architecture", long_body) == "concept"
        assert _guess_content_type("Quick note", "") == "how-to"

    def test_build_frontmatter(self) -> None:
        page = ConfluencePage(
            id="42",
            title="Test Page",
            content="<p>Hello</p>",
            space="DOCS",
        )
        fm = _build_frontmatter(page, "Hello world content here")
        assert "title:" in fm
        assert "content_type:" in fm
        assert 'confluence_id: "42"' in fm
        assert 'confluence_space: "DOCS"' in fm

    def test_make_summary_short_content(self) -> None:
        summary = _make_summary("My Page", "Short.")
        assert len(summary) >= 50
        assert "migrated from Confluence" in summary.lower() or "review" in summary.lower()

    def test_context_manager(self) -> None:
        cfg = ConfluenceConfig(base_url="https://acme.atlassian.net", token="tok")
        with ConfluenceRestClient(cfg) as client:
            assert client is not None
        # close() should have been called -- no error

"""Tests for the company web-research aggregator."""

from __future__ import annotations

import json

import pytest

from scripts import web_research as mod


class _FakeResp:
    def __init__(self, payload: object) -> None:
        self._data = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")

    def read(self, *_a: object) -> bytes:
        return self._data

    def __enter__(self) -> "_FakeResp":
        return self

    def __exit__(self, *_a: object) -> bool:
        return False


def test_resolve_provider_explicit_and_auto() -> None:
    assert mod.resolve_search_provider("brave", {})["name"] == "brave"
    assert mod.resolve_search_provider("nope", {}) is None
    auto = mod.resolve_search_provider("auto", {"SERPAPI_API_KEY": "x"})
    assert auto is not None and auto["name"] == "serpapi"
    assert mod.resolve_search_provider("auto", {}) is None


def test_search_normalizes_tavily(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"results": [{"title": "ACME API", "url": "https://acme.com/api", "content": "The API"}]}
    monkeypatch.setattr(mod, "urlopen", lambda req, timeout: _FakeResp(payload))
    provider = mod.resolve_search_provider("tavily", {})
    out = mod.search(provider, "key", "acme api", 5, 10)
    assert out == [{"title": "ACME API", "url": "https://acme.com/api", "snippet": "The API"}]


def test_search_normalizes_brave(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"web": {"results": [{"title": "Docs", "url": "https://acme.com/docs", "description": "Docs home"}]}}
    monkeypatch.setattr(mod, "urlopen", lambda req, timeout: _FakeResp(payload))
    provider = mod.resolve_search_provider("brave", {})
    out = mod.search(provider, "key", "acme docs", 5, 10)
    assert out[0]["url"] == "https://acme.com/docs"
    assert out[0]["snippet"] == "Docs home"


def test_search_normalizes_serpapi(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"organic_results": [{"title": "ACME", "link": "https://acme.com", "snippet": "Home"}]}
    monkeypatch.setattr(mod, "urlopen", lambda req, timeout: _FakeResp(payload))
    provider = mod.resolve_search_provider("serpapi", {})
    out = mod.search(provider, "key", "acme", 5, 10)
    assert out[0]["url"] == "https://acme.com"


def test_research_dedups_and_aggregates(monkeypatch: pytest.MonkeyPatch) -> None:
    # Same URL returned for every query -> deduped to one source.
    payload = {"results": [{"title": "ACME API", "url": "https://acme.com/api", "content": "API"}]}
    monkeypatch.setattr(mod, "urlopen", lambda req, timeout: _FakeResp(payload))
    provider = mod.resolve_search_provider("tavily", {})
    out = mod.research_company(
        company="ACME", domain="acme.com", provider=provider, api_key="key",
        max_results=5, timeout=10, do_crawl=False,
    )
    assert out["coverage"]["source_count"] == 1
    assert out["coverage"]["web_search_used"] is True
    assert len(out["queries"]) == 5


def test_crawl_extracts_title_and_description(monkeypatch: pytest.MonkeyPatch) -> None:
    html = b'<html><head><title>ACME Docs</title><meta name="description" content="Build with ACME"></head></html>'
    monkeypatch.setattr(mod, "urlopen", lambda req, timeout: _FakeResp(html))
    page = mod.crawl_page("https://acme.com/docs", 10)
    assert page["title"] == "ACME Docs"
    assert page["description"] == "Build with ACME"


def test_crawl_failure_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(req: object, timeout: object) -> object:
        raise mod.URLError("dns")

    monkeypatch.setattr(mod, "urlopen", _boom)
    assert mod.crawl_page("https://nope.invalid", 5) is None

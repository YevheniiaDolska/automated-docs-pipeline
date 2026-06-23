from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest


class _FakeHTTPResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> "_FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_crawl_site_and_payload_with_mocked_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import generate_public_docs_audit as mod

    html_root = """
    <html><body>
      <h1>Docs</h1>
      <p>This guide is and enables teams to ship.</p>
      <a href=\"/page2\">Next</a>
      <a href=\"/broken\">Broken</a>
      <code>curl /v1/ping</code>
    </body></html>
    """
    html_page2 = """
    <html><body>
      <h1>Reference</h1>
      <p>Reference is and provides endpoint details.</p>
      <a href=\"/ok\">OK</a>
    </body></html>
    """

    def _fake_fetch(url: str, timeout: int, _ua_idx: int = 0, head_only: bool = False, extra_headers: dict[str, str] | None = None):
        del timeout, _ua_idx, extra_headers
        if head_only:
            if url.endswith("/broken"):
                return 404, "text/plain", ""
            return 200, "text/plain", ""
        if url.endswith("/page2"):
            return 200, "text/html", html_page2
        if url.endswith("/ok"):
            return 200, "text/html", "<html><body><h1>OK</h1></body></html>"
        if url.endswith("/broken"):
            return 404, "text/html", ""
        return 200, "text/html", html_root

    monkeypatch.setattr(mod, "_fetch", _fake_fetch)
    monkeypatch.setattr(mod, "_USER_AGENTS", ["ua-only"])
    monkeypatch.setattr(mod, "_browser_verify_links", lambda urls, timeout: {u: 200 for u in urls})

    pages, status_map = mod._crawl_site(
        "https://docs.example.com",
        max_pages=3,
        timeout=2,
        verification_modes={"bot", "browser"},
        auth_headers={"Authorization": "Bearer x"},
        browser_verify_sample=10,
    )
    assert len(pages) >= 1
    assert "https://docs.example.com" in status_map

    monkeypatch.setattr(mod, "_crawl_site", lambda *a, **k: (pages, status_map))
    payload = mod._site_payload("https://docs.example.com", 3, 2, verification_modes={"bot"})
    assert payload["site_url"] == "https://docs.example.com"
    assert "metrics" in payload and "crawl" in payload["metrics"]


def test_llm_json_prompt_and_assumptions_clamping(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import generate_public_docs_audit as mod

    llm_payload = {
        "content": [
            {
                "type": "text",
                "text": "```json\n{\"engineer_hourly_usd\": 999, \"support_hourly_usd\": 1, \"release_count_per_month\": 99, \"baseline_manual_sync_hours_per_week\": -1, \"avg_release_delay_hours\": 500, \"monthly_support_tickets\": 3, \"docs_related_ticket_share\": 9, \"avg_ticket_handling_minutes\": 999, \"assumptions_confidence_pct\": 0, \"provenance\": [\"heuristic\"]}\n```",
            }
        ]
    }

    monkeypatch.setattr(mod, "urlopen", lambda req, timeout: _FakeHTTPResponse(llm_payload))

    parsed = mod._run_llm_json_prompt(
        api_key="k",
        model="claude",
        timeout=3,
        prompt="hello",
        max_tokens=100,
    )
    assert isinstance(parsed, dict)

    monkeypatch.setattr(mod, "_run_llm_json_prompt", lambda **kwargs: parsed)
    assumptions = mod._autofill_assumptions_with_llm(
        company_name="Acme",
        site_urls=["https://docs.example.com"],
        aggregate_metrics={"pages": 10},
        llm_api_key="k",
        llm_model="claude",
        llm_timeout=5,
    )
    assert assumptions["engineer_hourly_usd"] == 400.0
    assert assumptions["support_hourly_usd"] == 20.0
    assert assumptions["provenance"] == ["heuristic"]


def test_resolve_company_assumptions_path_and_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import generate_public_docs_audit as mod

    profiles = tmp_path / "profiles"
    profiles.mkdir()
    (profiles / "acme.json").write_text("{}", encoding="utf-8")
    (profiles / "default.json").write_text("{}", encoding="utf-8")

    resolved = mod._resolve_company_assumptions_path(
        explicit_path="",
        company_name="Acme Inc",
        site_urls=["https://docs.acme.com"],
        profiles_dir=str(profiles),
    )
    assert resolved.endswith("acme.json")

    explicit = mod._resolve_company_assumptions_path(
        explicit_path=str(profiles / "default.json"),
        company_name="",
        site_urls=[],
        profiles_dir=str(profiles),
    )
    assert explicit.endswith("default.json")

    env_file = tmp_path / ".env"
    env_file.write_text("ANTHROPIC_API_KEY=secret123\n", encoding="utf-8")
    val = mod._read_dotenv_value(str(env_file), "ANTHROPIC_API_KEY")
    assert val == "secret123"


def test_run_llm_analysis_and_build_html(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import generate_public_docs_audit as mod

    analysis_payload = {
        "content": [
            {
                "type": "text",
                "text": "```json\n{\"executive_summary\":\"Strong docs\",\"strengths\":[\"coverage\"],\"risks\":[\"drift\"],\"prioritized_actions\":[{\"action\":\"Fix\",\"impact\":\"high\",\"effort\":\"medium\"}],\"limitations\":[\"external scan\"]}\n```",
            }
        ]
    }

    monkeypatch.setattr(mod, "urlopen", lambda req, timeout: _FakeHTTPResponse(analysis_payload))
    llm = mod._run_llm_analysis(
        payload={"site_urls": ["https://docs.example.com"]},
        model="claude",
        api_key="k",
        timeout=5,
        summary_only=True,
    )
    assert llm["executive_summary"] == "Strong docs"

    html = mod._build_html(
        {
            "site_urls": ["https://docs.example.com"],
            "generated_at": "2026-03-25T12:00:00Z",
            "topology_mode": "single-product",
            "aggregate": {
                "metrics": {
                    "crawl": {"pages_crawled": 2},
                    "links": {"broken_internal_links_count": 1, "docs_broken_links_count": 1, "repo_broken_links_count": 0},
                    "seo_geo": {"geo_score": 80.0, "seo_geo_issue_rate_pct": 20.0},
                    "api_coverage": {"reference_coverage_pct": 75.0},
                    "examples": {"example_reliability_estimate_pct": 70.0},
                    "freshness": {"last_updated_coverage_pct": 65.0},
                }
            },
            "confidence": {"score": 80},
            "top_findings": ["Broken links found"],
            "sites": [
                {
                    "site_url": "https://docs.example.com",
                    "metrics": {
                        "crawl": {"pages_crawled": 2},
                        "links": {"broken_internal_links_count": 1},
                        "api_coverage": {"reference_coverage_pct": 75.0},
                        "examples": {"example_reliability_estimate_pct": 70.0},
                    },
                }
            ],
            "llm_analysis": {"status": "ok", "analysis": llm},
        }
    )
    assert "LLM Executive Analysis" in html
    assert "Strong docs" in html

    monkeypatch.setattr(
        mod,
        "urlopen",
        lambda req, timeout: _FakeHTTPResponse({"content": [{"type": "text", "text": "not-json"}]}),
    )
    with pytest.raises(RuntimeError):
        mod._run_llm_analysis(payload={}, model="claude", api_key="k", timeout=2)


def test_link_health_from_store_matches_in_memory() -> None:
    from scripts import generate_public_docs_audit as mod

    pages = [
        mod.PageData(
            url="https://docs.example.com/a",
            status=200,
            title="A",
            meta_description="desc",
            h1_count=1,
            heading_levels=[1, 2],
            internal_links=[
                "https://docs.example.com/live",
                "https://docs.example.com/broken",
                "https://github.com/org/repo/blob/main/README.md",
            ],
            external_links=[],
            text="A page",
            code_blocks=[],
            last_updated_hint="",
            internal_link_refs=[
                {"url": "https://docs.example.com/broken", "anchor_text": "Broken"},
                {"url": "https://github.com/org/repo/blob/main/README.md", "anchor_text": "Repo"},
            ],
        )
    ]
    status_map = {
        "https://docs.example.com/live": 200,
        "https://docs.example.com/broken": 404,
        "https://github.com/org/repo/blob/main/README.md": 404,
    }

    expected = mod._link_health(pages, status_map)
    store = mod._build_link_audit_store(pages)
    try:
        actual = mod._link_health_from_store(store, status_map)
    finally:
        store.close()

    assert actual["confirmed_broken_links_count"] == expected["confirmed_broken_links_count"]
    assert actual["docs_broken_links_count"] == expected["docs_broken_links_count"]
    assert actual["repo_broken_links_count"] == expected["repo_broken_links_count"]
    assert actual["_all_confirmed_broken_links"] == expected["_all_confirmed_broken_links"]
    assert actual["_broken_link_provenance"]["https://docs.example.com/broken"][0]["source_page"] == "https://docs.example.com/a"


def test_link_audit_store_uses_managed_local_tempdir() -> None:
    from scripts import generate_public_docs_audit as mod

    store = mod._LinkAuditStore()
    try:
        assert Path(store._path).parent == mod._LINK_AUDIT_LOCAL_TMPDIR
        assert Path(store._path).suffix == ".sqlite3"
    finally:
        store.close()


def test_select_unchecked_links_streams_without_materializing_all() -> None:
    from scripts import generate_public_docs_audit as mod

    pages = [
        mod.PageData(
            url="https://docs.example.com/root",
            status=200,
            title="Root",
            meta_description="desc",
            h1_count=1,
            heading_levels=[1],
            internal_links=[f"https://docs.example.com/page-{idx}" for idx in range(25)],
            external_links=[],
            text="Root page",
            code_blocks=[],
            last_updated_hint="",
            internal_link_refs=[],
        )
    ]
    store = mod._build_link_audit_store(pages)
    try:
        total, selected = mod._select_unchecked_links(
            store,
            status_map={"https://docs.example.com/page-0": 200},
            limit=5,
        )
    finally:
        store.close()

    assert total == 24
    assert len(selected) == 5
    assert selected == sorted(selected)


def test_site_payload_falls_back_when_link_audit_store_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import generate_public_docs_audit as mod

    pages = [
        mod.PageData(
            url="https://docs.example.com/a",
            status=200,
            title="A",
            meta_description="desc",
            h1_count=1,
            heading_levels=[1],
            internal_links=["https://docs.example.com/broken"],
            external_links=[],
            text="A page",
            code_blocks=[],
            last_updated_hint="",
            internal_link_refs=[{"url": "https://docs.example.com/broken", "anchor_text": "Broken"}],
        )
    ]
    status_map = {"https://docs.example.com/broken": 404}

    monkeypatch.setattr(mod, "_crawl_site", lambda *a, **k: (pages, status_map))
    monkeypatch.setattr(mod, "_seo_geo_metrics", lambda pages: {"geo_score": 80.0, "seo_geo_issue_rate_pct": 0.0})
    monkeypatch.setattr(
        mod,
        "_api_coverage_from_public_docs",
        lambda *a, **k: {"reference_coverage_pct": 0.0, "uncovered_endpoint_samples": []},
    )
    monkeypatch.setattr(mod, "_estimate_example_reliability", lambda pages: {"example_reliability_estimate_pct": 0.0})
    monkeypatch.setattr(mod, "_last_updated_metrics", lambda pages: {"last_updated_coverage_pct": 0.0})
    monkeypatch.setattr(
        mod,
        "_build_link_audit_store",
        lambda pages: (_ for _ in ()).throw(sqlite3.OperationalError("disk I/O error")),
    )

    payload = mod._site_payload("https://docs.example.com", 5, 2)
    assert payload["metrics"]["links"]["broken_internal_links_count"] == 1
    assert payload["metrics"]["links"]["_broken_link_provenance"]["https://docs.example.com/broken"][0]["anchor_text"] == "Broken"

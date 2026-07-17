"""Unit tests for the expanded cross-page contradiction detector.

Covers every contradiction class and every false-positive guard: cross-page
requirement, same-page juxtaposition suppression, plan-tier skip, archival-URL
skip, versioned-docs-subtree isolation, and confidence ordering.
"""

from __future__ import annotations

from typing import Any

from scripts import generate_public_docs_audit as mod


def _page(url: str, text: str = "", code: list[str] | None = None) -> Any:
    return mod.PageData(
        url=url,
        status=200,
        title="Title",
        meta_description="",
        h1_count=1,
        heading_levels=[1],
        internal_links=[],
        external_links=[],
        code_blocks=[{"code": c} for c in (code or [])],
        text=text,
        last_updated_hint="",
    )


def _detect(pages: list[Any]) -> dict[str, Any]:
    return mod._cross_page_contradictions(pages)


def _types(result: dict[str, Any]) -> list[str]:
    return [c["type"] for c in result["contradictions"]]


class TestAuthScheme:
    def test_bearer_vs_token_across_pages_fires(self) -> None:
        pages = [
            _page("https://d/quickstart", text="Send Authorization: Bearer YOUR_TOKEN"),
            _page("https://d/reference", text="Send Authorization: Token YOUR_TOKEN"),
        ]
        result = _detect(pages)
        assert result["contradictions_count"] == 1
        rec = result["contradictions"][0]
        assert rec["type"] == "auth_scheme"
        assert rec["confidence"] == "high"
        assert rec["summary"] == (
            "Authentication documented two ways: "
            "'Authorization: Bearer' and 'Authorization: Token'"
        )
        urls = {e["url"] for e in rec["evidence"]}
        assert urls == {"https://d/quickstart", "https://d/reference"}
        assert all(e["quote"] for e in rec["evidence"])

    def test_same_page_does_not_fire(self) -> None:
        pages = [
            _page(
                "https://d/auth",
                text="Use Authorization: Bearer or legacy Authorization: Token",
            )
        ]
        assert _detect(pages)["contradictions_count"] == 0

    def test_juxtaposed_page_suppresses(self) -> None:
        # Token page ALSO shows Bearer: the site juxtaposes both, so the claim
        # "two pages disagree" would be refutable. Must not fire.
        pages = [
            _page("https://d/a", text="Authorization: Bearer abc"),
            _page(
                "https://d/b",
                text="Authorization: Token abc but also Authorization: Bearer abc",
            ),
        ]
        assert _detect(pages)["contradictions_count"] == 0

    def test_basic_vs_bearer_does_not_fire(self) -> None:
        pages = [
            _page("https://d/a", text="Authorization: Bearer abc"),
            _page("https://d/b", text="Authorization: Basic abc"),
        ]
        assert _detect(pages)["contradictions_count"] == 0

    def test_bearer_vs_jwt_fires(self) -> None:
        pages = [
            _page("https://d/a", text="Authorization: Bearer abc"),
            _page("https://d/b", text="Authorization: JWT abc"),
        ]
        result = _detect(pages)
        assert _types(result) == ["auth_scheme"]


class TestApiKeyHeader:
    def test_different_header_names_in_code_fire(self) -> None:
        pages = [
            _page("https://d/a", code=['curl -H "X-API-Key: k1" https://api.d/v9/x']),
            _page("https://d/b", code=['curl -H "Api-Key: k1" https://api.d/v9/x']),
        ]
        result = _detect(pages)
        assert _types(result) == ["api_key_header"]
        assert result["contradictions"][0]["confidence"] == "high"

    def test_casing_variants_do_not_fire(self) -> None:
        # Header names are case-insensitive; X-API-Key vs x-api-key is one name.
        pages = [
            _page("https://d/a", code=['curl -H "X-API-Key: k1"']),
            _page("https://d/b", code=['curl -H "x-api-key: k1"']),
        ]
        assert _detect(pages)["contradictions_count"] == 0

    def test_prose_mentions_do_not_fire(self) -> None:
        # This class is code-block-only: prose talks about headers loosely.
        pages = [
            _page("https://d/a", text="Set the X-API-Key: header on each request"),
            _page("https://d/b", text="Set the Api-Key: header on each request"),
        ]
        assert _detect(pages)["contradictions_count"] == 0


class TestApiBaseVersion:
    def test_two_versions_same_host_fire(self) -> None:
        pages = [
            _page("https://d/a", code=["curl https://api.example.com/v1/users"]),
            _page("https://d/b", code=["curl https://api.example.com/v2/users"]),
        ]
        result = _detect(pages)
        assert _types(result) == ["api_base_version"]
        rec = result["contradictions"][0]
        assert rec["confidence"] == "medium"
        assert "api.example.com/v1" in rec["summary"]
        assert "api.example.com/v2" in rec["summary"]

    def test_different_hosts_do_not_fire(self) -> None:
        pages = [
            _page("https://d/a", code=["curl https://api.example.com/v1/users"]),
            _page("https://d/b", code=["curl https://api.other.com/v2/users"]),
        ]
        assert _detect(pages)["contradictions_count"] == 0


class TestDefaultPort:
    def test_conflicting_default_ports_fire(self) -> None:
        pages = [
            _page("https://d/a", text="The default port is 3000 for the server."),
            _page("https://d/b", text="Start it on the default port 8080 as usual."),
        ]
        result = _detect(pages)
        assert _types(result) == ["default_port"]
        assert result["contradictions"][0]["confidence"] == "medium"

    def test_versioned_docs_subtrees_are_isolated(self) -> None:
        # docs.foo.com/2.1/... and /3.0/... are different doc versions: a changed
        # default between major versions is history, not a contradiction.
        pages = [
            _page("https://d/2.1/setup", text="The default port is 3000."),
            _page("https://d/3.0/setup", text="The default port is 8080."),
        ]
        assert _detect(pages)["contradictions_count"] == 0

    def test_same_versioned_subtree_still_fires(self) -> None:
        pages = [
            _page("https://d/2.1/setup", text="The default port is 3000."),
            _page("https://d/2.1/deploy", text="The default port is 8080."),
        ]
        assert _detect(pages)["contradictions_count"] == 1


class TestRateLimit:
    def test_conflicting_rate_limits_fire(self) -> None:
        pages = [
            _page("https://d/a", text="The API rate limit is 60 requests per minute."),
            _page("https://d/b", text="Our rate limits allow 100 requests per minute."),
        ]
        result = _detect(pages)
        assert _types(result) == ["rate_limit"]
        summary = result["contradictions"][0]["summary"]
        assert "60 requests per minute" in summary
        assert "100 requests per minute" in summary

    def test_without_rate_limit_context_does_not_fire(self) -> None:
        pages = [
            _page("https://d/a", text="It can handle 60 requests per minute easily."),
            _page("https://d/b", text="It can handle 100 requests per minute easily."),
        ]
        assert _detect(pages)["contradictions_count"] == 0

    def test_plan_tier_lines_do_not_fire(self) -> None:
        pages = [
            _page("https://d/a", text="Free plan rate limit: 60 requests per minute."),
            _page("https://d/b", text="The rate limit is 100 requests per minute."),
        ]
        assert _detect(pages)["contradictions_count"] == 0

    def test_per_endpoint_lines_do_not_fire(self) -> None:
        pages = [
            _page("https://d/a", text="This endpoint rate limit is 10 requests per second."),
            _page("https://d/b", text="The rate limit is 50 requests per second."),
        ]
        assert _detect(pages)["contradictions_count"] == 0

    def test_different_units_do_not_conflict(self) -> None:
        pages = [
            _page("https://d/a", text="Rate limit: 60 requests per minute."),
            _page("https://d/b", text="Rate limit: 10 requests per second."),
        ]
        assert _detect(pages)["contradictions_count"] == 0


class TestRuntimeMinVersion:
    def test_conflicting_minimums_fire(self) -> None:
        pages = [
            _page("https://d/a", text="This SDK requires Node 18 to run."),
            _page("https://d/b", text="Install Node.js 16 or higher before continuing."),
        ]
        result = _detect(pages)
        assert _types(result) == ["runtime_min_version"]

    def test_equivalent_versions_do_not_fire(self) -> None:
        # 18 and 18.0 are the same minimum.
        pages = [
            _page("https://d/a", text="This SDK requires Node 18 to run."),
            _page("https://d/b", text="Use Node 18.0 or later for the CLI."),
        ]
        assert _detect(pages)["contradictions_count"] == 0

    def test_different_runtimes_do_not_conflict(self) -> None:
        pages = [
            _page("https://d/a", text="The server requires Python 3.10 at minimum."),
            _page("https://d/b", text="The CLI requires Node 18 at minimum."),
        ]
        assert _detect(pages)["contradictions_count"] == 0


class TestSizeLimit:
    def test_conflicting_payload_limits_fire(self) -> None:
        pages = [
            _page("https://d/a", text="The maximum payload size is 16 MB."),
            _page("https://d/b", text="Payloads are limited to 10 MB."),
        ]
        result = _detect(pages)
        assert _types(result) == ["size_limit"]
        summary = result["contradictions"][0]["summary"]
        assert "16 MB" in summary
        assert "10 MB" in summary

    def test_plan_tier_limits_do_not_fire(self) -> None:
        pages = [
            _page("https://d/a", text="Free plan: payloads are limited to 10 MB."),
            _page("https://d/b", text="The maximum payload size is 16 MB."),
        ]
        assert _detect(pages)["contradictions_count"] == 0

    def test_different_subjects_do_not_conflict(self) -> None:
        pages = [
            _page("https://d/a", text="The maximum payload size is 16 MB."),
            _page("https://d/b", text="The maximum file size is 25 MB."),
        ]
        assert _detect(pages)["contradictions_count"] == 0


class TestGlobalGuardsAndShape:
    def test_archival_pages_are_skipped(self) -> None:
        pages = [
            _page("https://d/docs/auth", text="Authorization: Bearer abc"),
            _page("https://d/blog/migrating", text="Authorization: Token abc"),
        ]
        assert _detect(pages)["contradictions_count"] == 0

    def test_high_confidence_sorts_first_and_counts(self) -> None:
        pages = [
            _page(
                "https://d/a",
                text="The default port is 3000. Use Authorization: Bearer abc",
            ),
            _page(
                "https://d/b",
                text="The default port is 8080. Use Authorization: Token abc",
            ),
        ]
        result = _detect(pages)
        assert result["contradictions_count"] == 2
        assert _types(result) == ["auth_scheme", "default_port"]
        assert result["by_confidence"] == {"high": 1, "medium": 1}

    def test_empty_input_shape(self) -> None:
        result = _detect([])
        assert result == {
            "pages_scanned": 0,
            "contradictions_count": 0,
            "by_confidence": {},
            "contradictions": [],
        }

    def test_pages_scanned_counts_all_pages(self) -> None:
        pages = [
            _page("https://d/a", text="nothing here"),
            _page("https://d/blog/x", text="nothing here either"),
        ]
        assert _detect(pages)["pages_scanned"] == 2

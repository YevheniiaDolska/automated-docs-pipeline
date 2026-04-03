from __future__ import annotations

import http.client
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class _Resp:
    def __init__(self, *, status: int = 200, ct: str = "text/html", body: bytes = b"", headers: dict[str, str] | None = None, raise_incomplete: bool = False) -> None:
        self.status = status
        self._body = body
        self.headers = headers or {"Content-Type": ct}
        self._raise_incomplete = raise_incomplete

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        if self._raise_incomplete:
            raise http.client.IncompleteRead(self._body, 10)
        return self._body


def _mk_page(
    mod,
    *,
    url: str,
    title: str,
    text: str,
    code_blocks: list[dict[str, str]] | None = None,
    internal_links: list[str] | None = None,
):
    return mod.PageData(
        url=url,
        status=200,
        title=title,
        meta_description="",
        h1_count=1,
        heading_levels=[1, 2],
        internal_links=internal_links or [],
        external_links=[],
        code_blocks=code_blocks or [],
        text=text,
        last_updated_hint="",
        internal_link_refs=[],
    )


def test_fetch_handles_incomplete_and_gzip(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import generate_public_docs_audit as mod

    body = b"<html><title>x</title></html>"
    monkeypatch.setattr(mod, "urlopen", lambda req, timeout=10: _Resp(body=body, raise_incomplete=True))
    st, ct, text = mod._fetch("https://example.com", timeout=5)
    assert st == 200
    assert "html" in text

    # gzip path via magic bytes
    import gzip

    gz = gzip.compress(b"hello")
    monkeypatch.setattr(mod, "urlopen", lambda req, timeout=10: _Resp(body=gz))
    st2, _, text2 = mod._fetch("https://example.com/file.gz", timeout=5)
    assert st2 == 200
    assert "hello" in text2


def test_structured_contract_parsing_and_source_of_truth(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import generate_public_docs_audit as mod

    html = "<html><body>not contract</body></html>"
    assert mod._parse_structured_contract_identifiers(html) == set()

    yaml_text = """
openapi: 3.1.0
paths:
  /v1/projects:
    get:
      operationId: listProjects
channels:
  task.updated: {}
services:
  - methods:
      - name: Health
"""
    ids = mod._parse_structured_contract_identifiers(yaml_text)
    assert "ep:/v1/projects" in ids
    assert "op:listprojects" in ids
    assert "ch:task.updated" in ids
    assert "rpc:health" in ids

    page = _mk_page(mod, url="https://example.com/docs", title="API", text="See /openapi.json", code_blocks=[])
    monkeypatch.setattr(mod, "_discover_contract_urls", lambda pages: ["https://example.com/openapi.json"])
    monkeypatch.setattr(mod, "_fetch", lambda url, timeout, extra_headers=None: (200, "application/json", json.dumps({"paths": {"/v1/a": {"get": {"operationId": "listA"}}}})))

    source_ids, note = mod._source_of_truth_identifiers([page], timeout=5, auth_headers={})
    assert not note
    assert "ep:/v1/a" in source_ids
    assert "op:lista" in source_ids


def test_api_coverage_and_link_health_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import generate_public_docs_audit as mod

    p_api = _mk_page(
        mod,
        url="https://example.com/reference/api",
        title="API ref",
        text='GET /v1/projects operationId: listProjects',
        code_blocks=[{"code": "POST /v1/projects"}],
    )
    p_guide = _mk_page(
        mod,
        url="https://example.com/guides/start",
        title="Guide",
        text='call /v1/projects and use listProjects',
        code_blocks=[],
    )

    monkeypatch.setattr(mod, "_source_of_truth_identifiers", lambda pages, timeout, auth_headers=None: ({"ep:/v1/projects", "op:listprojects"}, ""))
    cov = mod._api_coverage_from_public_docs([p_api, p_guide], timeout=5, auth_headers={})
    assert cov["coverage_method"] == "source_of_truth"
    assert cov["reference_coverage_pct"] >= 0

    # link health export path
    pages = [
        _mk_page(
            mod,
            url="https://example.com/p1",
            title="p1",
            text="[x](https://example.com/a)",
            code_blocks=[],
            internal_links=["https://example.com/a"],
        ),
        _mk_page(
            mod,
            url="https://example.com/p2",
            title="p2",
            text="[x](https://example.com/b)",
            code_blocks=[],
            internal_links=["https://example.com/b"],
        ),
    ]
    status_map = {"https://example.com/a": 404, "https://example.com/b": 200}
    health = mod._link_health(pages, status_map)
    assert health["broken_internal_links_count"] == 1

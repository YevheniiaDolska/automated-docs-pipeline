from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib import error

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class _Resp:
    def __init__(self, body: bytes = b"{}", code: int = 200, content_type: str = "application/json") -> None:
        self._body = body
        self.status = code
        self.headers = {"Content-Type": content_type}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._body


def _args(**overrides):
    base = {
        "postman_api_key_env": "POSTMAN_API_KEY",
        "postman_mock_server_id_env": "POSTMAN_MOCK_SERVER_ID",
        "postman_workspace_id_env": "POSTMAN_WORKSPACE_ID",
        "postman_collection_uid_env": "POSTMAN_COLLECTION_UID",
        "postman_mock_server_name": "",
        "postman_private": False,
        "project_slug": "acme",
        "spec_path": "",
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def test_http_json_error_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import ensure_external_mock_server as mod

    # HTTPError branch
    class _HttpErr(error.HTTPError):
        def __init__(self):
            super().__init__("https://x", 500, "boom", hdrs=None, fp=None)

        def read(self) -> bytes:
            return b"failed"

    monkeypatch.setattr(mod.request, "urlopen", lambda *a, **k: (_ for _ in ()).throw(_HttpErr()))
    with pytest.raises(RuntimeError):
        mod._http_json("GET", "https://x", api_key="k")

    # URLError branch
    monkeypatch.setattr(mod.request, "urlopen", lambda *a, **k: (_ for _ in ()).throw(error.URLError("offline")))
    with pytest.raises(RuntimeError):
        mod._http_json("GET", "https://x", api_key="k")

    # Non-dict JSON branch
    monkeypatch.setattr(mod.request, "urlopen", lambda *a, **k: _Resp(body=b"[]"))
    with pytest.raises(RuntimeError):
        mod._http_json("GET", "https://x", api_key="k")


def test_resolve_collection_id_fallbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import ensure_external_mock_server as mod

    monkeypatch.setattr(mod, "_http_json", lambda *a, **k: (_ for _ in ()).throw(OSError("x")))
    assert mod._resolve_collection_id("https://api.getpostman.com", "k", "uid-1") == "uid-1"

    monkeypatch.setattr(mod, "_http_json", lambda *a, **k: {"collection": {"info": {"id": "resolved"}}})
    assert mod._resolve_collection_id("https://api.getpostman.com", "k", "uid-2") == "resolved"


def test_find_existing_mock_by_name_and_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import ensure_external_mock_server as mod

    def _fail(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("no endpoint")

    monkeypatch.setattr(mod, "_http_json", _fail)
    assert mod._find_existing_mock_by_name("https://api.getpostman.com", "k", "w", "acme-mock") is None

    payload = {"mocks": [{"name": "acme-mock", "id": "m1", "url": "https://mock.example.com"}]}
    monkeypatch.setattr(mod, "_http_json", lambda *a, **k: payload)
    found = mod._find_existing_mock_by_name("https://api.getpostman.com", "k", "w", "Acme-Mock")
    assert found == {"mock_server_id": "m1", "mock_url": "https://mock.example.com"}


def test_resolve_postman_mock_workspace_preflight_and_spec_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import ensure_external_mock_server as mod

    monkeypatch.setenv("POSTMAN_API_KEY", "k")
    monkeypatch.setenv("POSTMAN_WORKSPACE_ID", "w")
    monkeypatch.delenv("POSTMAN_MOCK_SERVER_ID", raising=False)
    monkeypatch.delenv("POSTMAN_COLLECTION_UID", raising=False)

    args = _args(spec_path="")
    monkeypatch.setattr(mod, "_http_json", lambda *a, **k: {"workspace": {"id": "w"}})
    with pytest.raises(RuntimeError, match="POSTMAN_COLLECTION_UID is not set"):
        mod._resolve_postman_mock(args)

    args_missing_spec = _args(spec_path=str(tmp_path / "missing.yaml"))
    with pytest.raises(RuntimeError, match="Spec file for Postman import not found"):
        mod._resolve_postman_mock(args_missing_spec)

    def _workspace_fail(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("forbidden")

    monkeypatch.setattr(mod, "_http_json", _workspace_fail)
    with pytest.raises(RuntimeError, match="workspace preflight failed"):
        mod._resolve_postman_mock(_args(spec_path=str(tmp_path / "missing.yaml")))


def test_resolve_postman_mock_creation_attempts_then_reuse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import ensure_external_mock_server as mod

    spec = tmp_path / "openapi.yaml"
    spec.write_text("openapi: 3.0.3\ninfo:\n  title: API\n  version: 1.0.0\npaths: {}\n", encoding="utf-8")

    monkeypatch.setenv("POSTMAN_API_KEY", "k")
    monkeypatch.setenv("POSTMAN_WORKSPACE_ID", "w")
    monkeypatch.setenv("POSTMAN_COLLECTION_UID", "uid")
    monkeypatch.delenv("POSTMAN_MOCK_SERVER_ID", raising=False)

    attempts: list[str] = []

    def _fake_http(method: str, url: str, **kwargs):  # type: ignore[no-untyped-def]
        attempts.append(url)
        if "/workspaces/" in url:
            return {"workspace": {"id": "w"}}
        if "/collections/" in url and method == "GET":
            return {"collection": {"info": {"_postman_id": "col-id"}}}
        if any(seg in url for seg in ["/mocks", "/mockservers", "/mock-servers"]) and method == "POST":
            raise RuntimeError("create failed")
        return {}

    monkeypatch.setattr(mod, "_http_json", _fake_http)
    monkeypatch.setattr(
        mod,
        "_find_existing_mock_by_name",
        lambda *a, **k: {"mock_server_id": "reuse-1", "mock_url": "https://reuse.example.com"},
    )
    out = mod._resolve_postman_mock(_args(spec_path=str(spec)))
    assert out["mock_server_id"] == "reuse-1"
    assert any("/mocks" in url or "/mockservers" in url for url in attempts)


def test_main_unsupported_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import ensure_external_mock_server as mod

    monkeypatch.setattr(
        sys,
        "argv",
        ["x", "--provider", "invalid", "--project-slug", "acme"],
    )
    with pytest.raises(RuntimeError):
        mod.main()

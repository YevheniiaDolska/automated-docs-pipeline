from __future__ import annotations

import base64
import json
import sys
import types
from pathlib import Path

import jwt
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "packages" / "core") not in sys.path:
    sys.path.insert(0, str(ROOT / "packages" / "core"))


class _Req:
    def __init__(self, host: str = "127.0.0.1") -> None:
        self.client = types.SimpleNamespace(host=host)


class _FakeQuery:
    def __init__(self, user: object | None) -> None:
        self._user = user

    def filter(self, *_a, **_k):
        return self

    def first(self):
        return self._user


class _FakeDB:
    def __init__(self, user: object | None) -> None:
        self._user = user

    def query(self, *_a, **_k):
        return _FakeQuery(self._user)


def _settings(secret: str = "secret"):
    from pydantic import SecretStr

    return types.SimpleNamespace(secret_key=SecretStr(secret))


def test_get_current_user_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi import HTTPException
    from gitspeak_core.api import app as mod

    req = _Req()

    with pytest.raises(HTTPException):
        mod.get_current_user(req, authorization=None, settings=_settings(), db=_FakeDB(None))

    big_token = "x" * (mod.MAX_TOKEN_LENGTH_BYTES + 1)
    with pytest.raises(HTTPException):
        mod.get_current_user(req, authorization=f"Bearer {big_token}", settings=_settings(), db=_FakeDB(None))

    monkeypatch.setattr("gitspeak_core.api.auth.decode_access_token", lambda *a, **k: (_ for _ in ()).throw(jwt.ExpiredSignatureError("exp")))
    with pytest.raises(HTTPException):
        mod.get_current_user(req, authorization="Bearer t", settings=_settings(), db=_FakeDB(None))

    monkeypatch.setattr("gitspeak_core.api.auth.decode_access_token", lambda *a, **k: (_ for _ in ()).throw(jwt.InvalidTokenError("bad")))
    with pytest.raises(HTTPException):
        mod.get_current_user(req, authorization="Bearer t", settings=_settings(), db=_FakeDB(None))

    monkeypatch.setattr("gitspeak_core.api.auth.decode_access_token", lambda *a, **k: {})
    with pytest.raises(HTTPException):
        mod.get_current_user(req, authorization="Bearer t", settings=_settings(), db=_FakeDB(None))

    monkeypatch.setattr("gitspeak_core.api.auth.decode_access_token", lambda *a, **k: {"sub": "u1"})
    with pytest.raises(HTTPException):
        mod.get_current_user(req, authorization="Bearer t", settings=_settings(), db=_FakeDB(None))

    user = types.SimpleNamespace(id="u1", email="u1@example.com", is_active=True, is_superuser=False, subscription=types.SimpleNamespace(tier="pro"))
    out = mod.get_current_user(req, authorization="Bearer t", settings=_settings(), db=_FakeDB(user))
    assert out["user_id"] == "u1"
    assert out["tier"] == "pro"


def test_rate_limit_and_ops_token(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi import HTTPException
    from gitspeak_core.api import app as mod

    mod._rate_limit_store.clear()
    user = {"user_id": "u-rate", "tier": "free"}
    mod.check_rate_limit(user)
    assert len(mod._rate_limit_store["u-rate"]) == 1

    mod._rate_limit_store["u-rate"] = [123.0] * mod.TIER_RATE_LIMITS["free"]
    monkeypatch.setattr(mod.time, "time", lambda: 123.0)
    with pytest.raises(HTTPException):
        mod.check_rate_limit(user)

    monkeypatch.delenv("VERIOPS_SERVER_SHARED_TOKEN", raising=False)
    with pytest.raises(HTTPException):
        mod._require_ops_token("x")

    monkeypatch.setenv("VERIOPS_SERVER_SHARED_TOKEN", "expected")
    with pytest.raises(HTTPException):
        mod._require_ops_token("wrong")
    mod._require_ops_token("expected")


def test_key_loading_signature_allowlist_and_revocation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from gitspeak_core.api import app as mod

    key_path = tmp_path / "pub.key"
    monkeypatch.setattr(mod, "PACK_REGISTRY_PUBLIC_KEY_PATH", key_path)
    assert mod._load_pack_registry_public_key() is None

    raw = b"a" * 32
    key_path.write_bytes(raw)
    assert mod._load_pack_registry_public_key() == raw

    b64 = base64.b64encode(raw)
    key_path.write_bytes(b64)
    assert mod._load_pack_registry_public_key() == raw

    key_path.write_bytes(b"bad")
    assert mod._load_pack_registry_public_key() is None

    assert mod._verify_ed25519_signature(b"m", b"s", b"k") is False

    allow_path = tmp_path / "allow.yml"
    monkeypatch.setattr(mod, "EGRESS_ALLOWLIST_PATH", allow_path)
    allowed, blocked = mod._load_egress_allowlist()
    assert "tenant_id" in allowed

    allow_path.write_text(
        "allowed_fields:\n  - tenant_id\n  - build_id\nblocked_key_patterns:\n  - content\n",
        encoding="utf-8",
    )
    allowed2, blocked2 = mod._load_egress_allowlist()
    assert allowed2 == {"tenant_id", "build_id"}
    assert blocked2 == ["content"]

    ok, reason = mod._validate_metadata_payload({"tenant_id": "t", "build_id": "b"})
    assert ok is True and reason == "ok"
    bad, reason2 = mod._validate_metadata_payload({"tenant_id": "t", "content": "x"})
    assert bad is False and reason2.startswith("field_not_allowed")

    rev_path = tmp_path / "revocation" / "list.json"
    monkeypatch.setattr(mod, "REVOCATION_LIST_PATH", rev_path)
    assert mod._load_revocation_list() == {}
    mod._save_revocation_list({"revoked": ["x"]})
    assert mod._load_revocation_list() == {"revoked": ["x"]}
    rev_path.write_text("{", encoding="utf-8")
    assert mod._load_revocation_list() == {}


def test_init_sentry_and_get_db_and_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    from gitspeak_core.api import app as mod

    # no dsn => no-op
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    mod._init_sentry()

    # success path with fake module
    called: list[dict] = []

    class _Sentry:
        @staticmethod
        def init(**kwargs):
            called.append(kwargs)

    monkeypatch.setenv("SENTRY_DSN", "https://dsn")
    monkeypatch.setenv("VERIDOC_ENVIRONMENT", "production")
    monkeypatch.setitem(sys.modules, "sentry_sdk", _Sentry)
    mod._init_sentry()
    assert called and called[0]["environment"] == "production"

    # runtime error path
    class _SentryErr:
        @staticmethod
        def init(**kwargs):
            raise RuntimeError("boom")

    monkeypatch.setitem(sys.modules, "sentry_sdk", _SentryErr)
    mod._init_sentry()

    # get_settings cache path
    monkeypatch.setenv("VERIDOC_SECRET_KEY", "test-secret-for-unit-tests")
    mod._settings = None
    s1 = mod.get_settings()
    s2 = mod.get_settings()
    assert s1 is s2

    # get_db close path
    closed = {"v": False}

    class _Session:
        def close(self):
            closed["v"] = True

    monkeypatch.setattr("gitspeak_core.db.engine.get_session", lambda: _Session())
    gen = mod.get_db()
    _ = next(gen)
    with pytest.raises(StopIteration):
        next(gen)
    assert closed["v"] is True

from __future__ import annotations

import hashlib
import hmac
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "packages" / "core") not in sys.path:
    sys.path.insert(0, str(ROOT / "packages" / "core"))


@pytest.fixture
def db_session():
    from gitspeak_core.db.models import create_all_tables

    engine = create_engine("sqlite:///:memory:", echo=False)
    create_all_tables(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def _mk_user(db_session, user_id: str = "u1", email: str = "u1@example.com"):
    from gitspeak_core.db.models import User

    user = User(
        id=user_id,
        email=email,
        hashed_password="hash",
        full_name="User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_manual_subscription_upsert_valid_and_errors(db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    from gitspeak_core.api import billing as mod
    from gitspeak_core.db.models import Subscription

    user = _mk_user(db_session, "u-manual", "m@example.com")
    calls: list[str] = []
    monkeypatch.setattr(mod, "_issue_or_refresh_server_license", lambda *a, **k: calls.append("issued"))

    result = mod.handle_manual_subscription_upsert(
        {
            "user_id": user.id,
            "tier": "pro",
            "status": "active",
            "period_days": 30,
            "source": "manual_invoice",
            "external_customer_ref": "cust_1",
        },
        db_session,
    )
    assert result["status"] == "ok"
    assert result["tier"] == "pro"
    assert calls == ["issued"]

    sub = db_session.query(Subscription).filter(Subscription.user_id == user.id).first()
    assert sub is not None
    assert sub.ls_customer_id == "cust_1"

    with pytest.raises(ValueError):
        mod.handle_manual_subscription_upsert({}, db_session)
    with pytest.raises(ValueError):
        mod.handle_manual_subscription_upsert({"user_id": user.id, "tier": "bad"}, db_session)
    with pytest.raises(ValueError):
        mod.handle_manual_subscription_upsert({"user_id": user.id, "tier": "pro", "status": "weird"}, db_session)
    with pytest.raises(ValueError):
        mod.handle_manual_subscription_upsert({"user_id": user.id, "tier": "pro", "period_days": "x"}, db_session)
    with pytest.raises(ValueError):
        mod.handle_manual_subscription_upsert({"user_id": user.id, "tier": "pro", "period_days": 0}, db_session)
    with pytest.raises(ValueError):
        mod.handle_manual_subscription_upsert({"user_id": "missing", "tier": "pro"}, db_session)


def test_verify_manual_webhook_signature_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    from gitspeak_core.api import billing as mod

    payload = b'{"x":1}'
    assert mod.verify_manual_billing_webhook_signature(payload, "", secret="abc") is False
    assert mod.verify_manual_billing_webhook_signature(payload, "sig", secret="") is False

    secret = "manual-secret"
    sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    assert mod.verify_manual_billing_webhook_signature(payload, sig, secret=secret) is True


def test_resolve_manual_user_id_by_all_methods(db_session) -> None:
    from gitspeak_core.api import billing as mod
    from gitspeak_core.db.models import Subscription

    user = _mk_user(db_session, "u-resolve", "resolve@example.com")
    sub = Subscription(
        user_id=user.id,
        tier="starter",
        status="active",
        ls_customer_id="cust-xyz",
        current_period_start=datetime.now(timezone.utc),
        current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(sub)
    db_session.commit()

    assert mod._resolve_manual_webhook_user_id({"user_id": user.id}, db_session) == user.id
    assert mod._resolve_manual_webhook_user_id({"email": "resolve@example.com"}, db_session) == user.id
    assert mod._resolve_manual_webhook_user_id({"external_customer_ref": "cust-xyz"}, db_session) == user.id
    assert mod._resolve_manual_webhook_user_id({"email": "none@example.com"}, db_session) == ""


def test_manual_billing_webhook_event_routing(db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    from gitspeak_core.api import billing as mod

    user = _mk_user(db_session, "u-webhook", "webhook@example.com")
    monkeypatch.setattr(mod, "_resolve_manual_webhook_user_id", lambda payload, db: user.id)
    monkeypatch.setattr(mod, "handle_manual_subscription_upsert", lambda payload, db: {"ok": True, "payload": payload})

    active = mod.handle_manual_billing_webhook("payment_success", {"tier": "pro"}, db_session)
    assert active["status"] == "ok"
    assert active["result"]["payload"]["status"] == "active"

    failed = mod.handle_manual_billing_webhook("invoice_failed", {"tier": "starter"}, db_session)
    assert failed["result"]["payload"]["status"] == "past_due"

    cancelled = mod.handle_manual_billing_webhook("access_revoked", {"tier": "business"}, db_session)
    assert cancelled["result"]["payload"]["tier"] == "free"

    ignored = mod.handle_manual_billing_webhook("unknown_event", {}, db_session)
    assert ignored["status"] == "ignored"

    monkeypatch.setattr(mod, "_resolve_manual_webhook_user_id", lambda payload, db: "")
    no_user = mod.handle_manual_billing_webhook("payment_success", {}, db_session)
    assert no_user["reason"] == "user_not_resolved"


def test_license_status_and_token_branches(db_session, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from gitspeak_core.api import billing as mod
    from gitspeak_core.db.models import Subscription

    user = _mk_user(db_session, "u-license", "lic@example.com")
    sub = Subscription(
        user_id=user.id,
        tier="pro",
        status="active",
        current_period_start=datetime.now(timezone.utc),
        current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(sub)
    db_session.commit()

    monkeypatch.setattr(mod, "LICENSE_STORE_DIR", tmp_path)

    # Missing files branch
    status_missing = mod.handle_get_server_license_status(user.id, db_session)
    assert status_missing.enabled is True
    assert status_missing.has_license is False

    # Invalid JSON metadata branch
    user_dir = tmp_path / user.id
    user_dir.mkdir(parents=True, exist_ok=True)
    lic_path = user_dir / "license.jwt"
    meta_path = user_dir / "license_meta.json"
    lic_path.write_text("token-123\n", encoding="utf-8")
    meta_path.write_text("{", encoding="utf-8")
    status_bad_meta = mod.handle_get_server_license_status(user.id, db_session)
    assert status_bad_meta.has_license is True

    # Valid metadata branch
    meta_path.write_text(
        json.dumps({"expires_at": "x", "tier": "pro", "status": "active", "reason": "ok", "issued_at": "now"}),
        encoding="utf-8",
    )
    status_ok = mod.handle_get_server_license_status(user.id, db_session)
    assert status_ok.has_license is True
    assert status_ok.tier == "pro"

    token_ok = mod.handle_get_server_license_token(user.id, db_session)
    assert token_ok.has_license is True
    assert token_ok.token == "token-123"

    lic_path.write_text("\n", encoding="utf-8")
    token_empty = mod.handle_get_server_license_token(user.id, db_session)
    assert token_empty.has_license is False

    # Global disabled branch
    monkeypatch.setattr(mod, "LICENSE_AUTORENEW_ENABLED", False)
    disabled = mod.handle_get_server_license_status(user.id, db_session)
    assert disabled.enabled is False


def test_license_status_raises_without_subscription(db_session) -> None:
    from gitspeak_core.api import billing as mod

    user = _mk_user(db_session, "u-no-sub", "nosub@example.com")
    with pytest.raises(ValueError):
        mod.handle_get_server_license_status(user.id, db_session)


def test_license_token_requires_active_subscription(db_session, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from gitspeak_core.api import billing as mod
    from gitspeak_core.db.models import Subscription

    user = _mk_user(db_session, "u-inactive", "inactive@example.com")
    sub = Subscription(
        user_id=user.id,
        tier="pro",
        status="canceled",
        current_period_start=datetime.now(timezone.utc),
        current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(sub)
    db_session.commit()

    monkeypatch.setattr(mod, "LICENSE_STORE_DIR", tmp_path)
    user_dir = tmp_path / user.id
    user_dir.mkdir(parents=True, exist_ok=True)
    (user_dir / "license.jwt").write_text("token-123\n", encoding="utf-8")
    (user_dir / "license_meta.json").write_text(json.dumps({"expires_at": "2099-01-01T00:00:00+00:00"}), encoding="utf-8")

    token_resp = mod.handle_get_server_license_token(user.id, db_session)
    assert token_resp.has_license is False


def test_license_autorenew_batch_counts(db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    from gitspeak_core.api import billing as mod
    from gitspeak_core.db.models import Subscription

    u1 = _mk_user(db_session, "u-batch-1", "b1@example.com")
    u2 = _mk_user(db_session, "u-batch-2", "b2@example.com")
    db_session.add_all(
        [
            Subscription(
                user_id=u1.id,
                tier="pro",
                status="active",
                current_period_start=datetime.now(timezone.utc),
                current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
            ),
            Subscription(
                user_id=u2.id,
                tier="pro",
                status="canceled",
                current_period_start=datetime.now(timezone.utc),
                current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
            ),
        ]
    )
    db_session.commit()

    seen: list[str] = []

    def _fake_issue(sub: Any, reason: str, db_session: Any) -> None:
        seen.append(reason)

    monkeypatch.setattr(mod, "_issue_or_refresh_server_license", _fake_issue)
    result = mod.run_license_autorenew_batch(db_session)
    assert result["scanned"] == 2
    assert result["refreshed"] == 1
    assert result["degraded"] == 1
    assert result["errors"] == 0
    assert "batch_autorenew_active" in seen
    assert "batch_autorenew_inactive" in seen

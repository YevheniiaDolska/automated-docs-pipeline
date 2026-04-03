from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

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


def _mk_user(db_session, user_id: str, email: str):
    from gitspeak_core.db.models import User

    user = User(id=user_id, email=email, hashed_password="hash", full_name=user_id, is_active=True)
    db_session.add(user)
    db_session.commit()
    return user


def _mk_subscription(db_session, user_id: str, ls_sub_id: str = "sub_1", tier: str = "pro"):
    from gitspeak_core.db.models import Subscription

    sub = Subscription(
        user_id=user_id,
        tier=tier,
        status="active",
        ls_subscription_id=ls_sub_id,
        ls_variant_id="variant_pro_monthly",
        current_period_start=datetime.now(timezone.utc),
        current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(sub)
    db_session.commit()
    return sub


def test_subscription_created_and_updated_paths(db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    from gitspeak_core.api import billing as mod
    from gitspeak_core.db.models import ReferralAttribution, ReferralProfile, Subscription

    monkeypatch.setattr(mod, "_issue_or_refresh_server_license", lambda *a, **k: None)
    monkeypatch.setattr(mod, "VARIANT_TO_TIER", {"var_pro": "pro", "var_business": "business"})

    referred = _mk_user(db_session, "u_referred", "referred@example.com")
    referrer = _mk_user(db_session, "u_referrer", "referrer@example.com")
    _mk_subscription(db_session, referred.id, ls_sub_id="sub_created", tier="free")

    created_event = {
        "id": "sub_created",
        "attributes": {
            "variant_id": "var_pro",
            "status": "active",
            "customer_id": "cust_1",
            "created_at": "2026-03-01T12:00:00Z",
            "renews_at": "2026-04-01T12:00:00Z",
            "first_subscription_item": {
                "custom": {
                    "veridoc_user_id": referred.id,
                    "veridoc_referrer_user_id": referrer.id,
                    "veridoc_referral_code": "REF123",
                }
            },
        },
    }
    mod._on_subscription_created(created_event, db_session)

    sub = db_session.query(Subscription).filter(Subscription.user_id == referred.id).first()
    assert sub is not None
    assert sub.tier == "pro"
    assert sub.ls_customer_id == "cust_1"

    profile = db_session.query(ReferralProfile).filter(ReferralProfile.user_id == referred.id).first()
    assert profile is not None

    attr = db_session.query(ReferralAttribution).filter(ReferralAttribution.referred_user_id == referred.id).first()
    assert attr is not None
    assert attr.referrer_user_id == referrer.id

    # update path + tier change log branch
    updated_event = {
        "id": "sub_created",
        "attributes": {
            "variant_id": "var_business",
            "status": "active",
            "renews_at": "2026-05-01T12:00:00Z",
            "cancelled": True,
        },
    }
    mod._on_subscription_updated(updated_event, db_session)
    sub2 = db_session.query(Subscription).filter(Subscription.user_id == referred.id).first()
    assert sub2 is not None
    assert sub2.tier == "business"
    assert sub2.cancel_at_period_end is True


def test_subscription_status_event_handlers(db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    from gitspeak_core.api import billing as mod
    from gitspeak_core.db.models import Subscription

    monkeypatch.setattr(mod, "_issue_or_refresh_server_license", lambda *a, **k: None)
    user = _mk_user(db_session, "u_status", "status@example.com")
    _mk_subscription(db_session, user.id, ls_sub_id="sub_status", tier="pro")

    mod._on_subscription_cancelled({"id": "sub_status", "attributes": {"status": "cancelled"}}, db_session)
    sub = db_session.query(Subscription).filter(Subscription.user_id == user.id).first()
    assert sub is not None and sub.cancel_at_period_end is True

    mod._on_subscription_paused({"id": "sub_status"}, db_session)
    sub = db_session.query(Subscription).filter(Subscription.user_id == user.id).first()
    assert sub is not None and sub.status == "paused"

    mod._on_subscription_resumed({"id": "sub_status"}, db_session)
    sub = db_session.query(Subscription).filter(Subscription.user_id == user.id).first()
    assert sub is not None
    assert sub.status == "active"
    assert sub.cancel_at_period_end is False


def test_trial_ending_and_payment_handlers(db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    from gitspeak_core.api import billing as mod
    from gitspeak_core.db.models import ReferralAttribution, ReferralLedgerEntry, ReferralProfile, Subscription

    monkeypatch.setattr(mod, "_issue_or_refresh_server_license", lambda *a, **k: None)
    monkeypatch.setattr(mod, "_send_email", lambda **kwargs: True)
    monkeypatch.setattr(mod, "_extract_payment_amount_cents", lambda attrs, tier: 10000)

    referred = _mk_user(db_session, "u_pay", "pay@example.com")
    referrer = _mk_user(db_session, "u_pay_ref", "payref@example.com")

    sub = _mk_subscription(db_session, referred.id, ls_sub_id="sub_pay", tier="pro")
    ref_sub = _mk_subscription(db_session, referrer.id, ls_sub_id="sub_ref", tier="business")
    ref_sub.status = "active"

    profile = ReferralProfile(user_id=referrer.id, referral_code="CODEX", badge_opt_out=False)
    db_session.add(profile)
    db_session.flush()

    attr = ReferralAttribution(referrer_user_id=referrer.id, referred_user_id=referred.id, source="checkout", referral_code="CODEX")
    db_session.add(attr)
    db_session.commit()

    # trial ending notification
    mod._on_trial_ending(
        {
            "id": "sub_pay",
            "attributes": {
                "trial_ends_at": "2026-04-01T12:00:00Z",
            },
        },
        db_session,
    )

    # payment success with commission accrual
    mod._on_payment_success(
        {
            "id": "evt_pay_1",
            "attributes": {
                "subscription_id": "sub_pay",
                "order_id": "ord_1",
                "currency": "usd",
                "updated_at": "2026-04-01T13:00:00Z",
            },
        },
        db_session,
    )

    sub2 = db_session.query(Subscription).filter(Subscription.user_id == referred.id).first()
    assert sub2 is not None
    assert sub2.ai_requests_used == 0
    assert sub2.status == "active"

    ledger = db_session.query(ReferralLedgerEntry).filter(ReferralLedgerEntry.subscription_id == "sub_pay").first()
    assert ledger is not None
    assert ledger.amount_cents > 0

    # duplicate payment event does not create second ledger
    mod._on_payment_success(
        {
            "id": "evt_pay_1",
            "attributes": {"subscription_id": "sub_pay", "order_id": "ord_1", "currency": "usd"},
        },
        db_session,
    )
    count = db_session.query(ReferralLedgerEntry).filter(ReferralLedgerEntry.subscription_id == "sub_pay").count()
    assert count == 1

    # payment failed + refunded paths
    mod._on_payment_failed({"attributes": {"subscription_id": "sub_pay"}}, db_session)
    sub3 = db_session.query(Subscription).filter(Subscription.user_id == referred.id).first()
    assert sub3 is not None and sub3.status == "past_due"

    ledger.status = "accrued"
    db_session.commit()
    mod._on_payment_refunded({"id": "evt_refund", "attributes": {"subscription_id": "sub_pay"}}, db_session)
    db_session.refresh(ledger)
    assert ledger.status == "reversed"


def test_handle_webhook_dispatch_smoke(db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    from gitspeak_core.api import billing as mod

    events: list[str] = []
    monkeypatch.setattr(mod, "_on_subscription_created", lambda data, db: events.append("created"))
    monkeypatch.setattr(mod, "_on_subscription_updated", lambda data, db: events.append("updated"))

    assert mod.handle_webhook("subscription_created", {"x": 1}, db_session)["status"] == "ok"
    assert mod.handle_webhook("subscription_updated", {"x": 1}, db_session)["status"] == "ok"
    assert mod.handle_webhook("unknown_event", {}, db_session)["status"] == "ignored"
    assert events == ["created", "updated"]

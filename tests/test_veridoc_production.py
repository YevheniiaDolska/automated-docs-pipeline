"""Comprehensive tests for VeriDoc SaaS production infrastructure.

Tests cover:
- Database models and relationships
- JWT auth (register, login, token validation)
- Pipeline settings CRUD with tier gating
- Billing (LemonSqueezy) usage tracking and quota enforcement
- Automation schedules
- Audit logging
- Rate limiting
- LLM executor (GSD pattern)
- Celery task configuration
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure packages are importable
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "packages" / "core"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def db_engine():
    """Create an in-memory SQLite engine for testing."""
    from sqlalchemy import create_engine

    engine = create_engine("sqlite:///:memory:", echo=False)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Create a test database session with all tables."""
    from sqlalchemy.orm import sessionmaker

    from gitspeak_core.db.models import Base, create_all_tables

    create_all_tables(db_engine)
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user with subscription."""
    from gitspeak_core.db.models import Subscription, User

    user = User(
        id="test_user_001",
        email="test@veridoc.dev",
        hashed_password="pbkdf2:sha256:260000$" + "aa" * 32 + "$" + "bb" * 32,
        full_name="Test User",
    )
    db_session.add(user)
    db_session.flush()

    sub = Subscription(
        user_id=user.id,
        tier="pro",
        status="active",
        trial_ends_at=datetime.now(timezone.utc) + timedelta(days=14),
        current_period_start=datetime.now(timezone.utc),
        current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
        ai_requests_limit=2000,
    )
    db_session.add(sub)
    db_session.commit()
    return user


# =========================================================================
# Database Models Tests
# =========================================================================


class TestDatabaseModels:
    """Test SQLAlchemy ORM models and relationships."""

    def test_create_user(self, db_session):
        from gitspeak_core.db.models import User

        user = User(email="new@test.com", hashed_password="hash123")
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert len(user.id) == 32
        assert user.email == "new@test.com"
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.created_at is not None

    def test_user_email_unique(self, db_session):
        from sqlalchemy.exc import IntegrityError

        from gitspeak_core.db.models import User

        u1 = User(email="dup@test.com", hashed_password="h1")
        u2 = User(email="dup@test.com", hashed_password="h2")
        db_session.add(u1)
        db_session.commit()
        db_session.add(u2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_subscription_relationship(self, test_user, db_session):
        assert test_user.subscription is not None
        assert test_user.subscription.tier == "pro"
        assert test_user.subscription.status == "active"

    def test_pipeline_settings_model(self, test_user, db_session):
        from gitspeak_core.db.models import PipelineSettings

        settings = PipelineSettings(
            user_id=test_user.id,
            modules={"gap_detection": True, "drift_detection": True},
            flow_mode="api-first",
            default_protocols=["rest", "graphql"],
        )
        db_session.add(settings)
        db_session.commit()

        loaded = db_session.query(PipelineSettings).filter_by(user_id=test_user.id).first()
        assert loaded.modules["gap_detection"] is True
        assert loaded.flow_mode == "api-first"
        assert "graphql" in loaded.default_protocols

    def test_automation_schedule_model(self, test_user, db_session):
        from gitspeak_core.db.models import AutomationSchedule

        schedule = AutomationSchedule(
            user_id=test_user.id,
            name="Weekly docs refresh",
            cron_expr="0 3 * * 1",
            pipeline_config={"flow_mode": "code-first"},
        )
        db_session.add(schedule)
        db_session.commit()

        loaded = db_session.query(AutomationSchedule).filter_by(user_id=test_user.id).first()
        assert loaded.name == "Weekly docs refresh"
        assert loaded.cron_expr == "0 3 * * 1"
        assert loaded.enabled is True

    def test_pipeline_run_model(self, test_user, db_session):
        from gitspeak_core.db.models import PipelineRun

        run = PipelineRun(
            user_id=test_user.id,
            status="completed",
            trigger="manual",
            repo_path="/tmp/test-repo",
            flow_mode="code-first",
            phases=[{"name": "discovery", "status": "ok", "duration_seconds": 1.5}],
            artifacts=["/tmp/report.json"],
            quality_score=85.0,
            duration_seconds=12.3,
        )
        db_session.add(run)
        db_session.commit()

        loaded = db_session.query(PipelineRun).filter_by(user_id=test_user.id).first()
        assert loaded.status == "completed"
        assert loaded.quality_score == 85.0
        assert len(loaded.phases) == 1
        assert loaded.phases[0]["name"] == "discovery"

    def test_audit_log_model(self, db_session):
        from gitspeak_core.db.models import AuditLog

        entry = AuditLog(
            user_id="test123",
            action="pipeline.run",
            resource_type="pipeline_run",
            resource_id="run_001",
            details={"flow_mode": "api-first"},
            ip_address="192.168.1.1",
        )
        db_session.add(entry)
        db_session.commit()

        loaded = db_session.query(AuditLog).first()
        assert loaded.action == "pipeline.run"
        assert loaded.details["flow_mode"] == "api-first"

    def test_cascade_delete_user(self, test_user, db_session):
        """Deleting user cascades to subscription, settings, runs."""
        from gitspeak_core.db.models import PipelineRun, PipelineSettings, Subscription, User

        # Add settings and run
        settings = PipelineSettings(user_id=test_user.id, modules={})
        run = PipelineRun(user_id=test_user.id, status="pending")
        db_session.add_all([settings, run])
        db_session.commit()

        db_session.delete(test_user)
        db_session.commit()

        assert db_session.query(Subscription).filter_by(user_id="test_user_001").first() is None
        assert db_session.query(PipelineSettings).filter_by(user_id="test_user_001").first() is None
        assert db_session.query(PipelineRun).filter_by(user_id="test_user_001").first() is None


# =========================================================================
# Auth Tests
# =========================================================================


class TestAuth:
    """Test JWT auth system."""

    def test_password_hash_and_verify(self):
        from gitspeak_core.api.auth import hash_password, verify_password

        hashed = hash_password("SecurePass123!")
        assert hashed.startswith("pbkdf2:sha256:")
        assert verify_password("SecurePass123!", hashed) is True
        assert verify_password("WrongPassword", hashed) is False

    def test_password_hash_unique(self):
        from gitspeak_core.api.auth import hash_password

        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2  # different salts

    def test_create_and_decode_token(self):
        from gitspeak_core.api.auth import create_access_token, decode_access_token

        token = create_access_token(
            subject="user_123",
            secret_key="test-secret",
            expires_minutes=60,
            extra_claims={"email": "test@test.com", "tier": "pro"},
        )

        payload = decode_access_token(token, "test-secret")
        assert payload["sub"] == "user_123"
        assert payload["email"] == "test@test.com"
        assert payload["tier"] == "pro"
        assert "exp" in payload
        assert "jti" in payload

    def test_expired_token_rejected(self):
        import jwt

        from gitspeak_core.api.auth import create_access_token, decode_access_token

        token = create_access_token(
            subject="user_123",
            secret_key="test-secret",
            expires_minutes=-1,  # already expired
        )

        with pytest.raises(jwt.ExpiredSignatureError):
            decode_access_token(token, "test-secret")

    def test_wrong_secret_rejected(self):
        import jwt

        from gitspeak_core.api.auth import create_access_token, decode_access_token

        token = create_access_token(subject="user_123", secret_key="secret-a")

        with pytest.raises(jwt.InvalidSignatureError):
            decode_access_token(token, "secret-b")

    def test_register_creates_user_and_subscription(self, db_session):
        from gitspeak_core.api.auth import RegisterRequest, handle_register

        req = RegisterRequest(
            email="newuser@veridoc.dev",
            password="StrongPass123!",
            full_name="New User",
        )
        result = handle_register(req, db_session)

        assert result.email == "newuser@veridoc.dev"
        assert result.tier == "free"
        assert result.access_token

        from gitspeak_core.db.models import User

        user = db_session.query(User).filter_by(email="newuser@veridoc.dev").first()
        assert user is not None
        assert user.subscription is not None
        assert user.subscription.tier == "free"
        assert user.subscription.status == "trialing"

    def test_register_duplicate_email_fails(self, db_session):
        from gitspeak_core.api.auth import RegisterRequest, handle_register

        req = RegisterRequest(email="dup@test.com", password="Password123!")
        handle_register(req, db_session)

        with pytest.raises(ValueError, match="already registered"):
            handle_register(req, db_session)

    def test_login_success(self, db_session):
        from gitspeak_core.api.auth import (
            LoginRequest,
            RegisterRequest,
            handle_login,
            handle_register,
        )

        handle_register(
            RegisterRequest(email="login@test.com", password="MyPass123!"), db_session
        )
        result = handle_login(
            LoginRequest(email="login@test.com", password="MyPass123!"), db_session
        )

        assert result.access_token
        assert result.email == "login@test.com"

    def test_login_wrong_password(self, db_session):
        from gitspeak_core.api.auth import (
            LoginRequest,
            RegisterRequest,
            handle_login,
            handle_register,
        )

        handle_register(
            RegisterRequest(email="auth@test.com", password="Correct123!"), db_session
        )

        with pytest.raises(ValueError, match="Invalid email or password"):
            handle_login(
                LoginRequest(email="auth@test.com", password="Wrong123!"), db_session
            )

    def test_get_current_user_id(self):
        from gitspeak_core.api.auth import create_access_token, get_current_user_id

        token = create_access_token(subject="uid_abc", secret_key="s3cret")
        user_id = get_current_user_id(token, "s3cret")
        assert user_id == "uid_abc"

    def test_get_profile(self, test_user, db_session):
        from gitspeak_core.api.auth import handle_get_profile

        profile = handle_get_profile(test_user.id, db_session)
        assert profile.email == "test@veridoc.dev"
        assert profile.tier == "pro"


# =========================================================================
# Billing Tests (LemonSqueezy)
# =========================================================================


class TestBilling:
    """Test LemonSqueezy billing integration."""

    def test_usage_response(self, test_user, db_session):
        from gitspeak_core.api.billing import handle_get_usage

        usage = handle_get_usage(test_user.id, db_session)
        assert usage.tier == "pro"
        assert usage.ai_requests_limit == 2000
        assert usage.ai_requests_used == 0

    def test_check_quota_within_limit(self, test_user, db_session):
        from gitspeak_core.api.billing import check_quota

        assert check_quota(test_user.id, "ai_requests", db_session) is True

    def test_check_quota_exceeded(self, test_user, db_session):
        from gitspeak_core.api.billing import check_quota

        test_user.subscription.ai_requests_used = 2000
        db_session.commit()
        assert check_quota(test_user.id, "ai_requests", db_session) is False

    def test_increment_usage(self, test_user, db_session):
        from gitspeak_core.api.billing import increment_usage

        increment_usage(test_user.id, "ai_requests", 5, db_session)
        assert test_user.subscription.ai_requests_used == 5

        increment_usage(test_user.id, "pages", 3, db_session)
        assert test_user.subscription.pages_generated == 3

    def test_enterprise_unlimited_quota(self, test_user, db_session):
        from gitspeak_core.api.billing import check_quota

        test_user.subscription.tier = "enterprise"
        test_user.subscription.ai_requests_used = 999999
        db_session.commit()
        assert check_quota(test_user.id, "ai_requests", db_session) is True

    def test_tier_limits_structure(self):
        from gitspeak_core.api.billing import TIER_LIMITS

        assert set(TIER_LIMITS.keys()) == {"free", "starter", "pro", "business", "enterprise"}
        for tier, limits in TIER_LIMITS.items():
            assert "ai_requests" in limits
            assert "pages" in limits
            assert "api_calls" in limits

    def test_webhook_subscription_created(self, test_user, db_session):
        from gitspeak_core.api.billing import handle_webhook

        event_data = {
            "id": "sub_123",
            "attributes": {
                "customer_id": "cust_456",
                "variant_id": "variant_pro_monthly",
                "status": "active",
                "created_at": "2026-03-23T00:00:00Z",
                "renews_at": "2026-04-23T00:00:00Z",
                "custom_data": {"veridoc_user_id": test_user.id},
            },
        }

        result = handle_webhook("subscription_created", event_data, db_session)
        assert result["status"] == "ok"

    def test_webhook_subscription_cancelled(self, test_user, db_session):
        from gitspeak_core.api.billing import handle_webhook

        test_user.subscription.ls_subscription_id = "sub_cancel_test"
        db_session.commit()

        event_data = {
            "id": "sub_cancel_test",
            "attributes": {"status": "cancelled"},
        }

        result = handle_webhook("subscription_cancelled", event_data, db_session)
        assert result["status"] == "ok"
        assert test_user.subscription.cancel_at_period_end is True

    def test_webhook_payment_success_resets_usage(self, test_user, db_session):
        from gitspeak_core.api.billing import handle_webhook

        test_user.subscription.ls_subscription_id = "sub_pay_test"
        test_user.subscription.ai_requests_used = 500
        test_user.subscription.pages_generated = 50
        db_session.commit()

        event_data = {
            "attributes": {"subscription_id": "sub_pay_test"},
        }

        handle_webhook("subscription_payment_success", event_data, db_session)
        assert test_user.subscription.ai_requests_used == 0
        assert test_user.subscription.pages_generated == 0

    def test_webhook_unknown_event_ignored(self, db_session):
        from gitspeak_core.api.billing import handle_webhook

        result = handle_webhook("unknown_event", {}, db_session)
        assert result["status"] == "ignored"

    def test_verify_webhook_signature(self):
        from gitspeak_core.api.billing import verify_webhook_signature

        # With no secret, returns True (dev mode)
        assert verify_webhook_signature(b"test", "sig", "") is True

    def test_referral_attribution_and_recurring_commission(self, db_session):
        from gitspeak_core.api.auth import RegisterRequest, handle_register
        from gitspeak_core.api.billing import handle_get_referral_summary, handle_webhook
        from gitspeak_core.db.models import Subscription

        handle_register(
            RegisterRequest(email="referrer@test.com", password="StrongPass123!"),
            db_session,
        )
        handle_register(
            RegisterRequest(email="buyer@test.com", password="StrongPass123!"),
            db_session,
        )

        from gitspeak_core.db.models import User

        referrer = db_session.query(User).filter(User.email == "referrer@test.com").first()
        buyer = db_session.query(User).filter(User.email == "buyer@test.com").first()
        assert referrer is not None and buyer is not None

        summary = handle_get_referral_summary(referrer.id, db_session)
        code = summary.profile["referral_code"]

        created_event = {
            "id": "sub_ref_001",
            "attributes": {
                "customer_id": "cust_ref",
                "variant_id": "variant_pro_monthly",
                "status": "active",
                "custom_data": {
                    "veridoc_user_id": buyer.id,
                    "veridoc_referrer_user_id": referrer.id,
                    "veridoc_referral_code": code,
                },
            },
        }
        handle_webhook("subscription_created", created_event, db_session)

        buyer_sub = db_session.query(Subscription).filter(Subscription.user_id == buyer.id).first()
        assert buyer_sub is not None
        buyer_sub.tier = "pro"
        db_session.commit()

        payment_event = {
            "id": "evt_pay_ref_001",
            "attributes": {
                "subscription_id": "sub_ref_001",
                "total": "39900",
                "currency": "USD",
            },
        }
        handle_webhook("subscription_payment_success", payment_event, db_session)

        summary_after = handle_get_referral_summary(referrer.id, db_session)
        assert summary_after.earnings["accrued_cents"] > 0
        assert summary_after.earnings["is_recurring"] is True

    def test_badge_opt_out_blocked_for_cheapest_tier(self, test_user, db_session):
        from gitspeak_core.api.billing import ReferralSettingsRequest, handle_update_referral_settings

        test_user.subscription.tier = "starter"
        db_session.commit()

        with pytest.raises(ValueError, match="Badge cannot be disabled"):
            handle_update_referral_settings(
                test_user.id,
                ReferralSettingsRequest(badge_opt_out=True),
                db_session,
            )

    def test_checkout_response_includes_referral_settings_hint(self, test_user, db_session):
        from unittest.mock import patch

        from gitspeak_core.api.billing import CreateCheckoutRequest, handle_create_checkout

        fake_payload = {
            "data": {
                "attributes": {
                    "url": "https://checkout.example/abc",
                }
            }
        }

        class DummyResp:
            def raise_for_status(self):
                return None

            def json(self):
                return fake_payload

        with patch("gitspeak_core.api.billing.httpx.post", return_value=DummyResp()):
            result = handle_create_checkout(
                CreateCheckoutRequest(tier="pro"),
                user_id=test_user.id,
                user_email=test_user.email,
                db_session=db_session,
            )
        assert result.badge_settings_url == "/settings#referrals"
        assert "recurring referral commissions" in result.badge_settings_hint

    def test_webhook_payment_refunded_reverses_commission(self, db_session):
        from gitspeak_core.api.auth import RegisterRequest, handle_register
        from gitspeak_core.api.billing import handle_webhook
        from gitspeak_core.db.models import ReferralLedgerEntry

        handle_register(
            RegisterRequest(email="referrer2@test.com", password="StrongPass123!"),
            db_session,
        )
        handle_register(
            RegisterRequest(email="buyer2@test.com", password="StrongPass123!"),
            db_session,
        )
        from gitspeak_core.db.models import User

        referrer = db_session.query(User).filter(User.email == "referrer2@test.com").first()
        buyer = db_session.query(User).filter(User.email == "buyer2@test.com").first()
        assert referrer is not None and buyer is not None

        created_event = {
            "id": "sub_ref_002",
            "attributes": {
                "customer_id": "cust_ref_2",
                "variant_id": "variant_pro_monthly",
                "status": "active",
                "custom_data": {
                    "veridoc_user_id": buyer.id,
                    "veridoc_referrer_user_id": referrer.id,
                },
            },
        }
        handle_webhook("subscription_created", created_event, db_session)
        payment_event = {
            "id": "evt_pay_ref_002",
            "attributes": {
                "subscription_id": "sub_ref_002",
                "total": "39900",
                "currency": "USD",
            },
        }
        handle_webhook("subscription_payment_success", payment_event, db_session)

        row = db_session.query(ReferralLedgerEntry).filter(
            ReferralLedgerEntry.subscription_id == "sub_ref_002"
        ).first()
        assert row is not None
        assert row.status in {"accrued", "queued"}

        refund_event = {
            "id": "evt_refund_002",
            "attributes": {
                "subscription_id": "sub_ref_002",
            },
        }
        handle_webhook("subscription_payment_refunded", refund_event, db_session)
        db_session.refresh(row)
        assert row.status == "reversed"


# =========================================================================
# Settings and Module Registry Tests
# =========================================================================


class TestSettings:
    """Test pipeline settings with tier gating."""

    def test_available_modules_structure(self):
        from gitspeak_core.api.settings import AVAILABLE_MODULES

        assert len(AVAILABLE_MODULES) >= 19

        for mod in AVAILABLE_MODULES:
            assert "key" in mod
            assert "label" in mod
            assert "min_tier" in mod
            assert mod["min_tier"] in ("starter", "pro", "business", "enterprise")

    def test_enterprise_only_modules(self):
        from gitspeak_core.api.settings import AVAILABLE_MODULES

        enterprise_modules = {m["key"] for m in AVAILABLE_MODULES if m["min_tier"] == "enterprise"}
        assert "i18n_sync" in enterprise_modules
        assert "doc_compiler" in enterprise_modules

    def test_starter_modules(self):
        from gitspeak_core.api.settings import AVAILABLE_MODULES

        starter_modules = {m["key"] for m in AVAILABLE_MODULES if m["min_tier"] == "starter"}
        assert "gap_detection" in starter_modules
        assert "normalization" in starter_modules
        assert "self_checks" in starter_modules


# =========================================================================
# Rate Limiting Tests
# =========================================================================


class TestRateLimiting:
    """Test in-memory rate limiter."""

    def test_rate_limit_allows_within_limit(self):
        from gitspeak_core.api.app import _rate_limit_store, check_rate_limit

        user = {"user_id": "rate_test_1", "tier": "pro"}
        _rate_limit_store.pop("rate_test_1", None)

        # Pro tier = 60 req/min, should not raise
        for _ in range(59):
            check_rate_limit(user)

    def test_rate_limit_blocks_over_limit(self):
        from fastapi import HTTPException

        from gitspeak_core.api.app import _rate_limit_store, check_rate_limit

        user = {"user_id": "rate_test_2", "tier": "free"}
        _rate_limit_store.pop("rate_test_2", None)

        # Free tier = 10 req/min
        for _ in range(10):
            check_rate_limit(user)

        with pytest.raises(HTTPException) as exc_info:
            check_rate_limit(user)
        assert exc_info.value.status_code == 429

    def test_tier_rate_limits_defined(self):
        from gitspeak_core.api.app import TIER_RATE_LIMITS

        assert TIER_RATE_LIMITS["free"] < TIER_RATE_LIMITS["starter"]
        assert TIER_RATE_LIMITS["starter"] < TIER_RATE_LIMITS["pro"]
        assert TIER_RATE_LIMITS["pro"] < TIER_RATE_LIMITS["business"]
        assert TIER_RATE_LIMITS["business"] < TIER_RATE_LIMITS["enterprise"]


# =========================================================================
# LLM Executor Tests
# =========================================================================


class TestLLMExecutor:
    """Test GSD-style doc generation executor."""

    def test_llm_provider_selection(self):
        from gitspeak_core.docs.llm_executor import LLMProvider

        provider = LLMProvider(
            groq_api_key="key1",
            deepseek_api_key="",
            anthropic_api_key="",
            preference=["groq", "deepseek"],
        )
        assert provider.get_active_provider() == "groq"

    @patch.dict(os.environ, {"GROQ_API_KEY": "", "DEEPSEEK_API_KEY": ""}, clear=False)
    def test_llm_provider_fallback(self):
        from gitspeak_core.docs.llm_executor import LLMProvider

        provider = LLMProvider(
            groq_api_key="",
            deepseek_api_key="key2",
            anthropic_api_key="",
            preference=["groq", "deepseek"],
        )
        assert provider.get_active_provider() == "deepseek"

    @patch.dict(
        os.environ,
        {"GROQ_API_KEY": "", "DEEPSEEK_API_KEY": "", "ANTHROPIC_API_KEY": ""},
        clear=False,
    )
    def test_llm_provider_none_available(self):
        from gitspeak_core.docs.llm_executor import LLMProvider

        provider = LLMProvider(preference=["groq", "deepseek"])
        assert provider.get_active_provider() == "none"

    def test_generation_result_dataclass(self):
        from gitspeak_core.docs.llm_executor import GenerationResult

        result = GenerationResult(
            task_id="CONS-001",
            status="success",
            self_check_score=85.0,
            total_tokens=1500,
        )
        assert result.task_id == "CONS-001"
        assert result.errors == []
        assert result.retries == 0

    def test_gsd_executor_init(self):
        from gitspeak_core.docs.llm_executor import GSDDocExecutor, LLMProvider

        llm = LLMProvider(groq_api_key="test")
        executor = GSDDocExecutor(llm=llm, repo_root="/tmp/test")
        assert executor.max_retries == 2
        assert executor.gen_provider == "groq"

    def test_parse_verification_json(self):
        from gitspeak_core.docs.llm_executor import GSDDocExecutor, LLMProvider

        llm = LLMProvider(groq_api_key="test")
        executor = GSDDocExecutor(llm=llm)

        score, issues = executor._parse_verification(
            '```json\n{"score": 90, "issues": ["missing alt text"], "summary": "good"}\n```'
        )
        assert score == 90.0
        assert len(issues) == 1

    def test_parse_verification_fallback(self):
        from gitspeak_core.docs.llm_executor import GSDDocExecutor, LLMProvider

        llm = LLMProvider(groq_api_key="test")
        executor = GSDDocExecutor(llm=llm)

        score, issues = executor._parse_verification("unparseable response")
        assert score == 50.0  # fallback


# =========================================================================
# Celery Configuration Tests
# =========================================================================


class TestCeleryConfig:
    """Test Celery app configuration."""

    def test_celery_app_exists(self):
        from gitspeak_core.tasks.celery_app import app

        assert app.main == "veridoc"

    def test_celery_config_settings(self):
        from gitspeak_core.tasks.celery_app import app

        assert app.conf.task_serializer == "json"
        assert app.conf.timezone == "UTC"
        assert app.conf.task_track_started is True
        assert app.conf.task_time_limit == 3600

    def test_beat_schedule_defined(self):
        from gitspeak_core.tasks.celery_app import app

        assert "check-automation-schedules" in app.conf.beat_schedule
        schedule_config = app.conf.beat_schedule["check-automation-schedules"]
        assert schedule_config["schedule"] == 60.0


# =========================================================================
# System Prompt Tests
# =========================================================================


class TestSystemPrompt:
    """Test VeriOps prompt templates copied to VeriDoc."""

    def test_system_prompt_exists(self):
        from gitspeak_core.docs.system_prompt import GITSPEAK_SYSTEM_PROMPT

        assert len(GITSPEAK_SYSTEM_PROMPT) > 500
        assert "Stripe" in GITSPEAK_SYSTEM_PROMPT
        assert "frontmatter" in GITSPEAK_SYSTEM_PROMPT.lower()

    def test_doc_type_prompts_coverage(self):
        from gitspeak_core.docs.system_prompt import DOC_TYPE_PROMPTS

        expected_types = [
            "tutorial", "how_to", "concept", "reference",
            "troubleshooting", "quickstart", "faq", "webhook",
        ]
        for doc_type in expected_types:
            assert doc_type in DOC_TYPE_PROMPTS, f"Missing prompt for {doc_type}"

    def test_build_prompt_combines_parts(self):
        from gitspeak_core.docs.system_prompt import build_prompt

        result = build_prompt(
            doc_type="tutorial",
            template_content="# {{ title }}\n\nContent here.",
            context={"description": "A tutorial on webhooks"},
            shared_variables={"product_name": "Acme"},
        )

        assert "tutorial" in result.lower()
        assert "Acme" in result
        assert "A tutorial on webhooks" in result

    def test_build_prompt_without_variables(self):
        from gitspeak_core.docs.system_prompt import build_prompt

        result = build_prompt(
            doc_type="reference",
            template_content="# Reference",
            context={},
        )

        assert "SHARED VARIABLES" not in result
        assert "Reference" in result


# =========================================================================
# Template Library Tests
# =========================================================================


class TestTemplateLibrary:
    """Test built-in template library."""

    def test_template_library_loads(self):
        from gitspeak_core.docs.template_library import TemplateLibrary

        lib = TemplateLibrary()
        assert len(lib.templates) > 0

    def test_tutorial_template_exists(self):
        from gitspeak_core.docs.template_library import TemplateLibrary

        lib = TemplateLibrary()
        assert "tutorial" in lib.templates
        tpl = lib.templates["tutorial"]
        assert "title" in tpl.content
        assert "content_type: tutorial" in tpl.content


# =========================================================================
# Integration: Database Engine Tests
# =========================================================================


class TestDatabaseEngine:
    """Test database engine and session management."""

    def test_reset_engine(self):
        from gitspeak_core.db.engine import get_engine, reset_engine

        from gitspeak_core.config.settings import AppSettings

        settings = AppSettings(database_url="sqlite:///:memory:")
        engine = get_engine(settings)
        assert engine is not None

        reset_engine()
        # After reset, next call creates new engine

    def test_get_session(self):
        from gitspeak_core.db.engine import get_session, reset_engine

        reset_engine()
        from gitspeak_core.config.settings import AppSettings

        # Use a fresh in-memory DB
        settings = AppSettings(database_url="sqlite:///:memory:")
        session = get_session(settings)
        assert session is not None
        session.close()
        reset_engine()


# =========================================================================
# Full Pipeline Integration Test
# =========================================================================


class TestPipelineIntegration:
    """Test pipeline with DB persistence."""

    def test_pipeline_run_lifecycle(self, test_user, db_session):
        """Test creating and tracking a pipeline run."""
        from gitspeak_core.db.models import PipelineRun

        # Create
        run = PipelineRun(
            user_id=test_user.id,
            status="pending",
            trigger="manual",
            repo_path="/tmp/test-repo",
        )
        db_session.add(run)
        db_session.commit()

        # Start
        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        db_session.commit()

        # Complete
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        run.phases = [
            {"name": "discovery", "status": "ok", "duration_seconds": 2.0},
            {"name": "quality", "status": "ok", "duration_seconds": 5.0},
        ]
        run.quality_score = 88.5
        run.duration_seconds = 7.0
        db_session.commit()

        # Verify
        loaded = db_session.query(PipelineRun).filter_by(id=run.id).first()
        assert loaded.status == "completed"
        assert loaded.quality_score == 88.5
        assert len(loaded.phases) == 2
        assert loaded.user.email == "test@veridoc.dev"

    def test_multiple_runs_per_user(self, test_user, db_session):
        from gitspeak_core.db.models import PipelineRun

        for i in range(3):
            run = PipelineRun(
                user_id=test_user.id,
                status="completed",
                trigger="manual",
            )
            db_session.add(run)
        db_session.commit()

        runs = (
            db_session.query(PipelineRun)
            .filter_by(user_id=test_user.id)
            .all()
        )
        assert len(runs) == 3

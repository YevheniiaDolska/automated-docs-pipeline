"""LemonSqueezy billing integration for VeriDoc SaaS.

Provides:
- Checkout session creation (subscription flow via LemonSqueezy)
- Webhook handling (subscription lifecycle events)
- Customer portal link generation
- Usage tracking and quota enforcement
- Tier sync between LemonSqueezy and local DB

LemonSqueezy API docs: https://docs.lemonsqueezy.com/api
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
import smtplib
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import httpx
import jwt
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LemonSqueezy configuration
# ---------------------------------------------------------------------------

LEMONSQUEEZY_API_KEY = os.environ.get("LEMONSQUEEZY_API_KEY", "")
LEMONSQUEEZY_STORE_ID = os.environ.get("LEMONSQUEEZY_STORE_ID", "")
LEMONSQUEEZY_WEBHOOK_SECRET = os.environ.get("LEMONSQUEEZY_WEBHOOK_SECRET", "")
LEMONSQUEEZY_API_URL = "https://api.lemonsqueezy.com/v1"
BILLING_MODE = os.environ.get("VERIDOC_BILLING_MODE", "lemonsqueezy").strip().lower()
MANUAL_BILLING_MODE = BILLING_MODE in {"manual", "invoice", "custom"}
MANUAL_BILLING_WEBHOOK_SECRET = os.environ.get("VERIDOC_MANUAL_WEBHOOK_SECRET", "").strip()

# ---------------------------------------------------------------------------
# Variant ID -> Tier mapping (set in LemonSqueezy dashboard)
# ---------------------------------------------------------------------------

VARIANT_TO_TIER: dict[str, str] = {
    # Monthly variants (configure actual IDs from LemonSqueezy dashboard)
    os.environ.get("LS_VARIANT_STARTER_MONTHLY", "variant_starter_monthly"): "starter",
    os.environ.get("LS_VARIANT_PRO_MONTHLY", "variant_pro_monthly"): "pro",
    os.environ.get("LS_VARIANT_BUSINESS_MONTHLY", "variant_business_monthly"): "business",
    os.environ.get("LS_VARIANT_ENTERPRISE_MONTHLY", "variant_enterprise_monthly"): "enterprise",
    # Annual variants
    os.environ.get("LS_VARIANT_STARTER_ANNUAL", "variant_starter_annual"): "starter",
    os.environ.get("LS_VARIANT_PRO_ANNUAL", "variant_pro_annual"): "pro",
    os.environ.get("LS_VARIANT_BUSINESS_ANNUAL", "variant_business_annual"): "business",
    os.environ.get("LS_VARIANT_ENTERPRISE_ANNUAL", "variant_enterprise_annual"): "enterprise",
}

TIER_TO_VARIANT: dict[str, str] = {
    "starter": os.environ.get("LS_VARIANT_STARTER_MONTHLY", "variant_starter_monthly"),
    "pro": os.environ.get("LS_VARIANT_PRO_MONTHLY", "variant_pro_monthly"),
    "business": os.environ.get("LS_VARIANT_BUSINESS_MONTHLY", "variant_business_monthly"),
    "enterprise": os.environ.get("LS_VARIANT_ENTERPRISE_MONTHLY", "variant_enterprise_monthly"),
}

# Usage limits per tier (per billing period)
TIER_LIMITS: dict[str, dict[str, int]] = {
    "free": {"ai_requests": 50, "pages": 10, "api_calls": 100},
    "starter": {"ai_requests": 500, "pages": 50, "api_calls": 5000},
    "pro": {"ai_requests": 2000, "pages": 200, "api_calls": 20000},
    "business": {"ai_requests": 10000, "pages": 1000, "api_calls": 100000},
    "enterprise": {"ai_requests": -1, "pages": -1, "api_calls": -1},  # unlimited
}

# Referral and commission policy defaults.
CHEAPEST_PAID_TIER = os.environ.get("VERIDOC_CHEAPEST_PAID_TIER", "starter")
COMMISSION_RATE_DEFAULT = float(os.environ.get("VERIDOC_REFERRAL_COMMISSION_RATE", "0.15"))
COMMISSION_GRACE_DAYS = int(os.environ.get("VERIDOC_REFERRAL_GRACE_DAYS", "14"))
PAYOUT_MIN_CENTS = int(os.environ.get("VERIDOC_REFERRAL_PAYOUT_MIN_CENTS", "5000"))
WISE_API_TOKEN = os.environ.get("WISE_API_TOKEN", "")
WISE_PROFILE_ID = os.environ.get("WISE_PROFILE_ID", "")
WISE_API_URL = os.environ.get("WISE_API_URL", "https://api.transferwise.com")
WISE_DRY_RUN = os.environ.get("WISE_DRY_RUN", "true").lower() in {"1", "true", "yes"}
VERIOPS_LICENSE_KEY = os.environ.get("VERIOPS_LICENSE_KEY", "").strip()
LICENSE_AUTORENEW_ENABLED = os.environ.get(
    "VERIDOC_LICENSE_AUTORENEW_ENABLED", "true"
).lower() in {"1", "true", "yes"}
LICENSE_STORE_DIR = Path(
    os.environ.get("VERIDOC_LICENSE_STORE_DIR", "/var/lib/veridoc/licenses")
).expanduser()
LICENSE_ISSUER = os.environ.get("VERIDOC_LICENSE_ISSUER", "veridoc-billing")
LICENSE_AUDIENCE = os.environ.get("VERIDOC_LICENSE_AUDIENCE", "veriops-client")
LICENSE_REFRESH_BEFORE_SECONDS = int(
    os.environ.get("VERIDOC_LICENSE_REFRESH_BEFORE_SECONDS", "86400")
)

def _load_default_monthly_cents() -> dict[str, int]:
    """Load fallback tier prices from pricing config used by the landing."""
    try:
        from gitspeak_core.config.pricing import (
            BUSINESS_PLAN,
            ENTERPRISE_PLAN,
            PRO_PLAN,
            STARTER_PLAN,
        )

        return {
            "starter": int(STARTER_PLAN.price_monthly_usd) * 10,
            "pro": int(PRO_PLAN.price_monthly_usd) * 10,
            "business": int(BUSINESS_PLAN.price_monthly_usd) * 10,
            "enterprise": int(ENTERPRISE_PLAN.price_monthly_usd) * 10,
        }
    except ImportError:
        # Safe fallback if pricing module is unavailable in stripped runtime.
        return {
            "starter": 1490,
            "pro": 3990,
            "business": 7990,
            "enterprise": 14990,
        }


TIER_DEFAULT_MONTHLY_CENTS = _load_default_monthly_cents()
LICENSE_PLAN_BY_TIER: dict[str, str] = {
    "free": "pilot",
    "starter": "pilot",
    "pro": "professional",
    "business": "enterprise",
    "enterprise": "enterprise",
}


def _tier_to_license_capabilities(tier: str) -> tuple[list[str], dict[str, bool]]:
    """Return protocol and feature capabilities for issued server licenses."""
    normalized = (tier or "free").strip().lower()
    if normalized in {"enterprise", "business"}:
        protocols = ["rest", "graphql", "grpc", "asyncapi", "websocket"]
        features = {
            "api_first_flow": True,
            "multi_protocol_pipeline": True,
            "weekly_gap_batch": True,
            "public_docs_audit": True,
            "seo_geo_scoring": True,
            "ask_ai": True,
            "rollbacks": True,
        }
        return protocols, features
    if normalized == "pro":
        protocols = ["rest", "graphql"]
        features = {
            "api_first_flow": True,
            "multi_protocol_pipeline": False,
            "weekly_gap_batch": True,
            "public_docs_audit": True,
            "seo_geo_scoring": True,
            "ask_ai": True,
            "rollbacks": True,
        }
        return protocols, features
    protocols = ["rest"]
    features = {
        "api_first_flow": True,
        "multi_protocol_pipeline": False,
        "weekly_gap_batch": False,
        "public_docs_audit": False,
        "seo_geo_scoring": False,
        "ask_ai": False,
        "rollbacks": False,
    }
    return protocols, features


def _safe_dt(value: datetime | None) -> datetime | None:
    """Normalize datetime to timezone-aware UTC datetime."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _is_license_active_status(sub_status: str) -> bool:
    """Statuses that keep paid capabilities active."""
    return sub_status in {"trialing", "active"}


def _issue_or_refresh_server_license(
    sub: Any,
    reason: str,
    db_session: Any,
) -> None:
    """Issue or refresh a server-managed license token from subscription state.

    This provides a webhook-driven entitlement artifact for automated
    billing-to-license synchronization without requiring manual reissue.
    """
    if not LICENSE_AUTORENEW_ENABLED:
        return
    if not VERIOPS_LICENSE_KEY:
        logger.warning(
            "VERIOPS_LICENSE_KEY is not configured; skipping auto license issuance"
        )
        return

    now = datetime.now(timezone.utc)
    period_end = _safe_dt(getattr(sub, "current_period_end", None))
    status = str(getattr(sub, "status", "canceled") or "canceled")
    tier = str(getattr(sub, "tier", "free") or "free")
    user_id = str(getattr(sub, "user_id", "") or "")
    ls_subscription_id = str(getattr(sub, "ls_subscription_id", "") or "")

    active = _is_license_active_status(status)
    effective_tier = tier if active else "free"
    protocols, features = _tier_to_license_capabilities(effective_tier)
    plan = LICENSE_PLAN_BY_TIER.get(effective_tier, "pilot")
    exp_at = period_end if (period_end and active) else now + timedelta(days=7)
    iat = int(now.timestamp())
    exp = int(exp_at.timestamp())

    claims = {
        "sub": user_id,
        "tier": effective_tier,
        "plan": plan,
        "status": status,
        "ls_subscription_id": ls_subscription_id,
        "features": features,
        "protocols": protocols,
        "iat": iat,
        "exp": exp,
        "iss": LICENSE_ISSUER,
        "aud": LICENSE_AUDIENCE,
        "jti": uuid.uuid4().hex,
        "reason": reason,
        "auto_renewed": True,
    }
    token = jwt.encode(claims, VERIOPS_LICENSE_KEY, algorithm="HS256")

    user_dir = LICENSE_STORE_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    license_path = user_dir / "license.jwt"
    metadata_path = user_dir / "license_meta.json"
    license_path.write_text(token + "\n", encoding="utf-8")
    metadata = {
        "user_id": user_id,
        "tier": effective_tier,
        "status": status,
        "plan": plan,
        "reason": reason,
        "issued_at": now.isoformat(),
        "expires_at": exp_at.isoformat(),
        "ls_subscription_id": ls_subscription_id,
        "protocols": protocols,
        "features": features,
        "license_path": str(license_path),
    }
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    try:
        os.chmod(license_path, 0o600)
        os.chmod(metadata_path, 0o600)
    except OSError as exc:
        logger.debug("Failed to apply chmod on license artifacts for user=%s: %s", user_id, exc)

    # Best-effort audit trace.
    try:
        from gitspeak_core.db.models import AuditLog

        db_session.add(
            AuditLog(
                user_id=user_id,
                action="license.auto_renewed",
                resource_type="subscription",
                resource_id=getattr(sub, "id", None),
                details={
                    "tier": effective_tier,
                    "status": status,
                    "reason": reason,
                    "expires_at": exp_at.isoformat(),
                    "path": str(license_path),
                },
            )
        )
        db_session.commit()
    except SQLAlchemyError as exc:
        db_session.rollback()
        logger.warning("Failed to persist license audit log for user=%s: %s", user_id, exc)

    logger.info(
        "Server license issued: user=%s tier=%s status=%s reason=%s exp=%s",
        user_id,
        effective_tier,
        status,
        reason,
        exp_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class CreateCheckoutRequest(BaseModel):
    """Request to create a LemonSqueezy checkout."""

    model_config = ConfigDict(extra="forbid")

    tier: str = Field(description="Target subscription tier")
    annual: bool = Field(default=False, description="Annual billing")
    success_url: str = Field(default="", description="Redirect URL on success")
    referral_code: str = Field(
        default="",
        description="Optional referrer code to attribute recurring commissions.",
    )


class CheckoutResponse(BaseModel):
    """LemonSqueezy checkout URL."""

    model_config = ConfigDict(extra="forbid")

    checkout_url: str
    badge_settings_url: str = Field(
        default="/settings#referrals",
        description="Where higher-tier users can configure badge opt-out and referral payouts.",
    )
    badge_settings_hint: str = Field(
        default=(
            "On Business/Enterprise you can disable badge in Settings > Badge and referral income, "
            "or keep it enabled for recurring referral commissions. Read full terms at /referral-terms."
        ),
        description="UI hint to show near checkout and post-purchase screens.",
    )


class PortalResponse(BaseModel):
    """LemonSqueezy customer portal URL."""

    model_config = ConfigDict(extra="forbid")

    portal_url: str


class UsageResponse(BaseModel):
    """Current usage for the billing period."""

    model_config = ConfigDict(extra="forbid")

    tier: str
    status: str
    ai_requests_used: int
    ai_requests_limit: int
    pages_generated: int
    pages_limit: int
    api_calls_used: int
    api_calls_limit: int
    current_period_end: str | None
    trial_ends_at: str | None


class ReferralSettingsRequest(BaseModel):
    """User-controlled referral and badge settings."""

    model_config = ConfigDict(extra="forbid")

    badge_opt_out: bool | None = None
    payout_provider: str | None = None
    payout_recipient_id: str | None = None
    payout_email: str | None = None
    accept_terms: bool | None = None


class ReferralSummaryResponse(BaseModel):
    """Referral policy, earnings summary, and payouts."""

    model_config = ConfigDict(extra="forbid")

    policy: dict[str, Any]
    profile: dict[str, Any]
    earnings: dict[str, Any]
    recent_ledger: list[dict[str, Any]]
    payouts: list[dict[str, Any]]


class LicenseStatusResponse(BaseModel):
    """Current auto-issued server license status for user."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool
    has_license: bool
    license_path: str | None = None
    expires_at: str | None = None
    tier: str | None = None
    status: str | None = None
    reason: str | None = None
    updated_at: str | None = None


class LicenseTokenResponse(BaseModel):
    """Current server-issued license JWT for authenticated user."""

    model_config = ConfigDict(extra="forbid")

    has_license: bool
    token: str | None = None
    expires_at: str | None = None


# ---------------------------------------------------------------------------
# Invoice request models
# ---------------------------------------------------------------------------


class InvoiceRequestCreate(BaseModel):
    """Request body for invoice-only plan requests."""

    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=3, max_length=320)
    company: str | None = Field(None, max_length=300)
    plan_tier: str = Field(..., pattern=r"^(business|enterprise)$")
    billing_period: str = Field(..., pattern=r"^(monthly|annual)$")
    message: str | None = Field(None, max_length=2000)


class InvoiceRequestResponse(BaseModel):
    """Response after submitting an invoice request."""

    model_config = ConfigDict(extra="forbid")

    id: str
    status: str
    message: str


# ---------------------------------------------------------------------------
# Audit request models
# ---------------------------------------------------------------------------


class AuditRequestCreate(BaseModel):
    """Request body for free audit requests from landing page."""

    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=3, max_length=320)
    company: str | None = Field(None, max_length=300)
    docs_url: str | None = Field(None, max_length=500)
    message: str | None = Field(None, max_length=2000)


class AuditRequestResponse(BaseModel):
    """Response after submitting an audit request."""

    model_config = ConfigDict(extra="forbid")

    id: str
    status: str
    message: str


# ---------------------------------------------------------------------------
# Checkout handler
# ---------------------------------------------------------------------------


def handle_create_checkout(
    request: CreateCheckoutRequest,
    user_id: str,
    user_email: str,
    db_session: Any,
) -> CheckoutResponse:
    """Create a LemonSqueezy checkout URL for subscription.

    Uses the LemonSqueezy API to generate a checkout link.
    The user is redirected to LemonSqueezy to complete payment.
    """
    if MANUAL_BILLING_MODE:
        raise ValueError(
            "Self-serve checkout is disabled in manual billing mode. "
            "Use invoice flow and manual subscription activation."
        )

    suffix = "annual" if request.annual else "monthly"
    variant_key = f"variant_{request.tier}_{suffix}"
    env_var_name = f"LS_VARIANT_{request.tier.upper()}_{suffix.upper()}"
    variant_id = os.environ.get(env_var_name, "")

    if not variant_id:
        raise ValueError(
            f"Self-serve checkout is not available for {request.tier} {suffix}. "
            "Please use the invoice request form for this plan."
        )

    # LemonSqueezy checkout API
    headers = {
        "Authorization": f"Bearer {LEMONSQUEEZY_API_KEY}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
    }

    custom_payload: dict[str, Any] = {
        "veridoc_user_id": user_id,
    }
    if request.referral_code.strip():
        ref_payload = _resolve_referral_for_checkout(
            referral_code=request.referral_code.strip(),
            buyer_user_id=user_id,
            db_session=db_session,
        )
        custom_payload.update(ref_payload)

    attributes: dict[str, Any] = {
        "checkout_data": {
            "email": user_email,
            "custom": custom_payload,
        },
    }
    if request.success_url:
        attributes["product_options"] = {
            "redirect_url": request.success_url,
        }

    checkout_data = {
        "data": {
            "type": "checkouts",
            "attributes": attributes,
            "relationships": {
                "store": {
                    "data": {"type": "stores", "id": LEMONSQUEEZY_STORE_ID}
                },
                "variant": {
                    "data": {"type": "variants", "id": variant_id}
                },
            },
        }
    }

    resp = httpx.post(
        f"{LEMONSQUEEZY_API_URL}/checkouts",
        json=checkout_data,
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    result = resp.json()
    checkout_url = result["data"]["attributes"]["url"]

    return CheckoutResponse(checkout_url=checkout_url)


def handle_get_portal_url(
    user_id: str,
    db_session: Any,
) -> PortalResponse:
    """Get LemonSqueezy customer portal URL.

    LemonSqueezy provides a portal URL per subscription
    where users can manage their billing.
    """
    from gitspeak_core.db.models import User

    user = db_session.query(User).filter(User.id == user_id).first()
    if not user or not user.subscription:
        raise ValueError("No subscription found")

    sub = user.subscription
    if not sub.ls_subscription_id:
        raise ValueError("No LemonSqueezy subscription linked")

    headers = {
        "Authorization": f"Bearer {LEMONSQUEEZY_API_KEY}",
        "Accept": "application/vnd.api+json",
    }

    resp = httpx.get(
        f"{LEMONSQUEEZY_API_URL}/subscriptions/{sub.ls_subscription_id}",
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    result = resp.json()
    portal_url = result["data"]["attributes"]["urls"]["customer_portal"]

    return PortalResponse(portal_url=portal_url)


# ---------------------------------------------------------------------------
# Usage tracking
# ---------------------------------------------------------------------------


def handle_get_usage(user_id: str, db_session: Any) -> UsageResponse:
    """Get current usage for the billing period."""
    from gitspeak_core.db.models import User

    user = db_session.query(User).filter(User.id == user_id).first()
    if not user or not user.subscription:
        raise ValueError("No subscription found")

    sub = user.subscription
    limits = TIER_LIMITS.get(sub.tier, TIER_LIMITS["free"])

    return UsageResponse(
        tier=sub.tier,
        status=sub.status,
        ai_requests_used=sub.ai_requests_used,
        ai_requests_limit=limits["ai_requests"],
        pages_generated=sub.pages_generated,
        pages_limit=limits["pages"],
        api_calls_used=sub.api_calls_used,
        api_calls_limit=limits["api_calls"],
        current_period_end=(
            sub.current_period_end.isoformat() if sub.current_period_end else None
        ),
        trial_ends_at=(
            sub.trial_ends_at.isoformat() if sub.trial_ends_at else None
        ),
    )


def handle_manual_subscription_upsert(
    payload: dict[str, Any],
    db_session: Any,
) -> dict[str, Any]:
    """Upsert subscription state for manual-invoice billing mode.

    This enforces the same tier limits as webhook flow but does not depend
    on LemonSqueezy events.
    """
    from gitspeak_core.db.models import Subscription, User

    user_id = str(payload.get("user_id", "")).strip()
    tier = str(payload.get("tier", "free")).strip().lower()
    status = str(payload.get("status", "active")).strip().lower()
    period_days_raw = payload.get("period_days", 30)
    source = str(payload.get("source", "manual_invoice")).strip() or "manual_invoice"
    reset_usage = bool(payload.get("reset_usage", True))
    external_customer_ref = str(payload.get("external_customer_ref", "")).strip()

    if not user_id:
        raise ValueError("user_id is required")
    if tier not in TIER_LIMITS:
        raise ValueError(f"Unsupported tier: {tier}")
    allowed_status = {"trialing", "active", "past_due", "canceled", "unpaid", "paused"}
    if status not in allowed_status:
        raise ValueError(f"Unsupported status: {status}")
    try:
        period_days = int(period_days_raw)
    except (TypeError, ValueError):
        raise ValueError("period_days must be an integer")
    if period_days < 1 or period_days > 366:
        raise ValueError("period_days must be between 1 and 366")

    user = db_session.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User not found: {user_id}")

    sub = db_session.query(Subscription).filter(Subscription.user_id == user_id).first()
    if not sub:
        sub = Subscription(user_id=user_id, tier="free", status="trialing")
        db_session.add(sub)
        db_session.flush()

    now = datetime.now(timezone.utc)
    period_end = now + timedelta(days=period_days)
    limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

    sub.tier = tier
    sub.status = status
    sub.current_period_start = now
    sub.current_period_end = period_end
    sub.cancel_at_period_end = status in {"canceled", "unpaid"}
    sub.ai_requests_limit = limits["ai_requests"]
    if external_customer_ref:
        sub.ls_customer_id = external_customer_ref
    if reset_usage:
        sub.ai_requests_used = 0
        sub.pages_generated = 0
        sub.api_calls_used = 0

    db_session.commit()
    _issue_or_refresh_server_license(
        sub,
        reason=f"manual_billing_upsert:{source}",
        db_session=db_session,
    )

    return {
        "status": "ok",
        "user_id": user_id,
        "tier": sub.tier,
        "subscription_status": sub.status,
        "period_start": sub.current_period_start.isoformat() if sub.current_period_start else "",
        "period_end": sub.current_period_end.isoformat() if sub.current_period_end else "",
        "limits": limits,
        "usage_reset": reset_usage,
        "source": source,
    }


def verify_manual_billing_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str | None = None,
) -> bool:
    """Verify HMAC-SHA256 for manual billing webhook payload."""
    shared_secret = (secret or MANUAL_BILLING_WEBHOOK_SECRET).strip()
    if not shared_secret:
        logger.warning(
            "VERIDOC_MANUAL_WEBHOOK_SECRET is not configured; rejecting manual webhook"
        )
        return False
    if not signature.strip():
        return False
    expected = hmac.new(
        shared_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature.strip())


def _resolve_manual_webhook_user_id(payload: dict[str, Any], db_session: Any) -> str:
    """Resolve user identifier from manual webhook payload."""
    from gitspeak_core.db.models import Subscription, User

    user_id = str(payload.get("user_id", "")).strip()
    if user_id:
        return user_id

    email = str(payload.get("email", "")).strip().lower()
    if email:
        user = db_session.query(User).filter(User.email == email).first()
        if user:
            return str(user.id)

    external_customer_ref = str(payload.get("external_customer_ref", "")).strip()
    if external_customer_ref:
        sub = (
            db_session.query(Subscription)
            .filter(Subscription.ls_customer_id == external_customer_ref)
            .first()
        )
        if sub:
            return str(sub.user_id)

    return ""


def handle_manual_billing_webhook(
    event_name: str,
    event_data: dict[str, Any],
    db_session: Any,
) -> dict[str, Any]:
    """Process manual billing lifecycle events.

    Expected event names:
    - payment_success / payment_succeeded / invoice_paid / subscription_renewed
    - payment_failed / invoice_failed
    - subscription_canceled / access_revoked / chargeback
    """
    event = str(event_name or "").strip().lower()
    payload = event_data if isinstance(event_data, dict) else {}
    user_id = _resolve_manual_webhook_user_id(payload, db_session)
    if not user_id:
        return {"status": "ignored", "event": event, "reason": "user_not_resolved"}

    from gitspeak_core.db.models import Subscription

    current_sub = (
        db_session.query(Subscription)
        .filter(Subscription.user_id == user_id)
        .first()
    )
    current_tier = str(getattr(current_sub, "tier", "free") or "free").strip().lower()
    requested_tier = str(payload.get("tier", "")).strip().lower()
    if requested_tier not in TIER_LIMITS:
        requested_tier = current_tier if current_tier in TIER_LIMITS else "free"
    period_days = payload.get("period_days", 30)
    source = str(payload.get("source", "manual_webhook")).strip() or "manual_webhook"
    external_customer_ref = str(payload.get("external_customer_ref", "")).strip()

    active_events = {
        "payment_success",
        "payment_succeeded",
        "invoice_paid",
        "subscription_renewed",
    }
    failed_events = {"payment_failed", "invoice_failed"}
    cancel_events = {"subscription_canceled", "access_revoked", "chargeback"}

    if event in active_events:
        upsert_payload = {
            "user_id": user_id,
            "tier": requested_tier if requested_tier != "free" else current_tier,
            "status": "active",
            "period_days": period_days,
            "source": source,
            "reset_usage": True,
            "external_customer_ref": external_customer_ref,
        }
        result = handle_manual_subscription_upsert(upsert_payload, db_session)
        return {"status": "ok", "event": event, "result": result}

    if event in failed_events:
        upsert_payload = {
            "user_id": user_id,
            "tier": requested_tier if requested_tier in TIER_LIMITS else "free",
            "status": "past_due",
            "period_days": 1,
            "source": source,
            "reset_usage": False,
            "external_customer_ref": external_customer_ref,
        }
        result = handle_manual_subscription_upsert(upsert_payload, db_session)
        return {"status": "ok", "event": event, "result": result}

    if event in cancel_events:
        upsert_payload = {
            "user_id": user_id,
            "tier": "free",
            "status": "canceled",
            "period_days": 1,
            "source": source,
            "reset_usage": False,
            "external_customer_ref": external_customer_ref,
        }
        result = handle_manual_subscription_upsert(upsert_payload, db_session)
        return {"status": "ok", "event": event, "result": result}

    return {"status": "ignored", "event": event, "reason": "event_not_supported"}


def handle_get_server_license_status(
    user_id: str,
    db_session: Any,
) -> LicenseStatusResponse:
    """Return current webhook-managed server license status for a user."""
    from gitspeak_core.db.models import User

    user = db_session.query(User).filter(User.id == user_id).first()
    if not user or not user.subscription:
        raise ValueError("No subscription found")

    if not LICENSE_AUTORENEW_ENABLED:
        return LicenseStatusResponse(enabled=False, has_license=False)

    meta_path = LICENSE_STORE_DIR / user_id / "license_meta.json"
    lic_path = LICENSE_STORE_DIR / user_id / "license.jwt"
    if not meta_path.exists() or not lic_path.exists():
        return LicenseStatusResponse(
            enabled=True,
            has_license=False,
            license_path=str(lic_path),
        )
    try:
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, TypeError):
        payload = {}
    return LicenseStatusResponse(
        enabled=True,
        has_license=True,
        license_path=str(lic_path),
        expires_at=str(payload.get("expires_at") or ""),
        tier=str(payload.get("tier") or ""),
        status=str(payload.get("status") or ""),
        reason=str(payload.get("reason") or ""),
        updated_at=str(payload.get("issued_at") or ""),
    )


def handle_get_server_license_token(
    user_id: str,
    db_session: Any,
) -> LicenseTokenResponse:
    """Return current auto-managed license JWT for authenticated user."""
    from gitspeak_core.db.models import User

    user = db_session.query(User).filter(User.id == user_id).first()
    if not user or not user.subscription:
        raise ValueError("No subscription found")
    sub = user.subscription

    # Retainer-active gate: only trialing/active subscriptions can receive tokens.
    if not _is_license_active_status(str(getattr(sub, "status", "") or "")):
        return LicenseTokenResponse(has_license=False)

    # Opportunistic refresh: re-issue token when missing or near expiration.
    status_snapshot = handle_get_server_license_status(user_id, db_session)
    refresh_needed = not bool(status_snapshot.has_license)
    if not refresh_needed and status_snapshot.expires_at:
        try:
            expires_at = datetime.fromisoformat(str(status_snapshot.expires_at))
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            refresh_needed = (expires_at - datetime.now(timezone.utc)).total_seconds() <= LICENSE_REFRESH_BEFORE_SECONDS
        except ValueError:
            refresh_needed = True
    if refresh_needed:
        _issue_or_refresh_server_license(
            sub,
            reason="server_token_pull_refresh",
            db_session=db_session,
        )

    status = handle_get_server_license_status(user_id, db_session)
    if not status.has_license or not status.license_path:
        return LicenseTokenResponse(has_license=False)
    path = Path(status.license_path)
    if not path.exists():
        return LicenseTokenResponse(has_license=False)
    token = path.read_text(encoding="utf-8").strip()
    if not token:
        return LicenseTokenResponse(has_license=False)
    return LicenseTokenResponse(
        has_license=True,
        token=token,
        expires_at=status.expires_at,
    )


def run_license_autorenew_batch(
    db_session: Any,
    now: datetime | None = None,
) -> dict[str, int]:
    """Refresh/degrade server-managed licenses for all subscriptions.

    Intended for periodic server cron (hybrid/cloud renewal loop).
    """
    from gitspeak_core.db.models import Subscription

    now = now or datetime.now(timezone.utc)
    subs = db_session.query(Subscription).all()
    scanned = 0
    refreshed = 0
    degraded = 0
    errors = 0

    for sub in subs:
        scanned += 1
        try:
            active = _is_license_active_status(str(getattr(sub, "status", "") or ""))
            _issue_or_refresh_server_license(
                sub,
                reason="batch_autorenew_active" if active else "batch_autorenew_inactive",
                db_session=db_session,
            )
            if active:
                refreshed += 1
            else:
                degraded += 1
        except (RuntimeError, ValueError, TypeError, OSError):
            errors += 1
            db_session.rollback()

    return {
        "scanned": scanned,
        "refreshed": refreshed,
        "degraded": degraded,
        "errors": errors,
        "ran_at_utc": now.isoformat(),
    }


def check_quota(user_id: str, resource: str, db_session: Any) -> bool:
    """Check if user has remaining quota for a resource.

    Args:
        resource: "ai_requests", "pages", or "api_calls"

    Returns True if quota is available, False if exceeded.
    """
    from gitspeak_core.db.models import User

    user = db_session.query(User).filter(User.id == user_id).first()
    if not user or not user.subscription:
        return False

    sub = user.subscription
    limits = TIER_LIMITS.get(sub.tier, TIER_LIMITS["free"])
    limit = limits.get(resource, 0)

    if limit == -1:  # unlimited (enterprise)
        return True

    usage_map = {
        "ai_requests": sub.ai_requests_used,
        "pages": sub.pages_generated,
        "api_calls": sub.api_calls_used,
    }
    current = usage_map.get(resource, 0)
    return current < limit


def increment_usage(user_id: str, resource: str, amount: int, db_session: Any) -> None:
    """Increment usage counter for a resource."""
    from gitspeak_core.db.models import User

    user = db_session.query(User).filter(User.id == user_id).first()
    if not user or not user.subscription:
        return

    sub = user.subscription
    if resource == "ai_requests":
        sub.ai_requests_used += amount
    elif resource == "pages":
        sub.pages_generated += amount
    elif resource == "api_calls":
        sub.api_calls_used += amount
    db_session.commit()


# ---------------------------------------------------------------------------
# Referral policy, settings, and reporting
# ---------------------------------------------------------------------------


def ensure_referral_profile(user_id: str, db_session: Any) -> Any:
    """Create a referral profile for user if it does not exist."""
    from gitspeak_core.db.models import ReferralProfile

    profile = (
        db_session.query(ReferralProfile)
        .filter(ReferralProfile.user_id == user_id)
        .first()
    )
    if profile:
        return profile

    code = _generate_unique_referral_code(db_session)
    profile = ReferralProfile(
        user_id=user_id,
        referral_code=code,
        badge_opt_out=False,
        payout_provider="manual",
        payout_status="pending",
    )
    db_session.add(profile)
    db_session.commit()
    return profile


def handle_get_referral_summary(user_id: str, db_session: Any) -> ReferralSummaryResponse:
    """Return referral policy, recurring earnings, and payout history."""
    from gitspeak_core.db.models import ReferralLedgerEntry, ReferralPayout, User

    user = db_session.query(User).filter(User.id == user_id).first()
    if not user or not user.subscription:
        raise ValueError("No subscription found")

    profile = ensure_referral_profile(user_id, db_session)
    current_tier = user.subscription.tier
    mandatory_badge = _is_badge_mandatory(current_tier)
    commission_eligible = _is_referrer_commission_eligible_tier(current_tier)

    rows = (
        db_session.query(ReferralLedgerEntry)
        .filter(ReferralLedgerEntry.referrer_user_id == user_id)
        .order_by(ReferralLedgerEntry.created_at.desc())
        .limit(50)
        .all()
    )
    payouts = (
        db_session.query(ReferralPayout)
        .filter(ReferralPayout.user_id == user_id)
        .order_by(ReferralPayout.created_at.desc())
        .limit(20)
        .all()
    )

    totals = defaultdict(int)
    for row in rows:
        totals[row.status] += int(row.amount_cents or 0)

    policy_message = (
        "Free, Starter, and Pro must keep Powered by VeriDoc badge enabled and do not earn commission. "
        "Business and Enterprise can disable the badge, or keep it enabled to earn recurring commission. "
        "Recurring accrues only while both referrer and referred accounts remain on paid active subscriptions."
    )

    return ReferralSummaryResponse(
        policy={
            "cheapest_paid_tier": CHEAPEST_PAID_TIER,
            "commission_rate": COMMISSION_RATE_DEFAULT,
            "mandatory_badge": mandatory_badge,
            "commission_eligible": commission_eligible,
            "policy_message": policy_message,
            "ui_hint": "Manage badge and recurring referral payouts in Billing > Referrals.",
        },
        profile={
            "referral_code": profile.referral_code,
            "referral_link": f"{APP_BASE_URL}/?ref={profile.referral_code}",
            "badge_opt_out": bool(profile.badge_opt_out),
            "badge_opt_out_allowed": not mandatory_badge,
            "payout_provider": profile.payout_provider,
            "payout_recipient_id": profile.payout_recipient_id,
            "payout_email": profile.payout_email,
            "payout_status": profile.payout_status,
            "terms_accepted_at": (
                profile.terms_accepted_at.isoformat() if profile.terms_accepted_at else None
            ),
        },
        earnings={
            "currency": "USD",
            "accrued_cents": totals.get("accrued", 0),
            "queued_cents": totals.get("queued", 0),
            "paid_cents": totals.get("paid", 0),
            "reversed_cents": totals.get("reversed", 0),
            "payout_min_cents": PAYOUT_MIN_CENTS,
            "is_recurring": True,
            "recurring_rule": (
                "15% commission accrues on each successful paid renewal while referrer is on "
                "business/enterprise with badge enabled, and both accounts remain paid/active."
            ),
        },
        recent_ledger=[
            {
                "id": r.id,
                "referred_user_id": r.referred_user_id,
                "subscription_id": r.subscription_id,
                "status": r.status,
                "event_type": r.event_type,
                "amount_cents": r.amount_cents,
                "commission_rate": r.commission_rate,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "available_at": r.available_at.isoformat() if r.available_at else None,
                "paid_out_at": r.paid_out_at.isoformat() if r.paid_out_at else None,
            }
            for r in rows[:15]
        ],
        payouts=[
            {
                "id": p.id,
                "status": p.status,
                "provider": p.provider,
                "provider_payout_id": p.provider_payout_id,
                "amount_cents": p.amount_cents,
                "currency": p.currency,
                "error_message": p.error_message,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "processed_at": p.processed_at.isoformat() if p.processed_at else None,
            }
            for p in payouts
        ],
    )


def handle_update_referral_settings(
    user_id: str,
    request: ReferralSettingsRequest,
    db_session: Any,
) -> ReferralSummaryResponse:
    """Update badge and payout settings for current user."""
    from gitspeak_core.db.models import User

    user = db_session.query(User).filter(User.id == user_id).first()
    if not user or not user.subscription:
        raise ValueError("No subscription found")

    profile = ensure_referral_profile(user_id, db_session)
    mandatory_badge = _is_badge_mandatory(user.subscription.tier)

    if request.badge_opt_out is not None:
        if mandatory_badge and request.badge_opt_out:
            raise ValueError(
                "Badge cannot be disabled on Free, Starter, or Pro."
            )
        profile.badge_opt_out = bool(request.badge_opt_out)

    if request.payout_provider is not None:
        provider = request.payout_provider.strip().lower()
        if provider not in {"manual", "wise"}:
            raise ValueError("payout_provider must be 'manual' or 'wise'")
        profile.payout_provider = provider

    if request.payout_recipient_id is not None:
        profile.payout_recipient_id = request.payout_recipient_id.strip() or None
    if request.payout_email is not None:
        profile.payout_email = request.payout_email.strip() or None

    if request.accept_terms:
        profile.terms_accepted_at = datetime.now(timezone.utc)
        if profile.payout_status == "pending":
            profile.payout_status = "ready"

    db_session.commit()
    return handle_get_referral_summary(user_id, db_session)


def process_recurring_referral_payouts(
    db_session: Any,
    now: datetime | None = None,
) -> dict[str, int]:
    """Queue/process payouts for accrued recurring referral ledger entries."""
    from gitspeak_core.db.models import ReferralLedgerEntry, ReferralPayout, ReferralProfile

    now = now or datetime.now(timezone.utc)
    query = (
        db_session.query(ReferralLedgerEntry)
        .filter(
            ReferralLedgerEntry.status == "accrued",
            ReferralLedgerEntry.available_at <= now,
        )
        .order_by(ReferralLedgerEntry.created_at.asc())
    )
    entries = query.all()
    if not entries:
        return {"entries_considered": 0, "payouts_created": 0, "payouts_submitted": 0}

    grouped: dict[tuple[str, str], list[Any]] = defaultdict(list)
    for entry in entries:
        grouped[(entry.referrer_user_id, entry.currency)].append(entry)

    payouts_created = 0
    payouts_submitted = 0

    for (user_id, currency), rows in grouped.items():
        amount_cents = sum(int(r.amount_cents or 0) for r in rows)
        if amount_cents < PAYOUT_MIN_CENTS:
            continue

        profile = (
            db_session.query(ReferralProfile)
            .filter(ReferralProfile.user_id == user_id)
            .first()
        )
        provider = profile.payout_provider if profile else "manual"
        recipient = profile.payout_recipient_id if profile else None

        payout = ReferralPayout(
            user_id=user_id,
            currency=currency,
            amount_cents=amount_cents,
            status="queued_manual",
            provider=provider,
        )
        db_session.add(payout)
        db_session.flush()
        payouts_created += 1

        if provider == "wise" and recipient:
            transfer_id, error_message = _submit_wise_payout(
                recipient_id=recipient,
                amount_cents=amount_cents,
                currency=currency,
                payout_id=payout.id,
            )
            if transfer_id:
                payout.status = "submitted"
                payout.provider_payout_id = transfer_id
                payout.processed_at = now
                payouts_submitted += 1
            else:
                payout.status = "failed"
                payout.error_message = error_message or "Wise transfer failed"

        for row in rows:
            if payout.status in {"queued_manual", "submitted"}:
                row.status = "queued"
                row.payout_id = payout.id

    db_session.commit()
    return {
        "entries_considered": len(entries),
        "payouts_created": payouts_created,
        "payouts_submitted": payouts_submitted,
    }


def _resolve_referral_for_checkout(
    referral_code: str,
    buyer_user_id: str,
    db_session: Any,
) -> dict[str, str]:
    """Resolve referral code for checkout custom data."""
    from gitspeak_core.db.models import ReferralProfile

    profile = (
        db_session.query(ReferralProfile)
        .filter(ReferralProfile.referral_code == referral_code)
        .first()
    )
    if not profile:
        return {}
    if profile.user_id == buyer_user_id:
        return {}
    return {
        "veridoc_referrer_user_id": profile.user_id,
        "veridoc_referral_code": referral_code,
    }


def _generate_unique_referral_code(db_session: Any) -> str:
    """Generate a short unique referral code."""
    from gitspeak_core.db.models import ReferralProfile

    for _ in range(12):
        code = secrets.token_hex(4).upper()
        exists = (
            db_session.query(ReferralProfile)
            .filter(ReferralProfile.referral_code == code)
            .first()
        )
        if not exists:
            return code
    return secrets.token_hex(8).upper()


def _is_badge_mandatory(tier: str) -> bool:
    """Badge is mandatory on free/starter/pro tiers."""
    normalized = (tier or "").strip().lower()
    return normalized in {"free", "starter", "pro"}


def _is_referrer_commission_eligible_tier(tier: str) -> bool:
    """Only business and enterprise referrers can earn recurring commission."""
    normalized = (tier or "").strip().lower()
    return normalized in {"business", "enterprise"}


def _is_paid_tier(tier: str) -> bool:
    """Return True when tier is a paid plan."""
    return (tier or "").strip().lower() in {"starter", "pro", "business", "enterprise"}


def _is_subscription_paid_active(sub: Any | None) -> bool:
    """Return True when subscription is paid and in an active lifecycle state."""
    if sub is None:
        return False
    tier = str(getattr(sub, "tier", "") or "")
    status = str(getattr(sub, "status", "") or "")
    return _is_paid_tier(tier) and _is_license_active_status(status)


def _extract_payment_amount_cents(attrs: dict[str, Any], tier: str) -> int:
    """Extract payment amount in cents from webhook payload."""
    candidates = [
        attrs.get("subtotal"),
        attrs.get("total"),
        attrs.get("subtotal_usd"),
        attrs.get("total_usd"),
    ]
    for value in candidates:
        if value is None or value == "":
            continue
        try:
            text = str(value).strip()
            if "." in text:
                amount = int(round(float(text) * 100))
            else:
                raw = int(text)
                # LemonSqueezy can send cents (>=1000) or dollars (<1000).
                amount = raw * 100 if 0 < raw < 1000 else raw
            if amount > 0:
                return amount
        except (ValueError, TypeError):
            continue
    return int(TIER_DEFAULT_MONTHLY_CENTS.get(tier, 0))


def _submit_wise_payout(
    recipient_id: str,
    amount_cents: int,
    currency: str,
    payout_id: str,
) -> tuple[str | None, str | None]:
    """Submit payout to Wise or return dry-run transfer id."""
    if WISE_DRY_RUN:
        return (f"wise_dryrun_{payout_id}", None)
    if not WISE_API_TOKEN or not WISE_PROFILE_ID:
        return (None, "Wise credentials are not configured")

    quote_url = f"{WISE_API_URL}/v3/profiles/{WISE_PROFILE_ID}/quotes"
    transfer_url = f"{WISE_API_URL}/v1/transfers"
    headers = {
        "Authorization": f"Bearer {WISE_API_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=30) as client:
            quote_resp = client.post(
                quote_url,
                headers=headers,
                json={
                    "sourceCurrency": currency,
                    "targetCurrency": currency,
                    "sourceAmount": round(amount_cents / 100.0, 2),
                },
            )
            quote_resp.raise_for_status()
            quote_id = quote_resp.json().get("id")
            if not quote_id:
                return (None, "Wise quote id is missing")

            transfer_resp = client.post(
                transfer_url,
                headers=headers,
                json={
                    "targetAccount": recipient_id,
                    "quoteUuid": str(quote_id),
                    "customerTransactionId": payout_id,
                    "details": {"reference": f"VeriDoc referral payout {payout_id}"},
                },
            )
            transfer_resp.raise_for_status()
            transfer_id = transfer_resp.json().get("id")
            if transfer_id is None:
                return (None, "Wise transfer id is missing")
            return (str(transfer_id), None)
    except (httpx.HTTPError, ValueError, RuntimeError) as exc:
        logger.warning("Wise payout failed: %s", exc)
        return (None, str(exc))


# ---------------------------------------------------------------------------
# LemonSqueezy webhook handling
# ---------------------------------------------------------------------------


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str | None = None,
) -> bool:
    """Verify LemonSqueezy webhook HMAC-SHA256 signature."""
    secret = secret or LEMONSQUEEZY_WEBHOOK_SECRET
    if not secret:
        logger.warning("No webhook secret configured, skipping verification")
        return True

    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def handle_webhook(
    event_name: str,
    event_data: dict[str, Any],
    db_session: Any,
) -> dict[str, str]:
    """Process a LemonSqueezy webhook event.

    Key events:
    - subscription_created: new subscription
    - subscription_updated: plan change, status change
    - subscription_cancelled: cancellation
    - subscription_resumed: reactivation
    - subscription_payment_success: payment received
    - subscription_payment_failed: payment failed
    """
    handlers: dict[str, Any] = {
        "subscription_created": _on_subscription_created,
        "subscription_updated": _on_subscription_updated,
        "subscription_plan_changed": _on_subscription_updated,
        "subscription_cancelled": _on_subscription_cancelled,
        "subscription_expired": _on_subscription_cancelled,
        "subscription_paused": _on_subscription_paused,
        "subscription_resumed": _on_subscription_resumed,
        "subscription_unpaused": _on_subscription_resumed,
        "subscription_payment_success": _on_payment_success,
        "subscription_payment_failed": _on_payment_failed,
        "subscription_payment_refunded": _on_payment_refunded,
        "order_refunded": _on_payment_refunded,
        "subscription_trial_ending": _on_trial_ending,
    }

    handler = handlers.get(event_name)
    if handler:
        handler(event_data, db_session)
        return {"status": "ok", "event": event_name}
    logger.info("Unhandled LemonSqueezy event: %s", event_name)
    return {"status": "ignored", "event": event_name}


def _on_subscription_created(data: dict[str, Any], db_session: Any) -> None:
    """Handle new subscription from LemonSqueezy."""
    from gitspeak_core.db.models import ReferralAttribution, Subscription

    attrs = data.get("attributes", {})
    custom_data = attrs.get("first_subscription_item", {}).get("custom", {})
    # LemonSqueezy passes custom data through checkout
    user_id = (
        custom_data.get("veridoc_user_id")
        or attrs.get("custom_data", {}).get("veridoc_user_id")
    )
    if not user_id:
        logger.warning("Subscription created without veridoc_user_id")
        return

    sub = db_session.query(Subscription).filter(Subscription.user_id == user_id).first()
    if not sub:
        logger.warning("No subscription record for user %s", user_id)
        return

    variant_id = str(attrs.get("variant_id", ""))
    tier = VARIANT_TO_TIER.get(variant_id, "free")
    limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

    sub.ls_subscription_id = str(data.get("id", ""))
    sub.ls_customer_id = str(attrs.get("customer_id", ""))
    sub.ls_variant_id = variant_id
    sub.tier = tier
    sub.status = _map_ls_status(attrs.get("status", "active"))
    sub.ai_requests_limit = limits["ai_requests"]
    sub.current_period_start = _parse_ls_date(attrs.get("created_at"))
    sub.current_period_end = _parse_ls_date(attrs.get("renews_at"))
    sub.trial_ends_at = _parse_ls_date(attrs.get("trial_ends_at"))

    ensure_referral_profile(user_id, db_session)

    referrer_user_id = (
        str(custom_data.get("veridoc_referrer_user_id", "")).strip()
        or str(attrs.get("custom_data", {}).get("veridoc_referrer_user_id", "")).strip()
    )
    referral_code = (
        str(custom_data.get("veridoc_referral_code", "")).strip()
        or str(attrs.get("custom_data", {}).get("veridoc_referral_code", "")).strip()
    )
    if referrer_user_id and referrer_user_id != user_id:
        attribution = (
            db_session.query(ReferralAttribution)
            .filter(ReferralAttribution.referred_user_id == user_id)
            .first()
        )
        if not attribution:
            attribution = ReferralAttribution(
                referrer_user_id=referrer_user_id,
                referred_user_id=user_id,
                source="checkout",
                referral_code=referral_code or None,
            )
            db_session.add(attribution)

    db_session.commit()
    _issue_or_refresh_server_license(sub, reason="subscription_created", db_session=db_session)

    logger.info("Subscription created: user=%s tier=%s", user_id, tier)


def _on_subscription_updated(data: dict[str, Any], db_session: Any) -> None:
    """Handle subscription update (plan change, status change)."""
    from gitspeak_core.db.models import Subscription

    attrs = data.get("attributes", {})
    ls_sub_id = str(data.get("id", ""))

    sub = (
        db_session.query(Subscription)
        .filter(Subscription.ls_subscription_id == ls_sub_id)
        .first()
    )
    if not sub:
        logger.warning("Unknown LemonSqueezy subscription: %s", ls_sub_id)
        return

    variant_id = str(attrs.get("variant_id", ""))
    new_tier = VARIANT_TO_TIER.get(variant_id, sub.tier)
    limits = TIER_LIMITS.get(new_tier, TIER_LIMITS["free"])

    old_tier = sub.tier
    sub.tier = new_tier
    sub.ls_variant_id = variant_id
    sub.status = _map_ls_status(attrs.get("status", sub.status))
    sub.ai_requests_limit = limits["ai_requests"]
    sub.current_period_end = _parse_ls_date(attrs.get("renews_at"))
    sub.cancel_at_period_end = attrs.get("cancelled", False)
    db_session.commit()
    _issue_or_refresh_server_license(sub, reason="subscription_updated", db_session=db_session)

    if old_tier != new_tier:
        logger.info(
            "Subscription changed: user=%s %s -> %s", sub.user_id, old_tier, new_tier
        )


def _on_subscription_cancelled(data: dict[str, Any], db_session: Any) -> None:
    """Handle subscription cancellation."""
    from gitspeak_core.db.models import Subscription

    ls_sub_id = str(data.get("id", ""))
    sub = (
        db_session.query(Subscription)
        .filter(Subscription.ls_subscription_id == ls_sub_id)
        .first()
    )
    if not sub:
        return

    attrs = data.get("attributes", {})
    # LemonSqueezy: cancelled but active until period end
    sub.cancel_at_period_end = True
    sub.status = _map_ls_status(attrs.get("status", "cancelled"))
    db_session.commit()
    _issue_or_refresh_server_license(sub, reason="subscription_cancelled", db_session=db_session)

    logger.info("Subscription cancelled: user=%s", sub.user_id)


def _on_subscription_paused(data: dict[str, Any], db_session: Any) -> None:
    """Handle subscription pause."""
    from gitspeak_core.db.models import Subscription

    ls_sub_id = str(data.get("id", ""))
    sub = (
        db_session.query(Subscription)
        .filter(Subscription.ls_subscription_id == ls_sub_id)
        .first()
    )
    if not sub:
        return
    sub.status = "paused"
    db_session.commit()
    _issue_or_refresh_server_license(sub, reason="subscription_paused", db_session=db_session)
    logger.info("Subscription paused: user=%s", sub.user_id)


def _on_subscription_resumed(data: dict[str, Any], db_session: Any) -> None:
    """Handle subscription reactivation."""
    from gitspeak_core.db.models import Subscription

    ls_sub_id = str(data.get("id", ""))
    sub = (
        db_session.query(Subscription)
        .filter(Subscription.ls_subscription_id == ls_sub_id)
        .first()
    )
    if not sub:
        return

    sub.cancel_at_period_end = False
    sub.status = "active"
    db_session.commit()
    _issue_or_refresh_server_license(sub, reason="subscription_resumed", db_session=db_session)

    logger.info("Subscription resumed: user=%s", sub.user_id)


def _on_trial_ending(data: dict[str, Any], db_session: Any) -> None:
    """Handle trial-ending webhook from LemonSqueezy.

    Looks up the subscription by LemonSqueezy subscription ID,
    resolves the associated user, builds a trial-ending notification
    email with a checkout call-to-action, and sends it via SMTP.
    Delivery failures are logged but do not raise exceptions so
    that the webhook response remains successful.

    Args:
        data: LemonSqueezy webhook event data payload containing
            subscription attributes and trial_ends_at timestamp.
        db_session: Active SQLAlchemy database session.
    """
    from gitspeak_core.db.models import Subscription, User

    attrs = data.get("attributes", {})
    ls_sub_id = str(data.get("id", ""))

    sub = (
        db_session.query(Subscription)
        .filter(Subscription.ls_subscription_id == ls_sub_id)
        .first()
    )
    if not sub:
        logger.warning("Trial-ending event for unknown subscription: %s", ls_sub_id)
        return

    user = db_session.query(User).filter(User.id == sub.user_id).first()
    if not user:
        logger.warning(
            "Trial-ending event: user not found for subscription %s", ls_sub_id
        )
        return

    trial_ends_at = _parse_ls_date(attrs.get("trial_ends_at"))
    display_name = user.full_name or user.email

    subject, html_body = _build_trial_ending_email(
        user_name=display_name,
        tier=sub.tier,
        trial_ends_at=trial_ends_at,
    )

    sent = _send_email(to_address=user.email, subject=subject, html_body=html_body)
    if sent:
        logger.info(
            "Trial-ending notification sent: user=%s tier=%s ends=%s",
            user.id,
            sub.tier,
            trial_ends_at,
        )
    else:
        logger.warning(
            "Failed to send trial-ending notification: user=%s email=%s",
            user.id,
            user.email,
        )


def _on_payment_success(data: dict[str, Any], db_session: Any) -> None:
    """Handle successful payment -- reset usage counters."""
    from gitspeak_core.db.models import (
        ReferralAttribution,
        ReferralLedgerEntry,
        ReferralProfile,
        Subscription,
    )

    attrs = data.get("attributes", {})
    ls_sub_id = str(attrs.get("subscription_id", ""))
    if not ls_sub_id:
        return

    sub = (
        db_session.query(Subscription)
        .filter(Subscription.ls_subscription_id == ls_sub_id)
        .first()
    )
    if not sub:
        return

    sub.ai_requests_used = 0
    sub.pages_generated = 0
    sub.api_calls_used = 0
    sub.status = "active"

    # Recurring commissions accrue only when:
    # - referred account is paid and active
    # - referrer account is paid and active on business/enterprise
    # - referrer has not disabled badge (badge_opt_out=False)
    attribution = (
        db_session.query(ReferralAttribution)
        .filter(ReferralAttribution.referred_user_id == sub.user_id)
        .first()
    )
    referrer_sub = None
    referrer_profile = None
    if attribution:
        referrer_sub = (
            db_session.query(Subscription)
            .filter(Subscription.user_id == attribution.referrer_user_id)
            .first()
        )
        referrer_profile = (
            db_session.query(ReferralProfile)
            .filter(ReferralProfile.user_id == attribution.referrer_user_id)
            .first()
        )

    commission_allowed = (
        attribution is not None
        and _is_subscription_paid_active(sub)
        and _is_subscription_paid_active(referrer_sub)
        and _is_referrer_commission_eligible_tier(str(getattr(referrer_sub, "tier", "")))
        and bool(referrer_profile is not None)
        and not bool(getattr(referrer_profile, "badge_opt_out", False))
    )

    if commission_allowed and attribution:
        event_id = (
            str(data.get("id", "")).strip()
            or str(attrs.get("order_id", "")).strip()
            or f"{ls_sub_id}:{attrs.get('updated_at', '')}"
        )
        already = (
            db_session.query(ReferralLedgerEntry)
            .filter(ReferralLedgerEntry.payment_event_id == event_id)
            .first()
        )
        if not already:
            paid_amount_cents = _extract_payment_amount_cents(attrs, sub.tier)
            commission_cents = int(round(paid_amount_cents * COMMISSION_RATE_DEFAULT))
            if commission_cents > 0:
                now = datetime.now(timezone.utc)
                ledger = ReferralLedgerEntry(
                    referrer_user_id=attribution.referrer_user_id,
                    referred_user_id=sub.user_id,
                    attribution_id=attribution.id,
                    subscription_id=ls_sub_id,
                    payment_event_id=event_id,
                    event_type="subscription_payment_success",
                    amount_cents=commission_cents,
                    currency=str(attrs.get("currency", "USD")).upper(),
                    commission_rate=COMMISSION_RATE_DEFAULT,
                    status="accrued",
                    available_at=now + timedelta(days=COMMISSION_GRACE_DAYS),
                    entry_details={
                        "tier": sub.tier,
                        "paid_amount_cents": paid_amount_cents,
                    },
                )
                db_session.add(ledger)
    elif attribution:
        logger.info(
            "Commission skipped for subscription=%s: policy conditions not met",
            ls_sub_id,
        )

    db_session.commit()
    _issue_or_refresh_server_license(sub, reason="subscription_payment_success", db_session=db_session)

    logger.info("Payment success, usage reset: user=%s", sub.user_id)


def _on_payment_failed(data: dict[str, Any], db_session: Any) -> None:
    """Handle failed payment."""
    from gitspeak_core.db.models import Subscription

    attrs = data.get("attributes", {})
    ls_sub_id = str(attrs.get("subscription_id", ""))
    if not ls_sub_id:
        return

    sub = (
        db_session.query(Subscription)
        .filter(Subscription.ls_subscription_id == ls_sub_id)
        .first()
    )
    if sub:
        sub.status = "past_due"
        db_session.commit()
        _issue_or_refresh_server_license(sub, reason="subscription_payment_failed", db_session=db_session)

    logger.warning("Payment failed: subscription=%s", ls_sub_id)


def _on_payment_refunded(data: dict[str, Any], db_session: Any) -> None:
    """Handle refunded payment by reversing queued/accrued commission entries."""
    from gitspeak_core.db.models import ReferralLedgerEntry, Subscription

    attrs = data.get("attributes", {})
    ls_sub_id = str(attrs.get("subscription_id", "")).strip()
    if not ls_sub_id:
        # order_refunded payload can differ; try common fields.
        ls_sub_id = str(attrs.get("subscription", "")).strip()
    if not ls_sub_id:
        return

    row = (
        db_session.query(ReferralLedgerEntry)
        .filter(
            ReferralLedgerEntry.subscription_id == ls_sub_id,
            ReferralLedgerEntry.status.in_(["accrued", "queued"]),
        )
        .order_by(ReferralLedgerEntry.created_at.desc())
        .first()
    )
    if row:
        row.status = "reversed"
        row.entry_details = row.entry_details or {}
        row.entry_details["refund_event_id"] = str(data.get("id", ""))
    sub = (
        db_session.query(Subscription)
        .filter(Subscription.ls_subscription_id == ls_sub_id)
        .first()
    )
    if sub:
        sub.status = "past_due"
    db_session.commit()
    if sub:
        _issue_or_refresh_server_license(sub, reason="subscription_payment_refunded", db_session=db_session)


# ---------------------------------------------------------------------------
# Trial ending notification
# ---------------------------------------------------------------------------

SMTP_HOST = os.environ.get("VERIDOC_SMTP_HOST", "smtp.mailgun.org")
SMTP_PORT = int(os.environ.get("VERIDOC_SMTP_PORT", "587"))
SMTP_USER = os.environ.get("VERIDOC_SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("VERIDOC_SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("VERIDOC_SMTP_FROM", "noreply@veridoc.dev")
APP_BASE_URL = os.environ.get("VERIDOC_APP_BASE_URL", "https://app.veridoc.dev")
_admin_raw = os.environ.get(
    "VERIDOC_ADMIN_EMAIL", "jane.dolska@gmail.com,eugenia@veri-doc.app"
)
ADMIN_EMAILS: list[str] = [e.strip() for e in _admin_raw.split(",") if e.strip()]


def _send_email(
    to_address: str | list[str], subject: str, html_body: str
) -> bool:
    """Send an email via SMTP with TLS.

    Connects to the configured SMTP server and delivers an HTML
    email message. Accepts a single address or a list of addresses.
    Returns True on success, False on failure. All errors are logged
    rather than raised so that webhook processing is never blocked
    by email delivery failures.

    Args:
        to_address: Recipient email address or list of addresses.
        subject: Email subject line.
        html_body: HTML content of the email body.

    Returns:
        True if the email was accepted by the SMTP server, False otherwise.
    """
    recipients = [to_address] if isinstance(to_address, str) else list(to_address)

    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning(
            "SMTP credentials not configured (VERIDOC_SMTP_USER / VERIDOC_SMTP_PASSWORD), "
            "skipping email to %s",
            recipients,
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_FROM
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, recipients, msg.as_string())
        logger.info("Email sent to %s", recipients)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed when sending to %s", recipients)
        return False
    except smtplib.SMTPRecipientsRefused:
        logger.error("Recipient refused by SMTP server: %s", recipients)
        return False
    except smtplib.SMTPException as exc:
        logger.error("SMTP error sending email to %s: %s", recipients, exc)
        return False
    except OSError as exc:
        logger.error(
            "Network error connecting to SMTP server %s:%d for %s: %s",
            SMTP_HOST,
            SMTP_PORT,
            to_address,
            exc,
        )
        return False


def _build_trial_ending_email(
    user_name: str,
    tier: str,
    trial_ends_at: datetime | None,
) -> tuple[str, str]:
    """Build the subject and HTML body for a trial-ending notification.

    Generates a professional HTML email informing the user that their
    trial period is about to expire and encouraging them to subscribe.

    Args:
        user_name: Display name or email of the user.
        tier: Current subscription tier (e.g. "starter", "pro").
        trial_ends_at: UTC datetime when the trial expires, or None.

    Returns:
        A (subject, html_body) tuple ready for _send_email.
    """
    ends_str = (
        trial_ends_at.strftime("%B %d, %Y at %H:%M UTC")
        if trial_ends_at
        else "soon"
    )
    subject = f"Your VeriDoc {tier.capitalize()} trial ends {ends_str}"
    checkout_url = f"{APP_BASE_URL}/billing/checkout?tier={tier}"

    html_body = f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1a1a1a; max-width: 600px; margin: 0 auto; padding: 24px;">
  <h2 style="color: #111;">Your VeriDoc trial is ending</h2>
  <p>Hi {user_name},</p>
  <p>Your <strong>{tier.capitalize()}</strong> trial expires on <strong>{ends_str}</strong>.
     After that date your workspace will revert to the Free tier limits
     (50 AI requests, 10 pages, 100 API calls per period).</p>
  <p>To keep full access to all {tier.capitalize()} features:</p>
  <p style="text-align: center; margin: 32px 0;">
    <a href="{checkout_url}"
       style="background: #2563eb; color: #fff; padding: 12px 32px;
              border-radius: 6px; text-decoration: none; font-weight: 600;">
      Subscribe to {tier.capitalize()}
    </a>
  </p>
  <p>If you have questions, reply to this email or visit
     <a href="{APP_BASE_URL}/support">our support page</a>.</p>
  <p style="color: #666; font-size: 13px; margin-top: 40px;">
    VeriDoc -- Automated documentation pipeline<br>
    <a href="{APP_BASE_URL}/billing" style="color: #2563eb;">Manage billing</a>
  </p>
</body>
</html>"""
    return subject, html_body


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _map_ls_status(ls_status: str) -> str:
    """Map LemonSqueezy status to internal status."""
    mapping = {
        "on_trial": "trialing",
        "active": "active",
        "paused": "paused",
        "past_due": "past_due",
        "unpaid": "unpaid",
        "cancelled": "canceled",
        "expired": "canceled",
    }
    return mapping.get(ls_status, ls_status)


def _parse_ls_date(date_str: str | None) -> datetime | None:
    """Parse LemonSqueezy ISO 8601 date string."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# Invoice request handler
# ---------------------------------------------------------------------------

TIER_DISPLAY = {
    "business": "Business",
    "enterprise": "Enterprise",
}

PERIOD_DISPLAY = {
    "monthly": "Monthly",
    "annual": "Annual",
}


def handle_create_invoice_request(
    request: InvoiceRequestCreate,
    user_id: str | None,
    db_session: Any,
) -> InvoiceRequestResponse:
    """Save an invoice request and notify the admin via email.

    Creates a persistent InvoiceRequest record in the database and sends
    a notification email to the admin with the plan details and customer
    contact information.

    Args:
        request: Validated invoice request payload.
        user_id: Authenticated user ID (may be None for unauthenticated).
        db_session: SQLAlchemy database session.

    Returns:
        InvoiceRequestResponse confirming submission.
    """
    from gitspeak_core.db.models import InvoiceRequest

    record = InvoiceRequest(
        user_id=user_id,
        full_name=request.full_name,
        email=request.email,
        company=request.company,
        plan_tier=request.plan_tier,
        billing_period=request.billing_period,
        message=request.message,
        status="pending",
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    subject, html_body = _build_invoice_request_admin_email(
        full_name=request.full_name,
        email=request.email,
        company=request.company,
        plan_tier=request.plan_tier,
        billing_period=request.billing_period,
        message=request.message,
        request_id=record.id,
    )
    _send_email(ADMIN_EMAILS, subject, html_body)

    logger.info(
        "Invoice request created: id=%s tier=%s period=%s email=%s",
        record.id,
        request.plan_tier,
        request.billing_period,
        request.email,
    )

    return InvoiceRequestResponse(
        id=record.id,
        status="pending",
        message="Invoice request submitted. We will contact you shortly.",
    )


def _build_invoice_request_admin_email(
    full_name: str,
    email: str,
    company: str | None,
    plan_tier: str,
    billing_period: str,
    message: str | None,
    request_id: str,
) -> tuple[str, str]:
    """Build admin notification email for a new invoice request.

    Args:
        full_name: Customer name from the form.
        email: Customer email for invoice delivery.
        company: Optional company name.
        plan_tier: Requested plan tier (business or enterprise).
        billing_period: Billing frequency (monthly or annual).
        message: Optional customer message.
        request_id: Database record ID.

    Returns:
        A (subject, html_body) tuple ready for _send_email.
    """
    tier_label = TIER_DISPLAY.get(plan_tier, plan_tier.capitalize())
    period_label = PERIOD_DISPLAY.get(billing_period, billing_period.capitalize())
    company_line = f"<tr><td style='padding:6px 12px;color:#666;'>Company</td><td style='padding:6px 12px;font-weight:600;'>{company}</td></tr>" if company else ""
    message_section = f"<tr><td style='padding:6px 12px;color:#666;vertical-align:top;'>Message</td><td style='padding:6px 12px;'>{message}</td></tr>" if message else ""

    subject = f"New invoice request: {tier_label} {period_label} -- {full_name}"

    html_body = f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1a1a1a; max-width: 600px; margin: 0 auto; padding: 24px;">
  <h2 style="color: #111;">New Invoice Request</h2>
  <p>A customer has requested an invoice for a VeriDoc plan.</p>
  <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
    <tr style="background: #f8f9fa;">
      <td style="padding: 6px 12px; color: #666;">Request ID</td>
      <td style="padding: 6px 12px; font-weight: 600;">{request_id}</td>
    </tr>
    <tr>
      <td style="padding: 6px 12px; color: #666;">Plan</td>
      <td style="padding: 6px 12px; font-weight: 600;">{tier_label} ({period_label})</td>
    </tr>
    <tr style="background: #f8f9fa;">
      <td style="padding: 6px 12px; color: #666;">Customer name</td>
      <td style="padding: 6px 12px; font-weight: 600;">{full_name}</td>
    </tr>
    <tr>
      <td style="padding: 6px 12px; color: #666;">Invoice email</td>
      <td style="padding: 6px 12px; font-weight: 600;"><a href="mailto:{email}">{email}</a></td>
    </tr>
    {company_line}
    {message_section}
  </table>
  <p style="margin-top: 24px;">
    <strong>Action required:</strong> Create and send an invoice for the
    <strong>{tier_label}</strong> plan ({period_label} billing) to
    <a href="mailto:{email}">{email}</a>.
  </p>
  <p style="color: #666; font-size: 13px; margin-top: 40px;">
    VeriDoc -- Automated documentation pipeline<br>
    <a href="{APP_BASE_URL}/admin" style="color: #2563eb;">Admin dashboard</a>
  </p>
</body>
</html>"""
    return subject, html_body


# ---------------------------------------------------------------------------
# Audit request handler
# ---------------------------------------------------------------------------


def handle_create_audit_request(
    request: AuditRequestCreate,
    db_session: Any,
) -> AuditRequestResponse:
    """Save a free audit request and notify the admin via email.

    Creates a persistent AuditRequest record in the database and sends
    a notification email to the admin with the prospect's details.

    Args:
        request: Validated audit request payload.
        db_session: SQLAlchemy database session.

    Returns:
        AuditRequestResponse confirming submission.
    """
    from gitspeak_core.db.models import AuditRequest

    record = AuditRequest(
        full_name=request.full_name,
        email=request.email,
        company=request.company,
        docs_url=request.docs_url,
        message=request.message,
        status="pending",
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    subject, html_body = _build_audit_request_admin_email(
        full_name=request.full_name,
        email=request.email,
        company=request.company,
        docs_url=request.docs_url,
        message=request.message,
        request_id=record.id,
    )
    _send_email(ADMIN_EMAILS, subject, html_body)

    logger.info(
        "Audit request created: id=%s email=%s company=%s",
        record.id,
        request.email,
        request.company or "(none)",
    )

    return AuditRequestResponse(
        id=record.id,
        status="pending",
        message="Audit request submitted. We will contact you within 1 business day.",
    )


def _build_audit_request_admin_email(
    full_name: str,
    email: str,
    company: str | None,
    docs_url: str | None,
    message: str | None,
    request_id: str,
) -> tuple[str, str]:
    """Build admin notification email for a new audit request.

    Args:
        full_name: Prospect name.
        email: Prospect email.
        company: Optional company name.
        docs_url: Optional documentation URL to audit.
        message: Optional message from the prospect.
        request_id: Database record ID.

    Returns:
        A (subject, html_body) tuple ready for _send_email.
    """
    company_line = f"<tr><td style='padding:6px 12px;color:#666;'>Company</td><td style='padding:6px 12px;font-weight:600;'>{company}</td></tr>" if company else ""
    docs_line = f"<tr style='background:#f8f9fa;'><td style='padding:6px 12px;color:#666;'>Docs URL</td><td style='padding:6px 12px;'><a href='{docs_url}'>{docs_url}</a></td></tr>" if docs_url else ""
    message_section = f"<tr><td style='padding:6px 12px;color:#666;vertical-align:top;'>Message</td><td style='padding:6px 12px;'>{message}</td></tr>" if message else ""

    company_suffix = f" ({company})" if company else ""
    subject = f"New audit request from {full_name}{company_suffix}"

    html_body = f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1a1a1a; max-width: 600px; margin: 0 auto; padding: 24px;">
  <h2 style="color: #111;">New Free Audit Request</h2>
  <p>A prospect has requested a free documentation audit from the landing page.</p>
  <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
    <tr style="background: #f8f9fa;">
      <td style="padding: 6px 12px; color: #666;">Request ID</td>
      <td style="padding: 6px 12px; font-weight: 600;">{request_id}</td>
    </tr>
    <tr>
      <td style="padding: 6px 12px; color: #666;">Name</td>
      <td style="padding: 6px 12px; font-weight: 600;">{full_name}</td>
    </tr>
    <tr style="background: #f8f9fa;">
      <td style="padding: 6px 12px; color: #666;">Email</td>
      <td style="padding: 6px 12px; font-weight: 600;"><a href="mailto:{email}">{email}</a></td>
    </tr>
    {company_line}
    {docs_line}
    {message_section}
  </table>
  <p style="margin-top: 24px;">
    <strong>Action required:</strong> Reply to <a href="mailto:{email}">{email}</a>
    to schedule the audit.
  </p>
  <p style="color: #666; font-size: 13px; margin-top: 40px;">
    VeriDoc -- Automated documentation pipeline<br>
    <a href="{APP_BASE_URL}/admin" style="color: #2563eb;">Admin dashboard</a>
  </p>
</body>
</html>"""
    return subject, html_body

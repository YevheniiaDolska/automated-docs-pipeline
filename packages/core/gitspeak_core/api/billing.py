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
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LemonSqueezy configuration
# ---------------------------------------------------------------------------

LEMONSQUEEZY_API_KEY = os.environ.get("LEMONSQUEEZY_API_KEY", "")
LEMONSQUEEZY_STORE_ID = os.environ.get("LEMONSQUEEZY_STORE_ID", "")
LEMONSQUEEZY_WEBHOOK_SECRET = os.environ.get("LEMONSQUEEZY_WEBHOOK_SECRET", "")
LEMONSQUEEZY_API_URL = "https://api.lemonsqueezy.com/v1"

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


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class CreateCheckoutRequest(BaseModel):
    """Request to create a LemonSqueezy checkout."""

    model_config = ConfigDict(extra="forbid")

    tier: str = Field(description="Target subscription tier")
    annual: bool = Field(default=False, description="Annual billing")
    success_url: str = Field(default="", description="Redirect URL on success")


class CheckoutResponse(BaseModel):
    """LemonSqueezy checkout URL."""

    model_config = ConfigDict(extra="forbid")

    checkout_url: str


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
    suffix = "annual" if request.annual else "monthly"
    variant_key = f"variant_{request.tier}_{suffix}"
    variant_id = os.environ.get(
        f"LS_VARIANT_{request.tier.upper()}_{suffix.upper()}", variant_key
    )

    # LemonSqueezy checkout API
    headers = {
        "Authorization": f"Bearer {LEMONSQUEEZY_API_KEY}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
    }

    checkout_data = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "email": user_email,
                    "custom": {
                        "veridoc_user_id": user_id,
                    },
                },
                "product_options": {
                    "redirect_url": request.success_url or "",
                },
            },
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
        "subscription_cancelled": _on_subscription_cancelled,
        "subscription_resumed": _on_subscription_resumed,
        "subscription_payment_success": _on_payment_success,
        "subscription_payment_failed": _on_payment_failed,
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
    from gitspeak_core.db.models import Subscription

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
    db_session.commit()

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

    logger.info("Subscription cancelled: user=%s", sub.user_id)


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
    if not sub:
        return

    sub.ai_requests_used = 0
    sub.pages_generated = 0
    sub.api_calls_used = 0
    sub.status = "active"
    db_session.commit()

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

    logger.warning("Payment failed: subscription=%s", ls_sub_id)


# ---------------------------------------------------------------------------
# Trial ending notification
# ---------------------------------------------------------------------------

SMTP_HOST = os.environ.get("VERIDOC_SMTP_HOST", "smtp.mailgun.org")
SMTP_PORT = int(os.environ.get("VERIDOC_SMTP_PORT", "587"))
SMTP_USER = os.environ.get("VERIDOC_SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("VERIDOC_SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("VERIDOC_SMTP_FROM", "noreply@veridoc.dev")
APP_BASE_URL = os.environ.get("VERIDOC_APP_BASE_URL", "https://app.veridoc.dev")


def _send_email(to_address: str, subject: str, html_body: str) -> bool:
    """Send an email via SMTP with TLS.

    Connects to the configured SMTP server and delivers a single
    HTML email message. Returns True on success, False on failure.
    All errors are logged rather than raised so that webhook
    processing is never blocked by email delivery failures.

    Args:
        to_address: Recipient email address.
        subject: Email subject line.
        html_body: HTML content of the email body.

    Returns:
        True if the email was accepted by the SMTP server, False otherwise.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning(
            "SMTP credentials not configured (VERIDOC_SMTP_USER / VERIDOC_SMTP_PASSWORD), "
            "skipping email to %s",
            to_address,
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_FROM
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, [to_address], msg.as_string())
        logger.info("Trial-ending email sent to %s", to_address)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed when sending to %s", to_address)
        return False
    except smtplib.SMTPRecipientsRefused:
        logger.error("Recipient refused by SMTP server: %s", to_address)
        return False
    except smtplib.SMTPException as exc:
        logger.error("SMTP error sending trial-ending email to %s: %s", to_address, exc)
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

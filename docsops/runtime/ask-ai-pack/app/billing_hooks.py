"""Billing hooks for entitlement checks and webhook processing."""

from __future__ import annotations

import hmac
import hashlib


def verify_webhook_signature(body: bytes, signature: str | None, secret: str) -> bool:
    if not signature or not secret:
        return False
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)


def can_use_ask_ai(plan: str, billing_mode: str) -> bool:
    """Simple plan gate; replace with real subscription checks."""
    if billing_mode == "disabled":
        return False
    if billing_mode == "bring-your-own-key":
        return True
    allowed = {"pro", "business", "enterprise"}
    return plan.lower() in allowed

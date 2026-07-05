"""Billing hooks for entitlement checks and webhook processing."""

from __future__ import annotations

import hashlib
import hmac
import time

from fastapi import HTTPException

_webhook_replay_guard: dict[str, float] = {}
WEBHOOK_MAX_SKEW_SECONDS = 300
WEBHOOK_REPLAY_TTL_SECONDS = 3600


def verify_webhook_signature(body: bytes, signature: str | None, secret: str) -> bool:
    if not signature or not secret:
        return False
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)


def enforce_webhook_replay_protection(*, body: bytes, event_id: str | None, timestamp: str | None) -> None:
    """Reject stale and replayed webhook deliveries.

    Requires a signed event id and timestamp. Deliveries outside the allowed
    clock skew are rejected, and a repeated (event id, body) pair within the TTL
    is treated as a replay.
    """
    if not event_id or not event_id.strip():
        raise HTTPException(status_code=400, detail="Missing webhook event id")
    if not timestamp or not timestamp.strip():
        raise HTTPException(status_code=400, detail="Missing webhook timestamp")
    try:
        sent_ts = int(timestamp.strip())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook timestamp") from exc

    now = int(time.time())
    if abs(now - sent_ts) > WEBHOOK_MAX_SKEW_SECONDS:
        raise HTTPException(status_code=400, detail="Stale webhook timestamp")

    stale = [key for key, ts in _webhook_replay_guard.items() if now - ts > WEBHOOK_REPLAY_TTL_SECONDS]
    for key in stale:
        _webhook_replay_guard.pop(key, None)

    digest = hashlib.sha256(body).hexdigest()
    replay_key = f"{event_id.strip()}:{digest}"
    if replay_key in _webhook_replay_guard:
        raise HTTPException(status_code=409, detail="Webhook replay detected")
    _webhook_replay_guard[replay_key] = float(now)


def can_use_ask_ai(plan: str, billing_mode: str) -> bool:
    """Simple plan gate; replace with real subscription checks."""
    if billing_mode == "disabled":
        return False
    if billing_mode == "bring-your-own-key":
        return True
    allowed = {"pro", "business", "enterprise"}
    return plan.lower() in allowed

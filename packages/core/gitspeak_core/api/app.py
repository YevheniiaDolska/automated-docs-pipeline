"""VeriDoc SaaS -- FastAPI application.

Main entry point for the VeriDoc API server.

Start server:
    uvicorn gitspeak_core.api.app:app --host 0.0.0.0 --port 8000

Production:
    gunicorn gitspeak_core.api.app:app -w 4 -k uvicorn.workers.UvicornWorker
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import secrets
import sys
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Generator
from urllib.parse import urlencode

import httpx
import jwt

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, ConfigDict, Field

from gitspeak_core.config.settings import AppSettings, get_default_settings

logger = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).resolve().parents[4]
PACK_REGISTRY_DIR = Path(
    os.environ.get("VERIOPS_PACK_REGISTRY_DIR", "/var/lib/veridoc/pack-registry")
).expanduser()
TELEMETRY_DIR = Path(
    os.environ.get("VERIOPS_TELEMETRY_DIR", "/var/lib/veridoc/telemetry")
).expanduser()
REVOCATION_LIST_PATH = Path(
    os.environ.get("VERIOPS_REVOCATION_LIST_PATH", "/var/lib/veridoc/revoked_licenses.json")
).expanduser()
EGRESS_ALLOWLIST_PATH = REPO_ROOT / "config" / "ip_protection" / "egress_allowlist.yml"
BILLING_MODE = os.environ.get("VERIDOC_BILLING_MODE", "lemonsqueezy").strip().lower()
PACK_REGISTRY_REQUIRE_SIGNATURE = os.environ.get(
    "VERIOPS_PACK_REGISTRY_REQUIRE_SIGNATURE", "true"
).strip().lower() in {"1", "true", "yes"}
PACK_REGISTRY_PUBLIC_KEY_PATH = Path(
    os.environ.get(
        "VERIOPS_PACK_REGISTRY_PUBLIC_KEY_PATH",
        str(REPO_ROOT / "docsops" / "keys" / "veriops-licensing.pub"),
    )
).expanduser()


# ---------------------------------------------------------------------------
# Sentry error tracking (initialized early, before FastAPI app creation)
# ---------------------------------------------------------------------------

def _init_sentry() -> None:
    """Initialize Sentry SDK if SENTRY_DSN is configured."""

    dsn = os.getenv("SENTRY_DSN", "")
    if not dsn:
        return

    try:
        import sentry_sdk

        environment = os.getenv("VERIDOC_ENVIRONMENT", "development")
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=0.2 if environment == "production" else 1.0,
            profiles_sample_rate=0.1 if environment == "production" else 0.5,
            send_default_pii=False,
            enable_tracing=True,
        )
        logger.info("Sentry initialized: environment=%s", environment)
    except ImportError:
        logger.warning("sentry-sdk not installed, error tracking disabled")
    except (RuntimeError, ValueError, TypeError):
        logger.exception("Failed to initialize Sentry")


_init_sentry()


# ---------------------------------------------------------------------------
# Application settings (singleton)
# ---------------------------------------------------------------------------

_settings: AppSettings | None = None


def get_settings() -> AppSettings:
    """Return cached application settings singleton."""
    global _settings
    if _settings is None:
        _settings = get_default_settings()
    return _settings


# ---------------------------------------------------------------------------
# Database session dependency
# ---------------------------------------------------------------------------


def get_db() -> Generator[Any, None, None]:
    """FastAPI dependency: yield a DB session, auto-close after request."""
    from gitspeak_core.db.engine import get_session

    session = get_session()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------


MAX_TOKEN_LENGTH_BYTES: int = 8192


def get_current_user(
    request: Request,
    authorization: str | None = Header(None),
    settings: AppSettings = Depends(get_settings),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Extract and validate JWT token from Authorization header.

    Validates token format, length, signature, and expiration.
    Logs authentication failures with the client IP address for
    audit purposes.

    Args:
        request: Incoming HTTP request (used for client IP logging).
        authorization: Authorization header value.
        settings: Application settings with secret key.
        db: Database session dependency.

    Returns:
        Dictionary with user_id, email, and tier.

    Raises:
        HTTPException: 401 if authentication fails for any reason.
    """
    client_ip = request.client.host if request.client else "unknown"

    if not authorization or not authorization.startswith("Bearer "):
        logger.warning(
            "Auth failure: missing or malformed Authorization header, "
            "client_ip=%s",
            client_ip,
        )
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = authorization.split(" ", 1)[1]

    if len(token.encode("utf-8")) > MAX_TOKEN_LENGTH_BYTES:
        logger.warning(
            "Auth failure: token exceeds maximum length of %s bytes, "
            "client_ip=%s",
            MAX_TOKEN_LENGTH_BYTES,
            client_ip,
        )
        raise HTTPException(status_code=401, detail="Token too large")

    from gitspeak_core.api.auth import decode_access_token

    try:
        token_claims = decode_access_token(
            token, settings.secret_key.get_secret_value()
        )
    except jwt.ExpiredSignatureError:
        logger.warning(
            "Auth failure: expired token, client_ip=%s",
            client_ip,
        )
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as exc:
        logger.warning(
            "Auth failure: invalid token (%s), client_ip=%s",
            type(exc).__name__,
            client_ip,
        )
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = token_claims.get("sub")
    if not user_id:
        logger.warning(
            "Auth failure: token missing 'sub' claim, client_ip=%s",
            client_ip,
        )
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Verify user exists and is active
    from gitspeak_core.db.models import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        logger.warning(
            "Auth failure: user not found or deactivated, "
            "user_id=%s, client_ip=%s",
            user_id,
            client_ip,
        )
        raise HTTPException(status_code=401, detail="User not found or deactivated")

    tier = "free"
    if user.subscription:
        tier = user.subscription.tier

    return {
        "user_id": user.id,
        "email": user.email,
        "tier": tier,
        "is_superuser": bool(getattr(user, "is_superuser", False)),
    }


# ---------------------------------------------------------------------------
# Rate limiting (in-memory, per-user)
# ---------------------------------------------------------------------------

_rate_limit_store: dict[str, list[float]] = defaultdict(list)

# Requests per minute by tier
TIER_RATE_LIMITS: dict[str, int] = {
    "free": 10,
    "starter": 30,
    "pro": 60,
    "business": 120,
    "enterprise": 300,
}


def check_rate_limit(user: dict[str, Any]) -> None:
    """Enforce per-user rate limiting based on tier."""
    user_id = user["user_id"]
    tier = user.get("tier", "free")
    limit = TIER_RATE_LIMITS.get(tier, 10)

    now = time.time()
    window = 60.0  # 1 minute
    timestamps = _rate_limit_store[user_id]

    # Remove old timestamps
    _rate_limit_store[user_id] = [ts for ts in timestamps if now - ts < window]

    if len(_rate_limit_store[user_id]) >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({limit} requests/minute for {tier} tier)",
            headers={"Retry-After": "60"},
        )

    _rate_limit_store[user_id].append(now)


def _require_ops_token(x_veriops_server_token: str | None = Header(None)) -> None:
    """Protect internal ops endpoints with a shared secret token."""
    expected = os.environ.get("VERIOPS_SERVER_SHARED_TOKEN", "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="VERIOPS_SERVER_SHARED_TOKEN is not configured on server",
        )
    if not x_veriops_server_token or x_veriops_server_token.strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid ops token")


def _load_pack_registry_public_key() -> bytes | None:
    """Load Ed25519 public key for pack signature verification."""
    if not PACK_REGISTRY_PUBLIC_KEY_PATH.exists():
        return None
    raw = PACK_REGISTRY_PUBLIC_KEY_PATH.read_bytes().strip()
    if len(raw) == 32:
        return raw
    try:
        decoded = base64.b64decode(raw)
        if len(decoded) == 32:
            return decoded
    except (ValueError, TypeError):
        return None
    return None


def _verify_ed25519_signature(message: bytes, signature: bytes, public_key: bytes) -> bool:
    """Verify Ed25519 signature with PyNaCl or cryptography fallback."""
    try:
        from nacl.signing import VerifyKey

        VerifyKey(public_key).verify(message, signature)
        return True
    except ImportError:
        logger.debug("PyNaCl unavailable; trying cryptography")
    except (RuntimeError, ValueError, TypeError, OSError):
        return False

    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message)
        return True
    except ImportError:
        logger.debug("cryptography unavailable for Ed25519 verification")
    except (RuntimeError, ValueError, TypeError, OSError):
        return False
    return False


def _load_egress_allowlist() -> tuple[set[str], list[str]]:
    """Load metadata-only allowlist used by telemetry endpoint."""
    allowed_defaults = {
        "tenant_id", "build_id", "version", "platform", "plan", "hashes",
        "health", "error_code", "duration_ms", "event", "timestamp_utc", "run_status",
    }
    blocked_defaults = [
        "content", "text", "code", "source", "prompt", "snippet", "markdown", "doc", "file",
    ]
    if not EGRESS_ALLOWLIST_PATH.exists():
        return allowed_defaults, blocked_defaults
    try:
        import yaml

        raw = yaml.safe_load(EGRESS_ALLOWLIST_PATH.read_text(encoding="utf-8")) or {}
    except (ImportError, OSError, ValueError, TypeError):
        return allowed_defaults, blocked_defaults
    if not isinstance(raw, dict):
        return allowed_defaults, blocked_defaults
    allowed = raw.get("allowed_fields", [])
    blocked = raw.get("blocked_key_patterns", [])
    allowed_set = {
        str(v).strip() for v in allowed if str(v).strip()
    } if isinstance(allowed, list) else set(allowed_defaults)
    blocked_list = [
        str(v).strip().lower() for v in blocked if str(v).strip()
    ] if isinstance(blocked, list) else list(blocked_defaults)
    if not allowed_set:
        allowed_set = set(allowed_defaults)
    if not blocked_list:
        blocked_list = list(blocked_defaults)
    return allowed_set, blocked_list


def _validate_metadata_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    allowed, blocked = _load_egress_allowlist()
    for key in payload:
        key_norm = str(key).strip()
        if key_norm not in allowed:
            return False, f"field_not_allowed:{key_norm}"
        key_low = key_norm.lower()
        if any(pattern in key_low for pattern in blocked):
            return False, f"blocked_key_pattern:{key_norm}"
    return True, "ok"


def _load_revocation_list() -> dict[str, Any]:
    if not REVOCATION_LIST_PATH.exists():
        return {}
    try:
        payload = json.loads(REVOCATION_LIST_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _save_revocation_list(payload: dict[str, Any]) -> None:
    REVOCATION_LIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    REVOCATION_LIST_PATH.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Lifespan: startup / shutdown
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown."""
    settings = get_settings()
    logger.info(
        "VeriDoc API starting: env=%s, port=%s", settings.environment, settings.port
    )

    # Create tables (dev only; use Alembic in production)
    if settings.environment == "development":
        from gitspeak_core.db.engine import get_engine
        from gitspeak_core.db.models import create_all_tables

        create_all_tables(get_engine(settings))
        logger.info("Database tables created (development mode)")

    yield

    # Shutdown
    from gitspeak_core.db.engine import reset_engine

    reset_engine()
    logger.info("VeriDoc API shutdown")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="VeriDoc API",
    description="VeriDoc SaaS Documentation Pipeline API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------------------------


@app.middleware("http")
async def log_requests(
    request: Request,
    call_next: Callable[[Request], Any],
) -> Response:
    """Log request method/path, response code, and duration."""
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(
        "%s %s -> %d (%.3fs)",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )
    return response


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return liveness signal for load balancers and uptime checks."""
    return {
        "status": "healthy",
        "service": "veridoc-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health/ready")
async def readiness_check(db: Any = Depends(get_db)) -> dict[str, str]:
    """Check database connectivity."""
    try:
        from sqlalchemy import text

        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except (RuntimeError, ValueError, TypeError, OSError) as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": str(exc)},
        )


@app.get("/health/debug-sentry", tags=["health"])
async def debug_sentry() -> dict[str, str]:
    """Trigger a test exception to verify Sentry integration.

    Only available in non-production environments.
    """
    env = os.getenv("VERIDOC_ENVIRONMENT", "development")
    if env == "production":
        raise HTTPException(status_code=404, detail="Not Found")

    try:
        raise RuntimeError("VeriDoc Sentry test -- this error is intentional")
    except RuntimeError:
        try:
            import sentry_sdk

            sentry_sdk.capture_exception()
            sentry_sdk.flush(timeout=5)
            return {"status": "ok", "message": "Test error sent to Sentry"}
        except ImportError:
            return {"status": "skipped", "message": "sentry-sdk not installed"}


# =========================================================================
# AUTH ROUTES
# =========================================================================


@app.post("/auth/register", tags=["auth"])
async def register_user(request: Request, db: Any = Depends(get_db)) -> dict[str, Any]:
    """Register a new user."""
    from gitspeak_core.api.auth import RegisterRequest, handle_register

    body = await request.json()
    try:
        req = RegisterRequest(**body)
        result = handle_register(req, db)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/auth/login", tags=["auth"])
async def login_user(request: Request, db: Any = Depends(get_db)) -> dict[str, Any]:
    """Authenticate and receive JWT token."""
    from gitspeak_core.api.auth import LoginRequest, handle_login

    body = await request.json()
    try:
        req = LoginRequest(**body)
        result = handle_login(req, db)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@app.get("/auth/me", tags=["auth"])
async def get_me(
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Get current user profile."""
    from gitspeak_core.api.auth import handle_get_profile

    try:
        result = handle_get_profile(user["user_id"], db)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


def _oauth_redirect_uri(provider: str) -> str:
    configured = os.environ.get(f"{provider.upper()}_OAUTH_REDIRECT_URI", "").strip()
    if configured:
        return configured
    app_base = os.environ.get("VERIDOC_APP_BASE_URL", "https://veri-doc.app").rstrip("/")
    return f"{app_base}/api/auth/oauth/{provider}/callback"


def _oauth_frontend_callback_url() -> str:
    configured = os.environ.get("VERIDOC_OAUTH_CALLBACK_URL", "").strip()
    if configured:
        return configured
    app_base = os.environ.get("VERIDOC_APP_BASE_URL", "https://veri-doc.app").rstrip("/")
    return f"{app_base}/oauth/callback"


def _oauth_state_token(provider: str) -> str:
    settings = get_default_settings()
    payload = {
        "provider": provider,
        "nonce": secrets.token_urlsafe(16),
        "iat": int(time.time()),
        "exp": int(time.time()) + 900,
    }
    return jwt.encode(payload, settings.secret_key.get_secret_value(), algorithm="HS256")


def _decode_oauth_state(token: str) -> dict[str, Any]:
    settings = get_default_settings()
    try:
        payload = jwt.decode(token, settings.secret_key.get_secret_value(), algorithms=["HS256"])
        if not isinstance(payload, dict):
            raise ValueError("Invalid OAuth state payload")
        return payload
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid OAuth state: {exc}") from exc


def _get_oauth_config(provider: str) -> dict[str, str]:
    normalized = provider.strip().lower()
    if normalized == "google":
        client_id = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
        if not client_id or not client_secret:
            raise HTTPException(
                status_code=503,
                detail="OAuth provider 'google' is not configured on this deployment",
            )
        return {
            "provider": "google",
            "client_id": client_id,
            "client_secret": client_secret,
            "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
            "scope": "openid email profile",
        }
    if normalized == "github":
        client_id = os.environ.get("GITHUB_CLIENT_ID", "").strip()
        client_secret = os.environ.get("GITHUB_CLIENT_SECRET", "").strip()
        if not client_id or not client_secret:
            raise HTTPException(
                status_code=503,
                detail="OAuth provider 'github' is not configured on this deployment",
            )
        return {
            "provider": "github",
            "client_id": client_id,
            "client_secret": client_secret,
            "authorize_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "userinfo_url": "https://api.github.com/user",
            "emails_url": "https://api.github.com/user/emails",
            "scope": "read:user user:email",
        }
    raise HTTPException(status_code=404, detail="OAuth provider not supported")


async def _fetch_oauth_identity(provider: str, code: str) -> dict[str, str]:
    config = _get_oauth_config(provider)
    redirect_uri = _oauth_redirect_uri(provider)
    async with httpx.AsyncClient(timeout=20) as client:
        if provider == "google":
            token_res = await client.post(
                config["token_url"],
                data={
                    "client_id": config["client_id"],
                    "client_secret": config["client_secret"],
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
            token_res.raise_for_status()
            token_payload = token_res.json()
            access_token = token_payload.get("access_token", "")
            if not access_token:
                raise HTTPException(status_code=400, detail="Google OAuth token exchange failed")
            profile_res = await client.get(
                config["userinfo_url"],
                headers={"Authorization": f"Bearer {access_token}"},
            )
            profile_res.raise_for_status()
            profile = profile_res.json()
            email = str(profile.get("email", "")).strip().lower()
            full_name = str(profile.get("name", "")).strip()
            provider_id = str(profile.get("sub", "")).strip()
        else:
            token_res = await client.post(
                config["token_url"],
                headers={"Accept": "application/json"},
                data={
                    "client_id": config["client_id"],
                    "client_secret": config["client_secret"],
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
            )
            token_res.raise_for_status()
            token_payload = token_res.json()
            access_token = token_payload.get("access_token", "")
            if not access_token:
                raise HTTPException(status_code=400, detail="GitHub OAuth token exchange failed")
            profile_res = await client.get(
                config["userinfo_url"],
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            profile_res.raise_for_status()
            profile = profile_res.json()
            email = str(profile.get("email", "")).strip().lower()
            full_name = str(profile.get("name", "")).strip()
            provider_id = str(profile.get("id", "")).strip()
            if not email:
                emails_res = await client.get(
                    config["emails_url"],
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github+json",
                    },
                )
                emails_res.raise_for_status()
                emails_payload = emails_res.json()
                if isinstance(emails_payload, list):
                    primary = next(
                        (
                            item
                            for item in emails_payload
                            if isinstance(item, dict) and item.get("primary")
                        ),
                        None,
                    )
                    if isinstance(primary, dict):
                        email = str(primary.get("email", "")).strip().lower()
                    if not email and emails_payload and isinstance(emails_payload[0], dict):
                        email = str(emails_payload[0].get("email", "")).strip().lower()
        if not email:
            raise HTTPException(
                status_code=400,
                detail=f"{provider.capitalize()} OAuth did not return an email address",
            )
        return {
            "email": email,
            "full_name": full_name,
            "provider_id": provider_id,
        }


@app.get("/auth/oauth/{provider}", tags=["auth"])
@app.get("/api/auth/oauth/{provider}", tags=["auth"])
async def oauth_start(provider: str) -> RedirectResponse:
    """Start OAuth flow for configured providers."""
    normalized = provider.strip().lower()
    config = _get_oauth_config(normalized)
    state = _oauth_state_token(normalized)
    redirect_uri = _oauth_redirect_uri(normalized)
    query = {
        "client_id": config["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": config["scope"],
        "state": state,
    }
    if normalized == "google":
        query["access_type"] = "offline"
        query["prompt"] = "consent"
    auth_url = f"{config['authorize_url']}?{urlencode(query)}"
    return RedirectResponse(url=auth_url, status_code=307)


@app.get("/auth/oauth/{provider}/callback", tags=["auth"])
@app.get("/api/auth/oauth/{provider}/callback", tags=["auth"])
async def oauth_callback(
    provider: str,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Any = Depends(get_db),
) -> RedirectResponse:
    """Complete OAuth flow and redirect to frontend callback."""
    normalized = provider.strip().lower()
    callback_url = _oauth_frontend_callback_url()
    if error:
        return RedirectResponse(
            url=f"{callback_url}?error={error}",
            status_code=307,
        )
    if normalized not in {"google", "github"}:
        raise HTTPException(status_code=404, detail="OAuth provider not supported")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing OAuth callback parameters")
    state_payload = _decode_oauth_state(state)
    if state_payload.get("provider") != normalized:
        raise HTTPException(status_code=400, detail="OAuth state provider mismatch")

    identity = await _fetch_oauth_identity(normalized, code)

    from gitspeak_core.api.auth import create_access_token, hash_password
    from gitspeak_core.api.billing import ensure_referral_profile
    from gitspeak_core.config.settings import get_default_settings
    from gitspeak_core.db.models import Subscription, User

    user = db.query(User).filter(User.email == identity["email"]).first()
    if not user:
        user = User(
            email=identity["email"],
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            full_name=identity["full_name"] or None,
        )
        db.add(user)
        db.flush()
    elif (not user.full_name) and identity["full_name"]:
        user.full_name = identity["full_name"]

    now = datetime.now(timezone.utc)
    subscription = user.subscription
    if subscription is None:
        subscription = Subscription(
            user_id=user.id,
            tier="free",
            status="trialing",
            trial_ends_at=now + timedelta(days=14),
            current_period_start=now,
            current_period_end=now + timedelta(days=14),
            ai_requests_limit=50,
        )
        db.add(subscription)

    db.commit()
    ensure_referral_profile(user.id, db)

    settings = get_default_settings()
    expires = settings.access_token_expire_minutes
    tier = subscription.tier if subscription else "free"
    token = create_access_token(
        subject=user.id,
        secret_key=settings.secret_key.get_secret_value(),
        expires_minutes=expires,
        extra_claims={"email": user.email, "tier": tier},
    )
    front_query = urlencode(
        {
            "access_token": token,
            "expires_in": str(expires * 60),
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email,
            "tier": tier,
            "provider": normalized,
        }
    )
    return RedirectResponse(url=f"{callback_url}?{front_query}", status_code=307)


# =========================================================================
# PIPELINE ROUTES
# =========================================================================


class PipelineRunRequest(BaseModel):
    """Request to start a pipeline run (async via Celery)."""

    model_config = ConfigDict(extra="forbid")

    repo_path: str = Field(description="Path to repository root")
    flow_mode: str = Field(default="code-first")
    modules: dict[str, bool] | None = None
    protocols: list[str] | None = None


class PackPublishRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pack_name: str = Field(min_length=1, max_length=120)
    version: str = Field(min_length=1, max_length=64)
    plan: str = Field(default="enterprise", max_length=32)
    checksum_sha256: str = Field(min_length=32, max_length=128)
    encrypted_blob_b64: str = Field(min_length=16)
    signature_b64: str = Field(min_length=16)


class MetadataTelemetryRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    tenant_id: str = ""
    build_id: str = ""
    version: str = ""
    platform: str = ""
    plan: str = ""
    hashes: str = ""
    health: str = ""
    error_code: str = ""
    duration_ms: int = 0
    event: str = ""
    timestamp_utc: str = ""
    run_status: str = ""
    protocols: list[str] | None = None
    doc_scope: str = "standard"


class RevocationUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str = Field(min_length=1, max_length=255)
    reason: str = Field(default="manual_revoke", max_length=255)


class ManualSubscriptionUpsertRequest(BaseModel):
    """Manual invoice billing entitlement update (ops-only)."""

    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1, max_length=64)
    tier: str = Field(pattern=r"^(free|starter|pro|business|enterprise)$")
    status: str = Field(default="active", pattern=r"^(trialing|active|past_due|canceled|unpaid|paused)$")
    period_days: int = Field(default=30, ge=1, le=366)
    source: str = Field(default="manual_invoice", max_length=80)
    reset_usage: bool = True
    external_customer_ref: str | None = Field(default=None, max_length=128)


class LicenseRenewBatchRequest(BaseModel):
    """Ops-triggered server license renewal batch options."""

    model_config = ConfigDict(extra="forbid")

    dry_run: bool = False


class RagQueryRequest(BaseModel):
    """Live retrieval query request."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=2, max_length=5000)
    top_k: int = Field(default=5, ge=1, le=30)
    source_sites: list[str] | None = None
    tenant_id: str = Field(default="", max_length=255)
    domain: str = Field(default="", max_length=255)
    plan: str = Field(default="", max_length=32)


class RagReindexRequest(BaseModel):
    """RAG reindex lifecycle trigger request."""

    model_config = ConfigDict(extra="forbid")

    with_embeddings: bool = True
    embeddings_provider: str | None = Field(default=None, pattern=r"^(openai|local)?$")


@app.post("/pipeline/run", tags=["pipeline"])
async def start_pipeline_run(
    request: PipelineRunRequest,
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, str]:
    """Start an async pipeline run. Returns run_id for status polling."""
    check_rate_limit(user)

    from gitspeak_core.api.billing import check_quota

    if not check_quota(user["user_id"], "api_calls", db):
        raise HTTPException(status_code=402, detail="API call quota exceeded")

    from gitspeak_core.db.models import PipelineRun

    run = PipelineRun(
        user_id=user["user_id"],
        status="pending",
        trigger="manual",
        repo_path=request.repo_path,
        flow_mode=request.flow_mode,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Dispatch to Celery
    try:
        from gitspeak_core.tasks.pipeline_tasks import run_pipeline_async

        task = run_pipeline_async.delay(
            user_id=user["user_id"],
            run_id=run.id,
            repo_path=request.repo_path,
            flow_mode=request.flow_mode,
            modules=request.modules,
            protocols=request.protocols,
            user_tier=user["tier"],
        )
        run.celery_task_id = task.id
        db.commit()
    except (RuntimeError, ValueError, TypeError, OSError):
        # Celery not available -- run synchronously as fallback
        logger.warning("Celery not available, running pipeline synchronously")
        from gitspeak_core.api.pipeline import RunPipelineRequest, handle_run_pipeline

        req = RunPipelineRequest(
            repo_path=request.repo_path,
            flow_mode=request.flow_mode,
            modules=request.modules,
            protocols=request.protocols,
        )
        result = handle_run_pipeline(req, user_tier=user["tier"])
        run.status = "completed" if result.status == "ok" else "failed"
        run.phases = [p.model_dump() for p in result.phases]
        run.artifacts = result.artifacts
        run.errors = result.errors
        run.report = result.report
        run.completed_at = datetime.now(timezone.utc)
        db.commit()

    return {
        "run_id": run.id,
        "status": run.status,
        "message": "Pipeline run queued",
    }


@app.get("/pipeline/runs", tags=["pipeline"])
async def list_pipeline_runs(
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
) -> dict[str, list[dict[str, Any]]]:
    """List pipeline runs for current user."""
    from gitspeak_core.db.models import PipelineRun

    runs = (
        db.query(PipelineRun)
        .filter(PipelineRun.user_id == user["user_id"])
        .order_by(PipelineRun.created_at.desc())
        .offset(offset)
        .limit(min(limit, 100))
        .all()
    )

    return {
        "runs": [
            {
                "id": r.id,
                "status": r.status,
                "trigger": r.trigger,
                "flow_mode": r.flow_mode,
                "duration_seconds": r.duration_seconds,
                "quality_score": r.quality_score,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in runs
        ]
    }


@app.get("/pipeline/runs/{run_id}", tags=["pipeline"])
async def get_pipeline_run(
    run_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Get details of a specific pipeline run."""
    from gitspeak_core.db.models import PipelineRun

    run = (
        db.query(PipelineRun)
        .filter(PipelineRun.id == run_id, PipelineRun.user_id == user["user_id"])
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return {
        "id": run.id,
        "status": run.status,
        "trigger": run.trigger,
        "flow_mode": run.flow_mode,
        "phases": run.phases or [],
        "artifacts": run.artifacts or [],
        "errors": run.errors or [],
        "report": run.report,
        "quality_score": run.quality_score,
        "duration_seconds": run.duration_seconds,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


@app.post("/rag/query", tags=["rag"])
async def rag_query(
    request: RagQueryRequest,
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Run live retrieval query over the knowledge index with RBAC/ACL filters."""
    check_rate_limit(user)

    from gitspeak_core.api.rag_runtime import (
        append_rag_query_metric,
        infer_user_roles,
        load_ask_ai_config,
        load_retrieval_index,
        search_retrieval_index,
    )
    from gitspeak_core.db.models import PipelineSettings

    started = time.time()
    ask_cfg = load_ask_ai_config(REPO_ROOT)
    if not bool(ask_cfg.get("enabled", False)):
        raise HTTPException(status_code=400, detail="Ask AI is disabled")

    user_roles = infer_user_roles(user)
    allowed_roles = {
        str(v).strip().lower()
        for v in (ask_cfg.get("allowed_roles", []) if isinstance(ask_cfg.get("allowed_roles"), list) else [])
        if str(v).strip()
    }
    require_auth = bool(ask_cfg.get("require_user_auth", True))
    if require_auth and allowed_roles and user_roles.isdisjoint(allowed_roles):
        raise HTTPException(status_code=403, detail="RAG access forbidden for current role")

    settings_row = (
        db.query(PipelineSettings)
        .filter(PipelineSettings.user_id == user["user_id"])
        .first()
    )
    allowed_source_sites: set[str] = set()
    requested_tenant = str(request.tenant_id or "").strip().lower()
    requested_domain = str(request.domain or "").strip().lower()
    requested_plan = str(request.plan or user.get("tier", "free")).strip().lower()

    if settings_row and isinstance(settings_row.custom_config, dict):
        rag_acl = settings_row.custom_config.get("rag_acl", {})
        if isinstance(rag_acl, dict) and isinstance(rag_acl.get("allowed_source_sites"), list):
            allowed_source_sites = {
                str(v).strip().lower()
                for v in rag_acl.get("allowed_source_sites", [])
                if str(v).strip()
            }
        if isinstance(rag_acl, dict) and isinstance(rag_acl.get("allowed_tenants"), list) and requested_tenant:
            allowed_tenants = {str(v).strip().lower() for v in rag_acl.get("allowed_tenants", []) if str(v).strip()}
            if allowed_tenants and requested_tenant not in allowed_tenants:
                raise HTTPException(status_code=403, detail="RAG tenant ACL denied")
        if isinstance(rag_acl, dict) and isinstance(rag_acl.get("allowed_domains"), list) and requested_domain:
            allowed_domains = {str(v).strip().lower() for v in rag_acl.get("allowed_domains", []) if str(v).strip()}
            if allowed_domains and requested_domain not in allowed_domains:
                raise HTTPException(status_code=403, detail="RAG domain ACL denied")
        if isinstance(rag_acl, dict) and isinstance(rag_acl.get("allowed_plans"), list):
            allowed_plans = {str(v).strip().lower() for v in rag_acl.get("allowed_plans", []) if str(v).strip()}
            if allowed_plans and requested_plan and requested_plan not in allowed_plans:
                raise HTTPException(status_code=403, detail="RAG plan ACL denied")
    if request.source_sites:
        request_sites = {str(v).strip().lower() for v in request.source_sites if str(v).strip()}
        allowed_source_sites = request_sites if not allowed_source_sites else allowed_source_sites.intersection(request_sites)

    rows = load_retrieval_index(REPO_ROOT, ask_cfg)
    hits, blocked = search_retrieval_index(
        query=request.query,
        rows=rows,
        user_tier=str(user.get("tier", "free")),
        user_roles=user_roles,
        allowed_source_sites=allowed_source_sites,
        top_k=request.top_k,
    )
    latency_ms = int((time.time() - started) * 1000)
    append_rag_query_metric(
        telemetry_dir=TELEMETRY_DIR,
        user_id=str(user.get("user_id", "")),
        tier=str(user.get("tier", "free")),
        query=request.query,
        top_k=request.top_k,
        hits_count=len(hits),
        blocked_count=blocked,
        latency_ms=latency_ms,
        retrieval_mode="token",
    )

    return {
        "status": "ok",
        "query": request.query,
        "top_k": request.top_k,
        "hits": hits,
        "metrics": {
            "latency_ms": latency_ms,
            "candidate_count": len(rows),
            "acl_blocked_count": blocked,
            "returned_count": len(hits),
        },
    }


@app.post("/rag/runtime/query", tags=["rag"])
async def rag_runtime_query(
    request: RagQueryRequest,
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Unified runtime RAG query endpoint alias."""
    return await rag_query(request=request, user=user, db=db)


@app.get("/rag/metrics", tags=["rag"])
async def rag_metrics(
    _user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Return unified RAG observability snapshot."""
    from gitspeak_core.api.rag_runtime import evaluate_rag_alerts, load_rag_metrics_snapshot

    reports_dir = REPO_ROOT / "reports"
    snapshot = load_rag_metrics_snapshot(
        telemetry_dir=TELEMETRY_DIR,
        reports_dir=reports_dir,
    )
    alerts = evaluate_rag_alerts(snapshot=snapshot)
    level = "ok" if not alerts else "degraded"
    snapshot_path = reports_dir / "rag_metrics_snapshot.json"
    snapshot_path.write_text(
        json.dumps({"status": level, "snapshot": snapshot, "alerts": alerts}, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"status": level, "snapshot": snapshot, "alerts": alerts}


@app.get("/rag/alerts", tags=["rag"])
async def rag_alerts(
    _user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Return current RAG SLO alerts."""
    from gitspeak_core.api.rag_runtime import evaluate_rag_alerts, load_rag_metrics_snapshot

    reports_dir = REPO_ROOT / "reports"
    snapshot = load_rag_metrics_snapshot(
        telemetry_dir=TELEMETRY_DIR,
        reports_dir=reports_dir,
    )
    alerts = evaluate_rag_alerts(snapshot=snapshot)
    return {
        "status": "ok" if not alerts else "degraded",
        "alerts": alerts,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/rag/reindex", tags=["rag"])
async def rag_reindex(
    request: RagReindexRequest,
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Trigger standalone RAG reindex lifecycle with versioned artifacts."""
    if str(user.get("tier", "free")).strip().lower() not in {"business", "enterprise"}:
        raise HTTPException(status_code=403, detail="RAG reindex requires Business or Enterprise tier")

    from gitspeak_core.api.rag_runtime import resolve_embeddings_provider, run_reindex_lifecycle

    provider = resolve_embeddings_provider(request.embeddings_provider)
    try:
        report = run_reindex_lifecycle(
            repo_root=REPO_ROOT,
            python_bin=sys.executable,
            include_embeddings=bool(request.with_embeddings),
            embeddings_provider=provider,
        )
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"status": "ok", "report": report}


# =========================================================================
# SETTINGS ROUTES
# =========================================================================


@app.get("/settings", tags=["settings"])
async def get_pipeline_settings(
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Get pipeline settings for current user."""
    from gitspeak_core.db.models import PipelineSettings as PipelineSettingsModel

    settings = (
        db.query(PipelineSettingsModel)
        .filter(PipelineSettingsModel.user_id == user["user_id"])
        .first()
    )

    if not settings:
        # Return defaults
        return {
            "modules": {},
            "flow_mode": "code-first",
            "default_protocols": ["rest"],
            "algolia_enabled": False,
            "sandbox_backend": "external",
        }

    return {
        "modules": settings.modules or {},
        "flow_mode": settings.flow_mode,
        "default_protocols": settings.default_protocols or ["rest"],
        "algolia_enabled": settings.algolia_enabled,
        "algolia_config": settings.algolia_config,
        "sandbox_backend": settings.sandbox_backend,
        "repo_path": settings.repo_path,
    }


@app.put("/settings", tags=["settings"])
async def update_pipeline_settings(
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, str]:
    """Update pipeline settings."""
    body = await request.json()

    from gitspeak_core.api.settings import AVAILABLE_MODULES
    from gitspeak_core.db.models import PipelineSettings as PipelineSettingsModel

    settings = (
        db.query(PipelineSettingsModel)
        .filter(PipelineSettingsModel.user_id == user["user_id"])
        .first()
    )

    if not settings:
        settings = PipelineSettingsModel(user_id=user["user_id"])
        db.add(settings)

    # Validate module tier access
    user_tier = user["tier"]
    tier_order = ["free", "starter", "pro", "business", "enterprise"]
    user_tier_idx = tier_order.index(user_tier) if user_tier in tier_order else 0

    if "modules" in body:
        modules = body["modules"]
        # Filter out modules user does not have access to
        min_tiers = {m["key"]: m["min_tier"] for m in AVAILABLE_MODULES}
        validated = {}
        for key, enabled in modules.items():
            min_tier = min_tiers.get(key, "enterprise")
            min_idx = tier_order.index(min_tier) if min_tier in tier_order else 4
            if user_tier_idx >= min_idx:
                validated[key] = enabled
        settings.modules = validated

    if "flow_mode" in body:
        settings.flow_mode = body["flow_mode"]
    if "default_protocols" in body:
        settings.default_protocols = body["default_protocols"]
    if "algolia_enabled" in body:
        settings.algolia_enabled = body["algolia_enabled"]
    if "algolia_config" in body:
        settings.algolia_config = body["algolia_config"]
    if "sandbox_backend" in body:
        settings.sandbox_backend = body["sandbox_backend"]
    if "repo_path" in body:
        settings.repo_path = body["repo_path"]

    db.commit()

    return {"status": "ok", "message": "Settings updated"}


@app.get("/settings/modules", tags=["settings"])
async def list_modules(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    """List available modules with tier gating info."""
    from gitspeak_core.api.settings import AVAILABLE_MODULES

    tier_order = ["free", "starter", "pro", "business", "enterprise"]
    user_tier = user["tier"]
    user_idx = tier_order.index(user_tier) if user_tier in tier_order else 0

    result = []
    for mod in AVAILABLE_MODULES:
        min_idx = tier_order.index(mod["min_tier"]) if mod["min_tier"] in tier_order else 4
        result.append(
            {
                **mod,
                "available": user_idx >= min_idx,
            }
        )

    return {"modules": result, "user_tier": user_tier}


# =========================================================================
# AUTOMATION SCHEDULE ROUTES
# =========================================================================


class CreateScheduleRequest(BaseModel):
    """Request to create an automation schedule."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(max_length=200)
    cron_expr: str = Field(description="Cron expression (e.g., '0 3 * * 1')")
    pipeline_config: dict[str, Any] | None = None


@app.post("/automation/schedules", tags=["automation"])
async def create_schedule(
    request: CreateScheduleRequest,
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Create a new automation schedule (Pro+ tier)."""
    tier_order = ["free", "starter", "pro", "business", "enterprise"]
    if tier_order.index(user.get("tier", "free")) < 2:  # pro = index 2
        raise HTTPException(
            status_code=403, detail="Automation requires Pro tier or higher"
        )

    from gitspeak_core.db.models import AutomationSchedule

    schedule = AutomationSchedule(
        user_id=user["user_id"],
        name=request.name,
        cron_expr=request.cron_expr,
        pipeline_config=request.pipeline_config,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    return {
        "id": schedule.id,
        "name": schedule.name,
        "cron_expr": schedule.cron_expr,
        "enabled": schedule.enabled,
    }


@app.get("/automation/schedules", tags=["automation"])
async def list_schedules(
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, list[dict[str, Any]]]:
    """List automation schedules."""
    from gitspeak_core.db.models import AutomationSchedule

    schedules = (
        db.query(AutomationSchedule)
        .filter(AutomationSchedule.user_id == user["user_id"])
        .all()
    )

    return {
        "schedules": [
            {
                "id": s.id,
                "name": s.name,
                "cron_expr": s.cron_expr,
                "enabled": s.enabled,
                "last_run_at": s.last_run_at.isoformat() if s.last_run_at else None,
                "next_run_at": s.next_run_at.isoformat() if s.next_run_at else None,
            }
            for s in schedules
        ]
    }


@app.put("/automation/schedules/{schedule_id}", tags=["automation"])
async def update_schedule(
    schedule_id: str,
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, str]:
    """Update an automation schedule."""
    from gitspeak_core.db.models import AutomationSchedule

    schedule = (
        db.query(AutomationSchedule)
        .filter(
            AutomationSchedule.id == schedule_id,
            AutomationSchedule.user_id == user["user_id"],
        )
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    body = await request.json()
    if "name" in body:
        schedule.name = body["name"]
    if "cron_expr" in body:
        schedule.cron_expr = body["cron_expr"]
    if "enabled" in body:
        schedule.enabled = body["enabled"]
    if "pipeline_config" in body:
        schedule.pipeline_config = body["pipeline_config"]

    db.commit()
    return {"status": "ok"}


@app.delete("/automation/schedules/{schedule_id}", tags=["automation"])
async def delete_schedule(
    schedule_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, str]:
    """Delete an automation schedule."""
    from gitspeak_core.db.models import AutomationSchedule

    schedule = (
        db.query(AutomationSchedule)
        .filter(
            AutomationSchedule.id == schedule_id,
            AutomationSchedule.user_id == user["user_id"],
        )
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    db.delete(schedule)
    db.commit()
    return {"status": "ok"}


# =========================================================================
# BILLING ROUTES (LemonSqueezy)
# =========================================================================


@app.post("/billing/checkout", tags=["billing"])
async def create_checkout(
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Create a LemonSqueezy checkout URL."""
    from gitspeak_core.api.billing import CreateCheckoutRequest, handle_create_checkout

    body = await request.json()
    try:
        req = CreateCheckoutRequest(**body)
        result = handle_create_checkout(req, user["user_id"], user["email"], db)
        return result.model_dump()
    except (RuntimeError, ValueError, TypeError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/billing/portal", tags=["billing"])
async def get_portal(
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Get LemonSqueezy customer portal URL."""
    from gitspeak_core.api.billing import handle_get_portal_url

    try:
        result = handle_get_portal_url(user["user_id"], db)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/billing/usage", tags=["billing"])
async def get_usage(
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Get current billing period usage."""
    from gitspeak_core.api.billing import handle_get_usage

    try:
        result = handle_get_usage(user["user_id"], db)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/billing/license/status", tags=["billing"])
async def get_billing_license_status(
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Return current server-managed license status for authenticated user."""
    from gitspeak_core.api.billing import handle_get_server_license_status

    try:
        result = handle_get_server_license_status(user["user_id"], db)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/billing/license/token", tags=["billing"])
async def get_billing_license_token(
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Return current server-managed license JWT for authenticated user."""
    from gitspeak_core.api.billing import handle_get_server_license_token

    try:
        result = handle_get_server_license_token(user["user_id"], db)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/billing/referrals", tags=["billing"])
async def get_referral_summary(
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Get badge policy, recurring referral earnings, and payout history."""
    from gitspeak_core.api.billing import handle_get_referral_summary

    try:
        result = handle_get_referral_summary(user["user_id"], db)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.put("/billing/referrals", tags=["billing"])
async def update_referral_settings(
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Update badge opt-out and payout settings for current user."""
    from gitspeak_core.api.billing import (
        ReferralSettingsRequest,
        handle_update_referral_settings,
    )

    body = await request.json()
    try:
        req = ReferralSettingsRequest(**body)
        result = handle_update_referral_settings(user["user_id"], req, db)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/billing/referrals/payouts/run", tags=["billing"])
async def run_referral_payouts(
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Process referral payout queue (manual trigger for operator/admin use)."""
    from gitspeak_core.api.billing import process_recurring_referral_payouts

    if user.get("tier") not in {"business", "enterprise"}:
        raise HTTPException(
            status_code=403,
            detail="Referral payout run requires Business tier or higher.",
        )
    return process_recurring_referral_payouts(db)


@app.post("/billing/invoice-request", tags=["billing"])
async def create_invoice_request(
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Submit an invoice request for Business or Enterprise plans."""
    from gitspeak_core.api.billing import InvoiceRequestCreate, handle_create_invoice_request

    body = await request.json()
    try:
        req = InvoiceRequestCreate(**body)
        result = handle_create_invoice_request(req, user["user_id"], db)
        return result.model_dump()
    except (RuntimeError, ValueError, TypeError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/contact/audit-request", tags=["contact"])
@app.post("/api/contact/audit-request", tags=["contact"])
async def create_audit_request(
    request: Request,
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Submit a free documentation audit request (public, no auth required)."""
    from gitspeak_core.api.billing import AuditRequestCreate, handle_create_audit_request

    body = await request.json()
    try:
        req = AuditRequestCreate(**body)
        result = handle_create_audit_request(req, db)
        return result.model_dump()
    except (RuntimeError, ValueError, TypeError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/pricing/plans", tags=["billing"])
async def get_plans() -> dict[str, Any]:
    """Return public pricing data for all plans."""
    from gitspeak_core.config.pricing import get_pricing_data

    return get_pricing_data()


@app.post("/billing/webhooks/lemonsqueezy", tags=["billing"])
async def lemonsqueezy_webhook(
    request: Request,
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Handle LemonSqueezy webhook events.

    Verifies HMAC signature and processes subscription lifecycle events.
    """
    from gitspeak_core.api.billing import handle_webhook, verify_webhook_signature

    if BILLING_MODE in {"manual", "invoice", "custom"}:
        return {
            "status": "ignored",
            "event": "manual_billing_mode",
            "detail": "LemonSqueezy webhook handling is disabled in manual billing mode",
        }

    payload = await request.body()
    signature = request.headers.get("x-signature", "")

    if not verify_webhook_signature(payload, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    body = await request.json()
    event_name = body.get("meta", {}).get("event_name", "")
    event_data = body.get("data", {})

    result = handle_webhook(event_name, event_data, db)
    return result


@app.post("/billing/webhooks/manual", tags=["billing"])
async def manual_billing_webhook(
    request: Request,
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Handle manual billing webhook events for invoice-based flows."""
    from gitspeak_core.api.billing import (
        handle_manual_billing_webhook,
        verify_manual_billing_webhook_signature,
    )

    payload = await request.body()
    signature = request.headers.get("x-manual-signature", "")
    if not verify_manual_billing_webhook_signature(payload, signature):
        raise HTTPException(status_code=400, detail="Invalid manual webhook signature")

    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Invalid webhook payload")
    event_name = str(
        body.get("event_name")
        or body.get("event")
        or body.get("type")
        or ""
    ).strip()
    event_data = body.get("data")
    if not isinstance(event_data, dict):
        event_data = body
    result = handle_manual_billing_webhook(event_name, event_data, db)
    return result


@app.post("/ops/billing/manual-subscription/upsert", tags=["ops"])
async def ops_manual_subscription_upsert(
    request: ManualSubscriptionUpsertRequest,
    _auth: None = Depends(_require_ops_token),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Upsert subscription tier/status for manual invoice workflows."""
    from gitspeak_core.api.billing import handle_manual_subscription_upsert

    try:
        return handle_manual_subscription_upsert(request.model_dump(), db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/ops/billing/license/renew/run", tags=["ops"])
async def ops_run_license_renew_batch(
    request: LicenseRenewBatchRequest,
    db: Any = Depends(get_db),
    _auth: None = Depends(_require_ops_token),
) -> dict[str, Any]:
    """Run server-side license auto-renew batch (hybrid/cloud operator job)."""
    from gitspeak_core.api.billing import run_license_autorenew_batch

    if request.dry_run:
        return {"status": "ok", "dry_run": True}
    return {
        "status": "ok",
        "result": run_license_autorenew_batch(db),
    }


# =========================================================================
# OPS ROUTES (server-side entitlement, pack-registry, metadata telemetry)
# =========================================================================


@app.post("/ops/pack-registry/publish", tags=["ops"])
async def publish_pack(
    request: PackPublishRequest,
    _auth: None = Depends(_require_ops_token),
) -> dict[str, Any]:
    """Publish encrypted+signed pack to server registry."""
    blob_b64 = request.encrypted_blob_b64.strip()
    signature_b64 = request.signature_b64.strip()
    try:
        blob_bytes = base64.b64decode(blob_b64, validate=True)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid encrypted_blob_b64")
    if not blob_bytes:
        raise HTTPException(status_code=400, detail="Pack blob is empty")

    expected_checksum = hashlib.sha256(blob_bytes).hexdigest()
    provided_checksum = request.checksum_sha256.strip().lower()
    if expected_checksum != provided_checksum:
        raise HTTPException(status_code=400, detail="Checksum mismatch")

    signature_verified = False
    public_key = _load_pack_registry_public_key()
    if PACK_REGISTRY_REQUIRE_SIGNATURE:
        if public_key is None:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Pack signature verification is required but public key is missing. "
                    f"Expected key path: {PACK_REGISTRY_PUBLIC_KEY_PATH}"
                ),
            )
        try:
            signature_bytes = base64.b64decode(signature_b64, validate=True)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid signature_b64")
        signature_verified = _verify_ed25519_signature(blob_bytes, signature_bytes, public_key)
        if not signature_verified:
            raise HTTPException(status_code=400, detail="Invalid pack signature")

    safe_name = request.pack_name.strip().lower().replace("..", "").replace("/", "-")
    safe_version = request.version.strip().replace("/", "-")
    pack_dir = PACK_REGISTRY_DIR / safe_name
    pack_dir.mkdir(parents=True, exist_ok=True)
    pack_path = pack_dir / f"{safe_version}.enc.b64"
    meta_path = pack_dir / f"{safe_version}.json"

    pack_path.write_text(blob_b64 + "\n", encoding="utf-8")
    metadata = {
        "pack_name": safe_name,
        "version": safe_version,
        "plan": request.plan,
        "checksum_sha256": provided_checksum,
        "signature_b64": signature_b64,
        "signature_verified": signature_verified,
        "published_at_utc": datetime.now(timezone.utc).isoformat(),
        "storage_path": str(pack_path),
    }
    meta_path.write_text(json.dumps(metadata, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "ok",
        "pack_name": safe_name,
        "version": safe_version,
    }


@app.get("/ops/pack-registry/fetch", tags=["ops"])
async def fetch_pack(
    pack_name: str,
    version: str,
    _auth: None = Depends(_require_ops_token),
) -> dict[str, Any]:
    """Fetch encrypted pack payload and signature by pack name + version."""
    safe_name = pack_name.strip().lower().replace("..", "").replace("/", "-")
    safe_version = version.strip().replace("/", "-")
    pack_dir = PACK_REGISTRY_DIR / safe_name
    meta_path = pack_dir / f"{safe_version}.json"
    blob_path = pack_dir / f"{safe_version}.enc.b64"
    if not meta_path.exists() or not blob_path.exists():
        raise HTTPException(status_code=404, detail="Pack version not found")
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        raise HTTPException(status_code=500, detail="Pack metadata is corrupted")
    if not isinstance(meta, dict):
        raise HTTPException(status_code=500, detail="Pack metadata format is invalid")
    blob = blob_path.read_text(encoding="utf-8").strip()
    return {
        "pack_name": safe_name,
        "version": safe_version,
        "plan": str(meta.get("plan", "")),
        "checksum_sha256": str(meta.get("checksum_sha256", "")),
        "signature_b64": str(meta.get("signature_b64", "")),
        "signature_verified": bool(meta.get("signature_verified", False)),
        "encrypted_blob_b64": blob,
    }


@app.post("/ops/telemetry/metadata", tags=["ops"])
async def ingest_metadata_telemetry(
    request: MetadataTelemetryRequest,
    _auth: None = Depends(_require_ops_token),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Ingest metadata-only telemetry (no client docs/code allowed)."""
    payload = request.model_dump(exclude_none=True)
    valid, reason = _validate_metadata_payload(payload)
    if not valid:
        raise HTTPException(status_code=400, detail=f"Telemetry payload rejected: {reason}")
    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps(
        {
            **payload,
            "received_at_utc": datetime.now(timezone.utc).isoformat(),
        },
        ensure_ascii=True,
    )
    log_path = TELEMETRY_DIR / "metadata_events.ndjson"
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")

    # Best-effort DB audit trail.
    try:
        from gitspeak_core.db.models import AuditLog

        db.add(
            AuditLog(
                user_id=None,
                action="ops.metadata_telemetry",
                resource_type="telemetry",
                resource_id=str(payload.get("tenant_id", "")) or None,
                details=payload,
            )
        )
        db.commit()
    except (RuntimeError, ValueError, TypeError, OSError):
        db.rollback()
    return {"status": "ok"}


@app.get("/billing/license/revocation-check", tags=["billing"])
async def revocation_check(
    tenant_id: str = "",
    build_id: str = "",
    version: str = "",
    platform: str = "",
    plan: str = "",
    event: str = "",
    timestamp_utc: str = "",
) -> dict[str, Any]:
    """Return revocation status for metadata-only license check requests."""
    payload = {
        "tenant_id": tenant_id,
        "build_id": build_id,
        "version": version,
        "platform": platform,
        "plan": plan,
        "event": event or "revocation_check",
        "timestamp_utc": timestamp_utc,
    }
    normalized = {k: v for k, v in payload.items() if str(v).strip()}
    valid, reason = _validate_metadata_payload(normalized)
    if not valid:
        raise HTTPException(status_code=400, detail=f"Revocation payload rejected: {reason}")

    revoked_ids = {
        part.strip()
        for part in os.environ.get("VERIOPS_REVOKED_TENANTS", "").split(",")
        if part.strip()
    }
    revoked = False
    revoke_reason = ""
    tenant = str(normalized.get("tenant_id", "")).strip()
    if tenant and tenant in revoked_ids:
        revoked = True
        revoke_reason = "tenant_revoked_env"

    if not revoked:
        revocation_list = _load_revocation_list()
        blocked = revocation_list.get("revoked_tenants", [])
        if isinstance(blocked, list) and tenant and tenant in {str(v).strip() for v in blocked}:
            revoked = True
            revoke_reason = str(revocation_list.get("reason", "tenant_revoked_list")).strip() or "tenant_revoked_list"

    return {
        "revoked": revoked,
        "reason": revoke_reason,
    }


@app.get("/ops/revocation/list", tags=["ops"])
async def ops_revocation_list(
    _auth: None = Depends(_require_ops_token),
) -> dict[str, Any]:
    """Return current tenant revocation entries."""
    revocation_list = _load_revocation_list()
    blocked = revocation_list.get("revoked_tenants", [])
    tenants = (
        sorted({str(v).strip() for v in blocked if str(v).strip()})
        if isinstance(blocked, list)
        else []
    )
    return {
        "status": "ok",
        "revoked_tenants": tenants,
        "reason": str(revocation_list.get("reason", "manual_revoke")).strip() or "manual_revoke",
        "updated_at_utc": str(revocation_list.get("updated_at_utc", "")),
    }


@app.post("/ops/revocation/upsert", tags=["ops"])
async def ops_revocation_upsert(
    request: RevocationUpsertRequest,
    _auth: None = Depends(_require_ops_token),
) -> dict[str, Any]:
    """Insert tenant into revocation list (or refresh existing entry)."""
    revocation_list = _load_revocation_list()
    blocked = revocation_list.get("revoked_tenants", [])
    current = (
        {str(v).strip() for v in blocked if str(v).strip()}
        if isinstance(blocked, list)
        else set()
    )
    tenant = request.tenant_id.strip()
    current.add(tenant)
    payload = {
        "revoked_tenants": sorted(current),
        "reason": request.reason.strip() or "manual_revoke",
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    try:
        _save_revocation_list(payload)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to persist revocation list: {exc}")
    return {"status": "ok", "tenant_id": tenant, "revoked": True}


@app.delete("/ops/revocation/{tenant_id}", tags=["ops"])
async def ops_revocation_delete(
    tenant_id: str,
    _auth: None = Depends(_require_ops_token),
) -> dict[str, Any]:
    """Remove tenant from revocation list."""
    tenant = str(tenant_id).strip()
    if not tenant:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    revocation_list = _load_revocation_list()
    blocked = revocation_list.get("revoked_tenants", [])
    current = (
        {str(v).strip() for v in blocked if str(v).strip()}
        if isinstance(blocked, list)
        else set()
    )
    existed = tenant in current
    if existed:
        current.remove(tenant)
    payload = {
        "revoked_tenants": sorted(current),
        "reason": str(revocation_list.get("reason", "manual_revoke")).strip() or "manual_revoke",
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    try:
        _save_revocation_list(payload)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to persist revocation list: {exc}")
    return {"status": "ok", "tenant_id": tenant, "removed": existed}


@app.get("/ops/pack-registry/list", tags=["ops"])
async def ops_pack_registry_list(
    pack_name: str = "",
    _auth: None = Depends(_require_ops_token),
) -> dict[str, Any]:
    """List available pack versions from registry metadata."""
    entries: list[dict[str, str]] = []
    if not PACK_REGISTRY_DIR.exists():
        return {"status": "ok", "packs": entries}
    target = pack_name.strip().lower()
    try:
        pack_dirs = [p for p in PACK_REGISTRY_DIR.iterdir() if p.is_dir()]
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read pack registry: {exc}")
    for directory in sorted(pack_dirs):
        if target and directory.name != target:
            continue
        for meta_path in sorted(directory.glob("*.json")):
            try:
                meta_raw = json.loads(meta_path.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError):
                continue
            if not isinstance(meta_raw, dict):
                continue
            version_value = str(meta_raw.get("version", meta_path.stem)).strip() or meta_path.stem
            entries.append(
                {
                    "pack_name": str(meta_raw.get("pack_name", directory.name)).strip() or directory.name,
                    "version": version_value,
                    "plan": str(meta_raw.get("plan", "")).strip(),
                    "published_at_utc": str(meta_raw.get("published_at_utc", "")).strip(),
                }
            )
    return {"status": "ok", "packs": entries}


@app.delete("/ops/pack-registry/{pack_name}/{version}", tags=["ops"])
async def ops_pack_registry_delete(
    pack_name: str,
    version: str,
    _auth: None = Depends(_require_ops_token),
) -> dict[str, Any]:
    """Delete a specific pack version (.json + .enc.b64)."""
    safe_name = pack_name.strip().lower().replace("..", "").replace("/", "-")
    safe_version = version.strip().replace("/", "-")
    if not safe_name or not safe_version:
        raise HTTPException(status_code=400, detail="pack_name and version are required")
    pack_dir = PACK_REGISTRY_DIR / safe_name
    meta_path = pack_dir / f"{safe_version}.json"
    blob_path = pack_dir / f"{safe_version}.enc.b64"
    removed_files = 0
    for file_path in (meta_path, blob_path):
        if file_path.exists():
            try:
                file_path.unlink()
                removed_files += 1
            except OSError as exc:
                raise HTTPException(status_code=500, detail=f"Failed to delete pack artifact: {exc}")
    if removed_files == 0:
        raise HTTPException(status_code=404, detail="Pack version not found")
    if pack_dir.exists():
        try:
            next(pack_dir.iterdir())
        except StopIteration:
            try:
                pack_dir.rmdir()
            except OSError:
                logger.debug("Pack directory is not empty or cannot be removed: %s", pack_dir)
    return {"status": "ok", "pack_name": safe_name, "version": safe_version, "deleted_files": removed_files}


@app.get("/ops/telemetry/recent", tags=["ops"])
async def ops_telemetry_recent(
    limit: int = 50,
    _auth: None = Depends(_require_ops_token),
) -> dict[str, Any]:
    """Return most recent metadata telemetry events."""
    bounded = max(1, min(int(limit), 500))
    log_path = TELEMETRY_DIR / "metadata_events.ndjson"
    if not log_path.exists():
        return {"status": "ok", "events": []}
    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read telemetry log: {exc}")
    events: list[dict[str, Any]] = []
    for line in lines[-bounded:]:
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except (ValueError, TypeError):
            continue
        if isinstance(raw, dict):
            events.append(raw)
    return {"status": "ok", "events": events}


# =========================================================================
# Legacy compatibility routes (used by production smoke)
# =========================================================================


@app.get("/api/dashboard/", tags=["legacy"])
async def legacy_dashboard(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Compatibility endpoint for legacy smoke checks."""
    return {
        "status": "ok",
        "user_id": user["user_id"],
        "tier": user.get("tier", "free"),
    }


@app.get("/api/settings/", tags=["legacy"])
async def legacy_settings_get(
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Compatibility wrapper for settings GET."""
    result = await get_pipeline_settings(user=user, db=db)
    return {"settings": result}


@app.put("/api/settings/", tags=["legacy"])
async def legacy_settings_put(
    request: Request,
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Compatibility wrapper for settings PUT.

    Accepts legacy payload shape. Unknown fields are ignored.
    """
    body = await request.json()
    normalized: dict[str, Any] = {}
    if isinstance(body, dict):
        if "flow_mode" in body:
            normalized["flow_mode"] = body["flow_mode"]
        if "default_protocols" in body:
            normalized["default_protocols"] = body["default_protocols"]
        if "modules" in body:
            normalized["modules"] = body["modules"]
        if "algolia_enabled" in body:
            normalized["algolia_enabled"] = body["algolia_enabled"]
        if "sandbox_backend" in body:
            normalized["sandbox_backend"] = body["sandbox_backend"]
        # Legacy smoke payload provides automation block; map to no-op safe defaults.
        if "automation" in body and "flow_mode" not in normalized:
            normalized["flow_mode"] = "hybrid"
    from gitspeak_core.db.models import PipelineSettings as PipelineSettingsModel

    settings = (
        db.query(PipelineSettingsModel)
        .filter(PipelineSettingsModel.user_id == user["user_id"])
        .first()
    )
    if not settings:
        settings = PipelineSettingsModel(user_id=user["user_id"])
        db.add(settings)

    if "flow_mode" in normalized:
        settings.flow_mode = normalized["flow_mode"]
    if "default_protocols" in normalized:
        settings.default_protocols = normalized["default_protocols"]
    if "modules" in normalized:
        settings.modules = normalized["modules"]
    if "algolia_enabled" in normalized:
        settings.algolia_enabled = normalized["algolia_enabled"]
    if "sandbox_backend" in normalized:
        settings.sandbox_backend = normalized["sandbox_backend"]

    db.commit()
    result = await get_pipeline_settings(user=user, db=db)
    return {"status": "ok", "settings": result}


@app.get("/api/pipeline/automation/status", tags=["legacy"])
async def legacy_automation_status(
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
) -> dict[str, Any]:
    """Compatibility endpoint returning schedule count."""
    schedules = await list_schedules(user=user, db=db)
    return {
        "status": "ok",
        "schedule_count": len(schedules.get("schedules", [])),
        "tier": user.get("tier", "free"),
    }


# =========================================================================
# AUDIT LOG ROUTES
# =========================================================================


@app.get("/audit-log", tags=["admin"])
async def get_audit_log(
    user: dict[str, Any] = Depends(get_current_user),
    db: Any = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
) -> dict[str, list[dict[str, Any]]]:
    """Get audit log entries for current user."""
    from gitspeak_core.db.models import AuditLog

    entries = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == user["user_id"])
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(min(limit, 200))
        .all()
    )

    return {
        "entries": [
            {
                "id": e.id,
                "action": e.action,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "details": e.details,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ]
    }


# ---------------------------------------------------------------------------
# Audit log helper
# ---------------------------------------------------------------------------


def log_audit(
    db: Any,
    user_id: str | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> None:
    """Write an audit log entry."""
    from gitspeak_core.db.models import AuditLog

    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()

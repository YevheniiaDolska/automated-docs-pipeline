"""Authentication and authorization for VeriDoc SaaS.

Provides:
- Password hashing (bcrypt via passlib)
- JWT token generation and validation
- FastAPI dependencies for route protection
- Registration and login handlers
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Password hashing (PBKDF2-SHA256, no bcrypt dependency needed)
# ---------------------------------------------------------------------------

_PBKDF2_ITERATIONS = 260_000
_SALT_LENGTH = 32


def hash_password(password: str) -> str:
    """Hash a password with PBKDF2-SHA256."""
    salt = os.urandom(_SALT_LENGTH)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return f"pbkdf2:sha256:{_PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a PBKDF2-SHA256 hash."""
    try:
        parts = hashed.split("$")
        if len(parts) != 3:
            return False
        header, salt_hex, dk_hex = parts
        salt = bytes.fromhex(salt_hex)
        dk_expected = bytes.fromhex(dk_hex)
        dk_actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
        )
        return hmac.compare_digest(dk_actual, dk_expected)
    except (ValueError, AttributeError):
        return False


# ---------------------------------------------------------------------------
# JWT token handling (using PyJWT)
# ---------------------------------------------------------------------------

# Import jwt lazily to allow running without PyJWT in test environments
_jwt = None


def _get_jwt() -> Any:
    """Lazily import and cache the `jwt` module."""
    global _jwt
    if _jwt is None:
        try:
            import jwt as _jwt_mod

            _jwt = _jwt_mod
        except ImportError:
            raise ImportError(
                "PyJWT is required for authentication. "
                "Install with: pip install PyJWT"
            )
    return _jwt


def create_access_token(
    subject: str,
    secret_key: str,
    expires_minutes: int = 60,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a JWT access token."""
    jwt = _get_jwt()
    now = datetime.now(timezone.utc)
    claims = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
        "jti": secrets.token_hex(16),
    }
    if extra_claims:
        claims.update(extra_claims)
    return jwt.encode(claims, secret_key, algorithm="HS256")


def decode_access_token(token: str, secret_key: str) -> dict[str, Any]:
    """Decode and validate a JWT access token.

    Raises jwt.InvalidTokenError on failure.
    """
    jwt = _get_jwt()
    return jwt.decode(token, secret_key, algorithms=["HS256"])


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    """User registration request."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(description="User email address", min_length=5, max_length=320)
    password: str = Field(description="Password (min 8 chars)", min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=200)


class LoginRequest(BaseModel):
    """User login request."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """JWT token response."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user_id: str
    email: str
    tier: str


class UserResponse(BaseModel):
    """Public user profile."""

    model_config = ConfigDict(extra="forbid")

    id: str
    email: str
    full_name: str | None
    tier: str
    is_active: bool
    created_at: str


# ---------------------------------------------------------------------------
# Auth handlers (called by FastAPI routes)
# ---------------------------------------------------------------------------


def handle_register(
    request: RegisterRequest,
    db_session: Any,
) -> TokenResponse:
    """Register a new user with free trial.

    Creates user + subscription (14-day trial on free tier).
    Returns JWT token.
    """
    from gitspeak_core.db.models import Subscription, User

    # Check if email already exists
    existing = db_session.query(User).filter(User.email == request.email).first()
    if existing:
        raise ValueError("Email already registered")

    # Create user
    user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
        full_name=request.full_name,
    )
    db_session.add(user)
    db_session.flush()  # get user.id

    # Create free trial subscription
    now = datetime.now(timezone.utc)
    subscription = Subscription(
        user_id=user.id,
        tier="free",
        status="trialing",
        trial_ends_at=now + timedelta(days=14),
        current_period_start=now,
        current_period_end=now + timedelta(days=14),
        ai_requests_limit=50,
    )
    db_session.add(subscription)
    db_session.commit()

    # Prepare referral identity for recurring commission attribution.
    from gitspeak_core.api.billing import ensure_referral_profile

    ensure_referral_profile(user.id, db_session)

    # Generate token
    from gitspeak_core.config.settings import get_default_settings

    settings = get_default_settings()
    secret = settings.secret_key.get_secret_value()
    expires = settings.access_token_expire_minutes

    token = create_access_token(
        subject=user.id,
        secret_key=secret,
        expires_minutes=expires,
        extra_claims={"email": user.email, "tier": "free"},
    )

    return TokenResponse(
        access_token=token,
        expires_in=expires * 60,
        user_id=user.id,
        email=user.email,
        tier="free",
    )


def handle_login(
    request: LoginRequest,
    db_session: Any,
) -> TokenResponse:
    """Authenticate user and return JWT token."""
    from gitspeak_core.db.models import User

    user = db_session.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        logger.warning("Failed login attempt for email=%s", request.email)
        raise ValueError("Invalid email or password")

    if not user.is_active:
        logger.warning("Login attempt for deactivated account: email=%s", request.email)
        raise ValueError("Account is deactivated")

    # Get subscription tier
    tier = "free"
    if user.subscription:
        tier = user.subscription.tier

    from gitspeak_core.config.settings import get_default_settings

    settings = get_default_settings()
    secret = settings.secret_key.get_secret_value()
    expires = settings.access_token_expire_minutes

    token = create_access_token(
        subject=user.id,
        secret_key=secret,
        expires_minutes=expires,
        extra_claims={"email": user.email, "tier": tier},
    )

    return TokenResponse(
        access_token=token,
        expires_in=expires * 60,
        user_id=user.id,
        email=user.email,
        tier=tier,
    )


def handle_get_profile(user_id: str, db_session: Any) -> UserResponse:
    """Get current user profile."""
    from gitspeak_core.db.models import User

    user = db_session.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")

    tier = "free"
    if user.subscription:
        tier = user.subscription.tier

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        tier=tier,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else "",
    )


# ---------------------------------------------------------------------------
# Token extraction helper (for FastAPI dependency)
# ---------------------------------------------------------------------------


def get_current_user_id(token: str, secret_key: str) -> str:
    """Extract user_id from a valid JWT token.

    Raises ValueError if token is invalid/expired.
    """
    try:
        payload = decode_access_token(token, secret_key)
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token: missing subject")
        return user_id
    except (RuntimeError, ValueError, TypeError, OSError) as exc:
        raise ValueError(f"Invalid token: {exc}") from exc

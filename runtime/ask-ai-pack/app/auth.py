"""Authentication and request guardrails for Ask AI runtime."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class AuthContext:
    user_id: str
    user_role: str
    plan: str


def require_runtime_api_key(header_value: str | None) -> None:
    """Validate runtime API key from request header."""
    expected = os.getenv("ASK_AI_API_KEY", "").strip()
    if not expected:
        raise PermissionError("ASK_AI_API_KEY is not configured")
    if header_value != expected:
        raise PermissionError("Invalid runtime API key")


def parse_auth_context(user_id: str | None, user_role: str | None, plan: str | None) -> AuthContext:
    """Build auth context from headers or query metadata."""
    return AuthContext(
        user_id=(user_id or "anonymous").strip() or "anonymous",
        user_role=(user_role or "anonymous").strip() or "anonymous",
        plan=(plan or "free").strip() or "free",
    )


def validate_role(auth: AuthContext, allowed_roles: list[str], require_auth: bool) -> None:
    """Enforce role-based access control."""
    if not require_auth:
        return

    if auth.user_id == "anonymous":
        raise PermissionError("User authentication required")

    if allowed_roles and auth.user_role not in allowed_roles:
        raise PermissionError("Role is not allowed to use Ask AI")

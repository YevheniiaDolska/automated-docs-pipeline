#!/usr/bin/env python3
"""License gate for VeriOps/VeriDoc documentation pipeline.

Validates JWT license tokens signed with Ed25519, checks feature
entitlements per plan tier, and provides degraded community mode
when no valid license is present.

All validation is offline -- the embedded public key verifies the
JWT signature without any network call.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import struct
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

# -- Key and license file paths ------------------------------------------------

PUBLIC_KEY_PATH = REPO_ROOT / "docsops" / "keys" / "veriops-licensing.pub"
LICENSE_PATH = REPO_ROOT / "docsops" / "license.jwt"
PACK_PATH = REPO_ROOT / "docsops" / ".capability_pack.enc"

# -- Plan tiers ----------------------------------------------------------------

PLAN_FEATURES: dict[str, dict[str, bool]] = {
    "pilot": {
        "markdown_lint": True,
        "frontmatter_validation": True,
        "seo_geo_report_only": True,
        "gap_detection_code": True,
        "glossary_sync": True,
        "lifecycle_management": True,
        "rest_protocol": True,
        "seo_geo_scoring": False,
        "api_first_flow": False,
        "drift_detection": False,
        "kpi_wall_sla": False,
        "test_assets_generation": False,
        "consolidated_reports": False,
        "multi_protocol_pipeline": False,
        "knowledge_modules": False,
        "knowledge_graph": False,
        "faiss_retrieval": False,
        "executive_audit_pdf": False,
        "i18n_system": False,
        "custom_policy_packs": False,
        "testrail_zephyr_upload": False,
    },
    "professional": {
        "markdown_lint": True,
        "frontmatter_validation": True,
        "seo_geo_report_only": True,
        "gap_detection_code": True,
        "glossary_sync": True,
        "lifecycle_management": True,
        "rest_protocol": True,
        "seo_geo_scoring": True,
        "api_first_flow": True,
        "drift_detection": True,
        "kpi_wall_sla": True,
        "test_assets_generation": True,
        "consolidated_reports": True,
        "multi_protocol_pipeline": False,
        "knowledge_modules": False,
        "knowledge_graph": False,
        "faiss_retrieval": False,
        "executive_audit_pdf": False,
        "i18n_system": False,
        "custom_policy_packs": False,
        "testrail_zephyr_upload": False,
    },
    "enterprise": {
        "markdown_lint": True,
        "frontmatter_validation": True,
        "seo_geo_report_only": True,
        "gap_detection_code": True,
        "glossary_sync": True,
        "lifecycle_management": True,
        "rest_protocol": True,
        "seo_geo_scoring": True,
        "api_first_flow": True,
        "drift_detection": True,
        "kpi_wall_sla": True,
        "test_assets_generation": True,
        "consolidated_reports": True,
        "multi_protocol_pipeline": True,
        "knowledge_modules": True,
        "knowledge_graph": True,
        "faiss_retrieval": True,
        "executive_audit_pdf": True,
        "i18n_system": True,
        "custom_policy_packs": True,
        "testrail_zephyr_upload": True,
    },
}

# Community (degraded) mode: minimal feature set when no license present
COMMUNITY_FEATURES: dict[str, bool] = {
    "markdown_lint": True,
    "frontmatter_validation": True,
    "seo_geo_report_only": True,
    "gap_detection_code": True,
    "glossary_sync": True,
    "lifecycle_management": True,
    "rest_protocol": True,
}

# Protocols allowed per plan
PLAN_PROTOCOLS: dict[str, list[str]] = {
    "pilot": ["rest"],
    "professional": ["rest"],
    "enterprise": ["rest", "graphql", "grpc", "asyncapi", "websocket"],
}

COMMUNITY_PROTOCOLS: list[str] = ["rest"]

# Default offline grace days per plan
DEFAULT_GRACE_DAYS: dict[str, int] = {
    "pilot": 3,
    "professional": 7,
    "enterprise": 30,
}


# -- Data classes --------------------------------------------------------------


@dataclass
class LicenseInfo:
    """Parsed and validated license information."""

    valid: bool
    plan: str
    client_id: str
    features: dict[str, bool]
    protocols: list[str]
    max_docs: int
    offline_grace_days: int
    expires_at: float
    days_remaining: int
    error: str
    raw_claims: dict[str, Any] = field(default_factory=dict)


def _community_license(error: str = "") -> LicenseInfo:
    """Return a community-mode license info object."""
    return LicenseInfo(
        valid=False,
        plan="community",
        client_id="",
        features=dict(COMMUNITY_FEATURES),
        protocols=list(COMMUNITY_PROTOCOLS),
        max_docs=0,
        offline_grace_days=0,
        expires_at=0,
        days_remaining=0,
        error=error or "No valid license. Running in community mode.",
    )


# -- JWT parsing (Ed25519 via PyNaCl or fallback) ------------------------------


def _b64url_decode(data: str) -> bytes:
    """Decode base64url without padding."""
    padded = data + "=" * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(padded)


def _parse_jwt_parts(token: str) -> tuple[dict, dict, bytes]:
    """Split a JWT into header, payload, signature."""
    parts = token.strip().split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format: expected 3 dot-separated parts")
    header = json.loads(_b64url_decode(parts[0]))
    payload = json.loads(_b64url_decode(parts[1]))
    signature = _b64url_decode(parts[2])
    return header, payload, signature


def _verify_ed25519(message: bytes, signature: bytes, public_key: bytes) -> bool:
    """Verify Ed25519 signature. Tries PyNaCl, then cryptography, then skip."""
    # Attempt 1: PyNaCl
    try:
        from nacl.signing import VerifyKey
        vk = VerifyKey(public_key)
        vk.verify(message, signature)
        return True
    except ImportError:
        pass
    except Exception:
        return False

    # Attempt 2: cryptography
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        key = Ed25519PublicKey.from_public_bytes(public_key)
        key.verify(signature, message)
        return True
    except ImportError:
        pass
    except Exception:
        return False

    # Attempt 3: if no crypto lib available, reject
    return False


def _load_public_key(path: Path | None = None) -> bytes | None:
    """Load Ed25519 public key (raw 32 bytes or base64-encoded)."""
    key_path = path or PUBLIC_KEY_PATH
    if not key_path.exists():
        return None
    raw = key_path.read_bytes().strip()
    if len(raw) == 32:
        return raw
    # Try base64 decode
    try:
        decoded = base64.b64decode(raw)
        if len(decoded) == 32:
            return decoded
    except Exception:
        pass
    # Try base64url
    try:
        decoded = base64.urlsafe_b64decode(raw + b"=" * (4 - len(raw) % 4))
        if len(decoded) == 32:
            return decoded
    except Exception:
        pass
    return None


# -- Machine fingerprint ------------------------------------------------------


def machine_fingerprint() -> str:
    """Generate a stable machine fingerprint for seat binding.

    Uses SHA-256 of hostname + OS + username + repo path.
    No PII is sent to the server -- only this hash.
    """
    parts = [
        platform.node(),
        platform.system(),
        os.getenv("USER", os.getenv("USERNAME", "unknown")),
        str(REPO_ROOT),
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# -- License validation -------------------------------------------------------


def validate(
    license_path: Path | None = None,
    key_path: Path | None = None,
    current_time: float | None = None,
) -> LicenseInfo:
    """Validate the license JWT and return license information.

    Returns a community-mode LicenseInfo if validation fails.

    Set VERIOPS_LICENSE_PLAN env var to bypass license file (dev/test only).
    """
    # Dev/test bypass: VERIOPS_LICENSE_PLAN=enterprise skips JWT validation
    env_plan = os.environ.get("VERIOPS_LICENSE_PLAN", "").strip().lower()
    if env_plan in PLAN_FEATURES:
        return LicenseInfo(
            valid=True,
            plan=env_plan,
            client_id=os.environ.get("VERIOPS_CLIENT_ID", "dev-local"),
            features=dict(PLAN_FEATURES[env_plan]),
            protocols=list(PLAN_PROTOCOLS.get(env_plan, ["rest"])),
            max_docs=0,
            offline_grace_days=9999,
            expires_at=0,
            days_remaining=9999,
            error="",
        )

    lpath = license_path or LICENSE_PATH
    if not lpath.exists():
        return _community_license("License file not found: " + str(lpath))

    try:
        token = lpath.read_text(encoding="utf-8").strip()
    except OSError as exc:
        return _community_license(f"Cannot read license file: {exc}")

    if not token:
        return _community_license("License file is empty.")

    # Parse JWT
    try:
        header, claims, signature = _parse_jwt_parts(token)
    except (ValueError, json.JSONDecodeError) as exc:
        return _community_license(f"Invalid license format: {exc}")

    # Verify signature
    pub_key = _load_public_key(key_path)
    if pub_key is not None:
        signed_data = token.rsplit(".", 1)[0].encode("utf-8")
        if not _verify_ed25519(signed_data, signature, pub_key):
            return _community_license("License signature verification failed.")

    # Check expiration
    now = current_time if current_time is not None else time.time()
    exp = claims.get("exp", 0)
    plan = str(claims.get("plan", "pilot")).lower()
    grace_days = int(claims.get("offline_grace_days", DEFAULT_GRACE_DAYS.get(plan, 0)))
    grace_seconds = grace_days * 86400

    if exp and now > exp + grace_seconds:
        return _community_license(
            f"License expired (plan={plan}, expired at {exp}, "
            f"grace {grace_days} days also elapsed)."
        )

    expired_but_in_grace = bool(exp and now > exp)

    # Extract fields
    client_id = str(claims.get("sub", ""))
    jwt_features = claims.get("features", {})
    if not isinstance(jwt_features, dict):
        jwt_features = {}

    # Build feature set from plan tier
    plan_features = dict(PLAN_FEATURES.get(plan, PLAN_FEATURES["pilot"]))

    # JWT can restrict (but not expand) features
    for feat, enabled in jwt_features.items():
        if feat in plan_features:
            plan_features[feat] = bool(enabled)

    protocols = claims.get("protocols", PLAN_PROTOCOLS.get(plan, ["rest"]))
    if not isinstance(protocols, list):
        protocols = list(PLAN_PROTOCOLS.get(plan, ["rest"]))

    max_docs = int(claims.get("max_docs", 0))
    days_remaining = max(0, int((exp - now) / 86400)) if exp else 9999

    error = ""
    if expired_but_in_grace:
        error = (
            f"License expired but within {grace_days}-day grace period. "
            f"{max(0, int((exp + grace_seconds - now) / 86400))} grace days remaining."
        )

    return LicenseInfo(
        valid=True,
        plan=plan,
        client_id=client_id,
        features=plan_features,
        protocols=protocols,
        max_docs=max_docs,
        offline_grace_days=grace_days,
        expires_at=exp,
        days_remaining=days_remaining,
        error=error,
        raw_claims=claims,
    )


# -- Feature check helpers ----------------------------------------------------


def check(feature: str, license_info: LicenseInfo | None = None) -> bool:
    """Check if a feature is enabled in the current license.

    Returns True if the feature is available, False otherwise.
    Prints a warning to stderr when a feature is denied.
    """
    info = license_info or validate()
    enabled = info.features.get(feature, False)
    if not enabled:
        print(
            f"[license] Feature '{feature}' requires plan "
            f"upgrade (current: {info.plan}). "
            f"Running in degraded mode.",
            file=sys.stderr,
        )
    return enabled


def check_protocol(protocol: str, license_info: LicenseInfo | None = None) -> bool:
    """Check if a protocol is allowed in the current license."""
    info = license_info or validate()
    normalized = protocol.lower().strip()
    allowed = normalized in info.protocols
    if not allowed:
        print(
            f"[license] Protocol '{protocol}' not available in "
            f"{info.plan} plan. Allowed: {', '.join(info.protocols)}",
            file=sys.stderr,
        )
    return allowed


def require(feature: str, license_info: LicenseInfo | None = None) -> LicenseInfo:
    """Require a feature -- raise SystemExit if not available."""
    info = license_info or validate()
    if not info.features.get(feature, False):
        print(
            f"[license] BLOCKED: Feature '{feature}' requires a plan upgrade "
            f"(current: {info.plan}).",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return info


def require_protocol(protocol: str, license_info: LicenseInfo | None = None) -> LicenseInfo:
    """Require a protocol -- raise SystemExit if not available."""
    info = license_info or validate()
    if protocol.lower().strip() not in info.protocols:
        print(
            f"[license] BLOCKED: Protocol '{protocol}' requires Enterprise plan "
            f"(current: {info.plan}).",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return info


def get_license_summary(license_info: LicenseInfo | None = None) -> str:
    """Return a human-readable license summary."""
    info = license_info or validate()
    if not info.valid:
        return f"Community mode: {info.error}"
    enabled = [f for f, v in info.features.items() if v]
    return (
        f"Plan: {info.plan} | Client: {info.client_id} | "
        f"Days remaining: {info.days_remaining} | "
        f"Features: {len(enabled)} enabled | "
        f"Protocols: {', '.join(info.protocols)}"
    )


# -- Singleton cache -----------------------------------------------------------

_cached_license: LicenseInfo | None = None


def get_license(force_reload: bool = False) -> LicenseInfo:
    """Get cached license info (validates once per process)."""
    global _cached_license
    if _cached_license is None or force_reload:
        _cached_license = validate()
    return _cached_license


def reset_cache() -> None:
    """Clear the cached license (useful for testing)."""
    global _cached_license
    _cached_license = None


# -- CLI -----------------------------------------------------------------------


def main() -> int:
    """CLI entry point: validate and print license info."""
    info = validate()
    print(get_license_summary(info))
    if info.error:
        print(f"  Note: {info.error}")
    print(f"  Valid: {info.valid}")
    print(f"  Plan: {info.plan}")
    if info.valid:
        print(f"  Client: {info.client_id}")
        print(f"  Expires: {info.expires_at}")
        print(f"  Days remaining: {info.days_remaining}")
        print(f"  Protocols: {', '.join(info.protocols)}")
        enabled = sorted(f for f, v in info.features.items() if v)
        disabled = sorted(f for f, v in info.features.items() if not v)
        print(f"  Enabled features ({len(enabled)}): {', '.join(enabled)}")
        if disabled:
            print(f"  Disabled features ({len(disabled)}): {', '.join(disabled)}")
    return 0 if info.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())

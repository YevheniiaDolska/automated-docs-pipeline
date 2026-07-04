#!/usr/bin/env python3
"""License gate for VeriOps/VeriDoc documentation pipeline.

Validates JWT license tokens signed with Ed25519, checks feature
entitlements per plan tier, and provides degraded community mode
when no valid license is present.

Primary validation is offline -- the embedded public key verifies the
JWT signature without any network call.  A periodic phone-home check
(default every 30 days) contacts the VeriDoc SaaS server to verify
subscription status and download a fresh JWT.
"""

from __future__ import annotations

import base64
import argparse
import hashlib
import json
import logging
import os
import platform
import struct
import sys
import time
import urllib.error
import urllib.request
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

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
        "vale_lint": True,
        "cspell_lint": True,
        "spectral_lint": True,
        "seo_geo_report_only": True,
        "gap_detection_code": True,
        "glossary_sync": True,
        "lifecycle_management": True,
        "rest_protocol": True,
        "advanced_prompts": True,
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
        "doc_compiler": False,
    },
    "professional": {
        "markdown_lint": True,
        "frontmatter_validation": True,
        "vale_lint": True,
        "cspell_lint": True,
        "spectral_lint": True,
        "seo_geo_report_only": True,
        "gap_detection_code": True,
        "glossary_sync": True,
        "lifecycle_management": True,
        "rest_protocol": True,
        "advanced_prompts": True,
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
        "doc_compiler": False,
    },
    "enterprise": {
        "markdown_lint": True,
        "frontmatter_validation": True,
        "vale_lint": True,
        "cspell_lint": True,
        "spectral_lint": True,
        "seo_geo_report_only": True,
        "gap_detection_code": True,
        "glossary_sync": True,
        "lifecycle_management": True,
        "rest_protocol": True,
        "advanced_prompts": True,
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
        "doc_compiler": True,
    },
}

# Community (degraded) mode: minimal feature set when no license present
COMMUNITY_FEATURES: dict[str, bool] = {
    "markdown_lint": True,
    "frontmatter_validation": True,
    "vale_lint": True,
    "cspell_lint": True,
    "spectral_lint": True,
    "seo_geo_report_only": True,
    "gap_detection_code": False,
    "glossary_sync": False,
    "lifecycle_management": False,
    "rest_protocol": False,
    "advanced_prompts": False,
}

# Protocols allowed per plan
PLAN_PROTOCOLS: dict[str, list[str]] = {
    "pilot": ["rest"],
    "professional": ["rest"],
    "enterprise": ["rest", "graphql", "grpc", "asyncapi", "websocket"],
}

COMMUNITY_PROTOCOLS: list[str] = []

# Default offline grace days per plan
DEFAULT_GRACE_DAYS: dict[str, int] = {
    "pilot": 3,
    "professional": 7,
    "enterprise": 30,
}

# -- Phone-home configuration -------------------------------------------------

PHONE_HOME_URL = os.environ.get(
    "VERIOPS_PHONE_HOME_URL", "https://api.veridoc.dev"
).rstrip("/")

PHONE_HOME_INTERVAL_DAYS = int(
    os.environ.get("VERIOPS_PHONE_HOME_INTERVAL_DAYS", "30")
)

PHONE_HOME_ENABLED = os.environ.get(
    "VERIOPS_PHONE_HOME_ENABLED", "true"
).strip().lower() in ("true", "1", "yes")

PHONE_HOME_TIMEOUT_SECONDS = int(
    os.environ.get("VERIOPS_PHONE_HOME_TIMEOUT", "15")
)

HEARTBEAT_PATH = REPO_ROOT / "docsops" / ".license_heartbeat.json"
REPORTS_DIR = REPO_ROOT / "reports"
VERSION_FILE = REPO_ROOT / "docsops" / ".version.json"
REPO_BINDING_PATH = REPO_ROOT / "docsops" / ".repo_binding.json"
INTEGRITY_MANIFEST_PATH = REPO_ROOT / "docsops" / ".integrity_manifest.json"
REVOCATION_CHECK_ENABLED = os.environ.get(
    "VERIOPS_REVOCATION_CHECK_ENABLED", "false"
).strip().lower() in ("true", "1", "yes")
REVOCATION_URL = os.environ.get(
    "VERIOPS_REVOCATION_URL", f"{PHONE_HOME_URL}/billing/license/revocation-check"
).rstrip("/")


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
    tenant_id: str = ""
    company_domain: str = ""
    raw_claims: dict[str, Any] = field(default_factory=dict)
    # Permanently free grants from the signed JWT `free_features` /
    # `free_protocols` claims. These survive expiry and community degradation.
    free_features: list[str] = field(default_factory=list)
    free_protocols: list[str] = field(default_factory=list)


def _community_license(
    error: str = "",
    free_features: list[str] | None = None,
    free_protocols: list[str] | None = None,
    client_id: str = "",
) -> LicenseInfo:
    """Return a community-mode license info object.

    Permanently free grants (from a signed license) survive community
    degradation: features listed in the JWT `free_features` claim remain
    enabled forever, regardless of payment status.
    """
    features = dict(COMMUNITY_FEATURES)
    protocols = list(COMMUNITY_PROTOCOLS)
    for feat in free_features or []:
        features[str(feat)] = True
    for proto in free_protocols or []:
        normalized = str(proto).strip().lower()
        if normalized and normalized not in protocols:
            protocols.append(normalized)
    return LicenseInfo(
        valid=False,
        plan="community",
        client_id=client_id,
        features=features,
        protocols=protocols,
        max_docs=0,
        offline_grace_days=0,
        expires_at=0,
        days_remaining=0,
        error=error or "No valid license. Running in community mode.",
        tenant_id="",
        company_domain="",
        free_features=sorted({str(f) for f in (free_features or [])}),
        free_protocols=sorted({str(p).strip().lower() for p in (free_protocols or []) if str(p).strip()}),
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
        from nacl.exceptions import CryptoError
        from nacl.signing import VerifyKey
    except ImportError:
        logger.debug("PyNaCl is not installed; trying cryptography fallback")
    else:
        try:
            vk = VerifyKey(public_key)
            vk.verify(message, signature)
            return True
        except (CryptoError, RuntimeError, ValueError, TypeError, OSError) as exc:
            # CryptoError covers BadSignatureError: a bad signature must
            # degrade to community mode, never crash validation.
            logger.debug("Ed25519 verification failed (PyNaCl): %s", exc)
            return False

    # Attempt 2: cryptography
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError:
        logger.debug("cryptography is not installed; Ed25519 verification unavailable")
    else:
        try:
            key = Ed25519PublicKey.from_public_bytes(public_key)
            key.verify(signature, message)
            return True
        except (InvalidSignature, RuntimeError, ValueError, TypeError, OSError) as exc:
            logger.debug("Ed25519 verification failed (cryptography): %s", exc)
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
    except (RuntimeError, ValueError, TypeError, OSError) as exc:
        logger.debug("base64 standard decode failed for %s: %s", key_path, exc)
    # Try base64url
    try:
        decoded = base64.urlsafe_b64decode(raw + b"=" * (4 - len(raw) % 4))
        if len(decoded) == 32:
            return decoded
    except (RuntimeError, ValueError, TypeError, OSError) as exc:
        logger.debug("base64url decode failed for %s: %s", key_path, exc)
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


def _current_bundle_version() -> str:
    if not VERSION_FILE.exists():
        return "0.0.0"
    try:
        payload = json.loads(VERSION_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return "0.0.0"
    if isinstance(payload, dict):
        value = str(payload.get("version", "0.0.0")).strip()
        return value or "0.0.0"
    return "0.0.0"


def _repo_path_hash(repo_root: Path) -> str:
    """Stable hash of canonical repository path used for local binding."""
    canonical = str(repo_root.resolve())
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _load_repo_binding(path: Path | None = None) -> dict[str, Any]:
    # Resolve the module constant at call time so tests can monkeypatch it.
    binding_path = path if path is not None else REPO_BINDING_PATH
    if not binding_path.exists():
        return {}
    try:
        payload = json.loads(binding_path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def _save_repo_binding(payload: dict[str, Any], path: Path = REPO_BINDING_PATH) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    except OSError as exc:
        logger.debug("Cannot write repo binding file %s: %s", path, exc)


def _load_integrity_manifest(path: Path | None = None) -> dict[str, Any]:
    # Resolve the module constant at call time so tests can monkeypatch it.
    manifest_path = path if path is not None else INTEGRITY_MANIFEST_PATH
    if not manifest_path.exists():
        return {}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _enforce_integrity_manifest(claims_obj: dict[str, Any]) -> str:
    """Validate hash manifest for protected files.

    If manifest is missing or any protected file hash mismatches, degrade.
    """
    plan = str(claims_obj.get("plan", "pilot")).strip().lower()
    # Community mode has no paid integrity enforcement.
    if plan == "community":
        return ""

    manifest = _load_integrity_manifest()
    if not manifest:
        return "Integrity manifest missing. Reinstall/provisioning is required."

    files = manifest.get("files", {})
    if not isinstance(files, dict) or not files:
        return "Integrity manifest is invalid or empty."

    root_hash = str(manifest.get("repo_path_hash", "")).strip()
    expected_hash = _repo_path_hash(REPO_ROOT)
    if root_hash and root_hash != expected_hash:
        return "Integrity manifest repository binding mismatch."

    for rel, expected in files.items():
        rel_path = str(rel).strip()
        expected_hex = str(expected).strip().lower()
        if not rel_path or not expected_hex:
            return "Integrity manifest has malformed entries."
        target = REPO_ROOT / rel_path
        if not target.exists() or not target.is_file():
            return f"Integrity check failed: missing protected file '{rel_path}'."
        try:
            actual = _sha256_file(target).lower()
        except OSError:
            return f"Integrity check failed: cannot read protected file '{rel_path}'."
        if actual != expected_hex:
            return f"Integrity check failed: protected file changed '{rel_path}'."

    return ""


def _enforce_repo_binding(claims_obj: dict[str, Any], *, client_id: str) -> str:
    """Enforce local repository binding for paid/pilot bundles.

    - Binding file is expected to be created during install/provisioning.
    - If missing, validation degrades to community to prevent bundle cloning.
    - If path hash mismatches current repo, validation degrades to community.
    """
    binding = _load_repo_binding()
    expected_hash = _repo_path_hash(REPO_ROOT)
    expected_tenant = str(claims_obj.get("tenant_id", "")).strip()
    expected_sub = str(claims_obj.get("sub", client_id)).strip()

    if not binding:
        return (
            "Repository binding file missing. This bundle is locked to its original "
            "repository path and requires reinstall/provisioning."
        )

    bound_hash = str(binding.get("repo_path_hash", "")).strip()
    if not bound_hash or bound_hash != expected_hash:
        return "Repository binding mismatch: bundle moved to another repository path."

    bound_sub = str(binding.get("client_id", "")).strip()
    if bound_sub and expected_sub and bound_sub != expected_sub:
        return "Repository binding mismatch: client_id differs from license subject."

    bound_tenant = str(binding.get("tenant_id", "")).strip()
    if bound_tenant and expected_tenant and bound_tenant != expected_tenant:
        return "Repository binding mismatch: tenant_id differs from license."

    return ""


def _metadata_payload(
    *,
    client_id: str,
    plan: str = "",
    event: str,
    now: float,
) -> dict[str, Any]:
    return {
        "tenant_id": str(os.environ.get("VERIOPS_TENANT_ID", client_id)).strip(),
        "build_id": str(os.environ.get("VERIOPS_BUILD_ID", "")).strip(),
        "version": _current_bundle_version(),
        "platform": f"{platform.system().lower()}-{platform.machine().lower()}",
        "plan": plan.strip().lower(),
        "event": event,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
    }


def _enforce_metadata_allowlist(payload: dict[str, Any], *, step: str) -> dict[str, Any]:
    sanitized = {k: v for k, v in payload.items() if str(v).strip()}
    try:
        from scripts.llm_egress import enforce_metadata_egress_payload

        return enforce_metadata_egress_payload(
            payload=sanitized,
            reports_dir=REPORTS_DIR,
            step=step,
            source="license_gate.py",
        )
    except ImportError:
        return sanitized


# -- Phone-home (periodic license refresh) ------------------------------------


def _read_heartbeat(path: Path | None = None) -> dict[str, Any]:
    """Read the heartbeat state file. Returns empty dict on any error."""
    hb_path = path or HEARTBEAT_PATH
    if not hb_path.exists():
        return {}
    try:
        return json.loads(hb_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def _write_heartbeat(
    data: dict[str, Any],
    path: Path | None = None,
) -> None:
    """Write the heartbeat state file."""
    hb_path = path or HEARTBEAT_PATH
    try:
        hb_path.parent.mkdir(parents=True, exist_ok=True)
        hb_path.write_text(
            json.dumps(data, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.debug("Cannot write heartbeat file %s: %s", hb_path, exc)


def _phone_home_due(
    heartbeat: dict[str, Any],
    interval_days: int | None = None,
    current_time: float | None = None,
) -> bool:
    """Check whether a phone-home check is due based on last_check timestamp."""
    interval = interval_days if interval_days is not None else PHONE_HOME_INTERVAL_DAYS
    now = current_time if current_time is not None else time.time()
    last_check = heartbeat.get("last_check", 0)
    if not isinstance(last_check, (int, float)):
        return True
    return (now - last_check) >= interval * 86400


def phone_home(
    client_id: str,
    license_path: Path | None = None,
    heartbeat_path: Path | None = None,
    base_url: str | None = None,
    timeout: int | None = None,
    current_time: float | None = None,
    interval_days: int | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Contact the VeriDoc server to refresh the local license JWT.

    Returns a dict with keys:
        refreshed (bool): True if a new JWT was downloaded and saved.
        skipped (bool): True if phone-home was not due yet.
        error (str|None): Error message if refresh failed.
    """
    result: dict[str, Any] = {
        "refreshed": False,
        "skipped": False,
        "error": None,
    }

    if not PHONE_HOME_ENABLED and not force:
        result["skipped"] = True
        result["error"] = "Phone-home disabled via VERIOPS_PHONE_HOME_ENABLED"
        return result

    if not client_id:
        result["skipped"] = True
        result["error"] = "No client_id -- community mode, skipping phone-home"
        return result

    hb_path = heartbeat_path or HEARTBEAT_PATH
    heartbeat = _read_heartbeat(hb_path)

    if not force and not _phone_home_due(heartbeat, interval_days, current_time):
        result["skipped"] = True
        return result

    url = (base_url or PHONE_HOME_URL) + "/billing/license/token"
    t_out = timeout if timeout is not None else PHONE_HOME_TIMEOUT_SECONDS
    now = current_time if current_time is not None else time.time()

    fingerprint = machine_fingerprint()
    try:
        metadata = _enforce_metadata_allowlist(
            _metadata_payload(client_id=client_id, event="license_refresh", now=now),
            step="license_phone_home",
        )
    except ValueError as exc:
        result["error"] = f"Egress allowlist blocked license refresh payload: {exc}"
        return result
    headers = {
        "X-Client-Id": client_id,
        "X-Machine-Fingerprint": fingerprint,
        "X-Tenant-Id": str(metadata.get("tenant_id", "")),
        "X-Build-Id": str(metadata.get("build_id", "")),
        "X-Client-Version": str(metadata.get("version", "0.0.0")),
        "X-Client-Platform": str(metadata.get("platform", "")),
        "Accept": "application/json",
        "User-Agent": "VeriOps-LicenseGate/1.0",
    }

    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=t_out) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        token = body.get("token", "")
        if not token:
            result["error"] = "Server returned empty token"
            _write_heartbeat(
                {"last_check": now, "last_result": "error_empty_token"},
                hb_path,
            )
            return result

        # Validate the new token parses correctly before saving
        try:
            _parse_jwt_parts(token)
        except (ValueError, json.JSONDecodeError) as exc:
            result["error"] = f"Server returned invalid JWT: {exc}"
            _write_heartbeat(
                {"last_check": now, "last_result": "error_invalid_jwt"},
                hb_path,
            )
            return result

        # Write new license JWT
        lpath = license_path or LICENSE_PATH
        lpath.parent.mkdir(parents=True, exist_ok=True)
        lpath.write_text(token, encoding="utf-8")

        _write_heartbeat(
            {"last_check": now, "last_result": "success"},
            hb_path,
        )
        result["refreshed"] = True
        logger.info("License refreshed via phone-home for client %s", client_id)

    except urllib.error.HTTPError as exc:
        status = exc.code
        result["error"] = f"Server returned HTTP {status}"
        _write_heartbeat(
            {"last_check": now, "last_result": f"error_http_{status}"},
            hb_path,
        )
        logger.warning("Phone-home failed: HTTP %d", status)

    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        result["error"] = f"Network error: {exc}"
        logger.warning("Phone-home network error: %s", exc)
        # Do NOT update last_check on network failure so we retry next time

    except (json.JSONDecodeError, ValueError) as exc:
        result["error"] = f"Invalid server response: {exc}"
        _write_heartbeat(
            {"last_check": now, "last_result": "error_bad_response"},
            hb_path,
        )

    return result


def check_revocation(
    *,
    client_id: str,
    plan: str,
    current_time: float | None = None,
) -> tuple[bool, str]:
    """Check revocation list endpoint using metadata-only payload."""
    if not REVOCATION_CHECK_ENABLED or not client_id:
        return False, ""
    now = current_time if current_time is not None else time.time()
    try:
        payload = _enforce_metadata_allowlist(
            _metadata_payload(
                client_id=client_id,
                plan=plan,
                event="revocation_check",
                now=now,
            ),
            step="license_revocation_check",
        )
    except ValueError as exc:
        logger.warning("Revocation check blocked by egress allowlist: %s", exc)
        return False, ""
    params = urllib.parse.urlencode({k: str(v) for k, v in payload.items()})
    url = f"{REVOCATION_URL}?{params}"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
        with urllib.request.urlopen(req, timeout=PHONE_HOME_TIMEOUT_SECONDS) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        if isinstance(body, dict) and bool(body.get("revoked", False)):
            reason = str(body.get("reason", "revoked_by_server")).strip()
            return True, reason
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        logger.debug("Revocation check unavailable: %s", exc)
    return False, ""


# -- Phone-home recursion guard -----------------------------------------------
_phone_home_refreshing: bool = False


# -- Permanent free grants and environment helpers ------------------------------


def _is_vendor_repo() -> bool:
    """True when running inside the VeriOps master/vendor repository.

    The build/ tooling (license generator) is never distributed to clients,
    so its presence marks the vendor development environment.
    """
    return (REPO_ROOT / "build" / "generate_license.py").exists()


def _dev_bypass_allowed() -> bool:
    """Whether the VERIOPS_LICENSE_PLAN env bypass is honored.

    Allowed only in the vendor repo (dev/test) or when the bundle was
    explicitly built as a free/dev bundle (docsops/.dev_mode marker).
    Prevents paying clients from self-upgrading via an env variable.
    """
    if _is_vendor_repo():
        return True
    return (REPO_ROOT / "docsops" / ".dev_mode").exists()


def _extract_free_grants(claims_obj: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Extract permanently free feature/protocol grants from JWT claims."""
    raw_features = claims_obj.get("free_features", [])
    raw_protocols = claims_obj.get("free_protocols", [])
    features = [str(f).strip() for f in raw_features if str(f).strip()] if isinstance(raw_features, list) else []
    protocols = [str(p).strip().lower() for p in raw_protocols if str(p).strip()] if isinstance(raw_protocols, list) else []
    return features, protocols


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
    global _phone_home_refreshing

    # Dev/test bypass: VERIOPS_LICENSE_PLAN=enterprise skips JWT validation.
    # Honored only in the vendor repo or dev-mode bundles (see _dev_bypass_allowed).
    env_plan = os.environ.get("VERIOPS_LICENSE_PLAN", "").strip().lower()
    if env_plan in PLAN_FEATURES and not _dev_bypass_allowed():
        logger.warning(
            "VERIOPS_LICENSE_PLAN=%s ignored: env bypass is not permitted in "
            "licensed client bundles.",
            env_plan,
        )
        env_plan = ""
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

    def _normalize_domain(value: str) -> str:
        raw = value.strip().lower()
        if raw.startswith("http://"):
            raw = raw[len("http://") :]
        if raw.startswith("https://"):
            raw = raw[len("https://") :]
        raw = raw.split("/", 1)[0]
        if raw.startswith("www."):
            raw = raw[4:]
        return raw

    def _enforce_binding(claims_obj: dict[str, Any]) -> str:
        claim_tenant = str(claims_obj.get("tenant_id", "")).strip()
        claim_domain = _normalize_domain(str(claims_obj.get("company_domain", "")))
        expected_tenant = str(os.environ.get("VERIOPS_TENANT_ID", "")).strip()
        expected_domain = _normalize_domain(str(os.environ.get("VERIOPS_COMPANY_DOMAIN", "")))

        if claim_tenant and expected_tenant and claim_tenant != expected_tenant:
            return (
                "Tenant binding mismatch: "
                f"license tenant_id={claim_tenant}, env VERIOPS_TENANT_ID={expected_tenant}"
            )
        if claim_domain and expected_domain and claim_domain != expected_domain:
            return (
                "Domain binding mismatch: "
                f"license company_domain={claim_domain}, env VERIOPS_COMPANY_DOMAIN={expected_domain}"
            )
        return ""

    # Signature is verified at this point: permanent free grants in the claims
    # are trusted from here on. Anti-cloning binding failures still drop the
    # grants (a moved/cloned bundle is not the licensed installation).
    free_features, free_protocols = _extract_free_grants(claims)

    binding_error = _enforce_binding(claims)
    if binding_error:
        return _community_license(binding_error)

    repo_binding_error = _enforce_repo_binding(claims, client_id=str(claims.get("sub", "")))
    if repo_binding_error:
        return _community_license(repo_binding_error)
    integrity_error = _enforce_integrity_manifest(claims)
    if integrity_error:
        return _community_license(integrity_error)

    # Check expiration
    now = current_time if current_time is not None else time.time()
    exp = claims.get("exp", 0)
    plan = str(claims.get("plan", "pilot")).lower()
    grace_days = int(claims.get("offline_grace_days", DEFAULT_GRACE_DAYS.get(plan, 0)))
    grace_seconds = grace_days * 86400

    if exp and now > exp + grace_seconds:
        # Payment lapsed: degrade to community but keep permanently free grants.
        return _community_license(
            f"License expired (plan={plan}, expired at {exp}, "
            f"grace {grace_days} days also elapsed).",
            free_features=free_features,
            free_protocols=free_protocols,
            client_id=str(claims.get("sub", "")),
        )

    expired_but_in_grace = bool(exp and now > exp)

    # Extract fields
    client_id = str(claims.get("sub", ""))
    tenant_id = str(claims.get("tenant_id", "")).strip()
    company_domain = _normalize_domain(str(claims.get("company_domain", "")))
    jwt_features = claims.get("features", {})
    if not isinstance(jwt_features, dict):
        jwt_features = {}

    # Build feature set from plan tier
    plan_features = dict(PLAN_FEATURES.get(plan, PLAN_FEATURES["pilot"]))

    # JWT can restrict (but not expand) features
    for feat, enabled in jwt_features.items():
        if feat in plan_features:
            plan_features[feat] = bool(enabled)

    # Permanently free grants always win: they stay enabled regardless of
    # plan restrictions or later payment status.
    for feat in free_features:
        plan_features[feat] = True

    protocols = claims.get("protocols", PLAN_PROTOCOLS.get(plan, ["rest"]))
    if not isinstance(protocols, list):
        protocols = list(PLAN_PROTOCOLS.get(plan, ["rest"]))
    for proto in free_protocols:
        if proto not in protocols:
            protocols.append(proto)

    max_docs = int(claims.get("max_docs", 0))
    days_remaining = max(0, int((exp - now) / 86400)) if exp else 9999

    error = ""
    if expired_but_in_grace:
        error = (
            f"License expired but within {grace_days}-day grace period. "
            f"{max(0, int((exp + grace_seconds - now) / 86400))} grace days remaining."
        )

    # Phone-home: periodically contact the server to refresh the JWT.
    # Runs after offline validation so we have client_id and plan.
    # On success, re-validates with the fresh token.
    if (
        client_id
        and PHONE_HOME_ENABLED
        and not env_plan
        and not _phone_home_refreshing
    ):
        ph_result = phone_home(
            client_id=client_id,
            license_path=lpath,
            current_time=current_time,
        )
        if ph_result.get("refreshed"):
            # Re-validate with the fresh token (guard against recursion)
            _phone_home_refreshing = True
            try:
                return validate(
                    license_path=lpath,
                    key_path=key_path,
                    current_time=current_time,
                )
            finally:
                _phone_home_refreshing = False
    revoked, revoke_reason = check_revocation(
        client_id=client_id,
        plan=plan,
        current_time=current_time,
    )
    if revoked:
        # Revocation removes paid entitlements but keeps permanently free grants.
        return _community_license(
            f"License revoked by server policy: {revoke_reason}",
            free_features=free_features,
            free_protocols=free_protocols,
            client_id=client_id,
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
        tenant_id=tenant_id,
        company_domain=company_domain,
        raw_claims=claims,
        free_features=sorted(set(free_features)),
        free_protocols=sorted(set(free_protocols)),
    )


# -- Feature check helpers ----------------------------------------------------


def _pilot_trial_expired(info: LicenseInfo) -> bool:
    """Return True when pilot trial period has ended (grace does not keep premium access)."""
    return bool(
        info.plan == "pilot"
        and info.expires_at
        and info.days_remaining <= 0
    )


def _remove_paid_llm_instruction_files() -> None:
    """Remove paid LLM instruction files after pilot expiry."""
    candidates = [
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "CLAUDE.md",
        REPO_ROOT / "docsops" / "AGENTS.md",
        REPO_ROOT / "docsops" / "CLAUDE.md",
    ]
    for path in candidates:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            logger.debug("Cannot remove paid instruction file: %s", path)


def _remove_proprietary_assets_after_expiry() -> None:
    """Remove proprietary paid scripts/assets after pilot expiry.

    Keeps only baseline community assets (free lint stack, templates, glossary,
    shared vars, and core license/runtime skeleton).
    """
    # Keep these script basenames available in degraded community mode.
    keep_script_basenames = {
        "license_gate.py",
        "normalize_docs.py",
        "validate_frontmatter.py",
        "seo_geo_optimizer.py",
    }

    # Remove premium instruction packs and runtime add-ons.
    hard_remove_paths = [
        REPO_ROOT / "LOCAL_MODEL.md",
        REPO_ROOT / "docsops" / "LOCAL_MODEL.md",
        REPO_ROOT / "docsops" / "runtime" / "ask-ai-pack",
        REPO_ROOT / "runtime" / "ask-ai-pack",
        REPO_ROOT / "instructions" / "llm_plans" / "pilot",
        REPO_ROOT / "instructions" / "llm_plans" / "basic",
        REPO_ROOT / "instructions" / "llm_plans" / "pro",
        REPO_ROOT / "instructions" / "llm_plans" / "enterprise",
    ]

    # Remove script files except keep-list in both possible roots.
    script_roots = [
        REPO_ROOT / "scripts",
        REPO_ROOT / "docsops" / "scripts",
    ]

    for root in script_roots:
        if not root.exists() or not root.is_dir():
            continue
        for path in root.glob("*.py"):
            if path.name in keep_script_basenames:
                continue
            try:
                path.unlink()
            except OSError:
                logger.debug("Cannot remove proprietary script: %s", path)

    for path in hard_remove_paths:
        try:
            if path.is_dir():
                import shutil

                shutil.rmtree(path, ignore_errors=True)
            elif path.exists():
                path.unlink()
        except OSError:
            logger.debug("Cannot remove proprietary asset: %s", path)


def _collect_proprietary_cleanup_targets() -> dict[str, list[str]]:
    """Collect files/dirs that are subject to post-pilot cleanup."""
    llm_instruction_candidates = [
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "CLAUDE.md",
        REPO_ROOT / "docsops" / "AGENTS.md",
        REPO_ROOT / "docsops" / "CLAUDE.md",
        REPO_ROOT / "LOCAL_MODEL.md",
        REPO_ROOT / "docsops" / "LOCAL_MODEL.md",
    ]
    proprietary_dirs = [
        REPO_ROOT / "docsops" / "runtime" / "ask-ai-pack",
        REPO_ROOT / "runtime" / "ask-ai-pack",
        REPO_ROOT / "instructions" / "llm_plans" / "pilot",
        REPO_ROOT / "instructions" / "llm_plans" / "basic",
        REPO_ROOT / "instructions" / "llm_plans" / "pro",
        REPO_ROOT / "instructions" / "llm_plans" / "enterprise",
    ]
    script_roots = [
        REPO_ROOT / "scripts",
        REPO_ROOT / "docsops" / "scripts",
    ]
    keep_script_basenames = {
        "license_gate.py",
        "normalize_docs.py",
        "validate_frontmatter.py",
        "seo_geo_optimizer.py",
    }

    files = [str(p) for p in llm_instruction_candidates if p.exists()]
    dirs = [str(p) for p in proprietary_dirs if p.exists()]
    scripts: list[str] = []
    for root in script_roots:
        if not root.exists() or not root.is_dir():
            continue
        for path in root.glob("*.py"):
            if path.name in keep_script_basenames:
                continue
            scripts.append(str(path))
    return {
        "files": sorted(files),
        "dirs": sorted(dirs),
        "scripts": sorted(scripts),
    }


def _run_pilot_expiry_cleanup(info: LicenseInfo) -> None:
    """Run proprietary-asset cleanup after pilot expiry, with safety guards.

    Never destructive in the vendor/master repository, and never destructive
    when the license carries permanently free grants (their scripts must
    survive degradation).
    """
    if _is_vendor_repo():
        logger.debug("Pilot expiry cleanup skipped: vendor repository.")
        return
    if info.free_features or info.free_protocols:
        logger.info(
            "Pilot expiry cleanup skipped: license carries permanent free grants."
        )
        return
    _remove_paid_llm_instruction_files()
    _remove_proprietary_assets_after_expiry()


def _effective_plan(info: LicenseInfo) -> str:
    if _pilot_trial_expired(info):
        _run_pilot_expiry_cleanup(info)
        return "community"
    return info.plan


def _effective_features(info: LicenseInfo) -> dict[str, bool]:
    if _pilot_trial_expired(info):
        _run_pilot_expiry_cleanup(info)
        features = dict(COMMUNITY_FEATURES)
        for feat in info.free_features:
            features[feat] = True
        return features
    return dict(info.features)


def _effective_protocols(info: LicenseInfo) -> list[str]:
    if _pilot_trial_expired(info):
        _run_pilot_expiry_cleanup(info)
        protocols = list(COMMUNITY_PROTOCOLS)
        for proto in info.free_protocols:
            if proto not in protocols:
                protocols.append(proto)
        return protocols
    return list(info.protocols)


def allow_advanced_prompts(license_info: LicenseInfo | None = None) -> bool:
    """Whether advanced LLM prompt profile is allowed for current license."""
    info = license_info or validate()
    effective_features = _effective_features(info)
    return bool(effective_features.get("advanced_prompts", False))


def check(feature: str, license_info: LicenseInfo | None = None) -> bool:
    """Check if a feature is enabled in the current license.

    Returns True if the feature is available, False otherwise.
    Prints a warning to stderr when a feature is denied.
    """
    info = license_info or validate()
    effective_plan = _effective_plan(info)
    effective_features = _effective_features(info)
    enabled = effective_features.get(feature, False)
    if not enabled:
        print(
            f"[license] Feature '{feature}' requires plan "
            f"upgrade (current: {effective_plan}). "
            f"Running in degraded mode.",
            file=sys.stderr,
        )
    return enabled


def check_protocol(protocol: str, license_info: LicenseInfo | None = None) -> bool:
    """Check if a protocol is allowed in the current license."""
    info = license_info or validate()
    effective_plan = _effective_plan(info)
    effective_protocols = _effective_protocols(info)
    normalized = protocol.lower().strip()
    allowed = normalized in effective_protocols
    if not allowed:
        print(
            f"[license] Protocol '{protocol}' not available in "
            f"{effective_plan} plan. Allowed: {', '.join(effective_protocols)}",
            file=sys.stderr,
        )
    return allowed


def require(feature: str, license_info: LicenseInfo | None = None) -> LicenseInfo:
    """Require a feature -- raise SystemExit if not available."""
    info = license_info or validate()
    effective_plan = _effective_plan(info)
    effective_features = _effective_features(info)
    if not effective_features.get(feature, False):
        print(
            f"[license] BLOCKED: Feature '{feature}' requires a plan upgrade "
            f"(current: {effective_plan}).",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return info


def require_protocol(protocol: str, license_info: LicenseInfo | None = None) -> LicenseInfo:
    """Require a protocol -- raise SystemExit if not available."""
    info = license_info or validate()
    effective_plan = _effective_plan(info)
    effective_protocols = _effective_protocols(info)
    if protocol.lower().strip() not in effective_protocols:
        print(
            f"[license] BLOCKED: Protocol '{protocol}' requires Enterprise plan "
            f"(current: {effective_plan}).",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return info


def get_license_summary(license_info: LicenseInfo | None = None) -> str:
    """Return a human-readable license summary."""
    info = license_info or validate()
    if not info.valid:
        return f"Community mode: {info.error}"

    effective_plan = _effective_plan(info)
    effective_features = _effective_features(info)
    effective_protocols = _effective_protocols(info)
    enabled = [f for f, v in effective_features.items() if v]
    suffix = ""
    if _pilot_trial_expired(info):
        suffix = " | Pilot trial expired -> degraded mode active"

    return (
        f"Plan: {effective_plan} | Client: {info.client_id} | "
        f"Tenant: {info.tenant_id or '-'} | "
        f"Domain: {info.company_domain or '-'} | "
        f"Days remaining: {info.days_remaining} | "
        f"Features: {len(enabled)} enabled | "
        f"Protocols: {', '.join(effective_protocols)}"
        f"{suffix}"
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
    parser = argparse.ArgumentParser(description="Validate license and report feature entitlements.")
    parser.add_argument(
        "--simulate-pilot-expiry",
        action="store_true",
        help="Dry-run: show what would be removed and which community entitlements would remain after pilot expiry.",
    )
    args = parser.parse_args()

    if bool(args.simulate_pilot_expiry):
        targets = _collect_proprietary_cleanup_targets()
        print("Pilot expiry dry-run (no files removed)")
        print(f"Repo root: {REPO_ROOT}")
        print("Community entitlements after expiry:")
        community_enabled = sorted([k for k, v in COMMUNITY_FEATURES.items() if bool(v)])
        community_disabled = sorted([k for k, v in COMMUNITY_FEATURES.items() if not bool(v)])
        print(f"  Enabled ({len(community_enabled)}): {', '.join(community_enabled)}")
        print(f"  Disabled ({len(community_disabled)}): {', '.join(community_disabled)}")
        print(f"  Protocols: {', '.join(COMMUNITY_PROTOCOLS) if COMMUNITY_PROTOCOLS else '(none)'}")
        print(f"  Remove files ({len(targets['files'])})")
        for item in targets["files"]:
            print(f"    - {item}")
        print(f"  Remove directories ({len(targets['dirs'])})")
        for item in targets["dirs"]:
            print(f"    - {item}")
        print(f"  Remove proprietary scripts ({len(targets['scripts'])})")
        for item in targets["scripts"][:30]:
            print(f"    - {item}")
        if len(targets["scripts"]) > 30:
            print(f"    ... and {len(targets['scripts']) - 30} more")
        return 0

    info = validate()
    print(get_license_summary(info))
    if info.error:
        print(f"  Note: {info.error}")
    print(f"  Valid: {info.valid}")
    print(f"  Plan: {info.plan}")
    if info.valid:
        print(f"  Client: {info.client_id}")
        if info.tenant_id:
            print(f"  Tenant: {info.tenant_id}")
        if info.company_domain:
            print(f"  Company domain: {info.company_domain}")
        print(f"  Expires: {info.expires_at}")
        print(f"  Days remaining: {info.days_remaining}")
        effective_protocols = _effective_protocols(info)
        effective_features = _effective_features(info)
        print(f"  Protocols: {', '.join(effective_protocols)}")
        enabled = sorted(f for f, v in effective_features.items() if v)
        disabled = sorted(f for f, v in effective_features.items() if not v)
        print(f"  Enabled features ({len(enabled)}): {', '.join(enabled)}")
        if disabled:
            print(f"  Disabled features ({len(disabled)}): {', '.join(disabled)}")
    if info.free_features or info.free_protocols:
        print(f"  Permanent free features: {', '.join(info.free_features) or '-'}")
        print(f"  Permanent free protocols: {', '.join(info.free_protocols) or '-'}")
    return 0 if info.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())

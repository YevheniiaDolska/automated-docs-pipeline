#!/usr/bin/env python3
"""Capability pack runtime -- loads and decrypts signed encrypted packs.

A capability pack contains proprietary scoring weights, prompt templates,
and policy thresholds. Packs are encrypted per-client with AES-256-GCM
and the key is derived via HKDF from the license key.

All decryption happens locally. No client data leaves the network.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_PATH = REPO_ROOT / "docsops" / ".capability_pack.enc"
HKDF_SALT = b"veriops-pack-v2"
HKDF_INFO_PREFIX = b"veriops-pack-key-"

# -- Degraded defaults (community mode) ---------------------------------------

DEGRADED_GEO_RULES: dict[str, Any] = {
    "first_para_max_words": 60,
    "max_words_without_fact": 200,
    "meta_desc_min_chars": 50,
    "meta_desc_max_chars": 160,
    "min_heading_words": 3,
    "generic_headings": [
        "overview", "introduction", "configuration", "setup",
        "details", "information", "general", "notes", "summary",
    ],
    "definition_patterns": [
        r"\bis\b", r"\benables?\b", r"\bprovides?\b", r"\ballows?\b",
        r"\bcreates?\b", r"\bprocesses?\b", r"\bexecutes?\b",
    ],
    "fact_patterns": [
        r"\d+", r"`[^`]+`", r"\bdefault\b", r"\bport\b",
        r"\bversion\b", r"\bMB\b", r"\bGB\b", r"\bms\b",
        r"```", r"\bhttp[s]?://\b",
    ],
}

DEGRADED_GEO_RULES_BY_LOCALE: dict[str, dict[str, Any]] = {
    "ru": {
        "first_para_max_words": 80,
        "meta_desc_max_chars": 200,
        "generic_headings": [
            "overview", "introduction", "configuration", "setup",
            "details", "information", "general", "notes", "summary",
            "obzor", "vvedenie", "nastroyka", "nastrojka",
            "podrobnosti", "informatsiya", "obshchee", "zametki",
        ],
    },
    "de": {
        "first_para_max_words": 70,
        "meta_desc_max_chars": 180,
        "generic_headings": [
            "overview", "introduction", "configuration", "setup",
            "details", "information", "general", "notes", "summary",
            "ueberblick", "uebersicht", "einleitung", "konfiguration",
            "einrichtung", "details", "informationen", "allgemein",
        ],
    },
}

DEGRADED_SEO_RULES: dict[str, Any] = {
    "title_min_chars": 10,
    "title_max_chars": 70,
    "max_url_depth": 4,
    "min_internal_links": 1,
    "max_image_without_alt_pct": 0,
    "min_content_words": 100,
    "max_line_length_for_mobile": 180,
    "check_mobile_line_length": True,
    "max_long_lines_before_warning": 30,
}

DEGRADED_KPI_WEIGHTS: dict[str, Any] = {
    "metadata_weight": 0.35,
    "stale_weight": 0.30,
    "gap_penalty_per_item": 3,
    "gap_penalty_cap": 25,
}

DEGRADED_AUDIT_WEIGHTS: dict[str, float] = {
    "api_coverage": 0.22,
    "example_reliability": 0.20,
    "freshness": 0.14,
    "drift": 0.12,
    "layers": 0.12,
    "terminology": 0.10,
    "retrieval": 0.10,
    "hallucination_deduction": 0.08,
}

DEGRADED_RISK_WEIGHTS: dict[str, float] = {
    "undocumented": 0.30,
    "stale": 0.20,
    "drift": 0.20,
    "example_gap": 0.20,
    "terminology": 0.10,
}

DEGRADED_GRADE_THRESHOLDS: dict[str, int] = {
    "A": 90,
    "B": 80,
    "C": 70,
    "D": 60,
}

DEGRADED_TIER_WEIGHTS: dict[str, Any] = {
    "tier1_categories": ["breaking_change", "api_endpoint", "authentication"],
    "tier2_categories": [
        "signature_change", "new_function", "removed_function",
        "webhook", "config_option", "env_var", "cli_command", "stale_doc",
    ],
}


# -- Data classes --------------------------------------------------------------


@dataclass
class CapabilityPack:
    """Decrypted capability pack contents."""

    valid: bool
    plan: str
    version: str
    expires_at: float
    sections: dict[str, Any] = field(default_factory=dict)
    error: str = ""


def _degraded_pack(error: str = "") -> CapabilityPack:
    """Return a community-mode capability pack with flat defaults."""
    return CapabilityPack(
        valid=False,
        plan="community",
        version="0.0.0",
        expires_at=0,
        sections={
            "scoring": {
                "geo_rules": dict(DEGRADED_GEO_RULES),
                "geo_rules_by_locale": {
                    k: dict(v) for k, v in DEGRADED_GEO_RULES_BY_LOCALE.items()
                },
                "seo_rules": dict(DEGRADED_SEO_RULES),
                "kpi_weights": dict(DEGRADED_KPI_WEIGHTS),
                "audit_weights": dict(DEGRADED_AUDIT_WEIGHTS),
                "risk_weights": dict(DEGRADED_RISK_WEIGHTS),
                "grade_thresholds": dict(DEGRADED_GRADE_THRESHOLDS),
            },
            "priority": dict(DEGRADED_TIER_WEIGHTS),
            "prompts": {},
            "policies": {},
        },
        error=error or "No capability pack. Using degraded defaults.",
    )


# -- HKDF-SHA256 (RFC 5869) ---------------------------------------------------


def _hmac_sha256(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha256).digest()


def _hkdf_extract(salt: bytes, ikm: bytes) -> bytes:
    """HKDF-Extract: PRK = HMAC-SHA256(salt, IKM)."""
    return _hmac_sha256(salt, ikm)


def _hkdf_expand(prk: bytes, info: bytes, length: int = 32) -> bytes:
    """HKDF-Expand: OKM = T(1) || T(2) || ... truncated to length."""
    n = (length + 31) // 32
    okm = b""
    t = b""
    for i in range(1, n + 1):
        t = _hmac_sha256(prk, t + info + bytes([i]))
        okm += t
    return okm[:length]


def derive_pack_key(license_key: str, client_id: str) -> bytes:
    """Derive AES-256 key from license key and client ID via HKDF-SHA256."""
    ikm = license_key.encode("utf-8")
    info = HKDF_INFO_PREFIX + client_id.encode("utf-8")
    prk = _hkdf_extract(HKDF_SALT, ikm)
    return _hkdf_expand(prk, info, 32)


# -- AES-256-GCM encryption/decryption ----------------------------------------


def _aes_gcm_decrypt(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes) -> bytes:
    """Decrypt AES-256-GCM. Tries cryptography library."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aes = AESGCM(key)
        # cryptography expects ciphertext + tag concatenated
        return aes.decrypt(nonce, ciphertext + tag, None)
    except ImportError:
        logger.debug("cryptography is not installed; trying PyCryptodome for AES-GCM decrypt")
    except (RuntimeError, ValueError, TypeError, OSError) as exc:
        raise ValueError(f"AES-GCM decrypt failed: {exc}") from exc

    # Fallback: PyCryptodome
    try:
        from Crypto.Cipher import AES
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag)
    except ImportError:
        logger.debug("PyCryptodome is not installed; AES-GCM decrypt fallback unavailable")
    except (RuntimeError, ValueError, TypeError, OSError) as exc:
        raise ValueError(f"AES-GCM decrypt failed: {exc}") from exc

    raise RuntimeError(
        "No AES-GCM library available. Install 'cryptography' or 'pycryptodome'."
    )


def _aes_gcm_encrypt(key: bytes, plaintext: bytes) -> tuple[bytes, bytes, bytes]:
    """Encrypt with AES-256-GCM. Returns (nonce, ciphertext, tag)."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aes = AESGCM(key)
        nonce = os.urandom(12)
        ct_with_tag = aes.encrypt(nonce, plaintext, None)
        # Last 16 bytes are the tag
        ciphertext = ct_with_tag[:-16]
        tag = ct_with_tag[-16:]
        return nonce, ciphertext, tag
    except ImportError:
        logger.debug("cryptography is not installed; trying PyCryptodome for AES-GCM encrypt")

    try:
        from Crypto.Cipher import AES
        nonce = os.urandom(12)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)
        return nonce, ciphertext, tag
    except ImportError:
        logger.debug("PyCryptodome is not installed; AES-GCM encrypt fallback unavailable")

    raise RuntimeError(
        "No AES-GCM library available. Install 'cryptography' or 'pycryptodome'."
    )


# -- Pack file format ----------------------------------------------------------
#
# Binary layout:
#   4 bytes: magic "VPAK"
#   2 bytes: format version (uint16 big-endian, currently 1)
#  12 bytes: AES-GCM nonce
#  16 bytes: AES-GCM authentication tag
#   N bytes: AES-GCM ciphertext (rest of file)
#
# Plaintext is UTF-8 JSON matching build/pack_schema.yml.


PACK_MAGIC = b"VPAK"
PACK_FORMAT_VERSION = 1


def _parse_pack_file(data: bytes) -> tuple[bytes, bytes, bytes]:
    """Parse binary pack file into (nonce, tag, ciphertext)."""
    if len(data) < 34:
        raise ValueError("Pack file too small")
    if data[:4] != PACK_MAGIC:
        raise ValueError("Invalid pack file magic")
    version = int.from_bytes(data[4:6], "big")
    if version != PACK_FORMAT_VERSION:
        raise ValueError(f"Unsupported pack format version: {version}")
    nonce = data[6:18]
    tag = data[18:34]
    ciphertext = data[34:]
    return nonce, tag, ciphertext


def build_pack_file(nonce: bytes, tag: bytes, ciphertext: bytes) -> bytes:
    """Build binary pack file from components."""
    header = PACK_MAGIC + PACK_FORMAT_VERSION.to_bytes(2, "big")
    return header + nonce + tag + ciphertext


# -- Pack loading --------------------------------------------------------------


def load_pack(
    pack_path: Path | None = None,
    license_key: str | None = None,
    client_id: str | None = None,
    current_time: float | None = None,
) -> CapabilityPack:
    """Load and decrypt a capability pack.

    Falls back to degraded defaults if pack is missing, expired, or undecryptable.
    """
    fpath = pack_path or PACK_PATH
    if not fpath.exists():
        return _degraded_pack("Pack file not found: " + str(fpath))

    if not license_key or not client_id:
        return _degraded_pack("License key or client ID not provided for decryption.")

    try:
        raw = fpath.read_bytes()
    except OSError as exc:
        return _degraded_pack(f"Cannot read pack file: {exc}")

    try:
        nonce, tag, ciphertext = _parse_pack_file(raw)
    except ValueError as exc:
        return _degraded_pack(f"Invalid pack file: {exc}")

    # Derive key and decrypt
    aes_key = derive_pack_key(license_key, client_id)
    try:
        plaintext = _aes_gcm_decrypt(aes_key, nonce, ciphertext, tag)
    except (RuntimeError, ValueError, TypeError, OSError) as exc:
        return _degraded_pack(f"Pack decryption failed: {exc}")

    try:
        payload = json.loads(plaintext.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return _degraded_pack(f"Pack JSON parse failed: {exc}")

    # Validate expiration
    now = current_time if current_time is not None else time.time()
    expires_at = float(payload.get("expires_at", 0))
    if expires_at and now > expires_at:
        return _degraded_pack(f"Pack expired at {expires_at}.")

    return CapabilityPack(
        valid=True,
        plan=str(payload.get("plan", "unknown")),
        version=str(payload.get("version", "0.0.0")),
        expires_at=expires_at,
        sections=payload.get("sections", {}),
    )


# -- Accessors for scoring modules -------------------------------------------


def get_geo_rules(pack: CapabilityPack | None = None) -> dict[str, Any]:
    """Get GEO rules from pack or degraded defaults."""
    if pack is None or not pack.valid:
        return dict(DEGRADED_GEO_RULES)
    scoring = pack.sections.get("scoring", {})
    return scoring.get("geo_rules", dict(DEGRADED_GEO_RULES))


def get_kpi_weights(pack: CapabilityPack | None = None) -> dict[str, float]:
    """Get KPI quality score weights from pack or degraded defaults."""
    if pack is None or not pack.valid:
        return dict(DEGRADED_KPI_WEIGHTS)
    scoring = pack.sections.get("scoring", {})
    return scoring.get("kpi_weights", dict(DEGRADED_KPI_WEIGHTS))


def get_audit_weights(pack: CapabilityPack | None = None) -> dict[str, float]:
    """Get audit scorecard weights from pack or degraded defaults."""
    if pack is None or not pack.valid:
        return dict(DEGRADED_AUDIT_WEIGHTS)
    scoring = pack.sections.get("scoring", {})
    return scoring.get("audit_weights", dict(DEGRADED_AUDIT_WEIGHTS))


def get_geo_rules_by_locale(
    pack: CapabilityPack | None = None, locale: str | None = None,
) -> dict[str, Any]:
    """Get locale-specific GEO rule overrides from pack or degraded defaults.

    If *locale* is given, returns the merged rules for that locale.
    If *locale* is ``None``, returns the full locale-override mapping.
    """
    if pack is None or not pack.valid:
        src = {k: dict(v) for k, v in DEGRADED_GEO_RULES_BY_LOCALE.items()}
    else:
        scoring = pack.sections.get("scoring", {})
        src = scoring.get(
            "geo_rules_by_locale",
            {k: dict(v) for k, v in DEGRADED_GEO_RULES_BY_LOCALE.items()},
        )
    if locale is None:
        return src
    overrides = src.get(locale)
    if overrides is None:
        return get_geo_rules(pack)
    merged = get_geo_rules(pack).copy()
    merged.update(overrides)
    return merged


def get_seo_rules(pack: CapabilityPack | None = None) -> dict[str, Any]:
    """Get SEO rules from pack or degraded defaults."""
    if pack is None or not pack.valid:
        return dict(DEGRADED_SEO_RULES)
    scoring = pack.sections.get("scoring", {})
    return scoring.get("seo_rules", dict(DEGRADED_SEO_RULES))


def get_risk_weights(pack: CapabilityPack | None = None) -> dict[str, float]:
    """Get audit scorecard risk index weights from pack or degraded defaults."""
    if pack is None or not pack.valid:
        return dict(DEGRADED_RISK_WEIGHTS)
    scoring = pack.sections.get("scoring", {})
    return scoring.get("risk_weights", dict(DEGRADED_RISK_WEIGHTS))


def get_grade_thresholds(pack: CapabilityPack | None = None) -> dict[str, int]:
    """Get grade letter thresholds from pack or degraded defaults."""
    if pack is None or not pack.valid:
        return dict(DEGRADED_GRADE_THRESHOLDS)
    scoring = pack.sections.get("scoring", {})
    return scoring.get("grade_thresholds", dict(DEGRADED_GRADE_THRESHOLDS))


def get_tier_weights(pack: CapabilityPack | None = None) -> dict[str, Any]:
    """Get tier classification weights from pack or degraded defaults."""
    if pack is None or not pack.valid:
        return dict(DEGRADED_TIER_WEIGHTS)
    return pack.sections.get("priority", dict(DEGRADED_TIER_WEIGHTS))


def get_prompts(pack: CapabilityPack | None = None) -> dict[str, str]:
    """Get prompt templates from pack."""
    if pack is None or not pack.valid:
        return {}
    return pack.sections.get("prompts", {})


def get_policies(pack: CapabilityPack | None = None) -> dict[str, Any]:
    """Get policy rule sets from pack."""
    if pack is None or not pack.valid:
        return {}
    return pack.sections.get("policies", {})


# -- Singleton cache -----------------------------------------------------------

_cached_pack: CapabilityPack | None = None


def get_pack(force_reload: bool = False, **kwargs: Any) -> CapabilityPack:
    """Get cached capability pack (loads once per process)."""
    global _cached_pack
    if _cached_pack is None or force_reload:
        _cached_pack = load_pack(**kwargs)
    return _cached_pack


def reset_cache() -> None:
    """Clear the cached pack (useful for testing)."""
    global _cached_pack
    _cached_pack = None


# -- CLI -----------------------------------------------------------------------


def main() -> int:
    """CLI entry point: attempt to load and display pack info."""
    parser = argparse.ArgumentParser(description="VeriOps capability pack loader")
    parser.add_argument("--pack", default=str(PACK_PATH), help="Path to .capability_pack.enc")
    parser.add_argument("--license-key", default="", help="License key for decryption")
    parser.add_argument("--client-id", default="", help="Client ID for key derivation")
    args = parser.parse_args()

    pack = load_pack(
        pack_path=Path(args.pack),
        license_key=args.license_key or None,
        client_id=args.client_id or None,
    )
    print(f"Valid: {pack.valid}")
    print(f"Plan: {pack.plan}")
    print(f"Version: {pack.version}")
    if pack.error:
        print(f"Error: {pack.error}")
    if pack.valid:
        print(f"Sections: {', '.join(pack.sections.keys())}")
        print(f"Expires: {pack.expires_at}")
    return 0 if pack.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())

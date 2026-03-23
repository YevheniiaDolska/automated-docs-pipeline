#!/usr/bin/env python3
"""Tests for scripts/license_gate.py -- JWT validation, feature gating, degraded mode."""

from __future__ import annotations

import base64
import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.license_gate import (
    COMMUNITY_FEATURES,
    COMMUNITY_PROTOCOLS,
    DEFAULT_GRACE_DAYS,
    PLAN_FEATURES,
    PLAN_PROTOCOLS,
    LicenseInfo,
    _b64url_decode,
    _community_license,
    _parse_jwt_parts,
    check,
    check_protocol,
    get_license,
    get_license_summary,
    machine_fingerprint,
    require,
    require_protocol,
    reset_cache,
    validate,
)


# -- Helpers -------------------------------------------------------------------


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _make_unsigned_jwt(payload: dict, header: dict | None = None) -> str:
    """Create a JWT without real signature (for testing parse logic)."""
    hdr = header or {"alg": "EdDSA", "typ": "JWT"}
    h = _b64url_encode(json.dumps(hdr, separators=(",", ":")).encode())
    p = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    # Fake 64-byte signature
    s = _b64url_encode(b"\x00" * 64)
    return f"{h}.{p}.{s}"


@pytest.fixture(autouse=True)
def _reset_license_cache(monkeypatch):
    """Reset the license cache and clear env override before each test."""
    monkeypatch.delenv("VERIOPS_LICENSE_PLAN", raising=False)
    monkeypatch.delenv("VERIOPS_CLIENT_ID", raising=False)
    reset_cache()
    yield
    reset_cache()


# -- b64url_decode tests -------------------------------------------------------


class TestB64UrlDecode:
    def test_standard_padding(self):
        original = b"hello world"
        encoded = base64.urlsafe_b64encode(original).rstrip(b"=").decode()
        assert _b64url_decode(encoded) == original

    def test_empty(self):
        assert _b64url_decode("") == b""

    def test_url_safe_chars(self):
        data = b"\xff\xfe\xfd"
        encoded = base64.urlsafe_b64encode(data).rstrip(b"=").decode()
        assert _b64url_decode(encoded) == data


# -- JWT parsing ---------------------------------------------------------------


class TestParseJwt:
    def test_valid_jwt(self):
        payload = {"sub": "test", "plan": "enterprise", "exp": 9999999999}
        token = _make_unsigned_jwt(payload)
        header, claims, sig = _parse_jwt_parts(token)
        assert header["alg"] == "EdDSA"
        assert claims["sub"] == "test"
        assert claims["plan"] == "enterprise"
        assert len(sig) == 64

    def test_invalid_format_too_few_parts(self):
        with pytest.raises(ValueError, match="3 dot-separated"):
            _parse_jwt_parts("only.two")

    def test_invalid_format_too_many_parts(self):
        with pytest.raises(ValueError, match="3 dot-separated"):
            _parse_jwt_parts("a.b.c.d")

    def test_invalid_json_header(self):
        bad = _b64url_encode(b"not-json")
        p = _b64url_encode(b'{"sub":"x"}')
        s = _b64url_encode(b"\x00" * 64)
        with pytest.raises(json.JSONDecodeError):
            _parse_jwt_parts(f"{bad}.{p}.{s}")


# -- Community license ---------------------------------------------------------


class TestCommunityLicense:
    def test_defaults(self):
        lic = _community_license()
        assert lic.valid is False
        assert lic.plan == "community"
        assert lic.features == dict(COMMUNITY_FEATURES)
        assert lic.protocols == list(COMMUNITY_PROTOCOLS)

    def test_custom_error(self):
        lic = _community_license("custom error message")
        assert "custom error message" in lic.error


# -- Plan tiers ----------------------------------------------------------------


class TestPlanFeatures:
    def test_pilot_features(self):
        features = PLAN_FEATURES["pilot"]
        assert features["markdown_lint"] is True
        assert features["seo_geo_scoring"] is False
        assert features["multi_protocol_pipeline"] is False
        assert features["executive_audit_pdf"] is False

    def test_professional_features(self):
        features = PLAN_FEATURES["professional"]
        assert features["seo_geo_scoring"] is True
        assert features["api_first_flow"] is True
        assert features["drift_detection"] is True
        assert features["multi_protocol_pipeline"] is False
        assert features["knowledge_modules"] is False

    def test_enterprise_features(self):
        features = PLAN_FEATURES["enterprise"]
        all_true = all(v for v in features.values())
        assert all_true, "Enterprise should have all features enabled"

    def test_pilot_protocols(self):
        assert PLAN_PROTOCOLS["pilot"] == ["rest"]

    def test_enterprise_protocols(self):
        protos = PLAN_PROTOCOLS["enterprise"]
        assert "rest" in protos
        assert "graphql" in protos
        assert "grpc" in protos
        assert "asyncapi" in protos
        assert "websocket" in protos


# -- Validation ----------------------------------------------------------------


class TestValidate:
    def test_missing_license_file(self, tmp_path):
        result = validate(license_path=tmp_path / "nonexistent.jwt")
        assert result.valid is False
        assert result.plan == "community"
        assert "not found" in result.error

    def test_empty_license_file(self, tmp_path):
        f = tmp_path / "empty.jwt"
        f.write_text("")
        result = validate(license_path=f)
        assert result.valid is False
        assert "empty" in result.error

    def test_invalid_jwt_format(self, tmp_path):
        f = tmp_path / "bad.jwt"
        f.write_text("not-a-jwt")
        result = validate(license_path=f)
        assert result.valid is False
        assert "Invalid" in result.error or "format" in result.error.lower()

    def test_valid_jwt_no_signature_check(self, tmp_path):
        """Without a public key, signature check is skipped."""
        payload = {
            "sub": "acme-corp",
            "plan": "enterprise",
            "exp": int(time.time()) + 86400 * 365,
            "features": {},
            "protocols": ["rest", "graphql", "grpc", "asyncapi", "websocket"],
            "max_docs": 5000,
            "offline_grace_days": 30,
        }
        token = _make_unsigned_jwt(payload)
        f = tmp_path / "license.jwt"
        f.write_text(token)

        # No public key -> signature check returns False but we still parse
        # Actually with no key file, verify is skipped entirely
        result = validate(license_path=f, key_path=tmp_path / "no-key.pub")
        assert result.valid is True
        assert result.plan == "enterprise"
        assert result.client_id == "acme-corp"
        assert result.max_docs == 5000

    def test_expired_license_within_grace(self, tmp_path):
        """License expired but within grace period."""
        now = time.time()
        payload = {
            "sub": "acme-corp",
            "plan": "professional",
            "exp": int(now - 3600),  # Expired 1 hour ago
            "offline_grace_days": 7,
        }
        token = _make_unsigned_jwt(payload)
        f = tmp_path / "license.jwt"
        f.write_text(token)

        result = validate(license_path=f, key_path=tmp_path / "no-key.pub", current_time=now)
        assert result.valid is True
        assert "grace" in result.error.lower()

    def test_expired_license_past_grace(self, tmp_path):
        """License expired and grace period also elapsed."""
        now = time.time()
        payload = {
            "sub": "acme-corp",
            "plan": "pilot",
            "exp": int(now - 86400 * 30),  # Expired 30 days ago
            "offline_grace_days": 3,  # Grace was 3 days
        }
        token = _make_unsigned_jwt(payload)
        f = tmp_path / "license.jwt"
        f.write_text(token)

        result = validate(license_path=f, key_path=tmp_path / "no-key.pub", current_time=now)
        assert result.valid is False
        assert result.plan == "community"

    def test_plan_determines_features(self, tmp_path):
        """Features are derived from the plan tier."""
        for plan in ["pilot", "professional", "enterprise"]:
            payload = {
                "sub": f"test-{plan}",
                "plan": plan,
                "exp": int(time.time()) + 86400,
            }
            token = _make_unsigned_jwt(payload)
            f = tmp_path / f"license-{plan}.jwt"
            f.write_text(token)

            result = validate(license_path=f, key_path=tmp_path / "no-key.pub")
            assert result.valid is True
            assert result.plan == plan

            expected = PLAN_FEATURES[plan]
            for feature, enabled in expected.items():
                assert result.features.get(feature) == enabled, \
                    f"Plan {plan}: feature {feature} expected {enabled}"

    def test_jwt_can_restrict_features(self, tmp_path):
        """JWT features field can disable (but not enable beyond plan)."""
        payload = {
            "sub": "restricted",
            "plan": "enterprise",
            "exp": int(time.time()) + 86400,
            "features": {"i18n_system": False},
        }
        token = _make_unsigned_jwt(payload)
        f = tmp_path / "license.jwt"
        f.write_text(token)

        result = validate(license_path=f, key_path=tmp_path / "no-key.pub")
        assert result.valid is True
        assert result.features["i18n_system"] is False
        assert result.features["executive_audit_pdf"] is True


# -- Feature checks ------------------------------------------------------------


class TestFeatureCheck:
    def test_check_enabled_feature(self):
        lic = LicenseInfo(
            valid=True, plan="enterprise", client_id="test",
            features={"drift_detection": True},
            protocols=["rest"], max_docs=0,
            offline_grace_days=30, expires_at=0,
            days_remaining=365, error="",
        )
        assert check("drift_detection", lic) is True

    def test_check_disabled_feature(self, capsys):
        lic = LicenseInfo(
            valid=True, plan="pilot", client_id="test",
            features={"drift_detection": False},
            protocols=["rest"], max_docs=0,
            offline_grace_days=3, expires_at=0,
            days_remaining=90, error="",
        )
        assert check("drift_detection", lic) is False
        captured = capsys.readouterr()
        assert "upgrade" in captured.err.lower()

    def test_check_unknown_feature(self, capsys):
        lic = _community_license()
        assert check("nonexistent_feature", lic) is False

    def test_require_raises_on_missing_feature(self):
        lic = LicenseInfo(
            valid=True, plan="pilot", client_id="test",
            features={"executive_audit_pdf": False},
            protocols=["rest"], max_docs=0,
            offline_grace_days=3, expires_at=0,
            days_remaining=90, error="",
        )
        with pytest.raises(SystemExit):
            require("executive_audit_pdf", lic)

    def test_require_passes_on_enabled_feature(self):
        lic = LicenseInfo(
            valid=True, plan="enterprise", client_id="test",
            features={"executive_audit_pdf": True},
            protocols=["rest", "graphql"], max_docs=0,
            offline_grace_days=30, expires_at=0,
            days_remaining=365, error="",
        )
        result = require("executive_audit_pdf", lic)
        assert result.plan == "enterprise"


# -- Protocol checks -----------------------------------------------------------


class TestProtocolCheck:
    def test_allowed_protocol(self):
        lic = LicenseInfo(
            valid=True, plan="enterprise", client_id="test",
            features={}, protocols=["rest", "graphql", "grpc"],
            max_docs=0, offline_grace_days=30, expires_at=0,
            days_remaining=365, error="",
        )
        assert check_protocol("graphql", lic) is True
        assert check_protocol("grpc", lic) is True

    def test_denied_protocol(self, capsys):
        lic = LicenseInfo(
            valid=True, plan="pilot", client_id="test",
            features={}, protocols=["rest"],
            max_docs=0, offline_grace_days=3, expires_at=0,
            days_remaining=90, error="",
        )
        assert check_protocol("graphql", lic) is False
        captured = capsys.readouterr()
        assert "not available" in captured.err.lower()

    def test_require_protocol_raises(self):
        lic = LicenseInfo(
            valid=True, plan="pilot", client_id="test",
            features={}, protocols=["rest"],
            max_docs=0, offline_grace_days=3, expires_at=0,
            days_remaining=90, error="",
        )
        with pytest.raises(SystemExit):
            require_protocol("grpc", lic)


# -- Machine fingerprint ------------------------------------------------------


class TestMachineFingerprint:
    def test_deterministic(self):
        fp1 = machine_fingerprint()
        fp2 = machine_fingerprint()
        assert fp1 == fp2
        assert len(fp1) == 64  # SHA-256 hex

    def test_is_hex(self):
        fp = machine_fingerprint()
        int(fp, 16)  # Should not raise


# -- License summary -----------------------------------------------------------


class TestLicenseSummary:
    def test_community_summary(self):
        lic = _community_license()
        summary = get_license_summary(lic)
        assert "Community" in summary or "community" in summary.lower()

    def test_valid_summary(self):
        lic = LicenseInfo(
            valid=True, plan="professional", client_id="acme",
            features=PLAN_FEATURES["professional"],
            protocols=["rest"], max_docs=500,
            offline_grace_days=7, expires_at=time.time() + 86400 * 30,
            days_remaining=30, error="",
        )
        summary = get_license_summary(lic)
        assert "professional" in summary.lower()
        assert "acme" in summary


# -- Cache ---------------------------------------------------------------------


class TestCache:
    def test_cache_returns_same_object(self, tmp_path):
        payload = {
            "sub": "cached", "plan": "pilot",
            "exp": int(time.time()) + 86400,
        }
        token = _make_unsigned_jwt(payload)
        f = tmp_path / "license.jwt"
        f.write_text(token)

        with patch("scripts.license_gate.LICENSE_PATH", f), \
             patch("scripts.license_gate.PUBLIC_KEY_PATH", tmp_path / "no.pub"):
            reset_cache()
            lic1 = get_license()
            lic2 = get_license()
            assert lic1 is lic2

    def test_force_reload(self, tmp_path):
        payload = {
            "sub": "reload", "plan": "pilot",
            "exp": int(time.time()) + 86400,
        }
        token = _make_unsigned_jwt(payload)
        f = tmp_path / "license.jwt"
        f.write_text(token)

        with patch("scripts.license_gate.LICENSE_PATH", f), \
             patch("scripts.license_gate.PUBLIC_KEY_PATH", tmp_path / "no.pub"):
            reset_cache()
            lic1 = get_license()
            lic2 = get_license(force_reload=True)
            assert lic1 is not lic2


# -- Grace days ----------------------------------------------------------------


class TestGraceDays:
    def test_default_grace_days_per_plan(self):
        assert DEFAULT_GRACE_DAYS["pilot"] == 3
        assert DEFAULT_GRACE_DAYS["professional"] == 7
        assert DEFAULT_GRACE_DAYS["enterprise"] == 30

    def test_custom_grace_from_jwt(self, tmp_path):
        payload = {
            "sub": "grace-test",
            "plan": "pilot",
            "exp": int(time.time()) + 86400,
            "offline_grace_days": 14,
        }
        token = _make_unsigned_jwt(payload)
        f = tmp_path / "license.jwt"
        f.write_text(token)

        result = validate(license_path=f, key_path=tmp_path / "no.pub")
        assert result.offline_grace_days == 14

#!/usr/bin/env python3
"""Tests for scripts/license_gate.py -- JWT validation, feature gating, degraded mode."""

from __future__ import annotations

import base64
import json
import sys
import time
import urllib.error
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.license_gate import (
    COMMUNITY_FEATURES,
    COMMUNITY_PROTOCOLS,
    DEFAULT_GRACE_DAYS,
    HEARTBEAT_PATH,
    PLAN_FEATURES,
    PLAN_PROTOCOLS,
    LicenseInfo,
    _b64url_decode,
    _community_license,
    _parse_jwt_parts,
    _phone_home_due,
    _read_heartbeat,
    _write_heartbeat,
    check,
    check_protocol,
    get_license,
    get_license_summary,
    machine_fingerprint,
    phone_home,
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
        assert features["multi_protocol_pipeline"] is True
        assert features["knowledge_modules"] is True
        assert features["knowledge_graph"] is True
        assert features["faiss_retrieval"] is False
        assert features["executive_audit_pdf"] is True
        assert features["i18n_system"] is True

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

    def test_professional_protocols(self):
        protos = PLAN_PROTOCOLS["professional"]
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


# -- Heartbeat helpers --------------------------------------------------------


class TestReadHeartbeat:
    def test_missing_file(self, tmp_path):
        assert _read_heartbeat(tmp_path / "missing.json") == {}

    def test_valid_file(self, tmp_path):
        f = tmp_path / "hb.json"
        f.write_text('{"last_check": 1000, "last_result": "success"}')
        hb = _read_heartbeat(f)
        assert hb["last_check"] == 1000
        assert hb["last_result"] == "success"

    def test_corrupt_json(self, tmp_path):
        f = tmp_path / "hb.json"
        f.write_text("{bad json")
        assert _read_heartbeat(f) == {}

    def test_empty_file(self, tmp_path):
        f = tmp_path / "hb.json"
        f.write_text("")
        assert _read_heartbeat(f) == {}


class TestWriteHeartbeat:
    def test_creates_file(self, tmp_path):
        f = tmp_path / "sub" / "hb.json"
        _write_heartbeat({"last_check": 42}, f)
        assert f.exists()
        data = json.loads(f.read_text())
        assert data["last_check"] == 42

    def test_overwrites_existing(self, tmp_path):
        f = tmp_path / "hb.json"
        _write_heartbeat({"last_check": 1}, f)
        _write_heartbeat({"last_check": 2}, f)
        data = json.loads(f.read_text())
        assert data["last_check"] == 2


# -- Phone-home interval check -----------------------------------------------


class TestPhoneHomeDue:
    def test_empty_heartbeat_is_due(self):
        # Empty dict -> last_check defaults to 0 (epoch), so any modern timestamp is due
        assert _phone_home_due({}, interval_days=30, current_time=3_000_000) is True

    def test_never_checked_is_due(self):
        assert _phone_home_due({"last_check": 0}, interval_days=1, current_time=90000) is True

    def test_recently_checked_not_due(self):
        now = time.time()
        hb = {"last_check": now - 3600}  # 1 hour ago
        assert _phone_home_due(hb, interval_days=30, current_time=now) is False

    def test_past_interval_is_due(self):
        now = time.time()
        hb = {"last_check": now - 31 * 86400}  # 31 days ago
        assert _phone_home_due(hb, interval_days=30, current_time=now) is True

    def test_exactly_at_boundary(self):
        now = 1000000.0
        hb = {"last_check": now - 30 * 86400}  # exactly 30 days
        assert _phone_home_due(hb, interval_days=30, current_time=now) is True

    def test_invalid_last_check_type(self):
        assert _phone_home_due({"last_check": "bad"}, interval_days=1, current_time=1000) is True

    def test_custom_interval(self):
        now = 1000000.0
        hb = {"last_check": now - 7 * 86400}
        assert _phone_home_due(hb, interval_days=7, current_time=now) is True
        assert _phone_home_due(hb, interval_days=8, current_time=now) is False


# -- Phone-home function ------------------------------------------------------


def _mock_urlopen_response(body_dict: dict, status: int = 200):
    """Create a mock urllib response."""
    body = json.dumps(body_dict).encode("utf-8")
    resp = MagicMock()
    resp.read.return_value = body
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestPhoneHome:
    def test_disabled_skips(self, tmp_path):
        with patch("scripts.license_gate.PHONE_HOME_ENABLED", False):
            result = phone_home(
                client_id="acme",
                heartbeat_path=tmp_path / "hb.json",
            )
        assert result["skipped"] is True
        assert "disabled" in result["error"].lower()

    def test_no_client_id_skips(self, tmp_path):
        result = phone_home(
            client_id="",
            heartbeat_path=tmp_path / "hb.json",
        )
        assert result["skipped"] is True
        assert "community" in result["error"].lower()

    def test_not_due_skips(self, tmp_path):
        hb_path = tmp_path / "hb.json"
        now = time.time()
        _write_heartbeat({"last_check": now}, hb_path)

        result = phone_home(
            client_id="acme",
            heartbeat_path=hb_path,
            current_time=now,
            interval_days=30,
        )
        assert result["skipped"] is True
        assert result["refreshed"] is False

    def test_force_ignores_interval(self, tmp_path):
        hb_path = tmp_path / "hb.json"
        now = time.time()
        _write_heartbeat({"last_check": now}, hb_path)

        new_jwt = _make_unsigned_jwt({
            "sub": "acme", "plan": "enterprise",
            "exp": int(now) + 86400,
        })
        mock_resp = _mock_urlopen_response({"token": new_jwt})

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = phone_home(
                client_id="acme",
                license_path=tmp_path / "license.jwt",
                heartbeat_path=hb_path,
                base_url="http://localhost:9999",
                current_time=now,
                force=True,
            )
        assert result["refreshed"] is True

    def test_successful_refresh(self, tmp_path):
        hb_path = tmp_path / "hb.json"
        lic_path = tmp_path / "license.jwt"
        now = time.time()

        new_jwt = _make_unsigned_jwt({
            "sub": "acme", "plan": "professional",
            "exp": int(now) + 86400 * 365,
        })
        mock_resp = _mock_urlopen_response({"token": new_jwt})

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = phone_home(
                client_id="acme",
                license_path=lic_path,
                heartbeat_path=hb_path,
                base_url="http://localhost:9999",
                current_time=now,
                force=True,
            )

        assert result["refreshed"] is True
        assert result["error"] is None
        assert lic_path.exists()
        assert lic_path.read_text() == new_jwt

        hb = json.loads(hb_path.read_text())
        assert hb["last_result"] == "success"
        assert hb["last_check"] == now

    def test_empty_token_from_server(self, tmp_path):
        hb_path = tmp_path / "hb.json"
        now = time.time()
        mock_resp = _mock_urlopen_response({"token": ""})

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = phone_home(
                client_id="acme",
                heartbeat_path=hb_path,
                base_url="http://localhost:9999",
                current_time=now,
                force=True,
            )

        assert result["refreshed"] is False
        assert "empty" in result["error"].lower()

    def test_invalid_jwt_from_server(self, tmp_path):
        hb_path = tmp_path / "hb.json"
        now = time.time()
        mock_resp = _mock_urlopen_response({"token": "not.a.valid-jwt-at-all"})

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = phone_home(
                client_id="acme",
                heartbeat_path=hb_path,
                base_url="http://localhost:9999",
                current_time=now,
                force=True,
            )

        assert result["refreshed"] is False
        assert "invalid" in result["error"].lower()

    def test_http_error(self, tmp_path):
        hb_path = tmp_path / "hb.json"
        now = time.time()

        exc = urllib.error.HTTPError(
            url="http://localhost/billing/license/token",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=BytesIO(b""),
        )

        with patch("urllib.request.urlopen", side_effect=exc):
            result = phone_home(
                client_id="acme",
                heartbeat_path=hb_path,
                base_url="http://localhost:9999",
                current_time=now,
                force=True,
            )

        assert result["refreshed"] is False
        assert "401" in result["error"]
        # HTTP errors DO write heartbeat (to avoid hammering)
        hb = json.loads(hb_path.read_text())
        assert hb["last_result"] == "error_http_401"

    def test_network_error_no_heartbeat_update(self, tmp_path):
        """Network errors should NOT update last_check so retry happens next time."""
        hb_path = tmp_path / "hb.json"
        now = time.time()

        exc = urllib.error.URLError("Connection refused")

        with patch("urllib.request.urlopen", side_effect=exc):
            result = phone_home(
                client_id="acme",
                heartbeat_path=hb_path,
                base_url="http://localhost:9999",
                current_time=now,
                force=True,
            )

        assert result["refreshed"] is False
        assert "network" in result["error"].lower()
        # Heartbeat file should NOT be created/updated
        assert not hb_path.exists()

    def test_sends_correct_headers(self, tmp_path):
        hb_path = tmp_path / "hb.json"
        now = time.time()

        new_jwt = _make_unsigned_jwt({
            "sub": "acme", "plan": "pilot",
            "exp": int(now) + 86400,
        })
        mock_resp = _mock_urlopen_response({"token": new_jwt})

        captured_req = None

        def capture_urlopen(req, **kwargs):
            nonlocal captured_req
            captured_req = req
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=capture_urlopen):
            phone_home(
                client_id="acme-corp",
                license_path=tmp_path / "license.jwt",
                heartbeat_path=hb_path,
                base_url="http://test.local",
                current_time=now,
                force=True,
            )

        assert captured_req is not None
        assert captured_req.get_header("X-client-id") == "acme-corp"
        assert captured_req.get_header("X-machine-fingerprint") is not None
        assert len(captured_req.get_header("X-machine-fingerprint")) == 64
        assert "test.local/billing/license/token" in captured_req.full_url


# -- Phone-home integration in validate() ------------------------------------


class TestPhoneHomeIntegration:
    def test_validate_triggers_phone_home_when_due(self, tmp_path):
        """validate() should call phone_home when interval has elapsed."""
        now = time.time()
        payload = {
            "sub": "acme", "plan": "enterprise",
            "exp": int(now) + 86400 * 365,
        }
        token = _make_unsigned_jwt(payload)
        lic_path = tmp_path / "license.jwt"
        lic_path.write_text(token)

        ph_called = False

        def mock_phone_home(**kwargs):
            nonlocal ph_called
            ph_called = True
            return {"refreshed": False, "skipped": False, "error": None}

        with patch("scripts.license_gate.phone_home", side_effect=mock_phone_home), \
             patch("scripts.license_gate.PHONE_HOME_ENABLED", True):
            result = validate(
                license_path=lic_path,
                key_path=tmp_path / "no.pub",
                current_time=now,
            )

        assert result.valid is True
        assert ph_called is True

    def test_validate_skips_phone_home_for_env_plan(self, tmp_path, monkeypatch):
        """Phone-home should not trigger when using VERIOPS_LICENSE_PLAN env bypass."""
        monkeypatch.setenv("VERIOPS_LICENSE_PLAN", "enterprise")

        ph_called = False

        def mock_phone_home(**kwargs):
            nonlocal ph_called
            ph_called = True
            return {"refreshed": False, "skipped": True, "error": None}

        with patch("scripts.license_gate.phone_home", side_effect=mock_phone_home):
            result = validate()

        assert result.valid is True
        assert ph_called is False

    def test_validate_revalidates_on_refresh(self, tmp_path):
        """When phone_home returns refreshed=True, validate re-runs with new token."""
        now = time.time()
        old_payload = {
            "sub": "acme", "plan": "pilot",
            "exp": int(now) + 86400,
        }
        old_token = _make_unsigned_jwt(old_payload)
        lic_path = tmp_path / "license.jwt"
        lic_path.write_text(old_token)

        new_payload = {
            "sub": "acme", "plan": "enterprise",
            "exp": int(now) + 86400 * 365,
        }
        new_token = _make_unsigned_jwt(new_payload)

        call_count = 0

        def mock_phone_home(**kwargs):
            nonlocal call_count
            call_count += 1
            # Write the new token to the license file (simulating server refresh)
            lic_path.write_text(new_token)
            return {"refreshed": True, "skipped": False, "error": None}

        with patch("scripts.license_gate.phone_home", side_effect=mock_phone_home), \
             patch("scripts.license_gate.PHONE_HOME_ENABLED", True):
            result = validate(
                license_path=lic_path,
                key_path=tmp_path / "no.pub",
                current_time=now,
            )

        # phone_home called once (on first validate), not on re-validate (guard)
        assert call_count == 1
        # Result should reflect the NEW token
        assert result.plan == "enterprise"
        assert result.valid is True

    def test_recursion_guard_prevents_infinite_loop(self, tmp_path):
        """The recursion guard should prevent validate->phone_home->validate loop."""
        now = time.time()
        payload = {
            "sub": "acme", "plan": "professional",
            "exp": int(now) + 86400,
        }
        token = _make_unsigned_jwt(payload)
        lic_path = tmp_path / "license.jwt"
        lic_path.write_text(token)

        call_count = 0

        def mock_phone_home(**kwargs):
            nonlocal call_count
            call_count += 1
            # Always claim refreshed to trigger re-validate
            return {"refreshed": True, "skipped": False, "error": None}

        with patch("scripts.license_gate.phone_home", side_effect=mock_phone_home), \
             patch("scripts.license_gate.PHONE_HOME_ENABLED", True):
            result = validate(
                license_path=lic_path,
                key_path=tmp_path / "no.pub",
                current_time=now,
            )

        # phone_home should be called exactly once -- the re-validate call
        # has _phone_home_refreshing=True so it skips phone_home
        assert call_count == 1
        assert result.valid is True

    def test_phone_home_disabled_via_env(self, tmp_path):
        """PHONE_HOME_ENABLED=false should skip phone-home entirely."""
        now = time.time()
        payload = {
            "sub": "acme", "plan": "enterprise",
            "exp": int(now) + 86400,
        }
        token = _make_unsigned_jwt(payload)
        lic_path = tmp_path / "license.jwt"
        lic_path.write_text(token)

        ph_called = False

        def mock_phone_home(**kwargs):
            nonlocal ph_called
            ph_called = True
            return {"refreshed": False, "skipped": True, "error": None}

        with patch("scripts.license_gate.phone_home", side_effect=mock_phone_home), \
             patch("scripts.license_gate.PHONE_HOME_ENABLED", False):
            result = validate(
                license_path=lic_path,
                key_path=tmp_path / "no.pub",
                current_time=now,
            )

        assert result.valid is True
        assert ph_called is False

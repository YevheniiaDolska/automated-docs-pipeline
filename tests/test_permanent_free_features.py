#!/usr/bin/env python3
"""Tests for permanently free feature grants and the dev-bypass guard.

Permanent free grants (`free_features` / `free_protocols` JWT claims) must:
- be enabled while the license is valid, regardless of plan restrictions;
- survive expiry past grace (community degradation);
- survive pilot trial expiry without triggering destructive asset cleanup;
- NOT survive when there is no signed license at all (no file / bad file).

The VERIOPS_LICENSE_PLAN env bypass must only be honored in the vendor repo
or when a docsops/.dev_mode marker exists (free/dev bundles).
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
BUILD_DIR = str(REPO_ROOT / "build")
if BUILD_DIR not in sys.path:
    sys.path.insert(0, BUILD_DIR)

from scripts import license_gate as lg
from scripts.license_gate import (
    COMMUNITY_FEATURES,
    _effective_features,
    _effective_protocols,
    reset_cache,
    validate,
)

try:
    from generate_license import _generate_ed25519_keypair, generate_jwt
    HAVE_CRYPTO = True
except (ImportError, RuntimeError):
    HAVE_CRYPTO = False

pytestmark = pytest.mark.skipif(not HAVE_CRYPTO, reason="No Ed25519 library available")


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    monkeypatch.delenv("VERIOPS_LICENSE_PLAN", raising=False)
    monkeypatch.delenv("VERIOPS_CLIENT_ID", raising=False)
    monkeypatch.delenv("VERIOPS_TENANT_ID", raising=False)
    monkeypatch.delenv("VERIOPS_COMPANY_DOMAIN", raising=False)
    reset_cache()
    yield
    reset_cache()


@pytest.fixture(autouse=True)
def _installed_repo_binding(tmp_path, monkeypatch):
    """Simulate a provisioned install (binding + integrity + fresh heartbeat)."""
    repo_hash = hashlib.sha256(str(lg.REPO_ROOT.resolve()).encode("utf-8")).hexdigest()

    binding_path = tmp_path / ".repo_binding.json"
    binding_path.write_text(
        json.dumps({"repo_path_hash": repo_hash, "client_id": "", "tenant_id": ""}),
        encoding="utf-8",
    )

    gate_file = lg.REPO_ROOT / "scripts" / "license_gate.py"
    manifest_path = tmp_path / ".integrity_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema": "integrity-manifest/v1",
                "repo_path_hash": repo_hash,
                "files": {
                    "scripts/license_gate.py": hashlib.sha256(gate_file.read_bytes()).hexdigest()
                },
            }
        ),
        encoding="utf-8",
    )

    heartbeat_path = tmp_path / ".license_heartbeat.json"
    heartbeat_path.write_text(
        json.dumps({"last_check": time.time(), "last_result": "success"}),
        encoding="utf-8",
    )

    monkeypatch.setattr(lg, "REPO_BINDING_PATH", binding_path)
    monkeypatch.setattr(lg, "INTEGRITY_MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(lg, "HEARTBEAT_PATH", heartbeat_path)
    yield


@pytest.fixture()
def keypair(tmp_path):
    priv, pub = _generate_ed25519_keypair()
    pub_path = tmp_path / "veriops-licensing.pub"
    pub_path.write_bytes(base64.b64encode(pub))
    return priv, pub_path


def _signed_license(tmp_path, priv, **kwargs):
    defaults = dict(
        client_id="acme-corp",
        plan="pilot",
        days=30,
        private_key=priv,
    )
    defaults.update(kwargs)
    token = generate_jwt(**defaults)
    lic_path = tmp_path / "license.jwt"
    lic_path.write_text(token, encoding="utf-8")
    return lic_path


class TestFreeGrantsWhileValid:
    def test_free_feature_enabled_beyond_plan(self, tmp_path, keypair):
        priv, pub_path = keypair
        # Pilot plan does not include drift_detection; free grant enables it.
        lic = _signed_license(
            tmp_path, priv, plan="pilot", free_features=["drift_detection"]
        )
        info = validate(license_path=lic, key_path=pub_path)
        assert info.valid is True
        assert info.plan == "pilot"
        assert info.features["drift_detection"] is True
        assert info.free_features == ["drift_detection"]

    def test_free_protocol_added(self, tmp_path, keypair):
        priv, pub_path = keypair
        lic = _signed_license(
            tmp_path, priv, plan="pilot", free_protocols=["graphql"]
        )
        info = validate(license_path=lic, key_path=pub_path)
        assert info.valid is True
        assert "graphql" in info.protocols
        assert info.free_protocols == ["graphql"]

    def test_tampered_token_is_rejected(self, tmp_path, keypair):
        priv, pub_path = keypair
        lic = _signed_license(
            tmp_path, priv, plan="pilot", free_features=["drift_detection"]
        )
        # Tamper with the payload: flip plan to enterprise.
        header_b64, payload_b64, sig_b64 = lic.read_text().strip().split(".")
        padded = payload_b64 + "=" * (4 - len(payload_b64) % 4)
        claims = json.loads(base64.urlsafe_b64decode(padded))
        claims["plan"] = "enterprise"
        forged_payload = (
            base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
        )
        lic.write_text(f"{header_b64}.{forged_payload}.{sig_b64}", encoding="utf-8")
        info = validate(license_path=lic, key_path=pub_path)
        assert info.valid is False
        assert info.plan == "community"
        # Grants from a forged token must not apply.
        assert info.free_features == []


class TestFreeGrantsSurviveExpiry:
    def test_expired_past_grace_keeps_free_features(self, tmp_path, keypair):
        priv, pub_path = keypair
        lic = _signed_license(
            tmp_path,
            priv,
            plan="professional",
            days=10,
            free_features=["seo_geo_scoring", "drift_detection"],
            free_protocols=["rest"],
        )
        # 400 days later: way past expiry + any grace.
        future = time.time() + 400 * 86400
        info = validate(license_path=lic, key_path=pub_path, current_time=future)
        assert info.valid is False
        assert info.plan == "community"
        assert info.features["seo_geo_scoring"] is True
        assert info.features["drift_detection"] is True
        assert "rest" in info.protocols
        # Paid-only features are gone.
        assert info.features.get("multi_protocol_pipeline", False) is False

    def test_expired_past_grace_without_grants_is_plain_community(self, tmp_path, keypair):
        priv, pub_path = keypair
        lic = _signed_license(tmp_path, priv, plan="professional", days=10)
        future = time.time() + 400 * 86400
        info = validate(license_path=lic, key_path=pub_path, current_time=future)
        assert info.valid is False
        assert info.features == dict(COMMUNITY_FEATURES)

    def test_missing_license_file_grants_nothing(self, tmp_path):
        info = validate(license_path=tmp_path / "nope.jwt")
        assert info.free_features == []
        assert info.features == dict(COMMUNITY_FEATURES)


class TestPilotExpiryDegradation:
    def _expired_pilot_info(self, tmp_path, keypair, **kwargs):
        priv, pub_path = keypair
        lic = _signed_license(tmp_path, priv, plan="pilot", days=5, **kwargs)
        # 6 days later: expired but within default pilot grace (3 days)?
        # 5 + 2 days: expired, inside grace -> valid=True, days_remaining=0.
        future = time.time() + 7 * 86400 - 3600
        return validate(license_path=lic, key_path=pub_path, current_time=future)

    def test_pilot_trial_expiry_keeps_free_grants(self, tmp_path, keypair):
        info = self._expired_pilot_info(
            tmp_path, keypair, free_features=["gap_detection_code"], free_protocols=["rest"]
        )
        assert info.valid is True  # still in grace
        with patch.object(lg, "_remove_paid_llm_instruction_files") as rm_files, \
             patch.object(lg, "_remove_proprietary_assets_after_expiry") as rm_assets:
            features = _effective_features(info)
            protocols = _effective_protocols(info)
            # Free grants must prevent destructive cleanup entirely.
            rm_files.assert_not_called()
            rm_assets.assert_not_called()
        assert features["gap_detection_code"] is True
        assert "rest" in protocols

    def test_pilot_trial_expiry_never_destructive_in_vendor_repo(self, tmp_path, keypair):
        info = self._expired_pilot_info(tmp_path, keypair)
        # This test runs inside the vendor repo (build/generate_license.py exists),
        # so cleanup must be skipped even without free grants.
        assert lg._is_vendor_repo() is True
        with patch.object(lg, "_remove_paid_llm_instruction_files") as rm_files, \
             patch.object(lg, "_remove_proprietary_assets_after_expiry") as rm_assets:
            _effective_features(info)
            rm_files.assert_not_called()
            rm_assets.assert_not_called()


class TestDevBypassGuard:
    def test_bypass_honored_in_vendor_repo(self, monkeypatch):
        monkeypatch.setenv("VERIOPS_LICENSE_PLAN", "enterprise")
        info = validate()
        assert info.valid is True
        assert info.plan == "enterprise"

    def test_bypass_ignored_in_client_bundle(self, tmp_path, monkeypatch):
        monkeypatch.setenv("VERIOPS_LICENSE_PLAN", "enterprise")
        with patch.object(lg, "_is_vendor_repo", return_value=False), \
             patch.object(lg, "REPO_ROOT", tmp_path):
            info = validate(license_path=tmp_path / "missing.jwt")
        assert info.valid is False
        assert info.plan == "community"

    def test_bypass_honored_with_dev_mode_marker(self, tmp_path, monkeypatch):
        monkeypatch.setenv("VERIOPS_LICENSE_PLAN", "professional")
        marker = tmp_path / "docsops" / ".dev_mode"
        marker.parent.mkdir(parents=True)
        marker.write_text("free bundle", encoding="utf-8")
        with patch.object(lg, "_is_vendor_repo", return_value=False), \
             patch.object(lg, "REPO_ROOT", tmp_path):
            info = validate()
        assert info.valid is True
        assert info.plan == "professional"


class TestGeneratorClaims:
    def test_generate_jwt_embeds_free_claims(self):
        priv, _pub = _generate_ed25519_keypair()
        token = generate_jwt(
            client_id="acme",
            plan="pilot",
            days=30,
            private_key=priv,
            free_features=["drift_detection", " drift_detection ", ""],
            free_protocols=["GraphQL"],
        )
        payload_b64 = token.split(".")[1]
        padded = payload_b64 + "=" * (4 - len(payload_b64) % 4)
        claims = json.loads(base64.urlsafe_b64decode(padded))
        assert claims["free_features"] == ["drift_detection"]
        assert claims["free_protocols"] == ["graphql"]
        # Features/protocols maps also reflect the grants immediately.
        assert claims["features"]["drift_detection"] is True
        assert "graphql" in claims["protocols"]

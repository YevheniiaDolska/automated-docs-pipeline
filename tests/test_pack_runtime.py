#!/usr/bin/env python3
"""Tests for scripts/pack_runtime.py -- encrypted capability pack loader."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.pack_runtime import (
    DEGRADED_AUDIT_WEIGHTS,
    DEGRADED_GEO_RULES,
    DEGRADED_GEO_RULES_BY_LOCALE,
    DEGRADED_GRADE_THRESHOLDS,
    DEGRADED_KPI_WEIGHTS,
    DEGRADED_RISK_WEIGHTS,
    DEGRADED_SEO_RULES,
    DEGRADED_TIER_WEIGHTS,
    PACK_FORMAT_VERSION,
    PACK_MAGIC,
    CapabilityPack,
    _degraded_pack,
    _hkdf_expand,
    _hkdf_extract,
    _parse_pack_file,
    build_pack_file,
    derive_pack_key,
    get_audit_weights,
    get_geo_rules,
    get_geo_rules_by_locale,
    get_grade_thresholds,
    get_kpi_weights,
    get_policies,
    get_prompts,
    get_risk_weights,
    get_seo_rules,
    get_tier_weights,
    load_pack,
    reset_cache,
)


@pytest.fixture(autouse=True)
def _reset_pack_cache():
    reset_cache()
    yield
    reset_cache()


# -- HKDF tests ---------------------------------------------------------------


class TestHKDF:
    def test_extract_produces_32_bytes(self):
        prk = _hkdf_extract(b"salt", b"input-key-material")
        assert len(prk) == 32

    def test_expand_produces_32_bytes(self):
        prk = _hkdf_extract(b"salt", b"ikm")
        okm = _hkdf_expand(prk, b"info", 32)
        assert len(okm) == 32

    def test_expand_different_info_different_keys(self):
        prk = _hkdf_extract(b"salt", b"ikm")
        k1 = _hkdf_expand(prk, b"client-a", 32)
        k2 = _hkdf_expand(prk, b"client-b", 32)
        assert k1 != k2

    def test_derive_pack_key_deterministic(self):
        k1 = derive_pack_key("VDOC-ENT-acme-abc123", "acme-corp")
        k2 = derive_pack_key("VDOC-ENT-acme-abc123", "acme-corp")
        assert k1 == k2
        assert len(k1) == 32

    def test_derive_pack_key_different_clients(self):
        k1 = derive_pack_key("same-key", "client-a")
        k2 = derive_pack_key("same-key", "client-b")
        assert k1 != k2

    def test_derive_pack_key_different_keys(self):
        k1 = derive_pack_key("key-1", "same-client")
        k2 = derive_pack_key("key-2", "same-client")
        assert k1 != k2


# -- Pack file format ----------------------------------------------------------


class TestPackFileFormat:
    def test_build_and_parse_roundtrip(self):
        nonce = b"\x01" * 12
        tag = b"\x02" * 16
        ciphertext = b"\x03" * 100

        packed = build_pack_file(nonce, tag, ciphertext)

        assert packed[:4] == PACK_MAGIC
        assert int.from_bytes(packed[4:6], "big") == PACK_FORMAT_VERSION

        parsed_nonce, parsed_tag, parsed_ct = _parse_pack_file(packed)
        assert parsed_nonce == nonce
        assert parsed_tag == tag
        assert parsed_ct == ciphertext

    def test_parse_too_small(self):
        with pytest.raises(ValueError, match="too small"):
            _parse_pack_file(b"\x00" * 10)

    def test_parse_invalid_magic(self):
        data = b"XXXX" + b"\x00" * 30
        with pytest.raises(ValueError, match="magic"):
            _parse_pack_file(data)

    def test_parse_invalid_version(self):
        data = PACK_MAGIC + (99).to_bytes(2, "big") + b"\x00" * 28
        with pytest.raises(ValueError, match="version"):
            _parse_pack_file(data)


# -- Degraded pack -------------------------------------------------------------


class TestDegradedPack:
    def test_defaults(self):
        pack = _degraded_pack()
        assert pack.valid is False
        assert pack.plan == "community"
        assert "scoring" in pack.sections
        assert "priority" in pack.sections

    def test_custom_error(self):
        pack = _degraded_pack("custom error")
        assert "custom error" in pack.error

    def test_degraded_geo_rules(self):
        rules = get_geo_rules(None)
        assert rules == DEGRADED_GEO_RULES
        assert rules["first_para_max_words"] == 60
        assert "definition_patterns" in rules
        assert "fact_patterns" in rules

    def test_degraded_geo_rules_by_locale_full(self):
        locales = get_geo_rules_by_locale(None)
        assert "ru" in locales
        assert "de" in locales
        assert locales["ru"]["first_para_max_words"] == 80

    def test_degraded_geo_rules_by_locale_merged(self):
        merged = get_geo_rules_by_locale(None, "ru")
        assert merged["first_para_max_words"] == 80
        # Should inherit base GEO keys not overridden
        assert "max_words_without_fact" in merged
        assert merged["max_words_without_fact"] == 200

    def test_degraded_geo_rules_by_locale_unknown(self):
        result = get_geo_rules_by_locale(None, "fr")
        assert result == DEGRADED_GEO_RULES

    def test_degraded_seo_rules(self):
        rules = get_seo_rules(None)
        assert rules == DEGRADED_SEO_RULES
        assert rules["title_max_chars"] == 70

    def test_degraded_kpi_weights(self):
        weights = get_kpi_weights(None)
        assert weights == DEGRADED_KPI_WEIGHTS
        assert weights["metadata_weight"] == 0.35
        assert weights["gap_penalty_per_item"] == 3

    def test_degraded_audit_weights(self):
        weights = get_audit_weights(None)
        assert weights == DEGRADED_AUDIT_WEIGHTS
        assert weights["api_coverage"] == 0.22
        assert weights["hallucination_deduction"] == 0.08

    def test_degraded_risk_weights(self):
        weights = get_risk_weights(None)
        assert weights == DEGRADED_RISK_WEIGHTS
        assert weights["undocumented"] == 0.30

    def test_degraded_grade_thresholds(self):
        thresholds = get_grade_thresholds(None)
        assert thresholds == DEGRADED_GRADE_THRESHOLDS
        assert thresholds["A"] == 90

    def test_degraded_tier_weights(self):
        tiers = get_tier_weights(None)
        assert tiers == DEGRADED_TIER_WEIGHTS


# -- Pack loading with encryption ----------------------------------------------


class TestPackLoadEncrypted:
    """Integration tests that require a crypto library (cryptography or pycryptodome)."""

    @pytest.fixture
    def encrypted_pack(self, tmp_path):
        """Create a valid encrypted pack file."""
        try:
            from scripts.pack_runtime import _aes_gcm_encrypt
        except RuntimeError:
            pytest.skip("No AES-GCM library available")

        license_key = "VDOC-ENT-test-abc123"
        client_id = "test-corp"
        aes_key = derive_pack_key(license_key, client_id)

        payload = {
            "plan": "enterprise",
            "version": "1.0.0",
            "created_at": time.time(),
            "expires_at": time.time() + 86400 * 90,
            "sections": {
                "scoring": {
                    "geo_rules": {"first_para_max_words": 55},
                    "geo_rules_by_locale": {"ru": {"first_para_max_words": 75}},
                    "seo_rules": {"title_max_chars": 65},
                    "kpi_weights": {"metadata_weight": 0.40, "stale_weight": 0.25,
                                    "gap_penalty_per_item": 4, "gap_penalty_cap": 30},
                    "audit_weights": {"api_coverage": 0.25, "example_reliability": 0.18,
                                      "freshness": 0.14, "drift": 0.12, "layers": 0.12,
                                      "terminology": 0.10, "retrieval": 0.09,
                                      "hallucination_deduction": 0.07},
                    "risk_weights": {"undocumented": 0.35, "stale": 0.20,
                                     "drift": 0.15, "example_gap": 0.20,
                                     "terminology": 0.10},
                    "grade_thresholds": {"A": 92, "B": 82, "C": 72, "D": 62},
                },
                "priority": {"tier1_categories": ["breaking_change"]},
                "prompts": {"stripe_quality": "test prompt"},
                "policies": {"quality_gates": {"vale_blocks_commit": True}},
            },
        }
        plaintext = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        nonce, ciphertext, tag = _aes_gcm_encrypt(aes_key, plaintext)
        pack_data = build_pack_file(nonce, tag, ciphertext)

        pack_path = tmp_path / "test.pack.enc"
        pack_path.write_bytes(pack_data)

        return pack_path, license_key, client_id

    def test_load_valid_pack(self, encrypted_pack):
        pack_path, license_key, client_id = encrypted_pack
        pack = load_pack(pack_path, license_key, client_id)

        assert pack.valid is True
        assert pack.plan == "enterprise"
        assert pack.version == "1.0.0"

    def test_load_pack_scoring(self, encrypted_pack):
        pack_path, license_key, client_id = encrypted_pack
        pack = load_pack(pack_path, license_key, client_id)

        geo = get_geo_rules(pack)
        assert geo["first_para_max_words"] == 55

        kpi = get_kpi_weights(pack)
        assert kpi["metadata_weight"] == 0.40
        assert kpi["gap_penalty_per_item"] == 4

        audit = get_audit_weights(pack)
        assert audit["api_coverage"] == 0.25

        seo = get_seo_rules(pack)
        assert seo["title_max_chars"] == 65

        risk = get_risk_weights(pack)
        assert risk["undocumented"] == 0.35

        grades = get_grade_thresholds(pack)
        assert grades["A"] == 92

    def test_load_pack_locale_overrides(self, encrypted_pack):
        pack_path, license_key, client_id = encrypted_pack
        pack = load_pack(pack_path, license_key, client_id)

        ru = get_geo_rules_by_locale(pack, "ru")
        assert ru["first_para_max_words"] == 75

        all_locales = get_geo_rules_by_locale(pack)
        assert "ru" in all_locales

    def test_load_pack_priority(self, encrypted_pack):
        pack_path, license_key, client_id = encrypted_pack
        pack = load_pack(pack_path, license_key, client_id)

        tiers = get_tier_weights(pack)
        assert "breaking_change" in tiers["tier1_categories"]

    def test_load_pack_prompts(self, encrypted_pack):
        pack_path, license_key, client_id = encrypted_pack
        pack = load_pack(pack_path, license_key, client_id)

        prompts = get_prompts(pack)
        assert "stripe_quality" in prompts

    def test_load_pack_policies(self, encrypted_pack):
        pack_path, license_key, client_id = encrypted_pack
        pack = load_pack(pack_path, license_key, client_id)

        policies = get_policies(pack)
        assert policies["quality_gates"]["vale_blocks_commit"] is True

    def test_wrong_license_key(self, encrypted_pack):
        pack_path, _, client_id = encrypted_pack
        pack = load_pack(pack_path, "wrong-key", client_id)
        assert pack.valid is False
        assert "decryption" in pack.error.lower() or "failed" in pack.error.lower()

    def test_wrong_client_id(self, encrypted_pack):
        pack_path, license_key, _ = encrypted_pack
        pack = load_pack(pack_path, license_key, "wrong-client")
        assert pack.valid is False

    def test_expired_pack(self, tmp_path):
        """Pack that has expired returns degraded defaults."""
        try:
            from scripts.pack_runtime import _aes_gcm_encrypt
        except RuntimeError:
            pytest.skip("No AES-GCM library available")

        license_key = "VDOC-ENT-expired"
        client_id = "expired-corp"
        aes_key = derive_pack_key(license_key, client_id)

        payload = {
            "plan": "enterprise",
            "version": "1.0.0",
            "created_at": time.time() - 86400 * 100,
            "expires_at": time.time() - 86400,  # Expired yesterday
            "sections": {"scoring": {}, "priority": {}, "prompts": {}, "policies": {}},
        }
        plaintext = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        nonce, ciphertext, tag = _aes_gcm_encrypt(aes_key, plaintext)
        pack_data = build_pack_file(nonce, tag, ciphertext)

        pack_path = tmp_path / "expired.pack.enc"
        pack_path.write_bytes(pack_data)

        pack = load_pack(pack_path, license_key, client_id)
        assert pack.valid is False
        assert "expired" in pack.error.lower()


class TestPackLoadEdgeCases:
    def test_missing_pack_file(self, tmp_path):
        pack = load_pack(tmp_path / "nonexistent.enc", "key", "id")
        assert pack.valid is False
        assert "not found" in pack.error.lower()

    def test_no_credentials(self, tmp_path):
        f = tmp_path / "test.enc"
        f.write_bytes(b"anything")
        pack = load_pack(f, None, None)
        assert pack.valid is False
        assert "not provided" in pack.error.lower()

    def test_corrupted_pack_file(self, tmp_path):
        f = tmp_path / "corrupt.enc"
        f.write_bytes(PACK_MAGIC + b"\x00" * 100)
        pack = load_pack(f, "key", "id")
        assert pack.valid is False

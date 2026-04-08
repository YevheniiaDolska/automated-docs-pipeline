from __future__ import annotations

from pathlib import Path

from scripts import build_client_bundle as bundle_mod
from scripts import license_gate


def test_dev_bypass_blocked_when_security_disallows(monkeypatch) -> None:
    monkeypatch.setenv("VERIOPS_LICENSE_PLAN", "enterprise")
    monkeypatch.setattr(
        license_gate,
        "_security_config",
        lambda: {"allow_dev_bypass": False, "anti_tamper_enforced": False},
    )
    info = license_gate.validate()
    assert info.valid is False
    assert info.plan == "community"


def test_dev_bypass_allowed_in_relaxed_profile(monkeypatch) -> None:
    monkeypatch.setenv("VERIOPS_LICENSE_PLAN", "enterprise")
    monkeypatch.setattr(
        license_gate,
        "_security_config",
        lambda: {"allow_dev_bypass": True, "anti_tamper_enforced": False},
    )
    info = license_gate.validate()
    assert info.valid is True
    assert info.plan == "enterprise"


def test_integrity_manifest_missing_blocks_when_enforced(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(license_gate, "MODULE_HASH_MANIFEST", tmp_path / ".module_hashes.json")
    monkeypatch.setattr(license_gate, "_anti_tamper_enforced", lambda: True)
    ok, reason = license_gate._verify_integrity_manifest()
    assert ok is False
    assert "Integrity check failed" in reason


def test_build_env_template_includes_security_defaults(tmp_path: Path) -> None:
    profile = {
        "client": {"id": "acme", "tenant_id": "acme", "company_domain": "acme.example"},
        "licensing": {"expose_license_key_env": False, "expose_dev_plan_override_env": False},
    }
    runtime_cfg = {
        "integrations": {"algolia": {"enabled": False}, "ask_ai": {"enabled": False}},
        "api_first": {"enabled": False},
        "security": {
            "phone_home_enabled_default": False,
            "update_check_enabled_default": False,
        },
    }
    bundle_mod.build_local_env_template(profile, runtime_cfg, tmp_path)
    content = (tmp_path / ".env.docsops.local.template").read_text(encoding="utf-8")
    assert "VERIOPS_PHONE_HOME_ENABLED=false" in content
    assert "VERIOPS_UPDATE_CHECK_ENABLED=false" in content
    assert "VERIOPS_TENANT_ID=acme" in content
    assert "VERIOPS_COMPANY_DOMAIN=acme.example" in content


def test_expired_license_degrades_to_community(monkeypatch, tmp_path: Path) -> None:
    token = tmp_path / "license.jwt"
    token.write_text("x.y.z", encoding="utf-8")
    monkeypatch.delenv("VERIOPS_LICENSE_PLAN", raising=False)
    monkeypatch.setattr(license_gate, "_verify_integrity_manifest", lambda: (True, ""))
    monkeypatch.setattr(license_gate, "_parse_jwt_parts", lambda _: ({}, {"sub": "acme", "plan": "professional", "exp": 1}, b""))
    monkeypatch.setattr(license_gate, "_load_public_key", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(license_gate, "check_revocation", lambda **_kwargs: (False, ""))
    monkeypatch.setattr(license_gate, "_security_config", lambda: {"allow_dev_bypass": False, "anti_tamper_enforced": False})
    info = license_gate.validate(license_path=token, current_time=10_000_000.0)
    assert info.valid is False
    assert info.plan == "community"
    assert "expired" in info.error.lower()


def test_tenant_and_domain_binding_mismatch_degrades(monkeypatch, tmp_path: Path) -> None:
    token = tmp_path / "license.jwt"
    token.write_text("x.y.z", encoding="utf-8")
    monkeypatch.delenv("VERIOPS_LICENSE_PLAN", raising=False)
    monkeypatch.setenv("VERIOPS_TENANT_ID", "tenant-b")
    monkeypatch.setenv("VERIOPS_COMPANY_DOMAIN", "other.example")
    monkeypatch.setattr(license_gate, "_verify_integrity_manifest", lambda: (True, ""))
    monkeypatch.setattr(
        license_gate,
        "_parse_jwt_parts",
        lambda _: ({}, {"sub": "acme", "plan": "professional", "exp": 4102444800, "tenant_id": "tenant-a", "company_domain": "acme.example"}, b""),
    )
    monkeypatch.setattr(license_gate, "_load_public_key", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(license_gate, "_security_config", lambda: {"allow_dev_bypass": False, "anti_tamper_enforced": False})
    info = license_gate.validate(license_path=token, current_time=1_700_000_000.0)
    assert info.valid is False
    assert info.plan == "community"
    assert "binding mismatch" in info.error.lower()


def test_missing_capability_pack_degrades_premium_features(monkeypatch, tmp_path: Path) -> None:
    token = tmp_path / "license.jwt"
    token.write_text("x.y.z", encoding="utf-8")
    monkeypatch.delenv("VERIOPS_LICENSE_PLAN", raising=False)
    monkeypatch.setattr(license_gate, "_verify_integrity_manifest", lambda: (True, ""))
    monkeypatch.setattr(
        license_gate,
        "_parse_jwt_parts",
        lambda _: ({}, {"sub": "acme", "plan": "enterprise", "exp": 4102444800}, b""),
    )
    monkeypatch.setattr(license_gate, "_load_public_key", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(license_gate, "check_revocation", lambda **_kwargs: (False, ""))
    monkeypatch.setattr(
        license_gate,
        "_security_config",
        lambda: {"allow_dev_bypass": False, "anti_tamper_enforced": False, "require_pack_for_premium": True},
    )

    class _Pack:
        valid = False
        error = "missing"

    monkeypatch.setattr("scripts.pack_runtime.load_pack", lambda **_kwargs: _Pack())

    info = license_gate.validate(license_path=token, current_time=1_700_000_000.0)
    assert info.valid is True
    assert info.plan == "enterprise"
    assert info.features.get("multi_protocol_pipeline") is False
    assert "capability pack" in info.error.lower()

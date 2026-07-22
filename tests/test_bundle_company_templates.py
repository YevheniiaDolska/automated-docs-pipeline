"""Tests for the company-templates bundle hook (no LLM/network calls)."""

from __future__ import annotations

from pathlib import Path

from scripts import build_client_bundle as mod


def test_disabled_is_noop(tmp_path: Path) -> None:
    profile = {"bundle": {"company_templates": {"enabled": False}}, "client": {"company_name": "ACME"}}
    mod.build_company_templates(profile, tmp_path)
    # Nothing shipped when the feature is off.
    assert not (tmp_path / "scripts").exists()


def test_enabled_ships_toolchain_without_generating(tmp_path: Path, monkeypatch) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: calls.append(a[0]))
    profile = {
        "bundle": {"company_templates": {"enabled": True, "generate_on_build": False}},
        "client": {"company_name": "ACME"},
    }
    mod.build_company_templates(profile, tmp_path)
    # Assembly scripts are shipped...
    assert (tmp_path / "scripts" / "generate_doc_from_spec.py").exists()
    assert (tmp_path / "scripts" / "generate_company_templates.py").exists()
    assert (tmp_path / "snippets").exists()
    # ...but no LLM/research subprocess ran.
    assert calls == []


def test_generate_on_build_invokes_pipeline(tmp_path: Path, monkeypatch) -> None:
    calls: list[list[str]] = []

    class _R:
        returncode = 0

    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: calls.append(a[0]) or _R())
    profile = {
        "bundle": {"company_templates": {"enabled": True, "generate_on_build": True, "web_research": True}},
        "client": {"company_name": "ACME", "company_domain": "acme.com"},
        "runtime": {"api_protocols": ["rest", "graphql"]},
    }
    mod.build_company_templates(profile, tmp_path)
    joined = [" ".join(c) for c in calls]
    assert any("web_research.py" in j for j in joined)
    assert any("generate_company_templates.py" in j for j in joined)
    assert any("--api-protocols rest,graphql" in j for j in joined)

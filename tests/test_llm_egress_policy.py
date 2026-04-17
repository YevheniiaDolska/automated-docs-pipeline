from __future__ import annotations

from pathlib import Path

import pytest

from scripts import llm_egress as mod


def test_external_allowed_without_explicit_approval(tmp_path: Path) -> None:
    policy = mod.LLMEgressPolicy(
        llm_mode="external_preferred",
        external_llm_allowed=True,
        require_explicit_approval=False,
    )
    allowed = mod.ensure_external_allowed(
        policy=policy,
        step="unit-test",
        reports_dir=tmp_path,
        non_interactive=True,
    )
    assert allowed is True


def test_metadata_allowlist_accepts_run_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = tmp_path / "config" / "ip_protection"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "egress_allowlist.yml").write_text(
        "version: 1\n"
        "allowed_fields:\n"
        "  - tenant_id\n"
        "  - event\n"
        "  - timestamp_utc\n"
        "  - run_status\n"
        "blocked_key_patterns:\n"
        "  - content\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    payload = {
        "tenant_id": "t1",
        "event": "weekly",
        "timestamp_utc": "2026-04-17T00:00:00Z",
        "run_status": "ok",
    }
    out = mod.enforce_metadata_egress_payload(
        payload=payload,
        reports_dir=tmp_path / "reports",
        step="unit-test",
        source="tests",
    )
    assert out["run_status"] == "ok"


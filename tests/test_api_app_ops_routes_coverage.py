from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from typing import Any

import pytest
from fastapi import HTTPException


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "packages" / "core"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))


class _FakeQuery:
    def __init__(self, data: list[Any]) -> None:
        self._data = data

    def filter(self, *args: Any, **kwargs: Any) -> "_FakeQuery":
        return self

    def order_by(self, *args: Any, **kwargs: Any) -> "_FakeQuery":
        return self

    def offset(self, _value: int) -> "_FakeQuery":
        return self

    def limit(self, value: int) -> "_FakeQuery":
        self._data = self._data[:value]
        return self

    def first(self) -> Any:
        return self._data[0] if self._data else None

    def all(self) -> list[Any]:
        return list(self._data)


class _FakeDB:
    def __init__(self) -> None:
        self.storage: dict[str, list[Any]] = {"settings": [], "audit": []}

    def query(self, model: Any) -> _FakeQuery:
        name = getattr(model, "__name__", str(model))
        if name in {"PipelineSettings", "_PipelineSettings"}:
            return _FakeQuery(self.storage["settings"])
        if name == "AuditLog":
            return _FakeQuery(self.storage["audit"])
        return _FakeQuery([])

    def add(self, obj: Any) -> None:
        if hasattr(obj, "flow_mode"):
            self.storage["settings"].append(obj)
        elif hasattr(obj, "action"):
            self.storage["audit"].append(obj)

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None


class _FakeRequest:
    def __init__(self, payload: dict[str, Any] | None = None, headers: dict[str, str] | None = None, raw: bytes | None = None) -> None:
        self._payload = payload or {}
        self.headers = headers or {}
        self._raw = raw if raw is not None else json.dumps(self._payload).encode("utf-8")

    async def json(self) -> dict[str, Any]:
        return self._payload

    async def body(self) -> bytes:
        return self._raw


@pytest.mark.asyncio
async def test_app_ops_and_legacy_routes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from gitspeak_core.api import app as app_mod
    import gitspeak_core.api.billing as billing_mod
    import gitspeak_core.db.models as models_mod

    db = _FakeDB()

    class _PipelineSettings:
        user_id = "user_id"

        def __init__(self, user_id: str) -> None:
            self.user_id = user_id
            self.flow_mode = "code-first"
            self.default_protocols = ["rest"]
            self.modules = {}
            self.algolia_enabled = False
            self.sandbox_backend = "prism"

    monkeypatch.setattr(models_mod, "PipelineSettings", _PipelineSettings)

    # RAG route delegates.
    monkeypatch.setattr(billing_mod, "check_quota", lambda *_a, **_k: True)
    import gitspeak_core.api.rag_runtime as rag_mod

    monkeypatch.setattr(rag_mod, "load_ask_ai_config", lambda *_a, **_k: {"enabled": True, "allowed_roles": [], "require_user_auth": False})
    monkeypatch.setattr(rag_mod, "infer_user_roles", lambda user: {"owner"})
    monkeypatch.setattr(rag_mod, "load_retrieval_index", lambda *_a, **_k: [{"title": "Doc"}])
    monkeypatch.setattr(rag_mod, "search_retrieval_index", lambda **kwargs: ([{"title": "Doc"}], 0))
    monkeypatch.setattr(rag_mod, "append_rag_query_metric", lambda **kwargs: None)
    monkeypatch.setattr(rag_mod, "load_rag_metrics_snapshot", lambda **kwargs: {"latency_ms": 10})
    monkeypatch.setattr(rag_mod, "evaluate_rag_alerts", lambda **kwargs: [])
    monkeypatch.setattr(rag_mod, "resolve_embeddings_provider", lambda provider: provider or "openai")
    monkeypatch.setattr(rag_mod, "run_reindex_lifecycle", lambda **kwargs: {"status": "ok"})

    user = {"user_id": "u1", "tier": "enterprise"}
    out = await app_mod.rag_query(app_mod.RagQueryRequest(query="docs", top_k=3), user=user, db=db)
    assert out["status"] == "ok"
    assert isinstance(out["hits"], list)
    out_runtime = await app_mod.rag_runtime_query(app_mod.RagQueryRequest(query="docs"), user=user, db=db)
    assert out_runtime["status"] == "ok"
    assert "snapshot" in await app_mod.rag_metrics()
    assert "alerts" in await app_mod.rag_alerts()
    assert (await app_mod.rag_reindex(app_mod.RagReindexRequest(), user=user))["status"] == "ok"

    # Billing routes.
    monkeypatch.setattr(billing_mod, "handle_get_server_license_status", lambda *_a, **_k: types.SimpleNamespace(model_dump=lambda: {"enabled": True}))
    monkeypatch.setattr(billing_mod, "handle_get_server_license_token", lambda *_a, **_k: types.SimpleNamespace(model_dump=lambda: {"has_license": True}))
    monkeypatch.setattr(billing_mod, "handle_get_referral_summary", lambda *_a, **_k: types.SimpleNamespace(model_dump=lambda: {"policy": {}}))
    monkeypatch.setattr(billing_mod, "handle_update_referral_settings", lambda *_a, **_k: types.SimpleNamespace(model_dump=lambda: {"profile": {}}))
    monkeypatch.setattr(billing_mod, "process_recurring_referral_payouts", lambda *_a, **_k: {"status": "ok"})
    monkeypatch.setattr(billing_mod, "handle_create_invoice_request", lambda *_a, **_k: types.SimpleNamespace(model_dump=lambda: {"id": "1", "status": "pending"}))
    monkeypatch.setattr(billing_mod, "handle_create_audit_request", lambda *_a, **_k: types.SimpleNamespace(model_dump=lambda: {"id": "2", "status": "pending"}))
    import gitspeak_core.config.pricing as pricing_mod
    monkeypatch.setattr(pricing_mod, "get_pricing_data", lambda: {"plans": []})
    monkeypatch.setattr(billing_mod, "verify_manual_billing_webhook_signature", lambda *_a, **_k: True)
    monkeypatch.setattr(billing_mod, "handle_manual_billing_webhook", lambda *_a, **_k: {"ok": True})
    monkeypatch.setattr(billing_mod, "handle_manual_subscription_upsert", lambda *_a, **_k: {"status": "ok"})
    monkeypatch.setattr(billing_mod, "run_license_autorenew_batch", lambda *_a, **_k: {"scanned": 1, "refreshed": 1, "degraded": 0, "errors": 0})

    assert (await app_mod.get_billing_license_status(user={"user_id": "u1"}, db=db))["enabled"] is True
    assert (await app_mod.get_billing_license_token(user={"user_id": "u1"}, db=db))["has_license"] is True
    assert "policy" in (await app_mod.get_referral_summary(user={"user_id": "u1"}, db=db))
    assert "profile" in (await app_mod.update_referral_settings(_FakeRequest({"badge_opt_out": False}), user={"user_id": "u1"}, db=db))
    assert (await app_mod.run_referral_payouts(user={"tier": "business"}, db=db))["status"] == "ok"
    assert "id" in (await app_mod.create_invoice_request(_FakeRequest({"full_name": "A", "email": "a@x.io", "plan_tier": "business", "billing_period": "monthly"}), user={"user_id": "u1"}, db=db))
    assert "id" in (await app_mod.create_audit_request(_FakeRequest({"full_name": "A", "email": "a@x.io"}), db=db))
    assert "plans" in (await app_mod.get_plans())

    # Manual webhook and ops upsert.
    manual_ok = await app_mod.manual_billing_webhook(_FakeRequest({"event_name": "invoice_paid", "data": {"x": 1}}, headers={"x-manual-signature": "s"}), db=db)
    assert manual_ok["ok"] is True
    assert (await app_mod.ops_manual_subscription_upsert(app_mod.ManualSubscriptionUpsertRequest(user_id="u1", tier="pro"), db=db))["status"] == "ok"
    renew = await app_mod.ops_run_license_renew_batch(app_mod.LicenseRenewBatchRequest(dry_run=False), db=db, _auth=None)
    assert renew["status"] == "ok"
    assert renew["result"]["refreshed"] == 1

    # Pack registry + telemetry.
    monkeypatch.setattr(app_mod, "PACK_REGISTRY_REQUIRE_SIGNATURE", False)
    monkeypatch.setattr(app_mod, "PACK_REGISTRY_DIR", tmp_path / "packs")
    blob = (json.dumps({"x": 1}) + ("A" * 64)).encode("utf-8")
    publish = await app_mod.publish_pack(
        app_mod.PackPublishRequest(
            pack_name="core",
            version="1.0.0",
            checksum_sha256=__import__("hashlib").sha256(blob).hexdigest(),
            encrypted_blob_b64=__import__("base64").b64encode(blob).decode("ascii"),
            signature_b64=__import__("base64").b64encode(b"signature-bytes-1234567890").decode("ascii"),
        )
    )
    assert publish["status"] == "ok"
    fetched = await app_mod.fetch_pack(pack_name="core", version="1.0.0")
    assert fetched["pack_name"] == "core"
    listed = await app_mod.ops_pack_registry_list()
    assert listed["status"] == "ok"
    deleted = await app_mod.ops_pack_registry_delete(pack_name="core", version="1.0.0")
    assert deleted["deleted_files"] >= 1

    monkeypatch.setattr(app_mod, "TELEMETRY_DIR", tmp_path / "telemetry")
    monkeypatch.setattr(app_mod, "_validate_metadata_payload", lambda payload: (True, "ok"))
    telemetry = await app_mod.ingest_metadata_telemetry(app_mod.MetadataTelemetryRequest(tenant_id="t1", build_id="b1"), db=db)
    assert telemetry["status"] == "ok"
    recent = await app_mod.ops_telemetry_recent(limit=10)
    assert recent["status"] == "ok"

    # Revocation flow.
    monkeypatch.setattr(app_mod, "REVOCATION_LIST_PATH", tmp_path / "revoked.json")
    assert (await app_mod.revocation_check(tenant_id="t-x"))["revoked"] is False
    up = await app_mod.ops_revocation_upsert(app_mod.RevocationUpsertRequest(tenant_id="tenant-1", reason="manual"))
    assert up["revoked"] is True
    listed_rev = await app_mod.ops_revocation_list()
    assert "tenant-1" in listed_rev["revoked_tenants"]
    removed = await app_mod.ops_revocation_delete("tenant-1")
    assert removed["removed"] is True

    # Legacy wrappers.
    async def _fake_get_pipeline_settings(**kwargs: Any) -> dict[str, Any]:
        return {"flow_mode": "hybrid"}

    async def _fake_list_schedules(**kwargs: Any) -> dict[str, Any]:
        return {"schedules": [{"id": "sch-1"}]}

    monkeypatch.setattr(app_mod, "get_pipeline_settings", _fake_get_pipeline_settings)
    monkeypatch.setattr(app_mod, "list_schedules", _fake_list_schedules)
    dashboard = await app_mod.legacy_dashboard(user={"user_id": "u1", "tier": "pro"})
    assert dashboard["status"] == "ok"
    assert "settings" in (await app_mod.legacy_settings_get(user={"user_id": "u1"}, db=db))
    assert "settings" in (await app_mod.legacy_settings_put(_FakeRequest({"flow_mode": "hybrid"}), user={"user_id": "u1"}, db=db))
    assert "schedule_count" in (await app_mod.legacy_automation_status(user={"user_id": "u1", "tier": "pro"}, db=db))


@pytest.mark.asyncio
async def test_app_error_branches(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from gitspeak_core.api import app as app_mod

    # Invalid manual webhook signature.
    monkeypatch.setattr("gitspeak_core.api.billing.verify_manual_billing_webhook_signature", lambda *_a, **_k: False)
    with pytest.raises(HTTPException):
        await app_mod.manual_billing_webhook(_FakeRequest({"event_name": "x"}, headers={"x-manual-signature": "bad"}), db=_FakeDB())

    # Invalid revocation payload.
    monkeypatch.setattr(app_mod, "_validate_metadata_payload", lambda payload: (False, "bad_field"))
    with pytest.raises(HTTPException):
        await app_mod.revocation_check(tenant_id="bad")

    # Pack fetch not found.
    monkeypatch.setattr(app_mod, "PACK_REGISTRY_DIR", tmp_path / "missing-pack")
    with pytest.raises(HTTPException):
        await app_mod.fetch_pack(pack_name="x", version="y")

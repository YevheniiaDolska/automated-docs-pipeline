from __future__ import annotations

import asyncio
import io
import json
import sys
import types
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "packages" / "core"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))


class _MD:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def model_dump(self) -> dict[str, Any]:
        return self._payload


class _FakeRequest:
    def __init__(self, payload: dict[str, Any] | None = None, raw: bytes | None = None, headers: dict[str, str] | None = None) -> None:
        self._payload = payload or {}
        self._raw = raw if raw is not None else json.dumps(self._payload).encode("utf-8")
        self.headers = headers or {}

    async def json(self) -> dict[str, Any]:
        return self._payload

    async def body(self) -> bytes:
        return self._raw


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
        self.runs: list[Any] = []
        self.schedules: list[Any] = []
        self.users: list[Any] = []
        self.audit_entries: list[Any] = []

    def query(self, model: Any) -> _FakeQuery:
        name = getattr(model, "__name__", str(model))
        if name in {"PipelineRun", "_Run"}:
            return _FakeQuery(self.runs)
        if name in {"AutomationSchedule", "_Schedule"}:
            return _FakeQuery(self.schedules)
        if name == "User":
            return _FakeQuery(self.users)
        if name == "AuditLog":
            return _FakeQuery(self.audit_entries)
        return _FakeQuery([])

    def add(self, obj: Any) -> None:
        if hasattr(obj, "trigger"):
            if not getattr(obj, "id", ""):
                obj.id = "run-created"
            self.runs.append(obj)
        elif hasattr(obj, "cron_expr"):
            if not getattr(obj, "id", ""):
                obj.id = "sch-created"
            self.schedules.append(obj)
        elif hasattr(obj, "action"):
            self.audit_entries.append(obj)

    def delete(self, obj: Any) -> None:
        if obj in self.schedules:
            self.schedules.remove(obj)

    def execute(self, _stmt: Any) -> int:
        return 1

    def commit(self) -> None:
        return None

    def refresh(self, obj: Any) -> None:
        if not getattr(obj, "id", ""):
            obj.id = "refreshed-id"

    def flush(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_api_app_core_routes_and_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    from gitspeak_core.api import app as app_mod
    import gitspeak_core.api.auth as auth_mod
    import gitspeak_core.api.billing as billing_mod

    db = _FakeDB()

    async def _call_next(_request: Any) -> Any:
        return types.SimpleNamespace(status_code=200)

    req = types.SimpleNamespace(method="GET", url=types.SimpleNamespace(path="/x"))
    response = await app_mod.log_requests(req, _call_next)
    assert response.status_code == 200

    assert (await app_mod.health_check())["status"] == "healthy"
    assert (await app_mod.readiness_check(db=db))["status"] == "ready"

    class _BadDB(_FakeDB):
        def execute(self, _stmt: Any) -> int:
            raise RuntimeError("db down")

    not_ready = await app_mod.readiness_check(db=_BadDB())
    assert getattr(not_ready, "status_code", 0) == 503

    monkeypatch.setattr(auth_mod, "handle_register", lambda req, _db: _MD({"ok": True, "email": req.email}))
    monkeypatch.setattr(auth_mod, "handle_login", lambda req, _db: _MD({"access_token": "token"}))
    monkeypatch.setattr(auth_mod, "handle_get_profile", lambda _uid, _db: _MD({"id": "u1", "email": "u@x.io"}))

    reg = await app_mod.register_user(_FakeRequest({"email": "u@x.io", "password": "12345678"}), db=db)
    assert reg["ok"] is True

    login = await app_mod.login_user(_FakeRequest({"email": "u@x.io", "password": "12345678"}), db=db)
    assert "access_token" in login

    me = await app_mod.get_me(user={"user_id": "u1"}, db=db)
    assert me["id"] == "u1"

    monkeypatch.setattr(billing_mod, "check_quota", lambda *_args, **_kwargs: True)

    class _Run:
        id = "id"
        user_id = "user_id"
        created_at = types.SimpleNamespace(desc=lambda: 0)

        def __init__(self, **kwargs: Any) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)
            self.id = "run-1"
            self.celery_task_id = None
            self.phases = []
            self.artifacts = []
            self.errors = []
            self.report = {}
            self.completed_at = None
            self.duration_seconds = 0.0
            self.quality_score = 0.0
            self.created_at = None
            self.started_at = None

    class _Schedule:
        id = "id"
        user_id = "user_id"

        def __init__(self, **kwargs: Any) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)
            self.id = "sch-1"
            self.enabled = True
            self.last_run_at = None
            self.next_run_at = None

    import gitspeak_core.db.models as models_mod

    monkeypatch.setattr(models_mod, "PipelineRun", _Run)
    monkeypatch.setattr(models_mod, "AutomationSchedule", _Schedule)

    from gitspeak_core.tasks import pipeline_tasks as task_mod

    task_mod.run_pipeline_async.delay = lambda **_kwargs: types.SimpleNamespace(id="cel-1")

    started = await app_mod.start_pipeline_run(
        app_mod.PipelineRunRequest(repo_path="/repo", flow_mode="code-first"),
        user={"user_id": "u1", "tier": "free"},
        db=db,
    )
    assert started["run_id"] == "run-1"

    listed = await app_mod.list_pipeline_runs(user={"user_id": "u1"}, db=db)
    assert isinstance(listed["runs"], list)

    got = await app_mod.get_pipeline_run("run-1", user={"user_id": "u1"}, db=db)
    assert got["id"] == "run-1"

    settings_default = await app_mod.get_pipeline_settings(user={"user_id": "u1"}, db=db)
    assert settings_default["flow_mode"] == "code-first"

    updated = await app_mod.update_pipeline_settings(
        _FakeRequest({"flow_mode": "hybrid", "modules": {"gap_detection": True}}),
        user={"user_id": "u1", "tier": "enterprise"},
        db=db,
    )
    assert updated["status"] == "ok"

    modules = await app_mod.list_modules(user={"tier": "free"})
    assert "modules" in modules

    created = await app_mod.create_schedule(
        app_mod.CreateScheduleRequest(name="nightly", cron_expr="0 3 * * *", pipeline_config={"repo_path": "/repo"}),
        user={"user_id": "u1", "tier": "pro"},
        db=db,
    )
    assert created["id"] == "sch-1"

    schedules = await app_mod.list_schedules(user={"user_id": "u1"}, db=db)
    assert len(schedules["schedules"]) >= 1

    upd = await app_mod.update_schedule("sch-1", _FakeRequest({"enabled": False}), user={"user_id": "u1"}, db=db)
    assert upd["status"] == "ok"

    deleted = await app_mod.delete_schedule("sch-1", user={"user_id": "u1"}, db=db)
    assert deleted["status"] == "ok"

    monkeypatch.setattr(billing_mod, "handle_create_checkout", lambda *_a, **_k: _MD({"checkout_url": "https://c"}))
    monkeypatch.setattr(billing_mod, "handle_get_portal_url", lambda *_a, **_k: _MD({"portal_url": "https://p"}))
    monkeypatch.setattr(billing_mod, "handle_get_usage", lambda *_a, **_k: _MD({"tier": "free"}))
    monkeypatch.setattr(billing_mod, "verify_webhook_signature", lambda *_a, **_k: True)
    monkeypatch.setattr(billing_mod, "handle_webhook", lambda *_a, **_k: {"ok": True})

    checkout = await app_mod.create_checkout(_FakeRequest({"tier": "starter", "annual": False}), user={"user_id": "u1", "email": "u@x.io"}, db=db)
    assert "checkout_url" in checkout

    portal = await app_mod.get_portal(user={"user_id": "u1"}, db=db)
    assert "portal_url" in portal

    usage = await app_mod.get_usage(user={"user_id": "u1"}, db=db)
    assert usage["tier"] == "free"

    webhook = await app_mod.lemonsqueezy_webhook(
        _FakeRequest({"meta": {"event_name": "subscription_updated"}, "data": {}}),
        db=db,
    )
    assert webhook["ok"] is True

    app_mod.log_audit(db, user_id="u1", action="pipeline.run", details={"a": 1})
    audit = await app_mod.get_audit_log(user={"user_id": "u1"}, db=db)
    assert isinstance(audit["entries"], list)


def test_doc_worker_validations_and_main_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    from gitspeak_core.docs import doc_worker as worker

    bad = worker._validate_frontmatter("# Title")
    assert bad["valid"] is False

    content = """---\ntitle: \"T\"\ndescription: \"short\"\ncontent_type: how-to\n---\n\n# T\n\nThis paragraph lacks keyword patterns.\n"""
    fp = worker._validate_first_paragraph(content)
    assert isinstance(fp["warnings"], list)

    structure = worker._validate_markdown_structure("---\ntitle: t\ndescription: x\ncontent_type: how-to\n---\n\n# A\n# B\n")
    assert structure["valid"] is False

    checks = worker._run_self_checks(content)
    assert "score" in checks

    generated = worker._generate_document({"description": "desc", "output_format": {"title": "Doc", "description": "d" * 60, "content_type": "how-to"}})
    assert "content" in generated

    executed = worker.handle_execute({"task_id": "t1", "full_context": {"description": "desc", "output_format": {"title": "Doc", "description": "d" * 60, "content_type": "how-to"}}})
    assert executed["task_id"] == "t1"

    out = io.StringIO()
    monkeypatch.setattr(worker.sys, "stdin", io.StringIO(""))
    monkeypatch.setattr(worker.sys, "stdout", out)
    worker.main()
    assert json.loads(out.getvalue())["status"] == "failure"

    out2 = io.StringIO()
    monkeypatch.setattr(worker.sys, "stdin", io.StringIO("not-json"))
    monkeypatch.setattr(worker.sys, "stdout", out2)
    worker.main()
    assert "Invalid JSON" in json.loads(out2.getvalue())["self_check"]["error"]


def test_pattern_store_crud(tmp_path: Path) -> None:
    from gitspeak_core.learning.pattern_store import DocPatternStore

    store = DocPatternStore(tmp_path / "patterns.sqlite3")
    p1 = store.add_pattern("code-1", "ctx-1", category="template", score=91.0, metadata={"x": 1})
    p2 = store.add_pattern("code-2", "ctx-2", category="template", score=80.0)
    assert p1.pattern_id > 0 and p2.pattern_id > 0

    top = store.get_top_patterns(category="template", limit=2, min_score=85.0)
    assert len(top) == 1
    assert top[0].metadata["x"] == 1

    anti = store.add_antipattern("bad", "ctx-bad", category="template", error_messages=["e1"])
    assert anti.antipattern_id > 0

    anti_list = store.get_antipatterns(category="template", limit=2)
    assert anti_list[0].error_messages == ["e1"]

    baseline = store.get_evolution_baseline(category="template")
    assert baseline is not None


@pytest.mark.asyncio
async def test_orchestrator_plan_and_retry_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from gitspeak_core.docs.orchestrator import DocOrchestrator

    orchestrator = DocOrchestrator(plan_dir=tmp_path / "plans", pattern_store=None, max_retries=1)

    report = {
        "health_summary": {"quality_score": 72.0, "drift_status": "drift", "sla_status": "breach"},
        "action_items": [
            {
                "id": "A1",
                "source_report": "drift",
                "title": "Fix API",
                "category": "api_endpoint",
                "frequency": 4,
                "action_required": "Do it",
                "related_files": ["a.md"],
                "suggested_doc_type": "how-to",
            }
        ],
    }

    items = orchestrator.classify_action_items(report)
    assert items[0].tier == 1

    plan = orchestrator.create_plan(report, items)
    path = orchestrator.save_plan(plan)
    assert path.exists()
    loaded = orchestrator.load_plan()
    assert loaded is not None and loaded["plan_id"] == plan["plan_id"]

    calls = {"n": 0}

    async def _exec(_task: dict[str, Any]) -> dict[str, Any]:
        calls["n"] += 1
        if calls["n"] == 1:
            return {"status": "failure", "self_check": {"error": "boom"}}
        return {"status": "success", "self_check": {"score": 90.0}, "code": "# ok", "test_results": {"template_id": "how_to"}}

    monkeypatch.setattr(orchestrator, "execute_task", _exec)
    task = plan["tasks"][0]
    res = await orchestrator.execute_task_with_retries(task)
    assert res["status"] == "success"

    async def _exec_success(task_: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "success",
            "self_check": {"score": 88.0},
            "code": "doc",
            "test_results": {"template_id": "t"},
            "task_id": task_["task_id"],
        }

    monkeypatch.setattr(orchestrator, "execute_task_with_retries", _exec_success)

    report_path = tmp_path / "consolidated_report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    summary = await orchestrator.process_consolidated_report(report_path)
    assert summary.total_action_items == 1
    assert summary.tier_1_processed == 1


def test_llm_provider_and_executor_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from gitspeak_core.docs.llm_executor import GSDDocExecutor, LLMProvider, LLMResponse

    provider = LLMProvider(groq_api_key="k", preference=["groq"])
    assert provider.get_active_provider() == "groq"

    class _Resp:
        def __init__(self, payload: dict[str, Any]) -> None:
            self._payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return self._payload

    monkeypatch.setattr(
        "gitspeak_core.docs.llm_executor.httpx.post",
        lambda *a, **k: _Resp({"choices": [{"message": {"content": "ok"}}], "usage": {"prompt_tokens": 1, "completion_tokens": 2}, "model": "m"}),
    )
    groq = provider.generate("hello", provider="groq")
    assert groq.content == "ok"

    monkeypatch.setattr(provider, "generate", lambda *a, **k: LLMResponse(provider="groq", content='{"score": 90, "issues": []}', prompt_tokens=1, completion_tokens=1))
    exec_ = GSDDocExecutor(llm=provider, repo_root=tmp_path)

    task = {
        "task_id": "t-1",
        "full_context": {
            "description": "Generate doc",
            "output_format": {"content_type": "how-to", "title": "Title", "description": "desc"},
            "dependencies": [],
            "patterns_to_follow": [],
        },
    }

    result = exec_.execute_task(task)
    assert result.status == "success"
    assert result.self_check_score >= 80


@pytest.mark.asyncio
async def test_pipeline_tasks_run_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    from gitspeak_core.tasks import pipeline_tasks as task_mod

    db = _FakeDB()

    run = types.SimpleNamespace(
        id="run-1",
        status="pending",
        started_at=None,
        celery_task_id=None,
        phases=[],
        artifacts=[],
        errors=[],
        report={},
        duration_seconds=0.0,
        completed_at=None,
    )
    db.runs = [run]

    import gitspeak_core.db.engine as engine_mod
    import gitspeak_core.db.models as models_mod
    import gitspeak_core.api.pipeline as pipeline_mod
    import gitspeak_core.api.billing as billing_mod

    monkeypatch.setattr(engine_mod, "get_session", lambda: db)
    monkeypatch.setattr(models_mod, "PipelineRun", type("PipelineRun", (), {"id": "id"}))

    class _Phase:
        def model_dump(self) -> dict[str, Any]:
            return {"name": "phase"}

    monkeypatch.setattr(
        pipeline_mod,
        "handle_run_pipeline",
        lambda *a, **k: types.SimpleNamespace(status="ok", phases=[_Phase()], artifacts=["a"], errors=[], report={"docs_generated": 2}),
    )

    counters: list[tuple[str, int]] = []

    def _inc(_user_id: str, metric: str, amount: int, _session: Any) -> None:
        counters.append((metric, amount))

    monkeypatch.setattr(billing_mod, "increment_usage", _inc)

    out = task_mod.run_pipeline_async.__wrapped__(
        user_id="u1",
        run_id="run-1",
        repo_path="/repo",
        user_tier="starter",
    )
    assert out["status"] == "ok"
    assert ("api_calls", 1) in counters

    monkeypatch.setattr(models_mod, "PipelineRun", type("PipelineRun", (), {"id": "id"}))
    monkeypatch.setattr(
        "gitspeak_core.docs.orchestrator.DocOrchestrator",
        lambda **kwargs: types.SimpleNamespace(
            load_report=lambda: None,
            create_plan=lambda: {"tasks": [1, 2]},
            execute_plan=lambda _plan: types.SimpleNamespace(total_tasks=2, succeeded=2, failed=0, docs_generated=2),
        ),
    )

    llm_out = task_mod.run_llm_generation.__wrapped__(
        user_id="u1",
        run_id="run-1",
        repo_path="/repo",
        consolidated_report_path="/tmp/report.json",
    )
    assert llm_out["tasks"] == 2

    user = types.SimpleNamespace(id="u1", is_active=True, subscription=types.SimpleNamespace(tier="starter"))
    schedule = types.SimpleNamespace(id="s1", user_id="u1", enabled=True, next_run_at=task_mod.datetime.now(task_mod.timezone.utc), cron_expr="* * * * *", pipeline_config={"repo_path": "/repo"}, last_run_at=None)
    db.users = [user]
    db.schedules = [schedule]

    class _Expr:
        def is_(self, _value: Any) -> "_Expr":
            return self

        def __le__(self, _other: Any) -> "_Expr":
            return self

    monkeypatch.setattr(
        models_mod,
        "AutomationSchedule",
        type("AutomationSchedule", (), {"enabled": _Expr(), "next_run_at": _Expr(), "user_id": "uid"}),
    )
    monkeypatch.setattr(models_mod, "User", type("User", (), {"id": "id"}))
    monkeypatch.setattr(models_mod, "PipelineRun", lambda **kwargs: types.SimpleNamespace(id="new-run", **kwargs))
    monkeypatch.setattr(billing_mod, "check_quota", lambda *_a, **_k: True)
    task_mod.run_pipeline_async.delay = lambda **_kwargs: None

    sched = task_mod.check_scheduled_runs.run()
    assert "triggered" in sched

    next_run = task_mod._calculate_next_run("* * * * *", task_mod.datetime.now(task_mod.timezone.utc))
    assert next_run is not None

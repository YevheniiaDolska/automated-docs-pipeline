from __future__ import annotations

import json
import os
import runpy
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
import yaml


def test_roi_calculator_estimate_and_main_json(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    from scripts import roi_mrr_forecast_calculator as mod

    payload = mod.estimate_annual_roi(
        mod.RoiInputs(
            hours_doc_per_month=10,
            hours_eng_per_month=10,
            hours_qa_per_month=10,
            blended_rate_usd_per_hour=100,
            routine_time_saved_pct=50,
            incidents_per_month_before=1,
            incident_cost_usd=1000,
            incident_reduction_pct=50,
            releases_per_month=1,
            release_value_usd=1000,
            release_acceleration_pct=10,
            subscription_cost_usd_per_month=0,
        )
    )
    assert payload["annual_total_benefit_usd"] > 0
    assert payload["roi_pct"] == 0.0

    monkeypatch.setattr("sys.argv", ["x", "--json"])
    rc = mod.main()
    out = capsys.readouterr().out
    assert rc == 0
    parsed = json.loads(out)
    assert "roi_result" in parsed
    assert parsed["roi_result"]["annual_total_benefit_usd"] > 0


def test_retrieval_gate_mode_selection(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts import run_retrieval_evals_gate as mod

    repo = tmp_path / "repo"
    (repo / "docs/assets").mkdir(parents=True)
    (repo / "config").mkdir(parents=True)
    (repo / "reports").mkdir(parents=True)
    (repo / "docs/assets/knowledge-retrieval-index.json").write_text("[]\n", encoding="utf-8")
    (repo / "config/retrieval_eval_dataset.yml").write_text("queries: []\n", encoding="utf-8")
    (repo / "docs/assets/retrieval.faiss").write_text("faiss\n", encoding="utf-8")
    (repo / "scripts").mkdir(parents=True)
    (repo / "scripts/run_retrieval_evals.py").write_text("print('ok')\n", encoding="utf-8")

    monkeypatch.setattr(mod, "REPO_ROOT", repo)
    monkeypatch.setenv("DOCSOPS_SHARED_OPENAI_API_KEY", "k")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(mod, "_has_sentence_transformers", lambda: True)

    seen: dict[str, object] = {}

    def fake_run(cmd: list[str], cwd: str, env: dict[str, str], check: bool) -> SimpleNamespace:
        seen["cmd"] = cmd
        seen["cwd"] = cwd
        seen["env"] = env
        seen["check"] = check
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    rc = mod.main()
    assert rc == 0
    cmd = seen["cmd"]
    assert isinstance(cmd, list)
    assert "--mode" in cmd
    assert "hybrid+rerank" in cmd
    env = seen["env"]
    assert isinstance(env, dict)
    assert env["OPENAI_API_KEY"] == "k"


def test_production_smoke_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import production_smoke as mod

    monkeypatch.delenv("X_MISSING", raising=False)
    with pytest.raises(SystemExit):
        mod._env("X_MISSING")
    monkeypatch.setenv("X_PRESENT", "value")
    assert mod._env("X_PRESENT") == "value"

    response = httpx.Response(200, json={"ok": True})
    payload = mod._check(response, "health", {200})
    assert payload["ok"] is True

    bad = httpx.Response(500, text="boom")
    with pytest.raises(SystemExit):
        mod._check(bad, "health", {200})


def test_production_smoke_auth_token(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import production_smoke as mod

    class Client:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str]] = []

        def post(self, url: str, json: dict[str, str]) -> httpx.Response:
            self.calls.append(("POST", url))
            if url.endswith("/auth/register"):
                return httpx.Response(201, json={"ok": True})
            return httpx.Response(200, json={"access_token": "token-1"})

    client = Client()
    token = mod._auth_token(client, "https://api.example.com", "a@b.c", "pw")
    assert token == "token-1"
    assert len(client.calls) == 2


def test_production_smoke_auth_token_failures() -> None:
    from scripts import production_smoke as mod

    class BadRegisterClient:
        def post(self, url: str, json: dict[str, str]) -> httpx.Response:
            return httpx.Response(500, text="fail")

    with pytest.raises(SystemExit):
        mod._auth_token(BadRegisterClient(), "https://api.example.com", "a@b.c", "pw")

    class NoTokenClient:
        def post(self, url: str, json: dict[str, str]) -> httpx.Response:
            if url.endswith("/auth/register"):
                return httpx.Response(201, json={"ok": True})
            return httpx.Response(200, json={"access_token": ""})

    with pytest.raises(SystemExit):
        mod._auth_token(NoTokenClient(), "https://api.example.com", "a@b.c", "pw")


def test_docsops_generate_policy_and_security(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts import docsops_generate as mod

    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "kpi-sla-report.json").write_text(json.dumps({"status": "failed"}), encoding="utf-8")
    fired, reasons = mod._policy_triggered(reports)
    assert fired is True
    assert reasons

    monkeypatch.setenv("OPENAI_API_KEY", "x")
    with pytest.raises(RuntimeError):
        mod._assert_local_only_security(allow_api_env=False)

    mod._assert_local_only_security(allow_api_env=True)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    wrapped = mod._wrap_with_egress_guard(["echo", "ok"], egress_guard="off")
    assert wrapped == ["echo", "ok"]

    monkeypatch.setattr(mod.os, "name", "nt")
    with pytest.raises(RuntimeError):
        mod._wrap_with_egress_guard(["echo"], egress_guard="required")

    monkeypatch.setattr(mod.os, "name", "posix")
    monkeypatch.setattr(mod.shutil, "which", lambda _: "")
    with pytest.raises(RuntimeError):
        mod._wrap_with_egress_guard(["echo"], egress_guard="required")

    monkeypatch.setattr(mod.shutil, "which", lambda _: "/usr/bin/unshare")
    guarded = mod._wrap_with_egress_guard(["echo", "ok"], egress_guard="required")
    assert guarded[:3] == ["/usr/bin/unshare", "-n", "--"]


def test_docsops_generate_loaders_and_parsing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts import docsops_generate as mod

    missing = mod._load_json(tmp_path / "missing.json")
    assert missing == {}

    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{bad", encoding="utf-8")
    assert mod._load_json(bad_json) == {}

    array_json = tmp_path / "arr.json"
    array_json.write_text("[]", encoding="utf-8")
    assert mod._load_json(array_json) == {}

    bad_yaml = tmp_path / "bad.yml"
    bad_yaml.write_text("x: [", encoding="utf-8")
    assert mod._load_runtime_map(bad_yaml) == {}

    list_yaml = tmp_path / "list.yml"
    list_yaml.write_text("- a\n- b\n", encoding="utf-8")
    assert mod._load_runtime_map(list_yaml) == {}

    assert mod._nested_get({"a": {"b": 1}}, "a", "b") == 1
    assert mod._nested_get({"a": []}, "a", "b") is None
    assert mod._looks_passing("green") is True
    assert mod._looks_passing("failed") is False
    assert mod._looks_passing(False) is False
    assert mod._looks_passing("unknown") is None

    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "api_sdk_drift_report.json").write_text(json.dumps({"drift_detected": True}), encoding="utf-8")
    (reports / "pr_docs_contract.json").write_text(json.dumps({"status": "failed"}), encoding="utf-8")
    fired, reasons = mod._policy_triggered(reports)
    assert fired is True
    assert len(reasons) >= 1


def test_docsops_generate_run_local_and_cmd_generate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts import docsops_generate as mod

    runtime = tmp_path / "runtime.yml"
    runtime.write_text("veridoc:\n  api_generate_command: \"echo ok\"\n", encoding="utf-8")
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "consolidated_report.json").write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod.shutil, "which", lambda _: "/usr/bin/fake")
    monkeypatch.setattr(mod, "_wrap_with_egress_guard", lambda cmd, egress_guard: cmd)

    called: dict[str, object] = {}

    def fake_run(cmd: list[str], cwd: str, check: bool) -> SimpleNamespace:
        called["cmd"] = cmd
        called["cwd"] = cwd
        called["check"] = check
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    rc = mod._run_local_cli("codex", "prompt", auto_apply=True, dry_run=False, egress_guard="off")
    assert rc == 0
    assert called["cmd"] and isinstance(called["cmd"], list)

    args = SimpleNamespace(
        reports_dir=str(reports),
        runtime_config=str(runtime),
        mode="operator",
        trigger="always",
        auto=False,
        local_engine="codex",
        egress_guard="off",
        allow_api_env=True,
        api_generate_command="",
        dry_run=True,
    )
    rc2 = mod.cmd_generate(args)
    assert rc2 == 0

    args.mode = "veridoc"
    rc3 = mod.cmd_generate(args)
    assert rc3 == 0


def test_docsops_generate_local_cli_fallbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import docsops_generate as mod

    monkeypatch.setattr(mod.shutil, "which", lambda _: "")
    rc = mod._run_local_cli("auto", "p", auto_apply=False, dry_run=True, egress_guard="off")
    assert rc == 2

    monkeypatch.setattr(mod.shutil, "which", lambda name: "/usr/bin/fake" if name == "claude" else "")
    rc2 = mod._run_local_cli("claude", "p", auto_apply=False, dry_run=True, egress_guard="off")
    assert rc2 == 0


def test_docsops_generate_runtime_resolution_and_main(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts import docsops_generate as mod

    repo = tmp_path / "repo"
    (repo / "reports/acme-demo").mkdir(parents=True)
    fallback = repo / "reports/acme-demo/client_runtime.yml"
    fallback.write_text("x: 1\n", encoding="utf-8")
    monkeypatch.setattr(mod, "REPO_ROOT", repo)

    resolved = mod._resolve_runtime_config("missing-file.yml")
    assert resolved == fallback.resolve()
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path / "none")
    unresolved = mod._resolve_runtime_config("also-missing.yml")
    assert unresolved.name == "also-missing.yml"

    generated = repo / "generated.yml"
    generated.write_text(
        yaml.safe_dump(
            {
                "integrations": {
                    "ask_ai": {"generate_command": "echo test"},
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    runtime_map = mod._load_runtime_map(generated)
    cmd = mod._resolve_veridoc_api_command("", runtime_map)
    assert cmd == "echo test"
    assert mod._resolve_veridoc_api_command("echo explicit", runtime_map) == "echo explicit"

    monkeypatch.setattr("sys.argv", ["x", "generate", "--reports-dir", str(repo / "missing"), "--dry-run"])
    rc = mod.main()
    assert rc == 2


def test_docsops_generate_cmd_generate_edge_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts import docsops_generate as mod

    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "consolidated_report.json").write_text("{}\n", encoding="utf-8")
    runtime = tmp_path / "runtime.yml"
    runtime.write_text("{}\n", encoding="utf-8")

    args = SimpleNamespace(
        reports_dir=str(reports),
        runtime_config=str(runtime),
        mode="veridoc",
        trigger="always",
        auto=False,
        local_engine="auto",
        egress_guard="off",
        allow_api_env=False,
        api_generate_command="",
        dry_run=True,
    )
    assert mod.cmd_generate(args) == 2

    args.mode = "unsupported"
    assert mod.cmd_generate(args) == 2

    args.runtime_config = str(tmp_path / "absent.yml")
    assert mod.cmd_generate(args) == 2

    args.runtime_config = str(runtime)
    args.mode = "operator"
    args.trigger = "policy"
    (reports / "kpi-sla-report.json").write_text(json.dumps({"status": "ok"}), encoding="utf-8")
    assert mod.cmd_generate(args) == 0

    missing_consolidated = tmp_path / "reports_missing"
    missing_consolidated.mkdir()
    args.reports_dir = str(missing_consolidated)
    args.trigger = "always"
    assert mod.cmd_generate(args) == 2

    args.reports_dir = str(reports)
    args.trigger = "policy"
    args.allow_api_env = True
    (reports / "kpi-sla-report.json").write_text(json.dumps({"status": "failed"}), encoding="utf-8")
    monkeypatch.setattr(mod, "_run_local_cli", lambda *a, **k: 0)
    assert mod.cmd_generate(args) == 0

    monkeypatch.setenv("VERIDOC_API_GENERATE_COMMAND", "echo via-env")
    assert mod._resolve_veridoc_api_command("", {}) == "echo via-env"

    seen: dict[str, object] = {}

    def fake_run(cmd: list[str], cwd: str, check: bool) -> SimpleNamespace:
        seen["cmd"] = cmd
        seen["cwd"] = cwd
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    rc = mod._run_api_command("echo hi", dry_run=False)
    assert rc == 0
    assert seen["cmd"] == ["echo", "hi"]


def test_protocol_server_stubs_internal_helpers_and_main(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts import generate_protocol_server_stubs as mod

    assert mod._slug("Order Created!") == "order_created"
    schema = "type Query {\n  health: String!\n  project(id: ID): String!\n}\n"
    fields = mod._extract_graphql_fields(schema, "Query")
    assert fields == ["health", "project"]

    proto_dir = tmp_path / "proto"
    proto_dir.mkdir()
    proto_file = proto_dir / "svc.proto"
    proto_file.write_text('syntax = "proto3"; service S { rpc Ping (In) returns (Out); }\n', encoding="utf-8")
    files = mod._collect_proto_files(proto_dir)
    assert files == [proto_file]
    assert mod._collect_proto_files(proto_file) == [proto_file]
    assert mod._collect_proto_files(tmp_path / "missing.proto") == []
    rpcs = mod._extract_proto_rpcs(proto_file.read_text(encoding="utf-8"))
    assert ("S", "Ping") in rpcs

    asyncapi = tmp_path / "asyncapi.yaml"
    asyncapi.write_text(
        "asyncapi: 2.6.0\n"
        "channels:\n"
        "  project.updated:\n"
        "    publish: {}\n"
        "    subscribe: {}\n",
        encoding="utf-8",
    )
    out = tmp_path / "handlers.py"
    mod._asyncapi_stub(asyncapi, out)
    rendered = out.read_text(encoding="utf-8")
    assert "publish_handlers" in rendered
    assert "subscribe_handlers" in rendered

    ws = tmp_path / "ws.yaml"
    ws.write_text("channels:\n  room.joined: {}\n", encoding="utf-8")
    out_ws = tmp_path / "ws_handlers.py"
    mod._websocket_stub(ws, out_ws)
    assert "ws_routes" in out_ws.read_text(encoding="utf-8")

    grpc_out = tmp_path / "grpc_handlers.py"
    mod._grpc_stub(proto_dir, grpc_out)
    grpc_rendered = grpc_out.read_text(encoding="utf-8")
    assert "Task" not in grpc_rendered  # sanity check on actual source content path
    assert "class SServicer" in grpc_rendered
    assert "def Ping" in grpc_rendered

    with pytest.raises(FileNotFoundError):
        mod._grpc_stub(tmp_path / "empty_dir", tmp_path / "x.py")

    gql_source = tmp_path / "schema.graphql"
    gql_source.write_text(
        "type Query {\n  health: String!\n}\n"
        "type Mutation {\n  updateHealth: String!\n}\n"
        "type Subscription {\n  changed: String!\n}\n",
        encoding="utf-8",
    )
    gql_out = tmp_path / "graphql_handlers.py"
    mod._graphql_stub(gql_source, gql_out)
    gql_rendered = gql_out.read_text(encoding="utf-8")
    assert "query_resolvers" in gql_rendered
    assert "mutation_resolvers" in gql_rendered
    assert "subscription_resolvers" in gql_rendered

    class Fail:
        returncode = 1

    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: Fail())
    with pytest.raises(RuntimeError):
        mod._rest_stub(tmp_path / "openapi.yaml", tmp_path / "out.py")

    monkeypatch.setattr(
        "sys.argv",
        [
            "x",
            "--protocol",
            "graphql",
            "--source",
            str(asyncapi),  # source exists; parser handles no Query root
            "--output",
            str(tmp_path / "g.py"),
        ],
    )
    rc = mod.main()
    assert rc == 0


def test_retrieval_gate_import_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import run_retrieval_evals_gate as mod

    real_import = __import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "sentence_transformers":
            raise ImportError("x")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)
    assert mod._has_sentence_transformers() is False


def test_retrieval_gate_import_success() -> None:
    from scripts import run_retrieval_evals_gate as mod

    real_import = __import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "sentence_transformers":
            return object()
        return real_import(name, *args, **kwargs)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("builtins.__import__", fake_import)
        assert mod._has_sentence_transformers() is True


def test_protocol_server_stubs_runs_as_main(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    schema = tmp_path / "schema.graphql"
    schema.write_text("type Query {\n  ping: String!\n}\n", encoding="utf-8")
    out = tmp_path / "out.py"
    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_protocol_server_stubs.py",
            "--protocol",
            "graphql",
            "--source",
            str(schema),
            "--output",
            str(out),
        ],
    )
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("scripts.generate_protocol_server_stubs", run_name="__main__")
    assert int(exc.value.code) == 0
    assert out.exists()


def test_run_acme_demo_full_helpers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts import run_acme_demo_full as mod

    seen: dict[str, object] = {}

    def fake_run(cmd: list[str], cwd: str, check: bool) -> SimpleNamespace:
        seen["cmd"] = cmd
        seen["cwd"] = cwd
        seen["check"] = check
        return SimpleNamespace(returncode=7)

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    rc = mod._run(["python", "demo.py"])
    assert rc == 7
    assert seen["cmd"] == ["python", "demo.py"]
    assert seen["cwd"] == str(tmp_path)
    assert seen["check"] is False


def test_run_acme_demo_full_default_runtime(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts import run_acme_demo_full as mod

    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    assert mod._default_runtime() is None

    runtime = tmp_path / "docsops" / "config" / "client_runtime.yml"
    runtime.parent.mkdir(parents=True)
    runtime.write_text("{}\n", encoding="utf-8")
    assert mod._default_runtime() == runtime

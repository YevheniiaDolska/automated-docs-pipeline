from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_regression_snapshot_detects_change(tmp_path: Path) -> None:
    from scripts import check_protocol_regression as mod

    contract = tmp_path / "schema.graphql"
    contract.write_text("type Query { ping: String }\n", encoding="utf-8")
    snapshot = tmp_path / ".graphql-regression.json"

    rc_update = mod.main.__wrapped__ if hasattr(mod.main, "__wrapped__") else None
    assert rc_update is None  # keep coverage of branch without monkeypatch wrappers

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "check_protocol_regression.py"),
        "--protocol",
        "graphql",
        "--snapshot",
        str(snapshot),
        "--input",
        str(contract),
        "--update",
    ]
    assert __import__("subprocess").run(cmd, check=False).returncode == 0

    contract.write_text("type Query { ping: String!, pong: String }\n", encoding="utf-8")
    cmd2 = [
        sys.executable,
        str(ROOT / "scripts" / "check_protocol_regression.py"),
        "--protocol",
        "graphql",
        "--snapshot",
        str(snapshot),
        "--input",
        str(contract),
    ]
    assert __import__("subprocess").run(cmd2, check=False).returncode == 1


def test_protocol_test_assets_smart_merge_needs_review(tmp_path: Path) -> None:
    from scripts import generate_protocol_test_assets as mod

    source = tmp_path / "schema.graphql"
    source.write_text("type Query { a: String }\n", encoding="utf-8")
    out = tmp_path / "reports"

    rc = __import__("subprocess").run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_protocol_test_assets.py"),
            "--protocols",
            "graphql",
            "--source",
            str(source),
            "--output-dir",
            str(out),
        ],
        check=False,
    ).returncode
    assert rc == 0

    cases_path = out / "api_test_cases.json"
    data = json.loads(cases_path.read_text(encoding="utf-8"))
    assert data["needs_review_count"] == 0

    # Customize one case and force signature drift.
    cases = data["cases"]
    cases[0]["customized"] = True
    data["cases"] = cases
    cases_path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    source.write_text("type Query { a: String, b: String }\n", encoding="utf-8")
    rc2 = __import__("subprocess").run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_protocol_test_assets.py"),
            "--protocols",
            "graphql",
            "--source",
            str(source),
            "--output-dir",
            str(out),
        ],
        check=False,
    ).returncode
    assert rc2 == 0
    updated = json.loads(cases_path.read_text(encoding="utf-8"))
    assert updated["needs_review_count"] >= 1
    assert len(updated["cases"]) >= 3
    assert (out / "test_matrix.json").exists()
    assert (out / "fuzz_scenarios.json").exists()


def test_multi_protocol_flow_e2e_enterprise_strict(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import run_multi_protocol_contract_flow as mod

    schema = tmp_path / "schema.graphql"
    schema.write_text("type Query { health: String! }\n", encoding="utf-8")
    asyncapi = tmp_path / "asyncapi.yaml"
    asyncapi.write_text(
        "asyncapi: 2.6.0\n"
        "info: {title: x, version: 1.0.0}\n"
        "channels:\n"
        "  orders/created:\n"
        "    publish:\n"
        "      message:\n"
        "        payload:\n"
        "          type: object\n",
        encoding="utf-8",
    )

    runtime = {
        "api_governance": {"strictness": "enterprise-strict"},
        "api_protocols": ["graphql", "asyncapi"],
        "api_protocol_settings": {
            "graphql": {"enabled": True, "schema_path": str(schema), "generate_test_assets": True, "upload_test_assets": False},
            "asyncapi": {"enabled": True, "spec_path": str(asyncapi), "generate_test_assets": True, "upload_test_assets": False},
        },
    }
    runtime_path = tmp_path / "runtime.yml"
    runtime_path.write_text(yaml.safe_dump(runtime, sort_keys=False), encoding="utf-8")
    reports = tmp_path / "reports"

    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "x",
            "--runtime-config",
            str(runtime_path),
            "--reports-dir",
            str(reports),
        ],
    )

    rc = mod.main()
    assert rc == 0
    report = json.loads((reports / "multi_protocol_contract_report.json").read_text(encoding="utf-8"))
    assert report["strict_mode"] is True
    assert report["failed"] is False
    assert set(report["by_protocol"].keys()) == {"graphql", "asyncapi"}
    for protocol in ("graphql", "asyncapi"):
        stages = report["by_protocol"][protocol]
        coverage_stages = [s for s in stages if s.get("stage") == "test_assets"]
        assert coverage_stages
        assert all(bool(s.get("details", {}).get("coverage_ok", False)) for s in coverage_stages)


def test_publish_protocol_assets_blocks_absolute_target(tmp_path: Path) -> None:
    source = tmp_path / "schema.graphql"
    source.write_text("type Query { ping: String }\n", encoding="utf-8")
    doc = tmp_path / "graphql-api.md"
    doc.write_text("# GraphQL\n", encoding="utf-8")

    rc = __import__("subprocess").run(
        [
            sys.executable,
            str(ROOT / "scripts" / "publish_protocol_assets.py"),
            "--protocol",
            "graphql",
            "--source",
            str(source),
            "--generated-doc",
            str(doc),
            "--target-root",
            str(tmp_path.resolve()),
        ],
        check=False,
    ).returncode
    assert rc != 0


def test_protocol_helper_performance() -> None:
    from scripts.api_protocols import normalize_protocols

    data = ["rest", "graphql", "grpc", "asyncapi", "websocket"] * 20000
    start = time.perf_counter()
    out = normalize_protocols(data)
    elapsed = time.perf_counter() - start
    assert out == ["rest", "graphql", "grpc", "asyncapi", "websocket"]
    assert elapsed < 1.0


def test_protocol_docs_include_interactive_blocks(tmp_path: Path) -> None:
    schema = tmp_path / "schema.graphql"
    schema.write_text(
        "type Query { health: String! }\\n"
        "type Mutation { updateHealth(value: String!): String! }\\n"
        "type Subscription { healthChanged: String! }\\n",
        encoding="utf-8",
    )
    output = tmp_path / "graphql.md"

    rc = __import__("subprocess").run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_protocol_docs.py"),
            "--protocol",
            "graphql",
            "--source",
            str(schema),
            "--output",
            str(output),
            "--endpoint",
            "https://example.com/graphql",
        ],
        check=False,
    ).returncode
    assert rc == 0
    rendered = output.read_text(encoding="utf-8")
    assert "Interactive GraphQL Playground" in rendered
    assert "graphql-run" in rendered
    assert "https://example.com/graphql" in rendered
    assert "Subscription count" in rendered
    assert "healthChanged" in rendered


def test_protocol_docs_semantic_responses_for_all_non_rest_protocols(tmp_path: Path) -> None:
    graphql = tmp_path / "schema.graphql"
    graphql.write_text(
        "type Query { health: String! project(id: ID!): String }\\n"
        "type Mutation { createProject(name: String!): String }\\n",
        encoding="utf-8",
    )
    proto = tmp_path / "service.proto"
    proto.write_text(
        "syntax = \"proto3\";\n"
        "service ProjectService {\n"
        "  rpc GetProject (GetProjectRequest) returns (Project);\n"
        "}\n"
        "message GetProjectRequest { string project_id = 1; }\n"
        "message Project { string id = 1; string status = 2; }\n",
        encoding="utf-8",
    )
    asyncapi = tmp_path / "asyncapi.yaml"
    asyncapi.write_text(
        "asyncapi: 2.6.0\n"
        "info:\n"
        "  title: Acme Events\n"
        "  version: 1.0.0\n"
        "channels:\n"
        "  project.updated:\n"
        "    publish:\n"
        "      message:\n"
        "        payload:\n"
        "          type: object\n",
        encoding="utf-8",
    )
    websocket = tmp_path / "websocket.yaml"
    websocket.write_text(
        "channels:\n"
        "  project.updated:\n"
        "    description: project updates\n",
        encoding="utf-8",
    )

    gql_output = tmp_path / "graphql.md"
    grpc_output = tmp_path / "grpc.md"
    async_output = tmp_path / "asyncapi.md"
    ws_output = tmp_path / "websocket.md"

    rc_gql = __import__("subprocess").run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_protocol_docs.py"),
            "--protocol",
            "graphql",
            "--source",
            str(graphql),
            "--output",
            str(gql_output),
            "--endpoint",
            "https://example.com/graphql",
        ],
        check=False,
    ).returncode
    rc_grpc = __import__("subprocess").run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_protocol_docs.py"),
            "--protocol",
            "grpc",
            "--source",
            str(proto),
            "--output",
            str(grpc_output),
            "--endpoint",
            "https://example.com/grpc/invoke",
        ],
        check=False,
    ).returncode

    rc_async = __import__("subprocess").run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_protocol_docs.py"),
            "--protocol",
            "asyncapi",
            "--source",
            str(asyncapi),
            "--output",
            str(async_output),
            "--ws-endpoint",
            "wss://echo.websocket.events",
            "--http-endpoint",
            "https://example.com/events",
        ],
        check=False,
    ).returncode
    rc_ws = __import__("subprocess").run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_protocol_docs.py"),
            "--protocol",
            "websocket",
            "--source",
            str(websocket),
            "--output",
            str(ws_output),
            "--ws-endpoint",
            "wss://echo.websocket.events",
        ],
        check=False,
    ).returncode

    assert rc_gql == 0
    assert rc_grpc == 0
    assert rc_async == 0
    assert rc_ws == 0

    gql_rendered = gql_output.read_text(encoding="utf-8")
    grpc_rendered = grpc_output.read_text(encoding="utf-8")
    async_rendered = async_output.read_text(encoding="utf-8")
    ws_rendered = ws_output.read_text(encoding="utf-8")
    assert "semantic-fallback" in gql_rendered
    assert "simulated_response" in gql_rendered
    assert "semantic-fallback" in grpc_rendered
    assert "simulated_response" in grpc_rendered
    assert "Sandbox semantic mode" in async_rendered
    assert "simulated_response" in async_rendered
    assert "project.updated" in async_rendered
    assert "Sandbox semantic mode" in ws_rendered
    assert "simulated_response" in ws_rendered
    assert "subscribe" in ws_rendered


def test_code_first_export_hook_runs_before_ingest(tmp_path: Path) -> None:
    from scripts.multi_protocol_engine import ProtocolAdapter

    schema = tmp_path / "schema.graphql"
    marker = tmp_path / "marker.txt"
    cmd = f"echo ok > '{schema}' && echo run > '{marker}'"
    adapter = ProtocolAdapter(
        "graphql",
        {
            "mode": "code-first",
            "schema_path": str(schema),
            "code_first_schema_export_cmd": cmd,
        },
        repo_root=ROOT,
        scripts_dir=ROOT / "scripts",
    )
    result = adapter.ingest(allow_fail=False)
    assert result.ok is True
    assert schema.exists()
    assert marker.exists()


def test_quality_suite_semantic_check_fails_when_markers_missing(tmp_path: Path) -> None:
    doc = tmp_path / "websocket-api.md"
    doc.write_text("# WebSocket\n\nNo semantic markers here.\n", encoding="utf-8")
    reports = tmp_path / "reports"

    rc = __import__("subprocess").run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_protocol_docs_quality_suite.py"),
            "--protocol",
            "websocket",
            "--generated-doc",
            str(doc),
            "--docs-root",
            str(tmp_path),
            "--reports-dir",
            str(reports),
            "--semantic-required",
        ],
        check=False,
    ).returncode
    assert rc == 1

    report_path = reports / "websocket_quality_suite_report.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    semantic = [s for s in payload["steps"] if s.get("step") == "semantic_consistency"]
    assert semantic
    assert semantic[-1]["ok"] is False
    assert semantic[-1]["missing_markers"]


def test_quality_suite_semantic_conflict_scan_blocks_raw_echo_patterns(tmp_path: Path) -> None:
    doc = tmp_path / "websocket-api.md"
    doc.write_text(
        "\n".join(
            [
                "# WebSocket",
                "Sandbox semantic mode",
                "simulated_response",
                "subscribe",
                "publish",
                "list_projects",
                "wsConn.onmessage = function (e) { log('Received: ' + e.data); };",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    reports = tmp_path / "reports"

    rc = __import__("subprocess").run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_protocol_docs_quality_suite.py"),
            "--protocol",
            "websocket",
            "--generated-doc",
            str(doc),
            "--docs-root",
            str(tmp_path),
            "--reports-dir",
            str(reports),
            "--semantic-required",
        ],
        check=False,
    ).returncode
    assert rc == 1

    report_path = reports / "websocket_quality_suite_report.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    conflicts = [s for s in payload["steps"] if s.get("step") == "semantic_conflict_scan"]
    assert conflicts
    assert conflicts[-1]["ok"] is False
    assert conflicts[-1]["forbidden_patterns_found"]


@pytest.mark.parametrize(
    ("protocol", "output_rel"),
    [
        ("graphql", "api/schema.graphql"),
        ("grpc", "api/proto"),
        ("asyncapi", "api/asyncapi.yaml"),
        ("websocket", "api/websocket.yaml"),
    ],
)
def test_generate_contract_from_planning_notes_for_non_rest(tmp_path: Path, protocol: str, output_rel: str) -> None:
    notes = tmp_path / "notes.md"
    notes.write_text(
        "# Planning\n"
        "- query: project\n"
        "- mutation: create_project\n"
        "- event: project.updated\n"
        "- channel: task.completed\n",
        encoding="utf-8",
    )
    output = tmp_path / output_rel
    output.parent.mkdir(parents=True, exist_ok=True)

    rc = __import__("subprocess").run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_protocol_contract_from_planning_notes.py"),
            "--protocol",
            protocol,
            "--notes",
            str(notes),
            "--output",
            str(output),
            "--project-name",
            "Acme API",
        ],
        check=False,
    ).returncode
    assert rc == 0
    if protocol == "grpc":
        proto_files = sorted((tmp_path / "api/proto").rglob("*.proto"))
        assert proto_files
        rendered = proto_files[0].read_text(encoding="utf-8")
        assert 'syntax = "proto3";' in rendered
        assert "service AcmeApiService" in rendered
    else:
        assert output.exists()
        rendered = output.read_text(encoding="utf-8")
        if protocol == "graphql":
            assert "type Query" in rendered
        if protocol == "asyncapi":
            assert "channels:" in rendered and "publish:" in rendered
        if protocol == "websocket":
            assert "channels:" in rendered and "subscribe:" in rendered


def test_multi_protocol_flow_generates_missing_contracts_from_notes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import run_multi_protocol_contract_flow as mod

    notes = tmp_path / "notes" / "api-planning.md"
    notes.parent.mkdir(parents=True, exist_ok=True)
    notes.write_text(
        "# API planning\n"
        "- query: health\n"
        "- mutation: create_project\n"
        "- event: project.updated\n",
        encoding="utf-8",
    )

    runtime = {
        "api_governance": {"strictness": "enterprise-strict"},
        "api_protocols": ["graphql", "grpc", "asyncapi", "websocket"],
        "api_protocol_settings": {
            "graphql": {
                "enabled": True,
                "schema_path": str(tmp_path / "api/schema.graphql"),
                "notes_path": str(notes),
                "generate_from_notes": True,
                "generated_docs_output": str(tmp_path / "docs/reference/graphql-api.md"),
                "generate_test_assets": False,
            },
            "grpc": {
                "enabled": True,
                "proto_paths": [str(tmp_path / "api/proto")],
                "notes_path": str(notes),
                "generate_from_notes": True,
                "generated_docs_output": str(tmp_path / "docs/reference/grpc-api.md"),
                "generate_test_assets": False,
            },
            "asyncapi": {
                "enabled": True,
                "spec_path": str(tmp_path / "api/asyncapi.yaml"),
                "notes_path": str(notes),
                "generate_from_notes": True,
                "generated_docs_output": str(tmp_path / "docs/reference/asyncapi-api.md"),
                "generate_test_assets": False,
            },
            "websocket": {
                "enabled": True,
                "contract_path": str(tmp_path / "api/websocket.yaml"),
                "notes_path": str(notes),
                "generate_from_notes": True,
                "generated_docs_output": str(tmp_path / "docs/reference/websocket-api.md"),
                "generate_test_assets": False,
            },
        },
    }
    runtime_path = tmp_path / "runtime.yml"
    runtime_path.write_text(yaml.safe_dump(runtime, sort_keys=False), encoding="utf-8")
    reports = tmp_path / "reports"

    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "x",
            "--runtime-config",
            str(runtime_path),
            "--reports-dir",
            str(reports),
        ],
    )

    rc = mod.main()
    assert rc == 0
    report = json.loads((reports / "multi_protocol_contract_report.json").read_text(encoding="utf-8"))
    for protocol in ("graphql", "grpc", "asyncapi", "websocket"):
        stages = report["by_protocol"][protocol]
        assert any(s.get("stage") == "contract_from_notes_generation" for s in stages)

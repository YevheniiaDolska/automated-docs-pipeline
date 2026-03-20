from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> int:
    return subprocess.run(cmd, check=False).returncode


def test_graphql_validator_detects_duplicate_fields(tmp_path: Path) -> None:
    schema = tmp_path / "bad.graphql"
    schema.write_text("type Query { ping: String\n ping: String }\n", encoding="utf-8")
    rc = _run([sys.executable, str(ROOT / "scripts" / "validate_graphql_contract.py"), str(schema)])
    assert rc == 1


def test_proto_validator_detects_proto3_required(tmp_path: Path) -> None:
    proto = tmp_path / "bad.proto"
    proto.write_text(
        'syntax = "proto3";\\nmessage User { required string id = 1; }\\nservice U { rpc Get(User) returns (User); }\\n',
        encoding="utf-8",
    )
    rc = _run([sys.executable, str(ROOT / "scripts" / "validate_proto_contract.py"), "--proto", str(proto)])
    assert rc == 1


def test_asyncapi_validator_requires_operation_message_payload(tmp_path: Path) -> None:
    spec = tmp_path / "bad_asyncapi.yaml"
    spec.write_text(
        "asyncapi: 2.6.0\\n"
        "info: {title: x, version: 1.0.0}\\n"
        "channels:\\n"
        "  orders/created:\\n"
        "    publish: {}\\n",
        encoding="utf-8",
    )
    rc = _run([sys.executable, str(ROOT / "scripts" / "validate_asyncapi_contract.py"), str(spec)])
    assert rc == 1


def test_websocket_validator_requires_payload_shape(tmp_path: Path) -> None:
    contract = tmp_path / "bad_ws.yaml"
    contract.write_text("channels:\\n  chat.message:\\n    description: x\\n", encoding="utf-8")
    rc = _run([sys.executable, str(ROOT / "scripts" / "validate_websocket_contract.py"), str(contract)])
    assert rc == 1


def test_protocol_coverage_gate_fails_for_shallow_cases(tmp_path: Path) -> None:
    cases = {
        "cases": [
            {
                "id": "TC-graphql-query-positive",
                "protocol": "graphql",
                "entity": "query:health",
                "check_type": "positive",
            }
        ]
    }
    cases_path = tmp_path / "api_test_cases.json"
    cases_path.write_text(json.dumps(cases, ensure_ascii=True), encoding="utf-8")
    report = tmp_path / "coverage_report.json"
    rc = _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_protocol_test_coverage.py"),
            "--cases-json",
            str(cases_path),
            "--report",
            str(report),
        ]
    )
    assert rc == 1
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert payload["errors"]


def test_graphql_test_assets_include_subscription_entities(tmp_path: Path) -> None:
    schema = tmp_path / "schema.graphql"
    schema.write_text(
        "type Query { health: String! }\n"
        "type Mutation { updateHealth(value: String!): String! }\n"
        "type Subscription { healthChanged: String! }\n",
        encoding="utf-8",
    )
    out = tmp_path / "reports"
    rc = _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_protocol_test_assets.py"),
            "--protocols",
            "graphql",
            "--source",
            str(schema),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == 0
    payload = json.loads((out / "api_test_cases.json").read_text(encoding="utf-8"))
    entities = {str(case.get("entity", "")) for case in payload.get("cases", [])}
    assert any(e.startswith("subscription:") for e in entities)

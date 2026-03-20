from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_normalize_protocols_aliases() -> None:
    from scripts.api_protocols import normalize_protocols

    protocols = normalize_protocols(["OpenAPI", "gql", "proto", "asyncapi", "ws", "invalid"])
    assert protocols == ["rest", "graphql", "grpc", "asyncapi", "websocket"]


def test_docs_contract_detects_graphql_interface() -> None:
    from scripts.check_docs_contract import evaluate_contract

    report = evaluate_contract(["api/schema.graphql"])
    assert report["status"] == "drift"
    assert report["blocked"] is True

    report_ok = evaluate_contract(["api/schema.graphql", "docs/reference/graphql.md"])
    assert report_ok["status"] == "ok"


def test_drift_detects_grpc_changes() -> None:
    from scripts.check_api_sdk_drift import evaluate

    report = evaluate(["api/proto/service.proto"])
    assert report.status == "drift"

    report_ok = evaluate(["api/proto/service.proto", "docs/reference/grpc.md"])
    assert report_ok.status == "ok"


def test_build_runtime_config_contains_protocol_settings() -> None:
    from scripts.build_client_bundle import build_runtime_config

    runtime = build_runtime_config(
        {
            "client": {"id": "acme", "company_name": "Acme"},
            "runtime": {
                "api_protocols": ["rest", "graphql", "grpc"],
                "api_protocol_settings": {
                    "graphql": {"schema_path": "contracts/schema.graphql"},
                    "grpc": {"proto_paths": ["contracts/proto"]},
                },
            },
        }
    )

    assert runtime["api_protocols"] == ["rest", "graphql", "grpc"]
    assert runtime["api_protocol_settings"]["graphql"]["schema_path"] == "contracts/schema.graphql"
    assert runtime["api_protocol_settings"]["grpc"]["proto_paths"] == ["contracts/proto"]


def test_multi_protocol_contract_flow_runs_graphql(tmp_path: Path, monkeypatch) -> None:
    from scripts import run_multi_protocol_contract_flow as mod

    schema = tmp_path / "schema.graphql"
    schema.write_text("type Query { health: String! }\n", encoding="utf-8")

    runtime = {
        "api_protocols": ["graphql"],
        "api_protocol_settings": {
            "graphql": {
                "enabled": True,
                "schema_path": str(schema),
                "generate_test_assets": False,
                "upload_test_assets": False,
            }
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
            "--strict",
        ],
    )

    rc = mod.main()
    assert rc == 0
    assert (reports / "multi_protocol_contract_report.json").exists()

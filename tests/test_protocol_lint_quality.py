"""Tests for run_protocol_lint_stack and run_protocol_docs_quality_suite."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_protocol_lint_stack import (
    _asyncapi_checks,
    _collect_proto_files,
    _graphql_checks,
    _grpc_checks,
    _load_data,
    _run as lint_run,
    _websocket_checks,
    main as lint_main,
)
from scripts.run_protocol_docs_quality_suite import (
    _forbidden_semantic_patterns,
    _run as quality_run,
    _semantic_markers,
    main as quality_main,
)


# ---------------------------------------------------------------------------
# _load_data
# ---------------------------------------------------------------------------


def test_load_data_yaml(tmp_path: Path) -> None:
    """_load_data parses a YAML file into a dict."""
    f = tmp_path / "sample.yaml"
    f.write_text("key: value\n", encoding="utf-8")
    result = _load_data(f)
    assert result == {"key": "value"}


def test_load_data_yml_extension(tmp_path: Path) -> None:
    """_load_data also handles .yml extension."""
    f = tmp_path / "sample.yml"
    f.write_text("items:\n  - one\n  - two\n", encoding="utf-8")
    result = _load_data(f)
    assert result == {"items": ["one", "two"]}


def test_load_data_json(tmp_path: Path) -> None:
    """_load_data parses a JSON file."""
    f = tmp_path / "data.json"
    f.write_text('{"num": 42}', encoding="utf-8")
    result = _load_data(f)
    assert result == {"num": 42}


def test_load_data_text(tmp_path: Path) -> None:
    """_load_data returns raw text for non-YAML/JSON files."""
    f = tmp_path / "schema.graphql"
    f.write_text("type Query { ok: Boolean }", encoding="utf-8")
    result = _load_data(f)
    assert result == "type Query { ok: Boolean }"


def test_load_data_directory(tmp_path: Path) -> None:
    """_load_data returns None when given a directory."""
    result = _load_data(tmp_path)
    assert result is None


# ---------------------------------------------------------------------------
# _collect_proto_files
# ---------------------------------------------------------------------------


def test_collect_proto_files_single_file(tmp_path: Path) -> None:
    """_collect_proto_files returns a single .proto file in a list."""
    proto = tmp_path / "service.proto"
    proto.write_text('syntax = "proto3";', encoding="utf-8")
    result = _collect_proto_files(proto)
    assert result == [proto]


def test_collect_proto_files_directory(tmp_path: Path) -> None:
    """_collect_proto_files recursively finds .proto files in a directory."""
    sub = tmp_path / "protos"
    sub.mkdir()
    (sub / "a.proto").write_text("//a", encoding="utf-8")
    (sub / "b.proto").write_text("//b", encoding="utf-8")
    (sub / "readme.txt").write_text("not proto", encoding="utf-8")
    result = _collect_proto_files(sub)
    assert len(result) == 2
    assert all(p.suffix == ".proto" for p in result)


def test_collect_proto_files_non_proto(tmp_path: Path) -> None:
    """_collect_proto_files returns empty for a non-.proto single file."""
    f = tmp_path / "schema.graphql"
    f.write_text("type Query {}", encoding="utf-8")
    result = _collect_proto_files(f)
    assert result == []


def test_collect_proto_files_empty_dir(tmp_path: Path) -> None:
    """_collect_proto_files returns empty list for a dir with no .proto files."""
    result = _collect_proto_files(tmp_path)
    assert result == []


# ---------------------------------------------------------------------------
# _graphql_checks -- valid
# ---------------------------------------------------------------------------


def _valid_graphql(tmp_path: Path) -> Path:
    """Helper: write a valid GraphQL schema and return its path."""
    schema = tmp_path / "schema.graphql"
    schema.write_text(
        "type Query {\n  health: String!\n}\n\n"
        "type User {\n  id: ID!\n  name: String!\n}\n",
        encoding="utf-8",
    )
    return schema


def test_graphql_checks_all_pass(tmp_path: Path) -> None:
    """All 8 GraphQL checks pass on a valid schema."""
    schema = _valid_graphql(tmp_path)
    checks = _graphql_checks(schema)
    assert len(checks) == 8
    assert all(ok for _, ok, _ in checks)


def test_graphql_check_names(tmp_path: Path) -> None:
    """GraphQL checks have the expected names in order."""
    schema = _valid_graphql(tmp_path)
    names = [name for name, _, _ in _graphql_checks(schema)]
    expected = [
        "source_exists",
        "non_empty",
        "root_declared",
        "balanced_braces",
        "balanced_parentheses",
        "no_duplicate_types",
        "no_duplicate_fields",
        "schema_root_references",
    ]
    assert names == expected


# ---------------------------------------------------------------------------
# _graphql_checks -- invalid / edge cases
# ---------------------------------------------------------------------------


def test_graphql_missing_file(tmp_path: Path) -> None:
    """source_exists and non_empty fail when file does not exist."""
    missing = tmp_path / "missing.graphql"
    checks = _graphql_checks(missing)
    result = {name: ok for name, ok, _ in checks}
    assert result["source_exists"] is False
    assert result["non_empty"] is False


def test_graphql_empty_file(tmp_path: Path) -> None:
    """non_empty check fails on an empty file."""
    f = tmp_path / "empty.graphql"
    f.write_text("", encoding="utf-8")
    result = {name: ok for name, ok, _ in _graphql_checks(f)}
    assert result["source_exists"] is True
    assert result["non_empty"] is False


def test_graphql_unbalanced_braces(tmp_path: Path) -> None:
    """balanced_braces fails when braces do not match."""
    f = tmp_path / "bad.graphql"
    f.write_text("type Query { health: String\n", encoding="utf-8")
    result = {name: ok for name, ok, _ in _graphql_checks(f)}
    assert result["balanced_braces"] is False


def test_graphql_unbalanced_parentheses(tmp_path: Path) -> None:
    """balanced_parentheses fails when parens do not match."""
    f = tmp_path / "bad.graphql"
    f.write_text("type Query {\n  users(limit: Int: [User]\n}\n", encoding="utf-8")
    result = {name: ok for name, ok, _ in _graphql_checks(f)}
    assert result["balanced_parentheses"] is False


def test_graphql_duplicate_types(tmp_path: Path) -> None:
    """no_duplicate_types fails when the same type is declared twice."""
    f = tmp_path / "dup.graphql"
    f.write_text(
        "type Query { ok: Boolean }\ntype User { id: ID }\ntype User { name: String }\n",
        encoding="utf-8",
    )
    result = {name: ok for name, ok, _ in _graphql_checks(f)}
    assert result["no_duplicate_types"] is False


def test_graphql_duplicate_fields(tmp_path: Path) -> None:
    """no_duplicate_fields fails when a type has duplicate field names."""
    f = tmp_path / "dup_fields.graphql"
    f.write_text(
        "type Query {\n  id: ID\n  id: String\n}\n",
        encoding="utf-8",
    )
    result = {name: ok for name, ok, _ in _graphql_checks(f)}
    assert result["no_duplicate_fields"] is False


def test_graphql_schema_root_bad_reference(tmp_path: Path) -> None:
    """schema_root_references fails when schema block references missing type."""
    f = tmp_path / "bad_ref.graphql"
    f.write_text(
        "type Query { ok: Boolean }\nschema {\n  query: MissingType\n}\n",
        encoding="utf-8",
    )
    result = {name: ok for name, ok, _ in _graphql_checks(f)}
    assert result["schema_root_references"] is False


def test_graphql_no_root_declared(tmp_path: Path) -> None:
    """root_declared fails when neither 'type Query' nor 'schema' exists."""
    f = tmp_path / "noroot.graphql"
    f.write_text("type User {\n  id: ID\n}\n", encoding="utf-8")
    result = {name: ok for name, ok, _ in _graphql_checks(f)}
    assert result["root_declared"] is False


# ---------------------------------------------------------------------------
# _grpc_checks -- valid
# ---------------------------------------------------------------------------


def _valid_proto(tmp_path: Path) -> Path:
    """Helper: write a valid proto3 file and return its path."""
    proto = tmp_path / "service.proto"
    proto.write_text(
        'syntax = "proto3";\n\n'
        "service Greeter {\n"
        "  rpc SayHello (HelloRequest) returns (HelloReply) {}\n"
        "}\n\n"
        "message HelloRequest { string name = 1; }\n"
        "message HelloReply { string message = 1; }\n",
        encoding="utf-8",
    )
    return proto


def test_grpc_checks_all_pass(tmp_path: Path) -> None:
    """All 8 gRPC checks pass on a valid proto3 file."""
    proto = _valid_proto(tmp_path)
    checks = _grpc_checks(proto)
    assert len(checks) == 8
    assert all(ok for _, ok, _ in checks)


def test_grpc_check_names(tmp_path: Path) -> None:
    """gRPC checks have the expected names in order."""
    proto = _valid_proto(tmp_path)
    names = [name for name, _, _ in _grpc_checks(proto)]
    expected = [
        "source_exists",
        "proto_files_found",
        "syntax_declared",
        "balanced_braces",
        "service_present",
        "rpc_present",
        "no_duplicate_rpc",
        "proto3_no_required",
    ]
    assert names == expected


# ---------------------------------------------------------------------------
# _grpc_checks -- invalid / edge cases
# ---------------------------------------------------------------------------


def test_grpc_missing_file(tmp_path: Path) -> None:
    """source_exists and proto_files_found fail when file does not exist."""
    missing = tmp_path / "missing.proto"
    checks = _grpc_checks(missing)
    result = {name: ok for name, ok, _ in checks}
    assert result["source_exists"] is False
    assert result["proto_files_found"] is False


def test_grpc_no_syntax(tmp_path: Path) -> None:
    """syntax_declared fails when syntax line is missing."""
    f = tmp_path / "bad.proto"
    f.write_text(
        "service Greeter {\n  rpc SayHello (Req) returns (Resp) {}\n}\n",
        encoding="utf-8",
    )
    result = {name: ok for name, ok, _ in _grpc_checks(f)}
    assert result["syntax_declared"] is False


def test_grpc_unbalanced_braces(tmp_path: Path) -> None:
    """balanced_braces fails when braces do not match."""
    f = tmp_path / "bad.proto"
    f.write_text(
        'syntax = "proto3";\nservice Greeter {\n  rpc SayHello (Req) returns (Resp) {}\n',
        encoding="utf-8",
    )
    result = {name: ok for name, ok, _ in _grpc_checks(f)}
    assert result["balanced_braces"] is False


def test_grpc_no_service(tmp_path: Path) -> None:
    """service_present fails when no service is declared."""
    f = tmp_path / "noserv.proto"
    f.write_text(
        'syntax = "proto3";\nmessage Req { string name = 1; }\n',
        encoding="utf-8",
    )
    result = {name: ok for name, ok, _ in _grpc_checks(f)}
    assert result["service_present"] is False
    assert result["rpc_present"] is False


def test_grpc_duplicate_rpc(tmp_path: Path) -> None:
    """no_duplicate_rpc fails when the same rpc name appears twice."""
    f = tmp_path / "dup.proto"
    # Use semicolons instead of {} for rpc bodies so the non-greedy regex
    # captures both rpcs inside the service block.
    f.write_text(
        'syntax = "proto3";\n'
        "service Greeter {\n"
        "  rpc SayHello (Req) returns (Resp);\n"
        "  rpc SayHello (Req) returns (Resp);\n"
        "}\n"
        "message Req { string name = 1; }\n"
        "message Resp { string msg = 1; }\n",
        encoding="utf-8",
    )
    result = {name: ok for name, ok, _ in _grpc_checks(f)}
    assert result["no_duplicate_rpc"] is False


def test_grpc_proto3_required_field(tmp_path: Path) -> None:
    """proto3_no_required fails when 'required' keyword is used in proto3."""
    f = tmp_path / "req.proto"
    f.write_text(
        'syntax = "proto3";\n'
        "service Greeter {\n"
        "  rpc SayHello (Req) returns (Resp) {}\n"
        "}\n"
        "message Req { required string name = 1; }\n"
        "message Resp { string message = 1; }\n",
        encoding="utf-8",
    )
    result = {name: ok for name, ok, _ in _grpc_checks(f)}
    assert result["proto3_no_required"] is False


def test_grpc_proto2_required_allowed(tmp_path: Path) -> None:
    """proto3_no_required passes when 'required' is used in proto2."""
    f = tmp_path / "v2.proto"
    f.write_text(
        'syntax = "proto2";\n'
        "service Greeter {\n"
        "  rpc SayHello (Req) returns (Resp) {}\n"
        "}\n"
        "message Req { required string name = 1; }\n"
        "message Resp { optional string message = 1; }\n",
        encoding="utf-8",
    )
    result = {name: ok for name, ok, _ in _grpc_checks(f)}
    assert result["proto3_no_required"] is True


def test_grpc_directory_source(tmp_path: Path) -> None:
    """_grpc_checks handles a directory with multiple proto files."""
    d = tmp_path / "protos"
    d.mkdir()
    (d / "a.proto").write_text(
        'syntax = "proto3";\nservice A {\n  rpc DoA (Req) returns (Resp) {}\n}\n'
        "message Req { string x = 1; }\nmessage Resp { string y = 1; }\n",
        encoding="utf-8",
    )
    checks = _grpc_checks(d)
    result = {name: ok for name, ok, _ in checks}
    assert result["source_exists"] is True
    assert result["proto_files_found"] is True
    assert result["service_present"] is True


# ---------------------------------------------------------------------------
# _asyncapi_checks -- valid
# ---------------------------------------------------------------------------


def _valid_asyncapi(tmp_path: Path) -> Path:
    """Helper: write a valid AsyncAPI contract and return its path."""
    f = tmp_path / "asyncapi.yaml"
    data: dict[str, Any] = {
        "asyncapi": "2.6.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "channels": {
            "user/signedup": {
                "publish": {
                    "message": {
                        "payload": {
                            "type": "object",
                            "properties": {"userId": {"type": "string"}},
                        }
                    }
                }
            }
        },
    }
    f.write_text(yaml.dump(data), encoding="utf-8")
    return f


def test_asyncapi_checks_all_pass(tmp_path: Path) -> None:
    """All 8 AsyncAPI checks pass on a valid contract."""
    source = _valid_asyncapi(tmp_path)
    checks = _asyncapi_checks(source)
    assert len(checks) == 8
    assert all(ok for _, ok, _ in checks)


def test_asyncapi_check_names(tmp_path: Path) -> None:
    """AsyncAPI checks have the expected names in order."""
    source = _valid_asyncapi(tmp_path)
    names = [name for name, _, _ in _asyncapi_checks(source)]
    expected = [
        "source_exists",
        "top_level_keys",
        "info_title",
        "info_version",
        "channels_non_empty",
        "operations_present",
        "message_payload_present",
        "version_string",
    ]
    assert names == expected


# ---------------------------------------------------------------------------
# _asyncapi_checks -- invalid / edge cases
# ---------------------------------------------------------------------------


def test_asyncapi_missing_file(tmp_path: Path) -> None:
    """source_exists fails and top_level_keys fails for missing file."""
    missing = tmp_path / "missing.yaml"
    result = {name: ok for name, ok, _ in _asyncapi_checks(missing)}
    assert result["source_exists"] is False
    assert result["top_level_keys"] is False


def test_asyncapi_missing_info_title(tmp_path: Path) -> None:
    """info_title fails when info.title is empty."""
    f = tmp_path / "bad.yaml"
    data: dict[str, Any] = {
        "asyncapi": "2.6.0",
        "info": {"title": "", "version": "1.0.0"},
        "channels": {
            "ch": {"publish": {"message": {"payload": {"type": "string"}}}}
        },
    }
    f.write_text(yaml.dump(data), encoding="utf-8")
    result = {name: ok for name, ok, _ in _asyncapi_checks(f)}
    assert result["info_title"] is False


def test_asyncapi_empty_channels(tmp_path: Path) -> None:
    """channels_non_empty fails when channels dict is empty."""
    f = tmp_path / "empty_ch.yaml"
    data: dict[str, Any] = {
        "asyncapi": "2.6.0",
        "info": {"title": "T", "version": "1.0"},
        "channels": {},
    }
    f.write_text(yaml.dump(data), encoding="utf-8")
    result = {name: ok for name, ok, _ in _asyncapi_checks(f)}
    assert result["channels_non_empty"] is False


def test_asyncapi_no_operations(tmp_path: Path) -> None:
    """operations_present fails when channel has no publish/subscribe."""
    f = tmp_path / "no_op.yaml"
    data: dict[str, Any] = {
        "asyncapi": "2.6.0",
        "info": {"title": "T", "version": "1.0"},
        "channels": {"ch": {"description": "orphan channel"}},
    }
    f.write_text(yaml.dump(data), encoding="utf-8")
    result = {name: ok for name, ok, _ in _asyncapi_checks(f)}
    assert result["operations_present"] is False


def test_asyncapi_no_payload(tmp_path: Path) -> None:
    """message_payload_present fails when message has no payload."""
    f = tmp_path / "no_payload.yaml"
    data: dict[str, Any] = {
        "asyncapi": "2.6.0",
        "info": {"title": "T", "version": "1.0"},
        "channels": {"ch": {"publish": {"message": {"description": "no payload"}}}},
    }
    f.write_text(yaml.dump(data), encoding="utf-8")
    result = {name: ok for name, ok, _ in _asyncapi_checks(f)}
    assert result["message_payload_present"] is False


def test_asyncapi_version_not_string(tmp_path: Path) -> None:
    """version_string fails when asyncapi field is a number."""
    f = tmp_path / "bad_ver.yaml"
    data: dict[str, Any] = {
        "asyncapi": 2.6,
        "info": {"title": "T", "version": "1.0"},
        "channels": {
            "ch": {"publish": {"message": {"payload": {"type": "string"}}}}
        },
    }
    f.write_text(yaml.dump(data), encoding="utf-8")
    result = {name: ok for name, ok, _ in _asyncapi_checks(f)}
    assert result["version_string"] is False


# ---------------------------------------------------------------------------
# _websocket_checks -- valid
# ---------------------------------------------------------------------------


def _valid_websocket(tmp_path: Path, root_key: str = "channels") -> Path:
    """Helper: write a valid WebSocket contract and return its path."""
    f = tmp_path / "channels.yaml"
    data: dict[str, Any] = {
        root_key: {
            "chat": {
                "subscribe": True,
                "publish": True,
                "payload": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                },
            }
        }
    }
    f.write_text(yaml.dump(data), encoding="utf-8")
    return f


def test_websocket_checks_all_pass(tmp_path: Path) -> None:
    """All 8 WebSocket checks pass on a valid contract."""
    source = _valid_websocket(tmp_path)
    checks = _websocket_checks(source)
    assert len(checks) == 8
    assert all(ok for _, ok, _ in checks)


def test_websocket_check_names(tmp_path: Path) -> None:
    """WebSocket checks have the expected names in order."""
    source = _valid_websocket(tmp_path)
    names = [name for name, _, _ in _websocket_checks(source)]
    expected = [
        "source_exists",
        "root_channels_present",
        "channels_non_empty",
        "channel_objects",
        "payload_schema_present",
        "direction_or_message_present",
        "balanced_braces",
        "json_yaml_mapping",
    ]
    assert names == expected


# ---------------------------------------------------------------------------
# _websocket_checks -- flexible root keys and invalid cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("root_key", ["channels", "topics", "events", "messages"])
def test_websocket_flexible_root_keys(tmp_path: Path, root_key: str) -> None:
    """WebSocket checks accept channels, topics, events, or messages as root."""
    source = _valid_websocket(tmp_path, root_key=root_key)
    result = {name: ok for name, ok, _ in _websocket_checks(source)}
    assert result["root_channels_present"] is True


def test_websocket_missing_file(tmp_path: Path) -> None:
    """_websocket_checks raises FileNotFoundError for a missing file.

    The balanced_braces check calls source.read_text() unconditionally,
    so a missing file causes a FileNotFoundError after earlier checks
    have already been appended.
    """
    missing = tmp_path / "missing.yaml"
    with pytest.raises(FileNotFoundError):
        _websocket_checks(missing)


def test_websocket_no_root_key(tmp_path: Path) -> None:
    """root_channels_present fails when no recognized root key exists."""
    f = tmp_path / "norootkey.yaml"
    f.write_text(yaml.dump({"info": {"title": "T"}}), encoding="utf-8")
    result = {name: ok for name, ok, _ in _websocket_checks(f)}
    assert result["root_channels_present"] is False
    assert result["channels_non_empty"] is False


def test_websocket_empty_channels(tmp_path: Path) -> None:
    """channels_non_empty fails when channels is an empty dict."""
    f = tmp_path / "empty.yaml"
    f.write_text(yaml.dump({"channels": {}}), encoding="utf-8")
    result = {name: ok for name, ok, _ in _websocket_checks(f)}
    assert result["channels_non_empty"] is False


def test_websocket_channel_not_object(tmp_path: Path) -> None:
    """channel_objects fails when a channel value is a string, not dict."""
    f = tmp_path / "bad.yaml"
    f.write_text(yaml.dump({"channels": {"chat": "not_a_dict"}}), encoding="utf-8")
    result = {name: ok for name, ok, _ in _websocket_checks(f)}
    assert result["channel_objects"] is False


def test_websocket_no_payload(tmp_path: Path) -> None:
    """payload_schema_present fails when no payload/schema/message key exists."""
    f = tmp_path / "nopay.yaml"
    data: dict[str, Any] = {"channels": {"chat": {"subscribe": True}}}
    f.write_text(yaml.dump(data), encoding="utf-8")
    result = {name: ok for name, ok, _ in _websocket_checks(f)}
    assert result["payload_schema_present"] is False


def test_websocket_unbalanced_braces(tmp_path: Path) -> None:
    """balanced_braces fails when raw contract text has unbalanced braces."""
    f = tmp_path / "bad.yaml"
    f.write_text('channels:\n  chat:\n    payload: "{ unclosed"\n', encoding="utf-8")
    result = {name: ok for name, ok, _ in _websocket_checks(f)}
    assert result["balanced_braces"] is False


# ---------------------------------------------------------------------------
# lint_run dispatcher
# ---------------------------------------------------------------------------


def test_lint_run_graphql(tmp_path: Path) -> None:
    """_run dispatches to _graphql_checks for protocol 'graphql'."""
    schema = _valid_graphql(tmp_path)
    checks = lint_run("graphql", schema)
    assert len(checks) == 8
    assert all(ok for _, ok, _ in checks)


def test_lint_run_grpc(tmp_path: Path) -> None:
    """_run dispatches to _grpc_checks for protocol 'grpc'."""
    proto = _valid_proto(tmp_path)
    checks = lint_run("grpc", proto)
    assert len(checks) == 8
    assert all(ok for _, ok, _ in checks)


def test_lint_run_asyncapi(tmp_path: Path) -> None:
    """_run dispatches to _asyncapi_checks for protocol 'asyncapi'."""
    source = _valid_asyncapi(tmp_path)
    checks = lint_run("asyncapi", source)
    assert len(checks) == 8
    assert all(ok for _, ok, _ in checks)


def test_lint_run_websocket(tmp_path: Path) -> None:
    """_run dispatches to _websocket_checks for protocol 'websocket'."""
    source = _valid_websocket(tmp_path)
    checks = lint_run("websocket", source)
    assert len(checks) == 8
    assert all(ok for _, ok, _ in checks)


def test_lint_run_invalid_protocol(tmp_path: Path) -> None:
    """_run raises ValueError for an unsupported protocol."""
    f = tmp_path / "dummy.txt"
    f.write_text("dummy", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported protocol"):
        lint_run("rest", f)


# ---------------------------------------------------------------------------
# lint_main CLI
# ---------------------------------------------------------------------------


def test_lint_main_success_no_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """main() returns 0 for a valid contract without --json-report."""
    schema = _valid_graphql(tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        ["prog", "--protocol", "graphql", "--source", str(schema)],
    )
    assert lint_main() == 0


def test_lint_main_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """main() returns 1 when checks fail."""
    missing = tmp_path / "nope.graphql"
    monkeypatch.setattr(
        "sys.argv",
        ["prog", "--protocol", "graphql", "--source", str(missing)],
    )
    assert lint_main() == 1


def test_lint_main_json_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """main() writes a JSON report when --json-report is provided."""
    schema = _valid_graphql(tmp_path)
    report = tmp_path / "reports" / "lint_report.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "prog",
            "--protocol",
            "graphql",
            "--source",
            str(schema),
            "--json-report",
            str(report),
        ],
    )
    rc = lint_main()
    assert rc == 0
    assert report.exists()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["ok"] is True
    assert data["protocol"] == "graphql"
    assert data["checks_total"] == 8
    assert data["failed"] == []


def test_lint_main_json_report_with_failures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """JSON report records failures when checks do not pass."""
    empty = tmp_path / "empty.graphql"
    empty.write_text("", encoding="utf-8")
    report = tmp_path / "report.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "prog",
            "--protocol",
            "graphql",
            "--source",
            str(empty),
            "--json-report",
            str(report),
        ],
    )
    rc = lint_main()
    assert rc == 1
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["ok"] is False
    assert len(data["failed"]) > 0


def test_lint_main_grpc_protocol(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """main() works for gRPC protocol with a valid proto file."""
    proto = _valid_proto(tmp_path)
    report = tmp_path / "grpc_report.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "prog",
            "--protocol",
            "grpc",
            "--source",
            str(proto),
            "--json-report",
            str(report),
        ],
    )
    rc = lint_main()
    assert rc == 0
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["ok"] is True


# ---------------------------------------------------------------------------
# quality_run subprocess wrapper
# ---------------------------------------------------------------------------


def test_quality_run_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """_run returns ok=True when subprocess exits with 0."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
    result = quality_run("test_step", ["echo", "ok"], tmp_path)
    assert result["ok"] is True
    assert result["rc"] == 0
    assert result["step"] == "test_step"


def test_quality_run_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """_run returns ok=False when subprocess exits with non-zero."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
    result = quality_run("failing_step", ["false"], tmp_path)
    assert result["ok"] is False
    assert result["rc"] == 1


def test_quality_run_non_blocking(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """_run returns ok=True even for non-zero rc when non_blocking is True."""
    mock_result = MagicMock()
    mock_result.returncode = 2
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
    result = quality_run("nb_step", ["false"], tmp_path, non_blocking=True)
    assert result["ok"] is True
    assert result["rc"] == 2
    assert result["non_blocking"] is True


def test_quality_run_includes_command(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """_run includes the command list in the result dict."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
    cmd = ["python3", "some_script.py", "--flag"]
    result = quality_run("cmd_step", cmd, tmp_path)
    assert result["command"] == cmd


# ---------------------------------------------------------------------------
# _semantic_markers
# ---------------------------------------------------------------------------


def test_semantic_markers_graphql() -> None:
    """_semantic_markers returns expected markers for graphql."""
    markers = _semantic_markers("graphql")
    assert "semantic-fallback" in markers
    assert "simulated_response" in markers
    assert "Unknown query. Use:" in markers
    assert len(markers) == 3


def test_semantic_markers_grpc() -> None:
    """_semantic_markers returns expected markers for grpc."""
    markers = _semantic_markers("grpc")
    assert "UNIMPLEMENTED" in markers
    assert len(markers) == 3


def test_semantic_markers_asyncapi() -> None:
    """_semantic_markers returns expected markers for asyncapi."""
    markers = _semantic_markers("asyncapi")
    assert "Sandbox semantic mode" in markers
    assert "project.updated" in markers
    assert len(markers) == 4


def test_semantic_markers_websocket() -> None:
    """_semantic_markers returns expected markers for websocket."""
    markers = _semantic_markers("websocket")
    assert "subscribe" in markers
    assert "publish" in markers
    assert "list_projects" in markers
    assert len(markers) == 5


def test_semantic_markers_unknown_protocol() -> None:
    """_semantic_markers returns empty list for unknown protocol."""
    markers = _semantic_markers("rest")
    assert markers == []


# ---------------------------------------------------------------------------
# _forbidden_semantic_patterns
# ---------------------------------------------------------------------------


def test_forbidden_patterns_asyncapi() -> None:
    """_forbidden_semantic_patterns returns patterns for asyncapi."""
    patterns = _forbidden_semantic_patterns("asyncapi")
    assert len(patterns) == 2
    assert all(isinstance(p, str) for p in patterns)


def test_forbidden_patterns_websocket() -> None:
    """_forbidden_semantic_patterns returns patterns for websocket."""
    patterns = _forbidden_semantic_patterns("websocket")
    assert len(patterns) == 2


def test_forbidden_patterns_graphql_empty() -> None:
    """_forbidden_semantic_patterns returns empty for graphql (no forbidden)."""
    assert _forbidden_semantic_patterns("graphql") == []


def test_forbidden_patterns_grpc_empty() -> None:
    """_forbidden_semantic_patterns returns empty for grpc (no forbidden)."""
    assert _forbidden_semantic_patterns("grpc") == []


def test_forbidden_patterns_unknown_protocol() -> None:
    """_forbidden_semantic_patterns returns empty for unknown protocol."""
    assert _forbidden_semantic_patterns("unknown") == []


# ---------------------------------------------------------------------------
# quality_main -- semantic checks
# ---------------------------------------------------------------------------


def test_quality_main_semantic_markers_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """main() passes semantic_consistency when all markers exist in doc."""
    doc = tmp_path / "doc.md"
    markers = _semantic_markers("graphql")
    content = "---\ntitle: Test\n---\n" + "\n".join(markers) + "\n"
    doc.write_text(content, encoding="utf-8")

    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    mock_result = MagicMock()
    mock_result.returncode = 0
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
    monkeypatch.setattr(
        "sys.argv",
        [
            "prog",
            "--protocol",
            "graphql",
            "--generated-doc",
            str(doc),
            "--docs-root",
            str(tmp_path),
            "--reports-dir",
            str(reports_dir),
            "--no-rag-refresh",
        ],
    )

    # The --no-rag-refresh flag does not exist, so we patch args after parse
    # Instead, create the marker file to skip RAG refresh
    (reports_dir / ".protocol_rag_refresh_done").write_text("done\n", encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "prog",
            "--protocol",
            "graphql",
            "--generated-doc",
            str(doc),
            "--docs-root",
            str(tmp_path),
            "--reports-dir",
            str(reports_dir),
        ],
    )

    rc = quality_main()
    report_file = reports_dir / "graphql_quality_suite_report.json"
    assert report_file.exists()
    data = json.loads(report_file.read_text(encoding="utf-8"))
    semantic_step = next(
        (s for s in data["steps"] if s["step"] == "semantic_consistency"), None
    )
    assert semantic_step is not None
    assert semantic_step["ok"] is True


def test_quality_main_semantic_markers_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """main() fails semantic_consistency when markers are absent from doc."""
    doc = tmp_path / "doc.md"
    doc.write_text("---\ntitle: Empty Doc\n---\nNo markers here.\n", encoding="utf-8")

    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / ".protocol_rag_refresh_done").write_text("done\n", encoding="utf-8")

    mock_result = MagicMock()
    mock_result.returncode = 0
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
    monkeypatch.setattr(
        "sys.argv",
        [
            "prog",
            "--protocol",
            "grpc",
            "--generated-doc",
            str(doc),
            "--docs-root",
            str(tmp_path),
            "--reports-dir",
            str(reports_dir),
        ],
    )

    rc = quality_main()
    assert rc == 1
    data = json.loads(
        (reports_dir / "grpc_quality_suite_report.json").read_text(encoding="utf-8")
    )
    semantic_step = next(
        (s for s in data["steps"] if s["step"] == "semantic_consistency"), None
    )
    assert semantic_step is not None
    assert semantic_step["ok"] is False
    assert len(semantic_step["missing_markers"]) > 0


def test_quality_main_missing_doc_semantic_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """main() records semantic failure when generated doc does not exist."""
    missing_doc = tmp_path / "nonexistent.md"
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / ".protocol_rag_refresh_done").write_text("done\n", encoding="utf-8")

    mock_result = MagicMock()
    mock_result.returncode = 0
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
    monkeypatch.setattr(
        "sys.argv",
        [
            "prog",
            "--protocol",
            "asyncapi",
            "--generated-doc",
            str(missing_doc),
            "--docs-root",
            str(tmp_path),
            "--reports-dir",
            str(reports_dir),
        ],
    )

    rc = quality_main()
    assert rc == 1
    data = json.loads(
        (reports_dir / "asyncapi_quality_suite_report.json").read_text(encoding="utf-8")
    )
    semantic_step = next(
        (s for s in data["steps"] if s["step"] == "semantic_consistency"), None
    )
    assert semantic_step is not None
    assert semantic_step["ok"] is False


# ---------------------------------------------------------------------------
# quality_main -- forbidden patterns
# ---------------------------------------------------------------------------


def test_quality_main_forbidden_patterns_detected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """main() fails semantic_conflict_scan when forbidden patterns exist."""
    forbidden = _forbidden_semantic_patterns("asyncapi")
    markers = _semantic_markers("asyncapi")
    content = "---\ntitle: Test\n---\n" + "\n".join(markers) + "\n" + forbidden[0] + "\n"
    doc = tmp_path / "doc.md"
    doc.write_text(content, encoding="utf-8")

    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / ".protocol_rag_refresh_done").write_text("done\n", encoding="utf-8")

    mock_result = MagicMock()
    mock_result.returncode = 0
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
    monkeypatch.setattr(
        "sys.argv",
        [
            "prog",
            "--protocol",
            "asyncapi",
            "--generated-doc",
            str(doc),
            "--docs-root",
            str(tmp_path),
            "--reports-dir",
            str(reports_dir),
        ],
    )

    rc = quality_main()
    assert rc == 1
    data = json.loads(
        (reports_dir / "asyncapi_quality_suite_report.json").read_text(encoding="utf-8")
    )
    conflict_step = next(
        (s for s in data["steps"] if s["step"] == "semantic_conflict_scan"), None
    )
    assert conflict_step is not None
    assert conflict_step["ok"] is False
    assert len(conflict_step["forbidden_patterns_found"]) > 0


def test_quality_main_no_forbidden_patterns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """main() passes semantic_conflict_scan when no forbidden patterns exist."""
    markers = _semantic_markers("graphql")
    doc = tmp_path / "doc.md"
    doc.write_text("---\ntitle: T\n---\n" + "\n".join(markers) + "\n", encoding="utf-8")

    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / ".protocol_rag_refresh_done").write_text("done\n", encoding="utf-8")

    mock_result = MagicMock()
    mock_result.returncode = 0
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
    monkeypatch.setattr(
        "sys.argv",
        [
            "prog",
            "--protocol",
            "graphql",
            "--generated-doc",
            str(doc),
            "--docs-root",
            str(tmp_path),
            "--reports-dir",
            str(reports_dir),
        ],
    )

    rc = quality_main()
    data = json.loads(
        (reports_dir / "graphql_quality_suite_report.json").read_text(encoding="utf-8")
    )
    conflict_step = next(
        (s for s in data["steps"] if s["step"] == "semantic_conflict_scan"), None
    )
    assert conflict_step is not None
    assert conflict_step["ok"] is True


# ---------------------------------------------------------------------------
# quality_main -- RAG marker deduplication
# ---------------------------------------------------------------------------


def test_quality_main_rag_marker_skips_second_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """main() skips RAG refresh when marker file already exists."""
    markers = _semantic_markers("websocket")
    doc = tmp_path / "doc.md"
    doc.write_text("---\ntitle: T\n---\n" + "\n".join(markers) + "\n", encoding="utf-8")

    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    marker = reports_dir / ".protocol_rag_refresh_done"
    marker.write_text("done\n", encoding="utf-8")

    mock_result = MagicMock()
    mock_result.returncode = 0
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
    monkeypatch.setattr(
        "sys.argv",
        [
            "prog",
            "--protocol",
            "websocket",
            "--generated-doc",
            str(doc),
            "--docs-root",
            str(tmp_path),
            "--reports-dir",
            str(reports_dir),
        ],
    )

    rc = quality_main()
    data = json.loads(
        (reports_dir / "websocket_quality_suite_report.json").read_text(encoding="utf-8")
    )
    rag_step = next(
        (s for s in data["steps"] if s["step"] == "rag_refresh"), None
    )
    assert rag_step is not None
    assert rag_step["ok"] is True
    assert "already refreshed" in str(rag_step["command"])


# ---------------------------------------------------------------------------
# quality_main -- report structure
# ---------------------------------------------------------------------------


def test_quality_main_report_structure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """main() produces a report with expected top-level keys."""
    doc = tmp_path / "doc.md"
    doc.write_text("---\ntitle: T\n---\nContent.\n", encoding="utf-8")

    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / ".protocol_rag_refresh_done").write_text("done\n", encoding="utf-8")

    mock_result = MagicMock()
    mock_result.returncode = 0
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
    monkeypatch.setattr(
        "sys.argv",
        [
            "prog",
            "--protocol",
            "grpc",
            "--generated-doc",
            str(doc),
            "--docs-root",
            str(tmp_path),
            "--reports-dir",
            str(reports_dir),
        ],
    )

    quality_main()
    data = json.loads(
        (reports_dir / "grpc_quality_suite_report.json").read_text(encoding="utf-8")
    )
    assert "protocol" in data
    assert "generated_doc" in data
    assert "docs_root" in data
    assert "steps" in data
    assert "failed_steps" in data
    assert "ok" in data
    assert data["protocol"] == "grpc"


def test_quality_main_custom_json_report_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """main() writes to custom --json-report path when provided."""
    doc = tmp_path / "doc.md"
    doc.write_text("---\ntitle: T\n---\nContent.\n", encoding="utf-8")

    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / ".protocol_rag_refresh_done").write_text("done\n", encoding="utf-8")

    custom_report = tmp_path / "custom" / "my_report.json"

    mock_result = MagicMock()
    mock_result.returncode = 0
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
    monkeypatch.setattr(
        "sys.argv",
        [
            "prog",
            "--protocol",
            "graphql",
            "--generated-doc",
            str(doc),
            "--docs-root",
            str(tmp_path),
            "--reports-dir",
            str(reports_dir),
            "--json-report",
            str(custom_report),
        ],
    )

    quality_main()
    assert custom_report.exists()
    data = json.loads(custom_report.read_text(encoding="utf-8"))
    assert data["protocol"] == "graphql"

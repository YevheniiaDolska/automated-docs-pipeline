"""Tests for protocol contract validators (AsyncAPI, GraphQL, gRPC, WebSocket).

Covers functional happy-path, error detection, security injection patterns,
edge cases, CLI main() entry points, and file-not-found scenarios.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_asyncapi_contract import (
    _load as asyncapi_load,
    _message_has_payload as asyncapi_msg_has_payload,
    main as asyncapi_main,
    validate as asyncapi_validate,
)
from scripts.validate_graphql_contract import (
    _extract_blocks as graphql_extract_blocks,
    _extract_schema_root_types as graphql_extract_schema_roots,
    main as graphql_main,
    validate_schema as graphql_validate,
)
from scripts.validate_proto_contract import (
    _collect_proto_files as proto_collect,
    _validate_proto_text as proto_validate_text,
    main as proto_main,
)
from scripts.validate_websocket_contract import (
    _entry_has_payload as ws_entry_has_payload,
    _extract_channels as ws_extract_channels,
    _load as ws_load,
    main as ws_main,
    validate as ws_validate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_asyncapi() -> dict:
    """Return a minimal valid AsyncAPI payload."""
    return {
        "asyncapi": "2.6.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "channels": {
            "user/signup": {
                "publish": {
                    "message": {"payload": {"type": "object"}}
                }
            }
        },
    }


def _minimal_graphql() -> str:
    """Return a minimal valid GraphQL SDL string."""
    return "type Query {\n  hello: String\n}\n"


def _minimal_proto() -> str:
    """Return a minimal valid proto3 text."""
    return (
        'syntax = "proto3";\n\n'
        "service Greeter {\n"
        "  rpc SayHello (HelloRequest) returns (HelloReply);\n"
        "}\n\n"
        "message HelloRequest {\n  string name = 1;\n}\n"
        "message HelloReply {\n  string reply = 1;\n}\n"
    )


def _minimal_ws() -> dict:
    """Return a minimal valid WebSocket contract payload."""
    return {
        "channels": {
            "chat": {
                "publish": {"payload": {"type": "object"}}
            }
        }
    }


# ===================================================================
# AsyncAPI validator tests
# ===================================================================

class TestAsyncAPILoad:
    """Tests for AsyncAPI _load function."""

    def test_load_yaml_file(self, tmp_path: Path) -> None:
        """Valid YAML file loads successfully."""
        f = tmp_path / "spec.yaml"
        f.write_text(yaml.dump(_minimal_asyncapi()), encoding="utf-8")
        data = asyncapi_load(f)
        assert data["asyncapi"] == "2.6.0"

    def test_load_json_file(self, tmp_path: Path) -> None:
        """Valid JSON file loads successfully."""
        f = tmp_path / "spec.json"
        f.write_text(json.dumps(_minimal_asyncapi()), encoding="utf-8")
        data = asyncapi_load(f)
        assert data["asyncapi"] == "2.6.0"

    def test_load_non_dict_raises(self, tmp_path: Path) -> None:
        """YAML file with a list at root raises ValueError."""
        f = tmp_path / "bad.yaml"
        f.write_text("- item1\n- item2\n", encoding="utf-8")
        with pytest.raises(ValueError, match="must be a mapping"):
            asyncapi_load(f)


class TestAsyncAPIMessageHasPayload:
    """Tests for AsyncAPI _message_has_payload helper."""

    def test_direct_payload(self) -> None:
        """Message with direct payload key returns True."""
        assert asyncapi_msg_has_payload({"payload": {"type": "string"}}) is True

    def test_oneof_payload(self) -> None:
        """Message with oneOf containing payload returns True."""
        msg = {"oneOf": [{"payload": {"type": "string"}}]}
        assert asyncapi_msg_has_payload(msg) is True

    def test_oneof_without_payload(self) -> None:
        """Message with oneOf items lacking payload returns False."""
        msg = {"oneOf": [{"summary": "no payload here"}]}
        assert asyncapi_msg_has_payload(msg) is False

    def test_non_dict_message(self) -> None:
        """Non-dict message returns False."""
        assert asyncapi_msg_has_payload("not a dict") is False

    def test_empty_dict(self) -> None:
        """Empty dict message returns False."""
        assert asyncapi_msg_has_payload({}) is False


class TestAsyncAPIValidate:
    """Tests for AsyncAPI validate function."""

    def test_valid_contract_passes(self) -> None:
        """Minimal valid contract produces no errors."""
        errors = asyncapi_validate(_minimal_asyncapi())
        assert errors == []

    def test_missing_required_keys(self) -> None:
        """Empty dict reports missing asyncapi, info, channels."""
        errors = asyncapi_validate({})
        assert any("asyncapi" in e for e in errors)
        assert any("info" in e for e in errors)
        assert any("channels" in e for e in errors)

    def test_asyncapi_version_must_be_string(self) -> None:
        """Numeric asyncapi version triggers error."""
        payload = _minimal_asyncapi()
        payload["asyncapi"] = 2
        errors = asyncapi_validate(payload)
        assert any("version must be a string" in e for e in errors)

    def test_info_must_be_object(self) -> None:
        """Non-dict info triggers error."""
        payload = _minimal_asyncapi()
        payload["info"] = "bad"
        errors = asyncapi_validate(payload)
        assert any("`info` must be an object" in e for e in errors)

    def test_info_missing_title(self) -> None:
        """Missing info.title triggers error."""
        payload = _minimal_asyncapi()
        payload["info"] = {"version": "1.0.0"}
        errors = asyncapi_validate(payload)
        assert any("info.title" in e for e in errors)

    def test_info_missing_version(self) -> None:
        """Missing info.version triggers error."""
        payload = _minimal_asyncapi()
        payload["info"] = {"title": "Test"}
        errors = asyncapi_validate(payload)
        assert any("info.version" in e for e in errors)

    def test_channels_must_be_object(self) -> None:
        """Non-dict channels triggers error."""
        payload = _minimal_asyncapi()
        payload["channels"] = ["bad"]
        errors = asyncapi_validate(payload)
        assert any("`channels` must be an object" in e for e in errors)

    def test_empty_channels(self) -> None:
        """Empty channels dict triggers error."""
        payload = _minimal_asyncapi()
        payload["channels"] = {}
        errors = asyncapi_validate(payload)
        assert any("must not be empty" in e for e in errors)

    def test_channel_not_object(self) -> None:
        """Channel value that is not a dict triggers error."""
        payload = _minimal_asyncapi()
        payload["channels"] = {"bad_channel": "not_a_dict"}
        errors = asyncapi_validate(payload)
        assert any("bad_channel" in e and "must be an object" in e for e in errors)

    def test_channel_missing_operation(self) -> None:
        """Channel without publish or subscribe triggers error."""
        payload = _minimal_asyncapi()
        payload["channels"] = {"empty_ch": {}}
        errors = asyncapi_validate(payload)
        assert any("at least one operation" in e for e in errors)

    def test_operation_not_object(self) -> None:
        """Non-dict operation triggers error."""
        payload = _minimal_asyncapi()
        payload["channels"] = {"ch": {"publish": "not_a_dict"}}
        errors = asyncapi_validate(payload)
        assert any("operation `publish` must be an object" in e for e in errors)

    def test_operation_missing_payload(self) -> None:
        """Operation without message payload triggers error."""
        payload = _minimal_asyncapi()
        payload["channels"] = {"ch": {"subscribe": {"message": {}}}}
        errors = asyncapi_validate(payload)
        assert any("must define message payload" in e for e in errors)

    def test_subscribe_with_oneof_payload(self) -> None:
        """Subscribe operation with oneOf payload passes."""
        payload = _minimal_asyncapi()
        payload["channels"] = {
            "events": {
                "subscribe": {
                    "message": {"oneOf": [{"payload": {"type": "string"}}]}
                }
            }
        }
        errors = asyncapi_validate(payload)
        assert errors == []


class TestAsyncAPIMain:
    """Tests for AsyncAPI CLI main() entry point."""

    def test_main_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() returns 0 for a valid spec file."""
        f = tmp_path / "valid.yaml"
        f.write_text(yaml.dump(_minimal_asyncapi()), encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["validate_asyncapi_contract.py", str(f)])
        assert asyncapi_main() == 0

    def test_main_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() returns 1 for an invalid spec file."""
        f = tmp_path / "bad.yaml"
        f.write_text(yaml.dump({"asyncapi": "2.0.0"}), encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["validate_asyncapi_contract.py", str(f)])
        assert asyncapi_main() == 1

    def test_main_file_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() raises FileNotFoundError for missing file."""
        monkeypatch.setattr("sys.argv", ["validate_asyncapi_contract.py", "/no/such/file.yaml"])
        with pytest.raises(FileNotFoundError, match="not found"):
            asyncapi_main()


# ===================================================================
# GraphQL validator tests
# ===================================================================

class TestGraphQLExtractBlocks:
    """Tests for GraphQL _extract_blocks helper."""

    def test_extract_type_blocks(self) -> None:
        """Extracts named type blocks from SDL."""
        schema = "type Query {\n  hello: String\n}\ntype User {\n  id: ID!\n}\n"
        blocks = graphql_extract_blocks(schema, "type")
        names = [name for name, _ in blocks]
        assert "Query" in names
        assert "User" in names

    def test_extract_enum_blocks(self) -> None:
        """Extracts enum blocks from SDL."""
        schema = "enum Status {\n  ACTIVE\n  INACTIVE\n}\n"
        blocks = graphql_extract_blocks(schema, "enum")
        assert len(blocks) == 1
        assert blocks[0][0] == "Status"

    def test_extract_no_matches(self) -> None:
        """Returns empty list when no blocks of the kind exist."""
        blocks = graphql_extract_blocks("type Query { hello: String }", "enum")
        assert blocks == []


class TestGraphQLExtractSchemaRoots:
    """Tests for GraphQL _extract_schema_root_types helper."""

    def test_extract_schema_root(self) -> None:
        """Extracts query and mutation root types from schema block."""
        schema = "schema {\n  query: RootQuery\n  mutation: RootMutation\n}\n"
        roots = graphql_extract_schema_roots(schema)
        assert roots["query"] == "RootQuery"
        assert roots["mutation"] == "RootMutation"

    def test_no_schema_block(self) -> None:
        """Returns empty dict when no explicit schema block exists."""
        roots = graphql_extract_schema_roots("type Query { hello: String }")
        assert roots == {}

    def test_comments_in_schema_block(self) -> None:
        """Comments inside schema block are skipped."""
        schema = "schema {\n  # comment\n  query: Query\n}\n"
        roots = graphql_extract_schema_roots(schema)
        assert roots.get("query") == "Query"


class TestGraphQLValidateSchema:
    """Tests for GraphQL validate_schema function."""

    def test_valid_schema_passes(self) -> None:
        """Minimal valid schema produces no errors."""
        errors = graphql_validate(_minimal_graphql())
        assert errors == []

    def test_empty_schema(self) -> None:
        """Empty schema returns single error."""
        errors = graphql_validate("")
        assert errors == ["GraphQL schema is empty."]

    def test_whitespace_only(self) -> None:
        """Whitespace-only schema counts as empty."""
        errors = graphql_validate("   \n\t  ")
        assert errors == ["GraphQL schema is empty."]

    def test_missing_root_type(self) -> None:
        """Schema without type Query or schema block triggers error."""
        schema = "type User {\n  id: ID!\n}\n"
        errors = graphql_validate(schema)
        assert any("type Query" in e for e in errors)

    def test_unbalanced_braces(self) -> None:
        """Unbalanced braces trigger error."""
        schema = "type Query {\n  hello: String\n"
        errors = graphql_validate(schema)
        assert any("unbalanced braces" in e for e in errors)

    def test_unbalanced_parentheses(self) -> None:
        """Unbalanced parentheses trigger error."""
        schema = "type Query {\n  user(id: ID!: User\n}\n"
        errors = graphql_validate(schema)
        assert any("unbalanced parentheses" in e for e in errors)

    def test_duplicate_type_declaration(self) -> None:
        """Duplicate type names trigger error."""
        schema = (
            "type Query {\n  hello: String\n}\n"
            "type User {\n  id: ID!\n}\n"
            "type User {\n  name: String\n}\n"
        )
        errors = graphql_validate(schema)
        assert any("Duplicate type" in e and "User" in e for e in errors)

    def test_duplicate_field_in_type(self) -> None:
        """Duplicate field names within a type trigger error."""
        schema = "type Query {\n  hello: String\n  hello: Int\n}\n"
        errors = graphql_validate(schema)
        assert any("duplicate field" in e and "hello" in e for e in errors)

    def test_schema_root_references_missing_type(self) -> None:
        """Schema root referencing a non-existent type triggers error."""
        schema = (
            "schema {\n  query: RootQuery\n}\n"
            "type User {\n  id: ID!\n}\n"
        )
        errors = graphql_validate(schema)
        assert any("missing type" in e and "RootQuery" in e for e in errors)

    def test_valid_explicit_schema_block(self) -> None:
        """Valid schema with explicit schema block passes."""
        schema = (
            "schema {\n  query: MyQuery\n}\n"
            "type MyQuery {\n  hello: String\n}\n"
        )
        errors = graphql_validate(schema)
        assert errors == []

    def test_input_type_duplicate_fields(self) -> None:
        """Duplicate fields in input type trigger error."""
        schema = (
            "type Query {\n  hello: String\n}\n"
            "input CreateUser {\n  name: String\n  name: String\n}\n"
        )
        errors = graphql_validate(schema)
        assert any("duplicate field" in e and "name" in e for e in errors)

    def test_interface_duplicate_fields(self) -> None:
        """Duplicate fields in interface trigger error."""
        schema = (
            "type Query {\n  hello: String\n}\n"
            "interface Node {\n  id: ID!\n  id: ID!\n}\n"
        )
        errors = graphql_validate(schema)
        assert any("duplicate field" in e for e in errors)

    def test_security_injection_in_schema(self) -> None:
        """Schema with script injection in field names does not crash."""
        schema = 'type Query {\n  hello: String\n}\n# <script>alert("xss")</script>\n'
        errors = graphql_validate(schema)
        assert errors == []


class TestGraphQLMain:
    """Tests for GraphQL CLI main() entry point."""

    def test_main_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() returns 0 for a valid schema file."""
        f = tmp_path / "schema.graphql"
        f.write_text(_minimal_graphql(), encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["validate_graphql_contract.py", str(f)])
        assert graphql_main() == 0

    def test_main_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() returns 1 for an invalid schema file."""
        f = tmp_path / "bad.graphql"
        f.write_text("", encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["validate_graphql_contract.py", str(f)])
        assert graphql_main() == 1

    def test_main_file_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() raises FileNotFoundError for missing file."""
        monkeypatch.setattr("sys.argv", ["validate_graphql_contract.py", "/no/schema.graphql"])
        with pytest.raises(FileNotFoundError, match="not found"):
            graphql_main()


# ===================================================================
# gRPC proto validator tests
# ===================================================================

class TestProtoCollectFiles:
    """Tests for gRPC _collect_proto_files helper."""

    def test_collect_single_file(self, tmp_path: Path) -> None:
        """Collects a single .proto file."""
        f = tmp_path / "svc.proto"
        f.write_text(_minimal_proto(), encoding="utf-8")
        files = proto_collect([str(f)])
        assert len(files) == 1
        assert files[0].name == "svc.proto"

    def test_collect_from_directory(self, tmp_path: Path) -> None:
        """Collects all .proto files recursively from a directory."""
        sub = tmp_path / "protos"
        sub.mkdir()
        (sub / "a.proto").write_text(_minimal_proto(), encoding="utf-8")
        (sub / "b.proto").write_text(_minimal_proto(), encoding="utf-8")
        (sub / "readme.txt").write_text("not a proto", encoding="utf-8")
        files = proto_collect([str(sub)])
        assert len(files) == 2
        assert all(f.suffix == ".proto" for f in files)

    def test_collect_ignores_non_proto(self, tmp_path: Path) -> None:
        """Non-.proto files are ignored."""
        f = tmp_path / "notes.txt"
        f.write_text("some text", encoding="utf-8")
        files = proto_collect([str(f)])
        assert files == []

    def test_collect_empty_directory(self, tmp_path: Path) -> None:
        """Empty directory returns empty list."""
        d = tmp_path / "empty"
        d.mkdir()
        files = proto_collect([str(d)])
        assert files == []


class TestProtoValidateText:
    """Tests for gRPC _validate_proto_text function."""

    def test_valid_proto_passes(self, tmp_path: Path) -> None:
        """Minimal valid proto3 produces no errors."""
        p = tmp_path / "ok.proto"
        errors = proto_validate_text(_minimal_proto(), p)
        assert errors == []

    def test_missing_syntax(self, tmp_path: Path) -> None:
        """Proto without syntax declaration triggers error."""
        text = "message Foo { string bar = 1; }\n"
        errors = proto_validate_text(text, tmp_path / "bad.proto")
        assert any("syntax" in e for e in errors)

    def test_unbalanced_braces(self, tmp_path: Path) -> None:
        """Unbalanced braces trigger error."""
        text = 'syntax = "proto3";\nmessage Foo {\n  string bar = 1;\n'
        errors = proto_validate_text(text, tmp_path / "bad.proto")
        assert any("unbalanced braces" in e for e in errors)

    def test_no_declarations(self, tmp_path: Path) -> None:
        """Proto without service/message/enum triggers error."""
        text = 'syntax = "proto3";\n'
        errors = proto_validate_text(text, tmp_path / "empty.proto")
        assert any("service/message/enum" in e for e in errors)

    def test_duplicate_message(self, tmp_path: Path) -> None:
        """Duplicate message names trigger error."""
        text = (
            'syntax = "proto3";\n'
            "message Foo { string a = 1; }\n"
            "message Foo { string b = 1; }\n"
        )
        errors = proto_validate_text(text, tmp_path / "dup.proto")
        assert any("duplicate declaration" in e.lower() and "Foo" in e for e in errors)

    def test_duplicate_rpc_in_service(self, tmp_path: Path) -> None:
        """Duplicate rpc names within a service trigger error."""
        text = (
            'syntax = "proto3";\n'
            "service Svc {\n"
            "  rpc Do (Req) returns (Res);\n"
            "  rpc Do (Req) returns (Res);\n"
            "}\n"
            "message Req { string x = 1; }\n"
            "message Res { string y = 1; }\n"
        )
        errors = proto_validate_text(text, tmp_path / "dup_rpc.proto")
        assert any("duplicate rpc" in e.lower() for e in errors)

    def test_service_no_rpc(self, tmp_path: Path) -> None:
        """Service without rpc declarations triggers error."""
        text = (
            'syntax = "proto3";\n'
            "service Empty {\n}\n"
            "message Msg { string a = 1; }\n"
        )
        errors = proto_validate_text(text, tmp_path / "norpc.proto")
        assert any("no valid rpc" in e.lower() for e in errors)

    def test_proto3_required_field(self, tmp_path: Path) -> None:
        """Proto3 with required field label triggers error."""
        text = (
            'syntax = "proto3";\n'
            "message Bad {\n  required string name = 1;\n}\n"
        )
        errors = proto_validate_text(text, tmp_path / "req.proto")
        assert any("required" in e.lower() and "proto3" in e.lower() for e in errors)

    def test_proto2_required_field_allowed(self, tmp_path: Path) -> None:
        """Proto2 with required field label does not trigger proto3-specific error."""
        text = (
            'syntax = "proto2";\n'
            "message Msg {\n  required string name = 1;\n}\n"
        )
        errors = proto_validate_text(text, tmp_path / "p2.proto")
        assert not any("required" in e.lower() and "proto3" in e.lower() for e in errors)

    def test_security_sql_injection_comment(self, tmp_path: Path) -> None:
        """Proto file with SQL injection in comment does not crash."""
        text = (
            'syntax = "proto3";\n'
            "// DROP TABLE users; --\n"
            "message Msg { string a = 1; }\n"
        )
        errors = proto_validate_text(text, tmp_path / "inject.proto")
        assert errors == []


class TestProtoMain:
    """Tests for gRPC CLI main() entry point."""

    def test_main_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() returns 0 for a valid proto file."""
        f = tmp_path / "ok.proto"
        f.write_text(_minimal_proto(), encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["validate_proto_contract.py", "--proto", str(f)])
        assert proto_main() == 0

    def test_main_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() returns 1 for an invalid proto file."""
        f = tmp_path / "bad.proto"
        f.write_text("garbage\n", encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["validate_proto_contract.py", "--proto", str(f)])
        assert proto_main() == 1

    def test_main_no_files_found(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() raises FileNotFoundError when no .proto files match."""
        d = tmp_path / "empty"
        d.mkdir()
        monkeypatch.setattr("sys.argv", ["validate_proto_contract.py", "--proto", str(d)])
        with pytest.raises(FileNotFoundError, match="No .proto files"):
            proto_main()

    def test_main_directory_input(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() accepts a directory containing proto files."""
        d = tmp_path / "protos"
        d.mkdir()
        (d / "svc.proto").write_text(_minimal_proto(), encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["validate_proto_contract.py", "--proto", str(d)])
        assert proto_main() == 0


# ===================================================================
# WebSocket validator tests
# ===================================================================

class TestWSLoad:
    """Tests for WebSocket _load function."""

    def test_load_yaml(self, tmp_path: Path) -> None:
        """Valid YAML file loads successfully."""
        f = tmp_path / "ws.yaml"
        f.write_text(yaml.dump(_minimal_ws()), encoding="utf-8")
        data = ws_load(f)
        assert "channels" in data

    def test_load_json(self, tmp_path: Path) -> None:
        """Valid JSON file loads successfully."""
        f = tmp_path / "ws.json"
        f.write_text(json.dumps(_minimal_ws()), encoding="utf-8")
        data = ws_load(f)
        assert "channels" in data

    def test_load_non_dict_raises(self, tmp_path: Path) -> None:
        """Non-dict root raises ValueError."""
        f = tmp_path / "bad.yaml"
        f.write_text('"just a string"', encoding="utf-8")
        with pytest.raises(ValueError, match="must be a mapping"):
            ws_load(f)


class TestWSExtractChannels:
    """Tests for WebSocket _extract_channels helper."""

    def test_channels_key(self) -> None:
        """Extracts from the 'channels' root key."""
        key, channels = ws_extract_channels({"channels": {"a": {}}})
        assert key == "channels"
        assert "a" in channels

    def test_topics_key(self) -> None:
        """Extracts from the 'topics' root key."""
        key, channels = ws_extract_channels({"topics": {"t1": {}}})
        assert key == "topics"

    def test_events_key(self) -> None:
        """Extracts from the 'events' root key."""
        key, channels = ws_extract_channels({"events": {"e1": {}}})
        assert key == "events"

    def test_messages_key(self) -> None:
        """Extracts from the 'messages' root key."""
        key, channels = ws_extract_channels({"messages": {"m1": {}}})
        assert key == "messages"

    def test_no_recognized_key(self) -> None:
        """Returns empty key and dict when no recognized root key exists."""
        key, channels = ws_extract_channels({"other": {}})
        assert key == ""
        assert channels == {}

    def test_non_dict_value_skipped(self) -> None:
        """Non-dict value for a recognized key is skipped."""
        key, channels = ws_extract_channels({"channels": ["not", "a", "dict"]})
        assert key == ""


class TestWSEntryHasPayload:
    """Tests for WebSocket _entry_has_payload helper."""

    def test_direct_payload(self) -> None:
        """Entry with direct payload key returns True."""
        assert ws_entry_has_payload({"payload": {}}) is True

    def test_direct_schema(self) -> None:
        """Entry with direct schema key returns True."""
        assert ws_entry_has_payload({"schema": {}}) is True

    def test_direct_message(self) -> None:
        """Entry with direct message key returns True."""
        assert ws_entry_has_payload({"message": {}}) is True

    def test_nested_in_direction(self) -> None:
        """Payload nested inside a direction block returns True."""
        entry = {"publish": {"payload": {"type": "string"}}}
        assert ws_entry_has_payload(entry) is True

    def test_nested_schema_in_subscribe(self) -> None:
        """Schema nested inside subscribe block returns True."""
        entry = {"subscribe": {"schema": {"type": "object"}}}
        assert ws_entry_has_payload(entry) is True

    def test_no_payload_anywhere(self) -> None:
        """Entry without any payload/schema/message returns False."""
        assert ws_entry_has_payload({"description": "nothing useful"}) is False

    def test_direction_block_non_dict(self) -> None:
        """Non-dict direction block does not count as having payload."""
        entry = {"publish": "not_a_dict"}
        assert ws_entry_has_payload(entry) is False


class TestWSValidate:
    """Tests for WebSocket validate function."""

    def test_valid_contract_passes(self) -> None:
        """Minimal valid contract produces no errors."""
        errors = ws_validate(_minimal_ws())
        assert errors == []

    def test_no_root_key(self) -> None:
        """Missing channels/topics/events/messages triggers error."""
        errors = ws_validate({"info": "something"})
        assert any("channels/topics/events/messages" in e for e in errors)

    def test_empty_channels(self) -> None:
        """Empty channels dict triggers error."""
        errors = ws_validate({"channels": {}})
        assert any("must not be empty" in e for e in errors)

    def test_channel_not_object(self) -> None:
        """Channel value not a dict triggers error."""
        errors = ws_validate({"channels": {"bad": "string"}})
        assert any("must be an object" in e for e in errors)

    def test_channel_missing_payload(self) -> None:
        """Channel without payload/schema/message triggers error."""
        errors = ws_validate({"channels": {"ch": {"description": "no data"}}})
        assert any("must define payload" in e for e in errors)

    def test_topics_root_key_valid(self) -> None:
        """Contract using 'topics' root key with payload passes."""
        payload = {"topics": {"t1": {"payload": {"type": "string"}}}}
        errors = ws_validate(payload)
        assert errors == []

    def test_events_root_key_valid(self) -> None:
        """Contract using 'events' root key with schema passes."""
        payload = {"events": {"e1": {"schema": {"type": "object"}}}}
        errors = ws_validate(payload)
        assert errors == []

    def test_messages_root_key_valid(self) -> None:
        """Contract using 'messages' root key with message passes."""
        payload = {"messages": {"m1": {"message": {"type": "string"}}}}
        errors = ws_validate(payload)
        assert errors == []

    def test_direction_block_with_payload(self) -> None:
        """Payload nested inside a send direction block passes."""
        payload = {"channels": {"ch": {"send": {"payload": {"type": "object"}}}}}
        errors = ws_validate(payload)
        assert errors == []

    def test_security_yaml_bomb(self, tmp_path: Path) -> None:
        """Deeply nested but valid contract does not crash the validator."""
        deep = {"channels": {"ch": {"emit": {"payload": {"nested": {"level": 99}}}}}}
        errors = ws_validate(deep)
        assert errors == []


class TestWSMain:
    """Tests for WebSocket CLI main() entry point."""

    def test_main_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() returns 0 for a valid contract file."""
        f = tmp_path / "ws.yaml"
        f.write_text(yaml.dump(_minimal_ws()), encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["validate_websocket_contract.py", str(f)])
        assert ws_main() == 0

    def test_main_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() returns 1 for an invalid contract file."""
        f = tmp_path / "bad.yaml"
        f.write_text(yaml.dump({"nothing": "here"}), encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["validate_websocket_contract.py", str(f)])
        assert ws_main() == 1

    def test_main_file_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() raises FileNotFoundError for missing file."""
        monkeypatch.setattr("sys.argv", ["validate_websocket_contract.py", "/no/ws.yaml"])
        with pytest.raises(FileNotFoundError, match="not found"):
            ws_main()

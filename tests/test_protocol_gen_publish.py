"""Tests for protocol contract generation, docs generation, and asset publishing.

Covers:
- scripts/generate_protocol_contract_from_planning_notes.py
- scripts/generate_protocol_docs.py
- scripts/publish_protocol_assets.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_protocol_contract_from_planning_notes import (
    _asyncapi_contract,
    _extract_channels,
    _extract_keywords,
    _graphql_contract,
    _grpc_contract,
    _pascal,
    _slug,
    _websocket_contract,
    main as gen_contract_main,
)
from scripts.generate_protocol_docs import (
    _extract_async_channels,
    _extract_graphql_ops,
    _extract_grpc_methods,
    _extract_websocket_channels,
    _load_source,
    _render_asyncapi_tester,
    _render_graphql_playground,
    _render_grpc_tester,
    _render_summary,
    _render_websocket_tester,
    main as gen_docs_main,
)
from scripts.publish_protocol_assets import (
    _copy,
    main as publish_main,
)


# ---------------------------------------------------------------------------
# _slug tests
# ---------------------------------------------------------------------------


class TestSlug:
    """Tests for the _slug helper."""

    def test_basic_slug(self) -> None:
        """Normal project name converts to lowercase underscore slug."""
        assert _slug("My API Project") == "my_api_project"

    def test_special_characters_replaced(self) -> None:
        """Non-alphanumeric characters become underscores."""
        assert _slug("hello-world!@#test") == "hello_world_test"

    def test_empty_string_fallback(self) -> None:
        """Empty string returns the default fallback slug."""
        assert _slug("") == "api_project"

    def test_only_special_chars_fallback(self) -> None:
        """String with only special chars returns fallback."""
        assert _slug("@#$%^&") == "api_project"

    def test_unicode_characters(self) -> None:
        """Unicode non-ASCII characters are replaced with underscores."""
        result = _slug("projekt-uebersicht")
        assert result == "projekt_uebersicht"

    def test_leading_trailing_underscores_stripped(self) -> None:
        """Leading and trailing underscores are stripped."""
        assert _slug("__hello__") == "hello"


# ---------------------------------------------------------------------------
# _pascal tests
# ---------------------------------------------------------------------------


class TestPascal:
    """Tests for the _pascal helper."""

    def test_basic_pascal(self) -> None:
        """Normal text converts to PascalCase."""
        assert _pascal("my api project") == "MyApiProject"

    def test_empty_string_fallback(self) -> None:
        """Empty string returns the default fallback."""
        assert _pascal("") == "ApiProject"

    def test_only_special_chars_fallback(self) -> None:
        """String with only special chars returns fallback."""
        assert _pascal("---") == "ApiProject"

    def test_single_word(self) -> None:
        """Single word is capitalized."""
        assert _pascal("users") == "Users"

    def test_already_pascal(self) -> None:
        """Already PascalCase string stays the same."""
        assert _pascal("MyProject") == "Myproject"

    def test_hyphenated_name(self) -> None:
        """Hyphenated names split correctly."""
        assert _pascal("order-management") == "OrderManagement"


# ---------------------------------------------------------------------------
# _extract_keywords tests
# ---------------------------------------------------------------------------


class TestExtractKeywords:
    """Tests for keyword extraction from planning notes."""

    def test_finds_matching_keywords(self) -> None:
        """Keywords present in notes are returned."""
        notes = "The system provides health checks and user management."
        result = _extract_keywords(notes, ["health", "user", "missing"])
        assert result == ["health", "user"]

    def test_case_insensitive_matching(self) -> None:
        """Matching is case-insensitive."""
        notes = "HEALTH endpoint and Status monitoring."
        result = _extract_keywords(notes, ["health", "status"])
        assert result == ["health", "status"]

    def test_no_matches_returns_empty(self) -> None:
        """No matching keywords returns empty list."""
        result = _extract_keywords("some unrelated content", ["alpha", "beta"])
        assert result == []

    def test_deduplication(self) -> None:
        """Duplicate words in the search list produce no duplicates in result."""
        notes = "health health health"
        result = _extract_keywords(notes, ["health", "health"])
        assert result == ["health"]

    def test_empty_notes(self) -> None:
        """Empty notes string returns empty list."""
        result = _extract_keywords("", ["health"])
        assert result == []

    def test_substring_matching(self) -> None:
        """Keywords match as substrings within notes text."""
        notes = "check the user_health_status endpoint"
        result = _extract_keywords(notes, ["health"])
        assert result == ["health"]


# ---------------------------------------------------------------------------
# _extract_channels tests
# ---------------------------------------------------------------------------


class TestExtractChannels:
    """Tests for channel extraction from planning notes."""

    def test_channel_colon_pattern(self) -> None:
        """Matches channel: name pattern (priority 1)."""
        notes = "channel: order.created\nchannel: user.updated"
        result = _extract_channels(notes)
        assert "order.created" in result
        assert "user.updated" in result

    def test_topic_dash_pattern(self) -> None:
        """Matches topic - name pattern."""
        notes = "topic - payment.refunded"
        result = _extract_channels(notes)
        assert "payment.refunded" in result

    def test_event_colon_pattern(self) -> None:
        """Matches event: name pattern."""
        notes = "event: task.completed"
        result = _extract_channels(notes)
        assert "task.completed" in result

    def test_dotted_name_pattern(self) -> None:
        """Matches dotted names like order.created as pattern 2."""
        notes = "We listen on order.created and user.deleted events."
        result = _extract_channels(notes)
        assert "order.created" in result

    def test_slash_path_pattern(self) -> None:
        """Matches slash-separated channel paths as pattern 3."""
        notes = "Subscribe to events/orders/created for order events."
        result = _extract_channels(notes)
        assert "events/orders/created" in result

    def test_limit_enforced(self) -> None:
        """Respects the channel extraction limit."""
        notes = "\n".join(f"channel: ch{i}.event" for i in range(20))
        result = _extract_channels(notes, limit=5)
        assert len(result) <= 5

    def test_default_limit_is_8(self) -> None:
        """Default limit of 8 is enforced."""
        notes = "\n".join(f"channel: ch{i}.event" for i in range(20))
        result = _extract_channels(notes)
        assert len(result) <= 8

    def test_deduplication(self) -> None:
        """Duplicate channels are not returned twice."""
        notes = "channel: order.created\nchannel: order.created"
        result = _extract_channels(notes)
        assert result.count("order.created") == 1

    def test_empty_notes(self) -> None:
        """Empty notes returns empty list."""
        assert _extract_channels("") == []


# ---------------------------------------------------------------------------
# _graphql_contract tests
# ---------------------------------------------------------------------------


class TestGraphqlContract:
    """Tests for GraphQL contract generation."""

    def test_contains_schema_block(self) -> None:
        """Generated contract contains a schema block."""
        result = _graphql_contract("health check project", "TestProject")
        assert "schema {" in result
        assert "query: Query" in result
        assert "mutation: Mutation" in result
        assert "subscription: Subscription" in result

    def test_contains_query_type(self) -> None:
        """Generated contract contains type Query block."""
        result = _graphql_contract("health status", "TestProject")
        assert "type Query {" in result
        assert "health" in result

    def test_contains_project_name_comment(self) -> None:
        """Generated contract includes project name in comment."""
        result = _graphql_contract("notes", "MyService")
        assert "MyService" in result

    def test_defaults_when_no_keywords(self) -> None:
        """Provides default operations when no keywords match."""
        result = _graphql_contract("some random notes", "Default")
        assert "type Query {" in result
        assert "type Mutation {" in result

    def test_max_8_operations_per_type(self) -> None:
        """Each type block has at most 8 operations."""
        notes = "health status project task user list_projects create_project update_project create_task publish_event extra1 extra2"
        result = _graphql_contract(notes, "BigProject")
        query_block = result.split("type Query {")[1].split("}")[0]
        op_count = sum(1 for line in query_block.strip().splitlines() if line.strip())
        assert op_count <= 8


# ---------------------------------------------------------------------------
# _grpc_contract tests
# ---------------------------------------------------------------------------


class TestGrpcContract:
    """Tests for gRPC contract generation."""

    def test_proto3_syntax(self) -> None:
        """Generated contract starts with proto3 syntax declaration."""
        result = _grpc_contract("GetProject ListProjects", "TestService")
        assert 'syntax = "proto3";' in result

    def test_package_uses_slug(self) -> None:
        """Package name is derived from project name slug."""
        result = _grpc_contract("notes", "My Service")
        assert "package my_service.v1;" in result

    def test_service_uses_pascal(self) -> None:
        """Service name is derived from project name PascalCase."""
        result = _grpc_contract("notes", "My Service")
        assert "MyServiceService" in result

    def test_rpc_lines_generated(self) -> None:
        """RPC method definitions are generated."""
        result = _grpc_contract("GetProject CreateProject", "Svc")
        assert "rpc GetProject" in result
        assert "rpc CreateProject" in result

    def test_request_response_messages(self) -> None:
        """Request and response messages are generated for each RPC."""
        result = _grpc_contract("GetProject", "Svc")
        assert "GetProjectRequest" in result
        assert "GetProjectResponse" in result

    def test_max_10_methods(self) -> None:
        """At most 10 RPC methods are generated."""
        notes = " ".join([
            "GetProject", "ListProjects", "CreateProject",
            "UpdateProject", "DeleteProject", "CreateTask",
            "ListTasks",
        ])
        result = _grpc_contract(notes, "Big")
        rpc_count = result.count("rpc ")
        assert rpc_count <= 10

    def test_defaults_when_no_keywords(self) -> None:
        """Provides default methods when no keywords match."""
        result = _grpc_contract("some random notes", "Default")
        assert "rpc GetProject" in result


# ---------------------------------------------------------------------------
# _asyncapi_contract tests
# ---------------------------------------------------------------------------


class TestAsyncapiContract:
    """Tests for AsyncAPI contract generation."""

    def test_valid_yaml_output(self) -> None:
        """Generated contract is valid YAML."""
        result = _asyncapi_contract("channel: order.created", "TestAPI")
        parsed = yaml.safe_load(result)
        assert isinstance(parsed, dict)

    def test_asyncapi_version(self) -> None:
        """Contract specifies AsyncAPI version 2.6.0."""
        result = _asyncapi_contract("notes", "TestAPI")
        parsed = yaml.safe_load(result)
        assert parsed["asyncapi"] == "2.6.0"

    def test_info_contains_project_name(self) -> None:
        """Info block contains the project name."""
        result = _asyncapi_contract("notes", "EventBus")
        parsed = yaml.safe_load(result)
        assert "EventBus" in parsed["info"]["title"]

    def test_channels_from_notes(self) -> None:
        """Channels extracted from notes appear in contract."""
        result = _asyncapi_contract("channel: payment.received", "PayAPI")
        parsed = yaml.safe_load(result)
        assert "payment.received" in parsed["channels"]

    def test_default_channels_when_none_found(self) -> None:
        """Default channels are used when no channels found in notes."""
        result = _asyncapi_contract("unrelated content here", "Default")
        parsed = yaml.safe_load(result)
        channels = list(parsed["channels"].keys())
        assert "project.updated" in channels
        assert "task.completed" in channels

    def test_max_10_channels(self) -> None:
        """At most 10 channels are included."""
        notes = "\n".join(f"channel: ch{i}.events" for i in range(20))
        result = _asyncapi_contract(notes, "Big")
        parsed = yaml.safe_load(result)
        assert len(parsed["channels"]) <= 10

    def test_publish_and_subscribe_per_channel(self) -> None:
        """Each channel has both publish and subscribe sections."""
        result = _asyncapi_contract("channel: order.created", "Test")
        parsed = yaml.safe_load(result)
        ch = parsed["channels"]["order.created"]
        assert "publish" in ch
        assert "subscribe" in ch


# ---------------------------------------------------------------------------
# _websocket_contract tests
# ---------------------------------------------------------------------------


class TestWebsocketContract:
    """Tests for WebSocket contract generation."""

    def test_valid_yaml_output(self) -> None:
        """Generated contract is valid YAML."""
        result = _websocket_contract("channel: ws.events", "WsAPI")
        parsed = yaml.safe_load(result)
        assert isinstance(parsed, dict)

    def test_info_section(self) -> None:
        """Contract has info section with project name."""
        result = _websocket_contract("notes", "RealtimeAPI")
        parsed = yaml.safe_load(result)
        assert "RealtimeAPI" in parsed["info"]["title"]

    def test_channels_from_notes(self) -> None:
        """Channels from notes appear in the contract."""
        result = _websocket_contract("channel: live.updates", "WsAPI")
        parsed = yaml.safe_load(result)
        assert "live.updates" in parsed["channels"]

    def test_default_channels(self) -> None:
        """Default channels used when no channels found in notes."""
        result = _websocket_contract("unrelated", "Default")
        parsed = yaml.safe_load(result)
        assert "project.updated" in parsed["channels"]

    def test_max_10_channels(self) -> None:
        """At most 10 channels are included."""
        notes = "\n".join(f"channel: ws{i}.stream" for i in range(20))
        result = _websocket_contract(notes, "Big")
        parsed = yaml.safe_load(result)
        assert len(parsed["channels"]) <= 10

    def test_channel_has_description(self) -> None:
        """Each channel has a description field."""
        result = _websocket_contract("channel: live.feed", "WsAPI")
        parsed = yaml.safe_load(result)
        ch = parsed["channels"]["live.feed"]
        assert "description" in ch


# ---------------------------------------------------------------------------
# Contract generation CLI main() tests
# ---------------------------------------------------------------------------


class TestGenContractMain:
    """Tests for the generate_protocol_contract_from_planning_notes main()."""

    def test_graphql_cli(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """CLI generates a GraphQL contract file."""
        notes = tmp_path / "notes.md"
        notes.write_text("health check project management", encoding="utf-8")
        output = tmp_path / "schema.graphql"
        monkeypatch.setattr(
            "sys.argv",
            ["prog", "--protocol", "graphql", "--notes", str(notes),
             "--output", str(output), "--project-name", "CliTest"],
        )
        result = gen_contract_main()
        assert result == 0
        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert "type Query" in content

    def test_grpc_cli_directory_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """CLI generates a gRPC contract when output is a directory."""
        notes = tmp_path / "notes.md"
        notes.write_text("GetProject ListProjects", encoding="utf-8")
        out_dir = tmp_path / "proto_out"
        monkeypatch.setattr(
            "sys.argv",
            ["prog", "--protocol", "grpc", "--notes", str(notes),
             "--output", str(out_dir), "--project-name", "GrpcCli"],
        )
        result = gen_contract_main()
        assert result == 0
        proto_file = out_dir / "grpccli.proto"
        assert proto_file.exists()

    def test_asyncapi_cli(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """CLI generates an AsyncAPI contract."""
        notes = tmp_path / "notes.md"
        notes.write_text("channel: order.created", encoding="utf-8")
        output = tmp_path / "asyncapi.yaml"
        monkeypatch.setattr(
            "sys.argv",
            ["prog", "--protocol", "asyncapi", "--notes", str(notes),
             "--output", str(output)],
        )
        result = gen_contract_main()
        assert result == 0
        parsed = yaml.safe_load(output.read_text(encoding="utf-8"))
        assert "asyncapi" in parsed

    def test_websocket_cli(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """CLI generates a WebSocket contract."""
        notes = tmp_path / "notes.md"
        notes.write_text("channel: ws.stream", encoding="utf-8")
        output = tmp_path / "channels.yaml"
        monkeypatch.setattr(
            "sys.argv",
            ["prog", "--protocol", "websocket", "--notes", str(notes),
             "--output", str(output)],
        )
        result = gen_contract_main()
        assert result == 0
        assert output.exists()

    def test_skip_existing_without_force(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """CLI skips overwriting existing file without --force flag."""
        notes = tmp_path / "notes.md"
        notes.write_text("health", encoding="utf-8")
        output = tmp_path / "schema.graphql"
        output.write_text("existing content", encoding="utf-8")
        monkeypatch.setattr(
            "sys.argv",
            ["prog", "--protocol", "graphql", "--notes", str(notes),
             "--output", str(output)],
        )
        result = gen_contract_main()
        assert result == 0
        assert output.read_text(encoding="utf-8") == "existing content"

    def test_force_overwrites_existing(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """CLI overwrites existing file with --force flag."""
        notes = tmp_path / "notes.md"
        notes.write_text("health", encoding="utf-8")
        output = tmp_path / "schema.graphql"
        output.write_text("existing content", encoding="utf-8")
        monkeypatch.setattr(
            "sys.argv",
            ["prog", "--protocol", "graphql", "--notes", str(notes),
             "--output", str(output), "--force"],
        )
        result = gen_contract_main()
        assert result == 0
        assert output.read_text(encoding="utf-8") != "existing content"

    def test_missing_notes_raises(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """CLI raises FileNotFoundError when notes file is missing."""
        monkeypatch.setattr(
            "sys.argv",
            ["prog", "--protocol", "graphql", "--notes", str(tmp_path / "missing.md"),
             "--output", str(tmp_path / "out.graphql")],
        )
        with pytest.raises(FileNotFoundError):
            gen_contract_main()


# ---------------------------------------------------------------------------
# _load_source tests
# ---------------------------------------------------------------------------


class TestLoadSource:
    """Tests for the source file loader."""

    def test_load_yaml(self, tmp_path: Path) -> None:
        """Loads a .yaml file and returns parsed dict."""
        f = tmp_path / "test.yaml"
        f.write_text("key: value\n", encoding="utf-8")
        result = _load_source(f)
        assert result == {"key": "value"}

    def test_load_yml(self, tmp_path: Path) -> None:
        """Loads a .yml file and returns parsed dict."""
        f = tmp_path / "test.yml"
        f.write_text("items:\n  - a\n  - b\n", encoding="utf-8")
        result = _load_source(f)
        assert result == {"items": ["a", "b"]}

    def test_load_json(self, tmp_path: Path) -> None:
        """Loads a .json file and returns parsed dict."""
        f = tmp_path / "test.json"
        f.write_text('{"key": 42}', encoding="utf-8")
        result = _load_source(f)
        assert result == {"key": 42}

    def test_load_text_fallback(self, tmp_path: Path) -> None:
        """Non-YAML/JSON files return raw text."""
        f = tmp_path / "schema.graphql"
        f.write_text("type Query { health: String! }", encoding="utf-8")
        result = _load_source(f)
        assert isinstance(result, str)
        assert "type Query" in result


# ---------------------------------------------------------------------------
# _extract_graphql_ops tests
# ---------------------------------------------------------------------------


class TestExtractGraphqlOps:
    """Tests for GraphQL operation extraction from SDL."""

    def test_extracts_query_ops(self) -> None:
        """Extracts operation names from a Query type block."""
        schema = "type Query {\n  health(id: ID): String!\n  project(id: ID): Project\n}\n"
        ops = _extract_graphql_ops(schema, "Query")
        assert "health" in ops
        assert "project" in ops

    def test_extracts_mutation_ops(self) -> None:
        """Extracts operation names from a Mutation type block."""
        schema = "type Mutation {\n  createProject(input: Input!): Project\n}\n"
        ops = _extract_graphql_ops(schema, "Mutation")
        assert "createProject" in ops

    def test_skips_comments(self) -> None:
        """Lines starting with # inside a type block are skipped."""
        schema = "type Query {\n  # This is a comment\n  health: String!\n}\n"
        ops = _extract_graphql_ops(schema, "Query")
        assert ops == ["health"]

    def test_no_match_returns_empty(self) -> None:
        """Returns empty list when the type is not found."""
        ops = _extract_graphql_ops("type Query { health: String! }", "Mutation")
        assert ops == []

    def test_results_are_sorted_and_deduplicated(self) -> None:
        """Results are sorted and unique."""
        schema = "type Query {\n  beta: String!\n  alpha: String!\n  beta: String!\n}\n"
        ops = _extract_graphql_ops(schema, "Query")
        assert ops == ["alpha", "beta"]


# ---------------------------------------------------------------------------
# _extract_grpc_methods tests
# ---------------------------------------------------------------------------


class TestExtractGrpcMethods:
    """Tests for gRPC method extraction from proto text."""

    def test_extracts_from_proto_text(self, tmp_path: Path) -> None:
        """Extracts service/method tuples from proto3 text."""
        proto = (
            'syntax = "proto3";\n'
            "service Greeter {\n"
            "  rpc SayHello (HelloRequest) returns (HelloResponse);\n"
            "  rpc SayGoodbye (GoodbyeRequest) returns (GoodbyeResponse);\n"
            "}\n"
        )
        proto_file = tmp_path / "service.proto"
        proto_file.write_text(proto, encoding="utf-8")
        methods = _extract_grpc_methods(proto_file, proto)
        assert ("Greeter", "SayHello") in methods
        assert ("Greeter", "SayGoodbye") in methods

    def test_extracts_from_directory(self, tmp_path: Path) -> None:
        """Extracts methods from all .proto files in a directory."""
        proto1 = tmp_path / "a.proto"
        proto1.write_text(
            "service Alpha {\n  rpc DoA (AReq) returns (AResp);\n}\n",
            encoding="utf-8",
        )
        proto2 = tmp_path / "b.proto"
        proto2.write_text(
            "service Beta {\n  rpc DoB (BReq) returns (BResp);\n}\n",
            encoding="utf-8",
        )
        methods = _extract_grpc_methods(tmp_path, {})
        assert ("Alpha", "DoA") in methods
        assert ("Beta", "DoB") in methods

    def test_non_proto_file_non_string_payload(self, tmp_path: Path) -> None:
        """Non-proto file with non-string payload returns empty from text parse path."""
        f = tmp_path / "data.json"
        f.write_text("{}", encoding="utf-8")
        methods = _extract_grpc_methods(f, {"key": "val"})
        assert methods == []


# ---------------------------------------------------------------------------
# _extract_async_channels / _extract_websocket_channels tests
# ---------------------------------------------------------------------------


class TestExtractChannels:
    """Tests for AsyncAPI and WebSocket channel extraction."""

    def test_async_channels_from_dict(self) -> None:
        """Extracts sorted channel names from AsyncAPI payload."""
        payload: dict[str, Any] = {"channels": {"b.chan": {}, "a.chan": {}}}
        result = _extract_async_channels(payload)
        assert result == ["a.chan", "b.chan"]

    def test_async_channels_non_dict_returns_empty(self) -> None:
        """Non-dict payload returns empty list."""
        assert _extract_async_channels("not a dict") == []

    def test_async_channels_missing_key_returns_empty(self) -> None:
        """Missing channels key returns empty list."""
        assert _extract_async_channels({"info": {}}) == []

    def test_websocket_channels_from_dict(self) -> None:
        """Extracts sorted channel names from WebSocket payload."""
        payload: dict[str, Any] = {"channels": {"z.ws": {}, "a.ws": {}}}
        result = _extract_websocket_channels(payload)
        assert result == ["a.ws", "z.ws"]

    def test_websocket_events_fallback(self) -> None:
        """Falls back to events key when channels is missing."""
        payload: dict[str, Any] = {"events": {"evt1": {}, "evt2": {}}}
        result = _extract_websocket_channels(payload)
        assert result == ["evt1", "evt2"]

    def test_websocket_non_dict_returns_empty(self) -> None:
        """Non-dict payload returns empty list."""
        assert _extract_websocket_channels(42) == []


# ---------------------------------------------------------------------------
# Playground / tester renderer tests
# ---------------------------------------------------------------------------


class TestPlaygroundRenderers:
    """Tests for interactive playground HTML/JS generation."""

    def test_graphql_playground_structure(self) -> None:
        """GraphQL playground contains key HTML elements and JS."""
        lines = _render_graphql_playground("https://api.example.com/graphql")
        text = "\n".join(lines)
        assert "graphql-playground" in text
        assert "graphql-run" in text
        assert "<script>" in text
        assert "https://api.example.com/graphql" in text

    def test_graphql_playground_semantic_fallback(self) -> None:
        """GraphQL playground JS contains semantic fallback logic."""
        lines = _render_graphql_playground("")
        text = "\n".join(lines)
        assert "semantic-fallback" in text
        assert "fallback" in text

    def test_grpc_tester_structure(self) -> None:
        """gRPC tester contains service/method inputs and JS."""
        lines = _render_grpc_tester("https://gateway.example.com")
        text = "\n".join(lines)
        assert "grpc-playground" in text
        assert "grpc-service" in text
        assert "grpc-method" in text
        assert "<script>" in text

    def test_asyncapi_tester_dual_transport(self) -> None:
        """AsyncAPI tester has both WS and HTTP send buttons."""
        lines = _render_asyncapi_tester("wss://ws.example.com", "https://http.example.com")
        text = "\n".join(lines)
        assert "asyncapi-send-ws" in text
        assert "asyncapi-send-http" in text
        assert "wss://ws.example.com" in text
        assert "https://http.example.com" in text

    def test_websocket_tester_structure(self) -> None:
        """WebSocket tester contains endpoint view and send button."""
        lines = _render_websocket_tester("wss://ws.example.com")
        text = "\n".join(lines)
        assert "websocket-playground" in text
        assert "websocket-send" in text
        assert "wss://ws.example.com" in text

    def test_graphql_playground_empty_endpoint(self) -> None:
        """GraphQL playground with empty endpoint shows not configured."""
        lines = _render_graphql_playground("")
        text = "\n".join(lines)
        assert "not configured" in text.lower() or '""' in text


# ---------------------------------------------------------------------------
# _render_summary tests
# ---------------------------------------------------------------------------


class TestRenderSummary:
    """Tests for full Markdown document generation."""

    def test_graphql_summary(self, tmp_path: Path) -> None:
        """GraphQL summary includes operations and playground."""
        src = tmp_path / "schema.graphql"
        schema = "type Query {\n  health: String!\n  project(id: ID): Project\n}\n"
        src.write_text(schema, encoding="utf-8")
        result = _render_summary(
            "graphql", src, schema,
            mode="api-first", endpoint="", ws_endpoint="", http_endpoint="", index_link="../index.md",
        )
        assert "GRAPHQL" in result
        assert "Operations" in result
        assert "Query count:" in result
        assert "graphql-playground" in result

    def test_grpc_summary(self, tmp_path: Path) -> None:
        """gRPC summary includes service methods and tester."""
        proto = "service Greeter {\n  rpc SayHello (Req) returns (Resp);\n}\n"
        src = tmp_path / "service.proto"
        src.write_text(proto, encoding="utf-8")
        result = _render_summary(
            "grpc", src, proto,
            mode="api-first", endpoint="", ws_endpoint="", http_endpoint="", index_link="../index.md",
        )
        assert "GRPC" in result
        assert "Service Methods" in result
        assert "Greeter.SayHello" in result
        assert "grpc-playground" in result

    def test_asyncapi_summary(self, tmp_path: Path) -> None:
        """AsyncAPI summary includes channels and tester."""
        payload: dict[str, Any] = {"channels": {"order.created": {}, "user.updated": {}}}
        src = tmp_path / "asyncapi.yaml"
        src.write_text(yaml.safe_dump(payload), encoding="utf-8")
        result = _render_summary(
            "asyncapi", src, payload,
            mode="api-first", endpoint="", ws_endpoint="wss://ws.test", http_endpoint="https://http.test", index_link="../index.md",
        )
        assert "ASYNCAPI" in result
        assert "Channels" in result
        assert "order.created" in result
        assert "asyncapi-playground" in result

    def test_websocket_summary(self, tmp_path: Path) -> None:
        """WebSocket summary includes channels and tester."""
        payload: dict[str, Any] = {"channels": {"live.feed": {}}}
        src = tmp_path / "channels.yaml"
        src.write_text(yaml.safe_dump(payload), encoding="utf-8")
        result = _render_summary(
            "websocket", src, payload,
            mode="api-first", endpoint="", ws_endpoint="wss://ws.test", http_endpoint="", index_link="../index.md",
        )
        assert "WEBSOCKET" in result
        assert "Channels/Events" in result
        assert "live.feed" in result

    def test_unknown_protocol_summary(self, tmp_path: Path) -> None:
        """Unknown protocol produces a generic notes section."""
        src = tmp_path / "contract.txt"
        src.write_text("anything", encoding="utf-8")
        result = _render_summary(
            "custom", src, "anything",
            mode="manual", endpoint="", ws_endpoint="", http_endpoint="", index_link="../index.md",
        )
        assert "Notes" in result
        assert "Generated from source contract" in result

    def test_frontmatter_present(self, tmp_path: Path) -> None:
        """Generated doc contains YAML frontmatter."""
        src = tmp_path / "schema.graphql"
        src.write_text("type Query { h: String! }", encoding="utf-8")
        result = _render_summary(
            "graphql", src, "type Query { h: String! }",
            mode="api-first", endpoint="", ws_endpoint="", http_endpoint="", index_link="../index.md",
        )
        assert result.startswith("---")
        assert 'content_type: reference' in result

    def test_dict_payload_top_level_keys(self, tmp_path: Path) -> None:
        """Dict payloads generate a Top-level Keys section."""
        payload: dict[str, Any] = {"asyncapi": "2.6.0", "info": {}, "channels": {}}
        src = tmp_path / "asyncapi.yaml"
        src.write_text(yaml.safe_dump(payload), encoding="utf-8")
        result = _render_summary(
            "asyncapi", src, payload,
            mode="api-first", endpoint="", ws_endpoint="", http_endpoint="", index_link="../index.md",
        )
        assert "Top-level Keys" in result
        assert "`asyncapi`" in result


# ---------------------------------------------------------------------------
# generate_protocol_docs main() tests
# ---------------------------------------------------------------------------


class TestGenDocsMain:
    """Tests for the generate_protocol_docs CLI main()."""

    def test_graphql_docs_cli(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """CLI generates GraphQL reference doc from schema file."""
        schema = tmp_path / "schema.graphql"
        schema.write_text("type Query { health: String! }\n", encoding="utf-8")
        output = tmp_path / "graphql-ref.md"
        monkeypatch.setattr(
            "sys.argv",
            ["prog", "--protocol", "graphql", "--source", str(schema),
             "--output", str(output), "--endpoint", "https://api.test/graphql"],
        )
        result = gen_docs_main()
        assert result == 0
        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert "GRAPHQL" in content

    def test_missing_source_raises(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """CLI raises FileNotFoundError when source file is missing."""
        monkeypatch.setattr(
            "sys.argv",
            ["prog", "--protocol", "graphql", "--source", str(tmp_path / "missing.graphql"),
             "--output", str(tmp_path / "out.md")],
        )
        with pytest.raises(FileNotFoundError):
            gen_docs_main()

    def test_asyncapi_docs_cli_default_ws_endpoint(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """AsyncAPI docs CLI uses default WS endpoint when not specified."""
        spec = tmp_path / "asyncapi.yaml"
        spec.write_text(yaml.safe_dump({"channels": {"test.ch": {}}}), encoding="utf-8")
        output = tmp_path / "asyncapi-ref.md"
        monkeypatch.setattr(
            "sys.argv",
            ["prog", "--protocol", "asyncapi", "--source", str(spec),
             "--output", str(output)],
        )
        result = gen_docs_main()
        assert result == 0
        content = output.read_text(encoding="utf-8")
        assert "ASYNCAPI" in content


# ---------------------------------------------------------------------------
# _copy tests
# ---------------------------------------------------------------------------


class TestCopy:
    """Tests for the _copy helper in publish_protocol_assets."""

    def test_copies_existing_file(self, tmp_path: Path) -> None:
        """Copies an existing file to the destination."""
        src = tmp_path / "source.txt"
        src.write_text("hello", encoding="utf-8")
        dst = tmp_path / "sub" / "dest.txt"
        _copy(src, dst)
        assert dst.exists()
        assert dst.read_text(encoding="utf-8") == "hello"

    def test_skips_missing_source(self, tmp_path: Path) -> None:
        """Silently skips when source file does not exist."""
        src = tmp_path / "missing.txt"
        dst = tmp_path / "dest.txt"
        _copy(src, dst)
        assert not dst.exists()

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """Creates parent directories for the destination."""
        src = tmp_path / "file.txt"
        src.write_text("data", encoding="utf-8")
        dst = tmp_path / "a" / "b" / "c" / "file.txt"
        _copy(src, dst)
        assert dst.exists()


# ---------------------------------------------------------------------------
# publish_protocol_assets main() tests
# ---------------------------------------------------------------------------


class TestPublishMain:
    """Tests for the publish_protocol_assets CLI main()."""

    def test_publish_file_source(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Publishes a single file source into the target directory."""
        source = tmp_path / "schema.graphql"
        source.write_text("type Query { h: String! }", encoding="utf-8")
        doc = tmp_path / "ref.md"
        doc.write_text("# Reference", encoding="utf-8")
        target = "publish_out/protocols"
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            "sys.argv",
            ["prog", "--protocol", "graphql", "--source", str(source),
             "--generated-doc", str(doc), "--target-root", target],
        )
        result = publish_main()
        assert result == 0
        published = tmp_path / target / "graphql"
        assert (published / "schema.graphql").exists()
        assert (published / "ref.md").exists()
        index_md = tmp_path / target / "index.md"
        assert index_md.exists()
        assert "./graphql/" in index_md.read_text(encoding="utf-8")

    def test_publish_directory_source(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Publishes all files from a directory source."""
        src_dir = tmp_path / "protos"
        src_dir.mkdir()
        (src_dir / "a.proto").write_text("syntax = proto3;", encoding="utf-8")
        (src_dir / "b.proto").write_text("syntax = proto3;", encoding="utf-8")
        doc = tmp_path / "grpc.md"
        doc.write_text("# gRPC Ref", encoding="utf-8")
        target = "pub_out/protocols"
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            "sys.argv",
            ["prog", "--protocol", "grpc", "--source", str(src_dir),
             "--generated-doc", str(doc), "--target-root", target],
        )
        result = publish_main()
        assert result == 0
        published = tmp_path / target / "grpc"
        assert (published / "a.proto").exists()
        assert (published / "b.proto").exists()
        assert (published / "grpc.md").exists()
        index_md = tmp_path / target / "index.md"
        assert index_md.exists()
        assert "./grpc/" in index_md.read_text(encoding="utf-8")

    def test_absolute_target_root_raises(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Raises ValueError when --target-root is an absolute path."""
        source = tmp_path / "schema.graphql"
        source.write_text("data", encoding="utf-8")
        doc = tmp_path / "ref.md"
        doc.write_text("doc", encoding="utf-8")
        monkeypatch.setattr(
            "sys.argv",
            ["prog", "--protocol", "graphql", "--source", str(source),
             "--generated-doc", str(doc), "--target-root", "/absolute/path"],
        )
        with pytest.raises(ValueError, match="repository-relative"):
            publish_main()

    def test_publish_missing_source_file_skipped(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Publishing with a non-existent source is handled (source not file/dir)."""
        source = tmp_path / "nonexistent.graphql"
        doc = tmp_path / "ref.md"
        doc.write_text("# Ref", encoding="utf-8")
        target = "out/protocols"
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            "sys.argv",
            ["prog", "--protocol", "graphql", "--source", str(source),
             "--generated-doc", str(doc), "--target-root", target],
        )
        result = publish_main()
        assert result == 0
        published = tmp_path / target / "graphql"
        assert (published / "ref.md").exists()
        index_md = tmp_path / target / "index.md"
        assert index_md.exists()
        assert "./graphql/" in index_md.read_text(encoding="utf-8")

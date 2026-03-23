"""Coverage boost tests for low-coverage scripts.

Targets:
- scripts/generate_protocol_test_assets.py (15% -> higher)
- scripts/self_verify_prodlike_user_path.py (36% -> higher)
- scripts/run_protocol_self_verify.py (38% -> higher)
- scripts/upload_api_test_assets.py (49% -> higher)
- scripts/run_api_first_flow.py (50% -> higher)
"""

from __future__ import annotations

import base64
import csv
import json
import os
import subprocess
import sys
import textwrap
import urllib.error
from io import BytesIO
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# generate_protocol_test_assets.py
# ---------------------------------------------------------------------------

from scripts.generate_protocol_test_assets import (
    _default_cases,
    _event_cases,
    _extract_channels,
    _extract_graphql_fields,
    _extract_grpc_methods,
    _graphql_cases,
    _grpc_cases,
    _load_existing,
    _load_payload,
    _merge_cases,
    _mk_case,
    _source_hash,
    _write_fuzz,
    _write_matrix,
    _write_testrail_csv,
    _write_zephyr_json,
)


class TestSourceHash:
    """Tests for SHA-256 source hashing with file, dir, and string inputs."""

    def test_hash_returns_12_char_hex(self, tmp_path: Path) -> None:
        """Source hash of a string returns a 12-character hex digest."""
        result = _source_hash("hello world")
        assert len(result) == 12
        assert all(c in "0123456789abcdef" for c in result)

    def test_hash_file(self, tmp_path: Path) -> None:
        """Source hash reads file bytes when path points to an existing file."""
        f = tmp_path / "spec.graphql"
        f.write_text("type Query { hello: String }", encoding="utf-8")
        result = _source_hash(str(f))
        assert len(result) == 12

    def test_hash_file_deterministic(self, tmp_path: Path) -> None:
        """Same file content produces identical hash."""
        f = tmp_path / "a.txt"
        f.write_text("deterministic", encoding="utf-8")
        assert _source_hash(str(f)) == _source_hash(str(f))

    def test_hash_dir(self, tmp_path: Path) -> None:
        """Source hash aggregates all file bytes when path is a directory."""
        d = tmp_path / "protos"
        d.mkdir()
        (d / "a.proto").write_text("syntax = 'proto3';", encoding="utf-8")
        (d / "b.proto").write_text("service Svc {}", encoding="utf-8")
        result = _source_hash(str(d))
        assert len(result) == 12

    def test_hash_string_fallback(self) -> None:
        """Non-existent path falls back to encoding source string."""
        result = _source_hash("/nonexistent/path/to/spec")
        assert len(result) == 12

    def test_hash_different_content_differs(self, tmp_path: Path) -> None:
        """Different file content produces different hashes."""
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("content-a", encoding="utf-8")
        f2.write_text("content-b", encoding="utf-8")
        assert _source_hash(str(f1)) != _source_hash(str(f2))


class TestLoadPayload:
    """Tests for YAML/JSON payload loading."""

    def test_load_yaml(self, tmp_path: Path) -> None:
        """Loads YAML file and returns parsed dict."""
        f = tmp_path / "spec.yaml"
        f.write_text("channels:\n  events: {}", encoding="utf-8")
        result = _load_payload(f)
        assert isinstance(result, dict)
        assert "channels" in result

    def test_load_json(self, tmp_path: Path) -> None:
        """Loads JSON file and returns parsed dict."""
        f = tmp_path / "data.json"
        f.write_text('{"key": "value"}', encoding="utf-8")
        result = _load_payload(f)
        assert result == {"key": "value"}

    def test_load_other_extension_returns_text(self, tmp_path: Path) -> None:
        """Non-YAML/JSON files return raw text."""
        f = tmp_path / "schema.graphql"
        f.write_text("type Query { hello: String }", encoding="utf-8")
        result = _load_payload(f)
        assert isinstance(result, str)
        assert "Query" in result

    def test_load_nonexistent_returns_empty_dict(self, tmp_path: Path) -> None:
        """Missing path returns empty dict."""
        result = _load_payload(tmp_path / "missing.yaml")
        assert result == {}

    def test_load_dir_returns_empty_dict(self, tmp_path: Path) -> None:
        """Directory path returns empty dict."""
        result = _load_payload(tmp_path)
        assert result == {}

    def test_load_yml_extension(self, tmp_path: Path) -> None:
        """Loads .yml extension the same as .yaml."""
        f = tmp_path / "spec.yml"
        f.write_text("key: val", encoding="utf-8")
        result = _load_payload(f)
        assert result == {"key": "val"}


class TestExtractGraphqlFields:
    """Tests for regex-based GraphQL field extraction."""

    def test_extract_query_fields(self) -> None:
        """Extracts field names from a Query type block."""
        schema = textwrap.dedent("""\
            type Query {
                users: [User]
                project(id: ID!): Project
            }
        """)
        fields = _extract_graphql_fields(schema, "Query")
        assert "users" in fields
        assert "project" in fields

    def test_extract_mutation_fields(self) -> None:
        """Extracts field names from a Mutation type block."""
        schema = "type Mutation {\n  createUser(input: UserInput!): User\n  deleteUser(id: ID!): Boolean\n}\n"
        fields = _extract_graphql_fields(schema, "Mutation")
        assert sorted(fields) == ["createUser", "deleteUser"]

    def test_extract_skips_comments(self) -> None:
        """Lines starting with # inside a type block are skipped."""
        schema = "type Query {\n  # this is a comment\n  hello: String\n}\n"
        fields = _extract_graphql_fields(schema, "Query")
        assert fields == ["hello"]

    def test_extract_missing_type_returns_empty(self) -> None:
        """Non-existent type name returns empty list."""
        schema = "type Query { hello: String }"
        assert _extract_graphql_fields(schema, "Subscription") == []

    def test_extract_empty_type_block(self) -> None:
        """Empty type block returns empty list."""
        schema = "type Query {\n}\n"
        assert _extract_graphql_fields(schema, "Query") == []

    def test_extract_deduplicates_fields(self) -> None:
        """Duplicate field names are deduplicated and sorted."""
        schema = "type Query {\n  hello: String\n  hello: Int\n  world: Boolean\n}\n"
        fields = _extract_graphql_fields(schema, "Query")
        assert fields == ["hello", "world"]

    def test_extract_with_arguments(self) -> None:
        """Fields with arguments have the arg portion stripped."""
        schema = "type Query {\n  user(id: ID!, role: String): User\n}\n"
        fields = _extract_graphql_fields(schema, "Query")
        assert fields == ["user"]


class TestExtractGrpcMethods:
    """Tests for proto service/rpc method extraction."""

    def test_extract_from_proto_text(self, tmp_path: Path) -> None:
        """Extracts service.method names from proto text payload."""
        proto = textwrap.dedent("""\
            service UserService {
                rpc GetUser(GetUserReq) returns (User);
                rpc ListUsers(ListReq) returns (stream User);
            }
        """)
        source = tmp_path / "svc.proto"
        source.write_text(proto, encoding="utf-8")
        methods = _extract_grpc_methods(source, proto)
        assert sorted(methods) == ["UserService.GetUser", "UserService.ListUsers"]

    def test_extract_multiple_services(self, tmp_path: Path) -> None:
        """Extracts methods from multiple services."""
        proto = textwrap.dedent("""\
            service A {
                rpc DoA(Req) returns (Resp);
            }
            service B {
                rpc DoB(Req) returns (Resp);
            }
        """)
        source = tmp_path / "multi.proto"
        source.write_text(proto, encoding="utf-8")
        methods = _extract_grpc_methods(source, proto)
        assert sorted(methods) == ["A.DoA", "B.DoB"]

    def test_extract_from_dir(self, tmp_path: Path) -> None:
        """Scans directory for .proto files when payload is not a string."""
        d = tmp_path / "protos"
        d.mkdir()
        (d / "a.proto").write_text(
            "service Svc {\n  rpc Hello(Req) returns (Resp);\n}\n",
            encoding="utf-8",
        )
        methods = _extract_grpc_methods(d, {})
        assert methods == ["Svc.Hello"]

    def test_extract_empty_proto(self, tmp_path: Path) -> None:
        """Proto without services returns empty list."""
        source = tmp_path / "empty.proto"
        source.write_text("syntax = 'proto3';", encoding="utf-8")
        assert _extract_grpc_methods(source, "syntax = 'proto3';") == []

    def test_closing_brace_resets_service(self, tmp_path: Path) -> None:
        """Closing brace outside service context does not crash."""
        proto = "}\nservice S {\n  rpc M(R) returns (R);\n}\n"
        source = tmp_path / "s.proto"
        source.write_text(proto, encoding="utf-8")
        methods = _extract_grpc_methods(source, proto)
        assert methods == ["S.M"]


class TestExtractChannels:
    """Tests for channel extraction from AsyncAPI/WebSocket payloads."""

    def test_extract_channels_key(self) -> None:
        """Extracts channel names from 'channels' dict."""
        payload = {"channels": {"user.created": {}, "user.deleted": {}}}
        result = _extract_channels(payload)
        assert result == ["user.created", "user.deleted"]

    def test_extract_events_key(self) -> None:
        """Falls back to 'events' key when 'channels' is absent."""
        payload = {"events": {"order.placed": {}}}
        result = _extract_channels(payload)
        assert result == ["order.placed"]

    def test_extract_non_dict_returns_empty(self) -> None:
        """Non-dict payload returns empty list."""
        assert _extract_channels("not a dict") == []
        assert _extract_channels([]) == []

    def test_extract_channels_not_dict_returns_empty(self) -> None:
        """Channels value that is not a dict returns empty list."""
        assert _extract_channels({"channels": "not a dict"}) == []


class TestMkCase:
    """Tests for test case factory function."""

    def test_case_id_format(self) -> None:
        """Case ID is lowercase kebab with TC prefix."""
        case = _mk_case(
            protocol="graphql",
            entity="query:users",
            check="positive",
            title="test",
            expected="ok",
            source="s",
            signature="abc",
            steps=["step1"],
        )
        assert case["id"] == "tc-graphql-query:users-positive"
        assert case["origin"] == "auto"
        assert case["customized"] is False
        assert case["needs_review"] is False
        assert case["spec_signature"] == "abc"

    def test_case_suite_is_uppercase_protocol(self) -> None:
        """Suite field is protocol name uppercased plus ' Contract'."""
        case = _mk_case(
            protocol="grpc",
            entity="e",
            check="c",
            title="t",
            expected="e",
            source="s",
            signature="x",
            steps=[],
        )
        assert case["suite"] == "GRPC Contract"


class TestGraphqlCases:
    """Tests for GraphQL case generation."""

    def test_generates_5_checks_per_entity(self) -> None:
        """Each GraphQL entity produces 5 test cases."""
        schema = "type Query { hello: String }"
        cases = _graphql_cases("source.graphql", "sig123", schema)
        # 1 field * 5 checks
        assert len(cases) == 5
        check_types = {c["check_type"] for c in cases}
        assert check_types == {"positive", "negative", "auth", "security-injection", "performance-latency"}

    def test_fallback_entity_when_no_fields(self) -> None:
        """Generates fallback 'schema' entity when no types are found."""
        cases = _graphql_cases("source.graphql", "sig", "enum Color { RED GREEN }")
        assert all(c["entity"] == "schema" for c in cases)
        assert len(cases) == 5

    def test_queries_and_mutations_combined(self) -> None:
        """Extracts both Query and Mutation fields."""
        schema = "type Query { a: Int }\ntype Mutation { b: Int }\n"
        cases = _graphql_cases("s", "sig", schema)
        entities = {c["entity"] for c in cases}
        assert "query:a" in entities
        assert "mutation:b" in entities
        assert len(cases) == 10


class TestGrpcCases:
    """Tests for gRPC case generation."""

    def test_generates_5_checks_per_method(self, tmp_path: Path) -> None:
        """Each gRPC method produces 5 test cases."""
        proto = "service Svc {\n  rpc Do(R) returns (R);\n}\n"
        source = tmp_path / "s.proto"
        source.write_text(proto, encoding="utf-8")
        cases = _grpc_cases("s.proto", "sig", proto, source)
        assert len(cases) == 5
        check_types = {c["check_type"] for c in cases}
        assert check_types == {"positive", "status-codes", "deadline-retry", "security-authz", "performance-latency"}

    def test_fallback_method_when_no_services(self, tmp_path: Path) -> None:
        """Falls back to 'service.rpc' when no methods are found."""
        source = tmp_path / "empty.proto"
        source.write_text("syntax = 'proto3';", encoding="utf-8")
        cases = _grpc_cases("s.proto", "sig", {}, source)
        assert all(c["entity"] == "service.rpc" for c in cases)


class TestEventCases:
    """Tests for AsyncAPI and WebSocket event case generation."""

    def test_asyncapi_generates_5_checks_per_channel(self) -> None:
        """Each asyncapi channel produces 5 test cases with correct security check."""
        payload = {"channels": {"orders": {}}}
        cases = _event_cases("asyncapi", "src", "sig", payload)
        assert len(cases) == 5
        check_types = {c["check_type"] for c in cases}
        assert "security-signature" in check_types
        assert "performance-throughput" in check_types

    def test_websocket_uses_different_check_names(self) -> None:
        """WebSocket uses security-authz and performance-concurrency."""
        payload = {"channels": {"chat": {}}}
        cases = _event_cases("websocket", "src", "sig", payload)
        check_types = {c["check_type"] for c in cases}
        assert "security-authz" in check_types
        assert "performance-concurrency" in check_types

    def test_fallback_channel_when_empty(self) -> None:
        """Falls back to 'channel.default' when no channels found."""
        cases = _event_cases("asyncapi", "src", "sig", {})
        assert all(c["entity"] == "channel.default" for c in cases)


class TestDefaultCases:
    """Tests for protocol routing in _default_cases."""

    def test_routes_to_graphql(self, tmp_path: Path) -> None:
        """Protocol 'graphql' routes to _graphql_cases."""
        cases = _default_cases("graphql", "s", "sig", "type Query { x: Int }", tmp_path)
        assert all(c["protocol"] == "graphql" for c in cases)

    def test_routes_to_grpc(self, tmp_path: Path) -> None:
        """Protocol 'grpc' routes to _grpc_cases."""
        cases = _default_cases("grpc", "s", "sig", {}, tmp_path)
        assert all(c["protocol"] == "grpc" for c in cases)

    def test_routes_to_asyncapi(self, tmp_path: Path) -> None:
        """Protocol 'asyncapi' routes to _event_cases."""
        cases = _default_cases("asyncapi", "s", "sig", {}, tmp_path)
        assert all(c["protocol"] == "asyncapi" for c in cases)

    def test_routes_to_websocket(self, tmp_path: Path) -> None:
        """Protocol 'websocket' routes to _event_cases."""
        cases = _default_cases("websocket", "s", "sig", {}, tmp_path)
        assert all(c["protocol"] == "websocket" for c in cases)

    def test_unknown_protocol_fallback(self, tmp_path: Path) -> None:
        """Unknown protocol produces a single contract-level case."""
        cases = _default_cases("mqtt", "s", "sig", {}, tmp_path)
        assert len(cases) == 1
        assert cases[0]["entity"] == "contract"


class TestLoadExisting:
    """Tests for loading existing test cases from JSON."""

    def test_load_valid_cases(self, tmp_path: Path) -> None:
        """Loads cases array from JSON file."""
        data = {"cases": [{"id": "tc-1"}, {"id": "tc-2"}]}
        f = tmp_path / "cases.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        result = _load_existing(f)
        assert len(result) == 2

    def test_load_nonexistent_returns_empty(self, tmp_path: Path) -> None:
        """Missing file returns empty list."""
        assert _load_existing(tmp_path / "nope.json") == []

    def test_load_filters_invalid_entries(self, tmp_path: Path) -> None:
        """Entries without id or non-dict entries are filtered out."""
        data = {"cases": [{"id": "ok"}, {"id": ""}, "not-a-dict", {"no_id": True}]}
        f = tmp_path / "cases.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        result = _load_existing(f)
        assert len(result) == 1
        assert result[0]["id"] == "ok"

    def test_load_non_dict_root(self, tmp_path: Path) -> None:
        """Non-dict root JSON returns empty list."""
        f = tmp_path / "cases.json"
        f.write_text("[1,2,3]", encoding="utf-8")
        result = _load_existing(f)
        assert result == []


class TestMergeCases:
    """Tests for smart merge logic with full signature tracking."""

    def _make_case(
        self,
        cid: str,
        sig: str = "sig-a",
        origin: str = "auto",
        customized: bool = False,
        needs_review: bool = False,
    ) -> dict[str, Any]:
        """Helper to build a minimal test case dict."""
        return {
            "id": cid,
            "spec_signature": sig,
            "origin": origin,
            "customized": customized,
            "needs_review": needs_review,
            "title": f"Case {cid}",
        }

    def test_new_cases_are_added(self) -> None:
        """Cases not in existing list are added as new."""
        new = [self._make_case("tc-1")]
        merged, stats = _merge_cases(new, [])
        assert len(merged) == 1
        assert stats["new"] == 1

    def test_auto_generated_unchanged_replaced(self) -> None:
        """Auto-generated, non-customized existing cases are replaced."""
        existing = [self._make_case("tc-1", sig="sig-a")]
        new = [self._make_case("tc-1", sig="sig-b")]
        merged, stats = _merge_cases(new, existing)
        assert len(merged) == 1
        assert merged[0]["spec_signature"] == "sig-b"
        assert stats["updated"] == 1

    def test_manual_origin_never_overwritten(self) -> None:
        """Cases with origin='manual' are preserved, never overwritten."""
        existing = [self._make_case("tc-1", origin="manual", sig="old")]
        new = [self._make_case("tc-1", sig="new")]
        merged, stats = _merge_cases(new, existing)
        assert len(merged) == 1
        assert merged[0]["origin"] == "manual"
        assert merged[0]["spec_signature"] == "old"
        assert merged[0]["needs_review"] is False
        assert stats["preserved_manual"] == 1

    def test_customized_same_signature_preserved(self) -> None:
        """Customized case with same signature is preserved without needs_review."""
        existing = [self._make_case("tc-1", customized=True, sig="same")]
        new = [self._make_case("tc-1", sig="same")]
        merged, stats = _merge_cases(new, existing)
        assert len(merged) == 1
        assert merged[0]["customized"] is True
        assert merged[0]["needs_review"] is False
        assert stats["preserved_custom"] == 1

    def test_customized_changed_signature_needs_review(self) -> None:
        """Customized case with changed signature gets needs_review=True."""
        existing = [self._make_case("tc-1", customized=True, sig="old-sig")]
        new = [self._make_case("tc-1", sig="new-sig")]
        merged, stats = _merge_cases(new, existing)
        assert len(merged) == 1
        assert merged[0]["customized"] is True
        assert merged[0]["needs_review"] is True
        assert merged[0]["last_generated_signature"] == "new-sig"
        assert stats["preserved_custom"] == 1

    def test_removed_manual_case_marked_stale(self) -> None:
        """Manual case not in new set is marked stale with needs_review."""
        existing = [self._make_case("tc-old", origin="manual")]
        merged, stats = _merge_cases([], existing)
        assert len(merged) == 1
        assert merged[0]["needs_review"] is True
        assert merged[0]["review_reason"] == "contract_entity_removed"
        assert stats["stale_custom_needs_review"] == 1

    def test_removed_customized_case_marked_stale(self) -> None:
        """Customized case not in new set is marked stale."""
        existing = [self._make_case("tc-old", customized=True)]
        merged, stats = _merge_cases([], existing)
        assert len(merged) == 1
        assert merged[0]["needs_review"] is True
        assert stats["stale_custom_needs_review"] == 1

    def test_removed_auto_case_dropped(self) -> None:
        """Auto-generated, non-customized case not in new set is dropped silently."""
        existing = [self._make_case("tc-old", origin="auto", customized=False)]
        merged, stats = _merge_cases([], existing)
        assert len(merged) == 0
        assert stats["stale_custom_needs_review"] == 0

    def test_merged_output_sorted_by_id(self) -> None:
        """Merged output is sorted by case ID."""
        new = [self._make_case("tc-b"), self._make_case("tc-a")]
        merged, _ = _merge_cases(new, [])
        assert [c["id"] for c in merged] == ["tc-a", "tc-b"]

    def test_full_merge_scenario(self) -> None:
        """Complex scenario: new + updated + preserved manual + preserved custom + stale."""
        existing = [
            self._make_case("tc-1", sig="old"),  # auto, will be updated
            self._make_case("tc-2", origin="manual"),  # manual, in new set
            self._make_case("tc-3", customized=True, sig="old"),  # customized, sig changes
            self._make_case("tc-4", origin="manual"),  # manual, NOT in new set -> stale
            self._make_case("tc-5", customized=True, sig="old"),  # customized, NOT in new set -> stale
        ]
        new = [
            self._make_case("tc-1", sig="new"),
            self._make_case("tc-2", sig="new"),
            self._make_case("tc-3", sig="new"),
            self._make_case("tc-6", sig="new"),  # brand new
        ]
        merged, stats = _merge_cases(new, existing)
        assert stats["new"] == 1  # tc-6
        assert stats["updated"] == 1  # tc-1
        assert stats["preserved_manual"] == 1  # tc-2
        assert stats["preserved_custom"] == 1  # tc-3
        assert stats["stale_custom_needs_review"] == 2  # tc-4, tc-5


class TestWriteTestrailCsv:
    """Tests for TestRail CSV output writer."""

    def test_writes_csv_with_header(self, tmp_path: Path) -> None:
        """CSV has correct header row and data rows."""
        cases = [
            {
                "title": "Test A",
                "suite": "GraphQL Contract",
                "preconditions": ["Pre 1", "Pre 2"],
                "steps": ["Do X", "Do Y"],
                "expected_result": "Pass",
            }
        ]
        csv_path = tmp_path / "out.csv"
        _write_testrail_csv(csv_path, cases)
        with csv_path.open(encoding="utf-8") as f:
            reader = list(csv.reader(f))
        assert reader[0] == ["title", "section", "preconditions", "steps", "expected_result"]
        assert reader[1][0] == "Test A"
        assert "1. Do X" in reader[1][3]
        assert "2. Do Y" in reader[1][3]

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Creates parent directories if they do not exist."""
        csv_path = tmp_path / "sub" / "dir" / "out.csv"
        _write_testrail_csv(csv_path, [])
        assert csv_path.exists()


class TestWriteZephyrJson:
    """Tests for Zephyr Scale JSON output writer."""

    def test_writes_valid_json(self, tmp_path: Path) -> None:
        """Writes JSON with testCases array."""
        cases = [
            {
                "title": "Case Z",
                "expected_result": "OK",
                "preconditions": ["Ready"],
                "protocol": "graphql",
                "check_type": "positive",
            }
        ]
        out = tmp_path / "zephyr.json"
        _write_zephyr_json(out, cases)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data["testCases"]) == 1
        assert data["testCases"][0]["name"] == "Case Z"
        assert "multi-protocol" in data["testCases"][0]["labels"]


class TestWriteMatrix:
    """Tests for test matrix JSON output."""

    def test_writes_matrix(self, tmp_path: Path) -> None:
        """Matrix output contains id, protocol, entity, check_type, suite."""
        cases = [{"id": "tc-1", "protocol": "grpc", "entity": "e", "check_type": "c", "suite": "s"}]
        out = tmp_path / "matrix.json"
        _write_matrix(out, cases)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data["matrix"]) == 1
        assert data["matrix"][0]["id"] == "tc-1"


class TestWriteFuzz:
    """Tests for fuzz scenario JSON output."""

    def test_writes_fuzz_scenarios(self, tmp_path: Path) -> None:
        """Fuzz output contains scenario_id, mutations, and expected."""
        cases = [{"id": "tc-1", "protocol": "graphql", "entity": "q:hello"}]
        out = tmp_path / "fuzz.json"
        _write_fuzz(out, cases)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data["scenarios"]) == 1
        assert data["scenarios"][0]["scenario_id"] == "fuzz-tc-1"
        assert "missing_required_fields" in data["scenarios"][0]["payload_mutations"]


# ---------------------------------------------------------------------------
# run_protocol_self_verify.py
# ---------------------------------------------------------------------------

from scripts.run_protocol_self_verify import (
    _contains_any,
    _parse_json,
    _post_json,
    _validate_url,
    _graphql_self_verify,
    _grpc_self_verify,
    _asyncapi_self_verify,
    _websocket_self_verify,
)


class TestParseJson:
    """Tests for safe JSON parsing."""

    def test_valid_json_dict(self) -> None:
        """Valid JSON dict is returned as-is."""
        assert _parse_json('{"a": 1}') == {"a": 1}

    def test_valid_json_non_dict_returns_none(self) -> None:
        """Valid JSON that is not a dict returns None."""
        assert _parse_json("[1, 2]") is None

    def test_invalid_json_returns_none(self) -> None:
        """Malformed JSON returns None."""
        assert _parse_json("not json") is None

    def test_empty_string_returns_none(self) -> None:
        """Empty string returns None."""
        assert _parse_json("") is None


class TestContainsAny:
    """Tests for case-insensitive substring matching."""

    def test_matches_case_insensitive(self) -> None:
        """Finds substring regardless of case."""
        assert _contains_any("Hello World", ["hello"]) is True

    def test_no_match(self) -> None:
        """Returns False when no key matches."""
        assert _contains_any("abc", ["xyz"]) is False

    def test_multiple_keys(self) -> None:
        """Returns True if any key matches."""
        assert _contains_any("data response", ["error", "data"]) is True

    def test_empty_keys(self) -> None:
        """Empty keys list returns False."""
        assert _contains_any("anything", []) is False


class TestValidateUrl:
    """Tests for URL validation with optional WebSocket scheme support."""

    def test_valid_http(self) -> None:
        """HTTP URL passes validation."""
        assert _validate_url("http://localhost:4010/graphql") is True

    def test_valid_https(self) -> None:
        """HTTPS URL passes validation."""
        assert _validate_url("https://api.example.com/v1") is True

    def test_ws_blocked_by_default(self) -> None:
        """WebSocket scheme is rejected unless allow_ws=True."""
        assert _validate_url("ws://localhost:8080") is False

    def test_ws_allowed(self) -> None:
        """WebSocket scheme passes when allow_ws=True."""
        assert _validate_url("ws://localhost:8080", allow_ws=True) is True

    def test_wss_allowed(self) -> None:
        """Secure WebSocket scheme passes when allow_ws=True."""
        assert _validate_url("wss://example.com/ws", allow_ws=True) is True

    def test_ftp_rejected(self) -> None:
        """FTP scheme is always rejected."""
        assert _validate_url("ftp://files.example.com") is False

    def test_missing_scheme(self) -> None:
        """URL without scheme is rejected."""
        assert _validate_url("localhost:4010") is False

    def test_missing_netloc(self) -> None:
        """URL without netloc is rejected."""
        assert _validate_url("http://") is False

    def test_empty_string(self) -> None:
        """Empty string is rejected."""
        assert _validate_url("") is False


class TestGraphqlSelfVerify:
    """Tests for GraphQL self-verification with mock HTTP responses."""

    def _mock_post(self, responses: list[tuple[int, str]]) -> Any:
        """Create a side_effect for _post_json that returns responses in order."""
        call_count = 0

        def side_effect(url: str, payload: dict, timeout: float) -> tuple[int, str]:
            nonlocal call_count
            idx = min(call_count, len(responses) - 1)
            call_count += 1
            return responses[idx]

        return side_effect

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_success_with_different_responses(self, mock_post: MagicMock) -> None:
        """Two different valid JSON responses pass verification."""
        mock_post.side_effect = self._mock_post([
            (200, '{"data": {"__typename": "Query"}}'),
            (200, '{"data": {"project": {"id": "1", "name": "Demo", "status": "active"}}}'),
        ])
        ok, detail = _graphql_self_verify("http://localhost:4010/graphql", 5.0)
        assert ok is True
        assert "passed" in detail

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_on_server_error(self, mock_post: MagicMock) -> None:
        """Server 500 response fails verification."""
        mock_post.side_effect = self._mock_post([(500, "Internal error")])
        ok, detail = _graphql_self_verify("http://localhost/gql", 5.0)
        assert ok is False
        assert "500" in detail

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_on_empty_body(self, mock_post: MagicMock) -> None:
        """Empty body response fails verification."""
        mock_post.side_effect = self._mock_post([(200, "")])
        ok, detail = _graphql_self_verify("http://localhost/gql", 5.0)
        assert ok is False
        assert "empty" in detail

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_on_non_json(self, mock_post: MagicMock) -> None:
        """Non-JSON body fails verification."""
        mock_post.side_effect = self._mock_post([(200, "<html>not json</html>")])
        ok, detail = _graphql_self_verify("http://localhost/gql", 5.0)
        assert ok is False
        assert "non-json" in detail

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_missing_data_errors_envelope(self, mock_post: MagicMock) -> None:
        """Response without 'data' or 'errors' key fails verification."""
        mock_post.side_effect = self._mock_post([(200, '{"result": "ok"}')])
        ok, detail = _graphql_self_verify("http://localhost/gql", 5.0)
        assert ok is False
        assert "envelope" in detail

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_irrelevant_response(self, mock_post: MagicMock) -> None:
        """Response that does not contain expected keys fails."""
        mock_post.side_effect = self._mock_post([(200, '{"data": {"unrelated": true}}')])
        ok, detail = _graphql_self_verify("http://localhost/gql", 5.0)
        assert ok is False
        assert "not relevant" in detail

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_identical_responses(self, mock_post: MagicMock) -> None:
        """Identical responses for different queries fail (meta-check)."""
        identical = '{"data": {"__typename": "Query", "project": {"id": "1", "name": "x", "status": "ok"}}}'
        mock_post.side_effect = self._mock_post([(200, identical), (200, identical)])
        ok, detail = _graphql_self_verify("http://localhost/gql", 5.0)
        assert ok is False
        assert "identical" in detail


class TestGrpcSelfVerify:
    """Tests for gRPC self-verification with mock HTTP responses."""

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_success(self, mock_post: MagicMock) -> None:
        """Two different valid responses pass gRPC verification."""
        mock_post.side_effect = [
            (200, '{"getproject": true, "project": {"id": "1", "status": "ok"}}'),
            (200, '{"createproject": true, "project": {"id": "2"}, "created": true}'),
        ]
        ok, detail = _grpc_self_verify("http://localhost/grpc", 5.0)
        assert ok is True

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_server_error(self, mock_post: MagicMock) -> None:
        """Server 500 fails gRPC verification."""
        mock_post.return_value = (500, "error")
        ok, detail = _grpc_self_verify("http://localhost/grpc", 5.0)
        assert ok is False
        assert "500" in detail

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_empty_body(self, mock_post: MagicMock) -> None:
        """Empty body fails gRPC verification."""
        mock_post.return_value = (200, "  ")
        ok, detail = _grpc_self_verify("http://localhost/grpc", 5.0)
        assert ok is False
        assert "empty" in detail

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_non_json(self, mock_post: MagicMock) -> None:
        """Non-JSON body fails gRPC verification."""
        mock_post.return_value = (200, "not json")
        ok, detail = _grpc_self_verify("http://localhost/grpc", 5.0)
        assert ok is False
        assert "non-json" in detail

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_not_relevant(self, mock_post: MagicMock) -> None:
        """Response without expected keys fails gRPC verification."""
        mock_post.return_value = (200, '{"unrelated": true}')
        ok, detail = _grpc_self_verify("http://localhost/grpc", 5.0)
        assert ok is False
        assert "not relevant" in detail

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_identical_responses(self, mock_post: MagicMock) -> None:
        """Identical responses for different methods fail gRPC verification."""
        same = '{"getproject": true, "createproject": true, "project": {"id": "1"}, "status": "ok", "created": true}'
        mock_post.side_effect = [(200, same), (200, same)]
        ok, detail = _grpc_self_verify("http://localhost/grpc", 5.0)
        assert ok is False
        assert "identical" in detail


class TestAsyncapiSelfVerify:
    """Tests for AsyncAPI self-verification."""

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_success_http(self, mock_post: MagicMock) -> None:
        """HTTP publish with different responses passes."""
        mock_post.side_effect = [
            (200, '{"project.updated": true, "project": {}, "ack": true}'),
            (200, '{"task.completed": true, "task": {}, "ack": true}'),
        ]
        ok, detail = _asyncapi_self_verify("http://localhost/events", "", 5.0)
        assert ok is True

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_identical_http(self, mock_post: MagicMock) -> None:
        """Identical HTTP responses fail."""
        same = '{"project.updated": true, "task.completed": true, "project": {}, "task": {}, "ack": true}'
        mock_post.side_effect = [(200, same), (200, same)]
        ok, detail = _asyncapi_self_verify("http://localhost/events", "", 5.0)
        assert ok is False
        assert "identical" in detail

    def test_ws_only_endpoint(self) -> None:
        """WS-only endpoint returns informational failure."""
        ok, detail = _asyncapi_self_verify("", "ws://localhost:8080", 5.0)
        assert ok is False
        assert "ws-only" in detail

    def test_missing_endpoints(self) -> None:
        """Missing both endpoints fails."""
        ok, detail = _asyncapi_self_verify("", "", 5.0)
        assert ok is False
        assert "missing" in detail

    def test_ws_only_invalid_url(self) -> None:
        """Invalid WS URL fails validation."""
        ok, detail = _asyncapi_self_verify("", "not-a-url", 5.0)
        assert ok is False
        assert "invalid" in detail

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_server_error(self, mock_post: MagicMock) -> None:
        """Server 500 on HTTP publish fails."""
        mock_post.return_value = (500, "error")
        ok, detail = _asyncapi_self_verify("http://localhost/events", "", 5.0)
        assert ok is False
        assert "500" in detail

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_empty_body(self, mock_post: MagicMock) -> None:
        """Empty body fails asyncapi HTTP verification."""
        mock_post.return_value = (200, "")
        ok, detail = _asyncapi_self_verify("http://localhost/events", "", 5.0)
        assert ok is False
        assert "empty" in detail

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_non_json(self, mock_post: MagicMock) -> None:
        """Non-JSON body fails asyncapi verification."""
        mock_post.return_value = (200, "not-json")
        ok, detail = _asyncapi_self_verify("http://localhost/events", "", 5.0)
        assert ok is False
        assert "non-json" in detail

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_not_relevant(self, mock_post: MagicMock) -> None:
        """Response without expected keys fails asyncapi verification."""
        mock_post.return_value = (200, '{"other": true}')
        ok, detail = _asyncapi_self_verify("http://localhost/events", "", 5.0)
        assert ok is False
        assert "not relevant" in detail


class TestWebsocketSelfVerify:
    """Tests for WebSocket self-verification."""

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_success_http_bridge(self, mock_post: MagicMock) -> None:
        """HTTP bridge with different responses passes."""
        mock_post.side_effect = [
            (200, '{"subscribe": true, "project.updated": true, "ack": true}'),
            (200, '{"publish": true, "task.completed": true, "ack": true}'),
        ]
        ok, detail = _websocket_self_verify("ws://localhost", "http://localhost/bridge", 5.0)
        assert ok is True

    def test_ws_only_valid_url(self) -> None:
        """WS-only with valid URL returns informational failure."""
        ok, detail = _websocket_self_verify("ws://localhost:8080", "", 5.0)
        assert ok is False
        assert "ws-only" in detail

    def test_ws_only_invalid_url(self) -> None:
        """Invalid WS URL fails validation."""
        ok, detail = _websocket_self_verify("bad-url", "", 5.0)
        assert ok is False
        assert "invalid" in detail

    def test_missing_both_endpoints(self) -> None:
        """Missing both endpoints fails."""
        ok, detail = _websocket_self_verify("", "", 5.0)
        assert ok is False
        assert "missing" in detail

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_server_error(self, mock_post: MagicMock) -> None:
        """Server 500 on HTTP bridge fails."""
        mock_post.return_value = (500, "error")
        ok, detail = _websocket_self_verify("", "http://localhost/bridge", 5.0)
        assert ok is False
        assert "500" in detail

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_empty_body(self, mock_post: MagicMock) -> None:
        """Empty body fails websocket verification."""
        mock_post.return_value = (200, "")
        ok, detail = _websocket_self_verify("", "http://localhost/bridge", 5.0)
        assert ok is False
        assert "empty" in detail

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_non_json(self, mock_post: MagicMock) -> None:
        """Non-JSON body fails websocket verification."""
        mock_post.return_value = (200, "not-json")
        ok, detail = _websocket_self_verify("", "http://localhost/bridge", 5.0)
        assert ok is False
        assert "non-json" in detail

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_not_relevant(self, mock_post: MagicMock) -> None:
        """Response without expected keys fails websocket verification."""
        mock_post.return_value = (200, '{"other": true}')
        ok, detail = _websocket_self_verify("", "http://localhost/bridge", 5.0)
        assert ok is False
        assert "not relevant" in detail

    @patch("scripts.run_protocol_self_verify._post_json")
    def test_fail_identical_responses(self, mock_post: MagicMock) -> None:
        """Identical responses for different actions fail."""
        same = '{"subscribe": true, "publish": true, "project.updated": true, "task.completed": true, "ack": true}'
        mock_post.side_effect = [(200, same), (200, same)]
        ok, detail = _websocket_self_verify("", "http://localhost/bridge", 5.0)
        assert ok is False
        assert "identical" in detail


# ---------------------------------------------------------------------------
# upload_api_test_assets.py
# ---------------------------------------------------------------------------

from scripts.upload_api_test_assets import (
    _http_json,
    _load_cases,
    _testrail_headers,
    _upload_testrail,
    _upload_zephyr_scale,
)


class TestTestrailHeaders:
    """Tests for TestRail authentication header building."""

    def test_base64_encoding(self) -> None:
        """Produces correct Basic auth header with base64 encoding."""
        headers = _testrail_headers("user@example.com", "secret123")
        expected_token = base64.b64encode(b"user@example.com:secret123").decode("ascii")
        assert headers["Authorization"] == f"Basic {expected_token}"


class TestLoadCases:
    """Tests for test case loading from JSON file."""

    def test_load_valid(self, tmp_path: Path) -> None:
        """Loads list of case dicts from JSON file."""
        f = tmp_path / "cases.json"
        f.write_text('{"cases": [{"id": "1"}, {"id": "2"}]}', encoding="utf-8")
        assert len(_load_cases(f)) == 2

    def test_load_non_dict_root(self, tmp_path: Path) -> None:
        """Non-dict root JSON returns empty list."""
        f = tmp_path / "cases.json"
        f.write_text("[1,2]", encoding="utf-8")
        assert _load_cases(f) == []

    def test_load_non_list_cases(self, tmp_path: Path) -> None:
        """Non-list 'cases' value returns empty list."""
        f = tmp_path / "cases.json"
        f.write_text('{"cases": "not a list"}', encoding="utf-8")
        assert _load_cases(f) == []

    def test_load_filters_non_dicts(self, tmp_path: Path) -> None:
        """Non-dict entries in cases list are filtered out."""
        f = tmp_path / "cases.json"
        f.write_text('{"cases": [{"id": "ok"}, "string", 42]}', encoding="utf-8")
        result = _load_cases(f)
        assert len(result) == 1


class TestUploadTestrail:
    """Tests for TestRail upload with two-tier fallback."""

    @patch("scripts.upload_api_test_assets._http_json")
    def test_successful_upload(self, mock_http: MagicMock) -> None:
        """All cases uploaded on first try."""
        mock_http.return_value = {"id": 1}
        cases = [
            {
                "title": "Case A",
                "preconditions": ["Pre1"],
                "steps": ["Step1", "Step2"],
                "expected_result": "OK",
                "traceability": {"method": "GET", "path": "/users"},
                "operation_id": "listUsers",
            }
        ]
        result = _upload_testrail(
            base_url="https://testrail.example.com",
            email="user@test.com",
            api_key="key",
            section_id="100",
            suite_id="200",
            cases=cases,
            preconds_field="custom_preconds",
            steps_field="custom_steps",
            expected_field="custom_expected",
        )
        assert result["created"] == 1
        assert result["errors"] == []

    @patch("scripts.upload_api_test_assets._http_json")
    def test_fallback_on_first_failure(self, mock_http: MagicMock) -> None:
        """Falls back to minimal payload (title only) when full payload fails."""
        mock_http.side_effect = [RuntimeError("field error"), {"id": 1}]
        cases = [{"title": "Case A", "preconditions": [], "steps": [], "expected_result": "ok"}]
        result = _upload_testrail(
            base_url="https://testrail.example.com",
            email="u@t.com",
            api_key="k",
            section_id="1",
            suite_id="",
            cases=cases,
            preconds_field="p",
            steps_field="s",
            expected_field="e",
        )
        assert result["created"] == 1
        assert result["errors"] == []
        assert mock_http.call_count == 2

    @patch("scripts.upload_api_test_assets._http_json")
    def test_both_tiers_fail(self, mock_http: MagicMock) -> None:
        """Records error when both full and fallback payloads fail."""
        mock_http.side_effect = RuntimeError("fail")
        cases = [{"title": "Case A", "preconditions": [], "steps": [], "expected_result": ""}]
        result = _upload_testrail(
            base_url="https://testrail.example.com",
            email="u@t.com",
            api_key="k",
            section_id="1",
            suite_id="",
            cases=cases,
            preconds_field="p",
            steps_field="s",
            expected_field="e",
        )
        assert result["created"] == 0
        assert len(result["errors"]) == 1
        assert "fallback failed" in result["errors"][0]

    @patch("scripts.upload_api_test_assets._http_json")
    def test_skips_empty_title(self, mock_http: MagicMock) -> None:
        """Cases with empty title are skipped."""
        cases = [{"title": "", "preconditions": [], "steps": [], "expected_result": ""}]
        result = _upload_testrail(
            base_url="https://testrail.example.com",
            email="u@t.com",
            api_key="k",
            section_id="1",
            suite_id="",
            cases=cases,
            preconds_field="p",
            steps_field="s",
            expected_field="e",
        )
        assert result["created"] == 0
        assert mock_http.call_count == 0

    @patch("scripts.upload_api_test_assets._http_json")
    def test_needs_review_flag_sent(self, mock_http: MagicMock) -> None:
        """Cases with needs_review=True include custom_needs_review in payload."""
        mock_http.return_value = {"id": 1}
        cases = [{"title": "Review", "needs_review": True, "preconditions": [], "steps": [], "expected_result": ""}]
        _upload_testrail(
            base_url="https://tr.com",
            email="u@t.com",
            api_key="k",
            section_id="1",
            suite_id="",
            cases=cases,
            preconds_field="p",
            steps_field="s",
            expected_field="e",
        )
        payload_sent = mock_http.call_args[1]["payload"]
        assert payload_sent["custom_needs_review"] is True

    @patch("scripts.upload_api_test_assets._http_json")
    def test_suite_id_in_url(self, mock_http: MagicMock) -> None:
        """Suite ID is appended to section URL when provided."""
        mock_http.return_value = {"id": 1}
        cases = [{"title": "T", "preconditions": [], "steps": [], "expected_result": ""}]
        _upload_testrail(
            base_url="https://tr.com",
            email="u@t.com",
            api_key="k",
            section_id="10",
            suite_id="20",
            cases=cases,
            preconds_field="p",
            steps_field="s",
            expected_field="e",
        )
        url_called = mock_http.call_args_list[0][0][1]
        assert "suite_id=20" in url_called


class TestUploadZephyrScale:
    """Tests for Zephyr Scale upload."""

    @patch("scripts.upload_api_test_assets._http_json")
    def test_successful_upload(self, mock_http: MagicMock) -> None:
        """Cases are uploaded with correct payload structure."""
        mock_http.return_value = {"id": 1}
        cases = [
            {
                "title": "Z Case",
                "expected_result": "Pass",
                "preconditions": ["Ready"],
                "steps": ["Do X"],
                "needs_review": False,
            }
        ]
        result = _upload_zephyr_scale(
            base_url="https://api.zephyr.com/v2",
            api_token="token123",
            project_key="PROJ",
            folder_id="folder-1",
            cases=cases,
        )
        assert result["created"] == 1
        assert result["errors"] == []
        payload_sent = mock_http.call_args[1]["payload"]
        assert payload_sent["projectKey"] == "PROJ"
        assert payload_sent["folder"] == {"id": "folder-1"}

    @patch("scripts.upload_api_test_assets._http_json")
    def test_needs_review_label(self, mock_http: MagicMock) -> None:
        """Cases with needs_review get 'needs-review' label."""
        mock_http.return_value = {"id": 1}
        cases = [{"title": "R", "expected_result": "", "preconditions": [], "steps": [], "needs_review": True}]
        _upload_zephyr_scale(
            base_url="https://z.com/v2",
            api_token="t",
            project_key="P",
            folder_id="",
            cases=cases,
        )
        payload_sent = mock_http.call_args[1]["payload"]
        assert "needs-review" in payload_sent["labels"]

    @patch("scripts.upload_api_test_assets._http_json")
    def test_no_folder_when_empty(self, mock_http: MagicMock) -> None:
        """Folder key is omitted when folder_id is empty."""
        mock_http.return_value = {"id": 1}
        cases = [{"title": "C", "expected_result": "", "preconditions": [], "steps": []}]
        _upload_zephyr_scale(
            base_url="https://z.com/v2",
            api_token="t",
            project_key="P",
            folder_id="",
            cases=cases,
        )
        payload_sent = mock_http.call_args[1]["payload"]
        assert "folder" not in payload_sent

    @patch("scripts.upload_api_test_assets._http_json")
    def test_upload_failure_recorded(self, mock_http: MagicMock) -> None:
        """Upload errors are recorded in result."""
        mock_http.side_effect = RuntimeError("connection failed")
        cases = [{"title": "F", "expected_result": "", "preconditions": [], "steps": []}]
        result = _upload_zephyr_scale(
            base_url="https://z.com/v2",
            api_token="t",
            project_key="P",
            folder_id="",
            cases=cases,
        )
        assert result["created"] == 0
        assert len(result["errors"]) == 1

    @patch("scripts.upload_api_test_assets._http_json")
    def test_skips_empty_title(self, mock_http: MagicMock) -> None:
        """Cases with empty title are skipped."""
        cases = [{"title": "  ", "expected_result": "", "preconditions": [], "steps": []}]
        result = _upload_zephyr_scale(
            base_url="https://z.com/v2",
            api_token="t",
            project_key="P",
            folder_id="",
            cases=cases,
        )
        assert result["created"] == 0
        assert mock_http.call_count == 0


# ---------------------------------------------------------------------------
# self_verify_prodlike_user_path.py
# ---------------------------------------------------------------------------

from scripts.self_verify_prodlike_user_path import call_json, require


class TestRequire:
    """Tests for assertion helper."""

    def test_passes_on_true(self) -> None:
        """No exception when condition is True."""
        require(True, "should not raise")

    def test_raises_on_false(self) -> None:
        """RuntimeError raised when condition is False."""
        with pytest.raises(RuntimeError, match="failed check"):
            require(False, "failed check")


class TestCallJson:
    """Tests for HTTP request wrapper."""

    @patch("scripts.self_verify_prodlike_user_path.urllib.request.urlopen")
    def test_successful_get(self, mock_urlopen: MagicMock) -> None:
        """Successful GET returns status and parsed JSON body."""
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = b'{"id": "usr-1"}'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp
        status, body = call_json("GET", "http://localhost/v1/users/me")
        assert status == 200
        assert body == {"id": "usr-1"}

    @patch("scripts.self_verify_prodlike_user_path.urllib.request.urlopen")
    def test_http_error(self, mock_urlopen: MagicMock) -> None:
        """HTTP error returns error status and parsed error body."""
        error = urllib.error.HTTPError(
            url="http://localhost/v1/fail",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=BytesIO(b'{"error": "not found"}'),
        )
        mock_urlopen.side_effect = error
        status, body = call_json("GET", "http://localhost/v1/fail")
        assert status == 404
        assert body == {"error": "not found"}

    @patch("scripts.self_verify_prodlike_user_path.urllib.request.urlopen")
    def test_empty_response_body(self, mock_urlopen: MagicMock) -> None:
        """Empty response body returns None for body."""
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 204
        mock_resp.read.return_value = b""
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp
        status, body = call_json("DELETE", "http://localhost/v1/item/1")
        assert status == 204
        assert body is None


# ---------------------------------------------------------------------------
# run_api_first_flow.py
# ---------------------------------------------------------------------------

from scripts.run_api_first_flow import (
    _SpecBundler,
    _print_compact_output,
    _read_yaml,
    _resolve_docs_root,
    build_sandbox_page_url,
    bundle_openapi_spec,
    copy_spec_to_docs,
    ensure_file,
    run,
    run_first_available,
    self_verify_stub_coverage,
    sync_playground_sandbox_url,
)


class TestEnsureFile:
    """Tests for file existence check."""

    def test_existing_file_passes(self, tmp_path: Path) -> None:
        """No exception for existing file."""
        f = tmp_path / "exists.txt"
        f.write_text("ok", encoding="utf-8")
        ensure_file(f, "test file")

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        """FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError, match="Missing test label"):
            ensure_file(tmp_path / "nope.txt", "test label")


class TestCopySpecToDocs:
    """Tests for spec directory copy."""

    def test_copies_tree(self, tmp_path: Path) -> None:
        """Copies entire directory tree to target."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "a.yaml").write_text("a: 1", encoding="utf-8")
        dst = tmp_path / "dst"
        copy_spec_to_docs(src, dst)
        assert (dst / "a.yaml").exists()

    def test_overwrites_existing_target(self, tmp_path: Path) -> None:
        """Removes existing target before copying."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "new.yaml").write_text("new: 1", encoding="utf-8")
        dst = tmp_path / "dst"
        dst.mkdir()
        (dst / "old.yaml").write_text("old: 1", encoding="utf-8")
        copy_spec_to_docs(src, dst)
        assert (dst / "new.yaml").exists()
        assert not (dst / "old.yaml").exists()


class TestPrintCompactOutput:
    """Tests for compact output printing."""

    def test_short_output_prints_all(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Output shorter than max_lines prints all lines."""
        _print_compact_output("line1\nline2\nline3", max_lines=10)
        captured = capsys.readouterr().out
        assert "line1" in captured
        assert "line2" in captured

    def test_long_output_truncated(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Output longer than max_lines shows head + tail with omitted count."""
        lines = "\n".join(f"line{i}" for i in range(100))
        _print_compact_output(lines, max_lines=20)
        captured = capsys.readouterr().out
        assert "omitted" in captured

    def test_empty_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Empty output prints nothing."""
        _print_compact_output("")
        assert capsys.readouterr().out == ""

    def test_blank_lines_filtered(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Blank lines are filtered before counting."""
        _print_compact_output("a\n\n\nb", max_lines=10)
        captured = capsys.readouterr().out
        assert "a" in captured
        assert "b" in captured


class TestSpecBundler:
    """Tests for OpenAPI $ref resolution and bundling."""

    def test_simple_ref_resolution(self, tmp_path: Path) -> None:
        """Resolves a simple $ref to an external file."""
        schema_dir = tmp_path / "components" / "schemas"
        schema_dir.mkdir(parents=True)
        (schema_dir / "User.yaml").write_text(
            "type: object\nproperties:\n  id:\n    type: string\n",
            encoding="utf-8",
        )
        spec = tmp_path / "openapi.yaml"
        spec.write_text(
            yaml.safe_dump({
                "openapi": "3.0.3",
                "info": {"title": "Test", "version": "1.0"},
                "paths": {},
                "components": {
                    "schemas": {
                        "User": {"$ref": "components/schemas/User.yaml"},
                    }
                },
            }),
            encoding="utf-8",
        )
        bundler = _SpecBundler()
        result = bundler.bundle(spec)
        user_schema = result["components"]["schemas"]["User"]
        assert user_schema["type"] == "object"

    def test_nested_ref_resolution(self, tmp_path: Path) -> None:
        """Resolves nested $ref chains (A -> B -> value)."""
        schema_dir = tmp_path / "components" / "schemas"
        schema_dir.mkdir(parents=True)
        (schema_dir / "Address.yaml").write_text(
            "type: object\nproperties:\n  city:\n    type: string\n",
            encoding="utf-8",
        )
        (schema_dir / "User.yaml").write_text(
            yaml.safe_dump({
                "type": "object",
                "properties": {
                    "address": {"$ref": "Address.yaml"},
                },
            }),
            encoding="utf-8",
        )
        spec = tmp_path / "openapi.yaml"
        spec.write_text(
            yaml.safe_dump({
                "openapi": "3.0.3",
                "info": {"title": "T", "version": "1"},
                "paths": {},
                "components": {
                    "schemas": {
                        "User": {"$ref": "components/schemas/User.yaml"},
                    }
                },
            }),
            encoding="utf-8",
        )
        bundler = _SpecBundler()
        result = bundler.bundle(spec)
        user = result["components"]["schemas"]["User"]
        assert user["properties"]["address"]["type"] == "object"

    def test_json_pointer_resolution(self, tmp_path: Path) -> None:
        """Resolves $ref with JSON pointer (file.yaml#/path/to/node)."""
        ref_file = tmp_path / "defs.yaml"
        ref_file.write_text(
            yaml.safe_dump({
                "definitions": {
                    "Error": {"type": "object", "properties": {"message": {"type": "string"}}},
                }
            }),
            encoding="utf-8",
        )
        spec = tmp_path / "openapi.yaml"
        spec.write_text(
            yaml.safe_dump({
                "openapi": "3.0.3",
                "info": {"title": "T", "version": "1"},
                "paths": {},
                "components": {
                    "schemas": {
                        "Error": {"$ref": "defs.yaml#/definitions/Error"},
                    }
                },
            }),
            encoding="utf-8",
        )
        bundler = _SpecBundler()
        result = bundler.bundle(spec)
        assert result["components"]["schemas"]["Error"]["type"] == "object"

    def test_internal_ref_rewrite(self) -> None:
        """Internal ref #/Name is rewritten to #/components/schemas/Name."""
        bundler = _SpecBundler()
        result = bundler._resolve_ref("#User", Path("/tmp"))
        assert result == {"$ref": "#/components/schemas/User"}

    def test_pointer_tilde_escaping(self) -> None:
        """JSON pointer with ~0 and ~1 escapes are decoded."""
        bundler = _SpecBundler()
        data = {"a/b": {"c~d": "found"}}
        result = bundler._resolve_pointer(data, "/a~1b/c~0d")
        assert result == "found"

    def test_resolve_pointer_list_index(self) -> None:
        """JSON pointer resolves numeric indices in lists."""
        bundler = _SpecBundler()
        data = {"items": ["zero", "one", "two"]}
        result = bundler._resolve_pointer(data, "/items/1")
        assert result == "one"

    def test_resolve_pointer_invalid_key(self) -> None:
        """JSON pointer raises KeyError for invalid key on non-dict/list."""
        bundler = _SpecBundler()
        with pytest.raises(KeyError):
            bundler._resolve_pointer("string", "/invalid")

    def test_collect_schemas_from_allof(self, tmp_path: Path) -> None:
        """_collect_schemas_from_file picks up allOf schemas."""
        f = tmp_path / "schemas" / "Extended.yaml"
        f.parent.mkdir(parents=True)
        f.write_text(
            yaml.safe_dump({
                "ExtendedUser": {
                    "allOf": [
                        {"type": "object", "properties": {"name": {"type": "string"}}},
                    ]
                }
            }),
            encoding="utf-8",
        )
        bundler = _SpecBundler()
        bundler._collect_schemas_from_file(f)
        assert "ExtendedUser" in bundler._schemas

    def test_missing_ref_file_raises(self, tmp_path: Path) -> None:
        """Missing $ref file raises FileNotFoundError."""
        bundler = _SpecBundler()
        with pytest.raises(FileNotFoundError):
            bundler._resolve_ref("nonexistent.yaml", tmp_path)

    def test_file_cache(self, tmp_path: Path) -> None:
        """YAML files are cached after first load."""
        f = tmp_path / "cached.yaml"
        f.write_text("key: value", encoding="utf-8")
        bundler = _SpecBundler()
        r1 = bundler._load_yaml(f)
        r2 = bundler._load_yaml(f)
        assert r1 is r2

    def test_deep_resolve_list(self) -> None:
        """_deep_resolve processes list items recursively."""
        bundler = _SpecBundler()
        data = [{"key": "val"}, "str", 42]
        result = bundler._deep_resolve(data, Path("/tmp"))
        assert result == [{"key": "val"}, "str", 42]

    def test_deep_resolve_scalar(self) -> None:
        """_deep_resolve returns scalars unchanged."""
        bundler = _SpecBundler()
        assert bundler._deep_resolve(42, Path("/tmp")) == 42
        assert bundler._deep_resolve("text", Path("/tmp")) == "text"


class TestBundleOpenapiSpec:
    """Tests for the full bundle_openapi_spec function."""

    def test_writes_yaml_and_json(self, tmp_path: Path) -> None:
        """Writes both bundled YAML and JSON files."""
        spec = tmp_path / "openapi.yaml"
        spec.write_text(
            yaml.safe_dump({
                "openapi": "3.0.3",
                "info": {"title": "T", "version": "1"},
                "paths": {},
            }),
            encoding="utf-8",
        )
        out = tmp_path / "bundled.yaml"
        bundle_openapi_spec(spec, out)
        assert out.exists()
        assert out.with_suffix(".json").exists()
        data = yaml.safe_load(out.read_text(encoding="utf-8"))
        assert data["openapi"] == "3.0.3"


class TestBuildSandboxPageUrl:
    """Tests for sandbox page URL building."""

    def test_mkdocs_with_site_url(self, tmp_path: Path) -> None:
        """MkDocs provider uses site_url from mkdocs.yml."""
        mkdocs = tmp_path / "mkdocs.yml"
        mkdocs.write_text(yaml.safe_dump({"site_url": "https://docs.example.com"}), encoding="utf-8")
        url = build_sandbox_page_url(tmp_path, "mkdocs")
        assert url == "https://docs.example.com/reference/taskstream-api-playground/"

    def test_mkdocs_without_site_url(self, tmp_path: Path) -> None:
        """MkDocs without site_url returns relative path."""
        mkdocs = tmp_path / "mkdocs.yml"
        mkdocs.write_text(yaml.safe_dump({"theme": "material"}), encoding="utf-8")
        url = build_sandbox_page_url(tmp_path, "mkdocs")
        assert url == "/reference/taskstream-api-playground/"

    def test_docusaurus(self, tmp_path: Path) -> None:
        """Docusaurus provider returns docs-prefixed path."""
        url = build_sandbox_page_url(tmp_path, "docusaurus")
        assert url == "/docs/reference/taskstream-api-playground"

    def test_unknown_provider(self, tmp_path: Path) -> None:
        """Unknown provider returns default relative path."""
        url = build_sandbox_page_url(tmp_path, "hugo")
        assert url == "/reference/taskstream-api-playground/"


class TestSyncPlaygroundSandboxUrl:
    """Tests for mkdocs.yml playground endpoint sync."""

    def test_syncs_url(self, tmp_path: Path) -> None:
        """Updates both plg and legacy sandbox_base_url in mkdocs.yml."""
        mkdocs = tmp_path / "mkdocs.yml"
        mkdocs.write_text(yaml.safe_dump({"site_name": "Test"}), encoding="utf-8")
        sync_playground_sandbox_url(tmp_path, "https://mock.example.com/v1")
        data = yaml.safe_load(mkdocs.read_text(encoding="utf-8"))
        assert data["extra"]["plg"]["api_playground"]["endpoints"]["sandbox_base_url"] == "https://mock.example.com/v1"
        assert data["extra"]["api_playground"]["sandbox_base_url"] == "https://mock.example.com/v1"

    def test_skip_when_no_mkdocs(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Skips sync when mkdocs.yml does not exist."""
        sync_playground_sandbox_url(tmp_path, "https://mock.example.com/v1")
        assert "skip" in capsys.readouterr().out.lower()

    def test_skip_when_non_mapping(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Skips sync when mkdocs.yml content is not a mapping."""
        mkdocs = tmp_path / "mkdocs.yml"
        mkdocs.write_text("- item1\n- item2\n", encoding="utf-8")
        sync_playground_sandbox_url(tmp_path, "https://mock.example.com/v1")
        assert "skip" in capsys.readouterr().out.lower()


class TestSelfVerifyStubCoverage:
    """Tests for operationId stub coverage verification."""

    def test_all_operations_covered(self, tmp_path: Path) -> None:
        """Passes when all operationIds have handler functions."""
        spec = tmp_path / "openapi.yaml"
        spec.write_text(
            yaml.safe_dump({
                "openapi": "3.0.3",
                "info": {"title": "T", "version": "1"},
                "paths": {
                    "/users": {
                        "get": {"operationId": "listUsers"},
                        "post": {"operationId": "createUser"},
                    }
                },
            }),
            encoding="utf-8",
        )
        stubs = tmp_path / "main.py"
        stubs.write_text(
            "def listUsers():\n    pass\n\ndef createUser():\n    pass\n",
            encoding="utf-8",
        )
        self_verify_stub_coverage(spec, stubs)

    def test_missing_operation_raises(self, tmp_path: Path) -> None:
        """Raises RuntimeError when operationId handler is missing."""
        spec = tmp_path / "openapi.yaml"
        spec.write_text(
            yaml.safe_dump({
                "openapi": "3.0.3",
                "info": {"title": "T", "version": "1"},
                "paths": {
                    "/users": {"get": {"operationId": "listUsers"}},
                },
            }),
            encoding="utf-8",
        )
        stubs = tmp_path / "main.py"
        stubs.write_text("def otherFunc():\n    pass\n", encoding="utf-8")
        with pytest.raises(RuntimeError, match="listUsers"):
            self_verify_stub_coverage(spec, stubs)

    def test_ref_path_resolution(self, tmp_path: Path) -> None:
        """Resolves $ref in paths to external file."""
        paths_file = tmp_path / "paths" / "users.yaml"
        paths_file.parent.mkdir()
        paths_file.write_text(
            yaml.safe_dump({
                "get": {"operationId": "listUsers"},
            }),
            encoding="utf-8",
        )
        spec = tmp_path / "openapi.yaml"
        spec.write_text(
            yaml.safe_dump({
                "openapi": "3.0.3",
                "info": {"title": "T", "version": "1"},
                "paths": {
                    "/users": {"$ref": "paths/users.yaml"},
                },
            }),
            encoding="utf-8",
        )
        stubs = tmp_path / "main.py"
        stubs.write_text("def listUsers():\n    pass\n", encoding="utf-8")
        self_verify_stub_coverage(spec, stubs)


class TestReadYaml:
    """Tests for _read_yaml helper."""

    def test_valid_yaml(self, tmp_path: Path) -> None:
        """Returns dict from valid YAML file."""
        f = tmp_path / "cfg.yml"
        f.write_text("docs_root: docs/en", encoding="utf-8")
        assert _read_yaml(f) == {"docs_root": "docs/en"}

    def test_non_mapping_raises(self, tmp_path: Path) -> None:
        """Raises ValueError when YAML is not a mapping."""
        f = tmp_path / "cfg.yml"
        f.write_text("- a\n- b\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Expected YAML mapping"):
            _read_yaml(f)


class TestResolveDocsRoot:
    """Tests for _resolve_docs_root helper."""

    def test_returns_fallback_when_no_config(self) -> None:
        """Returns fallback when runtime_config is None."""
        assert _resolve_docs_root(None, "docs") == "docs"

    def test_returns_fallback_when_config_missing(self, tmp_path: Path) -> None:
        """Returns fallback when config file does not exist."""
        assert _resolve_docs_root(tmp_path / "missing.yml", "docs") == "docs"

    def test_returns_config_value(self, tmp_path: Path) -> None:
        """Returns docs_root from config file."""
        f = tmp_path / "runtime.yml"
        f.write_text("docs_root: docs/en\n", encoding="utf-8")
        assert _resolve_docs_root(f, "docs") == "docs/en"

    def test_empty_config_value_uses_fallback(self, tmp_path: Path) -> None:
        """Empty docs_root in config falls back to default."""
        f = tmp_path / "runtime.yml"
        f.write_text("docs_root: ''\n", encoding="utf-8")
        assert _resolve_docs_root(f, "docs") == "docs"


class TestRunFunction:
    """Tests for the run() subprocess wrapper."""

    def test_successful_command(self) -> None:
        """Successful command does not raise."""
        run(["python3", "-c", "print('hello')"])

    def test_failing_command_raises(self) -> None:
        """Non-zero exit code raises CalledProcessError."""
        with pytest.raises(subprocess.CalledProcessError):
            run(["python3", "-c", "import sys; sys.exit(1)"])

    def test_summary_label_printed(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Summary label is printed on success."""
        run(["python3", "-c", "pass"], summary_label="test passed")
        assert "test passed" in capsys.readouterr().out

    def test_compact_mode(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Compact mode uses _print_compact_output."""
        run(["python3", "-c", "print('hello')"], compact=True)
        assert "hello" in capsys.readouterr().out


class TestRunFirstAvailable:
    """Tests for fallback command execution."""

    def test_first_available_succeeds(self, tmp_path: Path) -> None:
        """Runs first available command and succeeds."""
        run_first_available(
            [["python3", "-c", "print('ok')"]],
            cwd=tmp_path,
        )

    def test_skips_missing_binary(self, tmp_path: Path) -> None:
        """Skips candidates where binary is not found (non-npx)."""
        run_first_available(
            [
                ["nonexistent_binary_xyz_abc", "--version"],
                ["python3", "-c", "print('fallback')"],
            ],
            cwd=tmp_path,
        )

    def test_no_candidates_raises(self, tmp_path: Path) -> None:
        """Raises RuntimeError when no candidate is available."""
        with pytest.raises(RuntimeError, match="No available"):
            run_first_available(
                [["nonexistent_binary_1"], ["nonexistent_binary_2"]],
                cwd=tmp_path,
            )

    def test_all_fail_raises_last_error(self, tmp_path: Path) -> None:
        """Raises RuntimeError with last error when all candidates fail."""
        with pytest.raises(RuntimeError, match="Unable to execute"):
            run_first_available(
                [["python3", "-c", "import sys; sys.exit(1)"]],
                cwd=tmp_path,
            )

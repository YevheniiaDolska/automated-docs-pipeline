"""Tests for the OpenAPI -> agent tool manifest generator."""

from __future__ import annotations

from scripts import generate_agent_manifest as mod

_SPEC = {
    "openapi": "3.0.3",
    "servers": [{"url": "https://api.example.com/v1"}],
    "paths": {
        "/tasks/{task_id}": {
            "parameters": [
                {"name": "task_id", "in": "path", "required": True, "schema": {"type": "string"},
                 "description": "Task id"},
            ],
            "get": {
                "operationId": "getTask",
                "summary": "Get a task",
                "description": "Return one task.",
                "parameters": [{"name": "fields", "in": "query", "schema": {"type": "string"}}],
            },
            "put": {
                "summary": "Replace a task",  # no operationId -> slug fallback
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Task"}}},
                },
            },
        }
    },
    "components": {
        "schemas": {
            "Task": {
                "type": "object",
                "required": ["title"],
                "properties": {"title": {"type": "string", "description": "Title"}},
            }
        }
    },
}


def test_resolve_refs_inlines_and_guards_cycles() -> None:
    root = {"components": {"schemas": {"A": {"$ref": "#/components/schemas/A"}}}}
    # Self-cycle must not recurse forever.
    assert mod.resolve_refs({"$ref": "#/components/schemas/A"}, root) == {}
    resolved = mod.resolve_refs({"$ref": "#/components/schemas/Task"}, _SPEC)
    assert resolved["properties"]["title"]["type"] == "string"


def test_build_tools_from_spec() -> None:
    tools = mod.build_tools(_SPEC)
    by_name = {t["name"]: t for t in tools}
    assert "getTask" in by_name                      # operationId used
    assert "put_tasks_task_id" in by_name            # slug fallback for missing operationId

    get_tool = by_name["getTask"]
    props = get_tool["input_schema"]["properties"]
    assert props["task_id"]["x-in"] == "path"        # path-level param inherited
    assert "fields" in props                          # operation-level query param
    assert get_tool["input_schema"]["required"] == ["task_id"]


def test_request_body_is_resolved_and_nested() -> None:
    tools = mod.build_tools(_SPEC)
    put_tool = next(t for t in tools if t["name"] == "put_tasks_task_id")
    schema = put_tool["input_schema"]
    assert "body" in schema["properties"]
    # $ref to Task must be inlined.
    assert schema["properties"]["body"]["properties"]["title"]["type"] == "string"
    assert "body" in schema["required"]


def test_format_shapes() -> None:
    tools = mod.build_tools(_SPEC)
    anthropic = mod.to_anthropic_tools(tools)
    mcp = mod.to_mcp_tools(tools)
    assert all("input_schema" in t for t in anthropic)   # snake_case
    assert all("inputSchema" in t for t in mcp["tools"])  # camelCase
    assert mod._server_url(_SPEC) == "https://api.example.com/v1"

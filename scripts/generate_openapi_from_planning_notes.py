#!/usr/bin/env python3
"""Generate split OpenAPI files from API planning notes."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path
from typing import Any

import yaml


METHOD_LINE = re.compile(r"^-\s*`(GET|POST|PUT|PATCH|DELETE)\s+([^`]+)`\s*(?:—|-)?\s*(.*)$")
PROJECT_LINE = re.compile(r"^Project:\s*\*\*(.+?)\*\*\s*$")
BASE_URL_LINE = re.compile(r"^Base URL:\s*`([^`]+)`")
VERSION_LINE = re.compile(r"^API version:\s*\*\*(.+?)\*\*")


def pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def op_id(method: str, path: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9{}_/]", "", path)
    parts = [p for p in clean.strip("/").split("/") if p]
    chunks: list[str] = []
    for part in parts:
        if part.startswith("{") and part.endswith("}"):
            chunks.append("by_" + part[1:-1])
        else:
            chunks.append(part.replace("-", "_"))
    stem = "_".join(chunks) if chunks else "root"
    return f"{method.lower()}_{stem}"


def group_for_path(path: str) -> str:
    if path.startswith("/projects"):
        return "projects"
    if path.startswith("/users"):
        return "users"
    if path.startswith("/tags") or "/tags/" in path:
        return "tags"
    if path.startswith("/comments") or "/comments" in path:
        return "comments"
    return "tasks"


def parse_notes(notes_text: str) -> tuple[str, str, str, list[tuple[str, str, str]]]:
    project_name = "API Project"
    base_url = "http://localhost:4010/v1"
    api_version = "v1"
    ops: list[tuple[str, str, str]] = []

    for raw in notes_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = PROJECT_LINE.match(line)
        if m:
            project_name = m.group(1).strip()
            continue
        m = BASE_URL_LINE.match(line)
        if m:
            base_url = m.group(1).strip()
            continue
        m = VERSION_LINE.match(line)
        if m:
            api_version = m.group(1).strip()
            continue
        m = METHOD_LINE.match(line)
        if m:
            method, path, desc = m.groups()
            ops.append((method.upper(), path.strip(), desc.strip() or f"{method.title()} {path}"))

    dedup = {}
    for method, path, desc in ops:
        dedup[(method, path)] = desc
    normalized = [(m, p, d) for (m, p), d in dedup.items()]
    normalized.sort(key=lambda x: (x[1], x[0]))
    return project_name, base_url, api_version, normalized


def id_param_ref(path: str) -> list[dict[str, str]]:
    mapping = {
        "project_id": "ProjectId",
        "task_id": "TaskId",
        "comment_id": "CommentId",
        "tag_id": "TagId",
        "user_id": "UserId",
    }
    refs: list[dict[str, str]] = []
    for token in re.findall(r"{([^}]+)}", path):
        name = mapping.get(token)
        if name:
            refs.append({"$ref": f"../components/parameters/common.yaml#/{name}"})
    return refs


def response_for(method: str, path: str) -> dict[str, Any]:
    if method == "POST":
        return {
            "201": {
                "description": "Created",
                "content": {
                    "application/json": {
                        "schema": {"type": "object", "additionalProperties": True},
                        "example": {"id": "2f2d41d5-9b6f-4d8b-b0fc-dcfef6d7e24f"},
                    }
                },
            },
            "400": {"$ref": "../components/responses/common.yaml#/Error400"},
            "401": {"$ref": "../components/responses/common.yaml#/Error401"},
            "500": {"$ref": "../components/responses/common.yaml#/Error500"},
        }
    if method == "DELETE":
        return {
            "204": {"description": "No Content"},
            "401": {"$ref": "../components/responses/common.yaml#/Error401"},
            "404": {"$ref": "../components/responses/common.yaml#/Error404"},
            "500": {"$ref": "../components/responses/common.yaml#/Error500"},
        }

    if method == "GET" and path == "/projects":
        return {
            "200": {
                "description": "Projects list",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "../components/schemas/common.yaml#/ProjectsListResponse"},
                        "example": {
                            "data": [
                                {
                                    "id": "8de2f75f-ef78-44e8-ab42-7276f0462df9",
                                    "name": "API-first rollout",
                                    "description": "Planning and execution",
                                    "status": "active",
                                    "owner_id": "1edd3e73-e605-4559-a6f9-dcd27f2f6488",
                                    "created_at": "2026-03-09T10:22:31Z",
                                    "updated_at": "2026-03-09T10:22:31Z",
                                    "archived_at": None,
                                }
                            ],
                            "page": {"next_cursor": None, "has_more": False},
                        },
                    }
                },
            },
            "400": {"$ref": "../components/responses/common.yaml#/Error400"},
            "401": {"$ref": "../components/responses/common.yaml#/Error401"},
            "500": {"$ref": "../components/responses/common.yaml#/Error500"},
        }

    if method == "GET" and path == "/tasks":
        return {
            "200": {
                "description": "Tasks list",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "../components/schemas/common.yaml#/TasksListResponse"},
                        "example": {
                            "data": [
                                {
                                    "id": "70d42a43-e224-4f72-9b95-53beea09b434",
                                    "project_id": "8de2f75f-ef78-44e8-ab42-7276f0462df9",
                                    "title": "Create API-first demo",
                                    "description": "Generate OpenAPI from planning notes",
                                    "status": "in_progress",
                                    "priority": "high",
                                    "assignee_id": "1edd3e73-e605-4559-a6f9-dcd27f2f6488",
                                    "due_date": "2026-03-12",
                                    "created_at": "2026-03-09T10:22:31Z",
                                    "updated_at": "2026-03-09T10:22:31Z",
                                    "completed_at": None,
                                }
                            ],
                            "page": {"next_cursor": None, "has_more": False},
                        },
                    }
                },
            },
            "400": {"$ref": "../components/responses/common.yaml#/Error400"},
            "401": {"$ref": "../components/responses/common.yaml#/Error401"},
            "500": {"$ref": "../components/responses/common.yaml#/Error500"},
        }

    if method == "GET" and path == "/users/me":
        return {
            "200": {
                "description": "Current user",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "../components/schemas/common.yaml#/User"},
                        "example": {
                            "id": "1edd3e73-e605-4559-a6f9-dcd27f2f6488",
                            "email": "alex@taskstream.example.com",
                            "full_name": "Alex Rivera",
                            "role": "admin",
                            "status": "active",
                            "created_at": "2026-01-15T09:00:00Z",
                        },
                    }
                },
            },
            "401": {"$ref": "../components/responses/common.yaml#/Error401"},
            "500": {"$ref": "../components/responses/common.yaml#/Error500"},
        }

    return {
        "200": {
            "description": "Success",
            "content": {
                "application/json": {
                    "schema": {"type": "object", "additionalProperties": True},
                    "example": {"ok": True},
                }
            },
        },
        "400": {"$ref": "../components/responses/common.yaml#/Error400"},
        "401": {"$ref": "../components/responses/common.yaml#/Error401"},
        "404": {"$ref": "../components/responses/common.yaml#/Error404"},
        "500": {"$ref": "../components/responses/common.yaml#/Error500"},
    }


def make_operation(method: str, path: str, desc: str) -> dict[str, Any]:
    tag = path.strip("/").split("/")[0] if path.strip("/") else "root"
    tag = tag.replace("-", " ").title()
    params = [{"$ref": "../components/parameters/common.yaml#/RequestId"}] + id_param_ref(path)
    if method == "GET" and "{" not in path:
        params.extend(
            [
                {"$ref": "../components/parameters/common.yaml#/Limit"},
                {"$ref": "../components/parameters/common.yaml#/Cursor"},
            ]
        )
    if method == "POST" and path in {"/projects", "/tasks"}:
        params.append({"$ref": "../components/parameters/common.yaml#/IdempotencyKey"})

    op: dict[str, Any] = {
        "operationId": op_id(method, path),
        "tags": [tag],
        "summary": desc,
        "description": f"{desc}. Generated from planning notes.",
        "security": [{"BearerAuth": []}],
        "parameters": params,
        "responses": response_for(method, path),
    }
    if method in {"POST", "PATCH", "PUT"}:
        op["requestBody"] = {
            "required": False,
            "content": {
                "application/json": {
                    "schema": {"type": "object", "additionalProperties": True},
                    "example": {"name": "Sample value"},
                }
            },
        }
    return op


def schemas_common() -> dict[str, Any]:
    return {
        "BaseResource": {
            "type": "object",
            "required": ["id", "created_at", "updated_at"],
            "properties": {
                "id": {"type": "string", "format": "uuid", "example": "8de2f75f-ef78-44e8-ab42-7276f0462df9"},
                "created_at": {"type": "string", "format": "date-time", "example": "2026-03-09T10:22:31Z"},
                "updated_at": {"type": "string", "format": "date-time", "example": "2026-03-09T10:22:31Z"},
            },
        },
        "Project": {
            "allOf": [
                {"$ref": "#/BaseResource"},
                {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "example": "API-first rollout"},
                        "description": {"type": "string", "example": "Planning and execution"},
                        "status": {"type": "string", "enum": ["active", "archived"], "example": "active"},
                        "owner_id": {
                            "type": "string",
                            "format": "uuid",
                            "example": "1edd3e73-e605-4559-a6f9-dcd27f2f6488",
                        },
                        "archived_at": {"type": "string", "nullable": True, "format": "date-time", "example": None},
                    },
                },
            ]
        },
        "Task": {
            "allOf": [
                {"$ref": "#/BaseResource"},
                {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "format": "uuid",
                            "example": "8de2f75f-ef78-44e8-ab42-7276f0462df9",
                        },
                        "title": {"type": "string", "example": "Create API-first demo"},
                        "description": {"type": "string", "example": "Generate OpenAPI from planning notes"},
                        "status": {
                            "type": "string",
                            "enum": ["todo", "in_progress", "done", "blocked"],
                            "example": "in_progress",
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "urgent"],
                            "example": "high",
                        },
                        "assignee_id": {
                            "type": "string",
                            "format": "uuid",
                            "example": "1edd3e73-e605-4559-a6f9-dcd27f2f6488",
                        },
                        "due_date": {"type": "string", "format": "date", "example": "2026-03-12"},
                        "completed_at": {"type": "string", "nullable": True, "format": "date-time", "example": None},
                    },
                },
            ]
        },
        "User": {
            "type": "object",
            "required": ["id", "email", "full_name", "role", "status", "created_at"],
            "properties": {
                "id": {"type": "string", "format": "uuid", "example": "1edd3e73-e605-4559-a6f9-dcd27f2f6488"},
                "email": {"type": "string", "format": "email", "example": "alex@taskstream.example.com"},
                "full_name": {"type": "string", "example": "Alex Rivera"},
                "role": {"type": "string", "enum": ["admin", "manager", "member", "guest"], "example": "admin"},
                "status": {
                    "type": "string",
                    "enum": ["active", "invited", "suspended"],
                    "example": "active",
                },
                "created_at": {"type": "string", "format": "date-time", "example": "2026-01-15T09:00:00Z"},
            },
        },
        "CursorPage": {
            "type": "object",
            "required": ["next_cursor", "has_more"],
            "properties": {
                "next_cursor": {"type": "string", "nullable": True, "example": None},
                "has_more": {"type": "boolean", "example": False},
            },
        },
        "ProjectsListResponse": {
            "type": "object",
            "required": ["data", "page"],
            "properties": {
                "data": {"type": "array", "items": {"$ref": "#/Project"}},
                "page": {"$ref": "#/CursorPage"},
            },
        },
        "TasksListResponse": {
            "type": "object",
            "required": ["data", "page"],
            "properties": {
                "data": {"type": "array", "items": {"$ref": "#/Task"}},
                "page": {"$ref": "#/CursorPage"},
            },
        },
        "ErrorEnvelope": {
            "type": "object",
            "required": ["error", "request_id"],
            "properties": {
                "error": {
                    "type": "object",
                    "required": ["code", "message"],
                    "properties": {
                        "code": {"type": "string", "example": "invalid_request"},
                        "message": {"type": "string", "example": "Invalid request"},
                        "details": {"type": "array", "items": {"type": "object"}, "example": []},
                    },
                },
                "request_id": {"type": "string", "example": "req_demo_user_path"},
            },
        },
        "AnyResource": {
            "oneOf": [
                {"$ref": "#/Project"},
                {"$ref": "#/Task"},
                {"$ref": "#/User"},
            ]
        },
    }


def parameters_common() -> dict[str, Any]:
    return {
        "RequestId": {
            "name": "X-Request-Id",
            "in": "header",
            "required": False,
            "schema": {"type": "string", "example": "req_demo_user_path"},
            "description": "Correlation ID for tracing.",
        },
        "IdempotencyKey": {
            "name": "Idempotency-Key",
            "in": "header",
            "required": False,
            "schema": {"type": "string", "example": "7f0f3677-3d01-478f-8d0f-02ca9f07ed50"},
            "description": "Idempotency key for safe retries.",
        },
        "Limit": {
            "name": "limit",
            "in": "query",
            "required": False,
            "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20, "example": 20},
            "description": "Page size.",
        },
        "Cursor": {
            "name": "cursor",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "example": "eyJvZmZzZXQiOjEwfQ=="},
            "description": "Opaque cursor token.",
        },
        "ProjectId": {
            "name": "project_id",
            "in": "path",
            "required": True,
            "schema": {"type": "string", "format": "uuid", "example": "8de2f75f-ef78-44e8-ab42-7276f0462df9"},
            "description": "Project identifier.",
        },
        "TaskId": {
            "name": "task_id",
            "in": "path",
            "required": True,
            "schema": {"type": "string", "format": "uuid", "example": "70d42a43-e224-4f72-9b95-53beea09b434"},
            "description": "Task identifier.",
        },
        "CommentId": {
            "name": "comment_id",
            "in": "path",
            "required": True,
            "schema": {"type": "string", "format": "uuid", "example": "9f0fb1f6-d4b5-4680-a17f-fd63ed63c45a"},
            "description": "Comment identifier.",
        },
        "TagId": {
            "name": "tag_id",
            "in": "path",
            "required": True,
            "schema": {"type": "string", "format": "uuid", "example": "0f5ce260-a1fd-49dc-b795-dc05f4bc4e69"},
            "description": "Tag identifier.",
        },
        "UserId": {
            "name": "user_id",
            "in": "path",
            "required": True,
            "schema": {"type": "string", "format": "uuid", "example": "1edd3e73-e605-4559-a6f9-dcd27f2f6488"},
            "description": "User identifier.",
        },
    }


def responses_common() -> dict[str, Any]:
    return {
        "Error400": {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "schema": {"$ref": "../schemas/common.yaml#/ErrorEnvelope"},
                    "example": {
                        "error": {"code": "invalid_request", "message": "Invalid query parameter", "details": []},
                        "request_id": "req_demo_user_path",
                    },
                }
            },
        },
        "Error401": {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "schema": {"$ref": "../schemas/common.yaml#/ErrorEnvelope"},
                    "example": {
                        "error": {"code": "unauthorized", "message": "Missing or invalid token", "details": []},
                        "request_id": "req_demo_user_path",
                    },
                }
            },
        },
        "Error404": {
            "description": "Not Found",
            "content": {
                "application/json": {
                    "schema": {"$ref": "../schemas/common.yaml#/ErrorEnvelope"},
                    "example": {
                        "error": {"code": "not_found", "message": "Resource not found", "details": []},
                        "request_id": "req_demo_user_path",
                    },
                }
            },
        },
        "Error500": {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "schema": {"$ref": "../schemas/common.yaml#/ErrorEnvelope"},
                    "example": {
                        "error": {"code": "internal_error", "message": "Unexpected error", "details": []},
                        "request_id": "req_demo_user_path",
                    },
                }
            },
        },
    }


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate split OpenAPI from planning notes")
    parser.add_argument("--notes", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--spec-tree", required=True)
    parser.add_argument("--openapi-version", default="3.0.3")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    notes_path = (repo / args.notes).resolve()
    spec_path = (repo / args.spec).resolve()
    spec_tree = (repo / args.spec_tree).resolve()

    notes_text = notes_path.read_text(encoding="utf-8")
    project_name, base_url, api_version, operations = parse_notes(notes_text)

    if spec_path.exists() and spec_path.is_dir():
        shutil.rmtree(spec_path)
    spec_path.parent.mkdir(parents=True, exist_ok=True)

    if spec_tree.exists():
        shutil.rmtree(spec_tree)
    paths_dir = spec_tree / "v1" / "paths"
    components_dir = spec_tree / "v1" / "components"
    tree_slug = spec_tree.name or "taskstream"

    grouped: dict[str, dict[str, dict[str, Any]]] = {"projects": {}, "tasks": {}, "comments": {}, "tags": {}, "users": {}}
    root_paths: dict[str, dict[str, str]] = {}

    for method, path, desc in operations:
        group = group_for_path(path)
        grouped.setdefault(group, {})
        grouped[group].setdefault(path, {})
        grouped[group][path][method.lower()] = make_operation(method, path, desc)
        root_paths[path] = {"$ref": f"./{tree_slug}/v1/paths/{group}.yaml#/{pointer_escape(path)}"}

    root_spec: dict[str, Any] = {
        "openapi": str(args.openapi_version).strip() or "3.0.3",
        "info": {
            "title": f"{project_name} Public API",
            "version": api_version,
            "description": f"API-first contract generated from planning notes for {project_name}.",
        },
        "servers": [{"url": base_url}],
        "security": [{"BearerAuth": []}],
        "paths": root_paths,
        "components": {
            "securitySchemes": {"BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}},
            "parameters": {
                "RequestId": {"$ref": f"./{tree_slug}/v1/components/parameters/common.yaml#/RequestId"},
                "IdempotencyKey": {"$ref": f"./{tree_slug}/v1/components/parameters/common.yaml#/IdempotencyKey"},
                "Limit": {"$ref": f"./{tree_slug}/v1/components/parameters/common.yaml#/Limit"},
                "Cursor": {"$ref": f"./{tree_slug}/v1/components/parameters/common.yaml#/Cursor"},
                "ProjectId": {"$ref": f"./{tree_slug}/v1/components/parameters/common.yaml#/ProjectId"},
                "TaskId": {"$ref": f"./{tree_slug}/v1/components/parameters/common.yaml#/TaskId"},
                "CommentId": {"$ref": f"./{tree_slug}/v1/components/parameters/common.yaml#/CommentId"},
                "TagId": {"$ref": f"./{tree_slug}/v1/components/parameters/common.yaml#/TagId"},
                "UserId": {"$ref": f"./{tree_slug}/v1/components/parameters/common.yaml#/UserId"},
            },
            "responses": {
                "Error400": {"$ref": f"./{tree_slug}/v1/components/responses/common.yaml#/Error400"},
                "Error401": {"$ref": f"./{tree_slug}/v1/components/responses/common.yaml#/Error401"},
                "Error404": {"$ref": f"./{tree_slug}/v1/components/responses/common.yaml#/Error404"},
                "Error500": {"$ref": f"./{tree_slug}/v1/components/responses/common.yaml#/Error500"},
            },
            "schemas": {
                "BaseResource": {"$ref": f"./{tree_slug}/v1/components/schemas/common.yaml#/BaseResource"},
                "Project": {"$ref": f"./{tree_slug}/v1/components/schemas/common.yaml#/Project"},
                "Task": {"$ref": f"./{tree_slug}/v1/components/schemas/common.yaml#/Task"},
                "User": {"$ref": f"./{tree_slug}/v1/components/schemas/common.yaml#/User"},
                "CursorPage": {"$ref": f"./{tree_slug}/v1/components/schemas/common.yaml#/CursorPage"},
                "ProjectsListResponse": {"$ref": f"./{tree_slug}/v1/components/schemas/common.yaml#/ProjectsListResponse"},
                "TasksListResponse": {"$ref": f"./{tree_slug}/v1/components/schemas/common.yaml#/TasksListResponse"},
                "ErrorEnvelope": {"$ref": f"./{tree_slug}/v1/components/schemas/common.yaml#/ErrorEnvelope"},
                "AnyResource": {"$ref": f"./{tree_slug}/v1/components/schemas/common.yaml#/AnyResource"},
            },
        },
    }

    write_yaml(spec_path, root_spec)

    for group, path_items in grouped.items():
        if path_items:
            write_yaml(paths_dir / f"{group}.yaml", path_items)

    write_yaml(components_dir / "schemas" / "common.yaml", schemas_common())
    write_yaml(components_dir / "parameters" / "common.yaml", parameters_common())
    write_yaml(components_dir / "responses" / "common.yaml", responses_common())

    print(f"[ok] generated OpenAPI from notes: {spec_path}")
    print(f"[ok] generated split tree: {spec_tree}")
    print(f"[ok] operations generated: {len(operations)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

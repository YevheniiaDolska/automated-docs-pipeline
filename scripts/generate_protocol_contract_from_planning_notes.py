#!/usr/bin/env python3
"""Generate non-REST protocol contracts from planning notes."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml


def _slug(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_")
    return cleaned.lower() or "api_project"


def _pascal(text: str) -> str:
    parts = re.split(r"[^a-zA-Z0-9]+", text)
    words = [p.capitalize() for p in parts if p]
    return "".join(words) or "ApiProject"


def _extract_keywords(notes: str, words: list[str]) -> list[str]:
    found: list[str] = []
    lowered = notes.lower()
    for word in words:
        if word.lower() in lowered and word not in found:
            found.append(word)
    return found


def _extract_channels(notes: str, limit: int = 8) -> list[str]:
    candidates: list[str] = []
    patterns = [
        r"(?:channel|topic|event)\s*[:\-]\s*([A-Za-z0-9._/\-]+)",
        r"\b([a-z][a-z0-9_-]*\.[a-z0-9_.-]+)\b",
        r"\b([a-z][a-z0-9_-]*/[a-z0-9_/\-]+)\b",
    ]
    for pattern in patterns:
        for match in re.findall(pattern, notes, flags=re.IGNORECASE):
            channel = str(match).strip().strip("`'\"")
            if channel and channel not in candidates:
                candidates.append(channel)
            if len(candidates) >= limit:
                return candidates
    return candidates


def _graphql_contract(notes: str, project_name: str) -> str:
    query_candidates = _extract_keywords(notes, ["health", "status", "project", "task", "user", "list_projects"])
    mutation_candidates = _extract_keywords(notes, ["create_project", "update_project", "create_task", "publish_event"])
    subscription_candidates = _extract_keywords(notes, ["project_updated", "task_completed", "events_stream"])

    queries = query_candidates or ["health", "project"]
    mutations = mutation_candidates or ["create_project", "update_project"]
    subscriptions = subscription_candidates or ["project_updated", "task_completed"]

    def _line(name: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9_]+", "_", name).strip("_").lower()
        return f"  {normalized}(id: ID): String!"

    query_block = "\n".join(_line(name) for name in queries[:8])
    mutation_block = "\n".join(_line(name) for name in mutations[:8])
    subscription_block = "\n".join(_line(name) for name in subscriptions[:8])
    return (
        f"# Generated from planning notes for {project_name}\n"
        "schema {\n"
        "  query: Query\n"
        "  mutation: Mutation\n"
        "  subscription: Subscription\n"
        "}\n\n"
        "type Query {\n"
        f"{query_block}\n"
        "}\n\n"
        "type Mutation {\n"
        f"{mutation_block}\n"
        "}\n\n"
        "type Subscription {\n"
        f"{subscription_block}\n"
        "}\n"
    )


def _grpc_contract(notes: str, project_name: str) -> str:
    package = _slug(project_name)
    service = f"{_pascal(project_name)}Service"
    method_candidates = _extract_keywords(
        notes,
        [
            "GetProject",
            "ListProjects",
            "CreateProject",
            "UpdateProject",
            "DeleteProject",
            "CreateTask",
            "ListTasks",
        ],
    )
    methods = method_candidates or ["GetProject", "ListProjects", "CreateProject", "UpdateProject"]

    rpc_lines = []
    message_lines = []
    for method in methods[:10]:
        clean = re.sub(r"[^A-Za-z0-9]+", "", method) or "Operation"
        req = f"{clean}Request"
        resp = f"{clean}Response"
        rpc_lines.append(f"  rpc {clean} ({req}) returns ({resp});")
        message_lines.append(f"message {req} {{ string id = 1; string trace_id = 2; }}")
        message_lines.append(f"message {resp} {{ string status = 1; string result_id = 2; }}")

    return (
        'syntax = "proto3";\n\n'
        f"package {package}.v1;\n\n"
        f"service {service} {{\n"
        + "\n".join(rpc_lines)
        + "\n}\n\n"
        + "\n\n".join(message_lines)
        + "\n"
    )


def _asyncapi_contract(notes: str, project_name: str) -> str:
    channels = _extract_channels(notes) or ["project.updated", "task.completed"]
    payload = {
        "asyncapi": "2.6.0",
        "info": {
            "title": f"{project_name} Async Events",
            "version": "1.0.0",
            "description": f"Generated from planning notes for {project_name}.",
        },
        "channels": {},
    }
    for channel in channels[:10]:
        payload["channels"][channel] = {
            "publish": {
                "message": {
                    "name": f"{_slug(channel)}_event",
                    "payload": {
                        "type": "object",
                        "properties": {
                            "event_id": {"type": "string"},
                            "event_type": {"type": "string", "example": channel},
                            "occurred_at": {"type": "string", "format": "date-time"},
                            "data": {"type": "object"},
                        },
                        "required": ["event_id", "event_type", "occurred_at"],
                    },
                }
            },
            "subscribe": {
                "message": {
                    "name": f"{_slug(channel)}_subscription",
                    "payload": {
                        "type": "object",
                        "properties": {"ack": {"type": "boolean"}, "event_id": {"type": "string"}},
                    },
                }
            },
        }
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)


def _websocket_contract(notes: str, project_name: str) -> str:
    channels = _extract_channels(notes) or ["project.updated", "task.completed"]
    payload = {
        "info": {
            "title": f"{project_name} WebSocket API",
            "version": "1.0.0",
            "description": f"Generated from planning notes for {project_name}.",
        },
        "channels": {},
    }
    for channel in channels[:10]:
        payload["channels"][channel] = {
            "description": f"Real-time stream for {channel}",
            "publish": {
                "message": {
                    "name": f"{_slug(channel)}_publish",
                    "payload": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "example": "publish"},
                            "channel": {"type": "string", "example": channel},
                            "data": {"type": "object"},
                        },
                    },
                }
            },
            "subscribe": {
                "message": {
                    "name": f"{_slug(channel)}_subscribe",
                    "payload": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "example": "subscribe"},
                            "channel": {"type": "string", "example": channel},
                        },
                    },
                }
            },
            "payload": {
                "type": "object",
                "properties": {
                    "event_type": {"type": "string", "example": channel},
                    "payload": {"type": "object"},
                },
            },
        }
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate protocol contract from planning notes")
    parser.add_argument("--protocol", required=True, choices=["graphql", "grpc", "asyncapi", "websocket"])
    parser.add_argument("--notes", required=True, help="Path to planning notes markdown")
    parser.add_argument("--output", required=True, help="Output contract path (or grpc directory)")
    parser.add_argument("--project-name", default="API Project")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    notes_path = Path(args.notes).resolve()
    if not notes_path.exists():
        raise FileNotFoundError(f"Planning notes not found: {notes_path}")
    notes = notes_path.read_text(encoding="utf-8")

    out = Path(args.output)
    if not out.is_absolute():
        out = (Path.cwd() / out).resolve()

    if args.protocol == "grpc" and (out.suffix == "" or out.is_dir()):
        out.mkdir(parents=True, exist_ok=True)
        out = out / f"{_slug(args.project_name)}.proto"

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and not args.force:
        print(f"[protocol-notes] skip existing contract: {out}")
        return 0

    if args.protocol == "graphql":
        rendered = _graphql_contract(notes, args.project_name)
    elif args.protocol == "grpc":
        rendered = _grpc_contract(notes, args.project_name)
    elif args.protocol == "asyncapi":
        rendered = _asyncapi_contract(notes, args.project_name)
    else:
        rendered = _websocket_contract(notes, args.project_name)

    out.write_text(rendered, encoding="utf-8")
    print(f"[protocol-notes] generated {args.protocol} contract: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

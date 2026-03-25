#!/usr/bin/env python3
"""Shared API protocol helpers for docs-ops pipeline."""

from __future__ import annotations

from typing import Any

SUPPORTED_API_PROTOCOLS: tuple[str, ...] = (
    "rest",
    "graphql",
    "grpc",
    "asyncapi",
    "websocket",
)

ECHO_WS_PRIMARY = "wss://echo.websocket.events"
ECHO_WS_FALLBACK = "wss://socketsbay.com/wss/v2/1/demo/"
ECHO_WS_LEGACY = "wss://echo.websocket.org"
ECHO_HTTP_POST = "https://postman-echo.com/post"


def _clean_protocol(value: str) -> str:
    normalized = value.strip().lower()
    aliases = {
        "openapi": "rest",
        "graph-ql": "graphql",
        "graph_ql": "graphql",
        "gql": "graphql",
        "grpc/proto": "grpc",
        "proto": "grpc",
        "events": "asyncapi",
        "event-driven": "asyncapi",
        "event_driven": "asyncapi",
        "ws": "websocket",
        "web-socket": "websocket",
        "web_socket": "websocket",
    }
    return aliases.get(normalized, normalized)


def default_asyncapi_ws_endpoint() -> str:
    return ECHO_WS_PRIMARY


def default_websocket_endpoint() -> str:
    return ECHO_WS_PRIMARY


def default_graphql_endpoint() -> str:
    return ECHO_HTTP_POST


def default_grpc_gateway_endpoint() -> str:
    return ECHO_HTTP_POST


def default_asyncapi_http_publish_endpoint() -> str:
    return ECHO_HTTP_POST


def default_websocket_http_bridge_endpoint() -> str:
    return ECHO_HTTP_POST


def normalize_protocols(raw: Any, default: list[str] | None = None) -> list[str]:
    """Normalize runtime/list input to unique supported protocol names."""
    if default is None:
        default = ["rest"]

    candidates: list[str] = []
    if isinstance(raw, str):
        candidates = [item for item in (v.strip() for v in raw.split(",")) if item]
    elif isinstance(raw, list):
        candidates = [str(item).strip() for item in raw if str(item).strip()]

    if not candidates:
        candidates = list(default)

    seen: set[str] = set()
    normalized: list[str] = []
    for item in candidates:
        protocol = _clean_protocol(item)
        if protocol not in SUPPORTED_API_PROTOCOLS:
            continue
        if protocol in seen:
            continue
        seen.add(protocol)
        normalized.append(protocol)

    return normalized if normalized else list(default)


def default_api_protocol_settings() -> dict[str, dict[str, Any]]:
    """Default protocol-specific settings for runtime configs."""
    return {
        "rest": {
            "enabled": True,
            "mode": "api-first",
            "spec_path": "api/openapi.yaml",
            "spec_tree_path": "api/project",
            "generate_server_stubs": True,
            "stubs_output": "generated/api-stubs/fastapi/app/main.py",
            "autofix_cycle_enabled": True,
            "autofix_max_attempts": 3,
            "generate_test_assets": True,
            "upload_test_assets": False,
        },
        "graphql": {
            "enabled": False,
            "mode": "api-first",
            "schema_path": "api/schema.graphql",
            "notes_path": "notes/graphql-api-planning.md",
            "generate_from_notes": True,
            "code_first_schema_export_cmd": "",
            "graphql_endpoint": default_graphql_endpoint(),
            "generate_server_stubs": True,
            "stubs_output": "generated/api-stubs/graphql/handlers.py",
            "autofix_cycle_enabled": True,
            "autofix_max_attempts": 3,
            "semantic_autofix_max_attempts": 3,
            "self_verify_runtime": True,
            "self_verify_require_endpoint": True,
            "publish_requires_live_green": True,
            "generate_test_assets": True,
            "upload_test_assets": False,
        },
        "grpc": {
            "enabled": False,
            "mode": "api-first",
            "proto_paths": ["api/proto"],
            "notes_path": "notes/grpc-api-planning.md",
            "generate_from_notes": True,
            "code_first_proto_export_cmd": "",
            "grpc_gateway_endpoint": default_grpc_gateway_endpoint(),
            "generate_server_stubs": True,
            "stubs_output": "generated/api-stubs/grpc/handlers.py",
            "autofix_cycle_enabled": True,
            "autofix_max_attempts": 3,
            "semantic_autofix_max_attempts": 3,
            "self_verify_runtime": True,
            "self_verify_require_endpoint": True,
            "publish_requires_live_green": True,
            "generate_test_assets": True,
            "upload_test_assets": False,
        },
        "asyncapi": {
            "enabled": False,
            "mode": "api-first",
            "spec_path": "api/asyncapi.yaml",
            "notes_path": "notes/asyncapi-planning.md",
            "generate_from_notes": True,
            "code_first_contract_export_cmd": "",
            "asyncapi_ws_endpoint": default_asyncapi_ws_endpoint(),
            "asyncapi_http_publish_endpoint": default_asyncapi_http_publish_endpoint(),
            "generate_server_stubs": True,
            "stubs_output": "generated/api-stubs/asyncapi/handlers.py",
            "autofix_cycle_enabled": True,
            "autofix_max_attempts": 3,
            "semantic_autofix_max_attempts": 3,
            "self_verify_runtime": True,
            "self_verify_require_endpoint": True,
            "publish_requires_live_green": True,
            "generate_test_assets": True,
            "upload_test_assets": False,
        },
        "websocket": {
            "enabled": False,
            "mode": "api-first",
            "contract_path": "api/websocket.yaml",
            "notes_path": "notes/websocket-api-planning.md",
            "generate_from_notes": True,
            "code_first_contract_export_cmd": "",
            "websocket_endpoint": default_websocket_endpoint(),
            "websocket_http_bridge_endpoint": default_websocket_http_bridge_endpoint(),
            "generate_server_stubs": True,
            "stubs_output": "generated/api-stubs/websocket/handlers.py",
            "autofix_cycle_enabled": True,
            "autofix_max_attempts": 3,
            "semantic_autofix_max_attempts": 3,
            "self_verify_runtime": True,
            "self_verify_require_endpoint": True,
            "publish_requires_live_green": True,
            "generate_test_assets": True,
            "upload_test_assets": False,
        },
    }


def merge_protocol_settings(
    current: Any,
    protocols: list[str],
) -> dict[str, dict[str, Any]]:
    """Merge user/runtime protocol settings into defaults with enabled flags."""
    defaults = default_api_protocol_settings()
    merged: dict[str, dict[str, Any]] = {k: dict(v) for k, v in defaults.items()}

    if isinstance(current, dict):
        for key, value in current.items():
            normalized = _clean_protocol(str(key))
            if normalized not in merged or not isinstance(value, dict):
                continue
            merged[normalized].update(value)

    active = set(protocols)
    for protocol in SUPPORTED_API_PROTOCOLS:
        merged[protocol]["enabled"] = protocol in active
    return merged


def apply_realtime_sandbox_defaults(settings_map: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Ensure AsyncAPI/WebSocket testers have working echo endpoints by default."""
    gql_cfg = settings_map.get("graphql")
    if isinstance(gql_cfg, dict):
        endpoint = str(gql_cfg.get("graphql_endpoint", "")).strip()
        if not endpoint:
            gql_cfg["graphql_endpoint"] = default_graphql_endpoint()
    grpc_cfg = settings_map.get("grpc")
    if isinstance(grpc_cfg, dict):
        endpoint = str(grpc_cfg.get("grpc_gateway_endpoint", "")).strip()
        if not endpoint:
            grpc_cfg["grpc_gateway_endpoint"] = default_grpc_gateway_endpoint()
    async_cfg = settings_map.get("asyncapi")
    if isinstance(async_cfg, dict):
        ws = str(async_cfg.get("asyncapi_ws_endpoint", "")).strip()
        if not ws:
            async_cfg["asyncapi_ws_endpoint"] = default_asyncapi_ws_endpoint()
        publish_endpoint = str(async_cfg.get("asyncapi_http_publish_endpoint", "")).strip()
        if not publish_endpoint:
            async_cfg["asyncapi_http_publish_endpoint"] = default_asyncapi_http_publish_endpoint()
    ws_cfg = settings_map.get("websocket")
    if isinstance(ws_cfg, dict):
        ws = str(ws_cfg.get("websocket_endpoint", "")).strip()
        if not ws:
            ws_cfg["websocket_endpoint"] = default_websocket_endpoint()
        bridge_endpoint = str(ws_cfg.get("websocket_http_bridge_endpoint", "")).strip()
        if not bridge_endpoint:
            ws_cfg["websocket_http_bridge_endpoint"] = default_websocket_http_bridge_endpoint()
    return settings_map

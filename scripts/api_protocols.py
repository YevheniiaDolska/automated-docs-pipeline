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
            "generate_test_assets": True,
            "upload_test_assets": False,
        },
        "graphql": {
            "enabled": False,
            "mode": "api-first",
            "schema_path": "api/schema.graphql",
            "code_first_schema_export_cmd": "",
            "graphql_endpoint": "",
            "self_verify_runtime": True,
            "self_verify_require_endpoint": False,
            "generate_test_assets": True,
            "upload_test_assets": False,
        },
        "grpc": {
            "enabled": False,
            "mode": "api-first",
            "proto_paths": ["api/proto"],
            "code_first_proto_export_cmd": "",
            "grpc_gateway_endpoint": "",
            "self_verify_runtime": True,
            "self_verify_require_endpoint": False,
            "generate_test_assets": True,
            "upload_test_assets": False,
        },
        "asyncapi": {
            "enabled": False,
            "mode": "api-first",
            "spec_path": "api/asyncapi.yaml",
            "code_first_contract_export_cmd": "",
            "asyncapi_ws_endpoint": default_asyncapi_ws_endpoint(),
            "asyncapi_http_publish_endpoint": "",
            "self_verify_runtime": True,
            "self_verify_require_endpoint": False,
            "generate_test_assets": True,
            "upload_test_assets": False,
        },
        "websocket": {
            "enabled": False,
            "mode": "api-first",
            "contract_path": "api/websocket.yaml",
            "code_first_contract_export_cmd": "",
            "websocket_endpoint": default_websocket_endpoint(),
            "self_verify_runtime": True,
            "self_verify_require_endpoint": False,
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
    async_cfg = settings_map.get("asyncapi")
    if isinstance(async_cfg, dict):
        ws = str(async_cfg.get("asyncapi_ws_endpoint", "")).strip()
        if not ws:
            async_cfg["asyncapi_ws_endpoint"] = default_asyncapi_ws_endpoint()
    ws_cfg = settings_map.get("websocket")
    if isinstance(ws_cfg, dict):
        ws = str(ws_cfg.get("websocket_endpoint", "")).strip()
        if not ws:
            ws_cfg["websocket_endpoint"] = default_websocket_endpoint()
    return settings_map

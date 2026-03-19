from __future__ import annotations

from scripts.api_protocols import (
    apply_realtime_sandbox_defaults,
    default_api_protocol_settings,
    merge_protocol_settings,
)


def test_default_protocol_settings_include_echo_endpoints() -> None:
    defaults = default_api_protocol_settings()
    assert str(defaults["asyncapi"]["asyncapi_ws_endpoint"]).startswith("wss://")
    assert str(defaults["websocket"]["websocket_endpoint"]).startswith("wss://")
    assert str(defaults["graphql"]["graphql_endpoint"]).startswith("https://")
    assert str(defaults["grpc"]["grpc_gateway_endpoint"]).startswith("https://")
    assert str(defaults["asyncapi"]["asyncapi_http_publish_endpoint"]).startswith("https://")
    assert str(defaults["websocket"]["websocket_http_bridge_endpoint"]).startswith("https://")
    assert defaults["graphql"]["self_verify_require_endpoint"] is True
    assert defaults["grpc"]["self_verify_require_endpoint"] is True
    assert defaults["asyncapi"]["self_verify_require_endpoint"] is True
    assert defaults["websocket"]["self_verify_require_endpoint"] is True
    assert defaults["graphql"]["publish_requires_live_green"] is True
    assert defaults["grpc"]["publish_requires_live_green"] is True
    assert defaults["asyncapi"]["publish_requires_live_green"] is True
    assert defaults["websocket"]["publish_requires_live_green"] is True


def test_apply_realtime_defaults_fills_empty_endpoints() -> None:
    settings = merge_protocol_settings(
        {
            "graphql": {"graphql_endpoint": ""},
            "grpc": {"grpc_gateway_endpoint": ""},
            "asyncapi": {"asyncapi_ws_endpoint": "", "asyncapi_http_publish_endpoint": ""},
            "websocket": {"websocket_endpoint": "", "websocket_http_bridge_endpoint": ""},
        },
        ["graphql", "grpc", "asyncapi", "websocket"],
    )
    hydrated = apply_realtime_sandbox_defaults(settings)
    assert hydrated["graphql"]["graphql_endpoint"]
    assert hydrated["grpc"]["grpc_gateway_endpoint"]
    assert hydrated["asyncapi"]["asyncapi_ws_endpoint"]
    assert hydrated["asyncapi"]["asyncapi_http_publish_endpoint"]
    assert hydrated["websocket"]["websocket_endpoint"]
    assert hydrated["websocket"]["websocket_http_bridge_endpoint"]

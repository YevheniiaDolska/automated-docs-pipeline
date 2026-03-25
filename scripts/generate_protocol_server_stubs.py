#!/usr/bin/env python3
"""Generate API-first server handlers from protocol contracts."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _slug(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower() or "operation"


def _extract_graphql_fields(schema: str, type_name: str) -> list[str]:
    pattern = rf"type\s+{type_name}\s*\{{(.*?)\}}"
    match = re.search(pattern, schema, flags=re.DOTALL)
    if not match:
        return []
    body = match.group(1)
    names = re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:\(|:)", body, flags=re.MULTILINE)
    unique: list[str] = []
    seen: set[str] = set()
    for name in names:
        if name not in seen:
            seen.add(name)
            unique.append(name)
    return unique


def _collect_proto_files(source: Path) -> list[Path]:
    if source.is_file() and source.suffix.lower() == ".proto":
        return [source]
    if source.is_dir():
        return sorted(path for path in source.rglob("*.proto") if path.is_file())
    return []


def _extract_proto_rpcs(proto_text: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for service_name, body in re.findall(r"\bservice\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{(.*?)\}", proto_text, flags=re.DOTALL):
        for method in re.findall(r"\brpc\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", body):
            pairs.append((service_name, method))
    return pairs


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _rest_stub(spec_path: Path, output: Path) -> None:
    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parent / "generate_fastapi_stubs_from_openapi.py"),
        "--spec",
        str(spec_path),
        "--output",
        str(output),
    ]
    completed = subprocess.run(cmd, check=False)
    if completed.returncode != 0:
        raise RuntimeError("REST stub generation failed")


def _graphql_stub(source: Path, output: Path) -> None:
    schema = source.read_text(encoding="utf-8")
    query_fields = _extract_graphql_fields(schema, "Query")
    mutation_fields = _extract_graphql_fields(schema, "Mutation")
    subscription_fields = _extract_graphql_fields(schema, "Subscription")

    lines: list[str] = [
        '"""GraphQL resolver handlers generated from schema-first contract."""',
        "",
        "from __future__ import annotations",
        "",
        "from datetime import datetime, timezone",
        "from typing import Any",
        "",
        "",
        "def _resolve_context(info: Any) -> dict[str, Any]:",
        "    context = getattr(info, 'context', None)",
        "    return context if isinstance(context, dict) else {}",
        "",
        "",
        "def _response(resolver_id: str, args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:",
        "    return {",
        "        'status': 'ok',",
        "        'resolver': resolver_id,",
        "        'data': {'args': args},",
        "        'meta': {",
        "            'request_id': context.get('request_id'),",
        "            'generated_at': datetime.now(timezone.utc).isoformat(),",
        "        },",
        "    }",
        "",
    ]

    def add_resolvers(root_name: str, fields: list[str]) -> None:
        if not fields:
            return
        lines.append(f"{root_name.lower()}_resolvers: dict[str, Any] = {{")
        for field in fields:
            fn = f"{root_name.lower()}_{_slug(field)}"
            lines.append(f"    {field!r}: lambda obj, info, **kwargs: {fn}(obj=obj, info=info, **kwargs),")
        lines.append("}")
        lines.append("")
        for field in fields:
            fn = f"{root_name.lower()}_{_slug(field)}"
            resolver_id = f"{root_name}.{field}"
            lines.extend(
                [
                    f"def {fn}(*, obj: Any, info: Any, **kwargs: Any) -> dict[str, Any]:",
                    "    context = _resolve_context(info)",
                    f"    return _response({resolver_id!r}, kwargs, context)",
                    "",
                ]
            )

    add_resolvers("Query", query_fields)
    add_resolvers("Mutation", mutation_fields)
    add_resolvers("Subscription", subscription_fields)

    if not query_fields and not mutation_fields and not subscription_fields:
        lines.extend(
            [
                "query_resolvers: dict[str, Any] = {}",
                "",
            ]
        )

    _write(output, "\n".join(lines).rstrip() + "\n")


def _grpc_stub(source: Path, output: Path) -> None:
    proto_files = _collect_proto_files(source)
    if not proto_files:
        raise FileNotFoundError(f"No .proto files found in {source}")

    lines: list[str] = [
        '"""gRPC service handlers generated from proto contracts."""',
        "",
        "from __future__ import annotations",
        "",
        "from datetime import datetime, timezone",
        "from typing import Any",
        "",
        "",
        "def _response(method_id: str, request: Any) -> dict[str, Any]:",
        "    payload = request if isinstance(request, dict) else {'repr': repr(request)}",
        "    return {",
        "        'status': 'ok',",
        "        'method': method_id,",
        "        'data': payload,",
        "        'meta': {'generated_at': datetime.now(timezone.utc).isoformat()},",
        "    }",
        "",
    ]

    declared_services: set[str] = set()
    for proto in proto_files:
        content = proto.read_text(encoding="utf-8")
        pairs = _extract_proto_rpcs(content)
        for service_name, method_name in pairs:
            class_name = f"{service_name}Servicer"
            if class_name not in declared_services:
                declared_services.add(class_name)
                lines.extend(
                    [
                        f"class {class_name}:",
                        f"    \"\"\"Generated service handler for {service_name}.\"\"\"",
                        "",
                    ]
                )
            lines.extend(
                [
                    f"    def {method_name}(self, request: Any, context: Any) -> dict[str, Any]:",
                    f"        return _response('{service_name}.{method_name}', request)",
                    "",
                ]
            )

    _write(output, "\n".join(lines).rstrip() + "\n")


def _asyncapi_stub(source: Path, output: Path) -> None:
    spec = _load_yaml(source)
    channels = spec.get("channels", {})
    lines: list[str] = [
        '"""AsyncAPI handlers generated from event contract."""',
        "",
        "from __future__ import annotations",
        "",
        "from datetime import datetime, timezone",
        "from typing import Any",
        "",
        "",
        "def _response(handler_id: str, message: dict[str, Any]) -> dict[str, Any]:",
        "    return {",
        "        'status': 'ok',",
        "        'handler': handler_id,",
        "        'data': message,",
        "        'meta': {'generated_at': datetime.now(timezone.utc).isoformat()},",
        "    }",
        "",
        "publish_handlers: dict[str, Any] = {}",
        "subscribe_handlers: dict[str, Any] = {}",
        "",
    ]

    if isinstance(channels, dict):
        for channel, channel_def in channels.items():
            key = _slug(str(channel))
            if isinstance(channel_def, dict) and "publish" in channel_def:
                fn = f"publish_{key}"
                lines.extend(
                    [
                        f"def {fn}(message: dict[str, Any]) -> dict[str, Any]:",
                        f"    return _response('publish:{channel}', message)",
                        "",
                        f"publish_handlers[{channel!r}] = {fn}",
                        "",
                    ]
                )
            if isinstance(channel_def, dict) and "subscribe" in channel_def:
                fn = f"subscribe_{key}"
                lines.extend(
                    [
                        f"def {fn}(message: dict[str, Any]) -> dict[str, Any]:",
                        f"    return _response('subscribe:{channel}', message)",
                        "",
                        f"subscribe_handlers[{channel!r}] = {fn}",
                        "",
                    ]
                )

    _write(output, "\n".join(lines).rstrip() + "\n")


def _websocket_stub(source: Path, output: Path) -> None:
    contract = _load_yaml(source)
    channels = contract.get("channels", {})
    lines: list[str] = [
        '"""WebSocket route handlers generated from channel contract."""',
        "",
        "from __future__ import annotations",
        "",
        "from datetime import datetime, timezone",
        "from typing import Any",
        "",
        "",
        "def _response(route_id: str, payload: dict[str, Any]) -> dict[str, Any]:",
        "    return {",
        "        'status': 'ok',",
        "        'route': route_id,",
        "        'data': payload,",
        "        'meta': {'generated_at': datetime.now(timezone.utc).isoformat()},",
        "    }",
        "",
        "ws_routes: dict[str, Any] = {}",
        "",
    ]

    if isinstance(channels, dict):
        for channel in channels:
            key = _slug(str(channel))
            fn = f"route_{key}"
            lines.extend(
                [
                    f"def {fn}(payload: dict[str, Any]) -> dict[str, Any]:",
                    f"    return _response({str(channel)!r}, payload)",
                    "",
                    f"ws_routes[{str(channel)!r}] = {fn}",
                    "",
                ]
            )

    _write(output, "\n".join(lines).rstrip() + "\n")


def _default_output(protocol: str) -> Path:
    if protocol == "rest":
        return Path("generated/api-stubs/fastapi/app/main.py")
    return Path(f"generated/api-stubs/{protocol}/handlers.py")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate server handlers for API protocols")
    parser.add_argument("--protocol", required=True, choices=["rest", "graphql", "grpc", "asyncapi", "websocket"])
    parser.add_argument("--source", required=True, help="Contract source path")
    parser.add_argument("--output", default="", help="Generated handler output path")
    args = parser.parse_args()

    protocol = args.protocol.strip().lower()
    source = Path(args.source)
    output = Path(args.output) if args.output else _default_output(protocol)

    if protocol == "rest":
        _rest_stub(source, output)
    elif protocol == "graphql":
        _graphql_stub(source, output)
    elif protocol == "grpc":
        _grpc_stub(source, output)
    elif protocol == "asyncapi":
        _asyncapi_stub(source, output)
    elif protocol == "websocket":
        _websocket_stub(source, output)

    print(f"[protocol-stubs] generated {args.protocol} handlers: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

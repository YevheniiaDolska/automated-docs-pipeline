#!/usr/bin/env python3
"""Generate an agent-ready tool manifest from an OpenAPI contract.

Turns each API operation into a normalized tool definition so the API/SDK is
usable by AI agents. Emits two formats from one source:

- ``tools.json``     -- Anthropic/OpenAI tool style: {name, description, input_schema}
- ``mcp-tools.json`` -- MCP tool style: {tools: [{name, description, inputSchema}]}

Path/query/header parameters become top-level input properties; a JSON request
body becomes a nested ``body`` property. Internal ``$ref`` pointers are resolved.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

_HTTP_METHODS = ("get", "post", "put", "patch", "delete", "options", "head")


def load_spec(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a valid OpenAPI document")
    return data


def _resolve_pointer(root: dict[str, Any], ref: str) -> Any:
    """Resolve a local '#/a/b' JSON pointer within the root document."""
    if not ref.startswith("#/"):
        return None
    node: Any = root
    for token in ref[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict) and token in node:
            node = node[token]
        else:
            return None
    return node


def resolve_refs(node: Any, root: dict[str, Any], seen: frozenset[str] = frozenset()) -> Any:
    """Recursively inline internal $ref pointers, guarding against cycles."""
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/"):
            if ref in seen:
                return {}  # cycle: stop expanding
            target = _resolve_pointer(root, ref)
            if target is None:
                return {}
            return resolve_refs(copy.deepcopy(target), root, seen | {ref})
        return {k: resolve_refs(v, root, seen) for k, v in node.items() if k != "$ref"}
    if isinstance(node, list):
        return [resolve_refs(item, root, seen) for item in node]
    return node


def _slug(method: str, path: str) -> str:
    cleaned = "".join(c if c.isalnum() else "_" for c in path)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return f"{method}_{cleaned}" if cleaned else method


def _operation_description(op: dict[str, Any], method: str, path: str) -> str:
    summary = str(op.get("summary", "")).strip()
    description = str(op.get("description", "")).strip()
    head = summary or description or f"{method.upper()} {path}"
    parts = [head]
    if description and description != head:
        parts.append(description)
    parts.append(f"HTTP {method.upper()} {path}")
    return "\n\n".join(parts)


def _build_input_schema(op: dict[str, Any], path_level_params: list[Any], root: dict[str, Any]) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    required: list[str] = []

    params = list(path_level_params) + list(op.get("parameters", []) or [])
    for raw in params:
        param = resolve_refs(raw, root)
        if not isinstance(param, dict) or not param.get("name"):
            continue
        name = str(param["name"])
        schema = param.get("schema", {}) if isinstance(param.get("schema"), dict) else {}
        prop = dict(schema) if schema else {"type": "string"}
        desc = param.get("description")
        if desc and "description" not in prop:
            prop["description"] = str(desc)
        prop.setdefault("x-in", param.get("in", "query"))
        properties[name] = prop
        if bool(param.get("required")):
            required.append(name)

    body = resolve_refs(op.get("requestBody", {}), root)
    if isinstance(body, dict) and body:
        content = body.get("content", {}) if isinstance(body.get("content"), dict) else {}
        json_ct = content.get("application/json", {})
        body_schema = json_ct.get("schema") if isinstance(json_ct, dict) else None
        if isinstance(body_schema, dict) and body_schema:
            properties["body"] = body_schema
            if bool(body.get("required")):
                required.append("body")

    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def build_tools(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Return normalized tool definitions for every operation in the spec."""
    tools: list[dict[str, Any]] = []
    paths = spec.get("paths", {}) if isinstance(spec.get("paths"), dict) else {}
    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        path_params = item.get("parameters", []) or []
        for method in _HTTP_METHODS:
            op = item.get(method)
            if not isinstance(op, dict):
                continue
            name = str(op.get("operationId", "")).strip() or _slug(method, path)
            tools.append(
                {
                    "name": name,
                    "description": _operation_description(op, method, path),
                    "input_schema": _build_input_schema(op, path_params, spec),
                    "_method": method.upper(),
                    "_path": path,
                }
            )
    return tools


def to_anthropic_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"name": t["name"], "description": t["description"], "input_schema": t["input_schema"]}
        for t in tools
    ]


def to_mcp_tools(tools: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "tools": [
            {"name": t["name"], "description": t["description"], "inputSchema": t["input_schema"]}
            for t in tools
        ]
    }


def _server_url(spec: dict[str, Any]) -> str:
    servers = spec.get("servers", [])
    if isinstance(servers, list) and servers and isinstance(servers[0], dict):
        return str(servers[0].get("url", ""))
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--spec", default="docs/assets/protocols/rest/openapi.yaml", help="OpenAPI document")
    parser.add_argument("--output-dir", default="docs/assets/agent", help="Where manifests are written")
    parser.add_argument("--formats", default="anthropic,mcp", help="Comma list: anthropic,mcp")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"[error] spec not found: {spec_path}")
        return 2
    spec = load_spec(spec_path)
    tools = build_tools(spec)
    if not tools:
        print(f"[warn] no operations found in {spec_path}")
        return 0

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    formats = {f.strip().lower() for f in str(args.formats).split(",") if f.strip()}
    generated_at = datetime.now(timezone.utc).isoformat()
    meta = {
        "generated_at": generated_at,
        "source_spec": str(spec_path),
        "server": _server_url(spec),
        "tool_count": len(tools),
    }

    written: list[str] = []
    if "anthropic" in formats:
        payload = {**meta, "tools": to_anthropic_tools(tools)}
        (out_dir / "tools.json").write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        written.append(str(out_dir / "tools.json"))
    if "mcp" in formats:
        payload = {**meta, **to_mcp_tools(tools)}
        (out_dir / "mcp-tools.json").write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        written.append(str(out_dir / "mcp-tools.json"))

    print(f"[ok] {len(tools)} tools from {spec_path} -> {', '.join(written)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

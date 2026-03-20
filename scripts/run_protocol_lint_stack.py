#!/usr/bin/env python3
"""Run protocol-specific lint stack with 7+ checks per protocol."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml


def _load_data(path: Path) -> Any:
    if path.is_dir():
        return None
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return text


def _collect_proto_files(source: Path) -> list[Path]:
    if source.is_file() and source.suffix.lower() == ".proto":
        return [source]
    if source.is_dir():
        return sorted(p for p in source.rglob("*.proto") if p.is_file())
    return []


def _graphql_checks(source: Path) -> list[tuple[str, bool, str]]:
    schema = source.read_text(encoding="utf-8") if source.exists() else ""
    checks: list[tuple[str, bool, str]] = []
    checks.append(("source_exists", source.exists(), str(source)))
    checks.append(("non_empty", bool(schema.strip()), "schema is not empty"))
    checks.append(("root_declared", ("type Query" in schema or "schema" in schema), "query root or schema block exists"))
    checks.append(("balanced_braces", schema.count("{") == schema.count("}"), "brace balance"))
    checks.append(("balanced_parentheses", schema.count("(") == schema.count(")"), "parentheses balance"))

    type_names = re.findall(r"\b(type|input|interface|enum|union|scalar)\s+([A-Za-z_][A-Za-z0-9_]*)", schema)
    seen: set[str] = set()
    dup_found = False
    for _kind, name in type_names:
        key = name.lower()
        if key in seen:
            dup_found = True
            break
        seen.add(key)
    checks.append(("no_duplicate_types", not dup_found, "duplicate type declarations"))

    dup_fields = False
    for kind, name in re.findall(r"\b(type|input|interface)\s+([A-Za-z_][A-Za-z0-9_]*)", schema):
        block = re.search(rf"\b{kind}\s+{re.escape(name)}[^{{]*\{{(.*?)\}}", schema, re.DOTALL)
        if not block:
            continue
        fields: set[str] = set()
        for line in block.group(1).splitlines():
            raw = line.strip()
            if not raw or raw.startswith("#"):
                continue
            field = raw.split("(", 1)[0].split(":", 1)[0].strip().lower()
            if not re.match(r"^[a-z_][a-z0-9_]*$", field):
                continue
            if field in fields:
                dup_fields = True
                break
            fields.add(field)
        if dup_fields:
            break
    checks.append(("no_duplicate_fields", not dup_fields, "duplicate fields in object/input/interface"))

    schema_block = re.search(r"\bschema\s*\{(.*?)\}", schema, re.DOTALL)
    refs_ok = True
    if schema_block:
        for line in schema_block.group(1).splitlines():
            raw = line.strip()
            if not raw or raw.startswith("#") or ":" not in raw:
                continue
            _root, tname = raw.split(":", 1)
            tname = tname.strip().lower()
            if tname and tname not in seen:
                refs_ok = False
                break
    checks.append(("schema_root_references", refs_ok, "schema block references existing types"))
    return checks


def _grpc_checks(source: Path) -> list[tuple[str, bool, str]]:
    files = _collect_proto_files(source)
    checks: list[tuple[str, bool, str]] = []
    checks.append(("source_exists", source.exists(), str(source)))
    checks.append(("proto_files_found", bool(files), f"files={len(files)}"))

    syntax_ok = True
    braces_ok = True
    service_ok = False
    rpc_ok = False
    dup_rpc = False
    proto3_required = False

    for fp in files:
        text = fp.read_text(encoding="utf-8")
        if not re.search(r'\bsyntax\s*=\s*"(proto2|proto3)"\s*;', text):
            syntax_ok = False
        if text.count("{") != text.count("}"):
            braces_ok = False
        if re.search(r"\bservice\s+[A-Za-z_][A-Za-z0-9_]*\s*\{", text):
            service_ok = True
        if re.search(r"\brpc\s+[A-Za-z_][A-Za-z0-9_]*\s*\(", text):
            rpc_ok = True

        syntax_proto3 = bool(re.search(r'\bsyntax\s*=\s*"proto3"\s*;', text))
        if syntax_proto3 and re.search(r"\brequired\s+[A-Za-z_][A-Za-z0-9_.<>]*\s+[A-Za-z_][A-Za-z0-9_]*\s*=", text):
            proto3_required = True

        for body in re.findall(r"\bservice\s+[A-Za-z_][A-Za-z0-9_]*\s*\{(.*?)\}", text, re.DOTALL):
            seen: set[str] = set()
            for name in re.findall(r"\brpc\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", body):
                key = name.lower()
                if key in seen:
                    dup_rpc = True
                    break
                seen.add(key)
            if dup_rpc:
                break

    checks.append(("syntax_declared", syntax_ok, "valid proto2/proto3 syntax declaration"))
    checks.append(("balanced_braces", braces_ok, "brace balance"))
    checks.append(("service_present", service_ok, "at least one service"))
    checks.append(("rpc_present", rpc_ok, "at least one rpc"))
    checks.append(("no_duplicate_rpc", not dup_rpc, "rpc duplicates inside service"))
    checks.append(("proto3_no_required", not proto3_required, "required not used in proto3"))
    return checks


def _asyncapi_checks(source: Path) -> list[tuple[str, bool, str]]:
    payload = _load_data(source) if source.exists() else {}
    payload = payload if isinstance(payload, dict) else {}
    channels = payload.get("channels", {}) if isinstance(payload.get("channels"), dict) else {}

    checks: list[tuple[str, bool, str]] = []
    checks.append(("source_exists", source.exists(), str(source)))
    checks.append(("top_level_keys", all(k in payload for k in ("asyncapi", "info", "channels")), "asyncapi/info/channels"))
    info = payload.get("info", {}) if isinstance(payload.get("info"), dict) else {}
    checks.append(("info_title", bool(str(info.get("title", "")).strip()), "info.title"))
    checks.append(("info_version", bool(str(info.get("version", "")).strip()), "info.version"))
    checks.append(("channels_non_empty", bool(channels), "channels not empty"))

    op_ok = True
    payload_ok = True
    for _name, cfg in channels.items():
        if not isinstance(cfg, dict):
            op_ok = False
            payload_ok = False
            continue
        has_op = False
        has_payload = False
        for op in ("publish", "subscribe"):
            op_cfg = cfg.get(op)
            if isinstance(op_cfg, dict):
                has_op = True
                msg = op_cfg.get("message")
                if isinstance(msg, dict) and ("payload" in msg or (isinstance(msg.get("oneOf"), list) and any(isinstance(x, dict) and "payload" in x for x in msg.get("oneOf", [])))):
                    has_payload = True
        if not has_op:
            op_ok = False
        if not has_payload:
            payload_ok = False
    checks.append(("operations_present", op_ok, "publish/subscribe present per channel"))
    checks.append(("message_payload_present", payload_ok, "message payload present per operation"))
    checks.append(("version_string", isinstance(payload.get("asyncapi"), str), "asyncapi version is string"))
    return checks


def _websocket_checks(source: Path) -> list[tuple[str, bool, str]]:
    payload = _load_data(source) if source.exists() else {}
    payload = payload if isinstance(payload, dict) else {}
    root_key = ""
    channels: dict[str, Any] = {}
    for key in ("channels", "topics", "events", "messages"):
        candidate = payload.get(key)
        if isinstance(candidate, dict):
            root_key = key
            channels = candidate
            break

    checks: list[tuple[str, bool, str]] = []
    checks.append(("source_exists", source.exists(), str(source)))
    checks.append(("root_channels_present", bool(root_key), "channels/topics/events/messages exists"))
    checks.append(("channels_non_empty", bool(channels), "at least one channel"))

    object_ok = True
    payload_ok = True
    direction_ok = True
    for _name, cfg in channels.items():
        if not isinstance(cfg, dict):
            object_ok = False
            payload_ok = False
            direction_ok = False
            continue
        if not any(k in cfg for k in ("payload", "schema", "message")):
            payload_ok = False
        if not any(k in cfg for k in ("publish", "subscribe", "send", "receive", "emit", "on", "message", "payload", "schema")):
            direction_ok = False
    checks.append(("channel_objects", object_ok, "channel entries are objects"))
    checks.append(("payload_schema_present", payload_ok, "payload/schema/message exists per channel"))
    checks.append(("direction_or_message_present", direction_ok, "directional blocks or message schema"))
    checks.append(("balanced_braces", source.read_text(encoding="utf-8").count("{") == source.read_text(encoding="utf-8").count("}"), "brace balance in raw contract"))
    checks.append(("json_yaml_mapping", isinstance(payload, dict), "contract parsed as mapping"))
    return checks


def _run(protocol: str, source: Path) -> list[tuple[str, bool, str]]:
    if protocol == "graphql":
        return _graphql_checks(source)
    if protocol == "grpc":
        return _grpc_checks(source)
    if protocol == "asyncapi":
        return _asyncapi_checks(source)
    if protocol == "websocket":
        return _websocket_checks(source)
    raise ValueError(f"Unsupported protocol for lint stack: {protocol}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run protocol-specific lint stack")
    parser.add_argument("--protocol", required=True, choices=["graphql", "grpc", "asyncapi", "websocket"])
    parser.add_argument("--source", required=True)
    parser.add_argument("--json-report", default="")
    args = parser.parse_args()

    source = Path(args.source)
    checks = _run(args.protocol, source)
    failed = [name for name, ok, _ in checks if not ok]

    if args.json_report:
        report_path = Path(args.json_report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "protocol": args.protocol,
            "source": str(source),
            "checks": [
                {"name": name, "ok": ok, "detail": detail}
                for name, ok, detail in checks
            ],
            "failed": failed,
            "ok": not bool(failed),
            "checks_total": len(checks),
        }
        report_path.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    for name, ok, detail in checks:
        status = "ok" if ok else "fail"
        print(f"[protocol-lint:{args.protocol}] {status} {name} - {detail}")

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())

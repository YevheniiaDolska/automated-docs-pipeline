#!/usr/bin/env python3
"""Validate gRPC proto contract files with semantic checks."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


PROTO_EXTENSIONS = {".proto"}


def _collect_proto_files(inputs: list[str]) -> list[Path]:
    files: list[Path] = []
    for item in inputs:
        p = Path(item)
        if p.is_dir():
            files.extend(sorted(candidate for candidate in p.rglob("*.proto") if candidate.is_file()))
        elif p.is_file() and p.suffix.lower() in PROTO_EXTENSIONS:
            files.append(p)
    return files


def _validate_proto_text(text: str, path: Path) -> list[str]:
    errors: list[str] = []

    syntax_match = re.search(r'\bsyntax\s*=\s*"(proto2|proto3)"\s*;', text)
    if not syntax_match:
        errors.append(f"{path}: missing or invalid `syntax = \"proto2|proto3\";` declaration")
        syntax = ""
    else:
        syntax = syntax_match.group(1)

    if text.count("{") != text.count("}"):
        errors.append(f"{path}: unbalanced braces")

    if not any(token in text for token in ("service ", "message ", "enum ")):
        errors.append(f"{path}: expected at least one of service/message/enum declarations")

    names: dict[str, str] = {}
    for kind in ("service", "message", "enum"):
        for name in re.findall(rf"\b{kind}\s+([A-Za-z_][A-Za-z0-9_]*)\b", text):
            key = name.lower()
            if key in names:
                errors.append(f"{path}: duplicate declaration `{name}` ({kind})")
            names[key] = kind

    for service_name, body in re.findall(r"\bservice\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{(.*?)\}", text, re.DOTALL):
        rpcs = re.findall(r"\brpc\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s*returns\s*\((.*?)\)\s*;", body)
        if not rpcs:
            errors.append(f"{path}: service `{service_name}` has no valid rpc declarations")
            continue
        seen_rpc: set[str] = set()
        for rpc_name, _in_type, _out_type in rpcs:
            rpc_key = rpc_name.lower()
            if rpc_key in seen_rpc:
                errors.append(f"{path}: service `{service_name}` has duplicate rpc `{rpc_name}`")
            seen_rpc.add(rpc_key)

    if syntax == "proto3" and re.search(r"\brequired\s+[A-Za-z_][A-Za-z0-9_.<>]*\s+[A-Za-z_][A-Za-z0-9_]*\s*=", text):
        errors.append(f"{path}: `required` field label is not allowed in proto3")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate proto contract inputs")
    parser.add_argument("--proto", dest="proto", action="append", required=True, help="Proto file or directory (repeatable)")
    args = parser.parse_args()

    files = _collect_proto_files(args.proto)
    if not files:
        raise FileNotFoundError("No .proto files found from provided --proto inputs")

    errors: list[str] = []
    for proto in files:
        errors.extend(_validate_proto_text(proto.read_text(encoding="utf-8"), proto))

    if errors:
        for err in errors:
            print(f"[grpc-contract] {err}")
        return 1

    print(f"[grpc-contract] ok: {len(files)} proto file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

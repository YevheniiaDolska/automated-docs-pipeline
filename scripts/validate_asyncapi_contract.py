#!/usr/bin/env python3
"""Validate AsyncAPI contract file with semantic checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def _load(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"AsyncAPI file must be a mapping: {path}")
    return data


def _message_has_payload(message: Any) -> bool:
    if not isinstance(message, dict):
        return False
    if "payload" in message:
        return True
    one_of = message.get("oneOf")
    if isinstance(one_of, list):
        return any(isinstance(item, dict) and "payload" in item for item in one_of)
    return False


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = ("asyncapi", "info", "channels")
    for key in required:
        if key not in payload:
            errors.append(f"Missing required key: {key}")

    version = payload.get("asyncapi")
    if version is not None and not isinstance(version, str):
        errors.append("`asyncapi` version must be a string")

    info = payload.get("info")
    if not isinstance(info, dict):
        errors.append("`info` must be an object")
    else:
        if not str(info.get("title", "")).strip():
            errors.append("`info.title` is required")
        if not str(info.get("version", "")).strip():
            errors.append("`info.version` is required")

    channels = payload.get("channels")
    if channels is not None and not isinstance(channels, dict):
        errors.append("`channels` must be an object/mapping")
        channels = {}

    if isinstance(channels, dict):
        if not channels:
            errors.append("`channels` must not be empty")
        for channel_name, channel_cfg in channels.items():
            if not isinstance(channel_cfg, dict):
                errors.append(f"channel `{channel_name}` must be an object")
                continue
            has_op = False
            for op in ("publish", "subscribe"):
                op_cfg = channel_cfg.get(op)
                if op_cfg is None:
                    continue
                has_op = True
                if not isinstance(op_cfg, dict):
                    errors.append(f"channel `{channel_name}` operation `{op}` must be an object")
                    continue
                if not _message_has_payload(op_cfg.get("message")):
                    errors.append(f"channel `{channel_name}` operation `{op}` must define message payload")
            if not has_op:
                errors.append(f"channel `{channel_name}` must define at least one operation: publish/subscribe")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AsyncAPI contract")
    parser.add_argument("spec", help="Path to AsyncAPI yaml/json")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        raise FileNotFoundError(f"AsyncAPI spec not found: {spec_path}")

    errors = validate(_load(spec_path))
    if errors:
        for err in errors:
            print(f"[asyncapi-contract] {err}")
        return 1

    print(f"[asyncapi-contract] ok: {spec_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

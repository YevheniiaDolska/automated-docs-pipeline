#!/usr/bin/env python3
"""Validate WebSocket contract file with semantic checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


CHANNEL_KEYS = ("channels", "topics", "events", "messages")
DIRECTION_KEYS = ("publish", "subscribe", "send", "receive", "emit", "on")


def _load(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"WebSocket contract must be a mapping: {path}")
    return data


def _extract_channels(payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    for key in CHANNEL_KEYS:
        candidate = payload.get(key)
        if isinstance(candidate, dict):
            return key, candidate
    return "", {}


def _entry_has_payload(entry: dict[str, Any]) -> bool:
    if any(key in entry for key in ("payload", "schema", "message")):
        return True
    for key in DIRECTION_KEYS:
        nested = entry.get(key)
        if isinstance(nested, dict) and any(k in nested for k in ("payload", "schema", "message")):
            return True
    return False


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    root_key, channels = _extract_channels(payload)
    if not root_key:
        errors.append("WebSocket contract must define one of: channels/topics/events/messages")
        return errors

    if not channels:
        errors.append(f"`{root_key}` must not be empty")
        return errors

    for channel_name, channel_cfg in channels.items():
        if not isinstance(channel_cfg, dict):
            errors.append(f"channel `{channel_name}` must be an object")
            continue
        if not _entry_has_payload(channel_cfg):
            errors.append(
                f"channel `{channel_name}` must define payload/schema/message directly or in direction blocks"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate WebSocket contract")
    parser.add_argument("contract", help="Path to websocket contract yaml/json")
    args = parser.parse_args()

    contract_path = Path(args.contract)
    if not contract_path.exists():
        raise FileNotFoundError(f"WebSocket contract not found: {contract_path}")

    errors = validate(_load(contract_path))
    if errors:
        for err in errors:
            print(f"[websocket-contract] {err}")
        return 1

    print(f"[websocket-contract] ok: {contract_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

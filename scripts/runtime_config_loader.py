#!/usr/bin/env python3
"""Load runtime config with operator-signed live overrides."""

from __future__ import annotations

import base64
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

try:
    from scripts.license_gate import (
        INTEGRITY_MANIFEST_PATH,
        _load_integrity_manifest,
        _load_public_key,
        _verify_ed25519,
    )
except ModuleNotFoundError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from license_gate import (  # type: ignore
        INTEGRITY_MANIFEST_PATH,
        _load_integrity_manifest,
        _load_public_key,
        _verify_ed25519,
    )

OPERATOR_OVERRIDE_FILENAME = "operator_runtime_overrides.yml"
OPERATOR_OVERRIDE_SIG_SUFFIX = ".sig"


def read_yaml_mapping(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return payload


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in override.items():
        if isinstance(merged.get(key), Mapping) and isinstance(value, Mapping):
            merged[key] = deep_merge(dict(merged[key]), dict(value))
        else:
            merged[key] = value
    return merged


def sibling_override_paths(runtime_path: Path) -> tuple[Path, Path]:
    override_path = runtime_path.with_name(OPERATOR_OVERRIDE_FILENAME)
    sig_path = override_path.with_suffix(override_path.suffix + OPERATOR_OVERRIDE_SIG_SUFFIX)
    return override_path, sig_path


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().lower()


def _enforce_runtime_integrity(runtime_path: Path) -> None:
    manifest = _load_integrity_manifest(INTEGRITY_MANIFEST_PATH)
    if not manifest:
        return
    files = manifest.get("files", {})
    if not isinstance(files, dict):
        return
    repo_root = INTEGRITY_MANIFEST_PATH.resolve().parents[1]
    try:
        rel = str(runtime_path.resolve().relative_to(repo_root)).replace("\\", "/")
    except ValueError:
        return
    expected = str(files.get(rel, "")).strip().lower()
    if not expected:
        return
    actual = _sha256_file(runtime_path)
    if actual != expected:
        raise RuntimeError(f"Protected runtime config changed: {rel}")


def _verify_override_signature(override_path: Path, sig_path: Path) -> None:
    public_key = _load_public_key()
    if public_key is None:
        raise RuntimeError("Public key missing; cannot verify operator override signature.")
    if not sig_path.exists():
        raise RuntimeError(f"Operator override signature missing: {sig_path}")
    try:
        signature = base64.b64decode(sig_path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"Invalid operator override signature file: {sig_path}") from exc
    payload = override_path.read_bytes()
    if not _verify_ed25519(payload, signature, public_key):
        raise RuntimeError(f"Operator override signature verification failed: {override_path}")


def load_runtime_config(runtime_path: Path) -> dict[str, Any]:
    runtime_path = runtime_path.resolve()
    if not runtime_path.exists():
        raise FileNotFoundError(f"Runtime config not found: {runtime_path}")
    _enforce_runtime_integrity(runtime_path)
    base = read_yaml_mapping(runtime_path)
    override_path, sig_path = sibling_override_paths(runtime_path)
    if not override_path.exists():
        return base
    _verify_override_signature(override_path, sig_path)
    override = read_yaml_mapping(override_path)
    return deep_merge(base, override)


def dump_override_signature_metadata(override_path: Path, sig_path: Path) -> dict[str, Any]:
    return {
        "override_path": str(override_path),
        "signature_path": str(sig_path),
        "signature_present": sig_path.exists(),
    }

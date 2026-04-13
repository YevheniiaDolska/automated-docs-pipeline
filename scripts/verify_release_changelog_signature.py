#!/usr/bin/env python3
"""Verify signed release changelog using Ed25519 public key."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.license_gate import _verify_ed25519


def _load_b64_key(path: Path, expected: int) -> bytes:
    raw = path.read_bytes().strip()
    decoded = base64.b64decode(raw)
    if len(decoded) != expected:
        raise ValueError(f"Invalid key length in {path}: expected {expected}, got {len(decoded)}")
    return decoded


def _load_signature(path: Path) -> tuple[str, str]:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Signature JSON must be an object.")
        sig_b64 = str(payload.get("signature_b64", "")).strip()
        expected_sha256 = str(payload.get("changelog_sha256", "")).strip().lower()
        return sig_b64, expected_sha256
    return path.read_text(encoding="utf-8").strip(), ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify CHANGELOG.md signature.")
    parser.add_argument("--changelog", default="CHANGELOG.md", help="Changelog file path.")
    parser.add_argument("--signature", default="CHANGELOG.md.sig", help="Signature file (.sig or .json).")
    parser.add_argument("--public-key", default="docsops/keys/veriops-licensing.pub", help="Base64 Ed25519 public key.")
    args = parser.parse_args()

    changelog_path = Path(args.changelog).resolve()
    signature_path = Path(args.signature).resolve()
    public_key_path = Path(args.public_key).resolve()

    if not changelog_path.exists():
        raise SystemExit(f"Changelog file not found: {changelog_path}")
    if not signature_path.exists():
        raise SystemExit(f"Signature file not found: {signature_path}")
    if not public_key_path.exists():
        raise SystemExit(f"Public key file not found: {public_key_path}")

    content = changelog_path.read_bytes()
    digest = hashlib.sha256(content).hexdigest().lower()
    sig_b64, expected_sha256 = _load_signature(signature_path)
    if not sig_b64:
        raise SystemExit("Signature payload is empty.")
    if expected_sha256 and expected_sha256 != digest:
        raise SystemExit(
            f"Signature metadata digest mismatch: expected={expected_sha256} actual={digest}"
        )

    signature = base64.b64decode(sig_b64)
    public_key = _load_b64_key(public_key_path, 32)
    ok = _verify_ed25519(content, signature, public_key)
    if not ok:
        raise SystemExit("Signature verification failed.")

    print(f"[changelog-verify] PASS: {changelog_path}")
    print(f"[changelog-verify] sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Publish encrypted capability pack to server registry.

Uploads only encrypted pack bytes + metadata (checksum/signature).
No client repository content is transmitted.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path


def _load_private_key(path: Path) -> bytes:
    raw = path.read_bytes().strip()
    if len(raw) == 32:
        return raw
    try:
        decoded = base64.b64decode(raw)
        if len(decoded) == 32:
            return decoded
    except (ValueError, TypeError):
        decoded = b""
    if len(decoded) == 32:
        return decoded
    raise ValueError(f"Unsupported private key format: {path}")


def _sign_ed25519(message: bytes, private_key: bytes) -> bytes:
    nacl_available = True
    try:
        from nacl.signing import SigningKey

        return SigningKey(private_key).sign(message).signature
    except ImportError:
        nacl_available = False

    if nacl_available:
        raise RuntimeError("PyNaCl signing failed unexpectedly.")

    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        return Ed25519PrivateKey.from_private_bytes(private_key).sign(message)
    except ImportError as exc:
        raise RuntimeError(
            "No Ed25519 library installed (PyNaCl/cryptography)."
        ) from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish encrypted pack to ops registry")
    parser.add_argument("--pack", default="docsops/.capability_pack.enc", help="Path to encrypted pack")
    parser.add_argument("--pack-name", required=True, help="Registry pack name")
    parser.add_argument("--version", required=True, help="Pack version label")
    parser.add_argument("--plan", default="enterprise", help="Plan label")
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("VERIOPS_PACK_PUBLISH_URL", "https://api.veri-doc.app/ops/pack-registry/publish"),
        help="Publish endpoint URL",
    )
    parser.add_argument(
        "--ops-token",
        default=os.environ.get("VERIOPS_SERVER_SHARED_TOKEN", ""),
        help="Ops shared token (or set VERIOPS_SERVER_SHARED_TOKEN)",
    )
    parser.add_argument(
        "--private-key",
        default=os.environ.get("VERIOPS_PACK_SIGNING_KEY", "docsops/keys/veriops-licensing.key"),
        help="Ed25519 private key path",
    )
    args = parser.parse_args()

    if not args.ops_token.strip():
        raise SystemExit("Missing --ops-token (or VERIOPS_SERVER_SHARED_TOKEN)")

    pack_path = Path(args.pack)
    if not pack_path.exists():
        raise SystemExit(f"Pack file not found: {pack_path}")

    pack_bytes = pack_path.read_bytes()
    checksum = hashlib.sha256(pack_bytes).hexdigest()

    private_key = _load_private_key(Path(args.private_key))
    signature = _sign_ed25519(pack_bytes, private_key)

    body = {
        "pack_name": args.pack_name,
        "version": args.version,
        "plan": args.plan,
        "checksum_sha256": checksum,
        "encrypted_blob_b64": base64.b64encode(pack_bytes).decode("ascii"),
        "signature_b64": base64.b64encode(signature).decode("ascii"),
    }

    req = urllib.request.Request(
        args.endpoint,
        data=json.dumps(body, ensure_ascii=True).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-VeriOps-Server-Token": args.ops_token,
            "User-Agent": "VeriOps-Pack-Publisher/1.0",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

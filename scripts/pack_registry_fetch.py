#!/usr/bin/env python3
"""Fetch encrypted capability pack from server registry and verify it locally."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


def _load_public_key(path: Path) -> bytes:
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
    raise ValueError(f"Unsupported public key format: {path}")


def _verify_ed25519(message: bytes, signature: bytes, public_key: bytes) -> bool:
    nacl_available = True
    try:
        from nacl.signing import VerifyKey

        VerifyKey(public_key).verify(message, signature)
        return True
    except ImportError:
        nacl_available = False
    except (RuntimeError, ValueError, TypeError, OSError):
        return False

    if nacl_available:
        return False

    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message)
        return True
    except ImportError:
        return False
    except (RuntimeError, ValueError, TypeError, OSError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and verify encrypted pack from registry")
    parser.add_argument("--pack-name", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("VERIOPS_PACK_REGISTRY_URL", "https://api.veri-doc.app/ops/pack-registry/fetch"),
    )
    parser.add_argument(
        "--ops-token",
        default=os.environ.get("VERIOPS_SERVER_SHARED_TOKEN", ""),
        help="Ops shared token (or set VERIOPS_SERVER_SHARED_TOKEN)",
    )
    parser.add_argument(
        "--public-key",
        default=os.environ.get("VERIOPS_PACK_PUBLIC_KEY", "docsops/keys/veriops-licensing.pub"),
    )
    parser.add_argument("--output", default="docsops/.capability_pack.enc")
    args = parser.parse_args()

    if not args.ops_token.strip():
        raise SystemExit("Missing --ops-token (or VERIOPS_SERVER_SHARED_TOKEN)")

    query = urllib.parse.urlencode({"pack_name": args.pack_name, "version": args.version})
    url = f"{args.endpoint}?{query}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "X-VeriOps-Server-Token": args.ops_token,
            "User-Agent": "VeriOps-Pack-Fetcher/1.0",
        },
        method="GET",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    blob_b64 = str(payload.get("encrypted_blob_b64", "")).strip()
    checksum = str(payload.get("checksum_sha256", "")).strip().lower()
    signature_b64 = str(payload.get("signature_b64", "")).strip()
    if not blob_b64 or not checksum or not signature_b64:
        raise SystemExit("Registry response missing blob/checksum/signature")

    blob = base64.b64decode(blob_b64, validate=True)
    local_checksum = hashlib.sha256(blob).hexdigest()
    if local_checksum != checksum:
        raise SystemExit("Checksum mismatch; refusing to install pack")

    pub_key = _load_public_key(Path(args.public_key))
    signature = base64.b64decode(signature_b64, validate=True)
    if not _verify_ed25519(blob, signature, pub_key):
        raise SystemExit("Signature verification failed; refusing to install pack")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)

    print(
        json.dumps(
            {
                "status": "ok",
                "pack_name": args.pack_name,
                "version": args.version,
                "output": str(out),
                "checksum_sha256": checksum,
                "signature_verified": True,
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

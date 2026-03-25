#!/usr/bin/env python3
"""Server-side license JWT generator for VeriOps licensing.

Creates Ed25519-signed JWTs with plan-specific feature flags.
This script runs on the VeriOps server only -- never distributed to clients.

Usage:
  python3 build/generate_license.py \\
    --client-id acme-corp \\
    --plan enterprise \\
    --days 365 \\
    --output docsops/license.jwt

  python3 build/generate_license.py \\
    --client-id startup-xyz \\
    --plan pilot \\
    --days 90 \\
    --max-docs 100 \\
    --output docsops/license.jwt
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

logger = logging.getLogger(__name__)

from scripts.license_gate import (
    DEFAULT_GRACE_DAYS,
    PLAN_FEATURES,
    PLAN_PROTOCOLS,
)


def _b64url_encode(data: bytes) -> str:
    """Base64url encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _generate_ed25519_keypair() -> tuple[bytes, bytes]:
    """Generate Ed25519 keypair. Returns (private_key, public_key)."""
    try:
        from nacl.signing import SigningKey
        sk = SigningKey.generate()
        return bytes(sk), bytes(sk.verify_key)
    except ImportError:
        logger.debug("PyNaCl unavailable; trying cryptography for key generation")

    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import (
            Encoding, NoEncryption, PrivateFormat, PublicFormat,
        )
        private_key = Ed25519PrivateKey.generate()
        priv_bytes = private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
        pub_bytes = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        return priv_bytes, pub_bytes
    except ImportError:
        logger.debug("cryptography unavailable for Ed25519 key generation")

    raise RuntimeError("No Ed25519 library available. Install 'PyNaCl' or 'cryptography'.")


def _sign_ed25519(message: bytes, private_key: bytes) -> bytes:
    """Sign a message with Ed25519 private key."""
    try:
        from nacl.signing import SigningKey
        sk = SigningKey(private_key)
        signed = sk.sign(message)
        return signed.signature
    except ImportError:
        logger.debug("PyNaCl unavailable; trying cryptography for signing")

    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        key = Ed25519PrivateKey.from_private_bytes(private_key)
        return key.sign(message)
    except ImportError:
        logger.debug("cryptography unavailable for Ed25519 signing")

    raise RuntimeError("No Ed25519 library available. Install 'PyNaCl' or 'cryptography'.")


def generate_jwt(
    client_id: str,
    plan: str,
    days: int,
    private_key: bytes,
    max_docs: int = 0,
    protocols: list[str] | None = None,
    features_override: dict[str, bool] | None = None,
    offline_grace_days: int | None = None,
) -> str:
    """Generate a signed JWT license token."""
    now = int(time.time())
    exp = now + (days * 86400)

    if protocols is None:
        protocols = list(PLAN_PROTOCOLS.get(plan, ["rest"]))

    features = dict(PLAN_FEATURES.get(plan, PLAN_FEATURES["pilot"]))
    if features_override:
        features.update(features_override)

    if offline_grace_days is None:
        offline_grace_days = DEFAULT_GRACE_DAYS.get(plan, 7)

    header = {
        "alg": "EdDSA",
        "typ": "JWT",
    }

    payload = {
        "sub": client_id,
        "plan": plan,
        "iat": now,
        "exp": exp,
        "features": features,
        "protocols": protocols,
        "max_docs": max_docs,
        "offline_grace_days": offline_grace_days,
    }

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    message = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = _sign_ed25519(message, private_key)
    signature_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate VeriOps license JWT")
    parser.add_argument("--client-id", required=True, help="Client identifier (e.g., acme-corp)")
    parser.add_argument("--plan", choices=["pilot", "professional", "enterprise"], required=True)
    parser.add_argument("--days", type=int, default=365, help="License validity in days")
    parser.add_argument("--max-docs", type=int, default=0, help="Document limit (0 = unlimited)")
    parser.add_argument("--protocols", default="", help="Comma-separated protocol list override")
    parser.add_argument("--offline-grace-days", type=int, default=None)
    parser.add_argument("--output", default="docsops/license.jwt", help="Output JWT file path")
    parser.add_argument("--private-key", default="", help="Path to Ed25519 private key file")
    parser.add_argument(
        "--generate-keypair", action="store_true",
        help="Generate a new keypair and save to docsops/keys/",
    )
    args = parser.parse_args()

    keys_dir = REPO_ROOT / "docsops" / "keys"
    keys_dir.mkdir(parents=True, exist_ok=True)

    if args.generate_keypair:
        priv_key, pub_key = _generate_ed25519_keypair()
        priv_path = keys_dir / "veriops-licensing.key"
        pub_path = keys_dir / "veriops-licensing.pub"
        priv_path.write_bytes(base64.b64encode(priv_key))
        pub_path.write_bytes(base64.b64encode(pub_key))
        print(f"[keygen] Private key: {priv_path}")
        print(f"[keygen] Public key: {pub_path}")
        os.chmod(str(priv_path), 0o600)
    elif args.private_key:
        key_data = Path(args.private_key).read_bytes().strip()
        priv_key = base64.b64decode(key_data)
    else:
        default_key_path = keys_dir / "veriops-licensing.key"
        if default_key_path.exists():
            priv_key = base64.b64decode(default_key_path.read_bytes().strip())
        else:
            print("[error] No private key found. Use --generate-keypair or --private-key.")
            return 1

    protocols = args.protocols.split(",") if args.protocols else None

    token = generate_jwt(
        client_id=args.client_id,
        plan=args.plan,
        days=args.days,
        private_key=priv_key,
        max_docs=args.max_docs,
        protocols=protocols,
        offline_grace_days=args.offline_grace_days,
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(token + "\n", encoding="utf-8")
    print(f"[license] JWT written to {out_path}")
    print(f"[license] Client: {args.client_id} | Plan: {args.plan} | Valid: {args.days} days")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

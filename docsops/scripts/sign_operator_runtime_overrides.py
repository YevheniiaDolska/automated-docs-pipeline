#!/usr/bin/env python3
"""Sign operator runtime overrides for live post-build tuning."""

from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.runtime_config_loader import sibling_override_paths


def _sign_ed25519(message: bytes, private_key: bytes) -> bytes:
    try:
        from nacl.signing import SigningKey
        key = SigningKey(private_key)
        signed = key.sign(message)
        return signed.signature
    except ImportError:
        pass
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        key = Ed25519PrivateKey.from_private_bytes(private_key)
        return key.sign(message)
    except ImportError:
        pass
    raise RuntimeError("No Ed25519 library available. Install 'PyNaCl' or 'cryptography'.")


def _load_private_key(path: Path) -> bytes:
    raw = path.read_bytes().strip()
    if len(raw) == 32:
        return raw
    decoded = base64.b64decode(raw)
    if len(decoded) != 32:
        raise ValueError(f"Invalid Ed25519 private key length: {path}")
    return decoded


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sign operator runtime overrides")
    parser.add_argument(
        "--runtime-config",
        default="docsops/config/client_runtime.yml",
        help="Base runtime config path; override file is resolved next to it.",
    )
    parser.add_argument(
        "--private-key",
        default="docsops/keys/veriops-licensing.key",
        help="Ed25519 private key path available only on operator machine.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runtime_path = Path(args.runtime_config).resolve()
    override_path, sig_path = sibling_override_paths(runtime_path)
    if not override_path.exists():
        raise FileNotFoundError(f"Override file not found: {override_path}")
    private_key = _load_private_key(Path(args.private_key).resolve())
    signature = _sign_ed25519(override_path.read_bytes(), private_key)
    sig_path.write_text(base64.b64encode(signature).decode("ascii") + "\n", encoding="utf-8")
    print(f"[ok] override signed: {override_path}")
    print(f"[ok] signature written: {sig_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

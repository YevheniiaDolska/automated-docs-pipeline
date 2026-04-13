#!/usr/bin/env python3
"""Sign release changelog with Ed25519 and emit signature artifacts."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "build") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "build"))

from generate_license import _sign_ed25519


def _load_b64_key(path: Path, expected: int) -> bytes:
    raw = path.read_bytes().strip()
    decoded = base64.b64decode(raw)
    if len(decoded) != expected:
        raise ValueError(f"Invalid key length in {path}: expected {expected}, got {len(decoded)}")
    return decoded


def main() -> int:
    parser = argparse.ArgumentParser(description="Sign CHANGELOG.md using Ed25519 private key.")
    parser.add_argument("--changelog", default="CHANGELOG.md", help="Changelog file path.")
    parser.add_argument("--private-key", default="docsops/keys/veriops-licensing.key", help="Base64 Ed25519 private key.")
    parser.add_argument("--public-key", default="docsops/keys/veriops-licensing.pub", help="Base64 Ed25519 public key.")
    parser.add_argument("--signature", default="CHANGELOG.md.sig", help="Output base64 signature path.")
    parser.add_argument("--metadata", default="reports/changelog_signature.json", help="Output JSON metadata path.")
    args = parser.parse_args()

    changelog_path = Path(args.changelog).resolve()
    private_key_path = Path(args.private_key).resolve()
    public_key_path = Path(args.public_key).resolve()
    signature_path = Path(args.signature).resolve()
    metadata_path = Path(args.metadata).resolve()

    if not changelog_path.exists():
        raise SystemExit(f"Changelog file not found: {changelog_path}")
    if not private_key_path.exists():
        raise SystemExit(f"Private key file not found: {private_key_path}")
    if not public_key_path.exists():
        raise SystemExit(f"Public key file not found: {public_key_path}")

    content = changelog_path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    private_key = _load_b64_key(private_key_path, 32)
    public_key = _load_b64_key(public_key_path, 32)
    signature = _sign_ed25519(content, private_key)
    signature_b64 = base64.b64encode(signature).decode("ascii")
    key_id = hashlib.sha256(public_key).hexdigest()[:16]

    signature_path.parent.mkdir(parents=True, exist_ok=True)
    signature_path.write_text(signature_b64 + "\n", encoding="utf-8")
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "changelog_path": str(changelog_path),
        "changelog_sha256": digest,
        "signature_path": str(signature_path),
        "signature_b64": signature_b64,
        "public_key_path": str(public_key_path),
        "key_id": key_id,
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    print(f"[changelog-sign] signature: {signature_path}")
    print(f"[changelog-sign] metadata: {metadata_path}")
    print(f"[changelog-sign] sha256: {digest}")
    print(f"[changelog-sign] key_id: {key_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

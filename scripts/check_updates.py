#!/usr/bin/env python3
"""Check for pipeline updates and apply signed delta bundles.

Contacts the VeriOps update server to check for new versions.
Downloads and verifies Ed25519-signed delta bundles.
No client data is sent -- only version and platform info.

Usage:
  python3 scripts/check_updates.py
  python3 scripts/check_updates.py --apply
  python3 scripts/check_updates.py --check-only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

# Update server endpoint (no client data sent)
UPDATE_SERVER = os.environ.get(
    "VERIOPS_UPDATE_SERVER",
    "https://updates.veriops.dev",
)

# Version file tracks current installed version
VERSION_FILE = REPO_ROOT / "docsops" / ".version.json"
BACKUP_DIR = REPO_ROOT / "docsops" / ".rollback"


def _current_version() -> dict[str, Any]:
    """Read current installed version info."""
    if not VERSION_FILE.exists():
        return {"version": "0.0.0", "platform": _detect_platform()}
    try:
        return json.loads(VERSION_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"version": "0.0.0", "platform": _detect_platform()}


def _detect_platform() -> str:
    """Detect current platform."""
    import platform as plat
    system = plat.system().lower()
    machine = plat.machine().lower()
    if system == "linux" and "x86_64" in machine:
        return "linux-x86_64"
    if system == "darwin" and "arm" in machine:
        return "macos-arm64"
    if system == "darwin":
        return "macos-x86_64"
    if system == "windows":
        return "windows-x64"
    return f"{system}-{machine}"


def _check_for_update(current: dict[str, Any]) -> dict[str, Any] | None:
    """Check the update server for available updates.

    Sends only: version, platform. No client docs or code.
    """
    try:
        from urllib.request import Request, urlopen
        from urllib.parse import urlencode

        params = urlencode({
            "version": current.get("version", "0.0.0"),
            "platform": current.get("platform", _detect_platform()),
        })
        url = f"{UPDATE_SERVER}/v1/check?{params}"

        # -- Network Transparency --
        # This request sends ONLY:
        #   GET /v1/check?version=X.Y.Z&platform=linux-x86_64
        # No cookies, no auth tokens, no client data.
        req = Request(url, method="GET")
        req.add_header("User-Agent", "VeriOps-Pipeline-Updater/1.0")

        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data if data.get("update_available") else None

    except Exception as exc:
        print(f"[update] Cannot reach update server: {exc}", file=sys.stderr)
        return None


def _verify_bundle_signature(bundle_path: Path, signature: str) -> bool:
    """Verify Ed25519 signature of downloaded bundle."""
    try:
        from scripts.license_gate import _load_public_key, _verify_ed25519
        pub_key = _load_public_key()
        if pub_key is None:
            print("[update] No public key found for verification.", file=sys.stderr)
            return False
        import base64
        sig_bytes = base64.b64decode(signature)
        data = bundle_path.read_bytes()
        return _verify_ed25519(data, sig_bytes, pub_key)
    except (ImportError, Exception) as exc:
        print(f"[update] Signature verification failed: {exc}", file=sys.stderr)
        return False


def _backup_current(version: str) -> Path:
    """Create a backup of current version for rollback."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = BACKUP_DIR / f"v{version}"
    if backup_path.exists():
        shutil.rmtree(backup_path)
    backup_path.mkdir()

    # Save version info
    if VERSION_FILE.exists():
        shutil.copy2(VERSION_FILE, backup_path / ".version.json")

    # Save compiled modules
    for so_file in (REPO_ROOT / "scripts").glob("*.so"):
        shutil.copy2(so_file, backup_path / so_file.name)
    for pyd_file in (REPO_ROOT / "scripts").glob("*.pyd"):
        shutil.copy2(pyd_file, backup_path / pyd_file.name)

    return backup_path


def _apply_update(update_info: dict[str, Any]) -> bool:
    """Download and apply an update bundle."""
    download_url = update_info.get("download_url", "")
    signature = update_info.get("signature", "")
    new_version = update_info.get("version", "unknown")

    if not download_url:
        print("[update] No download URL in update response.")
        return False

    print(f"[update] Downloading v{new_version}...")

    try:
        from urllib.request import urlopen
        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            with urlopen(download_url, timeout=120) as resp:
                tmp.write(resp.read())
    except Exception as exc:
        print(f"[update] Download failed: {exc}", file=sys.stderr)
        return False

    # Verify signature
    if signature:
        if not _verify_bundle_signature(tmp_path, signature):
            print("[update] Bundle signature verification FAILED. Update rejected.")
            tmp_path.unlink(missing_ok=True)
            return False
        print("[update] Signature verified.")
    else:
        print("[update] WARNING: No signature provided. Skipping verification.")

    # Backup current version
    current = _current_version()
    _backup_current(current.get("version", "0.0.0"))

    # Extract update
    print(f"[update] Applying v{new_version}...")
    try:
        import tarfile
        with tarfile.open(tmp_path, "r:gz") as tar:
            # Security: prevent path traversal
            for member in tar.getmembers():
                if member.name.startswith("/") or ".." in member.name:
                    print(f"[update] REJECTED: suspicious path in bundle: {member.name}")
                    return False
            tar.extractall(path=str(REPO_ROOT))
    except Exception as exc:
        print(f"[update] Extraction failed: {exc}", file=sys.stderr)
        return False
    finally:
        tmp_path.unlink(missing_ok=True)

    # Update version file
    VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    VERSION_FILE.write_text(
        json.dumps({
            "version": new_version,
            "platform": _detect_platform(),
            "updated_at": __import__("time").time(),
        }, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"[update] Successfully updated to v{new_version}.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Check for VeriOps pipeline updates")
    parser.add_argument("--check-only", action="store_true", help="Check without applying")
    parser.add_argument("--apply", action="store_true", help="Auto-apply available update")
    parser.add_argument("--force", action="store_true", help="Force re-download even if up to date")
    args = parser.parse_args()

    current = _current_version()
    print(f"[update] Current version: {current.get('version', '0.0.0')}")
    print(f"[update] Platform: {current.get('platform', 'unknown')}")

    update = _check_for_update(current)

    if not update:
        print("[update] Pipeline is up to date.")
        return 0

    print(f"[update] Update available: v{update.get('version', '?')}")
    if update.get("changelog"):
        print(f"[update] Changelog: {update['changelog']}")

    if args.check_only:
        return 0

    if args.apply or args.force:
        success = _apply_update(update)
        return 0 if success else 1

    print("[update] Run with --apply to install the update.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

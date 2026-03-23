#!/usr/bin/env python3
"""Rollback pipeline to a previous version.

Restores compiled modules and version info from a backup
created during the last update.

Usage:
  python3 scripts/rollback.py --list          # List available backups
  python3 scripts/rollback.py --version 1.0.0 # Rollback to specific version
  python3 scripts/rollback.py --latest        # Rollback to previous version
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = REPO_ROOT / "docsops" / ".version.json"
BACKUP_DIR = REPO_ROOT / "docsops" / ".rollback"


def _list_backups() -> list[str]:
    """List available backup versions."""
    if not BACKUP_DIR.exists():
        return []
    return sorted(
        [d.name.lstrip("v") for d in BACKUP_DIR.iterdir() if d.is_dir()],
        reverse=True,
    )


def _rollback_to(version: str) -> bool:
    """Restore a specific backup version."""
    backup_path = BACKUP_DIR / f"v{version}"
    if not backup_path.exists():
        print(f"[rollback] Backup not found: v{version}", file=sys.stderr)
        return False

    print(f"[rollback] Restoring v{version}...")

    # Restore version file
    backup_version = backup_path / ".version.json"
    if backup_version.exists():
        shutil.copy2(backup_version, VERSION_FILE)

    # Restore compiled modules
    scripts_dir = REPO_ROOT / "scripts"
    restored = 0
    for ext in ("*.so", "*.pyd"):
        for module_file in backup_path.glob(ext):
            target = scripts_dir / module_file.name
            shutil.copy2(module_file, target)
            restored += 1

    print(f"[rollback] Restored {restored} compiled modules.")
    print(f"[rollback] Successfully rolled back to v{version}.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Rollback VeriOps pipeline to previous version")
    parser.add_argument("--list", action="store_true", help="List available backups")
    parser.add_argument("--version", help="Rollback to specific version")
    parser.add_argument("--latest", action="store_true", help="Rollback to most recent backup")
    args = parser.parse_args()

    if args.list:
        backups = _list_backups()
        if not backups:
            print("[rollback] No backups available.")
            return 0
        print("[rollback] Available backups:")
        for v in backups:
            print(f"  v{v}")
        return 0

    if args.latest:
        backups = _list_backups()
        if not backups:
            print("[rollback] No backups available.", file=sys.stderr)
            return 1
        return 0 if _rollback_to(backups[0]) else 1

    if args.version:
        return 0 if _rollback_to(args.version) else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

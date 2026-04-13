#!/usr/bin/env python3
"""Enable/update server ops timers remotely over SSH in one command."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Enable VeriDoc ops timers on a remote server.")
    parser.add_argument("--host", required=True, help="Server host or IP.")
    parser.add_argument("--user", default="root", help="SSH user (default: root).")
    parser.add_argument("--repo-dir", default="/opt/veridoc", help="Remote repository path.")
    parser.add_argument("--ssh-key", default="", help="Optional SSH private key path.")
    parser.add_argument("--sudo", action="store_true", help="Prefix remote commands with sudo.")
    args = parser.parse_args()

    prefix = "sudo " if args.sudo else ""
    remote_cmd = (
        f"set -euo pipefail; "
        f"cd {shlex.quote(args.repo_dir)}; "
        f"{prefix}bash deploy/setup_observability.sh {shlex.quote(args.repo_dir)}; "
        "systemctl list-timers --all | grep -E "
        "'veridoc-(healthcheck|error)-monitor|veridoc-license-renew|veridoc-client-key-rotation'"
    )

    cmd: list[str] = ["ssh", "-o", "BatchMode=yes"]
    if args.ssh_key.strip():
        cmd.extend(["-i", args.ssh_key.strip()])
    cmd.append(f"{args.user}@{args.host}")
    cmd.append(remote_cmd)

    completed = subprocess.run(cmd, check=False)
    if completed.returncode == 0:
        print("[ok] server ops timers are enabled.")
    else:
        print("[error] failed to enable server ops timers via SSH.")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())

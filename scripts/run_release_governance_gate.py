#!/usr/bin/env python3
"""Run governance checks required for RC/release readiness."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> tuple[int, str]:
    completed = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    tail = (completed.stdout + "\n" + completed.stderr)[-2000:]
    return completed.returncode, tail


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RC/release governance gate.")
    parser.add_argument("--skip-hardening-matrix", action="store_true", help="Skip hardening e2e matrix.")
    args = parser.parse_args()

    checks: list[tuple[str, list[str]]] = [
        ("main_rules_compliance", [sys.executable, "scripts/check_main_rules_compliance.py"]),
        (
            "signed_changelog",
            [
                sys.executable,
                "scripts/verify_release_changelog_signature.py",
                "--changelog",
                "CHANGELOG.md",
                "--signature",
                "CHANGELOG.md.sig",
                "--public-key",
                "docsops/keys/veriops-licensing.pub",
            ],
        ),
    ]
    if not args.skip_hardening_matrix:
        checks.append(("hardening_e2e_matrix", [sys.executable, "scripts/run_hardening_e2e_matrix.py"]))

    failed = False
    for name, cmd in checks:
        rc, tail = _run(cmd)
        status = "PASS" if rc == 0 else "FAIL"
        print(f"[release-gate] {name}: {status}")
        if rc != 0:
            failed = True
            print(tail)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

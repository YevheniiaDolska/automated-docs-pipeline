#!/usr/bin/env python3
"""One-command Acme demo flow: autopipeline -> mkdocs demo build."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> int:
    print(f"[demo:acme:full] $ {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False)
    return int(completed.returncode)


def _default_runtime() -> Path | None:
    candidate = REPO_ROOT / "docsops" / "config" / "client_runtime.yml"
    return candidate if candidate.exists() else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run full Acme demo flow in one command")
    parser.add_argument("--reports-dir", default="reports/demo-acme")
    parser.add_argument("--output-root", default="demo-showcase/acme")
    parser.add_argument("--runtime-config", default="")
    parser.add_argument("--mode", choices=["operator", "veridoc"], default="veridoc")
    parser.add_argument("--skip-autopipeline", action="store_true")
    parser.add_argument(
        "--with-consolidated-report",
        action="store_true",
        help="Include consolidated report stage (default: skip for manual demo runs)",
    )
    parser.add_argument("--since", type=int, default=7)
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir)
    output_root = Path(args.output_root)
    runtime_path = Path(args.runtime_config) if args.runtime_config else _default_runtime()

    if not args.skip_autopipeline:
        if runtime_path is None:
            print("[demo:acme:full] Runtime config missing at docsops/config/client_runtime.yml.")
            print("[demo:acme:full] Pass --runtime-config <path> or run with --skip-autopipeline.")
            return 2

        autopipeline_cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "run_autopipeline.py"),
            "--docsops-root",
            ".",
            "--reports-dir",
            str(reports_dir),
            "--runtime-config",
            str(runtime_path),
            "--mode",
            args.mode,
            "--since",
            str(args.since),
        ]
        if not args.with_consolidated_report:
            autopipeline_cmd.append("--skip-consolidated-report")
        if args.mode == "veridoc":
            autopipeline_cmd.append("--skip-local-llm-packet")

        rc = _run(autopipeline_cmd)
        if rc != 0:
            return rc

    build_cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "build_acme_demo_site.py"),
        "--output-root",
        str(output_root),
        "--reports-dir",
        str(reports_dir),
        "--build",
    ]
    rc = _run(build_cmd)
    if rc != 0:
        return rc

    print("[demo:acme:full] Done.")
    print(f"[demo:acme:full] Site source: {output_root}")
    print(f"[demo:acme:full] Built site: {output_root / 'site' / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

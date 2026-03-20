#!/usr/bin/env python3
"""Create one doc and immediately run autopipeline in one command."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_TYPES = ["tutorial", "how-to", "concept", "reference", "troubleshooting", "api"]


def _run(cmd: list[str]) -> int:
    print(f"[doc:new:auto] $ {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False)
    return int(completed.returncode)


def _default_runtime() -> Path | None:
    candidate = REPO_ROOT / "docsops" / "config" / "client_runtime.yml"
    return candidate if candidate.exists() else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new doc and run autopipeline")
    parser.add_argument("doc_type", choices=DOC_TYPES)
    parser.add_argument("title")
    parser.add_argument("--output", default="")
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument("--locale", default="")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--runtime-config", default="")
    parser.add_argument("--mode", choices=["operator", "veridoc"], default="operator")
    parser.add_argument(
        "--with-consolidated-report",
        action="store_true",
        help="Include consolidated report stage (default: skip for manual runs)",
    )
    parser.add_argument("--since", type=int, default=7)
    args = parser.parse_args()

    create_cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "new_doc.py"),
        args.doc_type,
        args.title,
        "--docs-dir",
        args.docs_dir,
    ]
    if args.output:
        create_cmd.extend(["--output", args.output])
    if args.locale:
        create_cmd.extend(["--locale", args.locale])

    rc = _run(create_cmd)
    if rc != 0:
        return rc

    runtime_path = Path(args.runtime_config) if args.runtime_config else _default_runtime()
    if runtime_path is None:
        print("[doc:new:auto] Runtime config missing at docsops/config/client_runtime.yml.")
        print("[doc:new:auto] Pass --runtime-config <path>.")
        return 2

    pipeline_cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "run_autopipeline.py"),
        "--docsops-root",
        ".",
        "--reports-dir",
        args.reports_dir,
        "--runtime-config",
        str(runtime_path),
        "--mode",
        args.mode,
        "--since",
        str(args.since),
    ]
    if not args.with_consolidated_report:
        pipeline_cmd.append("--skip-consolidated-report")
    if args.mode == "veridoc":
        pipeline_cmd.append("--skip-local-llm-packet")

    return _run(pipeline_cmd)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run unified docs CI checks across site generators."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any

import yaml


def _run_shell(command: str, cwd: Path) -> int:
    print(f"[docs-ci] $ {command}")
    completed = subprocess.run(shlex.split(command), cwd=str(cwd), check=False)
    return int(completed.returncode)


def _read_runtime(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (RuntimeError, ValueError, TypeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _resolve_generator(runtime: dict[str, Any]) -> str:
    env_value = os.getenv("DOCSOPS_SITE_GENERATOR", "").strip().lower()
    if env_value:
        return env_value
    docs_site = runtime.get("docs_site", {})
    if isinstance(docs_site, dict):
        value = str(docs_site.get("generator", "")).strip().lower()
        if value:
            return value
    targets = runtime.get("output_targets", [])
    if isinstance(targets, list):
        for item in targets:
            val = str(item).strip().lower()
            if val:
                return val
    return "mkdocs"


def _resolve_lint_command(runtime: dict[str, Any]) -> str:
    env_value = os.getenv("DOCSOPS_DOCS_LINT_COMMAND", "").strip()
    if env_value:
        return env_value
    finalize = runtime.get("finalize_gate", {})
    if isinstance(finalize, dict):
        cmd = str(finalize.get("lint_command", "")).strip()
        if cmd:
            return cmd
    return "npm run lint"


def _has_npm_lint_script(repo_root: Path) -> bool:
    package_json = repo_root / "package.json"
    if not package_json.exists():
        return False
    try:
        payload = json.loads(package_json.read_text(encoding="utf-8"))
    except (RuntimeError, ValueError, TypeError, OSError):
        return False
    scripts = payload.get("scripts", {}) if isinstance(payload, dict) else {}
    return isinstance(scripts, dict) and "lint" in scripts


def _resolve_build_command(runtime: dict[str, Any], generator: str) -> str:
    env_value = os.getenv("DOCSOPS_SITE_BUILD_COMMAND", "").strip()
    if env_value:
        return env_value
    docs_site = runtime.get("docs_site", {})
    if isinstance(docs_site, dict):
        if not bool(docs_site.get("build_enabled", True)):
            return ""
        explicit = str(docs_site.get("build_command", "")).strip()
        if explicit:
            return explicit

    mapping = {
        "mkdocs": "mkdocs build --strict",
        "sphinx": "sphinx-build -W -b html docs docs/_build/html",
        "docusaurus": "npm run build",
        "vitepress": "npm run docs:build",
        "hugo": "hugo --minify",
        "jekyll": "bundle exec jekyll build",
        "docsify": "",
        "custom": "",
    }
    return mapping.get(generator, "")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run docs lint/build CI checks")
    parser.add_argument("--runtime-config", default="docsops/config/client_runtime.yml")
    parser.add_argument("--skip-build", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    runtime = _read_runtime(Path(args.runtime_config).resolve())

    generator = _resolve_generator(runtime)
    lint_command = _resolve_lint_command(runtime)
    build_command = _resolve_build_command(runtime, generator)
    runtime_cfg = str(args.runtime_config)

    if lint_command.strip() == "npm run lint" and not _has_npm_lint_script(repo_root):
        lint_command = (
            f"python3 docsops/scripts/finalize_docs_gate.py --docs-root docs "
            f"--reports-dir reports --runtime-config {shlex.quote(runtime_cfg)} --continue-on-error"
        )

    print(f"[docs-ci] generator={generator}")
    lint_rc = _run_shell(lint_command, repo_root)
    if lint_rc != 0:
        print(f"[docs-ci] lint failed (rc={lint_rc})")
        return lint_rc

    if args.skip_build or not build_command:
        print("[docs-ci] build step skipped")
        return 0

    build_rc = _run_shell(build_command, repo_root)
    if build_rc != 0:
        print(f"[docs-ci] build failed (rc={build_rc})")
    else:
        print("[docs-ci] build passed")
    return build_rc


if __name__ == "__main__":
    raise SystemExit(main())

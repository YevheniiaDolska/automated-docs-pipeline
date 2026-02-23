#!/usr/bin/env python3
"""Run smoke checks for markdown code examples explicitly tagged with `smoke`."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class CodeBlock:
    """Represents a fenced markdown code block."""

    path: Path
    line: int
    language: str
    tags: set[str]
    content: str


def _iter_markdown_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_file() and path.suffix.lower() == ".md":
            files.append(path)
            continue
        if path.is_dir():
            files.extend(sorted(path.rglob("*.md")))
    return sorted(set(files))


def _parse_blocks(path: Path) -> list[CodeBlock]:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    blocks: list[CodeBlock] = []

    in_block = False
    start_line = 0
    language = ""
    tags: set[str] = set()
    body: list[str] = []

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not in_block and stripped.startswith("```"):
            info = stripped[3:].strip()
            tokens = [token.strip().lower() for token in info.split() if token.strip()]
            language = tokens[0] if tokens else ""
            tags = set(tokens[1:])
            body = []
            start_line = index
            in_block = True
            continue

        if in_block and stripped.startswith("```"):
            blocks.append(
                CodeBlock(
                    path=path,
                    line=start_line,
                    language=language,
                    tags=tags,
                    content="\n".join(body).strip("\n"),
                )
            )
            in_block = False
            continue

        if in_block:
            body.append(line)

    return blocks


def _run_python(content: str, timeout: int) -> tuple[bool, str]:
    with tempfile.NamedTemporaryFile("w", suffix=".py", encoding="utf-8", delete=False) as handle:
        handle.write(content + "\n")
        script_path = Path(handle.name)
    try:
        result = subprocess.run(
            ["python3", str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            return False, result.stderr.strip() or "python example failed"
        return True, ""
    finally:
        script_path.unlink(missing_ok=True)


def _run_bash(content: str, timeout: int) -> tuple[bool, str]:
    with tempfile.NamedTemporaryFile("w", suffix=".sh", encoding="utf-8", delete=False) as handle:
        handle.write("set -euo pipefail\n")
        handle.write(content + "\n")
        script_path = Path(handle.name)
    try:
        subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )
        result = subprocess.run(
            ["bash", str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            return False, result.stderr.strip() or "bash example failed"
        return True, ""
    except subprocess.CalledProcessError as error:
        return False, error.stderr.strip() or "bash syntax check failed"
    finally:
        script_path.unlink(missing_ok=True)


def _run_json(content: str) -> tuple[bool, str]:
    try:
        json.loads(content)
        return True, ""
    except json.JSONDecodeError as error:
        return False, str(error)


def _run_yaml(content: str) -> tuple[bool, str]:
    try:
        yaml.safe_load(content)
        return True, ""
    except yaml.YAMLError as error:
        return False, str(error)


def _run_js(content: str, timeout: int) -> tuple[bool, str]:
    node = shutil.which("node")
    if node is None:
        return False, "node is not installed but JavaScript smoke block was found"

    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
        handle.write(content + "\n")
        script_path = Path(handle.name)
    try:
        syntax = subprocess.run(
            [node, "--check", str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if syntax.returncode != 0:
            return False, syntax.stderr.strip() or "javascript syntax check failed"
        run = subprocess.run(
            [node, str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if run.returncode != 0:
            return False, run.stderr.strip() or "javascript example failed"
        return True, ""
    finally:
        script_path.unlink(missing_ok=True)


def _run_curl(content: str, timeout: int, execute: bool) -> tuple[bool, str]:
    curl_bin = shutil.which("curl")
    if curl_bin is None:
        return False, "curl is not installed but curl smoke block was found"

    with tempfile.NamedTemporaryFile("w", suffix=".sh", encoding="utf-8", delete=False) as handle:
        handle.write("set -euo pipefail\n")
        handle.write(content + "\n")
        script_path = Path(handle.name)
    try:
        syntax = subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if syntax.returncode != 0:
            return False, syntax.stderr.strip() or "curl snippet syntax check failed"

        if not execute:
            return True, ""

        run = subprocess.run(
            ["bash", str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if run.returncode != 0:
            return False, run.stderr.strip() or "curl example failed"
        return True, ""
    finally:
        script_path.unlink(missing_ok=True)


def _run_go(content: str, timeout: int) -> tuple[bool, str]:
    go_bin = shutil.which("go")
    if go_bin is None:
        return False, "go is not installed but Go smoke block was found"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_path = temp_path / "main.go"
        source_path.write_text(content + "\n", encoding="utf-8")

        mod_init = subprocess.run(
            [go_bin, "mod", "init", "smokeexample"],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if mod_init.returncode != 0 and "go.mod already exists" not in (mod_init.stderr or ""):
            return False, mod_init.stderr.strip() or "go module init failed"

        build = subprocess.run(
            [go_bin, "build", "./..."],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if build.returncode != 0:
            return False, build.stderr.strip() or "go example build failed"
        return True, ""


def _run_typescript(content: str, timeout: int) -> tuple[bool, str]:
    tsc_bin = shutil.which("tsc")
    if tsc_bin is None:
        return False, "tsc is not installed but TypeScript smoke block was found"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_path = temp_path / "example.ts"
        source_path.write_text(content + "\n", encoding="utf-8")

        compile_result = subprocess.run(
            [
                tsc_bin,
                "--pretty",
                "false",
                "--noEmit",
                "--target",
                "ES2020",
                "--module",
                "commonjs",
                str(source_path),
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if compile_result.returncode != 0:
            return False, compile_result.stderr.strip() or "typescript compile check failed"
        return True, ""


def _run_smoke_block(block: CodeBlock, timeout: int, allow_network: bool) -> tuple[bool, str]:
    language = block.language
    if language in {"python", "py"}:
        return _run_python(block.content, timeout)
    if language in {"bash", "sh", "shell"}:
        return _run_bash(block.content, timeout)
    if language == "json":
        return _run_json(block.content)
    if language in {"yaml", "yml"}:
        return _run_yaml(block.content)
    if language in {"javascript", "js"}:
        return _run_js(block.content, timeout)
    if language in {"typescript", "ts"}:
        return _run_typescript(block.content, timeout)
    if language == "go":
        return _run_go(block.content, timeout)
    if language == "curl":
        # Curl examples are often network-bound. Execute only when explicitly tagged
        # with `network` and network execution is enabled.
        should_execute = "network" in block.tags and allow_network
        return _run_curl(block.content, timeout, should_execute)
    return False, f"unsupported language for smoke execution: '{language}'"


def run_smoke(paths: list[str], timeout: int, allow_empty: bool, allow_network: bool) -> int:
    files = _iter_markdown_files(paths)
    blocks: list[CodeBlock] = []
    for file_path in files:
        blocks.extend(_parse_blocks(file_path))

    smoke_blocks = [block for block in blocks if "smoke" in block.tags]
    print(f"Scanned markdown files: {len(files)}")
    print(f"Smoke-tagged code blocks: {len(smoke_blocks)}")

    if not smoke_blocks and not allow_empty:
        print("No smoke-tagged code examples found. Add fenced blocks with a `smoke` tag.")
        return 1

    failures: list[str] = []
    for block in smoke_blocks:
        ok, reason = _run_smoke_block(block, timeout, allow_network)
        if not ok:
            failures.append(f"{block.path}:{block.line} -> {reason}")

    if failures:
        print("Smoke code example failures detected:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Smoke code examples check passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run smoke checks for markdown code examples")
    parser.add_argument(
        "--paths",
        nargs="+",
        default=["docs", "templates"],
        help="Markdown files or directories to scan",
    )
    parser.add_argument("--timeout", type=int, default=12, help="Per-block timeout in seconds")
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow zero smoke-tagged examples",
    )
    parser.add_argument(
        "--allow-network",
        action="store_true",
        help="Allow execution of smoke blocks tagged with `network`",
    )
    args = parser.parse_args()

    return run_smoke(
        paths=args.paths,
        timeout=args.timeout,
        allow_empty=args.allow_empty,
        allow_network=args.allow_network,
    )


if __name__ == "__main__":
    raise SystemExit(main())

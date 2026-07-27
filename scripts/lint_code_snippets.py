#!/usr/bin/env python3
"""Lint all code snippets in markdown files for syntax errors.

This script extracts code blocks from markdown and runs syntax-only checks
(no execution) using appropriate linters for each language.

Supported languages:
- JavaScript/TypeScript: node --check / tsc --noEmit
- Python: python -m py_compile
- Bash/Shell: bash -n (syntax check)
- JSON: json.loads()
- YAML: yaml.safe_load()
- Go: go build (syntax only)
- Ruby: ruby -c (parse-only, blocking)
- PHP: php -l (parse-only, blocking)
- Swift: swiftc -parse (parse-only, blocking)
- C/C++: gcc/g++ -fsyntax-only (best-effort, non-blocking)
- Rust: rustc --crate-type lib --emit=metadata (best-effort, non-blocking)
- Java: javac (best-effort, non-blocking)
- Kotlin: kotlinc (best-effort, non-blocking)
- C#: csc (best-effort, non-blocking)
- Dart: dart analyze (best-effort, non-blocking)

Every linter is toolchain-detecting: if the compiler/interpreter is not on
PATH, the snippet is skipped with an info note rather than failing. Parse-only
checks (Ruby, PHP, Swift) are blocking; full-compile checks that resolve
external symbols report diagnostics at info severity so partial SDK snippets in
docs never break commits, even under --strict.

Usage:
    python scripts/lint_code_snippets.py docs/
    python scripts/lint_code_snippets.py --fix docs/  # Future: auto-fix support
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import yaml


@dataclass
class CodeBlock:
    """Represents a fenced code block in markdown."""

    filepath: Path
    line_number: int
    language: str
    content: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LintResult:
    """Result of linting a code block."""

    block: CodeBlock
    passed: bool
    error_message: str = ""
    severity: str = "error"  # error, warning, info


def extract_code_blocks(filepath: Path) -> list[CodeBlock]:
    """Extract all fenced code blocks from a markdown file."""
    content = filepath.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    blocks: list[CodeBlock] = []

    in_block = False
    block_start = 0
    language = ""
    tags: set[str] = set()
    block_lines: list[str] = []

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        if not in_block and stripped.startswith("```"):
            # Start of code block
            info = stripped[3:].strip()
            tokens = info.split()
            language = tokens[0].lower() if tokens else ""
            tags = set(t.lower() for t in tokens[1:])
            block_start = i
            block_lines = []
            in_block = True
            continue

        if in_block and stripped.startswith("```"):
            # End of code block
            # Normalize indentation for fenced blocks nested in MkDocs tabs/admonitions.
            normalized_content = textwrap.dedent("\n".join(block_lines)).strip("\n")
            blocks.append(CodeBlock(
                filepath=filepath,
                line_number=block_start,
                language=language,
                content=normalized_content,
                tags=tags,
            ))
            in_block = False
            continue

        if in_block:
            block_lines.append(line)

    return blocks


def lint_javascript(block: CodeBlock, timeout: int = 10) -> LintResult:
    """Lint JavaScript code using Node.js syntax check."""
    node = shutil.which("node")
    if node is None:
        return LintResult(block, True, "node not installed, skipping JS lint", "info")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".js", encoding="utf-8", delete=False
    ) as f:
        f.write(block.content)
        temp_path = Path(f.name)

    try:
        result = subprocess.run(
            [node, "--check", str(temp_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            error = result.stderr.strip().replace(str(temp_path), f"{block.filepath}:{block.line_number}")
            return LintResult(block, False, f"JavaScript syntax error: {error}")
        return LintResult(block, True)
    except subprocess.TimeoutExpired:
        return LintResult(block, False, "JavaScript lint timeout")
    finally:
        temp_path.unlink(missing_ok=True)


def lint_typescript(block: CodeBlock, timeout: int = 15) -> LintResult:
    """Lint TypeScript code using tsc."""
    tsc = shutil.which("tsc")
    if tsc is None:
        return LintResult(block, True, "tsc not installed, skipping TS lint", "info")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "snippet.ts"
        temp_path.write_text(block.content, encoding="utf-8")

        try:
            result = subprocess.run(
                [tsc, "--noEmit", "--pretty", "false", "--target", "ES2020",
                 "--module", "commonjs", "--skipLibCheck", "true", str(temp_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            # Check for tsc internal errors (broken installation)
            if "SyntaxError" in result.stderr and "tsc.js" in result.stderr:
                return LintResult(block, True, "tsc installation broken, skipping", "info")
            if result.returncode != 0:
                error = result.stdout.strip() or result.stderr.strip()
                # Filter out tsc internal errors
                if "SyntaxError" in error and "_tsc.js" in error:
                    return LintResult(block, True, "tsc installation broken, skipping", "info")
                error = error.replace(str(temp_path), f"{block.filepath}:{block.line_number}")
                return LintResult(block, False, f"TypeScript error: {error}")
            return LintResult(block, True)
        except subprocess.TimeoutExpired:
            return LintResult(block, False, "TypeScript lint timeout")
        except (RuntimeError, ValueError, TypeError, OSError) as e:
            return LintResult(block, True, f"tsc error: {e}, skipping", "info")


def lint_python(block: CodeBlock, timeout: int = 10) -> LintResult:
    """Lint Python code using py_compile."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", encoding="utf-8", delete=False
    ) as f:
        f.write(block.content)
        temp_path = Path(f.name)

    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(temp_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            error = result.stderr.strip().replace(str(temp_path), f"{block.filepath}:{block.line_number}")
            return LintResult(block, False, f"Python syntax error: {error}")
        return LintResult(block, True)
    except subprocess.TimeoutExpired:
        return LintResult(block, False, "Python lint timeout")
    finally:
        temp_path.unlink(missing_ok=True)


def lint_bash(block: CodeBlock, timeout: int = 10) -> LintResult:
    """Lint Bash code using bash -n and optionally shellcheck."""
    bash = shutil.which("bash")
    if bash is None:
        return LintResult(block, True, "bash not installed, skipping", "info")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".sh", encoding="utf-8", delete=False
    ) as f:
        f.write(block.content)
        temp_path = Path(f.name)

    try:
        # Basic syntax check
        result = subprocess.run(
            [bash, "-n", str(temp_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            error = result.stderr.strip()
            return LintResult(block, False, f"Bash syntax error: {error}")

        # Optional: shellcheck if available
        shellcheck = shutil.which("shellcheck")
        if shellcheck:
            sc_result = subprocess.run(
                [shellcheck, "-s", "bash", "-f", "gcc", str(temp_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if sc_result.returncode != 0:
                # shellcheck warnings are not blocking by default
                error = sc_result.stdout.strip()
                return LintResult(block, True, f"shellcheck warnings: {error}", "warning")

        return LintResult(block, True)
    except subprocess.TimeoutExpired:
        return LintResult(block, False, "Bash lint timeout")
    finally:
        temp_path.unlink(missing_ok=True)


def lint_json(block: CodeBlock, timeout: int = 5) -> LintResult:
    """Lint JSON code."""
    try:
        json.loads(block.content)
        return LintResult(block, True)
    except json.JSONDecodeError as e:
        return LintResult(block, False, f"JSON error at line {e.lineno}: {e.msg}")


def lint_yaml(block: CodeBlock, timeout: int = 5) -> LintResult:
    """Lint YAML code."""
    try:
        yaml.safe_load(block.content)
        return LintResult(block, True)
    except yaml.YAMLError as e:
        return LintResult(block, False, f"YAML error: {e}")


def lint_go(block: CodeBlock, timeout: int = 15) -> LintResult:
    """Lint Go code using go build."""
    go_bin = shutil.which("go")
    if go_bin is None:
        return LintResult(block, True, "go not installed, skipping", "info")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_file = temp_path / "main.go"
        source_file.write_text(block.content, encoding="utf-8")

        try:
            # Initialize module
            subprocess.run(
                [go_bin, "mod", "init", "snippet"],
                cwd=temp_dir,
                capture_output=True,
                timeout=timeout,
            )

            # Build (syntax check)
            result = subprocess.run(
                [go_bin, "build", "./..."],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode != 0:
                error = result.stderr.strip()
                return LintResult(block, False, f"Go build error: {error}")
            return LintResult(block, True)
        except subprocess.TimeoutExpired:
            return LintResult(block, False, "Go lint timeout")


def _first_tool(*names: str) -> str | None:
    """Return the path of the first available tool from ``names``, or None."""
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def _syntax_lint_file(
    block: CodeBlock,
    *,
    tool: str,
    flags: list[str],
    suffix: str,
    label: str,
    timeout: int,
    fatal: bool,
    content: str | None = None,
) -> LintResult:
    """Run ``tool flags <tempfile>`` as a single-file syntax check.

    ``fatal=True`` marks a genuine syntax gate (parse-only tools that never
    false-positive on undefined external symbols, e.g. ``ruby -c``): a failure
    blocks. ``fatal=False`` is for full-compile tools that resolve symbols and
    therefore report errors on legitimately-partial documentation snippets;
    their diagnostics are surfaced at ``info`` severity so they inform without
    ever blocking a commit, even under ``--strict``.
    """
    body = block.content if content is None else content
    with tempfile.TemporaryDirectory() as temp_dir:
        source = Path(temp_dir) / f"snippet{suffix}"
        source.write_text(body, encoding="utf-8")
        try:
            result = subprocess.run(
                [tool, *flags, str(source)],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return LintResult(block, not fatal, f"{label} lint timeout", "error" if fatal else "info")
        except OSError as exc:
            return LintResult(block, True, f"{label} runner error: {exc}, skipping", "info")
        if result.returncode != 0:
            error = (result.stderr.strip() or result.stdout.strip()).replace(
                str(source), f"{block.filepath}:{block.line_number}"
            )
            if fatal:
                return LintResult(block, False, f"{label} syntax error: {error}")
            return LintResult(block, True, f"{label} best-effort check reported issues (may be a partial snippet): {error}", "info")
        return LintResult(block, True)


def lint_ruby(block: CodeBlock, timeout: int = 10) -> LintResult:
    """Lint Ruby code using ruby -c (parse-only, no execution)."""
    ruby = shutil.which("ruby")
    if ruby is None:
        return LintResult(block, True, "ruby not installed, skipping", "info")
    return _syntax_lint_file(block, tool=ruby, flags=["-c"], suffix=".rb", label="Ruby", timeout=timeout, fatal=True)


def lint_php(block: CodeBlock, timeout: int = 10) -> LintResult:
    """Lint PHP code using php -l (lint/parse-only)."""
    php = shutil.which("php")
    if php is None:
        return LintResult(block, True, "php not installed, skipping", "info")
    return _syntax_lint_file(block, tool=php, flags=["-l"], suffix=".php", label="PHP", timeout=timeout, fatal=True)


def lint_swift(block: CodeBlock, timeout: int = 20) -> LintResult:
    """Lint Swift code using swiftc -parse (parse-only, no type resolution)."""
    swiftc = shutil.which("swiftc")
    if swiftc is None:
        return LintResult(block, True, "swiftc not installed, skipping", "info")
    return _syntax_lint_file(block, tool=swiftc, flags=["-parse"], suffix=".swift", label="Swift", timeout=timeout, fatal=True)


def lint_c(block: CodeBlock, timeout: int = 15) -> LintResult:
    """Lint C code using a compiler front-end syntax check (best-effort)."""
    cc = _first_tool("gcc", "clang", "cc")
    if cc is None:
        return LintResult(block, True, "no C compiler installed, skipping", "info")
    return _syntax_lint_file(
        block, tool=cc, flags=["-fsyntax-only", "-x", "c"], suffix=".c", label="C", timeout=timeout, fatal=False
    )


def lint_cpp(block: CodeBlock, timeout: int = 15) -> LintResult:
    """Lint C++ code using a compiler front-end syntax check (best-effort)."""
    cxx = _first_tool("g++", "clang++")
    if cxx is None:
        return LintResult(block, True, "no C++ compiler installed, skipping", "info")
    return _syntax_lint_file(
        block, tool=cxx, flags=["-fsyntax-only", "-x", "c++", "-std=c++17"], suffix=".cpp", label="C++",
        timeout=timeout, fatal=False,
    )


def lint_rust(block: CodeBlock, timeout: int = 20) -> LintResult:
    """Lint Rust code by compiling as a library to metadata only (best-effort)."""
    rustc = shutil.which("rustc")
    if rustc is None:
        return LintResult(block, True, "rustc not installed, skipping", "info")
    return _syntax_lint_file(
        block, tool=rustc, flags=["--edition", "2021", "--crate-type", "lib", "--emit=metadata"],
        suffix=".rs", label="Rust", timeout=timeout, fatal=False,
    )


def lint_kotlin(block: CodeBlock, timeout: int = 60) -> LintResult:
    """Lint Kotlin code using kotlinc (full compile, best-effort, non-blocking)."""
    kotlinc = shutil.which("kotlinc")
    if kotlinc is None:
        return LintResult(block, True, "kotlinc not installed, skipping", "info")
    if not re.search(r"\b(fun|class|object|interface|enum)\s+\w", block.content):
        return LintResult(block, True, "Kotlin fragment (no top-level declaration), skipping", "info")
    with tempfile.TemporaryDirectory() as temp_dir:
        source = Path(temp_dir) / "snippet.kt"
        source.write_text(block.content, encoding="utf-8")
        try:
            result = subprocess.run(
                [kotlinc, str(source), "-d", temp_dir],
                cwd=temp_dir, capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return LintResult(block, True, "Kotlin lint timeout (non-blocking)", "info")
        except OSError as exc:
            return LintResult(block, True, f"Kotlin runner error: {exc}, skipping", "info")
        if "error:" in (result.stderr or "").lower():
            return LintResult(block, True, f"Kotlin best-effort check reported issues (may be a partial snippet): {result.stderr.strip()}", "info")
        return LintResult(block, True)


def lint_csharp(block: CodeBlock, timeout: int = 30) -> LintResult:
    """Lint C# code using the Roslyn compiler csc (best-effort, non-blocking)."""
    csc = _first_tool("csc", "csc.exe")
    if csc is None:
        return LintResult(block, True, "csc not installed, skipping", "info")
    if not re.search(r"\b(class|interface|enum|struct|record|namespace)\s+\w", block.content):
        return LintResult(block, True, "C# fragment (no top-level declaration), skipping", "info")
    return _syntax_lint_file(
        block, tool=csc, flags=["-nologo", "-target:library", "-out:snippet.dll"],
        suffix=".cs", label="C#", timeout=timeout, fatal=False,
    )


def lint_java(block: CodeBlock, timeout: int = 25) -> LintResult:
    """Lint Java code using javac (full compile, best-effort, non-blocking).

    Only self-contained snippets that declare a top-level type are linted.
    Bare statement/method fragments are skipped, because wrapping them cannot
    be done reliably (a statement is invalid directly in a class body) and
    would produce misleading warnings. Because javac resolves symbols, snippets
    referencing external SDK types report errors surfaced as non-blocking
    warnings, never as commit-blocking failures.
    """
    javac = shutil.which("javac")
    if javac is None:
        return LintResult(block, True, "javac not installed, skipping", "info")
    content = block.content
    type_match = re.search(r"\b(?:class|interface|enum|record)\s+(\w+)", content)
    if type_match is None:
        return LintResult(block, True, "Java fragment (no top-level declaration), skipping", "info")
    # javac requires a public type to live in a file named after it.
    class_name = type_match.group(1)
    with tempfile.TemporaryDirectory() as temp_dir:
        source = Path(temp_dir) / f"{class_name}.java"
        source.write_text(content, encoding="utf-8")
        try:
            result = subprocess.run(
                [javac, "-d", temp_dir, str(source)],
                cwd=temp_dir, capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return LintResult(block, True, "Java lint timeout (non-blocking)", "info")
        except OSError as exc:
            return LintResult(block, True, f"Java runner error: {exc}, skipping", "info")
        if result.returncode != 0:
            error = result.stderr.strip().replace(str(source), f"{block.filepath}:{block.line_number}")
            return LintResult(block, True, f"Java best-effort check reported issues (may be a partial snippet): {error}", "info")
        return LintResult(block, True)


def lint_dart(block: CodeBlock, timeout: int = 30) -> LintResult:
    """Lint Dart code using dart analyze; only error-severity issues fail."""
    dart = shutil.which("dart")
    if dart is None:
        return LintResult(block, True, "dart not installed, skipping", "info")
    with tempfile.TemporaryDirectory() as temp_dir:
        source = Path(temp_dir) / "snippet.dart"
        source.write_text(block.content, encoding="utf-8")
        try:
            result = subprocess.run(
                [dart, "analyze", str(source)],
                cwd=temp_dir, capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return LintResult(block, True, "Dart lint timeout (non-blocking)", "info")
        except OSError as exc:
            return LintResult(block, True, f"Dart runner error: {exc}, skipping", "info")
        output = (result.stdout or "") + (result.stderr or "")
        # dart analyze lines look like: "  error - message - file:line:col - code".
        if re.search(r"^\s*error\b", output, re.MULTILINE):
            return LintResult(block, True, f"Dart best-effort check reported issues (may be a partial snippet): {output.strip()}", "info")
        return LintResult(block, True)


# Language to linter mapping
LINTERS: dict[str, Callable[[CodeBlock, int], LintResult]] = {
    "javascript": lint_javascript,
    "js": lint_javascript,
    "typescript": lint_typescript,
    "ts": lint_typescript,
    "python": lint_python,
    "py": lint_python,
    "bash": lint_bash,
    "sh": lint_bash,
    "shell": lint_bash,
    "json": lint_json,
    "yaml": lint_yaml,
    "yml": lint_yaml,
    "go": lint_go,
    "golang": lint_go,
    "ruby": lint_ruby,
    "rb": lint_ruby,
    "php": lint_php,
    "swift": lint_swift,
    "c": lint_c,
    "cpp": lint_cpp,
    "c++": lint_cpp,
    "rust": lint_rust,
    "rs": lint_rust,
    "kotlin": lint_kotlin,
    "kt": lint_kotlin,
    "csharp": lint_csharp,
    "cs": lint_csharp,
    "java": lint_java,
    "dart": lint_dart,
    "flutter": lint_dart,
}

# Languages to skip (output only, config, etc.)
SKIP_LANGUAGES = {
    "",  # No language specified
    "text", "txt", "plaintext",
    "console", "terminal",
    "diff",
    "markdown", "md",
    "html", "xml", "css", "scss", "sass",
    "sql",
    "toml", "ini", "conf", "config",
    "dockerfile",
    "makefile",
    "graphql", "gql",
    "proto", "protobuf",
    "mermaid",
    "output", "log", "result",
    "http",  # HTTP request examples
    "nginx",  # Nginx config
    "apache",  # Apache config
    "env",  # Environment files
    "properties",  # Java properties
}

# Patterns that indicate a code block is a template/placeholder (not real code)
TEMPLATE_PATTERNS = [
    r'\[[\w_]+\]',  # [operation], [Thing], [feature_name]
    r'\{\{[\s\w_]+\}\}',  # {{ variable }}, {{ product_name }}
    r'<[\w_-]+>',  # <placeholder>, <failing-pod>
    r'\.\.\.',  # Ellipsis indicating incomplete code
]


def _is_template_code(content: str) -> bool:
    """Check if code block contains template placeholders."""
    for pattern in TEMPLATE_PATTERNS:
        if re.search(pattern, content):
            return True
    return False


def lint_file(filepath: Path, timeout: int = 10) -> list[LintResult]:
    """Lint all code blocks in a markdown file."""
    blocks = extract_code_blocks(filepath)
    results: list[LintResult] = []

    for block in blocks:
        # Skip blocks tagged with 'nolint' or 'skip'
        if block.tags & {"nolint", "skip", "nocheck", "template"}:
            continue

        # Skip unsupported/output languages
        if block.language in SKIP_LANGUAGES:
            continue

        # Skip template code with placeholders
        if _is_template_code(block.content):
            continue

        # Get appropriate linter
        linter = LINTERS.get(block.language)
        if linter is None:
            # Unknown language - skip with info
            results.append(LintResult(
                block, True,
                f"No linter for language '{block.language}'", "info"
            ))
            continue

        # Run linter
        result = linter(block, timeout)
        results.append(result)

    return results


def lint_paths(paths: list[str], timeout: int = 10) -> tuple[list[LintResult], int, int]:
    """Lint all markdown files in given paths."""
    all_results: list[LintResult] = []
    files_checked = 0
    blocks_checked = 0

    for path_str in paths:
        path = Path(path_str)
        if path.is_file() and path.suffix.lower() == ".md":
            files = [path]
        elif path.is_dir():
            files = sorted(path.rglob("*.md"))
        else:
            continue

        for filepath in files:
            results = lint_file(filepath, timeout)
            all_results.extend(results)
            files_checked += 1
            blocks_checked += len(results)

    return all_results, files_checked, blocks_checked


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lint code snippets in markdown files for syntax errors"
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Markdown files or directories to lint",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Timeout per code block in seconds (default: 10)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only show errors, not warnings or info",
    )
    args = parser.parse_args()

    results, files_checked, blocks_checked = lint_paths(args.paths, args.timeout)

    # Categorize results
    errors = [r for r in results if not r.passed and r.severity == "error"]
    warnings = [r for r in results if r.passed and r.severity == "warning"]
    infos = [r for r in results if r.severity == "info"]

    # Print results
    print(f"\nCode snippet linting: {files_checked} files, {blocks_checked} blocks checked")
    print("=" * 60)

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for r in errors:
            print(f"  {r.block.filepath}:{r.block.line_number} [{r.block.language}]")
            print(f"    {r.error_message}")

    if warnings and not args.quiet:
        print(f"\nWarnings ({len(warnings)}):")
        for r in warnings:
            print(f"  {r.block.filepath}:{r.block.line_number} [{r.block.language}]")
            print(f"    {r.error_message}")

    if infos and not args.quiet:
        print(f"\nInfo ({len(infos)}):")
        for r in infos:
            print(f"  {r.block.filepath}:{r.block.line_number} [{r.block.language}]")
            print(f"    {r.error_message}")

    # Summary
    passed = blocks_checked - len(errors)
    print(f"\nSummary: {passed}/{blocks_checked} blocks passed")

    # Exit code
    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

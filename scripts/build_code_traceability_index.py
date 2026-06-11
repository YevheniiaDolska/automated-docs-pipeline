#!/usr/bin/env python3
"""Build AST/code-aware traceability index (imports/calls/config deps).

Outputs a JSON artifact that links docs claims to code evidence surfaces.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any


IGNORE_DIRS = {".git", "node_modules", "dist", "build", "coverage", "__pycache__", ".venv", "venv", "reports"}
JS_EXTS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
DEFAULT_SCAN_DIRS = ("scripts", "docsops/scripts", "src", "app", "api")


def _iter_files(root: Path, scan_dirs: list[str], max_files: int) -> list[Path]:
    files: list[Path] = []
    roots: list[Path] = []
    for rel in scan_dirs:
        candidate = (root / rel).resolve()
        if candidate.exists() and candidate.is_dir():
            roots.append(candidate)
    if not roots:
        roots = [root]

    for scan_root in roots:
        for p in scan_root.rglob("*"):
            if not p.is_file():
                continue
            if any(part in IGNORE_DIRS for part in p.parts):
                continue
            if p.suffix.lower() not in {".py", *JS_EXTS}:
                continue
            if p.stat().st_size > 1_000_000:
                continue
            files.append(p)
            if len(files) >= max_files:
                return sorted(files)
    return sorted(files)


def _scan_python(path: Path, repo_root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    imports: list[str] = []
    calls: list[str] = []
    env_vars: list[str] = []
    config_keys: list[str] = []
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return {"file": str(path.relative_to(repo_root)).replace("\\", "/"), "language": "python", "parse_error": True}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                imports.append(f"{mod}.{alias.name}" if mod else alias.name)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
        elif isinstance(node, ast.Subscript):
            # os.environ["VAR"]
            if isinstance(node.value, ast.Attribute) and getattr(node.value, "attr", "") == "environ":
                sl = node.slice
                if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                    env_vars.append(sl.value)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            # os.getenv("VAR") and config.get("key")
            if node.func.attr == "getenv" and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                env_vars.append(node.args[0].value)
            if node.func.attr == "get" and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                config_keys.append(node.args[0].value)

    return {
        "file": str(path.relative_to(repo_root)).replace("\\", "/"),
        "language": "python",
        "imports": sorted(set(imports)),
        "calls": sorted(set(calls)),
        "env_vars": sorted(set(env_vars)),
        "config_keys": sorted(set(config_keys)),
    }


def _scan_js(path: Path, repo_root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    imports = re.findall(r"(?:import\s+.*?from\s+['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+)['\"]\))", text)
    flat_imports = sorted({a or b for a, b in imports if (a or b)})
    calls = sorted(set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", text)))
    env_vars = sorted(set(re.findall(r"process\.env\.([A-Z][A-Z0-9_]+)", text)))
    config_keys = sorted(set(re.findall(r"(?:config|settings)\[['\"]([A-Za-z0-9_.-]+)['\"]\]|(?:config|settings)\.([A-Za-z_][A-Za-z0-9_]*)", text)))
    cfg_flat: list[str] = []
    for a, b in config_keys:
        if a:
            cfg_flat.append(a)
        if b:
            cfg_flat.append(b)

    return {
        "file": str(path.relative_to(repo_root)).replace("\\", "/"),
        "language": "javascript",
        "imports": flat_imports,
        "calls": calls[:400],
        "env_vars": env_vars,
        "config_keys": sorted(set(cfg_flat)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build code-aware traceability index")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default="reports/code_traceability_index.json")
    parser.add_argument("--scan-dirs", default=",".join(DEFAULT_SCAN_DIRS))
    parser.add_argument("--max-files", type=int, default=3000)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output_path = (repo_root / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    scan_dirs = [part.strip() for part in str(args.scan_dirs).split(",") if part.strip()]
    records: list[dict[str, Any]] = []
    for file_path in _iter_files(repo_root, scan_dirs=scan_dirs, max_files=max(1, int(args.max_files))):
        if file_path.suffix.lower() == ".py":
            records.append(_scan_python(file_path, repo_root))
        elif file_path.suffix.lower() in JS_EXTS:
            records.append(_scan_js(file_path, repo_root))

    payload = {
        "schema": "code-traceability-index/v1",
        "summary": {
            "files_indexed": len(records),
            "python_files": sum(1 for r in records if r.get("language") == "python"),
            "js_files": sum(1 for r in records if r.get("language") == "javascript"),
        },
        "records": records,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"[traceability] indexed files={len(records)} -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

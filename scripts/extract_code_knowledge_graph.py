#!/usr/bin/env python3
"""Build AST/code-aware chunks and a dependency graph for code-first RAG.

Outputs:
- docs/assets/code-knowledge-index.json
- docs/assets/code-dependency-graph.json
- reports/code_knowledge_report.json
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_DEFAULT_DIRS = ("packages", "src", "app", "apps", "services", "libs", "sdk")
_INCLUDE_EXTS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".java": "java",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
    ".rs": "rust",
    ".kt": "kotlin",
    ".swift": "swift",
}

_RE_IMPORT_FROM = re.compile(r"^\s*import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
_RE_REQUIRE = re.compile(r"require\(\s*['\"]([^'\"]+)['\"]\s*\)")
_RE_ES_IMPORT = re.compile(r"^\s*import\s+['\"]([^'\"]+)['\"]", re.MULTILINE)
_RE_ENV_JS = re.compile(r"process\.env\.([A-Z0-9_]+)")
_RE_ENV_PY = re.compile(r"os\.environ(?:\.get)?\(\s*['\"]([A-Z0-9_]+)['\"]\s*\)")
_RE_GETENV = re.compile(r"getenv\(\s*['\"]([A-Z0-9_]+)['\"]\s*\)")


@dataclass
class Chunk:
    """One code-aware unit."""

    chunk_id: str
    language: str
    path: str
    symbol: str
    kind: str
    start_line: int
    end_line: int
    signature: str
    text_excerpt: str
    dependencies: list[str]
    config_keys: list[str]

    def as_dict(self) -> dict[str, Any]:
        """Serialize chunk."""
        return {
            "id": self.chunk_id,
            "language": self.language,
            "path": self.path,
            "symbol": self.symbol,
            "kind": self.kind,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "signature": self.signature,
            "text_excerpt": self.text_excerpt,
            "dependencies": self.dependencies,
            "config_keys": self.config_keys,
        }


def _sha(text: str) -> str:
    """Stable hash."""
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _safe_read(path: Path) -> str:
    """Read text safely."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _iter_source_files(repo_root: Path, include_dirs: list[str], max_files: int) -> list[Path]:
    """Collect candidate source files."""
    roots: list[Path] = []
    for item in include_dirs:
        candidate = (repo_root / item).resolve()
        if candidate.exists() and candidate.is_dir():
            roots.append(candidate)
    if not roots:
        roots = [repo_root]
    files: list[Path] = []
    for root in roots:
        for p in root.rglob("*"):
            if len(files) >= max_files:
                return files
            if not p.is_file():
                continue
            if p.suffix.lower() not in _INCLUDE_EXTS:
                continue
            rel = p.relative_to(repo_root).as_posix()
            if rel.startswith(("node_modules/", ".git/", "venv/", ".venv/", "dist/", "build/", "generated/")):
                continue
            files.append(p)
    return files


def _py_signature(node: ast.AST, name: str) -> str:
    """Render lightweight Python signature."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        args = [arg.arg for arg in node.args.args]
        return f"{name}({', '.join(args)})"
    if isinstance(node, ast.ClassDef):
        return f"class {name}"
    return name


def _extract_py_chunks(rel: str, text: str) -> tuple[list[Chunk], set[str], set[str], list[dict[str, str]]]:
    """Extract Python AST chunks and dependency edges."""
    chunks: list[Chunk] = []
    imports: set[str] = set()
    config_keys: set[str] = set(_RE_ENV_PY.findall(text)) | set(_RE_GETENV.findall(text))
    edges: list[dict[str, str]] = []

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return chunks, imports, config_keys, edges

    lines = text.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
                edges.append({"type": "import", "source": rel, "target": alias.name})
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module:
                imports.add(module)
                edges.append({"type": "import", "source": rel, "target": module})

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        name = str(getattr(node, "name", "")).strip()
        if not name:
            continue
        start = int(getattr(node, "lineno", 1))
        end = int(getattr(node, "end_lineno", start))
        snippet = "\n".join(lines[start - 1 : min(end, start + 80)])
        deps: set[str] = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func = child.func
                if isinstance(func, ast.Name):
                    deps.add(func.id)
                elif isinstance(func, ast.Attribute):
                    deps.add(func.attr)
        chunk_id = f"code-{_sha(f'{rel}:{name}:{start}:{end}')}"
        chunk = Chunk(
            chunk_id=chunk_id,
            language="python",
            path=rel,
            symbol=name,
            kind="class" if isinstance(node, ast.ClassDef) else "function",
            start_line=start,
            end_line=end,
            signature=_py_signature(node, name),
            text_excerpt=snippet[:6000],
            dependencies=sorted(deps)[:200],
            config_keys=sorted(config_keys)[:200],
        )
        chunks.append(chunk)
        edges.append({"type": "defines", "source": rel, "target": f"{rel}::{name}"})
        for dep in sorted(deps)[:200]:
            edges.append({"type": "calls", "source": f"{rel}::{name}", "target": dep})

    return chunks, imports, config_keys, edges


def _extract_generic(rel: str, language: str, text: str) -> tuple[list[Chunk], set[str], set[str], list[dict[str, str]]]:
    """Extract coarse chunks/dependencies for non-Python files."""
    imports: set[str] = set()
    imports.update(_RE_IMPORT_FROM.findall(text))
    imports.update(_RE_REQUIRE.findall(text))
    imports.update(_RE_ES_IMPORT.findall(text))
    config_keys: set[str] = set(_RE_ENV_JS.findall(text)) | set(_RE_GETENV.findall(text))
    edges: list[dict[str, str]] = [{"type": "import", "source": rel, "target": mod} for mod in sorted(imports)[:300]]

    lines = text.splitlines()
    chunks: list[Chunk] = []
    block_start = 1
    block_size = 120
    chunk_count = 0
    while block_start <= len(lines) and chunk_count < 30:
        block_end = min(len(lines), block_start + block_size - 1)
        snippet = "\n".join(lines[block_start - 1 : block_end])
        symbol = f"block_{chunk_count + 1}"
        chunk_id = f"code-{_sha(f'{rel}:{symbol}:{block_start}:{block_end}')}"
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                language=language,
                path=rel,
                symbol=symbol,
                kind="block",
                start_line=block_start,
                end_line=block_end,
                signature=symbol,
                text_excerpt=snippet[:6000],
                dependencies=sorted(imports)[:200],
                config_keys=sorted(config_keys)[:200],
            )
        )
        chunk_count += 1
        block_start = block_end + 1

    return chunks, imports, config_keys, edges


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(description="Build AST/code-aware knowledge index and dependency graph")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default="docs/assets/code-knowledge-index.json")
    parser.add_argument("--graph-output", default="docs/assets/code-dependency-graph.json")
    parser.add_argument("--report", default="reports/code_knowledge_report.json")
    parser.add_argument("--include-dirs", default=",".join(_DEFAULT_DIRS))
    parser.add_argument("--max-files", type=int, default=3000)
    return parser.parse_args()


def main() -> int:
    """Run extraction."""
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    include_dirs = [x.strip() for x in str(args.include_dirs).split(",") if x.strip()]
    files = _iter_source_files(repo_root, include_dirs, max(1, int(args.max_files)))

    chunks: list[Chunk] = []
    nodes: set[str] = set()
    edges: list[dict[str, str]] = []
    language_counts: dict[str, int] = {}
    import_edges = 0
    call_edges = 0
    config_refs = 0

    for path in files:
        rel = path.relative_to(repo_root).as_posix()
        language = _INCLUDE_EXTS.get(path.suffix.lower(), "unknown")
        language_counts[language] = int(language_counts.get(language, 0)) + 1
        nodes.add(rel)
        text = _safe_read(path)
        if language == "python":
            file_chunks, imports, cfg_keys, file_edges = _extract_py_chunks(rel, text)
        else:
            file_chunks, imports, cfg_keys, file_edges = _extract_generic(rel, language, text)
        chunks.extend(file_chunks)
        for dep in sorted(imports)[:300]:
            nodes.add(dep)
        for edge in file_edges:
            edges.append(edge)
            if edge["type"] == "import":
                import_edges += 1
            elif edge["type"] == "calls":
                call_edges += 1
        config_refs += len(cfg_keys)
        for key in sorted(cfg_keys)[:200]:
            nodes.add(f"config:{key}")
            edges.append({"type": "config_dep", "source": rel, "target": f"config:{key}"})

    chunk_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "files_scanned": len(files),
        "chunks": [chunk.as_dict() for chunk in chunks],
    }
    graph_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "nodes": [{"id": node} for node in sorted(nodes)],
        "edges": edges,
    }
    report_payload = {
        "ok": True,
        "files_scanned": len(files),
        "chunks": len(chunks),
        "nodes": len(nodes),
        "edges": len(edges),
        "import_edges": int(import_edges),
        "call_edges": int(call_edges),
        "config_refs": int(config_refs),
        "languages": language_counts,
        "output": str((repo_root / args.output).resolve()),
        "graph_output": str((repo_root / args.graph_output).resolve()),
    }

    _write_json((repo_root / args.output).resolve(), chunk_payload)
    _write_json((repo_root / args.graph_output).resolve(), graph_payload)
    _write_json((repo_root / args.report).resolve(), report_payload)
    print(
        "[code-knowledge] files={} chunks={} nodes={} edges={}".format(
            len(files), len(chunks), len(nodes), len(edges)
        )
    )
    print(f"[code-knowledge] output={(repo_root / args.output).resolve()}")
    print(f"[code-knowledge] graph={(repo_root / args.graph_output).resolve()}")
    print(f"[code-knowledge] report={(repo_root / args.report).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

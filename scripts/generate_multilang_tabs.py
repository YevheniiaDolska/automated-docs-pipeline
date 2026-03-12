#!/usr/bin/env python3
"""Generate tabbed cURL/JavaScript/Python examples from standalone cURL blocks."""

from __future__ import annotations

import argparse
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CurlRequest:
    method: str
    url: str
    headers: dict[str, str]
    data: str | None


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


def _is_api_like_doc(path: Path) -> bool:
    p = path.as_posix().lower()
    name = path.name.lower()
    return ("api" in name) or ("openapi" in p) or ("playground" in name) or ("/reference/" in p and "api" in p)


def _parse_curl_block(content: str) -> CurlRequest | None:
    merged = " ".join(line.rstrip("\\").strip() for line in content.splitlines() if line.strip())
    if "curl " not in merged and not merged.strip().startswith("curl"):
        return None
    try:
        tokens = shlex.split(merged)
    except ValueError:
        return None
    if not tokens or tokens[0] != "curl":
        return None

    method = "GET"
    url = ""
    headers: dict[str, str] = {}
    data: str | None = None
    idx = 1
    while idx < len(tokens):
        token = tokens[idx]
        if token in {"-X", "--request"} and idx + 1 < len(tokens):
            method = tokens[idx + 1].upper()
            idx += 2
            continue
        if token in {"-H", "--header"} and idx + 1 < len(tokens):
            raw_header = tokens[idx + 1]
            if ":" in raw_header:
                key, value = raw_header.split(":", 1)
                headers[key.strip()] = value.strip()
            idx += 2
            continue
        if token in {"-d", "--data", "--data-raw", "--data-binary"} and idx + 1 < len(tokens):
            data = tokens[idx + 1]
            idx += 2
            continue
        if token.startswith("http://") or token.startswith("https://"):
            url = token
        idx += 1

    if not url:
        return None
    return CurlRequest(method=method, url=url, headers=headers, data=data)


def _py_literal(obj: Any) -> str:
    if obj is None:
        return "None"
    if isinstance(obj, str):
        return repr(obj)
    if isinstance(obj, dict):
        inner = ", ".join(f"{repr(k)}: {repr(v)}" for k, v in obj.items())
        return "{" + inner + "}"
    return repr(obj)


def _render_tabs(curl_source: str, req: CurlRequest) -> str:
    js_headers = "{\n" + "\n".join(f"      {repr(k)}: {repr(v)}," for k, v in req.headers.items()) + ("\n    }" if req.headers else "}")
    js_data = f"\n    body: JSON.stringify({req.data})," if req.data else ""
    py_headers = _py_literal(req.headers if req.headers else {})
    py_data = f"\n    json={_py_literal(req.data)}," if req.data else ""

    return (
        '=== "cURL"\n\n'
        "    ```bash smoke\n"
        + "\n".join(f"    {line}" for line in curl_source.splitlines())
        + "\n    ```\n\n"
        '=== "JavaScript"\n\n'
        "    ```javascript smoke\n"
        f"    const response = await fetch({req.url!r}, {{\n"
        f"      method: {req.method!r},\n"
        f"      headers: {js_headers},{js_data}\n"
        "    });\n"
        "    const payload = await response.json();\n"
        "    console.log(payload);\n"
        "    ```\n\n"
        '=== "Python"\n\n'
        "    ```python smoke\n"
        "    import requests\n\n"
        f"    response = requests.request(\n"
        f"        {req.method!r},\n"
        f"        {req.url!r},\n"
        f"        headers={py_headers},{py_data}\n"
        "        timeout=30,\n"
        "    )\n"
        "    response.raise_for_status()\n"
        "    print(response.json())\n"
        "    ```"
    )


def transform_markdown(text: str, *, scope: str, file_path: Path) -> tuple[str, int]:
    lines = text.splitlines()
    out: list[str] = []
    idx = 0
    changed = 0
    while idx < len(lines):
        line = lines[idx]
        if line.startswith("```") and not line.startswith("    ```"):
            info = line[3:].strip().lower()
            if info in {"curl", "bash", "shell", "sh"} and (scope == "all" or _is_api_like_doc(file_path)):
                start = idx + 1
                idx += 1
                block: list[str] = []
                while idx < len(lines) and lines[idx].strip() != "```":
                    block.append(lines[idx])
                    idx += 1
                if idx < len(lines) and lines[idx].strip() == "```":
                    req = _parse_curl_block("\n".join(block))
                    if req is not None:
                        out.append(_render_tabs("\n".join(block), req))
                        changed += 1
                        idx += 1
                        continue
                out.append(line)
                out.extend(block)
                if idx < len(lines):
                    out.append(lines[idx])
                    idx += 1
                continue
        out.append(line)
        idx += 1
    return "\n".join(out).rstrip() + "\n", changed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate multi-language tabs from cURL blocks")
    parser.add_argument("--paths", nargs="+", default=["docs", "templates"], help="Markdown files or directories")
    parser.add_argument("--scope", choices=["api", "all"], default="all")
    parser.add_argument("--write", action="store_true", help="Write updates to files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    files = _iter_markdown_files(args.paths)
    total = 0
    touched = 0
    for path in files:
        original = path.read_text(encoding="utf-8")
        updated, changed = transform_markdown(original, scope=args.scope, file_path=path)
        if changed == 0:
            continue
        total += changed
        if args.write:
            path.write_text(updated, encoding="utf-8")
            touched += 1

    mode = "write" if args.write else "dry-run"
    print(f"Multi-language tabs generator ({mode}): files={len(files)} blocks={total} touched={touched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

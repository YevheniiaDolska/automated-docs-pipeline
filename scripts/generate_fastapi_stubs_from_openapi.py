#!/usr/bin/env python3
"""Generate FastAPI endpoint stubs from an OpenAPI spec."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml

HTTP_METHODS = ("get", "post", "put", "patch", "delete", "options", "head")


def load_spec(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _resolve_ref_file(base_spec: Path, ref: str) -> tuple[Path, str]:
    file_ref, _, fragment = ref.partition("#")
    target_file = (base_spec.parent / file_ref).resolve()
    return target_file, fragment


def _walk_fragment(data: Any, fragment: str) -> Any:
    if not fragment:
        return data
    current = data
    pointer = fragment.lstrip("/")
    for raw_token in pointer.split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        current = current[token]
    return current


def resolve_paths(spec: dict[str, Any], spec_path: Path) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    for path_name, path_item in (spec.get("paths") or {}).items():
        if isinstance(path_item, dict) and "$ref" in path_item:
            target_file, fragment = _resolve_ref_file(spec_path, path_item["$ref"])
            target_data = yaml.safe_load(target_file.read_text(encoding="utf-8")) or {}
            resolved[path_name] = _walk_fragment(target_data, fragment)
        else:
            resolved[path_name] = path_item
    return resolved


def to_python_path(path: str) -> str:
    return re.sub(r"\{([^}]+)\}", r"{\1}", path)


def to_args(path: str) -> str:
    names = re.findall(r"\{([^}]+)\}", path)
    if not names:
        return "request: Request"
    typed = ", ".join(f"{name}: str" for name in names)
    return f"{typed}, request: Request"


def fallback_operation_id(method: str, path: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", path).strip("_")
    return f"{method}_{slug}".lower()


def build_app_source(spec: dict[str, Any], spec_path: Path) -> str:
    lines: list[str] = []
    lines.extend(
        [
            "from fastapi import FastAPI, Request",
            "from fastapi.responses import JSONResponse",
            "",
            f"app = FastAPI(title={spec.get('info', {}).get('title', 'Generated API')!r})",
            "",
            "",
            "def _not_implemented(operation_id: str, request_id: str | None) -> JSONResponse:",
            "    return JSONResponse(",
            "        status_code=501,",
            "        content={",
            "            'error': {",
            "                'code': 'not_implemented',",
            "                'message': f'Business logic for {operation_id} is not implemented yet.',",
            "            },",
            "            'request_id': request_id or 'generated-request-id',",
            "        },",
            "    )",
            "",
        ]
    )

    for path, path_item in resolve_paths(spec, spec_path).items():
        if not isinstance(path_item, dict):
            continue
        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId") or fallback_operation_id(method, path)
            description = operation.get("description", "")
            args = to_args(path)
            decorator = f"@app.{method}({to_python_path(path)!r}, summary={operation.get('summary', operation_id)!r})"
            lines.append(decorator)
            lines.append(f"async def {operation_id}({args}):")
            if description:
                lines.append(f"    \"\"\"{description}\"\"\"")
            lines.append("    request_id = request.headers.get('X-Request-Id')")
            lines.append(f"    return _not_implemented({operation_id!r}, request_id)")
            lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate FastAPI stubs from OpenAPI")
    parser.add_argument("--spec", required=True, help="Path to OpenAPI spec")
    parser.add_argument("--output", required=True, help="Output path for generated app file")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    out_path = Path(args.output)

    if not spec_path.exists():
        print(f"Spec file does not exist: {spec_path}")
        return 2

    spec = load_spec(spec_path)
    source = build_app_source(spec, spec_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(source, encoding="utf-8")

    print(f"Generated FastAPI stubs: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

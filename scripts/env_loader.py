#!/usr/bin/env python3
"""Lightweight local .env loader for docs-ops entrypoints."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


def _parse_line(raw: str) -> tuple[str, str] | None:
    line = raw.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith("export "):
        line = line[len("export ") :].strip()
    if "=" not in line:
        return None
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not key:
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    return key, value


def load_local_env(
    repo_root: Path,
    *,
    filenames: Iterable[str] = (".env", ".env.local", ".env.docsops.local"),
    override: bool = False,
) -> list[Path]:
    """Load env vars from local files if present.

    The loader is intentionally minimal to avoid external dependencies.
    Existing environment variables are preserved unless ``override=True``.
    """
    loaded: list[Path] = []
    for name in filenames:
        path = repo_root / name
        if not path.exists() or not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            parsed = _parse_line(raw)
            if not parsed:
                continue
            key, value = parsed
            if override or key not in os.environ:
                os.environ[key] = value
        loaded.append(path)
    return loaded


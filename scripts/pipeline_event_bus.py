#!/usr/bin/env python3
"""Shared pipeline event bus writer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _iso_now() -> str:
    """Internal helper for `_iso_now`."""
    return datetime.now(timezone.utc).isoformat()


def emit_event(
    *,
    repo_root: Path,
    event: str,
    stage: str | None = None,
    status: str = "info",
    payload: dict[str, Any] | None = None,
    log_path: str = "reports/pipeline_events.ndjson",
) -> None:
    """Append one structured event record to NDJSON log."""
    target = (repo_root / log_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    row: dict[str, Any] = {
        "timestamp": _iso_now(),
        "event": str(event).strip(),
        "status": str(status).strip() or "info",
    }
    if stage:
        row["stage"] = str(stage).strip()
    if payload:
        row["payload"] = payload
    with target.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=True) + "\n")


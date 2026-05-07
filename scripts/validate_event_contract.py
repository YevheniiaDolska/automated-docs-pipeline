#!/usr/bin/env python3
"""Validate pipeline event log against required event contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def _read_yaml(path: Path) -> dict[str, Any]:
    """Internal helper for `_read_yaml`."""
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _load_events(path: Path) -> list[dict[str, Any]]:
    """Internal helper for `_load_events`."""
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            row = json.loads(text)
        except (RuntimeError, ValueError, TypeError):
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def parse_args() -> argparse.Namespace:
    """Execute `parse_args` workflow."""
    parser = argparse.ArgumentParser(description="Validate required pipeline events")
    parser.add_argument("--events-log", default="reports/pipeline_events.ndjson")
    parser.add_argument("--contract", default="config/event_contract.yml")
    parser.add_argument("--output", default="reports/event_contract_validation_report.json")
    return parser.parse_args()


def main() -> int:
    """Execute `main` workflow."""
    args = parse_args()
    repo_root = Path.cwd()
    events_path = (repo_root / args.events_log).resolve()
    contract_path = (repo_root / args.contract).resolve()
    output_path = (repo_root / args.output).resolve()

    contract = _read_yaml(contract_path)
    required_events = [str(x).strip() for x in contract.get("required_events", []) if str(x).strip()]
    required_statuses = [str(x).strip() for x in contract.get("required_statuses", []) if str(x).strip()]
    rows = _load_events(events_path)

    seen_events = {str(row.get("event", "")).strip() for row in rows}
    seen_statuses = {str(row.get("status", "")).strip() for row in rows}
    missing_events = sorted(ev for ev in required_events if ev not in seen_events)
    missing_statuses = sorted(st for st in required_statuses if st not in seen_statuses)

    stage_started = sum(1 for row in rows if str(row.get("event", "")).strip() == "stage_started")
    stage_finished = sum(1 for row in rows if str(row.get("event", "")).strip() == "stage_finished")
    stage_balance_ok = stage_started == stage_finished and stage_started > 0

    ok = len(missing_events) == 0 and len(missing_statuses) == 0 and stage_balance_ok
    report = {
        "ok": ok,
        "events_log": str(events_path),
        "contract": str(contract_path),
        "total_events": len(rows),
        "required_events_count": len(required_events),
        "missing_events": missing_events,
        "required_statuses_count": len(required_statuses),
        "missing_statuses": missing_statuses,
        "stage_counts": {
            "started": stage_started,
            "finished": stage_finished,
            "balanced": stage_balance_ok,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"[event-contract] ok={ok} events={len(rows)} missing_events={len(missing_events)}")
    print(f"[event-contract] report={output_path}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

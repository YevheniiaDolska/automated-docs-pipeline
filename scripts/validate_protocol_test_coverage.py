#!/usr/bin/env python3
"""Validate non-REST protocol test-asset depth/coverage."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


REQUIRED_CHECKS = {
    "graphql": {"positive", "negative", "auth", "security-injection", "performance-latency"},
    "grpc": {"positive", "status-codes", "deadline-retry", "security-authz", "performance-latency"},
    "asyncapi": {"publish", "invalid-payload", "ordering-idempotency", "security-signature", "performance-throughput"},
    "websocket": {"publish", "invalid-payload", "ordering-idempotency", "security-authz", "performance-concurrency"},
}


def _normalize_check(value: str) -> str:
    return str(value or "").strip().lower()


def validate(cases: list[dict]) -> list[str]:
    errors: list[str] = []
    by_protocol_entity: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))

    for case in cases:
        protocol = str(case.get("protocol", "")).strip().lower()
        entity = str(case.get("entity", "")).strip() or "<unknown>"
        check = _normalize_check(str(case.get("check_type", "")))
        if protocol in REQUIRED_CHECKS and check:
            by_protocol_entity[protocol][entity].add(check)

    for protocol, entities in by_protocol_entity.items():
        required = REQUIRED_CHECKS.get(protocol, set())
        for entity, checks in entities.items():
            missing = sorted(required - checks)
            if missing:
                errors.append(f"{protocol}:{entity} missing check_types: {', '.join(missing)}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate protocol test asset coverage")
    parser.add_argument("--cases-json", required=True)
    parser.add_argument("--report", default="")
    args = parser.parse_args()

    cases_path = Path(args.cases_json)
    if not cases_path.exists():
        raise FileNotFoundError(f"cases json not found: {cases_path}")

    payload = json.loads(cases_path.read_text(encoding="utf-8"))
    cases = payload.get("cases", []) if isinstance(payload, dict) else []
    if not isinstance(cases, list):
        raise ValueError("`cases` must be a list")

    errors = validate([c for c in cases if isinstance(c, dict)])

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "ok": not bool(errors),
            "errors": errors,
            "cases": len(cases),
        }
        report_path.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    if errors:
        for err in errors:
            print(f"[protocol-coverage] {err}")
        return 1

    print("[protocol-coverage] ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

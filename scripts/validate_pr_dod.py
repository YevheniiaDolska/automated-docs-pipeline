#!/usr/bin/env python3
"""Validate PR-level Definition of Done contract from GitHub event payload."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

UPDATED_BOX = re.compile(r"-\s*\[(x|X)\]\s*I updated documentation affected by this PR\.")
NOT_NEEDED_BOX = re.compile(r"-\s*\[(x|X)\]\s*Documentation updates are not needed\.")
REASON_LINE = re.compile(r"Reason\s*:\s*(.+)", re.IGNORECASE)


def _load_body(event_path: Path) -> str:
    data = json.loads(event_path.read_text(encoding="utf-8"))
    pull_request = data.get("pull_request", {})
    body = pull_request.get("body")
    if not isinstance(body, str):
        return ""
    return body


def validate_dod(body: str) -> tuple[bool, str]:
    has_updated = bool(UPDATED_BOX.search(body))
    has_not_needed = bool(NOT_NEEDED_BOX.search(body))

    if not has_updated and not has_not_needed:
        return False, "DoD contract is incomplete: select one checkbox in the PR template."

    if has_updated and has_not_needed:
        return False, "DoD contract is invalid: select only one of the two documentation options."

    if has_not_needed:
        reason_match = REASON_LINE.search(body)
        if reason_match is None:
            return False, "DoD contract is incomplete: provide a reason for 'docs not needed'."
        reason_text = reason_match.group(1).strip()
        if len(reason_text) < 10:
            return False, "DoD contract reason is too short: provide a concrete explanation."

    return True, "DoD contract validation passed."


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PR DoD contract")
    parser.add_argument("--event-path", required=True, help="Path to GitHub event JSON")
    args = parser.parse_args()

    body = _load_body(Path(args.event_path))
    ok, message = validate_dod(body)

    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

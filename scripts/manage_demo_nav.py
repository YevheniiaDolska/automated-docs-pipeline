#!/usr/bin/env python3
"""Add or remove API-first demo pages in mkdocs nav."""

from __future__ import annotations

import argparse
from pathlib import Path


HOWTO_LINE = "  - Run API-first production flow: how-to/run-api-first-production-flow.md\n"
REF_LINES = [
    "  - TaskStream API playground: reference/taskstream-api-playground.md\n",
    "  - TaskStream API planning notes: reference/taskstream-planning-notes.md\n",
]


def add_lines(lines: list[str]) -> list[str]:
    out = lines[:]

    if HOWTO_LINE not in out:
        for i, line in enumerate(out):
            if line.strip() == "- Configure Webhook triggers: how-to/configure-webhook-trigger.md":
                out.insert(i + 1, HOWTO_LINE)
                break

    for ref_line in REF_LINES:
        if ref_line in out:
            continue
        for i, line in enumerate(out):
            if line.strip() == "- API playground: reference/api-playground.md":
                out.insert(i + 1, ref_line)
                break

    return out


def remove_lines(lines: list[str]) -> list[str]:
    blacklist = {HOWTO_LINE, *REF_LINES}
    return [line for line in lines if line not in blacklist]


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage demo nav entries in mkdocs.yml")
    parser.add_argument("--mode", choices=["add", "remove"], required=True)
    parser.add_argument("--mkdocs", default="mkdocs.yml")
    args = parser.parse_args()

    mkdocs_path = Path(args.mkdocs)
    lines = mkdocs_path.read_text(encoding="utf-8").splitlines(keepends=True)

    if args.mode == "add":
        updated = add_lines(lines)
    else:
        updated = remove_lines(lines)

    mkdocs_path.write_text("".join(updated), encoding="utf-8")
    print(f"mkdocs nav updated ({args.mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

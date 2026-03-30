#!/usr/bin/env python3
"""Interactive client-side wizard to create .env.docsops.local from template.

Run from client repository root after unpacking docsops bundle:
    python3 docsops/scripts/setup_client_env_wizard.py
"""

from __future__ import annotations

from pathlib import Path


ENV_FILE = ".env.docsops.local"
TEMPLATE_FILE = ".env.docsops.local.template"


def _parse_template(template_path: Path) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    pending_comment = ""
    for raw in template_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            pending_comment = line.lstrip("#").strip()
            continue
        if "=" not in line:
            continue
        key, default = line.split("=", 1)
        key = key.strip()
        default = default.strip()
        if not key:
            continue
        items.append((key, pending_comment or default))
        pending_comment = ""
    return items


def _read_existing(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def _write_env(path: Path, values: dict[str, str]) -> None:
    lines = [f"{k}={v}" for k, v in sorted(values.items()) if k]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    repo_root = Path(".").resolve()
    template_path = repo_root / TEMPLATE_FILE
    env_path = repo_root / ENV_FILE

    if not template_path.exists():
        print(f"[env-wizard] template not found: {template_path}")
        return 2

    items = _parse_template(template_path)
    if not items:
        print("[env-wizard] no keys found in template")
        return 0

    print("Client secrets wizard")
    print(f"- Source template: {template_path.name}")
    print(f"- Output file: {env_path.name}")
    print("- Press Enter to keep current/default value.\n")

    values = _read_existing(env_path)
    for key, hint in items:
        current = values.get(key, "")
        suffix = f" [{current}]" if current else ""
        prompt = f"{key} ({hint}){suffix}: "
        entered = input(prompt).strip()
        if entered:
            values[key] = entered
        elif key not in values:
            values[key] = ""

    _write_env(env_path, values)
    print(f"\n[env-wizard] wrote {env_path}")
    print("[env-wizard] next: run docsops/ops/run_weekly_docsops.sh (or .ps1)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build a full unlicensed enterprise client bundle.

This helper keeps the normal bundle build path, but preconfigures:
- enterprise feature profile
- no JWT/capability auto-generation
- local dev override in .env template (VERIOPS_LICENSE_PLAN=enterprise)
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_client_bundle import create_bundle, read_yaml, write_yaml


def _resolve_profile(path_raw: str) -> Path:
    path = Path(path_raw)
    if not path.is_absolute():
        path = (REPO_ROOT / path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Client profile not found: {path}")
    return path


def _override_profile_for_free_enterprise(profile: dict[str, Any], output_dir: str) -> dict[str, Any]:
    updated = dict(profile)
    client = updated.setdefault("client", {})
    if not isinstance(client, dict):
        raise ValueError("client section must be a mapping")
    client_id = str(client.get("id", "")).strip()
    if not client_id:
        raise ValueError("client.id is required")

    bundle = updated.setdefault("bundle", {})
    if not isinstance(bundle, dict):
        raise ValueError("bundle section must be a mapping")
    bundle["output_dir"] = output_dir

    licensing = updated.setdefault("licensing", {})
    if not isinstance(licensing, dict):
        raise ValueError("licensing section must be a mapping")
    licensing["plan"] = "enterprise"
    licensing["days"] = int(licensing.get("days", 30))
    licensing["auto_generate_capability_pack"] = False
    licensing["license_key"] = ""

    return updated


def _set_unlicensed_enterprise_env(bundle_root: Path) -> None:
    env_template = bundle_root / ".env.docsops.local.template"
    if not env_template.exists():
        raise FileNotFoundError(f"Env template missing in bundle: {env_template}")

    lines = env_template.read_text(encoding="utf-8").splitlines()
    out_lines: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith("VERIOPS_LICENSE_PLAN="):
            out_lines.append("VERIOPS_LICENSE_PLAN=enterprise")
            replaced = True
            continue
        out_lines.append(line)
    if not replaced:
        out_lines.append("VERIOPS_LICENSE_PLAN=enterprise")

    out_lines.append("")
    out_lines.append("# NOTE: Unlicensed enterprise bundle (full feature path via VERIOPS_LICENSE_PLAN override).")
    out_lines.append("# Replace VERIOPS_LICENSE_PLAN with signed JWT when switching to production licensing.")
    env_template.write_text("\n".join(out_lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build full unlicensed enterprise bundle without JWT license")
    parser.add_argument("--client", required=True, help="Path to *.client.yml (relative to repo or absolute)")
    parser.add_argument(
        "--output-dir",
        default="generated/client_bundles_free",
        help="Output root directory for generated free bundles",
    )
    args = parser.parse_args()

    profile_path = _resolve_profile(args.client)
    profile = read_yaml(profile_path)
    patched = _override_profile_for_free_enterprise(profile, args.output_dir)

    with tempfile.TemporaryDirectory(prefix="free-enterprise-profile-") as temp_dir:
        temp_profile = Path(temp_dir) / profile_path.name
        write_yaml(temp_profile, patched)
        bundle_root = create_bundle(temp_profile)

    _set_unlicensed_enterprise_env(bundle_root)
    print(f"[ok] unlicensed enterprise bundle created: {bundle_root}")
    print("[note] For production licensing, switch from plan override to signed JWT + capability pack.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

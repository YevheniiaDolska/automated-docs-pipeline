#!/usr/bin/env python3
"""Build an offline renewal bundle for strict-local clients.

Produces a handoff archive with:
- docsops/license.jwt
- optional docsops/.capability_pack.enc
- README_RENEWAL.md (3-step client instructions)
- renewal_manifest.json

Default output:
  generated/offline_renewals/renewal-<client_id>-<YYYYMMDD>.zip
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> None:
    completed = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()
        details = "\n".join(x for x in [stdout, stderr] if x)
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{details}".strip())


def _write_readme(path: Path, *, client_id: str, includes_pack: bool) -> None:
    pack_line = "and `docsops/.capability_pack.enc`" if includes_pack else "(no capability pack update in this renewal)"
    content = (
        "# Offline renewal package\n\n"
        "This package updates your local license for strict-local operation.\n\n"
        "## Apply in 3 steps\n\n"
        "1. Extract this archive at your repository root (the directory that contains `docsops/`).\n"
        "2. Replace `docsops/license.jwt` "
        f"{pack_line}.\n"
        "3. Run one check:\n\n"
        "```bash\n"
        "python3 docsops/scripts/license_gate.py --json\n"
        "```\n\n"
        "If validation succeeds, continue normal weekly/autopipeline runs.\n\n"
        f"- Client: `{client_id}`\n"
        f"- Generated at: `{dt.datetime.now(dt.timezone.utc).isoformat()}`\n"
    )
    path.write_text(content, encoding="utf-8")


def _create_archive(source_dir: Path, output_path: Path, archive_format: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if archive_format == "zip":
        with zipfile.ZipFile(output_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for file_path in sorted(source_dir.rglob("*")):
                if file_path.is_file():
                    zf.write(file_path, file_path.relative_to(source_dir))
        return
    if archive_format == "tar.gz":
        with tarfile.open(output_path, mode="w:gz") as tf:
            for file_path in sorted(source_dir.rglob("*")):
                tf.add(file_path, file_path.relative_to(source_dir))
        return
    raise ValueError(f"Unsupported archive format: {archive_format}")


def build_bundle(args: argparse.Namespace) -> Path:
    client_id = args.client_id.strip()
    if not client_id:
        raise ValueError("--client-id cannot be empty")
    tenant_id = (args.tenant_id or client_id).strip()
    company_domain = args.company_domain.strip().lower()
    plan = args.plan.strip().lower()
    days = int(args.days)
    with_pack = bool(args.with_pack)
    output_dir = Path(args.output_dir).resolve()

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    ext = "zip" if args.format == "zip" else "tar.gz"
    filename = args.filename or f"renewal-{client_id}-{stamp}.{ext}"
    output_path = output_dir / filename

    with tempfile.TemporaryDirectory(prefix="renewal_bundle_") as tmp:
        tmp_dir = Path(tmp)
        docsops_dir = tmp_dir / "docsops"
        docsops_dir.mkdir(parents=True, exist_ok=True)

        jwt_out = docsops_dir / "license.jwt"
        if args.license_jwt_path:
            src = Path(args.license_jwt_path).resolve()
            if not src.exists():
                raise FileNotFoundError(f"--license-jwt-path not found: {src}")
            shutil.copy2(src, jwt_out)
        else:
            license_cmd = [
                sys.executable,
                str(REPO_ROOT / "build" / "generate_license.py"),
                "--client-id",
                client_id,
                "--plan",
                plan,
                "--days",
                str(days),
                "--tenant-id",
                tenant_id,
                "--company-domain",
                company_domain,
                "--output",
                str(jwt_out),
            ]
            _run(license_cmd)

        pack_included = False
        pack_out = docsops_dir / ".capability_pack.enc"
        if with_pack:
            if args.capability_pack_path:
                src = Path(args.capability_pack_path).resolve()
                if not src.exists():
                    raise FileNotFoundError(f"--capability-pack-path not found: {src}")
                shutil.copy2(src, pack_out)
                pack_included = True
            else:
                license_key = (args.license_key or os.environ.get("VERIOPS_LICENSE_KEY", "")).strip()
                if not license_key:
                    raise ValueError(
                        "--with-pack requires --license-key, VERIOPS_LICENSE_KEY, or --capability-pack-path"
                    )
                pack_cmd = [
                    sys.executable,
                    str(REPO_ROOT / "build" / "generate_pack.py"),
                    "--client-id",
                    client_id,
                    "--plan",
                    plan,
                    "--license-key",
                    license_key,
                    "--days",
                    str(days),
                    "--output",
                    str(pack_out),
                ]
                _run(pack_cmd)
                pack_included = pack_out.exists()

        _write_readme(tmp_dir / "README_RENEWAL.md", client_id=client_id, includes_pack=pack_included)
        manifest: dict[str, Any] = {
            "client_id": client_id,
            "tenant_id": tenant_id,
            "company_domain": company_domain,
            "plan": plan,
            "days": days,
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "files": {
                "license_jwt": "docsops/license.jwt",
                "capability_pack": "docsops/.capability_pack.enc" if pack_included else "",
                "readme": "README_RENEWAL.md",
            },
            "strict_local_ready": True,
        }
        (tmp_dir / "renewal_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

        _create_archive(tmp_dir, output_path, args.format)

    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build offline renewal bundle for strict-local clients")
    parser.add_argument("--client-id", required=True, help="Client identifier")
    parser.add_argument("--plan", choices=["pilot", "professional", "enterprise"], required=True)
    parser.add_argument("--days", type=int, default=30, help="New license validity in days")
    parser.add_argument("--tenant-id", default="", help="Optional tenant claim (defaults to client-id)")
    parser.add_argument("--company-domain", default="", help="Optional company domain claim")
    parser.add_argument(
        "--with-pack",
        action="store_true",
        help="Include .capability_pack.enc in renewal archive",
    )
    parser.add_argument(
        "--license-key",
        default="",
        help="License key for pack generation (or set VERIOPS_LICENSE_KEY env)",
    )
    parser.add_argument(
        "--license-jwt-path",
        default="",
        help="Use pre-generated license JWT instead of generating a new one",
    )
    parser.add_argument(
        "--capability-pack-path",
        default="",
        help="Use pre-generated capability pack instead of generating one",
    )
    parser.add_argument(
        "--format",
        choices=["zip", "tar.gz"],
        default="zip",
        help="Archive format",
    )
    parser.add_argument("--output-dir", default="generated/offline_renewals", help="Directory for renewal archive")
    parser.add_argument("--filename", default="", help="Custom archive filename")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = build_bundle(args)
    print(f"[ok] offline renewal archive: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

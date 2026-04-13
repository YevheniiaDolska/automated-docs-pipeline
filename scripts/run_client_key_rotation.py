#!/usr/bin/env python3
"""Run per-client key rotation and license re-issuance as an ops batch."""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = REPO_ROOT / "build"
if str(BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(BUILD_DIR))

from generate_license import _generate_ed25519_keypair, generate_jwt


DEFAULT_REGISTRY = REPO_ROOT / "config" / "licensing" / "clients.yml"
DEFAULT_KEYS_DIR = REPO_ROOT / "docsops" / "keys" / "clients"
DEFAULT_REPORT = REPO_ROOT / "reports" / "client_key_rotation_report.json"
DEFAULT_JWT_DIR = REPO_ROOT / "generated" / "tmp" / "licenses"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(raw: str) -> datetime | None:
    text = str(raw or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _fmt_dt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_registry(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not path.exists():
        raise FileNotFoundError(f"Registry not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("Registry must be a mapping with 'clients' list.")
    clients = payload.get("clients", [])
    if not isinstance(clients, list):
        raise ValueError("Registry field 'clients' must be a list.")
    normalized: list[dict[str, Any]] = []
    for idx, raw in enumerate(clients):
        if not isinstance(raw, dict):
            raise ValueError(f"Client entry #{idx} must be a mapping.")
        normalized.append(dict(raw))
    payload["clients"] = normalized
    return payload, normalized


def _write_registry(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def _is_rotation_due(client: dict[str, Any], now: datetime, default_days: int) -> tuple[bool, str]:
    next_rot = _parse_dt(str(client.get("next_key_rotation_at", "")).strip())
    if next_rot is not None:
        return now >= next_rot, f"next_key_rotation_at={_fmt_dt(next_rot)}"
    last_rot = _parse_dt(str(client.get("last_key_rotated_at", "")).strip())
    period_days = int(client.get("key_rotation_days", default_days) or default_days)
    if last_rot is None:
        return True, "never_rotated"
    due_at = last_rot + timedelta(days=period_days)
    return now >= due_at, f"due_at={_fmt_dt(due_at)}"


def _should_process(client: dict[str, Any]) -> tuple[bool, str]:
    status = str(client.get("status", "active")).strip().lower()
    if status not in {"active", "enabled"}:
        return False, f"status={status}"
    if not bool(client.get("retainer_active", True)):
        return False, "retainer_inactive"
    client_id = str(client.get("client_id", "")).strip()
    if not client_id:
        return False, "missing_client_id"
    plan = str(client.get("plan", "")).strip().lower()
    if plan not in {"pilot", "professional", "enterprise"}:
        return False, f"unsupported_plan={plan or 'empty'}"
    return True, "ok"


def _rotate_one(
    client: dict[str, Any],
    *,
    now: datetime,
    keys_dir: Path,
    jwt_dir: Path,
    license_days_default: int,
    rotation_days_default: int,
    dry_run: bool,
) -> dict[str, Any]:
    client_id = str(client.get("client_id", "")).strip()
    tenant_id = str(client.get("tenant_id", client_id)).strip()
    company_domain = str(client.get("company_domain", "")).strip().lower()
    plan = str(client.get("plan", "")).strip().lower()
    max_docs = int(client.get("max_docs", 0) or 0)
    license_days = int(client.get("license_days", license_days_default) or license_days_default)
    rotation_days = int(client.get("key_rotation_days", rotation_days_default) or rotation_days_default)

    per_client_key_dir = keys_dir / client_id
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    versioned_key = per_client_key_dir / f"veriops-licensing-{stamp}.key"
    versioned_pub = per_client_key_dir / f"veriops-licensing-{stamp}.pub"
    current_key = per_client_key_dir / "veriops-licensing.key"
    current_pub = per_client_key_dir / "veriops-licensing.pub"
    jwt_path = jwt_dir / f"{client_id}.license.jwt"

    if dry_run:
        return {
            "client_id": client_id,
            "status": "DRY_RUN",
            "plan": plan,
            "rotation_days": rotation_days,
            "license_days": license_days,
            "next_key_rotation_at": _fmt_dt(now + timedelta(days=rotation_days)),
            "license_path": str(jwt_path),
            "public_key_path": str(current_pub),
            "private_key_path": str(current_key),
        }

    priv_key, pub_key = _generate_ed25519_keypair()
    token = generate_jwt(
        client_id=client_id,
        plan=plan,
        days=license_days,
        private_key=priv_key,
        max_docs=max_docs,
        tenant_id=tenant_id,
        company_domain=company_domain,
    )

    per_client_key_dir.mkdir(parents=True, exist_ok=True)
    jwt_dir.mkdir(parents=True, exist_ok=True)
    b64_priv = base64.b64encode(priv_key)
    b64_pub = base64.b64encode(pub_key)
    versioned_key.write_bytes(b64_priv + b"\n")
    versioned_pub.write_bytes(b64_pub + b"\n")
    current_key.write_bytes(b64_priv + b"\n")
    current_pub.write_bytes(b64_pub + b"\n")
    jwt_path.write_text(token + "\n", encoding="utf-8")
    try:
        os.chmod(versioned_key, 0o600)
        os.chmod(current_key, 0o600)
    except OSError:
        pass

    key_id = base64.urlsafe_b64encode(pub_key).decode("ascii").rstrip("=")[:20]
    expires = now + timedelta(days=license_days)
    return {
        "client_id": client_id,
        "status": "ROTATED",
        "plan": plan,
        "key_id": key_id,
        "rotation_days": rotation_days,
        "license_days": license_days,
        "rotated_at": _fmt_dt(now),
        "license_expires_at": _fmt_dt(expires),
        "next_key_rotation_at": _fmt_dt(now + timedelta(days=rotation_days)),
        "license_path": str(jwt_path),
        "public_key_path": str(current_pub),
        "private_key_path": str(current_key),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Rotate per-client keys and re-issue licenses.")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY), help="Path to client registry YAML.")
    parser.add_argument("--keys-dir", default=str(DEFAULT_KEYS_DIR), help="Root directory for per-client keypairs.")
    parser.add_argument("--jwt-dir", default=str(DEFAULT_JWT_DIR), help="Output directory for issued client JWTs.")
    parser.add_argument("--rotation-days", type=int, default=90, help="Default key rotation period in days.")
    parser.add_argument("--license-days", type=int, default=30, help="Default issued license validity in days.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Path to JSON report.")
    parser.add_argument("--dry-run", action="store_true", help="Evaluate and report without writing files.")
    args = parser.parse_args()

    now = _now_utc()
    registry_path = Path(args.registry).resolve()
    keys_dir = Path(args.keys_dir).resolve()
    jwt_dir = Path(args.jwt_dir).resolve()
    report_path = Path(args.report).resolve()

    payload, clients = _load_registry(registry_path)

    report: dict[str, Any] = {
        "generated_at": _fmt_dt(now),
        "registry_path": str(registry_path),
        "dry_run": bool(args.dry_run),
        "results": [],
        "summary": {"total": len(clients), "rotated": 0, "skipped": 0, "errors": 0},
    }

    for client in clients:
        client_id = str(client.get("client_id", "")).strip() or "<missing>"
        enabled, reason = _should_process(client)
        if not enabled:
            report["results"].append({"client_id": client_id, "status": "SKIPPED", "reason": reason})
            report["summary"]["skipped"] += 1
            continue

        due, due_reason = _is_rotation_due(client, now, int(args.rotation_days))
        if not due:
            report["results"].append({"client_id": client_id, "status": "SKIPPED", "reason": due_reason})
            report["summary"]["skipped"] += 1
            continue

        try:
            result = _rotate_one(
                client,
                now=now,
                keys_dir=keys_dir,
                jwt_dir=jwt_dir,
                license_days_default=int(args.license_days),
                rotation_days_default=int(args.rotation_days),
                dry_run=bool(args.dry_run),
            )
        except (RuntimeError, ValueError, TypeError, OSError) as exc:
            report["results"].append(
                {"client_id": client_id, "status": "ERROR", "reason": f"{due_reason}; {exc}"}
            )
            report["summary"]["errors"] += 1
            continue

        report["results"].append(result)
        report["summary"]["rotated"] += 1

        if not args.dry_run:
            client["last_key_rotated_at"] = result["rotated_at"]
            client["next_key_rotation_at"] = result["next_key_rotation_at"]
            client["private_key_path"] = result["private_key_path"]
            client["public_key_path"] = result["public_key_path"]
            client["last_license_issued_at"] = result["rotated_at"]
            client["last_license_expires_at"] = result["license_expires_at"]
            client["latest_license_jwt_path"] = result["license_path"]

    if not args.dry_run:
        _write_registry(registry_path, payload)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"[key-rotation] report: {report_path}")
    print(
        "[key-rotation] summary: "
        f"rotated={report['summary']['rotated']} "
        f"skipped={report['summary']['skipped']} "
        f"errors={report['summary']['errors']}"
    )
    return 0 if int(report["summary"]["errors"]) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Production smoke test for VeriDoc API.

Usage:
    VERIDOC_BASE_URL=https://api.veri-doc.app \
    VERIDOC_SMOKE_EMAIL=smoke@veri-doc.app \
    VERIDOC_SMOKE_PASSWORD='StrongPass123!' \
    python3 scripts/production_smoke.py
"""

from __future__ import annotations

import os
import sys
from typing import Any

import httpx


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name, default).strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def _check(response: httpx.Response, name: str, expected: set[int]) -> dict[str, Any]:
    if response.status_code not in expected:
        raise SystemExit(
            f"[FAIL] {name}: expected {sorted(expected)}, got {response.status_code}, body={response.text[:400]}"
        )
    payload = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
    print(f"[OK] {name}: {response.status_code}")
    return payload


def _auth_token(client: httpx.Client, base_url: str, email: str, password: str) -> str:
    register_payload = {
        "email": email,
        "password": password,
        "full_name": "Production Smoke User",
    }
    register = client.post(f"{base_url}/auth/register", json=register_payload)
    if register.status_code not in {200, 201, 409}:
        raise SystemExit(f"[FAIL] register: {register.status_code}, body={register.text[:400]}")
    print(f"[OK] register: {register.status_code}")

    login = client.post(f"{base_url}/auth/login", json={"email": email, "password": password})
    login_payload = _check(login, "login", {200})
    token = str(login_payload.get("access_token", "")).strip()
    if not token:
        raise SystemExit("[FAIL] login did not return access_token")
    return token


def main() -> int:
    base_url = _env("VERIDOC_BASE_URL")
    email = _env("VERIDOC_SMOKE_EMAIL")
    password = _env("VERIDOC_SMOKE_PASSWORD")
    timeout_seconds = int(os.getenv("VERIDOC_SMOKE_TIMEOUT_SECONDS", "20"))

    with httpx.Client(timeout=timeout_seconds) as client:
        _check(client.get(f"{base_url}/health"), "health", {200})
        _check(client.get(f"{base_url}/health/ready"), "health/ready", {200})

        token = _auth_token(client, base_url, email, password)
        headers = {"Authorization": f"Bearer {token}"}

        _check(client.get(f"{base_url}/api/dashboard/", headers=headers), "api/dashboard", {200})
        _check(client.get(f"{base_url}/api/settings/", headers=headers), "api/settings GET", {200})

        update_payload = {"automation": {"mode": "veridoc", "trigger": "policy", "publish_policy": "gated"}}
        _check(client.put(f"{base_url}/api/settings/", headers=headers, json=update_payload), "api/settings PUT", {200})

        _check(client.get(f"{base_url}/api/pipeline/automation/status", headers=headers), "api/pipeline/automation/status", {200})

    print("[OK] Production smoke completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())

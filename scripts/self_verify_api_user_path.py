#!/usr/bin/env python3
"""Run user-path smoke checks against an API mock server."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request


def call_json(method: str, url: str, body: dict | None = None) -> tuple[int, dict | None]:
    data = None
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": "Bearer demo-token",
        "X-Request-Id": "req_demo_user_path",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url=url, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            status = response.getcode()
            payload = response.read().decode("utf-8")
            if not payload:
                return status, None
            return status, json.loads(payload)
    except urllib.error.HTTPError as error:
        payload = error.read().decode("utf-8")
        parsed = json.loads(payload) if payload else None
        return error.code, parsed


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify API user path against mock server")
    parser.add_argument("--base-url", default="http://localhost:4010/v1")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")

    status, payload = call_json("GET", f"{base}/projects?limit=1")
    require(status == 200, f"GET /projects expected 200, got {status}")
    require(isinstance(payload, dict) and "data" in payload and "page" in payload, "GET /projects payload shape mismatch")

    status, payload = call_json(
        "POST",
        f"{base}/projects",
        body={
            "name": "API-first rollout",
            "description": "User-path verification project",
            "owner_id": "1edd3e73-e605-4559-a6f9-dcd27f2f6488",
        },
    )
    require(status in (200, 201), f"POST /projects expected 200/201, got {status}")

    status, payload = call_json("GET", f"{base}/tasks?limit=1")
    require(status == 200, f"GET /tasks expected 200, got {status}")
    require(isinstance(payload, dict) and "data" in payload and "page" in payload, "GET /tasks payload shape mismatch")

    status, payload = call_json("GET", f"{base}/users/me")
    require(status == 200, f"GET /users/me expected 200, got {status}")
    require(isinstance(payload, dict) and "email" in payload, "GET /users/me payload shape mismatch")

    print("API user-path self-verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

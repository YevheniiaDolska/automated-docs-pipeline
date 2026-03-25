#!/usr/bin/env python3
"""Runtime self-verification for non-REST protocols (mock/real endpoints)."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def _post_json(url: str, payload: dict[str, Any], timeout_sec: float) -> tuple[int, str]:
    body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:  # noqa: S310
            return int(getattr(resp, "status", 200) or 200), resp.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as exc:
        data = exc.read().decode("utf-8", errors="ignore") if exc.fp else ""
        return int(exc.code), data
    except urllib.error.URLError as exc:
        return 599, str(getattr(exc, "reason", exc))


def _parse_json(raw: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(raw)
    except (Exception,):  # noqa: BLE001
        return None
    return payload if isinstance(payload, dict) else None


def _contains_any(raw: str, keys: list[str]) -> bool:
    lowered = raw.lower()
    return any(key.lower() in lowered for key in keys)


def _validate_url(url: str, *, allow_ws: bool = False) -> bool:
    parsed = urllib.parse.urlparse(url)
    schemes = {"http", "https"}
    if allow_ws:
        schemes.update({"ws", "wss"})
    return bool(parsed.scheme in schemes and parsed.netloc)


def _graphql_self_verify(endpoint: str, timeout_sec: float) -> tuple[bool, str]:
    checks = [
        ("query HealthCheck { __typename }", ["__typename", "data", "health"]),
        ("query ProjectById { project(id: \"demo\") { id name status } }", ["project", "id", "name", "status"]),
    ]
    responses: list[str] = []
    for query, expected in checks:
        status, body = _post_json(endpoint, {"query": query}, timeout_sec)
        if status >= 500:
            return False, f"graphql endpoint returned {status}"
        if not body.strip():
            return False, "graphql endpoint returned empty body"
        payload = _parse_json(body)
        if payload is None:
            return False, "graphql endpoint returned non-json body"
        if not (("data" in payload) or ("errors" in payload)):
            return False, "graphql response missing data/errors envelope"
        if not _contains_any(body, expected):
            return False, "graphql response is not relevant to request"
        responses.append(body)
    if len(set(responses)) == 1:
        return False, "graphql responses are identical for different requests"
    return True, "graphql live relevance checks passed"


def _grpc_self_verify(endpoint: str, timeout_sec: float) -> tuple[bool, str]:
    checks = [
        (
            {"service": "ProjectService", "method": "GetProject", "payload": {"project_id": "demo"}},
            ["getproject", "project", "id", "status"],
        ),
        (
            {"service": "ProjectService", "method": "CreateProject", "payload": {"name": "Acme"}},
            ["createproject", "created", "project", "id"],
        ),
    ]
    responses: list[str] = []
    for payload, expected in checks:
        status, body = _post_json(endpoint, payload, timeout_sec)
        if status >= 500:
            return False, f"grpc gateway returned {status}"
        if not body.strip():
            return False, "grpc gateway returned empty body"
        parsed = _parse_json(body)
        if parsed is None:
            return False, "grpc gateway returned non-json body"
        if not _contains_any(body, expected):
            return False, "grpc response is not relevant to invoked method"
        responses.append(body)
    if len(set(responses)) == 1:
        return False, "grpc responses are identical for different methods"
    return True, "grpc live relevance checks passed"


def _asyncapi_self_verify(http_endpoint: str, ws_endpoint: str, timeout_sec: float) -> tuple[bool, str]:
    if http_endpoint:
        checks = [
            ({"event": "project.updated", "data": {"project_id": "demo"}}, ["project.updated", "project", "ack"]),
            ({"event": "task.completed", "data": {"task_id": "t-1"}}, ["task.completed", "task", "ack"]),
        ]
        responses: list[str] = []
        for payload, expected in checks:
            status, body = _post_json(http_endpoint, payload, timeout_sec)
            if status >= 500:
                return False, f"asyncapi http publish returned {status}"
            if not body.strip():
                return False, "asyncapi http publish returned empty body"
            parsed = _parse_json(body)
            if parsed is None:
                return False, "asyncapi publish returned non-json body"
            if not _contains_any(body, expected):
                return False, "asyncapi response is not relevant to published event"
            responses.append(body)
        if len(set(responses)) == 1:
            return False, "asyncapi responses are identical for different events"
        return True, "asyncapi live relevance checks passed"

    if ws_endpoint:
        if not _validate_url(ws_endpoint, allow_ws=True):
            return False, "invalid ws endpoint url"
        return False, "asyncapi ws-only endpoint is configured; set http publish endpoint for live relevance checks"

    return False, "missing asyncapi endpoints"


def _websocket_self_verify(ws_endpoint: str, http_endpoint: str, timeout_sec: float) -> tuple[bool, str]:
    if http_endpoint:
        checks = [
            (
                {"action": "subscribe", "channel": "project.updated", "payload": {"project_id": "demo"}},
                ["subscribe", "project.updated", "ack"],
            ),
            (
                {"action": "publish", "channel": "task.completed", "payload": {"task_id": "t-1"}},
                ["publish", "task.completed", "ack"],
            ),
        ]
        responses: list[str] = []
        for payload, expected in checks:
            status, body = _post_json(http_endpoint, payload, timeout_sec)
            if status >= 500:
                return False, f"websocket bridge returned {status}"
            if not body.strip():
                return False, "websocket bridge returned empty body"
            parsed = _parse_json(body)
            if parsed is None:
                return False, "websocket bridge returned non-json body"
            if not _contains_any(body, expected):
                return False, "websocket response is not relevant to action/channel"
            responses.append(body)
        if len(set(responses)) == 1:
            return False, "websocket responses are identical for different actions"
        return True, "websocket live relevance checks passed"

    if not ws_endpoint:
        return False, "missing websocket endpoint and http bridge endpoint"
    if not _validate_url(ws_endpoint, allow_ws=True):
        return False, "invalid websocket endpoint url"
    return False, "ws-only endpoint is configured; set websocket_http_bridge_endpoint for live relevance checks"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run runtime self verification for protocol")
    parser.add_argument("--protocol", required=True, choices=["graphql", "grpc", "asyncapi", "websocket"])
    parser.add_argument("--endpoint", default="")
    parser.add_argument("--ws-endpoint", default="")
    parser.add_argument("--http-endpoint", default="")
    parser.add_argument("--require-endpoint", action="store_true")
    parser.add_argument("--timeout-sec", type=float, default=8.0)
    parser.add_argument("--json-report", default="")
    args = parser.parse_args()

    endpoint = str(args.endpoint).strip()
    ws_endpoint = str(args.ws_endpoint).strip()
    http_endpoint = str(args.http_endpoint).strip()

    ok = True
    detail = ""
    skipped = False

    if args.protocol == "graphql":
        if not endpoint:
            skipped = True
            ok = not args.require_endpoint
            detail = "graphql endpoint not configured"
        elif not _validate_url(endpoint):
            ok = False
            detail = "invalid graphql endpoint url"
        else:
            ok, detail = _graphql_self_verify(endpoint, args.timeout_sec)
    elif args.protocol == "grpc":
        if not endpoint:
            skipped = True
            ok = not args.require_endpoint
            detail = "grpc gateway endpoint not configured"
        elif not _validate_url(endpoint):
            ok = False
            detail = "invalid grpc gateway endpoint url"
        else:
            ok, detail = _grpc_self_verify(endpoint, args.timeout_sec)
    elif args.protocol == "asyncapi":
        if not http_endpoint and not ws_endpoint:
            skipped = True
            ok = not args.require_endpoint
            detail = "asyncapi endpoints not configured"
        else:
            ok, detail = _asyncapi_self_verify(http_endpoint, ws_endpoint, args.timeout_sec)
    elif args.protocol == "websocket":
        resolved_ws = ws_endpoint or endpoint
        if not resolved_ws and not http_endpoint:
            skipped = True
            ok = not args.require_endpoint
            detail = "websocket endpoint not configured"
        else:
            ok, detail = _websocket_self_verify(resolved_ws, http_endpoint, args.timeout_sec)

    report = {
        "protocol": args.protocol,
        "ok": bool(ok),
        "skipped": bool(skipped),
        "detail": detail,
    }

    if args.json_report:
        report_path = Path(args.json_report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    status = "ok" if ok else "fail"
    print(f"[protocol-self-verify:{args.protocol}] {status} - {detail}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate protocol-aware test assets with smart merge and needs_review queue."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.api_protocols import normalize_protocols


def _source_hash(source: str) -> str:
    path = Path(source)
    if path.exists() and path.is_file():
        data = path.read_bytes()
    elif path.exists() and path.is_dir():
        chunks: list[bytes] = []
        for item in sorted(path.rglob("*")):
            if item.is_file():
                chunks.append(item.read_bytes())
        data = b"\n".join(chunks)
    else:
        data = source.encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:12]


def _load_payload(path: Path) -> Any:
    if not path.exists() or path.is_dir():
        return {}
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    if suffix == ".json":
        return json.loads(text)
    return text


def _extract_graphql_fields(schema_text: str, type_name: str) -> list[str]:
    block = re.search(rf"type\s+{re.escape(type_name)}\s*\{{(.*?)\}}", schema_text, re.DOTALL)
    if not block:
        return []
    fields: list[str] = []
    for raw in block.group(1).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name = line.split("(", 1)[0].split(":", 1)[0].strip()
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            fields.append(name)
    return sorted(set(fields))


def _extract_grpc_methods(source: Path, payload: Any) -> list[str]:
    methods: list[str] = []

    def parse_text(text: str) -> None:
        current_service = ""
        for raw in text.splitlines():
            line = raw.strip()
            svc = re.match(r"^service\s+([A-Za-z0-9_]+)\s*\{", line)
            if svc:
                current_service = svc.group(1)
                continue
            if line == "}":
                current_service = ""
                continue
            rpc = re.match(r"^rpc\s+([A-Za-z0-9_]+)\s*\(", line)
            if rpc and current_service:
                methods.append(f"{current_service}.{rpc.group(1)}")

    if isinstance(payload, str) and source.suffix.lower() == ".proto":
        parse_text(payload)
        return sorted(set(methods))

    if source.is_dir():
        for proto in sorted(source.rglob("*.proto")):
            parse_text(proto.read_text(encoding="utf-8"))
    return sorted(set(methods))


def _extract_channels(payload: Any) -> list[str]:
    if isinstance(payload, dict):
        channels = payload.get("channels", payload.get("events", {}))
        if isinstance(channels, dict):
            return sorted(str(ch) for ch in channels.keys())
    return []


def _mk_case(
    *,
    protocol: str,
    entity: str,
    check: str,
    title: str,
    expected: str,
    source: str,
    signature: str,
    steps: list[str],
) -> dict[str, Any]:
    cid = f"TC-{protocol}-{entity}-{check}".replace(" ", "-").lower()
    return {
        "id": cid,
        "title": title,
        "suite": f"{protocol.upper()} Contract",
        "operation_id": f"{entity}:{check}",
        "traceability": {"method": "N/A", "path": source, "operation_id": f"{entity}:{check}"},
        "preconditions": ["Contract source is available", "Target endpoint/mock is reachable"],
        "steps": steps,
        "expected_result": expected,
        "origin": "auto",
        "customized": False,
        "needs_review": False,
        "protocol": protocol,
        "entity": entity,
        "check_type": check,
        "spec_signature": signature,
    }


def _graphql_cases(source: str, signature: str, payload: Any) -> list[dict[str, Any]]:
    text = payload if isinstance(payload, str) else ""
    entities = [f"query:{f}" for f in _extract_graphql_fields(text, "Query")]
    entities.extend([f"mutation:{f}" for f in _extract_graphql_fields(text, "Mutation")])
    entities.extend([f"subscription:{f}" for f in _extract_graphql_fields(text, "Subscription")])
    if not entities:
        entities = ["schema"]

    cases: list[dict[str, Any]] = []
    for entity in entities:
        cases.append(
            _mk_case(
                protocol="graphql",
                entity=entity,
                check="positive",
                title=f"GraphQL {entity} happy path",
                expected="Response shape matches schema and required fields are present.",
                source=source,
                signature=signature,
                steps=["Execute operation with valid arguments.", "Validate response data and type contract."],
            )
        )
        cases.append(
            _mk_case(
                protocol="graphql",
                entity=entity,
                check="negative",
                title=f"GraphQL {entity} invalid input",
                expected="Validation error is returned with stable error envelope.",
                source=source,
                signature=signature,
                steps=["Send malformed input or invalid type.", "Validate deterministic error semantics."],
            )
        )
        cases.append(
            _mk_case(
                protocol="graphql",
                entity=entity,
                check="auth",
                title=f"GraphQL {entity} auth policy",
                expected="Unauthorized access is blocked; authorized call succeeds.",
                source=source,
                signature=signature,
                steps=["Call without auth token.", "Call with valid token and compare behavior."],
            )
        )
        cases.append(
            _mk_case(
                protocol="graphql",
                entity=entity,
                check="security-injection",
                title=f"GraphQL {entity} injection hardening",
                expected="Injection-like payloads are safely rejected and do not expose internals.",
                source=source,
                signature=signature,
                steps=["Send malicious nested/introspection/injection payload.", "Validate sanitized error behavior."],
            )
        )
        cases.append(
            _mk_case(
                protocol="graphql",
                entity=entity,
                check="performance-latency",
                title=f"GraphQL {entity} latency budget",
                expected="P95 latency remains within documented SLO under representative load.",
                source=source,
                signature=signature,
                steps=["Execute operation under target concurrency.", "Capture latency percentiles and compare with SLO."],
            )
        )
    return cases


def _grpc_cases(source: str, signature: str, payload: Any, source_path: Path) -> list[dict[str, Any]]:
    methods = _extract_grpc_methods(source_path, payload)
    if not methods:
        methods = ["service.rpc"]

    cases: list[dict[str, Any]] = []
    for method in methods:
        cases.append(
            _mk_case(
                protocol="grpc",
                entity=method,
                check="positive",
                title=f"gRPC {method} happy path",
                expected="Method returns success status and expected message contract.",
                source=source,
                signature=signature,
                steps=["Invoke RPC with valid payload.", "Verify status and response shape."],
            )
        )
        cases.append(
            _mk_case(
                protocol="grpc",
                entity=method,
                check="status-codes",
                title=f"gRPC {method} status-code behavior",
                expected="Invalid payload produces deterministic non-OK status code.",
                source=source,
                signature=signature,
                steps=["Invoke RPC with malformed payload.", "Verify returned status code semantics."],
            )
        )
        cases.append(
            _mk_case(
                protocol="grpc",
                entity=method,
                check="deadline-retry",
                title=f"gRPC {method} deadline/retry policy",
                expected="Deadline and retry behavior matches documented policy.",
                source=source,
                signature=signature,
                steps=["Call RPC with short deadline.", "Validate retry/backoff and failure semantics."],
            )
        )
        cases.append(
            _mk_case(
                protocol="grpc",
                entity=method,
                check="security-authz",
                title=f"gRPC {method} authz enforcement",
                expected="Unauthorized principal is denied; authorized principal receives valid response.",
                source=source,
                signature=signature,
                steps=["Invoke RPC without/with invalid credentials.", "Invoke with valid credentials and compare behavior."],
            )
        )
        cases.append(
            _mk_case(
                protocol="grpc",
                entity=method,
                check="performance-latency",
                title=f"gRPC {method} latency budget",
                expected="RPC latency stays within documented SLO under representative load.",
                source=source,
                signature=signature,
                steps=["Run target load against RPC.", "Validate P95/P99 latency against policy."],
            )
        )
    return cases


def _event_cases(protocol: str, source: str, signature: str, payload: Any) -> list[dict[str, Any]]:
    channels = _extract_channels(payload)
    if not channels:
        channels = ["channel.default"]
    cases: list[dict[str, Any]] = []
    for channel in channels:
        cases.append(
            _mk_case(
                protocol=protocol,
                entity=channel,
                check="publish",
                title=f"{protocol.upper()} {channel} publish contract",
                expected="Valid payload is accepted and routed according to contract.",
                source=source,
                signature=signature,
                steps=["Publish valid event/message.", "Verify downstream acceptance and schema conformance."],
            )
        )
        cases.append(
            _mk_case(
                protocol=protocol,
                entity=channel,
                check="invalid-payload",
                title=f"{protocol.upper()} {channel} invalid payload",
                expected="Invalid event payload is rejected with deterministic error handling.",
                source=source,
                signature=signature,
                steps=["Publish malformed payload.", "Validate rejection and error envelope."],
            )
        )
        cases.append(
            _mk_case(
                protocol=protocol,
                entity=channel,
                check="ordering-idempotency",
                title=f"{protocol.upper()} {channel} ordering/idempotency",
                expected="Duplicate/out-of-order messages are handled according to policy.",
                source=source,
                signature=signature,
                steps=["Send duplicate and reordered events.", "Verify idempotency and ordering semantics."],
            )
        )
        security_check = "security-signature" if protocol == "asyncapi" else "security-authz"
        security_expected = (
            "Invalid or missing event signature is rejected before processing."
            if protocol == "asyncapi"
            else "Unauthorized connection/publish attempt is denied."
        )
        cases.append(
            _mk_case(
                protocol=protocol,
                entity=channel,
                check=security_check,
                title=f"{protocol.upper()} {channel} security policy",
                expected=security_expected,
                source=source,
                signature=signature,
                steps=["Send event/message without valid security context.", "Validate deterministic rejection behavior."],
            )
        )
        perf_check = "performance-throughput" if protocol == "asyncapi" else "performance-concurrency"
        cases.append(
            _mk_case(
                protocol=protocol,
                entity=channel,
                check=perf_check,
                title=f"{protocol.upper()} {channel} performance profile",
                expected="Throughput/concurrency remains within documented SLO without contract violations.",
                source=source,
                signature=signature,
                steps=["Run representative load burst.", "Validate SLO metrics and message contract integrity."],
            )
        )
    return cases


def _default_cases(protocol: str, source: str, signature: str, payload: Any, source_path: Path) -> list[dict[str, Any]]:
    if protocol == "graphql":
        return _graphql_cases(source, signature, payload)
    if protocol == "grpc":
        return _grpc_cases(source, signature, payload, source_path)
    if protocol in {"asyncapi", "websocket"}:
        return _event_cases(protocol, source, signature, payload)
    return [
        _mk_case(
            protocol=protocol,
            entity="contract",
            check="positive",
            title=f"{protocol.upper()} contract happy path",
            expected="Contract validates and one happy-path flow passes.",
            source=source,
            signature=signature,
            steps=["Load contract.", "Run representative success flow."],
        )
    ]


def _load_existing(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data.get("cases", []) if isinstance(data, dict) else []
    return [item for item in cases if isinstance(item, dict) and str(item.get("id", "")).strip()]


def _merge_cases(new_cases: list[dict[str, Any]], existing_cases: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    existing = {str(case["id"]): dict(case) for case in existing_cases}
    merged: list[dict[str, Any]] = []
    stats = {
        "new": 0,
        "updated": 0,
        "preserved_custom": 0,
        "preserved_manual": 0,
        "stale_custom_needs_review": 0,
    }

    touched: set[str] = set()
    for case in new_cases:
        cid = str(case["id"])
        touched.add(cid)
        current = existing.get(cid)
        if current is None:
            merged.append(case)
            stats["new"] += 1
            continue

        if str(current.get("origin", "auto")) == "manual":
            manual_case = dict(current)
            manual_case["needs_review"] = False
            merged.append(manual_case)
            stats["preserved_manual"] += 1
            continue

        customized = bool(current.get("customized", False))
        signature_changed = str(current.get("spec_signature", "")) != str(case.get("spec_signature", ""))
        if customized:
            custom_case = dict(current)
            custom_case["needs_review"] = signature_changed
            custom_case["last_generated_signature"] = str(case.get("spec_signature", ""))
            merged.append(custom_case)
            stats["preserved_custom"] += 1
            continue

        merged.append(case)
        stats["updated"] += 1

    for cid, case in existing.items():
        if cid in touched:
            continue
        if str(case.get("origin", "auto")) == "manual" or bool(case.get("customized", False)):
            stale = dict(case)
            stale["needs_review"] = True
            stale["review_reason"] = "contract_entity_removed"
            merged.append(stale)
            stats["stale_custom_needs_review"] += 1

    merged.sort(key=lambda item: str(item.get("id", "")))
    return merged, stats


def _write_testrail_csv(path: Path, cases: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["title", "section", "preconditions", "steps", "expected_result"])
        for case in cases:
            writer.writerow(
                [
                    case.get("title", ""),
                    case.get("suite", ""),
                    "\n".join(case.get("preconditions", [])),
                    "\n".join(f"{idx + 1}. {step}" for idx, step in enumerate(case.get("steps", []))),
                    case.get("expected_result", ""),
                ]
            )


def _write_zephyr_json(path: Path, cases: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "testCases": [
            {
                "name": case.get("title", ""),
                "objective": case.get("expected_result", ""),
                "precondition": "\n".join(case.get("preconditions", [])),
                "labels": ["multi-protocol", "auto-generated", str(case.get("protocol", "api")), str(case.get("check_type", "contract"))],
                "statusName": "Draft",
                "priorityName": "Normal",
            }
            for case in cases
        ]
    }
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_matrix(path: Path, cases: list[dict[str, Any]]) -> None:
    matrix = [
        {
            "id": case.get("id", ""),
            "protocol": case.get("protocol", ""),
            "entity": case.get("entity", ""),
            "check_type": case.get("check_type", ""),
            "suite": case.get("suite", ""),
        }
        for case in cases
    ]
    path.write_text(json.dumps({"matrix": matrix}, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_fuzz(path: Path, cases: list[dict[str, Any]]) -> None:
    scenarios = [
        {
            "scenario_id": f"fuzz-{case.get('id', '')}",
            "protocol": case.get("protocol", ""),
            "entity": case.get("entity", ""),
            "payload_mutations": ["missing_required_fields", "invalid_types", "oversized_payload"],
            "expected": "Contract validation rejects malformed payloads without undefined behavior.",
        }
        for case in cases
    ]
    path.write_text(json.dumps({"scenarios": scenarios}, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate protocol-aware test assets")
    parser.add_argument("--protocols", default="graphql,grpc,asyncapi,websocket")
    parser.add_argument("--source", required=True)
    parser.add_argument("--output-dir", default="reports/api-test-assets")
    parser.add_argument("--testrail-csv", default="reports/api-test-assets/testrail_test_cases.csv")
    parser.add_argument("--zephyr-json", default="reports/api-test-assets/zephyr_test_cases.json")
    args = parser.parse_args()

    protocols = [p for p in normalize_protocols(args.protocols.split(","), default=[]) if p != "rest"]
    if not protocols:
        print("[protocol-test-assets] no non-REST protocols selected; nothing to generate")
        return 0

    source_path = Path(args.source)
    payload = _load_payload(source_path)
    signature = _source_hash(args.source)
    new_cases: list[dict[str, Any]] = []
    for protocol in protocols:
        new_cases.extend(_default_cases(protocol, args.source, signature, payload, source_path))

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cases_path = output_dir / "api_test_cases.json"
    existing = _load_existing(cases_path)
    merged, stats = _merge_cases(new_cases, existing)

    needs_review = [case for case in merged if bool(case.get("needs_review", False))]
    payload_out = {
        "cases": merged,
        "merge_stats": stats,
        "needs_review_count": len(needs_review),
        "needs_review_ids": [str(case.get("id", "")) for case in needs_review],
        "source_signature": signature,
    }
    cases_path.write_text(json.dumps(payload_out, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    _write_testrail_csv(Path(args.testrail_csv), merged)
    _write_zephyr_json(Path(args.zephyr_json), merged)
    _write_matrix(output_dir / "test_matrix.json", merged)
    _write_fuzz(output_dir / "fuzz_scenarios.json", merged)

    print(f"[protocol-test-assets] generated {len(merged)} cases -> {cases_path}")
    if needs_review:
        print(f"[protocol-test-assets] needs_review={len(needs_review)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

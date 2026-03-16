#!/usr/bin/env python3
"""Generate API test design assets from an OpenAPI specification.

Outputs:
- machine-readable test cases JSON
- test matrix JSON
- property/fuzz scenario JSON
- TestRail-compatible CSV
- Zephyr-compatible JSON
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}


@dataclass
class Operation:
    method: str
    path: str
    operation_id: str
    summary: str
    tags: list[str]
    request_schema: dict[str, Any] | None
    responses: dict[str, Any]
    parameters: list[dict[str, Any]]
    security_required: bool


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"OpenAPI file must be a mapping: {path}")
    return payload


def _resolve_pointer(document: Any, pointer: str) -> Any:
    current = document
    for token in pointer.lstrip("/").split("/"):
        if not token:
            continue
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            current = current[token]
        elif isinstance(current, list):
            current = current[int(token)]
        else:
            raise KeyError(f"Invalid pointer segment: {token}")
    return current


def _resolve_ref(ref: str, *, root_doc: dict[str, Any], current_file: Path) -> Any:
    ref_file, _, fragment = ref.partition("#")
    if ref_file:
        target_file = (current_file.parent / ref_file).resolve()
        target_doc = _load_yaml(target_file)
        if not fragment:
            return target_doc
        return _resolve_pointer(target_doc, fragment)
    if not fragment:
        return root_doc
    return _resolve_pointer(root_doc, fragment)


def _resolve_schema(schema: dict[str, Any], *, root_doc: dict[str, Any], current_file: Path) -> dict[str, Any]:
    if "$ref" in schema and isinstance(schema["$ref"], str):
        resolved = _resolve_ref(schema["$ref"], root_doc=root_doc, current_file=current_file)
        if isinstance(resolved, dict):
            return resolved
        return {}
    return schema


def _extract_request_schema(operation: dict[str, Any], *, root_doc: dict[str, Any], current_file: Path) -> dict[str, Any] | None:
    request_body = operation.get("requestBody")
    if isinstance(request_body, dict) and "$ref" in request_body:
        resolved = _resolve_ref(str(request_body["$ref"]), root_doc=root_doc, current_file=current_file)
        if isinstance(resolved, dict):
            request_body = resolved
    if not isinstance(request_body, dict):
        return None
    content = request_body.get("content")
    if not isinstance(content, dict):
        return None
    media = content.get("application/json") or next(iter(content.values()), None)
    if not isinstance(media, dict):
        return None
    schema = media.get("schema")
    if not isinstance(schema, dict):
        return None
    return _resolve_schema(schema, root_doc=root_doc, current_file=current_file)


def _extract_operations(spec_path: Path) -> list[Operation]:
    root_doc = _load_yaml(spec_path)
    paths = root_doc.get("paths", {})
    if not isinstance(paths, dict):
        return []

    operations: list[Operation] = []
    for path_name, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        if "$ref" in path_item and isinstance(path_item["$ref"], str):
            resolved = _resolve_ref(path_item["$ref"], root_doc=root_doc, current_file=spec_path)
            path_item = resolved if isinstance(resolved, dict) else {}

        path_params = path_item.get("parameters", [])
        if not isinstance(path_params, list):
            path_params = []

        for method, op in path_item.items():
            method_l = method.lower()
            if method_l not in HTTP_METHODS or not isinstance(op, dict):
                continue
            if "$ref" in op and isinstance(op["$ref"], str):
                resolved = _resolve_ref(op["$ref"], root_doc=root_doc, current_file=spec_path)
                op = resolved if isinstance(resolved, dict) else {}

            op_id = str(op.get("operationId", f"{method_l}_{path_name.strip('/').replace('/', '_') or 'root'}"))
            summary = str(op.get("summary", "")).strip() or f"{method.upper()} {path_name}"
            tags = [str(tag) for tag in (op.get("tags") or []) if isinstance(tag, str)]
            responses = op.get("responses") if isinstance(op.get("responses"), dict) else {}
            security_required = "security" in op or bool(root_doc.get("security"))
            op_params = op.get("parameters") if isinstance(op.get("parameters"), list) else []
            params = [*path_params, *op_params]
            request_schema = _extract_request_schema(op, root_doc=root_doc, current_file=spec_path)
            operations.append(
                Operation(
                    method=method_l,
                    path=str(path_name),
                    operation_id=op_id,
                    summary=summary,
                    tags=tags,
                    request_schema=request_schema,
                    responses=responses if isinstance(responses, dict) else {},
                    parameters=[p for p in params if isinstance(p, dict)],
                    security_required=security_required,
                )
            )
    return operations


def _response_codes(operation: Operation) -> set[str]:
    return {str(code) for code in operation.responses.keys()}


def _build_steps(operation: Operation, scenario: str) -> list[str]:
    steps = [
        f"Set base URL to sandbox endpoint for {operation.operation_id}.",
        f"Prepare {operation.method.upper()} request for {operation.path}.",
    ]
    if scenario == "positive":
        steps.append("Send request with valid payload and required headers.")
    elif scenario == "auth_negative":
        steps.append("Send request without auth token or with invalid token.")
    elif scenario == "validation_negative":
        steps.append("Send request with invalid payload shape or missing required field.")
    elif scenario == "not_found_negative":
        steps.append("Send request with non-existent resource identifier.")
    else:
        steps.append("Send request with malformed values and verify rejection.")
    return steps


def _build_expected(operation: Operation, scenario: str) -> str:
    if scenario == "positive":
        success_codes = [code for code in _response_codes(operation) if code.startswith(("2", "3"))]
        code = sorted(success_codes)[0] if success_codes else "2xx"
        return f"Response status is {code} and payload matches OpenAPI response schema."
    if scenario == "auth_negative":
        return "Response status is 401 or 403, and error envelope matches documented schema."
    if scenario == "validation_negative":
        return "Response status is 400 or 422, and validation errors are returned."
    if scenario == "not_found_negative":
        return "Response status is 404 with not-found error envelope."
    return "Response status is 4xx and service remains stable without schema violations."


def _scenario_catalog(operation: Operation) -> list[str]:
    scenarios = ["positive"]
    codes = _response_codes(operation)
    if operation.security_required or "401" in codes or "403" in codes:
        scenarios.append("auth_negative")
    if "400" in codes or "422" in codes or operation.request_schema is not None:
        scenarios.append("validation_negative")
    if "404" in codes or "{" in operation.path:
        scenarios.append("not_found_negative")
    scenarios.append("fuzz_negative")
    return scenarios


def _build_test_cases(operations: list[Operation]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for op in operations:
        for scenario in _scenario_catalog(op):
            case_id = f"TC-{op.operation_id}-{scenario}".replace("_", "-")
            cases.append(
                {
                    "id": case_id,
                    "title": f"{op.operation_id}: {scenario.replace('_', ' ')}",
                    "suite": (op.tags[0] if op.tags else "General API"),
                    "operation_id": op.operation_id,
                    "traceability": {
                        "method": op.method.upper(),
                        "path": op.path,
                        "operation_id": op.operation_id,
                    },
                    "preconditions": [
                        "Sandbox endpoint is available.",
                        "OpenAPI contract version matches deployed mock.",
                    ],
                    "steps": _build_steps(op, scenario),
                    "expected_result": _build_expected(op, scenario),
                    "priority": "high" if scenario in {"positive", "auth_negative"} else "medium",
                    "type": "functional" if scenario != "fuzz_negative" else "fuzz",
                }
            )
    return cases


def _build_property_scenarios(operations: list[Operation]) -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []
    for op in operations:
        properties: list[str] = []
        for param in op.parameters:
            schema = param.get("schema") if isinstance(param.get("schema"), dict) else {}
            name = str(param.get("name", "param"))
            if "minimum" in schema or "maximum" in schema:
                properties.append(f"{name} respects numeric boundary constraints.")
            if schema.get("type") == "string" and schema.get("maxLength"):
                properties.append(f"{name} enforces maxLength={schema.get('maxLength')}.")
        if op.request_schema and op.request_schema.get("type") == "object":
            req_required = op.request_schema.get("required")
            if isinstance(req_required, list) and req_required:
                properties.append("Request body rejects payloads missing required fields.")
        if properties:
            scenarios.append(
                {
                    "operation_id": op.operation_id,
                    "method": op.method.upper(),
                    "path": op.path,
                    "properties": properties,
                }
            )
    return scenarios


def _build_test_matrix(operations: list[Operation], cases: list[dict[str, Any]]) -> dict[str, Any]:
    by_operation: dict[str, dict[str, Any]] = {}
    for op in operations:
        by_operation[op.operation_id] = {
            "method": op.method.upper(),
            "path": op.path,
            "suite": op.tags[0] if op.tags else "General API",
            "cases": [],
        }
    for case in cases:
        op_id = str(case["operation_id"])
        if op_id in by_operation:
            by_operation[op_id]["cases"].append(case["id"])
    return {
        "summary": {
            "operations": len(operations),
            "test_cases": len(cases),
            "coverage_ratio": round((len(by_operation) / len(operations)) if operations else 0.0, 3),
        },
        "operations": list(by_operation.values()),
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_testrail_csv(path: Path, cases: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "Title",
                "Section",
                "Type",
                "Priority",
                "Preconditions",
                "Steps",
                "Expected Result",
                "Refs",
            ],
        )
        writer.writeheader()
        for case in cases:
            writer.writerow(
                {
                    "Title": case["title"],
                    "Section": case["suite"],
                    "Type": case["type"],
                    "Priority": case["priority"],
                    "Preconditions": "\n".join(case["preconditions"]),
                    "Steps": "\n".join(case["steps"]),
                    "Expected Result": case["expected_result"],
                    "Refs": f"{case['traceability']['method']} {case['traceability']['path']} ({case['operation_id']})",
                }
            )


def _build_zephyr_payload(cases: list[dict[str, Any]]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    for case in cases:
        issues.append(
            {
                "summary": case["title"],
                "description": "\n".join(
                    [
                        f"Operation: {case['traceability']['method']} {case['traceability']['path']}",
                        f"Operation ID: {case['operation_id']}",
                        "",
                        "Preconditions:",
                        *case["preconditions"],
                        "",
                        "Steps:",
                        *[f"- {step}" for step in case["steps"]],
                        "",
                        f"Expected: {case['expected_result']}",
                    ]
                ),
                "labels": ["api-first", "auto-generated", case["type"]],
                "priority": case["priority"],
                "suite": case["suite"],
            }
        )
    return {"issues": issues, "count": len(issues)}


def generate_assets(spec_path: Path, output_dir: Path, testrail_csv: Path, zephyr_json: Path) -> dict[str, Any]:
    operations = _extract_operations(spec_path)
    cases = _build_test_cases(operations)
    matrix = _build_test_matrix(operations, cases)
    property_scenarios = _build_property_scenarios(operations)

    assets = {
        "spec_path": str(spec_path),
        "operations_count": len(operations),
        "test_cases_count": len(cases),
        "property_scenarios_count": len(property_scenarios),
    }

    _write_json(output_dir / "api_test_cases.json", {"cases": cases, "summary": assets})
    _write_json(output_dir / "api_test_matrix.json", matrix)
    _write_json(output_dir / "api_property_fuzz_scenarios.json", {"scenarios": property_scenarios})
    _write_testrail_csv(testrail_csv, cases)
    _write_json(zephyr_json, _build_zephyr_payload(cases))
    _write_json(output_dir / "api_test_assets_report.json", assets)
    return assets


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate API test assets from OpenAPI")
    parser.add_argument("--spec", required=True, help="Path to root OpenAPI spec")
    parser.add_argument("--output-dir", default="reports/api-test-assets")
    parser.add_argument("--testrail-csv", default="reports/api-test-assets/testrail_test_cases.csv")
    parser.add_argument("--zephyr-json", default="reports/api-test-assets/zephyr_test_cases.json")
    args = parser.parse_args()

    spec_path = Path(args.spec).resolve()
    if not spec_path.exists():
        raise FileNotFoundError(f"Spec does not exist: {spec_path}")

    output_dir = Path(args.output_dir).resolve()
    testrail_csv = Path(args.testrail_csv).resolve()
    zephyr_json = Path(args.zephyr_json).resolve()

    assets = generate_assets(spec_path, output_dir, testrail_csv, zephyr_json)
    print(
        "Generated API test assets: "
        f"operations={assets['operations_count']} "
        f"cases={assets['test_cases_count']} "
        f"property_scenarios={assets['property_scenarios_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

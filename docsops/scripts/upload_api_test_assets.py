#!/usr/bin/env python3
"""Upload generated API test assets to TestRail and Zephyr Scale.

The script is safe by default:
- skips provider upload when required credentials are missing
- can run in strict mode to fail pipeline on upload errors
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.env_loader import load_local_env


def _read_env(name: str) -> str:
    return os.environ.get(name, "").strip()


def _http_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = None
    req_headers = {"Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        req_headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url=url, method=method, data=body, headers=req_headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {error.code} for {url}: {details or error.reason}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Network error for {url}: {error.reason}") from error

    parsed = json.loads(raw or "{}")
    if not isinstance(parsed, dict):
        raise RuntimeError(f"Unexpected JSON response from {url}")
    return parsed


def _load_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return []
    cases = payload.get("cases", [])
    if not isinstance(cases, list):
        return []
    return [case for case in cases if isinstance(case, dict)]


def _testrail_headers(email: str, api_key: str) -> dict[str, str]:
    raw = f"{email}:{api_key}".encode("utf-8")
    token = base64.b64encode(raw).decode("ascii")
    return {"Authorization": f"Basic {token}"}


def _upload_testrail(
    *,
    base_url: str,
    email: str,
    api_key: str,
    section_id: str,
    suite_id: str,
    cases: list[dict[str, Any]],
    preconds_field: str,
    steps_field: str,
    expected_field: str,
) -> dict[str, Any]:
    headers = _testrail_headers(email, api_key)
    section_url = f"{base_url.rstrip('/')}/index.php?/api/v2/add_case/{section_id}"
    if suite_id:
        section_url = f"{section_url}&{urllib.parse.urlencode({'suite_id': suite_id})}"

    created = 0
    errors: list[str] = []
    for case in cases:
        title = str(case.get("title", "")).strip()
        if not title:
            continue
        payload: dict[str, Any] = {"title": title}
        payload[preconds_field] = "\n".join(str(item) for item in case.get("preconditions", []))
        payload[steps_field] = "\n".join(f"{idx + 1}. {step}" for idx, step in enumerate(case.get("steps", [])))
        payload[expected_field] = str(case.get("expected_result", ""))
        refs = case.get("traceability", {})
        if isinstance(refs, dict):
            method = str(refs.get("method", "")).strip()
            path = str(refs.get("path", "")).strip()
            op_id = str(case.get("operation_id", "")).strip()
            payload["refs"] = ", ".join([item for item in [f"{method} {path}".strip(), op_id] if item]).strip(", ")
        if case.get("needs_review"):
            payload["custom_needs_review"] = True

        try:
            _http_json("POST", section_url, headers=headers, payload=payload)
            created += 1
        except (RuntimeError, ValueError, TypeError, OSError) as error:  # noqa: BLE001
            # Fallback for TestRail instances without custom fields configured.
            try:
                _http_json("POST", section_url, headers=headers, payload={"title": title})
                created += 1
            except (RuntimeError, ValueError, TypeError, OSError) as fallback_error:  # noqa: BLE001
                errors.append(f"{title}: {error}; fallback failed: {fallback_error}")
    return {"provider": "testrail", "created": created, "errors": errors}


def _upload_zephyr_scale(
    *,
    base_url: str,
    api_token: str,
    project_key: str,
    folder_id: str,
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {api_token}"}
    endpoint = f"{base_url.rstrip('/')}/testcases"

    created = 0
    errors: list[str] = []
    for case in cases:
        title = str(case.get("title", "")).strip()
        if not title:
            continue
        objective = str(case.get("expected_result", "")).strip()
        preconditions = "\n".join(str(item) for item in case.get("preconditions", []))
        steps = [{"inline": {"description": str(step), "expectedResult": objective}} for step in case.get("steps", [])]
        labels = ["api-first", "auto-generated"]
        if case.get("needs_review"):
            labels.append("needs-review")
        payload: dict[str, Any] = {
            "projectKey": project_key,
            "name": title,
            "objective": objective,
            "precondition": preconditions,
            "labels": labels,
            "statusName": "Draft",
            "priorityName": "Normal",
            "testScript": {"type": "STEP_BY_STEP", "steps": steps},
        }
        if folder_id:
            payload["folder"] = {"id": folder_id}
        try:
            _http_json("POST", endpoint, headers=headers, payload=payload)
            created += 1
        except (RuntimeError, ValueError, TypeError, OSError) as error:  # noqa: BLE001
            errors.append(f"{title}: {error}")
    return {"provider": "zephyr_scale", "created": created, "errors": errors}


def main() -> int:
    load_local_env(REPO_ROOT)
    parser = argparse.ArgumentParser(description="Upload generated API test assets to TestRail/Zephyr")
    parser.add_argument("--cases-json", default="reports/api-test-assets/api_test_cases.json")
    parser.add_argument("--report", default="reports/api-test-assets/upload_report.json")
    parser.add_argument("--strict", action="store_true")

    parser.add_argument("--testrail-enabled-env", default="TESTRAIL_UPLOAD_ENABLED")
    parser.add_argument("--testrail-base-url-env", default="TESTRAIL_BASE_URL")
    parser.add_argument("--testrail-email-env", default="TESTRAIL_EMAIL")
    parser.add_argument("--testrail-api-key-env", default="TESTRAIL_API_KEY")
    parser.add_argument("--testrail-section-id-env", default="TESTRAIL_SECTION_ID")
    parser.add_argument("--testrail-suite-id-env", default="TESTRAIL_SUITE_ID")
    parser.add_argument("--testrail-preconds-field", default="custom_preconds")
    parser.add_argument("--testrail-steps-field", default="custom_steps")
    parser.add_argument("--testrail-expected-field", default="custom_expected")

    parser.add_argument("--zephyr-enabled-env", default="ZEPHYR_UPLOAD_ENABLED")
    parser.add_argument("--zephyr-base-url-env", default="ZEPHYR_SCALE_BASE_URL")
    parser.add_argument("--zephyr-token-env", default="ZEPHYR_SCALE_API_TOKEN")
    parser.add_argument("--zephyr-project-key-env", default="ZEPHYR_SCALE_PROJECT_KEY")
    parser.add_argument("--zephyr-folder-id-env", default="ZEPHYR_SCALE_FOLDER_ID")
    args = parser.parse_args()

    cases_path = Path(args.cases_json)
    if not cases_path.exists():
        raise FileNotFoundError(f"Cases JSON is missing: {cases_path}")
    cases = _load_cases(cases_path)

    results: list[dict[str, Any]] = []
    failures: list[str] = []

    testrail_enabled = _read_env(args.testrail_enabled_env).lower() in {"1", "true", "yes", "on"}
    if testrail_enabled:
        testrail_base = _read_env(args.testrail_base_url_env)
        testrail_email = _read_env(args.testrail_email_env)
        testrail_key = _read_env(args.testrail_api_key_env)
        testrail_section = _read_env(args.testrail_section_id_env)
        testrail_suite = _read_env(args.testrail_suite_id_env)
        missing = [
            name
            for name, value in [
                (args.testrail_base_url_env, testrail_base),
                (args.testrail_email_env, testrail_email),
                (args.testrail_api_key_env, testrail_key),
                (args.testrail_section_id_env, testrail_section),
            ]
            if not value
        ]
        if missing:
            failures.append(f"TestRail upload enabled but missing env vars: {', '.join(missing)}")
        else:
            results.append(
                _upload_testrail(
                    base_url=testrail_base,
                    email=testrail_email,
                    api_key=testrail_key,
                    section_id=testrail_section,
                    suite_id=testrail_suite,
                    cases=cases,
                    preconds_field=args.testrail_preconds_field,
                    steps_field=args.testrail_steps_field,
                    expected_field=args.testrail_expected_field,
                )
            )
    else:
        results.append({"provider": "testrail", "skipped": True, "reason": "upload disabled"})

    zephyr_enabled = _read_env(args.zephyr_enabled_env).lower() in {"1", "true", "yes", "on"}
    if zephyr_enabled:
        zephyr_base = _read_env(args.zephyr_base_url_env) or "https://api.zephyrscale.smartbear.com/v2"
        zephyr_token = _read_env(args.zephyr_token_env)
        zephyr_project = _read_env(args.zephyr_project_key_env)
        zephyr_folder = _read_env(args.zephyr_folder_id_env)
        missing = [
            name
            for name, value in [
                (args.zephyr_token_env, zephyr_token),
                (args.zephyr_project_key_env, zephyr_project),
            ]
            if not value
        ]
        if missing:
            failures.append(f"Zephyr upload enabled but missing env vars: {', '.join(missing)}")
        else:
            results.append(
                _upload_zephyr_scale(
                    base_url=zephyr_base,
                    api_token=zephyr_token,
                    project_key=zephyr_project,
                    folder_id=zephyr_folder,
                    cases=cases,
                )
            )
    else:
        results.append({"provider": "zephyr_scale", "skipped": True, "reason": "upload disabled"})

    all_errors: list[str] = []
    for item in results:
        if isinstance(item, dict):
            errs = item.get("errors")
            if isinstance(errs, list):
                all_errors.extend(str(err) for err in errs)
    all_errors.extend(failures)

    report = {
        "cases_source": str(cases_path),
        "cases_count": len(cases),
        "results": results,
        "failures": failures,
        "error_count": len(all_errors),
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    for result in results:
        provider = str(result.get("provider", "unknown"))
        if result.get("skipped"):
            print(f"{provider}: skipped ({result.get('reason', 'unknown')})")
            continue
        print(f"{provider}: created={result.get('created', 0)} errors={len(result.get('errors', []))}")

    if all_errors:
        print(f"Upload completed with {len(all_errors)} error(s). Report: {report_path}")
        if args.strict:
            return 1
    else:
        print(f"Upload completed successfully. Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run full multi-protocol docs-ops flow for selected API architectures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.env_loader import load_local_env
from scripts.api_protocols import apply_realtime_sandbox_defaults, merge_protocol_settings, normalize_protocols
from scripts.multi_protocol_engine import ProtocolAdapter, StageResult


def _read_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return payload


def _result_to_json(result: StageResult) -> dict[str, Any]:
    return {
        "stage": result.stage,
        "protocol": result.protocol,
        "ok": result.ok,
        "rc": result.rc,
        "command": result.command,
        "details": result.details,
    }


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    load_local_env(REPO_ROOT)
    parser = argparse.ArgumentParser(description="Run multi-protocol docs-ops flow")
    parser.add_argument("--runtime-config", default="docsops/config/client_runtime.yml")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--protocols", default="")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--strictness", choices=["standard", "enterprise-strict"], default="")
    parser.add_argument("--generate-test-assets", action="store_true")
    parser.add_argument("--upload-test-assets", action="store_true")
    parser.add_argument("--skip-publish", action="store_true")
    args = parser.parse_args()

    runtime_path = Path(args.runtime_config)
    if not runtime_path.is_absolute():
        runtime_path = (Path.cwd() / runtime_path).resolve()
    runtime = _read_yaml(runtime_path)

    runtime_protocols = runtime.get("api_protocols", ["rest"])
    requested_protocols = args.protocols if args.protocols else runtime_protocols
    protocols = normalize_protocols(requested_protocols)

    governance = runtime.get("api_governance", {})
    strictness = args.strictness or str(governance.get("strictness", "standard")).strip().lower() or "standard"
    strict_mode = bool(args.strict or strictness == "enterprise-strict")

    settings_map = merge_protocol_settings(runtime.get("api_protocol_settings", {}), protocols)
    settings_map = apply_realtime_sandbox_defaults(settings_map)
    reports_dir = Path(args.reports_dir)
    if not reports_dir.is_absolute():
        reports_dir = (Path.cwd() / reports_dir).resolve()
    reports_dir.mkdir(parents=True, exist_ok=True)

    all_results: list[StageResult] = []
    protocol_results: dict[str, list[dict[str, Any]]] = {}
    failed_protocols: list[str] = []

    repo_root = Path.cwd()
    scripts_dir = Path(__file__).resolve().parent

    for protocol in protocols:
        settings = settings_map.get(protocol, {})
        if not bool(settings.get("enabled", protocol in protocols)):
            continue

        adapter = ProtocolAdapter(protocol, settings, repo_root=repo_root, scripts_dir=scripts_dir)
        per_protocol: list[StageResult] = []
        protocol_failed = False
        autofix_enabled = bool(settings.get("autofix_cycle_enabled", True))
        try:
            max_attempts = max(1, int(settings.get("autofix_max_attempts", 3)))
        except Exception:  # noqa: BLE001
            max_attempts = 3

        try:
            attempt = 1
            while True:
                attempt_results: list[StageResult] = []
                notes_gen = adapter.maybe_generate_contract_from_notes(allow_fail=True)
                if notes_gen is not None:
                    attempt_results.append(notes_gen)
                attempt_results.append(adapter.ingest(allow_fail=True))
                attempt_results.append(adapter.contract_validation(allow_fail=True))
                attempt_results.append(adapter.lint(allow_fail=True))
                attempt_results.append(adapter.regression(allow_fail=True))
                docs_result = adapter.docs_generation(allow_fail=True)
                attempt_results.append(docs_result)
                generated_doc = str(docs_result.details.get("generated_doc", ""))
                attempt_results.extend(adapter.quality_gates(allow_fail=True, generated_doc=generated_doc))

                should_generate_assets = args.generate_test_assets or bool(settings.get("generate_test_assets", False))
                if should_generate_assets:
                    assets_result = adapter.test_assets(allow_fail=True)
                    attempt_results.append(assets_result)
                    should_upload = args.upload_test_assets or bool(settings.get("upload_test_assets", False))
                    if should_upload:
                        attempt_results.append(adapter.upload(allow_fail=True))

                if not args.skip_publish:
                    attempt_results.append(adapter.publish(allow_fail=True, generated_doc=generated_doc))

                for result in attempt_results:
                    result.details["attempt"] = attempt
                per_protocol.extend(attempt_results)

                attempt_failed = any(not result.ok for result in attempt_results)
                if not attempt_failed:
                    break
                if not autofix_enabled or attempt >= max_attempts:
                    protocol_failed = True
                    break

                per_protocol.append(
                    StageResult(
                        stage="autofix_retry",
                        protocol=protocol,
                        ok=True,
                        rc=0,
                        command=["auto-retry", str(attempt + 1)],
                        details={
                            "attempt": attempt,
                            "next_attempt": attempt + 1,
                            "max_attempts": max_attempts,
                            "reason": "one or more stages failed; retrying full protocol flow",
                        },
                    )
                )
                attempt += 1
        except Exception as error:  # noqa: BLE001
            protocol_failed = True
            per_protocol.append(
                StageResult(
                    stage="exception",
                    protocol=protocol,
                    ok=False,
                    rc=1,
                    command=[],
                    details={"error": str(error)},
                )
            )

        if any(not result.ok for result in per_protocol):
            protocol_failed = True
        if protocol_failed:
            failed_protocols.append(protocol)

        all_results.extend(per_protocol)
        protocol_results[protocol] = [_result_to_json(item) for item in per_protocol]

        if protocol_failed and strict_mode:
            break

    report = {
        "strictness": strictness,
        "strict_mode": strict_mode,
        "protocols": protocols,
        "failed_protocols": failed_protocols,
        "failed": bool(failed_protocols),
        "stages": [_result_to_json(item) for item in all_results],
        "by_protocol": protocol_results,
    }

    report_path = reports_dir / "multi_protocol_contract_report.json"
    _write_report(report_path, report)
    print(f"[multi-protocol] report: {report_path}")

    if strict_mode and failed_protocols:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

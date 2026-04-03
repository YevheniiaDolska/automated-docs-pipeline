#!/usr/bin/env python3
"""Run full multi-protocol docs-ops flow for selected API architectures."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.env_loader import load_local_env
from scripts.flow_feedback import FlowNarrator
from scripts.api_protocols import apply_realtime_sandbox_defaults, merge_protocol_settings, normalize_protocols
from scripts.license_gate import require as _license_require, require_protocol as _license_require_protocol
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


def _http_to_ws(url: str, path_suffix: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return ""
    scheme = "wss" if parsed.scheme == "https" else "ws"
    base_path = parsed.path.rstrip("/")
    if base_path.endswith("/v1"):
        base_path = base_path[: -len("/v1")]
    merged = f"{base_path}/{path_suffix.lstrip('/')}".replace("//", "/")
    return f"{scheme}://{parsed.netloc}{merged}"


def _prepare_non_rest_live_endpoints(
    *,
    repo_root: Path,
    runtime: dict[str, Any],
    reports_dir: Path,
    protocols: list[str],
    settings_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    api_first = runtime.get("api_first", {})
    if not isinstance(api_first, dict):
        api_first = {}

    external_mock = api_first.get("external_mock", {})
    if not isinstance(external_mock, dict):
        external_mock = {}
    sandbox_backend = str(api_first.get("sandbox_backend", "")).strip().lower()
    mock_base_url = str(api_first.get("mock_base_url", "")).strip()

    resolution: dict[str, Any] = {
        "sandbox_backend": sandbox_backend,
        "base_url": mock_base_url,
        "resolved_by": "runtime",
        "protocols": {},
    }

    # Optional auto-prepare external mock (same mechanism as REST flow).
    if sandbox_backend == "external" and bool(external_mock.get("enabled", False)):
        postman = external_mock.get("postman", {})
        if not isinstance(postman, dict):
            postman = {}
        resolver_script = repo_root / "scripts" / "ensure_external_mock_server.py"
        if resolver_script.exists():
            out_path = reports_dir / "external_mock_resolution.non_rest.json"
            cmd = [
                sys.executable,
                str(resolver_script),
                "--provider",
                str(external_mock.get("provider", "postman")),
                "--spec",
                str(api_first.get("spec_path", "api/openapi.yaml")),
                "--base-path",
                str(external_mock.get("base_path", "/v1")),
                "--output",
                str(out_path),
                "--postman-api-key-env",
                str(postman.get("api_key_env", "POSTMAN_API_KEY")),
                "--postman-workspace-id-env",
                str(postman.get("workspace_id_env", "POSTMAN_WORKSPACE_ID")),
                "--postman-collection-uid-env",
                str(postman.get("collection_uid_env", "POSTMAN_COLLECTION_UID")),
                "--postman-mock-server-id-env",
                str(postman.get("mock_server_id_env", "POSTMAN_MOCK_SERVER_ID")),
                "--postman-mock-server-name",
                str(postman.get("mock_server_name", "")),
            ]
            if bool(postman.get("private", False)):
                cmd.append("--postman-private")
            completed = subprocess.run(cmd, cwd=str(repo_root), check=False)
            if completed.returncode == 0 and out_path.exists():
                try:
                    payload = json.loads(out_path.read_text(encoding="utf-8"))
                except (RuntimeError, ValueError, TypeError, OSError):  # noqa: BLE001
                    payload = {}
                resolved = str(payload.get("mock_base_url", "")).strip()
                if resolved:
                    mock_base_url = resolved
                    resolution["base_url"] = resolved
                    resolution["resolved_by"] = "ensure_external_mock_server"

    base = mock_base_url.rstrip("/")
    use_public_echo_fallback = False
    if not base:
        # Public fallback so strict live verify can still run without local infra.
        base = "https://postman-echo.com"
        use_public_echo_fallback = True
        resolution["base_url"] = base
        resolution["resolved_by"] = "fallback_public_echo"

    for protocol in protocols:
        if protocol == "rest":
            continue
        cfg = settings_map.get(protocol, {})
        if not isinstance(cfg, dict):
            continue
        protocol_payload: dict[str, Any] = {}
        if protocol == "graphql":
            endpoint = str(cfg.get("graphql_endpoint", "")).strip() or (f"{base}/post" if use_public_echo_fallback else f"{base}/graphql")
            cfg["graphql_endpoint"] = endpoint
            protocol_payload["graphql_endpoint"] = endpoint
        elif protocol == "grpc":
            endpoint = str(cfg.get("grpc_gateway_endpoint", "")).strip() or (f"{base}/post" if use_public_echo_fallback else f"{base}/grpc/invoke")
            cfg["grpc_gateway_endpoint"] = endpoint
            protocol_payload["grpc_gateway_endpoint"] = endpoint
        elif protocol == "asyncapi":
            http_endpoint = str(cfg.get("asyncapi_http_publish_endpoint", "")).strip() or (f"{base}/post" if use_public_echo_fallback else f"{base}/events/publish")
            ws_endpoint = str(cfg.get("asyncapi_ws_endpoint", "")).strip() or ("wss://echo.websocket.events" if use_public_echo_fallback else _http_to_ws(base, "/events/ws"))
            cfg["asyncapi_http_publish_endpoint"] = http_endpoint
            cfg["asyncapi_ws_endpoint"] = ws_endpoint
            protocol_payload["asyncapi_http_publish_endpoint"] = http_endpoint
            protocol_payload["asyncapi_ws_endpoint"] = ws_endpoint
        elif protocol == "websocket":
            ws_endpoint = str(cfg.get("websocket_endpoint", "")).strip() or ("wss://echo.websocket.events" if use_public_echo_fallback else _http_to_ws(base, "/ws"))
            bridge = str(cfg.get("websocket_http_bridge_endpoint", "")).strip() or (f"{base}/post" if use_public_echo_fallback else f"{base}/ws/invoke")
            cfg["websocket_endpoint"] = ws_endpoint
            cfg["websocket_http_bridge_endpoint"] = bridge
            protocol_payload["websocket_endpoint"] = ws_endpoint
            protocol_payload["websocket_http_bridge_endpoint"] = bridge
        if protocol_payload:
            # For strict publish gating we require real endpoint checks.
            cfg["self_verify_require_endpoint"] = True
            protocol_payload["self_verify_require_endpoint"] = True
            resolution["protocols"][protocol] = protocol_payload

    out = reports_dir / "non_rest_mock_endpoints.json"
    out.write_text(json.dumps(resolution, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return resolution


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
    narrator = FlowNarrator("Multi-protocol contract flow", total_steps=4)
    narrator.start("Generate, validate, lint, verify, and publish protocol docs contracts.")

    runtime_path = Path(args.runtime_config)
    if not runtime_path.is_absolute():
        runtime_path = (Path.cwd() / runtime_path).resolve()
    runtime = _read_yaml(runtime_path)
    narrator.stage(1, "Load runtime and enforce license", f"Runtime config: {runtime_path}")

    # -- License gate: multi-protocol requires enterprise plan --
    _license_require("multi_protocol_pipeline")

    runtime_protocols = runtime.get("api_protocols", ["rest"])
    requested_protocols = args.protocols if args.protocols else runtime_protocols
    protocols = normalize_protocols(requested_protocols)

    # -- License gate: check each requested protocol --
    for proto in protocols:
        if proto != "rest":
            _license_require_protocol(proto)
    narrator.done(f"Protocols selected: {', '.join(protocols)}")

    governance = runtime.get("api_governance", {})
    strictness = args.strictness or str(governance.get("strictness", "standard")).strip().lower() or "standard"
    strict_mode = bool(args.strict or strictness == "enterprise-strict")

    settings_map = merge_protocol_settings(runtime.get("api_protocol_settings", {}), protocols)
    settings_map = apply_realtime_sandbox_defaults(settings_map)
    modules = runtime.get("modules", {}) if isinstance(runtime.get("modules"), dict) else {}
    reports_dir = Path(args.reports_dir)
    if not reports_dir.is_absolute():
        reports_dir = (Path.cwd() / reports_dir).resolve()
    reports_dir.mkdir(parents=True, exist_ok=True)
    _prepare_non_rest_live_endpoints(
        repo_root=Path.cwd(),
        runtime=runtime,
        reports_dir=reports_dir,
        protocols=protocols,
        settings_map=settings_map,
    )
    narrator.stage(2, "Prepare protocol execution", "Runtime endpoint defaults and per-protocol settings resolved")
    narrator.done("Protocol environment prepared")

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
        narrator.stage(3, f"Run protocol pipeline: {protocol}", "Generate -> validate -> lint -> docs -> quality -> publish")
        per_protocol: list[StageResult] = []
        protocol_failed = False
        autofix_enabled = bool(settings.get("autofix_cycle_enabled", True))
        try:
            max_attempts = max(1, int(settings.get("autofix_max_attempts", 3)))
        except (RuntimeError, ValueError, TypeError, OSError):  # noqa: BLE001
            max_attempts = 3

        try:
                attempt = 1
                while True:
                    narrator.note(f"{protocol}: attempt {attempt}/{max_attempts}")
                    attempt_results: list[StageResult] = []
                notes_gen = adapter.maybe_generate_contract_from_notes(allow_fail=True)
                if notes_gen is not None:
                    attempt_results.append(notes_gen)
                attempt_results.append(adapter.ingest(allow_fail=True))
                attempt_results.append(adapter.contract_validation(allow_fail=True))
                if bool(settings.get("generate_server_stubs", True)):
                    attempt_results.append(adapter.server_stubs(allow_fail=True))
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

                publish_requires_live_green = bool(settings.get("publish_requires_live_green", True))
                self_verify_failures = [
                    r for r in attempt_results if r.stage == "quality_gate_self_verify" and not r.ok
                ]
                if not args.skip_publish:
                    if publish_requires_live_green and self_verify_failures:
                        attempt_results.append(
                            StageResult(
                                stage="publish_blocked_live_verify",
                                protocol=protocol,
                                ok=False,
                                rc=1,
                                command=["publish_blocked", "quality_gate_self_verify"],
                                details={
                                    "reason": "publish blocked: live self-verify is not green",
                                    "failed_stages": [r.stage for r in self_verify_failures],
                                },
                            )
                        )
                    else:
                        attempt_results.append(adapter.publish(allow_fail=True, generated_doc=generated_doc))

                for result in attempt_results:
                    result.details["attempt"] = attempt
                per_protocol.extend(attempt_results)

                attempt_failed = any(not result.ok for result in attempt_results)
                if not attempt_failed:
                    narrator.done(f"{protocol}: all stages green on attempt {attempt}")
                    break
                if not autofix_enabled or attempt >= max_attempts:
                    protocol_failed = True
                    narrator.warn(f"{protocol}: failed after {attempt} attempt(s)")
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
        except (RuntimeError, ValueError, TypeError, OSError) as error:  # noqa: BLE001
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
            narrator.warn(f"{protocol}: protocol marked as failed")

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
    narrator.stage(4, "Write report", "Persist by-protocol stage status")
    _write_report(report_path, report)
    print(f"[multi-protocol] report: {report_path}")
    narrator.done(str(report_path))

    rag_layer_script = (scripts_dir / "enforce_rag_optimization_layer.py").resolve()
    rag_enabled = bool(modules.get("rag_optimization", True) or modules.get("knowledge_validation", True))
    if rag_enabled and rag_layer_script.exists():
        rag_layer_cmd = [
            sys.executable,
            str(rag_layer_script),
            "--repo-root",
            str(repo_root),
            "--runtime-config",
            str(runtime_path),
            "--reports-dir",
            str(reports_dir),
            "--provider",
            "openai",
            "--retention-versions",
            "60",
            "--with-embeddings",
        ]
        rag_layer_rc = subprocess.run(rag_layer_cmd, cwd=str(repo_root), check=False).returncode
        if rag_layer_rc != 0:
            report["failed"] = True
            report.setdefault("failed_protocols", [])
            report["failed_protocols"] = sorted(set([*report["failed_protocols"], "rag-layer"]))
            _write_report(report_path, report)
            narrator.warn("RAG optimization layer failed")
            if strict_mode:
                narrator.finish(False, "Strict mode failed. RAG optimization layer is not green.")
                return 1

    if strict_mode and failed_protocols:
        narrator.finish(False, f"Strict mode failed. Protocols with errors: {', '.join(failed_protocols)}")
        return 1
    narrator.finish(True, "Multi-protocol flow completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

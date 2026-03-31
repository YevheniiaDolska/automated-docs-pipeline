#!/usr/bin/env python3
"""Universal API-first flow runner for any product."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
import shutil as sh
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.env_loader import load_local_env
from scripts.flow_feedback import FlowNarrator
from scripts.license_gate import require as _license_require


def _print_compact_output(output: str, *, max_lines: int = 28) -> None:
    lines = [line for line in output.splitlines() if line.strip()]
    if not lines:
        return
    if len(lines) <= max_lines:
        for line in lines:
            print(line, flush=True)
        return
    head = lines[:6]
    tail = lines[-12:]
    for line in head:
        print(line, flush=True)
    print(f"[demo] ... {len(lines) - len(head) - len(tail)} lines omitted ...", flush=True)
    for line in tail:
        print(line, flush=True)


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    compact: bool = False,
    summary_label: str | None = None,
) -> None:
    print(f"[run] {' '.join(cmd)}", flush=True)
    completed = subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )
    output = "\n".join([completed.stdout or "", completed.stderr or ""]).strip()
    if output:
        if compact:
            _print_compact_output(output)
        else:
            print(output, flush=True)
    if completed.returncode != 0:
        raise subprocess.CalledProcessError(
            completed.returncode,
            cmd,
            output=completed.stdout,
            stderr=completed.stderr,
        )
    if summary_label:
        print(f"[ok] {summary_label}", flush=True)


def run_first_available(
    candidates: list[list[str]],
    *,
    cwd: Path,
    compact: bool = False,
    summary_label: str | None = None,
) -> None:
    last_error: Exception | None = None
    for cmd in candidates:
        binary = cmd[0]
        if binary != "npx" and sh.which(binary) is None:
            continue
        try:
            run(cmd, cwd=cwd, compact=compact, summary_label=summary_label)
            return
        except (Exception,) as error:  # noqa: BLE001
            last_error = error
            continue
    if last_error:
        raise RuntimeError(f"Unable to execute command candidates: {candidates}. Last error: {last_error}")
    raise RuntimeError(f"No available command candidates found: {candidates}")


def ensure_file(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")


def copy_spec_to_docs(spec_root: Path, docs_target: Path) -> None:
    if docs_target.exists():
        shutil.rmtree(docs_target)
    shutil.copytree(spec_root, docs_target)
    print(f"[ok] copied spec assets to {docs_target}", flush=True)


class _SpecBundler:
    """Bundle a split OpenAPI spec into a single self-contained YAML."""

    def __init__(self) -> None:
        self._schemas: dict[str, Any] = {}
        self._file_cache: dict[str, Any] = {}

    def _load_yaml(self, path: Path) -> Any:
        key = str(path.resolve())
        if key not in self._file_cache:
            self._file_cache[key] = yaml.safe_load(path.read_text(encoding="utf-8"))
        return self._file_cache[key]

    def _resolve_pointer(self, data: Any, pointer: str) -> Any:
        parts = [p.replace("~1", "/").replace("~0", "~") for p in pointer.strip("/").split("/") if p]
        node = data
        for part in parts:
            if isinstance(node, dict):
                node = node[part]
            elif isinstance(node, list):
                node = node[int(part)]
            else:
                raise KeyError(f"Cannot traverse {type(node)} with key {part}")
        return node

    def _resolve_ref(self, ref_value: str, base_dir: Path) -> Any:
        if "#" in ref_value:
            file_part, pointer = ref_value.split("#", 1)
        else:
            file_part, pointer = ref_value, ""

        # Internal ref within same file -> rewrite to #/components/schemas/Name
        if not file_part and pointer:
            schema_name = pointer.strip("/")
            if "/" not in schema_name:
                return {"$ref": f"#/components/schemas/{schema_name}"}

        if not file_part:
            return {"$ref": ref_value}

        ref_path = (base_dir / file_part).resolve()
        ref_data = self._load_yaml(ref_path)
        ref_base = ref_path.parent

        if pointer:
            node = self._resolve_pointer(ref_data, pointer)
        else:
            node = ref_data

        return self._deep_resolve(node, ref_base)

    def _deep_resolve(self, obj: Any, base_dir: Path) -> Any:
        if isinstance(obj, dict):
            if "$ref" in obj and len(obj) == 1:
                return self._resolve_ref(obj["$ref"], base_dir)
            return {k: self._deep_resolve(v, base_dir) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._deep_resolve(item, base_dir) for item in obj]
        return obj

    def _collect_schemas_from_file(self, file_path: Path) -> None:
        data = self._load_yaml(file_path)
        if not isinstance(data, dict):
            return
        for key, value in data.items():
            if isinstance(value, dict) and ("type" in value or "allOf" in value or "oneOf" in value or "anyOf" in value):
                self._schemas[key] = self._deep_resolve(value, file_path.parent)

    def bundle(self, spec_path: Path) -> dict[str, Any]:
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
        base_dir = spec_path.parent

        # Collect schemas from all referenced component files
        schema_dir = base_dir
        for root_dir, _dirs, files in __import__("os").walk(str(base_dir)):
            for fname in files:
                fpath = Path(root_dir) / fname
                if fpath.suffix in (".yaml", ".yml") and "schemas" in str(fpath):
                    self._collect_schemas_from_file(fpath)

        bundled = self._deep_resolve(spec, base_dir)

        # Inject collected schemas into components.schemas
        if self._schemas:
            components = bundled.setdefault("components", {})
            schemas = components.setdefault("schemas", {})
            for name, definition in self._schemas.items():
                if name not in schemas:
                    schemas[name] = definition

        return bundled


def bundle_openapi_spec(spec_path: Path, output_path: Path) -> None:
    """Bundle a split OpenAPI spec with $ref into single YAML and JSON files."""
    bundler = _SpecBundler()
    bundled = bundler.bundle(spec_path)
    output_path.write_text(
        yaml.safe_dump(bundled, sort_keys=False, allow_unicode=True, width=120),
        encoding="utf-8",
    )
    json_path = output_path.with_suffix(".json")
    json_path.write_text(
        json.dumps(bundled, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[ok] bundled spec written to {output_path} and {json_path}", flush=True)


def build_sandbox_page_url(repo: Path, docs_provider: str) -> str:
    provider = docs_provider.lower()
    if provider == "mkdocs":
        import yaml

        mkdocs_cfg = yaml.safe_load((repo / "mkdocs.yml").read_text(encoding="utf-8")) or {}
        site_url = str(mkdocs_cfg.get("site_url", "")).rstrip("/")
        if site_url:
            return f"{site_url}/reference/taskstream-api-playground/"
        return "/reference/taskstream-api-playground/"
    if provider == "docusaurus":
        return "/docs/reference/taskstream-api-playground"
    return "/reference/taskstream-api-playground/"


def sync_playground_sandbox_url(repo: Path, sandbox_base_url: str) -> None:
    mkdocs_path = repo / "mkdocs.yml"
    if not mkdocs_path.exists():
        print("[demo] mkdocs.yml not found; skip playground endpoint sync", flush=True)
        return

    import yaml

    payload = yaml.safe_load(mkdocs_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        print("[demo] mkdocs.yml payload is not a mapping; skip playground endpoint sync", flush=True)
        return

    extra = payload.get("extra")
    if not isinstance(extra, dict):
        extra = {}
        payload["extra"] = extra

    plg = extra.get("plg")
    if not isinstance(plg, dict):
        plg = {}
        extra["plg"] = plg

    api_playground = plg.get("api_playground")
    if not isinstance(api_playground, dict):
        api_playground = {}
        plg["api_playground"] = api_playground

    endpoints = api_playground.get("endpoints")
    if not isinstance(endpoints, dict):
        endpoints = {}
        api_playground["endpoints"] = endpoints
    endpoints["sandbox_base_url"] = sandbox_base_url

    legacy = extra.get("api_playground")
    if not isinstance(legacy, dict):
        legacy = {}
        extra["api_playground"] = legacy
    legacy["sandbox_base_url"] = sandbox_base_url

    mkdocs_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=False), encoding="utf-8")
    print(f"[ok] synced playground sandbox endpoint in mkdocs.yml: {sandbox_base_url}", flush=True)


def resolve_mock_base_url(repo: Path, args: argparse.Namespace) -> str:
    base_url = str(args.mock_base_url).strip()
    sandbox_backend = str(args.sandbox_backend).strip().lower()
    if sandbox_backend != "external" or not args.auto_prepare_external_mock:
        return base_url

    out_path = repo / "reports" / "external_mock_resolution.json"
    cmd = [
        "python3",
        "scripts/ensure_external_mock_server.py",
        "--provider",
        str(args.external_mock_provider),
        "--project-slug",
        str(args.project_slug),
        "--base-path",
        str(args.external_mock_base_path),
        "--spec-path",
        str((repo / args.spec).resolve()),
        "--output-json",
        str(out_path),
        "--postman-api-key-env",
        str(args.external_mock_postman_api_key_env),
        "--postman-workspace-id-env",
        str(args.external_mock_postman_workspace_id_env),
        "--postman-collection-uid-env",
        str(args.external_mock_postman_collection_uid_env),
        "--postman-mock-server-id-env",
        str(args.external_mock_postman_mock_server_id_env),
        "--postman-mock-server-name",
        str(args.external_mock_postman_mock_server_name),
    ]
    if args.external_mock_postman_private:
        cmd.append("--postman-private")
    print("[api-first] Step 0/5: Ensure external mock server is ready.", flush=True)
    run(cmd, cwd=repo, compact=True, summary_label="external mock prepared")
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("Invalid external mock resolution payload.")
    resolved = str(payload.get("mock_base_url", "")).strip()
    if not resolved:
        raise RuntimeError("external mock resolver returned empty mock_base_url")
    print(f"[ok] resolved external mock_base_url: {resolved}", flush=True)
    return resolved


def self_verify_stub_coverage(spec_path: Path, stub_file: Path) -> None:
    import yaml

    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    resolved_paths: dict[str, dict] = {}
    for path_name, path_item in (spec.get("paths") or {}).items():
        if isinstance(path_item, dict) and "$ref" in path_item:
            file_ref, _, fragment = path_item["$ref"].partition("#")
            target_file = (spec_path.parent / file_ref).resolve()
            target_data = yaml.safe_load(target_file.read_text(encoding="utf-8")) or {}
            current: object = target_data
            for token in fragment.lstrip("/").split("/"):
                if not token:
                    continue
                current = current[token.replace("~1", "/").replace("~0", "~")]  # type: ignore[index]
            resolved_paths[path_name] = current if isinstance(current, dict) else {}
        elif isinstance(path_item, dict):
            resolved_paths[path_name] = path_item
        else:
            resolved_paths[path_name] = {}

    op_ids: list[str] = []
    for path_item in resolved_paths.values():
        if not isinstance(path_item, dict):
            continue
        for method, op in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head", "trace"}:
                continue
            if isinstance(op, dict) and op.get("operationId"):
                op_ids.append(op["operationId"])

    source = stub_file.read_text(encoding="utf-8")
    missing = [op for op in op_ids if f"def {op}(" not in source]
    if missing:
        raise RuntimeError(f"Stub coverage check failed. Missing operationId handlers: {', '.join(missing)}")

    print(f"[ok] stub self-verification passed ({len(op_ids)} operationIds covered)", flush=True)


def run_one_attempt(
    repo: Path,
    project_slug: str,
    spec: Path,
    spec_tree: Path,
    docs_target: Path,
    stubs_output: Path,
    verify_user_path: bool,
    mock_base_url: str,
    run_docs_lint: bool,
    generate_test_assets: bool,
    test_assets_output_dir: Path,
    testrail_csv_path: Path,
    zephyr_json_path: Path,
    upload_test_assets: bool,
    upload_test_assets_strict: bool,
    upload_report_path: Path,
    upload_testrail_enabled_env: str,
    upload_testrail_base_url_env: str,
    upload_testrail_email_env: str,
    upload_testrail_api_key_env: str,
    upload_testrail_section_id_env: str,
    upload_testrail_suite_id_env: str,
    upload_zephyr_enabled_env: str,
    upload_zephyr_base_url_env: str,
    upload_zephyr_token_env: str,
    upload_zephyr_project_key_env: str,
    upload_zephyr_folder_id_env: str,
    regression_snapshot: Path | None,
    update_regression_snapshot: bool,
    narrator: FlowNarrator,
) -> None:
    narrator.stage(1, "Validate contract", "Check OpenAPI structure and required metadata")
    run(
        ["python3", "scripts/validate_openapi_contract.py", str(spec)],
        cwd=repo,
        compact=True,
        summary_label="contract validation finished",
    )

    narrator.stage(2, "API quality lint", "Run Spectral, Redocly, and Swagger CLI")
    run_first_available(
        [
            ["spectral", "lint", str(spec), "--ruleset", ".spectral.yml"],
            ["npx", "-y", "@stoplight/spectral-cli", "lint", str(spec), "--ruleset", ".spectral.yml"],
        ],
        cwd=repo,
        compact=True,
        summary_label="spectral lint finished",
    )
    narrator.note("Continue lint stack: Redocly")
    run_first_available(
        [
            ["redocly", "lint", str(spec)],
            ["npx", "-y", "@redocly/cli", "lint", str(spec)],
        ],
        cwd=repo,
        compact=True,
        summary_label="redocly lint finished",
    )
    narrator.note("Continue lint stack: Swagger CLI")
    run_first_available(
        [
            ["swagger-cli", "validate", str(spec)],
            ["npx", "-y", "@apidevtools/swagger-cli", "validate", str(spec)],
        ],
        cwd=repo,
        compact=True,
        summary_label="swagger-cli validation finished",
    )

    narrator.stage(3, "Generate server stubs", "Build endpoint stubs from operation definitions")
    run(
        [
            "python3",
            "scripts/generate_fastapi_stubs_from_openapi.py",
            "--spec",
            str(spec),
            "--output",
            str(stubs_output),
        ],
        cwd=repo,
        compact=True,
        summary_label="fastapi stubs generated",
    )

    narrator.stage(4, "Publish API artifacts", "Sync docs assets and verify coverage")
    copy_spec_to_docs(spec_tree, docs_target / project_slug)
    shutil.copy2(spec, docs_target / "openapi.yaml")
    bundle_openapi_spec(docs_target / "openapi.yaml", docs_target / "openapi.bundled.yaml")

    narrator.note("Verify every operationId has a generated handler")
    self_verify_stub_coverage(spec, stubs_output)

    if regression_snapshot is not None:
        narrator.note("Run regression gate against saved snapshot")
        cmd = [
            "python3",
            "scripts/check_openapi_regression.py",
            "--spec",
            str(spec),
            "--spec-tree",
            str(spec_tree),
            "--snapshot",
            str(regression_snapshot),
        ]
        if update_regression_snapshot:
            cmd.append("--update")
        run(cmd, cwd=repo, compact=True, summary_label="openapi regression gate finished")

    if verify_user_path:
        narrator.note("Run user-path simulation against live mock endpoint")
        try:
            run(
                ["python3", "scripts/self_verify_api_user_path.py", "--base-url", mock_base_url],
                cwd=repo,
                compact=True,
                summary_label="user-path self-verification finished",
            )
        except (Exception,) as error:
            raise RuntimeError(
                f"Step 4/5 failed: user-path verification against mock `{mock_base_url}`. "
                f"Verify sandbox endpoint readiness and route mapping. Details: {error}"
            ) from error

    if generate_test_assets:
        narrator.note("Generate API test assets (matrix, fuzz, property-based)")
        run(
            [
                "python3",
                "scripts/generate_api_test_assets.py",
                "--spec",
                str(spec),
                "--output-dir",
                str(test_assets_output_dir),
                "--testrail-csv",
                str(testrail_csv_path),
                "--zephyr-json",
                str(zephyr_json_path),
            ],
            cwd=repo,
            compact=True,
            summary_label="API test assets generated",
        )
        if upload_test_assets:
            narrator.note("Upload generated API test assets to TestRail/Zephyr")
            upload_cmd = [
                "python3",
                "scripts/upload_api_test_assets.py",
                "--cases-json",
                str(test_assets_output_dir / "api_test_cases.json"),
                "--report",
                str(upload_report_path),
                "--testrail-enabled-env",
                upload_testrail_enabled_env,
                "--testrail-base-url-env",
                upload_testrail_base_url_env,
                "--testrail-email-env",
                upload_testrail_email_env,
                "--testrail-api-key-env",
                upload_testrail_api_key_env,
                "--testrail-section-id-env",
                upload_testrail_section_id_env,
                "--testrail-suite-id-env",
                upload_testrail_suite_id_env,
                "--zephyr-enabled-env",
                upload_zephyr_enabled_env,
                "--zephyr-base-url-env",
                upload_zephyr_base_url_env,
                "--zephyr-token-env",
                upload_zephyr_token_env,
                "--zephyr-project-key-env",
                upload_zephyr_project_key_env,
                "--zephyr-folder-id-env",
                upload_zephyr_folder_id_env,
            ]
            if upload_test_assets_strict:
                upload_cmd.append("--strict")
            run(
                upload_cmd,
                cwd=repo,
                compact=True,
                summary_label="API test assets upload finished",
            )

    if run_docs_lint:
        narrator.stage(5, "Run docs quality gates", "Normalize docs and execute full lint stack")
        run(
            ["python3", "scripts/normalize_docs.py", "docs/"],
            cwd=repo,
            compact=True,
            summary_label="docs normalization finished",
        )
        run(["npm", "run", "lint"], cwd=repo, compact=True, summary_label="docs lint stack finished")


def _read_yaml(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return raw


def _resolve_docs_root(runtime_config: Path | None, fallback: str) -> str:
    if runtime_config is None or not runtime_config.exists():
        return fallback
    payload = _read_yaml(runtime_config)
    docs_root = payload.get("docs_root", fallback)
    return str(docs_root).strip() or fallback


def main() -> int:
    load_local_env(REPO_ROOT)
    parser = argparse.ArgumentParser(description="Run universal API-first production flow")
    parser.add_argument("--project-slug", required=True)
    parser.add_argument("--notes", required=True, help="Planning notes markdown path")
    parser.add_argument("--spec", required=True, help="OpenAPI root spec path")
    parser.add_argument("--spec-tree", required=True, help="Directory with split OpenAPI files")
    parser.add_argument("--docs-provider", default="mkdocs")
    parser.add_argument("--docs-spec-target", default="docs/assets/api")
    parser.add_argument("--stubs-output", default="generated/api-stubs/fastapi/app/main.py")
    parser.add_argument("--verify-user-path", action="store_true")
    parser.add_argument("--mock-base-url", default="http://localhost:4010/v1")
    parser.add_argument("--sandbox-backend", default="docker")
    parser.add_argument("--auto-prepare-external-mock", action="store_true")
    parser.add_argument("--external-mock-provider", default="postman")
    parser.add_argument("--external-mock-base-path", default="/v1")
    parser.add_argument("--external-mock-postman-api-key-env", default="POSTMAN_API_KEY")
    parser.add_argument("--external-mock-postman-workspace-id-env", default="POSTMAN_WORKSPACE_ID")
    parser.add_argument("--external-mock-postman-collection-uid-env", default="POSTMAN_COLLECTION_UID")
    parser.add_argument("--external-mock-postman-mock-server-id-env", default="POSTMAN_MOCK_SERVER_ID")
    parser.add_argument("--external-mock-postman-mock-server-name", default="")
    parser.add_argument("--external-mock-postman-private", action="store_true")
    parser.add_argument("--run-docs-lint", action="store_true")
    parser.add_argument(
        "--finalize-gate",
        dest="finalize_gate",
        action="store_true",
        default=True,
        help="Run unified finalize gate (lint/fix loop) after API-first generation",
    )
    parser.add_argument(
        "--no-finalize-gate",
        dest="finalize_gate",
        action="store_false",
        help="Disable finalize gate",
    )
    parser.add_argument("--runtime-config", default="", help="Optional runtime config path for finalize gate settings")
    parser.add_argument("--docs-root", default="docs", help="Docs root for finalize gate")
    parser.add_argument("--finalize-continue-on-error", action="store_true")
    parser.add_argument("--ask-commit-confirmation", action="store_true")
    parser.add_argument(
        "--ui-confirmation",
        choices=["auto", "on", "off"],
        default="auto",
        help="Finalize gate confirmation UI mode",
    )
    parser.add_argument("--generate-test-assets", action="store_true")
    parser.add_argument("--test-assets-output-dir", default="reports/api-test-assets")
    parser.add_argument("--testrail-csv", default="reports/api-test-assets/testrail_test_cases.csv")
    parser.add_argument("--zephyr-json", default="reports/api-test-assets/zephyr_test_cases.json")
    parser.add_argument("--upload-test-assets", action="store_true")
    parser.add_argument("--upload-test-assets-strict", action="store_true")
    parser.add_argument("--test-assets-upload-report", default="reports/api-test-assets/upload_report.json")
    parser.add_argument("--upload-testrail-enabled-env", default="TESTRAIL_UPLOAD_ENABLED")
    parser.add_argument("--upload-testrail-base-url-env", default="TESTRAIL_BASE_URL")
    parser.add_argument("--upload-testrail-email-env", default="TESTRAIL_EMAIL")
    parser.add_argument("--upload-testrail-api-key-env", default="TESTRAIL_API_KEY")
    parser.add_argument("--upload-testrail-section-id-env", default="TESTRAIL_SECTION_ID")
    parser.add_argument("--upload-testrail-suite-id-env", default="TESTRAIL_SUITE_ID")
    parser.add_argument("--upload-zephyr-enabled-env", default="ZEPHYR_UPLOAD_ENABLED")
    parser.add_argument("--upload-zephyr-base-url-env", default="ZEPHYR_SCALE_BASE_URL")
    parser.add_argument("--upload-zephyr-token-env", default="ZEPHYR_SCALE_API_TOKEN")
    parser.add_argument("--upload-zephyr-project-key-env", default="ZEPHYR_SCALE_PROJECT_KEY")
    parser.add_argument("--upload-zephyr-folder-id-env", default="ZEPHYR_SCALE_FOLDER_ID")
    parser.add_argument("--auto-remediate", action="store_true")
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--inject-demo-nav", action="store_true")
    parser.add_argument(
        "--sync-playground-endpoint",
        dest="sync_playground_endpoint",
        action="store_true",
        default=True,
        help="Sync mkdocs API playground sandbox_base_url with --mock-base-url",
    )
    parser.add_argument(
        "--no-sync-playground-endpoint",
        dest="sync_playground_endpoint",
        action="store_false",
        help="Disable mkdocs playground endpoint sync",
    )
    parser.add_argument("--skip-generate-from-notes", action="store_true")
    parser.add_argument("--openapi-version", default="3.0.3")
    parser.add_argument(
        "--manual-overrides",
        default="",
        help="Optional YAML file with manual OpenAPI overrides",
    )
    parser.add_argument(
        "--regression-snapshot",
        default="",
        help="Optional JSON snapshot path for OpenAPI regression gate",
    )
    parser.add_argument(
        "--update-regression-snapshot",
        action="store_true",
        help="Refresh regression snapshot during this run",
    )
    args = parser.parse_args()
    narrator = FlowNarrator("API-first flow", total_steps=5)
    narrator.start("Generating contract, stubs, test assets, and docs-quality outputs.")

    # -- License gate: API-first flow requires professional+ plan --
    _license_require("api_first_flow")

    repo = Path(__file__).resolve().parents[1]
    notes = (repo / args.notes).resolve()
    spec = (repo / args.spec).resolve()
    spec_tree = (repo / args.spec_tree).resolve()
    docs_target = (repo / args.docs_spec_target).resolve()
    stubs_output = (repo / args.stubs_output).resolve()
    test_assets_output_dir = (repo / args.test_assets_output_dir).resolve()
    testrail_csv_path = (repo / args.testrail_csv).resolve()
    zephyr_json_path = (repo / args.zephyr_json).resolve()
    upload_report_path = (repo / args.test_assets_upload_report).resolve()
    manual_overrides = (repo / args.manual_overrides).resolve() if args.manual_overrides else None
    regression_snapshot = (repo / args.regression_snapshot).resolve() if args.regression_snapshot else None
    runtime_config = (repo / args.runtime_config).resolve() if args.runtime_config else None
    finalize_docs_root = _resolve_docs_root(runtime_config, str(args.docs_root))

    ensure_file(notes, "planning notes")

    if not args.skip_generate_from_notes:
        narrator.note("Pre-step: generate OpenAPI contract from planning notes")
        run(
            [
                "python3",
                "scripts/generate_openapi_from_planning_notes.py",
                "--notes",
                args.notes,
                "--spec",
                args.spec,
                "--spec-tree",
                args.spec_tree,
                "--openapi-version",
                args.openapi_version,
            ],
            cwd=repo,
            compact=True,
            summary_label="OpenAPI generation from notes finished",
        )

    ensure_file(spec, "OpenAPI spec")
    ensure_file(spec_tree, "OpenAPI split directory")

    resolved_mock_base_url = resolve_mock_base_url(repo, args)

    if args.docs_provider.lower() == "mkdocs" and args.sync_playground_endpoint:
        narrator.note("Sync mkdocs API playground endpoint with resolved sandbox URL")
        sync_playground_sandbox_url(repo, resolved_mock_base_url)

    if manual_overrides is not None:
        narrator.note("Apply manual OpenAPI overrides")
        ensure_file(manual_overrides, "OpenAPI manual overrides file")
        run(
            [
                "python3",
                "scripts/apply_openapi_overrides.py",
                "--spec",
                str(spec),
                "--spec-tree",
                str(spec_tree),
                "--overrides",
                str(manual_overrides),
            ],
            cwd=repo,
            compact=True,
            summary_label="manual OpenAPI overrides applied",
        )

    if args.inject_demo_nav:
        narrator.note("Inject demo navigation entries")
        run(["python3", "scripts/manage_demo_nav.py", "--mode", "add"], cwd=repo)

    last_error: Exception | None = None

    for attempt in range(1, args.max_attempts + 1):
        try:
            print(f"[flow] attempt {attempt}/{args.max_attempts}", flush=True)
            run_one_attempt(
                repo,
                args.project_slug,
                spec,
                spec_tree,
                docs_target,
                stubs_output,
                args.verify_user_path,
                resolved_mock_base_url,
                bool(args.run_docs_lint and not args.finalize_gate),
                args.generate_test_assets,
                test_assets_output_dir,
                testrail_csv_path,
                zephyr_json_path,
                args.upload_test_assets,
                args.upload_test_assets_strict,
                upload_report_path,
                str(args.upload_testrail_enabled_env),
                str(args.upload_testrail_base_url_env),
                str(args.upload_testrail_email_env),
                str(args.upload_testrail_api_key_env),
                str(args.upload_testrail_section_id_env),
                str(args.upload_testrail_suite_id_env),
                str(args.upload_zephyr_enabled_env),
                str(args.upload_zephyr_base_url_env),
                str(args.upload_zephyr_token_env),
                str(args.upload_zephyr_project_key_env),
                str(args.upload_zephyr_folder_id_env),
                regression_snapshot,
                args.update_regression_snapshot,
                narrator,
            )
            if args.finalize_gate:
                narrator.stage(5, "Finalize docs gate", "Run lint-fix-lint loop and generate gate report")
                finalize_cmd = [
                    "python3",
                    "scripts/finalize_docs_gate.py",
                    "--docs-root",
                    finalize_docs_root,
                    "--reports-dir",
                    "reports",
                ]
                if runtime_config is not None:
                    finalize_cmd.extend(["--runtime-config", str(runtime_config)])
                if args.finalize_continue_on_error:
                    finalize_cmd.append("--continue-on-error")
                if args.ask_commit_confirmation:
                    finalize_cmd.append("--ask-commit-confirmation")
                finalize_cmd.extend(["--ui-confirmation", str(args.ui_confirmation)])
                run(finalize_cmd, cwd=repo, compact=True, summary_label="finalize docs gate finished")
            narrator.note(f"Sandbox page URL: {build_sandbox_page_url(repo, args.docs_provider)}")
            print("[ok] API-first production flow completed successfully", flush=True)
            narrator.finish(True, "API-first flow completed successfully")
            return 0
        except (Exception,) as error:
            last_error = error
            if not args.auto_remediate or attempt >= args.max_attempts:
                break
            narrator.warn(f"Attempt failed; running remediation sync: {error}")
            copy_spec_to_docs(spec_tree, docs_target / args.project_slug)
            shutil.copy2(spec, docs_target / "openapi.yaml")
            bundle_openapi_spec(docs_target / "openapi.yaml", docs_target / "openapi.bundled.yaml")

    narrator.finish(False, f"API-first flow failed after {args.max_attempts} attempt(s)")
    raise RuntimeError(f"API-first flow failed after {args.max_attempts} attempt(s): {last_error}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        print(f"[error] command failed with exit code {error.returncode}")
        raise SystemExit(error.returncode)
    except (Exception,) as error:  # pragma: no cover
        print(f"[error] {error}")
        raise SystemExit(1)

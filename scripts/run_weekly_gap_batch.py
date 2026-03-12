#!/usr/bin/env python3
"""Run weekly local docs-ops batch and generate consolidated report.

Intended usage from a client repository (with docsops bundle in repo):
  python3 docsops/scripts/run_weekly_gap_batch.py --docsops-root docsops --reports-dir reports
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml


def _run(cmd: list[str], cwd: Path) -> None:
    print(f"[docsops] $ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(cwd), check=True)


def _run_allow_fail(cmd: list[str], cwd: Path) -> int:
    print(f"[docsops] $ {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=str(cwd), check=False)
    if completed.returncode != 0:
        print(f"[docsops] warning: non-blocking command failed with rc={completed.returncode}")
    return completed.returncode


def _run_shell(command: str, cwd: Path, continue_on_error: bool) -> int:
    print(f"[docsops] $ {command}")
    completed = subprocess.run(shlex.split(command), cwd=str(cwd), check=False)
    if completed.returncode != 0 and not continue_on_error:
        raise RuntimeError(f"Custom task failed: {command} (rc={completed.returncode})")
    if completed.returncode != 0:
        print(f"[docsops] warning: custom task failed but continue_on_error=true (rc={completed.returncode})")
    return completed.returncode


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return raw


def _is_enabled(modules: dict[str, Any], key: str, default: bool = True) -> bool:
    value = modules.get(key, default)
    return bool(value)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(dict(merged[key]), value)
        else:
            merged[key] = value
    return merged


def _iter_api_first_configs(api_first: dict[str, Any]) -> list[dict[str, Any]]:
    versions = api_first.get("versions", [])
    if not isinstance(versions, list) or not versions:
        return [api_first]

    base = dict(api_first)
    base.pop("versions", None)
    runs: list[dict[str, Any]] = []
    for item in versions:
        if not isinstance(item, dict):
            continue
        cfg = _deep_merge(base, item)
        cfg["enabled"] = bool(cfg.get("enabled", api_first.get("enabled", False)))
        runs.append(cfg)
    return runs


def _resolve_weekly_base_ref(repo_root: Path, since_days: int) -> str:
    ts = datetime.now(timezone.utc) - timedelta(days=since_days)
    before_arg = ts.strftime("%Y-%m-%d %H:%M:%S")
    cmd = [
        "git",
        "rev-list",
        "-1",
        f"--before={before_arg}",
        "HEAD",
    ]
    completed = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True, check=False)
    candidate = completed.stdout.strip()
    return candidate if candidate else "HEAD~1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Weekly local docs-ops batch runner")
    parser.add_argument("--docsops-root", default="docsops", help="Path to docsops bundle directory")
    parser.add_argument("--reports-dir", default="reports", help="Reports output directory")
    parser.add_argument("--since", type=int, default=7, help="Analyze last N days for gap detection")
    parser.add_argument(
        "--runtime-config",
        default=None,
        help="Optional runtime config path (defaults to <docsops-root>/config/client_runtime.yml)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    docsops_root = (repo_root / args.docsops_root).resolve()
    reports_dir = (repo_root / args.reports_dir).resolve()
    reports_dir.mkdir(parents=True, exist_ok=True)

    runtime_path = (
        Path(args.runtime_config).resolve()
        if args.runtime_config
        else docsops_root / "config" / "client_runtime.yml"
    )
    runtime = _read_yaml(runtime_path)
    docs_flow = runtime.get("docs_flow", {})
    flow_mode = str(docs_flow.get("mode", "code-first")).strip().lower()
    modules = runtime.get("modules", {})
    paths = runtime.get("paths", {})
    pipeline = runtime.get("pipeline", {})
    api_first = runtime.get("api_first", {})
    multilang_examples = runtime.get("multilang_examples", {})
    custom_tasks = runtime.get("custom_tasks", {})
    integrations = runtime.get("integrations", {})

    py = sys.executable
    scripts_dir = docsops_root / "scripts"
    policy_pack = docsops_root / "policy_packs" / "selected.yml"
    base_ref = _resolve_weekly_base_ref(repo_root, args.since)
    head_ref = "HEAD"

    gap_detector = scripts_dir / "gap_detector.py"
    if flow_mode in {"code-first", "hybrid"} and _is_enabled(modules, "gap_detection", True) and gap_detector.exists():
        _run(
            [
                py,
                str(gap_detector),
                "--since",
                str(args.since),
                "--output-dir",
                str(reports_dir),
            ],
            cwd=repo_root,
        )

    docs_contract = scripts_dir / "check_docs_contract.py"
    if flow_mode in {"code-first", "hybrid"} and _is_enabled(modules, "docs_contract", True) and docs_contract.exists():
        _run_allow_fail(
            [
                py,
                str(docs_contract),
                "--base",
                base_ref,
                "--head",
                head_ref,
                "--json-output",
                str(reports_dir / "pr_docs_contract.json"),
                "--policy-pack",
                str(policy_pack),
            ],
            cwd=repo_root,
        )

    drift_check = scripts_dir / "check_api_sdk_drift.py"
    if flow_mode in {"code-first", "hybrid"} and _is_enabled(modules, "drift_detection", True) and drift_check.exists():
        _run_allow_fail(
            [
                py,
                str(drift_check),
                "--base",
                base_ref,
                "--head",
                head_ref,
                "--json-output",
                str(reports_dir / "api_sdk_drift_report.json"),
                "--md-output",
                str(reports_dir / "api_sdk_drift_report.md"),
                "--policy-pack",
                str(policy_pack),
            ],
            cwd=repo_root,
        )

    normalize_docs = scripts_dir / "normalize_docs.py"
    if flow_mode in {"code-first", "hybrid"} and _is_enabled(modules, "normalization", True) and normalize_docs.exists():
        _run_allow_fail([py, str(normalize_docs), str(paths.get("docs_root", "docs"))], cwd=repo_root)

    lint_snippets = scripts_dir / "lint_code_snippets.py"
    if flow_mode in {"code-first", "hybrid"} and _is_enabled(modules, "snippet_lint", True) and lint_snippets.exists():
        _run_allow_fail([py, str(lint_snippets), str(paths.get("docs_root", "docs"))], cwd=repo_root)

    frontmatter_validator = scripts_dir / "validate_frontmatter.py"
    if flow_mode in {"code-first", "hybrid"} and _is_enabled(modules, "fact_checks", True) and frontmatter_validator.exists():
        _run_allow_fail([py, str(frontmatter_validator)], cwd=repo_root)

    multilang_generator = scripts_dir / "generate_multilang_tabs.py"
    multilang_validator = scripts_dir / "validate_multilang_examples.py"
    multilang_enabled = bool(multilang_examples.get("enabled", True))
    if flow_mode in {"code-first", "hybrid", "api-first"} and _is_enabled(modules, "multilang_examples", True) and multilang_enabled and multilang_validator.exists():
        required_languages = multilang_examples.get("required_languages", ["curl", "javascript", "python"])
        if not isinstance(required_languages, list) or not required_languages:
            required_languages = ["curl", "javascript", "python"]
        required_languages_csv = ",".join(str(v).strip() for v in required_languages if str(v).strip())
        scope = str(multilang_examples.get("scope", "all")).strip().lower() or "all"
        if multilang_generator.exists():
            _run_allow_fail(
                [
                    py,
                    str(multilang_generator),
                    "--paths",
                    str(paths.get("docs_root", "docs")),
                    "templates",
                    "--scope",
                    scope,
                    "--write",
                ],
                cwd=repo_root,
            )
        _run_allow_fail(
            [
                py,
                str(multilang_validator),
                "--docs-dir",
                str(paths.get("docs_root", "docs")),
                "--scope",
                scope,
                "--required-languages",
                required_languages_csv,
                "--report",
                str(reports_dir / "multilang_examples_report.json"),
            ],
            cwd=repo_root,
        )

    smoke_examples = scripts_dir / "check_code_examples_smoke.py"
    if flow_mode in {"code-first", "hybrid"} and _is_enabled(modules, "self_checks", True) and smoke_examples.exists():
        _run_allow_fail(
            [
                py,
                str(smoke_examples),
                "--paths",
                str(paths.get("docs_root", "docs")),
                "templates",
                "--allow-empty",
            ],
            cwd=repo_root,
        )

    fact_style = scripts_dir / "seo_geo_optimizer.py"
    if flow_mode in {"code-first", "hybrid"} and _is_enabled(modules, "fact_checks", True) and fact_style.exists():
        _run_allow_fail([py, str(fact_style), str(paths.get("docs_root", "docs"))], cwd=repo_root)

    algolia_cfg = integrations.get("algolia", {})
    if isinstance(algolia_cfg, dict) and bool(algolia_cfg.get("enabled", False)) and fact_style.exists():
        algolia_docs_dir = str(algolia_cfg.get("docs_dir", paths.get("docs_root", "docs")))
        algolia_output = str(algolia_cfg.get("report_output", str(reports_dir / "seo-report.json")))
        _run_allow_fail(
            [
                py,
                str(fact_style),
                algolia_docs_dir,
                "--algolia",
                "--output",
                algolia_output,
            ],
            cwd=repo_root,
        )
        if bool(algolia_cfg.get("upload_on_weekly", False)):
            upload_to_algolia = scripts_dir / "upload_to_algolia.py"
            if upload_to_algolia.exists():
                records_file = str(Path(algolia_output).with_suffix("").as_posix() + "-algolia.json")
                _run_allow_fail(
                    [
                        py,
                        str(upload_to_algolia),
                        "--records-file",
                        records_file,
                        "--app-id-env",
                        str(algolia_cfg.get("app_id_env", "ALGOLIA_APP_ID")),
                        "--api-key-env",
                        str(algolia_cfg.get("api_key_env", "ALGOLIA_API_KEY")),
                        "--index-name-env",
                        str(algolia_cfg.get("index_name_env", "ALGOLIA_INDEX_NAME")),
                        "--index-name-default",
                        str(algolia_cfg.get("index_name_default", "docs")),
                    ],
                    cwd=repo_root,
                )

    layers_validator = scripts_dir / "doc_layers_validator.py"
    if flow_mode in {"code-first", "hybrid"} and _is_enabled(modules, "fact_checks", True) and layers_validator.exists():
        _run_allow_fail(
            [
                py,
                str(layers_validator),
                "--docs-dir",
                str(paths.get("docs_root", "docs")),
                "--policy-pack",
                str(policy_pack),
                "--json-output",
                str(reports_dir / "doc_layers_report.json"),
                "--output",
                str(reports_dir / "doc_layers_report.html"),
            ],
            cwd=repo_root,
        )

    lifecycle_manager = scripts_dir / "lifecycle_manager.py"
    if flow_mode in {"code-first", "hybrid"} and _is_enabled(modules, "lifecycle_management", True) and lifecycle_manager.exists():
        _run_allow_fail(
            [
                py,
                str(lifecycle_manager),
                "--docs-dir",
                str(paths.get("docs_root", "docs")),
                "--scan",
                "--report",
                "--json-output",
                str(reports_dir / "lifecycle-report.json"),
            ],
            cwd=repo_root,
        )

    auto_extract_knowledge = scripts_dir / "extract_knowledge_modules_from_docs.py"
    if _is_enabled(modules, "knowledge_validation", True) and auto_extract_knowledge.exists():
        _run_allow_fail(
            [
                py,
                str(auto_extract_knowledge),
                "--docs-dir",
                str(paths.get("docs_root", "docs")),
                "--modules-dir",
                "knowledge_modules",
                "--report",
                str(reports_dir / "knowledge_auto_extract_report.json"),
            ],
            cwd=repo_root,
        )

    validate_knowledge = scripts_dir / "validate_knowledge_modules.py"
    if _is_enabled(modules, "knowledge_validation", True) and validate_knowledge.exists():
        _run_allow_fail([py, str(validate_knowledge)], cwd=repo_root)

    knowledge_index = scripts_dir / "generate_knowledge_retrieval_index.py"
    if _is_enabled(modules, "rag_optimization", True) and knowledge_index.exists():
        _run_allow_fail([py, str(knowledge_index)], cwd=repo_root)

    i18n_sync = scripts_dir / "i18n_sync.py"
    if _is_enabled(modules, "i18n_sync", True) and i18n_sync.exists():
        _run_allow_fail([py, str(i18n_sync)], cwd=repo_root)

    release_pack = scripts_dir / "generate_release_docs_pack.py"
    if _is_enabled(modules, "release_pack", True) and release_pack.exists():
        _run_allow_fail([py, str(release_pack), "--output", str(reports_dir / "release-docs-pack.md")], cwd=repo_root)

    # Optional KPI+SLA pass if scripts are present in the bundle.
    kpi_wall = scripts_dir / "generate_kpi_wall.py"
    kpi_sla = scripts_dir / "evaluate_kpi_sla.py"
    if flow_mode in {"code-first", "hybrid"} and _is_enabled(modules, "kpi_sla", True) and kpi_wall.exists() and kpi_sla.exists():
        docs_root = str(paths.get("docs_root", "docs"))
        stale_days = str(int(pipeline.get("weekly_stale_days", 180)))
        _run(
            [
                py,
                str(kpi_wall),
                "--docs-dir",
                docs_root,
                "--reports-dir",
                str(reports_dir),
                "--stale-days",
                stale_days,
            ],
            cwd=repo_root,
        )
        _run(
            [
                py,
                str(kpi_sla),
                "--current",
                str(reports_dir / "kpi-wall.json"),
                "--policy-pack",
                str(policy_pack),
                "--json-output",
                str(reports_dir / "kpi-sla-report.json"),
                "--md-output",
                str(reports_dir / "kpi-sla-report.md"),
            ],
            cwd=repo_root,
        )

    if flow_mode in {"api-first", "hybrid"}:
        api_runner = scripts_dir / "run_api_first_flow.py"
        if not api_runner.exists():
            print("[docsops] warning: api-first enabled but run_api_first_flow.py is missing in bundle")
        else:
            api_runs = _iter_api_first_configs(api_first if isinstance(api_first, dict) else {})
            for api_cfg in api_runs:
                if not bool(api_cfg.get("enabled", False)):
                    continue
                cmd = [
                    py,
                    str(api_runner),
                    "--project-slug",
                    str(api_cfg.get("project_slug", "project")),
                    "--notes",
                    str(api_cfg.get("notes_path", "notes/api-planning.md")),
                    "--spec",
                    str(api_cfg.get("spec_path", "api/openapi.yaml")),
                    "--spec-tree",
                    str(api_cfg.get("spec_tree_path", "api/project")),
                    "--docs-provider",
                    str(api_cfg.get("docs_provider", "mkdocs")),
                    "--docs-spec-target",
                    str(api_cfg.get("docs_spec_target", "docs/assets/api")),
                    "--stubs-output",
                    str(api_cfg.get("stubs_output", "generated/api-stubs/fastapi/app/main.py")),
                    "--max-attempts",
                    str(int(api_cfg.get("max_attempts", 3))),
                ]
                if bool(api_cfg.get("auto_remediate", True)):
                    cmd.append("--auto-remediate")
                if bool(api_cfg.get("verify_user_path", False)):
                    cmd.extend(
                        [
                            "--verify-user-path",
                            "--mock-base-url",
                            str(api_cfg.get("mock_base_url", "http://localhost:4010/v1")),
                        ]
                    )
                if bool(api_cfg.get("run_docs_lint", False)):
                    cmd.append("--run-docs-lint")
                if not bool(api_cfg.get("generate_from_notes", True)):
                    cmd.append("--skip-generate-from-notes")
                _run(cmd, cwd=repo_root)

    consolidate = scripts_dir / "consolidate_reports.py"
    if consolidate.exists():
        _run(
            [
                py,
                str(consolidate),
                "--reports-dir",
                str(reports_dir),
                "--output",
                str(reports_dir / "consolidated_report.json"),
            ],
            cwd=repo_root,
        )

    weekly_tasks = custom_tasks.get("weekly", [])
    if isinstance(weekly_tasks, list):
        for task in weekly_tasks:
            if not isinstance(task, dict):
                continue
            if not bool(task.get("enabled", False)):
                continue
            command = str(task.get("command", "")).strip()
            if not command:
                continue
            continue_on_error = bool(task.get("continue_on_error", True))
            _run_shell(command, cwd=repo_root, continue_on_error=continue_on_error)

    status_path = reports_dir / "docsops_status.json"
    consolidated_path = reports_dir / "consolidated_report.json"
    generated_at = datetime.now(timezone.utc).isoformat()
    if consolidated_path.exists():
        try:
            payload = json.loads(consolidated_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                value = payload.get("generated_at")
                if isinstance(value, str) and value.strip():
                    generated_at = value.strip()
        except Exception:  # noqa: BLE001
            pass
    status_payload = {
        "status": "ok",
        "last_run_at": datetime.now(timezone.utc).isoformat(),
        "report_file": str(consolidated_path),
        "report_generated_at": generated_at,
    }
    status_path.write_text(
        json.dumps(status_payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    ready_path = reports_dir / "READY_FOR_REVIEW.txt"
    ready_path.write_text(
        (
            "READY FOR REVIEW\n"
            f"last_run_at: {status_payload['last_run_at']}\n"
            f"report_generated_at: {status_payload['report_generated_at']}\n"
            "next_step: open reports/consolidated_report.json and send it to local LLM\n"
        ),
        encoding="utf-8",
    )

    print("[docsops] weekly batch completed")
    print(f"[docsops] consolidated report: {reports_dir / 'consolidated_report.json'}")
    print(f"[docsops] status file: {status_path}")
    print(f"[docsops] ready marker: {ready_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

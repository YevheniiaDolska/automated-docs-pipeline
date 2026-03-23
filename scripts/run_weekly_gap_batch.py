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

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.env_loader import load_local_env
from scripts.license_gate import get_license, get_license_summary


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


def _resolve_repo_path(repo_root: Path, repo_path: str) -> Path:
    target = Path(repo_path).expanduser()
    if not target.is_absolute():
        target = repo_root / target
    return target.resolve()


def _run_git_sync(repo_root: Path, git_sync: dict[str, Any]) -> None:
    if not isinstance(git_sync, dict) or not bool(git_sync.get("enabled", False)):
        return

    repo_path = str(git_sync.get("repo_path", ".")).strip() or "."
    target_repo = _resolve_repo_path(repo_root, repo_path)
    continue_on_error = bool(git_sync.get("continue_on_error", True))

    if not target_repo.exists():
        message = f"git sync repo path does not exist: {target_repo}"
        if continue_on_error:
            print(f"[docsops] warning: {message}")
            return
        raise RuntimeError(message)

    if not (target_repo / ".git").exists():
        message = f"git sync target is not a git repository: {target_repo}"
        if continue_on_error:
            print(f"[docsops] warning: {message}")
            return
        raise RuntimeError(message)

    remote = str(git_sync.get("remote", "origin")).strip()
    branch = str(git_sync.get("branch", "")).strip()
    fetch_first = bool(git_sync.get("fetch_first", True))
    rebase = bool(git_sync.get("rebase", True))
    autostash = bool(git_sync.get("autostash", True))

    if fetch_first:
        if remote:
            fetch_cmd = f"git fetch {shlex.quote(remote)} --prune"
        else:
            fetch_cmd = "git fetch --all --prune"
        _run_shell(fetch_cmd, target_repo, continue_on_error)

    pull_parts = ["git", "pull"]
    if rebase:
        pull_parts.append("--rebase")
        if autostash:
            pull_parts.append("--autostash")
    if remote and branch:
        pull_parts.extend([remote, branch])
    pull_cmd = " ".join(shlex.quote(part) for part in pull_parts)
    _run_shell(pull_cmd, target_repo, continue_on_error)


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return raw


def _resolve_policy_pack(docsops_root: Path, runtime: dict[str, Any]) -> Path:
    candidates: list[Path] = []
    runtime_policy = runtime.get("policy_pack_path", "")
    if isinstance(runtime_policy, str) and runtime_policy.strip():
        p = Path(runtime_policy.strip()).expanduser()
        if not p.is_absolute():
            p = Path.cwd() / p
        candidates.append(p.resolve())
    candidates.extend(
        [
            docsops_root / "policy_packs" / "selected.yml",
            docsops_root / "policy_packs" / "api-first.yml",
            docsops_root / "policy_packs" / "baseline.yml",
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    fallback = docsops_root / "policy_packs" / "selected.yml"
    print(
        "[docsops] warning: no policy pack found; proceeding in report-only best-effort mode. "
        f"missing expected path: {fallback}"
    )
    return fallback


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
    load_local_env(REPO_ROOT)
    args = parse_args()

    # -- License gate --
    lic = get_license()
    print(f"[docsops] License: {get_license_summary(lic)}")

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
    terminology = runtime.get("terminology", {})
    retrieval_eval = runtime.get("retrieval_eval", {})
    knowledge_graph = runtime.get("knowledge_graph", {})
    git_sync = runtime.get("git_sync", {})
    custom_tasks = runtime.get("custom_tasks", {})
    integrations = runtime.get("integrations", {})
    finalize_gate = runtime.get("finalize_gate", {})
    api_governance = runtime.get("api_governance", {})
    api_protocols_raw = runtime.get("api_protocols", ["rest"])
    api_protocol_settings = runtime.get("api_protocol_settings", {})

    if isinstance(api_protocols_raw, str):
        configured_protocols = [v.strip().lower() for v in api_protocols_raw.split(",") if v.strip()]
    elif isinstance(api_protocols_raw, list):
        configured_protocols = [str(v).strip().lower() for v in api_protocols_raw if str(v).strip()]
    else:
        configured_protocols = ["rest"]
    if not configured_protocols:
        configured_protocols = ["rest"]
    if not isinstance(api_protocol_settings, dict):
        api_protocol_settings = {}

    py = sys.executable
    scripts_dir = docsops_root / "scripts"
    policy_pack = _resolve_policy_pack(docsops_root, runtime)
    policy = _read_yaml(policy_pack) if policy_pack.exists() else {}
    policy_retrieval = policy.get("retrieval_evals", {}) if isinstance(policy.get("retrieval_evals"), dict) else {}
    policy_graph = policy.get("knowledge_graph", {}) if isinstance(policy.get("knowledge_graph"), dict) else {}

    _run_git_sync(repo_root, git_sync if isinstance(git_sync, dict) else {})

    # Multi-protocol contract/docs flow for non-REST architectures.
    non_rest_protocols: list[str] = []
    for protocol in configured_protocols:
        if protocol == "rest":
            continue
        cfg = api_protocol_settings.get(protocol, {})
        enabled = bool(cfg.get("enabled", protocol in configured_protocols)) if isinstance(cfg, dict) else bool(protocol in configured_protocols)
        if enabled and protocol not in non_rest_protocols:
            non_rest_protocols.append(protocol)

    multi_protocol_runner = scripts_dir / "run_multi_protocol_contract_flow.py"
    strictness = str(api_governance.get("strictness", "standard")).strip().lower() if isinstance(api_governance, dict) else "standard"
    if multi_protocol_runner.exists() and non_rest_protocols:
        multi_cmd = [
            py,
            str(multi_protocol_runner),
            "--runtime-config",
            str(runtime_path),
            "--reports-dir",
            str(reports_dir),
            "--protocols",
            ",".join(non_rest_protocols),
        ]
        if strictness == "enterprise-strict":
            multi_cmd.extend(["--strictness", "enterprise-strict"])
        _run(multi_cmd, cwd=repo_root)
    else:
        # Keep autopipeline artifact contract stable when only REST is configured.
        minimal_report = {
            "strictness": strictness or "standard",
            "strict_mode": bool(strictness == "enterprise-strict"),
            "protocols": non_rest_protocols,
            "failed_protocols": [],
            "failed": False,
            "stages": [],
            "by_protocol": {},
            "skipped_reason": "no_non_rest_protocols_selected_or_runner_missing",
        }
        (reports_dir / "multi_protocol_contract_report.json").write_text(
            json.dumps(minimal_report, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

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
                "--enforcement",
                "report-only",
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

    knowledge_graph_script = scripts_dir / "generate_knowledge_graph_jsonld.py"
    if (
        _is_enabled(modules, "ontology_graph", True)
        and knowledge_graph_script.exists()
        and bool(knowledge_graph.get("enabled", True))
    ):
        _run_allow_fail(
            [
                py,
                str(knowledge_graph_script),
                "--modules-dir",
                str(knowledge_graph.get("modules_dir", "knowledge_modules")),
                "--output",
                str(knowledge_graph.get("output_path", "docs/assets/knowledge-graph.jsonld")),
                "--report",
                str(reports_dir / "knowledge_graph_report.json"),
                "--min-graph-nodes",
                str(int(knowledge_graph.get("min_graph_nodes", policy_graph.get("min_graph_nodes", 0)))),
            ],
            cwd=repo_root,
        )

    retrieval_evals_script = scripts_dir / "run_retrieval_evals.py"
    if (
        _is_enabled(modules, "retrieval_evals", True)
        and retrieval_evals_script.exists()
        and bool(retrieval_eval.get("enabled", True))
    ):
        cmd = [
            py,
            str(retrieval_evals_script),
            "--index",
            str(retrieval_eval.get("index_path", "docs/assets/knowledge-retrieval-index.json")),
            "--dataset-out",
            str(reports_dir / "retrieval_eval_dataset.generated.yml"),
            "--report",
            str(reports_dir / "retrieval_evals_report.json"),
            "--top-k",
            str(int(retrieval_eval.get("top_k", 3))),
            "--min-precision",
            str(float(retrieval_eval.get("min_precision", policy_retrieval.get("min_precision", 0.5)))),
            "--min-recall",
            str(float(retrieval_eval.get("min_recall", policy_retrieval.get("min_recall", 0.5)))),
            "--max-hallucination-rate",
            str(float(retrieval_eval.get("max_hallucination_rate", policy_retrieval.get("max_hallucination_rate", 0.5)))),
            "--auto-samples",
            str(int(retrieval_eval.get("auto_samples", 25))),
            "--auto-generate-dataset",
        ]
        dataset_path = str(retrieval_eval.get("dataset_path", "")).strip()
        if dataset_path:
            cmd.extend(["--dataset", dataset_path])
        _run_allow_fail(cmd, cwd=repo_root)

    i18n_sync = scripts_dir / "i18n_sync.py"
    if _is_enabled(modules, "i18n_sync", True) and i18n_sync.exists():
        _run_allow_fail([py, str(i18n_sync)], cwd=repo_root)

    release_pack = scripts_dir / "generate_release_docs_pack.py"
    if _is_enabled(modules, "release_pack", True) and release_pack.exists():
        _run_allow_fail([py, str(release_pack), "--output", str(reports_dir / "release-docs-pack.md")], cwd=repo_root)

    glossary_sync = scripts_dir / "sync_project_glossary.py"
    if (
        flow_mode in {"code-first", "hybrid", "api-first"}
        and _is_enabled(modules, "terminology_management", True)
        and glossary_sync.exists()
        and bool(terminology.get("enabled", True))
    ):
        _run_allow_fail(
            [
                py,
                str(glossary_sync),
                "--paths",
                str(paths.get("docs_root", "docs")),
                "--glossary",
                str(terminology.get("glossary_path", "glossary.yml")),
                "--report",
                str(reports_dir / "glossary_sync_report.json"),
                "--write",
            ],
            cwd=repo_root,
        )

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
                    "--openapi-version",
                    str(api_cfg.get("openapi_version", "3.0.3")),
                    "--sandbox-backend",
                    str(api_cfg.get("sandbox_backend", "docker")),
                    "--no-finalize-gate",
                ]
                manual_overrides = str(api_cfg.get("manual_overrides_path", "")).strip()
                if manual_overrides:
                    cmd.extend(["--manual-overrides", manual_overrides])
                regression_snapshot = str(api_cfg.get("regression_snapshot_path", "")).strip()
                if regression_snapshot:
                    cmd.extend(["--regression-snapshot", regression_snapshot])
                if bool(api_cfg.get("update_regression_snapshot", False)):
                    cmd.append("--update-regression-snapshot")
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
                if bool(api_cfg.get("generate_test_assets", False)):
                    cmd.append("--generate-test-assets")
                    cmd.extend(
                        [
                            "--test-assets-output-dir",
                            str(api_cfg.get("test_assets_output_dir", "reports/api-test-assets")),
                            "--testrail-csv",
                            str(api_cfg.get("testrail_csv", "reports/api-test-assets/testrail_test_cases.csv")),
                            "--zephyr-json",
                            str(api_cfg.get("zephyr_json", "reports/api-test-assets/zephyr_test_cases.json")),
                        ]
                    )
                if bool(api_cfg.get("upload_test_assets", False)):
                    cmd.append("--upload-test-assets")
                    cmd.extend(
                        [
                            "--test-assets-upload-report",
                            str(api_cfg.get("test_assets_upload_report", "reports/api-test-assets/upload_report.json")),
                        ]
                    )
                    if bool(api_cfg.get("upload_test_assets_strict", False)):
                        cmd.append("--upload-test-assets-strict")
                    test_mgmt = api_cfg.get("test_management", {})
                    if isinstance(test_mgmt, dict):
                        testrail_cfg = test_mgmt.get("testrail", {})
                        if isinstance(testrail_cfg, dict):
                            cmd.extend(
                                [
                                    "--upload-testrail-enabled-env",
                                    str(testrail_cfg.get("enabled_env", "TESTRAIL_UPLOAD_ENABLED")),
                                    "--upload-testrail-base-url-env",
                                    str(testrail_cfg.get("base_url_env", "TESTRAIL_BASE_URL")),
                                    "--upload-testrail-email-env",
                                    str(testrail_cfg.get("email_env", "TESTRAIL_EMAIL")),
                                    "--upload-testrail-api-key-env",
                                    str(testrail_cfg.get("api_key_env", "TESTRAIL_API_KEY")),
                                    "--upload-testrail-section-id-env",
                                    str(testrail_cfg.get("section_id_env", "TESTRAIL_SECTION_ID")),
                                    "--upload-testrail-suite-id-env",
                                    str(testrail_cfg.get("suite_id_env", "TESTRAIL_SUITE_ID")),
                                ]
                            )
                        zephyr_cfg = test_mgmt.get("zephyr_scale", {})
                        if isinstance(zephyr_cfg, dict):
                            cmd.extend(
                                [
                                    "--upload-zephyr-enabled-env",
                                    str(zephyr_cfg.get("enabled_env", "ZEPHYR_UPLOAD_ENABLED")),
                                    "--upload-zephyr-base-url-env",
                                    str(zephyr_cfg.get("base_url_env", "ZEPHYR_SCALE_BASE_URL")),
                                    "--upload-zephyr-token-env",
                                    str(zephyr_cfg.get("api_token_env", "ZEPHYR_SCALE_API_TOKEN")),
                                    "--upload-zephyr-project-key-env",
                                    str(zephyr_cfg.get("project_key_env", "ZEPHYR_SCALE_PROJECT_KEY")),
                                    "--upload-zephyr-folder-id-env",
                                    str(zephyr_cfg.get("folder_id_env", "ZEPHYR_SCALE_FOLDER_ID")),
                                ]
                            )
                external_mock_cfg = api_cfg.get("external_mock", {})
                if isinstance(external_mock_cfg, dict) and bool(external_mock_cfg.get("enabled", False)):
                    cmd.extend(
                        [
                            "--auto-prepare-external-mock",
                            "--external-mock-provider",
                            str(external_mock_cfg.get("provider", "postman")),
                            "--external-mock-base-path",
                            str(external_mock_cfg.get("base_path", "/v1")),
                        ]
                    )
                    postman_cfg = external_mock_cfg.get("postman", {})
                    if isinstance(postman_cfg, dict):
                        cmd.extend(
                            [
                                "--external-mock-postman-api-key-env",
                                str(postman_cfg.get("api_key_env", "POSTMAN_API_KEY")),
                                "--external-mock-postman-workspace-id-env",
                                str(postman_cfg.get("workspace_id_env", "POSTMAN_WORKSPACE_ID")),
                                "--external-mock-postman-collection-uid-env",
                                str(postman_cfg.get("collection_uid_env", "POSTMAN_COLLECTION_UID")),
                                "--external-mock-postman-mock-server-id-env",
                                str(postman_cfg.get("mock_server_id_env", "POSTMAN_MOCK_SERVER_ID")),
                                "--external-mock-postman-mock-server-name",
                                str(postman_cfg.get("mock_server_name", "")),
                            ]
                        )
                        if bool(postman_cfg.get("private", False)):
                            cmd.append("--external-mock-postman-private")
                if bool(api_cfg.get("run_docs_lint", False)):
                    cmd.append("--run-docs-lint")
                if not bool(api_cfg.get("sync_playground_endpoint", True)):
                    cmd.append("--no-sync-playground-endpoint")
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

    audit_scorecard = scripts_dir / "generate_audit_scorecard.py"
    if audit_scorecard.exists():
        _run_allow_fail(
            [
                py,
                str(audit_scorecard),
                "--docs-dir",
                str(paths.get("docs_root", "docs")),
                "--reports-dir",
                str(reports_dir),
                "--spec-path",
                str(api_cfg.get("spec_path", "api/openapi.yaml")),
                "--policy-pack",
                str(policy_pack_path),
                "--glossary-path",
                str(terminology.get("glossary_path", "glossary.yml"))
                if isinstance(terminology, dict)
                else "glossary.yml",
                "--stale-days",
                str(int(private_tuning.get("weekly_stale_days", 180))),
                "--auto-run-smoke",
                "--json-output",
                str(reports_dir / "audit_scorecard.json"),
                "--html-output",
                str(reports_dir / "audit_scorecard.html"),
            ],
            cwd=repo_root,
        )

    doc_compiler = scripts_dir / "compile_doc_overview.py"
    if _is_enabled(modules, "doc_compiler", True) and doc_compiler.exists():
        dc_config = runtime.get("doc_compiler", {})
        if not isinstance(dc_config, dict):
            dc_config = {}
        dc_modalities = str(dc_config.get("modalities", "all")).strip() or "all"
        dc_cmd = [
            py,
            str(doc_compiler),
            "--docs-dir",
            str(paths.get("docs_root", "docs")),
            "--reports-dir",
            str(reports_dir),
            "--glossary-path",
            str(terminology.get("glossary_path", "glossary.yml"))
            if isinstance(terminology, dict)
            else "glossary.yml",
            "--modalities",
            dc_modalities,
        ]
        if bool(dc_config.get("generate_faq_doc", False)):
            dc_cmd.append("--generate-faq-doc")
        _run_allow_fail(dc_cmd, cwd=repo_root)

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

    finalize_script = scripts_dir / "finalize_docs_gate.py"
    finalize_enabled = bool(finalize_gate.get("enabled", True)) if isinstance(finalize_gate, dict) else True
    if finalize_enabled and finalize_script.exists():
        finalize_cmd = [
            py,
            str(finalize_script),
            "--docs-root",
            str(finalize_gate.get("docs_root", paths.get("docs_root", "docs"))) if isinstance(finalize_gate, dict) else str(paths.get("docs_root", "docs")),
            "--reports-dir",
            str(finalize_gate.get("reports_dir", reports_dir)) if isinstance(finalize_gate, dict) else str(reports_dir),
            "--runtime-config",
            str(runtime_path),
        ]
        if isinstance(finalize_gate, dict) and bool(finalize_gate.get("continue_on_error", True)):
            finalize_cmd.append("--continue-on-error")
        _run_allow_fail(finalize_cmd, cwd=repo_root)

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

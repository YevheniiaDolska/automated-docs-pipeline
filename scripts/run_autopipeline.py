#!/usr/bin/env python3
"""Unified smooth autopipeline runner.

Goal: no manual standalone command chain.
Single entrypoint executes weekly docs-ops flow, protocol automation,
quality gates, and produces local-LLM review packet.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.env_loader import load_local_env


def _read_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return payload


def _run(cmd: list[str], cwd: Path) -> int:
    print(f"[autopipeline] $ {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=str(cwd), check=False)
    return completed.returncode


def _safe_load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    return payload if isinstance(payload, dict) else {}


def _say(step: str, detail: str = "") -> None:
    suffix = f" - {detail}" if detail else ""
    print(f"[autopipeline] {step}{suffix}")


def _load_site_url(repo_root: Path) -> str:
    mkdocs_path = repo_root / "mkdocs.yml"
    if not mkdocs_path.exists():
        return ""
    try:
        payload = yaml.safe_load(mkdocs_path.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001
        return ""
    if not isinstance(payload, dict):
        return ""
    return str(payload.get("site_url", "")).rstrip("/")


def _normalize_site_url(site_url: str) -> str:
    """Prefer canonical non-language URL for generated demo/public links."""
    base = site_url.rstrip("/")
    if base.endswith("/en"):
        return base[: -len("/en")]
    return base


def _docs_public_url(repo_root: Path, abs_path: str, site_url: str) -> str:
    if not site_url:
        return ""
    site_url = _normalize_site_url(site_url)
    path = Path(abs_path)
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
    except Exception:  # noqa: BLE001
        return ""
    rel_text = str(rel).replace("\\", "/")
    if not rel_text.startswith("docs/"):
        return ""
    md_rel = rel_text[len("docs/") :]
    if md_rel.endswith(".md"):
        md_rel = md_rel[:-3] + "/"
    return f"{site_url}/{md_rel}".replace("//", "/").replace("https:/", "https://").replace("http:/", "http://")


def _build_stage_summary(
    runtime: dict[str, Any],
    repo_root: Path,
    reports_dir: Path,
    weekly_rc: int,
    strictness: str,
    skip_consolidated_report: bool,
) -> dict[str, Any]:
    modules = runtime.get("modules", {})
    api_first = runtime.get("api_first", {})
    protocol_settings = runtime.get("api_protocol_settings", {})
    if not isinstance(modules, dict):
        modules = {}
    if not isinstance(api_first, dict):
        api_first = {}
    if not isinstance(protocol_settings, dict):
        protocol_settings = {}

    checks: list[tuple[str, Path, bool]] = [("multi_protocol_contract", reports_dir / "multi_protocol_contract_report.json", True)]
    if not skip_consolidated_report:
        checks.append(("consolidated_report", reports_dir / "consolidated_report.json", True))

    checks.extend(
        [
            ("audit_scorecard", reports_dir / "audit_scorecard.json", True),
            ("finalize_gate", reports_dir / "finalize_gate_report.json", True),
            ("docsops_status", reports_dir / "docsops_status.json", True),
            ("ready_marker", reports_dir / "READY_FOR_REVIEW.txt", True),
        ]
    )

    if bool(modules.get("kpi_sla", True)):
        checks.extend(
            [
                ("kpi_wall", reports_dir / "kpi-wall.json", True),
                ("kpi_sla", reports_dir / "kpi-sla-report.json", True),
            ]
        )
    if bool(modules.get("terminology_management", True)):
        checks.append(("glossary_sync", reports_dir / "glossary_sync_report.json", False))
    if bool(modules.get("retrieval_evals", True)):
        checks.extend(
            [
                ("retrieval_evals", reports_dir / "retrieval_evals_report.json", True),
                ("retrieval_dataset", reports_dir / "retrieval_eval_dataset.generated.yml", False),
            ]
        )
    if bool(modules.get("rag_optimization", True)):
        checks.append(("rag_retrieval_index", repo_root / "docs/assets/knowledge-retrieval-index.json", True))
    if bool(modules.get("ontology_graph", True)):
        checks.extend(
            [
                ("knowledge_graph_report", reports_dir / "knowledge_graph_report.json", False),
                ("knowledge_graph", repo_root / "docs/assets/knowledge-graph.jsonld", True),
            ]
        )

    generate_assets = bool(api_first.get("generate_test_assets", False))
    upload_assets = bool(api_first.get("upload_test_assets", False))
    for cfg in protocol_settings.values():
        if isinstance(cfg, dict):
            generate_assets = generate_assets or bool(cfg.get("generate_test_assets", False))
            upload_assets = upload_assets or bool(cfg.get("upload_test_assets", False))
    if generate_assets:
        checks.extend(
            [
                ("test_assets_json", reports_dir / "api-test-assets" / "api_test_cases.json", True),
                ("test_assets_coverage", reports_dir / "api-test-assets" / "coverage_report.json", True),
                ("test_assets_fuzz", reports_dir / "api-test-assets" / "fuzz_scenarios.json", False),
                ("test_assets_summary", reports_dir / "api-test-assets" / "TEST_ASSETS_SUMMARY.md", True),
            ]
        )
    if upload_assets:
        checks.append(("test_assets_upload_report", reports_dir / "api-test-assets" / "upload_report.json", True))

    stages: list[dict[str, Any]] = []
    missing_required = 0
    for name, path, required in checks:
        exists = path.exists()
        if required and not exists:
            missing_required += 1
        stages.append(
            {
                "stage": name,
                "path": str(path),
                "exists": exists,
                "required": bool(required),
            }
        )
    return {
        "weekly_rc": int(weekly_rc),
        "strictness": strictness,
        "skip_consolidated_report": bool(skip_consolidated_report),
        "missing_required_artifacts": int(missing_required),
        "stages": stages,
        "ok": bool(weekly_rc == 0 and missing_required == 0),
    }


def _collect_artifacts(
    runtime: dict[str, Any],
    reports_dir: Path,
    repo_root: Path,
    skip_consolidated_report: bool,
) -> list[dict[str, Any]]:
    modules = runtime.get("modules", {})
    retrieval_eval = runtime.get("retrieval_eval", {})
    knowledge_graph = runtime.get("knowledge_graph", {})
    terminology = runtime.get("terminology", {})
    paths = runtime.get("paths", {})
    api_protocols = runtime.get("api_protocols", ["rest"])
    if not isinstance(api_protocols, list):
        api_protocols = ["rest"]
    api_protocols = [str(p).strip().lower() for p in api_protocols if str(p).strip()]
    protocol_settings = runtime.get("api_protocol_settings", {})
    if not isinstance(protocol_settings, dict):
        protocol_settings = {}
    api_first = runtime.get("api_first", {})
    if not isinstance(api_first, dict):
        api_first = {}

    def _enabled(name: str, default: bool = True) -> bool:
        return bool(modules.get(name, default))

    docs_root = str(paths.get("docs_root", "docs"))
    artifacts: list[dict[str, Any]] = []

    def add_artifact(title: str, rel_path: str, category: str, *, module: str = "", required: bool = False) -> None:
        path = (repo_root / rel_path).resolve() if not Path(rel_path).is_absolute() else Path(rel_path)
        artifacts.append(
            {
                "title": title,
                "category": category,
                "module": module,
                "required": bool(required),
                "path": str(path),
                "exists": path.exists(),
            }
        )

    # Core reports
    add_artifact(
        "Consolidated report",
        str(reports_dir / "consolidated_report.json"),
        "reports",
        required=not skip_consolidated_report,
    )
    add_artifact("Audit scorecard (JSON)", str(reports_dir / "audit_scorecard.json"), "reports")
    add_artifact("Audit scorecard (HTML)", str(reports_dir / "audit_scorecard.html"), "reports")
    add_artifact("Finalize gate report", str(reports_dir / "finalize_gate_report.json"), "reports")
    add_artifact("DocsOps status", str(reports_dir / "docsops_status.json"), "reports")
    add_artifact("Ready marker", str(reports_dir / "READY_FOR_REVIEW.txt"), "reports")

    # Docs browse entrypoints
    add_artifact("Docs index", f"{docs_root}/index.md", "docs", required=True)
    add_artifact("Faceted search page", f"{docs_root}/search-faceted.md", "search")
    add_artifact("Facets index", f"{docs_root}/assets/facets-index.json", "search")

    # Protocol docs and contract outputs
    add_artifact("Multi-protocol contract report", str(reports_dir / "multi_protocol_contract_report.json"), "protocols")
    protocol_doc_map = {
        "rest": "rest-api.md",
        "graphql": "graphql-api.md",
        "grpc": "grpc-api.md",
        "asyncapi": "asyncapi-api.md",
        "websocket": "websocket-api.md",
    }
    for protocol in api_protocols:
        doc_name = protocol_doc_map.get(protocol)
        if doc_name:
            add_artifact(f"{protocol.upper()} reference", f"{docs_root}/reference/{doc_name}", "protocols")
    add_artifact("REST playground", f"{docs_root}/reference/taskstream-api-playground.md", "protocols")

    # Test asset outputs
    generate_assets = bool(api_first.get("generate_test_assets", False))
    upload_assets = bool(api_first.get("upload_test_assets", False))
    for protocol in api_protocols:
        cfg = protocol_settings.get(protocol, {})
        if isinstance(cfg, dict):
            generate_assets = generate_assets or bool(cfg.get("generate_test_assets", False))
            upload_assets = upload_assets or bool(cfg.get("upload_test_assets", False))
    if generate_assets:
        add_artifact("API test cases JSON", str(reports_dir / "api-test-assets" / "api_test_cases.json"), "tests")
        add_artifact("TestRail CSV", str(reports_dir / "api-test-assets" / "testrail_test_cases.csv"), "tests")
        add_artifact("Zephyr JSON", str(reports_dir / "api-test-assets" / "zephyr_test_cases.json"), "tests")
        add_artifact("Test coverage report", str(reports_dir / "api-test-assets" / "coverage_report.json"), "tests")
        add_artifact("Fuzz scenarios", str(reports_dir / "api-test-assets" / "fuzz_scenarios.json"), "tests")
        add_artifact("Test assets summary", str(reports_dir / "api-test-assets" / "TEST_ASSETS_SUMMARY.md"), "tests")
    if upload_assets:
        add_artifact("Test assets upload report", str(reports_dir / "api-test-assets" / "upload_report.json"), "tests")

    if _enabled("terminology_management", True):
        glossary_path = str(terminology.get("glossary_path", "glossary.yml")) if isinstance(terminology, dict) else "glossary.yml"
        add_artifact("Glossary source", glossary_path, "quality", module="terminology_management")
        add_artifact("Glossary sync report", str(reports_dir / "glossary_sync_report.json"), "quality", module="terminology_management")

    if _enabled("kpi_sla", True):
        add_artifact("KPI wall", str(reports_dir / "kpi-wall.json"), "quality", module="kpi_sla")
        add_artifact("KPI SLA report", str(reports_dir / "kpi-sla-report.json"), "quality", module="kpi_sla")

    if _enabled("rag_optimization", True):
        index_path = "docs/assets/knowledge-retrieval-index.json"
        if isinstance(retrieval_eval, dict):
            index_path = str(retrieval_eval.get("index_path", index_path))
        add_artifact("RAG retrieval index", index_path, "rag", module="rag_optimization")

    if _enabled("ontology_graph", True):
        graph_path = "docs/assets/knowledge-graph.jsonld"
        if isinstance(knowledge_graph, dict):
            graph_path = str(knowledge_graph.get("output_path", graph_path))
        add_artifact("RAG knowledge graph", graph_path, "rag", module="ontology_graph")
        add_artifact("Knowledge graph report", str(reports_dir / "knowledge_graph_report.json"), "rag", module="ontology_graph")

    if _enabled("retrieval_evals", True):
        add_artifact("Retrieval eval report", str(reports_dir / "retrieval_evals_report.json"), "rag", module="retrieval_evals")
        add_artifact("Retrieval eval dataset", str(reports_dir / "retrieval_eval_dataset.generated.yml"), "rag", module="retrieval_evals")

    return artifacts


def _write_review_manifest(
    reports_dir: Path,
    runtime_path: Path,
    runtime: dict[str, Any],
    repo_root: Path,
    stage_summary: dict[str, Any],
    skip_consolidated_report: bool,
) -> Path:
    artifacts = _collect_artifacts(runtime, reports_dir, repo_root, skip_consolidated_report)
    available = [a for a in artifacts if bool(a.get("exists"))]
    missing = [a for a in artifacts if not bool(a.get("exists"))]

    retrieval_meta: dict[str, Any] = {}
    index_payload = _safe_load_json((repo_root / "docs/assets/knowledge-retrieval-index.json").resolve())
    if index_payload:
        records = index_payload.get("records")
        if isinstance(records, list):
            retrieval_meta["retrieval_records"] = len(records)

    graph_payload = _safe_load_json((repo_root / "docs/assets/knowledge-graph.jsonld").resolve())
    if graph_payload:
        nodes = graph_payload.get("nodes")
        edges = graph_payload.get("edges")
        if isinstance(nodes, list):
            retrieval_meta["graph_nodes"] = len(nodes)
        if isinstance(edges, list):
            retrieval_meta["graph_edges"] = len(edges)

    payload = {
        "runtime_config": str(runtime_path),
        "stage_summary": stage_summary,
        "artifacts": artifacts,
        "available_artifacts": len(available),
        "missing_artifacts": len(missing),
        "rag_metadata": retrieval_meta,
    }

    out_json = reports_dir / "review_manifest.json"
    out_md = reports_dir / "REVIEW_MANIFEST.md"
    out_json.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Review Manifest",
        "",
        f"- Runtime config: `{runtime_path}`",
        f"- Weekly run rc: `{stage_summary.get('weekly_rc')}`",
        f"- Strictness: `{stage_summary.get('strictness')}`",
        f"- Available artifacts: `{len(available)}`",
        f"- Missing artifacts: `{len(missing)}`",
        "",
        "## Stage Summary",
        "",
    ]
    for stage in stage_summary.get("stages", []):
        status = "OK" if stage.get("exists") else "MISSING"
        lines.append(f"- `{stage.get('stage')}`: **{status}** (`{stage.get('path')}`)")

    lines.extend(["", "## Review Links (Available)", ""])
    for item in available:
        lines.append(f"- [{item['title']}]({item['path']}) - `{item['category']}`")

    if missing:
        lines.extend(["", "## Expected But Missing", ""])
        for item in missing:
            mod = str(item.get("module", "")).strip()
            suffix = f" (module: `{mod}`)" if mod else ""
            lines.append(f"- `{item['title']}` -> `{item['path']}`{suffix}")

    if retrieval_meta:
        lines.extend(["", "## RAG Metadata", ""])
        for key, value in retrieval_meta.items():
            lines.append(f"- `{key}`: `{value}`")

    lines.extend(
        [
            "",
            "## Reviewer Checklist",
            "",
            "- Confirm stage summary has no missing required artifacts.",
            "- Review protocol docs and test assets links.",
            "- Review quality and retrieval reports before publish.",
            "- Approve publish only if critical findings are resolved.",
            "",
        ]
    )
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return out_md


def _write_output_index(
    reports_dir: Path,
    runtime_path: Path,
    stage_summary: dict[str, Any],
    review_manifest: Path,
    repo_root: Path,
) -> Path:
    manifest_json = _safe_load_json(reports_dir / "review_manifest.json")
    artifacts = manifest_json.get("artifacts", [])
    if not isinstance(artifacts, list):
        artifacts = []
    site_url = _load_site_url(repo_root)
    by_category: dict[str, list[dict[str, Any]]] = {}
    for item in artifacts:
        if not isinstance(item, dict):
            continue
        category = str(item.get("category", "other"))
        by_category.setdefault(category, []).append(item)

    lines = [
        "# Autopipeline Output Index",
        "",
        "Generated automatically after autopipeline run.",
        "",
        f"- Runtime config: `{runtime_path}`",
        f"- Stage summary: `{reports_dir / 'pipeline_stage_summary.json'}`",
        f"- Review manifest: `{review_manifest}`",
        f"- Weekly rc: `{stage_summary.get('weekly_rc')}`",
        f"- Strictness: `{stage_summary.get('strictness')}`",
        f"- Skip consolidated report: `{stage_summary.get('skip_consolidated_report')}`",
        "",
        "## Stage Articulation",
        "",
    ]
    for stage in stage_summary.get("stages", []):
        status = "OK" if bool(stage.get("exists")) else "MISSING"
        lines.append(f"- `{stage.get('stage')}`: **{status}**")

    for category in sorted(by_category.keys()):
        lines.extend(["", f"## {category.title()} Links", ""])
        for item in by_category[category]:
            title = str(item.get("title", "artifact"))
            path = str(item.get("path", ""))
            exists = bool(item.get("exists", False))
            status = "OK" if exists else "MISSING"
            lines.append(f"- {title}: `{path}` ({status})")
            public_url = _docs_public_url(repo_root, path, site_url)
            if public_url:
                lines.append(f"  Public URL: {public_url}")

    rag = manifest_json.get("rag_metadata", {})
    if isinstance(rag, dict) and rag:
        lines.extend(["", "## RAG Metadata", ""])
        for key, value in rag.items():
            lines.append(f"- `{key}`: `{value}`")

    lines.extend(
        [
            "",
            "## Browse/Searchability",
            "",
            "- Browsability: hierarchical navigation (MkDocs nav + cross-links) with stable page paths.",
            "- Searchability: faceted index (`docs/assets/facets-index.json`) + retrieval index (`docs/assets/knowledge-retrieval-index.json`).",
            "- AI retrieval: knowledge graph (`docs/assets/knowledge-graph.jsonld`) + retrieval eval reports.",
            "",
        ]
    )

    out = reports_dir / "AUTOPIPELINE_OUTPUT_INDEX.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def _publish_output_index_to_docs(repo_root: Path, output_index: Path) -> Path | None:
    docs_ops = repo_root / "docs" / "operations"
    if not docs_ops.exists():
        return None
    target = docs_ops / "AUTOPIPELINE_OUTPUT_INDEX.md"
    header = [
        "---",
        'title: "Autopipeline Output Index"',
        'description: "Auto-generated review index for autopipeline outputs."',
        "content_type: reference",
        "product: both",
        "tags:",
        "  - Reference",
        "  - Pipeline",
        "  - Review",
        "---",
        "",
    ]
    body = output_index.read_text(encoding="utf-8")
    target.write_text("\n".join(header) + body, encoding="utf-8")
    return target


def _build_llm_review_packet(reports_dir: Path, runtime_path: Path, review_manifest: Path) -> Path:
    consolidated = reports_dir / "consolidated_report.json"
    multi_protocol = reports_dir / "multi_protocol_contract_report.json"
    scorecard = reports_dir / "audit_scorecard.json"

    packet = {
        "runtime_config": str(runtime_path),
        "consolidated_report": str(consolidated),
        "multi_protocol_report": str(multi_protocol),
        "audit_scorecard": str(scorecard),
        "review_manifest": str(reports_dir / "review_manifest.json"),
        "instruction": (
            "Analyze reports as a strict docs-ops reviewer. "
            "List critical/major findings, provide exact remediation actions, "
            "and confirm publish readiness."
        ),
    }

    out_json = reports_dir / "local_llm_review_packet.json"
    out_md = reports_dir / "LOCAL_LLM_REVIEW_PACKET.md"
    out_json.write_text(json.dumps(packet, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    out_md.write_text(
        "\n".join(
            [
                "# Local LLM Review Packet",
                "",
                "Use this packet after autopipeline run.",
                "",
                f"- Runtime config: `{runtime_path}`",
                f"- Consolidated report: `{consolidated}`",
                f"- Multi-protocol report: `{multi_protocol}`",
                f"- Audit scorecard: `{scorecard}`",
                f"- Review manifest: `{review_manifest}`",
                "",
                "Prompt for local LLM:",
                "",
                "```text",
                packet["instruction"],
                "Evaluate report quality, drift, risks, and publish readiness.",
                "Output: 1) critical issues, 2) exact fixes, 3) final go/no-go.",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return out_md


def main() -> int:
    load_local_env(REPO_ROOT)
    parser = argparse.ArgumentParser(description="Run unified smooth docs-ops autopipeline")
    parser.add_argument("--docsops-root", default="docsops")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--since", type=int, default=7)
    parser.add_argument("--runtime-config", default="")
    parser.add_argument(
        "--mode",
        choices=["operator", "veridoc"],
        default="operator",
        help="operator: local LLM packet + optional review; veridoc: fully automated flow",
    )
    parser.add_argument(
        "--skip-local-llm-packet",
        action="store_true",
        help="Skip review packet generation (mostly for fully automated veridoc mode)",
    )
    parser.add_argument(
        "--skip-consolidated-report",
        action="store_true",
        help="Allow skipping consolidated report stage for non-cron/manual runs",
    )
    args = parser.parse_args()

    repo_root = Path.cwd()
    docsops_root = (repo_root / args.docsops_root).resolve()
    runtime_path = Path(args.runtime_config).resolve() if args.runtime_config else (docsops_root / "config" / "client_runtime.yml")
    reports_dir = (repo_root / args.reports_dir).resolve()
    reports_dir.mkdir(parents=True, exist_ok=True)

    if not runtime_path.exists():
        raise FileNotFoundError(f"Runtime config not found: {runtime_path}")

    runtime = _read_yaml(runtime_path)
    strictness = str(runtime.get("api_governance", {}).get("strictness", "standard")).strip().lower() or "standard"
    modules = runtime.get("modules", {})
    api_first = runtime.get("api_first", {})
    protocol_settings = runtime.get("api_protocol_settings", {})
    if not isinstance(modules, dict):
        modules = {}
    if not isinstance(api_first, dict):
        api_first = {}
    if not isinstance(protocol_settings, dict):
        protocol_settings = {}

    generate_assets = bool(api_first.get("generate_test_assets", False))
    upload_assets = bool(api_first.get("upload_test_assets", False))
    for cfg in protocol_settings.values():
        if isinstance(cfg, dict):
            generate_assets = generate_assets or bool(cfg.get("generate_test_assets", False))
            upload_assets = upload_assets or bool(cfg.get("upload_test_assets", False))

    execution_stages = [
        "weekly docs-ops run",
        "artifact verification (protocol contracts)",
        "artifact verification (quality + governance)",
    ]
    if generate_assets:
        execution_stages.append("artifact verification (test assets)")
    if upload_assets:
        execution_stages.append("artifact verification (test asset uploads)")
    if bool(modules.get("rag_optimization", True)) or bool(modules.get("ontology_graph", True)) or bool(modules.get("retrieval_evals", True)):
        execution_stages.append("artifact verification (RAG)")
    execution_stages.extend(["stage summary", "review manifest"])
    if not args.skip_local_llm_packet and args.mode == "operator":
        execution_stages.append("local review packet")
    execution_stages.extend(["output index and links", "publish docs review index"])
    total_stages = len(execution_stages)

    _say(f"Execution mode={args.mode}", f"strictness={strictness}")
    _say("Execution plan", f"{total_stages} stages")
    stage_no = 1
    _say(f"Stage {stage_no}/{total_stages}", execution_stages[stage_no - 1])

    weekly_cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "run_weekly_gap_batch.py"),
        "--docsops-root",
        str(docsops_root),
        "--reports-dir",
        str(reports_dir),
        "--since",
        str(args.since),
        "--runtime-config",
        str(runtime_path),
    ]
    if args.skip_consolidated_report:
        weekly_cmd.append("--skip-consolidated-report")
    rc = _run(weekly_cmd, cwd=repo_root)
    _say(f"Stage {stage_no}/{total_stages} done", f"rc={rc}")
    stage_no += 1
    _say(f"Stage {stage_no}/{total_stages}", execution_stages[stage_no - 1])

    stage_summary = _build_stage_summary(
        runtime=runtime,
        repo_root=repo_root,
        reports_dir=reports_dir,
        weekly_rc=rc,
        strictness=strictness,
        skip_consolidated_report=bool(args.skip_consolidated_report),
    )
    _say(
        f"Stage {stage_no}/{total_stages} done",
        f"required_missing={stage_summary.get('missing_required_artifacts', 0)}",
    )

    stage_no += 1
    _say(f"Stage {stage_no}/{total_stages}", execution_stages[stage_no - 1])
    quality_prefixes = ("audit_", "finalize_", "docsops_", "ready_", "kpi_", "glossary_")
    quality_checks = [s for s in stage_summary.get("stages", []) if str(s.get("stage", "")).startswith(quality_prefixes)]
    missing_quality = sum(1 for s in quality_checks if bool(s.get("required", False)) and not bool(s.get("exists", False)))
    _say(f"Stage {stage_no}/{total_stages} done", f"required_missing={missing_quality}")

    if generate_assets:
        stage_no += 1
        _say(f"Stage {stage_no}/{total_stages}", execution_stages[stage_no - 1])
        test_checks = [s for s in stage_summary.get("stages", []) if str(s.get("stage", "")).startswith("test_assets_")]
        missing_tests = sum(1 for s in test_checks if bool(s.get("required", False)) and not bool(s.get("exists", False)))
        _say(f"Stage {stage_no}/{total_stages} done", f"required_missing={missing_tests}")
    if upload_assets:
        stage_no += 1
        _say(f"Stage {stage_no}/{total_stages}", execution_stages[stage_no - 1])
        upload_checks = [s for s in stage_summary.get("stages", []) if str(s.get("stage", "")) == "test_assets_upload_report"]
        missing_upload = sum(1 for s in upload_checks if bool(s.get("required", False)) and not bool(s.get("exists", False)))
        _say(f"Stage {stage_no}/{total_stages} done", f"required_missing={missing_upload}")
    if bool(modules.get("rag_optimization", True)) or bool(modules.get("ontology_graph", True)) or bool(modules.get("retrieval_evals", True)):
        stage_no += 1
        _say(f"Stage {stage_no}/{total_stages}", execution_stages[stage_no - 1])
        rag_prefixes = ("rag_", "knowledge_graph", "retrieval_")
        rag_checks = [s for s in stage_summary.get("stages", []) if str(s.get("stage", "")).startswith(rag_prefixes)]
        missing_rag = sum(1 for s in rag_checks if bool(s.get("required", False)) and not bool(s.get("exists", False)))
        _say(f"Stage {stage_no}/{total_stages} done", f"required_missing={missing_rag}")

    stage_no += 1
    _say(f"Stage {stage_no}/{total_stages}", execution_stages[stage_no - 1])
    stage_summary_path = reports_dir / "pipeline_stage_summary.json"
    stage_summary_path.write_text(json.dumps(stage_summary, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    _say(f"Stage {stage_no}/{total_stages} done", str(stage_summary_path))

    stage_no += 1
    _say(f"Stage {stage_no}/{total_stages}", execution_stages[stage_no - 1])
    review_manifest = _write_review_manifest(
        reports_dir,
        runtime_path,
        runtime,
        repo_root,
        stage_summary,
        skip_consolidated_report=bool(args.skip_consolidated_report),
    )
    _say(f"Stage {stage_no}/{total_stages} done", str(review_manifest))

    if rc != 0 and strictness == "enterprise-strict":
        print("[autopipeline] failed in enterprise-strict mode")
        return rc
    if int(stage_summary.get("missing_required_artifacts", 0)) > 0 and strictness == "enterprise-strict":
        print("[autopipeline] missing required artifacts in enterprise-strict mode")
        return 1

    if not args.skip_local_llm_packet and args.mode == "operator":
        stage_no += 1
        _say(f"Stage {stage_no}/{total_stages}", execution_stages[stage_no - 1])
        packet_path = _build_llm_review_packet(reports_dir, runtime_path, review_manifest)
        _say(f"Stage {stage_no}/{total_stages} done", str(packet_path))
    elif args.mode == "veridoc":
        _say("Stage local review packet", "skipped in veridoc mode")

    stage_no += 1
    _say(f"Stage {stage_no}/{total_stages}", execution_stages[stage_no - 1])
    output_index = _write_output_index(
        reports_dir=reports_dir,
        runtime_path=runtime_path,
        stage_summary=stage_summary,
        review_manifest=review_manifest,
        repo_root=repo_root,
    )
    _say(f"Stage {stage_no}/{total_stages} done", str(output_index))
    stage_no += 1
    _say(f"Stage {stage_no}/{total_stages}", execution_stages[stage_no - 1])
    published = _publish_output_index_to_docs(repo_root, output_index)
    if published is not None:
        _say(f"Stage {stage_no}/{total_stages} done", str(published))
    else:
        _say(f"Stage {stage_no}/{total_stages} done", "docs/operations not present")
    _say("Done", "all outputs indexed for review")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

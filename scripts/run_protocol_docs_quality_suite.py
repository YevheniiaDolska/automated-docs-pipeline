#!/usr/bin/env python3
"""Run docs-quality suite for generated protocol API docs."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _run(step: str, cmd: list[str], cwd: Path, *, non_blocking: bool = False) -> dict[str, object]:
    completed = subprocess.run(cmd, cwd=str(cwd), check=False)
    ok = completed.returncode == 0 or non_blocking
    return {
        "step": step,
        "ok": ok,
        "rc": int(completed.returncode),
        "command": cmd,
        "non_blocking": bool(non_blocking),
    }


def _semantic_markers(protocol: str) -> list[str]:
    mapping = {
        "graphql": ["semantic-fallback", "simulated_response", "Unknown query. Use:"],
        "grpc": ["semantic-fallback", "simulated_response", "UNIMPLEMENTED"],
        "asyncapi": ["Sandbox semantic mode", "simulated_response", "project.updated", "task.completed"],
        "websocket": ["Sandbox semantic mode", "simulated_response", "subscribe", "publish", "list_projects"],
    }
    return mapping.get(protocol, [])


def _forbidden_semantic_patterns(protocol: str) -> list[str]:
    mapping = {
        "asyncapi": [
            "out.textContent = 'Endpoint: ' + endpoint + '\\nResponse: ' + e.data;",
            "Connection failed for all sandbox endpoints.'\n          - '\\nTried: '",
        ],
        "websocket": [
            "wsConn.onmessage = function (e) { log('Received: ' + e.data); };",
            "if (!wsConn || wsConn.readyState !== 1) { log('Not connected. Click Connect first.'); return; }",
        ],
    }
    return mapping.get(protocol, [])


def main() -> int:
    parser = argparse.ArgumentParser(description="Run protocol docs quality suite")
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--generated-doc", required=True)
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--required-languages", default="curl,javascript,python")
    parser.add_argument("--glossary", default="glossary.yml")
    parser.add_argument("--modules-dir", default="")
    parser.add_argument("--retrieval-index-output", default="docs/assets/knowledge-retrieval-index.json")
    parser.add_argument("--knowledge-graph-output", default="docs/assets/knowledge-graph.jsonld")
    parser.add_argument("--rag-refresh", action="store_true", default=True)
    parser.add_argument("--rag-strict", action="store_true")
    parser.add_argument("--json-report", default="")
    parser.add_argument("--semantic-required", action="store_true", default=True)
    args = parser.parse_args()

    repo_root = Path.cwd()
    scripts_dir = Path(__file__).resolve().parent
    py = sys.executable

    generated_doc = Path(args.generated_doc)
    if not generated_doc.is_absolute():
        generated_doc = (repo_root / generated_doc).resolve()

    docs_root = Path(args.docs_root)
    if not docs_root.is_absolute():
        docs_root = (repo_root / docs_root).resolve()

    reports_dir = Path(args.reports_dir)
    if not reports_dir.is_absolute():
        reports_dir = (repo_root / reports_dir).resolve()
    reports_dir.mkdir(parents=True, exist_ok=True)

    required_languages = str(args.required_languages).strip() or "curl,javascript,python"
    # Scope checks to the generated doc directory by default to avoid unrelated repo-wide failures.
    docs_scope_dir = generated_doc.parent if generated_doc.exists() else docs_root

    steps: list[dict[str, object]] = []

    normalize_docs = scripts_dir / "normalize_docs.py"
    if normalize_docs.exists() and generated_doc.exists():
        steps.append(_run("normalize_docs", [py, str(normalize_docs), str(generated_doc)], repo_root))

    lint_snippets = scripts_dir / "lint_code_snippets.py"
    if lint_snippets.exists() and generated_doc.exists():
        steps.append(_run("lint_code_snippets", [py, str(lint_snippets), str(generated_doc)], repo_root))

    multilang_generator = scripts_dir / "generate_multilang_tabs.py"
    if multilang_generator.exists() and generated_doc.exists():
        steps.append(
            _run(
                "generate_multilang_tabs",
                [py, str(multilang_generator), "--paths", str(generated_doc), "--scope", "api", "--write"],
                repo_root,
            )
        )

    multilang_validator = scripts_dir / "validate_multilang_examples.py"
    if multilang_validator.exists() and docs_scope_dir.exists():
        steps.append(
            _run(
                "validate_multilang_examples",
                [
                    py,
                    str(multilang_validator),
                    "--docs-dir",
                    str(docs_scope_dir),
                    "--scope",
                    "api",
                    "--required-languages",
                    required_languages,
                    "--report",
                    str(reports_dir / f"{args.protocol}_multilang_examples_report.json"),
                ],
                repo_root,
            )
        )

    smoke = scripts_dir / "check_code_examples_smoke.py"
    if smoke.exists() and generated_doc.exists():
        steps.append(
            _run(
                "check_code_examples_smoke",
                [
                    py,
                    str(smoke),
                    "--paths",
                    str(generated_doc),
                    "--allow-empty",
                    "--report",
                    str(reports_dir / f"{args.protocol}_smoke_examples_report.json"),
                ],
                repo_root,
            )
        )

    seo_geo = scripts_dir / "seo_geo_optimizer.py"
    if seo_geo.exists() and generated_doc.exists():
        steps.append(
            _run(
                "seo_geo_optimizer",
                [
                    py,
                    str(seo_geo),
                    str(generated_doc),
                    "--fix",
                    "--output",
                    str(reports_dir / f"{args.protocol}_seo_geo_report.json"),
                ],
                repo_root,
            )
        )

    glossary_sync = scripts_dir / "sync_project_glossary.py"
    glossary = Path(args.glossary)
    if not glossary.is_absolute():
        glossary = (repo_root / glossary).resolve()
    if glossary_sync.exists() and generated_doc.exists():
        steps.append(
            _run(
                "sync_project_glossary",
                [
                    py,
                    str(glossary_sync),
                    "--paths",
                    str(generated_doc),
                    "--glossary",
                    str(glossary),
                    "--report",
                    str(reports_dir / f"{args.protocol}_glossary_sync_report.json"),
                    "--write",
                ],
                repo_root,
            )
        )

    frontmatter = scripts_dir / "validate_frontmatter.py"
    frontmatter_schema = repo_root / "docs-schema.yml"
    if frontmatter.exists():
        if frontmatter_schema.exists():
            steps.append(_run("validate_frontmatter", [py, str(frontmatter)], repo_root))
        else:
            steps.append(
                {
                    "step": "validate_frontmatter",
                    "ok": True,
                    "rc": 0,
                    "command": ["skip", "docs-schema.yml not found"],
                }
            )

    if bool(args.rag_refresh):
        rag_marker = reports_dir / ".protocol_rag_refresh_done"
        if not rag_marker.exists():
            extract_modules = scripts_dir / "extract_knowledge_modules_from_docs.py"
            validate_modules = scripts_dir / "validate_knowledge_modules.py"
            detect_contradictions = scripts_dir / "detect_rag_contradictions.py"
            build_index = scripts_dir / "generate_knowledge_retrieval_index.py"
            build_graph = scripts_dir / "generate_knowledge_graph_jsonld.py"
            retrieval_eval = scripts_dir / "run_retrieval_evals.py"

            if str(args.modules_dir).strip():
                modules_dir = Path(args.modules_dir)
                if not modules_dir.is_absolute():
                    modules_dir = (repo_root / modules_dir).resolve()
            else:
                modules_dir = (reports_dir / "knowledge_modules_auto").resolve()
            retrieval_index_output = Path(args.retrieval_index_output)
            if not retrieval_index_output.is_absolute():
                retrieval_index_output = (repo_root / retrieval_index_output).resolve()
            knowledge_graph_output = Path(args.knowledge_graph_output)
            if not knowledge_graph_output.is_absolute():
                knowledge_graph_output = (repo_root / knowledge_graph_output).resolve()

            if extract_modules.exists() and docs_root.exists():
                steps.append(
                    _run(
                        "extract_knowledge_modules_from_docs",
                        [
                            py,
                            str(extract_modules),
                            "--docs-dir",
                            str(docs_root),
                            "--modules-dir",
                            str(modules_dir),
                            "--report",
                            str(reports_dir / f"{args.protocol}_knowledge_auto_extract_report.json"),
                        ],
                        repo_root,
                    )
                )
            if validate_modules.exists() and modules_dir.exists():
                steps.append(
                    _run(
                        "validate_knowledge_modules",
                        [
                            py,
                            str(validate_modules),
                            "--modules-dir",
                            str(modules_dir),
                            "--report",
                            str(reports_dir / f"{args.protocol}_knowledge_modules_report.json"),
                        ],
                        repo_root,
                    )
                )
            contradictions_report = reports_dir / f"{args.protocol}_rag_contradictions_report.json"
            if detect_contradictions.exists() and modules_dir.exists():
                steps.append(
                    _run(
                        "detect_rag_contradictions",
                        [
                            py,
                            str(detect_contradictions),
                            "--modules-dir",
                            str(modules_dir),
                            "--report",
                            str(contradictions_report),
                            "--stale-days",
                            "180",
                        ],
                        repo_root,
                    )
                )
            if build_index.exists() and modules_dir.exists():
                index_cmd = [
                    py,
                    str(build_index),
                    "--modules-dir",
                    str(modules_dir),
                    "--output",
                    str(retrieval_index_output),
                ]
                if contradictions_report.exists():
                    index_cmd.extend(
                        [
                            "--contradictions-report",
                            str(contradictions_report),
                            "--exclude-critical-contradictions",
                        ]
                    )
                steps.append(
                    _run(
                        "generate_knowledge_retrieval_index",
                        index_cmd,
                        repo_root,
                    )
                )
            if build_graph.exists() and modules_dir.exists():
                steps.append(
                    _run(
                        "generate_knowledge_graph_jsonld",
                        [
                            py,
                            str(build_graph),
                            "--modules-dir",
                            str(modules_dir),
                            "--output",
                            str(knowledge_graph_output),
                            "--report",
                            str(reports_dir / f"{args.protocol}_knowledge_graph_report.json"),
                        ],
                        repo_root,
                    )
                )
            if retrieval_eval.exists() and retrieval_index_output.exists():
                steps.append(
                    _run(
                        "run_retrieval_evals",
                        [
                            py,
                            str(retrieval_eval),
                            "--index",
                            str(retrieval_index_output),
                            "--auto-generate-dataset",
                            "--dataset-out",
                            str(reports_dir / f"{args.protocol}_retrieval_eval_dataset.generated.yml"),
                            "--report",
                            str(reports_dir / f"{args.protocol}_retrieval_evals_report.json"),
                        ],
                        repo_root,
                        non_blocking=not bool(args.rag_strict),
                    )
                )

            rag_marker.write_text("done\n", encoding="utf-8")
        else:
            steps.append(
                {
                    "step": "rag_refresh",
                    "ok": True,
                    "rc": 0,
                    "command": ["skip", "already refreshed in this run"],
                }
            )

    protocol_key = str(args.protocol).strip().lower()
    if bool(args.semantic_required) and protocol_key in {"graphql", "grpc", "asyncapi", "websocket"}:
        if not generated_doc.exists():
            steps.append(
                {
                    "step": "semantic_consistency",
                    "ok": False,
                    "rc": 1,
                    "command": ["missing_generated_doc", str(generated_doc)],
                    "missing_markers": _semantic_markers(protocol_key),
                }
            )
        else:
            content = generated_doc.read_text(encoding="utf-8")
            required = _semantic_markers(protocol_key)
            missing = [marker for marker in required if marker not in content]
            steps.append(
                {
                    "step": "semantic_consistency",
                    "ok": not bool(missing),
                    "rc": 0 if not missing else 1,
                    "command": ["marker_scan", str(generated_doc)],
                    "missing_markers": missing,
                }
            )

            forbidden = _forbidden_semantic_patterns(protocol_key)
            found_forbidden = [pattern for pattern in forbidden if pattern in content]
            steps.append(
                {
                    "step": "semantic_conflict_scan",
                    "ok": not bool(found_forbidden),
                    "rc": 0 if not found_forbidden else 1,
                    "command": ["forbidden_pattern_scan", str(generated_doc)],
                    "forbidden_patterns_found": found_forbidden,
                }
            )

    failed = [item for item in steps if not bool(item["ok"])]
    payload = {
        "protocol": args.protocol,
        "generated_doc": str(generated_doc),
        "docs_root": str(docs_root),
        "steps": steps,
        "failed_steps": [str(item["step"]) for item in failed],
        "ok": not bool(failed),
    }

    report_path = Path(args.json_report) if str(args.json_report).strip() else reports_dir / f"{args.protocol}_quality_suite_report.json"
    if not report_path.is_absolute():
        report_path = (repo_root / report_path).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    print(f"[protocol-quality-suite] report: {report_path}")
    if failed:
        for item in failed:
            print(f"[protocol-quality-suite] failed: {item['step']} rc={item['rc']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

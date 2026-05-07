#!/usr/bin/env python3
"""Run full docs quality audit for a client bundle and write unified reports.

The script executes pipeline-aligned quality checks and produces:
- JSON machine report
- Markdown human summary
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class StepResult:
    step: str
    required: bool
    executed: bool
    ok: bool
    rc: int
    duration_sec: float
    command: list[str]
    detail: str


def _check_paths_exist(repo_root: Path, rel_paths: list[str]) -> tuple[bool, list[str]]:
    """Internal helper for `_check_paths_exist`."""
    missing: list[str] = []
    for rel in rel_paths:
        if not (repo_root / rel).exists():
            missing.append(rel)
    return len(missing) == 0, missing


def _split_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
    """Internal helper for `_split_frontmatter`."""
    if not raw.startswith("---\n"):
        return {}, raw
    parts = raw.split("---\n", 2)
    if len(parts) < 3:
        return {}, raw
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except (RuntimeError, ValueError, TypeError):
        fm = {}
    if not isinstance(fm, dict):
        fm = {}
    return fm, parts[2]


def _first_paragraph_words(body: str) -> list[str]:
    """Internal helper for `_first_paragraph_words`."""
    chunks = [c.strip() for c in body.strip().split("\n\n") if c.strip()]
    if not chunks:
        return []
    para = chunks[0]
    return re.findall(r"\b[\w\-]+\b", para)


def _markdown_word_count_until_code(body: str) -> int:
    """Internal helper for `_markdown_word_count_until_code`."""
    words = 0
    for line in body.splitlines():
        if line.strip().startswith("```"):
            break
        words += len(re.findall(r"\b[\w\-]+\b", line))
    return words


def _run_process_compliance_checks(repo_root: Path, docs_root: str) -> dict[str, Any]:
    """Internal helper for `_run_process_compliance_checks`."""
    docs_path = (repo_root / docs_root).resolve()
    md_files = sorted(p for p in docs_path.rglob("*.md") if p.is_file())
    placeholders = ["[Topic]", "[one-sentence definition]", "actual-value", "test123", "[specific"]
    issues: list[dict[str, str]] = []
    checked = 0

    for path in md_files:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        fm, body = _split_frontmatter(raw)
        rel = str(path.relative_to(repo_root))
        checked += 1

        words = _first_paragraph_words(body)
        if words and len(words) > 60:
            issues.append({"file": rel, "type": "first_paragraph_gt_60_words"})

        code_position = _markdown_word_count_until_code(body)
        if "```" in body and code_position > 200:
            issues.append({"file": rel, "type": "first_code_after_200_words"})

        for token in placeholders:
            if token in raw:
                issues.append({"file": rel, "type": f"placeholder_token:{token}"})
                break

        ct = str(fm.get("content_type", "")).strip().lower()
        if ct:
            template_map = {
                "tutorial": "templates/tutorial.md",
                "how-to": "templates/how-to.md",
                "concept": "templates/concept.md",
                "reference": "templates/reference.md",
                "troubleshooting": "templates/troubleshooting.md",
                "release-note": "templates/release-note.md",
            }
            tpl = template_map.get(ct)
            if tpl and not (repo_root / tpl).exists():
                issues.append({"file": rel, "type": f"missing_template_for_content_type:{ct}"})

    trace_path = repo_root / "reports/generation_trace_report.json"
    trace_ok = True
    trace_issue = ""
    if trace_path.exists():
        try:
            payload = json.loads(trace_path.read_text(encoding="utf-8"))
        except (RuntimeError, ValueError, TypeError, OSError):
            payload = {}
        events = payload.get("events", []) if isinstance(payload, dict) else []
        if isinstance(events, list):
            last_template_idx = -1
            for idx, ev in enumerate(events):
                if not isinstance(ev, dict):
                    continue
                event = str(ev.get("event", "")).strip()
                if event in {"template_used", "template_created"}:
                    last_template_idx = idx
                if event == "doc_created":
                    if last_template_idx < 0 or last_template_idx > idx:
                        trace_ok = False
                        trace_issue = "doc_created_without_prior_template_event"
                        break
            has_doc = any(isinstance(ev, dict) and ev.get("event") == "doc_created" for ev in events)
            has_glossary = any(isinstance(ev, dict) and ev.get("event") == "glossary_sync" for ev in events)
            if has_doc and not has_glossary:
                trace_ok = False
                trace_issue = "missing_glossary_sync_event_for_created_docs"
        else:
            trace_ok = False
            trace_issue = "invalid_trace_events_format"
    else:
        trace_ok = False
        trace_issue = "generation_trace_report_missing"

    if not trace_ok:
        issues.append({"file": "reports/generation_trace_report.json", "type": trace_issue})

    ok = len(issues) == 0
    return {"ok": ok, "checked_files": checked, "issues": issues}


def _read_yaml(path: Path) -> dict[str, Any]:
    """Internal helper for `_read_yaml`."""
    if not path.exists():
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (RuntimeError, ValueError, TypeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _run(cmd: list[str], cwd: Path, timeout_sec: int) -> tuple[int, float, str]:
    """Internal helper for `_run`."""
    started = time.monotonic()
    print(f"[bundle-audit] $ {' '.join(shlex.quote(x) for x in cmd)}")
    completed = subprocess.run(
        cmd,
        cwd=str(cwd),
        check=False,
        text=True,
        capture_output=True,
        timeout=timeout_sec,
    )
    elapsed = time.monotonic() - started
    detail = ((completed.stdout or "") + "\n" + (completed.stderr or "")).strip()
    return int(completed.returncode), elapsed, detail


def _append(results: list[StepResult], item: StepResult) -> None:
    """Internal helper for `_append`."""
    results.append(item)
    state = "ok" if item.ok else "fail"
    print(f"[bundle-audit] {item.step}: {state} rc={item.rc} ({item.duration_sec:.1f}s)")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """Internal helper for `_write_json`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_md(path: Path, payload: dict[str, Any]) -> None:
    """Internal helper for `_write_md`."""
    lines: list[str] = []
    lines.append("# Bundle docs quality audit")
    lines.append("")
    lines.append(f"- Overall: **{'PASS' if payload['ok'] else 'FAIL'}**")
    lines.append(f"- Score: **{payload['score_percent']:.1f}%**")
    lines.append(f"- Required steps passed: **{payload['required_passed']}/{payload['required_total']}**")
    lines.append(f"- Executed steps passed: **{payload['executed_passed']}/{payload['executed_total']}**")
    lines.append("")
    lines.append("## Steps")
    lines.append("")
    for item in payload["steps"]:
        status = "PASS" if item["ok"] else "FAIL"
        req = "required" if item["required"] else "optional"
        lines.append(f"- `{item['step']}`: **{status}** ({req}, rc={item['rc']}, {item['duration_sec']:.1f}s)")
    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    for art in payload["artifacts"]:
        exists = "yes" if art["exists"] else "no"
        lines.append(f"- `{art['name']}`: {exists} (`{art['path']}`)")
    lines.append("")
    lines.append("## Functional coverage")
    lines.append("")
    lines.append(f"- Coverage score: **{payload['functional_coverage']['score_percent']:.1f}%**")
    for item in payload["functional_coverage"]["checks"]:
        status = "PASS" if item["ok"] else "FAIL"
        lines.append(f"- `{item['name']}`: **{status}**")
        if item.get("missing"):
            lines.append(f"  missing: {', '.join(item['missing'])}")
    lines.append("")
    lines.append("## Process compliance")
    lines.append("")
    pc = payload.get("process_compliance", {})
    lines.append(f"- Overall: **{'PASS' if pc.get('ok') else 'FAIL'}**")
    lines.append(f"- Checked docs files: **{pc.get('checked_files', 0)}**")
    lines.append(f"- Issues: **{len(pc.get('issues', []))}**")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    """Execute `parse_args` workflow."""
    parser = argparse.ArgumentParser(description="Audit client bundle docs quality")
    parser.add_argument("--repo-root", default=".", help="Client repo root")
    parser.add_argument("--docs-root", default="docs", help="Docs directory")
    parser.add_argument("--runtime-config", default="docsops/config/client_runtime.yml")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--timeout-sec", type=int, default=1800, help="Timeout per command")
    parser.add_argument("--run-autopipeline", action="store_true", help="Run full autopipeline before quality checks")
    parser.add_argument("--since-days", type=int, default=7, help="Autopipeline lookback window")
    parser.add_argument("--mode", default="operator", choices=["operator", "veridoc"], help="Autopipeline mode")
    parser.add_argument("--strict-gates", action="store_true", help="Run mandatory gates in strict mode")
    parser.add_argument("--output-json", default="reports/bundle_docs_quality_audit.json")
    parser.add_argument("--output-md", default="reports/bundle_docs_quality_audit.md")
    return parser.parse_args()


def main() -> int:
    """Execute `main` workflow."""
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    docs_root = str(args.docs_root).strip() or "docs"
    reports_dir = (repo_root / args.reports_dir).resolve()
    runtime = _read_yaml((repo_root / args.runtime_config).resolve())

    modules = runtime.get("modules", {}) if isinstance(runtime.get("modules"), dict) else {}
    rag_enabled = bool(modules.get("rag_optimization", True) or modules.get("knowledge_validation", True))
    graph_enabled = bool(modules.get("ontology_graph", True))
    eval_enabled = bool(modules.get("retrieval_evals", True))

    results: list[StepResult] = []

    commands: list[tuple[str, bool, list[str]]] = []
    if args.run_autopipeline:
        commands.append(
            (
                "autopipeline",
                True,
                [
                    "python3",
                    "scripts/run_autopipeline.py",
                    "--docsops-root",
                    "docsops",
                    "--reports-dir",
                    str(reports_dir),
                    "--since",
                    str(int(args.since_days)),
                    "--runtime-config",
                    args.runtime_config,
                    "--mode",
                    args.mode,
                    "--auto-generate",
                    "--skip-consolidated-report",
                ],
            )
        )

    commands.extend([
        ("npm_lint", True, ["npm", "run", "lint"]),
        ("docs_ci_checks", True, ["python3", "scripts/run_docs_ci_checks.py", "--runtime-config", args.runtime_config]),
        ("mandatory_gates", True, ["python3", "scripts/run_mandatory_gates.py", "--runtime-config", args.runtime_config, "--output", str(reports_dir / "mandatory_run_gates_report.json")] + (["--strict"] if args.strict_gates else [])),
        ("mkdocs_build", True, ["mkdocs", "build", "--strict"]),
        ("frontmatter", True, ["python3", "scripts/validate_frontmatter.py"]),
        ("snippet_lint", True, ["python3", "scripts/lint_code_snippets.py", docs_root]),
        ("examples_smoke", True, ["python3", "scripts/check_code_examples_smoke.py", docs_root]),
        ("seo_geo", True, ["python3", "scripts/seo_geo_optimizer.py", docs_root]),
        (
            "lifecycle_management",
            True,
            [
                "python3",
                "scripts/lifecycle_manager.py",
                "--docs-dir",
                docs_root,
                "--scan",
                "--report",
                "--json-output",
                str(reports_dir / "lifecycle_scan.json"),
            ],
        ),
        (
            "glossary_alignment",
            True,
            [
                "python3",
                "scripts/sync_project_glossary.py",
                "--paths",
                docs_root,
                "--glossary",
                "glossary.yml",
                "--report",
                str(reports_dir / "glossary_sync_report.json"),
            ],
        ),
        (
            "knowledge_extract",
            rag_enabled,
            [
                "python3",
                "scripts/extract_knowledge_modules_from_docs.py",
                "--docs-dir",
                docs_root,
                "--modules-dir",
                "knowledge_modules",
                "--report",
                str(reports_dir / "knowledge_auto_extract_report.json"),
            ],
        ),
        ("knowledge_validate", rag_enabled, ["python3", "scripts/validate_knowledge_modules.py"]),
        ("contradictions", rag_enabled, ["python3", "scripts/detect_rag_contradictions.py"]),
        ("retrieval_index", rag_enabled, ["python3", "scripts/generate_knowledge_retrieval_index.py"]),
        (
            "knowledge_graph",
            graph_enabled and rag_enabled,
            [
                "python3",
                "scripts/generate_knowledge_graph_jsonld.py",
                "--modules-dir",
                "knowledge_modules",
                "--output",
                "docs/assets/knowledge-graph.jsonld",
                "--report",
                str(reports_dir / "knowledge_graph_report.json"),
            ],
        ),
        ("retrieval_eval_gate", eval_enabled and rag_enabled, ["python3", "scripts/run_retrieval_evals_gate.py"]),
        (
            "event_contract_validation",
            True,
            [
                "python3",
                "scripts/validate_event_contract.py",
                "--events-log",
                str(reports_dir / "pipeline_events.ndjson"),
                "--contract",
                "config/event_contract.yml",
                "--output",
                str(reports_dir / "event_contract_validation_report.json"),
            ],
        ),
    ])

    for step_name, required, cmd in commands:
        if not required:
            _append(
                results,
                StepResult(step_name, required=False, executed=False, ok=True, rc=0, duration_sec=0.0, command=cmd, detail="not_required"),
            )
            continue
        try:
            rc, elapsed, detail = _run(cmd, repo_root, args.timeout_sec)
        except subprocess.TimeoutExpired:
            _append(
                results,
                StepResult(step_name, required=True, executed=True, ok=False, rc=124, duration_sec=float(args.timeout_sec), command=cmd, detail="timeout"),
            )
            continue
        _append(
            results,
            StepResult(
                step=step_name,
                required=True,
                executed=True,
                ok=(rc == 0),
                rc=rc,
                duration_sec=elapsed,
                command=cmd,
                detail=detail[-4000:],
            ),
        )

    artifacts = [
        ("consolidated_report", reports_dir / "consolidated_report.json"),
        ("seo_report", reports_dir / "seo-report.json"),
        ("lifecycle_report", repo_root / "lifecycle-report.md"),
        ("lifecycle_scan", reports_dir / "lifecycle_scan.json"),
        ("glossary_sync_report", reports_dir / "glossary_sync_report.json"),
        ("knowledge_extract_report", reports_dir / "knowledge_auto_extract_report.json"),
        ("retrieval_index", repo_root / "docs/assets/knowledge-retrieval-index.json"),
        ("knowledge_graph", repo_root / "docs/assets/knowledge-graph.jsonld"),
        ("contradictions_report", reports_dir / "rag_contradictions_report.json"),
        ("retrieval_eval_report", reports_dir / "retrieval_evals_report.json"),
        ("pipeline_events", reports_dir / "pipeline_events.ndjson"),
        ("event_contract_validation", reports_dir / "event_contract_validation_report.json"),
    ]
    artifact_rows = [{"name": name, "path": str(path), "exists": path.exists()} for name, path in artifacts]
    process_compliance = _run_process_compliance_checks(repo_root, docs_root)

    capability_checks: list[dict[str, Any]] = []
    capability_map: list[tuple[str, list[str]]] = [
        (
            "core_autopipeline",
            [
                "scripts/run_autopipeline.py",
                "scripts/run_weekly_gap_batch.py",
                "scripts/finalize_docs_gate.py",
                "scripts/run_mandatory_gates.py",
            ],
        ),
        (
            "api_first_rest",
            [
                "scripts/run_api_first_flow.py",
                "scripts/generate_openapi_from_planning_notes.py",
                "scripts/validate_openapi_contract.py",
                "scripts/generate_fastapi_stubs_from_openapi.py",
                "scripts/self_verify_api_user_path.py",
            ],
        ),
        (
            "multi_protocol",
            [
                "scripts/run_multi_protocol_contract_flow.py",
                "scripts/validate_graphql_contract.py",
                "scripts/validate_proto_contract.py",
                "scripts/validate_asyncapi_contract.py",
                "scripts/validate_websocket_contract.py",
            ],
        ),
        (
            "knowledge_rag_prep",
            [
                "scripts/extract_knowledge_modules_from_docs.py",
                "scripts/validate_knowledge_modules.py",
                "scripts/detect_rag_contradictions.py",
                "scripts/generate_knowledge_retrieval_index.py",
                "scripts/generate_knowledge_graph_jsonld.py",
                "scripts/run_retrieval_evals_gate.py",
                "scripts/validate_event_contract.py",
                "config/event_contract.yml",
            ],
        ),
        (
            "runtime_and_hardening",
            [
                "scripts/license_gate.py",
                "scripts/pack_runtime.py",
                "scripts/llm_egress.py",
                "docsops/config/client_runtime.yml",
            ],
        ),
        (
            "governance_docs_present",
            [
                "README.md",
                "docs/operations/CANONICAL_FLOW.md",
                "docs/operations/PIPELINE_CAPABILITIES_CATALOG.md",
            ],
        ),
        (
            "lifecycle_and_glossary_tools",
            [
                "scripts/lifecycle_manager.py",
                "scripts/sync_project_glossary.py",
                "glossary.yml",
            ],
        ),
        (
            "template_system_stripe_quality",
            [
                "templates/how-to.md",
                "templates/tutorial.md",
                "templates/reference.md",
                "templates/troubleshooting.md",
                "templates/api-reference.md",
            ],
        ),
        (
            "shared_variables_system",
            [
                "docs/_variables.yml",
            ],
        ),
    ]
    for name, rels in capability_map:
        ok, missing = _check_paths_exist(repo_root, rels)
        capability_checks.append({"name": name, "ok": ok, "missing": missing})

    func_total = len(capability_checks)
    func_passed = sum(1 for row in capability_checks if row["ok"])
    func_score = (func_passed / func_total * 100.0) if func_total else 100.0

    required_total = sum(1 for r in results if r.required)
    required_passed = sum(1 for r in results if r.required and r.ok)
    executed_total = sum(1 for r in results if r.executed)
    executed_passed = sum(1 for r in results if r.executed and r.ok)
    score = (required_passed / required_total * 100.0) if required_total else 100.0

    payload = {
        "ok": required_passed == required_total,
        "score_percent": score,
        "required_total": required_total,
        "required_passed": required_passed,
        "executed_total": executed_total,
        "executed_passed": executed_passed,
        "runtime_config": str((repo_root / args.runtime_config).resolve()),
        "docs_root": docs_root,
        "reports_dir": str(reports_dir),
        "functional_coverage": {
            "passed": func_passed,
            "total": func_total,
            "score_percent": func_score,
            "checks": capability_checks,
        },
        "process_compliance": process_compliance,
        "steps": [
            {
                "step": r.step,
                "required": r.required,
                "executed": r.executed,
                "ok": r.ok,
                "rc": r.rc,
                "duration_sec": round(r.duration_sec, 3),
                "command": r.command,
                "detail": r.detail,
            }
            for r in results
        ],
        "artifacts": artifact_rows,
    }

    out_json = (repo_root / args.output_json).resolve()
    out_md = (repo_root / args.output_md).resolve()
    _write_json(out_json, payload)
    _write_md(out_md, payload)
    print(f"[bundle-audit] report json: {out_json}")
    print(f"[bundle-audit] report md: {out_md}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

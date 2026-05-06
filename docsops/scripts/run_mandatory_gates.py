#!/usr/bin/env python3
"""Bundle-aware mandatory run gates for pilot/full/full+rag.

This script enforces the non-skippable quality and RAG hardening chain per
implementation tier and enabled runtime modules.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.pipeline_event_bus import emit_event


@dataclass
class GateResult:
    gate_id: str
    required: bool
    executed: bool
    ok: bool
    detail: str


def _read_yaml(path: Path) -> dict[str, Any]:
    """Internal helper for `_read_yaml`."""
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _run(cmd: list[str], cwd: Path) -> tuple[bool, str]:
    """Internal helper for `_run`."""
    print(f"[mandatory-gates] $ {' '.join(cmd)}")
    emit_event(
        repo_root=cwd,
        event="mandatory_gate_command_started",
        stage="mandatory_gates",
        status="started",
        payload={"command": cmd},
    )
    completed = subprocess.run(cmd, cwd=str(cwd), check=False)
    emit_event(
        repo_root=cwd,
        event="mandatory_gate_command_finished",
        stage="mandatory_gates",
        status="passed" if completed.returncode == 0 else "failed",
        payload={"command": cmd, "rc": int(completed.returncode)},
    )
    return completed.returncode == 0, f"rc={completed.returncode}"


def _map_license_plan_to_tier(plan: str) -> str:
    """Internal helper for `_map_license_plan_to_tier`."""
    value = str(plan).strip().lower()
    if value == "pilot":
        return "pilot"
    if value == "professional":
        return "full"
    if value == "enterprise":
        return "full+rag"
    if value == "community":
        return "community"
    return "full"


def _detect_tier(runtime: dict[str, Any], explicit_tier: str) -> tuple[str, str]:
    """Internal helper for `_detect_tier`."""
    if explicit_tier != "auto":
        return explicit_tier, "cli"

    try:
        from scripts.license_gate import get_license  # lazy import

        info = get_license()
        tier = _map_license_plan_to_tier(getattr(info, "plan", ""))
        return tier, "license_gate"
    except Exception:  # noqa: BLE001
        pass

    integrations = runtime.get("integrations", {}) if isinstance(runtime.get("integrations"), dict) else {}
    ask_ai = integrations.get("ask_ai", {}) if isinstance(integrations.get("ask_ai"), dict) else {}
    if bool(ask_ai.get("enabled", False)):
        return "full+rag", "runtime.integrations.ask_ai.enabled"

    modules = runtime.get("modules", {}) if isinstance(runtime.get("modules"), dict) else {}
    knowledge = bool(modules.get("knowledge_validation", False) or modules.get("rag_optimization", False))
    if knowledge:
        return "full", "runtime.modules"

    return "pilot", "runtime.fallback"


def _module_enabled(runtime: dict[str, Any], key: str, default: bool = False) -> bool:
    """Internal helper for `_module_enabled`."""
    modules = runtime.get("modules", {}) if isinstance(runtime.get("modules"), dict) else {}
    return bool(modules.get(key, default))


def _artifact_exists(path: Path) -> bool:
    """Internal helper for `_artifact_exists`."""
    return path.exists() and path.is_file()


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    """Internal helper for `_write_report`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    """Execute `parse_args` workflow."""
    parser = argparse.ArgumentParser(description="Run mandatory gates by implementation tier")
    parser.add_argument("--tier", choices=["auto", "community", "pilot", "full", "full+rag"], default="auto")
    parser.add_argument("--runtime-config", default="docsops/config/client_runtime.yml")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--check-only", action="store_true", help="Do not execute commands, only validate artifacts/config")
    parser.add_argument("--strict", action="store_true", help="Fail when expected module is disabled for the selected tier")
    parser.add_argument("--output", default="reports/mandatory_run_gates_report.json")
    return parser.parse_args()


def main() -> int:
    """Execute `main` workflow."""
    args = parse_args()
    repo_root = REPO_ROOT
    runtime_path = (repo_root / args.runtime_config).resolve()
    reports_dir = (repo_root / args.reports_dir).resolve()
    output_path = (repo_root / args.output).resolve()

    runtime = _read_yaml(runtime_path)
    tier, tier_source = _detect_tier(runtime, args.tier)
    emit_event(
        repo_root=repo_root,
        event="mandatory_gates_started",
        stage="mandatory_gates",
        status="started",
        payload={"tier": tier, "tier_source": tier_source},
    )

    gates: list[GateResult] = []
    failed = False

    def apply_command_gate(gate_id: str, required: bool, command: list[str], *, fail_open: bool = False) -> None:
        """Execute `apply_command_gate` workflow."""
        nonlocal failed
        if not required:
            gates.append(GateResult(gate_id, False, False, True, "not_required"))
            return
        if args.check_only:
            gates.append(GateResult(gate_id, True, False, True, "check_only"))
            return
        ok, detail = _run(command, repo_root)
        if ok:
            gates.append(GateResult(gate_id, True, True, True, detail))
            return
        if fail_open:
            gates.append(GateResult(gate_id, True, True, True, f"soft_failed:{detail}"))
            return
        gates.append(GateResult(gate_id, True, True, False, detail))
        if not ok:
            failed = True

    def apply_artifact_gate(gate_id: str, required: bool, path: Path) -> None:
        """Execute `apply_artifact_gate` workflow."""
        nonlocal failed
        if not required:
            gates.append(GateResult(gate_id, False, False, True, "not_required"))
            return
        ok = _artifact_exists(path)
        gates.append(GateResult(gate_id, True, False, ok, str(path)))
        if not ok:
            failed = True

    is_community = tier == "community"
    is_pilot = tier == "pilot"
    is_full = tier in {"full", "full+rag"}
    is_full_rag = tier == "full+rag"
    is_prep_tier = is_pilot or is_full

    # Baseline gates for all tiers
    apply_command_gate("baseline_quality", True, ["npm", "run", "validate:minimal"])
    apply_command_gate(
        "event_contract_validation",
        True,
        [
            "python3",
            "scripts/validate_event_contract.py",
            "--events-log",
            "reports/pipeline_events.ndjson",
            "--contract",
            "config/event_contract.yml",
            "--output",
            "reports/event_contract_validation_report.json",
        ],
    )

    # Full DocsOps gates
    if is_prep_tier:
        apply_command_gate("full_docs_quality", True, ["npm", "run", "lint"])
        code_intelligence_enabled = _module_enabled(runtime, "code_intelligence", True if is_full else False)
        code_intel_cfg = runtime.get("code_intelligence", {}) if isinstance(runtime.get("code_intelligence"), dict) else {}
        code_intel_fail_open = bool(code_intel_cfg.get("fail_open", True))
        if args.strict and not code_intelligence_enabled and is_full:
            gates.append(GateResult("module_code_intelligence_enabled", True, False, False, "runtime.modules.code_intelligence=false"))
            failed = True
        else:
            apply_command_gate(
                "code_knowledge_extract",
                code_intelligence_enabled,
                [
                    "python3",
                    "scripts/extract_code_knowledge_graph.py",
                    "--repo-root",
                    ".",
                    "--output",
                    "docs/assets/code-knowledge-index.json",
                    "--graph-output",
                    "docs/assets/code-dependency-graph.json",
                    "--report",
                    "reports/code_knowledge_report.json",
                ],
                fail_open=code_intel_fail_open,
            )
        apply_command_gate(
            "knowledge_extract",
            True,
            [
                "python3",
                "scripts/extract_knowledge_modules_from_docs.py",
                "--docs-dir",
                "docs",
                "--modules-dir",
                "knowledge_modules",
                "--report",
                "reports/knowledge_auto_extract_report.json",
            ],
        )
        apply_command_gate("knowledge_validate", True, ["python3", "scripts/validate_knowledge_modules.py"])
        apply_command_gate("stale_check", True, ["python3", "scripts/generate_kpi_wall.py", "--docs-dir", "docs", "--reports-dir", "reports", "--stale-days", "90"])
        apply_command_gate(
            "contradiction_check",
            True,
            ["python3", "scripts/detect_rag_contradictions.py", "--report", "reports/rag_contradictions_report.json"],
        )
        apply_command_gate(
            "retrieval_index_build_with_exclusion",
            True,
            [
                "python3",
                "scripts/generate_knowledge_retrieval_index.py",
                "--modules-dir",
                "knowledge_modules",
                "--output",
                "docs/assets/knowledge-retrieval-index.json",
                "--contradictions-report",
                "reports/rag_contradictions_report.json",
                "--exclude-critical-contradictions",
            ],
        )

        # Pilot includes RAG preparation, but premium toggles may still be off
        # depending on package/runtime profile.
        default_graph = True if is_full else False
        default_evals = True if is_full else False
        ontology_enabled = _module_enabled(runtime, "ontology_graph", default_graph)
        retrieval_eval_enabled = _module_enabled(runtime, "retrieval_evals", default_evals)

        if args.strict and not ontology_enabled:
            gates.append(GateResult("module_ontology_graph_enabled", True, False, False, "runtime.modules.ontology_graph=false"))
            failed = True
        else:
            apply_command_gate(
                "knowledge_graph_build",
                ontology_enabled,
                [
                    "python3",
                    "scripts/generate_knowledge_graph_jsonld.py",
                    "--modules-dir",
                    "knowledge_modules",
                    "--output",
                    "docs/assets/knowledge-graph.jsonld",
                    "--report",
                    "reports/knowledge_graph_report.json",
                ],
            )

        if args.strict and not retrieval_eval_enabled:
            gates.append(GateResult("module_retrieval_evals_enabled", True, False, False, "runtime.modules.retrieval_evals=false"))
            failed = True
        else:
            apply_command_gate("retrieval_eval_gate", retrieval_eval_enabled, ["python3", "scripts/run_retrieval_evals_gate.py"])

    # Full+RAG runtime guardrails gates
    if is_full_rag:
        apply_artifact_gate("ask_ai_runtime_retrieval", True, repo_root / "runtime/ask-ai-pack/app/retrieval.py")
        apply_artifact_gate("ask_ai_runtime_main", True, repo_root / "runtime/ask-ai-pack/app/main.py")

    # Artifacts presence checks
    if is_prep_tier:
        apply_artifact_gate("artifact_knowledge_extract_report", True, reports_dir / "knowledge_auto_extract_report.json")
        apply_artifact_gate("artifact_retrieval_index", True, repo_root / "docs/assets/knowledge-retrieval-index.json")
        apply_artifact_gate("artifact_contradictions_report", True, reports_dir / "rag_contradictions_report.json")
        if _module_enabled(runtime, "code_intelligence", True if is_full else False):
            if code_intel_fail_open:
                for gate_id, path in (
                    ("artifact_code_knowledge_index", repo_root / "docs/assets/code-knowledge-index.json"),
                    ("artifact_code_dependency_graph", repo_root / "docs/assets/code-dependency-graph.json"),
                    ("artifact_code_knowledge_report", reports_dir / "code_knowledge_report.json"),
                ):
                    ok = _artifact_exists(path)
                    gates.append(
                        GateResult(
                            gate_id,
                            True,
                            False,
                            True,
                            str(path) if ok else f"soft_missing:{path}",
                        )
                    )
            else:
                apply_artifact_gate("artifact_code_knowledge_index", True, repo_root / "docs/assets/code-knowledge-index.json")
                apply_artifact_gate("artifact_code_dependency_graph", True, repo_root / "docs/assets/code-dependency-graph.json")
                apply_artifact_gate("artifact_code_knowledge_report", True, reports_dir / "code_knowledge_report.json")

        if _module_enabled(runtime, "ontology_graph", True):
            apply_artifact_gate("artifact_knowledge_graph", True, repo_root / "docs/assets/knowledge-graph.jsonld")
        if _module_enabled(runtime, "retrieval_evals", True):
            apply_artifact_gate("artifact_retrieval_evals_report", True, reports_dir / "retrieval_evals_report.json")

    summary = {
        "ok": not failed,
        "tier": tier,
        "tier_source": tier_source,
        "runtime_config": str(runtime_path),
        "reports_dir": str(reports_dir),
        "check_only": bool(args.check_only),
        "strict": bool(args.strict),
        "gates": [
            {
                "id": g.gate_id,
                "required": g.required,
                "executed": g.executed,
                "ok": g.ok,
                "detail": g.detail,
            }
            for g in gates
        ],
    }
    _write_report(output_path, summary)

    print(f"[mandatory-gates] tier={tier} source={tier_source} ok={summary['ok']}")
    print(f"[mandatory-gates] report={output_path}")
    emit_event(
        repo_root=repo_root,
        event="mandatory_gates_finished",
        stage="mandatory_gates",
        status="passed" if summary["ok"] else "failed",
        payload={"tier": tier, "ok": bool(summary["ok"])},
    )
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

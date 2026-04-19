#!/usr/bin/env python3
"""Enforce unified RAG optimization layer for every generation/update flow."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _safe_load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (RuntimeError, ValueError, TypeError, OSError):  # noqa: BLE001
        return {}
    return payload if isinstance(payload, dict) else {}


def _resolve_script_path(repo_root: Path, script_name: str) -> Path:
    candidates = [
        repo_root / "scripts" / script_name,
        repo_root / "docsops" / "scripts" / script_name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[0].resolve()


def _run(cmd: list[str], cwd: Path) -> None:
    completed = subprocess.run(cmd, cwd=str(cwd), check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(
            f"Command failed rc={completed.returncode}: {' '.join(cmd)}\n"
            f"stdout={completed.stdout[-2000:]}\nstderr={completed.stderr[-2000:]}"
        )


def _run_allow_fail(cmd: list[str], cwd: Path) -> int:
    completed = subprocess.run(cmd, cwd=str(cwd), check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        output = "\n".join([completed.stdout or "", completed.stderr or ""]).strip()
        if output:
            print(output[-2000:], flush=True)
    return int(completed.returncode)


def _derive_profile(runtime: dict[str, Any]) -> str:
    llm_control = runtime.get("llm_control", {}) if isinstance(runtime.get("llm_control"), dict) else {}
    llm_mode = str(llm_control.get("llm_mode", "external_preferred")).strip().lower()
    strict_local = bool(llm_control.get("strict_local_first", llm_mode == "local_default"))
    if strict_local:
        return "strict-local"
    if llm_mode in {"local_default", "local_first"}:
        return "hybrid"
    return "cloud"


def _thresholds_from_runtime(runtime: dict[str, Any]) -> dict[str, float]:
    retrieval_eval = runtime.get("retrieval_eval", {}) if isinstance(runtime.get("retrieval_eval"), dict) else {}
    policy = runtime.get("retrieval_evals", {}) if isinstance(runtime.get("retrieval_evals"), dict) else {}
    return {
        "min_recall": float(retrieval_eval.get("min_recall", policy.get("min_recall", 0.50))),
        "max_hallucination_rate": float(
            retrieval_eval.get("max_hallucination_rate", policy.get("max_hallucination_rate", 0.20))
        ),
        "max_latency_p95_ms": float(retrieval_eval.get("max_latency_p95_ms", 2500)),
        "max_no_hit_rate": float(retrieval_eval.get("max_no_hit_rate", 0.35)),
    }


def _evaluate_alerts(
    *,
    rag_report: dict[str, Any],
    eval_report: dict[str, Any],
    metrics_snapshot: dict[str, Any],
    thresholds: dict[str, float],
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    recall = eval_report.get("metrics", {}).get("recall_at_k")
    hallucination = eval_report.get("metrics", {}).get("hallucination_rate")
    latency_p95 = metrics_snapshot.get("latency_p95_ms")
    no_hit_rate = metrics_snapshot.get("no_hit_rate")

    if isinstance(recall, (int, float)) and float(recall) < thresholds["min_recall"]:
        alerts.append({"code": "RAG_RECALL_LOW", "value": float(recall), "threshold": thresholds["min_recall"]})
    if isinstance(hallucination, (int, float)) and float(hallucination) > thresholds["max_hallucination_rate"]:
        alerts.append(
            {
                "code": "RAG_HALLUCINATION_HIGH",
                "value": float(hallucination),
                "threshold": thresholds["max_hallucination_rate"],
            }
        )
    if isinstance(latency_p95, (int, float)) and float(latency_p95) > thresholds["max_latency_p95_ms"]:
        alerts.append(
            {
                "code": "RAG_LATENCY_P95_HIGH",
                "value": float(latency_p95),
                "threshold": thresholds["max_latency_p95_ms"],
            }
        )
    if isinstance(no_hit_rate, (int, float)) and float(no_hit_rate) > thresholds["max_no_hit_rate"]:
        alerts.append(
            {
                "code": "RAG_NO_HIT_RATE_HIGH",
                "value": float(no_hit_rate),
                "threshold": thresholds["max_no_hit_rate"],
            }
        )
    if bool(rag_report.get("status")) and str(rag_report.get("status")) != "ok":
        alerts.append({"code": "RAG_LAYER_NOT_OK", "value": str(rag_report.get("status"))})
    return alerts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enforce RAG optimization layer")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--runtime-config", default="docsops/config/client_runtime.yml")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--provider", default="local", choices=["local", "openai"])
    parser.add_argument("--with-embeddings", action="store_true")
    parser.add_argument("--retention-versions", type=int, default=60)
    parser.add_argument("--promote-version", default="")
    parser.add_argument("--rollback-to-version", default="")
    parser.add_argument("--skip-rebuild", action="store_true")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    runtime_path = (repo_root / args.runtime_config).resolve()
    reports_dir = (repo_root / args.reports_dir).resolve()
    reports_dir.mkdir(parents=True, exist_ok=True)
    runtime = _read_yaml(runtime_path)

    rag_cmd = [
        sys.executable,
        str(_resolve_script_path(repo_root, "rag_reindex_lifecycle.py")),
        "--repo-root",
        str(repo_root),
        "--reports-dir",
        str(reports_dir),
        "--provider",
        str(args.provider),
        "--retention-versions",
        str(max(1, int(args.retention_versions))),
    ]
    if args.with_embeddings:
        rag_cmd.append("--with-embeddings")
    if args.skip_rebuild:
        rag_cmd.append("--skip-rebuild")
    if args.promote_version:
        rag_cmd.extend(["--promote-version", str(args.promote_version)])
    if args.rollback_to_version:
        rag_cmd.extend(["--rollback-to-version", str(args.rollback_to_version)])

    _run(rag_cmd, cwd=repo_root)

    eval_report_path = reports_dir / "retrieval_evals_report.json"
    if not eval_report_path.exists():
        eval_cmd = [
            sys.executable,
            str(_resolve_script_path(repo_root, "run_retrieval_evals.py")),
            "--index",
            "docs/assets/knowledge-retrieval-index.json",
            "--report",
            str(eval_report_path),
            "--dataset-out",
            str(reports_dir / "retrieval_eval_dataset.generated.yml"),
            "--auto-generate-dataset",
        ]
        eval_rc = _run_allow_fail(eval_cmd, cwd=repo_root)
        if eval_rc != 0:
            print(f"[rag-layer] retrieval eval command returned rc={eval_rc}; continuing with degraded status", flush=True)

    rag_report = _safe_load_json(reports_dir / "rag_reindex_report.json")
    eval_report = _safe_load_json(eval_report_path)
    telemetry_metrics = _safe_load_json(reports_dir / "rag_metrics_snapshot.json")
    query_metrics = telemetry_metrics.get("query_metrics", {}) if isinstance(telemetry_metrics.get("query_metrics"), dict) else {}
    thresholds = _thresholds_from_runtime(runtime)
    alerts = _evaluate_alerts(
        rag_report=rag_report,
        eval_report=eval_report,
        metrics_snapshot=query_metrics,
        thresholds=thresholds,
    )

    profile = _derive_profile(runtime)
    layer_report = {
        "status": "ok" if not alerts else "degraded",
        "strict": bool(args.strict),
        "profile": profile,
        "provider": args.provider,
        "with_embeddings": bool(args.with_embeddings),
        "thresholds": thresholds,
        "alerts": alerts,
        "rag_reindex_report_path": str(reports_dir / "rag_reindex_report.json"),
        "retrieval_evals_report_path": str(eval_report_path),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    out_path = reports_dir / "rag_optimization_layer_report.json"
    out_path.write_text(json.dumps(layer_report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    print(f"[rag-layer] status={layer_report['status']} profile={profile} alerts={len(alerts)}")
    if args.strict and alerts:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

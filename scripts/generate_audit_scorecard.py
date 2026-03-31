#!/usr/bin/env python3
"""Generate a sales-grade docs audit scorecard (JSON + HTML).

This report aggregates hard KPIs and adds a business-impact estimate layer.
It is intended for discovery/readout calls and pilot-to-full conversion.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import statistics
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# -- Pack runtime integration (optional) --------------------------------------
try:
    from scripts import pack_runtime as _pack_rt
    _pack = _pack_rt.get_pack()
except (RuntimeError, ValueError, TypeError, OSError, ImportError, ModuleNotFoundError):
    try:
        import pack_runtime as _pack_rt  # type: ignore[no-redef]
        _pack = _pack_rt.get_pack()
    except (RuntimeError, ValueError, TypeError, OSError, ImportError, ModuleNotFoundError):
        _pack_rt = None  # type: ignore[assignment]
        _pack = None

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}

# Explicit coverage map: only capabilities the pipeline can actually remediate.
CAPABILITY_MAP: dict[str, dict[str, Any]] = {
    "api_coverage_sync": {
        "label": "API coverage sync",
        "pipeline_modules": ["drift_detection", "docs_contract"],
        "related_flow": "api_first",
        "pilot": True,
        "full": True,
    },
    "example_execution_quality": {
        "label": "Executable examples quality",
        "pipeline_modules": ["self_checks", "snippet_lint", "normalization"],
        "related_flow": "docs_flow",
        "pilot": True,
        "full": True,
    },
    "freshness_lifecycle": {
        "label": "Freshness + lifecycle management",
        "pipeline_modules": ["kpi_sla", "release_pack"],
        "related_flow": "weekly",
        "pilot": True,
        "full": True,
    },
    "drift_contract_visibility": {
        "label": "Code/docs drift contract visibility",
        "pipeline_modules": ["drift_detection", "docs_contract"],
        "related_flow": "weekly",
        "pilot": True,
        "full": True,
    },
    "layer_completeness": {
        "label": "Doc layer completeness",
        "pipeline_modules": ["gap_detection", "fact_checks"],
        "related_flow": "docs_flow",
        "pilot": True,
        "full": True,
    },
    "terminology_governance": {
        "label": "Terminology governance",
        "pipeline_modules": ["terminology_management", "normalization"],
        "related_flow": "docs_flow",
        "pilot": True,
        "full": True,
    },
    "retrieval_quality_control": {
        "label": "RAG retrieval quality control",
        "pipeline_modules": ["rag_optimization", "ontology_graph", "retrieval_evals"],
        "related_flow": "knowledge",
        "pilot": True,
        "full": True,
    },
}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (yaml.YAMLError, ValueError, TypeError, OSError):  # noqa: BLE001
        return {}


def _safe_pct(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def _iter_docs(docs_dir: Path) -> list[Path]:
    if not docs_dir.exists():
        return []
    return sorted(p for p in docs_dir.rglob("*.md") if p.is_file())


def _extract_frontmatter(content: str) -> dict[str, Any]:
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        payload = yaml.safe_load(parts[1]) or {}
    except (yaml.YAMLError, ValueError, TypeError, OSError):  # noqa: BLE001
        return {}
    return payload if isinstance(payload, dict) else {}


def _parse_iso_date(raw: str) -> datetime | None:
    value = str(raw).strip()
    if not value:
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        value = value + "T00:00:00+00:00"
    value = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _freshness_metrics(docs_dir: Path, stale_days: int) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    ages_days: list[int] = []
    missing_dates = 0

    for path in _iter_docs(docs_dir):
        content = path.read_text(encoding="utf-8", errors="ignore")
        fm = _extract_frontmatter(content)
        raw_date = fm.get("last_reviewed") or fm.get("last_modified") or fm.get("date_created")
        dt = _parse_iso_date(str(raw_date)) if raw_date else None
        if dt is None:
            missing_dates += 1
            continue
        age = max(0, int((now - dt).total_seconds() // 86400))
        ages_days.append(age)

    total_docs = len(_iter_docs(docs_dir))
    dated_docs = len(ages_days)
    stale_docs = sum(1 for age in ages_days if age > stale_days)
    avg_age = round(sum(ages_days) / dated_docs, 2) if dated_docs else 0.0
    median_age = float(statistics.median(ages_days)) if dated_docs else 0.0

    return {
        "total_docs": total_docs,
        "dated_docs": dated_docs,
        "missing_date_docs": missing_dates,
        "average_age_days": avg_age,
        "median_age_days": round(median_age, 2),
        "stale_days_threshold": stale_days,
        "stale_docs_count": stale_docs,
        "stale_docs_pct": _safe_pct(stale_docs, dated_docs if dated_docs else total_docs),
    }


def _load_openapi(spec_path: Path) -> dict[str, Any]:
    if not spec_path.exists():
        return {}
    try:
        payload = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    except (RuntimeError, ValueError, TypeError, OSError):  # noqa: BLE001
        return {}
    return payload if isinstance(payload, dict) else {}


def _collect_operations(spec: dict[str, Any]) -> list[dict[str, str]]:
    ops: list[dict[str, str]] = []
    paths = spec.get("paths", {})
    if not isinstance(paths, dict):
        return ops
    for route, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            method_lower = str(method).lower()
            if method_lower not in HTTP_METHODS:
                continue
            op_id = ""
            if isinstance(operation, dict):
                op_id = str(operation.get("operationId", "")).strip()
            ops.append({"path": str(route), "method": method_lower, "operation_id": op_id})
    return ops


def _api_coverage_metrics(docs_dir: Path, spec_path: Path) -> dict[str, Any]:
    spec = _load_openapi(spec_path)
    operations = _collect_operations(spec)
    if not operations:
        return {
            "spec_found": spec_path.exists(),
            "spec_path": str(spec_path),
            "total_operations": 0,
            "documented_operations": 0,
            "undocumented_operations": 0,
            "undocumented_pct": 0.0,
            "coverage_pct": 0.0,
            "undocumented_samples": [],
        }

    docs_map: list[tuple[Path, str]] = []
    for md in _iter_docs(docs_dir):
        text = md.read_text(encoding="utf-8", errors="ignore").lower()
        docs_map.append((md, text))

    documented = 0
    undocumented_samples: list[str] = []
    for op in operations:
        op_id = op["operation_id"].strip().lower()
        route = op["path"].strip().lower()
        method = op["method"].strip().lower()

        found = False
        for _, text in docs_map:
            if op_id and op_id in text:
                found = True
                break
            if route and route in text and method in text:
                found = True
                break
        if found:
            documented += 1
        elif len(undocumented_samples) < 10:
            label = f"{method.upper()} {route}"
            if op_id:
                label = f"{label} ({op_id})"
            undocumented_samples.append(label)

    total = len(operations)
    undocumented = total - documented
    return {
        "spec_found": True,
        "spec_path": str(spec_path),
        "total_operations": total,
        "documented_operations": documented,
        "undocumented_operations": undocumented,
        "undocumented_pct": _safe_pct(undocumented, total),
        "coverage_pct": _safe_pct(documented, total),
        "undocumented_samples": undocumented_samples,
    }


def _examples_reliability_metrics(
    reports_dir: Path,
    docs_dir: Path,
    auto_run_smoke: bool,
) -> dict[str, Any]:
    smoke_report = reports_dir / "examples_smoke_report.json"
    payload = _read_json(smoke_report)
    if not payload and auto_run_smoke:
        cmd = [
            "python3",
            "scripts/check_code_examples_smoke.py",
            "--paths",
            str(docs_dir),
            "--report",
            str(smoke_report),
        ]
        subprocess.run(cmd, check=False)
        payload = _read_json(smoke_report)

    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    total = int(summary.get("smoke_blocks_executed", 0) or 0)
    failed = int(summary.get("smoke_blocks_failed", 0) or 0)
    reliability_pct = float(summary.get("example_reliability_pct", 0.0) or 0.0)
    if total == 0 and payload:
        total = int(summary.get("smoke_blocks_total", 0) or 0)
        if total > 0:
            reliability_pct = _safe_pct(total - failed, total)

    return {
        "report_found": bool(payload),
        "report_path": str(smoke_report),
        "executed_examples": total,
        "failed_examples": failed,
        "example_reliability_pct": round(reliability_pct, 2),
    }


def _drift_metrics(reports_dir: Path) -> dict[str, Any]:
    docs_contract = _read_json(reports_dir / "pr_docs_contract.json")
    api_drift = _read_json(reports_dir / "api_sdk_drift_report.json")

    interface_changed = docs_contract.get("interface_changed", [])
    mismatch_count = 0
    if isinstance(docs_contract.get("mismatches"), list):
        mismatch_count = len(docs_contract.get("mismatches", []))
    elif isinstance(interface_changed, list):
        docs_changed = docs_contract.get("docs_changed", [])
        mismatch_count = len(interface_changed) if not docs_changed else 0

    interface_count = len(interface_changed) if isinstance(interface_changed, list) else 0
    drift_pct = _safe_pct(mismatch_count, interface_count) if interface_count else 0.0
    api_drift_status = str(api_drift.get("status", "unknown")) if api_drift else "missing"

    return {
        "docs_contract_report_found": bool(docs_contract),
        "api_drift_report_found": bool(api_drift),
        "interface_changed_count": interface_count,
        "docs_contract_mismatch_count": mismatch_count,
        "docs_contract_drift_pct": drift_pct,
        "api_drift_status": api_drift_status,
    }


def _infer_feature_key(path: Path, fm: dict[str, Any], content_type: str) -> str:
    for key in ("feature_id", "feature", "component", "capability", "topic", "api_group"):
        value = fm.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    title = str(fm.get("title", "")).strip().lower()
    if title:
        norm = re.sub(r"[^a-z0-9]+", "-", title).strip("-")
        if norm:
            for suffix in ("-concept", "-how-to", "-reference", "-tutorial", "-troubleshooting"):
                if norm.endswith(suffix):
                    norm = norm[: -len(suffix)]
                    break
            return norm
    stem = path.stem.lower()
    for suffix in ("-concept", "-how-to", "-reference", "-tutorial", "-troubleshooting"):
        if stem.endswith(suffix):
            return stem[: -len(suffix)]
    return stem or content_type


def _layer_completeness_metrics(docs_dir: Path, policy_pack: Path | None) -> dict[str, Any]:
    required_layers = ["concept", "how-to", "reference"]
    if policy_pack and policy_pack.exists():
        try:
            payload = yaml.safe_load(policy_pack.read_text(encoding="utf-8")) or {}
            section = payload.get("doc_layers", {}) if isinstance(payload, dict) else {}
            from_pack = section.get("required_layers") if isinstance(section, dict) else None
            if isinstance(from_pack, list) and from_pack:
                required_layers = [str(v).strip().lower() for v in from_pack if str(v).strip()]
        except (RuntimeError, ValueError, TypeError, OSError):  # noqa: BLE001
            logger.warning("Failed reading required_layers from policy pack: %s", policy_pack)

    features: dict[str, set[str]] = {}
    for md in _iter_docs(docs_dir):
        content = md.read_text(encoding="utf-8", errors="ignore")
        fm = _extract_frontmatter(content)
        content_type = str(fm.get("content_type", "")).strip().lower()
        if not content_type:
            continue
        feature_key = _infer_feature_key(md, fm, content_type)
        features.setdefault(feature_key, set()).add(content_type)

    if not features:
        return {
            "required_layers": required_layers,
            "total_features": 0,
            "features_missing_required_layers": 0,
            "features_missing_required_layers_pct": 0.0,
            "sample_missing_features": [],
        }

    missing = 0
    sample_missing: list[dict[str, Any]] = []
    required = set(required_layers)
    for feature, seen in sorted(features.items()):
        absent = sorted(required - seen)
        if not absent:
            continue
        missing += 1
        if len(sample_missing) < 10:
            sample_missing.append({"feature": feature, "missing_layers": absent, "present_layers": sorted(seen)})

    return {
        "required_layers": required_layers,
        "total_features": len(features),
        "features_missing_required_layers": missing,
        "features_missing_required_layers_pct": _safe_pct(missing, len(features)),
        "sample_missing_features": sample_missing,
    }


def _retrieval_metrics(reports_dir: Path) -> dict[str, Any]:
    payload = _read_json(reports_dir / "retrieval_evals_report.json")
    metrics = payload.get("metrics", {}) if isinstance(payload.get("metrics"), dict) else {}
    return {
        "report_found": bool(payload),
        "status": str(payload.get("status", "missing")) if payload else "missing",
        "precision_at_k": float(metrics.get("precision_at_k", 0.0) or 0.0),
        "recall_at_k": float(metrics.get("recall_at_k", 0.0) or 0.0),
        "hallucination_rate": float(metrics.get("hallucination_rate", 0.0) or 0.0),
        "top_k": int(metrics.get("top_k", 0) or 0),
    }


def _terminology_metrics(docs_dir: Path, glossary_path: Path, reports_dir: Path) -> dict[str, Any]:
    glossary = {}
    if glossary_path.exists():
        try:
            payload = yaml.safe_load(glossary_path.read_text(encoding="utf-8")) or {}
            glossary = payload if isinstance(payload, dict) else {}
        except (RuntimeError, ValueError, TypeError, OSError):  # noqa: BLE001
            glossary = {}

    forbidden = glossary.get("forbidden", []) if isinstance(glossary.get("forbidden"), list) else []
    terms = glossary.get("terms", {}) if isinstance(glossary.get("terms"), dict) else {}
    normalized_forbidden = [str(v).strip() for v in forbidden if str(v).strip()]

    total_docs = 0
    docs_with_violations = 0
    total_occurrences = 0
    offenders: list[dict[str, Any]] = []
    patterns = [(term, re.compile(rf"\b{re.escape(term.lower())}\b")) for term in normalized_forbidden]

    for md in _iter_docs(docs_dir):
        total_docs += 1
        text = md.read_text(encoding="utf-8", errors="ignore").lower()
        doc_occurrences = 0
        found_terms: list[str] = []
        for term, pattern in patterns:
            count = len(pattern.findall(text))
            if count > 0:
                doc_occurrences += count
                found_terms.append(term)
        if doc_occurrences > 0:
            docs_with_violations += 1
            total_occurrences += doc_occurrences
            if len(offenders) < 10:
                offenders.append(
                    {
                        "file": str(md),
                        "forbidden_terms": sorted(found_terms),
                        "occurrences": doc_occurrences,
                    }
                )

    glossary_sync = _read_json(reports_dir / "glossary_sync_report.json")
    return {
        "glossary_path": str(glossary_path),
        "forbidden_terms_count": len(normalized_forbidden),
        "glossary_terms_count": len(terms),
        "docs_scanned": total_docs,
        "docs_with_forbidden_terms": docs_with_violations,
        "forbidden_term_occurrences": total_occurrences,
        "terminology_violation_pct": _safe_pct(docs_with_violations, total_docs),
        "terminology_consistency_pct": round(100.0 - _safe_pct(docs_with_violations, total_docs), 2),
        "offender_samples": offenders,
        "glossary_sync_report_found": bool(glossary_sync),
    }


@dataclass
class CostAssumptions:
    engineer_hourly_usd: float = 95.0
    support_hourly_usd: float = 45.0
    release_count_per_month: float = 4.0
    baseline_manual_sync_hours_per_week: float = 8.0
    avg_release_delay_hours: float = 3.0
    monthly_support_tickets: float = 300.0
    docs_related_ticket_share: float = 0.25
    avg_ticket_handling_minutes: float = 18.0


def _load_assumptions(path: Path | None) -> CostAssumptions:
    defaults = CostAssumptions()
    if path is None or not path.exists():
        return defaults
    payload = _read_json(path)
    if not payload:
        return defaults
    return CostAssumptions(
        engineer_hourly_usd=float(payload.get("engineer_hourly_usd", defaults.engineer_hourly_usd)),
        support_hourly_usd=float(payload.get("support_hourly_usd", defaults.support_hourly_usd)),
        release_count_per_month=float(payload.get("release_count_per_month", defaults.release_count_per_month)),
        baseline_manual_sync_hours_per_week=float(
            payload.get("baseline_manual_sync_hours_per_week", defaults.baseline_manual_sync_hours_per_week)
        ),
        avg_release_delay_hours=float(payload.get("avg_release_delay_hours", defaults.avg_release_delay_hours)),
        monthly_support_tickets=float(payload.get("monthly_support_tickets", defaults.monthly_support_tickets)),
        docs_related_ticket_share=float(payload.get("docs_related_ticket_share", defaults.docs_related_ticket_share)),
        avg_ticket_handling_minutes=float(payload.get("avg_ticket_handling_minutes", defaults.avg_ticket_handling_minutes)),
    )


def _business_impact(kpis: dict[str, Any], assumptions: CostAssumptions) -> dict[str, Any]:
    undocumented_pct = float(kpis["api_coverage"]["undocumented_pct"])
    stale_pct = float(kpis["freshness"]["stale_docs_pct"])
    drift_pct = float(kpis["drift"]["docs_contract_drift_pct"])
    example_reliability = float(kpis["example_reliability"]["example_reliability_pct"])
    terminology_violation_pct = float(kpis["terminology"]["terminology_violation_pct"])

    rw = _pack_rt.get_risk_weights(_pack) if _pack_rt is not None else None
    if rw is None:
        w_undoc, w_stale, w_drift, w_ex, w_term = 0.30, 0.20, 0.20, 0.20, 0.10
    else:
        w_undoc = rw.get("undocumented", 0.30)
        w_stale = rw.get("stale", 0.20)
        w_drift = rw.get("drift", 0.20)
        w_ex = rw.get("example_gap", 0.20)
        w_term = rw.get("terminology", 0.10)

    risk_index = (
        w_undoc * (undocumented_pct / 100.0)
        + w_stale * (stale_pct / 100.0)
        + w_drift * (drift_pct / 100.0)
        + w_ex * ((100.0 - example_reliability) / 100.0)
        + w_term * (terminology_violation_pct / 100.0)
    )
    risk_index = min(max(risk_index, 0.0), 1.0)

    engineering_hours = (
        assumptions.baseline_manual_sync_hours_per_week * 4.3
        + assumptions.release_count_per_month * assumptions.avg_release_delay_hours * risk_index
        + (undocumented_pct / 100.0) * 10.0
        + ((100.0 - example_reliability) / 100.0) * 12.0
    )
    support_hours = (
        assumptions.monthly_support_tickets
        * assumptions.docs_related_ticket_share
        * (assumptions.avg_ticket_handling_minutes / 60.0)
        * (0.5 + risk_index)
    )
    release_delay_hours = assumptions.release_count_per_month * assumptions.avg_release_delay_hours * risk_index

    base_cost = engineering_hours * assumptions.engineer_hourly_usd + support_hours * assumptions.support_hourly_usd

    def _scenario(multiplier: float) -> dict[str, float]:
        return {
            "monthly_cost_usd": round(base_cost * multiplier, 2),
            "engineering_hours": round(engineering_hours * multiplier, 2),
            "support_hours": round(support_hours * multiplier, 2),
            "release_delay_hours": round(release_delay_hours * multiplier, 2),
        }

    return {
        "risk_index_0_to_1": round(risk_index, 3),
        "engineering_support_hours_lost_estimate": _scenario(1.0),
        "scenarios": {
            "conservative": _scenario(0.7),
            "base": _scenario(1.0),
            "aggressive": _scenario(1.4),
        },
        "assumptions": assumptions.__dict__,
    }


def _overall_score(kpis: dict[str, Any]) -> dict[str, Any]:
    api_cov = float(kpis["api_coverage"]["coverage_pct"])
    ex_rel = float(kpis["example_reliability"]["example_reliability_pct"])
    stale_penalty = float(kpis["freshness"]["stale_docs_pct"])
    drift_penalty = float(kpis["drift"]["docs_contract_drift_pct"])
    layers_penalty = float(kpis["layer_completeness"]["features_missing_required_layers_pct"])
    term_consistency = float(kpis["terminology"]["terminology_consistency_pct"])
    retrieval = kpis["retrieval_quality"]
    retrieval_score = (
        (float(retrieval["precision_at_k"]) * 100.0 + float(retrieval["recall_at_k"]) * 100.0) / 2.0
        if retrieval["report_found"]
        else 50.0
    )
    hallucination_penalty = float(retrieval["hallucination_rate"]) * 100.0 if retrieval["report_found"] else 10.0

    aw = _pack_rt.get_audit_weights(_pack) if _pack_rt is not None else None
    if aw is None:
        w_api, w_ex, w_fresh, w_drift, w_layers = 0.22, 0.20, 0.14, 0.12, 0.12
        w_term, w_retr, w_halluc = 0.10, 0.10, 0.08
    else:
        w_api = aw.get("api_coverage", 0.22)
        w_ex = aw.get("example_reliability", 0.20)
        w_fresh = aw.get("freshness", 0.14)
        w_drift = aw.get("drift", 0.12)
        w_layers = aw.get("layers", 0.12)
        w_term = aw.get("terminology", 0.10)
        w_retr = aw.get("retrieval", 0.10)
        w_halluc = aw.get("hallucination_deduction", 0.08)

    score = (
        w_api * api_cov
        + w_ex * ex_rel
        + w_fresh * (100.0 - stale_penalty)
        + w_drift * (100.0 - drift_penalty)
        + w_layers * (100.0 - layers_penalty)
        + w_term * term_consistency
        + w_retr * retrieval_score
    ) - (w_halluc * hallucination_penalty)
    score = round(max(0.0, min(100.0, score)), 2)

    gt = _pack_rt.get_grade_thresholds(_pack) if _pack_rt is not None else None
    if gt is None:
        gt = {"A": 90, "B": 80, "C": 70, "D": 60}

    grade = "A"
    if score < gt.get("A", 90):
        grade = "B"
    if score < gt.get("B", 80):
        grade = "C"
    if score < gt.get("C", 70):
        grade = "D"
    if score < gt.get("D", 60):
        grade = "F"
    return {"audit_score_0_100": score, "grade": grade}


def _severity_from_gap(pct: float, high: float, medium: float) -> str:
    if pct >= high:
        return "high"
    if pct >= medium:
        return "medium"
    return "low"


def _pilot_full_fixability(capability_id: str) -> dict[str, Any]:
    capability = CAPABILITY_MAP.get(capability_id, {})
    return {
        "pilot": bool(capability.get("pilot", False)),
        "full": bool(capability.get("full", False)),
    }


def _build_findings(kpis: dict[str, Any], assumptions: CostAssumptions) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    def add(
        finding_id: str,
        title: str,
        capability_id: str,
        metric: str,
        current: float,
        target: float,
        unit: str,
        effort_hours: tuple[float, float],
        monthly_loss_factor: float,
        note: str,
        evidence: str,
        confidence: str,
    ) -> None:
        capability = CAPABILITY_MAP.get(capability_id, {})
        module_names = list(capability.get("pipeline_modules", []))
        if not module_names:
            return
        gap_value = max(0.0, current - target) if unit != "%" or current >= target else max(0.0, target - current)
        severity = _severity_from_gap(gap_value, high=25.0, medium=10.0)
        effort_low, effort_high = effort_hours
        effort_base = (effort_low + effort_high) / 2.0
        remediation_cost_low = round(effort_low * assumptions.engineer_hourly_usd, 2)
        remediation_cost_high = round(effort_high * assumptions.engineer_hourly_usd, 2)
        remediation_cost_base = round(effort_base * assumptions.engineer_hourly_usd, 2)
        monthly_loss_low = round(remediation_cost_low * monthly_loss_factor, 2)
        monthly_loss_base = round(remediation_cost_base * monthly_loss_factor * 1.2, 2)
        monthly_loss_high = round(remediation_cost_high * monthly_loss_factor * 1.6, 2)
        findings.append(
            {
                "id": finding_id,
                "title": title,
                "capability_id": capability_id,
                "capability_label": str(capability.get("label", capability_id)),
                "pipeline_related_flow": str(capability.get("related_flow", "")),
                "metric": metric,
                "current_value": round(current, 2),
                "target_value": round(target, 2),
                "unit": unit,
                "gap_value": round(gap_value, 2),
                "severity": severity,
                "pipeline_modules": module_names,
                "fixability": _pilot_full_fixability(capability_id),
                "effort_hours_low": round(effort_low, 1),
                "effort_hours_base": round(effort_base, 1),
                "effort_hours_high": round(effort_high, 1),
                "estimated_remediation_cost_usd_low": remediation_cost_low,
                "estimated_remediation_cost_usd_base": remediation_cost_base,
                "estimated_remediation_cost_usd_high": remediation_cost_high,
                "estimated_monthly_loss_usd_low": monthly_loss_low,
                "estimated_monthly_loss_usd_base": monthly_loss_base,
                "estimated_monthly_loss_usd_high": monthly_loss_high,
                "recommended_window_days": 7 if severity == "high" else 14 if severity == "medium" else 30,
                "evidence_source": evidence,
                "estimation_confidence": confidence,
                "note": note,
            }
        )

    api = kpis["api_coverage"]
    add(
        "F-API-COVERAGE",
        "Undocumented API operations",
        "api_coverage_sync",
        "API undocumented %",
        float(api["undocumented_pct"]),
        5.0,
        "%",
        (4.0, 16.0),
        2.2,
        "Generate/update reference + how-to from OpenAPI and enforce drift checks.",
        "OpenAPI + docs text scan",
        "high",
    )

    examples = kpis["example_reliability"]
    add(
        "F-EXAMPLES-RELIABILITY",
        "Code examples fail or are non-runnable",
        "example_execution_quality",
        "Example reliability %",
        max(0.0, 100.0 - float(examples["example_reliability_pct"])),
        5.0,
        "% shortfall",
        (3.0, 14.0),
        2.0,
        "Run smoke + expected-output checks and auto-fix broken snippets.",
        "examples_smoke_report.json",
        "high" if bool(examples.get("report_found")) else "medium",
    )

    fresh = kpis["freshness"]
    add(
        "F-FRESHNESS",
        "Documentation freshness debt",
        "freshness_lifecycle",
        "Stale docs %",
        float(fresh["stale_docs_pct"]),
        10.0,
        "%",
        (2.0, 8.0),
        1.7,
        "Prioritize stale pages via weekly SLA loop and lifecycle policies.",
        "frontmatter date scan",
        "high" if int(fresh.get("dated_docs", 0)) > 0 else "medium",
    )

    drift = kpis["drift"]
    add(
        "F-DRIFT",
        "Code/docs contract drift",
        "drift_contract_visibility",
        "Drift %",
        float(drift["docs_contract_drift_pct"]),
        2.0,
        "%",
        (2.0, 10.0),
        2.4,
        "Track interface changes and enforce docs updates with report-first governance.",
        "pr_docs_contract.json + api_sdk_drift_report.json",
        "high" if bool(drift.get("docs_contract_report_found")) else "low",
    )

    layers = kpis["layer_completeness"]
    add(
        "F-LAYERS",
        "Missing required doc layers",
        "layer_completeness",
        "Features missing required layers %",
        float(layers["features_missing_required_layers_pct"]),
        5.0,
        "%",
        (3.0, 12.0),
        1.8,
        "Backfill concept/how-to/reference coverage for key capabilities.",
        "policy pack + frontmatter layer scan",
        "high",
    )

    terms = kpis["terminology"]
    add(
        "F-TERMINOLOGY",
        "Terminology inconsistency",
        "terminology_governance",
        "Terminology violations %",
        float(terms["terminology_violation_pct"]),
        3.0,
        "%",
        (1.0, 6.0),
        1.5,
        "Enforce preferred terms and sync glossary markers continuously.",
        "glossary.yml forbidden terms scan",
        "high" if int(terms.get("forbidden_terms_count", 0)) > 0 else "low",
    )

    retrieval = kpis["retrieval_quality"]
    if retrieval["report_found"]:
        add(
            "F-RETRIEVAL",
            "RAG retrieval quality risk",
            "retrieval_quality_control",
            "Hallucination rate %",
            float(retrieval["hallucination_rate"]) * 100.0,
            10.0,
            "%",
            (4.0, 14.0),
            1.9,
            "Improve module metadata, index quality, and retrieval eval thresholds.",
            "retrieval_evals_report.json",
            "high",
        )
    else:
        findings.append(
            {
                "id": "F-RETRIEVAL-MISSING",
                "title": "Retrieval quality is not measured yet",
                "capability_id": "retrieval_quality_control",
                "capability_label": CAPABILITY_MAP["retrieval_quality_control"]["label"],
                "pipeline_related_flow": CAPABILITY_MAP["retrieval_quality_control"]["related_flow"],
                "metric": "Retrieval eval report availability",
                "current_value": 0,
                "target_value": 1,
                "unit": "binary",
                "gap_value": 1,
                "severity": "medium",
                "pipeline_modules": CAPABILITY_MAP["retrieval_quality_control"]["pipeline_modules"],
                "fixability": _pilot_full_fixability("retrieval_quality_control"),
                "effort_hours_low": 2.0,
                "effort_hours_base": 4.0,
                "effort_hours_high": 6.0,
                "estimated_remediation_cost_usd_low": round(2.0 * assumptions.engineer_hourly_usd, 2),
                "estimated_remediation_cost_usd_base": round(4.0 * assumptions.engineer_hourly_usd, 2),
                "estimated_remediation_cost_usd_high": round(6.0 * assumptions.engineer_hourly_usd, 2),
                "estimated_monthly_loss_usd_low": round(2.0 * assumptions.engineer_hourly_usd * 1.4, 2),
                "estimated_monthly_loss_usd_base": round(4.0 * assumptions.engineer_hourly_usd * 1.7, 2),
                "estimated_monthly_loss_usd_high": round(6.0 * assumptions.engineer_hourly_usd * 2.1, 2),
                "recommended_window_days": 14,
                "evidence_source": "retrieval_evals_report.json (missing)",
                "estimation_confidence": "medium",
                "note": "Enable retrieval index + evals to quantify AI answer quality.",
            }
        )

    if not bool(examples.get("report_found")):
        findings.append(
            {
                "id": "F-EVIDENCE-SMOKE-MISSING",
                "title": "Executable example evidence is missing",
                "capability_id": "example_execution_quality",
                "capability_label": CAPABILITY_MAP["example_execution_quality"]["label"],
                "pipeline_related_flow": CAPABILITY_MAP["example_execution_quality"]["related_flow"],
                "metric": "Smoke report availability",
                "current_value": 0,
                "target_value": 1,
                "unit": "binary",
                "gap_value": 1,
                "severity": "medium",
                "pipeline_modules": CAPABILITY_MAP["example_execution_quality"]["pipeline_modules"],
                "fixability": _pilot_full_fixability("example_execution_quality"),
                "effort_hours_low": 0.5,
                "effort_hours_base": 1.0,
                "effort_hours_high": 1.5,
                "estimated_remediation_cost_usd_low": round(0.5 * assumptions.engineer_hourly_usd, 2),
                "estimated_remediation_cost_usd_base": round(1.0 * assumptions.engineer_hourly_usd, 2),
                "estimated_remediation_cost_usd_high": round(1.5 * assumptions.engineer_hourly_usd, 2),
                "estimated_monthly_loss_usd_low": round(0.5 * assumptions.engineer_hourly_usd * 0.8, 2),
                "estimated_monthly_loss_usd_base": round(1.0 * assumptions.engineer_hourly_usd * 1.0, 2),
                "estimated_monthly_loss_usd_high": round(1.5 * assumptions.engineer_hourly_usd * 1.2, 2),
                "recommended_window_days": 7,
                "evidence_source": "examples_smoke_report.json (missing)",
                "estimation_confidence": "medium",
                "note": "Run smoke checks in weekly/finalize gates to replace assumptions with measured pass/fail evidence.",
            }
        )

    if not bool(drift.get("docs_contract_report_found")):
        findings.append(
            {
                "id": "F-EVIDENCE-DRIFT-MISSING",
                "title": "Drift evidence report is missing",
                "capability_id": "drift_contract_visibility",
                "capability_label": CAPABILITY_MAP["drift_contract_visibility"]["label"],
                "pipeline_related_flow": CAPABILITY_MAP["drift_contract_visibility"]["related_flow"],
                "metric": "Docs-contract report availability",
                "current_value": 0,
                "target_value": 1,
                "unit": "binary",
                "gap_value": 1,
                "severity": "medium",
                "pipeline_modules": CAPABILITY_MAP["drift_contract_visibility"]["pipeline_modules"],
                "fixability": _pilot_full_fixability("drift_contract_visibility"),
                "effort_hours_low": 0.5,
                "effort_hours_base": 1.0,
                "effort_hours_high": 2.0,
                "estimated_remediation_cost_usd_low": round(0.5 * assumptions.engineer_hourly_usd, 2),
                "estimated_remediation_cost_usd_base": round(1.0 * assumptions.engineer_hourly_usd, 2),
                "estimated_remediation_cost_usd_high": round(2.0 * assumptions.engineer_hourly_usd, 2),
                "estimated_monthly_loss_usd_low": round(0.5 * assumptions.engineer_hourly_usd * 0.9, 2),
                "estimated_monthly_loss_usd_base": round(1.0 * assumptions.engineer_hourly_usd * 1.1, 2),
                "estimated_monthly_loss_usd_high": round(2.0 * assumptions.engineer_hourly_usd * 1.4, 2),
                "recommended_window_days": 7,
                "evidence_source": "pr_docs_contract.json (missing)",
                "estimation_confidence": "medium",
                "note": "Enable weekly docs-contract report so drift is measured from git diffs, not assumptions.",
            }
        )

    findings.sort(key=lambda item: {"high": 0, "medium": 1, "low": 2}.get(str(item["severity"]), 3))
    return findings


def _findings_totals(findings: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "findings_count": len(findings),
        "high_count": sum(1 for f in findings if f.get("severity") == "high"),
        "medium_count": sum(1 for f in findings if f.get("severity") == "medium"),
        "low_count": sum(1 for f in findings if f.get("severity") == "low"),
        "pilot_fixable_count": sum(1 for f in findings if bool(f.get("fixability", {}).get("pilot"))),
        "full_fixable_count": sum(1 for f in findings if bool(f.get("fixability", {}).get("full"))),
        "remediation_cost_usd_low_total": round(sum(float(f.get("estimated_remediation_cost_usd_low", 0.0)) for f in findings), 2),
        "remediation_cost_usd_base_total": round(sum(float(f.get("estimated_remediation_cost_usd_base", 0.0)) for f in findings), 2),
        "remediation_cost_usd_high_total": round(sum(float(f.get("estimated_remediation_cost_usd_high", 0.0)) for f in findings), 2),
        "monthly_loss_usd_low_total": round(sum(float(f.get("estimated_monthly_loss_usd_low", 0.0)) for f in findings), 2),
        "monthly_loss_usd_base_total": round(sum(float(f.get("estimated_monthly_loss_usd_base", 0.0)) for f in findings), 2),
        "monthly_loss_usd_high_total": round(sum(float(f.get("estimated_monthly_loss_usd_high", 0.0)) for f in findings), 2),
    }


def _top3_gaps(reports_dir: Path) -> list[dict[str, Any]]:
    payload = _read_json(reports_dir / "doc_gaps_report.json")
    gaps = payload.get("gaps", []) if isinstance(payload.get("gaps"), list) else []
    scored: list[tuple[float, dict[str, Any]]] = []
    for gap in gaps:
        if not isinstance(gap, dict):
            continue
        priority = str(gap.get("priority", "medium")).lower()
        weight = {"high": 3.0, "medium": 2.0, "low": 1.0}.get(priority, 1.5)
        frequency = float(gap.get("frequency", 1.0) or 1.0)
        score = weight * math.log10(max(1.0, frequency) + 1.0)
        scored.append((score, gap))
    scored.sort(key=lambda x: x[0], reverse=True)
    result: list[dict[str, Any]] = []
    for _, gap in scored[:3]:
        result.append(
            {
                "id": gap.get("id"),
                "title": gap.get("title"),
                "priority": gap.get("priority"),
                "action_required": gap.get("action_required"),
                "related_files": gap.get("related_files", []),
            }
        )
    return result


def _capability_matrix() -> list[dict[str, Any]]:
    matrix: list[dict[str, Any]] = []
    for capability_id, payload in sorted(CAPABILITY_MAP.items()):
        matrix.append(
            {
                "capability_id": capability_id,
                "capability_label": payload.get("label"),
                "pipeline_modules": payload.get("pipeline_modules", []),
                "related_flow": payload.get("related_flow"),
                "pilot": bool(payload.get("pilot", False)),
                "full": bool(payload.get("full", False)),
            }
        )
    return matrix


def _build_html(payload: dict[str, Any]) -> str:
    score = payload["score"]["audit_score_0_100"]
    grade = payload["score"]["grade"]
    k = payload["kpis"]
    impact = payload["business_impact"]["scenarios"]["base"]
    findings = payload.get("findings", [])
    findings_totals = payload.get("findings_totals", {})
    top3 = payload["top_3_gaps"]

    def card(title: str, value: str, subtitle: str) -> str:
        return (
            "<div class='card'>"
            f"<h3>{title}</h3>"
            f"<div class='value'>{value}</div>"
            f"<p>{subtitle}</p>"
            "</div>"
        )

    top3_html = "".join(
        "<li><strong>{}</strong> ({})<br><span>{}</span></li>".format(
            str(item.get("title", "")),
            str(item.get("priority", "")),
            str(item.get("action_required", "")),
        )
        for item in top3
    ) or "<li>No gaps detected.</li>"

    findings_rows = "".join(
        (
            "<tr>"
            f"<td>{html.escape(str(item.get('id', '')))}</td>"
            f"<td>{html.escape(str(item.get('title', '')))}</td>"
            f"<td>{html.escape(str(item.get('severity', '')))}</td>"
            f"<td>{html.escape(str(item.get('capability_label', '')))}</td>"
            f"<td>{html.escape(str(item.get('metric', '')))}: {item.get('current_value')} -> {item.get('target_value')} {html.escape(str(item.get('unit', '')))}</td>"
            f"<td>{'Yes' if item.get('fixability', {}).get('pilot') else 'No'} / {'Yes' if item.get('fixability', {}).get('full') else 'No'}</td>"
            f"<td>{item.get('effort_hours_low')} / {item.get('effort_hours_base')} / {item.get('effort_hours_high')}h</td>"
            f"<td>${item.get('estimated_remediation_cost_usd_low')} / ${item.get('estimated_remediation_cost_usd_base')} / ${item.get('estimated_remediation_cost_usd_high')}</td>"
            f"<td>${item.get('estimated_monthly_loss_usd_low')} / ${item.get('estimated_monthly_loss_usd_base')} / ${item.get('estimated_monthly_loss_usd_high')}</td>"
            f"<td>{html.escape(str(item.get('estimation_confidence', '')))}</td>"
            "</tr>"
        )
        for item in findings
    ) or "<tr><td colspan='10'>No findings generated.</td></tr>"

    capability_rows = "".join(
        (
            "<tr>"
            f"<td>{html.escape(str(item.get('capability_id', '')))}</td>"
            f"<td>{html.escape(str(item.get('capability_label', '')))}</td>"
            f"<td>{html.escape(', '.join(str(v) for v in item.get('pipeline_modules', [])))}</td>"
            f"<td>{html.escape(str(item.get('related_flow', '')))}</td>"
            f"<td>{'Yes' if item.get('pilot') else 'No'} / {'Yes' if item.get('full') else 'No'}</td>"
            "</tr>"
        )
        for item in payload.get("capability_matrix", [])
    ) or "<tr><td colspan='5'>Capability map is empty.</td></tr>"

    generated_at = str(payload.get("generated_at", ""))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VeriOps Audit Scorecard</title>
<style>
  :root {{
    --bg:#f7fafc;
    --text:#1f2937;
    --muted:#6b7280;
    --surface:#ffffff;
    --accent:#0f766e;
    --accent-2:#1d4ed8;
    --warn:#b45309;
    --border:#e5e7eb;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: "Segoe UI", Arial, sans-serif; background: linear-gradient(135deg,#ecfeff,#eef2ff 60%,#f8fafc); color: var(--text); }}
  .wrap {{ max-width: 1100px; margin: 0 auto; padding: 28px 18px 40px; }}
  .hero {{ background: var(--surface); border:1px solid var(--border); border-radius:16px; padding:22px; box-shadow: 0 8px 24px rgba(15,23,42,.06); }}
  h1 {{ margin:0 0 6px; font-size: 30px; }}
  .sub {{ color: var(--muted); margin:0; }}
  .score {{ margin-top:14px; display:flex; gap:16px; align-items: baseline; }}
  .score .big {{ font-size: 44px; font-weight: 800; color: var(--accent); }}
  .score .grade {{ font-size: 22px; font-weight: 700; color: var(--accent-2); }}
  .grid {{ margin-top: 18px; display:grid; grid-template-columns: repeat(auto-fit,minmax(220px,1fr)); gap:12px; }}
  .card {{ background: var(--surface); border:1px solid var(--border); border-radius:12px; padding:14px; }}
  .card h3 {{ margin:0; font-size:14px; color:var(--muted); font-weight:600; }}
  .card .value {{ margin-top:8px; font-size:28px; font-weight:700; }}
  .card p {{ margin:6px 0 0; font-size:13px; color:var(--muted); }}
  .section {{ margin-top: 18px; background: var(--surface); border:1px solid var(--border); border-radius:12px; padding:16px; }}
  .section h2 {{ margin:0 0 10px; font-size:20px; }}
  .kpi-table {{ width:100%; border-collapse: collapse; font-size:14px; }}
  .kpi-table th,.kpi-table td {{ border-bottom:1px solid var(--border); text-align:left; padding:9px 8px; }}
  .kpi-table th {{ color:var(--muted); font-weight:600; }}
  .top3 li {{ margin-bottom: 10px; }}
  .top3 span {{ color:var(--muted); font-size:13px; }}
  .foot {{ margin-top:14px; color:var(--muted); font-size:12px; }}
</style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <h1>VeriOps Audit Scorecard</h1>
      <p class="sub">Generated at {generated_at}</p>
      <div class="score">
        <div class="big">{score}</div>
        <div class="grade">Grade {grade}</div>
      </div>
      <div class="grid">
        {card("API coverage", f"{k['api_coverage']['coverage_pct']}%", f"Undocumented: {k['api_coverage']['undocumented_operations']} / {k['api_coverage']['total_operations']} operations")}
        {card("Example reliability", f"{k['example_reliability']['example_reliability_pct']}%", f"Executed: {k['example_reliability']['executed_examples']}, failed: {k['example_reliability']['failed_examples']}")}
        {card("Freshness (median age)", f"{k['freshness']['median_age_days']} days", f"Stale over threshold: {k['freshness']['stale_docs_pct']}%")}
        {card("Docs contract drift", f"{k['drift']['docs_contract_drift_pct']}%", f"Mismatches: {k['drift']['docs_contract_mismatch_count']}")}
        {card("Layer completeness", f"{100.0 - k['layer_completeness']['features_missing_required_layers_pct']}%", f"Features missing layers: {k['layer_completeness']['features_missing_required_layers']}")}
        {card("Terminology consistency", f"{k['terminology']['terminology_consistency_pct']}%", f"Forbidden term occurrences: {k['terminology']['forbidden_term_occurrences']}")}
      </div>
    </div>

    <div class="section">
      <h2>Business Impact Estimate (Monthly)</h2>
      <table class="kpi-table">
        <tr><th>Metric</th><th>Estimate</th></tr>
        <tr><td>Engineering hours lost</td><td>{impact['engineering_hours']} h</td></tr>
        <tr><td>Support hours burden</td><td>{impact['support_hours']} h</td></tr>
        <tr><td>Release delay risk</td><td>{impact['release_delay_hours']} h</td></tr>
        <tr><td>Opportunity cost</td><td>${impact['monthly_cost_usd']}</td></tr>
      </table>
      <p class="foot">Per-finding totals (low/base/high): remediation ${findings_totals.get('remediation_cost_usd_low_total', 0)} / ${findings_totals.get('remediation_cost_usd_base_total', 0)} / ${findings_totals.get('remediation_cost_usd_high_total', 0)}, monthly loss ${findings_totals.get('monthly_loss_usd_low_total', 0)} / ${findings_totals.get('monthly_loss_usd_base_total', 0)} / ${findings_totals.get('monthly_loss_usd_high_total', 0)}.</p>
      <p class="foot">Fixability coverage: pilot can close {findings_totals.get('pilot_fixable_count', 0)} of {findings_totals.get('findings_count', 0)} findings; full implementation can close {findings_totals.get('full_fixable_count', 0)} of {findings_totals.get('findings_count', 0)}.</p>
    </div>

    <div class="section">
      <h2>Findings Matrix (Fixability + Cost per Issue)</h2>
      <table class="kpi-table">
        <tr>
          <th>ID</th><th>Issue</th><th>Severity</th><th>Capability</th><th>Gap</th><th>Pilot/Full</th><th>Effort (L/B/H)</th><th>Fix Cost (L/B/H)</th><th>Monthly Loss (L/B/H)</th><th>Confidence</th>
        </tr>
        {findings_rows}
      </table>
    </div>

    <div class="section">
      <h2>Pipeline Coverage Matrix (What can be fixed)</h2>
      <table class="kpi-table">
        <tr><th>Capability ID</th><th>Capability</th><th>Modules</th><th>Flow</th><th>Pilot/Full</th></tr>
        {capability_rows}
      </table>
    </div>

    <div class="section">
      <h2>Top 3 Gaps To Fix First</h2>
      <ol class="top3">
        {top3_html}
      </ol>
    </div>

    <div class="section">
      <h2>Retrieval Quality</h2>
      <table class="kpi-table">
        <tr><th>Precision@k</th><th>Recall@k</th><th>Hallucination rate</th></tr>
        <tr>
          <td>{k['retrieval_quality']['precision_at_k']}</td>
          <td>{k['retrieval_quality']['recall_at_k']}</td>
          <td>{k['retrieval_quality']['hallucination_rate']}</td>
        </tr>
      </table>
      <p class="foot">If retrieval report is missing, run: npm run eval:retrieval</p>
    </div>
  </div>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate audit scorecard JSON + HTML")
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--spec-path", default="api/openapi.yaml")
    parser.add_argument("--policy-pack", default="policy_packs/api-first.yml")
    parser.add_argument("--glossary-path", default="glossary.yml")
    parser.add_argument("--stale-days", type=int, default=180)
    parser.add_argument("--assumptions-json", default="")
    parser.add_argument("--auto-run-smoke", action="store_true")
    parser.add_argument("--json-output", default="reports/audit_scorecard.json")
    parser.add_argument("--html-output", default="reports/audit_scorecard.html")
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    reports_dir = Path(args.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    kpis = {
        "api_coverage": _api_coverage_metrics(docs_dir, Path(args.spec_path)),
        "example_reliability": _examples_reliability_metrics(reports_dir, docs_dir, bool(args.auto_run_smoke)),
        "freshness": _freshness_metrics(docs_dir, int(args.stale_days)),
        "drift": _drift_metrics(reports_dir),
        "layer_completeness": _layer_completeness_metrics(docs_dir, Path(args.policy_pack) if args.policy_pack else None),
        "retrieval_quality": _retrieval_metrics(reports_dir),
        "terminology": _terminology_metrics(docs_dir, Path(args.glossary_path), reports_dir),
    }
    assumptions = _load_assumptions(Path(args.assumptions_json) if str(args.assumptions_json).strip() else None)
    findings = _build_findings(kpis, assumptions)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "score": _overall_score(kpis),
        "kpis": kpis,
        "business_impact": _business_impact(kpis, assumptions),
        "capability_matrix": _capability_matrix(),
        "findings": findings,
        "findings_totals": _findings_totals(findings),
        "top_3_gaps": _top3_gaps(reports_dir),
    }

    json_out = Path(args.json_output)
    html_out = Path(args.html_output)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    html_out.parent.mkdir(parents=True, exist_ok=True)

    json_out.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    html_out.write_text(_build_html(payload), encoding="utf-8")

    print(f"[ok] audit scorecard JSON: {json_out}")
    print(f"[ok] audit scorecard HTML: {html_out}")
    print(
        "[ok] summary: "
        f"score={payload['score']['audit_score_0_100']} "
        f"api_coverage={kpis['api_coverage']['coverage_pct']}% "
        f"example_reliability={kpis['example_reliability']['example_reliability_pct']}%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

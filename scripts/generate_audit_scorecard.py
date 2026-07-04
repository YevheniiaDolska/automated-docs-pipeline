#!/usr/bin/env python3
"""Generate a sales-grade docs audit scorecard (JSON + HTML).

This report aggregates hard KPIs and adds a business-impact estimate layer.
It is intended for discovery/readout calls and pilot-to-full conversion.
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import math
import os
import re
import statistics
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

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

DEFAULT_SALES_JSON_FILENAME = "sales_teardown.json"
DEFAULT_SALES_HTML_FILENAME = "sales_teardown.html"
DEFAULT_SALES_PDF_FILENAME = "sales_teardown.pdf"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (yaml.YAMLError, ValueError, TypeError, OSError):  # noqa: BLE001
        return {}


def _resolve_optional_report_path(raw_path: str) -> Path | None:
    """Resolve an optional report path and ignore empty values."""
    value = str(raw_path).strip()
    if not value:
        return None
    return Path(value)


def _default_sales_output_path(base_output: Path, filename: str) -> Path:
    """Build a default sales asset path next to the main scorecard outputs."""
    return base_output.parent / filename


def _render_html_to_pdf_with_browser(html_input: Path, pdf_output: Path) -> tuple[bool, str]:
    """Render HTML to PDF through the browser-based export helper."""
    cmd = [
        "python3",
        "scripts/render_html_to_pdf_browser.py",
        "--html-input",
        str(html_input),
        "--pdf-output",
        str(pdf_output),
    ]
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=25)
    except subprocess.TimeoutExpired:
        return False, (
            "browser PDF export timed out; ensure Playwright Chromium is installed and runnable "
            "(try `npx playwright install chromium` or the interpreter-specific install command)"
        )
    if result.returncode == 0:
        return True, result.stdout.strip()
    message = result.stderr.strip() or result.stdout.strip() or f"browser PDF export failed with exit {result.returncode}"
    return False, message


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
    monthly_doc_influenced_evals: float = 40.0
    eval_to_customer_rate: float = 0.08
    avg_customer_monthly_value_usd: float = 2500.0
    docs_friction_revenue_sensitivity: float = 0.35


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
        monthly_doc_influenced_evals=float(payload.get("monthly_doc_influenced_evals", defaults.monthly_doc_influenced_evals)),
        eval_to_customer_rate=float(payload.get("eval_to_customer_rate", defaults.eval_to_customer_rate)),
        avg_customer_monthly_value_usd=float(payload.get("avg_customer_monthly_value_usd", defaults.avg_customer_monthly_value_usd)),
        docs_friction_revenue_sensitivity=float(
            payload.get("docs_friction_revenue_sensitivity", defaults.docs_friction_revenue_sensitivity)
        ),
    )


def _business_impact(kpis: dict[str, Any], assumptions: CostAssumptions) -> dict[str, Any]:
    undocumented_pct = float(kpis["api_coverage"]["undocumented_pct"])
    stale_pct = float(kpis["freshness"]["stale_docs_pct"])
    drift_pct = float(kpis["drift"]["docs_contract_drift_pct"])
    example_reliability = float(kpis["example_reliability"]["example_reliability_pct"])
    terminology_violation_pct = float(kpis["terminology"]["terminology_violation_pct"])
    layers_missing_pct = float(kpis["layer_completeness"]["features_missing_required_layers_pct"])
    retrieval = kpis["retrieval_quality"]
    retrieval_quality_pct = (
        (float(retrieval["precision_at_k"]) * 100.0 + float(retrieval["recall_at_k"]) * 100.0) / 2.0
        if retrieval.get("report_found")
        else 65.0
    )
    hallucination_penalty_pct = float(retrieval["hallucination_rate"]) * 100.0 if retrieval.get("report_found") else 10.0

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

    # -- Itemized monthly expense components (base scenario) ------------------
    # Each line item records its formula and inputs so the teardown can show
    # exactly where the monthly number comes from. Items are computed first
    # and the headline totals are derived from them, so the breakdown always
    # sums to the reported totals.
    baseline_upkeep_hours = assumptions.baseline_manual_sync_hours_per_week * 4.3
    release_delay_hours = assumptions.release_count_per_month * assumptions.avg_release_delay_hours * risk_index
    undocumented_drag_hours = (undocumented_pct / 100.0) * 10.0
    example_drag_hours = ((100.0 - example_reliability) / 100.0) * 12.0
    engineering_hours = baseline_upkeep_hours + release_delay_hours + undocumented_drag_hours + example_drag_hours
    support_hours = (
        assumptions.monthly_support_tickets
        * assumptions.docs_related_ticket_share
        * (assumptions.avg_ticket_handling_minutes / 60.0)
        * (0.5 + risk_index)
    )

    expense_items: list[dict[str, Any]] = [
        {
            "id": "manual_docs_upkeep",
            "label": "Manual docs upkeep the automation replaces",
            "category": "existing_process_cost",
            "formula": "baseline_manual_sync_hours_per_week x 4.3 weeks x engineer_hourly_usd",
            "inputs": {
                "baseline_manual_sync_hours_per_week": assumptions.baseline_manual_sync_hours_per_week,
                "engineer_hourly_usd": assumptions.engineer_hourly_usd,
            },
            "hours": round(baseline_upkeep_hours, 1),
            "monthly_usd": round(baseline_upkeep_hours * assumptions.engineer_hourly_usd, 2),
            "note": "Cost of keeping docs in sync by hand today. It does not depend on audit findings; it is what the pipeline automates away.",
        },
        {
            "id": "release_delay_drag",
            "label": "Release delay caused by docs work",
            "category": "quality_drag",
            "formula": "release_count_per_month x avg_release_delay_hours x risk_index x engineer_hourly_usd",
            "inputs": {
                "release_count_per_month": assumptions.release_count_per_month,
                "avg_release_delay_hours": assumptions.avg_release_delay_hours,
                "risk_index": round(risk_index, 3),
                "engineer_hourly_usd": assumptions.engineer_hourly_usd,
            },
            "hours": round(release_delay_hours, 1),
            "monthly_usd": round(release_delay_hours * assumptions.engineer_hourly_usd, 2),
            "note": "Scales with the measured risk index; zero when the audit finds no gaps.",
        },
        {
            "id": "undocumented_api_drag",
            "label": "Engineering answering questions undocumented APIs create",
            "category": "quality_drag",
            "formula": "(undocumented_pct / 100) x 10 h full-gap coefficient x engineer_hourly_usd",
            "inputs": {
                "undocumented_pct": round(undocumented_pct, 1),
                "full_gap_hours_coefficient": 10.0,
                "engineer_hourly_usd": assumptions.engineer_hourly_usd,
            },
            "hours": round(undocumented_drag_hours, 1),
            "monthly_usd": round(undocumented_drag_hours * assumptions.engineer_hourly_usd, 2),
            "note": "Proportional to the measured undocumented-API share.",
        },
        {
            "id": "broken_example_drag",
            "label": "Debugging integrations broken examples cause",
            "category": "quality_drag",
            "formula": "((100 - example_reliability_pct) / 100) x 12 h full-gap coefficient x engineer_hourly_usd",
            "inputs": {
                "example_reliability_pct": round(example_reliability, 1),
                "full_gap_hours_coefficient": 12.0,
                "engineer_hourly_usd": assumptions.engineer_hourly_usd,
            },
            "hours": round(example_drag_hours, 1),
            "monthly_usd": round(example_drag_hours * assumptions.engineer_hourly_usd, 2),
            "note": "Proportional to the measured share of failing code examples.",
        },
        {
            "id": "docs_driven_support",
            "label": "Support time on docs-related tickets",
            "category": "support_cost",
            "formula": "monthly_support_tickets x docs_related_ticket_share x (avg_ticket_handling_minutes / 60) x (0.5 + risk_index) x support_hourly_usd",
            "inputs": {
                "monthly_support_tickets": assumptions.monthly_support_tickets,
                "docs_related_ticket_share": assumptions.docs_related_ticket_share,
                "avg_ticket_handling_minutes": assumptions.avg_ticket_handling_minutes,
                "risk_index": round(risk_index, 3),
                "support_hourly_usd": assumptions.support_hourly_usd,
            },
            "hours": round(support_hours, 1),
            "monthly_usd": round(support_hours * assumptions.support_hourly_usd, 2),
            "note": "Docs-attributable ticket load, scaled between 0.5x and 1.5x of the nominal share by the measured risk index.",
        },
    ]

    operational_cost = engineering_hours * assumptions.engineer_hourly_usd + support_hours * assumptions.support_hourly_usd

    commercial_friction_index = min(
        max(
            (
                0.20 * (undocumented_pct / 100.0)
                + 0.10 * (stale_pct / 100.0)
                + 0.10 * (drift_pct / 100.0)
                + 0.20 * (layers_missing_pct / 100.0)
                + 0.20 * ((100.0 - example_reliability) / 100.0)
                + 0.10 * ((100.0 - retrieval_quality_pct) / 100.0)
                + 0.10 * (hallucination_penalty_pct / 100.0)
            ),
            0.0,
        ),
        1.0,
    )
    customers_at_risk = (
        assumptions.monthly_doc_influenced_evals
        * assumptions.eval_to_customer_rate
        * assumptions.docs_friction_revenue_sensitivity
        * commercial_friction_index
    )
    revenue_risk_usd = customers_at_risk * assumptions.avg_customer_monthly_value_usd
    total_signal_usd = operational_cost + revenue_risk_usd

    expense_items.append(
        {
            "id": "revenue_at_risk",
            "label": "Revenue at risk from evaluations lost to docs friction",
            "category": "revenue_risk",
            "formula": (
                "monthly_doc_influenced_evals x eval_to_customer_rate x "
                "docs_friction_revenue_sensitivity x commercial_friction_index x avg_customer_monthly_value_usd"
            ),
            "inputs": {
                "monthly_doc_influenced_evals": assumptions.monthly_doc_influenced_evals,
                "eval_to_customer_rate": assumptions.eval_to_customer_rate,
                "docs_friction_revenue_sensitivity": assumptions.docs_friction_revenue_sensitivity,
                "commercial_friction_index": round(commercial_friction_index, 3),
                "avg_customer_monthly_value_usd": assumptions.avg_customer_monthly_value_usd,
            },
            "hours": None,
            "monthly_usd": round(revenue_risk_usd, 2),
            "note": "Expected value of would-be customers who churn during evaluation because of docs friction; not booked revenue.",
        }
    )

    for item in expense_items:
        item["annual_usd"] = round(float(item.get("monthly_usd", 0.0) or 0.0) * 12.0, 2)

    monthly_expense_breakdown = {
        "items": expense_items,
        "operational_subtotal_usd": round(operational_cost, 2),
        "revenue_risk_subtotal_usd": round(revenue_risk_usd, 2),
        "total_monthly_usd": round(total_signal_usd, 2),
        "total_annual_usd": round(total_signal_usd * 12.0, 2),
        "methodology_note": (
            "Base-scenario estimate built only from the line items above. Every input is an "
            "adjustable assumption (see 'assumptions'); pass --assumptions <file.json> to recalculate "
            "with the client's own numbers. Conservative/aggressive scenarios apply x0.7 / x1.4. "
            "The 'manual docs upkeep' line is the cost of today's manual process (what automation "
            "replaces), not damage caused by documentation gaps."
        ),
    }

    def _scenario(multiplier: float) -> dict[str, float]:
        return {
            "monthly_cost_usd": round(operational_cost * multiplier, 2),
            "revenue_risk_usd": round(revenue_risk_usd * multiplier, 2),
            "total_signal_usd": round(total_signal_usd * multiplier, 2),
            "engineering_hours": round(engineering_hours * multiplier, 2),
            "support_hours": round(support_hours * multiplier, 2),
            "release_delay_hours": round(release_delay_hours * multiplier, 2),
            "potential_customers_lost": round(customers_at_risk * multiplier, 2),
        }

    return {
        "risk_index_0_to_1": round(risk_index, 3),
        "commercial_friction_index_0_to_1": round(commercial_friction_index, 3),
        "risk_weights": {
            "undocumented": w_undoc,
            "stale": w_stale,
            "drift": w_drift,
            "example_gap": w_ex,
            "terminology": w_term,
        },
        "engineering_support_hours_lost_estimate": _scenario(1.0),
        "monthly_expense_breakdown": monthly_expense_breakdown,
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


def _allocate_finding_monthly_losses(
    findings: list[dict[str, Any]],
    kpis: dict[str, Any],
    impact: dict[str, Any],
) -> None:
    """Replace effort-derived per-finding monthly losses with allocated shares
    of the driver-based cost model.

    The previous heuristic scaled monthly loss from remediation effort, which
    made finding-level dollars unrelated to the headline monthly cost signal.
    This allocation distributes the quality-attributable portion of the driver
    model (direct drag items + risk-driven pool + revenue-risk pool) across
    findings by their measured contribution, so per-finding losses sum to the
    attributable share of the monthly cost signal. The manual-upkeep baseline
    is deliberately excluded: it is not caused by any finding.
    """
    breakdown = impact.get("monthly_expense_breakdown", {})
    raw_items = breakdown.get("items", []) if isinstance(breakdown, dict) else []
    items = {
        str(item.get("id", "")): float(item.get("monthly_usd", 0.0) or 0.0)
        for item in raw_items
        if isinstance(item, dict)
    }
    if not items:
        return

    risk_index = float(impact.get("risk_index_0_to_1", 0.0) or 0.0)
    weights = impact.get("risk_weights", {}) if isinstance(impact.get("risk_weights"), dict) else {}

    undocumented_pct = float(kpis["api_coverage"]["undocumented_pct"])
    stale_pct = float(kpis["freshness"]["stale_docs_pct"])
    drift_pct = float(kpis["drift"]["docs_contract_drift_pct"])
    example_gap_pct = max(0.0, 100.0 - float(kpis["example_reliability"]["example_reliability_pct"]))
    terminology_pct = float(kpis["terminology"]["terminology_violation_pct"])
    layers_pct = float(kpis["layer_completeness"]["features_missing_required_layers_pct"])
    retrieval = kpis["retrieval_quality"]
    retrieval_quality_pct = (
        (float(retrieval["precision_at_k"]) * 100.0 + float(retrieval["recall_at_k"]) * 100.0) / 2.0
        if retrieval.get("report_found")
        else 65.0
    )
    hallucination_pct = float(retrieval["hallucination_rate"]) * 100.0 if retrieval.get("report_found") else 10.0

    # Direct drag items map 1:1 to a finding.
    direct_usd = {
        "F-API-COVERAGE": items.get("undocumented_api_drag", 0.0),
        "F-EXAMPLES-RELIABILITY": items.get("broken_example_drag", 0.0),
    }

    # Risk-driven pool: release delay plus the risk-scaled share of support
    # (the 0.5 baseline share of support exists even with perfect docs).
    support_usd = items.get("docs_driven_support", 0.0)
    support_attributable = support_usd * (risk_index / (0.5 + risk_index)) if risk_index > 0 else 0.0
    risk_pool_usd = items.get("release_delay_drag", 0.0) + support_attributable
    risk_contrib = {
        "F-API-COVERAGE": float(weights.get("undocumented", 0.30)) * undocumented_pct / 100.0,
        "F-FRESHNESS": float(weights.get("stale", 0.20)) * stale_pct / 100.0,
        "F-DRIFT": float(weights.get("drift", 0.20)) * drift_pct / 100.0,
        "F-EXAMPLES-RELIABILITY": float(weights.get("example_gap", 0.20)) * example_gap_pct / 100.0,
        "F-TERMINOLOGY": float(weights.get("terminology", 0.10)) * terminology_pct / 100.0,
    }
    risk_contrib_total = sum(risk_contrib.values())

    # Revenue pool split by the same weights the commercial friction index uses.
    revenue_pool_usd = items.get("revenue_at_risk", 0.0)
    friction_contrib = {
        "F-API-COVERAGE": 0.20 * undocumented_pct / 100.0,
        "F-FRESHNESS": 0.10 * stale_pct / 100.0,
        "F-DRIFT": 0.10 * drift_pct / 100.0,
        "F-LAYERS": 0.20 * layers_pct / 100.0,
        "F-EXAMPLES-RELIABILITY": 0.20 * example_gap_pct / 100.0,
        "F-RETRIEVAL": 0.10 * (100.0 - retrieval_quality_pct) / 100.0 + 0.10 * hallucination_pct / 100.0,
    }
    friction_contrib_total = sum(friction_contrib.values())

    for finding in findings:
        finding_id = str(finding.get("id", ""))
        base = direct_usd.get(finding_id, 0.0)
        if risk_contrib_total > 0:
            base += risk_pool_usd * risk_contrib.get(finding_id, 0.0) / risk_contrib_total
        if friction_contrib_total > 0:
            base += revenue_pool_usd * friction_contrib.get(finding_id, 0.0) / friction_contrib_total
        finding["estimated_monthly_loss_usd_low"] = round(base * 0.7, 2)
        finding["estimated_monthly_loss_usd_base"] = round(base, 2)
        finding["estimated_monthly_loss_usd_high"] = round(base * 1.4, 2)
        finding["estimated_annual_loss_usd_base"] = round(base * 12.0, 2)
        remediation_base = float(finding.get("estimated_remediation_cost_usd_base", 0.0) or 0.0)
        if base > 0 and remediation_base > 0:
            finding["payback_months"] = round(remediation_base / base, 1)
            finding["first_year_roi_multiple"] = round((base * 12.0) / remediation_base, 1)
        else:
            finding["payback_months"] = None
            finding["first_year_roi_multiple"] = None
        finding["monthly_loss_derivation"] = (
            "allocated share of the driver-based monthly cost model "
            "(direct drag + risk-pool share + revenue-risk share); "
            "excludes the manual-upkeep baseline"
            if base > 0
            else "no measured cost contribution attributed to this finding yet"
        )


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


def _extract_public_audit_metrics(public_audit: dict[str, Any]) -> dict[str, Any]:
    """Extract stable public-audit metrics used by the sales teardown."""
    sites = public_audit.get("sites", [])
    site = sites[0] if isinstance(sites, list) and sites and isinstance(sites[0], dict) else {}
    site_metrics = site.get("metrics", {}) if isinstance(site.get("metrics"), dict) else {}
    aggregate = public_audit.get("aggregate", {}) if isinstance(public_audit.get("aggregate"), dict) else {}
    aggregate_metrics = aggregate.get("metrics", {}) if isinstance(aggregate.get("metrics"), dict) else {}
    metrics = site_metrics or aggregate_metrics
    if not metrics:
        return {}
    crawl = metrics.get("crawl", {}) if isinstance(metrics.get("crawl"), dict) else {}
    links = metrics.get("links", {}) if isinstance(metrics.get("links"), dict) else {}
    coverage = metrics.get("api_coverage", {}) if isinstance(metrics.get("api_coverage"), dict) else {}
    quality = metrics.get("examples", {}) if isinstance(metrics.get("examples"), dict) else {}
    seo_geo = metrics.get("seo_geo", {}) if isinstance(metrics.get("seo_geo"), dict) else {}
    metadata = metrics.get("freshness", {}) if isinstance(metrics.get("freshness"), dict) else {}
    retrieval = metrics.get("retrieval_readiness", {}) if isinstance(metrics.get("retrieval_readiness"), dict) else {}
    evidence = metrics.get("evidence_coverage", {}) if isinstance(metrics.get("evidence_coverage"), dict) else {}
    actionability = metrics.get("actionability", {}) if isinstance(metrics.get("actionability"), dict) else {}
    return {
        "site_url": str(site.get("site_url", public_audit.get("site_url", ""))).strip(),
        "pages_crawled": int(crawl.get("pages_crawled", 0) or 0),
        "urls_examined": int(crawl.get("urls_examined", 0) or 0),
        "crawl_coverage_pct": float(crawl.get("crawl_coverage_pct", 0.0) or 0.0),
        "confirmed_broken_links_count": int(links.get("confirmed_broken_links_count", 0) or 0),
        "unverified_links_count": int(links.get("unverified_links_count", 0) or 0),
        "api_coverage_pct": float(coverage.get("reference_coverage_pct", 0.0) or 0.0),
        "api_pages_detected": int(coverage.get("api_pages_detected", 0) or 0),
        "example_reliability_pct": float(quality.get("example_reliability_estimate_pct", 0.0) or 0.0),
        "seo_geo_issue_pct": float(seo_geo.get("seo_geo_issue_rate_pct", 0.0) or 0.0),
        "freshness_metadata_pct": float(metadata.get("last_updated_coverage_pct", 0.0) or 0.0),
        "retrieval_chunkability_pct": float(retrieval.get("chunkability_pct", 0.0) or 0.0),
        "retrieval_answerability_pct": float(retrieval.get("answerability_pct", 0.0) or 0.0),
        "retrieval_citationability_pct": float(retrieval.get("citationability_pct", 0.0) or 0.0),
        "retrieval_stale_risk_pct": float(retrieval.get("stale_risk_pct", 0.0) or 0.0),
        "evidence_coverage_pct": float(evidence.get("coverage_pct", 0.0) or 0.0),
        "actionability_coverage_pct": float(actionability.get("coverage_pct", 0.0) or 0.0),
    }


def _merge_kpis_with_public_audit(base_kpis: dict[str, Any], public_audit: dict[str, Any]) -> dict[str, Any]:
    """Override repo-local KPI sources with site-specific public audit metrics when available."""
    public_metrics = _extract_public_audit_metrics(public_audit)
    if not public_metrics:
        return base_kpis

    pages_crawled = max(1, int(public_metrics.get("pages_crawled", 0) or 0))
    api_coverage_pct = float(public_metrics.get("api_coverage_pct", 0.0) or 0.0)
    example_reliability_pct = float(public_metrics.get("example_reliability_pct", 0.0) or 0.0)
    freshness_coverage_pct = float(public_metrics.get("freshness_metadata_pct", 0.0) or 0.0)
    retrieval_chunkability_pct = float(public_metrics.get("retrieval_chunkability_pct", 0.0) or 0.0)
    retrieval_answerability_pct = float(public_metrics.get("retrieval_answerability_pct", 0.0) or 0.0)
    retrieval_citationability_pct = float(public_metrics.get("retrieval_citationability_pct", 0.0) or 0.0)
    retrieval_stale_risk_pct = float(public_metrics.get("retrieval_stale_risk_pct", 0.0) or 0.0)
    evidence_coverage_pct = float(public_metrics.get("evidence_coverage_pct", 0.0) or 0.0)
    actionability_coverage_pct = float(public_metrics.get("actionability_coverage_pct", 0.0) or 0.0)

    merged = dict(base_kpis)
    merged["api_coverage"] = {
        "spec_found": True,
        "total_operations": max(1, int(public_metrics.get("api_pages_detected", 0) or 0)),
        "documented_operations": int(round(max(0.0, min(100.0, api_coverage_pct)) / 100.0 * max(1, int(public_metrics.get("api_pages_detected", 0) or 0)))),
        "undocumented_operations": int(round((100.0 - max(0.0, min(100.0, api_coverage_pct))) / 100.0 * max(1, int(public_metrics.get("api_pages_detected", 0) or 0)))),
        "coverage_pct": round(api_coverage_pct, 2),
        "undocumented_pct": round(max(0.0, 100.0 - api_coverage_pct), 2),
    }
    merged["example_reliability"] = {
        "report_found": True,
        "report_path": "public-audit-proxy",
        "executed_examples": pages_crawled,
        "failed_examples": int(round((100.0 - max(0.0, min(100.0, example_reliability_pct))) / 100.0 * pages_crawled)),
        "example_reliability_pct": round(example_reliability_pct, 2),
    }
    merged["freshness"] = {
        "total_docs": pages_crawled,
        "dated_docs": int(round((freshness_coverage_pct / 100.0) * pages_crawled)),
        "missing_date_docs": int(round(((100.0 - freshness_coverage_pct) / 100.0) * pages_crawled)),
        "average_age_days": float(base_kpis.get("freshness", {}).get("average_age_days", 0.0) or 0.0),
        "median_age_days": float(base_kpis.get("freshness", {}).get("median_age_days", 0.0) or 0.0),
        "stale_days_threshold": int(base_kpis.get("freshness", {}).get("stale_days_threshold", 180) or 180),
        "stale_docs_count": int(round((retrieval_stale_risk_pct / 100.0) * pages_crawled)),
        "stale_docs_pct": round(retrieval_stale_risk_pct, 2),
    }
    merged["drift"] = {
        "docs_contract_report_found": True,
        "api_drift_report_found": False,
        "docs_contract_mismatch_count": int(round(((100.0 - evidence_coverage_pct) / 100.0) * pages_crawled)),
        "docs_contract_interface_count": pages_crawled,
        "docs_contract_drift_pct": round(max(0.0, 100.0 - evidence_coverage_pct), 2),
        "api_drift_status": "public-audit-proxy",
    }
    missing_layers_pct = max(0.0, 100.0 - actionability_coverage_pct)
    merged["layer_completeness"] = {
        "required_layers": ["concept", "how-to", "reference"],
        "total_features": pages_crawled,
        "features_missing_required_layers": int(round((missing_layers_pct / 100.0) * pages_crawled)),
        "features_missing_required_layers_pct": round(missing_layers_pct, 2),
        "sample_missing_features": [],
    }
    merged["retrieval_quality"] = {
        "report_found": True,
        "status": "public-audit-proxy",
        "precision_at_k": round(retrieval_chunkability_pct / 100.0, 4),
        "recall_at_k": round(min(retrieval_answerability_pct, retrieval_citationability_pct) / 100.0, 4),
        "hallucination_rate": round(max(0.0, min(1.0, (100.0 - evidence_coverage_pct) / 100.0)), 4),
        "top_k": 3,
    }
    merged["terminology"] = {
        "glossary_found": False,
        "forbidden_term_occurrences": int(round((max(0.0, public_metrics.get("seo_geo_issue_pct", 0.0) or 0.0) / 100.0) * pages_crawled * 0.25)),
        "terminology_violation_pct": round(max(0.0, min(100.0, (public_metrics.get("seo_geo_issue_pct", 0.0) or 0.0) * 0.4)), 2),
        "terminology_consistency_pct": round(100.0 - max(0.0, min(100.0, (public_metrics.get("seo_geo_issue_pct", 0.0) or 0.0) * 0.4)), 2),
    }
    return merged


def _extract_llm_analysis(llm_summary: dict[str, Any]) -> dict[str, Any]:
    """Extract normalized LLM analysis sections for presentation."""
    analysis = llm_summary.get("analysis", {}) if isinstance(llm_summary.get("analysis"), dict) else {}
    strengths = analysis.get("strengths", []) if isinstance(analysis.get("strengths"), list) else []
    risks = analysis.get("risks", []) if isinstance(analysis.get("risks"), list) else []
    limitations = analysis.get("limitations", []) if isinstance(analysis.get("limitations"), list) else []
    prioritized_actions = analysis.get("prioritized_actions", []) if isinstance(analysis.get("prioritized_actions"), list) else []
    automation_first = analysis.get("automation_first", []) if isinstance(analysis.get("automation_first"), list) else []
    return {
        "executive_summary": str(analysis.get("executive_summary", "")).strip(),
        "strengths": [str(item).strip() for item in strengths if str(item).strip()],
        "risks": [str(item).strip() for item in risks if str(item).strip()],
        "limitations": [str(item).strip() for item in limitations if str(item).strip()],
        "prioritized_actions": [
            {
                "action": str(item.get("action", "")).strip(),
                "impact": str(item.get("impact", "")).strip(),
                "effort": str(item.get("effort", "")).strip(),
                "expected_value": str(item.get("expected_value", "")).strip(),
                "confidence": str(item.get("confidence", "")).strip(),
                "why_this_first": str(item.get("why_this_first", "")).strip(),
            }
            for item in prioritized_actions
            if isinstance(item, dict) and str(item.get("action", "")).strip()
        ],
        "automation_first": [str(item).strip() for item in automation_first if str(item).strip()],
    }


def _priority_bucket_score(value: str, *, inverse: bool = False) -> float:
    """Convert qualitative priority buckets into sortable numeric weights."""
    mapping = {
        "critical": 4.0,
        "high": 3.0,
        "medium": 2.0,
        "low": 1.0,
    }
    normalized = str(value or "").strip().lower()
    base = mapping.get(normalized, 0.0)
    if not inverse:
        return base
    inverse_mapping = {
        "low": 4.0,
        "medium": 2.5,
        "high": 1.0,
    }
    return inverse_mapping.get(normalized, 0.0)


def _llm_action_priority_score(action: dict[str, str]) -> float:
    """Rank LLM actions by expected near-term value, then impact, then effort."""
    return (
        _priority_bucket_score(action.get("expected_value", ""))
        * 4.0
        + _priority_bucket_score(action.get("impact", "")) * 2.0
        + _priority_bucket_score(action.get("confidence", "")) * 1.5
        + _priority_bucket_score(action.get("effort", ""), inverse=True)
    )


def _finding_priority_score(item: dict[str, Any]) -> float:
    """Estimate value-per-effort so deterministic fallback favors likely ROI-first fixes."""
    monthly_loss = float(item.get("estimated_monthly_loss_usd_base", 0.0) or 0.0)
    effort_hours = max(1.0, float(item.get("effort_hours_base", 0.0) or 1.0))
    confidence = _priority_bucket_score(str(item.get("estimation_confidence", "")))
    severity = _priority_bucket_score(str(item.get("severity", "")))
    recommended_window = max(1.0, float(item.get("recommended_window_days", 30) or 30.0))
    return (monthly_loss / effort_hours) + (confidence * 120.0) + (severity * 80.0) + (30.0 / recommended_window) * 20.0


def _sales_signal_cards(
    scorecard_payload: dict[str, Any],
    public_metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build compact visual cards for the sales teardown."""
    kpis = scorecard_payload.get("kpis", {})
    api_coverage = kpis.get("api_coverage", {}) if isinstance(kpis.get("api_coverage"), dict) else {}
    freshness = kpis.get("freshness", {}) if isinstance(kpis.get("freshness"), dict) else {}
    layer_completeness = kpis.get("layer_completeness", {}) if isinstance(kpis.get("layer_completeness"), dict) else {}
    retrieval = kpis.get("retrieval_quality", {}) if isinstance(kpis.get("retrieval_quality"), dict) else {}
    cards = [
        {
            "label": "Audit Score",
            "value": f"{scorecard_payload.get('score', {}).get('audit_score_0_100', 0)} / 100",
            "accent": "teal",
            "detail": f"Grade {scorecard_payload.get('score', {}).get('grade', 'n/a')}",
        },
        {
            "label": "Broken Links",
            "value": str(public_metrics.get("confirmed_broken_links_count", 0)),
            "accent": "amber",
            "detail": f"{public_metrics.get('unverified_links_count', 0)} unverified",
        },
        {
            "label": "API Coverage",
            "value": f"{api_coverage.get('coverage_pct', 0.0)}%",
            "accent": "blue",
            "detail": f"{api_coverage.get('undocumented_operations', 0)} undocumented ops",
        },
        {
            "label": "Freshness Coverage",
            "value": f"{public_metrics.get('freshness_metadata_pct', freshness.get('dated_docs', 0))}%",
            "accent": "slate",
            "detail": f"{freshness.get('missing_date_docs', 0)} docs missing dates",
        },
        {
            "label": "Layer Completeness",
            "value": f"{round(100.0 - float(layer_completeness.get('features_missing_required_layers_pct', 0.0) or 0.0), 2)}%",
            "accent": "violet",
            "detail": f"{layer_completeness.get('features_missing_required_layers', 0)} features missing required layers",
        },
        {
            "label": "Retrieval Precision",
            "value": f"{round(float(retrieval.get('precision_at_k', 0.0) or 0.0) * 100.0, 1)}%",
            "accent": "rose",
            "detail": f"Recall {round(float(retrieval.get('recall_at_k', 0.0) or 0.0) * 100.0, 1)}%",
        },
    ]
    return cards


def _sales_key_findings(
    scorecard_payload: dict[str, Any],
    public_metrics: dict[str, Any],
    llm_analysis: dict[str, Any],
) -> list[dict[str, str]]:
    """Build concise findings with business consequences for follow-up conversations."""
    findings = scorecard_payload.get("findings", [])
    top_findings = findings[:3] if isinstance(findings, list) else []
    mapped_findings: list[dict[str, str]] = []
    for item in top_findings:
        if not isinstance(item, dict):
            continue
        mapped_findings.append(
            {
                "headline": str(item.get("title", "")).strip(),
                "evidence": (
                    f"{item.get('metric', '')}: {item.get('current_value', 0)} -> "
                    f"{item.get('target_value', 0)} {item.get('unit', '')}"
                ).strip(),
                "business_consequence": str(item.get("note", "")).strip(),
            }
        )
    if mapped_findings:
        return mapped_findings
    fallback: list[dict[str, str]] = []
    if public_metrics.get("confirmed_broken_links_count", 0) > 0:
        fallback.append(
            {
                "headline": "Broken internal documentation paths",
                "evidence": f"{public_metrics.get('confirmed_broken_links_count', 0)} confirmed broken internal links",
                "business_consequence": "Developers lose trust faster when self-serve navigation fails at the moment of implementation.",
            }
        )
    risks = llm_analysis.get("risks", [])
    for risk in risks[: max(0, 3 - len(fallback))]:
        fallback.append(
            {
                "headline": risk,
                "evidence": "Derived from automated public-docs analysis",
                "business_consequence": "This usually shows up as slower onboarding, more support dependency, or weaker AI answer quality.",
            }
        )
    return fallback


def _public_audit_priority_actions(public_metrics: dict[str, Any]) -> list[dict[str, str]]:
    """Build site-specific actions from public audit metrics first."""
    actions: list[dict[str, str]] = []

    broken_links = int(public_metrics.get("confirmed_broken_links_count", 0) or 0)
    seo_issue_pct = float(public_metrics.get("seo_geo_issue_pct", 0.0) or 0.0)
    example_reliability = float(public_metrics.get("example_reliability_pct", 0.0) or 0.0)
    freshness_coverage = float(public_metrics.get("freshness_metadata_pct", 0.0) or 0.0)
    api_coverage = float(public_metrics.get("api_coverage_pct", 0.0) or 0.0)

    if broken_links > 0:
        actions.append(
            {
                "title": f"Fix {broken_links} confirmed broken internal links in the public docs path first.",
                "impact": "high",
                "effort": "2.0h est.",
                "expected_value": "high",
                "confidence": "high",
                "why_this_first": "Broken navigation blocks self-serve progress immediately and is usually cheap to recover.",
            }
        )
    if seo_issue_pct >= 20.0:
        actions.append(
            {
                "title": f"Rewrite pages failing SEO/GEO structural checks and reduce issue coverage from {round(seo_issue_pct, 1)}%.",
                "impact": "high",
                "effort": "4.0h est.",
                "expected_value": "high",
                "confidence": "medium",
                "why_this_first": "This improves answerability, discoverability, and onboarding quality across many pages at once.",
            }
        )
    if example_reliability < 60.0:
        actions.append(
            {
                "title": "Replace non-runnable or placeholder-heavy examples in the public docs surface.",
                "impact": "medium",
                "effort": "3.0h est.",
                "expected_value": "high",
                "confidence": "medium",
                "why_this_first": "Runnable examples remove implementation friction faster than broad copy edits when users are actively integrating.",
            }
        )
    if freshness_coverage < 50.0:
        actions.append(
            {
                "title": f"Add last-reviewed metadata to pages until freshness coverage exceeds {round(freshness_coverage, 1)}%.",
                "impact": "medium",
                "effort": "2.0h est.",
                "expected_value": "medium",
                "confidence": "medium",
                "why_this_first": "Freshness visibility helps users trust the docs and lets teams prioritize stale pages with less manual triage.",
            }
        )
    if api_coverage > 0.0 and api_coverage < 80.0:
        actions.append(
            {
                "title": f"Backfill missing public API coverage and raise reference coverage from {round(api_coverage, 1)}%.",
                "impact": "medium",
                "effort": "5.0h est.",
                "expected_value": "high",
                "confidence": "medium",
                "why_this_first": "Coverage gaps create repeated support demand and slow time-to-first-success for technical evaluators.",
            }
        )
    actions.sort(key=_llm_action_priority_score, reverse=True)
    return actions


def _sales_next_steps(
    scorecard_payload: dict[str, Any],
    public_metrics: dict[str, Any],
    llm_analysis: dict[str, Any],
) -> list[dict[str, str]]:
    """Build short prioritized actions for the sales teardown."""
    actions: list[dict[str, str]] = []
    prioritized = llm_analysis.get("prioritized_actions", [])
    prioritized_sorted = sorted(
        [item for item in prioritized if isinstance(item, dict)],
        key=_llm_action_priority_score,
        reverse=True,
    )
    for item in prioritized_sorted[:5]:
        if not isinstance(item, dict):
            continue
        candidate = {
            "title": str(item.get("action", "")).strip(),
            "impact": str(item.get("impact", "")).strip() or "high",
            "effort": str(item.get("effort", "")).strip() or "medium",
            "expected_value": str(item.get("expected_value", "")).strip() or "medium",
            "confidence": str(item.get("confidence", "")).strip() or "medium",
            "why_this_first": str(item.get("why_this_first", "")).strip(),
        }
        if candidate["title"] and all(candidate["title"] != existing["title"] for existing in actions):
            actions.append(candidate)
    if len(actions) >= 3:
        return actions[:3]

    for candidate in _public_audit_priority_actions(public_metrics):
        if candidate["title"] and all(candidate["title"] != existing["title"] for existing in actions):
            actions.append(candidate)
    if len(actions) >= 3:
        return actions[:3]

    findings = scorecard_payload.get("findings", [])
    sorted_findings = sorted(findings if isinstance(findings, list) else [], key=_finding_priority_score, reverse=True)
    for item in sorted_findings[:5]:
        if not isinstance(item, dict):
            continue
        candidate = {
            "title": str(item.get("note", "")).strip() or str(item.get("title", "")).strip(),
            "impact": str(item.get("severity", "")).strip() or "medium",
            "effort": f"{item.get('effort_hours_base', 0)}h est.",
            "expected_value": "high" if float(item.get("estimated_monthly_loss_usd_base", 0.0) or 0.0) >= 500.0 else "medium",
            "confidence": str(item.get("estimation_confidence", "")).strip() or "medium",
            "why_this_first": _finding_value_statement(item),
        }
        if candidate["title"] and all(candidate["title"] != existing["title"] for existing in actions):
            actions.append(candidate)
    return actions[:3]


def _finding_value_statement(item: dict[str, Any]) -> str:
    """One-line buyer-facing value framing for a finding: annual loss + payback."""
    monthly = float(item.get("estimated_monthly_loss_usd_base", 0.0) or 0.0)
    annual = float(item.get("estimated_annual_loss_usd_base", monthly * 12.0) or 0.0)
    effort = float(item.get("effort_hours_base", 0.0) or 0.0)
    payback = item.get("payback_months")
    roi = item.get("first_year_roi_multiple")
    parts = [f"Costs about ${round(annual):,}/year (${round(monthly):,}/month) while unfixed"]
    if effort > 0:
        parts.append(f"remediation is about {effort:.1f}h")
    if payback is not None and float(payback) > 0:
        weeks = float(payback) * 4.345
        if weeks < 1.0:
            parts.append("pays for itself within the first week")
        elif weeks < 9:
            parts.append(f"payback in about {weeks:.0f} week{'s' if weeks >= 1.5 else ''}")
        else:
            parts.append(f"payback in about {float(payback):.1f} months")
    if roi is not None and float(roi) >= 2:
        parts.append(f"~{float(roi):.0f}x first-year return")
    return "; ".join(parts) + "."


def _sales_automation_priorities(
    scorecard_payload: dict[str, Any],
    public_metrics: dict[str, Any],
    llm_analysis: dict[str, Any],
) -> list[str]:
    """Map real audit findings to the automation layer that should be added first."""
    llm_priorities = llm_analysis.get("automation_first", [])
    if isinstance(llm_priorities, list):
        normalized = [str(item).strip() for item in llm_priorities if str(item).strip()]
        if normalized:
            return normalized[:3]

    kpis = scorecard_payload.get("kpis", {}) if isinstance(scorecard_payload.get("kpis"), dict) else {}
    layer_completeness = kpis.get("layer_completeness", {}) if isinstance(kpis.get("layer_completeness"), dict) else {}
    freshness = kpis.get("freshness", {}) if isinstance(kpis.get("freshness"), dict) else {}
    retrieval = kpis.get("retrieval_quality", {}) if isinstance(kpis.get("retrieval_quality"), dict) else {}
    api_coverage = kpis.get("api_coverage", {}) if isinstance(kpis.get("api_coverage"), dict) else {}
    example_reliability = kpis.get("example_reliability", {}) if isinstance(kpis.get("example_reliability"), dict) else {}

    finding_map = {
        "layer_completeness": (
            "Add doc-layer coverage checks because "
            f"{int(layer_completeness.get('features_missing_required_layers', 0) or 0)} features are missing required concept, how-to, or reference layers, "
            "so new gaps are blocked before publish and fewer evaluators get stuck in incomplete journeys."
        ),
        "freshness_lifecycle": (
            "Add weekly freshness and lifecycle automation because "
            f"{int(freshness.get('missing_date_docs', 0) or 0)} docs are missing review dates and freshness coverage is "
            f"{round(float(public_metrics.get('freshness_metadata_pct', 0.0) or 0.0), 1)}%, "
            "so stale content can be queued before trust drops."
        ),
        "retrieval_quality_control": (
            "Add retrieval evals and index-quality gates because retrieval precision is "
            f"{round(float(retrieval.get('precision_at_k', 0.0) or 0.0) * 100.0, 1)}% "
            f"and recall is {round(float(retrieval.get('recall_at_k', 0.0) or 0.0) * 100.0, 1)}%, "
            "so AI-facing answers are measured before weak grounding reaches users."
        ),
        "api_coverage_sync": (
            "Add API drift and reference-generation automation because public API coverage is "
            f"{round(float(api_coverage.get('coverage_pct', 0.0) or 0.0), 1)}% with "
            f"{int(api_coverage.get('undocumented_operations', 0) or 0)} undocumented operations, "
            "so contract changes stop creating repeat support demand."
        ),
        "example_execution_quality": (
            "Add snippet smoke and expected-output checks because example reliability is "
            f"{round(float(example_reliability.get('reliable_pct', public_metrics.get('example_reliability_pct', 0.0)) or 0.0), 1)}%, "
            "so broken examples fail before they derail implementation attempts."
        ),
        "drift_contract_visibility": (
            "Add docs-contract drift reporting on every change so reference docs stop lagging behind shipped behavior and teams see mismatches before release."
        ),
        "terminology_governance": (
            "Add glossary sync and terminology governance so inconsistent language stops fragmenting search, onboarding, and AI retrieval across the docs surface."
        ),
    }
    priorities: list[str] = []
    findings = scorecard_payload.get("findings", [])
    sorted_findings = sorted(findings if isinstance(findings, list) else [], key=_finding_priority_score, reverse=True)
    for item in sorted_findings:
        if not isinstance(item, dict):
            continue
        capability_id = str(item.get("capability_id", "")).strip()
        mapped = finding_map.get(capability_id)
        if mapped and mapped not in priorities:
            priorities.append(mapped)
        if len(priorities) >= 3:
            return priorities

    if int(public_metrics.get("confirmed_broken_links_count", 0) or 0) > 0:
        priorities.append(
            "Add scheduled link health checks because "
            f"{int(public_metrics.get('confirmed_broken_links_count', 0) or 0)} confirmed broken links are already blocking user navigation, "
            "so dead-end journeys are caught before they hit high-intent readers."
        )
    if float(public_metrics.get("seo_geo_issue_pct", 0.0) or 0.0) >= 20.0:
        priorities.append(
            "Add SEO/GEO structural checks because "
            f"{round(float(public_metrics.get('seo_geo_issue_pct', 0.0) or 0.0), 1)}% of sampled pages fail answer-first or metadata quality checks, "
            "so discoverability and first-answer quality improve across the public surface."
        )
    if float(public_metrics.get("freshness_metadata_pct", 0.0) or 0.0) < 50.0:
        priorities.append(
            "Add metadata enforcement for review-date coverage because freshness metadata is present on only "
            f"{round(float(public_metrics.get('freshness_metadata_pct', 0.0) or 0.0), 1)}% of pages, "
            "so stale content becomes visible and measurable instead of silently aging."
        )

    fallback = [
        "Add scheduled docs quality checks targeted at the measured weak points in this audit so repeated regressions are caught before publish.",
        "Add docs-contract visibility around the highest-loss findings in this audit so code and reference drift stop compounding support demand.",
        "Add retrieval quality controls tied to the concrete documentation gaps in this audit so AI-facing answer quality improves where users are already failing.",
    ]
    for item in fallback:
        if item not in priorities:
            priorities.append(item)
        if len(priorities) >= 3:
            break
    return priorities[:3]


def _pipeline_price_comparison(monthly_cost_usd: float, pipeline_price_usd: float) -> dict[str, Any]:
    """Docs-cost vs pipeline-price framing, only when genuinely favorable.

    Shown only when a price is configured AND the estimated monthly docs cost
    exceeds it -- an unfavorable comparison is omitted, never spun.
    """
    if pipeline_price_usd <= 0 or monthly_cost_usd <= pipeline_price_usd:
        return {}
    return {
        "pipeline_monthly_price_usd": round(pipeline_price_usd, 2),
        "docs_cost_monthly_usd": round(monthly_cost_usd, 2),
        "cost_to_price_multiple": round(monthly_cost_usd / pipeline_price_usd, 1),
        "monthly_net_saving_usd": round(monthly_cost_usd - pipeline_price_usd, 2),
    }


def _build_sales_teardown_payload(
    scorecard_payload: dict[str, Any],
    *,
    public_audit: dict[str, Any],
    broken_links: dict[str, Any],
    llm_summary: dict[str, Any],
) -> dict[str, Any]:
    """Build a concise sales teardown payload from existing audit artifacts."""
    public_metrics = _extract_public_audit_metrics(public_audit)
    llm_analysis = _extract_llm_analysis(llm_summary)
    findings_totals = scorecard_payload.get("findings_totals", {})
    business_impact = scorecard_payload.get("business_impact", {})
    base_impact = business_impact.get("scenarios", {}).get("base", {}) if isinstance(business_impact.get("scenarios"), dict) else {}
    site_url = str(public_metrics.get("site_url", public_audit.get("site_url", ""))).strip()
    key_findings = _sales_key_findings(scorecard_payload, public_metrics, llm_analysis)
    payload = {
        "generated_at": scorecard_payload.get("generated_at", datetime.now(timezone.utc).isoformat()),
        "site_url": site_url,
        "headline": "Public docs teardown: highest-impact fixes and the automation layer to prioritize first",
        "score": scorecard_payload.get("score", {}),
        "summary": {
            "executive_summary": llm_analysis.get("executive_summary", ""),
            "pages_crawled": int(public_metrics.get("pages_crawled", 0) or 0),
            "crawl_coverage_pct": float(public_metrics.get("crawl_coverage_pct", 0.0) or 0.0),
            "broken_links_count": int(public_metrics.get("confirmed_broken_links_count", broken_links.get("totals", {}).get("docs_broken_links_count", 0)) or 0),
            "unverified_links_count": int(public_metrics.get("unverified_links_count", 0) or 0),
            "estimated_monthly_cost_usd": float(base_impact.get("total_signal_usd", base_impact.get("monthly_cost_usd", 0.0)) or 0.0),
            "estimated_annual_cost_usd": round(
                float(base_impact.get("total_signal_usd", base_impact.get("monthly_cost_usd", 0.0)) or 0.0) * 12.0, 2
            ),
        },
        "monthly_expense_breakdown": business_impact.get("monthly_expense_breakdown", {}),
        "pipeline_comparison": _pipeline_price_comparison(
            float(base_impact.get("total_signal_usd", 0.0) or 0.0),
            float(scorecard_payload.get("pipeline_monthly_price_usd", 0.0) or 0.0),
        ),
        "signal_cards": _sales_signal_cards(scorecard_payload, public_metrics),
        "key_findings": key_findings,
        "priority_actions": _sales_next_steps(scorecard_payload, public_metrics, llm_analysis),
        "strengths": llm_analysis.get("strengths", [])[:3],
        "risks": llm_analysis.get("risks", [])[:4],
        "limitations": llm_analysis.get("limitations", [])[:3],
        "automation_first": _sales_automation_priorities(scorecard_payload, public_metrics, llm_analysis),
        "commercial_snapshot": {
            "monthly_loss_usd_base_total": float(findings_totals.get("monthly_loss_usd_base_total", 0.0) or 0.0),
            "remediation_cost_usd_base_total": float(findings_totals.get("remediation_cost_usd_base_total", 0.0) or 0.0),
            "pilot_fixable_count": int(findings_totals.get("pilot_fixable_count", 0) or 0),
            "findings_count": int(findings_totals.get("findings_count", 0) or 0),
        },
    }
    return payload


def _build_sales_teardown_html(payload: dict[str, Any]) -> str:
    """Render a polished one-page sales teardown HTML asset."""
    score = payload.get("score", {})
    summary = payload.get("summary", {})
    cards = payload.get("signal_cards", [])
    findings = payload.get("key_findings", [])
    actions = payload.get("priority_actions", [])
    strengths = payload.get("strengths", [])
    risks = payload.get("risks", [])
    automation_first = payload.get("automation_first", [])
    snapshot = payload.get("commercial_snapshot", {})
    site_url = html.escape(str(payload.get("site_url", "")))

    def _accent_class(accent: str) -> str:
        safe = str(accent or "teal").strip().lower()
        return safe if safe in {"teal", "blue", "amber", "slate", "violet", "rose"} else "teal"

    cards_html = "".join(
        (
            f"<div class='metric-card {_accent_class(item.get('accent', 'teal'))}'>"
            f"<div class='metric-label'>{html.escape(str(item.get('label', '')))}</div>"
            f"<div class='metric-value'>{html.escape(str(item.get('value', '')))}</div>"
            f"<div class='metric-detail'>{html.escape(str(item.get('detail', '')))}</div>"
            "</div>"
        )
        for item in cards
        if isinstance(item, dict)
    )
    findings_html = "".join(
        (
            "<div class='finding'>"
            "<div class='finding-tag'>Highest-impact issue</div>"
            f"<h3>{html.escape(str(item.get('headline', '')))}</h3>"
            f"<p class='evidence'>{html.escape(str(item.get('evidence', '')))}</p>"
            f"<p>{html.escape(str(item.get('business_consequence', '')))}</p>"
            "</div>"
        )
        for item in findings
        if isinstance(item, dict)
    ) or "<div class='finding'><h3>No major findings extracted</h3><p>Review the full audit bundle for more detail.</p></div>"
    actions_html = "".join(
        (
            "<li>"
            f"<strong>{html.escape(str(item.get('title', '')))}</strong>"
            f"<span>{html.escape(str(item.get('expected_value', '')))} value · {html.escape(str(item.get('impact', '')))} impact · {html.escape(str(item.get('effort', '')))}</span>"
            f"<p>{html.escape(str(item.get('why_this_first', '')))}</p>"
            "</li>"
        )
        for item in actions
        if isinstance(item, dict)
    ) or "<li><strong>No prioritized actions extracted</strong><span>Use the full audit findings matrix as fallback.</span></li>"
    strengths_html = "".join(f"<li>{html.escape(str(item))}</li>" for item in strengths)
    risks_html = "".join(f"<li>{html.escape(str(item))}</li>" for item in risks)
    automation_html = "".join(f"<li>{html.escape(str(item))}</li>" for item in automation_first) or "<li>No automation priorities extracted.</li>"
    strengths_section_html = (
        "<section class='split'>"
        "<div class='surface'>"
        "<h2 class='section-title'>What Looks Strong</h2>"
        f"<ul class='clean'>{strengths_html}</ul>"
        "</div>"
        "<div class='surface'>"
        "<h2 class='section-title'>Main Risks</h2>"
        f"<ul class='clean'>{risks_html}</ul>"
        "</div>"
        "</section>"
    ) if strengths_html and risks_html else ""

    comparison = payload.get("pipeline_comparison", {})
    price_comparison_html = ""
    if isinstance(comparison, dict) and comparison.get("cost_to_price_multiple"):
        docs_cost = float(comparison.get("docs_cost_monthly_usd", 0.0) or 0.0)
        price = float(comparison.get("pipeline_monthly_price_usd", 0.0) or 0.0)
        multiple = float(comparison.get("cost_to_price_multiple", 0.0) or 0.0)
        saving = float(comparison.get("monthly_net_saving_usd", 0.0) or 0.0)
        price_comparison_html = (
            "<section class='split' style='grid-template-columns:1fr;'>"
            "<div class='surface' style='border-left:4px solid #10b981;'>"
            "<h2 class='section-title'>The Do-Nothing Cost vs This Pipeline</h2>"
            f"<p style='font-size:15px; margin:0;'>Documentation drag currently costs an estimated "
            f"<strong>${docs_cost:,.0f}/month</strong> (itemized below) &mdash; nobody books it, but it is being paid. "
            f"The pipeline costs <strong>${price:,.0f}/month</strong>: "
            f"<strong>{multiple:.1f}x less than the problem it removes</strong>, "
            f"for a net ~${saving:,.0f}/month back.</p>"
            "</div>"
            "</section>"
        )

    breakdown = payload.get("monthly_expense_breakdown", {})
    breakdown_items = breakdown.get("items", []) if isinstance(breakdown, dict) else []

    def _expense_row(item: dict[str, Any]) -> str:
        hours = item.get("hours")
        hours_text = html.escape(str(hours)) if hours is not None else "-"
        usd_value = float(item.get("monthly_usd", 0.0) or 0.0)
        usd_text = f"{usd_value:,.0f}"
        annual_value = float(item.get("annual_usd", usd_value * 12.0) or 0.0)
        annual_text = f"{annual_value:,.0f}"
        return (
            "<tr style='border-top:1px solid #e2e8f0;'>"
            f"<td style='padding:6px 8px;'><strong>{html.escape(str(item.get('label', '')))}</strong>"
            f"<div style='color:#64748b; font-family:monospace; font-size:11px; margin-top:2px;'>{html.escape(str(item.get('formula', '')))}</div>"
            f"<div style='color:#64748b; font-size:11px;'>{html.escape(str(item.get('note', '')))}</div></td>"
            f"<td style='text-align:right; padding:6px 8px; vertical-align:top;'>{hours_text}</td>"
            f"<td style='text-align:right; padding:6px 8px; vertical-align:top;'>${usd_text}</td>"
            f"<td style='text-align:right; padding:6px 8px; vertical-align:top;'><strong>${annual_text}</strong></td>"
            "</tr>"
        )

    breakdown_rows_html = "".join(_expense_row(item) for item in breakdown_items if isinstance(item, dict))
    expense_breakdown_html = (
        "<section class='split' style='grid-template-columns:1fr;'>"
        "<div class='surface'>"
        "<h2 class='section-title'>Where The Monthly Cost Signal Comes From</h2>"
        "<table class='expense-table' style='width:100%; border-collapse:collapse; font-size:13px;'>"
        "<thead><tr>"
        "<th style='text-align:left; padding:6px 8px;'>Expense line (base scenario)</th>"
        "<th style='text-align:right; padding:6px 8px;'>Hours / mo</th>"
        "<th style='text-align:right; padding:6px 8px;'>USD / mo</th>"
        "<th style='text-align:right; padding:6px 8px;'>USD / yr</th>"
        "</tr></thead>"
        f"<tbody>{breakdown_rows_html}</tbody>"
        "<tfoot>"
        "<tr><td style='padding:6px 8px;'><strong>Operational subtotal (engineering + support)</strong></td><td></td>"
        f"<td class='expense-usd'><strong>${float(breakdown.get('operational_subtotal_usd', 0.0) or 0.0):,.0f}</strong></td>"
        f"<td class='expense-usd'><strong>${float(breakdown.get('operational_subtotal_usd', 0.0) or 0.0) * 12.0:,.0f}</strong></td></tr>"
        "<tr><td style='padding:6px 8px;'><strong>Revenue at risk subtotal</strong></td><td></td>"
        f"<td class='expense-usd'><strong>${float(breakdown.get('revenue_risk_subtotal_usd', 0.0) or 0.0):,.0f}</strong></td>"
        f"<td class='expense-usd'><strong>${float(breakdown.get('revenue_risk_subtotal_usd', 0.0) or 0.0) * 12.0:,.0f}</strong></td></tr>"
        "<tr><td style='padding:6px 8px;'><strong>Total cost signal</strong></td><td></td>"
        f"<td class='expense-usd'><strong>${float(breakdown.get('total_monthly_usd', 0.0) or 0.0):,.0f}</strong></td>"
        f"<td class='expense-usd'><strong>${float(breakdown.get('total_annual_usd', float(breakdown.get('total_monthly_usd', 0.0) or 0.0) * 12.0) or 0.0):,.0f}</strong></td></tr>"
        "</tfoot>"
        "</table>"
        f"<p class='foot'>{html.escape(str(breakdown.get('methodology_note', '')))}</p>"
        "</div>"
        "</section>"
    ) if breakdown_items else ""

    bar_definitions = [
        ("Audit score", float(score.get("audit_score_0_100", 0.0) or 0.0)),
        ("Crawl coverage", float(summary.get("crawl_coverage_pct", 0.0) or 0.0)),
        ("Pilot fixability", 100.0 * (
            float(snapshot.get("pilot_fixable_count", 0) or 0.0) / max(1.0, float(snapshot.get("findings_count", 0) or 1.0))
        )),
    ]
    bars_html = "".join(
        (
            "<div class='bar-row'>"
            f"<div class='bar-meta'><span>{html.escape(label)}</span><strong>{round(value, 1)}%</strong></div>"
            f"<div class='bar-track'><div class='bar-fill' style='width:{min(max(value, 0.0), 100.0)}%'></div></div>"
            "</div>"
        )
        for label, value in bar_definitions
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VeriOps Sales Teardown</title>
<style>
  :root {{
    --bg:#f3f6fb;
    --text:#142033;
    --muted:#66758f;
    --surface:#ffffff;
    --surface-2:#f8fbff;
    --border:#dbe4f0;
    --border-strong:#bfd0e6;
    --shadow:0 30px 80px rgba(15,23,42,.10);
    --shadow-soft:0 16px 36px rgba(15,23,42,.06);
    --teal:#0f766e;
    --blue:#1d4ed8;
    --amber:#b45309;
    --slate:#334155;
    --violet:#6d28d9;
    --rose:#be123c;
    --ink-inverse:#eff6ff;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0;
    font-family:"Avenir Next", "Segoe UI", Arial, sans-serif;
    color:var(--text);
    background:
      radial-gradient(circle at top left, rgba(20,184,166,.12), transparent 28%),
      radial-gradient(circle at top right, rgba(59,130,246,.14), transparent 24%),
      linear-gradient(180deg, #eef4ff 0%, #f8fafc 55%, #edf2f8 100%);
  }}
  .wrap {{ max-width:1180px; margin:0 auto; padding:32px 20px 48px; }}
  .hero {{
    background:
      linear-gradient(135deg, rgba(11,23,46,.98), rgba(14,116,144,.96) 58%, rgba(29,78,216,.94));
    border-radius:28px;
    color:#fff;
    padding:32px;
    box-shadow:var(--shadow);
    position:relative;
    overflow:hidden;
  }}
  .hero::before {{
    content:"";
    position:absolute;
    inset:auto -60px -80px auto;
    width:280px;
    height:280px;
    border-radius:50%;
    background:radial-gradient(circle, rgba(255,255,255,.20), rgba(255,255,255,0));
    pointer-events:none;
  }}
  .eyebrow {{ font-size:12px; letter-spacing:.14em; text-transform:uppercase; opacity:.82; }}
  h1, h2 {{
    font-family:Georgia, "Times New Roman", serif;
    letter-spacing:-0.03em;
  }}
  h1 {{ margin:10px 0 8px; font-size:42px; line-height:1.02; max-width:920px; }}
  .hero-grid {{
    margin-top:22px;
    display:grid;
    grid-template-columns: 1.3fr .9fr;
    gap:20px;
  }}
  .hero-panel, .surface {{
    background:var(--surface);
    border:1px solid var(--border);
    border-radius:22px;
    box-shadow:var(--shadow-soft);
  }}
  .hero-panel {{
    background:linear-gradient(180deg, rgba(255,255,255,.14), rgba(255,255,255,.10));
    border:1px solid rgba(255,255,255,.20);
    box-shadow:none;
    padding:20px;
    color:var(--ink-inverse);
    backdrop-filter: blur(10px);
  }}
  .hero-panel .big {{ font-size:50px; font-weight:800; line-height:1; }}
  .hero-panel .sub {{ font-size:14px; opacity:.92; }}
  .surface {{ padding:24px; margin-top:20px; background:linear-gradient(180deg, #ffffff, var(--surface-2)); }}
  .metrics {{
    display:grid;
    grid-template-columns:repeat(auto-fit, minmax(180px, 1fr));
    gap:14px;
    margin-top:20px;
  }}
  .metric-card {{
    border-radius:20px;
    padding:16px;
    background:linear-gradient(180deg, #ffffff, #f8fbff);
    border:1px solid var(--border);
    box-shadow:0 12px 28px rgba(15,23,42,.05);
  }}
  .metric-card.teal {{ border-top:4px solid var(--teal); }}
  .metric-card.blue {{ border-top:4px solid var(--blue); }}
  .metric-card.amber {{ border-top:4px solid var(--amber); }}
  .metric-card.slate {{ border-top:4px solid var(--slate); }}
  .metric-card.violet {{ border-top:4px solid var(--violet); }}
  .metric-card.rose {{ border-top:4px solid var(--rose); }}
  .metric-label {{ font-size:12px; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); }}
  .metric-value {{ margin-top:8px; font-size:30px; font-weight:800; }}
  .metric-detail {{ margin-top:6px; font-size:13px; color:var(--muted); }}
  .split {{
    display:grid;
    grid-template-columns:1.15fr .85fr;
    gap:20px;
    margin-top:20px;
  }}
  .finding {{
    padding:16px 0;
    border-bottom:1px solid var(--border);
  }}
  .finding:last-child {{ border-bottom:none; }}
  .finding-tag {{
    display:inline-flex;
    margin-bottom:10px;
    padding:5px 10px;
    border-radius:999px;
    background:#ecfeff;
    border:1px solid #bfdbfe;
    color:#155e75;
    font-size:11px;
    font-weight:700;
    letter-spacing:.08em;
    text-transform:uppercase;
  }}
  .finding h3 {{ margin:0 0 6px; font-size:20px; }}
  .finding .evidence {{ margin:0 0 8px; color:var(--blue); font-weight:600; }}
  .section-title {{ margin:0 0 14px; font-size:24px; }}
  .summary-text {{ color:var(--muted); line-height:1.6; }}
  .bar-row {{ margin-bottom:14px; }}
  .bar-meta {{ display:flex; justify-content:space-between; gap:12px; margin-bottom:6px; font-size:14px; }}
  .bar-track {{ height:12px; border-radius:999px; background:#e2e8f0; overflow:hidden; }}
  .bar-fill {{ height:100%; border-radius:999px; background:linear-gradient(90deg, var(--teal), var(--blue)); }}
  ul.clean {{ margin:0; padding-left:18px; }}
  ul.clean li {{ margin-bottom:10px; color:var(--text); }}
  ul.action-list {{ list-style:none; margin:0; padding:0; }}
  ul.action-list li {{
    display:flex;
    flex-direction:column;
    gap:4px;
    padding:14px 0;
    border-bottom:1px solid var(--border);
  }}
  ul.action-list li:last-child {{ border-bottom:none; }}
  ul.action-list span {{ color:var(--muted); font-size:13px; }}
  .mini-grid {{
    display:grid;
    grid-template-columns:repeat(3, 1fr);
    gap:12px;
    margin-top:14px;
  }}
  .mini {{
    border-radius:18px;
    background:rgba(255,255,255,.96);
    border:1px solid rgba(255,255,255,.28);
    padding:14px;
    box-shadow:0 14px 30px rgba(2,6,23,.14);
  }}
  .mini .k {{ font-size:12px; text-transform:uppercase; color:#475569; font-weight:700; letter-spacing:.06em; }}
  .mini .v {{ margin-top:8px; font-size:28px; font-weight:900; color:#0f172a; }}
  .footnote {{ margin-top:10px; color:var(--muted); font-size:12px; }}
  @media (max-width: 920px) {{
    .hero-grid, .split {{ grid-template-columns:1fr; }}
    .mini-grid {{ grid-template-columns:1fr; }}
    h1 {{ font-size:30px; }}
  }}
</style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="eyebrow">VeriOps Sales Teardown</div>
      <h1>{html.escape(str(payload.get("headline", "")))}</h1>
      <p class="summary-text" style="color:rgba(255,255,255,.88); margin:0;">{html.escape(str(summary.get("executive_summary", "") or "Automated public-docs scan converted into a sales-friendly teardown for follow-up conversations."))}</p>
      <div class="hero-grid">
        <div class="hero-panel">
          <div class="sub">Site</div>
          <div style="font-size:22px; font-weight:700; margin-top:8px;">{site_url or "N/A"}</div>
          <div class="mini-grid">
            <div class="mini">
              <div class="k">Audit Score</div>
              <div class="v">{html.escape(str(score.get("audit_score_0_100", 0)))}</div>
            </div>
            <div class="mini">
              <div class="k">Grade</div>
              <div class="v">{html.escape(str(score.get("grade", "n/a")))}</div>
            </div>
            <div class="mini">
              <div class="k">Monthly Cost Signal</div>
              <div class="v">${html.escape(f"{float(summary.get('estimated_monthly_cost_usd', 0.0) or 0.0):,.0f}")}</div>
            </div>
            <div class="mini">
              <div class="k">Annualized</div>
              <div class="v">${html.escape(f"{float(summary.get('estimated_annual_cost_usd', 0.0) or 0.0):,.0f}")}</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="metrics">
      {cards_html}
    </section>

    <section class="split">
      <div class="surface">
        <h2 class="section-title">What We Found</h2>
        {findings_html}
      </div>
      <div class="surface">
        <h2 class="section-title">Readout Snapshot</h2>
        {bars_html}
        <div class="mini-grid">
          <div class="mini">
            <div class="k">Pages Crawled</div>
            <div class="v">{html.escape(str(summary.get("pages_crawled", 0)))}</div>
          </div>
          <div class="mini">
            <div class="k">Broken Links</div>
            <div class="v">{html.escape(str(summary.get("broken_links_count", 0)))}</div>
          </div>
          <div class="mini">
            <div class="k">Unverified Links</div>
            <div class="v">{html.escape(str(summary.get("unverified_links_count", 0)))}</div>
          </div>
        </div>
      </div>
    </section>

    <section class="split">
      <div class="surface">
        <h2 class="section-title">What I’d Prioritize First</h2>
        <ul class="action-list">
          {actions_html}
        </ul>
      </div>
      <div class="surface">
        <h2 class="section-title">Automation Layer To Add First</h2>
        <ul class="clean">
          {automation_html}
        </ul>
      </div>
    </section>

    {price_comparison_html}

    {expense_breakdown_html}

    {strengths_section_html}
  </div>
</body>
</html>
"""


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
        <tr><td>Operational cost</td><td>${impact['monthly_cost_usd']}</td></tr>
        <tr><td>Revenue at risk</td><td>${impact.get('revenue_risk_usd', 0)}</td></tr>
        <tr><td>Potential customers lost</td><td>{impact.get('potential_customers_lost', 0)}</td></tr>
        <tr><td>Total monthly signal</td><td>${impact.get('total_signal_usd', impact['monthly_cost_usd'])}</td></tr>
      </table>
      <p class="foot">Per-finding totals (low/base/high): remediation ${findings_totals.get('remediation_cost_usd_low_total', 0)} / ${findings_totals.get('remediation_cost_usd_base_total', 0)} / ${findings_totals.get('remediation_cost_usd_high_total', 0)}, monthly loss ${findings_totals.get('monthly_loss_usd_low_total', 0)} / ${findings_totals.get('monthly_loss_usd_base_total', 0)} / ${findings_totals.get('monthly_loss_usd_high_total', 0)}. Per-finding monthly losses are allocated shares of the driver-based cost model and sum to its quality-attributable portion; the manual-upkeep baseline is shown separately in the cost-signal breakdown.</p>
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
    parser.add_argument(
        "--pipeline-monthly-price-usd",
        type=float,
        default=float(os.environ.get("VERIOPS_PIPELINE_MONTHLY_PRICE_USD", "0") or 0),
        help=(
            "Your pipeline's monthly price for this prospect. When set and lower than the "
            "estimated monthly docs cost, the teardown shows a price-vs-cost comparison strip."
        ),
    )
    parser.add_argument(
        "--assumptions-json",
        default="",
        help=(
            "Cost-model assumptions JSON. Pick a scale preset from "
            "config/impact_assumptions/{startup,midmarket,enterprise}.json or pass the "
            "prospect's own numbers. Defaults to the (deliberately conservative) startup profile."
        ),
    )
    parser.add_argument("--auto-run-smoke", action="store_true")
    parser.add_argument("--json-output", default="reports/audit_scorecard.json")
    parser.add_argument("--html-output", default="reports/audit_scorecard.html")
    parser.add_argument("--public-audit-json", default="")
    parser.add_argument("--public-broken-links-json", default="")
    parser.add_argument("--llm-summary-json", default="")
    parser.add_argument("--sales-json-output", default="")
    parser.add_argument("--sales-html-output", default="")
    parser.add_argument("--sales-pdf-output", default="")
    parser.add_argument("--skip-sales-pdf", action="store_true")
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    reports_dir = Path(args.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    public_audit_path = _resolve_optional_report_path(args.public_audit_json)
    public_audit = _read_json(public_audit_path) if public_audit_path else {}

    kpis = {
        "api_coverage": _api_coverage_metrics(docs_dir, Path(args.spec_path)),
        "example_reliability": _examples_reliability_metrics(reports_dir, docs_dir, bool(args.auto_run_smoke)),
        "freshness": _freshness_metrics(docs_dir, int(args.stale_days)),
        "drift": _drift_metrics(reports_dir),
        "layer_completeness": _layer_completeness_metrics(docs_dir, Path(args.policy_pack) if args.policy_pack else None),
        "retrieval_quality": _retrieval_metrics(reports_dir),
        "terminology": _terminology_metrics(docs_dir, Path(args.glossary_path), reports_dir),
    }
    if public_audit:
        kpis = _merge_kpis_with_public_audit(kpis, public_audit)
    assumptions = _load_assumptions(Path(args.assumptions_json) if str(args.assumptions_json).strip() else None)
    findings = _build_findings(kpis, assumptions)
    business_impact = _business_impact(kpis, assumptions)
    _allocate_finding_monthly_losses(findings, kpis, business_impact)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_mode": "external_public_audit_bundle" if public_audit else "repo_local_docs",
        "score": _overall_score(kpis),
        "kpis": kpis,
        "business_impact": business_impact,
        "pipeline_monthly_price_usd": float(getattr(args, "pipeline_monthly_price_usd", 0.0) or 0.0),
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

    broken_links_path = _resolve_optional_report_path(args.public_broken_links_json)
    llm_summary_path = _resolve_optional_report_path(args.llm_summary_json)
    sales_json_out = (
        Path(args.sales_json_output)
        if str(args.sales_json_output).strip()
        else _default_sales_output_path(json_out, DEFAULT_SALES_JSON_FILENAME)
    )
    sales_html_out = (
        Path(args.sales_html_output)
        if str(args.sales_html_output).strip()
        else _default_sales_output_path(html_out, DEFAULT_SALES_HTML_FILENAME)
    )
    sales_pdf_out = (
        Path(args.sales_pdf_output)
        if str(args.sales_pdf_output).strip()
        else _default_sales_output_path(html_out, DEFAULT_SALES_PDF_FILENAME)
    )
    sales_json_out.parent.mkdir(parents=True, exist_ok=True)
    sales_html_out.parent.mkdir(parents=True, exist_ok=True)
    sales_pdf_out.parent.mkdir(parents=True, exist_ok=True)

    sales_payload = _build_sales_teardown_payload(
        payload,
        public_audit=_read_json(public_audit_path) if public_audit_path is not None else {},
        broken_links=_read_json(broken_links_path) if broken_links_path is not None else {},
        llm_summary=_read_json(llm_summary_path) if llm_summary_path is not None else {},
    )
    sales_json_out.write_text(json.dumps(sales_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    sales_html_out.write_text(_build_sales_teardown_html(sales_payload), encoding="utf-8")
    if not bool(args.skip_sales_pdf):
        ok, message = _render_html_to_pdf_with_browser(sales_html_out, sales_pdf_out)
        if ok:
            print(f"[ok] sales teardown PDF: {sales_pdf_out}")
        else:
            print(f"[warn] sales teardown PDF generation failed: {message}")

    print(f"[ok] audit scorecard JSON: {json_out}")
    print(f"[ok] audit scorecard HTML: {html_out}")
    print(f"[ok] sales teardown JSON: {sales_json_out}")
    print(f"[ok] sales teardown HTML: {sales_html_out}")
    print(
        "[ok] summary: "
        f"score={payload['score']['audit_score_0_100']} "
        f"api_coverage={kpis['api_coverage']['coverage_pct']}% "
        f"example_reliability={kpis['example_reliability']['example_reliability_pct']}%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

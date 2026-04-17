#!/usr/bin/env python3
"""Detect high-risk knowledge contradictions before retrieval indexing."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

SENTENCE_SPLIT_RE = re.compile(r"[.!?]\s+|\n+")
WORD_RE = re.compile(r"[a-z0-9_]+", re.IGNORECASE)
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
    "you",
    "your",
}

ENV_PORT_RE = re.compile(r"\b([A-Z][A-Z0-9_]*PORT)\b[^\n]{0,40}?(?:=|:)\s*([0-9]{2,5})")
PORT_RE = re.compile(r"\b(?:port|listen(?:ing)?\s+on(?:\s+port)?|default\s+port)\b[^\n]{0,40}?([0-9]{2,5})\b", re.IGNORECASE)
VERSION_RE = re.compile(r"\b(?:api\s+version|version)\b[^\n]{0,24}?\bv?([0-9]+\.[0-9]+(?:\.[0-9]+)?)\b", re.IGNORECASE)
TIMEOUT_RE = re.compile(
    r"\b(?:timeout|time-out|ttl|replay\s+window)\b[^\n]{0,40}?([0-9]+(?:\.[0-9]+)?)\s*(ms|milliseconds?|s|sec|seconds?|m|min|minutes?|h|hr|hours?)\b",
    re.IGNORECASE,
)
RATE_LIMIT_RE = re.compile(
    r"\b([0-9]+(?:\.[0-9]+)?)\s*(?:requests?|reqs?)\s*(?:/|per)\s*(second|sec|minute|min|hour|hr)\b",
    re.IGNORECASE,
)
PAYLOAD_RE = re.compile(
    r"\b(?:max(?:imum)?\s+payload(?:\s+size)?|payload\s+size\s+limit)\b[^\n]{0,40}?([0-9]+(?:\.[0-9]+)?)\s*(kb|mb|gb|bytes?)\b",
    re.IGNORECASE,
)

CRITICAL_TYPES = {"port", "version", "timeout", "rate_limit", "payload_size"}


def _parse_iso8601(value: str) -> datetime | None:
    raw = str(value).strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _read_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _tokenize(text: str) -> list[str]:
    return [tok.lower() for tok in WORD_RE.findall(text) if tok and tok.lower() not in STOPWORDS]


def _cosine_similarity(a: str, b: str) -> float:
    left = Counter(_tokenize(a))
    right = Counter(_tokenize(b))
    if not left or not right:
        return 0.0
    dot = sum(float(left[key]) * float(right.get(key, 0.0)) for key in left)
    if dot <= 0.0:
        return 0.0
    left_norm = math.sqrt(sum(float(v) ** 2 for v in left.values()))
    right_norm = math.sqrt(sum(float(v) ** 2 for v in right.values()))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


def _normalize_topic(module: dict[str, Any]) -> str:
    semantic = module.get("semantic", {}) if isinstance(module.get("semantic"), dict) else {}
    metadata = module.get("metadata", {}) if isinstance(module.get("metadata"), dict) else {}
    topic = (
        str(semantic.get("topic", "")).strip()
        or str(metadata.get("heading", "")).strip()
        or str(module.get("title", "")).strip()
        or str(module.get("id", "")).strip()
    )
    tokens = [t for t in _tokenize(topic) if t]
    return "-".join(tokens[:8]) or "general"


def _normalize_seconds(value: float, unit: str) -> float:
    key = unit.lower()
    if key in {"ms", "millisecond", "milliseconds"}:
        return value / 1000.0
    if key in {"s", "sec", "second", "seconds"}:
        return value
    if key in {"m", "min", "minute", "minutes"}:
        return value * 60.0
    if key in {"h", "hr", "hour", "hours"}:
        return value * 3600.0
    return value


def _normalize_bytes(value: float, unit: str) -> float:
    key = unit.lower()
    if key == "kb":
        return value * 1024.0
    if key == "mb":
        return value * 1024.0 * 1024.0
    if key == "gb":
        return value * 1024.0 * 1024.0 * 1024.0
    return value


def _normalize_requests_per_minute(value: float, unit: str) -> float:
    key = unit.lower()
    if key in {"second", "sec"}:
        return value * 60.0
    if key in {"hour", "hr"}:
        return value / 60.0
    return value


def _extract_claims(module: dict[str, Any]) -> list[dict[str, Any]]:
    content = module.get("content", {}) if isinstance(module.get("content"), dict) else {}
    text = str(content.get("docs_markdown", "")).strip()
    if not text:
        return []
    topic = _normalize_topic(module)
    module_id = str(module.get("id", "")).strip()
    metadata = module.get("metadata", {}) if isinstance(module.get("metadata"), dict) else {}
    source_path = str(metadata.get("source_path", "")).strip() or str(module.get("source_file", "")).strip()
    claims: list[dict[str, Any]] = []

    for sentence in SENTENCE_SPLIT_RE.split(text):
        line = sentence.strip()
        if len(line) < 12:
            continue

        for match in ENV_PORT_RE.finditer(line):
            env_name = str(match.group(1)).strip().lower()
            port = str(int(match.group(2)))
            claims.append(
                {
                    "type": "port",
                    "scope_key": f"{topic}:port:{env_name}",
                    "value": port,
                    "value_display": port,
                    "module_id": module_id,
                    "source_path": source_path,
                    "evidence": line,
                }
            )
        for match in PORT_RE.finditer(line):
            port = str(int(match.group(1)))
            claims.append(
                {
                    "type": "port",
                    "scope_key": f"{topic}:port:default",
                    "value": port,
                    "value_display": port,
                    "module_id": module_id,
                    "source_path": source_path,
                    "evidence": line,
                }
            )
        for match in VERSION_RE.finditer(line):
            version = str(match.group(1)).strip().lower().lstrip("v")
            claims.append(
                {
                    "type": "version",
                    "scope_key": f"{topic}:version:default",
                    "value": version,
                    "value_display": version,
                    "module_id": module_id,
                    "source_path": source_path,
                    "evidence": line,
                }
            )
        for match in TIMEOUT_RE.finditer(line):
            raw_value = float(match.group(1))
            unit = str(match.group(2)).strip().lower()
            seconds = _normalize_seconds(raw_value, unit)
            claims.append(
                {
                    "type": "timeout",
                    "scope_key": f"{topic}:timeout:default",
                    "value": f"{seconds:.6f}",
                    "value_display": f"{raw_value:g} {unit}",
                    "module_id": module_id,
                    "source_path": source_path,
                    "evidence": line,
                }
            )
        for match in RATE_LIMIT_RE.finditer(line):
            raw_value = float(match.group(1))
            unit = str(match.group(2)).strip().lower()
            rpm = _normalize_requests_per_minute(raw_value, unit)
            claims.append(
                {
                    "type": "rate_limit",
                    "scope_key": f"{topic}:rate_limit:default",
                    "value": f"{rpm:.6f}",
                    "value_display": f"{raw_value:g} req/{unit}",
                    "module_id": module_id,
                    "source_path": source_path,
                    "evidence": line,
                }
            )
        for match in PAYLOAD_RE.finditer(line):
            raw_value = float(match.group(1))
            unit = str(match.group(2)).strip().lower()
            size_bytes = _normalize_bytes(raw_value, unit)
            claims.append(
                {
                    "type": "payload_size",
                    "scope_key": f"{topic}:payload_size:default",
                    "value": f"{size_bytes:.6f}",
                    "value_display": f"{raw_value:g} {unit}",
                    "module_id": module_id,
                    "source_path": source_path,
                    "evidence": line,
                }
            )
    return claims


def _build_contradiction(
    *,
    issue_id: int,
    scope_key: str,
    claim_type: str,
    claims: list[dict[str, Any]],
    min_similarity: float,
) -> dict[str, Any] | None:
    values: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for claim in claims:
        values[str(claim.get("value", ""))].append(claim)
    if len(values) <= 1:
        return None

    similarity = 0.0
    value_keys = list(values.keys())
    for idx, left_key in enumerate(value_keys):
        for right_key in value_keys[idx + 1 :]:
            for left_claim in values[left_key]:
                for right_claim in values[right_key]:
                    score = _cosine_similarity(str(left_claim.get("evidence", "")), str(right_claim.get("evidence", "")))
                    if score > similarity:
                        similarity = score

    severity = "critical" if claim_type in CRITICAL_TYPES and similarity >= min_similarity else "warning"
    module_ids = sorted({str(item.get("module_id", "")) for item in claims if str(item.get("module_id", "")).strip()})
    sources = sorted({str(item.get("source_path", "")) for item in claims if str(item.get("source_path", "")).strip()})
    value_items = []
    for normalized, entries in values.items():
        value_items.append(
            {
                "normalized": normalized,
                "display": sorted({str(e.get("value_display", normalized)) for e in entries})[0],
                "module_ids": sorted({str(e.get("module_id", "")) for e in entries if str(e.get("module_id", "")).strip()}),
                "sources": sorted({str(e.get("source_path", "")) for e in entries if str(e.get("source_path", "")).strip()}),
                "examples": [str(e.get("evidence", ""))[:220] for e in entries[:2]],
            }
        )
    value_items.sort(key=lambda item: item["normalized"])

    return {
        "id": f"contradiction-{issue_id}",
        "claim_type": claim_type,
        "scope_key": scope_key,
        "severity": severity,
        "similarity_max": round(similarity, 4),
        "module_ids": module_ids,
        "sources": sources,
        "values": value_items,
        "recommendation": (
            "Resolve to a single source of truth and regenerate retrieval index."
            if severity == "critical"
            else "Review context and align docs if values refer to the same runtime behavior."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect contradictory claims before RAG indexing")
    parser.add_argument("--modules-dir", default="knowledge_modules")
    parser.add_argument("--report", default="reports/rag_contradictions_report.json")
    parser.add_argument("--stale-days", type=int, default=180)
    parser.add_argument("--min-similarity", type=float, default=0.35)
    parser.add_argument("--fail-on-critical", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    modules_dir = Path(args.modules_dir).resolve()
    report_path = Path(args.report).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)

    if not modules_dir.exists():
        raise FileNotFoundError(f"Modules directory not found: {modules_dir}")

    modules: list[dict[str, Any]] = []
    for path in sorted(modules_dir.glob("*.yml")):
        payload = _read_yaml(path)
        if not payload:
            continue
        payload["source_file"] = str(path)
        modules.append(payload)

    active_modules = [m for m in modules if str(m.get("status", "active")).strip().lower() == "active"]
    claims: list[dict[str, Any]] = []
    for module in active_modules:
        claims.extend(_extract_claims(module))

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for claim in claims:
        key = (str(claim.get("type", "")), str(claim.get("scope_key", "")))
        grouped[key].append(claim)

    contradictions: list[dict[str, Any]] = []
    issue_id = 1
    for (claim_type, scope_key), group_claims in sorted(grouped.items(), key=lambda item: item[0]):
        issue = _build_contradiction(
            issue_id=issue_id,
            scope_key=scope_key,
            claim_type=claim_type,
            claims=group_claims,
            min_similarity=float(max(0.0, args.min_similarity)),
        )
        if issue is None:
            continue
        contradictions.append(issue)
        issue_id += 1

    now = datetime.now(timezone.utc)
    stale_candidates: list[dict[str, Any]] = []
    stale_days = max(1, int(args.stale_days))
    for module in active_modules:
        metadata = module.get("metadata", {}) if isinstance(module.get("metadata"), dict) else {}
        updated_at = _parse_iso8601(str(metadata.get("updated_at", "")).strip())
        last_verified = _parse_iso8601(str(module.get("last_verified", "")).strip())
        baseline = updated_at or last_verified
        if baseline is None:
            continue
        age_days = int((now - baseline).total_seconds() // 86400)
        if age_days > stale_days:
            stale_candidates.append(
                {
                    "module_id": str(module.get("id", "")),
                    "source_path": str(metadata.get("source_path", "")),
                    "updated_at": str(metadata.get("updated_at", "")),
                    "last_verified": str(module.get("last_verified", "")),
                    "age_days": age_days,
                }
            )

    critical_count = sum(1 for issue in contradictions if str(issue.get("severity")) == "critical")
    warning_count = sum(1 for issue in contradictions if str(issue.get("severity")) == "warning")
    critical_module_ids = sorted(
        {
            module_id
            for issue in contradictions
            if str(issue.get("severity")) == "critical"
            for module_id in issue.get("module_ids", [])
            if str(module_id).strip()
        }
    )
    status = "ok"
    if critical_count > 0:
        status = "critical"
    elif warning_count > 0 or stale_candidates:
        status = "warning"

    report = {
        "status": status,
        "generated_at": now.isoformat(),
        "modules_dir": str(modules_dir),
        "modules_scanned": len(modules),
        "active_modules_scanned": len(active_modules),
        "claims_extracted": len(claims),
        "groups_checked": len(grouped),
        "contradictions": contradictions,
        "critical_module_ids": critical_module_ids,
        "stale_candidates": sorted(stale_candidates, key=lambda item: int(item.get("age_days", 0)), reverse=True),
        "summary": {
            "critical_contradictions": critical_count,
            "warning_contradictions": warning_count,
            "stale_candidates": len(stale_candidates),
        },
    }
    report_path.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    print(
        "[rag-contradictions] "
        f"status={status} critical={critical_count} warning={warning_count} "
        f"stale_candidates={len(stale_candidates)} report={report_path}"
    )
    if args.fail_on_critical and critical_count > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

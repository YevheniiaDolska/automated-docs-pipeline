"""RAG runtime utilities for live retrieval, ACL/RBAC, and observability."""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOKEN_PATTERN = re.compile(r"[a-z0-9]{2,}", flags=re.IGNORECASE)


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_PATTERN.findall(text or "")}


def _score_token_overlap(query: str, record: dict[str, Any]) -> float:
    q_tokens = _tokenize(query)
    if not q_tokens:
        return 0.0
    haystack = " ".join(
        [
            str(record.get("title", "")),
            str(record.get("summary", "")),
            str(record.get("docs_excerpt", "")),
            str(record.get("assistant_excerpt", "")),
            " ".join(str(v) for v in record.get("keywords", []) if str(v).strip()),
            str(record.get("topic", "")),
            str(record.get("semantic_intent", "")),
            str(record.get("semantic_audience", "")),
        ]
    )
    d_tokens = _tokenize(haystack)
    if not d_tokens:
        return 0.0
    overlap = len(q_tokens & d_tokens)
    return overlap / max(1.0, (len(q_tokens) * len(d_tokens)) ** 0.5)


def _read_json(path: Path) -> Any:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload


def load_ask_ai_config(repo_root: Path) -> dict[str, Any]:
    cfg_path = repo_root / "config" / "ask-ai.yml"
    if not cfg_path.exists():
        return {
            "enabled": False,
            "require_user_auth": True,
            "allowed_roles": ["admin", "support"],
            "knowledge_index_path": "docs/assets/knowledge-retrieval-index.json",
        }
    try:
        import yaml

        raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    except (ImportError, OSError, ValueError, TypeError):
        raw = {}
    return raw if isinstance(raw, dict) else {}


def load_retrieval_index(repo_root: Path, ask_ai_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    index_path = Path(str(ask_ai_cfg.get("knowledge_index_path", "docs/assets/knowledge-retrieval-index.json")))
    if not index_path.is_absolute():
        index_path = (repo_root / index_path).resolve()
    if not index_path.exists():
        return []
    payload = _read_json(index_path)
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        payload = payload["records"]
    if not isinstance(payload, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in payload:
        if isinstance(item, dict) and str(item.get("id", "")).strip():
            rows.append(item)
    return rows


def infer_user_roles(user: dict[str, Any]) -> set[str]:
    roles = {"user"}
    if bool(user.get("is_superuser", False)):
        roles.update({"admin", "support"})
    tier = str(user.get("tier", "free")).strip().lower()
    if tier in {"business", "enterprise"}:
        roles.update({"support", "analyst"})
    if tier in {"pro", "business", "enterprise"}:
        roles.add("developer")
    return roles


def _record_allowed_by_acl(
    record: dict[str, Any],
    *,
    user_tier: str,
    user_roles: set[str],
    allowed_source_sites: set[str],
) -> bool:
    metadata = record.get("metadata", {}) if isinstance(record.get("metadata"), dict) else {}

    source_site = str(record.get("source_site") or metadata.get("source_site") or "").strip().lower()
    if allowed_source_sites and source_site and source_site not in allowed_source_sites:
        return False

    record_roles: list[str] = []
    if isinstance(record.get("allowed_roles"), list):
        record_roles = [str(v).strip().lower() for v in record.get("allowed_roles", []) if str(v).strip()]
    elif isinstance(metadata.get("allowed_roles"), list):
        record_roles = [str(v).strip().lower() for v in metadata.get("allowed_roles", []) if str(v).strip()]
    if record_roles and user_roles.isdisjoint(set(record_roles)):
        return False

    record_tiers: list[str] = []
    if isinstance(record.get("allowed_tiers"), list):
        record_tiers = [str(v).strip().lower() for v in record.get("allowed_tiers", []) if str(v).strip()]
    elif isinstance(metadata.get("allowed_tiers"), list):
        record_tiers = [str(v).strip().lower() for v in metadata.get("allowed_tiers", []) if str(v).strip()]
    if record_tiers and str(user_tier).strip().lower() not in set(record_tiers):
        return False
    return True


def search_retrieval_index(
    *,
    query: str,
    rows: list[dict[str, Any]],
    user_tier: str,
    user_roles: set[str],
    allowed_source_sites: set[str],
    top_k: int = 5,
) -> tuple[list[dict[str, Any]], int]:
    ranked: list[tuple[float, dict[str, Any]]] = []
    blocked = 0
    for row in rows:
        if not _record_allowed_by_acl(
            row,
            user_tier=user_tier,
            user_roles=user_roles,
            allowed_source_sites=allowed_source_sites,
        ):
            blocked += 1
            continue
        score = _score_token_overlap(query, row)
        if score <= 0:
            continue
        ranked.append((score, row))
    ranked.sort(key=lambda item: (-item[0], str(item[1].get("id", ""))))
    out: list[dict[str, Any]] = []
    for score, row in ranked[: max(1, int(top_k))]:
        out.append(
            {
                "id": row.get("id"),
                "title": row.get("title"),
                "summary": row.get("summary"),
                "score": round(float(score), 6),
                "source_file": row.get("source_file"),
                "url": row.get("url"),
                "version": row.get("version"),
                "source_site": row.get("source_site"),
                "semantic_intent": row.get("semantic_intent"),
                "semantic_audience": row.get("semantic_audience"),
                "keywords": row.get("keywords", []),
                "docs_excerpt": row.get("docs_excerpt", ""),
            }
        )
    return out, blocked


def append_rag_query_metric(
    *,
    telemetry_dir: Path,
    user_id: str,
    tier: str,
    query: str,
    top_k: int,
    hits_count: int,
    blocked_count: int,
    latency_ms: int,
    retrieval_mode: str = "token",
) -> None:
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    out = telemetry_dir / "rag_query_metrics.jsonl"
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "tier": tier,
        "query_chars": len(query or ""),
        "top_k": int(top_k),
        "hits_count": int(hits_count),
        "blocked_count": int(blocked_count),
        "latency_ms": int(latency_ms),
        "retrieval_mode": retrieval_mode,
    }
    with out.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=True) + "\n")


def _percentile(values: list[int], percentile: int) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    idx = int(round((max(0, min(percentile, 100)) / 100.0) * (len(ordered) - 1)))
    return int(ordered[idx])


def load_rag_metrics_snapshot(
    *,
    telemetry_dir: Path,
    reports_dir: Path,
    max_rows: int = 2000,
) -> dict[str, Any]:
    telemetry_file = telemetry_dir / "rag_query_metrics.jsonl"
    rows: list[dict[str, Any]] = []
    if telemetry_file.exists():
        with telemetry_file.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except (json.JSONDecodeError, TypeError, ValueError):
                    continue
                if isinstance(item, dict):
                    rows.append(item)
    if len(rows) > max_rows:
        rows = rows[-max_rows:]

    latencies = [int(r.get("latency_ms", 0) or 0) for r in rows if int(r.get("latency_ms", 0) or 0) >= 0]
    hits = [int(r.get("hits_count", 0) or 0) for r in rows]
    blocked = [int(r.get("blocked_count", 0) or 0) for r in rows]
    no_hit = sum(1 for h in hits if h == 0)

    retrieval_eval = {}
    eval_path = reports_dir / "retrieval_evals_report.json"
    if eval_path.exists():
        try:
            payload = _read_json(eval_path)
            if isinstance(payload, dict):
                retrieval_eval = payload.get("metrics", {}) if isinstance(payload.get("metrics"), dict) else {}
        except (OSError, ValueError, TypeError):
            retrieval_eval = {}

    return {
        "window_rows": len(rows),
        "query_metrics": {
            "latency_p50_ms": _percentile(latencies, 50),
            "latency_p95_ms": _percentile(latencies, 95),
            "latency_p99_ms": _percentile(latencies, 99),
            "avg_hits_per_query": round((sum(hits) / len(hits)), 3) if hits else 0.0,
            "no_hit_rate": round((no_hit / len(hits)), 4) if hits else 0.0,
            "acl_block_avg_per_query": round((sum(blocked) / len(blocked)), 3) if blocked else 0.0,
        },
        "retrieval_eval_metrics": retrieval_eval,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def evaluate_rag_alerts(
    *,
    snapshot: dict[str, Any],
    min_recall: float = 0.50,
    max_hallucination_rate: float = 0.20,
    max_latency_p95_ms: int = 2500,
    max_no_hit_rate: float = 0.35,
) -> list[dict[str, Any]]:
    """Evaluate unified RAG SLO alerts from metrics and retrieval eval outputs."""
    alerts: list[dict[str, Any]] = []
    query_metrics = snapshot.get("query_metrics", {}) if isinstance(snapshot.get("query_metrics"), dict) else {}
    retrieval = (
        snapshot.get("retrieval_eval_metrics", {})
        if isinstance(snapshot.get("retrieval_eval_metrics"), dict)
        else {}
    )
    latency_p95 = query_metrics.get("latency_p95_ms")
    no_hit_rate = query_metrics.get("no_hit_rate")
    recall = retrieval.get("recall_at_k")
    hallucination = retrieval.get("hallucination_rate")

    if isinstance(latency_p95, (int, float)) and float(latency_p95) > float(max_latency_p95_ms):
        alerts.append(
            {
                "code": "RAG_LATENCY_P95_HIGH",
                "value": float(latency_p95),
                "threshold": float(max_latency_p95_ms),
            }
        )
    if isinstance(no_hit_rate, (int, float)) and float(no_hit_rate) > float(max_no_hit_rate):
        alerts.append(
            {
                "code": "RAG_NO_HIT_RATE_HIGH",
                "value": float(no_hit_rate),
                "threshold": float(max_no_hit_rate),
            }
        )
    if isinstance(recall, (int, float)) and float(recall) < float(min_recall):
        alerts.append(
            {
                "code": "RAG_RECALL_LOW",
                "value": float(recall),
                "threshold": float(min_recall),
            }
        )
    if isinstance(hallucination, (int, float)) and float(hallucination) > float(max_hallucination_rate):
        alerts.append(
            {
                "code": "RAG_HALLUCINATION_HIGH",
                "value": float(hallucination),
                "threshold": float(max_hallucination_rate),
            }
        )
    return alerts


def run_reindex_lifecycle(
    *,
    repo_root: Path,
    python_bin: str,
    include_embeddings: bool,
    embeddings_provider: str,
) -> dict[str, Any]:
    import subprocess

    started = time.time()
    script = repo_root / "scripts" / "rag_reindex_lifecycle.py"
    if not script.exists():
        raise FileNotFoundError(f"Missing script: {script}")
    cmd = [
        python_bin,
        str(script),
        "--repo-root",
        str(repo_root),
        "--provider",
        embeddings_provider,
    ]
    if include_embeddings:
        cmd.append("--with-embeddings")
    completed = subprocess.run(
        cmd,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    duration_ms = int((time.time() - started) * 1000)
    if completed.returncode != 0:
        raise RuntimeError(
            "RAG reindex failed: "
            f"rc={completed.returncode}; stdout={completed.stdout[-2000:]}; stderr={completed.stderr[-2000:]}"
        )
    report_path = repo_root / "reports" / "rag_reindex_report.json"
    report_payload: dict[str, Any] = {}
    if report_path.exists():
        try:
            payload = _read_json(report_path)
            if isinstance(payload, dict):
                report_payload = payload
        except (OSError, ValueError, TypeError):
            report_payload = {}
    report_payload["duration_ms"] = duration_ms
    report_payload["provider"] = embeddings_provider
    report_payload["with_embeddings"] = bool(include_embeddings)
    return report_payload


def resolve_embeddings_provider(explicit: str | None = None) -> str:
    value = str(explicit or "").strip().lower()
    if value in {"local", "openai"}:
        return value
    env = os.environ.get("VERIDOC_RAG_EMBED_PROVIDER", "").strip().lower()
    if env in {"local", "openai"}:
        return env
    return "local"

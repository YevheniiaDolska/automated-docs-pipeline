from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG_CORE = ROOT / "packages" / "core"
if str(PKG_CORE) not in sys.path:
    sys.path.insert(0, str(PKG_CORE))


def test_search_retrieval_index_applies_acl() -> None:
    from gitspeak_core.api.rag_runtime import search_retrieval_index

    rows = [
        {
            "id": "a",
            "title": "Configure webhook auth",
            "summary": "How to configure webhook authentication for api",
            "allowed_tiers": ["business", "enterprise"],
            "source_site": "docs.example.com",
        },
        {
            "id": "b",
            "title": "Configure webhook auth quickstart",
            "summary": "Quickstart for webhook authentication",
            "source_site": "docs.example.com",
        },
    ]
    hits, blocked = search_retrieval_index(
        query="configure webhook auth",
        rows=rows,
        user_tier="starter",
        user_roles={"user"},
        allowed_source_sites={"docs.example.com"},
        top_k=5,
    )
    assert blocked == 1
    assert [h["id"] for h in hits] == ["b"]


def test_load_metrics_snapshot_reads_eval_and_logs(tmp_path: Path) -> None:
    from gitspeak_core.api.rag_runtime import load_rag_metrics_snapshot

    telemetry = tmp_path / "telemetry"
    reports = tmp_path / "reports"
    telemetry.mkdir()
    reports.mkdir()
    (telemetry / "rag_query_metrics.jsonl").write_text(
        "\n".join(
            [
                json.dumps({"latency_ms": 100, "hits_count": 3, "blocked_count": 0}),
                json.dumps({"latency_ms": 400, "hits_count": 0, "blocked_count": 2}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (reports / "retrieval_evals_report.json").write_text(
        json.dumps(
            {
                "metrics": {
                    "precision_at_k": 0.82,
                    "recall_at_k": 0.77,
                    "hallucination_rate": 0.09,
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )
    snapshot = load_rag_metrics_snapshot(telemetry_dir=telemetry, reports_dir=reports)
    assert snapshot["window_rows"] == 2
    assert snapshot["query_metrics"]["latency_p95_ms"] >= 100
    assert snapshot["retrieval_eval_metrics"]["precision_at_k"] == 0.82


def test_resolve_embeddings_provider_defaults_to_local(monkeypatch) -> None:
    from gitspeak_core.api.rag_runtime import resolve_embeddings_provider

    monkeypatch.delenv("VERIDOC_RAG_EMBED_PROVIDER", raising=False)
    assert resolve_embeddings_provider(None) == "local"
    monkeypatch.setenv("VERIDOC_RAG_EMBED_PROVIDER", "openai")
    assert resolve_embeddings_provider(None) == "openai"
    assert resolve_embeddings_provider("local") == "local"


def test_evaluate_rag_alerts_detects_threshold_breaches() -> None:
    from gitspeak_core.api.rag_runtime import evaluate_rag_alerts

    snapshot = {
        "query_metrics": {
            "latency_p95_ms": 5000,
            "no_hit_rate": 0.8,
        },
        "retrieval_eval_metrics": {
            "recall_at_k": 0.1,
            "hallucination_rate": 0.9,
        },
    }
    alerts = evaluate_rag_alerts(
        snapshot=snapshot,
        min_recall=0.5,
        max_hallucination_rate=0.2,
        max_latency_p95_ms=2500,
        max_no_hit_rate=0.35,
    )
    codes = {a.get("code") for a in alerts}
    assert "RAG_LATENCY_P95_HIGH" in codes
    assert "RAG_NO_HIT_RATE_HIGH" in codes
    assert "RAG_RECALL_LOW" in codes
    assert "RAG_HALLUCINATION_HIGH" in codes

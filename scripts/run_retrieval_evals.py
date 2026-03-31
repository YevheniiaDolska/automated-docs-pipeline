#!/usr/bin/env python3
"""Run retrieval quality evals on the knowledge retrieval index."""

from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import os

import yaml

TOKEN_PATTERN = re.compile(r"[a-z0-9]{2,}", flags=re.IGNORECASE)

try:
    import numpy as np

    _HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore[assignment]
    _HAS_NUMPY = False

try:
    import faiss as _faiss_mod

    _HAS_FAISS = True
except ImportError:
    _faiss_mod = None  # type: ignore[assignment]
    _HAS_FAISS = False

try:
    from sentence_transformers import CrossEncoder as _CrossEncoder

    _HAS_CROSS_ENCODER = True
except ImportError:
    _CrossEncoder = None  # type: ignore[assignment]
    _HAS_CROSS_ENCODER = False

VALID_MODES = ("token", "semantic", "hybrid", "hybrid+rerank", "all")


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_PATTERN.findall(text or "")}


def _load_index(index_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Retrieval index must be a JSON list: {index_path}")
    rows: list[dict[str, Any]] = []
    for item in payload:
        if isinstance(item, dict) and str(item.get("id", "")).strip():
            rows.append(item)
    return rows


def _load_dataset(dataset_path: Path) -> list[dict[str, Any]]:
    payload = yaml.safe_load(dataset_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Eval dataset must be a YAML list: {dataset_path}")
    rows: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        query = str(item.get("query", "")).strip()
        expected = [str(v).strip() for v in item.get("expected_ids", []) if str(v).strip()]
        if query and expected:
            rows.append({"query": query, "expected_ids": expected})
    return rows


def _build_auto_dataset(index_rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in index_rows[:limit]:
        module_id = str(item.get("id", "")).strip()
        title = str(item.get("title", "")).strip()
        summary = str(item.get("summary", "")).strip()
        intents = " ".join(str(v).strip() for v in item.get("intents", []) if str(v).strip())
        audiences = " ".join(str(v).strip() for v in item.get("audiences", []) if str(v).strip())
        if not module_id:
            continue
        # Build a richer query to reduce ambiguity for common titles
        # such as "... (Part N)" chunks.
        fragments = [title, summary, intents, audiences]
        query = " ".join(part for part in fragments if part).strip()
        if not query:
            query = module_id
        rows.append({"query": query, "expected_ids": [module_id]})
    return rows


def _score_query(query: str, doc: dict[str, Any]) -> float:
    query_tokens = _tokenize(query)
    doc_text = " ".join(
        [
            str(doc.get("title", "")),
            str(doc.get("summary", "")),
            str(doc.get("docs_excerpt", "")),
            str(doc.get("assistant_excerpt", "")),
            " ".join(str(v) for v in doc.get("intents", [])),
            " ".join(str(v) for v in doc.get("audiences", [])),
        ]
    )
    doc_tokens = _tokenize(doc_text)
    if not query_tokens or not doc_tokens:
        return 0.0
    overlap = len(query_tokens & doc_tokens)
    return overlap / math.sqrt(len(query_tokens) * len(doc_tokens))


def _search_token(index_rows: list[dict[str, Any]], query: str, top_k: int) -> list[str]:
    scored = []
    for row in index_rows:
        score = _score_query(query, row)
        scored.append((score, str(row.get("id", "")).strip()))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [doc_id for _, doc_id in scored[:top_k] if doc_id]


# Keep backwards-compatible alias
_search = _search_token


def _load_faiss_assets(index_dir: Path) -> tuple[Any, list[dict[str, Any]]] | None:
    """Load FAISS index and metadata from the same directory as the retrieval index."""
    if not _HAS_FAISS or not _HAS_NUMPY:
        return None
    faiss_path = index_dir / "retrieval.faiss"
    metadata_path = index_dir / "retrieval-metadata.json"
    if not faiss_path.exists() or not metadata_path.exists():
        return None
    index = _faiss_mod.read_index(str(faiss_path))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(metadata, list):
        return None
    return index, metadata


def _embed_query(text: str, api_key: str, model: str, base_url: str) -> Any:
    """Embed a query for semantic search."""
    import httpx

    url = f"{base_url.rstrip('/')}/embeddings"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = httpx.post(url, headers=headers, json={"input": text, "model": model}, timeout=30.0)
    response.raise_for_status()
    vec = np.asarray(response.json()["data"][0]["embedding"], dtype=np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


def _search_semantic(
    faiss_index: Any,
    faiss_metadata: list[dict[str, Any]],
    query: str,
    top_k: int,
    api_key: str,
    model: str,
    base_url: str,
) -> list[str]:
    """Search using FAISS semantic similarity."""
    vec = _embed_query(query, api_key, model, base_url)
    q = vec.reshape(1, -1)
    k = min(top_k, faiss_index.ntotal)
    if k <= 0:
        return []
    scores, indices = faiss_index.search(q, k)
    results: list[str] = []
    for i in range(k):
        idx = int(indices[0][i])
        if 0 <= idx < len(faiss_metadata):
            doc_id = str(faiss_metadata[idx].get("id", "")).strip()
            if doc_id:
                results.append(doc_id)
    return results


# ---------------------------------------------------------------------------
# Hybrid search (RRF) for evals
# ---------------------------------------------------------------------------

def _reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[str]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores, key=lambda d: scores[d], reverse=True)


def _search_hybrid(
    index_rows: list[dict[str, Any]],
    faiss_index: Any,
    faiss_metadata: list[dict[str, Any]],
    query: str,
    top_k: int,
    api_key: str,
    model: str,
    base_url: str,
    rrf_k: int = 60,
) -> list[str]:
    """RRF fusion of token and semantic search."""
    token_ids = _search_token(index_rows, query, top_k)
    semantic_ids = _search_semantic(faiss_index, faiss_metadata, query, top_k, api_key, model, base_url)
    fused = _reciprocal_rank_fusion([token_ids, semantic_ids], k=rrf_k)
    return fused[:top_k]


# ---------------------------------------------------------------------------
# Hybrid + rerank for evals
# ---------------------------------------------------------------------------

_EVAL_RERANKER: Any = None
_EVAL_RERANKER_MODEL: str = ""


def _search_hybrid_rerank(
    index_rows: list[dict[str, Any]],
    faiss_index: Any,
    faiss_metadata: list[dict[str, Any]],
    query: str,
    top_k: int,
    api_key: str,
    model: str,
    base_url: str,
    rrf_k: int = 60,
    rerank_candidates: int = 20,
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
) -> list[str]:
    """Hybrid search with cross-encoder reranking."""
    global _EVAL_RERANKER, _EVAL_RERANKER_MODEL  # noqa: PLW0603

    if not _HAS_CROSS_ENCODER:
        return _search_hybrid(
            index_rows, faiss_index, faiss_metadata, query, top_k,
            api_key, model, base_url, rrf_k,
        )

    # Get more candidates for reranking
    token_ids = _search_token(index_rows, query, rerank_candidates)
    semantic_ids = _search_semantic(
        faiss_index, faiss_metadata, query, rerank_candidates, api_key, model, base_url,
    )
    fused = _reciprocal_rank_fusion([token_ids, semantic_ids], k=rrf_k)
    candidate_ids = fused[:rerank_candidates]

    # Build id->module lookup
    id_to_module: dict[str, dict[str, Any]] = {}
    for m in faiss_metadata:
        mid = str(m.get("id", "")).strip()
        if mid:
            id_to_module[mid] = m
    for m in index_rows:
        mid = str(m.get("id", "")).strip()
        if mid and mid not in id_to_module:
            id_to_module[mid] = m

    candidates = [id_to_module[cid] for cid in candidate_ids if cid in id_to_module]
    if not candidates:
        return candidate_ids[:top_k]

    # Load reranker
    if _EVAL_RERANKER is None or _EVAL_RERANKER_MODEL != rerank_model:
        _EVAL_RERANKER = _CrossEncoder(rerank_model)
        _EVAL_RERANKER_MODEL = rerank_model

    pairs = []
    for c in candidates:
        doc_text = " ".join(
            filter(None, [
                str(c.get("title", "")),
                str(c.get("summary", "")),
                str(c.get("assistant_excerpt", "")),
            ])
        )
        pairs.append((query, doc_text))

    scores = _EVAL_RERANKER.predict(pairs)
    scored = sorted(zip(scores, candidates), key=lambda x: float(x[0]), reverse=True)
    return [str(c.get("id", "")) for _, c in scored[:top_k]]


# ---------------------------------------------------------------------------
# Evaluation core
# ---------------------------------------------------------------------------

def evaluate(
    index_rows: list[dict[str, Any]],
    dataset_rows: list[dict[str, Any]],
    top_k: int,
    search_fn: Any | None = None,
) -> dict[str, Any]:
    if not dataset_rows:
        return {
            "status": "error",
            "message": "no eval samples",
            "precision_at_k": 0.0,
            "recall_at_k": 0.0,
            "hallucination_rate": 1.0,
            "samples": [],
        }

    precision_sum = 0.0
    recall_sum = 0.0
    hallucinated = 0
    retrieved_total = 0
    sample_rows: list[dict[str, Any]] = []
    corpus_ids = {str(row.get("id", "")).strip() for row in index_rows}

    for row in dataset_rows:
        query = row["query"]
        expected = {value for value in row["expected_ids"] if value}
        retrieved = search_fn(query, top_k) if search_fn else _search_token(index_rows, query, top_k=top_k)
        retrieved_set = set(retrieved)
        hits = len(expected & retrieved_set)
        precision = hits / max(len(retrieved), 1)
        recall = hits / max(len(expected), 1)
        precision_sum += precision
        recall_sum += recall
        retrieved_total += len(retrieved)
        hallucinated += len([item for item in retrieved if item not in corpus_ids])
        sample_rows.append(
            {
                "query": query,
                "expected_ids": sorted(expected),
                "retrieved_ids": retrieved,
                "hits": hits,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
            }
        )

    precision_at_k = precision_sum / len(dataset_rows)
    recall_at_k = recall_sum / len(dataset_rows)
    hallucination_rate = hallucinated / max(retrieved_total, 1)
    status = "ok"
    return {
        "status": status,
        "precision_at_k": round(precision_at_k, 4),
        "recall_at_k": round(recall_at_k, 4),
        "hallucination_rate": round(hallucination_rate, 4),
        "sample_count": len(dataset_rows),
        "top_k": top_k,
        "samples": sample_rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run retrieval quality evals")
    parser.add_argument("--index", default="docs/assets/knowledge-retrieval-index.json")
    parser.add_argument("--dataset", default="")
    parser.add_argument("--dataset-out", default="reports/retrieval_eval_dataset.generated.yml")
    parser.add_argument("--report", default="reports/retrieval_evals_report.json")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--min-precision", type=float, default=0.5)
    parser.add_argument("--min-recall", type=float, default=0.5)
    parser.add_argument("--max-hallucination-rate", type=float, default=0.5)
    parser.add_argument("--auto-generate-dataset", action="store_true")
    parser.add_argument("--auto-samples", type=int, default=25)
    parser.add_argument("--use-embeddings", action="store_true", help="Use FAISS semantic search instead of token scoring")
    parser.add_argument("--embedding-model", default="text-embedding-3-small")
    parser.add_argument(
        "--mode",
        default="token",
        choices=VALID_MODES,
        help="Search mode: token, semantic, hybrid, hybrid+rerank, or all (runs comparison)",
    )
    parser.add_argument("--rrf-k", type=int, default=60, help="RRF k parameter for hybrid search")
    parser.add_argument("--rerank-candidates", type=int, default=20, help="Candidate count for reranking")
    parser.add_argument(
        "--rerank-model",
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        help="Cross-encoder model for reranking",
    )
    return parser.parse_args()


def _run_single_mode(
    mode: str,
    index_rows: list[dict[str, Any]],
    dataset_rows: list[dict[str, Any]],
    top_k: int,
    api_key: str,
    embedding_model: str,
    base_url: str,
    faiss_assets: tuple[Any, list[dict[str, Any]]] | None,
    rrf_k: int,
    rerank_candidates: int,
    rerank_model: str,
) -> dict[str, Any]:
    """Run evaluation for a single search mode."""
    search_fn = None

    if mode == "token":
        search_fn = lambda q, k: _search_token(index_rows, q, k)  # noqa: E731

    elif mode == "semantic":
        if not api_key or faiss_assets is None:
            return {"status": "error", "message": "semantic mode requires OPENAI_API_KEY and FAISS index"}
        fi, fm = faiss_assets
        search_fn = lambda q, k: _search_semantic(fi, fm, q, k, api_key, embedding_model, base_url)  # noqa: E731

    elif mode == "hybrid":
        if not api_key or faiss_assets is None:
            return {"status": "error", "message": "hybrid mode requires OPENAI_API_KEY and FAISS index"}
        fi, fm = faiss_assets
        search_fn = lambda q, k: _search_hybrid(  # noqa: E731
            index_rows, fi, fm, q, k, api_key, embedding_model, base_url, rrf_k,
        )

    elif mode == "hybrid+rerank":
        if not api_key or faiss_assets is None:
            return {"status": "error", "message": "hybrid+rerank mode requires OPENAI_API_KEY and FAISS index"}
        if not _HAS_CROSS_ENCODER:
            return {"status": "error", "message": "hybrid+rerank requires sentence-transformers"}
        fi, fm = faiss_assets
        search_fn = lambda q, k: _search_hybrid_rerank(  # noqa: E731
            index_rows, fi, fm, q, k, api_key, embedding_model, base_url,
            rrf_k, rerank_candidates, rerank_model,
        )

    return evaluate(index_rows=index_rows, dataset_rows=dataset_rows, top_k=top_k, search_fn=search_fn)


def main() -> int:
    args = parse_args()
    index_path = Path(args.index)
    if not index_path.exists():
        raise FileNotFoundError(f"Retrieval index not found: {index_path}")

    index_rows = _load_index(index_path)
    dataset_path = Path(args.dataset) if args.dataset else None

    if args.auto_generate_dataset:
        dataset_rows = _build_auto_dataset(index_rows, limit=max(args.auto_samples, 1))
        generated_path = Path(args.dataset_out)
        generated_path.parent.mkdir(parents=True, exist_ok=True)
        generated_path.write_text(yaml.safe_dump(dataset_rows, sort_keys=False), encoding="utf-8")
        dataset_path = generated_path
    elif dataset_path and dataset_path.exists():
        dataset_rows = _load_dataset(dataset_path)
    else:
        dataset_rows = []

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    faiss_assets = _load_faiss_assets(index_path.parent) if api_key else None

    # Handle legacy --use-embeddings flag (maps to semantic mode)
    mode = args.mode
    if args.use_embeddings and mode == "token":
        mode = "semantic"

    if mode == "all":
        modes_to_run = ["token", "semantic", "hybrid", "hybrid+rerank"]
        comparison: dict[str, Any] = {}
        for m in modes_to_run:
            print(f"Running {m} mode...")
            result = _run_single_mode(
                m, index_rows, dataset_rows, max(args.top_k, 1),
                api_key, args.embedding_model, base_url, faiss_assets,
                args.rrf_k, args.rerank_candidates, args.rerank_model,
            )
            comparison[m] = {
                "status": result.get("status", "error"),
                "precision_at_k": result.get("precision_at_k", 0.0),
                "recall_at_k": result.get("recall_at_k", 0.0),
                "hallucination_rate": result.get("hallucination_rate", 0.0),
                "sample_count": result.get("sample_count", 0),
            }
            p = comparison[m]["precision_at_k"]
            r = comparison[m]["recall_at_k"]
            print(f"  {m}: precision={p} recall={r}")

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "ok",
            "index_path": str(index_path),
            "dataset_path": str(dataset_path) if dataset_path else "",
            "top_k": args.top_k,
            "comparison": comparison,
        }
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

        print(f"\nComparison report saved: {report_path}")
        print("\nSummary:")
        for m, data in comparison.items():
            print(f"  {m:20s}  precision={data['precision_at_k']:.4f}  recall={data['recall_at_k']:.4f}")
        return 0

    # Single mode
    metrics = _run_single_mode(
        mode, index_rows, dataset_rows, max(args.top_k, 1),
        api_key, args.embedding_model, base_url, faiss_assets,
        args.rrf_k, args.rerank_candidates, args.rerank_model,
    )

    if metrics.get("status") == "error":
        print(f"Error: {metrics.get('message', 'unknown')}")
        return 1

    breaches: list[str] = []
    if metrics["precision_at_k"] < args.min_precision:
        breaches.append(f"precision_at_k={metrics['precision_at_k']} < {args.min_precision}")
    if metrics["recall_at_k"] < args.min_recall:
        breaches.append(f"recall_at_k={metrics['recall_at_k']} < {args.min_recall}")
    if metrics["hallucination_rate"] > args.max_hallucination_rate:
        breaches.append(
            f"hallucination_rate={metrics['hallucination_rate']} > {args.max_hallucination_rate}"
        )

    status = "ok" if not breaches else "breach"
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "mode": mode,
        "index_path": str(index_path),
        "dataset_path": str(dataset_path) if dataset_path else "",
        "thresholds": {
            "min_precision": args.min_precision,
            "min_recall": args.min_recall,
            "max_hallucination_rate": args.max_hallucination_rate,
        },
        "metrics": metrics,
        "breaches": breaches,
    }

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print(
        f"Retrieval evals ({mode}): precision@{metrics['top_k']}={metrics['precision_at_k']} "
        f"recall@{metrics['top_k']}={metrics['recall_at_k']} "
        f"hallucination_rate={metrics['hallucination_rate']}"
    )
    if breaches:
        for breach in breaches:
            print(f"breach: {breach}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

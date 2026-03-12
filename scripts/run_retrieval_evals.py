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

import yaml

TOKEN_PATTERN = re.compile(r"[a-z0-9]{2,}", flags=re.IGNORECASE)


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
        if not module_id:
            continue
        query = title or summary[:80] or module_id
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


def _search(index_rows: list[dict[str, Any]], query: str, top_k: int) -> list[str]:
    scored = []
    for row in index_rows:
        score = _score_query(query, row)
        scored.append((score, str(row.get("id", "")).strip()))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [doc_id for _, doc_id in scored[:top_k] if doc_id]


def evaluate(
    index_rows: list[dict[str, Any]],
    dataset_rows: list[dict[str, Any]],
    top_k: int,
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
        retrieved = _search(index_rows, query, top_k=top_k)
        retrieved_set = set(retrieved)
        hits = len(expected & retrieved_set)
        precision = hits / max(len(retrieved), 1)
        recall = hits / max(len(expected), 1)
        precision_sum += precision
        recall_sum += recall
        retrieved_total += len(retrieved)
        hallucinated += len([item for item in retrieved if item not in expected or item not in corpus_ids])
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    index_path = Path(args.index)
    if not index_path.exists():
        raise FileNotFoundError(f"Retrieval index not found: {index_path}")

    index_rows = _load_index(index_path)
    dataset_path = Path(args.dataset) if args.dataset else None

    if dataset_path and dataset_path.exists():
        dataset_rows = _load_dataset(dataset_path)
    elif args.auto_generate_dataset:
        dataset_rows = _build_auto_dataset(index_rows, limit=max(args.auto_samples, 1))
        generated_path = Path(args.dataset_out)
        generated_path.parent.mkdir(parents=True, exist_ok=True)
        generated_path.write_text(yaml.safe_dump(dataset_rows, sort_keys=False), encoding="utf-8")
        dataset_path = generated_path
    else:
        dataset_rows = []

    metrics = evaluate(index_rows=index_rows, dataset_rows=dataset_rows, top_k=max(args.top_k, 1))
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
        f"Retrieval evals: precision@{metrics['top_k']}={metrics['precision_at_k']} "
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

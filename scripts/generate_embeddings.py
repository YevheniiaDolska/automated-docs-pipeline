#!/usr/bin/env python3
"""Build FAISS index from knowledge retrieval index using OpenAI embeddings."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np

try:
    import faiss
except ImportError:
    faiss = None  # type: ignore[assignment]

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]


def _load_index(index_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "records" in payload:
        payload = payload["records"]
    if not isinstance(payload, list):
        raise ValueError(f"Retrieval index must be a JSON list: {index_path}")
    rows: list[dict[str, Any]] = []
    for item in payload:
        if isinstance(item, dict) and str(item.get("id", "")).strip():
            rows.append(item)
    return rows


def _build_text(module: dict[str, Any]) -> str:
    parts = [
        str(module.get("title", "")),
        str(module.get("summary", "")),
        str(module.get("assistant_excerpt", "")),
        " ".join(str(v) for v in module.get("intents", [])),
    ]
    return " ".join(p for p in parts if p.strip())


def _embed_batch(
    texts: list[str],
    api_key: str,
    model: str,
    base_url: str,
    batch_size: int,
) -> list[list[float]]:
    if httpx is None:
        raise ImportError("httpx is required: pip install httpx>=0.27.0")
    url = f"{base_url.rstrip('/')}/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    all_embeddings: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        payload = {"input": batch, "model": model}
        response = httpx.post(url, headers=headers, json=payload, timeout=60.0)
        response.raise_for_status()
        data = response.json()
        batch_embeddings = sorted(data["data"], key=lambda x: x["index"])
        for item in batch_embeddings:
            all_embeddings.append(item["embedding"])
        print(f"  Embedded {min(start + batch_size, len(texts))}/{len(texts)} modules")
    return all_embeddings


def _build_faiss_index(embeddings: list[list[float]]) -> Any:
    if faiss is None:
        raise ImportError("faiss-cpu is required: pip install faiss-cpu>=1.7.4")
    matrix = np.asarray(embeddings, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    matrix = matrix / norms
    dim = matrix.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(matrix)
    return index


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate FAISS embeddings index")
    parser.add_argument(
        "--index",
        default="docs/assets/knowledge-retrieval-index.json",
        help="Path to knowledge retrieval index JSON",
    )
    parser.add_argument(
        "--output-dir",
        default="docs/assets",
        help="Directory for output .faiss and .json files",
    )
    parser.add_argument(
        "--model",
        default="text-embedding-3-small",
        help="OpenAI embedding model name",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for embedding API calls",
    )
    parser.add_argument(
        "--chunk",
        action="store_true",
        help="Enable token-aware chunking before embedding",
    )
    parser.add_argument(
        "--chunk-max-tokens",
        type=int,
        default=750,
        help="Maximum tokens per chunk (default: 750)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=100,
        help="Overlap tokens between consecutive chunks (default: 100)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("Warning: OPENAI_API_KEY not set. Skipping embedding generation.")
        return 0

    if faiss is None:
        print("Warning: faiss-cpu not installed. Skipping embedding generation.")
        return 0

    if httpx is None:
        print("Warning: httpx not installed. Skipping embedding generation.")
        return 0

    index_path = Path(args.index)
    if not index_path.exists():
        raise FileNotFoundError(f"Knowledge retrieval index not found: {index_path}")

    modules = _load_index(index_path)
    if not modules:
        print("No modules found in retrieval index.")
        return 0

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    if args.chunk:
        from scripts.chunker import chunk_module

        all_chunks: list[dict[str, Any]] = []
        for m in modules:
            all_chunks.extend(
                chunk_module(m, max_tokens=args.chunk_max_tokens, overlap_tokens=args.chunk_overlap)
            )
        print(
            f"Chunked {len(modules)} modules into {len(all_chunks)} chunks "
            f"(max_tokens={args.chunk_max_tokens}, overlap={args.chunk_overlap})"
        )
        texts = [c["text"] for c in all_chunks]
        embeddings = _embed_batch(texts, api_key, args.model, base_url, args.batch_size)

        print("Building FAISS index...")
        index = _build_faiss_index(embeddings)

        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        faiss_path = output_dir / "retrieval.faiss"
        metadata_path = output_dir / "retrieval-metadata.json"
        faiss.write_index(index, str(faiss_path))

        metadata = []
        for c in all_chunks:
            metadata.append({
                "id": c["chunk_id"],
                "chunk_id": c["chunk_id"],
                "parent_id": c["parent_id"],
                "chunk_index": c["chunk_index"],
                "title": c["title"],
                "source_file": c["source_file"],
                "text": c["text"],
            })
        metadata_path.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        print(f"FAISS index saved: {faiss_path} ({index.ntotal} vectors, dim={index.d})")
        print(f"Metadata saved: {metadata_path} ({len(metadata)} chunk entries)")
        return 0

    print(f"Generating embeddings for {len(modules)} modules using {args.model}...")
    texts = [_build_text(m) for m in modules]
    embeddings = _embed_batch(texts, api_key, args.model, base_url, args.batch_size)

    print("Building FAISS index...")
    index = _build_faiss_index(embeddings)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    faiss_path = output_dir / "retrieval.faiss"
    metadata_path = output_dir / "retrieval-metadata.json"

    faiss.write_index(index, str(faiss_path))

    metadata = []
    for m in modules:
        metadata.append({
            "id": m.get("id"),
            "title": m.get("title"),
            "summary": m.get("summary"),
            "assistant_excerpt": m.get("assistant_excerpt"),
            "source_file": m.get("source_file"),
            "intents": m.get("intents", []),
        })
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    print(f"FAISS index saved: {faiss_path} ({index.ntotal} vectors, dim={index.d})")
    print(f"Metadata saved: {metadata_path} ({len(metadata)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

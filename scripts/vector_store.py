"""FAISS vector store wrapper for semantic retrieval."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

try:
    import faiss
except ImportError:
    faiss = None  # type: ignore[assignment]

try:
    from sentence_transformers import CrossEncoder as _CrossEncoder

    _HAS_CROSS_ENCODER = True
except ImportError:
    _CrossEncoder = None  # type: ignore[assignment]
    _HAS_CROSS_ENCODER = False

_RERANKER_INSTANCE: Any = None
_RERANKER_MODEL_NAME: str = ""


def load_index(
    faiss_path: str | Path,
    metadata_path: str | Path,
) -> tuple[Any, list[dict[str, Any]]]:
    """Load a FAISS index and its metadata sidecar.

    Returns (faiss_index, metadata_list).
    """
    if faiss is None:
        raise ImportError("faiss-cpu is required: pip install faiss-cpu>=1.7.4")
    index = faiss.read_index(str(faiss_path))
    metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
    if not isinstance(metadata, list):
        raise ValueError(f"Metadata sidecar must be a JSON list: {metadata_path}")
    return index, metadata


def search(
    index: Any,
    metadata: list[dict[str, Any]],
    query_embedding: np.ndarray,
    top_k: int = 5,
) -> list[tuple[dict[str, Any], float]]:
    """Search the FAISS index and return (module_dict, score) pairs."""
    if index.ntotal == 0:
        return []
    query = np.asarray(query_embedding, dtype=np.float32)
    if query.ndim == 1:
        query = query.reshape(1, -1)
    k = min(top_k, index.ntotal)
    scores, indices = index.search(query, k)
    results: list[tuple[dict[str, Any], float]] = []
    for i in range(k):
        idx = int(indices[0][i])
        if idx < 0 or idx >= len(metadata):
            continue
        results.append((metadata[idx], float(scores[0][i])))
    return results


def load_reranker(model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> Any:
    """Load a cross-encoder reranker model (lazy singleton)."""
    global _RERANKER_INSTANCE, _RERANKER_MODEL_NAME  # noqa: PLW0603
    if not _HAS_CROSS_ENCODER:
        raise ImportError("sentence-transformers is required: pip install sentence-transformers>=2.2.0")
    if _RERANKER_INSTANCE is None or _RERANKER_MODEL_NAME != model_name:
        _RERANKER_INSTANCE = _CrossEncoder(model_name)
        _RERANKER_MODEL_NAME = model_name
    return _RERANKER_INSTANCE


def rerank(
    query: str,
    candidates: list[dict[str, Any]],
    top_n: int = 5,
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
) -> list[dict[str, Any]]:
    """Rerank candidate modules using a cross-encoder model.

    Each candidate is scored by pairing the query with a concatenation of the
    candidate's title, summary, and assistant_excerpt.
    """
    if not candidates:
        return []
    reranker = load_reranker(model_name)
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
    scores = reranker.predict(pairs)
    scored = sorted(zip(scores, candidates), key=lambda x: float(x[0]), reverse=True)
    return [c for _, c in scored[:top_n]]


def embed_query(
    text: str,
    api_key: str,
    model: str = "text-embedding-3-small",
    base_url: str = "https://api.openai.com/v1",
) -> np.ndarray:
    """Embed a single text query via the OpenAI embeddings API.

    Uses httpx to avoid adding the openai SDK as a dependency.
    """
    import httpx

    url = f"{base_url.rstrip('/')}/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"input": text, "model": model}
    response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
    response.raise_for_status()
    data = response.json()
    embedding = data["data"][0]["embedding"]
    vec = np.asarray(embedding, dtype=np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec

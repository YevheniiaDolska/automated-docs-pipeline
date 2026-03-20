"""Knowledge retrieval helpers for Ask AI runtime."""

from __future__ import annotations

import glob
import json
import os
import time
from pathlib import Path
from typing import Any

try:
    import faiss
    import numpy as np

    _HAS_FAISS = True
except ImportError:
    faiss = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]
    _HAS_FAISS = False

try:
    from sentence_transformers import CrossEncoder as _CrossEncoder

    _HAS_CROSS_ENCODER = True
except ImportError:
    _CrossEncoder = None  # type: ignore[assignment]
    _HAS_CROSS_ENCODER = False

# ---------------------------------------------------------------------------
# Embedding cache
# ---------------------------------------------------------------------------

_EMBED_CACHE: dict[str, tuple[float, Any]] = {}


def _get_cached_embedding(text: str, ttl: int) -> Any:
    entry = _EMBED_CACHE.get(text)
    if entry is None:
        return None
    ts, vec = entry
    if time.time() - ts > ttl:
        del _EMBED_CACHE[text]
        return None
    return vec


def _put_cached_embedding(text: str, vec: Any, max_size: int) -> None:
    if len(_EMBED_CACHE) >= max_size:
        oldest_key = min(_EMBED_CACHE, key=lambda k: _EMBED_CACHE[k][0])
        del _EMBED_CACHE[oldest_key]
    _EMBED_CACHE[text] = (time.time(), vec)


def _embed_query_cached(
    text: str,
    cache_enabled: bool = True,
    cache_ttl: int = 3600,
    cache_max_size: int = 512,
) -> Any:
    """Embed a query, using the in-memory cache when enabled."""
    if cache_enabled:
        cached = _get_cached_embedding(text, cache_ttl)
        if cached is not None:
            return cached
    vec = _embed_query(text)
    if vec is not None and cache_enabled:
        _put_cached_embedding(text, vec, cache_max_size)
    return vec


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_knowledge_index(path: str) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    payload = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    return []


def load_assistant_bundles(glob_pattern: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for file_path in sorted(glob.glob(glob_pattern)):
        p = Path(file_path)
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            items.append(payload)
    return items


def load_faiss_index(
    faiss_path: str,
    metadata_path: str,
) -> tuple[Any, list[dict[str, Any]]] | None:
    """Load FAISS index and metadata. Returns None if files missing or faiss unavailable."""
    if not _HAS_FAISS:
        return None
    fp = Path(faiss_path)
    mp = Path(metadata_path)
    if not fp.exists() or not mp.exists():
        return None
    try:
        index = faiss.read_index(str(fp))
        metadata = json.loads(mp.read_text(encoding="utf-8"))
        if not isinstance(metadata, list):
            return None
        return index, metadata
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

def _embed_query(text: str) -> Any:
    """Embed a query using the OpenAI embeddings API."""
    import httpx

    api_key = os.getenv("ASK_AI_PROVIDER_API_KEY", "").strip()
    if not api_key:
        return None
    model = os.getenv("ASK_AI_EMBEDDING_MODEL", "text-embedding-3-small")
    base_url = os.getenv("ASK_AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    url = f"{base_url}/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"input": text, "model": model}
    response = httpx.post(url, headers=headers, json=payload, timeout=15.0)
    response.raise_for_status()
    data = response.json()
    vec = np.asarray(data["data"][0]["embedding"], dtype=np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


# ---------------------------------------------------------------------------
# HyDE (Hypothetical Document Embeddings)
# ---------------------------------------------------------------------------

def _generate_hypothetical_document(
    question: str,
    api_key: str,
    model: str = "gpt-4.1-mini",
    base_url: str = "https://api.openai.com/v1",
) -> str | None:
    """Generate a hypothetical documentation passage that answers the question."""
    import httpx

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "temperature": 0.0,
        "max_tokens": 300,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Write a 100-200 word documentation passage that answers "
                    "the following question. Write as if this passage is from "
                    "official product documentation."
                ),
            },
            {"role": "user", "content": question},
        ],
    }
    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=20.0)
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            return None
        content = choices[0].get("message", {}).get("content", "")
        return content.strip() or None
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# Cross-encoder reranking (runtime-local copy)
# ---------------------------------------------------------------------------

_RERANKER_INSTANCE: Any = None
_RERANKER_MODEL_NAME: str = ""


def _load_reranker(model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> Any:
    global _RERANKER_INSTANCE, _RERANKER_MODEL_NAME  # noqa: PLW0603
    if not _HAS_CROSS_ENCODER:
        raise ImportError("sentence-transformers is required: pip install sentence-transformers>=2.2.0")
    if _RERANKER_INSTANCE is None or _RERANKER_MODEL_NAME != model_name:
        _RERANKER_INSTANCE = _CrossEncoder(model_name)
        _RERANKER_MODEL_NAME = model_name
    return _RERANKER_INSTANCE


def _rerank(
    query: str,
    candidates: list[dict[str, Any]],
    top_n: int = 5,
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
) -> list[dict[str, Any]]:
    if not candidates:
        return []
    reranker = _load_reranker(model_name)
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


# ---------------------------------------------------------------------------
# Semantic search
# ---------------------------------------------------------------------------

def rank_modules_semantic(
    question: str,
    faiss_index: Any,
    faiss_metadata: list[dict[str, Any]],
    limit: int,
    hyde_enabled: bool = False,
    hyde_model: str = "gpt-4.1-mini",
    cache_enabled: bool = True,
    cache_ttl: int = 3600,
    cache_max_size: int = 512,
) -> list[dict[str, Any]]:
    """Rank modules using FAISS semantic search, optionally with HyDE."""
    embed_text = question

    if hyde_enabled:
        api_key = os.getenv("ASK_AI_PROVIDER_API_KEY", "").strip()
        base_url = os.getenv("ASK_AI_BASE_URL", "https://api.openai.com/v1")
        if api_key:
            hypo = _generate_hypothetical_document(question, api_key, hyde_model, base_url)
            if hypo:
                embed_text = hypo

    try:
        query_vec = _embed_query_cached(
            embed_text,
            cache_enabled=cache_enabled,
            cache_ttl=cache_ttl,
            cache_max_size=cache_max_size,
        )
    except Exception:  # noqa: BLE001
        return []
    if query_vec is None:
        return []
    query = query_vec.reshape(1, -1)
    k = min(limit, faiss_index.ntotal)
    if k <= 0:
        return []
    scores, indices = faiss_index.search(query, k)
    results: list[dict[str, Any]] = []
    for i in range(k):
        idx = int(indices[0][i])
        if 0 <= idx < len(faiss_metadata):
            results.append(faiss_metadata[idx])
    return results


# ---------------------------------------------------------------------------
# Token-overlap search
# ---------------------------------------------------------------------------

def rank_modules(question: str, modules: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    q = question.lower()

    def score(module: dict[str, Any]) -> int:
        tokens = [
            str(module.get("title", "")).lower(),
            str(module.get("summary", "")).lower(),
            str(module.get("assistant_excerpt", "")).lower(),
            " ".join(str(v).lower() for v in module.get("intents", [])),
            " ".join(str(v).lower() for v in module.get("channels", [])),
        ]
        text = " ".join(tokens)
        return sum(1 for part in q.split() if part and part in text)

    ranked = sorted(modules, key=lambda m: (score(m), int(m.get("priority", 0))), reverse=True)
    return ranked[: max(limit, 1)]


# ---------------------------------------------------------------------------
# Hybrid search (RRF)
# ---------------------------------------------------------------------------

def _reciprocal_rank_fusion(
    rankings: list[list[str]],
    k: int = 60,
) -> list[str]:
    """Merge multiple ranked ID lists using Reciprocal Rank Fusion."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores, key=lambda d: scores[d], reverse=True)


def rank_modules_hybrid(
    question: str,
    modules: list[dict[str, Any]],
    faiss_index: Any,
    faiss_metadata: list[dict[str, Any]],
    candidate_limit: int,
    rrf_k: int = 60,
    hyde_enabled: bool = False,
    hyde_model: str = "gpt-4.1-mini",
    cache_enabled: bool = True,
    cache_ttl: int = 3600,
    cache_max_size: int = 512,
) -> list[dict[str, Any]]:
    """Rank modules using RRF fusion of semantic and token-overlap rankings."""
    semantic_results = rank_modules_semantic(
        question, faiss_index, faiss_metadata, candidate_limit,
        hyde_enabled=hyde_enabled, hyde_model=hyde_model,
        cache_enabled=cache_enabled, cache_ttl=cache_ttl,
        cache_max_size=cache_max_size,
    )
    semantic_ids = [str(m.get("id", "")) for m in semantic_results]

    token_results = rank_modules(question, modules, candidate_limit)
    token_ids = [str(m.get("id", "")) for m in token_results]

    fused_ids = _reciprocal_rank_fusion([semantic_ids, token_ids], k=rrf_k)

    id_to_module: dict[str, dict[str, Any]] = {}
    for m in semantic_results:
        mid = str(m.get("id", ""))
        if mid:
            id_to_module[mid] = m
    for m in token_results:
        mid = str(m.get("id", ""))
        if mid and mid not in id_to_module:
            id_to_module[mid] = m

    deduped: list[dict[str, Any]] = []
    for doc_id in fused_ids:
        if doc_id in id_to_module:
            deduped.append(id_to_module[doc_id])
    return deduped[:candidate_limit]


# ---------------------------------------------------------------------------
# Chunk deduplication
# ---------------------------------------------------------------------------

def _deduplicate_chunks(modules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate chunks that share the same parent_id, keeping only the first."""
    seen_parents: set[str] = set()
    result: list[dict[str, Any]] = []
    for m in modules:
        parent_id = m.get("parent_id")
        if parent_id:
            if parent_id in seen_parents:
                continue
            seen_parents.add(parent_id)
        result.append(m)
    return result


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def build_context(
    question: str,
    modules: list[dict[str, Any]],
    max_context_modules: int,
    faiss_data: tuple[Any, list[dict[str, Any]]] | None = None,
    rerank_enabled: bool = False,
    rerank_candidates: int = 20,
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    hybrid_enabled: bool = False,
    rrf_k: int = 60,
    hyde_enabled: bool = False,
    hyde_model: str = "gpt-4.1-mini",
    cache_enabled: bool = True,
    cache_ttl: int = 3600,
    cache_max_size: int = 512,
) -> dict[str, Any]:
    top: list[dict[str, Any]] = []
    fetch_limit = rerank_candidates if rerank_enabled else max_context_modules

    if faiss_data is not None:
        faiss_index, faiss_metadata = faiss_data
        if hybrid_enabled:
            top = rank_modules_hybrid(
                question, modules, faiss_index, faiss_metadata, fetch_limit,
                rrf_k=rrf_k,
                hyde_enabled=hyde_enabled, hyde_model=hyde_model,
                cache_enabled=cache_enabled, cache_ttl=cache_ttl,
                cache_max_size=cache_max_size,
            )
        else:
            top = rank_modules_semantic(
                question, faiss_index, faiss_metadata, fetch_limit,
                hyde_enabled=hyde_enabled, hyde_model=hyde_model,
                cache_enabled=cache_enabled, cache_ttl=cache_ttl,
                cache_max_size=cache_max_size,
            )

    # Deduplicate chunks that share the same parent module
    if top:
        top = _deduplicate_chunks(top)

    # Cross-encoder reranking
    if rerank_enabled and top and len(top) > max_context_modules and _HAS_CROSS_ENCODER:
        try:
            top = _rerank(question, top, top_n=max_context_modules, model_name=rerank_model)
        except Exception:  # noqa: BLE001
            top = top[:max_context_modules]
    elif top:
        top = top[:max_context_modules]

    # Fallback to token overlap
    if not top:
        top = rank_modules(question, modules, max_context_modules)

    return {
        "question": question,
        "modules": [
            {
                "id": m.get("id"),
                "title": m.get("title"),
                "summary": m.get("summary"),
                "assistant_excerpt": m.get("assistant_excerpt"),
                "source_file": m.get("source_file"),
            }
            for m in top
        ],
    }

"""Knowledge retrieval helpers for Ask AI runtime."""

from __future__ import annotations

import glob
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from app.secrets import resolve_provider_api_key

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
_WORD_RE = re.compile(r"[a-z0-9_]+", re.IGNORECASE)
_ENTITY_TOKEN_RE = re.compile(r"(?:/[a-z0-9._~!$&'()*+,;=:@-]+)+|v\d+(?:\.\d+)*|[a-z0-9._-]+", re.IGNORECASE)
_STOPWORDS = {
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
    except (Exception,):  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

def _embed_query(text: str) -> Any:
    """Embed a query using the OpenAI embeddings API."""
    import httpx

    provider = os.getenv("ASK_AI_PROVIDER", "openai").strip().lower()
    api_key = resolve_provider_api_key(provider)
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
    except (Exception,):  # noqa: BLE001
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
        provider = os.getenv("ASK_AI_PROVIDER", "openai").strip().lower()
        api_key = resolve_provider_api_key(provider)
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
    except (Exception,):  # noqa: BLE001
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
# Query decomposition and entity-first retrieval
# ---------------------------------------------------------------------------

def decompose_query(question: str, max_parts: int = 3) -> list[str]:
    q = str(question or "").strip()
    if not q:
        return []
    parts: list[str] = []
    lowered = q.lower()
    separators = [" and ", " then ", " vs ", " versus ", ";", ","]
    split_candidates = [q]
    for sep in separators:
        expanded: list[str] = []
        for chunk in split_candidates:
            expanded.extend([item.strip() for item in chunk.split(sep) if item.strip()])
        split_candidates = expanded if len(expanded) > 1 else split_candidates
    for chunk in split_candidates:
        normalized = " ".join(chunk.split())
        if normalized and normalized.lower() not in {p.lower() for p in parts}:
            parts.append(normalized)
        if len(parts) >= max_parts:
            break
    if any(token in lowered for token in ("between", "difference", "compare", "changed", "change")) and len(parts) == 1:
        parts.append(f"key changes in {q}")
    return parts[:max_parts]


def extract_entities(question: str, max_entities: int = 12) -> list[str]:
    entities: list[str] = []
    for match in _ENTITY_TOKEN_RE.findall(question or ""):
        token = str(match).strip().lower()
        if len(token) < 2 or token in _STOPWORDS:
            continue
        if token.isdigit():
            continue
        if token not in entities:
            entities.append(token)
        if len(entities) >= max_entities:
            break
    return entities


def rank_modules_entity_first(
    question: str,
    modules: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    entities = extract_entities(question)
    if not entities:
        return []

    def score(module: dict[str, Any]) -> float:
        haystack = " ".join(
            [
                str(module.get("title", "")),
                str(module.get("summary", "")),
                str(module.get("assistant_excerpt", "")),
                str(module.get("heading", "")),
                str(module.get("url", "")),
                " ".join(str(x) for x in module.get("intents", [])),
                " ".join(str(x) for x in module.get("tags", [])),
                " ".join(str(x) for x in module.get("keywords", [])),
            ]
        ).lower()
        points = 0.0
        for ent in entities:
            if not ent:
                continue
            if ent in str(module.get("url", "")).lower():
                points += 3.0
            elif ent in str(module.get("title", "")).lower():
                points += 2.5
            elif ent in haystack:
                points += 1.0
        points += max(0.0, min(int(module.get("priority", 0) or 0), 5) * 0.15)
        return points

    scored = sorted(modules, key=lambda m: score(m), reverse=True)
    return [m for m in scored if score(m) > 0][: max(limit, 1)]


# ---------------------------------------------------------------------------
# Vectorless structural search
# ---------------------------------------------------------------------------

def _question_terms(question: str) -> list[str]:
    return [tok.lower() for tok in _WORD_RE.findall(question or "") if tok and tok.lower() not in _STOPWORDS]


def _module_scalar_fields(module: dict[str, Any]) -> list[str]:
    return [
        str(module.get("title", "")).lower(),
        str(module.get("summary", "")).lower(),
        str(module.get("heading", "")).lower(),
        str(module.get("url", "")).lower(),
        str(module.get("topic", "")).lower(),
        str(module.get("semantic_intent", "")).lower(),
        str(module.get("semantic_audience", "")).lower(),
    ]


def _module_list_fields(module: dict[str, Any]) -> list[str]:
    merged: list[str] = []
    for key in ("intents", "channels", "tags", "keywords"):
        value = module.get(key, [])
        if isinstance(value, list):
            merged.extend(str(item).lower() for item in value if str(item).strip())
    return merged


def _vectorless_score(question: str, terms: list[str], module: dict[str, Any]) -> float:
    if not terms:
        return 0.0

    scalars = _module_scalar_fields(module)
    lists = _module_list_fields(module)
    title = scalars[0]
    heading = scalars[2]
    summary = scalars[1]
    assistant_excerpt = str(module.get("assistant_excerpt", "")).lower()
    metadata_blob = " ".join(scalars + lists)

    score = 0.0
    for term in terms:
        if term in heading:
            score += 4.0
        elif term in title:
            score += 3.0
        elif term in lists or term in metadata_blob:
            score += 2.5
        elif term in summary:
            score += 1.5
        elif term in assistant_excerpt:
            score += 1.0

    q = (question or "").lower()
    if any(token in q for token in ("what changed", "change", "changed", "difference", "between", "delta", "vs", "versus")):
        if any(token in metadata_blob for token in ("release", "changelog", "migration", "version", "updated", "changes")):
            score += 5.0
    if any(token in q for token in ("api", "endpoint", "request", "response", "schema", "graphql", "grpc", "asyncapi", "websocket")):
        if any(token in metadata_blob for token in ("api", "reference", "endpoint", "openapi", "graphql", "grpc", "asyncapi", "websocket")):
            score += 4.0
    if any(token in q for token in ("how", "configure", "setup", "install", "enable", "disable")):
        if any(token in metadata_blob for token in ("how-to", "tutorial", "guide", "configure", "setup", "install")):
            score += 4.0

    priority = int(module.get("priority", 0) or 0)
    score += max(0.0, min(priority, 5) * 0.2)
    return score


def rank_modules_vectorless_scored(
    question: str,
    modules: list[dict[str, Any]],
    limit: int,
) -> list[tuple[dict[str, Any], float]]:
    terms = _question_terms(question)
    scored: list[tuple[dict[str, Any], float]] = []
    for module in modules:
        s = _vectorless_score(question, terms, module)
        if s > 0:
            scored.append((module, s))
    scored.sort(key=lambda item: (item[1], int(item[0].get("priority", 0))), reverse=True)
    return scored[: max(limit, 1)]


def _should_use_vectorless_auto(
    question: str,
    modules: list[dict[str, Any]],
    faiss_data: tuple[Any, list[dict[str, Any]]] | None,
) -> bool:
    if faiss_data is None:
        return True
    q = (question or "").lower()
    if any(token in q for token in ("what changed", "difference", "between", "delta", "compare", "versus", "vs")):
        return True
    if any(token in q for token in ("policy", "sla", "slo", "terms", "compliance", "license", "pricing")):
        return True
    if not modules:
        return False
    structured_count = sum(1 for m in modules if str(m.get("heading", "")).strip() and str(m.get("url", "")).strip())
    return (structured_count / max(len(modules), 1)) >= 0.7


# ---------------------------------------------------------------------------
# Graph reranking
# ---------------------------------------------------------------------------

def _module_graph_neighbors(module: dict[str, Any], id_map: dict[str, dict[str, Any]]) -> set[str]:
    neighbors: set[str] = set()
    for dep in module.get("dependencies", []):
        dep_id = str(dep).strip()
        if dep_id and dep_id in id_map:
            neighbors.add(dep_id)
    current_id = str(module.get("id", "")).strip()
    if current_id:
        for mid, other in id_map.items():
            if mid == current_id:
                continue
            deps = {str(item).strip() for item in other.get("dependencies", [])}
            if current_id in deps:
                neighbors.add(mid)
    current_tags = {str(t).strip().lower() for t in module.get("tags", []) if str(t).strip()}
    current_topic = str(module.get("topic", "")).strip().lower()
    for mid, other in id_map.items():
        if mid == current_id:
            continue
        other_tags = {str(t).strip().lower() for t in other.get("tags", []) if str(t).strip()}
        other_topic = str(other.get("topic", "")).strip().lower()
        if current_tags and other_tags and current_tags.intersection(other_tags):
            neighbors.add(mid)
        elif current_topic and other_topic and current_topic == other_topic:
            neighbors.add(mid)
    return neighbors


def graph_rerank_candidates(
    question: str,
    candidates: list[dict[str, Any]],
    all_modules: list[dict[str, Any]],
    top_n: int,
    boost: float = 0.35,
) -> list[dict[str, Any]]:
    if not candidates:
        return []
    id_map: dict[str, dict[str, Any]] = {}
    for module in all_modules:
        mid = str(module.get("id", "")).strip()
        if mid:
            id_map[mid] = module

    seed_scores: dict[str, float] = {}
    entity_hits = set(extract_entities(question))
    for rank, module in enumerate(candidates):
        mid = str(module.get("id", "")).strip()
        if not mid:
            continue
        base = 1.0 / (rank + 1)
        hay = " ".join(
            [
                str(module.get("title", "")),
                str(module.get("summary", "")),
                str(module.get("assistant_excerpt", "")),
                str(module.get("heading", "")),
                str(module.get("url", "")),
            ]
        ).lower()
        entity_boost = sum(1.0 for ent in entity_hits if ent in hay) * 0.15
        seed_scores[mid] = base + entity_boost

    propagated = dict(seed_scores)
    for _ in range(2):
        next_scores = dict(propagated)
        for mid, score in propagated.items():
            module = id_map.get(mid)
            if not module:
                continue
            neighbors = _module_graph_neighbors(module, id_map)
            if not neighbors:
                continue
            share = (score * boost) / max(len(neighbors), 1)
            for neighbor in neighbors:
                if neighbor in next_scores:
                    next_scores[neighbor] = next_scores.get(neighbor, 0.0) + share
        propagated = next_scores

    ranked_ids = sorted(propagated, key=lambda m: propagated[m], reverse=True)
    ranked: list[dict[str, Any]] = []
    for mid in ranked_ids:
        if mid in id_map:
            ranked.append(id_map[mid])
        if len(ranked) >= max(1, top_n):
            break
    return ranked


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
    retrieval_mode: str = "auto",
    vectorless_min_score: float = 2.0,
    graph_rerank_enabled: bool = True,
    graph_rerank_boost: float = 0.35,
    query_decomp_enabled: bool = True,
    entity_first_enabled: bool = True,
) -> dict[str, Any]:
    top: list[dict[str, Any]] = []
    fetch_limit = rerank_candidates if rerank_enabled else max_context_modules
    selected_mode = "token"
    fallback_used = False

    normalized_mode = str(retrieval_mode or "auto").strip().lower()
    queries = [question]
    if query_decomp_enabled:
        for part in decompose_query(question):
            if part and part.lower() not in {q.lower() for q in queries}:
                queries.append(part)
            if len(queries) >= 3:
                break

    combined_rankings: list[list[str]] = []
    id_to_module: dict[str, dict[str, Any]] = {}

    def _capture(items: list[dict[str, Any]]) -> None:
        ids: list[str] = []
        for item in items:
            mid = str(item.get("id", "")).strip()
            if not mid:
                continue
            ids.append(mid)
            id_to_module[mid] = item
        if ids:
            combined_rankings.append(ids)

    for q in queries:
        local_top: list[dict[str, Any]] = []
        local_mode = selected_mode
        local_fallback = False

        if entity_first_enabled:
            entity_candidates = rank_modules_entity_first(q, modules, fetch_limit)
            _capture(entity_candidates)

        if normalized_mode == "vectorless" or (
            normalized_mode == "auto" and _should_use_vectorless_auto(q, modules, faiss_data)
        ):
            local_mode = "vectorless"
            scored_vectorless = rank_modules_vectorless_scored(q, modules, fetch_limit)
            local_top = [item[0] for item in scored_vectorless]
            top_score = float(scored_vectorless[0][1]) if scored_vectorless else 0.0
            if normalized_mode == "auto" and top_score < float(vectorless_min_score):
                local_fallback = True
                local_top = []

        if not local_top and faiss_data is not None and normalized_mode in {"auto", "hybrid", "semantic", "vectorless"}:
            faiss_index, faiss_metadata = faiss_data
            if normalized_mode == "semantic":
                local_mode = "semantic"
                local_top = rank_modules_semantic(
                    q, faiss_index, faiss_metadata, fetch_limit,
                    hyde_enabled=hyde_enabled, hyde_model=hyde_model,
                    cache_enabled=cache_enabled, cache_ttl=cache_ttl,
                    cache_max_size=cache_max_size,
                )
            elif hybrid_enabled and normalized_mode in {"auto", "hybrid", "vectorless"}:
                if local_mode != "vectorless":
                    local_mode = "hybrid"
                local_top = rank_modules_hybrid(
                    q, modules, faiss_index, faiss_metadata, fetch_limit,
                    rrf_k=rrf_k,
                    hyde_enabled=hyde_enabled, hyde_model=hyde_model,
                    cache_enabled=cache_enabled, cache_ttl=cache_ttl,
                    cache_max_size=cache_max_size,
                )
            else:
                local_mode = "semantic"
                local_top = rank_modules_semantic(
                    q, faiss_index, faiss_metadata, fetch_limit,
                    hyde_enabled=hyde_enabled, hyde_model=hyde_model,
                    cache_enabled=cache_enabled, cache_ttl=cache_ttl,
                    cache_max_size=cache_max_size,
                )

        if not local_top:
            local_mode = "token"
            local_top = rank_modules(q, modules, max_context_modules)

        _capture(local_top)
        selected_mode = local_mode
        fallback_used = fallback_used or local_fallback

    if combined_rankings:
        fused_ids = _reciprocal_rank_fusion(combined_rankings, k=rrf_k)
        top = [id_to_module[mid] for mid in fused_ids if mid in id_to_module][:fetch_limit]

    if graph_rerank_enabled and top:
        top = graph_rerank_candidates(
            question,
            candidates=top,
            all_modules=modules,
            top_n=fetch_limit,
            boost=graph_rerank_boost,
        )
        selected_mode = f"{selected_mode}+graph"

    # Deduplicate chunks that share the same parent module
    if top:
        top = _deduplicate_chunks(top)

    # Cross-encoder reranking
    if rerank_enabled and top and len(top) > max_context_modules and _HAS_CROSS_ENCODER:
        try:
            top = _rerank(question, top, top_n=max_context_modules, model_name=rerank_model)
        except (Exception,):  # noqa: BLE001
            top = top[:max_context_modules]
    elif top:
        top = top[:max_context_modules]

    # Fallback to token overlap
    if not top:
        selected_mode = "token"
        top = rank_modules(question, modules, max_context_modules)

    return {
        "question": question,
        "retrieval_mode": selected_mode,
        "retrieval_fallback_used": fallback_used,
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

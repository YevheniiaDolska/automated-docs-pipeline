"""Ask AI runtime API server (optional module)."""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone
import uuid
import os
from pathlib import Path
from typing import Any, AsyncGenerator

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.auth import parse_auth_context, require_runtime_api_key, validate_role
from app.billing_hooks import can_use_ask_ai, verify_webhook_signature
from app.retrieval import build_context, load_assistant_bundles, load_faiss_index, load_knowledge_index
from app.secrets import resolve_provider_api_key

logger = logging.getLogger(__name__)

load_dotenv()


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=4000)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    # Prior turns for multi-turn follow-ups. Only the most recent are used.
    history: list[ChatMessage] = Field(default_factory=list)


class AskResponse(BaseModel):
    answer: str
    citations: list[dict[str, Any]]
    question_id: str = ""
    grounded: bool = True
    warnings: list[str] = Field(default_factory=list)


class FeedbackRequest(BaseModel):
    question_id: str = Field(min_length=1, max_length=64)
    helpful: bool
    comment: str = Field(default="", max_length=2000)


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _load_runtime_config() -> dict[str, Any]:
    provider = os.getenv("ASK_AI_PROVIDER", "openai").strip().lower()
    # Provider-aware default endpoint: local models (Ollama and compatible)
    # default to the local OpenAI-compatible server; everything else to OpenAI.
    base_default = "http://localhost:11434/v1" if provider in {"local", "ollama"} else "https://api.openai.com/v1"
    return {
        "enabled": _bool_env("ASK_AI_ENABLED", True),
        "provider": provider,
        "model": os.getenv("ASK_AI_MODEL", "gpt-4.1-mini"),
        "base_url": os.getenv("ASK_AI_BASE_URL", base_default).rstrip("/"),
        # Local OpenAI-compatible servers (Ollama) need no key; use a sentinel
        # so generation proceeds instead of falling back to the no-key path.
        "provider_api_key": resolve_provider_api_key(provider)
        or ("local" if provider in {"local", "ollama"} else ""),
        "billing_mode": os.getenv("ASK_AI_BILLING_MODE", "disabled"),
        "max_context_modules": int(os.getenv("ASK_AI_MAX_CONTEXT_MODULES", "6")),
        "max_tokens": int(os.getenv("ASK_AI_MAX_TOKENS", "700")),
        "temperature": float(os.getenv("ASK_AI_TEMPERATURE", "0.2")),
        "require_auth": _bool_env("ASK_AI_REQUIRE_AUTH", True),
        "allowed_roles": [
            x.strip() for x in os.getenv("ASK_AI_ALLOWED_ROLES", "admin,support").split(",") if x.strip()
        ],
        "webhook_secret": os.getenv("ASK_AI_WEBHOOK_SECRET", "").strip(),
        "knowledge_index_path": os.getenv("ASK_AI_KNOWLEDGE_INDEX_PATH", "docs/assets/knowledge-retrieval-index.json"),
        "assistant_bundle_glob": os.getenv("ASK_AI_ASSISTANT_BUNDLE_GLOB", "reports/intent-bundles/*-assistant.json"),
        "faiss_index_path": os.getenv("ASK_AI_FAISS_INDEX_PATH", "docs/assets/retrieval.faiss"),
        "faiss_metadata_path": os.getenv("ASK_AI_FAISS_METADATA_PATH", "docs/assets/retrieval-metadata.json"),
        "rerank_enabled": _bool_env("ASK_AI_RERANK_ENABLED", True),
        "rerank_model": os.getenv("ASK_AI_RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"),
        "rerank_candidates": int(os.getenv("ASK_AI_RERANK_CANDIDATES", "20")),
        "hybrid_enabled": _bool_env("ASK_AI_HYBRID_ENABLED", True),
        "rrf_k": int(os.getenv("ASK_AI_RRF_K", "60")),
        "hyde_enabled": _bool_env("ASK_AI_HYDE_ENABLED", True),
        "hyde_model": os.getenv("ASK_AI_HYDE_MODEL", "gpt-4.1-mini"),
        "embed_cache_enabled": _bool_env("ASK_AI_EMBED_CACHE_ENABLED", True),
        "embed_cache_ttl": int(os.getenv("ASK_AI_EMBED_CACHE_TTL", "3600")),
        "embed_cache_max_size": int(os.getenv("ASK_AI_EMBED_CACHE_MAX_SIZE", "512")),
        "usage_log_enabled": _bool_env("ASK_AI_USAGE_LOG_ENABLED", True),
        "usage_log_path": os.getenv("ASK_AI_USAGE_LOG_PATH", "reports/ask_ai_usage.jsonl"),
        "history_max_turns": int(os.getenv("ASK_AI_HISTORY_MAX_TURNS", "6")),
        "rate_limit_per_minute": int(os.getenv("ASK_AI_RATE_LIMIT_PER_USER_PER_MINUTE", "20")),
        "min_confidence": float(os.getenv("ASK_AI_MIN_CONFIDENCE", "0.28")),
        "contradictions_report_path": os.getenv(
            "ASK_AI_CONTRADICTIONS_REPORT_PATH", "reports/rag_contradictions_report.json"
        ),
        "owner_alert_log_path": os.getenv("ASK_AI_OWNER_ALERT_LOG_PATH", "reports/ask_ai_owner_alerts.jsonl"),
        "retrieval_mode": os.getenv("ASK_AI_RETRIEVAL_MODE", "auto").strip().lower(),
        "vectorless_min_score": float(os.getenv("ASK_AI_VECTORLESS_MIN_SCORE", "2.0")),
        "graph_rerank_enabled": _bool_env("ASK_AI_GRAPH_RERANK_ENABLED", True),
        "graph_rerank_boost": float(os.getenv("ASK_AI_GRAPH_RERANK_BOOST", "0.35")),
        "query_decomp_enabled": _bool_env("ASK_AI_QUERY_DECOMP_ENABLED", True),
        "entity_first_enabled": _bool_env("ASK_AI_ENTITY_FIRST_ENABLED", True),
    }


def _append_usage_event(config: dict[str, Any], event: dict[str, Any]) -> None:
    """Append one JSONL usage event. Never lets logging break a request."""
    if not config.get("usage_log_enabled", True):
        return
    try:
        path = Path(str(config.get("usage_log_path", "reports/ask_ai_usage.jsonl")))
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=True) + "\n")
    except OSError as exc:
        logger.warning("Ask AI usage log write failed: %s", exc)


# Sliding-window rate limiter state: identity -> recent request timestamps.
_RATE_STATE: dict[str, list[float]] = {}


def _rate_limit_check(identity: str, limit_per_minute: int) -> None:
    """Enforce a per-identity request budget. Raises HTTP 429 when exceeded.

    Protects the public endpoint (and the provider quota behind it) from abuse.
    A limit of 0 disables the check.
    """
    if limit_per_minute <= 0:
        return
    now = time.time()
    window_start = now - 60.0
    hits = [t for t in _RATE_STATE.get(identity, []) if t >= window_start]
    if len(hits) >= limit_per_minute:
        retry_after = max(1, int(60 - (now - hits[0])))
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please slow down and try again shortly.",
            headers={"Retry-After": str(retry_after)},
        )
    hits.append(now)
    _RATE_STATE[identity] = hits
    # Bound memory: drop identities whose window has fully expired.
    if len(_RATE_STATE) > 4096:
        for key in [k for k, v in _RATE_STATE.items() if not v or v[-1] < window_start]:
            _RATE_STATE.pop(key, None)


def _apply_byok(
    config: dict[str, Any],
    provider_key: str | None,
    provider_base_url: str | None,
    model: str | None,
) -> dict[str, Any]:
    """Return an effective config that bills the caller's own provider key.

    When the caller sends X-Provider-Key, generation uses that key (and optional
    base URL and model), so each user pays for their own queries. In
    bring-your-own-key billing mode a caller key is required.
    """
    if not (provider_key and provider_key.strip()):
        if config.get("billing_mode") == "bring-your-own-key":
            raise HTTPException(
                status_code=402,
                detail="This deployment requires your own provider API key. Send it in the X-Provider-Key header.",
            )
        return config
    effective = dict(config)
    effective["provider_api_key"] = provider_key.strip()
    if provider_base_url and provider_base_url.strip():
        effective["base_url"] = provider_base_url.strip().rstrip("/")
    if model and model.strip():
        effective["model"] = model.strip()
    return effective


_LOW_CONFIDENCE_TEXT = (
    "I do not have enough reliable context to answer this safely. This topic may "
    "need documentation added or updated. Try rephrasing your question."
)
_CONF_STOPWORDS = frozenset(
    "a an the of to in on for and or is are be as with by from at this that these those it its how do "
    "does did can could should would will what which who where when why you your we our they them".split()
)


def _conf_tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9][a-z0-9\-]+", str(text).lower()) if len(t) > 2 and t not in _CONF_STOPWORDS]


def _estimate_context_confidence(question: str, modules: list[dict[str, Any]]) -> float:
    """Estimate how well the retrieved context covers the question (0..1).

    Combines question-token coverage across the top modules with a module-count
    signal. Low confidence triggers a safe refusal instead of a guessed answer.
    """
    if not modules:
        return 0.0
    q_tokens = _conf_tokens(question)
    if not q_tokens:
        return 1.0
    corpus = " ".join(
        " ".join([str(m.get("title", "")), str(m.get("summary", "")), str(m.get("assistant_excerpt", ""))]).lower()
        for m in modules
    )
    coverage = sum(1 for tok in q_tokens if tok in corpus) / len(q_tokens)
    module_signal = min(len(modules) / 3.0, 1.0)
    return min(1.0, 0.75 * coverage + 0.25 * module_signal)


def _load_critical_contradiction_ids(report_path: str) -> set[str]:
    """Load module IDs flagged as critical contradictions by the pipeline report."""
    path = Path(report_path)
    if not path.exists():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return set()
    if not isinstance(payload, dict):
        return set()
    ids: set[str] = set()
    raw_ids = payload.get("critical_module_ids", [])
    if isinstance(raw_ids, list):
        ids.update(str(item).strip() for item in raw_ids if str(item).strip())
    for issue in payload.get("contradictions", []) or []:
        if not isinstance(issue, dict) or str(issue.get("severity", "")).strip().lower() != "critical":
            continue
        for mod in issue.get("modules", []) or []:
            if isinstance(mod, dict) and str(mod.get("module_id", "")).strip():
                ids.add(str(mod.get("module_id", "")).strip())
    return ids


def _contradiction_check(
    config: dict[str, Any], citations: list[dict[str, Any]], context: dict[str, Any]
) -> list[str]:
    """Warn the user and alert doc owners when cited modules are in a contradiction.

    Returns any user-facing warnings. When a cited module is flagged critical, an
    owner-alert record is appended so a notifier can reach the document owner.
    """
    critical_ids = _load_critical_contradiction_ids(config["contradictions_report_path"])
    if not critical_ids:
        return []
    cited_ids = {str(c.get("id", "")).strip() for c in citations if str(c.get("id", "")).strip()}
    conflicted = sorted(cited_ids & critical_ids)
    if not conflicted:
        return []
    logger.warning("Ask AI contradiction warning for modules: %s", ", ".join(conflicted))
    owners = sorted(
        {
            str(m.get("owner", "")).strip()
            for m in context.get("modules", [])
            if str(m.get("id", "")).strip() in conflicted and str(m.get("owner", "")).strip()
        }
    )
    _append_usage_event(
        {"usage_log_enabled": True, "usage_log_path": config["owner_alert_log_path"]},
        {
            "type": "owner_alert",
            "ts": datetime.now(timezone.utc).isoformat(),
            "reason": "contradiction",
            "module_ids": conflicted,
            "owners": owners,
        },
    )
    return [
        "Potential contradiction detected in the cited documentation. Verify against "
        "the latest source docs before acting."
    ]


# Sentinel the model returns when the sources do not cover the question.
_NO_ANSWER = "NO_ANSWER"
_REFUSAL_TEXT = (
    "I could not find this in the current documentation. Try rephrasing your "
    "question, or this may be a gap worth documenting."
)
_NO_PROVIDER_TEXT = (
    "Ask AI runtime is active but the provider key is not configured, so I "
    "cannot generate an answer yet."
)

_SYSTEM_PROMPT = (
    "You are a documentation assistant. Answer the user's question using ONLY "
    "the numbered sources provided in the final message. Cite every source you "
    "rely on inline with its bracketed number, for example [1] or [2]. Give "
    "concise, practical guidance and use numbered steps when the task has an "
    "order. Do not use outside knowledge and do not invent URLs, endpoints, "
    "parameter names, or values. If the sources do not contain the answer, "
    f"reply with exactly this token and nothing else: {_NO_ANSWER}"
)


def _format_sources(modules: list[dict[str, Any]]) -> str:
    """Render retrieved modules as clean numbered sources for the prompt."""
    blocks = []
    for index, module in enumerate(modules, start=1):
        title = module.get("title") or module.get("id") or f"source {index}"
        url = str(module.get("url") or "").strip()
        excerpt = str(module.get("assistant_excerpt") or module.get("summary") or "").strip()
        header = f"[{index}] {title}"
        if url:
            header += f" ({url})"
        blocks.append(f"{header}\n{excerpt}" if excerpt else header)
    return "\n\n".join(blocks)


def _build_messages(
    config: dict[str, Any],
    question: str,
    history: list[ChatMessage],
    modules: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Assemble chat messages: system prompt, recent history, then question + sources."""
    messages: list[dict[str, str]] = [{"role": "system", "content": _SYSTEM_PROMPT}]
    max_turns = int(config.get("history_max_turns", 6))
    for msg in history[-max_turns:]:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append(
        {
            "role": "user",
            "content": f"Question: {question}\n\nSources:\n{_format_sources(modules)}",
        }
    )
    return messages


def _fallback_answer(modules: list[dict[str, Any]]) -> str:
    if modules:
        top = modules[0]
        excerpt = str(top.get("assistant_excerpt") or top.get("summary") or "")[:220]
        return f"{_NO_PROVIDER_TEXT} Best local match: {top.get('title')} -> {excerpt}"
    return _NO_PROVIDER_TEXT


def _referenced_citations(
    answer: str, all_citations: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Return only the sources the answer actually cited via [n] markers.

    Falls back to the full retrieved set when the answer cites nothing explicit,
    so a grounded answer never renders with zero sources.
    """
    referenced = sorted(
        {
            int(m)
            for m in re.findall(r"\[(\d+)\]", answer)
            if 1 <= int(m) <= len(all_citations)
        }
    )
    if not referenced:
        return all_citations
    return [all_citations[i - 1] for i in referenced]


def _finalize_answer(
    raw: str, all_citations: list[dict[str, Any]]
) -> tuple[str, list[dict[str, Any]], bool]:
    """Apply the grounding gate to a completed answer.

    Returns (answer_text, citations, grounded). A NO_ANSWER sentinel (or an
    empty answer) becomes a friendly refusal with no citations.
    """
    text = raw.strip()
    if not text or text.upper().startswith(_NO_ANSWER):
        return _REFUSAL_TEXT, [], False
    return text, _referenced_citations(text, all_citations), True


def _chat_payload(config: dict[str, Any], messages: list[dict[str, str]], stream: bool) -> dict[str, Any]:
    return {
        "model": config["model"],
        "temperature": config["temperature"],
        "max_tokens": config["max_tokens"],
        "messages": messages,
        "stream": stream,
    }


async def _ask_provider_once(config: dict[str, Any], messages: list[dict[str, str]]) -> str:
    """Single (non-streaming) provider call. Returns the raw answer text."""
    headers = {
        "Authorization": f"Bearer {config['provider_api_key']}",
        "Content-Type": "application/json",
    }
    url = f"{config['base_url']}/chat/completions"
    async with httpx.AsyncClient(timeout=25.0) as client:
        response = await client.post(url, headers=headers, json=_chat_payload(config, messages, False))
        response.raise_for_status()
        data = response.json()
    choices = data.get("choices", [])
    if not choices:
        return ""
    return str(choices[0].get("message", {}).get("content", "")).strip()


async def _stream_provider_tokens(
    config: dict[str, Any], messages: list[dict[str, str]]
) -> AsyncGenerator[str, None]:
    """Yield answer token chunks from an OpenAI-compatible streaming response."""
    headers = {
        "Authorization": f"Bearer {config['provider_api_key']}",
        "Content-Type": "application/json",
    }
    url = f"{config['base_url']}/chat/completions"
    async with httpx.AsyncClient(timeout=45.0) as client:
        async with client.stream("POST", url, headers=headers, json=_chat_payload(config, messages, True)) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                piece = delta.get("content")
                if piece:
                    yield piece


app = FastAPI(title="Ask AI Runtime", version="1.0.0")
app.mount("/public", StaticFiles(directory=str(Path(__file__).resolve().parents[1] / "public")), name="public")

_faiss_data: tuple[Any, list[dict[str, Any]]] | None = None


def _init_faiss() -> None:
    global _faiss_data  # noqa: PLW0603
    cfg = _load_runtime_config()
    _faiss_data = load_faiss_index(cfg["faiss_index_path"], cfg["faiss_metadata_path"])


_init_faiss()


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    cfg = _load_runtime_config()
    return {
        "ok": True,
        "enabled": cfg["enabled"],
        "provider": cfg["provider"],
        "billing_mode": cfg["billing_mode"],
        "semantic_retrieval": _faiss_data is not None,
        "reranking": cfg["rerank_enabled"],
        "hybrid_search": cfg["hybrid_enabled"],
        "retrieval_mode": cfg["retrieval_mode"],
        "graph_rerank": cfg["graph_rerank_enabled"],
        "query_decomposition": cfg["query_decomp_enabled"],
        "entity_first": cfg["entity_first_enabled"],
        "hyde": cfg["hyde_enabled"],
        "embedding_cache": cfg["embed_cache_enabled"],
        "confidence_guardrail": cfg["min_confidence"],
        "contradiction_warnings": bool(Path(cfg["contradictions_report_path"]).exists()),
    }


def _prepare_request(
    payload: AskRequest,
    x_ask_ai_key: str | None,
    x_user_id: str | None,
    x_user_role: str | None,
    x_user_plan: str | None,
) -> tuple[dict[str, Any], Any, dict[str, Any], list[dict[str, Any]]]:
    """Shared gate + retrieval for both the buffered and streaming endpoints.

    Returns (config, auth, context, all_citations). Raises HTTPException for
    disabled/unauthorized/unentitled requests.
    """
    config = _load_runtime_config()

    if not config["enabled"]:
        raise HTTPException(status_code=403, detail="Ask AI is disabled")

    try:
        require_runtime_api_key(x_ask_ai_key)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    auth = parse_auth_context(x_user_id, x_user_role, x_user_plan)
    try:
        validate_role(auth, config["allowed_roles"], config["require_auth"])
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    if not can_use_ask_ai(auth.plan, config["billing_mode"]):
        raise HTTPException(status_code=402, detail="Current plan is not entitled for Ask AI")

    # Abuse protection: rate limit per user (falls back to the API key identity).
    identity = (x_user_id or "").strip() or (x_ask_ai_key or "anonymous")
    _rate_limit_check(identity, config["rate_limit_per_minute"])

    modules = load_knowledge_index(config["knowledge_index_path"])
    bundles = load_assistant_bundles(config["assistant_bundle_glob"])
    # Keep bundles loaded for future adapter extensions.
    _ = bundles

    context = build_context(
        payload.question,
        modules,
        config["max_context_modules"],
        faiss_data=_faiss_data,
        rerank_enabled=config["rerank_enabled"],
        rerank_candidates=config["rerank_candidates"],
        rerank_model=config["rerank_model"],
        hybrid_enabled=config["hybrid_enabled"],
        rrf_k=config["rrf_k"],
        hyde_enabled=config["hyde_enabled"],
        hyde_model=config["hyde_model"],
        cache_enabled=config["embed_cache_enabled"],
        cache_ttl=config["embed_cache_ttl"],
        cache_max_size=config["embed_cache_max_size"],
        retrieval_mode=config["retrieval_mode"],
        vectorless_min_score=config["vectorless_min_score"],
        graph_rerank_enabled=config["graph_rerank_enabled"],
        graph_rerank_boost=config["graph_rerank_boost"],
        query_decomp_enabled=config["query_decomp_enabled"],
        entity_first_enabled=config["entity_first_enabled"],
        history=[{"role": m.role, "content": m.content} for m in payload.history],
    )
    all_citations = [
        {
            "id": item.get("id"),
            "title": item.get("title"),
            "source_file": item.get("source_file"),
            "url": item.get("url", ""),
        }
        for item in context["modules"]
    ]
    return config, auth, context, all_citations


def _log_question(
    config: dict[str, Any],
    auth: Any,
    question_id: str,
    question: str,
    context: dict[str, Any],
    citations: list[dict[str, Any]],
    answer: str,
    grounded: bool,
    session_id: str = "",
    confidence: float | None = None,
    warnings_count: int = 0,
) -> None:
    _append_usage_event(
        config,
        {
            "type": "question",
            "ts": datetime.now(timezone.utc).isoformat(),
            "question_id": question_id,
            "session_id": session_id,
            "question": question,
            "user_role": auth.user_role,
            "user_plan": auth.plan,
            "retrieved_ids": [str(item.get("id", "")) for item in context["modules"]],
            "citations_count": len(citations),
            "answer_chars": len(answer),
            "grounded": grounded,
            "confidence": round(float(confidence), 4) if confidence is not None else None,
            "low_confidence": bool(confidence is not None and confidence < float(config["min_confidence"])),
            "warnings_count": warnings_count,
        },
    )


@app.post("/api/v1/ask", response_model=AskResponse)
async def ask(
    payload: AskRequest,
    x_ask_ai_key: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
    x_user_plan: str | None = Header(default=None),
    x_session_id: str | None = Header(default=None),
    x_provider_key: str | None = Header(default=None),
    x_provider_base_url: str | None = Header(default=None),
    x_model: str | None = Header(default=None),
) -> AskResponse:
    config, auth, context, all_citations = _prepare_request(
        payload, x_ask_ai_key, x_user_id, x_user_role, x_user_plan
    )
    gen_config = _apply_byok(config, x_provider_key, x_provider_base_url, x_model)
    modules = context["modules"]
    confidence = _estimate_context_confidence(payload.question, modules)
    warnings: list[str] = []

    # Grounding + confidence gates: refuse rather than guess on empty or weak context.
    if not modules or confidence < config["min_confidence"]:
        answer, citations, grounded = (
            (_REFUSAL_TEXT if not modules else _LOW_CONFIDENCE_TEXT),
            [],
            False,
        )
    elif not gen_config["provider_api_key"]:
        answer, citations, grounded = _fallback_answer(modules), all_citations, True
    else:
        messages = _build_messages(gen_config, payload.question, payload.history, modules)
        raw = await _ask_provider_once(gen_config, messages)
        answer, citations, grounded = _finalize_answer(raw, all_citations)

    if citations:
        warnings = _contradiction_check(config, citations, context)

    question_id = uuid.uuid4().hex
    _log_question(
        config, auth, question_id, payload.question, context, citations, answer, grounded,
        session_id=(x_session_id or "").strip(), confidence=confidence, warnings_count=len(warnings),
    )
    return AskResponse(
        answer=answer, citations=citations, question_id=question_id, grounded=grounded, warnings=warnings
    )


def _sse(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event, ensure_ascii=True)}\n\n"


@app.post("/api/v1/ask/stream")
async def ask_stream(
    payload: AskRequest,
    x_ask_ai_key: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
    x_user_plan: str | None = Header(default=None),
    x_session_id: str | None = Header(default=None),
    x_provider_key: str | None = Header(default=None),
    x_provider_base_url: str | None = Header(default=None),
    x_model: str | None = Header(default=None),
) -> StreamingResponse:
    """Stream the answer token-by-token over Server-Sent Events.

    Emits {"type": "token", "text": ...} events while generating, then a final
    {"type": "done", ...} event carrying citations, question_id, and grounded.
    """
    config, auth, context, all_citations = _prepare_request(
        payload, x_ask_ai_key, x_user_id, x_user_role, x_user_plan
    )
    gen_config = _apply_byok(config, x_provider_key, x_provider_base_url, x_model)
    modules = context["modules"]
    question_id = uuid.uuid4().hex
    session_id = (x_session_id or "").strip()
    confidence = _estimate_context_confidence(payload.question, modules)

    async def event_stream() -> AsyncGenerator[str, None]:
        warnings: list[str] = []
        # Grounding + confidence gates: refuse rather than guess on empty or weak context.
        if not modules or confidence < config["min_confidence"]:
            answer, citations, grounded = (
                (_REFUSAL_TEXT if not modules else _LOW_CONFIDENCE_TEXT),
                [],
                False,
            )
            yield _sse({"type": "token", "text": answer})
        elif not gen_config["provider_api_key"]:
            answer, citations, grounded = _fallback_answer(modules), all_citations, True
            yield _sse({"type": "token", "text": answer})
        else:
            messages = _build_messages(gen_config, payload.question, payload.history, modules)
            buffer = ""
            gated = False  # becomes True once we confirm the answer is not NO_ANSWER
            try:
                async for piece in _stream_provider_tokens(gen_config, messages):
                    buffer += piece
                    if gated:
                        yield _sse({"type": "token", "text": piece})
                        continue
                    # Hold back until we can rule out the NO_ANSWER sentinel.
                    if len(buffer) < len(_NO_ANSWER):
                        continue
                    if buffer.strip().upper().startswith(_NO_ANSWER):
                        break
                    gated = True
                    yield _sse({"type": "token", "text": buffer})
            except httpx.HTTPError as exc:
                logger.warning("Ask AI stream failed: %s", exc)
                yield _sse({"type": "error", "message": "Streaming failed."})
                yield _sse({"type": "done", "citations": [], "question_id": question_id, "grounded": False})
                return
            answer, citations, grounded = _finalize_answer(buffer, all_citations)
            if not gated:
                # Nothing was streamed yet (short answer or a NO_ANSWER sentinel);
                # emit the finalized text as a single token.
                yield _sse({"type": "token", "text": answer})

        if citations:
            warnings = _contradiction_check(config, citations, context)

        _log_question(
            config, auth, question_id, payload.question, context, citations, answer, grounded,
            session_id=session_id, confidence=confidence, warnings_count=len(warnings),
        )
        yield _sse(
            {
                "type": "done",
                "citations": citations,
                "question_id": question_id,
                "grounded": grounded,
                "warnings": warnings,
            }
        )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/v1/feedback")
async def feedback(
    payload: FeedbackRequest,
    x_ask_ai_key: str | None = Header(default=None),
    x_session_id: str | None = Header(default=None),
) -> dict[str, str]:
    config = _load_runtime_config()
    try:
        require_runtime_api_key(x_ask_ai_key)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    _append_usage_event(
        config,
        {
            "type": "feedback",
            "ts": datetime.now(timezone.utc).isoformat(),
            "question_id": payload.question_id,
            "session_id": (x_session_id or "").strip(),
            "helpful": bool(payload.helpful),
            "comment": payload.comment[:2000],
        },
    )
    return {"status": "recorded"}


@app.post("/api/v1/billing/webhook")
async def billing_webhook(
    request: Request,
    x_signature: str | None = Header(default=None),
) -> JSONResponse:
    """Process billing webhook events and update entitlements.

    Validates the HMAC signature, parses the event payload, and
    applies entitlement changes based on subscription lifecycle
    events (created, updated, canceled, payment success/failure).
    Unrecognized events are acknowledged but not processed.

    Args:
        request: Incoming FastAPI request containing the webhook body.
        x_signature: HMAC-SHA256 signature from the billing provider.

    Returns:
        JSON response indicating processing result.

    Raises:
        HTTPException: 401 if signature verification fails,
            400 if the payload cannot be parsed.
    """
    config = _load_runtime_config()
    body = await request.body()

    if not verify_webhook_signature(body, x_signature, config["webhook_secret"]):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.error("Webhook payload parse error: %s", exc)
        raise HTTPException(
            status_code=400, detail="Malformed webhook payload"
        ) from exc

    event_name = payload.get("meta", {}).get("event_name", "")
    if not event_name:
        event_name = payload.get("event", "")

    event_data = payload.get("data", {})
    attrs = event_data.get("attributes", {})

    entitlement_events = {
        "subscription_created",
        "subscription_updated",
        "subscription_resumed",
        "subscription_payment_success",
    }
    downgrade_events = {
        "subscription_cancelled",
        "subscription_expired",
        "subscription_payment_failed",
    }

    result: dict[str, Any] = {"ok": True, "event": event_name}

    if event_name in entitlement_events:
        variant_id = str(attrs.get("variant_id", ""))
        plan = _resolve_plan_from_variant(variant_id)
        status = attrs.get("status", "active")
        custom_data = attrs.get("custom_data", {})
        user_id = custom_data.get("veridoc_user_id", "")

        result["action"] = "entitlement_granted"
        result["plan"] = plan
        result["status"] = status
        result["user_id"] = user_id

        logger.info(
            "Entitlement granted: event=%s user=%s plan=%s status=%s",
            event_name,
            user_id,
            plan,
            status,
        )

    elif event_name in downgrade_events:
        custom_data = attrs.get("custom_data", {})
        user_id = custom_data.get("veridoc_user_id", "")

        result["action"] = "entitlement_revoked"
        result["user_id"] = user_id

        logger.info(
            "Entitlement revoked: event=%s user=%s",
            event_name,
            user_id,
        )

    else:
        result["action"] = "ignored"
        logger.info("Unhandled billing webhook event: %s", event_name)

    return JSONResponse(result)


def _resolve_plan_from_variant(variant_id: str) -> str:
    """Map a billing provider variant ID to a VeriDoc plan name.

    Reads variant-to-plan mappings from environment variables.
    Falls back to "free" when the variant is unknown.

    Args:
        variant_id: The billing provider variant identifier.

    Returns:
        The VeriDoc plan name (e.g. "starter", "pro", "business").
    """
    variant_plan_map: dict[str, str] = {
        os.getenv("LS_VARIANT_STARTER_MONTHLY", ""): "starter",
        os.getenv("LS_VARIANT_STARTER_ANNUAL", ""): "starter",
        os.getenv("LS_VARIANT_PRO_MONTHLY", ""): "pro",
        os.getenv("LS_VARIANT_PRO_ANNUAL", ""): "pro",
        os.getenv("LS_VARIANT_BUSINESS_MONTHLY", ""): "business",
        os.getenv("LS_VARIANT_BUSINESS_ANNUAL", ""): "business",
        os.getenv("LS_VARIANT_ENTERPRISE_MONTHLY", ""): "enterprise",
        os.getenv("LS_VARIANT_ENTERPRISE_ANNUAL", ""): "enterprise",
    }
    variant_plan_map.pop("", None)
    return variant_plan_map.get(variant_id, "free")

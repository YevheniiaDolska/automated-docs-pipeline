"""Ask AI runtime API server (optional module)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.auth import parse_auth_context, require_runtime_api_key, validate_role
from app.billing_hooks import can_use_ask_ai, verify_webhook_signature
from app.retrieval import build_context, load_assistant_bundles, load_faiss_index, load_knowledge_index

load_dotenv()


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class AskResponse(BaseModel):
    answer: str
    citations: list[dict[str, Any]]


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _load_runtime_config() -> dict[str, Any]:
    return {
        "enabled": _bool_env("ASK_AI_ENABLED", True),
        "provider": os.getenv("ASK_AI_PROVIDER", "openai"),
        "model": os.getenv("ASK_AI_MODEL", "gpt-4.1-mini"),
        "base_url": os.getenv("ASK_AI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        "provider_api_key": os.getenv("ASK_AI_PROVIDER_API_KEY", "").strip(),
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
    }


async def _ask_provider(config: dict[str, Any], context: dict[str, Any]) -> str:
    """Call provider API; fallback to deterministic response when key is missing."""
    question = context["question"]
    modules = context["modules"]

    if not config["provider_api_key"]:
        if modules:
            top = modules[0]
            return (
                "Ask AI runtime is active but provider key is not configured. "
                f"Best local match: {top.get('title')} -> {top.get('assistant_excerpt', '')[:220]}"
            )
        return "Ask AI runtime is active but provider key is not configured, and no relevant module was found."

    if config["provider"] != "openai":
        return "Provider adapter is not implemented yet for this provider. Use openai or add adapter logic."

    system_prompt = (
        "You are a documentation assistant. Answer with clear steps. "
        "Use only provided context modules. If uncertain, say what is missing."
    )
    user_prompt = (
        f"Question: {question}\n\n"
        f"Context modules:\n{modules}\n\n"
        "Return short practical guidance with numbered steps."
    )

    payload = {
        "model": config["model"],
        "temperature": config["temperature"],
        "max_tokens": config["max_tokens"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    headers = {
        "Authorization": f"Bearer {config['provider_api_key']}",
        "Content-Type": "application/json",
    }

    url = f"{config['base_url']}/chat/completions"
    async with httpx.AsyncClient(timeout=25.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    choices = data.get("choices", [])
    if not choices:
        return "No answer returned from provider."
    message = choices[0].get("message", {})
    return str(message.get("content", "")).strip() or "No answer returned from provider."


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
        "hyde": cfg["hyde_enabled"],
        "embedding_cache": cfg["embed_cache_enabled"],
    }


@app.post("/api/v1/ask", response_model=AskResponse)
async def ask(
    payload: AskRequest,
    x_ask_ai_key: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
    x_user_plan: str | None = Header(default=None),
) -> AskResponse:
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
    )
    answer = await _ask_provider(config, context)

    citations = [
        {
            "id": item.get("id"),
            "title": item.get("title"),
            "source_file": item.get("source_file"),
        }
        for item in context["modules"]
    ]

    return AskResponse(answer=answer, citations=citations)


@app.post("/api/v1/billing/webhook")
async def billing_webhook(request: Request, x_signature: str | None = Header(default=None)) -> JSONResponse:
    config = _load_runtime_config()
    body = await request.body()

    if not verify_webhook_signature(body, x_signature, config["webhook_secret"]):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # TODO: Replace with real entitlement update logic in client environment.
    return JSONResponse({"ok": True, "message": "Webhook accepted"})

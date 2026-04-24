"""Ask AI runtime API server (optional module)."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime, timezone
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
from app.secrets import resolve_provider_api_key

logger = logging.getLogger(__name__)

load_dotenv()


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class AskResponse(BaseModel):
    answer: str
    citations: list[dict[str, Any]]
    warnings: list[str] = Field(default_factory=list)


class FeedbackRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    helpful: bool
    answer: str = Field(default="", max_length=12000)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    comment: str = Field(default="", max_length=1000)


STOPWORDS = {
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
WORD_RE = re.compile(r"[a-z0-9_]+", re.IGNORECASE)


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _load_runtime_config() -> dict[str, Any]:
    provider = os.getenv("ASK_AI_PROVIDER", "openai").strip().lower()
    base_default = "http://localhost:11434/v1" if provider in {"local", "ollama"} else "https://api.openai.com/v1"
    return {
        "enabled": _bool_env("ASK_AI_ENABLED", True),
        "provider": provider,
        "model": os.getenv("ASK_AI_MODEL", "gpt-4.1-mini"),
        "base_url": os.getenv("ASK_AI_BASE_URL", base_default).rstrip("/"),
        "provider_api_key": resolve_provider_api_key(provider),
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
        "retrieval_mode": os.getenv("ASK_AI_RETRIEVAL_MODE", "auto").strip().lower(),
        "vectorless_min_score": float(os.getenv("ASK_AI_VECTORLESS_MIN_SCORE", "2.0")),
        "min_confidence": float(os.getenv("ASK_AI_MIN_CONFIDENCE", "0.28")),
        "usage_log_path": os.getenv("ASK_AI_USAGE_LOG_PATH", "reports/ask_ai_usage.jsonl"),
        "feedback_log_path": os.getenv("ASK_AI_FEEDBACK_LOG_PATH", "reports/ask_ai_feedback.jsonl"),
        "contradictions_report_path": os.getenv("ASK_AI_CONTRADICTIONS_REPORT_PATH", "reports/rag_contradictions_report.json"),
    }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _append_jsonl(path: str, record: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=True) + "\n")


def _tokenize(text: str) -> list[str]:
    return [tok.lower() for tok in WORD_RE.findall(text) if tok and tok.lower() not in STOPWORDS]


def _estimate_context_confidence(question: str, modules: list[dict[str, Any]]) -> tuple[float, int, int]:
    if not modules:
        return 0.0, 0, 0
    q_tokens = [tok for tok in _tokenize(question) if len(tok) > 2]
    if not q_tokens:
        return 1.0, 0, 0
    corpus = " ".join(
        " ".join(
            [
                str(m.get("title", "")),
                str(m.get("summary", "")),
                str(m.get("assistant_excerpt", "")),
            ]
        ).lower()
        for m in modules
    )
    matched = sum(1 for tok in q_tokens if tok in corpus)
    coverage = matched / max(len(q_tokens), 1)
    module_signal = min(len(modules) / 3.0, 1.0)
    confidence = min(1.0, 0.75 * coverage + 0.25 * module_signal)
    return confidence, matched, len(q_tokens)


def _load_critical_contradiction_ids(report_path: str) -> set[str]:
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
    raw_issues = payload.get("contradictions", [])
    if isinstance(raw_issues, list):
        for issue in raw_issues:
            if not isinstance(issue, dict):
                continue
            if str(issue.get("severity", "")).strip().lower() != "critical":
                continue
            modules = issue.get("modules", [])
            if not isinstance(modules, list):
                continue
            for mod in modules:
                if not isinstance(mod, dict):
                    continue
                module_id = str(mod.get("module_id", "")).strip()
                if module_id:
                    ids.add(module_id)
    return ids


async def _ask_provider(config: dict[str, Any], context: dict[str, Any]) -> str:
    """Call provider API; fallback to deterministic response when key is missing."""
    question = context["question"]
    modules = context["modules"]
    provider = str(config.get("provider", "openai")).strip().lower()

    system_prompt = (
        "You are a documentation assistant. Answer with clear steps. "
        "Use only provided context modules. If uncertain, say what is missing."
    )
    user_prompt = (
        f"Question: {question}\n\n"
        f"Context modules:\n{modules}\n\n"
        "Return short practical guidance with numbered steps."
    )

    if provider in {"local", "ollama"}:
        base_url = str(config.get("base_url", "http://localhost:11434/v1")).rstrip("/")
        async with httpx.AsyncClient(timeout=60.0) as client:
            if base_url.endswith("/v1"):
                payload = {
                    "model": config["model"],
                    "temperature": config["temperature"],
                    "max_tokens": config["max_tokens"],
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                }
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers={"Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                choices = data.get("choices", [])
                if not choices:
                    return "No answer returned from local provider."
                message = choices[0].get("message", {})
                return str(message.get("content", "")).strip() or "No answer returned from local provider."

            payload = {
                "model": config["model"],
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "options": {
                    "temperature": float(config["temperature"]),
                    "num_predict": int(config["max_tokens"]),
                },
            }
            response = await client.post(
                f"{base_url}/api/chat",
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            message = data.get("message", {})
            return str(message.get("content", "")).strip() or "No answer returned from local provider."

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
        "retrieval_mode": cfg["retrieval_mode"],
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
    started_at = time.perf_counter()
    config = _load_runtime_config()
    status = "ok"
    error_detail = ""
    warnings: list[str] = []
    citations: list[dict[str, Any]] = []
    context: dict[str, Any] = {"retrieval_mode": "", "retrieval_fallback_used": False, "modules": []}
    confidence = 0.0
    matched_tokens = 0
    total_tokens = 0
    low_confidence = False

    try:
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
            retrieval_mode=config["retrieval_mode"],
            vectorless_min_score=config["vectorless_min_score"],
        )

        citations = [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "source_file": item.get("source_file"),
            }
            for item in context["modules"]
        ]

        confidence, matched_tokens, total_tokens = _estimate_context_confidence(payload.question, context["modules"])
        low_confidence = confidence < float(config["min_confidence"])

        critical_ids = _load_critical_contradiction_ids(config["contradictions_report_path"])
        if critical_ids:
            cited_ids = {str(item.get("id", "")).strip() for item in citations if str(item.get("id", "")).strip()}
            conflicted = sorted(cited_ids.intersection(critical_ids))
            if conflicted:
                warnings.append(
                    "Potential contradiction risk detected in cited knowledge modules. "
                    "Please verify against latest source docs before acting."
                )
                logger.warning("Ask AI contradiction warning for modules: %s", ", ".join(conflicted))

        if low_confidence:
            answer = (
                "I do not have enough reliable context to answer this safely. "
                "Please update or add source documentation for this topic, then rerun indexing."
            )
        else:
            answer = await _ask_provider(config, context)

        return AskResponse(answer=answer, citations=citations, warnings=warnings)
    except HTTPException as exc:
        status = "error"
        error_detail = str(exc.detail)
        raise
    except Exception as exc:  # noqa: BLE001
        status = "error"
        error_detail = str(exc)
        raise
    finally:
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        try:
            _append_jsonl(
                config["usage_log_path"],
                {
                    "timestamp": _utc_now_iso(),
                    "status": status,
                    "latency_ms": elapsed_ms,
                    "question": payload.question,
                    "question_length": len(payload.question),
                    "user_id": x_user_id or "",
                    "user_role": x_user_role or "",
                    "plan": x_user_plan or "",
                    "citation_ids": [str(item.get("id", "")).strip() for item in citations if str(item.get("id", "")).strip()],
                    "warnings_count": len(warnings),
                    "retrieval_mode": str(context.get("retrieval_mode", "")),
                    "retrieval_fallback_used": bool(context.get("retrieval_fallback_used", False)),
                    "low_confidence": low_confidence,
                    "confidence": round(float(confidence), 4),
                    "matched_question_tokens": matched_tokens,
                    "total_question_tokens": total_tokens,
                    "error": error_detail,
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to write Ask AI usage log: %s", exc)


@app.post("/api/v1/feedback")
def feedback(
    payload: FeedbackRequest,
    x_ask_ai_key: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
    x_user_plan: str | None = Header(default=None),
) -> dict[str, Any]:
    config = _load_runtime_config()
    try:
        require_runtime_api_key(x_ask_ai_key)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    auth = parse_auth_context(x_user_id, x_user_role, x_user_plan)
    try:
        validate_role(auth, config["allowed_roles"], config["require_auth"])
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    try:
        _append_jsonl(
            config["feedback_log_path"],
            {
                "timestamp": _utc_now_iso(),
                "user_id": auth.user_id,
                "user_role": auth.role,
                "plan": auth.plan,
                "helpful": bool(payload.helpful),
                "question": payload.question,
                "answer_length": len(payload.answer or ""),
                "comment": payload.comment or "",
                "citation_ids": [
                    str(item.get("id", "")).strip()
                    for item in payload.citations
                    if isinstance(item, dict) and str(item.get("id", "")).strip()
                ],
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to write Ask AI feedback log: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to persist feedback") from exc

    return {"ok": True}


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

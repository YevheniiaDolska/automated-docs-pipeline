from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _import_runtime_module(runtime_root: Path, module_name: str):
    to_delete = [name for name in sys.modules if name == "app" or name.startswith("app.")]
    for name in to_delete:
        del sys.modules[name]
    sys.path.insert(0, str(runtime_root))
    try:
        return importlib.import_module(module_name)
    finally:
        if sys.path and sys.path[0] == str(runtime_root):
            sys.path.pop(0)


@pytest.mark.parametrize(
    "runtime_root",
    [
        ROOT / "ask-ai-runtime",
        ROOT / "runtime" / "ask-ai-pack",
    ],
)
def test_auto_mode_prefers_vectorless_for_structured_change_query(runtime_root: Path) -> None:
    retrieval = _import_runtime_module(runtime_root, "app.retrieval")
    modules = [
        {
            "id": "release-q3",
            "title": "Release notes Q3",
            "summary": "Net revenue changes and financial updates for Q3.",
            "heading": "Net revenue changes",
            "url": "/releases/q3",
            "tags": ["release", "changelog"],
            "priority": 3,
            "assistant_excerpt": "Q3 net revenue changed by 12%.",
        },
        {
            "id": "auth-guide",
            "title": "API authentication guide",
            "summary": "How to configure API authentication.",
            "heading": "Configure API key auth",
            "url": "/how-to/api-auth",
            "tags": ["how-to", "api"],
            "priority": 2,
            "assistant_excerpt": "Use bearer token in Authorization header.",
        },
    ]

    context = retrieval.build_context(
        "what changed in net revenue between q2 and q3?",
        modules,
        max_context_modules=3,
        faiss_data=None,
        retrieval_mode="auto",
        vectorless_min_score=1.0,
        graph_rerank_enabled=False,
    )

    assert context["retrieval_mode"] == "vectorless"
    assert context["retrieval_fallback_used"] is False
    assert context["modules"]
    assert context["modules"][0]["id"] == "release-q3"


@pytest.mark.parametrize(
    "runtime_root",
    [
        ROOT / "ask-ai-runtime",
        ROOT / "runtime" / "ask-ai-pack",
    ],
)
def test_auto_mode_falls_back_to_token_when_vectorless_signal_is_low(runtime_root: Path) -> None:
    retrieval = _import_runtime_module(runtime_root, "app.retrieval")
    modules = [
        {
            "id": "m1",
            "title": "General docs index",
            "summary": "Overview for docs navigation.",
            "heading": "Overview",
            "url": "/index",
            "tags": ["docs"],
            "priority": 1,
            "assistant_excerpt": "Entry point.",
        }
    ]

    context = retrieval.build_context(
        "what changed in net revenue between q2 and q3?",
        modules,
        max_context_modules=2,
        faiss_data=None,
        retrieval_mode="auto",
        vectorless_min_score=999.0,
        graph_rerank_enabled=False,
    )

    assert context["retrieval_mode"] == "token"
    assert context["retrieval_fallback_used"] is True
    assert context["modules"]


@pytest.mark.parametrize(
    "runtime_root,provider,expected_base",
    [
        (ROOT / "ask-ai-runtime", "local", "http://localhost:11434/v1"),
        (ROOT / "ask-ai-runtime", "openai", "https://api.openai.com/v1"),
        (ROOT / "runtime" / "ask-ai-pack", "local", "http://localhost:11434/v1"),
        (ROOT / "runtime" / "ask-ai-pack", "openai", "https://api.openai.com/v1"),
    ],
)
def test_runtime_config_supports_local_hybrid_cloud_modes(
    runtime_root: Path,
    provider: str,
    expected_base: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main = _import_runtime_module(runtime_root, "app.main")
    monkeypatch.setenv("ASK_AI_PROVIDER", provider)
    monkeypatch.setenv("ASK_AI_RETRIEVAL_MODE", "auto")
    monkeypatch.setenv("ASK_AI_HYBRID_ENABLED", "true")
    cfg = main._load_runtime_config()

    assert cfg["provider"] == provider
    assert cfg["base_url"] == expected_base
    assert cfg["retrieval_mode"] == "auto"
    assert cfg["hybrid_enabled"] is True
    assert cfg["graph_rerank_enabled"] is True
    assert cfg["query_decomp_enabled"] is True
    assert cfg["entity_first_enabled"] is True


@pytest.mark.parametrize(
    "runtime_root",
    [
        ROOT / "ask-ai-runtime",
        ROOT / "runtime" / "ask-ai-pack",
    ],
)
def test_query_decomposition_combines_evidence_from_multiple_subqueries(runtime_root: Path) -> None:
    retrieval = _import_runtime_module(runtime_root, "app.retrieval")
    modules = [
        {
            "id": "billing-rules",
            "title": "Billing rules",
            "summary": "Invoice and payment policies.",
            "heading": "Billing",
            "url": "/reference/billing",
            "tags": ["billing"],
            "priority": 2,
            "assistant_excerpt": "Invoice generation.",
        },
        {
            "id": "auth-rules",
            "title": "Authentication policy",
            "summary": "SSO and token authentication.",
            "heading": "Auth",
            "url": "/reference/auth",
            "tags": ["security", "auth"],
            "priority": 2,
            "assistant_excerpt": "SSO setup and token scopes.",
        },
    ]

    context = retrieval.build_context(
        "show billing and authentication requirements",
        modules,
        max_context_modules=3,
        faiss_data=None,
        retrieval_mode="token",
        query_decomp_enabled=True,
        graph_rerank_enabled=False,
        entity_first_enabled=False,
    )

    ids = [m["id"] for m in context["modules"]]
    assert "billing-rules" in ids
    assert "auth-rules" in ids


@pytest.mark.parametrize(
    "runtime_root",
    [
        ROOT / "ask-ai-runtime",
        ROOT / "runtime" / "ask-ai-pack",
    ],
)
def test_entity_first_boosts_endpoint_specific_module(runtime_root: Path) -> None:
    retrieval = _import_runtime_module(runtime_root, "app.retrieval")
    modules = [
        {
            "id": "generic-auth",
            "title": "Authentication overview",
            "summary": "General auth model.",
            "heading": "Overview",
            "url": "/concepts/auth",
            "tags": ["auth"],
            "priority": 3,
            "assistant_excerpt": "General authentication concepts.",
        },
        {
            "id": "endpoint-auth",
            "title": "POST /v1/payments endpoint auth",
            "summary": "Auth requirements for /v1/payments",
            "heading": "Endpoint auth",
            "url": "/reference/post-v1-payments",
            "tags": ["api", "endpoint"],
            "priority": 1,
            "assistant_excerpt": "Use Bearer token for /v1/payments.",
        },
    ]

    context = retrieval.build_context(
        "auth for POST /v1/payments endpoint",
        modules,
        max_context_modules=2,
        faiss_data=None,
        retrieval_mode="token",
        entity_first_enabled=True,
        graph_rerank_enabled=False,
    )

    assert context["modules"]
    assert context["modules"][0]["id"] == "endpoint-auth"


@pytest.mark.parametrize(
    "runtime_root",
    [
        ROOT / "ask-ai-runtime",
        ROOT / "runtime" / "ask-ai-pack",
    ],
)
def test_graph_rerank_promotes_dependency_neighbor(runtime_root: Path) -> None:
    retrieval = _import_runtime_module(runtime_root, "app.retrieval")
    modules = [
        {
            "id": "seed",
            "title": "Webhook auth setup",
            "summary": "Configure webhook authentication.",
            "heading": "Webhook auth",
            "url": "/how-to/webhook-auth",
            "tags": ["webhook", "auth"],
            "priority": 2,
            "assistant_excerpt": "Configure signatures.",
            "dependencies": ["dep"],
        },
        {
            "id": "dep",
            "title": "Webhook signature verification",
            "summary": "Verify signatures and replay attack protections.",
            "heading": "Signature verification",
            "url": "/reference/webhook-signature",
            "tags": ["webhook", "security"],
            "priority": 1,
            "assistant_excerpt": "Validate signature header.",
            "dependencies": [],
        },
    ]

    context = retrieval.build_context(
        "configure webhook auth",
        modules,
        max_context_modules=2,
        faiss_data=None,
        retrieval_mode="token",
        query_decomp_enabled=False,
        entity_first_enabled=False,
        graph_rerank_enabled=True,
        graph_rerank_boost=0.9,
    )

    assert context["retrieval_mode"].endswith("+graph")
    ids = [m["id"] for m in context["modules"]]
    assert "seed" in ids
    assert "dep" in ids

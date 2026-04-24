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

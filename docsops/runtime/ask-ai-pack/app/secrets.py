"""Provider key resolution helpers for Ask AI runtime."""

from __future__ import annotations

import os


_PROVIDER_KEY_FALLBACKS: dict[str, tuple[str, ...]] = {
    "openai": (
        "ASK_AI_PROVIDER_API_KEY",
        "DOCSOPS_SHARED_OPENAI_API_KEY",
        "OPENAI_API_KEY",
    ),
    "anthropic": (
        "ASK_AI_PROVIDER_API_KEY",
        "DOCSOPS_SHARED_ANTHROPIC_API_KEY",
        "ANTHROPIC_API_KEY",
    ),
    "azure-openai": (
        "ASK_AI_PROVIDER_API_KEY",
        "DOCSOPS_SHARED_AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_API_KEY",
    ),
    "custom": (
        "ASK_AI_PROVIDER_API_KEY",
        "ASK_AI_API_KEY",
    ),
}


def resolve_provider_api_key(provider: str) -> str:
    """Resolve provider key with shared-key fallback support."""
    normalized = str(provider or "").strip().lower()
    names = _PROVIDER_KEY_FALLBACKS.get(normalized, ("ASK_AI_PROVIDER_API_KEY",))
    for env_name in names:
        value = os.getenv(env_name, "").strip()
        if value:
            return value
    return ""

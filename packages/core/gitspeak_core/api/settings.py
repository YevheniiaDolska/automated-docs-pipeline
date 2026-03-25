"""VeriDoc settings API endpoints.

Provides CRUD for pipeline module toggles, scoped by user tier.
Each module has a minimum tier requirement; attempts to enable
modules above the user's tier are rejected.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Module registry
# ---------------------------------------------------------------------------

AVAILABLE_MODULES: list[dict[str, str]] = [
    {"key": "gap_detection", "label": "Gap detection", "min_tier": "starter"},
    {"key": "drift_detection", "label": "API drift detection", "min_tier": "pro"},
    {"key": "docs_contract", "label": "Docs contract check", "min_tier": "pro"},
    {"key": "normalization", "label": "Doc normalization", "min_tier": "starter"},
    {"key": "snippet_lint", "label": "Code snippet lint", "min_tier": "starter"},
    {"key": "fact_checks", "label": "SEO/GEO + fact checks", "min_tier": "starter"},
    {"key": "multilang_examples", "label": "Multi-language examples", "min_tier": "pro"},
    {"key": "self_checks", "label": "Code examples smoke tests", "min_tier": "starter"},
    {"key": "lifecycle_management", "label": "Lifecycle management", "min_tier": "starter"},
    {"key": "knowledge_validation", "label": "Knowledge modules", "min_tier": "business"},
    {"key": "rag_optimization", "label": "RAG retrieval index", "min_tier": "business"},
    {"key": "ontology_graph", "label": "Knowledge graph", "min_tier": "business"},
    {"key": "retrieval_evals", "label": "Retrieval quality evals", "min_tier": "business"},
    {"key": "i18n_sync", "label": "i18n translation sync", "min_tier": "enterprise"},
    {"key": "release_pack", "label": "Release docs pack", "min_tier": "pro"},
    {"key": "terminology_management", "label": "Glossary sync", "min_tier": "starter"},
    {"key": "kpi_sla", "label": "KPI/SLA evaluation", "min_tier": "pro"},
    {"key": "doc_compiler", "label": "Docs health reports", "min_tier": "enterprise"},
    {"key": "diagram_validation", "label": "Diagram validation", "min_tier": "pro"},
    {"key": "test_assets_generation", "label": "Test assets generation", "min_tier": "pro"},
    {"key": "rag_test_generation", "label": "RAG test generation", "min_tier": "pro"},
    {"key": "finalize_gate", "label": "Finalize docs gate", "min_tier": "pro"},
]

TIER_ORDER = ["free", "starter", "pro", "business", "enterprise"]


def _tier_index(tier: str) -> int:
    """Map tier name to ordinal index; unknown tiers default to free."""
    try:
        return TIER_ORDER.index(tier.lower())
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class PipelineSettings(BaseModel):
    """User-configurable pipeline settings."""

    model_config = ConfigDict(extra="forbid")

    modules: dict[str, bool] = Field(
        default_factory=dict,
        description="Module key -> enabled flag",
    )
    flow_mode: str = Field(
        default="hybrid",
        description="api-first, code-first, or hybrid",
    )
    default_protocols: list[str] = Field(
        default_factory=list,
        description="Default API protocols for pipeline runs",
    )
    algolia_enabled: bool = False
    sandbox_backend: str = Field(
        default="external",
        description="external, docker, or prism",
    )


class ModuleInfo(BaseModel):
    """Module metadata with tier eligibility."""

    model_config = ConfigDict(extra="forbid")

    key: str
    label: str
    min_tier: str
    enabled: bool
    available: bool  # True if user tier meets min_tier


class SettingsResponse(BaseModel):
    """Full settings response."""

    model_config = ConfigDict(extra="forbid")

    settings: PipelineSettings
    modules: list[ModuleInfo] = Field(default_factory=list)


class UpdateSettingsRequest(BaseModel):
    """Request to update pipeline settings."""

    model_config = ConfigDict(extra="forbid")

    modules: dict[str, bool] | None = None
    flow_mode: str | None = None
    default_protocols: list[str] | None = None
    algolia_enabled: bool | None = None
    sandbox_backend: str | None = None


# ---------------------------------------------------------------------------
# In-memory store (production uses persistent storage)
# ---------------------------------------------------------------------------

_settings_store: dict[str, PipelineSettings] = {}


def _get_user_settings(user_id: str) -> PipelineSettings:
    """Get or create settings for a user."""
    if user_id not in _settings_store:
        _settings_store[user_id] = PipelineSettings()
    return _settings_store[user_id]


# ---------------------------------------------------------------------------
# Endpoint handlers
# ---------------------------------------------------------------------------


def handle_get_settings(
    user_id: str = "default",
    user_tier: str = "free",
) -> SettingsResponse:
    """Get current pipeline settings with module availability."""
    settings = _get_user_settings(user_id)
    user_idx = _tier_index(user_tier)

    modules: list[ModuleInfo] = []
    for mod in AVAILABLE_MODULES:
        mod_idx = _tier_index(mod["min_tier"])
        available = user_idx >= mod_idx
        enabled = settings.modules.get(mod["key"], available)
        # Cannot enable if tier is too low
        if not available:
            enabled = False
        modules.append(ModuleInfo(
            key=mod["key"],
            label=mod["label"],
            min_tier=mod["min_tier"],
            enabled=enabled,
            available=available,
        ))

    return SettingsResponse(settings=settings, modules=modules)


def handle_update_settings(
    request: UpdateSettingsRequest,
    user_id: str = "default",
    user_tier: str = "free",
) -> SettingsResponse | dict[str, Any]:
    """Update pipeline settings. Rejects module enables above tier."""
    settings = _get_user_settings(user_id)
    user_idx = _tier_index(user_tier)

    # Validate module toggles against tier
    if request.modules:
        module_min_tiers = {m["key"]: m["min_tier"] for m in AVAILABLE_MODULES}
        for key, enabled in request.modules.items():
            if key not in module_min_tiers:
                return {
                    "status": "error",
                    "error": f"Unknown module: {key}",
                    "status_code": 400,
                }
            if enabled and user_idx < _tier_index(module_min_tiers[key]):
                return {
                    "status": "error",
                    "error": (
                        f"Module '{key}' requires {module_min_tiers[key]} "
                        f"plan or higher. Current tier: {user_tier}"
                    ),
                    "status_code": 402,
                }
        settings.modules.update(request.modules)

    if request.flow_mode is not None:
        if request.flow_mode not in ("api-first", "code-first", "hybrid"):
            return {
                "status": "error",
                "error": f"Invalid flow_mode: {request.flow_mode}",
                "status_code": 400,
            }
        settings.flow_mode = request.flow_mode

    if request.default_protocols is not None:
        settings.default_protocols = request.default_protocols

    if request.algolia_enabled is not None:
        settings.algolia_enabled = request.algolia_enabled

    if request.sandbox_backend is not None:
        settings.sandbox_backend = request.sandbox_backend

    return handle_get_settings(user_id, user_tier)


def handle_get_modules(
    user_tier: str = "free",
) -> list[ModuleInfo]:
    """Get available modules with tier eligibility (no user context)."""
    user_idx = _tier_index(user_tier)
    modules: list[ModuleInfo] = []
    for mod in AVAILABLE_MODULES:
        mod_idx = _tier_index(mod["min_tier"])
        available = user_idx >= mod_idx
        modules.append(ModuleInfo(
            key=mod["key"],
            label=mod["label"],
            min_tier=mod["min_tier"],
            enabled=available,  # Default: enabled if available
            available=available,
        ))
    return modules

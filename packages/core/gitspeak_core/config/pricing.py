"""VeriDoc SaaS pricing plans, feature flags, and tier definitions."""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from typing import Any


class PlanTier(str, enum.Enum):
    """Available subscription tiers."""

    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True)
class PlanLimits:
    """Resource limits per plan."""

    max_repos: int = 1
    max_pages: int = 50
    max_ai_requests_per_month: int = 50
    max_team_members: int = 1
    max_api_calls_per_day: int = 100


@dataclass(frozen=True)
class PlanFeatures:
    """Feature flags for a pricing plan."""

    # Editor
    wysiwyg_editor: bool = False
    markdown_editor: bool = False

    # Git
    git_integration: bool = False
    natural_language_git: bool = False
    branch_management: bool = False

    # Documentation pipeline
    doc_generation: bool = False
    template_library: bool = False
    api_docs: bool = False
    multi_protocol: bool = False

    # Quality
    vale_linting: bool = False
    seo_optimization: bool = False
    geo_optimization: bool = False

    # AI
    ai_review: bool = False
    ai_translation: bool = False

    # Search & retrieval
    rag_test_generation: bool = False
    algolia_search: bool = False

    # i18n
    i18n_system: bool = False

    # Advanced
    custom_branding: bool = False
    sso: bool = False
    audit_log: bool = False
    priority_support: bool = False
    doc_compiler: bool = False


@dataclass
class PricingPlan:
    """Complete plan definition."""

    tier: PlanTier
    name: str
    price_monthly_usd: int
    price_yearly_usd: int
    description: str
    limits: PlanLimits
    features: PlanFeatures
    trial_days: int = 0
    highlight: bool = False


# ---------------------------------------------------------------------------
# Plan definitions
# ---------------------------------------------------------------------------

FREE_PLAN = PricingPlan(
    tier=PlanTier.FREE,
    name="Free",
    price_monthly_usd=0,
    price_yearly_usd=0,
    description="14-day trial with basic documentation features",
    trial_days=14,
    limits=PlanLimits(
        max_repos=1,
        max_pages=50,
        max_ai_requests_per_month=50,
        max_team_members=1,
        max_api_calls_per_day=100,
    ),
    features=PlanFeatures(
        wysiwyg_editor=True,
        markdown_editor=True,
        git_integration=True,
        natural_language_git=True,
    ),
)

STARTER_PLAN = PricingPlan(
    tier=PlanTier.STARTER,
    name="Starter",
    price_monthly_usd=149,
    price_yearly_usd=1490,
    description="For individuals and small projects",
    limits=PlanLimits(
        max_repos=3,
        max_pages=200,
        max_ai_requests_per_month=500,
        max_team_members=3,
        max_api_calls_per_day=1000,
    ),
    features=PlanFeatures(
        wysiwyg_editor=True,
        markdown_editor=True,
        git_integration=True,
        natural_language_git=True,
        branch_management=True,
        doc_generation=True,
        template_library=True,
        vale_linting=True,
    ),
)

PRO_PLAN = PricingPlan(
    tier=PlanTier.PRO,
    name="Pro",
    price_monthly_usd=399,
    price_yearly_usd=3990,
    description="For teams that need full pipeline automation",
    highlight=True,
    limits=PlanLimits(
        max_repos=10,
        max_pages=1000,
        max_ai_requests_per_month=5000,
        max_team_members=10,
        max_api_calls_per_day=10000,
    ),
    features=PlanFeatures(
        wysiwyg_editor=True,
        markdown_editor=True,
        git_integration=True,
        natural_language_git=True,
        branch_management=True,
        doc_generation=True,
        template_library=True,
        api_docs=True,
        vale_linting=True,
        seo_optimization=True,
        geo_optimization=True,
        ai_review=True,
        rag_test_generation=True,
        algolia_search=True,
    ),
)

BUSINESS_PLAN = PricingPlan(
    tier=PlanTier.BUSINESS,
    name="Business",
    price_monthly_usd=799,
    price_yearly_usd=7990,
    description="For organizations with advanced documentation needs",
    limits=PlanLimits(
        max_repos=50,
        max_pages=10000,
        max_ai_requests_per_month=50000,
        max_team_members=50,
        max_api_calls_per_day=100000,
    ),
    features=PlanFeatures(
        wysiwyg_editor=True,
        markdown_editor=True,
        git_integration=True,
        natural_language_git=True,
        branch_management=True,
        doc_generation=True,
        template_library=True,
        api_docs=True,
        vale_linting=True,
        seo_optimization=True,
        geo_optimization=True,
        ai_review=True,
        rag_test_generation=True,
        algolia_search=True,
        custom_branding=True,
    ),
)

ENTERPRISE_PLAN = PricingPlan(
    tier=PlanTier.ENTERPRISE,
    name="Enterprise",
    price_monthly_usd=1499,
    price_yearly_usd=14990,
    description="For large organizations with custom requirements",
    limits=PlanLimits(
        max_repos=0,  # unlimited
        max_pages=0,  # unlimited
        max_ai_requests_per_month=0,  # unlimited
        max_team_members=0,  # unlimited
        max_api_calls_per_day=0,  # unlimited
    ),
    features=PlanFeatures(
        wysiwyg_editor=True,
        markdown_editor=True,
        git_integration=True,
        natural_language_git=True,
        branch_management=True,
        doc_generation=True,
        template_library=True,
        api_docs=True,
        multi_protocol=True,
        vale_linting=True,
        seo_optimization=True,
        geo_optimization=True,
        ai_review=True,
        ai_translation=True,
        i18n_system=True,
        rag_test_generation=True,
        algolia_search=True,
        custom_branding=True,
        sso=True,
        audit_log=True,
        priority_support=True,
        doc_compiler=True,
    ),
)

ALL_PLANS: list[PricingPlan] = [
    FREE_PLAN,
    STARTER_PLAN,
    PRO_PLAN,
    BUSINESS_PLAN,
    ENTERPRISE_PLAN,
]

PLANS_BY_TIER: dict[PlanTier, PricingPlan] = {p.tier: p for p in ALL_PLANS}


def get_plan(tier: PlanTier | str) -> PricingPlan:
    """Return the plan for a given tier."""
    if isinstance(tier, str):
        tier = PlanTier(tier)
    return PLANS_BY_TIER[tier]


def has_feature(tier: PlanTier | str, feature: str) -> bool:
    """Check whether a plan tier has a specific feature enabled."""
    plan = get_plan(tier)
    return getattr(plan.features, feature, False)


def is_trial_expired(
    tier: PlanTier | str,
    signup_timestamp: float,
    current_time: float | None = None,
) -> bool:
    """Return True if the free trial period has expired."""
    plan = get_plan(tier)
    if plan.trial_days <= 0:
        return False
    now = current_time if current_time is not None else time.time()
    elapsed_days = (now - signup_timestamp) / 86400
    return elapsed_days > plan.trial_days


def get_pricing_data() -> list[dict[str, Any]]:
    """Return serializable pricing data for the frontend."""
    result: list[dict[str, Any]] = []
    for plan in ALL_PLANS:
        features_dict = {
            k: v
            for k, v in plan.features.__dict__.items()
            if not k.startswith("_")
        }
        limits_dict = {
            k: v
            for k, v in plan.limits.__dict__.items()
            if not k.startswith("_")
        }
        result.append(
            {
                "tier": plan.tier.value,
                "name": plan.name,
                "price_monthly_usd": plan.price_monthly_usd,
                "price_yearly_usd": plan.price_yearly_usd,
                "description": plan.description,
                "trial_days": plan.trial_days,
                "highlight": plan.highlight,
                "limits": limits_dict,
                "features": features_dict,
            }
        )
    return result

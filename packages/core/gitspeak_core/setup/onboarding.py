"""VeriDoc onboarding wizard -- production-ready question flow.

Collects project configuration through 8 steps:
1. Project name
2. Project type
3. Documentation need level
4. Repository URL
5. Team size
6. API protocols (multi-select)
7. LLM provider preference + API key
8. Integrations (Algolia, etc.)
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class ProjectType(str, enum.Enum):
    """Type of project being documented."""

    WEB_APP = "web_app"
    API_SERVICE = "api_service"
    LIBRARY = "library"
    CLI_TOOL = "cli_tool"
    MOBILE_APP = "mobile_app"
    OTHER = "other"


class DocNeed(str, enum.Enum):
    """Documentation need level."""

    NONE = "none"
    BASIC = "basic"
    STANDARD = "standard"
    FULL = "full"


class LLMProvider(str, enum.Enum):
    """Available LLM providers for SaaS mode."""

    GROQ = "groq"
    DEEPSEEK = "deepseek"
    OPENAI = "openai"


class TeamSize(str, enum.Enum):
    """Team size bracket."""

    SOLO = "solo"
    SMALL = "small"        # 2-5
    MEDIUM = "medium"      # 6-20
    LARGE = "large"        # 21-100
    ENTERPRISE = "enterprise"  # 100+


API_PROTOCOLS = ["rest", "graphql", "grpc", "asyncapi", "websocket"]

SITE_GENERATORS = ["mkdocs", "docusaurus", "hugo", "vitepress", "custom"]


@dataclass
class OnboardingAnswers:
    """Collected answers from the onboarding wizard."""

    # Step 1-5: Basic info
    project_name: str = ""
    project_type: str = ProjectType.WEB_APP.value
    doc_need: str = DocNeed.STANDARD.value
    repo_url: str = ""
    team_size: str = TeamSize.SOLO.value

    # Step 6: API protocols
    api_protocols: list[str] = field(default_factory=list)

    # Step 7: LLM provider
    llm_provider: str = LLMProvider.GROQ.value
    llm_api_key: str = ""

    # Step 8: Integrations
    site_generator: str = "mkdocs"
    enable_algolia: bool = False
    algolia_app_id: str = ""
    algolia_search_key: str = ""
    algolia_index_name: str = ""


@dataclass
class WizardQuestion:
    """A single onboarding question definition."""

    step: int
    id: str
    label: str
    description: str
    input_type: str  # text, select, multi_select, radio, toggle, password
    options: list[dict[str, str]] = field(default_factory=list)
    required: bool = True
    condition: str | None = None  # field.value condition for showing
    default: Any = None


def get_onboarding_questions() -> list[WizardQuestion]:
    """Return the full list of onboarding wizard questions."""
    return [
        # Step 1: Project name
        WizardQuestion(
            step=1,
            id="project_name",
            label="Project name",
            description="What is the name of your project?",
            input_type="text",
            default="",
        ),
        # Step 2: Project type
        WizardQuestion(
            step=2,
            id="project_type",
            label="Project type",
            description="What type of project are you documenting?",
            input_type="select",
            options=[
                {"value": t.value, "label": t.value.replace("_", " ").title()}
                for t in ProjectType
            ],
            default=ProjectType.WEB_APP.value,
        ),
        # Step 3: Documentation need
        WizardQuestion(
            step=3,
            id="doc_need",
            label="Documentation scope",
            description="How comprehensive should the documentation be?",
            input_type="radio",
            options=[
                {"value": "none", "label": "None -- I only need Git features"},
                {"value": "basic", "label": "Basic -- README and guides"},
                {"value": "standard", "label": "Standard -- Full docs site"},
                {"value": "full", "label": "Full -- Docs + API reference + i18n"},
            ],
            default=DocNeed.STANDARD.value,
        ),
        # Step 4: Repository URL
        WizardQuestion(
            step=4,
            id="repo_url",
            label="Repository URL",
            description=(
                "Paste your Git repository URL (GitHub, GitLab, Bitbucket)"
            ),
            input_type="text",
            required=False,
            default="",
        ),
        # Step 5: Team size
        WizardQuestion(
            step=5,
            id="team_size",
            label="Team size",
            description="How many people will use VeriDoc?",
            input_type="select",
            options=[
                {"value": "solo", "label": "Just me"},
                {"value": "small", "label": "2-5 people"},
                {"value": "medium", "label": "6-20 people"},
                {"value": "large", "label": "21-100 people"},
                {"value": "enterprise", "label": "100+ people"},
            ],
            default=TeamSize.SOLO.value,
        ),
        # Step 6: API protocols
        WizardQuestion(
            step=6,
            id="api_protocols",
            label="API protocols",
            description=(
                "Which API protocols does your project use? "
                "Select all that apply."
            ),
            input_type="multi_select",
            options=[
                {"value": "rest", "label": "REST (OpenAPI)"},
                {"value": "graphql", "label": "GraphQL"},
                {"value": "grpc", "label": "gRPC (Protobuf)"},
                {"value": "asyncapi", "label": "AsyncAPI (event-driven)"},
                {"value": "websocket", "label": "WebSocket"},
            ],
            condition="doc_need != none",
            default=[],
        ),
        # Step 7: LLM provider
        WizardQuestion(
            step=7,
            id="llm_provider",
            label="AI provider",
            description=(
                "Choose your preferred LLM provider for AI-powered features "
                "(documentation review, translation, test generation)."
            ),
            input_type="radio",
            options=[
                {
                    "value": "groq",
                    "label": "Groq (recommended -- fast, cost-effective)",
                },
                {"value": "deepseek", "label": "DeepSeek (budget-friendly)"},
                {"value": "openai", "label": "OpenAI (GPT-4o)"},
            ],
            default=LLMProvider.GROQ.value,
        ),
        # Step 7b: LLM API key
        WizardQuestion(
            step=7,
            id="llm_api_key",
            label="API key",
            description="Enter your API key for the selected provider.",
            input_type="password",
            required=False,
            default="",
        ),
        # Step 8: Site generator
        WizardQuestion(
            step=8,
            id="site_generator",
            label="Site generator",
            description="Which static site generator do you use?",
            input_type="select",
            options=[
                {"value": g, "label": g.title()} for g in SITE_GENERATORS
            ],
            condition="doc_need != none",
            default="mkdocs",
        ),
        # Step 8b: Algolia toggle
        WizardQuestion(
            step=8,
            id="enable_algolia",
            label="Algolia search",
            description="Enable Algolia-powered search for your docs site?",
            input_type="toggle",
            condition="doc_need != none",
            default=False,
        ),
        # Step 8c: Algolia app ID (shown if enable_algolia is True)
        WizardQuestion(
            step=8,
            id="algolia_app_id",
            label="Algolia App ID",
            description="Your Algolia application ID",
            input_type="text",
            required=False,
            condition="enable_algolia == true",
            default="",
        ),
        # Step 8d: Algolia search key
        WizardQuestion(
            step=8,
            id="algolia_search_key",
            label="Algolia Search API key",
            description="Your Algolia search-only API key",
            input_type="password",
            required=False,
            condition="enable_algolia == true",
            default="",
        ),
        # Step 8e: Algolia index name
        WizardQuestion(
            step=8,
            id="algolia_index_name",
            label="Algolia index name",
            description="The name of your Algolia search index",
            input_type="text",
            required=False,
            condition="enable_algolia == true",
            default="",
        ),
    ]


def get_recommended_config(answers: OnboardingAnswers) -> dict[str, Any]:
    """Generate a recommended pipeline configuration from onboarding answers.

    Returns a dict suitable for writing to ``client_runtime.yml``.
    """
    config: dict[str, Any] = {
        "project": {
            "name": answers.project_name,
            "type": answers.project_type,
        },
        "documentation": {
            "scope": answers.doc_need,
            "site_generator": answers.site_generator,
        },
        "llm": {
            "provider": answers.llm_provider,
            "backend_preference": _llm_preference(answers.llm_provider),
        },
        "team": {
            "size": answers.team_size,
        },
    }

    if answers.repo_url:
        config["project"]["repo_url"] = answers.repo_url

    # API protocols
    if answers.api_protocols:
        config["api"] = {
            "protocols": answers.api_protocols,
            "multi_protocol": len(answers.api_protocols) > 1,
        }

    # Algolia
    if answers.enable_algolia:
        config["integrations"] = {
            "algolia": {
                "enabled": True,
                "app_id": answers.algolia_app_id,
                "index_name": answers.algolia_index_name,
            },
        }

    # Recommended plan
    config["recommended_plan"] = _recommend_plan(answers)

    return config


def _llm_preference(provider: str) -> list[str]:
    """Return ordered backend preference list based on chosen provider."""
    order = {
        "groq": ["groq", "deepseek", "ollama"],
        "deepseek": ["deepseek", "groq", "ollama"],
        "openai": ["openai", "groq", "deepseek", "ollama"],
    }
    return order.get(provider, ["groq", "deepseek", "ollama"])


def save_onboarding_config(
    answers: OnboardingAnswers,
    user_id: str = "default",
) -> dict[str, Any]:
    """Persist onboarding answers as pipeline settings.

    Converts onboarding answers into pipeline module toggles and
    saves them via the settings API.  Returns the recommended config
    dict (same as ``get_recommended_config``) with an extra
    ``settings_saved: True`` key.
    """
    from gitspeak_core.api.settings import (
        UpdateSettingsRequest,
        handle_update_settings,
    )

    config = get_recommended_config(answers)
    recommended_tier = config.get("recommended_plan", "starter")

    # Build module toggles from answers
    modules: dict[str, bool] = {}
    if answers.doc_need != DocNeed.NONE.value:
        modules["gap_detection"] = True
        modules["normalization"] = True
        modules["snippet_lint"] = True
        modules["fact_checks"] = True
        modules["self_checks"] = True
        modules["lifecycle_management"] = True
        modules["terminology_management"] = True

    if answers.api_protocols:
        modules["drift_detection"] = True
        modules["docs_contract"] = True
        modules["test_assets_generation"] = True

    if answers.doc_need == DocNeed.FULL.value:
        modules["kpi_sla"] = True
        modules["release_pack"] = True
        modules["multilang_examples"] = True
        modules["knowledge_validation"] = True
        modules["rag_optimization"] = True

    # Determine flow mode
    protocols = answers.api_protocols or []
    non_rest = [p for p in protocols if p != "rest"]
    if non_rest:
        flow_mode = "hybrid"
    elif protocols:
        flow_mode = "api-first"
    else:
        flow_mode = "hybrid"

    update_req = UpdateSettingsRequest(
        modules=modules,
        flow_mode=flow_mode,
        default_protocols=protocols,
        algolia_enabled=answers.enable_algolia,
    )

    handle_update_settings(update_req, user_id=user_id, user_tier=recommended_tier)

    config["settings_saved"] = True
    return config


def _recommend_plan(answers: OnboardingAnswers) -> str:
    """Suggest a plan tier based on onboarding answers."""
    if answers.doc_need == DocNeed.NONE.value:
        return "starter"

    protocols = answers.api_protocols or []
    non_rest = [p for p in protocols if p != "rest"]

    if answers.team_size in ("large", "enterprise") or non_rest:
        return "business"

    if (
        answers.enable_algolia
        or answers.doc_need == DocNeed.FULL.value
        or len(protocols) >= 1
    ):
        return "pro"

    return "starter"

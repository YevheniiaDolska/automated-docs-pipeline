#!/usr/bin/env python3
"""Tests for VeriDoc SaaS platform alignment.

Covers:
- Feature flags (rag_test_generation, algolia_search)
- Free trial expiration
- Onboarding wizard questions
- Pipeline API endpoints (RAG tests, Algolia widget)
- LLM provider settings (groq/deepseek defaults, no local_only block)
- Expanded RunPipelineRequest with protocols
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "packages" / "core") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "packages" / "core"))


# ============================================================================
# Pricing & feature flags
# ============================================================================


class TestPlanTiers:
    """Verify plan definitions and feature flags."""

    def test_free_plan_exists(self):
        from gitspeak_core.config.pricing import FREE_PLAN, PlanTier

        assert FREE_PLAN.tier == PlanTier.FREE
        assert FREE_PLAN.price_monthly_usd == 0

    def test_free_plan_has_trial_days(self):
        from gitspeak_core.config.pricing import FREE_PLAN

        assert FREE_PLAN.trial_days == 14

    def test_free_plan_limits(self):
        from gitspeak_core.config.pricing import FREE_PLAN

        assert FREE_PLAN.limits.max_repos == 1
        assert FREE_PLAN.limits.max_pages == 50
        assert FREE_PLAN.limits.max_ai_requests_per_month == 50

    def test_free_plan_no_rag(self):
        from gitspeak_core.config.pricing import has_feature

        assert has_feature("free", "rag_test_generation") is False

    def test_free_plan_no_algolia(self):
        from gitspeak_core.config.pricing import has_feature

        assert has_feature("free", "algolia_search") is False

    def test_starter_plan_no_rag(self):
        from gitspeak_core.config.pricing import has_feature

        assert has_feature("starter", "rag_test_generation") is False

    def test_pro_plan_has_rag(self):
        from gitspeak_core.config.pricing import has_feature

        assert has_feature("pro", "rag_test_generation") is True

    def test_pro_plan_has_algolia(self):
        from gitspeak_core.config.pricing import has_feature

        assert has_feature("pro", "algolia_search") is True

    def test_business_plan_has_rag(self):
        from gitspeak_core.config.pricing import has_feature

        assert has_feature("business", "rag_test_generation") is True

    def test_business_plan_has_algolia(self):
        from gitspeak_core.config.pricing import has_feature

        assert has_feature("business", "algolia_search") is True

    def test_enterprise_plan_has_all_features(self):
        from gitspeak_core.config.pricing import ENTERPRISE_PLAN

        feats = ENTERPRISE_PLAN.features
        assert feats.rag_test_generation is True
        assert feats.algolia_search is True
        assert feats.sso is True
        assert feats.audit_log is True
        assert feats.multi_protocol is True

    def test_all_plans_count(self):
        from gitspeak_core.config.pricing import ALL_PLANS

        assert len(ALL_PLANS) == 5

    def test_get_plan_by_string(self):
        from gitspeak_core.config.pricing import PlanTier, get_plan

        plan = get_plan("pro")
        assert plan.tier == PlanTier.PRO

    def test_get_plan_by_enum(self):
        from gitspeak_core.config.pricing import PlanTier, get_plan

        plan = get_plan(PlanTier.ENTERPRISE)
        assert plan.name == "Enterprise"


class TestTrialExpiration:
    """Verify free trial time limit logic."""

    def test_trial_not_expired_within_14_days(self):
        from gitspeak_core.config.pricing import is_trial_expired

        now = time.time()
        signup = now - (13 * 86400)  # 13 days ago
        assert is_trial_expired("free", signup, current_time=now) is False

    def test_trial_expired_after_14_days(self):
        from gitspeak_core.config.pricing import is_trial_expired

        now = time.time()
        signup = now - (15 * 86400)  # 15 days ago
        assert is_trial_expired("free", signup, current_time=now) is True

    def test_trial_not_applicable_for_paid_plans(self):
        from gitspeak_core.config.pricing import is_trial_expired

        now = time.time()
        signup = now - (365 * 86400)  # 1 year ago
        assert is_trial_expired("pro", signup, current_time=now) is False
        assert is_trial_expired("enterprise", signup, current_time=now) is False

    def test_trial_boundary_exactly_14_days(self):
        from gitspeak_core.config.pricing import is_trial_expired

        now = time.time()
        signup = now - (14 * 86400)  # exactly 14 days
        # At exactly 14 days, elapsed == trial_days, not > trial_days
        assert is_trial_expired("free", signup, current_time=now) is False


class TestPricingData:
    """Verify serializable pricing output."""

    def test_get_pricing_data_returns_list(self):
        from gitspeak_core.config.pricing import get_pricing_data

        data = get_pricing_data()
        assert isinstance(data, list)
        assert len(data) == 5

    def test_pricing_data_includes_trial_info(self):
        from gitspeak_core.config.pricing import get_pricing_data

        data = get_pricing_data()
        free_plan = next(p for p in data if p["tier"] == "free")
        assert free_plan["trial_days"] == 14

    def test_pricing_data_includes_features(self):
        from gitspeak_core.config.pricing import get_pricing_data

        data = get_pricing_data()
        pro = next(p for p in data if p["tier"] == "pro")
        assert pro["features"]["rag_test_generation"] is True
        assert pro["features"]["algolia_search"] is True


# ============================================================================
# Settings
# ============================================================================


class TestLLMSettings:
    """Verify LLM provider settings for SaaS mode."""

    def test_local_only_defaults_false(self):
        from gitspeak_core.config.settings import LLMSettings

        settings = LLMSettings()
        assert settings.local_only is False

    def test_default_backend_preference(self):
        from gitspeak_core.config.settings import LLMSettings

        settings = LLMSettings()
        assert settings.llm_backend_preference == [
            "groq",
            "deepseek",
            "ollama",
        ]

    def test_no_codex_or_claude_in_default_preference(self):
        from gitspeak_core.config.settings import LLMSettings

        settings = LLMSettings()
        for backend in settings.llm_backend_preference:
            assert backend not in ("codex", "claude")

    def test_groq_api_key_empty_by_default(self):
        from gitspeak_core.config.settings import LLMSettings

        settings = LLMSettings()
        assert settings.groq_api_key.get_secret_value() == ""

    def test_active_backend_falls_back_to_ollama(self):
        from gitspeak_core.config.settings import LLMSettings

        settings = LLMSettings()
        # No API keys set, so falls through to ollama
        assert settings.get_active_backend() == "ollama"

    def test_active_backend_with_groq_key(self):
        from pydantic import SecretStr

        from gitspeak_core.config.settings import LLMSettings

        settings = LLMSettings(groq_api_key=SecretStr("gsk_test123"))
        assert settings.get_active_backend() == "groq"

    def test_local_only_forces_ollama(self):
        from pydantic import SecretStr

        from gitspeak_core.config.settings import LLMSettings

        settings = LLMSettings(
            local_only=True,
            groq_api_key=SecretStr("gsk_test123"),
        )
        assert settings.get_active_backend() == "ollama"

    def test_veriops_settings_are_local_only(self):
        from gitspeak_core.config.settings import get_veriops_settings

        settings = get_veriops_settings()
        assert settings.llm.local_only is True
        assert settings.llm.llm_backend_preference == ["ollama"]


# ============================================================================
# Onboarding wizard
# ============================================================================


class TestOnboardingQuestions:
    """Verify expanded onboarding wizard."""

    def test_total_questions_at_least_10(self):
        from gitspeak_core.setup.onboarding import get_onboarding_questions

        questions = get_onboarding_questions()
        assert len(questions) >= 10

    def test_api_protocols_question_exists(self):
        from gitspeak_core.setup.onboarding import get_onboarding_questions

        questions = get_onboarding_questions()
        ids = [q.id for q in questions]
        assert "api_protocols" in ids

    def test_llm_provider_question_exists(self):
        from gitspeak_core.setup.onboarding import get_onboarding_questions

        questions = get_onboarding_questions()
        ids = [q.id for q in questions]
        assert "llm_provider" in ids

    def test_algolia_toggle_exists(self):
        from gitspeak_core.setup.onboarding import get_onboarding_questions

        questions = get_onboarding_questions()
        ids = [q.id for q in questions]
        assert "enable_algolia" in ids

    def test_api_protocols_is_multi_select(self):
        from gitspeak_core.setup.onboarding import get_onboarding_questions

        questions = get_onboarding_questions()
        proto_q = next(q for q in questions if q.id == "api_protocols")
        assert proto_q.input_type == "multi_select"
        assert len(proto_q.options) == 5

    def test_llm_provider_default_is_groq(self):
        from gitspeak_core.setup.onboarding import get_onboarding_questions

        questions = get_onboarding_questions()
        llm_q = next(q for q in questions if q.id == "llm_provider")
        assert llm_q.default == "groq"


class TestOnboardingConfig:
    """Verify recommended config generation from answers."""

    def test_basic_config(self):
        from gitspeak_core.setup.onboarding import (
            OnboardingAnswers,
            get_recommended_config,
        )

        answers = OnboardingAnswers(
            project_name="TestProject",
            project_type="api_service",
            doc_need="standard",
        )
        config = get_recommended_config(answers)
        assert config["project"]["name"] == "TestProject"
        assert config["documentation"]["scope"] == "standard"
        assert config["llm"]["provider"] == "groq"

    def test_config_with_protocols(self):
        from gitspeak_core.setup.onboarding import (
            OnboardingAnswers,
            get_recommended_config,
        )

        answers = OnboardingAnswers(
            project_name="API",
            api_protocols=["rest", "graphql"],
        )
        config = get_recommended_config(answers)
        assert config["api"]["protocols"] == ["rest", "graphql"]
        assert config["api"]["multi_protocol"] is True

    def test_config_with_algolia(self):
        from gitspeak_core.setup.onboarding import (
            OnboardingAnswers,
            get_recommended_config,
        )

        answers = OnboardingAnswers(
            project_name="Docs",
            enable_algolia=True,
            algolia_app_id="APPID",
            algolia_index_name="docs_index",
        )
        config = get_recommended_config(answers)
        assert config["integrations"]["algolia"]["enabled"] is True
        assert config["integrations"]["algolia"]["app_id"] == "APPID"

    def test_recommend_pro_for_algolia(self):
        from gitspeak_core.setup.onboarding import (
            OnboardingAnswers,
            get_recommended_config,
        )

        answers = OnboardingAnswers(
            project_name="Docs",
            enable_algolia=True,
        )
        config = get_recommended_config(answers)
        assert config["recommended_plan"] == "pro"

    def test_recommend_business_for_multi_protocol(self):
        from gitspeak_core.setup.onboarding import (
            OnboardingAnswers,
            get_recommended_config,
        )

        answers = OnboardingAnswers(
            project_name="API",
            api_protocols=["rest", "graphql"],
        )
        config = get_recommended_config(answers)
        assert config["recommended_plan"] == "business"


# ============================================================================
# Pipeline API endpoints
# ============================================================================


class TestRunPipelineRequest:
    """Verify expanded pipeline request handling."""

    def test_protocols_in_request(self):
        from gitspeak_core.api.pipeline import RunPipelineRequest

        req = RunPipelineRequest(
            repo_path="/tmp/repo",
            protocols=["rest", "graphql"],
        )
        assert req.protocols == ["rest", "graphql"]

    def test_api_protocols_alias(self):
        from gitspeak_core.api.pipeline import RunPipelineRequest

        req = RunPipelineRequest(
            repo_path="/tmp/repo",
            api_protocols=["grpc"],
        )
        assert req.api_protocols == ["grpc"]

    def test_algolia_fields(self):
        from gitspeak_core.api.pipeline import RunPipelineRequest

        req = RunPipelineRequest(
            repo_path="/tmp/repo",
            algolia_enabled=True,
            algolia_config={"app_id": "X", "index": "Y"},
        )
        assert req.algolia_enabled is True
        assert req.algolia_config["app_id"] == "X"

    def test_sandbox_backend_field(self):
        from gitspeak_core.api.pipeline import RunPipelineRequest

        req = RunPipelineRequest(
            repo_path="/tmp/repo",
            sandbox_backend="external",
        )
        assert req.sandbox_backend == "external"

    def test_handle_run_pipeline(self):
        from gitspeak_core.api.pipeline import (
            RunPipelineRequest,
            handle_run_pipeline,
        )

        req = RunPipelineRequest(
            repo_path="/tmp/repo",
            protocols=["rest", "graphql"],
            algolia_enabled=True,
            sandbox_backend="docker",
        )
        resp = handle_run_pipeline(req, user_tier="pro")
        assert resp.status == "ok"
        assert "rest, graphql" in resp.message
        assert "Algolia" in resp.message
        assert "docker" in resp.message


class TestRagTestEndpoint:
    """Verify RAG test generation feature gate and request handling."""

    def test_rag_blocked_on_free_tier(self):
        from gitspeak_core.api.pipeline import RagTestRequest, handle_rag_test_generate

        req = RagTestRequest(
            repo_path="/tmp/repo",
            description="Test login flow",
        )
        resp = handle_rag_test_generate(req, user_tier="free")
        assert resp.status == "error"
        assert "rag_test_generation" in resp.error

    def test_rag_blocked_on_starter_tier(self):
        from gitspeak_core.api.pipeline import RagTestRequest, handle_rag_test_generate

        req = RagTestRequest(
            repo_path="/tmp/repo",
            description="Test login flow",
        )
        resp = handle_rag_test_generate(req, user_tier="starter")
        assert resp.status == "error"

    def test_rag_index_blocked_on_free_tier(self):
        from gitspeak_core.api.pipeline import (
            RagTestIndexRequest,
            handle_rag_test_index,
        )

        req = RagTestIndexRequest(repo_path="/tmp/repo")
        resp = handle_rag_test_index(req, user_tier="free")
        assert resp.status == "error"

    def test_rag_request_validation(self):
        from gitspeak_core.api.pipeline import RagTestRequest

        req = RagTestRequest(
            repo_path="/tmp/repo",
            test_dir="tests",
            description="Test webhook retry",
            category="test",
            top_k=3,
        )
        assert req.top_k == 3
        assert req.category == "test"


class TestAlgoliaWidgetEndpoint:
    """Verify Algolia widget generation feature gate and request handling."""

    def test_algolia_blocked_on_free_tier(self):
        from gitspeak_core.api.pipeline import (
            AlgoliaWidgetRequest,
            handle_algolia_widget,
        )

        req = AlgoliaWidgetRequest(
            generator="mkdocs",
            app_id="APPID",
            search_key="KEY",
            index_name="docs",
        )
        resp = handle_algolia_widget(req, user_tier="free")
        assert resp.status == "error"
        assert "algolia_search" in resp.error

    def test_algolia_blocked_on_starter_tier(self):
        from gitspeak_core.api.pipeline import (
            AlgoliaWidgetRequest,
            handle_algolia_widget,
        )

        req = AlgoliaWidgetRequest(
            generator="mkdocs",
            app_id="APPID",
            search_key="KEY",
            index_name="docs",
        )
        resp = handle_algolia_widget(req, user_tier="starter")
        assert resp.status == "error"

    def test_algolia_request_validation(self):
        from gitspeak_core.api.pipeline import AlgoliaWidgetRequest

        req = AlgoliaWidgetRequest(
            generator="docusaurus",
            app_id="68IGGT3CVI",
            search_key="12bd532b0a8c",
            index_name="veridoc_docs",
            output_dir="/tmp/widgets",
        )
        assert req.generator == "docusaurus"
        assert req.output_dir == "/tmp/widgets"


class TestFeatureGateHelper:
    """Verify the internal feature gate check function."""

    def test_gate_returns_none_for_allowed(self):
        from gitspeak_core.api.pipeline import _check_feature_gate

        result = _check_feature_gate("pro", "rag_test_generation")
        assert result is None

    def test_gate_returns_error_for_denied(self):
        from gitspeak_core.api.pipeline import _check_feature_gate

        result = _check_feature_gate("free", "rag_test_generation")
        assert result is not None
        assert result["status_code"] == 402
        assert "rag_test_generation" in result["error"]

    def test_gate_returns_error_for_nonexistent_feature(self):
        from gitspeak_core.api.pipeline import _check_feature_gate

        result = _check_feature_gate("enterprise", "nonexistent_feature")
        assert result is not None
        assert result["status_code"] == 402

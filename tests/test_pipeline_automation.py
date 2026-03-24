#!/usr/bin/env python3
"""Tests for VeriDoc 3-phase pipeline, automation, and settings.

Covers:
- 3-phase pipeline orchestration (Discovery, Generation, Quality)
- PhaseResult model and response structure
- Automation schedule CRUD + tier gating
- Settings CRUD + module tier enforcement
- Module registry completeness
- Onboarding -> settings persistence
- Pricing alignment (i18n, multi_protocol, doc_compiler Enterprise-only)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "packages" / "core") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "packages" / "core"))


# ============================================================================
# Pipeline models
# ============================================================================


class TestPipelineModels:
    """Verify expanded pipeline request/response models."""

    def test_run_pipeline_request_has_modules(self):
        from gitspeak_core.api.pipeline import RunPipelineRequest

        req = RunPipelineRequest(
            repo_path="/tmp/repo",
            modules={"gap_detection": True, "i18n_sync": False},
        )
        assert req.modules["gap_detection"] is True
        assert req.modules["i18n_sync"] is False

    def test_run_pipeline_request_has_flow_mode(self):
        from gitspeak_core.api.pipeline import RunPipelineRequest

        req = RunPipelineRequest(
            repo_path="/tmp/repo",
            flow_mode="api-first",
        )
        assert req.flow_mode == "api-first"

    def test_phase_result_model(self):
        from gitspeak_core.api.pipeline import PhaseResult

        phase = PhaseResult(
            name="gap_detection",
            status="ok",
            duration_seconds=1.23,
        )
        assert phase.name == "gap_detection"
        assert phase.status == "ok"
        assert phase.error is None

    def test_phase_result_with_error(self):
        from gitspeak_core.api.pipeline import PhaseResult

        phase = PhaseResult(
            name="consolidate_reports",
            status="error",
            duration_seconds=0.5,
            error="Script not found",
        )
        assert phase.status == "error"
        assert "Script not found" in phase.error

    def test_run_pipeline_response_has_phases(self):
        from gitspeak_core.api.pipeline import PhaseResult, RunPipelineResponse

        resp = RunPipelineResponse(
            status="ok",
            message="Done",
            phases=[
                PhaseResult(name="gap_detection", status="ok"),
                PhaseResult(name="consolidate_reports", status="error", error="fail"),
            ],
            errors=["Consolidation: fail"],
        )
        assert len(resp.phases) == 2
        assert resp.phases[0].status == "ok"
        assert len(resp.errors) == 1


# ============================================================================
# Pipeline feature gating
# ============================================================================


class TestPipelineFeatureGating:
    """Verify module tier enforcement in pipeline."""

    def test_has_feature_starter(self):
        from gitspeak_core.api.pipeline import _has_feature

        assert _has_feature("starter", "gap_detection") is True
        assert _has_feature("starter", "drift_detection") is False

    def test_has_feature_pro(self):
        from gitspeak_core.api.pipeline import _has_feature

        assert _has_feature("pro", "drift_detection") is True
        assert _has_feature("pro", "knowledge_validation") is False

    def test_has_feature_business(self):
        from gitspeak_core.api.pipeline import _has_feature

        assert _has_feature("business", "knowledge_validation") is True
        assert _has_feature("business", "i18n_sync") is False

    def test_has_feature_enterprise(self):
        from gitspeak_core.api.pipeline import _has_feature

        assert _has_feature("enterprise", "i18n_sync") is True
        assert _has_feature("enterprise", "doc_compiler") is True

    def test_is_enabled_respects_override(self):
        from gitspeak_core.api.pipeline import _is_enabled

        # Signature: _is_enabled(module_key, user_tier, overrides)
        # Tier allows it, but override disables it
        assert _is_enabled("gap_detection", "starter", {"gap_detection": False}) is False
        # Tier allows it and override enables it
        assert _is_enabled("gap_detection", "starter", {"gap_detection": True}) is True

    def test_is_enabled_blocks_low_tier(self):
        from gitspeak_core.api.pipeline import _is_enabled

        # Tier too low, even with override True
        assert _is_enabled("i18n_sync", "starter", {"i18n_sync": True}) is False


# ============================================================================
# Automation schedule CRUD
# ============================================================================


class TestAutomationSchedules:
    """Verify automation schedule endpoints."""

    def test_list_empty_for_free(self):
        from gitspeak_core.api.pipeline import handle_list_schedules

        resp = handle_list_schedules(user_tier="free")
        assert resp.schedules == []

    def test_create_blocked_for_starter(self):
        from gitspeak_core.api.pipeline import (
            AutomationSchedule,
            handle_create_schedule,
        )

        sched = AutomationSchedule(name="Weekly", cron="0 3 * * 1")
        result = handle_create_schedule(sched, user_tier="starter")
        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert result["status_code"] == 402

    def test_create_and_list_for_pro(self):
        from gitspeak_core.api.pipeline import (
            AutomationSchedule,
            _schedules,
            handle_create_schedule,
            handle_list_schedules,
        )

        # Clear store
        _schedules.clear()

        sched = AutomationSchedule(name="Weekly docs", cron="0 3 * * 1")
        created = handle_create_schedule(sched, user_tier="pro")
        assert isinstance(created, AutomationSchedule)
        assert created.id.startswith("sched_")
        assert created.name == "Weekly docs"

        listed = handle_list_schedules(user_tier="pro")
        assert len(listed.schedules) == 1

    def test_delete_schedule(self):
        from gitspeak_core.api.pipeline import (
            AutomationSchedule,
            _schedules,
            handle_create_schedule,
            handle_delete_schedule,
        )

        _schedules.clear()
        sched = AutomationSchedule(name="Nightly", cron="0 0 * * *")
        created = handle_create_schedule(sched, user_tier="pro")
        assert isinstance(created, AutomationSchedule)

        result = handle_delete_schedule(created.id, user_tier="pro")
        assert result["status"] == "ok"
        assert len(_schedules) == 0

    def test_trigger_disabled_schedule(self):
        from gitspeak_core.api.pipeline import (
            AutomationSchedule,
            _schedules,
            handle_create_schedule,
            handle_trigger_schedule,
        )

        _schedules.clear()
        sched = AutomationSchedule(name="Off", cron="0 0 * * *", enabled=False)
        created = handle_create_schedule(sched, user_tier="pro")
        assert isinstance(created, AutomationSchedule)

        resp = handle_trigger_schedule(created.id, user_tier="pro")
        assert resp.status == "error"
        assert "disabled" in resp.message


# ============================================================================
# Settings CRUD
# ============================================================================


class TestSettingsCRUD:
    """Verify settings endpoints."""

    def test_get_default_settings(self):
        from gitspeak_core.api.settings import _settings_store, handle_get_settings

        _settings_store.clear()
        resp = handle_get_settings(user_id="test1", user_tier="starter")
        assert resp.settings.flow_mode == "hybrid"
        assert len(resp.modules) > 0

    def test_module_availability_by_tier(self):
        from gitspeak_core.api.settings import _settings_store, handle_get_settings

        _settings_store.clear()
        resp = handle_get_settings(user_id="test2", user_tier="starter")
        mods = {m.key: m for m in resp.modules}

        # Starter modules are available
        assert mods["gap_detection"].available is True
        # Pro modules are not available for starter
        assert mods["drift_detection"].available is False
        # Enterprise modules are not available
        assert mods["i18n_sync"].available is False

    def test_update_modules_within_tier(self):
        from gitspeak_core.api.settings import (
            UpdateSettingsRequest,
            _settings_store,
            handle_update_settings,
        )

        _settings_store.clear()
        req = UpdateSettingsRequest(modules={"gap_detection": False})
        resp = handle_update_settings(req, user_id="test3", user_tier="starter")
        assert not isinstance(resp, dict)  # Not an error
        mods = {m.key: m for m in resp.modules}
        assert mods["gap_detection"].enabled is False

    def test_update_modules_above_tier_rejected(self):
        from gitspeak_core.api.settings import (
            UpdateSettingsRequest,
            _settings_store,
            handle_update_settings,
        )

        _settings_store.clear()
        req = UpdateSettingsRequest(modules={"i18n_sync": True})
        resp = handle_update_settings(req, user_id="test4", user_tier="starter")
        assert isinstance(resp, dict)
        assert resp["status"] == "error"
        assert resp["status_code"] == 402

    def test_update_flow_mode(self):
        from gitspeak_core.api.settings import (
            UpdateSettingsRequest,
            _settings_store,
            handle_update_settings,
        )

        _settings_store.clear()
        req = UpdateSettingsRequest(flow_mode="api-first")
        resp = handle_update_settings(req, user_id="test5", user_tier="pro")
        assert not isinstance(resp, dict)
        assert resp.settings.flow_mode == "api-first"

    def test_update_invalid_flow_mode(self):
        from gitspeak_core.api.settings import (
            UpdateSettingsRequest,
            _settings_store,
            handle_update_settings,
        )

        _settings_store.clear()
        req = UpdateSettingsRequest(flow_mode="invalid")
        resp = handle_update_settings(req, user_id="test6", user_tier="pro")
        assert isinstance(resp, dict)
        assert resp["status_code"] == 400

    def test_get_modules_list(self):
        from gitspeak_core.api.settings import handle_get_modules

        modules = handle_get_modules(user_tier="enterprise")
        assert len(modules) > 15
        # All should be available for enterprise
        for mod in modules:
            assert mod.available is True


# ============================================================================
# Module registry completeness
# ============================================================================


class TestModuleRegistry:
    """Verify module registry is consistent between pipeline and settings."""

    def test_settings_modules_match_pipeline(self):
        from gitspeak_core.api.pipeline import MODULE_MIN_TIER
        from gitspeak_core.api.settings import AVAILABLE_MODULES

        settings_keys = {m["key"] for m in AVAILABLE_MODULES}
        pipeline_keys = set(MODULE_MIN_TIER.keys())

        # Every settings module should be in pipeline
        assert settings_keys.issubset(pipeline_keys), (
            f"Settings modules not in pipeline: {settings_keys - pipeline_keys}"
        )

    def test_min_tiers_match(self):
        from gitspeak_core.api.pipeline import MODULE_MIN_TIER
        from gitspeak_core.api.settings import AVAILABLE_MODULES

        for mod in AVAILABLE_MODULES:
            pipeline_tier = MODULE_MIN_TIER.get(mod["key"])
            assert pipeline_tier == mod["min_tier"], (
                f"Tier mismatch for {mod['key']}: "
                f"pipeline={pipeline_tier}, settings={mod['min_tier']}"
            )


# ============================================================================
# Onboarding -> Settings persistence
# ============================================================================


class TestOnboardingSettingsPersistence:
    """Verify onboarding saves to settings."""

    def test_save_onboarding_config(self):
        from gitspeak_core.api.settings import _settings_store
        from gitspeak_core.setup.onboarding import (
            OnboardingAnswers,
            save_onboarding_config,
        )

        _settings_store.clear()

        answers = OnboardingAnswers(
            project_name="TestAPI",
            project_type="api_service",
            doc_need="full",
            api_protocols=["rest", "graphql"],
            enable_algolia=True,
        )

        config = save_onboarding_config(answers, user_id="onboard_test")
        assert config["settings_saved"] is True
        assert config["recommended_plan"] in ("pro", "business", "enterprise")

        # Verify settings were persisted
        from gitspeak_core.api.settings import handle_get_settings

        resp = handle_get_settings(
            user_id="onboard_test",
            user_tier=config["recommended_plan"],
        )
        assert resp.settings.algolia_enabled is True
        assert "rest" in resp.settings.default_protocols


# ============================================================================
# Pricing alignment
# ============================================================================


class TestPricingAlignment:
    """Verify i18n, multi_protocol, doc_compiler are Enterprise-only."""

    def test_business_no_i18n(self):
        from gitspeak_core.config.pricing import has_feature

        assert has_feature("business", "i18n_system") is False

    def test_business_no_multi_protocol(self):
        from gitspeak_core.config.pricing import has_feature

        assert has_feature("business", "multi_protocol") is False

    def test_business_no_doc_compiler(self):
        from gitspeak_core.config.pricing import has_feature

        assert has_feature("business", "doc_compiler") is False

    def test_enterprise_has_i18n(self):
        from gitspeak_core.config.pricing import has_feature

        assert has_feature("enterprise", "i18n_system") is True

    def test_enterprise_has_multi_protocol(self):
        from gitspeak_core.config.pricing import has_feature

        assert has_feature("enterprise", "multi_protocol") is True

    def test_enterprise_has_doc_compiler(self):
        from gitspeak_core.config.pricing import has_feature

        assert has_feature("enterprise", "doc_compiler") is True

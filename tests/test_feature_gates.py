#!/usr/bin/env python3
"""Integration tests for license feature gates across pipeline scripts."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.license_gate import (
    COMMUNITY_FEATURES,
    PLAN_FEATURES,
    LicenseInfo,
    _community_license,
    reset_cache,
)


@pytest.fixture(autouse=True)
def _reset_cache():
    reset_cache()
    yield
    reset_cache()


def _make_license(plan: str, **overrides) -> LicenseInfo:
    """Create a LicenseInfo for testing."""
    features = dict(PLAN_FEATURES.get(plan, COMMUNITY_FEATURES))
    from scripts.license_gate import PLAN_PROTOCOLS
    protocols = list(PLAN_PROTOCOLS.get(plan, ["rest"]))
    kwargs = {
        "valid": True,
        "plan": plan,
        "client_id": f"test-{plan}",
        "features": features,
        "protocols": protocols,
        "max_docs": 0,
        "offline_grace_days": 7,
        "expires_at": time.time() + 86400 * 365,
        "days_remaining": 365,
        "error": "",
    }
    kwargs.update(overrides)
    return LicenseInfo(**kwargs)


# -- Degraded mode (community) ------------------------------------------------


class TestDegradedMode:
    """Test that community mode provides basic functionality."""

    def test_community_has_markdown_lint(self):
        lic = _community_license()
        assert lic.features.get("markdown_lint") is True

    def test_community_has_frontmatter(self):
        lic = _community_license()
        assert lic.features.get("frontmatter_validation") is True

    def test_community_has_geo_report_only(self):
        lic = _community_license()
        assert lic.features.get("seo_geo_report_only") is True

    def test_community_no_scoring(self):
        lic = _community_license()
        assert lic.features.get("seo_geo_scoring", False) is False

    def test_community_no_drift(self):
        lic = _community_license()
        assert lic.features.get("drift_detection", False) is False

    def test_community_no_pdf(self):
        lic = _community_license()
        assert lic.features.get("executive_audit_pdf", False) is False

    def test_community_no_protocols(self):
        lic = _community_license()
        assert lic.protocols == []


# -- Pilot tier ----------------------------------------------------------------


class TestPilotTier:
    def test_pilot_basic_features(self):
        lic = _make_license("pilot")
        assert lic.features["markdown_lint"] is True
        assert lic.features["glossary_sync"] is True
        assert lic.features["lifecycle_management"] is True

    def test_pilot_no_scoring(self):
        lic = _make_license("pilot")
        assert lic.features["seo_geo_scoring"] is False

    def test_pilot_no_api_first(self):
        lic = _make_license("pilot")
        assert lic.features["api_first_flow"] is False

    def test_pilot_no_consolidated(self):
        lic = _make_license("pilot")
        assert lic.features["consolidated_reports"] is False

    def test_pilot_rest_only(self):
        lic = _make_license("pilot")
        assert lic.protocols == ["rest"]


# -- Professional tier ---------------------------------------------------------


class TestProfessionalTier:
    def test_professional_has_scoring(self):
        lic = _make_license("professional")
        assert lic.features["seo_geo_scoring"] is True

    def test_professional_has_api_first(self):
        lic = _make_license("professional")
        assert lic.features["api_first_flow"] is True

    def test_professional_has_drift(self):
        lic = _make_license("professional")
        assert lic.features["drift_detection"] is True

    def test_professional_has_kpi(self):
        lic = _make_license("professional")
        assert lic.features["kpi_wall_sla"] is True

    def test_professional_has_test_assets(self):
        lic = _make_license("professional")
        assert lic.features["test_assets_generation"] is True

    def test_professional_has_consolidated(self):
        lic = _make_license("professional")
        assert lic.features["consolidated_reports"] is True

    def test_professional_has_multi_protocol(self):
        lic = _make_license("professional")
        assert lic.features["multi_protocol_pipeline"] is True

    def test_professional_has_knowledge_prep(self):
        lic = _make_license("professional")
        assert lic.features["knowledge_modules"] is True

    def test_professional_has_pdf(self):
        lic = _make_license("professional")
        assert lic.features["executive_audit_pdf"] is True

    def test_professional_has_i18n(self):
        lic = _make_license("professional")
        assert lic.features["i18n_system"] is True

    def test_professional_no_faiss_retrieval(self):
        lic = _make_license("professional")
        assert lic.features["faiss_retrieval"] is False


# -- Enterprise tier -----------------------------------------------------------


class TestEnterpriseTier:
    def test_enterprise_all_features(self):
        lic = _make_license("enterprise")
        for feature, enabled in lic.features.items():
            assert enabled is True, f"Enterprise should have {feature} enabled"

    def test_enterprise_all_protocols(self):
        lic = _make_license("enterprise")
        for proto in ["rest", "graphql", "grpc", "asyncapi", "websocket"]:
            assert proto in lic.protocols

    def test_enterprise_has_pdf(self):
        lic = _make_license("enterprise")
        assert lic.features["executive_audit_pdf"] is True

    def test_enterprise_has_i18n(self):
        lic = _make_license("enterprise")
        assert lic.features["i18n_system"] is True

    def test_enterprise_has_knowledge_graph(self):
        lic = _make_license("enterprise")
        assert lic.features["knowledge_graph"] is True


# -- Feature gate integration -------------------------------------------------


class TestFeatureGateIntegration:
    """Test that feature gates work correctly with the check() function."""

    def test_check_respects_plan(self):
        from scripts.license_gate import check

        pilot = _make_license("pilot")
        pro = _make_license("professional")
        ent = _make_license("enterprise")

        # drift_detection: pilot=no, pro=yes, ent=yes
        assert check("drift_detection", pilot) is False
        assert check("drift_detection", pro) is True
        assert check("drift_detection", ent) is True

        # multi_protocol_pipeline: pilot=no, pro=yes, ent=yes
        assert check("multi_protocol_pipeline", pilot) is False
        assert check("multi_protocol_pipeline", pro) is True
        assert check("multi_protocol_pipeline", ent) is True

    def test_require_blocks_correctly(self):
        from scripts.license_gate import require

        pilot = _make_license("pilot")

        with pytest.raises(SystemExit):
            require("api_first_flow", pilot)

        with pytest.raises(SystemExit):
            require("consolidated_reports", pilot)

        # Basic features should pass
        result = require("markdown_lint", pilot)
        assert result.plan == "pilot"

    def test_protocol_gate(self):
        from scripts.license_gate import check_protocol, require_protocol

        pilot = _make_license("pilot")
        ent = _make_license("enterprise")

        assert check_protocol("rest", pilot) is True
        assert check_protocol("graphql", pilot) is False
        assert check_protocol("graphql", ent) is True

        with pytest.raises(SystemExit):
            require_protocol("grpc", pilot)

        result = require_protocol("grpc", ent)
        assert result.plan == "enterprise"


# -- Tier upgrade path ---------------------------------------------------------


class TestUpgradePath:
    """Verify that each tier adds features incrementally."""

    def test_professional_superset_of_pilot(self):
        pilot = PLAN_FEATURES["pilot"]
        pro = PLAN_FEATURES["professional"]

        for feature, enabled in pilot.items():
            if enabled:
                assert pro.get(feature) is True, \
                    f"Professional should include pilot feature: {feature}"

    def test_enterprise_superset_of_professional(self):
        pro = PLAN_FEATURES["professional"]
        ent = PLAN_FEATURES["enterprise"]

        for feature, enabled in pro.items():
            if enabled:
                assert ent.get(feature) is True, \
                    f"Enterprise should include professional feature: {feature}"

    def test_community_subset_of_pilot(self):
        community = COMMUNITY_FEATURES
        pilot = PLAN_FEATURES["pilot"]

        for feature, enabled in community.items():
            if enabled:
                assert pilot.get(feature) is True, \
                    f"Pilot should include community feature: {feature}"

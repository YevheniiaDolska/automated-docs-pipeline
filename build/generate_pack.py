#!/usr/bin/env python3
"""Server-side capability pack builder for VeriOps.

Extracts proprietary scoring weights, prompt templates, and policy
thresholds, then encrypts them into a binary pack for client deployment.

This script runs on the VeriOps server only -- never distributed to clients.

Usage:
  python3 build/generate_pack.py \\
    --client-id acme-corp \\
    --plan enterprise \\
    --license-key VDOC-ENT-acme-a8f3b2c1 \\
    --days 90 \\
    --output docsops/.capability_pack.enc
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.pack_runtime import (
    _aes_gcm_encrypt,
    build_pack_file,
    derive_pack_key,
)


# -- Scoring weight extraction -------------------------------------------------
# These are the proprietary values currently hardcoded in various scripts.
# The pack builder extracts them so they can be delivered encrypted.


def _extract_geo_rules() -> dict[str, Any]:
    """Extract GEO rules from seo_geo_optimizer.py defaults."""
    return {
        "first_para_max_words": 60,
        "max_words_without_fact": 200,
        "meta_desc_min_chars": 50,
        "meta_desc_max_chars": 160,
        "min_heading_words": 3,
        "generic_headings": [
            "overview", "introduction", "configuration", "setup",
            "details", "information", "general", "notes", "summary",
        ],
        "definition_patterns": [
            r"\bis\b", r"\benables?\b", r"\bprovides?\b", r"\ballows?\b",
            r"\bcreates?\b", r"\bprocesses?\b", r"\bexecutes?\b",
        ],
        "fact_patterns": [
            r"\d+", r"`[^`]+`", r"\bdefault\b", r"\bport\b",
            r"\bversion\b", r"\bMB\b", r"\bGB\b", r"\bms\b",
            r"```", r"\bhttp[s]?://\b",
        ],
    }


def _extract_geo_rules_by_locale() -> dict[str, dict[str, Any]]:
    """Extract locale-specific GEO rule overrides."""
    return {
        "ru": {
            "first_para_max_words": 80,
            "meta_desc_max_chars": 200,
            "generic_headings": [
                "overview", "introduction", "configuration", "setup",
                "details", "information", "general", "notes", "summary",
                "obzor", "vvedenie", "nastroyka", "nastrojka",
                "podrobnosti", "informatsiya", "obshchee", "zametki",
            ],
        },
        "de": {
            "first_para_max_words": 70,
            "meta_desc_max_chars": 180,
            "generic_headings": [
                "overview", "introduction", "configuration", "setup",
                "details", "information", "general", "notes", "summary",
                "ueberblick", "uebersicht", "einleitung", "konfiguration",
                "einrichtung", "details", "informationen", "allgemein",
            ],
        },
    }


def _extract_kpi_weights() -> dict[str, Any]:
    """Extract KPI quality score formula weights from generate_kpi_wall.py."""
    return {
        "metadata_weight": 0.35,
        "stale_weight": 0.30,
        "gap_penalty_per_item": 3,
        "gap_penalty_cap": 25,
    }


def _extract_seo_rules() -> dict[str, Any]:
    """Extract SEO rules from seo_geo_optimizer.py defaults."""
    return {
        "title_min_chars": 10,
        "title_max_chars": 70,
        "max_url_depth": 4,
        "min_internal_links": 1,
        "max_image_without_alt_pct": 0,
        "min_content_words": 100,
        "max_line_length_for_mobile": 180,
        "check_mobile_line_length": True,
        "max_long_lines_before_warning": 30,
    }


def _extract_audit_weights() -> dict[str, float]:
    """Extract 7-pillar audit score weights from generate_audit_scorecard.py."""
    return {
        "api_coverage": 0.22,
        "example_reliability": 0.20,
        "freshness": 0.14,
        "drift": 0.12,
        "layers": 0.12,
        "terminology": 0.10,
        "retrieval": 0.10,
        "hallucination_deduction": 0.08,
    }


def _extract_risk_weights() -> dict[str, float]:
    """Extract risk index weights from generate_audit_scorecard.py."""
    return {
        "undocumented": 0.30,
        "stale": 0.20,
        "drift": 0.20,
        "example_gap": 0.20,
        "terminology": 0.10,
    }


def _extract_grade_thresholds() -> dict[str, int]:
    """Extract grade letter thresholds from generate_audit_scorecard.py."""
    return {
        "A": 90,
        "B": 80,
        "C": 70,
        "D": 60,
    }


def _extract_tier_classification() -> dict[str, Any]:
    """Extract tier classification logic from consolidate_reports.py."""
    return {
        "tier1_categories": [
            "breaking_change", "api_endpoint", "authentication",
        ],
        "tier1_sources": ["drift", "sla"],
        "tier2_categories": [
            "signature_change", "new_function", "removed_function",
            "webhook", "config_option", "env_var", "cli_command", "stale_doc",
        ],
        "stale_doc_threshold_days": 90,
    }


def _extract_sla_thresholds() -> dict[str, Any]:
    """Extract SLA breach thresholds from evaluate_kpi_sla.py."""
    return {
        "min_quality_score": 70,
        "max_stale_pct": 20.0,
        "max_high_gaps": 5,
        "max_drift_items": 0,
    }


def _extract_prompt_templates() -> dict[str, str]:
    """Extract prompt templates for documentation generation."""
    return {
        "stripe_quality_formula": (
            "Opening paragraph (The Hook): State what the feature/API does "
            "in one sentence. Explain the primary use case. Set expectations.\n"
            "Immediate value (The Code): Show a complete, working example.\n"
            "Progressive disclosure: Simple case first (80%), common "
            "variations (15%), advanced scenarios (5%)."
        ),
        "geo_optimization": (
            "First paragraph: under 60 words, include definition pattern "
            "(is, enables, provides, allows). Descriptive headings only. "
            "Concrete facts every 200 words."
        ),
        "self_verification": (
            "Execute all code blocks. Verify shell commands. "
            "Fact-check assertions. Check internal consistency. "
            "Walk through as user."
        ),
    }


def _extract_policy_rules() -> dict[str, Any]:
    """Extract policy rule sets."""
    return {
        "drift_severity": {
            "breaking_change": "critical",
            "removed_function": "high",
            "signature_change": "high",
            "new_function": "medium",
            "config_option": "medium",
            "stale_doc": "low",
        },
        "quality_gates": {
            "vale_blocks_commit": True,
            "markdownlint_blocks_commit": True,
            "frontmatter_blocks_commit": True,
            "seo_geo_blocks_commit": True,
            "knowledge_modules_blocks_commit": True,
        },
    }


# -- Pack building -------------------------------------------------------------


def build_pack_payload(plan: str, days: int) -> dict[str, Any]:
    """Build the full pack payload for a given plan tier."""
    now = time.time()
    return {
        "plan": plan,
        "version": "1.0.0",
        "created_at": now,
        "expires_at": now + (days * 86400),
        "sections": {
            "scoring": {
                "geo_rules": _extract_geo_rules(),
                "geo_rules_by_locale": _extract_geo_rules_by_locale(),
                "seo_rules": _extract_seo_rules(),
                "kpi_weights": _extract_kpi_weights(),
                "audit_weights": _extract_audit_weights(),
                "risk_weights": _extract_risk_weights(),
                "grade_thresholds": _extract_grade_thresholds(),
                "sla_thresholds": _extract_sla_thresholds(),
            },
            "priority": _extract_tier_classification(),
            "prompts": _extract_prompt_templates(),
            "policies": _extract_policy_rules(),
        },
    }


def encrypt_pack(payload: dict[str, Any], license_key: str, client_id: str) -> bytes:
    """Encrypt pack payload and return binary pack file."""
    plaintext = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    aes_key = derive_pack_key(license_key, client_id)
    nonce, ciphertext, tag = _aes_gcm_encrypt(aes_key, plaintext)
    return build_pack_file(nonce, tag, ciphertext)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build VeriOps capability pack")
    parser.add_argument("--client-id", required=True, help="Client identifier")
    parser.add_argument("--plan", choices=["pilot", "professional", "enterprise"], required=True)
    parser.add_argument("--license-key", required=True, help="Client license key for encryption")
    parser.add_argument("--days", type=int, default=90, help="Pack validity in days")
    parser.add_argument("--output", default="docsops/.capability_pack.enc", help="Output pack file")
    args = parser.parse_args()

    payload = build_pack_payload(args.plan, args.days)
    pack_data = encrypt_pack(payload, args.license_key, args.client_id)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(pack_data)

    print(f"[pack] Capability pack written to {out_path}")
    print(f"[pack] Client: {args.client_id} | Plan: {args.plan} | Valid: {args.days} days")
    print(f"[pack] Size: {len(pack_data)} bytes")
    print(f"[pack] Sections: {', '.join(payload['sections'].keys())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

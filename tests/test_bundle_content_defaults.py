from __future__ import annotations

from pathlib import Path

import yaml


def _base_profile(output_dir: Path, commercial_package: str, plan: str) -> dict:
    return {
        "client": {"id": f"bundle-{commercial_package}", "company_name": "Bundle Co"},
        "bundle": {
            "output_dir": str(output_dir),
            "base_policy_pack": "minimal",
            "style_guide": "google",
            "include_scripts": [],
            "include_docs": [],
            "include_paths": [],
            "llm": {
                "codex_instructions_source": "AGENTS.md",
                "claude_instructions_source": "CLAUDE.md",
                "inject_managed_block": True,
                "docsops_root_in_client_repo": "docsops",
            },
        },
        "runtime": {
            "security": {
                "hardening_profile": "relaxed",
                "anti_tamper_enforced": False,
                "require_protected_modules": False,
                "allow_dev_bypass": True,
            }
        },
        "licensing": {
            "commercial_package": commercial_package,
            "plan": plan,
            "days": 30,
            "require_signed_jwt": False,
            "manual_jwt_path": "",
        },
    }


def test_create_bundle_includes_full_templates_and_consistency_assets(
    tmp_path: Path, monkeypatch
) -> None:
    from scripts import build_client_bundle as mod

    profile = _base_profile(tmp_path / "out", "full", "professional")
    profile_path = tmp_path / "full.client.yml"
    profile_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")

    copied_docs: list[str] = []
    copied_paths: list[str] = []
    monkeypatch.setattr(mod, "copy_into_bundle", lambda rel, root: copied_docs.append(str(rel)))
    monkeypatch.setattr(mod, "copy_path_into_bundle", lambda rel, root: copied_paths.append(str(rel)))

    mod.create_bundle(profile_path)

    assert "docs/_variables.yml" in copied_docs
    assert "glossary.yml" in copied_docs
    assert "templates/how-to.md" in copied_paths
    assert ".husky" in copied_paths
    assert ".pre-commit-config.yaml" in copied_paths
    assert "templates/legal/LICENSE-COMMERCIAL.template.md" not in copied_paths


def test_create_bundle_uses_pilot_template_subset(tmp_path: Path, monkeypatch) -> None:
    from scripts import build_client_bundle as mod

    profile = _base_profile(tmp_path / "out", "pilot", "pilot")
    profile_path = tmp_path / "pilot.client.yml"
    profile_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")

    copied_paths: list[str] = []
    monkeypatch.setattr(mod, "copy_into_bundle", lambda rel, root: None)
    monkeypatch.setattr(mod, "copy_path_into_bundle", lambda rel, root: copied_paths.append(str(rel)))

    mod.create_bundle(profile_path)

    assert "templates/how-to.md" in copied_paths
    assert "templates/plg-persona-guide.md" not in copied_paths

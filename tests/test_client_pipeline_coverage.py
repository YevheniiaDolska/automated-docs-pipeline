from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestBuildClientBundle:
    def test_deep_merge_and_cron_day(self) -> None:
        from scripts import build_client_bundle as mod

        merged = mod.deep_merge({"a": {"b": 1}, "x": 1}, {"a": {"c": 2}, "x": 2})
        assert merged["a"] == {"b": 1, "c": 2}
        assert merged["x"] == 2
        assert mod._cron_day_to_number("monday") == "1"
        with pytest.raises(ValueError):
            mod._cron_day_to_number("funday")

    def test_upsert_managed_block_insert_and_replace(self, tmp_path: Path) -> None:
        from scripts import build_client_bundle as mod

        fp = tmp_path / "AGENTS.md"
        fp.write_text("hello\n", encoding="utf-8")
        block = mod.build_managed_instruction_block("docsops")

        mod.upsert_managed_block(fp, block)
        first = fp.read_text(encoding="utf-8")
        assert mod.MANAGED_START in first

        mod.upsert_managed_block(fp, block.replace("DocsOps", "DocsOpsX"))
        second = fp.read_text(encoding="utf-8")
        assert "DocsOpsX" in second

    def test_create_bundle_end_to_end(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import build_client_bundle as mod

        repo = tmp_path / "repo"
        repo.mkdir()
        monkeypatch.setattr(mod, "REPO_ROOT", repo)

        (repo / "policy_packs").mkdir(parents=True)
        (repo / "policy_packs" / "minimal.yml").write_text("docs_contract:\n  interface_patterns: ['^api/']\n  doc_patterns: ['^docs/']\n", encoding="utf-8")
        (repo / "scripts").mkdir()
        (repo / "scripts" / "gap_detector.py").write_text("print('ok')\n", encoding="utf-8")
        (repo / "scripts" / "auto_fix_pr_docs.py").write_text("print('ok')\n", encoding="utf-8")
        (repo / "scripts" / "finalize_docs_gate.py").write_text("print('ok')\n", encoding="utf-8")
        (repo / "scripts" / "license_gate.py").write_text("print('ok')\n", encoding="utf-8")
        (repo / "scripts" / "pack_runtime.py").write_text("print('ok')\n", encoding="utf-8")
        (repo / "scripts" / "check_updates.py").write_text("print('ok')\n", encoding="utf-8")
        (repo / "scripts" / "rollback.py").write_text("print('ok')\n", encoding="utf-8")
        (repo / "docsops" / "keys").mkdir(parents=True)
        (repo / "docsops" / "keys" / "veriops-licensing.pub").write_text("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=\n", encoding="utf-8")
        (repo / "docs").mkdir()
        (repo / "docs" / "operations").mkdir(parents=True)
        (repo / "docs" / "operations" / "UNIFIED_CLIENT_CONFIG.md").write_text("x\n", encoding="utf-8")
        (repo / "templates" / "legal").mkdir(parents=True)
        (repo / "templates" / "legal" / "LICENSE-COMMERCIAL.template.md").write_text("Licensed to {{COMPANY_NAME}} {{CLIENT_ID}} {{DATE_ISSUED}}\n", encoding="utf-8")
        (repo / "templates" / "legal" / "NOTICE.template.md").write_text("NOTICE {{COMPANY_NAME}}\n", encoding="utf-8")
        (repo / "AGENTS.md").write_text("Agent base\n", encoding="utf-8")
        (repo / "CLAUDE.md").write_text("Claude base\n", encoding="utf-8")

        profile = {
            "client": {"id": "acme", "company_name": "Acme Inc", "contact_email": "a@b.c"},
            "runtime": {
                "preferred_llm": "codex",
                "docs_root": "docs",
                "output_targets": ["sphinx"],
                "modules": {"gap_detection": True},
                "custom_tasks": {"weekly": [], "on_demand": []},
            },
            "private_tuning": {"weekly_stale_days": 180},
            "bundle": {
                "output_dir": "generated/client_bundles",
                "base_policy_pack": "minimal",
                "policy_overrides": {"docs_contract": {"doc_patterns": ["^manual/"]}},
                "include_scripts": ["scripts/gap_detector.py"],
                "include_docs": ["docs/operations/UNIFIED_CLIENT_CONFIG.md"],
                "include_paths": ["templates/legal"],
                "style_guide": "hybrid",
                "llm": {
                    "inject_managed_block": True,
                    "docsops_root_in_client_repo": "docsops",
                    "codex_instructions_source": "AGENTS.md",
                    "claude_instructions_source": "CLAUDE.md",
                },
                "automation": {
                    "weekly_gap_report": {
                        "enabled": True,
                        "day_of_week": "tuesday",
                        "time_24h": "10:15",
                        "since_days": 9,
                    }
                },
            },
        }
        profile_path = repo / "profiles" / "clients" / "acme.client.yml"
        profile_path.parent.mkdir(parents=True)
        profile_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")

        out = mod.create_bundle(profile_path)

        assert out.exists()
        runtime = yaml.safe_load((out / "config" / "client_runtime.yml").read_text(encoding="utf-8"))
        assert runtime["project"]["client_id"] == "acme"
        assert runtime["pipeline"]["weekly_stale_days"] == 180
        assert runtime["api_first"]["openapi_version"] == "3.0.3"
        assert runtime["api_first"]["manual_overrides_path"] == ""
        assert runtime["api_first"]["regression_snapshot_path"] == ""
        assert runtime["api_first"]["sync_playground_endpoint"] is True
        assert runtime["api_first"]["external_mock"]["enabled"] is True
        assert runtime["api_first"]["external_mock"]["provider"] == "postman"
        assert runtime["terminology"]["enabled"] is True
        assert runtime["terminology"]["glossary_path"] == "glossary.yml"
        assert runtime["retrieval_eval"]["enabled"] is True
        assert runtime["retrieval_eval"]["top_k"] == 3
        assert runtime["knowledge_graph"]["enabled"] is True
        assert runtime["knowledge_graph"]["output_path"] == "docs/assets/knowledge-graph.jsonld"
        assert runtime["git_sync"]["enabled"] is False
        assert runtime["git_sync"]["remote"] == "origin"
        assert runtime["pr_autofix"]["enabled"] is False
        assert runtime["pr_autofix"]["workflow_filename"] == "docsops-pr-autofix.yml"
        selected = yaml.safe_load((out / "policy_packs" / "selected.yml").read_text(encoding="utf-8"))
        assert selected["docs_contract"]["doc_patterns"] == ["^manual/"]
        assert (out / "scripts" / "gap_detector.py").exists()
        assert (out / "docs" / "operations" / "UNIFIED_CLIENT_CONFIG.md").exists()
        assert (out / "templates" / "legal" / "NOTICE.template.md").exists()
        assert (out / "ops" / "run_weekly_docsops.sh").exists()
        assert "DocsOps Managed Local Workflow" in (out / "AGENTS.md").read_text(encoding="utf-8")
        assert "BasedOnStyles = Google, Microsoft" in (out / ".vale.ini").read_text(encoding="utf-8")
        # Licensing infrastructure
        assert (out / "scripts" / "license_gate.py").exists()
        assert (out / "scripts" / "pack_runtime.py").exists()
        assert (out / "scripts" / "check_updates.py").exists()
        assert (out / "scripts" / "rollback.py").exists()
        assert (out / "docsops" / "keys" / "veriops-licensing.pub").exists()
        assert (out / "docsops" / "license.jwt").exists()
        bundle_info = yaml.safe_load((out / "BUNDLE_INFO.yml").read_text(encoding="utf-8"))
        assert "licensing" in bundle_info
        assert bundle_info["licensing"]["public_key"] == "docsops/keys/veriops-licensing.pub"
        env_template = (out / ".env.docsops.local.template").read_text(encoding="utf-8")
        assert "VERIOPS_LICENSE_KEY" in env_template
        assert "VERIOPS_LICENSE_PLAN" in env_template

    def test_licensing_auto_generates_jwt_with_private_key(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """When Ed25519 private key exists, JWT is auto-generated in the bundle."""
        from scripts import build_client_bundle as mod

        repo = tmp_path / "repo"
        repo.mkdir()
        monkeypatch.setattr(mod, "REPO_ROOT", repo)

        # Minimal repo structure
        (repo / "policy_packs").mkdir()
        (repo / "policy_packs" / "minimal.yml").write_text("docs_contract: {}\n", encoding="utf-8")
        (repo / "scripts").mkdir()
        for s in ["finalize_docs_gate.py", "license_gate.py", "pack_runtime.py", "check_updates.py", "rollback.py"]:
            (repo / "scripts" / s).write_text("print('ok')\n", encoding="utf-8")
        (repo / "templates" / "legal").mkdir(parents=True)
        (repo / "templates" / "legal" / "LICENSE-COMMERCIAL.template.md").write_text("{{COMPANY_NAME}}\n", encoding="utf-8")
        (repo / "templates" / "legal" / "NOTICE.template.md").write_text("{{COMPANY_NAME}}\n", encoding="utf-8")
        (repo / "AGENTS.md").write_text("x\n", encoding="utf-8")
        (repo / "CLAUDE.md").write_text("x\n", encoding="utf-8")

        # Generate a real keypair
        import base64
        build_dir = str(ROOT / "build")
        if build_dir not in sys.path:
            sys.path.insert(0, build_dir)
        try:
            from generate_license import _generate_ed25519_keypair
        except ImportError:
            pytest.skip("No Ed25519 library available")

        priv_key, pub_key = _generate_ed25519_keypair()
        keys_dir = repo / "docsops" / "keys"
        keys_dir.mkdir(parents=True)
        (keys_dir / "veriops-licensing.key").write_bytes(base64.b64encode(priv_key))
        (keys_dir / "veriops-licensing.pub").write_bytes(base64.b64encode(pub_key))

        profile = {
            "client": {"id": "testcorp", "company_name": "Test Corp"},
            "licensing": {"plan": "enterprise", "days": 90},
            "bundle": {"output_dir": "out"},
        }
        profile_path = repo / "profile.yml"
        profile_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")

        out = mod.create_bundle(profile_path)

        jwt_file = out / "docsops" / "license.jwt"
        assert jwt_file.exists()
        jwt_text = jwt_file.read_text(encoding="utf-8").strip()
        # A real JWT has 3 dot-separated parts
        assert jwt_text.count(".") == 2, f"Expected JWT format, got: {jwt_text[:80]}"
        # Verify it validates
        from scripts.license_gate import _parse_jwt_parts
        _, claims, _ = _parse_jwt_parts(jwt_text)
        assert claims["sub"] == "testcorp"
        assert claims["plan"] == "enterprise"

    def test_build_vale_invalid_style(self, tmp_path: Path) -> None:
        from scripts import build_client_bundle as mod

        with pytest.raises(ValueError):
            mod.build_vale_config({"bundle": {"style_guide": "invalid"}}, tmp_path)


class TestProvisionClientRepo:
    def test_copy_bundle_to_repo(self, tmp_path: Path) -> None:
        from scripts import provision_client_repo as mod

        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "A.txt").write_text("1", encoding="utf-8")
        repo = tmp_path / "client"
        repo.mkdir()
        target = repo / "docsops"
        target.mkdir()
        (target / "old.txt").write_text("old", encoding="utf-8")

        installed = mod.copy_bundle_to_repo(bundle, repo, "docsops")
        assert installed.exists()
        assert (installed / "A.txt").exists()
        assert not (installed / "old.txt").exists()

    def test_run_scheduler_install_modes(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import provision_client_repo as mod

        repo = tmp_path / "repo"
        (repo / "docsops" / "ops").mkdir(parents=True)
        (repo / "docsops" / "ops" / "install_cron_weekly.sh").write_text("#!/bin/bash\n", encoding="utf-8")
        (repo / "docsops" / "ops" / "install_windows_task.ps1").write_text("Write-Host ok\n", encoding="utf-8")

        calls: list[list[str]] = []

        def fake_run(cmd: list[str], cwd: str, check: bool) -> SimpleNamespace:
            calls.append(cmd)
            assert cwd == str(repo)
            assert check is True
            return SimpleNamespace(returncode=0)

        monkeypatch.setattr(mod.subprocess, "run", fake_run)

        mod.run_scheduler_install(repo, "docsops", "none")
        mod.run_scheduler_install(repo, "docsops", "linux")
        mod.run_scheduler_install(repo, "docsops", "windows")

        assert calls[0][0] == "bash"
        assert calls[1][0] == "powershell"

        with pytest.raises(ValueError):
            mod.run_scheduler_install(repo, "docsops", "bad")

    def test_main_happy_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        from scripts import provision_client_repo as mod

        profile = tmp_path / "client.yml"
        profile.write_text("client: {id: a, company_name: b}\n", encoding="utf-8")
        repo = tmp_path / "repo"
        repo.mkdir()
        built = tmp_path / "built"
        built.mkdir()

        monkeypatch.setattr(mod, "create_bundle", lambda p: built)

        captured: dict[str, object] = {}

        def fake_copy(bundle_root: Path, client_repo: Path, docsops_dir: str) -> Path:
            captured["copy"] = (bundle_root, client_repo, docsops_dir)
            target = client_repo / docsops_dir
            target.mkdir(parents=True, exist_ok=True)
            return target

        monkeypatch.setattr(mod, "copy_bundle_to_repo", fake_copy)
        monkeypatch.setattr(mod, "run_scheduler_install", lambda c, d, m: captured.update({"scheduler": m}))
        monkeypatch.setattr(mod, "_collect_secret_inputs", lambda c, d: None)
        monkeypatch.setattr(sys, "argv", ["x", "--client", str(profile), "--client-repo", str(repo), "--install-scheduler", "none"])

        rc = mod.main()
        assert rc == 0
        assert captured["scheduler"] == "none"
        assert "bundle installed" in capsys.readouterr().out

    def test_dotenv_and_gitignore_helpers(self, tmp_path: Path) -> None:
        from scripts import provision_client_repo as mod

        repo = tmp_path / "repo"
        repo.mkdir()
        dotenv = repo / ".env"
        gitignore = repo / ".gitignore"
        gitignore.write_text("node_modules/\n", encoding="utf-8")

        mod._write_dotenv(dotenv, {"POSTMAN_API_KEY": "abc", "POSTMAN_WORKSPACE_ID": "ws"})
        loaded = mod._read_dotenv(dotenv)
        assert loaded["POSTMAN_API_KEY"] == "abc"
        assert loaded["POSTMAN_WORKSPACE_ID"] == "ws"

        mod._ensure_gitignore_has_env(repo, ".env.docsops.local")
        content = gitignore.read_text(encoding="utf-8")
        assert ".env.docsops.local" in content

    def test_interactive_wizard_and_missing_non_tty(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import provision_client_repo as mod

        args = SimpleNamespace(
            client=None,
            client_repo=None,
            docsops_dir="docsops",
            install_scheduler="none",
            interactive=False,
        )
        monkeypatch.setattr(mod.sys.stdin, "isatty", lambda: False)
        with pytest.raises(ValueError):
            mod._resolve_args(args)

        repo = tmp_path / "repo"
        repo.mkdir()
        profile = "profiles/clients/examples/basic.client.yml"
        answers = iter(["existing", profile, str(repo), "linux", "docsops"])
        monkeypatch.setattr(mod.sys.stdin, "isatty", lambda: True)
        monkeypatch.setattr("builtins.input", lambda *_a, **_k: next(answers))
        args2 = SimpleNamespace(
            client=None,
            client_repo=None,
            docsops_dir="docsops",
            install_scheduler="none",
            interactive=True,
        )
        resolved = mod._resolve_args(args2)
        assert resolved.client == profile
        assert resolved.client_repo == str(repo)
        assert resolved.install_scheduler == "linux"

    def test_apply_integrations_ask_ai(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import provision_client_repo as mod

        repo = tmp_path / "repo"
        (repo / "docsops" / "config").mkdir(parents=True)
        (repo / "docsops" / "scripts").mkdir(parents=True)
        (repo / "docsops" / "scripts" / "configure_ask_ai.py").write_text("print('ok')\n", encoding="utf-8")
        (repo / "docsops" / "scripts" / "install_ask_ai_runtime.py").write_text("print('ok')\n", encoding="utf-8")
        (repo / "docsops" / "config" / "client_runtime.yml").write_text(
            yaml.safe_dump(
                {
                    "integrations": {
                        "ask_ai": {
                            "enabled": True,
                            "auto_configure_on_provision": True,
                            "install_runtime_pack": True,
                            "provider": "openai",
                            "billing_mode": "user-subscription",
                            "model": "gpt-4.1-mini",
                            "base_url": "https://api.openai.com/v1",
                        }
                    }
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        calls: list[list[str]] = []

        def fake_run(cmd: list[str], cwd: str, check: bool) -> SimpleNamespace:
            calls.append(cmd)
            assert cwd == str(repo)
            assert check is True
            return SimpleNamespace(returncode=0)

        monkeypatch.setattr(mod.subprocess, "run", fake_run)
        mod.apply_integrations(repo, "docsops")

        assert len(calls) == 2
        assert "configure_ask_ai.py" in calls[0][1]
        assert "--enable" in calls[0]
        assert "install_ask_ai_runtime.py" in calls[1][1]

    def test_apply_integrations_disabled_noop(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import provision_client_repo as mod

        repo = tmp_path / "repo"
        (repo / "docsops" / "config").mkdir(parents=True)
        (repo / "docsops" / "config" / "client_runtime.yml").write_text(
            yaml.safe_dump(
                {
                    "integrations": {
                        "ask_ai": {
                            "enabled": False,
                            "auto_configure_on_provision": False,
                        }
                    }
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        called = {"n": 0}
        monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: called.update({"n": called["n"] + 1}))
        mod.apply_integrations(repo, "docsops")
        assert called["n"] == 0

    def test_generate_env_checklist(self, tmp_path: Path) -> None:
        from scripts import provision_client_repo as mod

        repo = tmp_path / "repo"
        (repo / "docsops" / "config").mkdir(parents=True)
        (repo / "docsops" / "config" / "client_runtime.yml").write_text(
            yaml.safe_dump(
                {
                    "integrations": {
                        "algolia": {"enabled": True},
                        "ask_ai": {"enabled": True, "provider": "openai"},
                    },
                    "api_first": {
                        "sandbox_backend": "external",
                        "external_mock": {
                            "enabled": True,
                            "provider": "postman",
                            "postman": {
                                "api_key_env": "POSTMAN_API_KEY",
                                "workspace_id_env": "POSTMAN_WORKSPACE_ID",
                                "collection_uid_env": "POSTMAN_COLLECTION_UID",
                                "mock_server_id_env": "POSTMAN_MOCK_SERVER_ID",
                            },
                        },
                    },
                    "pr_autofix": {
                        "enabled": True,
                        "workflow_filename": "docsops-pr-autofix.yml",
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        out = mod.generate_env_checklist(repo, "docsops")
        assert out is not None
        text = out.read_text(encoding="utf-8")
        assert "ALGOLIA_APP_ID" in text
        assert "OPENAI_API_KEY" in text
        assert "POSTMAN_API_KEY" in text
        assert "POSTMAN_WORKSPACE_ID" in text
        assert "POSTMAN_COLLECTION_UID" in text
        assert "docsops-pr-autofix.yml" in text
        assert "DOCSOPS_BOT_TOKEN" in text

    def test_install_pr_autofix_workflow(self, tmp_path: Path) -> None:
        from scripts import provision_client_repo as mod

        repo = tmp_path / "repo"
        (repo / "docsops" / "config").mkdir(parents=True)
        (repo / "docsops" / "config" / "client_runtime.yml").write_text(
            yaml.safe_dump(
                {
                    "paths": {"docs_root": "manuals"},
                    "pr_autofix": {
                        "enabled": True,
                        "require_label": False,
                        "enable_auto_merge": False,
                        "workflow_filename": "docsops-pr-autofix.yml",
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        out = mod.install_pr_autofix_workflow(repo, "docsops")
        assert out is not None
        assert out.exists()
        text = out.read_text(encoding="utf-8")
        assert "name: DocsOps PR Auto Fix" in text
        assert "python3 docsops/scripts/auto_fix_pr_docs.py" in text
        assert "--docs-root \"$DOCSOPS_DOCS_ROOT\"" in text
        assert "git add \"$DOCSOPS_DOCS_ROOT/\"" in text
        assert 'DOCSOPS_DOCS_ROOT: "manuals"' in text

    def test_install_pr_autofix_workflow_disabled(self, tmp_path: Path) -> None:
        from scripts import provision_client_repo as mod

        repo = tmp_path / "repo"
        (repo / "docsops" / "config").mkdir(parents=True)
        (repo / "docsops" / "config" / "client_runtime.yml").write_text(
            yaml.safe_dump(
                {
                    "pr_autofix": {
                        "enabled": False,
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        out = mod.install_pr_autofix_workflow(repo, "docsops")
        assert out is None


class TestAlgoliaWidgetGenerator:
    def test_generate_widget_mkdocs(self, tmp_path: Path) -> None:
        from scripts.generate_algolia_widget import generate_widget

        created = generate_widget("mkdocs", "APP123", "KEY456", "my_index", tmp_path)
        assert "docs/assets/javascripts/algolia-search.js" in created
        assert "docs/stylesheets/algolia-search.css" in created
        assert "docs/_algolia_mkdocs_patch.yml" in created
        patch = (tmp_path / "docs/_algolia_mkdocs_patch.yml").read_text(encoding="utf-8")
        assert "APP123" in patch
        assert "KEY456" in patch
        assert "my_index" in patch

    def test_generate_widget_docusaurus(self, tmp_path: Path) -> None:
        from scripts.generate_algolia_widget import generate_widget

        created = generate_widget("docusaurus", "APP123", "KEY456", "my_index", tmp_path)
        assert "_algolia_docusaurus_patch.js" in created
        text = (tmp_path / "_algolia_docusaurus_patch.js").read_text(encoding="utf-8")
        assert "APP123" in text
        assert "@docusaurus/theme-search-algolia" in text

    def test_generate_widget_hugo(self, tmp_path: Path) -> None:
        from scripts.generate_algolia_widget import generate_widget

        created = generate_widget("hugo", "APP123", "KEY456", "my_index", tmp_path)
        assert "_algolia_hugo_patch.toml" in created
        assert "layouts/partials/algolia-search.html" in created
        html = (tmp_path / "layouts/partials/algolia-search.html").read_text(encoding="utf-8")
        assert "APP123" in html
        assert "instantsearch" in html

    def test_generate_widget_vitepress(self, tmp_path: Path) -> None:
        from scripts.generate_algolia_widget import generate_widget

        created = generate_widget("vitepress", "APP123", "KEY456", "my_index", tmp_path)
        assert "_algolia_vitepress_patch.mts" in created
        text = (tmp_path / "_algolia_vitepress_patch.mts").read_text(encoding="utf-8")
        assert "provider: 'algolia'" in text
        assert "APP123" in text

    def test_generate_widget_custom(self, tmp_path: Path) -> None:
        from scripts.generate_algolia_widget import generate_widget

        created = generate_widget("custom", "APP123", "KEY456", "my_index", tmp_path)
        assert "algolia-search-widget.html" in created
        assert "algolia-search.css" in created
        html = (tmp_path / "algolia-search-widget.html").read_text(encoding="utf-8")
        assert "APP123" in html
        assert "algolia-search-overlay" in html

    def test_generate_widget_unknown_generator(self, tmp_path: Path) -> None:
        from scripts.generate_algolia_widget import generate_widget

        with pytest.raises(ValueError, match="Unknown generator"):
            generate_widget("unknown", "APP123", "KEY456", "my_index", tmp_path)

    def test_supported_generators_list(self) -> None:
        from scripts.generate_algolia_widget import GENERATORS

        assert set(GENERATORS.keys()) == {"mkdocs", "docusaurus", "hugo", "vitepress", "custom"}


class TestApplyAlgoliaWidget:
    def test_algolia_widget_creates_setup_script(self, tmp_path: Path) -> None:
        from scripts import provision_client_repo as mod

        repo = tmp_path / "repo"
        scripts_dir = repo / "docsops" / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "generate_algolia_widget.py").write_text("# placeholder", encoding="utf-8")

        runtime = {
            "paths": {"docs_root": "docs"},
            "integrations": {
                "algolia": {
                    "enabled": True,
                    "site_generator": "docusaurus",
                    "generate_search_widget": True,
                    "app_id_env": "ALGOLIA_APP_ID",
                    "api_key_env": "ALGOLIA_API_KEY",
                    "index_name_env": "ALGOLIA_INDEX_NAME",
                    "index_name_default": "docs",
                },
            },
        }
        mod._apply_algolia_widget(repo, "docsops", runtime)

        helper = scripts_dir / "setup_algolia_widget.sh"
        assert helper.exists()
        text = helper.read_text(encoding="utf-8")
        assert "docusaurus" in text
        assert "ALGOLIA_APP_ID" in text
        assert "generate_algolia_widget.py" in text

    def test_algolia_widget_skips_when_disabled(self, tmp_path: Path) -> None:
        from scripts import provision_client_repo as mod

        repo = tmp_path / "repo"
        scripts_dir = repo / "docsops" / "scripts"
        scripts_dir.mkdir(parents=True)

        runtime = {
            "integrations": {
                "algolia": {"enabled": False},
            },
        }
        mod._apply_algolia_widget(repo, "docsops", runtime)

        helper = scripts_dir / "setup_algolia_widget.sh"
        assert not helper.exists()

    def test_algolia_widget_skips_when_no_script(self, tmp_path: Path) -> None:
        from scripts import provision_client_repo as mod

        repo = tmp_path / "repo"
        (repo / "docsops" / "scripts").mkdir(parents=True)

        runtime = {
            "integrations": {
                "algolia": {
                    "enabled": True,
                    "generate_search_widget": True,
                    "site_generator": "mkdocs",
                },
            },
        }
        mod._apply_algolia_widget(repo, "docsops", runtime)
        assert not (repo / "docsops" / "scripts" / "setup_algolia_widget.sh").exists()

    def test_env_checklist_includes_algolia_widget_info(self, tmp_path: Path) -> None:
        from scripts import provision_client_repo as mod

        repo = tmp_path / "repo"
        (repo / "docsops" / "config").mkdir(parents=True)
        (repo / "docsops" / "config" / "client_runtime.yml").write_text(
            yaml.safe_dump(
                {
                    "integrations": {
                        "algolia": {
                            "enabled": True,
                            "site_generator": "hugo",
                        },
                        "ask_ai": {"enabled": False},
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        out = mod.generate_env_checklist(repo, "docsops")
        assert out is not None
        text = out.read_text(encoding="utf-8")
        assert "hugo" in text
        assert "setup_algolia_widget.sh" in text


class TestWeeklyBatch:
    def test_read_yaml_requires_mapping(self, tmp_path: Path) -> None:
        from scripts import run_weekly_gap_batch as mod

        fp = tmp_path / "a.yml"
        fp.write_text("- 1\n", encoding="utf-8")
        with pytest.raises(ValueError):
            mod._read_yaml(fp)

    def test_resolve_weekly_base_ref_fallback(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import run_weekly_gap_batch as mod

        def fake_run(*args, **kwargs):  # type: ignore[no-untyped-def]
            return SimpleNamespace(stdout="", returncode=0)

        monkeypatch.setattr(mod.subprocess, "run", fake_run)
        assert mod._resolve_weekly_base_ref(tmp_path, 7) == "HEAD~1"

    def test_run_shell_behavior(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import run_weekly_gap_batch as mod

        monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=1))
        with pytest.raises(RuntimeError):
            mod._run_shell("echo test", tmp_path, continue_on_error=False)
        rc = mod._run_shell("echo test", tmp_path, continue_on_error=True)
        assert rc == 1

    def test_run_git_sync_executes_fetch_and_pull(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import run_weekly_gap_batch as mod

        repo = tmp_path / "repo"
        (repo / ".git").mkdir(parents=True)

        calls: list[tuple[str, Path, bool]] = []
        monkeypatch.setattr(
            mod,
            "_run_shell",
            lambda command, cwd, continue_on_error: calls.append((command, cwd, continue_on_error)) or 0,
        )

        mod._run_git_sync(
            tmp_path,
            {
                "enabled": True,
                "repo_path": "repo",
                "remote": "origin",
                "branch": "main",
                "fetch_first": True,
                "rebase": True,
                "autostash": True,
                "continue_on_error": True,
            },
        )

        assert calls[0][0] == "git fetch origin --prune"
        assert calls[1][0] == "git pull --rebase --autostash origin main"
        assert calls[0][1] == repo.resolve()

    def test_main_code_first_and_custom_tasks(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import run_weekly_gap_batch as mod

        repo = tmp_path
        docsops = repo / "docsops"
        scripts_dir = docsops / "scripts"
        (docsops / "config").mkdir(parents=True)
        (docsops / "policy_packs").mkdir(parents=True)
        scripts_dir.mkdir(parents=True)
        (docsops / "policy_packs" / "selected.yml").write_text("docs_contract: {}\n", encoding="utf-8")

        for name in [
            "gap_detector.py",
            "check_docs_contract.py",
            "check_api_sdk_drift.py",
            "normalize_docs.py",
            "lint_code_snippets.py",
            "check_code_examples_smoke.py",
            "sync_project_glossary.py",
            "seo_geo_optimizer.py",
            "doc_layers_validator.py",
            "validate_knowledge_modules.py",
            "generate_knowledge_retrieval_index.py",
            "generate_knowledge_graph_jsonld.py",
            "run_retrieval_evals.py",
            "i18n_sync.py",
            "generate_release_docs_pack.py",
            "generate_kpi_wall.py",
            "evaluate_kpi_sla.py",
            "consolidate_reports.py",
        ]:
            (scripts_dir / name).write_text("print('ok')\n", encoding="utf-8")

        runtime = {
            "docs_flow": {"mode": "code-first"},
            "modules": {
                "gap_detection": True,
                "docs_contract": True,
                "drift_detection": True,
                "normalization": True,
                "snippet_lint": True,
                "self_checks": True,
                "fact_checks": True,
                "knowledge_validation": True,
                "rag_optimization": True,
                "ontology_graph": True,
                "retrieval_evals": True,
                "terminology_management": True,
                "i18n_sync": True,
                "release_pack": True,
                "kpi_sla": True,
            },
            "paths": {"docs_root": "docs"},
            "pipeline": {"weekly_stale_days": 180},
            "custom_tasks": {"weekly": [{"enabled": True, "command": "echo weekly", "continue_on_error": True}]},
        }
        (docsops / "config" / "client_runtime.yml").write_text(yaml.safe_dump(runtime, sort_keys=False), encoding="utf-8")

        ran: list[tuple[str, list[str]]] = []
        custom: list[str] = []

        def fake_run(cmd: list[str], cwd: Path) -> None:
            ran.append(("run", cmd))

        def fake_allow(cmd: list[str], cwd: Path) -> int:
            ran.append(("allow", cmd))
            return 0

        monkeypatch.chdir(repo)
        monkeypatch.setattr(mod, "_resolve_weekly_base_ref", lambda r, s: "abc123")
        monkeypatch.setattr(mod, "_run", fake_run)
        monkeypatch.setattr(mod, "_run_allow_fail", fake_allow)
        monkeypatch.setattr(mod, "_run_shell", lambda command, cwd, continue_on_error: custom.append(command) or 0)
        monkeypatch.setattr(sys, "argv", ["x", "--docsops-root", "docsops", "--reports-dir", "reports", "--since", "7"])

        rc = mod.main()
        assert rc == 0
        assert any("gap_detector.py" in " ".join(cmd) for _, cmd in ran)
        assert any("generate_knowledge_graph_jsonld.py" in " ".join(cmd) for _, cmd in ran)
        assert any("run_retrieval_evals.py" in " ".join(cmd) for _, cmd in ran)
        assert any("consolidate_reports.py" in " ".join(cmd) for _, cmd in ran)
        assert custom == ["echo weekly"]
    def test_main_api_first_branch(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import run_weekly_gap_batch as mod

        repo = tmp_path
        docsops = repo / "docsops"
        scripts_dir = docsops / "scripts"
        (docsops / "config").mkdir(parents=True)
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "run_api_first_flow.py").write_text("print('ok')\n", encoding="utf-8")

        runtime = {
            "docs_flow": {"mode": "api-first"},
            "modules": {},
            "api_first": {
                "enabled": True,
                "project_slug": "proj",
                "notes_path": "notes.md",
                "spec_path": "api/openapi.yaml",
                "spec_tree_path": "api/proj",
                "docs_provider": "mkdocs",
                "docs_spec_target": "docs/assets/api",
                "stubs_output": "generated/stubs.py",
                "max_attempts": 2,
                "auto_remediate": True,
                "verify_user_path": True,
                "mock_base_url": "http://localhost:4010/v1",
                "sandbox_backend": "external",
                "external_mock": {
                    "enabled": True,
                    "provider": "postman",
                    "base_path": "/v1",
                    "postman": {
                        "api_key_env": "POSTMAN_API_KEY",
                        "workspace_id_env": "POSTMAN_WORKSPACE_ID",
                        "collection_uid_env": "POSTMAN_COLLECTION_UID",
                        "mock_server_id_env": "POSTMAN_MOCK_SERVER_ID",
                        "mock_server_name": "demo-mock",
                        "private": True,
                    },
                },
                "sync_playground_endpoint": False,
                "run_docs_lint": True,
                "generate_from_notes": False,
            },
            "custom_tasks": {"weekly": []},
        }
        (docsops / "config" / "client_runtime.yml").write_text(yaml.safe_dump(runtime, sort_keys=False), encoding="utf-8")

        commands: list[list[str]] = []
        monkeypatch.chdir(repo)
        monkeypatch.setattr(mod, "_resolve_weekly_base_ref", lambda r, s: "abc123")
        monkeypatch.setattr(mod, "_run", lambda cmd, cwd: commands.append(cmd))
        monkeypatch.setattr(mod, "_run_allow_fail", lambda cmd, cwd: 0)
        monkeypatch.setattr(sys, "argv", ["x", "--docsops-root", "docsops", "--reports-dir", "reports"])

        rc = mod.main()
        assert rc == 0
        api_cmds = [cmd for cmd in commands if any("run_api_first_flow.py" in p for p in cmd)]
        assert len(api_cmds) == 1
        cmd = api_cmds[0]
        assert "--skip-generate-from-notes" in cmd
        assert "--verify-user-path" in cmd
        assert "--run-docs-lint" in cmd
        assert "--no-sync-playground-endpoint" in cmd
        assert "--sandbox-backend" in cmd and "external" in cmd
        assert "--auto-prepare-external-mock" in cmd
        assert "--external-mock-provider" in cmd and "postman" in cmd
        assert "--external-mock-postman-api-key-env" in cmd
        assert "--external-mock-postman-private" in cmd

    def test_main_api_first_versions_branch(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import run_weekly_gap_batch as mod

        repo = tmp_path
        docsops = repo / "docsops"
        scripts_dir = docsops / "scripts"
        (docsops / "config").mkdir(parents=True)
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "run_api_first_flow.py").write_text("print('ok')\n", encoding="utf-8")

        runtime = {
            "docs_flow": {"mode": "hybrid"},
            "modules": {},
            "api_first": {
                "enabled": True,
                "docs_provider": "mkdocs",
                "max_attempts": 2,
                "versions": [
                    {
                        "project_slug": "proj-v1",
                        "notes_path": "notes-v1.md",
                        "spec_path": "api/openapi-v1.yaml",
                        "spec_tree_path": "api/v1",
                        "docs_spec_target": "docs/assets/api/v1",
                        "stubs_output": "generated/stubs-v1.py",
                        "enabled": True,
                    },
                    {
                        "project_slug": "proj-v2",
                        "notes_path": "notes-v2.md",
                        "spec_path": "api/openapi-v2.yaml",
                        "spec_tree_path": "api/v2",
                        "docs_spec_target": "docs/assets/api/v2",
                        "stubs_output": "generated/stubs-v2.py",
                        "enabled": True,
                    },
                ],
            },
            "custom_tasks": {"weekly": []},
        }
        (docsops / "config" / "client_runtime.yml").write_text(yaml.safe_dump(runtime, sort_keys=False), encoding="utf-8")

        commands: list[list[str]] = []
        monkeypatch.chdir(repo)
        monkeypatch.setattr(mod, "_resolve_weekly_base_ref", lambda r, s: "abc123")
        monkeypatch.setattr(mod, "_run", lambda cmd, cwd: commands.append(cmd))
        monkeypatch.setattr(mod, "_run_allow_fail", lambda cmd, cwd: 0)
        monkeypatch.setattr(sys, "argv", ["x", "--docsops-root", "docsops", "--reports-dir", "reports"])

        rc = mod.main()
        assert rc == 0
        api_cmds = [cmd for cmd in commands if any("run_api_first_flow.py" in p for p in cmd)]
        assert len(api_cmds) == 2
        assert any("proj-v1" in " ".join(cmd) for cmd in api_cmds)
        assert any("proj-v2" in " ".join(cmd) for cmd in api_cmds)

    def test_main_api_first_forwards_overrides_and_regression(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import run_weekly_gap_batch as mod

        repo = tmp_path
        docsops = repo / "docsops"
        scripts_dir = docsops / "scripts"
        (docsops / "config").mkdir(parents=True)
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "run_api_first_flow.py").write_text("print('ok')\n", encoding="utf-8")

        runtime = {
            "docs_flow": {"mode": "api-first"},
            "modules": {},
            "api_first": {
                "enabled": True,
                "project_slug": "proj",
                "notes_path": "notes.md",
                "spec_path": "api/openapi.yaml",
                "spec_tree_path": "api/proj",
                "docs_provider": "mkdocs",
                "docs_spec_target": "docs/assets/api",
                "stubs_output": "generated/stubs.py",
                "openapi_version": "3.1.0",
                "manual_overrides_path": "api/overrides.yml",
                "regression_snapshot_path": "api/.openapi-regression.json",
                "update_regression_snapshot": True,
            },
            "custom_tasks": {"weekly": []},
        }
        (docsops / "config" / "client_runtime.yml").write_text(yaml.safe_dump(runtime, sort_keys=False), encoding="utf-8")

        commands: list[list[str]] = []
        monkeypatch.chdir(repo)
        monkeypatch.setattr(mod, "_resolve_weekly_base_ref", lambda r, s: "abc123")
        monkeypatch.setattr(mod, "_run", lambda cmd, cwd: commands.append(cmd))
        monkeypatch.setattr(mod, "_run_allow_fail", lambda cmd, cwd: 0)
        monkeypatch.setattr(sys, "argv", ["x", "--docsops-root", "docsops", "--reports-dir", "reports"])

        rc = mod.main()
        assert rc == 0
        api_cmds = [cmd for cmd in commands if any("run_api_first_flow.py" in p for p in cmd)]
        assert len(api_cmds) == 1
        cmd = api_cmds[0]
        assert "--openapi-version" in cmd and "3.1.0" in cmd
        assert "--manual-overrides" in cmd and "api/overrides.yml" in cmd
        assert "--regression-snapshot" in cmd and "api/.openapi-regression.json" in cmd
        assert "--update-regression-snapshot" in cmd


class TestOnboardClient:
    def test_onboard_happy_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import onboard_client as mod

        profile = tmp_path / "generated.client.yml"
        profile.write_text(
            yaml.safe_dump(
                {
                    "client": {"id": "acme", "company_name": "Acme"},
                    "runtime": {"docs_flow": {"mode": "code-first"}, "output_targets": ["mkdocs"]},
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        monkeypatch.setattr(
            mod,
            "parse_args",
            lambda: SimpleNamespace(
                client=None,
                client_repo=None,
                docsops_dir="docsops",
                install_scheduler="none",
                yes=True,
            ),
        )

        def fake_resolve(_args: SimpleNamespace) -> SimpleNamespace:
            return SimpleNamespace(
                client=str(profile),
                client_repo=str(tmp_path / "client-repo"),
                docsops_dir="docsops",
                install_scheduler="none",
            )

        monkeypatch.setattr(mod.provision, "_resolve_args", fake_resolve)
        monkeypatch.setattr(mod.provision, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(mod.provision, "execute_provision", lambda _args: 0)

        rc = mod.main()
        assert rc == 0


class TestValidateOpenApiContract:
    def test_validate_missing_fields(self, tmp_path: Path) -> None:
        from scripts import validate_openapi_contract as mod

        spec_path = tmp_path / "openapi.yaml"
        spec_path.write_text("openapi: 3.0.3\n", encoding="utf-8")
        errors = mod.validate({"openapi": "3.0.3"}, spec_path)
        assert any("Missing top-level key: info" in e for e in errors)

    def test_validate_success(self, tmp_path: Path) -> None:
        from scripts import validate_openapi_contract as mod

        tree = tmp_path / "taskstream" / "v1" / "components" / "schemas"
        tree.mkdir(parents=True)
        (tree / "common.yaml").write_text(
            "Base:\n  allOf:\n    - type: object\nPoly:\n  oneOf:\n    - type: string\n",
            encoding="utf-8",
        )
        spec_path = tmp_path / "openapi.yaml"
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "T", "description": "D"},
            "paths": {
                "/x": {
                    "get": {
                        "operationId": "get_x",
                        "tags": ["X"],
                        "summary": "Get",
                        "description": "Get x",
                        "responses": {"200": {"description": "ok"}},
                    }
                }
            },
            "components": {
                "securitySchemes": {"BearerAuth": {"type": "http", "scheme": "bearer"}},
                "responses": {"Error": {"description": "err"}},
                "schemas": {"Base": {"$ref": "./taskstream/v1/components/schemas/common.yaml#/Base"}},
            },
        }
        spec_path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
        assert mod.validate(spec, spec_path) == []

    def test_main_paths(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        from scripts import validate_openapi_contract as mod

        monkeypatch.setattr(sys, "argv", ["x"])
        assert mod.main() == 2

        monkeypatch.setattr(sys, "argv", ["x", str(tmp_path / "missing.yaml")])
        assert mod.main() == 2

        spec = tmp_path / "ok.yaml"
        spec.write_text("openapi: 3.0.3\n", encoding="utf-8")
        monkeypatch.setattr(mod, "load_yaml", lambda p: {})
        monkeypatch.setattr(mod, "validate", lambda s, p: ["bad"])
        monkeypatch.setattr(sys, "argv", ["x", str(spec)])
        assert mod.main() == 1
        assert "failed" in capsys.readouterr().out.lower()


class TestGenerateOpenApiFromPlanningNotes:
    def test_helpers(self) -> None:
        from scripts import generate_openapi_from_planning_notes as mod

        assert mod.pointer_escape("/a~b") == "~1a~0b"
        assert mod.op_id("GET", "/tasks/{task_id}") == "get_tasks_by_task_id"
        assert mod.group_for_path("/projects") == "projects"
        assert mod.group_for_path("/users/me") == "users"
        assert mod.group_for_path("/unknown") == "tasks"
        assert mod.id_param_ref("/tasks/{task_id}")
        assert mod.response_for("POST", "/projects").get("201")
        assert mod.response_for("DELETE", "/projects/{project_id}").get("204")
        assert mod.response_for("GET", "/projects").get("200")
        assert mod.response_for("GET", "/tasks").get("200")
        assert mod.response_for("GET", "/users/me").get("200")
        assert mod.response_for("PATCH", "/x").get("200")
        assert "requestBody" in mod.make_operation("POST", "/tasks", "Create")

    def test_parse_notes_and_main(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import generate_openapi_from_planning_notes as mod

        notes = """
Project: **TaskStream**
Base URL: `http://localhost:4010/v1`
API version: **v1**
- `GET /projects` - List projects
- `POST /projects` - Create project
- `GET /projects` - Duplicate should dedupe
- `GET /users/me` - Who am I
"""
        project, base, version, ops = mod.parse_notes(notes)
        assert project == "TaskStream"
        assert base.endswith("/v1")
        assert version == "v1"
        assert len(ops) == 3

        repo = tmp_path / "repo"
        repo.mkdir()
        monkeypatch.setattr(mod, "__file__", str(repo / "scripts" / "generate_openapi_from_planning_notes.py"))
        (repo / "notes").mkdir()
        (repo / "notes" / "api.md").write_text(notes, encoding="utf-8")
        (repo / "api").mkdir()

        monkeypatch.setattr(sys, "argv", [
            "x",
            "--notes",
            "notes/api.md",
            "--spec",
            "api/openapi.yaml",
            "--spec-tree",
            "api/taskstream",
        ])

        rc = mod.main()
        assert rc == 0
        assert (repo / "api" / "openapi.yaml").exists()
        assert (repo / "api" / "taskstream" / "v1" / "components" / "schemas" / "common.yaml").exists()


class TestRunApiFirstFlow:
    def test_compact_output_and_helpers(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        from scripts import run_api_first_flow as mod

        mod._print_compact_output("\n".join([f"line-{i}" for i in range(50)]), max_lines=10)
        out = capsys.readouterr().out
        assert "omitted" in out

        missing = tmp_path / "missing.txt"
        with pytest.raises(FileNotFoundError):
            mod.ensure_file(missing, "x")

    def test_build_sandbox_page_url(self, tmp_path: Path) -> None:
        from scripts import run_api_first_flow as mod

        (tmp_path / "mkdocs.yml").write_text("site_url: https://docs.example.com\n", encoding="utf-8")
        assert mod.build_sandbox_page_url(tmp_path, "mkdocs").startswith("https://docs.example.com")
        assert mod.build_sandbox_page_url(tmp_path, "docusaurus").endswith("taskstream-api-playground")

    def test_sync_playground_sandbox_url(self, tmp_path: Path) -> None:
        from scripts import run_api_first_flow as mod

        mkdocs = tmp_path / "mkdocs.yml"
        mkdocs.write_text("site_name: Demo\n", encoding="utf-8")
        mod.sync_playground_sandbox_url(tmp_path, "https://sandbox.example.com/v1")
        payload = yaml.safe_load(mkdocs.read_text(encoding="utf-8"))
        assert payload["extra"]["plg"]["api_playground"]["endpoints"]["sandbox_base_url"] == "https://sandbox.example.com/v1"
        assert payload["extra"]["api_playground"]["sandbox_base_url"] == "https://sandbox.example.com/v1"

    def test_self_verify_stub_coverage(self, tmp_path: Path) -> None:
        from scripts import run_api_first_flow as mod

        spec = tmp_path / "openapi.yaml"
        path_ref = tmp_path / "paths.yaml"
        path_ref.write_text(
            yaml.safe_dump({"/tasks": {"get": {"operationId": "get_tasks"}}}, sort_keys=False),
            encoding="utf-8",
        )
        spec.write_text(
            yaml.safe_dump({"paths": {"/tasks": {"$ref": "./paths.yaml#/~1tasks"}}}, sort_keys=False),
            encoding="utf-8",
        )
        stubs = tmp_path / "stubs.py"
        stubs.write_text("def get_tasks():\n    return None\n", encoding="utf-8")

        mod.self_verify_stub_coverage(spec, stubs)

        stubs.write_text("def other():\n    return None\n", encoding="utf-8")
        with pytest.raises(RuntimeError):
            mod.self_verify_stub_coverage(spec, stubs)

    def test_run_and_run_first_available(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import run_api_first_flow as mod

        def fake_subprocess(cmd, cwd=None, check=False, text=True, capture_output=True):  # type: ignore[no-untyped-def]
            return SimpleNamespace(returncode=0, stdout="ok", stderr="")

        monkeypatch.setattr(mod.subprocess, "run", fake_subprocess)
        mod.run(["echo", "ok"], cwd=tmp_path, compact=True, summary_label="done")

        monkeypatch.setattr(mod.sh, "which", lambda b: "/usr/bin/fake" if b == "tool" else None)
        mod.run_first_available([["tool", "run"]], cwd=tmp_path)

        monkeypatch.setattr(mod.sh, "which", lambda b: None)
        with pytest.raises(RuntimeError):
            mod.run_first_available([["missing", "run"]], cwd=tmp_path)

    def test_main_success_with_remediation(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import run_api_first_flow as mod

        monkeypatch.setattr(mod, "_license_require", lambda f: None)

        repo = tmp_path
        scripts_dir = repo / "scripts"
        scripts_dir.mkdir()
        monkeypatch.setattr(mod, "__file__", str(scripts_dir / "run_api_first_flow.py"))

        (repo / "notes").mkdir()
        (repo / "notes" / "plan.md").write_text("x", encoding="utf-8")
        (repo / "api").mkdir()
        (repo / "api" / "openapi.yaml").write_text("openapi: 3.0.3\n", encoding="utf-8")
        (repo / "api" / "taskstream").mkdir(parents=True)
        (repo / "docs" / "assets" / "api").mkdir(parents=True)

        attempts = {"n": 0}
        monkeypatch.setattr(mod, "run", lambda *a, **k: None)
        monkeypatch.setattr(mod, "run_first_available", lambda *a, **k: None)
        monkeypatch.setattr(mod, "copy_spec_to_docs", lambda *a, **k: None)
        monkeypatch.setattr(mod.shutil, "copy2", lambda *a, **k: None)
        monkeypatch.setattr(mod, "self_verify_stub_coverage", lambda *a, **k: None)
        monkeypatch.setattr(mod, "build_sandbox_page_url", lambda *a, **k: "/reference/taskstream-api-playground/")
        monkeypatch.setattr(mod, "bundle_openapi_spec", lambda *a, **k: None)

        def fake_attempt(*args, **kwargs):  # type: ignore[no-untyped-def]
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise RuntimeError("fail once")

        monkeypatch.setattr(mod, "run_one_attempt", fake_attempt)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "x",
                "--project-slug",
                "taskstream",
                "--notes",
                "notes/plan.md",
                "--spec",
                "api/openapi.yaml",
                "--spec-tree",
                "api/taskstream",
                "--auto-remediate",
                "--max-attempts",
                "2",
                "--inject-demo-nav",
            ],
        )

        assert mod.main() == 0

    def test_main_fail_exit(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import run_api_first_flow as mod

        monkeypatch.setattr(mod, "_license_require", lambda f: None)

        repo = tmp_path
        scripts_dir = repo / "scripts"
        scripts_dir.mkdir()
        monkeypatch.setattr(mod, "__file__", str(scripts_dir / "run_api_first_flow.py"))
        (repo / "notes").mkdir()
        (repo / "notes" / "plan.md").write_text("x", encoding="utf-8")
        (repo / "api").mkdir()
        (repo / "api" / "openapi.yaml").write_text("openapi: 3.0.3\n", encoding="utf-8")
        (repo / "api" / "taskstream").mkdir(parents=True)

        monkeypatch.setattr(mod, "run", lambda *a, **k: None)
        monkeypatch.setattr(mod, "run_one_attempt", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
        monkeypatch.setattr(sys, "argv", [
            "x",
            "--project-slug",
            "taskstream",
            "--notes",
            "notes/plan.md",
            "--spec",
            "api/openapi.yaml",
            "--spec-tree",
            "api/taskstream",
            "--max-attempts",
            "1",
        ])
        with pytest.raises(RuntimeError):
            mod.main()

    def test_main_forwards_overrides_and_openapi_version(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import run_api_first_flow as mod

        monkeypatch.setattr(mod, "_license_require", lambda f: None)

        repo = tmp_path
        scripts_dir = repo / "scripts"
        scripts_dir.mkdir()
        monkeypatch.setattr(mod, "__file__", str(scripts_dir / "run_api_first_flow.py"))

        (repo / "notes").mkdir()
        (repo / "notes" / "plan.md").write_text("x", encoding="utf-8")
        (repo / "api").mkdir()
        (repo / "api" / "openapi.yaml").write_text("openapi: 3.0.3\n", encoding="utf-8")
        (repo / "api" / "taskstream").mkdir(parents=True)
        (repo / "docs" / "assets" / "api").mkdir(parents=True)
        (repo / "overrides").mkdir()
        (repo / "overrides" / "api.yml").write_text("spec: {}\n", encoding="utf-8")

        commands: list[list[str]] = []

        def fake_run(cmd: list[str], **_: object) -> None:
            commands.append(cmd)

        monkeypatch.setattr(mod, "run", fake_run)
        monkeypatch.setattr(mod, "run_first_available", lambda *a, **k: None)
        monkeypatch.setattr(mod, "copy_spec_to_docs", lambda *a, **k: None)
        monkeypatch.setattr(mod.shutil, "copy2", lambda *a, **k: None)
        monkeypatch.setattr(mod, "self_verify_stub_coverage", lambda *a, **k: None)
        monkeypatch.setattr(mod, "build_sandbox_page_url", lambda *a, **k: "/reference/taskstream-api-playground/")
        monkeypatch.setattr(mod, "run_one_attempt", lambda *a, **k: None)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "x",
                "--project-slug",
                "taskstream",
                "--notes",
                "notes/plan.md",
                "--spec",
                "api/openapi.yaml",
                "--spec-tree",
                "api/taskstream",
                "--openapi-version",
                "3.1.0",
                "--manual-overrides",
                "overrides/api.yml",
            ],
        )

        assert mod.main() == 0
        assert any(
            "generate_openapi_from_planning_notes.py" in " ".join(cmd) and "--openapi-version" in cmd and "3.1.0" in cmd
            for cmd in commands
        )
        assert any("apply_openapi_overrides.py" in " ".join(cmd) for cmd in commands)


class TestAdditionalZeroCoverageScripts:
    def test_generate_pipeline_capabilities_catalog(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import generate_pipeline_capabilities_catalog as mod

        repo = tmp_path / "repo"
        repo.mkdir()
        monkeypatch.setattr(mod, "REPO_ROOT", repo)
        monkeypatch.setattr(mod, "PACKAGE_JSON", repo / "package.json")
        monkeypatch.setattr(mod, "OUTPUT", repo / "docs" / "operations" / "PIPELINE_CAPABILITIES_CATALOG.md")

        (repo / "templates").mkdir()
        (repo / "templates" / "a.md").write_text("x", encoding="utf-8")
        (repo / "templates" / "legal").mkdir()
        (repo / "policy_packs").mkdir()
        (repo / "policy_packs" / "minimal.yml").write_text("x: 1\n", encoding="utf-8")
        (repo / "knowledge_modules").mkdir()
        (repo / "knowledge_modules" / "km.yml").write_text("x: 1\n", encoding="utf-8")
        (repo / "docker-compose.docs-ops.yml").write_text("version: '3'\n", encoding="utf-8")
        (repo / "package.json").write_text(
            json.dumps({"scripts": {"api:first": "x", "lint": "y", "validate": "z", "demo:run": "d", "misc": "m"}}),
            encoding="utf-8",
        )

        rc = mod.main()
        assert rc == 0
        text = mod.OUTPUT.read_text(encoding="utf-8")
        assert "Pipeline Capabilities Catalog" in text
        assert "API-first" in text

    def test_manage_demo_nav(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import manage_demo_nav as mod

        lines = [
            "nav:\n",
            "  - How-to:\n",
            "    - Configure Webhook triggers: how-to/configure-webhook-trigger.md\n",
            "  - Reference:\n",
            "    - API playground: reference/api-playground.md\n",
        ]
        added = mod.add_lines(lines)
        assert any("run-api-first-production-flow" in line for line in added)
        removed = mod.remove_lines(added)
        assert not any("taskstream-api-playground" in line for line in removed)

        mkdocs = tmp_path / "mkdocs.yml"
        mkdocs.write_text("".join(lines), encoding="utf-8")
        monkeypatch.setattr(sys, "argv", ["x", "--mode", "add", "--mkdocs", str(mkdocs)])
        assert mod.main() == 0

    def test_self_verify_scripts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import self_verify_api_user_path as api
        from scripts import self_verify_prodlike_user_path as prod

        responses_api = [
            (200, {"data": [], "page": {}}),
            (201, {"id": "p1"}),
            (200, {"data": [], "page": {}}),
            (200, {"email": "a@b.c"}),
        ]
        monkeypatch.setattr(api, "call_json", lambda *a, **k: responses_api.pop(0))
        monkeypatch.setattr(sys, "argv", ["x", "--base-url", "http://localhost:4010/v1"])
        assert api.main() == 0

        responses_prod = [
            (200, {"id": "u1"}),
            (201, {"id": "p1"}),
            (201, {"id": "t1"}),
            (409, None),
            (200, {"data": [{"id": "tg1"}]}),
            (204, None),
            (201, {"id": "c1"}),
            (204, None),
            (200, {"status": "done"}),
            (200, {"data": []}),
            (204, None),
        ]
        monkeypatch.setattr(prod, "call_json", lambda *a, **k: responses_prod.pop(0))
        monkeypatch.setattr(sys, "argv", ["x", "--base-url", "http://localhost:4011/v1"])
        assert prod.main() == 0

    def test_require_and_call_json_error_branch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import self_verify_api_user_path as api

        with pytest.raises(RuntimeError):
            api.require(False, "bad")

        class FakeHttpError(Exception):
            def __init__(self) -> None:
                self.code = 400

            def read(self) -> bytes:
                return b'{"error":"x"}'

        monkeypatch.setattr(api.urllib.request, "urlopen", lambda *a, **k: (_ for _ in ()).throw(api.urllib.error.HTTPError("u", 400, "bad", {}, None)))
        status, payload = api.call_json("GET", "http://x")
        assert status == 400
        assert payload is None or isinstance(payload, dict)


class TestGenerateFastApiStubsFromOpenApi:
    def test_helpers(self, tmp_path: Path) -> None:
        from scripts import generate_fastapi_stubs_from_openapi as mod

        assert mod.to_python_path("/tasks/{task_id}") == "/tasks/{task_id}"
        assert mod.to_args("/tasks/{task_id}") == "task_id: str, request: Request"
        assert mod.to_args("/tasks") == "request: Request"
        assert mod.fallback_operation_id("GET", "/tasks/{task_id}") == "get_tasks_task_id"

        spec = tmp_path / "openapi.yaml"
        ref_file = tmp_path / "paths.yaml"
        ref_file.write_text(yaml.safe_dump({"/tasks": {"get": {"summary": "List"}}}), encoding="utf-8")
        spec.write_text(yaml.safe_dump({"paths": {"/tasks": {"$ref": "./paths.yaml#/~1tasks"}}}), encoding="utf-8")
        loaded = mod.load_spec(spec)
        resolved = mod.resolve_paths(loaded, spec)
        assert "/tasks" in resolved

    def test_walk_fragment(self) -> None:
        from scripts import generate_fastapi_stubs_from_openapi as mod

        data = {"a": {"b/c": {"d~e": 1}}}
        assert mod._walk_fragment(data, "/a/b~1c/d~0e") == 1

    def test_build_app_source_and_main(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import generate_fastapi_stubs_from_openapi as mod

        spec = tmp_path / "openapi.yaml"
        spec.write_text(
            yaml.safe_dump(
                {
                    "info": {"title": "Demo API"},
                    "paths": {
                        "/tasks": {
                            "get": {"operationId": "get_tasks", "summary": "List", "description": "List tasks"},
                            "post": {"summary": "Create"},
                        }
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        out = tmp_path / "generated" / "app.py"

        source = mod.build_app_source(mod.load_spec(spec), spec)
        assert "async def get_tasks" in source
        assert "@app.post('/tasks'" in source

        monkeypatch.setattr(sys, "argv", ["x", "--spec", str(spec), "--output", str(out)])
        rc = mod.main()
        assert rc == 0
        assert out.exists()

        missing = tmp_path / "missing.yaml"
        monkeypatch.setattr(sys, "argv", ["x", "--spec", str(missing), "--output", str(out)])
        assert mod.main() == 2


class TestApplyOpenApiOverrides:
    def test_deep_merge_and_apply(self, tmp_path: Path) -> None:
        from scripts import apply_openapi_overrides as mod

        spec = tmp_path / "openapi.yaml"
        spec.write_text(
            yaml.safe_dump(
                {
                    "openapi": "3.0.3",
                    "info": {"title": "Demo"},
                    "paths": {"/projects": {"get": {"summary": "List projects"}}},
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        tree = tmp_path / "split"
        file_path = tree / "v1" / "paths" / "projects.yaml"
        file_path.parent.mkdir(parents=True)
        file_path.write_text(yaml.safe_dump({"/projects": {"get": {"description": "Base"}}}, sort_keys=False), encoding="utf-8")

        overrides = tmp_path / "overrides.yml"
        overrides.write_text(
            yaml.safe_dump(
                {
                    "spec": {
                        "info": {"version": "v1"},
                        "x-internal-owner": "docs-team",
                    },
                    "files": {
                        "v1/paths/projects.yaml": {
                            "/projects": {
                                "get": {
                                    "x-codeSamples": [
                                        {"lang": "curl", "source": "curl -sS https://api.example.com/v1/projects"}
                                    ]
                                }
                            }
                        }
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        root_applied, files_applied = mod.apply_overrides(spec, tree, overrides)
        assert root_applied == 1
        assert files_applied == 1

        merged_spec = yaml.safe_load(spec.read_text(encoding="utf-8"))
        assert merged_spec["info"]["version"] == "v1"
        assert merged_spec["x-internal-owner"] == "docs-team"

        merged_path = yaml.safe_load(file_path.read_text(encoding="utf-8"))
        assert merged_path["/projects"]["get"]["x-codeSamples"][0]["lang"] == "curl"

    def test_main_validation(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import apply_openapi_overrides as mod

        spec = tmp_path / "openapi.yaml"
        spec.write_text("openapi: 3.0.3\n", encoding="utf-8")
        overrides = tmp_path / "overrides.yml"
        overrides.write_text("spec: {}\n", encoding="utf-8")

        monkeypatch.setattr(sys, "argv", ["x", "--spec", str(spec), "--overrides", str(overrides)])
        assert mod.main() == 0

        monkeypatch.setattr(sys, "argv", ["x", "--spec", str(tmp_path / "missing.yaml"), "--overrides", str(overrides)])
        assert mod.main() == 2


class TestCheckOpenApiRegression:
    def test_snapshot_update_and_compare(self, tmp_path: Path) -> None:
        from scripts import check_openapi_regression as mod

        spec = tmp_path / "openapi.yaml"
        spec.write_text(
            yaml.safe_dump(
                {
                    "openapi": "3.0.3",
                    "info": {"title": "Demo", "version": "v1"},
                    "paths": {},
                    "components": {},
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        tree = tmp_path / "api" / "demo"
        tree.mkdir(parents=True)
        (tree / "paths.yaml").write_text(yaml.safe_dump({"/x": {"get": {"summary": "X"}}}, sort_keys=False), encoding="utf-8")

        snapshot = mod.collect_snapshot(spec, tree)
        assert str(spec.as_posix()) in snapshot["files"]

        baseline = dict(snapshot)
        diff = mod.compare_snapshots(snapshot, baseline)
        assert diff == {"added": [], "removed": [], "changed": []}

        spec.write_text(
            yaml.safe_dump(
                {
                    "openapi": "3.0.3",
                    "info": {"title": "Demo Changed", "version": "v1"},
                    "paths": {},
                    "components": {},
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        changed = mod.collect_snapshot(spec, tree)
        diff = mod.compare_snapshots(changed, baseline)
        assert str(spec.as_posix()) in diff["changed"]


class TestBuildAllIntentExperiences:
    def test_load_modules_and_no_combinations(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        from scripts import build_all_intent_experiences as mod

        modules = tmp_path / "knowledge_modules"
        modules.mkdir()
        (modules / "a.yml").write_text("status: inactive\n", encoding="utf-8")
        active = mod._load_modules(modules)
        assert active == []

        monkeypatch.setattr(sys, "argv", ["x", "--modules-dir", str(modules)])
        mod.main()
        assert "No active module combinations found" in capsys.readouterr().out

    def test_main_happy_and_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts import build_all_intent_experiences as mod

        modules = tmp_path / "knowledge_modules"
        modules.mkdir()
        (modules / "a.yml").write_text(
            yaml.safe_dump({"status": "active", "intents": ["troubleshoot"], "audiences": ["developer"]}),
            encoding="utf-8",
        )

        calls: list[list[str]] = []

        def ok_run(cmd: list[str], check: bool, capture_output: bool, text: bool) -> SimpleNamespace:
            calls.append(cmd)
            assert check is False
            assert capture_output is True
            assert text is True
            return SimpleNamespace(returncode=0, stderr="")

        monkeypatch.setattr(mod.subprocess, "run", ok_run)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "x",
                "--modules-dir",
                str(modules),
                "--docs-output-dir",
                "docs/reference/intent-experiences",
                "--bundle-output-dir",
                "reports/intent-bundles",
            ],
        )
        mod.main()
        assert len(calls) == len(mod.CHANNELS)

        monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=1, stderr="boom"))
        with pytest.raises(RuntimeError):
            mod.main()


class TestConfigureAskAi:
    def test_load_parse_validate_helpers(self, tmp_path: Path) -> None:
        from scripts import configure_ask_ai as mod

        cfg_path = tmp_path / "ask-ai.yml"
        loaded = mod._load_config(cfg_path)
        assert loaded["provider"] == "openai"
        cfg_path.write_text("provider: custom\nbilling_mode: disabled\n", encoding="utf-8")
        loaded2 = mod._load_config(cfg_path)
        assert loaded2["provider"] == "custom"

        assert mod._parse_roles(None) is None
        assert mod._parse_roles("admin, support") == ["admin", "support"]
        assert mod._parse_roles(" , ") == []

        mod._validate_config({"provider": "openai", "billing_mode": "disabled"})
        with pytest.raises(ValueError):
            mod._validate_config({"provider": "bad", "billing_mode": "disabled"})
        with pytest.raises(ValueError):
            mod._validate_config({"provider": "openai", "billing_mode": "bad"})

    def test_main_modes_and_conflicts(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        from scripts import configure_ask_ai as mod

        cfg = tmp_path / "config" / "ask-ai.yml"
        out = tmp_path / "reports" / "ask-ai-config.json"

        monkeypatch.setattr(sys, "argv", ["x", "--config", str(cfg), "--status"])
        assert mod.main() == 0
        assert "enabled:" in capsys.readouterr().out

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "x",
                "--config",
                str(cfg),
                "--json-out",
                str(out),
                "--enable",
                "--provider",
                "anthropic",
                "--billing-mode",
                "bring-your-own-key",
                "--allowed-roles",
                "admin,support",
                "--no-audit-logging",
                "--no-require-user-auth",
            ],
        )
        assert mod.main() == 0
        payload = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        assert payload["enabled"] is True
        assert payload["provider"] == "anthropic"
        assert payload["allowed_roles"] == ["admin", "support"]
        assert out.exists()

        monkeypatch.setattr(sys, "argv", ["x", "--config", str(cfg), "--enable", "--disable"])
        with pytest.raises(ValueError):
            mod.main()
        monkeypatch.setattr(sys, "argv", ["x", "--config", str(cfg), "--require-user-auth", "--no-require-user-auth"])
        with pytest.raises(ValueError):
            mod.main()

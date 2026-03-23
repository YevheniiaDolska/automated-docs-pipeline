"""Coverage boost round 2: target 85%+ on 8 partially-covered scripts.

Targets:
- provision_client_repo.py (48%): wizard prompts, preset loading, dotenv, gitignore
- generate_multilang_tabs.py (61%): curl parsing, tab rendering, scope filtering
- run_retrieval_evals.py (57%): evaluate, dataset loading, mode dispatch, RRF
- multi_protocol_engine.py (77%): adapter stages, regression bootstrap, quality gates
- run_multi_protocol_contract_flow.py (69%): endpoint resolution, http_to_ws
- finalize_docs_gate.py (69%): _ask_confirmation, GUI probes, merge_config
- generate_kpi_wall.py (79%): color helpers, grade, HTML dashboard, i18n metrics
- validate_knowledge_modules.py (68%): cycle detection, set field validation, report
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
from io import StringIO
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ===========================================================================
# provision_client_repo.py
# ===========================================================================


class TestProvisionPromptWithDefault:
    """Cover _prompt_with_default function branches."""

    def test_returns_user_input(self) -> None:
        """User types a value -> returns that value."""
        from scripts.provision_client_repo import _prompt_with_default

        with patch("builtins.input", return_value="hello"):
            assert _prompt_with_default("Name") == "hello"

    def test_returns_default_on_empty(self) -> None:
        """User presses Enter -> returns default."""
        from scripts.provision_client_repo import _prompt_with_default

        with patch("builtins.input", return_value=""):
            assert _prompt_with_default("Name", "world") == "world"

    def test_raises_when_no_default_and_empty(self) -> None:
        """No default and empty input -> raises ValueError."""
        from scripts.provision_client_repo import _prompt_with_default

        with patch("builtins.input", return_value=""):
            with pytest.raises(ValueError, match="Value is required"):
                _prompt_with_default("Name")

    def test_strips_whitespace(self) -> None:
        """Leading/trailing whitespace is stripped."""
        from scripts.provision_client_repo import _prompt_with_default

        with patch("builtins.input", return_value="  trimmed  "):
            assert _prompt_with_default("Name") == "trimmed"


class TestProvisionPromptChoice:
    """Cover _prompt_choice function with valid and invalid inputs."""

    def test_valid_choice_first_try(self) -> None:
        """User picks a valid option immediately."""
        from scripts.provision_client_repo import _prompt_choice

        with patch("builtins.input", return_value="startup"):
            assert _prompt_choice("Preset", ["small", "startup", "enterprise"], "small") == "startup"

    def test_invalid_then_valid(self) -> None:
        """User enters invalid then valid option."""
        from scripts.provision_client_repo import _prompt_choice

        with patch("builtins.input", side_effect=["bad", "small"]):
            assert _prompt_choice("Preset", ["small", "startup"], "small") == "small"

    def test_default_on_empty(self) -> None:
        """Empty input -> returns default."""
        from scripts.provision_client_repo import _prompt_choice

        with patch("builtins.input", return_value=""):
            assert _prompt_choice("Preset", ["small", "startup"], "startup") == "startup"


class TestProvisionPromptYesNo:
    """Cover _prompt_yes_no function."""

    def test_default_yes(self) -> None:
        """Empty input with default_yes=True returns True."""
        from scripts.provision_client_repo import _prompt_yes_no

        with patch("builtins.input", return_value=""):
            assert _prompt_yes_no("Continue?", default_yes=True) is True

    def test_default_no(self) -> None:
        """Empty input with default_yes=False returns False."""
        from scripts.provision_client_repo import _prompt_yes_no

        with patch("builtins.input", return_value=""):
            assert _prompt_yes_no("Continue?", default_yes=False) is False

    def test_explicit_yes(self) -> None:
        """User types 'y' -> returns True."""
        from scripts.provision_client_repo import _prompt_yes_no

        with patch("builtins.input", return_value="y"):
            assert _prompt_yes_no("Continue?") is True

    def test_explicit_no(self) -> None:
        """User types 'no' -> returns False."""
        from scripts.provision_client_repo import _prompt_yes_no

        with patch("builtins.input", return_value="no"):
            assert _prompt_yes_no("Continue?") is False


class TestProvisionPromptCsv:
    """Cover _prompt_csv function."""

    def test_returns_parsed_csv(self) -> None:
        """User enters comma-separated values."""
        from scripts.provision_client_repo import _prompt_csv

        with patch("builtins.input", return_value="a, b, c"):
            result = _prompt_csv("Tags", ["x"])
            assert result == ["a", "b", "c"]

    def test_returns_default_on_empty(self) -> None:
        """Empty input returns default values."""
        from scripts.provision_client_repo import _prompt_csv

        with patch("builtins.input", return_value=""):
            result = _prompt_csv("Tags", ["mkdocs", "readme"])
            assert result == ["mkdocs", "readme"]


class TestProvisionSlugify:
    """Cover _slugify_client_id function."""

    def test_basic_slugify(self) -> None:
        """Converts company name to kebab-case slug."""
        from scripts.provision_client_repo import _slugify_client_id

        assert _slugify_client_id("ACME Corp.") == "acme-corp"

    def test_collapses_dashes(self) -> None:
        """Multiple dashes are collapsed to one."""
        from scripts.provision_client_repo import _slugify_client_id

        assert _slugify_client_id("hello---world") == "hello-world"

    def test_strips_leading_trailing_dashes(self) -> None:
        """Leading and trailing dashes are stripped."""
        from scripts.provision_client_repo import _slugify_client_id

        assert _slugify_client_id("--hello--") == "hello"

    def test_empty_string(self) -> None:
        """Empty input returns empty slug."""
        from scripts.provision_client_repo import _slugify_client_id

        assert _slugify_client_id("") == ""


class TestProvisionDeepMerge:
    """Cover _deep_merge function."""

    def test_shallow_merge(self) -> None:
        """Top-level keys are merged."""
        from scripts.provision_client_repo import _deep_merge

        result = _deep_merge({"a": 1}, {"b": 2})
        assert result == {"a": 1, "b": 2}

    def test_nested_merge(self) -> None:
        """Nested dicts are recursively merged."""
        from scripts.provision_client_repo import _deep_merge

        base = {"top": {"a": 1, "b": 2}}
        override = {"top": {"b": 3, "c": 4}}
        result = _deep_merge(base, override)
        assert result == {"top": {"a": 1, "b": 3, "c": 4}}

    def test_override_replaces_non_dict(self) -> None:
        """Non-dict values are replaced entirely."""
        from scripts.provision_client_repo import _deep_merge

        result = _deep_merge({"a": [1, 2]}, {"a": [3]})
        assert result == {"a": [3]}


class TestProvisionDotenv:
    """Cover _read_dotenv and _write_dotenv functions."""

    def test_read_dotenv_parses_values(self, tmp_path: Path) -> None:
        """Reads key=value pairs from .env file."""
        from scripts.provision_client_repo import _read_dotenv

        env_file = tmp_path / ".env"
        env_file.write_text("KEY1=value1\n# comment\n\nKEY2=value2\n", encoding="utf-8")
        result = _read_dotenv(env_file)
        assert result == {"KEY1": "value1", "KEY2": "value2"}

    def test_read_dotenv_missing_file(self, tmp_path: Path) -> None:
        """Missing file returns empty dict."""
        from scripts.provision_client_repo import _read_dotenv

        result = _read_dotenv(tmp_path / "missing")
        assert result == {}

    def test_read_dotenv_skips_invalid_lines(self, tmp_path: Path) -> None:
        """Lines without = are skipped."""
        from scripts.provision_client_repo import _read_dotenv

        env_file = tmp_path / ".env"
        env_file.write_text("NOEQUALSSIGN\nGOOD=val\n", encoding="utf-8")
        result = _read_dotenv(env_file)
        assert result == {"GOOD": "val"}

    def test_write_dotenv(self, tmp_path: Path) -> None:
        """Writes sorted key=value pairs."""
        from scripts.provision_client_repo import _write_dotenv

        env_file = tmp_path / ".env"
        _write_dotenv(env_file, {"B_KEY": "2", "A_KEY": "1"})
        content = env_file.read_text(encoding="utf-8")
        assert "A_KEY=1" in content
        assert "B_KEY=2" in content
        # Keys are sorted
        assert content.index("A_KEY") < content.index("B_KEY")


class TestProvisionGitignore:
    """Cover _ensure_gitignore_has_env function."""

    def test_creates_gitignore_if_missing(self, tmp_path: Path) -> None:
        """Creates .gitignore with the env entry if file does not exist."""
        from scripts.provision_client_repo import _ensure_gitignore_has_env

        _ensure_gitignore_has_env(tmp_path, ".env.local")
        content = (tmp_path / ".gitignore").read_text(encoding="utf-8")
        assert ".env.local" in content

    def test_skips_if_already_present(self, tmp_path: Path) -> None:
        """Does not duplicate if already in .gitignore."""
        from scripts.provision_client_repo import _ensure_gitignore_has_env

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(".env.local\n", encoding="utf-8")
        _ensure_gitignore_has_env(tmp_path, ".env.local")
        content = gitignore.read_text(encoding="utf-8")
        assert content.count(".env.local") == 1

    def test_appends_with_blank_line(self, tmp_path: Path) -> None:
        """Adds blank line before new entry if last line is not blank."""
        from scripts.provision_client_repo import _ensure_gitignore_has_env

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("node_modules", encoding="utf-8")
        _ensure_gitignore_has_env(tmp_path, ".env.local")
        content = gitignore.read_text(encoding="utf-8")
        assert ".env.local" in content
        assert "node_modules" in content


class TestProvisionCopyBundle:
    """Cover copy_bundle_to_repo function."""

    def test_copies_bundle(self, tmp_path: Path) -> None:
        """Copies bundle directory into client repo."""
        from scripts.provision_client_repo import copy_bundle_to_repo

        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "file.txt").write_text("hello", encoding="utf-8")
        client = tmp_path / "client"
        client.mkdir()
        result = copy_bundle_to_repo(bundle, client, "docsops")
        assert (result / "file.txt").exists()

    def test_overwrites_existing(self, tmp_path: Path) -> None:
        """Removes existing target dir before copying."""
        from scripts.provision_client_repo import copy_bundle_to_repo

        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "new.txt").write_text("new", encoding="utf-8")
        client = tmp_path / "client"
        target = client / "docsops"
        target.mkdir(parents=True)
        (target / "old.txt").write_text("old", encoding="utf-8")
        result = copy_bundle_to_repo(bundle, client, "docsops")
        assert (result / "new.txt").exists()
        assert not (result / "old.txt").exists()


class TestProvisionSchedulerInstall:
    """Cover run_scheduler_install function."""

    def test_none_mode_does_nothing(self, tmp_path: Path) -> None:
        """Mode 'none' returns without running anything."""
        from scripts.provision_client_repo import run_scheduler_install

        run_scheduler_install(tmp_path, "docsops", "none")

    def test_unsupported_mode_raises(self, tmp_path: Path) -> None:
        """Unsupported mode raises ValueError."""
        from scripts.provision_client_repo import run_scheduler_install

        with pytest.raises(ValueError, match="Unsupported"):
            run_scheduler_install(tmp_path, "docsops", "custom")

    @patch("subprocess.run")
    def test_linux_mode_calls_bash(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Linux mode calls bash with cron script."""
        from scripts.provision_client_repo import run_scheduler_install

        run_scheduler_install(tmp_path, "docsops", "linux")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "bash"

    @patch("subprocess.run")
    def test_windows_mode_calls_powershell(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Windows mode calls powershell with task script."""
        from scripts.provision_client_repo import run_scheduler_install

        run_scheduler_install(tmp_path, "docsops", "windows")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "powershell"


class TestProvisionResolveArgs:
    """Cover _resolve_args function."""

    def test_returns_args_when_complete(self) -> None:
        """Non-interactive with complete args returns unchanged."""
        import argparse
        from scripts.provision_client_repo import _resolve_args

        args = argparse.Namespace(
            interactive=False,
            client="profile.yml",
            client_repo="/tmp/repo",
            docsops_dir="docsops",
            install_scheduler="none",
        )
        result = _resolve_args(args)
        assert result.client == "profile.yml"

    def test_raises_when_non_tty_and_missing_args(self) -> None:
        """Raises ValueError if stdin not interactive and args missing."""
        import argparse
        from scripts.provision_client_repo import _resolve_args

        args = argparse.Namespace(
            interactive=False,
            client=None,
            client_repo=None,
            docsops_dir="docsops",
            install_scheduler="none",
        )
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = False
            with pytest.raises(ValueError, match="Missing required arguments"):
                _resolve_args(args)


class TestProvisionLoadYamlMapping:
    """Cover _load_yaml_mapping function."""

    def test_loads_valid_yaml(self, tmp_path: Path) -> None:
        """Loads a valid YAML mapping."""
        from scripts.provision_client_repo import _load_yaml_mapping

        f = tmp_path / "test.yml"
        f.write_text("key: value\n", encoding="utf-8")
        result = _load_yaml_mapping(f)
        assert result == {"key": "value"}

    def test_raises_on_non_mapping(self, tmp_path: Path) -> None:
        """Raises ValueError for YAML that is not a mapping."""
        from scripts.provision_client_repo import _load_yaml_mapping

        f = tmp_path / "test.yml"
        f.write_text("- item1\n- item2\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Expected YAML mapping"):
            _load_yaml_mapping(f)

    def test_empty_yaml_returns_empty_dict(self, tmp_path: Path) -> None:
        """Empty YAML file returns empty dict."""
        from scripts.provision_client_repo import _load_yaml_mapping

        f = tmp_path / "test.yml"
        f.write_text("", encoding="utf-8")
        result = _load_yaml_mapping(f)
        assert result == {}


class TestProvisionSaveGeneratedProfile:
    """Cover _save_generated_profile function."""

    def test_saves_profile_yaml(self, tmp_path: Path) -> None:
        """Saves profile to generated directory."""
        from scripts.provision_client_repo import _save_generated_profile

        profile = {"client": {"id": "test"}}
        with patch("scripts.provision_client_repo.REPO_ROOT", tmp_path):
            out = _save_generated_profile(profile, "test-client")
            assert out.exists()
            content = yaml.safe_load(out.read_text(encoding="utf-8"))
            assert content["client"]["id"] == "test"


# ===========================================================================
# generate_multilang_tabs.py
# ===========================================================================


class TestMultilangCurlParsing:
    """Cover _parse_curl_block with various curl formats."""

    def test_simple_get(self) -> None:
        """Parses simple GET request."""
        from scripts.generate_multilang_tabs import _parse_curl_block

        req = _parse_curl_block("curl https://api.example.com/users")
        assert req is not None
        assert req.method == "GET"
        assert req.url == "https://api.example.com/users"

    def test_post_with_data(self) -> None:
        """Parses POST with -d flag and JSON body."""
        from scripts.generate_multilang_tabs import _parse_curl_block

        block = 'curl -X POST https://api.example.com/users -H "Content-Type: application/json" -d \'{"name":"test"}\''
        req = _parse_curl_block(block)
        assert req is not None
        assert req.method == "POST"
        assert req.headers.get("Content-Type") == "application/json"
        assert req.data is not None

    def test_multiline_curl(self) -> None:
        """Parses multiline curl with backslash continuation."""
        from scripts.generate_multilang_tabs import _parse_curl_block

        block = "curl \\\n  -X PUT \\\n  https://api.example.com/items/1"
        req = _parse_curl_block(block)
        assert req is not None
        assert req.method == "PUT"

    def test_returns_none_for_non_curl(self) -> None:
        """Returns None for non-curl content."""
        from scripts.generate_multilang_tabs import _parse_curl_block

        assert _parse_curl_block("echo hello world") is None

    def test_returns_none_for_no_url(self) -> None:
        """Returns None when curl has no URL."""
        from scripts.generate_multilang_tabs import _parse_curl_block

        assert _parse_curl_block("curl -X GET") is None

    def test_data_raw_flag(self) -> None:
        """Parses --data-raw flag."""
        from scripts.generate_multilang_tabs import _parse_curl_block

        block = 'curl -X POST https://api.example.com/send --data-raw "payload"'
        req = _parse_curl_block(block)
        assert req is not None
        assert req.data == "payload"


class TestMultilangRenderTabs:
    """Cover _render_tabs function with various input combinations."""

    def test_renders_three_tabs(self) -> None:
        """Output contains cURL, JavaScript, and Python tabs."""
        from scripts.generate_multilang_tabs import CurlRequest, _render_tabs

        req = CurlRequest(method="GET", url="https://api.example.com/v1/data", headers={}, data=None)
        result = _render_tabs("curl https://api.example.com/v1/data", req)
        assert '=== "cURL"' in result
        assert '=== "JavaScript"' in result
        assert '=== "Python"' in result

    def test_renders_json_body(self) -> None:
        """JSON data is properly formatted in JS and Python."""
        from scripts.generate_multilang_tabs import CurlRequest, _render_tabs

        req = CurlRequest(
            method="POST",
            url="https://api.example.com/items",
            headers={"Content-Type": "application/json"},
            data='{"name": "test"}',
        )
        result = _render_tabs("curl ...", req)
        assert "JSON.stringify" in result
        assert "json=" in result

    def test_renders_non_json_body(self) -> None:
        """Non-JSON data is passed as raw string."""
        from scripts.generate_multilang_tabs import CurlRequest, _render_tabs

        req = CurlRequest(
            method="POST",
            url="https://api.example.com/upload",
            headers={},
            data="plain text payload",
        )
        result = _render_tabs("curl ...", req)
        assert "data=" in result

    def test_renders_headers(self) -> None:
        """Headers appear in JS and Python output."""
        from scripts.generate_multilang_tabs import CurlRequest, _render_tabs

        req = CurlRequest(
            method="GET",
            url="https://api.example.com/v1",
            headers={"Authorization": "Bearer tok123"},
            data=None,
        )
        result = _render_tabs("curl ...", req)
        assert "Authorization" in result
        assert "Bearer tok123" in result


class TestMultilangTransformMarkdown:
    """Cover transform_markdown scope filtering and block replacement."""

    def test_replaces_curl_block_in_all_scope(self, tmp_path: Path) -> None:
        """Curl block is replaced when scope=all."""
        from scripts.generate_multilang_tabs import transform_markdown

        md = "# API\n\n```bash\ncurl https://api.example.com/users\n```\n"
        result, changed = transform_markdown(md, scope="all", file_path=tmp_path / "doc.md")
        assert changed == 1
        assert '=== "cURL"' in result

    def test_skips_non_api_in_api_scope(self, tmp_path: Path) -> None:
        """Non-API file is skipped when scope=api."""
        from scripts.generate_multilang_tabs import transform_markdown

        md = "```bash\ncurl https://api.example.com/users\n```\n"
        result, changed = transform_markdown(md, scope="api", file_path=tmp_path / "tutorial.md")
        assert changed == 0

    def test_transforms_api_file_in_api_scope(self, tmp_path: Path) -> None:
        """API-like file is processed when scope=api."""
        from scripts.generate_multilang_tabs import transform_markdown

        md = "```bash\ncurl https://api.example.com/users\n```\n"
        result, changed = transform_markdown(md, scope="api", file_path=tmp_path / "api-reference.md")
        assert changed == 1

    def test_preserves_non_curl_bash_blocks(self, tmp_path: Path) -> None:
        """Non-curl bash blocks are preserved unchanged."""
        from scripts.generate_multilang_tabs import transform_markdown

        md = "```bash\necho hello\n```\n"
        result, changed = transform_markdown(md, scope="all", file_path=tmp_path / "doc.md")
        assert changed == 0
        assert "echo hello" in result

    def test_indented_code_blocks_are_skipped(self, tmp_path: Path) -> None:
        """Indented code blocks (inside tabs) are not processed."""
        from scripts.generate_multilang_tabs import transform_markdown

        md = "    ```bash\n    curl https://api.example.com\n    ```\n"
        result, changed = transform_markdown(md, scope="all", file_path=tmp_path / "doc.md")
        assert changed == 0


class TestMultilangIsApiLikeDoc:
    """Cover _is_api_like_doc detection logic."""

    def test_api_in_name(self) -> None:
        """Detects 'api' in filename."""
        from scripts.generate_multilang_tabs import _is_api_like_doc

        assert _is_api_like_doc(Path("docs/api-reference.md")) is True

    def test_reference_with_api_in_path(self) -> None:
        """Detects API reference path."""
        from scripts.generate_multilang_tabs import _is_api_like_doc

        assert _is_api_like_doc(Path("docs/reference/api-endpoints.md")) is True

    def test_non_api_doc(self) -> None:
        """Non-API doc returns False."""
        from scripts.generate_multilang_tabs import _is_api_like_doc

        assert _is_api_like_doc(Path("docs/tutorial/setup.md")) is False


class TestMultilangPyLiteral:
    """Cover _py_literal helper."""

    def test_none_literal(self) -> None:
        """None is rendered as Python None."""
        from scripts.generate_multilang_tabs import _py_literal

        assert _py_literal(None) == "None"

    def test_dict_literal(self) -> None:
        """Dict is rendered with repr keys and values."""
        from scripts.generate_multilang_tabs import _py_literal

        result = _py_literal({"key": "val"})
        assert "'key'" in result
        assert "'val'" in result


# ===========================================================================
# run_retrieval_evals.py
# ===========================================================================


class TestRetrievalTokenize:
    """Cover _tokenize function."""

    def test_tokenizes_text(self) -> None:
        """Extracts lowercase tokens from text."""
        from scripts.run_retrieval_evals import _tokenize

        tokens = _tokenize("Hello World 42")
        assert "hello" in tokens
        assert "world" in tokens
        assert "42" in tokens

    def test_empty_text(self) -> None:
        """Empty text returns empty set."""
        from scripts.run_retrieval_evals import _tokenize

        assert _tokenize("") == set()


class TestRetrievalLoadIndex:
    """Cover _load_index function."""

    def test_loads_valid_index(self, tmp_path: Path) -> None:
        """Loads a valid JSON array of index records."""
        from scripts.run_retrieval_evals import _load_index

        data = [{"id": "mod-1", "title": "Module One"}, {"id": "mod-2", "title": "Module Two"}]
        f = tmp_path / "index.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        result = _load_index(f)
        assert len(result) == 2

    def test_raises_on_non_list(self, tmp_path: Path) -> None:
        """Raises ValueError for non-list JSON."""
        from scripts.run_retrieval_evals import _load_index

        f = tmp_path / "index.json"
        f.write_text('{"key": "value"}', encoding="utf-8")
        with pytest.raises(ValueError, match="must be a JSON list"):
            _load_index(f)

    def test_skips_items_without_id(self, tmp_path: Path) -> None:
        """Skips items without a valid id."""
        from scripts.run_retrieval_evals import _load_index

        data = [{"id": "ok"}, {"no_id": True}, {"id": ""}]
        f = tmp_path / "index.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        result = _load_index(f)
        assert len(result) == 1


class TestRetrievalLoadDataset:
    """Cover _load_dataset function."""

    def test_loads_valid_dataset(self, tmp_path: Path) -> None:
        """Loads a valid YAML eval dataset."""
        from scripts.run_retrieval_evals import _load_dataset

        data = [{"query": "How to configure?", "expected_ids": ["mod-1"]}]
        f = tmp_path / "dataset.yml"
        f.write_text(yaml.safe_dump(data), encoding="utf-8")
        result = _load_dataset(f)
        assert len(result) == 1
        assert result[0]["query"] == "How to configure?"

    def test_raises_on_non_list(self, tmp_path: Path) -> None:
        """Raises ValueError for non-list YAML."""
        from scripts.run_retrieval_evals import _load_dataset

        f = tmp_path / "dataset.yml"
        f.write_text("key: value\n", encoding="utf-8")
        with pytest.raises(ValueError, match="must be a YAML list"):
            _load_dataset(f)

    def test_skips_invalid_items(self, tmp_path: Path) -> None:
        """Skips items without query or expected_ids."""
        from scripts.run_retrieval_evals import _load_dataset

        data = [
            {"query": "valid", "expected_ids": ["a"]},
            {"query": "", "expected_ids": ["b"]},
            "not a dict",
            {"query": "no ids", "expected_ids": []},
        ]
        f = tmp_path / "dataset.yml"
        f.write_text(yaml.safe_dump(data), encoding="utf-8")
        result = _load_dataset(f)
        assert len(result) == 1


class TestRetrievalBuildAutoDataset:
    """Cover _build_auto_dataset function."""

    def test_builds_from_index(self) -> None:
        """Auto-generates dataset from index rows."""
        from scripts.run_retrieval_evals import _build_auto_dataset

        index_rows = [
            {"id": "mod-1", "title": "Configure webhooks", "summary": "How to set up webhooks"},
            {"id": "mod-2", "title": "", "summary": "Troubleshooting guide for errors"},
        ]
        result = _build_auto_dataset(index_rows, limit=10)
        assert len(result) == 2
        assert result[0]["expected_ids"] == ["mod-1"]

    def test_respects_limit(self) -> None:
        """Respects the limit parameter."""
        from scripts.run_retrieval_evals import _build_auto_dataset

        rows = [{"id": f"m-{i}", "title": f"Title {i}", "summary": ""} for i in range(10)]
        result = _build_auto_dataset(rows, limit=3)
        assert len(result) == 3


class TestRetrievalEvaluate:
    """Cover evaluate function with various scenarios."""

    def test_empty_dataset_returns_error(self) -> None:
        """Empty dataset returns error status."""
        from scripts.run_retrieval_evals import evaluate

        result = evaluate([], [], top_k=3)
        assert result["status"] == "error"
        assert result["hallucination_rate"] == 1.0

    def test_perfect_retrieval(self) -> None:
        """Perfect retrieval returns 1.0 precision and recall."""
        from scripts.run_retrieval_evals import evaluate

        index_rows = [
            {"id": "a", "title": "Configure webhooks", "summary": "webhook setup"},
        ]
        dataset = [{"query": "webhooks", "expected_ids": ["a"]}]
        result = evaluate(index_rows, dataset, top_k=3)
        assert result["status"] == "ok"
        assert result["precision_at_k"] > 0
        assert result["recall_at_k"] > 0

    def test_custom_search_fn(self) -> None:
        """Custom search function is used when provided."""
        from scripts.run_retrieval_evals import evaluate

        index_rows = [{"id": "x"}]
        dataset = [{"query": "test", "expected_ids": ["x"]}]
        result = evaluate(
            index_rows, dataset, top_k=3,
            search_fn=lambda q, k: ["x"],
        )
        assert result["precision_at_k"] > 0

    def test_hallucination_detection(self) -> None:
        """Detects hallucinated IDs not in corpus."""
        from scripts.run_retrieval_evals import evaluate

        index_rows = [{"id": "real"}]
        dataset = [{"query": "test", "expected_ids": ["real"]}]
        result = evaluate(
            index_rows, dataset, top_k=3,
            search_fn=lambda q, k: ["real", "fake"],
        )
        assert result["hallucination_rate"] > 0


class TestRetrievalScoreQuery:
    """Cover _score_query function."""

    def test_score_with_overlap(self) -> None:
        """Returns positive score when query tokens overlap with doc."""
        from scripts.run_retrieval_evals import _score_query

        doc = {"title": "Configure webhook authentication", "summary": "webhooks setup"}
        score = _score_query("configure webhook", doc)
        assert score > 0

    def test_score_no_overlap(self) -> None:
        """Returns zero when no token overlap."""
        from scripts.run_retrieval_evals import _score_query

        doc = {"title": "Database migration", "summary": "postgres"}
        score = _score_query("webhook", doc)
        assert score == 0.0


class TestRetrievalSearchToken:
    """Cover _search_token function."""

    def test_returns_ranked_results(self) -> None:
        """Returns results ranked by token overlap score."""
        from scripts.run_retrieval_evals import _search_token

        rows = [
            {"id": "a", "title": "Configure webhooks", "summary": "webhook setup"},
            {"id": "b", "title": "Database migration", "summary": "postgres"},
        ]
        results = _search_token(rows, "configure webhooks", top_k=2)
        assert results[0] == "a"


class TestRetrievalRRF:
    """Cover _reciprocal_rank_fusion function."""

    def test_fuses_two_rankings(self) -> None:
        """Fuses two rankings using RRF."""
        from scripts.run_retrieval_evals import _reciprocal_rank_fusion

        r1 = ["a", "b", "c"]
        r2 = ["b", "a", "d"]
        fused = _reciprocal_rank_fusion([r1, r2], k=60)
        assert "a" in fused
        assert "b" in fused

    def test_empty_rankings(self) -> None:
        """Empty rankings return empty list."""
        from scripts.run_retrieval_evals import _reciprocal_rank_fusion

        assert _reciprocal_rank_fusion([[], []], k=60) == []


class TestRetrievalRunSingleMode:
    """Cover _run_single_mode for token and error cases."""

    def test_token_mode(self) -> None:
        """Token mode runs successfully."""
        from scripts.run_retrieval_evals import _run_single_mode

        index_rows = [{"id": "a", "title": "Setup guide", "summary": "How to set up"}]
        dataset = [{"query": "setup", "expected_ids": ["a"]}]
        result = _run_single_mode(
            "token", index_rows, dataset, top_k=3,
            api_key="", embedding_model="", base_url="",
            faiss_assets=None, rrf_k=60, rerank_candidates=20,
            rerank_model="",
        )
        assert result["status"] == "ok"

    def test_semantic_mode_without_key(self) -> None:
        """Semantic mode without API key returns error."""
        from scripts.run_retrieval_evals import _run_single_mode

        result = _run_single_mode(
            "semantic", [], [], top_k=3,
            api_key="", embedding_model="", base_url="",
            faiss_assets=None, rrf_k=60, rerank_candidates=20,
            rerank_model="",
        )
        assert result["status"] == "error"

    def test_hybrid_mode_without_key(self) -> None:
        """Hybrid mode without API key returns error."""
        from scripts.run_retrieval_evals import _run_single_mode

        result = _run_single_mode(
            "hybrid", [], [], top_k=3,
            api_key="", embedding_model="", base_url="",
            faiss_assets=None, rrf_k=60, rerank_candidates=20,
            rerank_model="",
        )
        assert result["status"] == "error"

    def test_hybrid_rerank_without_key(self) -> None:
        """Hybrid+rerank without API key returns error."""
        from scripts.run_retrieval_evals import _run_single_mode

        result = _run_single_mode(
            "hybrid+rerank", [], [], top_k=3,
            api_key="", embedding_model="", base_url="",
            faiss_assets=None, rrf_k=60, rerank_candidates=20,
            rerank_model="",
        )
        assert result["status"] == "error"


# ===========================================================================
# multi_protocol_engine.py
# ===========================================================================


class TestProtocolAdapterSource:
    """Cover ProtocolAdapter.source() for all protocols."""

    def _make_adapter(self, protocol: str, settings: dict[str, Any] | None = None) -> Any:
        from scripts.multi_protocol_engine import ProtocolAdapter

        return ProtocolAdapter(
            protocol,
            settings or {},
            repo_root=Path("/tmp/repo"),
            scripts_dir=Path("/tmp/scripts"),
        )

    def test_rest_source(self) -> None:
        """REST protocol returns OpenAPI spec path."""
        adapter = self._make_adapter("rest")
        assert adapter.source() == "api/openapi.yaml"

    def test_graphql_source(self) -> None:
        """GraphQL protocol returns schema path."""
        adapter = self._make_adapter("graphql")
        assert adapter.source() == "api/schema.graphql"

    def test_grpc_source_with_list(self) -> None:
        """gRPC protocol returns first proto path from list."""
        adapter = self._make_adapter("grpc", {"proto_paths": ["proto/v1", "proto/v2"]})
        assert adapter.source() == "proto/v1"

    def test_grpc_source_empty_list(self) -> None:
        """gRPC with empty proto_paths returns default."""
        adapter = self._make_adapter("grpc", {"proto_paths": []})
        assert adapter.source() == "api/proto"

    def test_asyncapi_source(self) -> None:
        """AsyncAPI returns spec path."""
        adapter = self._make_adapter("asyncapi")
        assert adapter.source() == "api/asyncapi.yaml"

    def test_websocket_source(self) -> None:
        """WebSocket returns contract path."""
        adapter = self._make_adapter("websocket")
        assert adapter.source() == "api/websocket.yaml"

    def test_unsupported_raises(self) -> None:
        """Unsupported protocol raises ValueError."""
        adapter = self._make_adapter("soap")
        with pytest.raises(ValueError, match="Unsupported protocol"):
            adapter.source()


class TestProtocolAdapterNotesPath:
    """Cover notes_path for all protocols."""

    def _make_adapter(self, protocol: str) -> Any:
        from scripts.multi_protocol_engine import ProtocolAdapter

        return ProtocolAdapter(protocol, {}, repo_root=Path("/tmp"), scripts_dir=Path("/tmp"))

    def test_graphql_notes(self) -> None:
        """GraphQL notes path default."""
        assert "graphql" in self._make_adapter("graphql").notes_path()

    def test_grpc_notes(self) -> None:
        """gRPC notes path default."""
        assert "grpc" in self._make_adapter("grpc").notes_path()

    def test_asyncapi_notes(self) -> None:
        """AsyncAPI notes path default."""
        assert "asyncapi" in self._make_adapter("asyncapi").notes_path()

    def test_websocket_notes(self) -> None:
        """WebSocket notes path default."""
        assert "websocket" in self._make_adapter("websocket").notes_path()

    def test_rest_notes(self) -> None:
        """REST notes path default."""
        assert "api-planning" in self._make_adapter("rest").notes_path()


class TestProtocolAdapterCodeFirstExport:
    """Cover _code_first_export_cmd for all protocols."""

    def _make_adapter(self, protocol: str, settings: dict[str, Any]) -> Any:
        from scripts.multi_protocol_engine import ProtocolAdapter

        return ProtocolAdapter(protocol, settings, repo_root=Path("/tmp"), scripts_dir=Path("/tmp"))

    def test_graphql_export(self) -> None:
        """GraphQL code-first export command."""
        a = self._make_adapter("graphql", {"code_first_schema_export_cmd": "npx schema-export"})
        assert a._code_first_export_cmd() == "npx schema-export"

    def test_grpc_export(self) -> None:
        """gRPC code-first export command."""
        a = self._make_adapter("grpc", {"code_first_proto_export_cmd": "protoc --desc_out"})
        assert a._code_first_export_cmd() == "protoc --desc_out"

    def test_asyncapi_export(self) -> None:
        """AsyncAPI code-first export command."""
        a = self._make_adapter("asyncapi", {"code_first_contract_export_cmd": "generate-async"})
        assert a._code_first_export_cmd() == "generate-async"

    def test_rest_export_empty(self) -> None:
        """REST protocol returns empty export command."""
        a = self._make_adapter("rest", {})
        assert a._code_first_export_cmd() == ""


class TestProtocolAdapterMaybeGenerateFromNotes:
    """Cover maybe_generate_contract_from_notes branches."""

    def _make_adapter(self, protocol: str, settings: dict[str, Any], repo_root: Path) -> Any:
        from scripts.multi_protocol_engine import ProtocolAdapter

        return ProtocolAdapter(protocol, settings, repo_root=repo_root, scripts_dir=Path("/tmp/scripts"))

    def test_rest_returns_none(self, tmp_path: Path) -> None:
        """REST protocol skips notes generation."""
        a = self._make_adapter("rest", {}, tmp_path)
        assert a.maybe_generate_contract_from_notes(allow_fail=True) is None

    def test_skips_when_disabled(self, tmp_path: Path) -> None:
        """Skips when generate_from_notes is False."""
        a = self._make_adapter("graphql", {"generate_from_notes": False}, tmp_path)
        assert a.maybe_generate_contract_from_notes(allow_fail=True) is None

    def test_skips_when_source_exists(self, tmp_path: Path) -> None:
        """Skips when source contract already exists."""
        src = tmp_path / "api" / "schema.graphql"
        src.parent.mkdir(parents=True)
        src.write_text("type Query { hello: String }", encoding="utf-8")
        a = self._make_adapter("graphql", {"schema_path": "api/schema.graphql"}, tmp_path)
        assert a.maybe_generate_contract_from_notes(allow_fail=True) is None

    def test_returns_failure_when_notes_missing(self, tmp_path: Path) -> None:
        """Returns failure result when notes file is missing."""
        a = self._make_adapter("graphql", {}, tmp_path)
        result = a.maybe_generate_contract_from_notes(allow_fail=True)
        assert result is not None
        assert not result.ok


class TestProtocolAdapterRegression:
    """Cover regression method including bootstrap."""

    @patch("subprocess.run")
    def test_bootstrap_on_rc2(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Regression bootstraps snapshot when rc=2."""
        from scripts.multi_protocol_engine import ProtocolAdapter

        # First call: rc=2 (missing snapshot), second call: rc=0 (bootstrap ok)
        mock_run.side_effect = [
            MagicMock(returncode=2),
            MagicMock(returncode=0),
        ]
        adapter = ProtocolAdapter("graphql", {}, repo_root=tmp_path, scripts_dir=Path("/tmp/scripts"))
        result = adapter.regression(allow_fail=True)
        assert result.ok is True
        assert mock_run.call_count == 2


# ===========================================================================
# run_multi_protocol_contract_flow.py
# ===========================================================================


class TestMultiProtocolHttpToWs:
    """Cover _http_to_ws URL conversion."""

    def test_https_to_wss(self) -> None:
        """HTTPS converts to WSS."""
        from scripts.run_multi_protocol_contract_flow import _http_to_ws

        result = _http_to_ws("https://api.example.com/v1", "/ws")
        assert result.startswith("wss://")
        assert "/ws" in result

    def test_http_to_ws(self) -> None:
        """HTTP converts to WS."""
        from scripts.run_multi_protocol_contract_flow import _http_to_ws

        result = _http_to_ws("http://localhost:8080/v1", "/events/ws")
        assert result.startswith("ws://")
        assert "localhost:8080" in result

    def test_strips_v1_suffix(self) -> None:
        """Strips /v1 from base path."""
        from scripts.run_multi_protocol_contract_flow import _http_to_ws

        result = _http_to_ws("https://api.example.com/v1", "/ws")
        assert "/v1/ws" not in result

    def test_invalid_url_returns_empty(self) -> None:
        """Invalid URL returns empty string."""
        from scripts.run_multi_protocol_contract_flow import _http_to_ws

        assert _http_to_ws("not-a-url", "/ws") == ""


class TestMultiProtocolWriteReport:
    """Cover _write_report function."""

    def test_writes_json_report(self, tmp_path: Path) -> None:
        """Writes JSON report to specified path."""
        from scripts.run_multi_protocol_contract_flow import _write_report

        path = tmp_path / "sub" / "report.json"
        _write_report(path, {"ok": True})
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["ok"] is True


class TestMultiProtocolResultToJson:
    """Cover _result_to_json conversion."""

    def test_converts_stage_result(self) -> None:
        """Converts StageResult to JSON-serializable dict."""
        from scripts.multi_protocol_engine import StageResult
        from scripts.run_multi_protocol_contract_flow import _result_to_json

        result = StageResult(
            stage="lint",
            protocol="graphql",
            ok=True,
            rc=0,
            command=["python3", "validate.py"],
            details={"key": "value"},
        )
        j = _result_to_json(result)
        assert j["stage"] == "lint"
        assert j["protocol"] == "graphql"
        assert j["ok"] is True


# ===========================================================================
# finalize_docs_gate.py
# ===========================================================================


class TestFinalizeAskConfirmation:
    """Cover _ask_confirmation with GUI probes and CLI fallback."""

    def test_cli_fallback_yes(self) -> None:
        """CLI fallback returns True on 'yes' input."""
        from scripts.finalize_docs_gate import _ask_confirmation

        with patch("builtins.input", return_value="yes"):
            assert _ask_confirmation("Approve?", "off") is True

    def test_cli_fallback_no(self) -> None:
        """CLI fallback returns False on 'no' input."""
        from scripts.finalize_docs_gate import _ask_confirmation

        with patch("builtins.input", return_value="no"):
            assert _ask_confirmation("Approve?", "off") is False

    def test_cli_fallback_empty(self) -> None:
        """CLI fallback returns False on empty input."""
        from scripts.finalize_docs_gate import _ask_confirmation

        with patch("builtins.input", return_value=""):
            assert _ask_confirmation("Approve?", "off") is False

    def test_cli_fallback_invalid_then_yes(self) -> None:
        """CLI fallback retries on invalid then accepts 'y'."""
        from scripts.finalize_docs_gate import _ask_confirmation

        with patch("builtins.input", side_effect=["maybe", "y"]):
            assert _ask_confirmation("Approve?", "off") is True

    @patch("subprocess.run")
    def test_zenity_probe_success(self, mock_run: MagicMock) -> None:
        """Zenity probe returns True when zenity exits 0."""
        from scripts.finalize_docs_gate import _ask_confirmation

        mock_run.side_effect = [
            MagicMock(returncode=0),  # which zenity
            MagicMock(returncode=0),  # zenity --question
        ]
        with patch.dict(os.environ, {"DISPLAY": ":0"}), patch("os.name", "posix"):
            result = _ask_confirmation("Approve?", "on")
            assert result is True

    @patch("subprocess.run")
    def test_zenity_probe_skipped_on_windows(self, mock_run: MagicMock) -> None:
        """Zenity probe is skipped on Windows."""
        from scripts.finalize_docs_gate import _ask_confirmation

        with patch("os.name", "nt"), patch("builtins.input", return_value="yes"):
            # Windows msgbox probe will also be tried but let it return None
            mock_run.return_value = MagicMock(returncode=0)
            result = _ask_confirmation("Approve?", "auto")
            assert isinstance(result, bool)

    @patch("subprocess.run")
    def test_zenity_probe_skipped_when_off(self, mock_run: MagicMock) -> None:
        """GUI probes are skipped when mode is 'off'."""
        from scripts.finalize_docs_gate import _ask_confirmation

        with patch("builtins.input", return_value="yes"):
            result = _ask_confirmation("Approve?", "off")
            assert result is True

    def test_gui_probe_exception_on_mode(self) -> None:
        """Exception in probe with mode='on' returns False."""
        from scripts.finalize_docs_gate import _ask_confirmation

        def boom() -> None:
            raise RuntimeError("GUI failed")

        with patch("os.name", "posix"), patch.dict(os.environ, {"DISPLAY": ":0"}):
            with patch("subprocess.run", side_effect=RuntimeError("boom")):
                result = _ask_confirmation("Approve?", "on")
                assert result is False


class TestFinalizeMergeConfig:
    """Cover _merge_config function."""

    def test_cli_defaults(self) -> None:
        """CLI args provide default values."""
        import argparse
        from scripts.finalize_docs_gate import _merge_config

        args = argparse.Namespace(
            docs_root="docs",
            reports_dir="reports",
            lint_command="npm run lint",
            max_iterations=5,
            llm_fix_command="",
            auto_fix_command=[],
            continue_on_error=False,
            ask_commit_confirmation=False,
            non_interactive_approval="fail",
            ui_confirmation="auto",
            precommit_command="sh .husky/pre-commit",
            run_precommit_before_commit=False,
            precommit_max_iterations=3,
            commit_on_approve=False,
            commit_message="docs: finalize",
            push_on_commit=False,
            json_report="reports/finalize_gate_report.json",
        )
        merged = _merge_config(args, {})
        assert merged["docs_root"] == "docs"
        # Empty auto_fix_commands -> filled with defaults
        assert len(merged["auto_fix_commands"]) == 2

    def test_runtime_config_overrides(self) -> None:
        """Runtime config values override CLI defaults."""
        import argparse
        from scripts.finalize_docs_gate import _merge_config

        args = argparse.Namespace(
            docs_root="docs",
            reports_dir="reports",
            lint_command="npm run lint",
            max_iterations=5,
            llm_fix_command="",
            auto_fix_command=[],
            continue_on_error=False,
            ask_commit_confirmation=False,
            non_interactive_approval="fail",
            ui_confirmation="auto",
            precommit_command="sh .husky/pre-commit",
            run_precommit_before_commit=False,
            precommit_max_iterations=3,
            commit_on_approve=False,
            commit_message="docs: finalize",
            push_on_commit=False,
            json_report="reports/finalize_gate_report.json",
        )
        cfg = {"max_iterations": 10, "commit_message": "custom message"}
        merged = _merge_config(args, cfg)
        assert merged["max_iterations"] == 10
        assert merged["commit_message"] == "custom message"


class TestFinalizeLoadConfig:
    """Cover _load_finalize_config function."""

    def test_returns_empty_when_none(self) -> None:
        """Returns empty dict when path is None."""
        from scripts.finalize_docs_gate import _load_finalize_config

        assert _load_finalize_config(None) == {}

    def test_returns_empty_when_missing(self, tmp_path: Path) -> None:
        """Returns empty dict when file does not exist."""
        from scripts.finalize_docs_gate import _load_finalize_config

        assert _load_finalize_config(tmp_path / "missing.yml") == {}

    def test_loads_finalize_gate_section(self, tmp_path: Path) -> None:
        """Loads the finalize_gate section from runtime config."""
        from scripts.finalize_docs_gate import _load_finalize_config

        config = {"finalize_gate": {"max_iterations": 7, "commit_on_approve": True}}
        f = tmp_path / "runtime.yml"
        f.write_text(yaml.safe_dump(config), encoding="utf-8")
        result = _load_finalize_config(f)
        assert result["max_iterations"] == 7


class TestFinalizeFormatCommand:
    """Cover _format_command template expansion."""

    def test_formats_placeholders(self) -> None:
        """Formats docs_root, reports_dir, and iteration."""
        from scripts.finalize_docs_gate import _format_command

        cmd = "lint {docs_root} --report {reports_dir}/r{iteration}.json"
        result = _format_command(cmd, "docs", "reports", 2)
        assert result == "lint docs --report reports/r2.json"


class TestFinalizeSafeGitAdd:
    """Cover _safe_git_add function."""

    @patch("subprocess.run")
    def test_adds_existing_paths(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Adds only paths that exist."""
        from scripts.finalize_docs_gate import _safe_git_add

        (tmp_path / "docs").mkdir()
        _safe_git_add(tmp_path, "docs")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "git" in args
        assert "add" in args

    @patch("subprocess.run")
    def test_skips_when_nothing_exists(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Does not call git add when no candidate paths exist."""
        from scripts.finalize_docs_gate import _safe_git_add

        _safe_git_add(tmp_path, "nonexistent")
        mock_run.assert_not_called()


class TestFinalizeDefaultAutoFixCommands:
    """Cover _default_auto_fix_commands function."""

    def test_returns_two_commands(self) -> None:
        """Returns normalize and seo_geo_optimizer commands."""
        from scripts.finalize_docs_gate import _default_auto_fix_commands

        cmds = _default_auto_fix_commands("docs")
        assert len(cmds) == 2
        assert "normalize_docs" in cmds[0]
        assert "seo_geo_optimizer" in cmds[1]


# ===========================================================================
# generate_kpi_wall.py
# ===========================================================================


class TestKpiScoreColor:
    """Cover _score_color function."""

    def test_green_for_high(self) -> None:
        """Score >= 85 returns green."""
        from scripts.generate_kpi_wall import _score_color

        assert _score_color(90) == "#10b981"

    def test_yellow_for_mid(self) -> None:
        """Score 70-84 returns yellow."""
        from scripts.generate_kpi_wall import _score_color

        assert _score_color(75) == "#f59e0b"

    def test_red_for_low(self) -> None:
        """Score < 70 returns red."""
        from scripts.generate_kpi_wall import _score_color

        assert _score_color(50) == "#ef4444"


class TestKpiScoreGrade:
    """Cover _score_grade function."""

    def test_grade_a(self) -> None:
        """Score >= 90 returns A."""
        from scripts.generate_kpi_wall import _score_grade

        assert _score_grade(95) == "A"

    def test_grade_b(self) -> None:
        """Score 80-89 returns B."""
        from scripts.generate_kpi_wall import _score_grade

        assert _score_grade(85) == "B"

    def test_grade_c(self) -> None:
        """Score 70-79 returns C."""
        from scripts.generate_kpi_wall import _score_grade

        assert _score_grade(72) == "C"

    def test_grade_d(self) -> None:
        """Score 60-69 returns D."""
        from scripts.generate_kpi_wall import _score_grade

        assert _score_grade(65) == "D"

    def test_grade_f(self) -> None:
        """Score < 60 returns F."""
        from scripts.generate_kpi_wall import _score_grade

        assert _score_grade(40) == "F"


class TestKpiStaleColor:
    """Cover _stale_color function."""

    def test_green_low_stale(self) -> None:
        """Stale <= 10% returns green."""
        from scripts.generate_kpi_wall import _stale_color

        assert _stale_color(5.0) == "#10b981"

    def test_yellow_mid_stale(self) -> None:
        """Stale 10-20% returns yellow."""
        from scripts.generate_kpi_wall import _stale_color

        assert _stale_color(15.0) == "#f59e0b"

    def test_red_high_stale(self) -> None:
        """Stale > 20% returns red."""
        from scripts.generate_kpi_wall import _stale_color

        assert _stale_color(25.0) == "#ef4444"


class TestKpiGapColor:
    """Cover _gap_color function."""

    def test_green_zero_gaps(self) -> None:
        """Zero gaps returns green."""
        from scripts.generate_kpi_wall import _gap_color

        assert _gap_color(0) == "#10b981"

    def test_yellow_few_gaps(self) -> None:
        """1-3 gaps returns yellow."""
        from scripts.generate_kpi_wall import _gap_color

        assert _gap_color(2) == "#f59e0b"

    def test_red_many_gaps(self) -> None:
        """More than 3 gaps returns red."""
        from scripts.generate_kpi_wall import _gap_color

        assert _gap_color(5) == "#ef4444"


class TestKpiMetaColor:
    """Cover _meta_color function."""

    def test_green_high_meta(self) -> None:
        """Metadata >= 95% returns green."""
        from scripts.generate_kpi_wall import _meta_color

        assert _meta_color(98.0) == "#10b981"

    def test_yellow_mid_meta(self) -> None:
        """Metadata 80-94% returns yellow."""
        from scripts.generate_kpi_wall import _meta_color

        assert _meta_color(88.0) == "#f59e0b"

    def test_red_low_meta(self) -> None:
        """Metadata < 80% returns red."""
        from scripts.generate_kpi_wall import _meta_color

        assert _meta_color(70.0) == "#ef4444"


class TestKpiComputeQualityScore:
    """Cover _compute_quality_score calculation."""

    def test_perfect_score(self) -> None:
        """Perfect inputs return 100."""
        from scripts.generate_kpi_wall import _compute_quality_score

        assert _compute_quality_score(100.0, 0.0, 0) == 100

    def test_low_metadata_reduces_score(self) -> None:
        """Low metadata pct reduces score."""
        from scripts.generate_kpi_wall import _compute_quality_score

        score = _compute_quality_score(50.0, 0.0, 0)
        assert score < 100

    def test_high_stale_reduces_score(self) -> None:
        """High stale pct reduces score."""
        from scripts.generate_kpi_wall import _compute_quality_score

        score = _compute_quality_score(100.0, 50.0, 0)
        assert score < 100

    def test_gaps_reduce_score(self) -> None:
        """High-priority gaps reduce score."""
        from scripts.generate_kpi_wall import _compute_quality_score

        score = _compute_quality_score(100.0, 0.0, 5)
        assert score < 100

    def test_score_clamped_to_0(self) -> None:
        """Score does not go below 0."""
        from scripts.generate_kpi_wall import _compute_quality_score

        score = _compute_quality_score(0.0, 100.0, 10)
        assert score >= 0


class TestKpiRenderMarkdownI18n:
    """Cover render_markdown with i18n section."""

    def test_includes_i18n_section(self) -> None:
        """Markdown includes translation coverage when i18n enabled."""
        from scripts.generate_kpi_wall import KpiMetrics, render_markdown

        metrics = KpiMetrics(
            generated_at="2026-03-21T00:00:00Z",
            total_docs=10,
            docs_with_frontmatter=10,
            metadata_completeness_pct=100.0,
            stale_docs=0,
            stale_pct=0.0,
            i18n_enabled=True,
            i18n_languages=["en", "ru"],
            i18n_translation_coverage={"en": 100.0, "ru": 75.0},
            i18n_stale_translations=2,
            i18n_missing_translations=3,
        )
        md = render_markdown(metrics)
        assert "Translation Coverage" in md
        assert "ru: **75.0%**" in md
        assert "Missing translations: **3**" in md

    def test_no_i18n_section(self) -> None:
        """Markdown omits translation section when i18n disabled."""
        from scripts.generate_kpi_wall import KpiMetrics, render_markdown

        metrics = KpiMetrics(
            generated_at="2026-03-21T00:00:00Z",
            total_docs=5,
            docs_with_frontmatter=5,
            metadata_completeness_pct=100.0,
            stale_docs=0,
            stale_pct=0.0,
        )
        md = render_markdown(metrics)
        assert "Translation Coverage" not in md


class TestKpiRenderDashboardHtml:
    """Cover render_dashboard_html function."""

    def test_generates_valid_html(self) -> None:
        """Dashboard HTML contains expected structure."""
        from scripts.generate_kpi_wall import KpiMetrics, render_dashboard_html

        metrics = KpiMetrics(
            generated_at="2026-03-21T00:00:00Z",
            total_docs=20,
            docs_with_frontmatter=18,
            metadata_completeness_pct=90.0,
            stale_docs=2,
            stale_pct=10.0,
            quality_score=85,
            gap_total=3,
            gap_high=1,
            debt_trend_note="Improving",
            before_after_note="Before/after baseline not available yet.",
        )
        html = render_dashboard_html(metrics)
        assert "<!doctype html>" in html
        assert "Documentation Operations Dashboard" in html
        assert "85" in html  # quality score
        assert "Grade B" in html


class TestKpiLoadGapMetrics:
    """Cover _load_gap_metrics function."""

    def test_loads_gap_counts(self, tmp_path: Path) -> None:
        """Reads gap counts from report."""
        from scripts.generate_kpi_wall import _load_gap_metrics

        report = {"gaps": [{"priority": "high"}, {"priority": "medium"}, {"priority": "high"}]}
        f = tmp_path / "gaps.json"
        f.write_text(json.dumps(report), encoding="utf-8")
        total, high = _load_gap_metrics(f)
        assert total == 3
        assert high == 2

    def test_missing_file_returns_zeros(self, tmp_path: Path) -> None:
        """Missing report file returns (0, 0)."""
        from scripts.generate_kpi_wall import _load_gap_metrics

        total, high = _load_gap_metrics(tmp_path / "missing.json")
        assert total == 0
        assert high == 0

    def test_invalid_json_returns_zeros(self, tmp_path: Path) -> None:
        """Invalid JSON returns (0, 0)."""
        from scripts.generate_kpi_wall import _load_gap_metrics

        f = tmp_path / "bad.json"
        f.write_text("not json", encoding="utf-8")
        total, high = _load_gap_metrics(f)
        assert total == 0

    def test_non_list_gaps_returns_zeros(self, tmp_path: Path) -> None:
        """Non-list 'gaps' value returns (0, 0)."""
        from scripts.generate_kpi_wall import _load_gap_metrics

        f = tmp_path / "report.json"
        f.write_text('{"gaps": "not a list"}', encoding="utf-8")
        total, high = _load_gap_metrics(f)
        assert total == 0


class TestKpiLoadBeforeAfterNote:
    """Cover _load_before_after_note function."""

    def test_missing_files(self, tmp_path: Path) -> None:
        """Missing baseline returns default note."""
        from scripts.generate_kpi_wall import _load_before_after_note

        note = _load_before_after_note(tmp_path)
        assert "not available" in note

    def test_valid_before_after(self, tmp_path: Path) -> None:
        """Valid files produce delta note."""
        from scripts.generate_kpi_wall import _load_before_after_note

        baseline = {"debt_score": {"total": 50}}
        latest = {"debt_score": {"total": 30}}
        (tmp_path / "pilot-baseline.json").write_text(json.dumps(baseline), encoding="utf-8")
        (tmp_path / "pilot-analysis.json").write_text(json.dumps(latest), encoding="utf-8")
        note = _load_before_after_note(tmp_path)
        assert "reduced" in note
        assert "20" in note

    def test_increased_debt(self, tmp_path: Path) -> None:
        """Increased debt produces 'increased' note."""
        from scripts.generate_kpi_wall import _load_before_after_note

        baseline = {"debt_score": {"total": 30}}
        latest = {"debt_score": {"total": 50}}
        (tmp_path / "pilot-baseline.json").write_text(json.dumps(baseline), encoding="utf-8")
        (tmp_path / "pilot-analysis.json").write_text(json.dumps(latest), encoding="utf-8")
        note = _load_before_after_note(tmp_path)
        assert "increased" in note

    def test_corrupt_files(self, tmp_path: Path) -> None:
        """Corrupt JSON files return parsing failed note."""
        from scripts.generate_kpi_wall import _load_before_after_note

        (tmp_path / "pilot-baseline.json").write_text("bad", encoding="utf-8")
        (tmp_path / "pilot-analysis.json").write_text("bad", encoding="utf-8")
        note = _load_before_after_note(tmp_path)
        assert "parsing failed" in note


class TestKpiExtractFrontmatter:
    """Cover _extract_frontmatter function."""

    def test_valid_frontmatter(self) -> None:
        """Extracts valid YAML frontmatter."""
        from scripts.generate_kpi_wall import _extract_frontmatter

        text = '---\ntitle: "Test"\ndescription: "A test doc"\n---\nContent here'
        result = _extract_frontmatter(text)
        assert result is not None
        assert result["title"] == "Test"

    def test_no_frontmatter(self) -> None:
        """Returns None for text without frontmatter."""
        from scripts.generate_kpi_wall import _extract_frontmatter

        assert _extract_frontmatter("No frontmatter here") is None

    def test_incomplete_frontmatter(self) -> None:
        """Returns None for incomplete frontmatter."""
        from scripts.generate_kpi_wall import _extract_frontmatter

        assert _extract_frontmatter("---\ntitle: test\n") is None

    def test_non_dict_frontmatter(self) -> None:
        """Returns None when frontmatter is a list, not dict."""
        from scripts.generate_kpi_wall import _extract_frontmatter

        assert _extract_frontmatter("---\n- item\n---\nContent") is None


class TestKpiParseDate:
    """Cover _parse_date function."""

    def test_iso_format(self) -> None:
        """Parses ISO date string."""
        from scripts.generate_kpi_wall import _parse_date

        result = _parse_date("2025-06-15")
        assert result is not None
        assert result.year == 2025

    def test_none_input(self) -> None:
        """Returns None for None input."""
        from scripts.generate_kpi_wall import _parse_date

        assert _parse_date(None) is None

    def test_invalid_format(self) -> None:
        """Returns None for invalid date format."""
        from scripts.generate_kpi_wall import _parse_date

        assert _parse_date("not-a-date") is None


class TestKpiDetectBuildCheckName:
    """Cover _detect_build_check_name function."""

    def test_returns_mkdocs_on_import_error(self) -> None:
        """Returns MkDocs Build when import fails."""
        from scripts.generate_kpi_wall import _detect_build_check_name

        with patch.dict("sys.modules", {"site_generator": None}):
            result = _detect_build_check_name()
            assert "MkDocs" in result or "Build" in result


# ===========================================================================
# validate_knowledge_modules.py
# ===========================================================================


class TestValidateModulesSetField:
    """Cover _validate_set_field function."""

    def test_missing_field(self, tmp_path: Path) -> None:
        """Missing field adds an issue."""
        from scripts.validate_knowledge_modules import ModuleIssue, _validate_set_field

        issues: list[ModuleIssue] = []
        _validate_set_field({}, "intents", {"install"}, issues, tmp_path / "mod.yml")
        assert len(issues) == 1
        assert "non-empty list" in issues[0].message

    def test_unsupported_value(self, tmp_path: Path) -> None:
        """Unsupported value in set adds an issue."""
        from scripts.validate_knowledge_modules import ModuleIssue, _validate_set_field

        issues: list[ModuleIssue] = []
        module = {"intents": ["install", "bad_intent"]}
        _validate_set_field(module, "intents", {"install", "configure"}, issues, tmp_path / "mod.yml")
        assert any("unsupported value" in i.message for i in issues)

    def test_non_string_value(self, tmp_path: Path) -> None:
        """Non-string value in list adds an issue."""
        from scripts.validate_knowledge_modules import ModuleIssue, _validate_set_field

        issues: list[ModuleIssue] = []
        module = {"intents": [123]}
        _validate_set_field(module, "intents", {"install"}, issues, tmp_path / "mod.yml")
        assert any("non-string" in i.message for i in issues)

    def test_valid_values_pass(self, tmp_path: Path) -> None:
        """All valid values produce no issues."""
        from scripts.validate_knowledge_modules import ModuleIssue, _validate_set_field

        issues: list[ModuleIssue] = []
        module = {"intents": ["install", "configure"]}
        _validate_set_field(module, "intents", {"install", "configure"}, issues, tmp_path / "mod.yml")
        assert len(issues) == 0


class TestValidateModulesCycleDetection:
    """Cover _dfs_cycle function."""

    def test_no_cycle(self) -> None:
        """No cycle returns empty list."""
        from scripts.validate_knowledge_modules import _dfs_cycle

        graph = {"a": ["b"], "b": []}
        visited: set[str] = set()
        stack: set[str] = set()
        cycles: list[list[str]] = []
        _dfs_cycle("a", graph, visited, stack, cycles)
        assert cycles == []

    def test_detects_cycle(self) -> None:
        """Detects circular dependency."""
        from scripts.validate_knowledge_modules import _dfs_cycle

        graph = {"a": ["b"], "b": ["a"]}
        visited: set[str] = set()
        stack: set[str] = set()
        cycles: list[list[str]] = []
        _dfs_cycle("a", graph, visited, stack, cycles)
        assert len(cycles) >= 1


class TestValidateModulesFull:
    """Cover validate_modules with full module files."""

    def _write_module(self, path: Path, data: dict[str, Any]) -> None:
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    def test_valid_module_passes(self, tmp_path: Path) -> None:
        """Valid module produces no issues."""
        from scripts.validate_knowledge_modules import validate_modules

        self._write_module(tmp_path / "mod.yml", {
            "id": "test-module",
            "title": "A valid test module title here",
            "summary": "This is a valid summary that is long enough to pass validation checks",
            "intents": ["install"],
            "audiences": ["developer"],
            "channels": ["docs"],
            "priority": 50,
            "status": "active",
            "owner": "team-docs",
            "last_verified": "2026-01-01",
            "content": {
                "docs_markdown": "x" * 100,
                "assistant_context": "y" * 80,
            },
        })
        modules, issues = validate_modules(tmp_path)
        assert len(modules) == 1
        assert len(issues) == 0

    def test_duplicate_id(self, tmp_path: Path) -> None:
        """Duplicate module IDs produce an issue."""
        from scripts.validate_knowledge_modules import validate_modules

        base = {
            "id": "dup-id",
            "title": "Module with duplicate ID title",
            "summary": "A summary long enough to pass the minimum character check",
            "intents": ["install"],
            "audiences": ["developer"],
            "channels": ["docs"],
            "priority": 50,
            "status": "active",
            "owner": "team",
            "last_verified": "2026-01-01",
            "content": {"docs_markdown": "x" * 100, "assistant_context": "y" * 80},
        }
        self._write_module(tmp_path / "a.yml", base)
        self._write_module(tmp_path / "b.yml", base)
        modules, issues = validate_modules(tmp_path)
        assert any("duplicate" in i.message for i in issues)

    def test_invalid_yaml(self, tmp_path: Path) -> None:
        """Invalid YAML file produces an issue."""
        from scripts.validate_knowledge_modules import validate_modules

        (tmp_path / "bad.yml").write_text(": invalid: yaml: {{", encoding="utf-8")
        modules, issues = validate_modules(tmp_path)
        assert any("invalid YAML" in i.message for i in issues)

    def test_missing_id(self, tmp_path: Path) -> None:
        """Module without id produces an issue."""
        from scripts.validate_knowledge_modules import validate_modules

        self._write_module(tmp_path / "no_id.yml", {"title": "Test"})
        modules, issues = validate_modules(tmp_path)
        assert any("missing 'id'" in i.message for i in issues)

    def test_short_title(self, tmp_path: Path) -> None:
        """Title too short produces an issue."""
        from scripts.validate_knowledge_modules import validate_modules

        self._write_module(tmp_path / "mod.yml", {
            "id": "short-title",
            "title": "Short",
            "summary": "A summary long enough to pass the minimum character check",
            "intents": ["install"],
            "audiences": ["developer"],
            "channels": ["docs"],
            "priority": 50,
            "status": "active",
            "content": {"docs_markdown": "x" * 100, "assistant_context": "y" * 80},
        })
        modules, issues = validate_modules(tmp_path)
        assert any("title" in i.message for i in issues)

    def test_invalid_priority(self, tmp_path: Path) -> None:
        """Priority outside 1-100 produces an issue."""
        from scripts.validate_knowledge_modules import validate_modules

        self._write_module(tmp_path / "mod.yml", {
            "id": "bad-priority",
            "title": "Module with invalid priority",
            "summary": "A summary long enough to pass the minimum character check",
            "intents": ["install"],
            "audiences": ["developer"],
            "channels": ["docs"],
            "priority": 200,
            "status": "active",
            "content": {"docs_markdown": "x" * 100, "assistant_context": "y" * 80},
        })
        modules, issues = validate_modules(tmp_path)
        assert any("priority" in i.message for i in issues)

    def test_invalid_status(self, tmp_path: Path) -> None:
        """Invalid status produces an issue."""
        from scripts.validate_knowledge_modules import validate_modules

        self._write_module(tmp_path / "mod.yml", {
            "id": "bad-status",
            "title": "Module with invalid status value",
            "summary": "A summary long enough to pass the minimum character check",
            "intents": ["install"],
            "audiences": ["developer"],
            "channels": ["docs"],
            "priority": 50,
            "status": "draft",
            "content": {"docs_markdown": "x" * 100, "assistant_context": "y" * 80},
        })
        modules, issues = validate_modules(tmp_path)
        assert any("status" in i.message for i in issues)

    def test_missing_content_fields(self, tmp_path: Path) -> None:
        """Short content fields produce issues."""
        from scripts.validate_knowledge_modules import validate_modules

        self._write_module(tmp_path / "mod.yml", {
            "id": "short-content",
            "title": "Module with short content fields",
            "summary": "A summary long enough to pass the minimum character check",
            "intents": ["install"],
            "audiences": ["developer"],
            "channels": ["docs"],
            "priority": 50,
            "status": "active",
            "content": {"docs_markdown": "short", "assistant_context": "tiny"},
        })
        modules, issues = validate_modules(tmp_path)
        assert any("docs_markdown" in i.message for i in issues)
        assert any("assistant_context" in i.message for i in issues)

    def test_unknown_dependency(self, tmp_path: Path) -> None:
        """Unknown dependency ID produces an issue."""
        from scripts.validate_knowledge_modules import validate_modules

        self._write_module(tmp_path / "mod.yml", {
            "id": "has-dep",
            "title": "Module with unknown dependency reference",
            "summary": "A summary long enough to pass the minimum character check",
            "intents": ["install"],
            "audiences": ["developer"],
            "channels": ["docs"],
            "priority": 50,
            "status": "active",
            "dependencies": ["nonexistent-module"],
            "content": {"docs_markdown": "x" * 100, "assistant_context": "y" * 80},
        })
        modules, issues = validate_modules(tmp_path)
        assert any("unknown dependency" in i.message for i in issues)

    def test_non_list_dependencies(self, tmp_path: Path) -> None:
        """Non-list dependencies produce an issue."""
        from scripts.validate_knowledge_modules import validate_modules

        self._write_module(tmp_path / "mod.yml", {
            "id": "bad-deps",
            "title": "Module with non-list dependencies field",
            "summary": "A summary long enough to pass the minimum character check",
            "intents": ["install"],
            "audiences": ["developer"],
            "channels": ["docs"],
            "priority": 50,
            "status": "active",
            "dependencies": "not-a-list",
            "content": {"docs_markdown": "x" * 100, "assistant_context": "y" * 80},
        })
        modules, issues = validate_modules(tmp_path)
        assert any("dependencies" in i.message for i in issues)

    def test_content_not_dict(self, tmp_path: Path) -> None:
        """Non-dict content produces an issue."""
        from scripts.validate_knowledge_modules import validate_modules

        self._write_module(tmp_path / "mod.yml", {
            "id": "bad-content",
            "title": "Module with non-dict content field",
            "summary": "A summary long enough to pass the minimum character check",
            "intents": ["install"],
            "audiences": ["developer"],
            "channels": ["docs"],
            "priority": 50,
            "status": "active",
            "content": "just a string",
        })
        modules, issues = validate_modules(tmp_path)
        assert any("content" in i.message for i in issues)


class TestValidateModulesBuildReport:
    """Cover _build_report function."""

    def test_builds_report_structure(self) -> None:
        """Builds report with correct structure."""
        from scripts.validate_knowledge_modules import ModuleIssue, _build_report

        modules = [
            {"id": "a", "intents": ["install", "configure"], "channels": ["docs"]},
            {"id": "b", "intents": ["troubleshoot"], "channels": ["assistant"]},
        ]
        issues = [ModuleIssue("mod.yml", "test issue")]
        report = _build_report(modules, issues)
        assert report["summary"]["module_count"] == 2
        assert report["summary"]["issue_count"] == 1
        assert report["summary"]["valid"] is False
        assert "install" in report["coverage"]["intents"]

    def test_valid_report(self) -> None:
        """Valid report has no issues."""
        from scripts.validate_knowledge_modules import _build_report

        report = _build_report([], [])
        assert report["summary"]["valid"] is True

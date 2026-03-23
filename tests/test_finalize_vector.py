"""Tests for finalize_docs_gate.py and vector_store.py -- zero-coverage scripts."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# finalize_docs_gate helpers
# ---------------------------------------------------------------------------


class TestReadYaml:
    """Tests for _read_yaml: safe YAML loading."""

    def test_valid_yaml_returns_dict(self, tmp_path: Path) -> None:
        """Valid YAML mapping is loaded as dict."""
        p = tmp_path / "good.yml"
        p.write_text("key: value\nnested:\n  a: 1\n", encoding="utf-8")

        from scripts.finalize_docs_gate import _read_yaml

        result = _read_yaml(p)
        assert result == {"key": "value", "nested": {"a": 1}}

    def test_empty_yaml_returns_empty_dict(self, tmp_path: Path) -> None:
        """Empty YAML file returns empty dict (not None)."""
        p = tmp_path / "empty.yml"
        p.write_text("", encoding="utf-8")

        from scripts.finalize_docs_gate import _read_yaml

        result = _read_yaml(p)
        assert result == {}

    def test_yaml_with_only_null_returns_empty_dict(self, tmp_path: Path) -> None:
        """YAML containing only null returns empty dict."""
        p = tmp_path / "null.yml"
        p.write_text("---\n", encoding="utf-8")

        from scripts.finalize_docs_gate import _read_yaml

        result = _read_yaml(p)
        assert result == {}

    def test_yaml_list_raises_value_error(self, tmp_path: Path) -> None:
        """YAML file that is a list (not a mapping) raises ValueError."""
        p = tmp_path / "list.yml"
        p.write_text("- item1\n- item2\n", encoding="utf-8")

        from scripts.finalize_docs_gate import _read_yaml

        with pytest.raises(ValueError, match="Expected YAML mapping"):
            _read_yaml(p)


class TestRun:
    """Tests for _run: subprocess wrapper."""

    def test_successful_command(self, tmp_path: Path) -> None:
        """Successful command returns exit code 0 with captured output."""
        from scripts.finalize_docs_gate import _run

        result = _run("echo hello", tmp_path)
        assert result.return_code == 0
        assert "hello" in result.output
        assert result.command == "echo hello"

    def test_failing_command(self, tmp_path: Path) -> None:
        """Failing command returns non-zero exit code."""
        from scripts.finalize_docs_gate import _run

        result = _run("false", tmp_path)
        assert result.return_code != 0

    def test_command_result_dataclass(self, tmp_path: Path) -> None:
        """CommandResult has command, return_code, and output fields."""
        from scripts.finalize_docs_gate import _run

        result = _run("echo test_output", tmp_path)
        assert hasattr(result, "command")
        assert hasattr(result, "return_code")
        assert hasattr(result, "output")


class TestFormatCommand:
    """Tests for _format_command: placeholder substitution."""

    def test_substitutes_all_placeholders(self) -> None:
        """All three placeholders are substituted correctly."""
        from scripts.finalize_docs_gate import _format_command

        cmd = "lint {docs_root} --report {reports_dir}/r{iteration}.json"
        result = _format_command(cmd, "docs", "reports", 3)
        assert result == "lint docs --report reports/r3.json"

    def test_no_placeholders_unchanged(self) -> None:
        """Command without placeholders is returned unchanged."""
        from scripts.finalize_docs_gate import _format_command

        assert _format_command("npm run lint", "d", "r", 1) == "npm run lint"

    def test_repeated_placeholders(self) -> None:
        """Same placeholder used multiple times is substituted in each occurrence."""
        from scripts.finalize_docs_gate import _format_command

        cmd = "{docs_root} {docs_root}"
        assert _format_command(cmd, "X", "Y", 1) == "X X"


class TestDefaultAutoFixCommands:
    """Tests for _default_auto_fix_commands."""

    def test_returns_two_commands(self) -> None:
        """Returns normalize_docs and seo_geo_optimizer commands."""
        from scripts.finalize_docs_gate import _default_auto_fix_commands

        cmds = _default_auto_fix_commands("docs")
        assert len(cmds) == 2
        assert "normalize_docs" in cmds[0]
        assert "seo_geo_optimizer" in cmds[1]

    def test_docs_root_quoted_in_commands(self) -> None:
        """Docs root with spaces is shell-quoted in commands."""
        from scripts.finalize_docs_gate import _default_auto_fix_commands

        cmds = _default_auto_fix_commands("path with spaces")
        assert "'path with spaces'" in cmds[0] or '"path with spaces"' in cmds[0]

    def test_seo_fix_flag_present(self) -> None:
        """The --fix flag is present in the seo_geo_optimizer command."""
        from scripts.finalize_docs_gate import _default_auto_fix_commands

        cmds = _default_auto_fix_commands("docs")
        assert "--fix" in cmds[1]


class TestSafeGitAdd:
    """Tests for _safe_git_add: adds existing files to git staging."""

    def test_adds_existing_paths(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Only existing candidate paths are passed to git add."""
        from scripts import finalize_docs_gate as mod

        (tmp_path / "my_docs").mkdir()
        (tmp_path / "mkdocs.yml").write_text("nav: []", encoding="utf-8")
        calls: list[Any] = []

        def fake_run(cmd: list[str], **kwargs: Any) -> SimpleNamespace:
            calls.append(cmd)
            return SimpleNamespace(returncode=0)

        monkeypatch.setattr(mod.subprocess, "run", fake_run)
        mod._safe_git_add(tmp_path, "my_docs")
        assert len(calls) == 1
        assert "my_docs" in calls[0]
        assert "mkdocs.yml" in calls[0]

    def test_no_existing_paths_skips_git_add(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """When no candidate paths exist, git add is not called."""
        from scripts import finalize_docs_gate as mod

        calls: list[Any] = []

        def fake_run(cmd: list[str], **kwargs: Any) -> SimpleNamespace:
            calls.append(cmd)
            return SimpleNamespace(returncode=0)

        monkeypatch.setattr(mod.subprocess, "run", fake_run)
        mod._safe_git_add(tmp_path, "nonexistent_docs")
        assert len(calls) == 0


class TestLoadFinalizeConfig:
    """Tests for _load_finalize_config."""

    def test_none_path_returns_empty(self) -> None:
        """None config path returns empty dict."""
        from scripts.finalize_docs_gate import _load_finalize_config

        assert _load_finalize_config(None) == {}

    def test_nonexistent_path_returns_empty(self, tmp_path: Path) -> None:
        """Path that does not exist returns empty dict."""
        from scripts.finalize_docs_gate import _load_finalize_config

        assert _load_finalize_config(tmp_path / "missing.yml") == {}

    def test_valid_config_returns_finalize_gate_block(self, tmp_path: Path) -> None:
        """Returns the finalize_gate block from the runtime config."""
        from scripts.finalize_docs_gate import _load_finalize_config

        cfg = tmp_path / "runtime.yml"
        cfg.write_text(
            "finalize_gate:\n  max_iterations: 10\n  lint_command: 'make lint'\n",
            encoding="utf-8",
        )
        result = _load_finalize_config(cfg)
        assert result["max_iterations"] == 10
        assert result["lint_command"] == "make lint"

    def test_missing_finalize_gate_block_returns_empty(self, tmp_path: Path) -> None:
        """Config without finalize_gate key returns empty dict."""
        from scripts.finalize_docs_gate import _load_finalize_config

        cfg = tmp_path / "runtime.yml"
        cfg.write_text("other_key: 42\n", encoding="utf-8")
        result = _load_finalize_config(cfg)
        assert result == {}

    def test_finalize_gate_non_dict_returns_empty(self, tmp_path: Path) -> None:
        """If finalize_gate is a scalar (not dict), returns empty dict."""
        from scripts.finalize_docs_gate import _load_finalize_config

        cfg = tmp_path / "runtime.yml"
        cfg.write_text("finalize_gate: 'just a string'\n", encoding="utf-8")
        result = _load_finalize_config(cfg)
        assert result == {}


class TestParseArgs:
    """Tests for parse_args: CLI argument parsing."""

    def test_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """All defaults are set when no arguments are provided."""
        from scripts.finalize_docs_gate import parse_args

        monkeypatch.setattr(sys, "argv", ["finalize_docs_gate.py"])
        args = parse_args()
        assert args.docs_root == "docs"
        assert args.reports_dir == "reports"
        assert args.max_iterations == 5
        assert args.lint_command == "npm run lint"
        assert args.continue_on_error is False
        assert args.non_interactive_approval == "fail"

    def test_custom_args(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Custom CLI arguments override defaults."""
        from scripts.finalize_docs_gate import parse_args

        monkeypatch.setattr(
            sys, "argv",
            [
                "finalize_docs_gate.py",
                "--docs-root", "my_docs",
                "--max-iterations", "10",
                "--continue-on-error",
                "--commit-on-approve",
                "--push-on-commit",
                "--non-interactive-approval", "approve",
            ],
        )
        args = parse_args()
        assert args.docs_root == "my_docs"
        assert args.max_iterations == 10
        assert args.continue_on_error is True
        assert args.commit_on_approve is True
        assert args.push_on_commit is True
        assert args.non_interactive_approval == "approve"


class TestMergeConfig:
    """Tests for _merge_config: CLI args + YAML config merge."""

    def _make_args(self, **overrides: Any) -> SimpleNamespace:
        """Create a namespace with default arg values."""
        defaults = {
            "docs_root": "docs",
            "reports_dir": "reports",
            "lint_command": "npm run lint",
            "max_iterations": 5,
            "llm_fix_command": "",
            "auto_fix_command": [],
            "continue_on_error": False,
            "ask_commit_confirmation": False,
            "non_interactive_approval": "fail",
            "ui_confirmation": "auto",
            "precommit_command": "sh .husky/pre-commit",
            "run_precommit_before_commit": False,
            "precommit_max_iterations": 3,
            "commit_on_approve": False,
            "commit_message": "docs: finalize generated docs",
            "push_on_commit": False,
            "json_report": "reports/finalize_gate_report.json",
        }
        defaults.update(overrides)
        return SimpleNamespace(**defaults)

    def test_cli_defaults_no_config(self) -> None:
        """With empty config, merged result matches CLI defaults."""
        from scripts.finalize_docs_gate import _merge_config

        args = self._make_args()
        merged = _merge_config(args, {})
        assert merged["docs_root"] == "docs"
        assert merged["lint_command"] == "npm run lint"
        assert merged["max_iterations"] == 5

    def test_config_overrides_cli(self) -> None:
        """Config values override matching CLI defaults."""
        from scripts.finalize_docs_gate import _merge_config

        args = self._make_args()
        cfg = {"max_iterations": 10, "lint_command": "make lint"}
        merged = _merge_config(args, cfg)
        assert merged["max_iterations"] == 10
        assert merged["lint_command"] == "make lint"

    def test_empty_config_values_not_applied(self) -> None:
        """Config values that are None or empty string do not override CLI."""
        from scripts.finalize_docs_gate import _merge_config

        args = self._make_args(lint_command="original")
        cfg = {"lint_command": "", "max_iterations": None}
        merged = _merge_config(args, cfg)
        assert merged["lint_command"] == "original"
        assert merged["max_iterations"] == 5

    def test_default_auto_fix_when_empty(self) -> None:
        """When no auto_fix_commands provided, defaults are filled."""
        from scripts.finalize_docs_gate import _merge_config

        args = self._make_args()
        merged = _merge_config(args, {})
        assert len(merged["auto_fix_commands"]) == 2
        assert "normalize_docs" in merged["auto_fix_commands"][0]

    def test_custom_auto_fix_preserved(self) -> None:
        """When auto_fix_command is provided via CLI, defaults are not added."""
        from scripts.finalize_docs_gate import _merge_config

        args = self._make_args(auto_fix_command=["custom_fix.sh"])
        merged = _merge_config(args, {})
        assert merged["auto_fix_commands"] == ["custom_fix.sh"]

    def test_runtime_config_merge_with_cli(self, tmp_path: Path) -> None:
        """Runtime config values merge correctly with CLI arguments."""
        from scripts.finalize_docs_gate import _merge_config

        args = self._make_args(docs_root="cli_docs", max_iterations=2)
        cfg = {"docs_root": "config_docs", "push_on_commit": True}
        merged = _merge_config(args, cfg)
        assert merged["docs_root"] == "config_docs"
        assert merged["push_on_commit"] is True


# ---------------------------------------------------------------------------
# main() integration tests
# ---------------------------------------------------------------------------


class TestMainIntegration:
    """Tests for the main() 4-phase orchestrator."""

    def _run_main(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        *,
        lint_returns: list[int] | None = None,
        precommit_returns: list[int] | None = None,
        extra_argv: list[str] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        """Helper to invoke main() with controlled subprocess results.

        lint_returns: sequence of exit codes for lint command invocations.
        precommit_returns: sequence of exit codes for precommit invocations.
        extra_argv: additional CLI flags.
        """
        from scripts import finalize_docs_gate as mod

        lint_codes = list(lint_returns or [0])
        precommit_codes = list(precommit_returns or [0])
        lint_idx = {"v": 0}
        precommit_idx = {"v": 0}

        def fake_run(cmd: str, cwd: Path) -> mod.CommandResult:
            if "lint" in cmd and "fix" not in cmd and "llm" not in cmd:
                rc = lint_codes[min(lint_idx["v"], len(lint_codes) - 1)]
                lint_idx["v"] += 1
                return mod.CommandResult(command=cmd, return_code=rc, output="lint output")
            if "pre-commit" in cmd or "husky" in cmd:
                rc = precommit_codes[min(precommit_idx["v"], len(precommit_codes) - 1)]
                precommit_idx["v"] += 1
                return mod.CommandResult(command=cmd, return_code=rc, output="precommit output")
            return mod.CommandResult(command=cmd, return_code=0, output="ok")

        monkeypatch.setattr(mod, "_run", fake_run)
        monkeypatch.setattr(mod, "_safe_git_add", lambda *a, **kw: None)
        monkeypatch.setattr(mod, "get_license", lambda: None)
        monkeypatch.setattr(mod, "_license_check", lambda feat, lic: True)

        report_file = tmp_path / "reports" / "finalize_gate_report.json"
        argv = [
            "finalize_docs_gate.py",
            "--docs-root", str(tmp_path / "docs"),
            "--reports-dir", str(tmp_path / "reports"),
            "--json-report", str(report_file),
        ]
        if extra_argv:
            argv.extend(extra_argv)
        monkeypatch.setattr(sys, "argv", argv)
        monkeypatch.chdir(tmp_path)

        (tmp_path / "docs").mkdir(exist_ok=True)
        (tmp_path / "reports").mkdir(exist_ok=True)

        rc = mod.main()
        report = json.loads(report_file.read_text(encoding="utf-8"))
        return rc, report

    def test_lint_passes_first_try(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Lint passes on the first iteration -> success."""
        rc, report = self._run_main(monkeypatch, tmp_path, lint_returns=[0])
        assert rc == 0
        assert report["ok"] is True

    def test_lint_fails_then_passes(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Lint fails on first attempt, auto-fix runs, lint passes on retry."""
        rc, report = self._run_main(monkeypatch, tmp_path, lint_returns=[1, 0])
        assert rc == 0
        assert report["ok"] is True
        phases = [h["phase"] for h in report["history"]]
        assert "auto_fix" in phases

    def test_max_iterations_exhausted(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """All iterations fail -> overall failure."""
        rc, report = self._run_main(
            monkeypatch, tmp_path,
            lint_returns=[1, 1, 1, 1, 1],
            extra_argv=["--max-iterations", "3"],
        )
        assert rc == 1
        assert report["ok"] is False

    def test_non_interactive_approve(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Non-interactive mode with approve auto-approves."""
        monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
        rc, report = self._run_main(
            monkeypatch, tmp_path,
            lint_returns=[0],
            extra_argv=[
                "--ask-commit-confirmation",
                "--non-interactive-approval", "approve",
                "--commit-on-approve",
            ],
        )
        assert rc == 0
        assert report["ok"] is True
        assert report["approved"] is True

    def test_non_interactive_deny(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Non-interactive mode with deny auto-denies."""
        monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
        rc, report = self._run_main(
            monkeypatch, tmp_path,
            lint_returns=[0],
            extra_argv=[
                "--ask-commit-confirmation",
                "--non-interactive-approval", "deny",
            ],
        )
        assert rc == 0
        assert report["approved"] is False

    def test_non_interactive_fail(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Non-interactive mode with fail mode causes failure."""
        monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
        rc, report = self._run_main(
            monkeypatch, tmp_path,
            lint_returns=[0],
            extra_argv=[
                "--ask-commit-confirmation",
                "--non-interactive-approval", "fail",
            ],
        )
        assert rc == 1
        assert report["ok"] is False

    def test_precommit_disabled(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """When run-precommit-before-commit is not set, precommit phase is skipped."""
        monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
        rc, report = self._run_main(
            monkeypatch, tmp_path,
            lint_returns=[0],
            extra_argv=[
                "--ask-commit-confirmation",
                "--non-interactive-approval", "approve",
            ],
        )
        assert rc == 0
        assert report["precommit_ok"] is None

    def test_precommit_loop_with_recovery(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Pre-commit fails then passes after auto-fix retry."""
        monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
        rc, report = self._run_main(
            monkeypatch, tmp_path,
            lint_returns=[0],
            precommit_returns=[1, 0],
            extra_argv=[
                "--ask-commit-confirmation",
                "--non-interactive-approval", "approve",
                "--run-precommit-before-commit",
                "--commit-on-approve",
            ],
        )
        assert rc == 0
        assert report["precommit_ok"] is True
        phases = [h["phase"] for h in report["history"]]
        assert "precommit" in phases
        assert "precommit_auto_fix" in phases

    def test_commit_and_push_success(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Commit and push succeed after approval."""
        monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
        rc, report = self._run_main(
            monkeypatch, tmp_path,
            lint_returns=[0],
            extra_argv=[
                "--ask-commit-confirmation",
                "--non-interactive-approval", "approve",
                "--commit-on-approve",
                "--push-on-commit",
            ],
        )
        assert rc == 0
        assert report["commit_done"] is True
        assert report["push_done"] is True

    def test_continue_on_error_returns_zero(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """When continue_on_error is set, exit code is 0 even on failure."""
        rc, report = self._run_main(
            monkeypatch, tmp_path,
            lint_returns=[1, 1, 1],
            extra_argv=["--max-iterations", "2", "--continue-on-error"],
        )
        assert rc == 0
        assert report["ok"] is False

    def test_llm_fix_command_runs_on_failure(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """LLM fix command runs when lint fails and llm-fix-command is specified."""
        rc, report = self._run_main(
            monkeypatch, tmp_path,
            lint_returns=[1, 0],
            extra_argv=["--llm-fix-command", "python3 llm_fix.py"],
        )
        assert rc == 0
        phases = [h["phase"] for h in report["history"]]
        assert "llm_fix" in phases

    def test_report_file_created(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """JSON report file is created with expected structure."""
        rc, report = self._run_main(monkeypatch, tmp_path, lint_returns=[0])
        assert "ok" in report
        assert "approved" in report
        assert "precommit_ok" in report
        assert "commit_done" in report
        assert "push_done" in report
        assert "history" in report
        assert isinstance(report["history"], list)

    def test_precommit_all_iterations_fail(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """When all pre-commit iterations fail, overall result is failure."""
        monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
        rc, report = self._run_main(
            monkeypatch, tmp_path,
            lint_returns=[0],
            precommit_returns=[1, 1, 1],
            extra_argv=[
                "--ask-commit-confirmation",
                "--non-interactive-approval", "approve",
                "--run-precommit-before-commit",
                "--precommit-max-iterations", "2",
            ],
        )
        assert rc == 1
        assert report["ok"] is False
        assert report["precommit_ok"] is False


# ===========================================================================
# vector_store.py tests
# ===========================================================================


class TestLoadIndex:
    """Tests for load_index: FAISS index + metadata loading."""

    def test_valid_load(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Loads FAISS index and metadata list successfully."""
        import scripts.vector_store as mod

        fake_index = MagicMock()
        fake_faiss = MagicMock()
        fake_faiss.read_index = MagicMock(return_value=fake_index)
        monkeypatch.setattr(mod, "faiss", fake_faiss)

        meta_path = tmp_path / "meta.json"
        meta_path.write_text('[{"id": "mod-1", "title": "Test"}]', encoding="utf-8")

        idx, meta = mod.load_index(str(tmp_path / "index.faiss"), meta_path)
        assert idx is fake_index
        assert meta == [{"id": "mod-1", "title": "Test"}]
        fake_faiss.read_index.assert_called_once()

    def test_faiss_not_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Raises ImportError when faiss is not available."""
        import scripts.vector_store as mod

        monkeypatch.setattr(mod, "faiss", None)
        with pytest.raises(ImportError, match="faiss-cpu"):
            mod.load_index("a.faiss", "b.json")

    def test_metadata_not_list_raises(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Raises ValueError when metadata JSON is not a list."""
        import scripts.vector_store as mod

        fake_faiss = MagicMock()
        fake_faiss.read_index = MagicMock(return_value=MagicMock())
        monkeypatch.setattr(mod, "faiss", fake_faiss)

        meta_path = tmp_path / "meta.json"
        meta_path.write_text('{"not": "a list"}', encoding="utf-8")

        with pytest.raises(ValueError, match="JSON list"):
            mod.load_index(str(tmp_path / "x.faiss"), meta_path)

    def test_accepts_path_objects(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Accepts both str and Path objects for file paths."""
        import scripts.vector_store as mod

        fake_faiss = MagicMock()
        fake_faiss.read_index = MagicMock(return_value=MagicMock())
        monkeypatch.setattr(mod, "faiss", fake_faiss)

        meta_path = tmp_path / "meta.json"
        meta_path.write_text("[]", encoding="utf-8")

        idx, meta = mod.load_index(tmp_path / "index.faiss", meta_path)
        assert meta == []


class TestSearch:
    """Tests for search: FAISS similarity search."""

    def _make_index(self, ntotal: int = 0) -> MagicMock:
        """Create a mock FAISS index with ntotal control."""
        idx = MagicMock()
        idx.ntotal = ntotal
        return idx

    def test_empty_index_returns_empty(self) -> None:
        """Empty index (ntotal=0) returns empty results."""
        from scripts.vector_store import search

        idx = self._make_index(ntotal=0)
        results = search(idx, [], np.zeros(4, dtype=np.float32))
        assert results == []

    def test_returns_matching_metadata(self) -> None:
        """Search returns metadata entries with scores."""
        from scripts.vector_store import search

        idx = self._make_index(ntotal=3)
        idx.search = MagicMock(return_value=(
            np.array([[0.9, 0.7, 0.5]], dtype=np.float32),
            np.array([[0, 2, 1]], dtype=np.int64),
        ))
        meta = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        results = search(idx, meta, np.ones(4, dtype=np.float32), top_k=3)
        assert len(results) == 3
        assert results[0][0] == {"id": "a"}
        assert results[0][1] == pytest.approx(0.9)
        assert results[1][0] == {"id": "c"}

    def test_top_k_exceeds_index_size(self) -> None:
        """top_k larger than index size limits to available entries."""
        from scripts.vector_store import search

        idx = self._make_index(ntotal=2)
        idx.search = MagicMock(return_value=(
            np.array([[0.8, 0.6]], dtype=np.float32),
            np.array([[0, 1]], dtype=np.int64),
        ))
        meta = [{"id": "x"}, {"id": "y"}]
        results = search(idx, meta, np.ones(4, dtype=np.float32), top_k=100)
        assert len(results) == 2
        idx.search.assert_called_once_with(pytest.approx(np.ones((1, 4), dtype=np.float32)), 2)

    def test_out_of_bounds_indices_skipped(self) -> None:
        """Negative or out-of-bounds indices from FAISS are skipped."""
        from scripts.vector_store import search

        idx = self._make_index(ntotal=3)
        idx.search = MagicMock(return_value=(
            np.array([[0.9, 0.7, 0.5]], dtype=np.float32),
            np.array([[0, -1, 99]], dtype=np.int64),
        ))
        meta = [{"id": "only_one"}]
        results = search(idx, meta, np.ones(4, dtype=np.float32), top_k=3)
        assert len(results) == 1
        assert results[0][0] == {"id": "only_one"}

    def test_1d_query_reshaped(self) -> None:
        """1D query vector is reshaped to 2D for FAISS."""
        from scripts.vector_store import search

        idx = self._make_index(ntotal=1)
        idx.search = MagicMock(return_value=(
            np.array([[0.5]], dtype=np.float32),
            np.array([[0]], dtype=np.int64),
        ))
        meta = [{"id": "m"}]
        search(idx, meta, np.array([1.0, 2.0], dtype=np.float32), top_k=1)
        call_args = idx.search.call_args[0]
        assert call_args[0].ndim == 2

    def test_2d_query_accepted(self) -> None:
        """2D query vector is accepted without reshaping issues."""
        from scripts.vector_store import search

        idx = self._make_index(ntotal=1)
        idx.search = MagicMock(return_value=(
            np.array([[0.5]], dtype=np.float32),
            np.array([[0]], dtype=np.int64),
        ))
        meta = [{"id": "m"}]
        q = np.array([[1.0, 2.0]], dtype=np.float32)
        results = search(idx, meta, q, top_k=1)
        assert len(results) == 1


class TestLoadReranker:
    """Tests for load_reranker: singleton pattern with cache."""

    def test_singleton_returns_same_instance(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Same model name returns the same cached instance."""
        import scripts.vector_store as mod

        mock_ce = MagicMock(return_value=MagicMock())
        monkeypatch.setattr(mod, "_HAS_CROSS_ENCODER", True)
        monkeypatch.setattr(mod, "_CrossEncoder", mock_ce)
        monkeypatch.setattr(mod, "_RERANKER_INSTANCE", None)
        monkeypatch.setattr(mod, "_RERANKER_MODEL_NAME", "")

        first = mod.load_reranker("model-a")
        # Simulate singleton state: set globals as load_reranker would
        monkeypatch.setattr(mod, "_RERANKER_INSTANCE", first)
        monkeypatch.setattr(mod, "_RERANKER_MODEL_NAME", "model-a")
        second = mod.load_reranker("model-a")
        assert first is second
        assert mock_ce.call_count == 1

    def test_different_model_creates_new_instance(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Different model name creates a new reranker instance."""
        import scripts.vector_store as mod

        instances = [MagicMock(name="inst-a"), MagicMock(name="inst-b")]
        call_count = {"v": 0}

        def fake_ce(name: str) -> MagicMock:
            inst = instances[call_count["v"]]
            call_count["v"] += 1
            return inst

        monkeypatch.setattr(mod, "_HAS_CROSS_ENCODER", True)
        monkeypatch.setattr(mod, "_CrossEncoder", fake_ce)
        monkeypatch.setattr(mod, "_RERANKER_INSTANCE", None)
        monkeypatch.setattr(mod, "_RERANKER_MODEL_NAME", "")

        first = mod.load_reranker("model-a")
        monkeypatch.setattr(mod, "_RERANKER_INSTANCE", first)
        monkeypatch.setattr(mod, "_RERANKER_MODEL_NAME", "model-a")

        second = mod.load_reranker("model-b")
        assert first is not second

    def test_missing_sentence_transformers_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Raises ImportError when sentence_transformers is not installed."""
        import scripts.vector_store as mod

        monkeypatch.setattr(mod, "_HAS_CROSS_ENCODER", False)
        monkeypatch.setattr(mod, "_RERANKER_INSTANCE", None)
        monkeypatch.setattr(mod, "_RERANKER_MODEL_NAME", "")

        with pytest.raises(ImportError, match="sentence-transformers"):
            mod.load_reranker()


class TestRerank:
    """Tests for rerank: cross-encoder scoring and ranking."""

    def test_empty_candidates_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Empty candidate list returns empty list without calling reranker."""
        import scripts.vector_store as mod

        result = mod.rerank("query", [])
        assert result == []

    def test_sorts_by_score_descending(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Candidates are sorted by cross-encoder score in descending order."""
        import scripts.vector_store as mod

        mock_reranker = MagicMock()
        mock_reranker.predict = MagicMock(return_value=np.array([0.1, 0.9, 0.5]))
        monkeypatch.setattr(mod, "load_reranker", lambda model_name: mock_reranker)

        candidates = [
            {"id": "low", "title": "Low"},
            {"id": "high", "title": "High"},
            {"id": "mid", "title": "Mid"},
        ]
        result = mod.rerank("test query", candidates, top_n=3)
        assert result[0]["id"] == "high"
        assert result[1]["id"] == "mid"
        assert result[2]["id"] == "low"

    def test_top_n_limits_output(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """top_n limits the number of returned candidates."""
        import scripts.vector_store as mod

        mock_reranker = MagicMock()
        mock_reranker.predict = MagicMock(return_value=np.array([0.9, 0.5, 0.1]))
        monkeypatch.setattr(mod, "load_reranker", lambda model_name: mock_reranker)

        candidates = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        result = mod.rerank("q", candidates, top_n=1)
        assert len(result) == 1

    def test_pairs_include_title_summary_excerpt(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Pairs passed to reranker include title, summary, and assistant_excerpt."""
        import scripts.vector_store as mod

        mock_reranker = MagicMock()
        mock_reranker.predict = MagicMock(return_value=np.array([0.5]))
        monkeypatch.setattr(mod, "load_reranker", lambda model_name: mock_reranker)

        candidates = [
            {"title": "T", "summary": "S", "assistant_excerpt": "E"},
        ]
        mod.rerank("q", candidates, top_n=1)
        pairs = mock_reranker.predict.call_args[0][0]
        assert len(pairs) == 1
        assert pairs[0][0] == "q"
        assert "T" in pairs[0][1]
        assert "S" in pairs[0][1]
        assert "E" in pairs[0][1]

    def test_missing_fields_handled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Candidates without title/summary/excerpt do not crash."""
        import scripts.vector_store as mod

        mock_reranker = MagicMock()
        mock_reranker.predict = MagicMock(return_value=np.array([0.5]))
        monkeypatch.setattr(mod, "load_reranker", lambda model_name: mock_reranker)

        result = mod.rerank("q", [{"id": "sparse"}], top_n=1)
        assert len(result) == 1


class TestEmbedQuery:
    """Tests for embed_query: HTTP POST to OpenAI API with L2 normalization."""

    def _mock_httpx_post(
        self,
        monkeypatch: pytest.MonkeyPatch,
        embedding: list[float],
    ) -> MagicMock:
        """Set up mock for httpx.post returning given embedding."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"embedding": embedding}],
        }
        mock_response.raise_for_status = MagicMock()

        mock_post = MagicMock(return_value=mock_response)
        # Patch httpx at the module level inside vector_store
        import scripts.vector_store as mod
        monkeypatch.setattr("scripts.vector_store.httpx.post", mock_post, raising=False)
        return mock_post

    def test_makes_correct_http_request(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Sends POST with correct headers, URL, and payload."""
        import httpx
        import scripts.vector_store as mod

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": [{"embedding": [1.0, 0.0, 0.0]}]}
        mock_response.raise_for_status = MagicMock()
        mock_post = MagicMock(return_value=mock_response)
        monkeypatch.setattr(httpx, "post", mock_post)

        mod.embed_query("test text", "sk-test-key", model="text-embedding-3-small")

        call_kwargs = mock_post.call_args
        assert "/embeddings" in call_kwargs[0][0] or "/embeddings" in str(call_kwargs)
        headers = call_kwargs[1]["headers"] if "headers" in call_kwargs[1] else call_kwargs[0][1]
        assert "Bearer sk-test-key" in str(headers)

    def test_normalizes_vector_l2(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Output vector is L2-normalized to unit length."""
        import httpx
        import scripts.vector_store as mod

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": [{"embedding": [3.0, 4.0]}]}
        mock_response.raise_for_status = MagicMock()
        monkeypatch.setattr(httpx, "post", MagicMock(return_value=mock_response))

        vec = mod.embed_query("text", "key")
        norm = float(np.linalg.norm(vec))
        assert norm == pytest.approx(1.0, abs=1e-6)
        assert vec[0] == pytest.approx(0.6, abs=1e-6)
        assert vec[1] == pytest.approx(0.8, abs=1e-6)

    def test_zero_vector_not_normalized(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Zero vector is returned as-is (no division by zero)."""
        import httpx
        import scripts.vector_store as mod

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": [{"embedding": [0.0, 0.0, 0.0]}]}
        mock_response.raise_for_status = MagicMock()
        monkeypatch.setattr(httpx, "post", MagicMock(return_value=mock_response))

        vec = mod.embed_query("text", "key")
        assert float(np.linalg.norm(vec)) == 0.0

    def test_strips_trailing_slash_from_base_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Trailing slash in base_url does not cause double slash."""
        import httpx
        import scripts.vector_store as mod

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": [{"embedding": [1.0]}]}
        mock_response.raise_for_status = MagicMock()
        mock_post = MagicMock(return_value=mock_response)
        monkeypatch.setattr(httpx, "post", mock_post)

        mod.embed_query("text", "key", base_url="https://api.example.com/v1/")
        url_arg = mock_post.call_args[0][0]
        assert "//" not in url_arg.replace("https://", "")
        assert url_arg.endswith("/embeddings")

    def test_custom_model_passed_in_payload(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Custom model name is included in the request payload."""
        import httpx
        import scripts.vector_store as mod

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": [{"embedding": [1.0]}]}
        mock_response.raise_for_status = MagicMock()
        mock_post = MagicMock(return_value=mock_response)
        monkeypatch.setattr(httpx, "post", mock_post)

        mod.embed_query("text", "key", model="text-embedding-ada-002")
        payload = mock_post.call_args[1]["json"]
        assert payload["model"] == "text-embedding-ada-002"

    def test_returns_float32_array(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Returned array has dtype float32."""
        import httpx
        import scripts.vector_store as mod

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": [{"embedding": [0.5, 0.5]}]}
        mock_response.raise_for_status = MagicMock()
        monkeypatch.setattr(httpx, "post", MagicMock(return_value=mock_response))

        vec = mod.embed_query("text", "key")
        assert vec.dtype == np.float32

    def test_input_text_passed_in_payload(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Input text is included in the request payload."""
        import httpx
        import scripts.vector_store as mod

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": [{"embedding": [1.0]}]}
        mock_response.raise_for_status = MagicMock()
        mock_post = MagicMock(return_value=mock_response)
        monkeypatch.setattr(httpx, "post", mock_post)

        mod.embed_query("hello world", "key")
        payload = mock_post.call_args[1]["json"]
        assert payload["input"] == "hello world"

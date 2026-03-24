"""Coverage boost round 3 -- target scripts at 0% and low coverage.

Covers:
  - scripts/build_acme_demo_site.py (0%)
  - scripts/check_updates.py (0%)
  - scripts/chunker.py (0%)
  - scripts/create_doc_and_run_pipeline.py (0%)
  - scripts/check_protocol_regression.py (32%)
  - scripts/ensure_external_mock_server.py (42%)
  - scripts/provision_client_repo.py (55%)
  - scripts/assemble_intent_experience.py (58%)
  - scripts/generate_public_docs_audit.py (63%)
  - scripts/run_retrieval_evals.py (65%)
"""

from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path
from typing import Any
from unittest import mock

import pytest
import yaml


# ---------------------------------------------------------------------------
# build_acme_demo_site
# ---------------------------------------------------------------------------

class TestBuildAcmeDemoSiteFlattenNav:
    """Tests for _flatten_nav_paths in build_acme_demo_site."""

    def test_flatten_simple_strings(self) -> None:
        """Flatten a nav list of plain strings."""
        from scripts.build_acme_demo_site import _flatten_nav_paths

        nav: list[Any] = ["index.md", "about.md"]
        result = _flatten_nav_paths(nav)
        assert result == {"index.md", "about.md"}

    def test_flatten_nested_dicts(self) -> None:
        """Flatten nested nav with dict entries."""
        from scripts.build_acme_demo_site import _flatten_nav_paths

        nav: list[Any] = [{"Home": "index.md"}, {"Guides": ["guides/tutorial.md"]}]
        result = _flatten_nav_paths(nav)
        assert "index.md" in result
        assert "guides/tutorial.md" in result

    def test_flatten_empty_nav(self) -> None:
        """Empty nav yields empty set."""
        from scripts.build_acme_demo_site import _flatten_nav_paths

        assert _flatten_nav_paths([]) == set()

    def test_flatten_deeply_nested(self) -> None:
        """Deeply nested dict/list structure is traversed."""
        from scripts.build_acme_demo_site import _flatten_nav_paths

        nav: list[Any] = [{"A": [{"B": [{"C": "deep.md"}]}]}]
        result = _flatten_nav_paths(nav)
        assert "deep.md" in result


class TestBuildAcmeParseFrontmatter:
    """Tests for _parse_frontmatter in build_acme_demo_site."""

    def test_valid_frontmatter(self) -> None:
        """Parse valid YAML frontmatter."""
        from scripts.build_acme_demo_site import _parse_frontmatter

        text = "---\ntitle: Test\n---\nBody"
        result = _parse_frontmatter(text, "test.md")
        assert result["title"] == "Test"

    def test_missing_frontmatter(self) -> None:
        """Raise ValueError when frontmatter opener is absent."""
        from scripts.build_acme_demo_site import _parse_frontmatter

        with pytest.raises(ValueError, match="Missing YAML frontmatter"):
            _parse_frontmatter("No frontmatter here", "test.md")

    def test_unterminated_frontmatter(self) -> None:
        """Raise ValueError when frontmatter is not closed."""
        from scripts.build_acme_demo_site import _parse_frontmatter

        with pytest.raises(ValueError, match="Unterminated"):
            _parse_frontmatter("---\ntitle: X\nbody text", "test.md")

    def test_invalid_mapping_frontmatter(self) -> None:
        """Raise ValueError when frontmatter is not a dict."""
        from scripts.build_acme_demo_site import _parse_frontmatter

        with pytest.raises(ValueError, match="Invalid frontmatter mapping"):
            _parse_frontmatter("---\n- item1\n- item2\n---\nbody", "test.md")


class TestBuildAcmeReadBody:
    """Tests for _read_body_without_frontmatter."""

    def test_strips_frontmatter(self) -> None:
        """Body returned without frontmatter section."""
        from scripts.build_acme_demo_site import _read_body_without_frontmatter

        text = "---\ntitle: T\n---\nActual body"
        assert _read_body_without_frontmatter(text) == "Actual body"

    def test_no_frontmatter(self) -> None:
        """Full text returned when no frontmatter."""
        from scripts.build_acme_demo_site import _read_body_without_frontmatter

        text = "Just plain content"
        assert _read_body_without_frontmatter(text) == text

    def test_unterminated_returns_text(self) -> None:
        """Unterminated frontmatter returns full text."""
        from scripts.build_acme_demo_site import _read_body_without_frontmatter

        text = "---\ntitle: T\nno closing"
        assert _read_body_without_frontmatter(text) == text


class TestBuildAcmeSlug:
    """Tests for _slug helper."""

    def test_slug_basic(self) -> None:
        """Alphanumeric slug generation."""
        from scripts.build_acme_demo_site import _slug

        assert _slug("Hello World 123") == "hello-world-123"

    def test_slug_special_chars(self) -> None:
        """Special characters become hyphens."""
        from scripts.build_acme_demo_site import _slug

        assert _slug("foo/bar.baz") == "foo-bar-baz"

    def test_slug_empty_string(self) -> None:
        """Empty input returns 'doc'."""
        from scripts.build_acme_demo_site import _slug

        assert _slug("") == "doc"


class TestBuildAcmeFirstParagraph:
    """Tests for _first_paragraph helper."""

    def test_extracts_first_paragraph(self) -> None:
        """First non-heading paragraph is extracted."""
        from scripts.build_acme_demo_site import _first_paragraph

        md = "---\ntitle: T\n---\n# Heading\n\nThis is the first paragraph.\n\nSecond."
        result = _first_paragraph(md)
        assert "first paragraph" in result

    def test_empty_body(self) -> None:
        """Empty content returns empty string."""
        from scripts.build_acme_demo_site import _first_paragraph

        assert _first_paragraph("") == ""

    def test_heading_only(self) -> None:
        """Document with only headings returns empty."""
        from scripts.build_acme_demo_site import _first_paragraph

        assert _first_paragraph("# Title\n\n## Sub") == ""


class TestBuildAcmeRefreshScore:
    """Tests for _refresh_score_in_page."""

    def test_updates_quality_score_line(self, tmp_path: Path) -> None:
        """Quality score row is replaced in-place."""
        from scripts.build_acme_demo_site import _refresh_score_in_page

        page = tmp_path / "index.md"
        page.write_text("| Quality score | **0%** | 80% | Bad |\n| Other | x |\n", encoding="utf-8")
        _refresh_score_in_page(page, 95, 10, 0, 0)
        text = page.read_text(encoding="utf-8")
        assert "**95%**" in text
        assert "Excellent" in text

    def test_updates_all_kpi_rows(self, tmp_path: Path) -> None:
        """All KPI rows (quality, total, stale, gaps) are updated."""
        from scripts.build_acme_demo_site import _refresh_score_in_page

        page = tmp_path / "index.md"
        lines = [
            "| Quality score | **0%** | 80% | Bad |",
            "| Total documents | **0** | -- | None |",
            "| Stale pages | **5** | 0 | Bad |",
            "| Documentation gaps | **3** | 0 | Gaps |",
        ]
        page.write_text("\n".join(lines) + "\n", encoding="utf-8")
        _refresh_score_in_page(page, 87, 20, 2, 1)
        text = page.read_text(encoding="utf-8")
        assert "**87%**" in text
        assert "**20**" in text
        assert "**2**" in text
        assert "**1**" in text
        assert "Good" in text

    def test_nonexistent_path_noop(self, tmp_path: Path) -> None:
        """No error when path does not exist."""
        from scripts.build_acme_demo_site import _refresh_score_in_page

        _refresh_score_in_page(tmp_path / "missing.md", 90, 1, 0, 0)


class TestBuildAcmeEnsureOpenapi:
    """Tests for _ensure_openapi."""

    def test_creates_openapi_file(self, tmp_path: Path) -> None:
        """OpenAPI YAML is written to expected location."""
        from scripts.build_acme_demo_site import _ensure_openapi

        _ensure_openapi(tmp_path)
        oa = tmp_path / "docs" / "assets" / "api" / "openapi.yaml"
        assert oa.exists()
        data = yaml.safe_load(oa.read_text(encoding="utf-8"))
        assert data["openapi"] == "3.0.3"


class TestBuildAcmeEnsureSwaggerHtml:
    """Tests for _ensure_swagger_html."""

    def test_creates_swagger_html(self, tmp_path: Path) -> None:
        """Swagger HTML file created when absent."""
        from scripts.build_acme_demo_site import _ensure_swagger_html

        _ensure_swagger_html(tmp_path)
        html = tmp_path / "docs" / "reference" / "swagger-test.html"
        assert html.exists()
        assert "SwaggerUIBundle" in html.read_text(encoding="utf-8")

    def test_repairs_existing_swagger_html(self, tmp_path: Path) -> None:
        """Existing HTML with wrong spec path gets repaired."""
        from scripts.build_acme_demo_site import _ensure_swagger_html

        html = tmp_path / "docs" / "reference" / "swagger-test.html"
        html.parent.mkdir(parents=True, exist_ok=True)
        html.write_text("url: 'openapi.bundled.json'", encoding="utf-8")
        _ensure_swagger_html(tmp_path)
        assert "openapi.yaml" in html.read_text(encoding="utf-8")


class TestBuildAcmeValidateScope:
    """Tests for _validate_scope."""

    def test_forbidden_token_detected(self, tmp_path: Path) -> None:
        """Files containing forbidden tokens raise ValueError."""
        from scripts.build_acme_demo_site import _validate_scope

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "page.md").write_text("This mentions taskstream badly.", encoding="utf-8")
        with pytest.raises(ValueError, match="forbidden token"):
            _validate_scope(tmp_path)

    def test_clean_docs_pass(self, tmp_path: Path) -> None:
        """Clean docs directory passes validation."""
        from scripts.build_acme_demo_site import _validate_scope

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "page.md").write_text("Clean content here.", encoding="utf-8")
        _validate_scope(tmp_path)

    def test_review_manifest_excluded(self, tmp_path: Path) -> None:
        """review-manifest.md is excluded from scope check."""
        from scripts.build_acme_demo_site import _validate_scope

        quality = tmp_path / "docs" / "quality"
        quality.mkdir(parents=True)
        (quality / "review-manifest.md").write_text("taskstream mention ok", encoding="utf-8")
        _validate_scope(tmp_path)


class TestBuildAcmeValidateNoSecrets:
    """Tests for _validate_no_secrets."""

    def test_secret_detected(self, tmp_path: Path) -> None:
        """Postman API key pattern triggers secret guard."""
        from scripts.build_acme_demo_site import _validate_no_secrets

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "page.md").write_text("key: PMAK-abcdefghijklmnopqrstu12345", encoding="utf-8")
        with pytest.raises(ValueError, match="Secret-leak"):
            _validate_no_secrets(tmp_path)

    def test_openai_key_detected(self, tmp_path: Path) -> None:
        """OpenAI-style key pattern triggers secret guard."""
        from scripts.build_acme_demo_site import _validate_no_secrets

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "page.md").write_text("key: sk-abcdefghijklmnopqrstuvwx", encoding="utf-8")
        with pytest.raises(ValueError, match="Secret-leak"):
            _validate_no_secrets(tmp_path)

    def test_clean_passes(self, tmp_path: Path) -> None:
        """No secrets in docs passes validation."""
        from scripts.build_acme_demo_site import _validate_no_secrets

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "page.md").write_text("Safe content.", encoding="utf-8")
        _validate_no_secrets(tmp_path)


class TestBuildAcmeGenerateEmbeddings:
    """Tests for _generate_embeddings_if_available."""

    def test_skips_when_no_api_key(self, tmp_path: Path) -> None:
        """Embedding generation skipped without OPENAI_API_KEY."""
        from scripts.build_acme_demo_site import _generate_embeddings_if_available

        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            _generate_embeddings_if_available(tmp_path)


# ---------------------------------------------------------------------------
# check_updates
# ---------------------------------------------------------------------------

class TestCheckUpdatesCurrentVersion:
    """Tests for _current_version in check_updates."""

    def test_no_version_file(self, tmp_path: Path) -> None:
        """Returns default when version file is missing."""
        from scripts.check_updates import _current_version, VERSION_FILE

        with mock.patch("scripts.check_updates.VERSION_FILE", tmp_path / "missing.json"):
            result = _current_version()
        assert result["version"] == "0.0.0"

    def test_valid_version_file(self, tmp_path: Path) -> None:
        """Reads version from existing file."""
        from scripts.check_updates import _current_version

        vf = tmp_path / ".version.json"
        vf.write_text(json.dumps({"version": "1.2.3", "platform": "linux-x86_64"}), encoding="utf-8")
        with mock.patch("scripts.check_updates.VERSION_FILE", vf):
            result = _current_version()
        assert result["version"] == "1.2.3"

    def test_corrupt_version_file(self, tmp_path: Path) -> None:
        """Returns default on corrupt JSON."""
        from scripts.check_updates import _current_version

        vf = tmp_path / ".version.json"
        vf.write_text("{invalid json", encoding="utf-8")
        with mock.patch("scripts.check_updates.VERSION_FILE", vf):
            result = _current_version()
        assert result["version"] == "0.0.0"


class TestCheckUpdatesDetectPlatform:
    """Tests for _detect_platform."""

    def test_linux_x86(self) -> None:
        """Linux x86_64 detected correctly."""
        from scripts.check_updates import _detect_platform

        with mock.patch("platform.system", return_value="Linux"), \
             mock.patch("platform.machine", return_value="x86_64"):
            assert _detect_platform() == "linux-x86_64"

    def test_macos_arm(self) -> None:
        """macOS ARM detected correctly."""
        from scripts.check_updates import _detect_platform

        with mock.patch("platform.system", return_value="Darwin"), \
             mock.patch("platform.machine", return_value="arm64"):
            assert _detect_platform() == "macos-arm64"

    def test_macos_intel(self) -> None:
        """macOS Intel detected correctly."""
        from scripts.check_updates import _detect_platform

        with mock.patch("platform.system", return_value="Darwin"), \
             mock.patch("platform.machine", return_value="x86_64"):
            assert _detect_platform() == "macos-x86_64"

    def test_windows(self) -> None:
        """Windows detected correctly."""
        from scripts.check_updates import _detect_platform

        with mock.patch("platform.system", return_value="Windows"), \
             mock.patch("platform.machine", return_value="AMD64"):
            assert _detect_platform() == "windows-x64"

    def test_unknown_platform(self) -> None:
        """Unknown platform returns system-machine."""
        from scripts.check_updates import _detect_platform

        with mock.patch("platform.system", return_value="FreeBSD"), \
             mock.patch("platform.machine", return_value="amd64"):
            assert _detect_platform() == "freebsd-amd64"


class TestCheckUpdatesCheckForUpdate:
    """Tests for _check_for_update."""

    def test_no_update_available(self) -> None:
        """Returns None when update_available is false."""
        from scripts.check_updates import _check_for_update

        response_data = json.dumps({"update_available": False}).encode()
        mock_resp = mock.MagicMock()
        mock_resp.read.return_value = response_data
        mock_resp.__enter__ = mock.MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = mock.MagicMock(return_value=False)

        with mock.patch("urllib.request.urlopen", return_value=mock_resp):
            result = _check_for_update({"version": "1.0.0", "platform": "linux-x86_64"})
        assert result is None

    def test_update_available(self) -> None:
        """Returns update info when update_available is true."""
        from scripts.check_updates import _check_for_update

        response_data = json.dumps({"update_available": True, "version": "2.0.0"}).encode()
        mock_resp = mock.MagicMock()
        mock_resp.read.return_value = response_data
        mock_resp.__enter__ = mock.MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = mock.MagicMock(return_value=False)

        with mock.patch("urllib.request.urlopen", return_value=mock_resp):
            result = _check_for_update({"version": "1.0.0", "platform": "linux-x86_64"})
        assert result is not None
        assert result["version"] == "2.0.0"

    def test_network_failure_returns_none(self) -> None:
        """Returns None on network failure."""
        from scripts.check_updates import _check_for_update

        with mock.patch("urllib.request.urlopen", side_effect=OSError("no network")):
            result = _check_for_update({"version": "1.0.0"})
        assert result is None


class TestCheckUpdatesVerifyBundle:
    """Tests for _verify_bundle_signature."""

    def test_import_error_returns_false(self, tmp_path: Path) -> None:
        """Returns False when license_gate import fails."""
        from scripts.check_updates import _verify_bundle_signature

        bundle = tmp_path / "bundle.tar.gz"
        bundle.write_bytes(b"test data")
        with mock.patch.dict("sys.modules", {"scripts.license_gate": None}):
            result = _verify_bundle_signature(bundle, "AAAA")
        assert result is False


class TestCheckUpdatesBackup:
    """Tests for _backup_current."""

    def test_creates_backup_directory(self, tmp_path: Path) -> None:
        """Backup directory created with version name."""
        from scripts.check_updates import _backup_current

        with mock.patch("scripts.check_updates.BACKUP_DIR", tmp_path / "rollback"), \
             mock.patch("scripts.check_updates.VERSION_FILE", tmp_path / "missing.json"), \
             mock.patch("scripts.check_updates.REPO_ROOT", tmp_path):
            scripts_dir = tmp_path / "scripts"
            scripts_dir.mkdir()
            result = _backup_current("1.0.0")
        assert result.exists()
        assert result.name == "v1.0.0"


class TestCheckUpdatesApply:
    """Tests for _apply_update."""

    def test_no_download_url(self) -> None:
        """Returns False when download_url is empty."""
        from scripts.check_updates import _apply_update

        assert _apply_update({"download_url": "", "version": "2.0"}) is False

    def test_download_failure(self) -> None:
        """Returns False on download failure."""
        from scripts.check_updates import _apply_update

        with mock.patch("urllib.request.urlopen", side_effect=OSError("fail")):
            result = _apply_update({"download_url": "https://example.com/bundle.tar.gz", "version": "2.0"})
        assert result is False


class TestCheckUpdatesMain:
    """Tests for main entry point."""

    def test_up_to_date(self) -> None:
        """Returns 0 when no update available."""
        from scripts.check_updates import main

        with mock.patch("scripts.check_updates._current_version", return_value={"version": "1.0.0"}), \
             mock.patch("scripts.check_updates._check_for_update", return_value=None), \
             mock.patch("sys.argv", ["check_updates.py"]):
            assert main() == 0


# ---------------------------------------------------------------------------
# chunker
# ---------------------------------------------------------------------------

class TestChunkerBuildText:
    """Tests for _build_text in chunker."""

    def test_builds_text_from_module(self) -> None:
        """Concatenates title, summary, excerpt, and intents."""
        from scripts.chunker import _build_text

        module = {
            "title": "Install guide",
            "summary": "How to install.",
            "assistant_excerpt": "Run pip install.",
            "intents": ["install", "configure"],
        }
        result = _build_text(module)
        assert "Install guide" in result
        assert "install configure" in result

    def test_empty_module(self) -> None:
        """Empty module yields empty string."""
        from scripts.chunker import _build_text

        assert _build_text({}).strip() == ""


class TestChunkerChunkModule:
    """Tests for chunk_module."""

    def test_single_chunk_when_small(self) -> None:
        """Small module produces single chunk."""
        from scripts.chunker import chunk_module

        module = {"id": "test-mod", "title": "Short", "summary": "Brief."}
        chunks = chunk_module(module, max_tokens=750, overlap_tokens=100)
        assert len(chunks) == 1
        assert chunks[0]["parent_id"] == "test-mod"
        assert chunks[0]["chunk_index"] == 0

    def test_multiple_chunks_when_large(self) -> None:
        """Large module is split into multiple chunks."""
        from scripts.chunker import chunk_module

        long_text = " ".join(["word"] * 2000)
        module = {"id": "big-mod", "title": "Large module", "summary": long_text}
        chunks = chunk_module(module, max_tokens=50, overlap_tokens=10)
        assert len(chunks) > 1
        for i, chunk in enumerate(chunks):
            assert chunk["chunk_id"] == f"big-mod__chunk_{i}"
            assert chunk["parent_id"] == "big-mod"

    def test_no_tiktoken_raises(self) -> None:
        """ImportError raised when tiktoken not available."""
        from scripts.chunker import _get_encoder

        with mock.patch("scripts.chunker._HAS_TIKTOKEN", False):
            with pytest.raises(ImportError, match="tiktoken"):
                _get_encoder()


# ---------------------------------------------------------------------------
# create_doc_and_run_pipeline
# ---------------------------------------------------------------------------

class TestCreateDocAndRunPipeline:
    """Tests for create_doc_and_run_pipeline."""

    def test_default_runtime_exists(self, tmp_path: Path) -> None:
        """Returns candidate path when file exists."""
        from scripts.create_doc_and_run_pipeline import _default_runtime

        candidate = tmp_path / "docsops" / "config" / "client_runtime.yml"
        candidate.parent.mkdir(parents=True)
        candidate.write_text("key: val", encoding="utf-8")
        with mock.patch("scripts.create_doc_and_run_pipeline.REPO_ROOT", tmp_path):
            result = _default_runtime()
        assert result == candidate

    def test_default_runtime_missing(self, tmp_path: Path) -> None:
        """Returns None when runtime config absent."""
        from scripts.create_doc_and_run_pipeline import _default_runtime

        with mock.patch("scripts.create_doc_and_run_pipeline.REPO_ROOT", tmp_path):
            result = _default_runtime()
        assert result is None

    def test_main_new_doc_fails(self) -> None:
        """Returns non-zero when new_doc creation fails."""
        from scripts.create_doc_and_run_pipeline import main

        mock_result = mock.MagicMock()
        mock_result.returncode = 1
        with mock.patch("subprocess.run", return_value=mock_result), \
             mock.patch("sys.argv", ["prog", "tutorial", "My Title"]):
            result = main()
        assert result == 1

    def test_main_no_runtime_config(self, tmp_path: Path) -> None:
        """Returns 2 when no runtime config available."""
        from scripts.create_doc_and_run_pipeline import main

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        with mock.patch("subprocess.run", return_value=mock_result), \
             mock.patch("scripts.create_doc_and_run_pipeline.REPO_ROOT", tmp_path), \
             mock.patch("sys.argv", ["prog", "tutorial", "My Title"]):
            result = main()
        assert result == 2

    def test_main_full_success(self, tmp_path: Path) -> None:
        """Returns 0 when both doc creation and pipeline succeed."""
        from scripts.create_doc_and_run_pipeline import main

        runtime = tmp_path / "docsops" / "config" / "client_runtime.yml"
        runtime.parent.mkdir(parents=True)
        runtime.write_text("key: val", encoding="utf-8")

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        with mock.patch("subprocess.run", return_value=mock_result), \
             mock.patch("scripts.create_doc_and_run_pipeline.REPO_ROOT", tmp_path), \
             mock.patch("sys.argv", ["prog", "how-to", "Test Doc"]):
            result = main()
        assert result == 0

    def test_main_veridoc_mode(self, tmp_path: Path) -> None:
        """Veridoc mode appends --skip-local-llm-packet."""
        from scripts.create_doc_and_run_pipeline import main

        runtime = tmp_path / "docsops" / "config" / "client_runtime.yml"
        runtime.parent.mkdir(parents=True)
        runtime.write_text("key: val", encoding="utf-8")

        calls: list[Any] = []
        mock_result = mock.MagicMock()
        mock_result.returncode = 0

        def capture_run(cmd: list[str], **kwargs: Any) -> Any:
            calls.append(cmd)
            return mock_result

        with mock.patch("subprocess.run", side_effect=capture_run), \
             mock.patch("scripts.create_doc_and_run_pipeline.REPO_ROOT", tmp_path), \
             mock.patch("sys.argv", ["prog", "concept", "Title", "--mode", "veridoc"]):
            main()

        pipeline_cmd = calls[-1]
        assert "--skip-local-llm-packet" in pipeline_cmd
        assert "--mode" in pipeline_cmd


# ---------------------------------------------------------------------------
# check_protocol_regression
# ---------------------------------------------------------------------------

class TestProtocolRegressionSnapshot:
    """Tests for collect_snapshot and compare_snapshots."""

    def test_collect_snapshot_single_file(self, tmp_path: Path) -> None:
        """Snapshot from a single YAML file."""
        from scripts.check_protocol_regression import collect_snapshot

        f = tmp_path / "spec.yaml"
        f.write_text("openapi: 3.0.3\n", encoding="utf-8")
        snap = collect_snapshot("rest", [f])
        assert snap["protocol"] == "rest"
        assert len(snap["files"]) == 1

    def test_collect_snapshot_directory(self, tmp_path: Path) -> None:
        """Snapshot from a directory of files."""
        from scripts.check_protocol_regression import collect_snapshot

        d = tmp_path / "proto"
        d.mkdir()
        (d / "a.proto").write_text("syntax = 'proto3';", encoding="utf-8")
        (d / "b.json").write_text('{"k": 1}', encoding="utf-8")
        snap = collect_snapshot("grpc", [d])
        assert len(snap["files"]) == 2

    def test_compare_no_changes(self, tmp_path: Path) -> None:
        """Identical snapshots yield no differences."""
        from scripts.check_protocol_regression import collect_snapshot, compare_snapshots

        f = tmp_path / "spec.graphql"
        f.write_text("type Query { hello: String }", encoding="utf-8")
        snap = collect_snapshot("graphql", [f])
        diff = compare_snapshots(snap, snap)
        assert diff == {"added": [], "removed": [], "changed": []}

    def test_compare_added_file(self, tmp_path: Path) -> None:
        """New file shows up as added."""
        from scripts.check_protocol_regression import compare_snapshots

        current = {"files": {"a.yaml": "abc", "b.yaml": "def"}}
        baseline = {"files": {"a.yaml": "abc"}}
        diff = compare_snapshots(current, baseline)
        assert "b.yaml" in diff["added"]
        assert diff["removed"] == []

    def test_compare_removed_file(self) -> None:
        """Missing file shows up as removed."""
        from scripts.check_protocol_regression import compare_snapshots

        current = {"files": {"a.yaml": "abc"}}
        baseline = {"files": {"a.yaml": "abc", "b.yaml": "def"}}
        diff = compare_snapshots(current, baseline)
        assert "b.yaml" in diff["removed"]

    def test_compare_changed_file(self) -> None:
        """Changed hash shows up as changed."""
        from scripts.check_protocol_regression import compare_snapshots

        current = {"files": {"a.yaml": "new_hash"}}
        baseline = {"files": {"a.yaml": "old_hash"}}
        diff = compare_snapshots(current, baseline)
        assert "a.yaml" in diff["changed"]

    def test_compare_invalid_format(self) -> None:
        """Invalid snapshot format raises ValueError."""
        from scripts.check_protocol_regression import compare_snapshots

        with pytest.raises(ValueError, match="files must be mapping"):
            compare_snapshots({"files": "not a dict"}, {"files": {}})


class TestProtocolRegressionNormalized:
    """Tests for _normalized_bytes."""

    def test_yaml_normalization(self, tmp_path: Path) -> None:
        """YAML files are normalized via JSON serialization."""
        from scripts.check_protocol_regression import _normalized_bytes

        f = tmp_path / "spec.yml"
        f.write_text("b: 2\na: 1\n", encoding="utf-8")
        result = _normalized_bytes(f)
        parsed = json.loads(result)
        assert parsed == {"a": 1, "b": 2}

    def test_json_normalization(self, tmp_path: Path) -> None:
        """JSON files are normalized with sorted keys."""
        from scripts.check_protocol_regression import _normalized_bytes

        f = tmp_path / "data.json"
        f.write_text('{"z": 1, "a": 2}', encoding="utf-8")
        result = _normalized_bytes(f)
        assert b'"a":2' in result

    def test_text_passthrough(self, tmp_path: Path) -> None:
        """Non-YAML/JSON files pass through as-is."""
        from scripts.check_protocol_regression import _normalized_bytes

        f = tmp_path / "schema.graphql"
        f.write_text("type Query { x: Int }", encoding="utf-8")
        result = _normalized_bytes(f)
        assert result == b"type Query { x: Int }"


class TestProtocolRegressionMain:
    """Tests for main entry point."""

    def test_main_update_mode(self, tmp_path: Path) -> None:
        """--update writes snapshot file."""
        from scripts.check_protocol_regression import main

        spec = tmp_path / "spec.yaml"
        spec.write_text("openapi: 3.0.3", encoding="utf-8")
        snap = tmp_path / "snap.json"
        with mock.patch("sys.argv", [
            "prog", "--protocol", "rest", "--snapshot", str(snap),
            "--input", str(spec), "--update",
        ]):
            rc = main()
        assert rc == 0
        assert snap.exists()

    def test_main_missing_input(self, tmp_path: Path) -> None:
        """Returns 2 when input paths do not exist."""
        from scripts.check_protocol_regression import main

        with mock.patch("sys.argv", [
            "prog", "--protocol", "rest", "--snapshot", str(tmp_path / "s.json"),
            "--input", str(tmp_path / "nonexistent.yaml"),
        ]):
            rc = main()
        assert rc == 2

    def test_main_no_regression(self, tmp_path: Path) -> None:
        """Returns 0 when no changes detected."""
        from scripts.check_protocol_regression import main, collect_snapshot

        spec = tmp_path / "spec.yaml"
        spec.write_text("openapi: 3.0.3", encoding="utf-8")
        snap_path = tmp_path / "snap.json"
        snap = collect_snapshot("rest", [spec])
        snap_path.write_text(json.dumps(snap), encoding="utf-8")

        with mock.patch("sys.argv", [
            "prog", "--protocol", "rest", "--snapshot", str(snap_path),
            "--input", str(spec),
        ]):
            rc = main()
        assert rc == 0


# ---------------------------------------------------------------------------
# ensure_external_mock_server
# ---------------------------------------------------------------------------

class TestEnsureMockReadEnv:
    """Tests for _read_env."""

    def test_required_missing_raises(self) -> None:
        """Raises RuntimeError when required env var is empty."""
        from scripts.ensure_external_mock_server import _read_env

        with mock.patch.dict(os.environ, {}, clear=False):
            with pytest.raises(RuntimeError, match="Missing required"):
                _read_env("NONEXISTENT_VAR_12345", required=True)

    def test_optional_missing_returns_empty(self) -> None:
        """Returns empty string when optional var is missing."""
        from scripts.ensure_external_mock_server import _read_env

        with mock.patch.dict(os.environ, {}, clear=False):
            assert _read_env("NONEXISTENT_VAR_12345", required=False) == ""


class TestEnsureMockFindMockHelpers:
    """Tests for _find_mock_node, _find_mock_url, _find_mock_id."""

    def test_find_mock_node_flat(self) -> None:
        """Find mock node in flat dict."""
        from scripts.ensure_external_mock_server import _find_mock_node

        result = _find_mock_node({"id": "abc", "url": "https://mock.example.com"})
        assert result is not None
        assert result["id"] == "abc"

    def test_find_mock_node_nested(self) -> None:
        """Find mock node in nested structure."""
        from scripts.ensure_external_mock_server import _find_mock_node

        payload = {"data": {"mock": {"id": "x", "url": "https://m.com"}}}
        result = _find_mock_node(payload)
        assert result is not None

    def test_find_mock_node_in_list(self) -> None:
        """Find mock node inside a list."""
        from scripts.ensure_external_mock_server import _find_mock_node

        payload = [{"other": 1}, {"id": "y", "url": "https://z.com"}]
        result = _find_mock_node(payload)
        assert result is not None

    def test_find_mock_node_none(self) -> None:
        """Returns None when no mock node found."""
        from scripts.ensure_external_mock_server import _find_mock_node

        assert _find_mock_node({"data": "string"}) is None

    def test_find_mock_url(self) -> None:
        """Extracts mockUrl or url from nested payload."""
        from scripts.ensure_external_mock_server import _find_mock_url

        assert _find_mock_url({"mockUrl": "https://m.com"}) == "https://m.com"
        assert _find_mock_url({"url": "https://u.com"}) == "https://u.com"
        assert _find_mock_url({"data": "none"}) == ""

    def test_find_mock_id(self) -> None:
        """Extracts id from nested payload."""
        from scripts.ensure_external_mock_server import _find_mock_id

        assert _find_mock_id({"id": "abc123"}) == "abc123"
        assert _find_mock_id({"nested": {"id": "deep"}}) == "deep"
        assert _find_mock_id({"no_id": True}) == ""


class TestEnsureMockExtractCollectionId:
    """Tests for _extract_collection_id."""

    def test_extracts_from_info(self) -> None:
        """Extracts collection id from info._postman_id."""
        from scripts.ensure_external_mock_server import _extract_collection_id

        payload = {"collection": {"info": {"_postman_id": "col-123"}}}
        assert _extract_collection_id(payload) == "col-123"

    def test_extracts_from_top_level(self) -> None:
        """Falls back to top-level id."""
        from scripts.ensure_external_mock_server import _extract_collection_id

        assert _extract_collection_id({"id": "top-id"}) == "top-id"

    def test_empty_payload(self) -> None:
        """Returns empty for payload without ids."""
        from scripts.ensure_external_mock_server import _extract_collection_id

        assert _extract_collection_id({}) == ""


class TestEnsureMockNormalizePath:
    """Tests for _normalize_base_path."""

    def test_normalize_with_slashes(self) -> None:
        """Normalizes path with leading/trailing slashes."""
        from scripts.ensure_external_mock_server import _normalize_base_path

        assert _normalize_base_path("/v1/") == "/v1"
        assert _normalize_base_path("v1") == "/v1"
        assert _normalize_base_path("") == ""


class TestEnsureMockExtractMocksList:
    """Tests for _extract_mocks_list."""

    def test_mocks_key(self) -> None:
        """Extracts from 'mocks' key."""
        from scripts.ensure_external_mock_server import _extract_mocks_list

        result = _extract_mocks_list({"mocks": [{"id": "1"}]})
        assert len(result) == 1

    def test_mock_singular_key(self) -> None:
        """Extracts from 'mock' singular key."""
        from scripts.ensure_external_mock_server import _extract_mocks_list

        result = _extract_mocks_list({"mock": {"id": "1"}})
        assert len(result) == 1

    def test_empty_payload(self) -> None:
        """Returns empty list for empty payload."""
        from scripts.ensure_external_mock_server import _extract_mocks_list

        result = _extract_mocks_list({})
        assert result == []


class TestEnsureMockExtractExamples:
    """Tests for _extract_examples_from_spec."""

    def test_extracts_response_examples(self, tmp_path: Path) -> None:
        """Extracts examples from OpenAPI responses."""
        from scripts.ensure_external_mock_server import _extract_examples_from_spec

        spec = {
            "paths": {
                "/users": {
                    "get": {
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "example": {"users": []}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        f = tmp_path / "openapi.yaml"
        f.write_text(yaml.safe_dump(spec), encoding="utf-8")
        result = _extract_examples_from_spec(str(f))
        assert ("GET", "/users") in result

    def test_nonexistent_spec(self) -> None:
        """Returns empty dict for nonexistent spec."""
        from scripts.ensure_external_mock_server import _extract_examples_from_spec

        assert _extract_examples_from_spec("/nonexistent/spec.yaml") == {}


class TestEnsureMockGetItemMethodPath:
    """Tests for _get_item_method_path."""

    def test_extracts_method_and_path(self) -> None:
        """Extracts HTTP method and path from Postman item."""
        from scripts.ensure_external_mock_server import _get_item_method_path

        item = {
            "request": {
                "method": "POST",
                "url": {"path": ["v1", "users"]},
            }
        }
        method, path = _get_item_method_path(item)
        assert method == "POST"
        assert "/users" in path

    def test_url_string(self) -> None:
        """Handles url as string."""
        from scripts.ensure_external_mock_server import _get_item_method_path

        item = {"request": {"method": "GET", "url": "https://api.example.com/v1/projects"}}
        method, path = _get_item_method_path(item)
        assert method == "GET"
        assert "/projects" in path

    def test_empty_request(self) -> None:
        """Returns empty strings for empty request."""
        from scripts.ensure_external_mock_server import _get_item_method_path

        assert _get_item_method_path({"request": "invalid"}) == ("", "")


# ---------------------------------------------------------------------------
# provision_client_repo
# ---------------------------------------------------------------------------

class TestProvisionSlugify:
    """Tests for _slugify_client_id."""

    def test_basic_slugify(self) -> None:
        """Company name slugified correctly."""
        from scripts.provision_client_repo import _slugify_client_id

        assert _slugify_client_id("ACME Corp.") == "acme-corp"

    def test_multiple_hyphens_collapsed(self) -> None:
        """Multiple consecutive hyphens reduced to one."""
        from scripts.provision_client_repo import _slugify_client_id

        assert _slugify_client_id("a--b---c") == "a-b-c"


class TestProvisionDeepMerge:
    """Tests for _deep_merge."""

    def test_simple_merge(self) -> None:
        """Non-overlapping keys merged."""
        from scripts.provision_client_repo import _deep_merge

        result = _deep_merge({"a": 1}, {"b": 2})
        assert result == {"a": 1, "b": 2}

    def test_nested_merge(self) -> None:
        """Nested dicts merged recursively."""
        from scripts.provision_client_repo import _deep_merge

        base = {"x": {"a": 1, "b": 2}}
        override = {"x": {"b": 3, "c": 4}}
        result = _deep_merge(base, override)
        assert result["x"] == {"a": 1, "b": 3, "c": 4}

    def test_override_non_dict(self) -> None:
        """Non-dict values overridden."""
        from scripts.provision_client_repo import _deep_merge

        result = _deep_merge({"a": 1}, {"a": 2})
        assert result["a"] == 2


class TestProvisionDotenv:
    """Tests for _read_dotenv and _write_dotenv."""

    def test_read_dotenv(self, tmp_path: Path) -> None:
        """Reads key=value pairs from dotenv file."""
        from scripts.provision_client_repo import _read_dotenv

        f = tmp_path / ".env"
        f.write_text("# comment\nKEY1=value1\nKEY2=value2\n\n", encoding="utf-8")
        result = _read_dotenv(f)
        assert result == {"KEY1": "value1", "KEY2": "value2"}

    def test_read_dotenv_missing(self, tmp_path: Path) -> None:
        """Returns empty dict for missing file."""
        from scripts.provision_client_repo import _read_dotenv

        assert _read_dotenv(tmp_path / "missing") == {}

    def test_write_dotenv(self, tmp_path: Path) -> None:
        """Writes sorted dotenv file."""
        from scripts.provision_client_repo import _write_dotenv

        f = tmp_path / ".env"
        _write_dotenv(f, {"B": "2", "A": "1"})
        text = f.read_text(encoding="utf-8")
        assert "A=1" in text
        assert text.index("A=1") < text.index("B=2")


class TestProvisionGitignore:
    """Tests for _ensure_gitignore_has_env."""

    def test_adds_entry(self, tmp_path: Path) -> None:
        """Adds env file to .gitignore."""
        from scripts.provision_client_repo import _ensure_gitignore_has_env

        _ensure_gitignore_has_env(tmp_path, ".env.docsops.local")
        gi = (tmp_path / ".gitignore").read_text(encoding="utf-8")
        assert ".env.docsops.local" in gi

    def test_no_duplicate(self, tmp_path: Path) -> None:
        """Does not add duplicate entry."""
        from scripts.provision_client_repo import _ensure_gitignore_has_env

        gi = tmp_path / ".gitignore"
        gi.write_text(".env.docsops.local\n", encoding="utf-8")
        _ensure_gitignore_has_env(tmp_path, ".env.docsops.local")
        assert gi.read_text(encoding="utf-8").count(".env.docsops.local") == 1


class TestProvisionCopyBundle:
    """Tests for copy_bundle_to_repo."""

    def test_copies_bundle(self, tmp_path: Path) -> None:
        """Bundle directory copied to target."""
        from scripts.provision_client_repo import copy_bundle_to_repo

        bundle = tmp_path / "bundle"
        bundle.mkdir()
        (bundle / "config").mkdir()
        (bundle / "config" / "runtime.yml").write_text("key: val", encoding="utf-8")
        repo = tmp_path / "client-repo"
        repo.mkdir()
        result = copy_bundle_to_repo(bundle, repo, "docsops")
        assert (result / "config" / "runtime.yml").exists()


class TestProvisionScheduler:
    """Tests for run_scheduler_install."""

    def test_none_mode_noop(self, tmp_path: Path) -> None:
        """Mode 'none' does nothing."""
        from scripts.provision_client_repo import run_scheduler_install

        run_scheduler_install(tmp_path, "docsops", "none")

    def test_unsupported_mode(self, tmp_path: Path) -> None:
        """Unsupported mode raises ValueError."""
        from scripts.provision_client_repo import run_scheduler_install

        with pytest.raises(ValueError, match="Unsupported"):
            run_scheduler_install(tmp_path, "docsops", "macos")

    def test_linux_mode(self, tmp_path: Path) -> None:
        """Linux mode calls bash with install script."""
        from scripts.provision_client_repo import run_scheduler_install

        with mock.patch("subprocess.run") as mock_run:
            run_scheduler_install(tmp_path, "docsops", "linux")
        mock_run.assert_called_once()
        assert "bash" in mock_run.call_args[0][0][0]


class TestProvisionResolveArgs:
    """Tests for _resolve_args."""

    def test_non_interactive_missing_args(self) -> None:
        """Raises when args missing and stdin not a tty."""
        from scripts.provision_client_repo import _resolve_args
        import argparse

        args = argparse.Namespace(
            interactive=False, client="", client_repo="",
            docsops_dir="docsops", install_scheduler="none",
        )
        with mock.patch("sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = False
            with pytest.raises(ValueError, match="Missing required"):
                _resolve_args(args)


# ---------------------------------------------------------------------------
# assemble_intent_experience
# ---------------------------------------------------------------------------

class TestAssembleIntentSlugify:
    """Tests for _slugify in assemble_intent_experience."""

    def test_basic_slugify(self) -> None:
        """Converts to lowercase with hyphens."""
        from scripts.assemble_intent_experience import _slugify

        assert _slugify("Install Guide") == "install-guide"

    def test_empty_string(self) -> None:
        """Empty string returns empty."""
        from scripts.assemble_intent_experience import _slugify

        assert _slugify("") == ""


class TestAssembleIntentMatchModule:
    """Tests for _match_module."""

    def test_matches_correctly(self) -> None:
        """Module matches when all criteria met."""
        from scripts.assemble_intent_experience import _match_module

        module = {
            "status": "active",
            "intents": ["install"],
            "audiences": ["beginner"],
            "channels": ["docs"],
        }
        assert _match_module(module, "install", "beginner", "docs") is True

    def test_audience_all_matches(self) -> None:
        """Module with 'all' audience matches any audience."""
        from scripts.assemble_intent_experience import _match_module

        module = {
            "status": "active",
            "intents": ["install"],
            "audiences": ["all"],
            "channels": ["docs"],
        }
        assert _match_module(module, "install", "architect", "docs") is True

    def test_wrong_intent_no_match(self) -> None:
        """Module does not match on wrong intent."""
        from scripts.assemble_intent_experience import _match_module

        module = {
            "status": "active",
            "intents": ["configure"],
            "audiences": ["beginner"],
            "channels": ["docs"],
        }
        assert _match_module(module, "install", "beginner", "docs") is False

    def test_deprecated_no_match(self) -> None:
        """Deprecated modules do not match."""
        from scripts.assemble_intent_experience import _match_module

        module = {
            "status": "deprecated",
            "intents": ["install"],
            "audiences": ["beginner"],
            "channels": ["docs"],
        }
        assert _match_module(module, "install", "beginner", "docs") is False


class TestAssembleIntentSortModules:
    """Tests for _sort_modules (topological sort)."""

    def test_sort_no_dependencies(self) -> None:
        """Modules without dependencies sorted alphabetically."""
        from scripts.assemble_intent_experience import _sort_modules

        modules = [
            {"id": "b-mod", "intents": ["install"]},
            {"id": "a-mod", "intents": ["install"]},
        ]
        result = _sort_modules(modules)
        assert [m["id"] for m in result] == ["a-mod", "b-mod"]

    def test_sort_with_dependencies(self) -> None:
        """Dependencies come before dependents."""
        from scripts.assemble_intent_experience import _sort_modules

        modules = [
            {"id": "child", "dependencies": ["parent"]},
            {"id": "parent"},
        ]
        result = _sort_modules(modules)
        ids = [m["id"] for m in result]
        assert ids.index("parent") < ids.index("child")

    def test_cycle_detection(self) -> None:
        """Circular dependencies raise ValueError."""
        from scripts.assemble_intent_experience import _sort_modules

        modules = [
            {"id": "a", "dependencies": ["b"]},
            {"id": "b", "dependencies": ["a"]},
        ]
        with pytest.raises(ValueError, match="cycle"):
            _sort_modules(modules)


class TestAssembleIntentBuildDocsPage:
    """Tests for _build_docs_page."""

    def test_generates_markdown(self) -> None:
        """Produces valid markdown with frontmatter."""
        from scripts.assemble_intent_experience import _build_docs_page

        modules = [
            {"id": "mod-1", "title": "Module One", "summary": "A summary.", "content": {"docs_markdown": "Content here."}},
        ]
        result = _build_docs_page("install", "beginner", modules)
        assert "---" in result
        assert "Module One" in result
        assert "Content here." in result


class TestAssembleIntentBuildChannelBundle:
    """Tests for _build_channel_bundle."""

    def test_docs_channel(self) -> None:
        """Builds docs channel bundle."""
        from scripts.assemble_intent_experience import _build_channel_bundle

        modules = [
            {"id": "m1", "title": "M1", "priority": 10, "content": {"docs_markdown": "Doc text."}},
        ]
        result = _build_channel_bundle("install", "beginner", "docs", modules)
        assert result["module_count"] == 1
        assert result["modules"][0]["content"] == "Doc text."

    def test_assistant_channel(self) -> None:
        """Builds assistant channel bundle."""
        from scripts.assemble_intent_experience import _build_channel_bundle

        modules = [
            {"id": "m1", "title": "M1", "priority": 5, "content": {"assistant_context": "AI text."}},
        ]
        result = _build_channel_bundle("configure", "developer", "assistant", modules)
        assert result["channel"] == "assistant"
        assert result["module_count"] == 1

    def test_empty_content_skipped(self) -> None:
        """Modules with empty channel content are skipped."""
        from scripts.assemble_intent_experience import _build_channel_bundle

        modules = [
            {"id": "m1", "title": "M1", "priority": 5, "content": {"docs_markdown": ""}},
        ]
        result = _build_channel_bundle("install", "beginner", "docs", modules)
        assert result["module_count"] == 0


# ---------------------------------------------------------------------------
# generate_public_docs_audit
# ---------------------------------------------------------------------------

class TestPublicDocsAuditHelpers:
    """Tests for helper functions in generate_public_docs_audit."""

    def test_slugify(self) -> None:
        """Slugify converts to lowercase hyphenated."""
        from scripts.generate_public_docs_audit import _slugify

        assert _slugify("Hello World!") == "hello-world"

    def test_slugify_empty(self) -> None:
        """Empty input returns 'client'."""
        from scripts.generate_public_docs_audit import _slugify

        assert _slugify("") == "client"

    def test_normalize_url(self) -> None:
        """URL normalized: trailing slash removed, fragment stripped."""
        from scripts.generate_public_docs_audit import _normalize_url

        assert _normalize_url("https://example.com/page/#section") == "https://example.com/page"

    def test_is_http_url(self) -> None:
        """Detects HTTP/HTTPS URLs."""
        from scripts.generate_public_docs_audit import _is_http_url

        assert _is_http_url("https://example.com") is True
        assert _is_http_url("ftp://example.com") is False
        assert _is_http_url("not a url") is False

    def test_same_host(self) -> None:
        """Same host comparison."""
        from scripts.generate_public_docs_audit import _same_host

        assert _same_host("https://docs.example.com/a", "https://docs.example.com/b") is True
        assert _same_host("https://a.com", "https://b.com") is False

    def test_safe_pct(self) -> None:
        """Percentage calculation with zero denominator handling."""
        from scripts.generate_public_docs_audit import _safe_pct

        assert _safe_pct(1, 4) == 25.0
        assert _safe_pct(1, 0) == 0.0

    def test_sanitize_url_basic(self) -> None:
        """Sanitize handles clean URLs."""
        from scripts.generate_public_docs_audit import _sanitize_url

        result = _sanitize_url("https://example.com/path")
        assert "example.com" in result


class TestPublicDocsAuditHeadingViolations:
    """Tests for _heading_violations."""

    def test_no_violations(self) -> None:
        """Sequential headings have no violations."""
        from scripts.generate_public_docs_audit import _heading_violations

        assert _heading_violations([1, 2, 3, 2, 3]) == 0

    def test_skip_level(self) -> None:
        """Skipped heading level counts as violation."""
        from scripts.generate_public_docs_audit import _heading_violations

        assert _heading_violations([1, 3]) == 1

    def test_empty(self) -> None:
        """Empty list has no violations."""
        from scripts.generate_public_docs_audit import _heading_violations

        assert _heading_violations([]) == 0


class TestPublicDocsAuditExampleReliability:
    """Tests for _estimate_example_reliability."""

    def test_no_pages(self) -> None:
        """No pages yields zero metrics."""
        from scripts.generate_public_docs_audit import _estimate_example_reliability

        result = _estimate_example_reliability([])
        assert result["total_code_examples"] == 0

    def test_with_code_blocks(self) -> None:
        """Code blocks detected and classified."""
        from scripts.generate_public_docs_audit import _estimate_example_reliability, PageData

        page = PageData(
            url="https://example.com",
            status=200,
            title="Test",
            meta_description="Desc",
            h1_count=1,
            heading_levels=[1],
            internal_links=[],
            external_links=[],
            code_blocks=[
                {"language": "python", "code": "print('hello')"},
                {"language": "yaml", "code": "key: val"},
            ],
            text="Some text",
            last_updated_hint="",
        )
        result = _estimate_example_reliability([page])
        assert result["total_code_examples"] == 1
        assert result["runnable_without_env"] == 1


class TestPublicDocsAuditApiPage:
    """Tests for _is_api_page."""

    def test_api_url(self) -> None:
        """Pages with API-related URL patterns detected."""
        from scripts.generate_public_docs_audit import _is_api_page, PageData

        page = PageData(
            url="https://docs.example.com/reference/api/users",
            status=200, title="", meta_description="", h1_count=0,
            heading_levels=[], internal_links=[], external_links=[],
            code_blocks=[], text="", last_updated_hint="",
        )
        assert _is_api_page(page) is True

    def test_non_api_url(self) -> None:
        """Regular pages not detected as API."""
        from scripts.generate_public_docs_audit import _is_api_page, PageData

        page = PageData(
            url="https://docs.example.com/getting-started",
            status=200, title="", meta_description="", h1_count=0,
            heading_levels=[], internal_links=[], external_links=[],
            code_blocks=[], text="Welcome to the guide.", last_updated_hint="",
        )
        assert _is_api_page(page) is False


class TestPublicDocsAuditSeoGeo:
    """Tests for _seo_geo_metrics."""

    def test_calculates_metrics(self) -> None:
        """SEO/GEO metrics computed from page data."""
        from scripts.generate_public_docs_audit import _seo_geo_metrics, PageData

        pages = [
            PageData(url="https://example.com/a", status=200, title="Title",
                     meta_description="A description", h1_count=1,
                     heading_levels=[1, 2], internal_links=[], external_links=[],
                     code_blocks=[], text="Text", last_updated_hint=""),
            PageData(url="https://example.com/b", status=200, title="",
                     meta_description="", h1_count=2,
                     heading_levels=[1, 1, 3], internal_links=[], external_links=[],
                     code_blocks=[], text="Text", last_updated_hint=""),
        ]
        result = _seo_geo_metrics(pages)
        assert result["pages_scanned"] == 2
        assert result["missing_title_count"] == 1
        assert result["missing_description_count"] == 1
        assert result["multiple_h1_count"] == 1


class TestPublicDocsAuditLinkHealth:
    """Tests for _link_health."""

    def test_broken_links_detected(self) -> None:
        """Broken internal links identified."""
        from scripts.generate_public_docs_audit import _link_health, PageData

        pages = [
            PageData(url="https://example.com", status=200, title="T",
                     meta_description="D", h1_count=1, heading_levels=[1],
                     internal_links=["https://example.com/broken"],
                     external_links=[], code_blocks=[], text="", last_updated_hint=""),
        ]
        status_map = {"https://example.com/broken": 404}
        result = _link_health(pages, status_map)
        assert result["broken_internal_links_count"] == 1


class TestPublicDocsAuditIsRepoLink:
    """Tests for _is_repo_link."""

    def test_github_blob_link(self) -> None:
        """GitHub blob link is a repo link."""
        from scripts.generate_public_docs_audit import _is_repo_link

        assert _is_repo_link("https://github.com/org/repo/blob/main/README.md") is True

    def test_regular_link(self) -> None:
        """Non-repo link returns False."""
        from scripts.generate_public_docs_audit import _is_repo_link

        assert _is_repo_link("https://docs.example.com/guide") is False


# ---------------------------------------------------------------------------
# run_retrieval_evals
# ---------------------------------------------------------------------------

class TestRetrievalEvalsTokenize:
    """Tests for _tokenize."""

    def test_tokenizes_text(self) -> None:
        """Extracts lowercase tokens from text."""
        from scripts.run_retrieval_evals import _tokenize

        tokens = _tokenize("Hello World 123")
        assert "hello" in tokens
        assert "world" in tokens
        assert "123" in tokens

    def test_empty_string(self) -> None:
        """Empty string yields empty set."""
        from scripts.run_retrieval_evals import _tokenize

        assert _tokenize("") == set()


class TestRetrievalEvalsLoadIndex:
    """Tests for _load_index."""

    def test_valid_index(self, tmp_path: Path) -> None:
        """Loads valid JSON list index."""
        from scripts.run_retrieval_evals import _load_index

        f = tmp_path / "index.json"
        f.write_text(json.dumps([{"id": "m1"}, {"id": "m2"}]), encoding="utf-8")
        rows = _load_index(f)
        assert len(rows) == 2

    def test_invalid_format(self, tmp_path: Path) -> None:
        """Raises ValueError for non-list JSON."""
        from scripts.run_retrieval_evals import _load_index

        f = tmp_path / "index.json"
        f.write_text('{"not": "a list"}', encoding="utf-8")
        with pytest.raises(ValueError, match="must be a JSON list"):
            _load_index(f)

    def test_filters_empty_ids(self, tmp_path: Path) -> None:
        """Entries without id are filtered out."""
        from scripts.run_retrieval_evals import _load_index

        f = tmp_path / "index.json"
        f.write_text(json.dumps([{"id": "valid"}, {"id": ""}, {"no_id": True}]), encoding="utf-8")
        rows = _load_index(f)
        assert len(rows) == 1


class TestRetrievalEvalsLoadDataset:
    """Tests for _load_dataset."""

    def test_valid_dataset(self, tmp_path: Path) -> None:
        """Loads valid YAML dataset."""
        from scripts.run_retrieval_evals import _load_dataset

        f = tmp_path / "dataset.yml"
        data = [{"query": "how to install", "expected_ids": ["install-guide"]}]
        f.write_text(yaml.safe_dump(data), encoding="utf-8")
        rows = _load_dataset(f)
        assert len(rows) == 1

    def test_invalid_dataset(self, tmp_path: Path) -> None:
        """Raises ValueError for non-list YAML."""
        from scripts.run_retrieval_evals import _load_dataset

        f = tmp_path / "dataset.yml"
        f.write_text("not_a_list: true", encoding="utf-8")
        with pytest.raises(ValueError, match="must be a YAML list"):
            _load_dataset(f)


class TestRetrievalEvalsBuildAutoDataset:
    """Tests for _build_auto_dataset."""

    def test_generates_from_index(self) -> None:
        """Auto-generates eval samples from index rows."""
        from scripts.run_retrieval_evals import _build_auto_dataset

        rows = [
            {"id": "m1", "title": "Install guide", "summary": "How to install."},
            {"id": "m2", "title": "Config ref", "summary": "Configuration options."},
        ]
        dataset = _build_auto_dataset(rows, limit=2)
        assert len(dataset) == 2
        assert dataset[0]["expected_ids"] == ["m1"]


class TestRetrievalEvalsScoreQuery:
    """Tests for _score_query."""

    def test_matching_tokens(self) -> None:
        """Overlapping tokens yield positive score."""
        from scripts.run_retrieval_evals import _score_query

        doc = {"title": "Install guide", "summary": "How to install"}
        score = _score_query("install guide", doc)
        assert score > 0

    def test_no_overlap(self) -> None:
        """No overlapping tokens yield zero score."""
        from scripts.run_retrieval_evals import _score_query

        doc = {"title": "XYZ feature", "summary": "ABC description"}
        score = _score_query("install guide", doc)
        assert score == 0.0


class TestRetrievalEvalsSearchToken:
    """Tests for _search_token."""

    def test_returns_top_k(self) -> None:
        """Returns top-k results sorted by score."""
        from scripts.run_retrieval_evals import _search_token

        rows = [
            {"id": "m1", "title": "Install guide", "summary": "How to install."},
            {"id": "m2", "title": "Unrelated topic", "summary": "Something else."},
        ]
        results = _search_token(rows, "install guide", top_k=1)
        assert len(results) == 1
        assert results[0] == "m1"


class TestRetrievalEvalsEvaluate:
    """Tests for evaluate function."""

    def test_empty_dataset(self) -> None:
        """Empty dataset returns error status."""
        from scripts.run_retrieval_evals import evaluate

        result = evaluate([], [], top_k=3)
        assert result["status"] == "error"

    def test_perfect_recall(self) -> None:
        """Perfect retrieval yields precision=1 and recall=1."""
        from scripts.run_retrieval_evals import evaluate

        index_rows = [{"id": "m1", "title": "Install guide"}]
        dataset = [{"query": "Install guide", "expected_ids": ["m1"]}]
        result = evaluate(index_rows, dataset, top_k=3)
        assert result["recall_at_k"] == 1.0
        assert result["precision_at_k"] > 0


class TestRetrievalEvalsRRF:
    """Tests for _reciprocal_rank_fusion."""

    def test_rrf_merges_rankings(self) -> None:
        """RRF combines two rankings with reciprocal rank scoring."""
        from scripts.run_retrieval_evals import _reciprocal_rank_fusion

        r1 = ["a", "b", "c"]
        r2 = ["b", "a", "d"]
        result = _reciprocal_rank_fusion([r1, r2], k=60)
        assert "a" in result
        assert "b" in result


class TestRetrievalEvalsRunSingleMode:
    """Tests for _run_single_mode."""

    def test_token_mode(self) -> None:
        """Token mode runs without FAISS."""
        from scripts.run_retrieval_evals import _run_single_mode

        index_rows = [{"id": "m1", "title": "Install guide"}]
        dataset = [{"query": "Install guide", "expected_ids": ["m1"]}]
        result = _run_single_mode(
            "token", index_rows, dataset, top_k=3,
            api_key="", embedding_model="", base_url="",
            faiss_assets=None, rrf_k=60, rerank_candidates=20,
            rerank_model="",
        )
        assert result["status"] == "ok"

    def test_semantic_mode_no_key(self) -> None:
        """Semantic mode returns error without API key."""
        from scripts.run_retrieval_evals import _run_single_mode

        result = _run_single_mode(
            "semantic", [], [], top_k=3,
            api_key="", embedding_model="", base_url="",
            faiss_assets=None, rrf_k=60, rerank_candidates=20,
            rerank_model="",
        )
        assert result["status"] == "error"

    def test_hybrid_mode_no_key(self) -> None:
        """Hybrid mode returns error without API key."""
        from scripts.run_retrieval_evals import _run_single_mode

        result = _run_single_mode(
            "hybrid", [], [], top_k=3,
            api_key="", embedding_model="", base_url="",
            faiss_assets=None, rrf_k=60, rerank_candidates=20,
            rerank_model="",
        )
        assert result["status"] == "error"

    def test_hybrid_rerank_no_key(self) -> None:
        """Hybrid+rerank mode returns error without API key."""
        from scripts.run_retrieval_evals import _run_single_mode

        result = _run_single_mode(
            "hybrid+rerank", [], [], top_k=3,
            api_key="", embedding_model="", base_url="",
            faiss_assets=None, rrf_k=60, rerank_candidates=20,
            rerank_model="",
        )
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# generate_public_docs_audit -- additional coverage
# ---------------------------------------------------------------------------

class TestPublicDocsAuditDotenvRead:
    """Tests for _read_dotenv_value_from_file."""

    def test_reads_value(self, tmp_path: Path) -> None:
        """Reads key from .env file."""
        from scripts.generate_public_docs_audit import _read_dotenv_value_from_file

        env = tmp_path / ".env"
        env.write_text("# comment\nMY_KEY=secret123\nOTHER=val\n", encoding="utf-8")
        assert _read_dotenv_value_from_file(env, "MY_KEY") == "secret123"

    def test_missing_key(self, tmp_path: Path) -> None:
        """Returns empty for missing key."""
        from scripts.generate_public_docs_audit import _read_dotenv_value_from_file

        env = tmp_path / ".env"
        env.write_text("OTHER=val\n", encoding="utf-8")
        assert _read_dotenv_value_from_file(env, "MISSING") == ""

    def test_missing_file(self, tmp_path: Path) -> None:
        """Returns empty for missing file."""
        from scripts.generate_public_docs_audit import _read_dotenv_value_from_file

        assert _read_dotenv_value_from_file(tmp_path / "no.env", "KEY") == ""

    def test_strips_quotes(self, tmp_path: Path) -> None:
        """Strips surrounding quotes from value."""
        from scripts.generate_public_docs_audit import _read_dotenv_value_from_file

        env = tmp_path / ".env"
        env.write_text("KEY='quoted_val'\n", encoding="utf-8")
        assert _read_dotenv_value_from_file(env, "KEY") == "quoted_val"


class TestPublicDocsAuditBuildLlmPrompt:
    """Tests for _build_llm_prompt."""

    def test_full_prompt(self) -> None:
        """Full prompt includes audit JSON."""
        from scripts.generate_public_docs_audit import _build_llm_prompt

        payload = {"site_urls": ["https://example.com"], "aggregate": {}}
        result = _build_llm_prompt(payload, summary_only=False)
        assert "auditor" in result
        assert "example.com" in result

    def test_summary_only_prompt(self) -> None:
        """Summary prompt includes only compact keys."""
        from scripts.generate_public_docs_audit import _build_llm_prompt

        payload = {"site_urls": ["https://ex.com"], "topology_mode": "single",
                    "aggregate": {"m": 1}, "top_findings": [], "sites": []}
        result = _build_llm_prompt(payload, summary_only=True)
        assert "ex.com" in result
        assert "sites" not in result.split("Audit JSON")[0]


class TestPublicDocsAuditApiCoverage:
    """Tests for _api_coverage_from_public_docs."""

    def test_no_pages(self) -> None:
        """No pages yields empty coverage."""
        from scripts.generate_public_docs_audit import _api_coverage_from_public_docs

        result = _api_coverage_from_public_docs([])
        assert result["reference_endpoint_count"] == 0

    def test_api_pages_detected(self) -> None:
        """API pages detected and endpoints extracted."""
        from scripts.generate_public_docs_audit import _api_coverage_from_public_docs, PageData

        api_page = PageData(
            url="https://docs.example.com/reference/users",
            status=200, title="Users API", meta_description="", h1_count=1,
            heading_levels=[1], internal_links=[], external_links=[],
            code_blocks=[{"language": "bash", "code": "curl /v1/users"}],
            text="GET /v1/users returns a list", last_updated_hint="",
        )
        result = _api_coverage_from_public_docs([api_page])
        assert result["api_pages_detected"] >= 1


class TestPublicDocsAuditLastUpdated:
    """Tests for _last_updated_metrics."""

    def test_with_hints(self) -> None:
        """Pages with last_updated hints counted."""
        from scripts.generate_public_docs_audit import _last_updated_metrics, PageData

        pages = [
            PageData(url="u1", status=200, title="", meta_description="", h1_count=0,
                     heading_levels=[], internal_links=[], external_links=[],
                     code_blocks=[], text="", last_updated_hint="2024-01-01"),
            PageData(url="u2", status=200, title="", meta_description="", h1_count=0,
                     heading_levels=[], internal_links=[], external_links=[],
                     code_blocks=[], text="", last_updated_hint=""),
        ]
        result = _last_updated_metrics(pages)
        assert result["pages_with_last_updated_hint"] == 1
        assert result["pages_without_last_updated_hint"] == 1


class TestPublicDocsAuditAggregate:
    """Tests for _aggregate_sites and _aggregate_api_coverage."""

    def test_aggregate_api_coverage_all_na(self) -> None:
        """All sites with no API pages returns -1 coverage."""
        from scripts.generate_public_docs_audit import _aggregate_api_coverage

        sites = [
            {"metrics": {"api_coverage": {"no_api_pages_found": True, "reference_endpoint_count": 0}}},
        ]
        result = _aggregate_api_coverage(sites)
        assert result["reference_coverage_pct"] == -1.0

    def test_aggregate_api_coverage_with_data(self) -> None:
        """Sites with API data aggregate correctly."""
        from scripts.generate_public_docs_audit import _aggregate_api_coverage

        sites = [
            {"metrics": {"api_coverage": {
                "no_api_pages_found": False,
                "reference_endpoint_count": 10,
                "endpoints_with_usage_docs": 5,
            }}},
        ]
        result = _aggregate_api_coverage(sites)
        assert result["reference_coverage_pct"] == 50.0

    def test_aggregate_sites(self) -> None:
        """Full site aggregation computes weighted averages."""
        from scripts.generate_public_docs_audit import _aggregate_sites

        sites = [
            {
                "site_url": "https://a.com",
                "metrics": {
                    "crawl": {"pages_crawled": 10, "requested_pages": 15, "max_pages": 50},
                    "links": {"broken_internal_links_count": 2, "docs_broken_links_count": 1, "repo_broken_links_count": 1},
                    "seo_geo": {"seo_geo_issue_rate_pct": 10.0},
                    "api_coverage": {"no_api_pages_found": True, "reference_endpoint_count": 0, "endpoints_with_usage_docs": 0},
                    "examples": {"example_reliability_estimate_pct": 50.0},
                    "freshness": {"last_updated_coverage_pct": 80.0},
                },
            },
        ]
        result = _aggregate_sites(sites)
        assert result["metrics"]["crawl"]["pages_crawled"] == 10


class TestPublicDocsAuditResolveXPlatform:
    """Tests for _resolve_cross_platform_path."""

    def test_existing_path_unchanged(self, tmp_path: Path) -> None:
        """Existing path returned as-is."""
        from scripts.generate_public_docs_audit import _resolve_cross_platform_path

        f = tmp_path / "file.txt"
        f.write_text("hi", encoding="utf-8")
        assert _resolve_cross_platform_path(f) == f

    def test_nonexistent_path_unchanged(self) -> None:
        """Non-existent path returned as-is when no conversion applies."""
        from scripts.generate_public_docs_audit import _resolve_cross_platform_path

        p = Path("/some/random/path/that/does/not/exist")
        assert _resolve_cross_platform_path(p) == p


class TestPublicDocsAuditHtmlParser:
    """Tests for _DocsHTMLParser."""

    def test_parses_title(self) -> None:
        """Extracts title from HTML."""
        from scripts.generate_public_docs_audit import _DocsHTMLParser

        parser = _DocsHTMLParser("https://example.com")
        parser.feed("<html><head><title>My Page</title></head><body></body></html>")
        assert parser.title == "My Page"

    def test_parses_meta_description(self) -> None:
        """Extracts meta description."""
        from scripts.generate_public_docs_audit import _DocsHTMLParser

        parser = _DocsHTMLParser("https://example.com")
        parser.feed('<html><head><meta name="description" content="A test page"></head></html>')
        assert parser.meta_description == "A test page"

    def test_counts_headings(self) -> None:
        """Counts H1 and tracks heading levels."""
        from scripts.generate_public_docs_audit import _DocsHTMLParser

        parser = _DocsHTMLParser("https://example.com")
        parser.feed("<h1>Title</h1><h2>Section</h2><h3>Sub</h3>")
        assert parser.h1_count == 1
        assert parser.heading_levels == [1, 2, 3]

    def test_extracts_links(self) -> None:
        """Separates internal and external links."""
        from scripts.generate_public_docs_audit import _DocsHTMLParser

        parser = _DocsHTMLParser("https://example.com")
        parser.feed(
            '<a href="/page">int</a>'
            '<a href="https://other.com/x">ext</a>'
        )
        assert len(parser.internal_links) == 1
        assert len(parser.external_links) == 1

    def test_extracts_code_blocks(self) -> None:
        """Extracts code from pre/code elements."""
        from scripts.generate_public_docs_audit import _DocsHTMLParser

        parser = _DocsHTMLParser("https://example.com")
        parser.feed('<pre><code class="language-python">print("hello")</code></pre>')
        assert len(parser.code_blocks) == 1
        assert parser.code_blocks[0]["language"] == "python"

    def test_as_page(self) -> None:
        """as_page produces PageData with deduplicated blocks."""
        from scripts.generate_public_docs_audit import _DocsHTMLParser

        parser = _DocsHTMLParser("https://example.com")
        parser.feed("<h1>T</h1><p>Hello world</p>")
        page = parser.as_page("https://example.com", 200)
        assert page.h1_count == 1
        assert page.status == 200

    def test_line_numbers_only_detected(self) -> None:
        """Line number blocks are filtered out."""
        from scripts.generate_public_docs_audit import _DocsHTMLParser

        assert _DocsHTMLParser._is_line_numbers_only("1 2 3 4 5") is True
        assert _DocsHTMLParser._is_line_numbers_only("print('hello')") is False
        assert _DocsHTMLParser._is_line_numbers_only("12345678") is True
        assert _DocsHTMLParser._is_line_numbers_only("") is False

    def test_highlight_div_code(self) -> None:
        """Code inside highlight div wrapper is extracted."""
        from scripts.generate_public_docs_audit import _DocsHTMLParser

        parser = _DocsHTMLParser("https://example.com")
        parser.feed(
            '<div class="highlight-python"><pre><code>x = 1</code></pre></div>'
        )
        assert len(parser.code_blocks) >= 1

    def test_meta_last_modified(self) -> None:
        """Detects last-modified from meta tags."""
        from scripts.generate_public_docs_audit import _DocsHTMLParser

        parser = _DocsHTMLParser("https://example.com")
        parser.feed('<meta property="article:modified_time" content="2024-06-15">')
        assert parser.last_updated_hint == "2024-06-15"


class TestPublicDocsAuditBuildHtml:
    """Tests for _build_html."""

    def test_builds_html_basic(self) -> None:
        """Generates valid HTML output."""
        from scripts.generate_public_docs_audit import _build_html

        payload = {
            "generated_at": "2026-03-21T00:00:00Z",
            "site_urls": ["https://example.com"],
            "topology_mode": "single",
            "aggregate": {
                "metrics": {
                    "crawl": {"pages_crawled": 5, "requested_pages": 10, "max_pages_total": 50},
                    "links": {"broken_internal_links_count": 1, "docs_broken_links_count": 0, "repo_broken_links_count": 1},
                    "seo_geo": {"seo_geo_issue_rate_pct": 5.0},
                    "api_coverage": {"reference_coverage_pct": 80.0, "no_api_pages_found": False},
                    "examples": {"example_reliability_estimate_pct": 90.0},
                    "freshness": {"last_updated_coverage_pct": 60.0},
                }
            },
            "sites": [],
            "top_findings": [],
        }
        result = _build_html(payload)
        assert "<!DOCTYPE html>" in result
        assert "5" in result  # pages_crawled


# ---------------------------------------------------------------------------
# build_acme_demo_site -- additional coverage
# ---------------------------------------------------------------------------

class TestBuildAcmeValidatePageContract:
    """Tests for _validate_page_contract."""

    def test_missing_mkdocs(self, tmp_path: Path) -> None:
        """Raises FileNotFoundError when mkdocs.yml missing."""
        from scripts.build_acme_demo_site import _validate_page_contract

        with pytest.raises(FileNotFoundError, match="Missing"):
            _validate_page_contract(tmp_path)

    def test_invalid_mkdocs_format(self, tmp_path: Path) -> None:
        """Raises ValueError for non-dict mkdocs.yml."""
        from scripts.build_acme_demo_site import _validate_page_contract

        (tmp_path / "mkdocs.yml").write_text("- list item", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid mkdocs.yml"):
            _validate_page_contract(tmp_path)

    def test_missing_nav(self, tmp_path: Path) -> None:
        """Raises ValueError when nav is not a list."""
        from scripts.build_acme_demo_site import _validate_page_contract

        (tmp_path / "mkdocs.yml").write_text("site_name: test\n", encoding="utf-8")
        with pytest.raises(ValueError, match="nav list"):
            _validate_page_contract(tmp_path)


class TestBuildAcmeValidateLocalLinks:
    """Tests for _validate_local_links."""

    def test_valid_links_pass(self, tmp_path: Path) -> None:
        """Docs with valid internal links pass."""
        from scripts.build_acme_demo_site import _validate_local_links

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("Check [other](other.md)", encoding="utf-8")
        (docs / "other.md").write_text("Content", encoding="utf-8")
        _validate_local_links(tmp_path)

    def test_broken_link_fails(self, tmp_path: Path) -> None:
        """Docs with broken local link raises ValueError."""
        from scripts.build_acme_demo_site import _validate_local_links

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("Check [missing](nonexistent.md)", encoding="utf-8")
        with pytest.raises(ValueError, match="Local link integrity"):
            _validate_local_links(tmp_path)

    def test_external_links_ignored(self, tmp_path: Path) -> None:
        """External links are not checked."""
        from scripts.build_acme_demo_site import _validate_local_links

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("Check [ext](https://example.com)", encoding="utf-8")
        _validate_local_links(tmp_path)

    def test_anchor_links_ignored(self, tmp_path: Path) -> None:
        """Fragment-only links are not checked."""
        from scripts.build_acme_demo_site import _validate_local_links

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("Check [section](#section-title)", encoding="utf-8")
        _validate_local_links(tmp_path)


class TestBuildAcmeValidateAssetsContract:
    """Tests for _validate_assets_contract."""

    def test_missing_assets_raises(self, tmp_path: Path) -> None:
        """Raises FileNotFoundError when required assets missing."""
        from scripts.build_acme_demo_site import _validate_assets_contract

        docs = tmp_path / "docs"
        docs.mkdir()
        with pytest.raises(FileNotFoundError, match="Missing required pipeline assets"):
            _validate_assets_contract(tmp_path)


class TestBuildAcmeRunAllowFail:
    """Tests for _run_allow_fail."""

    def test_returns_zero_on_success(self) -> None:
        """Returns 0 when command succeeds."""
        from scripts.build_acme_demo_site import _run_allow_fail

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        with mock.patch("subprocess.run", return_value=mock_result):
            rc = _run_allow_fail(["echo", "ok"], Path("."), "test")
        assert rc == 0

    def test_returns_nonzero_on_failure(self) -> None:
        """Returns nonzero but does not raise on failure."""
        from scripts.build_acme_demo_site import _run_allow_fail

        mock_result = mock.MagicMock()
        mock_result.returncode = 1
        with mock.patch("subprocess.run", return_value=mock_result):
            rc = _run_allow_fail(["false"], Path("."), "test-label")
        assert rc == 1


# ---------------------------------------------------------------------------
# provision_client_repo -- additional coverage
# ---------------------------------------------------------------------------

class TestProvisionEnvChecklist:
    """Tests for generate_env_checklist."""

    def test_no_runtime_returns_none(self, tmp_path: Path) -> None:
        """Returns None when runtime config does not exist."""
        from scripts.provision_client_repo import generate_env_checklist

        result = generate_env_checklist(tmp_path, "docsops")
        assert result is None

    def test_generates_checklist(self, tmp_path: Path) -> None:
        """Generates ENV_CHECKLIST.md with core section."""
        from scripts.provision_client_repo import generate_env_checklist

        docsops = tmp_path / "docsops" / "config"
        docsops.mkdir(parents=True)
        runtime = {
            "integrations": {"algolia": {"enabled": False}, "ask_ai": {"enabled": False}},
            "api_first": {"sandbox_backend": "docker"},
            "pr_autofix": {"enabled": False},
        }
        (docsops / "client_runtime.yml").write_text(yaml.safe_dump(runtime), encoding="utf-8")
        result = generate_env_checklist(tmp_path, "docsops")
        assert result is not None
        text = result.read_text(encoding="utf-8")
        assert "GITHUB_TOKEN" in text


class TestProvisionInstallPrAutofix:
    """Tests for install_pr_autofix_workflow."""

    def test_no_runtime_returns_none(self, tmp_path: Path) -> None:
        """Returns None when runtime missing."""
        from scripts.provision_client_repo import install_pr_autofix_workflow

        assert install_pr_autofix_workflow(tmp_path, "docsops") is None

    def test_disabled_returns_none(self, tmp_path: Path) -> None:
        """Returns None when pr_autofix is disabled."""
        from scripts.provision_client_repo import install_pr_autofix_workflow

        docsops = tmp_path / "docsops" / "config"
        docsops.mkdir(parents=True)
        runtime = {"pr_autofix": {"enabled": False}}
        (docsops / "client_runtime.yml").write_text(yaml.safe_dump(runtime), encoding="utf-8")
        assert install_pr_autofix_workflow(tmp_path, "docsops") is None

    def test_enabled_creates_workflow(self, tmp_path: Path) -> None:
        """Creates GitHub workflow file when enabled."""
        from scripts.provision_client_repo import install_pr_autofix_workflow

        docsops = tmp_path / "docsops" / "config"
        docsops.mkdir(parents=True)
        runtime = {"pr_autofix": {"enabled": True}, "paths": {"docs_root": "docs"}}
        (docsops / "client_runtime.yml").write_text(yaml.safe_dump(runtime), encoding="utf-8")
        result = install_pr_autofix_workflow(tmp_path, "docsops")
        assert result is not None
        assert result.exists()
        text = result.read_text(encoding="utf-8")
        assert "VeriOps PR Auto Fix" in text


class TestProvisionApplyIntegrations:
    """Tests for apply_integrations."""

    def test_no_runtime(self, tmp_path: Path) -> None:
        """Does nothing when runtime missing."""
        from scripts.provision_client_repo import apply_integrations

        apply_integrations(tmp_path, "docsops")

    def test_auto_configure_disabled(self, tmp_path: Path) -> None:
        """Does nothing when auto_configure_on_provision is False."""
        from scripts.provision_client_repo import apply_integrations

        docsops = tmp_path / "docsops" / "config"
        docsops.mkdir(parents=True)
        runtime = {"integrations": {"ask_ai": {"auto_configure_on_provision": False}}}
        (docsops / "client_runtime.yml").write_text(yaml.safe_dump(runtime), encoding="utf-8")
        apply_integrations(tmp_path, "docsops")


class TestProvisionLoadYaml:
    """Tests for _load_yaml_mapping."""

    def test_valid_yaml(self, tmp_path: Path) -> None:
        """Loads valid YAML mapping."""
        from scripts.provision_client_repo import _load_yaml_mapping

        f = tmp_path / "test.yml"
        f.write_text("key: value\n", encoding="utf-8")
        result = _load_yaml_mapping(f)
        assert result == {"key": "value"}

    def test_non_mapping_raises(self, tmp_path: Path) -> None:
        """Raises ValueError for non-mapping YAML."""
        from scripts.provision_client_repo import _load_yaml_mapping

        f = tmp_path / "test.yml"
        f.write_text("- item1\n- item2\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Expected YAML mapping"):
            _load_yaml_mapping(f)


# ---------------------------------------------------------------------------
# ensure_external_mock_server -- additional coverage
# ---------------------------------------------------------------------------

class TestEnsureMockBuildPostmanCollection:
    """Tests for _build_postman_collection."""

    def test_builds_from_spec(self, tmp_path: Path) -> None:
        """Builds Postman collection from OpenAPI spec."""
        from scripts.ensure_external_mock_server import _build_postman_collection

        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0"},
            "servers": [{"url": "https://api.example.com/v1"}],
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "listUsers",
                        "summary": "List users",
                        "responses": {"200": {"description": "OK"}},
                    },
                    "post": {
                        "operationId": "createUser",
                        "summary": "Create user",
                        "requestBody": {
                            "content": {"application/json": {"example": {"name": "John"}}}
                        },
                        "responses": {"201": {"description": "Created"}},
                    },
                }
            },
        }
        f = tmp_path / "openapi.yaml"
        f.write_text(yaml.safe_dump(spec), encoding="utf-8")
        result = _build_postman_collection(str(f), "test-col", "https://api.example.com/v1")
        assert result["info"]["name"] == "test-col"
        assert len(result["item"]) == 2  # GET and POST


class TestEnsureMockFindExistingByName:
    """Tests for _find_existing_mock_by_name."""

    def test_returns_none_when_all_fail(self) -> None:
        """Returns None when all endpoints fail."""
        from scripts.ensure_external_mock_server import _find_existing_mock_by_name

        with mock.patch("scripts.ensure_external_mock_server._http_json", side_effect=Exception("fail")):
            result = _find_existing_mock_by_name("https://api.example.com", "key", "ws-1", "my-mock")
        assert result is None

    def test_finds_existing_mock(self) -> None:
        """Finds existing mock by name."""
        from scripts.ensure_external_mock_server import _find_existing_mock_by_name

        mock_response = {"mocks": [{"name": "my-mock", "id": "m1", "url": "https://m.com"}]}
        with mock.patch("scripts.ensure_external_mock_server._http_json", return_value=mock_response):
            result = _find_existing_mock_by_name("https://api.example.com", "key", "ws-1", "my-mock")
        assert result is not None
        assert result["mock_server_id"] == "m1"

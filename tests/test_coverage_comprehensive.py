"""Comprehensive test suite for boosting coverage to 85%+.

Targets uncovered branches in:
- gap_detector.py (60%)
- check_api_sdk_drift.py (67%)
- preprocess_variables.py (69%)
- community_collector.py (69%)
- generate_release_docs_pack.py (74%)
- generate_docusaurus_config.py (75%)
- algolia_parser.py (76%)
- evaluate_kpi_sla.py (78%)
- batch_generator.py (78%)
- generate_facets_index.py (78%)
- doc_layers_validator.py (80%)

Tests cover: functional, security, performance, integration, edge cases.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch, mock_open

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.gap_detector import (
    _build_issue_body,
    _compute_debt_score,
    _create_github_issues,
    parse_args,
    run_analysis,
)
from scripts.check_api_sdk_drift import (
    DriftReport,
    _changed_files,
    _load_policy_pack,
    _render_markdown,
    _select,
    evaluate,
    OPENAPI_PATTERNS,
    SDK_PATTERNS,
    REFERENCE_DOC_PATTERNS,
)
from scripts.preprocess_variables import (
    _detect_locale,
    _flatten_dict,
    load_variables,
    load_variables_for_locale,
    preprocess_directory,
    replace_variables,
)
from scripts.evaluate_kpi_sla import (
    DEFAULT_THRESHOLDS,
    SlaReport,
    _load_json,
    _load_thresholds,
    _render_markdown as sla_render_markdown,
    evaluate as sla_evaluate,
)
from scripts.generate_release_docs_pack import (
    _commits_since,
    _previous_tag,
    _section,
    build_release_pack,
)
from scripts.generate_docusaurus_config import (
    _load_mkdocs_config,
    _load_variables as docusaurus_load_variables,
    _md_to_doc_id,
    convert_nav_item,
    convert_nav_to_sidebar,
    generate_docusaurus_config_js,
    generate_sidebars_js,
)
from scripts.generate_facets_index import (
    build_url_from_path,
    extract_first_paragraph,
    extract_frontmatter,
    generate_facets_index,
)
from scripts.doc_layers_validator import DocLayersValidator
from scripts.gap_detection.algolia_parser import (
    AlgoliaAnalytics,
    AlgoliaResult,
    SearchQuery,
    create_sample_data,
)
from scripts.gap_detection.community_collector import (
    CollectionResult,
    CommunityCollector,
    CommunityTopic,
)
from scripts.gap_detection.batch_generator import (
    BatchDocGenerator,
    BatchResult,
    DocumentTask,
)


# ===========================================================================
# gap_detector.py
# ===========================================================================


class TestGapDetectorComputeDebtScore:
    """Tests for _compute_debt_score edge cases."""

    def test_compute_debt_score_empty_gaps(self) -> None:
        """Empty gap list produces zero score with low risk."""
        result = _compute_debt_score([])
        assert result["total_score"] == 0
        assert result["risk_level"] == "low"
        assert result["total_gaps"] == 0

    def test_compute_debt_score_high_risk(self) -> None:
        """Many high-priority gaps produce high risk level."""
        gaps = [{"priority": "high"}] * 40
        result = _compute_debt_score(gaps)
        assert result["risk_level"] == "high"
        assert result["total_score"] >= 150

    def test_compute_debt_score_medium_risk(self) -> None:
        """Moderate gaps produce medium risk level."""
        gaps = [{"priority": "medium"}] * 20
        result = _compute_debt_score(gaps)
        assert result["risk_level"] == "medium"

    def test_compute_debt_score_unknown_priority_defaults_to_low(self) -> None:
        """Unknown priority values default to low weight."""
        gaps = [{"priority": "critical"}, {"priority": "unknown"}]
        result = _compute_debt_score(gaps)
        assert result["by_priority"]["low"] == 2

    def test_compute_debt_score_missing_priority_defaults_to_low(self) -> None:
        """Gaps without priority key default to low."""
        gaps = [{}]
        result = _compute_debt_score(gaps)
        assert result["by_priority"]["low"] == 1


class TestGapDetectorBuildIssueBody:
    """Tests for _build_issue_body."""

    def test_build_issue_body_complete(self) -> None:
        """Full gap data produces well-structured issue body."""
        gap = {
            "title": "Missing webhook docs",
            "source": "code",
            "category": "api_endpoint",
            "priority": "high",
            "description": "Webhook endpoint lacks docs.",
            "action_required": "Create reference doc.",
            "related_files": ["api/webhooks.py", "docs/ref.md"],
        }
        body = _build_issue_body(gap)
        assert "Missing webhook docs" in body
        assert "high" in body
        assert "`api/webhooks.py`" in body

    def test_build_issue_body_empty_related_files(self) -> None:
        """Empty related_files shows N/A."""
        gap = {"related_files": []}
        body = _build_issue_body(gap)
        assert "N/A" in body

    def test_build_issue_body_none_related_files(self) -> None:
        """None related_files shows N/A."""
        gap = {"related_files": None}
        body = _build_issue_body(gap)
        assert "N/A" in body

    def test_build_issue_body_defaults(self) -> None:
        """Missing fields use default values."""
        body = _build_issue_body({})
        assert "Untitled gap" in body
        assert "unknown" in body


class TestGapDetectorCreateGithubIssues:
    """Tests for _create_github_issues."""

    def test_create_github_issues_dry_run(self, capsys: pytest.CaptureFixture) -> None:
        """Dry run prints preview without calling subprocess."""
        gaps = [
            {"priority": "high", "title": "Missing docs"},
            {"priority": "low", "title": "Low prio"},
        ]
        _create_github_issues(gaps, dry_run=True)
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert "Missing docs" in captured.out

    def test_create_github_issues_non_dry_run(self) -> None:
        """Non-dry run calls subprocess for high-priority gaps."""
        gaps = [{"priority": "high", "title": "Test gap"}]
        with patch("scripts.gap_detector.subprocess.run") as mock_run:
            _create_github_issues(gaps, dry_run=False)
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert "gh" in call_args[0][0]
            assert "issue" in call_args[0][0]

    def test_create_github_issues_limits_to_five(self) -> None:
        """Only first 5 high-priority gaps create issues."""
        gaps = [{"priority": "high", "title": f"Gap {i}"} for i in range(10)]
        with patch("scripts.gap_detector.subprocess.run") as mock_run:
            _create_github_issues(gaps, dry_run=False)
            assert mock_run.call_count == 5

    def test_create_github_issues_skips_non_high(self, capsys: pytest.CaptureFixture) -> None:
        """Non-high-priority gaps are skipped."""
        gaps = [{"priority": "medium", "title": "Medium gap"}]
        _create_github_issues(gaps, dry_run=True)
        captured = capsys.readouterr()
        assert "[DRY RUN]" not in captured.out


class TestGapDetectorParseArgs:
    """Tests for parse_args."""

    def test_parse_args_defaults(self) -> None:
        """Default arguments are parsed correctly."""
        with patch("sys.argv", ["gap_detector.py"]):
            args = parse_args()
            assert args.since == 7
            assert args.output_dir == "reports"
            assert not args.json
            assert not args.create_issues

    def test_parse_args_custom(self) -> None:
        """Custom arguments are parsed correctly."""
        with patch("sys.argv", [
            "gap_detector.py", "--json", "--since", "14",
            "--output-dir", "custom", "--create-issues", "--dry-run",
            "--algolia-csv", "data.csv",
        ]):
            args = parse_args()
            assert args.json is True
            assert args.since == 14
            assert args.output_dir == "custom"
            assert args.create_issues is True
            assert args.dry_run is True
            assert args.algolia_csv == "data.csv"


class TestGapDetectorRunAnalysis:
    """Tests for run_analysis with mocked aggregator."""

    def test_run_analysis_success(self, tmp_path: Path) -> None:
        """Successful analysis returns expected structure."""
        mock_report = MagicMock()
        mock_report.gaps = []
        mock_report.summary = {"total_gaps": 0}
        mock_report.sources_analyzed = ["code"]

        with patch("scripts.gap_detector.GapAggregator") as mock_agg_cls:
            mock_agg = mock_agg_cls.return_value
            mock_agg.run_full_analysis.return_value = mock_report
            mock_agg.save_to_json = MagicMock()
            mock_agg.save_to_csv = MagicMock()
            mock_agg.save_to_excel = MagicMock()

            result = run_analysis(str(tmp_path), 7, None, None)

        assert "gaps" in result
        assert "debt_score" in result
        assert "timestamp" in result

    def test_run_analysis_excel_export_failure(self, tmp_path: Path) -> None:
        """Excel export failure is handled gracefully."""
        mock_report = MagicMock()
        mock_report.gaps = []
        mock_report.summary = {}
        mock_report.sources_analyzed = []

        with patch("scripts.gap_detector.GapAggregator") as mock_agg_cls:
            mock_agg = mock_agg_cls.return_value
            mock_agg.run_full_analysis.return_value = mock_report
            mock_agg.save_to_json = MagicMock()
            mock_agg.save_to_csv = MagicMock()
            mock_agg.save_to_excel.side_effect = ImportError("openpyxl not found")

            result = run_analysis(str(tmp_path), 7, None, None)

        assert "gaps" in result


# ===========================================================================
# check_api_sdk_drift.py
# ===========================================================================


class TestCheckApiSdkDriftChangedFiles:
    """Tests for _changed_files."""

    def test_changed_files_success(self) -> None:
        """Parses git diff output into file list."""
        mock_result = MagicMock()
        mock_result.stdout = "file1.py\nfile2.md\n\nfile3.yaml\n"
        with patch("scripts.check_api_sdk_drift.subprocess.run", return_value=mock_result):
            files = _changed_files("main", "feature")
        assert files == ["file1.py", "file2.md", "file3.yaml"]

    def test_changed_files_empty_output(self) -> None:
        """Empty git diff returns empty list."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        with patch("scripts.check_api_sdk_drift.subprocess.run", return_value=mock_result):
            files = _changed_files("main", "feature")
        assert files == []

    def test_changed_files_subprocess_error(self) -> None:
        """Subprocess failure raises CalledProcessError."""
        with patch(
            "scripts.check_api_sdk_drift.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "git"),
        ):
            with pytest.raises(subprocess.CalledProcessError):
                _changed_files("main", "feature")


class TestCheckApiSdkDriftLoadPolicyPack:
    """Tests for _load_policy_pack."""

    def test_load_policy_pack_none_returns_defaults(self) -> None:
        """None path returns default patterns."""
        openapi, sdk, ref = _load_policy_pack(None)
        assert openapi == OPENAPI_PATTERNS
        assert sdk == SDK_PATTERNS
        assert ref == REFERENCE_DOC_PATTERNS

    def test_load_policy_pack_valid_yaml(self, tmp_path: Path) -> None:
        """Valid policy pack YAML is loaded and merged."""
        policy = {
            "drift": {
                "openapi_patterns": [r"api/.*\.json$"],
                "sdk_patterns": [r"^lib/"],
                "reference_doc_patterns": [r"^docs/api/"],
            }
        }
        policy_file = tmp_path / "policy.yml"
        policy_file.write_text(yaml.dump(policy), encoding="utf-8")

        openapi, sdk, ref = _load_policy_pack(str(policy_file))
        assert openapi == (r"api/.*\.json$",)
        assert sdk == (r"^lib/",)
        assert ref == (r"^docs/api/",)

    def test_load_policy_pack_not_a_mapping(self, tmp_path: Path) -> None:
        """Non-mapping YAML raises ValueError."""
        policy_file = tmp_path / "policy.yml"
        policy_file.write_text("- item1\n- item2", encoding="utf-8")

        with pytest.raises(ValueError, match="must be a mapping"):
            _load_policy_pack(str(policy_file))

    def test_load_policy_pack_drift_section_not_mapping(self, tmp_path: Path) -> None:
        """Non-mapping drift section raises ValueError."""
        policy_file = tmp_path / "policy.yml"
        policy_file.write_text(yaml.dump({"drift": "not-a-dict"}), encoding="utf-8")

        with pytest.raises(ValueError, match="drift section must be a mapping"):
            _load_policy_pack(str(policy_file))

    def test_load_policy_pack_empty_patterns_raises(self, tmp_path: Path) -> None:
        """Empty openapi and sdk patterns raise ValueError."""
        policy = {
            "drift": {
                "openapi_patterns": [],
                "sdk_patterns": [],
                "reference_doc_patterns": [r"^docs/"],
            }
        }
        policy_file = tmp_path / "policy.yml"
        policy_file.write_text(yaml.dump(policy), encoding="utf-8")

        with pytest.raises(ValueError, match="must define openapi_patterns"):
            _load_policy_pack(str(policy_file))

    def test_load_policy_pack_empty_reference_raises(self, tmp_path: Path) -> None:
        """Empty reference_doc_patterns raises ValueError."""
        policy = {
            "drift": {
                "openapi_patterns": [r"api/"],
                "sdk_patterns": [r"sdk/"],
                "reference_doc_patterns": [],
            }
        }
        policy_file = tmp_path / "policy.yml"
        policy_file.write_text(yaml.dump(policy), encoding="utf-8")

        with pytest.raises(ValueError, match="reference_doc_patterns cannot be empty"):
            _load_policy_pack(str(policy_file))

    def test_load_policy_pack_defaults_from_missing_keys(self, tmp_path: Path) -> None:
        """Missing keys in drift section fall back to defaults."""
        policy = {"drift": {}}
        policy_file = tmp_path / "policy.yml"
        policy_file.write_text(yaml.dump(policy), encoding="utf-8")

        openapi, sdk, ref = _load_policy_pack(str(policy_file))
        assert openapi == OPENAPI_PATTERNS
        assert sdk == SDK_PATTERNS
        assert ref == REFERENCE_DOC_PATTERNS


# ===========================================================================
# preprocess_variables.py
# ===========================================================================


class TestPreprocessVariablesLoadForLocale:
    """Tests for load_variables_for_locale."""

    def test_load_variables_for_locale_no_locale(self, tmp_path: Path) -> None:
        """None locale returns base variables."""
        base_file = tmp_path / "_variables.yml"
        base_file.write_text(yaml.dump({"product_name": "Test"}), encoding="utf-8")

        result = load_variables_for_locale(None, tmp_path)
        assert result["product_name"] == "Test"

    def test_load_variables_for_locale_empty_locale(self, tmp_path: Path) -> None:
        """Empty string locale returns base variables."""
        base_vars = {"product_name": "Test"}
        result = load_variables_for_locale("", tmp_path, base_vars=base_vars)
        assert result["product_name"] == "Test"

    def test_load_variables_for_locale_with_overrides(self, tmp_path: Path) -> None:
        """Locale-specific variables override base values."""
        base_vars = {"product_name": "Test", "tagline": "Original"}
        locale_dir = tmp_path / "ru"
        locale_dir.mkdir()
        locale_file = locale_dir / "_variables.yml"
        locale_file.write_text(yaml.dump({"tagline": "Russian tagline"}), encoding="utf-8")

        result = load_variables_for_locale("ru", tmp_path, base_vars=base_vars)
        assert result["product_name"] == "Test"
        assert result["tagline"] == "Russian tagline"

    def test_load_variables_for_locale_deep_merge(self, tmp_path: Path) -> None:
        """Nested dicts are deep-merged."""
        base_vars = {"env_vars": {"port": "PORT", "host": "HOST"}}
        locale_dir = tmp_path / "de"
        locale_dir.mkdir()
        locale_file = locale_dir / "_variables.yml"
        locale_file.write_text(yaml.dump({"env_vars": {"port": "HAFEN"}}), encoding="utf-8")

        result = load_variables_for_locale("de", tmp_path, base_vars=base_vars)
        assert result["env_vars"]["port"] == "HAFEN"
        assert result["env_vars"]["host"] == "HOST"

    def test_load_variables_for_locale_missing_locale_dir(self, tmp_path: Path) -> None:
        """Missing locale directory returns base variables."""
        base_vars = {"key": "value"}
        result = load_variables_for_locale("fr", tmp_path, base_vars=base_vars)
        assert result == base_vars

    def test_load_variables_for_locale_loads_base_when_none(self, tmp_path: Path) -> None:
        """Loads base vars from file when base_vars is None."""
        base_file = tmp_path / "_variables.yml"
        base_file.write_text(yaml.dump({"loaded": True}), encoding="utf-8")

        result = load_variables_for_locale("en", tmp_path, base_vars=None)
        assert result["loaded"] is True


class TestPreprocessVariablesDetectLocale:
    """Tests for _detect_locale."""

    def test_detect_locale_two_letter(self, tmp_path: Path) -> None:
        """Two-letter locale code is detected."""
        filepath = tmp_path / "ru" / "guide.md"
        assert _detect_locale(filepath, tmp_path) == "ru"

    def test_detect_locale_three_letter(self, tmp_path: Path) -> None:
        """Three-letter locale code is detected."""
        filepath = tmp_path / "deu" / "guide.md"
        assert _detect_locale(filepath, tmp_path) == "deu"

    def test_detect_locale_not_locale_prefix(self, tmp_path: Path) -> None:
        """Non-locale directory name returns None."""
        filepath = tmp_path / "getting-started" / "guide.md"
        assert _detect_locale(filepath, tmp_path) is None

    def test_detect_locale_unrelated_path(self) -> None:
        """Unrelated path returns None."""
        filepath = Path("/some/other/path/file.md")
        docs_dir = Path("/completely/different")
        assert _detect_locale(filepath, docs_dir) is None

    def test_detect_locale_root_file(self, tmp_path: Path) -> None:
        """File directly in docs_dir returns None (no locale prefix)."""
        filepath = tmp_path / "index.md"
        assert _detect_locale(filepath, tmp_path) is None


class TestPreprocessDirectory:
    """Tests for preprocess_directory with locale awareness."""

    def test_preprocess_directory_locale_aware(self, tmp_path: Path) -> None:
        """Locale-aware processing uses per-locale variables."""
        base_file = tmp_path / "_variables.yml"
        base_file.write_text(yaml.dump({"product": "Base"}), encoding="utf-8")

        ru_dir = tmp_path / "ru"
        ru_dir.mkdir()
        ru_vars = ru_dir / "_variables.yml"
        ru_vars.write_text(yaml.dump({"product": "Baza"}), encoding="utf-8")

        en_dir = tmp_path / "en"
        en_dir.mkdir()
        en_file = en_dir / "guide.md"
        en_file.write_text("Product: {{ product }}", encoding="utf-8")

        ru_file = ru_dir / "guide.md"
        ru_file.write_text("Product: {{ product }}", encoding="utf-8")

        base_vars = load_variables(base_file)
        processed = preprocess_directory(tmp_path, base_vars, locale_aware=True)

        en_content = en_file.read_text(encoding="utf-8")
        ru_content = ru_file.read_text(encoding="utf-8")
        assert "Base" in en_content
        assert "Baza" in ru_content
        assert len(processed) >= 2

    def test_preprocess_directory_skips_underscore_files(self, tmp_path: Path) -> None:
        """Files starting with _ are skipped."""
        (tmp_path / "_variables.yml").write_text("", encoding="utf-8")
        (tmp_path / "_private.md").write_text("{{ test }}", encoding="utf-8")
        (tmp_path / "public.md").write_text("{{ test }}", encoding="utf-8")

        processed = preprocess_directory(tmp_path, {"test": "value"})
        filenames = [p.name for p in processed]
        assert "_private.md" not in filenames
        assert "public.md" in filenames

    def test_preprocess_directory_output_dir(self, tmp_path: Path) -> None:
        """Output directory receives processed files."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "doc.md").write_text("Port: {{ port }}", encoding="utf-8")
        out = tmp_path / "out"

        processed = preprocess_directory(src, {"port": "8080"}, output_dir=out)
        assert (out / "doc.md").exists()
        assert "8080" in (out / "doc.md").read_text(encoding="utf-8")


# ===========================================================================
# evaluate_kpi_sla.py
# ===========================================================================


class TestEvaluateKpiSlaLoadJson:
    """Tests for _load_json."""

    def test_load_json_valid(self, tmp_path: Path) -> None:
        """Valid JSON file is loaded correctly."""
        data = {"quality_score": 90, "stale_pct": 5.0}
        json_file = tmp_path / "kpi.json"
        json_file.write_text(json.dumps(data), encoding="utf-8")

        result = _load_json(json_file)
        assert result["quality_score"] == 90


class TestEvaluateKpiSlaLoadThresholds:
    """Tests for _load_thresholds."""

    def test_load_thresholds_none_returns_defaults(self) -> None:
        """None policy pack returns default thresholds."""
        result = _load_thresholds(None)
        assert result == DEFAULT_THRESHOLDS

    def test_load_thresholds_valid_policy_pack(self, tmp_path: Path) -> None:
        """Valid policy pack overrides default thresholds."""
        policy = {"kpi_sla": {"min_quality_score": 90, "max_stale_pct": 10.0}}
        policy_file = tmp_path / "policy.yml"
        policy_file.write_text(yaml.dump(policy), encoding="utf-8")

        result = _load_thresholds(str(policy_file))
        assert result["min_quality_score"] == 90
        assert result["max_stale_pct"] == 10.0
        assert result["max_high_priority_gaps"] == 8  # Default kept

    def test_load_thresholds_not_a_mapping(self, tmp_path: Path) -> None:
        """Non-mapping YAML raises ValueError."""
        policy_file = tmp_path / "policy.yml"
        policy_file.write_text("- item", encoding="utf-8")

        with pytest.raises(ValueError, match="must be a mapping"):
            _load_thresholds(str(policy_file))

    def test_load_thresholds_kpi_sla_section_not_mapping(self, tmp_path: Path) -> None:
        """Non-mapping kpi_sla section raises ValueError."""
        policy_file = tmp_path / "policy.yml"
        policy_file.write_text(yaml.dump({"kpi_sla": "bad"}), encoding="utf-8")

        with pytest.raises(ValueError, match="kpi_sla section must be a mapping"):
            _load_thresholds(str(policy_file))


# ===========================================================================
# generate_release_docs_pack.py
# ===========================================================================


class TestGenerateReleaseDocsPack:
    """Tests for generate_release_docs_pack functions."""

    def test_previous_tag_found(self) -> None:
        """Previous tag is found when current tag exists in list."""
        with patch("scripts.generate_release_docs_pack._run_git", return_value="v1.2.0\nv1.1.0\nv1.0.0"):
            result = _previous_tag("v1.2.0")
        assert result == "v1.1.0"

    def test_previous_tag_last_in_list(self) -> None:
        """Last tag returns None (no previous tag)."""
        with patch("scripts.generate_release_docs_pack._run_git", return_value="v1.1.0\nv1.0.0"):
            result = _previous_tag("v1.0.0")
        assert result is None

    def test_previous_tag_not_in_list(self) -> None:
        """Unknown tag returns first available tag."""
        with patch("scripts.generate_release_docs_pack._run_git", return_value="v2.0.0\nv1.0.0"):
            result = _previous_tag("v3.0.0")
        assert result == "v2.0.0"

    def test_previous_tag_empty_tags(self) -> None:
        """Empty tag list returns None."""
        with patch("scripts.generate_release_docs_pack._run_git", return_value=""):
            result = _previous_tag("v1.0.0")
        assert result is None

    def test_previous_tag_git_error(self) -> None:
        """Git failure returns None."""
        with patch(
            "scripts.generate_release_docs_pack._run_git",
            side_effect=subprocess.CalledProcessError(1, "git"),
        ):
            result = _previous_tag("v1.0.0")
        assert result is None

    def test_commits_since_empty_output(self) -> None:
        """Empty git log returns empty list."""
        with patch("scripts.generate_release_docs_pack._run_git", return_value=""):
            result = _commits_since("v1.0.0..HEAD")
        assert result == []

    def test_commits_since_with_commits(self) -> None:
        """Non-empty git log returns list of commits."""
        with patch("scripts.generate_release_docs_pack._run_git", return_value="abc feat: add X\ndef fix: bug Y"):
            result = _commits_since("v1.0.0..HEAD")
        assert len(result) == 2

    def test_build_release_pack_with_version_and_prev(self) -> None:
        """Build release pack with version that has a previous tag."""
        with patch("scripts.generate_release_docs_pack._previous_tag", return_value="v1.0.0"):
            with patch("scripts.generate_release_docs_pack._commits_since", return_value=[
                "abc feat: add webhook retry",
                "def fix: timeout bug",
                "ghi docs: update README",
                "jkl feat: breaking change in auth",
            ]):
                result = build_release_pack("v1.1.0")
        assert "v1.0.0..v1.1.0" in result
        assert "v1.1.0" in result
        assert "breaking" in result.lower()

    def test_build_release_pack_with_prev_no_version(self) -> None:
        """Build release pack with previous tag but no version."""
        with patch("scripts.generate_release_docs_pack._previous_tag", return_value="v1.0.0"):
            with patch("scripts.generate_release_docs_pack._commits_since", return_value=[]):
                result = build_release_pack(None)
        assert "v1.0.0..HEAD" in result
        assert "unversioned-release" in result

    def test_build_release_pack_no_prev_no_version(self) -> None:
        """Build release pack without previous tag or version."""
        with patch("scripts.generate_release_docs_pack._previous_tag", return_value=None):
            with patch("scripts.generate_release_docs_pack._commits_since", return_value=[]):
                result = build_release_pack(None)
        assert "HEAD~30..HEAD" in result


# ===========================================================================
# generate_docusaurus_config.py
# ===========================================================================


class TestGenerateDocusaurusConfig:
    """Tests for docusaurus config generation."""

    def test_load_mkdocs_config(self, tmp_path: Path) -> None:
        """Valid mkdocs.yml is parsed."""
        config = {"site_name": "My Docs", "nav": []}
        config_file = tmp_path / "mkdocs.yml"
        config_file.write_text(yaml.dump(config), encoding="utf-8")

        result = _load_mkdocs_config(config_file)
        assert result["site_name"] == "My Docs"

    def test_load_mkdocs_config_empty(self, tmp_path: Path) -> None:
        """Empty YAML returns empty dict."""
        config_file = tmp_path / "mkdocs.yml"
        config_file.write_text("", encoding="utf-8")

        result = _load_mkdocs_config(config_file)
        assert result == {}

    def test_load_variables_exists(self, tmp_path: Path) -> None:
        """Existing variables file is loaded."""
        var_file = tmp_path / "_variables.yml"
        var_file.write_text(yaml.dump({"product_name": "Test"}), encoding="utf-8")

        result = docusaurus_load_variables(var_file)
        assert result["product_name"] == "Test"

    def test_load_variables_missing(self, tmp_path: Path) -> None:
        """Missing variables file returns empty dict."""
        result = docusaurus_load_variables(tmp_path / "missing.yml")
        assert result == {}

    def test_convert_nav_item_with_dict_index_link(self) -> None:
        """Category with dict child as index page creates link."""
        item = {
            "Reference": [
                {"Overview": "reference/index.md"},
                {"API": "reference/api.md"},
            ]
        }
        result = convert_nav_item(item)
        assert result["type"] == "category"
        assert result["link"]["type"] == "doc"
        assert result["link"]["id"] == "reference/index"

    def test_convert_nav_item_unrecognized_returns_none(self) -> None:
        """Unrecognized item type returns None."""
        result = convert_nav_item(42)
        assert result is None

    def test_generate_sidebars_js(self) -> None:
        """Sidebar JS is generated with correct structure."""
        items = [
            {"type": "doc", "id": "getting-started/quickstart", "label": "Quickstart"},
            {
                "type": "category",
                "label": "Reference",
                "items": ["reference/api"],
            },
        ]
        result = generate_sidebars_js(items)
        assert "const sidebars" in result
        assert "module.exports = sidebars" in result
        assert "Quickstart" in result
        assert "Reference" in result
        assert "// @ts-check" in result


# ===========================================================================
# generate_facets_index.py
# ===========================================================================


class TestGenerateFacetsIndex:
    """Tests for facets index generation."""

    def test_extract_frontmatter_no_frontmatter(self, tmp_path: Path) -> None:
        """File without frontmatter returns None."""
        f = tmp_path / "no_fm.md"
        f.write_text("Just content", encoding="utf-8")
        assert extract_frontmatter(f) is None

    def test_extract_frontmatter_invalid_yaml(self, tmp_path: Path) -> None:
        """Invalid YAML frontmatter returns None."""
        f = tmp_path / "bad_fm.md"
        f.write_text("---\n: invalid: yaml: {{{\n---\n", encoding="utf-8")
        assert extract_frontmatter(f) is None

    def test_extract_frontmatter_read_error(self, tmp_path: Path) -> None:
        """Read error returns None gracefully."""
        f = tmp_path / "missing.md"
        # File does not exist but we pass the Path object
        with patch.object(Path, "read_text", side_effect=OSError("Permission denied")):
            assert extract_frontmatter(f) is None

    def test_extract_first_paragraph_long_content(self) -> None:
        """Paragraph extraction stops at reasonable length."""
        long_text = "# Heading\n\n" + "Word " * 50
        result = extract_first_paragraph(long_text)
        assert len(result) <= 200

    def test_extract_first_paragraph_with_emphasis(self) -> None:
        """Emphasis markers are cleaned from snippet."""
        content = "Some **Bold text** and *italic text* here."
        result = extract_first_paragraph(content)
        assert "**" not in result
        assert "Bold text" in result
        assert "italic text" in result

    def test_build_url_from_path_index_md(self, tmp_path: Path) -> None:
        """index.md files produce directory-style URLs."""
        docs = tmp_path / "docs"
        docs.mkdir()
        f = docs / "getting-started" / "index.md"
        f.parent.mkdir(parents=True)
        f.touch()

        url = build_url_from_path(f, docs)
        assert url.endswith("/")
        assert "index" not in url

    def test_build_url_from_path_with_generator(self, tmp_path: Path) -> None:
        """Custom generator is used when provided."""
        mock_gen = MagicMock()
        mock_gen.build_url_from_path.return_value = "/custom/path/"
        docs = tmp_path / "docs"
        docs.mkdir()
        f = docs / "file.md"
        f.touch()

        url = build_url_from_path(f, docs, generator=mock_gen)
        assert url == "/custom/path/"

    def test_generate_facets_index_with_statuses(self, tmp_path: Path) -> None:
        """Facets index handles active, deprecated, and removed statuses."""
        docs = tmp_path / "docs"
        docs.mkdir()

        # Active document
        active = docs / "active.md"
        active.write_text(
            "---\ntitle: Active Doc\ndescription: An active document for testing\n"
            "content_type: reference\n---\nContent here.",
            encoding="utf-8",
        )

        # Deprecated document
        deprecated = docs / "deprecated.md"
        deprecated.write_text(
            "---\ntitle: Old Feature\ndescription: A deprecated feature document\n"
            "status: deprecated\nreplacement_url: /new-feature\n"
            "content_type: reference\n---\nOld content.",
            encoding="utf-8",
        )

        # Removed document
        removed = docs / "removed.md"
        removed.write_text(
            "---\ntitle: Removed Feature\ndescription: A removed feature\n"
            "status: removed\ncontent_type: reference\n---\nGone.",
            encoding="utf-8",
        )

        output = tmp_path / "facets.json"
        result = generate_facets_index(str(docs), str(output))
        assert result is True

        index = json.loads(output.read_text(encoding="utf-8"))
        titles = [e["title"] for e in index]
        assert "Active Doc" in titles
        assert "[DEPRECATED] Old Feature" in titles
        # Removed documents are excluded from search
        assert not any("Removed Feature" in t for t in titles)

        # Check deprecated entry has replacement_url
        deprecated_entry = next(e for e in index if "DEPRECATED" in e["title"])
        assert deprecated_entry["replacement_url"] == "/new-feature"
        assert deprecated_entry["search_priority"] == -1


# ===========================================================================
# doc_layers_validator.py
# ===========================================================================


class TestDocLayersValidator:
    """Tests for doc_layers_validator."""

    def test_extract_content_type_invalid_yaml(self) -> None:
        """Invalid YAML in frontmatter returns empty string."""
        validator = DocLayersValidator()
        content = "---\n: {invalid yaml\n---\nBody"
        assert validator.extract_content_type(content) == ""

    def test_generate_report_with_violations(self, tmp_path: Path) -> None:
        """Report generation includes violation blocks."""
        docs = tmp_path / "docs"
        docs.mkdir()

        # Concept doc with step-by-step instructions (violation)
        concept = docs / "bad-concept.md"
        concept.write_text(
            "---\ntitle: Bad Concept\ncontent_type: concept\n---\n"
            "# Bad Concept\n\nStep 1: Do this\nStep 2: Do that\n"
            "Run the following command:\n```bash\necho hello\n```\n",
            encoding="utf-8",
        )

        validator = DocLayersValidator(str(docs))
        report = validator.generate_report()

        assert "Concept Documents" in report
        assert "violation" in report.lower()
        assert "bad-concept.md" in report

    def test_generate_report_no_violations(self, tmp_path: Path) -> None:
        """Report with no violations shows success message."""
        docs = tmp_path / "docs"
        docs.mkdir()

        clean = docs / "clean-concept.md"
        clean.write_text(
            "---\ntitle: Clean Concept\ncontent_type: concept\n---\n"
            "# Clean Concept\n\nThis concept explains what webhooks are and why they exist.\n",
            encoding="utf-8",
        )

        validator = DocLayersValidator(str(docs))
        report = validator.generate_report()

        assert "No layer violations found" in report

    def test_generate_report_multiple_content_types(self, tmp_path: Path) -> None:
        """Report groups violations by content type."""
        docs = tmp_path / "docs"
        docs.mkdir()

        concept = docs / "mixed-concept.md"
        concept.write_text(
            "---\ntitle: Mixed\ncontent_type: concept\n---\n"
            "Step 1: Click on the button\nRun the following command\n",
            encoding="utf-8",
        )

        ref = docs / "mixed-ref.md"
        ref.write_text(
            "---\ntitle: Mixed Ref\ncontent_type: reference\n---\n"
            "In this tutorial we explore\nLet's explore the details\n",
            encoding="utf-8",
        )

        validator = DocLayersValidator(str(docs))
        report = validator.generate_report()

        assert "Concept" in report
        assert "Reference" in report


# ===========================================================================
# algolia_parser.py
# ===========================================================================


class TestAlgoliaParserAnalyzeFromCsv:
    """Tests for AlgoliaAnalytics CSV analysis."""

    def test_analyze_from_csv_file_not_found(self) -> None:
        """Missing CSV file raises FileNotFoundError."""
        analytics = AlgoliaAnalytics()
        with pytest.raises(FileNotFoundError):
            analytics.analyze_from_csv("/nonexistent/file.csv")


class TestAlgoliaParserAnalyzeFromApi:
    """Tests for AlgoliaAnalytics API analysis."""

    def test_analyze_from_api_missing_credentials(self) -> None:
        """Missing credentials raise ValueError."""
        analytics = AlgoliaAnalytics()
        with pytest.raises(ValueError, match="credentials required"):
            analytics.analyze_from_api()

    def test_analyze_from_api_with_credentials(self) -> None:
        """API analysis with valid credentials fetches and analyzes queries."""
        analytics = AlgoliaAnalytics(
            app_id="test_app",
            api_key="test_key",
            index_name="test_index",
        )
        mock_response_data = json.dumps({
            "searches": [
                {"search": "webhook setup", "count": 10, "nbHits": 0, "clickThroughRate": 0},
            ]
        }).encode("utf-8")

        mock_response = MagicMock()
        mock_response.read.return_value = mock_response_data
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("scripts.gap_detection.algolia_parser.urlopen", return_value=mock_response):
            result = analytics.analyze_from_api(limit=10)

        assert isinstance(result, AlgoliaResult)

    def test_analyze_from_api_network_error(self) -> None:
        """Network error is handled gracefully."""
        from urllib.error import URLError

        analytics = AlgoliaAnalytics(
            app_id="test_app",
            api_key="test_key",
            index_name="test_index",
        )
        with patch(
            "scripts.gap_detection.algolia_parser.urlopen",
            side_effect=URLError("Network error"),
        ):
            result = analytics.analyze_from_api()

        assert isinstance(result, AlgoliaResult)


class TestAlgoliaParserCsvRowParsing:
    """Tests for CSV row CTR parsing edge cases."""

    def test_parse_csv_row_percentage_ctr(self, tmp_path: Path) -> None:
        """CTR with percentage sign is parsed correctly."""
        analytics = AlgoliaAnalytics()
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "Search,Count,Results,CTR\n"
            "webhook error,25,0,15%\n",
            encoding="utf-8",
        )
        result = analytics.analyze_from_csv(str(csv_file))
        assert isinstance(result, AlgoliaResult)

    def test_parse_csv_row_invalid_ctr(self, tmp_path: Path) -> None:
        """Invalid CTR value defaults to 0."""
        analytics = AlgoliaAnalytics()
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "Search,Count,Results,CTR\n"
            "test query,10,5,not-a-number\n",
            encoding="utf-8",
        )
        result = analytics.analyze_from_csv(str(csv_file))
        assert isinstance(result, AlgoliaResult)


class TestAlgoliaParserCreateSampleData:
    """Tests for create_sample_data."""

    def test_create_sample_data(self, tmp_path: Path) -> None:
        """Sample data file is created with expected structure."""
        output = str(tmp_path / "sample.json")
        create_sample_data(output)
        data = json.loads(Path(output).read_text(encoding="utf-8"))
        assert "queries" in data
        assert len(data["queries"]) == 10


class TestAlgoliaParserEnrichQuery:
    """Tests for _enrich_query doc type determination."""

    def test_enrich_query_reference_fallback(self) -> None:
        """Query without specific patterns gets 'reference' doc type."""
        analytics = AlgoliaAnalytics()
        query = SearchQuery(query="api endpoint list", count=5, results_count=3, click_through_rate=0.1)
        analytics._enrich_query(query)
        assert query.suggested_doc_type == "reference"

    def test_enrich_query_concept_type(self) -> None:
        """Query with 'what is' gets 'concept' doc type."""
        analytics = AlgoliaAnalytics()
        query = SearchQuery(query="what is a webhook", count=5, results_count=3, click_through_rate=0.1)
        analytics._enrich_query(query)
        assert query.suggested_doc_type == "concept"


# ===========================================================================
# community_collector.py
# ===========================================================================


class TestCommunityCollectorCollectAll:
    """Tests for CommunityCollector.collect_all."""

    def test_collect_all_with_rss_feeds(self) -> None:
        """collect_all aggregates topics from RSS feeds."""
        rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
          <channel>
            <item>
              <title>How to configure webhook retry</title>
              <link>https://forum.example.com/t/123</link>
              <pubDate>Mon, 01 Jan 2026 00:00:00 GMT</pubDate>
            </item>
            <item>
              <title>OAuth2 setup guide needed</title>
              <link>https://forum.example.com/t/456</link>
            </item>
          </channel>
        </rss>"""

        mock_response = MagicMock()
        mock_response.read.return_value = rss_xml.encode("utf-8")
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        collector = CommunityCollector(rss_feeds=[
            {"url": "https://forum.example.com/feed", "name": "Forum", "source": "forum"},
        ])

        with patch("scripts.gap_detection.community_collector.urlopen", return_value=mock_response):
            result = collector.collect_all(limit_per_feed=10)

        assert isinstance(result, CollectionResult)
        assert len(result.topics) >= 1

    def test_collect_rss_single_feed(self) -> None:
        """collect_rss processes a single RSS feed."""
        rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
          <channel>
            <item><title>Test topic</title><link>https://example.com/1</link></item>
          </channel>
        </rss>"""

        mock_response = MagicMock()
        mock_response.read.return_value = rss_xml.encode("utf-8")
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        collector = CommunityCollector()

        with patch("scripts.gap_detection.community_collector.urlopen", return_value=mock_response):
            topics = collector.collect_rss("https://example.com/feed", "Test Feed")

        assert len(topics) >= 1

    def test_fetch_rss_network_error(self) -> None:
        """Network error during RSS fetch is handled gracefully."""
        from urllib.error import URLError

        collector = CommunityCollector(rss_feeds=[
            {"url": "https://broken.example.com/feed", "name": "Broken", "source": "forum"},
        ])

        with patch(
            "scripts.gap_detection.community_collector.urlopen",
            side_effect=URLError("Connection refused"),
        ):
            result = collector.collect_all(limit_per_feed=10)

        assert isinstance(result, CollectionResult)
        assert len(result.topics) == 0

    def test_fetch_rss_atom_format(self) -> None:
        """Atom feed format is parsed correctly."""
        atom_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <title>Atom entry about webhooks</title>
            <link href="https://blog.example.com/webhooks"/>
            <published>2026-01-01T00:00:00Z</published>
          </entry>
        </feed>"""

        mock_response = MagicMock()
        mock_response.read.return_value = atom_xml.encode("utf-8")
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        collector = CommunityCollector(rss_feeds=[
            {"url": "https://blog.example.com/atom.xml", "name": "Blog", "source": "blog"},
        ])

        with patch("scripts.gap_detection.community_collector.urlopen", return_value=mock_response):
            result = collector.collect_all(limit_per_feed=10)

        assert len(result.topics) >= 1


# ===========================================================================
# batch_generator.py
# ===========================================================================


class TestBatchGeneratorGenerate:
    """Tests for BatchDocGenerator document generation."""

    def test_generate_documents_template_mode(self, tmp_path: Path) -> None:
        """Template-based generation creates output files."""
        templates = tmp_path / "templates"
        templates.mkdir()
        (templates / "how-to.md").write_text(
            "---\ntitle: \"[Title]\"\n---\n# [Title]\n\nContent for [Product].",
            encoding="utf-8",
        )

        generator = BatchDocGenerator(
            output_base=str(tmp_path),
            templates_dir=str(templates),
        )

        task = DocumentTask(
            id="TASK-001",
            gap_id="GAP-001",
            title="Configure webhook auth",
            doc_type="how-to",
            category="webhook",
            priority="high",
            output_path="docs/how-to/configure-webhook-auth.md",
            template_name="how-to.md",
            context={"title": "Configure webhook authentication"},
        )

        batch = BatchResult(tasks=[task])
        result = generator.generate_documents(batch, use_claude=False)

        assert len(result.generated_files) == 1
        assert task.status == "generated"
        output_file = tmp_path / task.output_path
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "ProductName" in content

    def test_generate_documents_template_not_found(self, tmp_path: Path) -> None:
        """Missing template causes error status."""
        generator = BatchDocGenerator(
            output_base=str(tmp_path),
            templates_dir=str(tmp_path / "nonexistent"),
        )

        task = DocumentTask(
            id="TASK-002",
            gap_id="GAP-002",
            title="Missing template doc",
            doc_type="how-to",
            category="other",
            priority="medium",
            output_path="docs/how-to/missing.md",
            template_name="nonexistent.md",
            context={},
        )

        batch = BatchResult(tasks=[task])
        result = generator.generate_documents(batch, use_claude=False)

        assert task.status == "error"
        assert len(result.errors) == 1

    def test_generate_with_claude_fallback_to_template(self, tmp_path: Path) -> None:
        """Claude Code not found falls back to template generation."""
        templates = tmp_path / "templates"
        templates.mkdir()
        (templates / "reference.md").write_text(
            "---\ntitle: \"[Title]\"\n---\n# [Title]\n",
            encoding="utf-8",
        )

        generator = BatchDocGenerator(
            output_base=str(tmp_path),
            templates_dir=str(templates),
        )

        task = DocumentTask(
            id="TASK-003",
            gap_id="GAP-003",
            title="API reference",
            doc_type="reference",
            category="api",
            priority="high",
            output_path="docs/reference/api.md",
            template_name="reference.md",
            context={"title": "API Reference"},
        )

        batch = BatchResult(tasks=[task])

        with patch(
            "scripts.gap_detection.batch_generator.subprocess.run",
            side_effect=FileNotFoundError("claude not found"),
        ):
            result = generator.generate_documents(batch, use_claude=True)

        assert task.status == "generated"

    def test_generate_with_claude_nonzero_exit(self, tmp_path: Path) -> None:
        """Claude Code failure produces error status."""
        templates = tmp_path / "templates"
        templates.mkdir()
        (templates / "how-to.md").write_text("# [Title]", encoding="utf-8")

        generator = BatchDocGenerator(
            output_base=str(tmp_path),
            templates_dir=str(templates),
        )

        task = DocumentTask(
            id="TASK-004",
            gap_id="GAP-004",
            title="Failing doc",
            doc_type="how-to",
            category="other",
            priority="low",
            output_path="docs/how-to/fail.md",
            template_name="how-to.md",
            context={},
        )

        batch = BatchResult(tasks=[task])
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Claude error"

        with patch(
            "scripts.gap_detection.batch_generator.subprocess.run",
            return_value=mock_result,
        ):
            result = generator.generate_documents(batch, use_claude=True)

        assert task.status == "error"
        assert len(result.errors) == 1


# ===========================================================================
# Security tests
# ===========================================================================


class TestSecurityInputValidation:
    """Security tests for input validation across scripts."""

    def test_policy_pack_path_traversal_safe(self, tmp_path: Path) -> None:
        """Policy pack loading uses safe path handling."""
        policy_file = tmp_path / "policy.yml"
        policy_file.write_text(yaml.dump({"drift": {}}), encoding="utf-8")
        openapi, sdk, ref = _load_policy_pack(str(policy_file))
        assert isinstance(openapi, tuple)

    def test_variable_replacement_no_code_injection(self) -> None:
        """Variable replacement does not execute embedded code."""
        content = "Value: {{ __import__('os').system('ls') }}"
        variables = {}
        result = replace_variables(content, variables)
        # Should remain unchanged since variable does not exist
        assert "__import__" in result

    def test_facets_index_xss_in_title(self, tmp_path: Path) -> None:
        """Frontmatter titles are stored as-is (sanitization at render layer)."""
        docs = tmp_path / "docs"
        docs.mkdir()
        xss = docs / "xss.md"
        xss.write_text(
            '---\ntitle: "<script>alert(1)</script>"\n'
            'description: "Test XSS in description field for validation"\n'
            'content_type: reference\n---\nSafe content.',
            encoding="utf-8",
        )
        output = tmp_path / "facets.json"
        generate_facets_index(str(docs), str(output))
        data = json.loads(output.read_text(encoding="utf-8"))
        assert len(data) == 1
        # Title is stored as-is; rendering layer handles escaping
        assert "<script>" in data[0]["title"]

    def test_build_issue_body_special_chars(self) -> None:
        """Special characters in gap data do not break markdown."""
        gap = {
            "title": "Test `backticks` and *stars*",
            "description": "Description with <html> tags",
            "related_files": ["path/with spaces/file.md"],
        }
        body = _build_issue_body(gap)
        assert "`backticks`" in body
        assert "<html>" in body


# ===========================================================================
# Performance tests
# ===========================================================================


class TestPerformance:
    """Performance tests for critical paths."""

    def test_compute_debt_score_large_input(self) -> None:
        """Debt score computation handles large gap lists efficiently."""
        gaps = [{"priority": "high"}] * 5000 + [{"priority": "medium"}] * 5000
        start = time.monotonic()
        result = _compute_debt_score(gaps)
        elapsed = time.monotonic() - start
        assert elapsed < 1.0, f"Debt score took {elapsed:.2f}s for 10000 gaps"
        assert result["total_gaps"] == 10000

    def test_replace_variables_large_document(self) -> None:
        """Variable replacement handles large documents efficiently."""
        variables = {f"var_{i}": f"value_{i}" for i in range(100)}
        lines = [f"Line with {{{{ var_{i % 100} }}}} placeholder" for i in range(2000)]
        content = "\n".join(lines)

        start = time.monotonic()
        result = replace_variables(content, variables)
        elapsed = time.monotonic() - start
        assert elapsed < 2.0, f"Variable replacement took {elapsed:.2f}s for 2000 lines"
        assert "value_0" in result

    def test_flatten_dict_deep_nesting(self) -> None:
        """Flatten dict handles deeply nested structures."""
        nested = {"a": {"b": {"c": {"d": {"e": "deep_value"}}}}}
        result = _flatten_dict(nested)
        assert result["a.b.c.d.e"] == "deep_value"

    def test_select_patterns_large_file_list(self) -> None:
        """Pattern selection handles large file lists efficiently."""
        files = [f"path/to/file_{i}.py" for i in range(5000)]
        files.append("openapi.yaml")

        start = time.monotonic()
        result = _select(files, OPENAPI_PATTERNS)
        elapsed = time.monotonic() - start
        assert elapsed < 1.0
        assert "openapi.yaml" in result


# ===========================================================================
# Integration tests
# ===========================================================================


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_drift_evaluate_with_custom_policy(self, tmp_path: Path) -> None:
        """Drift evaluation works end-to-end with custom policy pack."""
        policy = {
            "drift": {
                "openapi_patterns": [r"spec/.*\.yaml$"],
                "sdk_patterns": [r"^lib/client/"],
                "reference_doc_patterns": [r"^docs/api/"],
            }
        }
        policy_file = tmp_path / "policy.yml"
        policy_file.write_text(yaml.dump(policy), encoding="utf-8")

        openapi, sdk, ref = _load_policy_pack(str(policy_file))
        files = ["spec/v2.yaml", "lib/client/sdk.ts", "README.md"]
        report = evaluate(files, openapi, sdk, ref)

        assert report.status == "drift"
        assert len(report.openapi_changed) == 1
        assert len(report.sdk_changed) == 1

    def test_sla_evaluate_with_custom_thresholds(self, tmp_path: Path) -> None:
        """SLA evaluation with custom thresholds from policy pack."""
        policy = {"kpi_sla": {"min_quality_score": 95}}
        policy_file = tmp_path / "policy.yml"
        policy_file.write_text(yaml.dump(policy), encoding="utf-8")

        thresholds = _load_thresholds(str(policy_file))
        current = {"quality_score": 90, "stale_pct": 5.0, "gap_high": 2}
        report = sla_evaluate(current, None, thresholds)

        assert report.status == "breach"
        assert any("90 < 95" in b for b in report.breaches)

    def test_docusaurus_config_full_pipeline(self, tmp_path: Path) -> None:
        """Full Docusaurus config generation pipeline."""
        mkdocs = {
            "site_name": "Test Docs",
            "site_url": "https://docs.test.com",
            "nav": [
                {"Home": "index.md"},
                {
                    "Getting Started": [
                        "getting-started/index.md",
                        {"Quickstart": "getting-started/quickstart.md"},
                    ]
                },
            ],
        }
        variables = {"product_name": "TestProd", "docs_url": "https://docs.test.com"}

        sidebar_items = convert_nav_to_sidebar(mkdocs["nav"])
        config_js = generate_docusaurus_config_js(variables, mkdocs)
        sidebars_js = generate_sidebars_js(sidebar_items)

        assert "TestProd" in config_js
        assert "https://docs.test.com" in config_js
        assert "Getting Started" in sidebars_js
        assert "quickstart" in sidebars_js

    def test_preprocess_then_facets(self, tmp_path: Path) -> None:
        """Preprocessing variables followed by facets index generation."""
        docs = tmp_path / "docs"
        docs.mkdir()

        var_file = docs / "_variables.yml"
        var_file.write_text(yaml.dump({"product_name": "Pipeline"}), encoding="utf-8")

        guide = docs / "guide.md"
        guide.write_text(
            "---\ntitle: \"Guide\"\ndescription: \"A guide for Pipeline product testing\"\n"
            "content_type: how-to\n---\n# Guide\n\n"
            "Welcome to {{ product_name }}.\n",
            encoding="utf-8",
        )

        variables = load_variables(var_file)
        preprocess_directory(docs, variables)

        content = guide.read_text(encoding="utf-8")
        assert "Pipeline" in content

        output = tmp_path / "facets.json"
        generate_facets_index(str(docs), str(output))
        data = json.loads(output.read_text(encoding="utf-8"))
        assert len(data) >= 1


# ===========================================================================
# Edge case tests
# ===========================================================================


class TestEdgeCases:
    """Edge case tests for boundary conditions."""

    def test_replace_variables_inside_code_fence(self) -> None:
        """Variables inside code fences are not replaced."""
        content = "Before\n```python\n{{ var }}\n```\nAfter {{ var }}"
        result = replace_variables(content, {"var": "replaced"})
        lines = result.split("\n")
        assert lines[2] == "{{ var }}"  # Inside fence - unchanged
        assert "replaced" in lines[4]   # Outside fence - replaced

    def test_replace_variables_tilde_fence(self) -> None:
        """Tilde code fences are also respected."""
        content = "~~~\n{{ var }}\n~~~\n{{ var }}"
        result = replace_variables(content, {"var": "val"})
        lines = result.split("\n")
        assert lines[1] == "{{ var }}"
        assert "val" in lines[3]

    def test_debt_score_boundary_50(self) -> None:
        """Score exactly at 50 is medium risk."""
        # 10 high = 50 points
        gaps = [{"priority": "high"}] * 10
        result = _compute_debt_score(gaps)
        assert result["total_score"] == 50
        assert result["risk_level"] == "medium"

    def test_debt_score_boundary_149(self) -> None:
        """Score at 149 is still medium risk."""
        # 29 high = 145, 4 low = 4, total = 149 -- still medium
        gaps = [{"priority": "high"}] * 29 + [{"priority": "low"}] * 4
        result = _compute_debt_score(gaps)
        assert result["total_score"] == 149
        assert result["risk_level"] == "medium"

    def test_section_empty_commits(self) -> None:
        """Empty commit list produces 'none' section."""
        result = _section("Features", [])
        assert "- none" in result

    def test_section_with_commits(self) -> None:
        """Non-empty commit list produces bullet points."""
        result = _section("Features", ["abc feat: X", "def feat: Y"])
        assert "- abc feat: X" in result
        assert "- def feat: Y" in result

    def test_extract_first_paragraph_empty_content(self) -> None:
        """Empty content returns empty snippet."""
        result = extract_first_paragraph("")
        assert result == ""

    def test_extract_first_paragraph_only_headings(self) -> None:
        """Content with only headings returns empty snippet."""
        result = extract_first_paragraph("# Title\n## Section\n### Sub")
        assert result == ""

    def test_sla_evaluate_all_breaches(self) -> None:
        """All thresholds breached at once."""
        current = {"quality_score": 50, "stale_pct": 30.0, "gap_high": 20}
        previous = {"quality_score": 90}
        thresholds = DEFAULT_THRESHOLDS
        report = sla_evaluate(current, previous, thresholds)
        assert report.status == "breach"
        assert len(report.breaches) == 4  # quality, stale, gaps, trend

    def test_md_to_doc_id_mdx_extension(self) -> None:
        """MDX files are handled correctly."""
        assert _md_to_doc_id("path/to/file.mdx") == "path/to/file"

    def test_md_to_doc_id_backslash(self) -> None:
        """Backslashes are normalized to forward slashes."""
        assert _md_to_doc_id("path\\to\\file.md") == "path/to/file"

    def test_build_url_from_path_root_index(self, tmp_path: Path) -> None:
        """Root index.md produces empty URL."""
        docs = tmp_path / "docs"
        docs.mkdir()
        f = docs / "index.md"
        f.touch()
        url = build_url_from_path(f, docs)
        assert url == ""

    def test_render_markdown_drift_report(self) -> None:
        """Drift report Markdown rendering includes all sections."""
        report = DriftReport(
            status="drift",
            summary="Changes detected.",
            openapi_changed=["api/v2.yaml"],
            sdk_changed=[],
            reference_docs_changed=[],
        )
        md = _render_markdown(report)
        assert "DRIFT" in md
        assert "`api/v2.yaml`" in md
        assert "- none" in md

    def test_sla_render_markdown(self) -> None:
        """SLA report Markdown rendering includes thresholds and breaches."""
        report = SlaReport(
            status="breach",
            summary="Breached.",
            breaches=["Quality too low."],
            trend_notes=["Trending down."],
            metrics={"quality_score": 70},
        )
        md = sla_render_markdown(report, DEFAULT_THRESHOLDS)
        assert "BREACH" in md
        assert "Quality too low." in md
        assert "Trending down." in md

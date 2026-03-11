"""Tests for remaining scripts with 0% or low coverage.

Covers:
- doc_layers_validator.py
- generate_badge.py
- generate_facets_index.py
- gap_detector.py (_compute_debt_score, _build_issue_body)
- generate_release_docs_pack.py (_section, build_release_pack)
- validate_pr_dod.py
- preprocess_variables.py
- check_docs_contract.py (evaluate_contract, _load_policy_pack, _matches_any)
- check_api_sdk_drift.py (evaluate)
- evaluate_kpi_sla.py (evaluate)
- generate_kpi_wall.py (build_metrics, render_markdown)
"""

from __future__ import annotations

import json
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

import pytest
import yaml


# ---------------------------------------------------------------------------
# doc_layers_validator
# ---------------------------------------------------------------------------


class TestDocLayersValidator:
    """Tests for DocLayersValidator."""

    def _write_md(self, path: Path, frontmatter: str, body: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")
        return path

    def test_detects_code_blocks_in_concepts(self, tmp_path: Path) -> None:
        from scripts.doc_layers_validator import DocLayersValidator

        docs = tmp_path / "docs"
        docs.mkdir()
        self._write_md(
            docs / "test.md",
            'title: "Test"\ncontent_type: concept',
            "# Test\n\nRun the following command:\n```bash\necho hi\n```\n",
        )
        validator = DocLayersValidator(docs_dir=str(docs))
        violations = validator.detect_layer_violations()
        assert len(violations) >= 1

    def test_no_violations_for_valid_reference(self, tmp_path: Path) -> None:
        from scripts.doc_layers_validator import DocLayersValidator

        docs = tmp_path / "docs"
        docs.mkdir()
        self._write_md(
            docs / "api.md",
            'title: "API"\ncontent_type: reference',
            "# API\n\nThe endpoint returns a JSON object.\n\n```json\n{}\n```\n",
        )
        validator = DocLayersValidator(docs_dir=str(docs))
        violations = validator.detect_layer_violations()
        # Reference with code blocks should not trigger violations
        assert not any(v["content_type"] == "reference" for v in violations)

    def test_extract_content_type(self, tmp_path: Path) -> None:
        from scripts.doc_layers_validator import DocLayersValidator

        validator = DocLayersValidator()
        text = '---\ncontent_type: tutorial\n---\n# Body'
        assert validator.extract_content_type(text) == "tutorial"

    def test_extract_content_type_no_frontmatter(self) -> None:
        from scripts.doc_layers_validator import DocLayersValidator

        validator = DocLayersValidator()
        assert validator.extract_content_type("# No frontmatter") == ""

    def test_generate_report_html(self, tmp_path: Path) -> None:
        from scripts.doc_layers_validator import DocLayersValidator

        docs = tmp_path / "docs"
        docs.mkdir()
        self._write_md(docs / "test.md", 'title: "T"\ncontent_type: reference', "# T\n\nContent.\n")
        validator = DocLayersValidator(docs_dir=str(docs))
        html = validator.generate_report()
        assert "<!DOCTYPE html>" in html
        assert "Documentation Layers Validation" in html

    def test_save_report(self, tmp_path: Path) -> None:
        from scripts.doc_layers_validator import DocLayersValidator

        docs = tmp_path / "docs"
        docs.mkdir()
        self._write_md(docs / "test.md", 'title: "T"\ncontent_type: reference', "# T\n\nContent.\n")
        validator = DocLayersValidator(docs_dir=str(docs))
        output = str(tmp_path / "report.html")
        validator.save_report(output)
        assert Path(output).exists()

    def test_policy_pack_required_layers(self, tmp_path: Path) -> None:
        from scripts.doc_layers_validator import DocLayersValidator

        docs = tmp_path / "docs"
        docs.mkdir()
        self._write_md(
            docs / "billing-concept.md",
            'title: "Billing"\ncontent_type: concept\nfeature_id: billing',
            "# Billing\n\nConcept text.\n",
        )
        self._write_md(
            docs / "billing-how-to.md",
            'title: "Billing task"\ncontent_type: how-to\nfeature_id: billing',
            "# Billing Task\n\nSteps.\n",
        )
        policy = tmp_path / "policy.yml"
        policy.write_text(
            "doc_layers:\n  required_layers:\n    - concept\n    - how-to\n    - reference\n",
            encoding="utf-8",
        )

        validator = DocLayersValidator(docs_dir=str(docs), policy_pack_path=str(policy))
        violations = validator.detect_layer_violations()
        assert any("Missing required layers: reference" in v.get("violation", "") for v in violations)


# ---------------------------------------------------------------------------
# generate_badge
# ---------------------------------------------------------------------------


class TestGenerateBadge:
    """Tests for generate_badge.py."""

    def test_color_for_score(self) -> None:
        from scripts.generate_badge import _color_for_score

        assert _color_for_score(95) == "#4c1"
        assert _color_for_score(85) == "#97ca00"
        assert _color_for_score(75) == "#a3c51c"
        assert _color_for_score(65) == "#dfb317"
        assert _color_for_score(50) == "#fe7d37"
        assert _color_for_score(30) == "#e05d44"

    def test_make_badge_svg(self) -> None:
        from scripts.generate_badge import _make_badge_svg

        svg = _make_badge_svg("test label", "100", "#4c1")
        assert "<svg" in svg
        assert "test label" in svg
        assert "100" in svg

    def test_generate_badges(self, tmp_path: Path) -> None:
        from scripts.generate_badge import generate_badges

        kpi = {
            "quality_score": 85,
            "metadata_completeness_pct": 90.0,
            "stale_pct": 10.0,
            "gap_high": 2,
        }
        json_path = tmp_path / "kpi.json"
        json_path.write_text(json.dumps(kpi), encoding="utf-8")
        output_dir = tmp_path / "badges"
        badges = generate_badges(json_path, output_dir)
        assert len(badges) == 5
        for badge_path in badges:
            assert Path(badge_path).exists()
            assert Path(badge_path).read_text().startswith("<svg")


# ---------------------------------------------------------------------------
# generate_facets_index
# ---------------------------------------------------------------------------


class TestGenerateFacetsIndex:
    """Tests for generate_facets_index.py."""

    def _write_md(self, path: Path, frontmatter: str, body: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")
        return path

    def test_generates_index(self, tmp_path: Path) -> None:
        from scripts.generate_facets_index import generate_facets_index

        docs = tmp_path / "docs"
        docs.mkdir()
        self._write_md(docs / "test.md", 'title: "Test"\ndescription: "Desc"\ncontent_type: reference', "# Test\n\nBody.")
        output = str(tmp_path / "index.json")
        result = generate_facets_index(str(docs), output)
        assert result is True
        data = json.loads(Path(output).read_text())
        assert len(data) == 1
        assert data[0]["title"] == "Test"

    def test_skips_removed_documents(self, tmp_path: Path) -> None:
        from scripts.generate_facets_index import generate_facets_index

        docs = tmp_path / "docs"
        docs.mkdir()
        self._write_md(docs / "gone.md", 'title: "Gone"\nstatus: removed', "# Gone")
        output = str(tmp_path / "index.json")
        generate_facets_index(str(docs), output)
        data = json.loads(Path(output).read_text())
        assert len(data) == 0

    def test_marks_deprecated_documents(self, tmp_path: Path) -> None:
        from scripts.generate_facets_index import generate_facets_index

        docs = tmp_path / "docs"
        docs.mkdir()
        self._write_md(docs / "old.md", 'title: "Old"\nstatus: deprecated\nreplacement_url: "/new"', "# Old\n\nBody.")
        output = str(tmp_path / "index.json")
        generate_facets_index(str(docs), output)
        data = json.loads(Path(output).read_text())
        assert "[DEPRECATED]" in data[0]["title"]
        assert data[0]["replacement_url"] == "/new"

    def test_extract_first_paragraph(self) -> None:
        from scripts.generate_facets_index import extract_first_paragraph

        content = "# Title\nThis is the first paragraph.\n\nSecond paragraph."
        result = extract_first_paragraph(content)
        assert "first paragraph" in result

    def test_returns_false_for_missing_dir(self, tmp_path: Path) -> None:
        from scripts.generate_facets_index import generate_facets_index

        result = generate_facets_index(str(tmp_path / "nonexistent"), str(tmp_path / "out.json"))
        assert result is False

    def test_skips_underscore_files(self, tmp_path: Path) -> None:
        from scripts.generate_facets_index import generate_facets_index

        docs = tmp_path / "docs"
        docs.mkdir()
        self._write_md(docs / "_private.md", 'title: "Private"', "# Private")
        self._write_md(docs / "public.md", 'title: "Public"\ndescription: "Desc"', "# Public\n\nBody.")
        output = str(tmp_path / "index.json")
        generate_facets_index(str(docs), output)
        data = json.loads(Path(output).read_text())
        assert len(data) == 1
        assert data[0]["title"] == "Public"


# ---------------------------------------------------------------------------
# gap_detector (_compute_debt_score, _build_issue_body)
# ---------------------------------------------------------------------------


class TestGapDetector:
    """Tests for gap_detector helper functions."""

    def test_compute_debt_score_low_risk(self) -> None:
        from scripts.gap_detector import _compute_debt_score

        gaps = [{"priority": "low"}, {"priority": "low"}]
        score = _compute_debt_score(gaps)
        assert score["risk_level"] == "low"
        assert score["total_score"] == 2

    def test_compute_debt_score_medium_risk(self) -> None:
        from scripts.gap_detector import _compute_debt_score

        gaps = [{"priority": "high"}] * 10 + [{"priority": "medium"}] * 5
        score = _compute_debt_score(gaps)
        assert score["risk_level"] == "medium"

    def test_compute_debt_score_high_risk(self) -> None:
        from scripts.gap_detector import _compute_debt_score

        gaps = [{"priority": "high"}] * 50
        score = _compute_debt_score(gaps)
        assert score["risk_level"] == "high"

    def test_compute_debt_score_unknown_priority(self) -> None:
        from scripts.gap_detector import _compute_debt_score

        gaps = [{"priority": "critical"}]
        score = _compute_debt_score(gaps)
        assert score["by_priority"]["low"] == 1

    def test_build_issue_body(self) -> None:
        from scripts.gap_detector import _build_issue_body

        gap: dict[str, Any] = {
            "title": "Missing docs",
            "source": "code",
            "category": "api_endpoint",
            "priority": "high",
            "description": "Endpoint /users has no docs",
            "action_required": "Create reference page",
            "related_files": ["src/routes/users.ts"],
        }
        body = _build_issue_body(gap)
        assert "Missing docs" in body
        assert "src/routes/users.ts" in body
        assert "## Documentation Gap Detected" in body

    def test_build_issue_body_without_files(self) -> None:
        from scripts.gap_detector import _build_issue_body

        gap: dict[str, Any] = {"title": "Gap", "related_files": []}
        body = _build_issue_body(gap)
        assert "N/A" in body


# ---------------------------------------------------------------------------
# generate_release_docs_pack
# ---------------------------------------------------------------------------


class TestReleaseDocsPack:
    """Tests for generate_release_docs_pack helper functions."""

    def test_section_with_commits(self) -> None:
        from scripts.generate_release_docs_pack import _section

        result = _section("Features", ["abc1234 feat: add login", "def5678 feat: add logout"])
        assert "## Features" in result
        assert "abc1234" in result

    def test_section_without_commits(self) -> None:
        from scripts.generate_release_docs_pack import _section

        result = _section("Features", [])
        assert "- none" in result


# ---------------------------------------------------------------------------
# validate_pr_dod
# ---------------------------------------------------------------------------


class TestValidatePrDod:
    """Tests for validate_pr_dod."""

    def test_passes_with_updated_checkbox(self) -> None:
        from scripts.validate_pr_dod import validate_dod

        body = "- [x] I updated documentation affected by this PR."
        ok, message = validate_dod(body)
        assert ok is True

    def test_passes_with_not_needed_and_reason(self) -> None:
        from scripts.validate_pr_dod import validate_dod

        body = (
            "- [x] Documentation updates are not needed.\n"
            "Reason: Internal refactoring only, no public API changes.\n"
        )
        ok, message = validate_dod(body)
        assert ok is True

    def test_fails_with_no_checkbox(self) -> None:
        from scripts.validate_pr_dod import validate_dod

        ok, message = validate_dod("Some PR body without checkboxes.")
        assert ok is False
        assert "incomplete" in message

    def test_fails_with_both_checkboxes(self) -> None:
        from scripts.validate_pr_dod import validate_dod

        body = (
            "- [x] I updated documentation affected by this PR.\n"
            "- [x] Documentation updates are not needed.\n"
        )
        ok, message = validate_dod(body)
        assert ok is False
        assert "invalid" in message

    def test_fails_with_not_needed_but_no_reason(self) -> None:
        from scripts.validate_pr_dod import validate_dod

        body = "- [x] Documentation updates are not needed.\n"
        ok, message = validate_dod(body)
        assert ok is False
        assert "provide a reason" in message

    def test_fails_with_short_reason(self) -> None:
        from scripts.validate_pr_dod import validate_dod

        body = "- [x] Documentation updates are not needed.\nReason: N/A\n"
        ok, message = validate_dod(body)
        assert ok is False
        assert "too short" in message

    def test_load_body(self, tmp_path: Path) -> None:
        from scripts.validate_pr_dod import _load_body

        event = tmp_path / "event.json"
        event.write_text(
            json.dumps({"pull_request": {"body": "test body"}}),
            encoding="utf-8",
        )
        assert _load_body(event) == "test body"

    def test_load_body_missing_pr(self, tmp_path: Path) -> None:
        from scripts.validate_pr_dod import _load_body

        event = tmp_path / "event.json"
        event.write_text(json.dumps({}), encoding="utf-8")
        assert _load_body(event) == ""


# ---------------------------------------------------------------------------
# preprocess_variables
# ---------------------------------------------------------------------------


class TestPreprocessVariables:
    """Tests for preprocess_variables.py."""

    def test_flatten_dict(self) -> None:
        from scripts.preprocess_variables import _flatten_dict

        result = _flatten_dict({"a": {"b": "c", "d": "e"}, "f": "g"})
        assert result == {"a.b": "c", "a.d": "e", "f": "g"}

    def test_replace_variables(self) -> None:
        from scripts.preprocess_variables import replace_variables

        content = "Port is {{ default_port }} and name is {{ product_name }}."
        variables: dict[str, Any] = {"default_port": 5678, "product_name": "MyApp"}
        result = replace_variables(content, variables)
        assert "5678" in result
        assert "MyApp" in result

    def test_replace_nested_variables(self) -> None:
        from scripts.preprocess_variables import replace_variables

        content = "Set {{ env_vars.port }} to configure."
        variables: dict[str, Any] = {"env_vars": {"port": "APP_PORT"}}
        result = replace_variables(content, variables)
        assert "APP_PORT" in result

    def test_does_not_replace_in_code_blocks(self) -> None:
        from scripts.preprocess_variables import replace_variables

        content = "```\n{{ product_name }}\n```"
        variables: dict[str, Any] = {"product_name": "MyApp"}
        result = replace_variables(content, variables)
        assert "{{ product_name }}" in result

    def test_preserves_unknown_variables(self) -> None:
        from scripts.preprocess_variables import replace_variables

        content = "{{ unknown_var }}"
        result = replace_variables(content, {})
        assert "{{ unknown_var }}" in result

    def test_load_variables(self, tmp_path: Path) -> None:
        from scripts.preprocess_variables import load_variables

        var_file = tmp_path / "vars.yml"
        var_file.write_text("port: 5678\nname: Test", encoding="utf-8")
        result = load_variables(var_file)
        assert result["port"] == 5678

    def test_load_variables_missing_file(self, tmp_path: Path) -> None:
        from scripts.preprocess_variables import load_variables

        result = load_variables(tmp_path / "nonexistent.yml")
        assert result == {}

    def test_preprocess_directory(self, tmp_path: Path) -> None:
        from scripts.preprocess_variables import preprocess_directory

        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "test.md").write_text("Port: {{ port }}", encoding="utf-8")
        out = tmp_path / "output"
        processed = preprocess_directory(docs, {"port": 8080}, out)
        assert len(processed) == 1
        content = processed[0].read_text()
        assert "8080" in content


# ---------------------------------------------------------------------------
# check_docs_contract
# ---------------------------------------------------------------------------


class TestCheckDocsContract:
    """Tests for check_docs_contract.py."""

    def test_evaluate_contract_blocked(self) -> None:
        from scripts.check_docs_contract import evaluate_contract

        files = ["api/openapi.yaml", "src/utils.ts"]
        result = evaluate_contract(files)
        assert result["blocked"] is True
        assert len(result["interface_changed"]) >= 1
        assert len(result["docs_changed"]) == 0

    def test_evaluate_contract_not_blocked(self) -> None:
        from scripts.check_docs_contract import evaluate_contract

        files = ["api/openapi.yaml", "docs/reference/api.md"]
        result = evaluate_contract(files)
        assert result["blocked"] is False

    def test_evaluate_contract_no_interface_changes(self) -> None:
        from scripts.check_docs_contract import evaluate_contract

        files = ["README.md", "package.json"]
        result = evaluate_contract(files)
        assert result["blocked"] is False

    def test_matches_any(self) -> None:
        from scripts.check_docs_contract import _matches_any

        assert _matches_any("api/openapi.yaml", (r"^api/",)) is True
        assert _matches_any("src/index.ts", (r"^api/",)) is False

    def test_load_policy_pack_default(self) -> None:
        from scripts.check_docs_contract import _load_policy_pack

        interface_patterns, doc_patterns = _load_policy_pack(None)
        assert len(interface_patterns) > 0
        assert len(doc_patterns) > 0

    def test_load_policy_pack_custom(self, tmp_path: Path) -> None:
        from scripts.check_docs_contract import _load_policy_pack

        policy = tmp_path / "policy.yml"
        policy.write_text(
            yaml.dump({
                "docs_contract": {
                    "interface_patterns": ["^custom/"],
                    "doc_patterns": ["^custom-docs/"],
                },
            }),
            encoding="utf-8",
        )
        interface_patterns, doc_patterns = _load_policy_pack(str(policy))
        assert interface_patterns == ("^custom/",)
        assert doc_patterns == ("^custom-docs/",)

    def test_load_policy_pack_invalid(self, tmp_path: Path) -> None:
        from scripts.check_docs_contract import _load_policy_pack

        policy = tmp_path / "bad.yml"
        policy.write_text("- list item", encoding="utf-8")
        with pytest.raises(ValueError, match="must be a mapping"):
            _load_policy_pack(str(policy))


# ---------------------------------------------------------------------------
# check_api_sdk_drift
# ---------------------------------------------------------------------------


class TestCheckApiSdkDrift:
    """Tests for check_api_sdk_drift.py."""

    def test_evaluate_ok_when_no_drift(self) -> None:
        from scripts.check_api_sdk_drift import evaluate

        report = evaluate(["src/index.ts", "tests/test_foo.py"])
        assert report.status == "ok"

    def test_evaluate_drift_when_api_changed_without_docs(self) -> None:
        from scripts.check_api_sdk_drift import evaluate

        report = evaluate(["api/openapi.yaml", "sdk/client.ts"])
        assert report.status == "drift"
        assert len(report.openapi_changed) >= 1
        assert len(report.sdk_changed) >= 1

    def test_evaluate_ok_when_docs_updated_too(self) -> None:
        from scripts.check_api_sdk_drift import evaluate

        report = evaluate(["api/openapi.yaml", "docs/reference/api.md"])
        assert report.status == "ok"


# ---------------------------------------------------------------------------
# evaluate_kpi_sla
# ---------------------------------------------------------------------------


class TestEvaluateKpiSla:
    """Tests for evaluate_kpi_sla.py."""

    def test_evaluate_ok(self) -> None:
        from scripts.evaluate_kpi_sla import evaluate

        current = {"quality_score": 90, "stale_pct": 5.0, "gap_high": 2}
        previous = {"quality_score": 88, "stale_pct": 6.0, "gap_high": 3}
        thresholds = {
            "min_quality_score": 80,
            "max_stale_pct": 15.0,
            "max_high_priority_gaps": 10,
            "max_quality_score_drop": 10,
        }
        report = evaluate(current, previous, thresholds)
        assert report.status == "ok"
        assert len(report.breaches) == 0

    def test_evaluate_breach(self) -> None:
        from scripts.evaluate_kpi_sla import evaluate

        current = {"quality_score": 70, "stale_pct": 20.0, "gap_high": 15}
        previous = {"quality_score": 85, "stale_pct": 10.0, "gap_high": 5}
        thresholds = {
            "min_quality_score": 80,
            "max_stale_pct": 15.0,
            "max_high_priority_gaps": 10,
            "max_quality_score_drop": 5,
        }
        report = evaluate(current, previous, thresholds)
        assert report.status == "breach"
        assert len(report.breaches) >= 1


# ---------------------------------------------------------------------------
# generate_kpi_wall
# ---------------------------------------------------------------------------


class TestGenerateKpiWall:
    """Tests for generate_kpi_wall.py."""

    def _setup_kpi_fixture(self, tmp_path: Path) -> tuple[Path, Path]:
        docs = tmp_path / "docs"
        reports = tmp_path / "reports"
        docs.mkdir()
        reports.mkdir()

        (docs / "fresh.md").write_text(
            '---\ntitle: "Fresh"\ndescription: "Fresh document for testing."\ncontent_type: reference\nlast_reviewed: "2026-03-01"\n---\n# Fresh\nContent.\n',
            encoding="utf-8",
        )
        (docs / "stale.md").write_text(
            '---\ntitle: "Stale"\ndescription: "Stale document for testing."\ncontent_type: how-to\nlast_reviewed: "2025-01-01"\n---\n# Stale\nContent.\n',
            encoding="utf-8",
        )
        (reports / "doc_gaps_report.json").write_text(
            json.dumps({"gaps": [{"priority": "high"}, {"priority": "low"}]}),
            encoding="utf-8",
        )
        return docs, reports

    def test_build_metrics(self, tmp_path: Path) -> None:
        from scripts.generate_kpi_wall import build_metrics

        docs, reports = self._setup_kpi_fixture(tmp_path)
        metrics = build_metrics(
            docs_dir=docs,
            reports_dir=reports,
            stale_days=90,
            generated_at="2026-03-03T00:00:00Z",
            reference_date=date(2026, 3, 3),
        )
        assert metrics.total_docs == 2
        assert metrics.stale_docs == 1
        assert metrics.gap_total == 2
        assert metrics.gap_high == 1
        assert "stale.md" in metrics.stale_files

    def test_render_markdown(self, tmp_path: Path) -> None:
        from scripts.generate_kpi_wall import build_metrics, render_markdown

        docs, reports = self._setup_kpi_fixture(tmp_path)
        metrics = build_metrics(
            docs_dir=docs,
            reports_dir=reports,
            stale_days=90,
            generated_at="2026-03-03T00:00:00Z",
            reference_date=date(2026, 3, 3),
        )
        md = render_markdown(metrics)
        assert "KPI" in md or "Quality" in md
        assert str(metrics.quality_score) in md

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _base_runtime() -> dict:
    return {
        "api_governance": {"strictness": "standard"},
        "docs_flow": {"mode": "hybrid"},
        "paths": {"docs_root": "docs"},
        "modules": {
            "kpi_sla": True,
            "rag_optimization": True,
            "ontology_graph": True,
            "retrieval_evals": True,
            "terminology_management": True,
        },
        "api_protocols": ["rest", "graphql"],
        "api_protocol_settings": {
            "rest": {"generate_test_assets": False, "upload_test_assets": False},
            "graphql": {"generate_test_assets": False, "upload_test_assets": False},
        },
        "api_first": {"generate_test_assets": False, "upload_test_assets": False},
    }


def test_collect_artifacts_toggles_test_assets_by_runtime(tmp_path: Path) -> None:
    from scripts import run_autopipeline as mod

    runtime = _base_runtime()
    artifacts = mod._collect_artifacts(runtime, tmp_path / "reports", tmp_path, skip_consolidated_report=False)
    titles = {str(a.get("title")) for a in artifacts if isinstance(a, dict)}
    assert "API test cases JSON" not in titles
    assert "Test assets upload report" not in titles

    runtime["api_protocol_settings"]["graphql"]["generate_test_assets"] = True
    runtime["api_protocol_settings"]["graphql"]["upload_test_assets"] = True
    artifacts = mod._collect_artifacts(runtime, tmp_path / "reports", tmp_path, skip_consolidated_report=False)
    titles = {str(a.get("title")) for a in artifacts if isinstance(a, dict)}
    assert "API test cases JSON" in titles
    assert "Test assets upload report" in titles


def test_stage_summary_respects_skip_consolidated_flag(tmp_path: Path) -> None:
    from scripts import run_autopipeline as mod

    runtime = _base_runtime()
    s1 = mod._build_stage_summary(
        runtime=runtime,
        repo_root=tmp_path,
        reports_dir=tmp_path,
        weekly_rc=0,
        strictness="standard",
        skip_consolidated_report=True,
    )
    stages1 = {str(s.get("stage")) for s in s1.get("stages", []) if isinstance(s, dict)}
    assert "consolidated_report" not in stages1
    assert s1.get("skip_consolidated_report") is True

    s2 = mod._build_stage_summary(
        runtime=runtime,
        repo_root=tmp_path,
        reports_dir=tmp_path,
        weekly_rc=0,
        strictness="enterprise-strict",
        skip_consolidated_report=False,
    )
    stages2 = {str(s.get("stage")) for s in s2.get("stages", []) if isinstance(s, dict)}
    assert "consolidated_report" in stages2
    assert s2.get("skip_consolidated_report") is False


def test_output_index_contains_review_links_and_searchability(tmp_path: Path) -> None:
    from scripts import run_autopipeline as mod

    repo = tmp_path / "repo"
    reports = repo / "reports"
    docs = repo / "docs"
    reports.mkdir(parents=True)
    docs.mkdir(parents=True)
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    (docs / "search-faceted.md").write_text("# Search\n", encoding="utf-8")
    (repo / "mkdocs.yml").write_text(
        yaml.safe_dump({"site_url": "https://example.com/docs"}, sort_keys=False),
        encoding="utf-8",
    )

    manifest = {
        "artifacts": [
            {
                "title": "Docs index",
                "category": "docs",
                "path": str((docs / "index.md").resolve()),
                "exists": True,
            },
            {
                "title": "Faceted search page",
                "category": "search",
                "path": str((docs / "search-faceted.md").resolve()),
                "exists": True,
            },
        ],
        "rag_metadata": {"retrieval_records": 10, "graph_nodes": 5, "graph_edges": 8},
    }
    (reports / "review_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    review_manifest_md = reports / "REVIEW_MANIFEST.md"
    review_manifest_md.write_text("# Review\n", encoding="utf-8")
    stage_summary = {"weekly_rc": 0, "strictness": "standard", "skip_consolidated_report": True, "stages": []}

    out = mod._write_output_index(
        reports_dir=reports,
        runtime_path=repo / "runtime.yml",
        stage_summary=stage_summary,
        review_manifest=review_manifest_md,
        repo_root=repo,
    )
    text = out.read_text(encoding="utf-8")
    assert "Browse/Searchability" in text
    assert "Public URL: https://example.com/docs/index/" in text
    assert "Public URL: https://example.com/docs/search-faceted/" in text


def test_output_index_strips_en_suffix_from_site_url(tmp_path: Path) -> None:
    from scripts import run_autopipeline as mod

    repo = tmp_path / "repo"
    reports = repo / "reports"
    docs = repo / "docs"
    reports.mkdir(parents=True)
    docs.mkdir(parents=True)
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    (repo / "mkdocs.yml").write_text(
        yaml.safe_dump({"site_url": "https://example.com/docs/en"}, sort_keys=False),
        encoding="utf-8",
    )

    manifest = {
        "artifacts": [
            {
                "title": "Docs index",
                "category": "docs",
                "path": str((docs / "index.md").resolve()),
                "exists": True,
            }
        ],
        "rag_metadata": {},
    }
    (reports / "review_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    review_manifest_md = reports / "REVIEW_MANIFEST.md"
    review_manifest_md.write_text("# Review\n", encoding="utf-8")
    stage_summary = {"weekly_rc": 0, "strictness": "standard", "skip_consolidated_report": True, "stages": []}

    out = mod._write_output_index(
        reports_dir=reports,
        runtime_path=repo / "runtime.yml",
        stage_summary=stage_summary,
        review_manifest=review_manifest_md,
        repo_root=repo,
    )
    text = out.read_text(encoding="utf-8")
    assert "Public URL: https://example.com/docs/index/" in text
    assert "https://example.com/docs/en/index/" not in text


def test_policy_pack_fallback_uses_existing_pack(tmp_path: Path) -> None:
    from scripts import run_weekly_gap_batch as mod

    docsops = tmp_path / "docsops"
    packs = docsops / "policy_packs"
    packs.mkdir(parents=True)
    (packs / "api-first.yml").write_text("kpi_sla: {}\n", encoding="utf-8")
    runtime = {}
    resolved = mod._resolve_policy_pack(docsops, runtime)
    assert resolved.name == "api-first.yml"

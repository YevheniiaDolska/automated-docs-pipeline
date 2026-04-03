from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _seed_demo(root: Path) -> None:
    from scripts import build_acme_demo_site as mod

    docs = root / "docs"
    nav = []
    for rel in mod.REQUIRED_PAGES:
        p = docs / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            "---\n"
            f"title: {rel}\n"
            "description: Adequate description for demo docs pages.\n"
            "content_type: reference\n"
            "product: both\n"
            "tags:\n"
            "  - API\n"
            "---\n\n"
            "Powered by VeriDoc\n\n"
            "Paragraph one.\n\n"
            "[Go](../index.md)\n",
            encoding="utf-8",
        )
        nav.append({rel: rel})
    (root / "mkdocs.yml").write_text(yaml.safe_dump({"nav": nav}, sort_keys=False), encoding="utf-8")


def test_build_demo_rag_assets_and_slug_and_first_paragraph(tmp_path: Path) -> None:
    from scripts import build_acme_demo_site as mod

    _seed_demo(tmp_path)
    mod._build_demo_rag_assets(tmp_path)

    assets = tmp_path / "docs" / "assets"
    idx = json.loads((assets / "knowledge-retrieval-index.json").read_text(encoding="utf-8"))
    graph = json.loads((assets / "knowledge-graph.jsonld").read_text(encoding="utf-8"))
    facets = json.loads((assets / "facets-index.json").read_text(encoding="utf-8"))

    assert isinstance(idx.get("records"), list) and len(idx["records"]) > 0
    assert isinstance(graph.get("nodes"), list) and len(graph["nodes"]) > 0
    assert isinstance(facets.get("records"), list) and len(facets["records"]) > 0

    assert mod._slug("A B/C") == "a-b-c"
    assert mod._first_paragraph("# H\n\nFirst para here.\n\nSecond") == "First para here."


def test_generate_embeddings_sync_assets_and_kpi_refresh(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import build_acme_demo_site as mod

    _seed_demo(tmp_path)
    reports = tmp_path / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "REVIEW_MANIFEST.md").write_text("# Review\n", encoding="utf-8")

    # Embeddings disabled path
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    mod._generate_embeddings_if_available(tmp_path)

    # Embeddings enabled path (mock command runner)
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    calls: list[list[str]] = []
    monkeypatch.setattr(mod, "_run_allow_fail", lambda cmd, cwd, label: calls.append(cmd) or 0)
    # Need index file for embed step
    assets = tmp_path / "docs" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "knowledge-retrieval-index.json").write_text('{"records": []}', encoding="utf-8")
    mod._generate_embeddings_if_available(tmp_path)
    assert any("generate_embeddings.py" in " ".join(c) for c in calls)

    # sync assets and KPI score refresh
    monkeypatch.setattr(mod, "_compute_demo_kpi", lambda out, rep: {"quality_score": 97, "total_docs": 20, "stale_docs": 0, "gap_total": 0})
    mod._sync_pipeline_assets(tmp_path, reports)

    evidence = (tmp_path / "docs" / "quality" / "evidence.md").read_text(encoding="utf-8")
    assert "Powered by VeriDoc" in evidence
    assert (tmp_path / "docs" / "quality" / "review-manifest.md").exists()


def test_validate_built_site_additional_failures(tmp_path: Path) -> None:
    from scripts import build_acme_demo_site as mod

    site = tmp_path / "site"
    (site / "reference" / "rest-api").mkdir(parents=True, exist_ok=True)
    (site / "reference" / "swagger-test.html").parent.mkdir(parents=True, exist_ok=True)

    (site / "reference" / "rest-api" / "index.html").write_text('../swagger-test.html', encoding="utf-8")
    (site / "reference" / "swagger-test.html").write_text("ok", encoding="utf-8")

    # missing content.code.copy
    with pytest.raises(ValueError):
        mod._validate_built_site_contract(tmp_path)

    (site / "reference" / "rest-api" / "index.html").write_text('../swagger-test.html "content.code.copy"', encoding="utf-8")
    # missing clipboard runtime
    with pytest.raises(ValueError):
        mod._validate_built_site_contract(tmp_path)

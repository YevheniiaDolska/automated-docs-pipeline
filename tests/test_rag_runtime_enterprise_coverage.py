from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
PKG_CORE = ROOT / "packages" / "core"
if str(PKG_CORE) not in sys.path:
    sys.path.insert(0, str(PKG_CORE))


def test_load_ask_ai_config_defaults_and_invalid_shape(tmp_path: Path) -> None:
    from gitspeak_core.api import rag_runtime as mod

    cfg = mod.load_ask_ai_config(tmp_path)
    assert cfg["enabled"] is False
    assert cfg["knowledge_index_path"].endswith("knowledge-retrieval-index.json")

    cfg_path = tmp_path / "config" / "ask-ai.yml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text("- not-a-dict\n", encoding="utf-8")
    assert mod.load_ask_ai_config(tmp_path) == {}


def test_load_ask_ai_config_parse_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from types import SimpleNamespace

    from gitspeak_core.api import rag_runtime as mod

    cfg_path = tmp_path / "config" / "ask-ai.yml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text("enabled: true\n", encoding="utf-8")
    fake_yaml = SimpleNamespace(safe_load=lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("bad")))
    monkeypatch.setitem(sys.modules, "yaml", fake_yaml)
    assert mod.load_ask_ai_config(tmp_path) == {}


def test_load_retrieval_index_variants(tmp_path: Path) -> None:
    from gitspeak_core.api import rag_runtime as mod

    cfg = {"knowledge_index_path": "docs/assets/knowledge-retrieval-index.json"}
    assert mod.load_retrieval_index(tmp_path, cfg) == []

    idx = tmp_path / "docs" / "assets" / "knowledge-retrieval-index.json"
    idx.parent.mkdir(parents=True, exist_ok=True)
    idx.write_text(json.dumps({"records": [{"id": "a"}, {"id": ""}, {"x": 1}]}), encoding="utf-8")
    rows = mod.load_retrieval_index(tmp_path, cfg)
    assert [r["id"] for r in rows] == ["a"]

    idx.write_text(json.dumps({"records": "bad"}), encoding="utf-8")
    assert mod.load_retrieval_index(tmp_path, cfg) == []


def test_infer_roles_and_acl_paths() -> None:
    from gitspeak_core.api import rag_runtime as mod

    assert mod.infer_user_roles({"tier": "free"}) == {"user"}
    assert "developer" in mod.infer_user_roles({"tier": "pro"})
    assert {"analyst", "support"}.issubset(mod.infer_user_roles({"tier": "enterprise"}))
    assert "admin" in mod.infer_user_roles({"is_superuser": True, "tier": "starter"})

    rows = [
        {
            "id": "a",
            "title": "Tenant-only guide",
            "summary": "internal",
            "metadata": {"allowed_roles": ["admin"], "allowed_tiers": ["enterprise"], "source_site": "s1"},
        },
        {
            "id": "b",
            "title": "General docs",
            "summary": "configure webhooks",
            "source_site": "s2",
        },
    ]

    hits, blocked = mod.search_retrieval_index(
        query="configure webhooks",
        rows=rows,
        user_tier="starter",
        user_roles={"user"},
        allowed_source_sites={"s2"},
        top_k=0,  # covers max(1, int(top_k))
    )
    assert blocked == 1
    assert [h["id"] for h in hits] == ["b"]


def test_acl_metadata_role_tier_branches_and_no_score() -> None:
    from gitspeak_core.api import rag_runtime as mod

    rows = [
        {
            "id": "meta-block-role",
            "title": "Internal",
            "summary": "zzz",
            "metadata": {"allowed_roles": ["admin"]},
        },
        {
            "id": "meta-block-tier",
            "title": "Internal tier",
            "summary": "zzz",
            "metadata": {"allowed_tiers": ["enterprise"]},
        },
    ]
    hits, blocked = mod.search_retrieval_index(
        query="unmatched query tokens",
        rows=rows,
        user_tier="starter",
        user_roles={"user"},
        allowed_source_sites=set(),
        top_k=5,
    )
    assert hits == []
    assert blocked == 2


def test_append_metric_and_snapshot_trimming_and_invalid_lines(tmp_path: Path) -> None:
    from gitspeak_core.api import rag_runtime as mod

    telemetry = tmp_path / "telemetry"
    reports = tmp_path / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    mod.append_rag_query_metric(
        telemetry_dir=telemetry,
        user_id="u1",
        tier="pro",
        query="q",
        top_k=3,
        hits_count=2,
        blocked_count=1,
        latency_ms=120,
        retrieval_mode="token",
    )
    metrics_file = telemetry / "rag_query_metrics.jsonl"
    metrics_file.write_text(metrics_file.read_text(encoding="utf-8") + "not-json\n\n", encoding="utf-8")

    # Include invalid retrieval eval JSON to cover exception branch.
    (reports / "retrieval_evals_report.json").write_text("{invalid", encoding="utf-8")

    # Add one more row so slicing path (rows[-max_rows:]) executes.
    mod.append_rag_query_metric(
        telemetry_dir=telemetry,
        user_id="u2",
        tier="starter",
        query="q2",
        top_k=2,
        hits_count=0,
        blocked_count=0,
        latency_ms=99,
        retrieval_mode="token",
    )

    snapshot = mod.load_rag_metrics_snapshot(telemetry_dir=telemetry, reports_dir=reports, max_rows=1)
    assert snapshot["window_rows"] == 1
    assert snapshot["query_metrics"]["latency_p50_ms"] >= 0
    assert snapshot["retrieval_eval_metrics"] == {}

    assert mod._percentile([], 95) == 0


def test_score_overlap_empty_query_returns_zero() -> None:
    from gitspeak_core.api import rag_runtime as mod

    score = mod._score_token_overlap("", {"title": "abc"})
    assert score == 0.0

    score2 = mod._score_token_overlap("alpha", {"title": "", "summary": "", "keywords": []})
    assert score2 == 0.0


def test_run_reindex_lifecycle_success_and_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from gitspeak_core.api import rag_runtime as mod

    repo = tmp_path
    (repo / "scripts").mkdir()
    (repo / "reports").mkdir()
    script = repo / "scripts" / "rag_reindex_lifecycle.py"
    script.write_text("print('ok')\n", encoding="utf-8")
    report = repo / "reports" / "rag_reindex_report.json"
    report.write_text(json.dumps({"promoted_index_version": "v1"}), encoding="utf-8")

    monkeypatch.setattr(mod.time, "time", lambda: 100.0)

    def _run_ok(cmd, cwd, capture_output, text, check):  # type: ignore[no-untyped-def]
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("subprocess.run", _run_ok)
    out = mod.run_reindex_lifecycle(
        repo_root=repo,
        python_bin="python3",
        include_embeddings=True,
        embeddings_provider="local",
    )
    assert out["provider"] == "local"
    assert out["with_embeddings"] is True

    def _run_fail(cmd, cwd, capture_output, text, check):  # type: ignore[no-untyped-def]
        return SimpleNamespace(returncode=2, stdout="s" * 50, stderr="e" * 50)

    monkeypatch.setattr("subprocess.run", _run_fail)
    with pytest.raises(RuntimeError):
        mod.run_reindex_lifecycle(
            repo_root=repo,
            python_bin="python3",
            include_embeddings=False,
            embeddings_provider="openai",
        )

    script.write_text("print('ok')\n", encoding="utf-8")
    report.write_text("{bad", encoding="utf-8")
    monkeypatch.setattr("subprocess.run", _run_ok)
    out2 = mod.run_reindex_lifecycle(
        repo_root=repo,
        python_bin="python3",
        include_embeddings=False,
        embeddings_provider="openai",
    )
    assert out2["provider"] == "openai"
    assert out2["with_embeddings"] is False

    script.unlink()
    with pytest.raises(FileNotFoundError):
        mod.run_reindex_lifecycle(
            repo_root=repo,
            python_bin="python3",
            include_embeddings=False,
            embeddings_provider="openai",
        )


def test_resolve_embeddings_provider_fallbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    from gitspeak_core.api import rag_runtime as mod

    monkeypatch.setenv("VERIDOC_RAG_EMBED_PROVIDER", "garbage")
    assert mod.resolve_embeddings_provider(None) == "local"
    assert mod.resolve_embeddings_provider(" OPENAI ") == "openai"

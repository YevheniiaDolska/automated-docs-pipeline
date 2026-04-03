from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_enforce_rag_layer_helpers() -> None:
    from scripts import enforce_rag_optimization_layer as mod

    assert mod._derive_profile({"llm_control": {"strict_local_first": True}}) == "strict-local"
    assert mod._derive_profile({"llm_control": {"llm_mode": "local_default"}}) == "strict-local"
    assert mod._derive_profile({"llm_control": {"llm_mode": "external_preferred"}}) == "cloud"

    thresholds = mod._thresholds_from_runtime({})
    alerts = mod._evaluate_alerts(
        rag_report={"status": "degraded"},
        eval_report={"metrics": {"recall_at_k": 0.1, "hallucination_rate": 0.7}},
        metrics_snapshot={"latency_p95_ms": 99999, "no_hit_rate": 0.99},
        thresholds=thresholds,
    )
    codes = {a["code"] for a in alerts}
    assert "RAG_RECALL_LOW" in codes
    assert "RAG_HALLUCINATION_HIGH" in codes
    assert "RAG_LATENCY_P95_HIGH" in codes
    assert "RAG_NO_HIT_RATE_HIGH" in codes
    assert "RAG_LAYER_NOT_OK" in codes


def test_enforce_rag_layer_main_writes_report(tmp_path: Path, monkeypatch) -> None:
    from scripts import enforce_rag_optimization_layer as mod

    repo = tmp_path
    (repo / "docsops" / "config").mkdir(parents=True)
    (repo / "docsops" / "config" / "client_runtime.yml").write_text(
        "llm_control:\n  llm_mode: local_default\n",
        encoding="utf-8",
    )
    reports = repo / "reports"
    reports.mkdir()

    def _fake_run(cmd: list[str], cwd: Path) -> None:
        _ = (cmd, cwd)
        (reports / "rag_reindex_report.json").write_text(json.dumps({"status": "ok"}), encoding="utf-8")
        (reports / "retrieval_evals_report.json").write_text(
            json.dumps({"metrics": {"recall_at_k": 0.9, "hallucination_rate": 0.01}}),
            encoding="utf-8",
        )
        (reports / "rag_metrics_snapshot.json").write_text(
            json.dumps({"query_metrics": {"latency_p95_ms": 100, "no_hit_rate": 0.01}}),
            encoding="utf-8",
        )

    monkeypatch.setattr(mod, "_run", _fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "x",
            "--repo-root",
            str(repo),
            "--runtime-config",
            "docsops/config/client_runtime.yml",
            "--reports-dir",
            "reports",
            "--provider",
            "local",
        ],
    )

    rc = mod.main()
    assert rc == 0
    payload = json.loads((reports / "rag_optimization_layer_report.json").read_text(encoding="utf-8"))
    assert payload["status"] == "ok"
    assert payload["profile"] == "strict-local"


def test_rag_reindex_lifecycle_promote_and_rollback(tmp_path: Path, monkeypatch) -> None:
    from scripts import rag_reindex_lifecycle as mod

    repo = tmp_path
    versions = repo / "docs" / "assets" / "rag-versions" / "v1"
    versions.mkdir(parents=True)
    promoted_index = repo / "docs" / "assets" / "knowledge-retrieval-index.json"
    promoted_index.parent.mkdir(parents=True, exist_ok=True)
    (versions / "knowledge-retrieval-index.json").write_text("[]\n", encoding="utf-8")
    (versions / "retrieval.faiss").write_bytes(b"faiss")
    (versions / "retrieval-metadata.json").write_text("[]\n", encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "x",
            "--repo-root",
            str(repo),
            "--skip-rebuild",
            "--promote-version",
            "v1",
        ],
    )
    assert mod.main() == 0
    assert (repo / "docs" / "assets" / "rag_promoted.json").exists()

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "x",
            "--repo-root",
            str(repo),
            "--skip-rebuild",
            "--rollback-to-version",
            "v1",
        ],
    )
    assert mod.main() == 0
    assert promoted_index.exists()


def test_run_docs_ci_checks_paths(monkeypatch, tmp_path: Path) -> None:
    from scripts import run_docs_ci_checks as mod

    monkeypatch.chdir(tmp_path)
    runtime = tmp_path / "runtime.yml"
    runtime.write_text("docs_site:\n  generator: mkdocs\n", encoding="utf-8")

    calls: list[str] = []

    def _fake_run(command: str, cwd: Path) -> int:
        _ = cwd
        calls.append(command)
        return 0

    monkeypatch.setattr(mod, "_run_shell", _fake_run)
    monkeypatch.setattr(sys, "argv", ["x", "--runtime-config", str(runtime)])
    assert mod.main() == 0
    assert calls

    def _lint_fails(command: str, cwd: Path) -> int:
        _ = (command, cwd)
        return 2

    monkeypatch.setattr(mod, "_run_shell", _lint_fails)
    monkeypatch.setattr(sys, "argv", ["x", "--runtime-config", str(runtime)])
    assert mod.main() == 2


def test_run_workspace_preprod_check_reports(tmp_path: Path, monkeypatch) -> None:
    from scripts import run_workspace_preprod_check as mod

    repo_clean = tmp_path / "repo_clean"
    repo_dirty = tmp_path / "repo_dirty"
    for repo in (repo_clean, repo_dirty):
        (repo / "docsops" / "config").mkdir(parents=True)
        (repo / "docsops" / "policy_packs").mkdir(parents=True)
        (repo / "docsops" / "config" / "client_runtime.yml").write_text("ok: true\n", encoding="utf-8")
        (repo / "docsops" / "policy_packs" / "selected.yml").write_text("ok: true\n", encoding="utf-8")
        (repo / "docsops" / "license.jwt").write_text("jwt\n", encoding="utf-8")

    def _fake_git_run(cmd, cwd, check, capture_output, text):  # noqa: ANN001
        _ = (cmd, check, capture_output, text)
        stdout = " M x\n" if "repo_dirty" in str(cwd) else ""
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr(subprocess, "run", _fake_git_run)

    report = tmp_path / "out.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "x",
            "--repos",
            str(repo_clean),
            str(repo_dirty),
            "--report",
            str(report),
        ],
    )
    rc = mod.main()
    assert rc == 0
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["total"] == 2
    assert data["ok_count"] == 2

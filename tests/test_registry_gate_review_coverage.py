from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_pack_registry_fetch_helpers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts import pack_registry_fetch as mod

    raw_key = b"a" * 32
    key_raw = tmp_path / "raw.bin"
    key_raw.write_bytes(raw_key)
    assert mod._load_public_key(key_raw) == raw_key

    key_b64 = tmp_path / "b64.bin"
    key_b64.write_bytes(base64.b64encode(raw_key))
    assert mod._load_public_key(key_b64) == raw_key

    key_bad = tmp_path / "bad.bin"
    key_bad.write_text("bad-key", encoding="utf-8")
    with pytest.raises(ValueError):
        mod._load_public_key(key_bad)

    monkeypatch.setitem(sys.modules, "nacl.signing", None)

    orig_import = __import__

    def _import_missing(name, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name in {
            "nacl.signing",
            "cryptography.hazmat.primitives.asymmetric.ed25519",
        }:
            raise ImportError("missing")
        return orig_import(name, *args, **kwargs)
    monkeypatch.setattr("builtins.__import__", _import_missing)
    assert mod._verify_ed25519(b"m", b"s", b"k" * 32) is False
    monkeypatch.setattr("builtins.__import__", orig_import)


def test_pack_registry_publish_helpers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts import pack_registry_publish as mod

    raw_key = b"b" * 32
    key_raw = tmp_path / "raw.bin"
    key_raw.write_bytes(raw_key)
    assert mod._load_private_key(key_raw) == raw_key

    key_b64 = tmp_path / "b64.bin"
    key_b64.write_bytes(base64.b64encode(raw_key))
    assert mod._load_private_key(key_b64) == raw_key

    key_bad = tmp_path / "bad.bin"
    key_bad.write_text("bad-key", encoding="utf-8")
    with pytest.raises(ValueError):
        mod._load_private_key(key_bad)

    # Simulate both signing backends missing.
    orig_import = __import__

    def _import_missing(name, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name in {
            "nacl.signing",
            "cryptography.hazmat.primitives.asymmetric.ed25519",
        }:
            raise ImportError("missing")
        return orig_import(name, *args, **kwargs)
    monkeypatch.setattr("builtins.__import__", _import_missing)
    with pytest.raises(RuntimeError, match="No Ed25519 library installed"):
        mod._sign_ed25519(b"message", b"k" * 32)
    monkeypatch.setattr("builtins.__import__", orig_import)


def test_retrieval_gate_dataset_matching_and_main(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from scripts import run_retrieval_evals_gate as mod

    idx = tmp_path / "idx.json"
    data = tmp_path / "dataset.yml"
    idx.write_text(json.dumps([{"id": "a"}, {"id": "b"}]), encoding="utf-8")
    data.write_text("- expected_ids: ['a']\n- expected_ids: ['x']\n", encoding="utf-8")
    assert mod._dataset_matches_index(data, idx) is True

    bad = tmp_path / "bad.yml"
    bad.write_text("{}", encoding="utf-8")
    assert mod._dataset_matches_index(bad, idx) is False

    # Main path with auto dataset fallback and injected OPENAI key.
    repo = tmp_path / "repo"
    (repo / "docs/assets").mkdir(parents=True)
    (repo / "config").mkdir(parents=True)
    (repo / "reports").mkdir(parents=True)
    (repo / "scripts").mkdir(parents=True)
    (repo / "scripts/run_retrieval_evals.py").write_text("print('ok')\n", encoding="utf-8")
    (repo / "docs/assets/knowledge-retrieval-index.json").write_text(json.dumps([{"id": "x"}]), encoding="utf-8")
    (repo / "config/retrieval_eval_dataset.yml").write_text("- expected_ids: ['unknown']\n", encoding="utf-8")
    (repo / "docs/assets/retrieval.faiss").write_bytes(b"faiss")

    monkeypatch.setattr(mod, "REPO_ROOT", repo)
    monkeypatch.setenv("DOCSOPS_SHARED_OPENAI_API_KEY", "shared-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(mod, "_has_sentence_transformers", lambda: True)

    observed = {}

    def _run(cmd, cwd, env, check):  # type: ignore[no-untyped-def]
        observed["cmd"] = cmd
        observed["env"] = env
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(mod.subprocess, "run", _run)
    assert mod.main() == 0
    assert "--auto-generate-dataset" in observed["cmd"]
    assert "--use-embeddings" in observed["cmd"]
    assert observed["env"]["OPENAI_API_KEY"] == "shared-key"


def test_publish_review_branch_helpers_and_flow(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from scripts import publish_docs_review_branch as mod

    class _Proc:
        def __init__(self, rc: int = 0, out: str = "") -> None:
            self.returncode = rc
            self.stdout = out

    # Helper coverage
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: _Proc(0, "main\n"))
    assert mod._current_branch(tmp_path) == "main"
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: _Proc(1, ""))
    assert mod._current_branch(tmp_path) == ""
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: _Proc(0, ""))
    assert mod._has_changes(tmp_path) is False

    runtime_path = tmp_path / "runtime.yml"
    runtime_path.write_text("- not-a-dict\n", encoding="utf-8")
    assert mod._read_runtime(runtime_path) == {}
    assert mod._build_review_branch_name(" docs/review ")[:11] == "docs/review"

    calls: list[list[str]] = []

    def _fake_run(cmd, cwd, check=False, capture_output=False, text=False):  # type: ignore[no-untyped-def]
        calls.append(list(cmd))
        if cmd[:3] == ["git", "status", "--porcelain"]:
            return _Proc(0, " M docs/a.md\n")
        if cmd[:4] == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
            return _Proc(0, "main\n")
        if cmd[:4] == ["git", "show-ref", "--verify", "--quiet"]:
            return _Proc(0, "")
        return _Proc(0, "")

    monkeypatch.setattr(mod.subprocess, "run", _fake_run)
    monkeypatch.setattr(
        mod,
        "_read_runtime",
        lambda p: {"review_branch": {"enabled": True}, "finalize_gate": {}},
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "publish_docs_review_branch.py",
            "--lint-command",
            "echo lint-ok",
            "--precommit-command",
            "echo pre-ok",
        ],
    )
    monkeypatch.chdir(tmp_path)
    assert mod.main() == 0
    assert any(cmd[:2] == ["git", "push"] for cmd in calls)


def test_free_enterprise_bundle_profile_validation_and_main(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from scripts import build_free_enterprise_bundle as mod

    with pytest.raises(FileNotFoundError):
        mod._resolve_profile("missing.client.yml")

    with pytest.raises(ValueError):
        mod._override_profile_for_free_enterprise({"client": []}, "out")
    with pytest.raises(ValueError):
        mod._override_profile_for_free_enterprise({"client": {"id": ""}}, "out")
    with pytest.raises(ValueError):
        mod._override_profile_for_free_enterprise({"client": {"id": "a"}, "bundle": []}, "out")
    with pytest.raises(ValueError):
        mod._override_profile_for_free_enterprise({"client": {"id": "a"}, "bundle": {}, "licensing": []}, "out")

    repo = tmp_path / "repo"
    profile = repo / "client.client.yml"
    profile.parent.mkdir(parents=True, exist_ok=True)
    profile.write_text(
        "client:\n  id: acme\nbundle: {}\nlicensing:\n  days: 7\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "REPO_ROOT", repo)
    monkeypatch.setattr(mod, "read_yaml", lambda p: {"client": {"id": "acme"}, "bundle": {}, "licensing": {}})
    monkeypatch.setattr(mod, "write_yaml", lambda p, payload: p.write_text("ok\n", encoding="utf-8"))
    bundle_root = tmp_path / "bundle"
    bundle_root.mkdir(parents=True, exist_ok=True)
    (bundle_root / ".env.docsops.local.template").write_text("X=1\n", encoding="utf-8")
    monkeypatch.setattr(mod, "create_bundle", lambda p: bundle_root)
    monkeypatch.setattr(sys, "argv", ["build_free_enterprise_bundle.py", "--client", str(profile)])
    assert mod.main() == 0
    assert "VERIOPS_LICENSE_PLAN=enterprise" in (bundle_root / ".env.docsops.local.template").read_text(encoding="utf-8")

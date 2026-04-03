from __future__ import annotations

import base64
import json
from pathlib import Path

from scripts import (
    apply_veridoc_branding_policy as branding,
    bootstrap_workspace_veridoc_policy as bootstrap,
    build_free_enterprise_bundle as free_bundle,
    docs_ci_bootstrap as ci_bootstrap,
    pack_registry_fetch as pack_fetch,
    pack_registry_publish as pack_publish,
    publish_docs_review_branch as review_branch,
    setup_client_env_wizard as env_wizard,
)


def test_branding_main_mandatory_and_opt_out(tmp_path: Path, monkeypatch) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    target = docs / "guide.md"
    target.write_text("# Guide\n", encoding="utf-8")

    report = tmp_path / "reports" / "branding.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "apply_veridoc_branding_policy.py",
            "--repo-root",
            str(tmp_path),
            "--docs-root",
            "docs",
            "--landing-url",
            "https://veri-doc.app/landing",
            "--plan",
            "starter",
            "--report",
            str(report),
        ],
    )
    assert branding.main() == 0
    text = target.read_text(encoding="utf-8")
    assert "Powered by VeriDoc" in text

    monkeypatch.setattr(
        "sys.argv",
        [
            "apply_veridoc_branding_policy.py",
            "--repo-root",
            str(tmp_path),
            "--docs-root",
            "docs",
            "--landing-url",
            "https://veri-doc.app/landing",
            "--plan",
            "business",
            "--badge-opt-out",
            "--report",
            str(report),
        ],
    )
    assert branding.main() == 0
    text_after = target.read_text(encoding="utf-8")
    assert "VERIDOC_POWERED_BADGE:START" not in text_after
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["ok"] is True


def test_bootstrap_build_profile_and_main(tmp_path: Path, monkeypatch) -> None:
    template = {
        "client": {"id": "x", "company_name": "x", "contact_email": "x@example.com"},
        "runtime": {"integrations": {"algolia": {}, "ask_ai": {}}, "docs_flow": {}, "output_targets": []},
        "licensing": {},
        "bundle": {},
    }
    repo_root = tmp_path / "repo"
    (repo_root / "profiles" / "clients").mkdir(parents=True)
    (repo_root / "profiles" / "clients" / "_template.client.yml").write_text(
        json.dumps(template), encoding="utf-8"
    )
    monkeypatch.setattr(bootstrap, "REPO_ROOT", repo_root)

    client_repo = tmp_path / "client-one"
    (client_repo / "api").mkdir(parents=True)
    profile_path = bootstrap._build_profile(client_repo, "https://veri-doc.app/landing", "starter", "starter")
    assert profile_path.exists()
    profile = bootstrap._load_yaml(profile_path)
    assert profile["runtime"]["veridoc_branding"]["landing_url"] == "https://veri-doc.app/landing"

    def _fake_run(cmd: list[str]) -> tuple[int, str]:
        return 0, "ok"

    monkeypatch.setattr(bootstrap, "_run", _fake_run)
    report_path = tmp_path / "report.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "bootstrap_workspace_veridoc_policy.py",
            "--landing-url",
            "https://veri-doc.app/landing",
            "--repos",
            str(client_repo),
            "--report",
            str(report_path),
        ],
    )
    assert bootstrap.main() == 0
    assert json.loads(report_path.read_text(encoding="utf-8"))["ok"] is True


def test_free_bundle_helpers(tmp_path: Path) -> None:
    profile = {"client": {"id": "tenant-1"}, "bundle": {}, "licensing": {}}
    patched = free_bundle._override_profile_for_free_enterprise(profile, "generated/client_bundles_free")
    assert patched["licensing"]["plan"] == "enterprise"
    assert patched["licensing"]["auto_generate_capability_pack"] is False

    bundle_root = tmp_path / "bundle"
    bundle_root.mkdir()
    env_template = bundle_root / ".env.docsops.local.template"
    env_template.write_text("A=1\n", encoding="utf-8")
    free_bundle._set_unlicensed_enterprise_env(bundle_root)
    updated = env_template.read_text(encoding="utf-8")
    assert "VERIOPS_LICENSE_PLAN=enterprise" in updated


def test_ci_bootstrap_install_files_github(tmp_path: Path, monkeypatch) -> None:
    class _Completed:
        returncode = 0
        stdout = "git@github.com:test/repo.git\n"

    monkeypatch.setattr(ci_bootstrap.subprocess, "run", lambda *a, **k: _Completed())
    runtime = {"output_targets": ["mkdocs"], "finalize_gate": {"lint_command": "npm run lint"}}
    created = ci_bootstrap.install_docs_ci_files(tmp_path, runtime, install_jenkins=True)
    created_names = {p.name for p in created}
    assert "docsops-docs-ci.yml" in created_names
    assert "Jenkinsfile.docsops" in created_names


def test_pack_publish_and_fetch_main(tmp_path: Path, monkeypatch) -> None:
    # publish path
    pack = tmp_path / "pack.enc"
    pack.write_bytes(b"encrypted-pack")
    key_bytes = b"a" * 32
    key_file = tmp_path / "key.bin"
    key_file.write_bytes(key_bytes)

    monkeypatch.setattr(pack_publish, "_sign_ed25519", lambda message, private_key: b"sig")

    class _PublishResp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"status":"ok"}'

    monkeypatch.setattr(pack_publish.urllib.request, "urlopen", lambda *a, **k: _PublishResp())
    monkeypatch.setattr(
        "sys.argv",
        [
            "pack_registry_publish.py",
            "--pack",
            str(pack),
            "--pack-name",
            "core-pack",
            "--version",
            "1.0.0",
            "--private-key",
            str(key_file),
            "--ops-token",
            "token",
        ],
    )
    assert pack_publish.main() == 0

    # fetch path
    pub_key = tmp_path / "pub.bin"
    pub_key.write_bytes(b"b" * 32)

    class _FetchResp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            payload = {
                "encrypted_blob_b64": base64.b64encode(b"encrypted-pack").decode("ascii"),
                "checksum_sha256": "7df52402bc2cdc8022a2e24bee5580a7db163e624b218a2414a265426026f645",
                "signature_b64": base64.b64encode(b"sig").decode("ascii"),
            }
            return json.dumps(payload).encode("utf-8")

    monkeypatch.setattr(pack_fetch, "_verify_ed25519", lambda message, signature, public_key: True)
    monkeypatch.setattr(pack_fetch.urllib.request, "urlopen", lambda *a, **k: _FetchResp())
    output = tmp_path / "out.enc"
    monkeypatch.setattr(
        "sys.argv",
        [
            "pack_registry_fetch.py",
            "--pack-name",
            "core-pack",
            "--version",
            "1.0.0",
            "--public-key",
            str(pub_key),
            "--output",
            str(output),
            "--ops-token",
            "token",
        ],
    )
    assert pack_fetch.main() == 0
    assert output.read_bytes() == b"encrypted-pack"


def test_review_branch_main_no_changes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(review_branch, "_read_runtime", lambda path: {})
    monkeypatch.setattr(review_branch, "_has_changes", lambda repo_root: False)
    monkeypatch.setattr("sys.argv", ["publish_docs_review_branch.py"])
    assert review_branch.main() == 0


def test_env_wizard_main_with_template(tmp_path: Path, monkeypatch) -> None:
    template = tmp_path / ".env.docsops.local.template"
    template.write_text("A=1\nB=2\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    answers = iter(["", "", "n", "n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    monkeypatch.setattr(env_wizard, "_load_runtime", lambda repo_root: {})
    monkeypatch.setattr(env_wizard, "install_docs_ci_files", lambda *a, **k: [])
    assert env_wizard.main() == 0
    out = (tmp_path / ".env.docsops.local").read_text(encoding="utf-8")
    assert "A=" in out and "B=" in out

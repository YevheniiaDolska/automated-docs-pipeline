from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace


def test_build_offline_renewal_bundle_zip(monkeypatch, tmp_path: Path) -> None:
    from scripts import build_offline_renewal_bundle as mod

    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)

    def _fake_run(cmd: list[str], cwd: str, check: bool, capture_output: bool, text: bool):
        output_path = Path(cmd[cmd.index("--output") + 1])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if "generate_license.py" in cmd[1]:
            output_path.write_text("jwt-token\n", encoding="utf-8")
        elif "generate_pack.py" in cmd[1]:
            output_path.write_bytes(b"PACK")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(mod.subprocess, "run", _fake_run)

    args = SimpleNamespace(
        client_id="acme",
        plan="enterprise",
        days=30,
        tenant_id="acme",
        company_domain="acme.example",
        with_pack=True,
        license_key="KEY-123",
        license_jwt_path="",
        capability_pack_path="",
        format="zip",
        output_dir=str(tmp_path / "out"),
        filename="",
    )
    out = mod.build_bundle(args)
    assert out.exists()
    assert out.name.startswith("renewal-acme-")
    assert out.suffix == ".zip"


def test_build_offline_renewal_bundle_with_prebuilt_files(tmp_path: Path) -> None:
    from scripts import build_offline_renewal_bundle as mod

    jwt = tmp_path / "license.jwt"
    jwt.write_text("jwt\n", encoding="utf-8")
    pack = tmp_path / ".capability_pack.enc"
    pack.write_bytes(b"PACK")

    args = SimpleNamespace(
        client_id="demo",
        plan="professional",
        days=30,
        tenant_id="",
        company_domain="",
        with_pack=True,
        license_key="",
        license_jwt_path=str(jwt),
        capability_pack_path=str(pack),
        format="tar.gz",
        output_dir=str(tmp_path / "out"),
        filename="renewal-demo.tar.gz",
    )
    out = mod.build_bundle(args)
    assert out.exists()
    assert out.name == "renewal-demo.tar.gz"

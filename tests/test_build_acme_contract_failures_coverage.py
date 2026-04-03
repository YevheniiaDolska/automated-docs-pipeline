from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _make_base_page(rel: str) -> str:
    return (
        "---\n"
        f"title: {rel}\n"
        "description: This description is intentionally long enough for checks.\n"
        "content_type: reference\n"
        "product: both\n"
        "tags:\n"
        "  - API\n"
        "---\n\n"
        "Powered by VeriDoc\n\n"
        "Content body\n"
    )


def _seed_valid_tree(root: Path) -> None:
    from scripts import build_acme_demo_site as mod

    docs = root / "docs"
    nav = []
    for rel in mod.REQUIRED_PAGES:
        target = docs / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if rel == "quality/review-manifest.md":
            target.write_text("# Review\n", encoding="utf-8")
        else:
            target.write_text(_make_base_page(rel), encoding="utf-8")
        nav.append({rel: rel})

    (root / "mkdocs.yml").write_text(yaml.safe_dump({"nav": nav}, sort_keys=False), encoding="utf-8")


def test_validate_page_contract_failures(tmp_path: Path) -> None:
    from scripts import build_acme_demo_site as mod

    with pytest.raises(FileNotFoundError):
        mod._validate_page_contract(tmp_path)

    (tmp_path / "mkdocs.yml").write_text("site_name: x\n", encoding="utf-8")
    with pytest.raises(ValueError):
        mod._validate_page_contract(tmp_path)

    _seed_valid_tree(tmp_path)
    # remove one page from nav
    (tmp_path / "mkdocs.yml").write_text(yaml.safe_dump({"nav": [{"only": "index.md"}]}, sort_keys=False), encoding="utf-8")
    with pytest.raises(ValueError):
        mod._validate_page_contract(tmp_path)

    _seed_valid_tree(tmp_path)
    # missing required page file
    (tmp_path / "docs" / "reference" / "rest-api.md").unlink()
    with pytest.raises(FileNotFoundError):
        mod._validate_page_contract(tmp_path)

    _seed_valid_tree(tmp_path)
    p = tmp_path / "docs" / "reference" / "graphql-playground.md"
    p.write_text(p.read_text(encoding="utf-8").replace("Powered by VeriDoc", ""), encoding="utf-8")
    with pytest.raises(ValueError):
        mod._validate_page_contract(tmp_path)


def test_validate_scope_secrets_links_and_quality_stack(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import build_acme_demo_site as mod

    _seed_valid_tree(tmp_path)
    docs = tmp_path / "docs"

    # forbidden token detection
    bad = docs / "guides" / "tutorial.md"
    bad.write_text(bad.read_text(encoding="utf-8") + "\nblockstream-demo\n", encoding="utf-8")
    with pytest.raises(ValueError):
        mod._validate_scope(tmp_path)
    bad.write_text(bad.read_text(encoding="utf-8").replace("blockstream-demo", "clean-token"), encoding="utf-8")

    # secret detection
    sec = docs / "guides" / "how-to.md"
    sec.write_text(sec.read_text(encoding="utf-8") + "\nsk-abcdefghijklmnopqrstuvwx\n", encoding="utf-8")
    with pytest.raises(ValueError):
        mod._validate_no_secrets(tmp_path)
    sec.write_text(sec.read_text(encoding="utf-8").replace("sk-abcdefghijklmnopqrstuvwx", "safe-token"), encoding="utf-8")

    # broken local link
    index = docs / "index.md"
    index.write_text(index.read_text(encoding="utf-8") + "\n[bad](missing.md)\n", encoding="utf-8")
    with pytest.raises(ValueError):
        mod._validate_local_links(tmp_path)

    # quality stack command orchestration
    cmds: list[list[str]] = []
    monkeypatch.setattr(mod, "_run", lambda cmd, cwd: cmds.append(cmd))
    monkeypatch.setattr(mod, "_run_allow_fail", lambda cmd, cwd, label: 1)
    monkeypatch.setattr(mod, "_validate_local_links", lambda out: None)
    monkeypatch.setattr(mod, "_validate_no_secrets", lambda out: None)
    mod._run_quality_stack(tmp_path, tmp_path / "reports")
    assert any("normalize_docs.py" in " ".join(c) for c in cmds)
    assert any("lint_code_snippets.py" in " ".join(c) for c in cmds)


def test_assets_contract_and_built_site_failures(tmp_path: Path) -> None:
    from scripts import build_acme_demo_site as mod

    _seed_valid_tree(tmp_path)
    docs = tmp_path / "docs"
    with pytest.raises(FileNotFoundError):
        mod._validate_assets_contract(tmp_path)

    for rel in mod.REQUIRED_PIPELINE_ASSETS:
        t = docs / rel
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_text("x", encoding="utf-8")

    (docs / "assets" / "javascripts").mkdir(parents=True, exist_ok=True)
    (docs / "assets" / "javascripts" / "sandbox-config.js").write_text("missing", encoding="utf-8")
    with pytest.raises(ValueError):
        mod._validate_assets_contract(tmp_path)

    (docs / "assets" / "javascripts" / "sandbox-config.js").write_text(
        "asyncapi_ws_fallback_urls websocket_fallback_urls wss://echo.websocket.events",
        encoding="utf-8",
    )
    (docs / "reference" / "websocket-events.md").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        mod._validate_assets_contract(tmp_path)

    (docs / "reference" / "websocket-events.md").write_text(
        "__ACME_SANDBOX_CONTROLLER__ live-echo-plus-semantic offline-semantic-fallback simulated_response",
        encoding="utf-8",
    )
    (docs / "reference" / "asyncapi-events.md").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        mod._validate_assets_contract(tmp_path)

    (docs / "reference" / "asyncapi-events.md").write_text(
        "__ACME_SANDBOX_CONTROLLER__ live-echo-plus-semantic offline-semantic-fallback simulated_response project.updated task.completed",
        encoding="utf-8",
    )
    mod._validate_assets_contract(tmp_path)

    with pytest.raises(FileNotFoundError):
        mod._validate_built_site_contract(tmp_path)

    site = tmp_path / "site"
    (site / "reference" / "rest-api").mkdir(parents=True, exist_ok=True)
    (site / "reference" / "swagger-test.html").parent.mkdir(parents=True, exist_ok=True)
    (site / "reference" / "rest-api" / "index.html").write_text("no-link", encoding="utf-8")
    (site / "reference" / "swagger-test.html").write_text("ok", encoding="utf-8")
    with pytest.raises(ValueError):
        mod._validate_built_site_contract(tmp_path)

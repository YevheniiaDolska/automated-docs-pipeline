from __future__ import annotations

from pathlib import Path

from scripts import generate_public_docs_audit as public_audit
from scripts import personal_wizard as pw
from scripts import setup_client_env_wizard as env_wizard


def test_setup_template_and_existing_helpers(tmp_path: Path) -> None:
    template = tmp_path / ".env.template"
    template.write_text("# first key\nA=1\n\n# second\nB = 2\ninvalid\n", encoding="utf-8")
    items = env_wizard._parse_template(template)
    assert items == [("A", "first key"), ("B", "second")]

    env = tmp_path / ".env"
    env.write_text("# c\nA=1\nB=2\n\nBAD\n", encoding="utf-8")
    existing = env_wizard._read_existing(env)
    assert existing == {"A": "1", "B": "2"}


def test_setup_install_ollama_branches(monkeypatch, capsys) -> None:
    class _Res:
        def __init__(self, rc: int):
            self.returncode = rc

    # ollama exists -> pull success path
    monkeypatch.setattr(env_wizard.shutil, "which", lambda name: "/usr/bin/ollama" if name == "ollama" else None)
    monkeypatch.setattr(env_wizard.subprocess, "run", lambda *a, **k: _Res(0))
    env_wizard._install_ollama_and_model("qwen3:30b")

    # linux auto-install fails
    monkeypatch.setattr(env_wizard.shutil, "which", lambda name: None)
    monkeypatch.setattr(env_wizard.platform, "system", lambda: "Linux")
    monkeypatch.setattr(env_wizard.subprocess, "run", lambda *a, **k: _Res(1))
    env_wizard._install_ollama_and_model("qwen3:30b")

    # darwin without brew
    monkeypatch.setattr(env_wizard.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(env_wizard.shutil, "which", lambda name: None)
    env_wizard._install_ollama_and_model("qwen3:30b")

    # windows without winget
    monkeypatch.setattr(env_wizard.platform, "system", lambda: "Windows")
    monkeypatch.setattr(env_wizard.shutil, "which", lambda name: None)
    env_wizard._install_ollama_and_model("qwen3:30b")

    # unsupported os
    monkeypatch.setattr(env_wizard.platform, "system", lambda: "FreeBSD")
    env_wizard._install_ollama_and_model("qwen3:30b")
    assert capsys.readouterr().out


def test_setup_modelfile_and_create_model(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    docsops = repo / "docsops"
    docsops.mkdir(parents=True)
    (docsops / "LOCAL_MODEL.md").write_text("Rule A", encoding="utf-8")
    (docsops / "AGENTS.md").write_text("Rule B", encoding="utf-8")
    (docsops / "CLAUDE.md").write_text("Rule C", encoding="utf-8")
    modelfile = env_wizard._create_veridoc_modelfile(repo, "qwen3:30b", "veridoc-writer")
    text = modelfile.read_text(encoding="utf-8")
    assert "FROM qwen3:30b" in text
    assert "Rule A" in text and "Rule B" in text and "Rule C" in text

    # create model: no ollama
    monkeypatch.setattr(env_wizard.shutil, "which", lambda name: None)
    env_wizard._create_ollama_model("veridoc-writer", modelfile)

    # create model: success and fail
    class _Res:
        def __init__(self, rc: int):
            self.returncode = rc

    monkeypatch.setattr(env_wizard.shutil, "which", lambda name: "/usr/bin/ollama")
    monkeypatch.setattr(env_wizard.subprocess, "run", lambda *a, **k: _Res(0))
    env_wizard._create_ollama_model("veridoc-writer", modelfile)
    monkeypatch.setattr(env_wizard.subprocess, "run", lambda *a, **k: _Res(1))
    env_wizard._create_ollama_model("veridoc-writer", modelfile)


def test_personal_prompt_helpers(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    assert pw._prompt("Name", "default") == "default"
    assert pw._prompt_yes_no("Question", default_yes=False) is False

    vals = iter(["bad", "hybrid"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(vals))
    assert pw._prompt_choice("Mode", ["fully-local", "hybrid"], "hybrid") == "hybrid"

    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    assert pw._prompt_csv("CSV", ["a", "b"]) == ["a", "b"]
    assert pw._slugify(" ACME Docs!! ") == "acme-docs"


def test_public_audit_early_helpers(monkeypatch) -> None:
    assert public_audit._normalize_url("docs.example.com/path/") == "https://docs.example.com/path"
    assert public_audit._normalize_url("https://[service.name]") == ""
    assert public_audit._safe_join_normalize_url("https://docs.example.com/a", "../b") == "https://docs.example.com/b"
    assert public_audit._is_probable_crawl_trap("https://docs.example.com/search?q=a&x=1&y=2&z=3")

    xml = "<urlset><url><loc>https://docs.example.com/a</loc></url><url><loc>https://docs.example.com/b</loc></url></urlset>"
    assert public_audit._extract_http_urls_from_xml(xml) == [
        "https://docs.example.com/a",
        "https://docs.example.com/b",
    ]

    fetch_map = {
        "https://docs.example.com/robots.txt": (200, "text/plain", "Sitemap: https://docs.example.com/sitemap.xml"),
        "https://docs.example.com/sitemap.xml": (200, "application/xml", "<urlset><url><loc>https://docs.example.com/a</loc></url></urlset>"),
        "https://docs.example.com/sitemap_index.xml": (404, "text/plain", ""),
        "https://docs.example.com/sitemap-index.xml": (404, "text/plain", ""),
        "https://docs.example.com/feed": (200, "application/xml", "<rss><channel><link>https://docs.example.com/feed-item</link></channel></rss>"),
        "https://docs.example.com/rss": (404, "text/plain", ""),
        "https://docs.example.com/atom.xml": (404, "text/plain", ""),
        "https://docs.example.com/feed.xml": (404, "text/plain", ""),
    }

    monkeypatch.setattr(public_audit, "_fetch", lambda url, timeout, extra_headers=None: fetch_map.get(url, (404, "text/plain", "")))
    discovered, robot_count = public_audit._discover_seed_urls_from_sitemaps("https://docs.example.com", 10, auth_headers={})
    assert "https://docs.example.com/a" in discovered
    assert robot_count == 1

    feed_urls = public_audit._discover_seed_urls_from_feeds("https://docs.example.com", 10, auth_headers={})
    assert "https://docs.example.com/feed-item" in feed_urls

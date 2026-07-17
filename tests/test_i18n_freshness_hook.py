"""Tests for hooks/i18n_freshness.py (reader-facing freshness banner)."""

from __future__ import annotations

import hashlib
import re
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hooks"))

import i18n_freshness as hook


_FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n?", re.DOTALL)


@pytest.fixture(autouse=True)
def _reset_caches(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Clear the module-level caches between tests."""
    hook._CONFIG_CACHE = None
    hook._HASH_CACHE = {}
    monkeypatch.chdir(tmp_path)
    yield
    hook._CONFIG_CACHE = None
    hook._HASH_CACHE = {}


class FakePage:
    def __init__(self, meta: dict):
        self.meta = meta


class FakeConfig:
    def __init__(self, docs_dir: Path):
        self.docs_dir = str(docs_dir)


def _write_i18n_config(tmp_path: Path, **banner) -> None:
    settings = {"enabled": True, "show_when_fresh": True, "link_to_source": True}
    settings.update(banner)
    lines = ["default_language: en", "freshness_banner:"]
    for key, value in settings.items():
        lines.append(f"  {key}: {str(value).lower()}")
    (tmp_path / "i18n.yml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_source(docs: Path, rel: str, body: str = "Original.") -> str:
    path = docs / "en" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    text = textwrap.dedent(f"""\
        ---
        title: "Source"
        ---

        # Source

        {body}
        """)
    path.write_text(text, encoding="utf-8")
    stripped = _FRONTMATTER_RE.sub("", text, count=1).strip()
    return hashlib.sha256(stripped.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Banner states
# ---------------------------------------------------------------------------

def test_fresh_page_states_it_is_current(tmp_path: Path) -> None:
    _write_i18n_config(tmp_path)
    docs = tmp_path / "docs"
    source_hash = _write_source(docs, "guide.md")

    out = hook.on_page_markdown(
        "# Перевод\n",
        page=FakePage({
            "language": "ru",
            "translation_of": "en/guide.md",
            "source_hash": source_hash,
            "translated_at": "2026-07-17",
        }),
        config=FakeConfig(docs),
    )

    assert "Translation up to date" in out
    assert "2026-07-17" in out


def test_stale_page_warns_the_reader(tmp_path: Path) -> None:
    _write_i18n_config(tmp_path)
    docs = tmp_path / "docs"
    _write_source(docs, "guide.md")

    out = hook.on_page_markdown(
        "# Перевод\n",
        page=FakePage({
            "language": "ru",
            "translation_of": "en/guide.md",
            "source_hash": "0" * 64,
            "translated_at": "2026-01-01",
        }),
        config=FakeConfig(docs),
    )

    assert "Translation out of date" in out
    assert "may no longer be accurate" in out


def test_page_without_source_hash_is_marked_unverifiable(tmp_path: Path) -> None:
    """Silence would imply the page is fine. It is unverifiable, not fine."""
    _write_i18n_config(tmp_path)
    docs = tmp_path / "docs"
    _write_source(docs, "guide.md")

    out = hook.on_page_markdown(
        "# Перевод\n",
        page=FakePage({"language": "ru", "translation_of": "en/guide.md"}),
        config=FakeConfig(docs),
    )

    assert "freshness unknown" in out


def test_missing_source_file_yields_unknown_not_a_crash(tmp_path: Path) -> None:
    _write_i18n_config(tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()

    out = hook.on_page_markdown(
        "# Перевод\n",
        page=FakePage({
            "language": "ru",
            "translation_of": "en/gone.md",
            "source_hash": "abc",
        }),
        config=FakeConfig(docs),
    )

    assert "freshness unknown" in out


# ---------------------------------------------------------------------------
# Pages that must never be touched
# ---------------------------------------------------------------------------

def test_source_language_page_is_untouched(tmp_path: Path) -> None:
    _write_i18n_config(tmp_path)
    docs = tmp_path / "docs"
    _write_source(docs, "guide.md")
    markdown = "# Source page\n"

    out = hook.on_page_markdown(
        markdown, page=FakePage({"language": "en"}), config=FakeConfig(docs)
    )

    assert out == markdown


def test_page_without_language_metadata_is_untouched(tmp_path: Path) -> None:
    _write_i18n_config(tmp_path)
    docs = tmp_path / "docs"
    _write_source(docs, "guide.md")
    markdown = "# Ordinary page\n"

    out = hook.on_page_markdown(
        markdown, page=FakePage({}), config=FakeConfig(docs)
    )

    assert out == markdown


def test_disabled_banner_leaves_markdown_alone(tmp_path: Path) -> None:
    _write_i18n_config(tmp_path, enabled=False)
    docs = tmp_path / "docs"
    source_hash = _write_source(docs, "guide.md")
    markdown = "# Перевод\n"

    out = hook.on_page_markdown(
        markdown,
        page=FakePage({
            "language": "ru",
            "translation_of": "en/guide.md",
            "source_hash": source_hash,
        }),
        config=FakeConfig(docs),
    )

    assert out == markdown


def test_show_when_fresh_false_hides_only_the_fresh_banner(tmp_path: Path) -> None:
    _write_i18n_config(tmp_path, show_when_fresh=False)
    docs = tmp_path / "docs"
    source_hash = _write_source(docs, "guide.md")
    meta = {
        "language": "ru",
        "translation_of": "en/guide.md",
        "source_hash": source_hash,
    }

    fresh = hook.on_page_markdown("# Перевод\n", page=FakePage(meta), config=FakeConfig(docs))
    stale = hook.on_page_markdown(
        "# Перевод\n",
        page=FakePage({**meta, "source_hash": "0" * 64}),
        config=FakeConfig(docs),
    )

    assert fresh == "# Перевод\n"
    assert "Translation out of date" in stale


# ---------------------------------------------------------------------------
# Source URL derivation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("translation_of,expected", [
    ("en/how-to/guide.md", "/how-to/guide/"),
    ("en/index.md", "/"),
    ("en/how-to/index.md", "/how-to/"),
    ("en/guide.md", "/guide/"),
])
def test_source_url_derivation(translation_of: str, expected: str) -> None:
    assert hook._source_url(translation_of, "en") == expected


@pytest.mark.parametrize("translation_of", ["ru/guide.md", "guide.md", "en/guide.txt"])
def test_source_url_returns_empty_when_underivable(translation_of: str) -> None:
    assert hook._source_url(translation_of, "en") == ""


def test_missing_i18n_config_falls_back_to_defaults(tmp_path: Path) -> None:
    """A docs build must never fail because of a banner."""
    docs = tmp_path / "docs"
    source_hash = _write_source(docs, "guide.md")

    out = hook.on_page_markdown(
        "# Перевод\n",
        page=FakePage({
            "language": "ru",
            "translation_of": "en/guide.md",
            "source_hash": source_hash,
        }),
        config=FakeConfig(docs),
    )

    assert "Translation up to date" in out

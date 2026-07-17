"""
MkDocs hook: per-language translation freshness indicator.

Renders a freshness banner at the top of every translated page, so the answer
to "which version is accurate right now" takes five seconds to find instead of
requiring someone to open a JSON report.

The banner is derived from the same content hash the drift gate uses: the
translation's `source_hash` frontmatter field is compared against a live
SHA-256 of the English source body. A page whose source changed one minute
ago is marked out of date immediately -- there is no cache and no schedule.

Three states are possible:

  fresh    The translation matches the current English source.
  stale    The English source changed after this page was translated.
  unknown  The page declares no source_hash, so freshness cannot be verified.

Wire it up in mkdocs.yml:

    hooks:
      - hooks/i18n_freshness.py

Behavior is configured under `freshness_banner` in i18n.yml.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml


_FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n?", re.DOTALL)

# Resolved once per build and reused across pages.
_CONFIG_CACHE: dict[str, Any] | None = None
_HASH_CACHE: dict[str, str] = {}

_DEFAULTS = {
    "enabled": True,
    "show_when_fresh": True,
    "show_when_unknown": True,
    "link_to_source": True,
}


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _load_config(config_path: str = "i18n.yml") -> dict[str, Any]:
    """Load banner settings and the default language from i18n.yml.

    Falls back to safe defaults when i18n.yml is absent or unreadable, so a
    misconfigured banner never breaks a docs build.

    Args:
        config_path: Path to i18n.yml.

    Returns:
        Mapping with 'default_language' and the resolved banner settings.
    """
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    resolved: dict[str, Any] = dict(_DEFAULTS)
    resolved["default_language"] = "en"

    path = Path(config_path)
    if path.exists():
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            raw = {}
        if isinstance(raw, dict):
            resolved["default_language"] = raw.get("default_language", "en")
            banner = raw.get("freshness_banner", {})
            if isinstance(banner, dict):
                for key in _DEFAULTS:
                    if key in banner:
                        resolved[key] = banner[key]

    _CONFIG_CACHE = resolved
    return resolved


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def _source_body_hash(source_path: Path) -> str:
    """SHA-256 of a source document body, excluding frontmatter.

    Mirrors i18n_utils.compute_content_hash exactly. The hook does not import
    it, because scripts/ is not guaranteed to be importable from the MkDocs
    build environment, and a docs build must not fail over a banner.

    Args:
        source_path: Path to the English source document.

    Returns:
        Hex-encoded SHA-256, or "" if the file cannot be read.
    """
    key = source_path.as_posix()
    if key in _HASH_CACHE:
        return _HASH_CACHE[key]

    try:
        text = source_path.read_text(encoding="utf-8")
    except OSError:
        _HASH_CACHE[key] = ""
        return ""

    body = _FRONTMATTER_RE.sub("", text, count=1).strip()
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    _HASH_CACHE[key] = digest
    return digest


# ---------------------------------------------------------------------------
# Banner rendering
# ---------------------------------------------------------------------------

def _source_url(translation_of: str, default_language: str) -> str:
    """Build the reader-facing URL of the English source page.

    Args:
        translation_of: Source path relative to docs/ (for example
            "en/how-to/guide.md").
        default_language: The default locale code.

    Returns:
        Site-absolute URL, or "" if it cannot be derived.
    """
    rel = translation_of.strip()
    prefix = f"{default_language}/"
    if not rel.startswith(prefix):
        return ""

    rel = rel[len(prefix):]
    if not rel.endswith(".md"):
        return ""
    rel = rel[: -len(".md")]

    if rel.endswith("/index"):
        rel = rel[: -len("index")]
        return f"/{rel}"
    if rel == "index":
        return "/"
    return f"/{rel}/"


def _render_banner(
    state: str,
    translated_at: str,
    source_url: str,
    settings: dict[str, Any],
) -> str:
    """Render the freshness admonition for a translated page.

    Args:
        state: One of "fresh", "stale", "unknown".
        translated_at: Date the translation was last verified, or "".
        source_url: URL of the English source page, or "".
        settings: Resolved banner settings.

    Returns:
        Markdown admonition block, or "" when this state is not shown.
    """
    link = ""
    if settings["link_to_source"] and source_url:
        link = f" [Read the English version]({source_url})."

    if state == "stale":
        verified = (
            f" This translation was last verified on {translated_at}."
            if translated_at else ""
        )
        return (
            '!!! warning "Translation out of date"\n'
            "    The English source has changed since this page was "
            "translated, so parts of it may no longer be accurate."
            f"{verified}"
            f"{link}\n"
        )

    if state == "unknown":
        if not settings["show_when_unknown"]:
            return ""
        return (
            '!!! warning "Translation freshness unknown"\n'
            "    This page does not record which version of the English "
            "source it was translated from, so it cannot be verified as "
            "current."
            f"{link}\n"
        )

    if not settings["show_when_fresh"]:
        return ""

    verified = f" as of {translated_at}" if translated_at else ""
    return (
        '!!! info "Translation up to date"\n'
        f"    This page matches the current English source{verified}."
        f"{link}\n"
    )


# ---------------------------------------------------------------------------
# MkDocs hook
# ---------------------------------------------------------------------------

def on_page_markdown(
    markdown: str,
    page: Any = None,
    config: Any = None,
    files: Any = None,
    **kwargs: Any,
) -> str:
    """Prepend a freshness banner to translated pages.

    Only pages that declare a `language` other than the default are touched,
    so the English build is never modified.

    Args:
        markdown: Page Markdown, frontmatter already stripped by MkDocs.
        page: The MkDocs page object.
        config: The MkDocs config object.
        files: The MkDocs file collection.

    Returns:
        Markdown with the banner prepended, or unchanged.
    """
    settings = _load_config()
    if not settings["enabled"] or page is None:
        return markdown

    meta = getattr(page, "meta", None) or {}
    language = str(meta.get("language", "")).strip()
    default_language = str(settings["default_language"])

    # Untranslated pages and the source language itself carry no banner.
    if not language or language == default_language:
        return markdown

    translation_of = str(meta.get("translation_of", "")).strip()
    stored_hash = str(meta.get("source_hash", "")).strip()
    translated_at = str(meta.get("translated_at", "")).strip()

    docs_dir = Path(getattr(config, "docs_dir", "docs")) if config else Path("docs")
    source_url = _source_url(translation_of, default_language)

    if not translation_of or not stored_hash:
        state = "unknown"
    else:
        current_hash = _source_body_hash(docs_dir / translation_of)
        if not current_hash:
            state = "unknown"
        else:
            state = "fresh" if current_hash == stored_hash else "stale"

    banner = _render_banner(state, translated_at, source_url, settings)
    if not banner:
        return markdown

    return f"{banner}\n{markdown}"

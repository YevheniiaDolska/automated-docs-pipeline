#!/usr/bin/env python3
"""
Shared i18n utilities for the documentation pipeline.

Provides configuration loading, content hashing, locale detection,
and locale-aware variable merging used by i18n_sync, i18n_translate,
i18n_migrate, and other pipeline scripts.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class LanguageConfig:
    """Configuration for a single language."""
    locale: str
    name: str
    build: bool = True
    seo_overrides: dict[str, Any] = field(default_factory=dict)


@dataclass
class TranslationConfig:
    """Auto-translation provider settings."""
    stale_threshold_days: int = 30
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    max_concurrency: int = 3
    temperature: float = 0.3


@dataclass
class I18nConfig:
    """Top-level i18n configuration loaded from i18n.yml."""
    default_language: str
    docs_structure: str
    languages: list[LanguageConfig]
    translation: TranslationConfig

    def get_language(self, locale: str) -> LanguageConfig | None:
        """Return LanguageConfig for a locale, or None if not configured."""
        for lang in self.languages:
            if lang.locale == locale:
                return lang
        return None

    @property
    def locales(self) -> list[str]:
        """Return list of all configured locale codes."""
        return [lang.locale for lang in self.languages]

    @property
    def build_locales(self) -> list[str]:
        """Return list of locale codes with build enabled."""
        return [lang.locale for lang in self.languages if lang.build]

    @property
    def target_locales(self) -> list[str]:
        """Return non-default locales (translation targets)."""
        return [loc for loc in self.locales if loc != self.default_language]


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_i18n_config(config_path: str | Path = "i18n.yml") -> I18nConfig:
    """Load and validate the i18n configuration file.

    Args:
        config_path: Path to i18n.yml.

    Returns:
        Parsed I18nConfig instance.

    Raises:
        FileNotFoundError: If config file does not exist.
        ValueError: If config is invalid.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"i18n config not found: {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("i18n.yml must be a YAML mapping")

    default_lang = raw.get("default_language")
    if not default_lang:
        raise ValueError("i18n.yml: 'default_language' is required")

    docs_structure = raw.get("docs_structure", "folder")
    if docs_structure != "folder":
        raise ValueError(f"i18n.yml: unsupported docs_structure '{docs_structure}' (only 'folder' is supported)")

    # Parse languages
    raw_languages = raw.get("languages", [])
    if not raw_languages:
        raise ValueError("i18n.yml: at least one language must be defined")

    languages: list[LanguageConfig] = []
    for entry in raw_languages:
        if not isinstance(entry, dict) or "locale" not in entry:
            raise ValueError(f"i18n.yml: each language must have a 'locale' field: {entry}")
        languages.append(LanguageConfig(
            locale=entry["locale"],
            name=entry.get("name", entry["locale"]),
            build=entry.get("build", True),
            seo_overrides=entry.get("seo_overrides", {}),
        ))

    # Validate default_language is in the list
    locale_codes = [lang.locale for lang in languages]
    if default_lang not in locale_codes:
        raise ValueError(
            f"i18n.yml: default_language '{default_lang}' "
            f"is not in languages list: {locale_codes}"
        )

    # Parse translation settings
    raw_trans = raw.get("translation", {})
    auto = raw_trans.get("auto_translate", {})
    translation = TranslationConfig(
        stale_threshold_days=raw_trans.get("stale_threshold_days", 30),
        provider=auto.get("provider", "anthropic"),
        model=auto.get("model", "claude-sonnet-4-20250514"),
        max_concurrency=auto.get("max_concurrency", 3),
        temperature=auto.get("temperature", 0.3),
    )

    return I18nConfig(
        default_language=default_lang,
        docs_structure=docs_structure,
        languages=languages,
        translation=translation,
    )


# ---------------------------------------------------------------------------
# Locale detection
# ---------------------------------------------------------------------------

def get_locale_from_path(filepath: str | Path, docs_dir: str | Path = "docs") -> str | None:
    """Extract the locale code from a file path under the docs directory.

    Assumes folder-based layout: docs/{locale}/...

    Args:
        filepath: Path to a documentation file.
        docs_dir: Root docs directory.

    Returns:
        Locale code (e.g. "en", "ru") or None if not detectable.
    """
    filepath = Path(filepath)
    docs_dir = Path(docs_dir)

    try:
        rel = filepath.relative_to(docs_dir)
    except ValueError:
        return None

    parts = rel.parts
    if not parts:
        return None

    # First directory component is the locale
    candidate = parts[0]
    # Validate it looks like a locale code (2-3 lowercase letters)
    if re.match(r"^[a-z]{2,3}$", candidate):
        return candidate
    return None


# ---------------------------------------------------------------------------
# Content hashing
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n?", re.DOTALL)


def compute_content_hash(filepath: str | Path) -> str:
    """Compute SHA-256 hash of the document body (excluding frontmatter).

    This hash is used to detect when source content changes so that
    translations can be flagged as stale.

    Args:
        filepath: Path to a Markdown file.

    Returns:
        Hex-encoded SHA-256 hash string.
    """
    text = Path(filepath).read_text(encoding="utf-8")
    # Strip frontmatter
    body = _FRONTMATTER_RE.sub("", text, count=1).strip()
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Variable merging
# ---------------------------------------------------------------------------

def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override dict into base dict.

    Values in override take precedence. Nested dicts are merged recursively.
    The base dict is not mutated; a new dict is returned.

    Args:
        base: Base dictionary.
        override: Override dictionary.

    Returns:
        New merged dictionary.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_variables_for_locale(
    locale: str,
    docs_dir: str | Path = "docs",
) -> dict:
    """Load and merge variables for a specific locale.

    Loads the base _variables.yml from docs/ and merges any
    locale-specific overrides from docs/{locale}/_variables.yml.

    Args:
        locale: Locale code (e.g. "en", "ru").
        docs_dir: Root docs directory.

    Returns:
        Merged variables dictionary.
    """
    docs_path = Path(docs_dir)
    base_path = docs_path / "_variables.yml"
    locale_path = docs_path / locale / "_variables.yml"

    base_vars: dict = {}
    if base_path.exists():
        base_vars = yaml.safe_load(base_path.read_text(encoding="utf-8")) or {}

    if locale_path.exists():
        locale_vars = yaml.safe_load(locale_path.read_text(encoding="utf-8")) or {}
        return deep_merge(base_vars, locale_vars)

    return base_vars


# ---------------------------------------------------------------------------
# Frontmatter helpers
# ---------------------------------------------------------------------------

def extract_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Extract frontmatter dict and body from Markdown text.

    Args:
        text: Full Markdown content.

    Returns:
        Tuple of (frontmatter_dict, body_string).
    """
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, parts[2]


def set_frontmatter_field(filepath: Path, field: str, value: Any) -> None:
    """Update a single frontmatter field in a Markdown file.

    Args:
        filepath: Path to the Markdown file.
        field: Frontmatter field name.
        value: New value.
    """
    text = filepath.read_text(encoding="utf-8")
    fm, body = extract_frontmatter(text)
    fm[field] = value
    yaml_str = yaml.dump(fm, default_flow_style=False, sort_keys=False, allow_unicode=True)
    filepath.write_text(f"---\n{yaml_str}---\n{body}", encoding="utf-8")

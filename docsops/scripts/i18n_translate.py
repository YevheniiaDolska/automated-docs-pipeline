#!/usr/bin/env python3
"""
Auto-translation via Claude API

Translates documentation files from the source locale to target locales
using the Anthropic API. Preserves Markdown structure, code blocks,
{{ variables }}, and link paths.

Usage:
    # Translate a single file
    python3 scripts/i18n_translate.py --source en/how-to/guide.md --locale ru

    # Translate all missing translations
    python3 scripts/i18n_translate.py --all-missing --locale ru

    # Update stale translations only
    python3 scripts/i18n_translate.py --stale-only --locale ru

    # Dry run (show what would be translated)
    python3 scripts/i18n_translate.py --all-missing --locale ru --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from pathlib import Path

import yaml

from i18n_utils import (
    I18nConfig,
    compute_content_hash,
    extract_frontmatter,
    load_i18n_config,
    load_variables_for_locale,
)
from i18n_sync import I18nSyncChecker


class DocumentTranslator:
    """Translates documentation files using the Anthropic Claude API."""

    def __init__(
        self,
        config: I18nConfig,
        docs_dir: str | Path = "docs",
    ):
        self.config = config
        self.docs_dir = Path(docs_dir)
        self._client = None

    def _get_client(self):
        """Lazy-initialize the Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic()
            except ImportError:
                print(
                    "Error: anthropic package is required for auto-translation.\n"
                    "Install it with: pip install anthropic",
                    file=sys.stderr,
                )
                sys.exit(1)
        return self._client

    def build_translation_prompt(
        self,
        source_content: str,
        source_locale: str,
        target_locale: str,
        target_language_name: str,
    ) -> str:
        """Build the translation prompt for Claude.

        The prompt instructs Claude to:
        - Translate prose and frontmatter title/description
        - Preserve code blocks exactly as-is
        - Preserve {{ variable }} placeholders
        - Preserve Markdown structure and link paths
        - Preserve frontmatter fields (except translated ones)

        Args:
            source_content: Full Markdown content including frontmatter.
            source_locale: Source locale code (e.g. "en").
            target_locale: Target locale code (e.g. "ru").
            target_language_name: Human-readable target language name.

        Returns:
            Complete prompt string.
        """
        return f"""You are a professional technical documentation translator.
Translate the following Markdown document from {source_locale} ({source_locale.upper()}) to {target_locale} ({target_language_name}).

CRITICAL RULES - you MUST follow all of these:

1. TRANSLATE these elements:
   - Regular prose text (paragraphs, list items, admonition text)
   - Frontmatter `title` field value
   - Frontmatter `description` field value
   - Heading text (after #, ##, ### etc.)
   - Alt text for images

2. DO NOT TRANSLATE - preserve exactly as-is:
   - Code blocks (everything between ``` markers)
   - Inline code (between ` markers)
   - {{{{ variable }}}} placeholders (Jinja2/MkDocs macros)
   - Link paths and URLs: [translated text](original/path.md)
   - Frontmatter field NAMES (title, description, content_type, tags, etc.)
   - Frontmatter values for: content_type, product, tags, status, language
   - HTML tags and attributes
   - Admonition type keywords (tip, warning, info, danger, note)
   - Tab labels in === "Label" syntax (keep as-is or translate only the label text)

3. FORMATTING RULES:
   - Keep all blank lines exactly where they are
   - Keep all heading levels (#, ##, ###) the same
   - Keep list markers (-, 1.) the same
   - Keep admonition syntax (!!! type "Title") - translate only the "Title" part
   - Keep content tab syntax (=== "Label") - translate only the "Label" part

4. QUALITY:
   - Use natural, fluent {target_language_name} - not word-for-word translation
   - Use the standard technical terminology for {target_language_name}
   - Keep the same tone (professional, direct, second person "you")
   - Maintain the same level of technical precision

5. OUTPUT:
   - Return ONLY the translated Markdown document
   - Include the full frontmatter block (with --- delimiters)
   - Do not add any commentary, notes, or explanations
   - Do not wrap the output in a code block

SOURCE DOCUMENT:

{source_content}"""

    def translate_document(
        self,
        source_content: str,
        source_locale: str,
        target_locale: str,
        target_language_name: str,
    ) -> str:
        """Translate a single document using Claude API.

        Args:
            source_content: Full Markdown content.
            source_locale: Source locale code.
            target_locale: Target locale code.
            target_language_name: Human-readable language name.

        Returns:
            Translated Markdown content.
        """
        client = self._get_client()
        prompt = self.build_translation_prompt(
            source_content, source_locale, target_locale, target_language_name
        )

        response = client.messages.create(
            model=self.config.translation.model,
            max_tokens=8192,
            temperature=self.config.translation.temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        translated = response.content[0].text

        # Post-process: ensure frontmatter has correct i18n fields
        translated = self._post_process(
            translated, source_locale, target_locale, source_content
        )

        return translated

    def _post_process(
        self,
        translated: str,
        source_locale: str,
        target_locale: str,
        source_content: str,
    ) -> str:
        """Post-process translated content to fix i18n frontmatter fields.

        Ensures language, translation_of, and source_hash are set correctly
        regardless of what the LLM produced.
        """
        fm, body = extract_frontmatter(translated)
        if not fm:
            return translated

        # Extract source relative path info from original frontmatter
        source_fm, _ = extract_frontmatter(source_content)

        # Set/override i18n fields
        fm["language"] = target_locale

        # Compute source hash from the source content body
        source_body = source_content
        if source_content.startswith("---"):
            parts = source_content.split("---", 2)
            if len(parts) >= 3:
                source_body = parts[2].strip()

        source_hash = hashlib.sha256(source_body.encode("utf-8")).hexdigest()
        fm["source_hash"] = source_hash

        # Rebuild the document
        yaml_str = yaml.dump(
            fm, default_flow_style=False, sort_keys=False, allow_unicode=True
        )
        return f"---\n{yaml_str}---\n{body}"

    def create_translation_from_source(
        self,
        source_rel_path: str,
        target_locale: str,
        dry_run: bool = False,
    ) -> Path | None:
        """High-level: translate a source doc and write the translation.

        Args:
            source_rel_path: Path relative to docs/ (e.g. "en/how-to/guide.md").
            target_locale: Target locale code.
            dry_run: If True, skip writing and API call.

        Returns:
            Path to the created translation file, or None on dry run.
        """
        source_path = self.docs_dir / source_rel_path
        if not source_path.exists():
            print(f"  Source not found: {source_path}", file=sys.stderr)
            return None

        # Determine target path
        # source_rel_path = "en/how-to/guide.md" -> "how-to/guide.md"
        source_locale = self.config.default_language
        rel_from_locale = str(
            Path(source_rel_path).relative_to(source_locale)
        )
        target_path = self.docs_dir / target_locale / rel_from_locale

        if dry_run:
            print(f"  [DRY RUN] Would translate: {source_rel_path} -> {target_path}")
            return None

        # Get target language name
        lang_config = self.config.get_language(target_locale)
        target_name = lang_config.name if lang_config else target_locale

        # Read source
        source_content = source_path.read_text(encoding="utf-8")

        print(f"  Translating: {source_rel_path} -> {target_locale}...")

        # Translate
        translated = self.translate_document(
            source_content, source_locale, target_locale, target_name
        )

        # Set translation_of in frontmatter
        fm, body = extract_frontmatter(translated)
        if fm:
            fm["translation_of"] = source_rel_path
            yaml_str = yaml.dump(
                fm, default_flow_style=False, sort_keys=False, allow_unicode=True
            )
            translated = f"---\n{yaml_str}---\n{body}"

        # Write
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(translated, encoding="utf-8")
        print(f"  Created: {target_path}")

        return target_path

    def translate_batch(
        self,
        items: list[tuple[str, str]],
        dry_run: bool = False,
    ) -> list[Path]:
        """Translate a batch of documents.

        Uses sequential processing (async with semaphore is available
        for future optimization).

        Args:
            items: List of (source_rel_path, target_locale) tuples.
            dry_run: If True, skip writing and API calls.

        Returns:
            List of created file paths.
        """
        results: list[Path] = []
        total = len(items)

        for i, (source_path, target_locale) in enumerate(items, 1):
            print(f"  [{i}/{total}]", end="")
            result = self.create_translation_from_source(
                source_path, target_locale, dry_run=dry_run
            )
            if result:
                results.append(result)

        return results


def _get_items_from_sync(
    config: I18nConfig,
    docs_dir: Path,
    locale: str | None = None,
    stale_only: bool = False,
) -> list[tuple[str, str]]:
    """Get translation items from sync report.

    Args:
        config: i18n configuration.
        docs_dir: Docs directory.
        locale: Specific target locale (or None for all).
        stale_only: If True, only return stale items.

    Returns:
        List of (source_rel_path, target_locale) tuples.
    """
    checker = I18nSyncChecker(config, docs_dir=docs_dir)
    report = checker.check_all()

    items: list[tuple[str, str]] = []
    for item in report.items:
        if locale and item.target_locale != locale:
            continue
        if stale_only and item.status != "stale":
            continue
        if not stale_only and item.status not in ("missing", "stale"):
            continue
        items.append((item.source_path, item.target_locale))

    return items


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auto-translate documentation using Claude API"
    )
    parser.add_argument(
        "--config",
        default="i18n.yml",
        help="Path to i18n.yml (default: i18n.yml)",
    )
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Documentation root directory (default: docs)",
    )
    parser.add_argument(
        "--source",
        help="Source file path relative to docs/ (e.g. en/how-to/guide.md)",
    )
    parser.add_argument(
        "--locale",
        help="Target locale code (e.g. ru, de)",
    )
    parser.add_argument(
        "--all-missing",
        action="store_true",
        help="Translate all missing translations",
    )
    parser.add_argument(
        "--stale-only",
        action="store_true",
        help="Re-translate only stale translations",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be translated without making API calls",
    )
    args = parser.parse_args()

    try:
        config = load_i18n_config(args.config)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    docs_dir = Path(args.docs_dir)
    translator = DocumentTranslator(config, docs_dir=docs_dir)

    if args.source:
        # Single file translation
        if not args.locale:
            print("Error: --locale is required with --source", file=sys.stderr)
            sys.exit(1)
        translator.create_translation_from_source(
            args.source, args.locale, dry_run=args.dry_run
        )
    elif args.all_missing or args.stale_only:
        # Batch translation from sync report
        items = _get_items_from_sync(
            config, docs_dir, locale=args.locale, stale_only=args.stale_only
        )
        if not items:
            print("No items to translate.")
            sys.exit(0)

        print(f"Found {len(items)} items to translate:")
        results = translator.translate_batch(items, dry_run=args.dry_run)
        print(f"\nTranslated {len(results)} documents.")
    else:
        print(
            "Error: specify --source, --all-missing, or --stale-only",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

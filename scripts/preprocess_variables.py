#!/usr/bin/env python3
"""
Variable Preprocessor for Docusaurus

Replaces {{ variable }} placeholders in markdown files with values from
_variables.yml. This is the Docusaurus equivalent of the MkDocs macros plugin.

Supports i18n: when a locale is specified (or auto-detected from path),
locale-specific variable overrides from docs/{locale}/_variables.yml are
merged on top of the base variables.

Can be run as a pre-build step or on individual files.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml


def load_variables(variables_path: Path) -> dict:
    """Load variables from a YAML file."""
    if not variables_path.exists():
        return {}
    text = variables_path.read_text(encoding="utf-8")
    return yaml.safe_load(text) or {}


def load_variables_for_locale(
    locale: str | None,
    docs_dir: Path,
    base_vars: dict | None = None,
) -> dict:
    """Load and merge variables for a specific locale.

    Args:
        locale: Locale code (e.g. "en", "ru") or None for base only.
        docs_dir: Root docs directory.
        base_vars: Pre-loaded base variables (optimization). Loaded if None.

    Returns:
        Merged variables dictionary.
    """
    if base_vars is None:
        base_vars = load_variables(docs_dir / "_variables.yml")
    if not locale:
        return base_vars

    locale_path = docs_dir / locale / "_variables.yml"
    if not locale_path.exists():
        return base_vars

    locale_vars = yaml.safe_load(locale_path.read_text(encoding="utf-8")) or {}

    # Deep merge: locale overrides base
    result = base_vars.copy()
    for key, value in locale_vars.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            merged = result[key].copy()
            merged.update(value)
            result[key] = merged
        else:
            result[key] = value
    return result


def _detect_locale(filepath: Path, docs_dir: Path) -> str | None:
    """Detect locale from file path (docs/{locale}/...)."""
    try:
        rel = filepath.relative_to(docs_dir)
    except ValueError:
        return None
    parts = rel.parts
    if parts and re.match(r"^[a-z]{2,3}$", parts[0]):
        return parts[0]
    return None


def _flatten_dict(d: dict, prefix: str = "") -> dict[str, str]:
    """Flatten nested dict into dot-notation keys.

    {'env_vars': {'port': 'N8N_PORT'}} -> {'env_vars.port': 'N8N_PORT'}
    """
    flat: dict[str, str] = {}
    for key, value in d.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(_flatten_dict(value, full_key))
        else:
            flat[full_key] = str(value)
    return flat


def replace_variables(content: str, variables: dict) -> str:
    """Replace {{ variable }} and {{ nested.variable }} placeholders.

    Only replaces outside of fenced code blocks (``` ... ```).
    """
    flat = _flatten_dict(variables)
    # Also add top-level non-dict values directly
    for key, value in variables.items():
        if not isinstance(value, dict):
            flat[key] = str(value)

    lines = content.split("\n")
    output: list[str] = []
    in_fence = False
    fence_marker: str | None = None

    for line in lines:
        # Track fenced code blocks
        stripped = line.strip()
        if not in_fence:
            m = re.match(r"^(`{3,}|~{3,})", stripped)
            if m:
                in_fence = True
                fence_marker = m.group(1)
                output.append(line)
                continue
        else:
            if stripped == fence_marker or stripped.startswith(fence_marker or ""):
                in_fence = False
                fence_marker = None
            output.append(line)
            continue

        # Replace {{ variable }} patterns
        def _replace(match: re.Match) -> str:
            var_name = match.group(1).strip()
            return flat.get(var_name, match.group(0))

        processed = re.sub(r"\{\{\s*([^}]+?)\s*\}\}", _replace, line)
        output.append(processed)

    return "\n".join(output)


def preprocess_directory(
    docs_dir: Path,
    variables: dict,
    output_dir: Path | None = None,
    locale_aware: bool = False,
) -> list[Path]:
    """Replace variables in all markdown files in a directory.

    Args:
        docs_dir: Source documentation directory.
        variables: Base variable dict from _variables.yml.
        output_dir: Where to write processed files. If None, writes in-place.
        locale_aware: If True, auto-detect locale per file and merge
            locale-specific variable overrides.

    Returns:
        List of processed file paths.
    """
    out_path = output_dir if output_dir else docs_dir
    processed: list[Path] = []

    # Cache locale-specific variable sets
    locale_vars_cache: dict[str | None, dict] = {None: variables}

    for md_file in sorted(docs_dir.rglob("*.md")):
        if md_file.name.startswith("_"):
            continue

        # Determine which variables to use
        file_vars = variables
        if locale_aware:
            locale = _detect_locale(md_file, docs_dir)
            if locale not in locale_vars_cache:
                locale_vars_cache[locale] = load_variables_for_locale(
                    locale, docs_dir, base_vars=variables
                )
            file_vars = locale_vars_cache[locale]

        content = md_file.read_text(encoding="utf-8")
        result = replace_variables(content, file_vars)

        rel = md_file.relative_to(docs_dir)
        dest = out_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(result, encoding="utf-8")
        processed.append(dest)

    return processed


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Preprocess {{ variable }} placeholders for Docusaurus"
    )
    parser.add_argument(
        "source",
        help="Source file or directory",
    )
    parser.add_argument(
        "--variables",
        default="docs/_variables.yml",
        help="Path to _variables.yml (default: docs/_variables.yml)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file or directory (default: in-place)",
    )
    parser.add_argument(
        "--locale-aware",
        action="store_true",
        help="Auto-detect locale per file and merge locale-specific variables",
    )

    args = parser.parse_args()
    source = Path(args.source)
    variables = load_variables(Path(args.variables))

    if source.is_file():
        # For single file, detect locale if locale-aware mode
        file_vars = variables
        if args.locale_aware:
            docs_dir = Path(args.variables).parent
            locale = _detect_locale(source, docs_dir)
            file_vars = load_variables_for_locale(locale, docs_dir, base_vars=variables)

        content = source.read_text(encoding="utf-8")
        result = replace_variables(content, file_vars)
        if args.output:
            Path(args.output).write_text(result, encoding="utf-8")
            print(f"Processed: {args.output}")
        else:
            source.write_text(result, encoding="utf-8")
            print(f"Processed in-place: {source}")
    elif source.is_dir():
        out = Path(args.output) if args.output else None
        files = preprocess_directory(
            source, variables, out, locale_aware=args.locale_aware
        )
        print(f"Processed {len(files)} files")
    else:
        print(f"Error: {source} does not exist")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

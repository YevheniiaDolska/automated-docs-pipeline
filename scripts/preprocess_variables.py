#!/usr/bin/env python3
"""
Variable Preprocessor for Docusaurus

Replaces {{ variable }} placeholders in markdown files with values from
_variables.yml. This is the Docusaurus equivalent of the MkDocs macros plugin.

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
) -> list[Path]:
    """Replace variables in all markdown files in a directory.

    Args:
        docs_dir: Source documentation directory.
        variables: Variable dict from _variables.yml.
        output_dir: Where to write processed files. If None, writes in-place.

    Returns:
        List of processed file paths.
    """
    out_path = output_dir if output_dir else docs_dir
    processed: list[Path] = []

    for md_file in sorted(docs_dir.rglob("*.md")):
        if md_file.name.startswith("_"):
            continue

        content = md_file.read_text(encoding="utf-8")
        result = replace_variables(content, variables)

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

    args = parser.parse_args()
    source = Path(args.source)
    variables = load_variables(Path(args.variables))

    if source.is_file():
        content = source.read_text(encoding="utf-8")
        result = replace_variables(content, variables)
        if args.output:
            Path(args.output).write_text(result, encoding="utf-8")
            print(f"Processed: {args.output}")
        else:
            source.write_text(result, encoding="utf-8")
            print(f"Processed in-place: {source}")
    elif source.is_dir():
        out = Path(args.output) if args.output else None
        files = preprocess_directory(source, variables, out)
        print(f"Processed {len(files)} files")
    else:
        print(f"Error: {source} does not exist")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate facets-index.json for client-side faceted search.
Configurable for any project - reads frontmatter fields dynamically.
"""

import json
import yaml
from pathlib import Path
import sys
import re

def extract_frontmatter(file_path):
    """Extract frontmatter from a markdown file."""
    try:
        text = file_path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return None

        parts = text.split("---", 2)
        if len(parts) < 3:
            return None

        try:
            return yaml.safe_load(parts[1])
        except yaml.YAMLError:
            return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return None

def extract_first_paragraph(content):
    """Extract first meaningful paragraph as snippet."""
    lines = content.strip().split("\n")
    snippet_lines = []
    started = False

    for line in lines:
        stripped = line.strip()

        # Skip empty lines until we start
        if not stripped:
            if started:
                break
            continue

        # Skip headings
        if stripped.startswith("#"):
            started = True
            continue

        # Skip admonitions
        if stripped.startswith("!!!") or stripped.startswith("???"):
            continue

        # Skip tabs
        if stripped.startswith("==="):
            continue

        # Collect actual content
        snippet_lines.append(stripped)
        started = True

        # Stop at reasonable length
        if len(" ".join(snippet_lines)) > 150:
            break

    snippet = " ".join(snippet_lines)[:200]
    # Clean up snippet
    snippet = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', snippet)  # Remove links
    snippet = re.sub(r'`([^`]+)`', r'\1', snippet)  # Remove inline code
    snippet = re.sub(r'\*+([^\*]+)\*+', r'\1', snippet)  # Remove emphasis

    return snippet

def build_url_from_path(file_path, docs_dir):
    """Build URL path following MkDocs conventions."""
    rel_path = file_path.relative_to(docs_dir)

    # Handle index.md files
    if rel_path.name == "index.md":
        url = str(rel_path.parent) + "/"
    else:
        url = str(rel_path).replace(".md", "/")

    # Normalize path separators
    url = url.replace("\\", "/")

    # Clean up root index
    if url == "./":
        url = ""

    return url

def generate_facets_index(docs_dir="docs", output_file="docs/assets/facets-index.json"):
    """
    Generate facets index from all markdown files.
    Automatically discovers facet fields from frontmatter.
    """
    docs_path = Path(docs_dir)
    if not docs_path.exists():
        print(f"Error: Directory {docs_dir} does not exist", file=sys.stderr)
        return False

    index = []
    facet_fields = set()  # Track all unique facet fields

    # Scan all markdown files
    for md_file in sorted(docs_path.rglob("*.md")):
        # Skip private files
        if md_file.name.startswith("_"):
            continue

        # Read file
        text = md_file.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue

        # Parse frontmatter
        parts = text.split("---", 2)
        if len(parts) < 3:
            continue

        frontmatter = extract_frontmatter(md_file)
        if not frontmatter:
            continue

        # Check document status for deprecated/removed handling
        status = frontmatter.get("status", "active")

        # Skip removed documents entirely from search
        if status == "removed":
            continue

        # Build URL
        url = build_url_from_path(md_file, docs_path)

        # Extract snippet from content
        content = parts[2].strip() if len(parts) > 2 else ""
        snippet = extract_first_paragraph(content)

        # Build entry with all frontmatter fields (configurable)
        entry = {
            "title": frontmatter.get("title", ""),
            "description": frontmatter.get("description", ""),
            "url": url,
            "snippet": snippet,
            "status": status
        }

        # Mark deprecated documents in title and lower their priority
        if status == "deprecated":
            entry["title"] = f"[DEPRECATED] {entry['title']}"
            entry["search_priority"] = -1  # Lower ranking in search
            # Add replacement URL if available
            if "replacement_url" in frontmatter:
                entry["replacement_url"] = frontmatter["replacement_url"]
        else:
            entry["search_priority"] = 0  # Normal ranking

        # Add all frontmatter fields as potential facets
        # This makes it work for any project structure
        for key, value in frontmatter.items():
            if key not in ["title", "description", "status"]:
                entry[key] = value
                facet_fields.add(key)

        index.append(entry)

    # Create output directory if needed
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write index
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"Generated {output_path} with {len(index)} entries")

    # Report discovered facets for debugging
    if facet_fields:
        print(f"Discovered facet fields: {', '.join(sorted(facet_fields))}")

    return True

def main():
    """CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate facets index for client-side search")
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Documentation directory (default: docs)"
    )
    parser.add_argument(
        "--output",
        default="docs/assets/facets-index.json",
        help="Output file path (default: docs/assets/facets-index.json)"
    )

    args = parser.parse_args()

    success = generate_facets_index(args.docs_dir, args.output)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

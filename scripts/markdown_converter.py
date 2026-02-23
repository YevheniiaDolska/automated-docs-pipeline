#!/usr/bin/env python3
"""
Bidirectional Markdown Converter: MkDocs <-> Docusaurus

Converts MkDocs Material markdown extensions to Docusaurus MDX equivalents
and vice versa. Handles admonitions, content tabs, collapsible sections,
and variable placeholders.

Tracks fenced code block state to avoid converting syntax inside code.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

# ---------------------------------------------------------------------------
# Admonition type mapping (MkDocs -> Docusaurus)
# ---------------------------------------------------------------------------
ADMONITION_MAP = {
    "note": "note",
    "abstract": "note",
    "info": "info",
    "tip": "tip",
    "success": "tip",
    "question": "info",
    "warning": "warning",
    "failure": "danger",
    "danger": "danger",
    "bug": "danger",
    "example": "info",
    "quote": "note",
    "caution": "caution",
}

REVERSE_ADMONITION_MAP = {v: v for v in set(ADMONITION_MAP.values())}

# Regex patterns
_FENCE_RE = re.compile(r"^(`{3,}|~{3,})")
_ADMONITION_RE = re.compile(
    r'^(!{3}|[?]{3})\s+(\w+)(?:\s+"([^"]*)")?\s*$'
)
_TAB_RE = re.compile(r'^===\s+"([^"]+)"\s*$')
_DOCUSAURUS_ADMONITION_OPEN_RE = re.compile(
    r"^:::(\w+)(?:\[([^\]]*)\])?\s*$"
)
_DOCUSAURUS_ADMONITION_CLOSE_RE = re.compile(r"^:::\s*$")


# ---------------------------------------------------------------------------
# Helper: code-fence state tracking
# ---------------------------------------------------------------------------
def _is_fence_toggle(line: str, fence_marker: str | None) -> tuple[bool, str | None]:
    """Check if a line opens or closes a fenced code block.

    Returns (toggled, current_fence_marker).
    """
    m = _FENCE_RE.match(line)
    if m:
        marker = m.group(1)
        if fence_marker is None:
            return True, marker
        if line.rstrip() == fence_marker or line.startswith(fence_marker):
            return True, None
    return False, fence_marker


# ---------------------------------------------------------------------------
# MkDocs -> Docusaurus
# ---------------------------------------------------------------------------

def _collect_indented_block(lines: list[str], start: int) -> tuple[list[str], int]:
    """Collect consecutive 4-space-indented lines starting from *start*.

    Returns (content_lines_dedented, next_index).
    """
    block: list[str] = []
    idx = start
    while idx < len(lines):
        raw = lines[idx]
        # Blank lines inside the block are kept
        if raw.strip() == "":
            block.append("")
            idx += 1
            continue
        if raw.startswith("    "):
            block.append(raw[4:])
            idx += 1
        else:
            break
    # Trim trailing blank lines
    while block and block[-1] == "":
        block.pop()
    return block, idx


def _convert_admonition_mkdocs_to_docusaurus(
    kind: str, adm_type: str, title: str | None, body: list[str]
) -> list[str]:
    """Convert a single admonition / collapsible block."""
    mapped = ADMONITION_MAP.get(adm_type, "note")

    if kind == "???":
        # Collapsible -> <details>
        summary = title or mapped.capitalize()
        result = [f"<details><summary>{summary}</summary>", ""]
        result.extend(body)
        result.append("")
        result.append("</details>")
        return result

    # Regular admonition -> ::: directive
    if title:
        result = [f":::{mapped}[{title}]"]
    else:
        result = [f":::{mapped}"]
    result.extend(body)
    result.append(":::")
    return result


def _convert_tabs_mkdocs_to_docusaurus(tabs: list[tuple[str, list[str]]]) -> list[str]:
    """Convert a group of MkDocs content tabs to Docusaurus Tabs/TabItem."""
    result: list[str] = []
    result.append("<Tabs>")
    for idx, (label, body) in enumerate(tabs):
        value = f"t{idx}"
        result.append(f'<TabItem value="{value}" label="{label}">')
        result.append("")
        result.extend(body)
        result.append("")
        result.append("</TabItem>")
    result.append("</Tabs>")
    return result


def mkdocs_to_docusaurus(content: str) -> str:
    """Convert MkDocs Material markdown to Docusaurus MDX."""
    lines = content.split("\n")
    output: list[str] = []
    fence: str | None = None
    needs_tabs_import = False
    idx = 0

    while idx < len(lines):
        line = lines[idx]

        # Track fenced code blocks
        toggled, fence = _is_fence_toggle(line, fence)
        if fence is not None and not toggled:
            # Inside a code block -- pass through
            output.append(line)
            idx += 1
            continue
        if toggled and fence is not None:
            # Just opened a fence
            output.append(line)
            idx += 1
            continue
        if toggled and fence is None:
            # Just closed a fence
            output.append(line)
            idx += 1
            continue

        # Admonition detection
        adm_match = _ADMONITION_RE.match(line)
        if adm_match:
            kind = adm_match.group(1)  # !!! or ???
            adm_type = adm_match.group(2)
            title = adm_match.group(3)  # may be None
            idx += 1
            body, idx = _collect_indented_block(lines, idx)
            converted = _convert_admonition_mkdocs_to_docusaurus(
                kind, adm_type, title, body
            )
            output.extend(converted)
            continue

        # Tab detection
        tab_match = _TAB_RE.match(line)
        if tab_match:
            tabs: list[tuple[str, list[str]]] = []
            while idx < len(lines):
                tm = _TAB_RE.match(lines[idx])
                if not tm:
                    break
                label = tm.group(1)
                idx += 1
                body, idx = _collect_indented_block(lines, idx)
                tabs.append((label, body))
                # Skip blank lines between tabs
                while idx < len(lines) and lines[idx].strip() == "":
                    tab_peek = idx + 1
                    if tab_peek < len(lines) and _TAB_RE.match(lines[tab_peek]):
                        idx += 1
                        break
                    elif tab_peek < len(lines) and _TAB_RE.match(lines[idx]):
                        break
                    else:
                        break
            if tabs:
                needs_tabs_import = True
                output.extend(_convert_tabs_mkdocs_to_docusaurus(tabs))
            continue

        # Regular line
        output.append(line)
        idx += 1

    # Add MDX imports at the top if tabs were used
    if needs_tabs_import:
        import_lines = [
            "import Tabs from '@theme/Tabs';",
            "import TabItem from '@theme/TabItem';",
            "",
        ]
        # Insert after frontmatter if present
        insert_at = 0
        if output and output[0].strip() == "---":
            # Find closing ---
            for i in range(1, len(output)):
                if output[i].strip() == "---":
                    insert_at = i + 1
                    break
        # Insert blank line + imports
        for j, imp_line in enumerate(import_lines):
            output.insert(insert_at + j, imp_line)

    return "\n".join(output)


# ---------------------------------------------------------------------------
# Docusaurus -> MkDocs
# ---------------------------------------------------------------------------

def _convert_admonition_docusaurus_to_mkdocs(
    adm_type: str, title: str | None, body: list[str]
) -> list[str]:
    """Convert a Docusaurus ::: admonition to MkDocs !!! admonition."""
    mapped = adm_type if adm_type in ADMONITION_MAP else "note"
    if title:
        header = f'!!! {mapped} "{title}"'
    else:
        header = f"!!! {mapped}"

    result = [header]
    if not body:
        result.append("    ")
    else:
        for b in body:
            result.append(f"    {b}" if b.strip() else "")
    return result


def docusaurus_to_mkdocs(content: str) -> str:
    """Convert Docusaurus MDX markdown to MkDocs Material format."""
    lines = content.split("\n")
    output: list[str] = []
    fence: str | None = None
    idx = 0

    while idx < len(lines):
        line = lines[idx]

        # Track fenced code blocks
        toggled, fence = _is_fence_toggle(line, fence)
        if fence is not None and not toggled:
            output.append(line)
            idx += 1
            continue
        if toggled and fence is not None:
            output.append(line)
            idx += 1
            continue
        if toggled and fence is None:
            output.append(line)
            idx += 1
            continue

        # Skip Tabs/TabItem imports
        if line.strip().startswith("import Tabs from") or line.strip().startswith(
            "import TabItem from"
        ):
            idx += 1
            continue

        # Docusaurus admonition opening
        adm_open = _DOCUSAURUS_ADMONITION_OPEN_RE.match(line)
        if adm_open:
            adm_type = adm_open.group(1)
            title = adm_open.group(2)
            idx += 1
            body: list[str] = []
            while idx < len(lines):
                if _DOCUSAURUS_ADMONITION_CLOSE_RE.match(lines[idx]):
                    idx += 1
                    break
                body.append(lines[idx])
                idx += 1
            converted = _convert_admonition_docusaurus_to_mkdocs(
                adm_type, title, body
            )
            output.extend(converted)
            continue

        # <details> -> ??? collapsible
        if line.strip().startswith("<details>"):
            # Extract summary
            summary_match = re.search(r"<summary>(.*?)</summary>", line)
            title = summary_match.group(1) if summary_match else None
            idx += 1
            # Check next line for <summary>
            if not title and idx < len(lines):
                sm = re.search(r"<summary>(.*?)</summary>", lines[idx])
                if sm:
                    title = sm.group(1)
                    idx += 1
            body = []
            while idx < len(lines):
                if lines[idx].strip() == "</details>":
                    idx += 1
                    break
                body.append(lines[idx])
                idx += 1
            # Trim surrounding blank lines
            while body and body[0].strip() == "":
                body.pop(0)
            while body and body[-1].strip() == "":
                body.pop()
            header = f'??? note "{title}"' if title else "??? note"
            output.append(header)
            for b in body:
                output.append(f"    {b}" if b.strip() else "")
            continue

        # <Tabs> -> === content tabs
        if line.strip() == "<Tabs>":
            idx += 1
            tabs: list[tuple[str, list[str]]] = []
            while idx < len(lines):
                stripped = lines[idx].strip()
                if stripped == "</Tabs>":
                    idx += 1
                    break
                tab_open = re.match(
                    r'<TabItem\s+value="[^"]*"\s+label="([^"]*)">', stripped
                )
                if tab_open:
                    label = tab_open.group(1)
                    idx += 1
                    body = []
                    while idx < len(lines):
                        if lines[idx].strip() == "</TabItem>":
                            idx += 1
                            break
                        body.append(lines[idx])
                        idx += 1
                    # Trim surrounding blank lines
                    while body and body[0].strip() == "":
                        body.pop(0)
                    while body and body[-1].strip() == "":
                        body.pop()
                    tabs.append((label, body))
                else:
                    idx += 1

            for label, body in tabs:
                output.append(f'=== "{label}"')
                output.append("")
                for b in body:
                    output.append(f"    {b}" if b.strip() else "")
                output.append("")
            continue

        output.append(line)
        idx += 1

    return "\n".join(output)


# ---------------------------------------------------------------------------
# Directory-level conversion
# ---------------------------------------------------------------------------

def convert_directory(
    docs_dir: str | Path,
    target: str,
    output_dir: str | Path | None = None,
) -> list[Path]:
    """Convert all markdown files in a directory.

    Args:
        docs_dir: Source documentation directory.
        target: Either 'docusaurus' or 'mkdocs'.
        output_dir: Where to write converted files. If None, writes in-place.

    Returns:
        List of converted file paths.
    """
    docs_path = Path(docs_dir)
    out_path = Path(output_dir) if output_dir else docs_path

    if target not in ("docusaurus", "mkdocs"):
        raise ValueError(f"target must be 'docusaurus' or 'mkdocs', got '{target}'")

    converter = mkdocs_to_docusaurus if target == "docusaurus" else docusaurus_to_mkdocs
    converted: list[Path] = []

    for md_file in sorted(docs_path.rglob("*.md")):
        if md_file.name.startswith("_"):
            continue

        content = md_file.read_text(encoding="utf-8")
        result = converter(content)

        rel = md_file.relative_to(docs_path)
        dest = out_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(result, encoding="utf-8")
        converted.append(dest)

    return converted


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert markdown between MkDocs and Docusaurus formats"
    )
    parser.add_argument(
        "direction",
        choices=["to-docusaurus", "to-mkdocs"],
        help="Conversion direction",
    )
    parser.add_argument(
        "source",
        help="Source file or directory",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file or directory (default: stdout for files, in-place for dirs)",
    )

    args = parser.parse_args()
    source = Path(args.source)

    if source.is_file():
        content = source.read_text(encoding="utf-8")
        if args.direction == "to-docusaurus":
            result = mkdocs_to_docusaurus(content)
        else:
            result = docusaurus_to_mkdocs(content)

        if args.output:
            Path(args.output).write_text(result, encoding="utf-8")
            print(f"Converted: {args.output}")
        else:
            print(result)
    elif source.is_dir():
        target = "docusaurus" if args.direction == "to-docusaurus" else "mkdocs"
        files = convert_directory(source, target, args.output)
        print(f"Converted {len(files)} files")
    else:
        print(f"Error: {source} does not exist")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

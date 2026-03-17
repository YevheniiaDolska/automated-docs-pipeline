#!/usr/bin/env python3
"""Import Confluence export ZIP into Markdown docs."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

from confluence_converter import ConfluenceToMarkdownConverter


@dataclass
class ConfluencePage:
    """Confluence page extracted from entities.xml."""

    id: str
    title: str
    content: str
    space: str = ""
    parent_id: str | None = None
    created: str | None = None
    modified: str | None = None
    author: str = ""


@dataclass
class ImportResult:
    """Confluence import result summary."""

    source_zip: str
    output_dir: str
    total_pages: int = 0
    imported_pages: int = 0
    failed_pages: int = 0
    failed_titles: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    generated_files: list[str] = field(default_factory=list)


class ConfluenceImporter:
    """Confluence ZIP importer for docsops workflows."""

    def __init__(self) -> None:
        self.converter = ConfluenceToMarkdownConverter()

    def import_export(self, export_zip: Path, output_dir: Path) -> ImportResult:
        if not export_zip.exists():
            raise FileNotFoundError(f"Confluence export not found: {export_zip}")

        output_dir.mkdir(parents=True, exist_ok=True)

        result = ImportResult(
            source_zip=str(export_zip),
            output_dir=str(output_dir),
        )

        pages = self._parse_export(export_zip)
        result.total_pages = len(pages)

        for page in pages:
            try:
                file_path = output_dir / f"{self._safe_filename(page.title)}.md"
                markdown = self.converter.convert(page.content)
                frontmatter = self._build_frontmatter(page, markdown)
                full_doc = f"{frontmatter}\n\n# {page.title}\n\n{markdown}\n"
                file_path.write_text(full_doc, encoding="utf-8")
                result.generated_files.append(str(file_path))
                result.imported_pages += 1
            except Exception as exc:
                result.failed_pages += 1
                result.failed_titles.append(page.title)
                result.warnings.append(f"Failed page '{page.title}': {exc}")

        if result.imported_pages == 0 and result.total_pages > 0:
            result.warnings.append("No pages were successfully imported.")

        return result

    def _parse_export(self, export_zip: Path) -> list[ConfluencePage]:
        with zipfile.ZipFile(export_zip) as archive:
            xml_name = self._find_entities_xml(archive)
            xml_content = archive.read(xml_name)

        root = ET.fromstring(xml_content)
        page_elements = root.findall('.//object[@class="Page"]')
        pages: list[ConfluencePage] = []

        for elem in page_elements:
            page_id = self._read_id(elem)
            title = self._read_property(elem, "title") or "Untitled"
            content = self._read_property(elem, "bodyContent") or ""
            pages.append(
                ConfluencePage(
                    id=page_id,
                    title=title,
                    content=content,
                    space=self._read_property(elem, "spaceKey") or "",
                    parent_id=self._read_property(elem, "parent"),
                    created=self._read_property(elem, "creationDate"),
                    modified=self._read_property(elem, "lastModificationDate"),
                    author=self._read_property(elem, "creator") or "",
                )
            )

        return pages

    def _find_entities_xml(self, archive: zipfile.ZipFile) -> str:
        for name in archive.namelist():
            if name.endswith("entities.xml"):
                return name
        raise ValueError("Confluence export ZIP does not contain entities.xml")

    def _read_id(self, elem: ET.Element) -> str:
        id_elem = elem.find("id")
        return id_elem.text if id_elem is not None and id_elem.text else ""

    def _read_property(self, elem: ET.Element, name: str) -> str | None:
        for prop in elem.findall("property"):
            if prop.get("name") == name:
                return prop.text
        return None

    def _safe_filename(self, title: str) -> str:
        slug = title.lower().strip()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"\s+", "-", slug)
        slug = re.sub(r"-+", "-", slug)
        return slug[:120].strip("-") or "untitled-page"

    def _guess_content_type(self, title: str, markdown: str) -> str:
        title_lower = title.lower()
        if any(token in title_lower for token in ["troubleshoot", "error", "fail", "issue"]):
            return "troubleshooting"
        if any(token in title_lower for token in ["api", "endpoint", "reference", "parameter"]):
            return "reference"
        if any(token in title_lower for token in ["how to", "setup", "configure", "install"]):
            return "how-to"
        if len(markdown.splitlines()) > 40:
            return "concept"
        return "how-to"

    def _build_frontmatter(self, page: ConfluencePage, markdown: str) -> str:
        content_type = self._guess_content_type(page.title, markdown)
        summary = self._make_summary(page.title, markdown)
        tags = ["Migration", "Confluence", content_type.capitalize()]

        lines = [
            "---",
            f'title: "{self._escape_yaml(page.title)}"',
            f'description: "{self._escape_yaml(summary)}"',
            f"content_type: {content_type}",
            "product: both",
            "language: en",
            "tags:",
        ]
        for tag in tags:
            lines.append(f"  - {tag}")

        if page.id:
            lines.append(f'confluence_id: "{self._escape_yaml(page.id)}"')
        if page.space:
            lines.append(f'confluence_space: "{self._escape_yaml(page.space)}"')
        if page.parent_id:
            lines.append(f'confluence_parent_id: "{self._escape_yaml(page.parent_id)}"')
        if page.author:
            lines.append(f'confluence_author: "{self._escape_yaml(page.author)}"')
        if page.modified:
            lines.append(f'last_modified: "{self._escape_yaml(page.modified[:10])}"')

        lines.append("---")
        return "\n".join(lines)

    def _make_summary(self, title: str, markdown: str) -> str:
        clean = " ".join(markdown.replace("\n", " ").split())
        if not clean:
            clean = f"Migrated from Confluence: {title}."
        summary = clean[:180].rstrip()
        if len(summary) < 50:
            summary = (summary + " This page was migrated from Confluence and requires review.")[:180]
        return summary

    def _escape_yaml(self, value: str) -> str:
        return value.replace('"', "'")

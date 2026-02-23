#!/usr/bin/env python3
"""
Site Generator Abstraction Layer

Provides a unified interface for MkDocs and Docusaurus site generators.
Auto-detects the generator from project files or accepts explicit selection.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from pathlib import Path


class SiteGenerator(ABC):
    """Abstract base class for static site generators."""

    name: str = ""

    @abstractmethod
    def get_config_filename(self) -> str:
        """Return the primary configuration file name."""

    @abstractmethod
    def get_build_command(self) -> list[str]:
        """Return the build command as a list of arguments."""

    @abstractmethod
    def get_serve_command(self) -> list[str]:
        """Return the local dev-server command."""

    @abstractmethod
    def get_build_output_dir(self) -> str:
        """Return the directory where the build output is placed."""

    @abstractmethod
    def generate_config(self, variables: dict, nav: list) -> str:
        """Generate the main config file content from variables and nav."""

    @abstractmethod
    def build_url_from_path(self, filepath: Path, docs_dir: Path) -> str:
        """Convert a docs file path to its published URL path."""

    @abstractmethod
    def get_nav_update_instructions(self, filepath: str, title: str) -> str:
        """Return human-readable instructions for adding a page to navigation."""

    @abstractmethod
    def get_docs_dir(self) -> str:
        """Return the default documentation source directory name."""

    @staticmethod
    def detect(project_dir: Path | None = None) -> SiteGenerator:
        """Auto-detect the site generator from project files.

        Detection logic:
        - docusaurus.config.js or docusaurus.config.ts present -> Docusaurus
        - Otherwise -> MkDocs (default)
        """
        if project_dir is None:
            project_dir = Path(".")

        docusaurus_configs = [
            "docusaurus.config.js",
            "docusaurus.config.ts",
        ]
        for cfg in docusaurus_configs:
            if (project_dir / cfg).exists():
                return DocusaurusGenerator()

        return MkDocsGenerator()

    @staticmethod
    def from_name(name: str) -> SiteGenerator:
        """Create a generator instance by name.

        Args:
            name: Either 'mkdocs' or 'docusaurus' (case-insensitive).

        Raises:
            ValueError: If the name is not recognized.
        """
        normalized = name.strip().lower()
        if normalized == "mkdocs":
            return MkDocsGenerator()
        if normalized == "docusaurus":
            return DocusaurusGenerator()
        raise ValueError(
            f"Unknown generator '{name}'. Choose 'mkdocs' or 'docusaurus'."
        )


class MkDocsGenerator(SiteGenerator):
    """MkDocs Material site generator."""

    name = "mkdocs"

    def get_config_filename(self) -> str:
        return "mkdocs.yml"

    def get_build_command(self) -> list[str]:
        return ["mkdocs", "build", "--strict"]

    def get_serve_command(self) -> list[str]:
        return ["mkdocs", "serve"]

    def get_build_output_dir(self) -> str:
        return "site"

    def get_docs_dir(self) -> str:
        return "docs"

    def generate_config(self, variables: dict, nav: list) -> str:
        """Generate mkdocs.yml content."""
        import yaml

        product = variables.get("product_name", "Documentation")
        site_url = variables.get("docs_url", "https://example.com/docs/")

        config = {
            "site_name": f"{product} Documentation",
            "site_description": f"{product} documentation powered by Auto-Doc Pipeline",
            "site_url": site_url,
            "theme": {
                "name": "material",
                "language": "en",
                "features": [
                    "navigation.tabs",
                    "navigation.sections",
                    "navigation.top",
                    "search.suggest",
                    "content.tabs.link",
                    "content.code.copy",
                ],
                "palette": [
                    {
                        "scheme": "default",
                        "primary": "deep purple",
                        "accent": "amber",
                        "toggle": {
                            "icon": "material/brightness-7",
                            "name": "Switch to dark mode",
                        },
                    },
                    {
                        "scheme": "slate",
                        "primary": "deep purple",
                        "accent": "amber",
                        "toggle": {
                            "icon": "material/brightness-4",
                            "name": "Switch to light mode",
                        },
                    },
                ],
            },
            "plugins": [
                "search",
                "tags",
                {"macros": {"include_yaml": ["docs/_variables.yml"]}},
            ],
            "markdown_extensions": [
                "admonition",
                "pymdownx.details",
                "pymdownx.superfences",
                {"pymdownx.tabbed": {"alternate_style": True}},
                "pymdownx.highlight",
                "attr_list",
                "tables",
                {"toc": {"permalink": True}},
            ],
            "nav": nav or [],
        }

        return yaml.dump(config, default_flow_style=False, sort_keys=False)

    def build_url_from_path(self, filepath: Path, docs_dir: Path) -> str:
        """Build URL path following MkDocs conventions.

        - ``index.md`` -> ``section/``
        - ``page.md`` -> ``page/``
        """
        rel = filepath.relative_to(docs_dir)
        if rel.name == "index.md":
            url = str(rel.parent) + "/"
        else:
            url = str(rel).replace(".md", "/")
        url = url.replace("\\", "/")
        if url == "./":
            url = ""
        return url

    def get_nav_update_instructions(self, filepath: str, title: str) -> str:
        return (
            f"Add to mkdocs.yml nav section:\n"
            f'  - "{title}": {filepath}'
        )


class DocusaurusGenerator(SiteGenerator):
    """Docusaurus v3 site generator."""

    name = "docusaurus"

    def get_config_filename(self) -> str:
        return "docusaurus.config.js"

    def get_build_command(self) -> list[str]:
        return ["npx", "docusaurus", "build"]

    def get_serve_command(self) -> list[str]:
        return ["npx", "docusaurus", "start"]

    def get_build_output_dir(self) -> str:
        return "build"

    def get_docs_dir(self) -> str:
        return "docs"

    def generate_config(self, variables: dict, nav: list) -> str:
        """Generate docusaurus.config.js content."""
        product = variables.get("product_name", "Documentation")
        site_url = variables.get("docs_url", "https://example.com")
        repo_url = variables.get("repo_url", "https://github.com/org/repo")

        # Escape JS string values
        def js_escape(val: str) -> str:
            return val.replace("\\", "\\\\").replace("'", "\\'")

        lines = [
            "// @ts-check",
            "/** @type {import('@docusaurus/types').Config} */",
            "const config = {",
            f"  title: '{js_escape(product)} Documentation',",
            f"  url: '{js_escape(site_url)}',",
            "  baseUrl: '/',",
            "  onBrokenLinks: 'throw',",
            "  onBrokenMarkdownLinks: 'warn',",
            "",
            "  presets: [",
            "    [",
            "      'classic',",
            "      /** @type {import('@docusaurus/preset-classic').Options} */",
            "      ({",
            "        docs: {",
            "          routeBasePath: '/',",
            "          sidebarPath: require.resolve('./sidebars.js'),",
            f"          editUrl: '{js_escape(repo_url)}/edit/main/',",
            "        },",
            "        theme: {",
            "          customCss: require.resolve('./src/css/custom.css'),",
            "        },",
            "      }),",
            "    ],",
            "  ],",
            "",
            "  themeConfig:",
            "    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */",
            "    ({",
            "      navbar: {",
            f"        title: '{js_escape(product)}',",
            "        items: [",
            "          {",
            "            type: 'docSidebar',",
            "            sidebarId: 'docs',",
            "            position: 'left',",
            "            label: 'Docs',",
            "          },",
            "        ],",
            "      },",
            "    }),",
            "};",
            "",
            "module.exports = config;",
            "",
        ]
        return "\n".join(lines)

    def build_url_from_path(self, filepath: Path, docs_dir: Path) -> str:
        """Build URL path following Docusaurus conventions.

        - ``index.md`` -> ``section/``
        - ``page.md``  -> ``section/page``
        """
        rel = filepath.relative_to(docs_dir)
        rel_str = str(rel).replace("\\", "/")

        if rel.name == "index.md":
            parent = str(rel.parent).replace("\\", "/")
            if parent == ".":
                return ""
            return parent + "/"

        # Remove .md / .mdx extension
        url = re.sub(r"\.mdx?$", "", rel_str)
        return url

    def get_nav_update_instructions(self, filepath: str, title: str) -> str:
        doc_id = re.sub(r"\.mdx?$", "", filepath).replace("\\", "/")
        return (
            f"Add to sidebars.js:\n"
            f"  {{ type: 'doc', id: '{doc_id}', label: '{title}' }}"
        )

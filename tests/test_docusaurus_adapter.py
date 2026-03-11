#!/usr/bin/env python3
"""
Tests for the Docusaurus adapter: site_generator, markdown_converter,
generate_docusaurus_config, preprocess_variables, and run_generator.

25 test cases organised into 6 test classes following unittest patterns.
"""

import json
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from site_generator import (
    DocusaurusGenerator,
    HugoGenerator,
    JekyllGenerator,
    MkDocsGenerator,
    SphinxGenerator,
    SiteGenerator,
)
from markdown_converter import (
    convert_directory,
    docusaurus_to_mkdocs,
    mkdocs_to_docusaurus,
)
from generate_docusaurus_config import (
    convert_nav_to_sidebar,
    generate_docusaurus_config_js,
    generate_sidebars_js,
)
from preprocess_variables import replace_variables


# ====================================================================
# 1. Admonition conversion tests (7)
# ====================================================================

class AdmonitionConversionTests(unittest.TestCase):
    """Test MkDocs admonition -> Docusaurus conversion."""

    def test_simple_note(self):
        src = '!!! note "Title"\n    Content here.\n'
        result = mkdocs_to_docusaurus(src)
        self.assertIn(":::note[Title]", result)
        self.assertIn("Content here.", result)
        self.assertIn(":::", result)

    def test_warning_multiline(self):
        src = '!!! warning "Important"\n    First paragraph.\n\n    Second paragraph.\n'
        result = mkdocs_to_docusaurus(src)
        self.assertIn(":::warning[Important]", result)
        self.assertIn("First paragraph.", result)
        self.assertIn("Second paragraph.", result)

    def test_code_inside_admonition(self):
        src = '!!! note "With code"\n    Here is code:\n\n    ```python\n    print("hello")\n    ```\n'
        result = mkdocs_to_docusaurus(src)
        self.assertIn(":::note[With code]", result)
        self.assertIn('print("hello")', result)

    def test_collapsible(self):
        src = '??? note "Expand me"\n    Hidden content.\n'
        result = mkdocs_to_docusaurus(src)
        self.assertIn("<details>", result)
        self.assertIn("<summary>Expand me</summary>", result)
        self.assertIn("Hidden content.", result)
        self.assertIn("</details>", result)

    def test_untitled(self):
        src = "!!! tip\n    Some tip.\n"
        result = mkdocs_to_docusaurus(src)
        self.assertIn(":::tip", result)
        self.assertIn("Some tip.", result)

    def test_consecutive_admonitions(self):
        src = '!!! note "A"\n    First.\n\n!!! warning "B"\n    Second.\n'
        result = mkdocs_to_docusaurus(src)
        self.assertIn(":::note[A]", result)
        self.assertIn(":::warning[B]", result)

    def test_all_types(self):
        types = ["note", "warning", "tip", "info", "danger", "caution"]
        for t in types:
            src = f'!!! {t} "Title"\n    Content.\n'
            result = mkdocs_to_docusaurus(src)
            self.assertIn(":::", result, f"Failed for type: {t}")


# ====================================================================
# 2. Tab conversion tests (4)
# ====================================================================

class TabConversionTests(unittest.TestCase):
    """Test MkDocs content tabs -> Docusaurus Tabs conversion."""

    def test_two_tabs(self):
        src = '=== "Tab A"\n    Content A.\n\n=== "Tab B"\n    Content B.\n'
        result = mkdocs_to_docusaurus(src)
        self.assertIn("<Tabs>", result)
        self.assertIn('<TabItem value="t0" label="Tab A">', result)
        self.assertIn('<TabItem value="t1" label="Tab B">', result)
        self.assertIn("</Tabs>", result)

    def test_tabs_with_code(self):
        src = '=== "Python"\n    ```python\n    print("hi")\n    ```\n\n=== "JavaScript"\n    ```javascript\n    console.log("hi")\n    ```\n'
        result = mkdocs_to_docusaurus(src)
        self.assertIn("<Tabs>", result)
        self.assertIn('print("hi")', result)
        self.assertIn('console.log("hi")', result)

    def test_import_added_once(self):
        src = '=== "A"\n    One.\n\n=== "B"\n    Two.\n\nSome text.\n\n=== "C"\n    Three.\n\n=== "D"\n    Four.\n'
        result = mkdocs_to_docusaurus(src)
        count = result.count("import Tabs from")
        self.assertEqual(count, 1, "Tabs import should appear exactly once")

    def test_mixed_tabs_and_admonitions(self):
        src = '!!! note "Note"\n    Info.\n\n=== "Tab1"\n    Content.\n\n=== "Tab2"\n    Content.\n'
        result = mkdocs_to_docusaurus(src)
        self.assertIn(":::note[Note]", result)
        self.assertIn("<Tabs>", result)


# ====================================================================
# 3. Nav conversion tests (4)
# ====================================================================

class NavConversionTests(unittest.TestCase):
    """Test MkDocs nav -> Docusaurus sidebar conversion."""

    def test_flat_nav(self):
        nav = [{"Home": "index.md"}, {"FAQ": "faq.md"}]
        result = convert_nav_to_sidebar(nav)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "index")
        self.assertEqual(result[1]["id"], "faq")

    def test_nested_nav(self):
        nav = [
            {"Getting Started": [
                "getting-started/index.md",
                {"Quick": "getting-started/quick.md"},
            ]}
        ]
        result = convert_nav_to_sidebar(nav)
        self.assertEqual(result[0]["type"], "category")
        self.assertEqual(result[0]["label"], "Getting Started")
        self.assertIsInstance(result[0]["items"], list)

    def test_labeled_items(self):
        nav = [{"Custom Label": "path/to/doc.md"}]
        result = convert_nav_to_sidebar(nav)
        self.assertEqual(result[0]["label"], "Custom Label")
        self.assertEqual(result[0]["id"], "path/to/doc")

    def test_index_as_category_link(self):
        nav = [
            {"Section": [
                "section/index.md",
                {"Page": "section/page.md"},
            ]}
        ]
        result = convert_nav_to_sidebar(nav)
        cat = result[0]
        self.assertEqual(cat["type"], "category")
        self.assertIn("link", cat)
        self.assertEqual(cat["link"]["id"], "section/index")


# ====================================================================
# 4. SiteGenerator tests (6)
# ====================================================================

class SiteGeneratorTests(unittest.TestCase):
    """Test SiteGenerator ABC, detection, and factory methods."""

    def test_detect_mkdocs(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "mkdocs.yml").touch()
            gen = SiteGenerator.detect(Path(td))
            self.assertEqual(gen.name, "mkdocs")

    def test_detect_docusaurus(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "docusaurus.config.js").touch()
            gen = SiteGenerator.detect(Path(td))
            self.assertEqual(gen.name, "docusaurus")

    def test_detect_default(self):
        with tempfile.TemporaryDirectory() as td:
            gen = SiteGenerator.detect(Path(td))
            self.assertEqual(gen.name, "mkdocs")

    def test_detect_sphinx(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "conf.py").touch()
            gen = SiteGenerator.detect(Path(td))
            self.assertEqual(gen.name, "sphinx")

    def test_detect_hugo(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "hugo.toml").touch()
            gen = SiteGenerator.detect(Path(td))
            self.assertEqual(gen.name, "hugo")

    def test_detect_jekyll(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "_config.yml").touch()
            (Path(td) / "_layouts").mkdir()
            gen = SiteGenerator.detect(Path(td))
            self.assertEqual(gen.name, "jekyll")

    def test_mkdocs_build_command(self):
        gen = MkDocsGenerator()
        cmd = gen.get_build_command()
        self.assertIn("mkdocs", cmd)
        self.assertIn("--strict", cmd)

    def test_docusaurus_build_command(self):
        gen = DocusaurusGenerator()
        cmd = gen.get_build_command()
        self.assertIn("docusaurus", cmd)
        self.assertIn("build", cmd)

    def test_url_conventions(self):
        docs = Path("/tmp/docs")
        # MkDocs: page.md -> page/
        mkdocs = MkDocsGenerator()
        self.assertEqual(mkdocs.build_url_from_path(docs / "page.md", docs), "page/")
        self.assertEqual(mkdocs.build_url_from_path(docs / "sub" / "index.md", docs), "sub/")

        # Docusaurus: page.md -> page
        docus = DocusaurusGenerator()
        self.assertEqual(docus.build_url_from_path(docs / "page.md", docs), "page")
        self.assertEqual(docus.build_url_from_path(docs / "sub" / "index.md", docs), "sub/")

        # Sphinx: page.rst -> page.html
        sphinx = SphinxGenerator()
        self.assertEqual(sphinx.build_url_from_path(docs / "page.rst", docs), "page.html")
        self.assertEqual(sphinx.build_url_from_path(docs / "sub" / "index.rst", docs), "sub/")

        # Hugo: page.md -> page/
        hugo = HugoGenerator()
        self.assertEqual(hugo.build_url_from_path(docs / "page.md", docs), "page/")
        self.assertEqual(hugo.build_url_from_path(docs / "sub" / "_index.md", docs), "sub/")

        # Jekyll: page.md -> page.html
        jekyll = JekyllGenerator()
        self.assertEqual(jekyll.build_url_from_path(docs / "page.md", docs), "page.html")
        self.assertEqual(jekyll.build_url_from_path(docs / "sub" / "index.md", docs), "sub/")


# ====================================================================
# 5. Config generation tests (2)
# ====================================================================

class ConfigGenerationTests(unittest.TestCase):
    """Test Docusaurus config and sidebar generation."""

    def test_full_config(self):
        variables = {
            "product_name": "Acme API",
            "docs_url": "https://docs.acme.com",
            "repo_url": "https://github.com/acme/api",
        }
        config_js = generate_docusaurus_config_js(variables, {})
        self.assertIn("Acme API", config_js)
        self.assertIn("https://docs.acme.com", config_js)
        self.assertIn("module.exports = config;", config_js)

    def test_minimal_config(self):
        config_js = generate_docusaurus_config_js({}, {})
        self.assertIn("Documentation", config_js)
        self.assertIn("module.exports", config_js)


# ====================================================================
# 6. Integration tests (2)
# ====================================================================

class IntegrationTests(unittest.TestCase):
    """Integration tests for directory conversion and roundtrip."""

    def test_convert_directory(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as dst:
            src_path = Path(src)
            dst_path = Path(dst)

            # Create test files
            (src_path / "page.md").write_text(
                '!!! note "Test"\n    Content.\n', encoding="utf-8"
            )
            (src_path / "sub").mkdir()
            (src_path / "sub" / "nested.md").write_text(
                '=== "A"\n    Tab content.\n\n=== "B"\n    Tab B.\n',
                encoding="utf-8",
            )
            (src_path / "_private.md").write_text("skip me", encoding="utf-8")

            files = convert_directory(src_path, "docusaurus", dst_path)

            self.assertEqual(len(files), 2)
            page_content = (dst_path / "page.md").read_text(encoding="utf-8")
            self.assertIn(":::note[Test]", page_content)

            nested = (dst_path / "sub" / "nested.md").read_text(encoding="utf-8")
            self.assertIn("<Tabs>", nested)

            # Private file should not be copied
            self.assertFalse((dst_path / "_private.md").exists())

    def test_roundtrip(self):
        """MkDocs -> Docusaurus -> MkDocs should preserve content semantics."""
        original = textwrap.dedent("""\
            !!! note "Important"
                This is important content.

            !!! warning "Caution"
                Be careful here.
        """)

        docusaurus = mkdocs_to_docusaurus(original)
        self.assertIn(":::note[Important]", docusaurus)

        roundtrip = docusaurus_to_mkdocs(docusaurus)
        self.assertIn("!!! note", roundtrip)
        self.assertIn("This is important content.", roundtrip)
        self.assertIn("!!! warning", roundtrip)
        self.assertIn("Be careful here.", roundtrip)


# ====================================================================
# Test loading helper
# ====================================================================

def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(AdmonitionConversionTests))
    suite.addTests(loader.loadTestsFromTestCase(TabConversionTests))
    suite.addTests(loader.loadTestsFromTestCase(NavConversionTests))
    suite.addTests(loader.loadTestsFromTestCase(SiteGeneratorTests))
    suite.addTests(loader.loadTestsFromTestCase(ConfigGenerationTests))
    suite.addTests(loader.loadTestsFromTestCase(IntegrationTests))
    return suite


if __name__ == "__main__":
    unittest.main()

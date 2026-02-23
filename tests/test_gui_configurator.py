#!/usr/bin/env python3
"""
Tests for the GUI Configurator (generate_configurator.py).

7 test cases verifying the generated HTML is self-contained,
embeds all required data, and has the correct structure.
"""

import json
import re
import sys
import unittest
from pathlib import Path

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from generate_configurator import generate_html, load_policy_packs, load_schema, load_variables

# Locate project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _get_html() -> str:
    """Generate configurator HTML using real project data."""
    packs = load_policy_packs(PROJECT_ROOT / "policy_packs")
    variables = load_variables(PROJECT_ROOT / "docs" / "_variables.yml")
    schema = load_schema(PROJECT_ROOT / "docs-schema.yml")
    return generate_html(packs, variables, schema)


class ConfiguratorGenerationTests(unittest.TestCase):
    """Tests for the generated configurator HTML."""

    @classmethod
    def setUpClass(cls):
        cls.html = _get_html()

    def test_valid_html(self):
        """Generated HTML has proper structure."""
        self.assertIn("<!DOCTYPE html>", self.html)
        self.assertIn("<html", self.html)
        self.assertIn("</html>", self.html)
        self.assertIn("<head>", self.html)
        self.assertIn("</head>", self.html)
        self.assertIn("<body>", self.html)
        self.assertIn("</body>", self.html)

    def test_embeds_policy_packs(self):
        """All 5 policy packs are embedded in the HTML."""
        expected_packs = ["minimal", "api-first", "monorepo", "multi-product", "plg"]
        for pack in expected_packs:
            self.assertIn(
                pack,
                self.html,
                f"Policy pack '{pack}' not found in generated HTML",
            )

    def test_embeds_variables(self):
        """Default variable values are present in the embedded data."""
        # Check that the YAML variables are serialized as JSON
        self.assertIn("DEFAULT_VARIABLES", self.html)
        self.assertIn("product_name", self.html)
        self.assertIn("support_email", self.html)
        self.assertIn("default_port", self.html)

    def test_embeds_schema(self):
        """Schema fields are present in the embedded data."""
        self.assertIn("DOCS_SCHEMA", self.html)
        self.assertIn("content_type", self.html)
        self.assertIn("title", self.html)
        self.assertIn("description", self.html)

    def test_all_form_sections(self):
        """All 6 wizard steps are present."""
        steps = [
            "Policy Pack",
            "Variables",
            "Generator",
            "KPI Thresholds",
            "Preview",
            "Export",
        ]
        for step in steps:
            self.assertIn(step, self.html, f"Step '{step}' not found in HTML")

    def test_generator_choices(self):
        """Both MkDocs and Docusaurus generator options are present."""
        self.assertIn("MkDocs", self.html)
        self.assertIn("Docusaurus", self.html)
        self.assertIn('data-gen="mkdocs"', self.html)
        self.assertIn('data-gen="docusaurus"', self.html)

    def test_no_external_deps(self):
        """No external script or link tags (self-contained HTML)."""
        # Check for <script src="http..."> or <link href="http...">
        external_script = re.search(r'<script\s+src=["\']https?://', self.html)
        external_link = re.search(
            r'<link\s+[^>]*href=["\']https?://[^"\']*\.css', self.html
        )
        self.assertIsNone(
            external_script,
            "Found external <script> tag -- configurator must be self-contained",
        )
        self.assertIsNone(
            external_link,
            "Found external <link> stylesheet -- configurator must be self-contained",
        )


# ====================================================================
# Test loading helper
# ====================================================================

def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(ConfiguratorGenerationTests))
    return suite


if __name__ == "__main__":
    unittest.main()

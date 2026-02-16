#!/usr/bin/env python3
"""
Lifecycle Manager for Documentation
Handles maturity states and automatic actions for deprecated/removed content
Works with GitHub Pages, MkDocs, and Docusaurus
"""

import yaml
import json
from pathlib import Path
from datetime import datetime

class LifecycleManager:
    """Manages content lifecycle (preview, beta, ga, deprecated, removed)"""

    def __init__(self, docs_dir='docs', site_generator='mkdocs'):
        self.docs_dir = Path(docs_dir)
        self.site_generator = site_generator
        self.deprecated_pages = []
        self.removed_pages = []
        self.preview_pages = []

    def extract_frontmatter(self, text):
        """Extract frontmatter from markdown."""
        if not text.startswith('---'):
            return {}, text
        parts = text.split('---', 2)
        if len(parts) < 3:
            return {}, text
        try:
            fm = yaml.safe_load(parts[1]) or {}
            return fm, parts[2]
        except yaml.YAMLError:
            return {}, text

    def scan_all_pages(self):
        """Scan all documentation pages for lifecycle states."""
        results = {
            'preview': [],
            'beta': [],
            'ga': [],
            'deprecated': [],
            'removed': []
        }

        for md_file in self.docs_dir.rglob('*.md'):
            if md_file.name.startswith('_'):
                continue

            content = md_file.read_text(encoding='utf-8')
            frontmatter, _ = self.extract_frontmatter(content)

            maturity = frontmatter.get('maturity', 'ga')
            if maturity in results:
                results[maturity].append({
                    'file': str(md_file),
                    'title': frontmatter.get('title', ''),
                    'replaced_by': frontmatter.get('replaced_by', ''),
                    'deprecated_since': frontmatter.get('deprecated_since', ''),
                    'sunset_date': frontmatter.get('sunset_date', ''),
                    'last_reviewed': frontmatter.get('last_reviewed', '')
                })

        return results

    def generate_mkdocs_overrides(self, results):
        """Generate MkDocs template overrides for lifecycle states."""

        # Create overrides directory
        overrides_dir = Path('overrides')
        overrides_dir.mkdir(exist_ok=True)

        # Generate main.html override for automatic banners
        main_template = '''
{%- extends "base.html" -%}

{% block content %}

  {# Automatic lifecycle banners based on frontmatter #}
  {% if page.meta.maturity == 'deprecated' %}
    <div class="admonition warning">
      <p class="admonition-title">⚠️ Deprecated</p>
      <p>This feature is deprecated{% if page.meta.deprecated_since %} since {{ page.meta.deprecated_since }}{% endif %}.</p>
      {% if page.meta.replaced_by %}
        <p>Please use <a href="{{ page.meta.replaced_by }}">the replacement feature</a> instead.</p>
      {% endif %}
      {% if page.meta.sunset_date %}
        <p>This will be removed on {{ page.meta.sunset_date }}.</p>
      {% endif %}
    </div>
  {% elif page.meta.maturity == 'preview' %}
    <div class="admonition info">
      <p class="admonition-title">🔬 Preview Feature</p>
      <p>This feature is in preview and may change without notice.</p>
    </div>
  {% elif page.meta.maturity == 'beta' %}
    <div class="admonition info">
      <p class="admonition-title">🧪 Beta Feature</p>
      <p>This feature is in beta. APIs and functionality may change before general availability.</p>
    </div>
  {% endif %}

  {# Original content #}
  {{ super() }}

{% endblock %}

{% block htmltitle %}
  {# Add lifecycle state to page title #}
  {% if page.meta.maturity == 'deprecated' %}
    <title>[Deprecated] {{ page.title }} - {{ config.site_name }}</title>
  {% elif page.meta.maturity == 'preview' %}
    <title>[Preview] {{ page.title }} - {{ config.site_name }}</title>
  {% else %}
    {{ super() }}
  {% endif %}
{% endblock %}
'''

        (overrides_dir / 'main.html').write_text(main_template)

        print(f"✅ Created MkDocs overrides for lifecycle management")

    def generate_docusaurus_plugin(self, results):
        """Generate Docusaurus plugin for lifecycle management."""

        plugin_code = '''
// docusaurus-plugin-lifecycle.js
// Add to docusaurus.config.js plugins array

module.exports = function lifecyclePlugin(context, options) {
  return {
    name: 'docusaurus-lifecycle-plugin',

    async contentLoaded({ content, actions }) {
      const { setGlobalData } = actions;

      // Pass lifecycle data to theme
      setGlobalData({
        lifecyclePages: ''' + json.dumps(results, indent=2) + '''
      });
    },

    injectHtmlTags({ content }) {
      // Add canonical tags for deprecated pages
      const tags = [];

      if (content.metadata && content.metadata.maturity === 'deprecated') {
        if (content.metadata.replaced_by) {
          tags.push({
            tagName: 'link',
            attributes: {
              rel: 'canonical',
              href: content.metadata.replaced_by,
            },
          });
        }
      }

      return { headTags: tags };
    },

    async postBuild({ siteConfig, routesPaths, outDir }) {
      // Generate redirect pages for removed content
      const fs = require('fs-extra');
      const path = require('path');

      const removedPages = ''' + json.dumps(results.get('removed', []), indent=2) + ''';

      for (const page of removedPages) {
        if (page.replaced_by) {
          const redirectHtml = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Redirecting...</title>
  <link rel="canonical" href="${page.replaced_by}">
  <meta http-equiv="refresh" content="0; url=${page.replaced_by}">
  <script>window.location.replace("${page.replaced_by}");</script>
</head>
<body>
  <p>This page has moved to <a href="${page.replaced_by}">${page.replaced_by}</a></p>
</body>
</html>`;

          const oldPath = page.file.replace('.md', '.html');
          const outputPath = path.join(outDir, oldPath);
          await fs.outputFile(outputPath, redirectHtml);
        }
      }
    }
  };
};
'''

        Path('docusaurus-plugin-lifecycle.js').write_text(plugin_code)

        # Also create React component for banners
        banner_component = '''
// LifecycleBanner.jsx
// Add to src/theme/DocItem/index.js

import React from 'react';
import { useDoc } from '@docusaurus/theme-common';

export function LifecycleBanner() {
  const { metadata } = useDoc();
  const { maturity, deprecated_since, sunset_date, replaced_by } = metadata;

  if (maturity === 'deprecated') {
    return (
      <div className="alert alert--warning margin-bottom--md">
        <strong>⚠️ Deprecated</strong>
        {deprecated_since && <span> since {deprecated_since}</span>}
        {replaced_by && (
          <p>
            Please use <a href={replaced_by}>the replacement feature</a> instead.
          </p>
        )}
        {sunset_date && <p>Will be removed on {sunset_date}</p>}
      </div>
    );
  }

  if (maturity === 'preview') {
    return (
      <div className="alert alert--info margin-bottom--md">
        <strong>🔬 Preview Feature</strong>
        <p>This feature is in preview and may change without notice.</p>
      </div>
    );
  }

  if (maturity === 'beta') {
    return (
      <div className="alert alert--info margin-bottom--md">
        <strong>🧪 Beta Feature</strong>
        <p>APIs and functionality may change before general availability.</p>
      </div>
    );
  }

  return null;
}
'''

        Path('LifecycleBanner.jsx').write_text(banner_component)

        print("✅ Created Docusaurus plugin and component for lifecycle management")

    def generate_redirect_pages(self, results):
        """Generate redirect HTML pages for removed content (GitHub Pages compatible)."""

        redirects_dir = Path('docs/_redirects')
        redirects_dir.mkdir(exist_ok=True)

        for page in results.get('removed', []):
            if page['replaced_by']:
                # Create redirect HTML
                redirect_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Page Moved</title>
  <link rel="canonical" href="{page['replaced_by']}">
  <meta http-equiv="refresh" content="0; url={page['replaced_by']}">
  <script>window.location.replace("{page['replaced_by']}");</script>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
    }}
    .container {{ text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Page Moved</h1>
    <p>This page has been moved to a new location.</p>
    <p>If you are not redirected automatically, <a href="{page['replaced_by']}">click here</a>.</p>
  </div>
</body>
</html>'''

                # Save redirect page
                old_path = Path(page['file']).relative_to('docs')
                redirect_path = redirects_dir / old_path.with_suffix('.html')
                redirect_path.parent.mkdir(parents=True, exist_ok=True)
                redirect_path.write_text(redirect_html)

                print(f"✅ Created redirect: {old_path} → {page['replaced_by']}")

    def generate_lifecycle_report(self, results):
        """Generate lifecycle status report."""

        report = []
        report.append("# Documentation Lifecycle Report")
        report.append(f"\nGenerated: {datetime.now().isoformat()}\n")

        # Statistics
        report.append("## Statistics\n")
        for state, pages in results.items():
            report.append(f"- **{state.upper()}**: {len(pages)} pages")

        # Preview pages check
        report.append("\n## Preview Pages (Check Duration)\n")
        for page in results['preview']:
            report.append(f"- {page['title']} ({page['file']})")
            if page['last_reviewed']:
                days_old = (datetime.now() - datetime.fromisoformat(page['last_reviewed'])).days
                if days_old > 365:
                    report.append(f"  ⚠️ In preview for {days_old} days!")

        # Deprecated pages
        report.append("\n## Deprecated Pages\n")
        for page in results['deprecated']:
            report.append(f"- {page['title']} ({page['file']})")
            if page['replaced_by']:
                report.append(f"  → Replacement: {page['replaced_by']}")
            if page['sunset_date']:
                report.append(f"  ⏰ Sunset: {page['sunset_date']}")

        # Removed pages
        report.append("\n## Removed Pages (Need Redirects)\n")
        for page in results['removed']:
            report.append(f"- {page['title']} ({page['file']})")
            if page['replaced_by']:
                report.append(f"  → Redirect to: {page['replaced_by']}")
            else:
                report.append(f"  ⚠️ No replacement specified!")

        return '\n'.join(report)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Manage documentation lifecycle')
    parser.add_argument('--scan', action='store_true', help='Scan for lifecycle states')
    parser.add_argument('--mkdocs', action='store_true', help='Generate MkDocs overrides')
    parser.add_argument('--docusaurus', action='store_true', help='Generate Docusaurus plugin')
    parser.add_argument('--redirects', action='store_true', help='Generate redirect pages')
    parser.add_argument('--report', action='store_true', help='Generate lifecycle report')
    args = parser.parse_args()

    manager = LifecycleManager()

    # Always scan first
    results = manager.scan_all_pages()

    if args.mkdocs:
        manager.generate_mkdocs_overrides(results)

    if args.docusaurus:
        manager.generate_docusaurus_plugin(results)

    if args.redirects:
        manager.generate_redirect_pages(results)

    if args.report or args.scan:
        report = manager.generate_lifecycle_report(results)
        print(report)

        # Save report
        Path('lifecycle-report.md').write_text(report)
        print(f"\n✅ Report saved to lifecycle-report.md")

if __name__ == '__main__':
    main()

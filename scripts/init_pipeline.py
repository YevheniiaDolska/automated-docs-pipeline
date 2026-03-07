#!/usr/bin/env python3
"""
Auto-Doc Pipeline Initializer

One-command bootstrap for integrating the documentation pipeline
into an existing project. Run from the target project root:

    python3 path/to/init_pipeline.py --product-name "YourProduct" --docs-dir docs

This script:
1. Copies pipeline configs, scripts, templates, and workflows
2. Parametrizes all files with your product name and URLs
3. Installs dependencies (Python + Node)
4. Runs an initial validation to confirm everything works
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


PIPELINE_FILES = {
    "configs": [
        ".vale.ini",
        ".markdownlint.yml",
        "cspell.json",
        "docs-schema.yml",
        "glossary.yml",
        "requirements.txt",
        "Makefile",
    ],
    "directories": [
        "scripts",
        "runtime",
        "templates",
        "config",
        "policy_packs",
        ".vale",
        ".github/workflows",
        "overrides",
    ],
    "root_files": [
        "package.json",
        "mkdocs.yml",
        "CLAUDE.md",
        "AGENTS.md",
    ],
}

DOCUSAURUS_FILES = {
    "directories": [
        "docusaurus/src/css",
        "docusaurus/src/components",
    ],
    "templates": [
        "docusaurus/docusaurus.config.js.template",
        "docusaurus/sidebars.js.template",
        "docusaurus/package.json.template",
    ],
}


def print_step(step_num, total, message):
    """Print a formatted step message."""
    print(f"\n[{step_num}/{total}] {message}")
    print("-" * 60)


def copy_pipeline_files(source_dir, target_dir):
    """Copy pipeline files to target project."""
    copied = []

    # Copy config files
    for config_file in PIPELINE_FILES["configs"]:
        src = source_dir / config_file
        dst = target_dir / config_file
        if src.exists():
            shutil.copy2(src, dst)
            copied.append(config_file)

    # Copy directories
    for directory in PIPELINE_FILES["directories"]:
        src = source_dir / directory
        dst = target_dir / directory
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            copied.append(f"{directory}/")

    # Copy root files
    for root_file in PIPELINE_FILES["root_files"]:
        src = source_dir / root_file
        dst = target_dir / root_file
        if src.exists():
            shutil.copy2(src, dst)
            copied.append(root_file)

    return copied


def parametrize_variables(target_dir, config):
    """Replace placeholder values with actual product configuration."""
    variables_path = target_dir / "docs" / "_variables.yml"

    # Create docs directory if it does not exist
    (target_dir / "docs").mkdir(exist_ok=True)

    content = f"""# =============================================================
# PROJECT VARIABLES - Single source of truth
# =============================================================
# These variables are used across all documentation.
# Change them here to update everywhere.
#
# Usage in Markdown (with mkdocs-macros-plugin):
#   {{{{ product_name }}}}
#   {{{{ cloud_url }}}}
#   {{{{ support_email }}}}
# =============================================================

# --- PRODUCT INFO ---
product_name: "{config['product_name']}"
product_full_name: "{config.get('product_full_name', config['product_name'] + ' platform')}"
product_tagline: "{config.get('tagline', 'Enterprise platform')}"

# --- VERSIONS ---
current_version: "{config.get('version', '1.0.0')}"
min_supported_version: "{config.get('min_version', '1.0.0')}"
api_version: "{config.get('api_version', 'v1')}"
docs_version: "1.0"

# --- URLS ---
cloud_url: "{config.get('cloud_url', 'https://app.example.com')}"
cloud_signup_url: "{config.get('cloud_url', 'https://app.example.com')}/register"
docs_url: "{config.get('docs_url', 'https://docs.example.com')}"
community_url: "{config.get('community_url', 'https://community.example.com')}"
github_url: "{config.get('github_url', 'https://github.com/YOUR_ORG/YOUR_REPO')}"
status_page_url: "{config.get('status_url', 'https://status.example.com')}"

# --- SUPPORT ---
support_email: "{config.get('support_email', 'support@example.com')}"
sales_email: "{config.get('sales_email', 'sales@example.com')}"

# --- DEFAULT PORTS ---
default_port: {config.get('default_port', 8080)}
default_webhook_port: {config.get('webhook_port', 8080)}

# --- DEFAULT PATHS ---
default_data_folder: "~/.{config['product_name'].lower().replace(' ', '-')}"
default_config_path: "~/.{config['product_name'].lower().replace(' ', '-')}/config"

# --- ENVIRONMENT VARIABLES ---
env_vars:
  webhook_url: "WEBHOOK_URL"
  data_folder: "{config['product_name'].upper().replace(' ', '_')}_USER_FOLDER"
  port: "{config['product_name'].upper().replace(' ', '_')}_PORT"
  encryption_key: "{config['product_name'].upper().replace(' ', '_')}_ENCRYPTION_KEY"

# --- LIMITS ---
max_payload_size_mb: 16
max_execution_timeout_seconds: 3600
rate_limit_requests_per_minute: 60

# --- COMMON TERMS (for consistency) ---
terms:
  workflow: "workflow"
  node: "node"
  trigger: "trigger"
  execution: "execution"
  credential: "credential"
  expression: "expression"

# --- BRANDING ---
company_name: "{config.get('company_name', 'Your Company')}"
copyright_year: "2025"
"""

    with open(variables_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Update mkdocs.yml with product name
    mkdocs_path = target_dir / "mkdocs.yml"
    if mkdocs_path.exists():
        text = mkdocs_path.read_text(encoding="utf-8")
        text = text.replace(
            'site_name: "Documentation (Pipeline Demo)"',
            f'site_name: "{config["product_name"]} Documentation"',
        )
        mkdocs_path.write_text(text, encoding="utf-8")

    # Update package.json name
    pkg_path = target_dir / "package.json"
    if pkg_path.exists():
        text = pkg_path.read_text(encoding="utf-8")
        slug = config["product_name"].lower().replace(" ", "-")
        text = text.replace(
            '"name": "auto-doc-pipeline"',
            f'"name": "{slug}-docs-pipeline"',
        )
        pkg_path.write_text(text, encoding="utf-8")


def create_docs_skeleton(target_dir, product_name):
    """Create initial docs directory structure."""
    docs_dir = target_dir / "docs"

    directories = [
        "getting-started",
        "how-to",
        "concepts",
        "reference",
        "troubleshooting",
        "assets/javascripts",
        "stylesheets",
    ]

    for d in directories:
        (docs_dir / d).mkdir(parents=True, exist_ok=True)

    # Create index.md
    index_content = f"""---
title: "{product_name} documentation"
description: "Official documentation for {product_name}. Guides, tutorials, API reference, and troubleshooting."
content_type: reference
---

# {product_name} documentation

Welcome to the {product_name} documentation. Find guides, tutorials, API reference, and troubleshooting resources.

## Get started

- [Quickstart](getting-started/quickstart.md) - Set up {product_name} in 5 minutes
- [How-to guides](how-to/index.md) - Step-by-step task guides
- [API reference](reference/index.md) - Complete API documentation

## Explore by topic

| Section | Description |
|---------|-------------|
| [Getting started](getting-started/index.md) | Tutorials and quickstart guides |
| [How-to guides](how-to/index.md) | Task-oriented step-by-step guides |
| [Concepts](concepts/index.md) | Architecture and design explanations |
| [Reference](reference/index.md) | API specs, configuration, and parameters |
| [Troubleshooting](troubleshooting/index.md) | Common issues and solutions |
"""

    index_path = docs_dir / "index.md"
    if not index_path.exists():
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(index_content)

    # Create section index files
    sections = {
        "getting-started": ("Getting started", "Tutorials and quickstart guides for new users."),
        "how-to": ("How-to guides", "Task-oriented guides for specific goals and workflows."),
        "concepts": ("Concepts", "Architecture explanations and design decisions."),
        "reference": ("Reference", "API specifications, configuration parameters, and technical details."),
        "troubleshooting": ("Troubleshooting", "Solutions for common issues and error messages."),
    }

    for section, (title, desc) in sections.items():
        section_index = docs_dir / section / "index.md"
        if not section_index.exists():
            content = f"""---
title: "{title}"
description: "{desc}"
content_type: reference
---

# {title}

{desc}
"""
            with open(section_index, "w", encoding="utf-8") as f:
                f.write(content)

    # Create tags.md
    tags_path = docs_dir / "tags.md"
    if not tags_path.exists():
        with open(tags_path, "w", encoding="utf-8") as f:
            f.write("""---
title: "Tags"
description: "Browse documentation by tags and categories."
content_type: reference
---

# Tags

[TAGS]
""")


def create_reports_dir(target_dir):
    """Create reports directory for pipeline output."""
    reports_dir = target_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    gitkeep = reports_dir / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()


def install_dependencies(target_dir):
    """Install Python and Node dependencies."""
    print("  Installing Python dependencies...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        cwd=target_dir,
        capture_output=True,
    )

    print("  Installing Node dependencies...")
    subprocess.run(
        ["npm", "install"],
        cwd=target_dir,
        capture_output=True,
    )

    # Install Vale if not present
    print("  Checking Vale installation...")
    result = subprocess.run(["vale", "--version"], capture_output=True)
    if result.returncode != 0:
        print("  WARNING: Vale is not installed. Install it from https://vale.sh/docs/vale-cli/installation/")
    else:
        print(f"  Vale found: {result.stdout.decode().strip()}")

    # Sync Vale packages
    print("  Syncing Vale packages...")
    subprocess.run(["vale", "sync"], cwd=target_dir, capture_output=True)


def run_initial_validation(target_dir, generator="mkdocs"):
    """Run initial validation to confirm setup works."""
    print("  Running frontmatter validation...")
    result = subprocess.run(
        [sys.executable, "scripts/validate_frontmatter.py"],
        cwd=target_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("  Frontmatter validation: PASSED")
    else:
        print(f"  Frontmatter validation: {result.stdout or result.stderr}")

    print("  Running markdownlint...")
    result = subprocess.run(
        ["npx", "markdownlint", "docs/"],
        cwd=target_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("  Markdownlint: PASSED")
    else:
        print(f"  Markdownlint: Some issues found (normal for initial setup)")

    if generator == "docusaurus":
        print("  Running Docusaurus build...")
        result = subprocess.run(
            ["npx", "docusaurus", "build"],
            cwd=target_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("  Docusaurus build: PASSED")
        else:
            print(f"  Docusaurus build: {result.stderr[:200] if result.stderr else 'Issues found'}")
    else:
        print("  Running MkDocs build...")
        result = subprocess.run(
            ["mkdocs", "build", "--strict"],
            cwd=target_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("  MkDocs build: PASSED")
        else:
            print(f"  MkDocs build: {result.stderr[:200] if result.stderr else 'Issues found'}")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize Auto-Doc Pipeline in your project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic setup
  python3 init_pipeline.py --product-name "Acme API"

  # Full configuration
  python3 init_pipeline.py \\
    --product-name "Acme API" \\
    --company "Acme Corp" \\
    --docs-url "https://docs.acme.com" \\
    --github-url "https://github.com/acme/acme-api" \\
    --policy-pack api-first

  # Minimal setup (skip dependency installation)
  python3 init_pipeline.py --product-name "MyProduct" --skip-install
        """,
    )

    parser.add_argument(
        "--product-name",
        required=True,
        help="Your product name (e.g., 'Acme API')",
    )
    parser.add_argument(
        "--company",
        default="Your Company",
        help="Company name",
    )
    parser.add_argument(
        "--docs-url",
        default="https://docs.example.com",
        help="Documentation site URL",
    )
    parser.add_argument(
        "--cloud-url",
        default="https://app.example.com",
        help="Cloud/SaaS product URL",
    )
    parser.add_argument(
        "--github-url",
        default="https://github.com/YOUR_ORG/YOUR_REPO",
        help="GitHub repository URL",
    )
    parser.add_argument(
        "--community-url",
        default="https://community.example.com",
        help="Community forum URL",
    )
    parser.add_argument(
        "--support-email",
        default="support@example.com",
        help="Support email",
    )
    parser.add_argument(
        "--policy-pack",
        choices=["minimal", "api-first", "monorepo", "multi-product", "plg"],
        default="minimal",
        help="Policy pack to use (default: minimal)",
    )
    parser.add_argument(
        "--target-dir",
        default=".",
        help="Target project directory (default: current directory)",
    )
    parser.add_argument(
        "--generator",
        choices=["mkdocs", "docusaurus"],
        default="mkdocs",
        help="Site generator to use (default: mkdocs)",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip dependency installation",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip initial validation",
    )

    args = parser.parse_args()

    target_dir = Path(args.target_dir).resolve()
    source_dir = Path(__file__).parent.parent.resolve()

    total_steps = 6
    if args.skip_install:
        total_steps -= 1
    if args.skip_validation:
        total_steps -= 1

    step = 0

    print("=" * 60)
    print(f"  Auto-Doc Pipeline Initializer")
    print(f"  Product:   {args.product_name}")
    print(f"  Generator: {args.generator}")
    print(f"  Target:    {target_dir}")
    print("=" * 60)

    # Step 1: Copy pipeline files
    step += 1
    print_step(step, total_steps, "Copying pipeline files...")
    copied = copy_pipeline_files(source_dir, target_dir)
    if args.generator == "docusaurus":
        # Copy Docusaurus scaffold
        for d in DOCUSAURUS_FILES.get("directories", []):
            src = source_dir / d
            dst = target_dir / d
            if src.exists():
                dst.mkdir(parents=True, exist_ok=True)
                for item in src.iterdir():
                    if item.is_file():
                        shutil.copy2(item, dst / item.name)
                        copied.append(str(Path(d) / item.name))
        for t in DOCUSAURUS_FILES.get("templates", []):
            src = source_dir / t
            if src.exists():
                dst = target_dir / t
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                copied.append(t)
    for f in copied:
        print(f"  + {f}")

    # Step 2: Create docs skeleton
    step += 1
    print_step(step, total_steps, "Creating documentation structure...")
    create_docs_skeleton(target_dir, args.product_name)
    print("  Created docs/ directory structure")

    # Step 3: Parametrize variables
    step += 1
    print_step(step, total_steps, "Configuring product variables...")
    config = {
        "product_name": args.product_name,
        "company_name": args.company,
        "docs_url": args.docs_url,
        "cloud_url": args.cloud_url,
        "github_url": args.github_url,
        "community_url": args.community_url,
        "support_email": args.support_email,
    }
    parametrize_variables(target_dir, config)
    print(f"  Configured for: {args.product_name}")

    # Step 4: Create reports directory
    step += 1
    print_step(step, total_steps, "Setting up reports directory...")
    create_reports_dir(target_dir)
    print("  Created reports/ directory")

    # Step 5: Install dependencies
    if not args.skip_install:
        step += 1
        print_step(step, total_steps, "Installing dependencies...")
        install_dependencies(target_dir)

    # Step 6: Run validation
    if not args.skip_validation:
        step += 1
        print_step(step, total_steps, "Running initial validation...")
        run_initial_validation(target_dir, generator=args.generator)

    # Generator-specific commands for summary
    if args.generator == "docusaurus":
        serve_cmd = "npx docusaurus start"
        build_cmd = "npx docusaurus build"
    else:
        serve_cmd = "mkdocs serve"
        build_cmd = "mkdocs build --strict"

    # Summary
    print("\n" + "=" * 60)
    print("  Setup complete!")
    print("=" * 60)
    print(f"""
Next steps:

  1. Review docs/_variables.yml and customize values
  2. Set policy pack in your CI workflows:
     Policy: policy_packs/{args.policy_pack}.yml
  3. Start writing docs:
     python3 scripts/new_doc.py
  4. Preview locally:
     {serve_cmd}
  5. Run all checks:
     npm run lint

Useful commands:
  npm run lint              - Run all quality checks
  npm run validate:minimal  - Run core checks only
  npm run gaps              - Detect documentation gaps
  npm run kpi-wall          - Generate KPI dashboard
  npm run new-doc           - Create new document from template
  {serve_cmd:<24s}- Preview docs locally
  {build_cmd:<24s}- Build for production

Generator: {args.generator}
  Detected via: python3 scripts/run_generator.py detect
  Build:        python3 scripts/run_generator.py build
  Serve:        python3 scripts/run_generator.py serve
""")


if __name__ == "__main__":
    main()

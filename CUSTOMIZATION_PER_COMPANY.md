# Customizing the pipeline for a specific company

This guide explains how to adapt the Auto-Doc Pipeline for each client. It covers every configuration point, from product branding to quality thresholds.

## What you customize (overview)

When you install the pipeline for a new company, you change these files:

| File | What you change | Why |
| --- | --- | --- |
| `docs/_variables.yml` | Product name, URLs, ports, limits | All docs reference variables instead of hardcoded values |
| `policy_packs/*.yml` | Quality thresholds, drift patterns | Different companies need different strictness levels |
| `mkdocs.yml` | Site title, nav structure, theme colors | Client-facing documentation site |
| `CLAUDE.md` | Company-specific style rules (optional) | AI generates docs matching company tone |
| `AGENTS.md` | Same as CLAUDE.md for Codex | AI generates docs matching company tone |
| `cspell.json` | Company-specific terms | Spellcheck does not flag product names |
| `.vale/styles/` | Custom Vale rules (optional) | Company-specific writing rules |
| `templates/*.md` | Template frontmatter defaults | Templates pre-fill company-specific metadata |

## Step 1: Set up variables

The variables file is the single source of truth for all product-specific values. Every document references these variables using `{{ variable_name }}` syntax. When you change a value here, it changes across all documents.

Edit `docs/_variables.yml`:

```yaml
# ===== Product Identity =====
product_name: "Acme API"
product_full_name: "Acme API - Developer Integration Platform"
product_tagline: "Connect everything, build anything"
company_name: "Acme Corp"

# ===== Versions =====
current_version: "2.5.0"
min_supported_version: "2.0.0"
api_version: "v2"

# ===== URLs =====
cloud_url: "https://app.acme.com"
docs_url: "https://docs.acme.com"
github_url: "https://github.com/acmecorp/acme-api"
status_page_url: "https://status.acme.com"
community_url: "https://community.acme.com"

# ===== Support =====
support_email: "support@acme.com"
sales_email: "sales@acme.com"

# ===== Technical Defaults =====
default_port: 3000
default_data_folder: "~/.acme"

# ===== Environment Variables =====
env_vars:
  port: "ACME_PORT"
  webhook_url: "ACME_WEBHOOK_URL"
  api_key: "ACME_API_KEY"
  database_url: "ACME_DATABASE_URL"
  secret_key: "ACME_SECRET_KEY"
  log_level: "ACME_LOG_LEVEL"

# ===== Limits =====
max_payload_size_mb: 32
rate_limit_requests_per_minute: 120
max_connections: 1000
request_timeout_seconds: 30

# ===== Branding =====
copyright_year: 2026
```

**Important rules:**

- Use unique, descriptive names: `acme_webhook_retry_limit`, not `limit`.
- Group related variables with YAML nesting: `env_vars.port`, `env_vars.api_key`.
- Every value that appears in more than one document must be a variable.
- Never hardcode product names, URLs, ports, or version numbers in documents.

## Step 2: Choose and configure a policy pack

Policy packs control how strict the quality checks are. Start with the pack that matches the client:

### For a new team or pilot

Copy `policy_packs/minimal.yml`:

```bash
cp policy_packs/minimal.yml policy_packs/client-acme.yml
```

Minimal settings (most lenient):

```yaml
min_quality_score: 75
max_stale_percentage: 20
max_high_priority_gaps: 10
max_quality_score_drop: 8
```

### For an API-heavy team

Copy `policy_packs/api-first.yml`:

```bash
cp policy_packs/api-first.yml policy_packs/client-acme.yml
```

API-first settings (strict on API docs):

```yaml
min_quality_score: 82
max_stale_percentage: 12
max_high_priority_gaps: 6
max_quality_score_drop: 4
```

### For a product-led growth company

Copy `policy_packs/plg.yml`:

```bash
cp policy_packs/plg.yml policy_packs/client-acme.yml
```

PLG settings (strict on user-facing docs):

```yaml
min_quality_score: 85
max_stale_percentage: 10
max_high_priority_gaps: 5
max_quality_score_drop: 3
```

### Customize the policy pack

Edit `policy_packs/client-acme.yml`:

1. Adjust `interface_patterns` to match the client's code structure:

```yaml
interface_patterns:
  - "src/controllers/**"
  - "src/routes/**"
  - "src/api/**"
  - "lib/sdk/**"
```

1. Adjust `docs_patterns` to match the client's docs structure:

```yaml
docs_patterns:
  - "docs/**/*.md"
  - "guides/**/*.md"
```

1. Adjust KPI thresholds based on the baseline measurement from the pilot.

## Step 3: Configure the documentation site

Edit `mkdocs.yml`:

```yaml
site_name: "Acme API Documentation"
site_url: "https://docs.acme.com"
site_description: "Official documentation for Acme API"

theme:
  name: material
  palette:
    primary: blue        # Client brand color
    accent: light-blue
  logo: assets/logo.png  # Client logo
  favicon: assets/favicon.ico

nav:
  - Home: index.md
  - Getting Started:
    - getting-started/index.md
    - Quickstart: getting-started/quickstart.md
  - How-To Guides:
    - how-to/index.md
  - Concepts:
    - concepts/index.md
  - Reference:
    - reference/index.md
  - Troubleshooting:
    - troubleshooting/index.md

plugins:
  - search
  - tags
  - macros:
      module_name: docs/_variables
```

## Step 4: Add company terms to spellcheck

Edit `cspell.json`. Add the client's product names, brand terms, and technical jargon to the `words` array:

```json
{
  "words": [
    "Acme",
    "AcmeAPI",
    "acmecorp",
    "webhook",
    "GraphQL"
  ]
}
```

This prevents the spellchecker from flagging legitimate company terms.

## Step 5: Customize templates (optional)

For each template in `templates/`, you can pre-fill the client's product context:

1. Open a template, for example `templates/quickstart.md`.
1. Replace generic placeholders with the client's defaults:

```yaml
---
title: "{{ title }}"
description: "{{ description }}"
content_type: tutorial
product: both
tags:
  - Tutorial
  - Getting Started
---
```

1. Add client-specific sections if the client's product has unique patterns.

## Step 6: Customize AI instructions (optional)

If the client has specific writing rules beyond the standard, add them to `CLAUDE.md` and `AGENTS.md`.

**Example additions:**

```markdown
## Company-specific style rules

- Always refer to the product as "Acme API" (never "ACME" or "acme").
- Use "workspace" instead of "project" when referring to user containers.
- Authentication tokens are called "access keys" in this product.
- Error responses always include a `request_id` field - mention it in troubleshooting docs.
```

Add this section after the existing style rules in both `CLAUDE.md` and `AGENTS.md`.

## Step 7: Configure CI gates

### Enable only the docs-check gate (pilot)

In `.github/workflows/docs-check.yml`, make sure it runs on pull requests:

```yaml
on:
  pull_request:
    paths:
      - "docs/**"
      - "templates/**"
```

### Enable all four gates (full implementation)

Enable each workflow in the GitHub repository settings:

1. `docs-check.yml` - quality gate.
1. `pr-dod-contract.yml` - interface-to-docs contract.
1. `api-sdk-drift-gate.yml` - API/SDK drift detection.
1. `code-examples-smoke.yml` - code example validation.

Set them as required status checks in the branch protection rules.

## Step 8: Set up reporting (full implementation)

Enable scheduled workflows:

```yaml
# In kpi-wall.yml
on:
  schedule:
    - cron: "0 9 * * 1"  # Every Monday at 9 AM UTC

# In lifecycle-management.yml
on:
  schedule:
    - cron: "0 10 * * 1"  # Every Monday at 10 AM UTC
```

## Complete customization checklist

Use this checklist for every new company:

- [ ] `docs/_variables.yml` filled with all company-specific values.
- [ ] Policy pack selected and customized (or custom pack created).
- [ ] `mkdocs.yml` updated with site name, URL, branding, and navigation.
- [ ] `cspell.json` updated with company terms.
- [ ] Core templates adapted to the company's product.
- [ ] `CLAUDE.md` and `AGENTS.md` updated with company style rules (if needed).
- [ ] CI gates enabled in GitHub repository settings.
- [ ] Repository secrets configured (if using Algolia or other integrations).
- [ ] Baseline KPI measurement taken.
- [ ] `npm run validate:minimal` passes.
- [ ] Documentation site builds in strict mode: `mkdocs build --strict`.

## Using the GUI configurator

For a faster setup, use the browser-based configurator:

```bash
npm run configurator
```

Open `reports/pipeline-configurator.html` in a browser. The wizard walks through:

1. Policy pack selection (choose from built-in packs).
1. Variable editing (fill in product name, URLs, ports).
1. Generator choice (MkDocs or Docusaurus).
1. KPI threshold tuning (adjust quality, staleness, gap limits).
1. Live preview (see generated configuration files).
1. Export (download all configuration files as a bundle).

The exported files can be dropped directly into the client's repository.

## Using the init script

For bootstrapping a completely new repository:

```bash
python3 scripts/init_pipeline.py \
  --product-name "Acme API" \
  --generator mkdocs \
  --policy-pack policy_packs/api-first.yml
```

This script:

1. Copies all required pipeline files to the target directory.
1. Configures `docs/_variables.yml` with the product name.
1. Scaffolds the chosen site generator.
1. Runs initial validation.

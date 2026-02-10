# Claude Code Instructions for Documentation Pipeline

## Project Overview

This is an automated documentation pipeline for n8n. When writing or editing documentation, follow these rules strictly to ensure all linting checks pass.

## Critical Rules

### 1. Frontmatter Requirements (MANDATORY)

Every `.md` file in `docs/` MUST have valid frontmatter:

```yaml
---
title: "Descriptive title under 70 characters"
description: "Description between 50-160 characters for SEO. Include key terms."
content_type: tutorial|how-to|concept|reference|troubleshooting|release-note
product: both|n8n-cloud|n8n-self-hosted
tags:
  - Tag1
  - Tag2
---
```

**Validation rules:**
- `title`: Required, max 70 characters
- `description`: Required, 50-160 characters
- `content_type`: Required, must be one of the allowed values
- `product`: Optional but recommended
- `tags`: Optional, max 8 tags

### 2. GEO Optimization (for LLM/AI search)

**First paragraph rules:**
- Keep under 60 words
- Include a clear definition using "is", "enables", "provides", "allows"
- Answer the implied question directly

**Example:**
```markdown
# Webhook node reference

The Webhook node is a trigger that starts workflows when it receives HTTP requests. It supports GET, POST, PUT, PATCH, DELETE methods and provides built-in authentication options.
```

**Heading rules:**
- Use descriptive headings, NOT generic ones
- BAD: "Overview", "Configuration", "Setup"
- GOOD: "Configure HMAC authentication", "Set up webhook endpoints"

**Fact density:**
- Include concrete facts every 200 words (numbers, code, config values)
- Tables and code blocks count as facts

### 3. Document Types (Diátaxis Framework)

Use these templates based on `content_type`:

| Type | Purpose | Template |
|------|---------|----------|
| `tutorial` | Learning-oriented, step-by-step | `doc-tutorial` snippet |
| `how-to` | Task-oriented, specific goals | `doc-howto` snippet |
| `concept` | Understanding-oriented, explanations | `doc-concept` snippet |
| `reference` | Information-oriented, precise specs | `doc-reference` snippet |
| `troubleshooting` | Problem → cause → solution | `doc-troubleshoot` snippet |
| `release-note` | Version changes | `doc-release` snippet |

### 4. Style Rules (Vale checks these)

**DO:**
- Use active voice: "Configure the webhook" not "The webhook should be configured"
- Use second person: "you" not "the user"
- Use present tense: "This node sends" not "This node will send"
- Be direct: "Click Save" not "Please click the Save button"

**DON'T:**
- Use "simple", "easy", "just" (condescending)
- Use "obviously", "clearly" (if obvious, no need to document)
- Use passive voice unless necessary
- Use future tense for current features

### 5. Markdown Formatting

**Code blocks:**
- Always specify language: ```javascript, ```bash, ```yaml
- Use fenced blocks (```) not indented blocks

**Admonitions (MkDocs Material):**
```markdown
!!! info "Title"
    Content here.

!!! warning "Important"
    Warning content.

!!! tip "Pro tip"
    Helpful hint.
```

**Content tabs:**
```markdown
=== "n8n Cloud"

    Cloud-specific content

=== "Self-hosted"

    Self-hosted content
```

### 6. Allowed Tags

Use only these tags (defined in `mkdocs.yml`):
- Tutorial, How-To, Concept, Reference, Troubleshooting
- Cloud, Self-hosted
- Webhook, Nodes, AI

### 7. File Naming

- Use kebab-case: `configure-webhook-trigger.md`
- Be descriptive: `webhook-not-firing.md` not `issue-1.md`
- Match the title (slugified)

## Variables

Common values are in `docs/_variables.yml`. When the mkdocs-macros-plugin is enabled, use:

```markdown
The default port is {{ default_port }}.
Visit [n8n Cloud]({{ cloud_url }}).
```

## Pre-commit Checks

Before committing, these checks run automatically:
1. Vale (style)
2. markdownlint (formatting)
3. cspell (spelling)
4. validate_frontmatter.py (metadata)
5. geo_lint.py (GEO optimization)

To run manually:
```bash
npm run lint
# or individually:
vale docs/path/to/file.md
python scripts/geo_lint.py docs/path/to/file.md
```

## Creating New Documents

1. Determine the content type (tutorial, how-to, concept, reference, troubleshooting)
2. Create file in appropriate folder:
   - `docs/getting-started/` - tutorials
   - `docs/how-to/` - how-to guides
   - `docs/concepts/` - concept explanations
   - `docs/reference/` - reference docs
   - `docs/troubleshooting/` - troubleshooting guides
3. Use the appropriate VS Code snippet (`doc-tutorial`, `doc-howto`, etc.)
4. Fill in all required frontmatter fields
5. Write content following GEO and style rules
6. Run `npm run lint` to verify

## Quick Reference

### Snippet Prefixes (VS Code)
- `doc-tutorial` - Full tutorial template
- `doc-howto` - How-to guide template
- `doc-concept` - Concept explanation template
- `doc-reference` - Reference page template
- `doc-troubleshoot` - Troubleshooting template
- `doc-release` - Release note template
- `fm` - Basic frontmatter
- `note`, `warning`, `tip` - Admonition blocks
- `tabs` - Content tabs
- `mermaid-flow`, `mermaid-seq` - Diagrams
- `table-params`, `table-compare` - Tables

### Config Files
- `.vale.ini` - Style linting rules
- `.markdownlint.yml` - Markdown formatting rules
- `cspell.json` - Spelling dictionary
- `docs-schema.yml` - Frontmatter schema
- `glossary.yml` - Terminology glossary
- `mkdocs.yml` - Site configuration

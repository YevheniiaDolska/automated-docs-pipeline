# Claude Code Instructions for Documentation Pipeline

## 🚨 CRITICAL: Write Documents Right the First Time

**Claude, you MUST follow ALL these rules to avoid 20 iterations of fixes.**
**Every document you create MUST pass ALL linters on the first try.**

## Project Overview

This is an automated documentation pipeline for technical products. When writing or editing documentation, follow these rules strictly to ensure all linting checks pass.

**IMPORTANT**: This pipeline includes comprehensive SEO/GEO optimization with 60+ automated checks. All content MUST pass:

- GEO linting (LLM/AI optimization)
- SEO metadata validation
- Structured data requirements
- Search ranking optimization

## Critical Rules

### 🔴 RULE #1: Use Templates and Snippets When Available

**When creating documentation, prioritize consistency:**

1. **Check for relevant templates in `templates/` directory:**
   - If a matching template exists, use it as base
   - Copy it: `cp templates/[template] docs/[section]/[new-file].md`
   - Modify content while keeping structure

1. **OR use VS Code snippets from `.vscode/docs.code-snippets`:**
   - Type snippet prefix (doc-tutorial, doc-howto, etc.) and press Tab
   - Ensures consistent structure across documentation

1. **If no template matches, create carefully:**
   - Follow the structure from similar existing documents
   - Include all required frontmatter fields
   - Follow all formatting and SEO/GEO rules

1. **ALWAYS update `mkdocs.yml` navigation:**
   - Add new document to appropriate section in nav
   - Use descriptive titles, maintain logical order
   - Claude should ALWAYS update mkdocs.yml when adding docs

**Why this matters:** Templates and snippets ensure:

- Consistent structure and formatting
- All required sections are included
- Frontmatter is complete and valid
- SEO/GEO optimization rules are followed
- Navigation is properly maintained

## Original Critical Rules

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
## Webhook node reference

The Webhook node is a trigger that starts workflows when it receives HTTP requests. It supports GET, POST, PUT, PATCH, DELETE methods and provides built-in authentication options.

```

**Heading rules:**

- Use descriptive headings, NOT generic ones
- BAD: "Overview", "Configuration", "Setup"
- GOOD: "Configure HMAC authentication", "Set up webhook endpoints"

**Fact density:**

- Include concrete facts every 200 words (numbers, code, config values)
- Tables and code blocks count as facts
- Examples: port numbers (8080), timeout values (30s), version numbers (1.2.3)

### 3. Document Types (Diátaxis Framework)

Use these templates based on `content_type`:

| Type | Purpose | Template |
| ------ | --------- | ---------- |
| `tutorial` | Learning-oriented, step-by-step | `doc-tutorial` snippet |
| `how-to` | Task-oriented, specific goals | `doc-howto` snippet |
| `concept` | Understanding-oriented, explanations | `doc-concept` snippet |
| `reference` | Information-oriented, precise specs | `doc-reference` snippet |
| `troubleshooting` | Problem → cause → solution | `doc-troubleshoot` snippet |
| `release-note` | Version changes | `doc-release` snippet |

### 4. Style Rules (Vale checks these)

**🔴 CRITICAL: All documentation MUST pass Vale style checks on first write!**

**Vale Configuration:**

- **American English** - Use US spelling only
- **Google Developer Style Guide** - Primary style guide (may be Microsoft Writing Guide for some projects)
- **write-good** - Clear, concise writing rules

**Specific Vale Rules to Follow:**

**American English:**

- Use US spelling: "color", "optimize", "analyze", "center"
- NOT British spelling variants
- Use "license" (verb and noun)
- Use "canceled" not "cancelled"

**Google Style Guide Requirements:**

- **Acronyms**: Write out on first use: "Application Programming Interface (API)"
- **Contractions**: Avoid them. Use "do not" instead of "don't"
- **Numbers**: Spell out one through nine, use numerals for 10 and above
- **Oxford comma**: Always use it: "red, white, and blue"
- **Headings**: Use sentence case, not Title Case
- **Lists**: Use parallel structure (all items start with same part of speech)

**write-good Rules:**

- **Avoid weasel words**: "many", "various", "very", "extremely", "fairly"
- **No passive voice**: "Configure the setting" NOT "The setting should be configured"
- **Avoid adverbs**: "quickly", "easily", "simply" - be specific instead
- **No clichés**: "at the end of the day", "low-hanging fruit"
- **Be specific**: "in 5 seconds" not "quickly"

**DO:**

- Use active voice: "Configure the webhook" not "The webhook should be configured"
- Use second person: "you" not "the user"
- Use present tense: "This node sends" not "This node will send"
- Be direct: "Click Save" not "Please click the Save button"
- Be specific: "Processing takes 2-3 seconds" not "Processing is fast"

**DON'T:**

- Use "simple", "easy", "just", "simply", "easily" (condescending weasel words)
- Use "obviously", "clearly" (if obvious, no need to document)
- Use passive voice unless necessary
- Use future tense for current features
- Use hedge words: "generally", "usually", "often", "sometimes" (be precise)
- Start sentences with "There is/are" (wordy)

### 5. Markdown Formatting

**Code blocks:**

- Always specify language: `javascript`, `bash`, `yaml`
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

1. **Vale** (style - American English, Google/Microsoft Style Guide, write-good)
1. **markdownlint** (formatting)
1. **cspell** (spelling)
1. **validate_frontmatter.py** (metadata)
1. **seo_geo_optimizer.py** (comprehensive SEO/GEO optimization)

**🔴 Vale is configured STRICTLY - no --no-exit flag!**

- ALL Vale errors and warnings will block commits
- Write correctly the first time to avoid multiple iterations
- Check Vale output carefully: it shows exactly what needs fixing

To run manually:

```bash
# Run Vale style checks (MUST pass!)
vale docs/path/to/file.md

# Run all SEO/GEO checks
python scripts/seo_geo_optimizer.py docs/

# Run with auto-fix
python scripts/seo_geo_optimizer.py docs/ --fix

# Run all checks at once
npm run lint

# Individual checks
markdownlint docs/path/to/file.md
```

## Creating New Documents

### IMPORTANT: Use Templates and Snippets for Consistency

**ALWAYS use existing templates and snippets when creating new documentation:**

1. **Check for existing templates first:**

   ```bash
   ls templates/

```bash

   Available templates include:

   - `tutorial.md` - Step-by-step learning guides
   - `how-to.md` - Task-oriented guides
   - `concept.md` - Explanations and understanding
   - `reference.md` - Technical specifications
   - `troubleshooting.md` - Problem-solving guides
   - `quickstart.md` - Getting started quickly
   - `api-reference.md` - API documentation
   - `webhooks-guide.md` - Webhook-specific docs
   - And many more specialized templates

1. **Copy the most relevant template:**

   ```bash
   # Example: Creating a new webhook how-to guide
   cp templates/webhooks-guide.md docs/how-to/your-new-webhook-guide.md

```

1. **OR use VS Code snippets (preferred for consistency):**
   - Type the snippet prefix and press Tab
   - Available snippets:
     - `doc-tutorial` - Full tutorial with all sections
     - `doc-howto` - How-to guide structure
     - `doc-concept` - Concept explanation
     - `doc-reference` - Reference documentation
     - `doc-troubleshoot` - Troubleshooting guide
     - `fm` - Basic frontmatter only
     - `note`, `warning`, `tip` - Admonition blocks
     - `tabs` - Content tabs for Cloud/Self-hosted
     - `mermaid-flow` - Flow diagrams
     - `table-params` - Parameter tables

1. **Determine the correct location:**
   - `docs/getting-started/` - Tutorials and quickstarts
   - `docs/how-to/` - Step-by-step task guides
   - `docs/concepts/` - Understanding and theory
   - `docs/reference/` - API, configuration, specifications
   - `docs/reference/nodes/` - Node-specific reference
   - `docs/troubleshooting/` - Problem resolution
   - `docs/` - Top-level pages (index, tags, etc.)

1. **Update navigation in mkdocs.yml:**

   ```yaml
   nav:

     - Getting Started:
       - getting-started/index.md
       - "Your New Tutorial": getting-started/your-new-tutorial.md  # Add here

```text

   **Rules for nav updates:**

   - Add new documents in the appropriate section
   - Use descriptive titles (not just filenames)
   - Maintain alphabetical or logical order within sections
   - For multi-level navigation, create subsections:

     ```yaml

     - Reference:
       - reference/index.md
       - Nodes:
         - Webhook node: reference/nodes/webhook.md
         - HTTP node: reference/nodes/http.md  # New node

```

1. **File naming conventions:**
   - Use kebab-case: `configure-webhook-trigger.md`
   - Be descriptive: `webhook-hmac-authentication.md` not `auth.md`
   - Match the title (slugified)

1. **Content requirements:**
   - Fill in all required frontmatter fields
   - Keep first paragraph under 60 words
   - Include concrete examples and code
   - Follow GEO and style rules

1. **Validate before committing:**

   ```bash
   # Run all checks
   npm run lint

   # Or individual checks
   python scripts/validate_frontmatter.py
   python scripts/seo_geo_optimizer.py docs/your-new-file.md

```bash

### Template Selection Guide

| If you're documenting... | Use this template | Location | Snippet |
| ------------------------- | ------------------- | ---------- | --------- |
| First-time setup | `quickstart.md` | `docs/getting-started/` | `doc-tutorial` |
| Step-by-step learning | `tutorial.md` | `docs/getting-started/` | `doc-tutorial` |
| Specific task | `how-to.md` | `docs/how-to/` | `doc-howto` |
| Architecture/theory | `concept.md` | `docs/concepts/` | `doc-concept` |
| API endpoints | `api-reference.md` | `docs/reference/` | `doc-reference` |
| Node details | `reference.md` | `docs/reference/nodes/` | `doc-reference` |
| Webhook features | `webhooks-guide.md` | Appropriate section | `doc-howto` |
| Common problems | `troubleshooting.md` | `docs/troubleshooting/` | `doc-troubleshoot` |
| Version changes | `release-note.md` | `docs/releases/` | `doc-release` |

### Navigation Update Checklist

When adding a new document:

- [ ] Place file in correct directory based on content type
- [ ] Update `mkdocs.yml` nav section
- [ ] Use descriptive title in nav (not just filename)
- [ ] Maintain logical order (alphabetical or by importance)
- [ ] Test navigation locally: `mkdocs serve`
- [ ] Verify all links work
- [ ] Check that page appears in correct section

### Automated Navigation Management

**How Claude should handle document placement:**

1. **Automatic location selection based on content_type:**

```text
   content_type: tutorial → docs/getting-started/
   content_type: how-to → docs/how-to/
   content_type: concept → docs/concepts/
   content_type: reference → docs/reference/
   content_type: troubleshooting → docs/troubleshooting/

```

1. **Automatic mkdocs.yml update - Claude MUST:**
   - Read current mkdocs.yml structure
   - Find the appropriate nav section based on content_type
   - Add the new document with a descriptive title
   - Maintain logical ordering (alphabetical or by complexity)
   - Example commit message: "Add webhook authentication guide to how-to section"

1. **Smart placement logic Claude should follow:**

   ```yaml
   # If adding a new webhook how-to:

   1. File goes in: docs/how-to/configure-webhook-auth.md
   1. Update mkdocs.yml nav section "How-To Guides"
   1. Place alphabetically or after related webhook docs
   1. Use descriptive title: "Configure webhook authentication"

```yaml

1. **GitHub Actions will verify:**
   - No orphaned pages (files not in nav)
   - Proper categorization
   - Creates issues if navigation needs fixing

1. **Example nav update:**

   ```yaml
   # When adding a new webhook authentication guide:
   nav:

     - How-To Guides:
       - how-to/index.md
       - Configure Webhook triggers: how-to/configure-webhook-trigger.md
       - Authenticate Webhook requests: how-to/authenticate-webhooks.md  # NEW

```

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

## Important Linting Rules to Follow

### NO Emoji or Special Unicode in Code

**NEVER use emoji or special Unicode characters in:**

- Python scripts (causes encoding errors on Windows: cp1251 doesn't support them)
- Use plain ASCII: `->` instead of `→`, text instead of emoji
- Documentation can use ✓ and ✗ for checkmarks if needed
- Avoid all other emoji

### Markdown Formatting (IMPORTANT - Follow these rules!)

**Blank lines are REQUIRED for proper rendering:**

- Before and after ALL lists
- Before and after ALL code blocks
- Before and after ALL headings
- This ensures MkDocs renders everything correctly

**Code blocks:**

- ALWAYS specify language: ```python, ```bash, ```yaml
- Use fenced blocks (```), never indented (4 spaces)
- Exception: MkDocs content tabs may use indentation - that's OK

**Lists:**

- Ordered lists: Use `1.` for ALL items (auto-renumbering)

  ```markdown

  1. First item
  1. Second item
  1. Third item

```javascript

- This allows easy reordering without manual renumbering

**Headings:**

- Only ONE H1 (#) per document - this is the main title
- Use proper hierarchy: # → ## → ###, never skip levels
- Headings need blank lines before and after
- Example structure:

  ```markdown
  # Main Title (only one!)

  ## Section

  ### Subsection

  ## Another Section

```

### YAML Files

**Multiline strings in YAML workflows:**

- JavaScript template literals: Use `\n` for line breaks, not actual newlines

  ```yaml
  message = `Line 1\nLine 2\nLine 3`  # ✅
  message = `Line 1
  Line 2`  # ❌ Will break YAML parsing

```yaml

- Python in workflows: Use heredoc or external scripts
- Keep inline code simple to avoid YAML parsing issues

### Windows Compatibility

**Avoid Unicode issues:**

- No emoji or special Unicode characters in print statements
- Use plain ASCII text for console output
- This affects Python scripts that might run on Windows

### File Naming

- Always use absolute paths in tools, not relative paths
- Use kebab-case for file names
- Avoid special characters in file names

## CRITICAL Formatting Rules (ALL documents MUST follow)

**Use templates from `templates/` directory - they already follow these rules!**

### Essential Structure Requirements

**EVERY document MUST have:**

- ✅ **Blank line after frontmatter**
- ✅ **Blank lines before AND after ALL headings**
- ✅ **Blank lines before AND after ALL code blocks**
- ✅ **Blank lines before AND after ALL lists**
- ✅ **All ordered lists use `1.` for EVERY item** (auto-renumbers on render)
- ✅ **Code blocks ALWAYS have language specified** (```python, ```bash, etc.)
- ✅ **Only ONE H1 (#)** - must match the title in frontmatter
- ✅ **First paragraph under 60 words** for SEO/GEO optimization

### Template Usage

**ALWAYS use existing templates:**

1. Check `templates/` directory for matching template
1. Copy the template structure exactly
1. Templates are PRE-VALIDATED to pass all checks
1. DO NOT modify the formatting structure

Available templates in `templates/`:

- tutorial.md
- how-to.md
- concept.md
- reference.md
- troubleshooting.md
- api-reference.md
- quickstart.md
- migration-guide.md
- And more...

## Claude's Step-by-Step Process for New Documentation

When user asks to create new documentation, Claude MUST:

1. **Select template/snippet:**
   - Check `templates/` for matching template
   - OR use VS Code snippet (doc-tutorial, doc-howto, etc.)
   - NEVER write from scratch

1. **Choose location:**
   - Based on content_type in frontmatter
   - Place in correct folder (getting-started/, how-to/, etc.)

1. **Update mkdocs.yml:**
   - Add to appropriate nav section
   - Use descriptive title
   - Maintain logical order

1. **Follow formatting rules:**
   - Blank lines around headings/lists/code
   - Only one H1
   - Code blocks with language
   - No emoji in Python

1. **Validate:**
   - Run linting checks
   - Ensure frontmatter complete
   - First paragraph under 60 words

## Pull Request Reviews

### 🔴 CRITICAL: Fix BOTH Errors AND Warnings

**When reviewing pull requests or fixing linting issues, Claude MUST:**

1. **Fix ALL errors (red)** - These block commits and merges
1. **Fix ALL warnings (yellow)** - These indicate quality issues
1. **Not ignore any linting output** - Both errors and warnings need attention

**Why this matters:**
- Warnings today become technical debt tomorrow
- Clean code has zero warnings, not just zero errors
- Warnings often indicate SEO/GEO optimization issues
- Users expect professional quality with no linting issues at all

**Example workflow when reviewing PR:**
```bash
# Run all checks
npm run lint

# If output shows:
# ❌ ERROR: Missing frontmatter
# ⚠️ WARNING: Passive voice detected
# ⚠️ WARNING: Line too long

# Claude MUST fix ALL three issues, not just the error
```

## Automatic Validation

**TWO layers of protection ensure quality:**

1. **Pre-commit hooks** (local) - Run automatically before commit
1. **CI/CD checks** (GitHub) - Same checks run on PR/push

Both use IDENTICAL rules, so if it passes locally, it passes in CI.

## Quick Checklist for New Documents

**Claude, VERIFY each point before saving ANY file:**

**Content & Style (Vale):**

- [ ] **American English spelling** (optimize, color, analyze)
- [ ] **Active voice only** (no passive constructions)
- [ ] **No weasel words** (simple, easy, just, simply, various, many)
- [ ] **Second person "you"** not "the user" or "users"
- [ ] **Present tense** for current features
- [ ] **Specific facts** not vague claims ("2 seconds" not "quickly")
- [ ] **No contractions** (do not, not don't)
- [ ] **Oxford comma** in lists
- [ ] **Sentence case** in headings

**Formatting (Markdown):**

- [ ] **Blank lines present:**
  - Before/after headings
  - Before/after lists
  - Before/after code blocks
- [ ] **Only ONE H1 (#) heading**
- [ ] **Code blocks have language specified** (```python, not just ```)
- [ ] **Ordered lists use `1.` for all items**
- [ ] **No emoji in Python scripts** (plain ASCII only)
- [ ] **No bare URLs** - use [text](url) format

**Metadata & SEO:**

- [ ] **Frontmatter complete** with all required fields
- [ ] **First paragraph under 60 words** for GEO optimization
- [ ] **No dollar signs before commands** in code blocks
- [ ] **Title under 70 characters**
- [ ] **Description 50-160 characters**

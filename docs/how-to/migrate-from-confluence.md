---
title: Migrate documentation from Confluence
description: Import Confluence pages into the documentation pipeline with automatic
  quality enhancement, SEO optimization, and knowledge extraction.
content_type: how-to
product: both
last_reviewed: '2026-03-28'
tags:
- How-To
original_author: Kroha
---



# Migrate documentation from Confluence

The Confluence migration tool imports Confluence pages into pipeline-ready
Markdown with automatic frontmatter, heading hierarchy, SEO/GEO optimization,
and knowledge module extraction. It supports two import methods: REST API
(direct) and ZIP export (offline).

## Before you begin

Verify you have the following before starting the migration:

- Python 3.10 or higher installed
- The documentation pipeline cloned and dependencies installed
- For REST API mode: a Confluence API token (Cloud) or Personal Access Token
  (Server/Data Center)
- For ZIP export mode: a Confluence HTML+XML export ZIP file
- Sufficient disk space for imported Markdown and attachments

## Choose a migration method

The pipeline provides two ways to import Confluence content:

| Method | Best for | Requirements |
| --- | --- | --- |
| REST API | Ongoing sync, selective spaces, incremental updates | API token, network access to Confluence |
| ZIP export | One-time migration, air-gapped environments, full space backup | Admin access to export from Confluence |

## Method 1: Import with REST API

REST API mode connects directly to your Confluence instance, fetches pages,
and converts them to Markdown. It supports both Confluence Cloud (API v2) and
Server/Data Center (API v1).

### Step 1: Create an API token

=== "Cloud"

    1. Go to [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
    1. Select **Create API token**
    1. Enter a label (for example, "docs-migration") and select **Create**
    1. Copy the token value

=== "Server/Data Center"

    1. Go to your profile in Confluence Server
    1. Select **Personal Access Tokens** and then **Create token**
    1. Enter a name and select **Create**
    1. Copy the token value

### Step 2: Identify space keys

Find the space keys you want to import. Space keys appear in Confluence URLs
after `/spaces/` or `/display/`. For example, in a URL like
`mycompany.atlassian.net/wiki/spaces/DEV/overview`, the space key is `DEV`.

### Step 3: Run the migration

=== "Cloud"

    ```bash
    python3 scripts/run_confluence_migration.py \
      --confluence-url https://mycompany.atlassian.net \
      --confluence-token YOUR_API_TOKEN \
      --confluence-username your-email@company.com \
      --space-keys DEV,OPS \
      --include-attachments
    ```

=== "Server/Data Center"

    ```bash
    python3 scripts/run_confluence_migration.py \
      --confluence-url https://confluence.internal.company.com \
      --confluence-token YOUR_PERSONAL_ACCESS_TOKEN \
      --space-keys DEV,OPS \
      --include-attachments
    ```

The `--confluence-username` flag is required for Cloud (your Atlassian email
address) but optional for Server/Data Center when using a Personal Access
Token.

### Incremental sync

After the initial import, use `--incremental` to fetch only pages modified
since the last sync:

```bash
python3 scripts/run_confluence_migration.py \
  --confluence-url https://mycompany.atlassian.net \
  --confluence-token YOUR_API_TOKEN \
  --confluence-username your-email@company.com \
  --space-keys DEV \
  --incremental
```

The pipeline stores sync state in `.confluence_sync_state.json` at the
repository root. This file tracks the last sync timestamp and page versions
to determine which pages changed.

## Method 2: Import from ZIP export

ZIP export mode processes a Confluence HTML+XML export file offline. Use this
method when you do not have API access or need to migrate from an
air-gapped environment.

### Step 1: Export from Confluence

1. Open Confluence and go to the space you want to export
1. Select **Space settings** and then **Content Tools** and then **Export**
1. Choose **XML** export format
1. Select **Full Export** (includes all pages and attachments)
1. Wait for the export to complete and download the ZIP file

### Step 2: Run the migration

```bash
python3 scripts/run_confluence_migration.py \
  --export-zip /path/to/confluence-export.zip
```

## Customize the output directory

By default, imported Markdown files go to
`docs/imported/confluence/<timestamp>/`. Override this with `--output-dir`:

```bash
python3 scripts/run_confluence_migration.py \
  --export-zip /path/to/confluence-export.zip \
  --output-dir docs/imported/my-space
```

## What happens after import

The migration pipeline runs 14 post-processing steps automatically:

1. **Normalize check (before)** -- detect formatting issues in imported
   Markdown
1. **SEO/GEO audit (before)** -- baseline SEO/GEO score for imported content
1. **Normalize fix** -- fix list formatting, spacing, and section structure
1. **Quality enhancement** -- add frontmatter, fix heading hierarchy, fix
   code blocks, replace variables
1. **SEO/GEO fix** -- auto-correct metadata and content issues
1. **Validate frontmatter** -- verify all required frontmatter fields
1. **Normalize check (after)** -- confirm formatting issues are resolved
1. **SEO/GEO audit (after)** -- measure improvement in SEO/GEO scores
1. **Code examples smoke test** -- validate code blocks have language tags
1. **Knowledge extraction** -- extract RAG-ready knowledge modules
1. **Validate knowledge modules** -- check module schema and dependencies
1. **Rebuild retrieval index** -- update the knowledge retrieval index
1. **Glossary sync** -- synchronize terminology with the project glossary
1. **Final lint check** -- run a final SEO/GEO pass

Skip post-processing with `--skip-post-checks` if you want to run the steps
manually:

```bash
python3 scripts/run_confluence_migration.py \
  --export-zip /path/to/confluence-export.zip \
  --skip-post-checks
```

## Enable LLM-powered quality enhancement

Add `--use-llm` to enable AI-powered improvements during the quality
enhancement step:

```bash
python3 scripts/run_confluence_migration.py \
  --confluence-url https://mycompany.atlassian.net \
  --confluence-token YOUR_API_TOKEN \
  --confluence-username your-email@company.com \
  --space-keys DEV \
  --use-llm
```

LLM enhancement performs three additional operations:

- **Replace placeholder code** -- detects generic placeholders (`foo`, `bar`,
  `example.com`, `YOUR_API_KEY`) in code blocks and replaces them with
  realistic, runnable examples
- **Add missing sections** -- adds essential sections based on content type
  (error handling for how-to guides, rate limits for API references,
  security considerations for concept pages)
- **Verify code output** -- executes Python code blocks and corrects
  documented output comments that do not match actual execution results

LLM enhancement requires an LLM provider configured in your environment.
Without a provider, the pipeline skips LLM steps and logs a warning.

## Review migration reports

The pipeline generates two report files in the reports directory
(default: `reports/`):

- `confluence_migration_report.json` -- machine-readable report with page
  counts, check results, and status
- `confluence_migration_report.md` -- human-readable report with migration
  summary, automatic fixes applied, and check results

Specify a custom reports directory with `--reports-dir`:

```bash
python3 scripts/run_confluence_migration.py \
  --export-zip /path/to/confluence-export.zip \
  --reports-dir /path/to/reports
```

## Troubleshoot common issues

### Authentication fails with 401 error

**Cause:** Invalid or expired API token.

**Fix:** Generate a new token following the steps in
[Create an API token](#step-1-create-an-api-token). For Cloud, verify you use
your email address with `--confluence-username`, not your display name.

### Rate limiting (429 responses)

**Cause:** Confluence rate limits API requests.

**Fix:** The pipeline automatically retries with exponential backoff (3
retries). For large spaces with more than 1,000 pages, the pipeline
paginates requests automatically. If rate limiting persists, wait 60 seconds
and retry.

### Large spaces cause memory issues

**Cause:** Spaces with more than 5,000 pages consume significant memory
during conversion.

**Fix:** Import specific spaces one at a time instead of combining multiple
large spaces in a single `--space-keys` value.

### ZIP export missing entities.xml

**Cause:** The ZIP file does not contain the expected `entities.xml` file.

**Fix:** Re-export from Confluence using **XML** format, not HTML-only
export. The XML export includes `entities.xml` which contains page content
and metadata.

### Encoding errors in imported content

**Cause:** Confluence pages contain special characters that were not properly
encoded during export.

**Fix:** The pipeline uses UTF-8 encoding by default. If you see encoding
artifacts, re-export from Confluence and verify the export completed without
warnings.

## Next steps

After migration completes:

- Review the migration report in `reports/confluence_migration_report.md`
- Check imported files in the output directory for content accuracy
- Run `python3 scripts/seo_geo_optimizer.py docs/imported/` to verify
  SEO/GEO scores
- Add imported documents to the `mkdocs.yml` navigation
- Run `python3 scripts/validate_frontmatter.py --paths docs/imported/` to
  confirm frontmatter compliance

---
title: "Auto-Doc Pipeline quick start"
description: "Set up the Auto-Doc Pipeline in minutes, run gap analysis, and generate documentation with validation-ready commands."
content_type: tutorial
product: both
tags:
  - Tutorial
  - AI
last_reviewed: "2026-03-07"
---

# Quick start (5 minutes)

This tutorial shows you how to install the Auto-Doc Pipeline, enable smooth weekly automation,
and produce docs updates that pass validation checks.

## Prerequisites

Verify these are installed:

```bash
node --version   # 18+ required
python3 --version  # 3.11+ required
git --version
```

If anything is missing:

- Node.js: [Download Node.js](https://nodejs.org/)
- Python: [Download Python](https://www.python.org/downloads/)
- Git: [Install Git](https://git-scm.com/)

## Step 1: Clone and install

```bash
git clone <repo-url>
cd "Auto-Doc Pipeline"
npm install
pip install -r requirements.txt
```

On Windows, use `py -3 -m pip install -r requirements.txt` if `pip` is not on PATH.

## Step 2: Recommended weekly automation (no manual weekly commands)

Provision once into the target repository and install scheduler:

```bash
python3 scripts/provision_client_repo.py \
  --client profiles/clients/blockstream-demo.client.yml \
  --client-repo /path/to/client-repo \
  --docsops-dir docsops \
  --install-scheduler linux
```

After that, weekly `reports/consolidated_report.json` is generated automatically by `docsops/scripts/run_weekly_gap_batch.py`.

## Step 3: Generate the consolidated report now (optional immediate run)

```bash
npm run consolidate
```

This runs gap analysis, builds the KPI wall, evaluates SLA compliance, and merges everything into `reports/consolidated_report.json`.

To regenerate only the consolidated file from existing reports:

```bash
npm run consolidate:reports-only
```

## Step 4: Process with Claude Code

Open Claude Code in the project directory and give it the report:

```text
Process reports/consolidated_report.json
```

Claude Code reads the consolidated report, identifies documentation gaps, and generates or updates Markdown files in `docs/` following `CLAUDE.md`.
If a required doc type has no template, it creates a new template first and then generates docs from that template.

## Step 5: Review and commit

Check what changed:

```bash
git diff docs/
```

Validate the generated documentation:

```bash
npm run validate:minimal
```

If everything passes, commit:

```bash
git add docs/ mkdocs.yml
git commit -m "docs: generate documentation from gap analysis"
```

## Optional: Ask AI module (beginner setup)

If a client wants Ask AI configuration support, use these commands:

```bash
npm run askai:status
npm run askai:enable
npm run askai:configure -- --provider openai --billing-mode user-subscription
```

If the client does not need Ask AI, keep it disabled:

```bash
npm run askai:disable
```

If the client asks for a live Ask AI runtime (endpoint + widget), install it:

```bash
npm run askai:runtime:install
```

## What each command does

| Command | Purpose |
| --- | --- |
| `npm run consolidate` | Run all analyses and merge into one report |
| `npm run validate:minimal` | Fast lint check (markdownlint, frontmatter, GEO, examples) |
| `npm run validate:full` | Full lint check including e2e and golden tests |
| `npm run serve` | Preview docs site locally (auto-detects MkDocs or Docusaurus) |
| `npm run lint` | Run all individual linters (Vale, markdownlint, cspell, GEO) |
| `npm run askai:status` | Show Ask AI module configuration |
| `npm run askai:enable` | Enable Ask AI module |
| `npm run askai:disable` | Disable Ask AI module |
| `npm run askai:runtime:install` | Install Ask AI runtime pack in current repo |
| `npm run gaps` | Run gap analysis only |
| `npm run kpi-wall` | Generate KPI dashboard |

## Next steps

| Goal | Guide |
| --- | --- |
| Understand all features | [README](./README.md) |
| Full setup with troubleshooting | [Setup guide](./README_SETUP.md) |
| Install into another repository | [Setup for projects](./SETUP_FOR_PROJECTS.md) |
| Configure all client keys | [Unified client config](./docs/operations/UNIFIED_CLIENT_CONFIG.md) |
| Apply Basic/Pro/Enterprise plans | [Plan tiers](./docs/operations/PLAN_TIERS.md) |
| Customize for a company | [Customization guide](./CUSTOMIZATION_PER_COMPANY.md) |
| Windows setup from scratch | [Beginner guide](./BEGINNER_GUIDE.md) |

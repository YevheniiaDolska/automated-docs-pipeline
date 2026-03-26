---
title: Assemble intent experiences
description: Build user-intent documentation and channel bundles from reusable knowledge
  modules with validation, indexing, and consistent outputs.
content_type: how-to
product: both
tags:
- How-To
- AI
- Reference
last_reviewed: '2026-03-07'
original_author: Developer
---

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->


# Assemble intent experiences

Use this workflow to build a clean docs page and channel-ready AI bundle for one user intent from reusable knowledge modules.

```bash
npm run validate:knowledge
npm run build:intent -- --intent configure --audience operator --channel docs
npm run build:knowledge-index
```

## Before you start

You need:

- Python 3.10 or later
- Existing modules in `knowledge_modules/`
- Write access to `docs/reference/intent-experiences/` and `reports/intent-bundles/`

## Step 1: Validate module integrity

Run:

```bash
npm run lint:knowledge
```

This command checks required fields, allowed metadata values, missing dependencies, and dependency cycles.

## Step 2: Generate a docs experience page

Run:

```bash
npm run build:intent -- --intent configure --audience operator --channel docs
```

Expected output includes a generated Markdown page in:

```text
docs/reference/intent-experiences/configure-operator.md
```

## Step 3: Generate assistant and automation bundles

Run these commands for runtime channels:

```bash
npm run build:intent -- --intent configure --audience operator --channel assistant
npm run build:intent -- --intent configure --audience operator --channel automation
```

These outputs are JSON bundles in `reports/intent-bundles/`.

## Step 4: Rebuild retrieval index

Run:

```bash
npm run build:knowledge-index
```

The index file `docs/assets/knowledge-retrieval-index.json` now contains module-level records for search and assistant retrieval.

Generate graph and eval artifacts:

```bash
npm run build:knowledge-graph
npm run eval:retrieval
```

## Common issues

### No modules matched

Cause: intent, audience, or channel does not match module metadata.

Fix:

1. Confirm your module has `status: active`.
1. Confirm the target intent is listed under `intents`.
1. Confirm the target audience or `all` is listed under `audiences`.

### Dependency validation fails

Cause: a module references a missing dependency.

Fix:

1. Add the referenced module file.
1. Correct the `dependencies` value to an existing module `id`.

## Performance and quality notes

- Keep modules focused; 150-400 words per `docs_markdown` block works well.
- Keep assistant context under 300 words for faster retrieval.
- Re-run `npm run validate:knowledge` in CI for every module change.

## Next steps

- [Intelligent knowledge system architecture](../concepts/intelligent-knowledge-system.md)
- [Intent experiences reference](../reference/intent-experiences/index.md)

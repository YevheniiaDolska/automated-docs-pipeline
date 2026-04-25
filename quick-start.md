---
title: "Quick start"
description: "Fast local start for onboarding, wizard setup, autopipeline run, and validation commands."
content_type: how-to
product: both
last_reviewed: "2026-04-25"
tags:
  - Setup
  - Quickstart
---

# Quick start (15 minutes)

## Install

```bash
python3 -m pip install -r requirements.txt
npm install
```

## Onboard client locally

```bash
python3 scripts/onboard_client.py --mode install-local
python3 docsops/scripts/setup_client_env_wizard.py
```

## Run full autopipeline once

```bash
python3 scripts/run_autopipeline.py --docsops-root docsops --reports-dir reports --auto-generate
```

## Validate

```bash
npm run lint
python3 scripts/validate_knowledge_modules.py
python3 scripts/generate_knowledge_retrieval_index.py
```

## Read next

- `README.md`
- `SETUP_GUIDE.md`
- `USER_GUIDE.md`

## Next steps

- [Documentation index](../index.md)

---
title: "Setup guide canonical"
description: "Canonical setup flow for bundle installation, wizard configuration, and autopipeline execution."
content_type: how-to
product: both
last_reviewed: "2026-04-25"
tags:
  - Setup
  - Operations
---

# Setup guide (canonical)

This is the canonical setup entry for repository-level setup documentation.

Mirror copy path:

- `docsops/README_SETUP.md` (generated from this file)

## What this setup covers

1. Local prerequisites.
1. Bundle build/install flow.
1. Client setup wizard.
1. Weekly autopipeline operation.
1. Validation and troubleshooting entry points.

## Quick install

```bash
python3 -m pip install -r requirements.txt
npm install
python3 scripts/onboard_client.py --mode install-local
python3 docsops/scripts/setup_client_env_wizard.py
```

## Run autopipeline

```bash
python3 scripts/run_autopipeline.py --docsops-root docsops --reports-dir reports --auto-generate
```

## Commercial/runtime boundaries (current)

- Community/degraded mode: free lint defaults only.
- Full implementation: full automation except retrieval-time RAG.
- Full+RAG: complete stack including retrieval-time RAG.

## Related canonical docs

- `README.md`
- `SETUP_GUIDE.md`
- `USER_GUIDE.md`
- `docs/operations/UNIFIED_CLIENT_CONFIG.md`
- `docs/operations/CANONICAL_FLOW.md`

## Next steps

- [Documentation index](../index.md)

---
title: "Client handoff in 3 steps"
description: "Install the docsops bundle, configure local secrets, and run weekly automation with a minimal client-side workflow."
content_type: reference
product: both
tags:
  - Reference
  - VeriOps
  - Setup
last_reviewed: "2026-03-17"
---

# Client handoff: 3 steps

## Current product definition (2026-03-25)

This content follows the active implementation baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` modes.
1. The smooth autopipeline covers all five API protocols (REST, GraphQL, gRPC, AsyncAPI, and WebSocket) in one operational model.
1. Non-REST flow includes generated server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated, with Postman-supported auto-prepare in external mode.
1. Contract test assets are generated automatically and merged with smart-merge so manual/customized cases are preserved and flagged for review when needed.
1. Knowledge/RAG maintenance, terminology sync, and quality/compliance gates run through the same automation surface when enabled.
1. Plan tiers gate advanced capabilities; higher plans include broader non-REST and governance scope.


Use this page on the client side only.


## Non-API documentation flows (docs-first scope)

The platform is not limited to API-first automation. In active production usage, it also runs full docs-first and code-first documentation operations for non-API content:

1. Detects content gaps, stale pages, and drift across product docs, runbooks, admin guides, troubleshooting, and release notes.
1. Generates and updates documentation types beyond API references (tutorial, how-to, concept, reference, troubleshooting, release-note, security, SDK, user/admin, and operations docs).
1. Applies normalization, style, metadata/frontmatter, SEO/GEO, terminology governance, and snippet validation to all documentation categories.
1. Executes lifecycle controls (active/deprecated/removed states, replacement links, and freshness cadence).
1. Runs knowledge extraction and retrieval preparation for all docs, not only API pages.
1. Produces consolidated review artifacts so human input is focused on approval and business accuracy, not repetitive formatting and synchronization work.

## Step 1: Copy bundle into repository

Copy the received folder into your project repository as:

```text
<your-repo>/docsops/
```

## Step 2: Fill local secrets (not in git)

1. In repository root, copy:
   - `docsops/.env.docsops.local.template` -> `/.env.docsops.local`
1. Fill real values in `/.env.docsops.local`.
1. Ensure `.gitignore` contains:

```gitignore
/.env.docsops.local
reports/docsops-weekly.log
```

If unsure which values are required, open:

- `docsops/ENV_CHECKLIST.md`

## Step 3: Install weekly scheduler once

Before installing scheduler, make sure git access for this repository already works in terminal for the same OS user (SSH key or credential helper/PAT).
Scheduler runs under that same user. If `git pull` fails for this user, weekly run will fail too.

Linux/macOS:

```bash
bash docsops/ops/install_cron_weekly.sh
```

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File docsops/ops/install_windows_task.ps1
```

Default schedule: Monday 10:00 local machine time.

## Optional: one-click Confluence migration

If you export legacy docs from Confluence as ZIP:

```bash
npm run confluence:migrate -- --export-zip /path/to/confluence-export.zip
```

Result:

1. Imported docs in `docs/imported/confluence/<timestamp>/`
1. JSON report: `reports/confluence_migration_report.json`
1. Human report: `reports/confluence_migration_report.md`

## Run generation correctly (short commands)

Rule:

```text
Always use docsops pipeline commands. Never ask for ad-hoc doc generation.
```

Commands:

1. Weekly reports (manual on demand):

```bash
python3 docsops/scripts/run_weekly_gap_batch.py --docsops-root docsops --reports-dir reports --since 7
```

1. Regular docs update:

```text
Run docsops update from reports/consolidated_report.json via pipeline.
```

1. API-first update:

```text
Run API-first update via scripts/run_api_first_flow.py (planning notes -> OpenAPI -> docs/sandbox).
```

## Upgrade from pilot to full implementation

1. Replace `docsops/` folder in your repo with the new full bundle.
1. Keep the same `client_id` as in pilot.
1. Recreate local secrets file from new template:
   - `docsops/.env.docsops.local.template` -> `/.env.docsops.local`
1. Re-run scheduler installer:
   - Linux/macOS: `bash docsops/ops/install_cron_weekly.sh`
   - Windows: `powershell -ExecutionPolicy Bypass -File docsops/ops/install_windows_task.ps1`
1. Run one manual check:
   - `python3 docsops/scripts/run_weekly_gap_batch.py --docsops-root docsops --reports-dir reports --since 7`

Scheduler conflict safety:

1. Cron entry is replaced by marker for the same `client_id`.
1. Windows task is overwritten by same task name.
1. If you change `client_id`, duplicate scheduler entries can appear.

## Verify in 30 seconds

1. Wait for next scheduled run (or run `docsops/ops/run_weekly_docsops.sh` manually).
1. Check that `reports/consolidated_report.json` has fresh Modified timestamp.
1. If errors appear, check `reports/docsops-weekly.log`.

## Troubleshooting: scheduler cannot run `git pull`

### Case 1: Manual `git pull` works, scheduler fails

Cause: scheduler runs under another OS user.

Fix:

1. Linux/macOS: run `crontab -l` under the same user who has repo access.
1. Windows: in Task Scheduler, set task user to your normal account (not `SYSTEM`).
1. Re-run one manual scheduler script under that same user:

```bash
bash docsops/ops/run_weekly_docsops.sh
```

### Case 2: SSH key works only in interactive terminal

Cause: key is loaded in temporary `ssh-agent` session, but scheduler session has no key.

Fix:

1. Ensure the private key exists in `~/.ssh/`.
1. Add host + key config in `~/.ssh/config` (for example `Host github.com`, `IdentityFile ~/.ssh/id_ed25519`).
1. Verify non-interactive auth:

```bash
ssh -T git@github.com
```

### Case 3: PAT saved for one user, scheduler uses another

Cause: credential helper storage is per user profile.

Fix:

1. Configure git credential helper under scheduler user account.
1. Run once:

```bash
git pull
```

1. Enter credentials and save them for that user account.

### Case 4: Windows task runs as `SYSTEM` or service account

Cause: that account has no git credentials and no SSH keys.

Fix:

1. Open Task Scheduler -> task -> Properties -> General.
1. Set `When running the task, use the following user account` to your normal user.
1. Check `Run whether user is logged on or not` if needed.
1. Save task and run it once manually from Task Scheduler.

## Next steps

- [Documentation index](../index.md)

## Implementation status (2026-03-25)

This document is aligned to the current production implementation baseline.

Current baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` flows.
1. REST and non-REST protocols are supported in one automation model: REST, GraphQL, gRPC, AsyncAPI, and WebSocket.
1. Non-REST automation includes server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated into the smooth autopipeline, including Postman-supported auto-prepare mode.
1. Contract test assets are generated automatically and merged with smart-merge rules so manual/customized cases are preserved.
1. Knowledge/RAG tasks run as part of automation when enabled (module extraction, validation, retrieval index, graph, evals).
1. Plan gating is enforced by configuration and policy packs; advanced non-REST automation is reserved for higher plans.

Canonical execution order reference:

- `docs/operations/CANONICAL_FLOW.md`
- `docs/operations/UNIFIED_CLIENT_CONFIG.md`
- `README.md`

Commercial note:

- Where commercial packaging is discussed, recurring service terms (retainer/licensing) are part of the active go-to-market model.

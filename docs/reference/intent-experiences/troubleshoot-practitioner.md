---
title: "Intent experience: troubleshoot for practitioner"
description: "Assembled guidance for one intent and audience using reusable knowledge modules with verified metadata and channel-ready sections."
content_type: reference
product: both
tags:
  - Reference
  - AI
---

<!-- markdownlint-disable MD001 MD007 MD024 MD025 MD031 -->

# Intent experience: troubleshoot for practitioner

This page is assembled for the `troubleshoot` intent and the `practitioner` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent troubleshoot --audience practitioner --channel docs
```

## Included modules

### Assemble intent experiences (Part 2)

Build user-intent documentation and channel bundles from reusable knowledge modules with validation, indexing, and consistent outputs.

#### Assemble intent experiences (Part 2): Step 3: Generate assistant and automation bundles

Run these commands for runtime channels:

```bash

npm run build:intent -- --intent configure --audience operator --channel assistant
npm run build:intent -- --intent configure --audience operator --channel automation

```

These outputs are JSON bundles in `reports/intent-bundles/`.

#### Assemble intent experiences (Part 2): Step 4: Rebuild retrieval index

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

#### Assemble intent experiences (Part 2): Common issues

##### Assemble intent experiences (Part 2): No modules matched

Cause: intent, audience, or channel does not match module metadata.

Fix:

1. Confirm your module has `status: active`.
1. Confirm the target intent is listed under `intents`.
1. Confirm the target audience or `all` is listed under `audiences`.

##### Assemble intent experiences (Part 2): Dependency validation fails

Cause: a module references a missing dependency.

Fix:

1. Add the referenced module file.
1. Correct the `dependencies` value to an existing module `id`.

#### Assemble intent experiences (Part 2): Performance and quality notes

- Keep modules focused; 150-400 words per `docs_markdown` block works well.
- Keep assistant context under 300 words for faster retrieval.
- Re-run `npm run validate:knowledge` in CI for every module change.

### Configure Ask AI module (Part 4)

Enable or disable Ask AI, set provider and billing mode, and verify configuration in five steps for beginner operators.

#### Configure Ask AI module (Part 4): Step 6: Validate and commit

Run:

```bash

npm run lint
npm run askai:status

```

Confirm:

- `enabled` matches client request
- `billing_mode` matches contract
- `provider` and `model` match the planned setup
- `knowledge_index_path`, `knowledge_graph_path`, and `retrieval_eval_report_path` point to current RAG artifacts
- `faiss_index_path` and `faiss_metadata_path` point to FAISS embedding assets
- advanced retrieval features (hybrid search, HyDE, reranking, embedding cache) are enabled
- weekly pipeline refresh keeps RAG artifacts up to date before assistant runs

#### Configure Ask AI module (Part 4): Troubleshooting

##### Configure Ask AI module (Part 4): Error: unsupported provider or billing mode

Cause: the value is outside allowed options.

Fix:

```bash

npm run askai:configure -- --help

```

Use only:

- Provider: `openai`, `anthropic`, `azure-openai`, `custom`
- Billing: `disabled`, `bring-your-own-key`, `user-subscription`

##### Configure Ask AI module (Part 4): Configuration changed but team does not see it

Cause: local branch mismatch or uncommitted config.

Fix:

```bash

git status
git add config/ask-ai.yml reports/ask-ai-config.json
git commit -m "docs-ops: update Ask AI configuration"

```

#### Configure Ask AI module (Part 4): Next steps

- [Quick start](../getting-started/quickstart.md)
- [Assemble intent experiences](../../how-to/assemble-intent-experiences.md)
- [Intelligent knowledge system architecture](../concepts/intelligent-knowledge-system.md)

### Migrate documentation from Confluence (Part 5)

Import Confluence pages into the documentation pipeline with automatic quality enhancement, SEO optimization, and knowledge extraction.

#### Migrate documentation from Confluence (Part 5): What happens after import

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

### Migrate documentation from Confluence (Part 6)

Import Confluence pages into the documentation pipeline with automatic quality enhancement, SEO optimization, and knowledge extraction.

#### Migrate documentation from Confluence (Part 6): Enable LLM-powered quality enhancement

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

### Migrate documentation from Confluence (Part 7)

Import Confluence pages into the documentation pipeline with automatic quality enhancement, SEO optimization, and knowledge extraction.

#### Migrate documentation from Confluence (Part 7): Review migration reports

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

#### Migrate documentation from Confluence (Part 7): Troubleshoot common issues

##### Migrate documentation from Confluence (Part 7): Authentication fails with 401 error

**Cause:** Invalid or expired API token.

**Fix:** Generate a new token following the steps in
[Create an API token](#step-1-create-an-api-token). For Cloud, verify you use
your email address with `--confluence-username`, not your display name.

##### Migrate documentation from Confluence (Part 7): Rate limiting (429 responses)

**Cause:** Confluence rate limits API requests.

**Fix:** The pipeline automatically retries with exponential backoff (3
retries). For large spaces with more than 1,000 pages, the pipeline
paginates requests automatically. If rate limiting persists, wait 60 seconds
and retry.

### Migrate documentation from Confluence (Part 8)

Import Confluence pages into the documentation pipeline with automatic quality enhancement, SEO optimization, and knowledge extraction.

##### Migrate documentation from Confluence (Part 8): Large spaces cause memory issues

**Cause:** Spaces with more than 5,000 pages consume significant memory
during conversion.

**Fix:** Import specific spaces one at a time instead of combining multiple
large spaces in a single `--space-keys` value.

##### Migrate documentation from Confluence (Part 8): ZIP export missing entities.xml

**Cause:** The ZIP file does not contain the expected `entities.xml` file.

**Fix:** Re-export from Confluence using **XML** format, not HTML-only
export. The XML export includes `entities.xml` which contains page content
and metadata.

##### Migrate documentation from Confluence (Part 8): Encoding errors in imported content

**Cause:** Confluence pages contain special characters that were not properly
encoded during export.

**Fix:** The pipeline uses UTF-8 encoding by default. If you see encoding
artifacts, re-export from Confluence and verify the export completed without
warnings.

#### Migrate documentation from Confluence (Part 8): Next steps

After migration completes:

- Review the migration report in `reports/confluence_migration_report.md`
- Check imported files in the output directory for content accuracy
- Run `python3 scripts/seo_geo_optimizer.py docs/imported/` to verify
  SEO/GEO scores
- Add imported documents to the `mkdocs.yml` navigation
- Run `python3 scripts/validate_frontmatter.py --paths docs/imported/` to
  confirm frontmatter compliance

### Operator Runbook (Retainer Operations) (Part 11)

Step-by-step instructions for weekly report review, client questions, new repo setup, and profile tuning.

| Question | What to enter | Notes |
| --- | --- | --- |
| Profile source | "generate from preset" or path to existing `.client.yml` | Choose "generate" for new clients |
| Preset | `small` / `startup` / `enterprise` / `pilot-evidence` | Match the client plan tier |
| Company name | Client company name | Used in reports and PDF |
| Client ID | Lowercase slug (auto-suggested from company name) | Used in filenames and license |
| Contact email | Client docs owner email | Informational |
| License plan | `pilot` / `professional` / `enterprise` | Must match the sales agreement |
| License validity | Number of days (default: 365) | Typically 365 for annual contracts |
| Client repo path | Full path to the client repository | Must exist on disk |
| Docs path | Path to docs folder in client repo (default: `docs`) | |
| API path | Path to API specs (default: `api`) | |
| SDK path | Path to SDK code (default: `sdk`) | |
| Docs flow mode | `code-first` / `api-first` / `hybrid` | `code-first` if code exists, `api-first` if designing API from scratch |
| Vale style guide | `google` / `microsoft` / `hybrid` | Google is the default |
| Output targets | `mkdocs`, `readme`, `github`, etc. | Comma-separated |
| PR auto-fix | Yes/No (default: No) | Enable if client wants automatic PR doc updates |
| API sandbox backend | `docker` / `prism` / `external` | Only asked for api-first/hybrid mode |
| Test asset upload | Yes/No | TestRail/Zephyr upload |
| Algolia integration | Yes/No | Search index |
| Ask AI integration | Yes/No | AI assistant |
| Intent weekly build | Yes/No | Intent experience pages |
| Finalize gate confirmation | Yes/No | Interactive commit confirmation |
| Advanced module toggles | Yes/No per module | If enabled, configures each module individually |
| Scheduler | `none` / `linux` / `windows` | Install weekly cron/task |

### Operator Runbook (Retainer Operations) (Part 13)

Step-by-step instructions for weekly report review, client questions, new repo setup, and profile tuning.

##### Operator Runbook (Retainer Operations) (Part 13): Step 3.4: Post-setup verification checklist

After provisioning, verify these files exist in the client repo:

- [ ] `docsops/config/client_runtime.yml` -- runtime configuration
- [ ] `docsops/policy_packs/selected.yml` -- active policy pack
- [ ] `docsops/ENV_CHECKLIST.md` -- secrets checklist
- [ ] `docsops/license.jwt` -- license token (or placeholder)
- [ ] `docsops/ops/run_weekly_docsops.sh` (Linux) or `docsops/ops/run_weekly_docsops.ps1` (Windows) -- weekly script
- [ ] `docsops/CLAUDE.md` and/or `docsops/AGENTS.md` -- LLM instructions

##### Operator Runbook (Retainer Operations) (Part 13): Step 3.5: Coordinate secrets with client

Open `<client-repo>/docsops/ENV_CHECKLIST.md`. It lists all required environment variables for the enabled features. Send this to the client and ask them to provide values for:

| If this is enabled | Client must provide |
| --- | --- |
| External mock server (Postman) | `POSTMAN_API_KEY`, `POSTMAN_WORKSPACE_ID` |
| TestRail upload | `TESTRAIL_BASE_URL`, `TESTRAIL_EMAIL`, `TESTRAIL_API_KEY`, `TESTRAIL_SECTION_ID` |
| Zephyr upload | `ZEPHYR_SCALE_API_TOKEN`, `ZEPHYR_SCALE_PROJECT_KEY` |
| Algolia search | `ALGOLIA_APP_ID`, `ALGOLIA_API_KEY`, `ALGOLIA_INDEX_NAME` |
| PR auto-fix (org repos) | `DOCSOPS_BOT_TOKEN` (GitHub PAT) |

Secrets go into `<client-repo>/.env.docsops.local` (which is gitignored).

### Operator Runbook (Retainer Operations) (Part 14)

Step-by-step instructions for weekly report review, client questions, new repo setup, and profile tuning.

##### Operator Runbook (Retainer Operations) (Part 14): Step 3.6: Run a smoke test

Run one manual weekly cycle to verify everything works:

```bash

cd /path/to/client-repo
python3 docsops/scripts/run_weekly_gap_batch.py \
  --docsops-root docsops \
  --reports-dir reports

```

Verify:

- [ ] Script completes without errors (warnings are OK).
- [ ] `reports/consolidated_report.json` was created with a fresh timestamp.
- [ ] `reports/docsops_status.json` exists.

If the smoke test passes, the scheduler takes over and runs this automatically every Monday.

### Operator Runbook (Retainer Operations) (Part 16)

Step-by-step instructions for weekly report review, client questions, new repo setup, and profile tuning.

##### Operator Runbook (Retainer Operations) (Part 16): What the wizard configures vs what you edit manually

The interactive wizard (`python3 scripts/provision_client_repo.py --interactive --generate-profile`) configures all of these settings during initial setup:

- Preset selection (sets the baseline strictness)
- Policy pack (`minimal`, `api-first`, `monorepo`, `multi-product`, `plg`)
- Style guide (`google`, `microsoft`, `hybrid`)
- Protocol-specific thresholds (per-protocol autofix cycles, semantic checks)
- Module toggles (17 feature switches)
- SLA thresholds (via `policy_overrides`)
- All integration settings

For changes after initial setup, you have two options:

###### Operator Runbook (Retainer Operations) (Part 16): Option A: Re-run the wizard

```bash

python3 scripts/provision_client_repo.py --interactive --generate-profile

```

This regenerates the profile from scratch. Choose the new preset and adjust settings.

###### Operator Runbook (Retainer Operations) (Part 16): Option B: Edit the profile manually

Edit `profiles/clients/<client-id>.client.yml` directly.

### Operator Runbook (Retainer Operations) (Part 17)

Step-by-step instructions for weekly report review, client questions, new repo setup, and profile tuning.

##### Operator Runbook (Retainer Operations) (Part 17): Common adjustments

###### Operator Runbook (Retainer Operations) (Part 17): Change strictness level

```yaml

# Lenient (warnings only, no blocking)
bundle:
  base_policy_pack: "minimal"

# Medium (blocks on critical issues)
bundle:
  base_policy_pack: "api-first"

# Strict (blocks on all quality issues)
bundle:
  base_policy_pack: "multi-product"
  policy_overrides:
    kpi_sla:
      min_doc_coverage: 90
      max_stale_pct: 10
      max_quality_score_drop: 2

```

###### Operator Runbook (Retainer Operations) (Part 17): Change protocol-specific thresholds

```yaml

runtime:
  api_protocol_settings:
    graphql:
      autofix_cycle_enabled: true
      autofix_max_attempts: 3       # Reduce to 1 for faster runs
      semantic_autofix_max_attempts: 3
    grpc:
      autofix_cycle_enabled: true
      autofix_max_attempts: 3

```

###### Operator Runbook (Retainer Operations) (Part 17): Change stale document threshold

```yaml

private_tuning:
  stale_days: 21          # Days before a doc is considered stale in reports
  weekly_stale_days: 90   # Days before stale doc appears in weekly consolidated report

```

###### Operator Runbook (Retainer Operations) (Part 17): Add protocols (Enterprise only)

```yaml

runtime:
  api_protocols: ["rest", "graphql", "grpc"]
  api_protocol_settings:
    graphql:
      enabled: true
      schema_path: "api/schema.graphql"
    grpc:
      enabled: true
      proto_paths: ["api/proto"]

```

### Operator Runbook (Retainer Operations) (Part 19)

Step-by-step instructions for weekly report review, client questions, new repo setup, and profile tuning.

##### Operator Runbook (Retainer Operations) (Part 19): How licensing works

Every pipeline run validates the license locally using an Ed25519-signed JWT token. No client data is ever sent to any server.

Plan tiers control which features are available:

| Feature group | Pilot | Professional | Enterprise |
| --- | --- | --- | --- |
| Core quality (lint, frontmatter, SEO report) | Yes | Yes | Yes |
| Gap detection (code-only) | Yes | Yes | Yes |
| Glossary sync | Yes | Yes | Yes |
| REST protocol | Yes | Yes | Yes |
| SEO/GEO scoring + auto-fix | No | Yes | Yes |
| API-first flow | No | Yes | Yes |
| Drift detection | No | Yes | Yes |
| KPI/SLA reports | No | Yes | Yes |
| Test assets generation | No | Yes | Yes |
| Consolidated reports | No | Yes | Yes |
| All 5 protocols | No | No | Yes |
| Knowledge modules + RAG | No | No | Yes |
| Knowledge graph | No | No | Yes |
| FAISS retrieval | No | No | Yes |
| Executive audit PDF | No | No | Yes |
| i18n system | No | No | Yes |
| Custom policy packs | No | No | Yes |
| TestRail/Zephyr upload | No | No | Yes |

### Operator Runbook (Retainer Operations) (Part 20)

Step-by-step instructions for weekly report review, client questions, new repo setup, and profile tuning.

##### Operator Runbook (Retainer Operations) (Part 20): What happens without a license

The pipeline runs in **community mode** (degraded):

- Markdown lint works (no quality scoring)
- Frontmatter validation works (no quality scoring)
- SEO/GEO report only (no auto-fix, no scoring)
- Gap detection code-only (no community/search sources)
- REST protocol only
- No PDF reports, no KPI wall, no drift detection
- Quality gates warn-only (never block)

##### Operator Runbook (Retainer Operations) (Part 20): License file location

License JWT is stored at `<client-repo>/docsops/license.jwt`. The public key for verification is at `<client-repo>/docsops/keys/veriops-licensing.pub`.

##### Operator Runbook (Retainer Operations) (Part 20): Dev/test bypass

For local development and testing, set the environment variable:

```bash

export VERIOPS_LICENSE_PLAN=enterprise

```

This bypasses JWT validation entirely.

---

#### Operator Runbook (Retainer Operations) (Part 20): Troubleshooting

### Operator Runbook (Retainer Operations) (Part 21)

Step-by-step instructions for weekly report review, client questions, new repo setup, and profile tuning.

##### Operator Runbook (Retainer Operations) (Part 21): Scheduler did not run

1. Check if the cron job (Linux) or Windows Task (Windows) exists:

Linux:

```bash

crontab -l | grep docsops

```

Windows:

```bash

schtasks /query /tn "VeriOps Weekly"

```

1. If missing, re-install:

Linux:

```bash

bash <client-repo>/docsops/ops/install_cron_weekly.sh

```

Windows:

```bash

powershell -ExecutionPolicy Bypass -File <client-repo>/docsops/ops/install_windows_task.ps1

```

1. Check git access: the scheduler runs under the user account that installed it. That account must have `git pull` access to the repo (SSH key or credential helper).

1. Check logs: `<client-repo>/reports/docsops-weekly.log`.

##### Operator Runbook (Retainer Operations) (Part 21): Pipeline fails with license error

```text

[license] BLOCKED: Feature 'drift_detection' requires a plan upgrade (current: community).

```

Cause: License file is missing, expired, or corrupted.

Fix:

1. Check `docsops/license.jwt` exists and is not empty.
1. Check expiration: `python3 docsops/scripts/license_gate.py` (prints license summary).
1. If expired, generate a new license and send it to the client.
1. For dev/test: `export VERIOPS_LICENSE_PLAN=enterprise`.

### Operator Runbook (Retainer Operations) (Part 6)

Step-by-step instructions for weekly report review, client questions, new repo setup, and profile tuning.

##### Operator Runbook (Retainer Operations) (Part 6): Step 1.5: Process action items with LLM (optional)

If the client wants documentation fixes generated automatically, use the local LLM:

1. Open terminal in the client repository.
1. Ask the local LLM (Claude Code or Codex) to process the report:

```text

Process reports/consolidated_report.json

```

The LLM reads the consolidated report and generates/updates documentation based on the prioritized action items. It follows the rules in `CLAUDE.md` or `AGENTS.md` that were installed in the client repo.

1. Review the generated changes: `git diff`.
1. If changes look good, commit and push (or create a PR for client review).

---

#### Operator Runbook (Retainer Operations) (Part 6): Task 2: Answer client question (10-15 minutes, 2-3 times per month)

**When:** Client asks about their documentation health, a specific report number, or how to adjust pipeline behavior.

### Run API-first production flow (Part 2)

Generate OpenAPI from planning notes, run full lint and self-verification, publish playground assets, and keep a sandbox ready for client testing.

#### Run API-first production flow (Part 2): Step 2: Run generation and verification

Run the universal flow command:

```bash

python3 scripts/run_api_first_flow.py \
  --project-slug taskstream \
  --notes demos/api-first/taskstream-planning-notes.md \
  --spec api/openapi.yaml \
  --spec-tree api/taskstream \
  --openapi-version 3.1.0 \
  --manual-overrides api/overrides/openapi.manual.yml \
  --regression-snapshot api/.openapi-regression.json \
  --docs-provider mkdocs \
  --verify-user-path \
  --mock-base-url https://<your-real-public-mock-url>/v1 \
  --generate-test-assets \
  --upload-test-assets \
  --auto-remediate \
  --max-attempts 3

```

The runner performs:

1. OpenAPI generation from notes.
1. Contract validation.
1. Spectral, Redocly, and Swagger CLI lint checks.
1. FastAPI stub generation.
1. Self-verification of operation coverage and user-path calls.
1. Finalize gate (`scripts/finalize_docs_gate.py`): iterative `lint -> fix -> lint` before completion.

For interactive confirmation before commit, add:

```bash

--ask-commit-confirmation

```

If you maintain multiple API versions, run one flow per version and publish to separate docs asset paths.
Example layout:

```text

api/v1/openapi.yaml -> docs/assets/api/v1/
api/v2/openapi.yaml -> docs/assets/api/v2/

```

Use overrides and regression snapshot as follows:

### Run API-first production flow (Part 5)

Generate OpenAPI from planning notes, run full lint and self-verification, publish playground assets, and keep a sandbox ready for client testing.

##### Run API-first production flow (Part 5): Add a manual business-logic case

Open `reports/api-test-assets/api_test_cases.json` and append a case to the `cases` array:

```json

{
  "id": "TC-manual-order-capacity-1",
  "title": "Order queue rejects when warehouse is at capacity",
  "suite": "Business Logic",
  "operation_id": "manual",
  "traceability": {"method": "POST", "path": "/orders", "operation_id": "manual"},
  "preconditions": ["Warehouse capacity is set to 500.", "Current queue has 500 items."],
  "steps": [
    "Send POST /orders with a new order payload.",
    "Verify the response returns 409 Conflict.",
    "Verify the error body includes a capacity_exceeded code."
  ],
  "expected_result": "Order is rejected with a capacity exceeded error.",
  "priority": "high",
  "type": "functional",
  "origin": "manual",
  "customized": false,
  "needs_review": false,
  "review_reason": null,
  "spec_hash": ""
}

```

Set `origin` to `manual` and leave `spec_hash` empty. The merge engine never overwrites or drops manual cases.

### Set up a real-time webhook processing pipeline (Part 14)

Configure end-to-end webhook ingestion with HMAC verification, async queue processing, and delivery guarantees in under 15 minutes.

#### Set up a real-time webhook processing pipeline (Part 14): Explore the webhook pipeline architecture

The production webhook pipeline spans 13 components across 5 layers:

- **Clients layer:** Mobile App (2.1M users), Web Dashboard (450K DAU), and Partner API (85 integrations) generate webhook events via REST and WebSocket connections.
- **Edge layer:** CloudFlare CDN (99.99% uptime, TLS 1.3, DDoS protection) terminates connections. The Rate Limiter enforces 60 req/min per API key using a Redis-backed token bucket algorithm.
- **Verification layer:** The API Gateway routes 12K req/sec to the HMAC Validator, which completes HMAC-SHA256 signature checks in under 2 ms with timing-safe comparison and replay protection.
- **Processing layer:** The Event Router classifies payloads into 8 event types and dispatches them to the Redis-backed BullMQ Queue (at-least-once delivery, 10 concurrent workers). The Retry Engine handles exponential backoff (1 s, 2 s, 4 s, 8 s, 16 s) across 5 attempts.
- **Storage layer:** PostgreSQL handles 2 replicas, 8.5K qps with PgBouncer connection pooling and persists results. The Event Log provides 30-day retention with full-text search. Grafana Monitoring delivers real-time alerts via PagerDuty and Prometheus when error rates exceed 1%.
  PostgreSQL baseline metric: 2 replicas, 8.5K qps.

### Set up a real-time webhook processing pipeline (Part 8)

Configure end-to-end webhook ingestion with HMAC verification, async queue processing, and delivery guarantees in under 15 minutes.

// Route to appropriate handler
  switch (event.type) {
    case 'order.completed':
      await handleOrderCompleted(event);
      break;
    case 'payment.failed':
      await handlePaymentFailed(event);
      break;
    default:
      console.log(`Unhandled event type: ${event.type}`);
  }
}, {
  connection,
  concurrency: 10,  // Process 10 events in parallel
});

worker.on('completed', (job) => {
  console.log(`Job ${job.id} completed`);
});

worker.on('failed', (job, err) => {
  console.error(`Job ${job.id} failed: ${err.message}`);
});

```

## Webhook configuration parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `webhook_secret` | string | Required | HMAC-SHA256 signing secret (minimum 32 characters) |
| `max_payload_size` | integer | {{ max_payload_size_mb }} MB | Maximum accepted webhook body size |
| `signature_tolerance` | integer | 300 | Maximum age in seconds for replay protection (default: 5 minutes) |
| `retry_attempts` | integer | 5 | Number of delivery retry attempts before marking as failed |
| `retry_backoff` | string | exponential | Backoff strategy: `exponential`, `linear`, or `fixed` |
| `queue_concurrency` | integer | 10 | Number of events processed in parallel from the queue |
| `event_retention_days` | integer | 30 | Number of days to retain processed event logs |

## Next steps

- Validate modules: `npm run lint:knowledge`
- Rebuild retrieval index: `npm run build:knowledge-index`
- Generate assistant pack: `npm run build:intent -- --channel assistant`

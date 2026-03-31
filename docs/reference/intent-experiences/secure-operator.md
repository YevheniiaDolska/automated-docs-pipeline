---
title: "Intent experience: secure for operator"
description: "Assembled guidance for one intent and audience using reusable knowledge modules with verified metadata and channel-ready sections."
content_type: reference
product: both
tags:
  - Reference
  - AI
---

<!-- markdownlint-disable MD001 MD007 MD024 MD025 MD031 -->

# Intent experience: secure for operator

This page is assembled for the `secure` intent and the `operator` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent secure --audience operator --channel docs
```

## Included modules

### API playground (Part 3)

Interactive API reference with Swagger UI or Redoc and configurable sandbox behavior for product-led growth.

#### API playground (Part 3): Security guidance

1. `sandbox-only`: safest default for regulated or high-risk domains.
1. `real-api`: use only when product policy allows direct user requests.
1. `mixed`: let user choose sandbox vs real API explicitly.
1. Keep write operations protected by auth scopes and rate limits.

#### API playground (Part 3): Next steps

- [Documentation index](index.md)

### Auto-Doc Pipeline study guide (Part 5)

Learn the Auto-Doc Pipeline quickly with a simple architecture map, operating flow, plan mapping, and a detailed client FAQ.

##### Auto-Doc Pipeline study guide (Part 5): Step 2: prepare profile and bundle

1. Generate or update client profile in `profiles/clients/generated/`.
1. Build the client bundle in `generated/client_bundles/<client_id>/`.
1. Verify bundle contains needed scripts and config for selected plan/modules.

##### Auto-Doc Pipeline study guide (Part 5): Step 3: install in client repo

1. Copy bundle as `docsops/` into the client repository.
1. Create `/.env.docsops.local` from generated template.
1. Fill required secrets and integration keys (if used).
1. Confirm git auth works for the scheduler user (`git pull` must succeed).

##### Auto-Doc Pipeline study guide (Part 5): Step 4: configure runtime for this client

1. Set `runtime.docs_flow.mode` (`code-first`, `api-first`, `hybrid`).
1. Enable/disable modules per purchased plan.
1. For non-REST, configure protocol blocks in runtime config.
1. For external mock mode, set `mock_base_url` and enable `external_mock` when needed.
1. For Postman auto-prepare, add required Postman env vars and workspace settings.

##### Auto-Doc Pipeline study guide (Part 5): Step 5: run first verification cycle

1. Run weekly flow once manually:
   `python3 docsops/scripts/run_weekly_gap_batch.py`.
1. Confirm `reports/consolidated_report.json` is generated and fresh.
1. Check multi-protocol and test-asset reports if enabled.
1. Confirm no blocking gate failures before turning on scheduler.

### Auto-Doc Pipeline study guide (Part 8)

Learn the Auto-Doc Pipeline quickly with a simple architecture map, operating flow, plan mapping, and a detailed client FAQ.

##### Auto-Doc Pipeline study guide (Part 8): 13) How long does rollout usually take?

Pilot setup is typically quick because runtime and bundle templates are pre-structured.

##### Auto-Doc Pipeline study guide (Part 8): 14) How much manual work remains after rollout?

Usually review and approval work remains, not repetitive authoring and cross-file synchronization.

##### Auto-Doc Pipeline study guide (Part 8): 15) Can we run this inside existing CI/CD?

Yes. The flow is script-driven and supports local scheduler plus CI automation patterns.

##### Auto-Doc Pipeline study guide (Part 8): 16) What data should clients prepare?

Repo access, docs root, runtime config decisions, plan scope, and optional external integrations.

##### Auto-Doc Pipeline study guide (Part 8): 17) How is this different from a static docs generator?

It is a controlled operations pipeline, not only a renderer. It validates, remediates, merges, and governs.

##### Auto-Doc Pipeline study guide (Part 8): 18) What happens when a gate fails?

The pipeline emits explicit failure reports and can run remediation cycles before publish.

##### Auto-Doc Pipeline study guide (Part 8): 19) Can teams adopt this gradually?

Yes. Teams can start with quality gates and docs lifecycle, then enable protocol and RAG modules.

##### Auto-Doc Pipeline study guide (Part 8): 20) Why is this compelling commercially?

It compresses repetitive documentation and API verification work into a governed flow with measurable outputs.

#### Auto-Doc Pipeline study guide (Part 8): Next steps

- [Documentation index](index.md)

### Intelligent knowledge system architecture

Explains how the pipeline models reusable knowledge modules for AI retrieval, dynamic assembly, and multi-channel documentation delivery.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### Intelligent knowledge system architecture: Intelligent knowledge system architecture

The intelligent knowledge system is a structured layer that stores reusable modules, metadata, and intent mappings so humans and AI can retrieve the same trusted product knowledge.

The pipeline keeps authored modules in `knowledge_modules/*.yml`, validates them, and assembles clean output documents and channel bundles. This preserves normal documentation readability while enabling AI-native retrieval and reuse.

#### Intelligent knowledge system architecture: Core components

1. `Knowledge modules`: atomic YAML units with intent, audience, channel, dependency, and owner metadata.
1. `Intent assembler`: creates audience-specific docs pages and channel bundles from active modules.
1. `Retrieval index`: exports module-level records to `docs/assets/knowledge-retrieval-index.json`.
1. `JSON-LD graph`: exports module relationships to `docs/assets/knowledge-graph.jsonld`.
1. `Retrieval evals`: calculates Precision/Recall/Hallucination-rate in `reports/retrieval_evals_report.json`.
1. `Quality gates`: checks schema, dependency integrity, cycle safety, and content completeness.

### Intelligent knowledge system architecture (Part 2)

Explains how the pipeline models reusable knowledge modules for AI retrieval, dynamic assembly, and multi-channel documentation delivery.

#### Intelligent knowledge system architecture (Part 2): Why this improves documentation quality

Traditional pages duplicate content across docs, in-product guidance, and assistant prompts. Modules let you author once and distribute consistently.

- You reduce contradictory guidance because one module powers multiple channels.
- You improve AI response quality because retrieval uses intent and audience metadata.
- You cut update time because a verified module updates all downstream experiences.

#### Intelligent knowledge system architecture (Part 2): Data model

Each module defines:

- `id`, `title`, `summary`, and `owner`
- `intents`, such as `configure`, `secure`, or `troubleshoot`
- `audiences`, such as `operator` or `support`
- `channels`, such as `docs`, `assistant`, or `automation`
- `dependencies` for module composition order
- `content` blocks for each channel output

#### Intelligent knowledge system architecture (Part 2): Operational lifecycle

The knowledge lifecycle has six phases:

1. Schema and integrity validation (`npm run lint:knowledge`).
1. Intent assembly for channel outputs (`npm run build:intent`).
1. Retrieval index generation (`npm run build:knowledge-index`).
1. Graph generation for relationship context (`npm run build:knowledge-graph`).
1. Retrieval quality evaluation (`npm run eval:retrieval`).
1. Release gate consolidation (`npm run validate:knowledge`).

### Network transparency reference (Part 3)

Complete list of all outgoing network requests the pipeline makes, with exact payload schemas. No client data leaves your network.

##### Network transparency reference (Part 3): Request 2: Capability pack refresh

**When:** During weekly batch run, or when the current pack approaches expiration.

**Endpoint:** `POST /v1/pack/refresh`

**Frequency:** Weekly (configurable per plan).

```json

{
  "authorization": "Bearer <license-jwt>"
}

```

The JWT contains only license metadata (client ID, plan tier, expiration). The JWT payload schema:

```json

{
  "sub": "acme-corp",
  "plan": "enterprise",
  "iat": 1750000000,
  "exp": 1781536000
}

```

**What is NOT sent:** No document content, no file listings, no quality scores, no report data.

##### Network transparency reference (Part 3): Request 3: Update check

**When:** During weekly batch run, or manual `python3 scripts/check_updates.py`.

**Endpoint:** `GET /v1/check`

**Frequency:** Weekly (automatic), or on-demand.

```text

GET /v1/check?version=1.2.0&platform=linux-x86_64
User-Agent: VeriOps-Pipeline-Updater/1.0

```

**Query parameters:**

| Parameter | Type | Description | Contains client data? |
| --- | --- | --- | --- |
| `version` | string | Current installed pipeline version | No |
| `platform` | string | OS and architecture identifier | No |

**What is NOT sent:** No license info, no document counts, no quality metrics, no file paths.

### Network transparency reference (Part 4)

Complete list of all outgoing network requests the pipeline makes, with exact payload schemas. No client data leaves your network.

##### Network transparency reference (Part 4): Request 4: Update download

**When:** After an update check finds a new version and the user approves.

**Endpoint:** `GET /v1/download/{version}/{platform}`

**Frequency:** When updates are available (monthly for Professional, weekly opt-in for Enterprise).

```text

GET /v1/download/1.3.0/linux-x86_64

```

**What is NOT sent:** No request body. No authentication headers. No client data of any kind.

##### Network transparency reference (Part 4): Request 5: License deactivation

**When:** When a client explicitly deactivates their license (seat release).

**Endpoint:** `POST /v1/deactivate`

**Frequency:** Once per deactivation.

```json

{
  "authorization": "Bearer <license-jwt>"
}

```

**What is NOT sent:** No reason codes, no usage data, no document counts.

### Pipeline Capabilities Catalog (Part 10)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

#### Pipeline Capabilities Catalog (Part 10): Test assets generation and smart merge

`generate_protocol_test_assets.py` generates protocol-aware test cases for all five protocols with signature-based smart merge to preserve custom and manual test cases across contract changes.

**Test categories per protocol:**

| Protocol | Categories |
| --- | --- |
| REST | CRUD happy paths, validation errors, auth, rate limiting, pagination |
| GraphQL | Query/mutation/subscription happy path, invalid input, auth, injection, latency |
| gRPC | Unary/streaming positive, status codes, deadline/retry, authorization, latency SLO |
| AsyncAPI | Publish validation, invalid payload, ordering/idempotency, security, throughput |
| WebSocket | Connection/auth, message envelope, reconnect, security, concurrency |

**Output formats:** `api_test_cases.json`, `testrail_test_cases.csv` (TestRail), `zephyr_test_cases.json` (Zephyr Scale), `test_matrix.json`, `fuzz_scenarios.json`.

**Smart merge rules:** auto-generated cases are replaced on contract change; customized cases (`customized: true`) are preserved and flagged `needs_review: true` when the contract signature changes; manual cases (`origin: "manual"`) are never overwritten.

**TestRail/Zephyr upload:** `upload_api_test_assets.py` pushes generated cases to TestRail or Zephyr Scale. The `needs_review` flag propagates to both platforms so QA teams can triage stale custom cases.

### Pipeline Capabilities Catalog (Part 15)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

#### Pipeline Capabilities Catalog (Part 15): Templates

These can be shipped via `bundle.include_paths` and used by LLM generation flow.

- `templates/admin-guide.md`
- `templates/api-endpoint.md`
- `templates/api-reference.md`
- `templates/architecture-overview.md`
- `templates/authentication-guide.md`
- `templates/best-practices.md`
- `templates/changelog.md`
- `templates/concept.md`
- `templates/configuration-guide.md`
- `templates/configuration-reference.md`
- `templates/deployment-guide.md`
- `templates/error-handling-guide.md`
- `templates/faq.md`
- `templates/glossary-page.md`
- `templates/how-to.md`
- `templates/integration-guide.md`
- `templates/interactive-diagram.html`
- `templates/migration-guide.md`
- `templates/plg-persona-guide.md`
- `templates/plg-value-page.md`
- `templates/quickstart.md`
- `templates/reference.md`
- `templates/release-note.md`
- `templates/sdk-reference.md`
- `templates/security-guide.md`
- `templates/testing-guide.md`
- `templates/troubleshooting.md`
- `templates/tutorial.md`
- `templates/upgrade-guide.md`
- `templates/use-case.md`
- `templates/user-guide.md`
- `templates/webhooks-guide.md`

#### Pipeline Capabilities Catalog (Part 15): Policy Packs

- `api-first.yml`
- `minimal.yml`
- `monorepo.yml`
- `multi-product.yml`
- `plg.yml`

#### Pipeline Capabilities Catalog (Part 15): Knowledge Modules

Can be copied into client bundle with `bundle.include_paths: ['knowledge_modules']`.

- `webhook-auth-baseline.yml`
- `webhook-retry-policy.yml`

### SEO/GEO Optimization Guide (Part 5)

Comprehensive guide to SEO and GEO optimization in the documentation pipeline

##### SEO/GEO Optimization Guide (Part 5): Weekly Reports

The system generates:

- GEO compliance scores
- SEO metadata coverage
- Search query gaps (from Algolia)
- Stale content alerts
- Deprecated content tracking

##### SEO/GEO Optimization Guide (Part 5): Metrics Tracked

- First paragraph word count
- Heading descriptiveness score
- Fact density ratio
- Metadata completeness
- Search click-through rate

#### SEO/GEO Optimization Guide (Part 5): Best Practices

##### SEO/GEO Optimization Guide (Part 5): For Maximum LLM Visibility

\11. **Start with a definition**: "The Webhook node is a trigger for inbound HTTP events."
\11. **Use specific headings**: "Configure OAuth 2.0" not "Configuration"
\11. **Include concrete facts**: Ports, defaults, limits
\11. **Provide code examples**: Even small snippets help

##### SEO/GEO Optimization Guide (Part 5): For Search Optimization

\11. **Complete all metadata**: Helps with faceted search
\11. **Use descriptive titles**: Include key terms users search
\11. **Write clear descriptions**: 50-160 chars, action-oriented
\11. **Tag appropriately**: Maximum 8 relevant tags

##### SEO/GEO Optimization Guide (Part 5): For Content Lifecycle

\11. **Mark maturity state**: Helps users understand stability
\11. **Set replacement paths**: For deprecated content
\11. **Update regularly**: Keep last_reviewed current
\11. **Archive properly**: Use removed state, not delete

#### SEO/GEO Optimization Guide (Part 5): Troubleshooting

### SEO/GEO Optimization Guide (Part 6)

Comprehensive guide to SEO and GEO optimization in the documentation pipeline

##### SEO/GEO Optimization Guide (Part 6): Common Issues

**Issue**: "Description too short" error
**Fix**: Expand to 50+ characters with key terms

**Issue**: "Generic heading" warning
**Fix**: Make heading specific: "Configure webhook authentication"

**Issue**: "Low fact density"
**Fix**: Add numbers, code, configuration values

**Issue**: "No definition pattern"
**Fix**: Start with "X is/enables/provides" and include a concrete first-sentence definition.

##### SEO/GEO Optimization Guide (Part 6): Debug Mode

```bash

# Verbose output
python scripts/seo_geo_optimizer.py docs/ --output debug.json

# Dry run (no changes)
python scripts/seo_geo_optimizer.py docs/ --dry-run

```

#### SEO/GEO Optimization Guide (Part 6): Integration with Other Tools

##### SEO/GEO Optimization Guide (Part 6): Algolia

Records are optimized for:

- Faceted search by product/type/component
- Smart ranking based on content quality
- Section-level search granularity

##### SEO/GEO Optimization Guide (Part 6): Google Search

Structured data enables:

- Rich snippets in search results
- Breadcrumb navigation
- FAQ accordions
- How-to steps

##### SEO/GEO Optimization Guide (Part 6): AI Assistants

GEO optimization improves:

- Answer extraction accuracy
- Citation likelihood
- Context understanding
- Factual grounding

#### SEO/GEO Optimization Guide (Part 6): Next steps

- [Documentation index](index.md)

### TaskStream API planning notes

Input planning notes used by the API-first flow to generate and validate OpenAPI contracts for TaskStream demos.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### TaskStream API planning notes: TaskStream API planning notes

This page provides the exact planning-notes input artifact used by the API-first flow before OpenAPI generation and validation.

The pipeline treats these notes as the contract source of truth and derives endpoint shapes, resource life cycle behavior, filtering rules, sorting options, authentication requirements, and expected error envelopes. This input-first model keeps API design review aligned with technical writing and implementation planning.

#### TaskStream API planning notes: Input artifact location

- `demos/api-first/taskstream-planning-notes.md`

#### TaskStream API planning notes: How the pipeline uses this input

1. Parse planning notes into endpoint and schema requirements.
1. Generate or update split OpenAPI files.
1. Run OpenAPI lint, contract validation, stub generation, and self-verification.

#### TaskStream API planning notes: Notes format (demo excerpt)

```markdown

Project: **TaskStream**
API version: **v1**
Base URL: `https://api.taskstream.example.com/v1`
Planning date: 2026-03-09
Status: Draft for OpenAPI writing

```

#### TaskStream API planning notes: Next steps

- [API playground](api-playground.md)

### Unified Client Configuration (Part 3)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

Operator-first setup path (recommended):
\11. Run `python3 scripts/onboard_client.py`.
\11. Answer wizard questions (preset + client data + repo path + scheduler).
\11. Choose finalize gate interactive confirmation mode (`runtime.finalize_gate.ask_commit_confirmation`).
\11. Review generated profile in `profiles/clients/generated/<client_id>.client.yml`.
\11. Confirm install.
\11. Verify outputs:

- `<client-repo>/docsops/config/client_runtime.yml`
- `<client-repo>/docsops/policy_packs/selected.yml`
- `<client-repo>/docsops/ENV_CHECKLIST.md`

Different laptops setup path:
\11. Build bundle on operator machine: `python3 scripts/build_client_bundle.py --client profiles/clients/<client>.client.yml`.
\11. Copy generated bundle into client repo as `docsops/`.
\11. Install scheduler on client machine:
\11. Before scheduler install, verify git auth for the same user account (`git pull` from repo root must work for that user: SSH key or credential helper/PAT).

```bash

bash docsops/ops/install_cron_weekly.sh

```

Windows:

```bash

powershell -ExecutionPolicy Bypass -File docsops/ops/install_windows_task.ps1

```

Scheduler uses local machine timezone. Monday schedule follows client local time when installed on client machine.

Plan packaging reference:

- `docs/operations/PLAN_TIERS.md` (Basic / Pro / Enterprise presets)

Scope note:

### Webhook node reference for

Complete parameter reference for the Webhook trigger node including HTTP methods, authentication, response modes, and binary data handling.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

#### Webhook node reference for: Webhook node reference

The Webhook node is a trigger node that starts a workflow when it receives an HTTP request at a unique URL. It supports GET, POST, PUT, PATCH, DELETE, and HEAD methods.

#### Webhook node reference for: Parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| **HTTP Method** | enum | `GET` | HTTP method the webhook responds to. Options: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD` |
| **Path** | string | auto-generated UUID | URL path segment. The full URL is `{base_url}/webhook/{path}` |
| **Authentication** | enum | `None` | Authentication method. Options: `None`, `Basic Auth`, `Header Auth` |
| **Respond** | enum | `When Last Node Finishes` | When to send the HTTP response. Options: `Immediately`, `When Last Node Finishes`, `Using Respond to Webhook Node` |
| **Response Code** | number | `200` | HTTP status code returned to the caller |
| **Response Data** | enum | `First Entry JSON` | What data to return. Options: `All Entries`, `First Entry JSON`, `First Entry Binary`, `No Response Body` |

### Webhook node reference for (Part 2)

Complete parameter reference for the Webhook trigger node including HTTP methods, authentication, response modes, and binary data handling.

#### Webhook node reference for (Part 2): Authentication options

| Method | Credential type | Header checked |
| --- | --- | --- |
| None | — | — |
| Basic Auth | Basic Auth | `Authorization: Basic {base64}` |
| Header Auth | Header Auth | Custom header name/value pair |

#### Webhook node reference for (Part 2): URLs

Each Webhook node generates two URLs:

- **Test URL**: Active only while the workflow editor is open and listening. Format: `{base_url}/webhook-test/{path}`
- **Production URL**: Active when the workflow is toggled to Active. Format: `{base_url}/webhook/{path}`

=== "Cloud"

 Base URL: `<https://your-instance.app.the> product.cloud`

=== "Self-hosted"

 Base URL: your configured `WEBHOOK_URL` environment variable, or `<http://localhost:5678`> by default.

#### Webhook node reference for (Part 2): Output

The Webhook node outputs a single item with the following structure:

```json

{
 "json": {
 "headers": { "content-type": "application/json", "...": "..." },
 "params": {},
 "query": { "key": "value" },
 "body": { "...": "request body..." }
 }
}

```

For binary data (file uploads), the node outputs an additional `binary` key.

#### Webhook node reference for (Part 2): Smoke-checked examples

Use these minimal examples to verify that basic snippets still run in CI.

```bash smoke

python3 -c "print('webhook smoke ok')"

```

```python smoke

payload = {"event": "ping", "status": "ok"}
assert payload["status"] == "ok"
print("webhook smoke ok")

```

### Webhook node reference for (Part 3)

Complete parameter reference for the Webhook trigger node including HTTP methods, authentication, response modes, and binary data handling.

#### Webhook node reference for (Part 3): Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBHOOK_URL` | `<http://localhost:5678`> | Base URL for webhook endpoints |
| `APP_PAYLOAD_SIZE_MAX` | `16` | Maximum request body size in MB |

#### Webhook node reference for (Part 3): Related

- [Configure Webhook authentication](../../how-to/configure-webhook-trigger.md)
- [Webhook not firing](../../troubleshooting/webhook-not-firing.md)
- [Workflow execution model](../../concepts/workflow-execution-model.md)

#### Webhook node reference for (Part 3): Next steps

- [Documentation index](../index.md)

### Fix: Webhook trigger not firing (Part 3)

Troubleshoot Webhook nodes that do not receive requests. Common causes include inactive workflows, wrong URL type, and network configuration.

#### Fix: Webhook trigger not firing (Part 3): Still not working?

1. Check the logs for errors: `docker logs` or the process output.
1. Test with a minimal `curl` command from the same network as the service.
1. Verify the HTTP method matches (the Webhook node only responds to the configured method).

#### Fix: Webhook trigger not firing (Part 3): Related

- [Webhook node reference](../reference/nodes/webhook.md)
- [Configure Webhook authentication](../how-to/configure-webhook-trigger.md)

#### Fix: Webhook trigger not firing (Part 3): Next steps

- [Documentation index](index.md)

### Configure HMAC authentication for inbound webhooks

Covers secure webhook authentication setup for docs, assistant responses, in-product hints, and automation workflows with one reusable module.

Use HMAC validation to reject spoofed webhook requests before your workflow executes. Set the shared secret in {{ env_vars.webhook_url }} settings, then verify the `X-Signature` header with SHA-256. Reject requests older than 300 seconds, and return HTTP 401 for invalid signatures.

```bash

curl -X POST "http://localhost:{{ default_webhook_port }}/webhook/order-events" \\
  -H "Content-Type: application/json" \\
  -H "X-Signature: sha256=YOUR_CALCULATED_SIGNATURE" \\
  -d '{"order_id":"ord_9482","event":"order_paid","amount":129.99}'

```

Keep replay protection enabled, rotate the secret every 90 days, and monitor 401 spikes for abuse detection.

## Next steps

- Validate modules: `npm run lint:knowledge`
- Rebuild retrieval index: `npm run build:knowledge-index`
- Generate assistant pack: `npm run build:intent -- --channel assistant`

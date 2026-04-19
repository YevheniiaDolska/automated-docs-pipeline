---
title: "Intent experience: secure for developer"
description: "Assembled guidance for one intent and audience using reusable knowledge modules with verified metadata and channel-ready sections."
content_type: reference
product: both
tags:
  - Reference
  - AI
---

<!-- markdownlint-disable MD001 MD007 MD024 MD025 MD031 -->

# Intent experience: secure for developer

This page is assembled for the `secure` intent and the `developer` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent secure --audience developer --channel docs
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

### Configure webhook triggers

Set up and configure webhook trigger nodes to start workflows from incoming HTTP requests with authentication.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### Configure webhook triggers: Configure webhook triggers

The {{ product_name }} webhook trigger node starts workflows when it
receives HTTP requests. It supports GET, POST, PUT, PATCH, and DELETE
methods with built-in authentication options including Basic Auth,
Header Auth, and JWT validation.

#### Configure webhook triggers: Before you start

You need:

- {{ product_name }} {{ current_version }} or later
- Access to create workflows
- A publicly accessible URL (or a tunnel for local development)

#### Configure webhook triggers: Create a webhook trigger

1. Open the {{ product_name }} editor
1. Add a new workflow
1. Select **Webhook** as the trigger node
1. Choose the HTTP method (POST is recommended for event data)
1. Copy the generated webhook URL

=== "Cloud"

    {{ product_name }} Cloud provides a public URL automatically:

```text

    {{ cloud_url }}/webhook/your-workflow-id

```

=== "Self-hosted"

    Configure your instance URL with the {{ env_vars.webhook_url }}
    environment variable:

```bash

    export {{ env_vars.webhook_url }}="https://your-domain.example.com"

```

    Your webhook URL follows this pattern:

```text

    https://your-domain.example.com:{{ default_port }}/webhook/your-workflow-id

```

### Configure webhook triggers (Part 2)

Set up and configure webhook trigger nodes to start workflows from incoming HTTP requests with authentication.

#### Configure webhook triggers (Part 2): Configure authentication

!!! warning "Secure your webhooks"
    Always enable authentication on production webhook endpoints.
    Unauthenticated webhooks accept requests from any source.

Add authentication in the webhook node settings:

| Auth method | Use case | Configuration |
|-------------|----------|---------------|
| Header Auth | API key validation | Set header name and expected value |
| Basic Auth | Username and password | Set credentials in node settings |
| JWT | Token-based auth | Configure secret and algorithm |

### VeriDoc data processing agreement (Part 2)

Data processing agreement for VeriDoc platform covering GDPR compliance, sub-processors, data transfer mechanisms, and breach notification procedures.

##### VeriDoc data processing agreement (Part 2): Nature and purpose of processing

| Processing activity | Purpose | Data categories |
|---------------------|---------|-----------------|
| Pipeline execution | Transform and enhance documentation | Documentation content, metadata |
| LLM processing (opt-in) | AI-powered quality improvements | Document sections sent to LLM providers |
| Usage tracking | Quota enforcement and billing | Request counts, timestamps |
| Authentication | Access control | Email, hashed passwords, JWT tokens |
| Billing | Payment processing and invoicing | Email, subscription tier, payment history |

##### VeriDoc data processing agreement (Part 2): Categories of data subjects

Data subjects include your employees, contractors, and any individuals
whose personal data appears in documentation processed through VeriDoc.

### VeriDoc data processing agreement (Part 6)

Data processing agreement for VeriDoc platform covering GDPR compliance, sub-processors, data transfer mechanisms, and breach notification procedures.

##### VeriDoc data processing agreement (Part 6): EU-US transfers

For sub-processors located in the United States, we rely on:

1. Standard Contractual Clauses (SCCs) approved by the European Commission
   (June 2021 version).
1. Supplementary measures including encryption in transit and at rest.
1. Data minimization -- only the minimum data necessary is transferred.

##### VeriDoc data processing agreement (Part 6): Transfer impact assessment

We have conducted transfer impact assessments for each non-EU
sub-processor. Assessments are available upon request at
<privacy@veri-doc.app>.

#### VeriDoc data processing agreement (Part 6): Data breach notification

In the event of a personal data breach:

| Step | Timeline | Action |
|------|----------|--------|
| 1 | Within 24 hours | Internal incident response team activated |
| 2 | Within 72 hours | Written notification to you with breach details |
| 3 | Within 72 hours | Notification to supervisory authority (if required) |
| 4 | Ongoing | Regular updates on investigation and remediation |

Breach notification includes:

1. Nature of the breach and categories of data affected.
1. Estimated number of data subjects affected.
1. Likely consequences of the breach.
1. Measures taken to address and mitigate the breach.

### Install Ask AI runtime pack

Install the optional Ask AI runtime pack with API endpoint, widget, auth checks, and billing hooks in a few commands.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### Install Ask AI runtime pack: Install Ask AI runtime pack

Use this guide when a client asks for Ask AI runtime features such as a live endpoint, an embeddable widget, and billing webhook hooks.

```bash

npm run askai:runtime:install
npm run askai:status

```

#### Install Ask AI runtime pack: Before you start

You need:

- Pipeline repository installed in the client project
- `config/ask-ai.yml` present
- Python 3.10 or newer

#### Install Ask AI runtime pack: Step 1: Install the runtime pack

Run:

```bash

npm run askai:runtime:install

```

This creates `ask-ai-runtime/` with:

- FastAPI server (`app/main.py`) with advanced retrieval config
- auth guards (`app/auth.py`)
- billing hooks (`app/billing_hooks.py`)
- retrieval helpers (`app/retrieval.py`) with hybrid search, HyDE, reranking, embedding cache, and chunk deduplication
- widget script (`public/ask-ai-widget.js`)
- `.env.example` and runtime `README.md`

Runtime dependencies include `faiss-cpu`, `numpy`, `sentence-transformers` (for cross-encoder reranking), and `tiktoken` (for token-aware chunking).

#### Install Ask AI runtime pack: Step 2: Configure Ask AI module

Enable Ask AI and select billing mode:

```bash

npm run askai:enable
npm run askai:configure -- --provider openai --billing-mode user-subscription --model gpt-4.1-mini

```

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

### Operator Runbook (Retainer Operations) (Part 5)

Step-by-step instructions for weekly report review, client questions, new repo setup, and profile tuning.

##### Operator Runbook (Retainer Operations) (Part 5): Step 1.3: Review action items by priority

Scroll to `action_items` array. Items are pre-sorted by priority:

- **Tier 1 (high priority):** items with `source_report: "drift"` or `source_report: "sla"` -- these indicate broken API docs or SLA violations. Inform the client immediately.
- **Tier 2 (medium priority):** items with categories like `stale_doc`, `signature_change`, `new_function` -- these are code-driven gaps. Include in next documentation sprint.
- **Tier 3 (low priority):** community/search-driven gaps. Schedule when capacity allows.

##### Operator Runbook (Retainer Operations) (Part 5): Step 1.4: Send the weekly summary to the client

Write a brief summary (3-5 sentences) covering:

1. Quality score and trend (up/down/stable vs last week).
1. Any drift or SLA issues that need attention.
1. Number of action items by tier.
1. Recommended next steps (if any).

**Example email:**

> Weekly VeriOps Report -- ACME Inc. (March 21, 2026)
>
> Quality score: 82 (up from 76 last week). No API drift detected.
> SLA status: OK (all thresholds met).
> Action items: 3 high priority (stale auth docs), 5 medium, 4 low.
> Recommendation: Update authentication reference docs this week.

### Pipeline Capabilities Catalog (Part 13)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

#### Pipeline Capabilities Catalog (Part 13): Test assets generation and smart merge

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

### Pipeline Capabilities Catalog (Part 20)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

#### Pipeline Capabilities Catalog (Part 20): Templates

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

#### Pipeline Capabilities Catalog (Part 20): Policy Packs

- `api-first.yml`
- `minimal.yml`
- `monorepo.yml`
- `multi-product.yml`
- `plg.yml`

#### Pipeline Capabilities Catalog (Part 20): Knowledge Modules

Can be copied into client bundle with `bundle.include_paths: ['knowledge_modules']`.

- `webhook-auth-baseline.yml`
- `webhook-retry-policy.yml`

### VeriDoc privacy policy

Privacy policy for VeriDoc automated documentation platform, covering data collection, processing, storage, retention, and your rights under GDPR.

### VeriDoc privacy policy: VeriDoc privacy policy

This privacy policy explains how Liora Tech ("Company," "we," "us")
collects, uses, and protects your personal data when you use VeriDoc,
an automated documentation pipeline platform. This policy applies to
all users of the VeriDoc web application, API, and CLI tools.

#### VeriDoc privacy policy: Data controller

Liora Tech acts as the data controller for personal data collected through
the VeriDoc platform.

| Detail | Value |
|--------|-------|
| **Company** | Liora Tech |
| **Contact email** | <privacy@veri-doc.app> |
| **Data protection inquiries** | <privacy@veri-doc.app> |

#### VeriDoc privacy policy: Data we collect

##### VeriDoc privacy policy: Account data

When you register, we collect:

| Data field | Purpose | Legal basis |
|------------|---------|-------------|
| Email address | Authentication, billing notifications, support | Contract performance |
| Password hash | Authentication (PBKDF2-SHA256, never stored in plaintext) | Contract performance |
| Subscription tier | Service delivery, usage limit enforcement | Contract performance |
| Billing records | Payment processing, invoice generation | Contract performance |
| Referral code | Referral program tracking | Legitimate interest |

### VeriDoc privacy policy (Part 2)

Privacy policy for VeriDoc automated documentation platform, covering data collection, processing, storage, retention, and your rights under GDPR.

##### VeriDoc privacy policy (Part 2): Usage data

When you use the Service, we automatically collect:

| Data field | Purpose | Retention |
|------------|---------|-----------|
| Pipeline run metadata | Usage tracking, quota enforcement | 90 days |
| API request logs | Rate limiting, debugging, abuse prevention | 30 days |
| Error reports (Sentry) | Bug fixing, reliability improvement | 90 days |
| Authentication tokens | Session management | Token expiry (24 hours) |

##### VeriDoc privacy policy (Part 2): Documentation content

When you process documentation through the pipeline:

1. Your content is processed in memory during pipeline execution.
1. Generated outputs (processed Markdown, reports, knowledge modules) are
   stored in encrypted PostgreSQL databases.
1. We do not read, analyze, or use your documentation content for any
   purpose other than providing the Service.
1. We do not use your content to train machine learning models.

### VeriDoc privacy policy (Part 4)

Privacy policy for VeriDoc automated documentation platform, covering data collection, processing, storage, retention, and your rights under GDPR.

#### VeriDoc privacy policy (Part 4): How we use your data

We use personal data exclusively for:

1. **Service delivery** -- processing your documentation, enforcing usage
   limits, and managing your subscription.
1. **Billing** -- processing payments through LemonSqueezy, generating
   invoices, tracking referral commissions.
1. **Communication** -- sending transactional emails (subscription
   confirmations, trial expiry notices, invoice receipts).
1. **Security** -- detecting unauthorized access, enforcing rate limits,
   monitoring for abuse.
1. **Improvement** -- analyzing aggregate, anonymized usage patterns to
   improve the Service. We never analyze individual content.

#### VeriDoc privacy policy (Part 4): Data storage and security

##### VeriDoc privacy policy (Part 4): Infrastructure

| Component | Location | Encryption |
|-----------|----------|------------|
| Application servers | Hetzner Cloud, Germany | TLS 1.3 in transit |
| PostgreSQL database | Hetzner Cloud, Germany | AES-256 at rest |
| Redis cache | Hetzner Cloud, Germany | In-memory, no persistence of content |
| Backups | Hetzner Cloud, Germany | AES-256, 30-day retention |

### VeriDoc privacy policy (Part 5)

Privacy policy for VeriDoc automated documentation platform, covering data collection, processing, storage, retention, and your rights under GDPR.

##### VeriDoc privacy policy (Part 5): Security measures

1. All API communication uses TLS 1.3 encryption.
1. Passwords are hashed with PBKDF2-SHA256 (600,000 iterations).
1. JWT authentication tokens expire after 24 hours.
1. Database backups run daily with 30-day retention and automated restore
   testing.
1. Error tracking uses Sentry with PII scrubbing enabled.
1. Rate limiting enforces 60 requests per minute per user.

#### VeriDoc privacy policy (Part 5): Data retention

| Data type | Retention period | Deletion trigger |
|-----------|-----------------|------------------|
| Account data | Account lifetime + 30 days | Account closure |
| Billing records | 7 years (legal requirement) | Statutory expiry |
| Pipeline outputs | Account lifetime + 30 days | Account closure |
| API logs | 30 days | Automatic rotation |
| Error reports | 90 days | Automatic rotation |
| Backups | 30 days | Automatic rotation |

After account closure, we retain data for 30 days to allow you to
reactivate or export. After 30 days, all personal data is permanently
deleted.

### VeriDoc security contact policy

Security contact channels, response times, severity model, and disclosure workflow for VeriDoc incidents and vulnerability reports.

### VeriDoc security contact policy: VeriDoc security contact policy

This policy defines exactly how to contact VeriDoc for security incidents,
vulnerability reports, and urgent abuse cases.

#### VeriDoc security contact policy: Official contact channels

| Purpose | Channel | Target response |
|---------|---------|-----------------|
| Vulnerability disclosure | <security@veri-doc.app> | Within 24 hours |
| Incident escalation (active outage or suspected compromise) | <security@veri-doc.app> + <support@veri-doc.app> | Within 1 hour |
| Privacy and data-protection issues | <privacy@veri-doc.app> | Within 72 hours |

#### VeriDoc security contact policy: What to include in your report

Send a concise report with:

1. Affected endpoint, system, or feature.
1. Exact reproduction steps.
1. Expected result and actual result.
1. Scope estimate (single tenant, multi-tenant, or unknown).
1. Any logs, timestamps, and request IDs.

#### VeriDoc security contact policy: Severity model and SLA

| Severity | Typical examples | First response | Containment target |
|----------|------------------|----------------|--------------------|
| Critical | Data exposure, account takeover, production compromise | 1 hour | 4 hours |
| High | Auth bypass, privilege escalation, sustained API failure | 4 hours | 12 hours |
| Medium | Non-critical security misconfiguration | 24 hours | 3 business days |
| Low | Hardening recommendations, low-risk findings | 72 hours | Planned release |

### VeriDoc security policy

Security policy for VeriDoc platform covering infrastructure security, encryption, authentication, access controls, and incident response procedures.

### VeriDoc security policy: VeriDoc security policy

VeriDoc is an automated documentation pipeline platform that processes
customer documentation content. This security policy describes the
technical and organizational measures we implement to protect your data
and maintain service integrity.

#### VeriDoc security policy: Infrastructure security

##### VeriDoc security policy: Hosting environment

VeriDoc runs on dedicated infrastructure in Hetzner Cloud data centers
located in Germany (EU).

| Component | Technology | Security configuration |
|-----------|------------|----------------------|
| Application server | Ubuntu 22.04 LTS | Automated security patches, SSH key-only access |
| API service | FastAPI (Python 3.12) | CORS-restricted, rate-limited, JWT-authenticated |
| Database | PostgreSQL 16 | Encrypted at rest (AES-256), TLS connections |
| Cache | Redis 7 | Memory-only, no content persistence, private network |
| Task queue | Celery + Redis | Isolated worker processes, task timeout enforcement |
| Reverse proxy | Nginx | TLS 1.3, HTTP/2, security headers, rate limiting |

### VeriDoc security policy (Part 2)

Security policy for VeriDoc platform covering infrastructure security, encryption, authentication, access controls, and incident response procedures.

##### VeriDoc security policy (Part 2): Network security

1. All public endpoints require TLS 1.3 encryption. Older TLS versions
   are rejected.
1. Database and Redis ports are bound to `127.0.0.1` only -- no external
   access.
1. SSH access uses Ed25519 keys exclusively. Password authentication is
   disabled.
1. Firewall rules allow only ports 80 (redirect to 443), 443 (HTTPS), and
   22 (SSH from allowlisted IPs).

#### VeriDoc security policy (Part 2): Authentication and access control

##### VeriDoc security policy (Part 2): User authentication

| Mechanism | Implementation |
|-----------|---------------|
| Password hashing | PBKDF2-SHA256 with 600,000 iterations |
| Token format | JWT (PyJWT) with HS256 signing |
| Token expiry | 24 hours |
| Session management | Stateless JWT, no server-side sessions |
| Rate limiting | 60 requests per minute per user |

##### VeriDoc security policy (Part 2): API authentication

All API endpoints except `/health` and `/auth/register` require a valid
JWT token in the `Authorization: Bearer <token>` header.

```text

POST /auth/login
Content-Type: application/json

{"email": "user@example.com", "password": "your-password"}

Response: {"token": "eyJ...", "expires_in": 86400}

```

##### VeriDoc security policy (Part 2): Webhook verification

Incoming LemonSqueezy webhooks are verified using HMAC-SHA256 signatures.
Requests without a valid `X-Signature` header are rejected with HTTP 403.

#### VeriDoc security policy (Part 2): Encryption

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

### Set up a real-time webhook processing pipeline

Configure end-to-end webhook ingestion with HMAC verification, async queue processing, and delivery guarantees in under 15 minutes.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### Set up a real-time webhook processing pipeline: Set up a real-time webhook processing pipeline

{{ product_name }} webhook processing pipeline enables real-time event ingestion with cryptographic signature verification, async queue processing, and automatic retry logic. This guide walks you through setting up a production-ready webhook receiver with HMAC-SHA256 authentication, BullMQ event queuing, and delivery guarantees supporting up to {{ rate_limit_requests_per_minute }} events per minute.

#### Set up a real-time webhook processing pipeline: Prerequisites for webhook pipeline setup

Before starting, ensure you have:

- {{ product_name }} version {{ current_version }} or later
- Admin access to the {{ product_name }} dashboard at {{ cloud_url }}
- Node.js 18 or later and Python 3.10 or later installed
- Redis 7.0 or later running for queue storage
- 15 minutes for initial setup

Verify your environment:

```bash

node --version    # v18.0.0 or later
python3 --version # 3.10 or later
redis-cli ping    # PONG

```

!!! info "Already have a webhook endpoint running?"
    Skip to [configure HMAC signature verification](#verify-hmac-sha256-signatures) for adding cryptographic authentication to an existing receiver.

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

### VeriDoc terms of service

Terms of service governing the use of VeriDoc automated documentation platform, including subscription tiers, usage limits, and acceptable use policies.

### VeriDoc terms of service: VeriDoc terms of service

These terms of service ("Terms") govern your access to and use of VeriDoc,
an automated documentation pipeline platform operated by Liora Tech
("Company," "we," "us"). By creating an account or using the service, you
agree to these Terms.

#### VeriDoc terms of service: Key definitions

| Term | Meaning |
|------|---------|
| **Service** | The VeriDoc platform, including the API, web interface, and CLI tools |
| **User** | Any individual or entity that creates an account on the Service |
| **Subscription** | A paid plan that grants access to premium features and higher usage limits |
| **Content** | Documentation, code, configuration, and other materials processed by the Service |
| **Pipeline run** | A single execution of the documentation processing pipeline |

#### VeriDoc terms of service: Account registration

You must provide accurate information when creating an account. Each user
must maintain one account. Sharing account credentials violates these Terms.

You are responsible for all activity under your account. Notify us at
<support@veri-doc.app> if you suspect unauthorized access.

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

- [Documentation index](../../index.md)

## Next steps

- Validate modules: `npm run lint:knowledge`
- Rebuild retrieval index: `npm run build:knowledge-index`
- Generate assistant pack: `npm run build:intent -- --channel assistant`

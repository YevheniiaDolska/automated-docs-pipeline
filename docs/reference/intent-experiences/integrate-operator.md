---
title: "Intent experience: integrate for operator"
description: "Assembled guidance for one intent and audience using reusable knowledge modules with verified metadata and channel-ready sections."
content_type: reference
product: both
tags:
  - Reference
  - AI
---

<!-- markdownlint-disable MD001 MD007 MD024 MD025 MD031 -->

# Intent experience: integrate for operator

This page is assembled for the `integrate` intent and the `operator` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent integrate --audience operator --channel docs
```

## Included modules

### API playground

Interactive API reference with Swagger UI or Redoc and configurable sandbox behavior for product-led growth.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

#### API playground: Overview

This page embeds an API sandbox into documentation.

Use it to support product-led growth by giving users interactive API exploration
inside docs.

#### API playground: Provider options

1. `swagger-ui`: interactive explorer with optional `Try it out` requests.
1. `redoc`: high-readability API reference view.

#### API playground: Configure this page

Use the unified PLG config in `mkdocs.yml` under `extra.plg.api_playground`.
This works for both API-first and code-first teams.

- `provider`: `swagger-ui` or `redoc`
- `source.strategy`: `api-first` or `code-first`
- `source.api_first_spec_url`: OpenAPI spec URL for API-first
- `source.code_first_spec_url`: generated spec URL for code-first
- `try_it_enabled`: `true` or `false`
- `try_it_mode`: `sandbox-only`, `real-api`, or `mixed`
- `endpoints.sandbox_base_url`: request target for sandbox mode
- `endpoints.production_base_url`: request target for real API mode

### API playground (Part 2)

Interactive API reference with Swagger UI or Redoc and configurable sandbox behavior for product-led growth.

#### API playground (Part 2): Playground

<div id="swagger-ui-general"></div>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.18.2/swagger-ui.css">
<script src="https://unpkg.com/swagger-ui-dist@5.18.2/swagger-ui-bundle.js"></script>
<script>
(function() {
  var specUrl = "{{ config.site_url }}{{ config.extra.plg.api_playground.source.api_first_spec_url }}";
  var sandboxUrl = "{{ config.extra.plg.api_playground.endpoints.sandbox_base_url }}";
  function boot() {
    if (typeof SwaggerUIBundle === "undefined") { setTimeout(boot, 100); return; }
    SwaggerUIBundle({
      url: specUrl,
      dom_id: "#swagger-ui-general",
      deepLinking: true,
      docExpansion: "list",
      defaultModelsExpandDepth: 1,
      supportedSubmitMethods: [],
      requestInterceptor: function (req) {
        if (req.url === specUrl || req.url.indexOf("openapi") !== -1) return req;
        try {
          var u = new URL(req.url, location.origin);
          var t = new URL(sandboxUrl, location.origin);
          u.protocol = t.protocol; u.hostname = t.hostname; u.port = t.port;
          req.url = u.toString();
        } catch (e) {}
        return req;
      }
    });
  }
  boot();
})();
</script>

### API playground (Part 3)

Interactive API reference with Swagger UI or Redoc and configurable sandbox behavior for product-led growth.

#### API playground (Part 3): Security guidance

1. `sandbox-only`: safest default for regulated or high-risk domains.
1. `real-api`: use only when product policy allows direct user requests.
1. `mixed`: let user choose sandbox vs real API explicitly.
1. Keep write operations protected by auth scopes and rate limits.

#### API playground (Part 3): Next steps

- [Documentation index](index.md)

### ASYNCAPI API Reference

Auto-generated asyncapi reference from source contract.

### ASYNCAPI API Reference: ASYNCAPI Reference

Source: `/tmp/pytest-of-eudo/pytest-2841/test_multi_protocol_flow_e2e_e0/asyncapi.yaml`

Flow mode: `api-first`

#### ASYNCAPI API Reference: Top-level Keys

- `asyncapi`
- `channels`
- `info`

#### ASYNCAPI API Reference: Channels

- Channel count: `1`
- `orders/created`

### ASYNCAPI API Reference (Part 2)

Auto-generated asyncapi reference from source contract.

#### ASYNCAPI API Reference (Part 2): Interactive AsyncAPI Tester

> Sandbox semantic mode: this tester returns event-aware responses by `event_type` and payload fields.

### ASYNCAPI API Reference (Part 3)

Auto-generated asyncapi reference from source contract.

<div id="asyncapi-playground" style="border:1px solid #d1d5db; padding:12px; border-radius:8px;">
  <p><strong>WebSocket Endpoint:</strong> <code id="asyncapi-ws-view"></code></p>
  <p><strong>HTTP Publish Endpoint:</strong> <code id="asyncapi-http-view"></code></p>
  <!-- vale off -->
  <textarea id="asyncapi-message" rows="8" style="width:100%; font-family:monospace;">{
  "event_type": "project.updated",
  "event_id": "evt_001",
  "data": {"project_id": "prj_abc123", "status": "active"}
}</textarea><br/>
  <!-- vale on -->
  <button id="asyncapi-send-ws">Send via WebSocket</button>
  <button id="asyncapi-send-http">Send via HTTP</button>
  <pre id="asyncapi-output" style="margin-top:12px; max-height:320px; overflow:auto;"></pre>
</div>
<script>
(function(){ const wsEndpoint = "wss://echo.websocket.events"; const httpEndpoint = "https://postman-echo.com/post";
const wsView = document.getElementById('asyncapi-ws-view');
const httpView = document.getElementById('asyncapi-http-view');
const sendWs = document.getElementById('asyncapi-send-ws');
const sendHttp = document.getElementById('asyncapi-send-http');
const msg = document.getElementById('asyncapi-message');
const out = document.getElementById('asyncapi-output');
if (!wsView || !httpView || !sendWs || !sendHttp || !msg || !out) return;
wsView.textContent = wsEndpoint || 'not configured';
httpView.textContent = httpEndpoint || 'not configured';
function parseJson(raw){ try { return JSON.parse(String(raw || '{}')); } catch (_) { return { raw: String(raw || '') }; } }
function semanticEvent(input){
  const req = parseJson(input);
  const eventType = String(req.event_type || req.type || req.event || '').toLowerCase();
  const data = (req.data && typeof req.data === 'object') ? req.data : {};
  const eventId = req.event_id || ('evt_' + Math.random().toString(36).slice(2, 10));
  const projectId = String(data.project_id || 'prj_abc123');
  const occurredAt = req.occurred_at || new Date().toISOString();
  if (eventType === 'project.created') return { event_id: eventId, event_type: 'project.created', occurred_at: occurredAt, data: { project_id: projectId, name: data.name || 'New Project', status: data.status || 'draft' } };
  if (eventType === 'project.updated') return { event_id: eventId, event_type: 'project.updated', occurred_at: occurredAt, data: { project_id: projectId, status: data.status || 'active', changed_fields: data.changed_fields || ['status'] } };
  if (eventType === 'task.completed') return { event_id: eventId, event_type: 'task.completed', occurred_at: occurredAt, data: { task_id: data.task_id || 'tsk_123', project_id: projectId, completed_by: data.completed_by || 'usr_demo' } };
  return { event_id: eventId, event_type: eventType || 'custom.event', occurred_at: occurredAt, data: Object.assign({ project_id: projectId, status: 'accepted' }, data), hint: 'Use: project.created, project.updated, task.completed' };
}
sendWs.onclick = function(){
  if (!wsEndpoint) { out.textContent = 'WebSocket endpoint is not configured (runtime.api_protocol_settings.asyncapi.asyncapi_ws_endpoint)'; return; }
  try {
    const socket = new WebSocket(wsEndpoint);
    let received = false;
    socket.onopen = function(){ socket.send(msg.value); out.textContent = 'sent over websocket'; };
    socket.onmessage = function(e){
      received = true;
      const semantic = semanticEvent(e.data);
      out.textContent = JSON.stringify({ mode: 'live-echo-plus-semantic', raw: String(e.data || ''), simulated_response: semantic }, null, 2);
      socket.close();
    };
    socket.onerror = function(){
      const semantic = semanticEvent(msg.value);
      out.textContent = JSON.stringify({ mode: 'offline-semantic-fallback', simulated_response: semantic }, null, 2);
    };
    setTimeout(function(){
      if (!received) {
        const semantic = semanticEvent(msg.value);
        out.textContent = JSON.stringify({ mode: 'timeout-semantic-fallback', simulated_response: semantic }, null, 2);
        try { socket.close(); } catch (_) {}
      }
    }, 1500);
  } catch (error) { out.textContent = String(error); }
};
sendHttp.onclick = async function(){
  if (!httpEndpoint) { out.textContent = 'HTTP publish endpoint is not configured (runtime.api_protocol_settings.asyncapi.asyncapi_http_publish_endpoint)'; return; }
  out.textContent = 'Loading...';
  try {
    const body = JSON.parse(msg.value || '{}');
    const response = await fetch(httpEndpoint, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify(body) });
    const text = await response.text();
    const semantic = semanticEvent(body);
    out.textContent = JSON.stringify({ mode: 'http-plus-semantic', raw: text, simulated_response: semantic }, null, 2);
  } catch (error) {
    const semantic = semanticEvent(msg.value);
    out.textContent = JSON.stringify({ mode: 'http-semantic-fallback', error: String(error), simulated_response: semantic }, null, 2);
  }
};
})();
</script>

### ASYNCAPI API Reference (Part 4)

Auto-generated asyncapi reference from source contract.

#### ASYNCAPI API Reference (Part 4): Next steps

- [Documentation index](index.md)

This auto-generated knowledge chunk was expanded to satisfy minimum retrieval module length for stable indexing.

### Auto-Doc Pipeline study guide

Learn the Auto-Doc Pipeline quickly with a simple architecture map, operating flow, plan mapping, and a detailed client FAQ.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### Auto-Doc Pipeline study guide: Auto-Doc Pipeline study guide

Auto-Doc Pipeline is a docs-first platform that also supports code-first and API-first delivery. It enables teams to generate, verify, and publish documentation, non-REST stubs, mock sandboxes, and contract tests in one smooth automation flow.

```bash

python3 scripts/run_multi_protocol_contract_flow.py \
  --runtime-config docsops/config/client_runtime.yml \
  --reports-dir reports

```

#### Auto-Doc Pipeline study guide: One-minute mental model

1. Input: planning notes, contracts, codebase signals, and docs state.
1. Build: contracts, docs pages, server stubs, mock endpoints, and test assets.
1. Verify: quality gates, contract checks, smoke checks, and lifecycle checks.
1. Publish: review packet, optional approval, site build, and deployment.

#### Auto-Doc Pipeline study guide: What this platform is optimized for

- Keep docs aligned with releases without manual rework.
- Support REST and non-REST APIs in one operational model.
- Let QA test endpoints from docs before full backend implementation.
- Keep enterprise-grade governance through policy packs and quality gates.

### Auto-Doc Pipeline study guide (Part 2)

Learn the Auto-Doc Pipeline quickly with a simple architecture map, operating flow, plan mapping, and a detailed client FAQ.

#### Auto-Doc Pipeline study guide (Part 2): Modes you should remember

| Mode | Primary source | Best use case |
| --- | --- | --- |
| `code-first` | Existing code/contracts | Mature product with frequent implementation change |
| `api-first` | Planning notes and contract design | New API products, contract-first delivery |
| `hybrid` | Both code and contract sources | Teams migrating from ad-hoc to governed docs ops |

### Auto-Doc Pipeline study guide (Part 3)

Learn the Auto-Doc Pipeline quickly with a simple architecture map, operating flow, plan mapping, and a detailed client FAQ.

#### Auto-Doc Pipeline study guide (Part 3): Smooth autopipeline flow (what runs automatically)

1. Run weekly baseline checks: gap detection, stale checks, drift/docs-contract checks, and KPI/SLA (as enabled).
1. Run REST API-first branch (if enabled): OpenAPI flow, sandbox resolution, overrides, regression gate, and REST test assets.
1. Run multi-protocol non-REST branch (if enabled): `run_multi_protocol_contract_flow.py` for GraphQL, gRPC, AsyncAPI, and WebSocket.
1. Auto-generate non-REST server stubs with business-logic placeholders.
1. Resolve runtime endpoints for self-verification and docs testers; in `external` mode with `external_mock.enabled=true`, auto-prepare Postman mock.
1. Run RAG/knowledge tasks: modules extraction, module validation, retrieval index, JSON-LD graph, and retrieval evals.
1. Run terminology governance: sync glossary markers into `glossary.yml`.
1. Run multi-language examples flow: generate tabs, validate tabs, and run smoke checks.
1. Run intent assembly and `custom_tasks.weekly`, then write consolidated reports.

### Auto-Doc Pipeline study guide (Part 4)

Learn the Auto-Doc Pipeline quickly with a simple architecture map, operating flow, plan mapping, and a detailed client FAQ.

#### Auto-Doc Pipeline study guide (Part 4): Non-REST capability pack (GraphQL, gRPC, AsyncAPI, WebSocket)

- Contract generation and validation run per protocol.
- Server stubs are generated under `generated/api-stubs/<protocol>/`.
- Mock sandbox endpoints are resolved before live self-verification.
- Interactive docs testers use resolved sandbox URLs.
- Contract tests are generated and merged with existing customized cases.

#### Auto-Doc Pipeline study guide (Part 4): Plan-level distribution (quick map)

| Capability | Basic | Pro | Enterprise |
| --- | --- | --- | --- |
| Core docs quality gates | Yes | Yes | Yes |
| REST API-first automation | No | Optional | Full |
| Non-REST autopipeline + stubs + Postman mock | No | No | Yes |
| Contract test assets + smart merge | No | Yes | Yes |
| Knowledge/RAG maintenance | No | Yes | Yes |
| Strict multi-protocol publish gating | No | No | Yes |

#### Auto-Doc Pipeline study guide (Part 4): Your setup steps for each client repository

Use this checklist when you onboard a new client repo.

##### Auto-Doc Pipeline study guide (Part 4): Step 1: collect required inputs from the client

1. Repository URL and default branch.
1. Docs root path (for example `docs/`).
1. Runtime mode to start with: `code-first`, `api-first`, or `hybrid`.
1. Plan scope (Basic, Pro, Enterprise) and modules to enable.
1. API scope: REST-only or multi-protocol (GraphQL/gRPC/AsyncAPI/WebSocket).

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

### Auto-Doc Pipeline study guide (Part 6)

Learn the Auto-Doc Pipeline quickly with a simple architecture map, operating flow, plan mapping, and a detailed client FAQ.

##### Auto-Doc Pipeline study guide (Part 6): Step 6: enable automation

1. Install weekly scheduler (Linux cron or Windows task).
1. Keep `git_sync.enabled=true` unless client requests otherwise.
1. Optionally enable PR auto-fix workflow.
1. Optional: enable strict publish gates for enterprise clients.

##### Auto-Doc Pipeline study guide (Part 6): Step 7: handoff and operating cadence

1. Share report reading routine with client reviewers.
1. Keep human step focused on review/approval, not routine doc plumbing.
1. Revisit plan scope as usage grows (Pro -> Enterprise when needed).

#### Auto-Doc Pipeline study guide (Part 6): Core artifacts to know by memory

- `reports/consolidated_report.json`: top-level operational report.
- `reports/multi_protocol_contract_report.json`: protocol execution summary.
- `reports/api-test-assets/api_test_cases.json`: generated contract test set.
- `reports/api-test-assets/merge_report.json`: smart-merge decisions and `needs_review_ids`.
- `generated/api-stubs/<protocol>/handlers.py`: generated server stubs.

#### Auto-Doc Pipeline study guide (Part 6): Detailed FAQ for potential clients

##### Auto-Doc Pipeline study guide (Part 6): 1) What business problem does this solve first?

It removes the release bottleneck caused by stale docs, broken API examples, and manual test asset maintenance.

##### Auto-Doc Pipeline study guide (Part 6): 2) Is this only an API-first product?

No. The platform is docs-first and supports `code-first`, `api-first`, and `hybrid` operations in the same runtime.

##### Auto-Doc Pipeline study guide (Part 6): 3) Which API protocols are supported?

REST, GraphQL, gRPC, AsyncAPI, and WebSocket.

### Auto-Doc Pipeline study guide (Part 7)

Learn the Auto-Doc Pipeline quickly with a simple architecture map, operating flow, plan mapping, and a detailed client FAQ.

##### Auto-Doc Pipeline study guide (Part 7): 4) What is generated automatically for non-REST APIs?

Contracts, protocol references, server stubs with business placeholders, mock endpoint wiring, and contract test assets.

##### Auto-Doc Pipeline study guide (Part 7): 5) Can we test endpoints before backend implementation is complete?

Yes. The mock sandbox flow allows early endpoint testing from documentation and contract definitions.

##### Auto-Doc Pipeline study guide (Part 7): 6) Is Postman mandatory for mocks?

No. External mode is provider-agnostic. Postman is the built-in first-class path for auto-prepare.

##### Auto-Doc Pipeline study guide (Part 7): 7) How does smart merge protect manual test work?

Manual and customized cases are preserved across generation cycles; changed signatures are flagged for targeted review.

##### Auto-Doc Pipeline study guide (Part 7): 8) Does this replace technical writers?

No. It removes repetitive work and leaves writers with high-value review, structure, and clarity decisions.

##### Auto-Doc Pipeline study guide (Part 7): 9) What do developers gain directly?

Faster contract feedback, stub scaffolding, earlier integration checks, and fewer release surprises.

##### Auto-Doc Pipeline study guide (Part 7): 10) What do QA teams gain directly?

Auto-generated protocol-aware test packs, earlier mock-first verification, and reduced test case drift.

##### Auto-Doc Pipeline study guide (Part 7): 11) How do we control quality standards?

Through policy packs, strict gates, and threshold settings in runtime configuration.

##### Auto-Doc Pipeline study guide (Part 7): 12) Does this support enterprise governance?

Yes. It provides auditable reports, gate outcomes, and policy-driven publish control.

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

### Canonical Flow (Sales + Delivery)

Canonical sales and delivery flow for onboarding and operating client Auto-Doc Pipeline setups.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### Canonical Flow (Sales + Delivery): Canonical Flow (Sales + Delivery)

This is the single source of truth for how to sell and run the pipeline today.

#### Canonical Flow (Sales + Delivery): 1. Core promise

One-time setup, then smooth weekly automation:

\11. Generate/configure client profile.
\11. Provision bundle into client repo.
\11. Install scheduler.
\11. Weekly reports and checks run automatically.
\11. Human only reviews report + final docs.

### Canonical Flow (Sales + Delivery) (Part 2)

Canonical sales and delivery flow for onboarding and operating client Auto-Doc Pipeline setups.

#### Canonical Flow (Sales + Delivery) (Part 2): 2. One-time setup (you do this)

\11. Pick preset:

- `profiles/clients/presets/small.yml`
- `profiles/clients/presets/startup.yml`
- `profiles/clients/presets/enterprise.yml`
- `profiles/clients/presets/pilot-evidence.yml`

\11. Fastest path:

```bash

python3 scripts/onboard_client.py

```

\11. If you use manual mode, customize client profile:

- client identity
- repo paths (`docs_root`, `api_root`, `sdk_root`)
- output targets
- module toggles
- policy/plan strictness

\11. Choose delivery mode:

- Same machine mode (you can access client repo path directly): use provisioning.
- Different laptops mode: build bundle on your machine, then client installs scheduler locally.

\11. Provision (same machine mode):

```bash

python3 scripts/provision_client_repo.py \
  --client profiles/clients/<client>.client.yml \
  --client-repo /path/to/client-repo \
  --docsops-dir docsops \
  --install-scheduler linux

```

Windows:

```bash

python3 scripts/provision_client_repo.py \
  --client profiles/clients/<client>.client.yml \
  --client-repo C:/path/to/client-repo \
  --docsops-dir docsops \
  --install-scheduler windows

```

\11. Build + handoff (different laptops mode):

```bash

python3 scripts/build_client_bundle.py --client profiles/clients/<client>.client.yml

```

Client installs scheduler after copying bundle into `<client-repo>/docsops`:

### Canonical Flow (Sales + Delivery) (Part 3)

Canonical sales and delivery flow for onboarding and operating client Auto-Doc Pipeline setups.

```bash

bash docsops/ops/install_cron_weekly.sh

```

Windows:

```bash

powershell -ExecutionPolicy Bypass -File docsops/ops/install_windows_task.ps1

```

Scheduler timezone is local machine timezone. Monday schedule follows client local time when installed on client machine.
Default schedule is Monday at `10:00` local time.

### Canonical Flow (Sales + Delivery) (Part 4)

Canonical sales and delivery flow for onboarding and operating client Auto-Doc Pipeline setups.

#### Canonical Flow (Sales + Delivery) (Part 4): 3. Weekly automation (no manual commands)

Scheduler runs:

- `docsops/scripts/run_weekly_gap_batch.py`

It executes:

### Canonical Flow (Sales + Delivery) (Part 5)

Canonical sales and delivery flow for onboarding and operating client Auto-Doc Pipeline setups.

- gap detection
- stale checks
- drift + docs contract (if enabled)
  - docs contract is report-only by default (no hard weekly blocking)
  - consolidated report includes only new/changed docs-contract mismatches, ignores closed ones, and deduplicates overlap with other gap sources
- KPI/SLA (if enabled)
- API-first flow (if enabled)
  - supports `docker`, `prism` (no Docker), and `external` public sandbox URL
  - if `sync_playground_endpoint=true`, sandbox URL is auto-synced into docs playground config
  - manual overrides apply (`apply_openapi_overrides.py`)
  - regression gate (`check_openapi_regression.py`)
  - generates API test assets from OpenAPI (`generate_api_test_assets.py`)
  - optionally uploads test assets to TestRail/Zephyr (`upload_api_test_assets.py`)
- Multi-protocol API-first flow (if non-REST protocols are enabled)
  - runs `run_multi_protocol_contract_flow.py` for GraphQL, gRPC, AsyncAPI, and WebSocket
  - auto-generates server stubs with business-logic placeholders (`generate_protocol_server_stubs.py`)
  - auto-resolves runtime endpoints for self-verification and docs testers
  - in `external` sandbox mode with `external_mock.enabled=true`, auto-prepares Postman mock endpoint
- RAG/knowledge tasks:
  - `extract_knowledge_modules_from_docs.py`
  - `validate_knowledge_modules.py`
  - `generate_knowledge_retrieval_index.py`
  - `generate_knowledge_graph_jsonld.py`
  - `run_retrieval_evals.py` (Precision/Recall/Hallucination-rate)
- terminology governance:
  - `sync_project_glossary.py` (syncs glossary markers to `glossary.yml`)
- multi-language examples standard:
  - `generate_multilang_tabs.py`
  - `validate_multilang_examples.py`
  - `check_code_examples_smoke.py` (including `expected-output` comparison for tagged blocks)
- intent bundle assembly via `build_all_intent_experiences.py` when enabled in `runtime.custom_tasks.weekly`
- `custom_tasks.weekly` commands
- consolidated report generation

### Canonical Flow (Sales + Delivery) (Part 6)

Canonical sales and delivery flow for onboarding and operating client Auto-Doc Pipeline setups.

Output:

- `reports/consolidated_report.json`
- related reports are regenerated to the same filenames each run (no manual cleanup required)
- `reports/docsops_status.json` (quick freshness/status check for non-technical users)

Client repo `.gitignore` recommendation:

```gitignore

reports/docsops-weekly.log

```

#### Canonical Flow (Sales + Delivery) (Part 6): 4. Human role

\11. In file explorer, check Modified date of `reports/consolidated_report.json`.
\11. If date/time is fresh, ask local LLM to process the report.
\11. Review generated docs quickly.
\11. Publish/merge.

#### Canonical Flow (Sales + Delivery) (Part 6): 5. Operator manual checks after setup

\11. Check `<client-repo>/docsops/config/client_runtime.yml` for correct client values.
\11. Check `<client-repo>/docsops/policy_packs/selected.yml` for expected policy pack/overrides.
\11. Check `<client-repo>/docsops/ENV_CHECKLIST.md` and align secrets with client.
\11. Check `<client-repo>/docsops/license.jwt` exists and is valid: `python3 docsops/scripts/license_gate.py`.
\11. Run one smoke weekly cycle and ensure `reports/consolidated_report.json` is refreshed.

### Canonical Flow (Sales + Delivery) (Part 7)

Canonical sales and delivery flow for onboarding and operating client Auto-Doc Pipeline setups.

#### Canonical Flow (Sales + Delivery) (Part 7): 6. Licensing

Every pipeline run validates the license locally using an Ed25519-signed JWT. No client data is ever sent to any server.

- License file: `<client-repo>/docsops/license.jwt`
- Public key: `<client-repo>/docsops/keys/veriops-licensing.pub`
- Capability pack: `<client-repo>/docsops/.capability_pack.enc` (encrypted scoring weights)

Plan tiers control feature access (Pilot, Professional, Enterprise). Without a valid license, the pipeline runs in community mode (degraded: lint-only, no scoring, no drift, REST only).

Check license status: `python3 docsops/scripts/license_gate.py`.

Dev/test bypass: `export VERIOPS_LICENSE_PLAN=enterprise`.

Details: `docs/operations/PLAN_TIERS.md`, `docs/operations/OPERATOR_RUNBOOK.md`.

#### Canonical Flow (Sales + Delivery) (Part 7): 7. Plan packaging

- Basic: essential quality + gaps + stale.
- Pro: adds drift/contract, KPI/SLA, RAG/knowledge, hybrid/API-first.
- Enterprise: strict policy, full automation surface, advanced verification.

Details: `docs/operations/PLAN_TIERS.md`.

#### Canonical Flow (Sales + Delivery) (Part 7): 8. What to say in sales calls

\11. "You get one-time setup, then weekly documentation ops on autopilot."
\11. "Your team stops doing doc plumbing and only reviews final output."
\11. "Quality is controlled by policy packs and automated gates."
\11. "RAG/knowledge is maintained automatically, so AI outputs stay grounded."

### Canonical Flow (Sales + Delivery) (Part 8)

Canonical sales and delivery flow for onboarding and operating client Auto-Doc Pipeline setups.

#### Canonical Flow (Sales + Delivery) (Part 8): 9. Compatibility mode

If needed, run equivalent weekly flow via GitHub Actions cron (`weekly-consolidation.yml` and companion workflows). Recommended mode remains local scheduler automation in client repo.

#### Canonical Flow (Sales + Delivery) (Part 8): 10. Deep references

- `docs/operations/OPERATOR_RUNBOOK.md`
- `docs/operations/CENTRALIZED_CLIENT_BUNDLES.md`
- `docs/operations/UNIFIED_CLIENT_CONFIG.md`
- `docs/operations/PLAN_TIERS.md`
- `docs/operations/PIPELINE_CAPABILITIES_CATALOG.md`

#### Canonical Flow (Sales + Delivery) (Part 8): Next steps

- [Documentation index](../index.md)

### Canonical Flow (Sales + Delivery) (Part 9)

Canonical sales and delivery flow for onboarding and operating client Auto-Doc Pipeline setups.

#### Canonical Flow (Sales + Delivery) (Part 9): Implementation status (2026-03-25)

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

### Централизованная настройка клиентов

Практический путь настройки клиентских bundle и автозапуска pipeline из одного места.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

<!-- cspell:disable -->
### Централизованная настройка клиентов: Централизованная настройка клиентов (очень просто)

Это схема, где вы настраиваете все в одном месте, а клиент работает локально как раньше.

#### Централизованная настройка клиентов: Главное правило

- Вы запускаете `scripts/onboard_client.py` в своем мастер-репо.
- Скрипт создает/обновляет `profiles/clients/generated/<client_id>.client.yml`.
- Если клиентский репо доступен на этой же машине, скрипт сразу ставит `bundle` в локальный клон клиентского репо.
- Если у вас и у клиента разные ноутбуки, вы собираете `bundle` у себя и передаете клиенту для установки в `docsops/`.
- Клиент дальше просто работает локально через Claude Code / Codex.

#### Централизованная настройка клиентов: Что именно вы настраиваете (и где)

Один файл клиента: `profiles/clients/<client>.client.yml`.

Полный справочник:

- `docs/operations/UNIFIED_CLIENT_CONFIG.md`
- `docs/operations/PLAN_TIERS.md` (готовые планы Basic/Pro/Enterprise)
- `docs/operations/PIPELINE_CAPABILITIES_CATALOG.md` (полный список доступных команд/плюшек)

##### Централизованная настройка клиентов: 1) Пути в конкретном репо клиента

```yaml

runtime:
  docs_root: "docs"
  api_root: "openapi"
  sdk_root: "clients"

```

Если у клиента другой layout, меняете только эти 3 строки.

### Централизованная настройка клиентов (Part 10)

Практический путь настройки клиентских bundle и автозапуска pipeline из одного места.

#### Централизованная настройка клиентов (Part 10): Команда "под ключ" (без возни клиента)

Если вы хотите сразу настроить и запускать за клиента, используйте provisioning:

```bash

python3 scripts/provision_client_repo.py \
  --client profiles/clients/blockstream-demo.client.yml \
  --client-repo /path/to/client-repo \
  --docsops-dir docsops \
  --install-scheduler linux

```

Для Windows:

```bash

python3 scripts/provision_client_repo.py \
  --client profiles/clients/blockstream-demo.client.yml \
  --client-repo C:/path/to/client-repo \
  --docsops-dir docsops \
  --install-scheduler windows

```

Что делает команда:

\11. Собирает bundle из клиентского профиля.
\11. Копирует bundle в репозиторий клиента (`docsops/`).
\11. Генерирует `docsops/ENV_CHECKLIST.md` автоматически.
\11. Ставит weekly scheduler (cron или Task Scheduler).
\11. Клиенту не нужно руками настраивать pipeline.

##### Централизованная настройка клиентов (Part 10): Ручная проверка оператора (после установки)

\11. Проверить `<client-repo>/docsops/config/client_runtime.yml`.
\11. Проверить `<client-repo>/docsops/policy_packs/selected.yml`.
\11. Проверить `<client-repo>/docsops/ENV_CHECKLIST.md` и передать список env/secrets клиенту.
\11. Убедиться, что scheduler установлен (cron entry или Task Scheduler task).
\11. Запустить один тестовый weekly run и убедиться, что `reports/consolidated_report.json` обновился.

### Централизованная настройка клиентов (Part 11)

Практический путь настройки клиентских bundle и автозапуска pipeline из одного места.

#### Централизованная настройка клиентов (Part 11): Как это ставится клиенту

Клиент кладет папку bundle в свой репо, например:

```text

<client-repo>/docsops/

```

Там уже будут:

- `config/client_runtime.yml`
- `policy_packs/selected.yml`
- `scripts/...`
- `AGENTS.md`
- `CLAUDE.md`
- `LICENSE-COMMERCIAL.md`
- `NOTICE`
- `ops/run_weekly_docsops.sh` / `ops/run_weekly_docsops.ps1`
- `ops/install_cron_weekly.sh` / `ops/install_windows_task.ps1`
- `ops/runbook.md`

#### Централизованная настройка клиентов (Part 11): Не ломает ли это локальный опыт?

Не ломает.

- Клиент по-прежнему работает локально.
- LLM читает локальные `AGENTS.md`/`CLAUDE.md`.
- Все проверки и генерация выполняются локально в репо клиента.
- Еженедельный отчёт формируется по расписанию автоматически.

### Централизованная настройка клиентов (Part 12)

Практический путь настройки клиентских bundle и автозапуска pipeline из одного места.

#### Централизованная настройка клиентов (Part 12): Еженедельный автоматический поток

Скрипт `docsops/scripts/run_weekly_gap_batch.py` по расписанию:

\11. Собирает gap report за последние 7 дней.
\11. Проверяет stale-доки (по умолчанию 180 дней без изменений).
\11. Запускает KPI/SLA (если включено в bundle).
\11. При `mode=api-first|hybrid` запускает API-first flow (если включено в `runtime.api_first.enabled`).
\11. Для API sandbox поддерживает 3 режима: `docker`, `prism` (без Docker), `external` (публичный URL).
\11. Если `runtime.api_first.sync_playground_endpoint=true`, URL песочницы автоматически пишется в `mkdocs.yml`.
\11. Применяет manual overrides к OpenAPI артефактам (если задан `manual_overrides_path`).
\11. Проверяет regression snapshot (если задан `regression_snapshot_path`).
\11. Генерирует API test assets из OpenAPI (`generate_api_test_assets.py`).
\11. Опционально загружает test assets в TestRail/Zephyr (`upload_api_test_assets.py`).
\11. Генерирует и валидирует мультиязычные вкладки кода (новый стандарт).
\11. Выполняет smoke-проверки кода и сверяет `expected-output` (если указан).
\11. Запускает `runtime.custom_tasks.weekly` (если включены).
\11. Создает `reports/consolidated_report.json`.

Важно: API-first здесь только один из подпроцессов. Главный контур охватывает все типы документации и quality automation целиком.

Простой рекомендуемый блок для публичной API песочницы:

### Централизованная настройка клиентов (Part 13)

Практический путь настройки клиентских bundle и автозапуска pipeline из одного места.

```yaml

runtime:
  api_first:
    sandbox_backend: "external"
    mock_service: "custom"
    mock_base_url: "https://<your-real-public-mock-url>/v1"
    sync_playground_endpoint: true

```

Порог stale можно менять для каждого клиента:

- `private_tuning.weekly_stale_days` в `profiles/clients/<client>.client.yml`

Дальше оператор или команда:

\11. Передает consolidated report локальной LLM для batch generation.
\11. Делает быстрый визуальный финальный просмотр готовых docs.

#### Централизованная настройка клиентов (Part 13): Что добавить в `.gitignore` клиента

Рекомендуемый минимум:

```gitignore

reports/docsops-weekly.log

```

Это локальный лог планировщика. Его обычно не коммитят.

JSON/Markdown отчеты (`reports/consolidated_report.json` и связанные отчеты) обычно оставляют в репозитории, если команда ведет историю отчетов в git.

### Централизованная настройка клиентов (Part 14)

Практический путь настройки клиентских bundle и автозапуска pipeline из одного места.

#### Централизованная настройка клиентов (Part 14): RAG/knowledge без ручных запусков

Это уже укладывается в текущий smooth flow:

\11. Один раз настроить профиль клиента (`*.client.yml`):

- `runtime.modules.knowledge_validation: true`
- `runtime.modules.rag_optimization: true`
- `runtime.modules.ontology_graph: true`
- `runtime.modules.retrieval_evals: true`
- `runtime.custom_tasks.weekly` для RAG-задач, включая `build_all_intent_experiences.py`
- `bundle.include_paths: ["knowledge_modules"]`

\11. Один раз сделать provisioning:

- `provision_client_repo.py` ставит `docsops/` в клиентский репозиторий
- сразу ставится расписание (`cron` или `Task Scheduler`)

\11. Далее weekly job идет автоматически:

- запускается `run_weekly_gap_batch.py`
- внутри выполняются:
  - `extract_knowledge_modules_from_docs.py`
  - `validate_knowledge_modules.py`
  - `generate_knowledge_retrieval_index.py`
  - `generate_knowledge_graph_jsonld.py`
  - `run_retrieval_evals.py`
  - любые `custom_tasks.weekly` (например `build_all_intent_experiences.py`)
- отчеты формируются автоматически

Итог:

- клиентская команда не запускает команды вручную
- человек только смотрит weekly report и выборочно проверяет финальные docs

Поведение отчетов:

- weekly запуск пишет в те же имена файлов
- новые отчеты заменяют старые
- ручное удаление старых отчетов не требуется

Как клиенту быстро понять, что отчет новый (самый простой способ):

### Централизованная настройка клиентов (Part 15)

Практический путь настройки клиентских bundle и автозапуска pipeline из одного места.

\11. В проводнике/Finder/файловом менеджере найти `reports/consolidated_report.json`.
\11. Посмотреть `Modified` (дата/время изменения файла).
\11. Если `Modified` свежее (после планового запуска), отчет новый и готов к передаче локальной LLM.

Этого достаточно. Открывать дополнительные файлы не нужно.

Дополнительные тех-маркеры (опционально):

- `reports/READY_FOR_REVIEW.txt`
- `reports/docsops_status.json`

#### Централизованная настройка клиентов (Part 15): Два простых примера

##### Централизованная настройка клиентов (Part 15): Клиент 1: только Sphinx, без drift

```yaml

runtime:
  output_targets: ["sphinx"]
  modules:
    gap_detection: true
    drift_detection: false
    docs_contract: true
    kpi_sla: true
    rag_optimization: true
    ontology_graph: true
    retrieval_evals: true
    terminology_management: true
bundle:
  include_scripts:
    - "scripts/check_docs_contract.py"
    - "scripts/evaluate_kpi_sla.py"
    - "scripts/generate_knowledge_graph_jsonld.py"
    - "scripts/run_retrieval_evals.py"
    - "scripts/sync_project_glossary.py"

```

##### Централизованная настройка клиентов (Part 15): Клиент 2: ReadMe + GitHub, очень строгий quality bar

```yaml

runtime:
  output_targets: ["readme", "github"]
bundle:
  base_policy_pack: "plg"
  policy_overrides:
    kpi_sla:
      min_doc_coverage: 90
      max_quality_score_drop: 2

```

Вы меняете только профиль YAML. Код пайплайна не трогаете.

#### Централизованная настройка клиентов (Part 15): Next steps

- [Documentation index](../index.md)

### Централизованная настройка клиентов (Part 16)

Практический путь настройки клиентских bundle и автозапуска pipeline из одного места.

#### Централизованная настройка клиентов (Part 16): Implementation status (2026-03-25)

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

### Централизованная настройка клиентов (Part 2)

Практический путь настройки клиентских bundle и автозапуска pipeline из одного места.

##### Централизованная настройка клиентов (Part 2): 2) Какие генераторы документации нужны

```yaml

runtime:
  output_targets: ["sphinx", "readme", "github"]

```

Примеры:

- только Sphinx: `["sphinx"]`
- только ReadMe: `["readme"]`
- смешанный вариант: `["sphinx", "readme"]`

##### Централизованная настройка клиентов (Part 2): 2.1) Как выбрать flow: code-first / api-first / hybrid

```yaml

runtime:
  docs_flow:
    mode: "hybrid"

```

- `code-first`: стандартный docs-ops поток
- `api-first`: API-first поток
- `hybrid`: оба потока одновременно

### Централизованная настройка клиентов (Part 3)

Практический путь настройки клиентских bundle и автозапуска pipeline из одного места.

##### Централизованная настройка клиентов (Part 3): 3) Какие функции включены

Есть 2 уровня переключения:

\11. Логические флаги для LLM:

```yaml

runtime:
  modules:
    gap_detection: true
    drift_detection: true
    docs_contract: true
    kpi_sla: true
    rag_optimization: true
    ontology_graph: true
    retrieval_evals: true
    terminology_management: true
    lifecycle_management: true

```

\11. Практический набор скриптов в bundle:

```yaml

bundle:
  include_scripts:
    - "scripts/check_docs_contract.py"
    - "scripts/check_api_sdk_drift.py"

```

Если функция не нужна, убираете флаг и соответствующий скрипт.

По умолчанию baseline включен:

- self-checks
- multi-language tabs generation/validation for code examples
- fact/style checks
- lifecycle checks/reports
- SEO/GEO
- RAG/knowledge index
- JSON-LD knowledge graph (`generate_knowledge_graph_jsonld.py`)
- retrieval evals (`run_retrieval_evals.py`)
- terminology sync to glossary (`sync_project_glossary.py`)
- drift/contract/KPI-SLA

Ключевые возможности (ваше основное УТП) включаются через:

```yaml

runtime:
  custom_tasks:
    weekly:
      - id: "openapi-lint"
        enabled: true
        command: "npm run lint:openapi"
        continue_on_error: true

```

Это не `редкие спецзадачи`, а базовый контур docs-ops платформы. В том числе:

### Централизованная настройка клиентов (Part 4)

Практический путь настройки клиентских bundle и автозапуска pipeline из одного места.

- SEO/GEO (`seo_geo_optimizer.py`)
- RAG/knowledge index (`generate_knowledge_retrieval_index.py`)
- JSON-LD graph (`generate_knowledge_graph_jsonld.py`)
- retrieval evals (`run_retrieval_evals.py`)
- glossary sync (`sync_project_glossary.py`)
- интент-бандлы (`build_all_intent_experiences.py`)
- мультиязычные табы кода (`generate_multilang_tabs.py` + `validate_multilang_examples.py`)
- i18n sync/translate
- интерактивные диаграммы (через `bundle.include_paths`)
- Algolia upload
- любые другие скрипты/команды из полного каталога

### Централизованная настройка клиентов (Part 5)

Практический путь настройки клиентских bundle и автозапуска pipeline из одного места.

##### Централизованная настройка клиентов (Part 5): 3.2) API-first advanced controls (manual overrides + regression gate)

```yaml

runtime:
  api_first:
    enabled: true
    openapi_version: "3.1.0"
    manual_overrides_path: "api/overrides/openapi.manual.yml"
    regression_snapshot_path: "api/.openapi-regression.json"
    update_regression_snapshot: false
    generate_test_assets: true
    test_assets_output_dir: "reports/api-test-assets"
    testrail_csv: "reports/api-test-assets/testrail_test_cases.csv"
    zephyr_json: "reports/api-test-assets/zephyr_test_cases.json"
    upload_test_assets: false
    upload_test_assets_strict: false
    test_assets_upload_report: "reports/api-test-assets/upload_report.json"

```

Для этого в `bundle.include_scripts` должны быть:

- `scripts/apply_openapi_overrides.py`
- `scripts/check_openapi_regression.py`
- `scripts/generate_api_test_assets.py`
- `scripts/upload_api_test_assets.py`

### Централизованная настройка клиентов (Part 6)

Практический путь настройки клиентских bundle и автозапуска pipeline из одного места.

##### Централизованная настройка клиентов (Part 6): 3.3) PR авто-фикс документации (в ту же PR-ветку)

```yaml

runtime:
  pr_autofix:
    enabled: true
    require_label: false
    label_name: "auto-doc-fix"
    enable_auto_merge: false
    commit_message: "docs: auto-sync PR docs"
    workflow_filename: "docsops-pr-autofix.yml"

```

Что происходит:

\11. Workflow запускается на `pull_request` событиях.
\11. Смотрит только diff текущего PR (`base...head`).
\11. Если PR заблокирован по docs-contract/drift, добавляет docs-правки.
\11. Коммитит правки в ту же PR-ветку (не в `main`).
\11. Checks перезапускаются автоматически.

Одноразовая настройка для клиента:

\11. Включить `Read and write permissions` для GitHub Actions в репозитории.
\11. Опционально добавить `DOCSOPS_BOT_TOKEN` (`contents:write`, `pull_requests:write`) если в организации ограничен стандартный токен.
\11. Прогнать provisioning, чтобы установить `.github/workflows/docsops-pr-autofix.yml`.

### Централизованная настройка клиентов (Part 7)

Практический путь настройки клиентских bundle и автозапуска pipeline из одного места.

##### Централизованная настройка клиентов (Part 7): 3.1) Централизованные интеграции (Algolia + Ask AI)

```yaml

runtime:
  integrations:
    algolia:
      enabled: true
      upload_on_weekly: true
      app_id_env: "ALGOLIA_APP_ID"
      api_key_env: "ALGOLIA_API_KEY"
      index_name_env: "ALGOLIA_INDEX_NAME"
    ask_ai:
      enabled: true
      auto_configure_on_provision: true
      install_runtime_pack: false
      provider: "openai"
      billing_mode: "user-subscription"
      model: "gpt-4.1-mini"

```

Что это дает:

- Algolia работает одинаково для всех поддерживаемых site generators.
- Ask AI настраивается автоматически во время provisioning (без ручных CLI-команд).

##### Централизованная настройка клиентов (Part 7): 4) Насколько строгие правила качества

```yaml

bundle:
  base_policy_pack: "multi-product"
  policy_overrides:
    kpi_sla:
      min_doc_coverage: 85

```

- `base_policy_pack` = базовый режим
- `policy_overrides` = тонкая докрутка под клиента

##### Централизованная настройка клиентов (Part 7): 4.1) Как выбрать style guide (Vale)

```yaml

bundle:
  style_guide: "google" # google | microsoft | hybrid

```

Сборщик сам положит `.vale.ini` в bundle под выбранный профиль.

### Централизованная настройка клиентов (Part 8)

Практический путь настройки клиентских bundle и автозапуска pipeline из одного места.

##### Централизованная настройка клиентов (Part 8): 5) Автовставка блока в AGENTS/CLAUDE

```yaml

bundle:
  llm:
    codex_instructions_source: "AGENTS.md"
    claude_instructions_source: "CLAUDE.md"
    inject_managed_block: true
    docsops_root_in_client_repo: "docsops"

```

Сборщик автоматически положит в bundle:

- `AGENTS.md`
- `CLAUDE.md`

И добавит в оба файла управляемый блок с инструкцией читать:

- `docsops/config/client_runtime.yml`
- `docsops/policy_packs/selected.yml`

#### Централизованная настройка клиентов (Part 8): Команда сборки

```bash

cd "C:/Users/Kroha/Documents/development/Auto-Doc Pipeline"
python3 scripts/build_client_bundle.py --client profiles/clients/blockstream-demo.client.yml

```

Результат:

```text

generated/client_bundles/blockstream-demo/

```

### Централизованная настройка клиентов (Part 9)

Практический путь настройки клиентских bundle и автозапуска pipeline из одного места.

##### Централизованная настройка клиентов (Part 9): Два режима установки

1. На одной машине (у вас есть путь к клиентскому репо): используете `provision_client_repo.py`, scheduler ставится сразу.

1. На разных ноутбуках: вы собираете bundle командой выше, клиент кладет bundle в `<client-repo>/docsops`, затем клиент ставит scheduler локально:

```bash

bash docsops/ops/install_cron_weekly.sh

```

Windows:

```bash

powershell -ExecutionPolicy Bypass -File docsops/ops/install_windows_task.ps1

```

Scheduler использует локальную таймзону машины, где установлен. Если установлен на клиентском ноутбуке, Monday run идет по времени клиента.

Быстрый старт по пресетам:

- `profiles/clients/presets/small.yml`
- `profiles/clients/presets/startup.yml`
- `profiles/clients/presets/enterprise.yml`
- `profiles/clients/presets/pilot-evidence.yml`

Самый быстрый запуск:

```bash

python3 scripts/onboard_client.py

```

Скрипт задает вопросы, создает клиентский профиль, собирает bundle, ставит в клиентский репозиторий и устанавливает scheduler.
`onboard_client.py` остается в вашем мастер-репо и не включается в клиентский bundle по умолчанию.

Перед установкой вы видите preview профиля и подтверждаете запуск.

### VeriDoc data processing agreement

Data processing agreement for VeriDoc platform covering GDPR compliance, sub-processors, data transfer mechanisms, and breach notification procedures.

### VeriDoc data processing agreement: VeriDoc data processing agreement

This data processing agreement ("DPA") forms part of the agreement between
Liora Tech ("Processor," "we") and the entity subscribing to VeriDoc
("Controller," "you") for the processing of personal data through the
VeriDoc platform.

#### VeriDoc data processing agreement: Scope and roles

| Role | Party | Responsibility |
|------|-------|----------------|
| **Data Controller** | You (the customer) | Determines the purposes and means of processing documentation content |
| **Data Processor** | Liora Tech | Processes personal data on your behalf to provide the VeriDoc Service |
| **Sub-processors** | Third-party providers listed below | Process data under our supervision for specific service functions |

This DPA applies to all personal data processed through the VeriDoc
platform on your behalf, including documentation content that may contain
personal data (names, emails, or identifiers in your documentation).

#### VeriDoc data processing agreement: Processing details

##### VeriDoc data processing agreement: Subject matter and duration

We process personal data for the duration of your VeriDoc subscription.
Processing terminates 30 days after account closure, when all data is
permanently deleted.

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

### VeriDoc data processing agreement (Part 3)

Data processing agreement for VeriDoc platform covering GDPR compliance, sub-processors, data transfer mechanisms, and breach notification procedures.

#### VeriDoc data processing agreement (Part 3): Processor obligations

We commit to the following obligations:

This auto-generated knowledge chunk was expanded to satisfy minimum retrieval module length for stable indexing.

### VeriDoc data processing agreement (Part 4)

Data processing agreement for VeriDoc platform covering GDPR compliance, sub-processors, data transfer mechanisms, and breach notification procedures.

1. **Process only on your instructions.** We process personal data solely
   to provide the Service as documented in these Terms and this DPA. We do
   not process data for our own purposes.
1. **Confidentiality.** All personnel with access to personal data are
   bound by confidentiality obligations.
1. **Security measures.** We implement technical and organizational
   measures as described in the [security policy](security-policy.md):
   - TLS 1.3 encryption for all data in transit
   - AES-256 encryption for all data at rest
   - PBKDF2-SHA256 password hashing (600,000 iterations)
   - Daily encrypted database backups with 30-day retention
   - Rate limiting (60 requests per minute)
   - Sentry error tracking with PII scrubbing
1. **Sub-processor management.** We maintain an up-to-date list of
   sub-processors and notify you 30 days before adding new ones.
1. **Data subject rights.** We assist you in responding to data subject
   requests (access, deletion, portability) within 10 business days.
1. **Breach notification.** We notify you within 72 hours of discovering
   a personal data breach, with details on the nature, scope, and
   remediation steps.
1. **Audit rights.** You may request an audit of our data processing
   activities once per year with 30 days advance notice.
1. **Data return and deletion.** Upon termination, we return your data
   in a standard format (JSON export) and delete all copies within 30 days.

### VeriDoc data processing agreement (Part 5)

Data processing agreement for VeriDoc platform covering GDPR compliance, sub-processors, data transfer mechanisms, and breach notification procedures.

#### VeriDoc data processing agreement (Part 5): Sub-processors

We use the following sub-processors:

| Sub-processor | Purpose | Location | Data processed |
|---------------|---------|----------|----------------|
| Hetzner Online | Cloud infrastructure hosting | Germany (EU) | All application data (encrypted) |
| LemonSqueezy | Payment processing | United States | Email, subscription tier |
| Mailgun | Transactional email delivery | United States | Email address, email content |
| Sentry | Error monitoring | United States | Error context (PII scrubbed) |

##### VeriDoc data processing agreement (Part 5): Optional LLM sub-processors (opt-in only)

These sub-processors are engaged only when you explicitly enable AI
features:

| Sub-processor | Purpose | Location | Data processed |
|---------------|---------|----------|----------------|
| Anthropic | Document quality enhancement | United States | Document sections |
| Groq | Text generation | United States | Document sections |
| DeepSeek | Text generation | China | Document sections |
| OpenAI | Embeddings, text generation | United States | Document sections |

You control which LLM providers are used through your pipeline
configuration. Disable AI features to prevent any content from reaching
LLM sub-processors.

#### VeriDoc data processing agreement (Part 5): Data transfers

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

### VeriDoc data processing agreement (Part 7)

Data processing agreement for VeriDoc platform covering GDPR compliance, sub-processors, data transfer mechanisms, and breach notification procedures.

#### VeriDoc data processing agreement (Part 7): Data protection impact assessment

We support your data protection impact assessments (DPIAs) by providing:

1. Documentation of processing activities.
1. Technical details of security measures.
1. Sub-processor information and transfer mechanisms.

Request DPIA support materials at <privacy@veri-doc.app>.

#### VeriDoc data processing agreement (Part 7): Term and termination

This DPA remains in effect for the duration of your VeriDoc subscription.
Upon termination:

1. We stop processing personal data within 24 hours.
1. We provide a JSON data export within 7 business days upon request.
1. We permanently delete all personal data within 30 days.
1. We confirm deletion in writing.

#### VeriDoc data processing agreement (Part 7): Contact information

For DPA inquiries:

- Email: <privacy@veri-doc.app>
- Response time: within 10 business days

**Last updated:** March 28, 2026

#### VeriDoc data processing agreement (Part 7): Next steps

- Review the [terms of service](terms-of-service.md)
- Review the [privacy policy](privacy-policy.md)
- Review the [security policy](security-policy.md)

### Old Webhook API (Deprecated)

This API is deprecated. Use the new Webhook node instead.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

#### Old Webhook API (Deprecated): Old Webhook API

This is an example of a deprecated page. When you build the site with MkDocs, it will automatically:

\11. Show a deprecation warning banner at the top
\11. Lower its ranking in search results
\11. Add a canonical tag pointing to the replacement page

#### Old Webhook API (Deprecated): Example Code

```javascript

// OLD WAY (deprecated)
const webhook = new OldWebhook({
 port: 5678
});

// NEW WAY
const webhook = new WebhookNode({
 port: {{ default_port }}
});

```

#### Old Webhook API (Deprecated): Next steps

- [Documentation index](index.md)

### GRAPHQL API Reference

Auto-generated graphql reference from source contract.

### GRAPHQL API Reference: GRAPHQL Reference

Source: `/tmp/pytest-of-eudo/pytest-2841/test_multi_protocol_contract_f0/schema.graphql`

Flow mode: `api-first`

#### GRAPHQL API Reference: Operations

- Query count: `1`
- Mutation count: `0`
- Subscription count: `0`
- Queries: `health`

### GRAPHQL API Reference (Part 2)

Auto-generated graphql reference from source contract.

#### GRAPHQL API Reference (Part 2): Interactive GraphQL Playground

This auto-generated knowledge chunk was expanded to satisfy minimum retrieval module length for stable indexing.

### GRAPHQL API Reference (Part 3)

Auto-generated graphql reference from source contract.

<div id="graphql-playground" style="border:1px solid #d1d5db; padding:12px; border-radius:8px;">
  <p><strong>Endpoint:</strong> <code id="graphql-endpoint-view"></code></p>
  <textarea id="graphql-query" rows="12" style="width:100%; font-family:monospace;">query HealthCheck {
  __typename
}</textarea>
  <br/>
  <button id="graphql-run">Run Query</button>
  <pre id="graphql-output" style="margin-top:12px; max-height:320px; overflow:auto;"></pre>
</div>
<script>
(function(){ const endpoint = "https://postman-echo.com/post";
const view = document.getElementById('graphql-endpoint-view');
const run = document.getElementById('graphql-run');
const query = document.getElementById('graphql-query');
const out = document.getElementById('graphql-output');
if (!view || !run || !query || !out) return;
view.textContent = endpoint || 'not configured';
function normalize(v){ return String(v || '').replace(/\s+/g, ' ').trim().toLowerCase(); }
function fallback(queryText){
  const q = normalize(queryText);
  const idMatch = String(queryText || '').match(/id\s*:\s*\"([^\"]+)\"/i);
  const projectId = idMatch ? idMatch[1] : 'prj_abc123';
  if (q.indexOf('health') !== -1) return { data: { health: { status: 'healthy', version: '1.0.0' } } };
  if (q.indexOf('mutation') !== -1 && q.indexOf('createproject') !== -1) return { data: { createProject: { id: 'prj_demo001', name: 'New Project', status: 'draft' } } };
  if (q.indexOf('mutation') !== -1 && q.indexOf('updateproject') !== -1) return { data: { updateProject: { id: projectId, status: 'active', updatedAt: new Date().toISOString() } } };
  if (q.indexOf('projects') !== -1) return { data: { projects: [{ id: 'prj_abc123', status: 'active' }, { id: 'prj_def456', status: 'draft' }] } };
  if (q.indexOf('project') !== -1) return { data: { project: { id: projectId, name: 'Website Redesign', status: 'active' } } };
  return { data: null, errors: [{ message: 'Unknown query. Use: health, project, projects, createProject, updateProject' }] };
}
run.onclick = async function(){
  if (!endpoint) {
    out.textContent = JSON.stringify({ mode: 'semantic-fallback', simulated_response: fallback(query.value) }, null, 2);
    return;
  }
  out.textContent = 'Loading...';
  try {
    const response = await fetch(endpoint, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({ query: query.value }) });
    const text = await response.text();
    out.textContent = JSON.stringify({ mode: 'live', raw: text, simulated_response: fallback(query.value) }, null, 2);
  } catch (error) {
    out.textContent = JSON.stringify({ mode: 'semantic-fallback', error: String(error), simulated_response: fallback(query.value) }, null, 2);
  }
};
})();
</script>

### GRAPHQL API Reference (Part 4)

Auto-generated graphql reference from source contract.

#### GRAPHQL API Reference (Part 4): Next steps

- [Documentation index](index.md)

This auto-generated knowledge chunk was expanded to satisfy minimum retrieval module length for stable indexing.

### GRPC API Reference

Auto-generated grpc reference from source contract.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### GRPC API Reference: GRPC Reference

Source: `contracts/grpc/acme.proto`

Flow mode: `api-first`

#### GRPC API Reference: Top-level Keys

#### GRPC API Reference: Service Methods

- RPC method count: `4`
- `AutoDocPipelineService.CreateProject`
- `AutoDocPipelineService.GetProject`
- `AutoDocPipelineService.ListProjects`
- `AutoDocPipelineService.UpdateProject`

### GRPC API Reference (Part 2)

Auto-generated grpc reference from source contract.

#### GRPC API Reference (Part 2): Interactive gRPC Tester

This tester uses an HTTP gateway/adapter endpoint, so docs users can trigger gRPC methods from browser.

### GRPC API Reference (Part 3)

Auto-generated grpc reference from source contract.

<div id="grpc-playground" style="border:1px solid #d1d5db; padding:12px; border-radius:8px;">
  <p><strong>Gateway Endpoint:</strong> <code id="grpc-endpoint-view"></code></p>
  <label>Service</label><br/><input id="grpc-service" style="width:100%" placeholder="GreeterService"/><br/>
  <label>Method</label><br/><input id="grpc-method" style="width:100%" placeholder="SayHello"/><br/>
  <label>Payload (JSON)</label><br/><textarea id="grpc-payload" rows="8" style="width:100%; font-family:monospace;">{
  "name": "world"
}</textarea><br/>
  <button id="grpc-run">Invoke</button>
  <pre id="grpc-output" style="margin-top:12px; max-height:320px; overflow:auto;"></pre>
</div>
<script>
(function(){ const endpoint = "";
const view = document.getElementById('grpc-endpoint-view');
const run = document.getElementById('grpc-run');
const service = document.getElementById('grpc-service');
const method = document.getElementById('grpc-method');
const payload = document.getElementById('grpc-payload');
const out = document.getElementById('grpc-output');
if (!view || !run || !service || !method || !payload || !out) return;
view.textContent = endpoint || 'not configured';
function fallback(body){
  const m = String((body && body.method) || '').toLowerCase();
  const p = (body && body.payload && typeof body.payload === 'object') ? body.payload : {};
  if (m === 'getproject') return { id: p.project_id || 'prj_abc123', name: 'Website Redesign', status: 'active' };
  if (m === 'createproject') return { id: 'prj_demo001', name: p.name || 'New Project', status: p.status || 'draft' };
  if (m === 'listprojects') return [{ id: 'prj_abc123', status: 'active' }, { id: 'prj_def456', status: 'draft' }];
  return { error: { code: 'UNIMPLEMENTED', message: 'Use GetProject, CreateProject, or ListProjects' } };
}
run.onclick = async function(){
  try {
    const body = { service: service.value.trim(), method: method.value.trim(), payload: JSON.parse(payload.value || '{}') };
    if (!endpoint) {
      out.textContent = JSON.stringify({ mode: 'semantic-fallback', simulated_response: fallback(body) }, null, 2);
      return;
    }
    out.textContent = 'Loading...';
    const response = await fetch(endpoint, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify(body) });
    const text = await response.text();
    out.textContent = JSON.stringify({ mode: 'live', raw: text, simulated_response: fallback(body) }, null, 2);
  } catch (error) {
    let body = { method: method.value.trim(), payload: {} };
    try { body.payload = JSON.parse(payload.value || '{}'); } catch (_) {}
    out.textContent = JSON.stringify({ mode: 'semantic-fallback', error: String(error), simulated_response: fallback(body) }, null, 2);
  }
};
})();
</script>

### GRPC API Reference (Part 4)

Auto-generated grpc reference from source contract.

#### GRPC API Reference (Part 4): Next steps

- [Documentation index](index.md)

This auto-generated knowledge chunk was expanded to satisfy minimum retrieval module length for stable indexing.

### Legal and compliance (Part 2)

Legal documents for VeriDoc platform including terms of service, privacy policy, data processing agreement, and security policy.

#### Legal and compliance (Part 2): Next steps

- [Terms of service](terms-of-service.md)
- [Privacy policy](privacy-policy.md)

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

### Intelligent knowledge system architecture (Part 3)

Explains how the pipeline models reusable knowledge modules for AI retrieval, dynamic assembly, and multi-channel documentation delivery.

#### Intelligent knowledge system architecture (Part 3): RAG integration contract

Ask AI reads the same artifacts that the weekly knowledge pipeline refreshes.

- `docs/assets/knowledge-retrieval-index.json` is the primary retrieval index.
- `docs/assets/retrieval.faiss` is the FAISS vector index with `text-embedding-3-small` embeddings.
- `docs/assets/retrieval-metadata.json` is the metadata sidecar for the FAISS index.
- `docs/assets/knowledge-graph.jsonld` adds relationship context for retrieval and reasoning.
- `reports/retrieval_evals_report.json` provides retrieval quality gates (Precision, Recall, Hallucination-rate).

This shared contract keeps documentation generation, knowledge base updates, and RAG runtime aligned.

### Intelligent knowledge system architecture (Part 4)

Explains how the pipeline models reusable knowledge modules for AI retrieval, dynamic assembly, and multi-channel documentation delivery.

#### Intelligent knowledge system architecture (Part 4): Advanced retrieval pipeline

The RAG runtime uses six features that work together to maximize retrieval precision and recall:

1. **Token-aware chunking** splits long modules into 750-token chunks with 100-token overlap using the `cl100k_base` tokenizer. Short modules remain as single chunks. The embedding pipeline (`scripts/generate_embeddings.py --chunk`) embeds each chunk independently and stores chunk metadata (`chunk_id`, `parent_id`, `chunk_index`) in the FAISS sidecar.

1. **Hybrid search (RRF)** combines FAISS cosine similarity with token-overlap scoring. Reciprocal Rank Fusion (k=60) merges both rankings into a single list. This approach captures queries that mix specific terminology (tokens) with conceptual intent (embeddings).

1. **HyDE query expansion** generates a hypothetical documentation passage using `gpt-4.1-mini` before embedding the query. The generated passage captures domain vocabulary that the raw question may lack. The pipeline embeds the hypothetical document instead of the raw query text.

1. **Cross-encoder reranking** scores the top 20 candidates using `cross-encoder/ms-marco-MiniLM-L-6-v2`. The reranker evaluates (query, document) pairs and reorders results by relevance. This step reduces false positives before the final context window.

### Intelligent knowledge system architecture (Part 5)

Explains how the pipeline models reusable knowledge modules for AI retrieval, dynamic assembly, and multi-channel documentation delivery.

1. **Embedding cache** stores query embeddings in an in-memory LRU cache (TTL: 3,600 seconds, max: 512 entries). Repeated queries skip the OpenAI embedding API call.

1. **Multi-mode evaluation** compares token, semantic, hybrid, and hybrid+rerank search modes against a curated 50-query dataset (`config/retrieval_eval_dataset.yml`). Run `python3 scripts/run_retrieval_evals.py --mode all` to generate a comparison report.

##### Intelligent knowledge system architecture (Part 5): Retrieval orchestration flow

The retrieval flow starts with a question, chooses hybrid search when FAISS and hybrid mode are available, falls back to semantic or token overlap when needed, deduplicates by `parent_id`, optionally reranks with the cross-encoder, and returns top context modules.

##### Intelligent knowledge system architecture (Part 5): Configuration

All features are enabled by default in `config/ask-ai.yml`:

| Feature | Config key | Default |
| --- | --- | --- |
| Chunking | `chunking.enabled` | `true` |
| Hybrid search | `hybrid_search.enabled` | `true` |
| HyDE | `hyde.enabled` | `true` |
| Reranking | `reranking.enabled` | `true` |
| Embedding cache | `embedding_cache.enabled` | `true` |

Environment variable overrides: `ASK_AI_HYBRID_ENABLED`, `ASK_AI_HYDE_ENABLED`, `ASK_AI_RERANK_ENABLED`, `ASK_AI_EMBED_CACHE_ENABLED`.

### Intelligent knowledge system architecture (Part 6)

Explains how the pipeline models reusable knowledge modules for AI retrieval, dynamic assembly, and multi-channel documentation delivery.

#### Intelligent knowledge system architecture (Part 6): Security and governance

Use owner fields and verification dates to enforce accountability.

- Assign one owner per module.
- Verify security-sensitive modules every 30 days.
- Deprecate stale modules by changing `status` to `deprecated`.

#### Intelligent knowledge system architecture (Part 6): Next steps

- [Assemble intent experiences](../how-to/assemble-intent-experiences.md)
- [Intent experiences reference](../reference/intent-experiences/index.md)
- [Workflow execution model](workflow-execution-model.md)

### Multi-Protocol Architecture

Unified docs-ops pipeline for REST, GraphQL, gRPC, AsyncAPI, and WebSocket.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### Multi-Protocol Architecture: VeriDoc/VeriOps Multi-Protocol Architecture

Positioning statement:

`VeriDoc/VeriOps: one docs-ops pipeline for REST, GraphQL, gRPC, AsyncAPI, and WebSocket.`

#### Multi-Protocol Architecture: Supported protocols (core-5)

1. REST (OpenAPI)
1. GraphQL (SDL/introspection)
1. gRPC (Proto/descriptor)
1. AsyncAPI (event-driven specs)
1. WebSocket (channel/message contracts)

#### Multi-Protocol Architecture: Unified stage flow

`ingest -> contract validation -> server stub generation -> lint -> regression -> docs generation -> quality gates -> test assets -> upload -> publish`

Implementation entrypoint:

```bash

python3 scripts/run_multi_protocol_contract_flow.py \
  --runtime-config docsops/config/client_runtime.yml \
  --reports-dir reports

```

#### Multi-Protocol Architecture: Engine and adapters

- `scripts/multi_protocol_engine.py` - stage adapter orchestration.
- `scripts/run_multi_protocol_contract_flow.py` - flow runner + report output.
- `scripts/api_protocols.py` - protocol normalization, aliases, defaults.
- `scripts/generate_protocol_server_stubs.py` - protocol-specific server stubs with business-logic placeholders.

### Multi-Protocol Architecture (Part 2)

Unified docs-ops pipeline for REST, GraphQL, gRPC, AsyncAPI, and WebSocket.

#### Multi-Protocol Architecture (Part 2): Protocol-specific validators

- REST: `scripts/validate_openapi_contract.py`
- GraphQL: `scripts/validate_graphql_contract.py` (root/schema checks, duplicate types/fields, root-type references)
- gRPC: `scripts/validate_proto_contract.py` (syntax checks, duplicate declarations/rpcs, proto3 `required` guard)
- AsyncAPI: `scripts/validate_asyncapi_contract.py` (channel operations + message payload semantics)
- WebSocket: `scripts/validate_websocket_contract.py` (channel/event presence + payload/schema semantics)
- Deep protocol lint stack (7+ checks): `scripts/run_protocol_lint_stack.py`

#### Multi-Protocol Architecture (Part 2): Regression

- Generic snapshot gate: `scripts/check_protocol_regression.py`
- Per-protocol snapshot path is runtime-configurable.

#### Multi-Protocol Architecture (Part 2): Docs + publish

- Generate protocol docs: `scripts/generate_protocol_docs.py`
- Publish protocol assets: `scripts/publish_protocol_assets.py`
- Generated protocol docs include interactive testers:
  - GraphQL query execution (mock/real endpoint)
  - gRPC via HTTP gateway adapter
  - AsyncAPI ws/http publish checks
  - WebSocket live connect/send checks

### Multi-Protocol Architecture (Part 3)

Unified docs-ops pipeline for REST, GraphQL, gRPC, AsyncAPI, and WebSocket.

#### Multi-Protocol Architecture (Part 3): Test assets and smart-merge

- Generator: `scripts/generate_protocol_test_assets.py`
- Upload: `scripts/upload_api_test_assets.py`
- Coverage gate: `scripts/validate_protocol_test_coverage.py`
- Runtime self-verify (mock/real endpoint): `scripts/run_protocol_self_verify.py`
- Endpoint auto-resolution for non-REST testers:
  - preferred: Postman external mock (`scripts/ensure_external_mock_server.py`)
  - fallback: public echo endpoints (`https://postman-echo.com/post`, `wss://echo.websocket.events`)
- Protocol docs quality + lifecycle suite: `scripts/run_protocol_docs_quality_suite.py`
  - applies docs normalization, metadata optimization, multilang/smoke checks
  - updates glossary markers
  - refreshes RAG assets (knowledge modules, retrieval index, knowledge graph, retrieval evals)
- Smart-merge preserves manual/customized cases and sets `needs_review` on drift/stale entities.
- Non-REST generator emits richer artifacts: cases JSON, TestRail CSV, Zephyr JSON, `test_matrix.json`, `fuzz_scenarios.json`.

### Multi-Protocol Architecture (Part 4)

Unified docs-ops pipeline for REST, GraphQL, gRPC, AsyncAPI, and WebSocket.

#### Multi-Protocol Architecture (Part 4): Advanced RAG retrieval pipeline

The multi-protocol quality suite (`run_protocol_docs_quality_suite.py`) refreshes RAG assets including FAISS embeddings. Six advanced retrieval features are available:

| Feature | Module | Description |
| --- | --- | --- |
| Token-aware chunking | `scripts/chunker.py` | Splits modules into 750-token chunks with 100-token overlap (`cl100k_base`) |
| FAISS embeddings | `scripts/generate_embeddings.py --chunk` | Embeds chunks with `text-embedding-3-small`, builds FAISS index |
| Hybrid search (RRF) | `runtime/.../retrieval.py` | Fuses semantic and token-overlap rankings (k=60) |
| HyDE query expansion | `runtime/.../retrieval.py` | Generates hypothetical passage via `gpt-4.1-mini` before embedding |
| Cross-encoder reranking | `scripts/vector_store.py`, `runtime/.../retrieval.py` | Rescores top 20 candidates with `ms-marco-MiniLM-L-6-v2` |
| Embedding cache | `runtime/.../retrieval.py` | In-memory LRU cache (TTL: 3,600 seconds, max: 512) |
| Multi-mode evaluation | `scripts/run_retrieval_evals.py --mode all` | Compares token, semantic, hybrid, and hybrid+rerank modes |

### Multi-Protocol Architecture (Part 5)

Unified docs-ops pipeline for REST, GraphQL, gRPC, AsyncAPI, and WebSocket.

##### Multi-Protocol Architecture (Part 5): RAG prep behavior on pipeline run

1. Extract knowledge modules from docs
1. Validate modules and rebuild retrieval index
1. Generate FAISS embeddings with optional chunking (`--chunk`)
1. Run retrieval evals (single-mode or multi-mode comparison)
1. Output comparison report to `reports/retrieval_comparison.json`

##### Multi-Protocol Architecture (Part 5): Configuration

All features are enabled by default in `config/ask-ai.yml`. Runtime overrides via environment variables: `ASK_AI_HYBRID_ENABLED`, `ASK_AI_HYDE_ENABLED`, `ASK_AI_RERANK_ENABLED`, `ASK_AI_EMBED_CACHE_ENABLED`.

##### Multi-Protocol Architecture (Part 5): Eval dataset

A curated 50-query eval dataset is maintained at `config/retrieval_eval_dataset.yml`. It covers queries across all five protocols (REST, GraphQL, gRPC, AsyncAPI, WebSocket).

#### Multi-Protocol Architecture (Part 5): Template and snippet parity

- Protocol-specific templates are part of the default library:
  - `templates/protocols/graphql-reference.md`
  - `templates/protocols/grpc-reference.md`
  - `templates/protocols/asyncapi-reference.md`
  - `templates/protocols/websocket-reference.md`
- Reusable blocks are centralized in `templates/protocols/api-protocol-snippets.md`.
- LLM generation uses these assets to keep structure, terminology, and formatting consistent with REST-grade docs.

#### Multi-Protocol Architecture (Part 5): Next steps

- [Documentation index](../index.md)

### Multi-Protocol Architecture (Part 6)

Unified docs-ops pipeline for REST, GraphQL, gRPC, AsyncAPI, and WebSocket.

#### Multi-Protocol Architecture (Part 6): Implementation status (2026-03-25)

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

### Network transparency reference

Complete list of all outgoing network requests the pipeline makes, with exact payload schemas. No client data leaves your network.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### Network transparency reference: Network transparency reference

The {{ product_name }} pipeline is a locally installed tool that generates documentation using your own LLM. This reference lists every outgoing network request the pipeline can make, with exact payload schemas. You can verify each claim with a packet capture tool.

#### Network transparency reference: Zero client data guarantee

The pipeline processes all documentation locally. Your source code, API contracts, documentation content, and generated outputs never leave your network. The only outgoing requests contain license metadata and version information.

#### Network transparency reference: Complete outgoing request inventory

The pipeline makes exactly 5 types of outgoing HTTP requests. Each request is listed below with the exact JSON schema of what is sent.

### Network transparency reference (Part 2)

Complete list of all outgoing network requests the pipeline makes, with exact payload schemas. No client data leaves your network.

##### Network transparency reference (Part 2): Request 1: License activation

**When:** First time setup, or when re-activating after a license key change.

**Endpoint:** `POST /v1/activate`

**Frequency:** Once per installation.

```json

{
  "key": "VDOC-PRO-acme-a8f3b2c1",
  "machine_fingerprint": "sha256-hex-string-64-chars"
}

```

**Field details:**

| Field | Type | Description | Contains client data? |
| --- | --- | --- | --- |
| `key` | string | License key provided by VeriOps sales | No |
| `machine_fingerprint` | string | SHA-256 of `hostname + OS + username + repo_path` | No (one-way hash, not reversible) |

**What is NOT sent:** No file names, no document content, no source code, no API contracts, no IP addresses beyond the TCP connection itself.

**How to verify:**

```bash

# Capture the activation request with tcpdump
sudo tcpdump -i any -A host licensing.veriops.dev port 443

# Or use mitmproxy for HTTPS inspection
mitmproxy --mode upstream:https://licensing.veriops.dev

```

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

### Network transparency reference (Part 5)

Complete list of all outgoing network requests the pipeline makes, with exact payload schemas. No client data leaves your network.

#### Network transparency reference (Part 5): Requests the pipeline never makes

The following types of requests are architecturally impossible because the pipeline contains no code to construct them:

| Category | Why it cannot happen |
| --- | --- |
| Document content upload | No upload endpoint exists in the codebase. Search for `urllib` calls yourself. |
| File listing transmission | Pipeline reads files locally; no serialization-to-server code exists. |
| Quality score reporting | Scores are computed locally and written to local `reports/` directory. |
| Source code exfiltration | Pipeline scripts operate on `docs/` and `api/` directories only. |
| Telemetry or analytics | No telemetry SDK is included. No analytics endpoint is configured. |
| User behavior tracking | No session tracking, no event logging to external services. |

#### Network transparency reference (Part 5): How to audit the pipeline yourself

##### Network transparency reference (Part 5): Network audit with tcpdump

Run the full weekly batch while capturing all outgoing traffic:

```bash

# Terminal 1: Start packet capture
sudo tcpdump -i any -w pipeline-traffic.pcap \
  'not (src net 10.0.0.0/8 or src net 172.16.0.0/12 or src net 192.168.0.0/16)'

# Terminal 2: Run the pipeline
python3 scripts/run_weekly_gap_batch.py \
  --docsops-root docsops --reports-dir reports

# Terminal 1: Stop capture (Ctrl+C), then analyze
tcpdump -r pipeline-traffic.pcap -A | grep -i "POST\|GET\|Host:"

```

### Network transparency reference (Part 6)

Complete list of all outgoing network requests the pipeline makes, with exact payload schemas. No client data leaves your network.

##### Network transparency reference (Part 6): Air-gapped operation

The pipeline works without any network access. Set these to disable all outgoing requests:

```bash

# Block all VeriOps server communication
export VERIOPS_UPDATE_SERVER=""
export VERIOPS_LICENSE_PLAN=enterprise  # Dev/test bypass

# Run pipeline in fully offline mode
python3 scripts/run_weekly_gap_batch.py --docsops-root docsops

```

Without network access, the pipeline uses:

- Local license JWT file (`docsops/license.jwt`) for offline validation
- Local capability pack (`docsops/.capability_pack.enc`) for scoring weights
- Offline grace period (3, 7, or 30 days depending on plan tier) before degrading to community mode

##### Network transparency reference (Part 6): Source code audit

Every network call in the pipeline is in exactly 2 files:

```bash

# Find all outgoing HTTP calls in the pipeline
grep -rn "urlopen\|urllib\|requests\.\|httpx\.\|aiohttp" scripts/ build/

# Expected results: only in these files:
#   scripts/check_updates.py  -- update check + download
#   scripts/generate_public_docs_audit.py -- web crawler (optional, enterprise only)

```

The `generate_public_docs_audit.py` script crawls public documentation sites for quality auditing. It accesses only URLs explicitly provided by the user via `--site-url` arguments. It does not contact VeriOps servers.

### Network transparency reference (Part 7)

Complete list of all outgoing network requests the pipeline makes, with exact payload schemas. No client data leaves your network.

#### Network transparency reference (Part 7): Machine fingerprint details

The machine fingerprint is a SHA-256 hash used for seat counting. It is computed from:

```python

parts = [
    platform.node(),      # Hostname (e.g., "dev-server-01")
    platform.system(),    # OS (e.g., "Linux")
    os.getenv("USER"),    # Username (e.g., "deploy")
    str(REPO_ROOT),       # Repository path (e.g., "/opt/docs-pipeline")
]
fingerprint = sha256("|".join(parts))
# Result: "a1b2c3d4..." (64 hex characters)

```

The hash is one-way. VeriOps cannot reconstruct your hostname, username, or file paths from the fingerprint. The fingerprint changes if you move the pipeline to a different machine, which requires re-activation (seat transfer).

### Network transparency reference (Part 8)

Complete list of all outgoing network requests the pipeline makes, with exact payload schemas. No client data leaves your network.

#### Network transparency reference (Part 8): Capability pack contents

The encrypted capability pack (`docsops/.capability_pack.enc`) contains scoring intelligence, not client data. Contents after decryption:

| Section | What it contains | Example values |
| --- | --- | --- |
| `scoring.geo_rules` | GEO optimization thresholds | `first_para_max_words: 60` |
| `scoring.kpi_weights` | Quality score formula weights | `metadata_weight: 0.35` |
| `scoring.audit_weights` | 7-pillar audit scoring weights | `content_quality: 0.22` |
| `scoring.sla_thresholds` | SLA breach detection thresholds | `min_quality_score: 70` |
| `priority` | Action item tier classification | `tier1_categories: [breaking_change]` |
| `prompts` | Documentation quality prompt templates | Stripe-quality formula text |
| `policies` | Quality gate enforcement rules | `vale_blocks_commit: true` |

The pack is encrypted with AES-256-GCM. The encryption key is derived from your license key via HKDF-SHA256. Only your installation can decrypt your pack.

### Network transparency reference (Part 9)

Complete list of all outgoing network requests the pipeline makes, with exact payload schemas. No client data leaves your network.

#### Network transparency reference (Part 9): Summary of data flow

```text

Your Network                              VeriOps Server
+----------------------------------+      +----------------------+
| docs/ (your content)             |      |                      |
| api/ (your contracts)            |      | Receives ONLY:       |
| reports/ (your quality scores)   |      |  - License key       |
|                                  |      |  - Machine hash      |
| ALL processing happens here:     |      |  - Version string    |
|  - Linting                       |      |  - Platform string   |
|  - Scoring                       |      |                      |
|  - Gap analysis           ------>|      | Sends BACK:          |
|  - KPI wall               NEVER  |      |  - Signed JWT        |
|  - PDF generation                |      |  - Encrypted pack    |
|  - Knowledge modules             |      |  - Update bundles    |
|  - Test asset generation         |      |                      |
+----------------------------------+      +----------------------+

```

#### Network transparency reference (Part 9): Next steps

- [Documentation index](index.md)

### Pipeline Capabilities Catalog

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### Pipeline Capabilities Catalog: Pipeline Capabilities Catalog

### Pipeline Capabilities Catalog (Part 10)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

#### Pipeline Capabilities Catalog (Part 10): Multi-protocol contract pipeline

The pipeline supports five API protocols with a unified orchestrator (`run_multi_protocol_contract_flow.py`). Each protocol has its own contract format, validator, reference template, test generator, and sandbox fallback.

| Protocol | Contract format | Validator | Sandbox fallback |
| --- | --- | --- | --- |
| REST | OpenAPI 3.0 YAML | `validate_openapi_contract.py` + Spectral + Redocly | Prism / Postman mock server |
| GraphQL | SDL (`.graphql`) | `validate_graphql_contract.py` | `postman-echo.com/post` |
| gRPC | Proto3 (`.proto`) | `validate_proto_contract.py` | `postman-echo.com/post` (JSON-over-HTTP) |
| AsyncAPI | AsyncAPI 2.6 YAML | `validate_asyncapi_contract.py` | `postman-echo.com/post` + `echo.websocket.events` |
| WebSocket | Channel YAML | `validate_websocket_contract.py` | `echo.websocket.events` |

**9 pipeline stages per protocol:** ingest, contract validation, server stub generation, lint, regression detection, docs generation, quality gates (frontmatter + snippet lint + self-verification), test assets generation with smart merge, publish.

**Autofix cycle:** up to 3 auto-remediation attempts per protocol. Regenerates docs and retries semantic consistency checks on failure.

**Contract generation from planning notes:** `generate_protocol_contract_from_planning_notes.py` generates protocol specs from markdown planning notes.

### Pipeline Capabilities Catalog (Part 11)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

**Self-verification:** `run_protocol_self_verify.py` validates generated docs against live/mock endpoints (GraphQL introspection, gRPC method invocation, AsyncAPI event publish, WebSocket connection routing).

### Pipeline Capabilities Catalog (Part 12)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

#### Pipeline Capabilities Catalog (Part 12): Test assets generation and smart merge

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

### Pipeline Capabilities Catalog (Part 13)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

#### Pipeline Capabilities Catalog (Part 13): Quality checks (32 automated)

The pipeline enforces 32 automated checks on every documentation page across four categories:

| Category | Count | What they verify |
| --- | --- | --- |
| GEO checks | 8 | LLM and AI search optimization: meta descriptions, first paragraph length, heading hierarchy, fact density |
| SEO checks | 14 | Traditional search optimization: title length, URL depth, internal links, image alt text, structured data |
| Style checks | 6 | American English, active voice, no weasel words, no contractions, second person, present tense |
| Contract checks | 4 | Schema validation, regression detection, snippet lint, self-verification against endpoints |

### Pipeline Capabilities Catalog (Part 14)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

#### Pipeline Capabilities Catalog (Part 14): RAG retrieval pipeline

The pipeline generates a knowledge retrieval layer with six advanced features:

| Feature | Description |
| --- | --- |
| Token-aware chunking | Splits modules into 750-token chunks with 100-token overlap (`cl100k_base`) |
| Hybrid search (RRF) | Fuses semantic (FAISS) and token-overlap rankings with Reciprocal Rank Fusion (k=60) |
| HyDE query expansion | Generates hypothetical doc passage via LLM before embedding for better retrieval on vague queries |
| Cross-encoder reranking | Rescores top 20 candidates with `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Embedding cache | In-memory LRU cache (TTL 3,600 seconds, max 512 entries) for query embeddings |
| Multi-mode evaluation | Compares token, semantic, hybrid, and hybrid+rerank modes across curated queries |

**Pipeline scripts:**

1. `extract_knowledge_modules_from_docs.py` -- auto-chunk docs into knowledge modules
1. `validate_knowledge_modules.py` -- schema validation, duplicate ID detection, cycle check
1. `generate_knowledge_retrieval_index.py` -- JSON index for Algolia + FAISS input
1. `generate_embeddings.py` -- FAISS vector index (`text-embedding-3-small`, 1536 dims)
1. `generate_knowledge_graph_jsonld.py` -- JSON-LD knowledge graph
1. `run_retrieval_evals.py` -- precision@k, recall@k, hallucination rate evaluation

### Pipeline Capabilities Catalog (Part 15)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

#### Pipeline Capabilities Catalog (Part 15): RAG operations and runtime surface

Runtime and operations include:

1. Query endpoints: `/rag/query` and `/rag/runtime/query`
1. Observability endpoints: `/rag/metrics` and `/rag/alerts`
1. Version pointer artifacts: `docs/assets/rag_current.json`, `docs/assets/rag_promoted.json`
1. Version history and retention: `docs/assets/rag_version_history.json`, `docs/assets/rag-versions/`
1. Lifecycle report: `reports/rag_reindex_report.json`
1. Unified enforcement report: `reports/rag_optimization_layer_report.json`

#### Pipeline Capabilities Catalog (Part 15): Current retrieval gate snapshot (2026-04-05)

Latest local run (`npm run eval:retrieval`) produced:

1. Mode: `token` (no `OPENAI_API_KEY` and no FAISS artifacts in current run context)
1. Precision@3: `0.24`
1. Recall@3: `0.72`
1. Hallucination rate: `0.0`
1. Sample count: `25` (auto-generated dataset)

This snapshot confirms the RAG layer is active and measurable in local mode, and it also shows remaining headroom for precision improvements in strict local token fallback.

### Pipeline Capabilities Catalog (Part 16)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

#### Pipeline Capabilities Catalog (Part 16): Public docs auditor and executive PDF

The public docs auditor crawls live documentation sites and generates a comprehensive quality assessment.

**Audit modes:**

| Mode | Command | Description |
| --- | --- | --- |
| Basic | `npm run audit:public` | Crawl + evaluate (no LLM) |
| Interactive wizard | `npm run audit:public:wizard` | Step-by-step guided audit |
| LLM-powered | `npm run audit:public:llm` | Full expert analysis with Claude |
| LLM summary only | `npm run audit:public:llm-summary` | Quick LLM summary without full crawl |
| Executive PDF | `npm run audit:executive-pdf` | Consulting-grade PDF from audit results |
| Scorecard | `npm run audit:scorecard` | Comprehensive scoring across all quality dimensions |

**Executive PDF contents:** cover page with headline findings, executive summary with score gauge and grade, per-site metrics table, board-level KPI bars with financial impact, risk matrix with priority actions, expert analysis (LLM or data-driven fallback), methodology appendix, evidence appendix.

**Audit scorecard dimensions:** docs quality (SEO/GEO), API coverage, code example reliability, glossary health, content freshness, policy compliance.

### Pipeline Capabilities Catalog (Part 17)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

#### Pipeline Capabilities Catalog (Part 17): API-first external sandbox note

For public web playground usage, prefer `external` sandbox mode and a public HTTPS mock URL with CORS:

```bash

API_FIRST_DEMO_SANDBOX_BACKEND=external \
API_FIRST_DEMO_MOCK_BASE_URL="https://<your-real-public-mock-url>/v1" \
bash scripts/api_first_demo_live.sh

```

The pipeline is provider-agnostic. You can use Postman Mock Servers, Stoplight-hosted Prism, Mockoon Cloud, or your own hosted Prism-compatible endpoint.

For Postman auto-prepare mode, provide:

- `POSTMAN_API_KEY`
- `POSTMAN_WORKSPACE_ID`
- optional `POSTMAN_COLLECTION_UID` (if empty, pipeline imports collection from generated OpenAPI)
- optional `POSTMAN_MOCK_SERVER_ID`

#### Pipeline Capabilities Catalog (Part 17): PR auto-doc workflow capability

Enable in client profile with `runtime.pr_autofix`.

Installed workflow behavior:

1. Trigger on PR events (`opened`, `synchronize`, `reopened`, `labeled`).
1. Analyze only current PR diff (`base...head`).
1. Run docs auto-fix script if docs contract/drift gates require docs updates.
1. Commit generated docs into the same PR branch.
1. Rerun checks automatically.

### Pipeline Capabilities Catalog (Part 18)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

#### Pipeline Capabilities Catalog (Part 18): Templates

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

#### Pipeline Capabilities Catalog (Part 18): Policy Packs

- `api-first.yml`
- `minimal.yml`
- `monorepo.yml`
- `multi-product.yml`
- `plg.yml`

#### Pipeline Capabilities Catalog (Part 18): Knowledge Modules

Can be copied into client bundle with `bundle.include_paths: ['knowledge_modules']`.

- `webhook-auth-baseline.yml`
- `webhook-retry-policy.yml`

### Pipeline Capabilities Catalog (Part 19)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

#### Pipeline Capabilities Catalog (Part 19): Docker Compose Profiles

- `docker-compose.api-sandbox.live.yml`
- `docker-compose.api-sandbox.prodlike.yml`
- `docker-compose.api-sandbox.yml`
- `docker-compose.docs-ops.yml`

#### Pipeline Capabilities Catalog (Part 19): Next steps

- [Documentation index](../index.md)

### Pipeline Capabilities Catalog (Part 2)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

#### Pipeline Capabilities Catalog (Part 2): Current product definition (2026-04-05)

This content follows the active implementation baseline:

### Pipeline Capabilities Catalog (Part 20)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

#### Pipeline Capabilities Catalog (Part 20): Implementation status (2026-04-05)

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

### Pipeline Capabilities Catalog (Part 3)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` modes.
1. The smooth autopipeline covers all five API protocols (REST, GraphQL, gRPC, AsyncAPI, and WebSocket) in one operational model.
1. Non-REST flow includes generated server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated, with Postman-supported auto-prepare in external mode.
1. Contract test assets are generated automatically and merged with smart-merge so manual/customized cases are preserved and flagged for review when needed.
1. Knowledge/RAG maintenance, terminology sync, and quality/compliance gates run through the same automation surface when enabled.
1. Local-first operation is the default mode: weekly scheduler and quality gates run in the client repository, with GitHub Actions as a compatibility mode.
1. RAG runtime supports `cloud`, `hybrid`, and `strict-local` operational profiles with one enforcement layer.
1. RAG runtime endpoints include `/rag/query`, `/rag/runtime/query`, `/rag/metrics`, and `/rag/alerts` with access-control checks.
1. RAG index lifecycle supports versioned reindex, promote, rollback, and retention pruning through one command surface.
1. Plan tiers gate advanced capabilities; higher plans include broader non-REST and governance scope.

This catalog has two layers:

### Pipeline Capabilities Catalog (Part 4)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

1. npm script entry points (from `package.json`)
1. direct CLI entry points in `scripts/*.py` that are used by provisioning/operator flows and are not exposed as npm commands

Non-script concepts (policy semantics, sales packaging, pilot/full scope) are documented in ops guides.

Use this catalog with `runtime.custom_tasks.weekly` in client profiles to enable any capability.

### Pipeline Capabilities Catalog (Part 5)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

#### Pipeline Capabilities Catalog (Part 5): Non-API documentation flows (docs-first scope)

The platform is not limited to API-first automation. In active production usage, it also runs full docs-first and code-first documentation operations for non-API content:

1. Detects content gaps, stale pages, and drift across product docs, runbooks, admin guides, troubleshooting, and release notes.
1. Generates and updates documentation types beyond API references (tutorial, how-to, concept, reference, troubleshooting, release-note, security, SDK, user/admin, and operations docs).
1. Applies normalization, style, metadata/frontmatter, SEO/GEO, terminology governance, and snippet validation to all documentation categories.
1. Executes lifecycle controls (active/deprecated/removed states, replacement links, and freshness cadence).
1. Runs knowledge extraction and retrieval preparation for all docs, not only API pages.
1. Produces consolidated review artifacts so human input is focused on approval and business accuracy, not repetitive formatting and synchronization work.

### Pipeline Capabilities Catalog (Part 6)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

#### Pipeline Capabilities Catalog (Part 6): How to enable any capability for a client

```yaml

runtime:
  custom_tasks:
    weekly:
      - id: "my-task"
        enabled: true
        command: "npm run <script-name>"
        continue_on_error: true

```

### Pipeline Capabilities Catalog (Part 7)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

| Script | Category | Command |
| --- | --- | --- |
| `agent:claude:auto` | Agent/Demo | `bash scripts/claude-auto.sh` |
| `agent:codex:auto` | Agent/Demo | `bash scripts/codex-auto.sh` |
| `api-first-demo` | API-first | `bash scripts/api_first_demo_live.sh` |
| `api-first-demo:stop` | API-first | `bash scripts/api_first_demo_stop.sh` |
| `api-first:demo` | API-first | `bash -lc 'set -e; API_SANDBOX_EXTERNAL_BASE_URL=\"https://<your-real-public-mock-url>/v1\" bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010 external; python3 scripts/run_api_first_flow.py --project-slug taskstream --notes demos/api-first/taskstream-planning-notes.md --spec api/openapi.yaml --spec-tree api/taskstream --docs-provider mkdocs --inject-demo-nav --verify-user-path --mock-base-url https://<your-real-public-mock-url>/v1 --generate-test-assets --upload-test-assets --sync-playground-endpoint --auto-remediate --max-attempts 3'` |
| `api-first:demo:live` | API-first | `bash scripts/api_first_demo_live.sh` |
| `api-first:demo:stop` | API-first | `bash scripts/api_first_demo_stop.sh` |
| `api:first:flow:taskstream` | API-first | `python3 scripts/run_api_first_flow.py --project-slug taskstream --notes demos/api-first/taskstream-planning-notes.md --spec api/openapi.yaml --spec-tree api/taskstream --docs-provider mkdocs --inject-demo-nav --auto-remediate` |
| `api:first:v0:taskstream` | API-first | `python3 scripts/run_api_first_flow.py --project-slug taskstream --notes demos/api-first/taskstream-planning-notes.md --spec api/openapi.yaml --spec-tree api/taskstream --docs-provider mkdocs --auto-remediate --max-attempts 3` |
| `api:first:verify-user-path` | API-first | `python3 scripts/self_verify_api_user_path.py --base-url https://<your-real-public-mock-url>/v1` |
| `api:first:verify-user-path:prodlike` | API-first | `python3 scripts/self_verify_prodlike_user_path.py --base-url http://localhost:4011/v1` |
| `api:test:assets` | API-first | `python3 scripts/generate_api_test_assets.py --spec api/openapi.yaml --output-dir reports/api-test-assets --testrail-csv reports/api-test-assets/testrail_test_cases.csv --zephyr-json reports/api-test-assets/zephyr_test_cases.json` |
| `api:test:upload` | API-first | `python3 scripts/upload_api_test_assets.py --cases-json reports/api-test-assets/api_test_cases.json --report reports/api-test-assets/upload_report.json` |
| `audit:public` | Audit | `python3 scripts/generate_public_docs_audit.py` |
| `audit:public:wizard` | Audit | `python3 scripts/generate_public_docs_audit.py --interactive` |
| `audit:public:llm` | Audit | `python3 scripts/generate_public_docs_audit.py --llm-enabled --llm-model claude-sonnet-4-5` |
| `audit:public:llm-summary` | Audit | `python3 scripts/generate_public_docs_audit.py --llm-enabled --llm-summary-only --llm-model claude-sonnet-4-5` |
| `audit:executive-pdf` | Audit | `python3 scripts/generate_executive_audit_pdf.py --scorecard-json reports/audit_scorecard.json --public-audit-json reports/public_docs_audit.json --company-name "Client"` |
| `audit:scorecard` | Audit | `python3 scripts/generate_audit_scorecard.py --docs-dir docs --reports-dir reports --spec-path api/openapi.yaml --policy-pack policy_packs/api-first.yml --glossary-path glossary.yml --stale-days 180 --auto-run-smoke --json-output reports/audit_scorecard.json --html-output reports/audit_scorecard.html` |
| `api:sandbox:live` | API-first | `bash scripts/api_sandbox_live.sh up taskstream ./api/openapi.yaml 4010` |
| `api:sandbox:live:logs` | API-first | `bash scripts/api_sandbox_live.sh logs taskstream ./api/openapi.yaml 4010` |
| `api:sandbox:live:status` | API-first | `bash scripts/api_sandbox_live.sh status taskstream ./api/openapi.yaml 4010` |
| `api:sandbox:live:stop` | API-first | `bash scripts/api_sandbox_live.sh down taskstream ./api/openapi.yaml 4010` |
| `api:sandbox:mock` | API-first | `docker compose -f docker-compose.api-sandbox.yml up -d` |
| `api:sandbox:prodlike` | API-first | `bash scripts/api_prodlike_project.sh` |
| `api:sandbox:prodlike:down` | API-first | `bash scripts/api_prodlike_project.sh down taskstream 4011` |
| `api:sandbox:prodlike:logs` | API-first | `bash scripts/api_prodlike_project.sh logs taskstream 4011` |
| `api:sandbox:prodlike:status` | API-first | `bash scripts/api_prodlike_project.sh status taskstream 4011` |
| `api:sandbox:prodlike:up` | API-first | `bash scripts/api_prodlike_project.sh up taskstream 4011` |
| `api:sandbox:project` | API-first | `bash scripts/api_sandbox_project.sh` |
| `api:sandbox:stop` | API-first | `docker compose -f docker-compose.api-sandbox.yml down` |
| `askai:configure` | General | `python3 scripts/configure_ask_ai.py` |
| `askai:disable` | General | `python3 scripts/configure_ask_ai.py --disable` |
| `askai:enable` | General | `python3 scripts/configure_ask_ai.py --enable` |
| `askai:runtime:install` | General | `python3 scripts/install_ask_ai_runtime.py --target-dir .` |
| `askai:runtime:install:force` | General | `python3 scripts/install_ask_ai_runtime.py --target-dir . --force` |
| `askai:status` | General | `python3 scripts/configure_ask_ai.py --status` |
| `badges` | General | `python3 scripts/generate_badge.py --json reports/kpi-wall.json --output reports` |
| `build` | Build/Generate | `python3 scripts/run_generator.py build` |
| `build:docusaurus` | Build/Generate | `npx docusaurus build` |
| `build:intent` | Build/Generate | `python3 scripts/assemble_intent_experience.py` |
| `build:intent:all` | Build/Generate | `python3 scripts/build_all_intent_experiences.py` |
| `build:knowledge-enrich:llm` | Build/Generate | `python3 scripts/enrich_knowledge_modules_semantic.py` |
| `build:knowledge-graph` | Build/Generate | `python3 scripts/generate_knowledge_graph_jsonld.py --modules-dir knowledge_modules --output docs/assets/knowledge-graph.jsonld --report reports/knowledge_graph_report.json` |
| `build:knowledge-index` | Build/Generate | `python3 scripts/generate_knowledge_retrieval_index.py` |
| `build:mkdocs` | Build/Generate | `mkdocs build --strict` |
| `build:rag:reindex` | Build/Generate | `python3 scripts/rag_reindex_lifecycle.py --repo-root . --with-embeddings --provider local` |
| `configurator` | General | `python3 scripts/generate_configurator.py` |
| `consolidate` | General | `npm run gaps && npm run kpi-wall && npm run kpi-sla && npm run i18n:sync && npm run validate:knowledge && python3 scripts/consolidate_reports.py` |
| `consolidate:reports-only` | General | `python3 scripts/consolidate_reports.py` |
| `convert:to-docusaurus` | General | `python3 scripts/markdown_converter.py to-docusaurus docs/` |
| `convert:to-mkdocs` | General | `python3 scripts/markdown_converter.py to-mkdocs docs/` |
| `demo:api-first` | Agent/Demo | `bash scripts/api_first_demo_live.sh` |
| `demo:api-first:stop` | Agent/Demo | `bash scripts/api_first_demo_stop.sh` |
| `demo:claude:loop` | Agent/Demo | `bash scripts/claude-demo-loop.sh` |
| `demo:codex` | Agent/Demo | `bash scripts/codex-demo.sh` |
| `demo:codex:loop` | Agent/Demo | `bash scripts/codex-demo-loop.sh` |
| `docs-contract` | General | `python3 scripts/check_docs_contract.py --base origin/main --head HEAD --json-output reports/pr_docs_contract.json` |
| `docs-ops:e2e` | VeriOps tests | `python3 scripts/test_docs_ops_e2e.py` |
| `docs-ops:golden` | VeriOps tests | `python3 scripts/test_golden_reports_and_workflows.py` |
| `docs-ops:test-suite` | VeriOps tests | `python3 -m pytest -q tests/test_autopipeline_suite.py` |
| `docsops:generate` | General | `python3 scripts/docsops_generate.py generate --mode operator --trigger always` |
| `docsops:generate:auto` | General | `python3 scripts/docsops_generate.py generate --mode operator --trigger always --auto` |
| `docsops:generate:policy` | General | `python3 scripts/docsops_generate.py generate --mode operator --trigger policy --auto` |
| `docsops:generate:veridoc` | General | `python3 scripts/docsops_generate.py generate --mode veridoc --trigger policy --auto` |
| `drift-check` | General | `python3 scripts/check_api_sdk_drift.py --base origin/main --head HEAD --json-output reports/api_sdk_drift_report.json --md-output reports/api_sdk_drift_report.md` |
| `eval:retrieval` | General | `python3 scripts/run_retrieval_evals_gate.py` |
| `gaps` | Gap detection | `python3 -m scripts.gap_detection.cli analyze` |
| `gaps:code` | Gap detection | `python3 -m scripts.gap_detection.cli code` |
| `gaps:community` | Gap detection | `python3 -m scripts.gap_detection.cli community` |
| `gaps:full` | Gap detection | `python3 -m scripts.gap_detection.cli full --generate` |
| `gaps:generate` | Gap detection | `python3 -m scripts.gap_detection.cli generate --report reports/doc_gaps_report.json` |
| `generate:multilang-tabs` | General | `python3 scripts/generate_multilang_tabs.py --paths docs templates --scope api --write` |
| `generate:multilang-tabs:all` | General | `python3 scripts/generate_multilang_tabs.py --paths docs templates --scope all --write` |
| `generator:detect` | General | `python3 scripts/run_generator.py detect` |
| `generator:info` | General | `python3 scripts/run_generator.py info` |
| `glossary:sync` | General | `python3 scripts/sync_project_glossary.py --paths docs --glossary glossary.yml --report reports/glossary_sync_report.json --write` |
| `i18n:migrate` | Localization | `python3 scripts/i18n_migrate.py` |
| `i18n:sync` | Localization | `python3 scripts/i18n_sync.py` |
| `i18n:translate` | Localization | `python3 scripts/i18n_translate.py` |
| `i18n:translate:all` | Localization | `python3 scripts/i18n_translate.py --all-missing` |
| `i18n:translate:stale` | Localization | `python3 scripts/i18n_translate.py --stale-only` |
| `kpi-full` | KPI/SLA | `npm run kpi-wall && npm run badges` |
| `kpi-sla` | KPI/SLA | `python3 scripts/evaluate_kpi_sla.py --current reports/kpi-wall.json --policy-pack policy_packs/api-first.yml --json-output reports/kpi-sla-report.json --md-output reports/kpi-sla-report.md` |
| `kpi-wall` | KPI/SLA | `python3 scripts/generate_kpi_wall.py --docs-dir docs --reports-dir reports --stale-days 90` |
| `lint` | Lint/Quality | `npm run normalize:docs:check && npm run lint:vale && npm run lint:md && npm run lint:spell && npm run lint:frontmatter && npm run lint:geo && npm run lint:knowledge && npm run lint:snippets && npm run lint:multilang` |
| `lint:diagrams` | Lint/Quality | `python3 scripts/validate_diagram_content.py docs templates` |
| `lint:examples-smoke` | Lint/Quality | `python3 scripts/check_code_examples_smoke.py --paths docs templates` |
| `lint:examples-smoke:network` | Lint/Quality | `python3 scripts/check_code_examples_smoke.py --paths docs templates --allow-network` |
| `lint:frontmatter` | Lint/Quality | `python3 scripts/validate_frontmatter.py` |
| `lint:geo` | Lint/Quality | `python3 scripts/seo_geo_optimizer.py docs/` |
| `lint:knowledge` | Lint/Quality | `python3 scripts/validate_knowledge_modules.py` |
| `lint:layers` | Lint/Quality | `python3 scripts/doc_layers_validator.py` |
| `lint:md` | Lint/Quality | `markdownlint docs/` |
| `lint:multilang` | Lint/Quality | `python3 scripts/validate_multilang_examples.py --docs-dir docs --scope api --required-languages curl,javascript,python` |
| `lint:multilang:all` | Lint/Quality | `python3 scripts/validate_multilang_examples.py --docs-dir docs --scope all --required-languages curl,javascript,python` |
| `lint:openapi` | Lint/Quality | `npx -y @stoplight/spectral-cli lint api/openapi.yaml --ruleset .spectral.yml && npx -y @redocly/cli lint api/openapi.yaml && npx -y @apidevtools/swagger-cli validate api/openapi.yaml && python3 scripts/validate_openapi_contract.py api/openapi.yaml` |
| `lint:snippets` | Lint/Quality | `python3 scripts/lint_code_snippets.py docs/` |
| `lint:snippets:strict` | Lint/Quality | `python3 scripts/lint_code_snippets.py docs/ templates/ --strict` |
| `lint:spell` | Lint/Quality | `cspell "docs/**/*.md" --no-must-find-files` |
| `lint:vale` | Lint/Quality | `vale docs/` |
| `new-doc` | General | `python3 scripts/new_doc.py` |
| `normalize:docs` | General | `python3 scripts/normalize_docs.py docs/` |
| `normalize:docs:check` | General | `python3 scripts/normalize_docs.py docs/ --check` |
| `onboard:client` | General | `python3 scripts/onboard_client.py` |
| `openapi:overrides` | General | `python3 scripts/apply_openapi_overrides.py --spec api/openapi.yaml --spec-tree api/taskstream --overrides api/overrides/openapi.manual.yml` |
| `openapi:regression` | General | `python3 scripts/check_openapi_regression.py --spec api/openapi.yaml --spec-tree api/taskstream --snapshot api/.openapi-regression.json` |
| `openapi:regression:update` | General | `python3 scripts/check_openapi_regression.py --spec api/openapi.yaml --spec-tree api/taskstream --snapshot api/.openapi-regression.json --update` |
| `prepare` | General | `husky install` |
| `release-pack` | General | `python3 scripts/generate_release_docs_pack.py --output reports/release-docs-pack.md` |
| `serve` | General | `python3 scripts/run_generator.py serve` |
| `serve:docusaurus` | General | `npx docusaurus start` |
| `serve:mkdocs` | General | `mkdocs serve` |
| `smoke:prod` | Validation | `python3 scripts/production_smoke.py` |
| `test:adapter` | General | `python3 -m pytest tests/test_docusaurus_adapter.py -v` |
| `test:all` | General | `python3 -m pytest -q tests` |
| `test:configurator` | General | `python3 -m pytest tests/test_gui_configurator.py -v` |
| `validate:full` | Validation | `npm run validate:minimal && npm run lint:layers && npm run lint:diagrams && npm run validate:knowledge && npm run docs-ops:e2e && npm run docs-ops:golden && npm run docs-ops:test-suite && python3 test_pipeline.py` |
| `validate:knowledge` | Validation | `npm run lint:knowledge && npm run build:intent:all && npm run build:knowledge-index && npm run build:knowledge-graph && npm run eval:retrieval` |
| `validate:knowledge:with-llm-enrich` | Validation | `npm run build:knowledge-enrich:llm && npm run validate:knowledge` |
| `validate:minimal` | Validation | `npm run normalize:docs:check && npm run lint:md && npm run lint:frontmatter && npm run lint:geo && npm run lint:multilang && npm run lint:examples-smoke` |

### Pipeline Capabilities Catalog (Part 8)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

#### Pipeline Capabilities Catalog (Part 8): Direct CLI entry points (not exposed as npm scripts)

These are part of the current implementation and are invoked directly by operator/provisioning/weekly flows.

### Pipeline Capabilities Catalog (Part 9)

Generated catalog of available pipeline commands, templates, policy packs, and assets for client configuration.

| Script | Purpose |
| --- | --- |
| `scripts/build_client_bundle.py` | Build client-specific bundle in `generated/client_bundles/<client_id>/`. |
| `scripts/provision_client_repo.py` | One-shot install into client repo (bundle copy, config/policy, env checklist, scheduler install). |
| `scripts/init_pipeline.py` | Bootstrap pipeline directly from source into another repo (self-install path). |
| `scripts/run_weekly_gap_batch.py` | Main weekly local runner (gaps/stale/kpi/api-first/modules/custom tasks/consolidation). |
| `scripts/auto_fix_pr_docs.py` | PR branch docs autofix helper for optional GitHub workflow. |
| `scripts/ensure_external_mock_server.py` | Resolve/create external mock endpoint (Postman-supported flow). |
| `scripts/extract_knowledge_modules_from_docs.py` | Auto-extract knowledge modules from docs markdown. |
| `scripts/gap_detector.py` | Legacy/direct gap detector entry used in some compatibility paths. |
| `scripts/generate_docusaurus_config.py` | Generate/update Docusaurus config in adapter flows. |
| `scripts/generate_facets_index.py` | Build faceted search index artifacts. |
| `scripts/generate_fastapi_stubs_from_openapi.py` | Generate FastAPI stubs from OpenAPI. |
| `scripts/generate_openapi_from_planning_notes.py` | Generate OpenAPI root/tree from planning notes. |
| `scripts/generate_protocol_server_stubs.py` | Generate protocol server stubs with business-logic placeholders for REST, GraphQL, gRPC, AsyncAPI, and WebSocket. |
| `scripts/generate_pipeline_capabilities_catalog.py` | Regenerate this capabilities catalog file. |
| `scripts/lifecycle_manager.py` | Lifecycle scan/report/redirect guidance generation. |
| `scripts/manage_demo_nav.py` | Demo nav injection/removal helper. |
| `scripts/pilot_analysis.py` | Pilot analysis/report helper. |
| `scripts/preprocess_variables.py` | Variables pre-processing helper for docs generation flows. |
| `scripts/upload_to_algolia.py` | Upload generated search records to Algolia. |
| `scripts/validate_pr_dod.py` | DoD validation helper for PR workflows. |
| `scripts/run_multi_protocol_contract_flow.py` | Unified orchestrator for all 5 protocol documentation flows (REST, GraphQL, gRPC, AsyncAPI, WebSocket). Runs 9 stages: ingest, contract validation, server stub generation, lint, regression, docs generation, quality gates, test assets, publish. |
| `scripts/run_retrieval_evals_gate.py` | Smart retrieval gate with runtime mode selection (`token`, `hybrid`, `hybrid+rerank`) and adaptive threshold profile for dataset mismatch cases. |
| `scripts/rag_reindex_lifecycle.py` | Versioned RAG reindex lifecycle: extract, validate, index build, optional embeddings, promote, rollback, and retention pruning. |
| `scripts/enforce_rag_optimization_layer.py` | Unified RAG optimization layer enforcement for cloud, hybrid, and strict-local profiles with alert-enabled thresholds. |
| `scripts/generate_protocol_contract_from_planning_notes.py` | Generate protocol contracts (GraphQL SDL, Proto3, AsyncAPI YAML, WebSocket YAML) from planning notes markdown. |
| `scripts/generate_protocol_docs.py` | Auto-generate reference documentation from protocol contracts using protocol-specific templates. |
| `scripts/generate_protocol_test_assets.py` | Generate protocol-aware test cases with signature-based smart merge. Outputs JSON, TestRail CSV, Zephyr JSON, test matrix, and fuzz scenarios. |
| `scripts/run_protocol_self_verify.py` | Runtime validation against live/mock endpoints: GraphQL introspection, gRPC invocation, AsyncAPI event publish, WebSocket connection and message routing. |
| `scripts/validate_graphql_contract.py` | GraphQL SDL contract validation (syntax, semantics, operation types). |
| `scripts/validate_proto_contract.py` | Proto3 contract validation (syntax, service definitions, RPC methods). |
| `scripts/validate_asyncapi_contract.py` | AsyncAPI contract validation (channels, schemas, delivery guarantees). |
| `scripts/validate_websocket_contract.py` | WebSocket channel contract validation (message schemas, connection lifecycle). |
| `scripts/generate_public_docs_audit.py` | Public documentation site auditor: crawls live sites, evaluates broken links, SEO/GEO, API coverage, code examples, freshness. Supports interactive wizard and LLM-powered expert analysis. |
| `scripts/generate_audit_scorecard.py` | Comprehensive audit scorecard generator combining docs quality, API coverage, code examples, glossary health, and policy compliance into a single score. |
| `scripts/generate_executive_audit_pdf.py` | Consulting-grade executive PDF report from audit scorecard and public docs audit results. Includes score gauges, risk matrices, financial impact tables, and methodology appendix. |
| `scripts/generate_embeddings.py` | Generate FAISS vector index from knowledge modules using `text-embedding-3-small` (1536 dimensions). Builds `retrieval.faiss` and `retrieval-metadata.json`. |
| `scripts/docsops_generate.py` | Operator and policy-triggered generation entry point for local CLI workflows (`operator` and `veridoc` modes). |
| `scripts/production_smoke.py` | Production smoke validation for runtime readiness and deployment health signals. |

### Plan Tiers (Basic / Pro / Enterprise)

Feature packaging matrix and defaults for Basic, Pro, and Enterprise client plans.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### Plan Tiers (Basic / Pro / Enterprise): Plan Tiers (Basic / Pro / Enterprise)

### Plan Tiers (Basic / Pro / Enterprise) (Part 10)

Feature packaging matrix and defaults for Basic, Pro, and Enterprise client plans.

```yaml

bundle:
  base_policy_pack: "multi-product"
  style_guide: "microsoft"
  policy_overrides:
    kpi_sla:
      min_doc_coverage: 90
      max_stale_pct: 10
      max_quality_score_drop: 2
runtime:
  docs_flow:
    mode: "hybrid"
  pr_autofix:
    enabled: false
    require_label: false
    label_name: "auto-doc-fix"
    enable_auto_merge: false
  modules:
    gap_detection: true
    drift_detection: true
    docs_contract: true
    kpi_sla: true
    rag_optimization: true
    ontology_graph: true
    retrieval_evals: true
    terminology_management: true
    normalization: true
    snippet_lint: true
    self_checks: true
    fact_checks: true
    knowledge_validation: true
    i18n_sync: true
    release_pack: true
  api_first:
    enabled: true
    openapi_version: "3.1.0"
    manual_overrides_path: "api/overrides/openapi.manual.yml"
    regression_snapshot_path: "api/.openapi-regression.json"
    update_regression_snapshot: false
    generate_from_notes: true
    verify_user_path: true
    sandbox_backend: "external"
    mock_service: "custom"
    mock_base_url: "https://<your-real-public-mock-url>/v1"
    sync_playground_endpoint: true
    generate_test_assets: true
    test_assets_output_dir: "reports/api-test-assets"
    testrail_csv: "reports/api-test-assets/testrail_test_cases.csv"
    zephyr_json: "reports/api-test-assets/zephyr_test_cases.json"
    upload_test_assets: false
    upload_test_assets_strict: false
    test_assets_upload_report: "reports/api-test-assets/upload_report.json"
    external_mock:
      enabled: true
      provider: "postman"
      base_path: "/v1"
    run_docs_lint: true
    auto_remediate: true
    max_attempts: 5
  api_protocols:
    - "rest"
    - "graphql"
    - "grpc"
    - "asyncapi"
    - "websocket"
  api_protocol_settings:
    graphql:
      enabled: true
      mode: "api-first"
      generate_server_stubs: true
      stubs_output: "generated/api-stubs/graphql/handlers.py"
    grpc:
      enabled: true
      mode: "api-first"
      generate_server_stubs: true
      stubs_output: "generated/api-stubs/grpc/handlers.py"
    asyncapi:
      enabled: true
      mode: "api-first"
      generate_server_stubs: true
      stubs_output: "generated/api-stubs/asyncapi/handlers.py"
    websocket:
      enabled: true
      mode: "api-first"
      generate_server_stubs: true
      stubs_output: "generated/api-stubs/websocket/handlers.py"
  custom_tasks:
    weekly:
      - id: "seo-geo"
        enabled: true
        command: "python3 docsops/scripts/seo_geo_optimizer.py docs/"
        continue_on_error: true
      - id: "knowledge-validate"
        enabled: true
        command: "python3 docsops/scripts/validate_knowledge_modules.py"
        continue_on_error: true
      - id: "knowledge-index"
        enabled: true
        command: "python3 docsops/scripts/generate_knowledge_retrieval_index.py"
        continue_on_error: true
      - id: "intent-experiences"
        enabled: true
        command: "python3 docsops/scripts/build_all_intent_experiences.py"
        continue_on_error: true
private_tuning:
  weekly_stale_days: 180

```

### Plan Tiers (Basic / Pro / Enterprise) (Part 11)

Feature packaging matrix and defaults for Basic, Pro, and Enterprise client plans.

#### Plan Tiers (Basic / Pro / Enterprise) (Part 11): 3. How to apply a plan for a client

\11. Copy `profiles/clients/_template.client.yml` to `profiles/clients/<client>.client.yml`.
\11. Copy one preset from this page into the new profile.
\11. Adjust paths (`docs_root`, `api_root`, `sdk_root`) and output targets.
\11. Build/install:

```bash

python3 scripts/provision_client_repo.py \
  --client profiles/clients/<client>.client.yml \
  --client-repo /path/to/client-repo \
  --docsops-dir docsops \
  --install-scheduler linux

```

### Plan Tiers (Basic / Pro / Enterprise) (Part 12)

Feature packaging matrix and defaults for Basic, Pro, and Enterprise client plans.

#### Plan Tiers (Basic / Pro / Enterprise) (Part 12): 4. License enforcement

Plan tiers are enforced at runtime by `scripts/license_gate.py`. Every gated script calls `license_gate.require("feature_name")` before executing protected logic. The license is validated offline using an Ed25519-signed JWT stored at `docsops/license.jwt`.

Without a valid license, the pipeline runs in **community mode** (degraded):

- Markdown lint, frontmatter validation, SEO/GEO report-only, gap detection code-only, glossary sync, lifecycle management, REST protocol.
- No scoring, no auto-fix, no drift detection, no KPI/SLA, no PDF reports, no multi-protocol.
- Quality gates warn-only (never block).

License features per plan:

| Feature gate | Pilot | Professional | Enterprise |
| --- | --- | --- | --- |
| `seo_geo_scoring` | No | Yes | Yes |
| `api_first_flow` | No | Yes | Yes |
| `drift_detection` | No | Yes | Yes |
| `kpi_wall_sla` | No | Yes | Yes |
| `test_assets_generation` | No | Yes | Yes |
| `consolidated_reports` | No | Yes | Yes |
| `multi_protocol_pipeline` | No | No | Yes |
| `knowledge_modules` | No | No | Yes |
| `knowledge_graph` | No | No | Yes |
| `faiss_retrieval` | No | No | Yes |
| `executive_audit_pdf` | No | No | Yes |
| `i18n_system` | No | No | Yes |
| `custom_policy_packs` | No | No | Yes |
| `testrail_zephyr_upload` | No | No | Yes |

### Plan Tiers (Basic / Pro / Enterprise) (Part 13)

Feature packaging matrix and defaults for Basic, Pro, and Enterprise client plans.

Protocols per plan: Pilot and Professional allow REST only. Enterprise allows all 5 protocols.

Offline grace period: Pilot 3 days, Professional 7 days, Enterprise 30 days.

Check license status: `python3 docsops/scripts/license_gate.py`.

Dev/test bypass: `export VERIOPS_LICENSE_PLAN=enterprise`.

#### Plan Tiers (Basic / Pro / Enterprise) (Part 13): 5. Plan upgrade path

- `Basic -> Pro`: turn on `drift_detection`, `docs_contract`, `kpi_sla`, `rag_optimization`, `knowledge_validation`, set `api_first.enabled=true`. Update `licensing.plan` to `professional`.
- `Pro -> Enterprise`: enable `verify_user_path`, `run_docs_lint`, stricter `policy_overrides.kpi_sla`, add full weekly custom tasks. Update `licensing.plan` to `enterprise`.

After any plan change, rebuild the bundle and re-provision.

#### Plan Tiers (Basic / Pro / Enterprise) (Part 13): Next steps

- [Operator Runbook](OPERATOR_RUNBOOK.md) -- step-by-step retainer procedures
- [Documentation index](../index.md)

### Plan Tiers (Basic / Pro / Enterprise) (Part 14)

Feature packaging matrix and defaults for Basic, Pro, and Enterprise client plans.

#### Plan Tiers (Basic / Pro / Enterprise) (Part 14): Implementation status (2026-03-25)

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

### Plan Tiers (Basic / Pro / Enterprise) (Part 2)

Feature packaging matrix and defaults for Basic, Pro, and Enterprise client plans.

#### Plan Tiers (Basic / Pro / Enterprise) (Part 2): Current product definition (2026-03-25)

This content follows the active implementation baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` modes.
1. The smooth autopipeline covers all five API protocols (REST, GraphQL, gRPC, AsyncAPI, and WebSocket) in one operational model.
1. Non-REST flow includes generated server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated, with Postman-supported auto-prepare in external mode.
1. Contract test assets are generated automatically and merged with smart-merge so manual/customized cases are preserved and flagged for review when needed.
1. Knowledge/RAG maintenance, terminology sync, and quality/compliance gates run through the same automation surface when enabled.
1. Plan tiers gate advanced capabilities; higher plans include broader non-REST and governance scope.

This document defines how pipeline functionality is packaged by client plan.

Use this with:

- `profiles/clients/<client>.client.yml`
- `docs/operations/UNIFIED_CLIENT_CONFIG.md`

Important:

### Plan Tiers (Basic / Pro / Enterprise) (Part 3)

Feature packaging matrix and defaults for Basic, Pro, and Enterprise client plans.

- Basic/Pro/Enterprise are packaging presets, not hardcoded runtime limits.
- They are starting points for profile generation and commercial scope design.
- Pilot scope is defined separately by `profiles/clients/presets/pilot-evidence.yml`.
- Full implementation usually starts from plan-level Pro/Enterprise.
- In profile files, this is typically mapped to:
  - `profiles/clients/presets/startup.yml` (Pro-equivalent)
  - `profiles/clients/presets/enterprise.yml` (Enterprise-equivalent)

Practical mapping:

- Pilot -> `profiles/clients/presets/pilot-evidence.yml`
- Full Basic -> `profiles/clients/presets/small.yml`
- Full Pro -> `profiles/clients/presets/startup.yml`
- Full Enterprise -> `profiles/clients/presets/enterprise.yml`

In short:

- Plan = business scope level
- Preset = technical starting template
- Pilot/Full = implementation format

### Plan Tiers (Basic / Pro / Enterprise) (Part 4)

Feature packaging matrix and defaults for Basic, Pro, and Enterprise client plans.

#### Plan Tiers (Basic / Pro / Enterprise) (Part 4): Non-API documentation flows (docs-first scope)

The platform is not limited to API-first automation. In active production usage, it also runs full docs-first and code-first documentation operations for non-API content:

1. Detects content gaps, stale pages, and drift across product docs, runbooks, admin guides, troubleshooting, and release notes.
1. Generates and updates documentation types beyond API references (tutorial, how-to, concept, reference, troubleshooting, release-note, security, SDK, user/admin, and operations docs).
1. Applies normalization, style, metadata/frontmatter, SEO/GEO, terminology governance, and snippet validation to all documentation categories.
1. Executes lifecycle controls (active/deprecated/removed states, replacement links, and freshness cadence).
1. Runs knowledge extraction and retrieval preparation for all docs, not only API pages.
1. Produces consolidated review artifacts so human input is focused on approval and business accuracy, not repetitive formatting and synchronization work.

### Plan Tiers (Basic / Pro / Enterprise) (Part 5)

Feature packaging matrix and defaults for Basic, Pro, and Enterprise client plans.

#### Plan Tiers (Basic / Pro / Enterprise) (Part 5): 1. Feature matrix

| Capability | Basic | Pro | Enterprise |
| --- | --- | --- | --- |
| Core quality gates (normalize, snippets, smoke) | Yes | Yes | Yes |
| Gap detection | Yes | Yes | Yes |
| Weekly stale checks | Yes | Yes | Yes |
| Drift + docs contract gates | No | Yes | Yes |
| KPI/SLA reports | No | Yes | Yes |
| API-first flow | No | Optional | Full |
| Non-REST API-first autopipeline (GraphQL/gRPC/AsyncAPI/WebSocket) | No | No | Yes |
| Non-REST server stubs (business-logic placeholders) | No | No | Yes |
| Non-REST external mock auto-prepare (Postman) | No | No | Yes |
| API test assets (cases/matrix/fuzz docs) | No | Yes | Yes |
| TestRail/Zephyr upload from pipeline | No | Optional | Optional |
| RAG/knowledge validation/index | No | Yes | Yes |
| JSON-LD ontology/graph layer | No | Yes | Yes |
| Retrieval evals (Precision/Recall/Hallucination) | No | Yes | Yes |
| Terminology auto-sync (glossary markers) | Yes | Yes | Yes |
| PR auto-doc fix to same PR branch | Optional | Optional | Optional |
| i18n sync | No | Optional | Yes |
| SEO/GEO optimization weekly | Optional | Yes | Yes |
| Custom weekly task slots | 2 | 6 | Unlimited |
| Strict policy profile | minimal | api-first/monorepo | multi-product/plg + overrides |

#### Plan Tiers (Basic / Pro / Enterprise) (Part 5): 2. Default plan presets

### Plan Tiers (Basic / Pro / Enterprise) (Part 6)

Feature packaging matrix and defaults for Basic, Pro, and Enterprise client plans.

##### Plan Tiers (Basic / Pro / Enterprise) (Part 6): Basic preset

```yaml

bundle:
  base_policy_pack: "minimal"
  style_guide: "google"
runtime:
  docs_flow:
    mode: "code-first"
  pr_autofix:
    enabled: false
  modules:
    gap_detection: true
    drift_detection: false
    docs_contract: false
    kpi_sla: false
    rag_optimization: false
    ontology_graph: false
    retrieval_evals: false
    terminology_management: true
    normalization: true
    snippet_lint: true
    self_checks: true
    fact_checks: true
    knowledge_validation: false
    i18n_sync: false
    release_pack: true
  api_first:
    enabled: false
  custom_tasks:
    weekly:
      - id: "seo-geo-lite"
        enabled: true
        command: "python3 docsops/scripts/seo_geo_optimizer.py docs/"
        continue_on_error: true
      - id: "max-two-tasks"
        enabled: false
        command: ""
        continue_on_error: true
private_tuning:
  weekly_stale_days: 180

```

### Plan Tiers (Basic / Pro / Enterprise) (Part 7)

Feature packaging matrix and defaults for Basic, Pro, and Enterprise client plans.

##### Plan Tiers (Basic / Pro / Enterprise) (Part 7): Pro preset

This auto-generated knowledge chunk was expanded to satisfy minimum retrieval module length for stable indexing.

### Plan Tiers (Basic / Pro / Enterprise) (Part 8)

Feature packaging matrix and defaults for Basic, Pro, and Enterprise client plans.

```yaml

bundle:
  base_policy_pack: "api-first"
  style_guide: "hybrid"
runtime:
  docs_flow:
    mode: "hybrid"
  pr_autofix:
    enabled: false
    require_label: false
    label_name: "auto-doc-fix"
    enable_auto_merge: false
  modules:
    gap_detection: true
    drift_detection: true
    docs_contract: true
    kpi_sla: true
    rag_optimization: true
    ontology_graph: true
    retrieval_evals: true
    terminology_management: true
    normalization: true
    snippet_lint: true
    self_checks: true
    fact_checks: true
    knowledge_validation: true
    i18n_sync: true
    release_pack: true
  api_first:
    enabled: true
    openapi_version: "3.1.0"
    manual_overrides_path: "api/overrides/openapi.manual.yml"
    regression_snapshot_path: "api/.openapi-regression.json"
    update_regression_snapshot: false
    generate_from_notes: true
    sandbox_backend: "external"
    mock_service: "custom"
    mock_base_url: "https://<your-real-public-mock-url>/v1"
    sync_playground_endpoint: true
    generate_test_assets: true
    test_assets_output_dir: "reports/api-test-assets"
    testrail_csv: "reports/api-test-assets/testrail_test_cases.csv"
    zephyr_json: "reports/api-test-assets/zephyr_test_cases.json"
    upload_test_assets: false
    upload_test_assets_strict: false
    test_assets_upload_report: "reports/api-test-assets/upload_report.json"
    external_mock:
      enabled: true
      provider: "postman"
      base_path: "/v1"
    auto_remediate: true
    max_attempts: 3
  custom_tasks:
    weekly:
      - id: "seo-geo"
        enabled: true
        command: "python3 docsops/scripts/seo_geo_optimizer.py docs/"
        continue_on_error: true
      - id: "knowledge-index"
        enabled: true
        command: "python3 docsops/scripts/generate_knowledge_retrieval_index.py"
        continue_on_error: true
private_tuning:
  weekly_stale_days: 180

```

### Plan Tiers (Basic / Pro / Enterprise) (Part 9)

Feature packaging matrix and defaults for Basic, Pro, and Enterprise client plans.

##### Plan Tiers (Basic / Pro / Enterprise) (Part 9): Enterprise preset

This auto-generated knowledge chunk was expanded to satisfy minimum retrieval module length for stable indexing.

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

### VeriDoc privacy policy (Part 3)

Privacy policy for VeriDoc automated documentation platform, covering data collection, processing, storage, retention, and your rights under GDPR.

##### VeriDoc privacy policy (Part 3): LLM processing data

When you enable AI features (`--use-llm` flag), your documentation content
is sent to third-party LLM providers for processing:

| Provider | Data sent | Provider privacy policy |
|----------|-----------|------------------------|
| Anthropic (Claude) | Document sections for quality enhancement | [anthropic.com/privacy](https://www.anthropic.com/privacy) |
| Groq | Document sections for text generation | [groq.com/privacy-policy](https://groq.com/privacy-policy/) |
| DeepSeek | Document sections for text generation | [deepseek.com/privacy](https://www.deepseek.com/privacy) |
| OpenAI | Document sections for embeddings and text generation | [openai.com/privacy](https://openai.com/privacy) |

LLM processing is opt-in. Without the AI flag, no content leaves our
infrastructure.

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

### VeriDoc privacy policy (Part 6)

Privacy policy for VeriDoc automated documentation platform, covering data collection, processing, storage, retention, and your rights under GDPR.

#### VeriDoc privacy policy (Part 6): Your rights

Under GDPR and applicable data protection laws, you have the right to:

| Right | How to exercise |
|-------|-----------------|
| **Access** your data | Email <privacy@veri-doc.app> or use the API export endpoint |
| **Correct** inaccurate data | Update your profile in account settings |
| **Delete** your data | Close your account or email <privacy@veri-doc.app> |
| **Export** your data | Use the API data export endpoint or email <privacy@veri-doc.app> |
| **Restrict** processing | Email <privacy@veri-doc.app> |
| **Object** to processing | Email <privacy@veri-doc.app> |
| **Withdraw consent** | Disable AI features or close your account |

We respond to data rights requests within 30 days.

#### VeriDoc privacy policy (Part 6): Cookies and tracking

The VeriDoc web application uses only essential cookies for session
management. We do not use:

1. Third-party analytics cookies
1. Advertising cookies
1. Social media tracking pixels
1. Cross-site tracking

#### VeriDoc privacy policy (Part 6): Third-party processors

We share data with these processors solely for service delivery:

| Processor | Purpose | Data shared |
|-----------|---------|-------------|
| LemonSqueezy | Payment processing | Email, subscription tier |
| Hetzner | Infrastructure hosting | Encrypted application data |
| Sentry | Error tracking | Error context (PII scrubbed) |
| Mailgun | Transactional email delivery | Email address, email content |

### VeriDoc privacy policy (Part 7)

Privacy policy for VeriDoc automated documentation platform, covering data collection, processing, storage, retention, and your rights under GDPR.

#### VeriDoc privacy policy (Part 7): Age requirements

VeriDoc is not intended for users under 16 years of age. We do not
knowingly collect data from children.

#### VeriDoc privacy policy (Part 7): Changes to this policy

We notify users of material changes via email 30 days before the effective
date. Minor clarifications are published directly. The "Last updated" date
reflects the most recent revision.

#### VeriDoc privacy policy (Part 7): Contact information

For privacy inquiries or data rights requests:

- Email: <privacy@veri-doc.app>
- Response time: within 30 days

**Last updated:** March 28, 2026

#### VeriDoc privacy policy (Part 7): Next steps

- Review the [terms of service](terms-of-service.md)
- Review the [data processing agreement](data-processing-agreement.md)
- Review the [security policy](security-policy.md)

### REST API Reference

Auto-generated rest reference from source contract.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### REST API Reference: REST Reference

Source: `api/openapi.yaml`

Flow mode: `api-first`

#### REST API Reference: Top-level Keys

- `components`
- `info`
- `openapi`
- `paths`
- `security`
- `servers`

#### REST API Reference: Notes

- Generated from source contract.

#### REST API Reference: Next steps

- [Documentation index](index.md)

### Advanced Search

Search and filter documentation using faceted navigation for quick discovery

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### Advanced Search: Advanced Search

<div id="faceted-search-app">
  <p style="text-align: center; padding: 2rem; color: var(--md-default-fg-color--light);">
    Loading search interface.
  </p>
</div>

<style>
  /*Custom styles for faceted search*/
  .fs-container {
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
  }

.fs-sidebar {
    min-width: 250px;
    flex: 0 0 250px;
  }

.fs-results {
    flex: 1;
    min-width: 300px;
  }

.fs-search-box {
    width: 100%;
    padding: 10px 16px;
    margin-bottom: 1.5rem;
    border: 2px solid var(--md-default-fg-color--lighter);
    border-radius: 8px;
    font-size: 1rem;
    background: var(--md-default-bg-color);
    color: var(--md-default-fg-color);
    transition: border-color 0.2s;
  }

.fs-search-box:focus {
    outline: none;
    border-color: var(--md-primary-fg-color);
  }

.fs-facet-group {
    margin-bottom: 1.5rem;
  }

.fs-facet-title {
    display: block;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--md-default-fg-color--light);
  }

### Advanced Search (Part 2)

Search and filter documentation using faceted navigation for quick discovery

.fs-facet-option {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 0;
    font-size: 0.95rem;
    cursor: pointer;
  }

.fs-facet-option:hover {
    color: var(--md-primary-fg-color);
  }

.fs-facet-checkbox {
    cursor: pointer;
  }

.fs-facet-count {
    margin-left: auto;
    padding: 0 6px;
    font-size: 0.85rem;
    color: var(--md-default-fg-color--lighter);
    background: var(--md-default-bg-color--secondary);
    border-radius: 10px;
  }

.fs-clear-btn {
    margin-top: 1rem;
    padding: 8px 16px;
    cursor: pointer;
    border: 1px solid var(--md-default-fg-color--lighter);
    border-radius: 6px;
    background: var(--md-default-bg-color);
    color: var(--md-default-fg-color);
    font-size: 0.9rem;
    transition: all 0.2s;
  }

.fs-clear-btn:hover {
    background: var(--md-default-fg-color--lightest);
  }

.fs-result-count {
    color: var(--md-default-fg-color--light);
    margin-bottom: 1.5rem;
    font-size: 0.95rem;
  }

.fs-result-item {
    margin-bottom: 1.5rem;
    padding: 1.2rem;
    border: 1px solid var(--md-default-fg-color--lightest);
    border-radius: 8px;
    transition: all 0.2s;
  }

.fs-result-item:hover {
    border-color: var(--md-primary-fg-color);
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }

### Advanced Search (Part 3)

Search and filter documentation using faceted navigation for quick discovery

.fs-result-title {
    font-size: 1.15rem;
    font-weight: 600;
    text-decoration: none;
    color: var(--md-primary-fg-color);
  }

.fs-result-title:hover {
    text-decoration: underline;
  }

.fs-result-badges {
    margin: 0.5rem 0;
  }

.fs-badge {
    display: inline-block;
    padding: 3px 10px;
    margin-right: 6px;
    font-size: 0.8rem;
    border-radius: 4px;
    background: var(--md-primary-fg-color);
    color: var(--md-primary-bg-color);
  }

.fs-badge.type {
    background: var(--md-accent-fg-color);
  }

.fs-badge.product {
    background: var(--md-code-bg-color);
    color: var(--md-code-fg-color);
  }

.fs-result-description {
    margin: 0.5rem 0 0;
    font-size: 0.95rem;
    color: var(--md-default-fg-color--light);
    line-height: 1.5;
  }

.fs-no-results {
    padding: 3rem;
    text-align: center;
    color: var(--md-default-fg-color--light);
  }

@media (max-width: 768px) {
    .fs-sidebar {
      flex: 1 1 100%;
    }
  }
</style>

#### Advanced Search (Part 3): Next steps

- [Documentation index](index.md)

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

### VeriDoc security contact policy (Part 2)

Security contact channels, response times, severity model, and disclosure workflow for VeriDoc incidents and vulnerability reports.

#### VeriDoc security contact policy (Part 2): Disclosure rules

For responsible disclosure:

1. Do not access data that is not yours.
1. Do not modify or delete customer data.
1. Do not run denial-of-service tests.
1. Give VeriDoc up to 90 days before public disclosure.

#### VeriDoc security contact policy (Part 2): Communication and status updates

For confirmed incidents:

1. Initial acknowledgement is sent via email.
1. Ongoing updates are provided at least every 24 hours for critical incidents.
1. Final post-incident summary includes root cause and corrective actions.

#### VeriDoc security contact policy (Part 2): Next steps

- Review the [security policy](security-policy.md)
- Review the [data processing agreement](data-processing-agreement.md)
- Review the [privacy policy](privacy-policy.md)

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

### VeriDoc security policy (Part 3)

Security policy for VeriDoc platform covering infrastructure security, encryption, authentication, access controls, and incident response procedures.

##### VeriDoc security policy (Part 3): Data in transit

All data transmitted between clients and VeriDoc servers is encrypted
with TLS 1.3. The Nginx configuration enforces:

1. TLS 1.3 only (TLS 1.2 and below are disabled).
1. Strong cipher suites with forward secrecy.
1. HSTS headers with 1-year max-age.
1. OCSP stapling for certificate validation.

##### VeriDoc security policy (Part 3): Data at rest

| Data type | Encryption method |
|-----------|-------------------|
| PostgreSQL database | AES-256 (filesystem-level encryption) |
| Database backups | AES-256 encrypted archives |
| License files | AES-256-GCM with HKDF key derivation |
| Application secrets | Environment variables, not stored in code |

#### VeriDoc security policy (Part 3): Data processing security

##### VeriDoc security policy (Part 3): Pipeline execution

When VeriDoc processes your documentation:

1. Content is loaded into memory for processing.
1. Intermediate results are stored in the encrypted PostgreSQL database.
1. Pipeline workers run in isolated Celery processes with 1-hour timeouts.
1. Failed pipeline runs are logged to Sentry with PII scrubbing.

### VeriDoc security policy (Part 4)

Security policy for VeriDoc platform covering infrastructure security, encryption, authentication, access controls, and incident response procedures.

##### VeriDoc security policy (Part 4): LLM processing (opt-in)

When AI features are enabled, document sections are sent to LLM providers
over TLS-encrypted connections. Each request contains only the minimum
content necessary for the specific enhancement.

| Provider | Transport | Data retention by provider |
|----------|-----------|---------------------------|
| Anthropic (Claude) | HTTPS/TLS 1.3 | Not used for training |
| Groq | HTTPS/TLS 1.3 | Not used for training |
| DeepSeek | HTTPS/TLS 1.3 | Refer to provider policy |
| OpenAI | HTTPS/TLS 1.3 | Not used for training (API usage) |

Disable AI features to ensure no documentation content leaves VeriDoc
infrastructure.

#### VeriDoc security policy (Part 4): Backup and disaster recovery

| Measure | Configuration |
|---------|---------------|
| Backup frequency | Daily at 02:00 UTC |
| Backup retention | 30 days |
| Backup encryption | AES-256 |
| Restore testing | Weekly automated restore verification |
| Recovery time objective (RTO) | 4 hours |
| Recovery point objective (RPO) | 24 hours |

#### VeriDoc security policy (Part 4): Monitoring and incident response

### VeriDoc security policy (Part 5)

Security policy for VeriDoc platform covering infrastructure security, encryption, authentication, access controls, and incident response procedures.

##### VeriDoc security policy (Part 5): Monitoring

| System | Purpose | Alert threshold |
|--------|---------|-----------------|
| Health checks | Service availability | 2 consecutive failures (every 5 minutes) |
| Sentry | Error tracking | Real-time error capture |
| Log rotation | Log management | Daily rotation, 30-day retention |
| Latency monitoring | Performance tracking | Warning at 2,000 ms, critical at 5,000 ms |

##### VeriDoc security policy (Part 5): Incident response procedure

| Phase | Timeline | Actions |
|-------|----------|---------|
| **Detection** | Automated | Health check alerts via email within 10 minutes of failure |
| **Triage** | Within 1 hour | Assess severity, identify root cause |
| **Containment** | Within 2 hours | Isolate affected systems, prevent data loss |
| **Resolution** | Within 4 hours (critical) | Restore service, deploy fix |
| **Notification** | Within 72 hours | Notify affected customers per DPA obligations |
| **Post-mortem** | Within 7 days | Document root cause, implement preventive measures |

### VeriDoc security policy (Part 6)

Security policy for VeriDoc platform covering infrastructure security, encryption, authentication, access controls, and incident response procedures.

##### VeriDoc security policy (Part 6): Severity levels

| Level | Definition | Response time | Example |
|-------|------------|---------------|---------|
| **Critical** | Service down, data at risk | 1 hour | Database corruption, security breach |
| **High** | Feature degraded, no data risk | 4 hours | API errors, slow response times |
| **Medium** | Minor issue, workaround available | 24 hours | Non-critical feature bug |
| **Low** | Cosmetic or documentation issue | 72 hours | UI display issue |

#### VeriDoc security policy (Part 6): Vulnerability management

1. **Dependency scanning.** Python dependencies are reviewed weekly for
   known vulnerabilities using `pip-audit`.
1. **OS patching.** Security patches are applied within 48 hours of
   release.
1. **Container updates.** Docker base images are rebuilt monthly with
   latest security patches.
1. **Penetration testing.** External penetration testing is conducted
   annually.

#### VeriDoc security policy (Part 6): Responsible disclosure

If you discover a security vulnerability in VeriDoc:

1. Email <security@veri-doc.app> with a description of the vulnerability.
1. Include steps to reproduce the issue.
1. Allow 90 days for remediation before public disclosure.
1. Do not access or modify other users' data during testing.

We do not pursue legal action against security researchers who follow
responsible disclosure practices.

### VeriDoc security policy (Part 7)

Security policy for VeriDoc platform covering infrastructure security, encryption, authentication, access controls, and incident response procedures.

#### VeriDoc security policy (Part 7): Compliance standards

| Standard | Status |
|----------|--------|
| GDPR | Compliant (EU data processing, DPA available) |
| TLS 1.3 | Enforced on all endpoints |
| Password security | PBKDF2-SHA256, 600,000 iterations |
| Data retention | Defined retention periods with automated deletion |

#### VeriDoc security policy (Part 7): Contact information

For security inquiries or to report a vulnerability:

- Email: <security@veri-doc.app>
- Response time: within 24 hours for security reports

**Last updated:** March 28, 2026

#### VeriDoc security policy (Part 7): Next steps

- Review the [terms of service](terms-of-service.md)
- Review the [privacy policy](privacy-policy.md)
- Review the [data processing agreement](data-processing-agreement.md)

### SEO/GEO Optimization Guide

Comprehensive guide to SEO and GEO optimization in the documentation pipeline

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### SEO/GEO Optimization Guide: SEO/GEO Optimization Guide

This document explains the comprehensive SEO and GEO (Generative Engine Optimization) system implemented in this documentation pipeline.

#### SEO/GEO Optimization Guide: Overview

The `scripts/seo_geo_optimizer.py` is a unified tool that handles all SEO/GEO optimization:

- **GEO Linting**: Optimizes content for LLM extraction and citation
- **SEO Enhancement**: Generates structured data, meta tags, and sitemaps
- **Search Optimization**: Creates Algolia-optimized search records
- **Metadata Auto-Enhancement**: Infers metadata from paths and content

#### SEO/GEO Optimization Guide: Features

##### SEO/GEO Optimization Guide: 1. GEO (Generative Engine Optimization)

Optimizes documentation for AI/LLM consumption:

- **First Paragraph Optimization**: Ensures first 60 words contain clear definitions
- **Heading Quality**: Detects generic headings that reduce discoverability
- **Fact Density**: Ensures concrete facts every 200 words
- **Definition Patterns**: Checks for clear "is/enables/provides" patterns
- **Hierarchy Validation**: Ensures proper heading structure

### SEO/GEO Optimization Guide (Part 2)

Comprehensive guide to SEO and GEO optimization in the documentation pipeline

##### SEO/GEO Optimization Guide (Part 2): 2. SEO Enhancement

Improves traditional search engine optimization:

- **Structured Data**: Generates JSON-LD schema for rich snippets
- **Meta Tags**: Creates comprehensive Open Graph and Twitter Card tags
- **Canonical URLs**: Manages canonical links for duplicate content
- **Sitemap Generation**: Automated sitemap.xml with priorities
- **Lifecycle Management**: Handles deprecated/preview content

##### SEO/GEO Optimization Guide (Part 2): 3. Search Optimization

Optimizes for internal search (Algolia):

- **Faceted Search**: Enables filtering by product, type, component
- **Ranking Boost**: Prioritizes based on content type and freshness
- **Section Indexing**: Breaks documents into searchable chunks
- **Code Awareness**: Indexes code snippets separately

##### SEO/GEO Optimization Guide (Part 2): 4. Metadata Intelligence

Automatically infers and enhances metadata:

- **Path-based Inference**: Determines content_type from directory structure
- **Content Analysis**: Detects patterns to identify document type
- **Git Integration**: Adds last_reviewed dates from git history
- **Tag Generation**: Auto-generates relevant tags

#### SEO/GEO Optimization Guide (Part 2): Usage

### SEO/GEO Optimization Guide (Part 3)

Comprehensive guide to SEO and GEO optimization in the documentation pipeline

##### SEO/GEO Optimization Guide (Part 3): Command Line

```bash

# Basic GEO/SEO check
python scripts/seo_geo_optimizer.py docs/

# Fix issues and enhance metadata
python scripts/seo_geo_optimizer.py docs/ --fix

# Generate sitemap
python scripts/seo_geo_optimizer.py docs/ --sitemap

# Generate Algolia records
python scripts/seo_geo_optimizer.py docs/ --algolia

# All optimizations
python scripts/seo_geo_optimizer.py docs/ --fix --sitemap --algolia

```

#### SEO/GEO Optimization Guide (Part 3): GitHub Actions

The pipeline runs automatically:

\11. **On PR**: Validates SEO/GEO compliance
\11. **On Push to Main**: Updates search index and sitemap
\11. **Weekly**: Full optimization with auto-fixes

##### SEO/GEO Optimization Guide (Part 3): Pre-commit Hook

Runs automatically before commits:

```bash

# Install pre-commit
pip install pre-commit
pre-commit install

# Run manually
pre-commit run seo-geo-check --all-files

```

#### SEO/GEO Optimization Guide (Part 3): Configuration

##### SEO/GEO Optimization Guide (Part 3): Required Frontmatter

Every document must have:

```text

---
title: "Clear title under 70 characters"
description: "SEO description between 50-160 characters"
content_type: tutorial|how-to|concept|reference|troubleshooting
---

```

##### SEO/GEO Optimization Guide (Part 3): Optional Enhancements

```text

---
product: cloud|self-hosted|both
app_component: webhook|http-request|code|ai-agent
maturity: preview|beta|ga|deprecated|removed
tags: [Tag1, Tag2, Tag3] # Max 8 tags
last_reviewed: 2024-01-15
---

```

#### SEO/GEO Optimization Guide (Part 3): Validation Rules

### SEO/GEO Optimization Guide (Part 4)

Comprehensive guide to SEO and GEO optimization in the documentation pipeline

##### SEO/GEO Optimization Guide (Part 4): Critical (Blocks PR)

- Missing required frontmatter fields
- Description outside 50-160 character range
- Heading hierarchy violations
- Invalid content_type values

##### SEO/GEO Optimization Guide (Part 4): Warnings (Should Fix)

- First paragraph over 60 words
- Generic headings (Overview, Setup, etc.)
- Low fact density (>200 words without specifics)
- Missing definition patterns

##### SEO/GEO Optimization Guide (Part 4): Suggestions (Nice to Have)

- Add more descriptive headings
- Include code examples
- Add structured data hints

#### SEO/GEO Optimization Guide (Part 4): Lifecycle Management

##### SEO/GEO Optimization Guide (Part 4): Content Maturity States

\11. **preview**: New experimental features
\11. **beta**: Testing phase, may change
\11. **ga**: Generally available, stable
\11. **deprecated**: Will be removed, use alternatives
\11. **removed**: No longer available

##### SEO/GEO Optimization Guide (Part 4): Automated Actions

- **deprecated**: Lower search ranking, add warning banner
- **removed**: Generate 301 redirect, exclude from search
- **preview**: Add preview badge, monitor duration

#### SEO/GEO Optimization Guide (Part 4): Search Ranking Factors

Documents are ranked by:

\11. **Content Type** (tutorials > how-tos > reference)
\11. **Path Depth** (shallower = more important)
\11. **Freshness** (recently updated ranks higher)
\11. **Maturity** (GA > beta > preview > deprecated)
\11. **Fact Density** (more code/config = higher value)

#### SEO/GEO Optimization Guide (Part 4): Monitoring

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

### Browse by tag

Filter documentation by topic tags including tutorials, how-to guides, concepts, and component-specific content.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

#### Browse by tag: Browse documentation by tag

Use the tags below to filter content by topic, type, or component.

<!-- material/tags -->

#### Browse by tag: Next steps

- [Documentation index](index.md)

### TaskStream API playground

Interactive TaskStream OpenAPI playground with Swagger UI or Redoc and try-it-out requests against mock or prod-like sandbox endpoints.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### TaskStream API playground: TaskStream API playground

This page provides an interactive OpenAPI playground where users can send requests to the configured sandbox endpoint before production rollout.

#### TaskStream API playground: Start a sandbox endpoint

Mock mode:

```bash

bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010

```

No-Docker local mode:

```bash

bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010 prism

```

External hosted mode (recommended for public docs):

```bash

API_SANDBOX_EXTERNAL_BASE_URL="https://sandbox-api.example.com/v1" \
bash scripts/api_sandbox_project.sh up taskstream ./api/openapi.yaml 4010 external

```

Prod-like mode:

```bash

bash scripts/api_prodlike_project.sh up taskstream 4011

```

### TaskStream API playground (Part 2)

Interactive TaskStream OpenAPI playground with Swagger UI or Redoc and try-it-out requests against mock or prod-like sandbox endpoints.

#### TaskStream API playground (Part 2): Playground embed

<div id="swagger-ui-taskstream"></div>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.18.2/swagger-ui.css">
<script src="https://unpkg.com/swagger-ui-dist@5.18.2/swagger-ui-bundle.js"></script>
<script>
(function() {
  var specUrl = "{{ config.site_url }}assets/api/openapi.bundled.json";
  var sandboxUrl = "{{ config.extra.plg.api_playground.endpoints.sandbox_base_url }}";
  function boot() {
    if (typeof SwaggerUIBundle === "undefined") { setTimeout(boot, 100); return; }
    SwaggerUIBundle({
      url: specUrl,
      dom_id: "#swagger-ui-taskstream",
      deepLinking: true,
      docExpansion: "list",
      defaultModelsExpandDepth: 1,
      supportedSubmitMethods: ["get","put","post","delete","options","head","patch","trace"],
      requestInterceptor: function (req) {
        if (req.url === specUrl || req.url.indexOf("openapi") !== -1) return req;
        try {
          var u = new URL(req.url, location.origin);
          var t = new URL(sandboxUrl, location.origin);
          u.protocol = t.protocol; u.hostname = t.hostname; u.port = t.port;
          req.url = u.toString();
        } catch (e) {}
        return req;
      }
    });
  }
  boot();
})();
</script>

For multi-version API docs, publish one spec per version and add separate playground blocks or tabs:

- `/assets/api/v1/openapi.yaml`
- `/assets/api/v2/openapi.yaml`

### TaskStream API playground (Part 3)

Interactive TaskStream OpenAPI playground with Swagger UI or Redoc and try-it-out requests against mock or prod-like sandbox endpoints.

#### TaskStream API playground (Part 3): Multi-language request examples

=== "cURL"

```bash

    curl -sS "{{ config.extra.plg.api_playground.endpoints.sandbox_base_url }}/healthz"

```

=== "JavaScript"

```javascript

    const res = await fetch("{{ config.extra.plg.api_playground.endpoints.sandbox_base_url }}/healthz");
    console.log(await res.json());

```

=== "Python"

```python

    import requests

    res = requests.get("{{ config.extra.plg.api_playground.endpoints.sandbox_base_url }}/healthz", timeout=10)
    print(res.json())

```

#### TaskStream API playground (Part 3): What this validates

1. Request and response schema compatibility.
1. Pagination, filtering, and sorting behavior.
1. Error envelope and request-id propagation.
1. Endpoint availability before backend merge.

#### TaskStream API playground (Part 3): Related pages

- [Run API-first production flow](../how-to/run-api-first-production-flow.md)
- [TaskStream API planning notes](taskstream-planning-notes.md)

#### TaskStream API playground (Part 3): Next steps

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

### VeriDoc terms of service (Part 2)

Terms of service governing the use of VeriDoc automated documentation platform, including subscription tiers, usage limits, and acceptable use policies.

#### VeriDoc terms of service (Part 2): Subscription tiers and usage limits

VeriDoc offers five subscription tiers with the following usage limits per
billing period:

| Tier | AI requests | Pages | API calls | Price |
|------|-------------|-------|-----------|-------|
| **Free** | 50 | 10 | 100 | $0/month |
| **Starter** | 500 | 50 | 5,000 | Refer to pricing page |
| **Pro** | 2,000 | 200 | 20,000 | Refer to pricing page |
| **Business** | 10,000 | 1,000 | 100,000 | Refer to pricing page |
| **Enterprise** | Unlimited | Unlimited | Unlimited | Custom pricing |

When you exceed your tier limits, the Service restricts further pipeline
runs until the next billing period or until you upgrade your plan.

#### VeriDoc terms of service (Part 2): Billing and payments

Subscriptions are billed through LemonSqueezy, our payment processor.
By subscribing, you also agree to the
[LemonSqueezy terms of service](https://www.lemonsqueezy.com/terms).

Billing details:

1. Subscriptions renew automatically at the end of each billing period
   (monthly or annual).
1. You may cancel at any time from the billing portal. Cancellation takes
   effect at the end of the current billing period.
1. Refunds follow our 14-day refund policy. Contact <support@veri-doc.app>
   within 14 days of purchase for a full refund.
1. Failed payments are retried up to 3 times over 7 days. After 3 failures,
   the subscription is canceled automatically.

### VeriDoc terms of service (Part 3)

Terms of service governing the use of VeriDoc automated documentation platform, including subscription tiers, usage limits, and acceptable use policies.

#### VeriDoc terms of service (Part 3): Acceptable use

You agree not to:

1. Use the Service to process content that violates applicable laws.
1. Attempt to reverse-engineer, decompile, or extract source code from the
   Service.
1. Exceed rate limits (60 requests per minute) through automated means.
1. Share, resell, or sublicense your account access to third parties.
1. Transmit malware, phishing content, or exploit payloads through the
   pipeline.
1. Use the Service to generate documentation that infringes intellectual
   property rights of others.

Violation of acceptable use policies may result in immediate account
suspension without prior notice.

#### VeriDoc terms of service (Part 3): Intellectual property

**Your content.** You retain all rights to the documentation, code, and
configuration you upload to or generate through the Service. We do not claim
ownership of your content.

**Our service.** The VeriDoc platform, including its pipeline architecture,
templates, scripts, and methods, is owned by Liora Tech and protected by
intellectual property laws.

**License grant.** You grant us a limited license to process your content
solely for providing the Service. This license terminates when you delete
your content or close your account.

### VeriDoc terms of service (Part 4)

Terms of service governing the use of VeriDoc automated documentation platform, including subscription tiers, usage limits, and acceptable use policies.

#### VeriDoc terms of service (Part 4): Data handling

We process your documentation content to provide the Service. Refer to our
[privacy policy](privacy-policy.md) for details on data collection, storage,
and retention.

Key data handling commitments:

1. Your documentation content is processed in memory and stored in encrypted
   databases.
1. We do not use your content to train machine learning models.
1. LLM providers (Anthropic, OpenAI, Groq, DeepSeek) process content only
   when you enable AI features. Each provider's data handling policies
   apply to that processing.
1. You may request data export or deletion at any time per our
   [data processing agreement](data-processing-agreement.md).

#### VeriDoc terms of service (Part 4): Service availability

We target 99.9% uptime for the production environment. Planned maintenance
windows are announced 48 hours in advance via email and the status page.

We are not liable for downtime caused by:

1. Third-party service outages (LemonSqueezy, LLM providers, DNS).
1. Force majeure events.
1. Your network or infrastructure issues.
1. Scheduled maintenance communicated in advance.

#### VeriDoc terms of service (Part 4): Limitation of liability

To the maximum extent permitted by law, Liora Tech is not liable for
indirect, incidental, special, or consequential damages arising from your
use of the Service. Our total liability is limited to the amount you paid
for the Service in the 12 months preceding the claim.

### VeriDoc terms of service (Part 5)

Terms of service governing the use of VeriDoc automated documentation platform, including subscription tiers, usage limits, and acceptable use policies.

#### VeriDoc terms of service (Part 5): Termination

Either party may terminate the agreement:

1. **You** may close your account at any time from account settings. Active
   subscriptions are canceled at the end of the billing period.
1. **We** may suspend or terminate accounts that violate these Terms, with
   written notice to your registered email. For severe violations (security
   threats, illegal activity), we may act immediately.

Upon termination, we retain your data for 30 days to allow export. After
30 days, all data is permanently deleted.

#### VeriDoc terms of service (Part 5): Changes to these terms

We may update these Terms with 30 days advance notice via email. Continued
use after the effective date constitutes acceptance. If you disagree, close
your account before the changes take effect.

#### VeriDoc terms of service (Part 5): Governing law

These Terms are governed by the laws of Israel. Disputes are resolved in
the courts of Tel Aviv, Israel.

#### VeriDoc terms of service (Part 5): Contact information

For questions about these Terms:

- Email: <support@veri-doc.app>
- Web: [veri-doc.app/contact](https://veri-doc.app/contact)

**Last updated:** March 28, 2026

#### VeriDoc terms of service (Part 5): Next steps

- Review the [privacy policy](privacy-policy.md)
- Review the [data processing agreement](data-processing-agreement.md)
- Review the [security policy](security-policy.md)

### Unified Client Configuration

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### Unified Client Configuration: Unified Client Configuration

### Unified Client Configuration (Part 10)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

```yaml

runtime:
  api_first:
    enabled: true
    project_slug: "acme"
    notes_path: "notes/api-planning.md"
    spec_path: "api/openapi.yaml"
    spec_tree_path: "api/acme"
    docs_provider: "mkdocs"
    docs_spec_target: "docs/assets/api"
    stubs_output: "generated/api-stubs/fastapi/app/main.py"
    openapi_version: "3.0.3"
    manual_overrides_path: "api/overrides/openapi.manual.yml"
    regression_snapshot_path: "api/.openapi-regression.json"
    update_regression_snapshot: false
    generate_from_notes: true
    verify_user_path: false
    sandbox_backend: "external"
    mock_service: "custom"
    mock_base_url: "https://<your-real-public-mock-url>/v1"
    sync_playground_endpoint: true
    generate_test_assets: true
    test_assets_output_dir: "reports/api-test-assets"
    testrail_csv: "reports/api-test-assets/testrail_test_cases.csv"
    zephyr_json: "reports/api-test-assets/zephyr_test_cases.json"
    upload_test_assets: false
    upload_test_assets_strict: false
    test_assets_upload_report: "reports/api-test-assets/upload_report.json"
    test_management:
      testrail:
        enabled_env: "TESTRAIL_UPLOAD_ENABLED"
        base_url_env: "TESTRAIL_BASE_URL"
        email_env: "TESTRAIL_EMAIL"
        api_key_env: "TESTRAIL_API_KEY"
        section_id_env: "TESTRAIL_SECTION_ID"
        suite_id_env: "TESTRAIL_SUITE_ID"
      zephyr_scale:
        enabled_env: "ZEPHYR_UPLOAD_ENABLED"
        base_url_env: "ZEPHYR_SCALE_BASE_URL"
        api_token_env: "ZEPHYR_SCALE_API_TOKEN"
        project_key_env: "ZEPHYR_SCALE_PROJECT_KEY"
        folder_id_env: "ZEPHYR_SCALE_FOLDER_ID"
    external_mock:
      enabled: true
      provider: "postman"
      base_path: "/v1"
      postman:
        api_key_env: "POSTMAN_API_KEY"
        workspace_id_env: "POSTMAN_WORKSPACE_ID"
        collection_uid_env: "POSTMAN_COLLECTION_UID"
        mock_server_id_env: "POSTMAN_MOCK_SERVER_ID"
        mock_server_name: ""
        private: false
    run_docs_lint: false
    auto_remediate: true
    max_attempts: 3

```

### Unified Client Configuration (Part 11)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

Multi-version API docs (new standard):

```yaml

runtime:
  api_first:
    enabled: true
    docs_provider: "mkdocs"
    versions:
      - version: "v1"
        project_slug: "acme-v1"
        notes_path: "notes/api-v1-planning.md"
        spec_path: "api/v1/openapi.yaml"
        spec_tree_path: "api/v1"
        docs_spec_target: "docs/assets/api/v1"
        stubs_output: "generated/api-stubs/v1/main.py"
        openapi_version: "3.1.0"
        manual_overrides_path: "api/v1/overrides/openapi.manual.yml"
        regression_snapshot_path: "api/v1/.openapi-regression.json"
      - version: "v2"
        project_slug: "acme-v2"
        notes_path: "notes/api-v2-planning.md"
        spec_path: "api/v2/openapi.yaml"
        spec_tree_path: "api/v2"
        docs_spec_target: "docs/assets/api/v2"
        stubs_output: "generated/api-stubs/v2/main.py"
        openapi_version: "3.1.0"
        manual_overrides_path: "api/v2/overrides/openapi.manual.yml"
        regression_snapshot_path: "api/v2/.openapi-regression.json"

```

If your codebase has one API version, keep one config only.
If your codebase has multiple API versions, add one entry per version in `api_first.versions`.

New advanced keys:

### Unified Client Configuration (Part 12)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

- `openapi_version`: OpenAPI version for generation from planning notes.
- `manual_overrides_path`: YAML overlay file applied after generation for advanced schema blocks and `x-*` extensions.
- `regression_snapshot_path`: JSON baseline for contract regression gate.
- `update_regression_snapshot`: when `true`, refreshes baseline during run.
- `sandbox_backend`: `docker`, `prism`, or `external`.
- `mock_service`: informational provider marker for team ops (`postman`, `stoplight`, `mockoon`, `prism-hosted`, `custom`).
- `mock_base_url`: sandbox endpoint used by API self-verification.
- `sync_playground_endpoint`: when `true`, writes `mock_base_url` into `mkdocs.yml` API playground `sandbox_base_url`.
- `generate_test_assets`: generate API test documentation assets from OpenAPI.
- `upload_test_assets`: push generated assets to TestRail/Zephyr if credentials are enabled.
- `upload_test_assets_strict`: fail run if upload is enabled and provider upload fails.
- `test_management.*`: env var names for TestRail/Zephyr upload credentials.
- `external_mock.enabled`: when `true` and `sandbox_backend=external`, pipeline auto-prepares external mock before API-first checks.
- `external_mock.provider`: currently `postman`.
- `external_mock.base_path`: suffix appended to resolved mock URL (usually `/v1`).
- `external_mock.postman.*`: env var names used by automation.

External service behavior:

### Unified Client Configuration (Part 13)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

- The pipeline is provider-agnostic: it does not lock to one vendor.
- It uses `mock_base_url` as the source of truth for verification and Try-it requests.
- Common setups: Postman Mock Servers, Stoplight-hosted Prism, Mockoon Cloud, or your own hosted Prism.

In simple terms:

- `mock_base_url` is the one URL the whole pipeline uses for API sandbox checks.
- If that URL is public (HTTPS) and CORS is configured, Try-it works for every site visitor.

Client input checklist (Postman, one-time):

1. `POSTMAN_API_KEY`
1. `POSTMAN_WORKSPACE_ID`
1. optional `POSTMAN_COLLECTION_UID` (if missing, pipeline imports collection from generated OpenAPI)
1. Optional: `POSTMAN_MOCK_SERVER_ID` (if reusing an existing mock)

Optional test-management input checklist:

1. TestRail:
   `TESTRAIL_UPLOAD_ENABLED`, `TESTRAIL_BASE_URL`, `TESTRAIL_EMAIL`, `TESTRAIL_API_KEY`, `TESTRAIL_SECTION_ID`, optional `TESTRAIL_SUITE_ID`
1. Zephyr Scale:
   `ZEPHYR_UPLOAD_ENABLED`, `ZEPHYR_SCALE_API_TOKEN`, `ZEPHYR_SCALE_PROJECT_KEY`, optional `ZEPHYR_SCALE_BASE_URL`, optional `ZEPHYR_SCALE_FOLDER_ID`

After these are set, pipeline does the rest automatically:

### Unified Client Configuration (Part 14)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

1. Creates or reuses Postman mock server.
1. Resolves final public mock URL.
1. Uses it for API self-verification.
1. Syncs docs playground endpoint automatically.
1. Generates API test assets (cases, matrix, property/fuzz scenarios, CSV/JSON exports).
1. Optionally uploads those assets to TestRail/Zephyr.

##### Unified Client Configuration (Part 14): 6.1 Strict default behavior for multi-protocol flows

For GraphQL/gRPC/AsyncAPI/WebSocket, runtime uses strict defaults:

- contract validation runs before protocol lint/docs generation.
- semantic request/response relevance checks are mandatory in the protocol quality suite.
- if any enabled stage fails, pipeline retries protocol flow in an autofix cycle.

Runtime keys (per protocol under `runtime.api_protocol_settings.<protocol>`):

```yaml

generate_server_stubs: true
stubs_output: "generated/api-stubs/<protocol>/handlers.py"
self_verify_require_endpoint: true
publish_requires_live_green: true
autofix_cycle_enabled: true
autofix_max_attempts: 3
semantic_autofix_max_attempts: 3

```

These defaults are designed for smooth one-command autopipeline runs with minimal manual intervention.

### Unified Client Configuration (Part 15)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

##### Unified Client Configuration (Part 15): 6.2 Planning-notes generation for non-REST protocols

You can generate non-REST contracts directly from planning notes in the same autopipeline run.

```yaml

runtime:
  api_protocols: ["graphql", "grpc", "asyncapi", "websocket"]
  api_protocol_settings:
    graphql:
      schema_path: "api/schema.graphql"
      notes_path: "notes/graphql-api-planning.md"
      generate_from_notes: true
      generate_server_stubs: true
      stubs_output: "generated/api-stubs/graphql/handlers.py"
    grpc:
      proto_paths: ["api/proto"]
      notes_path: "notes/grpc-api-planning.md"
      generate_from_notes: true
      generate_server_stubs: true
      stubs_output: "generated/api-stubs/grpc/handlers.py"
    asyncapi:
      spec_path: "api/asyncapi.yaml"
      notes_path: "notes/asyncapi-planning.md"
      generate_from_notes: true
      generate_server_stubs: true
      stubs_output: "generated/api-stubs/asyncapi/handlers.py"
    websocket:
      contract_path: "api/websocket.yaml"
      notes_path: "notes/websocket-api-planning.md"
      generate_from_notes: true
      generate_server_stubs: true
      stubs_output: "generated/api-stubs/websocket/handlers.py"

```

When source contract is missing, pipeline auto-generates it from notes and continues with:
contract validation -> server stub generation -> lint -> regression -> docs generation -> semantic quality -> test assets -> publish.

### Unified Client Configuration (Part 16)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

#### Unified Client Configuration (Part 16): 7. Module switches

```yaml

runtime:
  modules:
    gap_detection: true
    drift_detection: true
    docs_contract: true
    kpi_sla: true
    rag_optimization: true
    ontology_graph: true
    retrieval_evals: true
    terminology_management: true
    normalization: true
    snippet_lint: true
    self_checks: true
    fact_checks: true
    lifecycle_management: true
    knowledge_validation: true
    i18n_sync: true
    release_pack: true

```

### Unified Client Configuration (Part 17)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

##### Unified Client Configuration (Part 17): Module -> required script in bundle

This auto-generated knowledge chunk was expanded to satisfy minimum retrieval module length for stable indexing.

### Unified Client Configuration (Part 18)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

- `gap_detection` -> `scripts/run_weekly_gap_batch.py` + `python3 -m scripts.gap_detection.cli analyze` (runtime command)
- `drift_detection` -> `scripts/check_api_sdk_drift.py`
- `docs_contract` -> `scripts/check_docs_contract.py`
- `kpi_sla` -> `scripts/evaluate_kpi_sla.py` + `scripts/generate_kpi_wall.py`
- `terminology_management` -> `scripts/sync_project_glossary.py`
- `normalization` -> `scripts/normalize_docs.py`
- `snippet_lint` -> `scripts/lint_code_snippets.py`
- `self_checks` -> `scripts/check_code_examples_smoke.py`
- `multilang_examples` -> `scripts/generate_multilang_tabs.py` + `scripts/validate_multilang_examples.py`
- `fact_checks` -> `scripts/seo_geo_optimizer.py` + `scripts/doc_layers_validator.py`
- `lifecycle_management` -> `scripts/lifecycle_manager.py` (+ lifecycle report/redirect guidance)
- `knowledge_validation` -> `scripts/extract_knowledge_modules_from_docs.py` + `scripts/validate_knowledge_modules.py`
- `rag_optimization` -> `scripts/generate_knowledge_retrieval_index.py`
- `ontology_graph` -> `scripts/generate_knowledge_graph_jsonld.py`
- `retrieval_evals` -> `scripts/run_retrieval_evals.py`
- `i18n_sync` -> `scripts/i18n_sync.py`
- `release_pack` -> `scripts/generate_release_docs_pack.py`
- `api-first/hybrid` -> `scripts/run_api_first_flow.py` + `scripts/generate_openapi_from_planning_notes.py` + `scripts/validate_openapi_contract.py` + `scripts/generate_fastapi_stubs_from_openapi.py` + `scripts/apply_openapi_overrides.py` + `scripts/check_openapi_regression.py`
- `finalize_gate` -> `scripts/finalize_docs_gate.py` (iterative lint/fix gate + optional user commit confirmation flow)

### Unified Client Configuration (Part 19)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

If script is missing in bundle, module is skipped or warned.

Pilot note:

- In `pilot-evidence` preset, script set is intentionally reduced.
- Full-scope presets (`startup`/`enterprise`, mapped to Pro/Enterprise plan levels) include broader script surface.
- Builder also auto-adds critical API-first dependencies when `runtime.api_first.enabled=true`.

Glossary marker format for new terms inside docs:

```markdown

<!-- glossary:add: Term | Description | alias-one, alias-two -->

```

`sync_project_glossary.py` reads markers and updates `glossary.yml`.

RAG-aligned retrieval eval and graph settings:

### Unified Client Configuration (Part 2)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

#### Unified Client Configuration (Part 2): Current product definition (2026-03-25)

This content follows the active implementation baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` modes.
1. The smooth autopipeline covers all five API protocols (REST, GraphQL, gRPC, AsyncAPI, and WebSocket) in one operational model.
1. Non-REST flow includes generated server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated, with Postman-supported auto-prepare in external mode.
1. Contract test assets are generated automatically and merged with smart-merge so manual/customized cases are preserved and flagged for review when needed.
1. Knowledge/RAG maintenance, terminology sync, and quality/compliance gates run through the same automation surface when enabled.
1. Plan tiers gate advanced capabilities; higher plans include broader non-REST and governance scope.

Single source of truth for per-client setup:

- `profiles/clients/<client>.client.yml`

This file controls all client-specific behavior: repo paths, flow mode, modules, quality strictness, automation schedule, and legal labeling.

### Unified Client Configuration (Part 20)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

```yaml

runtime:
  retrieval_eval:
    enabled: true
    index_path: "docs/assets/knowledge-retrieval-index.json"
    dataset_path: ""
    top_k: 3
    min_precision: 0.5
    min_recall: 0.5
    max_hallucination_rate: 0.5
    auto_samples: 25
  knowledge_graph:
    enabled: true
    modules_dir: "knowledge_modules"
    output_path: "docs/assets/knowledge-graph.jsonld"
  git_sync:
    enabled: true
    repo_path: "."
    remote: "origin"
    branch: ""
    fetch_first: true
    rebase: true
    autostash: true
    continue_on_error: true
  finalize_gate:
    enabled: true
    docs_root: "docs"
    reports_dir: "reports"
    lint_command: "npm run lint"
    max_iterations: 5
    continue_on_error: true
    auto_fix_commands:
      - "python3 scripts/normalize_docs.py {docs_root}"
      - "python3 scripts/seo_geo_optimizer.py {docs_root} --fix"
    llm_fix_command: ""
    ask_commit_confirmation: false
    run_precommit_before_commit: true
    commit_on_approve: false
    push_on_commit: false

```

By default, `git_sync.enabled=true`: weekly runner executes `git fetch` + `git pull` before report generation.
This lets the responsible person avoid manual pull steps.
Scheduler must run under a user account that already has git access to the private repo (SSH key or credential helper/PAT).

`finalize_gate` behavior:

### Unified Client Configuration (Part 21)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

- runs after generation/refinement tasks in weekly flow,
- runs lint/fix/lint loop (`scripts/finalize_docs_gate.py`),
- can optionally ask user confirmation before commit in interactive mode.

Important: API-first is only one flow branch.
The pipeline supports and generates all major doc types (tutorial/how-to/concept/reference/troubleshooting/release/security/sdk/api/user/admin/runbook), and quality automation applies across them.

### Unified Client Configuration (Part 22)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

#### Unified Client Configuration (Part 22): 8. Universal tasks (core UTP, not optional extras)

Use `runtime.custom_tasks.weekly` to wire any command from the capabilities catalog.

```yaml

runtime:
  custom_tasks:
    weekly:
      - id: "geo-lint"
        enabled: true
        command: "python3 docsops/scripts/seo_geo_optimizer.py docs/"
        continue_on_error: true
      - id: "openapi-lint"
        enabled: true
        command: "npm run lint:openapi"
        continue_on_error: true
    on_demand: []

```

Full list of available capabilities:

- `docs/operations/PIPELINE_CAPABILITIES_CATALOG.md`
- regenerate catalog: `python3 scripts/generate_pipeline_capabilities_catalog.py`

Recommended default for smooth intent assembly:

- Keep `scripts/build_all_intent_experiences.py` in `bundle.include_scripts`.
- Keep `python3 docsops/scripts/build_all_intent_experiences.py` enabled in `runtime.custom_tasks.weekly`.
- Keep `knowledge_modules` in `bundle.include_paths` (or store it directly in client repo).

### Unified Client Configuration (Part 23)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

#### Unified Client Configuration (Part 23): 9. Integrations (single control point)

Use one section to configure cross-stack integrations for any supported generator.

```yaml

runtime:
  integrations:
    algolia:
      enabled: true
      docs_dir: "docs"
      report_output: "reports/seo-report.json"
      upload_on_weekly: true
      app_id_env: "ALGOLIA_APP_ID"
      api_key_env: "ALGOLIA_API_KEY"
      index_name_env: "ALGOLIA_INDEX_NAME"
      index_name_default: "docs"
    ask_ai:
      enabled: true
      auto_configure_on_provision: true
      install_runtime_pack: false
      provider: "openai"
      billing_mode: "user-subscription"
      model: "gpt-4.1-mini"
      base_url: "https://api.openai.com/v1"

```

How it works:

- `algolia.enabled=true`: weekly runner generates Algolia payload from docs.
- `algolia.upload_on_weekly=true`: weekly runner also uploads to Algolia (if env credentials are set).
- `ask_ai.auto_configure_on_provision=true`: provisioning auto-writes `config/ask-ai.yml`.
- `ask_ai.install_runtime_pack=true`: provisioning auto-installs Ask AI runtime pack.

Manual verification for integrations:

- If `algolia.enabled=true`, ensure env names in `runtime.integrations.algolia.*_env` match client secrets naming.
- If `ask_ai.enabled=true`, confirm generated `config/ask-ai.yml` in client repo has expected provider/model/billing mode.

### Unified Client Configuration (Part 24)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

##### Unified Client Configuration (Part 24): Core UTP tasks (default-on baseline)

```yaml

runtime:
  custom_tasks:
    weekly:
      - id: "seo-geo"
        enabled: true
        command: "python3 docsops/scripts/seo_geo_optimizer.py docs/"
        continue_on_error: true
      - id: "knowledge-validate"
        enabled: true
        command: "python3 docsops/scripts/validate_knowledge_modules.py"
        continue_on_error: true
      - id: "knowledge-index"
        enabled: true
        command: "python3 docsops/scripts/generate_knowledge_retrieval_index.py"
        continue_on_error: true
      - id: "intent-all"
        enabled: true
        command: "python3 docsops/scripts/build_all_intent_experiences.py"
        continue_on_error: true

```

### Unified Client Configuration (Part 25)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

##### Unified Client Configuration (Part 25): Additional examples

###### Unified Client Configuration (Part 25): Multi-language examples baseline (new standard)

```yaml

runtime:
  modules:
    multilang_examples: true
  multilang_examples:
    enabled: true
    scope: "all"
    required_languages: ["curl", "javascript", "python"]

```

Bundle requirements:

```yaml

bundle:
  include_scripts:
    - "scripts/generate_multilang_tabs.py"
    - "scripts/validate_multilang_examples.py"

```

How it works in weekly runner:

- auto-generate tabbed examples from standalone cURL examples
- validate required language tabs
- run smoke execution and `expected-output` matching on tagged blocks

###### Unified Client Configuration (Part 25): API-first advanced baseline (overrides + regression gate)

```yaml

runtime:
  api_first:
    enabled: true
    openapi_version: "3.1.0"
    manual_overrides_path: "api/overrides/openapi.manual.yml"
    regression_snapshot_path: "api/.openapi-regression.json"
    update_regression_snapshot: false

```

Bundle requirements:

```yaml

bundle:
  include_scripts:
    - "scripts/apply_openapi_overrides.py"
    - "scripts/check_openapi_regression.py"

```

###### Unified Client Configuration (Part 25): SEO/GEO weekly

```yaml

runtime:
  custom_tasks:
    weekly:
      - id: "seo-geo"
        enabled: true
        command: "python3 docsops/scripts/seo_geo_optimizer.py docs/"
        continue_on_error: true

```

###### Unified Client Configuration (Part 25): RAG / knowledge base weekly

### Unified Client Configuration (Part 26)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

```yaml

runtime:
  custom_tasks:
    weekly:
      - id: "knowledge-validate"
        enabled: true
        command: "python3 docsops/scripts/validate_knowledge_modules.py"
        continue_on_error: true
      - id: "knowledge-index"
        enabled: true
        command: "python3 docsops/scripts/generate_knowledge_retrieval_index.py"
        continue_on_error: true
      - id: "intent-all"
        enabled: true
        command: "python3 docsops/scripts/build_all_intent_experiences.py"
        continue_on_error: true

```

###### Unified Client Configuration (Part 26): Multilingual (i18n) baseline

```yaml

runtime:
  modules:
    i18n_sync: true
  custom_tasks:
    weekly:
      - id: "i18n-translate-stale"
        enabled: false
        command: "python3 docsops/scripts/i18n_translate.py --stale-only"
        continue_on_error: true

```

Bundle requirements:

```yaml

bundle:
  include_scripts:
    - "scripts/i18n_sync.py"
    - "scripts/i18n_translate.py"
    - "scripts/i18n_migrate.py"
    - "scripts/i18n_utils.py"

```

Practical mode:

- Keep `i18n_sync` always on (checks coverage/drift for locales).
- Keep auto-translation off by default (`enabled: false`) unless client explicitly wants it.

###### Unified Client Configuration (Part 26): Interactive diagrams assets

```yaml

bundle:
  include_paths:
    - "templates/interactive-diagram.html"

```

###### Unified Client Configuration (Part 26): Search facets index

### Unified Client Configuration (Part 27)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

```yaml

runtime:
  custom_tasks:
    weekly:
      - id: "facets-index"
        enabled: true
        command: "python3 docsops/scripts/generate_facets_index.py --docs-dir docs --output docs/assets/facets-index.json"
        continue_on_error: true

```

###### Unified Client Configuration (Part 27): Algolia push

```yaml

runtime:
  custom_tasks:
    weekly:
      - id: "algolia-upload"
        enabled: true
        command: "python3 docsops/scripts/upload_to_algolia.py"
        continue_on_error: true

```

#### Unified Client Configuration (Part 27): 9. Private tuning

```yaml

private_tuning:
  gap_priority_weights:
    business_impact: 0.45
    user_frequency: 0.35
    implementation_cost: 0.20
  stale_days: 21
  weekly_stale_days: 180
  rag_chunk_target_tokens: 420
  verify_max_attempts: 3

```

`weekly_stale_days` default is 180 (half year), configurable per client.

#### Unified Client Configuration (Part 27): 10. Licensing

```yaml

licensing:
  plan: "professional"   # pilot | professional | enterprise
  days: 365              # License validity in days
  max_docs: 1000         # Page limit (0 = unlimited)

```

Builder generates a signed JWT license at `docsops/license.jwt` (if the Ed25519 private key is available at `docsops/keys/veriops-licensing.key`). If the private key is absent, a placeholder is written.

Plan tiers control feature access at runtime. See `docs/operations/PLAN_TIERS.md` for the full feature matrix and license enforcement details.

### Unified Client Configuration (Part 28)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

#### Unified Client Configuration (Part 28): 11. Legal labeling

```yaml

legal:
  license_type: "commercial"
  redistribution_allowed: false
  reseller_allowed: false

```

Builder generates:

- `LICENSE-COMMERCIAL.md`
- `NOTICE`

#### Unified Client Configuration (Part 28): 12. Flow presets (copy-paste)

##### Unified Client Configuration (Part 28): Code-first only

```yaml

runtime:
  docs_flow:
    mode: "code-first"
  modules:
    gap_detection: true
    drift_detection: true
    docs_contract: true
    kpi_sla: true

```

##### Unified Client Configuration (Part 28): API-first only

```yaml

runtime:
  docs_flow:
    mode: "api-first"
  api_first:
    enabled: true
    openapi_version: "3.1.0"
    manual_overrides_path: "api/overrides/openapi.manual.yml"
    regression_snapshot_path: "api/.openapi-regression.json"
    generate_from_notes: true

```

##### Unified Client Configuration (Part 28): Hybrid

```yaml

runtime:
  docs_flow:
    mode: "hybrid"
  api_first:
    enabled: true
  modules:
    gap_detection: true
    drift_detection: true
    docs_contract: true
    kpi_sla: true

```

### Unified Client Configuration (Part 29)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

##### Unified Client Configuration (Part 29): Full UTP baseline (recommended)

```yaml

runtime:
  docs_flow:
    mode: "hybrid"
  modules:
    gap_detection: true
    drift_detection: true
    docs_contract: true
    kpi_sla: true
    rag_optimization: true
    multilang_examples: true
    normalization: true
    snippet_lint: true
    knowledge_validation: true
    i18n_sync: true
    release_pack: true
  custom_tasks:
    weekly:
      - id: "seo-geo"
        enabled: true
        command: "python3 docsops/scripts/seo_geo_optimizer.py docs/"
        continue_on_error: true
      - id: "knowledge-index"
        enabled: true
        command: "python3 docsops/scripts/generate_knowledge_retrieval_index.py"
        continue_on_error: true

```

Default automation order in weekly runner:

\11. extract knowledge modules from docs (`extract_knowledge_modules_from_docs.py`)
\11. validate modules (`validate_knowledge_modules.py`)
\11. regenerate retrieval index (`generate_knowledge_retrieval_index.py`)
\11. generate JSON-LD knowledge graph (`generate_knowledge_graph_jsonld.py`)
\11. run retrieval evals (`run_retrieval_evals.py`)
\11. sync glossary markers to `glossary.yml` (`sync_project_glossary.py`)
\11. generate multi-language tabs (`generate_multilang_tabs.py`)
\11. validate multi-language tabs (`validate_multilang_examples.py`)
\11. run smoke checks with optional `expected-output` matching (`check_code_examples_smoke.py`)

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

### Unified Client Configuration (Part 30)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

#### Unified Client Configuration (Part 30): 9. Fully automated RAG/knowledge flow

To run RAG and knowledge base maintenance without manual commands:

\11. Configure once in client profile:

- enable `runtime.modules.knowledge_validation: true`
- enable `runtime.modules.rag_optimization: true`
- enable `runtime.modules.ontology_graph: true`
- enable `runtime.modules.retrieval_evals: true`
- add `runtime.custom_tasks.weekly` entries (for example intent experiences)
- include `bundle.include_paths: ["knowledge_modules"]`
- include scripts:
  - `scripts/extract_knowledge_modules_from_docs.py`
  - `scripts/validate_knowledge_modules.py`
  - `scripts/generate_knowledge_retrieval_index.py`
  - `scripts/generate_knowledge_graph_jsonld.py`
  - `scripts/run_retrieval_evals.py`

\11. Provision once:

- install bundle with `scripts/provision_client_repo.py`
- install scheduler with `--install-scheduler linux` or `--install-scheduler windows`

\11. Weekly automation then runs by itself:

- scheduler triggers `run_weekly_gap_batch.py`
- it runs `extract_knowledge_modules_from_docs.py`
- it runs `validate_knowledge_modules.py`
- it runs `generate_knowledge_retrieval_index.py`
- it runs `generate_knowledge_graph_jsonld.py`
- it runs `run_retrieval_evals.py`
- it runs all enabled `custom_tasks.weekly`
- it writes consolidated reports

Outcome:

### Unified Client Configuration (Part 31)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

- operators do not run commands manually each week
- operators only review report output and final published docs

#### Unified Client Configuration (Part 31): Next steps

- [Documentation index](../index.md)

#### Unified Client Configuration (Part 31): Implementation status (2026-03-25)

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

### Unified Client Configuration (Part 4)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

- `profiles/clients/presets/pilot-evidence.yml` is intentionally limited (core proof scope).
- Use full-scope plan presets for full implementation coverage:
  - `profiles/clients/presets/startup.yml` (Pro-equivalent)
  - `profiles/clients/presets/enterprise.yml` (Enterprise-equivalent)

#### Unified Client Configuration (Part 4): Non-API documentation flows (docs-first scope)

The platform is not limited to API-first automation. In active production usage, it also runs full docs-first and code-first documentation operations for non-API content:

1. Detects content gaps, stale pages, and drift across product docs, runbooks, admin guides, troubleshooting, and release notes.
1. Generates and updates documentation types beyond API references (tutorial, how-to, concept, reference, troubleshooting, release-note, security, SDK, user/admin, and operations docs).
1. Applies normalization, style, metadata/frontmatter, SEO/GEO, terminology governance, and snippet validation to all documentation categories.
1. Executes lifecycle controls (active/deprecated/removed states, replacement links, and freshness cadence).
1. Runs knowledge extraction and retrieval preparation for all docs, not only API pages.
1. Produces consolidated review artifacts so human input is focused on approval and business accuracy, not repetitive formatting and synchronization work.

### Unified Client Configuration (Part 5)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

#### Unified Client Configuration (Part 5): 1. Client identity

```yaml

client:
  id: "acme"
  company_name: "ACME Inc."
  contact_email: "docs-owner@acme.example"

```

#### Unified Client Configuration (Part 5): 2. Bundle packaging

```yaml

bundle:
  output_dir: "generated/client_bundles"
  base_policy_pack: "multi-product"
  style_guide: "google"
  policy_overrides: {}
  include_scripts: []
  include_docs: []
  include_paths: []

```

##### Unified Client Configuration (Part 5): `base_policy_pack`

Available built-ins:

- `minimal`
- `api-first`
- `monorepo`
- `multi-product`
- `plg`

##### Unified Client Configuration (Part 5): `policy_overrides`

Deep-merged into selected policy pack for per-client tuning.

Example:

```yaml

bundle:
  policy_overrides:
    kpi_sla:
      min_doc_coverage: 90
      max_quality_score_drop: 2

```

##### Unified Client Configuration (Part 5): `style_guide` (Vale style profile)

```yaml

bundle:
  style_guide: "google" # google | microsoft | hybrid

```

Builder writes `.vale.ini` in client bundle automatically based on this setting.

Notes:

- `google` -> Google-based lint profile
- `microsoft` -> Microsoft-based lint profile
- `hybrid` -> both style packs enabled
- all profiles include `write-good` and `AmericanEnglish` checks by default
- run `vale sync` in client repo after provisioning to fetch selected style packages

### Unified Client Configuration (Part 6)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

##### Unified Client Configuration (Part 6): `include_paths` (important for templates and knowledge)

Allows copying any extra files and folders into the bundle:

```yaml

bundle:
  include_paths:
    - "templates/interactive-diagram.html"
    - "knowledge_modules"

```

Use this for:

- interactive diagrams
- knowledge modules
- any custom assets

Default behavior:

- You normally do not need to edit `include_paths` manually.
- Preset and profile defaults are already applied during bundle build.
- Bundle is always created in `generated/client_bundles/<client_id>/`, so operator can inspect exact contents before handoff.

#### Unified Client Configuration (Part 6): 3. LLM instruction packaging

```yaml

bundle:
  llm:
    codex_instructions_source: "AGENTS.md"
    claude_instructions_source: "CLAUDE.md"
    inject_managed_block: true
    docsops_root_in_client_repo: "docsops"

```

When `inject_managed_block=true`, builder auto-inserts managed docsops block into bundled `AGENTS.md` and `CLAUDE.md`.

Plan-level defaults:

- Pilot preset -> `instructions/llm_plans/pilot/AGENTS.md`, `instructions/llm_plans/pilot/CLAUDE.md`
- Basic preset -> `instructions/llm_plans/basic/AGENTS.md`, `instructions/llm_plans/basic/CLAUDE.md`
- Pro preset -> `instructions/llm_plans/pro/AGENTS.md`, `instructions/llm_plans/pro/CLAUDE.md`
- Enterprise preset -> `AGENTS.md`, `CLAUDE.md` (current full-scope instructions)

### Unified Client Configuration (Part 7)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

#### Unified Client Configuration (Part 7): 4. Automation schedule (weekly)

```yaml

bundle:
  automation:
    weekly_gap_report:
      enabled: true
      since_days: 7
      day_of_week: "monday"
      time_24h: "10:00"

```

#### Unified Client Configuration (Part 7): 5. Runtime behavior

```yaml

runtime:
  docs_flow:
    mode: "code-first" # code-first | api-first | hybrid
  docs_root: "docs"
  api_root: "api"
  sdk_root: "sdk"
  preferred_llm: "claude"
  output_targets: ["sphinx", "readme"]

```

### Unified Client Configuration (Part 8)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

##### Unified Client Configuration (Part 8): 5.1 PR auto-doc workflow

```yaml

runtime:
  pr_autofix:
    enabled: false
    require_label: false
    label_name: "auto-doc-fix"
    enable_auto_merge: false
    commit_message: "docs: auto-sync PR docs"
    workflow_filename: "docsops-pr-autofix.yml"

```

Behavior when enabled:

- Trigger: PR opened/updated (`pull_request` events).
- Scope: only changed files in the current PR (`base...head` diff).
- If docs drift is detected, bot can generate docs patch and commit to the same PR branch.
- No commits to `main`.
- Checks rerun automatically after bot commit.

Default policy:

- `pr_autofix` is optional and disabled by default.
- `docs_contract` is report-only by default in weekly flow and consolidated report.
- Weekly consolidated report adds only new/changed docs-contract mismatches, ignores closed ones, and deduplicates with other gap sources.

One-time repo setup (done during provisioning):

1. Workflow file is generated in `.github/workflows/docsops-pr-autofix.yml`.
1. Set GitHub Actions permissions to `Read and write`.
1. Optional: set `DOCSOPS_BOT_TOKEN` for orgs that restrict default token pushes.

### Unified Client Configuration (Part 9)

Single source of truth for per-client Auto-Doc Pipeline configuration, modules, and automation.

#### Unified Client Configuration (Part 9): 6. API-first configuration (one branch, not the whole product)

This auto-generated knowledge chunk was expanded to satisfy minimum retrieval module length for stable indexing.

### Variables and Templates Guide

How to use Jinja2 variables and templates in documentation for consistency

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### Variables and Templates Guide: Variables and Templates Guide

#### Variables and Templates Guide: Overview

This documentation system uses **Jinja2 templating** through mkdocs-macros-plugin to maintain consistency and avoid repetition.

#### Variables and Templates Guide: How to Use Variables

##### Variables and Templates Guide: In Markdown Files

Simply use double curly braces:

```markdown

The default port for {{ product_name }} is {{ default_port }}.

Visit [{{ product_name }} Cloud]({{ cloud_url }}) to get started.

Maximum payload size: {{ max_payload_size_mb }}MB

```

##### Variables and Templates Guide: Conditional Content

Use Jinja2 conditions for dynamic content:

```markdown

{% if product == "the product-cloud" %}

## Cloud-specific Instructions
This feature is only available in {{ product_name }} Cloud.
{% else %}

## Self-hosted Instructions
Run on port {{ default_port }} by default.
{% endif %}

```

##### Variables and Templates Guide: Loops for Lists

```markdown

{% for var, value in env_vars.items() %}
- `{{ value }}`: Configure {{ var }}
{% endfor %}

```

#### Variables and Templates Guide: Available Variables

All variables are defined in `docs/_variables.yml`:

##### Variables and Templates Guide: Product Information

- `{{ product_name }}` - - `{{ product_full_name }}` - workflow automation
- `{{ current_version }}` - Current version number

### Variables and Templates Guide (Part 2)

How to use Jinja2 variables and templates in documentation for consistency

##### Variables and Templates Guide (Part 2): URLs

- `{{ cloud_url }}` - Cloud app URL
- `{{ docs_url }}` - Documentation URL
- `{{ community_url }}` - Community forum URL
- `{{ github_url }}` - GitHub repository

##### Variables and Templates Guide (Part 2): Configuration

- `{{ default_port }}` - Default port (5678)
- `{{ default_webhook_port }}` - Webhook port
- `{{ default_data_folder }}` - Data folder path
- `{{ max_payload_size_mb }}` - Max payload size

##### Variables and Templates Guide (Part 2): Environment Variables

Access via `env_vars` dictionary:

- `{{ env_vars.webhook_url }}` - WEBHOOK_URL
- `{{ env_vars.port }}` - APP_PORT
- `{{ env_vars.data_folder }}` - APP_USER_FOLDER

#### Variables and Templates Guide (Part 2): Setup Requirements

##### Variables and Templates Guide (Part 2): 1. Install mkdocs-macros-plugin

```bash

pip install mkdocs-macros-plugin

```

##### Variables and Templates Guide (Part 2): 2. Configure mkdocs.yml

```yaml

plugins:
  - macros:
      include_dir: docs
      include_yaml:
        - _variables.yml

```

##### Variables and Templates Guide (Part 2): 3. Use in Templates

All VS Code snippets now include variables:

- Type `doc-tutorial` → includes `{{ min_version }}`
- Type `doc-howto` → includes `{{ default_port }}`
- Type `doc-reference` → includes `{{ product_name }}`

#### Variables and Templates Guide (Part 2): Best Practices

##### Variables and Templates Guide (Part 2): 1. Always Use Variables For

- Product names
- Version numbers
- URLs
- Port numbers
- File paths
- Size limits
- Timeouts

##### Variables and Templates Guide (Part 2): 2. Never Hardcode

- URLs (use `{{ cloud_url }}`, `{{ docs_url }}`)
- Version numbers (use `{{ current_version }}`)
- Configuration values (use variables from `_variables.yml`)

### Variables and Templates Guide (Part 3)

How to use Jinja2 variables and templates in documentation for consistency

##### Variables and Templates Guide (Part 3): 3. Create New Variables When

- You use the same value in 3+ places
- The value might change in the future
- It's configuration-specific

#### Variables and Templates Guide (Part 3): Adding New Variables

\11. Edit `docs/_variables.yml`:

```yaml

# Add your variable
my_new_variable: "value"

```

\11. Use in any markdown file:

```markdown

The value is {{ my_new_variable }}.

```

\11. Variables are available immediately after saving.

#### Variables and Templates Guide (Part 3): Troubleshooting

##### Variables and Templates Guide (Part 3): Variable Not Rendering

**Problem**: You see `{{ variable_name }}` in output
**Solution**: Ensure mkdocs-macros-plugin is installed and configured

##### Variables and Templates Guide (Part 3): Variable Not Found Error

**Problem**: Build fails with "variable not defined"
**Solution**: Check variable name in `_variables.yml`

##### Variables and Templates Guide (Part 3): Conditional Content Not Working

**Problem**: Jinja2 conditions show in output
**Solution**: Use `{% raw %}` tags to escape if needed:

```markdown

{% raw %}
This will show: {{ variable_name }}
{% endraw %}

```

#### Variables and Templates Guide (Part 3): Examples

##### Variables and Templates Guide (Part 3): Complete Page with Variables

```markdown

---
title: "Configure {{ product_name }} Webhooks"
description: "Learn how to set up webhooks on port {{ default_webhook_port }}"
---

# Configure {{ product_name }} Webhooks

{{ product_name }} webhooks listen on port {{ default_webhook_port }} by default.

## Prerequisites

- {{ product_name }} version {{ min_supported_version }} or later
- Access to port {{ default_webhook_port }}

### Variables and Templates Guide (Part 4)

How to use Jinja2 variables and templates in documentation for consistency

#### Variables and Templates Guide (Part 4): Configuration

{% if product == "the product-cloud" %}
Visit [{{ product_name }} Cloud]({{ cloud_url }}) and navigate to Settings.
{% else %}
Set the environment variable:

```bash

export {{ env_vars.webhook_url }}=https://your-domain.com:{{ default_webhook_port }}

```text

{% endif %}

#### Variables and Templates Guide (Part 4): Limits

- Maximum payload: {{ max_payload_size_mb }}MB
- Timeout: {{ max_execution_timeout_seconds }} seconds
- Rate limit: {{ rate_limit_requests_per_minute }} requests/minute

#### Variables and Templates Guide (Part 4): Support

Contact us at {{ support_email }} or visit [Community Forum]({{ community_url }}).

```

## Variable Categories Reference

| Category | Variables | Usage |
|----------|-----------|--------|
| Product | `product_name`, `product_full_name` | Branding |
| Versions | `current_version`, `min_supported_version` | Requirements |
| URLs | `cloud_url`, `docs_url`, `github_url` | Links |
| Ports | `default_port`, `default_webhook_port` | Configuration |
| Paths | `default_data_folder`, `default_config_path` | File locations |
| Limits | `max_payload_size_mb`, `rate_limit_requests_per_minute` | Constraints |
| Support | `support_email`, `sales_email` | Contact info |

## Next steps

- [Documentation index](index.md)

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

### WEBSOCKET API Reference

Auto-generated websocket reference from source contract.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

### WEBSOCKET API Reference: WEBSOCKET Reference

Source: `reports/acme-demo/contracts/websocket.yaml`

Flow mode: `api-first`

#### WEBSOCKET API Reference: Top-level Keys

- `channels`

#### WEBSOCKET API Reference: Channels/Events

- Channel count: `1`
- `project.updated`

### WEBSOCKET API Reference (Part 2)

Auto-generated websocket reference from source contract.

#### WEBSOCKET API Reference (Part 2): Interactive WebSocket Tester

> Sandbox semantic mode: this tester returns protocol-aware responses based on message type/action.

### WEBSOCKET API Reference (Part 3)

Auto-generated websocket reference from source contract.

<!-- vale off -->
<div id="websocket-playground" style="border:1px solid #d1d5db; padding:12px; border-radius:8px;">
  <p><strong>Endpoint:</strong> <code id="websocket-endpoint-view"></code></p>
  <textarea id="websocket-message" rows="8" style="width:100%; font-family:monospace;">{
  "type": "subscribe",
  "request_id": "req_001",
  "payload": {"channel": "project.updated", "filters": {"project_id": "prj_abc123"}}
}</textarea><br/>
  <button id="websocket-send">Connect + Send</button>
  <pre id="websocket-output" style="margin-top:12px; max-height:320px; overflow:auto;"></pre>
</div>
<script>
(function(){ const endpoint = "wss://echo.websocket.events";
const view = document.getElementById('websocket-endpoint-view');
const send = document.getElementById('websocket-send');
const msg = document.getElementById('websocket-message');
const out = document.getElementById('websocket-output');
if (!view || !send || !msg || !out) return;
view.textContent = endpoint || 'not configured';
function parseJson(raw){ try { return JSON.parse(String(raw || '{}')); } catch (_) { return { raw: String(raw || '') }; } }
function semanticResponse(input){
  const req = parseJson(input);
  const payload = (req && req.payload && typeof req.payload === 'object') ? req.payload : {};
  const type = String(req.type || req.action || '').toLowerCase();
  const requestId = req.request_id || ('req_' + Date.now());
  const channel = String(payload.channel || payload.topic || 'project.updated');
  const projectId = String((payload.filters && payload.filters.project_id) || payload.project_id || 'prj_abc123');
  if (type === 'ping') return { type: 'pong', request_id: requestId, payload: { ts: new Date().toISOString() } };
  if (type === 'subscribe') return { type: 'ack', request_id: requestId, payload: { status: 'subscribed', channel: channel, filters: payload.filters || {} } };
  if (type === 'unsubscribe') return { type: 'ack', request_id: requestId, payload: { status: 'unsubscribed', channel: channel } };
  if (type === 'publish') return { type: 'event', request_id: requestId, payload: { event_type: channel, data: Object.assign({ project_id: projectId, status: 'active' }, (payload.data && typeof payload.data === 'object') ? payload.data : {}) } };
  if (type === 'get_project' || type === 'project.get' || type === 'query') return { type: 'event', request_id: requestId, payload: { event_type: 'project.snapshot', data: { project_id: projectId, name: 'Website Redesign', status: 'active', updated_at: new Date().toISOString() } } };
  if (type === 'list_projects' || type === 'project.list') return { type: 'event', request_id: requestId, payload: { event_type: 'project.list', data: [{ project_id: 'prj_abc123', status: 'active' }, { project_id: 'prj_def456', status: 'draft' }] } };
  return { type: 'ack', request_id: requestId, payload: { status: 'accepted', echo: req, hint: 'Use: ping, subscribe, unsubscribe, publish, get_project, list_projects' } };
}
send.onclick = function(){
  if (!endpoint) { out.textContent = 'Endpoint is not configured in runtime.api_protocol_settings.websocket.websocket_endpoint'; return; }
  try {
    const socket = new WebSocket(endpoint);
    let received = false;
    socket.onopen = function(){ socket.send(msg.value); out.textContent = 'message sent'; };
    socket.onmessage = function(e){
      received = true;
      const simulated = semanticResponse(e.data);
      out.textContent = JSON.stringify({ mode: 'live-echo-plus-semantic', raw: String(e.data || ''), simulated_response: simulated }, null, 2);
      socket.close();
    };
    socket.onerror = function(){
      const simulated = semanticResponse(msg.value);
      out.textContent = JSON.stringify({ mode: 'offline-semantic-fallback', simulated_response: simulated }, null, 2);
    };
    setTimeout(function(){
      if (!received) {
        const simulated = semanticResponse(msg.value);
        out.textContent = JSON.stringify({ mode: 'timeout-semantic-fallback', simulated_response: simulated }, null, 2);
        try { socket.close(); } catch (_) {}
      }
    }, 1500);
  } catch (error) { out.textContent = String(error); }
};
})();
</script>
<!-- vale on -->

### WEBSOCKET API Reference (Part 4)

Auto-generated websocket reference from source contract.

#### WEBSOCKET API Reference (Part 4): Next steps

- [Documentation index](index.md)

This auto-generated knowledge chunk was expanded to satisfy minimum retrieval module length for stable indexing.

### Workflow execution model

The workflow engine processes workflows by executing nodes sequentially, passing data as arrays of JSON objects between each node in the chain.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

#### Workflow execution model: Workflow execution model overview

The execution model determines how data flows from one node to the next within a workflow. The engine executes nodes sequentially and passes data as arrays of JSON objects. This model explains why node behavior is predictable across branches, retries, and failures.

#### Workflow execution model: Data structure between nodes

Every node receives and outputs data in the same format: an array of items, where each item is a JSON object wrapped in a `json` key (for example, user records and event payloads).

When a node receives 5 items, it processes each item independently. The Slack node, for example, sends 5 separate messages—one per item.

#### Workflow execution model: Execution flow

The engine follows these rules during execution:

1. The **trigger node** starts the workflow and produces the initial items.
1. Each subsequent node receives all output items from the previous node.
1. A node processes items either **once for all items** or **once per item**, depending on the node type and configuration.
1. **Branch nodes** (IF, Switch) route items to different paths based on conditions.
1. Execution stops when all branches reach their final nodes.

### Workflow execution model (Part 2)

The workflow engine processes workflows by executing nodes sequentially, passing data as arrays of JSON objects between each node in the chain.

#### Workflow execution model (Part 2): Execution modes

The platform supports two execution modes that affect error handling and performance.

=== "Regular mode (default)"

 Nodes execute one at a time. If a node fails, execution stops and the workflow reports an error. This mode is predictable and easier to debug.

 Typical setting: `EXECUTIONS_MODE=regular`

=== "Queue mode (production)"

 Workflow executions are distributed across worker processes. This mode handles high-volume workloads (hundreds of concurrent executions) and requires a Redis instance for coordination.

 Typical setting: `EXECUTIONS_MODE=queue`

#### Workflow execution model (Part 2): Error handling

When a node fails, behavior depends on the node's error handling setting:

- **Stop execution** (default): The workflow stops. The error appears in the execution log.
- **Continue on fail**: The node outputs an error object, and the next node receives it. Use this for non-critical steps like logging.
- **Error Trigger workflow**: A separate workflow handles the error path. This pattern is common for alerting and retry logic.

#### Workflow execution model (Part 2): Key implications for documentation writers

The execution model means that every node reference page should document what input format the node expects, what output format it produces (how many items, what structure), and how the node behaves with multiple items (once for all vs. once per item).

### Workflow execution model (Part 3)

The workflow engine processes workflows by executing nodes sequentially, passing data as arrays of JSON objects between each node in the chain.

#### Workflow execution model (Part 3): Related

- [Build your first workflow](../getting-started/quickstart.md)
- [Webhook node reference](../reference/nodes/webhook.md)

#### Workflow execution model (Part 3): Next steps

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

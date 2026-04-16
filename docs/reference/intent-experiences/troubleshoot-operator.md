---
title: "Intent experience: troubleshoot for operator"
description: "Assembled guidance for one intent and audience using reusable knowledge modules with verified metadata and channel-ready sections."
content_type: reference
product: both
tags:
  - Reference
  - AI
---

<!-- markdownlint-disable MD001 MD007 MD024 MD025 MD031 -->

# Intent experience: troubleshoot for operator

This page is assembled for the `troubleshoot` intent and the `operator` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent troubleshoot --audience operator --channel docs
```

## Included modules

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

### Troubleshooting Guide

Solutions for common problems including webhook failures, credential errors, execution timeouts, and memory issues.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

#### Troubleshooting Guide: Troubleshooting

Problem → cause → solution. Start here when something breaks.

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

### Fix: Webhook trigger not firing

Troubleshoot Webhook nodes that do not receive requests. Common causes include inactive workflows, wrong URL type, and network configuration.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

#### Fix: Webhook trigger not firing: Fix: Webhook trigger not firing

The Webhook node does not respond to incoming HTTP requests. The sender receives a timeout, connection refused, or 404 error.

#### Fix: Webhook trigger not firing: Cause 1: Using Test URL with an inactive editor

**Symptom:** Requests to the Test URL return a timeout or 404 after you close the editor tab.

**Why:** The Test URL (`/webhook-test/<id>`) is only active while the workflow editor is open and the workflow is in Listening mode. Closing the browser tab deactivates it.

**Fix:** Toggle the workflow to **Active** and use the **Production URL** (`/webhook/<id>`) instead. The Production URL remains active as long as the workflow is enabled.

#### Fix: Webhook trigger not firing: Cause 2: Workflow not activated

**Symptom:** Requests to the Production URL return 404 Not Found.

**Why:** The Production URL only works when the workflow toggle is set to **Active** (green). An inactive workflow does not register its webhook endpoints.

**Fix:** Open the workflow in the editor. Toggle the **Active** switch in the top-right corner. Verify the Production URL returns a response.

### Fix: Webhook trigger not firing (Part 2)

Troubleshoot Webhook nodes that do not receive requests. Common causes include inactive workflows, wrong URL type, and network configuration.

#### Fix: Webhook trigger not firing (Part 2): Cause 3: Firewall or reverse proxy blocking requests

**Symptom:** Requests from external services timeout. Local `curl` requests work fine.

**Why:** The service listens on port 5678 by default. If your server firewall or reverse proxy (Nginx, Caddy, Traefik) does not route traffic to this port, external requests never reach it.

**Fix:**

=== "Docker with Nginx"

 Verify your Nginx config routes traffic to the container:

```nginx

 location /webhook/ {
 proxy_pass http://product:5678;
 proxy_set_header Host $host;
 proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
 }

```

=== "Direct install"

 Check that port 5678 is open:

```bash

 sudo ufw allow 5678
 # or
 sudo firewall-cmd --add-port=5678/tcp --permanent

```

#### Fix: Webhook trigger not firing (Part 2): Cause 4: Incorrect WEBHOOK_URL environment variable

**Symptom:** The Webhook node shows a URL that does not match your domain. External services cannot reach it.

**Why:** The service uses the `WEBHOOK_URL` environment variable to generate webhook URLs. If this is set to `http://localhost:5678` (the default), external services cannot resolve `localhost`.

**Fix:** Set `WEBHOOK_URL` to your public-facing URL:

```bash

export WEBHOOK_URL=https://product.yourdomain.com

```

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

### Define idempotent webhook retry handling

Provides retry and idempotency patterns to avoid duplicate processing across documentation, assistant guidance, and runbook automation.

Use idempotency keys to make webhook retries safe. Persist a processed-event key for at least 24 hours, and skip duplicate events with HTTP 200 to stop upstream retries. Use exponential backoff for outbound retries: one second, two seconds, four seconds, eight seconds, and 16 seconds, capped at five attempts.

```javascript

const retryScheduleSeconds = [1, 2, 4, 8, 16];

function shouldProcess(eventId, cache) {
  if (cache.has(eventId)) {
    return false;
  }
  cache.add(eventId);
  return true;
}

```

Alert when retry rate exceeds 5% for 15 minutes. This threshold usually indicates downstream instability.

## Next steps

- Validate modules: `npm run lint:knowledge`
- Rebuild retrieval index: `npm run build:knowledge-index`
- Generate assistant pack: `npm run build:intent -- --channel assistant`

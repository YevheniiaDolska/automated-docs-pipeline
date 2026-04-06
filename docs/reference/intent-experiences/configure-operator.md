---
title: "Intent experience: configure for operator"
description: "Assembled guidance for one intent and audience using reusable knowledge modules with verified metadata and channel-ready sections."
content_type: reference
product: both
tags:
  - Reference
  - AI
---

<!-- markdownlint-disable MD001 MD007 MD024 MD025 MD031 -->

# Intent experience: configure for operator

This page is assembled for the `configure` intent and the `operator` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent configure --audience operator --channel docs
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

### ASYNCAPI API Reference (Part 3)

Auto-generated asyncapi reference from source contract.

<div id="asyncapi-playground" style="border:1px solid #d1d5db; padding:12px; border-radius:8px;">
  <p><strong>WebSocket Endpoint:</strong> <code id="asyncapi-ws-view"></code></p>
  <p><strong>HTTP Publish Endpoint:</strong> <code id="asyncapi-http-view"></code></p>
  <textarea id="asyncapi-message" rows="8" style="width:100%; font-family:monospace;">{
  "event_type": "project.updated",
  "event_id": "evt_001",
  "data": {"project_id": "prj_abc123", "status": "active"}
}</textarea><br/>
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

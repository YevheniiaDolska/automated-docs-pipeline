---
title: 'Intent experience: troubleshoot for developer'
description: Assembled guidance for one intent and audience using reusable knowledge
  modules with verified metadata and channel-ready sections.
content_type: reference
product: both
tags:
- Reference
- AI
last_reviewed: '2026-03-26'
original_author: Developer
---


<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

# Intent experience: troubleshoot for developer

This page is assembled for the `troubleshoot` intent and the `developer` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent troubleshoot --audience developer --channel docs
```

## Included modules

### ASYNCAPI API Reference (Part 3)

Auto-generated asyncapi reference from source contract.

<div id="asyncapi-playground" style="border:1px solid #d1d5db; padding:12px; border-radius:8px;">
  <p><strong>WebSocket Endpoint:</strong> <code id="asyncapi-ws-view"></code></p>
  <p><strong>HTTP Publish Endpoint:</strong> <code id="asyncapi-http-view"></code></p>
  <!-- vale Google.Quotes = NO -->
  <textarea id="asyncapi-message" rows="8" style="width:100%; font-family:monospace;">{
  "event": "health",
  "value": "ok"
}</textarea><br/>
  <!-- vale Google.Quotes = YES -->
  <button id="asyncapi-send-ws">Send via WebSocket</button>
  <button id="asyncapi-send-http">Send via HTTP</button>
  <pre id="asyncapi-output" style="margin-top:12px; max-height:320px; overflow:auto;"></pre>
</div>
<script>
(function(){ const wsEndpoint = ""; const httpEndpoint = "";
const wsView = document.getElementById('asyncapi-ws-view');
const httpView = document.getElementById('asyncapi-http-view');
const sendWs = document.getElementById('asyncapi-send-ws');
const sendHttp = document.getElementById('asyncapi-send-http');
const msg = document.getElementById('asyncapi-message');
const out = document.getElementById('asyncapi-output');
if (!wsView || !httpView || !sendWs || !sendHttp || !msg || !out) return;
wsView.textContent = wsEndpoint || 'not configured';
httpView.textContent = httpEndpoint || 'not configured';
sendWs.onclick = function(){
  if (!wsEndpoint) { out.textContent = 'WebSocket endpoint is not configured (runtime.api_protocol_settings.asyncapi.asyncapi_ws_endpoint)'; return; }
  try {
    const socket = new WebSocket(wsEndpoint);
    socket.onopen = function(){ socket.send(msg.value); out.textContent = 'sent over websocket'; socket.close(); };
    socket.onerror = function(e){ out.textContent = String(e); };
    socket.onmessage = function(e){ out.textContent = String(e.data); };
  } catch (error) { out.textContent = String(error); }
};
sendHttp.onclick = async function(){
  if (!httpEndpoint) { out.textContent = 'HTTP publish endpoint is not configured (runtime.api_protocol_settings.asyncapi.asyncapi_http_publish_endpoint)'; return; }
  out.textContent = 'Loading...';
  try {
    const body = JSON.parse(msg.value || '{}');
    const response = await fetch(httpEndpoint, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify(body) });
    const text = await response.text();
    out.textContent = text;
  } catch (error) { out.textContent = String(error); }
};
})();
</script>

### AsyncAPI event docs (Part 12)

AsyncAPI 2.6.0 event documentation for VeriOps with channel contracts, delivery semantics, payload schemas, and interactive event tester.

function tryNext(lastError) {
      if (idx >= candidates.length) {
        out.textContent = JSON.stringify(
          {
            mode: 'offline-semantic-fallback',
            tried: candidates,
            last_error: lastError || '',
            simulated_response: semanticAsync(safeParse(payload))
          },
          null,
          2
        );
        return;
      }
      var endpoint = candidates[idx++];
      out.textContent = 'Connecting to ' + endpoint + '…';
      try {
        var settled = false;
        var ws = new WebSocket(endpoint);
        var timeout = setTimeout(function () {
          if (settled) return;
          settled = true;
          try { ws.close(); } catch (e) {}
          tryNext('timeout');
        }, 6000);
        ws.onopen = function () {
          if (settled) return;
          ws.send(payload);
          out.textContent = 'Connected to ' + endpoint + '. Event sent. Waiting for acknowledgement…';
        };
        ws.onmessage = function (e) {
          if (settled) return;
          settled = true;
          clearTimeout(timeout);
          out.textContent = JSON.stringify(
            {
              endpoint: endpoint,
              mode: 'live-echo-plus-semantic',
              raw: String(e.data || ''),
              simulated_response: semanticAsync(safeParse(e.data))
            },
            null,
            2
          );
          ws.close();
        };
        ws.onerror = function () {
          if (settled) return;
          settled = true;
          clearTimeout(timeout);
          tryNext('handshake failed');
        };
        ws.onclose = function () {
          if (settled) return;
          settled = true;
          clearTimeout(timeout);
          tryNext('closed before response');
        };
      } catch (e) {
        tryNext(String(e));
      }
    }

### AsyncAPI event docs (Part 13)

AsyncAPI 2.6.0 event documentation for VeriOps with channel contracts, delivery semantics, payload schemas, and interactive event tester.

tryNext('');
  };
})();
</script>

## Error handling

| Error | Cause | Resolution |
| --- | --- | --- |
| `CONNECTION_REFUSED` | Broker unreachable | Verify `events.veriops.example:5672` is accessible from your network |
| `AUTH_FAILED` | Invalid credentials | Check bearer token or SASL credentials |
| `CHANNEL_NOT_FOUND` | Invalid channel name | Use exact channel names from the catalog above |
| `PAYLOAD_TOO_LARGE` | Message exceeds 256 KB | Reduce payload size or split into multiple events |
| `CONSUMER_TIMEOUT` | No ACK within 300 seconds | Acknowledge messages faster or increase prefetch count |

## Next steps

- [WebSocket event playground](websocket-events.md) for bidirectional real-time messaging
- [REST API reference](rest-api.md) for synchronous CRUD operations
- [Tutorial: launch your first integration](../guides/tutorial.md) to subscribe to events end-to-end

### Concept: pipeline-first documentation lifecycle (Part 7)

Pipeline-first documentation automates generation, validation, and publishing of API docs from source contracts, reducing review cycles by 60%.

| Check ID | Rule | Severity | Threshold |
| --- | --- | --- | --- |
| GEO-1 | Meta description present | Error | Must exist |
| GEO-1b | Meta description length (minimum) | Warning | 50 characters minimum |
| GEO-1c | Meta description length (maximum) | Warning | 160 characters maximum |
| GEO-2 | First paragraph length | Warning | 60 words maximum |
| GEO-3 | First paragraph definition pattern | Suggestion | Contains "is," "enables," "provides," or "allows" |
| GEO-4 | Heading specificity | Warning | No generic headings (overview, setup, configuration) |
| GEO-5 | Heading hierarchy | Error | No skipped levels (H2 to H4 is invalid) |
| GEO-6 | Fact density | Warning | At least one fact per 200 words |
| SEO-01 | Title length | Error/Warning | 10-70 characters |
| SEO-02 | Title keyword match | Suggestion | 50% overlap with filename keywords |
| SEO-03 | URL depth | Warning | Max 4 directory levels |
| SEO-04 | URL naming | Warning | Kebab-case only |
| SEO-05 | Image alt text | Warning | 100% of images must have alt text |
| SEO-06 | Internal links | Suggestion | At least 1 per page |
| SEO-07 | Bare URLs | Warning | All URLs must use `[text](url)` format |
| SEO-08 | Path special characters | Warning | Alphanumeric and hyphens only |
| SEO-09 | Line length | Warning | Max 120 characters outside code blocks |
| SEO-10 | Heading keyword overlap | Suggestion | H2 headings share keywords with title |
| SEO-11 | Freshness signal | Suggestion | `last_reviewed` or `date` in frontmatter |
| SEO-12 | Content depth | Warning | Minimum 100 words |
| SEO-13 | Duplicate headings | Warning | No two headings share the same text |
| SEO-14 | Structured data | Suggestion | At least 1 table, code block, or list |

### Quality evidence and gate results

Complete quality evidence from the VeriDoc pipeline for VeriOps docs, covering KPI metrics, protocol gates, 24 automated checks, and RAG readiness.

# Quality evidence and gate results

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-7c3aed?style=flat-square)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-7c3aed?style=flat-square)

</div>

This page provides the complete quality evidence generated by the VeriDoc pipeline for the VeriOps documentation site. It covers KPI metrics, protocol gate results, 24 automated quality checks, RAG retrieval readiness, and all pipeline artifacts.

## KPI metrics

These metrics come from `reports/acme-demo/kpi-wall.json`:

| Metric | Value | Target | Status |
| --- | --- | --- | --- |
| Quality score | **100%** | 80% | Excellent |
| Total documents | **12** | -- | Indexed across all protocols |
| Stale pages | **0** | 0 | No stale pages |
| Documentation gaps | **0** | 0 | No active gaps |
| Metadata completeness | **100%** | 100% | All frontmatter fields present and valid |
| Frontmatter errors | **0** | 0 | All pages pass schema validation |

### Quality evidence and gate results (Part 3)

Complete quality evidence from the VeriDoc pipeline for VeriOps docs, covering KPI metrics, protocol gates, 24 automated checks, and RAG readiness.

### GEO checks (8 checks -- LLM and AI search optimization)

| Check ID | Rule | Severity | Threshold | Purpose |
| --- | --- | --- | --- | --- |
| GEO-1 | Meta description present | Error | Must exist | Ensures every page has a description for search snippets |
| GEO-1b | Meta description minimum length | Warning | 50 characters | Prevents truncated search snippets |
| GEO-1c | Meta description maximum length | Warning | 160 characters | Prevents overflow in search results |
| GEO-2 | First paragraph length | Warning | 60 words max | Ensures concise opening for LLM extraction |
| GEO-3 | First paragraph definition | Suggestion | Contains definition verb | Helps LLMs identify what the page is about |
| GEO-4 | Heading specificity | Warning | No generic headings | Prevents vague headings like "Overview" or "Setup" |
| GEO-5 | Heading hierarchy | Error | No skipped levels | Ensures proper H2-H3-H4 nesting |
| GEO-6 | Fact density | Warning | 1 fact per 200 words | Keeps content information-rich |

### Quality evidence and gate results (Part 5)

Complete quality evidence from the VeriDoc pipeline for VeriOps docs, covering KPI metrics, protocol gates, 24 automated checks, and RAG readiness.

| Check ID | Rule | Severity | Threshold | Purpose |
| --- | --- | --- | --- | --- |
| SEO-01 | Title length | Error/Warning | 10-70 characters | Optimal title display in search results |
| SEO-02 | Title keyword match | Suggestion | 50% overlap | Aligns title with filename keywords |
| SEO-03 | URL depth | Warning | Max 4 levels | Prevents deep URLs that search engines deprioritize |
| SEO-04 | URL naming | Warning | Kebab-case | Consistent, readable URL structure |
| SEO-05 | Image alt text | Warning | 100% coverage | Accessibility and image search visibility |
| SEO-06 | Internal links | Suggestion | Min 1 link | Cross-references improve crawlability |
| SEO-07 | Bare URLs | Warning | Zero bare URLs | Requires descriptive link text |
| SEO-08 | Path characters | Warning | Alphanumeric + hyphens | Prevents encoding issues in URLs |
| SEO-09 | Line length | Warning | Max 120 characters | Mobile readability |
| SEO-10 | Heading keywords | Suggestion | Shared with title | Signals relevance to search engines |
| SEO-11 | Freshness signal | Suggestion | Date in frontmatter | Indicates content currency |
| SEO-12 | Content depth | Warning | Min 100 words | Prevents thin content penalties |
| SEO-13 | Duplicate headings | Warning | Zero duplicates | Unique headings for anchor links |
| SEO-14 | Structured data | Suggestion | Min 1 element | Tables, code blocks, or lists |

### GRAPHQL API Reference (Part 2)

Auto-generated graphql reference from source contract.

## Interactive GraphQL Playground

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
(function(){ const endpoint = "";
const view = document.getElementById('graphql-endpoint-view');
const run = document.getElementById('graphql-run');
const query = document.getElementById('graphql-query');
const out = document.getElementById('graphql-output');
if (!view || !run || !query || !out) return;
view.textContent = endpoint || 'not configured';
run.onclick = async function(){
  if (!endpoint) { out.textContent = 'Endpoint is not configured in runtime.api_protocol_settings.graphql.graphql_endpoint'; return; }
  out.textContent = 'Loading...';
  try {
    const response = await fetch(endpoint, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({ query: query.value }) });
    const text = await response.text();
    out.textContent = text;
  } catch (error) { out.textContent = String(error); }
};
})();
</script>

### GraphQL playground

Interactive GraphQL playground for VeriOps API with schema explorer, live query editor, subscription support, and advanced RAG retrieval pipeline.

# GraphQL playground

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-7c3aed?style=flat-square)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-7c3aed?style=flat-square)

</div>

The VeriOps GraphQL API provides a single endpoint for flexible queries across projects, tasks, and users. This page documents the full schema, provides a live query editor, covers authentication, error handling, performance limits, and the advanced RAG retrieval pipeline that powers AI-driven search across GraphQL documentation.

## Endpoint and authentication

| Setting | Value |
| --- | --- |
| Endpoint | [`https://api.veriops.example/graphql`](https://api.veriops.example/graphql) |
| Method | POST |
| Authentication | Bearer token in `Authorization` header |
| Content type | `application/json` |
| Max query depth | 10 levels |
| Max query complexity | 500 points |
| Rate limit | 60 requests per minute |
| Introspection | Enabled in development, disabled in production |

## Schema overview

The VeriOps GraphQL schema exposes three operation types and one core object type:

### GraphQL playground (Part 7)

Interactive GraphQL playground for VeriOps API with schema explorer, live query editor, subscription support, and advanced RAG retrieval pipeline.

### Multi-mode retrieval evaluation

The `run_retrieval_evals.py` script supports four search modes for comparison:

| Mode | Strategy | Use case |
| --- | --- | --- |
| `token` | Token-overlap scoring | Baseline, no API key required |
| `semantic` | FAISS cosine similarity | Embedding-based retrieval |
| `hybrid` | RRF fusion of token + semantic | Best recall for mixed queries |
| `hybrid+rerank` | Hybrid + cross-encoder reranking | Highest precision for production |

Run a full comparison:

```bash
python3 scripts/run_retrieval_evals.py \
  --mode all \
  --use-embeddings \
  --dataset config/retrieval_eval_dataset.yml \
  --report reports/retrieval_comparison.json
```

<!-- requires: OPENAI_API_KEY, faiss-cpu, sentence-transformers -->

## Error handling

GraphQL errors appear in the `errors` array alongside partial `data`:

```json
{
  "data": null,
  "errors": [
    {
      "message": "Project not found",
      "locations": [{"line": 2, "column": 3}],
      "path": ["project"],
      "extensions": {
        "code": "NOT_FOUND",
        "timestamp": "2026-03-20T14:30:00Z"
      }
    }
  ]
}
```

### GraphQL playground (Part 8)

Interactive GraphQL playground for VeriOps API with schema explorer, live query editor, subscription support, and advanced RAG retrieval pipeline.

### Error codes

| Code | HTTP equivalent | Meaning | Resolution |
| --- | --- | --- | --- |
| `UNAUTHENTICATED` | 401 | Missing or invalid bearer token | Provide a valid `Authorization: Bearer` header |
| `FORBIDDEN` | 403 | Token valid but lacks required scope | Request the `graphql:read` or `graphql:write` scope |
| `NOT_FOUND` | 404 | Requested resource does not exist | Verify the resource ID |
| `QUERY_TOO_COMPLEX` | 400 | Query exceeds 500 complexity points | Reduce nesting depth or remove unnecessary fields |
| `QUERY_TOO_DEEP` | 400 | Query exceeds 10 levels of nesting | Flatten the query or use separate requests |
| `RATE_LIMITED` | 429 | Exceeded 60 requests per minute | Implement request throttling on the client |
| `INTERNAL_ERROR` | 500 | Server error | Retry with exponential backoff (max 3 attempts) |

## Performance limits

| Limit | Value | Notes |
| --- | --- | --- |
| Max query depth | 10 levels | Nested field resolution depth |
| Max complexity | 500 points | Each field costs 1 point, lists cost 10 points |
| Max query size | 10 KB | Request body size limit |
| Timeout | 30 seconds | Per-query execution timeout |
| Batch queries | Up to 5 | Multiple queries in one request |

### gRPC gateway invoke (Part 7)

Invoke VeriOps gRPC services through the HTTP gateway with service catalog, proto definitions, and interactive request testing.

## Error handling and gRPC status codes

The HTTP gateway maps gRPC status codes to HTTP status codes:

| gRPC status | HTTP status | Description | Resolution |
| --- | --- | --- | --- |
| `OK` (0) | 200 | Success | -- |
| `INVALID_ARGUMENT` (3) | 400 | Malformed request or invalid field | Check the `payload` JSON matches the proto message |
| `UNAUTHENTICATED` (16) | 401 | Missing or invalid bearer token | Provide a valid `Authorization` header |
| `PERMISSION_DENIED` (7) | 403 | Token valid but lacks scope | Request `grpc:invoke` scope from admin |
| `NOT_FOUND` (5) | 404 | Resource does not exist | Verify the project ID format (`prj_*`) |
| `DEADLINE_EXCEEDED` (4) | 504 | RPC took longer than 30 seconds | Increase deadline or optimize the query |
| `UNAVAILABLE` (14) | 503 | Service temporarily unavailable | Retry with exponential backoff (3 attempts, initial 1 second) |
| `INTERNAL` (13) | 500 | Server error | Retry with exponential backoff |

### How-to: keep docs aligned with every release (Part 4)

Run the unified autopipeline on release day to synchronize API documentation across five protocols with quality gates and review manifests.

```text
[autopipeline] Starting VeriDoc pipeline run
[autopipeline] Runtime config: reports/acme-demo/client_runtime.yml
[autopipeline] Protocols enabled: rest, graphql, grpc, asyncapi, websocket
[stage] multi_protocol_contract ... DONE (5 protocols, 0 failures)
[stage] kpi_wall ... DONE (quality_score: 100)
[stage] retrieval_evals ... DONE (167 modules indexed)
[autopipeline] Pipeline complete. Exit code: 0
```

An exit code of 0 confirms all stages passed. A non-zero code indicates stages that need attention.

## Step 2: check protocol contract results

After the pipeline completes, verify which protocols passed contract validation:

```bash
python3 -c "
import json
r = json.load(open('reports/acme-demo/multi_protocol_contract_report.json'))
for p in r.get('protocols', []):
    status = 'PASS' if p not in r.get('failed_protocols', []) else 'FAIL'
    print(f'  {p}: {status}')
print(f'Failed: {r.get(\"failed_protocols\", [])}')"
```

**Expected output:**

```text
  rest: PASS
  graphql: PASS
  grpc: PASS
  asyncapi: PASS
  websocket: PASS
Failed: []
```

If any protocol fails, fix the root cause before proceeding. See [Troubleshooting](troubleshooting.md) for common fixes.

### How-to: keep docs aligned with every release (Part 7)

Run the unified autopipeline on release day to synchronize API documentation across five protocols with quality gates and review manifests.

## Step 5: build the demo site

Generate the browsable MkDocs documentation site:

```bash
python3 scripts/build_acme_demo_site.py \
  --output-root demo-showcase/acme \
  --reports-dir reports/acme-demo \
  --build
```

<!-- requires: python3, mkdocs -->

This command copies documentation pages, updates the `mkdocs.yml` navigation, and runs `mkdocs build` to produce the final HTML site in `demo-showcase/acme/site/`.

## Step 6: approve and publish

After verifying all gates pass, complete the reviewer checklist from the manifest:

- [ ] Confirm stage summary has no missing required artifacts.
- [ ] Review protocol docs and test asset links.
- [ ] Review quality and retrieval reports before publish.
- [ ] Approve publish only if critical findings are resolved.
- [ ] Verify RAG retrieval index is current and complete.
- [ ] Confirm advanced retrieval features are enabled (hybrid search, HyDE, reranking, embedding cache).

## Validation checklist

Before considering the release complete:

- [ ] All five protocol contracts validated (zero failures)
- [ ] Quality score at or above 80
- [ ] No high-priority documentation gaps remain
- [ ] Review manifest approved by operator
- [ ] MkDocs site builds without errors
- [ ] Knowledge graph and retrieval index are current
- [ ] Advanced retrieval features enabled (hybrid, HyDE, reranking, cache)

## Common issues and solutions

### How-to: keep docs aligned with every release (Part 8)

Run the unified autopipeline on release day to synchronize API documentation across five protocols with quality gates and review manifests.

### Issue: gRPC stage fails

The `protoc` compiler is not installed.

**Solution:**

```bash
apt-get install -y protobuf-compiler
protoc --version
```

Then re-run the pipeline.

### Issue: quality score below 80

Stale documents, missing frontmatter, or unresolved documentation gaps.

**Solution:**

1. Run `python3 -c "import json; r=json.load(open('reports/acme-demo/doc_gaps_report.json')); print(len([g for g in r.get('gaps',[]) if g.get('priority')=='high']), 'high-priority gaps')"` to count gaps.
1. Address each gap by creating or updating documents.
1. Re-run the pipeline.

### Issue: MkDocs build fails with theme error

**Solution:**

```bash
pip install mkdocs-material mkdocs-macros-plugin
```

## Next steps

- [Concept: pipeline-first documentation lifecycle](concept.md) to understand why this workflow matters
- [Quality evidence and gate results](../quality/evidence.md) for the latest KPI metrics
- [Troubleshooting: common pipeline issues](troubleshooting.md) for detailed fix procedures

### VeriOps documentation (Part 5)

Pipeline-generated multi-protocol API documentation for VeriOps with KPI dashboard, interactive references, and automated quality gates.

## Automated detection and repair

The pipeline detects documentation drift when source contracts change and regenerates affected pages automatically.

!!! example "Protocol drift detected and repaired"

    **Before:** The GraphQL schema added a new `priority` field to the `Project` type, but the GraphQL playground docs still listed only `id`, `name`, `status`, and `createdAt`.

    **Detection:** The `multi_protocol_contract` stage compared `contracts/graphql.schema.graphql` against the generated docs and flagged the missing field as a regression.

    **Autofix:** The pipeline regenerated the GraphQL reference page, added the `priority` field to the schema explorer table and query examples, and re-ran all 24 quality checks.

    **Result:** Re-validation passed. No manual editing required.

### VeriOps documentation (Part 8)

Pipeline-generated multi-protocol API documentation for VeriOps with KPI dashboard, interactive references, and automated quality gates.

## Quick links

- [REST API reference (Swagger)](reference/rest-api.md) -- 14 endpoints for projects, tasks, users, tags, and comments
- [GraphQL playground](reference/graphql-playground.md) -- live query editor with schema explorer
- [gRPC gateway invoke](reference/grpc-gateway.md) -- HTTP gateway adapter for `ProjectService`
- [AsyncAPI event docs](reference/asyncapi-events.md) -- event-driven channels with delivery semantics
- [WebSocket event playground](reference/websocket-events.md) -- bidirectional real-time messaging
- [Tutorial: launch your first integration](guides/tutorial.md) -- zero to working project in 15 minutes
- [How-to: keep docs aligned](guides/how-to.md) -- release-day pipeline workflow
- [Concept: pipeline-first lifecycle](guides/concept.md) -- why automated docs beat manual writing
- [Troubleshooting: pipeline issues](guides/troubleshooting.md) -- diagnose and fix common failures
- [Quality evidence and gate results](quality/evidence.md) -- KPI metrics and protocol gate details

### REST API reference

Interactive REST API reference for VeriOps with 14 endpoints across five resources, Bearer JWT authentication, and Swagger UI.

# REST API reference

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-7c3aed?style=flat-square)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-7c3aed?style=flat-square)

</div>

The VeriOps REST API provides 14 CRUD endpoints across five resources (projects, tasks, users, tags, and comments) over HTTP/1.1 with JSON payloads. This reference documents every endpoint, authentication flow, and error code.

## Base URL and authentication

| Setting | Value |
| --- | --- |
| Base URL | [`https://api.veriops.example/v1`](https://api.veriops.example/v1) |
| Authentication | Bearer JWT token in `Authorization` header |
| Content type | `application/json` |
| Rate limit | 60 requests per minute per API key |
| OpenAPI spec version | 3.0.3 |
| API version | v1 |

All requests require a valid JWT token:

```bash
curl -X GET https://api.veriops.example/v1/projects \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

<!-- requires: api-key -->

### REST API reference (Part 7)

Interactive REST API reference for VeriOps with 14 endpoints across five resources, Bearer JWT authentication, and Swagger UI.

### Comments

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/v1/comments?task_id={id}` | List comments on a task |
| `POST` | `/v1/comments` | Add a comment to a task |
| `DELETE` | `/v1/comments/{id}` | Delete a comment |

## Interactive Swagger UI

Explore and test all 14 endpoints in the embedded Swagger interface. Requests route to the Postman mock server sandbox automatically.

!!! info "Sandbox mode"
    All Try-it requests from Swagger UI route to the Postman mock server at
    [`https://662b99a9-ac2a-4096-8a8e-480a73cef3e3.mock.pstmn.io/v1`](https://662b99a9-ac2a-4096-8a8e-480a73cef3e3.mock.pstmn.io/v1).
    No API key is required for sandbox requests.

<div style="border:1px solid #dbe2ea;border-radius:12px;overflow:hidden;">
<iframe src="../swagger-test.html" width="100%" height="900" style="border:none;"></iframe>
</div>

## Error handling

Every error response uses a consistent envelope:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The 'name' field is required and must be 3-100 characters.",
    "details": [
      {
        "field": "name",
        "rule": "required",
        "message": "This field is required"
      }
    ]
  }
}
```

### REST API reference (Part 8)

Interactive REST API reference for VeriOps with 14 endpoints across five resources, Bearer JWT authentication, and Swagger UI.

### Error codes

| Status | Code | Meaning | Resolution |
| --- | --- | --- | --- |
| 400 | `validation_error` | Request body fails validation | Check the `details` array for specific field errors |
| 401 | `unauthorized` | Missing or invalid JWT token | Regenerate your token in the [dashboard](https://app.veriops.example/settings/api) |
| 403 | `forbidden` | Token valid but lacks permission | Request the required scope from your admin |
| 404 | `not_found` | Resource does not exist | Verify the resource ID in the URL path |
| 409 | `conflict` | Duplicate resource | A resource with that unique key already exists |
| 429 | `rate_limited` | Exceeded 60 requests per minute | Wait 60 seconds or implement request queuing |
| 500 | `internal_error` | Server error | Retry with exponential backoff (max 3 attempts, initial delay 1 second) |

## Rate limiting

The API enforces a limit of 60 requests per minute per API key. Rate limit headers appear on every response:

| Header | Description |
| --- | --- |
| `X-RateLimit-Limit` | Maximum requests per window (60) |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when the window resets |

When you exceed the limit, the API returns HTTP 429 with a `Retry-After` header indicating seconds to wait.

### WebSocket event playground (Part 9)

Interactive WebSocket playground for VeriOps real-time API with bidirectional messaging, channel subscriptions, and connection lifecycle management.

<script>
/* Sandbox onclick is set by acme-sandbox.js with local mock responses */
</script>

## WebSocket error handling

### WebSocket close codes

| Close code | Meaning | Client action |
| --- | --- | --- |
| 1000 | Normal closure | No action required |
| 1001 | Server going away | Reconnect with exponential backoff |
| 1006 | Abnormal close (no close frame) | Reconnect with exponential backoff |
| 1008 | Policy violation | Check message format and size |
| 4001 | Authentication failed | Verify your API key is valid and not expired |
| 4002 | Subscription limit reached | Unsubscribe from unused channels (max 50) |
| 4008 | Rate limited | Wait 60 seconds before reconnecting |
| 4009 | Message too large | Reduce message size to under 64 KB |

### Common issues

| Symptom | Cause | Resolution |
| --- | --- | --- |
| Connection drops every 30 seconds | Client not responding to `ping` | Implement `pong` response handler |
| Connection drops after 5 minutes | No messages sent or received | Send periodic messages or respond to pings |
| `Connection error` in browser | Mixed content (`ws://` on HTTPS page) | Use `wss://` endpoint |
| Missed events after reconnect | Subscriptions not restored | Re-subscribe to all channels on `open` event |

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

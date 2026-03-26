---
title: "Intent experience: troubleshoot for operator"
description: "Assembled guidance for one intent and audience using reusable knowledge modules with verified metadata and channel-ready sections."
content_type: reference
product: both
tags:
  - Reference
  - AI
---

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

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

### Troubleshooting: common VeriOps pipeline issues

Fix common VeriOps documentation pipeline issues in under 5 minutes, covering contract failures, quality gates, build errors, and WebSocket problems.

# Troubleshooting: common VeriOps pipeline issues

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-7c3aed?style=flat-square)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-7c3aed?style=flat-square)

</div>

Your VeriOps documentation pipeline is failing with contract validation errors, quality gate warnings, or build failures. This guide fixes 95% of pipeline issues in under 5 minutes.

## Quick diagnosis (30 seconds)

Check the pipeline exit code and stage summary first:

```bash
python3 -c "
import json
s = json.load(open('reports/acme-demo/pipeline_stage_summary.json'))
for stage in s.get('stages', []):
    status = 'EXISTS' if stage.get('exists') else 'MISSING'
    print(f'  {stage[\"name\"]}: {status}')
m = json.load(open('reports/acme-demo/review_manifest.json'))
print(f'Exit code: {m[\"weekly_rc\"]}')
print(f'Available: {m[\"available_artifacts\"]}, Missing: {m[\"missing_artifacts\"]}')"
```

### Troubleshooting: common VeriOps pipeline issues (Part 2)

Fix common VeriOps documentation pipeline issues in under 5 minutes, covering contract failures, quality gates, build errors, and WebSocket problems.

## Diagnosis table

| Symptom | Frequency | Fix time | Solution |
| --- | --- | --- | --- |
| gRPC contract fails | 40% | 2 min | [Contract validation fails for gRPC](#contract-validation-fails-for-grpc) |
| Quality score below 80 | 25% | 5 min | [Quality score drops below 80](#quality-score-drops-below-80) |
| MkDocs build fails | 15% | 1 min | [MkDocs build fails with theme error](#mkdocs-build-fails-with-theme-error) |
| WebSocket tester error | 10% | 1 min | [WebSocket tester shows connection error](#websocket-tester-shows-connection-error) |
| Reports directory empty | 5% | 2 min | [Pipeline reports directory is empty](#pipeline-reports-directory-is-empty) |
| RAG retrieval low precision | 5% | 10 min | [Retrieval precision below threshold](#retrieval-precision-below-threshold) |

## Contract validation fails for gRPC

**You see:** The `multi_protocol_contract_report.json` shows `grpc` in `failed_protocols`.

```json
{
  "failed_protocols": ["grpc"],
  "protocols": ["rest", "graphql", "grpc", "asyncapi", "websocket"]
}
```

**Root cause:** The `protoc` compiler is not installed, or the proto files reference missing imports.

### Troubleshooting: common VeriOps pipeline issues (Part 3)

Fix common VeriOps documentation pipeline issues in under 5 minutes, covering contract failures, quality gates, build errors, and WebSocket problems.

### Fix gRPC contract in 2 minutes

1. Install the protobuf compiler:

    ```bash
    apt-get install -y protobuf-compiler
    protoc --version
    ```

    Expected output: `libprotoc 3.21.x` or later.

1. Verify proto file paths match `client_runtime.yml`:

    ```yaml
    grpc:
      proto_paths:
        - reports/acme-demo/contracts/grpc
    ```

1. Re-run the pipeline:

    ```bash
    python3 scripts/run_autopipeline.py \
      --docsops-root . \
      --reports-dir reports/acme-demo \
      --runtime-config reports/acme-demo/client_runtime.yml \
      --mode veridoc
    ```

1. Verify gRPC passes:

    ```bash
    python3 -c "
    import json
    r = json.load(open('reports/acme-demo/multi_protocol_contract_report.json'))
    print('Failed:', r.get('failed_protocols', []))"
    ```

    Expected output: `Failed: []`

## Quality score drops below 80

**You see:** The `kpi-wall.json` shows `quality_score` below 80.

**Root cause:** Stale documents, missing frontmatter, or unresolved documentation gaps lower the quality score below the 80 threshold.

### Troubleshooting: common VeriOps pipeline issues (Part 4)

Fix common VeriOps documentation pipeline issues in under 5 minutes, covering contract failures, quality gates, build errors, and WebSocket problems.

### Fix quality score in 5 minutes

1. Check the gap report for high-priority items:

    ```bash
    python3 -c "
    import json
    r = json.load(open('reports/acme-demo/doc_gaps_report.json'))
    high = [g for g in r.get('gaps', []) if g.get('priority') == 'high']
    print(f'{len(high)} high-priority gaps:')
    for g in high:
        print(f'  [{g[\"priority\"]}] {g[\"title\"]}')"
    ```

1. Address each high-priority gap by creating or updating the relevant document. Common gaps include:

    | Gap category | Typical fix |
    | --- | --- |
    | `authentication` | Add authentication guide with token management |
    | `webhook` | Document webhook setup and payload schemas |
    | `database_schema` | Add data model reference with field descriptions |
    | `error_handling` | Create error code reference with resolution steps |

1. Re-run the pipeline and verify the score:

    ```bash
    python3 -c "
    import json
    print(json.load(open('reports/acme-demo/kpi-wall.json'))['quality_score'])"
    ```

## MkDocs build fails with theme error

**You see:** `mkdocs build` exits with `Theme 'material' not found` or `Module 'mkdocs_macros' not found`.

**Root cause:** The required Python packages are not installed in the current environment.

### Troubleshooting: common VeriOps pipeline issues (Part 5)

Fix common VeriOps documentation pipeline issues in under 5 minutes, covering contract failures, quality gates, build errors, and WebSocket problems.

### Fix MkDocs theme in 1 minute

```bash
pip install mkdocs-material mkdocs-macros-plugin pymdown-extensions
```

Verify the build succeeds:

```bash
cd demo-showcase/acme && mkdocs build --strict
```

Expected output: `INFO - Documentation built in X.XX seconds`

## WebSocket tester shows connection error

**You see:** The interactive WebSocket tester on the [WebSocket event playground](../reference/websocket-events.md) displays "Connection error."

**Root cause:** The browser blocks insecure WebSocket connections (`ws://`) from HTTPS pages, or the endpoint is unreachable.

### Fix WebSocket connection in 1 minute

- Verify the endpoint uses `wss://` (not `ws://`). The correct endpoint is `wss://api.acme.example/realtime`.
- Confirm the endpoint is accessible from your network. Try from the command line:

    ```bash
    curl -s -o /dev/null -w "%{http_code}" https://api.acme.example/realtime
    ```

- Check browser developer tools (Console tab) for specific error messages.
- If you use a corporate proxy, configure WebSocket passthrough or use the [AsyncAPI event docs](../reference/asyncapi-events.md) with direct AMQP instead.

### Troubleshooting: common VeriOps pipeline issues (Part 6)

Fix common VeriOps documentation pipeline issues in under 5 minutes, covering contract failures, quality gates, build errors, and WebSocket problems.

## Pipeline reports directory is empty

**You see:** The `reports/acme-demo/` directory contains no JSON files after running the autopipeline.

**Root cause:** The runtime config path is incorrect, or the `--reports-dir` argument points to a different location.

### Fix empty reports in 2 minutes

1. Verify the runtime config exists:

    ```bash
    ls -la reports/acme-demo/client_runtime.yml
    ```

1. Run the pipeline with explicit paths:

    ```bash
    python3 scripts/run_autopipeline.py \
      --docsops-root . \
      --reports-dir reports/acme-demo \
      --runtime-config reports/acme-demo/client_runtime.yml \
      --mode veridoc
    ```

1. Verify reports are generated:

    ```bash
    ls reports/acme-demo/*.json | head -10
    ```

    Expected output: at least 5 JSON report files.

## Retrieval precision below threshold

**You see:** The `retrieval_evals_report.json` shows precision below 0.7 or recall below 0.8.

**Root cause:** The token-overlap baseline scorer runs without external dependencies and produces conservative scores. Enable advanced retrieval features (hybrid search, HyDE, cross-encoder reranking) for production-grade precision and recall.

### Troubleshooting: common VeriOps pipeline issues (Part 7)

Fix common VeriOps documentation pipeline issues in under 5 minutes, covering contract failures, quality gates, build errors, and WebSocket problems.

### Fix retrieval precision in 10 minutes

1. Check the retrieval evaluation report:

```bash
    python3 -c "
    import json
    r = json.load(open('reports/acme-demo/retrieval_evals_report.json'))
    print(f'Status: {r[\"status\"]}')
    print(f'Precision: {r[\"precision\"]}')
    print(f'Recall: {r[\"recall\"]}')
    print(f'Hallucination rate: {r[\"hallucination_rate\"]}')"
    ```

1. Run a multi-mode comparison to identify the best search strategy:

```bash
    python3 scripts/run_retrieval_evals.py \
      --mode all \
      --dataset config/retrieval_eval_dataset.yml \
      --report reports/retrieval_comparison.json
    ```

This compares token, semantic, hybrid, and hybrid+rerank modes side by side.

1. Improve knowledge module coverage:

- Add more detailed content to documentation pages (each page should have at least 100 words)
    - Include code examples with inline comments (the knowledge extractor indexes code blocks)
    - Add tables with specific values (the knowledge extractor indexes structured data)

1. Rebuild the retrieval index with chunking:

```bash
    python3 scripts/validate_knowledge_modules.py
    python3 scripts/generate_knowledge_retrieval_index.py
    python3 scripts/generate_embeddings.py --chunk \
      --index docs/assets/knowledge-retrieval-index.json \
      --output-dir docs/assets/
    ```

### Troubleshooting: common VeriOps pipeline issues (Part 8)

Fix common VeriOps documentation pipeline issues in under 5 minutes, covering contract failures, quality gates, build errors, and WebSocket problems.

1. Verify advanced retrieval features are enabled in `config/ask-ai.yml`:

```yaml
    hybrid_search:
      enabled: true
    hyde:
      enabled: true
    reranking:
      enabled: true
    embedding_cache:
      enabled: true
    ```

1. Re-run retrieval evaluations:

```bash
    python3 scripts/run_autopipeline.py \
      --docsops-root . \
      --reports-dir reports/acme-demo \
      --runtime-config reports/acme-demo/client_runtime.yml \
      --mode veridoc
    ```

## Prevention checklist

Prevent 90% of pipeline issues with these practices:

- [ ] **Install all dependencies**: `protoc`, `mkdocs-material`, `pymdown-extensions`
- [ ] **Run the pipeline before every release**: Do not wait for the weekly schedule
- [ ] **Address high-priority gaps immediately**: They compound and lower the quality score
- [ ] **Keep contract files current**: Update OpenAPI, GraphQL schema, and proto files with every API change
- [ ] **Monitor the KPI dashboard**: Check `kpi-wall.json` quality score after every run

### Troubleshooting: common VeriOps pipeline issues (Part 9)

Fix common VeriOps documentation pipeline issues in under 5 minutes, covering contract failures, quality gates, build errors, and WebSocket problems.

## Performance baseline

After resolving issues, your pipeline should show:

| Metric | Good | Warning | Critical |
| --- | --- | --- | --- |
| Quality score | 80+ | 70-79 | Below 70 |
| Failed protocols | 0 | 1 | 2 or more |
| High-priority gaps | 0-2 | 3-5 | 6 or more |
| Pipeline exit code | 0 | 1 (non-critical) | 2 (critical failure) |
| Retrieval precision | 0.7+ | 0.5-0.69 | Below 0.5 |

## Next steps

- [How-to: keep docs aligned with every release](how-to.md) for the operational workflow
- [Quality evidence and gate results](../quality/evidence.md) for current gate status
- [Concept: pipeline-first documentation lifecycle](concept.md) to understand the pipeline architecture

### WebSocket event playground (Part 9)

Interactive WebSocket playground for VeriOps real-time API with bidirectional messaging, channel subscriptions, and connection lifecycle management.

<script>
/* Sandbox onclick is set by acme-sandbox.js with local mock responses */
</script>

## Error handling

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

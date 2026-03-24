---
title: "Intent experience: configure for practitioner"
description: "Assembled guidance for one intent and audience using reusable knowledge modules with verified metadata and channel-ready sections."
content_type: reference
product: both
tags:
  - Reference
  - AI
---

# Intent experience: configure for practitioner

This page is assembled for the `configure` intent and the `practitioner` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent configure --audience practitioner --channel docs
```

## Included modules

### How-to: keep docs aligned with every release

Run the unified autopipeline on release day to synchronize API documentation across five protocols with quality gates and review manifests.

## How-to: keep docs aligned with every release

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-7c3aed?style=flat-square)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-7c3aed?style=flat-square)

</div>

This guide shows you how to run the unified autopipeline on release day to ensure API documentation matches the latest contracts, passes quality gates, and generates a review manifest for operator approval. You complete the full flow in approximately 20 minutes.

## Prerequisites

Before starting, ensure you have:

- Python 3.9 or later installed (run `python3 --version` to verify)
- Node.js 18 or later for MkDocs plugins (run `node --version` to verify)
- `pip install mkdocs-material mkdocs-macros-plugin` for site building
- Write access to the documentation repository
- About 20 minutes for the full pipeline run

!!! info "Already have the pipeline running?"
    Skip to [Step 3: review the manifest](#step-3-review-the-manifest) to check results from a previous run.

### How-to: keep docs aligned with every release (Part 2)

Run the unified autopipeline on release day to synchronize API documentation across five protocols with quality gates and review manifests.

## When to run this flow

Run the autopipeline when any of these conditions apply:

- A new API version ships to production
- A protocol contract file changes (OpenAPI, GraphQL schema, proto, AsyncAPI spec, WebSocket contract)
- The weekly automation schedule triggers (configured in `client_runtime.yml`)
- Documentation gaps exceed the SLA threshold (default: 10 high-priority gaps)

### How-to: keep docs aligned with every release (Part 3)

Run the unified autopipeline on release day to synchronize API documentation across five protocols with quality gates and review manifests.

## Step 1: trigger the autopipeline

Run the unified pipeline from the repository root. This command executes gap detection, drift analysis, contract validation for all five protocols, KPI evaluation, and RAG metadata generation.

```bash
python3 scripts/run_autopipeline.py \
  --docsops-root . \
  --reports-dir reports/acme-demo \
  --runtime-config reports/acme-demo/client_runtime.yml \
  --mode veridoc \
  --since 7
```

<!-- requires: python3, pipeline-scripts -->

**What each flag does:**

| Flag | Value | Purpose |
| --- | --- | --- |
| `--docsops-root` | `.` | Root directory of the docs-ops repository |
| `--reports-dir` | `reports/acme-demo` | Where pipeline writes output artifacts |
| `--runtime-config` | `reports/acme-demo/client_runtime.yml` | Client-specific protocol and module settings |
| `--mode` | `veridoc` | Full pipeline mode with all quality gates |
| `--since` | `7` | Analyze changes from the last 7 days |

The pipeline runs seven stages. Expect 5-10 minutes depending on contract complexity.

**Expected output (summary):**

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

### How-to: keep docs aligned with every release (Part 5)

Run the unified autopipeline on release day to synchronize API documentation across five protocols with quality gates and review manifests.

## Step 3: review the manifest

Open the review manifest to see all generated artifacts and their availability:

```bash
cat reports/acme-demo/REVIEW_MANIFEST.md
```

The manifest lists every artifact, stage status, and provides a reviewer checklist. Key sections:

| Section | What to check |
| --- | --- |
| Pipeline execution summary | Exit code, strictness mode, artifact counts |
| Stage availability | Which stages produced artifacts, which are missing |
| Reviewer checklist | Approval gates before publish |

You can also check the machine-readable manifest:

```bash
python3 -c "
import json
m = json.load(open('reports/acme-demo/review_manifest.json'))
print(f'Available: {m[\"available_artifacts\"]}')
print(f'Missing: {m[\"missing_artifacts\"]}')
print(f'Strictness: {m[\"strictness\"]}')"
```

### How-to: keep docs aligned with every release (Part 6)

Run the unified autopipeline on release day to synchronize API documentation across five protocols with quality gates and review manifests.

## Step 4: verify quality gates

Check that quality metrics meet your thresholds:

| Gate | Command | Expected result |
| --- | --- | --- |
| Quality score | `python3 -c "import json; print(json.load(open('reports/acme-demo/kpi-wall.json'))['quality_score'])"` | 80 or higher |
| Contract validation | Check `multi_protocol_contract_report.json` | Zero failed protocols |
| Stage summary | Check `pipeline_stage_summary.json` | All required stages exist |
| Frontmatter | All docs have valid frontmatter | 100% metadata completeness |

If the quality score is below 80:

1. Check the gap report for high-priority items:

    ```bash
    python3 -c "
    import json
    r = json.load(open('reports/acme-demo/doc_gaps_report.json'))
    high = [g for g in r.get('gaps', []) if g.get('priority') == 'high']
    print(f'{len(high)} high-priority gaps')
    for g in high[:5]:
        print(f'  - {g[\"title\"]}')"
    ```

1. Address each high-priority gap by creating or updating the relevant document.

1. Re-run the pipeline and verify the score improves.

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

### Tutorial: launch your first VeriOps API integration

Build a working VeriOps API integration in 15 minutes with authenticated requests, project creation, and real-time WebSocket subscriptions.

## Tutorial: launch your first VeriOps API integration

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-7c3aed?style=flat-square)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-7c3aed?style=flat-square)

</div>

This tutorial walks you through creating your first VeriOps API project, sending authenticated requests across three protocols (REST, GraphQL, and WebSocket), and verifying the integration works. You complete all five steps in under 15 minutes.

## What you will build

By the end of this tutorial, you will have:

- A working REST API client that creates and retrieves projects
- A GraphQL query that fetches project data with custom field selection
- A WebSocket subscription that receives real-time project update events
- A test script that verifies all three protocols work together

**Time to first success:** 5 minutes for REST, 15 minutes for the complete multi-protocol integration.

### Tutorial: launch your first VeriOps API integration (Part 2)

Build a working VeriOps API integration in 15 minutes with authenticated requests, project creation, and real-time WebSocket subscriptions.

## Before you start

You need:

- An VeriOps API key from the [developer dashboard](https://app.veriops.example/settings/api)
- `curl` version 7.68 or later (run `curl --version` to verify)
- Node.js version 18 or later for the WebSocket client (run `node --version` to verify)
- A terminal with internet access
- About 15 minutes

!!! tip "Save time"
    Export your API key as an environment variable to avoid repeating it in every command:
    `export VERIOPS_API_KEY="YOUR_API_KEY"`

### Tutorial: launch your first VeriOps API integration (Part 3)

Build a working VeriOps API integration in 15 minutes with authenticated requests, project creation, and real-time WebSocket subscriptions.

## Step 1: verify your API key (2 minutes)

Run this command to confirm your API key authenticates against the VeriOps REST API:

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.veriops.example/v1/projects
```

<!-- requires: api-key -->

A `200` response confirms your key works. A `401` response means the key is invalid or expired. Generate a new key in the [dashboard](https://app.veriops.example/settings/api) if you receive `401`.

Next, verify the GraphQL endpoint:

```bash
curl -s -X POST https://api.veriops.example/graphql \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ health { status version } }"}' \
  | python3 -m json.tool
```

<!-- requires: api-key -->

**Expected response:**

```json
{
    "data": {
        "health": {
            "status": "ok",
            "version": "1.0.0"
        }
    }
}
```

### Tutorial: launch your first VeriOps API integration (Part 4)

Build a working VeriOps API integration in 15 minutes with authenticated requests, project creation, and real-time WebSocket subscriptions.

## Step 2: create a project via REST (3 minutes)

Create your first project resource using the REST API:

```bash
curl -X POST https://api.veriops.example/v1/projects \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tutorial Integration Project",
    "description": "Created during the VeriOps API tutorial",
    "status": "active"
  }'
```

<!-- requires: api-key -->

**Expected response (HTTP 201):**

```json
{
  "id": "prj_abc123",
  "name": "Tutorial Integration Project",
  "description": "Created during the VeriOps API tutorial",
  "status": "active",
  "created_at": "2026-03-19T10:00:00Z",
  "updated_at": "2026-03-19T10:00:00Z",
  "task_count": 0,
  "owner_id": "usr_789"
}
```

Save the `id` value (for example, `prj_abc123`). You need it for steps 3 and 4.

### Tutorial: launch your first VeriOps API integration (Part 5)

Build a working VeriOps API integration in 15 minutes with authenticated requests, project creation, and real-time WebSocket subscriptions.

## Step 3: query the project via GraphQL (3 minutes)

Use GraphQL to fetch the project you created with custom field selection. GraphQL returns only the fields you request, which reduces payload size.

```bash
curl -s -X POST https://api.veriops.example/graphql \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query GetProject($id: ID!) { project(id: $id) { id name status createdAt } }",
    "variables": {"id": "prj_abc123"}
  }' \
  | python3 -m json.tool
```

<!-- requires: api-key -->

**Expected response:**

```json
{
    "data": {
        "project": {
            "id": "prj_abc123",
            "name": "Tutorial Integration Project",
            "status": "active",
            "createdAt": "2026-03-19T10:00:00Z"
        }
    }
}
```

Notice that the response contains only the four fields you requested (`id`, `name`, `status`, `createdAt`), not the full project object. This is a key advantage of GraphQL over REST for bandwidth-sensitive clients.

### Tutorial: launch your first VeriOps API integration (Part 6)

Build a working VeriOps API integration in 15 minutes with authenticated requests, project creation, and real-time WebSocket subscriptions.

## Step 4: subscribe to real-time updates via WebSocket (5 minutes)

Open a WebSocket connection to receive live project change events. Create this Node.js script:

```javascript
// tutorial-websocket.js
// Connect to VeriOps WebSocket API and subscribe to project updates
// Requires: Node.js 18+ (built-in WebSocket support)
const ws = new WebSocket(
  'wss://api.veriops.example/realtime?token=YOUR_API_KEY'
);

ws.addEventListener('open', () => {
  console.log('Connected to VeriOps WebSocket API');

// Subscribe to updates for the project you created in Step 2
  ws.send(JSON.stringify({
    type: 'subscribe',
    request_id: 'tutorial-001',
    sent_at: new Date().toISOString(),
    payload: {
      channel: 'project.updated',
      filters: { project_id: 'prj_abc123' }
    }
  }));
});

ws.addEventListener('message', (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === 'ack') {
    console.log('Subscription confirmed:', msg.request_id);
  } else if (msg.type === 'event') {
    console.log('Project update received:');
    console.log('  Status:', msg.payload.data.status);
    console.log('  Updated by:', msg.payload.data.updated_by);
  } else if (msg.type === 'ping') {
    ws.send(JSON.stringify({ type: 'pong', request_id: msg.request_id }));
  }
});

ws.addEventListener('close', (event) => {
  console.log('Disconnected:', event.code, event.reason);
});

### Tutorial: launch your first VeriOps API integration (Part 7)

Build a working VeriOps API integration in 15 minutes with authenticated requests, project creation, and real-time WebSocket subscriptions.

// Keep the script running for 60 seconds to receive events
setTimeout(() => {
  ws.close(1000, 'Tutorial complete');
  console.log('Tutorial WebSocket client closed');
}, 60000);
```

<!-- requires: api-key -->

Run the script:

```bash
node tutorial-websocket.js
```

While the script runs, update the project status from another terminal to trigger an event:

```bash
curl -X PUT https://api.veriops.example/v1/projects/prj_abc123 \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"status": "archived"}'
```

<!-- requires: api-key -->

The WebSocket client prints the update event within 1-2 seconds.

### Tutorial: launch your first VeriOps API integration (Part 8)

Build a working VeriOps API integration in 15 minutes with authenticated requests, project creation, and real-time WebSocket subscriptions.

## Step 5: verify the integration (2 minutes)

Run this checklist to confirm all three protocols work:

| Protocol | Test command | Expected result |
| --- | --- | --- |
| REST | `GET /v1/projects` | HTTP 200 with project list |
| GraphQL | `query { health { status } }` | `{"data": {"health": {"status": "ok"}}}` |
| WebSocket | Connect to `wss://api.veriops.example/realtime` | Connection opens, subscription confirmed |

If any step fails:

- **HTTP 401 on REST or GraphQL**: Your API key is invalid. Generate a new one in the [dashboard](https://app.veriops.example/settings/api).
- **WebSocket connection error**: Verify you use `wss://` (not `ws://`) and the key is passed as `?token=` query parameter.
- **Timeout on any request**: Check your network allows outbound connections on port 443.

## What you accomplished

| Step | Protocol | Outcome |
| --- | --- | --- |
| Verify API key | REST + GraphQL | Confirmed authentication across two protocols |
| Create project | REST | Created a project resource via `POST /v1/projects` |
| Query project | GraphQL | Fetched project with custom field selection |
| Subscribe to events | WebSocket | Received real-time project update events |
| Verify integration | All three | Confirmed multi-protocol integration works end-to-end |

### Tutorial: launch your first VeriOps API integration (Part 9)

Build a working VeriOps API integration in 15 minutes with authenticated requests, project creation, and real-time WebSocket subscriptions.

## Next steps (2)

- [REST API reference](../reference/rest-api.md) for all 14 endpoints across five resources
- [GraphQL playground](../reference/graphql-playground.md) to explore the full schema interactively
- [gRPC gateway invoke](../reference/grpc-gateway.md) for high-performance RPC calls
- [How-to: keep docs aligned with every release](how-to.md) for the operator workflow
- [Troubleshooting: common pipeline issues](troubleshooting.md) if you encounter errors

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

## Next steps (3)

- Validate modules: `npm run lint:knowledge`
- Rebuild retrieval index: `npm run build:knowledge-index`
- Generate assistant pack: `npm run build:intent -- --channel assistant`

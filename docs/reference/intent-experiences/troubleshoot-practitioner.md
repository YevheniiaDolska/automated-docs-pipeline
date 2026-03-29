---
title: 'Intent experience: troubleshoot for practitioner'
description: Assembled guidance for one intent and audience using reusable knowledge
  modules with verified metadata and channel-ready sections.
content_type: reference
product: both
tags:
- Reference
- AI
last_reviewed: '2026-03-26'
original_author: Kroha
---


<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

# Intent experience: troubleshoot for practitioner

This page is assembled for the `troubleshoot` intent and the `practitioner` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent troubleshoot --audience practitioner --channel docs
```

## Included modules

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

## Next steps for API integration

- [REST API reference](../reference/rest-api.md) for all 14 endpoints across five resources
- [GraphQL playground](../reference/graphql-playground.md) to explore the full schema interactively
- [gRPC gateway invoke](../reference/grpc-gateway.md) for high-performance RPC calls
- [How-to: keep docs aligned with every release](how-to.md) for the operator workflow
- [Troubleshooting: common pipeline issues](troubleshooting.md) if you encounter errors

## Knowledge module pipeline steps

- Validate modules: `npm run lint:knowledge`
- Rebuild retrieval index: `npm run build:knowledge-index`
- Generate assistant pack: `npm run build:intent -- --channel assistant`

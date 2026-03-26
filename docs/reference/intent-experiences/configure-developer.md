---
title: "Intent experience: configure for developer"
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

# Intent experience: configure for developer

This page is assembled for the `configure` intent and the `developer` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent configure --audience developer --channel docs
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

### Quality evidence and gate results (Part 6)

Complete quality evidence from the VeriDoc pipeline for VeriOps docs, covering KPI metrics, protocol gates, 24 automated checks, and RAG readiness.

### Style checks (automated)

<!-- vale AmericanEnglish.Spelling = NO -->
<!-- vale proselint.Spelling = NO -->

| Rule | Enforced by | Description |
| --- | --- | --- |
| American English | Vale + AmericanEnglish | Use "color" instead of British "colour" and "optimize" instead of "optimise" |

<!-- vale AmericanEnglish.Spelling = YES -->
<!-- vale proselint.Spelling = YES -->
| Active voice | Vale + write-good | "Configure the webhook" not "The webhook should be configured" |
| No weasel words | Vale + write-good | No "simple," "easy," "just," "many," "various" |
| No contractions | Vale + Google style | "do not" not "don't," "cannot" not "can't" |
| Second person | Vale + Google style | "you" not "the user" or "one" |
| Present tense | Vale + Google style | "sends" not "will send" for current features |

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

### How-to: keep docs aligned with every release

Run the unified autopipeline on release day to synchronize API documentation across five protocols with quality gates and review manifests.

# How-to: keep docs aligned with every release

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

## Next steps

- Validate modules: `npm run lint:knowledge`
- Rebuild retrieval index: `npm run build:knowledge-index`
- Generate assistant pack: `npm run build:intent -- --channel assistant`

---
title: "Intent experience: troubleshoot for support"
description: "Assembled guidance for one intent and audience using reusable knowledge modules with verified metadata and channel-ready sections."
content_type: reference
product: both
tags:
  - Reference
  - AI
---

# Intent experience: troubleshoot for support

This page is assembled for the `troubleshoot` intent and the `support` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent troubleshoot --audience support --channel docs
```

## Included modules

### Troubleshooting: common VeriOps pipeline issues

Fix common VeriOps documentation pipeline issues in under 5 minutes, covering contract failures, quality gates, build errors, and WebSocket problems.

## Troubleshooting: common VeriOps pipeline issues

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

## Next steps (2)

- Validate modules: `npm run lint:knowledge`
- Rebuild retrieval index: `npm run build:knowledge-index`
- Generate assistant pack: `npm run build:intent -- --channel assistant`

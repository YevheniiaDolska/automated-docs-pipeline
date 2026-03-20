---
title: "How-to: keep docs aligned with every release"
description: "Run the unified autopipeline on release day to synchronize API documentation across five protocols with quality gates and review manifests."
content_type: how-to
product: both
tags:
  - How-To
last_reviewed: "2026-03-19"
---

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

## When to run this flow

Run the autopipeline when any of these conditions apply:

- A new API version ships to production
- A protocol contract file changes (OpenAPI, GraphQL schema, proto, AsyncAPI spec, WebSocket contract)
- The weekly automation schedule triggers (configured in `client_runtime.yml`)
- Documentation gaps exceed the SLA threshold (default: 10 high-priority gaps)

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

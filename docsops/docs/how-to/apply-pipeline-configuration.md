---
title: Apply a pilot, full, or RAG configuration
description: Update a client profile for pilot, full, or RAG-enabled operation and
  align it with cloud, strict-local, or hybrid LLM execution.
content_type: how-to
product: both
tags:
- How-To
- Cloud
- Self-hosted
- AI
last_reviewed: '2026-06-16'
original_author: Kroha
---

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veri-doc.app/)
<!-- VERIDOC_POWERED_BADGE:END -->


# Apply a pilot, full, or RAG configuration

This guide shows you how to take an existing client profile and switch it to `pilot`, `full`, or `full+RAG` while keeping LLM execution aligned with `cloud`, `strict-local`, or `hybrid` policy.

```yaml
runtime:
  llm_control:
    llm_mode: "external_preferred"
    external_llm_allowed: true
    require_explicit_approval: false
```

Use this guide when the client already has a `.client.yml` file and you need to change rollout depth or LLM behavior without rebuilding the profile from scratch.

## Prerequisites

Before you start, ensure you have:

- A client profile under `profiles/clients/`
- The target rollout decision: `pilot`, `full`, or `full+RAG`
- The target execution mode: `cloud`, `strict-local`, or `hybrid`
- Permission to rebuild or reprovision the bundle

## Step 1: Start from the nearest preset

Use the preset that is closest to the target state.

| Target state | Recommended preset |
| --- | --- |
| `pilot` | `profiles/clients/presets/pilot-evidence.yml` |
| `full` | `profiles/clients/presets/small.yml` or `startup.yml` |
| `full+RAG` | `profiles/clients/presets/startup.yml` or `enterprise.yml` |

If the profile already exists, compare it to the preset before changing fields by hand.

## Step 2: Set the scope tier

### Pilot

Use `pilot` when you need a narrow proof bundle.

```yaml
licensing:
  plan: "pilot"
runtime:
  modules:
    gap_detection: true
    drift_detection: true
    docs_contract: true
    kpi_sla: true
    rag_optimization: false
    ontology_graph: false
    retrieval_evals: false
```

### Full

Use `full` when you want full docs operations without forcing retrieval features.

```yaml
licensing:
  plan: "professional"
runtime:
  modules:
    gap_detection: true
    drift_detection: true
    docs_contract: true
    kpi_sla: true
    normalization: true
    snippet_lint: true
    self_checks: true
    fact_checks: true
    rag_optimization: false
    ontology_graph: false
    retrieval_evals: false
```

### Full+RAG

Use `full+RAG` when retrieval quality is part of the contract.

```yaml
licensing:
  plan: "enterprise"
runtime:
  modules:
    gap_detection: true
    drift_detection: true
    docs_contract: true
    kpi_sla: true
    rag_optimization: true
    ontology_graph: true
    retrieval_evals: true
```

## Step 3: Set the execution mode

### Cloud

```yaml
runtime:
  llm_control:
    llm_mode: "external_preferred"
    external_llm_allowed: true
    require_explicit_approval: false
    redact_before_external: true
```

### Strict-local

```yaml
runtime:
  llm_control:
    llm_mode: "local_default"
    external_llm_allowed: false
    require_explicit_approval: true
    redact_before_external: true
```

### Hybrid

```yaml
runtime:
  llm_control:
    llm_mode: "local_default"
    external_llm_allowed: true
    require_explicit_approval: true
    redact_before_external: true
```

Use `require_explicit_approval: false` in `hybrid` only if the client allows automatic external fallback.

## Step 4: Align flow-specific settings

If the client uses `api-first` or `hybrid` docs flow, confirm the API-first block is still coherent.

```yaml
runtime:
  docs_flow:
    mode: "hybrid"
  api_first:
    enabled: true
    generate_from_notes: true
    sandbox_backend: "prism"
    generate_test_assets: true
```

If the client uses retrieval features, keep the knowledge outputs enabled and versioned:

```yaml
runtime:
  retrieval_eval:
    enabled: true
    index_path: "docs/assets/knowledge-retrieval-index.json"
  knowledge_graph:
    enabled: true
    output_path: "docs/assets/knowledge-graph.jsonld"
```

## Step 5: Rebuild the bundle

After editing the profile, rebuild the bundle:

```bash
python3 scripts/build_client_bundle.py --client profiles/clients/acme.client.yml
```

If you are installing directly into a repo, reprovision it:

```bash
python3 scripts/provision_client_repo.py \
  --client profiles/clients/acme.client.yml \
  --client-repo /path/to/client-repo \
  --install-scheduler linux
```

## Step 6: Verify the included docs

Every generated bundle should now include the configuration docs that match its profile. Check for:

- `docs/getting-started/choose-pipeline-configuration.md`
- `docs/how-to/apply-pipeline-configuration.md`
- `docs/concepts/pipeline-configuration-combinations.md`
- `docs/reference/pipeline-configuration-reference.md`

Bundles may also include additional documents such as API-first or Ask AI instructions when those features are enabled.

## Common issues and fixes

### Issue: Full bundle still looks like pilot

Check `licensing.plan` and the three retrieval flags. If `plan` is still `pilot`, or all three retrieval flags are `false`, the profile is still scoped down.

### Issue: Strict-local bundle still attempts external LLM use

Check `runtime.llm_control.external_llm_allowed`. It must be `false`. Also verify the generated bundle copies the expected `config/client_runtime.yml`.

### Issue: Full+RAG bundle does not ship retrieval guidance

Rebuild the bundle after changing the profile. The bundle builder selects configuration docs from the final runtime config, not from stale outputs.

## Validation checklist

- [ ] `licensing.plan` matches the intended scope tier
- [ ] Retrieval flags match the intended scope tier
- [ ] `llm_control` matches the intended execution mode
- [ ] Bundle rebuild completed after the profile edit
- [ ] The bundle includes the configuration documents under `docs/`

## Next steps

- [Documentation index](index.md)

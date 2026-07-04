---
title: How pipeline configurations compose
description: Learn how the pipeline combines rollout scope and LLM execution mode
  so bundles stay aligned with proof, full, and RAG-enabled delivery.
content_type: concept
product: both
tags:
- Concept
- Cloud
- Self-hosted
- AI
last_reviewed: '2026-06-16'
original_author: Kroha
---

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veri-doc.app/)
<!-- VERIDOC_POWERED_BADGE:END -->


# How pipeline configurations compose

Pipeline configuration is a two-axis model. One axis defines rollout scope, and the other defines how LLM work is executed and governed.

```yaml
runtime:
  modules:
    rag_optimization: true
    ontology_graph: true
    retrieval_evals: true
  llm_control:
    llm_mode: "local_default"
    external_llm_allowed: true
```

<!-- glossary:add: strict-local mode | LLM execution mode that keeps llm_mode local_default and blocks external LLM egress by setting external_llm_allowed to false. | local-only mode -->

This model matters because a `pilot` bundle in `strict-local mode` should carry different scripts, governance, and user instructions than a `full+RAG` bundle in `cloud` mode.

## The two axes

The pipeline combines these dimensions:

| Axis | What it controls | Primary fields |
| --- | --- | --- |
| Rollout scope | Which modules, checks, and weekly tasks are active | `licensing.plan`, `runtime.modules`, `runtime.docs_flow` |
| Execution mode | Where LLM work runs and what egress policy applies | `runtime.llm_control.*` |

The builder does not infer one axis from the other. A bundle can be `pilot + cloud`, `full + strict-local`, or `full+RAG + hybrid`.

## Rollout scope is about delivery depth

Rollout scope answers: how much of the platform should this client receive now?

### Pilot

`pilot` narrows the surface to proof-oriented signals:

- weekly gap and drift evidence
- docs quality gates
- API-first generation if enabled
- reduced bundle script surface

Pilot intentionally keeps retrieval features off by default because the goal is short proof cycles, not full knowledge-system rollout.

### Full

`full` turns on the standard docs operations surface:

- governance and normalization
- docs-contract visibility
- KPI and SLA reporting
- lifecycle and release pack flows

Full can still be RAG-free. That is a valid state when the client wants governed documentation operations without retrieval evaluation or graph outputs.

### Full+RAG

`full+RAG` adds the retrieval layer to full docs operations:

- knowledge module extraction and validation
- retrieval index generation
- knowledge graph output
- retrieval quality evaluation

This mode is appropriate when the client expects AI-facing documentation quality to be measured, not only generated.

## Execution mode is about LLM governance

Execution mode answers: where may synthesis run, and what fallback is allowed?

### Cloud

Cloud mode prefers external models:

```yaml
runtime:
  llm_control:
    llm_mode: "external_preferred"
    external_llm_allowed: true
    require_explicit_approval: false
```

Use this mode when external-model quality and latency matter more than local-only execution controls.

### Strict-local

Strict-local mode keeps execution local and blocks external egress:

```yaml
runtime:
  llm_control:
    llm_mode: "local_default"
    external_llm_allowed: false
    require_explicit_approval: true
```

Use this mode when policy requires local inference or forbids external LLM traffic.

### Hybrid

Hybrid mode keeps local-first behavior but permits controlled fallback:

```yaml
runtime:
  llm_control:
    llm_mode: "local_default"
    external_llm_allowed: true
    require_explicit_approval: true
```

Use this mode when the team wants local defaults but still needs a path for harder synthesis tasks.

## Why full and full+RAG are not the same

A frequent mistake is assuming `full` automatically implies retrieval features. It does not.

The difference is the retrieval triplet:

- `rag_optimization`
- `ontology_graph`
- `retrieval_evals`

When all three are `true`, the configuration behaves as `full+RAG`. When they are all `false`, the bundle is still full-scope docs operations, but not a retrieval-governed rollout.

## Why bundles need configuration-specific docs

The same scripts are not enough across every configuration. Users need configuration-specific instructions because:

- `pilot` users need proof-oriented operating steps
- `full` users need broader automation and governance guidance
- `full+RAG` users need retrieval quality and knowledge-system guidance
- `strict-local` users need egress and local runtime instructions
- `cloud` users need external-model behavior spelled out

That is why the bundle builder now selects documentation from the final runtime config, not only from manual `include_docs` entries.

## Configuration patterns that work well

| Pattern | When it works best |
| --- | --- |
| `pilot + strict-local` | Early proof with tight security review |
| `pilot + cloud` | Fastest demo path for a time-boxed proof |
| `full + hybrid` | Standard production rollout with local-first governance |
| `full+RAG + hybrid` | AI-facing docs program with controlled external fallback |
| `full+RAG + cloud` | Maximum throughput and retrieval quality work on hosted models |

## Next steps

- Use [Choose a pipeline configuration](../getting-started/choose-pipeline-configuration.md) to select the starting combination.
- Follow [Apply a pilot, full, or RAG configuration](../how-to/apply-pipeline-configuration.md) to edit a profile.
- Check [Pipeline configuration reference](../reference/pipeline-configuration-reference.md) for exact field values.

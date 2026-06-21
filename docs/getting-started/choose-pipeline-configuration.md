---
title: Choose a pipeline configuration
description: Pick a pilot, full, or RAG-enabled bundle and pair it with cloud, strict-local,
  or hybrid execution in one guided setup.
content_type: tutorial
product: both
tags:
- Tutorial
- Cloud
- Self-hosted
- AI
last_reviewed: '2026-06-16'
original_author: Kroha
---


# Choose a pipeline configuration

The pipeline combines one scope tier with one execution mode. Start with that pair, then build or provision the matching bundle from a single client profile.

```yaml
licensing:
  plan: "pilot"
runtime:
  modules:
    rag_optimization: false
    ontology_graph: false
    retrieval_evals: false
  llm_control:
    llm_mode: "local_default"
    external_llm_allowed: false
```

Use this tutorial when you need to decide between `pilot`, `full`, and `full+RAG`, then choose whether LLM execution should be `cloud`, `strict-local`, or `hybrid`.

## Step 1: Pick the scope tier

Choose the tier that matches the rollout depth you want in the client repository.

| Scope tier | Use this when | Starting point | Key module pattern |
| --- | --- | --- | --- |
| `pilot` | You need proof in one week with a reduced script surface | `profiles/clients/presets/pilot-evidence.yml` | Core quality modules on, RAG modules off |
| `full` | You want full docs operations without retrieval evaluation features | `profiles/clients/presets/small.yml` or a custom profile | Governance and weekly automation on, RAG modules optional |
| `full+RAG` | You want retrieval index, graph, and eval gates in the same bundle | `profiles/clients/presets/startup.yml` or `enterprise.yml` | `rag_optimization`, `ontology_graph`, and `retrieval_evals` on |

For `pilot`, use the preset as-is unless you have a narrow reason to expand scope.

For `full`, keep the standard automation modules on:

- `gap_detection`
- `drift_detection`
- `docs_contract`
- `kpi_sla`
- `normalization`
- `snippet_lint`
- `self_checks`
- `fact_checks`

For `full+RAG`, keep these three modules enabled together:

- `rag_optimization`
- `ontology_graph`
- `retrieval_evals`

## Step 2: Pick the execution mode

Execution mode controls how the bundle handles LLM work.

| Execution mode | Use this when | `llm_control` pattern |
| --- | --- | --- |
| `cloud` | You want the fastest external-model path | `llm_mode: external_preferred`, `external_llm_allowed: true` |
| `strict-local` | You cannot allow external LLM egress | `llm_mode: local_default`, `external_llm_allowed: false` |
| `hybrid` | You want local-first execution with external fallback | `llm_mode: local_default`, `external_llm_allowed: true` |

Recommended starting values:

```yaml
runtime:
  llm_control:
    llm_mode: "local_default"
    external_llm_allowed: true
    require_explicit_approval: true
    redact_before_external: true
```

Use `cloud` when response quality and speed matter more than local-only controls. Use `strict-local` when policy blocks external LLM traffic. Use `hybrid` when you want local-first behavior but still need fallback for harder synthesis tasks.

## Step 3: Generate or edit the client profile

The interactive path is the fastest way to create the profile:

```bash
python3 scripts/provision_client_repo.py --interactive --generate-profile
```

When the wizard asks for a preset, map your selection as follows:

- `pilot` -> `pilot-evidence`
- `full` -> `small`, `startup`, or `enterprise`
- `full+RAG` -> `startup` or `enterprise`

Then set the LLM section to match your execution mode.

If you prefer editing YAML directly, copy a preset and adjust it:

```bash
cp profiles/clients/presets/startup.yml profiles/clients/acme.client.yml
python3 scripts/build_client_bundle.py --client profiles/clients/acme.client.yml
```

## Step 4: Verify the resulting configuration

Before you install the bundle, verify these fields in the final profile:

- `licensing.plan`
- `runtime.docs_flow.mode`
- `runtime.modules.rag_optimization`
- `runtime.modules.ontology_graph`
- `runtime.modules.retrieval_evals`
- `runtime.llm_control.llm_mode`
- `runtime.llm_control.external_llm_allowed`

For a `full+RAG` bundle, the three RAG module flags must all be `true`. For a `strict-local` bundle, `external_llm_allowed` must be `false`.

## Step 5: Build or provision the bundle

Build a distributable bundle:

```bash
python3 scripts/build_client_bundle.py --client profiles/clients/acme.client.yml
```

Provision directly into a client repository:

```bash
python3 scripts/provision_client_repo.py \
  --client profiles/clients/acme.client.yml \
  --client-repo /path/to/client-repo \
  --install-scheduler linux
```

## Validation checklist

- [ ] Scope tier matches the client rollout: `pilot`, `full`, or `full+RAG`
- [ ] Execution mode matches policy: `cloud`, `strict-local`, or `hybrid`
- [ ] `full+RAG` bundles keep all three retrieval modules enabled
- [ ] `strict-local` bundles keep `external_llm_allowed: false`
- [ ] The built bundle includes configuration docs under `docs/`

## Next steps

- Read [How pipeline configurations compose](../concepts/pipeline-configuration-combinations.md) for the model behind the matrix.
- Follow [Apply a pilot, full, or RAG configuration](../how-to/apply-pipeline-configuration.md) to edit an existing profile safely.
- Use [Pipeline configuration reference](../reference/pipeline-configuration-reference.md) for exact field values.

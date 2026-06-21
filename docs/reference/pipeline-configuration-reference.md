---
title: Pipeline configuration reference
description: Exact preset, module, and llm_control values for pilot, full, full+RAG,
  cloud, strict-local, and hybrid pipeline configurations.
content_type: reference
product: both
tags:
- Reference
- Cloud
- Self-hosted
- AI
last_reviewed: '2026-06-16'
original_author: Kroha
---


# Pipeline configuration reference

This page defines the exact fields that distinguish `pilot`, `full`, and `full+RAG`, plus the `cloud`, `strict-local`, and `hybrid` execution modes.

```yaml
runtime:
  llm_control:
    llm_mode: "external_preferred"
    external_llm_allowed: true
    require_explicit_approval: false
```

Use this page when you need exact values, not rollout guidance.

## Scope tier reference

| Scope tier | Preset or base profile | `licensing.plan` | Retrieval triplet |
| --- | --- | --- | --- |
| `pilot` | `profiles/clients/presets/pilot-evidence.yml` | `pilot` | all `false` |
| `full` | `profiles/clients/presets/small.yml` or custom | `professional` or `enterprise` | optional |
| `full+RAG` | `profiles/clients/presets/startup.yml` or `enterprise.yml` | `professional` or `enterprise` | all `true` |

### Retrieval triplet

The retrieval triplet is:

- `runtime.modules.rag_optimization`
- `runtime.modules.ontology_graph`
- `runtime.modules.retrieval_evals`

Interpretation rules:

- all `false` -> not RAG-enabled
- all `true` -> `full+RAG`
- mixed values -> transitional or custom rollout; document it explicitly

## Execution mode reference

| Execution mode | `llm_mode` | `external_llm_allowed` | `require_explicit_approval` | Typical use |
| --- | --- | --- | --- | --- |
| `cloud` | `external_preferred` | `true` | `false` | hosted model path |
| `strict-local` | `local_default` | `false` | `true` | no external egress |
| `hybrid` | `local_default` | `true` | `true` or `false` | local-first with fallback |

## Preset mapping

| Preset | User-facing meaning | Notes |
| --- | --- | --- |
| `pilot-evidence` | `pilot` | intentionally reduced script surface |
| `small` | `full` | full baseline without the larger startup defaults |
| `startup` | `full+RAG` default | balanced full-scope preset with retrieval features on |
| `enterprise` | `full+RAG` strict | largest default surface with Ask AI runtime support |

## Minimum module sets

### Pilot minimum

```yaml
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

### Full minimum

```yaml
runtime:
  modules:
    gap_detection: true
    drift_detection: true
    docs_contract: true
    kpi_sla: true
    terminology_management: true
    normalization: true
    snippet_lint: true
    self_checks: true
    fact_checks: true
    lifecycle_management: true
    knowledge_validation: true
```

### Full+RAG minimum

```yaml
runtime:
  modules:
    gap_detection: true
    drift_detection: true
    docs_contract: true
    kpi_sla: true
    terminology_management: true
    normalization: true
    snippet_lint: true
    self_checks: true
    fact_checks: true
    lifecycle_management: true
    knowledge_validation: true
    rag_optimization: true
    ontology_graph: true
    retrieval_evals: true
```

## Flow alignment rules

| Field | Allowed values | Notes |
| --- | --- | --- |
| `runtime.docs_flow.mode` | `code-first`, `api-first`, `hybrid` | `hybrid` is the default for most presets |
| `runtime.api_first.enabled` | `true`, `false` | Keep `true` for planning-notes to contract flow |
| `runtime.api_first.sandbox_backend` | `docker`, `prism`, `external` | `external` requires a reachable mock URL |
| `runtime.output_targets` | list | examples: `mkdocs`, `readme`, `github`, `sphinx` |

## Bundle documentation selection rules

The bundle builder now auto-includes configuration docs from the final runtime config.

Base configuration docs:

- `docs/getting-started/choose-pipeline-configuration.md`
- `docs/how-to/apply-pipeline-configuration.md`
- `docs/concepts/pipeline-configuration-combinations.md`
- `docs/reference/pipeline-configuration-reference.md`

Additional docs are added when relevant:

- `docs/how-to/run-api-first-production-flow.md` for `api-first` or `hybrid`
- `docs/how-to/configure-ask-ai-module.md` and `docs/how-to/install-ask-ai-runtime-pack.md` when Ask AI is enabled
- `docs/concepts/intelligent-knowledge-system.md` when retrieval features are enabled
- `docs/reference/network-transparency.md` when local-first or egress-sensitive execution is in use

## Validation rules

- `pilot` should not ship with the full retrieval triplet enabled unless the rollout is intentionally re-scoped.
- `strict-local` must keep `external_llm_allowed: false`.
- `cloud` should not use `llm_mode: local_default` unless the team intentionally wants local-first behavior.
- `full+RAG` should keep all three retrieval flags enabled together to avoid partial retrieval governance.

## Related files

- `profiles/clients/presets/pilot-evidence.yml`
- `profiles/clients/presets/small.yml`
- `profiles/clients/presets/startup.yml`
- `profiles/clients/presets/enterprise.yml`
- `scripts/build_client_bundle.py`
- `scripts/provision_client_repo.py`

## Next steps

- [Documentation index](index.md)

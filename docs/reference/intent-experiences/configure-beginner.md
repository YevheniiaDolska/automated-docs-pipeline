---
title: "Intent experience: configure for beginner"
description: "Assembled guidance for one intent and audience using reusable knowledge modules with verified metadata and channel-ready sections."
content_type: reference
product: both
tags:
  - Reference
  - AI
---

<!-- markdownlint-disable MD001 MD007 MD024 MD025 MD031 -->

# Intent experience: configure for beginner

This page is assembled for the `configure` intent and the `beginner` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent configure --audience beginner --channel docs
```

## Included modules

### Choose a pipeline configuration

Pick a pilot, full, or RAG-enabled bundle and pair it with cloud, strict-local, or hybrid execution in one guided setup.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veri-doc.app/)
<!-- VERIDOC_POWERED_BADGE:END -->

### Choose a pipeline configuration: Choose a pipeline configuration

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

### Choose a pipeline configuration (Part 2)

Pick a pilot, full, or RAG-enabled bundle and pair it with cloud, strict-local, or hybrid execution in one guided setup.

#### Choose a pipeline configuration (Part 2): Step 1: Pick the scope tier

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

### Choose a pipeline configuration (Part 3)

Pick a pilot, full, or RAG-enabled bundle and pair it with cloud, strict-local, or hybrid execution in one guided setup.

#### Choose a pipeline configuration (Part 3): Step 2: Pick the execution mode

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

### Choose a pipeline configuration (Part 4)

Pick a pilot, full, or RAG-enabled bundle and pair it with cloud, strict-local, or hybrid execution in one guided setup.

#### Choose a pipeline configuration (Part 4): Step 3: Generate or edit the client profile

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

#### Choose a pipeline configuration (Part 4): Step 4: Verify the resulting configuration

Before you install the bundle, verify these fields in the final profile:

- `licensing.plan`
- `runtime.docs_flow.mode`
- `runtime.modules.rag_optimization`
- `runtime.modules.ontology_graph`
- `runtime.modules.retrieval_evals`
- `runtime.llm_control.llm_mode`
- `runtime.llm_control.external_llm_allowed`

For a `full+RAG` bundle, the three RAG module flags must all be `true`. For a `strict-local` bundle, `external_llm_allowed` must be `false`.

### Choose a pipeline configuration (Part 5)

Pick a pilot, full, or RAG-enabled bundle and pair it with cloud, strict-local, or hybrid execution in one guided setup.

#### Choose a pipeline configuration (Part 5): Step 5: Build or provision the bundle

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

#### Choose a pipeline configuration (Part 5): Validation checklist

- [ ] Scope tier matches the client rollout: `pilot`, `full`, or `full+RAG`
- [ ] Execution mode matches policy: `cloud`, `strict-local`, or `hybrid`
- [ ] `full+RAG` bundles keep all three retrieval modules enabled
- [ ] `strict-local` bundles keep `external_llm_allowed: false`
- [ ] The built bundle includes configuration docs under `docs/`

#### Choose a pipeline configuration (Part 5): Next steps

- Read [How pipeline configurations compose](../concepts/pipeline-configuration-combinations.md) for the model behind the matrix.
- Follow [Apply a pilot, full, or RAG configuration](../how-to/apply-pipeline-configuration.md) to edit an existing profile safely.
- Use [Pipeline configuration reference](../reference/pipeline-configuration-reference.md) for exact field values.

### Build your first workflow in 5 minutes

Create a webhook-triggered workflow that receives HTTP requests and sends Slack notifications. No coding required.

<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veri-doc.app/)
<!-- VERIDOC_POWERED_BADGE:END -->

#### Build your first workflow in 5 minutes: Build your first workflow in 5 minutes

A workflow is a series of connected nodes that process data automatically. In this tutorial you create a workflow that receives an HTTP request via a Webhook node and sends a notification to Slack.

#### Build your first workflow in 5 minutes: Prerequisites

- An instance (Cloud or self-hosted). See the [getting started overview](index.md).
- A Slack workspace where you can add apps.

#### Build your first workflow in 5 minutes: Step 1: Create a new workflow

=== "Cloud"

- Log in to your Cloud instance.
- Select **New Workflow** from the top-right menu.
- The canvas opens with an empty workflow.

=== "Self-hosted"

- Open your instance at `http://localhost:5678`.
- Select **New Workflow**.
- The canvas opens with an empty workflow.

#### Build your first workflow in 5 minutes: Step 2: Add a Webhook trigger node

1. Select the **+** button on the canvas.
1. Search for **Webhook** and select it.
1. Set **HTTP Method** to `POST`.
1. Copy the **Test URL**—you will need it in Step 5.

!!! info "Test URL vs Production URL"
 The Test URL is active only while the workflow editor is open. The Production URL activates after you toggle the workflow to **Active**.

### Build your first workflow in 5 minutes (Part 2)

Create a webhook-triggered workflow that receives HTTP requests and sends Slack notifications. No coding required.

#### Build your first workflow in 5 minutes (Part 2): Step 3: Add a Slack node

1. Select the **+** button after the Webhook node.
1. Search for **Slack** and select it.
1. Set **Operation** to **Send a Message**.
1. Select your Slack credential or create one (requires a Slack Bot Token with `chat:write` scope).
1. Set **Channel** to your target channel name or ID.
1. Set **Text** to an expression:

```text

New webhook received: {% raw %}{{ $json.body.message }}{% endraw %}

```

#### Build your first workflow in 5 minutes (Part 2): Step 4: Test the workflow

1. Select **Test Workflow** in the top bar.
1. In a terminal, send a test request:

```bash

curl -X POST YOUR_TEST_URL \
 -H "Content-Type: application/json" \
 -d '{"message": "Hello from my first workflow!"}'

```

1. Check your Slack channel—the message appears within 2 seconds.

#### Build your first workflow in 5 minutes (Part 2): Step 5: Activate the workflow

1. Toggle the workflow to **Active** in the top-right corner.
1. Replace the Test URL with the **Production URL** in your application.

The workflow now runs automatically for every incoming request, without the editor open.

#### Build your first workflow in 5 minutes (Part 2): Next steps

- [Configure Webhook authentication](../how-to/configure-webhook-trigger.md) to secure your endpoint
- [Understand the execution model](../concepts/workflow-execution-model.md) to learn how workflows process data
- [Webhook node reference](../reference/nodes/webhook.md) for all available parameters

## Next steps

- Validate modules: `npm run lint:knowledge`
- Rebuild retrieval index: `npm run build:knowledge-index`
- Generate assistant pack: `npm run build:intent -- --channel assistant`

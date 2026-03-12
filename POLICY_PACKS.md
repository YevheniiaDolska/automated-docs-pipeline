---
title: "Policy packs"
description: "Reference guide for selecting, configuring, and enforcing policy packs across docs contract, drift, KPI/SLA, and terminology governance."
content_type: reference
product: both
last_reviewed: "2026-03-12"
tags:
  - Operations
  - Reference
---

# Policy packs

This guide explains what policy packs are, how they work, and how to choose the right one for each company.

## What is a policy pack?

A policy pack is a YAML configuration file that controls how strict the pipeline checks are. Think of it as a quality profile. Different companies need different levels of strictness.

For example:

- A new team running a pilot needs lenient checks so they can adopt the pipeline gradually.
- An API-heavy product needs strict drift detection so API docs never fall behind.
- A product-led growth company needs the strictest checks on user-facing docs.

## What a policy pack controls

Each policy pack defines top-level sections:

| Section | What it does | Used by |
| --- | --- | --- |
| `docs_contract` | Defines `interface_patterns` and `doc_patterns`. When a PR changes files matching interface patterns but does not change files matching doc patterns, the PR is blocked. | `check_docs_contract.py`, `pr-dod-contract.yml` |
| `drift` | Defines `openapi_patterns`, `sdk_patterns`, and `reference_doc_patterns`. When OpenAPI or SDK files change without a corresponding reference doc update, drift is reported. | `check_api_sdk_drift.py`, `api-sdk-drift-gate.yml` |
| `kpi_sla` | Defines numeric thresholds for quality score, stale percentage, gap count, and quality regression. Breaching any threshold fails the SLA check. | `evaluate_kpi_sla.py`, `kpi-wall.yml`, `weekly-consolidation.yml` |
| `terminology` | Defines glossary governance thresholds (`glossary_sync_required`, max new terms per week) for project terminology growth. | `sync_project_glossary.py`, `run_weekly_gap_batch.py` |
| `retrieval_evals` | Defines retrieval quality thresholds: minimum precision, minimum recall, and maximum hallucination rate. | `run_retrieval_evals.py`, `run_weekly_gap_batch.py` |
| `knowledge_graph` | Defines minimum node count for the generated JSON-LD knowledge graph. | `generate_knowledge_graph_jsonld.py`, `run_weekly_gap_batch.py` |
| `plg` | (PLG pack only) Controls API sandbox mode, value-first documentation requirements, and recommended sections. | Advisory guidance for PLG teams |

When a developer changes a file matching `interface_patterns` but does not change any file matching `doc_patterns`, the PR fails. That is how the pipeline enforces documentation freshness.

## Available policy packs

The pipeline ships with five built-in packs in the `policy_packs/` directory.

---

### 1. `minimal.yml` -- For pilots and new teams

**Use case:** First-time pipeline adoption, pilot weeks, or strict security environments where you need a minimal footprint. Lenient thresholds prevent early frustration while the team learns the workflow.

**Metadata:**

```yaml
name: minimal
version: 1
notes:
  - Minimal mode keeps only core quality gates and structure enforcement.
  - Use this mode for strict environments or fast pilot onboarding.
```

**Docs contract patterns (`docs_contract`):**

| Pattern type | Patterns |
| --- | --- |
| `interface_patterns` | `^api/`, `openapi.*\.(ya?ml\|json)$`, `^sdk/`, `^clients/` |
| `doc_patterns` | `^docs/`, `^templates/`, `^\.vscode/docs\.code-snippets$` |

**Drift patterns (`drift`):**

| Pattern type | Patterns |
| --- | --- |
| `openapi_patterns` | `openapi.*\.(ya?ml\|json)$`, `swagger.*\.(ya?ml\|json)$` |
| `sdk_patterns` | `^sdk/`, `^clients/` |
| `reference_doc_patterns` | `^docs/reference/`, `^templates/api-reference\.md$`, `^templates/sdk-reference\.md$` |

**KPI SLA thresholds (`kpi_sla`):**

| Threshold | Value |
| --- | --- |
| `min_quality_score` | 75 |
| `max_stale_pct` | 20.0% |
| `max_high_priority_gaps` | 10 |
| `max_quality_score_drop` | 8 |

**Key characteristics:**

- Broadest doc patterns (`^docs/`, `^templates/`) so almost any docs change satisfies the contract.
- Includes `.vscode/docs.code-snippets` as a valid doc change.
- Most lenient KPI thresholds across all packs.
- Allows quality to drop by up to 8 points between runs without triggering a breach.

---

### 2. `api-first.yml` -- For API-heavy products

**Use case:** Products where OpenAPI is the source of truth and API or SDK changes happen frequently. Prevents drift between API specifications and documentation with tight thresholds.

**Docs contract patterns (`docs_contract`):**

| Pattern type | Patterns |
| --- | --- |
| `interface_patterns` | `^api/`, `openapi.*\.(ya?ml\|json)$`, `swagger.*\.(ya?ml\|json)$`, `api-spec.*\.(ya?ml\|json)$`, `^sdk/`, `^clients/` |
| `doc_patterns` | `^docs/reference/`, `^docs/how-to/`, `^templates/api-reference\.md$`, `^templates/sdk-reference\.md$` |

**Drift patterns (`drift`):**

| Pattern type | Patterns |
| --- | --- |
| `openapi_patterns` | `openapi.*\.(ya?ml\|json)$`, `swagger.*\.(ya?ml\|json)$` |
| `sdk_patterns` | `^sdk/`, `^clients/` |
| `reference_doc_patterns` | `^docs/reference/`, `^templates/api-reference\.md$`, `^templates/sdk-reference\.md$` |

**KPI SLA thresholds (`kpi_sla`):**

| Threshold | Value |
| --- | --- |
| `min_quality_score` | 82 |
| `max_stale_pct` | 12.0% |
| `max_high_priority_gaps` | 6 |
| `max_quality_score_drop` | 4 |

**Key characteristics:**

- Recognizes `api-spec` files alongside `openapi` and `swagger` as interface triggers.
- Narrower doc patterns require updates specifically in `docs/reference/` or `docs/how-to/`, not just anywhere in `docs/`.
- This is the default pack used in all CI workflows (`pr-dod-contract.yml`, `api-sdk-drift-gate.yml`, `kpi-wall.yml`, `weekly-consolidation.yml`).
- Moderate-to-strict thresholds with a maximum quality drop of 4 points.

---

### 3. `monorepo.yml` -- For multi-service repositories

**Use case:** Repositories that contain multiple services or packages in subdirectories (for example, `services/auth/`, `services/billing/`, `packages/sdk-node/`). Patterns target nested folder structures.

**Docs contract patterns (`docs_contract`):**

| Pattern type | Patterns |
| --- | --- |
| `interface_patterns` | `^services/.*/api/`, `^services/.*/src/.*/(routes\|controllers\|public\|sdk)/`, `openapi.*\.(ya?ml\|json)$`, `swagger.*\.(ya?ml\|json)$`, `^packages/.*/sdk/` |
| `doc_patterns` | `^docs/`, `^services/.*/docs/`, `^templates/` |

**Drift patterns (`drift`):**

| Pattern type | Patterns |
| --- | --- |
| `openapi_patterns` | `openapi.*\.(ya?ml\|json)$`, `swagger.*\.(ya?ml\|json)$`, `^services/.*/api/` |
| `sdk_patterns` | `^packages/.*/sdk/`, `^clients/` |
| `reference_doc_patterns` | `^docs/reference/`, `^services/.*/docs/reference/`, `^templates/api-reference\.md$` |

**KPI SLA thresholds (`kpi_sla`):**

| Threshold | Value |
| --- | --- |
| `min_quality_score` | 80 |
| `max_stale_pct` | 15.0% |
| `max_high_priority_gaps` | 10 |
| `max_quality_score_drop` | 6 |

**Key characteristics:**

- Interface patterns use wildcard service paths (`services/.*/api/`, `packages/.*/sdk/`) to capture changes across all services automatically.
- Doc patterns accept both top-level `docs/` and per-service `services/.*/docs/` directories.
- Drift OpenAPI patterns also include `services/.*/api/` to catch per-service API definitions.
- Reference doc patterns include `services/.*/docs/reference/` for per-service reference documentation.
- Moderately lenient thresholds (quality 80, stale 15%) because monorepos accumulate stale docs more quickly.

---

### 4. `multi-product.yml` -- For product families

**Use case:** One documentation system covers multiple products (for example, `products/cloud/`, `products/self-hosted/`). Patterns target product-scoped directories under a `products/` root.

**Docs contract patterns (`docs_contract`):**

| Pattern type | Patterns |
| --- | --- |
| `interface_patterns` | `^api/`, `openapi.*\.(ya?ml\|json)$`, `swagger.*\.(ya?ml\|json)$`, `^products/.*/api/`, `^products/.*/sdk/` |
| `doc_patterns` | `^docs/products/`, `^docs/reference/`, `^templates/` |

**Drift patterns (`drift`):**

| Pattern type | Patterns |
| --- | --- |
| `openapi_patterns` | `openapi.*\.(ya?ml\|json)$`, `swagger.*\.(ya?ml\|json)$`, `^products/.*/api/` |
| `sdk_patterns` | `^products/.*/sdk/`, `^clients/` |
| `reference_doc_patterns` | `^docs/products/.*/reference/`, `^docs/reference/`, `^templates/api-reference\.md$`, `^templates/sdk-reference\.md$` |

**KPI SLA thresholds (`kpi_sla`):**

| Threshold | Value |
| --- | --- |
| `min_quality_score` | 84 |
| `max_stale_pct` | 10.0% |
| `max_high_priority_gaps` | 5 |
| `max_quality_score_drop` | 3 |

**Key characteristics:**

- Interface patterns include `products/.*/api/` and `products/.*/sdk/` for per-product boundaries.
- Doc patterns require changes in `docs/products/` (product-scoped docs) or `docs/reference/` (shared reference).
- Reference doc patterns include `docs/products/.*/reference/` for per-product reference documentation.
- Strict thresholds (quality 84, stale 10%, max 5 gaps, max 3-point drop) because product families need tight cross-product consistency.

---

### 5. `plg.yml` -- For product-led growth

**Use case:** Self-serve activation and adoption are top goals. Documentation must drive user onboarding without human intervention. Includes extra PLG-specific settings for API sandbox behavior and value-first documentation patterns.

**Metadata:**

```yaml
name: plg
version: 1
notes:
  - PLG profile adds value-first documentation patterns and interactive API sandbox controls.
  - Use this pack for self-serve onboarding and adoption-focused docs programs.
```

**Docs contract patterns (`docs_contract`):**

| Pattern type | Patterns |
| --- | --- |
| `interface_patterns` | `^api/`, `openapi.*\.(ya?ml\|json)$`, `^sdk/`, `^clients/`, `^src/` |
| `doc_patterns` | `^docs/`, `^templates/`, `^\.vscode/docs\.code-snippets$` |

**Drift patterns (`drift`):**

| Pattern type | Patterns |
| --- | --- |
| `openapi_patterns` | `openapi.*\.(ya?ml\|json)$`, `swagger.*\.(ya?ml\|json)$` |
| `sdk_patterns` | `^sdk/`, `^clients/` |
| `reference_doc_patterns` | `^docs/reference/`, `^templates/api-reference\.md$`, `^templates/sdk-reference\.md$` |

**KPI SLA thresholds (`kpi_sla`):**

| Threshold | Value |
| --- | --- |
| `min_quality_score` | 84 |
| `max_stale_pct` | 10.0% |
| `max_high_priority_gaps` | 5 |
| `max_quality_score_drop` | 3 |

**PLG-specific settings (`plg`):**

| Setting | Value | Description |
| --- | --- | --- |
| `mode` | `mixed` | PLG documentation mode |
| `try_it_mode` | `sandbox-only` | API playground behavior: `sandbox-only`, `real-api`, or `mixed` |
| `try_it_enabled` | `false` | Whether API playground is active |
| `value_first_docs.enabled` | `true` | Enables value-first documentation patterns |
| `value_first_docs.recommended_sections` | `time-to-value`, `expected-outcome`, `activation-checklist` | Advisory sections recommended for every document (not enforced as blocking requirements) |

**Key characteristics:**

- Broadest interface patterns: includes `^src/` so any source code change (not just API/SDK) triggers the docs contract.
- Same strict KPI thresholds as multi-product (quality 84, stale 10%, max 5 gaps, max 3-point drop).
- Only pack with the `plg` section for API sandbox and value-first documentation configuration.
- Broad doc patterns (like minimal) so that any docs change satisfies the contract.

---

## Side-by-side comparison of all five packs

### KPI SLA thresholds

| Threshold | `minimal` | `api-first` | `monorepo` | `multi-product` | `plg` |
| --- | --- | --- | --- | --- | --- |
| `min_quality_score` | 75 | 82 | 80 | 84 | 84 |
| `max_stale_pct` | 20.0% | 12.0% | 15.0% | 10.0% | 10.0% |
| `max_high_priority_gaps` | 10 | 6 | 10 | 5 | 5 |
| `max_quality_score_drop` | 8 | 4 | 6 | 3 | 3 |

### Retrieval eval thresholds

| Threshold | `minimal` | `api-first` | `monorepo` | `multi-product` | `plg` |
| --- | --- | --- | --- | --- | --- |
| `min_precision` | 0.40 | 0.50 | 0.50 | 0.55 | 0.60 |
| `min_recall` | 0.40 | 0.50 | 0.50 | 0.55 | 0.60 |
| `max_hallucination_rate` | 0.60 | 0.50 | 0.50 | 0.45 | 0.40 |

### Knowledge graph minimum size

| Threshold | `minimal` | `api-first` | `monorepo` | `multi-product` | `plg` |
| --- | --- | --- | --- | --- | --- |
| `min_graph_nodes` | 3 | 5 | 5 | 8 | 10 |

### Interface patterns (docs contract)

| Pattern | `minimal` | `api-first` | `monorepo` | `multi-product` | `plg` |
| --- | --- | --- | --- | --- | --- |
| `^api/` | Yes | Yes | -- | Yes | Yes |
| `openapi.*\.(ya?ml\|json)$` | Yes | Yes | Yes | Yes | Yes |
| `swagger.*\.(ya?ml\|json)$` | -- | Yes | Yes | Yes | -- |
| `api-spec.*\.(ya?ml\|json)$` | -- | Yes | -- | -- | -- |
| `^sdk/` | Yes | Yes | -- | -- | Yes |
| `^clients/` | Yes | Yes | -- | -- | Yes |
| `^src/` | -- | -- | -- | -- | Yes |
| `^services/.*/api/` | -- | -- | Yes | -- | -- |
| `^services/.*/src/.*/(routes\|controllers\|public\|sdk)/` | -- | -- | Yes | -- | -- |
| `^packages/.*/sdk/` | -- | -- | Yes | -- | -- |
| `^products/.*/api/` | -- | -- | -- | Yes | -- |
| `^products/.*/sdk/` | -- | -- | -- | Yes | -- |

### Doc patterns (docs contract)

| Pattern | `minimal` | `api-first` | `monorepo` | `multi-product` | `plg` |
| --- | --- | --- | --- | --- | --- |
| `^docs/` | Yes | -- | Yes | -- | Yes |
| `^docs/reference/` | -- | Yes | -- | -- | -- |
| `^docs/how-to/` | -- | Yes | -- | -- | -- |
| `^docs/products/` | -- | -- | -- | Yes | -- |
| `^services/.*/docs/` | -- | -- | Yes | -- | -- |
| `^templates/` | Yes | -- | Yes | Yes | Yes |
| `^templates/api-reference\.md$` | -- | Yes | -- | -- | -- |
| `^templates/sdk-reference\.md$` | -- | Yes | -- | -- | -- |
| `^\.vscode/docs\.code-snippets$` | Yes | -- | -- | -- | Yes |

### Strictness ranking (least to most strict)

1. **`minimal`** -- Most lenient. Broadest doc patterns, highest stale tolerance, largest quality drop allowed.
1. **`monorepo`** -- Moderate. Wider gap tolerance (10) for multi-service complexity, moderate stale tolerance (15%).
1. **`api-first`** -- Moderate-to-strict. Narrow doc patterns require targeted updates. Tight quality drop limit (4).
1. **`multi-product`** -- Strict. Tight thresholds across all four metrics. Product-scoped pattern enforcement.
1. **`plg`** -- Strictest KPI thresholds (tied with multi-product) plus broadest interface triggers (`^src/` catches all source changes) and PLG-specific documentation requirements.

---

## How to choose a pack

```text
Is this a pilot week or first-time adoption?
  YES -> minimal.yml
  NO  -> Continue

Does the product have an OpenAPI spec?
  YES -> Is product-led growth a priority?
    YES -> plg.yml
    NO  -> Continue
  NO  -> Continue

Is it a monorepo with multiple services?
  YES -> monorepo.yml
  NO  -> Continue

Does one docs system cover multiple products?
  YES -> multi-product.yml
  NO  -> api-first.yml (good default for most teams)
```

## How to configure a policy pack

### Option 1: Workflow inputs (recommended for CI)

The `kpi-wall.yml` and `weekly-consolidation.yml` workflows accept a `policy_pack` input when triggered manually:

```yaml
# In the GitHub Actions UI, set:
policy_pack: policy_packs/plg.yml
```

When triggered on schedule (no manual input), both workflows default to `policy_packs/api-first.yml`.

**Workflow defaults:**

| Workflow | Default pack | Accepts input? |
| --- | --- | --- |
| `pr-dod-contract.yml` | `policy_packs/api-first.yml` (hardcoded) | No |
| `api-sdk-drift-gate.yml` | `policy_packs/api-first.yml` (hardcoded) | No |
| `kpi-wall.yml` | `policy_packs/api-first.yml` | Yes (`policy_pack` input) |
| `weekly-consolidation.yml` | `policy_packs/api-first.yml` | Yes (`policy_pack` input) |
| `docs-ops-e2e.yml` | N/A (tests all packs) | No |

To change the default pack for PR-level workflows (`pr-dod-contract.yml`, `api-sdk-drift-gate.yml`), edit the `--policy-pack` argument in the workflow YAML file.

### Option 2: Command-line flag (for local runs)

Pass `--policy-pack` to any script that supports it:

```bash
python3 scripts/check_docs_contract.py \
  --base origin/main \
  --head HEAD \
  --policy-pack policy_packs/plg.yml

python3 scripts/check_api_sdk_drift.py \
  --base origin/main \
  --head HEAD \
  --policy-pack policy_packs/plg.yml \
  --json-output reports/api_sdk_drift_report.json \
  --md-output reports/api_sdk_drift_report.md

python3 scripts/evaluate_kpi_sla.py \
  --current reports/kpi-wall.json \
  --policy-pack policy_packs/plg.yml \
  --json-output reports/kpi-sla-report.json \
  --md-output reports/kpi-sla-report.md
```

When `--policy-pack` is omitted, each script falls back to hardcoded defaults:

| Script | Default thresholds |
| --- | --- |
| `check_docs_contract.py` | `INTERFACE_PATTERNS` and `DOC_PATTERNS` constants in the script |
| `check_api_sdk_drift.py` | `OPENAPI_PATTERNS`, `SDK_PATTERNS`, and `REFERENCE_DOC_PATTERNS` constants in the script |
| `evaluate_kpi_sla.py` | `min_quality_score: 80`, `max_stale_pct: 15.0`, `max_high_priority_gaps: 8`, `max_quality_score_drop: 5` |

### Option 3: GUI configurator

```bash
npm run configurator
```

Open `reports/pipeline-configurator.html` in a browser. The wizard lets you pick a pack, adjust thresholds, and export configuration files.

---

## How policy packs affect pipeline components

### KPI SLA evaluation

The `evaluate_kpi_sla.py` script reads the `kpi_sla` section from the selected policy pack and compares current metrics against four thresholds:

1. **`min_quality_score`** -- Current quality score must be greater than or equal to this value. If the score falls below, the report status becomes `breach`.
1. **`max_stale_pct`** -- Current stale document percentage must be less than or equal to this value. Exceeding it triggers a breach.
1. **`max_high_priority_gaps`** -- Number of high-priority documentation gaps must be less than or equal to this value. Exceeding it triggers a breach.
1. **`max_quality_score_drop`** -- When a previous KPI snapshot exists, the quality score must not drop more than this many points. A larger drop triggers a breach.

A single breach in any threshold causes the overall SLA status to become `breach`, which:

- Fails the `kpi-wall.yml` workflow job.
- Creates a GitHub issue labeled `high-priority`.
- Sets `sla_status: breach` in the consolidated report.

**Impact of pack selection on SLA evaluation:**

- `minimal` allows quality as low as 75 and stale as high as 20%, so it rarely triggers breaches.
- `plg` and `multi-product` require quality of 84 and stale under 10%, so they breach more aggressively.

### Drift detection

The `check_api_sdk_drift.py` script reads the `drift` section from the selected policy pack:

1. **`openapi_patterns`** -- Regex patterns that identify OpenAPI and Swagger spec file changes.
1. **`sdk_patterns`** -- Regex patterns that identify SDK and client library file changes.
1. **`reference_doc_patterns`** -- Regex patterns that identify reference documentation file changes.

The drift check compares changed files in a PR against these patterns. If any file matches `openapi_patterns` or `sdk_patterns` but no file matches `reference_doc_patterns`, the status becomes `drift`, which:

- Fails the `api-sdk-drift-gate.yml` workflow job.
- Creates a GitHub issue labeled `doc-gap`.
- Adds `priority: high` action items to the consolidated report.

**Impact of pack selection on drift detection:**

- `monorepo` includes `services/.*/api/` in its OpenAPI patterns, so per-service API changes trigger drift checks.
- `multi-product` includes `products/.*/api/` and scopes reference docs to `docs/products/.*/reference/`.
- `api-first` includes `api-spec` files that other packs do not recognize.

### DoD contract (docs contract)

The `check_docs_contract.py` script reads the `docs_contract` section from the selected policy pack:

1. **`interface_patterns`** -- Regex patterns that identify public interface file changes (API routes, controllers, SDK code).
1. **`doc_patterns`** -- Regex patterns that identify documentation file changes.

The contract check compares changed files in a PR. If any file matches `interface_patterns` but no file matches `doc_patterns`, the PR is blocked with exit code 1, which:

- Fails the `pr-dod-contract.yml` workflow job.
- Prevents merging until documentation is updated.

**Impact of pack selection on DoD contract:**

- `minimal` and `plg` use broad doc patterns (`^docs/`, `^templates/`), so almost any docs change satisfies the contract.
- `api-first` uses narrow doc patterns (`^docs/reference/`, `^docs/how-to/`), so only targeted reference or how-to updates satisfy the contract. Changing a tutorial or concept page does not count.
- `plg` has the broadest interface patterns (`^src/` catches all source code changes), so more PRs trigger the docs requirement.
- `monorepo` requires docs changes in either `^docs/` or `^services/.*/docs/`, supporting per-service documentation structures.

### Consolidated report prioritization

The `consolidate_reports.py` script does not read policy packs directly. Instead, it consumes the output of the three scripts above, which were already evaluated against the selected policy pack. The pack affects the consolidated report indirectly:

1. **SLA breach items** -- When `evaluate_kpi_sla.py` reports breaches (controlled by `kpi_sla` thresholds), the consolidator creates `priority: high` action items with category `sla_breach`. Stricter packs (PLG, multi-product) generate more SLA breach items.
1. **Drift items** -- When `check_api_sdk_drift.py` reports drift (controlled by `drift` patterns), the consolidator creates `priority: high` action items with category `api_drift` or `sdk_drift`. Packs with broader drift patterns (monorepo, multi-product) catch more drift events.
1. **Cross-referencing** -- The consolidator annotates gap items with `drift_related: true` when their `related_files` overlap with drift-detected files. Packs that watch more files for drift produce more cross-referenced items.
1. **Health summary** -- The consolidated report `health_summary` includes `sla_status` and `drift_status` values that come directly from the policy-pack-evaluated reports. The weekly GitHub issue displays these values.

**Practical effect:** A stricter policy pack produces more action items in the consolidated report and raises the urgency of the weekly GitHub issue. A lenient pack produces fewer action items.

---

## How to create a custom pack for a client

1. Copy the closest existing pack:

```bash
cp policy_packs/api-first.yml policy_packs/client-acme.yml
```

1. Edit the copy:

```yaml
# policy_packs/client-acme.yml

# Patterns matching the client's code structure
docs_contract:
  interface_patterns:
    - "^api/"
    - "openapi.*\\.(ya?ml|json)$"
    - "^sdk/"
    - "^clients/"
  doc_patterns:
    - "^docs/"
    - "^guides/"
    - "^templates/"

# Drift detection patterns
drift:
  openapi_patterns:
    - "openapi.*\\.(ya?ml|json)$"
    - "swagger.*\\.(ya?ml|json)$"
  sdk_patterns:
    - "^sdk/"
    - "^clients/"
  reference_doc_patterns:
    - "^docs/reference/"
    - "^templates/api-reference\\.md$"

# KPI thresholds (start lenient, tighten over time)
kpi_sla:
  min_quality_score: 78
  max_stale_pct: 15.0
  max_high_priority_gaps: 8
  max_quality_score_drop: 5
```

1. Test locally:

```bash
python3 scripts/check_docs_contract.py \
  --base origin/main \
  --head HEAD \
  --policy-pack policy_packs/client-acme.yml
```

1. When it passes, use it in CI workflows by updating the `--policy-pack` argument or the `policy_pack` workflow input.

## Common mistakes

| Mistake | What happens | Fix |
| --- | --- | --- |
| Patterns too broad (`src/**`) | Every code change triggers docs requirement | Narrow to specific directories |
| Patterns too narrow (`src/api/v2/users.py`) | Most changes bypass checks | Use glob patterns |
| Thresholds set without baseline | Immediate CI failures | Run `pilot_analysis.py` first, then set thresholds 5-10% below baseline |
| Using `plg.yml` for a pilot | Too strict, team gets frustrated | Start with `minimal.yml`, upgrade later |
| Forgetting to update PR workflows | PR checks still use the old default pack | Edit `--policy-pack` in `pr-dod-contract.yml` and `api-sdk-drift-gate.yml` |
| Omitting `drift` section | Scripts fall back to hardcoded defaults that may not match your repo structure | Always define all three sections in custom packs |

## Recommended rollout path

1. **Week 1**: Use `minimal.yml`. Run baseline measurement. Fix obvious issues.
1. **Week 2**: Tighten thresholds based on baseline data. Resolve top gaps.
1. **Week 3+**: Switch to `api-first.yml` or a custom client pack. Enable all CI gates.

## Definition of done for policy pack rollout

A policy pack rollout is done when:

1. Local checks pass with the selected pack.
1. PR checks pass with the selected pack.
1. Team understands why failures happen and how to fix them.
1. Baseline and target thresholds are documented.
1. Custom pack is created if built-in packs do not match.

## Next steps

- [Documentation index](../index.md)

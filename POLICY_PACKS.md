# Policy packs

This guide explains what policy packs are, how they work, and how to choose the right one for each company.

## What is a policy pack?

A policy pack is a YAML configuration file that controls how strict the pipeline checks are. Think of it as a quality profile. Different companies need different levels of strictness.

For example:

- A new team running a pilot needs lenient checks so they can adopt the pipeline gradually.
- An API-heavy product needs strict drift detection so API docs never fall behind.
- A product-led growth company needs the strictest checks on user-facing docs.

## What a policy pack controls

Each policy pack defines four things:

| Setting | What it does | Example |
| --- | --- | --- |
| `interface_patterns` | Which source code files count as "interface changes" | `src/controllers/**`, `src/routes/**` |
| `docs_patterns` | Which docs files must be updated when interfaces change | `docs/**/*.md`, `guides/**/*.md` |
| `drift_patterns` | Which files signal API/SDK drift | `openapi*.yaml`, `sdk/**` |
| `kpi_sla` | Quality thresholds for reporting | Min quality 82%, max stale 12% |

When a developer changes a file matching `interface_patterns` but does not change any file matching `docs_patterns`, the PR fails. That is how the pipeline enforces documentation freshness.

## Available policy packs

The pipeline ships with five built-in packs:

### 1. `minimal.yml` - For pilots and new teams

```yaml
# policy_packs/minimal.yml
min_quality_score: 75      # Lenient quality threshold
max_stale_percentage: 20   # Tolerates some stale docs
max_high_priority_gaps: 10 # Allows more gaps initially
max_quality_score_drop: 8  # Tolerates larger quality drops
```

**Use this when:**

- The team has never used the pipeline before.
- You are running a pilot week.
- The company has strict security restrictions and you need minimal footprint.

### 2. `api-first.yml` - For API-heavy products

```yaml
# policy_packs/api-first.yml
min_quality_score: 82      # Strict quality
max_stale_percentage: 12   # Low stale tolerance
max_high_priority_gaps: 6  # Few gaps allowed
max_quality_score_drop: 4  # Tight quality regression limit
```

**Use this when:**

- OpenAPI is the source of truth.
- API and SDK changes happen frequently.
- Preventing drift between API and docs is the top priority.

### 3. `monorepo.yml` - For multi-service repositories

```yaml
# policy_packs/monorepo.yml
min_quality_score: 80
max_stale_percentage: 15
max_high_priority_gaps: 8
max_quality_score_drop: 6
```

**Use this when:**

- Multiple services live in one repository.
- Docs and code are split across many folders.
- You need folder-specific interface and docs patterns.

### 4. `multi-product.yml` - For product families

```yaml
# policy_packs/multi-product.yml
min_quality_score: 80
max_stale_percentage: 15
max_high_priority_gaps: 8
max_quality_score_drop: 6
```

**Use this when:**

- One documentation system supports multiple products.
- You need boundaries between product areas.

### 5. `plg.yml` - For product-led growth

```yaml
# policy_packs/plg.yml
min_quality_score: 85      # Highest quality bar
max_stale_percentage: 10   # Lowest stale tolerance
max_high_priority_gaps: 5  # Fewest gaps allowed
max_quality_score_drop: 3  # Tightest quality regression limit
```

**Use this when:**

- Self-serve activation and adoption are top goals.
- You need value-first documentation patterns (persona guides, use-case pages).
- You want API playground behavior policy (`sandbox-only`, `real-api`, `mixed`).

## How to choose a pack

```text
Is this a pilot week?
  YES -> minimal.yml
  NO  -> Continue

Does the product have an OpenAPI spec?
  YES -> Is PLG a priority?
    YES -> plg.yml
    NO  -> api-first.yml
  NO  -> Continue

Is it a monorepo with multiple services?
  YES -> monorepo.yml
  NO  -> Continue

Does one docs system cover multiple products?
  YES -> multi-product.yml
  NO  -> api-first.yml (good default for most teams)
```

## How to use a policy pack

### Run checks with a specific pack

```bash
python3 scripts/check_docs_contract.py \
  --base origin/main \
  --head HEAD \
  --policy-pack policy_packs/api-first.yml

python3 scripts/check_api_sdk_drift.py \
  --base origin/main \
  --head HEAD \
  --policy-pack policy_packs/api-first.yml \
  --json-output reports/api_sdk_drift_report.json \
  --md-output reports/api_sdk_drift_report.md

python3 scripts/evaluate_kpi_sla.py \
  --current reports/kpi-wall.json \
  --policy-pack policy_packs/api-first.yml \
  --json-output reports/kpi-sla-report.json \
  --md-output reports/kpi-sla-report.md
```

### Use the GUI configurator

```bash
npm run configurator
```

Open `reports/pipeline-configurator.html` in a browser. The wizard lets you pick a pack, adjust thresholds, and export configuration files.

## How to create a custom pack for a client

1. Copy the closest existing pack:

```bash
cp policy_packs/api-first.yml policy_packs/client-acme.yml
```

1. Edit the copy:

```yaml
# policy_packs/client-acme.yml

# Patterns matching the client's code structure
interface_patterns:
  - "src/controllers/**"
  - "src/routes/**"
  - "src/api/**"
  - "lib/sdk/**"

# Patterns matching the client's docs structure
docs_patterns:
  - "docs/**/*.md"
  - "guides/**/*.md"

# KPI thresholds (start lenient, tighten over time)
kpi_sla:
  min_quality_score: 78
  max_stale_percentage: 15
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

1. When it passes, use it in CI workflows.

## Common mistakes

| Mistake | What happens | Fix |
| --- | --- | --- |
| Patterns too broad (`src/**`) | Every code change triggers docs requirement | Narrow to specific directories |
| Patterns too narrow (`src/api/v2/users.py`) | Most changes bypass checks | Use glob patterns |
| Thresholds set without baseline | Immediate CI failures | Run `pilot_analysis.py` first, then set thresholds 5-10% below baseline |
| Using `plg.yml` for a pilot | Too strict, team gets frustrated | Start with `minimal.yml`, upgrade later |

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

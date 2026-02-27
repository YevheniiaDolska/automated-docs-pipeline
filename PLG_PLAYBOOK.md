# PLG documentation playbook

This playbook explains how to create product-led growth (PLG) documentation. PLG documentation helps users activate themselves without talking to a salesperson. It focuses on showing value first, then explaining implementation.

## What product-led growth documentation is

Traditional documentation explains features. PLG documentation explains outcomes. The difference:

| Traditional docs | PLG docs |
| --- | --- |
| "The Webhook node accepts HTTP requests" | "Receive real-time notifications when customers place orders" |
| Feature-first structure | Value-first structure |
| Aimed at developers who already bought | Aimed at evaluators deciding whether to buy |
| One audience | Multiple personas (developer, marketer, operator) |

PLG documentation drives three things:

1. **Activation**: Users complete their first successful action without help.
1. **Adoption**: Users discover more use cases and expand usage.
1. **Retention**: Users keep coming back because docs make the product easy.

## When to use this playbook

Use this playbook when:

1. The product has a free tier or trial that users sign up for without sales.
1. Self-serve onboarding is a business priority.
1. The company measures activation rate, time-to-value, or product-qualified leads.
1. Documentation is part of the conversion funnel, not just a support resource.

If the product is sold only through enterprise sales with no self-serve path, use `API_FIRST_PLAYBOOK.md` instead.

## Core PLG documentation patterns

PLG docs use five patterns that traditional docs do not:

### 1. Persona entry pages

Instead of one generic "Getting Started" page, create a separate entry page for each user type.

Example personas:

1. **Developer**: wants API reference, SDKs, code examples.
1. **Marketer**: wants workflow automation, templates, integrations.
1. **Operations lead**: wants monitoring, alerts, compliance docs.

Each persona page answers: "What can this product do for someone like me?"

Template: `templates/plg-persona-guide.md`

### 2. Value-first use-case pages

Each use-case page starts with the business outcome, not the technical setup.

Structure:

1. **Headline**: "Automate order confirmations in 10 minutes"
1. **Setup time**: "Setup: 10 minutes. No coding required."
1. **Expected result**: "After setup, every new order triggers a confirmation email with tracking number."
1. **Step-by-step instructions**: How to set it up.
1. **What you built**: Summary of what the user accomplished.

Template: `templates/plg-value-page.md`

### 3. Workflow stack pages

Workflow stacks combine multiple features into one documented outcome. Instead of documenting each feature separately, show how they work together.

Example: "Build a customer onboarding pipeline" combines:

1. Webhook trigger (receives signup event).
1. Data transformation (formats user data).
1. Email send (welcome message).
1. CRM update (logs new customer).

### 4. Before-and-after framing

Every use-case page includes a before/after comparison to build decision confidence:

```markdown
## Before

1. Manual data entry into 3 systems after each sale.
1. 15 minutes per order.
1. Errors in 8% of entries.

## After

1. Automatic sync across all 3 systems.
1. 0 minutes per order (fully automated).
1. 0% manual entry errors.
```

### 5. Fast activation checklists

Short checklists that lead to first successful run. Target: under 5 minutes from signup to first success.

```markdown
## Quick activation checklist

1. [ ] Create account (1 minute).
1. [ ] Connect your first data source (2 minutes).
1. [ ] Run the sample workflow (1 minute).
1. [ ] Check the output in your dashboard (1 minute).

Total time: under 5 minutes.
```

## Templates for PLG documentation

The pipeline includes templates designed for PLG content:

| Template | What it creates | When to use |
| --- | --- | --- |
| `templates/plg-persona-guide.md` | Persona-specific entry page | One per user persona |
| `templates/plg-value-page.md` | Value-first use-case page | One per key use case |
| `templates/use-case.md` | General use-case documentation | Use cases without PLG framing |
| `templates/quickstart.md` | Fast activation guide | Main getting-started page |

## API playground as part of PLG

Interactive API documentation reduces onboarding friction. Instead of reading about API endpoints, users try them directly in the browser.

### What the API playground does

1. Displays API endpoints with request/response schemas.
1. Lets users send test requests from the documentation page.
1. Routes test requests to a safe sandbox (not production).

### How to configure the API playground

Add this configuration block to `mkdocs.yml`:

```yaml
extra:
  plg:
    mode: mixed
    approach: hybrid
    api_playground:
      enabled: true
      provider: swagger-ui
      try_it_mode: sandbox-only
      try_it_enabled: false
      source:
        strategy: api-first
        api_first_spec_url: /api/openapi.yaml
        code_first_spec_url: /api/openapi-generated.yaml
      endpoints:
        sandbox_base_url: https://sandbox-api.example.com
        production_base_url: https://api.example.com
```

### Configuration options explained

**Provider choices:**

| Provider | What it does |
| --- | --- |
| `swagger-ui` | Interactive API explorer with "Try it out" button |
| `redoc` | Readable API reference, non-interactive by default |

**Try-it-mode choices:**

| Mode | What happens when user clicks "Try it out" |
| --- | --- |
| `sandbox-only` | All requests go to sandbox URL (safest) |
| `real-api` | All requests go to production API |
| `mixed` | User can switch between sandbox and production |

For most PLG setups, use `sandbox-only` to prevent accidental production changes during evaluation.

### Start a mock API sandbox

If you do not have a sandbox environment yet, the pipeline can create one from your OpenAPI spec:

```bash
npm run api:sandbox:mock
```

This starts a Prism mock server on port 4010 that returns realistic fake responses based on your OpenAPI spec. Stop it with:

```bash
npm run api:sandbox:stop
```

## API source strategy

The playground needs an OpenAPI specification file. Two strategies exist for providing it:

### API-first

You write the OpenAPI spec manually and commit it to the repository. The spec is the source of truth.

```yaml
source:
  strategy: api-first
  api_first_spec_url: /api/openapi.yaml
```

### Code-first

Your code generates the OpenAPI spec automatically. The pipeline resolves the generated spec.

```yaml
source:
  strategy: code-first
  code_first_spec_url: /api/openapi-generated.yaml
```

The workflow `.github/workflows/openapi-source-sync.yml` handles resolution for both strategies.

## PLG policy pack

The `plg.yml` policy pack enforces the strictest quality standards because PLG documentation directly affects conversion:

```yaml
# policy_packs/plg.yml
min_quality_score: 85      # Highest quality bar
max_stale_percentage: 10   # Lowest stale tolerance
max_high_priority_gaps: 5  # Fewest gaps allowed
max_quality_score_drop: 3  # Tightest quality regression limit
```

Use this pack for all PLG documentation projects. See `POLICY_PACKS.md` for details on all available packs.

## PLG documentation checklist

Use this checklist when creating PLG documentation for a client:

1. [ ] Persona entry pages exist for each key user type.
1. [ ] At least 3 value-first use-case pages are written.
1. [ ] Each use-case page has setup time and expected result.
1. [ ] Activation checklist targets under 5 minutes.
1. [ ] API playground is configured (if product has an API).
1. [ ] `plg.yml` policy pack is selected.
1. [ ] All pages pass `npm run validate:full`.
1. [ ] Before/after framing is included in at least 2 pages.
1. [ ] Shared variables from `docs/_variables.yml` are used (no hardcoded values).

## Human role in PLG documentation

Automation and AI handle:

1. Drafting from templates.
1. Quality checks and enforcement.
1. Gap detection and staleness tracking.
1. SEO/GEO optimization.

Humans validate:

1. Business relevance of use cases.
1. Accuracy of setup times and outcomes.
1. Persona definitions match actual user segments.
1. Policy fit (is the quality bar right for this company).

## Related guides

| Guide | What it covers |
| --- | --- |
| `POLICY_PACKS.md` | All policy packs including `plg.yml` |
| `API_FIRST_PLAYBOOK.md` | API-first documentation workflow |
| `CUSTOMIZATION_PER_COMPANY.md` | Full per-company configuration |
| `PILOT_VS_FULL_IMPLEMENTATION.md` | Pilot week vs full implementation |

# PLG documentation playbook

Product-led growth (PLG) documentation helps users activate themselves without talking to a salesperson. This playbook covers how the Auto-Doc Pipeline supports PLG documentation through dedicated templates, a strict policy pack, and consolidated reporting.

## PLG policy pack thresholds

The `plg.yml` policy pack enforces the strictest quality bar because PLG documentation directly affects conversion and activation rates.

```yaml
# policy_packs/plg.yml
kpi_sla:
  min_quality_score: 84
  max_stale_pct: 10.0
  max_high_priority_gaps: 5
  max_quality_score_drop: 3
```

Compare with `minimal.yml` (score 75, stale 20%, gaps 10) and `api-first.yml` (score 82, stale 12%, gaps 6). The PLG pack is the tightest because outdated or confusing onboarding docs lose self-serve users permanently.

The PLG pack also enables value-first documentation guidance:

```yaml
plg:
  mode: mixed
  try_it_mode: sandbox-only
  value_first_docs:
    enabled: true
    recommended_sections:
      - time-to-value
      - expected-outcome
      - activation-checklist
```

## PLG templates

The pipeline includes two templates designed for PLG content:

| Template | Purpose | When to use |
| --- | --- | --- |
| `templates/plg-persona-guide.md` | Persona-specific entry page | One per user persona (developer, marketer, operator) |
| `templates/plg-value-page.md` | Value-first use-case page | One per key use case or workflow |

### Persona guide template

Instead of one generic getting-started page, create a separate entry page for each user type. Each persona page answers: "What can this product do for someone like me?"

Recommended personas:

1. **Developer**: API reference, SDKs, code examples.
1. **Marketer**: workflow automation, templates, integrations.
1. **Operations lead**: monitoring, alerts, compliance.

### Value page template

Each value page starts with the business outcome, not the technical setup:

1. **Headline**: State the outcome and time estimate.
1. **Setup time**: Tell the user how long this takes.
1. **Expected result**: Describe what happens after setup.
1. **Step-by-step instructions**: Walk through the implementation.
1. **What you built**: Summarize the accomplishment.

## PLG docs in the consolidated report

When you run `npm run consolidate`, the consolidated report prioritizes PLG documentation issues:

1. **Stale onboarding pages** appear at the top of the priority list because they directly affect activation rates.
1. **Missing persona pages** are flagged as high-priority gaps.
1. **Value pages without time-to-value sections** are flagged as quality issues.
1. **Activation checklists missing from quickstart pages** generate warnings.

The consolidated report merges gap detection, KPI wall, and staleness data into one actionable document that Claude Code can process to generate or fix documentation.

## Quickstart and tutorial templates for onboarding

PLG onboarding relies on two additional templates from the standard set:

| Template | PLG role |
| --- | --- |
| `templates/quickstart.md` | First activation experience (under 5 minutes to first success) |
| `templates/tutorial.md` | Guided learning path after activation |

### Quickstart for PLG

The quickstart template targets under 5 minutes from signup to first successful action. Structure:

1. One-sentence description of what the user will accomplish.
1. Prerequisites (keep to 2-3 items maximum).
1. Steps (keep to 5 or fewer).
1. Verification that it worked.
1. Link to next steps.

### Tutorial for PLG

Tutorials expand on the quickstart by teaching a complete workflow. They follow the Diataxis learning-oriented pattern but add PLG elements:

1. Before/after framing (what changes after completing this tutorial).
1. Time estimate at the top.
1. Real use-case context (not abstract examples).

## PLG documentation checklist

Use this checklist when creating PLG documentation:

1. [ ] Persona entry pages exist for each key user type.
1. [ ] At least 3 value-first use-case pages are written.
1. [ ] Each use-case page has setup time and expected result.
1. [ ] Activation checklist targets under 5 minutes.
1. [ ] `plg.yml` policy pack is selected in workflow configuration.
1. [ ] All pages pass `npm run validate:full`.
1. [ ] Before/after framing is included in at least 2 pages.
1. [ ] Shared variables from `docs/_variables.yml` are used everywhere.

## Switching to the PLG policy pack

Change the `policy_pack` input in your workflow files:

```yaml
# In .github/workflows/kpi-wall.yml
with:
  policy_pack: policy_packs/plg.yml
```

Or run locally:

```bash
python3 scripts/evaluate_kpi_sla.py \
  --current reports/kpi-wall.json \
  --policy-pack policy_packs/plg.yml \
  --md-output reports/kpi-sla-report.md
```

## Human role in PLG documentation

The pipeline handles drafting, quality checks, gap detection, and SEO/GEO optimization. Humans validate:

1. Business relevance of use cases.
1. Accuracy of setup times and outcomes.
1. Persona definitions match actual user segments.
1. Policy fit for the company stage.

## Related guides

| Guide | What it covers |
| --- | --- |
| `POLICY_PACKS.md` | All five policy packs and how to choose |
| `API_FIRST_PLAYBOOK.md` | API-first documentation workflow |
| `PILOT_VS_FULL_IMPLEMENTATION.md` | Pilot week vs full implementation |
| `CUSTOMIZATION_PER_COMPANY.md` | Full per-company configuration |

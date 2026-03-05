# Pilot week service proposal

## What you get

The pilot week is a 5-day engagement that installs the Auto-Doc Pipeline on your real repository and delivers measurable results. This is not a demo. You receive a working system, generated documentation, and data that proves the value.

## Deliverables

### 1. Configured pipeline

The pipeline is installed and configured in your repository with:

- Quality gates active in CI (markdownlint, frontmatter validation, SEO/GEO checks, code example smoke tests).
- `minimal.yml` policy pack with relaxed thresholds for initial adoption.
- `docs/_variables.yml` populated with your product information.
- 3-5 templates customized for your product and content model.

### 2. First consolidated report processed

The consolidated report merges gap detection, KPI data, and staleness analysis into one prioritized document. It identifies:

- Missing documentation ranked by business impact.
- Stale pages that need updating.
- Quality issues across existing documentation.
- SEO/GEO optimization opportunities.

### 3. Generated documentation (5-10 pages)

Claude Code processes the consolidated report and generates 5-10 documents from the highest-priority items. Each document:

- Uses a pre-validated template from the 31-template library.
- References shared variables (no hardcoded product names, URLs, or ports).
- Passes all 7 linters (Vale, markdownlint, cspell, frontmatter, SEO/GEO, contract, drift).
- Includes self-verified code examples and fact-checked assertions.

### 4. Before/after KPI comparison

Baseline measurements are captured on day 1 and final measurements on day 5:

- Documentation quality score.
- Stale documentation percentage.
- High-priority gap count.
- Metadata completeness.

### 5. Team training

A 60-90 minute session covering:

- How to create documentation from templates.
- How to run local validation (`npm run validate:minimal`).
- How to read the consolidated report.
- How to use Claude Code with the pipeline instructions.

## What happens after the pilot

If you proceed to full implementation, the pilot foundation stays. You switch to a stricter policy pack, enable all CI gates, and customize all templates. Nothing is thrown away.

If you stop after the pilot, you keep everything: CI checks, templates, analysis scripts, and the baseline report. The quality gates continue enforcing standards on every pull request.

## Timeline

| Day | Focus |
| --- | --- |
| 1 | Install pipeline, capture baseline, configure variables |
| 2 | Customize templates, enable core quality gate |
| 3 | Run consolidated report, process with Claude Code |
| 4 | Generate remaining docs, fix quality issues |
| 5 | Final measurement, team training, handoff |

## Next step

Book a 15-20 minute discovery call to confirm fit, repository prerequisites, and pilot success criteria before kickoff.

## Related guides

| Guide | What it covers |
| --- | --- |
| `PILOT_START_HERE.md` | Step-by-step self-serve pilot instructions |
| `PILOT_VS_FULL_IMPLEMENTATION.md` | Comparison of pilot vs full rollout |
| `PRICING_STRATEGY_REVISED.md` | Pricing model and packages |

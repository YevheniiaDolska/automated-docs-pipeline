# Pilot week offer

## What the pilot week is

The pilot week is a 5-day engagement that installs the Auto-Doc Pipeline on your real repository and proves it works with your actual documentation. At the end of the week, you have a functioning documentation quality system, a baseline health report, and a clear roadmap for what to do next.

This is not a demo or a proof of concept. The pilot installs real CI checks, runs real analysis scripts, and delivers real data about your documentation quality.

## Why this pilot is different

Most documentation pilots show a single feature. This pilot validates a complete operating model in 5 days:

1. **Automated quality enforcement.** CI checks block pull requests that do not meet documentation standards.
1. **Automated work detection.** Gap and staleness scanners find documentation that is missing, outdated, or incomplete.
1. **SEO/GEO discoverability checks.** 60+ automated checks ensure documentation is findable by search engines and AI systems.
1. **Standardized content creation.** Templates and snippets ensure every new document follows the same structure.
1. **Execution roadmap.** A 30/60/90-day plan shows what to do after the pilot ends.

## Day-by-day scope

### Day 1: foundation setup

**Goal:** Install the pipeline and capture a baseline measurement of documentation health.

1. Assess the current repository (file count, structure, existing automation).
1. Configure documentation quality gates in CI (markdownlint, frontmatter, SEO/GEO, smoke tests).
1. Run initial validation to capture the baseline score.
1. Align formatting standards with the team (style rules, frontmatter schema).

### Day 2: quality and authoring system

**Goal:** Set up the content creation workflow so the team can write documentation that passes all checks.

1. Adapt templates and snippets to the product's content model.
1. Validate frontmatter and metadata conventions against the team's existing patterns.
1. Test the authoring flow with 2-3 sample pages written by team members.
1. Fix any issues found during the test.

### Day 3: multi-source analysis

**Goal:** Run the analysis scripts on real documentation to find gaps, stale content, and SEO/GEO issues.

1. Run gap detection (`python3 scripts/gap_detector.py`).
1. Run SEO/GEO analysis (`python3 scripts/seo_geo_optimizer.py docs/`).
1. Run pilot analysis (`python3 scripts/pilot_analysis.py`).
1. Compile results into the pilot report.

### Day 4: full-system demonstration

**Goal:** Show the entire system working end-to-end and enable the team to use it independently.

1. Walk through the integrated workflow: code change, documentation update, CI check, merge.
1. Review findings from day 3: gaps, stale pages, SEO/GEO issues, prioritized actions.
1. Conduct a team enablement session (60-90 minutes) covering daily usage, CI gates, and troubleshooting.

### Day 5: handoff and roadmap

**Goal:** Deliver all artifacts and a clear plan for what comes next.

1. Deliver the 30/60/90-day execution plan.
1. Deliver the full implementation proposal with phased options.
1. Deliver governance recommendations and KPI definitions.
1. Answer remaining questions.

## Deliverables

At the end of the pilot week, the following artifacts are delivered:

| Deliverable | Format | Description |
| --- | --- | --- |
| Quality gate foundation | CI config files | Working CI checks in the repository |
| Baseline health report | Markdown or HTML | Current quality score, stale %, gap count |
| Prioritized action list | Markdown | Issues ranked by impact, from analysis output |
| Adapted template set | Markdown files | At least 5 templates customized for the product |
| Team handoff notes | Markdown | Usage instructions, troubleshooting, contacts |
| Implementation roadmap | Markdown | 30/60/90-day plan with scope and sequencing |

## Definition of done

The pilot is considered complete when all of the following criteria are met.

### Technical acceptance criteria

1. Quality gates are active in the repository: markdownlint, frontmatter validation, SEO/GEO checks, and code example smoke tests.
1. CI checks run automatically on every pull request.
1. Core analysis scripts run successfully on the repository's documentation:
   - `python3 scripts/gap_detector.py`
   - `python3 scripts/pilot_analysis.py`
   - `python3 scripts/seo_geo_optimizer.py docs/`
1. At least 5 adapted templates are delivered and tested by the team.

### Business acceptance criteria

1. A written baseline report is delivered with current issues and prioritized fixes.
1. A before/after KPI snapshot is delivered (quality score, metadata coverage, stale docs count).
1. A 30/60/90-day roadmap is delivered with scope and sequencing.
1. One live enablement session is completed with Q&A.

## KPI framework

The pilot tracks these metrics at baseline and at the end of the week:

| Metric | What it measures |
| --- | --- |
| Documentation quality pass rate | Percentage of documents that pass all CI checks |
| Metadata completeness | Percentage of documents with valid frontmatter |
| High-priority gap count | Number of gaps detected with priority "high" |
| Stale documentation percentage | Percentage of documents not updated in 90+ days |
| Search readiness score | SEO/GEO check pass rate |

## What happens after the pilot

If you continue to full implementation, the full rollout builds on the exact foundation installed during the pilot. Nothing is thrown away. See `PILOT_VS_FULL_IMPLEMENTATION.md` for the differences.

If you stop after the pilot, you keep everything that was installed: CI checks, templates, analysis scripts, and the baseline report. The system continues to enforce quality on every pull request.

## Commercial positioning

The pilot week is the low-risk way to validate whether this operating model should become your long-term documentation system. The investment is 5 days. The output is a working system, not a slide deck.

## Next step

Book a 15-20 minute discovery call. The call confirms fit, repository prerequisites, and pilot success criteria before kickoff.

## Related guides

| Guide | What it covers |
| --- | --- |
| `PILOT_VS_FULL_IMPLEMENTATION.md` | Differences between pilot and full rollout |
| `CUSTOMIZATION_PER_COMPANY.md` | Per-company configuration steps |
| `OPERATOR_RUNBOOK.md` | Delivery execution for the person running the pilot |
| `PRICING_STRATEGY_REVISED.md` | Pricing model and packages |

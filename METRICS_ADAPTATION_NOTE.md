# How AI adapts metrics in documentation

## The problem

Documentation templates contain placeholder values for metrics such as response times, uptime percentages, and cost savings. If an AI agent fills in these placeholders with invented numbers, the documentation becomes dishonest. Readers lose trust. Sales teams make promises the product cannot keep.

This guide defines the rules that AI agents (Claude Code, Codex, or any future agent) must follow when replacing metric placeholders in templates.

## Measurement model

Every business or performance claim in documentation must use one of these 3 labels:

| Label | Definition | Requirements |
| --- | --- | --- |
| **Measured** | Computed from real data | Must include timestamped window and data source |
| **Target** | A planned objective | Must include due date and owner |
| **Hypothesis** | An estimate pending validation | Must include confidence level and validation plan |

Use this structure when documenting any metric:

```markdown
Metric: <name>
Type: Measured | Target | Hypothesis
Formula: <explicit formula>
Window: <date range>
Source: <report or system>
Baseline: <value and date>
Current: <value and date>
Target: <value and deadline>
Confidence: High | Medium | Low
```

## Standard formulas

These formulas define how specific metrics are calculated across all documentation:

| Metric | Formula |
| --- | --- |
| Time-to-doc | `docs_merged_at - code_merged_at` (hours) |
| Stale percent | `(stale_docs / total_docs) * 100` |
| High-priority gap count | `count(gaps where priority == "high")` |
| Docs quality score | Weighted composite from metadata completeness, stale ratio, and gap pressure |
| Estimated annual savings (Hypothesis) | `(hours_saved_per_month * loaded_hourly_rate * 12) - annual_tooling_cost` |

## How the AI agent must handle metrics

### When real metrics are available

If the repository, monitoring system, or analytics dashboard provides actual data, the AI agent must use that data and cite the source:

```markdown
# Good: uses real data with source
Response time: 45 ms average (P50), 189 ms P99 (measured over 30 days, source: Datadog)
Uptime: 99.97% (measured January 1 to March 31, 2025, source: internal monitoring)
```

### When metrics are unknown (new project)

If no real data exists, the AI agent must clearly label the value as a target, industry standard, or estimate:

```markdown
# Good: clearly labeled as target
Target: >99.9% success rate (to be measured after deployment)

# Good: references industry standard
Industry standard: 99.95% uptime for critical services (source: Cloud provider SLAs)

# Good: estimate with basis
Expected: ~50 ms latency (based on Node.js + PostgreSQL typical performance)

# Good: placeholder for future measurement
Success rate: [to be measured after deployment]
```

### When making comparisons

If the template asks for a comparison (for example, "X times faster"), the AI agent must provide the actual numbers:

```markdown
# Good: shows both numbers
2.3x faster than v1.0 (measured: 450 ms reduced to 195 ms)

# Good: labeled as expected
Expected: 3-5x faster with caching enabled (to be validated in load testing)

# Good: references similar systems
Similar implementations show 2-4x improvement (source: published benchmarks)
```

## What the AI agent must never do

These patterns are prohibited:

```markdown
# Bad: specific number without source
Handles 1 million requests per second

# Bad: guarantee without SLA
99.999% uptime guaranteed

# Bad: number without context
45 ms response time

# Bad: cost claim without formula
Saves $10,000 per month
```

Every number must have either a source (for measured values), a label (for targets), or a confidence level (for hypotheses).

## Key principles

1. **Be honest.** If you do not have metrics, say so. "To be measured after deployment" is better than an invented number.
1. **Use targets for new projects.** Write "Target: X" or "Goal: Y" instead of stating unproven values as facts.
1. **Reference sources.** Use phrases like "based on," "measured by," and "according to."
1. **Use industry standards when available.** Published benchmarks from reputable sources are acceptable references.
1. **Prefer ranges over absolute values.** "10-50 ms" is more honest than "23 ms" when you do not have precise data.
1. **Label estimates clearly.** Use words like "estimated," "expected," and "typical" so readers know the value is not measured.

## Template placeholders

Templates in the `templates/` directory use these placeholders that the AI agent must replace:

| Placeholder | Meaning |
| --- | --- |
| `[X]` | A numeric value |
| `[metric]` | A specific metric name |
| `[measured]` | An actual measured value, or "to be measured" if unavailable |
| `[target]` | A target or goal value |
| `[estimate]` | An estimated value based on context |

The AI agent must:

1. Replace the placeholder with real data when available.
1. Use industry standards when real data is not available.
1. Clearly mark estimates and targets with labels.
1. Add measurement placeholders for future data collection.
1. Never invent specific numbers without a documented basis.

## Related guides

| Guide | What it covers |
| --- | --- |
| `CLAUDE.md` | AI agent instructions including self-verification rules |
| `AGENTS.md` | Codex agent instructions including fact-checking rules |
| `POLICY_PACKS.md` | Quality thresholds that metrics must meet |

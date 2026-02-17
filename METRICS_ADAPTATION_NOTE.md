# How Claude Code Adapts Metrics in Templates

## The Problem with Fake Metrics

Templates should NOT contain made-up numbers. Claude Code will adapt based on context:

## Adaptation Strategy

### 1. When Real Metrics Are Available

```markdown
# Template says: "[X]ms response time"

# Claude Code will write:
- If metrics exist: "45ms average response time (P50), 189ms P99 (measured over 30 days)"
- If from monitoring: "Response time: 45-67ms (Datadog metrics, last 7 days)"
- If from benchmarks: "Benchmark results: 52ms under normal load (1000 req/s)"
```

### 2. When Metrics Are Unknown (New Project)

```markdown
# Template says: "[X]% success rate"

# Claude Code will write:
- Target/Goal: "Target: >99.9% success rate"
- Industry standard: "Industry standard: 99.95% uptime for critical services"
- Estimate based on stack: "Expected: ~50ms latency (based on Node.js + PostgreSQL typical performance)"
- Placeholder for measurement: "Success rate: [to be measured after deployment]"
```

### 3. When Making Comparisons

```markdown
# Template says: "[X]x faster"

# Claude Code will write:
- If comparing versions: "2.3x faster than v1.0 (measured: 450ms → 195ms)"
- If theoretical: "Expected: 3-5x faster with caching enabled"
- If based on similar systems: "Similar implementations show 2-4x improvement"
```

## Examples of Proper Adaptation

### Good (Honest) Adaptations

```markdown
✅ "Target response time: <100ms (to be validated in load testing)"
✅ "Based on similar deployments, expect 10-50 requests/second"
✅ "Estimated cost: $50-200/month depending on usage"
✅ "Industry benchmark: 45ms P50 for similar APIs"
```

### Bad (Dishonest) Adaptations

```markdown
❌ "Handles 1 million requests/second" (unless actually tested)
❌ "99.999% uptime guaranteed" (unless SLA exists)
❌ "45ms response time" (without context/source)
❌ "Saves $10,000/month" (without basis)
```

## Key Principles

1. **Be Honest**: If you don't have metrics, say so
1. **Use Targets**: "Target: X" or "Goal: Y" for new projects
1. **Reference Sources**: "Based on," "Measured by," "According to"
1. **Industry Standards**: Use well-known benchmarks as references
1. **Ranges Over Absolutes**: "10-50 ms" is better than "23 ms" without data
1. **Clear About Estimates**: Use terms like estimated, expected, and typical

## Template Placeholders

Templates use these placeholders that Claude Code will replace:

- `[X]` - Numeric value
- `[metric]` - Specific metric name
- `[measured]` - Actual measured value or "to be measured"
- `[target]` - Target/goal value
- `[estimate]` - Estimated value based on context

Claude Code will:

- Replace with real data when available
- Use industry standards when applicable
- Clearly mark estimates and targets
- Add measurement placeholders for future data collection
- Never invent specific numbers without basis

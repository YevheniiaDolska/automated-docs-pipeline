---
title: "Testing guide"
description: "Test [Product] integrations across unit, integration, contract, and end-to-end layers with deterministic fixtures and failure-path coverage."
content_type: how-to
product: both
tags:
  - How-To
  - Performance
  - API
---

# Testing guide

Use this guide to build confidence before production rollout and after every release.

## Test strategy (pyramid)

| Layer | Goal | Typical runtime |
| --- | --- | --- |
| Unit | Validate business logic in isolation | seconds |
| Integration | Validate API/DB and SDK interactions | minutes |
| Contract | Prevent schema drift | minutes |
| End-to-end | Validate full user journey | longer-running |

## Environment model

- `local`: fast feedback with mocks and fixtures
- `staging`: production-like dependencies
- `production`: smoke tests only, no destructive flows

## Unit tests (with deterministic mocks)

```javascript
import { describe, it, expect, vi } from 'vitest';

const client = {
  projects: {
    create: vi.fn()
  }
};

it('creates project with normalized payload', async () => {
  client.projects.create.mockResolvedValue({ id: 'prj_1' });

  const result = await createProject(client, { name: ' Ops ' });

  expect(client.projects.create).toHaveBeenCalledWith({ name: 'Ops' });
  expect(result.id).toBe('prj_1');
});
```

## Integration tests

Validate:

- Authentication and token refresh
- Retry behavior on transient failures
- Idempotency for retried writes
- Pagination correctness

## Webhook tests

- Signature verification with valid and invalid secrets
- Replay attack prevention
- Idempotent event processing
- Dead-letter behavior for repeated failures

## Contract tests

Use schema snapshots to catch breaking API changes.

```yaml
# example assertion targets
response.required:
  - id
  - status
  - created_at
```

## Failure injection

Simulate:

- `429` rate limit responses
- `500/503` upstream failures
- slow network and timeout scenarios
- malformed webhook payloads

## CI quality gates

- [ ] All tests pass
- [ ] Coverage threshold met (`line`, `branch`)
- [ ] No flaky tests in last N runs
- [ ] Critical path e2e green

## Metrics for test quality

- Mean test duration
- Flake rate by suite
- Escaped defects by release
- Time to detect regressions

## Adaptation notes for template users

Replace resource names, fixture payloads, and failure thresholds with your domain values.

## Related docs

- `templates/integration-guide.md`
- `templates/error-handling-guide.md`
- `templates/security-guide.md`

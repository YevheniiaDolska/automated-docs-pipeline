---
title: "Intent experience: automate for developer"
description: "Assembled guidance for one intent and audience using reusable knowledge modules with verified metadata and channel-ready sections."
content_type: reference
product: both
tags:
  - Reference
  - AI
---

# Intent experience: automate for developer

This page is assembled for the `automate` intent and the `developer` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent automate --audience developer --channel docs
```

## Included modules

### Define idempotent webhook retry handling

Provides retry and idempotency patterns to avoid duplicate processing across documentation, assistant guidance, and runbook automation.

Use idempotency keys to make webhook retries safe. Persist a processed-event key for at least 24 hours, and skip duplicate events with HTTP 200 to stop upstream retries. Use exponential backoff for outbound retries: one second, two seconds, four seconds, eight seconds, and 16 seconds, capped at five attempts.

```javascript
const retryScheduleSeconds = [1, 2, 4, 8, 16];

function shouldProcess(eventId, cache) {
  if (cache.has(eventId)) {
    return false;
  }
  cache.add(eventId);
  return true;
}
```

Alert when retry rate exceeds 5% for 15 minutes. This threshold usually indicates downstream instability.

## Next steps

- Validate modules: `npm run lint:knowledge`
- Rebuild retrieval index: `npm run build:knowledge-index`
- Generate assistant pack: `npm run build:intent -- --channel assistant`

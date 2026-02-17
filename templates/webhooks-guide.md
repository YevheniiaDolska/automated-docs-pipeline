---
title: "Webhooks guide"
description: "Implement reliable and secure webhook handling for [Product]: endpoint setup, signature verification, idempotency, retries, and observability."
content_type: how-to
product: both
tags:
  - How-To
  - Integration
  - Security
---

# Webhooks guide

Webhooks let [Product] push event updates to your system in near real time. This guide focuses on correctness under retries, duplicates, and transient failures.

## Quick setup

```javascript
app.post('/webhooks/product', rawBodyMiddleware, async (req, res) => {
  if (!verifySignature(req.rawBody, req.headers['x-product-signature'])) {
    return res.status(400).send('invalid signature');
  }

  res.status(200).send('ok');
  await queueEvent(JSON.parse(req.rawBody));
});
```

## Delivery model

Expect at-least-once delivery:

- Events may be retried.
- Events may arrive out of order.
- Duplicate deliveries are normal.

## Register endpoint

1. Configure HTTPS endpoint.
1. Subscribe to minimal required event set.
1. Store webhook signing secret in secret manager.
1. Document owner and rotation schedule.

## Signature verification

```javascript
import crypto from 'node:crypto';

function verifySignature(rawBody, header, secret) {
  const [tPart, v1Part] = String(header || '').split(',');
  const timestamp = tPart?.split('=')[1];
  const signature = v1Part?.split('=')[1];

  if (!timestamp || !signature) return false;

  const ageSeconds = Math.abs(Date.now() / 1000 - Number(timestamp));
  if (ageSeconds > 300) return false;

  const payload = `${timestamp}.${rawBody}`;
  const expected = crypto.createHmac('sha256', secret).update(payload).digest('hex');

  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}
```

## Idempotent processing

Use event ID as idempotency key.

```sql
CREATE TABLE webhook_events (
  event_id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  received_at TIMESTAMP NOT NULL,
  processed_at TIMESTAMP NULL
);
```

Processing pattern:

1. Insert event ID if not exists.
1. If exists, skip side effects.
1. Mark processed on successful completion.

## Event routing pattern

```javascript
async function processEvent(event) {
  switch (event.type) {
    case 'project.created':
      return handleProjectCreated(event.data);
    case 'run.failed':
      return handleRunFailed(event.data);
    default:
      return null;
  }
}
```

## Retry and dead-letter strategy

- Retry transient failures with backoff.
- Send permanently failing events to dead-letter queue.
- Add replay endpoint for controlled reprocessing.

## Observability

Track:

- webhook delivery success rate
- signature verification failures
- end-to-end processing latency
- dead-letter volume

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `400 invalid signature` | Wrong secret or raw body modified | Use raw body and correct secret |
| Repeated duplicates | Retries after timeout | Acknowledge quickly, process async |
| Missing events | Subscriptions too narrow | Add required event types |

## Adaptation notes for template users

Replace event names and payload fields with your product model. Keep idempotency and signature sections unchanged in principle.

## Related docs

- `templates/security-guide.md`
- `templates/error-handling-guide.md`
- `templates/integration-guide.md`

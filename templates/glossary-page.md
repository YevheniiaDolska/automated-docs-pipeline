---
title: "[Product] glossary"
description: "Definitions for key terms used across [Product] documentation, APIs, security controls, and operations."
content_type: reference
product: both
tags:
  - Reference
---

# [Product] glossary

Use this glossary to normalize terminology across docs, APIs, and support conversations.

## Editorial rules

- Keep each definition short and concrete.
- Define the term, then explain why it matters.
- Link to one canonical deep-dive page.
- Avoid circular definitions.

## A

### Access token

Short-lived credential used to authorize API requests. Usually issued by OAuth and scoped to specific permissions.

### API key

Long-lived secret used for server-side authentication. Never expose in browser or mobile client code.

## C

### Client credentials flow

OAuth 2.0 flow where one service authenticates directly without user interaction.

### Concurrency limit

Maximum number of simultaneous requests/jobs allowed per account or endpoint.

## I

### Idempotency key

Unique key attached to write requests to prevent duplicate execution during retries.

### Integration

A configured connection between [Product] and an external system or service.

## P

### Pagination cursor

Opaque token used to request the next page of data without offset-based drift.

### Principle of least privilege

Security practice of granting only the permissions required to complete a task.

## R

### Rate limit

Maximum request volume allowed in a time window. Exceeding the limit typically returns `429`.

### Request ID

Unique identifier attached to API responses for troubleshooting and support.

## S

### Scope

Named permission included in credentials, such as `projects:read`.

### Signature verification

Validation that a webhook payload was sent by a trusted source and was not altered.

## T

### Time to first success (TTFS)

Elapsed time between starting integration and first successful end-to-end operation.

## Glossary maintenance checklist

- [ ] New terms from release notes are added.
- [ ] Definitions use current product behavior.
- [ ] Cross-links point to non-deprecated pages.

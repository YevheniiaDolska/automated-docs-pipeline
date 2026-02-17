---
title: "[Product] FAQ"
description: "Frequently asked questions about [Product], including setup, pricing model, limits, security, migration, and troubleshooting."
content_type: reference
product: both
tags:
  - Reference
---

# [Product] FAQ

Use this template for concise, high-signal answers to real user questions.

## FAQ writing rules

- Lead with the direct answer in one sentence.
- Add one short paragraph for context.
- Link to one deeper doc for implementation detail.
- Keep each answer under 120 words unless complexity requires more.

## Getting started

### What is [Product]?

[Product] is [one-sentence value proposition]. It helps [target persona] achieve [specific outcome].

### Who is [Product] for?

[Product] is designed for:

- [Persona 1] who need [capability]
- [Persona 2] who optimize [metric]
- [Persona 3] integrating [system type]

### How long does setup take?

Most teams reach first successful request in [X] minutes and production rollout in [Y] days.

## Product and platform

### Does [Product] support [feature]?

Yes/No. [Clarify availability by plan/region/version].

### Which languages and SDKs are supported?

List official SDKs and minimum runtime versions.

### What are the API limits?

State default limits and link to rate-limit reference page.

## Security and compliance

### How is data protected?

Describe encryption in transit and at rest, key controls, and access model.

### Which compliance standards are supported?

List concrete standards and scope. Avoid vague claims.

### Can we use customer-managed keys?

Explain whether supported and any plan prerequisites.

## Billing and operations

### How does pricing work?

State pricing dimensions (for example: requests, seats, storage) and where usage is visible.

### How do we cancel or downgrade?

Give exact UI/API steps and effective date behavior.

### Is there an SLA?

State SLA target and where incident history/status is published.

## Troubleshooting

### Why do I get `401 Unauthorized`?

Most common causes are missing token, expired token, or wrong environment key. Validate credentials and scopes.

### Why do webhooks fail?

Typical causes are signature mismatch, timeout, or non-2xx response. Verify secret and return `200` quickly before async processing.

## Escalation path

If the FAQ answer is insufficient, include:

- Link to deep-dive documentation
- Support contact and required diagnostic data (`request_id`, timestamp, region)

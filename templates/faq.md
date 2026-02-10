---
title: "[Product] FAQ"
description: "Frequently asked questions about [Product]. Find answers to common questions about pricing, features, limits, security, and troubleshooting."
content_type: reference
product: both
tags:
  - Reference
---

# Frequently asked questions

Quick answers to common questions about [Product].

## General

### What is [Product]?

[Product] is [one-sentence description of what it does and its primary value proposition].

### Who is [Product] for?

[Product] is designed for:

- [Target user 1] who need [capability]
- [Target user 2] looking to [goal]
- [Target user 3] building [type of application]

### How does [Product] compare to [Competitor]?

| Feature | [Product] | [Competitor] |
|---------|-----------|--------------|
| [Feature 1] | [Comparison] | [Comparison] |
| [Feature 2] | [Comparison] | [Comparison] |
| Pricing | [Info] | [Info] |

See our detailed [comparison guide](./comparisons/vs-competitor.md).

## Pricing & billing

### How much does [Product] cost?

| Plan | Price | Includes |
|------|-------|----------|
| Free | $0/month | [Limits] |
| Pro | $[X]/month | [Limits] |
| Enterprise | Custom | [Features] |

See [pricing page]([URL]) for full details.

### Is there a free trial?

Yes, [Product] offers [X]-day free trial of the Pro plan. No credit card required.

### What payment methods do you accept?

- Credit/debit cards (Visa, Mastercard, Amex)
- [Other methods]

### How do I cancel my subscription?

1. Go to [Dashboard]([URL]) → Settings → Billing
2. Click **Cancel subscription**
3. Confirm cancellation

Your access continues until the end of the billing period.

### Do you offer refunds?

[Refund policy description]

## Features

### What are the API rate limits?

| Plan | Requests/minute | Requests/day |
|------|-----------------|--------------|
| Free | [X] | [X] |
| Pro | [X] | [X] |
| Enterprise | Custom | Custom |

See [rate limits documentation](../reference/rate-limits.md).

### What programming languages are supported?

We provide official SDKs for:

- JavaScript/TypeScript
- Python
- [Other languages]

You can also use the [REST API](../reference/api.md) with any language.

### Does [Product] support [specific feature]?

Yes/No. [Brief explanation].

See [feature documentation](../how-to/feature.md) for details.

### What integrations are available?

[Product] integrates with:

- [Integration 1]
- [Integration 2]
- [Integration 3]

See [full integrations list](../reference/integrations.md).

## Security

### Is [Product] secure?

Yes. [Product] implements:

- [Security measure 1]
- [Security measure 2]
- [Compliance certifications]

See our [security overview](./security.md).

### Is [Product] SOC 2 / GDPR / HIPAA compliant?

- **SOC 2:** [Status]
- **GDPR:** [Status]
- **HIPAA:** [Status]

Contact [sales email] for compliance documentation.

### How is my data protected?

- Data encrypted at rest (AES-256)
- Data encrypted in transit (TLS 1.3)
- [Additional measures]

### Where is my data stored?

Data is stored in [regions/providers]. Enterprise customers can choose data residency.

### Can I export my data?

Yes. Go to [Dashboard]([URL]) → Settings → Export Data, or use the [export API](../reference/api.md#export).

## Account

### How do I reset my password?

1. Go to [login page]([URL])
2. Click **Forgot password**
3. Enter your email
4. Follow the reset link

### Can I change my email address?

Yes. Go to [Dashboard]([URL]) → Settings → Account → Change email.

### How do I delete my account?

1. Go to [Dashboard]([URL]) → Settings → Account
2. Click **Delete account**
3. Confirm deletion

!!! warning "Account deletion is permanent"
    All data will be permanently deleted within 30 days.

### How do I add team members?

1. Go to [Dashboard]([URL]) → Team
2. Click **Invite member**
3. Enter their email and role

See [team management guide](../how-to/team.md).

## Troubleshooting

### Why am I getting a 401 error?

A 401 error means your API key is invalid or expired.

**Fix:**
1. Check you're using the correct API key
2. Verify you're using the right environment (test vs. live)
3. [Generate a new key]([URL]) if needed

### Why am I getting rate limited?

You've exceeded the [rate limits](#what-are-the-api-rate-limits) for your plan.

**Fix:**
1. Implement [exponential backoff](../how-to/error-handling.md#retry-strategies)
2. Cache responses where possible
3. Consider upgrading your plan

### My webhook isn't receiving events

Common causes:

1. **Incorrect URL:** Ensure HTTPS and publicly accessible
2. **Firewall:** Allow [Product] IP ranges
3. **Signature verification failing:** Check webhook secret

See [webhook troubleshooting](../troubleshooting/webhooks.md).

### How do I contact support?

| Channel | Response time | Best for |
|---------|---------------|----------|
| [Help center]([URL]) | Self-service | Common questions |
| Email: [support email] | 24 hours | Account issues |
| [Community forum]([URL]) | Varies | Technical questions |
| [Priority support]([URL]) | 4 hours | Enterprise plans |

## Technical

### What's the API uptime SLA?

| Plan | Uptime SLA |
|------|------------|
| Free | No SLA |
| Pro | 99.9% |
| Enterprise | 99.99% |

See [status page]([URL]) for current status.

### What happens during planned maintenance?

- Announced [X] days in advance via [email/status page]
- API remains available (no downtime)
- [Any specific impacts]

### How do I test the integration?

Use the sandbox/test environment:

```javascript
const client = new [Product]Client({
  apiKey: 'sk_test_...', // Test key
  environment: 'test'
});
```

See [testing guide](../how-to/testing.md).

### Do you have a status page?

Yes: [status.product.com]([URL])

Subscribe to receive incident notifications.

## Didn't find your answer?

- Search our [documentation](../index.md)
- Ask in the [community forum]([URL])
- Contact [support]([URL])

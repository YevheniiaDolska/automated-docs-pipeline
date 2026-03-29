---
title: "VeriDoc privacy policy"
description: "Privacy policy for VeriDoc automated documentation platform, covering data collection, processing, storage, retention, and your rights under GDPR."
content_type: reference
product: cloud
tags:
  - Reference
last_reviewed: "2026-03-28"
---

# VeriDoc privacy policy

This privacy policy explains how Liora Tech ("Company," "we," "us")
collects, uses, and protects your personal data when you use VeriDoc,
an automated documentation pipeline platform. This policy applies to
all users of the VeriDoc web application, API, and CLI tools.

## Data controller

Liora Tech acts as the data controller for personal data collected through
the VeriDoc platform.

| Detail | Value |
|--------|-------|
| **Company** | Liora Tech |
| **Contact email** | <privacy@veri-doc.app> |
| **Data protection inquiries** | <privacy@veri-doc.app> |

## Data we collect

### Account data

When you register, we collect:

| Data field | Purpose | Legal basis |
|------------|---------|-------------|
| Email address | Authentication, billing notifications, support | Contract performance |
| Password hash | Authentication (PBKDF2-SHA256, never stored in plaintext) | Contract performance |
| Subscription tier | Service delivery, usage limit enforcement | Contract performance |
| Billing records | Payment processing, invoice generation | Contract performance |
| Referral code | Referral program tracking | Legitimate interest |

### Usage data

When you use the Service, we automatically collect:

| Data field | Purpose | Retention |
|------------|---------|-----------|
| Pipeline run metadata | Usage tracking, quota enforcement | 90 days |
| API request logs | Rate limiting, debugging, abuse prevention | 30 days |
| Error reports (Sentry) | Bug fixing, reliability improvement | 90 days |
| Authentication tokens | Session management | Token expiry (24 hours) |

### Documentation content

When you process documentation through the pipeline:

1. Your content is processed in memory during pipeline execution.
1. Generated outputs (processed Markdown, reports, knowledge modules) are
   stored in encrypted PostgreSQL databases.
1. We do not read, analyze, or use your documentation content for any
   purpose other than providing the Service.
1. We do not use your content to train machine learning models.

### LLM processing data

When you enable AI features (`--use-llm` flag), your documentation content
is sent to third-party LLM providers for processing:

| Provider | Data sent | Provider privacy policy |
|----------|-----------|------------------------|
| Anthropic (Claude) | Document sections for quality enhancement | [anthropic.com/privacy](https://www.anthropic.com/privacy) |
| Groq | Document sections for text generation | [groq.com/privacy-policy](https://groq.com/privacy-policy/) |
| DeepSeek | Document sections for text generation | [deepseek.com/privacy](https://www.deepseek.com/privacy) |
| OpenAI | Document sections for embeddings and text generation | [openai.com/privacy](https://openai.com/privacy) |

LLM processing is opt-in. Without the AI flag, no content leaves our
infrastructure.

## How we use your data

We use personal data exclusively for:

1. **Service delivery** -- processing your documentation, enforcing usage
   limits, and managing your subscription.
1. **Billing** -- processing payments through LemonSqueezy, generating
   invoices, tracking referral commissions.
1. **Communication** -- sending transactional emails (subscription
   confirmations, trial expiry notices, invoice receipts).
1. **Security** -- detecting unauthorized access, enforcing rate limits,
   monitoring for abuse.
1. **Improvement** -- analyzing aggregate, anonymized usage patterns to
   improve the Service. We never analyze individual content.

## Data storage and security

### Infrastructure

| Component | Location | Encryption |
|-----------|----------|------------|
| Application servers | Hetzner Cloud, Germany | TLS 1.3 in transit |
| PostgreSQL database | Hetzner Cloud, Germany | AES-256 at rest |
| Redis cache | Hetzner Cloud, Germany | In-memory, no persistence of content |
| Backups | Hetzner Cloud, Germany | AES-256, 30-day retention |

### Security measures

1. All API communication uses TLS 1.3 encryption.
1. Passwords are hashed with PBKDF2-SHA256 (600,000 iterations).
1. JWT authentication tokens expire after 24 hours.
1. Database backups run daily with 30-day retention and automated restore
   testing.
1. Error tracking uses Sentry with PII scrubbing enabled.
1. Rate limiting enforces 60 requests per minute per user.

## Data retention

| Data type | Retention period | Deletion trigger |
|-----------|-----------------|------------------|
| Account data | Account lifetime + 30 days | Account closure |
| Billing records | 7 years (legal requirement) | Statutory expiry |
| Pipeline outputs | Account lifetime + 30 days | Account closure |
| API logs | 30 days | Automatic rotation |
| Error reports | 90 days | Automatic rotation |
| Backups | 30 days | Automatic rotation |

After account closure, we retain data for 30 days to allow you to
reactivate or export. After 30 days, all personal data is permanently
deleted.

## Your rights

Under GDPR and applicable data protection laws, you have the right to:

| Right | How to exercise |
|-------|-----------------|
| **Access** your data | Email <privacy@veri-doc.app> or use the API export endpoint |
| **Correct** inaccurate data | Update your profile in account settings |
| **Delete** your data | Close your account or email <privacy@veri-doc.app> |
| **Export** your data | Use the API data export endpoint or email <privacy@veri-doc.app> |
| **Restrict** processing | Email <privacy@veri-doc.app> |
| **Object** to processing | Email <privacy@veri-doc.app> |
| **Withdraw consent** | Disable AI features or close your account |

We respond to data rights requests within 30 days.

## Cookies and tracking

The VeriDoc web application uses only essential cookies for session
management. We do not use:

1. Third-party analytics cookies
1. Advertising cookies
1. Social media tracking pixels
1. Cross-site tracking

## Third-party processors

We share data with these processors solely for service delivery:

| Processor | Purpose | Data shared |
|-----------|---------|-------------|
| LemonSqueezy | Payment processing | Email, subscription tier |
| Hetzner | Infrastructure hosting | Encrypted application data |
| Sentry | Error tracking | Error context (PII scrubbed) |
| Mailgun | Transactional email delivery | Email address, email content |

## Age requirements

VeriDoc is not intended for users under 16 years of age. We do not
knowingly collect data from children.

## Changes to this policy

We notify users of material changes via email 30 days before the effective
date. Minor clarifications are published directly. The "Last updated" date
reflects the most recent revision.

## Contact information

For privacy inquiries or data rights requests:

- Email: <privacy@veri-doc.app>
- Response time: within 30 days

**Last updated:** March 28, 2026

## Next steps

- Review the [terms of service](terms-of-service.md)
- Review the [data processing agreement](data-processing-agreement.md)
- Review the [security policy](security-policy.md)

---
title: "VeriDoc data processing agreement"
description: "Data processing agreement for VeriDoc platform covering GDPR compliance, sub-processors, data transfer mechanisms, and breach notification procedures."
content_type: reference
product: cloud
tags:
  - Reference
last_reviewed: "2026-03-28"
---

# VeriDoc data processing agreement

This data processing agreement ("DPA") forms part of the agreement between
Liora Tech ("Processor," "we") and the entity subscribing to VeriDoc
("Controller," "you") for the processing of personal data through the
VeriDoc platform.

## Scope and roles

| Role | Party | Responsibility |
|------|-------|----------------|
| **Data Controller** | You (the customer) | Determines the purposes and means of processing documentation content |
| **Data Processor** | Liora Tech | Processes personal data on your behalf to provide the VeriDoc Service |
| **Sub-processors** | Third-party providers listed below | Process data under our supervision for specific service functions |

This DPA applies to all personal data processed through the VeriDoc
platform on your behalf, including documentation content that may contain
personal data (names, emails, or identifiers in your documentation).

## Processing details

### Subject matter and duration

We process personal data for the duration of your VeriDoc subscription.
Processing terminates 30 days after account closure, when all data is
permanently deleted.

### Nature and purpose of processing

| Processing activity | Purpose | Data categories |
|---------------------|---------|-----------------|
| Pipeline execution | Transform and enhance documentation | Documentation content, metadata |
| LLM processing (opt-in) | AI-powered quality improvements | Document sections sent to LLM providers |
| Usage tracking | Quota enforcement and billing | Request counts, timestamps |
| Authentication | Access control | Email, hashed passwords, JWT tokens |
| Billing | Payment processing and invoicing | Email, subscription tier, payment history |

### Categories of data subjects

Data subjects include your employees, contractors, and any individuals
whose personal data appears in documentation processed through VeriDoc.

## Processor obligations

We commit to the following obligations:

1. **Process only on your instructions.** We process personal data solely
   to provide the Service as documented in these Terms and this DPA. We do
   not process data for our own purposes.
1. **Confidentiality.** All personnel with access to personal data are
   bound by confidentiality obligations.
1. **Security measures.** We implement technical and organizational
   measures as described in the [security policy](security-policy.md):
   - TLS 1.3 encryption for all data in transit
   - AES-256 encryption for all data at rest
   - PBKDF2-SHA256 password hashing (600,000 iterations)
   - Daily encrypted database backups with 30-day retention
   - Rate limiting (60 requests per minute)
   - Sentry error tracking with PII scrubbing
1. **Sub-processor management.** We maintain an up-to-date list of
   sub-processors and notify you 30 days before adding new ones.
1. **Data subject rights.** We assist you in responding to data subject
   requests (access, deletion, portability) within 10 business days.
1. **Breach notification.** We notify you within 72 hours of discovering
   a personal data breach, with details on the nature, scope, and
   remediation steps.
1. **Audit rights.** You may request an audit of our data processing
   activities once per year with 30 days advance notice.
1. **Data return and deletion.** Upon termination, we return your data
   in a standard format (JSON export) and delete all copies within 30 days.

## Sub-processors

We use the following sub-processors:

| Sub-processor | Purpose | Location | Data processed |
|---------------|---------|----------|----------------|
| Hetzner Online | Cloud infrastructure hosting | Germany (EU) | All application data (encrypted) |
| LemonSqueezy | Payment processing | United States | Email, subscription tier |
| Mailgun | Transactional email delivery | United States | Email address, email content |
| Sentry | Error monitoring | United States | Error context (PII scrubbed) |

### Optional LLM sub-processors (opt-in only)

These sub-processors are engaged only when you explicitly enable AI
features:

| Sub-processor | Purpose | Location | Data processed |
|---------------|---------|----------|----------------|
| Anthropic | Document quality enhancement | United States | Document sections |
| Groq | Text generation | United States | Document sections |
| DeepSeek | Text generation | China | Document sections |
| OpenAI | Embeddings, text generation | United States | Document sections |

You control which LLM providers are used through your pipeline
configuration. Disable AI features to prevent any content from reaching
LLM sub-processors.

## Data transfers

### EU-US transfers

For sub-processors located in the United States, we rely on:

1. Standard Contractual Clauses (SCCs) approved by the European Commission
   (June 2021 version).
1. Supplementary measures including encryption in transit and at rest.
1. Data minimization -- only the minimum data necessary is transferred.

### Transfer impact assessment

We have conducted transfer impact assessments for each non-EU
sub-processor. Assessments are available upon request at
<privacy@veri-doc.app>.

## Data breach notification

In the event of a personal data breach:

| Step | Timeline | Action |
|------|----------|--------|
| 1 | Within 24 hours | Internal incident response team activated |
| 2 | Within 72 hours | Written notification to you with breach details |
| 3 | Within 72 hours | Notification to supervisory authority (if required) |
| 4 | Ongoing | Regular updates on investigation and remediation |

Breach notification includes:

1. Nature of the breach and categories of data affected.
1. Estimated number of data subjects affected.
1. Likely consequences of the breach.
1. Measures taken to address and mitigate the breach.

## Data protection impact assessment

We support your data protection impact assessments (DPIAs) by providing:

1. Documentation of processing activities.
1. Technical details of security measures.
1. Sub-processor information and transfer mechanisms.

Request DPIA support materials at <privacy@veri-doc.app>.

## Term and termination

This DPA remains in effect for the duration of your VeriDoc subscription.
Upon termination:

1. We stop processing personal data within 24 hours.
1. We provide a JSON data export within 7 business days upon request.
1. We permanently delete all personal data within 30 days.
1. We confirm deletion in writing.

## Contact information

For DPA inquiries:

- Email: <privacy@veri-doc.app>
- Response time: within 10 business days

**Last updated:** March 28, 2026

## Next steps

- Review the [terms of service](terms-of-service.md)
- Review the [privacy policy](privacy-policy.md)
- Review the [security policy](security-policy.md)

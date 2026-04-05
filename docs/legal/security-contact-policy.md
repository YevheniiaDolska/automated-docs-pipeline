---
title: VeriDoc security contact policy
description: Security contact channels, response times, severity model, and disclosure
  workflow for VeriDoc incidents and vulnerability reports.
content_type: reference
product: cloud
tags:
- Reference
- Legal
last_reviewed: '2026-03-31'
original_author: Kroha
---


# VeriDoc security contact policy

This policy defines exactly how to contact VeriDoc for security incidents,
vulnerability reports, and urgent abuse cases.

## Official contact channels

| Purpose | Channel | Target response |
|---------|---------|-----------------|
| Vulnerability disclosure | <security@veri-doc.app> | Within 24 hours |
| Incident escalation (active outage or suspected compromise) | <security@veri-doc.app> + <support@veri-doc.app> | Within 1 hour |
| Privacy and data-protection issues | <privacy@veri-doc.app> | Within 72 hours |

## What to include in your report

Send a concise report with:

1. Affected endpoint, system, or feature.
1. Exact reproduction steps.
1. Expected result and actual result.
1. Scope estimate (single tenant, multi-tenant, or unknown).
1. Any logs, timestamps, and request IDs.

## Severity model and SLA

| Severity | Typical examples | First response | Containment target |
|----------|------------------|----------------|--------------------|
| Critical | Data exposure, account takeover, production compromise | 1 hour | 4 hours |
| High | Auth bypass, privilege escalation, sustained API failure | 4 hours | 12 hours |
| Medium | Non-critical security misconfiguration | 24 hours | 3 business days |
| Low | Hardening recommendations, low-risk findings | 72 hours | Planned release |

## Disclosure rules

For responsible disclosure:

1. Do not access data that is not yours.
1. Do not modify or delete customer data.
1. Do not run denial-of-service tests.
1. Give VeriDoc up to 90 days before public disclosure.

## Communication and status updates

For confirmed incidents:

1. Initial acknowledgement is sent via email.
1. Ongoing updates are provided at least every 24 hours for critical incidents.
1. Final post-incident summary includes root cause and corrective actions.

## Next steps

- Review the [security policy](security-policy.md)
- Review the [data processing agreement](data-processing-agreement.md)
- Review the [privacy policy](privacy-policy.md)

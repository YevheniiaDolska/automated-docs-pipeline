---
title: "Master Services Agreement Template"
description: "Master template used to generate Pilot, Full, and Full+RAG implementation agreements."
content_type: reference
product: both
last_reviewed: "2026-04-28"
tags:
  - Legal
  - Template
---

# {{AGREEMENT_NAME}}

This Agreement is entered into as of **{{EFFECTIVE_DATE}}** ("Effective Date") by and between:

- **Provider:** {{PROVIDER_LEGAL_NAME}}, a {{PROVIDER_ENTITY_TYPE}} registered under the laws of {{PROVIDER_JURISDICTION}}, with principal address at {{PROVIDER_ADDRESS}}.
- **Client:** {{CLIENT_LEGAL_NAME}}, a {{CLIENT_ENTITY_TYPE}} organized under the laws of {{CLIENT_JURISDICTION}}, with principal address at {{CLIENT_ADDRESS}}.

The Provider and the Client are each a "Party" and together the "Parties."

## 1. Services scope

Provider will deliver: **{{PROJECT_SCOPE}}**

For pilot engagements (where applicable), repository scope is:
- `{{REPOSITORY_IDENTIFIER}}`
- Pilot dates: `{{PILOT_START_DATE}}` through `{{PILOT_END_DATE}}`

## 2. Commercial terms

1. Agreement fee: **USD ${{TOTAL_FEE_USD}}**.
2. Payment terms: {{PAYMENT_TERMS}}
3. Pricing reference:
   - Pilot: USD ${{PILOT_PRICE_USD}}
   - Full: USD ${{FULL_PRICE_USD}}
   - RAG add-on: USD ${{RAG_ADDON_PRICE_USD}}
   - Full+RAG total: USD ${{FULL_RAG_PRICE_USD}}
4. Pilot credit policy:
   - If Client buys Full or Full+RAG within `{{CREDIT_VALIDITY_DAYS}}` days after pilot completion, paid pilot fee is credited.
   - Full after pilot: USD ${{FULL_AFTER_PILOT_USD}}
   - Full+RAG after pilot: USD ${{FULL_RAG_AFTER_PILOT_USD}}

## 3. Retainer terms

1. Retainer mode: `{{RETAINER_ENABLED}}`.
2. Monthly retainer fee: **USD ${{RETAINER_MONTHLY_USD}}** payable in advance.
3. Included monthly capacity: `{{RETAINER_INCLUDED_HOURS}}` hours.
4. Overage rate (above included capacity): **USD ${{RETAINER_OVERAGE_USD_PER_HOUR}} / hour**.
5. Scope covered by retainer: {{RETAINER_SCOPE}}
6. Response window target: {{RETAINER_RESPONSE_SLA}}
7. Unused hours policy: {{RETAINER_ROLLOVER_POLICY}}
8. If payment is overdue by more than `{{RETAINER_OVERDUE_SUSPEND_DAYS}}` days, Provider may suspend services until account is current.
9. Either Party may terminate the retainer with `{{RETAINER_TERMINATION_NOTICE_DAYS}}` days written notice (implementation work already accepted remains payable).
10. If retainer is not paid, not renewed, or is terminated, Provider may downgrade runtime entitlement to `community` mode after written notice and grace period of `{{RETAINER_DEGRADE_GRACE_DAYS}}` days.
11. Community mode includes only:
    - Markdown/content hygiene defaults (normalization and snippet checks).
    - Frontmatter and SEO/GEO validation (`fact_checks` path).
    - Example smoke checks (`self_checks`) for generated docs.
    - Minimal weekly status outputs (`reports/consolidated_report.json` fallback, `reports/docsops_status.json`, and `reports/READY_FOR_REVIEW.txt`).
    - Templates previously delivered in bundle/repository for manual use.
12. In community mode, advanced features are disabled, including:
    - Gap detection, drift/docs-contract checks, and KPI/SLA automation.
    - Glossary sync and lifecycle management automation.
    - API-first and multi-protocol pipelines (REST/GraphQL/gRPC/AsyncAPI/WebSocket).
    - Knowledge extraction/index/graph/retrieval evals and retrieval-time Ask AI runtime.
    - Custom weekly premium tasks and premium integrations (including Algolia upload and Ask AI billing runtime).

## 4. Deliverables and acceptance

1. Provider will deliver implementation artifacts, runbooks, and reports corresponding to service scope.
2. Client has five (5) business days after delivery to report material non-conformance.
3. If no material non-conformance is reported within that window, deliverables are deemed accepted.

## 5. Change control

Any scope expansion or modification requires a written change order signed by both Parties.

## 6. Client responsibilities

1. Provide timely technical access and required contacts.
2. Ensure legal rights for all submitted content and systems.
3. Provide timely review and decision feedback.

## 7. Confidentiality

Each Party will protect the other Party's Confidential Information with reasonable care and use it only for Agreement purposes.

## 8. Intellectual property

1. Provider retains pre-existing IP in methods, templates, and platform components.
2. Client retains rights in Client-provided data and materials.
3. Subject to payment, Client receives internal-use rights to delivered implementation artifacts.

## 9. Restricted use and protection of Provider solution

1. Client shall not copy, reproduce, distribute, publish, sublicense, sell, lease, assign, disclose, or otherwise transfer the Provider solution, or any substantial part of it, to any third party without Provider's prior written consent.
2. Client shall not reverse engineer, decompile, disassemble, or attempt to derive source logic, architecture, prompt policies, retrieval strategies, or internal methods from the deliverables, except where such restriction is prohibited by mandatory law.
3. Client shall not use the deliverables, documentation, workflows, templates, policy packs, or other Provider Confidential Information to build, commission, or assist in building a competing documentation automation or RAG operations solution.
4. Client shall not circumvent Provider by directly hiring, instructing, or engaging third parties to replicate the core commercial solution delivered under this Agreement using Provider materials or know-how.
5. These restrictions apply during the Agreement term and for `{{RESTRICTED_USE_MONTHS}}` months after termination or expiration.
6. Unauthorized use constitutes material breach and infringement of Provider rights.

## 10. Warranties and disclaimers

1. Provider will perform services in a professional and workmanlike manner.
2. Except as expressly stated, deliverables are provided "as is."

## 11. Limitation of liability

1. Each Party's aggregate liability is limited to fees paid or payable under this Agreement.
2. Neither Party is liable for indirect, incidental, special, consequential, or punitive damages, to the maximum extent permitted by law.

## 12. Remedies and injunctive relief

1. Client acknowledges that breach of Section 6 or Section 8 may cause irreparable harm to Provider for which monetary damages may be insufficient.
2. Provider is entitled to seek immediate injunctive or equitable relief, in addition to any other remedies available at law or in equity, without waiving other rights.
3. Client shall indemnify Provider for reasonable legal fees and enforcement costs arising from proven willful breach of Section 8 by Client.

## 13. Termination

Either Party may terminate for material breach not cured within the agreed cure period after written notice.

## 14. Governing law and venue

1. Governing law: {{GOVERNING_LAW_STATE_OR_COUNTRY}}
2. Venue: {{VENUE_CITY_AND_STATE_OR_COUNTRY}}

## 15. Electronic execution

Parties may execute this Agreement through SignNow (or equivalent e-signature platform). Electronic signatures are binding.

## 16. Entire agreement

This Agreement is the complete agreement for the described services and supersedes prior discussions on this subject.

## Signatures

**PROVIDER**  
Legal name: {{PROVIDER_LEGAL_NAME}}  
Name: {{PROVIDER_SIGNATORY_NAME}}  
Title: {{PROVIDER_SIGNATORY_TITLE}}  
Email: {{PROVIDER_SIGNATORY_EMAIL}}  
Signature: ________________________  
Date: ________________________

**CLIENT**  
Legal name: {{CLIENT_LEGAL_NAME}}  
Name: {{CLIENT_SIGNATORY_NAME}}  
Title: {{CLIENT_SIGNATORY_TITLE}}  
Email: {{CLIENT_SIGNATORY_EMAIL}}  
Signature: ________________________  
Date: ________________________

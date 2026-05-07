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

# Full Implementation Services Agreement

This Agreement is entered into as of **2026-05-02** ("Effective Date") by and between:

- **Provider:** VeriDoc Inc., a Sole Proprietor (Polish JDG/FOP) registered under the laws of Poland, with principal address at [Provider Address].
- **Client:** VeriOps, a Corporation organized under the laws of [Client Jurisdiction], with principal address at [Client Address].

The Provider and the Client are each a "Party" and together the "Parties."

## 1. Services scope

Provider will deliver: **Full Auto-Doc Pipeline implementation without production retrieval-time RAG runtime.**

For pilot engagements (where applicable), repository scope is:
- `veriops`
- Pilot dates: `2026-05-02` through `2026-05-23`

## 2. Commercial terms

1. Agreement fee: **USD $15,000**.
1. Payment terms: 100% due upfront within five (5) business days of signature.
1. Pricing reference:
   - Pilot: USD $5,000
   - Full: USD $15,000
   - RAG add-on: USD $10,000
   - Full+RAG total: USD $25,000
1. Pilot credit policy:
   - If Client buys Full or Full+RAG within `90` days after pilot completion, paid pilot fee is credited.
   - Full after pilot: USD $10,000
   - Full+RAG after pilot: USD $20,000

## 3. Retainer terms

1. Retainer mode: `disabled`.
1. Monthly retainer fee: **USD $0** payable in advance.
1. Included monthly capacity: `0` hours.
1. Overage rate (above included capacity): **USD $0 / hour**.
1. Scope covered by retainer: Post-implementation support, remediation, incremental documentation updates, and agreed automation adjustments.
1. Response window target: Within two (2) business days.
1. Unused hours policy: Unused hours expire at month end.
1. If payment is overdue by more than `7` days, Provider may suspend services until account is current.
1. Either Party may terminate the retainer with `30` days written notice (implementation work already accepted remains payable).
1. If retainer is not paid, not renewed, or is terminated, Provider may downgrade runtime entitlement to `community` mode after written notice and grace period of `7` days.
1. Community mode includes only:
    - Markdown/content hygiene defaults (normalization and snippet checks).
    - Frontmatter and SEO/GEO validation (`fact_checks` path).
    - Example smoke checks (`self_checks`) for generated docs.
    - Minimal weekly status outputs (`reports/consolidated_report.json` fallback, `reports/docsops_status.json`, and `reports/READY_FOR_REVIEW.txt`).
    - Templates previously delivered in bundle/repository for manual use.
1. In community mode, advanced features are disabled, including:
    - Gap detection, drift/docs-contract checks, and KPI/SLA automation.
    - Glossary sync and lifecycle management automation.
    - API-first and multi-protocol pipelines (REST/GraphQL/gRPC/AsyncAPI/WebSocket).
    - Knowledge extraction/index/graph/retrieval evals and retrieval-time Ask AI runtime.
    - Custom weekly premium tasks and premium integrations (including Algolia upload and Ask AI billing runtime).

## 4. Deliverables and acceptance

1. Provider will deliver implementation artifacts, runbooks, and reports corresponding to service scope.
1. Client has five (5) business days after delivery to report material non-conformance.
1. If no material non-conformance is reported within that window, deliverables are deemed accepted.

## 5. Change control

Any scope expansion or modification requires a written change order signed by both Parties.

## 6. Client responsibilities

1. Provide timely technical access and required contacts.
1. Ensure legal rights for all submitted content and systems.
1. Provide timely review and decision feedback.

## 7. Confidentiality

Each Party will protect the other Party's Confidential Information with reasonable care and use it only for Agreement purposes.

## 8. Intellectual property

1. Provider retains pre-existing IP in methods, templates, and platform components.
1. Client retains rights in Client-provided data and materials.
1. Subject to payment, Client receives internal-use rights to delivered implementation artifacts.

## 9. Restricted use and protection of Provider solution

1. Client shall not copy, reproduce, distribute, publish, sublicense, sell, lease, assign, disclose, or otherwise transfer the Provider solution, or any substantial part of it, to any third party without Provider's prior written consent.
1. Client shall not reverse engineer, decompile, disassemble, or attempt to derive source logic, architecture, prompt policies, retrieval strategies, or internal methods from the deliverables, except where such restriction is prohibited by mandatory law.
1. Client shall not use the deliverables, documentation, workflows, templates, policy packs, or other Provider Confidential Information to build, commission, or assist in building a competing documentation automation or RAG operations solution.
1. Client shall not circumvent Provider by directly hiring, instructing, or engaging third parties to replicate the core commercial solution delivered under this Agreement using Provider materials or know-how.
1. These restrictions apply during the Agreement term and for `36` months after termination or expiration.
1. Unauthorized use constitutes material breach and infringement of Provider rights.

## 10. Warranties and disclaimers

1. Provider will perform services in a professional and workmanlike manner.
1. Except as expressly stated, deliverables are provided "as is."

## 11. Limitation of liability

1. Each Party's aggregate liability is limited to fees paid or payable under this Agreement.
1. Neither Party is liable for indirect, incidental, special, consequential, or punitive damages, to the maximum extent permitted by law.

## 12. Remedies and injunctive relief

1. Client acknowledges that breach of Section 6 or Section 8 may cause irreparable harm to Provider for which monetary damages may be insufficient.
1. Provider is entitled to seek immediate injunctive or equitable relief, in addition to any other remedies available at law or in equity, without waiving other rights.
1. Client shall indemnify Provider for reasonable legal fees and enforcement costs arising from proven willful breach of Section 8 by Client.

## 13. Termination

Either Party may terminate for material breach not cured within the agreed cure period after written notice.

## 14. Governing law and venue

1. Governing law: Poland
1. Venue: Warsaw, Poland

## 15. Electronic execution

Parties may execute this Agreement through SignNow (or equivalent e-signature platform). Electronic signatures are binding.

## 16. Entire agreement

This Agreement is the complete agreement for the described services and supersedes prior discussions on this subject.

## Signatures

**PROVIDER**
Legal name: VeriDoc Inc.
Name:
Title:
Email:
Signature: ________________________
Date: ________________________

**CLIENT**
Legal name: VeriOps
Name:
Title:
Email: jane.dolska@gmail.com
Signature: ________________________
Date: ________________________

## Next steps

- [Documentation index](../index.md)

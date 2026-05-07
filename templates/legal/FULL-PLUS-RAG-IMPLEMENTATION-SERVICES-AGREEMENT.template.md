---
title: "Full Plus RAG Implementation Agreement"
description: "Template agreement for full Auto-Doc Pipeline plus production retrieval-time RAG implementation."
content_type: reference
product: both
last_reviewed: "2026-04-28"
tags:
  - Legal
  - Template
  - Full+RAG
---

# Full + RAG Implementation Services Agreement

This Full + RAG Implementation Services Agreement ("Agreement") is entered into as of **{{EFFECTIVE_DATE}}** by and between {{PROVIDER_LEGAL_NAME}} ("Provider") and {{CLIENT_LEGAL_NAME}} ("Client").

## 1. Scope

1. Provider will deliver full Auto-Doc Pipeline implementation plus production retrieval-time RAG runtime.
2. Scope includes all full implementation capabilities and RAG runtime capabilities listed in Exhibit A.
3. Deployment model (for example strict-local, on-prem, or air-gapped) is defined in Exhibit B.

## 2. Included full + RAG capabilities

1. Knowledge preparation pipeline:
   - normalization, structuring, and quality hardening before indexing,
   - semantic chunking into modules with metadata,
   - stale-check and contradiction-check,
   - critical module exclusion from retrieval index,
   - retrieval index + knowledge graph build,
   - retrieval evaluation gate (precision, recall, hallucination-risk metrics).
2. RAG runtime layer:
   - retrieval-time context grounding,
   - low-confidence guardrail,
   - runtime contradiction warnings,
   - usage logging and feedback loop.
3. Advanced retrieval stack:
   - retrieval mode auto-routing (`auto`, `hybrid`, `vectorless`, `semantic`, `token`),
   - vectorless structural retrieval for long structured docs,
   - query decomposition and evidence fusion for multi-hop requests,
   - entity-first retrieval,
   - graph rerank layer.

## 3. Exclusions

1. Features not listed in Exhibit A or purchased add-ons.
2. External third-party licensing costs unless explicitly included.
3. 24/7 SLA unless separately contracted.

## 4. Fees and payment

1. Full + RAG Implementation fee: **USD $25,000**.
2. If Client completed and paid Pilot with Provider and is eligible for credit, net Full + RAG fee is **USD $20,000**.
3. Payment schedule: {{PAYMENT_TERMS}}.
4. Taxes excluded.

## 5. Acceptance and go-live criteria

1. Acceptance criteria are defined in Exhibit C and include:
   - successful gate execution,
   - retrieval eval gate threshold achievement,
   - documented runbooks and operations handoff.
2. Client has five (5) business days after each acceptance submission to provide material defect notice.

## 6. Operational boundaries and risk controls

1. Client acknowledges that system behavior depends on source data quality and coverage.
2. Provider implements guardrails and quality controls, but does not guarantee zero error rate.
3. Client retains final responsibility for production policy decisions and user-facing risk posture.

## 7. Confidentiality, data handling, and compliance

1. Mutual confidentiality obligations apply.
2. Data processing terms, security controls, and compliance profile are defined in Exhibit D.
3. If required, Parties execute separate DPA/security addendum.

## 8. IP, licensing, and usage rights

1. Provider retains pre-existing IP and platform/tooling rights.
2. Client retains rights in Client content, data, and business artifacts.
3. Subject to payment, Client receives internal-use rights to configured deliverables and runtime package under this Agreement.

## 9. Warranty disclaimer and limitation of liability

1. Services are provided professionally and in good faith.
2. Except as expressly stated, deliverables are provided "as is."
3. Liability cap equals fees paid/payable under this Agreement; indirect/consequential damages excluded to the maximum extent allowed by law.

## 10. Termination

1. Either Party may terminate for uncured material breach after written notice and cure period.
2. On termination, Client pays for services rendered through effective termination date.

## 11. Governing law and signatures

1. Governing law: {{GOVERNING_LAW_STATE_OR_COUNTRY}}.
2. Venue: {{VENUE_CITY_AND_STATE_OR_COUNTRY}}.
3. Parties agree to SignNow or equivalent e-sign execution; such signatures are binding.

## 12. Entire agreement

1. This Agreement and exhibits are the complete agreement for full + RAG implementation.
2. Amendments require written signatures by both Parties.

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


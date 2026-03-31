---
title: "Customer packet checklist"
description: "Pre-outreach checklist for executive PDF, scorecard evidence, legal links, and outbound email package."
date: "2026-03-31"
last_reviewed: "2026-03-31"
---

# Customer packet checklist

Use this checklist before outreach or sales calls.

## Required artifacts

- [ ] Executive PDF exists (`reports/*executive-audit*.pdf`).
- [ ] HTML scorecard exists (`reports/audit_scorecard.html`).
- [ ] Public audit JSON exists (`reports/public_docs_audit.json`).
- [ ] Latest consolidated report exists (`reports/consolidated_report.md`).

## Legal links (must be public)

- [ ] Terms of service
- [ ] Privacy policy
- [ ] Data processing agreement
- [ ] Security policy
- [ ] Security contact policy

## Outbound email package

- [ ] Use template from `deploy/OUTREACH_EMAIL_TEMPLATE.md`.
- [ ] Include exactly one high-impact finding and one quantified opportunity.
- [ ] Attach executive PDF and scorecard link.
- [ ] Include a 20-minute review call link.

## Final validation

- [ ] `npm run lint` passes locally.
- [ ] `npm run docs-ops:e2e` passes locally.
- [ ] `production-gate.md` has no unresolved blocker in sections 8, 9, 10.

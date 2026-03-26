---
title: "Production gate checklist"
description: "Strict go or no-go checklist for VeriDoc and VeriOps production launch readiness."
date: "2026-03-24"
last_reviewed: "2026-03-24"
---

<!-- cspell:ignore veridoc lemonsqueezy -->

# Production Gate Checklist (VeriDoc + VeriOps)

This file is a strict GO/NO-GO gate. Do not start outreach until all items are `DONE`.
Use it together with [Deployment Runbook](deploy/production-runbook.md).

## 1. Release freeze

- [ ] `git_wrapper` pinned commit is recorded.
- [ ] `Auto-Doc Pipeline` pinned commit is recorded.
- [ ] No uncommitted changes in either repo.

## 2. Staging equals production

- [ ] Separate staging domain is live (for example, `staging.veridoc.app`).
- [ ] Same Docker images, env vars, and nginx config as production.
- [ ] Same DB engine/version and Redis version as production.

## 3. Secrets and keys

- [ ] No secrets in git history or tracked files.
- [ ] Server `.env` is used with `chmod 600`.
- [ ] `VERIDOC_SECRET_KEY` is unique and not default.
- [ ] LemonSqueezy secrets are set and tested.
- [ ] LLM keys are set only on server.

## 4. Network and TLS

- [ ] Domain and DNS are configured.
- [ ] HTTPS is valid (TLS certificate active).
- [ ] HTTP to HTTPS redirect is active.
- [ ] CORS allowlist uses explicit origins only.

## 5. Auth and access controls

- [ ] Register/login works in staging and production.
- [x] Token expiration works as expected.
- [x] Protected APIs reject missing/invalid token.
- [x] Protected APIs pass with valid token.

## 6. Billing

- [ ] Checkout links are correct for all plans.
- [x] Webhook signature verification is enabled.
- [x] Events tested: new subscription, renewal, cancel, payment failure, refund.
- [x] Plan limits are enforced after webhook updates.

## 7. Data safety and recovery

- [ ] Daily DB backup is automated.
- [ ] Restore test was run successfully from latest backup.
- [ ] Rollback procedure is documented and tested.

## 8. Observability

- [ ] API health checks are monitored.
- [ ] Error tracking is connected (for example, Sentry).
- [ ] Central logs are retained (API, worker, nginx).
- [ ] Alerts configured for uptime, 5xx rate, and latency.

## 9. Quality gates

- [ ] Pre-commit checks pass without `--no-verify`.
- [ ] Docs pipeline passes on staging.
- [x] End-to-end smoke scenario passes:
  `onboarding -> settings -> run pipeline -> artifacts -> executive report`.

## 10. Customer-facing package

- [ ] Audit PDF template finalized.
- [ ] `audit_scorecard.html` included as evidence.
- [ ] Outreach email template is ready.
- [ ] Terms, Privacy, DPA, and Security contact pages are published.

## GO decision

- [ ] All items above are done.
- [ ] You have one-click rollback command tested in staging.
- [x] You can run smoke test in production on demand.

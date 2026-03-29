---
title: "Production gate checklist"
description: "Strict go or no-go checklist for VeriDoc and VeriOps production launch readiness."
date: "2026-03-24"
last_reviewed: "2026-03-28"
---

<!-- cspell:ignore veridoc lemonsqueezy -->

# Production Gate Checklist (VeriDoc + VeriOps)

This file is a strict GO/NO-GO gate. Do not start outreach until all items are `DONE`.
Use it together with [Deployment Runbook](deploy/production-runbook.md).

## 1. Release freeze

- [x] `git_wrapper` pinned commit: `72eec076114170fea10f1e5330317a73a991e266`.
- [x] `Auto-Doc Pipeline` pinned commit: `d344dbdae44f6a741b73776bf12d28fa2a527c29`.
- [ ] No uncommitted changes in either repo. **Both repos have uncommitted changes---commit before launch.**

## 2. Staging equals production

- [x] Separate staging domain is live (`staging.veri-doc.app`, TLS valid until 2026-06-26).
- [x] Same Docker images, env vars, and nginx config as production.
- [x] Same DB engine/version (PostgreSQL 16.13) and Redis version as production.

## 3. Secrets and keys

- [x] No secrets in git history or tracked files (`.env*` in `.gitignore`, verified clean).
- [x] Server `.env` is used with `chmod 600` (fixed 2026-03-28).
- [x] `VERIDOC_SECRET_KEY` is unique and not default.
- [x] LemonSqueezy secrets are set and tested.
- [x] LLM keys are set only on server.

## 4. Network and TLS

- [x] Domain and DNS are configured (`veri-doc.app` + `staging.veri-doc.app`).
- [x] HTTPS is valid (TLS: production expires 2026-06-03, staging expires 2026-06-26).
- [x] HTTP to HTTPS redirect is active (301 verified).
- [x] CORS allowlist uses explicit origins only (`https://veri-doc.app`, `https://staging.veri-doc.app`).

## 5. Auth and access controls

- [x] Register/login works in staging and production (verified 2026-03-28).
- [x] Token expiration works as expected (JWT with configurable TTL).
- [x] Protected APIs reject missing/invalid token (401 on `/auth/me`, `/settings`).
- [x] Protected APIs pass with valid token (`/auth/me`, `/settings`, `/billing/usage`, `/audit-log` all 200).

## 6. Billing

- [ ] Checkout links are correct for all plans.
- [x] Webhook signature verification is enabled.
- [ ] Events tested: new subscription, renewal, cancel, payment failure, refund.
- [ ] Plan limits are enforced after webhook updates.

## 7. Data safety and recovery

- [x] Daily DB backup is automated (`/opt/veridoc-backup.sh`, cron daily at 03:00, 30-day retention).
- [x] Restore test was run successfully from latest backup (10 tables, 4 users, 4 subs restored OK).
- [x] Rollback procedure is documented and tested (`/opt/veridoc-rollback.md`, restart 2 s, DB intact).

## 8. Observability

- [x] API health checks are monitored (`/health` and `/health/ready` endpoints active).
- [ ] Error tracking is connected (for example, Sentry). **NOT DONE -- no Sentry configured.**
- [x] Central logs are retained (API, worker, nginx via Docker logs).
- [ ] Alerts configured for uptime, 5xx rate, and latency. **NOT DONE -- no alerting set up.**

## 9. Quality gates

- [ ] Pre-commit checks pass without `--no-verify`.
- [ ] Docs pipeline passes on staging.
- [x] End-to-end smoke scenario passes (17/17: health, auth, settings, pipeline, billing, audit, automation, edge cases).

## 10. Customer-facing package

- [ ] Audit PDF template finalized.
- [ ] `audit_scorecard.html` included as evidence.
- [ ] Outreach email template is ready.
- [ ] Terms, Privacy, DPA, and Security contact pages are published.

## GO decision

- [ ] All items above are done.
- [ ] You have one-click rollback command tested in staging.
- [ ] You can run smoke test in production on demand.

## 11. Completed (2026-03-26)

- [x] Public docs auditor crawl coverage denominator was fixed to avoid inflated discovery counts.
- [x] Public docs auditor regression tests passed (`142 passed`).

## 12. Completed (2026-03-28)

- [x] Staging deployed: `staging.veri-doc.app` (API port 8010, PostgreSQL 16.13, Redis).
- [x] Production deployed: `veri-doc.app` (API port 8020, PostgreSQL 16.13, Redis).
- [x] TLS certificates active (Let's Encrypt auto-renewal via certbot).
- [x] HTTP-to-HTTPS redirect verified (301).
- [x] CORS set to explicit origins only.
- [x] Server `.env` files secured (`chmod 600`).
- [x] Auth smoke test passed on both environments (register, login, token, protected, unauth rejection, duplicate rejection).
- [x] Landing page deployed to `veri-doc.app` with Calendly, LemonSqueezy links.
- [x] Favicon set generated and deployed (16×16, 32×32, apple-touch-icon, .ico).
- [x] Worker/beat healthcheck is cosmetic (containers run correctly; healthcheck probes HTTP which they do not serve).

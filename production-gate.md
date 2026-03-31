---
title: "Production gate checklist"
description: "Strict go or no-go checklist for VeriDoc and VeriOps production launch readiness."
date: "2026-03-24"
last_reviewed: "2026-03-31"
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
- [x] Error tracking is connected (Sentry optional + runtime error monitor).
  - Sentry hooks exist in API and worker (`SENTRY_DSN` env wiring).
  - Added runtime error alert monitor: `deploy/error_log_monitor.sh`.
- [x] Central logs are retained (API, worker, nginx via Docker logs).
- [x] Alerts configured for uptime and latency plus runtime error alerts.
  - Health monitor: `deploy/healthcheck_monitor.sh`.
  - Systemd timers/services added:
    - `deploy/systemd/veridoc-healthcheck-monitor.service`
    - `deploy/systemd/veridoc-healthcheck-monitor.timer`
    - `deploy/systemd/veridoc-error-monitor.service`
    - `deploy/systemd/veridoc-error-monitor.timer`
  - One-command installer: `deploy/setup_observability.sh`.

## 9. Quality gates

- [x] Pre-commit checks pass without `--no-verify` (verified 2026-03-31 by `npm run lint`).
- [x] Docs pipeline gate passes in automated E2E (`npm run docs-ops:e2e`, 2026-03-31).
- [x] End-to-end smoke scenario passes (17/17: health, auth, settings, pipeline, billing, audit, automation, edge cases).

## 10. Customer-facing package

- [x] Audit PDF template finalized (`deploy/EXECUTIVE_AUDIT_TEMPLATE.md`).
- [x] `audit_scorecard.html` included as evidence (`reports/audit_scorecard.html`, generated 2026-03-31).
- [x] Outreach email template is ready (`deploy/OUTREACH_EMAIL_TEMPLATE.md`).
- [x] Terms, Privacy, DPA, and Security contact pages are published.
  - Docs legal set:
    - `docs/legal/terms-of-service.md`
    - `docs/legal/privacy-policy.md`
    - `docs/legal/data-processing-agreement.md`
    - `docs/legal/security-policy.md`
    - `docs/legal/security-contact-policy.md`
  - Public web paths:
    - `/legal/terms.html`
    - `/legal/privacy.html`
    - `/legal/dpa.html`
    - `/legal/security.html`
    - `/legal/security-contact.html`

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

## 13. Verification log (2026-03-30)

- [x] Followed runbook commands that are executable in current environment (file checks, env checks, smoke command invocation).
- [ ] Full deploy commands from runbook completed in this environment.
  - Blocker: Docker CLI is unavailable in this WSL distro (`docker: command not found`).
- [x] Executed `npm run smoke:prod`.
- [ ] `smoke:prod` passed.
  - First failure: missing required env var `VERIDOC_BASE_URL`.
  - Second run with explicit vars failed due DNS resolution (`Temporary failure in name resolution` for `api.veri-doc.app`).
- [ ] Production GO can be confirmed from this environment.
  - Blockers: no DNS resolution to production API domain, no Docker runtime for runbook deploy steps.

## 14. Completed (2026-03-31)

- [x] `git_wrapper` main updated to `645686c` and deployed to both environments.
- [x] Production and staging are on the same commit (`645686c`).
- [x] Runtime health verified after deploy:
  - production: `veridoc-api`, `veridoc-web`, `veridoc-worker`, `veridoc-beat` are `healthy`.
  - staging: `veridoc-staging-api`, `veridoc-staging-web`, `veridoc-staging-worker`, `veridoc-staging-beat` are `healthy`.
- [x] Added automated Playwright staging smoke workflow:
  - `.github/workflows/playwright-staging.yml`
  - manual trigger (`workflow_dispatch`) and scheduled trigger (every 6 hours).
- [x] Backend quality checks aligned with CI:
  - `ruff check` passed,
  - `black --check` passed after full reformat,
  - contract+drift+smoke test bundle passed (`174 passed` in `packages/core/tests/{smoke,drift,contract}`).

## 16. Verification log (2026-03-31, late)

- [x] Post-deploy verification after latest rollout:
  - production head: `645686c`,
  - staging head: `645686c`,
  - all core containers are `healthy` in both environments (`api`, `web`, `worker`, `beat`).
- [ ] GitHub Actions run status directly confirmed from this environment.
  - Blocker: local `gh` cannot reach `api.github.com` in current network context.
- [x] Full monorepo `pytest tests` run completed to 100%.
  - Latest run result: `12315 passed`, `53 warnings`, `0 failed` (2026-03-31).

## 15. Current NO-GO blockers for paid launch

- [ ] Billing lifecycle not fully verified in production-like mode:
  - missing end-to-end confirmation for renewal, cancel, payment failure, refund events.
- [ ] Plan limits enforcement after webhook updates still not marked complete by evidence.
- [ ] Error tracking and alerting are still incomplete:
  - no confirmed Sentry (or equivalent) incident pipeline,
  - no confirmed uptime/latency/5xx alert routing.
- [ ] Customer/legal launch package still incomplete:
  - Terms, Privacy, DPA, security contact pages not all marked published,
  - outreach and evidence pack checklist not fully closed.

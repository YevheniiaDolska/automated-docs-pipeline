---
title: "Production gate checklist"
description: "Strict go or no-go checklist for VeriDoc and VeriOps production launch readiness."
date: "2026-03-24"
last_reviewed: "2026-04-01"
---

<!-- cspell:ignore veridoc lemonsqueezy msmtp brevo smtpstatus gitspeak -->

# Production Gate Checklist (VeriDoc + VeriOps)

This file is a strict GO/NO-GO gate. Do not start outreach until all items are `DONE`.
Use it together with [Deployment Runbook](deploy/production-runbook.md).

## 1. Release freeze

- [x] `git_wrapper` pinned commit: `72eec076114170fea10f1e5330317a73a991e266`.
- [x] `Auto-Doc Pipeline` pinned commit: `d344dbdae44f6a741b73776bf12d28fa2a527c29`.
- [x] No uncommitted changes in either repo.

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

- [x] Billing mode selected and documented.
  - Current mode: manual invoices (`VERIDOC_BILLING_MODE=manual`), no self-serve checkout required.
- [x] Webhook signature verification is enabled.
- [x] Lifecycle updates tested for selected billing mode.
  - For manual billing mode: `/ops/billing/manual-subscription/upsert` updates tier/status/period and refreshes license.
- [x] Plan limits are enforced after entitlement updates.
  - Manual upsert applies `TIER_LIMITS` and resets usage when requested.

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
- [x] Monitoring services enabled on server and verified (`2026-04-01`).
  - `veridoc-healthcheck-monitor.timer` and `veridoc-error-monitor.timer` are active.
  - Health monitor fixed for one-server route: `http://127.0.0.1:8020/health` returns `200`.
- [x] SMTP credentials configured and alert email pipeline validated (`2026-04-01`).
  - `.env` updated with Brevo SMTP fields.
  - `/opt/veridoc/deploy/configure_msmtp_from_env.sh` executed (`SMTP_CONFIGURED`).
  - Test email accepted by SMTP relay (`smtpstatus=250`, queued).

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

- [x] All items above are done.
- [x] You have one-click rollback command tested in staging.
- [x] You can run smoke test in production on demand.

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
- [x] Full deploy commands from runbook completed on target production server.
- [x] Executed `npm run smoke:prod`.
- [x] `smoke:prod` passed.
  - Passed on production server via API container execution (`/tmp/production_smoke.py`) against `http://127.0.0.1:8000`.
- [x] Production GO can be confirmed from server execution context.
  - Verified with production deploy command, service health, and smoke pass.

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
- [x] GitHub Actions run status directly confirmed from server environment.
  - Latest observed runs were reachable via GitHub API (conclusions: `failure` on recent CI/deploy workflows).
- [x] Full monorepo `pytest tests` run completed to 100%.
  - Latest run result: `12315 passed`, `53 warnings`, `0 failed` (2026-03-31).

## 17. Completed (2026-04-01, evening)

- [x] Runtime alert monitor hardened and deployed:
  - suppressed false alerts caused by `Traceback`-only log lines,
  - prevented empty normalized signatures/fingerprints in alert payload.
- [x] Error monitor script applied on server and verified:
  - `/opt/veridoc/deploy/error_log_monitor.sh` updated,
  - `veridoc-error-monitor.service` and timer run successfully (`status=0/SUCCESS`).
- [x] Worker traceback storm root cause fixed and deployed:
  - hardened `packages/core/gitspeak_core/tasks/pipeline_tasks.py` path resolution,
  - `api/worker/beat` rebuilt and returned to `healthy`.

## 19. Completed (2026-04-01, late evening)

- [x] Re-ran production deploy command on server:
  - `docker compose -f docker-compose.production.yml --env-file deploy/.env.production up -d --build`
- [x] Re-tested rollback path on staging (one-click restart):
  - stopped and started `api/worker/beat` via staging compose, then verified `http://127.0.0.1:8010/health`.
- [x] Re-ran production smoke successfully after deploy:
  - health, auth, dashboard, settings, and automation status checks passed.
- [x] Committed and pushed clean-state updates in both repos:
  - `Auto-Doc Pipeline`: `fade678`
  - `git_wrapper`: `0c1e94e`

## 18. Completed (2026-04-01, late evening)

- [x] API prompt flow now uses **user-provided planning notes as source of truth**.
  - Added explicit request payload support: `planning_notes`, `planning_notes_by_protocol`, `planning_notes_path`.
  - Removed synthetic planning-note generation path from task behavior.
- [x] API multi-protocol flow is enforced in strict mode for prompt runs.
  - Contracts/specs generation from planning notes where protocol source is missing.
  - Contract validation + regression checks + protocol lint stacks.
  - Server stub generation for endpoint code with placeholder business-logic stubs.
  - Protocol docs generation + quality suites + self-verify gates.
  - Contract test assets generation and publish gates.
- [x] Added dedicated REST API-first stage inside prompt pipeline execution.
  - Runs `run_api_first_flow.py` with user notes, endpoint stubs generation, user-path verification, test-assets.
  - Keeps sandbox/mock synchronization path in the same execution chain.

## 15. Current NO-GO blockers for paid launch

- [x] Billing lifecycle verified for selected mode:
  - manual mode uses invoice workflow plus `/ops/billing/manual-subscription/upsert`.
- [x] Plan limits enforcement after entitlement updates is implemented and documented.
- [x] Error tracking and alerting baseline is closed:
  - monitors/timers are active,
  - health checks are verified,
  - SMTP email routing is validated.
- [x] Customer/legal launch package closed:
  - legal docs/pages are present and linked,
  - outreach template and customer packet checklist are in `deploy/`.

## 20. RAG enterprise-suite gate

- [x] Unified runtime RAG endpoint is available (`/rag/query` + `/rag/runtime/query`) with ACL checks.
- [x] RAG observability snapshot and alerts endpoints are available (`/rag/metrics`, `/rag/alerts`).
- [x] Versioned RAG index lifecycle supports reindex + promote/rollback + retention policy.
- [x] Weekly/autopipeline/API-first/multi-protocol flows enforce RAG optimization layer automatically.
- [x] Egress metadata policy is enforced with local audit trail (`reports/llm_egress_log.json`).
- [ ] Full cloud/hybrid/strict-local E2E run executed on staging from clean release commit.
- [ ] Staging RAG alerts and thresholds validated under live load profile.

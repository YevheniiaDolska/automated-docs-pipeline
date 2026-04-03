---
title: "Production deployment runbook"
description: "Step-by-step beginner runbook to deploy, verify, back up, and roll back VeriDoc in production."
date: "2026-03-24"
last_reviewed: "2026-04-01"
---

<!-- cspell:ignore veridoc lemonsqueezy tokenurlsafe token_urlsafe urlsafe msmtp cust dgst chargeback -->

# Production Runbook (Beginner-Friendly)

This runbook is a copy-paste path for first deployment.

## 0. Prerequisites

1. VPS with Ubuntu 22.04+.
1. Domain attached to server IP:
   - `api.veridoc.app`
   - `app.veridoc.app`
1. Installed: Docker, Docker Compose plugin, Git.

## 1. Clone and prepare

```bash
sudo mkdir -p /opt/veridoc
sudo chown -R $USER:$USER /opt/veridoc
cd /opt/veridoc
git clone <YOUR_REPO_URL> .
```

## 2. Configure environment

```bash
cp deploy/.env.example .env
nano .env
chmod 600 .env
```

Set at minimum:

- `POSTGRES_PASSWORD`
- `VERIDOC_SECRET_KEY`
- `VERIOPS_LICENSE_KEY`
- `VERIDOC_CORS_ORIGINS=APP_ORIGIN`
- `LEMONSQUEEZY_API_KEY`
- `LEMONSQUEEZY_STORE_ID`
- `LEMONSQUEEZY_WEBHOOK_SECRET`
- `VERIDOC_ADMIN_EMAIL` (comma-separated list for alerts)
- `VERIDOC_SMTP_FROM` (alert sender)
- `VERIDOC_SMTP_HOST` (SMTP server host for alerts)
- `VERIDOC_SMTP_PORT` (SMTP port, usually `587`)
- `VERIDOC_SMTP_USER` (SMTP username/login)
- `VERIDOC_SMTP_PASSWORD` (SMTP password/app password)
- `SENTRY_DSN` (optional; if empty, log-based error monitor still works)

Generate a strong secret:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

## 3. Start production stack

```bash
docker compose -f docker-compose.production.yml --env-file .env up -d --build
docker compose -f docker-compose.production.yml ps
```

## 4. Verify health

```bash
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/health/ready
```

## 5. Nginx and TLS

1. Use `deploy/nginx.conf` (already includes rate limiting).
1. Put TLS certs under `deploy/ssl`.
1. Restart nginx container:

```bash
docker compose -f docker-compose.production.yml restart nginx
```

## 6. Run production smoke

```bash
VERIDOC_BASE_URL=https://api.veridoc.app \
VERIDOC_SMOKE_EMAIL=smoke@veridoc.app \
VERIDOC_SMOKE_PASSWORD='CHANGE_ME_STRONG' \
python3 scripts/production_smoke.py
```

Expected final line:

```text
[OK] Production smoke completed successfully
```

## 7. Enable automatic license renewal from payments

For fully automatic `payment -> access extended`, keep webhook processing enabled on server.

1. In LemonSqueezy, set webhook URL to:
   - `https://api.veridoc.app/api/billing/webhooks/lemonsqueezy`
   - If you use one-domain mode: `https://yourdomain.com/api/billing/webhooks/lemonsqueezy`
1. In LemonSqueezy webhook settings, subscribe at minimum to:
   - `subscription_created`
   - `subscription_updated`
   - `subscription_cancelled`
   - `subscription_resumed`
   - `subscription_payment_success`
   - `subscription_payment_failed`
   - `subscription_expired`
   - `subscription_paused`
   - `subscription_unpaused`
   - `subscription_plan_changed`
   - `order_refunded`
1. Ensure secrets are set in server `.env`:
   - `LEMONSQUEEZY_WEBHOOK_SECRET`
   - `VERIOPS_LICENSE_KEY`
1. Restart services after `.env` change:

```bash
docker compose -f docker-compose.production.yml --env-file .env up -d --build
```

1. Verify webhook processing in logs while sending a test event from LemonSqueezy:

```bash
docker compose -f docker-compose.production.yml logs -f api worker
```

Expected result:

- webhook signature is accepted,
- subscription state is updated,
- license entitlement is refreshed automatically for active paid plans.

### Manual invoice mode (no LemonSqueezy checkout)

If you bill clients manually (invoice-first), set:

```bash
VERIDOC_BILLING_MODE=manual
```

Then manage paid access via ops endpoint after invoice is paid:

```bash
curl -X POST "https://yourdomain.com/ops/billing/manual-subscription/upsert" \
  -H "Content-Type: application/json" \
  -H "X-VeriOps-Server-Token: $VERIOPS_SERVER_SHARED_TOKEN" \
  -d '{
    "user_id":"<USER_ID>",
    "tier":"enterprise",
    "status":"active",
    "period_days":30,
    "source":"manual_invoice",
    "reset_usage":true
  }'
```

Result:

- usage limits are applied from plan matrix,
- period window is updated,
- server license is reissued automatically.

### Full automation for manual billing (webhook-driven)

If you want zero manual calls, connect your payment system to:

- `POST /billing/webhooks/manual`

Required server env:

- `VERIDOC_BILLING_MODE=manual`
- `VERIDOC_MANUAL_WEBHOOK_SECRET=<strong_secret>`

Webhook body (example):

```json
{
  "event_name": "payment_success",
  "data": {
    "user_id": "<USER_ID>",
    "tier": "enterprise",
    "period_days": 30,
    "source": "wise_webhook",
    "external_customer_ref": "cust_12345"
  }
}
```

Signature header:

- Header: `X-Manual-Signature`
- Algorithm: `HMAC-SHA256`
- Value: `hex(hmac_sha256(secret, raw_request_body_bytes))`

Local signature example:

```bash
payload='{"event_name":"payment_success","data":{"user_id":"<USER_ID>","tier":"enterprise","period_days":30,"source":"wise_webhook"}}'
sig=$(printf '%s' "$payload" | openssl dgst -sha256 -hmac "$VERIDOC_MANUAL_WEBHOOK_SECRET" | awk '{print $2}')
curl -X POST "https://yourdomain.com/billing/webhooks/manual" \
  -H "Content-Type: application/json" \
  -H "X-Manual-Signature: $sig" \
  -d "$payload"
```

Supported manual events:

- `payment_success` / `payment_succeeded` / `invoice_paid` / `subscription_renewed`
- `payment_failed` / `invoice_failed`
- `subscription_canceled` / `access_revoked` / `chargeback`

## 8. Backup and restore check

Backup:

```bash
mkdir -p /opt/veridoc/backups
docker exec -t $(docker compose -f docker-compose.production.yml ps -q postgres) \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > /opt/veridoc/backups/veridoc-$(date +%F).sql
```

Restore test (run on staging DB, not prod):

```bash
cat /opt/veridoc/backups/veridoc-YYYY-MM-DD.sql | \
docker exec -i $(docker compose -f docker-compose.production.yml ps -q postgres) \
  psql -U "$POSTGRES_USER" "$POSTGRES_DB"
```

## 9. Rollback

If deployment fails:

```bash
git fetch --all --tags
git checkout <LAST_WORKING_COMMIT_OR_TAG>
docker compose -f docker-compose.production.yml --env-file .env up -d --build
```

## 10. Day-2 operations

1. Check logs:

```bash
docker compose -f docker-compose.production.yml logs -f api worker nginx
```

1. Weekly smoke test:
   - Run `scripts/production_smoke.py`
   - Run one billing webhook test from LemonSqueezy dashboard

1. Enable observability monitors (health + runtime error alerts):

## 11. RAG enterprise hardening verification

Run these checks after each deploy and before GO:

```bash
curl -fsS https://api.veridoc.app/rag/metrics
curl -fsS https://api.veridoc.app/rag/alerts
```

Trigger versioned reindex lifecycle (Business/Enterprise account):

```bash
curl -X POST "https://api.veridoc.app/rag/reindex" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"with_embeddings": true, "embeddings_provider": "openai"}'
```

Validate generated reports on server:

```bash
ls -la reports/rag_optimization_layer_report.json
ls -la reports/rag_reindex_report.json
ls -la reports/retrieval_evals_report.json
```

Validate metadata-only egress audit trail:

```bash
ls -la reports/llm_egress_log.json
tail -n 40 reports/llm_egress_log.json
```

If strict mode is required for regulated customers, confirm:

- `llm_control.strict_local_first=true`
- `llm_control.external_llm_allowed=false`
- provider in RAG layer is `local`

```bash
sudo bash deploy/setup_observability.sh /opt/veridoc
systemctl list-timers --all | grep -E 'veridoc-(healthcheck|error)-monitor'
```

1. Configure outbound SMTP for alert emails:

```bash
sudo bash deploy/configure_msmtp_from_env.sh
```

Expected:

- If all SMTP env vars are set: `SMTP_CONFIGURED`
- If something is missing: `/opt/veridoc/deploy/SMTP_SETUP_REQUIRED.txt` lists exact fields

1. Optional Sentry verification:

```bash
curl -fsS https://api.veri-doc.app/health/debug-sentry
```

Expected: response says test event was sent (or skipped if DSN is empty).

1. Customer/legal package before outreach:
   - Ensure legal pages are public:
     - `/legal/terms.html`
     - `/legal/privacy.html`
     - `/legal/dpa.html`
     - `/legal/security.html`
     - `/legal/security-contact.html`
   - Fill and run checklist: `deploy/CUSTOMER_PACKET_CHECKLIST.md`
   - Use outreach template: `deploy/OUTREACH_EMAIL_TEMPLATE.md`

1. Before outreach:
   - Confirm every checkbox in `production-gate.md` is done.

---
title: "Production deployment runbook"
description: "Step-by-step beginner runbook to deploy, verify, back up, and roll back VeriDoc in production."
date: "2026-03-24"
last_reviewed: "2026-03-26"
---

<!-- cspell:ignore veridoc lemonsqueezy tokenurlsafe token_urlsafe urlsafe -->

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

1. Before outreach:
   - Confirm every checkbox in `production-gate.md` is done.

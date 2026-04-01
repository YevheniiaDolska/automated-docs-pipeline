---
title: "1-day enterprise readiness checklist"
description: "Practical one-day checklist to finalize manual billing, IP protection, and local-first deployment readiness."
date: "2026-04-01"
last_reviewed: "2026-04-01"
---

<!-- cspell:ignore veridoc veriops lemonsqueezy -->

# 1-day enterprise readiness checklist

Use this checklist when you want full local-first delivery with protected server-side IP controls.

## A. Billing mode and enforcement

- [x] Set billing mode explicitly (`VERIDOC_BILLING_MODE=manual` for invoice-only flow).
- [x] Keep webhook endpoint available but ignored in manual mode.
- [x] Use ops entitlement endpoint after invoice payment:
  - `POST /ops/billing/manual-subscription/upsert`
- [x] Confirm limit enforcement path:
  - tier/status/period updated,
  - `TIER_LIMITS` applied,
  - optional usage reset,
  - server license auto-refreshed.

## B. Server pack-registry protection

- [x] Keep encrypted packs in server registry only.
- [x] Require checksum validation on publish.
- [x] Require Ed25519 signature verification on publish (server-side).
- [x] Publish/fetch only through ops token (`X-VeriOps-Server-Token`).
- [x] Keep revocation API active (`/billing/license/revocation-check`).

## C. Client-side secure pack flow

- [x] Publish CLI added: `scripts/pack_registry_publish.py`
- [x] Fetch+verify+install CLI added: `scripts/pack_registry_fetch.py`
- [x] Fetch flow verifies checksum and signature before writing `docsops/.capability_pack.enc`.
- [x] No client repo content is sent to pack-registry endpoints.

## D. Local-first data boundary

- [x] Egress allowlist stays metadata-only.
- [x] Telemetry endpoint blocks non-allowlisted fields.
- [x] LLM/content generation remains in client environment.

## E. Operator verification commands

```bash
# 1) Publish encrypted pack to server registry
python3 scripts/pack_registry_publish.py \
  --pack docsops/.capability_pack.enc \
  --pack-name core-policy \
  --version 2026.04.01 \
  --plan enterprise \
  --endpoint https://yourdomain.com/ops/pack-registry/publish \
  --ops-token "$VERIOPS_SERVER_SHARED_TOKEN" \
  --private-key docsops/keys/veriops-licensing.key

# 2) Fetch, verify, and install pack in client workspace
python3 scripts/pack_registry_fetch.py \
  --pack-name core-policy \
  --version 2026.04.01 \
  --endpoint https://yourdomain.com/ops/pack-registry/fetch \
  --ops-token "$VERIOPS_SERVER_SHARED_TOKEN" \
  --public-key docsops/keys/veriops-licensing.pub \
  --output docsops/.capability_pack.enc

# 3) Manual invoice paid -> grant/refresh enterprise entitlement
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

## Done criteria

- [ ] You can activate/deactivate paid access without LemonSqueezy checkout.
- [ ] You can rotate/update pack content via signed+encrypted registry flow.
- [ ] You can prove metadata-only egress and local-only content processing.

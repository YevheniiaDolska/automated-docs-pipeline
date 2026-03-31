---
title: "IP Protection Beginner Guide"
description: "Simple step-by-step setup guide for local-first operation with server-side IP protection."
date: "2026-03-31"
---

# IP protection beginner guide

This guide is for non-technical setup. Follow steps in order.

## What you get

1. Client data stays local.
1. Your product logic is protected by encryption, signatures, and licensing.
1. Server controls access and updates.

## Step 1. Build client bundle

Run on your machine in this repository:

```bash
python3 scripts/build_client_bundle.py --client profiles/clients/your-client.client.yml
```

This creates a client bundle with:

1. License gate.
1. Egress guard.
1. Traceability watermark.
1. Runtime scripts.

## Step 2. Fill client `.env.docsops.local`

Use generated template:

- `.env.docsops.local.template`

Set at minimum:

1. `VERIOPS_LICENSE_KEY`
1. `VERIOPS_TENANT_ID`
1. `VERIOPS_UPDATE_SERVER`
1. `VERIOPS_PHONE_HOME_URL`
1. `VERIOPS_PACK_REGISTRY_URL`
1. `VERIOPS_REVOCATION_CHECK_ENABLED`
1. `VERIOPS_REVOCATION_URL`
1. `VERIOPS_SERVER_SHARED_TOKEN` (set on server for protected ops endpoints)

## Step 3. Keep local-first mode

In `config/client_runtime.yml`, keep:

1. `llm_mode: local_default`
1. `external_llm_allowed: false`
1. `require_explicit_approval: true`
1. `redact_before_external: true`

## Step 4. Verify no content leaves client contour

Check:

- `reports/llm_egress_log.json`

You should see metadata-only approved events, and blocks for forbidden payloads.

## Step 5. Updates and entitlement

1. `check_updates.py` sends metadata only.
1. `license_gate.py` refreshes license metadata only.
1. Optional revoke checks can disable premium runtime if needed.

## Step 5.1. Server endpoints used by this flow

1. `POST /ops/pack-registry/publish` (requires `X-VeriOps-Server-Token`)
1. `GET /ops/pack-registry/fetch` (requires `X-VeriOps-Server-Token`)
1. `GET /ops/pack-registry/list` (requires `X-VeriOps-Server-Token`)
1. `DELETE /ops/pack-registry/{pack_name}/{version}` (requires `X-VeriOps-Server-Token`)
1. `POST /ops/telemetry/metadata` (requires `X-VeriOps-Server-Token`)
1. `GET /ops/telemetry/recent` (requires `X-VeriOps-Server-Token`)
1. `GET /billing/license/revocation-check` (metadata-only query)
1. `GET /ops/revocation/list` (requires `X-VeriOps-Server-Token`)
1. `POST /ops/revocation/upsert` (requires `X-VeriOps-Server-Token`)
1. `DELETE /ops/revocation/{tenant_id}` (requires `X-VeriOps-Server-Token`)

Example revoke workflow:

```bash
curl -sS -X POST "https://api.veri-doc.app/ops/revocation/upsert" \
  -H "X-VeriOps-Server-Token: $VERIOPS_SERVER_SHARED_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"acme-prod","reason":"billing_expired"}'

curl -sS "https://api.veri-doc.app/ops/revocation/list" \
  -H "X-VeriOps-Server-Token: $VERIOPS_SERVER_SHARED_TOKEN"
```

## Step 6. What to tell enterprise clients

Use this short statement:

1. "Your source code and documents never leave your environment."
1. "Only license/update metadata is sent to server."
1. "All advanced policy and prompt assets are delivered as encrypted signed packs."

## Important limitation

No local/on-prem setup can provide absolute 100% anti-reverse-engineering protection.

This design gives strong practical protection for commercial use:

1. Encryption in storage and transport.
1. Local-only content processing.
1. Watermark and traceability.
1. Server-side entitlement and revocation controls.

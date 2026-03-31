---
title: "Hybrid IP Protection v1"
description: "Server-local split for maximum IP protection with local-first client data safety."
date: "2026-03-31"
---

<!-- cspell:ignore Ollama -->

# Hybrid IP protection v1

This architecture keeps client code and docs local, while moving licensing, updates, and policy distribution to your server.

## Server side (maximum)

The server stores and controls:

1. Licenses, plans, entitlements, and renewals.
1. Billing/webhook processing.
1. Signed update manifests and rollback package references.
1. Encrypted policy/prompt/template packs (pack registry).
1. Metadata-only telemetry and anti-abuse controls.

## Local side (strict)

The client machine keeps and processes:

1. Repository source code and private documents.
1. API contracts, generated test assets, and reports.
1. Local LLM runs (Ollama).
1. Lint, quality gates, and docs generation pipeline.

No raw docs/code/prompt content is sent to server endpoints in this mode.

## Egress enforcement

The allowlist schema lives in:

- `config/ip_protection/egress_allowlist.yml`

Allowed outbound fields are metadata-only (for example: `tenant_id`, `build_id`, `version`, `plan`, `event`, `timestamp_utc`).

Outbound payload validation is enforced in:

- `scripts/llm_egress.py`
- `scripts/check_updates.py`
- `scripts/license_gate.py`

Egress decision log is written to:

- `reports/llm_egress_log.json`

If payload violates allowlist, request is blocked locally.

## Pack and prompt protection model

1. Prompt/policy/template packs are stored encrypted on server.
1. Client downloads encrypted pack only.
1. Pack is decrypted locally at runtime.
1. Optional cleanup removes temporary unpacked material after run.

This protects assets in storage and transport. During local execution, some logic can still be reverse-engineered.

## Concrete storage layout

Server layout:

1. `VERIOPS_PACK_REGISTRY_DIR` (default `/var/lib/veridoc/pack-registry`)
1. `VERIOPS_TELEMETRY_DIR` (default `/var/lib/veridoc/telemetry`)
1. `VERIOPS_REVOCATION_LIST_PATH` (default `/var/lib/veridoc/revoked_licenses.json`)

Client layout:

1. `<client-repo>/docsops/.capability_pack.enc` (encrypted package in rest state)
1. `<client-repo>/reports/llm_egress_log.json` (egress audit)
1. `<client-repo>/docsops/.bundle_trace.json` (watermark trace)

Temporary runtime:

1. Decrypt in memory or temp workspace.
1. Execute locally.
1. Optional cleanup removes temporary unpacked content after run.

## Traceability and watermark

Bundle build writes:

- `TRACEABILITY.yml`
- `docsops/.bundle_trace.json`

Fields include:

- `tenant_id`
- `build_id`
- `generated_at_utc`
- `source_git_commit`

This supports leak attribution and contract enforcement.

## Revocation and anti-abuse

Optional server revoke check is supported in `scripts/license_gate.py`.

Related env:

- `VERIOPS_REVOCATION_CHECK_ENABLED`
- `VERIOPS_REVOCATION_URL`

When enabled and server marks license as revoked, runtime drops to community mode.

Ops endpoints (server-side control plane):

1. `POST /ops/pack-registry/publish`
1. `GET /ops/pack-registry/fetch`
1. `GET /ops/pack-registry/list`
1. `DELETE /ops/pack-registry/{pack_name}/{version}`
1. `POST /ops/telemetry/metadata`
1. `GET /ops/telemetry/recent`
1. `GET /ops/revocation/list`
1. `POST /ops/revocation/upsert`
1. `DELETE /ops/revocation/{tenant_id}`

## Required env keys

Use these in `.env.docsops.local` on client side:

1. `VERIOPS_LICENSE_KEY`
1. `VERIOPS_TENANT_ID`
1. `VERIOPS_COMPANY_DOMAIN`
1. `VERIOPS_UPDATE_SERVER`
1. `VERIOPS_PHONE_HOME_URL`
1. `VERIOPS_PACK_REGISTRY_URL` (recommended: [pack fetch endpoint](https://api.veri-doc.app/ops/pack-registry/fetch))
1. `VERIOPS_REVOCATION_CHECK_ENABLED`
1. `VERIOPS_REVOCATION_URL` (recommended: [revocation check endpoint](https://api.veri-doc.app/billing/license/revocation-check))

## Security boundary summary

1. Client content remains local.
1. Server gets metadata only.
1. Critical product intelligence stays in encrypted server packs plus protected local binaries.
1. Signatures and revocation reduce unauthorized redistribution risk.

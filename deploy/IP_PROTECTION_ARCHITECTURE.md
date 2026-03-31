---
title: "Hybrid IP Protection v1"
description: "Server-local split for maximum IP protection with local-first client data safety."
date: "2026-03-31"
---

# Hybrid IP protection v1

This architecture keeps client code and docs local, while moving licensing, updates, and policy distribution to your server.

## Server side (maximum)

The server stores and controls:

1. Licenses, plans, entitlements, and renewals.
2. Billing/webhook processing.
3. Signed update manifests and rollback package references.
4. Encrypted policy/prompt/template packs (pack registry).
5. Metadata-only telemetry and anti-abuse controls.

## Local side (strict)

The client machine keeps and processes:

1. Repository source code and private documents.
2. API contracts, generated test assets, and reports.
3. Local LLM runs (Ollama).
4. Lint, quality gates, and docs generation pipeline.

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
2. Client downloads encrypted pack only.
3. Pack is decrypted locally at runtime.
4. Optional cleanup removes temporary unpacked material after run.

This protects assets in storage and transport. During local execution, some logic can still be reverse-engineered.

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

## Required env keys

Use these in `.env.docsops.local` on client side:

1. `VERIOPS_LICENSE_KEY`
2. `VERIOPS_TENANT_ID`
3. `VERIOPS_COMPANY_DOMAIN`
4. `VERIOPS_UPDATE_SERVER`
5. `VERIOPS_PHONE_HOME_URL`
6. `VERIOPS_PACK_REGISTRY_URL`
7. `VERIOPS_REVOCATION_CHECK_ENABLED`
8. `VERIOPS_REVOCATION_URL`

## Security boundary summary

1. Client content remains local.
2. Server gets metadata only.
3. Critical product intelligence stays in encrypted server packs plus protected local binaries.
4. Signatures and revocation reduce unauthorized redistribution risk.

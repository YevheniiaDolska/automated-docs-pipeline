---
title: "Policy packs"
description: "Canonical overview of built-in policy packs, usage model, and strictness boundaries."
content_type: reference
product: both
last_reviewed: "2026-04-25"
tags:
  - Operations
  - Policy
---

# Policy packs (canonical)

This page is the canonical policy-pack reference at repository root.

Mirror copy path:

- `docsops/POLICY_PACKS.md` (generated from this file)

## Built-in packs

- `minimal`
- `api-first`
- `monorepo`
- `multi-product`
- `plg`

## How packs are used

Policy packs define thresholds and behavior for quality, stale limits, gap tolerance, and operational strictness.

Selection is done through client profile and runtime config.

## Current practical model

1. Pilot usually starts with a lenient profile for onboarding.
1. Full implementation uses stricter production profile.
1. Community/degraded mode does not unlock advanced paid capabilities.

## Canonical deep docs

- `docs/operations/UNIFIED_CLIENT_CONFIG.md`
- `docs/operations/PLAN_TIERS.md`
- `docs/operations/OPERATOR_RUNBOOK.md`

## Next steps

- [Documentation index](../index.md)

---
title: Smart Merge and Manual Review
description: How needs_review works for protocol test assets and where operators review
  flagged cases.
content_type: how-to
product: both
last_reviewed: '2026-03-19'
tags:
- Testing
- Operations
- API
original_author: Kroha
---


# Smart Merge and Manual Review

## Where smart-merge runs

- `scripts/generate_protocol_test_assets.py`
- `reports/api-test-assets/api_test_cases.json`

## Merge rules

1. `origin=manual` cases are always preserved.
1. `customized=true` auto cases are preserved.
1. If contract signature changed, customized cases get `needs_review=true`.
1. Removed contract entities keep customized/manual cases with `needs_review=true` and `review_reason=contract_entity_removed`.
1. Non-customized auto cases are regenerated.

## Where reviewer sees required edits

Review queue is in generated JSON:

- `needs_review_count`
- `needs_review_ids`
- per-case `needs_review`, `review_reason`, `last_generated_signature`

Suggested operator flow:

1. Open `reports/api-test-assets/api_test_cases.json`.
1. Filter by `needs_review=true`.
1. Update cases and set `customized=true` for intentional overrides.
1. Re-run protocol test-asset generation.

## Next steps

- [Documentation index](../index.md)

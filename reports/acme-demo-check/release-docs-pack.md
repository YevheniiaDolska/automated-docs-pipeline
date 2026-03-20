---
title: "Release Docs Pack"
description: "Auto-generated release documentation package with changelogs, breaking changes, and migration checklists."
content_type: reference
product: both
---

# Release Docs Pack

Version: **unversioned-release**
Commit range: `HEAD~30..HEAD`

## Executive Summary

This package is generated automatically to accelerate release communication and reduce docs drift.

<!-- vale Google.Units = NO -->

## Draft changelog - features

- 53a1f90 feat(api-test-assets): add smart merge to preserve manual and customized test cases
- 162915a feat: add demo-showcase standalone site deployed to GitHub Pages

## Draft changelog - fixes

- 23212b4 fix(playground): skip requestInterceptor for spec URL fetch
- 8bdc356 fix(playground): use unique dom_id and immediate IIFE for Swagger UI init
- fe7d7ac fix(playground): inline Swagger UI loading on playground pages
- 75ea1c8 fix(playground): rewrite api-playground.js for MkDocs Material instant loading
- 67d8396 fix(playground): serve bundled OpenAPI as JSON for Swagger UI
- bf180f9 fix(playground): bundle OpenAPI spec for Swagger UI compatibility
- a2ad5e5 fix(playground): resolve spec URL for GitHub Pages subdirectory deploy

## Draft changelog - documentation

- f40dc7c docs: rewrite Acme demo site with LLM-written Stripe-quality content
- 0a24e3a docs: update pricing to value-based model ($149-$1,499/mo)
- 2d40ddc docs: restructure product strategy to per-repo pricing model
- ffc63f9 docs: add premium retainer tiers to product strategy
- 53b0fc7 docs: add product strategy for three-tier architecture
- 74dbe4e docs(demo): add webhook processing pipeline how-to with interactive diagram
- 651d947 docs(api-first): refresh taskstream playground and published sandbox

<!-- vale Google.Units = YES -->

## Potential breaking changes

- none

## Migration Notes Checklist

- [ ] Identify impacted API endpoints and SDK methods.
- [ ] Add before/after request and response examples.
- [ ] Include rollout and rollback instructions.
- [ ] Include compatibility matrix and deprecation dates.

## Breaking Change Acceptance Checklist

- [ ] Every breaking change has mitigation guidance.
- [ ] Every breaking change has a migration path.
- [ ] Every breaking change has a test plan.
- [ ] Customer communication snippets are prepared.

## Next steps

- [Documentation index](../index.md)

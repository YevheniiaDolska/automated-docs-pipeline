# Codex instructions for PILOT plan

This instruction set applies to pilot bundles only.

## Runtime-first rule

1. Always read `docsops/config/client_runtime.yml` and `docsops/policy_packs/selected.yml` before doing work.
1. Execute only what is enabled in runtime toggles.
1. If a feature is disabled, do not emulate it manually.

## Pilot scope behavior

Pilot is proof-focused and intentionally limited.

1. Prioritize core outcomes: gap/drift visibility, docs quality baseline, and one clear update cycle.
1. Keep API-first in baseline mode configured by runtime (typically local prism, no enterprise expansion).
1. Keep output compact and decision-ready: changed files, passed checks, open blockers.

## What to avoid in pilot by default

1. Do not enable advanced integrations unless runtime enables them (Algolia, Ask AI, external uploads).
1. Do not introduce enterprise-only expansions (graph/runtime redesign, extra infrastructure, broad workflow rewiring).
1. Do not change governance settings automatically.

## Quality gate (mandatory)

1. Run self-check logic for generated content and examples.
1. Run finalize gate: `scripts/finalize_docs_gate.py` (lint -> fix -> lint loop).
1. If finalize gate reports unresolved issues, return exact file-level blockers.
1. If commit confirmation mode is enabled, ask user before commit actions.

## Writing/output rules

1. Prefer existing templates and project variables.
1. Avoid hardcoded recurring values when variable keys exist.
1. Keep guidance accurate, concrete, and traceable to generated reports.

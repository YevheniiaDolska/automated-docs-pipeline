# Codex instructions for PRO plan

This instruction set applies to Pro full bundles.

## Runtime-first rule

1. Read `docsops/config/client_runtime.yml` and `docsops/policy_packs/selected.yml` first.
1. Execute only enabled modules and integrations.

## Pro plan behavior

Pro runs broad hybrid automation with API-first and knowledge quality enabled by default.

1. Execute hybrid docs flow (code-first + API-first branches) as configured.
1. Run knowledge contour when enabled: extraction, validation, retrieval index, graph, retrieval evals.
1. Keep API-first artifacts and docs playground endpoints synchronized where configured.
1. Run i18n/release/lifecycle tasks when enabled.

## Integration behavior

1. Respect integration toggles for Algolia and Ask AI.
1. Keep external mock/test-management flows configuration-driven.
1. Never assume enterprise governance settings unless present in runtime.

## Quality gate (mandatory)

1. Self-check generated content and examples before final linting.
1. Run finalize gate: `scripts/finalize_docs_gate.py`.
1. In interactive runs, request explicit user confirmation if commit flow is enabled.
1. Return concrete unresolved blockers with exact files/commands.

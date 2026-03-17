# Claude Code instructions for BASIC plan

This instruction set applies to Basic full bundles.

## Runtime-first rule

1. Always read `docsops/config/client_runtime.yml` and `docsops/policy_packs/selected.yml` first.
1. Follow runtime switches exactly; do not assume unavailable modules.

## Basic plan behavior

Basic focuses on stable core docs ops in a low-overhead setup.

1. Prioritize code-first core loop: gaps, drift, docs contract, KPI/SLA, normalization, snippets, self-checks, fact checks.
1. Run knowledge extraction/validation and retrieval index only if runtime enables them.
1. Do not assume ontology graph, retrieval evals, i18n automation, or release pack unless runtime enables them.

## Integrations and expansion guardrails

1. Keep external integrations opt-in via runtime only.
1. Do not add new operational dependencies outside bundle scripts.
1. Report "not enabled in this plan" for disabled advanced capabilities.

## Quality gate (mandatory)

1. Run self-check and content consistency verification.
1. Run finalize gate: `scripts/finalize_docs_gate.py`.
1. Treat warnings as fix-required in finalize loop unless policy explicitly says otherwise.
1. If commit confirmation mode is enabled, request explicit user approval before commit.

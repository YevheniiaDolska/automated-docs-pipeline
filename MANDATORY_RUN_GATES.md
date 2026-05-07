# Mandatory run gates

This file defines the non-skippable gate chain for every autopipeline run.

The objective is to enforce quality and RAG hardening in code, not only in prompt text.

## Scope model

Tiers are canonical:

1. `pilot`
1. `full`
1. `full+rag`
1. `community` (degraded fallback)

Resolution order in gate runner:

1. CLI `--tier` (if not `auto`)
1. `scripts/license_gate.py` plan mapping (`pilot` -> `pilot`, `professional` -> `full`, `enterprise` -> `full+rag`)
1. Runtime fallback from `docsops/config/client_runtime.yml`

## Command

```bash
python3 scripts/run_mandatory_gates.py --tier auto --strict
```

Report path:

- `reports/mandatory_run_gates_report.json`

## Gate matrix by tier

## `community`

Required:

1. Baseline quality gate:
   - `npm run validate:minimal`

Notes:

- This is degraded fallback mode after license/tier degradation.
- Advanced DocsOps and RAG-prep gates are not enforced in community mode.

## `pilot`

Pilot is broader than community and acts as a production-like pipeline demo
without retrieval-time RAG runtime.

Required sequence:

1. Baseline + full docs quality:
   - `npm run validate:minimal`
   - `npm run lint`
1. RAG preparation (no retrieval-time runtime):
   - `python3 scripts/extract_knowledge_modules_from_docs.py --docs-dir docs --modules-dir knowledge_modules --report reports/knowledge_auto_extract_report.json`
   - `python3 scripts/validate_knowledge_modules.py`
1. Separate hardening controls:
   - stale-check: `python3 scripts/generate_kpi_wall.py --docs-dir docs --reports-dir reports --stale-days 90`
   - contradiction-check: `python3 scripts/detect_rag_contradictions.py --report reports/rag_contradictions_report.json`
1. Critical contradiction exclusion from retrieval index:
   - `python3 scripts/generate_knowledge_retrieval_index.py --modules-dir knowledge_modules --output docs/assets/knowledge-retrieval-index.json --contradictions-report reports/rag_contradictions_report.json --exclude-critical-contradictions`
1. Optional (module-gated in runtime profile):
   - knowledge graph build (`modules.ontology_graph`)
   - retrieval eval gate (`modules.retrieval_evals`)

## `full`

Required sequence:

1. Baseline + full docs quality:
   - `npm run validate:minimal`
   - `npm run lint`
1. Knowledge preparation:
   - `python3 scripts/extract_knowledge_modules_from_docs.py --docs-dir docs --modules-dir knowledge_modules --report reports/knowledge_auto_extract_report.json`
   - `python3 scripts/validate_knowledge_modules.py`
1. Separate hardening controls:
   - stale-check: `python3 scripts/generate_kpi_wall.py --docs-dir docs --reports-dir reports --stale-days 90`
   - contradiction-check: `python3 scripts/detect_rag_contradictions.py --report reports/rag_contradictions_report.json`
1. Critical contradiction exclusion from retrieval index:
   - `python3 scripts/generate_knowledge_retrieval_index.py --modules-dir knowledge_modules --output docs/assets/knowledge-retrieval-index.json --contradictions-report reports/rag_contradictions_report.json --exclude-critical-contradictions`
1. Knowledge graph (when `modules.ontology_graph: true`):
   - `python3 scripts/generate_knowledge_graph_jsonld.py ...`
1. Retrieval eval gate (when `modules.retrieval_evals: true`):
   - `python3 scripts/run_retrieval_evals_gate.py`

## `full+rag`

All `full` gates, plus runtime guardrail presence checks:

1. `runtime/ask-ai-pack/app/retrieval.py` exists
1. `runtime/ask-ai-pack/app/main.py` exists

This validates that retrieval-time layer is present in the delivered implementation.

## Strict mode behavior

`--strict` enforces module expectations for the selected tier.

Example:

- If `tier=full` and `runtime.modules.ontology_graph=false`, gate fails in strict mode.

## Integration recommendation

Call this gate script at the end of autopipeline and before review/finalize steps:

```bash
python3 scripts/run_autopipeline.py --docsops-root docsops --reports-dir reports --auto-generate
python3 scripts/run_mandatory_gates.py --tier auto --strict
```

In current runtime, autopipeline invokes mandatory gates internally and runs remediation loops before finalizing reports.

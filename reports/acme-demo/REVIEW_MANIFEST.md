---
title: "Review Manifest"
description: "Pipeline review manifest listing available and missing artifacts with stage summary and reviewer checklist."
content_type: reference
product: both
---

# Review Manifest

- Runtime config: `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/client_runtime.yml`
- Weekly run rc: `1`
- Strictness: `standard`
- Available artifacts: `15`
- Missing artifacts: `12`

## Stage Summary

- `multi_protocol_contract`: **OK** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/multi_protocol_contract_report.json`)
- `consolidated_report`: **MISSING** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/consolidated_report.json`)
- `audit_scorecard`: **MISSING** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/audit_scorecard.json`)
- `finalize_gate`: **MISSING** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/finalize_gate_report.json`)
- `kpi_wall`: **OK** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/kpi-wall.json`)
- `kpi_sla`: **MISSING** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/kpi-sla-report.json`)
- `retrieval_evals`: **OK** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/retrieval_evals_report.json`)

## Review Links (Available)

- [Docs index](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/index.md) - `docs`
- [Faceted search page](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/search-faceted.md) - `docs`
- [Facets index](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/assets/facets-index.json) - `search`
- [Multi-protocol contract report](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/multi_protocol_contract_report.json) - `protocols`
- [GraphQL reference](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/reference/graphql-api.md) - `protocols`
- [AsyncAPI reference](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/reference/asyncapi-api.md) - `protocols`
- [REST playground](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/reference/taskstream-api-playground.md) - `protocols`
- [Glossary source](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/glossary.yml) - `quality`
- [Glossary sync report](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/glossary_sync_report.json) - `quality`
- [KPI wall](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/kpi-wall.json) - `quality`
- [RAG retrieval index](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/assets/knowledge-retrieval-index.json) - `rag`
- [RAG knowledge graph](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/assets/knowledge-graph.jsonld) - `rag`
- [Knowledge graph report](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/knowledge_graph_report.json) - `rag`
- [Retrieval eval report](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/retrieval_evals_report.json) - `rag`
- [Retrieval eval dataset](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/retrieval_eval_dataset.generated.yml) - `rag`

## Expected But Missing

- `Consolidated report` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/consolidated_report.json`
- `Audit scorecard (JSON)` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/audit_scorecard.json`
- `Audit scorecard (HTML)` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/audit_scorecard.html`
- `Finalize gate report` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/finalize_gate_report.json`
- `DocsOps status` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/docsops_status.json`
- `Ready marker` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/READY_FOR_REVIEW.txt`
- `API test cases JSON` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/api-test-assets/api_test_cases.json`
- `TestRail CSV` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/api-test-assets/testrail_test_cases.csv`
- `Zephyr JSON` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/api-test-assets/zephyr_test_cases.json`
- `Test coverage report` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/api-test-assets/coverage_report.json`
- `Fuzz scenarios` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/api-test-assets/fuzz_scenarios.json`
- `KPI SLA report` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/kpi-sla-report.json` (module: `kpi_sla`)

## Reviewer Checklist

- Confirm stage summary has no missing required artifacts.
- Review protocol docs and test assets links.
- Review quality and retrieval reports before publish.
- Approve publish only if critical findings are resolved.

## Next steps

- [Documentation index](../index.md)

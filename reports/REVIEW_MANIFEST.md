# Review Manifest

- Runtime config: `C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\docsops\config\client_runtime.yml`
- Weekly run rc: `0`
- Strictness: `standard`
- Available artifacts: `14`
- Missing artifacts: `10`

## Stage Summary

- `multi_protocol_contract`: **OK** (`C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\multi_protocol_contract_report.json`)
- `consolidated_report`: **OK** (`C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\consolidated_report.json`)
- `audit_scorecard`: **MISSING** (`C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\audit_scorecard.json`)
- `finalize_gate`: **MISSING** (`C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\finalize_gate_report.json`)
- `docsops_status`: **OK** (`C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\docsops_status.json`)
- `ready_marker`: **OK** (`C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\READY_FOR_REVIEW.txt`)
- `code_traceability`: **MISSING** (`C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\code_traceability_index.json`)
- `kpi_wall`: **OK** (`C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\kpi-wall.json`)
- `kpi_sla`: **OK** (`C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\kpi-sla-report.json`)
- `glossary_sync`: **OK** (`C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\glossary_sync_report.json`)
- `test_assets_json`: **MISSING** (`C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\api-test-assets\api_test_cases.json`)
- `test_assets_coverage`: **MISSING** (`C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\api-test-assets\coverage_report.json`)
- `test_assets_fuzz`: **MISSING** (`C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\api-test-assets\fuzz_scenarios.json`)
- `test_assets_summary`: **MISSING** (`C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\api-test-assets\TEST_ASSETS_SUMMARY.md`)

## Review Links (Available)

- [Consolidated report](C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\consolidated_report.json) - `reports`
- [VeriOps status](C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\docsops_status.json) - `reports`
- [Ready marker](C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\READY_FOR_REVIEW.txt) - `reports`
- [VeriDoc branding policy report](C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\veridoc_branding_policy_report.json) - `reports`
- [Docs index](C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\docs\index.md) - `docs`
- [Faceted search page](C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\docs\search-faceted.md) - `search`
- [Facets index](C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\docs\assets\facets-index.json) - `search`
- [Multi-protocol contract report](C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\multi_protocol_contract_report.json) - `protocols`
- [REST reference](C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\docs\reference\rest-api.md) - `protocols`
- [REST playground](C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\docs\reference\taskstream-api-playground.md) - `protocols`
- [Glossary source](C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\glossary.yml) - `quality`
- [Glossary sync report](C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\glossary_sync_report.json) - `quality`
- [KPI wall](C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\kpi-wall.json) - `quality`
- [KPI SLA report](C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\kpi-sla-report.json) - `quality`

## Expected But Missing

- `Audit scorecard (JSON)` -> `C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\audit_scorecard.json`
- `Audit scorecard (HTML)` -> `C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\audit_scorecard.html`
- `Finalize gate report` -> `C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\finalize_gate_report.json`
- `Generated changes list` -> `C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\generated_changes.json`
- `API test cases JSON` -> `C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\api-test-assets\api_test_cases.json`
- `TestRail CSV` -> `C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\api-test-assets\testrail_test_cases.csv`
- `Zephyr JSON` -> `C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\api-test-assets\zephyr_test_cases.json`
- `Test coverage report` -> `C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\api-test-assets\coverage_report.json`
- `Fuzz scenarios` -> `C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\api-test-assets\fuzz_scenarios.json`
- `Test assets summary` -> `C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\api-test-assets\TEST_ASSETS_SUMMARY.md`

## Reviewer Checklist

- Confirm stage summary has no missing required artifacts.
- Review protocol docs and test assets links.
- Review quality and retrieval reports before publish.
- Approve publish only if critical findings are resolved.

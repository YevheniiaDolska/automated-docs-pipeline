# Review Manifest

- Runtime config: `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docsops/config/client_runtime.yml`
- Weekly run rc: `0`
- Strictness: `standard`
- Available artifacts: `23`
- Missing artifacts: `1`

## Stage Summary

- `multi_protocol_contract`: **OK** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/multi_protocol_contract_report.json`)
- `consolidated_report`: **OK** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/consolidated_report.json`)
- `audit_scorecard`: **OK** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/audit_scorecard.json`)
- `finalize_gate`: **OK** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/finalize_gate_report.json`)
- `docsops_status`: **OK** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/docsops_status.json`)
- `ready_marker`: **OK** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/READY_FOR_REVIEW.txt`)
- `kpi_wall`: **OK** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/kpi-wall.json`)
- `kpi_sla`: **OK** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/kpi-sla-report.json`)
- `glossary_sync`: **OK** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/glossary_sync_report.json`)
- `test_assets_json`: **OK** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/api-test-assets/api_test_cases.json`)
- `test_assets_coverage`: **OK** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/api-test-assets/coverage_report.json`)
- `test_assets_fuzz`: **OK** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/api-test-assets/fuzz_scenarios.json`)
- `test_assets_summary`: **MISSING** (`/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/api-test-assets/TEST_ASSETS_SUMMARY.md`)

## Review Links (Available)

- [Consolidated report](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/consolidated_report.json) - `reports`
- [Audit scorecard (JSON)](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/audit_scorecard.json) - `reports`
- [Audit scorecard (HTML)](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/audit_scorecard.html) - `reports`
- [Finalize gate report](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/finalize_gate_report.json) - `reports`
- [VeriOps status](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/docsops_status.json) - `reports`
- [Ready marker](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/READY_FOR_REVIEW.txt) - `reports`
- [Generated changes list](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/generated_changes.json) - `reports`
- [VeriDoc branding policy report](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/veridoc_branding_policy_report.json) - `reports`
- [Docs index](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/index.md) - `docs`
- [Faceted search page](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/search-faceted.md) - `search`
- [Facets index](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/assets/facets-index.json) - `search`
- [Multi-protocol contract report](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/multi_protocol_contract_report.json) - `protocols`
- [REST reference](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/reference/rest-api.md) - `protocols`
- [REST playground](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/docs/reference/taskstream-api-playground.md) - `protocols`
- [API test cases JSON](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/api-test-assets/api_test_cases.json) - `tests`
- [TestRail CSV](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/api-test-assets/testrail_test_cases.csv) - `tests`
- [Zephyr JSON](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/api-test-assets/zephyr_test_cases.json) - `tests`
- [Test coverage report](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/api-test-assets/coverage_report.json) - `tests`
- [Fuzz scenarios](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/api-test-assets/fuzz_scenarios.json) - `tests`
- [Glossary source](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/glossary.yml) - `quality`
- [Glossary sync report](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/glossary_sync_report.json) - `quality`
- [KPI wall](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/kpi-wall.json) - `quality`
- [KPI SLA report](/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/kpi-sla-report.json) - `quality`

## Expected But Missing

- `Test assets summary` -> `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/api-test-assets/TEST_ASSETS_SUMMARY.md`

## Reviewer Checklist

- Confirm stage summary has no missing required artifacts.
- Review protocol docs and test assets links.
- Review quality and retrieval reports before publish.
- Approve publish only if critical findings are resolved.

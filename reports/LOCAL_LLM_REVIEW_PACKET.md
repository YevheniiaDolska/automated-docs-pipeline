# Local LLM Review Packet

Use this packet after autopipeline run.

- Runtime config: `C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\docsops\config\client_runtime.yml`
- Consolidated report: `C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\consolidated_report.json`
- Multi-protocol report: `C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\multi_protocol_contract_report.json`
- Audit scorecard: `C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\audit_scorecard.json`
- Review manifest: `C:\Users\Kroha\Documents\development\Auto-Doc Pipeline\reports\REVIEW_MANIFEST.md`

Prompt for local LLM:

```text
Analyze reports as a strict docs-ops reviewer. List critical/major findings, provide exact remediation actions, and confirm publish readiness.
Evaluate report quality, drift, risks, and publish readiness.
Output: 1) critical issues, 2) exact fixes, 3) final go/no-go.
```

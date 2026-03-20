---
title: "Local LLM Review Packet"
description: "Review packet with report paths and prompts for local LLM-based documentation quality analysis."
content_type: reference
product: both
---

# Local LLM Review Packet

Use this packet after autopipeline run.

- Runtime config: `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/client_runtime.yml`
- Consolidated report: `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/consolidated_report.json`
- Multi-protocol report: `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/multi_protocol_contract_report.json`
- Audit scorecard: `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/audit_scorecard.json`
- Review manifest: `/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline/reports/acme-demo/REVIEW_MANIFEST.md`

Prompt for local LLM:

```text
Analyze reports as a strict docs-ops reviewer. List critical/major findings, provide exact remediation actions, and confirm publish readiness.
Evaluate report quality, drift, risks, and publish readiness.
Output: 1) critical issues, 2) exact fixes, 3) final go/no-go.
```

## Next steps

- [Documentation index](../index.md)

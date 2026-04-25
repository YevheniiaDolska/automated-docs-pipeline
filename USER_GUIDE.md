# User guide

This is the canonical day-to-day usage guide.

## Weekly operation model

1. Scheduler or manual trigger runs autopipeline.
1. Reports are generated in `reports/`.
1. Team reviews consolidated output and applies approved changes.
1. Quality gates run before merge/release.

## Manual run commands

```bash
python3 scripts/run_autopipeline.py --docsops-root docsops --reports-dir reports --auto-generate
npm run lint
```

## API-first flows

- REST flow: `python3 scripts/run_api_first_flow.py ...`
- Multi-protocol flow (GraphQL/gRPC/AsyncAPI/WebSocket):

```bash
python3 scripts/run_multi_protocol_contract_flow.py --runtime-config docsops/config/client_runtime.yml --reports-dir reports
```

## RAG preparation and runtime behavior

1. Docs are normalized and validated.
1. Knowledge modules are extracted with metadata.
1. Stale and contradiction checks run before indexing.
1. Critical conflicts are excluded from retrieval index.
1. Retrieval index and knowledge graph are rebuilt.
1. Retrieval eval gates check precision/recall/hallucination.
1. Runtime uses low-confidence guardrails and contradiction warnings.
1. Usage and feedback logs are captured for iterative improvement.

## Where to inspect outputs

- `reports/consolidated_report.json`
- `reports/rag_contradictions_report.json`
- `reports/stale_docs_report.json`
- `reports/ask_ai_usage.jsonl`
- `reports/ask_ai_feedback.jsonl`

## Escalation guidance

Escalate when:

1. Quality gates fail repeatedly.
1. API-first flow breaks in production config.
1. Retrieval warnings indicate persistent contradictions.

Use `docs/operations/OPERATOR_RUNBOOK.md` for incident procedures.

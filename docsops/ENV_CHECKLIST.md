# ENV_CHECKLIST

Set these environment variables in local shell and CI secrets.

## Core

- [ ] `GITHUB_TOKEN` (normally auto-provided in GitHub Actions)

## API external sandbox

- This is a one-time setup. After that, weekly/API-first flow updates mock automatically.
- Provider: `postman`

Give these inputs to the pipeline:
- [ ] `POSTMAN_API_KEY`: Postman API key (required)
- [ ] `POSTMAN_WORKSPACE_ID`: Postman workspace id (required for auto-create mode)
- [ ] `POSTMAN_COLLECTION_UID`: Postman collection uid (optional; if missing, pipeline imports collection from generated OpenAPI)
- [ ] `POSTMAN_MOCK_SERVER_ID`: existing Postman mock id (optional, to reuse existing mock)

How it works:
- If mock id is provided, pipeline reuses that mock and resolves URL automatically.
- If mock id is empty, pipeline creates/updates collection from generated OpenAPI, then creates mock.
- Resolved URL is written into docs playground endpoint via `sync_playground_endpoint`.

## Verification

- [ ] Run one weekly cycle and check `reports/consolidated_report.json` timestamp.
- [ ] Ensure there are no missing-secret errors in `reports/docsops-weekly.log`.

# API-first live demo

Run a client-facing API-first live demo with the same presentation style as `/demo`:

- clear phase framing;
- concise English narration for each stage;
- compact, readable command output (no overwhelming raw lint logs);
- final sandbox URL and mock-live confirmation.

## Trigger contract

- Claude command: `/api-first-demo`
- Codex trigger: `api-first demo live`

## Execution mode

Run autonomously. Do not ask for per-step confirmations.

## Stage script

1. Say: "I will run an end-to-end API-first flow and narrate each stage in English."
1. Say: "I will show planning notes to OpenAPI generation, contract checks, mock-backed user-path verification, and published MkDocs sandbox verification."
1. Say: "Knowledge/retrieval/graph stages are platform-level quality artifacts and are not injected into API page content."
1. Run:

```bash
cd "/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline"
npm run api-first-demo
```

For no-Docker/public sandbox mode:

```bash
cd "/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline"
API_FIRST_DEMO_SANDBOX_BACKEND=external \
API_FIRST_DEMO_MOCK_BASE_URL="https://sandbox-api.example.com/v1" \
npm run api-first-demo
```

If `API_FIRST_DEMO_MOCK_BASE_URL` is not set, demo auto-reads `mkdocs.yml` playground `sandbox_base_url`.

For fully automated Postman external mock mode:

```bash
cd "/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline"
API_FIRST_DEMO_SANDBOX_BACKEND=external \
API_FIRST_DEMO_AUTO_PREPARE_EXTERNAL_MOCK=true \
POSTMAN_API_KEY="YOUR_POSTMAN_API_KEY" \
POSTMAN_WORKSPACE_ID="YOUR_WORKSPACE_ID" \
npm run api-first-demo
```

Optional:

- `POSTMAN_COLLECTION_UID` to reuse a specific collection (otherwise demo imports from generated OpenAPI).
- `POSTMAN_MOCK_SERVER_ID` to reuse an existing mock.

1. While running, narrate the meaning of each stage in short English sentences:
   - Stage 0: planning notes to OpenAPI generation;
   - Stage 1: mock sandbox startup;
   - Stage 2-5: API-first flow (contract/lint/stubs/user-path checks/docs assets);
   - Stage 6: multilingual API examples baseline;
   - Stage 7: glossary sync as terminology governance layer;
   - Stage 8: retrieval evals as knowledge-system quality telemetry;
   - Stage 9: JSON-LD knowledge graph generation as separate artifact;
   - Stage 10: commit and push generated API-first demo output;
   - Stage 11: wait for successful `deploy.yml` run;
   - Stage 12: verify published MkDocs sandbox page and endpoint wiring.
1. End with:
   - sandbox page URL;
   - deploy success confirmation;
   - mock status and stop command.

## Final message (required)

Use this exact operational close:

- "Live API-first demo completed."
- "Sandbox page: <printed URL>"
- "Published deploy: success"
- "Mock status: running"
- "Stop command: `npm run api-first-demo:stop`"

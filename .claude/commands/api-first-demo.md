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

1. Say: "I will run a nine-stage API-first flow and narrate each stage in English."
1. Say: "I will show the exact planning notes input format first, then run validation, linting, stub generation, user-path checks, multilingual examples, glossary sync, retrieval evals, and JSON-LD graph generation."
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

1. While running, narrate the meaning of each stage in short English sentences:
   - Stage 0: planning notes to OpenAPI generation;
   - Stage 1: mock sandbox startup;
   - Stage 2-5: API-first flow (contract/lint/stubs/user-path checks/docs assets);
   - Stage 6: multilingual examples baseline;
   - Stage 7: glossary sync (`sync_project_glossary.py`);
   - Stage 8: retrieval evals (Precision/Recall/Hallucination-rate);
   - Stage 9: JSON-LD knowledge graph generation.
1. End with:
   - sandbox page URL;
   - confirmation that the mock server is still running for the client walkthrough;
   - stop command.

## Final message (required)

Use this exact operational close:

- "Live API-first demo completed."
- "Sandbox page: <printed URL>"
- "Mock status: running"
- "Stop command: `npm run api-first-demo:stop`"

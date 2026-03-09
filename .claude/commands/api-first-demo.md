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

1. Say: "I will run a five-stage API-first flow and narrate each stage in English."
1. Say: "I will show the exact planning notes input format first, then run validation, linting, stub generation, user-path checks, and docs publishing."
1. Run:

```bash
cd "/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline"
npm run api-first-demo
```

1. While running, narrate the meaning of each stage in short English sentences:
   - Stage 0: mock sandbox startup;
   - Stage 1: contract structure validation;
   - Stage 2: lint stack (Spectral, Redocly, Swagger CLI);
   - Stage 3: server stub generation;
   - Stage 4: self-verification against live mock + docs assets;
   - Stage 5: documentation quality checks (when enabled).
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

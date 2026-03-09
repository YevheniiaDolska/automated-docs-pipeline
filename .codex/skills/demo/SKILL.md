---
name: demo
description: Run a live Auto-Doc Pipeline demo. Supports standard docs demo and API-first live demo triggers.
---

# Demo skill

Use this skill when the user asks for one of these triggers:

- `demo` or `$demo`
- `api-first demo live`

## Trigger behavior

1. If trigger is `api-first demo live`:
   - Follow `.claude/commands/api-first-demo.md`.
   - Run `bash scripts/api_first_demo_live.sh`.
   - Keep mock sandbox running after completion.
   - Narrate all stages in concise English, in the same style as regular `demo`.
   - Keep narration human-readable and compact so users do not need to expand long raw logs.
   - Print final sandbox URL and confirm mock is still running.

1. If trigger is `demo` or `$demo`:
   - Follow `.claude/commands/demo.md`.
   - Treat optional user text after `demo` as a topic override.

## Execution rules

1. Execute steps in order and do not skip validation.
1. Run autonomously without per-step user confirmations.
1. If any step/check/deploy fails, remediate in a loop until successful.

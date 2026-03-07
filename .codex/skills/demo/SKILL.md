---
name: demo
description: Run a live Auto-Doc Pipeline demonstration workflow when the user asks for demo or $demo in Codex.
---

# Demo skill

Use this skill when the user asks for `demo` or `$demo`.

## What to do

1. Treat optional user text after `demo` as a topic override.
1. Follow the workflow in `.claude/commands/demo.md`.
1. Execute steps in order and do not skip validation.
1. Run autonomously without per-step user confirmations.
1. If any step/check/deploy fails, remediate and continue in a loop until deploy succeeds.

## Input handling

- No argument: use the default topic from `.claude/commands/demo.md`.
- With argument: adapt title, content type, and slug to the provided topic.

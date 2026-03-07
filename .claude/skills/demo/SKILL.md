---
name: demo
description: Run a live Auto-Doc Pipeline demonstration workflow when the user asks for /demo.
---

# Demo skill

Run this workflow when the user invokes `/demo` or asks to run the pipeline demo.

## Source of truth

Follow the exact demo procedure from `.claude/commands/demo.md`.

## Behavior

1. If arguments are provided after `/demo`, use them as a custom topic.
1. If no arguments are provided, use the default webhook topic.
1. Execute steps in order and do not skip validation commands.
1. If a command fails, stop and report the exact failing command and minimal fix.

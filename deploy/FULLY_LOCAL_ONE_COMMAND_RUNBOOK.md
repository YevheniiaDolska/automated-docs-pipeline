---
title: "Fully Local One Command Runbook"
description: "One-command setup to prepare Ollama and veridoc-writer for fully local docs generation in client environment."
date: "2026-03-31"
last_reviewed: "2026-03-31"
---

<!-- cspell:ignore Ollama qwen Modelfile -->

# Fully Local One-Command Runbook

Goal: start client bundle in fully local mode (air-gapped style) with `veridoc-writer`.

## 1) From client repo root

```bash
python3 docsops/scripts/setup_client_env_wizard.py
```

What this wizard does:

1. Creates/updates `.env.docsops.local`.
1. Installs Ollama if missing.
1. Pulls base model (`qwen3:30b` by default).
1. Generates `docsops/ollama/Modelfile` from `LOCAL_MODEL.md` + `AGENTS.md` + `CLAUDE.md`.
1. Creates local model profile `veridoc-writer`.

After success, local model command is:

```bash
ollama run veridoc-writer
```

## 2) Install weekly scheduler once

Linux/macOS:

```bash
bash docsops/ops/install_cron_weekly.sh
```

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File docsops/ops/install_windows_task.ps1
```

## 3) What weekly run executes automatically

The scheduled job runs:

1. `run_autopipeline.py` (collect + validate + consolidate reports)
1. `docsops_generate.py --auto` (local-first generation)
1. In fully local mode: local model first, no external egress by default.

## 4) If preflight fails

Run manually:

```bash
ollama pull qwen3:30b
ollama create veridoc-writer -f docsops/ollama/Modelfile
```

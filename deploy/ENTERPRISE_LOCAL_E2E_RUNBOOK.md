---
title: "Enterprise Local E2E Runbook"
description: "Step-by-step runbook to validate enterprise bundle delivery, local setup, and scheduled local generation."
date: "2026-03-31"
last_reviewed: "2026-03-31"
---

<!-- cspell:ignore Ollama qwen Modelfile -->

# Enterprise Bundle Test Runbook (Wizard-First)

This runbook matches your required path:

1. Build an Enterprise bundle.
1. Deliver it to an empty folder (client-like machine).
1. Run in test mode without binding to a real client repository.

## 0. What you use

1. Profile wizard file: `scripts/onboard_client.py --mode bundle-only`
1. Bundle build: `python3 -m scripts.build_client_bundle --client <profile>`
1. Client-side run: `docsops/ops/run_weekly_docsops.sh` or `.ps1`

## 1. Operator machine: start built-in wizard (question flow)

Run from the master repo:

```bash
cd "/mnt/c/Users/Kroha/Documents/development/Auto-Doc Pipeline"
python3 scripts/onboard_client.py --mode bundle-only
```

In wizard answers:

1. `Delivery mode`: `bundle-only`
1. `Profile source`: `preset`
1. `Choose preset`: `enterprise`
1. Skip local repo/scheduler questions (not needed in bundle-only mode)
1. `Target folder`: `docsops`

This creates a profile and builds handoff-ready bundle without local install.

Generated profile path is printed in console, usually:

`profiles/clients/generated/<client_id>.client.yml`

Alternative (low-level same wizard):
`python3 scripts/provision_client_repo.py --interactive --generate-profile`

## 2. Operator machine: build handoff bundle explicitly

Use the generated profile from step 1:

```bash
python3 -m scripts.build_client_bundle --client profiles/clients/generated/<client_id>.client.yml
```

Bundle output:

`generated/client_bundles/<client_id>/`

Optional: if you want encrypted capability pack during build, set key before build:

```bash
export VERIOPS_LICENSE_KEY='<your_hex_key>'
```

## 3. Simulate client machine with an empty folder

Create empty folder (this is your client-like sandbox):

```bash
rm -rf /tmp/veridoc-client-empty
mkdir -p /tmp/veridoc-client-empty
```

Copy bundle as `docsops` (exactly how client receives it):

```bash
cp -R generated/client_bundles/<client_id> /tmp/veridoc-client-empty/docsops
cd /tmp/veridoc-client-empty
```

## 4. Client-side local prerequisites

In `/tmp/veridoc-client-empty`:

1. Run client secrets wizard (recommended):

```bash
python3 docsops/scripts/setup_client_env_wizard.py
```

This wizard now also supports fully local mode bootstrap:

1. Installs Ollama (if missing).
1. Pulls local base model (default `qwen3:30b`).
1. Generates `docsops/ollama/Modelfile` from `docsops/LOCAL_MODEL.md`.
1. Creates local profile model `veridoc-writer` (run with `ollama run veridoc-writer`).

1. If you prefer manual setup, create local env from template:

```bash
cp docsops/.env.docsops.local.template .env.docsops.local
```

1. Enable test plan override (so local tests are not blocked by license tier):

```bash
echo "VERIOPS_LICENSE_PLAN=enterprise" >> .env.docsops.local
```

1. Add at least one LLM key in `.env.docsops.local` if generation path needs it.

## 5. Create minimal test project skeleton (no real repo needed)

```bash
mkdir -p docs api sdk reports
cat > docs/index.md <<'EOF'
# Sandbox docs
This is a local sandbox to validate bundle behavior.
EOF
cat > mkdocs.yml <<'EOF'
site_name: Sandbox Docs
nav:
  - Home: index.md
EOF
cat > glossary.yml <<'EOF'
terms: {}
EOF
```

## 6. Test run as client

Linux/macOS:

```bash
bash docsops/ops/run_weekly_docsops.sh
```

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File docsops/ops/run_weekly_docsops.ps1
```

Note: weekly runner now executes:
`run_autopipeline -> consolidated report -> docsops_generate`
so local generation runs automatically in the same scheduled cycle.

Expected primary artifact:

`reports/consolidated_report.json`

## 7. Test zero-config LLM behavior

Open LLM in `/tmp/veridoc-client-empty` and use plain prompts, for example:

1. `Generate a how-to guide for enterprise webhook setup.`
1. `Update API docs from planning notes and run all pipeline checks.`

Expected behavior:

1. User does not provide orchestration commands.
1. LLM runs pipeline scripts itself.
1. LLM returns changed files and artifact paths.

## 8. What to verify before repeating for real repos

1. `docsops/config/client_runtime.yml` exists and matches enterprise profile.
1. `docsops/policy_packs/selected.yml` is enterprise-grade.
1. `docsops/AGENTS.md` and `docsops/CLAUDE.md` are present.
1. `reports/consolidated_report.json` is refreshed by run.
1. No missing-secret blockers in output/log.

## 9. Fast fallback (single wizard command)

If you want full same-machine install in one pass (without separate handoff simulation):

```bash
python3 scripts/onboard_client.py
```

Your requested delivery simulation is sections 1-8 above.

## 10. Switch plan safely (Pilot -> Enterprise)

You can test all plans on the same machine and then switch to Enterprise.

Important:

1. Replacing `docsops/` is the plan switch.
1. Reinstall scheduler after switch if scheduler was enabled.

### Linux/macOS switch commands

From client repo root:

```bash
rm -rf docsops
cp -R /path/to/generated/client_bundles/<enterprise_client_id> docsops
cp -f docsops/.env.docsops.local.template .env.docsops.local
bash docsops/ops/install_cron_weekly.sh
```

### Windows PowerShell switch commands

From client repo root:

```powershell
if (Test-Path .\docsops) { Remove-Item .\docsops -Recurse -Force }
Copy-Item "C:\path\to\generated\client_bundles\<enterprise_client_id>" .\docsops -Recurse -Force
Copy-Item .\docsops\.env.docsops.local.template .\.env.docsops.local -Force
powershell -ExecutionPolicy Bypass -File .\docsops\ops\install_windows_task.ps1
```

### Scheduler automation note

1. In `install-local` wizard mode, scheduler install is automatic.
1. In `bundle-only` mode (manual unpack), scheduler install is manual (one command above).
1. Reinstall is safe: installer scripts use stable task names/markers and overwrite/update existing schedule entries.

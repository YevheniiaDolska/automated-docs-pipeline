# Weekly automation runbook

Client first step (set secrets interactively):
1. Run `python3 docsops/scripts/setup_client_env_wizard.py` once.

If fully-local mode is selected, setup wizard can also install Ollama,
pull the base model, and create `veridoc-writer` from `docsops/LOCAL_MODEL.md`.

Linux:
1. Run `bash docsops/ops/install_cron_weekly.sh` once.

macOS:
1. Run `bash docsops/ops/install_macos_launchd.sh` once.

Windows:
1. Run `powershell -ExecutionPolicy Bypass -File docsops/ops/install_windows_task.ps1` once.

Scheduled run executes full chain:
`run_autopipeline -> consolidated report -> docsops_generate`.

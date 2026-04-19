# Capability Catalog Full Test Report

Source: docs/operations/PIPELINE_CAPABILITIES_CATALOG.md

Total capabilities tested: 161
PASS: 97
PASS_COMPILE_ONLY: 1
FAIL: 56
TIMEOUT: 7

## docker_runtime (16)

- `api-first-demo:stop` [FAIL] - https://docs.docker.com/go/wsl2/
- `api-first:demo` [FAIL] - https://docs.docker.com/go/wsl2/
- `api-first:demo:stop` [FAIL] - https://docs.docker.com/go/wsl2/
- `api:sandbox:live` [FAIL] - https://docs.docker.com/go/wsl2/
- `api:sandbox:live:logs` [FAIL] - https://docs.docker.com/go/wsl2/
- `api:sandbox:live:status` [FAIL] - https://docs.docker.com/go/wsl2/
- `api:sandbox:live:stop` [FAIL] - https://docs.docker.com/go/wsl2/
- `api:sandbox:mock` [FAIL] - https://docs.docker.com/go/wsl2/
- `api:sandbox:prodlike` [FAIL] - https://docs.docker.com/go/wsl2/
- `api:sandbox:prodlike:down` [FAIL] - https://docs.docker.com/go/wsl2/
- `api:sandbox:prodlike:logs` [FAIL] - https://docs.docker.com/go/wsl2/
- `api:sandbox:prodlike:status` [FAIL] - https://docs.docker.com/go/wsl2/
- `api:sandbox:prodlike:up` [FAIL] - https://docs.docker.com/go/wsl2/
- `api:sandbox:project` [FAIL] - https://docs.docker.com/go/wsl2/
- `api:sandbox:stop` [FAIL] - https://docs.docker.com/go/wsl2/
- `demo:api-first:stop` [FAIL] - https://docs.docker.com/go/wsl2/

## license_gate (7)

- `api-first-demo` [FAIL] - [license] BLOCKED: Feature 'api_first_flow' requires a plan upgrade (current: community).
- `api-first:demo:live` [FAIL] - [license] BLOCKED: Feature 'api_first_flow' requires a plan upgrade (current: community).
- `api:first:flow:taskstream` [FAIL] - [license] BLOCKED: Feature 'api_first_flow' requires a plan upgrade (current: community).
- `api:first:v0:taskstream` [FAIL] - [license] BLOCKED: Feature 'api_first_flow' requires a plan upgrade (current: community).
- `demo:api-first` [FAIL] - [license] BLOCKED: Feature 'api_first_flow' requires a plan upgrade (current: community).
- `docsops:generate` [FAIL] - ------------------------------------------------------------------------------
- `docsops:generate:auto` [FAIL] - ------------------------------------------------------------------------------

## missing_env_or_credentials (2)

- `i18n:translate:all` [FAIL] - TypeError: "Could not resolve authentication method. Expected either api_key or auth_token to be set. Or for one of the `X-Api-Key` or `Authorization` headers to be explicitly omitted"
- `smoke:prod` [FAIL] - Missing required environment variable: VERIDOC_BASE_URL

## other_runtime_failure (12)

- `agent:claude:auto` [FAIL] - Error: Input must be provided either through stdin or as a prompt argument when using --print
- `build` [FAIL] - INFO    -  meta-descriptions: Added meta descriptions to 162 of 162 pages, 0 using the first paragraph
- `build:docusaurus` [FAIL] - npm error You can rerun the command with `--loglevel=verbose` to see the logs in your terminal
- `build:knowledge-enrich:llm` [FAIL] - ModuleNotFoundError: No module named 'scripts.env_loader'
- `build:mkdocs` [FAIL] - INFO    -  meta-descriptions: Added meta descriptions to 162 of 162 pages, 0 using the first paragraph
- `consolidate:reports-only` [FAIL] - [consolidate] WARNING: consolidated_reports feature requires Professional+ license.
- `lint` [FAIL] - - docs/reference/intent-experiences/troubleshoot-operator.md
- `lint:multilang:all` [FAIL] -   docs/troubleshooting/webhook-not-firing.md: No tab group contains required languages: curl, javascript, python
- `lint:openapi` [FAIL] - npm error You can rerun the command with `--loglevel=verbose` to see the logs in your terminal
- `openapi:overrides` [FAIL] - Overrides file does not exist: api/overrides/openapi.manual.yml
- `openapi:regression` [FAIL] - Run with --update to create baseline snapshot.
- `validate:knowledge:with-llm-enrich` [FAIL] - ModuleNotFoundError: No module named 'scripts.env_loader'

## quality_regression (5)

- `lint:md` [FAIL] - docs/troubleshooting/webhook-not-firing.md:54 MD012/no-multiple-blanks Multiple consecutive blank lines [Expected: 1; Actual: 2]
- `lint:snippets` [FAIL] - Summary: 694/696 blocks passed
- `lint:snippets:strict` [FAIL] - Summary: 809/822 blocks passed
- `validate:full` [FAIL] - docs/troubleshooting/webhook-not-firing.md:54 MD012/no-multiple-blanks Multiple consecutive blank lines [Expected: 1; Actual: 2]
- `validate:minimal` [FAIL] - docs/troubleshooting/webhook-not-firing.md:54 MD012/no-multiple-blanks Multiple consecutive blank lines [Expected: 1; Actual: 2]

## required_input_or_args (8)

- `audit:public` [FAIL] - No --site-url provided. Use --interactive or pass one or more --site-url values.
- `audit:public:wizard` [FAIL] - EOFError: EOF when reading a line
- `audit:public:llm` [FAIL] - No --site-url provided. Use --interactive or pass one or more --site-url values.
- `audit:public:llm-summary` [FAIL] - No --site-url provided. Use --interactive or pass one or more --site-url values.
- `build:intent` [FAIL] - assemble_intent_experience.py: error: the following arguments are required: --intent, --audience, --channel
- `i18n:translate` [FAIL] - Error: specify --source, --all-missing, or --stale-only
- `new-doc` [FAIL] - new_doc.py: error: the following arguments are required: type, title
- `onboard:client` [FAIL] - ValueError: Missing required arguments. Provide --client and (for install-local mode) --client-repo, or run in a terminal with --interactive.

## sandbox_or_permission (6)

- `agent:codex:auto` [FAIL] - Error: Permission denied (os error 13)
- `api:first:verify-user-path` [FAIL] - urllib.error.URLError: <urlopen error [Errno 1] Operation not permitted>
- `api:first:verify-user-path:prodlike` [FAIL] - urllib.error.URLError: <urlopen error [Errno 1] Operation not permitted>
- `demo:codex` [FAIL] - For more information, try '--help'.
- `serve` [FAIL] - PermissionError: [Errno 1] Operation not permitted
- `serve:mkdocs` [FAIL] - PermissionError: [Errno 1] Operation not permitted

## timeout (7)

- `build:intent:all` [TIMEOUT] -
- `consolidate` [TIMEOUT] -
- `demo:claude:loop` [TIMEOUT] -
- `demo:codex:loop` [TIMEOUT] -
- `serve:docusaurus` [TIMEOUT] -
- `test:all` [TIMEOUT] -
- `validate:knowledge` [TIMEOUT] -

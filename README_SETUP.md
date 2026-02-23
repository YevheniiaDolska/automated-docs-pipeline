# Setup guide for beginners

This guide gives the fastest reliable setup path.

## What happens after setup

Once configured, the pipeline runs automatically in CI.

1. It continuously checks documentation quality and contract compliance.
1. It detects API and SDK drift and documentation gaps.
1. It produces reports for prioritization and planning.
1. Teams can use those reports as input for AI drafting with strict quality prompts.
1. Humans review facts, context, and final decisions before merge.
1. Quality bar is set to Stripe-level clarity and usability from the first draft.

Local AI behavior:

1. It reads repository structure and changed files.
1. It identifies what docs to add or update based on those changes.
1. It follows project templates, snippets, and lint constraints automatically.

Platform capabilities summary:

1. Continuous gap detection and backlog reports.
1. DoD enforcement and API or SDK drift prevention.
1. KPI wall, SLA evaluation, and release docs pack.
1. SEO and GEO optimization as part of quality gates.
1. Optional Algolia indexing for searchable and browsable docs.
1. Optional API-first scaffold from OpenAPI to server stubs and client SDKs.
1. Automated lifecycle management loop with safe guardrails.
1. Optional PLG API playground with Swagger UI or Redoc.
1. Optional OpenAPI mock sandbox generation for test environments.
1. Unified PLG config block (`extra.plg`) for API-first and code-first projects.

Lifecycle guardrails:

1. Automatic lifecycle issue creation is enabled.
1. Automatic lifecycle pull requests are draft-only.
1. Archive or removal actions are always manual after human review.

## 1. Prerequisites

Install:

1. Python 3.10 or newer
1. Node.js 18 or newer
1. Git
1. Optional: Docker Desktop
1. Optional: GNU Make

Check versions:

```bash
python3 --version
node --version
npm --version
git --version
```

## 2. Install locally

```bash
git clone <repo-url>
cd "Auto-Doc Pipeline"
python3 -m pip install -r requirements.txt
npm install
```

## 3. First validation run

If `make` exists:

```bash
make validate-minimal
```

If `make` is not installed:

```bash
npm run validate:minimal
```

Expected result: all checks pass.

## 4. Full validation run

If `make` exists:

```bash
make validate-full
```

Without `make`:

```bash
npm run validate:full
```

## 5. Run docs locally

If `make` exists:

```bash
make docs-serve
```

Without `make`:

```bash
npm run serve
```

## 6. Containerized setup (optional)

Use this if local tooling conflicts:

```bash
docker compose -f docker-compose.docs-ops.yml up --build
```

Or use VS Code Dev Container with `.devcontainer/devcontainer.json`.

## 7. Next guides

1. `SETUP_GUIDE.md` for detailed setup and troubleshooting.
1. `SETUP_FOR_PROJECTS.md` for rollout to another repository.
1. `PRIVATE_REPO_SETUP.md` for private repository specifics.
1. `USER_GUIDE.md` for daily team usage.

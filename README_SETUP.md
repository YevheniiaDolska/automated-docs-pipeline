# Documentation pipeline setup guide (beginner-first)

## What this repository gives you

This is a documentation operations system, not only templates.

It includes:

1. Document quality gates.
1. Frontmatter schema validation.
1. API and SDK drift checks.
1. DoD contract checks for pull requests.
1. KPI and release reporting.
1. Smoke checks for runnable code examples.

## Fast setup

```bash
git clone <repo-url>
cd "Auto-Doc Pipeline"
python3 -m pip install -r requirements.txt
npm install
make validate-minimal
```

## Choose execution mode

### Minimal mode

Use when company has strict constraints.

```bash
make validate-minimal
```

Includes:

1. Markdown linting.
1. Frontmatter schema checks.
1. SEO/GEO structure checks.
1. Code example smoke checks.
1. DoD and drift contracts.

### Full mode

Use when you want all checks and reports.

```bash
make validate-full
```

## One-command workflow

```bash
make validate
```

## Development container

If your local Python or Node setup is unstable, use containerized setup.

1. Open project in VS Code.
1. Reopen in Dev Container.
1. Run `make validate-minimal`.

Files:

1. `.devcontainer/devcontainer.json`
1. `.devcontainer/Dockerfile`
1. `docker-compose.docs-ops.yml`

## Security first

Before enabling automation in company repos, read:

1. `SECURITY_OPERATIONS.md`

## Next documents

1. `SETUP_GUIDE.md` for detailed local setup.
1. `SETUP_FOR_PROJECTS.md` for integrating into external repos.
1. `PRIVATE_REPO_SETUP.md` for private GitHub repositories.
1. `OPERATOR_RUNBOOK.md` for pilot delivery steps.

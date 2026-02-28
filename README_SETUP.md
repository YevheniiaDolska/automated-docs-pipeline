# Setup guide for beginners

This guide covers the fastest reliable path to get the Auto-Doc Pipeline running locally. It explains what happens after setup, the prerequisites, and the installation steps.

## What happens after setup

Once configured, the pipeline runs automatically in CI on every pull request. Here is what it does:

1. **Checks documentation quality** (style, formatting, spelling, frontmatter, SEO/GEO).
1. **Enforces the docs contract** (if interface files changed, docs must change too).
1. **Detects API/SDK drift** (if API or SDK changed, reference docs must update).
1. **Executes code examples** (fenced code blocks tagged `smoke` must run without errors).
1. **Generates reports** (KPI dashboard, gap backlog, lifecycle alerts).

Locally, AI assistants (Claude or Codex) can draft documentation using project-specific templates and instructions. Humans review facts and approve content.

## Prerequisites

Install these tools:

| Tool | Minimum version | Where to get it |
| --- | --- | --- |
| Python | 3.10 | `https://www.python.org/downloads/` |
| Node.js | 18 | `https://nodejs.org/` |
| Git | Any recent version | `https://git-scm.com/` |
| Docker Desktop | Optional | `https://www.docker.com/products/docker-desktop/` |
| GNU Make | Optional | Included on macOS/Linux; optional on Windows |

Verify your installations:

```bash
python3 --version
node --version
npm --version
git --version
```

## Install locally

```bash
git clone <repo-url>
cd "Auto-Doc Pipeline"
python3 -m pip install -r requirements.txt
npm install
```

## Run minimal validation

If `make` is available:

```bash
make validate-minimal
```

If `make` is not installed (common on Windows):

```bash
npm run validate:minimal
```

Expected result: the command runs and reports any issues found. It may find issues in existing docs (that is normal for a first setup).

`validate:minimal` does not run Vale or spelling checks. To run the broader local lint suite that matches CI more closely:

```bash
npm run lint
```

## Run full validation

```bash
npm run validate:full
```

This runs all checks including the end-to-end test suite.

## Preview docs locally

The pipeline auto-detects whether you use MkDocs or Docusaurus:

```bash
npm run serve
```

Or explicitly choose a generator:

```bash
npm run serve:mkdocs       # MkDocs on port 8000
npm run serve:docusaurus   # Docusaurus on port 3000
```

Check which generator is active:

```bash
npm run generator:detect
```

## Choose a generator (optional)

The pipeline defaults to MkDocs. To switch to Docusaurus:

```bash
npm run convert:to-docusaurus
npm run build:docusaurus
```

To switch back:

```bash
npm run convert:to-mkdocs
```

## Generate the GUI configurator (optional)

Create a browser-based setup wizard:

```bash
npm run configurator
```

Open `reports/pipeline-configurator.html` in a browser. No internet required.

## Containerized setup (optional)

If local tooling conflicts, use Docker:

```bash
docker compose -f docker-compose.docs-ops.yml up --build
```

This container flow runs one validation pass via `make validate` and exits. It is useful for confirming the toolchain, but it is not a long-running preview server.

Or use VS Code Dev Container with `.devcontainer/devcontainer.json`.

## Next steps

| Situation | Guide |
| --- | --- |
| First time, need step-by-step hand-holding | `BEGINNER_GUIDE.md` |
| Installing pipeline into another repository | `SETUP_FOR_PROJECTS.md` |
| Private repository specifics | `PRIVATE_REPO_SETUP.md` |
| Daily team usage | `USER_GUIDE.md` |
| Full feature walkthrough | `GETTING_STARTED_ZERO_TO_PRO.md` |

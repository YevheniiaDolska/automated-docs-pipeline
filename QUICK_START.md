# Quick start (first 30 minutes)

This guide assumes you have never seen this pipeline before. It walks you through setup step by step.

## Prerequisites

Before you start, make sure you have these tools installed on your machine:

1. **Python 3.10 or later.** Check: `python3 --version`. On Windows, try `py -3 --version`.
1. **Node.js 18 or later.** Check: `node --version`.
1. **npm** (comes with Node.js). Check: `npm --version`.
1. **Git.** Check: `git --version`.

If any of these commands fail, install the missing tool first:

- Python: [https://www.python.org/downloads/](https://www.python.org/downloads/)
- Node.js: [https://nodejs.org/](https://nodejs.org/)
- Git: [https://git-scm.com/](https://git-scm.com/)

## Step 1: Clone and enter the project

```bash
git clone <repo-url>
cd "Auto-Doc Pipeline"
```

Replace `<repo-url>` with the actual repository URL.

## Step 2: Install dependencies

This installs Python packages (Vale, linters) and Node.js packages (markdownlint, cspell):

```bash
python3 -m pip install -r requirements.txt
npm install
```

On Windows, if `python3` does not work, use:

```bash
py -3 -m pip install -r requirements.txt
npm install
```

## Step 3: Run minimal validation

This is the fastest way to check that your setup works:

```bash
npm run validate:minimal
```

Or, if you have `make` installed:

```bash
make validate-minimal
```

**What happens:** The command runs Vale style checks, markdownlint formatting checks, and frontmatter validation on all files in the `docs/` directory. If everything is green, your setup is working.

**If it fails:** Read the error messages. They tell you exactly what is wrong and where. Common issues:

- Missing Python package: run `pip install -r requirements.txt` again.
- Missing Vale styles: run `vale sync` to download style packages.
- A doc file has a formatting error: fix it, then rerun.

## Step 4: Run full validation (optional)

Full validation runs all checks, including SEO/GEO optimization and code snippet linting:

```bash
npm run validate:full
```

This takes longer but catches more issues.

## Step 5: Start documentation preview

The pipeline auto-detects whether your project uses MkDocs or Docusaurus:

```bash
npm run serve
```

**What happens:**

- If `mkdocs.yml` exists, it starts MkDocs at `http://127.0.0.1:8000`.
- If `docusaurus.config.js` exists, it starts Docusaurus at `http://localhost:3000`.

Open the URL in your browser. You see the documentation site with live reload. Edit any `.md` file and the browser updates automatically.

To check which generator is active:

```bash
npm run generator:detect
```

## Step 6: Understand the file structure

```text
Auto-Doc Pipeline/
  docs/                     # Documentation source files (Markdown)
    _variables.yml          # Shared variables (product name, ports, URLs)
    getting-started/        # Tutorial and quickstart pages
    how-to/                 # Task-oriented guides
    concepts/               # Explanation pages
    reference/              # API and configuration reference
    troubleshooting/        # Problem-solution pages
  templates/                # 27 pre-validated document templates
  scripts/                  # 35+ automation scripts
  policy_packs/             # 5 quality profiles for different companies
  .github/workflows/        # 22 CI/CD automation workflows
  mkdocs.yml                # Site configuration (MkDocs)
  CLAUDE.md                 # AI instructions for Claude
  AGENTS.md                 # AI instructions for Codex
  package.json              # npm scripts for all commands
  Makefile                  # Make shortcuts
```

## Step 7: Create your first document (optional)

Use a template to create a new document:

```bash
cp templates/how-to.md docs/how-to/my-first-guide.md
```

Edit `docs/how-to/my-first-guide.md`:

1. Update the frontmatter (title, description, content_type).
1. Replace placeholder content with your text.
1. Use variables: `{{ product_name }}` instead of hardcoded product names.

Validate your new document:

```bash
npm run validate:minimal
```

## Step 8: Generate GUI configurator (optional)

The GUI configurator creates a browser-based wizard for configuring the pipeline:

```bash
npm run configurator
```

Open `reports/pipeline-configurator.html` in a browser. The wizard walks you through:

1. Policy pack selection.
1. Variable editing (product name, URLs, ports).
1. Generator choice (MkDocs or Docusaurus).
1. KPI threshold tuning.
1. Live preview of generated configuration.
1. Export as individual files.

## Step 9: Bootstrap into a new project (optional)

To install the pipeline into another repository:

```bash
python3 scripts/init_pipeline.py --product-name "Your Product Name" --generator mkdocs
```

Use `--generator docusaurus` for Docusaurus projects.

This copies required files, configures variables, scaffolds the chosen generator, and runs initial validation.

## Step 10: Run with Docker (optional)

```bash
docker compose -f docker-compose.docs-ops.yml up --build
```

## What to do next

| What you want to do | Guide |
| --- | --- |
| Understand all features | `README.md` |
| Set up Windows from scratch | `BEGINNER_GUIDE.md` |
| Full setup with troubleshooting | `README_SETUP.md` |
| Install into another repository | `SETUP_FOR_PROJECTS.md` |
| Run a pilot for a client | `PILOT_VS_FULL_IMPLEMENTATION.md` |
| Customize for a company | `CUSTOMIZATION_PER_COMPANY.md` |
| Understand policy packs | `POLICY_PACKS.md` |
| Set up private repository | `PRIVATE_REPO_SETUP.md` |
| Learn about security | `SECURITY_OPERATIONS.md` |

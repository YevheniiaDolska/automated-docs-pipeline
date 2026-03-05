# Quick start (5 minutes)

Set up the Auto-Doc Pipeline and generate your first documentation from gap analysis reports.

## Prerequisites

Verify these are installed:

```bash
node --version   # 18+ required
python3 --version  # 3.11+ required
git --version
```

If anything is missing:

- Node.js: <https://nodejs.org/>
- Python: <https://www.python.org/downloads/>
- Git: <https://git-scm.com/>

## Step 1: Clone and install

```bash
git clone <repo-url>
cd "Auto-Doc Pipeline"
npm install
pip install -r requirements.txt
```

On Windows, use `py -3 -m pip install -r requirements.txt` if `pip` is not on PATH.

## Step 2: Generate the consolidated report

```bash
npm run consolidate
```

This runs gap analysis, builds the KPI wall, evaluates SLA compliance, and merges everything into `reports/consolidated_report.json`.

To regenerate only the consolidated file from existing reports:

```bash
npm run consolidate:reports-only
```

## Step 3: Process with Claude Code

Open Claude Code in the project directory and give it the report:

```text
Process reports/consolidated_report.json
```

Claude Code reads the consolidated report, identifies documentation gaps, and generates or updates Markdown files in `docs/` following the templates in `templates/` and the rules in `CLAUDE.md`.

## Step 4: Review and commit

Check what changed:

```bash
git diff docs/
```

Validate the generated documentation:

```bash
npm run validate:minimal
```

If everything passes, commit:

```bash
git add docs/ mkdocs.yml
git commit -m "docs: generate documentation from gap analysis"
```

## What each command does

| Command | Purpose |
| --- | --- |
| `npm run consolidate` | Run all analyses and merge into one report |
| `npm run validate:minimal` | Fast lint check (markdownlint, frontmatter, GEO, examples) |
| `npm run validate:full` | Full lint check including e2e and golden tests |
| `npm run serve` | Preview docs site locally (auto-detects MkDocs or Docusaurus) |
| `npm run lint` | Run all individual linters (Vale, markdownlint, cspell, GEO) |
| `npm run gaps` | Run gap analysis only |
| `npm run kpi-wall` | Generate KPI dashboard |

## Next steps

| Goal | Guide |
| --- | --- |
| Understand all features | `README.md` |
| Full setup with troubleshooting | `README_SETUP.md` |
| Install into another repository | `SETUP_FOR_PROJECTS.md` |
| Customize for a company | `CUSTOMIZATION_PER_COMPANY.md` |
| Windows setup from scratch | `BEGINNER_GUIDE.md` |

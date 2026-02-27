# Private repository setup

The Auto-Doc Pipeline works in private repositories with no changes to the core pipeline. This guide covers the additional configuration steps specific to private repositories on GitHub.

If you have not installed the pipeline yet, start with `SETUP_FOR_PROJECTS.md`. This guide assumes the pipeline files are already in the repository.

## 1. Enable GitHub Actions

Private repositories on GitHub have GitHub Actions disabled by default. Enable it:

1. Go to your repository on GitHub.
1. Click `Settings` then `Actions` then `General`.
1. Under "Actions permissions," select `Allow all actions and reusable workflows` (or restrict to specific actions if company policy requires it).
1. Click `Save`.

If your organization restricts GitHub Actions, ask an organization admin to allow the actions used by this pipeline. The pipeline uses only standard `actions/checkout` and `actions/setup-python` actions.

## 2. Configure workflow permissions

GitHub Actions in private repositories need explicit permissions to read repository contents and create issues:

1. In the same `Settings` then `Actions` then `General` page, scroll to "Workflow permissions."
1. Select `Read and write permissions` if you want lifecycle management to create issues automatically.
1. Or select `Read repository contents` for minimum access (lifecycle management will not be able to create issues).
1. Click `Save`.

Each workflow file in the pipeline declares its own `permissions` block. The repository-level setting acts as an upper bound. If the repository allows `read`, a workflow cannot escalate to `write`.

## 3. Configure secrets

If you use optional integrations, add the required secrets:

1. Go to `Settings` then `Secrets and variables` then `Actions`.
1. Click `New repository secret` for each secret.

| Secret | Required | Purpose |
| --- | --- | --- |
| `ALGOLIA_APP_ID` | Only if using Algolia search | Algolia Application ID |
| `ALGOLIA_ADMIN_KEY` | Only if using Algolia search | Algolia Admin API Key |
| `ALGOLIA_INDEX_NAME` | Only if using Algolia search | Algolia index name |

The core pipeline (quality checks, contract enforcement, drift detection, smoke tests) does not require any secrets. It uses only the default `GITHUB_TOKEN`.

## 4. Validate before merging

Run the validation commands locally before merging the pipeline setup branch:

```bash
npm run validate:minimal
```

This runs markdown linting, frontmatter validation, SEO/GEO checks, and code example smoke tests. All 4 checks must pass.

For a more thorough check that includes end-to-end tests:

```bash
npm run validate:full
```

## 5. Set required status checks

After the pipeline is merged to `main`, configure branch protection rules so that CI checks are required to pass before merging any pull request:

1. Go to `Settings` then `Branches`.
1. Click `Add branch protection rule` (or edit the existing rule for `main`).
1. Enable `Require status checks to pass before merging`.
1. Search for and add these status checks:

| Status check | Workflow |
| --- | --- |
| Documentation quality checks | `docs-check.yml` |
| PR DoD contract | `pr-dod-contract.yml` |
| API and SDK drift gate | `api-sdk-drift-gate.yml` |
| Code examples smoke | `code-examples-smoke.yml` |

Optional but recommended:

1. Lifecycle management (`lifecycle-management.yml`). Scans for stale pages weekly and creates issues.

## 6. Private repository considerations

### GitHub Actions minutes

Private repositories consume GitHub Actions minutes from your plan. The pipeline workflows are lightweight (typically 1-3 minutes each), but monitor your usage:

1. Go to `Settings` then `Billing and plans` then `Plans and usage`.
1. Check "Actions" usage.

### Forked pull requests

By default, GitHub Actions workflows do not run on pull requests from forks of private repositories. If your workflow requires fork support, configure it in the workflow file:

```yaml
on:
  pull_request:
    types: [opened, synchronize]
```

For private repositories, this is usually not an issue because forks are restricted.

### Visibility of workflow logs

In private repositories, workflow logs are visible only to repository collaborators. Secrets are masked in logs automatically.

## 7. Security checklist

Before completing the setup:

1. No secrets appear in markdown, templates, snippets, or code files.
1. Only least-privilege tokens are used (prefer `GITHUB_TOKEN` over personal access tokens).
1. Credential rotation is scheduled (every 90 days minimum).
1. `SECURITY_OPERATIONS.md` is followed for incident response procedures.
1. `.gitignore` excludes `.env` and other local configuration files that may contain secrets.

## Related guides

| Guide | What it covers |
| --- | --- |
| `SETUP_FOR_PROJECTS.md` | Full pipeline installation steps |
| `SECURITY_OPERATIONS.md` | Secrets management and incident response |
| `MINIMAL_MODE.md` | Running only core checks without optional integrations |
| `POLICY_PACKS.md` | Choosing quality thresholds for the repository |

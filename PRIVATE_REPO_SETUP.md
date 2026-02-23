# Private repository setup

This pipeline works in private repositories.

## 1. Add pipeline files in feature branch

Follow `SETUP_FOR_PROJECTS.md`, then open a pull request.

## 2. Configure repository settings

1. Enable GitHub Actions for the repository.
1. Set workflow permissions to at least read repository contents.
1. Grant additional permissions only to workflows that need them.

## 3. Configure secrets

Create only required secrets:

1. `ALGOLIA_APP_ID` (optional)
1. `ALGOLIA_ADMIN_KEY` (optional)
1. `ALGOLIA_INDEX_NAME` (optional)

Store secrets in GitHub Actions secrets only.

## 4. Validate before merge

```bash
npm run validate:minimal
```

Recommended before major merges:

```bash
npm run validate:full
```

## 5. Required CI checks in PR

1. Documentation quality checks.
1. PR DoD contract.
1. API and SDK drift gate.
1. Code examples smoke.
1. Lifecycle management workflow (recommended).

## 6. Security checklist

1. No secrets in markdown, snippets, templates, or code.
1. Least-privilege tokens only.
1. Rotate credentials on a fixed schedule.
1. Use `SECURITY_OPERATIONS.md` for incident response.

# Private repository setup guide

Yes, the pipeline works in private repositories.

## 1. Add pipeline files

Follow `SETUP_FOR_PROJECTS.md` and commit in a feature branch.

## 2. Configure repository permissions

1. Allow GitHub Actions in the repository.
1. Ensure workflow permissions allow reading contents.
1. Grant issue creation only to workflows that need it.

## 3. Configure secrets

Only if used:

1. `ALGOLIA_APP_ID`
1. `ALGOLIA_ADMIN_API_KEY`
1. `ALGOLIA_INDEX_NAME`

Store only in Actions secrets.

## 4. Validate in private repo

```bash
make validate-minimal
```

## 5. Open pull request

CI should run:

1. docs checks
1. DoD contract
1. drift gate
1. smoke examples

## Security checklist

1. No secrets in docs or snippets.
1. Use least-privilege tokens.
1. Rotate tokens every 90 days.

Reference: `SECURITY_OPERATIONS.md`.

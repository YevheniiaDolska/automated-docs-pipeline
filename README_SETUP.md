# How to customize the README for your project

When you fork or install the VeriOps into a new repository, update the README to reflect your product. This guide covers what to change.

## Replace product names

Search for "VeriOps" and replace with your product documentation name. Update these fields in the README:

- Project title and description.
- Any references to the pipeline name in badges or links.
- The footer or copyright line.

## Update badges

The pipeline generates SVG badges in `reports/`. Update the badge URLs in your README to point to your repository:

```markdown
![Quality Score](reports/quality-score.svg)
![Stale Docs](reports/stale-docs.svg)
![Gaps](reports/gaps.svg)
```

If you host badges externally, update the image URLs to your hosting location.

## Customize the feature list

The default README lists all pipeline features. Remove features you do not use and add any custom integrations:

- Remove Algolia search if you do not use it.
- Remove API sandbox references if your product has no API.
- Add any custom policy packs or templates you created.

## Add your deployment URL

Replace the default documentation site URL with your own:

```markdown
Live documentation: [docs.yourproduct.com](https://docs.yourproduct.com)
```

Update the `docs_url` in `docs/_variables.yml` to match.

## Update the quick start section

Replace the example commands with your repository URL and product-specific setup steps. Verify that all commands in the README work by running them.

For client delivery, prefer:

```bash
python3 scripts/onboard_client.py
```

Manual operator checks after onboarding:
\11. Review generated profile: `profiles/clients/generated/<client_id>.client.yml`.
\11. Review installed runtime config: `<client-repo>/docsops/config/client_runtime.yml`.
\11. Review installed policy: `<client-repo>/docsops/policy_packs/selected.yml`.
\11. Review env checklist: `<client-repo>/docsops/ENV_CHECKLIST.md`.

## Verify after changes

Run validation to confirm the README does not break any checks:

```bash
npm run validate:minimal
```

## Related guides

| Guide | What it covers |
| --- | --- |
| `quick-start.md` | 10-step setup for any environment |
| `SETUP_FOR_PROJECTS.md` | Full pipeline installation steps |
| `docs/operations/CANONICAL_FLOW.md` | One-page canonical flow for sales + delivery |
| `docs/operations/CENTRALIZED_CLIENT_BUNDLES.md` | Centralized per-client profiles, bundle provisioning, weekly automation |
| `docs/operations/UNIFIED_CLIENT_CONFIG.md` | Full config reference (all keys) |
| `docs/operations/PLAN_TIERS.md` | Plan matrix and ready presets (Basic/Pro/Enterprise) |
| `docs/operations/PIPELINE_CAPABILITIES_CATALOG.md` | Full capabilities list generated from package scripts |

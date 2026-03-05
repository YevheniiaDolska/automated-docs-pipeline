# How to customize the README for your project

When you fork or install the Auto-Doc Pipeline into a new repository, update the README to reflect your product. This guide covers what to change.

## Replace product names

Search for "Auto-Doc Pipeline" and replace with your product documentation name. Update these fields in the README:

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

## Verify after changes

Run validation to confirm the README does not break any checks:

```bash
npm run validate:minimal
```

## Related guides

| Guide | What it covers |
| --- | --- |
| `QUICK_START.md` | 10-step setup for any environment |
| `SETUP_FOR_PROJECTS.md` | Full pipeline installation steps |

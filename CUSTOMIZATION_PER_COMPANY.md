# Customizing the pipeline per company

This guide covers every customization point when adapting the Auto-Doc Pipeline for a specific company or product.

## Variables customization

Edit `docs/_variables.yml` to set all product-specific values. Documents reference these with `{{ variable_name }}` syntax, so one change updates every page.

```yaml
product_name: "Acme API"
company_name: "Acme Corp"
current_version: "2.5.0"
cloud_url: "https://app.acme.com"
docs_url: "https://docs.acme.com"
default_port: 3000
support_email: "support@acme.com"

env_vars:
  port: "ACME_PORT"
  api_key: "ACME_API_KEY"
  webhook_url: "ACME_WEBHOOK_URL"

max_payload_size_mb: 32
rate_limit_requests_per_minute: 120
```

**Rules:**

- Every value that appears in more than one document must be a variable.
- Use descriptive names with units: `request_timeout_seconds`, not `timeout`.
- Group related values with YAML nesting: `env_vars.port`, `env_vars.api_key`.
- Never hardcode product names, URLs, ports, or versions in documents.

## Template customization

Templates in `templates/` are pre-validated to pass all linters. Customize them for your product:

1. **Update frontmatter defaults** -- Set the `product` field and default tags.
1. **Add product-specific sections** -- If your product has unique patterns (for example, "workspaces" instead of "projects"), update the template structure.
1. **Keep the formatting structure** -- Do not remove required sections or change the heading hierarchy. The linter-passing structure is intentional.

All 31 templates follow the Diataxis framework: tutorials, how-to guides, concepts, and references.

## Policy pack selection

Policy packs set quality thresholds for CI gates. Choose one and update the workflow references.

| Pack | Use case | Quality % | Max stale % |
| --- | --- | --- | --- |
| `minimal.yml` | Pilot, new teams | 75 | 20 |
| `api-first.yml` | API-heavy products | 82 | 12 |
| `monorepo.yml` | Multi-service repos | 80 | 15 |
| `multi-product.yml` | Product families | 80 | 15 |
| `plg.yml` | Product-led growth | 85 | 10 |

To create a custom pack, copy the closest match and adjust:

```bash
cp policy_packs/api-first.yml policy_packs/client-acme.yml
```

Then update `interface_patterns` and `docs_patterns` to match the company's code structure:

```yaml
interface_patterns:
  - "src/controllers/**"
  - "src/routes/**"
docs_patterns:
  - "docs/**/*.md"
```

Update these workflow files to reference your pack: `pr-dod-contract.yml`, `api-sdk-drift-gate.yml`, `kpi-wall.yml`.

## Workflow customization

### CI gates

The 4 mandatory PR gates work out of the box. To adjust which file paths trigger them, edit the `on.pull_request.paths` section in each workflow file.

### Scheduled workflows

Adjust the schedule for recurring workflows:

- `kpi-wall.yml` -- Runs weekly on Monday by default. Change the cron expression for a different day.
- `lifecycle-management.yml` -- Runs weekly to scan for stale pages. Adjust frequency as needed.

### Optional workflows

Enable or disable based on the company's needs:

- `algolia-index.yml` -- Enable if the company uses Algolia for search.
- `api-first-scaffold.yml` -- Enable if the company generates code from OpenAPI specs.
- `openapi-source-sync.yml` -- Enable if the company maintains OpenAPI specs.

## Branding

### Documentation site

Edit `mkdocs.yml`:

```yaml
site_name: "Acme API Documentation"
site_url: "https://docs.acme.com"

theme:
  name: material
  palette:
    primary: blue
    accent: light-blue
  logo: assets/logo.png
  favicon: assets/favicon.ico
```

### Spelling dictionary

Add company-specific terms to `cspell.json` so the spellchecker does not flag product names:

```json
{
  "words": ["Acme", "AcmeAPI", "acmecorp"]
}
```

### AI instructions

Add company-specific style rules to `CLAUDE.md` and `AGENTS.md`:

```markdown
## Company-specific style rules

- Always refer to the product as "Acme API" (never "ACME" or "acme").
- Use "workspace" instead of "project."
- Authentication tokens are called "access keys."
```

### GUI configurator

Run `npm run configurator` to generate a browser-based wizard at `reports/pipeline-configurator.html`. It walks through policy pack selection, variable editing, generator choice, and KPI threshold tuning in 6 steps. Export the configuration as files ready to drop into the company's repository.

## Customization checklist

- [ ] `docs/_variables.yml` filled with company-specific values.
- [ ] Policy pack selected and referenced in workflows.
- [ ] `mkdocs.yml` updated with site name, URL, logo, and colors.
- [ ] `cspell.json` updated with company terms.
- [ ] Templates adapted to company patterns.
- [ ] `CLAUDE.md` and `AGENTS.md` updated with company style rules.
- [ ] `npm run validate:minimal` passes.

## Related guides

| Guide | What it covers |
| --- | --- |
| `SETUP_FOR_PROJECTS.md` | Full pipeline installation |
| `ALGOLIA_SETUP.md` | Search integration |
| `POLICY_PACKS.md` | Policy pack details |

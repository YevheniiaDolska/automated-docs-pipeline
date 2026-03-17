# Start a 10-14 day pilot of this pipeline

This guide walks you through a focused 10-14 calendar day pilot (typically 5-10 business days) of the Auto-Doc Pipeline on your own repository. By the end, you have working quality gates, automated weekly reporting, and generated documentation.

## Prerequisites

You need Git, Node.js 18+, Python 3.11+, and npm installed. On Windows, use `py -3` if `python3` does not work.

## Step 1: Fork the repository

Fork or clone the Auto-Doc Pipeline repository:

```bash
git clone <your-fork-url>
cd "Auto-Doc Pipeline"
python3 -m pip install -r requirements.txt
npm install
```

## Step 2: Edit `_variables.yml`

Open `docs/_variables.yml` and replace the placeholder values with your product information:

```yaml
product_name: "Your Product"
product_full_name: "Your Product platform"
current_version: "1.0.0"
cloud_url: "https://app.yourproduct.com"
docs_url: "https://docs.yourproduct.com"
support_email: "support@yourcompany.com"
default_port: 8080
```

Every document references these variables. Update them once and all docs reflect your product.

## Step 3: Choose the minimal policy pack

The `minimal.yml` policy pack uses relaxed thresholds suitable for a pilot:

- Minimum quality score: 75 (instead of 82-84)
- Maximum stale percentage: 20% (instead of 10-12%)
- Maximum high-priority gaps: 10 (instead of 5-6)

No workflow changes are needed for local testing. For CI, set the policy pack input:

```yaml
# In workflow files
with:
  policy_pack: policy_packs/minimal.yml
```

## Step 4: Enable weekly automation (recommended)

Provision once and install scheduler:

```bash
python3 scripts/provision_client_repo.py \
  --client profiles/clients/examples/basic.client.yml \
  --client-repo /path/to/client-repo \
  --docsops-dir docsops \
  --install-scheduler linux
```

## Step 5: Run the consolidated report now (optional)

Generate a single report that merges gap detection, KPI data, and staleness analysis:

```bash
npm run consolidate
```

This produces a consolidated report in `reports/` that identifies missing documentation, stale pages, and quality issues in priority order.

## Step 6: Process with Claude Code

Feed the consolidated report to Claude Code. The `CLAUDE.md` and `AGENTS.md` files in the repository instruct the AI to:

\11. Select the correct template from `templates/`.
\11. Use variables from `docs/_variables.yml`.
\11. Follow all style and formatting rules.
\11. Self-verify code examples and fact-check assertions.

Generate 5-10 documents from the highest-priority items in the report.

## Step 7: Review results

Run validation on the generated documents:

```bash
npm run validate:minimal
```

Review each document for factual accuracy. The pipeline handles formatting, style, and SEO/GEO optimization. You verify that the technical content is correct for your product.

## Step 8: Decide on full implementation

After the pilot, you have:

\11. A working quality gate system.
\11. A consolidated report showing documentation health.
\11. 5-10 generated documents that pass all linters.
\11. Baseline KPI data for before/after comparison.

To move to full implementation, switch to a stricter policy pack (`api-first.yml` or `plg.yml`), enable all four CI gates, and customize the remaining templates. See `PILOT_VS_FULL_IMPLEMENTATION.md` for details.

## Related guides

| Guide | What it covers |
| --- | --- |
| `PILOT_VS_FULL_IMPLEMENTATION.md` | Comparison of pilot vs full rollout |
| `MINIMAL_MODE.md` | Details on the minimal policy pack |
| `quick-start.md` | 10-step setup for any environment |

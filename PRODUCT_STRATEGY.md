# Product strategy: three-tier documentation automation

This document defines the positioning, feature allocation, and anti-cannibalization rules
for the three-tier product architecture.

## Product tiers

```text
                     Customization
                          ^
                          |
   Auto-Doc Pipeline      |   Premium consulting ($5K-25K + retainer)
                          |   For: regulated, complex, multi-repo
                          |
   VeriDoc Enterprise     |   Self-serve maximum ($49/seat/mo)
   ($49/seat/mo)          |   For: mature teams who want full control
                          |
   VeriDoc Business       |   Automation tier ($29/seat/mo)
   ($29/seat/mo)          |   For: growing teams, CI gates, KPI
                          |
   VeriDoc Team/Pro       |   Entry tier ($15/seat/mo)
   ($15/seat/mo)          |   For: startups, solo devs
                          |
                          +-------------------------------------> Scale
                     1 client                           10,000+ clients
```

### docsops-core

Minimal open-source framework. Defines the draft-verify-fix-optimize-publish loop.
Used as a template for any repository that needs docs automation.

- **Role:** reference standard, community adoption driver
- **Revenue model:** none (open source)
- **Value:** ecosystem gravity, pipeline-compatible repos

### VeriDoc (git_wrapper)

SaaS product for mass market. Self-serve onboarding, Web UI, API, billing.
Runs in cloud with optional local mode.

- **Role:** scalable revenue engine
- **Revenue model:** seat-based subscription
- **Value:** recurring revenue, large customer base, upsell funnel for premium

### Auto-Doc Pipeline

Premium consulting engagement. Full customization, local deployment, dedicated support.

- **Role:** high-touch revenue, case studies, credibility
- **Revenue model:** project-based + monthly retainer
- **Value:** high margin, deep customer relationships, reference accounts

## Feature matrix by tier

| Feature | Free | Pro $15 | Team $15/seat | Business $29/seat | Enterprise $49/seat | Premium consulting |
| --- | --- | --- | --- | --- | --- | --- |
| Git operations + NL interface | Y | Y | Y | Y | Y | Y |
| Basic docs generation (README, changelog) | Y | Y | Y | Y | Y | Y |
| Markdownlint + style linting | - | Y | Y | Y | Y | Y |
| Vale integration (Google style guide) | - | Y | Y | Y | Y | Y |
| Frontmatter validation | - | Y | Y | Y | Y | Y |
| SEO/GEO optimization (24 checks) | - | view | auto-fix | auto-fix | auto-fix | auto-fix + custom rules |
| Docs normalization | - | - | Y | Y | Y | Y |
| Multi-language code tabs | - | - | Y | Y | Y | Y |
| Gap analysis (community + code) | - | - | Y | Y | Y | Y |
| Glossary sync | - | - | Y | Y | Y | Y |
| Code example smoke tests | - | - | Y | Y | Y | Y |
| Lifecycle management | - | - | Y | Y | Y | Y |
| API-first flow (OpenAPI generation) | - | - | - | Y | Y | Y |
| API contract validation + Spectral | - | - | - | Y | Y | Y |
| API sandbox (Prism/external mock) | - | - | - | Y | Y | Y |
| API playground (Swagger UI) | - | - | - | Y | Y | Y |
| Drift detection (API/SDK) | - | - | - | Y | Y | Y |
| Docs-in-PR contract | - | - | - | Y | Y | Y |
| KPI wall + SLA dashboard | - | - | - | Y | Y | Y |
| Test assets generation + smart merge | - | - | - | Y | Y | Y |
| Consolidated reports | - | - | - | Y | Y | Y |
| Knowledge modules extraction | - | - | - | - | Y | Y |
| Knowledge graph (JSON-LD) | - | - | - | - | Y | Y |
| Retrieval evals | - | - | - | - | Y | Y |
| i18n system (sync + translate) | - | - | - | - | Y | Y |
| Custom policy packs | - | - | - | - | Y | Y |
| TestRail/Zephyr upload | - | - | - | - | Y | Y |
| Confluence migration tools | - | - | - | - | Y | Y |
| On-premises deployment | - | - | - | - | Y | Y |
| Client bundle builder | - | - | - | - | - | Y |
| Custom CLAUDE.md generation | - | - | - | - | - | Y |
| Dedicated handover sessions | - | - | - | - | - | Y |
| Custom gate/policy creation | - | - | - | - | - | Y |
| Retainer with response SLA | - | - | - | - | - | Y |
| Team training sessions | - | - | - | - | - | Y |

## Anti-cannibalization rules

### What Enterprise SaaS never gets

These features remain exclusive to Premium consulting:

1. **Client bundle builder** — custom docsops/ directory generation for client repos.
1. **Custom CLAUDE.md/AGENTS.md** — tailored agent contracts per client.
1. **Dedicated handover sessions** — live training and knowledge transfer.
1. **Custom gate creation** — bespoke quality gates beyond standard policy packs.
1. **Response SLA retainer** — guaranteed response time for support.
1. **Multi-repo fleet orchestration** — coordinated pipeline across 3+ repos.

### When a customer chooses Premium over Enterprise SaaS

- Data cannot leave their infrastructure (banks, healthcare, defense).
- Need custom gates or policies not available in SaaS.
- Want team training and handover.
- Multi-repo with non-standard infrastructure.
- Regulatory compliance requires on-site audit trail.

### When a customer chooses Enterprise SaaS over Premium

- Do not want to wait for a consulting engagement.
- Budget is seat-based, not project-based.
- Standard requirements, no deep customization needed.
- Want to start today, not in two weeks.
- Internal team can self-manage after initial setup.

## Confluence exit opportunity

Atlassian is pushing Server/Data Center customers to Cloud. Many teams are dissatisfied:

- Cloud pricing increases.
- Performance and control concerns.
- Docs-as-code adoption trend (MkDocs, Docusaurus, GitBook).

### Capture strategy

**VeriDoc SaaS** captures the mass exodus:

- Built-in Confluence migration tools (converter + importer).
- One-click migration path from Confluence export to docs-as-code.
- Familiar editing experience through WYSIWYG + Markdown.
- Lower total cost of ownership than Confluence Cloud.

**Auto-Doc Pipeline** captures enterprise exodus:

- Full migration service with quality audit.
- Content restructuring during migration.
- Compliance-grade audit trail.
- Custom integration with existing enterprise tooling.

### Migration funnel

```text
Confluence user dissatisfied
        |
        v
    Discovers VeriDoc (SEO, content marketing, referrals)
        |
        v
    Free tier: tries Confluence migration tool
        |
        v
    Team tier: migrates team docs, enables quality gates
        |
        v
    Business tier: adds API-first, drift detection, KPI
        |
        +-------> Happy at Business tier (majority)
        |
        v
    Needs: custom policies, on-prem, multi-repo fleet
        |
        v
    Enterprise SaaS or Premium consulting engagement
```

## Scaling model

| Growth stage | Premium clients/year | VeriDoc users | Revenue mix |
| --- | --- | --- | --- |
| Year 1 (now) | 5-10 | 100-500 | 80% premium / 20% SaaS |
| Year 2 | 15-30 | 1,000-5,000 | 50% premium / 50% SaaS |
| Year 3 | 30-50 + partners | 10,000-50,000 | 30% premium / 70% SaaS |
| Year 4+ | 50+ via channel | 50,000+ | 20% premium / 80% SaaS |

### Scaling premium beyond solo

1. **Playbook-driven delivery** — CLAUDE.md + AGENTS.md + client profiles automate 80% of setup.
1. **Junior/partner delivery** — train partners to deliver using the playbook.
1. **VeriDoc as funnel** — Enterprise SaaS users who outgrow self-serve become premium leads.
1. **Channel partners** — system integrators resell and deliver premium using the tooling.

## Upsell paths

```text
Free -> Pro: "Unlock style linting and frontmatter validation"
Pro -> Team: "Add SEO/GEO, gap analysis, and collaboration"
Team -> Business: "Add API-first, drift detection, and KPI dashboard"
Business -> Enterprise: "Add knowledge system, i18n, custom policies"
Enterprise -> Premium: "Need custom setup, training, or fleet management?"
```

## Revenue protection

### Premium protects SaaS

- Premium clients generate case studies and testimonials.
- Premium success stories drive SaaS adoption.
- Premium consulting surfaces feature requests for SaaS roadmap.

### SaaS protects Premium

- SaaS provides a self-serve pilot experience before premium engagement.
- SaaS demonstrates product value without sales overhead.
- SaaS handles clients too small for premium, preventing revenue leakage.

## Technical sync rules

### What flows from Auto-Doc Pipeline to VeriDoc

All scripts in `scripts/` are synced to `git_wrapper/scripts/`. The docs pipeline
modules in `packages/core/gitspeak_core/docs/` wrap these scripts for the SaaS context.

### What stays exclusive to Auto-Doc Pipeline

- `profiles/clients/` — client-specific configuration profiles.
- `instructions/llm_plans/` — tier-specific agent instructions for client repos.
- Client handoff documents (CLIENT_HANDOFF.md, OPERATOR_QUESTIONNAIRE.md).
- Sales playbooks and pricing cheatsheets.

### Sync cadence

When a new feature is added to Auto-Doc Pipeline:

1. Implement and test in Auto-Doc Pipeline.
1. Copy the script to `git_wrapper/scripts/`.
1. Add wrapper module in `gitspeak_core/docs/` if needed.
1. Add feature gate in `gitspeak_core/saas/` for the correct tier.
1. Update pricing.py feature list.

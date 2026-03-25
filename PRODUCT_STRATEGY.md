# Product strategy: three-tier documentation automation

## Current product definition (2026-03-25)

This content follows the active implementation baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` modes.
1. The smooth autopipeline covers all five API protocols (REST, GraphQL, gRPC, AsyncAPI, and WebSocket) in one operational model.
1. Non-REST flow includes generated server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated, with Postman-supported auto-prepare in external mode.
1. Contract test assets are generated automatically and merged with smart-merge so manual/customized cases are preserved and flagged for review when needed.
1. Knowledge/RAG maintenance, terminology sync, and quality/compliance gates run through the same automation surface when enabled.
1. Plan tiers gate advanced capabilities; higher plans include broader non-REST and governance scope.


This document defines the positioning, feature allocation, and anti-cannibalization rules
for the three-tier product architecture.


## Non-API documentation flows (docs-first scope)

The platform is not limited to API-first automation. In active production usage, it also runs full docs-first and code-first documentation operations for non-API content:

1. Detects content gaps, stale pages, and drift across product docs, runbooks, admin guides, troubleshooting, and release notes.
1. Generates and updates documentation types beyond API references (tutorial, how-to, concept, reference, troubleshooting, release-note, security, SDK, user/admin, and operations docs).
1. Applies normalization, style, metadata/frontmatter, SEO/GEO, terminology governance, and snippet validation to all documentation categories.
1. Executes lifecycle controls (active/deprecated/removed states, replacement links, and freshness cadence).
1. Runs knowledge extraction and retrieval preparation for all docs, not only API pages.
1. Produces consolidated review artifacts so human input is focused on approval and business accuracy, not repetitive formatting and synchronization work.

## Product tiers

```text
                     Customization
                          ^
                          |
   VeriOps                |   Done-for-you service ($5K-25K + retainer)
                          |   For: regulated, complex, multi-repo
                          |   Includes VeriDoc licenses for client team
                          |
   VeriDoc Enterprise     |   Full platform ($1,499/mo, unlimited repos/pages)
                          |   For: mature teams, full feature parity, SSO, SLA
                          |
   VeriDoc Business       |   Multi-repo automation ($799/mo, 15 repos, 5K pages)
                          |   For: growing teams, API-first, CI gates
                          |
   VeriDoc Pro            |   Growth tier ($399/mo, 5 repos, 1K pages)
                          |   For: growing teams, full automation
                          |
   VeriDoc Starter        |   Entry tier ($149/mo, 1 repo, 200 pages)
                          |   For: solo writers, small projects
                          |
                          +-------------------------------------> Scale
                     1 client                           10,000+ clients
```

**Pricing rationale: value-based, not cost-based.**

A documentation team of 2-3 tech writers costs $14,000-36,000/month (salary + taxes
- benefits). VeriDoc automates the bulk of their work: generation, linting, SEO/GEO,
drift detection, lifecycle management, gap analysis, API docs, and quality gates.
At Business tier ($799/mo), VeriDoc replaces most of the manual work that would
require 2-3 writers at $8-12K each. That is a 20-30x ROI.

Even at Starter ($149/mo), a solo writer reclaims 60-70% of their time for strategic
work instead of mechanical formatting, linting, and consistency checks.

**Team collaboration seats** are included in the plan:

- Starter: 1 seat included, additional seats $19/seat/mo
- Pro: 5 seats included, additional seats $19/seat/mo
- Business: 15 seats included, additional seats $15/seat/mo
- Enterprise: unlimited seats

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
- **Revenue model:** per-repo subscription + optional team seat add-ons
- **Value:** recurring revenue, large customer base, upsell funnel for VeriOps

### VeriOps

Done-for-you documentation operations service. Same automation engine as VeriDoc,
deployed on client infrastructure with custom configuration, training, and retainer.

- **Role:** high-touch revenue, case studies, credibility
- **Revenue model:** project-based ($5K-25K) + monthly retainer ($1,500-6,000)
- **Value:** high margin, deep customer relationships, reference accounts
- **Key difference from VeriDoc:** not functionality, but delivery model.
  VeriOps clients pay for a human who sets up, trains, and maintains. VeriDoc
  clients get the same features but configure and manage themselves.

## Feature matrix by tier

| Feature | Starter $149/mo (1 repo, 200 pages) | Pro $399/mo (5 repos, 1K pages) | Business $799/mo (15 repos, 5K pages) | Enterprise $1,499/mo (unlimited) | VeriOps (done-for-you) |
| --- | --- | --- | --- | --- | --- |
| Git operations + NL interface | Y | Y | Y | Y | Y |
| Basic docs generation (README, changelog) | Y | Y | Y | Y | Y |
| Markdownlint + style linting | Y | Y | Y | Y | Y |
| Vale integration (Google style guide) | Y | Y | Y | Y | Y |
| Frontmatter validation | Y | Y | Y | Y | Y |
| SEO/GEO optimization (32 checks: 8 GEO + 14 SEO + 6 Style + 4 Contract) | auto-fix | auto-fix | auto-fix | auto-fix | auto-fix + custom rules |
| Gap analysis (community + code) | Y | Y | Y | Y | Y |
| Glossary sync | Y | Y | Y | Y | Y |
| Code example smoke tests | Y | Y | Y | Y | Y |
| Lifecycle management | Y | Y | Y | Y | Y |
| Docs normalization | Y | Y | Y | Y | Y |
| Multi-language code tabs | Y | Y | Y | Y | Y |
| API-first flow (OpenAPI generation) | - | Y | Y | Y | Y |
| API contract validation + Spectral | - | Y | Y | Y | Y |
| API sandbox (Prism/external mock) | - | Y | Y | Y | Y |
| API playground (Swagger UI) | - | Y | Y | Y | Y |
| Drift detection (API/SDK) | - | Y | Y | Y | Y |
| Docs-in-PR contract | - | Y | Y | Y | Y |
| Multi-protocol pipeline (GraphQL, gRPC, AsyncAPI, WebSocket) | - | - | Y | Y | Y |
| Protocol contract generation from planning notes | - | - | Y | Y | Y |
| Protocol self-verification against live/mock endpoints | - | - | Y | Y | Y |
| KPI wall + SLA dashboard | - | - | Y | Y | Y |
| Test assets generation + smart merge (5 protocols) | - | - | Y | Y | Y |
| Consolidated reports | - | - | Y | Y | Y |
| Public docs auditor (site crawl + quality assessment) | - | - | Y | Y | Y |
| API access | - | - | Y | Y | Y |
| SSO + audit logs | - | - | Y | Y | Y |
| Priority support | - | - | Y | Y | Y |
| Knowledge modules extraction | - | - | - | Y | Y |
| Knowledge graph (JSON-LD) | - | - | - | Y | Y |
| RAG pipeline (HyDE, hybrid search, cross-encoder reranking) | - | - | - | Y | Y |
| FAISS vector index + embedding cache | - | - | - | Y | Y |
| Retrieval evals (precision, recall, hallucination rate) | - | - | - | Y | Y |
| Executive audit PDF (consulting-grade reports) | - | - | - | Y | Y |
| LLM-powered expert analysis (audit + docs generation) | - | - | - | Y | Y |
| i18n system (sync + translate) | - | - | - | Y | Y |
| Custom policy packs | - | - | - | Y | Y |
| TestRail/Zephyr upload (with needs_review propagation) | - | - | - | Y | Y |
| Confluence migration tools | - | - | - | Y | Y |
| On-premises deployment | - | - | - | Y | Y |
| Dedicated support channel | - | - | - | Y | Y |
| SLA guarantee | - | - | - | Y | Y |
| Client bundle builder | - | - | - | - | Y |
| Custom CLAUDE.md generation | - | - | - | - | Y |
| Dedicated handover sessions | - | - | - | - | Y |
| Custom gate/policy creation | - | - | - | - | Y |
| Retainer with response SLA | - | - | - | - | Y |
| Team training sessions | - | - | - | - | Y |
| VeriDoc licenses included | - | - | - | - | Y |

**Note:** VeriDoc Enterprise has full feature parity with VeriOps automation.
The difference is delivery: Enterprise is self-service, VeriOps is done-for-you.
VeriOps exclusive items (bottom 7 rows) are services, not software features.

## Anti-cannibalization rules

### Why VeriDoc and VeriOps do not cannibalize each other

The difference is **delivery model**, not functionality. VeriDoc Enterprise
has full feature parity with VeriOps automation. Clients self-sort:

- **Tech-savvy teams** with docs culture buy VeriDoc Enterprise ($1,499/mo).
  They configure it themselves, use docs and tutorials, submit support tickets.
  Zero operator time required.
- **Teams without docs culture** buy VeriOps ($5K-25K + retainer). They need
  a human to set up, train, and maintain. Self-service for them means "bought,
  never configured, abandoned." They pay for results, not software.

This is the Salesforce model: same product, but some buy licenses and self-manage,
others pay Accenture $500K to configure it. Both are valid, non-competing segments.

### What VeriOps delivers beyond VeriDoc Enterprise

These are **services**, not software features:

1. **Client bundle builder** — custom docsops/ directory generation for client repos.
1. **Custom CLAUDE.md/AGENTS.md** — tailored agent contracts per client.
1. **Dedicated handover sessions** — live training and knowledge transfer.
1. **Custom gate creation** — bespoke quality gates built for specific compliance needs.
1. **Response SLA retainer** — guaranteed 4-48 hour response time.
1. **Multi-repo fleet orchestration** — coordinated pipeline across 3+ repos.
1. **VeriDoc licenses included** — client team gets VeriDoc access as part of the package.

### When a customer chooses VeriOps

- Data cannot leave their infrastructure (banks, healthcare, defense).
- Docs are in chaos, no docs culture, no dedicated person.
- Need custom gates or compliance policies built from scratch.
- Want team training and live handover sessions.
- Multi-repo with non-standard infrastructure.
- Regulatory compliance requires on-site audit trail.
- Pre-IPO or post-acquisition documentation overhaul.

### When a customer chooses VeriDoc Enterprise

- Strong internal docs culture, technical team can self-manage.
- Want to start today, not in two weeks.
- Standard requirements, no deep customization needed.
- Budget is per-repo, not project-based.

### Natural upsell path

VeriDoc Enterprise at $1,499/month ($17,988/year) covers unlimited repos with full
automation. VeriOps ($15K implementation + $1,500/mo retainer = $33K/year) adds
hands-on support plus local pipeline deployment on client infrastructure.
Companies naturally upgrade when they need custom gates, compliance, or fleet management.

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

**VeriOps** captures enterprise exodus:

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
    Starter: tries VeriDoc on one repo, runs migration tool
        |
        v
    Pro: expands to 5 repos, adds API-first, drift detection
        |
        v
    Business: scales to 15 repos, KPI dashboard, SSO
        |
        +-------> Happy at Business tier (majority)
        |
        v
    Needs: custom policies, on-prem, unlimited repos
        |
        v
    Enterprise SaaS or VeriOps engagement
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
Starter -> Pro: "Add API-first, drift detection, and scale to 5 repos"
Pro -> Business: "Add multi-protocol pipeline, test assets with smart merge, public docs auditor, KPI dashboard, SSO, and scale to 15 repos"
Business -> Enterprise: "Add RAG pipeline with HyDE/reranking, knowledge graph, executive PDF reports, LLM expert analysis, i18n, TestRail/Zephyr upload, custom policies, on-prem, unlimited"
Enterprise -> VeriOps: "Need custom setup, training, or fleet management?"
```

## Premium retainer tiers

After the initial project engagement ($5K-25K setup), clients transition to a monthly
retainer for ongoing docs operations support. Three tiers based on involvement depth:

### Retainer Lite ($1,500/month)

**Docs health monitoring** -- analogous to DevOps infrastructure monitoring.

Scope:

- Weekly review of `consolidated_report.json` (gaps, drift, KPI, SLA).
- Monitor KPI drift: quality score drops, new gaps, staleness growth.
- Generate fixes for routine issues (stale docs, minor drift).
- Provide recommendations for non-trivial issues requiring team input.
- Monthly health summary report with trends.

Deliverables:

- Up to 8 hours/month of active work.
- Response within 48 hours on routine issues.
- Monthly health report email.

Best fit: teams that completed initial setup and can self-manage day-to-day,
but want a safety net and ongoing quality assurance.

### Retainer Growth ($3,000/month)

**Monitoring + expansion** -- everything in Lite plus proactive growth work.

Scope:

- Everything in Retainer Lite.
- Expand pipeline to new repositories (up to 2 new repos/month).
- Configure and maintain i18n system for new locales.
- Build and update knowledge/RAG layer (knowledge modules, retrieval evals).
- Update policy packs when product or compliance requirements change.
- Quarterly pipeline audit and optimization.

Deliverables:

- Up to 20 hours/month of active work.
- Response within 24 hours.
- Quarterly audit report with pipeline improvements.

Best fit: growing companies adding new products, entering new markets (i18n),
or building out their knowledge management layer.

### Retainer Critical ($6,000/month)

**Acting Head of Docs Operations** -- full operational ownership.

Scope:

- Everything in Retainer Growth.
- Full operational ownership of the documentation pipeline.
- Decide what to generate, when to update, and how to prioritize.
- Maintain and evolve pipeline infrastructure (scripts, templates, configs).
- Own KPI SLA compliance: responsible for meeting quality targets.
- Manage template library and update templates as product evolves.
- Coordinate with engineering on API-first flow and drift resolution.
- Attend weekly standups or async updates with engineering leads.
- Train new team members on pipeline operations.

Deliverables:

- Up to 40 hours/month (effectively part-time embedded role).
- Response within 4 hours during business hours.
- Weekly status report and KPI dashboard update.
- Direct Slack/Teams channel access.

Best fit: companies without a dedicated docs lead, companies going through
rapid growth or product launches, regulated industries requiring continuous
compliance monitoring.

### Retainer tier comparison

| Aspect | Lite $1,500/mo | Growth $3,000/mo | Critical $6,000/mo |
| --- | --- | --- | --- |
| Hours/month | Up to 8 | Up to 20 | Up to 40 |
| Response time | 48 hours | 24 hours | 4 hours (business) |
| Weekly report review | Y | Y | Y |
| Fix generation | Routine only | Routine + expansion | Full ownership |
| New repo expansion | - | Up to 2/month | Unlimited |
| i18n setup | - | Y | Y |
| Knowledge/RAG layer | - | Y | Y |
| Policy pack updates | - | Y | Y |
| Pipeline maintenance | - | - | Y |
| Template evolution | - | - | Y |
| KPI SLA ownership | - | - | Y |
| Team training | - | - | Y |
| Direct channel access | - | - | Y |

### Retainer revenue model

Retainers are the most predictable revenue stream. Expected progression:

- Year 1: 5-10 active retainers (mix of Lite and Growth) = $90K-270K ARR.
- Year 2: 15-25 retainers + 2-5 Critical = $270K-750K ARR.
- Year 3: 30-50 retainers via partners = $540K-1.5M ARR.

Most clients start at Lite after project completion. Upsell to Growth happens
when they add new repos or enter new markets. Critical is rare but
high-value -- typically pre-IPO or post-acquisition documentation overhauls.

## Revenue protection

### Premium protects SaaS

- Premium clients generate case studies and testimonials.
- Premium success stories drive SaaS adoption.
- VeriOps surfaces feature requests for SaaS roadmap.

### SaaS protects Premium

- SaaS provides a self-serve pilot experience before premium engagement.
- SaaS demonstrates product value without sales overhead.
- SaaS handles clients too small for premium, preventing revenue leakage.

## Technical sync rules

### What flows from VeriOps to VeriDoc

All scripts in `scripts/` are synced to `git_wrapper/scripts/`. This includes
the multi-protocol pipeline (`run_multi_protocol_contract_flow.py`, protocol validators,
`generate_protocol_test_assets.py`, `run_protocol_self_verify.py`), the RAG pipeline
(`generate_embeddings.py`, `run_retrieval_evals.py`, `generate_knowledge_graph_jsonld.py`),
the public docs auditor (`generate_public_docs_audit.py`, `generate_executive_audit_pdf.py`,
`generate_audit_scorecard.py`), and the test upload flow (`upload_api_test_assets.py`).
The docs pipeline modules in `packages/core/gitspeak_core/docs/` wrap these scripts
for the SaaS context.

### What stays exclusive to VeriOps

- `profiles/clients/` — client-specific configuration profiles.
- `instructions/llm_plans/` — tier-specific agent instructions for client repos.
- Client handoff documents (CLIENT_HANDOFF.md, OPERATOR_QUESTIONNAIRE.md).
- Sales playbooks and pricing cheatsheets.

### Sync cadence

When a new feature is added to VeriOps:

1. Implement and test in VeriOps.
1. Copy the script to `git_wrapper/scripts/`.
1. Add wrapper module in `gitspeak_core/docs/` if needed.
1. Add feature gate in `gitspeak_core/saas/` for the correct tier.
1. Update pricing.py feature list.

## Implementation status (2026-03-25)

This document is aligned to the current production implementation baseline.

Current baseline:

1. The platform is docs-first and also supports `code-first`, `api-first`, and `hybrid` flows.
1. REST and non-REST protocols are supported in one automation model: REST, GraphQL, gRPC, AsyncAPI, and WebSocket.
1. Non-REST automation includes server stubs with business-logic placeholders.
1. External mock sandbox resolution is integrated into the smooth autopipeline, including Postman-supported auto-prepare mode.
1. Contract test assets are generated automatically and merged with smart-merge rules so manual/customized cases are preserved.
1. Knowledge/RAG tasks run as part of automation when enabled (module extraction, validation, retrieval index, graph, evals).
1. Plan gating is enforced by configuration and policy packs; advanced non-REST automation is reserved for higher plans.

Canonical execution order reference:

- `docs/operations/CANONICAL_FLOW.md`
- `docs/operations/UNIFIED_CLIENT_CONFIG.md`
- `README.md`

Commercial note:

- Where commercial packaging is discussed, recurring service terms (retainer/licensing) are part of the active go-to-market model.

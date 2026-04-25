# Start the 21-day pilot

This guide explains how to run the current VeriOps pilot in one real repository.

## Commercial model (current)

- Pilot: `$5,000` for 21 calendar days.
- Full implementation: `$15,000` one-time.
- RAG add-on: `$10,000` one-time (optional).
- Monthly retainer after implementation: `$1,500`, `$3,000`, or `$6,000`.

## What the 21-day pilot includes

1. One repository onboarding (`bundle-only` or `install-local`).
1. Baseline configuration and policy pack setup.
1. One complete docs cycle from a free-form prompt.
1. One complete API-first cycle from planning notes.
1. Weekly automation check and consolidated report review.
1. KPI baseline and handoff session.

## What is not included in pilot

1. Multi-repository rollout.
1. Organization-wide change management.
1. Full RAG runtime unless purchased as add-on.
1. 24/7 SLA support.

## Pilot workflow

## Step 1: Prepare environment

```bash
python3 -m pip install -r requirements.txt
npm install
```

## Step 2: Build/install client bundle

```bash
python3 scripts/onboard_client.py --mode bundle-only
# or
python3 scripts/onboard_client.py --mode install-local
```

## Step 3: Run setup wizard in client repo

```bash
python3 docsops/scripts/setup_client_env_wizard.py
```

## Step 4: Run autopipeline from free-form intent

```bash
python3 scripts/run_autopipeline.py --docsops-root docsops --reports-dir reports --auto-generate
```

## Step 5: Validate outputs

```bash
npm run lint
python3 scripts/validate_knowledge_modules.py
python3 scripts/generate_knowledge_retrieval_index.py
```

## Step 6: Prepare pilot decision report

At day 21, provide:

1. What passed/failed.
1. Open risks.
1. What full implementation unlocks.
1. GO/NO-GO decision.

## Upgrade path after pilot

- If client upgrades to full: expand to full scope, keep existing artifacts.
- If client does not upgrade: delivered baseline remains, advanced capabilities degrade by plan/license policy.

## Related docs

- `PILOT_WEEK_OFFER.md`
- `PILOT_VS_FULL_IMPLEMENTATION.md`
- `docs/operations/PLAN_TIERS.md`
- `docs/operations/UNIFIED_CLIENT_CONFIG.md`

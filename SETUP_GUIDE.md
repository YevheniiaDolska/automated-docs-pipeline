# Setup guide

This is the canonical technical setup document.

## 1. Prerequisites

- Python 3.11+
- Node.js 18+
- Git

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
npm install
```

## 2. Onboarding paths

### Path A: Bundle only

```bash
python3 scripts/onboard_client.py --mode bundle-only
```

### Path B: Install local

```bash
python3 scripts/onboard_client.py --mode install-local
```

Then run setup wizard in client repo:

```bash
python3 docsops/scripts/setup_client_env_wizard.py
```

## 3. Run autopipeline

```bash
python3 scripts/run_autopipeline.py --docsops-root docsops --reports-dir reports --auto-generate
```

## 4. Validate generated outputs

```bash
npm run lint
python3 scripts/extract_knowledge_modules_from_docs.py --docs-dir docs --modules-dir knowledge_modules --report reports/knowledge_auto_extract_report.json
python3 scripts/validate_knowledge_modules.py
python3 scripts/generate_knowledge_retrieval_index.py
```

## 5. Deployment/runtime modes

- Cloud
- Hybrid
- Strict-local (air-gapped)

Strict-local defaults to local runtime where configured (for example, local Ollama path), with optional BYOK mode when external providers are enabled by policy.

## 6. Plan boundaries

- Community/degraded: free lint defaults only.
- Full: full autopipeline except retrieval-time RAG.
- Full+RAG: full autopipeline including retrieval-time RAG.

## 7. Canonical references

- `docs/operations/CANONICAL_FLOW.md`
- `docs/operations/UNIFIED_CLIENT_CONFIG.md`
- `docs/operations/PLAN_TIERS.md`
- `docs/operations/PIPELINE_CAPABILITIES_CATALOG.md`

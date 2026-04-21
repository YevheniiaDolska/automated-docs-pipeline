# Staging RAG live-load validation (2026-04-21)

- Commit deployed to staging source repo (`/opt/veridoc-staging`): `fd95dcd` (`fix(rag): keep metrics endpoint alive when snapshot write fails`).
- Environment: `https://staging.veri-doc.app`
- Auth context: enterprise-tier test user (subscription updated to `enterprise`, `active` on staging DB).

## Checks

1. Health
   - `GET http://127.0.0.1:8010/health` -> `200`
2. RAG query load
   - 30 sequential `POST /rag/query`
   - Result codes in `rag_load_codes.txt`: `30 x 200`
3. Metrics endpoint under load
   - `GET /rag/metrics` before load -> `200`, `status=ok`, `window_rows=0`
   - `GET /rag/metrics` after load -> `200`, `status=degraded`, `window_rows=30`
4. Alerts endpoint under load
   - `GET /rag/alerts` after load -> `200`, alert raised: `RAG_NO_HIT_RATE_HIGH` (expected for no-hit synthetic queries)
5. Public staging route check
   - `GET https://staging.veri-doc.app/api/rag/metrics` -> `200`
   - `GET https://staging.veri-doc.app/api/rag/alerts` -> `200`

## Artifacts

- `reports/staging-rag-gate-20260421/rag_metrics_before.json`
- `reports/staging-rag-gate-20260421/rag_metrics_after.json`
- `reports/staging-rag-gate-20260421/rag_alerts_after.json`
- `reports/staging-rag-gate-20260421/rag_load_codes.txt`

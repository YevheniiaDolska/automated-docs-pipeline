---
title: Network transparency reference
description: Complete list of all outgoing network requests the pipeline makes, with
  exact payload schemas. No client data leaves your network.
content_type: reference
product: both
tags:
- Reference
last_reviewed: '2026-03-26'
original_author: Kroha
---


<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

# Network transparency reference

The {{ product_name }} pipeline is a locally installed tool that generates documentation using your own LLM. This reference lists every outgoing network request the pipeline can make, with exact payload schemas. You can verify each claim with a packet capture tool.

## Zero client data guarantee

The pipeline processes all documentation locally. Your source code, API contracts, documentation content, and generated outputs never leave your network. The only outgoing requests contain license metadata and version information.

## Complete outgoing request inventory

The pipeline makes exactly 5 types of outgoing HTTP requests. Each request is listed below with the exact JSON schema of what is sent.

### Request 1: License activation

**When:** First time setup, or when re-activating after a license key change.

**Endpoint:** `POST /v1/activate`

**Frequency:** Once per installation.

```json
{
  "key": "VDOC-PRO-acme-a8f3b2c1",
  "machine_fingerprint": "sha256-hex-string-64-chars"
}
```

**Field details:**

| Field | Type | Description | Contains client data? |
| --- | --- | --- | --- |
| `key` | string | License key provided by VeriOps sales | No |
| `machine_fingerprint` | string | SHA-256 of `hostname + OS + username + repo_path` | No (one-way hash, not reversible) |

**What is NOT sent:** No file names, no document content, no source code, no API contracts, no IP addresses beyond the TCP connection itself.

**How to verify:**

```bash
# Capture the activation request with tcpdump
sudo tcpdump -i any -A host licensing.veriops.dev port 443

# Or use mitmproxy for HTTPS inspection
mitmproxy --mode upstream:https://licensing.veriops.dev
```

### Request 2: Capability pack refresh

**When:** During weekly batch run, or when the current pack approaches expiration.

**Endpoint:** `POST /v1/pack/refresh`

**Frequency:** Weekly (configurable per plan).

```json
{
  "authorization": "Bearer <license-jwt>"
}
```

The JWT contains only license metadata (client ID, plan tier, expiration). The JWT payload schema:

```json
{
  "sub": "acme-corp",
  "plan": "enterprise",
  "iat": 1750000000,
  "exp": 1781536000
}
```

**What is NOT sent:** No document content, no file listings, no quality scores, no report data.

### Request 3: Update check

**When:** During weekly batch run, or manual `python3 scripts/check_updates.py`.

**Endpoint:** `GET /v1/check`

**Frequency:** Weekly (automatic), or on-demand.

```text
GET /v1/check?version=1.2.0&platform=linux-x86_64
User-Agent: VeriOps-Pipeline-Updater/1.0
```

**Query parameters:**

| Parameter | Type | Description | Contains client data? |
| --- | --- | --- | --- |
| `version` | string | Current installed pipeline version | No |
| `platform` | string | OS and architecture identifier | No |

**What is NOT sent:** No license info, no document counts, no quality metrics, no file paths.

### Request 4: Update download

**When:** After an update check finds a new version and the user approves.

**Endpoint:** `GET /v1/download/{version}/{platform}`

**Frequency:** When updates are available (monthly for Professional, weekly opt-in for Enterprise).

```text
GET /v1/download/1.3.0/linux-x86_64
```

**What is NOT sent:** No request body. No authentication headers. No client data of any kind.

### Request 5: License deactivation

**When:** When a client explicitly deactivates their license (seat release).

**Endpoint:** `POST /v1/deactivate`

**Frequency:** Once per deactivation.

```json
{
  "authorization": "Bearer <license-jwt>"
}
```

**What is NOT sent:** No reason codes, no usage data, no document counts.

## Requests the pipeline never makes

The following types of requests are architecturally impossible because the pipeline contains no code to construct them:

| Category | Why it cannot happen |
| --- | --- |
| Document content upload | No upload endpoint exists in the codebase. Search for `urllib` calls yourself. |
| File listing transmission | Pipeline reads files locally; no serialization-to-server code exists. |
| Quality score reporting | Scores are computed locally and written to local `reports/` directory. |
| Source code exfiltration | Pipeline scripts operate on `docs/` and `api/` directories only. |
| Telemetry or analytics | No telemetry SDK is included. No analytics endpoint is configured. |
| User behavior tracking | No session tracking, no event logging to external services. |

## How to audit the pipeline yourself

### Network audit with tcpdump

Run the full weekly batch while capturing all outgoing traffic:

```bash
# Terminal 1: Start packet capture
sudo tcpdump -i any -w pipeline-traffic.pcap \
  'not (src net 10.0.0.0/8 or src net 172.16.0.0/12 or src net 192.168.0.0/16)'

# Terminal 2: Run the pipeline
python3 scripts/run_weekly_gap_batch.py \
  --docsops-root docsops --reports-dir reports

# Terminal 1: Stop capture (Ctrl+C), then analyze
tcpdump -r pipeline-traffic.pcap -A | grep -i "POST\|GET\|Host:"
```

### Air-gapped operation

The pipeline works without any network access. Set these to disable all outgoing requests:

```bash
# Block all VeriOps server communication
export VERIOPS_UPDATE_SERVER=""
export VERIOPS_LICENSE_PLAN=enterprise  # Dev/test bypass

# Run pipeline in fully offline mode
python3 scripts/run_weekly_gap_batch.py --docsops-root docsops
```

Without network access, the pipeline uses:

- Local license JWT file (`docsops/license.jwt`) for offline validation
- Local capability pack (`docsops/.capability_pack.enc`) for scoring weights
- Offline grace period (3, 7, or 30 days depending on plan tier) before degrading to community mode

### Source code audit

Every network call in the pipeline is in exactly 2 files:

```bash
# Find all outgoing HTTP calls in the pipeline
grep -rn "urlopen\|urllib\|requests\.\|httpx\.\|aiohttp" scripts/ build/

# Expected results: only in these files:
#   scripts/check_updates.py  -- update check + download
#   scripts/generate_public_docs_audit.py -- web crawler (optional, enterprise only)
```

The `generate_public_docs_audit.py` script crawls public documentation sites for quality auditing. It accesses only URLs explicitly provided by the user via `--site-url` arguments. It does not contact VeriOps servers.

## Machine fingerprint details

The machine fingerprint is a SHA-256 hash used for seat counting. It is computed from:

```python
parts = [
    platform.node(),      # Hostname (e.g., "dev-server-01")
    platform.system(),    # OS (e.g., "Linux")
    os.getenv("USER"),    # Username (e.g., "deploy")
    str(REPO_ROOT),       # Repository path (e.g., "/opt/docs-pipeline")
]
fingerprint = sha256("|".join(parts))
# Result: "a1b2c3d4..." (64 hex characters)
```

The hash is one-way. VeriOps cannot reconstruct your hostname, username, or file paths from the fingerprint. The fingerprint changes if you move the pipeline to a different machine, which requires re-activation (seat transfer).

## Capability pack contents

The encrypted capability pack (`docsops/.capability_pack.enc`) contains scoring intelligence, not client data. Contents after decryption:

| Section | What it contains | Example values |
| --- | --- | --- |
| `scoring.geo_rules` | GEO optimization thresholds | `first_para_max_words: 60` |
| `scoring.kpi_weights` | Quality score formula weights | `metadata_weight: 0.35` |
| `scoring.audit_weights` | 7-pillar audit scoring weights | `content_quality: 0.22` |
| `scoring.sla_thresholds` | SLA breach detection thresholds | `min_quality_score: 70` |
| `priority` | Action item tier classification | `tier1_categories: [breaking_change]` |
| `prompts` | Documentation quality prompt templates | Stripe-quality formula text |
| `policies` | Quality gate enforcement rules | `vale_blocks_commit: true` |

The pack is encrypted with AES-256-GCM. The encryption key is derived from your license key via HKDF-SHA256. Only your installation can decrypt your pack.

## Summary of data flow

```text
Your Network                              VeriOps Server
+----------------------------------+      +----------------------+
| docs/ (your content)             |      |                      |
| api/ (your contracts)            |      | Receives ONLY:       |
| reports/ (your quality scores)   |      |  - License key       |
|                                  |      |  - Machine hash      |
| ALL processing happens here:     |      |  - Version string    |
|  - Linting                       |      |  - Platform string   |
|  - Scoring                       |      |                      |
|  - Gap analysis           ------>|      | Sends BACK:          |
|  - KPI wall               NEVER  |      |  - Signed JWT        |
|  - PDF generation                |      |  - Encrypted pack    |
|  - Knowledge modules             |      |  - Update bundles    |
|  - Test asset generation         |      |                      |
+----------------------------------+      +----------------------+
```

## Next steps

- [Documentation index](index.md)

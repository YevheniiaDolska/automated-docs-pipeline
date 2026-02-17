---
title: "Configuration guide"
description: "Configure [Product] for local, staging, and production with safe defaults, environment variables, and operational checks."
content_type: how-to
product: both
tags:
  - How-To
  - Configuration
  - Security
---

# Configuration guide

Use this guide to move from default config to production-ready configuration without surprises.

## Quick start (minimal working configuration)

```bash
export PRODUCT_ENV=development
export PRODUCT_PORT=8080
export PRODUCT_DATABASE_URL="postgres://user:pass@localhost:5432/product"
export PRODUCT_ENCRYPTION_KEY="replace-with-32-byte-secret"
```

```yaml
# config.yml
server:
  host: 0.0.0.0
  port: 8080
security:
  encryption_key: ${PRODUCT_ENCRYPTION_KEY}
```

## Configuration precedence

1. Runtime flags
1. Environment variables
1. Config file values
1. Built-in defaults

## Environment profiles

| Profile | Purpose | Key differences |
| --- | --- | --- |
| local | Development on laptop | Debug logs on, lower limits |
| staging | Pre-production validation | Production-like integrations |
| production | Live traffic | Strict security and observability |

## Core settings

| Setting | Description | Example |
| --- | --- | --- |
| `PRODUCT_PORT` | HTTP listener port | `8080` |
| `PRODUCT_BASE_URL` | Public base URL for callbacks | `https://api.example.com` |
| `PRODUCT_DATABASE_URL` | Primary data store DSN | `postgres://...` |
| `PRODUCT_LOG_LEVEL` | Logging verbosity | `info` |
| `PRODUCT_REGION` | Deployment region tag | `us-east-1` |

## Security-critical settings

| Setting | Why it matters | Recommendation |
| --- | --- | --- |
| `PRODUCT_ENCRYPTION_KEY` | Protects sensitive data at rest | 32+ random bytes, rotate quarterly |
| `PRODUCT_JWT_SIGNING_KEY` | Signs service tokens | Use KMS/HSM-managed key when possible |
| `PRODUCT_WEBHOOK_SECRET` | Verifies incoming webhooks | Unique per endpoint, rotate regularly |

## Cloud vs self-hosted

=== "Cloud"

    Configuration is managed through control-plane settings. Document only tenant-specific options and integration credentials.

=== "Self-hosted"

    Use environment variables for secrets and keep non-secret defaults in versioned config files.

## Recommended production baseline

```yaml
# config.production.yml
server:
  port: 8080
  request_timeout_ms: 30000

limits:
  max_request_body_mb: 5
  max_concurrency: 200

retries:
  upstream_max_attempts: 3
  base_backoff_ms: 200

observability:
  metrics_enabled: true
  trace_sampling_rate: 0.1
```

## Validation and rollout

1. Run config linter before deploy.
1. Validate required secrets exist.
1. Deploy to staging first.
1. Smoke test critical paths.
1. Promote to production.

## Common failures and fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Service fails on startup | Missing required secret | Add secret and restart |
| Callback URLs incorrect | Wrong base URL | Set `PRODUCT_BASE_URL` to public URL |
| Slow API responses | Too-low timeouts/retries | Tune limits and backoff |

## Adaptation notes for template users

Replace placeholders:

- `[Product]`
- `PRODUCT_*` variable names
- DSN format, limits, and defaults

## Related docs

- `templates/configuration-reference.md`
- `templates/security-guide.md`
- `templates/testing-guide.md`

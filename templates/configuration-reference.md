---
title: "Configuration reference"
description: "Complete reference of [Product] configuration: environment variables, file keys, defaults, allowed values, and validation rules."
content_type: reference
product: both
tags:
  - Reference
  - Configuration
---

# Configuration reference

This page is the source of truth for configuration behavior. Keep values exact and versioned.

## How to read this reference

- Use this page for exact keys and allowed values.
- Use `templates/configuration-guide.md` for workflows and rollout strategy.

## Precedence and loading order

1. CLI/runtime flag
1. Environment variable
1. Configuration file
1. Internal default

## Environment variables

| Variable | Type | Required | Default | Allowed values | Notes |
| --- | --- | --- | --- | --- | --- |
| `PRODUCT_ENV` | string | No | `production` | `development`, `staging`, `production` | Controls mode-specific defaults |
| `PRODUCT_PORT` | integer | No | `8080` | `1-65535` | Public API listener |
| `PRODUCT_BASE_URL` | string | Yes | - | valid URL | Must be externally reachable |
| `PRODUCT_DATABASE_URL` | string | Yes | - | DSN | Required at startup |
| `PRODUCT_LOG_LEVEL` | string | No | `info` | `debug`, `info`, `warn`, `error` | Prefer `info` in production |
| `PRODUCT_ENCRYPTION_KEY` | string | Yes | - | 32+ bytes | Secret, never log |

## File-based configuration keys

```yaml
server:
  host: 0.0.0.0
  port: 8080
  request_timeout_ms: 30000

database:
  pool_min: 5
  pool_max: 25

security:
  cors_allow_origins:
    - https://app.example.com
```

## Schema constraints

| Key | Constraint |
| --- | --- |
| `server.request_timeout_ms` | `1000-120000` |
| `database.pool_max` | must be `>= database.pool_min` |
| `security.cors_allow_origins` | no wildcard in production |

## Sensitive keys

Treat these as secrets:

- `PRODUCT_ENCRYPTION_KEY`
- `PRODUCT_DATABASE_URL`
- `PRODUCT_WEBHOOK_SECRET`
- `PRODUCT_JWT_SIGNING_KEY`

## Example: complete production config

```yaml
server:
  host: 0.0.0.0
  port: 8080
  request_timeout_ms: 30000

database:
  url: ${PRODUCT_DATABASE_URL}
  pool_min: 10
  pool_max: 50

security:
  encryption_key: ${PRODUCT_ENCRYPTION_KEY}
  cors_allow_origins:
    - https://app.example.com

observability:
  metrics_enabled: true
  log_level: info
```

## Validation checklist

- [ ] Required keys are present.
- [ ] No secret is hardcoded in repository files.
- [ ] Production values are explicit, not implicit defaults.
- [ ] Limits and pools are sized for expected load.

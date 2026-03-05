---
title: "Upgrade to [Product] [version]"
description: "Upgrade [Product] from [old version] to [new version]: breaking changes, migration steps, rollback procedure, and verification checklist."
content_type: how-to
product: both
tags:
  - How-To
  - Self-hosted
---

# Upgrade to [Product] [version]

[Product] [version] introduces [primary feature] and improves [metric] by [percentage]. This guide walks you through upgrading from [old version], covering breaking changes, data migration, and rollback procedures.

## Upgrade summary

| Aspect | Details |
| --- | --- |
| **From version** | [old version] |
| **To version** | [new version] |
| **Estimated time** | [N] minutes (+ [N] minutes for large datasets) |
| **Downtime required** | Yes / No / Rolling upgrade supported |
| **Database migration** | Yes / No |
| **Breaking changes** | [N] (see below) |

## Breaking changes

!!! warning "Read before upgrading"
    These changes require action before or during the upgrade.

### 1. [Breaking change title]

**What changed**: [Previous behavior] is now [new behavior].

**Impact**: [Who is affected and how]

**Migration**:

```bash
# Before upgrade: export old format
[product-cli] export --format v1 --output backup-v1.json

# After upgrade: import to new format
[product-cli] import --format v2 --input backup-v1.json --migrate
```

### 2. [Breaking change title]

**What changed**: Configuration key `old_key` renamed to `new_key`.

**Migration**: Update your configuration file:

```yaml
# Before ({{ min_supported_version }})
old_key: "value"

# After ({{ current_version }})
new_key: "value"
```

## Pre-upgrade checklist

- [ ] Back up your database: `pg_dump -U [product] -d [product_db] > backup.sql`
- [ ] Back up configuration: `cp -r {{ default_config_path }} {{ default_config_path }}.bak`
- [ ] Read all breaking changes above
- [ ] Verify current version: `[product-cli] --version`
- [ ] Test upgrade in staging environment first
- [ ] Schedule maintenance window: [N] minutes
- [ ] Notify affected users

## Upgrade steps

### Step 1: Stop the service

```bash
systemctl stop [product]
```

### Step 2: Update to new version

=== "Docker"

    ```bash
    docker pull [product]:{{ current_version }}
    docker compose up -d
    ```

=== "Package manager"

    ```bash
    # Debian/Ubuntu
    apt update && apt install [product]={{ current_version }}

    # RHEL/CentOS
    yum update [product]-{{ current_version }}
    ```

=== "Binary"

    ```bash
    curl -L https://releases.example.com/[product]/{{ current_version }}/[product]-linux-amd64 \
      -o /usr/local/bin/[product]
    chmod +x /usr/local/bin/[product]
    ```

### Step 3: Run database migration

```bash
[product-cli] db migrate --target {{ current_version }}
# Expected output: "Migration completed: 3 migrations applied"
```

### Step 4: Start and verify

```bash
systemctl start [product]

# Verify version
curl -s http://localhost:{{ default_port }}/health | jq .version
# Expected: "{{ current_version }}"

# Verify core functionality
[product-cli] self-test
# Expected: "All 12 checks passed"
```

## Rollback procedure

If issues occur after upgrading:

```bash
# 1. Stop new version
systemctl stop [product]

# 2. Restore database
psql -U [product] -d [product_db] < backup.sql

# 3. Restore configuration
cp -r {{ default_config_path }}.bak {{ default_config_path }}

# 4. Reinstall previous version
docker pull [product]:{{ min_supported_version }}
docker compose up -d

# 5. Verify rollback
curl -s http://localhost:{{ default_port }}/health | jq .version
# Expected: "{{ min_supported_version }}"
```

## Post-upgrade verification

| Check | Command | Expected result |
| --- | --- | --- |
| Service health | `curl localhost:{{ default_port }}/health` | `{"status": "healthy"}` |
| Version | `[product-cli] --version` | `{{ current_version }}` |
| Database | `[product-cli] db status` | `"up to date"` |
| API response | `curl localhost:{{ default_port }}/api/{{ api_version }}/status` | HTTP 200 |
| Existing data | Spot-check 5 records in UI | Data intact |

## Next steps

- [Release notes](../releases/[version].md) for full changelog
- [Migration guide](../how-to/migrate-data.md) for data format changes
- [Configuration reference](../reference/configuration.md) for new settings

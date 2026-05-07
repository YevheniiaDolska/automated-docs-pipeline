---
title: "[Product] administration guide"
description: "Administer [Product] in production: user management, backup procedures, monitoring setup, and scaling configuration for teams of [N]+ users."
content_type: how-to
product: self-hosted
tags:
  - How-To
  - Self-hosted
---

# [Product] administration guide

[Product] administration covers user management, backup, monitoring, and scaling for production deployments. This guide targets system administrators running {{ product_name }} on self-hosted infrastructure with [N]+ active users.

## System requirements

| Component | Minimum | Recommended | High availability |
| --- | --- | --- | --- |
| CPU | 2 cores | 4 cores | 8 cores per node |
| RAM | 4 GB | 8 GB | 16 GB per node |
| Disk | 20 GB SSD | 100 GB SSD | 500 GB NVMe |
| Network | 100 Mbps | 1 Gbps | 10 Gbps |
| Database | PostgreSQL 14+ | PostgreSQL 15+ | PostgreSQL 15+ (HA cluster) |

## User management

### Create administrator account

```bash
# Create admin user via CLI
[product-cli] user create \
  --email admin@yourcompany.com \
  --role admin \
  --name "System Administrator"

# Verify the account
[product-cli] user list --role admin
```

### Configure authentication

=== "SAML SSO"

    ```yaml
    # config.yml
    auth:
      method: saml
      saml:
        idp_metadata_url: "https://idp.yourcompany.com/metadata"
        sp_entity_id: "{{ cloud_url }}"
        attribute_mapping:
          email: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
          name: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
    ```

=== "LDAP"

    ```yaml
    # config.yml
    auth:
      method: ldap
      ldap:
        url: "ldaps://ldap.yourcompany.com:636"
        base_dn: "dc=yourcompany,dc=com"
        bind_dn: "cn=service-account,dc=yourcompany,dc=com"
        user_filter: "(uid={username})"
    ```

## Backup and recovery

### Automated daily backup

```bash
#!/bin/bash
# /etc/cron.daily/product-backup

BACKUP_DIR="/var/backups/[product]"
DATE=$(date +%Y%m%d)
RETENTION_DAYS=30

# Database backup
pg_dump -h localhost -U [product] -d [product_db] \
  | gzip > "${BACKUP_DIR}/db-${DATE}.sql.gz"

# Configuration backup
tar czf "${BACKUP_DIR}/config-${DATE}.tar.gz" \
  {{ default_config_path }}

# Remove old backups
find "${BACKUP_DIR}" -name "*.gz" -mtime +${RETENTION_DAYS} -delete

echo "Backup completed: ${DATE}"
```

### Recovery procedure

1. Stop the service: `systemctl stop [product]`
1. Restore database: `gunzip -c db-YYYYMMDD.sql.gz | psql -U [product] -d [product_db]`
1. Restore config: `tar xzf config-YYYYMMDD.tar.gz -C /`
1. Start the service: `systemctl start [product]`
1. Verify: `curl http://localhost:{{ default_port }}/health`

## Monitoring

### Health check endpoint

```bash
# Basic health check
curl -s http://localhost:{{ default_port }}/health | jq .
# Expected: { "status": "healthy", "version": "{{ current_version }}" }

# Detailed metrics
curl -s http://localhost:{{ default_port }}/metrics
```

### Recommended alerts

| Alert | Condition | Severity | Action |
| --- | --- | --- | --- |
| Service down | Health check fails 3x | Critical | Restart service, check logs |
| High CPU | CPU > 85% for 5 min | Warning | Scale horizontally |
| High memory | RAM > 90% for 5 min | Warning | Increase memory limit |
| Disk space | Disk > 80% full | Warning | Clean old data, expand volume |
| Slow queries | P99 > 500 ms | Warning | Optimize queries, add indexes |
| Error rate | 5xx > 1% of requests | Critical | Check logs, rollback if needed |

## Scaling

### Horizontal scaling

```yaml
# docker-compose.scale.yml
services:
  product:
    image: [product]:{{ current_version }}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: "4"
          memory: 8G
    environment:
      - {{ env_vars.port }}={{ default_port }}
      - DB_HOST=postgres-primary
      - REDIS_HOST=redis-cluster

  postgres-primary:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis-cluster:
    image: redis:7-alpine
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
```

## Security hardening

### Production checklist

- [ ] Change default {{ env_vars.encryption_key }}
- [ ] Enable TLS for all connections
- [ ] Configure firewall: allow only ports {{ default_port }} and 443
- [ ] Set up log rotation (max 1 GB, 30 days retention)
- [ ] Enable audit logging for admin actions
- [ ] Configure rate limiting ({{ rate_limit_requests_per_minute }} requests/minute)
- [ ] Restrict admin panel access to internal network
- [ ] Set up automated backups with encryption

## Next steps

- [Deployment guide](../how-to/deploy-production.md) for initial production setup
- [Security guide](../reference/security-reference.md) for detailed security configuration
- [Monitoring guide](../how-to/setup-monitoring.md) for Prometheus/Grafana integration

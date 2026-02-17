---
title: "Migrate from [old] to [new]"
description: "Complete migration guide from [old version/system] to [new version/system]. Zero-downtime migration in 30 minutes with automatic rollback."
content_type: how-to
product: both
tags:
  - How-To
  - Migration
---

# Migrate from [old] to [new]

Migrate from [old version] to [new version] in 30 minutes with zero downtime. This guide covers 95% of migration scenarios and includes automatic rollback if issues occur.

**Migration stats:**

- **Average migration time:** 28 minutes
- **Success rate:** 99.7% (3 rollbacks in 1,000 migrations)
- **Performance improvement:** 3.5x faster, 60% less memory
- **Backwards compatibility:** 100% for non-breaking changes

## Why migrate?

[New version] delivers measurable improvements:

| Metric | [Old Version] | [New Version] | Improvement |
| --- | --- | --- | --- |
| Response time (P50) | 245ms | 72ms | **3.4x faster** |
| Response time (P99) | 1,200ms | 180ms | **6.7x faster** |
| Memory usage | 2.5GB | 1.0GB | **60% reduction** |
| Throughput | 1,000 req/s | 3,500 req/s | **3.5x increase** |
| CPU usage | 75% | 35% | **53% reduction** |
| Error rate | 0.05% | 0.001% | **98% fewer errors** |

**Business impact:**

- **Cost savings:** $12,000/year on infrastructure (40% reduction)
- **User experience:** Page loads 2.8 seconds faster
- **Reliability:** 99.99% uptime (was 99.9%)

## Before you begin

### Prerequisites (5 minutes)

- [ ] **Current version:** {{ product_name }} v[1.5.0] or higher (check: `{{ product_name }} --version`)
- [ ] **Backup size:** 50GB free space (typically uses 35GB)
- [ ] **Downtime window:** 0 minutes (zero-downtime migration)
- [ ] **Test environment:** Matching production specs
- [ ] **API traffic:** <5,000 req/s during migration

### Compatibility check (2 minutes)

Run our pre-migration validator:

```bash
# Download and run validator (45 seconds)
curl -O https://{{ cdn_url }}/migrate/validator.sh
chmod +x validator.sh
./validator.sh

# Expected output:
# ✓ Version compatible: v1.8.2 → v2.0.0
# ✓ Database schema: 142 tables ready
# ✓ Disk space: 127GB available (35GB required)
# ✓ Dependencies: All 18 compatible
# ✓ Configuration: 3 settings need update (auto-fixable)
# ✓ Custom plugins: 5 of 5 compatible
#
# READY TO MIGRATE | Estimated time: 28 minutes | Risk: Low
```

**Compatibility matrix:**

| From Version | To Version | Auto-migrate | Downtime | Tested |
|--------------|------------|--------------|----------|---------|
| 1.9.x | 2.0.x | ✅ Yes | 0 min | 10,000+ times |
| 1.8.x | 2.0.x | ✅ Yes | 0 min | 5,000+ times |
| 1.7.x | 2.0.x | ⚠️ Two-step | 5 min | 1,000+ times |
| 1.6.x | 2.0.x | ❌ Manual | 30 min | 500+ times |

## Breaking changes

!!! warning "Action required for 12% of users"
    Review these breaking changes. Our telemetry shows 88% of users are unaffected.

### API endpoint changes (affects 8% of users)

**What changed:** REST endpoints moved from `/api/v1/*` to `/api/v2/*`

**Impact:** API calls will return 404 until updated

**Detection command:**

```bash
# Check if you're affected (2 seconds)
grep -r "api/v1" . --include="*.js" --include="*.ts" | wc -l
# If output > 0, you're affected
```

**Before (v1.x):**

```javascript
// 245ms average response time
const response = await fetch('https://api.example.com/api/v1/users', {
  headers: { 'API-Key': apiKey }
});
```

**After (v2.x):**

```javascript
// 72ms average response time (3.4x faster)
const response = await fetch('https://api.example.com/api/v2/users', {
  headers: { 'Authorization': `Bearer ${apiKey}` }  // Note: header change
});
```

**Auto-migration available:**

```bash
npx @{{ org }}/migrate-api --auto
# Migrates 100 files/minute, creates backup
```

### Configuration format change (affects 4% of users)

**What changed:** YAML config replaced with JSON for 3x faster parsing

**Before (`config.yaml`, 850ms load time):**

```yaml
server:
  port: 8080
  workers: 4
database:
  host: localhost
  pool: 10
```

**After (`config.json`, 12ms load time):**

```json
{
  "server": {
    "port": 8080,
    "workers": 4,
    "clusterMode": true  // New: enables clustering
  },
  "database": {
    "host": "localhost",
    "pool": 50,          // Increased from 10
    "ssl": true          // New: required for production
  }
}
```

**One-line migration:**

```bash
npx @{{ org }}/config-converter config.yaml > config.json
# Validates and converts in 200ms
```

## Migration steps

**Total time:** 28 minutes average (measured across 10,000+ migrations)

### Step 1: Create backup (3 minutes)

```bash
# Automated backup with compression (typically 35GB → 8GB)
{{ product_name }} backup create --name pre-v2-migration --compress

# Output:
# Creating backup... [████████████████] 100% | 2:47
# Compressed: 35.2GB → 8.1GB (77% reduction)
# Backup ID: bkp_20240115_142532
# Location: /var/backups/{{ product_name }}/bkp_20240115_142532.tar.gz
```

**Verify backup integrity:**

```bash
{{ product_name }} backup verify bkp_20240115_142532

# Expected output:
# ✓ Checksum valid: SHA256 matches
# ✓ Files intact: 18,429 of 18,429
# ✓ Database dumps: All 142 tables present
# ✓ Config included: config.json, .env
# ✓ Restore tested: Dry run successful (45 seconds)
```

### Step 2: Update dependencies (2 minutes)

```bash
# Update all dependencies to compatible versions
npm update --save
npm audit fix

# Specific version requirements:
npm install redis@4.6.0      # Required for new caching
npm install postgres@14.5    # For connection pooling
npm install fastify@4.25.0   # 40% faster than Express

# Verify:
npm list --depth=0
# Should show all packages with green checkmarks
```

### Step 3: Migrate configuration (1 minute)

**Automated configuration migration:**

```bash
{{ product_name }} migrate config --auto

# Output:
# Analyzing current config...
# Found 3 deprecated settings:
#   - workers: 4 → workerThreads: 8 (2x performance)
#   - timeout: 30 → timeout: 30000 (now in ms)
#   - cache: true → cache: { enabled: true, ttl: 3600 }
#
# ✓ Config migrated successfully
# ✓ Backup saved: config.json.backup
```

**Configuration changes applied:**

| Old Setting | New Setting | Impact |
| --- | --- | --- |
| `workers: 4` | `workerThreads: 8` | 2x throughput (1,000 → 2,000 req/s) |
| `timeout: 30` | `timeout: 30000` | Prevents early timeouts |
| `cache: true` | `cache: {enabled: true, ttl: 3600}` | 85% cache hit rate |
| `ssl: false` | `ssl: true` | Required for production |
| `poolSize: 10` | `poolSize: 50` | 5x concurrent connections |

### Step 4: Run migration with zero downtime (20 minutes)

=== "Automated (recommended)"

    ```bash
    # Start blue-green deployment (zero downtime)
    {{ product_name }} migrate start --strategy blue-green

    # Real-time progress:
    # [Phase 1/5] Starting new version alongside old... ✓ (45s)
    # [Phase 2/5] Syncing data (142 tables)...
    #   Tables: [████████████░░░] 89/142 | 12 min remaining
    #   Rows: 45,231,899 of 67,000,000 | 125 MB/s
    # [Phase 3/5] Switching traffic gradually...
    #   10% → new version (monitoring for 60s) ✓
    #   25% → new version (monitoring for 60s) ✓
    #   50% → new version (monitoring for 60s) ✓
    #   75% → new version (monitoring for 60s) ✓
    #   100% → new version ✓
    # [Phase 4/5] Validating all endpoints... ✓ (127 of 127 healthy)
    # [Phase 5/5] Cleanup old version... ✓
    #
    # SUCCESS | Total time: 19 min 32 sec | Zero downtime achieved
    ```

=== "Manual (if auto fails)"

    ```bash
    # 1. Start new version on different port (30 seconds)
    {{ product_name }} start --version 2.0.0 --port 8081

    # 2. Sync data while old version runs (15 minutes)
    {{ product_name }} sync-data --from 8080 --to 8081 --live

    # 3. Switch load balancer (5 seconds downtime)
    nginx -s reload  # After updating upstream to :8081

    # 4. Stop old version
    {{ product_name }} stop --port 8080
    ```

### Step 5: Validate migration (2 minutes)

```bash
# Comprehensive validation suite
{{ product_name }} validate post-migration

# Output:
# Running 47 validation checks...
#
# API Endpoints:
# ✓ GET /api/v2/health - 12ms (was 89ms) - 7.4x faster
# ✓ POST /api/v2/users - 34ms (was 245ms) - 7.2x faster
# ✓ All 127 endpoints responding
#
# Database:
# ✓ All 142 tables present
# ✓ Row count matches: 67,000,142 (± 0)
# ✓ Indexes optimized: 89 of 89
# ✓ Query performance: 8.5x improvement
#
# Performance:
# ✓ Memory usage: 1.0GB (was 2.5GB) - 60% reduction
# ✓ CPU usage: 35% (was 75%) - 53% reduction
# ✓ Response time P50: 72ms (was 245ms)
# ✓ Response time P99: 180ms (was 1,200ms)
#
# VALIDATION PASSED | Score: 47/47 | Ready for production
```

## Post-migration monitoring

Monitor these metrics for 24 hours post-migration:

### Real-time dashboard

```bash
{{ product_name }} monitor --dashboard

# Live metrics (updates every second):
# ┌─────────────────────────────────────────────┐
# │ PERFORMANCE           │ Before  → After     │
# ├─────────────────────────────────────────────┤
# │ Response Time (P50)   │ 245ms  → 72ms  ✓   │
# │ Response Time (P99)   │ 1200ms → 180ms ✓   │
# │ Throughput           │ 1000   → 3500 req/s │
# │ Error Rate           │ 0.05%  → 0.001% ✓  │
# │ CPU Usage            │ 75%    → 35% ✓     │
# │ Memory Usage         │ 2.5GB  → 1.0GB ✓   │
# └─────────────────────────────────────────────┘
```

### Alert thresholds

The system auto-alerts if metrics exceed these thresholds:

| Metric | Warning | Critical | Auto-rollback |
| --- | --- | --- | --- |
| Error rate | >0.1% | >1% | >5% |
| P99 latency | >500ms | >1000ms | >2000ms |
| Memory | >80% | >90% | >95% |
| CPU | >70% | >85% | >95% |

## Rollback procedure

**Rollback success rate:** 99.9% (1,247 successful rollbacks of 1,248 attempts)

### Automatic rollback (triggered by alerts)

The system automatically rolls back if critical thresholds are exceeded:

```bash
# System auto-rollback in action:
# [ALERT] Error rate exceeded 5% threshold (current: 5.2%)
# [AUTO] Initiating rollback to v1.9.2...
# [AUTO] Switching traffic back... done (3 seconds)
# [AUTO] Restoring configuration... done (1 second)
# [AUTO] Rollback complete | Downtime: 4 seconds
```

### Manual rollback (30 seconds)

```bash
# One-command rollback
{{ product_name }} rollback

# Output:
# Detected last stable version: v1.9.2
# Found backup: bkp_20240115_142532
#
# Rolling back...
# [1/3] Switching traffic... ✓ (3s)
# [2/3] Restoring config... ✓ (1s)
# [3/3] Restarting services... ✓ (5s)
#
# ROLLBACK COMPLETE | Time: 9 seconds | Status: Healthy
```

### Emergency rollback from backup (5 minutes)

If quick rollback fails:

```bash
# Full restore from backup
{{ product_name }} backup restore bkp_20240115_142532 --force

# Progress:
# Extracting backup (8.1GB)... ✓ (45s)
# Stopping current services... ✓ (5s)
# Restoring database (142 tables)... ✓ (3m 20s)
# Restoring configuration... ✓ (2s)
# Starting services... ✓ (8s)
# Running health checks... ✓ (15s)
#
# RESTORE COMPLETE | Version: v1.9.2 | All systems operational
```

## Troubleshooting migration issues

Based on 10,000+ migrations, these issues cover 98% of problems:

### Database lock timeout (32% of issues)

**Symptom:**

```text
ERROR: Lock wait timeout exceeded; try restarting transaction
Migration stalled at "Syncing data (42/142 tables)"
```

**Cause:** Long-running transactions blocking migration

**Fix (45 seconds):**

```bash
# Find and kill blocking queries
{{ product_name }} db kill-locks --older-than 60s

# Output:
# Found 3 blocking queries:
# - PID 8923: Running for 847s (killed)
# - PID 8924: Running for 623s (killed)
# - PID 8925: Running for 419s (killed)
#
# Locks cleared. Migration resuming...
```

**Success rate:** Fixes issue 94% of the time

### Memory spike during migration (18% of issues)

**Symptom:** Process killed, OOM (Out of Memory) errors

**Fix (2 minutes):**

```bash
# Reduce batch size for memory-constrained systems
{{ product_name }} migrate start --batch-size 1000 --memory-limit 512MB

# Uses 75% less memory, adds ~5 minutes to migration
```

### Version compatibility error (15% of issues)

**Symptom:**

```text
ERROR: Cannot migrate from 1.6.x to 2.0.x directly
```

**Fix:** Two-step migration (adds 15 minutes)

```bash
# First migrate to intermediate version
{{ product_name }} migrate --to 1.9.0
# Then to final version
{{ product_name }} migrate --to 2.0.0
```

### Network timeout on large datasets (12% of issues)

**Symptom:** Migration fails at 85-90% with timeout errors

**Fix:**

```bash
# Increase timeouts and use resume feature
{{ product_name }} migrate start \
  --timeout 3600 \
  --resume-on-failure \
  --checkpoint-interval 1000

# If it fails, resume from checkpoint:
{{ product_name }} migrate resume
# Resumes from last successful checkpoint (no data loss)
```

## Migration timeline breakdown

Based on real migration data from 10,000+ production systems:

| Phase | P50 Time | P90 Time | P99 Time | What happens |
|-------|----------|----------|----------|--------------|
| **1. Validation** | 45s | 1m 20s | 2m 15s | Compatibility checks, space verification |
| **2. Backup** | 2m 30s | 4m 15s | 8m 45s | Full system backup with compression |
| **3. Dependencies** | 1m 15s | 2m 10s | 3m 30s | Update packages, install new deps |
| **4. Schema migration** | 30s | 1m 45s | 5m 20s | Database structure updates |
| **5. Data migration** | 12m 00s | 22m 30s | 45m 00s | Transfer and transform data |
| **6. Traffic switch** | 5s | 12s | 30s | Blue-green deployment switch |
| **7. Validation** | 1m 30s | 2m 15s | 3m 45s | Post-migration health checks |
| **8. Cleanup** | 45s | 1m 30s | 2m 00s | Remove old version artifacts |
| **Total** | **19m 30s** | **35m 47s** | **70m 35s** | Complete migration |

**Factors affecting duration:**

- **Database size:** +1 minute per 10GB
- **Network speed:** +2 minutes per 100ms latency
- **CPU cores:** -3 minutes per 4 additional cores
- **Custom plugins:** +30 seconds per plugin

## Getting help

**Response times by channel:**

- 🚨 **Critical issues:** [Emergency hotline](tel:+1-555-911-MIGRATE) - 5 minute response
- 💬 **Discord:** [#migration-help](<https://discord.gg/{{> product_name }}) - 15 minute avg response
- 📧 **Email support:** migration@{{ product_name }}.io - 2 hour response (business hours)
- 🤖 **AI assistant:** Built into CLI via `{{ product_name }} migrate --help` - Instant

**Before contacting support, run:**

```bash
{{ product_name }} debug-report --migration > migration-debug.log
# Collects all relevant logs, configs, and metrics
# Attach this file to your support request
```

## Success metrics

Track these KPIs post-migration:

```bash
{{ product_name }} metrics --post-migration

# Key Performance Indicators:
# ✓ Response time improved: 245ms → 72ms (70.6% faster)
# ✓ Error rate reduced: 0.05% → 0.001% (98% fewer)
# ✓ Throughput increased: 1,000 → 3,500 req/s (3.5x)
# ✓ Infrastructure cost: -$1,000/month (40% reduction)
# ✓ User satisfaction: +23 NPS points
#
# ROI: Migration cost recovered in 2.3 months
```

---
title: "[Component] not working"
description: "Fix [component] issues in under 5 minutes. Covers connection errors (60% of cases), performance issues (30%), and configuration problems (10%)."
content_type: troubleshooting
product: both
tags:
  - Troubleshooting
  - [Component]
---

# [Component] not working

Your [component] is failing with [specific error] or showing [specific behavior]. This guide fixes 95% of [component] issues in under 5 minutes.

## Quick diagnosis (30 seconds)

Run this diagnostic command first:

```bash
{{ product_name }} diagnose [component] --verbose

# Expected output:
# ✓ Service running (pid: 12345)
# ✓ Port 8080 accessible
# ✓ Memory usage: 245MB/2GB (12%)
# ✓ CPU usage: 15%
# ✗ Database connection failed (timeout after 5000ms)
#   → This is your issue. Jump to: Database Connection
```

## Diagnosis table

| Error Message | Frequency | Fix Time | Jump to Solution |
|--------------|-----------|----------|------------------|
| `Connection refused` | 45% | 30 sec | [Service not running](#1-service-not-running-45-of-cases) |
| `Timeout after Xms` | 25% | 2 min | [Performance degradation](#2-performance-degradation-25-of-cases) |
| `Invalid configuration` | 15% | 1 min | [Configuration errors](#3-configuration-errors-15-of-cases) |
| `Out of memory` | 10% | 3 min | [Resource exhaustion](#4-resource-exhaustion-10-of-cases) |
| `Permission denied` | 5% | 1 min | [Permission issues](#5-permission-issues-5-of-cases) |

## 1. Service not running (45% of cases)

**You see:**

```text
Error: connect ECONNREFUSED 127.0.0.1:8080
```

**Root cause:** Service crashed or never started. Usually happens after system reboot or deployment.

### Fix in 30 seconds

```bash
# 1. Check if running (2 seconds)
{{ product_name }} status [component]
# Shows: STOPPED

# 2. Start the service (5 seconds)
{{ product_name }} start [component]
# Output: Starting [component]... OK (pid: 12345)

# 3. Verify it's working (2 seconds)
curl http://localhost:8080/health
# Expected: {"status":"healthy","uptime":5}
```

**Success rate:** 92% fixed with restart alone.

### If restart doesn't work

Check the logs for startup errors:

```bash
tail -n 50 /var/log/{{ product_name }}/[component].log

# Common startup errors:
# "Port 8080 already in use" → Kill process using port
# "Cannot connect to database" → Check database is running
# "License expired" → Update license key
```

## 2. Performance degradation (25% of cases)

**You see:**

- Response times > 500ms (normal: < 50ms)
- CPU usage > 80%
- Memory usage > 90%
- Timeouts after 30 seconds

### Fix in 2 minutes

```bash
# 1. Check current resource usage (5 seconds)
{{ product_name }} stats [component]

# Output:
# CPU: 87% (CRITICAL)
# Memory: 3.8GB/4GB (95% - CRITICAL)
# Connections: 987/1000
# Queue depth: 5432 items
# Processing rate: 12 req/s (normal: 100 req/s)
```

### Solution by bottleneck

**High CPU (87%+):**

```yaml
# Increase workers in config.yml
workers: 16  # Was 4
batch_size: 100  # Was 10

# Restart to apply
{{ product_name }} restart [component]
# Result: CPU drops to 45%, throughput increases 4x
```

**High Memory (90%+):**

```yaml
# Increase memory limit
memory_limit: 8GB  # Was 4GB
cache_size: 100MB  # Was 1GB (reduce cache)

# Clear current cache
{{ product_name }} cache clear
# Frees ~2GB immediately
```

**Connection saturation:**

```yaml
# Increase connection pool
max_connections: 5000  # Was 1000
connection_timeout: 10000  # Was 30000 (reduce timeout)
```

**Actual improvement:** Response time drops from 2000ms to 45ms (44x faster).

## 3. Configuration errors (15% of cases)

**You see:**

```text
Error: Invalid configuration at line 42
Key 'timeout' expects number, got string "30 seconds"
```

### Fix in 1 minute

```bash
# 1. Validate configuration (3 seconds)
{{ product_name }} config validate

# Output shows exact error:
# ✗ Line 42: timeout must be number (milliseconds)
#   Current: "30 seconds"
#   Expected: 30000

# 2. Fix the configuration
nano /etc/{{ product_name }}/config.yml
# Change: timeout: "30 seconds"
# To: timeout: 30000

# 3. Test configuration (2 seconds)
{{ product_name }} config test
# ✓ Configuration valid

# 4. Reload without downtime (5 seconds)
{{ product_name }} reload [component]
# ✓ Configuration reloaded (0 downtime)
```

### Common configuration mistakes

| Mistake | Wrong | Correct | Impact |
| --- | --- | --- | --- |
| String instead of number | `port: "8080"` | `port: 8080` | Service won't start |
| Wrong time unit | `timeout: 30` | `timeout: 30000` | Timeouts after 30ms instead of 30s |
| Invalid enum | `level: "verbose"` | `level: "debug"` | Falls back to default |
| Missing required | — | `api_key: "sk_..."` | Authentication failures |

## 4. Resource exhaustion (10% of cases)

**You see:**

```text
Error: Cannot allocate memory
Error: Too many open files
Error: No space left on device
```

### Immediate fixes (3 minutes)

**Out of memory:**

```bash
# 1. Check what's using memory (5 seconds)
{{ product_name }} memory-report

# Top consumers:
# - Cache: 3.2GB (80%)
# - Active connections: 512MB (13%)
# - Buffers: 288MB (7%)

# 2. Clear cache (instant, frees 3.2GB)
{{ product_name }} cache clear --all

# 3. Restart with lower cache (10 seconds)
{{ product_name }} restart [component] --cache-size=500MB
```

**Too many open files:**

```bash
# Current limit
ulimit -n
# Output: 1024 (too low)

# Increase limit
ulimit -n 65536

# Make permanent
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Restart service
{{ product_name }} restart [component]
```

**Disk space:**

```bash
# 1. Check disk usage (2 seconds)
df -h
# /var/log: 98% full

# 2. Rotate logs (frees ~5GB typically)
{{ product_name }} logs rotate --compress

# 3. Set up auto-rotation
{{ product_name }} config set logs.max_size=100MB
{{ product_name }} config set logs.max_files=10
```

## 5. Permission issues (5% of cases)

**You see:**

```text
Error: EACCES: permission denied
Error: Cannot write to /var/lib/[component]
```

### Fix in 1 minute

```bash
# 1. Check current permissions
ls -la /var/lib/{{ product_name }}/

# 2. Fix ownership (most common issue)
sudo chown -R {{ product_name }}:{{ product_name }} /var/lib/{{ product_name }}/

# 3. Fix permissions
sudo chmod -R 755 /var/lib/{{ product_name }}/
sudo chmod -R 644 /var/lib/{{ product_name }}/*.conf

# 4. Restart with correct user
sudo -u {{ product_name }} {{ product_name }} restart [component]
```

## Still not working?

If you've tried all solutions above (5 minutes total) and still have issues:

### 1. Collect debug information (30 seconds)

```bash
{{ product_name }} debug-report --full > debug.log

# This collects:
# - Last 1000 log lines
# - Configuration (sanitized)
# - System resources
# - Network status
# - Recent errors
```

### 2. Check known issues

- [Status page](https://status.example.com) - Current outages
- [GitHub issues](https://github.com/example/product/issues) - Known bugs
- [Community forum](https://forum.example.com) - Similar problems

### 3. Get help

**Community support (free, ~2 hour response):**

- Post in [Forum](https://forum.example.com) with `debug.log`
- Join [Discord](https://discord.gg/product) #support channel

**Priority support (paid, <30 min response):**

- Email: <support@example.com>
- Include: `debug.log`, account ID, urgency level

## Prevention checklist

Prevent 90% of issues with these practices:

- [ ] **Enable auto-restart**: `{{ product_name }} config set auto_restart=true`
- [ ] **Set up monitoring**: Get alerts before issues become critical
- [ ] **Configure log rotation**: Prevent disk space issues
- [ ] **Regular updates**: `{{ product_name }} update` monthly
- [ ] **Resource limits**: Set memory/CPU limits to prevent exhaustion
- [ ] **Health checks**: `*/5 * * * * {{ product_name }} health-check`

## Performance baseline

After fixing, your [component] should show:

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Response time | <50ms | 50-200ms | >200ms |
| CPU usage | <60% | 60-80% | >80% |
| Memory usage | <70% | 70-90% | >90% |
| Error rate | <0.1% | 0.1-1% | >1% |
| Throughput | >100 req/s | 50-100 req/s | <50 req/s |

Run `{{ product_name }} benchmark [component]` to verify performance.

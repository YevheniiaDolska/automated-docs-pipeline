---
title: "[Product] [feature] user guide"
description: "[Feature] enables [primary capability] for [user role]. This guide covers setup, daily usage, and advanced configuration with production examples."
content_type: how-to
product: both
tags:
  - How-To
  - [Topic]
---

# [Product] [feature] user guide

[Feature] enables [user role] to [primary action] without [previous limitation]. This guide covers everything from initial setup to advanced daily workflows, with real examples from production environments processing [concrete metric].

## Prerequisites

Before using [feature], verify:

- **[Product] version**: {{ current_version }} or later
- **Access level**: [specific role or permission]
- **Dependencies**: [list concrete requirements]

```bash
# Verify your version
[product-cli] --version
# Expected: v{{ current_version }} or higher
```

## Initial setup

### Step 1: Enable [feature]

Navigate to **Settings > [Section] > [Feature]** and enable the toggle.

=== "Cloud"

    [Feature] is enabled by default on {{ product_name }} Cloud.
    Visit [{{ cloud_url }}]({{ cloud_url }}) to access your dashboard.

=== "Self-hosted"

    Set the environment variable to enable [feature]:

    ```bash
    export {{ env_vars.port }}=5678
    # Restart the service
    systemctl restart [product]
    ```

### Step 2: Configure basic settings

```yaml
# config.yml
feature:
  enabled: true
  mode: "standard"        # Options: standard, advanced, custom
  timeout_seconds: 30     # Default: {{ max_execution_timeout_seconds }}
  max_retries: 3
```

## Daily usage

### [Primary workflow name]

The most common workflow involves [number] steps:

1. **[Action 1]**: Navigate to [location] and [specific click/command]
1. **[Action 2]**: Enter [specific values] in the [field name] field
1. **[Action 3]**: Click **[Button name]** to [expected result]

```javascript
// Example: programmatic usage of [feature]
const result = await client.feature.execute({
  input: "realistic-example-data",
  options: {
    timeout: 30000,       // 30 seconds
    retryCount: 3,
    mode: "standard"
  }
});

console.log('Result:', result.status);
// Output: "completed"
console.log('Processed:', result.itemCount, 'items');
// Output: "Processed: 150 items"
```

### [Secondary workflow name]

For [specific scenario], use [alternative approach]:

1. Open [location]
1. Select **[option]** from the dropdown
1. Configure [setting] to [value]

!!! tip "Save time with keyboard shortcuts"
    Press `Ctrl+Shift+E` to execute [feature] directly from any page.

## Advanced configuration

### Custom [aspect] rules

Define custom rules in your configuration:

```yaml
rules:
  - name: "high-priority-processing"
    condition: "priority == 'high'"
    action: "process_immediately"
    timeout: 10

  - name: "batch-processing"
    condition: "type == 'batch'"
    action: "queue_for_batch"
    max_batch_size: 100
```

### Performance tuning

| Setting | Default | Recommended for high load | Max |
| --- | --- | --- | --- |
| `concurrency` | 5 | 20 | 50 |
| `batch_size` | 10 | 100 | 1000 |
| `timeout_seconds` | 30 | 60 | {{ max_execution_timeout_seconds }} |
| `memory_limit_mb` | 256 | 1024 | 4096 |

## Troubleshooting common issues

### [Feature] is not responding

**Symptom**: [Specific error message or behavior]

**Cause**: [Root cause explanation]

**Solution**:

```bash
# Check service status
systemctl status [product]

# Review logs for errors
tail -100 /var/log/[product]/[feature].log | grep ERROR
```

### Rate limit exceeded

**Symptom**: HTTP 429 responses

**Cause**: More than {{ rate_limit_requests_per_minute }} requests per minute

**Solution**: Implement exponential backoff:

```javascript
async function withRetry(fn, maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (error.status === 429 && attempt < maxRetries - 1) {
        const delay = Math.pow(2, attempt) * 1000;
        console.log(`Rate limited. Retrying in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        throw error;
      }
    }
  }
}
```

## Next steps

- [Advanced feature guide](../reference/[feature]-reference.md) for full API reference
- [Integration guide](../how-to/integrate-[feature].md) to connect with external services
- [Best practices](../concepts/[feature]-best-practices.md) for production deployments

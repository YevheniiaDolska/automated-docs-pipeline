---
title: "Get started with [Product]"
description: "Make your first [API call] in 5 minutes. Zero to production-ready [feature] with step-by-step instructions and working code."
content_type: tutorial
product: both
tags:
  - Tutorial
  - Quickstart
---

# Get started with [Product]

Get [Product] running and make your first [API call] in under 5 minutes. By minute 10, you'll have a production-ready [feature] processing [100 requests/second].

## You'll build this

```javascript
// A working [feature] that:
const result = await client.[operation]({
  data: "your-data",
  options: { parallel: true }
});
// Processes 100 items in 1.2 seconds
// Handles errors automatically
// Scales to 10,000+ items
```

**Time to first success:** 2 minutes
**Time to production-ready:** 10 minutes
**What you'll learn:** Core concepts that apply to all [Product] features

## Before you start (30 seconds)

You need:

- A computer with internet (that's it for Cloud)
- For self-hosted: [Docker](https://docker.com) or [Node.js 18+](https://nodejs.org)
- 10 minutes of focused time

## Step 1: Get [Product] running (2 minutes)

=== "{{ product_name }} Cloud (Fastest)"

    ```bash
    # 1. Sign up (30 seconds)
    open https://{{ cloud_url }}/signup

    # 2. Get your API key from dashboard
    # 3. You're ready! Skip to Step 2
    ```

    **Why Cloud?** Zero setup, automatic scaling, 99.99% uptime SLA.

=== "Docker (Local development)"

    ```bash
    # Pull and run (90 seconds on average connection)
    docker run -d \
      --name [product] \
      -p 8080:8080 \
      -e LICENSE=trial \
      [docker-image]:latest

    # Verify it's running (< 1 second)
    curl http://localhost:8080/health
    # Expected: {"status":"healthy","version":"2.1.0"}
    ```

=== "npm (For Node.js developers)"

    ```bash
    # Install globally (45 seconds)
    npm install -g @[org]/[product]

    # Start server (5 seconds)
    [product] start --port 8080

    # Verify
    curl http://localhost:8080/health
    # Expected: {"status":"healthy","version":"2.1.0"}
    ```

!!! success "Checkpoint"
    You should see `{"status":"healthy"}`. If not, [troubleshoot here](#common-issues).

## Step 2: Get your credentials (1 minute)

=== "{{ product_name }} Cloud"

    1. Open [Dashboard](https://{{ cloud_url }}/dashboard)
    2. Click **API Keys** → **Create Key**
    3. Copy the key (starts with `sk_live_`)

    ```bash
    # Save securely (never commit this!)
    export API_KEY="sk_live_your_actual_key_here"
    ```

=== "Self-hosted"

    ```bash
    # Generate local API key
    curl -X POST http://localhost:8080/auth/keys \
      -H "Content-Type: application/json" \
      -d '{"name":"quickstart","scopes":["read","write"]}'

    # Response:
    # {"key":"sk_local_abc123...","created":1705320000}

    export API_KEY="sk_local_your_key_here"
    ```

⚠️ **Security:** Treat API keys like passwords. Never share or commit them.

## Step 3: Make your first request (2 minutes)

Let's create a [resource] that processes data:

=== "cURL (Universal)"

    ```bash
    curl https://{{ api_url }}/v1/[resources] \
      -H "Authorization: Bearer $API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "My First [Resource]",
        "type": "production",
        "config": {
          "workers": 4,
          "timeout": 30000
        }
      }'
    ```

    **Response (127ms):**
    ```json
    {
      "id": "res_abc123xyz",
      "name": "My First [Resource]",
      "status": "active",
      "created": 1705320000,
      "performance": {
        "capacity": "100 req/sec",
        "current_load": "0%"
      }
    }
    ```

=== "JavaScript"

    ```javascript
    // Install SDK: npm install @[org]/[product]-sdk

    const { Client } = require('@[org]/[product]-sdk');

    const client = new Client({
      apiKey: process.env.API_KEY,
      timeout: 30000
    });

    const resource = await client.resources.create({
      name: "My First [Resource]",
      type: "production",
      config: {
        workers: 4,
        timeout: 30000
      }
    });

    console.log(`Created ${resource.id} in ${resource.duration}ms`);
    // Output: Created res_abc123xyz in 127ms
    ```

=== "Python"

    ```python
    # Install: pip install [product]-sdk

    from [product]_sdk import Client
    import os

    client = Client(
        api_key=os.environ['API_KEY'],
        timeout=30000
    )

    resource = client.resources.create(
        name="My First [Resource]",
        type="production",
        config={
            "workers": 4,
            "timeout": 30000
        }
    )

    print(f"Created {resource.id} in {resource.duration}ms")
    # Output: Created res_abc123xyz in 127ms
    ```

## Step 4: Process real data (3 minutes)

Now let's use your [resource] to process actual data:

```javascript
// Process 100 items in parallel
const data = Array.from({length: 100}, (_, i) => ({
  id: i,
  value: `item-${i}`
}));

const result = await client.process({
  resourceId: "res_abc123xyz",
  data: data,
  options: {
    parallel: true,
    batchSize: 10
  }
});

console.log(`
  Processed: ${result.processed} items
  Duration: ${result.duration}ms
  Throughput: ${result.throughput} items/sec
  Errors: ${result.errors}
`);
```

**Actual output:**

```text
Processed: 100 items
Duration: 1247ms
Throughput: 80.19 items/sec
Errors: 0
```

## Step 5: View results (1 minute)

=== "Dashboard"

    Open [Dashboard](https://{{ cloud_url }}/dashboard) to see:
    - Real-time metrics
    - Processing history
    - Error logs (if any)

=== "API"

    ```bash
    # Get detailed metrics
    curl https://{{ api_url }}/v1/[resources]/res_abc123xyz/metrics \
      -H "Authorization: Bearer $API_KEY"
    ```

    ```json
    {
      "resource_id": "res_abc123xyz",
      "period": "last_hour",
      "metrics": {
        "requests": 100,
        "success_rate": 100.0,
        "avg_latency_ms": 12.47,
        "p99_latency_ms": 23.5,
        "throughput": "80.19 items/sec"
      }
    }
    ```

## ✅ Success! You're done

In just 10 minutes, you:

1. **Deployed [Product]** - Cloud or self-hosted
1. **Authenticated securely** - API key obtained
1. **Created a [resource]** - Ready for production
1. **Processed 100 items** - In 1.2 seconds
1. **Monitored performance** - Real-time metrics

Your setup can now handle:

- 📊 **100+ requests/second**
- ⚡ **12ms average latency**
- 🔄 **Automatic retry on failures**
- 📈 **Scales to 10,000+ items**

## What's next?

Now that you have [Product] running, here's your learning path:

| Time | Goal | Resource | You'll Learn |
| --- | --- | --- | --- |
| 15 min | Build a complete workflow | [Tutorial: Build [feature]](../tutorials/build-feature.md) | Connect multiple resources |
| 10 min | Add error handling | [How-to: Handle errors](../how-to/error-handling.md) | Retry strategies, fallbacks |
| 20 min | Deploy to production | [Production guide](../how-to/deploy-production.md) | Scaling, monitoring, security |
| 5 min | Optimize performance | [Performance tuning](../how-to/performance.md) | 10x throughput improvement |

## Common issues and fixes

### "Connection refused" error

```bash
# Check if service is running
docker ps | grep [product]
# or
systemctl status [product]

# Fix: Restart the service
docker restart [product]
# or
[product] restart
```

**Success rate:** This fixes 90% of connection issues.

### "Unauthorized" error

```bash
# Verify your API key
echo $API_KEY
# Should start with sk_live_ or sk_local_

# Test the key
curl https://{{ api_url }}/v1/auth/verify \
  -H "Authorization: Bearer $API_KEY"

# Expected: {"valid":true,"scopes":["read","write"]}
```

### Rate limiting (429 error)

You hit the rate limit (60 req/min for free tier). Solutions:

1. **Wait 60 seconds** - Limit resets
1. **Upgrade plan** - Get 10,000 req/min
1. **Use batch operations** - Process multiple items per request

### Slow performance

If processing takes >5 seconds for 100 items:

```javascript
// Optimize with these settings
config: {
  parallel: true,      // Enable parallel processing
  batchSize: 25,       // Optimal batch size
  workers: 8,          // More workers
  cache: true          // Enable caching
}
// Result: 100 items in ~500ms (10x faster)
```

## Get help

- 💬 **Community:** [Discord](https://discord.gg/[product]) - 2,000+ members, <5 min response time
- 📚 **Docs:** [Full documentation](https://docs.example.com) - 500+ pages
- 🎥 **Video:** [YouTube quickstart](https://youtube.com/watch?v=...) - 12 minutes
- 📧 **Support:** <support@example.com> - <2 hour response (business hours)

## Feedback

**How was this quickstart?** [Rate it](https://feedback.example.com) (takes 10 seconds)

---

**Next:** [Build your first production workflow →](../tutorials/first-workflow.md) (15 minutes)

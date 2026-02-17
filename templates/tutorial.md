---
title: "[Action] [thing] in [time estimate]"
description: "Learn how to [action] [thing] with real examples. Build a working [outcome] that handles [specific capability]."
content_type: tutorial
product: both
tags:
  - Tutorial
  - [Topic]
---

# [Action] [thing] in [time estimate]

[Thing] enables [primary benefit with specific metric]. This tutorial shows you how to build a production-ready [thing] that processes [concrete number] [items] per [time unit] in approximately [time estimate] minutes.

## What you'll build

By the end of this tutorial, you'll have:

- A working [thing] that [specific capability with number]
- Automatic [feature] handling [specific scenario]
- Performance monitoring showing [specific metric]

**Time to first success:** 5 minutes for basic setup, [full time] for complete implementation.

## Before you start

You need:

- {{ product_name }} version {{ current_version }} or later ([check your version](../reference/version.md))
- [Specific tool] installed (run `tool --version` to verify)
- API key from [service] ([get one here](https://example.com/api-keys))
- About [time estimate] minutes

!!! tip "Save time"
    Download the [complete example](https://github.com/example/tutorial-code) to follow along with working code.

## Step 1: Set up your environment (2 minutes)

First, create the project structure. This foundation handles [specific capability]:

```bash
# Create project directory
mkdir my-[thing]
cd my-[thing]

# Initialize configuration
cat > config.yml << EOF
name: production-[thing]
port: 8080
workers: 4
timeout: 30
EOF
```

Expected output:

```text
✓ Created project directory
✓ Generated config.yml
```

If you see "permission denied", ensure you have write access to the current directory.

## Step 2: Configure [core component] (3 minutes)

Configure the [component] to handle [specific volume] requests per second:

=== "{{ product_name }} Cloud"

    ```javascript
    const config = {
      endpoint: "https://{{ cloud_url }}/api",
      apiKey: process.env.API_KEY,
      rateLimit: 1000,  // requests per minute
      timeout: 30000,    // milliseconds
      retries: 3
    };

    // Initialize with production settings
    const client = new CloudClient(config);
    ```

=== "Self-hosted"

    ```javascript
    const config = {
      endpoint: "http://localhost:8080/api",
      apiKey: process.env.API_KEY,
      rateLimit: 5000,  // higher limit for local
      timeout: 30000,
      retries: 3
    };

    // Initialize with local settings
    const client = new SelfHostedClient(config);
    ```

Key settings explained:

- `rateLimit`: Maximum requests per minute (Cloud: 1000, Self-hosted: 5000)
- `timeout`: Connection timeout in milliseconds (30 seconds recommended)
- `retries`: Automatic retry attempts for failed requests

## Step 3: Implement [main functionality] (5 minutes)

Now implement the core logic that processes [specific data type]:

```javascript
// Main processing function
async function process[Thing](data) {
  // Validate input
  if (!data || data.length === 0) {
    throw new Error('Input data is required');
  }

  // Process with metrics
  const startTime = Date.now();

  try {
    // Actual processing
    const result = await client.process({
      data: data,
      options: {
        parallel: true,      // Process in parallel
        batchSize: 100,      // Optimal batch size
        compression: 'gzip'  // Reduce network overhead
      }
    });

    // Log performance metrics
    const duration = Date.now() - startTime;
    console.log(`Processed ${data.length} items in ${duration}ms`);
    console.log(`Throughput: ${(data.length / duration * 1000).toFixed(2)} items/sec`);

    return result;

  } catch (error) {
    // Specific error handling
    if (error.code === 'RATE_LIMIT') {
      console.error('Rate limited. Waiting 60 seconds...');
      await new Promise(r => setTimeout(r, 60000));
      return process[Thing](data); // Retry
    }
    throw error;
  }
}
```

!!! warning "Common mistake"
    Don't forget to set `parallel: true` for better performance. Sequential processing is 10x slower.

## Step 4: Add error handling (3 minutes)

Production systems need robust error handling:

```javascript
// Wrap with proper error handling
async function safe[Thing]Processor(data) {
  const errors = [];
  const results = [];

  for (const batch of chunkArray(data, 100)) {
    try {
      const result = await process[Thing](batch);
      results.push(result);
    } catch (error) {
      errors.push({
        batch: batch.slice(0, 3), // Log first 3 items
        error: error.message,
        timestamp: new Date().toISOString()
      });

      // Continue processing other batches
      continue;
    }
  }

  // Report results
  console.log(`Success: ${results.length} batches`);
  console.log(`Failed: ${errors.length} batches`);

  if (errors.length > 0) {
    console.error('Failed batches:', JSON.stringify(errors, null, 2));
  }

  return { results, errors };
}

// Helper function
function chunkArray(array, size) {
  const chunks = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
}
```

## Step 5: Test your implementation (2 minutes)

Verify everything works with real data:

```bash
# Test with sample data
cat > test-data.json << EOF
[
  {"id": 1, "value": "test-1"},
  {"id": 2, "value": "test-2"},
  {"id": 3, "value": "test-3"}
]
EOF

# Run the test
node test-processor.js
```

Expected successful output:

```text
Starting processing...
✓ Validated 3 items
✓ Processed 3 items in 245ms
✓ Throughput: 12.24 items/sec
✓ All tests passed

Results saved to: output/results-2024-01-15.json
```

If you see errors:

- `API_KEY not found`: Set your API key with `export API_KEY=your-key-here`
- `Connection refused`: Check the service is running on port 8080
- `Rate limit exceeded`: Wait 60 seconds or reduce batch size

## Complete working example

Here's the full implementation ready for production:

```javascript
// complete-[thing].js
require('dotenv').config();

const { CloudClient } = require('@company/sdk');

// Production configuration
const config = {
  endpoint: process.env.API_ENDPOINT || 'https://api.example.com',
  apiKey: process.env.API_KEY,
  rateLimit: parseInt(process.env.RATE_LIMIT) || 1000,
  timeout: parseInt(process.env.TIMEOUT) || 30000,
  retries: parseInt(process.env.RETRIES) || 3
};

const client = new CloudClient(config);

async function main() {
  try {
    // Load your data
    const data = require('./data.json');

    console.log(`Processing ${data.length} items...`);
    const startTime = Date.now();

    // Process with error handling
    const { results, errors } = await safe[Thing]Processor(data);

    // Report metrics
    const duration = Date.now() - startTime;
    console.log(`\n=== Performance Report ===`);
    console.log(`Total time: ${(duration / 1000).toFixed(2)} seconds`);
    console.log(`Items processed: ${results.length * 100}`);
    console.log(`Errors: ${errors.length}`);
    console.log(`Average throughput: ${(data.length / duration * 1000).toFixed(2)} items/sec`);

    // Save results
    require('fs').writeFileSync(
      `output/results-${new Date().toISOString().split('T')[0]}.json`,
      JSON.stringify(results, null, 2)
    );

    process.exit(errors.length > 0 ? 1 : 0);

  } catch (error) {
    console.error('Fatal error:', error);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { process[Thing], safe[Thing]Processor };
```

## Performance benchmarks

Based on real production data:

| Data Size | Processing Time | Throughput | Memory Usage |
|-----------|----------------|------------|--------------|
| 100 items | 1.2 seconds | 83 items/sec | 125 MB |
| 1,000 items | 8.5 seconds | 117 items/sec | 180 MB |
| 10,000 items | 72 seconds | 138 items/sec | 420 MB |
| 100,000 items | 12 minutes | 138 items/sec | 1.2 GB |

## Troubleshooting

### Error: Rate limit exceeded

You're hitting the API limit. Solutions:

1. **Reduce batch size**:

   ```javascript
   options: { batchSize: 50 }  // Instead of 100
   ```

1. **Add delays between batches**:

   ```javascript
   await new Promise(r => setTimeout(r, 1000)); // 1 second delay
   ```

1. **Upgrade your plan** for higher limits

### Error: Timeout after 30000ms

Large requests are timing out. Fix:

```javascript
config.timeout = 60000;  // Increase to 60 seconds
// OR
options: { compression: 'gzip' }  // Reduce payload size
```

### Memory issues with large datasets

Process in smaller chunks:

```javascript
// Instead of processing all at once
const CHUNK_SIZE = 1000;
for (let i = 0; i < data.length; i += CHUNK_SIZE) {
  const chunk = data.slice(i, i + CHUNK_SIZE);
  await process[Thing](chunk);

  // Free memory between chunks
  if (global.gc) global.gc();
}
```

## What you learned

You now have a production-ready [thing] that:

- ✅ Processes [X] items per second with automatic retry logic
- ✅ Handles errors gracefully without losing data
- ✅ Provides detailed performance metrics
- ✅ Scales to handle 100,000+ items

**Your [thing] is ready for production!** It can handle real-world load with proper error handling and monitoring.

## Next steps

Take your [thing] further:

- [Add caching](../how-to/add-caching.md) - Reduce API calls by 80%
- [Deploy to production](../how-to/deploy-production.md) - Scale to millions of requests
- [Monitor performance](../how-to/monitor-metrics.md) - Track real-time metrics
- [Optimize for cost](../how-to/optimize-costs.md) - Reduce API usage by 50%

## Additional resources

- [Complete source code](https://github.com/example/tutorial-complete)
- [Video walkthrough](https://youtube.com/watch?v=example) (15 minutes)
- [Community forum](https://forum.example.com/tutorial-help)
- [Office hours](https://calendly.com/support) - Get live help

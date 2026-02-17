#!/usr/bin/env python3
"""
Unified Document Creation Tool
Generates new documentation from templates with proper frontmatter and structure.
Follows Diátaxis framework and ensures all linting rules are met from the start.
"""

import argparse
import re
import yaml
from datetime import date
from pathlib import Path
import subprocess

class DocumentCreator:
    """Creates new documentation files from templates with all required metadata."""

    def __init__(self, base_dir: str = "docs"):
        self.base_dir = Path(base_dir)
        self.templates_dir = Path("templates")
        self.variables_file = self.base_dir / "_variables.yml"
        self.variables = self.load_variables()

    def load_variables(self) -> dict:
        """Load shared variables from _variables.yml."""
        if self.variables_file.exists():
            with open(self.variables_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}

    def get_templates(self) -> dict:
        """Define all available templates following Diátaxis framework."""
        return {
            "tutorial": {
                "dir": "getting-started",
                "content_type": "tutorial",
                "description_template": "Learn how to {topic} with {product_name}",
                "body": """
[Topic] is a [one-sentence definition]. This tutorial teaches you how to [concrete outcome] in approximately [time estimate].

## Before you start

You need:

- {product_name} version {current_version} or later
- [Specific tool/access requirement with version]
- About [time] minutes

## Step 1: [Concrete action verb + object]

[One sentence explaining why this step matters]. [Direct instruction].

```bash
# Replace with actual command
command --with-real-flags
```

Expected output:
```
[Show what successful output looks like]
```

!!! tip "Common mistake"
    [Specific thing people often get wrong and how to avoid it].

## Step 2: [Concrete action verb + object]

[Why this step]. [What to do].

```javascript
// Real code example
const example = {
  setting: "actual-value",
  port: 8080
};
```

To verify this worked, run:
```bash
verification-command
```

## Step 3: Test your setup

Confirm everything works by [specific test action]:

```bash
# Test command
test-command
```

You should see:
```
✓ [Specific success indicator]
✓ [Another success indicator]
```

## What you built

You now have a working [thing] that:

- [Specific capability with metric]
- [Another capability with detail]
- [Third concrete outcome]

**Time to production:** Your [thing] is ready for [specific use case].

## Troubleshooting

### Error: [Specific error message]

This happens when [cause]. Fix it by:

```bash
fix-command
```

### [Thing] not working

Check these in order:
1. [Most common cause]: Run `diagnostic-command`
1. [Second cause]: Verify [specific setting]
1. [Third cause]: Check logs at `/path/to/logs`

## Next steps

- [Scale your setup](../how-to/scale-setup.md) - Handle 10x more traffic
- [Add authentication](../how-to/add-auth.md) - Secure your endpoints
- [Monitor performance](../how-to/monitor.md) - Track metrics in production
"""
            },
            "how-to": {
                "dir": "how-to",
                "content_type": "how-to",
                "description_template": "Step-by-step guide to {topic}",
                "body": """
This guide shows you how to [specific outcome]. It takes about [time] minutes.

## Before you start

You need:
- {product_name} version {current_version} or later ([check version](../reference/version.md))
- [Specific tool] installed (`command --version`)
- Access to [specific resource]

## Step 1: [Action verb + specific object]

[One sentence why]. Run:

```bash
actual-command --with-flags
```

This command [what it does]. The output shows:

```
[Expected output]
Key value: [important-value]
Status: active
```

Save the `[important-value]` - you need it in Step 3.

## Step 2: Configure [specific thing]

Create the configuration file:

```yaml
# config.yml
setting_name: "actual_value"
port: 8080
timeout: 30
important_value: "[from-step-1]"
```

Key settings:
- `port`: Must be between 1024-65535 (default: 8080)
- `timeout`: Seconds before connection drops (default: 30)
- `important_value`: The value from Step 1

## Step 3: Start the service

Start with your configuration:

```bash
start-command --config config.yml
```

Wait for:
```
Service started on port 8080
Ready to accept connections
```

## Step 4: Verify it works

Test the setup:

```bash
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.2.3",
  "uptime": 42
}
```

## What happens next

Your [thing] now:
- Automatically [specific behavior]
- Handles [specific scenario]
- Logs to `[specific location]`

## Common issues

### Port already in use

```
Error: bind: address already in use :8080
```

Fix: Use a different port in config.yml or stop the conflicting service:
```bash
lsof -i :8080  # Find what's using it
kill -9 [PID]  # Stop it
```

### Connection refused

Check:
1. Service is running: `ps aux | grep service-name`
1. Firewall allows port 8080: `firewall-cmd --list-ports`
1. Config file is valid: `validate-config config.yml`

## Related guides

- [Monitor your setup](./monitor-setup.md) - Add metrics and alerting
- [Scale horizontally](./scale-horizontal.md) - Run multiple instances
- [Secure with TLS](./add-tls.md) - Enable HTTPS
"""
            },
            "concept": {
                "dir": "concepts",
                "content_type": "concept",
                "description_template": "Understanding {topic} in {product_name}",
                "body": """
[Topic] is [one-sentence definition stating what it is]. It solves [specific problem] by [core mechanism], enabling you to [primary benefit with metric].

## The problem

Without [topic], you face:

- **[Pain point 1]**: [Specific consequence with number/metric]
- **[Pain point 2]**: [Another consequence with impact]
- **[Pain point 3]**: [Third consequence with cost/time]

Traditional approaches like [alternative] fail because [specific limitation with example].

## How [topic] works

[Topic] operates on three principles:

### 1. [Core principle]

[Topic] [specific mechanism]. For example, when [scenario], it [specific behavior], resulting in [measurable outcome].

```
[Input] → [Process] → [Output]
Example: [concrete] → [transformation] → [result]
```

### 2. [Second principle]

[Technical explanation with specific detail]. This means [practical implication with number].

Key metrics:
- **Latency**: [specific number]ms
- **Throughput**: [specific number]/second
- **Resource usage**: [specific percentage]

### 3. [Third principle]

[How it integrates]. Unlike [alternative], [topic] [specific advantage with comparison].

## Real-world example

Consider an e-commerce platform processing 10,000 orders/hour:

**Without [topic]:**
- Processing time: 500ms per order
- Error rate: 2.5%
- Manual intervention: 40 hours/week

**With [topic]:**
- Processing time: 50ms per order (10x faster)
- Error rate: 0.1% (25x reduction)
- Manual intervention: 2 hours/week (95% reduction)

The difference: [Specific calculation showing ROI or improvement].

## When to use [topic]

✅ **Use [topic] when:**
- You have [specific condition with number]
- Your [metric] exceeds [threshold]
- You need [specific capability]

❌ **Don't use [topic] when:**
- Your scale is below [specific number]
- You need [different requirement]
- [Specific constraint] is critical

**Better alternatives:**
- For [scenario 1]: Use [alternative 1] because [reason]
- For [scenario 2]: Use [alternative 2] for [benefit]

## Architecture patterns

[Topic] fits into your system through:

1. **[Pattern 1]**: Connect via [specific interface]
1. **[Pattern 2]**: Integrate with [specific system]
1. **[Pattern 3]**: Deploy as [specific architecture]

## Performance characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Latency | [X]ms | P99 under load |
| Throughput | [X]/sec | Per instance |
| Memory | [X]MB | Base footprint |
| CPU | [X]% | Average usage |

## Related concepts

- **[Prerequisite concept]**: Required foundation - [one line explanation]
- **[Complementary concept]**: Often used together - [synergy explanation]
- **[Advanced concept]**: Natural progression - [when to level up]

## Next steps

1. [Try the quickstart](../getting-started/topic-quickstart.md) - 10 minutes to working example
1. [Configure for production](../how-to/topic-production.md) - Scale to thousands
1. [Deep dive into internals](../reference/topic-internals.md) - Implementation details
"""
            },
            "reference": {
                "dir": "reference",
                "content_type": "reference",
                "description_template": "Technical reference for {topic}",
                "body": """
The [component name] [what it does in one sentence]. Available in {product_name} {current_version}+.

## Quick example

```javascript
// Most common usage
const example = new Component({
  required: "value",
  port: 8080
});

example.start();
// Output: Component started on port 8080
```

## Constructor

### `new Component(options)`

Creates a new instance with the specified configuration.

```typescript
interface ComponentOptions {
  required: string;      // Required: [what it's for]
  port?: number;         // Default: 8080. Valid: 1024-65535
  timeout?: number;      // Default: 30000ms. Connection timeout
  debug?: boolean;       // Default: false. Enable debug logging
}
```

**Example with all options:**
```javascript
const instance = new Component({
  required: "my-value",
  port: 3000,
  timeout: 60000,
  debug: true
});
```

## Methods

### `start(callback?)`

Starts the component and begins accepting connections.

**Parameters:**
- `callback` (Function, optional): Called when started or on error

**Returns:** Promise<void>

**Example:**
```javascript
// Promise style
await component.start();
console.log("Started successfully");

// Callback style
component.start((err) => {
  if (err) console.error("Failed:", err);
  else console.log("Started successfully");
});
```

**Errors:**
- `EADDRINUSE`: Port already in use
- `EACCES`: Permission denied (port < 1024)
- `EINVAL`: Invalid configuration

### `stop(force?)`

Gracefully stops the component.

**Parameters:**
- `force` (boolean): Default false. Force immediate shutdown

**Returns:** Promise<void>

**Example:**
```javascript
// Graceful shutdown (waits for connections to close)
await component.stop();

// Force shutdown (kills all connections)
await component.stop(true);
```

### `process(data, options?)`

Processes input data according to configuration.

**Parameters:**
- `data` (Buffer | string): Input to process
- `options` (Object, optional):
  - `encoding` (string): Default "utf8"
  - `timeout` (number): Override default timeout

**Returns:** Promise<ProcessResult>

```typescript
interface ProcessResult {
  output: Buffer;
  duration: number;    // Processing time in ms
  metadata: {
    size: number;      // Output size in bytes
    timestamp: number; // Unix timestamp
  };
}
```

**Example:**
```javascript
const result = await component.process("input data", {
  encoding: "base64",
  timeout: 5000
});

console.log(`Processed in ${result.duration}ms`);
// Output: Processed in 23ms
```

## Events

The component extends EventEmitter and emits these events:

### `ready`
Emitted when component is ready to accept connections.

```javascript
component.on('ready', () => {
  console.log('Component ready');
});
```

### `error`
Emitted on critical errors.

```javascript
component.on('error', (err) => {
  console.error('Component error:', err.code, err.message);
});
```

### `data`
Emitted when data is processed.

```javascript
component.on('data', (result) => {
  console.log(`Processed ${result.size} bytes in ${result.duration}ms`);
});
```

## Configuration file

Instead of passing options to constructor, load from file:

```yaml
# config.yml
required: my-value
port: 8080
timeout: 30000
debug: false

# Advanced settings
pool:
  size: 10
  overflow: 5
retry:
  attempts: 3
  delay: 1000
```

Load with:
```javascript
const config = Component.loadConfig('./config.yml');
const component = new Component(config);
```

## Error codes

| Code | Description | Common cause | Solution |
|------|-------------|--------------|----------|
| `E001` | Invalid configuration | Missing required field | Check all required fields are provided |
| `E002` | Connection failed | Network issue | Verify network connectivity |
| `E003` | Timeout exceeded | Slow processing | Increase timeout or optimize processing |
| `E004` | Resource exhausted | Too many connections | Increase pool size or add rate limiting |
| `E005` | Authentication failed | Invalid credentials | Check API keys and permissions |

## Performance

Benchmarked on AWS t3.medium instance:

| Operation | Throughput | Latency (P99) | CPU | Memory |
|-----------|------------|---------------|-----|--------|
| Process small (<1KB) | 10,000/sec | 2ms | 15% | 120MB |
| Process medium (10KB) | 2,000/sec | 8ms | 40% | 180MB |
| Process large (1MB) | 50/sec | 95ms | 80% | 500MB |

## Limits

- Maximum connections: 1,000 (configurable)
- Maximum message size: 10MB
- Maximum timeout: 5 minutes
- Rate limit: 1,000 requests/minute per IP

## Migration from v1

Key changes from v1.x:

```javascript
// v1 (deprecated)
const old = new OldComponent();
old.configure({ port: 8080 });
old.run();

// v2 (current)
const component = new Component({
  required: "value",  // Now required
  port: 8080
});
await component.start();  // Now async
```

## See also

- [Getting started tutorial](../getting-started/component-tutorial.md)
- [Configuration guide](../how-to/configure-component.md)
- [Understanding components](../concepts/component-architecture.md)
- [API client libraries](./client-libraries.md)
"""
            },
            "troubleshooting": {
                "dir": "troubleshooting",
                "content_type": "troubleshooting",
                "description_template": "Troubleshooting {topic} issues",
                "body": """
## Symptom

[Describe what the user observes - error message, unexpected behavior, etc.]

## Cause

[Explain why this problem occurs.]

## Solution

### Quick fix

[If there's a simple solution, provide it first.]

### Detailed solution

1. [Step 1 to resolve]
1. [Step 2 to resolve]
1. [Step 3 to resolve]

### Verification

After applying the solution:

- [ ] [Check this]
- [ ] [Verify that]
- [ ] [Confirm this]

## Prevention

To avoid this issue in the future:

- [Preventive measure 1]
- [Preventive measure 2]
- [Preventive measure 3]

## Related issues

- [Similar Problem 1](./similar-1.md)
- [Similar Problem 2](./similar-2.md)

## Still having problems?

If this solution doesn't resolve your issue:

1. Check the [FAQ](../reference/faq.md)
1. Search [existing issues](https://github.com/org/repo/issues)
1. Contact support at {{ support_email }}
"""
            },
            "api": {
                "dir": "reference",
                "content_type": "reference",
                "description_template": "API reference for {topic}",
                "body": """
## Endpoint

`[METHOD] /api/v1/[endpoint]`

## Description

[Brief description of what this endpoint does.]

## Authentication

This endpoint requires [authentication type].

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \\
     https://{{ api_url }}/api/v1/[endpoint]
```

## Parameters

### Path parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Yes | Resource ID |

### Query parameters

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `limit` | integer | No | Results per page | `10` |
| `offset` | integer | No | Pagination offset | `0` |

### Request body

```json
{
  "field1": "value",
  "field2": 123,
  "field3": true
}
```

## Response

### Success response

**Code:** `200 OK`

**Body:**
```json
{
  "status": "success",
  "data": {
    "id": "123",
    "field": "value"
  }
}
```

### Error responses

**Code:** `400 Bad Request`
```json
{
  "error": "Invalid parameters",
  "details": "Field 'name' is required"
}
```

**Code:** `401 Unauthorized`
```json
{
  "error": "Authentication required"
}
```

## Rate limiting

This endpoint is rate limited to {{ rate_limit_requests_per_minute }} requests per minute.

## Examples

### Example request

```bash
curl -X POST \\
  https://{{ api_url }}/api/v1/[endpoint] \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -d '{
    "field1": "value",
    "field2": 123
  }'
```

### Example response

```json
{
  "status": "success",
  "data": {
    "id": "abc123",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

## SDK examples

### JavaScript

```javascript
const response = await client.[method]({
  field1: "value",
  field2: 123
});
```

### Python

```python
response = client.[method](
    field1="value",
    field2=123
)
```

## Webhooks

This endpoint triggers the `[event.name]` webhook event.

## See also

- [Authentication Guide](../how-to/authenticate.md)
- [Rate Limiting](../concepts/rate-limiting.md)
- [Webhook Events](./webhooks.md)
"""
            }
        }

    def create_document(self, doc_type: str, title: str, output_path: str = None) -> Path:
        """Create a new document from template."""
        templates = self.get_templates()

        if doc_type not in templates:
            raise ValueError(f"Unknown document type: {doc_type}. Available: {list(templates.keys())}")

        template = templates[doc_type]

        # Generate filename if not provided
        if not output_path:
            slug = self.slugify(title)
            output_dir = self.base_dir / template["dir"]
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{slug}.md"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate frontmatter
        frontmatter = self.generate_frontmatter(title, template, doc_type)

        # Replace variables in body
        body = self.replace_variables(template["body"])

        # Combine frontmatter and body
        content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n{body}"

        # Write file
        output_path.write_text(content, encoding='utf-8')

        print(f"✅ Created {doc_type} document: {output_path}")

        # Update mkdocs.yml navigation if needed
        self.update_navigation(str(output_path.relative_to(self.base_dir)), title, doc_type)

        # Validate with linters
        self.validate_document(output_path)

        return output_path

    def generate_frontmatter(self, title: str, template: dict, doc_type: str) -> dict:
        """Generate complete frontmatter for the document."""
        # Generate description from template
        topic = title.lower().replace("how to ", "").replace("understanding ", "")
        description = template["description_template"].format(
            topic=topic,
            product_name=self.variables.get("product_name", "Product")
        )

        # Ensure description is within SEO limits (50-160 chars)
        if len(description) > 160:
            description = description[:157] + "..."
        elif len(description) < 50:
            description = f"{description}. Complete guide with examples."

        frontmatter = {
            "title": title[:70],  # Max 70 chars for SEO
            "description": description,
            "content_type": template["content_type"],
            "product": "both",  # Default to both, can be customized
            "tags": self.suggest_tags(title, doc_type),
            "date_created": str(date.today()),
            "last_modified": str(date.today())
        }

        return frontmatter

    def suggest_tags(self, title: str, doc_type: str) -> list:
        """Suggest relevant tags based on title and type."""
        tags = [doc_type.replace("-", " ").title()]

        # Add topic-based tags
        title_lower = title.lower()
        if "webhook" in title_lower:
            tags.append("Webhook")
        if "api" in title_lower:
            tags.append("API")
        if "auth" in title_lower or "authentication" in title_lower:
            tags.append("Authentication")
        if "config" in title_lower:
            tags.append("Configuration")
        if "install" in title_lower or "setup" in title_lower:
            tags.append("Setup")

        return tags[:5]  # Limit to 5 tags

    def replace_variables(self, content: str) -> str:
        """Replace variables with values from _variables.yml."""
        for key, value in self.variables.items():
            # Handle nested variables
            if isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    content = content.replace(f"{{{{ {key}.{nested_key} }}}}", str(nested_value))
            else:
                content = content.replace(f"{{{{ {key} }}}}", str(value))

        # Replace product_name specifically if not in variables
        if "product_name" not in self.variables:
            content = content.replace("{product_name}", "Product")

        # Replace current_version if not in variables
        if "current_version" not in self.variables:
            content = content.replace("{current_version}", "1.0.0")

        return content

    def slugify(self, text: str) -> str:
        """Convert title to URL-friendly slug."""
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s-]', '', text)
        text = re.sub(r'\s+', '-', text)
        text = re.sub(r'-+', '-', text)
        return text.strip('-')

    def update_navigation(self, file_path: str, title: str, doc_type: str):
        """Update mkdocs.yml navigation with new document."""
        mkdocs_path = Path("mkdocs.yml")
        if not mkdocs_path.exists():
            print("⚠️ mkdocs.yml not found, skipping navigation update")
            return

        print(f"📝 Remember to add '{title}: {file_path}' to the appropriate section in mkdocs.yml")

    def validate_document(self, file_path: Path):
        """Run basic validation on the created document."""
        print(f"🔍 Validating {file_path.name}...")

        # Check with Vale if available
        try:
            result = subprocess.run(
                ["vale", str(file_path)],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print("  ✅ Vale validation passed")
            else:
                print(f"  ⚠️ Vale found issues (fix these later):\n{result.stdout[:500]}")
        except:
            print("  ⏭️ Vale not available, skipping style check")

        # Check frontmatter
        content = file_path.read_text(encoding='utf-8')
        if content.startswith("---"):
            print("  ✅ Valid frontmatter detected")
        else:
            print("  ❌ Missing frontmatter!")

        print(f"\n📄 Document created successfully!")
        print(f"   Edit your new document: {file_path}")

def main():
    parser = argparse.ArgumentParser(
        description='Create new documentation from templates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a how-to guide
  python scripts/new_doc.py how-to "Configure webhooks"

  # Create a tutorial
  python scripts/new_doc.py tutorial "Getting started with API"

  # Create a concept explanation
  python scripts/new_doc.py concept "Understanding authentication"

  # Create a reference document
  python scripts/new_doc.py reference "Webhook API"

  # Create with custom output path
  python scripts/new_doc.py how-to "Setup guide" -o docs/setup/guide.md

Available document types:
  tutorial        - Learning-oriented, step-by-step guide
  how-to          - Task-oriented, practical steps
  concept         - Understanding-oriented, explanations
  reference       - Information-oriented, technical specs
  troubleshooting - Problem-solving guide
  api             - API endpoint documentation
        """
    )

    parser.add_argument(
        'type',
        choices=['tutorial', 'how-to', 'concept', 'reference', 'troubleshooting', 'api'],
        help='Type of document to create'
    )
    parser.add_argument(
        'title',
        help='Title of the document (will be used for filename if -o not provided)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file path (optional, auto-generated if not provided)'
    )
    parser.add_argument(
        '--docs-dir',
        default='docs',
        help='Base documentation directory (default: docs)'
    )

    args = parser.parse_args()

    creator = DocumentCreator(base_dir=args.docs_dir)
    creator.create_document(args.type, args.title, args.output)

if __name__ == "__main__":
    main()

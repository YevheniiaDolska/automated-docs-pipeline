#!/usr/bin/env python3
"""Generate a new documentation page from a template with pre-filled frontmatter."""

import argparse
import re
from datetime import date
from pathlib import Path

TEMPLATES = {
    "tutorial": {
        "dir": "getting-started",
        "content_type": "tutorial",
        "body": """
## Prerequisites

- List what the reader needs before starting.

## Step 1: [First action]

Describe the first step.

## Step 2: [Second action]

Describe the second step.

## Step 3: [Verify the result]

Describe how to verify everything works.

## Next steps

- Link to related how-to guides
- Link to relevant concepts
"""
    },
    "how-to": {
        "dir": "how-to",
        "content_type": "how-to",
        "body": """
## Prerequisites

- List requirements.

## Steps

1. First step.
2. Second step.
3. Third step.

## Verify

Describe how to confirm the task is complete.

## Related

- Link to reference pages
- Link to troubleshooting
"""
    },
    "concept": {
        "dir": "concepts",
        "content_type": "concept",
        "body": """
## How it works

Explain the architecture or design.

```mermaid
flowchart LR
    A[Input] --> B[Process] --> C[Output]
```

## Key principles

Explain the important design decisions.

## Implications

What does this mean for users?

## Related

- Link to tutorials that use this concept
- Link to reference pages
"""
    },
    "reference": {
        "dir": "reference/nodes",
        "content_type": "reference",
        "body": """
## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| **Parameter 1** | string | `""` | Description |
| **Parameter 2** | enum | `option_a` | Options: `option_a`, `option_b` |

## Output

```json
{
  "json": {
    "key": "value"
  }
}
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VAR_NAME` | `value` | Description |

## Related

- Link to how-to guides
- Link to troubleshooting
"""
    },
    "troubleshooting": {
        "dir": "troubleshooting",
        "content_type": "troubleshooting",
        "body": """
## Cause 1: [Most common cause]

**Symptom:** What the user sees.

**Why:** Why this happens.

**Fix:** How to resolve it.

## Cause 2: [Second cause]

**Symptom:** What the user sees.

**Why:** Why this happens.

**Fix:** How to resolve it.

## Still not working?

1. Check logs.
2. Verify configuration.
3. Ask on the community forum.

## Related

- Link to reference page
- Link to how-to guide
"""
    }
}

def slugify(title):
    slug = title.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')

def main():
    parser = argparse.ArgumentParser(description="Generate a new doc page from template")
    parser.add_argument("--type", required=True, choices=TEMPLATES.keys(), help="Document type")
    parser.add_argument("--title", required=True, help="Page title")
    parser.add_argument("--product", default="both", choices=["n8n-cloud", "n8n-self-hosted", "both"])
    parser.add_argument("--component", default=None, help="n8n component (webhook, code, ai-agent, etc.)")
    args = parser.parse_args()

    template = TEMPLATES[args.type]
    slug = slugify(args.title)
    filepath = Path(f"docs/{template['dir']}/{slug}.md")

    tags_list = [args.type.capitalize().replace("-", "-").title()]
    if args.type == "how-to":
        tags_list = ["How-To"]
    elif args.type == "troubleshooting":
        tags_list = ["Troubleshooting"]

    frontmatter = f"""---
title: "{args.title}"
description: "Comprehensive guide covering all aspects of this topic with examples and best practices."
content_type: {template['content_type']}
product: {args.product}"""

    if args.component:
        frontmatter += f"\nn8n_component: {args.component}"

    frontmatter += f"""
tags:
  - {tags_list[0]}
---

# {args.title}
{template['body']}"""

    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(frontmatter)
    print(f"✅ Created: {filepath}")
    print(f"   Don't forget to:")
    print(f"   1. Write a proper description (50-160 chars)")
    print(f"   2. Add the page to mkdocs.yml nav section")
    print(f"   3. Fill in the content")

if __name__ == "__main__":
    main()

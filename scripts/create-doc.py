#!/usr/bin/env python3
"""
Quick document creator with all formatting rules built-in.
Usage: python scripts/create-doc.py --type how-to --title "Configure webhooks"
NOTE: All templates follow linting rules and are product-agnostic.
"""

import argparse
import os
from pathlib import Path
from datetime import datetime


TEMPLATES = {
    'tutorial': {
        'path': 'docs/getting-started',
        'template': '''---
title: "{title}"
description: "{description}"
content_type: tutorial
product: both
tags:
  - Tutorial
---

## {title}

{intro}

## Prerequisites

Before you begin, ensure you have:

- First requirement
- Second requirement

## Step 1: First step

1. First action
1. Second action
1. Third action

## Step 2: Second step

```bash
# Example command
echo "example"
```

## Next steps

- [Related guide](../how-to/related.md)
- [Troubleshooting](../troubleshooting/common-issues.md)
'''
    },
    'how-to': {
        'path': 'docs/how-to',
        'template': '''---
title: "{title}"
description: "{description}"
content_type: how-to
product: both
tags:
  - How-To
---

## {title}

{intro}

## Prerequisites

- Required setup
- Required access

## Configure the feature

1. Open settings
1. Select option
1. Save changes

## Verify configuration

```bash
# Test command
curl http://localhost:5678/test
```

## Troubleshooting

If issues occur, check:

- Configuration is saved
- Service is running
'''
    }
}


def create_document(doc_type, title, description=None):
    """Create a new document with proper formatting."""
    if doc_type not in TEMPLATES:
        print(f"Unknown type: {doc_type}")
        return

    template_info = TEMPLATES[doc_type]

    # Generate description if not provided
    if not description:
        description = f"Learn how to {title.lower()}. Step-by-step guide with examples."

    # Generate intro paragraph (under 60 words)
    intro = f"This guide shows you how to {title.lower()}. Follow these steps to get started quickly."

    # Create filename
    filename = title.lower().replace(' ', '-').replace('/', '-') + '.md'
    filepath = Path(template_info['path']) / filename

    # Fill template
    content = template_info['template'].format(
        title=title,
        description=description[:160],  # Max 160 chars
        intro=intro
    )

    # Create file
    os.makedirs(template_info['path'], exist_ok=True)
    filepath.write_text(content)

    print(f"✅ Created: {filepath}")
    print(f"📝 Type: {doc_type}")
    print(f"📂 Location: {template_info['path']}")
    print("\nNext steps:")
    print("1. Edit the content in the file")
    print("2. Update mkdocs.yml navigation")
    print("3. Run: git add . && git commit")


def main():
    parser = argparse.ArgumentParser(description='Create a new documentation file')
    parser.add_argument('--type', required=True, choices=TEMPLATES.keys(),
                        help='Document type')
    parser.add_argument('--title', required=True,
                        help='Document title')
    parser.add_argument('--description',
                        help='SEO description (optional)')

    args = parser.parse_args()
    create_document(args.type, args.title, args.description)


if __name__ == '__main__':
    main()

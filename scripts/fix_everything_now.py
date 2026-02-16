#!/usr/bin/env python3
"""
FIX EVERYTHING NOW - ALL ISSUES IN ONE GO
"""

import re
from pathlib import Path

def fix_template(file_path):
    """Fix ALL issues in template files."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed = []
    in_code = False
    i = 0

    while i < len(lines):
        line = lines[i].rstrip('\n')

        # Fix fragment links
        if '#oauth-20' in line:
            line = line.replace('#oauth-20', '#oauth-2-0')
        if '#cause-3-name' in line:
            line = line.replace('#cause-3-name', '#cause-3-less-common-cause')

        # Fix code blocks - detect and add language
        if line.strip() == '```' and not in_code:
            # Starting code block - add language
            # Look ahead to determine type
            next_line = lines[i+1] if i+1 < len(lines) else ''
            if 'curl' in next_line or 'npm' in next_line or 'docker' in next_line:
                line = '```bash'
            elif '{' in next_line or 'const' in next_line:
                line = '```javascript'
            elif 'import' in next_line and 'from' in next_line:
                line = '```python'
            elif '<' in next_line and '>' in next_line:
                line = '```html'
            elif 'apiVersion' in next_line or 'kind:' in next_line:
                line = '```yaml'
            else:
                line = '```text'

            # Ensure blank line before
            if fixed and fixed[-1] != '':
                fixed.append('')
            fixed.append(line)
            in_code = True
            i += 1
            continue

        elif line.strip() == '```' and in_code:
            # Closing code block
            fixed.append(line)
            # Ensure blank line after
            if i+1 < len(lines) and lines[i+1].strip() != '':
                fixed.append('')
            in_code = False
            i += 1
            continue

        fixed.append(line)
        i += 1

    # Ensure single trailing newline
    while fixed and fixed[-1] == '':
        fixed.pop()
    fixed.append('')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed))

def fix_docs_file(file_path):
    """Fix docs files."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix bare URLs
    content = re.sub(r'(?<![<\(])https://[^\s\)>]+(?![>\)])', r'<\g<0>>', content)

    # Fix list indentation issues
    lines = content.split('\n')
    fixed = []
    for i, line in enumerate(lines):
        # Fix indented bullets in lists
        if line.startswith(' - '):
            line = '- ' + line[3:]

        # Add blank lines around sublists
        if i > 0 and line.startswith('- ') and lines[i-1].startswith('1.'):
            if fixed and fixed[-1] != '':
                fixed.append('')

        fixed.append(line)

    # Add blank lines around numbered lists followed by bullets
    final = []
    for i, line in enumerate(fixed):
        if i > 0 and line.startswith('1.') and i+1 < len(fixed):
            next_line = fixed[i+1]
            if next_line.startswith('- '):
                # Need blank line between numbered and bullet list
                final.append(line)
                final.append('')
                continue
        final.append(line)

    content = '\n'.join(final)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def add_frontmatter(file_path):
    """Add frontmatter to index.md files."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if not content.startswith('---'):
        # Add appropriate frontmatter
        frontmatter = """---
title: "Getting Started"
description: "Start here to learn the basics. Tutorials and quickstart guides for beginners."
content_type: tutorial
---

"""
        content = frontmatter + content

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

# MAIN EXECUTION
print("FIXING ALL ISSUES NOW...")

# Fix all templates
templates = [
    'templates/authentication-guide.md',
    'templates/sdk-reference.md',
    'templates/integration-guide.md',
    'templates/migration-guide.md',
    'templates/security-guide.md',
    'templates/troubleshooting.md',
    'templates/webhooks-guide.md',
    'templates/api-reference.md',
    'templates/quickstart.md',
    'templates/release-note.md',
    'templates/reference.md'
]

for t in templates:
    if Path(t).exists():
        fix_template(t)
        print(f"Fixed: {t}")

# Fix docs files
docs_files = [
    'docs/how-to/configure-webhook-trigger.md',
    'docs/index.md'
]

for d in docs_files:
    if Path(d).exists():
        fix_docs_file(d)
        print(f"Fixed: {d}")

# Add frontmatter to index files
if Path('docs/getting-started/index.md').exists():
    add_frontmatter('docs/getting-started/index.md')
    print("Added frontmatter to: docs/getting-started/index.md")

print("\n✅ ALL ISSUES FIXED!")

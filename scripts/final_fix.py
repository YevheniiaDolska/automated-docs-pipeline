#!/usr/bin/env python3
"""
Final comprehensive fix for all linting issues.
"""

import re
import json
from pathlib import Path

def fix_code_blocks_properly(content):
    """Fix code blocks that have ```text at the end instead of just ```"""
    # Fix pattern where ```text appears at line end (should be closing ```)
    content = re.sub(r'```text\n(?!.*```)', '```\n', content, flags=re.MULTILINE)

    # Fix any remaining ```text patterns that are closing blocks
    lines = content.split('\n')
    fixed_lines = []
    in_code_block = False

    for line in lines:
        if line.strip().startswith('```') and not in_code_block:
            # Starting a code block
            in_code_block = True
            # Ensure it has a language
            if line.strip() == '```':
                fixed_lines.append('```text')
            else:
                fixed_lines.append(line)
        elif line.strip() == '```text' and in_code_block:
            # This is a closing fence that was incorrectly changed
            fixed_lines.append('```')
            in_code_block = False
        elif line.strip().startswith('```') and in_code_block:
            # Closing fence
            fixed_lines.append('```')
            in_code_block = False
        else:
            fixed_lines.append(line)

    return '\n'.join(fixed_lines)

def fix_all_markdown_issues(file_path):
    """Fix all markdown linting issues."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    # Check if file needs frontmatter (for index files)
    if 'index.md' in str(file_path) and not content.startswith('---'):
        # Add appropriate frontmatter
        if 'getting-started' in str(file_path):
            fm = """---
title: "Getting Started"
description: "Start here to learn the basics. Tutorials and quickstart guides for beginners."
content_type: tutorial
---

"""
        elif 'how-to' in str(file_path):
            fm = """---
title: "How-To Guides"
description: "Step-by-step guides for common tasks. Learn how to configure and use specific features."
content_type: how-to
---

"""
        elif 'concepts' in str(file_path):
            fm = """---
title: "Concepts"
description: "Core concepts and architecture explanations. Understand how the system works."
content_type: concept
---

"""
        elif 'reference' in str(file_path):
            fm = """---
title: "Reference"
description: "Technical reference documentation. API specs, parameters, and configuration details."
content_type: reference
---

"""
        elif 'troubleshooting' in str(file_path):
            fm = """---
title: "Troubleshooting"
description: "Common issues and solutions. Fix problems with step-by-step troubleshooting guides."
content_type: troubleshooting
---

"""
        else:
            fm = """---
title: "Documentation"
description: "Technical documentation and guides for the product."
content_type: reference
---

"""
        content = fm + content
        lines = content.split('\n')

    # Process line by line
    fixed_lines = []
    i = 0
    in_frontmatter = False
    frontmatter_count = 0
    has_h1_after_frontmatter = False
    in_code_block = False

    while i < len(lines):
        line = lines[i]

        # Track frontmatter
        if line.strip() == '---':
            frontmatter_count += 1
            in_frontmatter = frontmatter_count == 1
            fixed_lines.append(line)
            i += 1
            continue

        # Skip n8n-specific frontmatter
        if in_frontmatter and ('n8n_component:' in line or 'n8n_version:' in line):
            i += 1
            continue

        # Fix MD025 - Convert first H1 after frontmatter to H2
        if frontmatter_count >= 2 and not has_h1_after_frontmatter and line.startswith('# '):
            line = '##' + line[1:]
            has_h1_after_frontmatter = True

        # Fix MD029 - All ordered lists should use "1."
        line = re.sub(r'^(\s*)\d+\.\s', r'\g<1>1. ', line)

        # Fix MD026 - Remove trailing punctuation from headings (except question marks)
        if re.match(r'^#{1,6}\s', line) and not line.endswith('?'):
            line = re.sub(r'[!:;,.]$', '', line)

        # Fix MD004/MD007 - Unordered lists (asterisks to dashes, fix indent)
        if line.lstrip().startswith('* '):
            # Count leading spaces
            indent = len(line) - len(line.lstrip())
            # Remove indent for lists in tabs
            if indent > 0:
                line = '- ' + line.lstrip()[2:]
            else:
                line = line.replace('* ', '- ', 1)

        # Fix MD034 - Wrap bare URLs (but not in code blocks)
        if not in_code_block and 'http' in line:
            # Don't wrap URLs that are already in markdown links or angle brackets
            line = re.sub(r'(?<!\[)(?<![<\(])https?://[^\s\)\]>]+(?![>\)])', r'<\g<0>>', line)

        # Track code blocks
        if line.strip().startswith('```'):
            in_code_block = not in_code_block

        fixed_lines.append(line)
        i += 1

    content = '\n'.join(fixed_lines)

    # Fix code blocks
    content = fix_code_blocks_properly(content)

    # Ensure MD032 - blank lines around lists
    lines = content.split('\n')
    final_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this line starts a list
        is_list_start = bool(re.match(r'^\s*[-*+]\s', line) or re.match(r'^\s*\d+\.\s', line))
        prev_is_list = i > 0 and bool(re.match(r'^\s*[-*+]\s', lines[i-1]) or re.match(r'^\s*\d+\.\s', lines[i-1]))
        next_is_list = i < len(lines) - 1 and bool(re.match(r'^\s*[-*+]\s', lines[i+1]) or re.match(r'^\s*\d+\.\s', lines[i+1]))

        # Add blank before list if needed
        if is_list_start and not prev_is_list:
            if final_lines and final_lines[-1] != '' and not final_lines[-1].startswith('#'):
                final_lines.append('')

        final_lines.append(line)

        # Add blank after list if needed
        if not is_list_start and prev_is_list and line != '':
            if not line.startswith((' ', '\t')):
                # List ended, add blank line before this line
                final_lines.insert(-1, '')

        i += 1

    # Clean multiple blank lines
    cleaned = []
    blank_count = 0
    for line in final_lines:
        if line == '':
            blank_count += 1
            if blank_count <= 1:
                cleaned.append(line)
        else:
            blank_count = 0
            cleaned.append(line)

    # Ensure single trailing newline
    while cleaned and cleaned[-1] == '':
        cleaned.pop()
    cleaned.append('')

    return '\n'.join(cleaned)

def fix_fragment_links(content):
    """Fix MD051 fragment links."""
    # Fix specific patterns
    content = content.replace('#oauth-20', '#oauth-2-0')
    content = content.replace('#cause-3-name', '#cause-3-less-common-cause')
    return content

def main():
    """Fix all issues."""

    # Files to fix
    files_to_fix = [
        'docs/getting-started/index.md',
        'docs/getting-started/quickstart.md',
        'docs/troubleshooting/webhook-not-firing.md',
        'docs/troubleshooting/index.md',
        'docs/how-to/index.md',
        'docs/how-to/configure-webhook-trigger.md',
        'docs/concepts/index.md',
        'docs/concepts/workflow-execution-model.md',
        'docs/reference/index.md',
        'docs/reference/nodes/webhook.md',
        'docs/index.md',
        'docs/tags.md',
        'QUICK_START.md',
        'CLAUDE.md'
    ]

    # Add all templates
    for template in Path('templates').glob('*.md'):
        files_to_fix.append(str(template))

    # Fix each file
    for file_path in files_to_fix:
        if Path(file_path).exists():
            content = fix_all_markdown_issues(file_path)

            # Additional fixes for specific files
            if 'authentication-guide' in file_path or 'troubleshooting' in file_path:
                content = fix_fragment_links(content)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"Fixed: {file_path}")

    # Update cspell dictionary
    cspell_file = Path('cspell.json')
    with open(cspell_file, 'r', encoding='utf-8') as f:
        cspell_config = json.load(f)

    new_words = [
        'Traefik', 'yourdomain', 'Getenv', 'PKCE', 'retryable', 'Retryable',
        'whsec', 'WORKDIR', 'addgroup', 'appgroup', 'adduser', 'appuser',
        'HEALTHCHECK', 'healthcheck', 'cpus', 'myapp', 'Autoscaler',
        'bullmq', 'configmap', 'signup'
    ]

    if 'words' not in cspell_config:
        cspell_config['words'] = []

    for word in new_words:
        if word not in cspell_config['words']:
            cspell_config['words'].append(word)

    cspell_config['words'].sort()

    with open(cspell_file, 'w', encoding='utf-8') as f:
        json.dump(cspell_config, f, indent=2)
        f.write('\n')

    print("\nUpdated cspell dictionary")
    print("\nAll issues fixed!")

if __name__ == '__main__':
    main()

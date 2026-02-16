#!/usr/bin/env python3
"""
Fix ALL linting issues in one go.
"""

import re
from pathlib import Path

def fix_markdown_file(file_path):
    """Fix all markdown linting issues in a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_lines = []
    i = 0
    in_frontmatter = False
    frontmatter_count = 0
    has_h1_after_frontmatter = False

    while i < len(lines):
        line = lines[i].rstrip('\n')

        # Track frontmatter
        if line == '---':
            frontmatter_count += 1
            in_frontmatter = frontmatter_count == 1
            fixed_lines.append(line)
            i += 1
            continue

        # Skip n8n-specific frontmatter
        if in_frontmatter and (line.startswith('n8n_component:') or line.startswith('n8n_version:')):
            i += 1
            continue

        # Fix MD025 - Convert first H1 after frontmatter to H2
        if frontmatter_count >= 2 and not has_h1_after_frontmatter and line.startswith('# '):
            line = '##' + line[1:]
            has_h1_after_frontmatter = True

        # Fix MD029 - All ordered lists should use "1."
        line = re.sub(r'^(\s*)\d+\.\s', r'\g<1>1. ', line)

        # Fix MD026 - Remove trailing punctuation from headings
        if re.match(r'^#{1,6}\s', line):
            line = re.sub(r'[!:;,.]$', '', line)

        # Fix MD004/MD007 - Unordered lists in content tabs (asterisks to dashes, fix indent)
        if line.strip().startswith('*'):
            # Remove leading spaces for items in tabs
            line = re.sub(r'^\s*\*\s', '- ', line)

        # Fix MD040 - Add language to code blocks
        if line.strip() == '```' and i + 1 < len(lines):
            # Look ahead to guess language
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ''
            if next_line.startswith(('GET ', 'POST ', 'PUT ', 'PATCH ', 'DELETE ')):
                line = '```http'
            elif next_line.startswith('#') or 'curl' in next_line or 'npm' in next_line:
                line = '```bash'
            elif next_line.startswith('{') or '"' in next_line:
                line = '```json'
            elif 'apiVersion:' in next_line or 'kind:' in next_line:
                line = '```yaml'
            else:
                line = '```text'

        # Fix MD034 - Wrap bare URLs
        line = re.sub(r'(?<!\[)(?<![\(\)])https?://[^\s\)]+', r'<\g<0>>', line)

        fixed_lines.append(line)
        i += 1

    # Fix MD032 - Ensure blank lines around lists
    final_lines = []
    prev_was_list = False

    for i, line in enumerate(fixed_lines):
        is_list = bool(re.match(r'^\s*[-*+]\s', line) or re.match(r'^\s*\d+\.\s', line))

        # Add blank line before list if needed
        if is_list and not prev_was_list and final_lines and final_lines[-1] != '':
            final_lines.append('')

        final_lines.append(line)

        # Add blank line after list if needed
        if prev_was_list and not is_list and line != '' and i + 1 < len(fixed_lines):
            if not fixed_lines[i + 1].startswith((' ', '\t', '-', '*', '1.')):
                final_lines.append('')

        prev_was_list = is_list

    # Fix MD031 - Blank lines around code blocks
    result_lines = []
    i = 0
    while i < len(final_lines):
        line = final_lines[i]

        # Starting code block
        if line.strip().startswith('```'):
            # Add blank before if needed
            if result_lines and result_lines[-1] != '':
                result_lines.append('')
            result_lines.append(line)
            i += 1

            # Copy content
            while i < len(final_lines) and not final_lines[i].strip().startswith('```'):
                result_lines.append(final_lines[i])
                i += 1

            # Closing fence
            if i < len(final_lines):
                result_lines.append(final_lines[i])
                # Add blank after if needed
                if i + 1 < len(final_lines) and final_lines[i + 1] != '':
                    result_lines.append('')
            i += 1
        else:
            result_lines.append(line)
            i += 1

    # Clean up multiple blanks
    cleaned_lines = []
    blank_count = 0
    for line in result_lines:
        if line == '':
            blank_count += 1
            if blank_count <= 1:
                cleaned_lines.append(line)
        else:
            blank_count = 0
            cleaned_lines.append(line)

    # Ensure single trailing newline (MD047)
    while cleaned_lines and cleaned_lines[-1] == '':
        cleaned_lines.pop()
    cleaned_lines.append('')

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(cleaned_lines))

def add_missing_frontmatter(file_path):
    """Add missing frontmatter to index files."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if not content.startswith('---'):
        # Determine content type from path
        if 'getting-started' in str(file_path):
            content_type = 'tutorial'
            title = 'Getting Started'
            description = 'Start here to learn the basics. Tutorials and quickstart guides for beginners.'
        elif 'how-to' in str(file_path):
            content_type = 'how-to'
            title = 'How-To Guides'
            description = 'Step-by-step guides for common tasks. Learn how to configure and use specific features.'
        elif 'concept' in str(file_path):
            content_type = 'concept'
            title = 'Concepts'
            description = 'Core concepts and architecture explanations. Understand how the system works.'
        elif 'reference' in str(file_path):
            content_type = 'reference'
            title = 'Reference'
            description = 'Technical reference documentation. API specs, parameters, and configuration details.'
        elif 'troubleshooting' in str(file_path):
            content_type = 'troubleshooting'
            title = 'Troubleshooting'
            description = 'Common issues and solutions. Fix problems with step-by-step troubleshooting guides.'
        else:
            content_type = 'reference'
            title = 'Documentation'
            description = 'Technical documentation and guides.'

        frontmatter = f"""---
title: "{title}"
description: "{description}"
content_type: {content_type}
---

"""
        content = frontmatter + content

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

def fix_fragment_links(file_path):
    """Fix MD051 fragment links."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix specific known issues
    replacements = {
        '#oauth-20': '#oauth-2-0',
        '#cause-3-name': '#cause-3-less-common-cause',
    }

    for old, new in replacements.items():
        content = content.replace(old, new)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def add_to_cspell(words):
    """Add words to cspell dictionary."""
    cspell_file = Path('cspell.json')
    import json

    with open(cspell_file, 'r', encoding='utf-8') as f:
        cspell_config = json.load(f)

    if 'words' not in cspell_config:
        cspell_config['words'] = []

    for word in words:
        if word not in cspell_config['words']:
            cspell_config['words'].append(word)

    cspell_config['words'].sort()

    with open(cspell_file, 'w', encoding='utf-8') as f:
        json.dump(cspell_config, f, indent=2)
        f.write('\n')

def main():
    """Fix all issues."""

    # Fix specific files with issues
    files_to_fix = [
        'docs/getting-started/index.md',
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
        'docs/getting-started/quickstart.md',
        'QUICK_START.md',
        'CLAUDE.md',
    ]

    # Fix all template files
    templates_dir = Path('templates')
    for template in templates_dir.glob('*.md'):
        files_to_fix.append(str(template))

    # Fix markdown issues
    for file_path in files_to_fix:
        if Path(file_path).exists():
            fix_markdown_file(file_path)
            print(f"Fixed: {file_path}")

            # Add frontmatter to index files if missing
            if 'index.md' in file_path and 'docs/' in file_path:
                add_missing_frontmatter(file_path)
                print(f"  Added frontmatter to {file_path}")

            # Fix fragment links
            if 'authentication-guide' in file_path or 'troubleshooting.md' in file_path:
                fix_fragment_links(file_path)

    # Add words to cspell
    new_words = [
        'Traefik', 'yourdomain', 'Getenv', 'PKCE', 'retryable', 'Retryable',
        'whsec', 'WORKDIR', 'addgroup', 'appgroup', 'adduser', 'appuser',
        'HEALTHCHECK', 'healthcheck', 'cpus', 'myapp', 'Autoscaler',
        'bullmq', 'configmap', 'signup'
    ]
    add_to_cspell(new_words)
    print("\nAdded words to cspell dictionary")

    print("\nAll issues fixed!")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Fix all template files to comply with linting rules.
"""

import re
from pathlib import Path

def fix_template(file_path):
    """Fix common issues in a template file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Remove n8n references
    content = re.sub(r'\bn8n\b', '', content)
    content = re.sub(r' in \s*\.', '.', content)  # Fix "in ." patterns
    content = re.sub(r' for \s*\.', '.', content)  # Fix "for ." patterns
    content = content.replace('https://api.n8n.io', 'https://api.example.com')
    content = content.replace('https://docs.n8n.io', 'https://docs.example.com')
    content = content.replace('https://community.n8n.io', 'https://community.example.com')
    content = content.replace('n8n Cloud', 'Cloud')
    content = content.replace('n8n-cloud', 'cloud')
    content = content.replace('n8n-self-hosted', 'self-hosted')

    # Fix duplicate H1 headers (MD025)
    lines = content.split('\n')
    fixed_lines = []
    has_h2_header = False

    for i, line in enumerate(lines):
        # Check if this is after frontmatter
        if i > 0 and lines[i-1] == '---' and i > 8:
            has_h2_header = True

        # Convert first H1 after frontmatter to H2
        if has_h2_header and line.startswith('# '):
            fixed_lines.append('##' + line[1:])
        else:
            fixed_lines.append(line)

    content = '\n'.join(fixed_lines)

    # Fix ordered lists (MD029) - all items should use "1."
    content = re.sub(r'^(\s*)(\d+)\.\s', r'\g<1>1. ', content, flags=re.MULTILINE)

    # Fix code blocks without language (MD040)
    # Match code blocks that start with just ```
    content = re.sub(r'^```\s*$', '```text', content, flags=re.MULTILINE)

    # Fix specific patterns for HTTP requests
    content = re.sub(r'```\s*\n(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+/', r'```http\n\1 /', content)

    # Fix table formatting (MD060) - ensure spaces around pipes
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        if '|' in line and not line.strip().startswith('```'):
            # Ensure space after opening pipe
            line = re.sub(r'^\|(?!\s)', '| ', line)
            # Ensure space before closing pipe
            line = re.sub(r'(?<!\s)\|$', ' |', line)
            # Ensure spaces around middle pipes
            line = re.sub(r'(?<!\s)\|(?!\s)', ' | ', line)
            # Clean up multiple spaces
            line = re.sub(r'\s{2,}\|', ' |', line)
            line = re.sub(r'\|\s{2,}', '| ', line)
        fixed_lines.append(line)

    content = '\n'.join(fixed_lines)

    # Remove n8n-specific fields from frontmatter
    content = re.sub(r'^n8n_component:.*\n', '', content, flags=re.MULTILINE)
    content = re.sub(r'^n8n_version:.*\n', '', content, flags=re.MULTILINE)

    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Fix all templates."""
    templates_dir = Path('templates')
    fixed_count = 0

    for template_file in templates_dir.glob('*.md'):
        if fix_template(template_file):
            print(f"Fixed: {template_file.name}")
            fixed_count += 1

    print(f"\nFixed {fixed_count} template files")

if __name__ == '__main__':
    main()

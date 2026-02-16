#!/usr/bin/env python3
"""
Remove n8n references from documentation files.
"""

import re
from pathlib import Path

def remove_n8n_references(file_path):
    """Remove n8n references from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Remove n8n references but keep context
    content = re.sub(r'\bn8n\s+', '', content)  # Remove "n8n " prefix
    content = re.sub(r'\sn8n\b', '', content)  # Remove " n8n" suffix
    content = re.sub(r'\bn8n\b', 'the product', content)  # Replace standalone n8n

    # Fix specific patterns
    content = content.replace('https://docs.n8n.io', 'https://docs.example.com')
    content = content.replace('https://community.n8n.io', 'https://community.example.com')
    content = content.replace('n8n Cloud', 'Cloud')
    content = content.replace('n8n-cloud', 'cloud')
    content = content.replace('n8n-self-hosted', 'self-hosted')
    content = content.replace('N8N_', 'APP_')  # Environment variables
    content = content.replace('n8n_', 'app_')

    # Remove n8n-specific frontmatter fields
    lines = content.split('\n')
    fixed_lines = []
    in_frontmatter = False
    frontmatter_count = 0

    for line in lines:
        if line.strip() == '---':
            frontmatter_count += 1
            in_frontmatter = frontmatter_count == 1
            fixed_lines.append(line)
        elif in_frontmatter and (line.startswith('n8n_component:') or line.startswith('n8n_version:')):
            continue  # Skip n8n-specific fields
        else:
            fixed_lines.append(line)

    content = '\n'.join(fixed_lines)

    # Clean up any double spaces created
    content = re.sub(r'  +', ' ', content)

    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Remove n8n from all docs."""
    docs_dir = Path('docs')
    fixed_count = 0

    # Find all markdown files
    for md_file in docs_dir.glob('**/*.md'):
        if remove_n8n_references(md_file):
            print(f"Fixed: {md_file.relative_to(docs_dir)}")
            fixed_count += 1

    print(f"\nRemoved n8n references from {fixed_count} files")

if __name__ == '__main__':
    main()

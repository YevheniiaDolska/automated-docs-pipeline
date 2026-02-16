#!/usr/bin/env python3
"""
Fix VS Code snippets to follow linting rules and remove n8n references.
"""

import json
import re

def fix_snippet_body(body_lines):
    """Fix snippet body to follow linting rules."""
    fixed_lines = []

    for line in body_lines:
        # Remove n8n references
        line = line.replace('n8n-cloud', 'cloud')
        line = line.replace('n8n-self-hosted', 'self-hosted')
        line = line.replace('n8n Cloud', 'Cloud')
        line = line.replace('n8n version', 'version')
        line = line.replace(' in ${3:product}', '')
        line = line.replace(' in n8n', '')

        # Remove n8n_component and n8n_version frontmatter fields from snippets
        if 'n8n_component:' in line or 'n8n_version:' in line:
            continue

        # Fix H1 headers to H2 (after frontmatter)
        if line.strip().startswith('"# '):
            line = line.replace('"# ', '"## ')
        elif line.strip() == '# ':
            line = line.replace('# ', '## ')

        # Fix ordered lists - change 2. and 3. to 1.
        line = re.sub(r'"(\s*)2\.\s', r'"\g<1>1. ', line)
        line = re.sub(r'"(\s*)3\.\s', r'"\g<1>1. ', line)
        line = re.sub(r'^(\s*)2\.\s', r'\g<1>1. ', line)
        line = re.sub(r'^(\s*)3\.\s', r'\g<1>1. ', line)

        fixed_lines.append(line)

    return fixed_lines

def main():
    """Fix VS Code snippets file."""
    snippets_file = '.vscode/docs.code-snippets'

    # Read the file
    with open(snippets_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse as JSON
    try:
        snippets = json.loads(content)
    except json.JSONDecodeError:
        print("Error: Could not parse snippets file as JSON")
        return

    # Fix each snippet
    for name, snippet in snippets.items():
        if 'body' in snippet and isinstance(snippet['body'], list):
            snippet['body'] = fix_snippet_body(snippet['body'])

    # Write back with proper formatting
    with open(snippets_file, 'w', encoding='utf-8') as f:
        json.dump(snippets, f, indent=2, ensure_ascii=False)
        f.write('\n')

    print(f"Fixed: {snippets_file}")
    print("- Removed n8n references")
    print("- Fixed H1 headers to H2")
    print("- Fixed ordered list numbering")
    print("- Removed n8n-specific frontmatter fields")

if __name__ == '__main__':
    main()

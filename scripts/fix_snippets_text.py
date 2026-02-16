#!/usr/bin/env python3
"""
Fix VS Code snippets using text processing (since it has comments).
"""

import re

def fix_snippets_file(file_path):
    """Fix snippets file as text."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Remove n8n references
    content = content.replace('n8n-cloud', 'cloud')
    content = content.replace('n8n-self-hosted', 'self-hosted')
    content = content.replace('"n8n Cloud"', '"Cloud"')
    content = content.replace('=== \\"n8n Cloud\\"', '=== \\"Cloud\\"')
    content = content.replace(' in ${3:product}"', '"')
    content = content.replace(' in n8n"', '"')
    content = content.replace('n8n version', 'version')

    # Fix product options
    content = content.replace('${6|both,n8n-cloud,n8n-self-hosted|}', '${6|both,cloud,self-hosted|}')
    content = content.replace('${5|both,n8n-cloud,n8n-self-hosted|}', '${5|both,cloud,self-hosted|}')
    content = content.replace('${4|both,n8n-cloud,n8n-self-hosted|}', '${4|both,cloud,self-hosted|}')

    # Remove n8n_component and n8n_version lines
    lines = content.split('\n')
    fixed_lines = []
    for line in lines:
        if 'n8n_component:' in line or 'n8n_version:' in line:
            continue  # Skip these lines
        fixed_lines.append(line)
    content = '\n'.join(fixed_lines)

    # Fix H1 headers to H2 in body arrays
    # Match pattern like "# ${1:Action} ${2:thing}"
    content = re.sub(r'"\s*#\s+\$\{', r'"## ${', content)
    content = re.sub(r'"\s*#\s+([A-Z])', r'"## \1', content)

    # Fix ordered lists - change "2. " and "3. " to "1. "
    content = re.sub(r'"(\s*)2\.\s', r'"\g<1>1. ', content)
    content = re.sub(r'"(\s*)3\.\s', r'"\g<1>1. ', content)

    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Fix VS Code snippets."""
    snippets_file = '.vscode/docs.code-snippets'

    if fix_snippets_file(snippets_file):
        print(f"Fixed: {snippets_file}")
        print("- Removed n8n references")
        print("- Fixed H1 headers to H2")
        print("- Fixed ordered list numbering")
        print("- Removed n8n-specific frontmatter fields")
    else:
        print("No changes needed")

if __name__ == '__main__':
    main()

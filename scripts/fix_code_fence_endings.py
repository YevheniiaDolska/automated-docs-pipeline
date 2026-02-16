#!/usr/bin/env python3
"""
Fix code fence endings that have ```text instead of just ```
"""

import re
from pathlib import Path

def fix_code_fence_endings(file_path):
    """Fix malformed code fence endings."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Replace lines that end with ```text (which should be closing fences)
    # This happens when a code block ends and ```text was incorrectly added
    content = re.sub(r'```text\n', '```\n', content)

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
        if fix_code_fence_endings(template_file):
            print(f"Fixed: {template_file.name}")
            fixed_count += 1

    print(f"\nFixed {fixed_count} template files")

if __name__ == '__main__':
    main()

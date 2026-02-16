#!/usr/bin/env python3
"""
Fix code block language specifiers in templates.
"""

import re
from pathlib import Path

def fix_code_blocks(file_path):
    """Fix malformed code blocks."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Fix pattern where ```text appears at the end of blocks
    content = re.sub(r'```text\n(.*?)\n```text', r'```\n\1\n```', content, flags=re.DOTALL)

    # Fix standalone ```text lines that should close blocks
    lines = content.split('\n')
    fixed_lines = []
    in_code_block = False

    for line in lines:
        if line.strip() == '```text':
            if in_code_block:
                # This closes a block
                fixed_lines.append('```')
                in_code_block = False
            else:
                # This opens a block
                fixed_lines.append('```text')
                in_code_block = True
        elif line.strip().startswith('```'):
            if line.strip() == '```':
                in_code_block = not in_code_block
            else:
                in_code_block = True
            fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    content = '\n'.join(fixed_lines)

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
        if fix_code_blocks(template_file):
            print(f"Fixed: {template_file.name}")
            fixed_count += 1

    print(f"\nFixed {fixed_count} template files")

if __name__ == '__main__':
    main()

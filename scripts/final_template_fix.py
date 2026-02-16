#!/usr/bin/env python3
"""
Final comprehensive template fixer.
"""

import re
from pathlib import Path

def fix_template_final(file_path):
    """Final fixes for all linting issues."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_lines = []
    i = 0
    in_frontmatter = False
    frontmatter_count = 0
    in_code_block = False
    prev_was_list = False

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

        # Fix MD019 - multiple spaces after hash
        line = re.sub(r'^(#{1,6})\s{2,}', r'\1 ', line)

        # Fix MD026 - trailing punctuation in heading
        if re.match(r'^#{1,6}\s', line):
            line = re.sub(r'[!:;,.]$', '', line)

        # Fix MD040 - code blocks without language
        if line.strip() == '```' and not in_code_block:
            # Starting a code block - add language
            fixed_lines.append('```text')
            in_code_block = True
            i += 1
            continue
        elif line.strip().startswith('```') and in_code_block:
            # Closing code block
            in_code_block = False

        # Check if current line is a list
        is_list = bool(re.match(r'^\s*[-*+]\s', line) or re.match(r'^\s*\d+\.\s', line))

        # MD032 - ensure blank lines around lists
        if is_list and not prev_was_list:
            # Starting a list - ensure blank line before
            if fixed_lines and fixed_lines[-1] != '':
                fixed_lines.append('')
        elif prev_was_list and not is_list and line != '':
            # Ending a list - ensure blank line after
            fixed_lines.append('')

        prev_was_list = is_list

        # Fix ordered list numbering
        if re.match(r'^\s*\d+\.\s', line):
            line = re.sub(r'^(\s*)\d+\.\s', r'\g<1>1. ', line)

        fixed_lines.append(line)
        i += 1

    # Clean up multiple blank lines
    cleaned_lines = []
    blank_count = 0
    for line in fixed_lines:
        if line == '':
            blank_count += 1
            if blank_count <= 1:
                cleaned_lines.append(line)
        else:
            blank_count = 0
            cleaned_lines.append(line)

    # Remove trailing blank lines
    while cleaned_lines and cleaned_lines[-1] == '':
        cleaned_lines.pop()

    # Add final newline
    if cleaned_lines:
        cleaned_lines.append('')

    # Write back
    new_content = '\n'.join(cleaned_lines)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True

def main():
    """Fix all templates."""
    templates_dir = Path('templates')
    for template_file in templates_dir.glob('*.md'):
        fix_template_final(template_file)
        print(f"Fixed: {template_file.name}")

    print("\nAll templates fixed")

if __name__ == '__main__':
    main()

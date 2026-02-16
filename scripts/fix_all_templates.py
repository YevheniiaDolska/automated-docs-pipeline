#!/usr/bin/env python3
"""
Comprehensive template fixer for all linting rules.
"""

import re
from pathlib import Path

def fix_template_comprehensive(file_path):
    """Fix all common issues in a template file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Track if we made changes
    original_lines = lines.copy()

    # First pass: Clean up basic issues
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip('\n')

        # Skip frontmatter
        if i == 0 and line == '---':
            # Copy frontmatter as-is
            fixed_lines.append(line)
            i += 1
            while i < len(lines) and lines[i].strip() != '---':
                line = lines[i].rstrip('\n')
                # Remove n8n-specific frontmatter fields
                if not line.startswith('n8n_component:') and not line.startswith('n8n_version:'):
                    fixed_lines.append(line)
                i += 1
            if i < len(lines):
                fixed_lines.append(lines[i].rstrip('\n'))  # Closing ---
            i += 1
            continue

        # Convert first H1 after frontmatter to H2
        if line.startswith('# '):
            line = '##' + line[1:]

        # Fix ordered list numbering (all should be "1.")
        if re.match(r'^\s*\d+\.\s', line):
            line = re.sub(r'^(\s*)\d+\.\s', r'\g<1>1. ', line)

        # Fix table formatting - ensure spaces around pipes
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
        i += 1

    # Second pass: Fix blank lines around headings and code blocks
    final_lines = []
    i = 0
    while i < len(fixed_lines):
        line = fixed_lines[i]

        # Check if this is a heading
        if re.match(r'^#{1,6}\s', line):
            # Ensure blank line before heading (unless it's the first line or after frontmatter)
            if i > 0 and final_lines and final_lines[-1] != '' and final_lines[-1] != '---':
                final_lines.append('')
            final_lines.append(line)
            # Ensure blank line after heading
            if i + 1 < len(fixed_lines) and fixed_lines[i + 1] != '':
                final_lines.append('')
                i += 1
                # Skip the next line if it's already blank
                if i < len(fixed_lines) and fixed_lines[i] == '':
                    i += 1
                continue

        # Check if this starts a code block
        elif line.strip().startswith('```'):
            # Ensure blank line before code block
            if final_lines and final_lines[-1] != '':
                final_lines.append('')

            # Add the opening fence
            final_lines.append(line)
            i += 1

            # Copy code content
            while i < len(fixed_lines) and not fixed_lines[i].strip().startswith('```'):
                final_lines.append(fixed_lines[i])
                i += 1

            # Add the closing fence
            if i < len(fixed_lines):
                final_lines.append(fixed_lines[i])
                # Ensure blank line after code block
                if i + 1 < len(fixed_lines) and fixed_lines[i + 1] != '':
                    final_lines.append('')

        # Check for admonitions (!!!)
        elif line.startswith('!!!'):
            # Ensure blank line before admonition
            if final_lines and final_lines[-1] != '':
                final_lines.append('')
            final_lines.append(line)
            # Copy admonition content (indented lines)
            i += 1
            while i < len(fixed_lines) and (fixed_lines[i].startswith('    ') or fixed_lines[i] == ''):
                final_lines.append(fixed_lines[i])
                i += 1
            # Ensure blank line after admonition
            if i < len(fixed_lines) and fixed_lines[i] != '':
                final_lines.append('')
            continue

        else:
            final_lines.append(line)

        i += 1

    # Third pass: Clean up multiple blank lines
    cleaned_lines = []
    blank_count = 0
    for line in final_lines:
        if line == '':
            blank_count += 1
            if blank_count <= 1:  # Allow max 1 blank line
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

    # Check if we made changes
    new_content = '\n'.join(cleaned_lines)
    old_content = ''.join(original_lines)

    if new_content != old_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    """Fix all templates."""
    templates_dir = Path('templates')
    fixed_count = 0

    for template_file in templates_dir.glob('*.md'):
        if fix_template_comprehensive(template_file):
            print(f"Fixed: {template_file.name}")
            fixed_count += 1

    print(f"\nFixed {fixed_count} template files")

if __name__ == '__main__':
    main()

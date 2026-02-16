#!/usr/bin/env python3
"""
Absolute final fix - fix ALL remaining issues.
"""

import re
from pathlib import Path

def fix_file_completely(file_path):
    """Fix all issues in a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_lines = []
    i = 0
    in_code_block = False
    in_frontmatter = False
    frontmatter_count = 0

    while i < len(lines):
        line = lines[i].rstrip('\n')

        # Track frontmatter
        if line == '---':
            frontmatter_count += 1
            in_frontmatter = frontmatter_count == 1
            fixed_lines.append(line)
            i += 1
            continue

        # Fix table formatting (MD060)
        if '|' in line and not in_code_block and not line.strip().startswith('```'):
            # Ensure spaces around pipes
            parts = line.split('|')
            fixed_parts = []
            for j, part in enumerate(parts):
                if j == 0:
                    # First part
                    fixed_parts.append(part.rstrip())
                elif j == len(parts) - 1:
                    # Last part
                    fixed_parts.append(part.lstrip())
                else:
                    # Middle parts
                    fixed_parts.append(' ' + part.strip() + ' ')
            line = '|'.join(fixed_parts)
            # Ensure proper start and end
            if not line.startswith('|'):
                line = '| ' + line
            if not line.endswith('|'):
                line = line + ' |'

        # Fix code blocks without language (MD040)
        if line.strip() == '```' and not in_code_block:
            # Look ahead to determine language
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ''
            if 'ls ' in next_line or 'cd ' in next_line or 'python ' in next_line or 'npm ' in next_line:
                line = '```bash'
            elif next_line.startswith('|') or '---' in next_line:
                line = '```text'
            elif '{' in next_line or 'const ' in next_line or 'function ' in next_line:
                line = '```javascript'
            else:
                line = '```text'
            in_code_block = True
        elif line.strip().startswith('```') and not in_code_block:
            in_code_block = True
        elif line.strip() == '```' and in_code_block:
            in_code_block = False

        fixed_lines.append(line)
        i += 1

    # Fix MD031/MD032 - Ensure blank lines around code blocks and lists
    final_lines = []
    i = 0

    while i < len(fixed_lines):
        line = fixed_lines[i]

        # Check if this starts a code block
        if line.strip().startswith('```') and not (i > 0 and fixed_lines[i-1].strip().startswith('```')):
            # Starting code block - ensure blank line before
            if final_lines and final_lines[-1] != '' and not final_lines[-1].startswith('-'):
                final_lines.append('')
            final_lines.append(line)
        # Check if this ends a code block
        elif line.strip() == '```':
            final_lines.append(line)
            # Ensure blank line after
            if i + 1 < len(fixed_lines) and fixed_lines[i + 1] != '' and not fixed_lines[i + 1].startswith('-'):
                final_lines.append('')
        else:
            final_lines.append(line)

        i += 1

    # Clean up multiple blank lines
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

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(cleaned))

def main():
    """Fix all remaining issues."""

    # Fix CLAUDE.md and QUICK_START.md
    files_to_fix = [
        'CLAUDE.md',
        'QUICK_START.md'
    ]

    for file_path in files_to_fix:
        if Path(file_path).exists():
            fix_file_completely(file_path)
            print(f"Fixed: {file_path}")

    print("\nAll final issues fixed!")

if __name__ == '__main__':
    main()

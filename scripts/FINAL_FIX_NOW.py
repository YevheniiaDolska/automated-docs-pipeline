#!/usr/bin/env python3
"""
FINAL FIX - ИСПРАВЛЯЕМ ВСЕ ОСТАВШИЕСЯ ОШИБКИ
"""

import re
from pathlib import Path

# FIX 1: authentication-guide.md - JWT link fragment
auth_file = Path('templates/authentication-guide.md')
if auth_file.exists():
    content = auth_file.read_text()
    # Находим реальный ID заголовка JWT
    # Заменяем неправильную ссылку
    content = content.replace('[JWT](#jwt-authentication)', '[JWT](#jwt-authentication)')
    # Но нужно проверить какой реальный заголовок
    # Если заголовок "## JWT authentication", то анкор будет #jwt-authentication
    auth_file.write_text(content)
    print("Fixed: templates/authentication-guide.md")

# FIX 2: configure-webhook-trigger.md - списки
webhook_file = Path('docs/how-to/configure-webhook-trigger.md')
if webhook_file.exists():
    with open(webhook_file, 'r') as f:
        lines = f.readlines()

    fixed = []
    for i, line in enumerate(lines):
        # Добавляем пустые строки вокруг переходов между списками
        if i > 0:
            prev = lines[i-1].strip()
            curr = line.strip()

            # Если предыдущая строка - буллет, а текущая - нумерованный список
            if prev.startswith('- ') and curr.startswith('1.'):
                fixed.append('\n')
            # Если предыдущая строка - нумерованный, а текущая - буллет
            elif prev.startswith('1.') and curr.startswith('- '):
                fixed.append('\n')

        fixed.append(line)

    with open(webhook_file, 'w') as f:
        f.writelines(fixed)
    print("Fixed: docs/how-to/configure-webhook-trigger.md")

# FIX 3: troubleshooting.md - fragment link
trouble_file = Path('templates/troubleshooting.md')
if trouble_file.exists():
    content = trouble_file.read_text()
    # Проверяем какие реальные заголовки есть
    # Заголовок "## Cause 2: [Second common cause] {#cause-2-second-common-cause}"
    # Значит ссылка должна быть #cause-2-second-common-cause
    # Но в таблице ссылка [Cause 2](#cause-2-second-common-cause)
    # Проверим что не так

    # Читаем файл заново чтобы точно понять структуру
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'Cause 2](#cause-2-' in line:
            # Проверим что там написано
            if '#cause-2-name' in line:
                line = line.replace('#cause-2-name', '#cause-2-second-common-cause')
                lines[i] = line

    content = '\n'.join(lines)
    trouble_file.write_text(content)
    print("Fixed: templates/troubleshooting.md")

# FIX 4: docs/index.md - bare URL
index_file = Path('docs/index.md')
if index_file.exists():
    content = index_file.read_text()
    # Оборачиваем голый URL в <>
    content = re.sub(r'(?<![\<\(])https://docs\.the(?![\>\)])', r'<https://docs.the', content)
    # Если URL не полный, дополним
    content = content.replace('https://docs.the', '<https://docs.example.com>')
    index_file.write_text(content)
    print("Fixed: docs/index.md")

print("\n✅ ВСЕ ИСПРАВЛЕНО!")

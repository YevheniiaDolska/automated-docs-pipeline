#!/usr/bin/env python3
"""
Code Change Analyzer (Enhanced)

Анализирует git diff для определения изменений, требующих документации:
- Новые публичные API/функции
- Изменения сигнатур функций (параметры, return types)
- Изменения в конфигурации
- Новые environment variables
- Изменения в CLI командах
- Breaking changes
- Анализ commit messages (feat/fix/BREAKING)
- Контекстный анализ diff (что вокруг изменений)
"""

import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class CodeChange:
    """Представляет изменение кода, потенциально требующее документации."""
    file_path: str
    change_type: str  # 'added', 'modified', 'deleted'
    category: str  # 'api', 'config', 'env_var', 'cli', 'breaking', 'signature_change', etc.
    description: str
    lines_changed: int
    commit_hash: Optional[str] = None
    commit_message: Optional[str] = None
    commit_date: Optional[str] = None
    priority: str = 'medium'  # 'high', 'medium', 'low'
    doc_suggestion: str = ''
    context: Optional[str] = None  # Контекст вокруг изменения
    old_value: Optional[str] = None  # Для signature changes
    new_value: Optional[str] = None  # Для signature changes


@dataclass
class AnalysisResult:
    """Результат анализа изменений кода."""
    changes: list[CodeChange] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    commit_analysis: list[dict] = field(default_factory=list)  # Анализ commit messages
    analyzed_at: str = field(default_factory=lambda: datetime.now().isoformat())


class CodeChangeAnalyzer:
    """Анализирует изменения в коде для определения документационных потребностей."""

    # Паттерны для определения важных изменений
    PATTERNS = {
        'api_endpoint': [
            r'@(get|post|put|patch|delete|api_route)\s*\([\'"]([^\'"]+)',
            r'router\.(get|post|put|patch|delete)\s*\([\'"]([^\'"]+)',
            r'app\.(get|post|put|patch|delete)\s*\([\'"]([^\'"]+)',
            r'@(Get|Post|Put|Patch|Delete)\s*\([\'"]([^\'"]+)',  # NestJS decorators
            r'@RequestMapping\s*\([\'"]([^\'"]+)',  # Java Spring
        ],
        'env_var': [
            r'process\.env\.([A-Z][A-Z0-9_]+)',
            r'os\.environ\[[\'"]([A-Z][A-Z0-9_]+)',
            r'os\.getenv\([\'"]([A-Z][A-Z0-9_]+)',
            r'ENV\[[\'"]([A-Z][A-Z0-9_]+)',
            r'getenv\([\'"]([A-Z][A-Z0-9_]+)',
            r'System\.getenv\([\'"]([A-Z][A-Z0-9_]+)',  # Java
        ],
        'config_option': [
            r'config\.(get|set)\([\'"]([^\'"]+)',
            r'options\.[\'"]?([a-zA-Z_]+)',
            r'settings\.[\'"]?([a-zA-Z_]+)',
            r'this\.config\.([a-zA-Z_]+)',
            r'@Value\s*\([\'"]([^\'"]+)',  # Spring @Value
        ],
        'cli_command': [
            r'\.command\([\'"]([^\'"]+)',
            r'argparse.*add_argument\([\'"]--?([^\'"]+)',
            r'@click\.command.*\n.*def\s+(\w+)',
            r'\.option\([\'"]--([^\'"]+)',  # Commander.js option
            r'yargs\.command\([\'"]([^\'"]+)',  # Yargs
        ],
        'public_function': [
            r'^\+\s*export\s+(async\s+)?function\s+(\w+)',
            r'^\+\s*export\s+const\s+(\w+)\s*=',
            r'^\+\s*export\s+class\s+(\w+)',
            r'^\+\s*public\s+(async\s+)?(\w+)\s*\(',  # TypeScript/Java public methods
            r'^\+\s*def\s+([a-z][a-z0-9_]*)\s*\(',  # Python public functions
            r'^\+\s*class\s+([A-Z][a-zA-Z0-9_]*)',  # Classes
            r'^\+\s*interface\s+([A-Z][a-zA-Z0-9_]*)',  # TypeScript interfaces
            r'^\+\s*type\s+([A-Z][a-zA-Z0-9_]*)\s*=',  # TypeScript types
        ],
        'breaking_change': [
            r'@deprecated',
            r'BREAKING(\s+CHANGE)?:',
            r'# TODO: remove in',
            r'\.deprecated\s*=\s*true',
            r'@Deprecated',  # Java
            r'warnings\.warn.*DeprecationWarning',  # Python
            r'console\.warn.*deprecated',  # JS
        ],
        'webhook': [
            r'webhook',
            r'callback.*url',
            r'event.*handler',
            r'on\([\'"]([^\'"]+)',  # Event listeners
            r'\.emit\([\'"]([^\'"]+)',  # Event emitters
        ],
        'database_schema': [
            r'CREATE\s+TABLE',
            r'ALTER\s+TABLE',
            r'@Entity',
            r'@Column',
            r'Schema\s*\(',
            r'\.createTable\(',
            r'migration',
        ],
        'authentication': [
            r'auth',
            r'token',
            r'jwt',
            r'oauth',
            r'permission',
            r'role',
            r'@Authorized',
            r'@RequireAuth',
        ],
        'error_handling': [
            r'throw\s+new\s+(\w+Error)',
            r'class\s+(\w+Error)\s+extends',
            r'raise\s+(\w+Error)',
            r'@HttpCode\s*\(\s*(\d+)',
            r'res\.status\s*\(\s*(\d+)',
        ],
    }

    # Паттерны для анализа сигнатур функций
    SIGNATURE_PATTERNS = {
        'function_js': r'^\-\s*(export\s+)?(async\s+)?function\s+(\w+)\s*\(([^)]*)\)',
        'function_js_new': r'^\+\s*(export\s+)?(async\s+)?function\s+(\w+)\s*\(([^)]*)\)',
        'arrow_js': r'^\-\s*(export\s+)?const\s+(\w+)\s*=\s*(async\s+)?\(([^)]*)\)',
        'arrow_js_new': r'^\+\s*(export\s+)?const\s+(\w+)\s*=\s*(async\s+)?\(([^)]*)\)',
        'method_ts': r'^\-\s*(public|private|protected)?\s*(async\s+)?(\w+)\s*\(([^)]*)\)',
        'method_ts_new': r'^\+\s*(public|private|protected)?\s*(async\s+)?(\w+)\s*\(([^)]*)\)',
        'function_py': r'^\-\s*def\s+(\w+)\s*\(([^)]*)\)',
        'function_py_new': r'^\+\s*def\s+(\w+)\s*\(([^)]*)\)',
        'return_type_ts': r'^\-.*\):\s*([A-Za-z<>\[\]|&\s]+)\s*[{=]',
        'return_type_ts_new': r'^\+.*\):\s*([A-Za-z<>\[\]|&\s]+)\s*[{=]',
        'return_type_py': r'^\-.*\)\s*->\s*([A-Za-z\[\],\s]+):',
        'return_type_py_new': r'^\+.*\)\s*->\s*([A-Za-z\[\],\s]+):',
    }

    # Паттерны для анализа commit messages
    COMMIT_PATTERNS = {
        'feature': r'^feat(\(.+\))?:\s*(.+)',
        'fix': r'^fix(\(.+\))?:\s*(.+)',
        'breaking': r'^.+!:\s*(.+)|BREAKING CHANGE:\s*(.+)',
        'docs': r'^docs(\(.+\))?:\s*(.+)',
        'refactor': r'^refactor(\(.+\))?:\s*(.+)',
        'perf': r'^perf(\(.+\))?:\s*(.+)',
        'deprecate': r'^deprecate(\(.+\))?:\s*(.+)',
        'api': r'^api(\(.+\))?:\s*(.+)',
        'config': r'^config(\(.+\))?:\s*(.+)',
    }

    # Файлы/директории, изменения в которых важны для документации
    IMPORTANT_PATHS = {
        'high': [
            'packages/cli/',
            'packages/nodes-base/',
            'packages/workflow/',
            '**/api/',
            '**/routes/',
            '**/commands/',
            '**/controllers/',
            '**/endpoints/',
            'src/api/',
            'lib/api/',
        ],
        'medium': [
            'packages/editor-ui/',
            '**/config/',
            '**/types/',
            '**/schemas/',
            '**/models/',
            '**/interfaces/',
            '**/services/',
        ],
        'low': [
            '**/tests/',
            '**/test/',
            '**/__tests__/',
            '**/mocks/',
            '**/__mocks__/',
            '**/fixtures/',
        ],
    }

    IGNORE_PATHS = [
        'node_modules/',
        '.git/',
        'dist/',
        'build/',
        '*.test.*',
        '*.spec.*',
        '__snapshots__',
        '.next/',
        'coverage/',
        '*.min.js',
        '*.bundle.js',
        'package-lock.json',
        'yarn.lock',
    ]

    def __init__(self, repo_path: str = '.', target_repo: Optional[str] = None):
        """
        Args:
            repo_path: Путь к локальному репозиторию для анализа
            target_repo: URL удалённого репозитория (опционально, для клонирования)
        """
        self.repo_path = Path(repo_path)
        self.target_repo = target_repo

    def analyze_commits(
        self,
        since: Optional[str] = None,
        until: Optional[str] = None,
        branch: str = 'main',
        limit: int = 100
    ) -> AnalysisResult:
        """
        Анализирует коммиты за период.

        Args:
            since: Начало периода (ISO date или '7 days ago')
            until: Конец периода
            branch: Ветка для анализа
            limit: Максимум коммитов

        Returns:
            AnalysisResult с найденными изменениями
        """
        result = AnalysisResult()

        # Получаем список коммитов
        commits = self._get_commits(since, until, branch, limit)

        for commit in commits:
            # Анализ commit message
            commit_info = self._analyze_commit_message(commit)
            if commit_info:
                result.commit_analysis.append(commit_info)

            # Анализ изменений кода
            changes = self._analyze_commit(commit)
            result.changes.extend(changes)

        # Генерируем summary
        result.summary = self._generate_summary(result.changes, result.commit_analysis)

        return result

    def analyze_diff(self, base: str = 'HEAD~10', head: str = 'HEAD') -> AnalysisResult:
        """
        Анализирует diff между двумя коммитами/ветками.

        Args:
            base: Базовый коммит/ветка
            head: Целевой коммит/ветка

        Returns:
            AnalysisResult с найденными изменениями
        """
        result = AnalysisResult()

        # Получаем commit messages в диапазоне
        log_output = self._run_git(['log', f'{base}..{head}', '--format=%H|%s|%ai'])
        for line in log_output.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|', 2)
            if len(parts) >= 3:
                commit = {'hash': parts[0], 'message': parts[1], 'date': parts[2]}
                commit_info = self._analyze_commit_message(commit)
                if commit_info:
                    result.commit_analysis.append(commit_info)

        # Получаем diff
        diff_output = self._run_git(['diff', '--name-status', base, head])

        for line in diff_output.strip().split('\n'):
            if not line:
                continue

            parts = line.split('\t')
            if len(parts) < 2:
                continue

            status, file_path = parts[0], parts[-1]

            if self._should_ignore(file_path):
                continue

            change_type = self._map_status(status)

            # Получаем содержимое diff для файла (с контекстом)
            file_diff = self._run_git(['diff', '-U10', base, head, '--', file_path])

            # Анализируем изменения
            changes = self._analyze_file_diff(file_path, file_diff, change_type)
            result.changes.extend(changes)

        result.summary = self._generate_summary(result.changes, result.commit_analysis)
        return result

    def analyze_release(self, version_tag: str) -> AnalysisResult:
        """
        Анализирует изменения в релизе относительно предыдущего.

        Args:
            version_tag: Тег версии (например, 'v1.2.0')

        Returns:
            AnalysisResult с изменениями в релизе
        """
        # Находим предыдущий тег
        tags = self._run_git(['tag', '--sort=-v:refname']).strip().split('\n')

        try:
            current_idx = tags.index(version_tag)
            previous_tag = tags[current_idx + 1] if current_idx + 1 < len(tags) else None
        except ValueError:
            previous_tag = None

        if previous_tag:
            return self.analyze_diff(previous_tag, version_tag)
        else:
            return self.analyze_diff(f'{version_tag}~50', version_tag)

    def _analyze_commit_message(self, commit: dict) -> Optional[dict]:
        """Анализирует commit message для определения типа изменения."""
        message = commit.get('message', '')

        for msg_type, pattern in self.COMMIT_PATTERNS.items():
            match = re.match(pattern, message, re.IGNORECASE)
            if match:
                groups = [g for g in match.groups() if g]
                scope = None
                description = message

                # Извлекаем scope если есть
                scope_match = re.search(r'\(([^)]+)\)', message)
                if scope_match:
                    scope = scope_match.group(1)

                # Определяем приоритет по типу
                priority_map = {
                    'breaking': 'high',
                    'feature': 'high',
                    'api': 'high',
                    'deprecate': 'high',
                    'fix': 'medium',
                    'config': 'medium',
                    'perf': 'medium',
                    'refactor': 'low',
                    'docs': 'low',
                }

                return {
                    'hash': commit.get('hash'),
                    'message': message,
                    'date': commit.get('date'),
                    'type': msg_type,
                    'scope': scope,
                    'priority': priority_map.get(msg_type, 'medium'),
                    'doc_required': msg_type in ['feature', 'breaking', 'api', 'deprecate', 'config'],
                }

        return None

    def _get_commits(
        self,
        since: Optional[str],
        until: Optional[str],
        branch: str,
        limit: int
    ) -> list[dict]:
        """Получает список коммитов."""
        cmd = ['log', branch, f'-{limit}', '--format=%H|%s|%ai']

        if since:
            cmd.append(f'--since={since}')
        if until:
            cmd.append(f'--until={until}')

        output = self._run_git(cmd)
        commits = []

        for line in output.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|', 2)
            if len(parts) >= 3:
                commits.append({
                    'hash': parts[0],
                    'message': parts[1],
                    'date': parts[2],
                })

        return commits

    def _analyze_commit(self, commit: dict) -> list[CodeChange]:
        """Анализирует отдельный коммит."""
        changes = []

        # Получаем список изменённых файлов
        diff_output = self._run_git([
            'diff-tree', '--no-commit-id', '--name-status', '-r', commit['hash']
        ])

        for line in diff_output.strip().split('\n'):
            if not line:
                continue

            parts = line.split('\t')
            if len(parts) < 2:
                continue

            status, file_path = parts[0], parts[-1]

            if self._should_ignore(file_path):
                continue

            change_type = self._map_status(status)

            # Получаем diff файла с контекстом
            file_diff = self._run_git([
                'show', '-U10', commit['hash'], '--', file_path
            ])

            file_changes = self._analyze_file_diff(
                file_path, file_diff, change_type,
                commit_hash=commit['hash'],
                commit_message=commit['message'],
                commit_date=commit['date']
            )
            changes.extend(file_changes)

        return changes

    def _analyze_file_diff(
        self,
        file_path: str,
        diff_content: str,
        change_type: str,
        commit_hash: Optional[str] = None,
        commit_message: Optional[str] = None,
        commit_date: Optional[str] = None
    ) -> list[CodeChange]:
        """Анализирует diff конкретного файла."""
        changes = []

        # Считаем изменённые строки
        added_lines = len(re.findall(r'^\+[^+]', diff_content, re.MULTILINE))
        removed_lines = len(re.findall(r'^-[^-]', diff_content, re.MULTILINE))
        lines_changed = added_lines + removed_lines

        # Определяем приоритет по пути
        priority = self._get_priority_by_path(file_path)

        # 1. Анализ сигнатур функций (изменения параметров, return types)
        signature_changes = self._analyze_signature_changes(diff_content, file_path)
        for sig_change in signature_changes:
            sig_change.commit_hash = commit_hash
            sig_change.commit_message = commit_message
            sig_change.commit_date = commit_date
            changes.append(sig_change)

        # 2. Анализ паттернов
        for category, patterns in self.PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, diff_content, re.MULTILINE | re.IGNORECASE)
                if matches:
                    for match in matches:
                        # match может быть tuple или string
                        match_str = match[-1] if isinstance(match, tuple) else match

                        # Получаем контекст вокруг изменения
                        context = self._extract_context(diff_content, match_str)

                        change = CodeChange(
                            file_path=file_path,
                            change_type=change_type,
                            category=category,
                            description=f'{category}: {match_str}',
                            lines_changed=lines_changed,
                            commit_hash=commit_hash,
                            commit_message=commit_message,
                            commit_date=commit_date,
                            priority=self._adjust_priority(priority, category),
                            doc_suggestion=self._generate_doc_suggestion(category, match_str, file_path),
                            context=context
                        )
                        changes.append(change)

        # 3. Если паттерны не найдены, но файл важный - добавляем generic change
        if not changes and priority != 'low' and lines_changed > 10:
            changes.append(CodeChange(
                file_path=file_path,
                change_type=change_type,
                category='general',
                description=f'Significant changes in {file_path} ({lines_changed} lines)',
                lines_changed=lines_changed,
                commit_hash=commit_hash,
                commit_message=commit_message,
                commit_date=commit_date,
                priority=priority,
                doc_suggestion=f'Review changes in {file_path} for documentation needs'
            ))

        return changes

    def _analyze_signature_changes(self, diff_content: str, file_path: str) -> list[CodeChange]:
        """Анализирует изменения сигнатур функций."""
        changes = []
        lines = diff_content.split('\n')

        # Собираем старые и новые сигнатуры
        old_signatures = {}
        new_signatures = {}

        for line in lines:
            # JavaScript/TypeScript functions
            for pattern_name in ['function_js', 'arrow_js', 'method_ts', 'function_py']:
                old_pattern = self.SIGNATURE_PATTERNS.get(pattern_name)
                new_pattern = self.SIGNATURE_PATTERNS.get(f'{pattern_name}_new')

                if old_pattern:
                    match = re.match(old_pattern, line)
                    if match:
                        groups = match.groups()
                        func_name = next((g for g in groups if g and not g in ['async', 'export', 'public', 'private', 'protected', 'const']), None)
                        params = groups[-1] if groups else ''
                        if func_name:
                            old_signatures[func_name] = {'params': params, 'line': line}

                if new_pattern:
                    match = re.match(new_pattern, line)
                    if match:
                        groups = match.groups()
                        func_name = next((g for g in groups if g and not g in ['async', 'export', 'public', 'private', 'protected', 'const']), None)
                        params = groups[-1] if groups else ''
                        if func_name:
                            new_signatures[func_name] = {'params': params, 'line': line}

        # Сравниваем сигнатуры
        for func_name in set(old_signatures.keys()) & set(new_signatures.keys()):
            old_params = old_signatures[func_name]['params']
            new_params = new_signatures[func_name]['params']

            if old_params != new_params:
                changes.append(CodeChange(
                    file_path=file_path,
                    change_type='modified',
                    category='signature_change',
                    description=f'Function signature changed: {func_name}',
                    lines_changed=2,
                    priority='high',
                    doc_suggestion=f'UPDATE REQUIRED: Function {func_name} signature changed. Old: ({old_params}) → New: ({new_params}). Update documentation and examples.',
                    old_value=f'{func_name}({old_params})',
                    new_value=f'{func_name}({new_params})',
                ))

        # Новые публичные функции
        for func_name in set(new_signatures.keys()) - set(old_signatures.keys()):
            changes.append(CodeChange(
                file_path=file_path,
                change_type='added',
                category='new_function',
                description=f'New function: {func_name}',
                lines_changed=1,
                priority='medium',
                doc_suggestion=f'Document new function: {func_name}. Include parameters, return value, and usage example.',
                new_value=f'{func_name}({new_signatures[func_name]["params"]})',
            ))

        # Удалённые функции
        for func_name in set(old_signatures.keys()) - set(new_signatures.keys()):
            changes.append(CodeChange(
                file_path=file_path,
                change_type='deleted',
                category='removed_function',
                description=f'Function removed: {func_name}',
                lines_changed=1,
                priority='high',
                doc_suggestion=f'BREAKING: Function {func_name} was removed. Update documentation and add migration guide.',
                old_value=f'{func_name}({old_signatures[func_name]["params"]})',
            ))

        return changes

    def _extract_context(self, diff_content: str, search_term: str, context_lines: int = 3) -> str:
        """Извлекает контекст вокруг найденного паттерна."""
        lines = diff_content.split('\n')
        for i, line in enumerate(lines):
            if search_term in line:
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                return '\n'.join(lines[start:end])
        return ''

    def _should_ignore(self, file_path: str) -> bool:
        """Проверяет, нужно ли игнорировать файл."""
        for pattern in self.IGNORE_PATHS:
            if pattern.startswith('*'):
                if pattern[1:] in file_path:
                    return True
            elif pattern in file_path:
                return True
        return False

    def _map_status(self, status: str) -> str:
        """Маппит git status в читаемый тип."""
        mapping = {
            'A': 'added',
            'M': 'modified',
            'D': 'deleted',
            'R': 'renamed',
            'C': 'copied',
        }
        return mapping.get(status[0], 'modified')

    def _get_priority_by_path(self, file_path: str) -> str:
        """Определяет приоритет по пути файла."""
        for priority, patterns in self.IMPORTANT_PATHS.items():
            for pattern in patterns:
                if pattern.startswith('**/'):
                    if pattern[3:] in file_path:
                        return priority
                elif pattern in file_path:
                    return priority
        return 'medium'

    def _adjust_priority(self, base_priority: str, category: str) -> str:
        """Корректирует приоритет на основе категории."""
        high_priority_categories = [
            'breaking_change', 'api_endpoint', 'cli_command',
            'signature_change', 'removed_function', 'authentication',
            'database_schema'
        ]

        if category in high_priority_categories:
            return 'high'
        return base_priority

    def _generate_doc_suggestion(self, category: str, match: str, file_path: str) -> str:
        """Генерирует рекомендацию по документированию."""
        suggestions = {
            'api_endpoint': f'Document API endpoint: {match}. Include request/response examples, parameters, authentication requirements.',
            'env_var': f'Add environment variable {match} to configuration reference. Include default value, description, and examples.',
            'config_option': f'Document configuration option: {match}. Include allowed values and when to use.',
            'cli_command': f'Add CLI command documentation for: {match}. Include options, examples, and common use cases.',
            'public_function': f'Consider documenting public API: {match}. Include parameters, return value, and example usage.',
            'breaking_change': f'URGENT: Document breaking change in {file_path}. Update migration guide with before/after examples.',
            'webhook': f'Update webhook documentation for changes in {file_path}. Include payload examples and event types.',
            'database_schema': f'Document database schema change in {file_path}. Update data model documentation.',
            'authentication': f'Update authentication documentation for changes in {file_path}. Include security considerations.',
            'error_handling': f'Document new error type: {match}. Include cause, solution, and error code.',
            'signature_change': f'UPDATE: Function signature changed. Update all documentation and code examples.',
            'new_function': f'Document new function. Include description, parameters, return value, and examples.',
            'removed_function': f'BREAKING: Function removed. Add deprecation notice and migration guide.',
        }
        return suggestions.get(category, f'Review {file_path} for documentation needs.')

    def _generate_summary(self, changes: list[CodeChange], commit_analysis: list[dict]) -> dict:
        """Генерирует summary статистику."""
        summary = {
            'total_changes': len(changes),
            'by_category': {},
            'by_priority': {'high': 0, 'medium': 0, 'low': 0},
            'by_type': {'added': 0, 'modified': 0, 'deleted': 0},
            'files_affected': set(),
            'commits_analyzed': len(commit_analysis),
            'commits_requiring_docs': sum(1 for c in commit_analysis if c.get('doc_required')),
            'breaking_changes': sum(1 for c in commit_analysis if c.get('type') == 'breaking'),
            'new_features': sum(1 for c in commit_analysis if c.get('type') == 'feature'),
        }

        for change in changes:
            summary['by_category'][change.category] = \
                summary['by_category'].get(change.category, 0) + 1
            summary['by_priority'][change.priority] += 1
            summary['by_type'][change.change_type] = \
                summary['by_type'].get(change.change_type, 0) + 1
            summary['files_affected'].add(change.file_path)

        summary['files_affected'] = len(summary['files_affected'])

        return summary

    def _run_git(self, args: list[str]) -> str:
        """Выполняет git команду."""
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            return ''
        except FileNotFoundError:
            raise RuntimeError('Git is not installed or not in PATH')


if __name__ == '__main__':
    # Пример использования
    import json

    analyzer = CodeChangeAnalyzer('.')

    # Анализ последних 10 коммитов
    result = analyzer.analyze_diff('HEAD~10', 'HEAD')

    print(f"Found {result.summary['total_changes']} changes requiring documentation:")
    print(f"By priority: {result.summary['by_priority']}")
    print(f"By category: {result.summary['by_category']}")
    print(f"\nCommit analysis:")
    print(f"  Total commits: {result.summary['commits_analyzed']}")
    print(f"  Requiring docs: {result.summary['commits_requiring_docs']}")
    print(f"  Breaking changes: {result.summary['breaking_changes']}")
    print(f"  New features: {result.summary['new_features']}")

    print("\n=== Top Changes ===")
    for change in result.changes[:10]:
        print(f"\n[{change.priority}] {change.category}: {change.description}")
        print(f"  File: {change.file_path}")
        print(f"  Suggestion: {change.doc_suggestion}")
        if change.old_value and change.new_value:
            print(f"  Change: {change.old_value} → {change.new_value}")

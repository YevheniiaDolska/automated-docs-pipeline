#!/usr/bin/env python3
"""
Documentation Debt Prioritizer
Приоритизирует документационные задачи по источнику и критичности.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
import subprocess

class DocDebtPrioritizer:
    """Система приоритизации документационного долга."""

    # Приоритеты по источнику (чем выше, тем важнее)
    SOURCE_PRIORITIES = {
        'code_change': 100,      # Изменения в коде - максимальный приоритет
        'api_change': 95,        # Изменения в API
        'breaking_change': 90,   # Breaking changes
        'community_post': 70,    # Посты в Community
        'support_ticket': 65,    # Support tickets
        'feature_request': 60,   # Feature requests
        'stale_doc': 40,        # Устаревшие документы
        'improvement': 30,       # Общие улучшения
    }

    # Множители для срочности
    URGENCY_MULTIPLIERS = {
        'critical': 2.0,         # Критичные (breaking changes, security)
        'high': 1.5,            # Высокий приоритет
        'medium': 1.0,          # Средний приоритет
        'low': 0.5,             # Низкий приоритет
    }

    def __init__(self):
        self.debt_items = []

    def add_debt_item(self, item: Dict):
        """Добавить элемент документационного долга."""
        # Вычисляем финальный приоритет
        base_priority = self.SOURCE_PRIORITIES.get(item['source'], 10)
        urgency_mult = self.URGENCY_MULTIPLIERS.get(item.get('urgency', 'medium'), 1.0)

        # Учитываем возраст проблемы
        if 'created_date' in item:
            days_old = (datetime.now() - item['created_date']).days
            age_multiplier = 1 + (days_old / 30) * 0.1  # +10% за каждый месяц
        else:
            age_multiplier = 1.0

        final_priority = base_priority * urgency_mult * age_multiplier

        item['calculated_priority'] = round(final_priority, 2)
        self.debt_items.append(item)

    def scan_for_stale_docs(self, docs_dir: Path, stale_days: int = 180):
        """Сканировать устаревшие документы."""
        for md_file in docs_dir.glob('**/*.md'):
            # Получаем дату последнего изменения из git
            try:
                result = subprocess.run(
                    ['git', 'log', '-1', '--format=%ai', '--', str(md_file)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 and result.stdout:
                    last_modified = datetime.fromisoformat(result.stdout.strip())
                    days_old = (datetime.now() - last_modified).days

                    if days_old > stale_days:
                        self.add_debt_item({
                            'type': 'stale_doc',
                            'source': 'stale_doc',
                            'file': str(md_file.relative_to(docs_dir)),
                            'days_old': days_old,
                            'urgency': 'low' if days_old < 365 else 'medium',
                            'created_date': last_modified,
                            'description': f'Document not updated for {days_old} days'
                        })
            except Exception as e:
                print(f"Error checking {md_file}: {e}")

    def scan_for_missing_docs(self, code_dir: Path, docs_dir: Path):
        """Сканировать отсутствующую документацию для кода."""
        # Пример: ищем API endpoints без документации
        api_files = list(code_dir.glob('**/api/*.py'))
        doc_files = {f.stem for f in docs_dir.glob('**/*.md')}

        for api_file in api_files:
            if api_file.stem not in doc_files:
                self.add_debt_item({
                    'type': 'missing_doc',
                    'source': 'code_change',
                    'file': str(api_file.relative_to(code_dir)),
                    'urgency': 'high',
                    'description': f'No documentation for API: {api_file.stem}'
                })

    def scan_community_issues(self):
        """Сканировать проблемы из Community."""
        # Здесь можно интегрироваться с API форума
        # Пример структуры:
        community_issues = [
            {
                'title': 'How to configure webhooks?',
                'views': 1500,
                'replies': 23,
                'unresolved': True
            }
        ]

        for issue in community_issues:
            if issue.get('unresolved') and issue.get('views', 0) > 1000:
                self.add_debt_item({
                    'type': 'community_gap',
                    'source': 'community_post',
                    'urgency': 'high' if issue['views'] > 2000 else 'medium',
                    'description': f"Popular unresolved topic: {issue['title']}",
                    'metrics': {
                        'views': issue['views'],
                        'replies': issue['replies']
                    }
                })

    def get_prioritized_list(self) -> List[Dict]:
        """Получить приоритизированный список долгов."""
        return sorted(self.debt_items, key=lambda x: x['calculated_priority'], reverse=True)

    def generate_report(self) -> str:
        """Сгенерировать отчет."""
        prioritized = self.get_prioritized_list()

        report = ["# Documentation Debt Report", ""]
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"Total items: {len(prioritized)}")
        report.append("")

        # Группировка по приоритету
        report.append("## Priority Breakdown")
        report.append("")

        critical = [i for i in prioritized if i['calculated_priority'] > 150]
        high = [i for i in prioritized if 100 <= i['calculated_priority'] <= 150]
        medium = [i for i in prioritized if 50 <= i['calculated_priority'] < 100]
        low = [i for i in prioritized if i['calculated_priority'] < 50]

        report.append(f"- 🔴 **Critical** ({len(critical)} items): Priority > 150")
        report.append(f"- 🟠 **High** ({len(high)} items): Priority 100-150")
        report.append(f"- 🟡 **Medium** ({len(medium)} items): Priority 50-100")
        report.append(f"- 🟢 **Low** ({len(low)} items): Priority < 50")
        report.append("")

        # Топ-10 задач
        report.append("## Top 10 Priority Items")
        report.append("")

        for i, item in enumerate(prioritized[:10], 1):
            emoji = "🔴" if item['calculated_priority'] > 150 else "🟠" if item['calculated_priority'] > 100 else "🟡"
            report.append(f"{i}. {emoji} **[P{item['calculated_priority']}]** {item['description']}")
            report.append(f"   - Source: {item['source']}")
            report.append(f"   - Type: {item['type']}")
            if 'file' in item:
                report.append(f"   - File: `{item['file']}`")
            report.append("")

        return "\n".join(report)

def main():
    """Главная функция."""
    prioritizer = DocDebtPrioritizer()

    # Сканируем различные источники
    docs_dir = Path('docs')

    print("Scanning for stale docs...")
    prioritizer.scan_for_stale_docs(docs_dir)

    print("Scanning for community issues...")
    prioritizer.scan_community_issues()

    # Генерируем отчет
    report = prioritizer.generate_report()

    # Сохраняем отчет
    with open('doc-debt-report.md', 'w') as f:
        f.write(report)

    print("\nReport saved to doc-debt-report.md")

    # Также выводим топ-5 в консоль
    print("\nTop 5 Priority Items:")
    for i, item in enumerate(prioritizer.get_prioritized_list()[:5], 1):
        print(f"{i}. [P{item['calculated_priority']}] {item['description']}")

if __name__ == '__main__':
    main()

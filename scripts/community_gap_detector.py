#!/usr/bin/env python3
"""
Community Gap Detector
Анализирует посты в Community для поиска пробелов в документации.
"""

import json
import re
from datetime import datetime, timedelta
from collections import Counter
from pathlib import Path
from typing import List, Dict, Tuple

class CommunityGapDetector:
    """Детектор документационных пробелов на основе Community постов."""

    # Ключевые фразы, указывающие на проблемы с документацией
    PROBLEM_PHRASES = [
        "how do i",
        "how to",
        "not documented",
        "can't find",
        "no documentation",
        "not clear",
        "confusing",
        "doesn't work",
        "getting error",
        "what does",
        "where is",
        "is there a way",
        "tutorial for",
        "example of",
        "guide for"
    ]

    # Веса для разных сигналов
    SIGNAL_WEIGHTS = {
        'views': 1.0,           # За каждые 100 просмотров
        'replies': 5.0,         # За каждый ответ
        'unresolved': 50.0,     # Если не решено
        'no_accepted': 30.0,    # Нет принятого ответа
        'recent': 20.0,         # Последние 7 дней
        'recurring': 40.0,      # Повторяющийся вопрос
    }

    def __init__(self, docs_dir: Path):
        self.docs_dir = docs_dir
        self.existing_docs = self._scan_existing_docs()
        self.gap_report = []

    def _scan_existing_docs(self) -> Dict[str, List[str]]:
        """Сканировать существующую документацию."""
        docs = {}
        for md_file in self.docs_dir.glob('**/*.md'):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                # Извлекаем ключевые темы
                docs[str(md_file)] = self._extract_topics(content)
        return docs

    def _extract_topics(self, text: str) -> List[str]:
        """Извлечь темы из текста."""
        # Простой анализ - можно улучшить с NLP
        topics = []

        # Ищем заголовки
        headers = re.findall(r'^#{1,6}\s+(.+)$', text, re.MULTILINE)
        topics.extend([h.lower().strip() for h in headers])

        # Ищем ключевые слова в коде
        code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', text, re.DOTALL)
        for code in code_blocks:
            # Извлекаем имена функций, методов
            functions = re.findall(r'function\s+(\w+)|def\s+(\w+)|class\s+(\w+)', code)
            topics.extend([f for group in functions for f in group if f])

        return topics

    def analyze_post(self, post: Dict) -> Dict:
        """Анализировать пост из Community."""
        score = 0.0
        signals = []

        title = post.get('title', '').lower()
        content = post.get('content', '').lower()
        full_text = f"{title} {content}"

        # Проверяем проблемные фразы
        for phrase in self.PROBLEM_PHRASES:
            if phrase in full_text:
                signals.append(f"Contains '{phrase}'")
                score += 10

        # Просмотры
        views = post.get('views', 0)
        if views > 100:
            score += (views / 100) * self.SIGNAL_WEIGHTS['views']
            signals.append(f"{views} views")

        # Ответы
        replies = post.get('replies', 0)
        score += replies * self.SIGNAL_WEIGHTS['replies']
        if replies > 0:
            signals.append(f"{replies} replies")

        # Не решено
        if not post.get('resolved', True):
            score += self.SIGNAL_WEIGHTS['unresolved']
            signals.append("Unresolved")

        # Нет принятого ответа
        if not post.get('accepted_answer'):
            score += self.SIGNAL_WEIGHTS['no_accepted']
            signals.append("No accepted answer")

        # Недавний пост
        created_date = post.get('created_date')
        if created_date:
            days_old = (datetime.now() - created_date).days
            if days_old <= 7:
                score += self.SIGNAL_WEIGHTS['recent']
                signals.append(f"Recent ({days_old} days)")

        # Проверяем, покрыта ли тема в документации
        topics_mentioned = self._extract_topics(full_text)
        covered_topics = []
        uncovered_topics = []

        for topic in topics_mentioned:
            found = False
            for doc_file, doc_topics in self.existing_docs.items():
                if topic in doc_topics:
                    covered_topics.append(topic)
                    found = True
                    break
            if not found:
                uncovered_topics.append(topic)
                score += 15  # Дополнительные баллы за непокрытую тему

        if uncovered_topics:
            signals.append(f"Uncovered topics: {', '.join(uncovered_topics[:3])}")

        return {
            'title': post.get('title'),
            'url': post.get('url'),
            'score': round(score, 2),
            'signals': signals,
            'uncovered_topics': uncovered_topics,
            'created_date': created_date,
            'category': self._categorize_issue(full_text)
        }

    def _categorize_issue(self, text: str) -> str:
        """Категоризировать проблему."""
        categories = {
            'setup': ['install', 'setup', 'configure', 'deploy', 'docker', 'kubernetes'],
            'api': ['api', 'endpoint', 'request', 'response', 'rest', 'graphql'],
            'authentication': ['auth', 'login', 'token', 'oauth', 'jwt', 'credential'],
            'webhooks': ['webhook', 'trigger', 'event', 'callback'],
            'error': ['error', 'exception', 'fail', 'crash', 'bug'],
            'integration': ['integration', 'connect', 'third-party', 'external'],
            'workflow': ['workflow', 'automation', 'flow', 'node', 'execution'],
            'performance': ['slow', 'performance', 'speed', 'optimize', 'scale']
        }

        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category

        return 'general'

    def find_recurring_themes(self, posts: List[Dict]) -> Dict[str, int]:
        """Найти повторяющиеся темы."""
        all_topics = []

        for post in posts:
            full_text = f"{post.get('title', '')} {post.get('content', '')}".lower()
            topics = self._extract_topics(full_text)
            all_topics.extend(topics)

        # Считаем частоту
        topic_counts = Counter(all_topics)

        # Фильтруем только частые темы
        recurring = {topic: count for topic, count in topic_counts.items() if count >= 3}

        return recurring

    def generate_gap_report(self, posts: List[Dict]) -> str:
        """Генерировать отчет о пробелах."""
        analyzed_posts = []

        # Анализируем каждый пост
        for post in posts:
            analysis = self.analyze_post(post)
            if analysis['score'] > 20:  # Порог значимости
                analyzed_posts.append(analysis)

        # Сортируем по приоритету
        analyzed_posts.sort(key=lambda x: x['score'], reverse=True)

        # Находим повторяющиеся темы
        recurring_themes = self.find_recurring_themes(posts)

        # Генерируем отчет
        report = ["# Community Documentation Gaps Report", ""]
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"Analyzed posts: {len(posts)}")
        report.append(f"Significant gaps found: {len(analyzed_posts)}")
        report.append("")

        # Сводка по категориям
        report.append("## Gap Categories")
        report.append("")

        category_counts = Counter(p['category'] for p in analyzed_posts)
        for category, count in category_counts.most_common():
            report.append(f"- **{category.capitalize()}**: {count} issues")
        report.append("")

        # Повторяющиеся темы
        if recurring_themes:
            report.append("## Recurring Themes (mentioned 3+ times)")
            report.append("")
            for theme, count in sorted(recurring_themes.items(), key=lambda x: x[1], reverse=True)[:10]:
                report.append(f"- **{theme}**: mentioned {count} times")
            report.append("")

        # Топ-10 пробелов
        report.append("## Top 10 Documentation Gaps")
        report.append("")

        for i, post in enumerate(analyzed_posts[:10], 1):
            report.append(f"### {i}. [{post['score']:.1f}] {post['title']}")
            report.append(f"**Category**: {post['category']}")
            report.append(f"**Signals**: {', '.join(post['signals'])}")

            if post['uncovered_topics']:
                report.append(f"**Missing documentation for**: {', '.join(post['uncovered_topics'][:5])}")

            if post.get('url'):
                report.append(f"**Link**: {post['url']}")

            report.append("")

        # Рекомендации
        report.append("## Recommendations")
        report.append("")

        # Приоритетные действия на основе анализа
        if 'setup' in category_counts and category_counts['setup'] > 3:
            report.append("1. **Improve installation/setup documentation** - Multiple setup issues reported")

        if 'error' in category_counts and category_counts['error'] > 5:
            report.append("2. **Create comprehensive troubleshooting guide** - Many error-related questions")

        if 'integration' in category_counts:
            report.append("3. **Add more integration examples** - Users struggling with third-party connections")

        if recurring_themes:
            top_theme = list(recurring_themes.keys())[0]
            report.append(f"4. **Create dedicated guide for '{top_theme}'** - Most frequently mentioned topic")

        return "\n".join(report)

def main():
    """Пример использования."""
    # Здесь должна быть интеграция с API форума
    # Для примера используем моковые данные

    sample_posts = [
        {
            'title': 'How to configure webhook authentication?',
            'content': 'I cant find documentation on setting up webhook auth. Getting 401 errors.',
            'views': 1543,
            'replies': 12,
            'resolved': False,
            'created_date': datetime.now() - timedelta(days=3),
            'url': 'https://community.example.com/t/12345'
        },
        {
            'title': 'Webhook not triggering - no docs on debugging',
            'content': 'My webhooks are not firing and there is no documentation on how to debug this.',
            'views': 892,
            'replies': 7,
            'resolved': False,
            'accepted_answer': False,
            'created_date': datetime.now() - timedelta(days=5)
        },
        {
            'title': 'OAuth setup guide needed',
            'content': 'The OAuth documentation is confusing. Need a step-by-step tutorial.',
            'views': 2103,
            'replies': 15,
            'resolved': True,
            'created_date': datetime.now() - timedelta(days=10)
        }
    ]

    detector = CommunityGapDetector(Path('docs'))
    report = detector.generate_gap_report(sample_posts)

    # Сохраняем отчет
    with open('community-gaps-report.md', 'w') as f:
        f.write(report)

    print("Community gaps report saved to community-gaps-report.md")

if __name__ == '__main__':
    main()

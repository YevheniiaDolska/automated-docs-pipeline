#!/usr/bin/env python3
"""
Community Topics Collector

Собирает вопросы из community источников для определения документационных гэпов:
- RSS feeds (community.n8n.io, forums)
- Категоризация по темам
- Определение частых вопросов без документации
"""

import re
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError


@dataclass
class CommunityTopic:
    """Представляет тему из community."""
    title: str
    url: str
    source: str  # 'rss', 'github_discussions', 'discord'
    published_date: Optional[str] = None
    category: str = 'general'
    keywords: list[str] = field(default_factory=list)
    potential_doc_type: str = 'how-to'  # 'how-to', 'troubleshooting', 'concept', 'reference'
    frequency: int = 1  # Сколько раз похожий вопрос встречался


@dataclass
class CollectionResult:
    """Результат сбора community данных."""
    topics: list[CommunityTopic] = field(default_factory=list)
    keyword_frequency: dict = field(default_factory=dict)
    suggested_docs: list[dict] = field(default_factory=list)
    collected_at: str = field(default_factory=lambda: datetime.now().isoformat())


class CommunityCollector:
    """Собирает и анализирует community вопросы для определения doc gaps."""

    # RSS feeds для мониторинга
    DEFAULT_RSS_FEEDS = [
        {
            'url': 'https://community.n8n.io/c/questions/7.rss',
            'name': 'n8n Community Questions',
            'source': 'n8n_community'
        },
        {
            'url': 'https://community.n8n.io/c/feature-requests/6.rss',
            'name': 'n8n Feature Requests',
            'source': 'n8n_features'
        },
    ]

    # Ключевые слова для категоризации
    CATEGORY_KEYWORDS = {
        'webhook': ['webhook', 'trigger', 'http', 'callback', 'endpoint'],
        'authentication': ['auth', 'oauth', 'api key', 'credential', 'token', 'login', 'sso'],
        'error': ['error', 'fail', 'not working', 'issue', 'problem', 'bug', 'broken'],
        'integration': ['integrate', 'connect', 'api', 'service', 'node'],
        'workflow': ['workflow', 'automation', 'flow', 'execute', 'run'],
        'data': ['data', 'json', 'transform', 'map', 'parse', 'format'],
        'scheduling': ['schedule', 'cron', 'timer', 'interval', 'trigger'],
        'deployment': ['deploy', 'install', 'docker', 'kubernetes', 'self-host', 'cloud'],
        'performance': ['slow', 'performance', 'timeout', 'memory', 'scale'],
        'security': ['security', 'permission', 'access', 'encrypt', 'ssl', 'https'],
    }

    # Паттерны для определения типа документации
    DOC_TYPE_PATTERNS = {
        'troubleshooting': [
            r'not working',
            r'error',
            r'fail(ed|ing|s)?',
            r'issue',
            r'problem',
            r'can\'?t',
            r'doesn\'?t',
            r'won\'?t',
            r'help',
            r'stuck',
        ],
        'how-to': [
            r'how (do|can|to)',
            r'way to',
            r'possible to',
            r'want to',
            r'need to',
            r'trying to',
            r'looking for',
        ],
        'concept': [
            r'what is',
            r'what are',
            r'difference between',
            r'explain',
            r'understand',
            r'why (does|is|do)',
        ],
        'reference': [
            r'documentation',
            r'parameters?',
            r'options?',
            r'configuration',
            r'settings?',
            r'list of',
        ],
    }

    def __init__(self, rss_feeds: Optional[list[dict]] = None):
        """
        Args:
            rss_feeds: Список RSS feeds для мониторинга
                      Формат: [{'url': '...', 'name': '...', 'source': '...'}]
        """
        self.rss_feeds = rss_feeds or self.DEFAULT_RSS_FEEDS

    def collect_all(self, limit_per_feed: int = 50) -> CollectionResult:
        """
        Собирает данные из всех источников.

        Args:
            limit_per_feed: Максимум топиков с каждого feed

        Returns:
            CollectionResult с агрегированными данными
        """
        result = CollectionResult()

        # Собираем из RSS
        for feed in self.rss_feeds:
            topics = self._fetch_rss(feed, limit_per_feed)
            result.topics.extend(topics)

        # Анализируем частоту ключевых слов
        result.keyword_frequency = self._analyze_keyword_frequency(result.topics)

        # Генерируем рекомендации по документации
        result.suggested_docs = self._generate_doc_suggestions(result.topics, result.keyword_frequency)

        return result

    def collect_rss(self, feed_url: str, feed_name: str = 'RSS', limit: int = 50) -> list[CommunityTopic]:
        """
        Собирает топики из одного RSS feed.

        Args:
            feed_url: URL RSS feed
            feed_name: Название источника
            limit: Максимум топиков

        Returns:
            Список CommunityTopic
        """
        return self._fetch_rss({'url': feed_url, 'name': feed_name, 'source': 'rss'}, limit)

    def _fetch_rss(self, feed: dict, limit: int) -> list[CommunityTopic]:
        """Загружает и парсит RSS feed."""
        topics = []

        try:
            # Делаем запрос с User-Agent
            request = Request(
                feed['url'],
                headers={'User-Agent': 'DocGapDetector/1.0'}
            )
            with urlopen(request, timeout=30) as response:
                content = response.read()

            # Парсим XML
            root = ET.fromstring(content)

            # Находим items (поддержка RSS 2.0 и Atom)
            items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')

            for item in items[:limit]:
                topic = self._parse_rss_item(item, feed)
                if topic:
                    topics.append(topic)

        except (URLError, ET.ParseError) as e:
            print(f"Warning: Failed to fetch {feed['name']}: {e}")

        return topics

    def _parse_rss_item(self, item: ET.Element, feed: dict) -> Optional[CommunityTopic]:
        """Парсит отдельный item из RSS."""
        # RSS 2.0
        title = item.findtext('title')
        link = item.findtext('link')
        pub_date = item.findtext('pubDate')

        # Atom fallback
        if not title:
            title = item.findtext('{http://www.w3.org/2005/Atom}title')
        if not link:
            link_elem = item.find('{http://www.w3.org/2005/Atom}link')
            link = link_elem.get('href') if link_elem is not None else None
        if not pub_date:
            pub_date = item.findtext('{http://www.w3.org/2005/Atom}published')

        if not title:
            return None

        # Очищаем title
        title = self._clean_title(title)

        # Определяем категорию и тип документации
        category = self._categorize_topic(title)
        doc_type = self._determine_doc_type(title)
        keywords = self._extract_keywords(title)

        return CommunityTopic(
            title=title,
            url=link or '',
            source=feed['source'],
            published_date=pub_date,
            category=category,
            keywords=keywords,
            potential_doc_type=doc_type,
        )

    def _clean_title(self, title: str) -> str:
        """Очищает заголовок от HTML и лишних символов."""
        # Удаляем HTML теги
        title = re.sub(r'<[^>]+>', '', title)
        # Удаляем лишние пробелы
        title = ' '.join(title.split())
        return title.strip()

    def _categorize_topic(self, title: str) -> str:
        """Определяет категорию топика по ключевым словам."""
        title_lower = title.lower()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return category

        return 'general'

    def _determine_doc_type(self, title: str) -> str:
        """Определяет подходящий тип документации."""
        title_lower = title.lower()

        for doc_type, patterns in self.DOC_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, title_lower):
                    return doc_type

        return 'how-to'

    def _extract_keywords(self, title: str) -> list[str]:
        """Извлекает ключевые слова из заголовка."""
        # Убираем стоп-слова
        stop_words = {
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'can',
            'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
            'as', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'under', 'again', 'further',
            'then', 'once', 'here', 'there', 'when', 'where', 'why',
            'how', 'all', 'each', 'few', 'more', 'most', 'other',
            'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
            'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if',
            'or', 'because', 'until', 'while', 'this', 'that', 'these',
            'those', 'i', 'my', 'me', 'we', 'our', 'you', 'your', 'it',
        }

        # Извлекаем слова
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9_-]*\b', title.lower())

        # Фильтруем
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return keywords[:10]  # Топ 10 keywords

    def _analyze_keyword_frequency(self, topics: list[CommunityTopic]) -> dict:
        """Анализирует частоту ключевых слов."""
        all_keywords = []

        for topic in topics:
            all_keywords.extend(topic.keywords)
            all_keywords.append(topic.category)

        return dict(Counter(all_keywords).most_common(50))

    def _generate_doc_suggestions(
        self,
        topics: list[CommunityTopic],
        keyword_freq: dict
    ) -> list[dict]:
        """Генерирует рекомендации по документации на основе анализа."""
        suggestions = []

        # Группируем похожие топики
        topic_groups = self._group_similar_topics(topics)

        for group_key, group_topics in topic_groups.items():
            if len(group_topics) >= 2:  # Минимум 2 похожих вопроса
                # Определяем наиболее частый doc_type
                doc_types = Counter(t.potential_doc_type for t in group_topics)
                primary_doc_type = doc_types.most_common(1)[0][0]

                # Собираем уникальные keywords
                all_keywords = []
                for t in group_topics:
                    all_keywords.extend(t.keywords)
                top_keywords = [k for k, _ in Counter(all_keywords).most_common(5)]

                suggestions.append({
                    'topic': group_key,
                    'frequency': len(group_topics),
                    'suggested_doc_type': primary_doc_type,
                    'keywords': top_keywords,
                    'category': group_topics[0].category,
                    'sample_questions': [t.title for t in group_topics[:3]],
                    'priority': 'high' if len(group_topics) >= 5 else 'medium',
                })

        # Сортируем по частоте
        suggestions.sort(key=lambda x: x['frequency'], reverse=True)

        return suggestions[:20]  # Топ 20 рекомендаций

    def _group_similar_topics(self, topics: list[CommunityTopic]) -> dict[str, list[CommunityTopic]]:
        """Группирует похожие топики по категории и ключевым словам."""
        groups = {}

        for topic in topics:
            # Ключ группы - категория + топ keyword
            if topic.keywords:
                group_key = f"{topic.category}:{topic.keywords[0]}"
            else:
                group_key = topic.category

            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(topic)

        return groups


if __name__ == '__main__':
    # Пример использования
    collector = CommunityCollector()

    print("Collecting community topics...")
    result = collector.collect_all(limit_per_feed=20)

    print(f"\nCollected {len(result.topics)} topics")
    print(f"\nTop keywords: {list(result.keyword_frequency.items())[:10]}")

    print(f"\n=== Top Documentation Suggestions ===")
    for suggestion in result.suggested_docs[:5]:
        print(f"\n[{suggestion['priority']}] {suggestion['topic']}")
        print(f"  Type: {suggestion['suggested_doc_type']}")
        print(f"  Frequency: {suggestion['frequency']} questions")
        print(f"  Keywords: {', '.join(suggestion['keywords'])}")
        print(f"  Sample: {suggestion['sample_questions'][0][:80]}...")

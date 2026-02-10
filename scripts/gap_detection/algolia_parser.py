#!/usr/bin/env python3
"""
Algolia Search Analytics Parser

Парсит данные из Algolia Analytics для определения:
- Поисковые запросы без результатов (no results)
- Частые запросы с низким CTR
- Популярные запросы (для приоритизации документации)

Требует Algolia Analytics API ключи или CSV экспорт.
"""

import csv
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError


@dataclass
class SearchQuery:
    """Представляет поисковый запрос из Algolia."""
    query: str
    count: int  # Сколько раз искали
    results_count: int  # Сколько результатов показано
    click_through_rate: float  # CTR (0-1)
    category: str = 'general'
    suggested_doc_type: str = 'how-to'
    priority: str = 'medium'


@dataclass
class AlgoliaResult:
    """Результат анализа Algolia данных."""
    no_results_queries: list[SearchQuery] = field(default_factory=list)
    low_ctr_queries: list[SearchQuery] = field(default_factory=list)
    popular_queries: list[SearchQuery] = field(default_factory=list)
    suggested_docs: list[dict] = field(default_factory=list)
    analyzed_at: str = field(default_factory=lambda: datetime.now().isoformat())


class AlgoliaAnalytics:
    """Парсит и анализирует данные поиска из Algolia."""

    # Ключевые слова для категоризации запросов
    CATEGORY_KEYWORDS = {
        'webhook': ['webhook', 'trigger', 'http trigger'],
        'authentication': ['auth', 'oauth', 'api key', 'credential', 'token'],
        'error': ['error', 'fail', 'not working', 'issue'],
        'integration': ['integrate', 'connect', 'node'],
        'workflow': ['workflow', 'automation', 'flow'],
        'data': ['json', 'transform', 'parse', 'format', 'map'],
        'deployment': ['deploy', 'install', 'docker', 'self-host'],
    }

    def __init__(
        self,
        app_id: Optional[str] = None,
        api_key: Optional[str] = None,
        index_name: Optional[str] = None
    ):
        """
        Args:
            app_id: Algolia Application ID
            api_key: Algolia Analytics API Key (не Search API Key!)
            index_name: Имя индекса
        """
        self.app_id = app_id
        self.api_key = api_key
        self.index_name = index_name
        self.base_url = f"https://analytics.algolia.com/2"

    def analyze_from_csv(self, csv_path: str) -> AlgoliaResult:
        """
        Анализирует данные из CSV экспорта Algolia.

        Algolia позволяет экспортировать analytics в CSV из Dashboard:
        Analytics > Searches > Export

        Args:
            csv_path: Путь к CSV файлу

        Returns:
            AlgoliaResult с анализом
        """
        result = AlgoliaResult()
        queries = []

        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                query = self._parse_csv_row(row)
                if query:
                    queries.append(query)

        return self._analyze_queries(queries)

    def analyze_from_api(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> AlgoliaResult:
        """
        Анализирует данные напрямую из Algolia Analytics API.

        Args:
            start_date: Начало периода (YYYY-MM-DD)
            end_date: Конец периода (YYYY-MM-DD)
            limit: Максимум запросов

        Returns:
            AlgoliaResult с анализом
        """
        if not all([self.app_id, self.api_key, self.index_name]):
            raise ValueError("Algolia credentials required for API access")

        queries = []

        # Получаем популярные запросы
        popular = self._fetch_searches('popular', start_date, end_date, limit)
        queries.extend(popular)

        # Получаем запросы без результатов
        no_results = self._fetch_searches('noResults', start_date, end_date, limit)
        queries.extend(no_results)

        return self._analyze_queries(queries)

    def analyze_from_json(self, json_path: str) -> AlgoliaResult:
        """
        Анализирует данные из JSON файла.

        Формат JSON:
        {
            "queries": [
                {"query": "...", "count": 10, "nbHits": 0, "clickThroughRate": 0},
                ...
            ]
        }

        Args:
            json_path: Путь к JSON файлу

        Returns:
            AlgoliaResult с анализом
        """
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        queries = []
        for item in data.get('queries', []):
            query = SearchQuery(
                query=item.get('query', ''),
                count=item.get('count', 0),
                results_count=item.get('nbHits', item.get('results_count', 0)),
                click_through_rate=item.get('clickThroughRate', item.get('ctr', 0)),
            )
            if query.query:
                self._enrich_query(query)
                queries.append(query)

        return self._analyze_queries(queries)

    def _fetch_searches(
        self,
        search_type: str,
        start_date: Optional[str],
        end_date: Optional[str],
        limit: int
    ) -> list[SearchQuery]:
        """Получает данные из Algolia API."""
        queries = []

        # Строим URL
        endpoint = f"{self.base_url}/searches/{self.index_name}"
        params = [f"limit={limit}"]

        if search_type == 'noResults':
            params.append("tags=noResults")

        if start_date:
            params.append(f"startDate={start_date}")
        if end_date:
            params.append(f"endDate={end_date}")

        url = f"{endpoint}?{'&'.join(params)}"

        try:
            request = Request(url, headers={
                'X-Algolia-Application-Id': self.app_id,
                'X-Algolia-API-Key': self.api_key,
            })

            with urlopen(request, timeout=30) as response:
                data = json.loads(response.read())

            for item in data.get('searches', []):
                query = SearchQuery(
                    query=item.get('search', ''),
                    count=item.get('count', 0),
                    results_count=item.get('nbHits', 0),
                    click_through_rate=item.get('clickThroughRate', 0),
                )
                if query.query:
                    self._enrich_query(query)
                    queries.append(query)

        except (URLError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to fetch Algolia data: {e}")

        return queries

    def _parse_csv_row(self, row: dict) -> Optional[SearchQuery]:
        """Парсит строку CSV."""
        # Algolia CSV может иметь разные названия колонок
        query_text = (
            row.get('Search') or
            row.get('query') or
            row.get('Query') or
            row.get('search') or
            ''
        )

        if not query_text:
            return None

        count = int(row.get('Count', row.get('count', row.get('Searches', 0))) or 0)
        results = int(row.get('Results', row.get('nbHits', row.get('Hits', 0))) or 0)

        ctr_str = row.get('CTR', row.get('Click-through rate', row.get('clickThroughRate', '0')))
        if isinstance(ctr_str, str):
            ctr_str = ctr_str.replace('%', '').strip()
        try:
            ctr = float(ctr_str) / 100 if float(ctr_str) > 1 else float(ctr_str)
        except (ValueError, TypeError):
            ctr = 0

        query = SearchQuery(
            query=query_text,
            count=count,
            results_count=results,
            click_through_rate=ctr,
        )

        self._enrich_query(query)
        return query

    def _enrich_query(self, query: SearchQuery):
        """Обогащает query категорией и приоритетом."""
        query_lower = query.query.lower()

        # Определяем категорию
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    query.category = category
                    break

        # Определяем тип документации
        if any(word in query_lower for word in ['error', 'fail', 'not working', 'issue']):
            query.suggested_doc_type = 'troubleshooting'
        elif any(word in query_lower for word in ['how to', 'how do', 'configure', 'setup']):
            query.suggested_doc_type = 'how-to'
        elif any(word in query_lower for word in ['what is', 'explain', 'understand']):
            query.suggested_doc_type = 'concept'
        else:
            query.suggested_doc_type = 'reference'

        # Определяем приоритет
        if query.results_count == 0 and query.count >= 10:
            query.priority = 'high'
        elif query.results_count == 0 and query.count >= 5:
            query.priority = 'medium'
        elif query.click_through_rate < 0.1 and query.count >= 20:
            query.priority = 'high'  # Много поисков, но не кликают - плохие результаты
        else:
            query.priority = 'low'

    def _analyze_queries(self, queries: list[SearchQuery]) -> AlgoliaResult:
        """Анализирует список запросов."""
        result = AlgoliaResult()

        for query in queries:
            # Запросы без результатов
            if query.results_count == 0:
                result.no_results_queries.append(query)

            # Запросы с низким CTR (но есть результаты)
            elif query.click_through_rate < 0.1 and query.count >= 5:
                result.low_ctr_queries.append(query)

            # Популярные запросы
            if query.count >= 10:
                result.popular_queries.append(query)

        # Сортируем по count
        result.no_results_queries.sort(key=lambda x: x.count, reverse=True)
        result.low_ctr_queries.sort(key=lambda x: x.count, reverse=True)
        result.popular_queries.sort(key=lambda x: x.count, reverse=True)

        # Генерируем рекомендации
        result.suggested_docs = self._generate_suggestions(result)

        return result

    def _generate_suggestions(self, result: AlgoliaResult) -> list[dict]:
        """Генерирует рекомендации по документации."""
        suggestions = []

        # Приоритет 1: Запросы без результатов (люди ищут, но не находят)
        for query in result.no_results_queries[:20]:
            suggestions.append({
                'query': query.query,
                'reason': 'no_results',
                'search_count': query.count,
                'suggested_doc_type': query.suggested_doc_type,
                'category': query.category,
                'priority': query.priority,
                'action': f'Create {query.suggested_doc_type} document for: "{query.query}"',
            })

        # Приоритет 2: Низкий CTR (результаты есть, но не полезны)
        for query in result.low_ctr_queries[:10]:
            suggestions.append({
                'query': query.query,
                'reason': 'low_ctr',
                'search_count': query.count,
                'ctr': query.click_through_rate,
                'suggested_doc_type': query.suggested_doc_type,
                'category': query.category,
                'priority': 'medium',
                'action': f'Improve documentation for: "{query.query}" (CTR: {query.click_through_rate:.1%})',
            })

        return suggestions


def create_sample_data(output_path: str = 'sample_algolia_data.json'):
    """Создаёт пример данных для тестирования."""
    sample_data = {
        "queries": [
            {"query": "webhook not working", "count": 45, "nbHits": 0, "clickThroughRate": 0},
            {"query": "oauth2 setup", "count": 32, "nbHits": 0, "clickThroughRate": 0},
            {"query": "how to schedule workflow", "count": 28, "nbHits": 5, "clickThroughRate": 0.05},
            {"query": "json transform", "count": 25, "nbHits": 3, "clickThroughRate": 0.08},
            {"query": "api key authentication", "count": 22, "nbHits": 0, "clickThroughRate": 0},
            {"query": "docker install n8n", "count": 20, "nbHits": 2, "clickThroughRate": 0.15},
            {"query": "error 500 http request", "count": 18, "nbHits": 0, "clickThroughRate": 0},
            {"query": "cron expression", "count": 15, "nbHits": 1, "clickThroughRate": 0.03},
            {"query": "workflow timeout", "count": 12, "nbHits": 0, "clickThroughRate": 0},
            {"query": "google sheets integration", "count": 10, "nbHits": 8, "clickThroughRate": 0.25},
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2)

    print(f"Sample data created: {output_path}")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--create-sample':
        create_sample_data()
    else:
        # Демо с sample данными
        create_sample_data('/tmp/sample_algolia.json')

        analyzer = AlgoliaAnalytics()
        result = analyzer.analyze_from_json('/tmp/sample_algolia.json')

        print(f"=== Algolia Search Analysis ===")
        print(f"\nNo Results Queries: {len(result.no_results_queries)}")
        for q in result.no_results_queries[:5]:
            print(f"  [{q.priority}] \"{q.query}\" - {q.count} searches")

        print(f"\nLow CTR Queries: {len(result.low_ctr_queries)}")
        for q in result.low_ctr_queries[:5]:
            print(f"  \"{q.query}\" - {q.count} searches, CTR: {q.click_through_rate:.1%}")

        print(f"\n=== Documentation Suggestions ===")
        for s in result.suggested_docs[:5]:
            print(f"\n[{s['priority']}] {s['action']}")
            print(f"  Reason: {s['reason']}, Category: {s['category']}")

"""
Documentation Gap Detection System

Автоматически определяет пробелы в документации из трёх источников:
1. Изменения кода (git diff) - новые/изменённые фичи
2. Community вопросы (RSS feed) - частые темы без ответов в docs
3. Algolia analytics - поисковые запросы без результатов

Выход: Excel отчёт для анализа Claude Code → batch генерация документов
"""

__version__ = "1.0.0"

from .code_analyzer import CodeChangeAnalyzer
from .community_collector import CommunityCollector
from .algolia_parser import AlgoliaAnalytics
from .gap_aggregator import GapAggregator
from .batch_generator import BatchDocGenerator

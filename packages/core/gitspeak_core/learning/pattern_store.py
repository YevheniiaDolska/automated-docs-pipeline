"""
Documentation Pattern Store.

SQLite-based pattern store for documentation generation learning.
Stores successful document patterns, SEO/GEO scores, template
selections, and content quality patterns for pseudo-RL optimization.

Same interface as CodeForge's PatternStore for cross-product
sync compatibility via CrossProductSyncManager.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DocPattern:
    """
    A stored documentation generation pattern.

    Attributes:
        pattern_id: Unique pattern identifier.
        code_snippet: Document content or template usage example.
        context: Description of when this pattern applies.
        category: Pattern category (template, seo_geo, content, structure).
        score: Validation score when pattern was recorded.
        usage_count: Number of times this pattern was used.
        metadata: Additional context about the pattern.
        created_at: Unix timestamp of creation.
    """

    pattern_id: int = 0
    code_snippet: str = ""
    context: str = ""
    category: str = "content"
    score: float = 0.0
    usage_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0


@dataclass
class DocAntipattern:
    """
    A stored documentation antipattern to avoid.

    Attributes:
        antipattern_id: Unique identifier.
        code_snippet: The problematic document content or template usage.
        context: Description of why this is an antipattern.
        category: Pattern category.
        error_messages: Error messages from linting or validation.
        metadata: Additional context.
        created_at: Unix timestamp of creation.
    """

    antipattern_id: int = 0
    code_snippet: str = ""
    context: str = ""
    category: str = "content"
    error_messages: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0


class DocPatternStore:
    """
    SQLite-based pattern store for documentation generation learning.

    Stores document generation patterns, SEO/GEO scores, template
    selections, and content quality patterns. Provides the same
    interface as CodeForge's PatternStore for cross-product sync
    compatibility via CrossProductSyncManager.

    Attributes:
        db_path: Path to SQLite database file.

    Example:
        >>> store = DocPatternStore(Path("~/.veridoc/patterns.db"))
        >>> store.add_pattern(
        ...     code="template: how_to, score: 98, seo: 95",
        ...     context="How-to guide with frontmatter and GEO optimization",
        ...     category="template",
        ...     score=98.0,
        ... )
        >>> patterns = store.get_top_patterns(category="template", limit=5)
    """

    def __init__(self, db_path: Path) -> None:
        """
        Initialize documentation pattern store.

        Creates the database and tables if they do not exist.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """Create database tables if they do not exist."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS patterns (
                    pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code_snippet TEXT NOT NULL,
                    context TEXT NOT NULL DEFAULT '',
                    category TEXT NOT NULL DEFAULT 'content',
                    score REAL NOT NULL DEFAULT 0.0,
                    usage_count INTEGER NOT NULL DEFAULT 0,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS antipatterns (
                    antipattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code_snippet TEXT NOT NULL,
                    context TEXT NOT NULL DEFAULT '',
                    category TEXT NOT NULL DEFAULT 'content',
                    error_messages TEXT NOT NULL DEFAULT '[]',
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_patterns_category_score
                ON patterns(category, score DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_antipatterns_category
                ON antipatterns(category)
            """)
            conn.commit()

    def add_pattern(
        self,
        code: str,
        context: str,
        category: str = "content",
        score: float = 0.0,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> DocPattern:
        """
        Add a successful documentation pattern to the store.

        Args:
            code: Document content, template usage, or structure example.
            context: Description of when this pattern applies.
            category: Pattern category (template, seo_geo, content, structure).
            score: Validation score (SEO/GEO + style linter combined).
            metadata: Additional context (template_id, doc_type, etc.).
            **kwargs: Additional keyword arguments (ignored, for compatibility).

        Returns:
            The stored DocPattern.
        """
        now = time.time()
        meta_json = json.dumps(metadata or {})

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                """
                INSERT INTO patterns (code_snippet, context, category, score, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (code, context, category, score, meta_json, now),
            )
            conn.commit()
            pattern_id = cursor.lastrowid or 0

        pattern = DocPattern(
            pattern_id=pattern_id,
            code_snippet=code,
            context=context,
            category=category,
            score=score,
            metadata=metadata or {},
            created_at=now,
        )

        logger.debug(
            "Stored doc pattern %d (category=%s, score=%.1f)",
            pattern_id,
            category,
            score,
        )
        return pattern

    def add_antipattern(
        self,
        code: str,
        context: str,
        category: str = "content",
        error_messages: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> DocAntipattern:
        """
        Add a failed documentation pattern as an antipattern.

        Args:
            code: The problematic document content or template usage.
            context: Description of why this failed (linting errors, etc.).
            category: Pattern category.
            error_messages: Error messages from linting or validation.
            metadata: Additional context.
            **kwargs: Additional keyword arguments (ignored, for compatibility).

        Returns:
            The stored DocAntipattern.
        """
        now = time.time()
        meta_json = json.dumps(metadata or {})
        errors_json = json.dumps(error_messages or [])

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                """
                INSERT INTO antipatterns (code_snippet, context, category, error_messages, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (code, context, category, errors_json, meta_json, now),
            )
            conn.commit()
            antipattern_id = cursor.lastrowid or 0

        antipattern = DocAntipattern(
            antipattern_id=antipattern_id,
            code_snippet=code,
            context=context,
            category=category,
            error_messages=error_messages or [],
            metadata=metadata or {},
            created_at=now,
        )

        logger.debug("Stored doc antipattern %d (category=%s)", antipattern_id, category)
        return antipattern

    def get_top_patterns(
        self,
        category: str = "content",
        limit: int = 5,
        min_score: float = 0.0,
    ) -> list[DocPattern]:
        """
        Get top-scoring documentation patterns for a category.

        Args:
            category: Pattern category to query.
            limit: Maximum number of patterns to return.
            min_score: Minimum score threshold.

        Returns:
            List of DocPattern objects ordered by score descending.
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                """
                SELECT pattern_id, code_snippet, context, category, score,
                       usage_count, metadata, created_at
                FROM patterns
                WHERE category = ? AND score >= ?
                ORDER BY score DESC
                LIMIT ?
                """,
                (category, min_score, limit),
            ).fetchall()

        return [
            DocPattern(
                pattern_id=row[0],
                code_snippet=row[1],
                context=row[2],
                category=row[3],
                score=row[4],
                usage_count=row[5],
                metadata=json.loads(row[6]) if row[6] else {},
                created_at=row[7],
            )
            for row in rows
        ]

    def get_antipatterns(
        self,
        category: str = "content",
        limit: int = 5,
    ) -> list[DocAntipattern]:
        """
        Get documentation antipatterns for a category.

        Args:
            category: Pattern category to query.
            limit: Maximum number of antipatterns to return.

        Returns:
            List of DocAntipattern objects ordered by creation time descending.
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                """
                SELECT antipattern_id, code_snippet, context, category,
                       error_messages, metadata, created_at
                FROM antipatterns
                WHERE category = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (category, limit),
            ).fetchall()

        return [
            DocAntipattern(
                antipattern_id=row[0],
                code_snippet=row[1],
                context=row[2],
                category=row[3],
                error_messages=json.loads(row[4]) if row[4] else [],
                metadata=json.loads(row[5]) if row[5] else {},
                created_at=row[6],
            )
            for row in rows
        ]

    def get_evolution_baseline(self, category: str = "content") -> DocPattern | None:
        """
        Get the highest-scoring pattern as a baseline to beat.

        Args:
            category: Pattern category.

        Returns:
            Highest-scoring DocPattern or None if no patterns exist.
        """
        patterns = self.get_top_patterns(category=category, limit=1)
        return patterns[0] if patterns else None

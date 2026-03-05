#!/usr/bin/env python3
"""
Consolidated Report Generator

Объединяет 4 отдельных отчёта документации в один консолидированный файл.
LLM (Claude Code / Codex) читает этот один файл и приоритизирует работу
на основе правил из CLAUDE.md / AGENTS.md.

Входные отчёты:
  - reports/doc_gaps_report.json     (gap analysis)
  - reports/api_sdk_drift_report.json (API/SDK drift)
  - reports/kpi-wall.json            (quality KPIs)
  - reports/kpi-sla-report.json      (SLA violations)

Выходной файл:
  - reports/consolidated_report.json

Запуск:
  python3 scripts/consolidate_reports.py
  python3 scripts/consolidate_reports.py --reports-dir reports --output reports/consolidated_report.json
"""

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class InputReportStatus:
    """Статус одного входного отчёта."""
    found: bool
    generated_at: str = ""
    details: dict = field(default_factory=dict)


@dataclass
class HealthSummary:
    """Сводка здоровья документации."""
    quality_score: int = 0
    stale_pct: float = 0.0
    total_docs: int = 0
    metadata_completeness_pct: float = 0.0
    drift_status: str = "unknown"
    sla_status: str = "unknown"
    sla_breaches: list[str] = field(default_factory=list)
    total_action_items: int = 0
    translation_coverage: dict[str, float] = field(default_factory=dict)


@dataclass
class ActionItem:
    """Один элемент действия для LLM."""
    id: str
    source_report: str
    source_id: str | None
    title: str
    category: str
    suggested_doc_type: str | None
    priority: str
    frequency: int
    action_required: str
    related_files: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    sample_queries: list[str] = field(default_factory=list)
    context: dict = field(default_factory=dict)


class ReportConsolidator:
    """Объединяет 4 отчёта документации в один консолидированный файл."""

    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = Path(reports_dir)
        self.action_items: list[ActionItem] = []
        self.input_statuses: dict[str, InputReportStatus] = {}
        self.health = HealthSummary()
        self._counter = 0

    def _next_id(self) -> str:
        """Генерирует следующий ID вида CONS-001."""
        self._counter += 1
        return f"CONS-{self._counter:03d}"

    def _read_json(self, filename: str) -> dict | None:
        """Читает JSON-файл, возвращает None если файл не найден."""
        filepath = self.reports_dir / filename
        if not filepath.exists():
            return None
        try:
            return json.loads(filepath.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"  Warning: cannot read {filepath}: {e}", file=sys.stderr)
            return None

    def _process_gaps(self) -> None:
        """Обрабатывает doc_gaps_report.json."""
        data = self._read_json("doc_gaps_report.json")
        if data is None:
            self.input_statuses["gaps"] = InputReportStatus(found=False)
            return

        summary = data.get("summary", {})
        self.input_statuses["gaps"] = InputReportStatus(
            found=True,
            generated_at=data.get("generated_at", ""),
            details={
                "total_gaps": summary.get("total_gaps", 0),
                "high_priority": summary.get("high_priority", 0),
                "medium_priority": summary.get("medium_priority", 0),
                "low_priority": summary.get("low_priority", 0),
            },
        )

        for gap in data.get("gaps", []):
            item = ActionItem(
                id=self._next_id(),
                source_report="gaps",
                source_id=gap.get("id"),
                title=gap.get("title", ""),
                category=gap.get("category", ""),
                suggested_doc_type=gap.get("suggested_doc_type"),
                priority=gap.get("priority", "medium"),
                frequency=gap.get("frequency", 1),
                action_required=gap.get("action_required", ""),
                related_files=gap.get("related_files", []),
                keywords=gap.get("keywords", []),
                sample_queries=gap.get("sample_queries", []),
                context={
                    "source": gap.get("source", ""),
                    "status": gap.get("status", "new"),
                    "drift_related": False,
                    "sla_breach_related": False,
                },
            )
            self.action_items.append(item)

    def _process_drift(self) -> None:
        """Обрабатывает api_sdk_drift_report.json."""
        data = self._read_json("api_sdk_drift_report.json")
        if data is None:
            self.input_statuses["drift"] = InputReportStatus(found=False)
            return

        status = data.get("status", "ok")
        self.input_statuses["drift"] = InputReportStatus(
            found=True,
            details={"status": status},
        )
        self.health.drift_status = status

        if status != "drift":
            return

        # Создаём action_items для каждой группы дрифта
        openapi_changed = data.get("openapi_changed", [])
        sdk_changed = data.get("sdk_changed", [])

        if openapi_changed:
            item = ActionItem(
                id=self._next_id(),
                source_report="drift",
                source_id=None,
                title="API spec changed without documentation update",
                category="api_drift",
                suggested_doc_type="reference",
                priority="high",
                frequency=0,
                action_required=(
                    "Update reference docs to match API spec changes. "
                    f"Changed files: {', '.join(openapi_changed)}"
                ),
                related_files=openapi_changed,
                context={
                    "drift_related": True,
                    "drift_type": "openapi",
                    "changed_files": openapi_changed,
                },
            )
            self.action_items.append(item)

        if sdk_changed:
            item = ActionItem(
                id=self._next_id(),
                source_report="drift",
                source_id=None,
                title="SDK changed without documentation update",
                category="sdk_drift",
                suggested_doc_type="reference",
                priority="high",
                frequency=0,
                action_required=(
                    "Update SDK reference docs to match code changes. "
                    f"Changed files: {', '.join(sdk_changed)}"
                ),
                related_files=sdk_changed,
                context={
                    "drift_related": True,
                    "drift_type": "sdk",
                    "changed_files": sdk_changed,
                },
            )
            self.action_items.append(item)

    def _process_kpi(self) -> None:
        """Обрабатывает kpi-wall.json (метаданные + stale docs как action_items)."""
        data = self._read_json("kpi-wall.json")
        if data is None:
            self.input_statuses["kpi"] = InputReportStatus(found=False)
            return

        stale_files = data.get("stale_files", [])
        self.input_statuses["kpi"] = InputReportStatus(
            found=True,
            generated_at=data.get("generated_at", ""),
            details={
                "quality_score": data.get("quality_score", 0),
                "stale_docs": data.get("stale_docs", 0),
                "stale_files_count": len(stale_files),
            },
        )

        self.health.quality_score = data.get("quality_score", 0)
        self.health.stale_pct = data.get("stale_pct", 0.0)
        self.health.total_docs = data.get("total_docs", 0)
        self.health.metadata_completeness_pct = data.get("metadata_completeness_pct", 0.0)

        # Создаём action_item для каждого stale документа
        for filepath in stale_files:
            item = ActionItem(
                id=self._next_id(),
                source_report="kpi",
                source_id=None,
                title=f"Stale document needs review: {filepath}",
                category="stale_doc",
                suggested_doc_type=None,
                priority="medium",
                frequency=0,
                action_required=(
                    f"Review {filepath} (not updated in 90+ days). "
                    "Read the document and assess: (1) if content is outdated, "
                    "update it and set last_reviewed to today; (2) if content is "
                    "still accurate, only update last_reviewed to today."
                ),
                related_files=[filepath],
                context={
                    "stale_related": True,
                },
            )
            self.action_items.append(item)

    def _process_sla(self) -> None:
        """Обрабатывает kpi-sla-report.json."""
        data = self._read_json("kpi-sla-report.json")
        if data is None:
            self.input_statuses["sla"] = InputReportStatus(found=False)
            return

        status = data.get("status", "ok")
        breaches = data.get("breaches", [])
        self.input_statuses["sla"] = InputReportStatus(
            found=True,
            details={
                "status": status,
                "breaches": breaches,
                "metrics": data.get("metrics", {}),
            },
        )
        self.health.sla_status = status
        self.health.sla_breaches = breaches

        if status != "breach":
            return

        # Создаём action_item для каждого нарушения SLA
        for breach_text in breaches:
            item = ActionItem(
                id=self._next_id(),
                source_report="sla",
                source_id=None,
                title=f"SLA breach: {breach_text}",
                category="sla_breach",
                suggested_doc_type=None,
                priority="high",
                frequency=0,
                action_required=breach_text,
                context={
                    "sla_breach_related": True,
                    "breach_details": breach_text,
                    "metrics": data.get("metrics", {}),
                },
            )
            self.action_items.append(item)

    def _process_i18n(self) -> None:
        """Process i18n_sync_report.json (5th input)."""
        data = self._read_json("i18n_sync_report.json")
        if data is None:
            self.input_statuses["i18n"] = InputReportStatus(found=False)
            return

        coverage = data.get("coverage", {})
        self.input_statuses["i18n"] = InputReportStatus(
            found=True,
            generated_at=data.get("generated_at", ""),
            details={
                "total_source_docs": data.get("total_source_docs", 0),
                "languages": data.get("languages", []),
                "coverage": coverage,
            },
        )

        # Store coverage in health summary
        for locale, stats in coverage.items():
            self.health.translation_coverage[locale] = stats.get("coverage_pct", 0.0)

        # Create action items for missing and stale translations
        for item in data.get("items", []):
            status = item.get("status", "")
            if status not in ("missing", "stale"):
                continue

            category = f"{status}_translation"
            priority = "medium" if status == "missing" else "low"

            action = ActionItem(
                id=self._next_id(),
                source_report="i18n",
                source_id=None,
                title=f"{status.capitalize()} translation: {item.get('target_path', '')}",
                category=category,
                suggested_doc_type=None,
                priority=priority,
                frequency=0,
                action_required=(
                    f"{'Create' if status == 'missing' else 'Update'} translation "
                    f"at {item.get('target_path', '')} "
                    f"from source {item.get('source_path', '')}"
                ),
                related_files=[
                    item.get("source_path", ""),
                    item.get("target_path", ""),
                ],
                context={
                    "i18n_related": True,
                    "translation_status": status,
                    "target_locale": item.get("target_locale", ""),
                    "source_hash": item.get("source_hash", ""),
                },
            )
            self.action_items.append(action)

    def _cross_reference_drift(self) -> None:
        """Аннотирует gap-элементы, связанные с дрифтом."""
        drift_data = self._read_json("api_sdk_drift_report.json")
        if drift_data is None or drift_data.get("status") != "drift":
            return

        drift_files = set(
            drift_data.get("openapi_changed", [])
            + drift_data.get("sdk_changed", [])
        )
        if not drift_files:
            return

        for item in self.action_items:
            if item.source_report != "gaps":
                continue
            overlap = drift_files & set(item.related_files)
            if overlap:
                item.context["drift_related"] = True
                item.context["drift_overlapping_files"] = list(overlap)

    def consolidate(self) -> dict:
        """Запускает полную консолидацию и возвращает результат."""
        print("Consolidating reports...")

        self._process_gaps()
        self._process_drift()
        self._process_kpi()
        self._process_sla()
        self._process_i18n()
        self._cross_reference_drift()

        self.health.total_action_items = len(self.action_items)

        result = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "input_reports": {
                k: asdict(v) for k, v in self.input_statuses.items()
            },
            "health_summary": asdict(self.health),
            "action_items": [asdict(item) for item in self.action_items],
        }

        return result

    def save(self, output_path: str = "reports/consolidated_report.json") -> Path:
        """Консолидирует и сохраняет результат."""
        result = self.consolidate()
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        self._print_summary(result)
        return out

    def _print_summary(self, result: dict) -> None:
        """Выводит сводку в stdout."""
        health = result["health_summary"]
        inputs = result["input_reports"]
        items = result["action_items"]

        print()
        print("=" * 60)
        print("  CONSOLIDATED REPORT SUMMARY")
        print("=" * 60)
        print()

        # Статус входных отчётов
        for name, info in inputs.items():
            status_mark = "[OK]" if info["found"] else "[MISSING]"
            print(f"  {status_mark} {name}")

        print()
        print(f"  Quality score:    {health['quality_score']}")
        print(f"  Drift status:     {health['drift_status']}")
        print(f"  SLA status:       {health['sla_status']}")
        print(f"  Total docs:       {health['total_docs']}")
        print(f"  Stale docs:       {health['stale_pct']:.1f}%")
        print()
        print(f"  Total action items: {len(items)}")

        # Подсчёт по source_report
        by_source: dict[str, int] = {}
        by_priority: dict[str, int] = {}
        for item in items:
            by_source[item["source_report"]] = by_source.get(item["source_report"], 0) + 1
            by_priority[item["priority"]] = by_priority.get(item["priority"], 0) + 1

        if by_source:
            print("  By source:")
            for src, cnt in sorted(by_source.items()):
                print(f"    {src}: {cnt}")

        if by_priority:
            print("  By priority:")
            for pri, cnt in sorted(by_priority.items()):
                print(f"    {pri}: {cnt}")

        print()
        print(f"  Output: {self.reports_dir / 'consolidated_report.json'}")
        print("=" * 60)
        print()
        print("Next step: open Claude Code in the project directory and say:")
        print('  "Process reports/consolidated_report.json"')
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Consolidate 4 documentation reports into one prioritized file."
    )
    parser.add_argument(
        "--reports-dir",
        default="reports",
        help="Directory containing input reports (default: reports)",
    )
    parser.add_argument(
        "--output",
        default="reports/consolidated_report.json",
        help="Output path for consolidated report (default: reports/consolidated_report.json)",
    )
    args = parser.parse_args()

    consolidator = ReportConsolidator(reports_dir=args.reports_dir)
    consolidator.save(output_path=args.output)


if __name__ == "__main__":
    main()

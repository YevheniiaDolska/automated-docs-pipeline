#!/usr/bin/env python3
"""
Documentation Gap Detection CLI

Главный скрипт для запуска анализа документационных гэпов.

Использование:
    python -m gap_detection.cli analyze --since 7d
    python -m gap_detection.cli generate --report reports/doc_gaps_report.json --max 5
    python -m gap_detection.cli full --since 7d --generate --max 10
"""

import argparse
import sys
from pathlib import Path


def cmd_analyze(args):
    """Запускает анализ гэпов."""
    from .gap_aggregator import GapAggregator

    print("=" * 60)
    print("Documentation Gap Analysis")
    print("=" * 60)

    aggregator = GapAggregator(args.output_dir)

    # Определяем путь к Algolia данным
    algolia_csv = args.algolia_csv if hasattr(args, 'algolia_csv') else None
    algolia_json = args.algolia_json if hasattr(args, 'algolia_json') else None

    # Запускаем анализ
    report = aggregator.run_full_analysis(
        repo_path=args.repo,
        since_days=args.since,
        algolia_csv=algolia_csv,
        algolia_json=algolia_json,
    )

    # Сохраняем отчёты
    json_path = aggregator.save_to_json(report)
    csv_path = aggregator.save_to_csv(report)

    try:
        excel_path = aggregator.save_to_excel(report)
    except (ImportError, OSError, ValueError) as exc:
        print(f"Warning: Excel report was not generated: {exc}")
        excel_path = None

    # Выводим summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total gaps found: {report.summary['total_gaps']}")
    print(f"  High priority: {report.summary['high_priority']}")
    print(f"  Medium priority: {report.summary['medium_priority']}")
    print(f"  Low priority: {report.summary['low_priority']}")
    print(f"\nBy source: {report.summary['by_source']}")
    print(f"By doc type: {report.summary['by_doc_type']}")

    print("\n" + "=" * 60)
    print("Reports saved:")
    print("=" * 60)
    print(f"  JSON: {json_path}")
    print(f"  CSV:  {csv_path}")
    if excel_path:
        print(f"  Excel: {excel_path}")

    # Показываем top gaps
    print("\n" + "=" * 60)
    print("Top 5 High Priority Gaps")
    print("=" * 60)
    high_priority = [g for g in report.gaps if g.priority == 'high'][:5]
    for gap in high_priority:
        print(f"\n[{gap.id}] {gap.title}")
        print(f"  Type: {gap.suggested_doc_type} | Source: {gap.source}")
        print(f"  Action: {gap.action_required[:80]}...")

    return json_path


def cmd_generate(args):
    """Генерирует документы из отчёта."""
    from .batch_generator import run_batch_generation

    print("=" * 60)
    print("Batch Document Generation")
    print("=" * 60)

    priority = args.priority.split(',') if args.priority else ['high', 'medium']

    run_batch_generation(
        report_path=args.report,
        max_tasks=args.max,
        priority=priority,
        use_claude=args.use_claude,
    )


def cmd_full(args):
    """Полный цикл: анализ + генерация."""
    print("Running full gap detection pipeline...")
    print()

    # Шаг 1: Анализ
    json_path = cmd_analyze(args)

    # Шаг 2: Генерация (если включена)
    if args.generate:
        print("\n" + "=" * 60)
        print("Generating documents...")
        print("=" * 60)

        args.report = json_path
        cmd_generate(args)


def cmd_community(args):
    """Только сбор community данных."""
    from .community_collector import CommunityCollector

    print("Collecting community topics...")

    collector = CommunityCollector()
    result = collector.collect_all(limit_per_feed=args.limit)

    print(f"\nCollected {len(result.topics)} topics")
    print(f"Top keywords: {list(result.keyword_frequency.items())[:10]}")

    print("\nTop documentation suggestions:")
    for s in result.suggested_docs[:5]:
        print(f"\n[{s['priority']}] {s['topic']}")
        print(f"  Type: {s['suggested_doc_type']}, Frequency: {s['frequency']}")


def cmd_code(args):
    """Только анализ кода."""
    from .code_analyzer import CodeChangeAnalyzer

    print(f"Analyzing code changes in {args.repo}...")

    analyzer = CodeChangeAnalyzer(args.repo)

    if args.tag:
        result = analyzer.analyze_release(args.tag)
    else:
        result = analyzer.analyze_commits(since=f'{args.since} days ago')

    print(f"\nFound {result.summary['total_changes']} documentation-relevant changes")
    print(f"By priority: {result.summary['by_priority']}")
    print(f"By category: {result.summary['by_category']}")

    print("\nTop changes:")
    for change in result.changes[:10]:
        print(f"\n[{change.priority}] {change.category}: {change.description}")
        print(f"  File: {change.file_path}")
        print(f"  Suggestion: {change.doc_suggestion[:80]}...")


def main():
    parser = argparse.ArgumentParser(
        description='Documentation Gap Detection System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full analysis with defaults
  python -m gap_detection.cli analyze

  # Analyze last 30 days
  python -m gap_detection.cli analyze --since 30

  # Full pipeline: analyze and generate docs
  python -m gap_detection.cli full --since 7 --generate --max 5

  # Generate docs from existing report
  python -m gap_detection.cli generate --report reports/doc_gaps_report.json

  # Only collect community topics
  python -m gap_detection.cli community --limit 100

  # Analyze specific release
  python -m gap_detection.cli code --tag v1.2.0
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # analyze command
    p_analyze = subparsers.add_parser('analyze', help='Run gap analysis')
    p_analyze.add_argument('--repo', default='.', help='Path to git repository')
    p_analyze.add_argument('--since', type=int, default=7, help='Analyze commits from last N days')
    p_analyze.add_argument('--output-dir', default='./reports', help='Output directory for reports')
    p_analyze.add_argument('--algolia-csv', help='Path to Algolia CSV export')
    p_analyze.add_argument('--algolia-json', help='Path to Algolia JSON data')
    p_analyze.set_defaults(func=cmd_analyze)

    # generate command
    p_generate = subparsers.add_parser('generate', help='Generate docs from report')
    p_generate.add_argument('--report', required=True, help='Path to JSON report')
    p_generate.add_argument('--max', type=int, default=10, help='Max documents to generate')
    p_generate.add_argument('--priority', default='high,medium', help='Priority filter (comma-separated)')
    p_generate.add_argument('--use-claude', action='store_true', help='Use Claude Code for generation')
    p_generate.set_defaults(func=cmd_generate)

    # full command
    p_full = subparsers.add_parser('full', help='Full pipeline: analyze + generate')
    p_full.add_argument('--repo', default='.', help='Path to git repository')
    p_full.add_argument('--since', type=int, default=7, help='Analyze commits from last N days')
    p_full.add_argument('--output-dir', default='./reports', help='Output directory')
    p_full.add_argument('--generate', action='store_true', help='Also generate documents')
    p_full.add_argument('--max', type=int, default=10, help='Max documents to generate')
    p_full.add_argument('--priority', default='high,medium', help='Priority filter')
    p_full.add_argument('--use-claude', action='store_true', help='Use Claude Code')
    p_full.add_argument('--algolia-csv', help='Algolia CSV export')
    p_full.add_argument('--algolia-json', help='Algolia JSON data')
    p_full.set_defaults(func=cmd_full)

    # community command
    p_community = subparsers.add_parser('community', help='Collect community topics only')
    p_community.add_argument('--limit', type=int, default=50, help='Max topics per feed')
    p_community.set_defaults(func=cmd_community)

    # code command
    p_code = subparsers.add_parser('code', help='Analyze code changes only')
    p_code.add_argument('--repo', default='.', help='Path to git repository')
    p_code.add_argument('--since', type=int, default=7, help='Days to analyze')
    p_code.add_argument('--tag', help='Analyze specific release tag')
    p_code.set_defaults(func=cmd_code)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()

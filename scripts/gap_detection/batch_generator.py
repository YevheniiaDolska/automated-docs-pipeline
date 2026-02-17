#!/usr/bin/env python3
"""
Batch Document Generator

Генерирует документы пакетами на основе анализа гэпов.
Включает:
- Приоритизацию тем для документации
- Генерацию структуры документов из шаблонов
- Подготовку промптов для Claude Code
- Создание batch задач для параллельной обработки
"""

import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

if __package__:
    from .gap_aggregator import DocumentationGap, AggregatedReport
else:
    from gap_aggregator import DocumentationGap, AggregatedReport


@dataclass
class DocumentTask:
    """Задача на создание документа."""
    id: str
    gap_id: str
    title: str
    doc_type: str
    category: str
    priority: str
    output_path: str
    template_name: str
    context: dict = field(default_factory=dict)
    status: str = 'pending'  # 'pending', 'generated', 'reviewed', 'published'
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class BatchResult:
    """Результат batch генерации."""
    tasks: list[DocumentTask] = field(default_factory=list)
    generated_files: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    claude_prompt: str = ''


class BatchDocGenerator:
    """Генерирует документы пакетами на основе gap analysis."""

    # Маппинг doc_type -> template file
    TEMPLATE_MAP = {
        'tutorial': 'tutorial.md',
        'how-to': 'how-to.md',
        'concept': 'concept.md',
        'reference': 'reference.md',
        'troubleshooting': 'troubleshooting.md',
        'quickstart': 'quickstart.md',
        'integration-guide': 'integration-guide.md',
        'faq': 'faq.md',
    }

    # Маппинг doc_type -> output directory
    OUTPUT_DIRS = {
        'tutorial': 'docs/getting-started',
        'how-to': 'docs/how-to',
        'concept': 'docs/concepts',
        'reference': 'docs/reference',
        'troubleshooting': 'docs/troubleshooting',
        'quickstart': 'docs/getting-started',
        'integration-guide': 'docs/how-to',
        'faq': 'docs/reference',
    }

    def __init__(
        self,
        templates_dir: str = './templates',
        output_base: str = '.',
        claude_commands_dir: str = './.claude/commands'
    ):
        """
        Args:
            templates_dir: Директория с шаблонами
            output_base: Базовая директория для документов
            claude_commands_dir: Директория для Claude Code команд
        """
        self.templates_dir = Path(templates_dir)
        self.output_base = Path(output_base)
        self.claude_commands_dir = Path(claude_commands_dir)

    def create_batch_from_report(
        self,
        report: AggregatedReport,
        max_tasks: int = 10,
        priority_filter: Optional[list[str]] = None
    ) -> BatchResult:
        """
        Создаёт batch задач из отчёта о гэпах.

        Args:
            report: AggregatedReport с гэпами
            max_tasks: Максимум задач в batch
            priority_filter: Фильтр по приоритету ['high', 'medium']

        Returns:
            BatchResult с задачами
        """
        result = BatchResult()
        priority_filter = priority_filter or ['high', 'medium']

        # Фильтруем и сортируем гэпы
        filtered_gaps = [
            g for g in report.gaps
            if g.priority in priority_filter
        ]

        # Берём top N
        selected_gaps = filtered_gaps[:max_tasks]

        # Создаём задачи
        for i, gap in enumerate(selected_gaps, 1):
            task = self._create_task_from_gap(gap, i)
            result.tasks.append(task)

        # Генерируем Claude prompt для batch обработки
        result.claude_prompt = self._generate_claude_prompt(result.tasks)

        return result

    def generate_documents(self, batch: BatchResult, use_claude: bool = False) -> BatchResult:
        """
        Генерирует документы для batch задач.

        Args:
            batch: BatchResult с задачами
            use_claude: Использовать Claude Code для генерации

        Returns:
            Обновлённый BatchResult
        """
        for task in batch.tasks:
            try:
                if use_claude:
                    # Используем Claude Code через subprocess
                    self._generate_with_claude(task)
                else:
                    # Генерируем из шаблона
                    self._generate_from_template(task)

                task.status = 'generated'
                batch.generated_files.append(task.output_path)

            except Exception as e:
                task.status = 'error'
                batch.errors.append(f'{task.id}: {str(e)}')

        return batch

    def save_batch_config(self, batch: BatchResult, filename: str = 'batch_tasks.json') -> str:
        """
        Сохраняет конфигурацию batch для последующей обработки.

        Args:
            batch: BatchResult
            filename: Имя файла

        Returns:
            Путь к файлу
        """
        output_path = self.output_base / 'reports' / filename

        data = {
            'generated_at': datetime.now().isoformat(),
            'total_tasks': len(batch.tasks),
            'tasks': [
                {
                    'id': t.id,
                    'gap_id': t.gap_id,
                    'title': t.title,
                    'doc_type': t.doc_type,
                    'category': t.category,
                    'priority': t.priority,
                    'output_path': t.output_path,
                    'template_name': t.template_name,
                    'context': t.context,
                    'status': t.status,
                }
                for t in batch.tasks
            ],
            'claude_prompt': batch.claude_prompt,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Batch config saved: {output_path}")
        return str(output_path)

    def save_claude_command(self, batch: BatchResult, command_name: str = 'generate-docs') -> str:
        """
        Создаёт Claude Code slash command для генерации документов.

        Args:
            batch: BatchResult с промптом
            command_name: Имя команды (без слеша)

        Returns:
            Путь к файлу команды
        """
        self.claude_commands_dir.mkdir(parents=True, exist_ok=True)
        command_path = self.claude_commands_dir / f'{command_name}.md'

        command_content = f"""# Generate Documentation from Gap Analysis

{batch.claude_prompt}

## After Generation

1. Run pre-commit hooks: `git add . && git commit -m "docs: add generated documentation"`
2. If hooks fail, fix issues and retry
3. Create PR for human review
"""

        with open(command_path, 'w', encoding='utf-8') as f:
            f.write(command_content)

        print(f"Claude command saved: {command_path}")
        print(f"Use with: /generate-docs")
        return str(command_path)

    def _create_task_from_gap(self, gap: DocumentationGap, index: int) -> DocumentTask:
        """Создаёт задачу из гэпа."""
        doc_type = gap.suggested_doc_type
        template_name = self.TEMPLATE_MAP.get(doc_type, 'how-to.md')
        output_dir = self.OUTPUT_DIRS.get(doc_type, 'docs/how-to')

        # Генерируем slug для filename
        slug = self._slugify(gap.title)
        output_path = f'{output_dir}/{slug}.md'

        # Контекст для шаблона
        context = {
            'title': self._clean_title(gap.title),
            'description': gap.description,
            'category': gap.category,
            'keywords': gap.keywords,
            'sample_queries': gap.sample_queries,
            'action_required': gap.action_required,
            'source': gap.source,
        }

        return DocumentTask(
            id=f'DOC-{index:03d}',
            gap_id=gap.id,
            title=gap.title,
            doc_type=doc_type,
            category=gap.category,
            priority=gap.priority,
            output_path=output_path,
            template_name=template_name,
            context=context,
        )

    def _generate_from_template(self, task: DocumentTask):
        """Генерирует документ из шаблона."""
        template_path = self.templates_dir / task.template_name

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        # Читаем шаблон
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # Простая замена плейсхолдеров
        content = template
        content = content.replace('[Title]', task.context.get('title', task.title))
        content = content.replace('[Product]', 'n8n')
        content = content.replace('[product]', 'n8n')
        content = content.replace('[PRODUCT]', 'N8N')

        # Записываем файл
        output_path = self.output_base / task.output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_with_claude(self, task: DocumentTask):
        """Генерирует документ через Claude Code."""
        prompt = self._create_single_doc_prompt(task)

        # Записываем prompt в temp файл
        prompt_file = self.output_base / '.tmp_prompt.md'
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)

        # Вызываем Claude Code (если доступен)
        try:
            result = subprocess.run(
                ['claude', '-p', str(prompt_file)],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                raise RuntimeError(f"Claude Code failed: {result.stderr}")
        except FileNotFoundError:
            # Claude Code не установлен - fallback to template
            self._generate_from_template(task)
        finally:
            if prompt_file.exists():
                prompt_file.unlink()

    def _generate_claude_prompt(self, tasks: list[DocumentTask]) -> str:
        """Генерирует общий prompt для Claude Code."""
        prompt_parts = [
            "# Documentation Generation Tasks",
            "",
            "Generate the following documentation files based on the gap analysis.",
            "Follow these rules:",
            "",
            "1. Use the templates in `./templates/` directory",
            "2. Follow frontmatter schema from `docs-schema.yml`",
            "3. Keep descriptions 50-160 characters for SEO",
            "4. First paragraph must be <60 words with a clear definition",
            "5. Use concrete examples and code samples",
            "6. Don't use words like 'simple', 'easy', 'just'",
            "",
            "## Tasks",
            "",
        ]

        for task in tasks:
            prompt_parts.extend([
                f"### {task.id}: {task.title}",
                f"- **Type**: {task.doc_type}",
                f"- **Priority**: {task.priority}",
                f"- **Output**: `{task.output_path}`",
                f"- **Template**: `templates/{task.template_name}`",
                f"- **Category**: {task.category}",
                "",
                f"**Context**: {task.context.get('description', '')}",
                "",
                f"**Keywords**: {', '.join(task.context.get('keywords', []))}",
                "",
                f"**Sample questions from users**:",
            ])

            for q in task.context.get('sample_queries', [])[:3]:
                prompt_parts.append(f"- {q}")

            prompt_parts.extend(["", "---", ""])

        prompt_parts.extend([
            "## Execution",
            "",
            "For each task:",
            "1. Read the template file",
            "2. Create the document with proper frontmatter",
            "3. Fill in content based on context and keywords",
            "4. Save to the specified output path",
            "",
            "After generating all documents, run: `npm run lint` to validate.",
        ])

        return '\n'.join(prompt_parts)

    def _create_single_doc_prompt(self, task: DocumentTask) -> str:
        """Создаёт prompt для одного документа."""
        return f"""Create a {task.doc_type} document for: {task.title}

Template: templates/{task.template_name}
Output: {task.output_path}

Context:
- Category: {task.category}
- Description: {task.context.get('description', '')}
- Keywords: {', '.join(task.context.get('keywords', []))}

User questions that indicate need for this doc:
{chr(10).join('- ' + q for q in task.context.get('sample_queries', [])[:3])}

Requirements:
1. Follow frontmatter schema (title, description 50-160 chars, content_type: {task.doc_type})
2. First paragraph <60 words with clear definition
3. Include practical code examples
4. Use active voice, present tense
"""

    def _slugify(self, text: str) -> str:
        """Преобразует текст в slug для filename."""
        import re
        # Удаляем префиксы типа "CODE-0001:" или "Webhook:"
        text = re.sub(r'^[A-Z]+-\d+:\s*', '', text)
        text = re.sub(r'^[A-Za-z]+:\s*', '', text)

        # Стандартный slugify
        slug = text.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')[:50]

    def _clean_title(self, title: str) -> str:
        """Очищает title от лишних префиксов."""
        import re
        # Удаляем ID префиксы
        title = re.sub(r'^[A-Z]+-\d+:\s*', '', title)
        # Удаляем категорию если она дублирует
        title = re.sub(r'^(Webhook|Error|Config|Api|Search):\s*', '', title, flags=re.IGNORECASE)
        return title.strip()


def run_batch_generation(
    report_path: str,
    max_tasks: int = 10,
    priority: list[str] = None,
    use_claude: bool = False
):
    """
    Запускает batch генерацию из JSON отчёта.

    Args:
        report_path: Путь к JSON отчёту от gap_aggregator
        max_tasks: Максимум задач
        priority: Фильтр приоритета
        use_claude: Использовать Claude Code
    """
    if __package__:
        from .gap_aggregator import AggregatedReport, DocumentationGap
    else:
        from gap_aggregator import AggregatedReport, DocumentationGap

    # Загружаем отчёт
    with open(report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Восстанавливаем объекты
    report = AggregatedReport(
        gaps=[DocumentationGap(**g) for g in data['gaps']],
        summary=data['summary'],
        sources_analyzed=data['sources_analyzed'],
        generated_at=data['generated_at'],
    )

    # Создаём batch
    generator = BatchDocGenerator()
    batch = generator.create_batch_from_report(
        report,
        max_tasks=max_tasks,
        priority_filter=priority or ['high', 'medium']
    )

    print(f"Created {len(batch.tasks)} tasks")

    # Сохраняем конфиг и Claude command
    generator.save_batch_config(batch)
    generator.save_claude_command(batch)

    if use_claude:
        print("\nGenerating documents with Claude Code...")
        batch = generator.generate_documents(batch, use_claude=True)
        print(f"Generated {len(batch.generated_files)} files")
        if batch.errors:
            print(f"Errors: {batch.errors}")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print("Usage: python scripts/gap_detection/batch_generator.py <report.json> [max_tasks]")
        print("\nExample:")
        print("  python scripts/gap_detection/batch_generator.py reports/doc_gaps_report.json 5")
        sys.exit(0)

    if len(sys.argv) > 1:
        run_batch_generation(
            sys.argv[1],
            max_tasks=int(sys.argv[2]) if len(sys.argv) > 2 else 10
        )
    else:
        print("Usage: python scripts/gap_detection/batch_generator.py <report.json> [max_tasks]")
        print("\nExample:")
        print("  python scripts/gap_detection/batch_generator.py reports/doc_gaps_report.json 5")

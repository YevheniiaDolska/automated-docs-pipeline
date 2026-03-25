"""
Documentation Orchestrator.

Wraps the existing VeriDoc pipeline with the extended orchestrator
pattern: auto-analyzes consolidated reports, creates plans with
one task per action_item (Tier 1 first, then 2, then 3), executes
each document in a subprocess with fresh context, runs self-checks
(linting, frontmatter, SEO/GEO validation), reviews each document,
and manages pattern storage.

Unlike other Forge products, DocOrchestrator does not conduct
interactive interviews. Instead, it infers priorities and constraints
directly from the consolidated report's health_summary and
action_items structure.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ActionItem:
    """
    A single action item from the consolidated report.

    Attributes:
        item_id: Unique identifier (e.g., CONS-001).
        source_report: Origin report (gaps, drift, kpi, sla).
        title: Short description of the action.
        category: Action category (authentication, api_drift, stale_doc, etc.).
        suggested_doc_type: Recommended document type (how-to, reference, etc.).
        priority: Priority level (high, medium, low).
        frequency: How often this item appears in analysis.
        action_required: Description of what needs to be done.
        related_files: List of file paths related to this action.
        context: Additional context flags (drift_related, sla_breach_related).
        tier: Assigned processing tier (1, 2, or 3).
    """

    item_id: str = ""
    source_report: str = ""
    title: str = ""
    category: str = ""
    suggested_doc_type: str | None = None
    priority: str = "medium"
    frequency: int = 0
    action_required: str = ""
    related_files: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    tier: int = 2


@dataclass
class DocTaskResult:
    """
    Result of processing a single documentation action item.

    Attributes:
        item_id: The action item identifier.
        status: Processing status (completed, failed, blocked).
        document_path: Path to the created or updated document.
        lint_attempts: Number of lint retry attempts used.
        self_check_score: Score from self-validation checks.
        errors: List of errors encountered during processing.
    """

    item_id: str = ""
    status: str = "pending"
    document_path: str = ""
    lint_attempts: int = 0
    self_check_score: float = 0.0
    errors: list[str] = field(default_factory=list)


@dataclass
class DocOrchestrationSummary:
    """
    Summary of an entire documentation orchestration run.

    Attributes:
        quality_score: Overall quality score from the report.
        drift_status: API/SDK drift status (ok, drift).
        sla_status: SLA compliance status (ok, breach).
        total_action_items: Total number of action items processed.
        tier_1_processed: Count of Tier 1 items processed.
        tier_1_blocked: Count of Tier 1 items blocked.
        tier_2_processed: Count of Tier 2 items processed.
        tier_2_blocked: Count of Tier 2 items blocked.
        tier_3_processed: Count of Tier 3 items processed.
        tier_3_blocked: Count of Tier 3 items blocked.
        documents_created: Number of new documents created.
        documents_updated: Number of existing documents updated.
        lint_retries_total: Total lint retries across all documents.
        blocked_items: List of item IDs that could not be processed.
        results: Per-item processing results.
    """

    quality_score: float = 0.0
    drift_status: str = "ok"
    sla_status: str = "ok"
    total_action_items: int = 0
    tier_1_processed: int = 0
    tier_1_blocked: int = 0
    tier_2_processed: int = 0
    tier_2_blocked: int = 0
    tier_3_processed: int = 0
    tier_3_blocked: int = 0
    documents_created: int = 0
    documents_updated: int = 0
    lint_retries_total: int = 0
    blocked_items: list[str] = field(default_factory=list)
    results: list[DocTaskResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Tier classification constants
# ---------------------------------------------------------------------------

TIER_1_CATEGORIES = frozenset({
    "breaking_change",
    "api_endpoint",
    "authentication",
})

TIER_1_SOURCES = frozenset({
    "drift",
    "sla",
})

TIER_2_CATEGORIES = frozenset({
    "signature_change",
    "new_function",
    "removed_function",
    "webhook",
    "config_option",
    "env_var",
    "cli_command",
    "stale_doc",
})


class DocOrchestrator:
    """
    Documentation orchestrator with plan-driven subprocess execution.

    Wraps the existing VeriDoc pipeline with the extended orchestrator
    pattern. Auto-analyzes consolidated reports, assigns tiers to
    action items, executes document generation in isolated subprocesses,
    and manages pattern storage for pseudo-RL learning.

    Attributes:
        plan_dir: Directory for storing orchestration plan files.
        pattern_store: DocPatternStore for pseudo-RL learning.
        worker_script: Python module path for subprocess workers.
        timeout_seconds: Maximum seconds per subprocess task.
        max_retries: Maximum retry attempts per task.
        max_lint_retries: Maximum lint retry attempts per document.

    Example:
        >>> orchestrator = DocOrchestrator(
        ...     plan_dir=Path("~/.veridoc/plans"),
        ...     pattern_store=DocPatternStore(Path("~/.veridoc/patterns.db")),
        ... )
        >>> summary = await orchestrator.process_consolidated_report(
        ...     report_path=Path("reports/consolidated_report.json"),
        ... )
        >>> print(f"Processed {summary.total_action_items} items")
    """

    def __init__(
        self,
        plan_dir: Path,
        pattern_store: Any | None = None,
        worker_script: str = "gitspeak_core.docs.doc_worker",
        timeout_seconds: int = 300,
        max_retries: int = 3,
        max_lint_retries: int = 5,
    ) -> None:
        """
        Initialize documentation orchestrator.

        Args:
            plan_dir: Directory for storing orchestration plan files.
            pattern_store: DocPatternStore instance for pseudo-RL learning.
            worker_script: Python module path for subprocess workers.
            timeout_seconds: Maximum seconds per subprocess task.
            max_retries: Maximum retry attempts per task.
            max_lint_retries: Maximum lint retry attempts per document.
        """
        self.plan_dir = plan_dir
        self.plan_dir.mkdir(parents=True, exist_ok=True)
        self.pattern_store = pattern_store
        self.worker_script = worker_script
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_lint_retries = max_lint_retries
        self._plan: dict[str, Any] | None = None

    # ------------------------------------------------------------------
    # Report loading and tier assignment
    # ------------------------------------------------------------------

    def load_report(self, report_path: Path) -> dict[str, Any]:
        """
        Load and parse a consolidated report JSON file.

        Args:
            report_path: Path to consolidated_report.json.

        Returns:
            Parsed report dict.

        Raises:
            FileNotFoundError: If the report file does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
        """
        content = report_path.read_text(encoding="utf-8")
        report: dict[str, Any] = json.loads(content)
        logger.info(
            "Loaded consolidated report with %d action items",
            len(report.get("action_items", [])),
        )
        return report

    def classify_action_items(
        self,
        report: dict[str, Any],
    ) -> list[ActionItem]:
        """
        Classify action items into 3 processing tiers.

        Tier 1 (revenue-critical): drift, SLA breaches, breaking changes,
            API endpoints, authentication issues.
        Tier 2 (code-driven): signature changes, new/removed functions,
            webhooks, config options, stale docs.
        Tier 3 (community/search): everything else.

        Within each tier, items are sorted by frequency descending.

        Args:
            report: Parsed consolidated report dict.

        Returns:
            List of ActionItem objects sorted by tier then frequency.
        """
        raw_items = report.get("action_items", [])
        classified: list[ActionItem] = []

        for raw in raw_items:
            item = ActionItem(
                item_id=raw.get("id", ""),
                source_report=raw.get("source_report", ""),
                title=raw.get("title", ""),
                category=raw.get("category", ""),
                suggested_doc_type=raw.get("suggested_doc_type"),
                priority=raw.get("priority", "medium"),
                frequency=raw.get("frequency", 0),
                action_required=raw.get("action_required", ""),
                related_files=raw.get("related_files", []),
                context=raw.get("context", {}),
            )

            if (
                item.source_report in TIER_1_SOURCES
                or item.category in TIER_1_CATEGORIES
            ):
                item.tier = 1
            elif item.category in TIER_2_CATEGORIES:
                item.tier = 2
            else:
                item.tier = 3

            classified.append(item)

        classified.sort(key=lambda x: (x.tier, -x.frequency))

        tier_counts = {1: 0, 2: 0, 3: 0}
        for item in classified:
            tier_counts[item.tier] += 1

        logger.info(
            "Classified %d items: Tier 1=%d, Tier 2=%d, Tier 3=%d",
            len(classified),
            tier_counts[1],
            tier_counts[2],
            tier_counts[3],
        )

        return classified

    # ------------------------------------------------------------------
    # Plan lifecycle
    # ------------------------------------------------------------------

    def create_plan(
        self,
        report: dict[str, Any],
        action_items: list[ActionItem],
    ) -> dict[str, Any]:
        """
        Create an orchestration plan from classified action items.

        Each action item becomes a task with self-contained context
        including the item details, related files, and document type.

        Args:
            report: Parsed consolidated report dict.
            action_items: Classified and sorted action items.

        Returns:
            Plan dict ready for saving to disk.
        """
        health = report.get("health_summary", {})

        tasks = []
        for idx, item in enumerate(action_items):
            task = {
                "task_id": item.item_id,
                "sequence": idx,
                "status": "pending",
                "tier": item.tier,
                "full_context": {
                    "description": item.action_required,
                    "relevant_code": "",
                    "patterns_to_follow": self._get_patterns_for_category(item.category),
                    "antipatterns_to_avoid": self._get_antipatterns_for_category(item.category),
                    "dependencies": item.related_files,
                    "output_format": {
                        "content_type": item.suggested_doc_type or "how-to",
                        "title": item.title,
                        "description": item.action_required[:160],
                    },
                    "project_rules": "",
                },
                "result": None,
                "retry_count": 0,
                "max_retries": self.max_retries,
                "error_history": [],
            }
            tasks.append(task)

        plan = {
            "plan_id": f"doc-{health.get('quality_score', 0):.0f}-{len(tasks)}",
            "project": "auto-doc-pipeline",
            "status": "active",
            "health_summary": health,
            "tasks": tasks,
        }

        self._plan = plan
        logger.info(
            "Created plan %s with %d tasks",
            plan["plan_id"],
            len(tasks),
        )
        return plan

    def save_plan(self, plan: dict[str, Any]) -> Path:
        """
        Save the orchestration plan to disk as JSON.

        Args:
            plan: Plan dict to save.

        Returns:
            Path to the saved plan file.
        """
        plan_path = self.plan_dir / "current_plan.json"
        plan_path.write_text(
            json.dumps(plan, indent=2, default=str),
            encoding="utf-8",
        )
        logger.info("Saved plan to %s", plan_path)
        return plan_path

    def load_plan(self) -> dict[str, Any] | None:
        """
        Load an existing plan from disk.

        Returns:
            Plan dict or None if no plan file exists.
        """
        plan_path = self.plan_dir / "current_plan.json"
        if not plan_path.exists():
            return None
        content = plan_path.read_text(encoding="utf-8")
        plan: dict[str, Any] = json.loads(content)
        self._plan = plan
        return plan

    def delete_plan(self) -> None:
        """Delete the plan file after successful completion."""
        plan_path = self.plan_dir / "current_plan.json"
        if plan_path.exists():
            plan_path.unlink()
            logger.info("Deleted completed plan file")
        self._plan = None

    # ------------------------------------------------------------------
    # Subprocess execution
    # ------------------------------------------------------------------

    async def execute_task(
        self,
        task: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute a single documentation task in an isolated subprocess.

        Sends the task context to the worker process via stdin JSON
        and reads the result from stdout JSON.

        Args:
            task: Task dict with 'task_id' and 'full_context'.

        Returns:
            Subprocess protocol response dict.
        """
        request = {
            "protocol_version": "1.0",
            "task_id": task["task_id"],
            "command": "execute",
            "full_context": task["full_context"],
            "previous_attempt": (
                task["error_history"][-1] if task["error_history"] else None
            ),
        }

        request_json = json.dumps(request)

        try:
            process = await asyncio.create_subprocess_exec(
                "python", "-m", self.worker_script,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(input=request_json.encode("utf-8")),
                timeout=self.timeout_seconds,
            )

            if stderr_bytes:
                logger.debug(
                    "Task %s stderr: %s",
                    task["task_id"],
                    stderr_bytes.decode("utf-8", errors="replace")[:500],
                )

            if process.returncode != 0:
                error_msg = stderr_bytes.decode("utf-8", errors="replace")[:500]
                return {
                    "protocol_version": "1.0",
                    "task_id": task["task_id"],
                    "status": "failure",
                    "code": "",
                    "tests": "",
                    "self_check": {
                        "passed": False,
                        "error": f"Process exited with code {process.returncode}: {error_msg}",
                    },
                    "test_results": {},
                }

            response: dict[str, Any] = json.loads(
                stdout_bytes.decode("utf-8")
            )
            return response

        except asyncio.TimeoutError:
            logger.error(
                "Task %s timed out after %d seconds",
                task["task_id"],
                self.timeout_seconds,
            )
            return {
                "protocol_version": "1.0",
                "task_id": task["task_id"],
                "status": "failure",
                "code": "",
                "tests": "",
                "self_check": {
                    "passed": False,
                    "error": f"Timeout after {self.timeout_seconds}s",
                },
                "test_results": {},
            }
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Task %s execution error: %s", task["task_id"], exc)
            return {
                "protocol_version": "1.0",
                "task_id": task["task_id"],
                "status": "failure",
                "code": "",
                "tests": "",
                "self_check": {"passed": False, "error": str(exc)},
                "test_results": {},
            }

    async def execute_task_with_retries(
        self,
        task: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute a task with retry logic on failure.

        On each failure, the error is appended to error_history
        and passed to the next subprocess as previous_attempt
        context for self-correction.

        Args:
            task: Task dict with 'task_id', 'full_context', etc.

        Returns:
            Final subprocess protocol response dict.
        """
        max_retries = task.get("max_retries", self.max_retries)

        for attempt in range(max_retries + 1):
            task["status"] = "running"
            task["retry_count"] = attempt

            response = await self.execute_task(task)

            if response.get("status") == "success":
                task["status"] = "completed"
                task["result"] = response
                return response

            error_msg = (
                response.get("self_check", {}).get("error", "")
                or f"Attempt {attempt + 1} failed"
            )
            task["error_history"].append(error_msg)

            if attempt < max_retries:
                logger.info(
                    "Task %s failed (attempt %d/%d), retrying: %s",
                    task["task_id"],
                    attempt + 1,
                    max_retries + 1,
                    error_msg[:200],
                )
            else:
                task["status"] = "failed"
                task["result"] = response
                logger.warning(
                    "Task %s exhausted all %d retries",
                    task["task_id"],
                    max_retries + 1,
                )

        return response

    # ------------------------------------------------------------------
    # Full orchestration
    # ------------------------------------------------------------------

    async def process_consolidated_report(
        self,
        report_path: Path,
    ) -> DocOrchestrationSummary:
        """
        Process an entire consolidated report end-to-end.

        Loads the report, classifies action items into tiers,
        creates a plan, executes each task in a subprocess,
        stores patterns, and produces a summary.

        Args:
            report_path: Path to consolidated_report.json.

        Returns:
            DocOrchestrationSummary with processing results.
        """
        summary = DocOrchestrationSummary()

        report = self.load_report(report_path)
        health = report.get("health_summary", {})
        summary.quality_score = health.get("quality_score", 0.0)
        summary.drift_status = health.get("drift_status", "ok")
        summary.sla_status = health.get("sla_status", "ok")

        if summary.sla_status == "breach":
            logger.warning("SLA breach detected in consolidated report")
        if summary.drift_status == "drift":
            logger.warning("API/SDK drift detected in consolidated report")

        action_items = self.classify_action_items(report)
        summary.total_action_items = len(action_items)

        plan = self.create_plan(report, action_items)
        self.save_plan(plan)

        for task in plan["tasks"]:
            tier = task.get("tier", 2)
            task_result = DocTaskResult(item_id=task["task_id"])

            response = await self.execute_task_with_retries(task)

            if response.get("status") == "success":
                task_result.status = "completed"
                task_result.self_check_score = (
                    response.get("self_check", {}).get("score", 0.0)
                )
                task_result.lint_attempts = task.get("retry_count", 0) + 1

                self._store_success_pattern(task, response)

                if tier == 1:
                    summary.tier_1_processed += 1
                elif tier == 2:
                    summary.tier_2_processed += 1
                else:
                    summary.tier_3_processed += 1

                summary.documents_created += 1
            else:
                task_result.status = "blocked"
                task_result.errors = task.get("error_history", [])

                self._store_failure_pattern(task, response)

                if tier == 1:
                    summary.tier_1_blocked += 1
                elif tier == 2:
                    summary.tier_2_blocked += 1
                else:
                    summary.tier_3_blocked += 1

                summary.blocked_items.append(task["task_id"])

            summary.lint_retries_total += task.get("retry_count", 0)
            summary.results.append(task_result)

        self.delete_plan()

        logger.info(
            "Orchestration complete: %d processed, %d blocked",
            (summary.tier_1_processed + summary.tier_2_processed + summary.tier_3_processed),
            len(summary.blocked_items),
        )

        return summary

    # ------------------------------------------------------------------
    # Pattern store helpers
    # ------------------------------------------------------------------

    def _get_patterns_for_category(self, category: str) -> list[str]:
        """
        Get successful patterns relevant to a document category.

        Args:
            category: Action item category.

        Returns:
            List of pattern code snippets.
        """
        if not self.pattern_store:
            return []
        try:
            patterns = self.pattern_store.get_top_patterns(
                category=category,
                limit=3,
                min_score=80.0,
            )
            return [p.code_snippet for p in patterns]
        except (Exception,):
            logger.debug("Failed to load patterns for category %s", category)
            return []

    def _get_antipatterns_for_category(self, category: str) -> list[str]:
        """
        Get antipatterns to avoid for a document category.

        Args:
            category: Action item category.

        Returns:
            List of antipattern code snippets.
        """
        if not self.pattern_store:
            return []
        try:
            antipatterns = self.pattern_store.get_antipatterns(
                category=category,
                limit=3,
            )
            return [a.code_snippet for a in antipatterns]
        except (Exception,):
            logger.debug("Failed to load antipatterns for category %s", category)
            return []

    def _store_success_pattern(
        self,
        task: dict[str, Any],
        response: dict[str, Any],
    ) -> None:
        """
        Store a successful document generation as a pattern.

        Args:
            task: Completed task dict.
            response: Subprocess response dict.
        """
        if not self.pattern_store:
            return
        try:
            context_desc = task.get("full_context", {}).get("description", "")
            output_format = task.get("full_context", {}).get("output_format", {})
            self.pattern_store.add_pattern(
                code=response.get("code", "")[:500],
                context=context_desc[:200],
                category=output_format.get("content_type", "content"),
                score=response.get("self_check", {}).get("score", 0.0),
                metadata={
                    "task_id": task["task_id"],
                    "template_id": response.get("test_results", {}).get("template_id", ""),
                    "tier": task.get("tier", 2),
                },
            )
        except (Exception,):
            logger.debug("Failed to store success pattern for %s", task["task_id"])

    def _store_failure_pattern(
        self,
        task: dict[str, Any],
        response: dict[str, Any],
    ) -> None:
        """
        Store a failed document generation as an antipattern.

        Args:
            task: Failed task dict.
            response: Subprocess response dict.
        """
        if not self.pattern_store:
            return
        try:
            context_desc = task.get("full_context", {}).get("description", "")
            output_format = task.get("full_context", {}).get("output_format", {})
            self.pattern_store.add_antipattern(
                code=response.get("code", "")[:500],
                context=context_desc[:200],
                category=output_format.get("content_type", "content"),
                error_messages=task.get("error_history", []),
                metadata={
                    "task_id": task["task_id"],
                    "tier": task.get("tier", 2),
                },
            )
        except (Exception,):
            logger.debug("Failed to store failure pattern for %s", task["task_id"])

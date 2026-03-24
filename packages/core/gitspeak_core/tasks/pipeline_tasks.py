"""Celery tasks for async pipeline execution.

Tasks:
- run_pipeline_async: execute full 3-phase pipeline in background
- check_scheduled_runs: periodic task to trigger scheduled pipelines
- run_llm_generation: Phase 2 LLM doc generation (Claude + Groq/DeepSeek)
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone

from gitspeak_core.tasks.celery_app import app

logger = logging.getLogger(__name__)


@app.task(bind=True, name="gitspeak_core.tasks.pipeline_tasks.run_pipeline_async")
def run_pipeline_async(
    self,
    user_id: str,
    run_id: str,
    repo_path: str,
    flow_mode: str = "code-first",
    modules: dict[str, bool] | None = None,
    protocols: list[str] | None = None,
    user_tier: str = "free",
):
    """Execute the full pipeline asynchronously.

    Updates PipelineRun record in DB with progress and results.
    """
    from gitspeak_core.api.pipeline import RunPipelineRequest, handle_run_pipeline
    from gitspeak_core.db.engine import get_session
    from gitspeak_core.db.models import PipelineRun

    session = get_session()
    try:
        # Mark run as started
        run = session.query(PipelineRun).filter(PipelineRun.id == run_id).first()
        if run:
            run.status = "running"
            run.started_at = datetime.now(timezone.utc)
            run.celery_task_id = self.request.id
            session.commit()

        # Build request
        request = RunPipelineRequest(
            repo_path=repo_path,
            flow_mode=flow_mode,
            modules=modules,
            protocols=protocols,
        )

        # Execute pipeline
        start = time.monotonic()
        response = handle_run_pipeline(request, user_tier=user_tier)
        duration = time.monotonic() - start

        # Save results
        if run:
            run.status = "completed" if response.status == "ok" else "failed"
            run.phases = [p.model_dump() for p in response.phases]
            run.artifacts = response.artifacts
            run.errors = response.errors
            run.report = response.report
            run.duration_seconds = duration
            run.completed_at = datetime.now(timezone.utc)
            session.commit()

        # Increment usage
        from gitspeak_core.api.billing import increment_usage

        increment_usage(user_id, "api_calls", 1, session)
        if response.report:
            pages = response.report.get("docs_generated", 0)
            if pages:
                increment_usage(user_id, "pages", pages, session)

        return {
            "run_id": run_id,
            "status": response.status,
            "phases": len(response.phases),
            "duration": duration,
        }

    except Exception as exc:
        logger.exception("Pipeline task failed: run_id=%s", run_id)
        if run:
            run.status = "failed"
            run.errors = [str(exc)]
            run.completed_at = datetime.now(timezone.utc)
            session.commit()
        raise
    finally:
        session.close()


@app.task(bind=True, name="gitspeak_core.tasks.pipeline_tasks.run_llm_generation")
def run_llm_generation(
    self,
    user_id: str,
    run_id: str,
    repo_path: str,
    consolidated_report_path: str,
    user_tier: str = "free",
):
    """Phase 2: LLM-powered doc generation using orchestrator.

    Uses Claude as planner/verifier, Groq/DeepSeek as content generators.
    GSD pattern: fresh context per task, atomic tasks with verification.
    """
    from gitspeak_core.db.engine import get_session
    from gitspeak_core.db.models import PipelineRun
    from gitspeak_core.docs.orchestrator import DocOrchestrator

    session = get_session()
    try:
        run = session.query(PipelineRun).filter(PipelineRun.id == run_id).first()

        orchestrator = DocOrchestrator(
            repo_root=repo_path,
            consolidated_report_path=consolidated_report_path,
        )

        # Load and classify action items
        orchestrator.load_report()
        plan = orchestrator.create_plan()

        # Execute each task (subprocess workers with LLM)
        summary = orchestrator.execute_plan(plan)

        if run:
            run.report = run.report or {}
            run.report["generation_summary"] = {
                "total_tasks": summary.total_tasks,
                "succeeded": summary.succeeded,
                "failed": summary.failed,
                "docs_generated": summary.docs_generated,
            }
            session.commit()

        # Increment usage
        from gitspeak_core.api.billing import increment_usage

        increment_usage(user_id, "ai_requests", summary.total_tasks, session)
        increment_usage(user_id, "pages", summary.docs_generated, session)

        return {
            "run_id": run_id,
            "tasks": summary.total_tasks,
            "succeeded": summary.succeeded,
            "docs_generated": summary.docs_generated,
        }

    except Exception as exc:
        logger.exception("LLM generation failed: run_id=%s", run_id)
        raise
    finally:
        session.close()


@app.task(name="gitspeak_core.tasks.pipeline_tasks.check_scheduled_runs")
def check_scheduled_runs():
    """Periodic task: check automation schedules and trigger due pipelines.

    Runs every 60 seconds via Celery beat.
    """
    from gitspeak_core.db.engine import get_session
    from gitspeak_core.db.models import AutomationSchedule, PipelineRun, User

    session = get_session()
    try:
        now = datetime.now(timezone.utc)

        # Find schedules that are due
        due_schedules = (
            session.query(AutomationSchedule)
            .filter(
                AutomationSchedule.enabled.is_(True),
                AutomationSchedule.next_run_at <= now,
            )
            .all()
        )

        triggered = 0
        for schedule in due_schedules:
            user = session.query(User).filter(User.id == schedule.user_id).first()
            if not user or not user.is_active:
                continue

            tier = "free"
            if user.subscription:
                tier = user.subscription.tier

            # Check quota
            from gitspeak_core.api.billing import check_quota

            if not check_quota(user.id, "api_calls", session):
                logger.info(
                    "Skipping schedule %s: quota exceeded for user %s",
                    schedule.id,
                    user.id,
                )
                continue

            # Create pipeline run record
            config = schedule.pipeline_config or {}
            run = PipelineRun(
                user_id=user.id,
                schedule_id=schedule.id,
                status="pending",
                trigger="scheduled",
                repo_path=config.get("repo_path", ""),
                flow_mode=config.get("flow_mode", "code-first"),
            )
            session.add(run)
            session.flush()

            # Dispatch async task
            run_pipeline_async.delay(
                user_id=user.id,
                run_id=run.id,
                repo_path=config.get("repo_path", ""),
                flow_mode=config.get("flow_mode", "code-first"),
                modules=config.get("modules"),
                protocols=config.get("protocols"),
                user_tier=tier,
            )

            # Update schedule
            schedule.last_run_at = now
            schedule.next_run_at = _calculate_next_run(schedule.cron_expr, now)
            triggered += 1

        session.commit()

        if triggered:
            logger.info("Triggered %d scheduled pipeline runs", triggered)

        return {"triggered": triggered}

    except Exception:
        logger.exception("Failed to check scheduled runs")
        session.rollback()
        raise
    finally:
        session.close()


def _calculate_next_run(cron_expr: str, after: datetime) -> datetime:
    """Calculate next run time from cron expression.

    Falls back to 24h from now if croniter is not available.
    """
    try:
        from croniter import croniter

        cron = croniter(cron_expr, after)
        return cron.get_next(datetime)
    except ImportError:
        return after + timedelta(hours=24)

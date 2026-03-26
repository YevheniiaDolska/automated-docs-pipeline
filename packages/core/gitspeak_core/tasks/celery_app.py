"""Celery application configuration for VeriDoc.

Broker: Redis (default redis://localhost:6379/0)
Backend: Redis (same instance, db 1)

Start worker:
    celery -A gitspeak_core.tasks.celery_app worker --loglevel=info

Start beat (scheduler):
    celery -A gitspeak_core.tasks.celery_app beat --loglevel=info
"""

from __future__ import annotations

import os

from celery import Celery

REDIS_URL = os.environ.get("VERIDOC_REDIS_URL", "redis://localhost:6379/0")
REDIS_BACKEND = os.environ.get("VERIDOC_REDIS_BACKEND", "redis://localhost:6379/1")

app = Celery(
    "veridoc",
    broker=REDIS_URL,
    backend=REDIS_BACKEND,
    include=[
        "gitspeak_core.tasks.pipeline_tasks",
    ],
)

app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Task settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 min soft limit
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # one task at a time per worker
    # Result expiry
    result_expires=86400,  # 24 hours
    # Retry
    task_default_retry_delay=60,
    task_max_retries=3,
    # Beat schedule (for automation schedules)
    beat_schedule={
        "check-automation-schedules": {
            "task": "gitspeak_core.tasks.pipeline_tasks.check_scheduled_runs",
            "schedule": 60.0,  # every minute
        },
        "process-referral-payouts": {
            "task": "gitspeak_core.tasks.pipeline_tasks.process_referral_payouts",
            "schedule": 3600.0,  # every hour
        },
    },
)

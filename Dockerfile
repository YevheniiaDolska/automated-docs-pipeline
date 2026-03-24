FROM python:3.12-slim AS base

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY packages/ ./packages/
COPY scripts/ ./scripts/
COPY templates/ ./templates/
COPY runtime/ ./runtime/
COPY config/ ./config/

# Environment
ENV PYTHONPATH=/app/packages/core:/app/scripts
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# ---- API Server ----
FROM base AS api
CMD ["uvicorn", "gitspeak_core.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# ---- Celery Worker ----
FROM base AS worker
CMD ["celery", "-A", "gitspeak_core.tasks.celery_app", "worker", "--loglevel=info", "--concurrency=2"]

# ---- Celery Beat (Scheduler) ----
FROM base AS beat
CMD ["celery", "-A", "gitspeak_core.tasks.celery_app", "beat", "--loglevel=info"]

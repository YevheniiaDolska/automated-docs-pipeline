"""VeriDoc SaaS -- FastAPI application.

Main entry point for the VeriDoc API server.

Start server:
    uvicorn gitspeak_core.api.app:app --host 0.0.0.0 --port 8000

Production:
    gunicorn gitspeak_core.api.app:app -w 4 -k uvicorn.workers.UvicornWorker
"""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

import jwt

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from gitspeak_core.config.settings import AppSettings, get_default_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application settings (singleton)
# ---------------------------------------------------------------------------

_settings: AppSettings | None = None


def get_settings() -> AppSettings:
    global _settings
    if _settings is None:
        _settings = get_default_settings()
    return _settings


# ---------------------------------------------------------------------------
# Database session dependency
# ---------------------------------------------------------------------------


def get_db():
    """FastAPI dependency: yield a DB session, auto-close after request."""
    from gitspeak_core.db.engine import get_session

    session = get_session()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------


MAX_TOKEN_LENGTH_BYTES: int = 8192


def get_current_user(
    request: Request,
    authorization: str = Header(None),
    settings: AppSettings = Depends(get_settings),
    db=Depends(get_db),
) -> dict[str, Any]:
    """Extract and validate JWT token from Authorization header.

    Validates token format, length, signature, and expiration.
    Logs authentication failures with the client IP address for
    audit purposes.

    Args:
        request: Incoming HTTP request (used for client IP logging).
        authorization: Authorization header value.
        settings: Application settings with secret key.
        db: Database session dependency.

    Returns:
        Dictionary with user_id, email, and tier.

    Raises:
        HTTPException: 401 if authentication fails for any reason.
    """
    client_ip = request.client.host if request.client else "unknown"

    if not authorization or not authorization.startswith("Bearer "):
        logger.warning(
            "Auth failure: missing or malformed Authorization header, "
            "client_ip=%s",
            client_ip,
        )
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = authorization.split(" ", 1)[1]

    if len(token.encode("utf-8")) > MAX_TOKEN_LENGTH_BYTES:
        logger.warning(
            "Auth failure: token exceeds maximum length of %s bytes, "
            "client_ip=%s",
            MAX_TOKEN_LENGTH_BYTES,
            client_ip,
        )
        raise HTTPException(status_code=401, detail="Token too large")

    from gitspeak_core.api.auth import decode_access_token

    try:
        token_claims = decode_access_token(
            token, settings.secret_key.get_secret_value()
        )
    except jwt.ExpiredSignatureError:
        logger.warning(
            "Auth failure: expired token, client_ip=%s",
            client_ip,
        )
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as exc:
        logger.warning(
            "Auth failure: invalid token (%s), client_ip=%s",
            type(exc).__name__,
            client_ip,
        )
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = token_claims.get("sub")
    if not user_id:
        logger.warning(
            "Auth failure: token missing 'sub' claim, client_ip=%s",
            client_ip,
        )
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Verify user exists and is active
    from gitspeak_core.db.models import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        logger.warning(
            "Auth failure: user not found or deactivated, "
            "user_id=%s, client_ip=%s",
            user_id,
            client_ip,
        )
        raise HTTPException(status_code=401, detail="User not found or deactivated")

    tier = "free"
    if user.subscription:
        tier = user.subscription.tier

    return {
        "user_id": user.id,
        "email": user.email,
        "tier": tier,
    }


# ---------------------------------------------------------------------------
# Rate limiting (in-memory, per-user)
# ---------------------------------------------------------------------------

_rate_limit_store: dict[str, list[float]] = defaultdict(list)

# Requests per minute by tier
TIER_RATE_LIMITS: dict[str, int] = {
    "free": 10,
    "starter": 30,
    "pro": 60,
    "business": 120,
    "enterprise": 300,
}


def check_rate_limit(user: dict[str, Any]) -> None:
    """Enforce per-user rate limiting based on tier."""
    user_id = user["user_id"]
    tier = user.get("tier", "free")
    limit = TIER_RATE_LIMITS.get(tier, 10)

    now = time.time()
    window = 60.0  # 1 minute
    timestamps = _rate_limit_store[user_id]

    # Remove old timestamps
    _rate_limit_store[user_id] = [ts for ts in timestamps if now - ts < window]

    if len(_rate_limit_store[user_id]) >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({limit} requests/minute for {tier} tier)",
            headers={"Retry-After": "60"},
        )

    _rate_limit_store[user_id].append(now)


# ---------------------------------------------------------------------------
# Lifespan: startup / shutdown
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    settings = get_settings()
    logger.info(
        "VeriDoc API starting: env=%s, port=%s", settings.environment, settings.port
    )

    # Create tables (dev only; use Alembic in production)
    if settings.environment == "development":
        from gitspeak_core.db.engine import get_engine
        from gitspeak_core.db.models import create_all_tables

        create_all_tables(get_engine(settings))
        logger.info("Database tables created (development mode)")

    yield

    # Shutdown
    from gitspeak_core.db.engine import reset_engine

    reset_engine()
    logger.info("VeriDoc API shutdown")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="VeriDoc API",
    description="VeriDoc SaaS Documentation Pipeline API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("VERIDOC_CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------------------------


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(
        "%s %s -> %d (%.3fs)",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )
    return response


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "veridoc-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health/ready")
async def readiness_check(db=Depends(get_db)):
    """Check database connectivity."""
    try:
        from sqlalchemy import text

        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": str(exc)},
        )


# =========================================================================
# AUTH ROUTES
# =========================================================================


@app.post("/auth/register", tags=["auth"])
async def register_user(request: Request, db=Depends(get_db)):
    """Register a new user."""
    from gitspeak_core.api.auth import RegisterRequest, handle_register

    body = await request.json()
    try:
        req = RegisterRequest(**body)
        result = handle_register(req, db)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/auth/login", tags=["auth"])
async def login_user(request: Request, db=Depends(get_db)):
    """Authenticate and receive JWT token."""
    from gitspeak_core.api.auth import LoginRequest, handle_login

    body = await request.json()
    try:
        req = LoginRequest(**body)
        result = handle_login(req, db)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@app.get("/auth/me", tags=["auth"])
async def get_me(
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get current user profile."""
    from gitspeak_core.api.auth import handle_get_profile

    try:
        result = handle_get_profile(user["user_id"], db)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# =========================================================================
# PIPELINE ROUTES
# =========================================================================


class PipelineRunRequest(BaseModel):
    """Request to start a pipeline run (async via Celery)."""

    model_config = ConfigDict(extra="forbid")

    repo_path: str = Field(description="Path to repository root")
    flow_mode: str = Field(default="code-first")
    modules: dict[str, bool] | None = None
    protocols: list[str] | None = None
    doc_scope: str = "standard"


@app.post("/pipeline/run", tags=["pipeline"])
async def start_pipeline_run(
    request: PipelineRunRequest,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Start an async pipeline run. Returns run_id for status polling."""
    check_rate_limit(user)

    from gitspeak_core.api.billing import check_quota

    if not check_quota(user["user_id"], "api_calls", db):
        raise HTTPException(status_code=402, detail="API call quota exceeded")

    from gitspeak_core.db.models import PipelineRun

    run = PipelineRun(
        user_id=user["user_id"],
        status="pending",
        trigger="manual",
        repo_path=request.repo_path,
        flow_mode=request.flow_mode,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Dispatch to Celery
    try:
        from gitspeak_core.tasks.pipeline_tasks import run_pipeline_async

        task = run_pipeline_async.delay(
            user_id=user["user_id"],
            run_id=run.id,
            repo_path=request.repo_path,
            flow_mode=request.flow_mode,
            modules=request.modules,
            protocols=request.protocols,
            user_tier=user["tier"],
        )
        run.celery_task_id = task.id
        db.commit()
    except Exception:
        # Celery not available -- run synchronously as fallback
        logger.warning("Celery not available, running pipeline synchronously")
        from gitspeak_core.api.pipeline import RunPipelineRequest, handle_run_pipeline

        req = RunPipelineRequest(
            repo_path=request.repo_path,
            flow_mode=request.flow_mode,
            modules=request.modules,
            protocols=request.protocols,
        )
        result = handle_run_pipeline(req, user_tier=user["tier"])
        run.status = "completed" if result.status == "ok" else "failed"
        run.phases = [p.model_dump() for p in result.phases]
        run.artifacts = result.artifacts
        run.errors = result.errors
        run.report = result.report
        run.completed_at = datetime.now(timezone.utc)
        db.commit()

    return {
        "run_id": run.id,
        "status": run.status,
        "message": "Pipeline run queued",
    }


@app.get("/pipeline/runs", tags=["pipeline"])
async def list_pipeline_runs(
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    """List pipeline runs for current user."""
    from gitspeak_core.db.models import PipelineRun

    runs = (
        db.query(PipelineRun)
        .filter(PipelineRun.user_id == user["user_id"])
        .order_by(PipelineRun.created_at.desc())
        .offset(offset)
        .limit(min(limit, 100))
        .all()
    )

    return {
        "runs": [
            {
                "id": r.id,
                "status": r.status,
                "trigger": r.trigger,
                "flow_mode": r.flow_mode,
                "duration_seconds": r.duration_seconds,
                "quality_score": r.quality_score,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in runs
        ]
    }


@app.get("/pipeline/runs/{run_id}", tags=["pipeline"])
async def get_pipeline_run(
    run_id: str,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get details of a specific pipeline run."""
    from gitspeak_core.db.models import PipelineRun

    run = (
        db.query(PipelineRun)
        .filter(PipelineRun.id == run_id, PipelineRun.user_id == user["user_id"])
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return {
        "id": run.id,
        "status": run.status,
        "trigger": run.trigger,
        "flow_mode": run.flow_mode,
        "phases": run.phases or [],
        "artifacts": run.artifacts or [],
        "errors": run.errors or [],
        "report": run.report,
        "quality_score": run.quality_score,
        "duration_seconds": run.duration_seconds,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


# =========================================================================
# SETTINGS ROUTES
# =========================================================================


@app.get("/settings", tags=["settings"])
async def get_pipeline_settings(
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get pipeline settings for current user."""
    from gitspeak_core.db.models import PipelineSettings as PipelineSettingsModel

    settings = (
        db.query(PipelineSettingsModel)
        .filter(PipelineSettingsModel.user_id == user["user_id"])
        .first()
    )

    if not settings:
        # Return defaults
        return {
            "modules": {},
            "flow_mode": "code-first",
            "default_protocols": ["rest"],
            "algolia_enabled": False,
            "sandbox_backend": "external",
        }

    return {
        "modules": settings.modules or {},
        "flow_mode": settings.flow_mode,
        "default_protocols": settings.default_protocols or ["rest"],
        "algolia_enabled": settings.algolia_enabled,
        "algolia_config": settings.algolia_config,
        "sandbox_backend": settings.sandbox_backend,
        "repo_path": settings.repo_path,
    }


@app.put("/settings", tags=["settings"])
async def update_pipeline_settings(
    request: Request,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Update pipeline settings."""
    body = await request.json()

    from gitspeak_core.api.settings import AVAILABLE_MODULES
    from gitspeak_core.db.models import PipelineSettings as PipelineSettingsModel

    settings = (
        db.query(PipelineSettingsModel)
        .filter(PipelineSettingsModel.user_id == user["user_id"])
        .first()
    )

    if not settings:
        settings = PipelineSettingsModel(user_id=user["user_id"])
        db.add(settings)

    # Validate module tier access
    user_tier = user["tier"]
    tier_order = ["free", "starter", "pro", "business", "enterprise"]
    user_tier_idx = tier_order.index(user_tier) if user_tier in tier_order else 0

    if "modules" in body:
        modules = body["modules"]
        # Filter out modules user does not have access to
        min_tiers = {m["key"]: m["min_tier"] for m in AVAILABLE_MODULES}
        validated = {}
        for key, enabled in modules.items():
            min_tier = min_tiers.get(key, "enterprise")
            min_idx = tier_order.index(min_tier) if min_tier in tier_order else 4
            if user_tier_idx >= min_idx:
                validated[key] = enabled
        settings.modules = validated

    if "flow_mode" in body:
        settings.flow_mode = body["flow_mode"]
    if "default_protocols" in body:
        settings.default_protocols = body["default_protocols"]
    if "algolia_enabled" in body:
        settings.algolia_enabled = body["algolia_enabled"]
    if "algolia_config" in body:
        settings.algolia_config = body["algolia_config"]
    if "sandbox_backend" in body:
        settings.sandbox_backend = body["sandbox_backend"]
    if "repo_path" in body:
        settings.repo_path = body["repo_path"]

    db.commit()

    return {"status": "ok", "message": "Settings updated"}


@app.get("/settings/modules", tags=["settings"])
async def list_modules(user: dict = Depends(get_current_user)):
    """List available modules with tier gating info."""
    from gitspeak_core.api.settings import AVAILABLE_MODULES

    tier_order = ["free", "starter", "pro", "business", "enterprise"]
    user_tier = user["tier"]
    user_idx = tier_order.index(user_tier) if user_tier in tier_order else 0

    result = []
    for mod in AVAILABLE_MODULES:
        min_idx = tier_order.index(mod["min_tier"]) if mod["min_tier"] in tier_order else 4
        result.append(
            {
                **mod,
                "available": user_idx >= min_idx,
            }
        )

    return {"modules": result, "user_tier": user_tier}


# =========================================================================
# AUTOMATION SCHEDULE ROUTES
# =========================================================================


class CreateScheduleRequest(BaseModel):
    """Request to create an automation schedule."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(max_length=200)
    cron_expr: str = Field(description="Cron expression (e.g., '0 3 * * 1')")
    pipeline_config: dict[str, Any] | None = None


@app.post("/automation/schedules", tags=["automation"])
async def create_schedule(
    request: CreateScheduleRequest,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Create a new automation schedule (Pro+ tier)."""
    tier_order = ["free", "starter", "pro", "business", "enterprise"]
    if tier_order.index(user.get("tier", "free")) < 2:  # pro = index 2
        raise HTTPException(
            status_code=403, detail="Automation requires Pro tier or higher"
        )

    from gitspeak_core.db.models import AutomationSchedule

    schedule = AutomationSchedule(
        user_id=user["user_id"],
        name=request.name,
        cron_expr=request.cron_expr,
        pipeline_config=request.pipeline_config,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    return {
        "id": schedule.id,
        "name": schedule.name,
        "cron_expr": schedule.cron_expr,
        "enabled": schedule.enabled,
    }


@app.get("/automation/schedules", tags=["automation"])
async def list_schedules(
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """List automation schedules."""
    from gitspeak_core.db.models import AutomationSchedule

    schedules = (
        db.query(AutomationSchedule)
        .filter(AutomationSchedule.user_id == user["user_id"])
        .all()
    )

    return {
        "schedules": [
            {
                "id": s.id,
                "name": s.name,
                "cron_expr": s.cron_expr,
                "enabled": s.enabled,
                "last_run_at": s.last_run_at.isoformat() if s.last_run_at else None,
                "next_run_at": s.next_run_at.isoformat() if s.next_run_at else None,
            }
            for s in schedules
        ]
    }


@app.put("/automation/schedules/{schedule_id}", tags=["automation"])
async def update_schedule(
    schedule_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Update an automation schedule."""
    from gitspeak_core.db.models import AutomationSchedule

    schedule = (
        db.query(AutomationSchedule)
        .filter(
            AutomationSchedule.id == schedule_id,
            AutomationSchedule.user_id == user["user_id"],
        )
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    body = await request.json()
    if "name" in body:
        schedule.name = body["name"]
    if "cron_expr" in body:
        schedule.cron_expr = body["cron_expr"]
    if "enabled" in body:
        schedule.enabled = body["enabled"]
    if "pipeline_config" in body:
        schedule.pipeline_config = body["pipeline_config"]

    db.commit()
    return {"status": "ok"}


@app.delete("/automation/schedules/{schedule_id}", tags=["automation"])
async def delete_schedule(
    schedule_id: str,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Delete an automation schedule."""
    from gitspeak_core.db.models import AutomationSchedule

    schedule = (
        db.query(AutomationSchedule)
        .filter(
            AutomationSchedule.id == schedule_id,
            AutomationSchedule.user_id == user["user_id"],
        )
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    db.delete(schedule)
    db.commit()
    return {"status": "ok"}


# =========================================================================
# BILLING ROUTES (LemonSqueezy)
# =========================================================================


@app.post("/billing/checkout", tags=["billing"])
async def create_checkout(
    request: Request,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Create a LemonSqueezy checkout URL."""
    from gitspeak_core.api.billing import CreateCheckoutRequest, handle_create_checkout

    body = await request.json()
    try:
        req = CreateCheckoutRequest(**body)
        result = handle_create_checkout(req, user["user_id"], user["email"], db)
        return result.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/billing/portal", tags=["billing"])
async def get_portal(
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get LemonSqueezy customer portal URL."""
    from gitspeak_core.api.billing import handle_get_portal_url

    try:
        result = handle_get_portal_url(user["user_id"], db)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/billing/usage", tags=["billing"])
async def get_usage(
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get current billing period usage."""
    from gitspeak_core.api.billing import handle_get_usage

    try:
        result = handle_get_usage(user["user_id"], db)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/billing/webhooks/lemonsqueezy", tags=["billing"])
async def lemonsqueezy_webhook(request: Request, db=Depends(get_db)):
    """Handle LemonSqueezy webhook events.

    Verifies HMAC signature and processes subscription lifecycle events.
    """
    from gitspeak_core.api.billing import handle_webhook, verify_webhook_signature

    payload = await request.body()
    signature = request.headers.get("x-signature", "")

    if not verify_webhook_signature(payload, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    body = await request.json()
    event_name = body.get("meta", {}).get("event_name", "")
    event_data = body.get("data", {})

    result = handle_webhook(event_name, event_data, db)
    return result


# =========================================================================
# AUDIT LOG ROUTES
# =========================================================================


@app.get("/audit-log", tags=["admin"])
async def get_audit_log(
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """Get audit log entries for current user."""
    from gitspeak_core.db.models import AuditLog

    entries = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == user["user_id"])
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(min(limit, 200))
        .all()
    )

    return {
        "entries": [
            {
                "id": e.id,
                "action": e.action,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "details": e.details,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ]
    }


# ---------------------------------------------------------------------------
# Audit log helper
# ---------------------------------------------------------------------------


def log_audit(
    db,
    user_id: str | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> None:
    """Write an audit log entry."""
    from gitspeak_core.db.models import AuditLog

    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()

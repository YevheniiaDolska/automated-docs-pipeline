"""SQLAlchemy ORM models for VeriDoc SaaS.

Tables:
- users: user accounts with auth credentials
- subscriptions: Stripe billing state per user
- pipeline_settings: per-user pipeline configuration
- automation_schedules: scheduled pipeline runs
- pipeline_runs: execution history with phase details
- audit_log: compliance and security event log
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


def _utcnow() -> datetime:
    """Return current UTC timestamp for ORM default fields."""
    return datetime.now(timezone.utc)


def _new_id() -> str:
    """Generate compact random hex identifier for primary keys."""
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    """Shared declarative base for all VeriDoc models."""


# -----------------------------------------------------------------------
# Users
# -----------------------------------------------------------------------


class User(Base):
    __tablename__ = "users"

    id = Column(String(32), primary_key=True, default=_new_id)
    email = Column(String(320), unique=True, nullable=False, index=True)
    hashed_password = Column(String(128), nullable=False)
    full_name = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    # Relationships
    subscription = relationship(
        "Subscription", back_populates="user", uselist=False, cascade="all, delete"
    )
    settings = relationship(
        "PipelineSettings",
        back_populates="user",
        uselist=False,
        cascade="all, delete",
    )
    runs = relationship("PipelineRun", back_populates="user", cascade="all, delete")
    schedules = relationship(
        "AutomationSchedule", back_populates="user", cascade="all, delete"
    )
    referral_profile = relationship(
        "ReferralProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete",
        foreign_keys="ReferralProfile.user_id",
    )
    referrals_made = relationship(
        "ReferralAttribution",
        back_populates="referrer",
        cascade="all, delete",
        foreign_keys="ReferralAttribution.referrer_user_id",
    )
    referral_source = relationship(
        "ReferralAttribution",
        back_populates="referred",
        uselist=False,
        cascade="all, delete",
        foreign_keys="ReferralAttribution.referred_user_id",
    )


# -----------------------------------------------------------------------
# Subscriptions (LemonSqueezy billing)
# -----------------------------------------------------------------------


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(32), primary_key=True, default=_new_id)
    user_id = Column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    tier = Column(String(20), nullable=False, default="free")  # free/starter/pro/business/enterprise
    # LemonSqueezy identifiers
    ls_customer_id = Column(String(64), nullable=True, index=True)
    ls_subscription_id = Column(String(64), nullable=True, unique=True)
    ls_variant_id = Column(String(64), nullable=True)
    status = Column(String(20), nullable=False, default="trialing")  # trialing/active/past_due/canceled/unpaid/paused
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    # Usage tracking
    ai_requests_used = Column(Integer, default=0, nullable=False)
    ai_requests_limit = Column(Integer, default=50, nullable=False)  # per billing period
    pages_generated = Column(Integer, default=0, nullable=False)
    api_calls_used = Column(Integer, default=0, nullable=False)

    user = relationship("User", back_populates="subscription")

    __table_args__ = (
        Index("ix_subscriptions_ls_sub", "ls_subscription_id"),
    )


# -----------------------------------------------------------------------
# Pipeline settings (per-user)
# -----------------------------------------------------------------------


class PipelineSettings(Base):
    __tablename__ = "pipeline_settings"

    id = Column(String(32), primary_key=True, default=_new_id)
    user_id = Column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    modules = Column(JSON, nullable=False, default=dict)  # {"gap_detection": true, ...}
    flow_mode = Column(String(20), nullable=False, default="code-first")
    default_protocols = Column(JSON, nullable=False, default=list)  # ["rest"]
    algolia_enabled = Column(Boolean, default=False, nullable=False)
    algolia_config = Column(JSON, nullable=True)
    sandbox_backend = Column(String(20), nullable=False, default="external")
    repo_path = Column(String(500), nullable=True)
    custom_config = Column(JSON, nullable=True)  # extensible config bag
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    user = relationship("User", back_populates="settings")


# -----------------------------------------------------------------------
# Automation schedules
# -----------------------------------------------------------------------


class AutomationSchedule(Base):
    __tablename__ = "automation_schedules"

    id = Column(String(32), primary_key=True, default=_new_id)
    user_id = Column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(200), nullable=False)
    cron_expr = Column(String(100), nullable=False)  # "0 3 * * 1" = Monday 03:00
    enabled = Column(Boolean, default=True, nullable=False)
    pipeline_config = Column(JSON, nullable=True)  # override per schedule
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    user = relationship("User", back_populates="schedules")

    __table_args__ = (
        Index("ix_schedules_user_enabled", "user_id", "enabled"),
        Index("ix_schedules_next_run", "next_run_at"),
    )


# -----------------------------------------------------------------------
# Pipeline runs (execution history)
# -----------------------------------------------------------------------


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(String(32), primary_key=True, default=_new_id)
    user_id = Column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    schedule_id = Column(String(32), nullable=True)  # null = manual run
    status = Column(String(20), nullable=False, default="pending")  # pending/running/completed/failed/canceled
    trigger = Column(String(20), nullable=False, default="manual")  # manual/scheduled/webhook
    repo_path = Column(String(500), nullable=True)
    flow_mode = Column(String(20), nullable=True)
    phases = Column(JSON, nullable=False, default=list)  # list of PhaseResult dicts
    artifacts = Column(JSON, nullable=False, default=list)  # list of file paths
    errors = Column(JSON, nullable=False, default=list)
    report = Column(JSON, nullable=True)  # consolidated report snapshot
    quality_score = Column(Float, nullable=True)
    duration_seconds = Column(Float, default=0.0, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    # Celery task tracking
    celery_task_id = Column(String(64), nullable=True, index=True)

    user = relationship("User", back_populates="runs")

    __table_args__ = (
        Index("ix_runs_user_status", "user_id", "status"),
        Index("ix_runs_created", "created_at"),
    )


# -----------------------------------------------------------------------
# Audit log (compliance + security)
# -----------------------------------------------------------------------


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String(32), primary_key=True, default=_new_id)
    user_id = Column(String(32), nullable=True)  # null for system events
    action = Column(String(100), nullable=False)  # e.g. "pipeline.run", "settings.update"
    resource_type = Column(String(50), nullable=True)  # e.g. "pipeline_run", "schedule"
    resource_id = Column(String(32), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_audit_user_action", "user_id", "action"),
        Index("ix_audit_created", "created_at"),
    )


# -----------------------------------------------------------------------
# Referrals and payouts
# -----------------------------------------------------------------------


class ReferralProfile(Base):
    __tablename__ = "referral_profiles"

    id = Column(String(32), primary_key=True, default=_new_id)
    user_id = Column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    referral_code = Column(String(40), unique=True, nullable=False, index=True)
    badge_opt_out = Column(Boolean, default=False, nullable=False)
    payout_provider = Column(String(20), default="manual", nullable=False)
    payout_recipient_id = Column(String(128), nullable=True)
    payout_email = Column(String(320), nullable=True)
    payout_status = Column(String(20), default="pending", nullable=False)
    terms_accepted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    user = relationship("User", back_populates="referral_profile", foreign_keys=[user_id])


class ReferralAttribution(Base):
    __tablename__ = "referral_attributions"

    id = Column(String(32), primary_key=True, default=_new_id)
    referrer_user_id = Column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    referred_user_id = Column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    source = Column(String(20), default="badge", nullable=False)
    referral_code = Column(String(40), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    referrer = relationship("User", back_populates="referrals_made", foreign_keys=[referrer_user_id])
    referred = relationship("User", back_populates="referral_source", foreign_keys=[referred_user_id])

    __table_args__ = (
        Index("ix_referral_attr_referrer", "referrer_user_id"),
    )


class ReferralPayout(Base):
    __tablename__ = "referral_payouts"

    id = Column(String(32), primary_key=True, default=_new_id)
    user_id = Column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    currency = Column(String(8), default="USD", nullable=False)
    amount_cents = Column(Integer, nullable=False, default=0)
    status = Column(String(30), nullable=False, default="queued_manual")
    provider = Column(String(20), nullable=False, default="manual")
    provider_payout_id = Column(String(128), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")

    __table_args__ = (
        Index("ix_referral_payout_user_status", "user_id", "status"),
    )


class ReferralLedgerEntry(Base):
    __tablename__ = "referral_ledger_entries"

    id = Column(String(32), primary_key=True, default=_new_id)
    referrer_user_id = Column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    referred_user_id = Column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    attribution_id = Column(
        String(32), ForeignKey("referral_attributions.id", ondelete="CASCADE"), nullable=False
    )
    subscription_id = Column(String(64), nullable=True, index=True)
    payment_event_id = Column(String(128), nullable=True, unique=True)
    event_type = Column(String(40), nullable=False, default="subscription_payment_success")
    amount_cents = Column(Integer, nullable=False, default=0)
    currency = Column(String(8), nullable=False, default="USD")
    commission_rate = Column(Float, nullable=False, default=0.0)
    status = Column(String(20), nullable=False, default="accrued")  # accrued/queued/paid/reversed
    available_at = Column(DateTime(timezone=True), nullable=True)
    paid_out_at = Column(DateTime(timezone=True), nullable=True)
    payout_id = Column(String(32), ForeignKey("referral_payouts.id", ondelete="SET NULL"), nullable=True)
    entry_details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    referrer = relationship("User", foreign_keys=[referrer_user_id])
    referred = relationship("User", foreign_keys=[referred_user_id])
    attribution = relationship("ReferralAttribution")
    payout = relationship("ReferralPayout")

    __table_args__ = (
        Index("ix_referral_ledger_referrer_status", "referrer_user_id", "status"),
        Index("ix_referral_ledger_available_at", "available_at"),
    )


# -----------------------------------------------------------------------
# Helper: create all tables
# -----------------------------------------------------------------------


def create_all_tables(engine: Any) -> None:
    """Create all tables (for development/testing). Use Alembic in production."""
    Base.metadata.create_all(engine)

#!/usr/bin/env python3
"""LLM egress policy guard: local-first, explicit external approval, redaction, logging."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


@dataclass
class LLMEgressPolicy:
    llm_mode: str = "local_default"
    external_llm_allowed: bool = False
    require_explicit_approval: bool = True
    redact_before_external: bool = True
    approval_cache_scope: str = "run"
    local_model: str = "veridoc-writer"
    local_base_model: str = "qwen3:30b"
    local_model_command: str = "ollama run {model} \"{prompt}\""
    quality_delta_note: str = "Fully local mode may reduce output quality by ~10-15% on hardest synthesis tasks."


@dataclass
class EgressAllowlistPolicy:
    allowed_fields: set[str]
    blocked_key_patterns: list[str]
    schema_version: int = 1


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (RuntimeError, ValueError, TypeError, OSError):  # noqa: BLE001
        return {}
    return raw if isinstance(raw, dict) else {}


def load_policy(runtime_config: Path | str | None = None) -> LLMEgressPolicy:
    default = LLMEgressPolicy()
    candidates: list[Path] = []
    if runtime_config:
        candidates.append(Path(str(runtime_config)).expanduser())
    candidates.extend(
        [
            Path("docsops/config/client_runtime.yml"),
            Path("config/client_runtime.yml"),
        ]
    )
    payload: dict[str, Any] = {}
    for c in candidates:
        if c.exists():
            payload = _load_yaml(c)
            break
    cfg = payload.get("llm_control", {})
    if not isinstance(cfg, dict):
        cfg = {}
    return LLMEgressPolicy(
        llm_mode=str(cfg.get("llm_mode", default.llm_mode)).strip().lower() or default.llm_mode,
        external_llm_allowed=bool(cfg.get("external_llm_allowed", default.external_llm_allowed)),
        require_explicit_approval=bool(cfg.get("require_explicit_approval", default.require_explicit_approval)),
        redact_before_external=bool(cfg.get("redact_before_external", default.redact_before_external)),
        approval_cache_scope=str(cfg.get("approval_cache_scope", default.approval_cache_scope)).strip().lower()
        or default.approval_cache_scope,
        local_model=str(cfg.get("local_model", default.local_model)).strip() or default.local_model,
        local_base_model=str(cfg.get("local_base_model", default.local_base_model)).strip()
        or default.local_base_model,
        local_model_command=str(cfg.get("local_model_command", default.local_model_command)).strip()
        or default.local_model_command,
        quality_delta_note=str(cfg.get("quality_delta_note", default.quality_delta_note)).strip()
        or default.quality_delta_note,
    )


_SECRET_PATTERNS = [
    re.compile(r"\b(sk-[a-zA-Z0-9]{16,})\b"),
    re.compile(r"\b(xai-[a-zA-Z0-9]{16,})\b"),
    re.compile(r"\b(gsk_[a-zA-Z0-9]{16,})\b"),
    re.compile(r"\b([A-Za-z0-9_\-]{24,}\.[A-Za-z0-9_\-]{16,}\.[A-Za-z0-9_\-]{16,})\b"),  # JWT-ish
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\b\s*[:=]\s*['\"]?([^\s'\",]+)"),
]


def redact_text(value: str) -> str:
    out = value
    for pattern in _SECRET_PATTERNS:
        out = pattern.sub("[REDACTED]", out)
    return out


def redact_payload(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_payload(v) for v in value]
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for k, v in value.items():
            key = str(k)
            if key.lower() in {"api_key", "token", "secret", "password", "authorization"}:
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_payload(v)
        return redacted
    return value


def _egress_log_path(reports_dir: Path) -> Path:
    return reports_dir / "llm_egress_log.json"


def _append_egress_log(reports_dir: Path, record: dict[str, Any]) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = _egress_log_path(reports_dir)
    existing: list[dict[str, Any]] = []
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                existing = [r for r in raw if isinstance(r, dict)]
        except (RuntimeError, ValueError, TypeError, OSError):  # noqa: BLE001
            existing = []
    existing.append(record)
    path.write_text(json.dumps(existing, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def load_egress_allowlist() -> EgressAllowlistPolicy:
    """Load metadata-only egress allowlist schema."""
    candidates = [
        Path("config/ip_protection/egress_allowlist.yml"),
        Path("docsops/config/ip_protection/egress_allowlist.yml"),
    ]
    payload: dict[str, Any] = {}
    for path in candidates:
        if path.exists():
            payload = _load_yaml(path)
            break
    allowed = payload.get("allowed_fields", [])
    if not isinstance(allowed, list) or not allowed:
        allowed = [
            "tenant_id", "build_id", "version", "platform", "plan",
            "health", "error_code", "duration_ms", "event", "timestamp_utc", "run_status",
        ]
    blocked = payload.get("blocked_key_patterns", [])
    if not isinstance(blocked, list) or not blocked:
        blocked = ["content", "text", "code", "source", "prompt", "snippet", "markdown", "doc", "file"]
    return EgressAllowlistPolicy(
        allowed_fields={str(v).strip() for v in allowed if str(v).strip()},
        blocked_key_patterns=[str(v).strip().lower() for v in blocked if str(v).strip()],
        schema_version=int(payload.get("version", 1) or 1),
    )


def validate_metadata_egress_payload(payload: dict[str, Any], policy: EgressAllowlistPolicy) -> tuple[bool, str]:
    """Validate that outbound payload contains metadata only and no raw docs/code fields."""
    for key in payload:
        key_norm = str(key).strip()
        if key_norm not in policy.allowed_fields:
            return False, f"field_not_allowed:{key_norm}"
        low = key_norm.lower()
        if any(pattern in low for pattern in policy.blocked_key_patterns):
            return False, f"blocked_key_pattern:{key_norm}"
    return True, "ok"


def enforce_metadata_egress_payload(
    *,
    payload: dict[str, Any],
    reports_dir: Path,
    step: str,
    source: str,
) -> dict[str, Any]:
    """Validate and sanitize egress payload to metadata-only allowlist."""
    policy = load_egress_allowlist()
    normalized = {str(k).strip(): v for k, v in payload.items() if str(k).strip()}
    valid, reason = validate_metadata_egress_payload(normalized, policy)
    now = datetime.now(timezone.utc).isoformat()
    if not valid:
        _append_egress_log(
            reports_dir,
            {
                "timestamp_utc": now,
                "step": step,
                "source": source,
                "decision": "blocked",
                "reason": reason,
                "schema_version": policy.schema_version,
            },
        )
        raise ValueError(f"Egress payload blocked by metadata allowlist: {reason}")

    _append_egress_log(
        reports_dir,
        {
            "timestamp_utc": now,
            "step": step,
            "source": source,
            "decision": "approved",
            "reason": "metadata_only",
            "schema_version": policy.schema_version,
            "fields": sorted(normalized.keys()),
        },
    )
    return normalized


def ensure_external_allowed(
    *,
    policy: LLMEgressPolicy,
    step: str,
    reports_dir: Path,
    approve_once: bool = False,
    approve_for_run: bool = False,
    non_interactive: bool = False,
) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    if not policy.external_llm_allowed:
        _append_egress_log(
            reports_dir,
            {
                "timestamp_utc": now,
                "step": step,
                "decision": "blocked",
                "reason": "external_llm_allowed=false",
            },
        )
        return False

    approved = bool(approve_once)
    approval_flag = reports_dir / ".external_llm_approved_for_run"
    if approve_for_run:
        approval_flag.write_text("approved\n", encoding="utf-8")
        approved = True
    elif policy.approval_cache_scope == "run" and approval_flag.exists():
        approved = True

    if not policy.require_explicit_approval:
        approved = True

    if policy.require_explicit_approval and not approved:
        if non_interactive:
            _append_egress_log(
                reports_dir,
                {
                    "timestamp_utc": now,
                    "step": step,
                    "decision": "blocked",
                    "reason": "explicit approval required",
                },
            )
            return False
        try:
            raw = input(
                f"[llm-egress] External LLM step '{step}' may send redacted data outside the environment. Approve once? [y/N]: "
            ).strip().lower()
        except (RuntimeError, ValueError, TypeError, OSError):  # noqa: BLE001
            raw = "n"
        approved = raw in {"y", "yes"}

    _append_egress_log(
        reports_dir,
        {
            "timestamp_utc": now,
            "step": step,
            "decision": "approved" if approved else "blocked",
            "require_explicit_approval": policy.require_explicit_approval,
            "external_llm_allowed": policy.external_llm_allowed,
        },
    )
    return approved

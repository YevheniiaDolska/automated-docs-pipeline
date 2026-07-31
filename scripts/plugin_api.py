#!/usr/bin/env python3
"""Stable extension contract for client plugins.

This is the ONLY surface a client (or an AI assistant acting for a client, such
as Claude or Codex) needs to adapt the pipeline. Client code lives in a
``client_plugins/`` directory and hooks into well-defined lifecycle points --
it never edits, imports private internals of, or forks the protected core.

Why this exists
---------------
The pipeline core (scoring, retrieval/RAG, contract engines, LLM policy packs)
is the vendor's protected intellectual property. Clients still need to adapt the
pipeline to their repository. This module resolves that tension: it publishes a
small, versioned, backward-compatible contract that plugins build against, so a
client can extend behavior freely without touching the core and without the core
having to expose how it works.

Writing a plugin
----------------
Create a ``.py`` file under ``client_plugins/`` that defines one or more hook
functions by name. Each receives a :class:`PipelineContext` and returns
``None`` (or a :class:`PluginResult`). Example::

    # client_plugins/notify_slack.py
    PLUGIN = {"name": "notify-slack", "priority": 50}

    def after_pipeline(ctx):
        summary = ctx.load_report("docsops_status.json")
        # ... post summary to Slack via the client's own webhook ...
        return ctx.ok(f"notified: quality={summary.get('quality_score')}")

Supported hooks (see ``HOOKS``): ``before_pipeline``, ``after_pipeline``,
``before_commit``, ``after_stage``. Missing hooks are simply not called. A
plugin that raises is isolated: its failure is logged and, by default, does not
abort the pipeline (a ``before_commit`` plugin may opt into blocking by raising
:class:`PluginBlock`).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Contract version. Bump the minor for additive, backward-compatible changes;
# bump the major only for a breaking change to the hook signatures or context.
API_VERSION = "1.0"

# Lifecycle hooks a plugin module may define, by function name.
HOOKS: tuple[str, ...] = (
    "before_pipeline",   # ctx -> None : before any stage runs
    "after_pipeline",    # ctx -> None : after all stages, before the final summary
    "before_commit",     # ctx -> None : before the review-branch/commit stage
    "after_stage",       # ctx, stage_name -> None : after each named stage
)


class PluginBlock(Exception):
    """Raised by a plugin to intentionally halt the pipeline (e.g. a gate)."""


@dataclass
class PluginResult:
    """Outcome a hook may return so the pipeline can report it."""

    ok: bool = True
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineContext:
    """Everything a plugin is allowed to see and mutate.

    This is a deliberately small, stable surface. It exposes the repository
    layout, the resolved (read-only) runtime configuration, and a shared
    ``state`` dict for passing data between hooks -- but never the core's
    internal modules. Treat ``runtime`` as read-only; mutate ``state`` freely.
    """

    repo_root: Path
    docsops_root: Path
    reports_dir: Path
    docs_root: Path
    runtime: dict[str, Any]
    changed_files: list[str] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)
    api_version: str = API_VERSION

    def load_report(self, name: str) -> dict[str, Any]:
        """Load a JSON report from ``reports_dir`` by file name; {} if absent."""
        path = self.reports_dir / name
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return {}
        return data if isinstance(data, dict) else {}

    def write_report(self, name: str, payload: dict[str, Any]) -> Path:
        """Write a JSON report into ``reports_dir`` (for the plugin's own output)."""
        path = self.reports_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        return path

    def config(self, *keys: str, default: Any = None) -> Any:
        """Read a nested runtime-config value, e.g. ctx.config('modules', 'kpi_sla')."""
        node: Any = self.runtime
        for key in keys:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    def ok(self, message: str = "", **data: Any) -> PluginResult:
        return PluginResult(ok=True, message=message, data=dict(data))

    def fail(self, message: str = "", **data: Any) -> PluginResult:
        return PluginResult(ok=False, message=message, data=dict(data))

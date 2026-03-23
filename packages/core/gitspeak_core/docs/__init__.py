"""
Documentation Orchestration Package.

Provides the DocOrchestrator wrapper around the pipeline for
subprocess-isolated, plan-driven documentation generation with
self-checks, orchestrator review, and pseudo-RL pattern collection.
"""

from gitspeak_core.docs.orchestrator import DocOrchestrator

__all__ = [
    "DocOrchestrator",
]

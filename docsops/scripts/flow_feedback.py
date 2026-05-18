#!/usr/bin/env python3
"""Human-readable flow narration helpers for pipeline scripts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


@dataclass
class FlowNarrator:
    """Pretty, compact CLI narration for long-running flows."""

    flow_name: str
    total_steps: int = 0

    def start(self, intro: str = "") -> None:
        print("")
        print("=" * 78)
        print(f"[{_ts()}] FLOW START :: {self.flow_name}")
        if intro:
            print(f"[{_ts()}] {intro}")
        if self.total_steps > 0:
            print(f"[{_ts()}] Planned stages: {self.total_steps}")
        print("=" * 78)

    def stage(self, step_no: int, title: str, detail: str = "") -> None:
        prefix = f"[{_ts()}] Stage {step_no}/{self.total_steps}" if self.total_steps > 0 else f"[{_ts()}] Stage {step_no}"
        print("")
        print(f"{prefix} :: {title}")
        if detail:
            print(f"[{_ts()}]   {detail}")

    def done(self, summary: str = "") -> None:
        if summary:
            print(f"[{_ts()}]   OK :: {summary}")
        else:
            print(f"[{_ts()}]   OK")

    def note(self, text: str) -> None:
        print(f"[{_ts()}]   NOTE :: {text}")

    def warn(self, text: str) -> None:
        print(f"[{_ts()}]   WARN :: {text}")

    def command(self, cmd: str) -> None:
        print(f"[{_ts()}]   CMD  :: {cmd}")

    def finish(self, success: bool = True, summary: str = "") -> None:
        status = "SUCCESS" if success else "FAILED"
        print("")
        print("-" * 78)
        print(f"[{_ts()}] FLOW {status} :: {self.flow_name}")
        if summary:
            print(f"[{_ts()}] {summary}")
        print("-" * 78)
        print("")


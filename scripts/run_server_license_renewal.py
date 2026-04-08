#!/usr/bin/env python3
"""Run server-side license auto-renew batch for hybrid/cloud deployments.

Usage:
  python3 scripts/run_server_license_renewal.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "packages" / "core") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "packages" / "core"))


def main() -> int:
    from gitspeak_core.api.billing import run_license_autorenew_batch
    from gitspeak_core.db.engine import get_session

    session = get_session()
    try:
        result = run_license_autorenew_batch(session)
        print(json.dumps(result, ensure_ascii=True, indent=2))
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

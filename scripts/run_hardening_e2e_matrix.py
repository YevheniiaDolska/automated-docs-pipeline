#!/usr/bin/env python3
"""Run hardening e2e matrix and emit PASS/FAIL report."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "reports" / "hardening_e2e_matrix_report.json"


def _run_pytest(node_id: str) -> dict[str, Any]:
    cmd = ["pytest", "-q", node_id]
    started = time.time()
    completed = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    duration = round(time.time() - started, 3)
    return {
        "command": " ".join(cmd),
        "returncode": completed.returncode,
        "duration_seconds": duration,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run hardening e2e matrix.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Path to JSON report.")
    args = parser.parse_args()

    matrix = {
        "tamper_detection": "tests/test_hardening_controls.py::test_integrity_manifest_missing_blocks_when_enforced",
        "expired_jwt_degrade": "tests/test_hardening_controls.py::test_expired_license_degrades_to_community",
        "tenant_domain_mismatch_degrade": "tests/test_hardening_controls.py::test_tenant_and_domain_binding_mismatch_degrades",
        "missing_invalid_pack_premium_off": "tests/test_hardening_controls.py::test_missing_capability_pack_degrades_premium_features",
        "strict_local_offline_renewal_bundle": "tests/test_build_offline_renewal_bundle.py",
        "hybrid_cloud_server_renewal_path": "tests/test_run_server_license_renewal.py",
    }

    results: dict[str, Any] = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "checks": {}}
    failures = 0
    for check_name, node_id in matrix.items():
        outcome = _run_pytest(node_id)
        results["checks"][check_name] = outcome
        if outcome["status"] != "PASS":
            failures += 1

    results["summary"] = {
        "total": len(matrix),
        "passed": len(matrix) - failures,
        "failed": failures,
        "status": "PASS" if failures == 0 else "FAIL",
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, ensure_ascii=True, indent=2), encoding="utf-8")
    print(f"[hardening-matrix] report: {output_path}")
    print(f"[hardening-matrix] summary: {results['summary']['status']} ({results['summary']['passed']}/{results['summary']['total']})")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

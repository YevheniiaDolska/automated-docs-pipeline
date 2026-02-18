#!/usr/bin/env python3
"""Comprehensive test suite for the documentation automation pipeline."""

from __future__ import annotations

import json
import subprocess
import tempfile
import time
import unittest
from datetime import date
from pathlib import Path

from scripts.check_api_sdk_drift import evaluate as evaluate_drift
from scripts.check_code_examples_smoke import run_smoke
from scripts.check_docs_contract import evaluate_contract
from scripts.evaluate_kpi_sla import evaluate as evaluate_sla
from scripts.generate_kpi_wall import build_metrics
from scripts.test_docs_ops_e2e import run_docs_contract_tests, run_drift_tests, run_sla_tests


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"


class FunctionalTests(unittest.TestCase):
    """Validate core business logic for docs contract, drift, KPI, and SLA."""

    def test_docs_contract_blocks_without_docs(self) -> None:
        files = ["api/openapi.yaml", "src/app/routes/orders.py"]
        report = evaluate_contract(files)
        self.assertTrue(report["blocked"])

    def test_docs_contract_passes_with_docs(self) -> None:
        files = ["api/openapi.yaml", "docs/reference/orders.md"]
        report = evaluate_contract(files)
        self.assertFalse(report["blocked"])

    def test_drift_detected_without_reference_docs(self) -> None:
        files = ["api/openapi.yaml", "sdk/client.ts"]
        report = evaluate_drift(files)
        self.assertEqual(report.status, "drift")

    def test_drift_passes_with_reference_docs(self) -> None:
        files = ["api/openapi.yaml", "docs/reference/orders.md"]
        report = evaluate_drift(files)
        self.assertEqual(report.status, "ok")

    def test_sla_breach_for_low_quality(self) -> None:
        current = {"quality_score": 70, "stale_pct": 20.0, "gap_high": 9}
        previous = {"quality_score": 90, "stale_pct": 10.0, "gap_high": 2}
        thresholds = {
            "min_quality_score": 80,
            "max_stale_pct": 15.0,
            "max_high_priority_gaps": 8,
            "max_quality_score_drop": 5,
        }
        report = evaluate_sla(current, previous, thresholds)
        self.assertEqual(report.status, "breach")
        self.assertGreaterEqual(len(report.breaches), 3)


class IntegrationTests(unittest.TestCase):
    """Validate cross-script behavior with realistic generated artifacts."""

    def test_kpi_output_is_consumed_by_sla_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            tmp_path = Path(temp)
            docs_dir = tmp_path / "docs"
            reports_dir = tmp_path / "reports"
            docs_dir.mkdir(parents=True, exist_ok=True)
            reports_dir.mkdir(parents=True, exist_ok=True)

            (docs_dir / "service.md").write_text(
                """---
title: Service
description: Service documentation page.
content_type: reference
last_reviewed: '2026-01-01'
---

# Service
Integration test page.
""",
                encoding="utf-8",
            )

            metrics = build_metrics(
                docs_dir=docs_dir,
                reports_dir=reports_dir,
                stale_days=90,
                generated_at="2026-02-18T00:00:00Z",
                reference_date=date(2026, 4, 15),
            )

            current_path = reports_dir / "kpi-wall.json"
            current_path.write_text(json.dumps(metrics.__dict__), encoding="utf-8")

            policy_path = tmp_path / "policy.yml"
            policy_path.write_text(
                json.dumps(
                    {
                        "kpi_sla": {
                            "min_quality_score": 0,
                            "max_stale_pct": 100.0,
                            "max_high_priority_gaps": 100,
                            "max_quality_score_drop": 100,
                        }
                    }
                ),
                encoding="utf-8",
            )

            json_out = reports_dir / "kpi-sla-report.json"
            md_out = reports_dir / "kpi-sla-report.md"
            cmd = [
                "python3",
                str(SCRIPTS_DIR / "evaluate_kpi_sla.py"),
                "--current",
                str(current_path),
                "--policy-pack",
                str(policy_path),
                "--json-output",
                str(json_out),
                "--md-output",
                str(md_out),
            ]
            completed = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True, check=False)
            self.assertEqual(
                completed.returncode,
                0,
                msg=f"SLA CLI should pass in integration test. stderr={completed.stderr}",
            )
            self.assertTrue(json_out.exists())
            self.assertTrue(md_out.exists())


class SecurityTests(unittest.TestCase):
    """Validate basic secure coding constraints for pipeline scripts."""

    def test_no_shell_true_in_subprocess_calls(self) -> None:
        offenders: list[str] = []
        for path in sorted(SCRIPTS_DIR.glob("*.py")):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "subprocess.run(" in text and "shell=True" in text:
                offenders.append(str(path))
        self.assertEqual(offenders, [], msg=f"Found shell=True in: {offenders}")

    def test_no_inline_secret_literals_in_scripts(self) -> None:
        patterns = ("sk_live_", "sk_test_", "AKIA", "ghp_", "xoxb-")
        offenders: list[str] = []
        for path in sorted(SCRIPTS_DIR.glob("*.py")):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if any(pattern in text for pattern in patterns):
                offenders.append(str(path))
        self.assertEqual(offenders, [], msg=f"Possible hardcoded secret markers in: {offenders}")


class PerformanceTests(unittest.TestCase):
    """Validate core checks stay within practical runtime budgets."""

    def test_contract_and_drift_scale_to_large_change_sets(self) -> None:
        files = [f"src/service/module_{i}.py" for i in range(12000)]
        files.extend(f"api/spec_{i}.yaml" for i in range(3000))
        files.extend(f"sdk/client_{i}.ts" for i in range(3000))
        files.extend(f"docs/reference/endpoint_{i}.md" for i in range(2000))

        start = time.perf_counter()
        contract_report = evaluate_contract(files)
        contract_elapsed = time.perf_counter() - start

        start = time.perf_counter()
        drift_report = evaluate_drift(files)
        drift_elapsed = time.perf_counter() - start

        self.assertFalse(contract_report["blocked"])
        self.assertEqual(drift_report.status, "ok")
        self.assertLess(contract_elapsed, 3.0)
        self.assertLess(drift_elapsed, 3.0)


class E2ETests(unittest.TestCase):
    """Validate full fixture-driven behavior from existing E2E checks."""

    def test_fixture_driven_e2e_suite(self) -> None:
        fixtures_dir = ROOT_DIR / "tests" / "fixtures" / "docs_ops"
        run_docs_contract_tests(fixtures_dir)
        run_drift_tests(fixtures_dir)
        run_sla_tests()


class WorkflowContractTests(unittest.TestCase):
    """Validate required docs-ops workflows exist in repository."""

    def test_required_workflow_files_exist(self) -> None:
        required = [
            ".github/workflows/pr-dod-contract.yml",
            ".github/workflows/api-sdk-drift-gate.yml",
            ".github/workflows/kpi-wall.yml",
            ".github/workflows/release-docs-pack.yml",
            ".github/workflows/docs-ops-e2e.yml",
            ".github/workflows/api-first-scaffold.yml",
            ".github/workflows/code-examples-smoke.yml",
        ]
        missing = [path for path in required if not (ROOT_DIR / path).exists()]
        self.assertEqual(missing, [], msg=f"Missing workflow files: {missing}")


class CodeExamplesSmokeTests(unittest.TestCase):
    """Validate smoke runner behavior on markdown code examples."""

    def test_smoke_runner_executes_tagged_examples(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            tmp_path = Path(temp)
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)

            smoke_doc = docs_dir / "smoke.md"
            smoke_doc.write_text(
                """# Smoke example

```python smoke
print("ok")
```

```json smoke
{"service":"docs","status":"ok"}
```
""",
                encoding="utf-8",
            )

            result = run_smoke(paths=[str(docs_dir)], timeout=8, allow_empty=False)
            self.assertEqual(result, 0)


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str) -> unittest.TestSuite:
    """Run from `python3 -m unittest tests/test_autopipeline_suite.py` deterministically."""
    del tests
    del pattern
    suite = unittest.TestSuite()
    for test_case in [
        FunctionalTests,
        IntegrationTests,
        SecurityTests,
        PerformanceTests,
        E2ETests,
        WorkflowContractTests,
        CodeExamplesSmokeTests,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(test_case))
    return suite


if __name__ == "__main__":
    unittest.main(verbosity=2)

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> int:
    return subprocess.run(cmd, check=False).returncode


def test_protocol_lint_stack_graphql_pass(tmp_path: Path) -> None:
    schema = tmp_path / "schema.graphql"
    schema.write_text(
        "type Query { health: String! }\n"
        "type Mutation { setHealth(v: String!): String! }\n"
        "type Subscription { healthChanged: String! }\n",
        encoding="utf-8",
    )
    report = tmp_path / "lint.json"
    rc = _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_protocol_lint_stack.py"),
            "--protocol",
            "graphql",
            "--source",
            str(schema),
            "--json-report",
            str(report),
        ]
    )
    assert rc == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["checks_total"] >= 7
    assert payload["ok"] is True


def test_protocol_lint_stack_graphql_fail_duplicate_field(tmp_path: Path) -> None:
    schema = tmp_path / "bad.graphql"
    schema.write_text("type Query { ping: String\n ping: String }\n", encoding="utf-8")
    rc = _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_protocol_lint_stack.py"),
            "--protocol",
            "graphql",
            "--source",
            str(schema),
        ]
    )
    assert rc == 1


def test_protocol_self_verify_skips_without_endpoint_when_not_required(tmp_path: Path) -> None:
    report = tmp_path / "self_verify.json"
    rc = _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_protocol_self_verify.py"),
            "--protocol",
            "graphql",
            "--json-report",
            str(report),
        ]
    )
    assert rc == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["skipped"] is True


def test_protocol_self_verify_fails_without_endpoint_when_required(tmp_path: Path) -> None:
    rc = _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_protocol_self_verify.py"),
            "--protocol",
            "graphql",
            "--require-endpoint",
        ]
    )
    assert rc == 1

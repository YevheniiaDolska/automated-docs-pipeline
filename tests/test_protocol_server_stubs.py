from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> int:
    return subprocess.run(cmd, check=False).returncode


def test_generate_graphql_server_stubs(tmp_path: Path) -> None:
    source = tmp_path / "schema.graphql"
    source.write_text(
        "type Query { health: String! project(id: ID): String! }\n"
        "type Mutation { createProject(id: ID): String! }\n",
        encoding="utf-8",
    )
    output = tmp_path / "graphql_handlers.py"
    rc = _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_protocol_server_stubs.py"),
            "--protocol",
            "graphql",
            "--source",
            str(source),
            "--output",
            str(output),
        ]
    )
    assert rc == 0
    rendered = output.read_text(encoding="utf-8")
    assert "def query_health" in rendered
    assert "def mutation_createproject" in rendered
    assert "'status': 'ok'" in rendered
    assert "generated_at" in rendered


def test_generate_grpc_server_stubs(tmp_path: Path) -> None:
    source = tmp_path / "service.proto"
    source.write_text(
        'syntax = "proto3";\n'
        "service TaskService {\n"
        "  rpc ListTasks (ListTasksRequest) returns (ListTasksResponse);\n"
        "}\n",
        encoding="utf-8",
    )
    output = tmp_path / "grpc_handlers.py"
    rc = _run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_protocol_server_stubs.py"),
            "--protocol",
            "grpc",
            "--source",
            str(source),
            "--output",
            str(output),
        ]
    )
    assert rc == 0
    rendered = output.read_text(encoding="utf-8")
    assert "class TaskServiceServicer" in rendered
    assert "def ListTasks" in rendered
    assert "'status': 'ok'" in rendered
    assert "generated_at" in rendered

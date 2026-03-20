from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_autopipeline_operator_mode_generates_packet(tmp_path: Path, monkeypatch) -> None:
    from scripts import run_autopipeline as mod

    docsops = tmp_path / "docsops"
    (docsops / "config").mkdir(parents=True)
    runtime = {
        "api_governance": {"strictness": "standard"},
        "docs_flow": {"mode": "code-first"},
        "modules": {},
        "paths": {"docs_root": "docs"},
        "pipeline": {},
        "custom_tasks": {"weekly": []},
    }
    runtime_path = docsops / "config" / "client_runtime.yml"
    runtime_path.write_text(yaml.safe_dump(runtime, sort_keys=False), encoding="utf-8")

    reports = tmp_path / "reports"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(mod, "_run", lambda cmd, cwd: 0)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "x",
            "--docsops-root",
            "docsops",
            "--reports-dir",
            "reports",
            "--runtime-config",
            str(runtime_path),
            "--mode",
            "operator",
        ],
    )

    rc = mod.main()
    assert rc == 0
    packet = reports / "local_llm_review_packet.json"
    assert packet.exists()
    payload = json.loads(packet.read_text(encoding="utf-8"))
    assert "consolidated_report" in payload

from __future__ import annotations

import json
from pathlib import Path

from scripts import upload_api_test_assets as mod


def _write_cases(path: Path) -> None:
    payload = {
        "cases": [
            {
                "title": "getUser: positive",
                "operation_id": "getUser",
                "traceability": {"method": "GET", "path": "/users/{id}"},
                "preconditions": ["Sandbox is available"],
                "steps": ["Send GET request"],
                "expected_result": "200 OK",
            }
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_upload_skips_when_disabled(tmp_path: Path, monkeypatch) -> None:
    cases = tmp_path / "cases.json"
    report = tmp_path / "report.json"
    _write_cases(cases)

    rc = mod.main.__wrapped__ if hasattr(mod.main, "__wrapped__") else None
    assert rc is None

    monkeypatch.setenv("TESTRAIL_UPLOAD_ENABLED", "false")
    monkeypatch.setenv("ZEPHYR_UPLOAD_ENABLED", "false")

    # call through CLI-compatible entry by patching argv
    monkeypatch.setattr(
        "sys.argv",
        ["upload_api_test_assets.py", "--cases-json", str(cases), "--report", str(report)],
    )
    code = mod.main()
    assert code == 0

    payload = json.loads(report.read_text(encoding="utf-8"))
    providers = {item.get("provider"): item for item in payload["results"]}
    assert providers["testrail"]["skipped"] is True
    assert providers["zephyr_scale"]["skipped"] is True


def test_upload_testrail_success_path(tmp_path: Path, monkeypatch) -> None:
    cases = tmp_path / "cases.json"
    report = tmp_path / "report.json"
    _write_cases(cases)

    calls: list[tuple[str, str]] = []

    def fake_http(method, url, headers=None, payload=None):  # noqa: ANN001
        calls.append((method, url))
        return {"id": 123}

    monkeypatch.setattr(mod, "_http_json", fake_http)
    monkeypatch.setenv("TESTRAIL_UPLOAD_ENABLED", "true")
    monkeypatch.setenv("TESTRAIL_BASE_URL", "https://testrail.example.com")
    monkeypatch.setenv("TESTRAIL_EMAIL", "qa@example.com")
    monkeypatch.setenv("TESTRAIL_API_KEY", "secret")
    monkeypatch.setenv("TESTRAIL_SECTION_ID", "44")
    monkeypatch.setenv("ZEPHYR_UPLOAD_ENABLED", "false")
    monkeypatch.setattr(
        "sys.argv",
        ["upload_api_test_assets.py", "--cases-json", str(cases), "--report", str(report)],
    )

    code = mod.main()
    assert code == 0
    assert calls
    payload = json.loads(report.read_text(encoding="utf-8"))
    testrail = [item for item in payload["results"] if item.get("provider") == "testrail"][0]
    assert testrail["created"] == 1
    assert not testrail["errors"]


def test_upload_strict_fails_on_missing_required_env(tmp_path: Path, monkeypatch) -> None:
    cases = tmp_path / "cases.json"
    report = tmp_path / "report.json"
    _write_cases(cases)

    monkeypatch.setenv("TESTRAIL_UPLOAD_ENABLED", "true")
    monkeypatch.setenv("ZEPHYR_UPLOAD_ENABLED", "false")
    monkeypatch.setattr(
        "sys.argv",
        [
            "upload_api_test_assets.py",
            "--cases-json",
            str(cases),
            "--report",
            str(report),
            "--strict",
        ],
    )
    code = mod.main()
    assert code == 1

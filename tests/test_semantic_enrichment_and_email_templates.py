from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_email_templates_are_importable_and_have_placeholders() -> None:
    from packages.core.gitspeak_core.email_templates import onboarding_day3
    from packages.core.gitspeak_core.email_templates import outreach_audit
    from packages.core.gitspeak_core.email_templates import outreach_followup
    from packages.core.gitspeak_core.email_templates import upgrade_prompt
    from packages.core.gitspeak_core.email_templates import welcome

    templates = [
        onboarding_day3,
        outreach_audit,
        outreach_followup,
        upgrade_prompt,
        welcome,
    ]
    for module in templates:
        assert isinstance(module.SUBJECT, str) and module.SUBJECT
        assert isinstance(module.HTML_BODY, str) and "<html" in module.HTML_BODY.lower()


def test_semantic_helpers_and_normalization() -> None:
    from scripts import enrich_knowledge_modules_semantic as mod

    payload = mod._normalize_semantic(
        {
            "topic": "API auth",
            "intent": "configure",
            "audience": "developer",
            "keywords": ["Auth", "OAuth", "OAuth"],
        },
        fallback_intent="configure",
        fallback_audience="operator",
        fallback_topic="fallback",
    )
    assert payload["topic"] == "API auth"
    assert payload["intent"] == "configure"
    assert payload["audience"] == "developer"
    assert payload["keywords"] == ["auth", "oauth"]

    fallback = mod._normalize_semantic(
        {"intent": "invalid", "audience": "invalid", "keywords": []},
        fallback_intent="integrate",
        fallback_audience="all",
        fallback_topic="Topic X",
    )
    assert fallback["intent"] == "integrate"
    assert fallback["audience"] == "all"
    assert fallback["keywords"] == ["topic x"]

    prompt = mod._prompt_for_module(
        {
            "title": "How to configure SSO",
            "summary": "Guide for SSO setup",
            "content": {"docs_markdown": "# Step\nDo this"},
        }
    )
    assert "intent must be one of" in prompt
    assert "How to configure SSO" in prompt


def test_call_anthropic_json_parses_fenced_json(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import enrich_knowledge_modules_semantic as mod

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            raw = {
                "content": [
                    {
                        "type": "text",
                        "text": "```json\n{\"topic\":\"A\",\"intent\":\"configure\",\"audience\":\"all\",\"keywords\":[\"x\"]}\n```",
                    }
                ]
            }
            return json.dumps(raw).encode("utf-8")

    monkeypatch.setattr(mod, "urlopen", lambda req, timeout=45: _Resp())
    out = mod._call_anthropic_json(api_key="k", model="m", prompt="p", timeout=5)
    assert out["topic"] == "A"


def test_semantic_main_updates_module_and_writes_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import enrich_knowledge_modules_semantic as mod

    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir(parents=True)

    modules = repo / "knowledge_modules"
    modules.mkdir(parents=True)
    module_path = modules / "m1.yml"
    module_path.write_text(
        yaml.safe_dump(
            {
                "id": "m1",
                "status": "active",
                "title": "Configure webhooks",
                "summary": "Webhook setup",
                "intents": ["configure"],
                "audiences": ["developer"],
                "content": {"docs_markdown": "Webhook details"},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    report = repo / "reports" / "semantic_report.json"

    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setattr(mod, "load_local_env", lambda *a, **k: None)

    class _Policy:
        redact_before_external = False

    monkeypatch.setattr(mod, "load_policy", lambda *a, **k: _Policy())
    monkeypatch.setattr(mod, "ensure_external_allowed", lambda **kwargs: True)
    monkeypatch.setattr(mod, "redact_payload", lambda payload: payload)
    monkeypatch.setattr(
        mod,
        "_call_anthropic_json",
        lambda **kwargs: {
            "topic": "Webhook security",
            "intent": "secure",
            "audience": "operator",
            "keywords": ["webhook", "hmac", "signature"],
        },
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "x",
            "--modules-dir",
            str(modules),
            "--report",
            str(report),
            "--non-interactive",
            "--limit",
            "1",
        ],
    )

    rc = mod.main()
    assert rc == 0
    updated = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    assert updated["semantic"]["intent"] == "secure"
    assert report.exists()


def test_semantic_main_handles_missing_modules_and_missing_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import enrich_knowledge_modules_semantic as mod

    missing_modules = tmp_path / "no_modules"
    report = tmp_path / "reports" / "r.json"

    monkeypatch.setattr(mod, "load_local_env", lambda *a, **k: None)
    monkeypatch.setattr(
        sys,
        "argv",
        ["x", "--modules-dir", str(missing_modules), "--report", str(report)],
    )
    rc_missing = mod.main()
    assert rc_missing == 1

    modules = tmp_path / "modules"
    modules.mkdir(parents=True)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(
        sys,
        "argv",
        ["x", "--modules-dir", str(modules), "--report", str(report)],
    )
    rc_no_key = mod.main()
    assert rc_no_key == 0

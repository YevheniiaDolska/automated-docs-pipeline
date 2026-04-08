from __future__ import annotations

import types


def test_run_server_license_renewal_main(monkeypatch, capsys) -> None:
    from scripts import run_server_license_renewal as mod

    class _FakeSession:
        def close(self) -> None:
            return None

    fake_engine = types.SimpleNamespace(get_session=lambda: _FakeSession())
    fake_billing = types.SimpleNamespace(
        run_license_autorenew_batch=lambda session: {
            "scanned": 2,
            "refreshed": 1,
            "degraded": 1,
            "errors": 0,
            "ran_at_utc": "2026-04-08T00:00:00+00:00",
        }
    )

    import sys

    monkeypatch.setitem(sys.modules, "gitspeak_core.db.engine", fake_engine)
    monkeypatch.setitem(sys.modules, "gitspeak_core.api.billing", fake_billing)

    rc = mod.main()
    out = capsys.readouterr().out
    assert rc == 0
    assert '"scanned": 2' in out

"""Tests for the client plugin extension system."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.plugin_api import PipelineContext, PluginBlock
from scripts.plugin_manager import PluginManager, discover_plugins


def _ctx(tmp_path: Path) -> PipelineContext:
    reports = tmp_path / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    return PipelineContext(
        repo_root=tmp_path,
        docsops_root=tmp_path / "docsops",
        reports_dir=reports,
        docs_root=tmp_path / "docs",
        runtime={"modules": {"kpi_sla": True}, "paths": {"docs_root": "docs"}},
    )


def _write_plugin(tmp_path: Path, name: str, body: str) -> Path:
    pdir = tmp_path / "client_plugins"
    pdir.mkdir(parents=True, exist_ok=True)
    path = pdir / name
    path.write_text(body, encoding="utf-8")
    return path


def test_discovery_respects_enabled_and_hooks(tmp_path: Path) -> None:
    _write_plugin(tmp_path, "a.py", "PLUGIN={'name':'a'}\ndef before_pipeline(ctx):\n    return ctx.ok('a')\n")
    _write_plugin(tmp_path, "off.py", "PLUGIN={'name':'off','enabled':False}\ndef before_pipeline(ctx):\n    return None\n")
    _write_plugin(tmp_path, "_ignored.py", "def before_pipeline(ctx):\n    return None\n")
    _write_plugin(tmp_path, "nohooks.py", "PLUGIN={'name':'nohooks'}\nX=1\n")

    plugins = discover_plugins(tmp_path)
    names = [p.name for p in plugins]
    assert names == ["a"]  # off (disabled), _ignored (underscore), nohooks (no hooks) excluded


def test_priority_ordering(tmp_path: Path) -> None:
    _write_plugin(tmp_path, "late.py", "PLUGIN={'name':'late','priority':200}\ndef before_pipeline(ctx):\n    return None\n")
    _write_plugin(tmp_path, "early.py", "PLUGIN={'name':'early','priority':10}\ndef before_pipeline(ctx):\n    return None\n")
    plugins = discover_plugins(tmp_path)
    assert [p.name for p in plugins] == ["early", "late"]


def test_invoke_runs_hook_and_reports_result(tmp_path: Path) -> None:
    _write_plugin(
        tmp_path, "r.py",
        "PLUGIN={'name':'r'}\ndef after_pipeline(ctx):\n    ctx.state['ran']=True\n    return ctx.ok('done')\n",
    )
    ctx = _ctx(tmp_path)
    mgr = PluginManager(ctx)
    outcomes = mgr.invoke("after_pipeline")
    assert len(outcomes) == 1
    assert outcomes[0].ok and outcomes[0].message == "done"
    assert ctx.state.get("ran") is True


def test_broken_plugin_is_isolated(tmp_path: Path) -> None:
    _write_plugin(tmp_path, "boom.py", "PLUGIN={'name':'boom'}\ndef before_pipeline(ctx):\n    raise RuntimeError('kaboom')\n")
    _write_plugin(tmp_path, "good.py", "PLUGIN={'name':'good'}\ndef before_pipeline(ctx):\n    return ctx.ok('fine')\n")
    mgr = PluginManager(_ctx(tmp_path))
    outcomes = {o.plugin: o for o in mgr.invoke("before_pipeline")}
    assert outcomes["boom"].ok is False and outcomes["boom"].blocked is False
    assert outcomes["good"].ok is True  # the good plugin still runs


def test_plugin_block_halts(tmp_path: Path) -> None:
    _write_plugin(
        tmp_path, "gate.py",
        "from scripts.plugin_api import PluginBlock\nPLUGIN={'name':'gate'}\n"
        "def before_commit(ctx):\n    raise PluginBlock('nope')\n",
    )
    mgr = PluginManager(_ctx(tmp_path))
    outcomes = mgr.invoke("before_commit")
    assert outcomes[0].blocked is True and outcomes[0].ok is False


def test_context_helpers(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path)
    assert ctx.config("modules", "kpi_sla") is True
    assert ctx.config("modules", "missing", default="d") == "d"
    ctx.write_report("x.json", {"a": 1})
    assert ctx.load_report("x.json") == {"a": 1}
    assert ctx.load_report("absent.json") == {}


def test_no_plugins_is_inactive(tmp_path: Path) -> None:
    mgr = PluginManager(_ctx(tmp_path))
    assert mgr.active is False
    assert mgr.invoke("before_pipeline") == []


def test_unknown_hook_rejected(tmp_path: Path) -> None:
    mgr = PluginManager(_ctx(tmp_path))
    with pytest.raises(ValueError):
        mgr.invoke("not_a_hook")

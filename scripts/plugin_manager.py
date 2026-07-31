#!/usr/bin/env python3
"""Discover, load, and invoke client plugins against the stable extension API.

The manager is the core-side counterpart to ``plugin_api``. It finds client
plugin modules, loads them in isolation, and calls their lifecycle hooks. A
broken or malicious plugin cannot take down the pipeline: import errors and
hook exceptions are caught and reported, and only an explicit
:class:`~scripts.plugin_api.PluginBlock` (from a ``before_commit`` gate) halts
execution.

Discovery locations (first existing wins per file name):
- ``<repo_root>/client_plugins/``
- ``<docsops_root>/client_plugins/``

Only top-level ``*.py`` files are loaded (no packages, no recursion), and files
starting with ``_`` are ignored. Load order is by the plugin's ``PLUGIN`` dict
``priority`` (ascending; default 100), then file name.
"""

from __future__ import annotations

import importlib.util
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

try:
    from scripts.plugin_api import HOOKS, PipelineContext, PluginBlock, PluginResult
except ModuleNotFoundError:  # running from a bundle where scripts/ is on sys.path
    from plugin_api import HOOKS, PipelineContext, PluginBlock, PluginResult

PLUGIN_DIRNAME = "client_plugins"


@dataclass
class LoadedPlugin:
    name: str
    priority: int
    path: Path
    module: Any
    enabled: bool = True

    def hook(self, name: str) -> Callable[..., Any] | None:
        fn = getattr(self.module, name, None)
        return fn if callable(fn) else None


@dataclass
class HookOutcome:
    plugin: str
    hook: str
    ok: bool
    message: str = ""
    blocked: bool = False


def _plugin_dirs(repo_root: Path, docsops_root: Path | None) -> list[Path]:
    dirs = [repo_root / PLUGIN_DIRNAME]
    if docsops_root is not None:
        dirs.append(docsops_root / PLUGIN_DIRNAME)
    seen: set[Path] = set()
    result: list[Path] = []
    for d in dirs:
        rp = d.resolve()
        if rp not in seen and d.is_dir():
            seen.add(rp)
            result.append(d)
    return result


def _load_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(f"client_plugin_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot build import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def discover_plugins(repo_root: Path, docsops_root: Path | None = None) -> list[LoadedPlugin]:
    """Return loaded, enabled plugins ordered by (priority, file name).

    Files that fail to import are skipped with a printed warning -- one broken
    plugin never blocks the others or the pipeline.
    """
    plugins: list[LoadedPlugin] = []
    seen_names: set[str] = set()
    for directory in _plugin_dirs(repo_root, docsops_root):
        for path in sorted(directory.glob("*.py")):
            if path.name.startswith("_"):
                continue
            try:
                module = _load_module(path)
            except Exception as exc:  # noqa: BLE001 - isolate any import-time failure
                print(f"[plugins] skip {path.name}: import failed ({exc})")
                continue
            meta = getattr(module, "PLUGIN", {})
            if not isinstance(meta, dict):
                meta = {}
            name = str(meta.get("name", path.stem)).strip() or path.stem
            if name in seen_names:
                print(f"[plugins] skip {path.name}: duplicate plugin name '{name}'")
                continue
            if not bool(meta.get("enabled", True)):
                continue
            defined = [h for h in HOOKS if callable(getattr(module, h, None))]
            if not defined:
                print(f"[plugins] skip {path.name}: defines no known hooks {HOOKS}")
                continue
            seen_names.add(name)
            plugins.append(
                LoadedPlugin(
                    name=name,
                    priority=int(meta.get("priority", 100)),
                    path=path,
                    module=module,
                )
            )
    plugins.sort(key=lambda p: (p.priority, p.path.name))
    return plugins


class PluginManager:
    """Loads client plugins once and invokes their hooks with a shared context."""

    def __init__(self, context: PipelineContext, plugins: list[LoadedPlugin] | None = None) -> None:
        self.context = context
        if plugins is None:
            plugins = discover_plugins(context.repo_root, context.docsops_root)
        self.plugins = plugins

    @property
    def active(self) -> bool:
        return bool(self.plugins)

    def names(self) -> list[str]:
        return [p.name for p in self.plugins]

    def invoke(self, hook: str, **kwargs: Any) -> list[HookOutcome]:
        """Call ``hook`` on every plugin that defines it.

        Returns one :class:`HookOutcome` per invocation. A :class:`PluginBlock`
        raised by a plugin sets ``blocked=True`` on its outcome so the caller can
        decide to halt (used for ``before_commit`` gates). Any other exception is
        caught and reported as a failed-but-non-blocking outcome.
        """
        if hook not in HOOKS:
            raise ValueError(f"unknown hook '{hook}'; valid: {HOOKS}")
        outcomes: list[HookOutcome] = []
        for plugin in self.plugins:
            fn = plugin.hook(hook)
            if fn is None:
                continue
            try:
                result = fn(self.context, **kwargs)
            except PluginBlock as block:
                outcomes.append(HookOutcome(plugin.name, hook, ok=False, message=str(block), blocked=True))
                continue
            except Exception as exc:  # noqa: BLE001 - isolate plugin faults from the core
                print(f"[plugins] {plugin.name}.{hook} raised: {exc}")
                traceback.print_exc()
                outcomes.append(HookOutcome(plugin.name, hook, ok=False, message=str(exc)))
                continue
            ok = True
            message = ""
            if isinstance(result, PluginResult):
                ok = result.ok
                message = result.message
            outcomes.append(HookOutcome(plugin.name, hook, ok=ok, message=message))
        return outcomes

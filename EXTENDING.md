# Extending the pipeline (client guide)

You can adapt this pipeline to your repository **without editing the core**. All
your customizations live in one directory, `client_plugins/`, and hook into the
pipeline through a small, stable contract. The core stays sealed and updatable;
your plugins keep working across core updates.

This is also the safe way to ask an AI assistant (Claude, Codex) to extend the
pipeline: point it at this file. It should only ever create or edit files under
`client_plugins/` -- never core files under `scripts/`.

## The one rule

- **Edit only `client_plugins/`.** Never modify, monkey-patch, or import private
  internals from `scripts/` except the public contract in `scripts/plugin_api.py`.
- Core files are integrity-protected and may be replaced on update; changes to
  them are unsupported and will be lost.

## Write a plugin in three steps

1. Copy `client_plugins/example_plugin.py` to a new file, e.g.
   `client_plugins/enforce_ticket_link.py`.
1. Set its metadata and enable it:

   ```python
   PLUGIN = {"name": "enforce-ticket-link", "priority": 100, "enabled": True}
   ```

1. Keep only the hook functions you need. Each takes a `PipelineContext`.

## Lifecycle hooks

Define any subset of these functions in your plugin module:

| Hook | When it runs | Typical use |
| --- | --- | --- |
| `before_pipeline(ctx)` | Before any stage | Set up, fetch external data, seed `ctx.state` |
| `after_stage(ctx, stage_name)` | After each named stage | React to a specific stage's output |
| `before_commit(ctx)` | Before the commit/review stage | Custom gate (can block), extra edits |
| `after_pipeline(ctx)` | After all stages | Notify Slack/email, publish metrics |

Hooks you do not define are skipped. A plugin that raises an ordinary exception
is isolated -- its failure is logged and the pipeline continues.

## The context object

`ctx` is a `PipelineContext` (see `scripts/plugin_api.py`). Useful members:

- `ctx.repo_root`, `ctx.docs_root`, `ctx.reports_dir` -- paths (`pathlib.Path`).
- `ctx.runtime` -- the resolved runtime config (treat as read-only).
- `ctx.config("modules", "kpi_sla", default=False)` -- read a nested config value.
- `ctx.load_report("docsops_status.json")` -- load a JSON report as a dict.
- `ctx.write_report("my_plugin.json", {...})` -- write your own report.
- `ctx.state` -- a mutable dict shared across hooks and plugins in one run.
- `ctx.ok("msg")` / `ctx.fail("msg")` -- build a result to return (optional).

## Make a blocking gate

Raise `PluginBlock` from `before_commit` to stop the pipeline:

```python
from scripts.plugin_api import PluginBlock


def before_commit(ctx):
    changed = ctx.changed_files
    if any(f.startswith("docs/reference/api") for f in changed):
        status = ctx.load_report("api_sdk_drift_report.json")
        if status.get("status") == "drift":
            raise PluginBlock("API docs changed while drift is unresolved")
    return ctx.ok()
```

## Load order and multiple plugins

- Every top-level `*.py` in `client_plugins/` is a plugin (files starting with
  `_` are ignored).
- Order is by `PLUGIN["priority"]` ascending (default 100), then file name.
- Plugin names must be unique.

## What you cannot do (by design)

- You cannot change how scoring, retrieval/RAG, contract validation, or the LLM
  policy packs work -- those are the protected core. You consume their outputs
  (via reports) and add behavior around them.
- If you find yourself wanting to edit the core, that is a signal to request a
  new hook or config option from the vendor rather than forking.

## Config-only extension (no code)

For simple additions you may not need a plugin at all. `client_runtime.yml`
already supports `custom_tasks.weekly` and `custom_tasks.on_demand` -- lists of
shell commands the pipeline runs at defined points. Use those for "run my
script" needs; use plugins when you need pipeline context or a gate.

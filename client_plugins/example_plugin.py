"""Example client plugin -- copy this file and adapt it.

This file is disabled (``enabled: False``) so it never runs until you turn it
on. Rename it, set ``enabled: True``, and keep only the hooks you need. You (or
Claude/Codex on your behalf) only ever edit files in this directory -- never the
pipeline core.

See EXTENDING.md for the full contract.
"""

# Optional metadata. name defaults to the file stem; priority orders plugins
# (ascending, default 100); set enabled True to activate.
PLUGIN = {
    "name": "example",
    "priority": 100,
    "enabled": False,
}


def before_pipeline(ctx):
    """Runs before any stage. ctx is a PipelineContext (see scripts/plugin_api.py)."""
    docs_root = ctx.docs_root
    print(f"[example] pipeline starting; docs root = {docs_root}")
    # Stash something for a later hook:
    ctx.state["example_started"] = True
    return ctx.ok("example before_pipeline ran")


def after_pipeline(ctx):
    """Runs after all stages. Read any report the pipeline produced."""
    status = ctx.load_report("docsops_status.json")
    quality = status.get("quality_score", "n/a")
    ctx.write_report("example_plugin_report.json", {"observed_quality_score": quality})
    return ctx.ok(f"example saw quality_score={quality}")


def before_commit(ctx):
    """Runs before the commit/review-branch stage.

    To turn this into a blocking gate, raise PluginBlock:

        from scripts.plugin_api import PluginBlock
        if some_condition:
            raise PluginBlock("custom gate failed: ...")
    """
    return ctx.ok("example before_commit ran (non-blocking)")

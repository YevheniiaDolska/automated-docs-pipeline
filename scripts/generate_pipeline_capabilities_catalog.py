#!/usr/bin/env python3
"""Generate a full catalog of pipeline capabilities.

Sources:
- package.json scripts
- templates/
- policy_packs/
- knowledge_modules/
- docker-compose*.yml
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_JSON = REPO_ROOT / "package.json"
OUTPUT = REPO_ROOT / "docs" / "operations" / "PIPELINE_CAPABILITIES_CATALOG.md"


def classify(name: str) -> str:
    if name.startswith("api:") or name.startswith("api-first"):
        return "API-first"
    if name.startswith("lint"):
        return "Lint/Quality"
    if name.startswith("validate"):
        return "Validation"
    if name.startswith("gaps"):
        return "Gap detection"
    if name.startswith("kpi"):
        return "KPI/SLA"
    if name.startswith("i18n"):
        return "Localization"
    if name.startswith("build"):
        return "Build/Generate"
    if name.startswith("docs-ops"):
        return "DocsOps tests"
    if name.startswith("agent:") or name.startswith("demo:"):
        return "Agent/Demo"
    return "General"


def main() -> int:
    pkg = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    scripts = pkg.get("scripts", {})
    if not isinstance(scripts, dict):
        raise ValueError("package.json scripts must be a mapping")

    lines: list[str] = []
    lines.append("# Pipeline Capabilities Catalog")
    lines.append("")
    lines.append("This file is auto-generated from `package.json` scripts.")
    lines.append("")
    lines.append("Use this catalog with `runtime.custom_tasks.weekly` in client profiles to enable any capability.")
    lines.append("")
    lines.append("## How to enable any capability for a client")
    lines.append("")
    lines.append("```yaml")
    lines.append("runtime:")
    lines.append("  custom_tasks:")
    lines.append("    weekly:")
    lines.append("      - id: \"my-task\"")
    lines.append("        enabled: true")
    lines.append("        command: \"npm run <script-name>\"")
    lines.append("        continue_on_error: true")
    lines.append("```")
    lines.append("")
    lines.append("| Script | Category | Command |")
    lines.append("| --- | --- | --- |")

    for name in sorted(scripts):
        cmd = str(scripts[name]).replace("|", "\\|")
        category = classify(name)
        lines.append(f"| `{name}` | {category} | `{cmd}` |")

    templates = sorted((REPO_ROOT / "templates").glob("*"))
    if templates:
        lines.append("")
        lines.append("## Templates")
        lines.append("")
        lines.append("These can be shipped via `bundle.include_paths` and used by LLM generation flow.")
        lines.append("")
        for p in templates:
            if p.name == "legal":
                continue
            lines.append(f"- `{p.as_posix().replace(str(REPO_ROOT.as_posix()) + '/', '')}`")

    packs = sorted((REPO_ROOT / "policy_packs").glob("*.yml"))
    if packs:
        lines.append("")
        lines.append("## Policy Packs")
        lines.append("")
        for p in packs:
            lines.append(f"- `{p.name}`")

    modules = sorted((REPO_ROOT / "knowledge_modules").glob("*.yml"))
    if modules:
        lines.append("")
        lines.append("## Knowledge Modules")
        lines.append("")
        lines.append("Can be copied into client bundle with `bundle.include_paths: ['knowledge_modules']`.")
        lines.append("")
        for p in modules:
            lines.append(f"- `{p.name}`")

    compose = sorted(REPO_ROOT.glob("docker-compose*.yml"))
    if compose:
        lines.append("")
        lines.append("## Docker Compose Profiles")
        lines.append("")
        for p in compose:
            lines.append(f"- `{p.name}`")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[ok] catalog generated: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

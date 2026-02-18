#!/usr/bin/env python3
"""Generate release docs pack: changelog draft, migration notes, and breaking-change checklist."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def _run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _previous_tag(current_tag: str) -> str | None:
    try:
        tags = _run_git(["tag", "--sort=-creatordate"]).splitlines()
    except subprocess.CalledProcessError:
        return None

    if not tags:
        return None

    if current_tag in tags:
        idx = tags.index(current_tag)
        if idx + 1 < len(tags):
            return tags[idx + 1]
        return None

    return tags[0]


def _commits_since(range_spec: str) -> list[str]:
    try:
        output = _run_git(["log", "--pretty=format:%h %s", range_spec])
    except subprocess.CalledProcessError:
        return []

    if not output:
        return []
    return output.splitlines()


def _section(title: str, commits: list[str]) -> str:
    if not commits:
        return f"## {title}\n\n- none\n\n"
    lines = "\n".join(f"- {line}" for line in commits)
    return f"## {title}\n\n{lines}\n\n"


def build_release_pack(version: str | None) -> str:
    effective_version = version or "unversioned-release"
    prev = _previous_tag(effective_version) if version else _previous_tag("")

    if prev and version:
        range_spec = f"{prev}..{version}"
    elif prev:
        range_spec = f"{prev}..HEAD"
    else:
        range_spec = "HEAD~30..HEAD"

    commits = _commits_since(range_spec)
    feats = [c for c in commits if " feat:" in c or c.startswith("feat:") or "feat(" in c]
    fixes = [c for c in commits if " fix:" in c or c.startswith("fix:") or "fix(" in c]
    docs = [c for c in commits if " docs:" in c or c.startswith("docs:") or "docs(" in c]
    breaking = [c for c in commits if "breaking" in c.lower()]

    return (
        f"# Release Docs Pack\n\n"
        f"Version: **{effective_version}**\n"
        f"Commit range: `{range_spec}`\n\n"
        "## Executive Summary\n\n"
        "This package is generated automatically to accelerate release communication and reduce docs drift.\n\n"
        + _section("Draft changelog - features", feats)
        + _section("Draft changelog - fixes", fixes)
        + _section("Draft changelog - documentation", docs)
        + _section("Potential breaking changes", breaking)
        + "## Migration Notes Checklist\n\n"
        "- [ ] Identify impacted API endpoints and SDK methods.\n"
        "- [ ] Add before/after request and response examples.\n"
        "- [ ] Include rollout and rollback instructions.\n"
        "- [ ] Include compatibility matrix and deprecation dates.\n\n"
        "## Breaking Change Acceptance Checklist\n\n"
        "- [ ] Every breaking change has mitigation guidance.\n"
        "- [ ] Every breaking change has a migration path.\n"
        "- [ ] Every breaking change has a test plan.\n"
        "- [ ] Customer communication snippets are prepared.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate release docs pack")
    parser.add_argument("--version", help="Release version/tag (optional)")
    parser.add_argument("--output", default="reports/release-docs-pack.md", help="Output Markdown file")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_release_pack(args.version), encoding="utf-8")
    print(f"Release docs pack written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

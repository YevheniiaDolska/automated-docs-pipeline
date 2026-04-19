#!/usr/bin/env python3
"""Build all intent experiences for active knowledge modules."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml

CHANNELS = ["docs", "assistant", "automation", "in-product", "field", "sales"]


def _load_modules(modules_dir: Path) -> list[dict]:
    modules: list[dict] = []
    for path in sorted(modules_dir.glob("*.yml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and payload.get("status") == "active":
            modules.append(payload)
    return modules


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build all intent experiences")
    parser.add_argument("--modules-dir", default="knowledge_modules")
    parser.add_argument("--docs-output-dir", default="docs/reference/intent-experiences")
    parser.add_argument("--bundle-output-dir", default="reports/intent-bundles")
    return parser.parse_args()


def _resolve_assemble_script() -> Path:
    local = Path(__file__).resolve().parent / "assemble_intent_experience.py"
    if local.exists():
        return local
    cwd = Path.cwd()
    candidates = [
        cwd / "scripts" / "assemble_intent_experience.py",
        cwd / "docsops" / "scripts" / "assemble_intent_experience.py",
    ]
    for path in candidates:
        if path.exists():
            return path
    return local


def main() -> None:
    args = parse_args()
    modules = _load_modules(Path(args.modules_dir))
    assemble_script = _resolve_assemble_script()

    combinations: set[tuple[str, str]] = set()
    for module in modules:
        intents = [str(value) for value in module.get("intents", [])]
        audiences = [str(value) for value in module.get("audiences", [])]
        for intent in intents:
            for audience in audiences:
                combinations.add((intent, audience))

    if not combinations:
        print("No active module combinations found")
        return

    for intent, audience in sorted(combinations):
        for channel in CHANNELS:
            result = subprocess.run(
                [
                    "python3",
                    str(assemble_script),
                    "--modules-dir",
                    args.modules_dir,
                    "--intent",
                    intent,
                    "--audience",
                    audience,
                    "--channel",
                    channel,
                    "--docs-output-dir",
                    args.docs_output_dir,
                    "--bundle-output-dir",
                    args.bundle_output_dir,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"Failed to assemble {intent}/{audience}/{channel}: {result.stderr.strip()}"
                )

    print(f"Built intent experiences for {len(combinations)} intent/audience combinations")


if __name__ == "__main__":
    main()

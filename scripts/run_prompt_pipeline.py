#!/usr/bin/env python3
"""Run docs generation from short prompt(s) and execute full autopipeline.

User flow:
- provide one short prompt OR a text file with prompts (one per line)
- script infers doc type/output targets
- creates docs via new_doc.py
- runs full autopipeline with optional consolidated report and review mode
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from scripts.flow_feedback import FlowNarrator

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_TYPES = {"tutorial", "how-to", "concept", "reference", "troubleshooting", "api"}


@dataclass
class DocTask:
    doc_type: str
    title: str
    output: str = ""


def _run(cmd: list[str]) -> int:
    print(f"[prompt:pipeline] $ {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False)
    return int(completed.returncode)


def _default_runtime() -> Path | None:
    candidate = REPO_ROOT / "docsops" / "config" / "client_runtime.yml"
    return candidate if candidate.exists() else None


def _clean_slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "generated-doc"


def _infer_doc_type(prompt: str) -> str:
    p = prompt.lower()
    if "tutorial" in p or "туториал" in p:
        return "tutorial"
    if "how-to" in p or "how to" in p or "гайд" in p or "инструк" in p:
        return "how-to"
    if "concept" in p or "концеп" in p or "методолог" in p:
        return "concept"
    if "troubleshoot" in p or "debug" in p or "проблем" in p or "ошиб" in p:
        return "troubleshooting"
    if "api" in p or "reference" in p or "референс" in p:
        return "reference"
    return "how-to"


def _infer_title(prompt: str, doc_type: str) -> str:
    p = prompt.strip()
    if len(p) <= 120:
        return p[0].upper() + p[1:] if p else f"{doc_type.title()} document"
    return f"{doc_type.title()} document"


def _infer_output(prompt: str, doc_type: str) -> str:
    p = prompt.lower()
    if "grpc" in p:
        return "docs/reference/grpc-api.md"
    if "graphql" in p:
        return "docs/reference/graphql-api.md"
    if "asyncapi" in p:
        return "docs/reference/asyncapi-api.md"
    if "websocket" in p:
        return "docs/reference/websocket-api.md"
    if "rest" in p or "openapi" in p:
        return "docs/reference/rest-api.md"

    folder_map = {
        "tutorial": "docs/getting-started",
        "how-to": "docs/how-to",
        "concept": "docs/concepts",
        "reference": "docs/reference",
        "troubleshooting": "docs/troubleshooting",
        "api": "docs/reference",
    }
    base = folder_map.get(doc_type, "docs/how-to")
    return f"{base}/{_clean_slug(prompt)}.md"


def _prompts_from_file(path: Path) -> list[str]:
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def _parse_tasks(prompt: str | None, prompt_file: str | None) -> list[DocTask]:
    prompts: list[str] = []
    if prompt:
        prompts.append(prompt.strip())
    if prompt_file:
        prompts.extend(_prompts_from_file(Path(prompt_file).resolve()))
    prompts = [p for p in prompts if p]
    if not prompts:
        raise ValueError("Provide --prompt or --prompt-file with at least one request.")

    tasks: list[DocTask] = []
    for p in prompts:
        doc_type = _infer_doc_type(p)
        title = _infer_title(p, doc_type)
        output = _infer_output(p, doc_type)
        tasks.append(DocTask(doc_type=doc_type, title=title, output=output))
    return tasks


def _scope_tokens_from_tasks(tasks: list[DocTask]) -> tuple[set[str], set[str]]:
    joined = " ".join(f"{t.title} {t.output}" for t in tasks).lower()
    allowed: set[str] = set()
    if "acme" in joined:
        allowed.add("acme")
    if "taskstream" in joined:
        allowed.add("taskstream")
    # Default forbidden foreign demo/client slugs.
    forbidden = {"taskstream", "blockstream-demo", "acme"}
    forbidden = {f for f in forbidden if f not in allowed}
    return allowed, forbidden


def _scope_guard(paths: list[Path], forbidden_tokens: set[str]) -> None:
    if not forbidden_tokens:
        return
    violations: list[str] = []
    patterns = [re.compile(rf"\b{re.escape(token)}\b", re.IGNORECASE) for token in sorted(forbidden_tokens)]
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in patterns:
            if pattern.search(text):
                violations.append(f"{path}: contains '{pattern.pattern}'")
                break
    if violations:
        raise RuntimeError(
            "Project scope guard failed. Generated content contains foreign project markers:\n- "
            + "\n- ".join(violations)
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate docs from short prompt(s) and run autopipeline")
    parser.add_argument("--prompt", default="", help='Short request, e.g. "Сгенерируй API-референс для gRPC"')
    parser.add_argument("--prompt-file", default="", help="Text file with prompts, one per line")
    parser.add_argument("--locale", default="")
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--runtime-config", default="")
    parser.add_argument("--mode", choices=["operator", "veridoc"], default="operator")
    parser.add_argument("--with-consolidated-report", action="store_true")
    parser.add_argument("--since", type=int, default=7)
    args = parser.parse_args()
    narrator = FlowNarrator("Prompt-to-pipeline flow", total_steps=3)
    narrator.start("Create docs from plain-language prompts and run full autopipeline.")

    tasks = _parse_tasks(args.prompt or None, args.prompt_file or None)
    narrator.stage(1, "Interpret prompts", f"Tasks detected: {len(tasks)}")
    runtime_path = Path(args.runtime_config) if args.runtime_config else _default_runtime()
    if runtime_path is None:
        print("[prompt:pipeline] Runtime config missing at docsops/config/client_runtime.yml.")
        print("[prompt:pipeline] Pass --runtime-config <path>.")
        narrator.finish(False, "Runtime config is missing")
        return 2
    narrator.done(f"Runtime config: {runtime_path}")

    generated_paths: list[Path] = []
    narrator.stage(2, "Generate requested documents", "Create docs from tasks")
    for task in tasks:
        narrator.note(f"{task.doc_type}: {task.title} -> {task.output}")
        create_cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "new_doc.py"),
            task.doc_type,
            task.title,
            "--docs-dir",
            args.docs_dir,
            "--output",
            task.output,
        ]
        if args.locale:
            create_cmd.extend(["--locale", args.locale])
        rc = _run(create_cmd)
        if rc != 0:
            narrator.finish(False, f"Doc generation failed with rc={rc}")
            return rc
        generated_paths.append((REPO_ROOT / task.output).resolve())

    _, forbidden_tokens = _scope_tokens_from_tasks(tasks)
    try:
        _scope_guard(generated_paths, forbidden_tokens)
    except RuntimeError as exc:
        print(f"[prompt:pipeline] {exc}")
        narrator.finish(False, "Scope guard failed")
        return 3
    narrator.done("All generated docs passed scope guard")

    narrator.stage(3, "Run full autopipeline", "Execute weekly + quality + review stages automatically")
    pipeline_cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "run_autopipeline.py"),
        "--docsops-root",
        ".",
        "--reports-dir",
        args.reports_dir,
        "--runtime-config",
        str(runtime_path),
        "--mode",
        args.mode,
        "--since",
        str(args.since),
    ]
    if not args.with_consolidated_report:
        pipeline_cmd.append("--skip-consolidated-report")
    if args.mode == "veridoc":
        pipeline_cmd.append("--skip-local-llm-packet")

    rc = _run(pipeline_cmd)
    narrator.finish(rc == 0, f"Autopipeline rc={rc}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

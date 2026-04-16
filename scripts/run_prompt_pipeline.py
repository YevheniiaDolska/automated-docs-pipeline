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
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import yaml

try:
    from scripts.flow_feedback import FlowNarrator
except ModuleNotFoundError:  # bundle layout: docsops/scripts/*
    from flow_feedback import FlowNarrator

REPO_ROOT = Path(__file__).resolve().parents[1]
EXEC_ROOT = REPO_ROOT.parent if REPO_ROOT.name == "docsops" else REPO_ROOT
DOC_TYPES = {"tutorial", "how-to", "concept", "reference", "troubleshooting", "api"}

DOC_TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "tutorial": (
        "tutorial", "туториал", "учебник", "guide for beginners",
        "tutoriale", "tutoriales", "tutoriel", "anleitung", "leitfaden",
        "tutoriale", "guida introduttiva", "教程", "チュートリアル", "튜토리얼",
    ),
    "how-to": (
        "how-to", "how to", "guide", "гайд", "инструк", "как сделать",
        "como", "guia", "guía", "comment", "anleitung", "wie", "como fazer",
        "come fare", "how do i", "手順", "指南", "방법", "jak", "instrukcja", "دليل", "कैसे",
    ),
    "concept": (
        "concept", "концеп", "методолог", "architecture", "архитектура",
        "concepto", "conceptos", "conceptuel", "konzept", "conceito", "concetto",
        "概念", "アーキテクチャ", "개념", "koncepcja", "مفهوم", "अवधारणा",
    ),
    "troubleshooting": (
        "troubleshoot", "debug", "problem", "issue", "error", "ошиб", "проблем",
        "depurar", "problema", "erro", "erreur", "fehler", "risolvere", "corriger",
        "故障", "问题", "トラブル", "오류", "blad", "błąd", "خطا", "خطأ", "समस्या", "त्रुटि",
    ),
    "reference": (
        "api", "reference", "референс", "справочник", "documentation",
        "documentación", "referencia", "référence", "referenz", "documentacao",
        "documentação", "riferimento", "api文档", "api ドキュメント", "api 문서",
        "dokumentacja", "توثيق", "एपीआई दस्तावेज",
    ),
}

PROTOCOL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "grpc": ("grpc", "g-r-p-c", "g rpc"),
    "graphql": ("graphql", "graph ql", "graph-ql"),
    "asyncapi": ("asyncapi", "async api", "event api", "событийн"),
    "websocket": ("websocket", "web socket", "ws api"),
    "rest": ("rest", "openapi", "open api", "restful", "рест", "оpenapi"),
}

EXPLICIT_LOCALE_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("en", ("in english", "на английском", "en ingles", "en inglés", "en anglais", "auf englisch", "in inglese", "po angielsku", "بالانجليزية", "अंग्रेज़ी में")),
    ("de", ("in german", "на немецком", "en aleman", "en alemán", "en allemand", "auf deutsch", "in tedesco", "po niemiecku", "بالالمانية", "जर्मन में")),
    ("fr", ("in french", "на французском", "en frances", "en francés", "en francais", "en français", "auf franzosisch", "auf französisch", "in francese", "po francusku", "بالفرنسية", "फ्रेंच में")),
    ("ru", ("in russian", "на русском", "en ruso", "en russe", "auf russisch", "in russo", "po rosyjsku", "بالروسية", "रूसी में")),
    ("es", ("in spanish", "на испанском", "en espanol", "en español", "en espagnol", "auf spanisch", "in spagnolo", "po hiszpansku", "بالاسبانية", "स्पेनिश में")),
    ("it", ("in italian", "на итальянском", "en italiano", "en italien", "auf italienisch", "in italiano", "po wlosku", "po włosku", "بالايطالية", "इटालियन में")),
    ("pl", ("in polish", "на польском", "en polaco", "en polonais", "auf polnisch", "in polacco", "po polsku", "بالبولندية", "पोलिश में")),
    ("zh", ("in chinese", "на китайском", "en chino", "en chinois", "auf chinesisch", "in cinese", "po chinsku", "po chińsku", "بالصينية", "中文", "汉语", "普通话", "चीनी में")),
    ("ar", ("in arabic", "на арабском", "en arabe", "en árabe", "auf arabisch", "in arabo", "po arabsku", "بالعربية", "अरबी में")),
    ("hi", ("in hindi", "на хинди", "en hindi", "auf hindi", "in hindi", "po hindi", "بالهندية", "हिंदी में")),
]


@dataclass
class DocTask:
    doc_type: str
    title: str
    output: str = ""
    locale: str = "en"
    protocol: str = ""


def _run(cmd: list[str]) -> int:
    print(f"[prompt:pipeline] $ {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=str(EXEC_ROOT), check=False)
    return int(completed.returncode)


def _default_runtime() -> Path | None:
    candidates = [
        REPO_ROOT / "docsops" / "config" / "client_runtime.yml",
        REPO_ROOT / "config" / "client_runtime.yml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _clean_slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "generated-doc"


def _normalize_prompt(prompt: str) -> str:
    lowered = prompt.casefold()
    normalized = unicodedata.normalize("NFKC", lowered)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _infer_protocol(prompt: str) -> str:
    p = _normalize_prompt(prompt)
    for protocol, keywords in PROTOCOL_KEYWORDS.items():
        if _contains_any(p, keywords):
            return protocol
    return ""


def _infer_doc_type(prompt: str) -> str:
    p = _normalize_prompt(prompt)
    protocol = _infer_protocol(p)
    if protocol:
        return "reference"
    for doc_type in ("troubleshooting", "tutorial", "how-to", "concept", "reference"):
        if _contains_any(p, DOC_TYPE_KEYWORDS[doc_type]):
            return doc_type
    return "how-to"


def _infer_requested_locale(prompt: str) -> str:
    p = _normalize_prompt(prompt)
    for locale, patterns in EXPLICIT_LOCALE_PATTERNS:
        if _contains_any(p, patterns):
            return locale
    return ""


def _infer_title(prompt: str, doc_type: str, protocol: str = "", explicit_locale: str = "") -> str:
    if not protocol and not explicit_locale:
        p = prompt.strip()
        if len(p) <= 120:
            return p[0].upper() + p[1:] if p else f"{doc_type.title()} document"
        return f"{doc_type.title()} document"
    if not explicit_locale:
        protocol_titles = {
            "rest": "REST API reference",
            "graphql": "GraphQL API reference",
            "grpc": "gRPC API reference",
            "asyncapi": "AsyncAPI reference",
            "websocket": "WebSocket API reference",
        }
        if protocol in protocol_titles:
            return protocol_titles[protocol]
        generic_titles = {
            "tutorial": "Tutorial guide",
            "how-to": "How-to guide",
            "concept": "Concept overview",
            "reference": "Reference documentation",
            "troubleshooting": "Troubleshooting guide",
            "api": "API reference",
        }
        return generic_titles.get(doc_type, "How-to guide")
    p = prompt.strip()
    if len(p) <= 120:
        return p[0].upper() + p[1:] if p else f"{doc_type.title()} document"
    return f"{doc_type.title()} document"


def _infer_output(prompt: str, doc_type: str) -> str:
    protocol = _infer_protocol(prompt)
    if protocol == "grpc":
        return "docs/reference/grpc-api.md"
    if protocol == "graphql":
        return "docs/reference/graphql-api.md"
    if protocol == "asyncapi":
        return "docs/reference/asyncapi-api.md"
    if protocol == "websocket":
        return "docs/reference/websocket-api.md"
    if protocol == "rest":
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
        explicit_locale = _infer_requested_locale(p)
        protocol = _infer_protocol(p)
        doc_type = _infer_doc_type(p)
        title = _infer_title(p, doc_type, protocol, explicit_locale)
        output = _infer_output(p, doc_type)
        locale = explicit_locale or "en"
        tasks.append(
            DocTask(
                doc_type=doc_type,
                title=title,
                output=output,
                locale=locale,
                protocol=protocol,
            )
        )
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


def _write_if_missing(path: Path, content: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _bootstrap_protocol_contract_seed(repo_root: Path, runtime_path: Path, protocol: str) -> None:
    protocol = protocol.strip().lower()
    if not protocol:
        return
    runtime: dict[str, object] = {}
    try:
        runtime = yaml.safe_load(runtime_path.read_text(encoding="utf-8")) or {}
    except (RuntimeError, ValueError, TypeError, OSError):
        runtime = {}
    if not isinstance(runtime, dict):
        runtime = {}

    api_first = runtime.get("api_first", {}) if isinstance(runtime.get("api_first"), dict) else {}
    protocol_settings = (
        runtime.get("api_protocol_settings", {})
        if isinstance(runtime.get("api_protocol_settings"), dict)
        else {}
    )
    cfg = protocol_settings.get(protocol, {}) if isinstance(protocol_settings.get(protocol), dict) else {}

    default_paths = {
        "rest": str(api_first.get("spec_path", "api/openapi.yaml")).strip() or "api/openapi.yaml",
        "graphql": str(cfg.get("contract_path", "api/schema.graphql")).strip() or "api/schema.graphql",
        "grpc": str(cfg.get("contract_path", "api/proto")).strip() or "api/proto",
        "asyncapi": str(cfg.get("contract_path", "api/asyncapi.yaml")).strip() or "api/asyncapi.yaml",
        "websocket": str(cfg.get("contract_path", "api/websocket.yaml")).strip() or "api/websocket.yaml",
    }
    rel_path = default_paths.get(protocol, "")
    if not rel_path:
        return
    target = (repo_root / rel_path).resolve()
    default_notes_paths = {
        "rest": str(api_first.get("notes_path", "notes/api-planning.md")).strip() or "notes/api-planning.md",
        "graphql": str(cfg.get("notes_path", "notes/graphql-api-planning.md")).strip() or "notes/graphql-api-planning.md",
        "grpc": str(cfg.get("notes_path", "notes/grpc-api-planning.md")).strip() or "notes/grpc-api-planning.md",
        "asyncapi": str(cfg.get("notes_path", "notes/asyncapi-planning.md")).strip() or "notes/asyncapi-planning.md",
        "websocket": str(cfg.get("notes_path", "notes/websocket-api-planning.md")).strip() or "notes/websocket-api-planning.md",
    }
    notes_rel = default_notes_paths.get(protocol, "")
    if notes_rel:
        notes_target = (repo_root / notes_rel).resolve()
        notes_seed = (
            "# API planning notes\n\n"
            "Project: **TaskStream**\n"
            "API version: **v1**\n"
            "Base URL: `https://api.taskstream.example.com/v1`\n"
            "- `GET /projects` — List projects\n"
            "- `POST /projects` — Create project\n"
            "- `GET /users/me` — Get current user\n"
        )
        if protocol == "graphql":
            notes_seed = (
                "# GraphQL API planning notes\n\n"
                "Project: **TaskStream**\n"
                "API version: **v1**\n"
                "- query `project(id: ID!)`: fetch a project by id\n"
                "- query `projects`: list projects\n"
                "- mutation `createProject(name: String!)`: create project\n"
            )
        elif protocol == "grpc":
            notes_seed = (
                "# gRPC API planning notes\n\n"
                "Service: TaskStreamService\n"
                "- rpc GetProject(GetProjectRequest) returns (Project)\n"
                "- rpc ListProjects(ListProjectsRequest) returns (ListProjectsResponse)\n"
            )
        elif protocol == "asyncapi":
            notes_seed = (
                "# AsyncAPI planning notes\n\n"
                "Channel: project.updated\n"
                "- publish project.updated events with project_id and status\n"
            )
        elif protocol == "websocket":
            notes_seed = (
                "# WebSocket planning notes\n\n"
                "Channel: project.updated\n"
                "- subscribe to project.updated\n"
                "- publish project.updated acknowledgements\n"
            )
        _write_if_missing(
            notes_target,
            notes_seed,
        )

    if protocol == "rest":
        _write_if_missing(
            target,
            "openapi: 3.0.3\n"
            "info:\n"
            "  title: Seed REST API\n"
            "  version: 1.0.0\n"
            "paths:\n"
            "  /health:\n"
            "    get:\n"
            "      responses:\n"
            "        '200':\n"
            "          description: OK\n",
        )
        return
    if protocol == "graphql":
        _write_if_missing(
            target,
            "type Query {\n"
            "  health: String!\n"
            "}\n",
        )
        return
    if protocol == "grpc":
        proto_file = target / "seed.proto" if target.suffix == "" else target
        _write_if_missing(
            proto_file,
            'syntax = "proto3";\n'
            "package seed;\n"
            "service HealthService {\n"
            "  rpc Check (HealthRequest) returns (HealthResponse);\n"
            "}\n"
            "message HealthRequest {}\n"
            "message HealthResponse { string status = 1; }\n",
        )
        return
    if protocol == "asyncapi":
        _write_if_missing(
            target,
            "asyncapi: '2.6.0'\n"
            "info:\n"
            "  title: Seed AsyncAPI\n"
            "  version: '1.0.0'\n"
            "channels:\n"
            "  health:\n"
            "    publish:\n"
            "      message:\n"
            "        payload:\n"
            "          type: object\n"
            "          properties:\n"
            "            status:\n"
            "              type: string\n",
        )
        return
    if protocol == "websocket":
        _write_if_missing(
            target,
            "openapi: 3.0.3\n"
            "info:\n"
            "  title: Seed WebSocket Contract\n"
            "  version: 1.0.0\n"
            "x-websocket:\n"
            "  endpoint: wss://echo.websocket.events\n"
            "  channels:\n"
            "    - name: health\n"
            "      messages:\n"
            "        - type: health.ping\n",
        )
        return


def _api_first_args_from_runtime(runtime_path: Path) -> list[str]:
    try:
        runtime = yaml.safe_load(runtime_path.read_text(encoding="utf-8")) or {}
    except (RuntimeError, ValueError, TypeError, OSError):
        runtime = {}
    if not isinstance(runtime, dict):
        runtime = {}
    api_first = runtime.get("api_first", {})
    if not isinstance(api_first, dict):
        api_first = {}
    project_slug = str(api_first.get("project_slug", "acme")).strip() or "acme"
    notes_path = str(api_first.get("notes_path", "notes/api-planning.md")).strip() or "notes/api-planning.md"
    spec_path = str(api_first.get("spec_path", "api/openapi.yaml")).strip() or "api/openapi.yaml"
    spec_tree = str(api_first.get("spec_tree_path", "api/acme")).strip() or "api/acme"
    return [
        "--project-slug",
        project_slug,
        "--notes",
        notes_path,
        "--spec",
        spec_path,
        "--spec-tree",
        spec_tree,
    ]


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
    if not runtime_path.is_absolute():
        cwd_candidate = (Path.cwd() / runtime_path).resolve()
        repo_candidate = (REPO_ROOT / runtime_path).resolve()
        runtime_path = cwd_candidate if cwd_candidate.exists() else repo_candidate
    narrator.done(f"Runtime config: {runtime_path}")

    generated_paths: list[Path] = []
    narrator.stage(2, "Generate requested documents", "Create docs from tasks")
    for task in tasks:
        if task.protocol:
            narrator.note(f"{task.protocol}: route to protocol pipeline")
        else:
            narrator.note(f"{task.doc_type}: {task.title} -> {task.output}")
        if task.protocol:
            _bootstrap_protocol_contract_seed(REPO_ROOT, runtime_path, task.protocol)
            if task.protocol == "rest":
                protocol_cmd = [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "run_api_first_flow.py"),
                ]
                protocol_cmd.extend(_api_first_args_from_runtime(runtime_path))
                protocol_cmd.extend(
                    [
                    "--runtime-config",
                    str(runtime_path),
                    ]
                )
            else:
                protocol_cmd = [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "run_multi_protocol_contract_flow.py"),
                    "--runtime-config",
                    str(runtime_path),
                    "--reports-dir",
                    args.reports_dir,
                    "--protocols",
                    task.protocol,
                ]
            rc = _run(protocol_cmd)
            if rc != 0:
                narrator.finish(False, f"Protocol pipeline failed for {task.protocol} with rc={rc}")
                return rc
            generated_paths.append((REPO_ROOT / task.output).resolve())
            continue
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
        task_locale = args.locale or task.locale
        if task_locale:
            create_cmd.extend(["--locale", task_locale])
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
        "docsops" if (EXEC_ROOT / "docsops").exists() else ".",
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

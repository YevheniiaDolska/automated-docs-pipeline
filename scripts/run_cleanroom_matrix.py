#!/usr/bin/env python3
"""Run clean-room bundle matrix in docs_test with reset between configurations."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_TEST_ROOT = Path("/mnt/c/Users/Kroha/Documents/development/docs_test")
CLIENT_REPO = DOCS_TEST_ROOT / "client_repo"
PROFILES_DIR = DOCS_TEST_ROOT / "profiles"
REPORT_PATH = REPO_ROOT / "reports" / "cleanroom_matrix_report.json"

MATRIX = [
    {"package": "pilot", "plan": "pilot", "mode": "strict-local"},
    {"package": "pilot", "plan": "pilot", "mode": "hybrid"},
    {"package": "pilot", "plan": "pilot", "mode": "cloud"},
    {"package": "full", "plan": "professional", "mode": "strict-local"},
    {"package": "full", "plan": "professional", "mode": "hybrid"},
    {"package": "full", "plan": "professional", "mode": "cloud"},
    {"package": "full+rag", "plan": "enterprise", "mode": "strict-local"},
    {"package": "full+rag", "plan": "enterprise", "mode": "hybrid"},
    {"package": "full+rag", "plan": "enterprise", "mode": "cloud"},
]


def _run(cmd: list[str], cwd: Path, timeout_sec: int = 1800) -> dict[str, Any]:
    print(f"[cleanroom] RUN ({cwd}): {' '.join(cmd)}", flush=True)
    started = time.time()
    completed = subprocess.run(
        cmd,
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
    )
    duration = round(time.time() - started, 3)
    return {
        "command": " ".join(cmd),
        "rc": int(completed.returncode),
        "ok": completed.returncode == 0,
        "duration_seconds": duration,
        "stdout_tail": (completed.stdout or "")[-4000:],
        "stderr_tail": (completed.stderr or "")[-4000:],
    }


def _seed_client_repo() -> None:
    CLIENT_REPO.mkdir(parents=True, exist_ok=True)
    (CLIENT_REPO / "docs").mkdir(parents=True, exist_ok=True)
    (CLIENT_REPO / "notes").mkdir(parents=True, exist_ok=True)
    (CLIENT_REPO / "api").mkdir(parents=True, exist_ok=True)

    (CLIENT_REPO / "docs" / "index.md").write_text(
        "---\n"
        "title: \"Client docs\"\n"
        "description: \"Client documentation root page for clean-room verification runs.\"\n"
        "content_type: concept\n"
        "product: both\n"
        "tags:\n"
        "  - Concept\n"
        "---\n\n"
        "# Client docs\n\n"
        "Initial page.\n",
        encoding="utf-8",
    )
    (CLIENT_REPO / "mkdocs.yml").write_text(
        "site_name: Cleanroom Client Docs\n"
        "docs_dir: docs\n"
        "nav:\n"
        "  - Home: index.md\n",
        encoding="utf-8",
    )

    notes = {
        "taskstream-planning-notes.md": (
            "# Planning notes\n\n"
            "Project: **Taskstream API**\n"
            "Base URL: `http://localhost:4010/v1`\n"
            "API version: **v1**\n\n"
            "- `GET /projects` — List projects\n"
            "- `POST /projects` — Create project\n"
            "- `GET /tasks` — List tasks\n"
            "- `POST /tasks` — Create task\n"
            "- `GET /users/me` — Get current user profile\n"
        ),
        "graphql-notes.md": "# GraphQL planning notes\n\nCreate GraphQL API with Query health and Mutation createTask.\n",
        "grpc-notes.md": "# gRPC planning notes\n\nDefine TaskService with rpc GetTask and CreateTask.\n",
        "asyncapi-notes.md": "# AsyncAPI planning notes\n\nPublish task.created and task.completed events.\n",
        "websocket-notes.md": "# WebSocket planning notes\n\nProvide channels for task updates and project updates.\n",
    }
    for name, content in notes.items():
        (CLIENT_REPO / "notes" / name).write_text(content, encoding="utf-8")

    _run(["git", "init", "-q"], cwd=CLIENT_REPO, timeout_sec=60)
    _run(["git", "config", "user.email", "qa@example.com"], cwd=CLIENT_REPO, timeout_sec=60)
    _run(["git", "config", "user.name", "qa-bot"], cwd=CLIENT_REPO, timeout_sec=60)
    _run(["git", "add", "-A"], cwd=CLIENT_REPO, timeout_sec=60)
    _run(["git", "commit", "-qm", "init client sandbox"], cwd=CLIENT_REPO, timeout_sec=60)


def _build_profile(config: dict[str, str]) -> Path:
    template = yaml.safe_load((REPO_ROOT / "profiles/clients/_template.client.yml").read_text(encoding="utf-8"))
    if not isinstance(template, dict):
        raise RuntimeError("Invalid template profile")

    package = config["package"]
    plan = config["plan"]
    mode = config["mode"]
    name = f"{package}-{mode}"
    client_id = f"rc-{name}"

    template["client"]["id"] = client_id
    template["client"]["company_name"] = f"RC {name}"
    template["client"]["contact_email"] = "qa@example.com"
    template["client"]["tenant_id"] = client_id
    template["client"]["company_domain"] = "example.com"

    template["licensing"] = {
        "commercial_package": package,
        "plan": plan,
        "days": 30,
        "max_docs": 0,
        "require_signed_jwt": True,
        "manual_jwt_path": "",
        "expose_license_key_env": False,
        "expose_dev_plan_override_env": False,
    }

    template["runtime"]["docs_flow"]["mode"] = "hybrid"
    template["runtime"]["api_first"]["enabled"] = True
    template["runtime"]["api_first"]["project_slug"] = "taskstream"
    template["runtime"]["api_first"]["notes_path"] = "notes/taskstream-planning-notes.md"
    template["runtime"]["api_first"]["spec_path"] = "api/openapi.yaml"
    template["runtime"]["api_first"]["spec_tree_path"] = "api/taskstream"
    template["runtime"]["api_first"]["docs_provider"] = "mkdocs"
    template["runtime"]["api_first"]["sandbox_backend"] = "prism" if mode == "strict-local" else "external"
    template["runtime"]["api_first"]["mock_base_url"] = "http://localhost:4010/v1"
    template["runtime"]["api_first"]["generate_test_assets"] = True
    template["runtime"]["api_first"]["upload_test_assets"] = False

    template["runtime"]["api_protocols"] = ["rest", "graphql", "grpc", "asyncapi", "websocket"]
    template["runtime"]["api_protocol_settings"] = {
        "graphql": {
            "enabled": True,
            "schema_path": "api/schema.graphql",
            "generate_from_notes": True,
            "notes_path": "notes/graphql-notes.md",
            "generate_test_assets": True,
            "upload_test_assets": False,
            "self_verify_runtime": False,
        },
        "grpc": {
            "enabled": True,
            "proto_paths": ["api/proto"],
            "generate_from_notes": True,
            "notes_path": "notes/grpc-notes.md",
            "generate_test_assets": True,
            "upload_test_assets": False,
            "self_verify_runtime": False,
        },
        "asyncapi": {
            "enabled": True,
            "spec_path": "api/asyncapi.yaml",
            "generate_from_notes": True,
            "notes_path": "notes/asyncapi-notes.md",
            "generate_test_assets": True,
            "upload_test_assets": False,
            "self_verify_runtime": False,
        },
        "websocket": {
            "enabled": True,
            "contract_path": "api/websocket.yaml",
            "generate_from_notes": True,
            "notes_path": "notes/websocket-notes.md",
            "generate_test_assets": True,
            "upload_test_assets": False,
            "self_verify_runtime": False,
        },
    }

    security = template["runtime"]["security"]
    llm = template["runtime"]["llm_control"]
    security["hardening_profile"] = "production"
    security["allow_dev_bypass"] = False
    security["anti_tamper_enforced"] = True
    security["require_protected_modules"] = True
    # Clean-room matrix validates functional bundle flows without external pack registry.
    # Dedicated hardening/licensing suites validate premium pack gating behavior.
    security["require_pack_for_premium"] = False

    if mode == "strict-local":
        security["operation_mode"] = "strict-local"
        security["phone_home_enabled_default"] = False
        security["update_check_enabled_default"] = False
        llm["llm_mode"] = "local_default"
        llm["strict_local_first"] = True
        llm["external_llm_allowed"] = False
        llm["require_explicit_approval"] = True
    elif mode == "cloud":
        security["operation_mode"] = "cloud"
        security["phone_home_enabled_default"] = True
        security["update_check_enabled_default"] = True
        llm["llm_mode"] = "external_preferred"
        llm["strict_local_first"] = False
        llm["external_llm_allowed"] = True
        llm["require_explicit_approval"] = False
    else:
        security["operation_mode"] = "hybrid"
        security["phone_home_enabled_default"] = True
        security["update_check_enabled_default"] = True
        llm["llm_mode"] = "external_preferred"
        llm["strict_local_first"] = False
        llm["external_llm_allowed"] = True
        llm["require_explicit_approval"] = False
    # Keep clean-room E2E deterministic and offline-friendly.
    # Local runtime bootstrap is covered by dedicated licensing/hardening tests.
    llm["auto_install_local_model_on_setup"] = False

    rag_enabled = package == "full+rag"
    modules = template["runtime"].get("modules", {})
    if isinstance(modules, dict):
        for key in ("rag_optimization", "ontology_graph", "retrieval_evals"):
            if key in modules:
                modules[key] = rag_enabled

    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    out = PROFILES_DIR / f"{name}.client.yml"
    out.write_text(yaml.safe_dump(template, sort_keys=False, allow_unicode=False), encoding="utf-8")
    return out


def _cleanup_cleanroom() -> None:
    if CLIENT_REPO.exists():
        try:
            shutil.rmtree(CLIENT_REPO)
        except OSError:
            # Windows/WSL occasionally leaves read-only or busy artifacts.
            subprocess.run(["chmod", "-R", "u+w", str(CLIENT_REPO)], check=False)
            subprocess.run(["rm", "-rf", str(CLIENT_REPO)], check=False)
            if CLIENT_REPO.exists():
                raise


def _collect_needs_review_ids() -> list[str]:
    payload = CLIENT_REPO / "reports" / "api-test-assets" / "api_test_cases.json"
    if not payload.exists():
        return []
    try:
        parsed = json.loads(payload.read_text(encoding="utf-8"))
    except (RuntimeError, ValueError, TypeError, OSError):  # noqa: BLE001
        return []
    raw = parsed.get("needs_review_ids", [])
    if isinstance(raw, list):
        return [str(v) for v in raw]
    return []


def _is_expected_license_block(step_name: str, step_result: dict[str, Any], config: dict[str, str]) -> bool:
    stderr_tail = str(step_result.get("stderr_tail", ""))
    if "[license] BLOCKED" not in stderr_tail:
        return False
    package = str(config.get("package", "")).strip().lower()
    if step_name == "api_first_rest" and package == "pilot":
        return True
    if step_name == "multi_protocol" and package == "pilot":
        return True
    return False


def _run_single(config: dict[str, str]) -> dict[str, Any]:
    print(f"[cleanroom] === config: {config['package']} + {config['mode']} ===", flush=True)
    _cleanup_cleanroom()
    _seed_client_repo()
    profile = _build_profile(config)

    steps: dict[str, Any] = {}
    steps["build_bundle"] = _run(
        [
            "python3",
            "scripts/build_client_bundle.py",
            "--client",
            str(profile),
        ],
        cwd=REPO_ROOT,
    )
    steps["provision_install_local"] = _run(
        [
            "python3",
            "scripts/provision_client_repo.py",
            "--client",
            str(profile),
            "--client-repo",
            str(CLIENT_REPO),
            "--docsops-dir",
            "docsops",
            "--install-scheduler",
            "none",
        ],
        cwd=REPO_ROOT,
    )
    if (CLIENT_REPO / "docsops").exists():
        docsops_notes = CLIENT_REPO / "docsops" / "notes"
        docsops_notes.mkdir(parents=True, exist_ok=True)
        for note in (CLIENT_REPO / "notes").glob("*.md"):
            shutil.copy2(note, docsops_notes / note.name)

    steps["setup_wizard"] = _run(
        ["bash", "-lc", "yes '' | python3 docsops/scripts/setup_client_env_wizard.py"],
        cwd=CLIENT_REPO,
        timeout_sec=900,
    )
    steps["weekly_run"] = _run(
        ["python3", "docsops/scripts/run_weekly_gap_batch.py", "--docsops-root", "docsops", "--reports-dir", "reports", "--since", "7"],
        cwd=CLIENT_REPO,
        timeout_sec=1200,
    )
    steps["docs_ci_checks"] = _run(
        ["python3", "docsops/scripts/run_docs_ci_checks.py", "--runtime-config", "docsops/config/client_runtime.yml", "--skip-build"],
        cwd=CLIENT_REPO,
        timeout_sec=1200,
    )
    steps["new_howto"] = _run(
        ["python3", "docsops/scripts/new_doc.py", "how-to", "Configure webhook authentication", "--docs-dir", "docs"],
        cwd=CLIENT_REPO,
    )
    steps["new_reference"] = _run(
        ["python3", "docsops/scripts/new_doc.py", "reference", "Webhook API reference", "--docs-dir", "docs"],
        cwd=CLIENT_REPO,
    )
    steps["api_first_rest"] = _run(
        [
            "python3",
            "docsops/scripts/run_api_first_flow.py",
            "--project-slug",
            "taskstream",
            "--notes",
            "notes/taskstream-planning-notes.md",
            "--spec",
            "api/openapi.yaml",
            "--spec-tree",
            "api/taskstream",
            "--docs-provider",
            "mkdocs",
            "--docs-spec-target",
            "docs/assets/api",
            "--stubs-output",
            "generated/api-stubs/fastapi/app/main.py",
            "--generate-test-assets",
            "--auto-remediate",
            "--max-attempts",
            "2",
            "--no-finalize-gate",
        ],
        cwd=CLIENT_REPO,
        timeout_sec=1200,
    )
    steps["multi_protocol"] = _run(
        [
            "python3",
            "docsops/scripts/run_multi_protocol_contract_flow.py",
            "--runtime-config",
            "docsops/config/client_runtime.yml",
            "--reports-dir",
            "reports",
            "--protocols",
            "graphql,grpc,asyncapi,websocket",
            "--generate-test-assets",
        ],
        cwd=CLIENT_REPO,
        timeout_sec=1200,
    )
    steps["publish_review_branch"] = _run(
        [
            "python3",
            "docsops/scripts/publish_docs_review_branch.py",
            "--runtime-config",
            "docsops/config/client_runtime.yml",
            "--docs-root",
            "docs",
        ],
        cwd=CLIENT_REPO,
        timeout_sec=600,
    )

    needs_review = _collect_needs_review_ids()
    normalized_steps: dict[str, Any] = {}
    for step_name, step_result in steps.items():
        if _is_expected_license_block(step_name, step_result, config):
            adjusted = dict(step_result)
            adjusted["ok"] = True
            adjusted["expected_blocked"] = True
            normalized_steps[step_name] = adjusted
        else:
            normalized_steps[step_name] = step_result
    ok = all(bool(item.get("ok", False)) for item in normalized_steps.values())
    return {
        "config": config,
        "profile": str(profile),
        "steps": normalized_steps,
        "needs_review_ids": needs_review,
        "status": "PASS" if ok else "FAIL",
    }


def main() -> int:
    rows: list[dict[str, Any]] = []
    failures = 0
    for cfg in MATRIX:
        result = _run_single(cfg)
        rows.append(result)
        if result["status"] != "PASS":
            failures += 1
        partial = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "matrix": rows,
            "summary": {
                "total": len(MATRIX),
                "processed": len(rows),
                "passed": len([r for r in rows if r.get("status") == "PASS"]),
                "failed": len([r for r in rows if r.get("status") != "PASS"]),
            },
        }
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(partial, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "matrix": rows,
        "summary": {
            "total": len(rows),
            "passed": len(rows) - failures,
            "failed": failures,
            "status": "PASS" if failures == 0 else "FAIL",
        },
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"[cleanroom-matrix] report: {REPORT_PATH}")
    print(f"[cleanroom-matrix] summary: {payload['summary']['status']} ({payload['summary']['passed']}/{payload['summary']['total']})")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Universal API-first flow runner for any product."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
import shutil as sh


def _print_compact_output(output: str, *, max_lines: int = 28) -> None:
    lines = [line for line in output.splitlines() if line.strip()]
    if not lines:
        return
    if len(lines) <= max_lines:
        for line in lines:
            print(line, flush=True)
        return
    head = lines[:6]
    tail = lines[-12:]
    for line in head:
        print(line, flush=True)
    print(f"[demo] ... {len(lines) - len(head) - len(tail)} lines omitted ...", flush=True)
    for line in tail:
        print(line, flush=True)


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    compact: bool = False,
    summary_label: str | None = None,
) -> None:
    print(f"[run] {' '.join(cmd)}", flush=True)
    completed = subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )
    output = "\n".join([completed.stdout or "", completed.stderr or ""]).strip()
    if output:
        if compact:
            _print_compact_output(output)
        else:
            print(output, flush=True)
    if completed.returncode != 0:
        raise subprocess.CalledProcessError(
            completed.returncode,
            cmd,
            output=completed.stdout,
            stderr=completed.stderr,
        )
    if summary_label:
        print(f"[ok] {summary_label}", flush=True)


def run_first_available(
    candidates: list[list[str]],
    *,
    cwd: Path,
    compact: bool = False,
    summary_label: str | None = None,
) -> None:
    last_error: Exception | None = None
    for cmd in candidates:
        binary = cmd[0]
        if binary != "npx" and sh.which(binary) is None:
            continue
        try:
            run(cmd, cwd=cwd, compact=compact, summary_label=summary_label)
            return
        except Exception as error:  # noqa: BLE001
            last_error = error
            continue
    if last_error:
        raise RuntimeError(f"Unable to execute command candidates: {candidates}. Last error: {last_error}")
    raise RuntimeError(f"No available command candidates found: {candidates}")


def ensure_file(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")


def copy_spec_to_docs(spec_root: Path, docs_target: Path) -> None:
    if docs_target.exists():
        shutil.rmtree(docs_target)
    shutil.copytree(spec_root, docs_target)
    print(f"[ok] copied spec assets to {docs_target}", flush=True)


def build_sandbox_page_url(repo: Path, docs_provider: str) -> str:
    provider = docs_provider.lower()
    if provider == "mkdocs":
        import yaml

        mkdocs_cfg = yaml.safe_load((repo / "mkdocs.yml").read_text(encoding="utf-8")) or {}
        site_url = str(mkdocs_cfg.get("site_url", "")).rstrip("/")
        if site_url:
            return f"{site_url}/reference/taskstream-api-playground/"
        return "/reference/taskstream-api-playground/"
    if provider == "docusaurus":
        return "/docs/reference/taskstream-api-playground"
    return "/reference/taskstream-api-playground/"


def self_verify_stub_coverage(spec_path: Path, stub_file: Path) -> None:
    import yaml

    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    resolved_paths: dict[str, dict] = {}
    for path_name, path_item in (spec.get("paths") or {}).items():
        if isinstance(path_item, dict) and "$ref" in path_item:
            file_ref, _, fragment = path_item["$ref"].partition("#")
            target_file = (spec_path.parent / file_ref).resolve()
            target_data = yaml.safe_load(target_file.read_text(encoding="utf-8")) or {}
            current: object = target_data
            for token in fragment.lstrip("/").split("/"):
                if not token:
                    continue
                current = current[token.replace("~1", "/").replace("~0", "~")]  # type: ignore[index]
            resolved_paths[path_name] = current if isinstance(current, dict) else {}
        elif isinstance(path_item, dict):
            resolved_paths[path_name] = path_item
        else:
            resolved_paths[path_name] = {}

    op_ids: list[str] = []
    for path_item in resolved_paths.values():
        if not isinstance(path_item, dict):
            continue
        for method, op in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head", "trace"}:
                continue
            if isinstance(op, dict) and op.get("operationId"):
                op_ids.append(op["operationId"])

    source = stub_file.read_text(encoding="utf-8")
    missing = [op for op in op_ids if f"def {op}(" not in source]
    if missing:
        raise RuntimeError(f"Stub coverage check failed. Missing operationId handlers: {', '.join(missing)}")

    print(f"[ok] stub self-verification passed ({len(op_ids)} operationIds covered)", flush=True)


def run_one_attempt(
    repo: Path,
    project_slug: str,
    spec: Path,
    spec_tree: Path,
    docs_target: Path,
    stubs_output: Path,
    verify_user_path: bool,
    mock_base_url: str,
    run_docs_lint: bool,
) -> None:
    print("[demo] Step 1/5: Validate contract structure and required metadata.", flush=True)
    run(
        ["python3", "scripts/validate_openapi_contract.py", str(spec)],
        cwd=repo,
        compact=True,
        summary_label="contract validation finished",
    )

    print("[demo] Step 2/5: Run API quality linting (Spectral).", flush=True)
    run_first_available(
        [
            ["spectral", "lint", str(spec), "--ruleset", ".spectral.yml"],
            ["npx", "-y", "@stoplight/spectral-cli", "lint", str(spec), "--ruleset", ".spectral.yml"],
        ],
        cwd=repo,
        compact=True,
        summary_label="spectral lint finished",
    )
    print("[demo] Step 2/5: Run API quality linting (Redocly).", flush=True)
    run_first_available(
        [
            ["redocly", "lint", str(spec)],
            ["npx", "-y", "@redocly/cli", "lint", str(spec)],
        ],
        cwd=repo,
        compact=True,
        summary_label="redocly lint finished",
    )
    print("[demo] Step 2/5: Run API quality linting (Swagger CLI).", flush=True)
    run_first_available(
        [
            ["swagger-cli", "validate", str(spec)],
            ["npx", "-y", "@apidevtools/swagger-cli", "validate", str(spec)],
        ],
        cwd=repo,
        compact=True,
        summary_label="swagger-cli validation finished",
    )

    print("[demo] Step 3/5: Generate server endpoint stubs from operation definitions.", flush=True)
    run(
        [
            "python3",
            "scripts/generate_fastapi_stubs_from_openapi.py",
            "--spec",
            str(spec),
            "--output",
            str(stubs_output),
        ],
        cwd=repo,
        compact=True,
        summary_label="fastapi stubs generated",
    )

    print("[demo] Step 4/5: Publish OpenAPI assets for the docs playground.", flush=True)
    copy_spec_to_docs(spec_tree, docs_target / project_slug)
    shutil.copy2(spec, docs_target / "openapi.yaml")

    print("[demo] Step 4/5: Verify that every operation is covered by a generated handler.", flush=True)
    self_verify_stub_coverage(spec, stubs_output)

    if verify_user_path:
        print("[demo] Step 4/5: Simulate end-user API calls against the live mock server.", flush=True)
        run(
            ["python3", "scripts/self_verify_api_user_path.py", "--base-url", mock_base_url],
            cwd=repo,
            compact=True,
            summary_label="user-path self-verification finished",
        )

    if run_docs_lint:
        print("[demo] Step 5/5: Run documentation quality checks (Vale, markdownlint, SEO/GEO, and more).", flush=True)
        run(["npm", "run", "lint"], cwd=repo, compact=True, summary_label="docs lint stack finished")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run universal API-first production flow")
    parser.add_argument("--project-slug", required=True)
    parser.add_argument("--notes", required=True, help="Planning notes markdown path")
    parser.add_argument("--spec", required=True, help="OpenAPI root spec path")
    parser.add_argument("--spec-tree", required=True, help="Directory with split OpenAPI files")
    parser.add_argument("--docs-provider", default="mkdocs")
    parser.add_argument("--docs-spec-target", default="docs/assets/api")
    parser.add_argument("--stubs-output", default="generated/api-stubs/fastapi/app/main.py")
    parser.add_argument("--verify-user-path", action="store_true")
    parser.add_argument("--mock-base-url", default="http://localhost:4010/v1")
    parser.add_argument("--run-docs-lint", action="store_true")
    parser.add_argument("--auto-remediate", action="store_true")
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--inject-demo-nav", action="store_true")
    parser.add_argument("--skip-generate-from-notes", action="store_true")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    notes = (repo / args.notes).resolve()
    spec = (repo / args.spec).resolve()
    spec_tree = (repo / args.spec_tree).resolve()
    docs_target = (repo / args.docs_spec_target).resolve()
    stubs_output = (repo / args.stubs_output).resolve()

    ensure_file(notes, "planning notes")

    if not args.skip_generate_from_notes:
        print("[demo] Step 0/5: Generate OpenAPI contract from planning notes.", flush=True)
        run(
            [
                "python3",
                "scripts/generate_openapi_from_planning_notes.py",
                "--notes",
                args.notes,
                "--spec",
                args.spec,
                "--spec-tree",
                args.spec_tree,
            ],
            cwd=repo,
            compact=True,
            summary_label="OpenAPI generation from notes finished",
        )

    ensure_file(spec, "OpenAPI spec")
    ensure_file(spec_tree, "OpenAPI split directory")

    if args.inject_demo_nav:
        run(["python3", "scripts/manage_demo_nav.py", "--mode", "add"], cwd=repo)

    last_error: Exception | None = None

    for attempt in range(1, args.max_attempts + 1):
        try:
            print(f"[flow] attempt {attempt}/{args.max_attempts}", flush=True)
            run_one_attempt(
                repo,
                args.project_slug,
                spec,
                spec_tree,
                docs_target,
                stubs_output,
                args.verify_user_path,
                args.mock_base_url,
                args.run_docs_lint,
            )
            print(f"[demo] sandbox page URL: {build_sandbox_page_url(repo, args.docs_provider)}", flush=True)
            print("[ok] API-first production flow completed successfully", flush=True)
            return 0
        except Exception as error:
            last_error = error
            if not args.auto_remediate or attempt >= args.max_attempts:
                break
            print(f"[warn] attempt failed, running remediation sync: {error}", flush=True)
            copy_spec_to_docs(spec_tree, docs_target / args.project_slug)
            shutil.copy2(spec, docs_target / "openapi.yaml")

    raise RuntimeError(f"API-first flow failed after {args.max_attempts} attempt(s): {last_error}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        print(f"[error] command failed with exit code {error.returncode}")
        raise SystemExit(error.returncode)
    except Exception as error:  # pragma: no cover
        print(f"[error] {error}")
        raise SystemExit(1)

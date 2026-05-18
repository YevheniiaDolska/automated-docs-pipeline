#!/usr/bin/env python3
"""Install docs CI pipelines for common git providers and Jenkins.

Supported site generators:
- mkdocs
- sphinx
- docusaurus
- vitepress
- hugo
- jekyll
- docsify
- custom (explicit build command)
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def detect_git_provider(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return "github"
    remote = completed.stdout.strip().lower()
    if "gitlab" in remote:
        return "gitlab"
    if "forgejo" in remote or "codeberg" in remote:
        return "forgejo"
    if "gitea" in remote:
        return "gitea"
    return "github"


def _site_generator(runtime: dict[str, Any]) -> str:
    docs_site = runtime.get("docs_site", {})
    if isinstance(docs_site, dict):
        value = str(docs_site.get("generator", "")).strip().lower()
        if value:
            return value

    targets = runtime.get("output_targets", [])
    if isinstance(targets, list):
        for item in targets:
            val = str(item).strip().lower()
            if val:
                return val
    return "mkdocs"


def _build_command(runtime: dict[str, Any], generator: str) -> str:
    docs_site = runtime.get("docs_site", {})
    if isinstance(docs_site, dict):
        explicit = str(docs_site.get("build_command", "")).strip()
        if explicit:
            return explicit

    mapping = {
        "mkdocs": "mkdocs build --strict",
        "sphinx": "sphinx-build -W -b html docs docs/_build/html",
        "docusaurus": "npm run build",
        "vitepress": "npm run docs:build",
        "hugo": "hugo --minify",
        "jekyll": "bundle exec jekyll build",
        "docsify": "",
        "custom": "",
    }
    return mapping.get(generator, "")


def _lint_command(runtime: dict[str, Any]) -> str:
    finalize = runtime.get("finalize_gate", {})
    if isinstance(finalize, dict):
        cmd = str(finalize.get("lint_command", "")).strip()
        if cmd:
            return cmd
    return "npm run lint"


def _docs_root(runtime: dict[str, Any]) -> str:
    paths = runtime.get("paths", {})
    if isinstance(paths, dict):
        return str(paths.get("docs_root", "docs")).strip() or "docs"
    return "docs"


def _runner_command(runtime_config_path: str = "docsops/config/client_runtime.yml") -> str:
    return f"python3 docsops/scripts/run_docs_ci_checks.py --runtime-config {runtime_config_path}"


def install_docs_ci_files(repo_root: Path, runtime: dict[str, Any], *, install_jenkins: bool = True) -> list[Path]:
    docs_root = _docs_root(runtime)
    provider = detect_git_provider(repo_root)
    generator = _site_generator(runtime)
    build_cmd = _build_command(runtime, generator)
    lint_cmd = _lint_command(runtime)
    runner_cmd = _runner_command()
    created: list[Path] = []

    if provider == "github":
        workflow_dir = repo_root / ".github" / "workflows"
        workflow_dir.mkdir(parents=True, exist_ok=True)
        output = workflow_dir / "docsops-docs-ci.yml"
        content = (
            "name: DocsOps Docs CI\n\n"
            "on:\n"
            "  pull_request:\n"
            f"    paths:\n      - '{docs_root}/**'\n      - 'mkdocs.yml'\n      - 'docsops/**'\n"
            "  push:\n"
            f"    paths:\n      - '{docs_root}/**'\n      - 'mkdocs.yml'\n      - 'docsops/**'\n\n"
            "jobs:\n"
            "  lint-and-build-docs:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "      - uses: actions/setup-node@v4\n"
            "        with:\n"
            "          node-version: '20'\n"
            "      - uses: actions/setup-python@v5\n"
            "        with:\n"
            "          python-version: '3.11'\n"
            "      - name: Install dependencies\n"
            "        run: |\n"
            "          npm ci || true\n"
            "          python3 -m pip install --upgrade pip\n"
            "          python3 -m pip install -r requirements-dev.txt || true\n"
            "          python3 -m pip install mkdocs sphinx || true\n"
            "      - name: Run docs checks\n"
            "        env:\n"
            f"          DOCSOPS_SITE_GENERATOR: '{generator}'\n"
            f"          DOCSOPS_SITE_BUILD_COMMAND: '{build_cmd}'\n"
            f"          DOCSOPS_DOCS_LINT_COMMAND: '{lint_cmd}'\n"
            "        run: |\n"
            f"          {runner_cmd}\n"
        )
        output.write_text(content, encoding="utf-8")
        created.append(output)

    elif provider == "gitlab":
        output = repo_root / ".gitlab-ci.docsops.yml"
        content = (
            "docsops_docs_lint_build:\n"
            "  image: node:20\n"
            "  stage: test\n"
            "  rules:\n"
            f"    - changes:\n        - {docs_root}/**/*\n        - mkdocs.yml\n        - docsops/**/*\n"
            "  before_script:\n"
            "    - apt-get update && apt-get install -y python3 python3-pip\n"
            "    - npm ci || true\n"
            "    - python3 -m pip install --upgrade pip\n"
            "    - python3 -m pip install -r requirements-dev.txt || true\n"
            "    - python3 -m pip install mkdocs sphinx || true\n"
            "  script:\n"
            f"    - DOCSOPS_SITE_GENERATOR='{generator}' DOCSOPS_SITE_BUILD_COMMAND='{build_cmd}' DOCSOPS_DOCS_LINT_COMMAND='{lint_cmd}' {runner_cmd}\n"
        )
        output.write_text(content, encoding="utf-8")
        created.append(output)
        main_ci = repo_root / ".gitlab-ci.yml"
        include_line = "include:\n  - local: '.gitlab-ci.docsops.yml'\n"
        if not main_ci.exists():
            main_ci.write_text(include_line, encoding="utf-8")
        else:
            current = main_ci.read_text(encoding="utf-8")
            if ".gitlab-ci.docsops.yml" not in current:
                main_ci.write_text(current.rstrip() + "\n\n" + include_line, encoding="utf-8")
        created.append(main_ci)

    else:
        workflow_rel = ".forgejo/workflows" if provider == "forgejo" else ".gitea/workflows"
        workflow_dir = repo_root / workflow_rel
        workflow_dir.mkdir(parents=True, exist_ok=True)
        output = workflow_dir / "docsops-docs-ci.yml"
        content = (
            "name: DocsOps Docs CI\n\n"
            "on:\n"
            "  pull_request:\n"
            "  push:\n\n"
            "jobs:\n"
            "  lint-and-build-docs:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "      - uses: actions/setup-node@v4\n"
            "        with:\n"
            "          node-version: '20'\n"
            "      - uses: actions/setup-python@v5\n"
            "        with:\n"
            "          python-version: '3.11'\n"
            "      - name: Install dependencies\n"
            "        run: |\n"
            "          npm ci || true\n"
            "          python3 -m pip install --upgrade pip\n"
            "          python3 -m pip install -r requirements-dev.txt || true\n"
            "          python3 -m pip install mkdocs sphinx || true\n"
            "      - name: Run docs checks\n"
            "        env:\n"
            f"          DOCSOPS_SITE_GENERATOR: '{generator}'\n"
            f"          DOCSOPS_SITE_BUILD_COMMAND: '{build_cmd}'\n"
            f"          DOCSOPS_DOCS_LINT_COMMAND: '{lint_cmd}'\n"
            "        run: |\n"
            f"          {runner_cmd}\n"
        )
        output.write_text(content, encoding="utf-8")
        created.append(output)

    if install_jenkins:
        jenkins = repo_root / "Jenkinsfile.docsops"
        jenkins_content = (
            "pipeline {\n"
            "  agent any\n"
            "  options { timestamps() }\n"
            "  stages {\n"
            "    stage('Checkout') {\n"
            "      steps { checkout scm }\n"
            "    }\n"
            "    stage('Install') {\n"
            "      steps {\n"
            "        sh 'npm ci || true'\n"
            "        sh 'python3 -m pip install --upgrade pip'\n"
            "        sh 'python3 -m pip install -r requirements-dev.txt || true'\n"
            "        sh 'python3 -m pip install mkdocs sphinx || true'\n"
            "      }\n"
            "    }\n"
            "    stage('Docs Lint + Build') {\n"
            "      environment {\n"
            f"        DOCSOPS_SITE_GENERATOR = '{generator}'\n"
            f"        DOCSOPS_SITE_BUILD_COMMAND = '{build_cmd}'\n"
            f"        DOCSOPS_DOCS_LINT_COMMAND = '{lint_cmd}'\n"
            "      }\n"
            "      steps {\n"
            f"        sh '{runner_cmd}'\n"
            "      }\n"
            "    }\n"
            "  }\n"
            "}\n"
        )
        jenkins.write_text(jenkins_content, encoding="utf-8")
        created.append(jenkins)

    return created


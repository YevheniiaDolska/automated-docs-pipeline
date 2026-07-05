#!/usr/bin/env python3
"""Interactive client-side wizard to create .env.docsops.local from template.

Run from client repository root after unpacking docsops bundle:
    python3 docsops/scripts/setup_client_env_wizard.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore

try:
    from scripts.docs_ci_bootstrap import install_docs_ci_files
    from scripts.runtime_config_loader import load_runtime_config
except ModuleNotFoundError:
    # Allow running from client repo where docsops/ is not installed as a package.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from docs_ci_bootstrap import install_docs_ci_files
    from runtime_config_loader import load_runtime_config


ENV_FILE = ".env.docsops.local"
TEMPLATE_FILE = ".env.docsops.local.template"

DEFAULT_ENV_VALUES: dict[str, str] = {
    "VERIOPS_UPDATE_SERVER": "https://updates.veriops.dev",
    "VERIOPS_PHONE_HOME_URL": "https://api.veri-doc.app",
    "VERIOPS_REVOCATION_CHECK_ENABLED": "false",
    "VERIOPS_REVOCATION_URL": "https://api.veri-doc.app/billing/license/revocation-check",
    "VERIOPS_PACK_REGISTRY_URL": "https://api.veri-doc.app/ops/pack-registry/fetch",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Client-side docsops environment setup wizard")
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Non-interactive setup: keep defaults/template values, skip optional prompts, install scheduler.",
    )
    parser.add_argument(
        "--install-ci",
        action="store_true",
        help="Install docs CI workflow files without prompt (default: prompt in interactive mode, skip in --auto).",
    )
    parser.add_argument(
        "--skip-scheduler",
        action="store_true",
        help="Do not install scheduler.",
    )
    parser.add_argument(
        "--install-playwright",
        action="store_true",
        help="Install Python Playwright package and Chromium browser without prompt.",
    )
    parser.add_argument(
        "--skip-screenshot-setup",
        action="store_true",
        help="Skip screenshot automation bootstrap (plan generation + Playwright check).",
    )
    return parser.parse_args()


def _parse_template(template_path: Path) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    pending_comment = ""
    for raw in template_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            pending_comment = line.lstrip("#").strip()
            continue
        if "=" not in line:
            continue
        key, default = line.split("=", 1)
        key = key.strip()
        default = default.strip()
        if not key:
            continue
        items.append((key, pending_comment or default))
        pending_comment = ""
    return items


def _read_existing(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def _write_env(path: Path, values: dict[str, str]) -> None:
    lines = [f"{k}={v}" for k, v in sorted(values.items()) if k]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _ensure_ip_protection_defaults(values: dict[str, str]) -> None:
    for key, default_value in DEFAULT_ENV_VALUES.items():
        current = str(values.get(key, "")).strip()
        if not current:
            values[key] = default_value


def _runtime_integrations(runtime: dict[str, Any]) -> tuple[bool, bool, str]:
    integrations = runtime.get("integrations", {}) if isinstance(runtime.get("integrations"), dict) else {}
    algolia = integrations.get("algolia", {}) if isinstance(integrations.get("algolia"), dict) else {}
    ask_ai = integrations.get("ask_ai", {}) if isinstance(integrations.get("ask_ai"), dict) else {}
    algolia_enabled = bool(algolia.get("enabled", False))
    ask_ai_enabled = bool(ask_ai.get("enabled", False))
    ask_ai_provider = str(ask_ai.get("provider", "openai")).strip().lower()
    return algolia_enabled, ask_ai_enabled, ask_ai_provider


def _is_key_relevant(key: str, algolia_enabled: bool, ask_ai_enabled: bool, ask_ai_provider: str) -> bool:
    if key.startswith("ALGOLIA_"):
        return algolia_enabled
    if key.startswith("OPENAI_") or key.startswith("DOCSOPS_SHARED_OPENAI_API_KEY"):
        return ask_ai_enabled and ask_ai_provider == "openai"
    if key.startswith("ANTHROPIC_"):
        return ask_ai_enabled and ask_ai_provider == "anthropic"
    if key.startswith("AZURE_OPENAI_"):
        return ask_ai_enabled and ask_ai_provider == "azure-openai"
    if key.startswith("ASK_AI_ALERT_"):
        # Owner-alert delivery applies to any provider when Ask AI is enabled.
        return ask_ai_enabled
    if key.startswith("ASK_AI_"):
        return ask_ai_enabled and ask_ai_provider == "custom"
    return True


def _load_runtime(repo_root: Path) -> dict[str, Any]:
    candidates = [
        repo_root / "docsops" / "config" / "client_runtime.yml",
        repo_root / "config" / "client_runtime.yml",
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                raw = load_runtime_config(candidate)
            except (AttributeError, TypeError, ValueError, OSError, RuntimeError):
                raw = {}
            if isinstance(raw, dict):
                return raw
    return {}


def _prompt_yes_no(prompt: str, default_yes: bool = True) -> bool:
    suffix = "[Y/n]" if default_yes else "[y/N]"
    raw = input(f"{prompt} {suffix}: ").strip().lower()
    if not raw:
        return default_yes
    return raw in {"y", "yes"}


def _install_ollama_and_model(model: str) -> None:
    ollama_bin = shutil.which("ollama")
    if ollama_bin is None:
        system = platform.system().lower()
        print("[env-wizard] Ollama is not installed. Attempting auto-install...")
        if system == "linux":
            cmd = "curl -fsSL https://ollama.com/install.sh | sh"
            res = subprocess.run(["bash", "-lc", cmd], check=False)
            if res.returncode != 0:
                print("[env-wizard] Ollama auto-install failed on Linux.")
                print("[env-wizard] Install manually, then run: ollama pull {}".format(model))
                return
        elif system == "darwin":
            if shutil.which("brew"):
                res = subprocess.run(["brew", "install", "ollama"], check=False)
                if res.returncode != 0:
                    print("[env-wizard] brew install ollama failed.")
                    print("[env-wizard] Install Ollama manually and run: ollama pull {}".format(model))
                    return
            else:
                print("[env-wizard] Homebrew not found. Install Ollama manually, then run: ollama pull {}".format(model))
                return
        elif system == "windows":
            if shutil.which("winget"):
                res = subprocess.run(["winget", "install", "-e", "--id", "Ollama.Ollama"], check=False)
                if res.returncode != 0:
                    print("[env-wizard] winget install Ollama failed.")
                    print("[env-wizard] Install Ollama manually and run: ollama pull {}".format(model))
                    return
            else:
                print("[env-wizard] winget not found. Install Ollama manually and run: ollama pull {}".format(model))
                return
        else:
            print("[env-wizard] Unsupported OS for auto-install. Install Ollama manually and run: ollama pull {}".format(model))
            return
        ollama_bin = shutil.which("ollama")
        if ollama_bin is None:
            print("[env-wizard] Ollama still not found in PATH after install.")
            return

    print(f"[env-wizard] Pulling local model: {model}")
    pull = subprocess.run([ollama_bin, "pull", model], check=False)
    if pull.returncode == 0:
        print(f"[env-wizard] Local model ready: {model}")
    else:
        print(f"[env-wizard] Failed to pull model: {model}")
        print(f"[env-wizard] Run manually: ollama pull {model}")


def _create_veridoc_modelfile(repo_root: Path, base_model: str, model_name: str = "veridoc-writer") -> Path:
    docsops_root = repo_root / "docsops"
    sources = [
        docsops_root / "LOCAL_MODEL.md",
        docsops_root / "AGENTS.md",
        docsops_root / "CLAUDE.md",
    ]
    chunks: list[str] = []
    seen: set[str] = set()
    for src in sources:
        if not src.exists():
            continue
        text = src.read_text(encoding="utf-8", errors="ignore")
        key = str(hash(text))
        if key in seen:
            continue
        seen.add(key)
        chunks.append(f"\n# Source: {src.name}\n{text}\n")
    system_prompt = "\n".join(chunks).strip()
    if not system_prompt:
        system_prompt = "Follow project documentation standards strictly."
    system_prompt = system_prompt.replace('"""', '\\"""')
    ollama_dir = docsops_root / "ollama"
    ollama_dir.mkdir(parents=True, exist_ok=True)
    modelfile = ollama_dir / "Modelfile"
    content = (
        f"FROM {base_model}\n"
        "PARAMETER num_ctx 131072\n"
        "PARAMETER temperature 0.1\n"
        f"SYSTEM \"\"\"\n{system_prompt}\n\"\"\"\n"
    )
    modelfile.write_text(content, encoding="utf-8")
    print(f"[env-wizard] Modelfile written: {modelfile}")
    return modelfile


def _create_ollama_model(model_name: str, modelfile_path: Path) -> None:
    ollama_bin = shutil.which("ollama")
    if not ollama_bin:
        print("[env-wizard] ollama is not available in PATH; skip custom model creation.")
        return
    print(f"[env-wizard] Creating local model profile: {model_name}")
    res = subprocess.run([ollama_bin, "create", model_name, "-f", str(modelfile_path)], check=False)
    if res.returncode == 0:
        print(f"[env-wizard] Ready: ollama run {model_name}")
    else:
        print(f"[env-wizard] Failed to create model '{model_name}'.")
        print(f"[env-wizard] Run manually: ollama create {model_name} -f {modelfile_path}")


def _install_scheduler(repo_root: Path) -> None:
    system = platform.system().lower()
    docsops_root = repo_root / "docsops"
    if not docsops_root.exists():
        docsops_root = repo_root

    if system == "windows":
        script = docsops_root / "ops" / "install_windows_task.ps1"
        if not script.exists():
            print(f"[env-wizard] scheduler installer not found: {script}")
            return
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
        ]
    elif system == "darwin":
        script = docsops_root / "ops" / "install_macos_launchd.sh"
        if not script.exists():
            print(f"[env-wizard] scheduler installer not found: {script}")
            return
        cmd = ["bash", str(script)]
    else:
        script = docsops_root / "ops" / "install_cron_weekly.sh"
        if not script.exists():
            print(f"[env-wizard] scheduler installer not found: {script}")
            return
        cmd = ["bash", str(script)]

    print(f"[env-wizard] installing scheduler using: {script}")
    res = subprocess.run(cmd, cwd=str(repo_root), check=False)
    if res.returncode == 0:
        print("[env-wizard] scheduler installed")
    else:
        print(f"[env-wizard] scheduler install failed (exit {res.returncode})")
        print(f"[env-wizard] run manually: {' '.join(cmd)}")


def _install_playwright_stack(repo_root: Path) -> None:
    py = sys.executable
    print("[env-wizard] checking Playwright Python package...")
    probe = subprocess.run([py, "-c", "import playwright"], check=False)
    if probe.returncode != 0:
        print("[env-wizard] installing playwright package...")
        pip_cmd = [py, "-m", "pip", "install", "playwright"]
        res = subprocess.run(pip_cmd, cwd=str(repo_root), check=False)
        if res.returncode != 0:
            print("[env-wizard] failed to install playwright package.")
            print(f"[env-wizard] run manually: {' '.join(pip_cmd)}")
            return
    print("[env-wizard] installing Chromium browser for Playwright...")
    browser_cmd = [py, "-m", "playwright", "install", "chromium"]
    browser_res = subprocess.run(browser_cmd, cwd=str(repo_root), check=False)
    if browser_res.returncode == 0:
        print("[env-wizard] playwright chromium ready")
    else:
        print("[env-wizard] failed to install playwright chromium")
        print(f"[env-wizard] run manually: {' '.join(browser_cmd)}")


def _bootstrap_screenshot_plan(repo_root: Path, runtime: dict[str, Any]) -> None:
    docs_root = str(runtime.get("docs_root", "docs")) if isinstance(runtime, dict) else "docs"
    docs_site = runtime.get("docs_site", {}) if isinstance(runtime.get("docs_site"), dict) else {}
    base_url = str(docs_site.get("production_url", "")).strip() or "http://localhost:3000"
    cmd = [
        sys.executable,
        str(repo_root / "docsops" / "scripts" / "generate_screenshot_capture_plan.py"),
        "--docs-root",
        docs_root,
        "--output",
        "docs/screenshots.capture.yml",
        "--base-url",
        base_url,
    ]
    if not (repo_root / "docsops" / "scripts" / "generate_screenshot_capture_plan.py").exists():
        cmd = [
            sys.executable,
            str(repo_root / "scripts" / "generate_screenshot_capture_plan.py"),
            "--docs-root",
            docs_root,
            "--output",
            "docs/screenshots.capture.yml",
            "--base-url",
            base_url,
        ]
    res = subprocess.run(cmd, cwd=str(repo_root), check=False)
    if res.returncode == 0:
        print("[env-wizard] screenshots capture plan generated: docs/screenshots.capture.yml")
    else:
        print("[env-wizard] failed to generate screenshots capture plan")
        print(f"[env-wizard] run manually: {' '.join(cmd)}")


def _license_gate_root(repo_root: Path) -> Path:
    """Directory the installed license gate resolves as its REPO_ROOT.

    license_gate.py computes REPO_ROOT as parents[1] of its own file, so all
    binding/integrity artifacts must be written relative to the installed
    gate location, not the client repo root. In a standard client install the
    gate lives at <repo>/docsops/scripts/license_gate.py, so its REPO_ROOT is
    <repo>/docsops and it reads <repo>/docsops/docsops/.repo_binding.json.
    """
    candidates = [
        repo_root / "docsops" / "scripts" / "license_gate.py",
        repo_root / "scripts" / "license_gate.py",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve().parents[1]
    docsops_root = repo_root / "docsops"
    return docsops_root if docsops_root.exists() else repo_root


def _write_repo_binding(repo_root: Path, runtime: dict[str, Any]) -> None:
    gate_root = _license_gate_root(repo_root)
    binding_path = gate_root / "docsops" / ".repo_binding.json"
    binding_path.parent.mkdir(parents=True, exist_ok=True)
    tenant_id = ""
    env_path = repo_root / ENV_FILE
    if env_path.exists():
        raw_env = _read_existing(env_path)
        tenant_id = str(raw_env.get("VERIOPS_TENANT_ID", "")).strip()
    payload = {
        "repo_path_hash": hashlib.sha256(str(gate_root.resolve()).encode("utf-8")).hexdigest(),
        "repo_path_hint": str(gate_root.resolve()),
        "tenant_id": tenant_id,
        "client_id": "",
        "docs_root": str(runtime.get("docs_root", "docs")) if isinstance(runtime, dict) else "docs",
    }
    binding_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    print(f"[env-wizard] repo binding written: {binding_path}")


def _write_integrity_manifest(repo_root: Path) -> None:
    gate_root = _license_gate_root(repo_root)
    out = gate_root / "docsops" / ".integrity_manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    # Paths must be relative to the gate's REPO_ROOT because the gate
    # resolves and re-hashes them from there.
    protected_relpaths = [
        "AGENTS.md",
        "CLAUDE.md",
        "LOCAL_MODEL.md",
        "scripts/license_gate.py",
        "docsops/scripts/license_gate.py",
        "docsops/.repo_binding.json",
    ]
    files: dict[str, str] = {}
    for rel in protected_relpaths:
        path = gate_root / rel
        if not path.exists() or not path.is_file():
            continue
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        files[rel] = h.hexdigest()

    payload = {
        "schema": "integrity-manifest/v1",
        "repo_path_hash": hashlib.sha256(str(gate_root.resolve()).encode("utf-8")).hexdigest(),
        "files": files,
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    print(f"[env-wizard] integrity manifest written: {out}")


def main() -> int:
    args = _parse_args()
    repo_root = Path(".").resolve()
    template_path = repo_root / TEMPLATE_FILE
    env_path = repo_root / ENV_FILE

    # Common bundle layout is <repo>/docsops/.env.docsops.local.template.
    if not template_path.exists():
        nested_template = repo_root / "docsops" / TEMPLATE_FILE
        if nested_template.exists():
            template_path = nested_template

    if not template_path.exists():
        print(f"[env-wizard] template not found: {template_path}")
        return 2

    items = _parse_template(template_path)
    if not items:
        print("[env-wizard] no keys found in template")
        return 0

    print("Client secrets wizard")
    print(f"- Source template: {template_path.name}")
    print(f"- Output file: {env_path.name}")
    runtime = _load_runtime(repo_root)
    algolia_enabled, ask_ai_enabled, ask_ai_provider = _runtime_integrations(runtime)

    values = _read_existing(env_path)
    if args.auto:
        print("- Auto mode: using existing/template/default values.\n")
        for key, _hint in items:
            if not _is_key_relevant(key, algolia_enabled, ask_ai_enabled, ask_ai_provider):
                continue
            values.setdefault(key, "")
    else:
        print("- Press Enter to keep current/default value.\n")
        for key, hint in items:
            if not _is_key_relevant(key, algolia_enabled, ask_ai_enabled, ask_ai_provider):
                continue
            current = values.get(key, "")
            suffix = f" [{current}]" if current else ""
            prompt = f"{key} ({hint}){suffix}: "
            entered = input(prompt).strip()
            if entered:
                values[key] = entered
            elif key not in values:
                values[key] = ""

    _ensure_ip_protection_defaults(values)
    _write_env(env_path, values)
    print(f"\n[env-wizard] wrote {env_path}")
    _write_repo_binding(repo_root, runtime)
    _write_integrity_manifest(repo_root)
    llm_control = runtime.get("llm_control", {}) if isinstance(runtime.get("llm_control"), dict) else {}
    llm_mode = str(llm_control.get("llm_mode", "local_default")).strip().lower()
    model = str(llm_control.get("local_model", "veridoc-writer")).strip() or "veridoc-writer"
    base_model = str(llm_control.get("local_base_model", "qwen3:30b")).strip() or "qwen3:30b"
    auto_install = bool(llm_control.get("auto_install_local_model_on_setup", True))
    quality_note = str(
        llm_control.get(
            "quality_delta_note",
            "Fully local mode may reduce output quality by ~10-15% on hardest synthesis tasks.",
        )
    ).strip()
    if llm_mode == "local_default" and not args.auto:
        print(f"[env-wizard] LLM mode: fully local by default. {quality_note}")
        if auto_install and _prompt_yes_no(f"Install Ollama + pull base model '{base_model}' now?", default_yes=True):
            _install_ollama_and_model(base_model)
            modelfile_path = _create_veridoc_modelfile(repo_root, base_model=base_model, model_name=model)
            if _prompt_yes_no(f"Create local model profile '{model}' now?", default_yes=True):
                _create_ollama_model(model, modelfile_path)

    install_ci = args.install_ci or (not args.auto and _prompt_yes_no("Install docs CI workflow files now (PR/push lint)?", default_yes=True))
    if install_ci:
        ci_paths = install_docs_ci_files(repo_root, runtime, install_jenkins=True)
        for ci_path in ci_paths:
            print(f"[env-wizard] docs CI installed: {ci_path}")

    install_scheduler = (not args.skip_scheduler) and (args.auto or _prompt_yes_no("Install weekly scheduler now (auto-detect OS)?", default_yes=True))
    if install_scheduler:
        _install_scheduler(repo_root)

    if not args.skip_screenshot_setup:
        _bootstrap_screenshot_plan(repo_root, runtime)
        install_playwright = bool(args.install_playwright)
        if not install_playwright and not args.auto:
            install_playwright = _prompt_yes_no("Install Playwright + Chromium for automatic screenshots now?", default_yes=True)
        if install_playwright:
            _install_playwright_stack(repo_root)

    print("[env-wizard] next: run docsops/ops/run_weekly_docsops.sh (or .ps1)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

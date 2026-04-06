#!/usr/bin/env python3
"""Interactive client-side wizard to create .env.docsops.local from template.

Run from client repository root after unpacking docsops bundle:
    python3 docsops/scripts/setup_client_env_wizard.py
"""

from __future__ import annotations

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

SCRIPT_PATH = Path(__file__).resolve()
DOCSOPS_ROOT = SCRIPT_PATH.parents[1]
if str(DOCSOPS_ROOT) not in sys.path:
    sys.path.insert(0, str(DOCSOPS_ROOT))

from scripts.docs_ci_bootstrap import install_docs_ci_files


ENV_FILE = ".env.docsops.local"
TEMPLATE_FILE = ".env.docsops.local.template"

DEFAULT_ENV_VALUES: dict[str, str] = {
    "VERIOPS_UPDATE_SERVER": "https://updates.veriops.dev",
    "VERIOPS_PHONE_HOME_URL": "https://api.veri-doc.app",
    "VERIOPS_REVOCATION_CHECK_ENABLED": "false",
    "VERIOPS_REVOCATION_URL": "https://api.veri-doc.app/billing/license/revocation-check",
    "VERIOPS_PACK_REGISTRY_URL": "https://api.veri-doc.app/ops/pack-registry/fetch",
}


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


def _load_runtime(repo_root: Path) -> dict[str, Any]:
    if yaml is None:
        return {}
    candidates = [
        repo_root / "docsops" / "config" / "client_runtime.yml",
        repo_root / "config" / "client_runtime.yml",
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                raw = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
            except (AttributeError, TypeError, ValueError, OSError):
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


def main() -> int:
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
    print("- Press Enter to keep current/default value.\n")

    values = _read_existing(env_path)
    for key, hint in items:
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
    runtime = _load_runtime(repo_root)
    llm_control = runtime.get("llm_control", {}) if isinstance(runtime.get("llm_control"), dict) else {}
    llm_mode = str(llm_control.get("llm_mode", "external_preferred")).strip().lower()
    strict_local = bool(llm_control.get("strict_local_first", llm_mode == "local_default"))
    model = str(llm_control.get("local_model", "veridoc-writer")).strip() or "veridoc-writer"
    base_model = str(llm_control.get("local_base_model", "qwen3:30b")).strip() or "qwen3:30b"
    auto_install = bool(llm_control.get("auto_install_local_model_on_setup", True))
    quality_note = str(
        llm_control.get(
            "quality_delta_note",
            "Fully local mode may reduce output quality by ~10-15% on hardest synthesis tasks.",
        )
    ).strip()
    if strict_local or llm_mode == "local_default":
        print(f"[env-wizard] LLM mode: fully local by default. {quality_note}")
        if auto_install and _prompt_yes_no(f"Install Ollama + pull base model '{base_model}' now?", default_yes=True):
            _install_ollama_and_model(base_model)
            modelfile_path = _create_veridoc_modelfile(repo_root, base_model=base_model, model_name=model)
            if _prompt_yes_no(f"Create local model profile '{model}' now?", default_yes=True):
                _create_ollama_model(model, modelfile_path)
    else:
        print(
            "[env-wizard] LLM mode: cloud/hybrid (external providers allowed). "
            "Use strict local-first profile for regulated environments."
        )

    if _prompt_yes_no("Install docs CI workflow files now (PR/push lint)?", default_yes=True):
        ci_paths = install_docs_ci_files(repo_root, runtime, install_jenkins=True)
        for ci_path in ci_paths:
            print(f"[env-wizard] docs CI installed: {ci_path}")

    print("[env-wizard] next: run docsops/ops/run_weekly_docsops.sh (or .ps1)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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

AUTO_ACCEPT_KEYS: set[str] = {
    "VERIOPS_UPDATE_SERVER",
    "VERIOPS_PHONE_HOME_URL",
    "VERIOPS_PHONE_HOME_ENABLED",
    "VERIOPS_UPDATE_CHECK_ENABLED",
    "VERIOPS_REVOCATION_CHECK_ENABLED",
    "VERIOPS_REVOCATION_URL",
    "VERIOPS_PACK_REGISTRY_URL",
    "VERIOPS_LICENSE_PLAN",
}

AUTO_ACCEPT_IF_PRESENT_KEYS: set[str] = {
    "VERIOPS_TENANT_ID",
    "VERIOPS_COMPANY_DOMAIN",
}

FIELD_GUIDANCE: dict[str, str] = {
    "ALGOLIA_APP_ID": "Take from your Algolia dashboard (Settings/API). Use your own account.",
    "ALGOLIA_API_KEY": "Use your Algolia Admin API key for write/indexing operations (not search-only). Never use a shared operator key.",
    "ALGOLIA_INDEX_NAME": "You can invent it. Best practice: veriops_<client_slug>_docs (for example veriops_acme_docs).",
    "OPENAI_API_KEY": "Use your OpenAI key. Do not reuse a shared operator key.",
    "ANTHROPIC_API_KEY": "Use your Anthropic key.",
    "AZURE_OPENAI_API_KEY": "Use your Azure OpenAI key.",
    "AZURE_OPENAI_ENDPOINT": "Use your Azure OpenAI endpoint URL from Azure portal.",
    "POSTMAN_API_KEY": "Use your Postman API key.",
    "POSTMAN_WORKSPACE_ID": "Take from your Postman workspace settings.",
    "POSTMAN_COLLECTION_UID": "Optional. Leave empty to auto-import from generated contract.",
    "POSTMAN_MOCK_SERVER_ID": "Optional. Leave empty to auto-create.",
    "VERIOPS_TENANT_ID": "Set to your tenant/org slug. Must match license JWT binding if set.",
    "VERIOPS_COMPANY_DOMAIN": "Your primary domain (for binding check). Optional but recommended.",
    "VERIOPS_LICENSE_PLAN": "Dev/test only. Keep empty in production; production uses docsops/license.jwt.",
    "VERIOPS_LICENSE_KEY": "Operator-only in most deliveries. Keep empty unless your operator asks for it.",
    "VERIOPS_UPDATE_SERVER": "Usually keep generated default value.",
    "VERIOPS_PHONE_HOME_URL": "Usually keep generated default value.",
    "VERIOPS_PHONE_HOME_ENABLED": "Usually keep generated default value.",
    "VERIOPS_UPDATE_CHECK_ENABLED": "Usually keep generated default value.",
    "VERIOPS_REVOCATION_CHECK_ENABLED": "Usually false unless operator mandates online revocation checks.",
    "VERIOPS_REVOCATION_URL": "Usually keep generated default value.",
    "VERIOPS_PACK_REGISTRY_URL": "Usually keep generated default value.",
    "TESTRAIL_UPLOAD_ENABLED": "Set true only if you want upload to TestRail.",
    "ZEPHYR_UPLOAD_ENABLED": "Set true only if you want upload to Zephyr Scale.",
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


def _guidance_for_key(key: str) -> str:
    direct = FIELD_GUIDANCE.get(key)
    if direct:
        return direct
    if key.endswith("_API_KEY"):
        return "Take from your provider dashboard. Use your own key."
    if key.endswith("_APP_ID"):
        return "Take from your provider dashboard."
    if key.endswith("_INDEX_NAME"):
        return "You can invent it. Best practice: <product>_<client_slug>_<purpose>."
    if key.endswith("_BASE_URL") or key.endswith("_URL") or key.endswith("_ENDPOINT"):
        return "Use your service URL (or the one provided by your operator)."
    if key.endswith("_ENABLED"):
        return "Boolean flag. Use true/false."
    return ""


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


def _git_toplevel(start_dir: Path) -> Path | None:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=str(start_dir),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    out = completed.stdout.strip()
    if not out:
        return None
    return Path(out).resolve()


def _resolve_docsops_runtime(git_root: Path, current_dir: Path) -> tuple[str, str] | None:
    candidates = [
        ("docsops", "docsops/config/client_runtime.yml", git_root / "docsops" / "scripts" / "run_docs_ci_checks.py"),
        (".", "config/client_runtime.yml", git_root / "scripts" / "run_docs_ci_checks.py"),
        ("docsops", "docsops/config/client_runtime.yml", current_dir / "docsops" / "scripts" / "run_docs_ci_checks.py"),
        (".", "config/client_runtime.yml", current_dir / "scripts" / "run_docs_ci_checks.py"),
    ]
    for docsops_prefix, runtime_cfg, check_script in candidates:
        if check_script.exists():
            return docsops_prefix, runtime_cfg
    return None


def install_local_precommit_hooks(repo_root: Path) -> tuple[bool, list[Path], str]:
    """Install repository-local pre-commit hooks for docsops checks.

    Creates both:
    - `.husky/pre-commit` (so review branch flow can run `sh .husky/pre-commit`)
    - `.git/hooks/pre-commit` (so local `git commit` is actually gated)
    """
    git_root = _git_toplevel(repo_root)
    if git_root is None:
        return False, [], "Not inside a git repository."

    resolved = _resolve_docsops_runtime(git_root, repo_root)
    if resolved is None:
        return (
            False,
            [],
            "Cannot locate docsops/scripts/run_docs_ci_checks.py. "
            "Ensure bundle is unpacked as <repo>/docsops.",
        )
    docsops_prefix, runtime_cfg_rel = resolved

    if docsops_prefix == ".":
        check_cmd = f'python3 scripts/run_docs_ci_checks.py --runtime-config "{runtime_cfg_rel}"'
    else:
        check_cmd = f'python3 {docsops_prefix}/scripts/run_docs_ci_checks.py --runtime-config "{runtime_cfg_rel}"'

    husky_dir = git_root / ".husky"
    husky_internal = husky_dir / "_"
    husky_dir.mkdir(parents=True, exist_ok=True)
    husky_internal.mkdir(parents=True, exist_ok=True)

    husky_helper = husky_internal / "husky.sh"
    if not husky_helper.exists():
        husky_helper.write_text("#!/usr/bin/env sh\nset -e\n", encoding="utf-8")

    husky_hook = husky_dir / "pre-commit"
    husky_hook.write_text(
        "#!/usr/bin/env sh\n"
        "set -e\n"
        f"{check_cmd}\n",
        encoding="utf-8",
    )

    git_hook = git_root / ".git" / "hooks" / "pre-commit"
    git_hook.parent.mkdir(parents=True, exist_ok=True)
    git_hook.write_text(
        "#!/usr/bin/env sh\n"
        "set -e\n"
        "if [ -f ./.husky/pre-commit ]; then\n"
        "  exec sh ./.husky/pre-commit\n"
        "fi\n"
        f"{check_cmd}\n",
        encoding="utf-8",
    )

    for path in (husky_helper, husky_hook, git_hook):
        try:
            path.chmod(0o755)
        except OSError as exc:
            print(f"[env-wizard] warning: cannot set executable bit on {path}: {exc}")

    installed = [husky_hook, git_hook]
    return True, installed, ""


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
    print("- You only need to enter values for external services you enable (Algolia/LLM/Postman/etc).")
    print("- Internal VeriOps server endpoints are auto-kept unless your operator tells you to change them.")
    print("- Press Enter to keep current/default value.\n")

    values = _read_existing(env_path)
    prompted_count = 0
    for key, hint in items:
        if key in AUTO_ACCEPT_KEYS:
            if key not in values:
                values[key] = ""
            continue
        if key in AUTO_ACCEPT_IF_PRESENT_KEYS and str(values.get(key, "")).strip():
            continue
        # Shared fallback keys are optional by design for centrally managed entitlement.
        # Keep them empty by default and do not prompt during standard client setup.
        if key.startswith("DOCSOPS_SHARED_") and not values.get(key, "").strip():
            values[key] = ""
            continue
        current = values.get(key, "")
        suffix = f" [{current}]" if current else ""
        guidance = _guidance_for_key(key)
        composed_hint = hint.strip()
        if guidance:
            composed_hint = f"{composed_hint} | {guidance}" if composed_hint else guidance
        prompt = f"{key} ({composed_hint}){suffix}: "
        entered = input(prompt).strip()
        prompted_count += 1
        if entered:
            values[key] = entered
        elif key not in values:
            values[key] = ""

    _ensure_ip_protection_defaults(values)
    _write_env(env_path, values)
    print(f"\n[env-wizard] wrote {env_path}")
    print(f"[env-wizard] prompted fields: {prompted_count}")
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

    if _prompt_yes_no("Install local git pre-commit hooks now (required for local commit gate)?", default_yes=True):
        ok, installed_paths, error = install_local_precommit_hooks(repo_root)
        if not ok:
            print(f"[env-wizard] hook install failed: {error}")
            return 3
        for hook_path in installed_paths:
            print(f"[env-wizard] hook installed: {hook_path}")

    system = platform.system().lower()
    if system == "windows":
        print("[env-wizard] next (PowerShell): .\\docsops\\ops\\run_weekly_docsops.ps1")
        print("[env-wizard] next (Git Bash): bash docsops/ops/run_weekly_docsops.sh")
    else:
        print("[env-wizard] next: bash docsops/ops/run_weekly_docsops.sh")
        print("[env-wizard] next (if using pwsh): ./docsops/ops/run_weekly_docsops.ps1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

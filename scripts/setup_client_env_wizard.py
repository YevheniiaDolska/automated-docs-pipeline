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
import time
import urllib.error
import urllib.request
import json
import os
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

SETUP_PREFLIGHT_REPORT = Path("reports/setup_prerequisites_report.json")

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


def _resolve_runtime_path(repo_root: Path) -> Path | None:
    candidates = [
        repo_root / "docsops" / "config" / "client_runtime.yml",
        repo_root / "config" / "client_runtime.yml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _write_runtime(path: Path, runtime: dict[str, Any]) -> bool:
    if yaml is None:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(runtime, sort_keys=False), encoding="utf-8")
    return True


def _is_tool_available(binary: str) -> bool:
    return bool(shutil.which(binary))


def _detect_setup_prereqs(runtime: dict[str, Any], env_values: dict[str, str]) -> dict[str, Any]:
    integrations = runtime.get("integrations", {}) if isinstance(runtime.get("integrations"), dict) else {}
    ask_ai = integrations.get("ask_ai", {}) if isinstance(integrations.get("ask_ai"), dict) else {}
    algolia = integrations.get("algolia", {}) if isinstance(integrations.get("algolia"), dict) else {}
    api_first = runtime.get("api_first", {}) if isinstance(runtime.get("api_first"), dict) else {}
    llm_control = runtime.get("llm_control", {}) if isinstance(runtime.get("llm_control"), dict) else {}
    security = runtime.get("security", {}) if isinstance(runtime.get("security"), dict) else {}
    operation_mode = str(security.get("operation_mode", "")).strip().lower()
    llm_mode = str(llm_control.get("llm_mode", "external_preferred")).strip().lower()
    strict_local = bool(llm_control.get("strict_local_first", llm_mode == "local_default"))

    required_client_inputs: list[dict[str, str]] = []
    if bool(ask_ai.get("enabled", False)):
        provider = str(ask_ai.get("provider", "openai")).strip().lower()
        if provider == "openai":
            required_client_inputs.append({"key": "OPENAI_API_KEY", "purpose": "Ask AI provider credentials"})
        elif provider == "anthropic":
            required_client_inputs.append({"key": "ANTHROPIC_API_KEY", "purpose": "Ask AI provider credentials"})
        elif provider == "azure-openai":
            required_client_inputs.extend(
                [
                    {"key": "AZURE_OPENAI_API_KEY", "purpose": "Ask AI provider credentials"},
                    {"key": "AZURE_OPENAI_ENDPOINT", "purpose": "Ask AI provider endpoint"},
                ]
            )
        else:
            required_client_inputs.extend(
                [
                    {"key": "ASK_AI_API_KEY", "purpose": "Custom Ask AI provider credentials"},
                    {"key": "ASK_AI_BASE_URL", "purpose": "Custom Ask AI provider URL"},
                ]
            )
    if bool(algolia.get("enabled", False)):
        required_client_inputs.extend(
            [
                {"key": str(algolia.get("app_id_env", "ALGOLIA_APP_ID")), "purpose": "Algolia app id"},
                {"key": str(algolia.get("api_key_env", "ALGOLIA_API_KEY")), "purpose": "Algolia admin key"},
                {"key": str(algolia.get("index_name_env", "ALGOLIA_INDEX_NAME")), "purpose": "Algolia index name"},
            ]
        )

    sandbox_backend = str(api_first.get("sandbox_backend", "docker")).strip().lower()
    docker_required = bool(api_first.get("enabled", False)) and sandbox_backend == "docker"
    external_mock = api_first.get("external_mock", {}) if isinstance(api_first.get("external_mock"), dict) else {}
    if sandbox_backend == "external" and bool(external_mock.get("enabled", False)):
        postman_cfg = external_mock.get("postman", {}) if isinstance(external_mock.get("postman"), dict) else {}
        required_client_inputs.extend(
            [
                {"key": str(postman_cfg.get("api_key_env", "POSTMAN_API_KEY")), "purpose": "External mock provider API key"},
                {"key": str(postman_cfg.get("workspace_id_env", "POSTMAN_WORKSPACE_ID")), "purpose": "External mock provider workspace id"},
            ]
        )

    missing_inputs = [entry["key"] for entry in required_client_inputs if not str(env_values.get(entry["key"], "")).strip()]
    available_tools = {
        "docker": _is_tool_available("docker"),
        "node": _is_tool_available("node"),
        "npm": _is_tool_available("npm"),
        "python3": _is_tool_available("python3"),
        "ollama": _discover_ollama_bin(Path.cwd()) is not None,
    }
    blocking_reasons: list[str] = []
    warnings: list[str] = []
    if docker_required and not available_tools["docker"]:
        blocking_reasons.append("docker_runtime_missing")
    if missing_inputs:
        warnings.append("missing_optional_or_external_credentials")

    strict_local_alternatives = {
        "docker_missing": "Use api_first.sandbox_backend=prism for local contract sandbox without Docker.",
        "external_provider_keys_missing": "In strict-local mode keep Ask AI/Algolia/external mock disabled or run with local Ollama only.",
        "llm_audit_or_translate_without_cloud_keys": "Run local generation path and skip cloud-translation/audit steps until keys are provided.",
    }
    return {
        "profile": "strict-local" if (strict_local or operation_mode == "strict-local") else (operation_mode or "hybrid/cloud"),
        "operation_mode": operation_mode or "unspecified",
        "required_client_inputs": required_client_inputs,
        "operator_managed": [
            {"artifact": "docsops/license.jwt", "purpose": "Signed license entitlement"},
            {"artifact": "capability pack (optional per plan)", "purpose": "Premium feature runtime pack"},
            {"artifact": "policy defaults", "purpose": "Security/egress baseline"},
        ],
        "missing_inputs": missing_inputs,
        "available_tools": available_tools,
        "blocking_reasons": blocking_reasons,
        "warnings": warnings,
        "api_first": {
            "enabled": bool(api_first.get("enabled", False)),
            "sandbox_backend": sandbox_backend,
            "docker_required": docker_required,
        },
        "strict_local_alternatives": strict_local_alternatives,
    }


def _apply_local_fallbacks(runtime: dict[str, Any], prereqs: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    updates: list[str] = []
    api_first = runtime.get("api_first", {}) if isinstance(runtime.get("api_first"), dict) else {}
    runtime["api_first"] = api_first
    backend = str(api_first.get("sandbox_backend", "docker")).strip().lower()
    docker_ok = bool(prereqs.get("available_tools", {}).get("docker", False))
    security = runtime.get("security", {}) if isinstance(runtime.get("security"), dict) else {}
    llm_control = runtime.get("llm_control", {}) if isinstance(runtime.get("llm_control"), dict) else {}
    llm_mode = str(llm_control.get("llm_mode", "external_preferred")).strip().lower()
    strict_local = bool(llm_control.get("strict_local_first", llm_mode == "local_default"))
    operation_mode = str(security.get("operation_mode", "")).strip().lower()
    if backend == "docker" and not docker_ok and (strict_local or operation_mode in {"strict-local", "hybrid"}):
        api_first["sandbox_backend"] = "prism"
        updates.append("api_first.sandbox_backend: docker -> prism (docker not available)")

    if operation_mode == "strict-local":
        external_mock = api_first.get("external_mock", {})
        if isinstance(external_mock, dict) and bool(external_mock.get("enabled", False)):
            external_mock["enabled"] = False
            updates.append("api_first.external_mock.enabled: true -> false (strict-local)")
    return runtime, updates


def _prompt_yes_no(prompt: str, default_yes: bool = True) -> bool:
    suffix = "[Y/n]" if default_yes else "[y/N]"
    raw = input(f"{prompt} {suffix}: ").strip().lower()
    if not raw:
        return default_yes
    return raw in {"y", "yes"}


def _detect_linux_asset_name() -> str:
    arch = platform.machine().lower()
    if arch in {"x86_64", "amd64"}:
        return "ollama-linux-amd64.tar.zst"
    if arch in {"aarch64", "arm64"}:
        return "ollama-linux-arm64.tar.zst"
    raise RuntimeError(f"Unsupported Linux architecture for Ollama auto-install: {arch}")


def _discover_ollama_bins(repo_root: Path) -> list[str]:
    candidates = [
        shutil.which("ollama"),
        "/usr/local/bin/ollama",
        "/opt/homebrew/bin/ollama",
        str(repo_root / "docsops" / "tools" / "ollama" / "bin" / "ollama"),
        str(repo_root / "tools" / "ollama" / "bin" / "ollama"),
    ]
    found: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate:
            continue
        resolved = str(Path(candidate).expanduser().resolve())
        if resolved in seen:
            continue
        path = Path(resolved)
        if path.exists() and os.access(path, os.X_OK):
            seen.add(resolved)
            found.append(resolved)
    return found


def _discover_ollama_bin(repo_root: Path) -> str | None:
    bins = _discover_ollama_bins(repo_root)
    return bins[0] if bins else None


def _find_reachable_ollama_bin(repo_root: Path) -> str | None:
    for candidate in _discover_ollama_bins(repo_root):
        probe = subprocess.run([candidate, "list"], check=False, capture_output=True, text=True)
        if int(getattr(probe, "returncode", 1) or 1) == 0:
            return candidate
    return None


def _latest_linux_asset_url() -> str:
    api_url = "https://api.github.com/repos/ollama/ollama/releases/latest"
    req = urllib.request.Request(
        api_url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "docsops-setup-wizard"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # nosec B310
        payload = json.loads(resp.read().decode("utf-8"))
    assets = payload.get("assets", [])
    if not isinstance(assets, list):
        raise RuntimeError("Unexpected Ollama release payload format.")
    wanted = _detect_linux_asset_name()
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        if str(asset.get("name", "")).strip() == wanted:
            url = str(asset.get("browser_download_url", "")).strip()
            if url:
                return url
    raise RuntimeError(f"Ollama release asset not found: {wanted}")


def _shared_ollama_cache_root() -> Path:
    configured = os.environ.get("VERIDOC_OLLAMA_CACHE_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return Path.home() / ".cache" / "veridoc" / "ollama"


def _copy_cached_ollama_binary(install_root: Path, cache_root: Path) -> str | None:
    cached_bin = cache_root / "bin" / "ollama"
    if not cached_bin.exists():
        return None
    target_bin = install_root / "bin" / "ollama"
    target_bin.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(cached_bin, target_bin)
    target_bin.chmod(0o755)
    return str(target_bin)


def _install_ollama_local_linux(repo_root: Path) -> str | None:
    install_root = repo_root / "docsops" / "tools" / "ollama"
    install_root.mkdir(parents=True, exist_ok=True)
    candidate = install_root / "bin" / "ollama"
    cache_root = _shared_ollama_cache_root()
    cache_root.mkdir(parents=True, exist_ok=True)
    asset_name = _detect_linux_asset_name()
    archive = cache_root / asset_name
    try:
        url = _latest_linux_asset_url()
    except (RuntimeError, ValueError, TypeError, OSError, urllib.error.URLError) as exc:
        print(f"[env-wizard] Failed to resolve latest Ollama Linux asset: {exc}")
        return None

    if candidate.exists():
        candidate.chmod(0o755)
        os.environ["PATH"] = f"{candidate.parent}:{os.environ.get('PATH', '')}"
        return str(candidate)

    cached_bin = _copy_cached_ollama_binary(install_root, cache_root)
    if cached_bin:
        print(f"[env-wizard] Reused cached local Ollama binary: {cached_bin}")
        os.environ["PATH"] = f"{Path(cached_bin).parent}:{os.environ.get('PATH', '')}"
        return cached_bin

    download_ok = False
    last_error = ""
    if archive.exists() and archive.stat().st_size > 0:
        download_ok = True
    for attempt in range(1, 4):
        if download_ok:
            break
        download = subprocess.run(
            [
                "curl",
                "-fL",
                "--retry",
                "5",
                "--retry-all-errors",
                "--continue-at",
                "-",
                url,
                "-o",
                str(archive),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if int(getattr(download, "returncode", 1) or 1) == 0:
            download_ok = True
            break
        last_error = (getattr(download, "stderr", "") or getattr(download, "stdout", "") or "").strip()
        print(f"[env-wizard] Local Ollama download attempt {attempt}/3 failed.")
        time.sleep(2)
    if not download_ok:
        if archive.exists():
            try:
                # If a large archive is already present, attempt extraction anyway.
                # Some resume flows can return non-zero despite having a usable file.
                size_mb = archive.stat().st_size / (1024 * 1024)
                if size_mb >= 1024:
                    print(
                        "[env-wizard] Local Ollama download reported failure, "
                        f"but archive is present ({size_mb:.0f} MB). Trying extraction..."
                    )
                    download_ok = True
            except OSError as exc:
                print(f"[env-wizard] Could not inspect cached archive size: {exc}")
        if not download_ok:
            print(f"[env-wizard] Local Ollama download failed: {last_error[:240]}")
            return None

    extract = subprocess.run(
        ["tar", "--zstd", "-xf", str(archive), "-C", str(cache_root)],
        check=False,
        capture_output=True,
        text=True,
    )
    if int(getattr(extract, "returncode", 1) or 1) != 0:
        err = (getattr(extract, "stderr", "") or getattr(extract, "stdout", "") or "").strip()
        # Fallback for environments without system zstd binary.
        if "cannot exec" in err.lower() and "zstd" in err.lower():
            print("[env-wizard] System zstd not found. Trying Python zstandard fallback...")
            py_runner = sys.executable
            py_extract_script = (
                "import pathlib, sys, tarfile\n"
                "import zstandard as zstd\n"
                "archive = pathlib.Path(sys.argv[1])\n"
                "dest = pathlib.Path(sys.argv[2])\n"
                "dest.mkdir(parents=True, exist_ok=True)\n"
                "with archive.open('rb') as fh:\n"
                "    dctx = zstd.ZstdDecompressor()\n"
                "    with dctx.stream_reader(fh) as reader:\n"
                "        with tarfile.open(fileobj=reader, mode='r|') as tf:\n"
                "            tf.extractall(path=dest)\n"
            )

            py_extract = subprocess.run(
                [py_runner, "-c", py_extract_script, str(archive), str(cache_root)],
                check=False,
                capture_output=True,
                text=True,
            )
            if int(getattr(py_extract, "returncode", 1) or 1) != 0:
                install_cmds = [
                    [sys.executable, "-m", "pip", "install", "--user", "zstandard"],
                    [sys.executable, "-m", "pip", "install", "--break-system-packages", "zstandard"],
                ]
                last_install_error = ""
                for install_cmd in install_cmds:
                    pip_install = subprocess.run(
                        install_cmd,
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    if int(getattr(pip_install, "returncode", 1) or 1) == 0:
                        py_extract = subprocess.run(
                            [py_runner, "-c", py_extract_script, str(archive), str(cache_root)],
                            check=False,
                            capture_output=True,
                            text=True,
                        )
                        if int(getattr(py_extract, "returncode", 1) or 1) == 0:
                            break
                    last_install_error = (
                        getattr(pip_install, "stderr", "") or getattr(pip_install, "stdout", "") or ""
                    ).strip()

                if int(getattr(py_extract, "returncode", 1) or 1) != 0:
                    # Last fallback: local venv with isolated dependency install.
                    venv_dir = cache_root / ".pydeps"
                    mkvenv = subprocess.run(
                        [sys.executable, "-m", "venv", str(venv_dir)],
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    if int(getattr(mkvenv, "returncode", 1) or 1) == 0:
                        venv_py = venv_dir / "bin" / "python"
                        venv_install = subprocess.run(
                            [str(venv_py), "-m", "pip", "install", "zstandard"],
                            check=False,
                            capture_output=True,
                            text=True,
                        )
                        if int(getattr(venv_install, "returncode", 1) or 1) == 0:
                            py_extract = subprocess.run(
                                [str(venv_py), "-c", py_extract_script, str(archive), str(cache_root)],
                                check=False,
                                capture_output=True,
                                text=True,
                            )
                        else:
                            last_install_error = (
                                getattr(venv_install, "stderr", "") or getattr(venv_install, "stdout", "") or ""
                            ).strip()
                    else:
                        last_install_error = (
                            getattr(mkvenv, "stderr", "") or getattr(mkvenv, "stdout", "") or ""
                        ).strip()

                if int(getattr(py_extract, "returncode", 1) or 1) != 0:
                    py_err = (getattr(py_extract, "stderr", "") or getattr(py_extract, "stdout", "") or "").strip()
                    if last_install_error and not py_err:
                        py_err = last_install_error
                    if (cache_root / "bin" / "ollama").exists():
                        print(
                            "[env-wizard] Python extraction fallback failed, "
                            "but ollama binary is present. Continuing with existing binary."
                        )
                    else:
                        print(f"[env-wizard] Python extraction fallback failed: {py_err[:240]}")
                        return None
        else:
            if (cache_root / "bin" / "ollama").exists():
                print(
                    "[env-wizard] Local Ollama extraction reported failure, "
                    "but binary exists. Continuing with existing binary."
                )
            else:
                print(f"[env-wizard] Local Ollama extraction failed: {err[:240]}")
                return None

    copied = _copy_cached_ollama_binary(install_root, cache_root)
    if copied:
        os.environ["PATH"] = f"{Path(copied).parent}:{os.environ.get('PATH', '')}"
        print(f"[env-wizard] Ollama installed locally: {copied}")
        return copied
    print("[env-wizard] Local Ollama install completed but binary not found in expected path.")
    return None


def _ensure_ollama_daemon(ollama_bin: str) -> bool:
    probe = subprocess.run([ollama_bin, "list"], check=False, capture_output=True, text=True)
    if probe.returncode == 0:
        return True
    subprocess.Popen(  # noqa: S603
        [ollama_bin, "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    for _ in range(15):
        time.sleep(1)
        retry = subprocess.run([ollama_bin, "list"], check=False, capture_output=True, text=True)
        if retry.returncode == 0:
            return True
    return False


def _ollama_model_present(ollama_bin: str, model: str) -> bool:
    listed = subprocess.run([ollama_bin, "list"], check=False, capture_output=True, text=True)
    if listed.returncode != 0:
        return False
    target = model.strip().lower()
    stdout = str(getattr(listed, "stdout", "") or "")
    for raw in stdout.splitlines():
        line = raw.strip()
        if not line or line.lower().startswith("name"):
            continue
        first_col = line.split()[0].strip().lower()
        if first_col == target:
            return True
    return False


def _ollama_pull_in_progress(model: str) -> bool:
    if platform.system().lower() == "windows":
        return False
    probe = subprocess.run(
        ["ps", "-ef"],
        check=False,
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        return False
    needle = f"ollama pull {model}".strip().lower()
    stdout = str(getattr(probe, "stdout", "") or "")
    for raw in stdout.splitlines():
        line = raw.strip().lower()
        if needle in line and "setup_client_env_wizard.py" not in line:
            return True
    return False


def _wait_for_ollama_model(ollama_bin: str, model: str, timeout_seconds: int = 4 * 60 * 60) -> bool:
    start = time.time()
    while int(time.time() - start) < timeout_seconds:
        if _ollama_model_present(ollama_bin, model):
            return True
        time.sleep(20)
    return False


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


def _install_ollama_and_model(model: str, repo_root: Path | None = None) -> bool:
    if repo_root is None:
        repo_root = Path.cwd()
    # Prefer any already running/reachable local Ollama runtime first.
    ollama_bin = _find_reachable_ollama_bin(repo_root)
    if ollama_bin is None:
        installed_bins = _discover_ollama_bins(repo_root)
        # Ollama binary exists but daemon is not reachable yet.
        # Reuse existing binary and start daemon instead of reinstalling.
        if installed_bins:
            ollama_bin = installed_bins[0]

    if ollama_bin is None:
        system = platform.system().lower()
        print("[env-wizard] Ollama is not installed. Attempting auto-install...")
        if system == "linux":
            can_sudo_noninteractive = False
            if shutil.which("sudo"):
                probe = subprocess.run(["sudo", "-n", "true"], check=False, capture_output=True, text=True)
                can_sudo_noninteractive = int(getattr(probe, "returncode", 1) or 1) == 0
            if can_sudo_noninteractive:
                cmd = "curl -fsSL https://ollama.com/install.sh | sh"
                res = subprocess.run(["bash", "-lc", cmd], check=False)
            else:
                print("[env-wizard] Skipping global Ollama install (sudo password prompt not allowed in auto flow).")
                class _NoSudoRes:
                    returncode = 1
                res = _NoSudoRes()
            if res.returncode != 0:
                print("[env-wizard] Global Ollama install failed on Linux. Trying local install in docsops/tools/ollama...")
                ollama_bin = _install_ollama_local_linux(repo_root)
                if not ollama_bin:
                    print("[env-wizard] Install manually, then run: ollama pull {}".format(model))
                    return False
        elif system == "darwin":
            if shutil.which("brew"):
                res = subprocess.run(["brew", "install", "ollama"], check=False)
                if res.returncode != 0:
                    print("[env-wizard] brew install ollama failed.")
                    print("[env-wizard] Install Ollama manually and run: ollama pull {}".format(model))
                    return False
            else:
                print("[env-wizard] Homebrew not found. Install Ollama manually, then run: ollama pull {}".format(model))
                return False
        elif system == "windows":
            if shutil.which("winget"):
                res = subprocess.run(["winget", "install", "-e", "--id", "Ollama.Ollama"], check=False)
                if res.returncode != 0:
                    print("[env-wizard] winget install Ollama failed.")
                    print("[env-wizard] Install Ollama manually and run: ollama pull {}".format(model))
                    return False
            else:
                print("[env-wizard] winget not found. Install Ollama manually and run: ollama pull {}".format(model))
                return False
        else:
            print("[env-wizard] Unsupported OS for auto-install. Install Ollama manually and run: ollama pull {}".format(model))
            return False
        ollama_bin = _discover_ollama_bin(repo_root)
        if ollama_bin is None:
            print("[env-wizard] Ollama still not found in PATH after install.")
            return False

    if not _ensure_ollama_daemon(ollama_bin):
        print("[env-wizard] Ollama daemon is not reachable. Start it manually and rerun setup.")
        return False

    if _ollama_model_present(ollama_bin, model):
        print(f"[env-wizard] Local model already present: {model}")
        return True
    if _ollama_pull_in_progress(model):
        print(f"[env-wizard] Detected active pull for '{model}'. Waiting for completion...")
        if _wait_for_ollama_model(ollama_bin, model):
            print(f"[env-wizard] Local model ready: {model}")
            return True
        print(f"[env-wizard] Timed out waiting for existing pull of '{model}'.")
        return False

    print(f"[env-wizard] Pulling local model: {model}")
    pull = subprocess.run([ollama_bin, "pull", model], check=False)
    if pull.returncode == 0:
        print(f"[env-wizard] Local model ready: {model}")
        return True
    else:
        print(f"[env-wizard] Failed to pull model: {model}")
        print(f"[env-wizard] Run manually: ollama pull {model}")
        return False


def bootstrap_local_llm_runtime(repo_root: Path, runtime: dict[str, Any], interactive: bool = True) -> tuple[bool, str]:
    llm_control = runtime.get("llm_control", {}) if isinstance(runtime.get("llm_control"), dict) else {}
    llm_mode = str(llm_control.get("llm_mode", "external_preferred")).strip().lower()
    strict_local = bool(llm_control.get("strict_local_first", llm_mode == "local_default"))
    model = str(llm_control.get("local_model", "veridoc-writer")).strip() or "veridoc-writer"
    base_model = str(llm_control.get("local_base_model", "qwen3:30b")).strip() or "qwen3:30b"
    auto_install = bool(llm_control.get("auto_install_local_model_on_setup", True))
    security = runtime.get("security", {}) if isinstance(runtime.get("security"), dict) else {}
    operation_mode = str(security.get("operation_mode", "")).strip().lower()
    should_bootstrap = strict_local or llm_mode == "local_default" or operation_mode in {"strict-local", "hybrid"}

    if not should_bootstrap:
        return True, "skip: mode does not require local runtime bootstrap"
    if not auto_install:
        return True, "skip: auto_install_local_model_on_setup=false"

    # If runtime and required base model already exist, do not ask for reinstall/repull.
    ready_bin = _find_reachable_ollama_bin(repo_root)
    if ready_bin and _ollama_model_present(ready_bin, base_model):
        print(f"[env-wizard] Detected existing Ollama runtime and base model: {base_model}")
        modelfile_path = _create_veridoc_modelfile(repo_root, base_model=base_model, model_name=model)
        if not _ollama_model_present(ready_bin, model):
            if interactive:
                if _prompt_yes_no(f"Create local model profile '{model}' now?", default_yes=True):
                    _create_ollama_model(model, modelfile_path)
            else:
                _create_ollama_model(model, modelfile_path)
        else:
            print(f"[env-wizard] Local model profile already present: {model}")
        return True, f"ok: reused existing Ollama runtime ({base_model})"

    if interactive:
        if not _prompt_yes_no(
            f"Install Ollama + pull base model '{base_model}' now for operation_mode={operation_mode or llm_mode}?",
            default_yes=True,
        ):
            return True, "skipped by user"

    try:
        install_result = _install_ollama_and_model(base_model, repo_root)
    except TypeError:
        # Backward-compatible path for tests/monkeypatches with legacy 1-arg stub.
        install_result = _install_ollama_and_model(base_model)  # type: ignore[misc]
    if install_result is False:
        return False, "failed: ollama install/pull"

    modelfile_path = _create_veridoc_modelfile(repo_root, base_model=base_model, model_name=model)
    if interactive:
        if _prompt_yes_no(f"Create local model profile '{model}' now?", default_yes=True):
            _create_ollama_model(model, modelfile_path)
    else:
        _create_ollama_model(model, modelfile_path)
    return True, f"ok: ollama runtime prepared ({base_model} -> {model})"


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
    if _ollama_model_present(ollama_bin, model_name):
        print(f"[env-wizard] Local model profile already present: {model_name}")
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


def install_weekly_scheduler(repo_root: Path) -> tuple[bool, str]:
    """Install weekly scheduler automatically for docsops bundle."""
    candidates = [
        repo_root / "docsops" / "ops",
        repo_root / "ops",
    ]
    ops_dir = next((p for p in candidates if p.exists()), None)
    if ops_dir is None:
        return False, "ops directory not found (expected docsops/ops or ops)."

    system = platform.system().lower()
    if system == "windows":
        script = ops_dir / "install_windows_task.ps1"
        if not script.exists():
            return False, f"missing scheduler script: {script}"
        ps_bin = shutil.which("powershell") or shutil.which("pwsh")
        if not ps_bin:
            return False, "PowerShell is not available in PATH."
        cmd = [ps_bin, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)]
    else:
        script = ops_dir / "install_cron_weekly.sh"
        if not script.exists():
            return False, f"missing scheduler script: {script}"
        cmd = ["bash", str(script)]

    completed = subprocess.run(cmd, cwd=str(repo_root), check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        details = (completed.stderr or completed.stdout or "").strip()
        return False, details or f"scheduler install command failed with rc={completed.returncode}"
    return True, ""


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
    runtime_path = _resolve_runtime_path(repo_root)
    prereqs = _detect_setup_prereqs(runtime, values)
    runtime, fallback_updates = _apply_local_fallbacks(runtime, prereqs)
    if runtime_path is not None and fallback_updates:
        if _write_runtime(runtime_path, runtime):
            print(f"[env-wizard] applied strict-local fallback updates: {len(fallback_updates)}")
            for line in fallback_updates:
                print(f"[env-wizard] - {line}")
        else:
            print("[env-wizard] warning: cannot persist fallback updates (PyYAML missing).")

    print("\n[env-wizard] Ownership and prerequisites")
    print("- Client-managed: provider keys, optional external integrations, runner prerequisites.")
    print("- Operator-managed: signed license JWT, capability pack, default policy endpoints.")
    if prereqs.get("missing_inputs"):
        print(f"- Missing client inputs: {len(prereqs['missing_inputs'])} (can be added later to {env_path.name}).")
    if prereqs.get("blocking_reasons"):
        print(f"- Hard blockers detected: {', '.join(prereqs['blocking_reasons'])}")
    else:
        print("- Hard blockers: none")

    preflight_report = {
        "ok": len(prereqs.get("blocking_reasons", [])) == 0,
        "env_path": str(env_path),
        "runtime_path": str(runtime_path) if runtime_path else "",
        "fallback_updates": fallback_updates,
        "prerequisites": prereqs,
    }
    SETUP_PREFLIGHT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    SETUP_PREFLIGHT_REPORT.write_text(json.dumps(preflight_report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[env-wizard] preflight report: {SETUP_PREFLIGHT_REPORT}")

    llm_control = runtime.get("llm_control", {}) if isinstance(runtime.get("llm_control"), dict) else {}
    llm_mode = str(llm_control.get("llm_mode", "external_preferred")).strip().lower()
    strict_local = bool(llm_control.get("strict_local_first", llm_mode == "local_default"))
    quality_note = str(
        llm_control.get(
            "quality_delta_note",
            "Fully local mode may reduce output quality by ~10-15% on hardest synthesis tasks.",
        )
    ).strip()
    security = runtime.get("security", {}) if isinstance(runtime.get("security"), dict) else {}
    operation_mode = str(security.get("operation_mode", "")).strip().lower()
    if strict_local or llm_mode == "local_default" or operation_mode in {"strict-local", "hybrid"}:
        print(f"[env-wizard] LLM runtime bootstrap enabled for mode={operation_mode or llm_mode}. {quality_note}")
        ok_bootstrap, message = bootstrap_local_llm_runtime(repo_root, runtime, interactive=True)
        print(f"[env-wizard] local runtime bootstrap: {message}")
        if not ok_bootstrap:
            return 2
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

    ok_scheduler, scheduler_error = install_weekly_scheduler(repo_root)
    if ok_scheduler:
        print("[env-wizard] weekly scheduler installed automatically.")
    else:
        print(f"[env-wizard] scheduler auto-install failed: {scheduler_error}")

    system = platform.system().lower()
    if system == "windows":
        print("[env-wizard] manual run (optional, scheduler already installed): .\\docsops\\ops\\run_weekly_docsops.ps1")
        print("[env-wizard] next (Git Bash): bash docsops/ops/run_weekly_docsops.sh")
    else:
        print("[env-wizard] manual run (optional, scheduler already installed): bash docsops/ops/run_weekly_docsops.sh")
        print("[env-wizard] next (if using pwsh): ./docsops/ops/run_weekly_docsops.ps1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

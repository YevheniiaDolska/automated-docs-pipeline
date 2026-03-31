#!/usr/bin/env python3
"""Install optional Ask AI runtime pack into a target repository."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install Ask AI runtime pack")
    parser.add_argument("--target-dir", default=".", help="Target repository root")
    parser.add_argument("--output-dir", default="ask-ai-runtime", help="Runtime pack directory in target repo")
    parser.add_argument("--force", action="store_true", help="Overwrite existing output directory")
    parser.add_argument(
        "--skip-if-missing",
        action="store_true",
        help="Exit successfully when the runtime pack is missing",
    )
    return parser.parse_args()


def _copy_pack(source: Path, destination: Path, force: bool) -> None:
    if destination.exists():
        if not force:
            raise FileExistsError(
                f"Destination already exists: {destination}. Use --force to overwrite."
            )
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def _update_ask_ai_config(config_path: Path, runtime_dir: str) -> None:
    defaults = {
        "enabled": False,
        "provider": "openai",
        "billing_mode": "disabled",
        "model": "gpt-4.1-mini",
        "base_url": "https://api.openai.com/v1",
        "knowledge_index_path": "docs/assets/knowledge-retrieval-index.json",
        "knowledge_graph_path": "docs/assets/knowledge-graph.jsonld",
        "retrieval_eval_report_path": "reports/retrieval_evals_report.json",
        "assistant_bundle_glob": "reports/intent-bundles/*-assistant.json",
        "max_context_modules": 6,
        "temperature": 0.2,
        "top_p": 1.0,
        "max_tokens": 700,
        "require_user_auth": True,
        "allowed_roles": ["admin", "support"],
        "rate_limit_per_user_per_minute": 20,
        "retention_days": 30,
        "audit_logging": True,
    }

    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("pyyaml is required to update config/ask-ai.yml") from exc

    payload = defaults.copy()
    if config_path.exists():
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        if isinstance(loaded, dict):
            payload.update(loaded)

    runtime = payload.get("runtime", {})
    if not isinstance(runtime, dict):
        runtime = {}
    runtime.setdefault("enabled", False)
    runtime.setdefault("base_url", "http://localhost:8090")
    runtime.setdefault("ask_endpoint", "/api/v1/ask")
    runtime.setdefault("health_endpoint", "/healthz")
    runtime.setdefault("billing_webhook_endpoint", "/api/v1/billing/webhook")
    runtime.setdefault("widget_script_path", "/public/ask-ai-widget.js")
    runtime.setdefault("runtime_dir", runtime_dir)
    payload["runtime"] = runtime

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=False), encoding="utf-8")


def _write_install_report(target_dir: Path, output_dir: str) -> Path:
    report = {
        "installed": True,
        "runtime_dir": output_dir,
        "next_steps": [
            f"cd {output_dir}",
            "cp .env.example .env",
            "python3 -m venv .venv",
            "source .venv/bin/activate",
            "pip install -r requirements.txt",
            "uvicorn app.main:app --host 0.0.0.0 --port 8090",
        ],
    }
    report_path = target_dir / "reports" / "ask-ai-runtime-install.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return report_path


def main() -> int:
    args = parse_args()

    script_dir = Path(__file__).resolve().parent
    source_pack = script_dir.parent / "runtime" / "ask-ai-pack"
    if not source_pack.exists():
        if args.skip_if_missing:
            print(f"Ask AI runtime pack not found, skipping install: {source_pack}")
            return 0
        raise FileNotFoundError(f"Ask AI runtime pack not found: {source_pack}")

    target_dir = Path(args.target_dir).resolve()
    destination = target_dir / args.output_dir

    _copy_pack(source_pack, destination, args.force)
    _update_ask_ai_config(target_dir / "config" / "ask-ai.yml", args.output_dir)
    report_path = _write_install_report(target_dir, args.output_dir)

    print(f"Installed Ask AI runtime pack to: {destination}")
    print(f"Updated Ask AI config: {target_dir / 'config' / 'ask-ai.yml'}")
    print(f"Install report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

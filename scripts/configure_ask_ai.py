#!/usr/bin/env python3
"""Configure optional Ask AI module settings for customer deployments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG: dict[str, Any] = {
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

ALLOWED_PROVIDERS = {"openai", "anthropic", "azure-openai", "custom", "local", "ollama"}
ALLOWED_BILLING_MODES = {"disabled", "bring-your-own-key", "user-subscription"}


def _load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return DEFAULT_CONFIG.copy()
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("Ask AI config must be a YAML mapping.")
    merged = DEFAULT_CONFIG.copy()
    merged.update(payload)
    return merged


def _parse_roles(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    roles = [item.strip() for item in raw.split(",") if item.strip()]
    return roles or []


def _validate_config(config: dict[str, Any]) -> None:
    provider = str(config.get("provider", "")).strip()
    billing_mode = str(config.get("billing_mode", "")).strip()
    if provider not in ALLOWED_PROVIDERS:
        raise ValueError(
            f"Unsupported provider '{provider}'. Allowed: {sorted(ALLOWED_PROVIDERS)}"
        )
    if billing_mode not in ALLOWED_BILLING_MODES:
        raise ValueError(
            f"Unsupported billing_mode '{billing_mode}'. Allowed: {sorted(ALLOWED_BILLING_MODES)}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Configure Ask AI module")
    parser.add_argument("--config", default="config/ask-ai.yml", help="Path to ask-ai YAML config")
    parser.add_argument("--status", action="store_true", help="Print current config and exit")
    parser.add_argument("--enable", action="store_true", help="Enable Ask AI")
    parser.add_argument("--disable", action="store_true", help="Disable Ask AI")
    parser.add_argument("--provider", choices=sorted(ALLOWED_PROVIDERS), help="LLM provider")
    parser.add_argument(
        "--billing-mode",
        choices=sorted(ALLOWED_BILLING_MODES),
        help="Billing mode: disabled|bring-your-own-key|user-subscription",
    )
    parser.add_argument("--model", help="Model name")
    parser.add_argument("--base-url", help="Provider API base URL")
    parser.add_argument("--knowledge-index-path", help="Path to retrieval index JSON")
    parser.add_argument("--knowledge-graph-path", help="Path to JSON-LD knowledge graph")
    parser.add_argument("--retrieval-eval-report-path", help="Path to retrieval eval report JSON")
    parser.add_argument("--assistant-bundle-glob", help="Glob for assistant bundles")
    parser.add_argument("--max-context-modules", type=int, help="Max retrieved modules per answer")
    parser.add_argument("--temperature", type=float, help="Sampling temperature")
    parser.add_argument("--top-p", type=float, help="Nucleus sampling top-p")
    parser.add_argument("--max-tokens", type=int, help="Max output tokens")
    parser.add_argument("--require-user-auth", action="store_true", help="Require auth")
    parser.add_argument("--no-require-user-auth", action="store_true", help="Do not require auth")
    parser.add_argument("--allowed-roles", help="Comma-separated roles")
    parser.add_argument("--rate-limit-per-user-per-minute", type=int, help="Per-user rate limit")
    parser.add_argument("--retention-days", type=int, help="Retention window in days")
    parser.add_argument("--audit-logging", action="store_true", help="Enable audit logging")
    parser.add_argument("--no-audit-logging", action="store_true", help="Disable audit logging")
    parser.add_argument("--json-out", default="reports/ask-ai-config.json", help="Output JSON snapshot path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    config = _load_config(config_path)

    if args.status:
        print(yaml.safe_dump(config, sort_keys=False, allow_unicode=False))
        return 0

    if args.enable and args.disable:
        raise ValueError("Use only one of --enable or --disable.")

    if args.enable:
        config["enabled"] = True
    if args.disable:
        config["enabled"] = False
        if str(config.get("billing_mode")) == "user-subscription":
            config["billing_mode"] = "disabled"

    updates: dict[str, Any] = {
        "provider": args.provider,
        "billing_mode": args.billing_mode,
        "model": args.model,
        "base_url": args.base_url,
        "knowledge_index_path": args.knowledge_index_path,
        "knowledge_graph_path": args.knowledge_graph_path,
        "retrieval_eval_report_path": args.retrieval_eval_report_path,
        "assistant_bundle_glob": args.assistant_bundle_glob,
        "max_context_modules": args.max_context_modules,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "max_tokens": args.max_tokens,
        "rate_limit_per_user_per_minute": args.rate_limit_per_user_per_minute,
        "retention_days": args.retention_days,
    }
    for key, value in updates.items():
        if value is not None:
            config[key] = value

    roles = _parse_roles(args.allowed_roles)
    if roles is not None:
        config["allowed_roles"] = roles

    if args.require_user_auth and args.no_require_user_auth:
        raise ValueError("Use only one of --require-user-auth or --no-require-user-auth.")
    if args.require_user_auth:
        config["require_user_auth"] = True
    if args.no_require_user_auth:
        config["require_user_auth"] = False

    if args.audit_logging and args.no_audit_logging:
        raise ValueError("Use only one of --audit-logging or --no-audit-logging.")
    if args.audit_logging:
        config["audit_logging"] = True
    if args.no_audit_logging:
        config["audit_logging"] = False

    _validate_config(config)

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )

    json_out = Path(args.json_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(config, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    status = "enabled" if config.get("enabled") else "disabled"
    print(f"Ask AI is {status}. Config saved to {config_path}")
    print(f"Snapshot written to {json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

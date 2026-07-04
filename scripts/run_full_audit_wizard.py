#!/usr/bin/env python3
"""Run full audit flow (scorecard -> public audit -> executive PDF) in one interactive wizard."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
from pathlib import Path


def _slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug (lowercase, hyphens)."""
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-") or "client"


def _ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    raw = input(f"{prompt}{suffix}: ").strip()
    return raw if raw else default


def _ask_yes_no(prompt: str, default: bool) -> bool:
    default_label = "Y/n" if default else "y/N"
    raw = input(f"{prompt} ({default_label}): ").strip().lower()
    if not raw:
        return default
    return raw in {"y", "yes", "1", "true"}


PRICE_ENV_KEY = "VERIOPS_PIPELINE_MONTHLY_PRICE_USD"


def _read_env_value(env_path: Path, key: str) -> str:
    if not env_path.exists():
        return ""
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return ""


def _persist_env_value(env_path: Path, key: str, value: str) -> None:
    lines: list[str] = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    replaced = False
    for i, raw in enumerate(lines):
        if raw.strip().startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            replaced = True
            break
    if not replaced:
        lines.append(f"{key}={value}")
    env_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _run(cmd: list[str], cwd: Path) -> None:
    print(f"\n[audit] $ {' '.join(shlex.quote(part) for part in cmd)}")
    completed = subprocess.run(cmd, cwd=str(cwd), check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed (exit {completed.returncode}): {' '.join(cmd)}")


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    print("Full Audit Wizard (single-command flow)")
    print("This will run: scorecard -> public audit -> executive PDF.")

    company_name = _ask("Company name for PDF/report", "Client")
    topology = _ask("Topology mode (single-product|multi-project)", "single-product")
    if topology not in {"single-product", "multi-project"}:
        print("Invalid topology mode. Use single-product or multi-project.")
        return 2

    max_pages = _ask("Max pages per site", "120")
    timeout = _ask("Request timeout seconds", "15")
    llm_enabled = _ask_yes_no("Enable LLM executive analysis", True)
    llm_model = "claude-sonnet-5"
    llm_env_file = str(repo / ".env")
    llm_env_name = "ANTHROPIC_API_KEY"
    if llm_enabled:
        llm_model = _ask("LLM model", llm_model)
        llm_env_file = _ask("LLM .env file path", llm_env_file)
        llm_env_name = _ask("LLM API key env name", llm_env_name)

    env_path = repo / ".env"
    stored_price = os.environ.get(PRICE_ENV_KEY, "").strip() or _read_env_value(env_path, PRICE_ENV_KEY) or "1500"
    price_raw = _ask(
        "Pipeline monthly subscription quoted to this prospect, USD (tiers: 1500 / 3000 / 6000)",
        stored_price,
    )
    try:
        pipeline_price = max(0.0, float(price_raw))
    except ValueError:
        print(f"[warn] not a number: {price_raw!r}; price comparison disabled for this run")
        pipeline_price = 0.0
    if pipeline_price > 0 and price_raw != stored_price:
        if _ask_yes_no(f"Save {price_raw} as the default in .env ({PRICE_ENV_KEY})", False):
            _persist_env_value(env_path, PRICE_ENV_KEY, price_raw)
            print(f"[ok] default saved to {env_path}")

    print("\nEnter public docs URLs (one per line). Empty line to finish.")
    site_urls: list[str] = []
    idx = 1
    while True:
        raw = input(f"URL #{idx}: ").strip()
        if not raw:
            break
        site_urls.append(raw)
        idx += 1
    if not site_urls:
        print("At least one site URL is required.")
        return 2

    # 1) Internal scorecard (repo-aware, money model + findings)
    _run(
        [
            "python3",
            "scripts/generate_audit_scorecard.py",
            "--docs-dir",
            "docs",
            "--reports-dir",
            "reports",
            "--spec-path",
            "api/openapi.yaml",
            "--policy-pack",
            "policy_packs/api-first.yml",
            "--glossary-path",
            "glossary.yml",
            "--stale-days",
            "180",
            "--auto-run-smoke",
            "--json-output",
            "reports/audit_scorecard.json",
            "--html-output",
            "reports/audit_scorecard.html",
        ]
        + (["--pipeline-monthly-price-usd", str(pipeline_price)] if pipeline_price > 0 else []),
        cwd=repo,
    )

    # 2) Public audit (external signals + optional LLM + internal scorecard overlay)
    public_cmd = [
        "python3",
        "scripts/generate_public_docs_audit.py",
        "--topology-mode",
        topology,
        "--max-pages",
        str(max_pages),
        "--timeout",
        str(timeout),
        "--verification-modes",
        "bot,browser,authenticated",
        "--auto-scorecard",
        "--assumptions-profiles-dir",
        "config/company_assumptions",
        "--assumptions-autofill",
    ]
    if pipeline_price > 0:
        public_cmd.extend(["--pipeline-monthly-price-usd", str(pipeline_price)])
    for url in site_urls:
        public_cmd.extend(["--site-url", url])
    if llm_enabled:
        public_cmd.extend(
            [
                "--llm-enabled",
                "--llm-model",
                llm_model,
                "--llm-env-file",
                llm_env_file,
                "--llm-api-key-env-name",
                llm_env_name,
            ]
        )
    _run(public_cmd, cwd=repo)

    # 3) Premium executive PDF
    pdf_path = f"reports/{_slugify(company_name)}-executive-audit.pdf"
    _run(
        [
            "python3",
            "scripts/generate_executive_audit_pdf.py",
            "--scorecard-json",
            "reports/audit_scorecard.json",
            "--public-audit-json",
            "reports/public_docs_audit.json",
            "--llm-summary-json",
            "reports/public_docs_audit_llm_summary.json",
            "--company-name",
            company_name,
            "--output",
            pdf_path,
        ],
        cwd=repo,
    )

    print("\n[ok] Full audit flow complete.")
    print("[ok] reports/audit_scorecard.html")
    print("[ok] reports/public_docs_audit.html")
    print(f"[ok] {pdf_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.")
        raise SystemExit(130)
    except (RuntimeError, ValueError, TypeError, OSError) as error:  # noqa: BLE001
        print(f"\n[error] {error}", file=sys.stderr)
        raise SystemExit(1)

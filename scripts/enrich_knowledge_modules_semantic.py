#!/usr/bin/env python3
"""Optional LLM semantic enrichment for knowledge modules.

Adds/updates:
- semantic.topic
- semantic.intent
- semantic.audience
- semantic.keywords
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import yaml

from scripts.env_loader import load_local_env
from scripts.llm_egress import ensure_external_allowed, load_policy, redact_payload

ALLOWED_INTENTS = {
    "install", "configure", "troubleshoot", "optimize", "secure",
    "migrate", "automate", "compare", "integrate",
}
ALLOWED_AUDIENCES = {
    "beginner", "practitioner", "operator", "developer",
    "architect", "sales", "support", "all",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=False), encoding="utf-8")


def _call_anthropic_json(*, api_key: str, model: str, prompt: str, timeout: int) -> dict[str, Any]:
    body = {
        "model": model,
        "max_tokens": 500,
        "temperature": 0.1,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = Request(
        url="https://api.anthropic.com/v1/messages",
        data=json.dumps(body, ensure_ascii=True).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urlopen(req, timeout=timeout) as resp:
        raw = json.loads(resp.read().decode("utf-8", errors="ignore") or "{}")
    text = ""
    for part in raw.get("content", []) if isinstance(raw.get("content"), list) else []:
        if isinstance(part, dict) and part.get("type") == "text":
            text = str(part.get("text", "")).strip()
            if text:
                break
    if not text:
        raise RuntimeError("LLM returned empty response")
    stripped = text.strip()
    if stripped.startswith("```"):
        first_nl = stripped.find("\n")
        if first_nl != -1:
            stripped = stripped[first_nl + 1 :]
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()
    parsed = json.loads(stripped)
    if not isinstance(parsed, dict):
        raise RuntimeError("LLM response must be JSON object")
    return parsed


def _normalize_semantic(value: dict[str, Any], fallback_intent: str, fallback_audience: str, fallback_topic: str) -> dict[str, Any]:
    topic = str(value.get("topic", "")).strip() or fallback_topic
    intent = str(value.get("intent", "")).strip().lower() or fallback_intent
    audience = str(value.get("audience", "")).strip().lower() or fallback_audience
    if intent not in ALLOWED_INTENTS:
        intent = fallback_intent
    if audience not in ALLOWED_AUDIENCES:
        audience = fallback_audience
    raw_keywords = value.get("keywords", [])
    keywords: list[str] = []
    if isinstance(raw_keywords, list):
        for item in raw_keywords:
            text = str(item).strip().lower()
            if text and text not in keywords:
                keywords.append(text)
            if len(keywords) >= 12:
                break
    if not keywords:
        keywords = [topic.lower()[:40]] if topic else []
    return {
        "topic": topic[:120],
        "intent": intent,
        "audience": audience,
        "keywords": keywords,
        "status": "llm_enriched",
    }


def _prompt_for_module(module: dict[str, Any]) -> str:
    title = str(module.get("title", "")).strip()
    summary = str(module.get("summary", "")).strip()
    content = module.get("content", {}) if isinstance(module.get("content"), dict) else {}
    docs_markdown = str(content.get("docs_markdown", "")).strip()[:3000]
    return (
        "Return strict JSON only with keys: topic, intent, audience, keywords. "
        f"intent must be one of {sorted(ALLOWED_INTENTS)}. "
        f"audience must be one of {sorted(ALLOWED_AUDIENCES)}. "
        "keywords must be an array of 3-12 short lowercase terms.\n\n"
        f"title: {title}\nsummary: {summary}\ncontent:\n{docs_markdown}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LLM semantic enrichment for knowledge modules")
    parser.add_argument("--modules-dir", default="knowledge_modules")
    parser.add_argument("--report", default="reports/knowledge_semantic_enrichment_report.json")
    parser.add_argument("--llm-model", default="claude-sonnet-4-5")
    parser.add_argument("--llm-api-key-env-name", default="ANTHROPIC_API_KEY")
    parser.add_argument("--llm-timeout", type=int, default=45)
    parser.add_argument("--llm-env-file", default=".env")
    parser.add_argument("--approve-external-once", action="store_true")
    parser.add_argument("--approve-external-for-run", action="store_true")
    parser.add_argument("--non-interactive", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="Optional max modules to enrich")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    modules_dir = Path(args.modules_dir)
    report_path = Path(args.report)
    load_local_env(repo_root, filenames=(args.llm_env_file, ".env", ".env.local", ".env.docsops.local"))

    api_key = str(os.environ.get(str(args.llm_api_key_env_name), "")).strip()
    if not modules_dir.exists():
        print(f"modules directory not found: {modules_dir}")
        return 1
    if not api_key:
        print(f"missing {args.llm_api_key_env_name}; skip enrichment")
        return 0

    policy = load_policy(repo_root / "docsops" / "config" / "client_runtime.yml")
    reports_dir = report_path.parent
    approved = ensure_external_allowed(
        policy=policy,
        step="knowledge_module_semantic_enrichment",
        reports_dir=reports_dir,
        approve_once=bool(args.approve_external_once),
        approve_for_run=bool(args.approve_external_for_run),
        non_interactive=bool(args.non_interactive),
    )
    if not approved:
        print("external LLM enrichment blocked by policy")
        return 0

    updated = 0
    failed = 0
    processed = 0
    details: list[dict[str, Any]] = []
    for path in sorted(modules_dir.glob("*.yml")):
        module = _load_yaml(path)
        if str(module.get("status", "")).strip().lower() != "active":
            continue
        processed += 1
        if int(args.limit) > 0 and processed > int(args.limit):
            break
        intents = module.get("intents", [])
        audiences = module.get("audiences", [])
        fallback_intent = str(intents[0]).strip().lower() if isinstance(intents, list) and intents else "configure"
        fallback_audience = str(audiences[0]).strip().lower() if isinstance(audiences, list) and audiences else "practitioner"
        fallback_topic = str(module.get("title", "")).strip() or "documentation"
        try:
            prompt_payload = {
                "title": module.get("title", ""),
                "summary": module.get("summary", ""),
                "content": (module.get("content", {}) or {}).get("docs_markdown", ""),
            }
            prompt_payload = redact_payload(prompt_payload) if policy.redact_before_external else prompt_payload
            prompt = _prompt_for_module(
                {
                    "title": prompt_payload.get("title", ""),
                    "summary": prompt_payload.get("summary", ""),
                    "content": {"docs_markdown": prompt_payload.get("content", "")},
                }
            )
            llm_raw = _call_anthropic_json(
                api_key=api_key,
                model=str(args.llm_model),
                prompt=prompt,
                timeout=int(args.llm_timeout),
            )
            module["semantic"] = _normalize_semantic(llm_raw, fallback_intent, fallback_audience, fallback_topic)
            _write_yaml(path, module)
            updated += 1
            details.append({"module_id": module.get("id"), "status": "updated"})
        except (RuntimeError, ValueError, TypeError, OSError, json.JSONDecodeError) as exc:
            failed += 1
            details.append({"module_id": module.get("id"), "status": "failed", "error": str(exc)})

    report = {
        "status": "ok",
        "processed": processed,
        "updated": updated,
        "failed": failed,
        "llm_model": str(args.llm_model),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "details": details[:200],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"knowledge semantic enrichment: updated={updated}, failed={failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

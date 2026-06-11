#!/usr/bin/env python3
"""Capture documentation screenshots from a metadata plan using Playwright.

Plan format (YAML/JSON):
captures:
  - id: shot-login
    url: https://app.example.com/login
    output: docs/assets/screenshots/login.png
    doc_path: how-to/authenticate-webhooks.md
    section_heading: Configure webhook authentication
    section_anchor: configure-webhook-authentication
    alt: Login screen
    wait_for: networkidle
    wait_selector: "#app"
    clip_selector: ".main-panel"
    full_page: false
    viewport:
      width: 1440
      height: 900
    actions:
      - type: click
        selector: "button[data-testid='start']"
      - type: fill
        selector: "input[name='email']"
        value: "demo@example.com"
      - type: wait_for_selector
        selector: ".loaded"
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import yaml


def _load_plan(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yml", ".yaml"}:
        payload = yaml.safe_load(text) or {}
    else:
        payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("Screenshot capture plan must be an object with `captures` list")
    return payload


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return default


def _norm_wait_until(raw: str) -> str:
    text = str(raw or "networkidle").strip().lower()
    if text in {"load", "domcontentloaded", "networkidle", "commit"}:
        return text
    return "networkidle"


def _default_output(item: dict[str, Any], idx: int) -> str:
    item_id = str(item.get("id", "")).strip() or f"capture-{idx+1}"
    safe_id = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in item_id).strip("-")
    if not safe_id:
        safe_id = f"capture-{idx+1}"
    return f"docs/assets/screenshots/{safe_id}.png"


def _run_action(page: Any, action: dict[str, Any], timeout_ms: int) -> None:
    action_type = str(action.get("type", "")).strip().lower()
    selector = str(action.get("selector", "")).strip()
    if action_type == "click" and selector:
        page.locator(selector).first.click(timeout=timeout_ms)
        return
    if action_type == "fill" and selector:
        value = str(action.get("value", ""))
        if value.startswith("${") and value.endswith("}"):
            env_name = value[2:-1].strip()
            value = os.getenv(env_name, "")
        page.locator(selector).first.fill(value, timeout=timeout_ms)
        return
    if action_type == "press" and selector:
        key = str(action.get("key", "Enter"))
        page.locator(selector).first.press(key, timeout=timeout_ms)
        return
    if action_type == "wait_for_selector" and selector:
        state = str(action.get("state", "visible"))
        page.wait_for_selector(selector, state=state, timeout=timeout_ms)
        return
    if action_type == "wait_ms":
        wait_ms = int(action.get("value", 500))
        page.wait_for_timeout(wait_ms)


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture screenshots from plan")
    parser.add_argument("--plan", default="docs/screenshots.capture.yml")
    parser.add_argument("--output-manifest", default="reports/screenshot_capture_manifest.json")
    parser.add_argument("--report", default="reports/screenshot_capture_report.json")
    parser.add_argument("--storage-state", default="")
    parser.add_argument("--timeout-ms", type=int, default=15000)
    parser.add_argument("--headless", default="true")
    args = parser.parse_args()

    repo_root = Path.cwd()
    plan_path = (repo_root / args.plan).resolve()
    out_manifest = (repo_root / args.output_manifest).resolve()
    report_path = (repo_root / args.report).resolve()
    out_manifest.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    plan = _load_plan(plan_path)
    defaults = plan.get("defaults", {}) if isinstance(plan.get("defaults"), dict) else {}
    auth = plan.get("auth", {}) if isinstance(plan.get("auth"), dict) else {}
    captures = plan.get("captures", [])
    if not isinstance(captures, list) or not captures:
        payload = {
            "ok": True,
            "skipped": True,
            "reason": "capture_plan_not_found_or_empty",
            "plan": str(plan_path),
        }
        out_manifest.write_text(json.dumps({"captures": []}, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        report_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        print(f"[screenshot-capture] skipped: {plan_path} is missing or empty")
        return 0

    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        payload = {
            "ok": False,
            "skipped": True,
            "reason": "playwright_not_available",
            "plan": str(plan_path),
            "hint": "Install playwright and browser binaries to enable automatic screenshot capture.",
        }
        out_manifest.write_text(json.dumps({"captures": []}, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        report_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        print("[screenshot-capture] skipped: playwright not available")
        return 0

    results: list[dict[str, Any]] = []
    failed = 0
    headless = _as_bool(args.headless, default=True)
    storage_state = str(args.storage_state).strip() or str(defaults.get("storage_state", "")).strip()

    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(headless=headless)
        except Exception as exc:  # noqa: BLE001
            payload = {
                "ok": False,
                "skipped": True,
                "reason": "playwright_browser_not_installed",
                "hint": "Run: python -m playwright install chromium",
                "error": str(exc),
            }
            out_manifest.write_text(json.dumps({"captures": []}, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
            report_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
            print("[screenshot-capture] skipped: playwright browser binaries are missing")
            return 0
        context_kwargs: dict[str, Any] = {}
        if storage_state:
            state_path = Path(storage_state)
            if not state_path.is_absolute():
                state_path = (repo_root / state_path).resolve()
            if state_path.exists():
                context_kwargs["storage_state"] = str(state_path)

        context = browser.new_context(**context_kwargs)
        try:
            if bool(auth.get("enabled", False)):
                login_url = str(auth.get("login_url", "")).strip()
                auth_steps = auth.get("steps", [])
                auth_state_out = str(auth.get("storage_state_output", storage_state or "reports/playwright_storage_state.json")).strip()
                if login_url and isinstance(auth_steps, list):
                    login_page = context.new_page()
                    try:
                        login_page.goto(login_url, wait_until=_norm_wait_until(str(defaults.get("wait_for", "networkidle"))), timeout=args.timeout_ms)
                        for action in auth_steps:
                            if isinstance(action, dict):
                                _run_action(login_page, action, args.timeout_ms)
                        state_path = Path(auth_state_out)
                        if not state_path.is_absolute():
                            state_path = (repo_root / state_path).resolve()
                        state_path.parent.mkdir(parents=True, exist_ok=True)
                        context.storage_state(path=str(state_path))
                    finally:
                        login_page.close()

            for idx, raw in enumerate(captures):
                if not isinstance(raw, dict):
                    continue
                item = dict(raw)
                item_id = str(item.get("id", "")).strip() or f"capture-{idx+1}"
                url = str(item.get("url", "")).strip()
                if not url:
                    failed += 1
                    continue

                page = context.new_page()
                viewport = item.get("viewport") if isinstance(item.get("viewport"), dict) else {}
                if not viewport and isinstance(defaults.get("viewport"), dict):
                    viewport = defaults.get("viewport")
                if viewport:
                    width = int(viewport.get("width", 1440))
                    height = int(viewport.get("height", 900))
                    page.set_viewport_size({"width": width, "height": height})

                status = "ok"
                error = ""
                output_rel = str(item.get("output", "")).strip() or _default_output(item, idx)
                output_abs = Path(output_rel)
                if not output_abs.is_absolute():
                    output_abs = (repo_root / output_rel).resolve()
                output_abs.parent.mkdir(parents=True, exist_ok=True)

                try:
                    wait_until = _norm_wait_until(str(item.get("wait_for", defaults.get("wait_for", "networkidle"))))
                    page.goto(url, wait_until=wait_until, timeout=args.timeout_ms)

                    wait_selector = str(item.get("wait_selector", "")).strip()
                    if wait_selector:
                        page.wait_for_selector(wait_selector, timeout=args.timeout_ms)

                    actions = item.get("actions", [])
                    if isinstance(actions, list):
                        for action in actions:
                            if isinstance(action, dict):
                                _run_action(page, action, args.timeout_ms)

                    clip_selector = str(item.get("clip_selector", "")).strip()
                    full_page = _as_bool(item.get("full_page", defaults.get("full_page", False)), default=False)
                    if clip_selector:
                        page.locator(clip_selector).first.screenshot(path=str(output_abs))
                    else:
                        page.screenshot(path=str(output_abs), full_page=full_page)
                except Exception as exc:  # noqa: BLE001
                    status = "failed"
                    error = str(exc)
                    failed += 1
                finally:
                    page.close()

                rec = {
                    "id": item_id,
                    "output": str(output_abs.relative_to(repo_root)).replace("\\", "/"),
                    "doc_path": str(item.get("doc_path", "")).strip(),
                    "section_anchor": str(item.get("section_anchor", "")).strip(),
                    "section_heading": str(item.get("section_heading", "")).strip(),
                    "alt": str(item.get("alt", "")).strip(),
                    "url": url,
                    "status": status,
                }
                if error:
                    rec["error"] = error
                results.append(rec)
        finally:
            context.close()
            browser.close()

    manifest_payload = {"captures": results}
    out_manifest.write_text(json.dumps(manifest_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    report_payload = {
        "ok": failed == 0,
        "plan": str(plan_path),
        "captures_total": len(results),
        "captures_failed": failed,
        "output_manifest": str(out_manifest),
    }
    report_path.write_text(json.dumps(report_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"[screenshot-capture] captured={len(results)} failed={failed} -> {out_manifest}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

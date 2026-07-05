#!/usr/bin/env python3
"""Deliver Ask AI owner-alert records via email and Slack.

The Ask AI runtime appends an ``owner_alert`` record to a JSONL log whenever a
cited knowledge module is flagged as a critical contradiction. This script reads
that log and notifies the document owners over email (SMTP) and/or Slack
(incoming webhook). It tracks a cursor so each alert is delivered once.

Both channels are optional and independent: configure email, Slack, or both.
Nothing is sent when neither is configured (the script reports and exits 0).

Configuration (environment variables):

  Email:
    ASK_AI_ALERT_EMAIL_TO         Comma-separated recipient addresses
    ASK_AI_ALERT_EMAIL_FROM       From address (default: alerts@localhost)
    ASK_AI_ALERT_SMTP_HOST        SMTP server host
    ASK_AI_ALERT_SMTP_PORT        SMTP port (default: 587)
    ASK_AI_ALERT_SMTP_USER        SMTP username (optional)
    ASK_AI_ALERT_SMTP_PASSWORD    SMTP password (optional)
    ASK_AI_ALERT_SMTP_TLS         Use STARTTLS (default: true)

  Slack:
    ASK_AI_ALERT_SLACK_WEBHOOK    Slack incoming webhook URL

Usage:
  python3 scripts/notify_owner_alerts.py \
    --alerts-log reports/ask_ai_owner_alerts.jsonl [--dry-run] [--since-start]
"""

from __future__ import annotations

import argparse
import json
import os
import smtplib
import ssl
import urllib.error
import urllib.request
from email.message import EmailMessage
from pathlib import Path
from typing import Any


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_alerts(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    alerts: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict) and record.get("type") == "owner_alert":
            alerts.append(record)
    return alerts


def _cursor_path(alerts_log: Path) -> Path:
    return alerts_log.parent / (alerts_log.name + ".notified.cursor")


def read_cursor(alerts_log: Path) -> int:
    cursor = _cursor_path(alerts_log)
    if not cursor.exists():
        return 0
    try:
        return int(cursor.read_text(encoding="utf-8").strip() or "0")
    except (ValueError, OSError):
        return 0


def write_cursor(alerts_log: Path, count: int) -> None:
    cursor = _cursor_path(alerts_log)
    cursor.parent.mkdir(parents=True, exist_ok=True)
    cursor.write_text(str(count), encoding="utf-8")


def format_alert(alert: dict[str, Any]) -> str:
    modules = ", ".join(str(m) for m in alert.get("module_ids", [])) or "(unknown)"
    owners = ", ".join(str(o) for o in alert.get("owners", [])) or "(no owner on record)"
    reason = str(alert.get("reason", "contradiction"))
    ts = str(alert.get("ts", ""))
    return (
        f"Ask AI {reason} alert\n"
        f"  Time: {ts}\n"
        f"  Modules: {modules}\n"
        f"  Owners: {owners}\n"
        "  Action: review the cited docs and resolve the conflicting facts, then re-run indexing."
    )


def send_email(subject: str, body: str) -> tuple[bool, str]:
    recipients = [a.strip() for a in os.getenv("ASK_AI_ALERT_EMAIL_TO", "").split(",") if a.strip()]
    host = os.getenv("ASK_AI_ALERT_SMTP_HOST", "").strip()
    if not recipients or not host:
        return False, "email not configured"
    sender = os.getenv("ASK_AI_ALERT_EMAIL_FROM", "alerts@localhost").strip()
    port = int(os.getenv("ASK_AI_ALERT_SMTP_PORT", "587"))
    user = os.getenv("ASK_AI_ALERT_SMTP_USER", "").strip()
    password = os.getenv("ASK_AI_ALERT_SMTP_PASSWORD", "").strip()
    use_tls = _bool_env("ASK_AI_ALERT_SMTP_TLS", True)

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            if use_tls:
                server.starttls(context=ssl.create_default_context())
            if user and password:
                server.login(user, password)
            server.send_message(message)
        return True, f"email sent to {len(recipients)} recipient(s)"
    except (smtplib.SMTPException, OSError) as exc:
        return False, f"email failed: {exc}"


def send_slack(text: str) -> tuple[bool, str]:
    webhook = os.getenv("ASK_AI_ALERT_SLACK_WEBHOOK", "").strip()
    if not webhook:
        return False, "slack not configured"
    payload = json.dumps({"text": text}).encode("utf-8")
    request = urllib.request.Request(
        webhook, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            if 200 <= response.status < 300:
                return True, "slack delivered"
            return False, f"slack HTTP {response.status}"
    except (urllib.error.URLError, OSError) as exc:
        return False, f"slack failed: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Deliver Ask AI owner-alert records via email and Slack")
    parser.add_argument(
        "--alerts-log",
        default=os.getenv("ASK_AI_OWNER_ALERT_LOG_PATH", "reports/ask_ai_owner_alerts.jsonl"),
    )
    parser.add_argument("--dry-run", action="store_true", help="Print what would be sent; do not send or advance cursor")
    parser.add_argument("--since-start", action="store_true", help="Ignore the cursor and process all alerts")
    args = parser.parse_args()

    alerts_log = Path(args.alerts_log)
    alerts = load_alerts(alerts_log)
    cursor = 0 if args.since_start else read_cursor(alerts_log)
    pending = alerts[cursor:]

    email_configured = bool(os.getenv("ASK_AI_ALERT_EMAIL_TO", "").strip() and os.getenv("ASK_AI_ALERT_SMTP_HOST", "").strip())
    slack_configured = bool(os.getenv("ASK_AI_ALERT_SLACK_WEBHOOK", "").strip())

    print(f"[owner-alerts] total={len(alerts)} pending={len(pending)} email={email_configured} slack={slack_configured}")
    if not pending:
        print("[owner-alerts] nothing to deliver")
        return 0
    if not (email_configured or slack_configured) and not args.dry_run:
        print("[owner-alerts] no delivery channel configured; leaving alerts unsent")
        return 0

    delivered = 0
    for alert in pending:
        body = format_alert(alert)
        subject = "Ask AI documentation contradiction alert"
        if args.dry_run:
            print("---\n" + body)
            continue
        results = [send_email(subject, body), send_slack(body)]
        for ok, detail in results:
            print(f"[owner-alerts] {'sent' if ok else 'skip'}: {detail}")
        if any(ok for ok, _ in results):
            delivered += 1

    if not args.dry_run:
        write_cursor(alerts_log, len(alerts))
        print(f"[owner-alerts] delivered={delivered} cursor={len(alerts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

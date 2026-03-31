#!/usr/bin/env bash
# VeriDoc error log monitor
# Scans recent Docker logs for API/worker errors and sends deduplicated email alerts.
#
# Usage:
#   deploy/error_log_monitor.sh [minutes]
#
# Requirements:
#   - docker compose
#   - sendmail or compatible MTA
#   - VERIDOC_ADMIN_EMAIL and VERIDOC_SMTP_FROM in env files (optional fallback defaults used)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="/var/log/veridoc"
STATE_DIR="/var/lib/veridoc/error-monitor"
mkdir -p "$LOG_DIR" "$STATE_DIR"

# Load env from deploy files if present.
for envfile in "$SCRIPT_DIR/.env.production" "$SCRIPT_DIR/.env.staging"; do
    if [[ -f "$envfile" ]]; then
        # shellcheck disable=SC1090
        set -a; source "$envfile"; set +a
        break
    fi
done

ADMIN_EMAIL="${VERIDOC_ADMIN_EMAIL:-jane.dolska@gmail.com,eugenia@veri-doc.app}"
SMTP_FROM="${VERIDOC_SMTP_FROM:-noreply@veri-doc.app}"
WINDOW_MINUTES="${1:-5}"
ALERT_LOG="$LOG_DIR/error_monitor_alerts.log"
LAST_HASH_FILE="$STATE_DIR/last_error_hash.txt"

send_alert() {
    local subject="$1"
    local body="$2"
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) ALERT: $subject" >> "$ALERT_LOG"
    if command -v sendmail >/dev/null 2>&1; then
        IFS=',' read -ra ADDRS <<< "$ADMIN_EMAIL"
        for addr in "${ADDRS[@]}"; do
            addr="$(echo "$addr" | xargs)"
            {
                echo "From: $SMTP_FROM"
                echo "To: $addr"
                echo "Subject: [VeriDoc Error Alert] $subject"
                echo "Content-Type: text/plain; charset=utf-8"
                echo ""
                echo "$body"
            } | sendmail -f "$SMTP_FROM" "$addr" 2>/dev/null || true
        done
    fi
}

if ! command -v docker >/dev/null 2>&1; then
    echo "[error-monitor] docker not found; skipping"
    exit 0
fi

cd "$PROJECT_ROOT"

# Pull logs from API and worker only (most meaningful runtime errors).
raw_logs="$(docker compose -f docker-compose.production.yml logs api worker --since "${WINDOW_MINUTES}m" 2>/dev/null || true)"
if [[ -z "$raw_logs" ]]; then
    exit 0
fi

# Detect critical errors while ignoring common noise.
err_lines="$(echo "$raw_logs" | grep -E "ERROR|CRITICAL|Traceback|Exception:" | grep -v -E "Invalid webhook signature|404 Not Found|healthcheck" || true)"
if [[ -z "$err_lines" ]]; then
    exit 0
fi

hash_value="$(echo "$err_lines" | sha256sum | awk '{print $1}')"
last_hash=""
if [[ -f "$LAST_HASH_FILE" ]]; then
    last_hash="$(cat "$LAST_HASH_FILE" || true)"
fi

# Deduplicate: send only if a new distinct error signature appears.
if [[ "$hash_value" == "$last_hash" ]]; then
    exit 0
fi

echo "$hash_value" > "$LAST_HASH_FILE"

body="VeriDoc detected runtime errors in the last ${WINDOW_MINUTES} minutes.

Host: $(hostname)
Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)

Top lines:
$(echo "$err_lines" | tail -n 40)

Next steps:
1) docker compose -f docker-compose.production.yml ps
2) docker compose -f docker-compose.production.yml logs --tail 200 api worker
3) curl -fsS http://127.0.0.1:8000/health/ready
"

send_alert "API/worker runtime errors detected" "$body"

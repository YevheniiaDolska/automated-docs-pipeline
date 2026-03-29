#!/usr/bin/env bash
# VeriDoc health check monitor
# Checks staging and production endpoints, sends email alerts on failure.
# Designed to run via cron every 5 minutes.
#
# Usage: deploy/healthcheck_monitor.sh [staging|production|both]
# Default: both
#
# Requires: curl, msmtp or sendmail (for email alerts)
# Env vars (from .env file or exported):
#   VERIDOC_SMTP_HOST, VERIDOC_SMTP_PORT, VERIDOC_SMTP_USER,
#   VERIDOC_SMTP_PASSWORD, VERIDOC_SMTP_FROM, VERIDOC_ADMIN_EMAIL

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="/var/log/veridoc"
mkdir -p "$LOG_DIR"

# Load env if available
for envfile in "$SCRIPT_DIR/.env.staging" "$SCRIPT_DIR/.env.production"; do
    if [[ -f "$envfile" ]]; then
        # shellcheck disable=SC1090
        set -a; source "$envfile"; set +a
        break
    fi
done

ADMIN_EMAIL="${VERIDOC_ADMIN_EMAIL:-jane.dolska@gmail.com,eugenia@veri-doc.app}"
SMTP_FROM="${VERIDOC_SMTP_FROM:-noreply@veri-doc.app}"
ALERT_LOG="$LOG_DIR/healthcheck_alerts.log"
METRICS_LOG="$LOG_DIR/healthcheck_metrics.log"

# State files to avoid alert storms (one alert per incident, not per check)
STATE_DIR="/var/lib/veridoc/healthcheck"
mkdir -p "$STATE_DIR"

# Endpoints
STAGING_URL="http://127.0.0.1:8010/health/ready"
PRODUCTION_URL="http://127.0.0.1:8020/health/ready"

# Thresholds
LATENCY_WARN_MS=2000
LATENCY_CRIT_MS=5000
MAX_CONSECUTIVE_FAILURES=2

TARGET="${1:-both}"

log_metric() {
    local env="$1" status="$2" latency_ms="$3" http_code="$4"
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) env=$env status=$status latency_ms=$latency_ms http_code=$http_code" \
        >> "$METRICS_LOG"
}

send_alert() {
    local subject="$1" body="$2"
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) ALERT: $subject" >> "$ALERT_LOG"

    # Try sendmail first (works with msmtp, postfix, etc.)
    if command -v sendmail &>/dev/null; then
        IFS=',' read -ra ADDRS <<< "$ADMIN_EMAIL"
        for addr in "${ADDRS[@]}"; do
            addr="$(echo "$addr" | xargs)"
            {
                echo "From: $SMTP_FROM"
                echo "To: $addr"
                echo "Subject: [VeriDoc Alert] $subject"
                echo "Content-Type: text/plain; charset=utf-8"
                echo ""
                echo "$body"
            } | sendmail -f "$SMTP_FROM" "$addr" 2>/dev/null || true
        done
    fi

    # Also try curl to SMTP if sendmail is not available
    # (swmail is the primary path; this is a fallback)
}

check_endpoint() {
    local env_name="$1" url="$2"
    local state_file="$STATE_DIR/${env_name}_failures"
    local resolved_file="$STATE_DIR/${env_name}_resolved"

    # Perform the health check with timing
    local start_ns http_code body latency_ms
    start_ns=$(date +%s%N)

    set +e
    body=$(curl -sf --max-time 10 -w "\n%{http_code}" "$url" 2>/dev/null)
    local exit_code=$?
    set -e

    local end_ns
    end_ns=$(date +%s%N)
    latency_ms=$(( (end_ns - start_ns) / 1000000 ))

    # Extract HTTP status code (last line of output)
    http_code=$(echo "$body" | tail -1)
    body=$(echo "$body" | sed '$d')

    local failures=0
    [[ -f "$state_file" ]] && failures=$(cat "$state_file")

    if [[ $exit_code -ne 0 ]] || [[ "$http_code" -ge 500 ]] 2>/dev/null; then
        # Failure
        failures=$((failures + 1))
        echo "$failures" > "$state_file"
        rm -f "$resolved_file"

        log_metric "$env_name" "FAIL" "$latency_ms" "${http_code:-000}"

        if [[ $failures -ge $MAX_CONSECUTIVE_FAILURES ]]; then
            # Only alert once per incident (check if we already alerted)
            local alerted_file="$STATE_DIR/${env_name}_alerted"
            if [[ ! -f "$alerted_file" ]]; then
                send_alert \
                    "$env_name DOWN - $failures consecutive failures" \
                    "VeriDoc $env_name health check has failed $failures consecutive times.

URL: $url
HTTP code: ${http_code:-timeout}
Response: ${body:-<no response>}
Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)

Check server status:
  ssh root@204.168.146.27
  docker ps
  docker logs veridoc-${env_name}-api-1 --tail 50"
                touch "$alerted_file"
            fi
        fi
    else
        # Success
        if [[ $failures -ge $MAX_CONSECUTIVE_FAILURES ]]; then
            # Was down, now recovered - send recovery alert
            local alerted_file="$STATE_DIR/${env_name}_alerted"
            if [[ -f "$alerted_file" ]]; then
                send_alert \
                    "$env_name RECOVERED after $failures failures" \
                    "VeriDoc $env_name has recovered.

URL: $url
HTTP code: $http_code
Latency: ${latency_ms}ms
Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
                rm -f "$alerted_file"
            fi
        fi

        echo "0" > "$state_file"
        log_metric "$env_name" "OK" "$latency_ms" "$http_code"

        # Latency alerts
        if [[ $latency_ms -ge $LATENCY_CRIT_MS ]]; then
            local latency_alert_file="$STATE_DIR/${env_name}_slow"
            if [[ ! -f "$latency_alert_file" ]]; then
                send_alert \
                    "$env_name HIGH LATENCY: ${latency_ms}ms" \
                    "VeriDoc $env_name health check response time is critically high.

URL: $url
Latency: ${latency_ms}ms (threshold: ${LATENCY_CRIT_MS}ms)
Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
                touch "$latency_alert_file"
            fi
        elif [[ $latency_ms -lt $LATENCY_WARN_MS ]]; then
            rm -f "$STATE_DIR/${env_name}_slow"
        fi
    fi
}

# Run checks based on target
case "$TARGET" in
    staging)
        check_endpoint "staging" "$STAGING_URL"
        ;;
    production)
        check_endpoint "production" "$PRODUCTION_URL"
        ;;
    both)
        check_endpoint "staging" "$STAGING_URL"
        check_endpoint "production" "$PRODUCTION_URL"
        ;;
    *)
        echo "Usage: $0 [staging|production|both]"
        exit 1
        ;;
esac

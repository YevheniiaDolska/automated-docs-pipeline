#!/usr/bin/env bash
# Health check for license renewal timer/service.
#
# Verifies:
# - timer enabled/active
# - last service run completed successfully

set -euo pipefail

SERVICE="${1:-veridoc-license-renew.service}"
TIMER="${2:-veridoc-license-renew.timer}"

systemctl is-enabled "$TIMER" >/dev/null
systemctl is-active "$TIMER" >/dev/null

if ! systemctl --no-pager --full status "$SERVICE" | grep -Eq "Active: inactive \\(dead\\)|Active: active \\(running\\)"; then
    echo "[license-renew-health] unexpected service status for $SERVICE"
    systemctl --no-pager --full status "$SERVICE" || true
    exit 1
fi

if journalctl -u "$SERVICE" -n 20 --no-pager | grep -Fq "[license-renew] start"; then
    echo "[license-renew-health] OK: recent renewal run detected."
else
    echo "[license-renew-health] WARN: no recent renewal log marker."
fi

echo "[license-renew-health] timer is active and enabled."

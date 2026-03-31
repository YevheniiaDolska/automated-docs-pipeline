#!/usr/bin/env bash
# Install and enable VeriDoc observability monitors (health + runtime errors).
#
# Run on server:
#   sudo bash /opt/veridoc/deploy/setup_observability.sh

set -euo pipefail

ROOT_DIR="${1:-/opt/veridoc}"
DEPLOY_DIR="$ROOT_DIR/deploy"
SYSTEMD_DIR="/etc/systemd/system"

if [[ ! -d "$DEPLOY_DIR" ]]; then
    echo "[obs] deploy directory not found: $DEPLOY_DIR"
    exit 1
fi

chmod +x "$DEPLOY_DIR/healthcheck_monitor.sh" "$DEPLOY_DIR/error_log_monitor.sh"

install -m 0644 "$DEPLOY_DIR/systemd/veridoc-healthcheck-monitor.service" "$SYSTEMD_DIR/veridoc-healthcheck-monitor.service"
install -m 0644 "$DEPLOY_DIR/systemd/veridoc-healthcheck-monitor.timer" "$SYSTEMD_DIR/veridoc-healthcheck-monitor.timer"
install -m 0644 "$DEPLOY_DIR/systemd/veridoc-error-monitor.service" "$SYSTEMD_DIR/veridoc-error-monitor.service"
install -m 0644 "$DEPLOY_DIR/systemd/veridoc-error-monitor.timer" "$SYSTEMD_DIR/veridoc-error-monitor.timer"

systemctl daemon-reload
systemctl enable --now veridoc-healthcheck-monitor.timer
systemctl enable --now veridoc-error-monitor.timer

echo "[obs] Enabled timers:"
systemctl list-timers --all | grep -E "veridoc-(healthcheck|error)-monitor" || true

echo "[obs] Recent service runs:"
systemctl --no-pager --full status veridoc-healthcheck-monitor.service || true
systemctl --no-pager --full status veridoc-error-monitor.service || true

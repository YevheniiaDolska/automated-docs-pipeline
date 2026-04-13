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

maybe_chmod() {
    local path="$1"
    if [[ -f "$path" ]]; then
        chmod +x "$path"
    fi
}

install_unit_if_exists() {
    local src="$1"
    local dst="$2"
    if [[ -f "$src" ]]; then
        install -m 0644 "$src" "$dst"
        return 0
    fi
    return 1
}

maybe_chmod "$DEPLOY_DIR/healthcheck_monitor.sh"
maybe_chmod "$DEPLOY_DIR/error_log_monitor.sh"
maybe_chmod "$DEPLOY_DIR/server_license_renewal.sh"
maybe_chmod "$DEPLOY_DIR/license_renewal_healthcheck.sh"
maybe_chmod "$DEPLOY_DIR/server_client_key_rotation.sh"

install_unit_if_exists "$DEPLOY_DIR/systemd/veridoc-healthcheck-monitor.service" "$SYSTEMD_DIR/veridoc-healthcheck-monitor.service" || true
install_unit_if_exists "$DEPLOY_DIR/systemd/veridoc-healthcheck-monitor.timer" "$SYSTEMD_DIR/veridoc-healthcheck-monitor.timer" || true
install_unit_if_exists "$DEPLOY_DIR/systemd/veridoc-error-monitor.service" "$SYSTEMD_DIR/veridoc-error-monitor.service" || true
install_unit_if_exists "$DEPLOY_DIR/systemd/veridoc-error-monitor.timer" "$SYSTEMD_DIR/veridoc-error-monitor.timer" || true
install_unit_if_exists "$DEPLOY_DIR/systemd/veridoc-license-renew.service" "$SYSTEMD_DIR/veridoc-license-renew.service" || true
install_unit_if_exists "$DEPLOY_DIR/systemd/veridoc-license-renew.timer" "$SYSTEMD_DIR/veridoc-license-renew.timer" || true
install_unit_if_exists "$DEPLOY_DIR/systemd/veridoc-client-key-rotation.service" "$SYSTEMD_DIR/veridoc-client-key-rotation.service" || true
install_unit_if_exists "$DEPLOY_DIR/systemd/veridoc-client-key-rotation.timer" "$SYSTEMD_DIR/veridoc-client-key-rotation.timer" || true

systemctl daemon-reload
systemctl enable --now veridoc-healthcheck-monitor.timer 2>/dev/null || true
systemctl enable --now veridoc-error-monitor.timer 2>/dev/null || true
systemctl enable --now veridoc-license-renew.timer 2>/dev/null || true
systemctl enable --now veridoc-client-key-rotation.timer 2>/dev/null || true

echo "[obs] Enabled timers:"
systemctl list-timers --all | grep -E "veridoc-(healthcheck|error)-monitor|veridoc-license-renew|veridoc-client-key-rotation" || true

echo "[obs] Recent service runs:"
systemctl --no-pager --full status veridoc-healthcheck-monitor.service || true
systemctl --no-pager --full status veridoc-error-monitor.service || true
systemctl --no-pager --full status veridoc-license-renew.service || true
systemctl --no-pager --full status veridoc-client-key-rotation.service || true

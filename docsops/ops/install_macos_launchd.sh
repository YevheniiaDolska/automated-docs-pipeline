#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPO_SLUG="$(basename "$REPO_ROOT" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-')"
if [[ -z "$REPO_SLUG" ]]; then
  REPO_SLUG="repo"
fi

LABEL="app.veriops.weekly.${REPO_SLUG}"
PLIST_PATH="$HOME/Library/LaunchAgents/${LABEL}.plist"
RUNNER_PATH="$REPO_ROOT/docsops/ops/run_weekly_docsops.sh"
LOG_PATH="$REPO_ROOT/reports/docsops-weekly.log"

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$REPO_ROOT/reports"

cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>

  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>${RUNNER_PATH}</string>
  </array>

  <key>WorkingDirectory</key>
  <string>${REPO_ROOT}</string>

  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key>
    <integer>1</integer>
    <key>Hour</key>
    <integer>10</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>

  <key>StandardOutPath</key>
  <string>${LOG_PATH}</string>
  <key>StandardErrorPath</key>
  <string>${LOG_PATH}</string>

  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
PLIST

launchctl unload "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl load "$PLIST_PATH"

echo "Installed launchd job: ${LABEL} (Monday 10:00 local)"
echo "plist: ${PLIST_PATH}"

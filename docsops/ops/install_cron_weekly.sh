#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPO_SLUG="$(basename "$REPO_ROOT" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-')"
MARKER="# docsops-weekly-veriops-$REPO_SLUG"
LINE="0 10 * * 1 cd '$REPO_ROOT' && bash docsops/ops/run_weekly_docsops.sh >> '$REPO_ROOT/reports/docsops-weekly.log' 2>&1 $MARKER"
(crontab -l 2>/dev/null | grep -v "$MARKER"; echo "$LINE") | crontab -
echo "Installed weekly cron for VeriOpsWeekly-veriops-$REPO_SLUG at monday 10:00"

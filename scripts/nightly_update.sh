#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOY_DIR="${DEPLOY_DIR:-/var/www/ohmoors.de/html}"
RELOAD_NGINX="${RELOAD_NGINX:-0}"

cd "$ROOT_DIR"

# Refresh events.json only. schedule.html reads it client-side at runtime.
/usr/bin/env python3 events.py

if [[ -e "$DEPLOY_DIR" && ! -d "$DEPLOY_DIR" ]]; then
  echo "ERROR: DEPLOY_DIR is a file: $DEPLOY_DIR"
  echo "Set DEPLOY_DIR to a directory for static files (for example /var/www/ohmoors)."
  exit 1
fi

mkdir -p "$DEPLOY_DIR"
install -m 0644 "$ROOT_DIR/events.json" "$DEPLOY_DIR/events.json"

if [[ "$RELOAD_NGINX" == "1" ]]; then
  nginx -t
  systemctl reload nginx
fi

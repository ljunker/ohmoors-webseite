#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$HOME/ohmoors-website}"
DEPLOY_DIR="${DEPLOY_DIR:-/var/www/ohmoors.de/html}"

if [[ ! -d "$PROJECT_ROOT" ]]; then
  echo "ERROR: PROJECT_ROOT fehlt: $PROJECT_ROOT" >&2
  exit 1
fi

if [[ ! -d "$DEPLOY_DIR" ]]; then
  echo "ERROR: DEPLOY_DIR fehlt: $DEPLOY_DIR" >&2
  exit 1
fi

if [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
else
  PYTHON_BIN="$(command -v python3)"
fi

"$PYTHON_BIN" "$PROJECT_ROOT/events.py"
install -m 0644 "$PROJECT_ROOT/events.json" "$DEPLOY_DIR/events.json"

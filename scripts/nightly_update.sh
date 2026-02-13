#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOY_DIR="${DEPLOY_DIR:-/var/www/ohmoors.de/html}"
PROJECT_ROOT="${PROJECT_ROOT:-$ROOT_DIR}"
LOCK_FILE="${LOCK_FILE:-/tmp/ohmoors-events.lock}"

if [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
else
  PYTHON_BIN="$(command -v python3)"
fi

if [[ ! -d "$PROJECT_ROOT" ]]; then
  echo "ERROR: PROJECT_ROOT does not exist: $PROJECT_ROOT"
  exit 1
fi

if [[ ! -f "$PROJECT_ROOT/events.py" ]]; then
  echo "ERROR: Missing events.py in PROJECT_ROOT: $PROJECT_ROOT"
  exit 1
fi

if [[ -e "$DEPLOY_DIR" && ! -d "$DEPLOY_DIR" ]]; then
  echo "ERROR: DEPLOY_DIR is a file: $DEPLOY_DIR"
  echo "Set DEPLOY_DIR to a directory for static files (for example /var/www/ohmoors.de/html)."
  exit 1
fi

mkdir -p "$DEPLOY_DIR"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "INFO: Another update run is active. Exiting without changes."
  exit 0
fi

tmp_dir="$(mktemp -d)"
cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

echo "INFO: Generating events.json from calendar feed..."
(cd "$tmp_dir" && "$PYTHON_BIN" "$PROJECT_ROOT/events.py")

candidate="$tmp_dir/events.json"
if [[ ! -s "$candidate" ]]; then
  echo "ERROR: Generated events.json is missing or empty."
  exit 2
fi

"$PYTHON_BIN" -m json.tool "$candidate" >/dev/null

dest="$DEPLOY_DIR/events.json"
backup="$DEPLOY_DIR/events.json.last-good"
staged="$DEPLOY_DIR/.events.json.tmp.$$"

install -m 0644 "$candidate" "$staged"
if [[ -f "$dest" ]]; then
  install -m 0644 "$dest" "$backup"
fi
mv -f "$staged" "$dest"

echo "INFO: events.json updated successfully."

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

before="$(git rev-parse HEAD)"
git pull --ff-only
after="$(git rev-parse HEAD)"

if [[ "$before" != "$after" ]]; then
  source .venv/bin/activate
  make clean build deploy
else
  echo "Kein Git-Update vorhanden, überspringe make."
fi

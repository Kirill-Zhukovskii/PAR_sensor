#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

if [[ ! -x "$PROJECT_DIR/.venv/bin/uvicorn" ]]; then
  echo "Virtual environment is missing. Run ./scripts/install_on_pi.sh first." >&2
  exit 1
fi

set -a
source "$PROJECT_DIR/.env"
set +a

exec "$PROJECT_DIR/.venv/bin/uvicorn" app.main:app --host "${WEB_HOST:-0.0.0.0}" --port "${WEB_PORT:-8000}"

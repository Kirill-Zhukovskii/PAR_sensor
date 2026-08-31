#!/usr/bin/env bash
set -euo pipefail

# Run this script once on the Raspberry Pi. It registers the already-installed
# application as a systemd service and starts it now and after every boot.

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
ENV_FILE="$PROJECT_DIR/.env"
START_SCRIPT="$PROJECT_DIR/scripts/start.sh"
SERVICE_NAME="par-sensor.service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"
RUN_USER="${SUDO_USER:-$(id -un)}"
RUN_GROUP="$(id -gn "$RUN_USER")"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Error: $VENV_PYTHON was not found or is not executable." >&2
  echo "Create the virtual environment and install requirements first." >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Error: $ENV_FILE was not found." >&2
  echo "Copy .env.example to .env and check its settings first." >&2
  exit 1
fi

if [[ ! -f "$START_SCRIPT" ]]; then
  echo "Error: $START_SCRIPT was not found." >&2
  exit 1
fi

if [[ "$PROJECT_DIR" == *$'\n'* || "$PROJECT_DIR" == *'"'* ]]; then
  echo "Error: the project path cannot contain a newline or double quote." >&2
  exit 1
fi

# Import the application before installing the service so configuration or
# dependency errors are reported immediately.
(
  cd "$PROJECT_DIR"
  "$VENV_PYTHON" -c "import app.main"
)

sudo tee "$SERVICE_FILE" >/dev/null <<EOF_SERVICE
[Unit]
Description=PAR Sensor web application
After=network.target

[Service]
Type=simple
User=$RUN_USER
Group=$RUN_GROUP
WorkingDirectory="$PROJECT_DIR"
ExecStart=/bin/bash "$START_SCRIPT"
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF_SERVICE

sudo systemctl daemon-reload
sudo systemd-analyze verify "$SERVICE_FILE"
sudo systemctl enable --now "$SERVICE_NAME"

echo
echo "$SERVICE_NAME is enabled and running."
echo "Status: sudo systemctl status $SERVICE_NAME"
echo "Logs:   journalctl -u $SERVICE_NAME -f"

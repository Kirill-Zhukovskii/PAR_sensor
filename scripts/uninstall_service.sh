#!/usr/bin/env bash
set -euo pipefail

sudo systemctl disable --now par-sensor.service 2>/dev/null || true
sudo rm -f /etc/systemd/system/par-sensor.service
sudo systemctl daemon-reload
echo "par-sensor.service removed. Project files were not deleted."

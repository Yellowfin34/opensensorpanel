#!/usr/bin/env bash
set -euo pipefail

APP_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/opensensorpanel"
BIN_PATH="${HOME}/.local/bin/opensensorpanel"
DESKTOP_FILE="${XDG_DATA_HOME:-$HOME/.local/share}/applications/opensensorpanel.desktop"

rm -f "$BIN_PATH" "$DESKTOP_FILE"
rm -rf "$APP_HOME"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "${XDG_DATA_HOME:-$HOME/.local/share}/applications" || true
fi

echo "OpenSensorPanel user install removed."

#!/usr/bin/env bash
set -euo pipefail

APP_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/opensensorpanel"
BIN_DIR="${HOME}/.local/bin"
VENV_DIR="${APP_HOME}/venv"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "$APP_HOME" "$BIN_DIR"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install "$REPO_DIR"

cat > "$BIN_DIR/opensensorpanel" <<EOF
#!/usr/bin/env bash
exec "$VENV_DIR/bin/opensensorpanel" "\$@"
EOF
chmod +x "$BIN_DIR/opensensorpanel"

"$BIN_DIR/opensensorpanel" install-desktop --launcher "$BIN_DIR/opensensorpanel"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "${XDG_DATA_HOME:-$HOME/.local/share}/applications" || true
fi

echo "OpenSensorPanel installed for this user."
echo "Launch it from your app menu, or run: opensensorpanel app --kiosk"

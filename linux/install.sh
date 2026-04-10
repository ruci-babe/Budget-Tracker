#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPT_DIR"

RUN_AFTER_INSTALL=false
if [ "${1:-}" = "--run" ] || [ "${1:-}" = "-r" ]; then
  RUN_AFTER_INSTALL=true
fi

echo "=== Expense Tracker install script ==="

echo "Installing required system packages..."
if ! command -v apt-get >/dev/null 2>&1; then
  echo "ERROR: apt-get is required for this install script." >&2
  exit 1
fi

sudo apt-get update || true
sudo apt-get install -y python3 python3-venv python3-pip python3-tk tesseract-ocr libtesseract-dev

if [ ! -d ".venv" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

python3 -m pip install --upgrade pip
python3 -m pip install --extra-index-url https://PySimpleGUI.net/install -r requirements.txt
python3 -m pip install --force-reinstall --extra-index-url https://PySimpleGUI.net/install PySimpleGUI

# Install desktop launcher file for Pop!_OS/GNOME integration
echo "Installing desktop launcher file and icon..."
DESKTOP_DIR="${HOME}/.local/share/applications"
ICON_DIR="${HOME}/.local/share/icons/hicolor/scalable/apps"
mkdir -p "$DESKTOP_DIR" "$ICON_DIR"

# Install icon file
if [ -f "${SCRIPT_DIR}/expense-tracker.svg" ]; then
  cp "${SCRIPT_DIR}/expense-tracker.svg" "${ICON_DIR}/expense-tracker.svg"
  echo "✓ Icon installed to: $ICON_DIR/expense-tracker.svg"
fi

# Create the .desktop file with the correct installation path
DESKTOP_FILE="$DESKTOP_DIR/expense-tracker.desktop"
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Expense Tracker
Comment=Track receipts, scan emails, and manage spending
Categories=Office;Finance;
Exec=env PYTHONUNBUFFERED=1 ${SCRIPT_DIR}/.venv/bin/python3 ${SCRIPT_DIR}/desktop_app.py
Icon=expense-tracker
Terminal=false
StartupNotify=true
Keywords=expenses;budget;tracker;receipts;
X-GNOME-Keywords=expenses;budget;tracker;receipts;
Path=${SCRIPT_DIR}
EOF

chmod +x "$DESKTOP_FILE"
echo "✓ Desktop launcher installed to: $DESKTOP_DIR/expense-tracker.desktop"

# Update icon cache to make the app appear immediately in application menu
if command -v update-desktop-database >/dev/null 2>&1; then
  echo "Updating application menu database..."
  update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
  echo "✓ Application menu updated"
fi

# Update icon cache if available
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  echo "Updating icon cache..."
  gtk-update-icon-cache "${HOME}/.local/share/icons/hicolor" 2>/dev/null || true
  echo "✓ Icon cache updated"
fi

if [ "$RUN_AFTER_INSTALL" = true ]; then
  echo "Expense Tracker installed successfully. Launching now..."
  python3 desktop_app.py
  exit 0
fi

cat <<'EOF'

Installation complete.
The app has been integrated with Pop!_OS application menu and supports light/dark theme switching.

Run the app with:
  source .venv/bin/activate
  python3 desktop_app.py

Or search for "Expense Tracker" in your applications menu.

To build a standalone Linux executable, run:
  ./build.sh
EOF

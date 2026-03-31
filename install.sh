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

if [ "$RUN_AFTER_INSTALL" = true ]; then
  echo "Expense Tracker installed successfully. Launching now..."
  python3 desktop_app.py
  exit 0
fi

cat <<'EOF'

Installation complete.
Run the app with:
  source .venv/bin/activate
  python3 desktop_app.py

To build a standalone Linux executable, run:
  ./build.sh
EOF

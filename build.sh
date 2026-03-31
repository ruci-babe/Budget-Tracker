#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

. .venv/bin/activate
pip install --upgrade pip
pip install --extra-index-url https://PySimpleGUI.net/install -r requirements.txt
pip install --force-reinstall --extra-index-url https://PySimpleGUI.net/install PySimpleGUI
pyinstaller --noconfirm --clean --onefile --windowed desktop_app.py

echo "Build complete: dist/desktop_app"
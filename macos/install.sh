#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPT_DIR"

RUN_AFTER_INSTALL=false
if [ "${1:-}" = "--run" ] || [ "${1:-}" = "-r" ]; then
  RUN_AFTER_INSTALL=true
fi

echo "=== Expense Tracker macOS Installer ==="
echo

# Check if Python 3 is installed
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: Python 3.8+ is required but not installed."
  echo "Please install Python from https://www.python.org/downloads/"
  echo "Or use Homebrew: brew install python3"
  exit 1
fi

echo "Python version:"
python3 --version
echo

# Install Homebrew if not present
if ! command -v brew >/dev/null 2>&1; then
  echo "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install Tesseract OCR
echo "Checking for Tesseract OCR..."
if ! command -v tesseract >/dev/null 2>&1; then
  echo "Installing Tesseract OCR via Homebrew..."
  brew install tesseract
else
  echo "✓ Tesseract already installed"
fi

# Create virtual environment
if [ ! -d ".venv" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install --extra-index-url https://PySimpleGUI.net/install -r requirements.txt
python3 -m pip install --force-reinstall --extra-index-url https://PySimpleGUI.net/install PySimpleGUI

# Create macOS app bundle (optional but recommended)
echo "Setting up macOS app integration..."
APP_BUNDLE_DIR="${HOME}/Applications/Expense Tracker.app"
mkdir -p "${APP_BUNDLE_DIR}/Contents/MacOS"
mkdir -p "${APP_BUNDLE_DIR}/Contents/Resources"

# Create launcher script
cat > "${APP_BUNDLE_DIR}/Contents/MacOS/launcher.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." >/dev/null 2>&1 && pwd)"
source "${SCRIPT_DIR}/.venv/bin/activate"
python3 "${SCRIPT_DIR}/desktop_app.py"
EOF

chmod +x "${APP_BUNDLE_DIR}/Contents/MacOS/launcher.sh"

# Copy icon if available
if [ -f "${SCRIPT_DIR}/../expense-tracker.icns" ]; then
  cp "${SCRIPT_DIR}/../expense-tracker.icns" "${APP_BUNDLE_DIR}/Contents/Resources/AppIcon.icns"
fi

# Create Info.plist
cat > "${APP_BUNDLE_DIR}/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleExecutable</key>
    <string>launcher.sh</string>
    <key>CFBundleIdentifier</key>
    <string>com.expensetracker.app</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Expense Tracker</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>NSMainNibFile</key>
    <string></string>
    <key>NSHumanReadableCopyright</key>
    <string>© 2026 Expense Tracker</string>
</dict>
</plist>
EOF

echo "✓ macOS app bundle created at: ${APP_BUNDLE_DIR}"

if [ "$RUN_AFTER_INSTALL" = true ]; then
  echo "Expense Tracker installed successfully. Launching now..."
  python3 desktop_app.py
  exit 0
fi

cat <<'EOF'

Installation complete!
================================

You can launch the app with:
1. Double-click "Expense Tracker.app" in your Applications folder
2. From command line:
   source .venv/bin/activate
   python3 desktop_app.py

To build a standalone macOS executable (optional):
  pyinstaller --onefile --windowed --osx-bundle-identifier=com.expensetracker.app desktop_app.py

EOF

# Expense Tracker - macOS Installation

## Quick Start

```bash
chmod +x install.sh
./install.sh
```

Then launch from Applications folder or run:

```bash
source .venv/bin/activate
python3 desktop_app.py
```

## Prerequisites

### Python 3.8+
- Install via Homebrew (recommended):
  ```bash
  brew install python3
  ```
- Or download from https://www.python.org/downloads/

### Tesseract OCR
- Automatically installed via Homebrew during setup
- Enables receipt scanning with OCR

## Installation Details

The installer will:
1. ✅ Check for Python 3 installation
2. ✅ Install Homebrew (if not present)
3. ✅ Install Tesseract OCR
4. ✅ Create a Python virtual environment
5. ✅ Install Python packages
6. ✅ Create macOS app bundle in Applications folder
7. ✅ Set up app icon integration

## Features
- **Native macOS Integration**: Appears as a proper app bundle
- **Homebrew Support**: Easy dependency management
- **Dark Mode Support**: Works beautifully with macOS dark mode
- **Tesseract OCR**: Built-in receipt scanning

## Launching the App

### From Applications
1. Open Finder
2. Go to Applications
3. Double-click "Expense Tracker.app"

### From Terminal
```bash
source .venv/bin/activate
python3 desktop_app.py
```

## Building Standalone DMG (Optional)

To create a distributable DMG file:

```bash
pip install py2app
python setup.py py2app
```

## Troubleshooting

### "Python 3 not found"
```bash
brew install python3
```

### Tesseract installation fails
```bash
brew tap UB-Mannheim/tesseract
brew install tesseract
```

### App doesn't launch from Applications
Try launching from Terminal to see error messages:
```bash
cd path/to/Budget-Tracker
source .venv/bin/activate
python3 desktop_app.py
```

### Permission denied on install.sh
```bash
chmod +x install.sh
./install.sh
```

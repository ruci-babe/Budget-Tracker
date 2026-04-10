# Expense Tracker - Linux Installation

## Quick Start

```bash
chmod +x install.sh
./install.sh
```

Then search for "Expense Tracker" in your applications menu, or run:

```bash
source .venv/bin/activate
python3 desktop_app.py
```

## Features
- **GTK Integration**: Automatically matches your system's light/dark theme
- **GNOME Application Menu**: Launch directly from Pop!_OS Applications
- **Native Icon**: Custom poop emoji icon in your app drawer
- **Tesseract OCR**: Built-in receipt scanning

## Installation Details

The installer will:
1. ✅ Install system dependencies (Python, Tesseract, tkinter)
2. ✅ Create a Python virtual environment
3. ✅ Install Python packages
4. ✅ Create a desktop launcher file
5. ✅ Install custom application icon
6. ✅ Update application menu database

## Building Standalone Binary

To create a distributable Linux executable:

```bash
./build.sh
```

The resulting app will be available at `dist/desktop_app`.

## Troubleshooting

### "permission denied" error
```bash
chmod +x install.sh
```

### Tesseract not found
```bash
sudo apt install tesseract-ocr libtesseract-dev
```

### App not appearing in menu
```bash
update-desktop-database ~/.local/share/applications
```

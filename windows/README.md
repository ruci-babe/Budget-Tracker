# Expense Tracker - Windows Installation

## Quick Start

Double-click `install.bat` and follow the prompts.

```
install.bat
```

Then search for "Expense Tracker" in the Start Menu, or run from Command Prompt:

```cmd
.venv\Scripts\python.exe desktop_app.py
```

## Prerequisites

### Python 3.8+
- Download from https://www.python.org/downloads/
- **IMPORTANT**: Check "Add Python to PATH" during installation
- Verify installation:
  ```cmd
  python --version
  ```

### Tesseract OCR (Optional but recommended)
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Install and add to PATH
- Enables receipt scanning with OCR

## Installation Details

The installer will:
1. ✅ Check for Python installation
2. ✅ Create a Python virtual environment
3. ✅ Install Python packages
4. ✅ Create a Start Menu shortcut
5. ✅ Install the custom application icon

## Troubleshooting

### "Python is not recognized"
1. Download Python from https://www.python.org/downloads/
2. During installation, **check "Add Python to PATH"**
3. Restart Command Prompt and try again

### "cannot find PIL or pytesseract"
```cmd
.venv\Scripts\python.exe -m pip install pillow pytesseract
```

### App won't start
1. Open Command Prompt in this folder
2. Run:
   ```cmd
   .venv\Scripts\python.exe desktop_app.py
   ```
3. Check the error message

## Building Standalone Executable

To create a .exe file for distribution:

```cmd
build_windows.bat
```

The .exe will be in `dist\desktop_app.exe`.

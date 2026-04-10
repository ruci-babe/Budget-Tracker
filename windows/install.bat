@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo === Expense Tracker Windows Installer ===
echo.

REM Check if Python is installed
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ERROR: Python 3.8+ is required but not installed.
    echo Please download Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo Installing required system packages...
echo Python found: 
python --version

REM Check if Tesseract is installed
where tesseract >nul 2>&1
if !errorlevel! neq 0 (
    echo.
    echo WARNING: Tesseract OCR is not found in PATH.
    echo To enable OCR features, please download and install Tesseract from:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo You can continue without OCR, but receipt scanning won't work.
    choice /C YN /M "Continue installation without Tesseract?"
    if !errorlevel! equ 2 (
        exit /b 1
    )
) else (
    echo Tesseract OCR found.
)

REM Create virtual environment
if not exist ".venv" (
    echo Creating Python virtual environment...
    python -m venv .venv
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install Python dependencies
echo Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install --extra-index-url https://PySimpleGUI.net/install -r requirements.txt
python -m pip install --force-reinstall --extra-index-url https://PySimpleGUI.net/install PySimpleGUI

REM Create Start Menu shortcut
echo Installing Start Menu shortcut...
powershell -Command "Start-Process -Verb runas -FilePath 'powershell' -ArgumentList 'Add-Type -AssemblyName System.Windows.Forms; $WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut(\"%ProgramData%\Microsoft\Windows\Start Menu\Programs\Expense Tracker.lnk\"); $Shortcut.TargetPath = \"%CD%\.venv\Scripts\pythonw.exe\"; $Shortcut.Arguments = \"%CD%\desktop_app.py\"; $Shortcut.WorkingDirectory = \"%CD%\"; $Shortcut.IconLocation = \"%CD%\expense-tracker.ico\"; $Shortcut.Save()'" >nul 2>&1

if exist "%ProgramData%\Microsoft\Windows\Start Menu\Programs\Expense Tracker.lnk" (
    echo ✓ Start Menu shortcut created
) else (
    echo Note: Could not create Start Menu shortcut (requires admin). You can find the app in this folder.
)

echo.
echo ===================================
echo Installation complete!
echo ===================================
echo.
echo To launch the app:
echo 1. Double-click desktop_app.py in this folder, or
echo 2. Search for "Expense Tracker" in the Start Menu, or
echo 3. Run from command line:
echo    .venv\Scripts\python.exe desktop_app.py
echo.
pause

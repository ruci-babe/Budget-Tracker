# Expense Tracker

A simple expense tracker with uploads for monthly statements, receipts, and screenshots. It uses OCR for images/PDFs and automatically categorizes transactions.

## Features
- Upload CSV, PDF, JPG, PNG, or TIFF files
- Auto-extract transaction date, amount, and description
- Automatic category suggestions with editable values
- Monthly summary totals for money in and money spent
- Category breakdown chart
- Recurring transaction detection after 3 or more repeats
- Editable transaction list for manual correction
- Local persistence so transactions stay saved between sessions
- Date-range, category, and search filters
- Category manager for custom categories
- OCR preview for image/PDF text extraction

## Setup
1. Use the installer script (recommended):

```bash
./install.sh
```

To install and launch the app immediately:

```bash
./install.sh --run
```

This installs system dependencies, creates the virtual environment, installs Python packages, and then starts the app.

If you prefer to do it manually, use:

```bash
python -m pip install --upgrade pip
python -m pip install --extra-index-url https://PySimpleGUI.net/install -r requirements.txt
```

If PySimpleGUI still fails, run:

```bash
python -m pip install --force-reinstall --extra-index-url https://PySimpleGUI.net/install PySimpleGUI
```

2. Install Tesseract OCR and tkinter:

- On Linux:

```bash
sudo apt update
sudo apt install python3-tk tesseract-ocr libtesseract-dev
```

- On Windows:

Install Tesseract from the official installer and make sure the install path is added to your PATH.

3. Run the desktop application:

```bash
python desktop_app.py
```

4. Optional: run the Streamlit version:

```bash
streamlit run app.py
```

## Packaging for Windows

To build a standalone Windows executable from a Windows machine:

```bash
pyinstaller --onefile --windowed desktop_app.py
```

## Packaging on Linux

To build a standalone Linux executable from this repository:

```bash
./build.sh
```

The resulting app will be available at `dist/desktop_app`.

> Note: OCR still requires the Tesseract engine binary installed separately unless you bundle it explicitly.

## Usage
- Use the Browse button to select one or more CSV, PDF, or image files.
- Use OCR Preview to review extracted text from receipts and PDFs.
- The app automatically extracts transactions and categorizes them.
- Add cash spending manually with reason, category, vendor, and date fields.
- Link an email address, configure IMAP, and fetch receipt emails directly.
- Scan a folder of exported email receipts if you prefer local files.
- Apply filters by date range, category, or search terms.
- Edit the selected transaction details using the fields on the right.
- Add custom categories in the Category Manager.
- Transactions are saved locally and reloaded automatically.
- Recurring transactions are flagged after the same description appears at least 3 times.

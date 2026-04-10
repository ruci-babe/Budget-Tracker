# Expense Tracker 💩

A multi-platform expense tracking application with mobile sync capabilities. Track receipts, scan emails, and manage spending across desktop (Linux, macOS, Windows) and mobile (Android) devices.

## ✨ Features

- 📱 **Multi-Platform**: Desktop (Linux, macOS, Windows) + Android mobile
- 🔄 **Cloud Sync**: Sync expenses between devices in real-time
- 📸 **Receipt Scanning**: OCR-powered receipt and email parsing
- 🏷️ **Smart Categorization**: Automatic expense categorization with manual override
- 📊 **Analytics**: Monthly summaries, category breakdowns, recurring expenses
- 💾 **Offline Support**: Works offline, syncs when connected
- 🎨 **Dark Mode**: Automatic light/dark theme detection on desktop
- 🔐 **Secure**: JWT authentication, encrypted passwords

## 📦 Project Structure

```
Budget-Tracker/
├── linux/                 # 🐧 Linux Desktop App (Pop!_OS optimized)
├── windows/              # 🪟 Windows Desktop App
├── macos/               # 🍎 macOS Desktop App
├── android/             # 📱 Android Mobile App
├── backend/             # 🔗 Sync API Server
├── app.py               # Streamlit web version (optional)
├── requirements.txt     # Desktop dependencies
└── docs/               # Documentation
```

## 🚀 Quick Start

Choose your platform and follow the installation guide:

### Linux (Pop!_OS/Ubuntu)
```bash
cd linux
chmod +x install.sh
./install.sh
```
Then search for "Expense Tracker" in your applications menu.

**Features:**
- ✅ GTK integration with automatic theme detection
- ✅ Native application menu icon
- ✅ Tesseract OCR for receipt scanning

### Windows
```bash
cd windows
install.bat
```
Then search for "Expense Tracker" in Start Menu or double-click `desktop_app.py`

**Features:**
- ✅ Start Menu integration
- ✅ Easy Python setup with dependency checker
- ✅ Tesseract OCR support (optional)

### macOS
```bash
cd macos
chmod +x install.sh
./install.sh
```
Then open "Expense Tracker" from Applications folder.

**Features:**
- ✅ Native app bundle
- ✅ Dark mode support
- ✅ Automatic Homebrew dependency installation
- ✅ Tesseract via Homebrew

### Android (Coming Soon)
See `android/README.md` for development setup.

**Features:**
- 📱 Add expenses on the go
- 📸 Capture receipts with camera
- 🔄 Auto-sync with desktop
- 🏷️ Quick expense categorization

## 🔗 Backend Sync Server

The backend API enables syncing between devices. See `backend/README.md` for:
- Installation and deployment
- API documentation
- Docker setup
- Security considerations

Quick start:
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
python -c "from app import init_db; init_db()"
python app.py
```

## 📱 Features Overview

### Desktop Application
- Upload CSV, PDF, JPG, PNG, or TIFF files
- Auto-extract transaction date, amount, and description
- Automatic category suggestions with manual override
- Monthly summary totals for income and expenses
- Category breakdown chart
- Recurring transaction detection (3+ repeats)
- Editable transaction list
- Local persistence (no account required initially)
- Date-range, category, and search filters
- Manage custom categories
- OCR preview for image/PDF text extraction
- Email receipt integration (IMAP fetch & folder scan)
- Theme-aware UI (light/dark mode on Pop!_OS)
- Desktop icon in applications menu

### Mobile App (Android - In Development)
- Add expenses with photos
- Real-time sync with desktop
- Offline expense storage
- Quick categorization
- View spending summaries
- Receipt capture with OCR
- Synced categories from desktop

## 🔄 Sync Workflow

1. **Desktop First**: Create/manage expenses on desktop, app stores locally
2. **Optional Sync**: Link account to sync with other devices
3. **Mobile Add**: Add expenses on Android app while out
4. **Auto-Sync**: Desktop automatically pulls new expenses when online
5. **Conflict Resolution**: Last-write-wins strategy for simultaneous edits

## 🛠️ Tech Stack

### Desktop (All Platforms)
- Python 3.8+
- PySimpleGUI (cross-platform GUI)
- Pandas (data processing)
- Tesseract OCR (receipt scanning)
- PyPDF, Pillow (file processing)

### Backend
- Flask (API server)
- SQLAlchemy (ORM)
- PostgreSQL/SQLite (database)
- JWT (authentication)

### Mobile (Android)
- Kotlin
- Jetpack Compose (UI)
- Room (local database)
- Retrofit (API client)
- Hilt (dependency injection)

## 📋 Installation Details per Platform

For detailed setup instructions and troubleshooting, see:
- [Linux Setup](linux/README.md)
- [Windows Setup](windows/README.md)
- [macOS Setup](macos/README.md)
- [Backend Setup](backend/README.md)
- [Android Setup](android/README.md)

## 🔐 Offline & Sync

The app works great standalone:
- ✅ No account required to use desktop app
- ✅ All data stored locally
- ✅ OCR works on your machine
- ✅ Email scanning local files

To enable device sync:
1. Start backend server (or use cloud deployment)
2. Create account in desktop app settings
3. Register your devices
4. Enable sync - now all your devices stay updated!

## 🐛 Building Standalone Executables

### Linux
```bash
cd linux
./build.sh
# Output: dist/desktop_app
```

### Windows
```bash
cd windows
.venv\Scripts\pyinstaller --onefile --windowed desktop_app.py
# Output: dist\desktop_app.exe
```

### macOS
```bash
cd macos
pip install py2app
python setup.py py2app
# Output: dist/Expense Tracker.app
```

## 📚 Documentation

- [Backend API Docs](backend/README.md)
- [Linux Installation](linux/README.md)
- [Windows Installation](windows/README.md)
- [macOS Installation](macos/README.md)
- [Android App](android/README.md)

## 🤝 Contributing

Contributions welcome! Areas of focus:
- Android app development
- Backend improvements
- UI/UX enhancements
- Test coverage
- Documentation

## 📄 License

See LICENSE file

## 🎯 Roadmap

- ✅ Multi-platform desktop support (Linux, Windows, macOS)
- ✅ Backend sync infrastructure
- 🚧 Android mobile app
- 📋 iOS mobile app
- 📋 Web dashboard
- 📋 Advanced reporting
- 📋 Budget alerts & notifications
- 📋 Recurring transaction templates
- 📋 Family/shared budgets

---

**Icon**: 💩 "Because everyone poops money away on random things!"

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

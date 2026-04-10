import json
import os
import platform
from pathlib import Path

import pandas as pd
import PySimpleGUI as sg

from utils import (
    CATEGORY_KEYWORDS,
    DEFAULT_CATEGORIES,
    EMAIL_CONFIG_FILE,
    add_duplicate_pattern,
    dedupe_transactions,
    extract_raw_text_from_path,
    extract_transactions_from_email_file,
    fetch_email_receipts,
    find_recurring,
    load_category_names,
    load_duplicate_patterns,
    load_email_config,
    load_transactions_from_file,
    prepare_transactions,
    save_category_names,
    save_duplicate_patterns,
    save_email_config,
    summarize_month,
    category_breakdown,
)

DATA_DIR = Path.home() / ".expense_tracker"
STORAGE_FILE = DATA_DIR / "transactions.csv"
HEADERS = ["Date", "Description", "Amount", "Category", "Vendor", "PaymentMethod", "Recurring", "Duplicate"]


def detect_system_theme():
    """
    Detect system theme preference (light/dark mode).
    Supports Linux (GNOME/D-Bus), with fallback to light theme.
    """
    try:
        if platform.system() == "Linux":
            import subprocess
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "gtk-application-prefer-dark-theme"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0 and "true" in result.stdout.lower():
                return "dark"
    except Exception:
        pass
    return "light"


def apply_theme(theme_mode: str = None):
    """
    Apply appropriate GTK-integrated theme based on system preferences.
    Pop!_OS uses GNOME, so this integrates with the system theme.
    """
    if theme_mode is None:
        theme_mode = detect_system_theme()
    
    if theme_mode == "dark":
        sg.theme("DarkGray13")
        color_scheme = {
            "primary": "#E8E8E8",
            "accent": "#4A9EFF",
            "success": "#2ECC71",
            "danger": "#E74C3C",
            "warning": "#F39C12",
            "text": "#FFFFFF",
            "bg_light": "#2B2B2B",
        }
    else:
        sg.theme("LightGrey1")
        color_scheme = {
            "primary": "#333333",
            "accent": "#2E86DE",
            "success": "#28A745",
            "danger": "#C0392B",
            "warning": "#1F618D",
            "text": "#555555",
            "bg_light": "#F8F9F9",
        }
    return color_scheme


def format_money(amount):
    return f"${amount:,.2f}"


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_persisted_transactions():
    if STORAGE_FILE.exists():
        df = pd.read_csv(
            STORAGE_FILE,
            parse_dates=["Date"],
            dtype={"Description": str, "Amount": float, "Category": str, "Vendor": str, "PaymentMethod": str, "Recurring": bool, "Duplicate": bool},
        )
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
        for column in HEADERS:
            if column not in df.columns:
                if column in {"Recurring", "Duplicate"}:
                    df[column] = False
                else:
                    df[column] = ""
        df["PaymentMethod"] = df["PaymentMethod"].fillna("Imported")
        df["Recurring"] = df["Recurring"].fillna(False).astype(bool)
        df["Duplicate"] = df["Duplicate"].fillna(False).astype(bool)
        return df[HEADERS].fillna("")
    return pd.DataFrame(columns=HEADERS)


def save_persisted_transactions(df: pd.DataFrame):
    ensure_data_dir()
    df.to_csv(STORAGE_FILE, index=False)


def filter_transactions(df: pd.DataFrame, start_date, end_date, category, search):
    filtered = df.copy()
    if start_date:
        filtered = filtered[filtered["Date"].notna() & (filtered["Date"] >= start_date)]
    if end_date:
        filtered = filtered[filtered["Date"].notna() & (filtered["Date"] <= end_date)]
    if category and category != "All":
        filtered = filtered[filtered["Category"] == category]
    if search:
        mask = filtered["Description"].astype(str).str.contains(search, case=False, na=False) | filtered["Vendor"].astype(str).str.contains(search, case=False, na=False)
        filtered = filtered[mask]
    return filtered


def build_table_data(df: pd.DataFrame):
    if df.empty:
        return []
    return df.fillna("").astype(str)[HEADERS].values.tolist()


def build_breakdown_text(df: pd.DataFrame):
    breakdown = category_breakdown(df)
    if breakdown.empty:
        return "No category data available."
    lines = [f"{row.Category}: {format_money(row.Amount)}" for row in breakdown.itertuples()]
    return "\n".join(lines)


def build_table_row_colors(df: pd.DataFrame):
    colors = []
    for i, row in df.reset_index(drop=True).iterrows():
        if bool(row.get("Duplicate", False)):
            colors.append((i, "#FADBD8"))
        elif row.get("Amount") is not None:
            try:
                amount = float(row["Amount"])
                if amount < 0:
                    colors.append((i, "#FCF3CF"))
                elif amount > 0:
                    colors.append((i, "#D5F5E3"))
                else:
                    colors.append((i, "#EBF5FB"))
            except Exception:
                colors.append((i, "#EBF5FB"))
        else:
            colors.append((i, "#EBF5FB"))
    return colors


def update_ui(window: sg.Window, all_df: pd.DataFrame, filtered_df: pd.DataFrame):
    summary = summarize_month(filtered_df)
    window["-COUNT-"].update(f"Transactions found: {len(filtered_df)} / {len(all_df)}")
    window["-INCOME-"].update(format_money(summary["income"]))
    window["-SPENT-"].update(format_money(summary["spending"]))
    window["-NET-"].update(format_money(summary["net"]))
    window["-TABLE-"].update(values=build_table_data(filtered_df), row_colors=build_table_row_colors(filtered_df))
    window["-BREAKDOWN-"].update(build_breakdown_text(filtered_df))
    recurring = all_df[all_df["Recurring"] == True]
    if recurring.empty:
        window["-RECURRING-"].update("No recurring transactions detected yet.")
    else:
        lines = [f"{row.Date} | {row.Description} | {format_money(row.Amount)}" for row in recurring.itertuples()]
        window["-RECURRING-"].update("\n".join(lines))


def parse_date_input(text: str):
    try:
        parsed = pd.to_datetime(text, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.date()
    except Exception:
        return None


def load_categories():
    categories = load_category_names()
    for category in DEFAULT_CATEGORIES:
        if category not in categories:
            categories.append(category)
    return ["All"] + sorted(set(categories), key=str.casefold)


def update_category_controls(window: sg.Window, categories):
    window["-FILTER_CATEGORY-"].update(values=categories, value="All")
    window["-CATEGORY_DROPDOWN-"].update(values=categories[1:], value=categories[1] if len(categories) > 1 else "")
    window["-CASH_CATEGORY-"].update(values=categories[1:], value=categories[1] if len(categories) > 1 else "")
    window["-CATEGORY_LIST-"].update(values=categories[1:])


def show_ocr_preview(paths):
    preview_texts = []
    for path in paths:
        content = extract_raw_text_from_path(path)
        preview_texts.append(f"=== {Path(path).name} ===\n{content[:1000]}\n")
    sg.popup_scrolled("OCR / Text Preview", "\n".join(preview_texts), size=(100, 30))


def scan_email_receipts(folder: str, email_address: str):
    transactions = []
    if not folder or not email_address:
        return transactions
    for path in Path(folder).rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".eml", ".txt", ".html", ".htm", ".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}:
            extracted = extract_transactions_from_email_file(str(path), email_address)
            for tx in extracted:
                tx["PaymentMethod"] = "Email"
                transactions.append(tx)
    return transactions


def main():
    color_scheme = apply_theme()
    ensure_data_dir()
    transactions = load_persisted_transactions()
    duplicate_patterns = load_duplicate_patterns()
    categories = load_categories()
    filtered = transactions.copy()

    email_config = load_email_config()
    linked_email = email_config.get("email", "")
    receipt_folder = email_config.get("receipt_folder", "")

    header = [
        [
            sg.Text("Expense Tracker", font=("Segoe UI", 24, "bold"), pad=((0, 0), (0, 5))),
        ],
        [
            sg.Text(
                "Track receipts, scan emails, and manage spending with a simple, friendly interface.",
                font=("Segoe UI", 11),
                text_color="#555555",
            )
        ],
        [
            sg.Text(
                "Tip: start by loading receipts or email exports, then review, categorize, and save your data.",
                font=("Segoe UI", 10),
                text_color="#1F618D",
            )
        ],
    ]

    file_controls = [
        sg.Input(key="-FILEPATH-", enable_events=True, visible=False),
        sg.FilesBrowse(
            button_text="Browse Files",
            target="-FILEPATH-",
            file_types=(
                ("Supported files", "*.csv;*.pdf;*.png;*.jpg;*.jpeg;*.tiff;*.bmp"),
            ),
            size=(12, 1),
            button_color=("white", "#2E86DE"),
        ),
        sg.Button("Load Files", key="-LOAD-", size=(12, 1), button_color=("white", "#28A745")),
        sg.Button("OCR Preview", key="-SHOW_OCR-", size=(12, 1)),
        sg.Button("Save CSV", key="-SAVE-", size=(10, 1)),
        sg.Button("Clear Data", key="-CLEAR-", size=(10, 1)),
        sg.Button("Exit", size=(10, 1), button_color=("white", "#C0392B")),
    ]

    email_frame = [
        [sg.Text("Linked Email:"), sg.Input(key="-LINKED_EMAIL-", size=(26, 1), default_text=linked_email)],
        [sg.Button("Link Email", key="-LINK_EMAIL-", size=(12, 1)), sg.Button("Gmail", key="-PRESET_GMAIL-", size=(10, 1)), sg.Button("Outlook", key="-PRESET_OUTLOOK-", size=(10, 1))],
        [sg.Text("IMAP Server:"), sg.Input(key="-IMAP_SERVER-", size=(24, 1), default_text=email_config.get("imap_server", "")), sg.Text("Port:"), sg.Input(key="-IMAP_PORT-", size=(6, 1), default_text=str(email_config.get("imap_port", 993)))],
        [sg.Text("Password:"), sg.Input(key="-EMAIL_PASSWORD-", password_char="*", size=(30, 1))],
        [sg.Text("From:"), sg.Input(key="-IMAP_FROM-", size=(20, 1)), sg.Text("Subject:"), sg.Input(key="-IMAP_SUBJECT-", size=(18, 1))],
        [sg.Text("Since:"), sg.Input(key="-IMAP_SINCE-", size=(12, 1), tooltip="YYYY-MM-DD")],
        [sg.Text("Saved export folder:"), sg.Input(key="-EMAIL_FOLDER-", size=(33, 1), default_text=receipt_folder), sg.FolderBrowse("Browse", target="-EMAIL_FOLDER-")],
        [sg.Button("Scan Email Receipts", key="-SCAN_EMAIL-", size=(18, 1)), sg.Button("Fetch IMAP Receipts", key="-FETCH_IMAP-", size=(18, 1))],
    ]

    filter_frame = [
        [sg.Text("Date from:"), sg.Input(key="-FILTER_FROM-", size=(12, 1), tooltip="YYYY-MM-DD"), sg.Text("to:"), sg.Input(key="-FILTER_TO-", size=(12, 1), tooltip="YYYY-MM-DD")],
        [sg.Text("Category:"), sg.Combo(categories, default_value="All", key="-FILTER_CATEGORY-", readonly=True, size=(18, 1)), sg.Text("Search:"), sg.Input(key="-FILTER_SEARCH-", size=(24, 1))],
        [sg.Button("Apply Filters", key="-APPLY_FILTERS-", size=(12, 1)), sg.Button("Clear Filters", key="-CLEAR_FILTERS-", size=(12, 1))],
    ]

    left_column = [
        [sg.Frame("Import Receipts", [file_controls], title_color="#2E86DE")],
        [sg.Frame("Email Receipt Import", email_frame, title_color="#2E86DE")],
        [sg.Frame("Search & Filters", filter_frame, title_color="#2E86DE")],
        [
            sg.Frame(
                "Transactions",
                [
                    [
                        sg.Table(
                            values=[],
                            headings=HEADERS,
                            auto_size_columns=False,
                            col_widths=[12, 30, 12, 14, 16, 14, 12, 12],
                            display_row_numbers=False,
                            justification="left",
                            num_rows=18,
                            row_height=24,
                            alternating_row_color="#F8F9F9",
                            key="-TABLE-",
                            enable_events=True,
                            expand_x=True,
                            expand_y=True,
                            select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                            tooltip="Click a row to edit details on the right.",
                        )
                    ]
                ],
                expand_x=True,
                expand_y=True,
                title_color="#2E86DE",
            )
        ],
    ]

    right_column = [
        [
            sg.Frame(
                "At a Glance",
                [
                    [sg.Text("Money In", size=(14, 1)), sg.Text("$0.00", key="-INCOME-", font=("Segoe UI", 12, "bold"), text_color="#117A65")],
                    [sg.Text("Money Spent", size=(14, 1)), sg.Text("$0.00", key="-SPENT-", font=("Segoe UI", 12, "bold"), text_color="#C0392B")],
                    [sg.Text("Net Change", size=(14, 1)), sg.Text("$0.00", key="-NET-", font=("Segoe UI", 12, "bold"), text_color="#1F618D")],
                    [sg.Text("Transactions"), sg.Text("0 / 0", key="-COUNT-", font=("Segoe UI", 10), text_color="#555555")],
                ],
                element_justification="left",
                pad=((10, 10), (10, 10)),
                title_color="#2E86DE",
            )
        ],
        [
            sg.Frame(
                "Quick Start",
                [
                    [sg.Text("📁 Browse your receipts or statements." , font=("Segoe UI", 10))],
                    [sg.Text("✏️ Select a transaction to edit category, vendor, or amount.", font=("Segoe UI", 10))],
                    [sg.Text("🔎 Use filters to focus on dates, categories, and searches.", font=("Segoe UI", 10))],
                ],
                element_justification="left",
                pad=((10, 10), (10, 10)),
                title_color="#2E86DE",
            )
        ],
        [
            sg.Frame(
                "How it Works",
                [
                    [sg.Text("• Import receipts from files or email receipts.", font=("Segoe UI", 10))],
                    [sg.Text("• AI-style suggestions categorize expenses automatically.", font=("Segoe UI", 10))],
                    [sg.Text("• Save your data and export a CSV summary.", font=("Segoe UI", 10))],
                ],
                element_justification="left",
                pad=((10, 10), (10, 10)),
                title_color="#2E86DE",
            )
        ],
        [
            sg.Frame(
                "Selected Transaction",
                [
                    [sg.Text("Date", size=(10, 1)), sg.Input(key="-DATE-", size=(26, 1))],
                    [sg.Text("Amount", size=(10, 1)), sg.Input(key="-AMOUNT-", size=(26, 1))],
                    [sg.Text("Category", size=(10, 1)), sg.Combo(categories[1:], key="-CATEGORY_DROPDOWN-", size=(24, 1))],
                    [sg.Text("Vendor", size=(10, 1)), sg.Input(key="-VENDOR-", size=(26, 1))],
                    [sg.Text("Description", size=(10, 1))],
                    [sg.Multiline(key="-DESCRIPTION-", size=(38, 6))],
                    [sg.Checkbox("Duplicate", key="-DUPLICATE_CHECK-", enable_events=False), sg.Button("Mark Duplicate", key="-MARK_DUPLICATE-", button_color=("white", "#A93226"))],
                    [sg.Button("Save Changes", key="-SAVE_EDIT-", size=(20, 1), button_color=("white", "#2E86DE"))],
                ],
                expand_y=True,
                title_color="#2E86DE",
            )
        ],
        [
            sg.Frame(
                "Quick Add",
                [
                    [sg.Text("Date", size=(9, 1)), sg.Input(key="-CASH_DATE-", size=(22, 1), tooltip="YYYY-MM-DD")],
                    [sg.Text("Amount", size=(9, 1)), sg.Input(key="-CASH_AMOUNT-", size=(22, 1))],
                    [sg.Text("Category", size=(9, 1)), sg.Combo(categories[1:], key="-CASH_CATEGORY-", size=(20, 1), readonly=True)],
                    [sg.Text("Reason", size=(9, 1)), sg.Input(key="-CASH_REASON-", size=(36, 1))],
                    [sg.Text("Vendor", size=(9, 1)), sg.Input(key="-CASH_VENDOR-", size=(36, 1))],
                    [sg.Button("Add Cash Expense", key="-ADD_CASH-", size=(20, 1), button_color=("white", "#28A745"))],
                ],
                title_color="#2E86DE",
            )
        ],
        [
            sg.Frame(
                "Categories",
                [
                    [sg.Listbox(values=categories[1:], size=(30, 8), key="-CATEGORY_LIST-", enable_events=True)],
                    [sg.Input(key="-NEW_CATEGORY-", size=(22, 1)), sg.Button("Add Category", key="-ADD_CATEGORY-")],
                    [sg.Button("Remove Selected", key="-REMOVE_CATEGORY-")],
                ],
                expand_y=True,
                title_color="#2E86DE",
            )
        ],
        [
            sg.Frame(
                "Insights",
                [
                    [sg.Text("Category Breakdown", font=("Segoe UI", 10, "bold"))],
                    [sg.Multiline(key="-BREAKDOWN-", size=(45, 7), disabled=True, autoscroll=True)],
                    [sg.Text("Recurring Transactions", font=("Segoe UI", 10, "bold"))],
                    [sg.Multiline(key="-RECURRING-", size=(45, 7), disabled=True, autoscroll=True)],
                ],
                title_color="#2E86DE",
                expand_x=True,
            )
        ],
    ]

    layout = [
        [sg.Column(header, expand_x=True)],
        [
            sg.Column([[sg.Frame("Import & Email", left_column, element_justification="left", expand_x=True, expand_y=True, title_color="#2E86DE")]], expand_x=True, expand_y=True),
        ],
        [sg.Column(right_column, expand_x=True, expand_y=True)],
        [sg.HorizontalSeparator()],
        [
            sg.Text("Status:", pad=((0, 5), (5, 0))),
            sg.Text(
                "Ready to import receipts or connect your email for automatic receipt scanning.",
                key="-STATUS-",
                size=(90, 1),
                text_color="#205081",
                background_color="#FEF9E7",
                pad=((5, 0), (5, 0)),
            ),
        ],
    ]

    window = sg.Window("Expense Tracker", layout, resizable=True, finalize=True, size=(1180, 860))
    filtered = filter_transactions(transactions, None, None, "All", "")
    update_ui(window, transactions, filtered)
    selected_index = None

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Exit"):
            break

        if event == "-LOAD-":
            file_paths = values["-FILEPATH-"]
            if not file_paths:
                sg.popup("Please select one or more files to load.")
                continue
            paths = [p.strip() for p in file_paths.split(";") if p.strip()]
            new_transactions = []
            for path in paths:
                if os.path.isfile(path):
                    new_transactions.extend(load_transactions_from_file(path))
            if not new_transactions:
                sg.popup("No transactions were detected in the selected files.")
                continue
            loaded_df = prepare_transactions(new_transactions)
            transactions = pd.concat([transactions, loaded_df], ignore_index=True)
            transactions = find_recurring(transactions)
            filtered = filter_transactions(transactions, parse_date_input(values["-FILTER_FROM-"]), parse_date_input(values["-FILTER_TO-"]), values["-FILTER_CATEGORY-"], values["-FILTER_SEARCH-"])
            update_ui(window, transactions, filtered)
            save_persisted_transactions(transactions)
            window["-STATUS-"].update(f"Loaded {len(new_transactions)} transactions from files.")
            sg.popup(f"Loaded {len(new_transactions)} transactions.")

        if event == "-SHOW_OCR-":
            file_paths = values["-FILEPATH-"]
            if not file_paths:
                sg.popup("Select files first to see OCR preview.")
                continue
            paths = [p.strip() for p in file_paths.split(";") if p.strip()]
            show_ocr_preview(paths)

        if event == "-PRESET_GMAIL-":
            window["-IMAP_SERVER-"].update("imap.gmail.com")
            window["-IMAP_PORT-"].update("993")
            continue

        if event == "-PRESET_OUTLOOK-":
            window["-IMAP_SERVER-"].update("outlook.office365.com")
            window["-IMAP_PORT-"].update("993")
            continue

        if event == "-LINK_EMAIL-":
            email_address = values["-LINKED_EMAIL-"].strip()
            imap_server = values["-IMAP_SERVER-"].strip()
            try:
                imap_port = int(values["-IMAP_PORT-"])
            except Exception:
                imap_port = 993
            receipt_folder = values["-EMAIL_FOLDER-"].strip()
            if not email_address or "@" not in email_address:
                sg.popup("Enter a valid email address before linking.")
                continue
            if not imap_server:
                sg.popup("Enter your IMAP server before linking.")
                continue
            if receipt_folder and not Path(receipt_folder).is_dir():
                sg.popup("Enter a valid receipt folder path or leave it blank.")
                continue
            save_email_config(email_address, imap_server, imap_port, receipt_folder)
            sg.popup(f"Email linked: {email_address}")

        if event == "-SCAN_EMAIL-":
            email_address = values["-LINKED_EMAIL-"].strip()
            receipt_folder = values["-EMAIL_FOLDER-"].strip()
            try:
                imap_port = int(values["-IMAP_PORT-"])
            except Exception:
                imap_port = 993
            if not email_address or "@" not in email_address:
                sg.popup("Enter a valid linked email address before scanning receipts.")
                continue
            if not receipt_folder or not Path(receipt_folder).is_dir():
                sg.popup("Select a valid folder containing exported email receipts.")
                continue
            scanned = scan_email_receipts(receipt_folder, email_address)
            if not scanned:
                sg.popup("No receipt transactions were found in that folder.")
                continue
            loaded_df = prepare_transactions(scanned)
            loaded_df, duplicates_removed = dedupe_transactions(loaded_df, transactions, duplicate_patterns)
            transactions = pd.concat([transactions, loaded_df], ignore_index=True)
            transactions = transactions.drop_duplicates(subset=["Date", "Description", "Amount", "Category", "Vendor", "PaymentMethod"], keep="first")
            transactions = find_recurring(transactions)
            filtered = filter_transactions(
                transactions,
                parse_date_input(values["-FILTER_FROM-"] ),
                parse_date_input(values["-FILTER_TO-"] ),
                values["-FILTER_CATEGORY-"],
                values["-FILTER_SEARCH-"] or "",
            )
            update_ui(window, transactions, filtered)
            save_persisted_transactions(transactions)
            save_email_config(email_address, values["-IMAP_SERVER-"].strip(), imap_port, receipt_folder)
            window["-STATUS-"].update(f"Imported {len(loaded_df)} receipts from folder, skipped {duplicates_removed} duplicates.")
            sg.popup(f"Scanned and loaded {len(loaded_df)} transactions from email receipts. Skipped {duplicates_removed} duplicates.")

        if event == "-FETCH_IMAP-":
            email_address = values["-LINKED_EMAIL-"].strip()
            imap_server = values["-IMAP_SERVER-"].strip()
            try:
                imap_port = int(values["-IMAP_PORT-"])
            except Exception:
                imap_port = 993
            email_password = values["-EMAIL_PASSWORD-"].strip()
            if not email_address or "@" not in email_address:
                sg.popup("Enter a valid linked email address before fetching receipts.")
                continue
            if not imap_server:
                sg.popup("Enter your IMAP server before fetching receipts.")
                continue
            if not email_password:
                sg.popup("Enter your email password to fetch receipts.")
                continue
            fetched = fetch_email_receipts(
                imap_server,
                imap_port,
                email_address,
                email_password,
                sender=values["-IMAP_FROM-"].strip() or None,
                subject=values["-IMAP_SUBJECT-"].strip() or None,
                since=values["-IMAP_SINCE-"].strip() or None,
            )
            if not fetched:
                sg.popup("No receipts were found via IMAP or the login failed.")
                continue
            loaded_df = prepare_transactions(fetched)
            loaded_df, duplicates_removed = dedupe_transactions(loaded_df, transactions, duplicate_patterns)
            transactions = pd.concat([transactions, loaded_df], ignore_index=True)
            transactions = transactions.drop_duplicates(subset=["Date", "Description", "Amount", "Category", "Vendor", "PaymentMethod"], keep="first")
            transactions = find_recurring(transactions)
            filtered = filter_transactions(
                transactions,
                parse_date_input(values["-FILTER_FROM-"] ),
                parse_date_input(values["-FILTER_TO-"] ),
                values["-FILTER_CATEGORY-"],
                values["-FILTER_SEARCH-"] or "",
            )
            update_ui(window, transactions, filtered)
            save_persisted_transactions(transactions)
            save_email_config(email_address, imap_server, imap_port, values["-EMAIL_FOLDER-"].strip())
            window["-STATUS-"].update(f"Fetched {len(loaded_df)} IMAP receipts, skipped {duplicates_removed} duplicates.")
            sg.popup(f"Fetched and loaded {len(loaded_df)} transactions from IMAP receipts. Skipped {duplicates_removed} duplicates.")

        if event == "-ADD_CASH-":
            cash_date = parse_date_input(values["-CASH_DATE-"])
            try:
                cash_amount = float(values["-CASH_AMOUNT-"])
            except Exception:
                sg.popup("Enter a valid amount for the cash expense.")
                continue
            if cash_amount == 0:
                sg.popup("Enter a non-zero cash amount.")
                continue
            cash_amount = -abs(cash_amount)
            cash_category = values["-CASH_CATEGORY-"] or "Other"
            cash_reason = values["-CASH_REASON-"] or "Cash spending"
            cash_vendor = values["-CASH_VENDOR-"] or cash_reason
            new_tx = {
                "Date": cash_date,
                "Description": cash_reason,
                "Amount": cash_amount,
                "Category": cash_category,
                "Vendor": cash_vendor,
                "PaymentMethod": "Cash",
            }
            loaded_df = prepare_transactions([new_tx])
            transactions = pd.concat([transactions, loaded_df], ignore_index=True)
            transactions = find_recurring(transactions)
            filtered = filter_transactions(
                transactions,
                parse_date_input(values["-FILTER_FROM-"],),
                parse_date_input(values["-FILTER_TO-"],),
                values["-FILTER_CATEGORY-"],
                values["-FILTER_SEARCH-"] or "",
            )
            update_ui(window, transactions, filtered)
            save_persisted_transactions(transactions)
            window["-STATUS-"].update("Cash expense added.")
            sg.popup("Cash expense added.")

        if event == "-APPLY_FILTERS-":
            filtered = filter_transactions(
                transactions,
                parse_date_input(values["-FILTER_FROM-"]),
                parse_date_input(values["-FILTER_TO-"]),
                values["-FILTER_CATEGORY-"],
                values["-FILTER_SEARCH-"] or "",
            )
            update_ui(window, transactions, filtered)

        if event == "-CLEAR_FILTERS-":
            window["-FILTER_FROM-"].update("")
            window["-FILTER_TO-"].update("")
            window["-FILTER_CATEGORY-"].update("All")
            window["-FILTER_SEARCH-"].update("")
            filtered = transactions.copy()
            update_ui(window, transactions, filtered)
            window["-STATUS-"].update("Filters cleared. Showing all transactions.")

        if event == "-TABLE-" and values["-TABLE-"]:
            selected_index = values["-TABLE-"][0]
            row = filtered.iloc[selected_index]
            window["-DATE-"].update(row["Date"])
            window["-AMOUNT-"].update(row["Amount"])
            window["-CATEGORY_DROPDOWN-"].update(value=row["Category"])
            window["-VENDOR-"].update(row["Vendor"])
            window["-DESCRIPTION-"].update(row["Description"])
            window["-DUPLICATE_CHECK-"].update(bool(row.get("Duplicate", False)))

        if event == "-MARK_DUPLICATE-":
            if selected_index is None or selected_index >= len(filtered):
                sg.popup("Select a visible transaction row before marking a duplicate.")
                continue
            row_index = filtered.index[selected_index]
            transactions.at[row_index, "Duplicate"] = True
            duplicate_patterns = add_duplicate_pattern(transactions.loc[row_index], duplicate_patterns)
            save_duplicate_patterns(duplicate_patterns)
            window["-DUPLICATE_CHECK-"].update(True)
            filtered = filter_transactions(
                transactions,
                parse_date_input(values["-FILTER_FROM-"]),
                parse_date_input(values["-FILTER_TO-"]),
                values["-FILTER_CATEGORY-"],
                values["-FILTER_SEARCH-"] or "",
            )
            update_ui(window, transactions, filtered)
            save_persisted_transactions(transactions)
            sg.popup("Transaction marked as duplicate and learned for future deduplication.")

        if event == "-SAVE_EDIT-":
            if selected_index is None or selected_index >= len(filtered):
                sg.popup("Select a visible transaction row before saving edits.")
                continue
            row_date = parse_date_input(values["-DATE-"])
            try:
                amount = float(values["-AMOUNT-"])
            except Exception:
                amount = 0.0
            changed_category = values["-CATEGORY_DROPDOWN-"] or "Other"
            changed_description = values["-DESCRIPTION-"] or "Unknown"
            changed_vendor = values["-VENDOR-"] or changed_description
            changed_duplicate = bool(values["-DUPLICATE_CHECK-"])
            row_index = filtered.index[selected_index]
            transactions.at[row_index, "Date"] = row_date
            transactions.at[row_index, "Description"] = changed_description
            transactions.at[row_index, "Amount"] = amount
            transactions.at[row_index, "Category"] = changed_category
            transactions.at[row_index, "Vendor"] = changed_vendor
            transactions.at[row_index, "Duplicate"] = changed_duplicate
            if changed_duplicate:
                duplicate_patterns = add_duplicate_pattern(transactions.loc[row_index], duplicate_patterns)
                save_duplicate_patterns(duplicate_patterns)
            transactions = find_recurring(transactions)
            filtered = filter_transactions(
                transactions,
                parse_date_input(values["-FILTER_FROM-"]),
                parse_date_input(values["-FILTER_TO-"]),
                values["-FILTER_CATEGORY-"],
                values["-FILTER_SEARCH-"] or "",
            )
            update_ui(window, transactions, filtered)
            save_persisted_transactions(transactions)
            window["-STATUS-"].update("Transaction updated.")
            sg.popup("Transaction updated.")

        if event == "-SAVE-":
            save_path = sg.popup_get_file("Save transactions as CSV", save_as=True, file_types=(("CSV files", "*.csv"),), default_extension="csv")
            if save_path:
                transactions.to_csv(save_path, index=False)
                sg.popup(f"Saved transactions to {save_path}")

        if event == "-ADD_CATEGORY-":
            new_category = values["-NEW_CATEGORY-"].strip()
            if not new_category:
                sg.popup("Enter a category name before adding.")
                continue
            if new_category in categories:
                sg.popup("That category already exists.")
                continue
            categories.append(new_category)
            categories = ["All"] + sorted(set(categories) - {"All"}, key=str.casefold)
            save_category_names([c for c in categories if c != "All"])
            update_category_controls(window, categories)
            window["-NEW_CATEGORY-"].update("")

        if event == "-REMOVE_CATEGORY-":
            selected = values["-CATEGORY_LIST-"]
            if not selected:
                sg.popup("Select a category to remove.")
                continue
            category_to_remove = selected[0]
            if category_to_remove in DEFAULT_CATEGORIES:
                sg.popup("Default categories cannot be removed.")
                continue
            categories = [c for c in categories if c != category_to_remove]
            save_category_names([c for c in categories if c != "All"])
            update_category_controls(window, categories)

        if event == "-CLEAR-":
            if sg.popup_yes_no("Clear all saved transactions? This cannot be undone.") != "Yes":
                continue
            transactions = pd.DataFrame(columns=HEADERS)
            filtered = transactions.copy()
            selected_index = None
            update_ui(window, transactions, filtered)
            window["-DATE-"].update("")
            window["-AMOUNT-"].update("")
            window["-CATEGORY_DROPDOWN-"].update("")
            window["-VENDOR-"].update("")
            window["-DESCRIPTION-"].update("")
            save_persisted_transactions(transactions)
            window["-STATUS-"].update("Transactions have been cleared.")
            sg.popup("Transactions have been cleared.")

    save_persisted_transactions(transactions)
    save_category_names([c for c in categories if c != "All"])
    window.close()


if __name__ == "__main__":
    main()

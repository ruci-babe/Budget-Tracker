import email
import imaplib
import io
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from email import policy
from email.header import decode_header
from email.utils import parsedate_to_datetime
from pathlib import Path

import pandas as pd
import pytesseract
import pdfplumber
from PIL import Image

AMOUNT_RE = re.compile(r"(-?\$?\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d{2})?)")
DATE_RE = re.compile(r"(\d{1,4}[\/\-.]\d{1,2}[\/\-.]\d{2,4})")

CATEGORY_KEYWORDS = {
    "Groceries": ["supermarket", "grocery", "walmart", "costco", "aldi", "whole foods", "trader joe", "instacart"],
    "Utilities": ["electric", "water", "gas", "internet", "utility", "verizon", "at&t", "comcast", "spectrum"],
    "Rent": ["rent", "apartment", "landlord", "lease"],
    "Transport": ["uber", "lyft", "taxi", "gasoline", "shell", "chevron", "exxon", "metro", "bus", "train"],
    "Dining": ["restaurant", "cafe", "coffee", "starbucks", "mcdonald", "chipotle", "dunkin", "domino"],
    "Entertainment": ["netflix", "spotify", "hulu", "amazon prime", "movie", "cinema", "theater"],
    "Health": ["doctor", "pharmacy", "walgreens", "cvss", "urgent care", "clinic"],
    "Income": ["payroll", "salary", "deposit", "transfer", "refund", "income"],
    "Other": [],
}

CATEGORY_FILE = Path.home() / ".expense_tracker" / "categories.json"
EMAIL_CONFIG_FILE = Path.home() / ".expense_tracker" / "email_config.json"
DEFAULT_CATEGORIES = list(CATEGORY_KEYWORDS.keys())


def load_category_names(path: str | Path | None = None):
    path = Path(path or CATEGORY_FILE)
    if path.exists():
        try:
            categories = json.loads(path.read_text())
            if isinstance(categories, list):
                return list(dict.fromkeys([c for c in categories if isinstance(c, str)]))
        except Exception:
            pass
    return DEFAULT_CATEGORIES.copy()


DUPLICATE_PATTERNS_FILE = Path.home() / ".expense_tracker" / "duplicate_patterns.json"


def save_category_names(categories, path: str | Path | None = None):
    path = Path(path or CATEGORY_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(list(dict.fromkeys(categories)), indent=2))


def load_duplicate_patterns(path: str | Path | None = None):
    path = Path(path or DUPLICATE_PATTERNS_FILE)
    if path.exists():
        try:
            data = json.loads(path.read_text())
            if isinstance(data, list):
                return [item for item in data if isinstance(item, str)]
        except Exception:
            pass
    return []


def save_duplicate_patterns(patterns, path: str | Path | None = None):
    path = Path(path or DUPLICATE_PATTERNS_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(set(patterns)), indent=2))


def transaction_duplicate_keys(tx):
    date_value = tx.get("Date")
    if isinstance(date_value, str):
        date_value = parse_date(date_value)
    if not date_value:
        return []
    amount = tx.get("Amount")
    try:
        amount = round(float(amount), 2)
    except Exception:
        return []
    base = f"{date_value.isoformat()}|{amount}"
    keys = [base]
    description = normalize_text(str(tx.get("Description", "") or tx.get("Vendor", "")))
    if description:
        keys.append(f"{base}|{description}")
    return keys


def is_duplicate_transaction(tx, existing_keys, duplicate_patterns):
    for key in transaction_duplicate_keys(tx):
        if key in existing_keys or key in duplicate_patterns:
            return True
    return False


def dedupe_transactions(new_df, existing_df, duplicate_patterns):
    existing_keys = set()
    for _, row in existing_df.iterrows():
        existing_keys.update(transaction_duplicate_keys(row))
    filtered_rows = []
    duplicates_removed = 0
    seen = set()
    for _, row in new_df.iterrows():
        keys = transaction_duplicate_keys(row)
        if not keys:
            filtered_rows.append(row)
            continue
        if any(key in seen for key in keys) or any(key in existing_keys for key in keys) or any(key in duplicate_patterns for key in keys):
            duplicates_removed += 1
            continue
        seen.update(keys)
        filtered_rows.append(row)
    result = pd.DataFrame(filtered_rows)
    if result.empty:
        result = pd.DataFrame(columns=new_df.columns)
    return result, duplicates_removed


def add_duplicate_pattern(tx, patterns):
    patterns = set(patterns)
    for key in transaction_duplicate_keys(tx):
        patterns.add(key)
    return sorted(patterns)


def load_email_config(path: str | Path | None = None):
    path = Path(path or EMAIL_CONFIG_FILE)
    if path.exists():
        try:
            config = json.loads(path.read_text())
            if isinstance(config, dict):
                return {
                    "email": config.get("email", ""),
                    "imap_server": config.get("imap_server", ""),
                    "imap_port": int(config.get("imap_port", 993)) if config.get("imap_port") else 993,
                    "receipt_folder": config.get("receipt_folder", ""),
                }
        except Exception:
            pass
    return {"email": "", "imap_server": "", "imap_port": 993, "receipt_folder": ""}


def save_email_config(email_address: str, imap_server: str, imap_port: int, receipt_folder: str, path: str | Path | None = None):
    path = Path(path or EMAIL_CONFIG_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "email": email_address,
        "imap_server": imap_server,
        "imap_port": imap_port,
        "receipt_folder": receipt_folder,
    }, indent=2))


def html_to_text(html: str):
    text = re.sub(r"<script.*?>.*?</script>", "", html, flags=re.S | re.I)
    text = re.sub(r"<style.*?>.*?</style>", "", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_email_date(date_text: str):
    try:
        parsed = parsedate_to_datetime(date_text)
        if parsed is not None:
            return parsed.date()
    except Exception:
        pass
    return None


def email_message_to_text(message):
    body_parts = []
    attachments = []
    for part in message.walk():
        if part.is_multipart():
            continue
        content_disposition = part.get_content_disposition() or ""
        content_type = part.get_content_type()
        data = part.get_payload(decode=True)
        if data is None:
            continue
        filename = part.get_filename()
        if content_disposition == "attachment" or filename:
            if filename:
                attachments.append((filename, data))
            continue
        if content_type == "text/plain":
            try:
                body_parts.append(data.decode(part.get_content_charset() or "utf-8", errors="ignore"))
            except Exception:
                body_parts.append(str(data))
        elif content_type == "text/html":
            try:
                body_parts.append(html_to_text(data.decode(part.get_content_charset() or "utf-8", errors="ignore")))
            except Exception:
                pass
    return "\n".join(body_parts), attachments


def extract_transactions_from_email_message(raw_message: bytes, email_address: str):
    try:
        msg = email.message_from_bytes(raw_message, policy=policy.default)
    except Exception:
        return []

    subject = str(msg.get("Subject", ""))
    msg_date = parse_email_date(str(msg.get("Date", "")))
    body_text, attachments = email_message_to_text(msg)
    combined = f"{subject}\n{body_text}"
    receipt_keywords = ["receipt", "invoice", "order", "payment", "confirmation"]
    if not any(keyword in combined.lower() for keyword in receipt_keywords):
        return []

    transactions = extract_transactions_from_text(combined)
    if not transactions and msg_date:
        transactions = [{"Date": msg_date, "Description": subject or "Email receipt", "Amount": 0.0}]

    for filename, data in attachments:
        lower_name = filename.lower()
        if lower_name.endswith(".pdf"):
            text = capture_pdf_text(data)
            transactions.extend(extract_transactions_from_text(text))
        elif lower_name.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp")):
            text = capture_image_text(data)
            transactions.extend(extract_transactions_from_text(text))
        elif lower_name.endswith(".csv"):
            try:
                transactions.extend(parse_csv(io.BytesIO(data)))
            except Exception:
                pass
        else:
            try:
                transactions.extend(extract_transactions_from_text(data.decode("utf-8", errors="ignore")))
            except Exception:
                pass

    for tx in transactions:
        if not tx.get("Date") and msg_date:
            tx["Date"] = msg_date
    return transactions


def extract_transactions_from_email_file(file_path: str, email_address: str):
    path = Path(file_path)
    suffix = path.suffix.lower()
    try:
        if suffix == ".eml":
            return extract_transactions_from_email_message(path.read_bytes(), email_address)
        if suffix in {".txt", ".html", ".htm"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            return extract_transactions_from_text(html_to_text(text) if suffix in {".html", ".htm"} else text)
        if suffix == ".pdf":
            return extract_transactions_from_text(capture_pdf_text(path.read_bytes()))
        if suffix in {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}:
            return extract_transactions_from_text(capture_image_text(path.read_bytes()))
        if suffix == ".csv":
            with path.open("rb") as f:
                return parse_csv(f)
        return extract_transactions_from_text(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return []


def fetch_email_receipts(
    imap_server: str,
    imap_port: int,
    email_address: str,
    password: str,
    mailbox: str = "INBOX",
    sender: str | None = None,
    subject: str | None = None,
    since: str | None = None,
):
    if not imap_server or not email_address or not password:
        return []
    receipts = []
    try:
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        mail.login(email_address, password)
        mail.select(mailbox)
        criteria = ["ALL"]
        if sender:
            criteria.extend(["FROM", f'"{sender}"'])
        if subject:
            criteria.extend(["SUBJECT", f'"{subject}"'])
        if since:
            parsed = parse_date(since)
            if parsed:
                criteria.extend(["SINCE", parsed.strftime("%d-%b-%Y")])
        typ, data = mail.search(None, *criteria)
        if typ != "OK":
            mail.logout()
            return []
        msg_ids = data[0].split()
        recent_ids = msg_ids[-500:]
        for msg_id in recent_ids:
            typ, msg_data = mail.fetch(msg_id, "(RFC822)")
            if typ != "OK" or not msg_data or not msg_data[0]:
                continue
            raw = msg_data[0][1]
            extracted = extract_transactions_from_email_message(raw, email_address)
            for tx in extracted:
                tx["PaymentMethod"] = "Email"
                receipts.append(tx)
        mail.logout()
    except Exception:
        return []
    return receipts


def normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def parse_amount(text: str):
    if not isinstance(text, str):
        return None
    match = AMOUNT_RE.search(text.replace(",", ""))
    if not match:
        return None
    cleaned = match.group(1).replace("$", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_date(text: str):
    if not isinstance(text, str):
        return None
    for fmt in ["%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y.%m.%d"]:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def extract_transactions_from_text(text: str):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    transactions = []
    for line in lines:
        amount = parse_amount(line)
        date_match = DATE_RE.search(line)
        date = parse_date(date_match.group(1)) if date_match else None
        if amount is not None:
            description = line
            transactions.append({"Date": date, "Description": description, "Amount": amount})
    return transactions


def capture_image_text(file_bytes: bytes):
    with Image.open(io.BytesIO(file_bytes)) as img:
        img = img.convert("RGB")
        return pytesseract.image_to_string(img)


def capture_pdf_text(file_bytes: bytes):
    text = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text.append(page_text)
    return "\n".join(text)


def extract_raw_text_from_path(file_path: str):
    lower_name = file_path.lower()
    if lower_name.endswith(".pdf"):
        with open(file_path, "rb") as f:
            return capture_pdf_text(f.read())
    if lower_name.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp")):
        with open(file_path, "rb") as f:
            return capture_image_text(f.read())
    if lower_name.endswith(".csv"):
        return Path(file_path).read_text(errors="ignore")
    return ""


def load_transactions_from_file(uploaded_file):
    if isinstance(uploaded_file, str):
        with open(uploaded_file, "rb") as f:
            data = f.read()
        name = uploaded_file
    elif isinstance(uploaded_file, bytes):
        data = uploaded_file
        name = ""
    elif hasattr(uploaded_file, "read"):
        try:
            data = uploaded_file.read()
        except TypeError:
            data = bytes(uploaded_file)
        name = getattr(uploaded_file, "name", "")
    else:
        return []

    name = name.lower() if isinstance(name, str) else ""
    if name.endswith(".csv"):
        return parse_csv(io.BytesIO(data))
    if name.endswith(".pdf"):
        text = capture_pdf_text(data)
        return extract_transactions_from_text(text)
    if name.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp")):
        text = capture_image_text(data)
        return extract_transactions_from_text(text)
    return []


def parse_csv(file_obj):
    df = pd.read_csv(file_obj, dtype=str, keep_default_na=False)
    candidates = []
    for _, row in df.iterrows():
        description = " ".join(str(v) for v in row.values if v)
        amount = None
        date = None
        for col in row.index:
            if row[col] and amount is None:
                amount = parse_amount(str(row[col]))
            if row[col] and date is None:
                date = parse_date(str(row[col]))
        if amount is not None:
            candidates.append({"Date": date, "Description": description, "Amount": amount})
    return candidates


def categorize_transaction(description: str):
    normalized = normalize_text(description)
    for category, keywords in CATEGORY_KEYWORDS.items():
        if category == "Other":
            continue
        for keyword in keywords:
            if keyword in normalized:
                return category
    if "payroll" in normalized or "deposit" in normalized or "salary" in normalized:
        return "Income"
    if "refund" in normalized:
        return "Income"
    return "Other"


def prepare_transactions(transactions):
    for tx in transactions:
        tx["Description"] = tx.get("Description", "Unknown") or "Unknown"
        tx["Amount"] = tx.get("Amount") or 0.0
        tx["Date"] = tx.get("Date") or None
        tx["Category"] = tx.get("Category") or categorize_transaction(tx["Description"])
        tx["Vendor"] = tx.get("Vendor", tx["Description"]) or tx["Description"]
        tx["PaymentMethod"] = tx.get("PaymentMethod", "Imported") or "Imported"
        tx["Duplicate"] = bool(tx.get("Duplicate", False))
    df = pd.DataFrame(transactions)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
    if "Duplicate" not in df.columns:
        df["Duplicate"] = False
    return df


def find_recurring(df):
    df = df.copy()
    df["Normalized"] = df["Description"].astype(str).apply(normalize_text)
    counts = Counter(df["Normalized"])
    recurring = {text for text, count in counts.items() if count >= 3}
    df["Recurring"] = df["Normalized"].isin(recurring)
    return df.drop(columns=["Normalized"])


def summarize_month(df):
    summary = {}
    if df.empty:
        return {"income": 0.0, "spending": 0.0, "net": 0.0}
    income = df[df["Amount"] > 0]["Amount"].sum()
    spending = df[df["Amount"] < 0]["Amount"].sum()
    return {"income": float(income), "spending": float(spending), "net": float(income + spending)}


def category_breakdown(df):
    if df.empty:
        return pd.DataFrame(columns=["Category", "Amount"])
    grouped = df.groupby("Category")["Amount"].sum().reset_index()
    return grouped.sort_values(by="Amount", ascending=False)

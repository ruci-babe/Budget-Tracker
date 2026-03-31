import streamlit as st
import pandas as pd

from utils import (
    find_recurring,
    load_transactions_from_file,
    prepare_transactions,
    summarize_month,
    category_breakdown,
)

st.set_page_config(page_title="Expense Tracker", layout="wide")

st.title("Expense Tracker")
st.markdown(
    "Upload statements, screenshots, or receipts and review your monthly spending with categories, totals, and recurring transaction detection."
)

if "transactions" not in st.session_state:
    st.session_state.transactions = pd.DataFrame(
        columns=["Date", "Description", "Amount", "Category", "Vendor", "Recurring"]
    )

with st.sidebar:
    st.header("Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload CSV, PDF, PNG, JPG, or TIFF files",
        type=["csv", "pdf", "png", "jpg", "jpeg", "tiff", "bmp"],
        accept_multiple_files=True,
    )

    if st.button("Process Uploads"):
        new_rows = []
        for uploaded_file in uploaded_files:
            transactions = load_transactions_from_file(uploaded_file)
            new_rows.extend(transactions)

        if new_rows:
            loaded_df = prepare_transactions(new_rows)
            combined = pd.concat([st.session_state.transactions, loaded_df], ignore_index=True)
            combined = find_recurring(combined)
            st.session_state.transactions = combined
            st.success(f"Loaded {len(new_rows)} transactions.")
        else:
            st.warning("No transactions were detected. Try a different file or check your data.")

    if st.button("Clear Transactions"):
        st.session_state.transactions = pd.DataFrame(
            columns=["Date", "Description", "Amount", "Category", "Vendor", "Recurring"]
        )
        st.info("Transactions cleared.")

    st.markdown("---")
    st.markdown("### Notes")
    st.markdown(
        "- Edit the table to fix names, categories, or amounts.\n"
        "- Recurring transactions are flagged after 3 matching appearances.\n"
        "- Category suggestions are automatic but can be changed."
    )

st.header("Monthly Summary")
summary = summarize_month(st.session_state.transactions)
col1, col2, col3 = st.columns(3)
col1.metric("Money In This Month", f"${summary['income']:,.2f}")
col2.metric("Money Spent This Month", f"${summary['spending']:,.2f}")
col3.metric("Net Change", f"${summary['net']:,.2f}")

st.header("Category Breakdown")
category_df = category_breakdown(st.session_state.transactions)
if category_df.empty:
    st.info("Upload transactions to see a category breakdown.")
else:
    st.bar_chart(category_df.set_index("Category")
                 .rename(columns={"Amount": "Total"}))
    st.dataframe(category_df.style.format({"Amount": "${:,.2f}"}), use_container_width=True)

st.header("Transactions")
if st.session_state.transactions.empty:
    st.info("No transactions yet. Upload statements, receipts, or screenshots to begin.")
else:
    edited = st.data_editor(
        st.session_state.transactions,
        num_rows="dynamic",
        hide_index=True,
    )
    if st.button("Save Changes"):
        edited = edited.copy()
        edited["Date"] = pd.to_datetime(edited["Date"], errors="coerce").dt.date
        edited["Amount"] = pd.to_numeric(edited["Amount"], errors="coerce").fillna(0.0)
        edited["Recurring"] = edited.get("Recurring", False)
        st.session_state.transactions = find_recurring(edited)
        st.success("Transaction edits saved.")

    st.markdown("### Recurring Transactions")
    recurring_tx = st.session_state.transactions[st.session_state.transactions["Recurring"] == True]
    if recurring_tx.empty:
        st.write("No recurring transactions identified yet.")
    else:
        st.dataframe(recurring_tx, use_container_width=True)

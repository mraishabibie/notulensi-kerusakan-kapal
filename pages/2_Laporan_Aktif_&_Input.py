import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="Input Notulensi", page_icon="🛠️")

st.title("📋 Input Notulensi Kerusakan Kapal")
st.markdown("Gunakan form di bawah untuk menambahkan data notulensi baru ke Google Sheet.")

# --- Konfigurasi Google Sheets ---
SHEET_NAME = "Sheet1"  # Ganti sesuai dengan nama sheet kamu
SPREADSHEET_ID = "1Dnv5CQ2P1LtSst4f7DySC_vkEQBk5rPmzLst0KeAZ7g"  # ID dari URL Sheet kamu

# Ambil credentials dari secrets Streamlit (step 4)
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"])

# Koneksi ke Google Sheet
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

# --- Form Input ---
with st.form("notulensi_form"):
    day = st.text_input("Day")
    vessel = st.text_input("Vessel")
    permasalahan = st.text_area("Permasalahan")
    penyelesaian = st.text_area("Penyelesaian")
    unit = st.text_input("Unit")
    issued_date = st.date_input("Issued Date")
    closed_date = st.date_input("Closed Date", value=None)
    keterangan = st.text_area("Keterangan")
    status = st.selectbox("Status", ["Open", "Closed", "Pending"])

    submitted = st.form_submit_button("Submit")

    if submitted:
        # Ubah ke format list sesuai urutan kolom di Google Sheet
        new_row = [
            day,
            vessel,
            permasalahan,
            penyelesaian,
            unit,
            issued_date.strftime("%Y-%m-%d"),
            closed_date.strftime("%Y-%m-%d") if closed_date else "",
            keterangan,
            status
        ]

        # Simpan ke Google Sheet
        sheet.append_row(new_row)
        st.success("✅ Data berhasil disimpan ke Google Sheet!")

        # Optional: tampilkan preview data yang baru dikirim
        st.subheader("Data yang dikirim:")
        df_preview = pd.DataFrame([new_row], columns=[
            "Day", "Vessel", "Permasalahan", "Penyelesaian", "Unit",
            "Issued Date", "Closed Date", "Keterangan", "Status"
        ])
        st.dataframe(df_preview)

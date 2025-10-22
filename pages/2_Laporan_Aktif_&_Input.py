import streamlit as st
import pandas as pd
import numpy as np
import gspread
import json
import os
from google.oauth2.service_account import Credentials
from datetime import datetime

# =======================================================
# GOOGLE SHEETS CONNECTION
# =======================================================
def connect_to_gsheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
    ]
    creds_dict = json.loads(os.environ["GCP_SERVICE_ACCOUNT"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key("1Dnv5CQ2P1LtSst4f7DySC_vkEQBk5rPmzLst0KeAZ7g").sheet1
    return sheet


def load_data():
    sheet = connect_to_gsheet()
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    if not df.empty:
        if 'Day' in df.columns:
            df['Day'] = pd.to_datetime(df['Day'], errors='coerce')
    return df


def save_data(df):
    sheet = connect_to_gsheet()
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())


# =======================================================
# PAGE CONFIG
# =======================================================
st.set_page_config(page_title="Laporan Aktif & Input", layout="wide")

st.title("📋 Laporan Aktif & Input")
st.write("Gunakan halaman ini untuk menambahkan laporan baru dan melihat laporan aktif.")

# =======================================================
# LOAD DATA
# =======================================================
try:
    df = load_data()
except Exception as e:
    st.error(f"Gagal memuat data dari Google Sheets: {e}")
    st.stop()

if df.empty:
    st.warning("Data masih kosong. Silakan tambahkan laporan pertama.")
else:
    st.success("Data berhasil dimuat dari Google Sheets.")

# =======================================================
# FORM INPUT
# =======================================================
with st.expander("➕ Tambah Laporan Baru", expanded=True):
    with st.form("form_laporan"):
        col1, col2, col3 = st.columns(3)

        with col1:
            vessel = st.text_input("Vessel")
            unit = st.text_input("Unit")

        with col2:
            permasalahan = st.text_area("Permasalahan", height=100)
            penyelesaian = st.text_area("Penyelesaian", height=100)

        with col3:
            issued_date = st.date_input("Issued Date", datetime.today())
            closed_date = st.date_input("Closed Date", datetime.today())
            status = st.selectbox("Status", ["OPEN", "CLOSED", "ON PROGRESS"])
            keterangan = st.text_input("Keterangan")

        submitted = st.form_submit_button("💾 Simpan Laporan")

        if submitted:
            new_row = {
                "Day": datetime.now().strftime("%d/%m/%Y"),
                "Vessel": vessel,
                "Permasalahan": permasalahan,
                "Penyelesaian": penyelesaian,
                "Unit": unit,
                "Issued Date": issued_date.strftime("%d/%m/%Y"),
                "Closed Date": closed_date.strftime("%d/%m/%Y"),
                "Keterangan": keterangan,
                "Status": status,
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
            st.success("✅ Laporan berhasil disimpan ke Google Sheets!")
            st.rerun()

# =======================================================
# TABEL LAPORAN AKTIF
# =======================================================
st.subheader("📄 Laporan Aktif")

if df.empty:
    st.info("Belum ada data laporan.")
else:
    # Filter laporan aktif (bisa ubah filter sesuai kebutuhan)
    laporan_aktif = df[df["Status"].isin(["OPEN", "ON PROGRESS"])]

    st.dataframe(
        laporan_aktif,
        use_container_width=True,
        hide_index=True,
    )

# =======================================================
# EDIT / DELETE SECTION (Opsional)
# =======================================================
st.subheader("✏️ Edit Data")

if not df.empty:
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="editable_table",
    )

    if st.button("💾 Simpan Perubahan"):
        save_data(edited_df)
        st.success("Perubahan berhasil disimpan ke Google Sheets!")
        st.rerun()

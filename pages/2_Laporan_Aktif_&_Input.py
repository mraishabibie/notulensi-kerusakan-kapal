import streamlit as st
import pandas as pd
from datetime import datetime
import os
import numpy as np 

# --- Logika Autentikasi ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("Anda harus login untuk mengakses halaman ini. Silakan kembali ke halaman utama.")
    st.stop() 

# --- Konfigurasi ---
DATA_FILE = 'notulensi_kapal.csv'

# --- Fungsi untuk memuat dan menyimpan data ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if 'Issued Date' in df.columns:
            df['Date_Day'] = pd.to_datetime(df['Issued Date'], errors='coerce')
        return df
    else:
        return pd.DataFrame()

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# --- Inisialisasi data di session_state ---
if 'data_master_df' not in st.session_state:
    st.session_state['data_master_df'] = load_data()

df_master = st.session_state['data_master_df']

# --- Pilihan kapal dan filter ---
vessels = sorted(df_master['Vessel'].dropna().unique()) if not df_master.empty else []
selected_vessel = st.selectbox("Pilih Kapal:", options=vessels)

if selected_vessel:
    df_filtered_ship = df_master[df_master['Vessel'] == selected_vessel].copy()

    # --- Pilihan filter tahun ---
    df_filtered_ship['Year'] = df_filtered_ship['Date_Day'].dt.year
    years = sorted(df_filtered_ship['Year'].dropna().unique(), reverse=True)
    selected_year = st.selectbox("Pilih Tahun:", options=['All'] + [str(y) for y in years])

    # --- Menampilkan laporan OPEN ---
    with st.expander("📂 Laporan Aktif (OPEN)"):
        df_open = df_filtered_ship[df_filtered_ship['Status'].str.upper() == 'OPEN'].copy()
        if selected_year and selected_year != 'All':
            df_open = df_open[df_open['Date_Day'].dt.year == int(selected_year)]

        if df_open.empty:
            st.info("Belum ada laporan dengan status OPEN untuk kapal ini.")
        else:
            st.dataframe(df_open.drop(columns=['Date_Day'], errors='ignore'), hide_index=True, use_container_width=True)

    # --- Menampilkan laporan CLOSED ---
    with st.expander("📁 Lihat Riwayat Laporan (CLOSED)"):
        df_closed = df_filtered_ship[df_filtered_ship['Status'].str.upper() == 'CLOSED'].copy()

        if selected_year and selected_year != 'All':
            df_closed = df_closed[df_closed['Date_Day'].dt.year == int(selected_year)]

        if df_closed.empty:
            st.info("Belum ada laporan yang berstatus CLOSED untuk kapal ini.")
        else:
            st.caption("Klik dua kali pada sel untuk mengubah data langsung.")

            # --- Konfigurasi kolom untuk tampilan ---
            COLUMNS = [c for c in df_closed.columns if c not in ['Date_Day']]
            df_closed_display = df_closed.drop(columns=['Date_Day'], errors='ignore')

            # --- Editor interaktif ---
            edited_df = st.data_editor(
                df_closed_display,
                hide_index=True,
                use_container_width=True,
                num_rows="dynamic",
                column_order=COLUMNS,
                disabled=["Vessel", "Issued Date"],  # kolom yang tidak boleh diubah
            )

            # --- Deteksi perubahan dan tombol simpan ---
            if not edited_df.equals(df_closed_display):
                st.warning("Perubahan terdeteksi. Klik tombol di bawah untuk menyimpan.")

                if st.button("💾 Simpan Perubahan"):
                    df_master = st.session_state['data_master_df'].copy()

                    for _, row in edited_df.iterrows():
                        uid = row.get('unique_id', None)
                        if uid is not None:
                            for col in COLUMNS:
                                df_master.loc[df_master['unique_id'] == uid, col] = row[col]

                    save_data(df_master)
                    st.success("✅ Semua perubahan berhasil disimpan!")
                    st.session_state['data_master_df'] = df_master
                    st.rerun()

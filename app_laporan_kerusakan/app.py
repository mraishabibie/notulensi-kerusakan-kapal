import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time 

# --- Konfigurasi ---
DATA_FILE = 'notulensi_kerusakan.csv'
COLUMNS = ['Day', 'Vessel', 'Permasalahan', 'Penyelesaian', 'Unit', 'Issued Date', 'Keterangan', 'Status']

# --- Fungsi Manajemen Data (Tidak Berubah) ---

@st.cache_data(ttl=60) 
def load_data():
    """Memuat data dari CSV atau membuat DataFrame kosong jika file tidak ada."""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Keterangan'] = df.get('Keterangan', pd.Series([''] * len(df))).astype(str).fillna('')
        df['Status'] = df.get('Status', pd.Series(['OPEN'] * len(df))).astype(str).fillna('OPEN')
        df['Vessel'] = df['Vessel'].astype(str).str.upper().str.strip() 
        df = df[COLUMNS]
    else:
        df = pd.DataFrame(columns=COLUMNS)
    return df

def get_report_stats(df):
    """Menghitung total, open, dan closed report."""
    total = len(df)
    open_count = len(df[df['Status'].str.upper() == 'OPEN'])
    closed_count = len(df[df['Status'].str.upper() == 'CLOSED'])
    return total, open_count, closed_count

def save_data(df):
    """Menyimpan DataFrame kembali ke CSV."""
    df.to_csv(DATA_FILE, index=False)
    st.cache_data.clear() 

def add_new_data(new_entry):
    """Menambahkan baris data baru."""
    df = load_data()
    new_row_df = pd.DataFrame([new_entry], columns=COLUMNS)
    df = pd.concat([df, new_row_df], ignore_index=True)
    save_data(df)

# --- Tampilan Utama Streamlit ---

st.set_page_config(layout="wide")
st.title('⚓ Notulensi Kerusakan Kapal')

df_master = load_data()
total_reports, open_reports, closed_reports = get_report_stats(df_master)

# =========================================================
# === BAGIAN BARU: DASHBOARD STATISTIK DI DALAM CONTAINER ===
# =========================================================

# Buat Container untuk mengelompokkan semua metrik
with st.container(border=True): 
    # Tambahkan Judul kecil di dalam container (Opsional)
    st.markdown("##### Ringkasan Status Laporan")
    
    # Gunakan Columns di dalam Container
    col_total, col_open, col_closed, col_spacer = st.columns([1, 1, 1, 3]) 

    with col_total:
        st.metric("Total Seluruh Laporan", total_reports)

    with col_open:
        st.metric("Laporan Masih OPEN", open_reports)
        
    with col_closed:
        st.metric("Laporan Sudah CLOSED", closed_reports)

st.markdown("---") # Garis pemisah antara metrik dan input

# =========================================================
# === BAGIAN INPUT DATA BARU (SAMA SEPERTI SEBELUMNYA) ===
# =========================================================

# ... (Kode untuk input data baru, laporan aktif, dan riwayat di bawah ini tetap sama)

# =========================================================
# === DATA AKTIF (TANPA FILTER SELECTBOX DAN INFO TOTAL) ===
# =========================================================

st.subheader("📋 Laporan Kerusakan Aktif (OPEN)")

if df_master.empty:
    st.info("Belum ada data notulensi kerusakan tersimpan.")
else:
    df_active = df_master[df_master['Status'] == 'OPEN'].copy()

    df_display = df_active 
        
    # --- Fitur Edit Inline (menggunakan st.data_editor) ---

    editable_columns = {
        'Day': st.column_config.TextColumn("Day (DD/MM/YYYY)"),
        'Vessel': st.column_config.TextColumn("Vessel", help="Gunakan nama kapal yang konsisten."),
        'Issued Date': st.column_config.TextColumn("Issued Date", disabled=True), 
        'Status': st.column_config.SelectboxColumn(
            "Status",
            options=['OPEN', 'CLOSED'],
            required=True
        )
    }
    
    st.caption("Klik dua kali pada sel di tabel, atau gunakan kolom pencarian di kanan atas untuk memfilter laporan.")
    
    edited_df = st.data_editor(
        df_display,
        column_config=editable_columns,
        column_order=['Day', 'Vessel', 'Permasalahan', 'Penyelesaian', 'Unit', 'Issued Date', 'Keterangan', 'Status'],
        hide_index=True,
        use_container_width=True,
    )
    
    if not df_display.equals(edited_df):
        st.warning("⚠️ Perubahan terdeteksi. Silakan klik tombol 'Simpan Perubahan' untuk menyimpan data.")
        
        if st.button("💾 Simpan Perubahan"):
            
            original_indices = df_display.index
            
            for i, idx in enumerate(original_indices):
                edited_row = edited_df.iloc[i]
                df_master.loc[idx, edited_df.columns] = edited_row.values
            
            save_data(df_master)
            st.success("✅ Data berhasil diperbarui!")
            time.sleep(1)
            st.rerun()

# =========================================================
# === TOMBOL INPUT DI BAWAH TABEL ===
# =========================================================
st.write("")
if st.button("➕ Tambah Laporan Kerusakan Baru", use_container_width=True):
    st.session_state.show_new_report_form = True

# Tampilkan formulir jika tombol diklik atau jika state sudah aktif
if st.session_state.get('show_new_report_form'):
    st.subheader("Formulir Laporan Baru")
    
    with st.form("new_report_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            vessel = st.text_input("Nama Kapal (Vessel)*") 
            unit = st.text_input("Unit/Sistem yang Rusak")
            day = st.date_input("Tanggal Kejadian (Day)", datetime.now().date())
        
        with col2:
            permasalahan = st.text_area("Detail Permasalahan*", height=100)
            penyelesaian = st.text_area("Langkah Penyelesaian Sementara/Tindakan")
            keterangan = st.text_input("Keterangan Tambahan")
            default_status = st.selectbox("Status Awal Laporan", options=['OPEN', 'CLOSED'], index=0) 

        submitted_new = st.form_submit_button("✅ Simpan Laporan")
        
        if submitted_new:
            if vessel and permasalahan:
                today_date_str = datetime.now().strftime('%d/%m/%Y')
                new_row = {
                    'Day': day.strftime('%d/%m/%Y'),
                    'Vessel': vessel.upper().strip(), 
                    'Permasalahan': permasalahan,
                    'Penyelesaian': penyelesaian,
                    'Unit': unit,
                    'Issued Date': today_date_str,
                    'Keterangan': keterangan,
                    'Status': default_status 
                }
                add_new_data(new_row)
                st.success("Laporan baru berhasil disimpan!")
                st.session_state.show_new_report_form = False 
                time.sleep(1) 
                st.rerun() 
            else:
                st.error("Nama Kapal dan Permasalahan wajib diisi.")

st.markdown("---")

# =========================================================
# === TAMPILAN DATA RIWAYAT (CLOSED) ===
# =========================================================

with st.expander("📁 Lihat Riwayat Laporan (CLOSED)"):
    df_closed = df_master[df_master['Status'] == 'CLOSED'].copy()
    if df_closed.empty:
        st.info("Belum ada laporan yang berstatus CLOSED.")
    else:
        st.caption("Gunakan fitur edit *inline* di tabel aktif untuk membuka kembali laporan yang sudah ditutup.")
        st.dataframe(df_closed, 
                     hide_index=True, 
                     use_container_width=True,
                     column_order=COLUMNS,
                     )
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time 
import numpy as np 

# --- Logika Autentikasi ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("Anda harus login untuk mengakses halaman ini. Silakan kembali ke halaman utama.")
    st.stop() 

# --- PERBAIKAN: INISIALISASI SESSION STATE YANG HILANG ---
# Pastikan status form input baru sudah diinisialisasi, terutama jika halaman ini diakses langsung
if 'show_new_report_form_v2' not in st.session_state:
    st.session_state.show_new_report_form_v2 = False
# --------------------------------------------------------

# --- Konfigurasi ---
DATA_FILE = 'notulensi_kerusakan.csv'
COLUMNS = ['Day', 'Vessel', 'Permasalahan', 'Penyelesaian', 'Unit', 'Issued Date', 'Closed Date', 'Keterangan', 'Status'] 
DATE_FORMAT = '%d/%m/%Y'

# --- Fungsi Manajemen Data ---

def load_data():
    """Memuat data dari CSV atau membuat DataFrame kosong, dan mengaturnya ke Session State."""
    
    # 1. Cek apakah data sudah ada di session state. Jika ya, kembalikan data dari state.
    if 'data_master_df' in st.session_state and not st.session_state['data_master_df'].empty:
        return st.session_state['data_master_df'].copy()

    # 2. Jika tidak ada di session state, muat dari file CSV
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        
        if 'Closed Date' not in df.columns:
            df['Closed Date'] = pd.NA
        
        # Penanganan kolom untuk memastikan format yang benar
        df['Keterangan'] = df.get('Keterangan', pd.Series([''] * len(df))).astype(str).fillna('')
        df['Status'] = df.get('Status', pd.Series(['OPEN'] * len(df))).astype(str).fillna('OPEN').str.upper()
        df['Vessel'] = df['Vessel'].astype(str).str.upper().str.strip() 
        df['Unit'] = df['Unit'].astype(str).str.upper().str.strip() 
        
        df['Date_Day'] = pd.to_datetime(df['Day'], format=DATE_FORMAT, errors='coerce')
        
        df = df.reindex(columns=COLUMNS + ['Date_Day']) 
        
    else:
        df = pd.DataFrame(columns=COLUMNS + ['Date_Day'])
        
    # 3. Simpan data yang baru dimuat ke Session State
    st.session_state['data_master_df'] = df.copy() 
    
    return df

def get_report_stats(df, year=None):
    """Menghitung total, open, dan closed report, difilter berdasarkan tahun."""
    df_filtered = df.copy()
    
    if year and year != 'All':
        df_filtered = df_filtered[df_filtered['Date_Day'].dt.year == int(year)]
        
    total = len(df_filtered)
    open_count = len(df_filtered[df_filtered['Status'].str.upper() == 'OPEN'])
    closed_count = len(df_filtered[df_filtered['Status'].str.upper() == 'CLOSED'])
    return total, open_count, closed_count, df_filtered

def save_data(df):
    """Menyimpan DataFrame kembali ke CSV, memperbarui Session State, dan clear cache global."""
    df_to_save = df.drop(columns=['Date_Day'], errors='ignore')
    df_to_save.to_csv(DATA_FILE, index=False)
    
    # Perbarui Session State dan Clear Cache Global
    st.session_state['data_master_df'] = df.copy()
    st.cache_data.clear()
    st.cache_resource.clear() 

def add_new_data(new_entry):
    """Menambahkan baris data baru."""
    df = load_data() 
    new_row_df = pd.DataFrame([new_entry], columns=COLUMNS) 
    
    if new_entry.get('Day') and pd.notna(new_entry['Day']):
        try:
            date_day_dt = datetime.strptime(new_entry['Day'], DATE_FORMAT)
            new_row_df['Date_Day'] = date_day_dt
        except ValueError:
            new_row_df['Date_Day'] = pd.NaT 
    else:
        new_row_df['Date_Day'] = pd.NaT
        
    df = pd.concat([df, new_row_df], ignore_index=True)
    save_data(df)

# --- Tampilan Utama ---
st.title('📝 Laporan Kerusakan Aktif & Input Data')

df_master = load_data()

vessel_options = sorted(df_master['Vessel'].dropna().unique().tolist())
unit_options = sorted(df_master['Unit'].dropna().unique().tolist())

# =========================================================
# === DASHBOARD STATISTIK DENGAN FILTER TAHUN ===
# =========================================================

valid_years = df_master['Date_Day'].dt.year.dropna().astype(int).unique()
year_options = ['All'] + sorted(valid_years.tolist(), reverse=True)

with st.container(border=True): 
    col_filter, col_spacer_top = st.columns([1, 4])
    
    with col_filter:
        selected_year = st.selectbox("Filter Tahun Kejadian", year_options, key="filter_tahun_aktif")
        
    total_reports, open_reports, closed_reports, _ = get_report_stats(df_master, selected_year)

    st.markdown("##### Ringkasan Status Laporan")
    
    col_total, col_open, col_closed, col_spacer = st.columns([1, 1, 1, 3]) 

    with col_total:
        st.metric("Total Seluruh Laporan", total_reports)

    with col_open:
        st.metric("Laporan Masih OPEN", open_reports)
        
    with col_closed:
        st.metric("Laporan Sudah CLOSED", closed_reports)

st.markdown("---") 

# =========================================================
# === DATA AKTIF (EDITABLE) ===
# =========================================================

st.subheader("📋 Laporan Kerusakan Aktif (OPEN)")

if df_master.empty:
    st.info("Belum ada data notulensi kerusakan tersimpan.")
else:
    df_active = df_master[df_master['Status'].str.upper() == 'OPEN'].copy()

    if selected_year and selected_year != 'All':
          df_active = df_active[df_active['Date_Day'].dt.year == int(selected_year)]

    df_display = df_active.drop(columns=['Date_Day'], errors='ignore')
    
    # Kolom Issued Date dan Status harus ada untuk inisialisasi
    if 'Issued Date' not in df_display.columns:
        df_display['Issued Date'] = pd.NA
    if 'Status' not in df_display.columns:
        df_display['Status'] = 'OPEN'

    # --- EDITABLE COLUMNS DENGAN SELECTBOX UNTUK VESSEL DAN UNIT ---
    editable_columns = {
        'Day': st.column_config.TextColumn("Day (DD/MM/YYYY)", required=True),
        'Vessel': st.column_config.SelectboxColumn( 
            "Vessel", 
            options=vessel_options, 
            required=True,
            help="Pilih dari daftar kapal yang sudah ada untuk konsistensi data."
        ),
        'Unit': st.column_config.SelectboxColumn( 
            "Unit", 
            options=unit_options, 
            required=True,
            help="Pilih dari daftar unit yang sudah ada."
        ),
        'Issued Date': st.column_config.TextColumn("Issued Date", disabled=True), 
        'Closed Date': st.column_config.TextColumn("Closed Date (DD/MM/YYYY)"),
        'Status': st.column_config.SelectboxColumn(
            "Status",
            options=['OPEN', 'CLOSED'],
            required=True
        )
    }
    
    st.caption("Klik dua kali pada sel di tabel untuk **Edit Inline**. Tanggal harus dalam format **DD/MM/YYYY**.")
    
    edited_df = st.data_editor(
        df_display,
        column_config=editable_columns,
        column_order=COLUMNS,
        hide_index=True,
        use_container_width=True,
        key='active_report_editor' 
    )
    
    if not df_display.equals(edited_df):
        st.warning("⚠️ Perubahan terdeteksi. Silakan klik tombol 'Simpan Perubahan' untuk menyimpan data.")
        
        col_save, col_spacer_save = st.columns([1, 5])
        with col_save:
            if st.button("💾 Simpan Perubahan", key='save_button_active'):
                
                original_indices = df_display.index
                
                for i, idx in enumerate(original_indices):
                    edited_row = edited_df.iloc[i]
                    
                    closed_date_val = str(edited_row['Closed Date']).strip()
                    current_status = edited_row['Status'].upper().strip()
                    
                    if current_status == 'OPEN':
                        df_master.loc[idx, 'Closed Date'] = pd.NA
                    elif current_status == 'CLOSED':
                        if closed_date_val == '' or pd.isna(closed_date_val):
                             st.error(f"Baris ke-{i+1}: Status CLOSED membutuhkan Tanggal Selesai (Closed Date).")
                             st.stop()
                        try:
                            datetime.strptime(closed_date_val, DATE_FORMAT)
                            df_master.loc[idx, 'Closed Date'] = closed_date_val
                        except ValueError:
                            st.error(f"Baris ke-{i+1}: Format Tanggal Selesai (Closed Date) salah. Gunakan DD/MM/YYYY.")
                            st.stop()
                    
                    df_master.loc[idx, 'Status'] = current_status
                        
                    day_val = str(edited_row['Day']).strip()
                    try:
                        date_dt = datetime.strptime(day_val, DATE_FORMAT)
                        df_master.loc[idx, 'Day'] = day_val
                        df_master.loc[idx, 'Date_Day'] = date_dt
                    except ValueError:
                        st.error(f"Baris ke-{i+1}: Format Tanggal Kejadian (Day) salah. Gunakan DD/MM/YYYY.")
                        st.stop()
                        
                    for col in ['Vessel', 'Permasalahan', 'Penyelesaian', 'Unit', 'Keterangan']:
                        val = edited_row[col]
                        if col in ['Vessel', 'Unit']:
                            df_master.loc[idx, col] = str(val).upper().strip()
                        else:
                            df_master.loc[idx, col] = val
                            
                save_data(df_master)
                st.success("✅ Data berhasil diperbarui!")
                time.sleep(1)
                st.rerun()

# =========================================================
# === TOMBOL INPUT & FORMULIR ===
# =========================================================

st.markdown("---")
if st.button("➕ Tambah Laporan Kerusakan Baru", use_container_width=True):
    st.session_state.show_new_report_form_v2 = not st.session_state.show_new_report_form_v2

if st.session_state.get('show_new_report_form_v2'):
    st.subheader("Formulir Laporan Baru")
    
    with st.form("new_report_form_v2", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        vessel_options_new = sorted(df_master['Vessel'].dropna().unique().tolist())
        unit_options_new = sorted(df_master['Unit'].dropna().unique().tolist())
        
        with col1:
            vessel_select = st.selectbox("Nama Kapal (Vessel)*", options=[''] + vessel_options_new + ['--- Input Baru ---'], key="vessel_select") 
            if vessel_select == '--- Input Baru ---' or vessel_select == '':
                vessel = st.text_input("Vessel (Input Manual)*", key="vessel_manual").upper().strip()
            else:
                vessel = vessel_select
                
            unit_select = st.selectbox("Unit/Sistem yang Rusak", options=[''] + unit_options_new + ['--- Input Baru ---'], key="unit_select") 
            if unit_select == '--- Input Baru ---' or unit_select == '':
                unit = st.text_input("Unit (Input Manual)", key="unit_manual").upper().strip()
            else:
                unit = unit_select
                
            day = st.date_input("Tanggal Kejadian (Day)*", datetime.now().date(), key="day_input")
        
        with col2:
            permasalahan = st.text_area("Detail Permasalahan*", height=100)
            penyelesaian = st.text_area("Langkah Penyelesaian Sementara/Tindakan")
            keterangan = st.text_input("Keterangan Tambahan")
            
            status_cols = st.columns(2)
            with status_cols[0]:
                default_status = st.selectbox("Status Awal Laporan", options=['OPEN', 'CLOSED'], index=0) 
            
            with status_cols[1]:
                closed_date_input = st.date_input("Tanggal Selesai (Jika Closed)", 
                                                  value=None, 
                                                  disabled=(default_status == 'OPEN'),
                                                  key='closed_date_input_new')

        submitted_new = st.form_submit_button("✅ Simpan Laporan")
        
        if submitted_new:
            final_vessel = vessel.upper().strip()
            final_unit = unit.upper().strip()
            
            if not final_vessel or not permasalahan:
                st.error("Nama Kapal dan Permasalahan wajib diisi.")
                st.stop()
            
            closed_date_val = pd.NA
            if default_status == 'CLOSED':
                if closed_date_input is None:
                    st.error("Status CLOSED memerlukan Tanggal Selesai (Closed Date) diisi.")
                    st.stop()
                closed_date_val = closed_date_input.strftime(DATE_FORMAT)
                
            
            today_date_str = datetime.now().strftime(DATE_FORMAT)
            
            new_row = {
                'Day': day.strftime(DATE_FORMAT),
                'Vessel': final_vessel, 
                'Permasalahan': permasalahan,
                'Penyelesaian': penyelesaian,
                'Unit': final_unit,
                'Issued Date': today_date_str,
                'Closed Date': closed_date_val, 
                'Keterangan': keterangan,
                'Status': default_status.upper() 
            }
            
            add_new_data(new_row)
            
            st.success("Laporan baru berhasil disimpan!")
            st.session_state.show_new_report_form_v2 = False 
            time.sleep(1) 
            st.rerun() 

st.markdown("---")

# =========================================================
# === TAMPILAN DATA RIWAYAT (CLOSED) ===
# =========================================================

with st.expander("📁 Lihat Riwayat Laporan (CLOSED)"):
    df_closed = df_master[df_master['Status'].str.upper() == 'CLOSED'].copy()

    if selected_year and selected_year != 'All':
          df_closed = df_closed[df_closed['Date_Day'].dt.year == int(selected_year)]

    if df_closed.empty:
        st.info("Belum ada laporan yang berstatus CLOSED.")
    else:
        st.caption("Gunakan ikon corong/search bar untuk memfilter riwayat.")
        df_closed_display = df_closed.drop(columns=['Date_Day'], errors='ignore')
        
        st.dataframe(df_closed_display, 
                     hide_index=True, 
                     use_container_width=True,
                     column_order=COLUMNS,
                     )
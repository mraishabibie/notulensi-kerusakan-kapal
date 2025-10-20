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

# --- PERBAIKAN: Cek Kapal Terpilih & Inisialisasi Variabel Kapal ---
if 'selected_ship_code' not in st.session_state or st.session_state.selected_ship_code is None:
    st.error("Anda harus memilih kapal dari halaman utama terlebih dahulu.")
    st.stop() 

SELECTED_SHIP_CODE = st.session_state.selected_ship_code
SELECTED_SHIP_NAME = st.session_state.selected_ship_name
# -------------------------------------------------------------------

# --- PERBAIKAN: INISIALISASI SESSION STATE YANG HILANG ---
if 'show_new_report_form_v2' not in st.session_state:
    st.session_state.show_new_report_form_v2 = False
# --------------------------------------------------------

# --- Konfigurasi ---
DATA_FILE = 'notulensi_kerusakan.csv'
COLUMNS = ['Day', 'Vessel', 'Permasalahan', 'Penyelesaian', 'Unit', 'Issued Date', 'Closed Date', 'Keterangan', 'Status'] 
DATE_FORMAT = '%d/%m/%Y'

# --- Fungsi Manajemen Data ---

def load_data():
    """Memuat data master UTUH dari CSV ke Session State, lalu mengembalikan data yang DIFILTER."""
    
    # 1. Muat data master UTUH jika belum ada di session state
    if 'data_master_df' not in st.session_state or st.session_state['data_master_df'].empty:
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            
            if 'Closed Date' not in df.columns:
                df['Closed Date'] = pd.NA
            
            # Penanganan kolom untuk memastikan format yang benar
            df['Keterangan'] = df.get('Keterangan', pd.Series([''] * len(df))).astype(str).fillna('')
            df['Status'] = df.get('Status', pd.Series(['OPEN'] * len(df))).astype(str).fillna('OPEN').str.upper()
            df['Vessel'] = df['Vessel'].astype(str).str.upper().str.strip() 
            df['Unit'] = df['Unit'].astype(str).str.upper().str.strip() 
            
            # Kolom Day digunakan untuk Date_Day
            df['Date_Day'] = pd.to_datetime(df['Day'], format=DATE_FORMAT, errors='coerce')
            
            df = df.reindex(columns=COLUMNS + ['Date_Day']) 
            
        else:
            df = pd.DataFrame(columns=COLUMNS + ['Date_Day'])
            
        # Simpan data UTUH ke Session State
        st.session_state['data_master_df'] = df.copy() 
    
    # 2. Filter dan kembalikan data HANYA untuk kapal yang dipilih
    df_all = st.session_state['data_master_df'].copy()
    
    df_filtered_ship = df_all[
        df_all['Vessel'].astype(str).str.upper() == SELECTED_SHIP_CODE.upper()
    ].copy()
    
    return df_filtered_ship

def get_report_stats(df, year=None):
    """Menghitung total, open, dan closed report, difilter berdasarkan tahun."""
    df_filtered = df.copy()
    
    if year and year != 'All':
        df_filtered = df_filtered[df_filtered['Date_Day'].dt.year == int(year)]
        
    total = len(df_filtered)
    open_count = len(df_filtered[df_filtered['Status'].str.upper() == 'OPEN'])
    closed_count = len(df_filtered[df_filtered['Status'].str.upper() == 'CLOSED'])
    return total, open_count, closed_count, df_filtered

def save_data(df_to_save_full):
    """Menyimpan DataFrame master UTUH kembali ke CSV, memperbarui Session State, dan clear cache global."""
    # Fungsi ini menerima DataFrame master UTUH (df_all)
    df_to_save_full_clean = df_to_save_full.drop(columns=['Date_Day'], errors='ignore')
    df_to_save_full_clean.to_csv(DATA_FILE, index=False)
    
    # Perbarui Session State dan Clear Cache Global
    st.session_state['data_master_df'] = df_to_save_full.copy()
    st.cache_data.clear()
    st.cache_resource.clear() 

def add_new_data(new_entry):
    """Menambahkan baris data baru ke data master UTUH di Session State."""
    # Ambil data master UTUH
    df_all = st.session_state['data_master_df'].copy()
    
    new_row_df = pd.DataFrame([new_entry], columns=COLUMNS) 
    
    if new_entry.get('Day') and pd.notna(new_entry['Day']):
        try:
            date_day_dt = datetime.strptime(new_entry['Day'], DATE_FORMAT)
            new_row_df['Date_Day'] = date_day_dt
        except ValueError:
            new_row_df['Date_Day'] = pd.NaT 
    else:
        new_row_df['Date_Day'] = pd.NaT
        
    df_all = pd.concat([df_all, new_row_df], ignore_index=True)
    save_data(df_all)

# --- Tampilan Utama ---
st.title(f'📝 Laporan Kerusakan Aktif & Input Data: {SELECTED_SHIP_NAME} ({SELECTED_SHIP_CODE})')

df_filtered_ship = load_data() # df_filtered_ship hanya berisi data kapal yang dipilih

# Karena hanya ada 1 kapal, Vessel Options tidak perlu banyak
vessel_options = [SELECTED_SHIP_CODE] 
unit_options = sorted(df_filtered_ship['Unit'].dropna().unique().tolist())

# =========================================================
# === DASHBOARD STATISTIK DENGAN FILTER TAHUN ===
# =========================================================

valid_years = df_filtered_ship['Date_Day'].dt.year.dropna().astype(int).unique()
year_options = ['All'] + sorted(valid_years.tolist(), reverse=True)

with st.container(border=True): 
    col_filter, col_spacer_top = st.columns([1, 4])
    
    with col_filter:
        selected_year = st.selectbox("Filter Tahun Kejadian", year_options, key="filter_tahun_aktif")
        
    total_reports, open_reports, closed_reports, _ = get_report_stats(df_filtered_ship, selected_year)

    st.markdown("##### Ringkasan Status Laporan")
    
    col_total, col_open, col_closed, col_spacer = st.columns([1, 1, 1, 3]) 
    
    # --- CSS KUSTOM UNTUK METRIK ---
    st.markdown("""
        <style>
            .metric-box-custom {
                background-color: #F0F2F6; /* Background light */
                border-radius: 8px;
                padding: 10px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                min-height: 80px;
            }
            .metric-value-total {
                font-size: 2em;
                font-weight: bold;
                color: #005691; /* Dark Blue for Total/Neutral */
            }
            .metric-value-open {
                font-size: 2em;
                font-weight: bold;
                color: #FF4B4B; /* Red for Open */
            }
            .metric-value-closed {
                font-size: 2em;
                font-weight: bold;
                color: #00BA38; /* Green for Closed */
            }
            .metric-label-custom {
                font-size: 0.9em;
                color: #555555;
            }
        </style>
    """, unsafe_allow_html=True)
    # -------------------------------

    with col_total:
        st.markdown(f"""
            <div class="metric-box-custom" style="border-left: 5px solid #005691;">
                <div class="metric-label-custom">Total Seluruh Laporan</div>
                <div class="metric-value-total">{total_reports}</div>
            </div>
        """, unsafe_allow_html=True)

    with col_open:
        st.markdown(f"""
            <div class="metric-box-custom" style="border-left: 5px solid #FF4B4B;">
                <div class="metric-label-custom">Laporan Masih OPEN</div>
                <div class="metric-value-open">{open_reports}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col_closed:
        st.markdown(f"""
            <div class="metric-box-custom" style="border-left: 5px solid #00BA38;">
                <div class="metric-label-custom">Laporan Sudah CLOSED</div>
                <div class="metric-value-closed">{closed_reports}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---") 

# =========================================================
# === DATA AKTIF (EDITABLE) ===
# (Menggunakan df_filtered_ship)
# =========================================================

st.subheader("📋 Laporan Kerusakan Aktif (OPEN)")

if df_filtered_ship.empty:
    st.info("Belum ada data notulensi kerusakan tersimpan untuk kapal ini.")
else:
    # Filter status OPEN
    df_active = df_filtered_ship[df_filtered_ship['Status'].str.upper() == 'OPEN'].copy()

    if selected_year and selected_year != 'All':
          df_active = df_active[df_active['Date_Day'].dt.year == int(selected_year)]

    df_display = df_active.drop(columns=['Date_Day'], errors='ignore')
    
    if 'Issued Date' not in df_display.columns:
        df_display['Issued Date'] = pd.NA
    if 'Status' not in df_display.columns:
        df_display['Status'] = 'OPEN'

    # --- EDITABLE COLUMNS DENGAN SELECTBOX UNTUK VESSEL DAN UNIT ---
    editable_columns = {
        'Day': st.column_config.TextColumn("Day (DD/MM/YYYY)", required=True),
        'Vessel': st.column_config.SelectboxColumn( 
            "Vessel", 
            options=vessel_options, # Hanya satu kapal
            required=True,
            help="Nama kapal sudah difilter."
        ),
        'Unit': st.column_config.SelectboxColumn( 
            "Unit", 
            options=unit_options, 
            required=True,
            help="Pilih dari daftar unit yang sudah ada."
        ),
        # PERBAIKAN: Issued Date dibuat disable/readonly karena nilainya mengikuti Day
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
                
                # Load data master UTUH
                df_master_all = st.session_state['data_master_df'].copy()

                original_indices = df_display.index
                
                # Update baris di data master UTUH
                for i, idx in enumerate(original_indices):
                    edited_row = edited_df.iloc[i]
                    
                    closed_date_val = str(edited_row['Closed Date']).strip()
                    current_status = edited_row['Status'].upper().strip()
                    
                    # 1. Validasi dan Update Status/Closed Date
                    if current_status == 'OPEN':
                        df_master_all.loc[idx, 'Closed Date'] = pd.NA
                    elif current_status == 'CLOSED':
                        if closed_date_val == '' or pd.isna(closed_date_val):
                             st.error(f"Baris ke-{i+1}: Status CLOSED membutuhkan Tanggal Selesai (Closed Date).")
                             st.stop()
                        try:
                            datetime.strptime(closed_date_val, DATE_FORMAT)
                            df_master_all.loc[idx, 'Closed Date'] = closed_date_val
                        except ValueError:
                            st.error(f"Baris ke-{i+1}: Format Tanggal Selesai (Closed Date) salah. Gunakan DD/MM/YYYY.")
                            st.stop()
                    
                    df_master_all.loc[idx, 'Status'] = current_status
                        
                    # 2. Validasi dan Update Day & Issued Date
                    day_val = str(edited_row['Day']).strip()
                    try:
                        date_dt = datetime.strptime(day_val, DATE_FORMAT)
                        df_master_all.loc[idx, 'Day'] = day_val
                        df_master_all.loc[idx, 'Date_Day'] = date_dt
                        # PERBAIKAN: Issued Date = Day
                        df_master_all.loc[idx, 'Issued Date'] = day_val 
                    except ValueError:
                        st.error(f"Baris ke-{i+1}: Format Tanggal Kejadian (Day) salah. Gunakan DD/MM/YYYY.")
                        st.stop()
                        
                    # 3. Update Kolom Lain
                    for col in ['Vessel', 'Permasalahan', 'Penyelesaian', 'Unit', 'Keterangan']:
                        # Kolom Issued Date sudah diupdate di langkah 2
                        if col == 'Issued Date': continue 
                            
                        val = edited_row[col]
                        if col in ['Vessel', 'Unit']:
                            df_master_all.loc[idx, col] = str(val).upper().strip()
                        else:
                            df_master_all.loc[idx, col] = val
                            
                save_data(df_master_all) # Simpan data master UTUH
                st.success("✅ Data berhasil diperbarui!")
                time.sleep(1)
                st.rerun()

# =========================================================
# === TOMBOL INPUT & FORMULIR ===
# =========================================================

st.write("")
if st.button("➕ Tambah Laporan Kerusakan Baru", use_container_width=True):
    st.session_state.show_new_report_form_v2 = not st.session_state.show_new_report_form_v2

if st.session_state.get('show_new_report_form_v2'):
    st.subheader("Formulir Laporan Baru")
    
    # --- CSS KUSTOM UNTUK FORMULIR INPUT BARU ---
    st.markdown("""
        <style>
            /* Target stForm container */
            .stForm {
                background-color: #FFFFFF; /* Latar belakang putih */
                border-radius: 12px;
                padding: 20px;
                /* Shadow tipis */
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1); 
                border-top: 5px solid #005691; /* Border aksen biru */
                margin-bottom: 20px;
            }
            /* Styling untuk tombol submit di dalam form */
            .stForm .stButton>button {
                background-color: #00BA38; /* Hijau untuk tombol Simpan */
                color: white;
                border: none;
                border-radius: 8px;
                margin-top: 10px;
            }
            .stForm .stButton>button:hover {
                background-color: #00992C;
            }
        </style>
    """, unsafe_allow_html=True)
    # ---------------------------------------------
    
    with st.form("new_report_form_v2", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        vessel_options_new = [SELECTED_SHIP_CODE] 
        unit_options_new = sorted(df_filtered_ship['Unit'].dropna().unique().tolist())
        
        with col1:
            st.markdown("<h5 style='color:#005691;'>Informasi Dasar</h5>", unsafe_allow_html=True)
            vessel_select = st.selectbox("Nama Kapal (Vessel)*", 
                                         options=vessel_options_new, 
                                         key="vessel_select_new",
                                         index=0,
                                         disabled=True)
            vessel = vessel_select 
                
            unit_select = st.selectbox("Unit/Sistem yang Rusak", options=[''] + unit_options_new + ['--- Input Baru ---'], key="unit_select") 
            if unit_select == '--- Input Baru ---' or unit_select == '':
                unit = st.text_input("Unit (Input Manual)", key="unit_manual").upper().strip()
            else:
                unit = unit_select
                
            day = st.date_input("Tanggal Kejadian (Day)*", datetime.now().date(), key="day_input")
        
        with col2:
            st.markdown("<h5 style='color:#005691;'>Detail Laporan & Status</h5>", unsafe_allow_html=True)
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
                
            # PERBAIKAN: Issued Date mengambil nilai dari Day
            issued_date_val = day.strftime(DATE_FORMAT)
            
            new_row = {
                'Day': issued_date_val, # Day
                'Vessel': final_vessel, 
                'Permasalahan': permasalahan,
                'Penyelesaian': penyelesaian,
                'Unit': final_unit,
                'Issued Date': issued_date_val, # Issued Date = Day
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
# (Menggunakan df_filtered_ship)
# =========================================================

with st.expander("📁 Lihat Riwayat Laporan (CLOSED)"):
    df_closed = df_filtered_ship[df_filtered_ship['Status'].str.upper() == 'CLOSED'].copy()

    if selected_year and selected_year != 'All':
          df_closed = df_closed[df_closed['Date_Day'].dt.year == int(selected_year)]

    if df_closed.empty:
        st.info("Belum ada laporan yang berstatus CLOSED untuk kapal ini.")
    else:
        st.caption("Gunakan ikon corong/search bar untuk memfilter riwayat.")
        df_closed_display = df_closed.drop(columns=['Date_Day'], errors='ignore')
        
        st.dataframe(df_closed_display, 
                     hide_index=True, 
                     use_container_width=True,
                     column_order=COLUMNS,
                     )

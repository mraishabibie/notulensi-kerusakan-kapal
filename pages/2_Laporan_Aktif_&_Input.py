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
            
            # PENTING: Reset index dan jadikan index sebagai ID unik
            df = df.reset_index(drop=True)
            df['unique_id'] = df.index
            
        else:
            df = pd.DataFrame(columns=COLUMNS + ['Date_Day', 'unique_id'])
            
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
    # Hapus kolom 'Date_Day' dan 'unique_id' sebelum simpan ke CSV
    df_to_save_full_clean = df_to_save_full.drop(columns=['Date_Day', 'unique_id'], errors='ignore')
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
        
    # Tetapkan ID unik baru
    new_id = df_all['unique_id'].max() + 1 if not df_all.empty else 0
    new_row_df['unique_id'] = new_id
        
    df_all = pd.concat([df_all, new_row_df], ignore_index=True)
    save_data(df_all)

def delete_data(index_to_delete):
    """Menghapus baris berdasarkan unique_id."""
    df_all = st.session_state['data_master_df'].copy()
    
    # Hapus baris berdasarkan unique_id (karena index bisa berubah-ubah)
    df_deleted = df_all[df_all['unique_id'] != index_to_delete]
    
    # PENTING: Hapus cache agar pemuatan data berikutnya mengambil yang sudah dihapus
    st.cache_data.clear()
    save_data(df_deleted)
    st.success(f"✅ Laporan dengan ID {index_to_delete} berhasil dihapus.")
    time.sleep(1)
    st.rerun()


# --- Tampilan Utama ---
st.title(f'📝 Laporan Kerusakan Aktif & Input Data: {SELECTED_SHIP_NAME} ({SELECTED_SHIP_CODE})')

df_filtered_ship = load_data() # df_filtered_ship hanya berisi data kapal yang dipilih

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
# === DATA AKTIF (EDITABLE DAN DELETABLE) ===
# =========================================================

st.subheader("📋 Laporan Kerusakan Aktif (OPEN)")

if df_filtered_ship.empty:
    st.info("Belum ada data notulensi kerusakan tersimpan untuk kapal ini.")
else:
    # Filter status OPEN
    df_active = df_filtered_ship[df_filtered_ship['Status'].str.upper() == 'OPEN'].copy()

    if selected_year and selected_year != 'All':
          df_active = df_active[df_active['Date_Day'].dt.year == int(selected_year)]
          
    # Pindahkan kolom unique_id ke index untuk memudahkan
    df_active = df_active.set_index('unique_id', drop=False)

    df_display = df_active.drop(columns=['Date_Day', 'unique_id'], errors='ignore')
    
    # 1. Edit Data (Tetap menggunakan st.data_editor untuk kemudahan inline edit)
    st.caption("Klik dua kali pada sel di tabel untuk **Edit Inline**. Tanggal harus dalam format **DD/MM/YYYY**.")
    
    edited_df = st.data_editor(
        df_display,
        column_config={
            'Day': st.column_config.TextColumn("Day (DD/MM/YYYY)", required=True),
            'Vessel': st.column_config.SelectboxColumn("Vessel", options=vessel_options, required=True, help="Nama kapal sudah difilter."),
            'Unit': st.column_config.SelectboxColumn("Unit", options=unit_options, required=True, help="Pilih dari daftar unit yang sudah ada."),
            'Issued Date': st.column_config.TextColumn("Issued Date", disabled=True), 
            'Closed Date': st.column_config.TextColumn("Closed Date (DD/MM/YYYY)"),
            'Status': st.column_config.SelectboxColumn("Status", options=['OPEN', 'CLOSED'], required=True)
        },
        column_order=COLUMNS,
        hide_index=False, # Tampilkan Index (unique_id) untuk debugging/referensi
        use_container_width=True,
        key='active_report_editor' 
    )
    
    # Logika Penyimpanan Data
    if not df_display.equals(edited_df):
        st.warning("⚠️ Perubahan terdeteksi. Silakan klik tombol 'Simpan Perubahan' untuk menyimpan data.")
        
    # --- MENAMBAH TOMBOL SIMPAN DI BAWAH TABEL (LEBIH MENONJOL) ---
    col_save_bottom, col_spacer_bottom = st.columns([1, 5])
    
    with col_save_bottom:
        if st.button("💾 SIMPAN SEMUA PERUBAHAN", key='save_button_bottom', use_container_width=True, help="Klik ini untuk menyimpan semua perubahan inline di tabel di atas."):
            
            if df_display.equals(edited_df):
                 st.info("Tidak ada perubahan data yang terdeteksi untuk disimpan.")
                 st.stop()
                 
            df_master_all = st.session_state['data_master_df'].copy()

            # Loop melalui baris yang diedit dan update di df_master_all
            for unique_id, edited_row in edited_df.iterrows():
                
                closed_date_val = str(edited_row['Closed Date']).strip()
                current_status = edited_row['Status'].upper().strip()
                
                # Update Status/Closed Date
                if current_status == 'OPEN':
                    df_master_all.loc[df_master_all['unique_id'] == unique_id, 'Closed Date'] = pd.NA
                elif current_status == 'CLOSED':
                    if closed_date_val == '' or pd.isna(closed_date_val):
                         st.error(f"Baris ID {unique_id}: Status CLOSED membutuhkan Tanggal Selesai (Closed Date).")
                         st.stop()
                    try:
                        datetime.strptime(closed_date_val, DATE_FORMAT)
                        df_master_all.loc[df_master_all['unique_id'] == unique_id, 'Closed Date'] = closed_date_val
                    except ValueError:
                        st.error(f"Baris ID {unique_id}: Format Tanggal Selesai (Closed Date) salah. Gunakan DD/MM/YYYY.")
                        st.stop()
                
                df_master_all.loc[df_master_all['unique_id'] == unique_id, 'Status'] = current_status
                    
                # Update Day & Issued Date
                day_val = str(edited_row['Day']).strip()
                try:
                    date_dt = datetime.strptime(day_val, DATE_FORMAT)
                    df_master_all.loc[df_master_all['unique_id'] == unique_id, 'Day'] = day_val
                    df_master_all.loc[df_master_all['unique_id'] == unique_id, 'Date_Day'] = date_dt
                    df_master_all.loc[df_master_all['unique_id'] == unique_id, 'Issued Date'] = day_val 
                except ValueError:
                    st.error(f"Baris ID {unique_id}: Format Tanggal Kejadian (Day) salah. Gunakan DD/MM/YYYY.")
                    st.stop()
                    
                # Update Kolom Lain
                for col in ['Vessel', 'Permasalahan', 'Penyelesaian', 'Unit', 'Keterangan']:
                    if col == 'Issued Date': continue 
                        
                    val = edited_row[col]
                    if col in ['Vessel', 'Unit']:
                        df_master_all.loc[df_master_all['unique_id'] == unique_id, col] = str(val).upper().strip()
                    else:
                        df_master_all.loc[df_master_all['unique_id'] == unique_id, col] = val
                        
            save_data(df_master_all) 
            st.success("✅ Data berhasil diperbarui!")
            time.sleep(1)
            st.rerun()

    # 2. Hapus Data (Ditempatkan di kolom terpisah, di samping tabel edit)
    st.markdown("---")
    st.subheader("🗑️ Hapus Laporan Aktif")
    st.warning("PERHATIAN: Penghapusan bersifat permanen. Klik tombol Hapus pada baris yang sesuai.")

    df_deletable = df_active.copy()
    
    # Hanya tampilkan kolom yang relevan untuk konfirmasi penghapusan
    df_deletable = df_deletable[['unique_id', 'Day', 'Unit', 'Permasalahan']].rename(columns={'unique_id': 'ID', 'Day': 'Tgl', 'Permasalahan': 'Detail Masalah'})
    
    # --- HEADER TABEL HAPUS ---
    col_id, col_masalah, col_tgl, col_unit, col_delete = st.columns([0.5, 3, 1, 1.5, 1.5])
    col_id.markdown('**ID**', unsafe_allow_html=True)
    col_masalah.markdown('**DETAIL MASALAH**', unsafe_allow_html=True)
    col_tgl.markdown('**TGL**', unsafe_allow_html=True)
    col_unit.markdown('**UNIT**', unsafe_allow_html=True)
    col_delete.markdown('**TINDAKAN**', unsafe_allow_html=True)
    st.markdown("---")
    
    # Loop untuk menampilkan setiap baris dengan tombol hapus
    for i, row in df_deletable.iterrows():
        col_id, col_masalah, col_tgl, col_unit, col_delete = st.columns([0.5, 3, 1, 1.5, 1.5])
        
        col_id.write(f"**{int(row['ID'])}**")
        col_tgl.write(row['Tgl'])
        col_unit.write(row['Unit'])
        
        # Tampilkan detail masalah yang dipotong
        problem_detail = str(row['Detail Masalah'])
        if len(problem_detail) > 100:
            problem_detail = problem_detail[:97] + '...'
        col_masalah.write(problem_detail)
        
        # Tombol Hapus
        if col_delete.button("Hapus", key=f"delete_btn_{int(row['ID'])}", use_container_width=True):
             # Logika konfirmasi dan hapus
             delete_data(int(row['ID']))

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
        
        # Hapus kolom unique_id, Date_Day sebelum ditampilkan
        df_closed_display = df_closed.drop(columns=['Date_Day', 'unique_id'], errors='ignore')
        
        st.dataframe(df_closed_display, 
                     hide_index=True, 
                     use_container_width=True,
                     column_order=COLUMNS,
                     )

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
DATA_FILE = 'notulensi_kerusakan.csv'
DATE_FORMAT = '%d/%m/%Y'

# --- FUNGSI PEMBANTU UNTUK MEMUAT DAN MEMPROSES DATA CSV ---
@st.cache_data(ttl=3600) 
def get_processed_data_for_display(selected_year=None):
    """Memuat, memproses, dan memfilter data CSV untuk mendapatkan statistik per kapal dan global."""
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(), 0, 0, []

    try:
        df = pd.read_csv(DATA_FILE)
    except Exception:
        return pd.DataFrame(), 0, 0, []

    # Data cleaning dan preprocessing
    df['Vessel'] = df['Vessel'].astype(str).str.upper().str.strip()
    df['Status'] = df.get('Status', 'OPEN').astype(str).str.upper().str.strip()
    df['Issued Date'] = df.get('Issued Date', pd.NA).astype(str).str.strip()
    
    # Konversi tanggal Issued Date 
    df['Date_Issued'] = pd.to_datetime(df['Issued Date'], format=DATE_FORMAT, errors='coerce')
    
    # Filter baris yang tidak memiliki kode kapal atau tanggal invalid
    df = df.dropna(subset=['Vessel', 'Date_Issued'])
    df = df[df['Vessel'] != 'NAN']

    # Dapatkan tahun-tahun yang valid
    valid_years = df['Date_Issued'].dt.year.dropna().astype(int).unique()

    # Terapkan filter tahun
    df_filtered = df.copy()
    if selected_year and selected_year != 'All':
        df_filtered = df_filtered[df_filtered['Date_Issued'].dt.year == int(selected_year)]

    # 1. Hitung TOTAL GLOBAL (setelah filter tahun)
    total_open_global = (df_filtered['Status'] == 'OPEN').sum()
    total_closed_global = (df_filtered['Status'] == 'CLOSED').sum()

    # 2. Hitung statistik per kapal
    stats = df_filtered.groupby('Vessel')['Status'].value_counts().unstack(fill_value=0)
    
    stats['OPEN'] = stats.get('OPEN', 0)
    stats['CLOSED'] = stats.get('CLOSED', 0)
    
    last_inspection = df.groupby('Vessel')['Date_Issued'].max().dt.strftime(DATE_FORMAT)

    result = stats[['OPEN', 'CLOSED']].reset_index()
    result['last_inspection'] = result['Vessel'].map(last_inspection)
    
    return result, total_open_global, total_closed_global, valid_years.tolist()


# --- FUNGSI UTAMA UNTUK DATA CARD ---
def get_ship_list(df_stats):
    """Mengambil data status Open/Closed NC secara dinamis dari DataFrame statistik."""
    ship_list = []
    if not df_stats.empty:
        for _, row in df_stats.iterrows():
            ship_list.append({
                "code": row['Vessel'],
                "open_nc": int(row['OPEN']),
                "closed_nc": int(row['CLOSED']),
                "last_inspection": row['last_inspection'] if pd.notna(row['last_inspection']) else 'N/A'
            })
    return ship_list


# --- FUNGSI DISPLAY CARD DENGAN HTML/CSS KUSTOM ---
def display_ship_cards(ship_list):
    """Menampilkan daftar kapal dalam format card kustom."""
    st.markdown("""
        <style>
            /* Global Card Container */
            .card-container {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                padding: 10px;
            }
            .ship-card-content {
                background-color: #FFFFFF; 
                border-radius: 12px 12px 0 0;
                padding: 20px;
                width: 100% !important; 
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15); 
                border-top: 5px solid #005691;
                transition: transform 0.2s;
            }
            .stButton>button {
                margin-top: 0px; 
                height: 40px;
                background-color: #005691;
                color: white;
                border: none;
                border-radius: 0 0 12px 12px;
            }
            .stButton>button:hover {
                background-color: #004070;
            }
            .ship-code-display {
                font-size: 1.5em;
                font-weight: bold;
                color: #111111;
                margin-bottom: 5px;
            }
            .nc-grid {
                display: flex;
                justify-content: space-between;
                margin-top: 15px;
            }
            .nc-item {
                text-align: center;
            }
            .nc-value-open {
                font-size: 1.8em;
                font-weight: bold;
                color: #FF4B4B;
            }
            .nc-value-closed {
                font-size: 1.8em;
                font-weight: bold;
                color: #00BA38;
            }
            .last-inspection {
                font-size: 0.8em;
                color: #777777;
                margin-top: 15px;
                border-top: 1px solid #DDDDDD; 
                padding-top: 8px;
            }
            .global-metric-box {
                background-color: #FFFFFF;
                border-radius: 12px;
                padding: 15px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); 
            }
            .global-value-open {
                font-size: 2em;
                font-weight: bold;
                color: #FF4B4B;
            }
            .global-value-closed {
                font-size: 2em;
                font-weight: bold;
                color: #00BA38;
            }
            .global-value-total {
                font-size: 2em;
                font-weight: bold;
                color: #005691; 
            }
            .global-label {
                font-size: 0.9em;
                color: #555555;
            }
        </style>
    """, unsafe_allow_html=True)

    ship_list.sort(key=lambda x: x['code']) 
    num_cols = 3 
    cols = st.columns(num_cols)
    
    for i, ship in enumerate(ship_list):
        col = cols[i % num_cols]
        
        ship_name = ship['code']

        with col:
            card_html = f"""
                <div class="ship-card-content">
                    <div class="ship-code-display">{ship_name}</div>
                    <div style="font-size: 0.9em; color: #777;">Kode Kapal: {ship['code']}</div>
                    <div class="nc-grid">
                        <div class="nc-item">
                            <div class="nc-value-open">{ship['open_nc']}</div>
                            <div class="nc-label">Laporan Open</div>
                        </div>
                        <div class="nc-item">
                            <div class="nc-value-closed">{ship['closed_nc']}</div>
                            <div class="nc-label">Laporan Closed</div>
                        </div>
                    </div>
                    <div class="last-inspection">
                        Terakhir Update: {ship['last_inspection']}
                    </div>
                </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            if st.button(f"Lihat Detail {ship['code']}", key=f"btn_{ship['code']}", use_container_width=True):
                 st.session_state.selected_ship_code = ship['code']
                 st.session_state.selected_ship_name = ship_name 
                 st.switch_page("pages/2_Laporan_Aktif_&_Input.py")
                 
            st.markdown(f'<div style="margin-bottom: 20px;"></div>', unsafe_allow_html=True)


# --- MAIN LOGIC ---
st.sidebar.success(f"Selamat Datang, {st.session_state.username}!")
st.markdown("# Homepage")
st.markdown("## Laporan Kerusakan Kapal")
st.write("---")

# 💅 CSS tambahan buat tombol Export CSV biar sejajar & warna seragam
st.markdown("""
    <style>
        div[data-testid="stDownloadButton"] > button {
            height: 38px;
            margin-top: 22px;
            background-color: #005691 !important;
            color: white !important;
            border: none;
            border-radius: 6px;
        }
        div[data-testid="stDownloadButton"] > button:hover {
            background-color: #004070 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- FILTER TAHUN & EXPORT BUTTON ---
df_stats_temp, _, _, valid_years_list_temp = get_processed_data_for_display()
year_options = ['All'] + sorted(valid_years_list_temp, reverse=True)

col_filter, col_export = st.columns([3, 1])

with col_filter:
    selected_year = st.selectbox("Filter Tahun Kejadian (Global)", year_options, key="filter_tahun_homepage")

with col_export:
    try:
        with open(DATA_FILE, "rb") as file:
            st.download_button(
                label="⬇️ Export CSV",
                data=file,
                file_name="notulensi_kerusakan.csv",
                mime="text/csv",
                use_container_width=True
            )
    except FileNotFoundError:
        st.warning("File CSV belum tersedia", icon="⚠️")

# --- LOAD DATA ---
df_stats, total_open, total_closed, _ = get_processed_data_for_display(selected_year)

# --- MENAMPILKAN METRIK GLOBAL ---
st.markdown("### Ringkasan Status Global")

col_open, col_closed, col_total = st.columns(3)

with col_open:
    st.markdown(f"""
        <div class="global-metric-box" style="border-top: 5px solid #FF4B4B;">
            <div class="global-label">TOTAL LAPORAN OPEN</div>
            <div class="global-value-open">{total_open}</div>
        </div>
    """, unsafe_allow_html=True)

with col_closed:
    st.markdown(f"""
        <div class="global-metric-box" style="border-top: 5px solid #00BA38;">
            <div class="global-label">TOTAL LAPORAN CLOSED</div>
            <div class="global-value-closed">{total_closed}</div>
        </div>
    """, unsafe_allow_html=True)

with col_total:
    st.markdown(f"""
        <div class="global-metric-box" style="border-top: 5px solid #005691;">
            <div class="global-label">TOTAL SELURUH LAPORAN</div>
            <div class="global-value-total">{total_open + total_closed}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- TAMPILKAN CARD KAPAL ---
st.markdown("### Pilih Kapal untuk Laporan Detail")

if df_stats.empty:
    st.warning("Tidak ada data kapal yang valid ditemukan untuk filter ini.")
else:
    final_ship_list = get_ship_list(df_stats)
    display_ship_cards(final_ship_list)

st.info("Silakan pilih salah satu kapal di atas untuk melihat atau menginput laporan kerusakan.")

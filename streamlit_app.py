import streamlit as st
import pandas as pd
from datetime import datetime
import os
import numpy as np 

# --- Konfigurasi ---
USERNAME = "staffdpagls" 
PASSWORD = "gls@123" 
DATA_FILE = 'notulensi_kerusakan.csv'
DATE_FORMAT = '%d/%m/%Y'

# st.set_page_config tetap dipertahankan
st.set_page_config(
    page_title="Sistem Laporan Kerusakan Kapal",
    layout="wide"
)

# --- Inisialisasi Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'selected_ship_code' not in st.session_state:
    st.session_state.selected_ship_code = None
    
# Inisialisasi data master
if 'data_master_df' not in st.session_state:
    COLUMNS = ['Day', 'Vessel', 'Permasalahan', 'Penyelesaian', 'Unit', 'Issued Date', 'Closed Date', 'Keterangan', 'Status'] 
    st.session_state['data_master_df'] = pd.DataFrame(columns=COLUMNS + ['Date_Day'])


# --- FUNGSI PEMBANTU UNTUK MEMUAT DAN MEMPROSES DATA CSV ---
@st.cache_data(ttl=3600) 
def get_processed_data_for_mock_ship_data():
    """Memuat dan memproses data CSV untuk mendapatkan statistik per kapal."""
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(), 0, 0 # Mengembalikan df, total_open, total_closed

    try:
        df = pd.read_csv(DATA_FILE)
    except Exception:
        return pd.DataFrame(), 0, 0

    # Data cleaning dan preprocessing
    df['Vessel'] = df['Vessel'].astype(str).str.upper().str.strip()
    df['Status'] = df.get('Status', 'OPEN').astype(str).str.upper().str.strip()
    df['Issued Date'] = df.get('Issued Date', pd.NA).astype(str).str.strip()
    
    # Konversi tanggal Issued Date 
    df['Date_Issued'] = pd.to_datetime(df['Issued Date'], format=DATE_FORMAT, errors='coerce')
    
    # Filter baris yang tidak memiliki kode kapal
    df = df.dropna(subset=['Vessel'])
    df = df[df['Vessel'] != 'NAN']

    # 1. Hitung TOTAL GLOBAL
    total_open_global = (df['Status'] == 'OPEN').sum()
    total_closed_global = (df['Status'] == 'CLOSED').sum()

    # 2. Hitung statistik per kapal
    stats = df.groupby('Vessel')['Status'].value_counts().unstack(fill_value=0)
    
    stats['OPEN'] = stats.get('OPEN', 0)
    stats['CLOSED'] = stats.get('CLOSED', 0)
    
    last_inspection = df.groupby('Vessel')['Date_Issued'].max().dt.strftime(DATE_FORMAT)

    result = stats[['OPEN', 'CLOSED']].reset_index()
    result['last_inspection'] = result['Vessel'].map(last_inspection)
    
    return result, total_open_global, total_closed_global


# --- FUNGSI UTAMA UNTUK DATA CARD ---
def get_ship_data():
    """Mengambil data status Open/Closed NC secara dinamis dari CSV."""
    df_stats, _, _ = get_processed_data_for_mock_ship_data()
    
    ship_list = []
    if not df_stats.empty:
        for _, row in df_stats.iterrows():
            ship_list.append({
                "code": row['Vessel'],
                "open_nc": int(row['OPEN']),
                "closed_nc": int(row['CLOSED']),
                "last_inspection": row['last_inspection']
            })
    return ship_list

# --- FUNGSI DISPLAY CARD DENGAN HTML/CSS KUSTOM ---
def display_ship_cards(ship_list):
    """Menampilkan daftar kapal dalam format card kustom."""
    st.markdown("""
        <style>
            /* Mengubah tema keseluruhan ke light mode */
            .stApp {
                background-color: #F0F2F6; /* Light Grayish Background */
            }

            /* Global Card Container */
            .card-container {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                padding: 10px;
            }
            /* Styling untuk Global Metric Box (Background Putih) */
            .global-metric-box {
                background-color: #FFFFFF; /* White Background */
                border-radius: 12px;
                padding: 15px;
                flex: 1;
                text-align: center;
                /* Shadow tipis */
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); 
            }
            .global-value-open {
                font-size: 2em;
                font-weight: bold;
                color: #FF4B4B; /* Red for Open */
            }
            .global-value-closed {
                font-size: 2em;
                font-weight: bold;
                color: #00BA38; /* Green for Closed */
            }
            .global-label {
                font-size: 0.9em;
                color: #555555; /* Darker text */
            }
            /* Ship Card Styling (Background Putih) */
            .ship-card-content {
                background-color: #FFFFFF; /* White Background */
                /* Hapus radius bawah agar menyatu dengan tombol */
                border-radius: 12px 12px 0 0; 
                padding: 20px;
                width: 100% !important; 
                /* Shadow yang lebih terlihat */
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15); 
                border-top: 5px solid #005691; /* Dark Blue Top Border */
                transition: transform 0.2s;
            }
            .ship-card-content:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.25); /* Shadow lebih dalam saat hover */
            }
            .ship-code-display {
                font-size: 1.5em;
                font-weight: bold;
                color: #111111; /* Black text */
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
                border-top: 1px solid #DDDDDD; /* Light separator */
                padding-top: 8px;
            }
            /* Styling Button agar menyatu dengan card */
            div.stButton {
                /* Menghilangkan margin vertikal default Streamlit */
                margin-top: 0px !important; 
                margin-bottom: 0px !important;
                /* Menyatukan Card + Button menjadi 1 unit box shadow */
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15); 
                border-radius: 0 0 12px 12px;
                transition: box-shadow 0.2s;
            }
            /* Styling Button (Footer Biru) */
            .stButton>button {
                margin-top: 0px; 
                height: 40px;
                background-color: #005691; /* Dark Blue button */
                color: white;
                border: none;
                /* Berikan radius hanya di bagian bawah */
                border-radius: 0 0 12px 12px; 
                width: 100%; 
                transition: background-color 0.2s;
                /* Hapus shadow dari tombol agar shadow utama dari card yang terlihat */
                box-shadow: none !important;
                /* Jarak antar card */
                margin-bottom: 25px; 
            }
            .stButton>button:hover {
                background-color: #004070;
            }
            /* Menggabungkan transform hover di Card Content dan Button Container */
            .stButton:hover {
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.25);
                transform: translateY(-5px);
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
            # 1. Tampilkan HTML Card Content
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
            
            # 2. Tambahkan Tombol untuk Navigasi (Menyatu dengan Card)
            if st.button(f"Lihat Detail {ship['code']}", key=f"btn_{ship['code']}", use_container_width=True):
                 st.session_state.selected_ship_code = ship['code']
                 st.session_state.selected_ship_name = ship_name 
                 st.switch_page("pages/1_Laporan_Aktif_&_Input.py")
                 
            # Hapus st.markdown("<br>") karena sudah dihandle oleh margin-bottom di CSS button


# --- MAIN LOGIC ---
if not st.session_state.logged_in:
    st.title("🚢 Login Sistem Laporan Kerusakan")
    
    with st.form("login_form"): 
        st.subheader("Masukkan ID dan Password Anda")
        username_input = st.text_input("ID Pengguna", key="user_input")
        password_input = st.text_input("Password", type="password", key="pass_input")
        submitted = st.form_submit_button("Login")

        if submitted:
            if username_input == USERNAME and password_input == PASSWORD:
                st.session_state.logged_in = True
                st.session_state.username = username_input
                st.success("Login Berhasil! Silakan pilih kapal.")
                st.rerun() 
            else:
                st.error("ID atau Password salah.")
else:
    st.sidebar.success(f"Selamat Datang, {st.session_state.username}!")
    
    # *** TRIK UNTUK MENGUBAH JUDUL SIDEBAR MENJADI "Homepage" ***
    # Menggunakan st.markdown("# Judul") di awal halaman root akan menimpa nama file di sidebar.
    st.markdown("# Homepage") 
    
    # Judul yang tampil di Body halaman
    st.markdown("## Pilih Kapal untuk Inspeksi")
    
    ship_data, total_open, total_closed = get_processed_data_for_mock_ship_data()
    
    # --- MENAMPILKAN METRIK GLOBAL ---
    st.markdown("### Ringkasan Status Global")
    
    col_open, col_closed, col_total = st.columns(3)
    
    with col_open:
        st.markdown(f"""
            <div class="global-metric-box">
                <div class="global-label">TOTAL LAPORAN OPEN</div>
                <div class="global-value-open">{total_open}</div>
            </div>
        """, unsafe_allow_html=True)

    with col_closed:
        st.markdown(f"""
            <div class="global-metric-box">
                <div class="global-label">TOTAL LAPORAN CLOSED</div>
                <div class="global-value-closed">{total_closed}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col_total:
        st.markdown(f"""
            <div class="global-metric-box" style="border-top: 5px solid #AAAAAA; color: #111111;">
                <div class="global-label">TOTAL SELURUH LAPORAN</div>
                <div style="font-size: 2em; font-weight: bold;">{total_open + total_closed}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    # ----------------------------------------
    
    if ship_data.empty:
        st.warning("Tidak ada data kapal yang valid ditemukan di file CSV.")
    else:
        # Pindahkan logika konversi ke list ke sini agar tidak memanggil cache ulang
        final_ship_list = get_ship_data()
        display_ship_cards(final_ship_list)

    st.info("Silakan pilih salah satu kapal di atas untuk melihat atau menginput laporan kerusakan.")

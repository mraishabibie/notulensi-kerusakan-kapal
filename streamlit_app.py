import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- Konfigurasi ---
USERNAME = "staffdpagls" 
PASSWORD = "gls@123" 
DATA_FILE = 'notulensi_kerusakan.csv'
DATE_FORMAT = '%d/%m/%Y'

st.set_page_config(
    page_title="Sistem Laporan Kerusakan Kapal",
    layout="wide"
)

# --- Inisialisasi Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'selected_ship_code' not in st.session_state:
    st.session_state.selected_ship_code = None
    
# Inisialisasi data master (Penting untuk Cache Lintas Halaman)
if 'data_master_df' not in st.session_state:
    COLUMNS = ['Day', 'Vessel', 'Permasalahan', 'Penyelesaian', 'Unit', 'Issued Date', 'Closed Date', 'Keterangan', 'Status'] 
    st.session_state['data_master_df'] = pd.DataFrame(columns=COLUMNS + ['Date_Day'])


# --- MAIN LOGIC ---
if not st.session_state.logged_in:
    st.title("🚢 Login Sistem Laporan Kerusakan")
    
    # --- CSS Kustom untuk Tampilan Login ---
    st.markdown("""
        <style>
            .stApp {
                background-color: #F0F2F6; /* Light Grayish Background */
            }
            /* Menargetkan formulir login */
            .stForm {
                background-color: #FFFFFF;
                border-radius: 12px;
                padding: 30px;
                margin: 50px auto;
                width: 400px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); 
            }
            /* Tombol login */
            .stForm .stButton>button {
                background-color: #005691;
                color: white;
                border-radius: 8px;
                height: 40px;
                margin-top: 15px;
            }
            .stForm .stButton>button:hover {
                background-color: #004070;
            }
        </style>
    """, unsafe_allow_html=True)
    # ------------------------------------------

    with st.form("login_form"): 
        st.subheader("Masukkan ID dan Password Anda")
        username_input = st.text_input("ID Pengguna", key="user_input")
        password_input = st.text_input("Password", type="password", key="pass_input")
        submitted = st.form_submit_button("Login")

        if submitted:
            if username_input == USERNAME and password_input == PASSWORD:
                st.session_state.logged_in = True
                st.session_state.username = username_input
                st.success("Login Berhasil! Mengalihkan ke Homepage...")
                # PERBAIKAN PANGGILAN 1: Gunakan nama file tanpa ekstensi atau folder
                st.switch_page("1_Homepage") 
            else:
                st.error("ID atau Password salah.")
else:
    # Jika sudah login, langsung redirect ke Home
    # PERBAIKAN PANGGILAN 2: Gunakan nama file tanpa ekstensi atau folder
    st.switch_page("1_Homepage")

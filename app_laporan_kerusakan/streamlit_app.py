import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- Konfigurasi User Login Tunggal ---
USERNAME = "staffdpagls" 
PASSWORD = "gls@123" 

st.set_page_config(
    page_title="Sistem Laporan Kerusakan Kapal",
    layout="wide"
)

# Inisialisasi session state untuk status login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    
# Inisialisasi state untuk form input di halaman 1
if 'show_new_report_form_v2' not in st.session_state:
    st.session_state.show_new_report_form_v2 = False

# Inisialisasi data master (PENTING untuk konsistensi antar halaman)
if 'data_master_df' not in st.session_state:
    COLUMNS = ['Day', 'Vessel', 'Permasalahan', 'Penyelesaian', 'Unit', 'Issued Date', 'Closed Date', 'Keterangan', 'Status'] 
    st.session_state['data_master_df'] = pd.DataFrame(columns=COLUMNS + ['Date_Day'])


def check_login():
    """Fungsi untuk memproses form login."""
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
                st.success("Login Berhasil! Silakan pilih halaman di sidebar.")
                st.rerun() 
            else:
                st.error("ID atau Password salah.")

if not st.session_state.logged_in:
    check_login()
else:
    # Konten halaman setelah login
    st.sidebar.success(f"Selamat Datang, {st.session_state.username}!")
    st.write("# Selamat Datang di Sistem Notulensi Kapal ⚓")
    
    st.info("Login berhasil! Silakan klik tombol di bawah ini atau gunakan menu di sidebar untuk memulai.")
    
    col_btn_start, col_btn_spacer = st.columns([1, 4])
    
    with col_btn_start:
        # st.page_link sekarang akan tampil sebagai link biasa
        st.page_link("pages/1_Laporan_Aktif_&_Input.py", 
                     label="▶️ Mulai Input Laporan", 
                     use_container_width=True) 

    st.warning("Jika link di atas tidak berfungsi, silakan pilih **Laporan Aktif & Input** dari menu di sidebar kiri.")
import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- Konfigurasi ---
USERNAME = "staffdpagls" 
PASSWORD = "gls@123" 

st.set_page_config(
    page_title="Sistem Laporan Kerusakan Kapal",
    layout="wide"
)

# --- CSS untuk Memusatkan Konten ---
# Blok CSS ini juga memastikan judul 'Homepage' muncul di sidebar jika file utamanya adalah 'streamlit_app.py'
st.markdown("""
    <style>
    /* Styling untuk Container Login */
    .login-container {
        background-color: #FFFFFF;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        max-width: 450px; /* Batasi lebar kotak login */
        margin: 0 auto; /* Memusatkan secara horizontal jika tidak di dalam st.columns */
        margin-top: 10vh; /* Jarak dari atas layar */
    }
    .stForm {
        padding: 0; /* Hapus padding default form Streamlit */
    }
    </style>
""", unsafe_allow_html=True)
# ------------------------------------

# --- Inisialisasi Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'selected_ship_code' not in st.session_state:
    st.session_state.selected_ship_code = None
    
# --- MAIN LOGIC ---

# Trik untuk mengubah judul di sidebar (walaupun file ini hanya gerbang)
# Ini adalah judul yang akan dilihat user saat belum login
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    
    # 1. Gunakan kolom untuk memusatkan secara horizontal
    col1, col2, col3 = st.columns([1, 1.5, 1]) # 1.5 untuk kolom login, 1 dan 1 sebagai spacer
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        st.markdown('<h3 style="text-align: center; color: #005691;">🚢 Login Sistem Laporan</h3>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.subheader("Masukkan ID dan Password Anda")
            
            username_input = st.text_input("ID Pengguna", key="user_input")
            password_input = st.text_input("Password", type="password", key="pass_input")
            
            st.markdown("---")
            submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if username_input == USERNAME and password_input == PASSWORD:
                    st.session_state.logged_in = True
                    st.session_state.username = username_input
                    st.success("Login Berhasil! Mengalihkan ke Homepage...")
                    
                    # Dialihkan ke 1_Homepage.py
                    st.switch_page("1_Homepage") 
                    
                else:
                    st.error("ID atau Password salah.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
else:
    # Jika sudah login, langsung alihkan ke Homepage
    st.switch_page("1_Homepage")

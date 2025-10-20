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

# --- Inisialisasi Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'selected_ship_code' not in st.session_state:
    st.session_state.selected_ship_code = None
    
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
                st.success("Login Berhasil! Mengalihkan ke Homepage...")
                
                # PERBAIKAN: Dialihkan ke 1_Homepage
                # Streamlit akan mencari file 1_Homepage.py di folder pages/
                st.switch_page("1_Homepage") 
                
            else:
                st.error("ID atau Password salah.")
else:
    # Jika sudah login, langsung alihkan ke Homepage
    # PERBAIKAN: Dialihkan ke 1_Homepage
    st.switch_page("1_Homepage")

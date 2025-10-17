import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import numpy as np 

# --- Logika Autentikasi ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("Anda harus login untuk mengakses halaman ini. Silakan kembali ke halaman utama.")
    st.stop() 

# --- Konfigurasi ---
# Catatan: DATA_FILE sekarang berada di root repositori
DATA_FILE = 'notulensi_kerusakan.csv' 
COLUMNS = ['Day', 'Vessel', 'Permasalahan', 'Penyelesaian', 'Unit', 'Issued Date', 'Closed Date', 'Keterangan', 'Status'] 
DATE_FORMAT = '%d/%m/%Y'

# --- Fungsi Manajemen Data ---

@st.cache_data() 
def load_data_dashboard():
    """Memuat data dari CSV dan melakukan pre-processing untuk analisis."""
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
        except Exception as e:
            st.error(f"Gagal memuat file data '{DATA_FILE}'. Error: {e}")
            return pd.DataFrame()
            
        if 'Closed Date' not in df.columns:
             df['Closed Date'] = pd.NA
        
        df['Vessel'] = df['Vessel'].astype(str).str.upper().str.strip()
        df['Status'] = df.get('Status', 'OPEN').astype(str).str.upper()
        df['Unit'] = df['Unit'].astype(str).str.upper().str.strip().fillna('TIDAK DITENTUKAN')

        # Konversi tanggal
        df['Date_Day'] = pd.to_datetime(df['Day'], format=DATE_FORMAT, errors='coerce')
        df['Date_Issue'] = pd.to_datetime(df['Issued Date'], format=DATE_FORMAT, errors='coerce')
        df['Date_Closed'] = pd.to_datetime(df['Closed Date'], format=DATE_FORMAT, errors='coerce') 

        # Hapus baris di mana Date_Day tidak valid
        df = df.dropna(subset=['Date_Day']).reset_index(drop=True)
        
        # Hitung Resolution Time (hanya untuk yang sudah CLOSED dan tanggal valid)
        df['Resolution_Time_Days'] = (df['Date_Closed'] - df['Date_Issue']).dt.days
        # Bersihkan Resolution_Time_Days yang negatif (issue > closed)
        df.loc[df['Resolution_Time_Days'] < 0, 'Resolution_Time_Days'] = np.nan
        
        return df
    else:
        st.info(f"File data '{DATA_FILE}' tidak ditemukan di lokasi yang diharapkan. Pastikan sudah ada.")
        return pd.DataFrame()

# --- Tampilan Utama Dashboard ---

st.title("📊 Dashboard Analisis Kerusakan Kapal")

df = load_data_dashboard()

if df.empty:
    st.info("Data laporan kerusakan tidak ditemukan atau kosong. Silakan input data di halaman Laporan Aktif & Input.")
    st.stop() 

# --- Filter Global Tahun ---
valid_years = df['Date_Day'].dt.year.dropna().astype(int).unique()
year_options = ['All'] + sorted(valid_years.tolist(), reverse=True)

with st.container(border=True): 
    col_filter, col_spacer_top = st.columns([1, 4])
    
    with col_filter:
        selected_year = st.selectbox("Filter Tahun Kejadian", year_options, key="filter_tahun_dashboard")
        
    # Filter data utama
    df_filtered = df.copy()
    if selected_year and selected_year != 'All':
        df_filtered = df_filtered[df_filtered['Date_Day'].dt.year == int(selected_year)]

    # === Bagian 1: Ringkasan Metrik & KPI ===
    total = len(df_filtered)
    open_count = len(df_filtered[df_filtered['Status'] == 'OPEN'])
    closed_count = len(df_filtered[df_filtered['Status'] == 'CLOSED'])

    st.markdown("##### Ringkasan Status Laporan (Total: **{}**) - Data diambil per {}".format(total, datetime.now().strftime('%H:%M:%S')))
    
    col_open, col_closed, col_avg_days_res = st.columns(3) 

    col_open.metric("Laporan Masih OPEN", open_count)
    col_closed.metric("Laporan Sudah CLOSED", closed_count)
    
    df_closed = df_filtered[df_filtered['Status'] == 'CLOSED'].copy()
    
    # Hitung Avg. Waktu Penyelesaian Global (MTTR Global)
    if not df_closed.empty and df_closed['Resolution_Time_Days'].notna().any():
        avg_res_time = df_closed[df_closed['Resolution_Time_Days'] >= 0]['Resolution_Time_Days'].mean() 
        col_avg_days_res.metric("Avg. Waktu Penyelesaian (MTTR)", f"{avg_res_time:,.1f} Hari")
    else:
        col_avg_days_res.metric("Avg. Waktu Penyelesaian (MTTR)", "N/A")

st.markdown("---")

# =========================================================
# === Bagian 2: Analisis Detail Menggunakan Tabs ===
# =========================================================

tab_unit, tab_vessel, tab_time, tab_kpi = st.tabs(["📊 Analisis Unit/Sistem", "⚓ Kinerja Kapal", "📈 Tren Kerusakan", "🏆 Metrik Keandalan (MTBF/MTTR)"])

with tab_unit:
    st.subheader("Penyebaran Kerusakan berdasarkan Unit/Sistem")
    
    col_bar, col_spacer, col_pie = st.columns([2, 0.1, 1])

    unit_counts = df_filtered['Unit'].value_counts().reset_index()
    unit_counts.columns = ['Unit', 'Jumlah Kerusakan']
    
    fig_unit_bar = px.bar(
        unit_counts.head(10).sort_values(by='Jumlah Kerusakan', ascending=True),
        x='Jumlah Kerusakan',
        y='Unit', 
        title='Top 10 Unit Paling Bermasalah',
        color='Jumlah Kerusakan',
        color_continuous_scale=px.colors.sequential.Sunset,
        orientation='h'
    )
    fig_unit_bar.update_layout(xaxis_title="Jumlah Kerusakan", yaxis_title="")
    col_bar.plotly_chart(fig_unit_bar, use_container_width=True)
    
    top_units = unit_counts['Unit'].head(5).tolist()
    if top_units:
        df_top_unit = df_filtered[df_filtered['Unit'].isin(top_units)]
        
        status_counts_top_unit = df_top_unit['Status'].value_counts().reset_index()
        status_counts_top_unit.columns = ['Status', 'Count']
        
        fig_unit_pie = px.pie(
            status_counts_top_unit,
            values='Count',
            names='Status',
            title=f'Status Laporan pada Top {len(top_units)} Unit',
            hole=0.3,
            color_discrete_map={'OPEN':'red', 'CLOSED':'green'}
        )
        col_pie.plotly_chart(fig_unit_pie, use_container_width=True)
    else:
        col_pie.info("Tidak cukup data untuk analisis Top Unit.")


with tab_vessel:
    st.subheader("Analisis Kinerja Kerusakan per Kapal")

    vessel_counts = df_filtered['Vessel'].value_counts().reset_index()
    vessel_counts.columns = ['Vessel', 'Total Kerusakan']
    
    fig_vessel_bar = px.bar(
        vessel_counts.sort_values(by='Total Kerusakan', ascending=True),
        x='Total Kerusakan',
        y='Vessel',
        title='Total Kerusakan Berdasarkan Kapal',
        color='Total Kerusakan',
        color_continuous_scale=px.colors.sequential.Viridis,
        orientation='h'
    )
    fig_vessel_bar.update_layout(xaxis_title="Jumlah Kerusakan", yaxis_title="")
    st.plotly_chart(fig_vessel_bar, use_container_width=True)

    st.markdown("##### Laporan OPEN Terbanyak per Kapal")
    df_vessel_open = df_filtered[df_filtered['Status'] == 'OPEN']
    vessel_open_counts = df_vessel_open.groupby('Vessel').size().sort_values(ascending=False).reset_index(name='Jumlah OPEN')
    
    st.data_editor(
        vessel_open_counts,
        column_config={
            "Jumlah OPEN": st.column_config.NumberColumn(
                "Jumlah OPEN",
                format="%d", 
                help="Total laporan yang masih OPEN",
                width="small" 
            )
        },
        column_order=['Vessel', 'Jumlah OPEN'],
        hide_index=True,
        use_container_width=True,
        disabled=True 
    )


with tab_time:
    st.subheader("Tren Laporan Kerusakan dari Waktu ke Waktu")
    
    df_filtered['Month'] = df_filtered['Date_Day'].dt.to_period('M')
    
    monthly_trend = df_filtered.groupby(['Month', 'Status']).size().reset_index(name='Jumlah')
    monthly_trend['Month'] = monthly_trend['Month'].astype(str)
    
    fig_trend = px.line(
        monthly_trend,
        x='Month',
        y='Jumlah',
        color='Status',
        title='Tren Laporan OPEN vs CLOSED per Bulan',
        markers=True,
        color_discrete_map={'OPEN':'red', 'CLOSED':'green'}
    )
    fig_trend.update_layout(xaxis_title="Bulan", yaxis_title="Jumlah Laporan")
    st.plotly_chart(fig_trend, use_container_width=True)
    
    st.markdown("##### Timeline 15 Permasalahan Aktif (OPEN) Terlama")
    
    df_open_timeline = df_filtered[df_filtered['Status'] == 'OPEN'].copy()
    
    if not df_open_timeline.empty:
        df_open_timeline['Duration'] = (datetime.now() - df_open_timeline['Date_Day']).dt.days
        df_open_timeline = df_open_timeline.sort_values('Duration', ascending=False).head(15).copy()
        
        df_open_timeline['Current_Time'] = datetime.now()
        
        df_open_timeline['Label'] = df_open_timeline['Vessel'] + ' - ' + df_open_timeline['Permasalahan'].str.slice(0, 30) + '...'

        fig_timeline = px.timeline(
            df_open_timeline,
            x_start="Date_Day",
            x_end="Current_Time", 
            y="Label",
            color="Vessel",
            title="Timeline Durasi 15 Laporan OPEN Terlama",
            text="Duration"
        )
        fig_timeline.update_yaxes(autorange="reversed") 
        fig_timeline.update_traces(textposition='inside', marker_line_width=0, opacity=0.8) 
        fig_timeline.update_layout(xaxis_title="Tanggal", yaxis_title="")
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("Tidak ada laporan yang berstatus OPEN.")
        
        
with tab_kpi:
    st.subheader("🏆 Metrik Keandalan Unit (MTBF & MTTR)")
    
    if df_filtered.empty:
        st.info("Data tidak cukup untuk menghitung metrik keandalan.")
    else:
        
        # --- PERHITUNGAN MTBF (Mean Time Between Failures) ---
        start_date = df_filtered['Date_Day'].min()
        end_date = datetime.now()
        total_period_days = (end_date - start_date).days
        
        if total_period_days <= 0:
            st.warning("Periode data terlalu singkat untuk analisis MTBF.")
        else:
            # Hitung Jumlah Kegagalan (Failure Count) per Unit
            failure_counts = df_filtered.groupby('Unit').size().reset_index(name='Jumlah Kerusakan')
            
            # Hitung MTBF (Hari/Kegagalan)
            failure_counts['MTBF (Hari)'] = total_period_days / failure_counts['Jumlah Kerusakan']
            
            
            # --- PERHITUNGAN MTTR (Mean Time to Repair) ---
            # Hanya gunakan data yang sudah CLOSED
            df_closed_mttr = df_filtered[df_filtered['Status'] == 'CLOSED'].copy()

            if not df_closed_mttr.empty:
                # Hitung rata-rata Resolution_Time_Days per Unit
                mttr_unit = df_closed_mttr.groupby('Unit')['Resolution_Time_Days'].mean().reset_index(name='MTTR (Hari)')
                
                # Gabungkan MTBF dan MTTR
                reliability_metrics = pd.merge(failure_counts, mttr_unit, on='Unit', how='left').fillna({'MTTR (Hari)': np.nan})
                
                # Format dan sort berdasarkan MTBF Terendah (paling tidak andal)
                mtbf_mttr_display = reliability_metrics.sort_values(by='MTBF (Hari)', ascending=True).reset_index(drop=True)

                st.info(f"Analisis MTBF dilakukan selama periode **{total_period_days:,.0f} Hari** (dari {start_date.strftime('%d/%m/%Y')} hingga Hari Ini). MTTR hanya dihitung dari laporan yang sudah CLOSED.")

                st.markdown("##### 1. Keandalan dan Efisiensi Perbaikan per Unit")
                
                # Tampilkan tabel gabungan MTBF dan MTTR
                st.data_editor(
                    mtbf_mttr_display,
                    column_config={
                        "MTBF (Hari)": st.column_config.NumberColumn(
                            "MTBF (Keandalan)",
                            format="%.1f",
                            help="Rata-rata Hari Kalender antar kerusakan (Semakin Kecil, Semakin Tidak Andal)"
                        ),
                        "MTTR (Hari)": st.column_config.NumberColumn(
                            "MTTR (Perbaikan)",
                            format="%.1f",
                            help="Rata-rata Waktu yang dibutuhkan untuk menutup laporan (Semakin Besar, Semakin Lambat Perbaikan)"
                        ),
                        "Jumlah Kerusakan": st.column_config.NumberColumn(
                            "Kerusakan",
                            format="%d",
                            width="small"
                        )
                    },
                    column_order=['Unit', 'Jumlah Kerusakan', 'MTBF (Hari)', 'MTTR (Hari)'],
                    hide_index=True,
                    use_container_width=True,
                    disabled=True
                )
            else:
                st.warning("Tidak ada laporan yang berstatus CLOSED, sehingga MTTR per Unit tidak dapat dihitung.")

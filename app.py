from datetime import datetime
import pandas as pd
from supabase import create_client
import streamlit as st

# 1. Konfigurasi Halaman Dashboard
st.set_page_config(
    page_title="Monitoring Gempa Real-time BMKG",
    page_icon="🌋",
    layout="wide",
)

waktu = datetime.now().date()
st.title(f"🌋 Dashboard Monitoring Gempa Terkini Indonesia ({waktu})")
st.markdown(
    "Data ini diambil langsung dari API BMKG, diproses melalui pipeline ETL, dan disimpan di **PostgreSQL Cloud Data Warehouse via Supabase**."
)
st.write("---")

# 2. EXTRACT: Mengambil data dari Supabase Cloud secara aman via st.secrets
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


@st.cache_data
def load_data_from_supabase():
    # Inisialisasi client Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Ambil data dari tabel cloud
    response = supabase.table("info_gempa").select("*").execute()

    # Ubah response JSON menjadi Pandas DataFrame
    df_cloud = pd.DataFrame(response.data)
    return df_cloud


# Ambil dataframe dari fungsi cache
df = load_data_from_supabase()

# Jika database kosong saat pertama kali run, berikan warning terarah
if df.empty:
    st.warning(
        "Database Cloud Supabase masih kosong. Pastikan kamu sudah menjalankan skrip `etl.py` terlebih dahulu di terminal laptopmu."
    )
    st.stop()

# 3. TRANSFORM (Logika Pengolahan Grafik)
df["waktu_gempa"] = pd.to_datetime(df["waktu_gempa"])
df["tanggal"] = df["waktu_gempa"].dt.date

df_tren = df.groupby("tanggal").size().reset_index(name="jumlah_gempa")
df_tren["jumlah_gempa"] = df_tren["jumlah_gempa"].astype(int)
df_tren = df_tren.sort_values("tanggal")


# 4. VISUALIZATION: Menyusun Komponen Dashboard (5 Kolom Metrik Utama)
kolom1, kolom2, kolom3, kolom4, kolom5 = st.columns(5)

with kolom1:
    total_gempa = len(df)
    st.metric(label="Total Gempa Terpantau", value=f"{total_gempa} Kejadian")

with kolom2:
    max_magnitude = df["magnitudo"].max()
    st.metric(
        label="Magnitudo Tertinggi",
        value=f"{max_magnitude} SR",
        delta="Perlu Waspada",
        delta_color="inverse",
    )

with kolom3:
    avg_kedalaman = round(df["kedalaman_km"].mean(), 1)
    st.metric(label="Rata-rata Kedalaman", value=f"{avg_kedalaman} Km")

with kolom4:
    min_kedalaman = round(df["kedalaman_km"].min())
    st.metric(label="Minimal Kedalaman", value=f"{min_kedalaman} Km")

with kolom5:
    max_kedalaman = round(df["kedalaman_km"].max())
    st.metric(label="Maksimal Kedalaman", value=f"{max_kedalaman} Km")

st.write("---")


# 5. VISUALIZATION: Tata Letak (Peta, Tren Grafik, & Log Tabel)
kolom_peta, kolom_tren, kolom_data = st.columns([2, 1, 1])

with kolom_peta:
    st.subheader("📍 Peta Sebaran Titik Gempa")
    # Streamlit mendeteksi latitude & longitude langsung dari kolom database cloud
    st.map(df)

with kolom_tren:
    st.subheader("📊 Tren Harian")
    st.bar_chart(
        data=df_tren,
        x="tanggal",
        y="jumlah_gempa",
        width='stretch',
    )

with kolom_data:
    st.subheader("📋 Data Log Bersih")
    st.dataframe(
        df[["waktu_gempa", "magnitudo", "kedalaman_km", "wilayah"]],
        hide_index=True,
    )
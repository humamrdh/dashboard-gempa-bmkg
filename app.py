from datetime import datetime
import pandas as pd
import streamlit as st
from supabase import create_client

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


# Ditambahkan ttl=600 (10 menit) agar data otomatis ter-update jika database berubah
@st.cache_data(ttl=600)
def load_data_from_supabase():
    # Inisialisasi client Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Ambil data dari tabel cloud
    response = (
        supabase.table("info_gempa")
        .select("*")
        .order("waktu_gempa", desc=True)
        .limit(50)
        .execute()
    )
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

# 3. TRANSFORM & BINDING DATA
df["waktu_gempa"] = pd.to_datetime(df["waktu_gempa"])
df["tanggal"] = df["waktu_gempa"].dt.date

# PENTING: Pastikan nama kolom lat/lon sesuai dengan database kamu.
# Jika di database namanya 'lintang' dan 'bujur', aktifkan baris di bawah ini:
# df = df.rename(columns={"lintang": "latitude", "bujur": "longitude"})

# Logika Pengolahan Grafik Tren
df_tren = df.groupby("tanggal").size().reset_index(name="jumlah_gempa")
df_tren["jumlah_gempa"] = df_tren["jumlah_gempa"].astype(int)
df_tren = df_tren.sort_values("tanggal")


# 4. VISUALIZATION: Ringkasan Metrik Utama
kolom1, kolom2, kolom3, kolom4 = st.columns(4)

with kolom1:
    max_magnitude = df["magnitudo"].max()
    st.metric(
        label="💥 Magnitudo Tertinggi",
        value=f"{max_magnitude} SR",
        delta="Perlu Waspada" if max_magnitude >= 5.0 else "Kondisi Aman",
        delta_color="inverse" if max_magnitude >= 5.0 else "normal",
    )

with kolom2:
    avg_kedalaman = round(df["kedalaman_km"].mean(), 1)
    st.metric(label="📉 Rata-rata Kedalaman", value=f"{avg_kedalaman} Km")

with kolom3:
    min_kedalaman = round(df["kedalaman_km"].min())
    st.metric(label="🟢 Kedalaman Terpendek", value=f"{min_kedalaman} Km")

with kolom4:
    max_kedalaman = round(df["kedalaman_km"].max())
    st.metric(label="🔴 Kedalaman Terdalam", value=f"{max_kedalaman} Km")

st.write("---")


# 5. VISUALIZATION: Tata Letak (Peta Sebaran & Tren Grafik)
# Mengubah grid menjadi 2 kolom utama agar visualisasi peta dan grafik mendapatkan ruang maksimal
kolom_peta, kolom_tren = st.columns([3, 2])

with kolom_peta:
    st.subheader("🗺️ Peta Sebaran 50 Titik Gempa Terbaru")
    st.map(df)

with kolom_tren:
    st.subheader("📊 Tren Frekuensi Gempa Harian")
    st.bar_chart(
        data=df_tren,
        x="tanggal",
        y="jumlah_gempa",
    )

st.write("---")

# 6. VISUALIZATION: Tabel Data Log Terkini (Ditaruh di paling bawah secara penuh)
st.subheader("📋 Log Ringkas 20 Kejadian Gempa Terkini")
st.dataframe(
    df[["waktu_gempa", "magnitudo", "kedalaman_km", "wilayah"]].head(20),
    width="stretch",
    hide_index=True,
)

import pandas as pd
import requests
import os
from dotenv import load_dotenv
from supabase import create_client

# 1. MUAT FILE .ENV & KONEKSI KE SUPABASE
load_dotenv()

# Masukkan URL dan API Key anon
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Inisialisasi client supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=== Memulai Proses ETL Gempa BMKG ===")

try:
    # 2. EXTRACT: Ambil data .json dari API BMKG
    print("[1/4] Mengekstrak data dari API BMKG...")
    URL = "https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json"
    response = requests.get(URL, timeout=10)
    response.raise_for_status()    #Memastikan koneksi HTTP sukses

    # Memasukkan data masuk yang berbentuk .json menjadi DataFrame
    df_raw = pd.DataFrame(response.json()['infogempa']['gempa'])

    # 3. TRANSFORM: Pembersihan dan standarisasi tipe data sesuai kebutuhan
    print("[2/4] Melakukan transformasi data")
    df_raw['Jam_bersih'] = df_raw['Jam'].str.replace(" WIB", "", case=False).str.strip()
    df_raw['datetime_bersih'] = df_raw['Tanggal'] + " " + df_raw['Jam_bersih']
    df_raw['waktu_gempa'] = pd.to_datetime(df_raw['datetime_bersih'], format="%d %b %Y %H:%M:%S")
    df_raw['waktu_gempa'] = df_raw['waktu_gempa'].dt.strftime("%Y-%m-%d %H:%M:%S")     #Diubah format tanggalnya biar bisa masuk database
    df_raw['magnitudo'] = df_raw['Magnitude'].astype(float)
    df_raw['kedalaman_km'] = df_raw['Kedalaman'].str.replace(" km", "", case=False).str.strip().astype(int)

    #Menghapus ["LU", "LS"] di kolom Lintang & ["BT", "BB"] di kolom Bujur dengan membuat fungsi
    def penghapus(nilai, objek_yang_ingin_dihapus):
        angka_saja = float(nilai.split()[0])
        return -angka_saja if objek_yang_ingin_dihapus in nilai else angka_saja
    
    df_raw['latitude'] = df_raw['Lintang'].apply(lambda a: penghapus(a, "LS"))
    df_raw['longitude'] = df_raw['Bujur'].apply(lambda b: penghapus(b, "BB"))

    #Jika sudah selesai, copy DataFrame-nya & ambil kolom yang diperlukan
    df_bersih = df_raw[[
        "waktu_gempa", "magnitudo", "kedalaman_km", "latitude", "longitude", "Wilayah", "Potensi"
        ]].copy()
    df_bersih = df_bersih.rename(columns={"Wilayah": "wilayah", "Potensi": "potensi"})

    # 4. LOAD: Simpan data bersih ke database/data warehouse(Supabase)
    print("[3/4] Mengonversi data ke format JSON(dict)")
    masuk_database = df_bersih.to_dict(orient='records')    #Jadiin dictionary dulu
    
    print("[4/4] Mengirim data ke Supabase Cloud")
    response_cloud = supabase.table("info_gempa").upsert(masuk_database).execute()
    print("=== ETL Sukses, Data BMKG telah ter-update di Supabase Cloud ===")
except requests.exceptions.RequestException as req_err:
    print(f"[ERROR] Gagal terhubung ke API BMKG: {req_err}")
except Exception as e:
    print(f"[ERROR] Terjadi kesalahan dalam proses ETL: {e}")
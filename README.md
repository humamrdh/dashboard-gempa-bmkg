# 🌋 End-to-End Earthquake Monitoring Dashboard (BMKG x Supabase)

Dashboard interaktif yang dirancang untuk mengekstrak, mengolah, dan memvisualisasikan data aktivitas gempa bumi real-time di Indonesia menggunakan data resmi dari BMKG. 

Proyek ini menerapkan arsitektur pemisahan *Compute* (ETL Pipeline) dan *Serving* (Dashboard Frontend) untuk menghemat *resource* dan memastikan performa aplikasi tetap optimal.

---

## 🛠️ Tech Stack & Alat
*   **Bahasa Pemrograman:** Python 3.14+
*   **Database & Cloud Storage:** Supabase (PostgreSQL)
*   **Pembersihan & Manipulasi Data:** Pandas, Requests
*   **Visualisasi & Aplikasi Web:** Streamlit
*   **Manajemen Environment & Keamanan:** Python-dotenv, Git

---

## 🏗️ Desain Arsitektur & Alur Data

Proyek ini dibangun dengan prinsip arsitektur data modern:

1.  **Extract & Transform (Local Backend):**
    *   Skrip `etl.py` menembak API BMKG untuk mengambil data gempa terkini dalam format XML/JSON.
    *   Menggunakan **Pandas** untuk membersihkan tipe data, memisahkan teks koordinat menjadi nilai lintang/bujur numerik, dan membuang duplikasi data.
2.  **Load (Cloud Data Warehouse):**
    *   Data yang telah bersih dikirim ke **Supabase** menggunakan metode `.upsert()`. Pendekatan ini memastikan data baru langsung masuk, sementara data lama yang sudah ada tidak akan terduplikasi berdasarkan *primary key* waktu gempa.
3.  **Data Serving (Cloud Production):**
    *   Aplikasi web `app.py` di-deploy secara publik di **Streamlit Community Cloud**.
    *   Setiap kali pengguna membuka dashboard, Streamlit langsung menarik data bersih dari Supabase secara instan tanpa perlu membebani API BMKG lagi.

---

## 🔒 Manajemen Keamanan Data

Proyek ini menerapkan standar keamanan industri untuk mencegah kebocoran kredensial database (*API Keys*):
*   **Akses Lokal (ETL):** Kredensial disimpan dalam file `.env` dan dibaca menggunakan library `python-dotenv`.
*   **Akses Web (Streamlit):** Kredensial lokal menggunakan `.streamlit/secrets.toml`, sedangkan untuk versi *live/production* menggunakan fitur **Advanced Secrets** bawaan Streamlit Cloud.
*   **Git Security:** File `.env`, `.secrets.toml`, dan *folder cache* (`__pycache__/`) telah dikunci di dalam file `.gitignore` sehingga tidak akan pernah bocor ke publik saat di-push ke GitHub.

---

## 🚀 Cara Menjalankan Proyek di Lokal

### 1. Kloning Repositori & Instal Dependency
```bash
git clone [https://github.com/humamrdh/dashboard-gempa-bmkg.git](https://github.com/humamrdh/dashboard-gempa-bmkg.git)
cd dashboard-gempa-bmkg
pip install -r requirements.txt
# 🔗 AbsenChain — Sistem Absensi Berbasis Blockchain

AbsenChain adalah sistem absensi digital yang mengintegrasikan teknologi **Blockchain privat** dengan **QR Code terenkripsi** untuk menciptakan catatan kehadiran yang transparan, tidak dapat dimanipulasi, dan dapat diverifikasi secara kriptografis.

---

## ✨ Fitur Utama

### 🛡️ Keamanan Berlapis
- **QR Code Terenkripsi** — Setiap siswa memiliki QR unik dengan payload terenkripsi (Fernet) dan ditandatangani HMAC-SHA256 untuk mencegah pemalsuan
- **Smart Contract** — 5 aturan validasi otomatis sebelum transaksi dicatat ke blockchain
- **ECDSA Validator Signature** — Setiap blok ditandatangani server menggunakan kurva eliptik SECP256K1
- **Password Hashing** — Bcrypt dengan salt rounds 12

### ⛓️ Blockchain Privat
- Implementasi blockchain murni Python (tanpa library eksternal)
- **Proof of Work** dengan target hash prefix `"00"`
- **Genesis Block** dibuat otomatis saat pertama kali dijalankan
- **Merkle Root** per blok untuk integritas data
- `verify_chain()` dijalankan setiap saat untuk memastikan rantai tidak dimanipulasi

### 📷 Absensi QR Real-Time
- Kamera laptop langsung di browser via **WebRTC** (streamlit-webrtc)
- Deteksi QR menggunakan **pyzbar + OpenCV**
- Notifikasi popup (`st.toast`) saat siswa berhasil scan
- Daftar hadir live selama sesi berlangsung

### 👤 Manajemen Akun
- **Admin**: Membuat sesi, scan QR, konfirmasi akun siswa, lihat rekap
- **Siswa**: Lihat QR pribadi, statistik kehadiran, histori blockchain
- Akun siswa baru berstatus **PENDING** hingga disetujui admin

### 📊 Dashboard
- Rekap absensi per sesi (Hadir / Terlambat / Absen)
- Badge otomatis: ⭐⭐⭐ Si Rajin · ⭐⭐ Si Pas-Pas · ⭐ Si Malas
- Visualisasi histori blok blockchain per siswa
- Validator rantai blockchain di dashboard admin

---

## 🏗️ Struktur Folder

```
absenchain/
├── app.py                    # Entry point aplikasi
├── config.py                 # Konfigurasi dari .env
├── requirements.txt
├── .env.example              # Template konfigurasi
├── blockchain/               # Implementasi blockchain privat
│   ├── block.py              # Struktur blok
│   ├── chain.py              # Manajemen rantai
│   ├── smart_contract.py     # Aturan validasi CONTRACT-01~05
│   ├── crypto_utils.py       # HMAC, ECDSA signing
│   └── proof_of_work.py      # Algoritma PoW
├── database/                 # ORM dan model database
│   ├── connection.py
│   ├── models.py
│   └── migrations/
├── auth/                     # Autentikasi dan password
├── qr/                       # Generate, scan, dan validasi QR
├── attendance/               # Logika absensi dan session
├── views/                    # Halaman Streamlit
│   ├── login_page.py
│   ├── register_page.py
│   ├── student_dashboard.py
│   └── admin_dashboard.py
├── components/               # Widget UI yang dapat digunakan ulang
└── utils/                    # Helper: logger, validator, date utils
```

---

## 🚀 Cara Menjalankan

### Prasyarat
- Python 3.10+
- PostgreSQL 15+
- pip

### 1. Clone / Unduh Proyek

```bash
# Masuk ke direktori proyek
cd absenchain
```

### 2. Buat Virtual Environment

```bash
python -m venv venv

# Aktivasi — Windows
venv\Scripts\activate

# Aktivasi — Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Database

Pastikan PostgreSQL sudah berjalan, lalu buat database baru:

```sql
-- Di psql atau pgAdmin
CREATE DATABASE absenchain;
CREATE USER absenchain_user WITH PASSWORD 'password_anda';
GRANT ALL PRIVILEGES ON DATABASE absenchain TO absenchain_user;
```

Salin file konfigurasi dan sesuaikan nilainya:

```bash
cp .env.example .env
```

Buka file `.env` dan isi dengan kredensial Anda:

```env
DATABASE_URL=postgresql://<user>:<password>@localhost:5432/<nama_database>
SECRET_KEY=<random_string_minimal_32_karakter>
HMAC_SECRET=<random_string_untuk_signing_qr>
```

> **Tips keamanan**: Gunakan perintah berikut untuk menghasilkan SECRET_KEY yang aman:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### 5. Jalankan Aplikasi

```bash
streamlit run app.py
```

Aplikasi akan terbuka di browser pada `http://localhost:8501`.  
Tabel database dibuat **otomatis** saat pertama kali dijalankan.

---

## 🔑 Akun Default

Saat pertama kali dijalankan, sistem otomatis membuat akun admin:

| Field    | Nilai        |
|----------|--------------|
| Username | `admin@admin` |
| Password | `admin123`   |
| Role     | Admin        |

> ⚠️ **Segera ganti password admin** setelah login pertama melalui pengaturan akun.

---

## 📋 Alur Penggunaan

### Alur Absensi Lengkap
```
Admin login
  └─► Buat sesi baru (mapel, kelas, jam, toleransi)
        └─► Kamera aktif (tab Live Sesi & Kamera)
              └─► Siswa arahkan QR ke kamera
                    └─► Smart Contract validasi (5 aturan)
                          └─► Blok blockchain baru dibuat
                                └─► Notifikasi popup muncul
                                      └─► Admin tutup sesi
                                            └─► Siswa yang belum scan → ABSEN (dicatat ke blockchain)
                                                  └─► Rekap tampil di tab Rekap Absensi
```

### Alur Registrasi Siswa
```
Siswa daftar (username harus berakhiran @siswa)
  └─► Status: PENDING
        └─► Admin setujui di tab Konfirmasi Akun
              └─► QR Code otomatis digenerate
                    └─► Siswa dapat lihat & unduh QR dari dashboard
```

---

## ⚙️ Smart Contract (Aturan Validasi)

| Kode | Aturan |
|------|--------|
| CONTRACT-01 | QR signature (HMAC-SHA256) tidak valid — indikasi manipulasi |
| CONTRACT-02 | Akun siswa tidak terdaftar atau tidak aktif |
| CONTRACT-03 | Sesi absensi sudah ditutup atau tidak ditemukan |
| CONTRACT-04 | Siswa sudah tercatat hadir pada sesi ini (duplikat) |
| CONTRACT-05 | Waktu scan berada di luar rentang jam sesi |

---

## 🛠️ Tech Stack

| Komponen | Teknologi |
|----------|-----------|
| Framework | Streamlit |
| Database | PostgreSQL 15+ |
| ORM | SQLAlchemy + psycopg2 |
| Blockchain | Python murni (tanpa library eksternal) |
| Kriptografi | hashlib, HMAC-SHA256, ECDSA (cryptography), bcrypt |
| QR Code | qrcode[pil], pyzbar, OpenCV |
| Kamera | streamlit-webrtc (WebRTC) |

---

## 📄 Lisensi

Proyek ini dibuat untuk keperluan akademik — Tugas Kuliah Teknologi Blockchain.

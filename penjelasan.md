# 📘 Penjelasan Arsitektur & Alur Kerja AbsenChain

Dokumen ini menjelaskan secara rinci bagaimana aplikasi AbsenChain bekerja di belakang layar, khususnya mengenai implementasi teknologi Blockchain privat dan *Smart Contract* untuk menjamin transparansi dan keamanan absensi.

---

## 1. 🔄 Alur Kerja Sistem (System Flow)

Sistem ini melibatkan dua aktor utama: **Admin** (Guru/Sistem) dan **Siswa**.

1. **Pembuatan Akun & QR Code**:
   - Siswa melakukan registrasi. Akun yang dibuat akan berstatus **PENDING**.
   - Admin memeriksa dan **Menyetujui** akun siswa.
   - Saat disetujui, sistem membuat **QR Code** unik. Data di dalam QR Code (seperti `student_id` dan `nis`) akan dienkripsi menggunakan algoritma **AES (Fernet)** dan diberi tanda tangan digital menggunakan **HMAC-SHA256**.
2. **Pembuatan Sesi Absensi**:
   - Admin membuat **Sesi** (Mata Pelajaran, Kelas, Rentang Waktu, Toleransi Keterlambatan).
   - Setelah sesi dibuka, kamera WebRTC di halaman Admin akan aktif untuk memindai QR Code.
3. **Proses Pemindaian (Scan) QR**:
   - Siswa menunjukkan QR Code mereka ke kamera Admin.
   - Sistem akan mendekripsi payload QR, kemudian memasukkan datanya ke dalam antrean (Queue) sistem.
   - Sistem akan mencoba merekam data ini ke Blockchain dengan melalui tahap **Smart Contract** terlebih dahulu.
4. **Penutupan Sesi (Tutup Sesi & Rekap)**:
   - Saat Admin menekan tombol "Tutup Sesi", sistem secara otomatis mencari siswa yang berada di kelas tersebut tetapi **belum melakukan scan**.
   - Siswa tersebut akan langsung diberikan status **ABSEN** dan dicatat dalam blok baru di blockchain.

---

## 2. ⛓️ Sistem Blockchain: Penyimpanan & Keamanan

Sistem tidak bergantung pada blockchain publik (seperti Ethereum), melainkan mengimplementasikan struktur Blockchain Privat murni menggunakan Python yang disimpan di atas tabel database relasional (`blockchains`).

### A. Struktur Data Sebuah Blok
Setiap blok yang menyimpan transaksi kehadiran memiliki komponen berikut:
- **`index`**: Nomor urut blok (dimulai dari 0 untuk *Genesis Block*).
- **`timestamp`**: Waktu pasti saat blok ditambang (mined).
- **`data`**: Informasi transaksi (ID siswa, ID sesi, status kehadiran, dll).
- **`previous_hash`**: Hash kriptografis dari blok sebelumnya. Ini adalah kunci yang mengikat blok satu dengan yang lain membentuk "rantai" (chain).
- **`nonce`**: Angka acak yang dicari saat proses *Proof of Work*.
- **`hash`**: Hash SHA-256 dari seluruh isi blok ini sendiri.
- **`validator_sig`**: Tanda tangan digital (menggunakan algoritma *Elliptic Curve* ECDSA) dari server validator untuk memastikan blok tersebut benar-benar dibuat oleh sistem yang sah.

### B. Bagaimana Blockchain Disimpan?
1. Saat aplikasi pertama kali dijalankan, sistem mengecek apakah tabel `blockchains` kosong. Jika kosong, sistem otomatis membuat **Genesis Block** (Blok Pertama) dengan `previous_hash` bernilai "0".
2. Setiap kali ada absensi sukses, blok baru akan dibuat di RAM memori, ditambang (Proof of Work), dan kemudian **disimpan sebagai baris baru di tabel database PostgreSQL** (`blockchains`).
3. Ini adalah desain *Hybrid* — memanfaatkan kemudahan query database relasional untuk UI dashboard, sambil mempertahankan sifat *immutable* (tidak dapat diubah) ala blockchain. Jika ada seseorang yang mengubah data di PostgreSQL secara paksa, rantai hash akan putus dan terdeteksi rusak oleh sistem (dapat dilihat di tab "Validasi Ledger").

### C. Pengamanan Blok (Proof of Work & Kriptografi)
- **Proof of Work (PoW)**: Sebelum blok disimpan, sistem harus menemukan nilai `nonce` sedemikian rupa sehingga `hash` akhir dari blok tersebut diawali dengan `"00"` (Difficulty = 2). Ini mensimulasikan mekanisme *mining*.
- **Hashing**: Perubahan sekecil apapun pada `data` di sebuah blok akan mengubah `hash` blok tersebut. Karena blok berikutnya menyimpan `previous_hash`, perubahan ini akan membatalkan blok-blok di depannya.
- **Tanda Tangan Digital (ECDSA)**: Blok ditandatangani oleh *Private Key* server (validator). Jika *database admin* nakal mencoba merekayasa blok beserta hash-nya, mereka tidak akan bisa merekayasa `validator_sig` tanpa mengetahui *Private Key* tersebut.

---

## 3. 📜 Smart Contract & Aturan Validasi

Dalam arsitektur AbsenChain, **Smart Contract** bukanlah program yang berjalan di EVM (Ethereum Virtual Machine), melainkan sekumpulan *business logic* mutlak (bersifat deterministik) yang harus terpenuhi **sebelum** sebuah blok absensi diizinkan untuk masuk ke Blockchain.

### Alur Smart Contract:
Ketika QR Code berhasil didecode oleh kamera, fungsi `record_attendance` akan memicu `AttendanceContract.validate()`. Kontrak ini mengeksekusi 5 aturan secara sekuensial (berurutan):

1. **CONTRACT-01: Validasi Keaslian QR (HMAC)**
   - Sistem memisahkan `hmac_signature` dari QR Code.
   - Sistem menghitung ulang HMAC dari payload data siswa menggunakan kunci rahasia server.
   - *Tujuan*: Jika ada siswa yang mencoba mengedit isi QR Code (misal mengubah NIS-nya menjadi NIS temannya), perhitungan HMAC tidak akan cocok dan Smart Contract langsung menolaknya.

2. **CONTRACT-02: Validasi Status Akun Aktif**
   - Sistem memeriksa apakah ID Siswa terdaftar di database dan status akunnya adalah `ACTIVE`.
   - *Tujuan*: Mencegah siswa yang akunnya sudah diblokir atau belum disetujui (PENDING) untuk melakukan absensi.

3. **CONTRACT-03: Validasi Sesi Terbuka**
   - Sistem memastikan bahwa `session_id` yang sedang berjalan berstatus `open`.
   - *Tujuan*: Mencegah absensi susulan ilegal ketika sesi/kelas sudah ditutup oleh Guru/Admin.

4. **CONTRACT-04: Validasi Anti-Duplikasi (Double Spending)**
   - Sistem mengecek apakah siswa tersebut sudah memiliki record kehadiran pada sesi ini.
   - *Tujuan*: Mencegah satu siswa melakukan scan QR berulang-kali (spamming) yang bisa mengotori ledger blockchain.

5. **CONTRACT-05: Validasi Toleransi Waktu Batas Sesi**
   - Sistem mengekstrak waktu saat ini (`now`) dan membandingkannya dengan rentang waktu (`jam_mulai` dan `jam_selesai`) yang didefinisikan saat pembuatan sesi.
   - *Tujuan*: Sistem secara absolut menolak absensi jika kelas memang belum dimulai atau kelas sudah lewat batas waktunya.

> **Hanya jika kelima kontrak ini mengembalikan nilai `True` (Valid)**, barulah blok absensi dikirim ke tahapan **Proof of Work** untuk di-mining dan disambungkan ke ujung rantai Blockchain.

---

## 4. 🛡️ Mengapa Data Benar-Benar Tidak Dapat Diubah (Immutable)?

Untuk memastikan bahwa data absensi (yang disimpan di dalam database PostgreSQL) **benar-benar tidak dapat dimanipulasi** oleh siapa pun (termasuk Database Administrator), sistem menerapkan 4 lapis pertahanan kriptografi:

1. **Keterikatan Rantai Hash (Chaining) 🔗**
   Setiap blok absensi (Blok 2) tidak berdiri sendiri, melainkan mengikat **Hash dari blok sebelumnya** (Blok 1) di dalam parameter `previous_hash`.
   - **Skenario Manipulasi:** Misal ada admin nakal membuka database dan mengubah status siswa dari "Absen" menjadi "Hadir" di Blok 1.
   - **Apa yang terjadi?** Jika 1 huruf saja diubah, maka **Hash Blok 1 akan berubah total**. Akibatnya, `previous_hash` yang disimpan di Blok 2 menjadi **tidak cocok** dengan Hash Blok 1 yang baru. Rantai seketika putus!

2. **Validasi Terus-Menerus (Continuous Verification) 🔍**
   Di Tab "Validasi Ledger" pada dashboard admin, sistem secara rutin menjalankan fungsi `verify_chain()`. Fungsi ini akan menghitung ulang seluruh hash dari Blok 0 sampai blok terakhir. Jika terdeteksi ada hash yang tidak cocok akibat manipulasi, sistem membunyikan alarm visual: **"TERDETEKSI MANIPULASI (INVALID) ❌"**.

3. **Tanda Tangan Server (Validator Signature / ECDSA) ✍️**
   Ini adalah pertahanan level tertinggi terhadap manipulasi.
   - **Skenario Hacker:** Hacker yang cerdas mungkin tahu bahwa rantai akan putus, jadi ia menghitung ulang hash Blok 1, lalu sengaja memperbarui *previous_hash* di Blok 2, menghitung ulang hash Blok 2, dan seterusnya sampai ujung rantai.
   - **Pencegahan AbsenChain:** Setiap kali blok dibuat secara sah, sistem membubuhkan `validator_sig` (Tanda Tangan Digital) yang di-*generate* menggunakan **Private Key server** (Asymmetric Cryptography). Hacker bisa mengubah data dan hash, namun ia **TIDAK BISA** memalsukan `validator_sig` karena ia tidak mengetahui *Private Key* tersebut. Blok yang dimodifikasi akan langsung ditolak!

4. **Proof of Work (Mekanisme Penambangan / Mining) ⛏️**
   Setiap perubahan blok memaksa pelaku untuk mencari ulang angka acak (`nonce`) agar hasil hash-nya memenuhi syarat awalan tertentu (seperti `"00"`). Mengubah blok di tengah rantai memaksa pelaku menambang ulang seluruh blok setelahnya, yang memakan daya komputasi secara sia-sia.

---

## 5. 🛠️ Cara Membuktikan Ketahanan (Uji Coba Hacking Ledger)

Anda dapat membuktikan sendiri kecanggihan sistem pendeteksi manipulasi ini dengan melakukan simulasi serangan pengubahan data (Data Tampering):

**Langkah-langkah Uji Coba:**
1. **Buka Database Management Tool** (seperti *pgAdmin*, *DBeaver*, atau terminal `psql`).
2. Masuk ke database `absenchain` dan buka tabel `blockchains`.
3. Cari baris milik salah satu siswa (pastikan bukan *Genesis Block* di Index 0).
4. Pada kolom `data` (yang berbentuk JSON), cari parameter `"status": "absen"`.
5. Ubah nilainya secara paksa menjadi `"status": "hadir"` lalu tekan **Save / Commit** pada database. (Tindakan ini menyimulasikan kelakuan "Admin Nakal" yang menerima suap untuk mengubah absensi secara diam-diam melalui database).
6. Buka kembali aplikasi web AbsenChain di browser Anda.
7. Masuk ke menu **Tab 5: Validasi Ledger**.
8. **HASILNYA:** Sistem tidak akan tertipu. Akan muncul *banner* peringatan berwarna merah terang:
   > ❌ **Pemeriksaan Rantai Selesai: TERDETEKSI MANIPULASI (INVALID)**

Hal ini terjadi karena meskipun data di database berubah, **hash dari blok tersebut telah rusak** dan **Tanda Tangan ECDSA** (*validator_sig*) sudah tidak sinkron lagi dengan isi datanya. Bukti nyata bahwa blockchain bekerja sebagaimana mestinya!

---

## 6. 🚑 Cara Memulihkan Rantai Blockchain yang Telah Rusak

Jika blockchain terlanjur berstatus **INVALID** akibat percobaan pengubahan data di atas, bagaimana cara mengembalikannya menjadi **VALID ✅**? 

Dalam arsitektur *AbsenChain*, karena ini adalah sistem terpusat bersistem blockchain privat (tanpa jaringan desentralisasi P2P yang bisa melakukan sinkronisasi ulang), Anda memiliki dua pilihan:

### A. Mengembalikan Data ke Kondisi Semula (Revert)
Sistem blockchain mendeteksi kerusakan berdasarkan ketidakcocokan hash dengan isi data. Jika Anda mengembalikan isi kolom `data` persis seperti sedia kala (mengembalikan `"status": "hadir"` menjadi `"status": "absen"` lagi), maka hash yang lama akan kembali cocok (*match*) dengan isi datanya.
- **Cara:** Buka database, ubah kembali teks JSON yang diedit menjadi 100% sama dengan aslinya (termasuk spasi dan tanda baca). Simpan, lalu cek web. Rantai akan kembali VALID!

### B. Merekalkulasi Seluruh Rantai (Hacking Balik / Hard Fork)
Jika data aslinya lupa, maka rantai dari blok tersebut hingga blok paling baru di masa depan telah rusak secara permanen. Satu-satunya cara sistematis untuk membetulkannya (yang mana ini setara dengan membajak server) adalah dengan membuat *script* khusus yang melakukan:
1. Menghitung ulang **Hash** blok yang diubah.
2. Melakukan **Mining / Proof of Work** ulang (mencari `nonce` baru).
3. Melakukan **Tanda Tangan Ulang (ECDSA)** menggunakan Private Key rahasia server (mengambil dari `.env`).
4. Memperbarui nilai `previous_hash` pada **SEMUA** blok di atasnya satu per satu, dan mengulangi proses mining & signing untuk setiap blok tersebut.
*(Inilah mengapa dalam skala besar, mengubah data blockchain dianggap mustahil karena butuh waktu dan komputasi yang luar biasa besar).*

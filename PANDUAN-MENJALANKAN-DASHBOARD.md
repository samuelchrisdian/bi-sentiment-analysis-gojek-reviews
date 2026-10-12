# Panduan Menjalankan Dashboard Ulasan Gojek

Panduan ini membawa Anda dari nol sampai dashboard terbuka di browser.
**Anda tidak perlu bisa pemrograman.** Cukup ikuti langkahnya satu per satu,
lalu salin-tempel perintah yang sudah disediakan.

Perkiraan waktu: **30–60 menit** untuk pertama kali (sebagian besar untuk
mengunduh dan memasang program). Setelah itu, menyalakan dashboard cukup
**1 menit**.

---

## Gambaran Singkat

Bayangkan dashboard ini seperti sebuah restoran kecil yang terdiri dari tiga
bagian:

| Bagian | Ibarat | Tugasnya |
|--------|--------|----------|
| **Database** | Gudang | Menyimpan 526.322 ulasan Gojek (Oktober 2021 – September 2026) beserta hasil analisisnya |
| **API** | Pelayan | Mengambil data dari gudang ketika diminta |
| **Dashboard** | Ruang makan | Tampilan grafik dan tabel yang Anda lihat di browser |

Ketiganya dijalankan oleh satu program bernama **Docker**. Anda cukup
menyuruh Docker "nyalakan semuanya", dan Docker yang mengurus sisanya.

---

## Yang Perlu Disiapkan

- [ ] Komputer/laptop dengan **Windows 10/11**, **macOS**, atau **Linux**
- [ ] Ruang kosong di hard disk minimal **10 GB**
- [ ] Koneksi internet (cukup untuk pemasangan pertama kali)
- [ ] Berkas data bernama **`db_dump.sql.gz`** (±44 MB) — **minta ke pemilik
      proyek**. Berkas ini berisi seluruh data ulasan dan sengaja tidak
      disimpan di GitHub.

---

## Langkah 1 — Pasang Dua Program

Anda perlu memasang dua program gratis. Cukup dilakukan **sekali saja**.

### a. Git (untuk mengunduh proyek)

1. Buka <https://git-scm.com/downloads>
2. Pilih sistem operasi Anda, unduh, lalu pasang.
3. Saat pemasangan, **klik "Next" terus** sampai selesai — pengaturan bawaan
   sudah cukup.

> Pengguna macOS: Git biasanya sudah ada. Jika nanti diminta memasang
> "command line developer tools", klik **Install**.

### b. Docker Desktop (untuk menjalankan dashboard)

1. Buka <https://www.docker.com/products/docker-desktop/>
2. Unduh sesuai sistem operasi Anda, lalu pasang.
3. Setelah terpasang, **buka aplikasi Docker Desktop** dan tunggu sampai
   muncul tulisan **"Engine running"** (atau ikon paus di pojok layar berhenti
   bergerak).

> **Pengguna Windows:** jika Docker meminta memasang atau memperbarui
> **WSL**, ikuti saja petunjuknya lalu **restart komputer**.

> ⚠️ **Penting:** Docker Desktop harus **selalu dalam keadaan terbuka** setiap
> kali Anda ingin memakai dashboard.

---

## Langkah 2 — Buka Jendela Perintah (Terminal)

Terminal adalah jendela tempat Anda menempelkan perintah. Tampilannya
biasanya hitam/putih polos berisi teks — itu normal.

| Sistem operasi | Cara membuka |
|----------------|--------------|
| **Windows** | Tekan tombol **Windows**, ketik **PowerShell**, lalu tekan **Enter** |
| **macOS** | Tekan **Cmd + Spasi**, ketik **Terminal**, lalu tekan **Enter** |
| **Linux** | Tekan **Ctrl + Alt + T** |

**Cara memakai terminal di panduan ini:**

1. Salin perintah dari kotak abu-abu di panduan ini.
2. Tempel ke terminal (klik kanan → *Paste*, atau **Ctrl + V** /
   **Cmd + V**).
3. Tekan **Enter**.
4. **Tunggu sampai selesai** — tanda selesai adalah munculnya lagi baris
   kosong tempat Anda bisa mengetik.

---

## Langkah 3 — Unduh Proyek dari GitHub

Tempel perintah ini lalu tekan Enter:

```
git clone https://github.com/samuelchrisdian/bi-sentiment-analysis-gojek-reviews.git
```

Akan muncul folder baru bernama `bi-sentiment-analysis-gojek-reviews`. Masuk ke
folder itu dengan perintah:

```
cd bi-sentiment-analysis-gojek-reviews
```

> Jika muncul pesan meminta *username/password* atau *"Repository not
> found"*, artinya Anda belum diberi akses ke proyek ini. Hubungi pemilik
> proyek.

> 💡 Folder ini tersimpan di folder pengguna Anda (Windows:
> `C:\Users\NamaAnda\`, macOS: `/Users/NamaAnda/`).

---

## Langkah 4 — Siapkan Berkas Pengaturan

Proyek ini butuh satu berkas pengaturan. Isinya sudah disiapkan, Anda
cukup menyalinnya.

**Windows (PowerShell):**

```
copy .env.example .env
```

**macOS / Linux:**

```
cp .env.example .env
```

Perintah ini tidak menampilkan apa-apa jika berhasil — itu normal.

---

## Langkah 5 — Letakkan Berkas Data

Ambil berkas **`db_dump.sql.gz`** yang Anda terima dari pemilik proyek, lalu
pindahkan ke dalam folder **`docs`** di dalam folder proyek.

Jadi letaknya:

```
bi-sentiment-analysis-gojek-reviews
└── docs
    └── db_dump.sql.gz   ← di sini
```

Anda bisa memindahkannya lewat File Explorer (Windows) atau Finder (macOS)
seperti memindahkan berkas biasa.

> ⚠️ Pastikan nama berkasnya **persis** `db_dump.sql.gz`. Beberapa komputer
> menambahkan angka saat mengunduh, misalnya `db_dump.sql (1).gz` — jika
> begitu, ubah namanya.

---

## Langkah 6 — Nyalakan Dashboard

Pastikan Docker Desktop sudah terbuka, lalu tempel perintah ini di terminal:

```
docker compose up -d --build
```

⏳ **Pertama kali, ini bisa memakan waktu 5–15 menit** karena Docker
mengunduh bahan-bahan yang dibutuhkan. Anda akan melihat banyak tulisan
bergulir — biarkan saja.

Selesai jika di bagian akhir muncul tulisan seperti:

```
✔ Container gojek_db    Started
✔ Container gojek_api   Started
✔ Container gojek_web   Started
```

---

## Langkah 7 — Isi Data ke Dashboard

Saat ini dashboard sudah menyala, tetapi **masih kosong** — gudangnya belum
diisi. Tunggu sekitar **30 detik** setelah Langkah 6, lalu jalankan **dua
perintah** berikut, satu per satu.

**Perintah pertama** — memasukkan berkas data ke dalam Docker:

```
docker cp docs/db_dump.sql.gz gojek_db:/tmp/data.sql.gz
```

**Perintah kedua** — mengosongkan gudang, lalu membongkar dan mengisi data.
Datanya cukup besar (lebih dari setengah juta ulasan), jadi proses ini bisa
memakan **beberapa menit**. Jangan tutup terminal sampai baris kosong untuk
mengetik muncul lagi:

```
docker exec gojek_db sh -c "psql -q -U gojek -d gojek_sentiment -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;' && gunzip -c /tmp/data.sql.gz | psql -q -U gojek -d gojek_sentiment"
```

Akan muncul beberapa baris tulisan seperti `NOTICE`, `set_config`, atau
`setval` — **itu normal**, bukan kesalahan.

> 💡 Mengapa gudang dikosongkan dulu? Saat pertama kali dinyalakan, Docker
> sudah membuatkan "rak-rak" kosong di gudang. Berkas data membawa rak-raknya
> sendiri, jadi rak kosong tadi dibuang lebih dulu supaya tidak bentrok.

> ✅ Langkah ini **cukup dilakukan sekali saja**. Data akan tetap tersimpan
> walaupun komputer dimatikan.

---

## Langkah 8 — Buka Dashboard 🎉

Buka browser (Chrome, Firefox, Edge, atau Safari), lalu kunjungi alamat:

### 👉 http://localhost:5173

Anda akan melihat dashboard **"Analisis Sentimen Ulasan Gojek"** berisi:

- Ringkasan angka utama (persentase ulasan negatif, total ulasan, rata-rata
  bintang, jumlah versi aplikasi)
- Grafik tren dari waktu ke waktu (Oktober 2021 – September 2026)
- Grafik per versi aplikasi
- Peringkat kategori keluhan — klik salah satu untuk membaca ulasan aslinya
- Perbandingan model analisis

### ✅ Cara memastikan semuanya benar

Lihat kartu **Total ulasan** di bagian atas dashboard. Jika isinya:

```
526.322
1 Okt 2021 – 30 Sep 2026
```

berarti data sudah terisi lengkap dan dashboard berjalan dengan benar.

Jika angkanya **berbeda** (misalnya 100.000), kemungkinan Anda memakai berkas
data versi lama. Minta berkas `db_dump.sql.gz` terbaru ke pemilik proyek,
letakkan di folder `docs` (Langkah 5), lalu ulangi Langkah 7.

### Lima kategori keluhan yang akan Anda lihat

Di bagian peringkat kategori keluhan, ada lima kategori berikut (diurutkan
dari yang paling sering dikeluhkan):

1. Pencarian & Penugasan Driver, Waktu Tunggu & Pembatalan Pesanan
2. Layanan Pelanggan & Penanganan Keluhan
3. Tarif, Ongkir & Promo
4. Transaksi, Saldo & Pemblokiran GoPay
5. Kendala Penggunaan Aplikasi & Akses Akun

Klik salah satu kategori untuk membaca contoh ulasan aslinya.

---

## Pemakaian Sehari-hari

Setelah pemasangan pertama selesai, Anda **tidak perlu mengulang** Langkah
1–7. Cukup:

**Untuk menyalakan:**

1. Buka **Docker Desktop**.
2. Buka terminal, lalu masuk ke folder proyek:
   ```
   cd bi-sentiment-analysis-gojek-reviews
   ```
3. Nyalakan:
   ```
   docker compose up -d
   ```
4. Buka **http://localhost:5173** di browser.

**Untuk mematikan** (agar komputer tidak berat):

```
docker compose stop
```

Data Anda tetap aman saat dimatikan.

> 💡 Cara lain tanpa terminal: di Docker Desktop, buka menu **Containers**,
> cari **bi-sentiment-analysis-gojek-reviews**, lalu klik tombol ▶ (nyalakan)
> atau ■ (matikan).

---

## Jika Ada Masalah

| Yang terjadi | Penyebab | Solusi |
|--------------|----------|--------|
| Muncul pesan `Cannot connect to the Docker daemon` atau `error during connect` | Docker Desktop belum dibuka | Buka Docker Desktop, tunggu sampai "Engine running", lalu ulangi perintahnya |
| Muncul pesan `'docker' is not recognized` atau `command not found: docker` | Docker belum terpasang, atau terminal dibuka sebelum Docker dipasang | Pasang Docker (Langkah 1b), lalu **tutup dan buka lagi** terminal |
| Muncul pesan `'git' is not recognized` | Git belum terpasang | Pasang Git (Langkah 1a), lalu tutup dan buka lagi terminal |
| Muncul pesan `no configuration file provided` | Anda tidak sedang berada di folder proyek | Jalankan `cd bi-sentiment-analysis-gojek-reviews` terlebih dahulu |
| Muncul pesan `port is already allocated` | Ada program lain yang memakai "pintu" yang sama (dashboard memakai pintu **5173**, API **8000**, database **5434**) | Tutup program lain yang mungkin bentrok, atau restart komputer, lalu ulangi Langkah 6 |
| Muncul pesan `No such container: gojek_db` | Dashboard belum dinyalakan | Jalankan Langkah 6 dulu |
| Muncul pesan `no such file` pada Langkah 7 | Berkas data belum ada di folder `docs` atau namanya berbeda | Periksa kembali Langkah 5 |
| Muncul pesan `invalid command \restrict` pada Langkah 7 | Program database di komputer Anda versi lama | Jalankan `docker compose pull db`, lalu `docker compose up -d`, tunggu 30 detik, dan ulangi Langkah 7 |
| **Total ulasan** tidak menunjukkan **526.322** | Berkas data yang dipakai versi lama | Minta `db_dump.sql.gz` terbaru ke pemilik proyek, ganti berkas di folder `docs`, lalu ulangi Langkah 7 |
| Browser menampilkan *"This site can't be reached"* | Dashboard belum menyala, atau masih dalam proses | Tunggu 1 menit lalu muat ulang halaman (F5). Jika tetap gagal, ulangi Langkah 6 |
| Dashboard terbuka tetapi **kosong / tidak ada angka** | Data belum diisi | Jalankan Langkah 7 |
| Fitur **"Coba Prediksi"** menampilkan pesan *"Model tidak tersedia"* | Fitur ini butuh pemasangan tambahan yang bersifat teknis | **Normal**, bagian dashboard lainnya tetap berfungsi penuh. Hubungi pemilik proyek bila fitur ini diperlukan |

Jika masalah tetap belum teratasi, ambil **tangkapan layar (screenshot)**
terminal Anda dan kirimkan ke pemilik proyek.

---

## Kamus Istilah

| Istilah | Artinya |
|---------|---------|
| **Terminal / PowerShell** | Jendela untuk memberi perintah ke komputer lewat tulisan |
| **Git** | Program untuk mengunduh proyek dari GitHub |
| **GitHub** | Situs tempat kode proyek ini disimpan |
| **Clone** | Mengunduh salinan proyek ke komputer Anda |
| **Docker** | Program yang menjalankan seluruh bagian dashboard sekaligus |
| **Container** | Satu "kotak" berisi satu bagian dashboard (database, API, atau tampilan) |
| **Database** | Tempat penyimpanan data ulasan |
| **localhost** | Artinya "komputer ini sendiri" — dashboard hanya bisa dibuka dari komputer Anda |
| **5173** | Nomor "pintu" tempat dashboard bisa diakses |
| **8000** | Nomor "pintu" API (pelayan yang mengambil data dari gudang) |
| **5434** | Nomor "pintu" database. Anda tidak perlu membukanya; angka ini hanya penting bila muncul pesan `port is already allocated` |

# KONTRAK DATA

**Fase 1 · T-1.4** · Dihasilkan dari `ml/src/ingest.py` dan `ml/notebooks/01_eda.ipynb`
Seluruh angka pada dokumen ini berasal dari kode yang dijalankan, bukan dari estimasi.

---

## 1. Provenans

| Properti | Nilai |
|----------|-------|
| Berkas | `data/raw/ulasan_com.gojek.app.csv` |
| Ukuran | 10.771.654 byte |
| **SHA-256** | `9b7f8e50737f9f17bce4ab8a44f7d2f8587deea86c6ad175e2579932cc22b524` |
| Asal | Unduhan langsung Kaggle, **tanpa modifikasi** |
| Dataset | *Gojek App Reviews Indonesia — Google Play Store*, pengunggah `pandaa12`, versi 1 |
| URL | https://www.kaggle.com/datasets/pandaa12/gojek-app-reviews-indonesia-google-play-store/versions/1?resource=download |

Rincian konsekuensi metodologis dan keterbatasan dataset sekunder:
`docs/data_provenance_notes.md`.

Hash SHA-256 di atas dicatat ulang di `MANIFEST.json` (Fase 4) sebagai
pengikat antara artefak model dan data yang melatihnya.

---

## 2. Kamus Kolom

### 2.1 Kolom asli (6)

| Kolom | Tipe pandas | Tipe PostgreSQL | Nullable | Contoh | Keterangan |
|-------|-------------|-----------------|----------|--------|------------|
| `Nama User` | `string` | `TEXT` | tidak | `Budi Santoso` | Tidak dipakai untuk pemodelan |
| `Ulasan` | `string` | `TEXT NOT NULL` | **tidak** | `aplikasi error terus` | Teks mentah, tidak pernah diubah |
| `Rating` | `int8` | `SMALLINT NOT NULL` | tidak | `1` | Rentang 1–5, divalidasi `CHECK` |
| `Tanggal` | `datetime64[ns]` | `TIMESTAMPTZ NOT NULL` | tidak | `2024-11-03 08:14:22` | Di-parse dengan `format="mixed"` |
| `Likes` | `int32` | `INTEGER NOT NULL` | tidak | `0` | Median 0; 83,7% bernilai nol |
| `Versi App` | `string` | `TEXT` | **ya (21,9%)** | `4.93.1` | **Tidak diimputasi** |

### 2.2 Kolom turunan (4)

| Kolom | Definisi | Dihitung di |
|-------|----------|-------------|
| `versi_minor` | `Versi App` dipotong ke dua segmen: `4.93.1` → `4.93`; NaN tetap NaN | `ingest.derive_versi_minor` |
| `word_count` | Jumlah token hasil `split()` atas **`ulasan_normalized`** (setelah normalisasi slang, **sebelum** stemming) | Fase 2 |
| `sentimen_aktual` | `0` bila `Rating ∈ {1,2}`; `1` bila `Rating ∈ {4,5}`; `NULL` bila `Rating = 3` | Fase 2 |
| `bulan` | `Tanggal` dipotong ke periode bulanan | `eda.prepare` |

> **Catatan penting tentang `word_count`.** Dihitung dari `ulasan_normalized`,
> bukan `ulasan_clean`. Setelah *stopword removal* dan *stemming*, ulasan 7 kata
> dapat menyusut menjadi 3 kata, sehingga ambang `>= 5` untuk set evaluasi
> `informative_ge5w` tidak lagi mengukur apa yang dimaksud. Definisi ini wajib
> konsisten di Fase 2, 3, dan 6.
>
> Pada Fase 1, `word_count` dihitung dari `Ulasan` mentah untuk keperluan EDA.
> Angka 39.859 ulasan ≤2 kata pada dokumen ini merujuk definisi mentah tersebut.

---

## 3. Aturan Validasi

Seluruh aturan di bawah ditegakkan sebagai `assert` di `ml/src/ingest.py`.
Pipeline **berhenti** bila salah satunya dilanggar — tidak ada penanganan diam-diam.

| # | Aturan | Implementasi |
|---|--------|--------------|
| V-1 | Enam kolom yang diharapkan harus ada | `validate_schema` |
| V-2 | Jumlah baris tepat **100.000** | `validate_schema` |
| V-3 | `Tanggal` dapat di-parse seluruhnya (0 NaT) | `parse_types` |
| V-4 | `Tanggal` berada dalam `2024-05-21 .. 2025-12-31` | `parse_types` |
| V-5 | `Rating` seluruhnya dalam 1–5 | `parse_types` |
| V-6 | `Likes` tidak negatif | `parse_types` |
| V-7 | `Ulasan` tidak ada yang null | `parse_types` |

> **Jangan memvalidasi jumlah baris dengan `wc -l`.** Perintah itu mengembalikan
> 100.002 karena sebagian teks ulasan memuat *newline* di dalam tanda kutip.
> Jumlah baris yang sah hanya yang dihitung pandas: **100.000**.

---

## 4. Penanganan Nilai Kosong

Hanya satu kolom yang memiliki nilai kosong.

**`Versi App` — 21.910 baris (21,9%) NULL.**

Aturan:

1. **Jangan diimputasi.** Tidak ada nilai pengganti, tidak ada kategori
   "Tidak diketahui" yang diperlakukan sebagai versi.
2. Baris tetap **dipakai penuh** untuk analisis sentimen, tren temporal, dan
   ekstraksi topik.
3. Baris **dikecualikan** dari seluruh analisis per-versi.
4. Setiap grafik dan tabel per-versi **wajib** mencantumkan dua angka:
   proporsi baris tanpa versi (21,9%) dan ambang minimum yang dipakai.

Ambang versi yang dipilih: **≥100 ulasan per versi** → 66 versi, mencakup
96,4% dari data yang berversi. Dasar pemilihan (`docs/tables/cakupan_versi.csv`):

| Ambang | Jumlah versi | Cakupan data berversi |
|--------|--------------|----------------------|
| ≥30 | 86 | 97,6% |
| **≥100** | **66** | **96,4%** |
| ≥200 | 64 | 95,9% |
| ≥500 | 56 | 92,4% |

---

## 5. Karakteristik yang Mengikat Desain Fase Berikutnya

| Temuan | Angka terukur | Konsekuensi |
|--------|---------------|-------------|
| **Asimetri panjang antar kelas** | Bintang 5: 4,4 kata · Bintang 1: 20,8 kata | Evaluasi ganda `full` vs `informative_ge5w` menjadi **wajib** di Fase 3 |
| **Ulasan sangat pendek** | 39.859 (39,9%) hanya ≤2 kata | Akurasi pada test set penuh melebih-lebihkan kemampuan model |
| **Duplikasi teks** | 32.101 (32,1%) total; hanya 2,0% pada kelas negatif | Deduplikasi diterapkan **hanya** pada training set (Fase 3) |
| **Kelas netral tipis** | 3.534 (3,5%), rasio 1:19 terhadap positif | Skema biner sebagai model utama (H-3); 3 kelas sebagai eksperimen |
| **Baseline mayoritas** | **72,3%** akurasi | Angka yang wajib dikalahkan; dicantumkan di setiap tabel hasil |
| **`Likes` timpang** | 83,7% bernilai nol; median 0 | Bukan fitur model; hanya filter sekunder dashboard |
| **Data temporal sehat** | 20 bulan, tanpa *gap*, 3.620–6.641/bulan | Analisis tren layak; Mei 2024 (1.879) ditandai periode parsial |

---

## 6. Pemetaan Nama Kolom untuk Revisi Naskah

Naskah awal mengasumsikan konvensi *google-play-scraper*. Berkas aktual memakai
nama berbahasa Indonesia dari pengunggah Kaggle. Tabel ini dipakai saat
menyusun `docs/koreksi-naskah.md` di Fase 9.

| Naskah (asumsi awal) | Berkas aktual |
|----------------------|---------------|
| `content` | `Ulasan` |
| `score` | `Rating` |
| `at` | `Tanggal` |
| `reviewCreatedVersion` | `Versi App` |
| `thumbsUpCount` | `Likes` |
| — | `Nama User` |

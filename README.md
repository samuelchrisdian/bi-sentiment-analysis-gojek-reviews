# Analisis Sentimen & Dashboard Ulasan Gojek

## Ringkasan

Sistem analisis sentimen dan ekstraksi topik keluhan atas **100.000 ulasan
aplikasi Gojek** di Google Play Store (21 Mei 2024 – 31 Desember 2025), lengkap
dengan dashboard *business intelligence* untuk menelusuri hasilnya. Label
sentimen diturunkan dari rating bintang dengan skema **biner** (1–2★ negatif,
4–5★ positif; 3★ dikeluarkan), empat model klasik dibandingkan pada dua set
evaluasi, dan model terpilih menskor seluruh korpus secara *batch* ke
PostgreSQL. Sembilan kategori keluhan diekstraksi dengan LDA lalu dipetakan ke
label bisnis. Hasil akhirnya: **macro-F1 0,9336** pada model produksi terhadap
baseline mayoritas 0,4196, dan peringkat kategori keluhan yang dapat ditelusuri
sampai ke teks ulasan aslinya di dashboard.

## Temuan Utama

- **Model produksi: LogisticRegression** (`C=1.0`, `class_weight="balanced"`,
  TF-IDF 1–2 gram) — macro-F1 **0,9336** pada set `full` vs **0,9078** pada set
  `informative_ge5w`. Recall negatif 0,9316 (`full`) dan 0,9536
  (`informative_ge5w`); akurasi 0,9459.
- **Baseline mayoritas: 72,3% akurasi / macro-F1 0,4196.** Keempat model
  mengungguli baseline pada macro-F1 dengan selisih besar; rentang antar-model
  sendiri hanya **1,88 poin** (0,9153–0,9341), sehingga pemilihan model
  produksi ditentukan oleh interpretabilitas dan bentuk kesalahan, bukan oleh
  skor.
- **Selisih `full` vs `informative_ge5w`: 2,59 poin macro-F1** → akurasi pada
  test set penuh **melebih-lebihkan** kemampuan model, karena 39,9% ulasan
  hanya berisi ≤2 kata dan hampir seluruhnya positif. Set kedua adalah ukuran
  kemampuan yang sesungguhnya pada teks yang membawa informasi.
- **48% kesalahan model bukan kesalahan model.** Pemeriksaan manual 50 kesalahan
  menunjukkan hampir separuhnya adalah rating bintang yang bertentangan dengan
  isi ulasan — 22 dari 24 kasus adalah pengguna yang memberi 4–5★ sambil menulis
  keluhan. Plafon akurasi realistis pada dataset ini ≈0,974, bukan 1,000, dan
  model sudah mencapai **97,1%** dari plafon itu.
- **5 kategori keluhan teratas** (dari 9 kategori, seluruh korpus):

  | # | Kategori | Ulasan | Total likes | % negatif |
  |---|----------|--------|-------------|-----------|
  | 1 | Ketersediaan & Respons Mitra Driver | 9.663 | 25.913 | 36,15% |
  | 2 | Pesanan GoFood & Pembatalan | 9.155 | 27.805 | 34,25% |
  | 3 | Tarif, Ongkir & Promo | 6.939 | 17.754 | 25,96% |
  | 4 | Layanan Pelanggan & Penanganan Keluhan | 6.916 | 20.941 | 25,87% |
  | 5 | Transaksi & Saldo GoPay | 4.874 | 11.869 | 18,23% |

- **Eksperimen 3 kelas dijalankan dan gagal seperti diprediksi**: macro-F1
  0,6470 vs 0,9341 pada skema biner — turun **28,7 poin**. Kegagalan ini
  dilaporkan sebagai temuan, bukan disembunyikan (`docs/three_class_experiment.md`).

## Arsitektur

Empat lapisan, dengan satu batas yang menentukan seluruh desainnya: **model
tidak pernah dipanggil saat request dashboard.**

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. DATA & ML (batch, offline)                       ml/src/*.py     │
│                                                                     │
│    ulasan_com.gojek.app.csv (100.000 baris)                         │
│      → ingest      validasi skema + hash SHA-256                    │
│      → preprocess  normalisasi slang, stopword non-negasi, stemming │
│      → train/tune  4 model × 2 set evaluasi, GridSearchCV           │
│      → finalize    artefak model produksi (joblib)                  │
│      → topics      LDA k=9 + pemetaan ke kategori bisnis            │
│      → score       skoring BATCH seluruh korpus                     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ load_reviews / load_scores / load_metrics
┌───────────────────────────────▼─────────────────────────────────────┐
│ 2. PENYIMPANAN                                    PostgreSQL 16     │
│    reviews · review_scores · review_topics · topics · model_metrics │
│    + materialized view agregat (ml/sql/002) & view API (ml/sql/003) │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ SQLAlchemy — SELECT agregat saja
┌───────────────────────────────▼─────────────────────────────────────┐
│ 3. API                                    FastAPI · api/*.py :8000  │
│    /api/kpi  /api/trend  /api/versions  /api/topics                 │
│    /api/topics/{id}/reviews  /api/model/metrics  /api/health        │
│    /api/predict — demo kapabilitas, BUKAN sumber data dashboard     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTP/JSON (axios)
┌───────────────────────────────▼─────────────────────────────────────┐
│ 4. DASHBOARD                  Vue 3 · Pinia · ECharts · nginx :5173 │
│    KPI · tren · per-versi · peringkat topik · drill-down ulasan     │
│    · perbandingan model · demo prediksi                             │
└─────────────────────────────────────────────────────────────────────┘
```

**Catatan penting:** dashboard **tidak** memanggil model saat request. Seluruh
prediksi dilakukan sekali secara *batch* (`ml/src/score.py`) dan disimpan di
tabel `review_scores`. Endpoint `/api/predict` ada semata sebagai demo
kapabilitas di halaman dashboard. Konsekuensinya: waktu respons dashboard tidak
bergantung pada kecepatan inferensi, dan mengganti model berarti menjalankan
ulang skoring batch — bukan menyentuh API.

## Cara Menjalankan

### Prasyarat

| Kebutuhan | Versi terverifikasi | Untuk |
|-----------|--------------------|-------|
| Docker + Docker Compose | v2 | jalur Docker (direkomendasikan) |
| Python | 3.12.3 | pipeline ML |
| Node.js | 24.x | dashboard mode dev |
| PostgreSQL | 16 | disediakan container `db` |

Berkas data mentah `data/raw/ulasan_com.gojek.app.csv` **tidak ikut di-commit**
(lihat `.gitignore`). Unduh dari sumbernya — lihat [Lisensi & Sumber
Data](#lisensi--sumber-data) — dan letakkan di path tersebut sebelum
menjalankan pipeline.

### Menjalankan dengan Docker (direkomendasikan)

```bash
cp .env.example .env            # nilai default sudah cocok untuk lokal
docker compose up -d --build    # db + api + web
```

Tunggu `db` sehat (`docker compose ps` → `healthy`), lalu isi datanya dengan
salah satu dari dua jalur di bawah. Setelah itu buka **http://localhost:5173**
(API di http://localhost:8000, Swagger di http://localhost:8000/docs).

**Jalur cepat — restore dump (untuk demo):**

```bash
gunzip -c docs/db_dump.sql.gz | docker exec -i gojek_db psql -U gojek -d gojek_sentiment
```

**Jalur lengkap — jalankan pipeline ML dari awal:** lihat bagian berikutnya.

Memulai dari kondisi benar-benar bersih (menghapus volume database):

```bash
docker compose down -v && docker compose up -d --build
```

### Menjalankan pipeline ML dari awal

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -c ml/requirements.txt -r ml/requirements.txt
./ml/run_pipeline.sh
```

`run_pipeline.sh` menjalankan seluruh rantai secara berurutan — ingest →
preprocess → load_reviews → train → tune → finalize → topics → topic_assign →
score → load_scores → load_metrics → materialized view. Urutannya mengikuti
dependensi *foreign key* yang sebenarnya, bukan nomor fase.

Perlu ≈30–45 menit pada mesin kelas laptop; bagian terberatnya adalah stemming
Sastrawi atas 100.000 ulasan dan GridSearchCV. **Untuk demo, pakai jalur restore
dump di atas** dan hindari menjalankan ulang seluruh pipeline.

Container `api` me-*mount* `ml/artifacts/` dan `data/processed/` dari host
secara *read-only* — artefak model dibuat di host oleh pipeline, API hanya
membacanya. Menjalankan pipeline karenanya wajib sebelum `/api/predict` bisa
dipakai.

### Menjalankan tanpa Docker (dev)

```bash
# 1. Database saja lewat Docker (paling praktis)
docker compose up -d db

# 2. API
source .venv/bin/activate
pip install -r api/requirements.txt
uvicorn api.main:app --reload --port 8000

# 3. Dashboard
cd web && npm ci && npm run dev      # http://localhost:5173
```

`web/.env.development` sudah mengarah ke API lokal. Saat build Docker, alamat
API di-*inline* ke dalam bundel lewat build arg `VITE_API_BASE` — mengubahnya di
`environment:` compose tidak berpengaruh pada bundel yang sudah jadi.

## Struktur Repositori

```
.
├── docker-compose.yml         3 service: db, api, web
├── .env.example               kredensial lokal (salin ke .env)
├── ml/
│   ├── config.yaml            sumber kebenaran tunggal seluruh parameter
│   ├── run_pipeline.sh        orkestrasi end-to-end
│   ├── requirements.txt       versi terkunci eksak
│   ├── src/                   ingest, preprocess, train, tune, finalize,
│   │                          topics, score, loader DB, visualisasi
│   ├── notebooks/             01_eda, 02_model_comparison (+ builder .py)
│   ├── sql/                   001_schema, 002_matviews, 003_api_views
│   └── artifacts/             model & report (tidak di-commit)
├── api/                       FastAPI: main, crud, models, schemas, ml_service
├── web/                       Vue 3 + Pinia + ECharts, nginx untuk produksi
├── data/                      raw & processed (tidak di-commit)
└── docs/
    ├── data_contract.md       kontrak kolom & tipe
    ├── data_provenance_notes.md
    ├── model_decision.md      keputusan model produksi (H-10)
    ├── error_analysis.md      analisis 50 kesalahan
    ├── three_class_experiment.md
    ├── topic_extraction_findings.md · topic_labeling_rules.md
    ├── limitations.md         7 keterbatasan eksplisit
    ├── koreksi-naskah.md      daftar koreksi untuk naskah eksternal
    ├── repro_test.md          catatan uji reprodusibilitas
    ├── tables/                seluruh angka yang dikutip, sebagai CSV
    └── figures/final/         Gambar 1–13, 300 dpi
```

## Keputusan Metodologis Penting

### 1. Skema biner, bukan 3 kelas

Rating 3★ hanya 3.534 ulasan (3,5%) — rasio **1:19** terhadap kelas positif.
Alih-alih menyatakan bahwa kelas netral "terlalu kecil", skema 3 kelas
**dijalankan** dengan protokol identik: macro-F1 **0,6470** vs **0,9341** pada
skema biner, turun 28,7 poin. Yang membatasi bukan *hyperparameter* melainkan
contoh netral yang tidak terpisahkan secara leksikal dari kelas negatif.
Bukti: `docs/three_class_experiment.md`, Gambar 7.

### 2. Evaluasi ganda: `full` vs `informative_ge5w`

39,9% ulasan hanya berisi ≤2 kata ("bagus", "mantap"), dan hampir seluruhnya
positif — ulasan 5★ rata-rata 4,4 kata, sementara 1★ mencapai 20,8 kata.
Mengevaluasi hanya pada test set penuh berarti menghitung "bagus" → positif
sebagai keberhasilan model. Karena itu **setiap** model dilaporkan pada dua set:
`full` dan `informative_ge5w` (≥5 kata). Selisih 2,59 poin pada model produksi
adalah ukuran seberapa besar set penuh melebih-lebihkan kemampuan.
Bukti: Gambar 11, `docs/model_comparison_findings.md`.

### 3. ComplementNB (bukan hanya MultinomialNB) dan LinearSVC (bukan SVC-RBF)

ComplementNB dirancang untuk kelas tak seimbang — pada data 72% positif ini
bukan pilihan kosmetik, dan hasilnya terlihat: recall negatif tertinggi (0,9553)
meski macro-F1 terendah. LinearSVC dipilih menggantikan SVC kernel RBF karena
pada TF-IDF berdimensi 30.000 fitur, kernel non-linear menambah biaya latih
ordo besaran tanpa keuntungan yang terbukti — LinearSVC selesai dalam 1,44 detik.

**Model produksi jatuh pada LogisticRegression**, bukan pada skor tertinggi.
Kerangka keputusan menetapkan: bila LinearSVC unggul ≥2 poin, ia menjadi model
produksi dengan kalibrasi; bila selisihnya <2 poin, pilih model yang lebih
sederhana dan menghasilkan probabilitas langsung. Selisihnya **0,03 poin** —
meleset dua orde besaran dari ambang. LogisticRegression juga menghasilkan 56
alarm palsu lebih sedikit dengan presisi negatif tertinggi (0,8845).
Bukti: `docs/model_decision.md`.

### 4. Stopword kustom yang mempertahankan negasi

Daftar stopword standar bahasa Indonesia membuang `tidak`, `bukan`, `jangan`,
`belum` — kata yang justru membalik polaritas kalimat. Membuangnya membuat
"tidak bagus" dan "bagus" menjadi vektor yang identik. Daftar stopword proyek
ini mempertahankan seluruh penanda negasi, dan TF-IDF memakai n-gram 1–2
sehingga "tidak bagus" tertangkap sebagai satu fitur.
Bukti: `ml/src/stopwords.py`, `docs/preprocessing_validation.md`.

### 5. Ambang versi ≥100 ulasan; 21,9% versi kosong tidak diimputasi

Terdapat 291 versi aplikasi unik, sebagian hanya berisi segelintir ulasan —
proporsi sentimennya tidak bermakna secara statistik. Analisis per-versi
dibatasi pada versi dengan ≥100 ulasan: 66 versi yang mencakup **96,4%** dari
data berversi. Sebanyak 21.910 baris (21,9%) tidak mencantumkan versi sama
sekali dan **tidak diimputasi** — baris itu dikeluarkan dari analisis per-versi
dan tetap dipakai di seluruh analisis lain.
Bukti: `docs/tables/cakupan_versi.csv`, Gambar 5.

## Keterbatasan

Tujuh keterbatasan dinyatakan lengkap dengan angka pendukungnya di
**[`docs/limitations.md`](docs/limitations.md)**. Ringkasnya: label berasal dari
rating bintang dan bukan anotasi manusia; ulasan sangat pendek membuat metrik
pada test set penuh optimistis; kelas netral dikeluarkan; seperlima data tidak
punya versi aplikasi; pelabelan kategori topik subjektif (Cohen's κ = 0,4621,
*moderate*); data statis satu periode tanpa evaluasi *concept drift*; dan sistem
adalah prototipe lokal yang tidak di-*deploy* ke produksi.

## Lisensi & Sumber Data

Dataset berasal dari Kaggle: **"Gojek App Reviews Indonesia — Google Play
Store"**, pengunggah `pandaa12`, versi 1 —
<https://www.kaggle.com/datasets/pandaa12/gojek-app-reviews-indonesia-google-play-store>

Berkas dipakai **apa adanya, tanpa modifikasi oleh peneliti**: penamaan kolom
berbahasa Indonesia (`Ulasan`, `Rating`, `Tanggal`, `Versi App`, `Likes`,
`Nama User`) berasal dari pengunggah dataset. SHA-256 berkas yang dipakai:
`9b7f8e50737f9f17bce4ab8a44f7d2f8587deea86c6ad175e2579932cc22b524`.
Karena dataset berasal dari unggahan pihak ketiga, metode pengambilan data asli
tidak dapat diverifikasi — konsekuensinya dicatat di `docs/limitations.md` dan
`docs/data_provenance_notes.md`.

Kode dalam repositori ini dibuat untuk keperluan penelitian akademik. Hak atas
teks ulasan tetap pada penulis masing-masing dan Google Play Store.

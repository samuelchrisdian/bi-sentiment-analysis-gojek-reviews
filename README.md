# Analisis Sentimen & Dashboard Ulasan Gojek

## Ringkasan

Sistem analisis sentimen dan ekstraksi topik keluhan atas **526.322 ulasan
aplikasi Gojek** di Google Play Store (1 Oktober 2021 – 30 September 2026,
60 bulan penuh), lengkap dengan dashboard *business intelligence* untuk
menelusuri hasilnya. Data diambil sendiri oleh peneliti dengan
`google-play-scraper`; ulasan yang dominan berbahasa Inggris diterjemahkan ke
bahasa Indonesia sebelum dianalisis. Label sentimen diturunkan dari rating
bintang dengan skema **biner** (1–2★ negatif, 4–5★ positif; 3★ dikeluarkan),
empat varian model dari tiga keluarga algoritma klasik dibandingkan pada dua
set evaluasi, dan model produksi menskor seluruh korpus secara *batch* ke
PostgreSQL. Lima kategori keluhan diturunkan dari LDA lalu dinamai penulis.
Hasil akhirnya: **macro-F1 0,9261** pada model produksi terhadap baseline
mayoritas 0,4154, peringkat kategori keluhan yang dapat ditelusuri sampai ke
teks ulasan aslinya, dan pola proporsi ulasan negatif menurut bulan dan versi
aplikasi.

<!-- src: docs/synthesis/facts.yaml (dataset, model.produksi, model.baseline, topik) -->

## Temuan Utama

- **Model produksi: LogisticRegression** (`C=1.0`, `class_weight="balanced"`,
  TF-IDF 1–2 gram): macro-F1 **0,9261** pada set `full` dan **0,8951** pada set
  `informative_ge5w`. Recall negatif 0,9192 (`full`) dan 0,9442
  (`informative_ge5w`); akurasi 0,9383.
- **Baseline mayoritas: akurasi 71,1%, macro-F1 0,4154.** Keempat varian
  mengungguli baseline dengan selisih besar. Rentang macro-F1 antar-varian
  hanya **2,33 poin** (0,9037–0,9270), dan LinearSVC unggul atas
  LogisticRegression hanya **0,08 poin** (0,9270 vs 0,9261), jauh di bawah ambang
  2 poin pada kerangka keputusan. Karena itu model produksi dipilih menurut
  kerangka keputusan (model yang lebih sederhana dan langsung menghasilkan
  probabilitas), bukan menurut skor tertinggi.
- **Selisih `full` vs `informative_ge5w`: 3,10 poin macro-F1.** Akurasi pada
  test set penuh **melebih-lebihkan** kemampuan model, karena 40,6% ulasan hanya
  berisi ≤2 kata dan sebagian besar positif (56,2% ulasan positif berisi ≤2 kata,
  dibanding 6,5% ulasan negatif). Set kedua adalah ukuran kemampuan yang lebih
  jujur pada teks yang membawa informasi.
- **Separuh kesalahan model bukan kesalahan model.** Pemeriksaan manual atas
  50 kesalahan LinearSVC menunjukkan 25 (50%) adalah rating bintang yang
  bertentangan dengan isi ulasan; 23 di antaranya adalah pengguna yang memberi
  4–5★ sambil menulis keluhan. Bila proporsi ini berlaku umum, plafon akurasi
  realistis pada data ini ≈0,9695, bukan 1,000, dan model produksi sudah
  mencapai **96,8%** dari plafon itu.
- **Lima kategori keluhan** (urut frekuensi, persentase dari 145.924 ulasan
  negatif; satu ulasan dapat masuk lebih dari satu kategori, dan 77,25% ulasan
  negatif memperoleh minimal satu kategori):

  | # | Kategori | Ulasan | Total likes | % ulasan negatif |
  |---|----------|--------|-------------|------------------|
  | 1 | Pencarian & Penugasan Driver, Waktu Tunggu & Pembatalan Pesanan | 55.745 | 144.538 | 38,20% |
  | 2 | Layanan Pelanggan & Penanganan Keluhan | 41.154 | 148.724 | 28,20% |
  | 3 | Tarif, Ongkir & Promo | 36.061 | 91.095 | 24,71% |
  | 4 | Transaksi, Saldo & Pemblokiran GoPay | 32.251 | 73.579 | 22,10% |
  | 5 | Kendala Penggunaan Aplikasi & Akses Akun | 18.331 | 47.601 | 12,56% |

  <!-- src: docs/tables/topics_ranked.csv; facts.yaml topik -->

  Jumlah topik LDA terpilih k=5 (koherensi c_v 0,5908) **jatuh di batas bawah**
  rentang pemindaian 5–12, sehingga salah satu kriteria hipotesis tema keluhan
  tidak terpenuhi. Hal ini dilaporkan apa adanya; rentang tidak diubah setelah
  hasil dibaca.
- **Pola sentimen menurut waktu dan versi.** Menurut prediksi model produksi,
  31,98% seluruh ulasan bernada negatif. Proporsi bulanan bergerak dari 20,67%
  (Juni 2022) sampai 56,62% (September 2026); di antara 198 versi minor dengan
  ≥100 ulasan, proporsinya berkisar 17,66% (versi 4.13) sampai 60,63% (versi
  5.75). Uji χ² menolak keseragaman proporsi negatif antarversi. Aturan penandaan
  rilis (naik ≥5 poin dari versi sebelumnya dan uji z satu sisi dengan koreksi
  Benjamini–Hochberg q < 0,05) menandai 23 dari 197 perbandingan berurutan; 16 di
  antaranya juga ditandai bila memakai label rating (`ml/src/rm3.py`,
  `docs/tables/rm3_uji_versi.csv`). Ini asosiasi, bukan sebab-akibat.
- **Eksperimen 3 kelas dijalankan dan dilaporkan sebagai temuan**: macro-F1
  0,6617 vs 0,9270 pada skema biner (turun **26,5 poin**); recall kelas netral
  hanya 0,1872 (`docs/three_class_experiment.md`).

<!-- src: docs/synthesis/facts.yaml (model, asimetri_panjang, analisis_kesalahan, topik, pola_sentimen_rm3, tiga_kelas) -->

## Arsitektur

Empat lapisan, dengan satu batas yang menentukan seluruh desainnya: **model
tidak pernah dipanggil saat request dashboard.**

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. DATA & ML (batch, offline)                       ml/src/*.py     │
│                                                                     │
│    scrape_5_tahun.py → gojek_reviews_5Y.csv (526.329 baris)         │
│      → translate   ulasan dominan Inggris → bahasa Indonesia        │
│      → ingest      validasi skema, buang 7 ulasan kosong (526.322)  │
│      → preprocess  normalisasi slang, stopword non-negasi, stemming │
│      → train/tune  4 varian × 2 set evaluasi, GridSearchCV          │
│      → finalize    artefak model produksi (joblib)                  │
│      → topics      LDA k=5..12 pada korpus negatif                  │
│      → topic_assign penetapan 5 kategori berbasis kata kunci        │
│      → score       skoring BATCH seluruh korpus                     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ load_reviews / load_scores / load_metrics
┌───────────────────────────────▼─────────────────────────────────────┐
│ 2. PENYIMPANAN                          PostgreSQL 16 · host :5434  │
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
│    KPI · tren · per-versi · peringkat kategori · drill-down ulasan  │
│    · perbandingan model · demo prediksi                             │
└─────────────────────────────────────────────────────────────────────┘
```

**Catatan penting:** dashboard **tidak** memanggil model saat request. Seluruh
prediksi dilakukan sekali secara *batch* (`ml/src/score.py`) dan disimpan di
tabel `review_scores`. Endpoint `/api/predict` ada semata sebagai demo
kapabilitas di halaman dashboard. Konsekuensinya: waktu respons dashboard tidak
bergantung pada kecepatan inferensi, dan mengganti model berarti menjalankan
ulang skoring batch, bukan menyentuh API.

## Cara Menjalankan

### Prasyarat

| Kebutuhan | Versi terverifikasi | Untuk |
|-----------|--------------------|-------|
| Docker + Docker Compose | v2 | jalur Docker (direkomendasikan) |
| Python | 3.12.3 | pipeline ML (`.venv`) dan terjemahan (`.venv-translate`) |
| Node.js | 24.x | dashboard mode dev |
| PostgreSQL | 16 | disediakan container `db` (port host **5434**) |

Data mentah (`data/raw/`), teks terjemahan (`data/interim/`), data olahan
(`data/processed/`), artefak model (`ml/artifacts/`), dan dump basis data
(`docs/db_dump.sql.gz`) **tidak ikut di-commit** (lihat `.gitignore`). Data
mentah dibuat ulang dengan skrip scraping (langkah 1 di bawah); dump basis data
diminta dari pemilik proyek atau dibuat sendiri dari basis data yang sudah
terisi (`docs/repro_test.md` §5).

### Menjalankan dengan Docker (direkomendasikan)

```bash
cp .env.example .env            # nilai default sudah cocok untuk lokal
docker compose up -d --build    # db + api + web
```

Tunggu `db` sehat (`docker compose ps` → `healthy`), lalu isi datanya dengan
salah satu dari dua jalur di bawah. Setelah itu buka **http://localhost:5173**
(API di http://localhost:8000, Swagger di http://localhost:8000/docs).
PostgreSQL dapat dihubungi dari host di `localhost:5434` (di dalam jaringan
compose, container `api` memakai `db:5432`).

**Jalur cepat — restore dump (untuk demo):**

Letakkan `docs/db_dump.sql.gz` (±44 MB) di folder `docs/`, lalu:

```bash
docker cp docs/db_dump.sql.gz gojek_db:/tmp/data.sql.gz
docker exec gojek_db sh -c "psql -q -U gojek -d gojek_sentiment \
  -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;' \
  && gunzip -c /tmp/data.sql.gz | psql -q -U gojek -d gojek_sentiment"
```

Skema dikosongkan lebih dulu karena saat pertama kali dinyalakan, container
`db` sudah membuat tabel dari `ml/sql/` (folder itu di-*mount* ke
`docker-entrypoint-initdb.d`), sedangkan dump membuat ulang seluruh tabelnya
sendiri. Dump ini memulihkan 526.322 ulasan, 2.631.610 baris skor (lima varian
model × 526.322 ulasan), 183.542 penetapan kategori, 20 baris metrik model, dan
kedelapan materialized view dalam keadaan terisi; cukup untuk menjalankan
seluruh dashboard tanpa menyentuh pipeline ML. Tanda berhasil: kartu **Total
ulasan** di dashboard menunjukkan **526.322** dengan rentang 1 Okt 2021 – 30 Sep
2026.

Dump tidak memuat artefak model. Tanpa isi `ml/artifacts/` (dibuat pipeline,
tidak di-commit), seluruh dashboard tetap jalan, tetapi demo prediksi
(`/api/predict`) mengembalikan 503 dan `/api/health` berstatus `degraded`.
Salin artefak dari pemilik proyek atau jalankan pipeline sampai langkah
`finalize` agar demo itu aktif.

Dump dibuat dengan `pg_dump` 16.15. Bila restore gagal dengan pesan
`invalid command \restrict`, image `postgres:16-alpine` di komputer Anda terlalu
lama: jalankan `docker compose pull db`, nyalakan ulang, lalu ulangi restore.

**Jalur lengkap — jalankan pipeline ML dari awal:** lihat bagian berikutnya.

Memulai dari kondisi benar-benar bersih (menghapus volume basis data):

```bash
docker compose down -v && docker compose up -d --build
```

### Menjalankan pipeline ML dari awal

**Lingkungan Python.** Pipeline memakai dua lingkungan terpisah. `.venv` utama
mengunci NumPy 1.26.4 karena gensim 4.3.3 menuntut NumPy <2, sedangkan torch
pada lingkungan terjemahan menuntut NumPy 2.

```bash
# Lingkungan utama
python3 -m venv .venv
.venv/bin/pip install -c ml/requirements.txt -r ml/requirements.txt
.venv/bin/pip install google-play-scraper==1.2.7     # hanya untuk scraping

# Lingkungan terjemahan (tanpa pip bawaan; pip dipasang lewat pip milik .venv)
python3 -m venv --without-pip .venv-translate
.venv/bin/pip --python .venv-translate/bin/python install pip
.venv-translate/bin/pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
.venv-translate/bin/pip install transformers==5.19.0 sentencepiece==0.2.2 \
    sacremoses==0.2.0 pandas==3.0.6 pyyaml==6.0.3
```

Versi di atas adalah versi yang terpasang saat penelitian dijalankan
(`.venv-translate`: torch 2.14.1+cpu, transformers 5.19.0, NumPy 2.5.4,
pandas 3.0.6). Versi torch dan transformers juga tercatat di
`data/interim/terjemahan_inggris.meta.json`.

**Urutan langkah.** Perintah di bawah dijalankan dari akar repo dengan
`.venv` aktif (`source .venv/bin/activate`), kecuali langkah terjemahan.
Langkah bertanda ✋ adalah pekerjaan manusia; hasilnya disimpan di
`docs/tables/` dan dibaca oleh langkah berikutnya.

```bash
# 1. Scraping Google Play: lang="id" lalu lang="en", negara Indonesia,
#    Sort.NEWEST, 1 Okt 2021 – 30 Sep 2026 → data/raw/gojek_reviews_5Y.csv
#    (+ .meta.json). Progres disimpan di checkpoint; run yang terputus cukup
#    dijalankan ulang.
python data/script-scraping/scrape_5_tahun.py

# 2. Terjemahan ulasan dominan Inggris (MarianMT Helsinki-NLP/opus-mt-en-id,
#    revisi terkunci, beam 4, per kalimat) → data/interim/terjemahan_inggris.csv
.venv-translate/bin/python -m ml.src.translate
#    ✋ Audit terjemahan: docs/tables/audit_terjemahan_sampel_50_reviewed.csv

# 3. Kamus slang dari isian manusia → ml/src/slang_dict.py
#    ✋ Isian: token_normalisasi_terisi.csv, token_normalisasi_tambahan.csv,
#       unknown_tokens_baru_scraping_reviewed.csv
python -m ml.src.build_slang_dict

# 4. (opsional) Validasi skema & cetak SHA-256 berkas mentah; tidak menulis berkas
python -m ml.src.ingest

# 5. Pra-pemrosesan → data/processed/reviews_clean.parquet
python -m ml.src.preprocess
#    ✋ Verifikasi hasil pra-pemrosesan:
#       preprocessing_sample_{100,ronde2,ronde3,ronde4}_reviewed.csv

# 6. Pelatihan, tuning, dan artefak model produksi
python -m ml.src.train
python -m ml.src.tune
python -m ml.src.finalize logistic_regression   # ✋ keputusan: docs/model_decision.md

# 7. Analisis lanjutan model dan gambar
python -m ml.src.three_class
python -m ml.src.interpret
python -m ml.src.error_analysis
#    ✋ Analisis kesalahan: error_analysis_50.csv → error_analysis_50_reviewed.csv
python -m ml.src.viz_cm
python -m ml.src.viz_models

# 8. Topik keluhan (LDA pada korpus negatif ≥5 kata)
python -m ml.src.topics
#    ✋ Penamaan kategori: lda_clusters_for_labeling.csv
#       → lda_clusters_for_labeling_reviewed.csv

# 9. Basis data (modul pemuat membaca DATABASE_URL dari environment)
docker compose up -d db
set -a; source .env; set +a
python -m ml.src.load_reviews
python -m ml.src.topic_assign
#    ✋ Validasi silang penilai independen:
#       cross_validation_sample_50_reviewed.csv (definisi kategori:
#       cross_validation_definisi_kategori.csv)
python -m ml.src.score
python -m ml.src.load_scores
python -m ml.src.load_metrics
docker exec -i gojek_db psql -U gojek -d gojek_sentiment -v ON_ERROR_STOP=1 < ml/sql/002_matviews.sql
docker exec -i gojek_db psql -U gojek -d gojek_sentiment -v ON_ERROR_STOP=1 < ml/sql/003_api_views.sql

# 10. EDA (tabel & gambar deskriptif) dan rekap angka
python -m ml.src.eda
python -m ml.src.collect_facts                 # → docs/synthesis/facts.yaml
```

Urutan pada langkah 9 mengikuti dependensi *foreign key*: `load_reviews` harus
mendahului `topic_assign` dan `load_scores`, karena `review_topics` dan
`review_scores` merujuk tabel `reviews`. `003_api_views.sql` dijalankan setelah
`002_matviews.sql` dan mengandaikan `review_topics` sudah terisi. Bila `psql`
terpasang di host, kedua berkas SQL juga dapat dijalankan langsung ke
`localhost:5434` (DSN di `.env`, tanpa prefiks `+psycopg2`).

`ml/run_pipeline.sh` menjalankan rantai inti secara berurutan (ingest →
preprocess → load_reviews → train → tune → finalize → topics → topic_assign →
score → load_scores → load_metrics → materialized view). Skrip itu
**tidak** mencakup scraping, terjemahan, pembuatan kamus slang, analisis
lanjutan (langkah 7), EDA, maupun `collect_facts`, dan mengandaikan
`data/interim/terjemahan_inggris.csv`, `ml/src/slang_dict.py`, serta isian
manusia di `docs/tables/` sudah ada.

Bagian terberat secara komputasi adalah terjemahan (CPU) dan stemming Sastrawi
atas 526.322 ulasan; GridSearchCV keempat varian memerlukan total 213,1 detik.
**Untuk demo, pakai jalur restore dump di atas** dan hindari menjalankan ulang
seluruh pipeline.

Container `api` me-*mount* `ml/artifacts/` dan `data/processed/` dari host
secara *read-only*: artefak model dibuat di host oleh pipeline, API hanya
membacanya. Karena itu pipeline wajib dijalankan sebelum `/api/predict` bisa
dipakai.

### Langkah manual (pekerjaan manusia)

Seluruh isian manual tersimpan di `docs/tables/` dan dibaca ulang oleh
pipeline atau oleh `collect_facts`, sehingga setiap angka hasil tetap dapat
ditelusuri ke isian manusianya.

| Langkah | Berkas hasil | Hasil |
|---------|--------------|-------|
| Audit terjemahan | `audit_terjemahan_sampel_50_reviewed.csv` | Deteksi bahasa Inggris benar 47/50 (94%); terjemahan layak 43/50 (86%) |
| Kamus slang | `token_normalisasi_terisi.csv`, `token_normalisasi_tambahan.csv`, `unknown_tokens_baru_scraping_reviewed.csv` | Kamus akhir 639 entri (termasuk 60 token baru dari data scraping dan 10 varian negasi) |
| Verifikasi pra-pemrosesan | `preprocessing_sample_100_reviewed.csv`, `preprocessing_sample_ronde{2,3,4}_reviewed.csv` | 4 putaran, 400 sampel; putaran 1–3 menemukan masalah sistemik yang diperbaiki, putaran 4 tidak menemukan lagi masalah yang mengubah makna |
| Penetapan model produksi | `docs/model_decision.md` | LogisticRegression `C=1.0`, `class_weight="balanced"` |
| Analisis kesalahan | `error_analysis_50_reviewed.csv` | 50 kesalahan; 25 (50%) berupa label keliru dari pengguna |
| Penamaan kategori | `lda_clusters_for_labeling_reviewed.csv` | Lima nama kategori final dari penulis |
| Validasi silang | `cross_validation_sample_50_reviewed.csv` → `h9_hasil_kesepakatan.csv` | Cohen's κ 0,543 (moderat); kesepakatan longgar 78%, ketat 62% |

<!-- src: facts.yaml dataset.penanganan_bahasa.audit_manual, preprocessing, analisis_kesalahan, validasi_silang; docs/synthesis/bab-3-pembaruan-data-scraping.md A.3 -->

### Menjalankan tanpa Docker (dev)

```bash
# 1. Basis data saja lewat Docker (paling praktis) — host port 5434
docker compose up -d db

# 2. API
source .venv/bin/activate
pip install -r api/requirements.txt
uvicorn api.main:app --reload --port 8000

# 3. Dashboard
cd web && npm ci && npm run dev      # http://localhost:5173
```

API membaca `DATABASE_URL` dari `.env` (bawaan:
`postgresql+psycopg2://gojek:gojek@localhost:5434/gojek_sentiment`).
`web/.env.development` sudah mengarah ke API lokal. Saat build Docker, alamat
API di-*inline* ke dalam bundel lewat build arg `VITE_API_BASE`; mengubahnya di
`environment:` compose tidak berpengaruh pada bundel yang sudah jadi.

## Struktur Repositori

```
.
├── docker-compose.yml         3 service: db (host :5434), api (:8000), web (:5173)
├── .env.example               kredensial lokal (salin ke .env)
├── data/
│   ├── script-scraping/       scrape_5_tahun.py (skrip scraping)
│   ├── raw/ interim/ processed/   data mentah, terjemahan, olahan (tidak di-commit)
├── ml/
│   ├── config.yaml            sumber kebenaran tunggal seluruh parameter
│   ├── run_pipeline.sh        orkestrasi rantai inti
│   ├── requirements.txt       versi terkunci eksak (.venv utama)
│   ├── src/                   translate, ingest, preprocess, train, tune,
│   │                          finalize, topics, topic_assign, score, loader DB,
│   │                          analisis & visualisasi, collect_facts
│   ├── notebooks/             01_eda, 02_model_comparison (+ builder .py)
│   ├── sql/                   001_schema, 002_matviews, 003_api_views
│   └── artifacts/             model & report (tidak di-commit)
├── api/                       FastAPI: main, crud, models, schemas, ml_service
├── web/                       Vue 3 + Pinia + ECharts, nginx untuk produksi
├── archive/                   arsip lokal hasil versi sebelumnya (tidak di-commit)
└── docs/
    ├── synthesis/facts.yaml   seluruh angka final (dibuat collect_facts)
    ├── data_contract.md       kontrak kolom & tipe
    ├── data_provenance_notes.md
    ├── model_decision.md      keputusan model produksi
    ├── error_analysis.md      analisis 50 kesalahan
    ├── three_class_experiment.md
    ├── topic_extraction_findings.md · topic_labeling_rules.md
    ├── limitations.md         keterbatasan eksplisit
    ├── repro_test.md          catatan uji reprodusibilitas
    ├── tables/                angka sumber & isian manual, sebagai CSV
    └── figures/final/         gambar final, 300 dpi
```

## Keputusan Metodologis Penting

### 1. Skema biner, bukan 3 kelas

Rating 3★ hanya 22.114 ulasan (4,2%), dengan rasio **1:16,2** terhadap kelas
positif. Alih-alih menyatakan bahwa kelas netral "terlalu kecil", skema 3 kelas
**dijalankan** dengan protokol yang sama: macro-F1 **0,6617** vs **0,9270** pada
skema biner, turun 26,5 poin. Recall netral hanya 0,1872, dan 54,8% ulasan
bintang 3 pada data uji diprediksi negatif: contoh netral tidak terpisahkan
secara leksikal dari kelas negatif.
Bukti: `docs/three_class_experiment.md`, Gambar 7.

### 2. Evaluasi ganda: `full` vs `informative_ge5w`

40,6% ulasan hanya berisi ≤2 kata ("bagus", "mantap"), dan sebagian besar
positif: ulasan 5★ rata-rata 4,3 kata, sementara 1★ mencapai 20,3 kata.
Mengevaluasi hanya pada test set penuh berarti menghitung "bagus" → positif
sebagai keberhasilan model. Karena itu **setiap** model dilaporkan pada dua set:
`full` (100.842 ulasan) dan `informative_ge5w` (≥5 kata, 45.069 ulasan).
Selisih 3,10 poin pada model produksi adalah ukuran seberapa besar set penuh
melebih-lebihkan kemampuan.
Bukti: Gambar 11, `docs/model_comparison_findings.md`.

### 3. ComplementNB (bukan hanya MultinomialNB) dan LinearSVC (bukan SVC-RBF)

ComplementNB dirancang untuk kelas tak seimbang. Pada data yang 71,1% positif,
pilihan ini bukan kosmetik, dan hasilnya terlihat: recall negatif tertinggi
(0,9414) meski macro-F1 terendah (0,9037). LinearSVC dipilih menggantikan SVC
kernel RBF karena pada TF-IDF berdimensi 30.000 fitur, kernel non-linear
menambah biaya latih berlipat tanpa keuntungan yang terbukti; LinearSVC
selesai dilatih dalam 9,34 detik.

**Model produksi jatuh pada LogisticRegression**, bukan pada skor tertinggi.
Kerangka keputusan menetapkan: bila LinearSVC unggul ≥2 poin, ia menjadi model
produksi dengan kalibrasi; bila selisihnya <2 poin, pilih model yang lebih
sederhana dan menghasilkan probabilitas langsung (ComplementNB atau
LogisticRegression). Selisihnya **0,08 poin**, sehingga cabang kedua berlaku. Di
antara dua kandidat itu, LogisticRegression unggul pada kedua set evaluasi
(0,9261 vs 0,9037 pada `full`; 0,8951 vs 0,8833 pada `informative_ge5w`).
Dibanding LinearSVC, LogisticRegression menghasilkan 73 alarm palsu lebih
sedikit dengan presisi negatif tertinggi (0,8742). GridSearchCV dan aturan satu
simpangan baku memilih parameter yang sama (`C=1.0`, `class_weight="balanced"`).
Bukti: `docs/model_decision.md`.

### 4. Stopword kustom yang mempertahankan negasi

Daftar stopword standar bahasa Indonesia membuang `tidak`, `bukan`, `jangan`,
`belum`, kata yang justru membalik polaritas kalimat. Membuangnya membuat
"tidak bagus" dan "bagus" menjadi vektor yang identik. Daftar stopword proyek
ini mempertahankan seluruh penanda negasi, varian negasi informal (`gak`,
`gda`, `enggak`, dan lainnya) dibakukan lewat kamus slang, dan TF-IDF memakai
n-gram 1–2 sehingga "tidak bagus" tertangkap sebagai satu fitur.
Bukti: `ml/src/stopwords.py`, `docs/preprocessing_validation.md`.

### 5. Ambang versi ≥100 ulasan; 21,5% versi kosong tidak diimputasi

Terdapat 270 versi minor aplikasi, sebagian hanya berisi segelintir ulasan,
sehingga proporsi sentimennya tidak bermakna secara statistik. Analisis
per-versi dibatasi pada versi minor dengan ≥100 ulasan: 198 versi yang mencakup
**410.313** ulasan (99,4% dari data berversi). Sebanyak 113.357 baris (21,5%)
tidak mencantumkan versi sama sekali dan **tidak diimputasi**: baris itu
dikeluarkan dari analisis per-versi dan tetap dipakai di seluruh analisis lain.
Bukti: `ml/sql/002_matviews.sql` (`agg_version`), Gambar 5.

### 6. Dua putaran scraping dan terjemahan ulasan berbahasa Inggris

Pengambilan dengan `lang="id"` saja menghasilkan 462.528 ulasan; putaran
`lang="en"` (negara tetap Indonesia) menghasilkan 63.801 ulasan lain yang tidak
beririsan sama sekali, dan sebagian besar ternyata berbahasa Indonesia. Temuan
empiris ini menunjukkan Google Play mengelompokkan ulasan menurut bahasa yang
terkait dengan penulisnya, bukan menurut bahasa teksnya (mekanisme internal
Google Play tidak terdokumentasi resmi). Ulasan putaran `lang="en"` juga lebih
negatif (41,0% berating 1–2, dibanding 25,9% pada putaran `lang="id"`), sehingga
mengabaikannya akan membuat korpus tampak lebih positif dari kenyataan.
Sebanyak 14.671 ulasan (2,8%) yang dominan berbahasa Inggris (aturan kata
fungsi, `ml/src/language_filter.py`) diterjemahkan, bukan dibuang; teks aslinya
tetap disimpan untuk audit.
Bukti: `data/raw/gojek_reviews_5Y.meta.json`,
`docs/synthesis/bab-3-pembaruan-data-scraping.md` Bagian A.

## Keterbatasan

Keterbatasan dinyatakan lengkap dengan angka pendukungnya di
**[`docs/limitations.md`](docs/limitations.md)**. Ringkasnya: label berasal dari
rating bintang dan bukan anotasi manusia (separuh sampel kesalahan adalah label
keliru pengguna); ulasan sangat pendek membuat metrik pada test set penuh
optimistis; kelas netral dikeluarkan; 21,5% data tidak punya versi aplikasi;
ulasan berbahasa Inggris dianalisis lewat terjemahan mesin (86% layak pada
audit 50 sampel); pra-pemrosesan masih menyisakan kelemahan minor (angka
dibuang global, sebagian stopword seperti "masih" dan "hanya", stemming kata
berfrekuensi rendah); k LDA terpilih jatuh di batas bawah rentang; pelabelan
kategori topik subjektif (Cohen's κ = 0,543, moderat); data diambil sekali pada
11 Oktober 2026 tanpa evaluasi *concept drift*; penandaan rilis RM3 memakai
tanggal ulasan pertama sebagai proksi tanggal rilis (versi yang sudah ada
sebelum Oktober 2021 tersensor kiri); dan sistem adalah
prototipe lokal yang tidak di-*deploy* ke produksi.

## Lisensi & Sumber Data

Data diambil sendiri oleh peneliti dari Google Play Store dengan pustaka
`google-play-scraper` 1.2.7 (`data/script-scraping/scrape_5_tahun.py`):
aplikasi `com.gojek.app`, negara Indonesia, urutan terbaru (`Sort.NEWEST`),
rentang 1 Oktober 2021 – 30 September 2026, dalam dua putaran `lang="id"` dan
`lang="en"`. Scraping dijalankan pada 11 Oktober 2026; parameter, waktu, dan
jumlah ulasan per putaran tercatat di `data/raw/gojek_reviews_5Y.meta.json`.
Berkas hasil `data/raw/gojek_reviews_5Y.csv` berisi 526.329 baris, SHA-256
`51e87f6b44a25c3da0d4529cf7a006b445525a16fe4a7e52569d83049910937f`. Karena
ulasan di Google Play dapat disunting atau dihapus penulisnya, scraping ulang
di kemudian hari tidak dijamin menghasilkan berkas yang identik.

Versi awal proyek memakai dataset publik Kaggle; dataset itu sudah diganti
dengan data scraping di atas sesuai arahan dosen pembimbing, dan hasil
berbasis Kaggle hanya disimpan sebagai arsip lokal di `archive/kaggle-v1/`.

Kode dalam repositori ini dibuat untuk keperluan penelitian akademik. Hak atas
teks ulasan tetap pada penulis masing-masing dan Google Play Store.

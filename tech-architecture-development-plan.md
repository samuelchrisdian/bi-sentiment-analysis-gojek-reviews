# TECHNICAL ARCHITECTURE & DEVELOPMENT PLAN
## Sistem Analisis Sentimen & Dashboard Analitik Ulasan Gojek

**Peran dokumen:** spesifikasi teknis siap eksekusi untuk agent/developer
**Basis data:** `ulasan_com_gojek_app.csv` (sudah diprofilkan, hasil di Bagian 0)
**Status angka:** seluruh angka pada Bagian 0 adalah hasil pengukuran aktual terhadap file yang diunggah. Angka kinerja model **belum ada** dan tidak diestimasi di dokumen ini.

---

# BAGIAN 0 — HASIL PROFILING DATA

> **Baca bagian ini lebih dulu.** Enam temuan di bawah mengubah beberapa keputusan yang sudah tertulis di Bab 1 dan di rencana awal Anda. Melompat langsung ke Bagian 1 akan menghasilkan arsitektur yang salah asumsi.

## 0.1 Profil Dataset

| Properti | Nilai Terukur |
|----------|---------------|
| Jumlah baris | **100.000** |
| Jumlah kolom | **6** |
| Periode | **21 Mei 2024 – 31 Desember 2025** (20 bulan penuh) |
| Volume bulanan | 1.879 – 6.641 ulasan/bulan |
| Kolom | `Nama User`, `Ulasan`, `Rating`, `Tanggal`, `Likes`, `Versi App` |
| *Missing values* | Hanya `Versi App`: **21.910 baris (21,9%)**. Kolom lain 0. |
| Duplikat baris penuh | 0 |
| Duplikat teks `Ulasan` | **32.101 (32,1%)** |

**Distribusi Rating:**

| Rating | Jumlah | Persentase |
|--------|--------|-----------|
| 1 ★ | 23.178 | 23,2% |
| 2 ★ | 3.554 | 3,6% |
| 3 ★ | 3.534 | 3,5% |
| 4 ★ | 5.083 | 5,1% |
| 5 ★ | 64.651 | 64,7% |

---

## 0.2 Enam Temuan yang Mengubah Desain

### ⚠️ TEMUAN 1 — Nama kolom tidak sesuai Bab 1

Bab 1 Anda menyebut `content`, `at`, `score`, dan `reviewCreatedVersion`. File aktual menggunakan nama berbahasa Indonesia. Ini bukan sekadar soal *rename* di kode — **Bab 1 harus direvisi**, karena saat ini ia mendeskripsikan dataset yang berbeda dari yang Anda pakai.

| Bab 1 (asumsi) | File aktual | Tipe |
|----------------|-------------|------|
| `content` | `Ulasan` | str |
| `score` | `Rating` | int64 |
| `at` | `Tanggal` | str → parse ke datetime |
| `reviewCreatedVersion` | `Versi App` | str |
| `thumbsUpCount` | `Likes` | int64 |
| — | `Nama User` | str |

**Tindakan wajib:** perbarui tabel variabel di Bab 1 dan di dokumen storytelling. Sekaligus pastikan provenans file ini — apakah benar berasal dari dataset Kaggle yang Anda sitasi, atau hasil *scraping* terpisah? Keduanya sah, tetapi metodologinya berbeda dan harus dinyatakan jujur.

---

### 🔴 TEMUAN 2 — Asimetri panjang ulasan antar kelas (paling kritis)

Rata-rata panjang ulasan per rating:

| Rating | Rata-rata kata |
|--------|----------------|
| 1 ★ | **20,8** |
| 2 ★ | **22,4** |
| 3 ★ | 20,0 |
| 4 ★ | 10,0 |
| 5 ★ | **4,4** |

Ulasan bintang 5 rata-rata hanya 4,4 kata; bintang 1 hampir lima kali lebih panjang. Diperkuat data berikut:

- **39.859 ulasan (39,9%) hanya berisi ≤2 kata.**
- Teks paling sering berulang: `Mantap` (2.063×), `mantap` (1.911×), `ok` (1.740×), `Ok` (1.620×), `bagus` (1.403×), `Sangat membantu` (1.149×), `Good` (1.134×).
- Pada kelas negatif, noise ini nyaris tidak ada: dari 26.732 ulasan negatif, hanya **546 duplikat teks (2%)** dan **1.614 berisi ≤2 kata (6%)**.

**Implikasi arsitektural:**

1. Model TF-IDF akan mempelajari korelasi trivial `mantap|bagus|ok|good → positif`. **Akurasi akan terlihat sangat tinggi tanpa model benar-benar memahami sentimen.**
2. Jangan laporkan *accuracy* sebagai metrik utama. Gunakan **macro-F1** dan **recall kelas negatif**.
3. **Wajib: evaluasi ganda.** Selain *test set* penuh, evaluasi pada subset ulasan informatif (≥5 kata). Selisih skor antara keduanya adalah ukuran seberapa besar kinerja model bertumpu pada kata-kata pujian pendek. Ini akan menjadi temuan metodologis terkuat di laporan Anda.
4. Pertimbangkan deduplikasi teks pada *training set* (bukan pada statistik deskriptif) agar 2.063 kemunculan "Mantap" tidak mendominasi pembelajaran.

---

### ⚠️ TEMUAN 3 — Rencana 3 kelas tidak layak secara statistik

Bab 1 revisi Anda menetapkan tiga kelas. Faktanya:

| Skema | Komposisi |
|-------|-----------|
| **3 kelas** | Negatif 26.732 (26,7%) · **Netral 3.534 (3,5%)** · Positif 69.734 (69,7%) |
| **2 kelas** | Negatif 26.732 (27,7%) · Positif 69.734 (72,3%) — 3.534 dikeluarkan (3,5%) |

Kelas netral hanya 3,5% dengan rasio 1:20 terhadap positif. Pada volume ini *recall* netral hampir pasti rendah, dan yang lebih buruk: ulasan bintang 3 rata-rata sepanjang 20 kata — mirip kelas negatif — sehingga sebagian besar akan salah terklasifikasi sebagai negatif.

**Rekomendasi:** gunakan **biner sebagai model utama**, dan jalankan varian 3 kelas sebagai **eksperimen pembanding**. Laporkan kegagalan kelas netral sebagai temuan, bukan sebagai kelemahan yang disembunyikan. Biaya tambahannya kecil (satu kali *run*), nilai akademiknya besar.

Kabar baiknya: mengeluarkan bintang 3 hanya membuang 3,5% data — jauh lebih murah dibanding risiko metodologisnya.

---

### ⚠️ TEMUAN 4 — `Versi App` butuh penanganan eksplisit

- **21.910 baris (21,9%) kosong** → tidak bisa dipakai untuk RM3.
- **291 versi unik** → terlalu banyak untuk satu grafik.

Cakupan data berdasarkan ambang minimum:

| Ambang | Jumlah versi | Cakupan data berversi |
|--------|--------------|----------------------|
| ≥30 ulasan | 86 | 97,6% |
| **≥100 ulasan** | **66** | **96,4%** |
| ≥200 ulasan | 64 | 95,9% |
| ≥500 ulasan | 56 | 92,4% |

**Rekomendasi:** ambang **≥100 ulasan** (66 versi, cakupan 96,4%). Cantumkan ambang ini di keterangan grafik. Untuk visualisasi, agregasi ke level *minor version* (`4.93.x`) agar terbaca.

---

### ℹ️ TEMUAN 5 — `Likes` lemah sebagai fitur pembobot

Median = 0, kuartil ke-75 = 0, rata-rata 1,06, maksimum 2.904. Distribusi sangat timpang — mayoritas ulasan tidak pernah di-*like*.

**Rekomendasi:** jangan jadikan fitur model. Gunakan hanya sebagai **filter sekunder di dashboard** ("tampilkan keluhan dengan Likes tertinggi") untuk menemukan keluhan yang beresonansi.

---

### ℹ️ TEMUAN 6 — Data temporal sehat, RM3 dimensi waktu aman

20 bulan penuh tanpa *gap*, volume 3.600–6.600/bulan (kecuali Mei 2024 yang parsial: 1.879). Analisis tren bulanan layak dilakukan. Kecualikan atau beri catatan pada Mei 2024 karena periodenya tidak penuh.

---

# BAGIAN 1 — REKOMENDASI TECH STACK

## 1.1 Keputusan Arsitektur Utama

> **Dashboard TIDAK memanggil model saat request.**

Ini keputusan terpenting di dokumen ini. Dataset Anda statis (100k baris, periode tertutup). Tidak ada alasan menjalankan inferensi per permintaan HTTP.

| Pendekatan | Kelemahan/Keunggulan |
|------------|---------------------|
| ❌ Inferensi real-time per request | Latensi tinggi, model + vectorizer harus di memori, agregasi lambat, kompleksitas tanpa manfaat |
| ✅ **Pre-scoring batch → simpan ke DB → API serve agregat** | Dashboard sub-100ms, backend ringan, agregasi dilakukan PostgreSQL |

Endpoint inferensi *live* tetap disediakan, tetapi perannya adalah **demo kapabilitas model** (user mengetik ulasan → dapat prediksi), bukan sumber data dashboard.

## 1.2 Diagram Arsitektur

```
┌────────────────────────────────────────────────────────────────┐
│  LAPISAN 1 — OFFLINE / BATCH  (Python, dijalankan sekali)      │
│                                                                │
│   ulasan_com_gojek_app.csv                                     │
│            │                                                   │
│            ▼                                                   │
│   [ ingest.py ]      validasi skema, parse Tanggal, label      │
│            │                                                   │
│            ▼                                                   │
│   [ preprocess.py ]  cleaning · normalisasi · Sastrawi         │
│            │                                                   │
│            ├──────────────┬────────────────┐                   │
│            ▼              ▼                ▼                   │
│   [ train.py ]     [ topics.py ]    [ aggregate.py ]           │
│  NB·SVM·LogReg     n-gram/LDA       metrik harian/versi        │
│            │              │                │                   │
│            ▼              ▼                ▼                   │
│   artifacts/*.joblib   topics.parquet   ─────┐                 │
│            │                                 │                 │
│            └────────► [ score.py ] ──────────┤                 │
│                       prediksi 100k baris    │                 │
└──────────────────────────────────────────────┼─────────────────┘
                                               ▼
┌────────────────────────────────────────────────────────────────┐
│  LAPISAN 2 — PERSISTENSI   PostgreSQL                          │
│  reviews · review_scores · agg_monthly · agg_version · topics  │
└──────────────────────────────┬─────────────────────────────────┘
                               ▼
┌────────────────────────────────────────────────────────────────┐
│  LAPISAN 3 — API           FastAPI + SQLAlchemy + Pydantic     │
│  /kpi  /trend  /versions  /topics  /reviews  /model/metrics    │
│  /predict  ← satu-satunya endpoint yang memuat model           │
└──────────────────────────────┬─────────────────────────────────┘
                               ▼
┌────────────────────────────────────────────────────────────────┐
│  LAPISAN 4 — FRONTEND      Vue 3 + Vite + Pinia + ECharts      │
└────────────────────────────────────────────────────────────────┘
```

## 1.3 Stack per Lapisan

| Lapisan | Pilihan | Alasan |
|---------|---------|--------|
| **Data processing** | Pandas, NumPy | 100k baris — masuk memori tanpa masalah. Tidak perlu Spark/Dask. |
| **NLP Indonesia** | Sastrawi (stemming + stopword), kamus normalisasi *slang* kustom | Wajib untuk teks informal. Siapkan kamus alay→baku sendiri; ini bagian dari kontribusi akademik Anda. |
| **Vektorisasi** | `TfidfVectorizer` (unigram + bigram, `min_df=3`, `max_features≈30.000`) | Bigram penting untuk menangkap "tidak bagus", "gagal bayar". |
| **ML** | Scikit-Learn | Sesuai batasan proposal dan keahlian Anda. |
| **Artifact** | `joblib` + `MANIFEST.json` (hash data, versi lib, timestamp, metrik) | Reprodusibilitas — dosen bisa menuntut ini. |
| **Database** | **PostgreSQL** | Seluruh agregasi dashboard adalah `GROUP BY` + *window function*. Dorong kerja ke DB, bukan ke Python. |
| **Backend** | **FastAPI** (bukan Flask) | Validasi Pydantic otomatis, dokumentasi OpenAPI/Swagger gratis, dukungan async. Swagger auto-generated juga berguna sebagai lampiran laporan. |
| **Frontend** | **Vue 3 + Vite + Pinia + Apache ECharts** | ECharts unggul untuk *time series* dan interaksi *drill-down* dibanding Chart.js. |
| **Deployment** | Docker Compose (3 service: `db`, `api`, `web`) | Satu perintah untuk demo. Penting saat presentasi. |

## 1.4 Catatan: FastAPI vs Laravel

Anda menguasai keduanya, tetapi untuk proyek ini **jangan gunakan Laravel**. Alasannya operasional, bukan preferensi: model, vectorizer, dan pipeline preprocessing hidup di Python. Menaruh API di Laravel memaksa Anda menjalankan dua runtime dan menjembataninya lewat *subprocess* atau antrian — kompleksitas tambahan tanpa manfaat sedikit pun untuk lingkup ini.

FastAPI menempatkan API di runtime yang sama dengan model. Satu bahasa, satu proses *build*, satu container.

## 1.5 Skema Database

```sql
CREATE TABLE reviews (
    id              BIGSERIAL PRIMARY KEY,
    nama_user       TEXT,
    ulasan          TEXT        NOT NULL,
    ulasan_clean    TEXT,
    rating          SMALLINT    NOT NULL CHECK (rating BETWEEN 1 AND 5),
    tanggal         TIMESTAMPTZ NOT NULL,
    likes           INTEGER     NOT NULL DEFAULT 0,
    versi_app       TEXT,                    -- NULL pada 21,9% baris
    versi_minor     TEXT,                    -- turunan: '4.93.1' -> '4.93'
    word_count      SMALLINT,                -- untuk filter subset informatif
    sentimen_aktual SMALLINT                 -- 0=neg, 1=pos, NULL jika rating=3
);

CREATE TABLE review_scores (
    review_id     BIGINT REFERENCES reviews(id) ON DELETE CASCADE,
    model_name    TEXT    NOT NULL,          -- 'complement_nb' | 'linear_svc'
    pred_label    SMALLINT NOT NULL,
    pred_proba    REAL,                      -- NULL jika model tanpa kalibrasi
    PRIMARY KEY (review_id, model_name)
);

CREATE TABLE topics (
    id          SERIAL PRIMARY KEY,
    kategori    TEXT NOT NULL,               -- 'Pembayaran', 'Mitra Driver', ...
    keyword     TEXT NOT NULL,
    bobot       REAL
);

CREATE TABLE review_topics (
    review_id  BIGINT REFERENCES reviews(id) ON DELETE CASCADE,
    topic_id   INTEGER REFERENCES topics(id),
    PRIMARY KEY (review_id, topic_id)
);

CREATE TABLE model_metrics (
    id            SERIAL PRIMARY KEY,
    model_name    TEXT NOT NULL,
    eval_set      TEXT NOT NULL,             -- 'full' | 'informative_ge5w'
    accuracy      REAL, precision_neg REAL,
    recall_neg    REAL, f1_neg REAL, macro_f1 REAL,
    train_seconds REAL,
    created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_reviews_tanggal   ON reviews (tanggal);
CREATE INDEX idx_reviews_versi     ON reviews (versi_minor) WHERE versi_minor IS NOT NULL;
CREATE INDEX idx_reviews_sentimen  ON reviews (sentimen_aktual);
CREATE INDEX idx_reviews_wordcount ON reviews (word_count);
```

Tabel `agg_monthly` dan `agg_version` dibuat sebagai **materialized view** — datanya statis, jadi `REFRESH` cukup sekali setelah *scoring*.

## 1.6 Spesifikasi API

| Method | Endpoint | Query params | Mengembalikan |
|--------|----------|--------------|---------------|
| GET | `/api/kpi` | `from`, `to` | Total ulasan, % negatif, rata-rata rating, jumlah versi |
| GET | `/api/trend` | `from`, `to`, `granularity` | Deret waktu proporsi negatif + volume |
| GET | `/api/versions` | `min_reviews` (default 100) | Proporsi sentimen per versi |
| GET | `/api/topics` | `limit`, `from`, `to` | Peringkat topik keluhan + frekuensi |
| GET | `/api/topics/{id}/reviews` | `sort_by=likes`, `page` | Ulasan mentah per topik (*drill-down*) |
| GET | `/api/model/metrics` | — | Perbandingan NB, SVM & LogReg dari `model_metrics` |
| POST | `/api/predict` | body: `{"text": "..."}` | Prediksi sentimen + probabilitas *(demo)* |

## 1.7 Struktur Repositori

```
gojek-sentiment/
├── docker-compose.yml
├── README.md
├── data/
│   ├── raw/ulasan_com_gojek_app.csv
│   └── processed/
├── ml/
│   ├── config.yaml              # satu sumber kebenaran: threshold, seed, params
│   ├── src/
│   │   ├── ingest.py  preprocess.py  features.py
│   │   ├── train.py   evaluate.py    topics.py
│   │   ├── score.py   load_to_db.py
│   │   └── slang_dict.py
│   ├── notebooks/01_eda.ipynb  02_model_comparison.ipynb
│   └── artifacts/               # *.joblib + MANIFEST.json
├── api/
│   ├── main.py  models.py  schemas.py  crud.py  db.py
│   └── requirements.txt
└── web/
    ├── src/{views,components,stores,api}/
    └── package.json
```

---

# BAGIAN 2 — KOMPARASI NAIVE BAYES, SVM & LOGISTIC REGRESSION

## 2.1 Koreksi Varian Algoritma

Sebelum tabel perbandingan, dua koreksi penting terhadap rencana awal:

**a) Gunakan `ComplementNB`, bukan `MultinomialNB`.**
ComplementNB dirancang khusus untuk data tidak seimbang. Dengan rasio 27:72 pada data Anda, ini pilihan yang lebih tepat. Jalankan keduanya — biayanya beberapa detik — dan laporkan perbandingannya.

**b) Gunakan `LinearSVC`, JANGAN `SVC(kernel='rbf')`.**
Ini bukan preferensi, melainkan batas komputasi. `SVC` berkompleksitas antara O(n²) dan O(n³); pada 100.000 baris, pelatihannya bisa berjam-jam hingga gagal. `LinearSVC` menggunakan *solver* liblinear yang skalabel dan justru unggul pada data teks berdimensi tinggi — kernel non-linear jarang memberi manfaat pada ruang TF-IDF yang sudah hampir terpisah secara linear.

**c) Tambahkan `LogisticRegression` sebagai model ketiga.**

> **Pemutakhiran (H-10, 17 September 2026):** LogisticRegression naik dari
> pembanding menjadi model penuh dalam RM1, dan ditetapkan sebagai model
> produksi. Perbandingannya menjadi **tiga keluarga algoritma dengan empat
> varian terlatih** (ComplementNB, MultinomialNB, LinearSVC,
> LogisticRegression). Dasar dan konsekuensinya: `docs/model_decision.md` §5.3.

Biayanya hampir nol, dan ia menyediakan dua hal yang tidak dimiliki LinearSVC: probabilitas terkalibrasi (untuk indikator keyakinan di dashboard) dan koefisien yang langsung dapat ditafsirkan. Perbandingan tiga model juga lebih kuat secara akademik daripada dua.

## 2.2 Tabel Perbandingan

| Kriteria | ComplementNB | LinearSVC | LogisticRegression |
|----------|--------------|-----------|-----------------------------------|
| **Prinsip** | Probabilistik, asumsi independensi fitur | Margin maksimum, diskriminatif | Probabilistik diskriminatif |
| **Ekspektasi akurasi pada data ini** | Baik pada teks pendek; asumsi independensi terlanggar oleh bigram | Umumnya terbaik pada TF-IDF berdimensi tinggi | Mendekati LinearSVC |
| **Kecepatan latih (100k × ~30k fitur)** | ⚡ **Ordo detik** | Ordo puluhan detik–beberapa menit | Ordo puluhan detik |
| **Kecepatan inferensi** | Sangat cepat | Sangat cepat (dot product) | Sangat cepat |
| **Output probabilitas** | ✅ Native `predict_proba` | ❌ Hanya `decision_function` → butuh `CalibratedClassifierCV` | ✅ Native, terkalibrasi baik |
| **Interpretabilitas** | ✅ Rasio log-probabilitas per kata, intuitif dijelaskan | ⚠️ `coef_` dapat dibaca, tetapi skala bobot tidak intuitif | ✅ Koefisien = log-odds, paling mudah dinarasikan |
| **Ketahanan thd ketidakseimbangan** | Sedang (ComplementNB dirancang untuk ini) | ✅ Baik dengan `class_weight='balanced'` | ✅ Baik dengan `class_weight='balanced'` |
| **Beban tuning** | Rendah — hanya `alpha` | Sedang — `C`, `class_weight`, `max_iter` | Sedang — `C`, `class_weight`, `solver` |
| **Risiko utama pada data ini** | Terlalu mudah "menang" lewat kata pujian pendek | Konvergensi lambat bila `C` terlalu besar | — |

## 2.3 Metrik Evaluasi yang Dilaporkan

**Jangan jadikan *accuracy* metrik utama.** Dengan komposisi 72,3% positif, model yang selalu menebak "positif" langsung memperoleh akurasi 72,3% tanpa mempelajari apa pun. Itulah *baseline* yang harus Anda kalahkan, dan harus dicantumkan eksplisit di laporan.

| Prioritas | Metrik | Alasan |
|-----------|--------|--------|
| 1 | **Recall kelas negatif** | Keluhan yang lolos triase = kegagalan bisnis langsung |
| 2 | **Macro-F1** | Tidak bias terhadap kelas mayoritas |
| 3 | **F1 kelas negatif** | Menyeimbangkan presisi dan recall pada kelas yang dipedulikan |
| 4 | *Accuracy* | Dilaporkan sebagai pelengkap, selalu disandingkan dengan *baseline* 72,3% |
| — | Waktu latih | Diukur dengan `time.perf_counter()`, bukan dikira-kira |

**Protokol evaluasi ganda (wajib — lihat Temuan 2):**

| Set evaluasi | Definisi | Fungsi |
|--------------|----------|--------|
| `full` | Seluruh *test set* | Angka yang biasa dilaporkan |
| `informative_ge5w` | Subset dengan `word_count >= 5` | Kinerja sesungguhnya pada ulasan bermakna |

Selisih macro-F1 antara keduanya adalah temuan metodologis Anda. Jika `full` jauh lebih tinggi, itu bukti kuantitatif bahwa sebagian besar "keberhasilan" model berasal dari kata pujian pendek yang berulang.

## 2.4 Interpretable ML

Untuk kedua model, ekstrak 20 fitur berbobot tertinggi per kelas dan sajikan sebagai tabel di laporan:

```python
# LinearSVC / LogisticRegression
feat = np.array(vectorizer.get_feature_names_out())
coef = model.coef_[0]
top_neg = feat[np.argsort(coef)[:20]]
top_pos = feat[np.argsort(coef)[-20:]]

# ComplementNB
log_ratio = model.feature_log_prob_[0] - model.feature_log_prob_[1]
```

Pertanyaan yang harus Anda jawab dalam pembahasan: apakah kata-kata berbobot tertinggi masuk akal secara domain (`gagal`, `error`, `saldo`, `dipotong`, `dibatalkan`), atau justru artefak (nama orang, tanda baca, *stopword* yang lolos)? Yang kedua menandakan *pipeline* preprocessing perlu diperbaiki.

Untuk penjelasan level instans, `LimeTextExplainer` cukup sebagai pelengkap — tapi opsional, jangan sampai menunda jadwal.

## 2.5 Rekomendasi

Jalankan ketiganya dengan konfigurasi TF-IDF identik dan `random_state` yang sama, lalu putuskan berdasarkan angka Anda sendiri. Kerangka keputusan:

- **Jika LinearSVC unggul macro-F1 ≥2 poin** → jadikan model produksi, bungkus `CalibratedClassifierCV` untuk probabilitas.
- **Jika selisihnya <2 poin** → pilih ComplementNB atau LogisticRegression. Model yang lebih sederhana dan lebih mudah dijelaskan lebih berharga pada konteks akademik dan operasional.
- **Apa pun hasilnya** → laporkan ketiganya. Perbandingan yang menunjukkan model sederhana setara dengan yang kompleks adalah temuan yang sah, bukan kegagalan.

---

# BAGIAN 3 — DEVELOPMENT ROADMAP

Sembilan fase. Estimasi mengasumsikan pengerjaan paruh waktu.

---

## FASE 0 — Fondasi & Reprodusibilitas
**Estimasi: 0,5 hari**

- Inisialisasi repo sesuai struktur 1.7, `git init`, `.gitignore` (kecualikan `data/raw/`, `artifacts/`)
- `requirements.txt` dengan **versi terkunci**
- `ml/config.yaml` sebagai sumber kebenaran tunggal: `random_state: 42`, ambang versi, parameter TF-IDF, rasio *split*
- `docker-compose.yml` untuk PostgreSQL

**Definition of Done:** `docker compose up db` berhasil; `python -c "import sklearn, Sastrawi"` tidak error.

---

## FASE 1 — EDA & Data Contract
**Estimasi: 1 hari** · *Sebagian besar sudah dikerjakan di Bagian 0 — tinggal diformalkan ke notebook*

- Pindahkan seluruh angka Bagian 0 ke `01_eda.ipynb` dengan sel yang benar-benar dijalankan
- Buat visualisasi Gambar 1–5 sesuai dokumen storytelling
- Tulis `data_contract.md`: nama kolom, tipe, aturan validasi, penanganan *null*
- Isi slot `[A-1]` sampai `[A-24]` pada dokumen storytelling

**Definition of Done:** notebook berjalan *end-to-end* dari sel pertama tanpa error; seluruh angka di Bab 1 revisi bersumber dari sini.

---

## FASE 2 — Preprocessing & Desain Label
**Estimasi: 2 hari** · *Fase dengan risiko kualitas tertinggi*

- `preprocess.py`: *case folding* → hapus URL/emoji/angka/tanda baca → normalisasi slang → *stopword removal* → *stemming* Sastrawi
- **Bangun `slang_dict.py`.** Ambil 300–500 token paling sering yang tidak dikenali kamus baku, petakan manual (`gk/ga/nggak → tidak`, `bgt → banget`, `udh → sudah`). Ini pekerjaan manual yang membosankan tetapi berdampak langsung pada kualitas model — dan merupakan kontribusi keilmuan yang Anda klaim di Bab 1.
- Turunkan `word_count`, `sentimen_aktual`, `versi_minor`
- Simpan hasil ke `data/processed/reviews_clean.parquet`

**Definition of Done:** ambil 100 sampel acak sebelum-sesudah, periksa manual. Jika ada teks bermakna yang menjadi kosong setelah preprocessing, perbaiki dulu sebelum lanjut.

⚠️ **Peringatan:** Sastrawi *stemming* pada 100k dokumen lambat (bisa >10 menit). Terapkan *caching* per kata unik — bukan per dokumen. Ini memangkas waktu secara drastis.

---

## FASE 3 — Baseline & Komparasi Model
**Estimasi: 2 hari**

- *Stratified train-test split* 80:20, `random_state` dari config
- **Hitung baseline mayoritas (72,3%) terlebih dahulu** dan catat
- Latih ComplementNB, MultinomialNB, LinearSVC, LogisticRegression dengan TF-IDF identik
- Ukur waktu latih dengan `time.perf_counter()`
- **Evaluasi ganda**: `full` dan `informative_ge5w`
- Simpan seluruh hasil ke `model_metrics`

**Definition of Done:** tabel perbandingan 4 model × 2 set evaluasi terisi penuh; seluruh model mengungguli baseline 72,3% pada macro-F1.

---

## FASE 4 — Tuning & Evaluasi Jujur
**Estimasi: 1,5 hari**

- `GridSearchCV` dengan `scoring='f1_macro'` dan `StratifiedKFold(n_splits=5)`
  - ComplementNB: `alpha ∈ [0.1, 0.5, 1.0, 2.0]`
  - LinearSVC: `C ∈ [0.1, 0.5, 1.0, 5.0]`, `class_weight ∈ [None, 'balanced']`
- *Confusion matrix* untuk model terbaik
- **Analisis kesalahan:** ambil 50 kesalahan klasifikasi, kelompokkan penyebabnya (sarkasme, negasi, campur kode, label keliru dari pengguna). Tulis sebagai subbab tersendiri.
- Ekstraksi fitur teratas (2.4)
- Eksperimen varian 3 kelas, laporkan kegagalan kelas netral
- Simpan artefak + `MANIFEST.json`

**Definition of Done:** model final tersimpan; analisis kesalahan terdokumentasi; `MANIFEST.json` memuat hash data dan seluruh parameter.

---

## FASE 5 — Ekstraksi Topik (RM2)
**Estimasi: 2 hari**

- Analisis frekuensi unigram/bigram pada korpus negatif (26.732 ulasan, relatif bersih — Temuan 2)
- LDA dengan `n_topics ∈ [5..12]`, pilih berdasarkan *coherence score*
- **Pelabelan manual kategori** — ini pekerjaan manusia, bukan otomatis. Petakan klaster ke kategori bisnis: Pembayaran, Mitra Driver, Performa Aplikasi, Tarif & Promo, Layanan Pelanggan, Akurasi Lokasi
- Isi tabel `topics` dan `review_topics`
- Ranking berdasarkan frekuensi **dan** total Likes (dua kolom terpisah — ingat batasan Bab 1 bahwa prioritas hanya berbasis frekuensi)

**Definition of Done:** setiap kategori punya ≥5 kata kunci dan contoh ulasan nyata; peringkat topik siap masuk Tabel 3 dokumen storytelling.

---

## FASE 6 — Scoring & Muat ke Database
**Estimasi: 1 hari**

- `score.py`: prediksi 100k baris → `review_scores`
- `load_to_db.py`: muat `reviews`, `topics`, `review_topics`, `model_metrics`
- Buat *materialized view* `agg_monthly` dan `agg_version` (hormati ambang ≥100 ulasan)
- `REFRESH MATERIALIZED VIEW`

**Definition of Done:** `SELECT count(*) FROM reviews` mengembalikan 100000; seluruh query agregat selesai <200ms.

---

## FASE 7 — Backend API
**Estimasi: 2 hari**

- FastAPI + SQLAlchemy, skema Pydantic untuk semua respons
- Implementasi 7 endpoint (1.6)
- `/predict` memuat artefak sekali saat *startup* (`lifespan` event), bukan per request
- CORS untuk origin dev Vue
- Uji manual lewat Swagger di `/docs`

**Definition of Done:** seluruh endpoint mengembalikan 200 dengan skema valid; Swagger dapat diekspor sebagai lampiran laporan.

---

## FASE 8 — Dashboard Frontend
**Estimasi: 3 hari**

Susunan sesuai rancangan Gambar 7 di dokumen storytelling:

| Komponen | Sumber |
|----------|--------|
| Baris KPI | `/api/kpi` |
| Grafik tren bulanan (garis, sumbu ganda) | `/api/trend` |
| Topik keluhan (batang horizontal) | `/api/topics` |
| Sentimen per versi (batang bertumpuk) | `/api/versions` |
| Tabel ulasan (*drill-down*, urut Likes) | `/api/topics/{id}/reviews` |
| Panel perbandingan model | `/api/model/metrics` |
| Kotak demo prediksi | `/api/predict` |

- Filter global (periode, versi, kategori) di Pinia store
- Status *loading* dan *empty state* untuk setiap grafik

**Definition of Done:** filter memengaruhi seluruh grafik secara konsisten; klik batang topik membuka ulasan terkait; tidak ada error di konsol.

---

## FASE 9 — Pengemasan & Dokumentasi
**Estimasi: 1 hari**

- `docker-compose up` menjalankan seluruh sistem
- README: cara menjalankan, arsitektur, ringkasan temuan
- Ekspor grafik resolusi tinggi untuk laporan
- **Sinkronkan Bab 1 dengan realitas**: nama kolom (Temuan 1), keputusan biner vs 3 kelas (Temuan 3), tautan sumber data
- Isi seluruh slot `[A-…]` dan `[T-…]` di dokumen storytelling

**Definition of Done:** repo bersih dapat di-*clone* dan dijalankan orang lain; tidak ada placeholder tersisa di naskah.

---

## 3.1 Ringkasan Jadwal

| Fase | Estimasi | Jalur kritis |
|------|----------|--------------|
| 0 · Fondasi | 0,5 hari | |
| 1 · EDA | 1 hari | |
| 2 · Preprocessing | 2 hari | ⚠️ Risiko kualitas tertinggi |
| 3 · Komparasi model | 2 hari | ⚠️ Inti RM1 |
| 4 · Tuning & evaluasi | 1,5 hari | ⚠️ Inti RM1 |
| 5 · Ekstraksi topik | 2 hari | ⚠️ Inti RM2 |
| 6 · Scoring & DB | 1 hari | |
| 7 · API | 2 hari | |
| 8 · Dashboard | 3 hari | |
| 9 · Pengemasan | 1 hari | |
| **Total** | **≈16 hari kerja** | |

Fase 2–5 adalah inti akademik yang menjawab rumusan masalah. Bila waktu menipis, **potong Fase 8** (sederhanakan dashboard) — **jangan potong Fase 4 atau 5**.

## 3.2 Registrasi Risiko

| Risiko | Dampak | Mitigasi |
|--------|--------|----------|
| Akurasi menyesatkan akibat asimetri panjang (Temuan 2) | **Tinggi** | Evaluasi ganda `full` vs `informative_ge5w`; laporkan baseline 72,3% |
| Kelas netral gagal diprediksi (Temuan 3) | Sedang | Model utama biner; 3 kelas sebagai eksperimen yang dilaporkan jujur |
| Stemming Sastrawi lambat | Sedang | Cache per kata unik, bukan per dokumen |
| 21,9% `Versi App` kosong | Sedang | Nyatakan eksplisit di setiap grafik versi; jangan diimputasi |
| Pelabelan topik subjektif | Sedang | Dokumentasikan aturan pemetaan; minta rekan memvalidasi silang sebagian sampel |
| Ruang lingkup melebar ke *deployment* | Sedang | Bab 1 sudah membatasinya — patuhi |

---

# LAMPIRAN — Prompt Eksekusi untuk Agent

Berikan per fase, jangan sekaligus:

```
Konteks: proyek analisis sentimen ulasan Gojek.
Dataset: data/raw/ulasan_com_gojek_app.csv — 100.000 baris, kolom:
Nama User, Ulasan, Rating, Tanggal, Likes, Versi App.
Arsitektur & keputusan desain: lihat tech-architecture-development-plan.md

Kerjakan FASE <N> saja. Patuhi:
- Seluruh parameter dibaca dari ml/config.yaml
- random_state=42 di semua tempat yang stokastik
- Jangan lanjut ke fase berikutnya
- Laporkan Definition of Done fase ini secara eksplisit
- Jangan mengarang angka; setiap metrik harus berasal dari kode yang dijalankan
```

---

## Catatan Penutup

Seluruh angka pada Bagian 0 terukur dari file Anda dan dapat langsung dikutip di laporan. Bagian 1 dan 3 adalah rekomendasi desain. Bagian 2 sengaja tidak memuat prediksi angka kinerja — tabel perbandingannya adalah kerangka yang Anda isi sendiri setelah Fase 3.

Satu hal yang perlu diklarifikasi sebelum Fase 1: file ini memiliki 100.000 baris dengan skema kolom berbahasa Indonesia, sementara halaman Kaggle yang Anda sitasi menyebut "100k+" dengan konvensi kolom *google-play-scraper*. Pastikan asal file ini sebelum menulis bagian metodologi — apakah unduhan langsung, hasil olahan Anda, atau *scraping* terpisah. Ketiganya sah, tetapi harus dinyatakan apa adanya.

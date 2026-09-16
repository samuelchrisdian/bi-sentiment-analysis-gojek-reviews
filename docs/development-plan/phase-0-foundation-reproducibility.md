# FASE 0 — Fondasi & Reprodusibilitas

**Estimasi:** 0,5 hari
**Prasyarat:** ✅ sudah terpenuhi — Docker Compose v5.5.0, Python 3.12.3, Node 24.19.0 (lihat H-2)
**Output utama:** kerangka kerja yang bisa di-*clone* dan dijalankan orang lain

---

## 0. Kondisi Awal (sudah ada — JANGAN diulang)

Repositori **sudah diinisialisasi**. Kondisi saat fase ini dimulai:

```
bi-sentiment-analysis-gojek-reviews/        ← root repo, .git sudah ada
├── .git/                                   ← sudah ada, belum ada commit
├── data/raw/ulasan_com.gojek.app.csv       ← sudah ada (10,7 MB)
├── docs/development-plan/                  ← sudah ada (file fase 0–10)
└── tech-architecture-development-plan.md   ← sudah ada
```

Konsekuensinya:

- **Jangan jalankan `git init`** — repositori sudah ada.
- **Jangan buat folder root baru bernama `gojek-sentiment/`.** Root proyek
  adalah direktori ini; seluruh path di dokumen fase relatif terhadapnya.
- **Jangan pindahkan atau ganti nama file CSV.** Nama aktualnya
  `ulasan_com.gojek.app.csv` (memakai titik, bukan garis bawah) dan sudah
  dipakai sebagai nilai `paths.raw_csv` di config.
- ⚠️ **Belum ada `.gitignore`, dan `data/` saat ini berstatus untracked.**
  Commit pertama tanpa `.gitignore` akan memasukkan CSV 10,7 MB ke riwayat git.
  Karena itu T-0.1 dikerjakan **sebelum** `git add` apa pun.

Yang belum ada dan menjadi pekerjaan fase ini: `ml/`, `api/`, `web/`,
`.gitignore`, `.env.example`, `docker-compose.yml`, dan seluruh file konfigurasi.

---

## 1. Objective

Melengkapi fondasi teknis sebelum satu baris kode analisis ditulis: struktur
direktori kerja, penguncian versi dependensi, satu sumber kebenaran konfigurasi,
dan database yang siap menerima data.

Fase ini murni *setup*. Nilainya baru terasa di Fase 9 ketika penguji meminta
sistem dijalankan ulang dari nol — dan di Fase 3–4 ketika hasil model harus
bisa direproduksi persis.

Target utama: **tidak ada satu pun angka konfigurasi yang tersebar di dalam
script.** Semua masuk `ml/config.yaml`.

---

## 2. Technical Tasks

### T-0.1 — `.gitignore` (KERJAKAN PERTAMA, sebelum `git add`)

Kecualikan data mentah dan artefak biner — ukurannya besar, dan data mentah
punya isu provenans yang belum diklarifikasi:

```gitignore
# Data & artefak
data/raw/*
!data/raw/.gitkeep
data/processed/*
!data/processed/.gitkeep
ml/artifacts/*
!ml/artifacts/.gitkeep

# Python
__pycache__/
*.py[cod]
.venv/
venv/
.ipynb_checkpoints/

# Node
node_modules/
web/dist/

# Env & OS
.env
.DS_Store
```

Verifikasi segera setelah dibuat:

```bash
git status --short          # data/raw/*.csv TIDAK boleh muncul
git check-ignore -v data/raw/ulasan_com.gojek.app.csv
```

### T-0.2 — Lengkapi struktur direktori

Direktori yang perlu dibuat (root sudah ada, jangan buat ulang):

```bash
mkdir -p data/processed \
         ml/src ml/notebooks ml/artifacts ml/sql \
         api web \
         docs/figures docs/tables
touch data/raw/.gitkeep data/processed/.gitkeep ml/artifacts/.gitkeep
```

Struktur akhir yang diharapkan:

```
bi-sentiment-analysis-gojek-reviews/
├── docker-compose.yml
├── .gitignore
├── .env.example
├── README.md
├── tech-architecture-development-plan.md   # sudah ada
├── data/
│   ├── raw/ulasan_com.gojek.app.csv        # sudah ada
│   └── processed/
├── ml/{config.yaml,requirements.txt,src/,notebooks/,artifacts/,sql/}
├── api/{main.py,requirements.txt}
├── web/
└── docs/{development-plan/,figures/,tables/}   # development-plan sudah ada
```

### T-0.3 — `ml/requirements.txt` dengan versi terkunci

Jangan gunakan `>=`. Kunci ke versi eksak agar hasil Fase 3–4 reprodusibel.

```txt
pandas==2.2.2
numpy==1.26.4
scikit-learn==1.5.1
scipy==1.13.1
Sastrawi==1.0.1
pyyaml==6.0.2
joblib==1.4.2
pyarrow==17.0.0
matplotlib==3.9.2
seaborn==0.13.2
gensim==4.3.3
psycopg2-binary==2.9.9
SQLAlchemy==2.0.32
tqdm==4.66.5
jupyter==1.1.1
```

`api/requirements.txt`:

```txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
SQLAlchemy==2.0.32
psycopg2-binary==2.9.9
pydantic==2.9.2
pydantic-settings==2.5.2
python-dotenv==1.0.1
joblib==1.4.2
scikit-learn==1.5.1   # WAJIB sama persis dengan ml/requirements.txt
```

> ⚠️ Versi `scikit-learn` di `api/` **harus identik** dengan di `ml/`.
> Artefak `.joblib` yang di-*unpickle* oleh versi berbeda bisa gagal atau,
> lebih berbahaya, memberi prediksi berbeda diam-diam.

> ⚠️ `gensim==4.3.3` menuntut `numpy<2`. Itulah alasan `numpy` dikunci di
> `1.26.4`. Jangan naikkan salah satunya tanpa menguji keduanya.

> ✅ **Kompatibilitas Python 3.12 sudah diverifikasi** (H-2): wheel
> `gensim-4.3.3-cp312` dan `numpy-1.26.4-cp312` tersedia. Seluruh versi di
> daftar ini dipakai apa adanya — tidak ada yang perlu dinaikkan karena
> environment memakai 3.12.3, bukan 3.11.

### T-0.4 — `ml/config.yaml` (sumber kebenaran tunggal)

```yaml
seed: 42

paths:
  raw_csv: data/raw/ulasan_com.gojek.app.csv   # nama file memakai TITIK
  processed_dir: data/processed
  clean_parquet: data/processed/reviews_clean.parquet
  artifacts_dir: ml/artifacts

schema:
  expected_columns: ["Nama User", "Ulasan", "Rating", "Tanggal", "Likes", "Versi App"]
  expected_rows: 100000
  date_format: null          # biarkan pandas infer, lalu validasi rentang
  valid_date_range: ["2024-05-21", "2025-12-31"]

labeling:
  scheme: binary             # binary | three_class
  negative_ratings: [1, 2]
  neutral_ratings: [3]
  positive_ratings: [4, 5]
  drop_neutral_in_binary: true

preprocessing:
  lowercase: true
  remove_url: true
  remove_emoji: true
  remove_digits: true
  remove_punctuation: true
  normalize_slang: true
  remove_stopwords: true
  stemming: true
  stem_cache: true           # cache per kata unik, bukan per dokumen
  dedup_training_text: true  # hanya pada training set

features:
  tfidf:
    ngram_range: [1, 2]
    min_df: 3
    max_features: 30000
    sublinear_tf: true

split:
  test_size: 0.2
  stratify: true

evaluation:
  informative_min_words: 5
  primary_metric: f1_macro
  majority_baseline: 0.723
  eval_sets: ["full", "informative_ge5w"]

topics:
  lda_n_topics_range: [5, 12]
  top_n_terms: 20
  categories:
    - Pembayaran
    - Mitra Driver
    - Performa Aplikasi
    - Tarif & Promo
    - Layanan Pelanggan
    - Akurasi Lokasi

versions:
  min_reviews_per_version: 100
  aggregate_to_minor: true

temporal:
  exclude_partial_first_month: true
  partial_month: "2024-05"

database:
  dsn_env: DATABASE_URL
```

### T-0.5 — `ml/src/config.py` (loader)

Satu fungsi, dipakai semua script. Tidak ada script yang membaca YAML sendiri.

```python
# ml/src/config.py
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]   # -> root repo

def load_config(path: str | Path = None) -> dict:
    path = Path(path) if path else ROOT / "ml" / "config.yaml"
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["_root"] = ROOT
    return cfg

def resolve(cfg: dict, key_path: str) -> Path:
    """resolve(cfg, 'paths.raw_csv') -> Path absolut."""
    node = cfg
    for k in key_path.split("."):
        node = node[k]
    return cfg["_root"] / node
```

Tambahkan `ml/src/__init__.py` dan `ml/__init__.py` (file kosong) agar
`python -m ml.src.<modul>` bekerja dari root repo.

### T-0.6 — `docker-compose.yml` (mulai dengan service `db` saja)

Service `api` dan `web` ditambahkan pada Fase 7 dan 8.

```yaml
services:
  db:
    image: postgres:16-alpine
    container_name: gojek_db
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-gojek}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-gojek}
      POSTGRES_DB: ${POSTGRES_DB:-gojek_sentiment}
    ports:
      - "5433:5432"          # 5433 agar tidak bentrok Postgres lokal
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./ml/sql:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-gojek}"]
      interval: 5s
      timeout: 5s
      retries: 10

volumes:
  pgdata:
```

`.env.example`:

```env
POSTGRES_USER=gojek
POSTGRES_PASSWORD=gojek
POSTGRES_DB=gojek_sentiment
DATABASE_URL=postgresql+psycopg2://gojek:gojek@localhost:5433/gojek_sentiment
```

### T-0.7 — `ml/sql/001_schema.sql`

Salin skema DDL dari Bagian 1.5 dokumen induk (tabel `reviews`,
`review_scores`, `topics`, `review_topics`, `model_metrics` + 4 index).
File ini dipasang sebagai *init script* container sehingga skema terbentuk
otomatis saat `docker compose up db` pertama kali.

> Materialized view `agg_monthly` dan `agg_version` **belum** dibuat di sini —
> pembuatannya milik Fase 6, setelah data masuk.

### T-0.8 — Verifikasi environment

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r ml/requirements.txt
cp .env.example .env
docker compose up -d db
docker compose ps        # status harus "healthy"
```

### T-0.9 — Commit pertama

Repositori belum punya satu commit pun. Buat commit awal **setelah**
`.gitignore` terverifikasi:

```bash
git add .
git status            # periksa ulang: tidak ada file CSV di daftar
git commit -m "Fase 0: fondasi proyek, konfigurasi, dan skema database"
git tag phase-0-done
```

---

## 3. Deliverables / Output

| Artefak | Lokasi | Keterangan |
|---------|--------|------------|
| `.gitignore` | root | `data/raw/`, `artifacts/`, `.env` dikecualikan |
| Struktur direktori | root | `ml/`, `api/`, `web/`, `data/processed/`, `docs/figures/`, `docs/tables/` |
| `ml/requirements.txt` | `ml/` | Versi terkunci eksak (`==`) |
| `api/requirements.txt` | `api/` | sklearn versi identik dengan ml/ |
| `ml/config.yaml` | `ml/` | Sumber kebenaran tunggal seluruh parameter |
| `ml/src/config.py` | `ml/src/` | Loader config, dipakai semua script |
| `docker-compose.yml` | root | Service `db` (PostgreSQL 16) |
| `.env.example` | root | Template kredensial |
| `ml/sql/001_schema.sql` | `ml/sql/` | DDL 5 tabel + 4 index |
| Commit awal | git | Tag `phase-0-done` |

---

## 4. Definition of Done

- [ ] `git check-ignore -v data/raw/ulasan_com.gojek.app.csv` mengonfirmasi file terabaikan; `git status --short` tidak menampilkan file CSV.
- [ ] `docker compose up -d db` berhasil; `docker compose ps` menunjukkan status `healthy`.
- [ ] `psql $DATABASE_URL -c "\dt"` menampilkan 5 tabel: `reviews`, `review_scores`, `topics`, `review_topics`, `model_metrics`.
- [ ] `python -c "import sklearn, pandas, yaml, joblib, gensim; from Sastrawi.Stemmer.StemmerFactory import StemmerFactory; print('OK')"` tidak error.
- [ ] `python -c "from ml.src.config import load_config, resolve; c=load_config(); print(c['seed'], resolve(c,'paths.raw_csv').exists())"` mencetak `42 True` — membuktikan config terbaca **dan** path CSV benar.
- [ ] Commit pertama dibuat; `git log --oneline` menampilkan satu commit; ukuran `.git` < 5 MB.
- [ ] Commit ditag `phase-0-done`.

---

## 5. Risiko & Catatan

| Risiko | Mitigasi |
|--------|----------|
| **CSV 10,7 MB masuk riwayat git** karena commit dilakukan sebelum `.gitignore` | T-0.1 dikerjakan pertama; DoD memverifikasi dengan `git check-ignore`. Bila terlanjur, perbaiki sekarang (`git rm --cached`) selagi riwayat masih kosong |
| Nama file CSV salah tulis (`_` vs `.`) | Nama aktual: `ulasan_com.gojek.app.csv`. DoD memverifikasi `resolve(...).exists()` |
| Port 5432 bentrok dengan Postgres lokal | Sudah dipetakan ke `5433` di host |
| Versi sklearn berbeda antara `ml/` dan `api/` menyebabkan unpickle gagal di Fase 7 | Kunci versi identik sejak sekarang; catat di README |
| `gensim` menolak numpy 2.x | `numpy==1.26.4` sudah dikunci |

**Catatan jumlah baris:** `wc -l` pada file CSV mengembalikan 100.002 baris,
bukan 100.001 (header + 100.000). Selisih ini normal untuk CSV dengan teks
ber-*newline* di dalam tanda kutip. **Jumlah baris yang sah hanya yang dihitung
pandas** — inilah yang divalidasi di Fase 1. Jangan pakai `wc -l` untuk
memverifikasi jumlah data.

**Tugas manusia yang berjalan paralel:** klarifikasi provenans file CSV —
lihat `00-human-prep-checklist.md` butir H-1. Jawabannya dibutuhkan di Fase 1
(`data_contract.md`) dan Fase 9 (bab metodologi), tetapi tidak memblokir Fase 0.

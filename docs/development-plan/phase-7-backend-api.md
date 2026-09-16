# FASE 7 — Backend API (FastAPI)

**Estimasi:** 2 hari
**Prasyarat:** Fase 6 selesai (DB terisi, materialized view siap)
**Output utama:** 7 endpoint berjalan + Swagger dapat diekspor

---

## 1. Objective

Menyediakan lapisan penyajian data antara PostgreSQL dan dashboard Vue.

Prinsip yang menentukan desainnya: **enam dari tujuh endpoint hanya membaca
agregat dari database.** Hanya `/api/predict` yang memuat model, dan perannya
adalah demo kapabilitas — user mengetik ulasan, mendapat prediksi — bukan
sumber data dashboard.

FastAPI dipilih (bukan Laravel) karena alasan operasional, bukan preferensi:
model, vectorizer, dan pipeline preprocessing hidup di Python. Menaruh API di
Laravel memaksa dua runtime dijembatani lewat *subprocess* atau antrian —
kompleksitas tambahan tanpa manfaat untuk lingkup ini.

---

## 2. Technical Tasks

### T-7.1 — Struktur modul

```
api/
├── main.py           # app, lifespan, CORS, router
├── db.py             # engine, SessionLocal, get_db dependency
├── models.py         # SQLAlchemy ORM
├── schemas.py        # Pydantic response models
├── crud.py           # query — seluruh SQL ada di sini
├── ml_service.py     # pemuatan artefak + preprocessing + predict
├── config.py         # pydantic-settings, baca .env
└── requirements.txt
```

Aturan: **tidak ada SQL di `main.py`**, dan **tidak ada logika ML di `crud.py`**.
Pemisahan ini membuat endpoint mudah diuji dan mudah dijelaskan saat presentasi.

### T-7.2 — Pemuatan model sekali saat startup (`lifespan`)

Jangan memuat artefak per request — itu menambah ratusan milidetik ke setiap
panggilan dan mengalahkan tujuan arsitektur batch.

```python
from contextlib import asynccontextmanager

ml = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    ml["vectorizer"] = joblib.load(ART / "vectorizer.joblib")
    ml["model"]      = joblib.load(ART / "model_final.joblib")
    ml["manifest"]   = json.loads((ART / "MANIFEST.json").read_text())
    yield
    ml.clear()

app = FastAPI(
    title="Gojek Sentiment API",
    description="API analisis sentimen & topik keluhan ulasan Gojek",
    version="1.0.0",
    lifespan=lifespan,
)
```

`ml_service.py` **wajib memakai fungsi preprocessing yang sama persis dengan
Fase 2** — impor dari `ml.src.preprocess`, jangan tulis ulang. Pipeline yang
berbeda antara pelatihan dan inferensi adalah salah satu bug paling sering dan
paling sulit terdeteksi di sistem ML.

### T-7.3 — Implementasi 7 endpoint

| # | Method | Endpoint | Query params | Mengembalikan |
|---|--------|----------|--------------|---------------|
| 1 | GET | `/api/kpi` | `from`, `to` | Total ulasan, % negatif, rata-rata rating, jumlah versi |
| 2 | GET | `/api/trend` | `from`, `to`, `granularity` | Deret waktu proporsi negatif + volume |
| 3 | GET | `/api/versions` | `min_reviews` (default 100) | Proporsi sentimen per versi |
| 4 | GET | `/api/topics` | `limit`, `from`, `to` | Peringkat topik + frekuensi + total likes |
| 5 | GET | `/api/topics/{id}/reviews` | `sort_by=likes`, `page`, `page_size` | Ulasan mentah per topik (drill-down) |
| 6 | GET | `/api/model/metrics` | — | Perbandingan seluruh model dari `model_metrics` |
| 7 | POST | `/api/predict` | body `{"text": "..."}` | Prediksi + probabilitas (demo) |

Ketentuan per endpoint:

**`/api/kpi`** — sertakan `baseline_negatif` dan catatan cakupan versi
(`versi_null_pct: 21.9`) dalam respons, agar frontend tidak perlu meng-*hardcode*
angka-angka itu.

**`/api/trend`** — `granularity ∈ {month, week}`; default `month`. Sertakan flag
`periode_parsial` per titik data (Mei 2024) agar frontend bisa memberi anotasi.

**`/api/versions`** — `min_reviews` default dari config (100). Respons wajib
memuat metadata:

```json
{
  "min_reviews_threshold": 100,
  "versions_included": 66,
  "coverage_pct": 96.4,
  "null_version_pct": 21.9,
  "data": []
}
```

Ini membuat catatan metodologis ikut mengalir ke UI secara otomatis, bukan
bergantung pada developer frontend yang ingat menuliskannya.

**`/api/topics/{id}/reviews`** — wajib berpaginasi (`page_size` default 20,
maksimum 100). Kembalikan **teks ulasan asli**, bukan `ulasan_clean` — teks
ter-*stem* tidak terbaca oleh manusia.

**`/api/model/metrics`** — kembalikan seluruh baris termasuk
`majority_baseline`, dikelompokkan per `eval_set`, agar frontend bisa
menampilkan perbandingan `full` vs `informative_ge5w` berdampingan. Ini
adalah temuan metodologis utama yang harus terlihat di dashboard.

**`/api/predict`** — validasi input: panjang 1–1000 karakter, tidak kosong
setelah preprocessing. Respons:

```json
{
  "text": "aplikasi error terus gabisa bayar",
  "text_preprocessed": "aplikasi error tidak bisa bayar",
  "prediction": 0,
  "label": "Negatif",
  "confidence": 0.94,
  "model_name": "linear_svc_tuned",
  "note": "Endpoint demo. Data dashboard berasal dari pre-scoring batch."
}
```

Kembalikan `text_preprocessed` — ini membuat pipeline transparan dan sangat
membantu saat demo di depan penguji.

### T-7.4 — Skema Pydantic untuk semua respons

Setiap endpoint punya `response_model`. Ini memberi tiga hal sekaligus:
validasi otomatis, dokumentasi OpenAPI yang akurat, dan kontrak yang jelas
untuk frontend.

```python
class KpiResponse(BaseModel):
    total_ulasan: int
    persen_negatif: float = Field(..., ge=0, le=100)
    rata_rating: float = Field(..., ge=1, le=5)
    jumlah_versi: int
    periode: PeriodeInfo
    catatan: list[str]
```

### T-7.5 — CORS untuk origin dev Vue

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

Jangan gunakan `allow_origins=["*"]` — meski ini proyek akademik, kebiasaan
yang benar mudah dibentuk sejak awal dan tidak menambah pekerjaan.

### T-7.6 — Penanganan error

- 404 untuk `topic_id` yang tidak ada.
- 422 otomatis dari Pydantic untuk parameter tidak valid.
- 400 untuk teks kosong di `/predict`.
- 503 bila artefak model gagal dimuat saat startup — gagal cepat dan jelas,
  jangan biarkan API menyala dengan `/predict` yang rusak diam-diam.

### T-7.7 — Uji manual via Swagger + ekspor

```bash
uvicorn api.main:app --reload --port 8000
# buka http://localhost:8000/docs
curl http://localhost:8000/openapi.json -o docs/openapi.json
```

Uji setiap endpoint langsung dari Swagger UI, catat waktu respons. Ekspor
`openapi.json` untuk dilampirkan di laporan.

### T-7.8 — Tambahkan service `api` ke docker-compose

```yaml
  api:
    build: ./api
    depends_on:
      db: { condition: service_healthy }
    environment:
      DATABASE_URL: postgresql+psycopg2://gojek:gojek@db:5432/gojek_sentiment
      ARTIFACTS_DIR: /app/artifacts
    volumes:
      - ./ml/artifacts:/app/artifacts:ro
    ports:
      - "8000:8000"
```

Artefak di-*mount* read-only, tidak disalin ke image — ukurannya besar dan
image tetap ramping.

---

## 3. Deliverables / Output

| Artefak | Lokasi | Keterangan |
|---------|--------|------------|
| `main.py`, `db.py`, `models.py`, `schemas.py`, `crud.py`, `ml_service.py` | `api/` | Modul terpisah sesuai tanggung jawab |
| `Dockerfile` | `api/` | Base `python:3.12-slim` (samakan dengan runtime pembuat artefak) |
| Service `api` | `docker-compose.yml` | Depends on `db` healthy |
| `docs/openapi.json` | `docs/` | Ekspor Swagger — lampiran laporan |
| `docs/api_test_log.md` | `docs/` | Hasil uji manual 7 endpoint + waktu respons |
| URL endpoint aktif | `http://localhost:8000` | Swagger di `/docs` |

---

## 4. Definition of Done

- [ ] `uvicorn api.main:app` menyala tanpa error; artefak termuat di `lifespan`, bukan per request (diverifikasi dari log startup).
- [ ] **Ketujuh endpoint mengembalikan HTTP 200** dengan skema yang valid terhadap `response_model`-nya.
- [ ] `/api/kpi` mengembalikan `total_ulasan = 100000` untuk rentang penuh.
- [ ] `/api/versions` mengembalikan 66 versi dengan metadata ambang & cakupan null.
- [ ] `/api/model/metrics` mengembalikan seluruh model termasuk `majority_baseline`, terkelompok per `eval_set`.
- [ ] `/api/predict` bekerja untuk 5 kalimat uji manual (3 negatif jelas, 2 positif jelas) dan mengembalikan `text_preprocessed`.
- [ ] Pipeline preprocessing di `/predict` **diimpor dari `ml.src.preprocess`**, bukan diimplementasikan ulang (verifikasi kode).
- [ ] Endpoint agregat merespons **< 200ms** (diukur, dicatat di `api_test_log.md`).
- [ ] `/api/topics/{id}/reviews` berpaginasi dan mengembalikan teks ulasan **asli**.
- [ ] CORS memperbolehkan `http://localhost:5173`; diuji dari browser.
- [ ] `docs/openapi.json` terekspor dan terbaca.
- [ ] `docker compose up api` berjalan dan terhubung ke `db`.
- [ ] Commit ditag `phase-7-done`.

---

## 5. Risiko & Catatan

| Risiko | Dampak | Mitigasi |
|--------|--------|----------|
| Pipeline preprocessing `/predict` berbeda dengan saat training | **Tinggi** — prediksi demo salah di depan penguji | Impor modul yang sama; uji dengan 5 kalimat yang hasilnya sudah diketahui |
| Artefak `.joblib` gagal di-unpickle karena versi sklearn | Sedang | Versi dikunci identik sejak Fase 0; uji di container, bukan hanya di venv lokal |
| Model dimuat per request | Sedang | `lifespan` event; verifikasi via log startup |
| Container `api` start sebelum `db` siap | Rendah | `depends_on: condition: service_healthy` |
| `LinearSVC` tanpa `predict_proba` | Rendah | Gunakan `model_calibrated.joblib` dari Fase 4; bila tidak ada, kembalikan `confidence: null` dan tangani di UI |

**Catatan lingkup:** jangan menambahkan autentikasi, *rate limiting*, atau
*caching* Redis. Bab 1 sudah membatasi lingkup di luar *deployment* produksi —
patuhi. Setiap tambahan di sini adalah waktu yang diambil dari Fase 8.

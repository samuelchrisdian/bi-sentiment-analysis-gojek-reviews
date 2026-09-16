# FASE 6 — Scoring & Muat ke Database

**Estimasi:** 1 hari
**Prasyarat:** Fase 4 (artefak model final) **dan** Fase 5 (tabel topik) selesai
**Output utama:** PostgreSQL terisi penuh + materialized view siap query

---

## 1. Objective

Menjembatani lapisan offline (Python) dan lapisan penyajian (API + dashboard).

Keputusan arsitektur terpenting di proyek ini diwujudkan di sini:
**dashboard tidak memanggil model saat request.** Seluruh 100.000 baris
diprediksi sekali di sini, hasilnya disimpan, dan dashboard hanya membaca
agregat. Konsekuensinya: dashboard merespons di bawah 100ms, backend tetap
ringan, dan agregasi dikerjakan PostgreSQL — bukan Python.

---

## 2. Technical Tasks

### T-6.1 — `ml/src/score.py` — prediksi 100k baris

Perhatikan: yang diprediksi adalah **seluruh 100.000 baris**, termasuk yang
rating 3 (yang dikeluarkan dari pelatihan). Dashboard perlu menampilkan prediksi
untuk semua ulasan, dan ulasan bintang 3 justru menarik: ke arah mana model
mengklasifikasikannya?

```python
vec   = joblib.load(art / "vectorizer.joblib")
model = joblib.load(art / "model_final.joblib")

df = pd.read_parquet(cfg_path("clean_parquet"))   # 100.000 baris
X  = vec.transform(df["ulasan_clean"])

pred = model.predict(X)
proba = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else None
```

Jalankan scoring untuk **minimal dua model** (`complement_nb` dan
`linear_svc`), karena `review_scores` ber-PK `(review_id, model_name)` dan
dashboard perbandingan model akan memanfaatkannya.

Verifikasi sanity sebelum menulis ke DB:

```python
# Proporsi prediksi negatif harus wajar (~25-30%), bukan 0% atau 90%
print(pd.Series(pred).value_counts(normalize=True))
# Kesesuaian dengan label aktual pada baris berlabel
mask = df["sentimen_aktual"].notna()
print("Agreement:", (pred[mask] == df.loc[mask, "sentimen_aktual"]).mean())
```

Angka *agreement* ini akan lebih tinggi dari akurasi test set (karena mencakup
data latih) — itu wajar dan bukan metrik yang dilaporkan. Fungsinya murni
sebagai deteksi bug: bila nilainya rendah, ada yang salah pada pemuatan artefak.

### T-6.2 — `ml/src/load_to_db.py` — muat tabel dasar

Urutan pemuatan (wajib, karena ada *foreign key*):

```
1. reviews        (100.000 baris)
2. topics         (dari Fase 5)
3. review_topics  (FK ke reviews + topics)
4. review_scores  (FK ke reviews)
5. model_metrics  (sudah sebagian diisi Fase 3–4; pastikan lengkap)
```

Gunakan `COPY` PostgreSQL, bukan `to_sql` baris per baris:

```python
import io
buf = io.StringIO()
df_reviews.to_csv(buf, index=False, header=False, sep="\t", na_rep="\\N")
buf.seek(0)
with engine.raw_connection().cursor() as cur:
    cur.copy_expert(
        "COPY reviews (id, nama_user, ulasan, ulasan_clean, rating, tanggal, "
        "likes, versi_app, versi_minor, word_count, sentimen_aktual) "
        "FROM STDIN WITH (FORMAT csv, DELIMITER E'\\t', NULL '\\\\N')", buf)
```

`to_sql` dengan 100k baris memakan menit; `COPY` selesai dalam detik.

Buat script **idempoten** — `TRUNCATE ... CASCADE` di awal, agar bisa dijalankan
ulang tanpa duplikasi saat ada perbaikan.

### T-6.3 — Materialized view `agg_monthly`

```sql
CREATE MATERIALIZED VIEW agg_monthly AS
SELECT
    date_trunc('month', r.tanggal)::date        AS bulan,
    count(*)                                     AS total_ulasan,
    count(*) FILTER (WHERE rs.pred_label = 0)    AS jumlah_negatif,
    round(100.0 * count(*) FILTER (WHERE rs.pred_label = 0)
          / NULLIF(count(*), 0), 2)              AS persen_negatif,
    round(avg(r.rating)::numeric, 2)             AS rata_rating,
    sum(r.likes)                                 AS total_likes,
    bool_or(date_trunc('month', r.tanggal)::date = DATE '2024-05-01')
                                                 AS periode_parsial
FROM reviews r
JOIN review_scores rs
  ON rs.review_id = r.id AND rs.model_name = 'linear_svc'
GROUP BY 1
ORDER BY 1;

CREATE UNIQUE INDEX idx_agg_monthly_bulan ON agg_monthly (bulan);
```

Kolom `periode_parsial` menandai Mei 2024 (Temuan 6) supaya frontend bisa
memberi anotasi visual, bukan diam-diam menampilkannya seolah setara.

### T-6.4 — Materialized view `agg_version` (hormati ambang ≥100)

```sql
CREATE MATERIALIZED VIEW agg_version AS
WITH per_minor AS (
    SELECT
        r.versi_minor,
        count(*)                                  AS total_ulasan,
        count(*) FILTER (WHERE rs.pred_label = 0) AS jumlah_negatif,
        round(avg(r.rating)::numeric, 2)          AS rata_rating,
        min(r.tanggal)                            AS pertama_muncul
    FROM reviews r
    JOIN review_scores rs
      ON rs.review_id = r.id AND rs.model_name = 'linear_svc'
    WHERE r.versi_minor IS NOT NULL
    GROUP BY r.versi_minor
)
SELECT *,
       round(100.0 * jumlah_negatif / NULLIF(total_ulasan, 0), 2) AS persen_negatif
FROM per_minor
WHERE total_ulasan >= 100          -- ambang dari config; 66 versi, cakupan 96,4%
ORDER BY pertama_muncul;

CREATE UNIQUE INDEX idx_agg_version_minor ON agg_version (versi_minor);
```

> ⚠️ Ambang ≥100 dan fakta bahwa **21,9% baris tidak punya `Versi App`** wajib
> dicantumkan di keterangan setiap grafik versi. Jangan diimputasi, jangan
> dibiarkan tanpa penjelasan.

### T-6.5 — View `agg_topic` (pendukung `/api/topics`)

```sql
CREATE MATERIALIZED VIEW agg_topic AS
SELECT
    t.id, t.kategori,
    count(DISTINCT rt.review_id) AS jumlah_ulasan,
    sum(r.likes)                 AS total_likes,
    round(avg(r.rating)::numeric, 2) AS rata_rating
FROM topics t
JOIN review_topics rt ON rt.topic_id = t.id
JOIN reviews r        ON r.id = rt.review_id
GROUP BY t.id, t.kategori
ORDER BY jumlah_ulasan DESC;
```

### T-6.6 — Refresh & verifikasi kinerja

```sql
REFRESH MATERIALIZED VIEW agg_monthly;
REFRESH MATERIALIZED VIEW agg_version;
REFRESH MATERIALIZED VIEW agg_topic;
```

Karena data statis, `REFRESH` cukup dijalankan sekali setelah pemuatan. Tidak
perlu penjadwalan.

Ukur waktu query dengan `EXPLAIN ANALYZE` untuk kelima query yang akan dipakai
endpoint API. Target: **< 200ms** untuk setiap query agregat.

### T-6.7 — Script orkestrasi `ml/run_pipeline.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
python -m ml.src.ingest
python -m ml.src.preprocess
python -m ml.src.train
python -m ml.src.topics
python -m ml.src.score
python -m ml.src.load_to_db
psql "$DATABASE_URL" -f ml/sql/002_matviews.sql
echo "Pipeline selesai."
```

Ini yang nanti dirujuk README di Fase 9 sebagai "satu perintah untuk
membangun ulang seluruh data".

---

## 3. Deliverables / Output

| Artefak | Lokasi | Keterangan |
|---------|--------|------------|
| `score.py` | `ml/src/` | Prediksi 100k baris × ≥2 model |
| `load_to_db.py` | `ml/src/` | Pemuatan idempoten via `COPY` |
| `002_matviews.sql` | `ml/sql/` | DDL `agg_monthly`, `agg_version`, `agg_topic` |
| `run_pipeline.sh` | `ml/` | Orkestrasi end-to-end |
| DB terisi | PostgreSQL | 100.000 `reviews`, ≥200.000 `review_scores` |
| `docs/db_performance.md` | `docs/` | Hasil `EXPLAIN ANALYZE` 5 query utama |

---

## 4. Definition of Done

- [ ] `SELECT count(*) FROM reviews` → **100000**.
- [ ] `SELECT count(*) FROM review_scores` → 200000 (2 model × 100k), atau kelipatan sesuai jumlah model yang di-*score*.
- [ ] `SELECT count(*) FROM review_topics` > 0; cakupan topik pada ulasan negatif tercatat.
- [ ] `SELECT count(*) FROM model_metrics` ≥ 10 (mencakup baseline, model default, model tuned).
- [ ] `SELECT count(*) FROM agg_version` → **66** (ambang ≥100 ulasan).
- [ ] `SELECT count(*) FROM agg_monthly` → **20** (bulan penuh, Mei 2024 ditandai `periode_parsial = true`).
- [ ] **Seluruh query agregat selesai < 200ms** — dibuktikan dengan `EXPLAIN ANALYZE`, bukan perkiraan.
- [ ] Tidak ada FK violation; `load_to_db.py` bisa dijalankan dua kali berturut-turut tanpa duplikasi.
- [ ] Sanity check prediksi: proporsi prediksi negatif berada di rentang wajar (±25–32%).
- [ ] `run_pipeline.sh` berjalan end-to-end dari database kosong.
- [ ] Commit ditag `phase-6-done`.

---

## 5. Risiko & Catatan

| Risiko | Dampak | Mitigasi |
|--------|--------|----------|
| `to_sql` lambat untuk 100k baris | Sedang | Gunakan `COPY` (T-6.2) |
| Ketidaksesuaian `id` antara parquet dan DB | Sedang | `id` ditetapkan di Fase 2 dan dibawa apa adanya; jangan biarkan DB men-*generate* ulang |
| Query agregat >200ms | Sedang | Index sudah ada dari Fase 0; materialized view memindahkan beban ke waktu *build* |
| `REFRESH` gagal karena ada view yang bergantung | Rendah | Refresh sesuai urutan dependensi |
| Timezone `tanggal` bergeser saat masuk DB | Sedang | Kolom bertipe `TIMESTAMPTZ`; pastikan parquet UTC-aware; verifikasi min/max tanggal setelah muat |

**Catatan:** setelah fase ini, seluruh lapisan Python selesai. Fase 7–9 tidak
lagi menyentuh model atau data mentah — cukup membaca database.

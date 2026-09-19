-- Materialized view tambahan untuk Fase 7 (T-7.3) — dijalankan setelah
-- 002_matviews.sql dan setelah review_topics terisi (Fase 5 T-5.7).
--
-- Alasan berkas ini ada. `agg_topic` (Fase 6) dikelompokkan per `topics.id`,
-- yaitu pasangan (kategori, keyword): 146 baris untuk 9 kategori bisnis.
-- Peringkat topik di dashboard adalah peringkat KATEGORI — "Ketersediaan &
-- Respons Mitra Driver", bukan kata kunci "driver". Mengagregasi ulang ke
-- kategori saat request memerlukan join reviews x review_scores x
-- review_topics; diukur 145 ms, terlalu dekat dengan anggaran 200 ms untuk
-- query yang hasilnya tidak pernah berubah antar request. Maka dipraagregasi
-- di sini, sejalan dengan keputusan arsitektur Fase 6 §1.

-- Indeks penolong: PK review_topics adalah (review_id, topic_id), sehingga
-- penelusuran ARAH SEBALIKNYA (topic_id -> review) tidak terindeks.
CREATE INDEX IF NOT EXISTS idx_review_topics_topic ON review_topics (topic_id);
CREATE INDEX IF NOT EXISTS idx_topics_kategori     ON topics (kategori);

DROP MATERIALIZED VIEW IF EXISTS agg_kategori;
DROP MATERIALIZED VIEW IF EXISTS review_kategori;
DROP MATERIALIZED VIEW IF EXISTS agg_weekly;

-- ---------------------------------------------------------------------------
-- review_kategori — satu baris per (kategori, ulasan), bukan per keyword.
--
-- Satu ulasan dapat memicu beberapa kata kunci dari kategori yang sama;
-- DISTINCT di sini yang membuat COUNT per kategori tidak menghitung ganda
-- (alasan yang sama dengan `pemicu` di ml/src/topic_assign.py).
-- `id` kategori = min(topics.id) miliknya: stabil selama isi tabel `topics`
-- tidak diubah, dan tidak menuntut tabel kategori baru.
-- ---------------------------------------------------------------------------
CREATE MATERIALIZED VIEW review_kategori AS
WITH kat AS (
    SELECT min(id) AS kategori_id, kategori FROM topics GROUP BY kategori
),
pasangan AS (
    SELECT DISTINCT k.kategori_id, k.kategori, rt.review_id
    FROM review_topics rt
    JOIN topics t ON t.id = rt.topic_id
    JOIN kat    k ON k.kategori = t.kategori
)
SELECT p.kategori_id, p.kategori, p.review_id,
       -- Kolom di bawah DIDUPLIKASI dari reviews/review_scores dengan sengaja.
       -- /api/topics berfilter tanggal semula menjoin reviews x review_scores
       -- saat request: 95 ms, separuh anggaran 200 ms untuk sesuatu yang tidak
       -- berubah antar request. Dengan kolom ini, query itu membaca satu view
       -- saja dan turun ke satuan milidetik. Biayanya 53.000 baris salinan —
       -- dan kewajiban me-refresh view ini setiap kali review_scores berubah.
       r.tanggal, r.rating, r.likes, rs.pred_label
FROM pasangan p
JOIN reviews r        ON r.id = p.review_id
JOIN review_scores rs ON rs.review_id = p.review_id
                     AND rs.model_name = 'logistic_regression_final';

CREATE UNIQUE INDEX idx_review_kategori_pk      ON review_kategori (kategori_id, review_id);
CREATE INDEX        idx_review_kategori_rev     ON review_kategori (review_id);
CREATE INDEX        idx_review_kategori_tanggal ON review_kategori (kategori_id, tanggal);
CREATE INDEX        idx_review_kategori_likes   ON review_kategori (kategori_id, likes DESC, review_id);

-- ---------------------------------------------------------------------------
-- agg_kategori — jalur cepat /api/topics saat tanpa filter tanggal.
-- Memakai model produksi yang sama dengan agg_monthly/agg_version (gerbang
-- H-10): logistic_regression_final.
-- ---------------------------------------------------------------------------
CREATE MATERIALIZED VIEW agg_kategori AS
SELECT
    rk.kategori_id                            AS id,
    rk.kategori,
    count(*)                                  AS jumlah_ulasan,
    count(*) FILTER (WHERE rk.pred_label = 0) AS jumlah_negatif,
    round(100.0 * count(*) FILTER (WHERE rk.pred_label = 0)
          / NULLIF(count(*), 0), 2)           AS persen_negatif,
    sum(rk.likes)                             AS total_likes,
    round(avg(rk.rating)::numeric, 2)         AS rata_rating
FROM review_kategori rk
GROUP BY rk.kategori_id, rk.kategori
ORDER BY jumlah_ulasan DESC;

CREATE UNIQUE INDEX idx_agg_kategori_id ON agg_kategori (id);

-- ---------------------------------------------------------------------------
-- agg_weekly — /api/trend dengan granularity=week.
-- Bentuknya sengaja dibuat identik dengan agg_monthly agar satu skema Pydantic
-- melayani kedua granularitas.
-- ---------------------------------------------------------------------------
CREATE MATERIALIZED VIEW agg_weekly AS
SELECT
    date_trunc('week', r.tanggal)::date        AS bulan,
    count(*)                                     AS total_ulasan,
    count(*) FILTER (WHERE rs.pred_label = 0)    AS jumlah_negatif,
    round(100.0 * count(*) FILTER (WHERE rs.pred_label = 0)
          / NULLIF(count(*), 0), 2)              AS persen_negatif,
    round(avg(r.rating)::numeric, 2)             AS rata_rating,
    sum(r.likes)                                 AS total_likes,
    -- Pekan parsial: pekan pertama (data mulai 21 Mei 2024, hari Selasa) dan
    -- pekan terakhir (data berhenti 31 Desember 2025, hari Rabu).
    date_trunc('week', r.tanggal)::date IN (
        (SELECT date_trunc('week', min(tanggal))::date FROM reviews),
        (SELECT date_trunc('week', max(tanggal))::date FROM reviews)
    )                                            AS periode_parsial
FROM reviews r
JOIN review_scores rs
  ON rs.review_id = r.id AND rs.model_name = 'logistic_regression_final'
GROUP BY 1
ORDER BY 1;

CREATE UNIQUE INDEX idx_agg_weekly_bulan ON agg_weekly (bulan);

REFRESH MATERIALIZED VIEW review_kategori;
REFRESH MATERIALIZED VIEW agg_kategori;
REFRESH MATERIALIZED VIEW agg_weekly;

-- ---------------------------------------------------------------------------
-- agg_monthly_aktual — label AKTUAL (dari rating), bukan prediksi model.
--
-- /api/kpi melaporkan `baseline_negatif` berdampingan dengan `persen_negatif`
-- hasil model. Tanpa baris ini, angka pembanding itu harus dihitung dari
-- 100.000 baris `reviews` pada setiap request, atau — lebih buruk —
-- di-hardcode di frontend.
--
-- Rating 3 (`sentimen_aktual` NULL) tidak punya label aktual dan tidak ikut
-- dihitung; itu sebabnya `n_berlabel` < `total_ulasan` agg_monthly.
-- ---------------------------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS agg_monthly_aktual;

CREATE MATERIALIZED VIEW agg_monthly_aktual AS
SELECT
    date_trunc('month', tanggal)::date          AS bulan,
    count(*) FILTER (WHERE sentimen_aktual IS NOT NULL) AS n_berlabel,
    count(*) FILTER (WHERE sentimen_aktual = 0)         AS n_negatif_aktual
FROM reviews
GROUP BY 1
ORDER BY 1;

CREATE UNIQUE INDEX idx_agg_monthly_aktual_bulan ON agg_monthly_aktual (bulan);

-- ---------------------------------------------------------------------------
-- agg_meta — satu baris konstanta cakupan data.
--
-- Angka-angka inilah yang dituntut T-7.3 agar "catatan metodologis ikut
-- mengalir ke UI secara otomatis": persentase versi NULL dan cakupan versi
-- yang lolos ambang. Dihitung sekali di sini supaya tidak ada satu pun angka
-- metodologis yang di-hardcode, baik di API maupun di frontend.
-- ---------------------------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS agg_meta;

CREATE MATERIALIZED VIEW agg_meta AS
SELECT
    (SELECT count(*) FROM reviews)                                    AS total_ulasan,
    (SELECT count(*) FROM reviews WHERE versi_minor IS NOT NULL)      AS n_versi_minor_terisi,
    (SELECT round(100.0 * count(*) FILTER (WHERE versi_app IS NULL)
                  / NULLIF(count(*), 0), 2) FROM reviews)             AS versi_null_pct,
    (SELECT min(tanggal) FROM reviews)                                AS tanggal_min,
    (SELECT max(tanggal) FROM reviews)                                AS tanggal_max;

REFRESH MATERIALIZED VIEW agg_monthly_aktual;
REFRESH MATERIALIZED VIEW agg_meta;

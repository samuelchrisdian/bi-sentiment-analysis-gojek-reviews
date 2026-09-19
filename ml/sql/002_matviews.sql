-- Materialized view agregat untuk API/dashboard (Fase 6, T-6.3 s/d T-6.5).
--
-- Ketiga view di bawah memakai model_name = 'logistic_regression_final' —
-- BUKAN 'linear_svc' seperti draf awal rencana Fase 6. Gerbang H-10
-- (docs/model_decision.md, 17 September 2026) menetapkan LogisticRegression
-- C=1.0 sebagai model produksi setelah rencana ini ditulis; dashboard agregat
-- harus mencerminkan model yang sesungguhnya melayani /api/predict, bukan
-- kandidat pembanding. Perbandingan lintas-model (5 baris review_scores per
-- ulasan) tetap tersedia lewat query terpisah di endpoint perbandingan model.

DROP MATERIALIZED VIEW IF EXISTS agg_monthly;
DROP MATERIALIZED VIEW IF EXISTS agg_version;
DROP MATERIALIZED VIEW IF EXISTS agg_topic;

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
  ON rs.review_id = r.id AND rs.model_name = 'logistic_regression_final'
GROUP BY 1
ORDER BY 1;

CREATE UNIQUE INDEX idx_agg_monthly_bulan ON agg_monthly (bulan);

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
      ON rs.review_id = r.id AND rs.model_name = 'logistic_regression_final'
    WHERE r.versi_minor IS NOT NULL
    GROUP BY r.versi_minor
)
SELECT *,
       round(100.0 * jumlah_negatif / NULLIF(total_ulasan, 0), 2) AS persen_negatif
FROM per_minor
WHERE total_ulasan >= 100          -- ambang dari config: versions.min_reviews_per_version
ORDER BY pertama_muncul;

CREATE UNIQUE INDEX idx_agg_version_minor ON agg_version (versi_minor);

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

REFRESH MATERIALIZED VIEW agg_monthly;
REFRESH MATERIALIZED VIEW agg_version;
REFRESH MATERIALIZED VIEW agg_topic;

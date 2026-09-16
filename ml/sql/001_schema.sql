-- Skema database (Fase 0, T-0.7) — sesuai Bagian 1.5 dokumen arsitektur.
-- Dipasang sebagai init script container: dijalankan otomatis saat volume kosong.
-- Materialized view agg_* TIDAK dibuat di sini; itu milik Fase 6.

CREATE TABLE reviews (
    id              BIGINT      PRIMARY KEY,
    nama_user       TEXT,
    ulasan          TEXT        NOT NULL,
    ulasan_clean    TEXT,
    rating          SMALLINT    NOT NULL CHECK (rating BETWEEN 1 AND 5),
    tanggal         TIMESTAMPTZ NOT NULL,
    likes           INTEGER     NOT NULL DEFAULT 0,
    versi_app       TEXT,                    -- NULL pada 21,9% baris (Temuan 4)
    versi_minor     TEXT,                    -- turunan: '4.93.1' -> '4.93'
    word_count      SMALLINT,                -- dari ulasan_normalized (Fase 2)
    sentimen_aktual SMALLINT                 -- 0=neg, 1=pos, NULL jika rating=3
);

CREATE TABLE review_scores (
    review_id     BIGINT   REFERENCES reviews(id) ON DELETE CASCADE,
    model_name    TEXT     NOT NULL,         -- 'complement_nb' | 'linear_svc'
    pred_label    SMALLINT NOT NULL,
    pred_proba    REAL,                      -- NULL jika model tanpa kalibrasi
    PRIMARY KEY (review_id, model_name)
);

CREATE TABLE topics (
    id          SERIAL PRIMARY KEY,
    kategori    TEXT NOT NULL,               -- diisi manusia di gerbang H-8
    keyword     TEXT NOT NULL,
    bobot       REAL
);

CREATE TABLE review_topics (
    review_id  BIGINT  REFERENCES reviews(id) ON DELETE CASCADE,
    topic_id   INTEGER REFERENCES topics(id),
    PRIMARY KEY (review_id, topic_id)
);

CREATE TABLE model_metrics (
    id            SERIAL PRIMARY KEY,
    model_name    TEXT NOT NULL,
    eval_set      TEXT NOT NULL,             -- 'full' | 'informative_ge5w'
    accuracy      REAL,
    precision_neg REAL,
    recall_neg    REAL,
    f1_neg        REAL,
    macro_f1      REAL,
    train_seconds REAL,
    created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_reviews_tanggal   ON reviews (tanggal);
CREATE INDEX idx_reviews_versi     ON reviews (versi_minor) WHERE versi_minor IS NOT NULL;
CREATE INDEX idx_reviews_sentimen  ON reviews (sentimen_aktual);
CREATE INDEX idx_reviews_wordcount ON reviews (word_count);

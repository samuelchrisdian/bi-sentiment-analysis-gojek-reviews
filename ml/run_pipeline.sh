#!/usr/bin/env bash
# Orkestrasi end-to-end (Fase 6, T-6.7): satu perintah untuk membangun ulang
# seluruh data, dari CSV mentah sampai database + materialized view siap
# query. Dirujuk README Fase 9.
#
# Urutan mengikuti dependensi nyata, bukan sekadar nomor fase:
#   - load_reviews HARUS mendahului topic_assign & load_scores, karena
#     `review_topics` dan `review_scores` ber-FK ke `reviews`.
#   - finalize dijalankan dengan model hasil gerbang H-10 (LogisticRegression,
#     lihat docs/model_decision.md) — bukan pilihan otomatis skor tertinggi.
set -euo pipefail
cd "$(dirname "$0")/.."

set -a; source .env; set +a
# psql tidak menerima prefiks SQLAlchemy "+psycopg2" pada DATABASE_URL.
PSQL_DSN="${DATABASE_URL/+psycopg2/}"

python -m ml.src.ingest
python -m ml.src.preprocess
python -m ml.src.load_reviews

python -m ml.src.train
python -m ml.src.tune
python -m ml.src.finalize logistic_regression      # gerbang H-10

python -m ml.src.topics
python -m ml.src.topic_assign

python -m ml.src.score
python -m ml.src.load_scores
python -m ml.src.load_metrics

psql "$PSQL_DSN" -f ml/sql/002_matviews.sql

echo "Pipeline selesai."

#!/usr/bin/env bash
# Pipeline end-to-end: data mentah sampai database, materialized view, dan facts.yaml.
#
# Langkah manual (berkas *_reviewed.csv di docs/tables/) harus sudah ada; skrip ini
# tidak menggantikan audit terjemahan, verifikasi pra-pemrosesan, penamaan
# kategori, analisis kesalahan, maupun validasi silang.
#
#   ./ml/run_pipeline.sh            # pakai data mentah yang ada
#   ./ml/run_pipeline.sh --scrape   # ambil ulang dari Google Play dulu (lama, butuh internet)
set -euo pipefail
cd "$(dirname "$0")/.."

set -a; source .env; set +a
# psql tidak menerima prefiks SQLAlchemy "+psycopg2".
PSQL_DSN="${DATABASE_URL/+psycopg2/}"
PY=.venv/bin/python

if [[ "${1:-}" == "--scrape" || ! -f data/raw/gojek_reviews_5Y.csv ]]; then
  $PY data/script-scraping/scrape_5_tahun.py
fi
# venv terpisah: torch butuh NumPy 2, .venv utama mengunci NumPy <2 untuk gensim.
.venv-translate/bin/python -m ml.src.translate

$PY -m ml.src.build_slang_dict
$PY -m ml.src.preprocess
$PY -m ml.src.train
$PY -m ml.src.tune
$PY -m ml.src.finalize logistic_regression   # docs/model_decision.md
for m in three_class interpret error_analysis viz_cm viz_models topics; do
  $PY -m ml.src.$m
done

# reviews harus dimuat sebelum topic_assign dan load_scores (FK ke reviews).
$PY -m ml.src.load_reviews
$PY -m ml.src.topic_assign
$PY -m ml.src.score
$PY -m ml.src.load_scores
$PY -m ml.src.load_metrics

psql "$PSQL_DSN" -v ON_ERROR_STOP=1 -q -f ml/sql/002_matviews.sql
# 003 membaca review_topics, jadi setelah topic_assign.
psql "$PSQL_DSN" -v ON_ERROR_STOP=1 -q -f ml/sql/003_api_views.sql

$PY -m ml.src.eda
$PY -m ml.src.rm3
$PY -m ml.src.collect_facts

echo "Pipeline selesai."

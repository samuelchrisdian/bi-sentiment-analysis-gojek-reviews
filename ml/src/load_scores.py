"""Muat review_scores ke PostgreSQL (Fase 6, T-6.2).

`review_scores` ber-FK ke `reviews`, sehingga tabel itu harus terisi lebih
dulu (`load_reviews.py`). 500.000 baris (5 model x 100.000 ulasan) lewat
`to_sql` memakan menit; `COPY` selesai dalam detik (T-6.2, rencana Fase 6).
"""
from __future__ import annotations

import io
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from .config import load_config

CFG = load_config()
ROOT = CFG["_root"]
KOLOM = ["review_id", "model_name", "pred_label", "pred_proba"]


def main() -> None:
    load_dotenv(ROOT / ".env")
    eng = create_engine(os.environ[CFG["database"]["dsn_env"]])
    df = pd.read_parquet(ROOT / "data" / "processed" / "review_scores.parquet")[KOLOM]

    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False, sep="\t", na_rep="\\N")
    buf.seek(0)

    with eng.begin() as c:
        c.execute(text("TRUNCATE review_scores"))
        with c.connection.cursor() as cur:
            cur.copy_expert(
                "COPY review_scores (review_id, model_name, pred_label, pred_proba) "
                "FROM STDIN WITH (FORMAT csv, DELIMITER E'\\t', NULL '\\N')", buf)

    with eng.connect() as c:
        n = c.execute(text("SELECT count(*) FROM review_scores")).scalar()
        print(f"review_scores: {n:,} baris")
        for r in c.execute(text(
                "SELECT model_name, count(*), "
                "round(100.0 * count(*) FILTER (WHERE pred_label = 0) / count(*), 2), "
                "count(pred_proba) FROM review_scores "
                "GROUP BY model_name ORDER BY model_name")):
            print(f"  {r[0]:28s} n={r[1]:,}  pred_negatif={r[2]}%  "
                  f"pred_proba_terisi={r[3]:,}")

    n_model = df.model_name.nunique()
    assert n == CFG["schema"]["expected_rows"] * n_model, \
        f"{n} != {CFG['schema']['expected_rows']} x {n_model}"


if __name__ == "__main__":
    main()

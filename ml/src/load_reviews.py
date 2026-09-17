"""Muat reviews ke PostgreSQL (prasyarat Fase 5 T-5.6/T-5.8 dan Fase 6).

`review_topics` memiliki foreign key ke `reviews`, sehingga tabel ini harus
terisi sebelum penetapan topik dapat ditulis. Sumbernya parquet Fase 2 — bukan
CSV mentah — agar `ulasan_clean`, `word_count`, dan `sentimen_aktual` yang masuk
DB identik dengan yang dipakai melatih model.
"""
from __future__ import annotations

import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from .config import load_config, resolve

CFG = load_config()
ROOT = CFG["_root"]
KOLOM = ["id", "nama_user", "ulasan", "ulasan_clean", "rating", "tanggal",
         "likes", "versi_app", "versi_minor", "word_count", "sentimen_aktual"]


def main() -> None:
    load_dotenv(ROOT / ".env")
    eng = create_engine(os.environ[CFG["database"]["dsn_env"]])
    df = pd.read_parquet(resolve(CFG, "paths.clean_parquet"))[KOLOM].copy()

    # sentimen_aktual bertipe Int8 (nullable) — psycopg2 butuh object/None.
    df["sentimen_aktual"] = df.sentimen_aktual.astype("object").where(
        df.sentimen_aktual.notna(), None)
    for k in ("nama_user", "versi_app", "versi_minor"):
        df[k] = df[k].astype("object").where(df[k].notna(), None)

    with eng.begin() as c:
        # review_topics & review_scores punya FK ON DELETE CASCADE ke reviews.
        c.execute(text("TRUNCATE reviews CASCADE"))
    df.to_sql("reviews", eng, if_exists="append", index=False,
              chunksize=5000, method="multi")

    with eng.connect() as c:
        n = c.execute(text("SELECT count(*) FROM reviews")).scalar()
        neg = c.execute(text("SELECT count(*) FROM reviews WHERE sentimen_aktual = 0")).scalar()
        nul = c.execute(text("SELECT count(*) FROM reviews WHERE sentimen_aktual IS NULL")).scalar()
        rng = c.execute(text("SELECT min(tanggal)::date, max(tanggal)::date FROM reviews")).one()
        lk = c.execute(text("SELECT sum(likes) FROM reviews")).scalar()
    print(f"reviews        : {n:,} baris")
    print(f"  negatif      : {neg:,}")
    print(f"  netral (NULL): {nul:,}")
    print(f"  rentang      : {rng[0]} s/d {rng[1]}")
    print(f"  total likes  : {lk:,}")
    assert n == CFG["schema"]["expected_rows"], f"{n} != {CFG['schema']['expected_rows']}"


if __name__ == "__main__":
    main()

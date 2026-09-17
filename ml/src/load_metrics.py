"""Muat model_metrics ke PostgreSQL (Fase 3, T-3.8).

Dua jalur penulisan dilakukan keduanya: CSV untuk laporan (tidak butuh DB
hidup) dan tabel PostgreSQL sebagai sumber endpoint /api/model/metrics.
"""
from __future__ import annotations

import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from .config import load_config

CFG = load_config()
ROOT = CFG["_root"]
KOLOM_DB = ["model_name", "eval_set", "accuracy", "precision_neg", "recall_neg",
            "f1_neg", "macro_f1", "train_seconds"]


def main() -> None:
    load_dotenv(ROOT / ".env")
    dsn = os.environ[CFG["database"]["dsn_env"]]
    df = pd.read_csv(ROOT / "docs" / "tables" / "model_metrics.csv")

    # Hanya varian dedup (konfigurasi resmi) yang masuk DB; varian pembanding
    # tetap hidup di CSV agar tidak mengacaukan dashboard dengan baris ganda.
    df = df[df.dedup_training].copy()
    df["model_name"] = df.model_name + df.eval_set.map(lambda _: "")

    eng = create_engine(dsn)
    with eng.begin() as c:
        c.execute(text("TRUNCATE model_metrics RESTART IDENTITY"))
    df[KOLOM_DB].to_sql("model_metrics", eng, if_exists="append", index=False)

    with eng.connect() as c:
        n = c.execute(text("SELECT count(*) FROM model_metrics")).scalar()
        print(f"model_metrics: {n} baris")
        for r in c.execute(text(
                "SELECT model_name, eval_set, round(macro_f1::numeric,4), "
                "round(recall_neg::numeric,4) FROM model_metrics "
                "ORDER BY macro_f1 DESC")):
            print(f"  {r[0]:22s} {r[1]:17s} macro_f1={r[2]}  recall_neg={r[3]}")


if __name__ == "__main__":
    main()

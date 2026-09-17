"""Split kanonik yang dipakai seluruh Fase 4 (T-4.1 s/d T-4.6).

Fase 3 memvektorisasi di dalam `train.siapkan_data`. Fase 4 membutuhkan split
pada level TEKS, karena `GridSearchCV` harus mem-fit vectorizer ulang di setiap
fold (T-4.1). Modul ini menyediakan split itu dengan urutan operasi yang persis
sama seperti Fase 3 — split -> dedup train -> (vectorize belakangan) — sehingga
angka train/test identik dan perbandingan default vs tuned tetap sah.

`assert_konsisten_fase3()` menguji klaim itu, bukan mengasumsikannya.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from .config import load_config, resolve

CFG = load_config()
ROOT = CFG["_root"]
SEED = CFG["seed"]
AMBANG_INFORMATIF = CFG["evaluation"]["informative_min_words"]

# Angka resmi Fase 3 (docs/model_comparison_findings.md). Dipakai sebagai
# pengaman regresi, bukan sebagai dokumentasi.
FASE3 = {"n_labeled": 96466, "n_train": 77172, "n_test": 19294, "n_train_dedup": 45614}


def muat_parquet() -> pd.DataFrame:
    return pd.read_parquet(resolve(CFG, "paths.clean_parquet"))


def _label_tiga_kelas(rating: pd.Series) -> pd.Series:
    """0=negatif(1-2), 1=netral(3), 2=positif(4-5)."""
    lab = pd.Series(1, index=rating.index, dtype="int64")
    lab[rating.isin(CFG["labeling"]["negative_ratings"])] = 0
    lab[rating.isin(CFG["labeling"]["positive_ratings"])] = 2
    return lab


def siapkan_teks(dedup: bool = True, scheme: str = "binary") -> dict:
    """Split stratified pada level teks.

    scheme='binary'      -> rating 3 dibuang, label 0/1 (protokol resmi)
    scheme='three_class' -> seluruh 100k dipakai, label 0/1/2 (T-4.6)
    """
    df = muat_parquet()

    if scheme == "binary":
        df = df[df["sentimen_aktual"].notna()].copy()
        y_all = df["sentimen_aktual"].astype(int)
    elif scheme == "three_class":
        df = df.copy()
        y_all = _label_tiga_kelas(df["rating"])
    else:
        raise ValueError(f"scheme tidak dikenal: {scheme}")

    X_tr, X_te, y_tr, y_te, idx_tr, idx_te = train_test_split(
        df["ulasan_clean"], y_all, df.index,
        test_size=CFG["split"]["test_size"],
        stratify=y_all if CFG["split"]["stratify"] else None,
        random_state=SEED,
    )

    n_sebelum = len(X_tr)
    if dedup:
        # HANYA training set — test set harus tetap merepresentasikan distribusi
        # nyata, duplikat dan semuanya.
        mask = ~X_tr.duplicated()
        X_tr, y_tr, idx_tr = X_tr[mask], y_tr[mask], idx_tr[mask]

    wc = df.loc[idx_te, "word_count"].to_numpy()
    return {
        "df": df,
        "X_tr": X_tr, "X_te": X_te,
        "y_tr": y_tr.to_numpy(), "y_te": y_te.to_numpy(),
        "idx_tr": idx_tr, "idx_te": idx_te,
        "mask_informatif": wc >= AMBANG_INFORMATIF,
        "n_labeled": len(df), "n_train": len(X_tr),
        "n_train_sebelum_dedup": n_sebelum, "n_test": len(X_te),
    }


def assert_konsisten_fase3(d: dict) -> None:
    aktual = {"n_labeled": d["n_labeled"], "n_train": d["n_train_sebelum_dedup"],
              "n_test": d["n_test"], "n_train_dedup": d["n_train"]}
    if aktual != FASE3:
        raise AssertionError(
            f"Split Fase 4 menyimpang dari Fase 3.\n  diharapkan: {FASE3}\n  aktual   : {aktual}")


if __name__ == "__main__":
    d = siapkan_teks()
    assert_konsisten_fase3(d)
    print("Split biner konsisten dengan Fase 3:")
    for k in ("n_labeled", "n_train_sebelum_dedup", "n_train", "n_test"):
        print(f"  {k:24s} {d[k]:,}")
    print(f"  informatif di test       {int(d['mask_informatif'].sum()):,}")

    t = siapkan_teks(scheme="three_class")
    print("\nSplit tiga kelas:")
    print(f"  data                     {t['n_labeled']:,}")
    print(f"  train (dedup) / test     {t['n_train']:,} / {t['n_test']:,}")
    print(f"  distribusi train         {np.bincount(t['y_tr']).tolist()}")
    print(f"  distribusi test          {np.bincount(t['y_te']).tolist()}")

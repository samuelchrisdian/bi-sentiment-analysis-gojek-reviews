"""Baseline & komparasi model (Fase 3, T-3.1 s/d T-3.8).

Urutan operasi TIDAK BOLEH dibalik:

    1. split stratified   (sebelum apa pun yang melihat data)
    2. deduplikasi        (HANYA training set)
    3. fit vectorizer     (HANYA pada training set)

Mem-fit TF-IDF pada data penuh, atau mendeduplikasi test set, adalah kebocoran
data yang membatalkan seluruh angka di fase ini.
"""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import ComplementNB, MultinomialNB
from sklearn.svm import LinearSVC

from .config import load_config, resolve
from .evaluate import hitung_metrik, laporan_lengkap
from .features import build_vectorizer

CFG = load_config()
ROOT = CFG["_root"]
SEED = CFG["seed"]
AMBANG_INFORMATIF = CFG["evaluation"]["informative_min_words"]


def bangun_model(cfg: dict) -> dict:
    """Empat model dengan konfigurasi TF-IDF dan random_state identik.

    ComplementNB, bukan hanya MultinomialNB: ComplementNB dirancang untuk data
    tidak seimbang, dan rasio di sini 27:72. Keduanya tetap dijalankan agar
    perbandingannya dapat dilaporkan; biayanya hitungan detik.

    LinearSVC, BUKAN SVC(kernel='rbf'): kompleksitas SVC antara O(n^2) dan
    O(n^3); pada 96k baris pelatihannya dapat berjam-jam atau gagal. Ini batas
    komputasi, bukan preferensi.

    Naive Bayes tidak menerima class_weight — ketidakseimbangan ditangani
    ComplementNB secara struktural, bukan lewat pembobotan.
    """
    s = cfg["seed"]
    return {
        "complement_nb": ComplementNB(alpha=1.0),
        "multinomial_nb": MultinomialNB(alpha=1.0),
        "linear_svc": LinearSVC(C=1.0, class_weight="balanced", max_iter=5000,
                                random_state=s),
        "logistic_regression": LogisticRegression(C=1.0, class_weight="balanced",
                                                  max_iter=1000, solver="liblinear",
                                                  random_state=s),
    }


def siapkan_data(dedup: bool = True) -> dict:
    df = pd.read_parquet(resolve(CFG, "paths.clean_parquet"))
    df = df[df["sentimen_aktual"].notna()].copy()          # buang rating 3
    df["sentimen_aktual"] = df["sentimen_aktual"].astype(int)
    print(f"  data berlabel        : {len(df):,} baris (100.000 - 3.534 netral)")

    X_tr, X_te, y_tr, y_te, idx_tr, idx_te = train_test_split(
        df["ulasan_clean"], df["sentimen_aktual"], df.index,
        test_size=CFG["split"]["test_size"],
        stratify=df["sentimen_aktual"] if CFG["split"]["stratify"] else None,
        random_state=SEED,
    )
    print(f"  train / test         : {len(X_tr):,} / {len(X_te):,}")

    n_sebelum = len(X_tr)
    if dedup:
        # HANYA training set. Test set harus merepresentasikan distribusi nyata
        # yang akan dihadapi model, duplikat dan semuanya.
        mask = ~X_tr.duplicated()
        X_tr, y_tr = X_tr[mask], y_tr[mask]
        print(f"  dedup training       : {n_sebelum:,} -> {len(X_tr):,} "
              f"({n_sebelum - len(X_tr):,} dibuang)")

    vec = build_vectorizer(CFG)
    Xtr = vec.fit_transform(X_tr)      # fit HANYA pada train
    Xte = vec.transform(X_te)
    print(f"  fitur TF-IDF         : {Xtr.shape[1]:,}")

    wc = df.loc[idx_te, "word_count"].to_numpy()
    return {"Xtr": Xtr, "Xte": Xte, "y_tr": y_tr.to_numpy(), "y_te": y_te.to_numpy(),
            "vec": vec, "mask_informatif": wc >= AMBANG_INFORMATIF,
            "n_train": len(X_tr), "n_train_sebelum_dedup": n_sebelum, "n_test": len(X_te)}


def evaluasi_ganda(nama: str, y_te, y_pred, mask_inf, train_s: float,
                   predict_s: float, simpan_laporan: bool = True) -> list[dict]:
    """Set `full` dan `informative_ge5w`.

    Selisih macro-F1 antara keduanya adalah temuan metodologis utama: ia
    mengukur seberapa besar kinerja model bertumpu pada kata pujian pendek yang
    berulang (39,9% ulasan hanya <=2 kata, hampir seluruhnya positif).
    """
    baris = []
    for eval_set, mask in (("full", np.ones(len(y_te), bool)),
                           ("informative_ge5w", mask_inf)):
        m = hitung_metrik(y_te[mask], y_pred[mask])
        baris.append({"model_name": nama, "eval_set": eval_set, "n_eval": int(mask.sum()),
                      **m, "train_seconds": train_s, "predict_seconds": predict_s})
        if simpan_laporan:
            d = ROOT / "ml" / "artifacts" / "reports"
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{nama}_{eval_set}.json").write_text(
                json.dumps(laporan_lengkap(y_te[mask], y_pred[mask]), indent=2),
                encoding="utf-8")
    return baris


def jalankan(dedup: bool = True, simpan: bool = True) -> pd.DataFrame:
    print(f"\n{'='*64}\nFASE 3 — dedup training: {dedup}\n{'='*64}")
    d = siapkan_data(dedup=dedup)
    hasil: list[dict] = []

    # --- BASELINE DIHITUNG LEBIH DULU, sebelum model apa pun dilatih ---
    print("\n[baseline] kelas mayoritas")
    t0 = time.perf_counter()
    dummy = DummyClassifier(strategy="most_frequent").fit(d["Xtr"], d["y_tr"])
    t_train = time.perf_counter() - t0
    t0 = time.perf_counter()
    pred = dummy.predict(d["Xte"])
    hasil += evaluasi_ganda("majority_baseline", d["y_te"], pred, d["mask_informatif"],
                            t_train, time.perf_counter() - t0, simpan_laporan=False)
    base_acc = hasil[0]["accuracy"]
    base_f1 = hasil[0]["macro_f1"]
    print(f"           accuracy={base_acc:.4f}  macro_f1={base_f1:.4f}  "
          f"recall_neg={hasil[0]['recall_neg']:.4f}")
    print("           -> model yang tidak mengungguli macro_f1 ini tidak mempelajari apa pun")

    for nama, model in bangun_model(CFG).items():
        print(f"\n[{nama}]")
        t0 = time.perf_counter()
        model.fit(d["Xtr"], d["y_tr"])
        t_train = time.perf_counter() - t0
        t0 = time.perf_counter()
        pred = model.predict(d["Xte"])
        t_pred = time.perf_counter() - t0
        baris = evaluasi_ganda(nama, d["y_te"], pred, d["mask_informatif"],
                               t_train, t_pred, simpan_laporan=simpan)
        hasil += baris
        for b in baris:
            print(f"  {b['eval_set']:17s} macro_f1={b['macro_f1']:.4f}  "
                  f"recall_neg={b['recall_neg']:.4f}  acc={b['accuracy']:.4f}")
        print(f"  latih {t_train:.2f}s · inferensi {t_pred:.3f}s")

    out = pd.DataFrame(hasil)
    out["dedup_training"] = dedup
    out["n_train"] = d["n_train"]
    out["n_test"] = d["n_test"]
    return out


if __name__ == "__main__":
    tabel = jalankan(dedup=CFG["preprocessing"]["dedup_training_text"])
    path = ROOT / "docs" / "tables" / "model_metrics.csv"
    tabel.to_csv(path, index=False)
    print(f"\nDisimpan: {path.relative_to(ROOT)} ({len(tabel)} baris)")

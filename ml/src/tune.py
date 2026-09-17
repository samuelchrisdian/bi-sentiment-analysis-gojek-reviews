"""GridSearchCV + evaluasi model tuned (Fase 4, T-4.1 & T-4.2).

Vectorizer berada DI DALAM Pipeline. Ini bukan detail gaya: mem-fit TF-IDF di
luar cross-validation membuat setiap fold validasi ikut menentukan vocabulary
dan bobot IDF-nya sendiri — kebocoran halus yang menaikkan skor CV tanpa
menaikkan kinerja sebenarnya. Di sini vectorizer di-fit ulang pada 4/5 data di
setiap fold, sama seperti yang terjadi saat model dipakai pada data baru.

scoring='f1_macro', bukan 'accuracy' — konsisten dengan prioritas metrik
Bagian 2.3 (baseline mayoritas sudah memperoleh accuracy 0,723 tanpa belajar).
"""
from __future__ import annotations

import json
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.naive_bayes import ComplementNB, MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from .config import load_config
from .dataset import assert_konsisten_fase3, siapkan_teks
from .evaluate import hitung_metrik, laporan_lengkap
from .features import build_vectorizer

CFG = load_config()
ROOT = CFG["_root"]
SEED = CFG["seed"]

# Grid sengaja kecil (4-8 kombinasi per model). Grid besar pada 45k x 30k
# menghabiskan waktu tanpa menambah informasi: kurva C untuk model linear pada
# TF-IDF landai, dan alpha NB hanya menggeser smoothing.
GRIDS = {
    "complement_nb": {"clf__alpha": [0.1, 0.5, 1.0, 2.0]},
    "multinomial_nb": {"clf__alpha": [0.1, 0.5, 1.0, 2.0]},
    "linear_svc": {"clf__C": [0.1, 0.5, 1.0, 5.0],
                   "clf__class_weight": [None, "balanced"]},
    "logistic_regression": {"clf__C": [0.1, 0.5, 1.0, 5.0],
                            "clf__class_weight": [None, "balanced"]},
}

BASE = {
    "complement_nb": ComplementNB(),
    "multinomial_nb": MultinomialNB(),
    "linear_svc": LinearSVC(max_iter=5000, random_state=SEED),
    "logistic_regression": LogisticRegression(max_iter=1000, solver="liblinear",
                                              random_state=SEED),
}


def _cv() -> StratifiedKFold:
    return StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)


def gridsearch_satu(nama: str, X_tr, y_tr) -> GridSearchCV:
    pipe = Pipeline([("tfidf", build_vectorizer(CFG)), ("clf", BASE[nama])])
    gs = GridSearchCV(pipe, GRIDS[nama], scoring="f1_macro", cv=_cv(),
                      n_jobs=-1, verbose=1, return_train_score=True)
    t0 = time.perf_counter()
    gs.fit(X_tr, y_tr)
    gs.waktu_ = time.perf_counter() - t0
    return gs


def evaluasi_ganda(nama: str, y_te, y_pred, mask_inf, train_s: float,
                   predict_s: float) -> list[dict]:
    baris = []
    d = ROOT / "ml" / "artifacts" / "reports"
    d.mkdir(parents=True, exist_ok=True)
    for eval_set, mask in (("full", np.ones(len(y_te), bool)),
                           ("informative_ge5w", mask_inf)):
        baris.append({"model_name": nama, "eval_set": eval_set,
                      "n_eval": int(mask.sum()),
                      **hitung_metrik(y_te[mask], y_pred[mask]),
                      "train_seconds": train_s, "predict_seconds": predict_s})
        (d / f"{nama}_{eval_set}.json").write_text(
            json.dumps(laporan_lengkap(y_te[mask], y_pred[mask]), indent=2),
            encoding="utf-8")
    return baris


def jalankan() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    d = siapkan_teks(dedup=CFG["preprocessing"]["dedup_training_text"])
    assert_konsisten_fase3(d)
    print(f"train {d['n_train']:,} · test {d['n_test']:,} · "
          f"informatif {int(d['mask_informatif'].sum()):,}\n")

    cv_rows, metrik_rows, terbaik = [], [], {}

    for nama in GRIDS:
        n_komb = int(np.prod([len(v) for v in GRIDS[nama].values()]))
        print(f"{'='*64}\n[{nama}] {n_komb} kombinasi x 5 fold = {n_komb*5} fit")
        gs = gridsearch_satu(nama, d["X_tr"], d["y_tr"])
        print(f"  best f1_macro (CV) = {gs.best_score_:.4f}  params={gs.best_params_}")
        print(f"  waktu gridsearch   = {gs.waktu_:.1f} s")

        r = pd.DataFrame(gs.cv_results_)
        r.insert(0, "model_name", nama)
        r["overfit_gap"] = r["mean_train_score"] - r["mean_test_score"]
        cv_rows.append(r)

        # Refit pada seluruh train dengan parameter terbaik -> ini model tuned.
        best = gs.best_estimator_
        t0 = time.perf_counter()
        pred = best.predict(d["X_te"])
        t_pred = time.perf_counter() - t0

        # gs.refit sudah melatih best_estimator_ pada seluruh train; waktunya
        # diukur terpisah agar sebanding dengan train_seconds Fase 3.
        t0 = time.perf_counter()
        clone(best).fit(d["X_tr"], d["y_tr"])
        t_train = time.perf_counter() - t0

        baris = evaluasi_ganda(f"{nama}_tuned", d["y_te"], pred,
                               d["mask_informatif"], t_train, t_pred)
        metrik_rows += baris
        for b in baris:
            print(f"  {b['eval_set']:17s} macro_f1={b['macro_f1']:.4f}  "
                  f"recall_neg={b['recall_neg']:.4f}  acc={b['accuracy']:.4f}")

        terbaik[nama] = {
            "best_params": {k.replace("clf__", ""): v for k, v in gs.best_params_.items()},
            "cv_f1_macro": float(gs.best_score_),
            "cv_f1_macro_std": float(r.loc[gs.best_index_, "std_test_score"]),
            "overfit_gap": float(r.loc[gs.best_index_, "overfit_gap"]),
            "gridsearch_seconds": round(gs.waktu_, 2),
        }
        joblib.dump(best, ROOT / "ml" / "artifacts" / f"tuned_{nama}.joblib")

    cv = pd.concat(cv_rows, ignore_index=True)
    met = pd.DataFrame(metrik_rows)
    met["dedup_training"] = True
    met["n_train"] = d["n_train"]
    met["n_test"] = d["n_test"]
    return cv, met, terbaik


def simpan(cv: pd.DataFrame, met: pd.DataFrame, terbaik: dict) -> None:
    kol = ["model_name", "params", "mean_test_score", "std_test_score",
           "mean_train_score", "std_train_score", "overfit_gap",
           "rank_test_score", "mean_fit_time"]
    p = ROOT / "docs" / "tables" / "gridsearch_results.csv"
    cv[kol].sort_values(["model_name", "rank_test_score"]).to_csv(p, index=False)
    print(f"\nDisimpan: {p.relative_to(ROOT)} ({len(cv)} kombinasi)")

    # Baris Fase 3 TIDAK ditimpa — perbandingan default vs tuned adalah hasil.
    pm = ROOT / "docs" / "tables" / "model_metrics.csv"
    lama = pd.read_csv(pm)
    lama = lama[~lama.model_name.str.endswith("_tuned")]      # idempoten
    pd.concat([lama, met], ignore_index=True).to_csv(pm, index=False)
    print(f"Disimpan: {pm.relative_to(ROOT)} (+{len(met)} baris *_tuned)")

    pb = ROOT / "ml" / "artifacts" / "best_params.json"
    pb.write_text(json.dumps(terbaik, indent=2), encoding="utf-8")
    print(f"Disimpan: {pb.relative_to(ROOT)}")


if __name__ == "__main__":
    simpan(*jalankan())


def pilih_1se(cv: pd.DataFrame, nama: str) -> dict:
    """Aturan satu simpangan baku (Breiman et al., 1984).

    `GridSearchCV` memilih skor CV tertinggi tanpa memperhitungkan bahwa skor
    itu sendiri punya ragam. Aturan 1-SE memilih model PALING SEDERHANA yang
    skornya masih berada dalam satu simpangan baku dari yang terbaik — pada
    model linear, "paling sederhana" berarti regularisasi terkuat (C terkecil).

    Ini relevan di sini karena LogisticRegression C=5,0 hanya unggul 0,00015
    dari C=1,0, sementara simpangan bakunya 0,0030 — dua puluh kali lebih besar
    dari selisihnya, dan C=5,0 punya selisih train-test dua kali lipat.
    """
    g = cv[cv.model_name == nama].copy()
    terbaik = g.loc[g.mean_test_score.idxmax()]
    ambang = terbaik.mean_test_score - terbaik.std_test_score
    kandidat = g[g.mean_test_score >= ambang].copy()

    # "Paling sederhana" = regularisasi terkuat: C terkecil, atau alpha terbesar.
    kandidat["params_dict"] = kandidat.params.apply(
        lambda s: eval(s) if isinstance(s, str) else s)
    def kesederhanaan(p):
        if "clf__C" in p:
            return p["clf__C"]
        return -p["clf__alpha"]          # alpha besar = smoothing kuat = sederhana
    kandidat["_urut"] = kandidat.params_dict.apply(kesederhanaan)
    pilih = kandidat.sort_values(["_urut", "mean_test_score"],
                                 ascending=[True, False]).iloc[0]
    p = pilih.params_dict
    return {
        "best_params": {k.replace("clf__", ""): v for k, v in p.items()},
        "cv_f1_macro": float(pilih.mean_test_score),
        "cv_f1_macro_std": float(pilih.std_test_score),
        "overfit_gap": float(pilih.overfit_gap),
        "ambang_1se": float(ambang),
        "n_kandidat_dalam_1se": int(len(kandidat)),
        "sama_dengan_gridsearch": bool(pilih.mean_test_score == terbaik.mean_test_score),
    }

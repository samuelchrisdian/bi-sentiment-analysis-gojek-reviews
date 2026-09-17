"""Eksperimen varian tiga kelas (Fase 4, T-4.6).

Dijalankan justru karena diperkirakan gagal. Keputusan H-3 membuang rating 3;
keputusan itu hanya dapat dipertahankan di laporan bila ada bukti kuantitatif
bahwa skema tiga kelas memang tidak layak pada dataset ini — bukan sekadar
pernyataan bahwa kelasnya kecil.

Dua argumennya diuji terpisah:
  (a) ketimpangan  — rasio kelas netral terhadap positif,
  (b) kemiripan    — panjang teks kelas netral vs kelas negatif (Temuan 3).
Confusion matrix menunjukkan ke mana ulasan bintang 3 sebenarnya jatuh.
"""
from __future__ import annotations

import json
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (classification_report, confusion_matrix, f1_score,
                             recall_score)
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from .config import load_config
from .dataset import siapkan_teks
from .features import build_vectorizer

CFG = load_config()
ROOT = CFG["_root"]
FIG = ROOT / "docs" / "figures"
KELAS = ["Negatif (1-2)", "Netral (3)", "Positif (4-5)"]


def _model():
    """Parameter hasil tuning biner (T-4.1), dipakai apa adanya.

    Menyetel ulang grid untuk skema tiga kelas tidak akan mengubah kesimpulan:
    yang membatasi bukan hyperparameter, melainkan 2.595 contoh netral yang
    tidak terpisahkan secara leksikal dari kelas negatif.
    """
    bp = json.loads((ROOT / "ml" / "artifacts" / "best_params.json").read_text())
    p = bp["linear_svc"]["best_params"]
    return LinearSVC(C=p["C"], class_weight=p["class_weight"], max_iter=5000,
                     random_state=CFG["seed"])


def panjang_per_kelas(d: dict) -> pd.DataFrame:
    """Argumen (b): apakah netral benar-benar mirip negatif dalam panjang teks."""
    df = d["df"].loc[d["idx_te"]].copy()
    df["kelas"] = d["y_te"]
    t = df.groupby("kelas")["word_count"].agg(["count", "mean", "median", "std"])
    t.index = KELAS
    return t.round(2)


def jalankan() -> dict:
    d = siapkan_teks(dedup=CFG["preprocessing"]["dedup_training_text"],
                     scheme="three_class")
    pipe = Pipeline([("tfidf", build_vectorizer(CFG)), ("clf", _model())])
    t0 = time.perf_counter()
    pipe.fit(d["X_tr"], d["y_tr"])
    t_train = time.perf_counter() - t0
    pred = pipe.predict(d["X_te"])

    cm = confusion_matrix(d["y_te"], pred, labels=[0, 1, 2])
    rec = recall_score(d["y_te"], pred, average=None, labels=[0, 1, 2], zero_division=0)
    return {
        "macro_f1": float(f1_score(d["y_te"], pred, average="macro", zero_division=0)),
        "recall": dict(zip(KELAS, rec.round(4).tolist())),
        "cm": cm,
        "laporan": classification_report(d["y_te"], pred, labels=[0, 1, 2],
                                         target_names=KELAS, zero_division=0,
                                         output_dict=True),
        "panjang": panjang_per_kelas(d),
        "n_train": d["n_train"], "n_test": d["n_test"],
        "dist_train": np.bincount(d["y_tr"], minlength=3).tolist(),
        "dist_test": np.bincount(d["y_te"], minlength=3).tolist(),
        "train_seconds": round(t_train, 2),
    }


def gambar_07(cm: np.ndarray) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6))
    for ax, norm in zip(axes, (False, True)):
        m = cm / cm.sum(axis=1, keepdims=True) if norm else cm
        ax.imshow(m, cmap="Oranges", vmin=0, vmax=m.max())
        for i in range(3):
            for j in range(3):
                ax.text(j, i, f"{m[i, j]:.3f}" if norm else f"{cm[i, j]:,}",
                        ha="center", va="center", fontsize=10.5,
                        color="white" if m[i, j] > m.max() * 0.55 else "#222")
        ax.set_xticks(range(3), KELAS, fontsize=8.5, rotation=12)
        ax.set_yticks(range(3), KELAS, fontsize=8.5)
        ax.set_xlabel("Prediksi"); ax.set_ylabel("Aktual")
        ax.set_title("Ternormalisasi per baris (= recall)" if norm
                     else "Hitungan absolut", fontsize=10)
    fig.suptitle("Gambar 7 — Skema tiga kelas: ke mana ulasan bintang 3 jatuh",
                 fontsize=11.5)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    for dpi, suf in ((150, ""), (300, "@300")):
        fig.savefig(FIG / f"gambar-07-tiga-kelas{suf}.png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    h = jalankan()
    gambar_07(h["cm"])
    print(f"train {h['n_train']:,} · test {h['n_test']:,} · latih {h['train_seconds']} s")
    print(f"distribusi train {h['dist_train']} · test {h['dist_test']}")
    print(f"\nmacro-F1 tiga kelas = {h['macro_f1']:.4f}")
    for k, v in h["recall"].items():
        print(f"  recall {k:16s} = {v:.4f}")
    print(f"\nConfusion matrix (baris=aktual):\n{h['cm']}")
    n3 = h["cm"][1]
    print(f"\nDari {n3.sum():,} ulasan bintang 3 di test:")
    for i, k in enumerate(KELAS):
        print(f"  -> diprediksi {k:16s} {n3[i]:5,}  ({n3[i]/n3.sum():.1%})")
    print(f"\nPanjang teks per kelas (test):\n{h['panjang'].to_string()}")
    (ROOT / "ml" / "artifacts" / "reports" / "three_class_linear_svc.json").write_text(
        json.dumps({k: v for k, v in h.items() if k not in ("cm", "panjang")}
                   | {"cm": h["cm"].tolist(), "panjang": h["panjang"].to_dict()},
                   indent=2), encoding="utf-8")
    print("\nDisimpan: docs/figures/gambar-07-tiga-kelas.png, "
          "ml/artifacts/reports/three_class_linear_svc.json")

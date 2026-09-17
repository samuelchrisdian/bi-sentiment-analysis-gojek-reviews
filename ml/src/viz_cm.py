"""Confusion matrix model terbaik (Fase 4, T-4.3) — Gambar 6.

Dua versi ditampilkan berdampingan karena keduanya menjawab pertanyaan berbeda:
hitungan absolut menunjukkan berapa banyak keluhan yang lolos triase (biaya
bisnis), ternormalisasi per baris menunjukkan recall per kelas (kualitas model
terlepas dari ketimpangan kelas). Menampilkan hanya yang pertama pada data 72%
positif menyesatkan.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import joblib
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import confusion_matrix

from .config import load_config
from .dataset import siapkan_teks

CFG = load_config()
ROOT = CFG["_root"]
FIG = ROOT / "docs" / "figures"
KELAS = ["Negatif", "Positif"]


def _panel(ax, cm, judul, normalize: bool) -> None:
    m = cm / cm.sum(axis=1, keepdims=True) if normalize else cm
    im = ax.imshow(m, cmap="Blues", vmin=0, vmax=m.max())
    ambang = m.max() * 0.55
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            teks = f"{m[i, j]:.3f}" if normalize else f"{cm[i, j]:,}"
            ax.text(j, i, teks, ha="center", va="center", fontsize=11,
                    color="white" if m[i, j] > ambang else "#222")
    ax.set_xticks([0, 1], KELAS); ax.set_yticks([0, 1], KELAS)
    ax.set_xlabel("Prediksi"); ax.set_ylabel("Aktual")
    ax.set_title(judul, fontsize=9.5)
    return im


def gambar_06(nama_model: str = "linear_svc_tuned") -> dict:
    stem = nama_model.replace("_tuned", "")
    pipe = joblib.load(ROOT / "ml" / "artifacts" / f"tuned_{stem}.joblib")
    d = siapkan_teks(dedup=CFG["preprocessing"]["dedup_training_text"])
    pred = pipe.predict(d["X_te"])

    sets = (("full", np.ones(len(d["y_te"]), bool)),
            ("informative_ge5w (≥5 kata)", d["mask_informatif"]))
    fig, axes = plt.subplots(2, 2, figsize=(8.6, 7.4))
    hasil = {}
    for r, (nama_set, mask) in enumerate(sets):
        cm = confusion_matrix(d["y_te"][mask], pred[mask], labels=[0, 1])
        hasil[nama_set] = cm
        _panel(axes[r, 0], cm, f"{nama_set} — hitungan absolut", False)
        _panel(axes[r, 1], cm, f"{nama_set} — ternormalisasi per baris (= recall)", True)

    fig.suptitle(f"Gambar 6 — Confusion matrix {nama_model} pada dua set evaluasi",
                 fontsize=11.5, y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    for dpi, suf in ((150, ""), (300, "@300")):
        fig.savefig(FIG / f"gambar-06-confusion-matrix{suf}.png", dpi=dpi,
                    bbox_inches="tight")
    plt.close(fig)
    return hasil


if __name__ == "__main__":
    for nama_set, cm in gambar_06().items():
        fn, fp = cm[0, 1], cm[1, 0]
        print(f"\n{nama_set}")
        print(f"  {cm.tolist()}")
        print(f"  negatif lolos triase (FN kelas negatif) : {fn:,} dari {cm[0].sum():,}"
              f"  -> recall neg = {cm[0,0]/cm[0].sum():.4f}")
        print(f"  positif salah ditandai negatif           : {fp:,} dari {cm[1].sum():,}"
              f"  -> recall pos = {cm[1,1]/cm[1].sum():.4f}")
    print(f"\nDisimpan: docs/figures/gambar-06-confusion-matrix.png")

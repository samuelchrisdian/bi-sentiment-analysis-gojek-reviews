"""Visualisasi komparasi model (Fase 3, T-3.9)."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import load_config

CFG = load_config()
ROOT = CFG["_root"]
FIG = ROOT / "docs" / "figures"
BASELINE = CFG["evaluation"]["majority_baseline"]
NAMA = {"complement_nb": "ComplementNB", "multinomial_nb": "MultinomialNB",
        "linear_svc": "LinearSVC", "logistic_regression": "LogisticRegression"}


def _muat() -> pd.DataFrame:
    d = pd.read_csv(ROOT / "docs" / "tables" / "model_metrics.csv")
    return d[d.dedup_training & (d.model_name != "majority_baseline")].copy()


def _simpan(fig, stem: str) -> None:
    for dpi, suf in ((150, ""), (300, "@300")):
        fig.savefig(FIG / f"{stem}{suf}.png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def gambar_10_perbandingan() -> pd.DataFrame:
    """macro-F1 per model x set evaluasi, dengan garis baseline."""
    d = _muat()
    piv = d.pivot(index="model_name", columns="eval_set", values="macro_f1")
    piv = piv.loc[[m for m in NAMA if m in piv.index]]
    x = np.arange(len(piv)); w = 0.38
    base_f1 = pd.read_csv(ROOT / "docs" / "tables" / "model_metrics.csv")
    base_f1 = base_f1[(base_f1.model_name == "majority_baseline") &
                      (base_f1.eval_set == "full") & base_f1.dedup_training].macro_f1.iloc[0]

    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    ax.bar(x - w/2, piv["full"], w, label="full", color="#4C78A8")
    ax.bar(x + w/2, piv["informative_ge5w"], w, label="informative_ge5w (≥5 kata)",
           color="#F58518")
    for i, (a, b) in enumerate(zip(piv["full"], piv["informative_ge5w"])):
        ax.text(i - w/2, a + .006, f"{a:.3f}", ha="center", fontsize=8)
        ax.text(i + w/2, b + .006, f"{b:.3f}", ha="center", fontsize=8)
    ax.axhline(base_f1, color="#E45756", ls="--", lw=1.4)
    ax.text(len(piv) - .55, base_f1 + .012,
            f"baseline mayoritas = {base_f1:.3f}", color="#E45756", fontsize=8.5)
    ax.set_xticks(x); ax.set_xticklabels([NAMA[m] for m in piv.index], fontsize=9)
    ax.set_ylabel("macro-F1"); ax.set_ylim(0.38, 1.0)
    ax.set_title("Gambar 10 — Perbandingan model pada dua set evaluasi")
    ax.legend(fontsize=8.5, loc="lower right"); ax.spines[["top", "right"]].set_visible(False)
    _simpan(fig, "gambar-10-perbandingan-model")
    return piv


def gambar_11_selisih() -> pd.DataFrame:
    """Selisih macro-F1 full - informative_ge5w: temuan metodologis utama.

    Semakin besar selisihnya, semakin besar porsi 'keberhasilan' model yang
    bertumpu pada kata pujian pendek yang berulang, bukan pada pemahaman
    sentimen.
    """
    d = _muat()
    piv = d.pivot(index="model_name", columns="eval_set", values="macro_f1")
    piv["selisih"] = piv["full"] - piv["informative_ge5w"]
    piv = piv.loc[[m for m in NAMA if m in piv.index]].sort_values("selisih")

    fig, ax = plt.subplots(figsize=(8, 3.8))
    warna = ["#54A24B" if v < .02 else "#F58518" if v < .03 else "#E45756"
             for v in piv["selisih"]]
    ax.barh([NAMA[m] for m in piv.index], piv["selisih"] * 100, color=warna)
    for i, v in enumerate(piv["selisih"] * 100):
        ax.text(v + .04, i, f"{v:.2f} poin", va="center", fontsize=9)
    ax.set_xlabel("Penurunan macro-F1 dari set `full` ke `informative_ge5w` (poin)")
    ax.set_xlim(0, max(piv["selisih"] * 100) * 1.3)
    ax.set_title("Gambar 11 — Seberapa besar kinerja bertumpu pada ulasan pendek")
    ax.spines[["top", "right"]].set_visible(False)
    _simpan(fig, "gambar-11-selisih-evaluasi")
    return piv


def gambar_12_waktu() -> pd.DataFrame:
    d = _muat()
    t = d[d.eval_set == "full"].set_index("model_name")[["train_seconds", "predict_seconds"]]
    t = t.loc[[m for m in NAMA if m in t.index]]
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.barh([NAMA[m] for m in t.index], t["train_seconds"], color="#72B7B2")
    for i, v in enumerate(t["train_seconds"]):
        ax.text(v * 1.05, i, f"{v:.3f} s", va="center", fontsize=9)
    ax.set_xscale("log"); ax.set_xlabel("Waktu latih (detik, skala log)")
    ax.set_title("Gambar 12 — Waktu pelatihan (time.perf_counter)")
    ax.spines[["top", "right"]].set_visible(False)
    _simpan(fig, "gambar-12-waktu-latih")
    return t


def semua() -> dict[str, pd.DataFrame]:
    return {"perbandingan": gambar_10_perbandingan(), "selisih": gambar_11_selisih(),
            "waktu": gambar_12_waktu()}


if __name__ == "__main__":
    for k, v in semua().items():
        print(f"\n=== {k} ===\n{v.round(4).to_string()}")

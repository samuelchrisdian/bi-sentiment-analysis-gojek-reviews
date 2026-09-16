"""Analisis eksploratif & kontrak data (Fase 1).

Seluruh angka yang dikutip di laporan dihasilkan di sini. Notebook 01_eda.ipynb
memanggil fungsi-fungsi modul ini agar angka notebook dan angka script identik.
Setiap fungsi mengembalikan DataFrame dan menuliskannya ke docs/tables/.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import load_config, resolve
from .ingest import derive_versi_minor, derive_word_count, load_raw, sha256_of_raw

CFG = load_config()
ROOT: Path = CFG["_root"]
TABLES = ROOT / "docs" / "tables"
FIGURES = ROOT / "docs" / "figures"
TABLES.mkdir(parents=True, exist_ok=True)
FIGURES.mkdir(parents=True, exist_ok=True)

FACTS: dict[str, object] = {}


def _save(df: pd.DataFrame, name: str) -> pd.DataFrame:
    df.to_csv(TABLES / name, index=False)
    return df


def _fact(label: str, nilai, satuan: str, kalimat: str) -> None:
    FACTS[label] = {"nilai": nilai, "satuan": satuan, "kalimat_siap_tempel": kalimat}


def _savefig(fig, stem: str) -> None:
    for dpi, suffix in ((150, ""), (300, "@300")):
        fig.savefig(FIGURES / f"{stem}{suffix}.png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- prepare ---
def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Kolom turunan untuk EDA (tanpa preprocessing teks — itu Fase 2)."""
    df = df.copy()
    df["versi_minor"] = derive_versi_minor(df["Versi App"])
    df["word_count"] = derive_word_count(df["Ulasan"])
    df["bulan"] = df["Tanggal"].dt.to_period("M")
    neg, pos = CFG["labeling"]["negative_ratings"], CFG["labeling"]["positive_ratings"]
    df["sentimen_aktual"] = np.where(
        df["Rating"].isin(neg), 0, np.where(df["Rating"].isin(pos), 1, np.nan)
    )
    return df


# ------------------------------------------------------------ 2. profil ---
def profil_dataset(df: pd.DataFrame) -> pd.DataFrame:
    n_rows, n_cols = df.shape
    miss = df[CFG["schema"]["expected_columns"]].isna().sum()
    rows = [
        ("Jumlah baris", f"{n_rows:,}"),
        ("Jumlah kolom", str(n_cols)),
        ("Periode awal", str(df["Tanggal"].min().date())),
        ("Periode akhir", str(df["Tanggal"].max().date())),
        ("Jumlah bulan", str(df["bulan"].nunique())),
        ("SHA-256 berkas", sha256_of_raw(CFG)),
    ] + [(f"Missing · {c}", f"{int(v):,}") for c, v in miss.items()]
    _fact("A-01", n_rows, "baris", f"{n_rows:,} ulasan")
    _fact("A-02", int(miss['Versi App']), "baris",
          f"{int(miss['Versi App']):,} baris ({miss['Versi App'] / n_rows * 100:.1f}%) tidak mencantumkan versi aplikasi")
    return _save(pd.DataFrame(rows, columns=["properti", "nilai"]), "profil_dataset.csv")


def duplikasi(df: pd.DataFrame) -> pd.DataFrame:
    dup_full = int(df.duplicated().sum())
    dup_teks = int(df["Ulasan"].duplicated().sum())
    n = len(df)
    _fact("A-03", dup_teks, "baris",
          f"{dup_teks:,} ulasan ({dup_teks / n * 100:.1f}%) merupakan duplikat teks")
    out = pd.DataFrame(
        [("Duplikat baris penuh", dup_full, dup_full / n * 100),
         ("Duplikat teks Ulasan", dup_teks, dup_teks / n * 100)],
        columns=["jenis", "jumlah", "persen"])
    return _save(out, "duplikasi.csv")


def distribusi_rating(df: pd.DataFrame) -> pd.DataFrame:
    vc = df["Rating"].value_counts().sort_index()
    out = pd.DataFrame({"rating": vc.index, "jumlah": vc.values,
                        "persen": (vc.values / len(df) * 100).round(1)})
    for r, j, p in out.itertuples(index=False):
        _fact(f"A-1{r}", int(j), "ulasan", f"bintang {r}: {j:,} ulasan ({p}%)")
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(out["rating"], out["jumlah"], color="#4C78A8")
    for b, p in zip(bars, out["persen"]):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{p}%",
                ha="center", va="bottom", fontsize=9)
    ax.set_xlabel("Rating (bintang)"); ax.set_ylabel("Jumlah ulasan")
    ax.set_title(f"Gambar 1 — Distribusi rating (n={len(df):,})")
    ax.spines[["top", "right"]].set_visible(False)
    _savefig(fig, "gambar-01-distribusi-rating")
    return _save(out, "distribusi_rating.csv")


# -------------------------------------------- 5-6. asimetri panjang teks ---
def panjang_per_rating(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("Rating")["word_count"]
    out = pd.DataFrame({"rating": g.mean().index,
                        "rata_kata": g.mean().round(1).values,
                        "median_kata": g.median().values,
                        "jumlah": g.size().values})
    _fact("A-20", float(out.loc[out.rating == 5, "rata_kata"].iloc[0]), "kata",
          f"ulasan bintang 5 rata-rata hanya {out.loc[out.rating == 5, 'rata_kata'].iloc[0]} kata, "
          f"sementara bintang 1 mencapai {out.loc[out.rating == 1, 'rata_kata'].iloc[0]} kata")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(out["rating"], out["rata_kata"], color="#E45756")
    for r, v in zip(out["rating"], out["rata_kata"]):
        ax.text(v + 0.3, r, f"{v}", va="center", fontsize=9)
    ax.set_xlabel("Rata-rata jumlah kata"); ax.set_ylabel("Rating (bintang)")
    ax.set_title("Gambar 2 — Asimetri panjang ulasan antar kelas")
    ax.spines[["top", "right"]].set_visible(False)
    _savefig(fig, "gambar-02-panjang-per-rating")
    return _save(out, "panjang_per_rating.csv")


def ulasan_pendek(df: pd.DataFrame) -> pd.DataFrame:
    n = len(df)
    le2 = int((df["word_count"] <= 2).sum())
    _fact("A-21", le2, "ulasan",
          f"{le2:,} ulasan ({le2 / n * 100:.1f}%) hanya berisi dua kata atau kurang")
    top = (df["Ulasan"].value_counts().head(20).rename_axis("teks")
           .reset_index(name="frekuensi"))
    _save(top, "teks_paling_berulang.csv")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(df["word_count"].clip(upper=100), bins=50, color="#54A24B")
    ax.set_yscale("log")
    for x, lab in ((2, "≤2 kata"), (5, "ambang informatif")):
        ax.axvline(x, color="#E45756", ls="--", lw=1)
        ax.text(x + 1, ax.get_ylim()[1] * 0.4, lab, fontsize=8, color="#E45756")
    ax.set_xlabel("Jumlah kata (dipotong di 100)"); ax.set_ylabel("Frekuensi (log)")
    ax.set_title("Gambar 3 — Distribusi panjang ulasan")
    ax.spines[["top", "right"]].set_visible(False)
    _savefig(fig, "gambar-03-distribusi-wordcount")
    out = pd.DataFrame([("≤2 kata", le2, le2 / n * 100),
                        ("≥5 kata (informatif)", int((df["word_count"] >= 5).sum()),
                         float((df["word_count"] >= 5).mean() * 100))],
                       columns=["kelompok", "jumlah", "persen"])
    return _save(out, "ulasan_pendek.csv")


def kontras_kelas(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label, sub in (("Negatif", df[df.sentimen_aktual == 0]),
                       ("Positif", df[df.sentimen_aktual == 1])):
        rows.append((label, len(sub), int(sub["Ulasan"].duplicated().sum()),
                     int((sub["word_count"] <= 2).sum())))
    out = pd.DataFrame(rows, columns=["kelas", "jumlah", "duplikat_teks", "ulasan_le2kata"])
    out["persen_duplikat"] = (out.duplikat_teks / out.jumlah * 100).round(1)
    out["persen_le2kata"] = (out.ulasan_le2kata / out.jumlah * 100).round(1)
    neg = out[out.kelas == "Negatif"].iloc[0]
    _fact("A-22", int(neg.duplikat_teks), "ulasan",
          f"pada kelas negatif hanya {neg.persen_duplikat}% ulasan yang merupakan duplikat teks, "
          f"dibanding {out[out.kelas == 'Positif'].iloc[0].persen_duplikat}% pada kelas positif")
    return _save(out, "kontras_kelas.csv")


# --------------------------------------------------- 7. kelayakan kelas ---
def komposisi_kelas(df: pd.DataFrame) -> pd.DataFrame:
    n_neg = int((df.sentimen_aktual == 0).sum())
    n_pos = int((df.sentimen_aktual == 1).sum())
    n_net = int(df.sentimen_aktual.isna().sum())
    n = len(df)
    rows = [("3 kelas", "Negatif", n_neg, n_neg / n * 100),
            ("3 kelas", "Netral", n_net, n_net / n * 100),
            ("3 kelas", "Positif", n_pos, n_pos / n * 100),
            ("Biner", "Negatif", n_neg, n_neg / (n_neg + n_pos) * 100),
            ("Biner", "Positif", n_pos, n_pos / (n_neg + n_pos) * 100)]
    out = pd.DataFrame(rows, columns=["skema", "kelas", "jumlah", "persen"])
    out["persen"] = out["persen"].round(2)
    base = n_pos / (n_neg + n_pos) * 100
    _fact("A-23", round(base, 1), "%",
          f"baseline mayoritas pada skema biner adalah {base:.1f}% — angka yang harus dikalahkan model")
    _fact("A-24", n_net, "ulasan",
          f"kelas netral hanya {n_net:,} ulasan ({n_net / n * 100:.1f}%), rasio 1:{n_pos // n_net} terhadap kelas positif")
    return _save(out, "komposisi_kelas.csv")


# ------------------------------------------------------- 8. analisis versi ---
def cakupan_versi(df: pd.DataFrame) -> pd.DataFrame:
    berversi = df[df["Versi App"].notna()]
    vc = berversi["Versi App"].value_counts()
    rows = []
    for amb in (30, 100, 200, 500):
        keep = vc[vc >= amb]
        rows.append((amb, len(keep), int(keep.sum()),
                     keep.sum() / len(berversi) * 100))
    out = pd.DataFrame(rows, columns=["ambang", "jumlah_versi", "ulasan_tercakup",
                                      "persen_cakupan_berversi"])
    out["persen_cakupan_berversi"] = out["persen_cakupan_berversi"].round(1)
    _fact("A-30", int(vc.size), "versi", f"terdapat {vc.size} versi aplikasi unik")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(out["ambang"].astype(str), out["persen_cakupan_berversi"], color="#72B7B2")
    for i, (v, c) in enumerate(zip(out["jumlah_versi"], out["persen_cakupan_berversi"])):
        ax.text(i, c, f"{c}%\n({v} versi)", ha="center", va="bottom", fontsize=8)
    ax.set_ylim(0, 112)
    ax.set_xlabel("Ambang minimum ulasan per versi"); ax.set_ylabel("Cakupan data berversi (%)")
    ax.set_title("Gambar 5 — Cakupan data per ambang versi")
    ax.spines[["top", "right"]].set_visible(False)
    _savefig(fig, "gambar-05-cakupan-versi")
    return _save(out, "cakupan_versi.csv")


# ---------------------------------------------------------- 9-10. lain ---
def profil_likes(df: pd.DataFrame) -> pd.DataFrame:
    d = df["Likes"].describe()
    out = (d.rename_axis("statistik").reset_index(name="nilai"))
    out.loc[len(out)] = ["persen_likes_nol", float((df["Likes"] == 0).mean() * 100)]
    _fact("A-40", float((df["Likes"] == 0).mean() * 100), "%",
          f"{(df['Likes'] == 0).mean() * 100:.1f}% ulasan tidak pernah mendapat satu pun like")
    return _save(out, "profil_likes.csv")


def volume_bulanan(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("bulan")
    out = pd.DataFrame({"bulan": g.size().index.astype(str), "jumlah": g.size().values,
                        "rata_rating": g["Rating"].mean().round(2).values})
    out["periode_parsial"] = out["bulan"] == CFG["temporal"]["partial_month"]
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(out["bulan"], out["jumlah"], marker="o", color="#4C78A8")
    if out["periode_parsial"].any():
        ax.axvspan(-0.4, 0.4, color="#E45756", alpha=0.15)
        ax.text(0.5, out["jumlah"].max() * 0.95, "Mei 2024 — periode parsial\n(mulai 21 Mei)",
                fontsize=8, color="#E45756")
    ax.set_xticks(range(len(out)))
    ax.set_xticklabels(out["bulan"], rotation=60, ha="right", fontsize=8)
    ax.set_ylabel("Jumlah ulasan"); ax.set_title("Gambar 4 — Volume ulasan per bulan")
    ax.spines[["top", "right"]].set_visible(False)
    _savefig(fig, "gambar-04-volume-bulanan")
    return _save(out, "volume_bulanan.csv")


# ------------------------------------------------------------- pipeline ---
def run_all() -> dict[str, pd.DataFrame]:
    df = prepare(load_raw(CFG))
    hasil = {
        "profil_dataset": profil_dataset(df), "duplikasi": duplikasi(df),
        "distribusi_rating": distribusi_rating(df), "panjang_per_rating": panjang_per_rating(df),
        "ulasan_pendek": ulasan_pendek(df), "kontras_kelas": kontras_kelas(df),
        "komposisi_kelas": komposisi_kelas(df), "cakupan_versi": cakupan_versi(df),
        "profil_likes": profil_likes(df), "volume_bulanan": volume_bulanan(df),
    }
    angka = pd.DataFrame(
        [{"label": k, **v} for k, v in sorted(FACTS.items())])  # type: ignore[arg-type]
    angka["sumber_sel_notebook"] = "ml/src/eda.py :: run_all()"
    _save(angka, "angka_storytelling.csv")
    hasil["angka_storytelling"] = angka
    return hasil


if __name__ == "__main__":
    for nama, tabel in run_all().items():
        print(f"\n=== {nama} ===")
        print(tabel.to_string(index=False, max_colwidth=60))

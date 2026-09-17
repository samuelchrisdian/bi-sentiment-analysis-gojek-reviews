"""Analisis kesalahan (Fase 4, T-4.4) — GERBANG H-7.

Modul ini menghasilkan berkas kerja untuk pemeriksaan manusia dan menghitung
statistik kesalahan yang bersifat mekanis. Kolom `kategori_penyebab` sengaja
dibiarkan KOSONG.

Alasannya bukan formalitas: menilai apakah sebuah ulasan sarkastik, atau apakah
bintang yang diberikan pengguna bertentangan dengan isi tulisannya, adalah
penilaian manusia terhadap bahasa dan konteks. Kategori yang ditebak agent
menghasilkan subbab pembahasan yang tidak bisa dipertahankan penulisnya saat
diuji. `hitung_distribusi()` baru dijalankan setelah berkas dikembalikan terisi.
"""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd

from .config import load_config
from .dataset import siapkan_teks

CFG = load_config()
ROOT = CFG["_root"]
SEED = CFG["seed"]
N_SAMPEL = 50
MODEL_DIPERIKSA = "linear_svc"          # macro-F1 tertinggi setelah tuning

TAKSONOMI = [
    "sarkasme_ironi",
    "negasi_kompleks",
    "campur_kode",
    "label_keliru_pengguna",
    "terlalu_pendek_ambigu",
    "topik_netral_offtopic",
    "kegagalan_preprocessing",
]

KOLOM = ["id", "ulasan", "ulasan_clean", "rating", "word_count",
         "label_aktual", "prediksi", "arah_kesalahan", "skor_keputusan",
         "jarak_ke_batas", "kategori_penyebab", "catatan"]


def _prediksi(nama: str, d: dict):
    pipe = joblib.load(ROOT / "ml" / "artifacts" / f"tuned_{nama}.joblib")
    pred = pipe.predict(d["X_te"])
    clf = pipe.named_steps["clf"]
    skor = (clf.decision_function(pipe.named_steps["tfidf"].transform(d["X_te"]))
            if hasattr(clf, "decision_function") else None)
    return pred, skor


def bangun_berkas_kerja() -> tuple[pd.DataFrame, pd.DataFrame]:
    d = siapkan_teks(dedup=CFG["preprocessing"]["dedup_training_text"])
    pred, skor = _prediksi(MODEL_DIPERIKSA, d)
    salah = pred != d["y_te"]

    df = d["df"].loc[d["idx_te"], ["id", "ulasan", "ulasan_clean", "rating",
                                   "word_count"]].copy()
    df["label_aktual"] = d["y_te"]
    df["prediksi"] = pred
    df["skor_keputusan"] = skor                    # >0 -> positif, <0 -> negatif
    df["jarak_ke_batas"] = np.abs(skor)            # kecil = model ragu
    df["arah_kesalahan"] = np.where(
        (df.label_aktual == 0) & (df.prediksi == 1), "negatif_lolos_sebagai_positif",
        np.where((df.label_aktual == 1) & (df.prediksi == 0),
                 "positif_salah_ditandai_negatif", "benar"))

    err = df[salah].copy()
    sampel = err.sample(N_SAMPEL, random_state=SEED).sort_values("jarak_ke_batas")
    sampel["kategori_penyebab"] = ""               # DIISI MANUSIA — lihat H-7
    sampel["catatan"] = ""
    return err, sampel[KOLOM]


def profil_kesalahan(err: pd.DataFrame, n_test: int) -> pd.DataFrame:
    """Statistik yang murni mekanis — tidak menyentuh penyebab."""
    tot = len(err)
    rows = [("total kesalahan", tot, f"{tot/n_test:.2%} dari {n_test:,} baris test")]
    for arah, g in err.groupby("arah_kesalahan"):
        rows.append((arah, len(g), f"{len(g)/tot:.1%} dari seluruh kesalahan"))
    for lo, hi, nama in ((0, 2, "<=2 kata"), (3, 4, "3-4 kata"), (5, 19, "5-19 kata"),
                         (20, 10**6, ">=20 kata")):
        n = ((err.word_count >= lo) & (err.word_count <= hi)).sum()
        rows.append((f"panjang {nama}", int(n), f"{n/tot:.1%}"))
    for r in sorted(err.rating.unique()):
        n = int((err.rating == r).sum())
        rows.append((f"rating {r}", n, f"{n/tot:.1%}"))
    ragu = int((err.jarak_ke_batas < 0.5).sum())
    rows.append(("jarak ke batas < 0,5 (model ragu)", ragu, f"{ragu/tot:.1%}"))
    return pd.DataFrame(rows, columns=["properti", "n", "keterangan"])


def tumpang_tindih_model() -> pd.DataFrame:
    """Apakah keempat model salah pada baris yang sama?

    Bila tumpang tindihnya tinggi, taksonomi penyebab yang disusun dari
    kesalahan satu model berlaku juga untuk model lain — sehingga keputusan
    H-10 tidak membatalkan hasil pemeriksaan manual ini.
    """
    d = siapkan_teks(dedup=CFG["preprocessing"]["dedup_training_text"])
    salah = {}
    for nama in ("linear_svc", "logistic_regression", "complement_nb", "multinomial_nb"):
        pred, _ = _prediksi(nama, d)
        salah[nama] = pred != d["y_te"]
    nama_model = list(salah)
    m = pd.DataFrame(index=nama_model, columns=nama_model, dtype=float)
    for a in nama_model:
        for b in nama_model:
            inter = (salah[a] & salah[b]).sum()
            union = (salah[a] | salah[b]).sum()
            m.loc[a, b] = inter / union            # Jaccard
    m["n_salah"] = [int(salah[a].sum()) for a in nama_model]
    return m.round(3)


def hitung_distribusi(path=None) -> pd.DataFrame:
    """Dijalankan SETELAH berkas dikembalikan manusia dengan kategori terisi."""
    path = path or ROOT / "docs" / "tables" / "error_analysis_50.csv"
    df = pd.read_csv(path)
    kosong = df.kategori_penyebab.isna() | (df.kategori_penyebab.astype(str).str.strip() == "")
    if kosong.any():
        raise RuntimeError(
            f"GERBANG H-7 belum dilewati: {int(kosong.sum())} dari {len(df)} baris "
            "masih kosong pada kolom `kategori_penyebab`.")
    tak_dikenal = set(df.kategori_penyebab.str.strip()) - set(TAKSONOMI)
    if tak_dikenal:
        raise RuntimeError(f"Kategori di luar taksonomi: {sorted(tak_dikenal)}")
    t = (df.kategori_penyebab.str.strip().value_counts()
           .rename_axis("kategori").reset_index(name="n"))
    t["persen"] = (t.n / len(df) * 100).round(1)
    return t


if __name__ == "__main__":
    err, sampel = bangun_berkas_kerja()
    d_n_test = 19294
    p = ROOT / "docs" / "tables" / "error_analysis_50.csv"
    sampel.to_csv(p, index=False)

    print(f"Model diperiksa : {MODEL_DIPERIKSA}_tuned")
    print(f"Disimpan        : {p.relative_to(ROOT)} "
          f"({len(sampel)} baris, kolom `kategori_penyebab` KOSONG)\n")
    print("Profil kesalahan (mekanis, bukan penyebab):")
    print(profil_kesalahan(err, d_n_test).to_string(index=False))
    print("\nTumpang tindih kesalahan antar model (Jaccard):")
    print(tumpang_tindih_model().to_string())
    print("\nTaksonomi yang tersedia untuk kolom `kategori_penyebab`:")
    for t in TAKSONOMI:
        print(f"  - {t}")

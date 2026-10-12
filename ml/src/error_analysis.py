"""Analisis kesalahan manual (Fase 4).

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
from .dataset import FASE3, siapkan_teks

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
    sampel["kategori_penyebab"] = ""               # DIISI MANUSIA
    sampel["catatan"] = ""
    return err, sampel[KOLOM]


def pertahankan_label(err: pd.DataFrame, sampel: pd.DataFrame,
                      lama: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Pertahankan sampel yang sudah dilabeli manusia saat pipeline dijalankan ulang.

    Ulasan pada `lama` yang MASIH salah diprediksi model baru tetap dipakai
    beserta label penyebabnya. Yang kini diprediksi benar diganti kesalahan
    acak baru (random_state sama) dengan kolom `kategori_penyebab` kosong.
    Mengembalikan sampel gabungan dan jumlah baris pengganti.
    """
    lama = lama.set_index("id")
    tetap = err[err["id"].isin(lama.index)].copy()
    tetap["kategori_penyebab"] = tetap["id"].map(lama["kategori_penyebab"]).fillna("")
    tetap["catatan"] = tetap["id"].map(lama["catatan"]).fillna("")
    n_ganti = N_SAMPEL - len(tetap)
    pengganti = (err[~err["id"].isin(lama.index)]
                 .sample(n_ganti, random_state=SEED)
                 .assign(kategori_penyebab="", catatan=""))
    gabung = pd.concat([tetap, pengganti]).sort_values("jarak_ke_batas")
    return gabung[KOLOM], n_ganti


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
    model produksi tidak membatalkan hasil pemeriksaan manual ini.
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
            f"Analisis kesalahan manual belum lengkap: {int(kosong.sum())} dari {len(df)} baris "
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
    d_n_test = FASE3["n_test"]
    p = ROOT / "docs" / "tables" / "error_analysis_50.csv"
    p_rev = p.with_name("error_analysis_50_reviewed.csv")
    if p_rev.exists():
        # Label manusia dari run sebelumnya dipertahankan (lihat pertahankan_label).
        sampel, n_ganti = pertahankan_label(err, sampel, pd.read_csv(p_rev, keep_default_na=False))
        sampel.to_csv(p, index=False)
        if n_ganti == 0:
            sampel.to_csv(p_rev, index=False)
        else:
            p_rev.rename(p_rev.with_name("error_analysis_50_reviewed_sebelumnya.csv"))
        print(f"Label dipertahankan: {N_SAMPEL - n_ganti}; baris pengganti yang perlu "
              f"dilabeli: {n_ganti}")
    else:
        sampel.to_csv(p, index=False)

    print(f"Model diperiksa : {MODEL_DIPERIKSA}_tuned")
    print(f"Disimpan        : {p.relative_to(ROOT)} ({len(sampel)} baris)\n")
    print("Profil kesalahan (mekanis, bukan penyebab):")
    print(profil_kesalahan(err, d_n_test).to_string(index=False))
    print("\nTumpang tindih kesalahan antar model (Jaccard):")
    print(tumpang_tindih_model().to_string())
    print("\nTaksonomi yang tersedia untuk kolom `kategori_penyebab`:")
    for t in TAKSONOMI:
        print(f"  - {t}")

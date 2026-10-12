"""Uji pola sentimen per versi aplikasi untuk RM3 (Bab III 3.6.7).

- Uji homogenitas chi-kuadrat proporsi negatif antarversi.
- Penandaan rilis: versi v ditandai bila naik >= min_kenaikan_pp poin dari
  versi sebelumnya (urut nomor versi) DAN uji z satu sisi lolos BH q < alpha_q.
- Tiga pemeriksaan kelayakan: ulang dengan label rating, keselarasan pekanan
  di sekitar tanggal ulasan pertama, dan komposisi kategori keluhan.

Label utama adalah prediksi model produksi; label rating menjadi pembanding.

    python -m ml.src.rm3
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, norm

from .config import load_config, resolve

CFG = load_config()
ROOT = CFG["_root"]
TAB = ROOT / "docs" / "tables"
R = CFG["rm3"]
MIN_N = CFG["versions"]["min_reviews_per_version"]
MODEL_PRODUKSI = "logistic_regression_final"


def kunci_versi(v: str) -> tuple[int, ...]:
    # Urut numerik: 4.9 sebelum 4.10.
    return tuple(int(x) for x in str(v).split("."))


def bh(p: np.ndarray) -> np.ndarray:
    """Nilai q Benjamini–Hochberg."""
    n = len(p)
    urut = np.argsort(p)
    q = p[urut] * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(q[::-1])[::-1].clip(max=1)
    out = np.empty(n)
    out[urut] = q
    return out


def muat() -> pd.DataFrame:
    rev = pd.read_parquet(resolve(CFG, "paths.clean_parquet"),
                          columns=["id", "tanggal", "versi_minor", "sentimen_aktual"])
    sk = pd.read_parquet(resolve(CFG, "paths.processed_dir") / "review_scores.parquet")
    sk = sk.loc[sk["model_name"] == MODEL_PRODUKSI, ["review_id", "pred_label"]]
    d = rev.merge(sk, left_on="id", right_on="review_id", how="inner")
    assert len(d) == len(rev), "skor model produksi tidak lengkap"
    d["tanggal"] = pd.to_datetime(d["tanggal"])
    d["neg_pred"] = d["pred_label"] == 0
    return d


def uji_versi(d: pd.DataFrame, kol_neg: str, label: str) -> tuple[pd.DataFrame, dict]:
    """Chi-kuadrat dan penandaan rilis untuk satu sumber label."""
    g = (d.groupby("versi_minor")
          .agg(n=(kol_neg, "size"), n_neg=(kol_neg, "sum"), pertama_muncul=("tanggal", "min")))
    g = g[g.index.isin(VERSI)].copy()
    g = g.loc[sorted(g.index, key=kunci_versi)]
    g["pct_neg"] = g["n_neg"] / g["n"] * 100

    chi2, p_chi2, dof, _ = chi2_contingency(np.c_[g["n_neg"], g["n"] - g["n_neg"]])

    p1, n1 = g["pct_neg"].to_numpy() / 100, g["n"].to_numpy()
    p0, n0 = np.r_[np.nan, p1[:-1]], np.r_[np.nan, n1[:-1]]
    pool = (g["n_neg"].to_numpy() + np.r_[np.nan, g["n_neg"].to_numpy()[:-1]]) / (n1 + n0)
    z = (p1 - p0) / np.sqrt(pool * (1 - pool) * (1 / n1 + 1 / n0))
    p = norm.sf(z)
    q = np.full(len(g), np.nan)
    q[1:] = bh(p[1:])

    g["selisih_pp"] = (p1 - p0) * 100
    g["z"], g["p"], g["q"] = z, p, q
    g["ditandai"] = (g["selisih_pp"] >= R["min_kenaikan_pp"]) & (g["q"] < R["alpha_q"])
    g["selisih_vs_rerata_pp"] = g["pct_neg"] - g["n_neg"].sum() / g["n"].sum() * 100
    ringkas = {"label": label, "chi2": float(chi2), "dof": int(dof), "p": float(p_chi2),
               "n_versi": int(len(g)), "n_perbandingan": int(len(g) - 1),
               "n_ditandai": int(g["ditandai"].sum())}
    return g.add_suffix(f"_{label}"), ringkas


def keselarasan_pekanan(d: pd.DataFrame, versi: list[str], awal: pd.Series) -> pd.DataFrame:
    """Proporsi negatif seluruh ulasan pada jendela sebelum vs sesudah ulasan pertama versi."""
    w = pd.Timedelta(weeks=R["jendela_pekan"])
    baris = []
    for v in versi:
        t0 = awal[v]
        seb = d[(d["tanggal"] >= t0 - w) & (d["tanggal"] < t0)]["neg_pred"]
        ses = d[(d["tanggal"] >= t0) & (d["tanggal"] < t0 + w)]["neg_pred"]
        pool = (seb.sum() + ses.sum()) / (len(seb) + len(ses))
        z = (ses.mean() - seb.mean()) / np.sqrt(pool * (1 - pool) * (1 / len(seb) + 1 / len(ses)))
        baris.append({"versi": v, "pertama_muncul": t0.date(), "n_sebelum": len(seb),
                      "pct_neg_sebelum": seb.mean() * 100, "n_sesudah": len(ses),
                      "pct_neg_sesudah": ses.mean() * 100,
                      "selisih_pp": (ses.mean() - seb.mean()) * 100, "z": z, "p": norm.sf(z)})
    return pd.DataFrame(baris)


def komposisi_keluhan(d: pd.DataFrame, versi: list[str]) -> pd.DataFrame:
    """Sebaran kategori pada ulasan negatif versi ditandai vs seluruh ulasan negatif berversi."""
    top = pd.read_parquet(resolve(CFG, "paths.processed_dir") / "topics.parquet")
    top = top.drop_duplicates(["review_id", "kategori"])
    neg = d[(d["sentimen_aktual"] == 0) & d["versi_minor"].isin(VERSI)][["id", "versi_minor"]]
    t = top.merge(neg, left_on="review_id", right_on="id")

    def pangsa(ids: pd.Series, x: pd.DataFrame) -> pd.Series:
        return x.groupby("kategori")["review_id"].nunique() / ids.nunique() * 100

    semua = pangsa(neg["id"], t)
    sel = neg[neg["versi_minor"].isin(versi)]
    tandai = pangsa(sel["id"], t[t["versi_minor"].isin(versi)]) if len(sel) else semua * np.nan
    out = pd.DataFrame({"pct_versi_ditandai": tandai, "pct_semua_berversi": semua}).fillna(0)
    out["selisih_pp"] = out["pct_versi_ditandai"] - out["pct_semua_berversi"]
    out.attrs["n_neg_ditandai"], out.attrs["n_neg_berversi"] = len(sel), len(neg)
    return out.sort_values("selisih_pp", ascending=False)


def jalankan() -> dict:
    global VERSI
    d = muat()
    hit = d["versi_minor"].value_counts()
    VERSI = set(hit[hit >= MIN_N].index)

    pred, r_pred = uji_versi(d, "neg_pred", "pred")
    lab = d[d["sentimen_aktual"].notna()].assign(neg_rating=lambda x: x["sentimen_aktual"] == 0)
    rat, r_rat = uji_versi(lab, "neg_rating", "rating")
    tabel = pred.join(rat, how="left")
    tabel.index.name = "versi"

    # Versi yang sudah ada sebelum periode data: tanggal ulasan pertamanya bukan proksi rilis.
    batas = d["tanggal"].min() + pd.Timedelta(weeks=R["jendela_pekan"])
    tabel["tersensor_kiri"] = tabel["pertama_muncul_pred"] < batas

    ditandai = tabel.index[tabel["ditandai_pred"]].tolist()
    keduanya = tabel.index[tabel["ditandai_pred"] & tabel["ditandai_rating"].fillna(False)].tolist()
    selaras = keselarasan_pekanan(d, ditandai, tabel["pertama_muncul_pred"])
    kompos = komposisi_keluhan(d, ditandai)
    return {"tabel": tabel, "ringkas": [r_pred, r_rat], "ditandai": ditandai,
            "keduanya": keduanya, "selaras": selaras, "kompos": kompos}


VERSI: set[str] = set()


if __name__ == "__main__":
    h = jalankan()
    t = h["tabel"].reset_index()
    t.to_csv(TAB / "rm3_uji_versi.csv", index=False, float_format="%.6g")
    h["selaras"].to_csv(TAB / "rm3_keselarasan_pekanan.csv", index=False, float_format="%.6g")
    h["kompos"].rename_axis("kategori").reset_index().to_csv(
        TAB / "rm3_komposisi_keluhan.csv", index=False, float_format="%.4f")
    for r in h["ringkas"]:
        print(f"[{r['label']}] chi2={r['chi2']:.1f} dof={r['dof']} p={r['p']:.3g} · "
              f"{r['n_perbandingan']} perbandingan · ditandai {r['n_ditandai']}")
    print(f"ditandai (prediksi): {h['ditandai']}")
    print(f"ditandai pada kedua label: {h['keduanya']}")
    print(h["selaras"].round(2).to_string(index=False))
    print(h["kompos"].round(2).to_string())
    print("Disimpan: docs/tables/rm3_{uji_versi,keselarasan_pekanan,komposisi_keluhan}.csv")

"""Fitur paling berpengaruh per kelas (Fase 4, T-4.5).

Tujuannya bukan sekadar menampilkan daftar kata, melainkan menguji pipeline
Fase 2: bila yang muncul adalah istilah domain (`gagal`, `saldo`, `potong`),
model mempelajari sentimen; bila yang muncul adalah artefak (nama orang, sisa
tanda baca, stopword yang lolos, potongan stemming yang salah), pipeline
preprocessing yang perlu diperbaiki — bukan model yang perlu diganti.

Model linear dan Naive Bayes memakai skala bobot yang berbeda dan TIDAK boleh
dibandingkan angkanya lintas model; yang dibandingkan adalah daftar katanya.
"""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd

from .config import load_config

CFG = load_config()
ROOT = CFG["_root"]
TOP_N = 20
MODEL = ["linear_svc", "logistic_regression", "complement_nb", "multinomial_nb"]


def bobot_per_kelas(nama: str):
    """-> (fitur, skor) dengan skor tinggi = indikatif kelas NEGATIF."""
    pipe = joblib.load(ROOT / "ml" / "artifacts" / f"tuned_{nama}.joblib")
    fitur = np.array(pipe.named_steps["tfidf"].get_feature_names_out())
    clf = pipe.named_steps["clf"]

    if hasattr(clf, "coef_"):
        # coef_ positif -> mendorong ke kelas 1 (positif). Dibalik tandanya agar
        # konvensinya sama dengan cabang Naive Bayes di bawah.
        return fitur, -clf.coef_[0]

    # ComplementNB (norm=False) menyimpan feature_log_prob_ sudah dinegasikan
    # sklearn sehingga "lebih besar = lebih indikatif", sama seperti
    # MultinomialNB. Selisih baris 0 - baris 1 = log-ratio ke arah negatif.
    return fitur, clf.feature_log_prob_[0] - clf.feature_log_prob_[1]


def tabel_top() -> pd.DataFrame:
    baris = []
    for nama in MODEL:
        fitur, skor = bobot_per_kelas(nama)
        urut = np.argsort(skor)
        for kelas, idx in (("negatif", urut[::-1][:TOP_N]), ("positif", urut[:TOP_N])):
            for r, i in enumerate(idx, 1):
                baris.append({"model": nama, "kelas": kelas, "rank": r,
                              "fitur": fitur[i], "bobot": float(skor[i])})
    return pd.DataFrame(baris)


def audit_artefak(df: pd.DataFrame) -> pd.DataFrame:
    """Hitung indikator artefak yang dapat diperiksa secara mekanis.

    Ini TIDAK menjawab 'masuk akal secara domain?' — itu penilaian bahasa yang
    ditulis manusia di docs/error_analysis.md. Yang dihitung di sini hanya hal
    yang objektif: token satu huruf, token berangka, dan sisa tanda baca.
    """
    u = df.copy()
    tok = u.fitur.str.split()                      # bigram -> dua token
    u["n_gram"] = tok.str.len()
    u["ada_digit"] = u.fitur.str.contains(r"\d", regex=True)
    u["ada_nonalnum"] = u.fitur.str.contains(r"[^a-z0-9 ]", regex=True)
    u["token_1huruf"] = tok.apply(lambda t: any(len(x) == 1 for x in t))
    return (u.groupby(["model", "kelas"])[["ada_digit", "ada_nonalnum", "token_1huruf"]]
              .sum().astype(int).reset_index())


if __name__ == "__main__":
    df = tabel_top()
    p = ROOT / "docs" / "tables" / "top_features.csv"
    df.to_csv(p, index=False)
    print(f"Disimpan: {p.relative_to(ROOT)} ({len(df)} baris = "
          f"{len(MODEL)} model x 2 kelas x {TOP_N})\n")

    for nama in MODEL:
        d = df[df.model == nama]
        neg = d[d.kelas == "negatif"].fitur.tolist()
        pos = d[d.kelas == "positif"].fitur.tolist()
        print(f"=== {nama}")
        print(f"  NEGATIF: {', '.join(neg)}")
        print(f"  POSITIF: {', '.join(pos)}\n")

    print("Audit artefak mekanis (jumlah dari 20 fitur):")
    print(audit_artefak(df).to_string(index=False))

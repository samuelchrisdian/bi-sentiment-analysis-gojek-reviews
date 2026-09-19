"""Skoring seluruh 100.000 baris dengan lima model (Fase 6, T-6.1).

Diskor SELURUH baris, termasuk rating 3 yang dikeluarkan dari pelatihan
(`sentimen_aktual` NULL) — dashboard perlu menampilkan prediksi untuk semua
ulasan, dan ke arah mana model mengklasifikasikan ulasan bintang 3 justru
menarik untuk dilaporkan.

Lima baris `model_name` ditulis ke `review_scores`, bukan dua seperti draf
awal rencana Fase 6: gerbang H-10 (`docs/model_decision.md`) menjadikan
LogisticRegression `C=1.0` model produksi, mengangkat perbandingan dari dua
model menjadi "tiga keluarga algoritma, empat varian" (§5.3). Kelima baris:

    complement_nb_tuned        \\  keempat varian GridSearchCV Fase 4 —
    multinomial_nb_tuned        \\ tiap Pipeline (`tuned_*.joblib`) membawa
    linear_svc_tuned            /  vectorizer TF-IDF sendiri, HASIL fold-nya
    logistic_regression_tuned  /   sendiri, bukan `vectorizer.joblib`.
    logistic_regression_final  --  model produksi (Fase 4 T-4.7): clf terpisah
                                    dari vectorizer, dipasangkan manual di sini.

`logistic_regression_tuned` (C=5.0, pemenang GridSearchCV) dan
`logistic_regression_final` (C=1.0, aturan 1-SE) SENGAJA dibedakan meski satu
keluarga algoritma — parameternya beda dan keduanya baris yang sah untuk
dibandingkan di dashboard.

`linear_svc_tuned` tidak dikalibrasi (`PERLU_KALIBRASI` di `finalize.py` hanya
berlaku untuk model produksi), sehingga `pred_proba`-nya NULL — `LinearSVC`
tidak punya `predict_proba` bawaan.
"""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd

from .config import load_config, resolve

CFG = load_config()
ROOT = CFG["_root"]
ART = ROOT / "ml" / "artifacts"

# (model_name, path artefak, "pipeline" jika vectorizer ada di dalamnya,
#  "clf_terpisah" jika perlu dipasangkan dengan vectorizer.joblib)
MODEL_SPEC = [
    ("complement_nb_tuned", ART / "tuned_complement_nb.joblib", "pipeline"),
    ("multinomial_nb_tuned", ART / "tuned_multinomial_nb.joblib", "pipeline"),
    ("linear_svc_tuned", ART / "tuned_linear_svc.joblib", "pipeline"),
    ("logistic_regression_tuned", ART / "tuned_logistic_regression.joblib", "pipeline"),
    ("logistic_regression_final", ART / "model_final.joblib", "clf_terpisah"),
]


def _prediksi_satu(nama: str, path, jenis: str, teks: pd.Series, vec_final) -> dict:
    model = joblib.load(path)
    if jenis == "pipeline":
        X = model.named_steps["tfidf"].transform(teks)
        clf = model.named_steps["clf"]
    else:
        X = vec_final.transform(teks)
        clf = model

    pred = clf.predict(X)
    proba = (clf.predict_proba(X)[:, 1] if hasattr(clf, "predict_proba") else
             np.full(len(teks), np.nan))
    return {"model_name": nama, "pred_label": pred.astype(int), "pred_proba": proba}


def skor_semua_model(df: pd.DataFrame) -> pd.DataFrame:
    teks = df["ulasan_clean"].fillna("")
    vec_final = joblib.load(ART / "vectorizer.joblib")

    hasil = []
    for nama, path, jenis in MODEL_SPEC:
        r = _prediksi_satu(nama, path, jenis, teks, vec_final)
        hasil.append(pd.DataFrame({
            "review_id": df["id"].to_numpy(),
            "model_name": r["model_name"],
            "pred_label": r["pred_label"],
            "pred_proba": r["pred_proba"],
        }))
    return pd.concat(hasil, ignore_index=True)


def sanity_check(df: pd.DataFrame, skor: pd.DataFrame) -> None:
    berlabel = df["sentimen_aktual"].notna()
    aktual = df.loc[berlabel, ["id", "sentimen_aktual"]].set_index("id")["sentimen_aktual"]

    print("Sanity check per model")
    print("-" * 60)
    for nama, g in skor.groupby("model_name"):
        prop_neg = (g["pred_label"] == 0).mean()
        pred_berlabel = g.set_index("review_id").loc[aktual.index, "pred_label"]
        agreement = (pred_berlabel.to_numpy() == aktual.to_numpy()).mean()
        print(f"  {nama:28s} pred_negatif={prop_neg:6.2%}   "
              f"agreement(label aktual)={agreement:6.2%}")


def main() -> None:
    df = pd.read_parquet(resolve(CFG, "paths.clean_parquet"))
    assert len(df) == CFG["schema"]["expected_rows"], \
        f"{len(df)} != {CFG['schema']['expected_rows']}"

    skor = skor_semua_model(df)
    sanity_check(df, skor)

    n_model = len(MODEL_SPEC)
    assert len(skor) == len(df) * n_model, \
        f"{len(skor)} != {len(df)} x {n_model}"

    out_path = ROOT / "data" / "processed" / "review_scores.parquet"
    skor.to_parquet(out_path, index=False)
    print(f"\nDisimpan: {out_path.relative_to(ROOT)} ({len(skor):,} baris, "
          f"{n_model} model x {len(df):,} ulasan)")


if __name__ == "__main__":
    main()

"""Kumpulkan seluruh angka final ke docs/synthesis/facts.yaml (Fase 10, T-10.1).

Berkas keluaran adalah satu-satunya sumber angka bagi naskah Fase 10. Setiap
nilai dihitung ulang dari berkas sumber — CSV di ``docs/tables/`` dan laporan
JSON di ``ml/artifacts/reports/`` — sehingga tidak ada angka yang disalin
tangan.

    python -m ml.src.collect_facts
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml
from sklearn.metrics import cohen_kappa_score

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "docs" / "tables"
REPORTS = ROOT / "ml" / "artifacts" / "reports"
OUT = ROOT / "docs" / "synthesis" / "facts.yaml"

# Empat varian terlatih (tiga keluarga algoritma) — baseline ditangani terpisah.
VARIAN = ["complement_nb", "multinomial_nb", "linear_svc", "logistic_regression"]
MODEL_PRODUKSI = "logistic_regression_final"


def tabel(nama: str) -> pd.DataFrame:
    return pd.read_csv(TABLES / f"{nama}.csv")


def ada_tabel(nama: str) -> bool:
    return (TABLES / f"{nama}.csv").exists()


def menunggu(langkah: str, berkas: str) -> dict:
    """Penanda seksi yang bergantung pada isian manusia yang belum ada."""
    return {"status": f"MENUNGGU — {langkah} belum dikerjakan untuk data scraping",
            "berkas_yang_harus_diisi": berkas}


def manifest() -> dict:
    return json.loads((ROOT / "ml" / "artifacts" / "MANIFEST.json").read_text())


def laporan(nama: str) -> dict:
    return json.loads((REPORTS / f"{nama}.json").read_text())


def r(x, n: int = 4) -> float:
    """Bulatkan ke n desimal dan buang tipe numpy agar YAML tetap bersih."""
    return round(float(x), n)


def poin(a, b, n: int = 2) -> float:
    """Selisih dua metrik dalam satuan poin persentase."""
    return round((float(a) - float(b)) * 100, n)


# --------------------------------------------------------------------------
# 1. Dataset & EDA
# --------------------------------------------------------------------------
def fakta_dataset() -> dict:
    prof = tabel("profil_dataset").set_index("properti")["nilai"]
    dup = tabel("duplikasi").set_index("jenis")
    versi = tabel("cakupan_versi")
    v100 = versi[versi["ambang"] == 100].iloc[0]
    likes = tabel("profil_likes").set_index("statistik")["nilai"]
    ang = tabel("angka_storytelling").set_index("label")["nilai"]

    return {
        "n_baris": int(str(prof["Jumlah baris"]).replace(",", "")),
        "n_kolom_csv": int(prof["Jumlah kolom"]),
        "n_kolom_analisis": 6,
        "periode_awal": str(prof["Periode awal"]),
        "periode_akhir": str(prof["Periode akhir"]),
        "n_bulan": int(prof["Jumlah bulan"]),
        "sha256": str(prof["SHA-256 berkas"]),
        "missing_versi_app": int(str(prof["Missing · Versi App"]).replace(",", "")),
        "pct_missing_versi_app": r(
            int(str(prof["Missing · Versi App"]).replace(",", ""))
            / int(str(prof["Jumlah baris"]).replace(",", ""))
            * 100,
            1,
        ),
        "n_versi_unik": int(ang["A-30"]),
        "n_versi_min100": int(v100["jumlah_versi"]),
        "ulasan_tercakup_min100": int(v100["ulasan_tercakup"]),
        "pct_cakupan_versi_min100": r(v100["persen_cakupan_berversi"], 1),
        "duplikat_baris_penuh": int(dup.loc["Duplikat baris penuh", "jumlah"]),
        "duplikat_teks": int(dup.loc["Duplikat teks Ulasan", "jumlah"]),
        "pct_duplikat_teks": r(dup.loc["Duplikat teks Ulasan", "persen"], 1),
        "pct_likes_nol": r(likes["persen_likes_nol"], 1),
        "likes_maks": int(likes["max"]),
        "berkas_sumber": manifest()["data"]["raw_file"],
        "sumber_data": "scraping Google Play (google-play-scraper), bukan Kaggle",
        "penanganan_bahasa": _penanganan_bahasa(),
        "source_table": "docs/tables/profil_dataset.csv",
    }


def _penanganan_bahasa() -> dict:
    from ml.src.config import load_config, resolve
    from ml.src.ingest import ringkasan_saring_bahasa
    cfg = load_config()
    h = ringkasan_saring_bahasa(cfg)
    out = {"mode": cfg["language_filter"]["mode"],
           "n_mentah": h["n_mentah"], "n_dominan_inggris": h["n_inggris"],
           "pct_dominan_inggris": r(h["n_inggris"] / h["n_mentah"] * 100, 1),
           "n_dianalisis": h["n_analisis"],
           "dominan_inggris_per_rating": {int(k): int(v)
                                          for k, v in h["inggris_per_rating"].items()}}
    meta = resolve(cfg, "translation.output_csv").with_suffix(".meta.json")
    if out["mode"] == "translate" and meta.exists():
        out["terjemahan"] = json.loads(meta.read_text())
    if not ada_tabel("audit_terjemahan_sampel_50_reviewed"):
        out["audit_manual"] = menunggu("audit manual terjemahan",
                                       "docs/tables/audit_terjemahan_sampel_50.csv -> *_reviewed.csv")
        return out
    a = tabel("audit_terjemahan_sampel_50_reviewed")
    ya = lambda c: int((a[c].astype(str).str.strip().str.lower() == "ya").sum())
    out["audit_manual"] = {
        "n_sampel": int(len(a)),
        "n_deteksi_benar": ya("deteksi_benar_inggris"),
        "pct_deteksi_benar": r(ya("deteksi_benar_inggris") / len(a) * 100, 1),
        "n_terjemahan_layak": ya("terjemahan_layak"),
        "pct_terjemahan_layak": r(ya("terjemahan_layak") / len(a) * 100, 1),
        "source_table": "docs/tables/audit_terjemahan_sampel_50_reviewed.csv",
    }
    return out


def fakta_rating() -> dict:
    d = tabel("distribusi_rating").set_index("rating")
    out = {
        f"bintang_{k}": {"n": int(d.loc[k, "jumlah"]), "pct": r(d.loc[k, "persen"], 1)}
        for k in range(1, 6)
    }
    out["pct_ekstrem_1_dan_5"] = r(d.loc[1, "persen"] + d.loc[5, "persen"], 1)
    out["pct_tengah_2_3_4"] = r(d.loc[2, "persen"] + d.loc[3, "persen"] + d.loc[4, "persen"], 1)
    out["n_negatif_1_2"] = int(d.loc[1, "jumlah"] + d.loc[2, "jumlah"])
    out["n_positif_4_5"] = int(d.loc[4, "jumlah"] + d.loc[5, "jumlah"])
    out["source_table"] = "docs/tables/distribusi_rating.csv"
    return out


def fakta_asimetri() -> dict:
    p = tabel("panjang_per_rating").set_index("rating")
    pendek = tabel("ulasan_pendek").set_index("kelompok")
    kontras = tabel("kontras_kelas").set_index("kelas")
    ulang = tabel("teks_paling_berulang")
    return {
        "rata_kata_per_rating": {
            f"r{k}": r(p.loc[k, "rata_kata"], 1) for k in range(1, 6)
        },
        "median_kata_per_rating": {
            f"r{k}": r(p.loc[k, "median_kata"], 1) for k in range(1, 6)
        },
        "n_ulasan_max_2_kata": int(pendek.loc["≤2 kata", "jumlah"]),
        "pct_ulasan_max_2_kata": r(pendek.loc["≤2 kata", "persen"], 1),
        "n_ulasan_min_5_kata": int(pendek.loc["≥5 kata (informatif)", "jumlah"]),
        "pct_ulasan_min_5_kata": r(pendek.loc["≥5 kata (informatif)", "persen"], 1),
        "duplikat_teks_negatif": int(kontras.loc["Negatif", "duplikat_teks"]),
        "pct_duplikat_negatif": r(kontras.loc["Negatif", "persen_duplikat"], 1),
        "duplikat_teks_positif": int(kontras.loc["Positif", "duplikat_teks"]),
        "pct_duplikat_positif": r(kontras.loc["Positif", "persen_duplikat"], 1),
        "pct_le2kata_negatif": r(kontras.loc["Negatif", "persen_le2kata"], 1),
        "pct_le2kata_positif": r(kontras.loc["Positif", "persen_le2kata"], 1),
        "teks_terulang_teratas": str(ulang.iloc[0]["teks"]),
        "frekuensi_teks_terulang_teratas": int(ulang.iloc[0]["frekuensi"]),
        "source_table": "docs/tables/panjang_per_rating.csv",
    }


def fakta_kelas() -> dict:
    k = tabel("komposisi_kelas")
    biner = k[k["skema"] == "Biner"].set_index("kelas")
    tiga = k[k["skema"] == "3 kelas"].set_index("kelas")
    n_neg = int(biner.loc["Negatif", "jumlah"])
    n_pos = int(biner.loc["Positif", "jumlah"])
    n_net = int(tiga.loc["Netral", "jumlah"])
    return {
        "n_negatif": n_neg,
        "n_positif": n_pos,
        "n_netral_dibuang": n_net,
        "pct_netral": r(tiga.loc["Netral", "persen"], 1),
        "n_dipakai_biner": n_neg + n_pos,
        "pct_negatif_biner": r(biner.loc["Negatif", "persen"], 1),
        "pct_positif_biner": r(biner.loc["Positif", "persen"], 1),
        "rasio_netral_positif": r(n_pos / n_net, 1),
        "source_table": "docs/tables/komposisi_kelas.csv",
    }


# --------------------------------------------------------------------------
# 2. Model
# --------------------------------------------------------------------------
def _metrik(row: pd.Series) -> dict:
    return {
        "macro_f1": r(row["macro_f1"]),
        "recall_neg": r(row["recall_neg"]),
        "precision_neg": r(row["precision_neg"]),
        "f1_neg": r(row["f1_neg"]),
        "accuracy": r(row["accuracy"]),
        "n_eval": int(row["n_eval"]),
    }


def fakta_model() -> dict:
    m = tabel("model_metrics")
    m = m[m["dedup_training"]]  # protokol final memakai training terdeduplikasi
    idx = m.set_index(["model_name", "eval_set"])

    base = idx.loc[("majority_baseline", "full")]
    hasil: dict = {
        "n_train": int(base["n_train"]),
        "n_train_sebelum_dedup": int(
            tabel("model_metrics").query("~dedup_training").iloc[0]["n_train"]
        ),
        "n_test": int(base["n_test"]),
        "n_test_informative": int(idx.loc[("majority_baseline", "informative_ge5w")]["n_eval"]),
        "baseline": {
            "macro_f1_full": r(base["macro_f1"]),
            "accuracy_full": r(base["accuracy"]),
            "pct_accuracy_full": r(base["accuracy"] * 100, 1),
            "macro_f1_informative": r(
                idx.loc[("majority_baseline", "informative_ge5w")]["macro_f1"]
            ),
        },
        "varian": {},
        "source_table": "docs/tables/model_metrics.csv",
    }

    for nama in VARIAN:
        hasil["varian"][nama] = {
            "default": {
                "full": _metrik(idx.loc[(nama, "full")]),
                "informative": _metrik(idx.loc[(nama, "informative_ge5w")]),
            },
            "tuned": {
                "full": _metrik(idx.loc[(f"{nama}_tuned", "full")]),
                "informative": _metrik(idx.loc[(f"{nama}_tuned", "informative_ge5w")]),
                "train_seconds": r(idx.loc[(f"{nama}_tuned", "full")]["train_seconds"], 2),
            },
        }

    # Selisih dihitung dari nilai belum dibulatkan; selisih dari nilai empat
    # desimal dapat meleset satu digit (0,9270 - 0,9261 = 0,09, padahal 0,08).
    f1_tuned = {n: float(idx.loc[(f"{n}_tuned", "full")]["macro_f1"]) for n in VARIAN}
    terbaik = max(f1_tuned, key=f1_tuned.get)
    terendah = min(f1_tuned, key=f1_tuned.get)
    hasil["rentang_macro_f1_tuned"] = {
        "tertinggi": r(f1_tuned[terbaik]),
        "tertinggi_model": terbaik,
        "terendah": r(f1_tuned[terendah]),
        "terendah_model": terendah,
        "rentang_poin": poin(f1_tuned[terbaik], f1_tuned[terendah]),
        "selisih_dua_teratas_poin": poin(*sorted(f1_tuned.values(), reverse=True)[:2]),
        "selisih_dua_teratas_baris": int(
            round(
                (sorted(f1_tuned.values(), reverse=True)[0]
                 - sorted(f1_tuned.values(), reverse=True)[1])
                * hasil["n_test"]
            )
        ),
    }

    prod_full = idx.loc[(MODEL_PRODUKSI, "full")]
    prod_inf = idx.loc[(MODEL_PRODUKSI, "informative_ge5w")]
    cm = laporan("logistic_regression_final_full")
    hasil["produksi"] = {
        "nama": "logistic_regression",
        "parameter": ", ".join(f"{k}={v}" for k, v in manifest()["model"]["params"].items()),
        "full": _metrik(prod_full),
        "informative": _metrik(prod_inf),
        "recall_pos_full": r(cm["positif"]["recall"]),
        "precision_pos_full": r(cm["positif"]["precision"]),
        "selisih_macro_f1_poin": poin(prod_full["macro_f1"], prod_inf["macro_f1"]),
        "selisih_accuracy_poin": poin(prod_full["accuracy"], prod_inf["accuracy"]),
        "selisih_recall_neg_poin": poin(prod_inf["recall_neg"], prod_full["recall_neg"]),
        "unggul_baseline_poin": poin(prod_full["macro_f1"], base["macro_f1"]),
    }
    return hasil


def fakta_tuning() -> dict:
    g = tabel("gridsearch_results")
    bp = json.loads((ROOT / "ml" / "artifacts" / "best_params.json").read_text())

    def terpilih(model: str) -> pd.Series:
        sub = g[g["model_name"] == model]
        return sub.loc[sub["mean_test_score"].idxmax()]

    svc = terpilih("linear_svc")
    lr = terpilih("logistic_regression")
    def kombinasi(model: str, c: str) -> pd.Series:
        sub = g[
            (g["model_name"] == model)
            & g["params"].str.contains(f"'clf__C': {c},")
            & g["params"].str.contains("'balanced'")
        ]
        return sub.iloc[0]

    svc_c5 = kombinasi("linear_svc", "5.0")

    out = {
        "n_kombinasi": int(len(g)),
        "n_fit": int(len(g) * 5),
        "cv_folds": 5,
        "linear_svc": {
            "cv_macro_f1": r(svc["mean_test_score"], 4),
            "std": r(svc["std_test_score"], 4),
            "overfit_gap": r(svc["overfit_gap"], 4),
            "train_score_c5": r(svc_c5["mean_train_score"], 4),
            "cv_score_c5": r(svc_c5["mean_test_score"], 4),
            "overfit_gap_c5": r(svc_c5["overfit_gap"], 4),
        },
        "logistic_regression": {
            "pemenang_grid": str(bp["logistic_regression"]["best_params"]),
            "cv_macro_f1_grid": r(lr["mean_test_score"], 6),
            "std_grid": r(lr["std_test_score"], 6),
            "overfit_gap_grid": r(lr["overfit_gap"], 4),
            "pilihan_1se": str(bp["logistic_regression"]["seleksi_1se"]["best_params"]),
            "cv_macro_f1_1se": r(bp["logistic_regression"]["seleksi_1se"]["cv_f1_macro"], 6),
            "std_1se": r(bp["logistic_regression"]["seleksi_1se"]["cv_f1_macro_std"], 6),
            "overfit_gap_1se": r(bp["logistic_regression"]["seleksi_1se"]["overfit_gap"], 4),
            "selisih_cv": r(lr["mean_test_score"]
                            - bp["logistic_regression"]["seleksi_1se"]["cv_f1_macro"], 5),
        },
        "seleksi_1se": {
            model: {
                "pemenang_grid": str(bp[model]["best_params"]),
                "pilihan_1se": str(bp[model]["seleksi_1se"]["best_params"]),
                "n_kandidat": int(bp[model]["seleksi_1se"]["n_kandidat_dalam_1se"]),
                "overfit_gap_1se": r(bp[model]["seleksi_1se"]["overfit_gap"], 4),
                "sama_dengan_grid": bool(bp[model]["seleksi_1se"]["sama_dengan_gridsearch"]),
            }
            for model in VARIAN
        },
        "gridsearch_seconds_total": r(
            sum(bp[model]["gridsearch_seconds"] for model in VARIAN), 1
        ),
        "source_table": "docs/tables/gridsearch_results.csv",
    }
    return out


# --------------------------------------------------------------------------
# 3. Analisis kesalahan, tiga kelas, fitur
# --------------------------------------------------------------------------
def fakta_error(n_test: int, akurasi_produksi: float) -> dict:
    if not ada_tabel("error_analysis_50_reviewed"):
        m = tabel("model_metrics")
        idx = m[m["dedup_training"]].set_index(["model_name", "eval_set"])
        n_salah = int(round((1 - idx.loc[("linear_svc_tuned", "full")]["accuracy"]) * n_test))
        return {**menunggu("analisis kesalahan manual (kategori penyebab)",
                           "docs/tables/error_analysis_50.csv -> *_reviewed.csv"),
                "n_salah_linear_svc_tuned": n_salah,
                "pct_salah_linear_svc_tuned": r(n_salah / n_test * 100, 2)}
    e = tabel("error_analysis_50_reviewed")
    n = len(e)
    kat = e["kategori_penyebab"].value_counts()
    label_keliru = int(kat.get("label_keliru_pengguna", 0))
    pct_label_keliru = r(label_keliru / n * 100, 1)

    m = tabel("model_metrics")
    idx = m[m["dedup_training"]].set_index(["model_name", "eval_set"])
    n_salah_svc = int(round((1 - idx.loc[("linear_svc_tuned", "full")]["accuracy"]) * n_test))

    derau_n = int(round(n_salah_svc * label_keliru / n))
    derau_pct = r(derau_n / n_test * 100, 2)
    plafon = r(1 - derau_n / n_test, 4)

    fp = e[e["rating"] >= 4]
    fn = e[e["rating"] <= 2]
    fp_keliru = int((fp["kategori_penyebab"] == "label_keliru_pengguna").sum())
    fn_keliru = int((fn["kategori_penyebab"] == "label_keliru_pengguna").sum())

    yakin = e[e["jarak_ke_batas"] >= 0.5]
    return {
        "n_sampel": n,
        "n_salah_linear_svc_tuned": n_salah_svc,
        "pct_salah_linear_svc_tuned": r(n_salah_svc / n_test * 100, 2),
        "kategori": {str(k): int(v) for k, v in kat.items()},
        "pct_kategori": {str(k): r(v / n * 100, 1) for k, v in kat.items()},
        "n_label_keliru": label_keliru,
        "pct_label_keliru": pct_label_keliru,
        "n_fp_sampel": int(len(fp)),
        "n_fp_label_keliru": fp_keliru,
        "pct_fp_label_keliru": r(fp_keliru / len(fp) * 100, 1),
        "n_fn_sampel": int(len(fn)),
        "n_fn_label_keliru": fn_keliru,
        "pct_fn_label_keliru": r(fn_keliru / len(fn) * 100, 1),
        "n_kesalahan_yakin": int(len(yakin)),
        "n_yakin_label_keliru": int(
            (yakin["kategori_penyebab"] == "label_keliru_pengguna").sum()
        ),
        "pct_yakin_label_keliru": r(
            (yakin["kategori_penyebab"] == "label_keliru_pengguna").sum() / len(yakin) * 100, 1
        ),
        "n_kesalahan_ragu": int(n - len(yakin)),
        "derau_label_n": derau_n,
        "derau_label_pct": derau_pct,
        "plafon_akurasi": plafon,
        "pct_plafon_tercapai": r(akurasi_produksi / plafon * 100, 1),
        "sisa_perbaikan_poin": poin(plafon, akurasi_produksi),
        "source_table": "docs/tables/error_analysis_50_reviewed.csv",
    }


def fakta_tiga_kelas(macro_f1_biner_terbaik: float, recall_neg_biner: float) -> dict:
    d = laporan("three_class_linear_svc")
    cm = d["cm"]
    n_netral = int(sum(cm[1]))
    return {
        "macro_f1": r(d["macro_f1"]),
        "macro_f1_biner_pembanding": macro_f1_biner_terbaik,
        "penurunan_poin": poin(macro_f1_biner_terbaik, d["macro_f1"], 1),
        "accuracy": r(d["laporan"]["accuracy"]),
        "recall_negatif": r(d["recall"]["Negatif (1-2)"]),
        "penurunan_recall_neg_poin": poin(recall_neg_biner, d["recall"]["Negatif (1-2)"], 1),
        "recall_netral": r(d["recall"]["Netral (3)"]),
        "recall_positif": r(d["recall"]["Positif (4-5)"]),
        "n_train": int(d["n_train"]),
        "n_test": int(d["n_test"]),
        "n_netral_train": int(d["dist_train"][1]),
        "n_netral_test": n_netral,
        "netral_jadi_negatif": int(cm[1][0]),
        "pct_netral_jadi_negatif": r(cm[1][0] / n_netral * 100, 1),
        "netral_jadi_netral": int(cm[1][1]),
        "pct_netral_jadi_netral": r(cm[1][1] / n_netral * 100, 1),
        "netral_jadi_positif": int(cm[1][2]),
        "pct_netral_jadi_positif": r(cm[1][2] / n_netral * 100, 1),
        "rasio_netral_positif_test": r(d["dist_test"][2] / n_netral, 1),
        "panjang_negatif": r(d["panjang"]["mean"]["Negatif (1-2)"], 2),
        "panjang_netral": r(d["panjang"]["mean"]["Netral (3)"], 2),
        "panjang_positif": r(d["panjang"]["mean"]["Positif (4-5)"], 2),
        "source_table": "ml/artifacts/reports/three_class_linear_svc.json",
    }


def fakta_fitur() -> dict:
    t = tabel("top_features")
    lr = t[t["model"] == "logistic_regression"]
    return {
        "n_fitur_per_kelas": int(lr[lr["kelas"] == "negatif"]["rank"].max()),
        "teratas_negatif": [
            str(x) for x in lr[lr["kelas"] == "negatif"].sort_values("rank")["fitur"].head(10)
        ],
        "teratas_positif": [
            str(x) for x in lr[lr["kelas"] == "positif"].sort_values("rank")["fitur"].head(10)
        ],
        "source_table": "docs/tables/top_features.csv",
    }


# --------------------------------------------------------------------------
# 4. Topik
# --------------------------------------------------------------------------
def fakta_topik(n_negatif: int) -> dict:
    t = tabel("topics_ranked").sort_values("peringkat_frekuensi")
    coh = tabel("lda_coherence")
    terbaik = coh.loc[coh["coherence_cv"].idxmax()]
    ng = tabel("ngram_negatif")

    peringkat = [
        {
            "peringkat": int(row["peringkat_frekuensi"]),
            "kategori": str(row["kategori"]),
            "n": int(row["jumlah_ulasan"]),
            "pct_negatif": r(row["persen_ulasan_negatif"], 2),
            "total_likes": int(row["total_likes"]),
            "rata_likes": r(row["rata_likes"], 2),
            "peringkat_likes": int(row["peringkat_likes"]),
        }
        for _, row in t.iterrows()
    ]

    cerita = tabel("tabel3_storytelling_topik").set_index("kategori")
    kutipan = [
        {
            "kategori": p["kategori"],
            "nomor": n,
            "teks": str(cerita.loc[p["kategori"], f"contoh_{n}"]),
            "likes": int(cerita.loc[p["kategori"], f"contoh_{n}_likes"]),
        }
        for p in peringkat[:3]
        for n in (1, 2)
    ]

    def ngram(term: str) -> dict:
        row = ng[ng["term"].astype(str) == term]
        if row.empty:
            return {}
        row = row.iloc[0]
        return {
            "frekuensi": int(row["freq"]),
            "n_dokumen": int(row["n_dokumen"]),
            "pct_dokumen": r(row["persen_dokumen"], 1),
        }

    return {
        "n_kategori": int(len(t)),
        "n_penetapan_kategori": int(t["jumlah_ulasan"].sum()),
        "lda_k": int(terbaik["k"]),
        "coherence_cv": r(terbaik["coherence_cv"], 4),
        "peringkat": peringkat,
        "dua_teratas_pct": r(
            peringkat[0]["pct_negatif"] + peringkat[1]["pct_negatif"], 2
        ),
        "n_ulasan_negatif": n_negatif,
        "kutipan": kutipan,
        "ngram_pengemudi": ngram("pengemudi"),
        "ngram_dapat_pengemudi": ngram("dapat pengemudi"),
        "ngram_tidak": ngram("tidak"),
        "source_table": "docs/tables/topics_ranked.csv",
    }


def fakta_validasi() -> dict:
    if not ada_tabel("h9_hasil_kesepakatan"):
        return menunggu("validasi silang oleh penilai independen",
                        "docs/tables/cross_validation_sample_50.csv -> *_reviewed.csv")
    d = tabel("h9_hasil_kesepakatan")
    return {
        "n_sampel": int(len(d)),
        "cohen_kappa": r(cohen_kappa_score(d["penilai"], d["otomatis_utama"])),
        "kesepakatan_longgar": r(d["sepakat_longgar"].mean(), 2),
        "pct_kesepakatan_longgar": r(d["sepakat_longgar"].mean() * 100, 1),
        "kesepakatan_ketat": r((d["penilai"] == d["otomatis_utama"]).mean(), 2),
        "pct_kesepakatan_ketat": r((d["penilai"] == d["otomatis_utama"]).mean() * 100, 1),
        "jaccard_rerata": r(d["jaccard"].mean()),
        "source_table": "docs/tables/h9_hasil_kesepakatan.csv",
    }


def fakta_tren() -> dict:
    v = tabel("volume_bulanan")
    t = tabel("topic_trend_monthly")
    puncak = t.loc[t["jumlah"].idxmax()]
    penuh = v[~v["periode_parsial"]]
    t_penuh = t[~t["periode_parsial"]]
    awal, akhir = t_penuh["bulan"].min(), t_penuh["bulan"].max()
    per_kat = t_penuh.pivot_table(index="kategori", columns="bulan", values="jumlah",
                                  fill_value=0)
    return {
        "n_bulan": int(len(v)),
        "volume_tertinggi_bulan": str(v.loc[v["jumlah"].idxmax(), "bulan"]),
        "volume_tertinggi": int(v["jumlah"].max()),
        "volume_terendah_bulan": str(
            v[~v["periode_parsial"]].loc[v[~v["periode_parsial"]]["jumlah"].idxmin(), "bulan"]
        ),
        "volume_terendah": int(v[~v["periode_parsial"]]["jumlah"].min()),
        "bulan_penuh_awal": str(penuh.iloc[0]["bulan"]),
        "bulan_penuh_akhir": str(penuh.iloc[-1]["bulan"]),
        "rata_rating_awal": r(penuh.iloc[0]["rata_rating"], 2),
        "rata_rating_akhir": r(penuh.iloc[-1]["rata_rating"], 2),
        "puncak_kategori": str(puncak["kategori"]),
        "puncak_bulan": str(puncak["bulan"])[:7],
        "puncak_jumlah": int(puncak["jumlah"]),
        "kategori_bulan_penuh_awal_vs_akhir": {
            str(k): {"awal": int(row[awal]), "akhir": int(row[akhir])}
            for k, row in per_kat.iterrows()
        },
        "source_table": "docs/tables/topic_trend_monthly.csv",
    }


def fakta_pola_sentimen() -> dict:
    """Deskriptif RM3: proporsi negatif (prediksi model produksi) per bulan & versi.

    Hanya statistik deskriptif. Uji chi-kuadrat dan aturan penandaan rilis
    (Bab 3, 3.6.7) belum diimplementasikan.
    """
    rev = pd.read_parquet(ROOT / "data" / "processed" / "reviews_clean.parquet",
                          columns=["id", "tanggal", "versi_minor", "sentimen_aktual"])
    sk = pd.read_parquet(ROOT / "data" / "processed" / "review_scores.parquet")
    sk = sk[sk["model_name"] == MODEL_PRODUKSI][["review_id", "pred_label"]]
    d = rev.merge(sk, left_on="id", right_on="review_id")
    d["neg"] = d["pred_label"] == 0
    d["bulan"] = pd.to_datetime(d["tanggal"]).dt.strftime("%Y-%m")
    parsial = set(yaml.safe_load((ROOT / "ml" / "config.yaml").read_text())
                  ["temporal"]["partial_months"])
    bln = d.groupby("bulan").agg(n=("neg", "size"), pct_neg=("neg", "mean"))
    bln_penuh = bln[~bln.index.isin(parsial)]
    ver = d.dropna(subset=["versi_minor"]).groupby("versi_minor").agg(
        n=("neg", "size"), pct_neg=("neg", "mean"))
    ver = ver[ver["n"] >= 100]
    return {
        "label": f"prediksi {MODEL_PRODUKSI}",
        "pct_negatif_keseluruhan": r(d["neg"].mean() * 100, 2),
        "bulanan_pct_negatif": {k: r(v * 100, 2) for k, v in bln["pct_neg"].items()},
        "bulan_parsial": sorted(parsial),
        "bulan_penuh_pct_negatif_terendah": {
            "bulan": str(bln_penuh["pct_neg"].idxmin()),
            "pct": r(bln_penuh["pct_neg"].min() * 100, 2)},
        "bulan_penuh_pct_negatif_tertinggi": {
            "bulan": str(bln_penuh["pct_neg"].idxmax()),
            "pct": r(bln_penuh["pct_neg"].max() * 100, 2)},
        "n_versi_dianalisis": int(len(ver)),
        "n_ulasan_versi_dianalisis": int(ver["n"].sum()),
        "versi_pct_negatif_terendah": {
            "versi": str(ver["pct_neg"].idxmin()), "pct": r(ver["pct_neg"].min() * 100, 2)},
        "versi_pct_negatif_tertinggi": {
            "versi": str(ver["pct_neg"].idxmax()), "pct": r(ver["pct_neg"].max() * 100, 2)},
        "status_uji_rm3": "BELUM DIIMPLEMENTASIKAN — uji chi-kuadrat & penandaan rilis",
        "source_table": "data/processed/review_scores.parquet",
    }


def fakta_preprocessing() -> dict:
    """Angka preprocessing dihitung ulang dari parquet hasil Fase 2."""
    parquet = ROOT / "data" / "processed" / "reviews_clean.parquet"
    if not parquet.exists():
        raise SystemExit(
            f"❌ {parquet.relative_to(ROOT)} tidak ada. "
            "Jalankan `./ml/run_pipeline.sh` lebih dulu — facts.yaml tidak boleh "
            "diisi angka yang tidak dapat dihitung ulang."
        )
    import re as _re

    from ml.src.slang_dict import SLANG_DICT
    from ml.src.stopwords import NEGATION_KEEP

    df = pd.read_parquet(parquet, columns=["ulasan_clean", "word_count"])
    teks = df["ulasan_clean"].fillna("")

    def n_dok(frasa: str) -> int:
        return int(teks.str.contains(rf"\b{_re.escape(frasa)}\b", regex=True).sum())

    # Putaran verifikasi: sampel_100, lalu ronde2, ronde3, ... Sebuah putaran
    # dihitung bila berkas `_reviewed`-nya ada. Verifikasi belum selesai selama
    # masih ada berkas sampel yang belum dikembalikan sebagai `_reviewed`.
    nama = ["preprocessing_sample_100"] + [f"preprocessing_sample_ronde{i}" for i in range(2, 10)]
    selesai = [b for b in nama if ada_tabel(f"{b}_reviewed")]
    tertunda = [b for b in nama if ada_tabel(b) and not ada_tabel(f"{b}_reviewed")]
    n_sampel = sum(len(tabel(f"{b}_reviewed")) for b in selesai) if selesai else None
    return {
        "n_baris": int(len(df)),
        "teks_kosong_akhir": int((teks.str.strip() == "").sum()),
        "pct_teks_kosong_akhir": r((teks.str.strip() == "").sum() / len(df) * 100, 1),
        "n_entri_slang": int(len(SLANG_DICT)),
        "n_entri_slang_multikata": int(
            sum(1 for v in SLANG_DICT.values() if len(v) > 1)
        ),
        "n_negation_keep": int(len(NEGATION_KEEP)),
        "n_sampel_verifikasi_manual": n_sampel,
        "n_putaran_verifikasi": len(selesai) or None,
        "status_verifikasi_manual": (
            f"MENUNGGU — verifikasi manual sampel pra-pemrosesan data scraping "
            f"(docs/tables/{tertunda[0]}.csv)" if tertunda else "selesai"),
        "dok_tidak": n_dok("tidak"),
        "dok_tidak_bisa": n_dok("tidak bisa"),
        "dok_tidak_ada": n_dok("tidak ada"),
        "dok_jangan": n_dok("jangan"),
        "source_table": "data/processed/reviews_clean.parquet",
    }


# --------------------------------------------------------------------------
# 5. Angka struktural (bukan hasil pengukuran)
# --------------------------------------------------------------------------
ANGKA_STRUKTURAL = {
    "penjelasan": (
        "Angka yang muncul di naskah sebagai penomoran, tahun, atau parameter "
        "konfigurasi — bukan hasil pengukuran. Didaftarkan eksplisit agar "
        "verify_manuscript.py tidak menganggapnya angka tanpa sumber."
    ),
    "penomoran_bagian": list(range(0, 21)),
    "tahun": [1977, 1984, 2014, 2024, 2025, 2026],
    "konfigurasi": {
        "seed": 42,
        "tfidf_ngram_min": 1,
        "tfidf_ngram_max": 2,
        "tfidf_min_df": 3,
        "tfidf_max_features": 30000,
        "test_size": 0.2,
        "pct_train": 80,
        "pct_test": 20,
        "informative_min_words": 5,
        "C_produksi": manifest()["model"]["params"].get("C"),
        "C_grid": [0.1, 0.5, 1.0, 5.0],
        "alpha_grid": [0.1, 0.5, 1.0, 2.0],
        "n_top_features": 20,
        "n_top_terms_lda": 20,
        "lda_k_min": 5,
        "lda_k_max": 12,
        "min_reviews_per_version": 100,
        "python": 3.12,
        "postgres": 16,
        "n_container": 3,
        "n_endpoint_api": 7,
        "n_komponen_dashboard": 7,
        "n_gambar": 15,
        "ambang_1se": 1,
    },
}


def main() -> None:
    dataset = fakta_dataset()
    rating = fakta_rating()
    kelas = fakta_kelas()
    model = fakta_model()
    tiga = fakta_tiga_kelas(
        model["rentang_macro_f1_tuned"]["tertinggi"],
        model["varian"]["linear_svc"]["tuned"]["full"]["recall_neg"],
    )
    error = fakta_error(model["n_test"], model["produksi"]["full"]["accuracy"])

    facts = {
        "meta": {
            "dihasilkan_oleh": "python -m ml.src.collect_facts",
            "fase": "pembaruan data scraping",
            "aturan": (
                "Seluruh nilai dihitung ulang dari docs/tables/*.csv dan "
                "ml/artifacts/reports/*.json. Angka yang tidak ada di berkas ini "
                "tidak boleh muncul di naskah."
            ),
            "prasyarat": (
                "Seksi preprocessing dihitung dari data/processed/reviews_clean.parquet "
                "yang tidak ikut di-commit; jalankan ./ml/run_pipeline.sh lebih dulu "
                "pada klon bersih."
            ),
        },
        "dataset": dataset,
        "distribusi_rating": rating,
        "asimetri_panjang": fakta_asimetri(),
        "komposisi_kelas": kelas,
        "preprocessing": fakta_preprocessing(),
        "model": model,
        "tuning": fakta_tuning(),
        "analisis_kesalahan": error,
        "tiga_kelas": tiga,
        "fitur": fakta_fitur(),
        "topik": fakta_topik(kelas["n_negatif"]),
        "validasi_silang": fakta_validasi(),
        "tren": fakta_tren(),
        "pola_sentimen_rm3": fakta_pola_sentimen(),
        "angka_struktural": ANGKA_STRUKTURAL,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        yaml.safe_dump(facts, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )
    n_nilai = yaml.safe_load(OUT.read_text())
    print(f"✅ {OUT.relative_to(ROOT)} ditulis — {len(n_nilai)} seksi")


if __name__ == "__main__":
    main()

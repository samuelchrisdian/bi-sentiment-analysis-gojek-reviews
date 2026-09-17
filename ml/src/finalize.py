"""Artefak produksi + MANIFEST.json (Fase 4, T-4.7) — jalankan SETELAH H-10.

Script ini tidak memilih model. Nama model diberikan sebagai argumen, karena
keputusan model produksi adalah pernyataan manusia (gerbang H-10) yang alasannya
ditulis di docs/model_decision.md — bukan konsekuensi otomatis dari macro-F1
tertinggi. Pada Fase 4 selisih keempat model 1,9 poin dan syarat "LinearSVC
unggul >=2 poin" tidak terpenuhi, sehingga angka saja memang tidak menentukan.

    python -m ml.src.finalize logistic_regression              # seleksi 1-SE (default)
    python -m ml.src.finalize logistic_regression --seleksi grid
    python -m ml.src.finalize logistic_regression --dry-run

Model dilatih ulang dari parameter terpilih, lalu dievaluasi sendiri di sini —
metrik di MANIFEST.json berasal dari model yang benar-benar disimpan, bukan
dari pencarian baris di CSV.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import LabelEncoder

from sklearn.pipeline import Pipeline

from .config import load_config, resolve
from .dataset import assert_konsisten_fase3, siapkan_teks
from .evaluate import hitung_metrik, laporan_lengkap
from .features import build_vectorizer
from .tune import BASE

CFG = load_config()
ROOT = CFG["_root"]
NAMA_KELAS = ["negatif", "positif"]
# Model tanpa predict_proba: butuh kalibrasi agar /api/predict dapat
# mengembalikan probabilitas, bukan sekadar label.
PERLU_KALIBRASI = {"linear_svc"}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def _versi_pustaka() -> dict:
    import matplotlib, pyarrow, scipy, yaml
    v = {"python": platform.python_version(), "scikit-learn": sklearn.__version__,
         "numpy": np.__version__, "pandas": pd.__version__, "scipy": scipy.__version__,
         "joblib": joblib.__version__, "pyarrow": pyarrow.__version__,
         "matplotlib": matplotlib.__version__, "pyyaml": yaml.__version__}
    try:
        import Sastrawi
        v["Sastrawi"] = getattr(Sastrawi, "__version__", "1.0.1")
    except ImportError:
        v["Sastrawi"] = "tidak terpasang"
    return v


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                       text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def _evaluasi(clf, vec, d: dict) -> tuple[dict, np.ndarray, float]:
    """Protokol evaluasi ganda Fase 3, dijalankan pada model final itu sendiri."""
    Xte = vec.transform(d["X_te"])
    _t0 = time.perf_counter()
    pred = clf.predict(Xte)
    t_pred = round(time.perf_counter() - _t0, 6)
    out = {}
    for nama_set, mask in (("full", np.ones(len(d["y_te"]), bool)),
                           ("informative_ge5w", d["mask_informatif"])):
        out[nama_set] = {k: round(float(v), 6)
                         for k, v in hitung_metrik(d["y_te"][mask], pred[mask]).items()}
        out[nama_set]["n_eval"] = int(mask.sum())
    return out, pred, t_pred


def bangun(nama: str, out: Path, seleksi: str = "1se") -> dict:
    out.mkdir(parents=True, exist_ok=True)
    bp = json.loads((ROOT / "ml" / "artifacts" / "best_params.json").read_text())
    if nama not in bp:
        raise SystemExit(f"model '{nama}' tidak ditemukan. Pilihan: {list(bp)}")
    sumber = bp[nama]["seleksi_1se"] if seleksi == "1se" else bp[nama]
    params = sumber["best_params"]

    d = siapkan_teks(dedup=CFG["preprocessing"]["dedup_training_text"])
    assert_konsisten_fase3(d)

    # Dilatih ulang dari parameter terpilih, bukan memuat pipeline tuned:
    # seleksi 1-SE dapat menghasilkan parameter yang berbeda dari pemenang grid.
    # Vectorizer dan classifier disimpan terpisah sesuai kontrak API — vectorizer
    # dipakai juga oleh jalur lain (topik, dashboard).
    pipe = Pipeline([("tfidf", build_vectorizer(CFG)),
                     ("clf", clone(BASE[nama]).set_params(**params))])
    _t0 = time.perf_counter()
    pipe.fit(d["X_tr"], d["y_tr"])
    t_train = round(time.perf_counter() - _t0, 4)
    vec = pipe.named_steps["tfidf"]
    clf = pipe.named_steps["clf"]
    Xtr = vec.transform(d["X_tr"])
    metrik, pred, t_pred = _evaluasi(clf, vec, d)

    le = LabelEncoder().fit(NAMA_KELAS)      # identitas: label sudah 0/1 sejak Fase 2
    joblib.dump(vec, out / "vectorizer.joblib")
    joblib.dump(clf, out / "model_final.joblib")
    joblib.dump(le, out / "label_encoder.joblib")

    dikalibrasi = nama in PERLU_KALIBRASI
    if dikalibrasi:
        cal = CalibratedClassifierCV(clone(clf), method="sigmoid", cv=5)
        cal.fit(Xtr, d["y_tr"])
        joblib.dump(cal, out / "model_calibrated.joblib")

    raw = resolve(CFG, "paths.raw_csv")
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "phase": "fase-4",
        "git_commit": _git_commit(),
        "data": {
            "raw_file": raw.name,
            "sha256": _sha256(raw),
            "n_rows_raw": CFG["schema"]["expected_rows"],
            "n_rows_used": d["n_labeled"],
            "n_train_before_dedup": d["n_train_sebelum_dedup"],
            "n_train_after_dedup": d["n_train"],
            "n_test": d["n_test"],
            "n_test_informative_ge5w": int(d["mask_informatif"].sum()),
        },
        "config_snapshot": {k: v for k, v in CFG.items() if k != "_root"},
        "environment": _versi_pustaka(),
        "model": {
            "name": f"{nama}_final",
            "estimator": type(clf).__name__,
            "params": params,
            "selection_rule": ("one-standard-error (Breiman et al., 1984)"
                               if seleksi == "1se" else "GridSearchCV best_score_"),
            "gridsearch_best_params": bp[nama]["best_params"],
            "cv_f1_macro": round(sumber["cv_f1_macro"], 6),
            "cv_f1_macro_std": round(sumber["cv_f1_macro_std"], 6),
            "overfit_gap_cv": round(sumber["overfit_gap"], 6),
            "calibrated": dikalibrasi,
            "calibration_method": "sigmoid" if dikalibrasi else None,
        },
        "labels": {"0": "negatif", "1": "positif"},
        "train_seconds": t_train,
        "predict_seconds": t_pred,
        "metrics": metrik,
        "baseline_majority_accuracy": CFG["evaluation"]["majority_baseline"],
        "random_state": CFG["seed"],
    }
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False),
                                       encoding="utf-8")

    # Baris *_final masuk model_metrics.csv agar /api/model/metrics menampilkan
    # model yang benar-benar dilayankan, berdampingan dengan default dan tuned.
    if out == ROOT / "ml" / "artifacts":
        pm = ROOT / "docs" / "tables" / "model_metrics.csv"
        lama = pd.read_csv(pm)
        lama = lama[~lama.model_name.str.endswith("_final")]        # idempoten
        baru = pd.DataFrame([
            {"model_name": f"{nama}_final", "eval_set": k, **{kk: vv for kk, vv in v.items()},
             "train_seconds": t_train, "predict_seconds": t_pred, "dedup_training": True,
             "n_train": d["n_train"], "n_test": d["n_test"]}
            for k, v in metrik.items()])
        pd.concat([lama, baru], ignore_index=True).to_csv(pm, index=False)

        rep = ROOT / "ml" / "artifacts" / "reports"
        for nama_set, mask in (("full", np.ones(len(d["y_te"]), bool)),
                               ("informative_ge5w", d["mask_informatif"])):
            (rep / f"{nama}_final_{nama_set}.json").write_text(
                json.dumps(laporan_lengkap(d["y_te"][mask], pred[mask]), indent=2),
                encoding="utf-8")

    # Referensi untuk uji muat ulang di proses terpisah (DoD Fase 4).
    sampel = d["X_te"].iloc[:10]
    ref = {"teks": sampel.tolist(),
           "pred": clf.predict(vec.transform(sampel)).tolist()}
    (out / "_uji_muat_ulang.json").write_text(json.dumps(ref, ensure_ascii=False),
                                              encoding="utf-8")
    return manifest


def verifikasi_muat_ulang(out: Path) -> bool:
    """Dijalankan sebagai PROSES BARU — itulah yang diuji."""
    kode = (
        "import json,joblib,sys;from pathlib import Path;"
        f"p=Path(r'{out}');"
        "r=json.loads((p/'_uji_muat_ulang.json').read_text());"
        "v=joblib.load(p/'vectorizer.joblib');m=joblib.load(p/'model_final.joblib');"
        "pred=m.predict(v.transform(r['teks'])).tolist();"
        "sys.exit(0 if pred==r['pred'] else 1)"
    )
    return subprocess.run([sys.executable, "-c", kode], cwd=ROOT).returncode == 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("model", help="linear_svc | logistic_regression | complement_nb | multinomial_nb")
    ap.add_argument("--seleksi", choices=["1se", "grid"], default="1se",
                    help="1se = aturan satu simpangan baku (default); grid = pemenang GridSearchCV")
    ap.add_argument("--dry-run", action="store_true",
                    help="tulis ke direktori sementara, jangan sentuh ml/artifacts/")
    a = ap.parse_args()

    out = (Path(__import__("tempfile").mkdtemp(prefix="finalize-")) if a.dry_run
           else ROOT / "ml" / "artifacts")
    man = bangun(a.model, out, seleksi=a.seleksi)
    print(f"Artefak ditulis ke: {out}")
    for f in sorted(out.glob("*")):
        if f.name.startswith(("tuned_", "best_params")) or f.is_dir():
            continue
        print(f"  {f.name:28s} {f.stat().st_size:>9,} B")
    m = man["model"]
    print(f"\nmodel       : {m['name']}  params={m['params']}")
    print(f"seleksi     : {m['selection_rule']}")
    print(f"  pemenang grid : {m['gridsearch_best_params']}")
    print(f"  CV f1_macro   : {m['cv_f1_macro']:.4f} (std {m['cv_f1_macro_std']:.4f}, "
          f"selisih train-test {m['overfit_gap_cv']:.4f})")
    print(f"terkalibrasi: {m['calibrated']}")
    print("\nmetrik model final (dievaluasi di sini, bukan dari CSV):")
    for k, v in man["metrics"].items():
        print(f"  {k:17s} macro_f1={v['macro_f1']:.4f}  recall_neg={v['recall_neg']:.4f}  "
              f"f1_neg={v['f1_neg']:.4f}  acc={v['accuracy']:.4f}  (n={v['n_eval']:,})")
    ok = verifikasi_muat_ulang(out)
    print(f"\nUji muat ulang di proses baru (10 sampel): {'LOLOS' if ok else 'GAGAL'}")
    if not ok:
        raise SystemExit(1)

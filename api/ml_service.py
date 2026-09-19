"""Pemuatan artefak & inferensi satuan untuk /api/predict (Fase 7, T-7.2).

Endpoint ini adalah DEMO kapabilitas, bukan sumber data dashboard. Enam
endpoint lain tidak pernah menyentuh modul ini; seluruh angka dashboard berasal
dari pre-scoring batch Fase 6 yang sudah tersimpan di `review_scores`.

Dua hal yang dijaga ketat di sini:

1. **Preprocessing diimpor, tidak ditulis ulang.** `ml.src.preprocess.praproses_satu`
   adalah fungsi yang sama yang membentuk `ulasan_clean` di Fase 2 — diverifikasi
   identik pada 300 sampel acak korpus. Menulis ulang pipeline di sisi API adalah
   bug yang tidak melempar error, hanya membuat prediksi pelan-pelan salah.
2. **Artefak dimuat sekali**, lewat `lifespan` di `main.py`, bukan per request.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import joblib

from .config import get_settings

S = get_settings()

LABEL = {0: "Negatif", 1: "Positif"}

CATATAN_DEMO = ("Endpoint demo. Data dashboard berasal dari pre-scoring batch "
                "(Fase 6), bukan dari endpoint ini.")


class ArtefakGagalDimuat(RuntimeError):
    """Dibedakan dari RuntimeError biasa agar `main.py` dapat memetakannya ke 503."""


def muat(artifacts_dir: Path | None = None) -> dict[str, Any]:
    """Muat vectorizer + classifier + manifest. Gagal keras bila salah satu hilang.

    `model_final.joblib` adalah classifier TELANJANG — vectorizer-nya terpisah
    (`vectorizer.joblib`). Ini mengikuti `ml/src/score.py` jenis 'clf_terpisah';
    memasangkannya terbalik dengan vectorizer milik pipeline `tuned_*` akan
    menghasilkan ruang fitur yang berbeda dan prediksi yang tidak berarti.
    """
    art = Path(artifacts_dir or S.artifacts_dir)
    try:
        t0 = time.perf_counter()
        vectorizer = joblib.load(art / "vectorizer.joblib")
        model = joblib.load(art / "model_final.joblib")
        manifest = json.loads((art / "MANIFEST.json").read_text(encoding="utf-8"))

        # Pemanasan: impor ml.src.preprocess menarik Sastrawi, kamus slang, dan
        # cache stem (±586 KB). Dilakukan di startup agar request pertama tidak
        # menanggung biayanya.
        from ml.src.preprocess import praproses_satu
        praproses_satu("aplikasi error terus gabisa bayar")
    except FileNotFoundError as e:
        raise ArtefakGagalDimuat(f"artefak tidak ditemukan: {e.filename}") from e
    except Exception as e:                                   # unpickle gagal, dll.
        raise ArtefakGagalDimuat(f"{type(e).__name__}: {e}") from e

    nama = manifest.get("model", {}).get("name", S.model_produksi)
    if nama != S.model_produksi:
        raise ArtefakGagalDimuat(
            f"MANIFEST menyebut model '{nama}', konfigurasi API menuntut "
            f"'{S.model_produksi}'. Agregat dashboard diskor dengan "
            f"'{S.model_produksi}'; melayani /predict dengan model lain akan "
            f"membuat demo tidak konsisten dengan grafiknya sendiri.")

    return {
        "vectorizer": vectorizer,
        "model": model,
        "manifest": manifest,
        "model_name": nama,
        "punya_proba": hasattr(model, "predict_proba"),
        "load_seconds": round(time.perf_counter() - t0, 3),
    }


def prediksi(ml: dict[str, Any], teks: str) -> dict[str, Any] | None:
    """None bila teks habis setelah preprocessing — dipetakan ke 400 di main.py.

    Teks bisa habis secara sah: ulasan yang seluruhnya emoji, angka, atau
    stopword tidak menyisakan token apa pun untuk TF-IDF. Memprediksi vektor
    nol akan selalu mengembalikan kelas mayoritas, dan itu jawaban yang
    terlihat meyakinkan tanpa berdasar apa pun.
    """
    from ml.src.preprocess import praproses_satu

    hasil = praproses_satu(teks)
    clean = hasil["ulasan_clean"].strip()
    if not clean:
        return None

    X = ml["vectorizer"].transform([clean])
    pred = int(ml["model"].predict(X)[0])

    confidence = None
    if ml["punya_proba"]:
        proba = ml["model"].predict_proba(X)[0]
        confidence = round(float(proba[pred]), 4)

    return {
        "text": teks,
        "text_preprocessed": clean,
        "text_normalized": hasil["ulasan_normalized"],
        "prediction": pred,
        "label": LABEL[pred],
        "confidence": confidence,
        "model_name": ml["model_name"],
        "note": CATATAN_DEMO,
    }

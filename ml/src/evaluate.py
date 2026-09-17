"""Metrik evaluasi (Fase 3, T-3.7).

Accuracy BUKAN metrik utama. Dengan komposisi 72,3% positif, model yang selalu
menebak "positif" memperoleh akurasi 72,3% tanpa mempelajari apa pun. Prioritas
pelaporan: recall kelas negatif -> macro-F1 -> F1 negatif, dengan accuracy
sebagai pelengkap yang selalu disandingkan dengan baseline.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (accuracy_score, classification_report, f1_score,
                             precision_score, recall_score)

NEG = 0  # label kelas negatif


def hitung_metrik(y_true, y_pred) -> dict[str, float]:
    return {
        "recall_neg": recall_score(y_true, y_pred, pos_label=NEG, zero_division=0),
        "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "f1_neg": f1_score(y_true, y_pred, pos_label=NEG, zero_division=0),
        "precision_neg": precision_score(y_true, y_pred, pos_label=NEG, zero_division=0),
        "accuracy": accuracy_score(y_true, y_pred),
    }


def laporan_lengkap(y_true, y_pred) -> dict:
    return classification_report(y_true, y_pred, output_dict=True, zero_division=0,
                                 target_names=["negatif", "positif"])

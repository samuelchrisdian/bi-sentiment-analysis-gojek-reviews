"""Vektorisasi TF-IDF (Fase 3, T-3.4).

Satu builder dipakai seluruh model agar perbedaan skor benar-benar berasal dari
algoritmanya, bukan dari perlakuan fitur yang berbeda.
"""
from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer


def build_vectorizer(cfg: dict) -> TfidfVectorizer:
    t = cfg["features"]["tfidf"]
    return TfidfVectorizer(
        ngram_range=tuple(t["ngram_range"]),
        min_df=t["min_df"],
        max_features=t["max_features"],
        sublinear_tf=t["sublinear_tf"],
        # Teks sudah di-case-fold dan ditokenisasi pada Fase 2. Tanpa dua
        # argumen berikut, TF-IDF akan menokenisasi ulang dengan regex bawaan
        # yang membuang token satu huruf dan memotong hasil normalisasi.
        lowercase=False,
        token_pattern=r"\S+",
    )

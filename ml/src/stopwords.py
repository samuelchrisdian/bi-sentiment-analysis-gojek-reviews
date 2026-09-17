"""Daftar stopword kustom (Fase 2, T-2.2).

Daftar bawaan Sastrawi memuat `tidak`, `bukan`, `jangan`, dan `belum` — kata
pembawa negasi yang justru paling menentukan pada klasifikasi sentimen. Memakai
daftar itu apa adanya membuat "tidak bagus" menjadi "bagus", yaitu kebalikan
maknanya, tepat pada kelas yang menjadi fokus penelitian.

Keputusan ini bersifat metodologis, bukan detail implementasi, dan dilaporkan
di bab metodologi.
"""
from __future__ import annotations

from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

NEGATION_KEEP: frozenset[str] = frozenset({
    "tidak", "bukan", "jangan", "belum", "tanpa",
    "kurang", "susah", "sulit", "sering", "selalu", "pernah",
})


def build_stopwords() -> frozenset[str]:
    base = set(StopWordRemoverFactory().get_stop_words())
    return frozenset(base - NEGATION_KEEP)

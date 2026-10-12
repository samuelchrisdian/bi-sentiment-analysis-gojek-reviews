"""Daftar stopword kustom (Fase 2).

Daftar bawaan Sastrawi memuat `tidak`, `bukan`, `jangan`, dan `belum` — kata
pembawa negasi yang justru paling menentukan pada klasifikasi sentimen. Memakai
daftar itu apa adanya membuat "tidak bagus" menjadi "bagus", yaitu kebalikan
maknanya, tepat pada kelas yang menjadi fokus penelitian.

Keputusan ini bersifat metodologis, bukan detail implementasi, dan dilaporkan
di bab metodologi.
"""
from __future__ import annotations

from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

# Diperluas setelah verifikasi manual pra-pemrosesan: membuang modal dan
# eksistensial menghapus hampir semua frasa "tidak bisa", "tidak ada", dan
# "tidak dapat" ("tidak bisa dibatalkan" menjadi "tidak batal"). Ini juga
# melumpuhkan bigram, padahal "tidak_bisa" adalah fitur negatif terkuat.
NEGATION_KEEP: frozenset[str] = frozenset({
    # Negasi inti
    "tidak", "bukan", "jangan", "belum", "tanpa",
    # Modal & eksistensial — pembentuk frasa negasi
    "bisa", "ada", "dapat", "boleh", "mau", "perlu", "usah", "akan",
    "mungkin", "sempat", "harus",
    # Penanda derajat & frekuensi yang membawa sentimen
    "kurang", "susah", "sulit", "sering", "selalu", "pernah",
    # Penghubung yang membawa relasi antar klausa keluhan
    "atau",
    # Pembentuk frasa evaluatif negatif ("tidak guna", "tidak becus")
    "guna",
})


def build_stopwords() -> frozenset[str]:
    base = set(StopWordRemoverFactory().get_stop_words())
    return frozenset(base - NEGATION_KEEP)

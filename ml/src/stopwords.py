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

# Diperluas setelah gerbang H-6 putaran 2. Pemeriksaan manual menemukan bahwa
# membuang modal dan eksistensial merusak struktur negasi secara masif:
#
#     "tidak bisa"  : 4.834 dokumen -> hanya 3 bertahan
#     "tidak ada"   : 4.000 dokumen -> hanya 9 bertahan
#     "tidak dapat" : 1.109 dokumen -> hanya 69 bertahan
#
# "tidak bisa dibatalkan" menyusut menjadi "tidak batal" — modalitasnya hilang
# dan maknanya berubah. Ini juga melumpuhkan strategi bigram yang menjadi alasan
# ngram_range=(1,2) dipilih: justru "tidak_bisa" adalah fitur negatif terkuat
# pada ulasan aplikasi.
NEGATION_KEEP: frozenset[str] = frozenset({
    # Negasi inti
    "tidak", "bukan", "jangan", "belum", "tanpa",
    # Modal & eksistensial — pembentuk frasa negasi
    "bisa", "ada", "dapat", "boleh", "mau", "perlu", "usah", "akan",
    "mungkin", "sempat", "harus",
    # Penanda derajat & frekuensi yang membawa sentimen
    "kurang", "susah", "sulit", "sering", "selalu", "pernah",
})


def build_stopwords() -> frozenset[str]:
    base = set(StopWordRemoverFactory().get_stop_words())
    return frozenset(base - NEGATION_KEEP)

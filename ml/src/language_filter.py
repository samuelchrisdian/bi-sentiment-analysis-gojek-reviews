"""Penyaringan ulasan berbahasa Inggris (pembaruan data scraping).

Populasi penelitian adalah ulasan berbahasa Indonesia. google-play-scraper
dengan `lang="id"` tetap mengembalikan sebagian ulasan yang ditulis dalam
bahasa Inggris; pada korpus ini ulasan tersebut cukup banyak di kelas negatif
sehingga membentuk satu topik LDA sendiri yang berisi bahasa, bukan tema.

Aturannya sengaja sederhana dan dapat diaudit: hanya KATA FUNGSI yang dihitung
(bukan kata isi seperti `driver` atau `app` yang lazim dipakai dalam ulasan
berbahasa Indonesia). Sebuah ulasan dianggap dominan Inggris bila

    n_token >= MIN_TOKEN  dan  n_inggris >= MIN_INGGRIS
    dan  n_inggris > RASIO * n_indonesia

Ulasan sangat pendek (mis. "good", "great") tidak dapat ditentukan bahasanya
dengan andal dan karena itu dipertahankan.
"""
from __future__ import annotations

import re

import pandas as pd

KATA_FUNGSI_INGGRIS = frozenset("""
the to and i a it is my of for you this not but that with be was are have they
me your can so very in on at just when or if from no all what there more
because too even after would will dont don't cant can't it's i'm im their them
our we us has had been than only also really still always never every
""".split())

KATA_FUNGSI_INDONESIA = frozenset("""
dan yang di ke dari tidak ga gak nggak ngga gk tdk ini itu saya aku nya ada
bisa sudah udah sangat banget tapi untuk dengan kalau kalo mau lagi juga sih
aja saja jadi karena krn yg dgn sama buat kok deh dong apa kenapa mohon tolong
belum blm masih harus
""".split())

_TOKEN = re.compile(r"[a-z']+")


def hitung(teks: str) -> tuple[int, int, int]:
    tok = _TOKEN.findall(str(teks).lower())
    return (len(tok),
            sum(t in KATA_FUNGSI_INGGRIS for t in tok),
            sum(t in KATA_FUNGSI_INDONESIA for t in tok))


def tandai_inggris(teks: pd.Series, cfg: dict) -> pd.Series:
    """True untuk ulasan yang dominan berbahasa Inggris."""
    p = cfg["language_filter"]
    h = teks.fillna("").map(hitung)
    n, en, idn = h.str[0], h.str[1], h.str[2]
    return ((n >= p["min_tokens"]) & (en >= p["min_english_function_words"])
            & (en > p["english_to_indonesian_ratio"] * idn))

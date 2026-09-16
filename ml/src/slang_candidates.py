"""Ekstraksi kandidat kamus slang (Fase 2, T-2.1 — bagian agent sebelum H-5).

Menghasilkan docs/tables/unknown_tokens_500.csv berisi token paling sering yang
TIDAK dikenali kamus kata dasar Sastrawi. Kolom `bentuk_baku` dan `buang`
sengaja dibiarkan kosong — pengisiannya adalah wewenang manusia (gerbang H-5).

Agent TIDAK BOLEH mengisi kolom tersebut dengan tebakan.
"""
from __future__ import annotations

import re
from collections import Counter

import pandas as pd
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

from .config import load_config, resolve
from .ingest import load_raw

CFG = load_config()
TABLES = CFG["_root"] / "docs" / "tables"
N_TOKENS = 500

# Varian negasi — diprioritaskan ke baris teratas karena paling berdampak pada
# kelas negatif, kelas yang menjadi fokus penelitian. Daftar eksplisit dipakai
# alih-alih pola longgar, supaya token seperti `good`, `bug`, atau `ngambil`
# tidak salah ditandai dan manusia tidak dibuat menyaring penanda yang keliru.
NEGASI_EKSAK = {
    "ga", "gak", "gk", "ngga", "nggak", "ngak", "ngk", "gaa", "gag",
    "tdk", "tak", "td", "blm", "blom", "blum", "bkn", "bukn", "jgn", "jangn",
}
NEGASI_AWALAN = re.compile(r"^(ga|gk|ngga|nggak|ngak)[a-z]{2,}$")


def is_negasi(token: str) -> bool:
    return token in NEGASI_EKSAK or bool(NEGASI_AWALAN.match(token))


_TOKEN_RE = re.compile(r"[a-z]+")


def tokenize_corpus(texts: pd.Series) -> Counter:
    counter: Counter = Counter()
    for t in texts.fillna("").str.lower():
        counter.update(_TOKEN_RE.findall(t))
    return counter


# Token di bawah ambang ini tidak pernah masuk 500 besar; menyaringnya lebih
# dulu memangkas pemanggilan stemmer Sastrawi dari puluhan ribu ke ribuan.
MIN_FREQ = 20


def build_candidates() -> pd.DataFrame:
    df = load_raw(CFG)
    freq = tokenize_corpus(df["Ulasan"])

    kamus = set(StemmerFactory().get_words())
    stemmer = StemmerFactory().create_stemmer()

    kandidat = {t: n for t, n in freq.items() if n >= MIN_FREQ and len(t) >= 2
                and t not in kamus}
    unknown = {t: n for t, n in kandidat.items() if stemmer.stem(t) not in kamus}

    top = sorted(unknown.items(), key=lambda kv: kv[1], reverse=True)[:N_TOKENS]
    target = {t for t, _ in top}

    # Satu contoh konteks nyata per token, dikumpulkan dalam SATU sapuan korpus
    # (bukan satu sapuan per token) agar tidak menjadi 500 x 100.000 operasi.
    contoh: dict[str, str] = {}
    for teks in df["Ulasan"].fillna("").str.lower():
        if len(contoh) == len(target):
            break
        for tok in set(_TOKEN_RE.findall(teks)) & target:
            contoh.setdefault(tok, teks[:110])
    for t in target:
        contoh.setdefault(t, "")

    out = pd.DataFrame(
        [{"token_asli": t, "frekuensi": n,
          "kemungkinan_negasi": is_negasi(t),
          "contoh_konteks": contoh[t],
          "bentuk_baku": "", "buang": ""}
         for t, n in top]
    )
    # Varian negasi naik ke atas, sisanya menurut frekuensi
    out = out.sort_values(["kemungkinan_negasi", "frekuensi"],
                          ascending=[False, False]).reset_index(drop=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    out.to_csv(TABLES / "unknown_tokens_500.csv", index=False)
    return out


if __name__ == "__main__":
    out = build_candidates()
    n_neg = int(out["kemungkinan_negasi"].sum())
    print(f"Ditulis: docs/tables/unknown_tokens_500.csv ({len(out)} token)")
    print(f"Kandidat varian negasi di baris teratas: {n_neg}")
    print(f"Total kemunculan token ini di korpus: {out['frekuensi'].sum():,}")
    print("\n--- 25 baris teratas ---")
    print(out.head(25)[["token_asli", "frekuensi", "kemungkinan_negasi", "contoh_konteks"]]
          .to_string(index=False, max_colwidth=45))

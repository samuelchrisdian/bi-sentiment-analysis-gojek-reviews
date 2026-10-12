"""Konversi CSV kamus slang hasil isian manusia menjadi ml/src/slang_dict.py (Fase 2).

Konversi ini MEKANIS: tidak ada entri yang ditambahkan, diubah, atau ditebak
oleh agent. Sumber kebenaran adalah docs/tables/token_normalisasi_terisi.csv
yang diisi manusia.
"""
from __future__ import annotations

import pandas as pd

from .config import load_config

CFG = load_config()
ROOT = CFG["_root"]
SRC = ROOT / "docs" / "tables" / "token_normalisasi_terisi.csv"
OUT = ROOT / "ml" / "src" / "slang_dict.py"

HEADER = '''"""Kamus normalisasi slang — DIHASILKAN OTOMATIS, JANGAN DISUNTING TANGAN.

Sumber  : docs/tables/token_normalisasi_terisi.csv, token_normalisasi_tambahan.csv,
          unknown_tokens_baru_scraping_reviewed.csv (seluruhnya diisi manusia)
Pembuat : python -m ml.src.build_slang_dict

SLANG_DICT memetakan token informal ke daftar token baku. Nilainya berupa list
karena sebagian pemetaan menghasilkan lebih dari satu kata
(mis. "gabisa" -> ["tidak", "bisa"]).

NOISE_TOKENS dibuang sepenuhnya, tidak dinormalisasi.
"""

'''


def main() -> None:
    d = pd.read_csv(SRC, keep_default_na=False, encoding="utf-8-sig")
    d.columns = [c.strip() for c in d.columns]
    d["token_asli"] = d.token_asli.astype(str).str.strip().str.lower()
    d["bentuk_baku"] = d.bentuk_baku.astype(str).str.strip().str.lower()
    d["buang"] = d.buang.astype(str).str.strip()

    buang = sorted(d.loc[(d.buang != "") & (d.buang.str.lower() != "nan"), "token_asli"])

    # Pemetaan yang DITOLAK pemeriksa pada verifikasi manual pra-pemrosesan.
    # `it` -> `itu` mengubah singkatan teknologi/tim IT menjadi kata tunjuk;
    # `jek` -> `gojek` membuat "Go-Jek" menjadi "go gojek" (token ganda).
    DITOLAK = {"it", "jek"}
    peta = {r.token_asli: r.bentuk_baku.split()
            for r in d.itertuples()
            if r.bentuk_baku and r.token_asli not in buang and r.token_asli not in DITOLAK}

    # Token yang diusulkan pemeriksa saat verifikasi manual pra-pemrosesan;
    # seluruh pemetaan tetap berasal dari manusia.
    tambahan = ROOT / "docs" / "tables" / "token_normalisasi_tambahan.csv"
    n_tambahan = 0
    if tambahan.exists():
        t = pd.read_csv(tambahan, keep_default_na=False, encoding="utf-8-sig")
        for r in t.itertuples():
            tok, baku = str(r.token_asli).strip().lower(), str(r.bentuk_baku).strip().lower()
            if tok and baku and tok not in buang and tok not in DITOLAK:
                peta[tok] = baku.split()
                n_tambahan += 1
        print(f"  tambahan verifikasi data awal: {n_tambahan} pemetaan")

    # Tambahan data scraping: 60 token tak dikenal berfrekuensi tertinggi pada
    # data baru, diputuskan manusia. Kolom `buang` berisi ya/tidak. Berkas ini
    # dibaca terakhir, sehingga entrinya menggantikan entri lama (mis. `goceng`).
    scraping = ROOT / "docs" / "tables" / "unknown_tokens_baru_scraping_reviewed.csv"
    if scraping.exists():
        s = pd.read_csv(scraping, keep_default_na=False, encoding="utf-8-sig")
        n_peta = n_buang = 0
        for r in s.itertuples():
            tok, baku = str(r.token_asli).strip().lower(), str(r.bentuk_baku).strip().lower()
            if str(r.buang).strip().lower() == "ya":
                peta.pop(tok, None)
                buang = sorted(set(buang) | {tok})
                n_buang += 1
            elif tok and baku:
                peta[tok] = baku.split()
                n_peta += 1
        print(f"  tambahan data scraping: {n_peta} pemetaan, {n_buang} dibuang")

    lines = [HEADER, "SLANG_DICT: dict[str, list[str]] = {\n"]
    def _freq(t: str) -> int:
        hit = d.loc[d.token_asli == t, "frekuensi"]
        return int(hit.iloc[0]) if len(hit) else 0

    for tok in sorted(peta, key=lambda t: (-_freq(t), t)):
        lines.append(f"    {tok!r}: {peta[tok]!r},\n")
    lines.append("}\n\nNOISE_TOKENS: frozenset[str] = frozenset({\n")
    for tok in buang:
        lines.append(f"    {tok!r},\n")
    lines.append("})\n")
    OUT.write_text("".join(lines), encoding="utf-8")

    n_multi = sum(1 for v in peta.values() if len(v) > 1)
    print(f"Ditulis: {OUT.relative_to(ROOT)}")
    print(f"  SLANG_DICT  : {len(peta)} entri ({n_multi} menghasilkan >1 kata)")
    print(f"  NOISE_TOKENS: {len(buang)} entri -> {buang}")


if __name__ == "__main__":
    main()

"""Konversi CSV hasil gerbang H-5 menjadi ml/src/slang_dict.py (Fase 2, T-2.1 langkah 6).

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

Sumber  : docs/tables/token_normalisasi_terisi.csv (diisi manusia, gerbang H-5)
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

    # Pemetaan yang DITOLAK pemeriksa pada gerbang H-6 putaran 2.
    # `it` -> `itu` mengubah singkatan teknologi/tim IT menjadi kata tunjuk;
    # `jek` -> `gojek` membuat "Go-Jek" menjadi "go gojek" (token ganda).
    DITOLAK = {"it", "jek"}
    peta = {r.token_asli: r.bentuk_baku.split()
            for r in d.itertuples()
            if r.bentuk_baku and r.token_asli not in buang and r.token_asli not in DITOLAK}

    # Tambahan hasil gerbang H-6: token yang diusulkan pemeriksa saat verifikasi
    # 100 sampel. Sama seperti H-5, seluruh pemetaan berasal dari manusia.
    tambahan = ROOT / "docs" / "tables" / "token_normalisasi_tambahan.csv"
    n_tambahan = 0
    if tambahan.exists():
        t = pd.read_csv(tambahan, keep_default_na=False, encoding="utf-8-sig")
        for r in t.itertuples():
            tok, baku = str(r.token_asli).strip().lower(), str(r.bentuk_baku).strip().lower()
            if tok and baku and tok not in buang and tok not in DITOLAK:
                peta[tok] = baku.split()
                n_tambahan += 1
        print(f"  tambahan H-6: {n_tambahan} pemetaan")

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

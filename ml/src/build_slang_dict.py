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
    peta = {r.token_asli: r.bentuk_baku.split()
            for r in d.itertuples() if r.bentuk_baku and r.token_asli not in buang}

    lines = [HEADER, "SLANG_DICT: dict[str, list[str]] = {\n"]
    for tok in sorted(peta, key=lambda t: (-int(d.loc[d.token_asli == t, "frekuensi"].iloc[0]), t)):
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

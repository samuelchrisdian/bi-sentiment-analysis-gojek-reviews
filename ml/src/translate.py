"""Terjemahan ulasan berbahasa Inggris ke bahasa Indonesia.

Populasi penelitian adalah ulasan berbahasa Indonesia, tetapi google-play-scraper
dengan `lang="id"` tetap mengembalikan sebagian ulasan berbahasa Inggris.
Ulasan itu tidak dibuang: yang terdeteksi dominan Inggris (aturan kata fungsi,
`ml/src/language_filter.py`) diterjemahkan dengan model MarianMT
Helsinki-NLP/opus-mt-en-id pada revisi yang dikunci, lalu `ingest.load_raw`
memakai terjemahannya sebagai teks ulasan. Teks asli tetap disimpan.

Model dijalankan luring di CPU dan bersifat deterministik (beam search tanpa
sampling), sehingga hasilnya dapat diulang. Setiap ulasan dipecah per kalimat
lebih dulu: MarianMT cenderung menghilangkan kalimat kedua dan seterusnya bila
satu masukan memuat beberapa kalimat.

Dijalankan dengan lingkungan terpisah (torch & transformers tidak dipasang di
.venv utama karena versi NumPy-nya dikunci untuk gensim):

    .venv-translate/bin/python -m ml.src.translate
"""
from __future__ import annotations

import json
import re
import time

import pandas as pd

from .config import load_config, resolve
from .language_filter import tandai_inggris

CFG = load_config()
T = CFG["translation"]
KELUARAN = resolve(CFG, "translation.output_csv")
META = KELUARAN.with_suffix(".meta.json")

_KALIMAT = re.compile(r"(?<=[.!?])\s+|\n+")


def pecah_kalimat(teks: str) -> list[str]:
    return [k.strip() for k in _KALIMAT.split(str(teks)) if k and k.strip()]


def muat_sumber() -> pd.DataFrame:
    df = pd.read_csv(resolve(CFG, "paths.raw_csv"), encoding="utf-8-sig",
                     usecols=["reviewId", "content"])
    return df[tandai_inggris(df["content"], CFG)].reset_index(drop=True)


def terjemahkan_kalimat(kalimat: list[str]) -> dict[str, str]:
    import torch
    from transformers import MarianMTModel, MarianTokenizer

    torch.set_num_threads(T["threads"])
    tok = MarianTokenizer.from_pretrained(T["model"], revision=T["revision"])
    model = MarianMTModel.from_pretrained(T["model"], revision=T["revision"]).eval()

    # Urut menurut panjang agar padding per batch minimal.
    urut = sorted(set(kalimat), key=len)
    hasil: dict[str, str] = {}
    t0 = time.perf_counter()
    with torch.no_grad():
        for i in range(0, len(urut), T["batch_size"]):
            batch = urut[i:i + T["batch_size"]]
            enc = tok(batch, return_tensors="pt", padding=True, truncation=True,
                      max_length=T["max_tokens"])
            out = model.generate(**enc, num_beams=T["num_beams"], do_sample=False,
                                 max_new_tokens=T["max_tokens"])
            hasil.update(zip(batch, tok.batch_decode(out, skip_special_tokens=True)))
            if (i // T["batch_size"]) % 25 == 0:
                laju = len(hasil) / max(time.perf_counter() - t0, 1e-9)
                print(f"  {len(hasil):,}/{len(urut):,} kalimat ({laju:.1f}/detik)", flush=True)
    return hasil


def main() -> None:
    src = muat_sumber()
    print(f"Ulasan dominan Inggris: {len(src):,}", flush=True)

    lama = (pd.read_csv(KELUARAN) if KELUARAN.exists()
            else pd.DataFrame(columns=["reviewId", "content_terjemahan"]))
    sudah = set(lama["reviewId"])
    baru = src[~src["reviewId"].isin(sudah)]
    print(f"Sudah diterjemahkan sebelumnya: {len(src) - len(baru):,}; "
          f"perlu diterjemahkan: {len(baru):,}", flush=True)

    if len(baru):
        pecahan = baru["content"].map(pecah_kalimat)
        peta = terjemahkan_kalimat([k for ks in pecahan for k in ks])
        baru = baru.assign(
            n_kalimat=pecahan.map(len),
            content_terjemahan=pecahan.map(lambda ks: " ".join(peta[k] for k in ks)))
        lama = pd.concat([lama, baru.rename(columns={"content": "content_asli"})],
                         ignore_index=True)

    out = lama[lama["reviewId"].isin(set(src["reviewId"]))]
    KELUARAN.parent.mkdir(parents=True, exist_ok=True)
    out[["reviewId", "content_asli", "content_terjemahan", "n_kalimat"]].to_csv(
        KELUARAN, index=False)

    from importlib.metadata import version
    META.write_text(json.dumps({
        "model": T["model"], "revision": T["revision"], "num_beams": T["num_beams"],
        "max_tokens": T["max_tokens"], "transformers": version("transformers"),
        "torch": version("torch"), "n_ulasan_diterjemahkan": int(len(out)),
        "n_kalimat": int(out["n_kalimat"].sum()),
    }, indent=2), encoding="utf-8")
    print(f"Disimpan: {KELUARAN.relative_to(CFG['_root'])} ({len(out):,} ulasan)")


if __name__ == "__main__":
    main()
